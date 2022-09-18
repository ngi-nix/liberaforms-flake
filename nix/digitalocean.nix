# settings
{
  self,
  serverCfg,
  ...
}:
# module args
{
  modulesPath,
  lib,
  ...
}:
with serverCfg; {
  imports =
    lib.optional (builtins.pathExists ./do-userdata.nix) ./do-userdata.nix
    ++ [
      (modulesPath + "/virtualisation/digital-ocean-config.nix")
      self.nixosModules.liberaforms
    ];

  networking.hostName = "${hostname}";
  networking.domain = "${domain}";
  # A timezone must be specified for use in the LiberaForms config file
  time.timeZone = "America/Montreal";

  services.liberaforms = {
    enable = true;
    enablePostgres = true;
    enableNginx = true;
    enableHTTPS = true;
    domain = "${hostname}.${domain}";
    enableDatabaseBackup = true;
    rootEmail = "${email}";
  };
}
