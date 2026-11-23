# Roadmap

## Active

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Sans
<!-- vale HouseStyle.Headings = YES -->

- Follow the three fixes this fork carries that Public Sans has not merged yet: uswds/public-sans PRs #396 (italic `å`), #397 (subscript digits) and #398 (Thin kerning of space and dashes). Checked at each release (see the release steps in [CONTRIBUTING.md](CONTRIBUTING.md#releases)).
- Some pairs of `T V W Y` before `ĩ ī ĭ ǐ`, and of `W Y` before `ȁ ȅ ȍ ȕ`, are closer than 30 units by outline distance while their row gaps pass, mostly in the heavy italic and before `ǐ` (Black Italic `Yī` 23). Bring them to 30 and empty the exemption tables in `tests/test_tvwy_gaps.py`.
- Make the ring of `ǻ Ǻ` (`_ringacute`) round in Thin to Regular Italic, as the ring of `å` now is (D5): its italic outer contour is 4 – 7 % narrower than the upright one there, and the same at Black.
- Typed `ị̏ ɨ̏` after `T V W Y` overlap the capital (outline distance 0 at every weight), because `ccmp` composes no glyph for them and they keep plain `i` kerning. Add `idotbelow_dblgravecomb` and `istroke_dblgravecomb`, like the other typed `ị ɨ` forms, and kern them like `ȉ` (K21).
- Review which alternates should become the default form, which would revisit decision F4 (alternates are opt-in). Do this after every other Offentlig Sans item above.

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Serif
<!-- vale HouseStyle.Headings = YES -->

- Adapt IBM Plex Serif, weights 100 – 700.

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Mono
<!-- vale HouseStyle.Headings = YES -->

- Adapt IBM Plex Mono, weights 100 – 700.

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
