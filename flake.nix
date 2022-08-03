{
  description = "Liberaforms — An open source form server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    liberaforms.url = "gitlab:liberaforms/liberaforms";
    liberaforms.flake = false;
    mach-nix.url = "github:DavHau/mach-nix/3.5.0";
  };

  outputs = {
    self,
    nixpkgs,
    mach-nix,
    ...
  } @ inputs: let
    # Extract version from VERSION.txt.
    remove-newline = string: builtins.replaceStrings ["\n"] [""] string;
    version = remove-newline (builtins.readFile (inputs.liberaforms + "/VERSION.txt"));

    # Postgres setup script for tests.
    initPostgres = ./nix/initPostgres.sh;

    # System types to support.
    supportedSystems = ["x86_64-linux"];
    # Helper function to generate an attrset '{ x86_64-linux = f "x86_64-linux"; ... }'.
    genSystems = nixpkgs.lib.genAttrs supportedSystems;
    pkgsFor = nixpkgs.legacyPackages;
  in {
    overlays.default = _: prev: let
      inherit (nixpkgs) lib;

      req = builtins.readFile (inputs.liberaforms + "/requirements.txt");
      # filter out "cryptography" as it makes mach-nix fail. also it is considered bad practice to hold back that package
      filteredReq = lib.concatStringsSep "\n" (builtins.filter (e: e != "cryptography==36.0.1") (lib.splitString "\n" req));

      liberaforms-env = mach-nix.lib.${system}.mkPython {
        requirements = filteredReq;
      };
    in {
      liberaforms = stdenv.mkDerivation rec {
        inherit version;
        pname = "liberaforms";

        src = inputs.liberaforms;

        dontConfigure = true; # do not use ./configure
        propagatedBuildInputs = [liberaforms-env python38Packages.flask_migrate postgresql];

        installPhase = ''
          cp -r . $out
        '';
      };
    };

    # Provide a nix-shell env to work with liberaforms.
    # TODO: maybe remove? Nix automatically uses the default package if no devShell is found and `nix develop` is run
    devShells.default = genSystems (system:
      pkgsFor.${system}.mkShell {
        packages = [self.packages.${system}.liberaforms];
      });

    # Provide some packages for selected system types.
    packages = genSystems (
      system:
        (self.overlays.default null pkgsFor.${system})
        // {default = self.packages.${system}.liberaforms;}
    );

    # Expose the module for use as an input in another flake
    nixosModules.liberaforms = import ./nix/module.nix self;

    # System configuration for a nixos-container local dev deployment
    nixosConfigurations.liberaforms =
      nixpkgs.lib.nixosSystem
      {
        system = "x86_64-linux";
        modules = [
          ({
            pkgs,
            lib,
            ...
          }: {
            imports = [self.nixosModules.liberaforms];

            boot.isContainer = true;
            networking.useDHCP = false;
            networking.hostName = "liberaforms";

            # A timezone must be specified for use in the LiberaForms config file
            time.timeZone = "Etc/UTC";

            services.liberaforms = {
              enable = true;
              flaskEnv = "development";
              flaskConfig = "development";
              enablePostgres = true;
              enableNginx = true;
              #enableHTTPS = true;
              domain = "liberaforms.local";
              enableDatabaseBackup = true;
              rootEmail = "admin@example.org";
            };
          })
        ];
      };

    # Tests run by 'nix flake check' and by Hydra.
    checks = genSystems (system: let
      inherit (self.packages.${system}) liberaforms;
      pkgs = pkgsFor.${system};
    in {
      liberaforms-test = pkgs.stdenv.mkDerivation {
        name = "${liberaforms.name}-test";

        src = inputs.liberaforms;

        buildInputs = [liberaforms];

        buildPhase = ''
          source ${initPostgres}
          initPostgres $(pwd)
        '';

        doCheck = true;

        checkInputs = with pkgs.python38Packages; [pytest pytest-dotenv];

        checkPhase = ''
          # Run pytest on the installed version. A running postgres database server is needed.
          (cd tests && cp test.ini.example test.ini && pytest)
        '';

        installPhase = "mkdir -p $out"; # make this derivation return success
      };
    });
  };
}
