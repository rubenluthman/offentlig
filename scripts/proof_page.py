"""Build a self-contained tester page (weight waterfall, editorial view, feature view) from docs/proof/allemansratten.txt.

Writes build/proof/allemansratten.html, which loads the built WOFF2 files by relative path.
"""
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "proof" / "allemansratten.txt"
OUT = ROOT / "build" / "proof" / "allemansratten.html"
WEIGHTS = [("Thin", 100), ("ExtraLight", 200), ("Light", 300), ("Regular", 400), ("Medium", 500),
           ("SemiBold", 600), ("Bold", 700), ("ExtraBold", 800), ("Black", 900)]

sections = {}
current = None
for block in SRC.read_text(encoding="utf-8").split("\n"):
    if block.startswith("# "):
        current = block[2:]
        sections[current] = []
    elif block.strip() and current:
        sections[current].append(block)

statute = [(h, p) for h, p in sections.items() if not h.startswith(("Source", "Supplementary"))]
supp = sections["Supplementary strings (not statutory text)"]
source = " ".join(sections["Source"])

editorial = "".join(
    f"<h2>{html.escape(h)}</h2>" + "".join(f"<p>{html.escape(x)}</p>" for x in paras) for h, paras in statute)
waterfall = "".join(
    f'<div class="row"><span class="label">{n} {w}</span>'
    f'<span style="font-weight:{w}">{html.escape(statute[0][1][-1][:60])}</span></div>'
    for n, w in WEIGHTS)
features = "".join(f"<p>{html.escape(x)}</p>" for x in supp)

page = f"""<!doctype html>
<html lang="sv"><head><meta charset="utf-8"><title>Offentlig Sans tester</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@font-face {{ font-family: "Offentlig Sans"; src: url("../../fonts/OffentligSans/webfonts/OffentligSans[wght].woff2") format("woff2"); font-weight: 100 900; font-style: normal; }}
@font-face {{ font-family: "Offentlig Sans"; src: url("../../fonts/OffentligSans/webfonts/OffentligSans-Italic[wght].woff2") format("woff2"); font-weight: 100 900; font-style: italic; }}
body {{ background: #fff; color: #000; font-family: "Offentlig Sans", sans-serif; margin: 0 auto; max-width: 46rem; padding: 2rem 1rem 4rem; line-height: 1.5; }}
h1 {{ font-size: 2.25rem; margin: 0 0 .25rem; }} h2 {{ font-size: 1.25rem; margin: 2rem 0 .5rem; }}
.note {{ font-size: .8rem; color: #444; }}
.row {{ display: flex; gap: 1rem; align-items: baseline; font-size: 1.5rem; white-space: nowrap; overflow: hidden; }}
.label {{ flex: 0 0 9rem; font-size: .75rem; font-weight: 400; color: #444; }}
.ital {{ font-style: italic; }}
.tnum {{ font-variant-numeric: tabular-nums; }} .ss01 {{ font-feature-settings: "ss01"; }} .ss02 {{ font-feature-settings: "ss02"; }}
</style></head><body>
<h1>Offentlig Sans</h1><p class="note">{html.escape(source)}</p>
<h2>Weight waterfall</h2>{waterfall}
<h2>Editorial, 18 px</h2><div style="font-size:18px">{editorial}</div>
<h2>Editorial, italic</h2><div class="ital" style="font-size:18px">{"".join(f"<p>{html.escape(x)}</p>" for x in statute[1][1])}</div>
<h2>Features and supplementary strings</h2>
<div style="font-size:1.25rem">{features}
<p class="tnum">tnum: 1994 1111 2222 3333</p><p class="ss01">ss01: glad lilla gula igloo</p><p class="ss02">ss02: glad lilla gula igloo</p></div>
</body></html>"""
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page, encoding="utf-8")
print(OUT)
