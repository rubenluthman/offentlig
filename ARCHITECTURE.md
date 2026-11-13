# Architecture

Offentlig is one repository and one SemVer version for the whole superfamily. Families share one tree and are told apart by file name in `sources/` and by subfolder in the build output. Units are font units of 2000 per em unless a number says otherwise.

## Layout

```text
sources/
  OffentligSans.designspace, OffentligSans-Italic.designspace
  OffentligSans-{Thin,Regular,Black}.ufo, OffentligSans-{ThinItalic,RegularItalic,BlackItalic}.ufo
  config-OffentligSans.yaml        gftools builder configuration
tests/                             pytest suite, runs against the built fonts
Makefile                           venv, build, test, qa, proof, specimen, social-preview, verify
requirements.txt, requirements-qa.txt   Python dependencies for the build and for QA
scripts/verify_commit.sh           pre-commit verification
scripts/check_prose.sh             house style check (Vale), run by verify_commit.sh and prose.yaml
scripts/check_conflict_markers.sh  fails on leftover git conflict markers, run by verify_commit.sh and prose.yaml
scripts/release_notes.sh           CHANGELOG.md section for one version, used as the release notes
scripts/proof_page.py              tester page from docs/proof/allemansratten.txt (make proof)
scripts/specimen.py                docs/specimen.png and the social preview (make specimen, make social-preview)
scripts/fsp_summary.py             summary of the Fontspector reports (make qa)
.github/workflows/ci.yaml          CI: build, test, Fontspector; draft release with zip and LICENSE on v* tags
.github/workflows/prose.yaml       CI: conflict markers and house style check on changes to prose files
docs/                              contributor docs, docs/adr/, docs/proof/ (tester text) and docs/specimen.png
fonts/OffentligSans/{otf,ttf,variable,webfonts}/    build output, gitignored
build/                             Fontspector and proof output, gitignored
```

Later families add `OffentligSerif*` and `OffentligMono*` files next to these and `fonts/OffentligSerif/` and `fonts/OffentligMono/` in the output.

## Build pipeline

```mermaid
flowchart LR
  A[designspace + UFO masters] --> B[gftools builder]
  B --> C[fontmake: variable TTF]
  B --> D[fontmake: static TTF and OTF]
  C --> E[STAT table, gftools-fix-font]
  D --> E
  E --> F[WOFF2]
```

- Each style (upright, italic) has three masters on the `wght` axis: Thin (design 100), Regular (design 375) and Black (design 900). The axis map sends user weights 100 – 900 to design coordinates 100, 220, 300, 375, 450, 525, 650, 775 and 900.
- The variable default is Regular (400). Static instances are declared in each designspace.
- The `STAT` table comes from `config-OffentligSans.yaml`. Regular links to Bold.
- Font version follows the package version: `0.X.Y` becomes `0.(X × 100 + Y)`, so `0.1.0` is `0.100` and `0.2.0` is `0.200` (`head.fontRevision`, name ID 5). The sources carry it as `versionMajor` and `versionMinor` in every master's `fontinfo.plist`.

## Shared vertical metrics

These values are identical in every master and are enforced by `tests/test_metrics_and_names.py`. They stay as in Public Sans and become the shared values for later families.

| Key | Value |
| --- | --- |
| `unitsPerEm` | 2000 |
| `typoAscender` | 1900 |
| `typoDescender` | -450 |
| `typoLineGap` | 0 |
| `hheaAscender` | 1900 |
| `hheaDescender` | -450 |
| `hheaLineGap` | 0 |
| `winAscent` | 2315 |
| `winDescent` | 495 |

`USE_TYPO_METRICS` is set in every font.

## OpenType features

| Tag | Effect |
| --- | --- |
| `ss01` | Alternate `g` (`g.ss01`) |
| `ss02` | Alternate `l` (`l.ss02`), also in the `fl` ligature (`fl.ss02`) and the Catalan `ŀ` (`ldot.ss02`, `ldot.ss02.ss03` under `ss03`), so one word never shows both forms of `l` |
| `salt` | Both alternates, with the `fl` and `ŀ` forms of `ss02`, and nothing else, as in Public Sans. Apps that offer one alternates button use `salt`, so it keeps doing what it did there; later alternates are reached only by their own tags. |
| `cv01` | Wider `J` (`J.cv01`, `Jcircumflex.cv01`) and the Ĳ forms that use it |
| `cv03` | Round `G` without spur, with its accented forms |
| `cv04` | Single-storey `a`, with its accented forms |
| `cv05` | `I` with serifs, with its accented forms and the Ĳ forms that use it |
| `ss03` | Round dots in place of the square ones: `i`, `j`, the dot accents and diaeresis with every letter built on them, `. : ; ! ? ¡ ¿ ÷ …` and the comma heads (181 `.ss03` glyphs). It runs after the `cv` features, so a dotted letter alternate has its own round-dot form (`adieresis.cv04.ss03`) and `ss03` keeps the alternate |
| `cv06` | `1` with a base (`one.cv06`, `one.cv06.osf`); the tabular `1` already has its own base |
| `zero` | Slashed `0` (`zero.slash`, `zero.slash.tf`, `zero.slash.osf`) |
| `onum` | Oldstyle figures: `0 1 2` at x-height, `3 4 5 7 9` hanging below the baseline, `6 8` at full height (`zero.osf` to `nine.osf`) |
| `aalt` | Collects every single-substitution feature in the font (`locl`, `subs`, `sinf`, `sups`, `numr`, `dnom`, `frac`, `ordn`, `lnum`, `pnum`, `tnum`, `onum`, `salt`, `ss01`, `ss02`, `ss03`, `cv01`, `cv03`, `cv04`, `cv05`, `cv06`, `zero`) |

## Invariants enforced by tests

- Italic and upright `å` differ from `ǻ`.
- U+2080 – U+2089 map to the `.subs` glyphs.
- U+207A – U+207E and U+208A – U+208E (superscript and subscript `+ − = ( )`) map to `plussuperior` and the other `*superior` glyphs and to `plus.subs` and the other `.subs` glyphs, which are the base sign scaled 0.629 and raised like the figures; `sups`, `subs` and `sinf` substitute them.
- A spaced en dash keeps both spaces at every weight.
- The em dash has the en dash's side bearings, no `calt` feature exists, and an em dash between two spaces shapes the same whether or not the text is split into runs after the dash.
- `A` is kerned against the stem-letter group (`m n r p h b`, accented n and r letters included) at every weight, in upright and italic, and never tighter than against `o` (`-20`, `-26`, `-38` in Thin, Regular, Black).
- The `name` table uses Offentlig Sans as the family and never Public Sans, and name ID 5 equals `Version versionMajor.versionMinor` and `head.fontRevision` equals `versionMajor.versionMinor` of the masters in every static and variable font (`tests/test_metrics_and_names.py`).
- Å Ä Ö å ä ö É é exist in every font.
- The variable default is 400, and the default named instance has the same PostScript name as the font itself.
- `Ǔ` (U+01D3) exists, so every cased letter has its counterpart (Fontspector `case_mapping`).
- The ring stroke is at least 45 % of the `o` stroke and the outer ring stays round (width to height 0.93 – 1.03) at every weight, and the ring of `ǻ` and `Ǻ` follows the plain ring's stroke share.
- The two dots of the diaeresis sit as far apart in the italic as in the upright, at every weight.
- The italic masters are sheared about half the x-height. Brought back along the 8 degree slant (`x - (y - xHeight / 2) * tan 8`), an italic glyph has the left and right bearing of its upright glyph: within 5 units for `I.cv05`, `one.cv06`, `one.cv06.osf`, `ʒ`, `ǯ`, `ẞ` and the modifier letters `ʹ ʺ ˈ ˌ ʾ ʿ`, the primes `′ ″ ‴` and the small letters `ʰ ʳ ˢ ᵈ ᵗ ⁿ`, and the ink of the combining marks below (U+0323, U+0331, U+032E) is centred on the slant line through `_bottom`. The italic superior and subscript `9` have the width of `nine.numr` and `nine.dnom` (`tests/test_italic_placement.py`, `tests/test_wagner_italic_marks.py`).
- `™` (U+2122) and `℠` (U+2120) top out at cap height, within 20 units.
- U+20BF (Bitcoin sign) is mapped in every font and has a 1400-wide tabular form under `tnum`.
- The 20 pinyin letters of uswds/public-sans#258 (Ǎ Ǐ Ǒ Ǔ Ǖ Ǘ Ǚ Ǜ Ḿ Ǹ and lowercase) are mapped, keep the width of their base letter and rise above it; the tone mark of a stacked letter clears the diaeresis.
- `M` and `m` take combining marks: base plus mark shapes to the same ink extents as the precomposed Ḿ ḿ Ǹ ǹ Ǎ Ǐ Ǒ ǎ ǐ ǒ.
- The DIN 91379 letters that are composites of existing parts (Ĳ ĳ ŉ and the Latin Extended-A/B and Extended Additional letters listed in uswds/public-sans#277) are mapped and keep the advance of their base letter. U+0310, U+0315, U+0325, U+032E and U+0331 exist as zero-width marks. The comma above right (U+0315) stays at least 40 units from the ink of `C c K k P p T t Č č` at every weight, upright and italic (the `_top` anchor of the mark is 65 units lower in Black, so the mark rides higher there).
- Combining marks attach through GPOS on every base the DIN 91379 sequence list needs (F f K k M m P p T t d and the others in `tests/test_din91379.py`), and a second mark on an accented letter clears the first (mark-to-mark stacking).
- The prime marks U+2032 – 2034 (`minute`, `second`, `tripleprime`) are one, two and three copies of `primemod` at the pitch of `dblprimemod`, so they match ʹ ʺ. The small letters ʰ ʳ ˢ ᵈ ᵗ ⁿ (U+02B0, U+02B3, U+02E2, U+1D48, U+1D57, U+207F) are drawn from h r s d t n, scaled to the height of `ª º` and given the stem weight of `ª` by a slightly heavier outline in each master (within 10 percent, in every weight, upright and italic). They stand on the baseline of the superior figures (the bottom of `ʳ ⁿ` and the overshoot of `ˢ ᵈ` within 20 units of `onesuperior`; 8 degrees slanted in the italic) and have 0.65 of the side bearings of h r s d t n. `ᵗ` has a left bearing of at least 50 units at Black, so `⁴ᵗ` keeps clear. `sups` maps h r s d t n to them only after a superior figure, a superior parenthesis or another small letter (a chained contextual lookup after the lookup for figures and signs), so `1er`, `Ste` and `century` keep their letters; `ordn` is unchanged (`tests/test_modifier_letters.py`).
- `V v Q q ð þ Þ ŋ ĸ Ə ƒ ẞ ɨ ị` take combining marks: each has a `top` anchor placed like its nearest sibling (`W`, `w`, `O`, `o`, `b`, `P`, `n`, `k`, `f`, `B`; `ð` sits at 1460, above its stroke), and each has a `bottom` anchor (under the descender end on `q þ ƒ ŋ`, which have a descender). `ị` and `ɨ` drop the dot under a top mark, like `i`. With U+0301, U+0300, U+0304, U+0303, U+0302, U+0306, U+0308 or U+030C, `ccmp` replaces the pair with one glyph (`idotbelow_acutecomb`, `istroke_brevecomb` and so on, `.ss03` for round dots) built on the precomposed `í ì ī ĩ î ĭ ï ǐ`, so the advance, mark position and kerning match them; the typed accent then clears the next letter by at least 30 units at every weight. Any other top mark swaps the letter for `idotbelow.dotless` or `istroke.dotless` (`tests/test_typed_accent_bases.py`).
- The letters drawn for DIN 91379 (Ƈ ƈ Ɨ ɨ Ǥ ǥ Ʒ ʒ, the modifier letters ʹ ʺ ʾ ʿ ˈ ˌ, and U+030D, U+035F) are mapped in every font. The barred and hooked letters keep the advance of their base letter (ǥ is built on the single-storey `g.ss01`), Ʒ has a flat top at cap height, ʒ descends below the baseline, and U+035F is a fixed-length bar that reaches into the following letter. Ǯ and ǯ are composites of Ʒ or ʒ and a caron, with the caron above the letter.
- `ss01` swaps the plain `g` only. `ss02` swaps the plain `l`, `fl` and `ŀ` (Catalan `l·l` shapes as `ldot.ss02` and `l.ss02`), and `salt` swaps both letters with those forms. The accented forms `ĝ ğ ġ ģ ĺ ļ ľ ł` do not change. `fl.ss02` is in the kerning groups of `fl` on the left and of `l.ss02` on the right; `ldot.ss02` is in those of `l.ss02` on the left and of `ldot` on the right (`tests/test_features.py`, `tests/test_spacing.py`).
- In the italic masters every accent composite places its mark's `_name` anchor within 10 units of the base's `name` anchor.
- `cv01` (wider `J`), `cv03` (round `G`), `cv04` (single-storey `a`) and `cv05` (`I` with serifs) each swap their letter and its accented forms only. Every encoded letter built on `G`, `a` or `I` has its alternate, with its marks placed on the alternate base's anchors (`tests/test_alternate_coverage.py`). No feature changes default shaping, and `salt` stays `g` and `l`.
- In `cv03` the outer lower right is about 7% fuller than the lower left in the diagonal part, in every master. The `cv04` step is the step of `q`.
- `zero` (slashed `0`) and `cv06` (`1` with base) are opt-in. The default digits never change, and each alternate has matching tabular and oldstyle forms, except the `1`, whose tabular form already has its own base. The small digits (numerators, subscripts) keep the default design.
- The 16 `.cv05` letters (`I.cv05` and its accented forms) have their own kerning groups `public.kern1.Icv05` and `public.kern2.Icv05`, because the serifs reach into the side bearings. Each pair carries the plain `I` value plus the extra space that keeps the serifed pair within 20 units of the plain pair's closest ink distance; `tests/test_letter_alternates.py` fails if any pair with a letter touches or comes closer than 30 units.
- Every encoded letter and every `cv` or `ss` form of a letter is in a `kern1` and a `kern2` group, except the letters named in `tests/test_spacing.py`. `ẞ` follows `B` on the right and `H` on the left, `Ĳ ĳ ŉ` follow the letters they are made of, the `G.cv03` forms have their own right-hand group `public.kern1.Gcv03` (the pairs of `G` plus the space that makes them close like `O`), and `seven.osf` has its own left-hand group `public.kern2.sevenosf`. Pair exceptions aim at a gap of 40 units (12 for the diaeresis of `ï ő`, which the tests hold to 8) between the marks of `ǐ ǰ ḯ ǒ ě ḻ ṟ ṯ`, the hook of `ƈ` and their neighbours; the tests fail below 30. The same holds for every accented lowercase letter after the `kern1` groups of `T`, `V` and `Y` (which hold `W` and the accented capitals): each pair is a group-to-glyph exception, and the masters are fitted so that no weight between them closes below 30. This holds with `cv04` (single-storey `a`) and `ss03` (round dots) on as well, alone or together. The tests measure the ink gap in rows 4 units tall, because 20-unit rows missed thin mark tips. Two further groups of pairs follow the same rule, with their own test: the circumflex of `î` before the lowercase letters (`îl îb îh îk îi`), and `Ơ Ư` with their accented forms before the lowercase that follows (`Ời Ơi Ườ Ưi`); both closed in the heavy weights of Public Sans. A third group, the accented `i` letters (`í î ï ĩ ī ĭ ǐ ȉ ȋ ḯ`, also with `ss03`) against `) ] } ? ! ' " ’ ” » ›`, uses glyph-to-glyph exceptions on the same 40-unit aim and 30-unit floor. The typed `ị` and `ɨ` with an acute, grave, circumflex, macron, tilde, breve, diaeresis or caron shape as one glyph (`idotbelow_acutecomb`, `istroke_brevecomb` and the others) and have the same exceptions, copied from the precomposed letter and raised where the Black masters stay under the aim; the same glyphs carry extra exceptions before `H l n i` so that no weight closes below 30. The pairs are in all six masters, so they interpolate. These are glyph-to-glyph exceptions for `î` and `kern1` group-to-glyph exceptions for `Ơ Ư`.
- U+1E9E is mapped and wider than `S`; U+00DF still maps to `germandbls`.
- The ten `.tf` digits share one advance at every weight, static and variable (`tnum`).
- Black and Black Italic `five` have no tiny smooth curve at the join between the diagonal and the bowl.
- The eight arrows U+2190 – U+2193 and U+2196 – U+2199 (from public-sans pull request #252) are mapped in every font, have an advance of 1446 and outlines. Their bounding-box centre lies within 12 units of the `plus` centre for the four axis arrows and within 70 units for the four diagonals.
- `leftArrow` and `rightArrow` have the same bounding-box height.
- `onum` draws `0 1 2` at x-height, `3 4 5 7 9` hanging from x-height below the baseline, and `6 8` at full figure height, each with its own outline.
- Every glyph that carries a dot has an `.ss03` form in every font, and every dotted `.cv03`, `.cv04` or `.cv05` letter has a `.cvNN.ss03` form; `ss03` substitutes all of them (composites use the `.ss03` forms of their parts), shaping with `ss03` off contains no `.ss03` glyph, and `ss03` keeps every advance.
- The `percent` and `perthousand` slashes are at least 0.80 of the stroke of the small circles in `%`, and the `asciitilde` and `approxequal` strokes are at least 0.85 of the hyphen thickness, at every weight in both styles.
- In the italic styles a superior figure sits at its numerator figure shifted right by its rise times tan 8 degrees; in the upright styles it is not shifted. A subscript figure sits at its denominator figure shifted by its drop times tan 8 degrees (to the left) in the italic styles, within 2 units.

## Marks and anchors

- A base glyph attaches marks only if `public.openTypeCategories` in `lib.plist` lists it as `base`; anchors on an unlisted glyph are ignored by the mark feature writer.
- Bases carry `top`, `bottom`, `ogonek` and `horn` anchors; combining marks carry the matching `_top`, `_bottom`, `_ogonek` and `_horn`.
- Top marks also carry a `top` anchor above their own ink, which produces the mark-to-mark lookup. A precomposed letter with a top mark carries a `top` anchor above that mark, so a further mark stacks instead of colliding.
- Precomposed letters are component glyphs: the base letter plus mark glyphs offset to the base's anchors, with an upper mark stacked above the lower one. They join every kerning group of their base letter in `groups.plist`.
- The stored `top` and `bottom` anchor of a base-plus-mark composite is the anchor ufo2ft's propagation gives: the anchor of the last mark above (or below) the base, moved by the mark's offset. It must be stored, because a typed mark attaches to it, and an alternate built on `.cv03`, `.cv04` or `.cv05` otherwise keeps the base letter's height. `tests/test_anchor_drift.py` fails if a stored anchor is more than 1 unit from the propagated one (ligatures, glyphs mixing contours and components, and mark-first composites such as the o-horn and u-horn letters are not checked), and checks that each mark of a `.ss03` glyph is on its anchor or at the offset the plain glyph has it.
- A letter alternate keeps the width rule of its plain glyph: `width(X.cvNN) = width(X) + width(base.cvNN) - width(base)` (base is `G`, `a`, `I` or `J`), and an `.ss03` form has the width of its non-`.ss03` glyph, so the wider italic accented `a` stays wider and an alternate never runs into the next letter (checked within 0.5 units by `tests/test_anchor_drift.py`; the `IJ` ligatures are not checked).
- A mark's `top` sits 31 units under its own ink top (`ringcomb`, `macroncomb`, `_ringacute`), in the italic on the slant line through `_top`. A `_bottom` or `_top` anchor lies under or over the ink centre of the mark, in the italic on the slant line through it. `C c S s` carry `ogonek` and `horn` anchors like `O o`, and `tcaron` stores a `top` at its ink top because the caron stands beside the stem (`tests/test_mark_anchors.py`, `tests/test_din91379.py`). Every encoded glyph has the same non-underscore anchors upright and italic.
- The round comma heads (`commaaccentcomb.ss03`, `commaturnedabovecomb.ss03`) end at the same inner edge as the square heads and carry at least 85 % of their ink (77 % in Thin).
- `locl` registers each lookup under every language it serves: the dotted `i` for AZE, CRT, KAZ, TAT and TRK, the comma forms of Ş Ţ ş ţ for ROM and MOL, and the Catalan `l·l` for CAT (`tests/test_locl.py`).
- Drawn parts that overlap their base (the hooks of Ƈ and ƈ) are separate component glyphs named `_hook.*`. They are listed in `public.skipExportGlyphs` in the lib of both designspaces (the builder reads the designspace lib, not the UFO lib), together with the other helpers that are never typed (`__horn`, `espaciador`, `_ringacute`, `_j-hook`, `_dot`, `_emdash`). The builder decomposes them into the glyphs that use them, so no built font contains them (`tests/test_helper_glyphs.py`). Tests that measure the ring of `_ringacute` read it from the source masters. Tangent-continuous joins in drawn contours carry `smooth="yes"`; without it the `eraseOpenCorners` filter can remove a point in one master only and break compatibility.
- `aringacute.cv04` in Black and Black Italic carries its ring 60 units above the `_top` anchor. Its other counters stay at two at every weight (`tests/test_outline_fixes.py`).
- The slot of `ẞ` between the stem and the lower terminal is 60 units or more at every weight.
- The hook of `Ƈ ƈ` is 0.62 – 0.80 of the `H` stem in Bold and Black.
- `acutecomb.viet`, `gravecomb.viet` and `fraction.alt` are in the fonts, but no cmap entry, feature or component reaches them. They come from Public Sans and are kept.
- The combining tilde swing is at least 0.55 of its stroke at every weight, and in Black the tilde and macron strokes are at most 201 units.
- The tilde inside the stacked marks (`uni03060303`, `uni03020303`: `ẫ ẵ ễ ỗ` and capitals) has the stroke and wave of `tildecomb`.
- A hook above a breve (`Ẳ`, `ẳ`) reaches no higher than the same hook above a circumflex in the upright. In the italic the hook is raised along the slant (28 units at Thin and Regular, 34 at Black), so its ink gap to the breve is at least 40 units at every weight (Public Sans: 54 – 69); the italic mark may then stand up to 36 units higher than the circumflex stack. Both rules are in `tests/test_wagner_marks.py`.

## Round dots (`ss03`) and the diaeresis

- The diaeresis dot is never larger than the `i` dot: 0.93 – 1.0 of its width and 0.89 – 1.0 of its height in every master, as in Public Sans (`tests/test_diaeresis_height.py`).
- Each round dot is a circle with a diameter of 1.12 times the smaller side of the square dot it replaces, centred on that dot in every master. Italic circles are not sheared.
- Dots over a letter keep the lower edge of the square dot, so the clearance to the letter is unchanged; the dot below a letter keeps its upper edge.
- The two dots of `dieresiscomb.ss03` sit closer together as the weight rises: the gap between them is 0.9 times the dot diameter at Regular and 0.4 times in Black. Thin keeps the spacing of the square dots.
- The diaeresis is lowered at Thin (54 units) and Regular (34 units); Black is unchanged. The Regular square dots keep the size they have in Public Sans (180.8 by 178.8). `dieresiscomb.ss03` follows: its dots keep the lower edge of the square dots, and at Regular the round dots keep their diameter of 200.2, which is 1.12 times the smaller side of the square dot. The `top` anchor of both marks and the upper mark of the precomposed stacks (ǖ ǘ ǚ ǜ ȫ Ǟ and the capitals) move with the dot tops, so the gap above the dots is unchanged; in the italic masters the dots and the anchor also shift along the 8 degree slant (checked by `tests/test_diaeresis_height.py`).
- Every `.ss03` glyph with a raised `top` anchor on its plain counterpart has the same anchor, plus the amount by which the round dots rise above the square ones (never less), so a mark stacked on a dotted letter clears the dots by at least the default gap (checked by `tests/test_round_dots.py`).
- In the italic masters every `.ss03` composite places each mark so that the mark's `_top` or `_bottom` anchor lies on the anchor of the preceding component that carries that name (checked by `tests/test_round_dots.py`).

## Documents

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for workflow and [docs/adr/README.md](docs/adr/README.md) for decision records.
