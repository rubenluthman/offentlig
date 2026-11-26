# Roadmap

## Active

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Sans
<!-- vale HouseStyle.Headings = YES -->

- seen: Typed `i̇` plus a top mark touches adjacent glyphs (`0.0` units across all 18 `idotless_dotaccentcomb_*` and `.ss03` glyphs in every master, e.g. `Ơi̇́` in Black and Black Italic, `i̇́ȟ`, `i̇́ǩ`, `i̇́Ȉ`, `i̇̂Î`, `Îi̇̂`, `Ĵi̇̂`, `i̇̂ĥ`, `[i̇̂`, and `i̇̂]` with `case` in Thin and Regular, and `Íi̇̀`, `ḯi̇̀`, `ĺi̇̀` in heavier weights): `groups.plist` puts all 18 glyphs in `public.kern1.u` and `public.kern2.n` with few exceptions, while the floor, accent-pair, contact, and punctuation tests omit `i̇` from their main character or loop sets (commit `4c6e7f0e`, `sources/OffentligSans-*.ufo/{groups,kerning}.plist`, `tests/test_ink_floor.py`, `tests/test_accent_pairs.py`, `tests/test_contact.py`, `tests/test_spacing.py`).
- seen: Typed `ị̏` (`idotbelow_dblgravecomb`) and `ɨ̏` (`istroke_dblgravecomb`) touch or crowd adjacent glyphs (`0.0` units for `ị̏ƒ` in Thin and Thin Italic, `13.8` / `11.9` TTF in Regular and Regular Italic; `0.0` for `ị̏ṟ` in Black and Black Italic; `7.0` / `7.1` TTF for `ɨ̏€` in Regular and Regular Italic): `groups.plist` puts them in `public.kern1.idblgrave` and `public.kern2.idblgrave` with `kern=0` against `ƒ`, `ṟ`, and `€`, and the tests omit `ƒ ṟ €` and U+030F from `SET` and `TOP_MARKS` (commit `ddbf7ac2`, `sources/OffentligSans-*.ufo/groups.plist`, `tests/test_ink_floor.py`, `tests/test_accent_pairs.py`).
- seen: Lookup `ccmp_latn_2` omits `DFLT` and all eight explicit `latn` language systems (`AZE`, `CAT`, `CRT`, `KAZ`, `MOL`, `ROM`, `TAT`, `TRK`), and invokes `lookup ccmp_latn_2;` a second time right below its inline block under `script latn;`: shaping `i̇` plus a top mark (`"i\u0307\u0301"`) leaves uncomposed `dotlessi + uni0307 + acutecomb` under `DFLT` and under `latn` for Romanian, Catalan, Turkish, or Azerbaijani (commit `4c6e7f0e`, `sources/OffentligSans-*.ufo/features.fea`).
- seen: Accented capitals `Ŧ Ţ Ț Ṭ Ṯ Ỵ` fall below the static ink floor before lowercase letters with top marks in lighter masters (all six fail in Thin Italic from `23.1` for `Ŧ Ţ Ț Ṭ Ṯ` + `ǐ` and `30.6` for `Ỵ` + `ī` against `54.6`, and in Regular Italic from `31.4` / `31.9` against `45.9`; `Ŧ` fails in upright Thin from `38.2` against `55.0` and Regular from `40.0` against `46.5`): `test_ink_floor.py` omits these six capitals from `FLOOR_CAPITALS` and checks `TY_CAPITALS` at Black and Black Italic only (commit `4c6e7f0e`, `tests/test_ink_floor.py`, `sources/OffentligSans-{Thin,Regular,ThinItalic,RegularItalic}.ufo/kerning.plist`).
- seen: Accented `W` capitals `Ẃ Ŵ Ẅ Ẇ Ẁ` fall below the ink floor before lowercase letters with top marks across five of six masters (all five in Thin `38.0` – `38.7` vs `55.0`, Regular `38.2` – `39.1` vs `46.5`, Thin Italic `37.0` – `54.1` vs `54.6`, and Regular Italic `29.3` – `39.9` vs `45.9`, plus `Ẃ` in Black Italic `27.1` – `29.7` vs `29.7`): `test_ink_floor.py` checks only `T` and `Y` capitals, and `test_tvwy_gaps.py` checks only the ceiling (`tests/test_ink_floor.py`, `tests/test_tvwy_gaps.py`, `sources/OffentligSans-{Thin,Regular,ThinItalic,RegularItalic,BlackItalic}.ufo/kerning.plist`).
- seen: Capitals `Ÿ Ẏ Ỵ` fall below the Black (`30.0`) and Black Italic (`29.7`) floors before `ǎ`, `ǧ`, and `à` when a user enables `ss03` or `cv04` alone (`26.1` for `.ss03` + `ǎ` and `29.1` for `.ss03` + `ǧ` and default + `ǎ.cv04` in Black; `28.0` for `.ss03` + `à` and default + `à.cv04`, plus `29.1` for default + `ǎ.cv04`, in Black Italic): `FEATURE_SETS` tests `ss03` and `cv04` only together, so cross-pairs miss the glyph exceptions and fall back to tighter `public.kern1.Y` group kerns (`tests/test_ink_floor.py`, `sources/OffentligSans-{Black,BlackItalic}.ufo/kerning.plist`).
- seen: Typed `į` composites and `ǐį` fall below the ink floor where kerning exceptions or tests skip them (`į̈:` with `case` alone in Black Italic is `20.9` TTF vs `29.7`; `į̌ȍ` is `17.2` TTF and `į̆ħ` is `24.3` TTF in Regular Italic vs `45.9`; `į̄ĵ` is `20.2` TTF in Regular and `23.8` TTF in Regular Italic; `ǐį` with `ss03` in Black Italic is `25.0` TTF because `icaron + iogonek.ss03` lacks the exception of plain `iogonek`): `test_ink_floor.py` omits `į`, `ȍ`, `ħ`, `ĵ`, and `case`, and `test_accent_pairs.py` checks wider row gaps (commit `315045df`, `sources/OffentligSans-{Regular,RegularItalic,BlackItalic}.ufo/kerning.plist`, `tests/test_ink_floor.py`, `tests/test_accent_pairs.py`).
- seen: Alternate small `1` (`one.cv06`) falls below the ink floor with `kern=0` in `numr`, `dnom`, and `subs` (`1€` with `cv06` + `numr` is `11.0` TTF in Thin, `11.6` TTF in Thin Italic, and `30.0` TTF in Regular; `1₣` with `cv06` + `dnom` is `12.0` TTF in Black and `11.0` TTF in Black Italic; `1ṟ` with `cv06` + `subs` is `25.9` TTF in Thin): neither `test_alternate_pairs.py` nor `test_ink_floor.py` enables `numr`, `dnom`, or `subs` (commit `2874a14c`, `sources/OffentligSans-*.ufo/kerning.plist`, `tests/feature_pairs.py`, `tests/test_ink_floor.py`).
- seen: Pre-existing encoded pairs crowd below the ink floor in characters or feature splits dropped from `test_ink_floor.py` (`łï` is `7.00` and `ïl` is `14.65` with `ss03` alone in Black Italic vs `29.69`; `ťĪ` is `15.52` and `[ḧ` with `case` is `18.41` in Black vs `30.00`; `ĺÌ` with `cv05` is `15.98` in Black Italic; `ǰÝ` is `19.95` in Regular, `22.56` in Regular Italic, and `29.07` in Black Italic): `SET` omits `Ì`, `Ī`, `Ý`, and `case`, and `FEATURE_SETS` bundles `ss02` with `ss03` (commit `ddbf7ac2`, `tests/test_ink_floor.py`, `sources/OffentligSans-*.ufo/kerning.plist`).
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
