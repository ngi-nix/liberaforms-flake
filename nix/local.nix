# settings
{ self
, serverCfg
, ...
}:
# module args
{ modulesPath
, lib
, ...
}:
with serverCfg; {
  imports =
    [
      ./local-hardware-configuration.nix
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
    # enableHTTPS = true;
    domain = "${hostname}.${domain}";
    enableDatabaseBackup = true;
    rootEmail = "${email}";
  };
}
