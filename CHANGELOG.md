# Changelog

## [Unreleased]

- Added the pinyin tone letters and the Latin letters of DIN 91379 (including drawn Ƈ ƈ Ɨ ɨ Ǥ ǥ Ʒ ʒ), six combining marks, the modifier letters ʹ ʺ ʾ ʿ ˈ ˌ, eight arrows (← ↑ → ↓ ↖ ↗ ↘ ↙, drawn by Wayne Shih for Public Sans), the Bitcoin sign ₿ and a drawn capital sharp s ẞ (U+1E9E) in every weight and in the italic.
- Changed existing text: marks stacked on a letter now land where the precomposed letter puts them, also in the italic fonts, the bar of `ŧ` is lighter in Bold and Black, the em dash has the en dash's side bearings and no longer uses `calt`, capital `A` is kerned against `m n r p h b` and similar letters, the trademark and service mark signs sit at cap height, the strokes of `$` and `¢` are lighter in Regular, Bold and Black, and the ring of `å Å ů Ů ǻ Ǻ` is thicker with an open hole while italic diaeresis dots are spaced like the upright, and the Black `5` has a clean join where the diagonal meets the bowl.
- Added new optional forms: the `onum` feature now draws true oldstyle figures (`0 1 2` at x-height, `3 4 5 7 9` hanging below the baseline, `6 8` at full height) in every weight and in the italic; Public Sans maps `onum` to the lining figures; the opt-in letter alternates `cv01` (wider `J`), `cv03` (round `G`), `cv04` (single-storey `a`) and `cv05` (`I` with serifs), with their accented forms and the Ĳ forms that follow `cv01` and `cv05`.

## [0.1.0] - 2026-11-10

- Added Offentlig Sans, a fork of Public Sans (upstream commit `e40fcf567`) renamed to Offentlig Sans.
- Fixed four Public Sans issues: italic `å` rendered as `ǻ`, subscript digits U+2080 – U+2089 were unencoded, a spaced en dash lost its spaces in every weight except Black, and capital `Ǔ` (U+01D3) was missing.
- Split `ss01` into `ss01` (`g`) and `ss02` (`l`), and made Regular (400) the default of the variable fonts.
