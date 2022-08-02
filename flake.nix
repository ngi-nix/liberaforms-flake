{
  description = "Liberaforms — An open source form server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    liberaforms.url = "gitlab:liberaforms/liberaforms";
    liberaforms.flake = false;
    machnix.url = "github:DavHau/mach-nix/3.5.0";
  };

  outputs = {
    self,
    nixpkgs,
    machnix,
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

    # mach-nix instantiated for supported system types.
    machnixFor = genSystems (system:
      import machnix {
        pkgs = pkgsFor.${system};
        python = "python38";

        # The default version of the pypi dependencies db that is updated with every mach-nix release
        # might not be sufficient for newer releases of liberaforms. Edit here to pin to specific commit.
        # The corresponding sha256 hash can be obtained with:
        # $ nix-prefetch-url --unpack https://github.com/DavHau/pypi-deps-db/tarball/<pypiDataRev>
        pypiDataRev = "020c5fbad4b0a6a9317646ed377631123730031c";
        pypiDataSha256 = "14a0b5gn3rhd10yhg7a5m3mx9ans1v105iy0xdxik8v4zyjw3hmd";
      });
  in {
    # A Nixpkgs overlay.
    overlays.default = _: prev:
      with prev.pkgs; let
        # Adding cffi to the requirements list was necessary for the cryptography package to build properly.
        # The cryptography build also logged a message about the "packaging" package so it was added as well.
        liberaforms-env = machnixFor.${system}.mkPython {
          requirements = builtins.readFile (inputs.liberaforms + "/requirements.txt") + "\ncffi>=1.14.5" + "\npackaging>=20.9";
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
