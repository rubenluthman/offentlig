# No reserved font name
Status: Active · 2026-11-09

## Decision

Offentlig Sans reserves no font name under the SIL Open Font License 1.1.

- The copyright notice in `LICENSE` and in the font `name` table carries no Reserved Font Name clause.
- Do not add "with Reserved Font Name" to any later release, file header or `LICENSE`.

## Why

The OFL lets the copyright holder reserve font names, and a derivative may not use a reserved name, so it must be renamed. Neither Public Sans nor Libre Franklin declares one. Offentlig Sans is a renamed fork so that it installs beside Public Sans; the question was whether to reserve "Offentlig" for the new work.

Under the OFL, subsetting a font counts as modification, and every web font service and many build tools subset. With a reserved name, each site that subsets Offentlig Sans would have to ship a renamed copy. Reserving no name lets subsets and forks keep the name, so web use needs no rename.

Undoing this would break web use for everyone who subsets the font, and OFL FAQ 8.1 means it could not reach releases already out anyway.

## What we gave up

- **Control over what carries the name.** A third party can publish a changed build under the family name Offentlig, and users cannot tell it from this project's release by name alone.
- **The option to reserve the name later.** OFL FAQ 8.1 states that a Reserved Font Name cannot be added to versions already released under the licence without it. If the owner later wants one, it applies only to new releases, and `v0.1.0` and later stay free of it.

## Revisit if

- Modified copies circulating under the name Offentlig cause real confusion or harm.
