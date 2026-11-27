# Roadmap

## Active

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Sans
<!-- vale HouseStyle.Headings = YES -->

- Fix the pairs listed in `tests/data/floor-baseline.json.gz` (K24) in the final Offentlig Sans review before 1.0.0: old small-figure pairs, typed `ị ɨ į ı i̇` pairs and some plain pairs under the nearest-ink floor. Layout is frozen until then (M8), so they wait. Rerun `scripts/write_floor_baseline.py` after each fix; the file is done when it lists nothing.
- Widen the floor test to the typed `i̇ į ị ɨ ı` + mark forms against symbols, superscripts, modifier letters and the small figures (`numr dnom subs sups`), which no floor test covers yet (`i̇̂²` is under the floor in Thin). List what it finds in the K24 baseline, then fix those pairs with the others before 1.0.0.
- Lower the group kerning `public.kern1.idotaccent` | `public.kern2.idblgrave` (999 in Black): every pair it covers has its own exception, so it moves nothing today, but a glyph added to either group would take it.
- Follow the three fixes this fork carries that Public Sans has not merged yet: uswds/public-sans PRs #396 (italic `å`), #397 (subscript digits) and #398 (Thin kerning of space and dashes). Checked at each release (see the release steps in [CONTRIBUTING.md](CONTRIBUTING.md#releases)).
- Study joined `f` and `t` crossbars (`ff ft tt`) as drawn ligatures, and other drawn letter pairs, after 0.9.0. Both crossbars end at the x-height in every master. Render the options before deciding.
- After 0.9.0, release only 0.9.x patches that leave layout unchanged (M8). Changes that move text, including joined crossbars if chosen, wait for 1.0.0, after a final review of Offentlig Sans. A 0.10.0 is not planned.

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Serif
<!-- vale HouseStyle.Headings = YES -->

- Adapt IBM Plex Serif, weights 100 – 700, with the round Offentlig dot in place of the Plex dot (D1).

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Mono
<!-- vale HouseStyle.Headings = YES -->

- Adapt IBM Plex Mono, weights 100 – 700, with the round Offentlig dot in place of the Plex dot (D1).

## Icebox

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Sans
<!-- vale HouseStyle.Headings = YES -->

- Cyrillic, to complete DIN 91379 (see public-sans issue #17). Before drawing, find an OFL font closer to Public Sans than Inter that has Cyrillic, to measure proportions from, and check whether issue #17 points to existing work. Reuse the letters Cyrillic shares with Latin, and build the lowercase letters shaped like small capitals from Offentlig's capitals, with the stroke weight corrected. For the rest, make a first draft: measure stem width, x-height, contrast, width and slant in the reference font and in Offentlig, apply those ratios to the reference font's letters as whole-letter changes, then redraw the curves and stroke ends in Offentlig's details. Check the reference font's licence first.
- Greek, to complete DIN 91379 (see public-sans issue #17). Before drawing, find an OFL font closer to Public Sans than Inter that has Greek, to measure proportions from. Reuse the capitals Greek shares with Latin, and draft the rest, above all the lowercase, the same way as Cyrillic: apply the measured ratios to the reference font's letters, then redraw them in Offentlig's details.

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Serif
<!-- vale HouseStyle.Headings = YES -->

- A Black master of our own, extending the weight axis from 700 to 900 to match Offentlig Sans.
