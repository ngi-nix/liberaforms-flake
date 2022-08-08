final: prev:
#TODO can I do better than this
(with builtins; seq ((hasAttr "inputs" prev) || throw "If you are calling this directly, make sure the overlays have an `inputs` attribute conforming to the flakes interface."))
{
  # TODO ? Technically, this does redundant work if you've already built the packge. Tradeoff between clean source and less build?
  liberaforms-test = prev.liberaforms.overrideAttrs (o: {
    doCheck = true;
  });
}
