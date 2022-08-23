{
  description = "Liberaforms — An open source form server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    mach-nix.url = "github:DavHau/mach-nix/3.5.0";
    deploy-rs.url = "github:serokell/deploy-rs";
    deploy-rs.inputs.nixpkgs.follows = "nixpkgs";

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
    # initPostgres = ./nix/initPostgres.sh;

    # System types to support.
    supportedSystems = ["x86_64-linux"];
    # Helper function to generate an attrset '{ x86_64-linux = f "x86_64-linux"; ... }'.
    genSystems = nixpkgs.lib.genAttrs supportedSystems;
    # genAttrs but you can also apply a function to the name
    genAttrs' = names: fn: fv: nixpkgs.lib.listToAttrs (map (n: nixpkgs.lib.nameValuePair (fn n) (fv n)) names);
    pkgsFor = nixpkgs.legacyPackages;

    serverCfg = {
      hostname = "forms";
      domain = "example.org";
      email = "admin@example.org";
    };
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

      liberaforms = prev.stdenv.mkDerivation {
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

    # System configurations for nixos-container local dev deployment and DigitalOcean deployments
    nixosConfigurations = let
      genConfig = name: args:
        genAttrs' supportedSystems (system: "${name}-" + system) (system:
          nixpkgs.lib.nixosSystem {
            inherit system;
            modules = [(import ./nix/${name}.nix args)];
          });
    in
      (genConfig "container" self) // (genConfig "digitalocean" {inherit self serverCfg;});

    deploy.nodes = genAttrs' supportedSystems (s: "liberaforms-${s}") (system: {
      hostname = serverCfg.domain;
      profiles.system = {
        user = "root";
        sshUser = "root";
        path = inputs.deploy-rs.lib.${system}.activate.nixos self.nixosConfigurations."liberaforms-${system}";
      };
    });

    # This is highly advised, and will prevent many possible mistakes
    checks = builtins.mapAttrs (system: deployLib: deployLib.deployChecks self.deploy) inputs.deploy-rs.lib;
  };
}
