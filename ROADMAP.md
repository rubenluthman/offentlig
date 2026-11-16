# Roadmap

## Active

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Sans
<!-- vale HouseStyle.Headings = YES -->

- [ ] Audit every design and spacing decision before work on Offentlig Serif and Offentlig Mono starts, since they will reuse these rules. List each decision in a register in `docs/`: what it is, where it is enforced (`ARCHITECTURE.md`, the decision records, the tests and their exemption lists), where it comes from (Public Sans, this project, or an outside standard such as DIN 91379) and its basis, from the pull requests. For each problem a decision solves, measure how Noto Sans, Inter, Source Sans 3, IBM Plex Sans and Libre Franklin handle it. Keep those fonts in `build/reference-fonts/`, next to `build/public-sans-reference/` and ignored by git like the rest of `build/`, one folder per family with a note of its source, release and checksum, so every later check measures the same files. Antigravity reviews the register (was each decision correct, does it agree, what other solutions exist), then a new Claude session reviews it without seeing that answer. Disagreements are settled by measurement, the owner decides matters of taste, and the fixes ship in 0.4.0. Open items from the start: the diaeresis that runs into the next mark in italic `ïï ïĩ ïī īï`, the 8-unit floor for the diaeresis next to tall letters, and the pairs the tests leave alone (the fraction slash, the doubled daggers).
- [ ] Follow the three fixes this fork carries that Public Sans has not merged yet: uswds/public-sans PRs #396 (italic `å`), #397 (subscript digits) and #398 (Thin kerning of space and dashes).

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Serif
<!-- vale HouseStyle.Headings = YES -->

- [ ] Adapt IBM Plex Serif, weights 100 – 700.

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Mono
<!-- vale HouseStyle.Headings = YES -->

- [ ] Adapt IBM Plex Mono, weights 100 – 700.

## Icebox

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Sans
<!-- vale HouseStyle.Headings = YES -->

- [ ] A narrower double grave on `ȉ ȑ`, which collides with neighbours, and with `cv05` `Iȉ`.
- [ ] The shape of the ogonek. Public-sans issue #158 names it without a target, so take one from a reference design, such as Libre Franklin (the source of Public Sans), and check it on the Polish and Lithuanian letters.
- [ ] Contextual kerning for an accent typed after a base letter that has no precomposed form, after `T V W Y` (Yoruba `ọ̀ ẹ̀`, `Tc̏`).
- [ ] Cyrillic, to complete DIN 91379 (see public-sans issue #17). Before drawing, find an OFL font closer to Public Sans than Inter that has Cyrillic, to measure proportions from, and check whether issue #17 points to existing work. Reuse the letters Cyrillic shares with Latin, and build the lowercase letters shaped like small capitals from Offentlig's capitals, with the stroke weight corrected. For the rest, make a first draft: measure stem width, x-height, contrast, width and slant in the reference font and in Offentlig, apply those ratios to the reference font's letters as whole-letter changes, then redraw the curves and stroke ends in Offentlig's details. Check the reference font's licence first.
- [ ] Greek, to complete DIN 91379 (see public-sans issue #17). Before drawing, find an OFL font closer to Public Sans than Inter that has Greek, to measure proportions from. Reuse the capitals Greek shares with Latin, and draft the rest, above all the lowercase, the same way as Cyrillic: apply the measured ratios to the reference font's letters, then redraw them in Offentlig's details.

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Serif
<!-- vale HouseStyle.Headings = YES -->

- [ ] A Black master of our own, extending the weight axis from 700 to 900 to match Offentlig Sans.
