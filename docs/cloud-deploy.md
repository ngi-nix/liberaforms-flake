# Deploy LiberaForms on NixOS in DigitalOcean

This repository contains a Nix flake for easily deploying an instance of
[LiberaForms](https://liberaforms.org) to a public NixOS VM using the
[deploy-rs](https://github.com/serokell/deploy-rs) tool. 

The default/tested config is for Digital Ocean (DO), but in theory it could be
deployed to any [virtualization platform supported by NixOS](https://github.com/NixOS/nixpkgs/tree/master/nixos/modules/virtualisation).

0. [Build a custom image for DO](https://justinas.org/nixos-in-the-cloud-step-by-step-part-1)
from the `nixos-unstable` branch, upload it through their web interface, and
then use it to create a new droplet (VM).
1. Configure a DNS A record to point to the IP address of the new VM and then
confirm that you can login as root at your domain, for example
`ssh root@forms.example.org`.
2. Clone this repo `git clone https://github.com/ngi-nix/liberaforms-flake` to
your local system running Nix with
[flakes enabled](https://nixos.wiki/wiki/Flakes#System-wide_installation).
3. Modify the `flake.nix` file to fill in the required configs (hostname, domain,
email).
4. Run the deployment `nix run github:serokell/deploy-rs .#liberaforms-x86_64-linux`.

You should now have a new instance of LiberaForms running on your domain and can
follow the instructions on
[bootstrapping a first Admin user](https://gitlab.com/liberaforms/liberaforms/-/tree/develop#bootstrapping-the-first-admin).
For more information, see the [container page](./container.md). 