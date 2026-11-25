# Roadmap

## Active

<!-- vale HouseStyle.Headings = NO -->
### Offentlig Sans
<!-- vale HouseStyle.Headings = YES -->

- Follow the three fixes this fork carries that Public Sans has not merged yet: uswds/public-sans PRs #396 (italic `å`), #397 (subscript digits) and #398 (Thin kerning of space and dashes). Checked at each release (see the release steps in [CONTRIBUTING.md](CONTRIBUTING.md#releases)).
- Make the wide `J` the default and keep the narrow `J` as the alternate `cv07` (F4, F5): the narrow `J` is the narrowest capital after `I`, its ink 62 % as wide as `L` at Regular. Retire `cv01`, so text that turned it on keeps the wide `J`. Do this after every other Offentlig Sans item above.
- Extend `cv06` and `zero` to the superscript, subscript and fraction figures and `½ ¼ ⅛ ⅓`, so text with them on never mixes two forms.
- Study joined `f` and `t` crossbars (`ff ft tt`) as drawn ligatures, and other drawn letter pairs, after 0.9.0. Both crossbars end at the x-height in every master. Render the options before deciding.
- No 0.10.0 (M8): `versionMinor` 1000 would give the font revision 0.1000, lower than 0.900. After 0.9.0, releases are 0.9.x patches that leave layout unchanged; changes that move text, including joined crossbars if chosen, wait for 1.0.0, after a final review of Offentlig Sans. Before 1.0.0, set the revision rule for 1.x and later (the current one breaks again at 1.10.0) and add a test that the revision only increases.

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
