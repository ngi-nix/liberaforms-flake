{
  description = "Liberaforms — An open source form server";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    mach-nix.url = "github:DavHau/mach-nix/3.5.0";
    deploy-rs.url = "github:serokell/deploy-rs";
    deploy-rs.inputs.nixpkgs.follows = "nixpkgs";

    liberaforms = {
    # url = "gitlab:liberaforms/liberaforms?rev=34c82375c1e991745a562e71ac0b1e80e429d8ce"; # v2.1.0
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
    # System types to support.
    supportedSystems = ["x86_64-linux"];
    # Helper function to generate an attrset '{ x86_64-linux = f "x86_64-linux"; ... }'.
    genSystems = nixpkgs.lib.genAttrs supportedSystems;
    # genAttrs but you can also apply a function to the name
    genAttrs' = names: fn: fv: nixpkgs.lib.listToAttrs (map (n: nixpkgs.lib.nameValuePair (fn n) (fv n)) names);
    pkgsFor = genSystems (system:
      import nixpkgs {
        inherit system;
        overlays = [self.overlays.default];
      });

    serverCfg = {
      hostname = "secuform";
      domain = "local";
      email = "cleeyv@riseup.net";
    };
  in {
    # Overlay containing package definitions
    overlays.default = import nix/overlay.nix inputs;

    # Provide some packages for selected system types.
    packages = genSystems (
      system: {
        # Include everything from the overlay
        inherit (pkgsFor.${system}) liberaforms liberaforms-env;
        # Set the default package
        default = self.packages.${system}.liberaforms;
      }
    );

    # Expose the module for use as an input in another flake
    nixosModules.liberaforms = import ./nix/module.nix self;

    # System configurations for nixos-container local dev deployment and DigitalOcean deployments
    nixosConfigurations = let
      genConfig = name: args:
        genAttrs' supportedSystems (s: "${name}-${s}") (system:
          nixpkgs.lib.nixosSystem {
            inherit system;
            modules = [(import ./nix/${name}.nix args)];
          });
    in
      (genConfig "container" self) // (genConfig "local" {inherit self serverCfg;});

    deploy.nodes = genAttrs' supportedSystems (s: "liberaforms-${s}") (system: {
      hostname = "${serverCfg.hostname}.${serverCfg.domain}";
      profiles.system = {
        user = "root";
        sshUser = "root";
        path = inputs.deploy-rs.lib.${system}.activate.nixos self.nixosConfigurations."local-${system}";
      };
    });

    # This is highly advised, and will prevent many possible mistakes
    checks = builtins.mapAttrs (system: deployLib: deployLib.deployChecks self.deploy) inputs.deploy-rs.lib;
  };
}
