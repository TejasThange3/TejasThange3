"""One-off: subsets the three OFL fonts and stores them as base64 WOFF in scripts/fonts.json.
Run locally (needs fonttools); the Action only reads the JSON."""
import base64, io, json, sys
from fontTools.ttLib import TTFont
from fontTools.subset import Subsetter, Options
from fontTools.varLib.instancer import instantiateVariableFont

SRC = sys.argv[1]
TEXT = "".join(chr(c) for c in range(32, 127)) + "·°…–—’"
SPEC = [("Sora", 700, f"{SRC}/sora/Sora[wght].ttf"), ("Sora", 400, f"{SRC}/sora/Sora[wght].ttf"),
        ("JetBrains Mono", 400, f"{SRC}/jetbrainsmono/JetBrainsMono[wght].ttf"),
        ("Great Vibes", 400, f"{SRC}/greatvibes/GreatVibes-Regular.ttf")]
out = {}
for fam, w, path in SPEC:
    f = TTFont(path)
    if "fvar" in f:
        f = instantiateVariableFont(f, {"wght": w})
    o = Options(); o.flavor = "woff"; o.layout_features = ["kern", "liga", "calt"]
    s = Subsetter(o); s.populate(text=TEXT); s.subset(f)
    f.flavor = "woff"
    b = io.BytesIO(); f.save(b)
    out.setdefault(fam, {})[str(w)] = base64.b64encode(b.getvalue()).decode()
    print(fam, w, len(b.getvalue()), "bytes")
json.dump(out, open("scripts/fonts.json", "w"))
