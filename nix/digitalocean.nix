{
  description = "Deployment of LiberaForms";

  # For accessing `deploy-rs`'s utility Nix functions
  inputs.deploy-rs.url = "github:serokell/deploy-rs";
  inputs.liberaforms.url = "github:ngi-nix/liberaforms";
  inputs.nixpkgs.url = "github:nixos/nixpkgs/master";

  outputs = { self, nixpkgs, deploy-rs, liberaforms }:
    let
      ##############################
      ## Required configs go here ##
      ##############################
      hostname = "FORMS";
      domain = "EXAMPLE.ORG";
      email = "ADMIN@EXAMPLE.ORG";
    in
    {
      nixosConfigurations = {
        liberaforms-vm = nixpkgs.lib.nixosSystem {
          system = "x86_64-linux";
          modules = [
            # NixOS module from LiberaForms flake
            liberaforms.nixosModules.liberaforms

            # Digital Ocean VM config from nixos/modules/virtualisation/digital-ocean-init.nix
            ./digitalocean.nix

            ({ config, pkgs, liberaforms, ... }:
              {
                networking.hostName = "${hostname}";
                networking.domain = "${domain}";
                # A timezone must be specified for use in the LiberaForms config file
                time.timeZone = "Etc/UTC";

                services.liberaforms = {
                  enable = true;
                  enablePostgres = true;
                  enableNginx = true;
                  enableHTTPS = true;
                  domain = "${hostname}.${domain}";
                  enableDatabaseBackup = true;
                  rootEmail = "${email}";
                };
              })
          ];
          specialArgs = { inherit self; };
        };
      };

      deploy.nodes = {
        liberaforms-vm = {
          hostname = "${hostname}.${domain}";
          profiles.system = {
            user = "root";
            sshUser = "root";
            path = deploy-rs.lib.x86_64-linux.activate.nixos self.nixosConfigurations.liberaforms-vm;
          };
        };
      };

      # This is highly advised, and will prevent many possible mistakes
      checks = builtins.mapAttrs (system: deployLib: deployLib.deployChecks self.deploy) deploy-rs.lib;
    };
}
