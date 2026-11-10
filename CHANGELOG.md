# Changelog

## [Unreleased]

- Added the pinyin tone letters and the Latin letters of DIN 91379 (including drawn Ƈ ƈ Ɨ ɨ Ǥ ǥ Ʒ ʒ), six combining marks, the modifier letters ʹ ʺ ʾ ʿ ˈ ˌ and eight arrows (← ↑ → ↓ ↖ ↗ ↘ ↙, drawn by Wayne Shih for Public Sans).
- Changed existing text: marks stacked on a letter now land where the precomposed letter puts them, also in the italic fonts, the bar of `ŧ` is lighter in Bold and Black, the em dash has the en dash's side bearings and no longer uses `calt`, and capital `A` is kerned against `m n r p h b` and similar letters.

## [0.1.0] - 2026-11-10

- Added Offentlig Sans, a fork of Public Sans (upstream commit `e40fcf567`) renamed to Offentlig Sans.
- Fixed four Public Sans issues: italic `å` rendered as `ǻ`, subscript digits U+2080 – U+2089 were unencoded, a spaced en dash lost its spaces in every weight except Black, and capital `Ǔ` (U+01D3) was missing.
- Split `ss01` into `ss01` (`g`) and `ss02` (`l`), and made Regular (400) the default of the variable fonts.
