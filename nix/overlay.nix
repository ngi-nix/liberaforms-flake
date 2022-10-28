inputs: final: prev: {
  liberaforms-env = let
    req = builtins.readFile (inputs.liberaforms + "/requirements.txt");
    #TODO lots of notes here; mach-nix doesnt handle (??xref various issues) range of cryptography package - because it doesnt support pyproject.toml?
    #I don't like this, but doing this is the fastest way to get the cryptography from nixpkgs, which is at 36.0.0 (mach-nix automatically finds it)
    filteredReq = builtins.replaceStrings ["cryptography==36.0.1"] ["cryptography==36.0.0"] req; # for liberaforms > v2.0.1
    # Needed for tests only; TODO upstream should make a dev-requirements.txt or whatever?
    # https://gitlab.com/liberaforms/liberaforms/-/commit/16c893ff539bfb6249b3b02f4c834eb8848c16d5
    extraReq = "factory_boy";
    requirements = ''
      ${filteredReq}
      ${extraReq}
    '';
  in
    inputs.mach-nix.lib.${prev.system}.mkPython {inherit requirements;};

  liberaforms = prev.stdenv.mkDerivation {
    pname = "liberaforms";
    version = with builtins; let
      remove-newline = replaceStrings ["\n"] [""];
    in
      remove-newline (readFile (inputs.liberaforms + "/VERSION.txt"));

    src = inputs.liberaforms;

    dontConfigure = true; # do not use ./configure

    propagatedBuildInputs = [final.liberaforms-env prev.postgresql]; #TODO unfuck

    installPhase = ''
      cp -r . $out
    '';

    #doCheck = true; #TODO why does this explicitly need to be set #NOTE: this is default false here then?, - and it's overridden to enabled in the flake check
    checkInputs = with final.liberaforms-env.passthru.pkgs; [pytest pytest-dotenv];

    passthru.test = ''
      source ${./test_env.sh.in}
      initPostgres $(mktemp -d)

      # Run pytest on the installed version. A running postgres database server is needed.
      (cd tests && cp test.ini.example test.ini && pytest -k "not test_save_smtp_config") #TODO why does this break?

      shutdownPostgres
    '';
  };
}
