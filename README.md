# LiberaForms flake

This flake provides the package, NixOS module, NixOS container and development
environment for LiberaForms.

`nix flake show github:ngi-nix/liberaforms-flake` - show what the flake provides

`nix develop github:ngi-nix/liberaforms-flake` - enter the devShell for LiberaForms

## LiberaForms on NixOS

These instructions are for running a local development instance of LiberaForms
in a NixOS container.

For an easy way to deploy a production LiberaForms instance to NixOS on a
public cloud VM, see [this guide](./docs/cloud-deploy.md).

## Nix flake

The `flake.nix` (along with the `nix/module.nix`) contains the configuration to
run a LiberaForms instance and all of its dependencies and recommended
configurations (postgres, nginx, and db backups). For running in a local
nixos-container HTTPS is disabled by default, and flask (the python web
framework used to create LiberaForms) is running in development mode. All of
the required secrets and variables are generated automatically.

## NixOS container

See [this guide](./docs/container.md).

## Tests

The [unit and functional test suite](https://gitlab.com/liberaforms/liberaforms/-/tree/develop/tests)
for LiberaForms can be run on NixOS using the command `nix flake check`.
