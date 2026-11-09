---
status: accepted
date: 2026-11-09
deciders: Ruben Luthman
tags: [licence, release]
---

# ADR-0003: No Reserved Font Name

## Context and Problem Statement

The SIL Open Font License 1.1 lets the copyright holder reserve one or more font names. A derivative may not use a reserved name, so the work must be renamed. Neither Public Sans nor Libre Franklin declares one. Offentlig Sans is a renamed fork so that it installs beside Public Sans; the question is whether to reserve "Offentlig" for the new work.

Under the OFL, subsetting a font, which every web font service and many build tools do, counts as modification. With a reserved name, each site that subsets Offentlig Sans would have to ship a renamed copy.

## Considered Options

1. **Reserve "Offentlig".** Forks and subsets cannot pass as the original. Every subset served from a site would need a new name.
2. **Reserve no name.** Subsets and forks keep the name, so web use needs no rename. Nothing stops a modified copy from using the name.

## Decision Outcome

Option 2.

### Invariants & Negative Constraints

- The copyright notice in `LICENSE` and in the font `name` table carries no Reserved Font Name clause.
- Do not add "with Reserved Font Name" to any later release, file header or `OFL.txt`.

### Negative Consequences

- **A modified copy can keep the name Offentlig.** Verified worst case: a third party can publish a changed build under the same family name, and users cannot tell it from this project's release by name alone. Set aside: control over what carries the name.
- **Irreversible for releases already out.** OFL FAQ 8.1 states that a Reserved Font Name cannot be added to versions already released under the licence without it. Verified worst case: if the owner later wants a reserved name, it applies only to new releases, and `v0.1.0` and later stay free of it. Set aside: the option to reserve the name after publication.
