# Deploy LiberaForms

This repository contains a Nix flake for easily deploying an instance of [LiberaForms](https://liberaforms.org) to a public NixOS VM using the [deploy-rs](https://github.com/serokell/deploy-rs) tool. 
The default/tested config is for Digital Ocean (DO), but in theory it could be to any [virtualization platform supported by NixOS](https://github.com/NixOS/nixpkgs/tree/master/nixos/modules/virtualisation).

## Steps

0. [Build a custom image for DO](https://justinas.org/nixos-in-the-cloud-step-by-step-part-1) from the nixos-unstable branch, upload it through their web interface, and then use it to create a new droplet (VM).
1. Configure a DNS A record to point to the IP address of the new VM and then confirm that you can login as root at your domain, for example `ssh root@forms.example.org`.
2. Clone this repo `git clone https://github.com/ngi-nix/deploy-liberaforms` to your local system running Nix with [flakes enabled](https://nixos.wiki/wiki/Flakes#System-wide_installation).
3. Modify the flake.nix file to fill in the required configs (hostname, domain, email).
4. Run the deployment `nix run github:serokell/deploy-rs .#liberaforms-vm`.

You should now have a new instance of LiberaForms running on your domain and can follow the instructions on [bootstrapping a first Admin user](https://gitlab.com/liberaforms/liberaforms/-/tree/develop#bootstrapping-the-first-admin). For more information, see the [NixOS page](https://github.com/ngi-nix/liberaforms/blob/main/docs/nixos.md) of the LiberaForms documentation. 

TODO:
- Update the nixpkgs branches in the flake inputs, and the image branch in these docs, to 21.11 after it is released (for greater stability).
- Update 'github.com/ngi-nix/liberaforms' flake inputs and doc links to the upstream repo `gitlab.com/liberaforms/liberaforms` if/when the [package flake](https://github.com/ngi-nix/liberaforms) is merged there.
