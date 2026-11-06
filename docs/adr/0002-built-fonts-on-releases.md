---
status: accepted
date: 2026-11-06
deciders: Ruben Luthman
tags: [build, release]
---

# ADR-0002: Built fonts are attached to releases, not committed

## Context and Problem Statement

Upstream Public Sans and the Google Fonts template commit built binaries in `fonts/`. Binaries are large, do not diff, and can drift from the sources they claim to come from. The repository needs one rule for where built fonts live.

## Considered Options

1. **Commit built fonts.** Users can download a file from the tree. Every release adds binary churn, and a stale binary can be committed by accident.
2. **Gitignore `fonts/`; build with `make build` or CI; attach the build to each tagged release.** The tree holds sources only, and every distributed binary is traceable to a tag.

## Decision Outcome

Option 2.

### Invariants & Negative Constraints

- `fonts/` and `build/` stay in `.gitignore`. Do not commit font binaries, including for convenience or to match Public Sans or Geist.
- Tests run against a local `make build` output, not against committed files.
- Each tagged release carries a zip with every format (OTF, TTF, variable TTF, WOFF2). The release is the only distribution channel for binaries.

### Negative Consequences

- **No download from the tree.** Verified worst case: a visitor who clones the repository has no font files until they run `make build` (about 25 seconds with the pinned environment) or open the Releases page. Set aside: zero-step access from a clone.
- **Releases depend on a local or CI build.** Verified worst case: a release cannot be produced without Python 3.14 and the pinned environment in `requirements.txt`. Set aside: independence from the build toolchain.
