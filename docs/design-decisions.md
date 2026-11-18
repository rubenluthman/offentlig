# Design decisions

This register lists the design and spacing decisions in Offentlig Sans: what each one solves, where it lives, what it rests on, and whether Offentlig Serif and Offentlig Mono must follow it. It is the first step of the decision audit in `ROADMAP.md`.

Units are font units of 2000 per em. PR numbers are pull requests in this repository unless they name `uswds/public-sans` (written PS #n). Dates are merge or decision dates.

## How to read the tables

Each table has the same columns:

- **Decision**: what was decided and the problem it solves.
- **Where**: the `ARCHITECTURE.md` section, decision record, test and constant, feature or glyph. "Not enforced" means no document or test holds it.
- **Source**: *Public Sans* (inherited from Public Sans at `e40fcf567`, unchanged in substance), *Offentlig* (decided in this project) or *Standard* (required by DIN 91379, the SIL Open Font License, OpenType or Unicode, or a Fontspector check).
- **Basis**: PR and date, upstream issue, the reason and what was measured.
- **S/M**: whether the decision constrains Serif and Mono. *Yes*: it carries over as it is. *Weigh*: it needs a fresh decision for each family. *No*: it belongs to the Sans outlines.

## Project and method

| ID | Decision | Where | Source | Basis | S/M |
| --- | --- | --- | --- | --- | --- |
| P1 | UFO and designspace files are the only sources. Solves: the upstream `.glyphs` files need a proprietary editor and diff poorly. | ADR-0001, `AGENTS.md` | Offentlig | 2026-11-06. Plain text, clean diffs, and every editor and fontmake read it. | Yes |
| P2 | Regular is a true master, no longer interpolated from Thin and Black (Sans design coordinate 375; Plex Serif/Mono use 400). Solves: Regular can be corrected on its own. | ADR-0001 | Offentlig | ADR-0001 (2026-11-06); Plex sources already have Thin, Regular and Bold masters. | Yes |
| P3 | Built fonts are not committed; they ship only with releases. | ADR-0002, `AGENTS.md` | Offentlig | 2026-11-06. | Yes |
| P4 | No Reserved Font Name for Offentlig. | ADR-0003 | Offentlig | 2026-11-09. The OFL allows either. Plex Serif and Mono carry IBM's "Plex" reservation, which stays. | Weigh |
| P5 | One repository and one SemVer version for all families. | `ARCHITECTURE.md` intro, `AGENTS.md` | Offentlig | 2026-11-06. | Yes |
| P6 | Remote CI on `ubuntu-latest` is the clean-build gate, and Fontspector must report no FAIL. | `.github/workflows/ci.yaml`, `AGENTS.md` | Offentlig | Fontspector universal and OpenType profiles, from #1 (2026-11-06). | Yes |
| P7 | Depart from the upstream baseline only for a reason that can be measured and seen (Sans: Public Sans; Serif: IBM Plex Serif; Mono: IBM Plex Mono). | Not enforced | Offentlig | From #26 (2026-11-12); confirmed in 0.4.0. | Yes |
| P8 | Fix every confirmed problem, wherever it came from. | Not enforced | Offentlig | 2026-11-14. The kerning series #38 – #50 fixes inherited collisions too. | Yes |
| P9 | Added strokes (slashes, bars) stay lighter than the stems in Bold and Black, as in Inter. | `tests/test_bar_thickness.py`, `tests/test_currency_strokes.py` | Offentlig | 2026-11-07, from the slashed zero and the `Ǥ` bar. Black stroke-to-stem ratios measured in Inter and five more fonts. | Weigh |
| P10 | Alternates are judged as a set: what the font should offer, not which requests turned up upstream. | Not enforced | Offentlig | 2026-11-07. Panel count per alternate measured in six fonts. | Yes |
| P11 | Upstream reasoning is context, never a veto. | Not enforced | Offentlig | 2026-11-07. | Yes |
| P12 | Before a release, check everything against Public Sans and flag anything made worse by accident. | Not enforced | Offentlig | 2026-11-09, after the first ring change in #6 shrank the Black hole. | Yes |
| P13 | The regression thresholds: a counter that loses more than 15 %, ink that changes more than 6 %, a mark gap that shrinks more than 25 %, any new collision. | Not enforced | Offentlig | 2026-11-09; confirmed in 0.4.0. | Yes |

## Build, metrics and versions

| ID | Decision | Where | Source | Basis | S/M |
| --- | --- | --- | --- | --- | --- |
| M1 | 2000 units per em (Plex 1000-UPM sources scale 2×). | Shared vertical metrics, `tests/test_metrics_and_names.py` | Public Sans | Upstream moved to 2000 in 2019 (`bfb0b5d`). | Yes |
| M2 | Vertical metrics: typo and hhea 1900 / -450 / 0, win 2315 / 495. | Shared vertical metrics, `tests/test_metrics_and_names.py` | Public Sans | Upstream commits `a2d6083` and `e3845f8` (2019). | Yes |
| M3 | Later families share `typo` and `hhea` metrics (1900 / -450 / 0); each family sets `winAscent` and `winDescent` to cover its own glyphs (Mono reaches -700 on box-drawing glyphs). | Shared vertical metrics | Offentlig | 2026-11-13, updated 0.4.0: with `USE_TYPO_METRICS` set, `win` controls clipping only. | Yes |
| M4 | `USE_TYPO_METRICS` is set. | Shared vertical metrics | Public Sans | Same `fsSelection` bits in every upstream static. | Yes |
| M5 | Weight axis 100 – 900, mapped to design 100, 220, 300, 375, 450, 525, 650, 775, 900. | Build pipeline | Public Sans | Same map in the upstream designspace. Plex Serif and Mono stop at 700. | Weigh |
| M6 | The variable default is 400. Solves: upstream variable fonts default to Thin, so an unstyled page shows hairline text. | Build pipeline, `README.md` | Offentlig | 2026-11-06; confirmed in 0.4.0 (Noto, Inter and Plex also default to 400). | Yes |
| M7 | `STAT` from the builder configuration, Regular linked to Bold. | Build pipeline | Public Sans | Same values upstream. | Yes |
| M8 | Font version `0.X.Y` becomes `0.(X × 100 + Y)` in `head.fontRevision` and name ID 5. | Build pipeline, `tests/test_metrics_and_names.py` | Offentlig | Fits SemVer into the OpenType fixed-point revision; version test from #29 (2026-11-13). | Yes |
| M9 | The italic is the upright sheared 8 degrees about half the x-height, with no optical correction. | Invariants (italic placement), `tests/test_italic_placement.py` | Public Sans | Measured shear pivot y 505 – 519 upstream; Libre Franklin sets `italicAngle = 8` around y 508. Plex Serif (14°) and Plex Mono (9.5°) have true italics. | No |
| M10 | `₩` has two intermediate drawings at design coordinates 450 and 775 (user weights 500 Medium and 800 ExtraBold). Solves: blending the three masters pinches the counters between them. | Marks and anchors (`₩ ₦`) | Offentlig | #49 (2026-11-15). Pinholes measured in between. | No |
| M11 | The `name` table says Offentlig Sans and never Public Sans. | Invariants (`name` table), `tests/test_metrics_and_names.py` | Offentlig | 2026-11-06, with the fork under a new name. | Yes |
| M12 | The default named instance has the PostScript name of the font itself. | Invariants (variable default) | Standard | Fontspector check on variable fonts. | Yes |

## Features and alternates

| ID | Decision | Where | Source | Basis | S/M |
| --- | --- | --- | --- | --- | --- |
| F1 | Superfamily feature-tag map: `ss01` swaps `g`, `ss02` swaps `l`, `ss03` round dots, `cv04` single-storey `a`, `zero` slashed `0` (Plex's other alternates map to free `cv` tags). | OpenType features, `tests/test_features.py` | Offentlig | 2026-11-06; asked for in PS #321; established as superfamily standard in 0.4.0. | Yes |
| F2 | Accented `g` and `l` follow their alternate, so one word never shows both forms. | OpenType features, `tests/test_alternate_coverage.py` | Offentlig | Asked for in PS #208; #46 (2026-11-14). | Yes |
| F3 | `salt` stays `g` and `l` (with their `fl`, `ŀ` and accented forms) and nothing else. Solves: apps with one alternates button keep the upstream behaviour. | OpenType features | Offentlig | Reason stated in `ARCHITECTURE.md`. | Weigh |
| F4 | Alternates are opt-in; no feature changes default shaping. Solves: a new default would move existing text. | Invariants (`cv` features), `tests/test_features.py` | Offentlig | #8 (2026-11-10). | Yes |
| F5 | `cv01`: a wider `J`, with the terminal at 0.34 of the cap height. Solves: default `J` is narrow (`0.55` of `U` advance at Regular). | OpenType features, `tests/test_letter_alternates.py` | Offentlig | #8 (2026-11-10), chosen from drawn candidates. Measured `J.cv01 / U`: 0.725 / 0.762 / 0.775; panel 0.74 – 0.78 at Regular. | No |
| F6 | `cv02` stays unused: the flush `G` was declined. | OpenType features | Offentlig | 2026-11-09. | Weigh |
| F7 | `cv03`: round `G` without spur, its outer lower right ~8 – 9 % fuller than the left; Black right wall thickened in 0.4.0 to match the left wall. | OpenType features; invariants (`cv03`) | Offentlig | #8; 0.4.0. One of six panel fonts has the form. | No |
| F8 | `cv04`: single-storey `a`, drawn from the font's own `d` with the stem cut at x-height; its step is the step of `q`. | OpenType features; invariants (`cv04`) | Offentlig | #8. Matches `q` and `g`. Three of six panel fonts offer one. | No |
| F9 | `cv05`: `I` with serifs, for telling `I` from `l`. | OpenType features, `tests/test_letter_alternates.py` | Offentlig | #8; PS #195 and DIN 1450. Serif length and weight follow measured Inter, Source Sans 3 and Figtree. | No |
| F10 | `cv06`: `1` with a base, opt-in. | OpenType features | Offentlig | #17 (2026-11-10). | No |
| F11 | The tabular `1` keeps its foot; no plain tabular `1` (`cv20`, PR #18 closed). | Invariants (`zero`, `cv06`) | Public Sans | Drawn on purpose upstream (PS #22); weighed again on 2026-11-09. Measured: the plain `1` fills 34 % of the cell against 45 – 48 % elsewhere; seven of eleven fonts give the tabular `1` a foot. | No |
| F12 | `zero`: slashed `0`, with a slash lighter than the stems in Black (0.39 of the ring). | Not enforced | Offentlig | #17; PS #33. Measured against Inter, Plex and Source Sans 3. Plex has its own slashed and dotted zero (mapped to `zero` / free `cv` tag). | Yes |
| F13 | `onum`: real oldstyle figures, `0 1 2` at x-height, `3 4 5 7 9` hanging no deeper than `p`, `6 8` at full height. | OpenType features; invariants (`onum`), `tests/test_wagner_oldstyle.py` | Offentlig | #13 (2026-11-10), from PS #158 item 14. Upstream `onum` pointed at copies of the lining figures. | Weigh |
| F14 | `tnum` + `onum` give tabular oldstyle figures, in either order: each `.tf.osf` glyph is the `.osf` outline placed so its ink centre is the ink centre of the same `.tf` figure (the `.tf` figures are not centred on the cell: `five.tf` sits 24 units right of centre at Regular, 48 at Black), so `onum` moves no figure sideways. Where the `.osf` and `.tf` ink widths match, the left side bearing matches too. `zero` reaches `zero.slash.tf.osf`. The tabular oldstyle `1` keeps a base (`one.cv06.osf` outline), so `cv06` changes nothing there, as with `tnum` alone. The new glyphs have no kerning groups. | Invariants (`zero`, `cv06`), `tests/test_tabular_oldstyle.py` | Public Sans | Upstream has no `.tf.osf` glyphs; Noto, Source Sans 3 and Plex keep oldstyle. Measured ink width of the `1` against the round `0` (Thin, Regular, Black): bare `1` 41, 46 and 53 %; `1` with base 72, 73 and 73 %; lining `.tf` `1` 109, 101 and 89 %. The bare `1` would leave 465 units on each side of its ink in the 1400 cell at Regular, the based one 325, and `tnum` already gives the lining `1` a base (F11). | Weigh |
| F15 | `ss03`: round dots in place of the square ones, opt-in. | OpenType features; round dots section | Offentlig | #16 (2026-11-11). Round and square dots look the same at 16 and 24 px. | No |
| F16 | `ss03` runs after the `cv` features, so a dotted alternate keeps its form with round dots. | OpenType features, `tests/test_round_dots.py`, `tests/test_alternate_coverage.py` | Offentlig | #23 (2026-11-11). Shaping order. | No |
| F17 | `aalt` lists every single-substitution feature. | OpenType features | Offentlig | OpenType convention for `aalt`. | Yes |
| F18 | No `calt`; the em dash takes the side bearings of the en dash (124 at Regular, was 371). Reverses upstream's deliberate contextual em dash. | Invariants (dashes), `tests/test_dashes.py` | Offentlig | 2026-11-06, option (a) of three; #4 (2026-11-10). | Weigh |
| F19 | Open `4`, straight `6 9`, flat-top `3` and the `ss05` set were drafted and dropped. | Not enforced | Offentlig | 2026-11-07. | Weigh |
| F20 | No distinct `b d p q` (`ss04`, PR #15 closed). | Not enforced | Offentlig | 2026-11-09; PS #288. Measured mirror overlap 1 – 8 %; no study found that distinct forms help reading. | Weigh |
| F21 | No compact `t f`, straight `y R` or alternate `ß`. | Not enforced | Offentlig | 2026-11-09: add them when users ask. | Weigh |
| F22 | No simplified `u` and no `Q` tail. | Not enforced | Offentlig | Dropped during the font survey; confirmed in 0.4.0. | Weigh |
| F23 | The italic keeps its shear without optical correction; the B2 curve correction was dropped. | Not enforced | Offentlig | 20-glyph pilot; B2 dropped on 2026-11-10: invisible at text size, and it moved anchors. PS #158 item 1. | Weigh |
| F24 | Handles at smooth points stay as in Public Sans (PR #12 closed). | Not enforced | Offentlig | 2026-11-10: no glyph changed visibly, even at 72 px, and the Black Italic infinity bent. PS #158 item 4. | Weigh |
| F25 | `locl` registers each lookup under every language it serves (AZE, CRT, KAZ, TAT, TRK; ROM, MOL; CAT). | Marks and anchors (`locl`), `tests/test_locl.py` | Standard | OpenType language systems; #26 (2026-11-12). | Yes |
| F26 | Tabular figures are 1400 wide and the ten `.tf` digits and the ten `.tf.osf` digits share one advance at every weight. | Invariants (`tnum`), `tests/test_tabular_oldstyle.py` | Public Sans | Upstream `.tf` widths. | Weigh |
| F27 | A letter alternate keeps the width rule of its plain glyph (`width(X.cvNN) = width(X) + width(base.cvNN) - width(base)`), and an `.ss03` form keeps the width of its plain glyph (except `IJ` and `OWN_WIDTH` `l.ss02` accented forms). Solves: an alternate ran into the next letter. | Marks and anchors (alternate widths), `tests/test_anchor_drift.py` | Offentlig | #24 (2026-11-11). | Yes |

## Spacing and kerning

| ID | Decision | Where | Source | Basis | S/M |
| --- | --- | --- | --- | --- | --- |
| K1 | Kerning by `public.kern1` and `public.kern2` groups, one per side shape; accented letters join their base letter's groups. | Marks and anchors (precomposed letters), `tests/test_spacing.py` | Public Sans | Upstream group scheme, largely from Libre Franklin. | Weigh |
| K2 | Every fix for a pair is a glyph-to-glyph exception, never a group value. Solves: a group value moves the plain letters too. | Invariants (accent pairs, plain pairs) | Offentlig | From #28 (2026-11-13) on. Cost: tens of thousands of kerning entries per master against 692 upstream. | Weigh |
| K3 | Pair exceptions aim at 40 units; tests fail below 30. | Invariants (pair exceptions), `tests/test_plain_pairs.py` `FLOOR`, `tests/test_accent_pairs.py` `FLOOR` | Offentlig | 40 from #19 (2026-11-11), generalised in #28 and #30; confirmed in 0.4.0. The pair tests assert the 30-unit floor. | Serif: Weigh / Mono: No |
| K4 | A pair with an accented letter keeps at least the smaller of the same pair's gap without accents and 30, less 2 (2-unit slack is measurement tolerance for 4-unit rows; closing/opening punctuation keeps 30 with 0 slack). | Invariants (accent pairs), `tests/test_accent_pairs.py` `ACCENT_SLACK` | Offentlig | #47 (2026-11-14); confirmed in 0.4.0. | Serif: Weigh / Mono: No |
| K5 | A round-dot or alternate pair keeps at least the smaller of the default pair's gap and 30, less 2 (2-unit slack is measurement tolerance for 4-unit rows). | Invariants (round dots, alternates), `tests/test_accent_pairs.py` `ROUND_DOT_SLACK`, `tests/test_alternate_pairs.py` | Offentlig | #43 (2026-11-14) and #50 (2026-11-16); confirmed in 0.4.0. | Serif: Weigh / Mono: No |
| K6 | Each master gets the smallest value that clears every static made from it; Thin and Regular change only where a static made from them collides. A test fails when they loosen a clear pair. | Invariants (accent pairs) | Offentlig | #41 (2026-11-13). | Serif: Weigh / Mono: No |
| K7 | Gaps are measured in rows 4 units tall, paired with the diagonal check (`K8`). | Invariants (pair exceptions), `tests/pairs.py` | Offentlig | #36 (2026-11-13). | Serif: Yes / Mono: Drawing only |
| K8 | Whole-font diagonal `outline_distance` check (`>= 15` units across all 18 statics, leaving out `⁄ ȉ ȑ` and ExtraBold/Black Italic `E2`), plus `>= 30` on touching pairs. | Invariants (plain pairs), `tests/ink.py` `outline_distance`, `tests/test_contact.py`, `tests/test_diagonal_gaps.py` | Offentlig | #50 (2026-11-16); whole-font 15-unit check added in 0.4.0. | Serif: Weigh / Mono: Drawing only |
| K9 | Fix every pair the rules find, including pairs no language writes (`ÍÌ`). Cost: the variable woff2 files grow by about half. | Invariants (accent pairs); `CHANGELOG.md` | Offentlig | 2026-11-14, after a size comparison with Source Sans 3, Plex, Inter and Noto Sans. | Serif: Weigh / Mono: No |
| K10 | Plain pairs (no accent) follow the same floor. | Invariants (plain pairs), `tests/test_plain_pairs.py` | Offentlig | #48 (2026-11-15). Exemption E3. | Serif: Weigh / Mono: No |
| K11 | `A` is kerned against `m n r p h b` (-20, -26, -38), never tighter than against `o`. | Invariants (`A` kerning), `tests/test_spacing.py` | Offentlig | #4 (2026-11-10); PS #259. `A n` is 0 – 2 units looser than `A o`. | No |
| K12 | A spaced en dash keeps both spaces: the Thin-only kerning of space and dashes is gone. | Invariants (dashes), `tests/test_dashes.py` | Offentlig | #4; PS #370. Fix filed upstream as PS #398. | Serif: Yes / Mono: No |
| K13 | Every letter and alternate is in a `kern1` and a `kern2` group, except a named list (E6, E7). | Invariants (groups), `tests/test_spacing.py` `EXEMPT` | Offentlig | #28 (2026-11-13). | Serif: Weigh / Mono: No |
| K14 | `ẞ` follows `B` on the right and `H` on the left (`public.kern2.N`); `Ĳ ĳ ŉ` follow their letters; `G.cv03` (`public.kern1.Gcv03` on the right, `public.kern2.O` on the left), `seven.osf` and the `cv05` letters get their own groups. | Invariants (groups), `tests/test_spacing.py` | Offentlig | #8 and #28. Measured: `ẞ` had no kerning (`ẞT` 0 against `BT` -46). | No |
| K15 | Serifed `cv05` pairs stay within 60 units (30 per 1000 em) of the plain pair's closest ink, both tighter and looser; the test checks both directions and touching. | Invariants (`cv05`), `tests/test_letter_alternates.py` | Offentlig | #28; missing `v/f/t/r`/round kerning and looseness check fixed in 0.4.0. | No |
| K16 | `ŀ` with `ss02` moves its dot right and widens to keep the right bearing of `ŀ`; `ỉ` has the advance of `ı`; `ǥ` uses the groups of `g.ss01`. | Invariants (alternate pairs) | Offentlig | #50 (2026-11-16). | No |
| K17 | `ı` (and thus `i.loclTRK`) has the advance of `i` in all six masters, matching all five sans references. | Invariants (`ı`), `tests/test_idotless.py` | Offentlig | #45 (2026-11-14); equalized across all masters in 0.4.0. | No |
| K18 | `₿` has no kerning, only side bearings. | Not enforced | Offentlig | #5 (2026-11-10). | No |

## Marks, accents and dots

| ID | Decision | Where | Source | Basis | S/M |
| --- | --- | --- | --- | --- | --- |
| D1 | Dots are square by default (period, `i`, `j`, diaeresis). | Round dots section | Public Sans | Upstream dots are four-point rectangles. | Weigh |
| D2 | The diaeresis dot is never larger than the `i` dot (`0.85 – 1.005` in `test_diaeresis_height.py`); the Regular Sans dots keep the Public Sans size. | Round dots section, `tests/test_diaeresis_height.py` | Offentlig | #20 (2026-11-11) enlarged them; #26 (2026-11-12) went back. | Weigh |
| D3 | The diaeresis is lowered 54 units at Thin and 34 at Regular; Black unchanged. Upstream puts its top at cap height. | Round dots section, `tests/test_diaeresis_height.py` | Offentlig | #20 (2026-11-11). Panel fonts set the dots 40 – 50 units closer at Thin and Regular. | Weigh |
| D4 | The italic diaeresis dots sit as far apart as in the upright. Departs from Public Sans on purpose. | Invariants (diaeresis), `tests/test_diacritics.py` | Offentlig | 2026-11-06; #6 (2026-11-10). Upright pitch 312 / 389 / 536, italic 312 / 388.5 / 536 at Thin, Regular, Black (Public Sans italic 232 / 336 / 536). | Weigh |
| D5 | The ring of `å` grows as a whole: stroke at least 40 % of the `o` stroke (43 % at Black), hole at least as wide as the stroke, outer ring round (0.93 – 1.03). | Invariants (ring), `tests/test_diacritics.py` | Offentlig | #6 (2026-11-10), `a36cc09f`. Thickening the stroke alone shrank the Black hole to a quarter of the upstream one; the ring now grows the way other fonts keep the hole, and the stroke floor went from 45 % to 40 % so the hole stays open. Measured against Inter, Source Sans 3 and IBM Plex Sans. | Weigh |
| D6 | The ring of `ǻ Ǻ` grows upward with its bottom fixed and follows the plain ring's stroke share. | Invariants (ring) | Offentlig | #6. Chosen from drawn candidates. | No |
| D7 | Italic `å` is `a` plus a ring, not a copy of `ǻ`. | Invariants (`å`) | Offentlig | Upstream bug PS #262; fix filed as PS #396. | Yes |
| D8 | Bases carry `top bottom ogonek horn`; marks carry `_top _bottom _ogonek _horn`; only bases listed in `public.openTypeCategories` attach marks. | Marks and anchors | Public Sans | Upstream anchor scheme and GDEF classes, read by ufo2ft. | Yes |
| D9 | A composite stores the `top` and `bottom` anchor that ufo2ft propagation gives. | Marks and anchors, `tests/test_anchor_drift.py` | Standard | #24 (2026-11-11). It matched ufo2ft for 503 of 572 glyphs; the rest were fixed. | Yes |
| D10 | A mark's `top` sits 31 units under its own ink top; `_top` and `_bottom` sit over the ink centre, on the slant in the italic. | Marks and anchors, `tests/test_mark_anchors.py` | Offentlig | #26 (2026-11-12). 31 is the value most marks already had. | Weigh |
| D11 | In the italic every accent composite places its mark within 10 units of the base anchor. | Invariants (italic accents), `tests/test_wagner_italic_marks.py` | Offentlig | #14 (2026-11-11); PS #158 item 2. Measured: 6 / 17 / 32 marks off before, 0 after. | Yes |
| D12 | A typed second mark in the italic sits on the slant (its anchor moved by height × tan 8 degrees). | Invariants (stacking) | Offentlig | #2 (2026-11-10). Chosen from drawn candidates. | No |
| D13 | A precomposed macron over a diaeresis, dot or tilde moves up to the typed height. | Invariants (stacking) | Offentlig | #2. The shared anchor also places the acute, grave and caron stacks, so the typed height is the one that fits all of them. | No |
| D14 | Every letter `A–Z a–z` and its alternates take typed U+0301, U+0323 and U+0331; `W w x f J g y` get `bottom` anchors; `Q` lowers its anchor up to 38 (46 italic) in Black. | Marks and anchors, `tests/test_typed_accent_bases.py` | Offentlig | #37 and #49 (2026-11-13 and 2026-11-15). The `Q` values are the smallest that keep U+0331 40 units from the tail. | Weigh |
| D15 | The DIN 91379 Latin letters are covered: composites where parts exist, drawn `Ƈ ƈ Ɨ ɨ Ǥ ǥ Ʒ ʒ` and modifier letters where they do not; Greek and Cyrillic are left out. | Invariants (DIN 91379), `tests/test_din91379.py` | Standard | #2 (2026-11-10); PS #17 and #277. | Weigh |
| D16 | The 20 pinyin letters of PS #258 keep their base width and rise above it; the tone mark clears the diaeresis. | Invariants (pinyin), `tests/test_pinyin.py` | Offentlig | #2. | No |
| D17 | Soft-dotted letters (`i j į ɨ ị`) drop their dot under a top mark. | Invariants (Soft_Dotted), `tests/test_feature_and_mark_fixes.py` | Standard | Unicode Soft_Dotted property; #38 and #44 (2026-11-13 and 2026-11-14). PS #177. | Yes |
| D18 | Typed `ị ɨ` with a top mark shape as one glyph built on `í ì ī ĩ î ĭ ï ǐ`, with their advance, marks and kerning. | Invariants (typed accents), `tests/test_typed_accent_bases.py` | Offentlig | #38 and #40 (2026-11-13). | No |
| D19 | `ċ ė ġ ż İ` keep the shared round dot (`dotaccentcomb.ss03`), which is smaller than the `i` dot; the lowercase Turkish `i` (`idotaccent.ss03`) round dot is the `i.ss03` dot. | Invariants (Soft_Dotted), `tests/test_feature_and_mark_fixes.py` | Offentlig | #44 (2026-11-14); `İ` check added in 0.4.0. | No |
| D20 | `ydotbelow` keeps its dot beside the tail, off the anchor. | Marks and anchors, `tests/test_wagner_italic_marks.py` `KEEPS_PUBLIC_SANS_DOT` | Public Sans | #49. | No |
| D21 | The o-horn and u-horn letters list the mark first, so the drift test reads their `top` and `bottom` anchors apart from the rest (`skipped_composites`, `skipped_drift`). | Marks and anchors, `tests/test_anchor_drift.py` | Public Sans | Upstream glyph structure. | No |
| D22 | The caron of `ď ľ ť Ľ` is a straight tapered wedge. Solves: the curved comma sat too close to the next stem. | Invariants (caron), `tests/test_caron_wedge.py` | Offentlig | #19 (2026-11-11), from two rounds of drawn candidates. Five of six panel fonts draw a straight wedge. | No |
| D23 | Open: the ogonek keeps the Public Sans shape until its shape is decided (ROADMAP Icebox). | Not enforced | Public Sans | 2026-11-09: only Libre Franklin matches (Offentlig `-324 – -340`, Libre Franklin `-332 – -348`); Noto Sans, Inter, Source Sans 3 and Plex are 80 – 140 units deeper. PS #158 item 6. | Weigh |
| D24 | The comma above right (U+0315) stays 40 units from the ink of `C c K k P p T t Č č`. | Invariants (DIN 91379) | Offentlig | #30 (2026-11-13). | No |
| D25 | A hook above a breve is no higher than above a circumflex; in the italic it keeps a 40-unit gap (Public Sans 54 – 69) and may stand 36 units higher. | Invariants (hook over breve), `tests/test_wagner_marks.py` | Offentlig | #10 (2026-11-11) and #30; confirmed in 0.4.0. PS #158 item 8. | No |
| D26 | In Black the tilde and macron strokes are at most 201 units; the tilde swing is at least 0.55 of its stroke. | Marks and anchors, `tests/test_wagner_marks.py` | Offentlig | #10 (2026-11-11); confirmed in 0.4.0 (200 units inside refs' 194 – 246). PS #158 items 7 and 9. | Weigh |
| D27 | Round dots are circles with the same ink area as the square dot, measured on its contour (`diameter = 2/√π × √area`; in the italic the square is a parallelogram, so its bounding box is not used), centred on the square; dots over a letter keep the square's lower edge and the dot below a letter its upper edge; italic circles are not sheared. In the Black masters `dieresiscomb.ss03` is capped at a diameter of 364 so that stacked `Udieresiscaron.ss03` stays inside `winAscent` 2315. | Round dots section, `tests/test_round_dots.py` | Offentlig | #16; switched from `1.12 × min` to equal-area in 0.4.0; the italic dots were sized from the bounding box of the slanted square at first and corrected to the true area before the release. | Weigh |
| D28 | The two round dots of the diaeresis close up with weight: gap 0.9 of the diameter at Regular, 0.4 in Black. | Round dots section | Offentlig | #16. Compared against Inter and Source Sans 3. | No |
| D29 | Round comma heads end at the square head's inner edge and keep at least 85 % of its ink (77 % in Thin). | Marks and anchors, `tests/test_mark_anchors.py` | Offentlig | #16 and #26; confirmed in 0.4.0. | No |
| D30 | The ring of `aringacute.cv04` in Black sits 60 units above its anchor. Solves: on the anchor it closes a pinhole counter. | Marks and anchors, `tests/test_outline_fixes.py` | Offentlig | #27 (2026-11-12). | No |
| D31 | `tcaron` stores its `top` at its ink top, because the caron stands beside the stem. | Marks and anchors, `tests/test_anchor_drift.py` `EXCLUDED` | Offentlig | #24 and #26. | No |
| D32 | `rinvertedbreve` places its mark on the `top` anchor of `r`; `ȓ` sits higher and gets pair exceptions. | Marks and anchors | Offentlig | #49 (2026-11-15). | No |
| D33 | U+2126 and U+03A9 map to one glyph, so NFC text keeps the font's `Ω`; no other Greek. | Marks and anchors | Offentlig | #49 (2026-11-15). | Weigh |
| D34 | `M m V v Q q ð þ Þ ŋ ĸ Ə ƒ ẞ ɨ ị` take combining marks, with anchors placed like their nearest sibling. | Invariants (typed accents) | Offentlig | #2 and #37. | No |
| D35 | Every `.ss03` glyph with a raised `top` anchor raises it by at least the amount the round dots rise; in the italic each `.ss03` mark sits on its component's anchor. | Round dots section, `tests/test_round_dots.py` | Offentlig | #24 and #25 (2026-11-11 and 2026-11-12). | No |
| D36 | The tilde inside the stacked marks of `ẫ ẵ ễ ỗ` has the stroke and wave of `tildecomb`. | Marks and anchors | Offentlig | #10 (2026-11-11), with D26. | No |

## Drawn glyphs and symbols

| ID | Decision | Where | Source | Basis | S/M |
| --- | --- | --- | --- | --- | --- |
| G1 | `ẞ` is drawn: Source Sans 3 structure with Offentlig curves, about the width of `H`, slot of 60 or more; `ß` still uppercases to `SS`. | Invariants (`ẞ`), `tests/test_outline_fixes.py` | Offentlig | #7 (2026-11-10). Measured: width 0.96 – 1.04 of `H`, panel 0.95 – 1.06. | No |
| G2 | Black `5` has no tiny curve at the join of diagonal and bowl. | Invariants (`5`) | Offentlig | #7; PS #194. | No |
| G3 | `™ ℠` top out at cap height, following Libre Franklin's proportion. `®` is unchanged. | Invariants (`™`), `tests/test_symbols.py` | Offentlig | #5 (2026-11-10); PS #216. | Weigh |
| G4 | `₿` is `B` with two short strokes and a 1400-wide tabular form. | Invariants (`₿`) | Offentlig | #5. | Weigh |
| G5 | `$ ¢ ₿` strokes are lighter in Bold and Black (upper limits of 0.60 of the `H` stem in Bold and 0.52 in Black, `test_currency_strokes.py`). | `tests/test_currency_strokes.py` | Offentlig | #5. 0.50 is Noto Sans's level; panel at Black runs from Inter 0.30 to Source Sans 3 0.65. | Weigh |
| G6 | The `ŧ` bar is lighter in Bold and Black (0.39 of the stem in Black); `Ŧ` is unchanged. | `tests/test_bar_thickness.py` | Offentlig | #2 (2026-11-10). Panel: Inter about 0.36, Libre Franklin 0.39, Noto Sans 0.45. | No |
| G7 | The `Ɨ ɨ` bars are as thick as the `Ħ ħ` bars. | `tests/test_bar_thickness.py` | Offentlig | #2. Same family of barred letters. | No |
| G8 | `ǥ` is built on the single-storey `g` with a thin bar at half x-height; `Ǥ` has a thin bar with air under it in Black. | Invariants (DIN 91379), `tests/test_gstroke_bar.py` | Offentlig | #2 and #33 (2026-11-13), from drawn candidates. | No |
| G9 | The hook of `Ƈ ƈ` is 0.55 – 0.80 in Regular and 0.62 – 0.80 of the `H` stem in Bold and Black. | Marks and anchors, `tests/test_outline_fixes.py` | Offentlig | #27 (2026-11-12); confirmed in 0.4.0. | No |
| G10 | `Ʒ ʒ` and the modifier letters `ʹ ʺ ʾ ʿ ˈ ˌ` are drawn here (`ˈ ˌ` lengthened to 440 units in 0.4.0). | Invariants (DIN 91379) | Offentlig | #2; 0.4.0. | No |
| G11 | `Ŋ` keeps the `J` hook; `? ¿` keep the Public Sans terminals. | Not enforced | Offentlig | 2026-11-09. Flat cuts like `c s` did not fit these glyphs. | No |
| G12 | The `%` and `‰` slashes are at least 0.80 of the small circles' stroke; `~ ≈` at least 0.85 of the hyphen. | Invariants (symbols), `tests/test_wagner_symbols.py` | Offentlig | #9 (2026-11-11); PS #158 items 10 and 11. | Weigh |
| G13 | Superscript and subscript `+ − = ( )` are the base sign scaled 0.629; the subscript parentheses are raised 55 units to stay inside `winDescent`. | Invariants (super and subscript), `tests/test_super_sub_signs.py` | Offentlig | #21 (2026-11-11), from drawn candidates; raising the parentheses keeps `winDescent` unchanged. | Weigh |
| G14 | Italic superior figures shift right by their rise × tan 8 degrees; subscripts shift left. | Invariants (italic figures) | Offentlig | #11 (2026-11-11); PS #158 item 12. | Weigh |
| G15 | U+2080 – U+2089 map to the `.subs` glyphs. | Invariants (subscripts) | Offentlig | Upstream bug PS #273; fix filed as PS #397. | Yes |
| G16 | The primes are copies of `primemod`; `ʰ ʳ ˢ ᵈ ᵗ ⁿ` are drawn from `h r s d t n` at the size of `ª º`, 0.65 of the bearings, and `sups` uses them only after a superior figure. | Invariants (modifier letters), `tests/test_modifier_letters.py` | Offentlig | #31 and #35 (2026-11-13). | Weigh |
| G17 | The eight arrows of PS #252 have an advance of 1446. | Invariants (arrows), `tests/test_arrows.py` | Offentlig | #3 (2026-11-10), an upstream contribution. | Weigh |
| G18 | The `₩ ₦` bars are lighter than the stems and sit further apart with weight. | Marks and anchors (`₩ ₦`) | Offentlig | #49 (2026-11-15), from drawn versions. | No |
| G19 | `Ǔ` is added, so every cased letter has its pair. | Invariants (`Ǔ`) | Standard | Fontspector `case_mapping`. | Yes |
| G20 | `acutecomb.viet`, `gravecomb.viet` and `fraction.alt` stay in the fonts, unreachable. | Marks and anchors | Offentlig | 2026-11-12. They come from Public Sans. | No |
| G21 | Helpers that are never typed (`_hook.*`, `__horn`, `_ringacute` and others) are decomposed and not exported. | Marks and anchors, `tests/test_helper_glyphs.py` | Offentlig | #30 (2026-11-13). Upstream had the skip list. | Yes |
| G22 | `Å Ä Ö å ä ö É é` exist in every font. | Invariants (Swedish letters) | Public Sans | Present upstream; the test guards them. | Yes |
| G23 | Brought back along the slant, an italic `I.cv05`, `one.cv06`, `ʒ ǯ ẞ`, modifier letter, prime or small letter has its upright bearings within 5 units; marks below are centred on the slant line. | Invariants (italic placement), `tests/test_italic_placement.py` | Offentlig | #25 (2026-11-12). Measured: up to 75 units off before. | Weigh |
| G24 | Tangent joins in drawn contours carry `smooth="yes"`. Solves: the `eraseOpenCorners` filter could remove a point in one master only and break compatibility. | Not enforced | Offentlig | #27 and #30. | Yes |

## Test exemptions

Each row is a list in a test that leaves something out, with the reason the code gives.

| ID | Exemption | Where | Source | Basis | S/M |
| --- | --- | --- | --- | --- | --- |
| E2 | The diaeresis of `ï ḯ ị̈ ɨ̈` next to tall letters (`H l i b k h d`) is held to 8 units only in ExtraBold and Black Italic; 30 units everywhere else. | `tests/test_accent_pairs.py` `DIAERESIS_FLOOR`, `tests/test_spacing.py` `DIAERESIS_TALL`, `tests/test_diagonal_gaps.py` | Offentlig | #28 (2026-11-13); narrowed in 0.4.0 after fixing the 14 regressions against Public Sans. | Weigh |
| E3 | Pairs with the fraction slash: it overlaps figures, which `frac` handles. | `tests/test_plain_pairs.py` and `tests/test_contact.py` `LEFT_OUT`, `tests/test_alternate_pairs.py`, `tests/test_diagonal_gaps.py` | Offentlig | #48 (2026-11-15). | Serif: Weigh / Mono: No |
| E4 | Pairs with `ȉ ȑ`: the double grave would need over 300 units; a narrower double grave is in the Icebox. | `tests/test_spacing.py` `LEFT_FOR_THE_ICEBOX`, `LEFT_OUT`, `tests/feature_pairs.py`, `tests/test_diagonal_gaps.py` | Offentlig | #41 (2026-11-13). | No |
| E6 | No kerning group for `Ʒ ǯ ʒ Ǯ` (rare, spaced by side bearings), `Ω` (unit sign), `π` (maths), `ƒ` (currency), `ℓ` (unit). | `tests/test_spacing.py` `EXEMPT` | Offentlig | #28. | No |
| E7 | No right-hand group for `Ŀ ŀ` and their `ss02` and `ss03` forms in the italic (`đ` joined `public.kern1.u` in 0.4.0). | `tests/test_spacing.py` `EXEMPT` | Public Sans | #28 and #30 record it as inherited; `đ` fixed in 0.4.0. | No |
| E8 | `ǒ ě` are checked only against `T Y V W`. | `tests/test_spacing.py` `ARM_ONLY` | Offentlig | #28. | No |
| E9 | `ǐ ǰ` and typed `ị̌ ɨ̌` are left out of the Thin-and-Regular test: their caron tip has its own exceptions, forced by ExtraLight. | `tests/test_spacing.py` | Offentlig | #41. | No |
| E10 | Opening punctuation before the typed `ị ɨ` is left out: fitted per glyph. | `tests/test_spacing.py` `OPENING_PUNCTUATION` | Offentlig | #42 (2026-11-13). | No |
| E11 | `candrabinducomb.ss03` has no anchor check: a dot centred in a breve. | `tests/test_anchor_drift.py` `SS03_EXCLUDED`, `tests/test_round_dots.py` | Offentlig | #24 and #16. | No |
| E12 | The accented `l.ss02` letters keep their own width: their marks are wider than the stem. | `tests/test_anchor_drift.py` `OWN_WIDTH` | Offentlig | #50 (2026-11-16). | No |
| E13 | `IJ` ligatures are not width- or placement-checked. | `tests/test_anchor_drift.py`, `tests/test_italic_placement.py`, `tests/test_alternate_coverage.py`, `tests/test_din91379.py` | Offentlig | #2, #24, #25. | No |
| E14 | The italic `G.cv03 J.cv01 a.cv04` are allowed 10 units from the upright bearings instead of 5: redrawn for the italic. | `tests/test_italic_placement.py` `REDRAWN` | Offentlig | #25 (2026-11-12). | No |
| E15 | `aringacute.cv04` in Black Italic is left out of the mark-placement tests (see D30). | `tests/test_letter_alternates.py`, `tests/test_wagner_italic_marks.py` | Offentlig | #27. | No |
| E16 | `ȋ`, and `į` in the light italics, are left out of the `ı` width check: their marks set the advance. | `tests/test_idotless.py` | Offentlig | #45 (2026-11-14). | No |
| E17 | The left side of `ᵗ`, and sides with a full-size bearing under 40, are left out of the 0.65 bearing check. | `tests/test_modifier_letters.py` | Offentlig | #35 (2026-11-13). | No |
| E18 | `ǥ` is left alone by `ss01`: it is already built on `g.ss01`. `Ǥ.cv03`, `Ɨ.cv05`, `ł.ss02` are drawn, not composed. | `tests/test_alternate_coverage.py` `DRAWN` | Offentlig | #23 and #25. | No |
| E19 | Under `ss02` only `ľ` is checked for the caron wedge. | `tests/test_caron_wedge.py` | Offentlig | #19. | No |
| E20 | Pairs that do not shape to exactly two glyphs are skipped. | `tests/test_spacing.py` and others | Offentlig | #28 onward. | Yes |
| E21 | The italic `Ẳ ẳ` may stand up to 36 units higher than the circumflex stack (see D25). | `tests/test_wagner_marks.py` | Offentlig | #30. | No |
| E22 | `Ǻ ǻ` differ from the stacked marks of `å` plus acute. | Not enforced | Offentlig | #14 (2026-11-11). | No |
