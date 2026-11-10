# Changelog

## [Unreleased]

- Added the pinyin tone letters and the Latin letters of DIN 91379 (including drawn Ƈ ƈ Ɨ ɨ Ǥ ǥ Ʒ ʒ), six combining marks and the modifier letters ʹ ʺ ʾ ʿ ˈ ˌ.
- Changed existing text: marks stacked on a letter now land where the precomposed letter puts them, also in the italic fonts, and the bar of `ŧ` is lighter in Bold and Black.

## [0.1.0] - 2026-11-10

- Added Offentlig Sans, a fork of Public Sans (upstream commit `e40fcf567`) renamed to Offentlig Sans.
- Fixed four Public Sans issues: italic `å` rendered as `ǻ`, subscript digits U+2080 – U+2089 were unencoded, a spaced en dash lost its spaces in every weight except Black, and capital `Ǔ` (U+01D3) was missing.
- Split `ss01` into `ss01` (`g`) and `ss02` (`l`), and made Regular (400) the default of the variable fonts.
