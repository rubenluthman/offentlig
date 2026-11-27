# Roadmap

## Active

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Sans
<!-- vale HouseStyle.Headings = YES -->

- seen: Typed `i̇` plus a top mark touches adjacent glyphs (`0.0` units) across all 18 statics when placed next to another typed `i̇` + mark glyph or before `ị̈`, `ɨ̈`, or `į̈` – type two `i̇` + top mark forms side by side (such as `i̇̂i̇̂` or `i̇̃i̇̃`, `0.0` in all 18 statics; `i̇́i̇̀`, `0.0` in 16 statics from ExtraLight upward; `i̇̀į̈`, `i̇̀ɨ̈`, `i̇̀ị̈`, `0.0` in Black Italic), and `public.kern1.idotaccent` has no kerning entry or exceptions against `public.kern2.idotaccent` while `suite_found` checks typed forms only against single-codepoint letters (commit `20f194b9`, `sources/OffentligSans-*.ufo/{groups,kerning}.plist`, `tests/test_ink_floor.py` `suite_found`).
- seen: Typed `i̇` plus a top mark touches (`0.0` units) or crowds `.cv01` and `.cv05` capitals when square dots (`ss03`) are enabled with `cv01` or `cv05` – enable `ss03` with `cv01` or `cv05` and set `Ĵi̇̂` (`0.0` in all 18 statics), `i̇́Ȉ`..`i̇̌Ȉ` (`0.0` in Regular, Regular Italic, Black, and Black Italic), or `i̇́Ì`, `i̇́Ï`, `i̇́Ḯ`, `i̇̂Ï`, `i̇̂Ḯ` (`0.0` in Black and Black Italic; `i̇̂Î` is `0.0` in Black and `8.5` in Black Italic), because `.ss03` glyphs lack `.cv01`/`.cv05` exceptions and `ALL_SETS` separates `ss03` from `letters` while `encoded_texts` omits `i̇` (commit `20f194b9`, `sources/OffentligSans-*.ufo/kerning.plist`, `tests/test_ink_floor.py` `FEATURE_SETS`, `tests/test_accent_pairs.py` `encoded_texts`).
- seen: Typed `i̇` plus a top mark touches (`0.0` units) or crowds raised `.case` brackets and parentheses when `case` and `ss03` are both enabled – enable `case` and `ss03` and set `[i̇̂]` (`0.0` in all nine upright statics and SemiBold Italic–Black Italic), `i̇̂}` or `i̇̏}` (`0.0` in Regular–Black and Regular Italic–Black Italic), or `(i̇̂)` (`0.0` in Bold–Black and ExtraBold Italic–Black Italic, `7.7` in Bold Italic), because `.case` keys cover only the non-`.ss03` glyphs while `SINGLE_SETS` runs `case-alone` and `encoded_texts` omits `i̇` (commit `20f194b9`, `sources/OffentligSans-*.ufo/kerning.plist`, `tests/test_ink_floor.py` `SINGLE_SETS`, `tests/test_accent_pairs.py` `encoded_texts`).
- seen: Eleven capitals of the `T`, `V`, and `Y` kern groups (`Ṯ Ṫ Ţ Ț Ṭ Ẇ Ẏ Ȳ Ỵ Ỷ Ỹ`) are skipped by `tvy_group_capitals`, leaving pairs with them under the nearest-ink floor – set `Ţǐ`, `Țǐ`, `Ṭǐ`, or `Ṯǐ` in Thin Italic (`23.1` default, `22.0` on `Țǐ` and `Ṭǐ` with `ss03`, vs `54.6` floor; `Ţǐ`–`Ţḯ` also fail under Romanian `locl`), `Ỵī` (`30.6`), `Ẇǐ` in Regular Italic (`29.3` vs `45.9`), or `Ẇȗ` in Thin (`38.0` vs `55.0`) and Regular (`38.6` vs `46.5`), because `tvy_group_capitals` matches UFO source names against compiled production names (`uniXXXX`) and `FLOOR_CAPITALS` omits `Ŧ Ţ Ț Ṭ Ṯ Ỵ` (commit `20f194b9`, `tests/test_ink_floor.py` `tvy_group_capitals` and `FLOOR_CAPITALS`, `sources/OffentligSans-*.ufo/kerning.plist`).
- seen: `ROADMAP.md` defers typed forms against symbols to the `1.0.0` baseline review (`i̇̂² is under the floor in Thin`), contradicting K24 which keeps touching (`0`) pairs out of the baseline and fixes them now – type `√i̇̂`, `√i̇̃`, or `√i̇̄` in any of the 18 statics (`0.0`), `∫i̇̂` in any upright static (`0.0`), `√i̇̆` in Thin–Light upright (`0.0`), or `√i̇̈` or `∫i̇̄` in Black or Black Italic (`0.0`) (commit `01a46f2e`, `ROADMAP.md`, `docs/design-decisions.md` K24).
- seen: Encoded letter pairs outside the 112-character `SET + EXTRA_COLUMNS` column set pass all tests while crowding below the nearest-ink floor – set `łḯ` with `ss03` in Black Italic (`7.0` vs `29.7` floor), `ấȅ` in Black Italic (`15.1`), `ṯǰ` or `ṯȷ` in Thin (`15.3` vs `55.0`) and Thin Italic (`16.1`), `ổǐ` (`17.3`) or `ếǰ` (`17.4`) in Black, or `ưĦ` in Thin (`24.4`), because `suite_found` checks encoded letters only against `SET + EXTRA_COLUMNS` and `test_all_encoded_pairs_clear_diagonal_floor` checks only `{}` down to `15.0` (with `_SegPen._closePath` dropping the closing contour edge) (commit `20f194b9`, `tests/test_ink_floor.py` `suite_found`, `tests/test_diagonal_gaps.py` `DIAGONAL_FLOOR` and `_SegPen`).

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
