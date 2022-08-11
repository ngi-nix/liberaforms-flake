{
  description = "Liberaforms — An open source form server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    mach-nix.url = "github:DavHau/mach-nix/3.5.0";

    liberaforms = {
      url = "gitlab:liberaforms/liberaforms";
      flake = false;
    };
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

      liberaforms-env = mach-nix.lib.${prev.system}.mkPython {
        requirements = filteredReq;
      };
    in {
      inherit liberaforms-env;

      liberaforms = prev.stdenv.mkDerivation rec {
        inherit version;
        pname = "liberaforms";

        src = inputs.liberaforms;

        dontConfigure = true; # do not use ./configure
        propagatedBuildInputs =
          [liberaforms-env prev.postgresql]
          ++ (with prev.python39Packages; [
            flask_migrate
            flask_login
            pillow
          ]);

        installPhase = ''
          cp -r . $out
        '';
      };
    };

    # Provide a nix-shell env to work with liberaforms.
    # TODO: maybe remove? Nix automatically uses the default package if no devShell is found and `nix develop` is run
    devShells = genSystems (system: {
      default = pkgsFor.${system}.mkShell {
        packages = [self.packages.${system}.liberaforms];
      };
    });

    # Provide some packages for selected system types.
    packages = genSystems (
      system:
      # Include everything from the overlay
        (self.overlays.default null pkgsFor.${system})
        # Set the default package
        // {default = self.packages.${system}.liberaforms;}
    );

    # Expose the module for use as an input in another flake
    nixosModules.liberaforms = import ./nix/module.nix self;

    # System configuration for a nixos-container local dev deployment
    nixosConfigurations = genSystems (system:
      nixpkgs.lib.nixosSystem {
        inherit system;
        modules = [(import ./nix/container.nix self)];
      });
  };
}
