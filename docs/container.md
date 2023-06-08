# NixOS container

### Create and start

Within the cloned `liberaforms-flake` directory, run the following commands to create
and then start the nixos-container
```sh
sudo nixos-container create liberaforms --flake ./#container-x86_64-linux
sudo nixos-container start liberaforms
```
The `create` command will output a local container IP address (such as
`10.233.1.2`). Once the container is started, visiting this address in a browser
on the host system will display the LiberaForms instance where you can then
follow the instructions on
[bootstrapping a first Admin user](https://gitlab.com/liberaforms/liberaforms/-/tree/develop#bootstrapping-the-first-admin).
The default admin email address is `admin@example.org` though this can be
easily modified in the `flake.nix`.

### Login

This command can be used to login to a root shell for the container:
```sh
sudo nixos-container root-login liberaforms
```

### Update

If you make changes to the flake.nix or the nix/module.nix and would like to see
them reflected in an already running container, you can use the update command
for this purpose:
```sh
sudo nixos-container update liberaforms --flake ./container-x86_64-linux
```

### Stop and destroy

A container that has been started can be stopped, and one that has been created
can be destroyed:
```sh
sudo nixos-container stop liberaforms
sudo nixos-container destroy liberaforms
```

## Tests

The [unit and functional test suite](https://gitlab.com/liberaforms/liberaforms/-/tree/develop/tests)
for LiberaForms can be run on NixOS using the command `nix flake check`.
