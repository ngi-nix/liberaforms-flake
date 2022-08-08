final: prev: 
(with builtins; seq ((hasAttr "inputs" prev) || throw "If you are calling this directly, make sure the overlays have an `inputs` attribute conforming to the flakes interface."))
(let
  packages = final.inputs.self.packages.${prev.system};
in {
  liberaforms-env =
    let
      req = builtins.readFile (final.inputs.liberaforms + "/requirements.txt");
      #TODO lots of notes here; mach-nix doesnt handle (??xref various issues) range of cryptography package - because it doesnt support pyproject.toml?
      #I don't like this, but doing this is the fastest way to get the cryptography from nixpkgs, which is at 36.0.0 (mach-nix automatically finds it)
      filteredReq = builtins.replaceStrings ["cryptography==36.0.1"] ["cryptography==36.0.0"] req;
      # Needed for tests only; TODO upstream should make a dev-requirements.txt or whatever?
      # https://gitlab.com/liberaforms/liberaforms/-/commit/16c893ff539bfb6249b3b02f4c834eb8848c16d5
      extraReq = "factory_boy"; 
      requirements = ''
        ${filteredReq}
        ${extraReq}
      '';
    in final.inputs.mach-nix.lib.${prev.system}.mkPython { inherit requirements; };

  liberaforms = prev.stdenv.mkDerivation {
    pname = "liberaforms";
    version = with builtins; let
        remove-newline = replaceStrings ["\n"] [""];
      in remove-newline (readFile (final.inputs.liberaforms + "/VERSION.txt"));

    src = final.inputs.liberaforms;

    dontConfigure = true; # do not use ./configure
    propagatedBuildInputs = [packages.liberaforms-env prev.postgresql]; #TODO unfuck
    installPhase = ''
      cp -r . $out
    '';

    #doCheck = true; #TODO why does this explicitly need to be set #NOTE: this is default false here then?, - and it's overridden to enabled in the flake check
    checkInputs = with packages.liberaforms-env.passthru.pkgs; [pytest pytest-dotenv ];
    checkPhase = ''
      source ${./test_env.sh.in}
      initPostgres $(mktemp -d)

      # Run pytest on the installed version. A running postgres database server is needed.
      (cd tests && cp test.ini.example test.ini && pytest -k "not test_save_smtp_config") #TODO why does this break?

      shutdownPostgres
    '';
  };
})
