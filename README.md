# Offentlig

Offentlig is a planned open-source font superfamily. Offentlig Sans is the first member: a renamed fork of [Public Sans](https://github.com/uswds/public-sans) with correct Swedish letters. Serif and Mono families are planned but not yet started.

![Offentlig Sans specimen](docs/specimen.png)

<!-- vale HouseStyle.Headings = NO -->
## Offentlig Sans
<!-- vale HouseStyle.Headings = YES -->

- Nine weights (Thin to Black) in upright and italic, plus variable fonts on the `wght` axis (default 400).
- Stylistic sets: `ss01` selects an alternate `g`, `ss02` an alternate `l`, and `salt` both. Character variants: `cv01` a wider `J`, `cv03` a round `G` without spur, `cv04` a single-storey `a`, `cv05` an `I` with serifs and `cv06` a `1` with a base; `cv01` and `cv05` also change `Ĳ`. `zero` draws a slashed `0`. The digit forms also work with `onum` and `tnum`. `ss03` replaces the square dots (`i`, `j`, `ä`, `ö`, `. : ; ! ?` and the comma shapes) with round ones.
- Oldstyle figures: the `onum` feature draws `0 1 2` at x-height, `3 4 5 7 9` hanging below the baseline and `6 8` at full height, in every weight and in the italic.
- Capital sharp s ẞ (U+1E9E) is drawn as its own letter, about as wide as `H`, in every weight and in the italic. Uppercasing ß is unchanged and still produces SS.
- Formats: OTF, TTF, variable TTF and WOFF2.

<!-- vale HouseStyle.Headings = NO -->
## Differences from Public Sans
<!-- vale HouseStyle.Headings = YES -->

Offentlig Sans starts from Public Sans `develop` at `e40fcf567` and differs in these ways:

| | Public Sans | Offentlig Sans |
| --- | --- | --- |
| Italic `å` | Renders as `ǻ` (ring with acute accent) | Renders as `å` |
| Subscript digits `₀` – `₉` | Drawn, but not mapped to U+2080 – U+2089 | Mapped, so they work as text |
| Spaced en dash | Kerning removes most of the space around ` – ` in every weight except Black (a quarter em at Regular) | Spaces kept |
| Capital `Ǔ` (U+01D3) | Missing, though lowercase `ǔ` exists | Added |
| Pinyin and DIN 91379 letters | Pinyin tone letters, many Latin Extended letters and several combining marks missing; marks stacked on a letter do not always land where the precomposed letter puts them | Added (110 composites, 18 pinyin letters and drawn Ƈ ƈ Ɨ ɨ Ǥ ǥ Ʒ ʒ), and stacked marks follow the precomposed positions, also in italic |
| Arrows `←` `↑` `→` `↓` `↖` `↗` `↘` `↙` | Missing | Added (U+2190 – U+2193 and U+2196 – U+2199), drawn by Wayne Shih for Public Sans |
| Em dash (U+2014) | Wide side bearings (371 per side at Regular), and a `calt` substitution that breaks the spacing when the space after the dash sits in another element such as a link | Side bearings of the en dash (124 per side at Regular), and `calt` and `emdash.alt` removed |
| Capital `A` before `m n r p h b` and similar letters | No kerning, so the gap is wider than before `o` | Kerned, never tighter than `A` before `o` |
| Trademark `™` and service mark `℠`, Bitcoin sign `₿`, strokes of `$` and `¢` | Marks sit low, `₿` (U+20BF) missing, strokes of `$` and `¢` heavy in Bold and Black | Marks top out at cap height, `₿` added, and the `$` `¢` `₿` strokes are lighter (about 0.56 of the stem at Bold and 0.50 at Black) |
| Ring of `å Å ů Ů ǻ Ǻ` and italic diaeresis dots | The ring is thin in Regular to Black (stroke 0.35 of the `o` stroke at Black), and the italic dots sit closer together than in the upright | The ring is thicker with an open hole (Black stroke 82, hole 100 per 1000 em), and the italic dots are spaced like the upright |
| Capital sharp s `ẞ` (U+1E9E) and Black `5` | No drawn `ẞ`, and the Black and Black Italic `5` has a small notch where the diagonal meets the bowl | `ẞ` drawn as its own letter, about as wide as `H`, in all weights and in the italic, and the Black `5` has a clean join |
| Oldstyle figures (`onum`) | The `.osf` figures are components of the lining figures, so `onum` changes nothing visible | Each of the ten figures has its own oldstyle outline in every weight and in the italic |
| Letter alternates `cv01`, `cv03`, `cv04`, `cv05` | None: `J` can read as `I` or `U`, `G` has a spur, `a` is double-storey only, and `I` has no serifs | Optional wide `J`, round `G`, single-storey `a` and serifed `I`, with their accented letters and `Ĳ`; default letters unchanged |
| Digit alternates `zero`, `cv06` | None: `0` can read as `O` and `1` as `I` or `l` | Optional slashed `0` and `1` with a base, in lining, tabular and oldstyle forms; default figures unchanged |
| Round dots `ss03` | None: the dots of `i`, `j`, the dot accents, the diaeresis and punctuation are square | Optional round dots on 108 glyphs, so every letter with a dot or diaeresis follows `i` and `j`; default letters unchanged. The dotted letters added for pinyin and DIN 91379, and the dotted alternates with `cv04` and `cv05`, keep square dots under `ss03` |
| Stylistic sets | `ss01` switches both `g` and `l` | `ss01` switches `g`, `ss02` switches `l`, `salt` both |
| Variable font default | Thin (100) | Regular (400) |

The variable font opens at Regular because Public Sans opens at Thin, so a web page that loads it without setting a weight shows hairline text. Inter, Noto Sans and Atkinson also default to 400.

The first three fixes went to Public Sans as pull requests [#396](https://github.com/uswds/public-sans/pull/396), [#397](https://github.com/uswds/public-sans/pull/397) and [#398](https://github.com/uswds/public-sans/pull/398). The `Ǔ` addition is noted on issue [#258](https://github.com/uswds/public-sans/issues/258).

## Install on macOS

Download the zip from the Releases page. Open the `otf` folder, select all files and open them in Font Book, or copy them to `~/Library/Fonts`. Offentlig Sans installs beside Public Sans without conflict because the family names differ.

## Use on the web

Self-host the WOFF2 files from the `webfonts` folder of the release.

```css
@font-face {
  font-family: "Offentlig Sans";
  src: url("OffentligSans[wght].woff2") format("woff2");
  font-weight: 100 900;
  font-style: normal;
}
@font-face {
  font-family: "Offentlig Sans";
  src: url("OffentligSans-Italic[wght].woff2") format("woff2");
  font-weight: 100 900;
  font-style: italic;
}
```

## Credits and license

- Based on Public Sans by the Public Sans project authors and the [U.S. Web Design System](https://designsystem.digital.gov), commit `e40fcf567` of https://github.com/uswds/public-sans. The U.S. Government's changes are in the public domain; the combined work is used under the OFL.
- Public Sans is based on Libre Franklin by Pablo Impallari and Rodrigo Fuenzalida, a reinterpretation of Morris Fuller Benton's 1912 typeface.
- Offentlig Sans by Ruben Luthman.

Licensed under the SIL Open Font License 1.1, see [LICENSE](LICENSE). The font has no Reserved Font Name, so a web font made by subsetting Offentlig Sans needs no rename. Authors are listed in [AUTHORS.txt](AUTHORS.txt) and [CONTRIBUTORS.txt](CONTRIBUTORS.txt).
