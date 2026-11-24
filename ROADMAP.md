# Roadmap

## Active

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Sans
<!-- vale HouseStyle.Headings = YES -->

- Follow the three fixes this fork carries that Public Sans has not merged yet: uswds/public-sans PRs #396 (italic `å`), #397 (subscript digits) and #398 (Thin kerning of space and dashes). Checked at each release (see the release steps in [CONTRIBUTING.md](CONTRIBUTING.md#releases)).
- Some pairs of `T V W Y` before `ĩ ī ĭ ǐ`, and of `W Y` before `ȁ ȅ ȍ ȕ`, are closer than 30 units by outline distance while their row gaps pass, mostly in the heavy italic and before `ǐ` (Black Italic `Yī` 23). Bring them to 30 and empty the exemption tables in `tests/test_tvwy_gaps.py`.
- Typed `ị̏ ɨ̏` after `T V W Y` overlap the capital (outline distance 0 at every weight), because `ccmp` composes no glyph for them and they keep plain `i` kerning. Add `idotbelow_dblgravecomb` and `istroke_dblgravecomb`, like the other typed `ị ɨ` forms, and kern them like `ȉ` (K21).
- Add contextual forms of `î ï` with narrower accents after `T Y f` and brackets and next to another `î ï`. Today these pairs come closest of any in the font: by outline distance, Thin `Tï` 27.7, Black `ïî` 22.2, `î]` 25.3, `î}` 27.5, `fî` 28.3, `îS` 28.6.
- Make the wide `J` the default and retire `cv01` with the narrow `J` (F4, F5): the narrow `J` is the narrowest capital after `I`, its ink 62 % as wide as `L` at Regular. Do this after every other Offentlig Sans item above.
- Extend `cv06` and `zero` to the superscript, subscript and fraction figures and `½ ¼ ⅛ ⅓`, so text with them on never mixes two forms.
- Study joined `f` and `t` crossbars (`ff ft tt`) as drawn ligatures, and other drawn letter pairs, after 0.9.0. Both crossbars end at the x-height in every master. Render the options before deciding.
- Change the version scheme before any 0.10.0 release (M8): `versionMinor` 1000 would give the font revision 0.1000, lower than 0.900. Add a test that the revision only increases.

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
