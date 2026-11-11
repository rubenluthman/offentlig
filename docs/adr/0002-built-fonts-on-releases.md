# Built fonts are attached to releases, not committed
Status: Active · 2026-11-06

## Decision

Built font binaries never live in the repository. They are built with `make build` or CI and attached to each tagged release.

- `fonts/` and `build/` stay in `.gitignore`. Do not commit font binaries, including for convenience or to match Public Sans or Geist.
- Tests run against a local `make build` output, not against committed files.
- Each tagged release carries a zip with every format (OTF, TTF, variable TTF, WOFF2). The release is the only distribution channel for binaries.

## Why

Upstream Public Sans and the Google Fonts template commit built binaries in `fonts/`. Binaries are large, do not diff, and can drift from the sources they claim to come from. Committing them would add binary churn on every release and let a stale binary be committed by accident. With binaries only on releases, the tree holds sources only and every distributed file traces to a tag.

Undoing this would let users download fonts that no longer match the sources, which breaks something people rely on.

## What we gave up

- **Download from the tree.** A visitor who clones the repository has no font files until they run `make build` (about 25 seconds with the pinned environment) or open the Releases page.
- **Independence from the build toolchain.** A release cannot be produced without the Python version and pinned environment in `requirements.txt`.

## Revisit if

- A distribution channel the project relies on requires binaries in the tree.
