{ pkgs, lib, inputs ? builtins.throw "Expected an inputs argument that corresponds to flake conventions", ... }: {
  imports = [inputs.self.nixosModules.liberaforms];

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
}
