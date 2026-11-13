# Contributing

## Environment

Python 3.14 on macOS.

```bash
make venv
```

QA tools: Diffenator2 is installed by `make venv` into `venv/diffenator`. Fontspector 1.9.0 is a release binary from https://github.com/fonttools/fontspector/releases, saved as `venv/bin/fontspector`.

## Build, test, verify

```bash
make build     # fonts/OffentligSans/{otf,ttf,variable,webfonts}
make test      # pytest against the built fonts
make qa        # Fontspector universal and OpenType profiles, expected 0 FAIL
make proof     # tester page (docs/proof/allemansratten.txt) and Diffenator2 proof pages in build/proof
make specimen  # docs/specimen.png from the built TTFs and the Allemansrätten text
make social-preview  # build/social-preview.png, 1280 x 640, uploaded by hand under Settings > General > Social preview
make verify    # tests, links, house style, conflict markers, paths and secrets
```

## Editing sources

Edit the UFO files in `sources/` with any UFO editor (see ADR-0001). The Regular master is a regular master: a change to Thin or Black must be repeated in Regular. Keep Thin, Regular and Black compatible (same contours, same point order) and keep the vertical metrics in `ARCHITECTURE.md`.

## Credits

Anyone whose drawings ship in the fonts goes in `AUTHORS.txt` as well as `CONTRIBUTORS.txt`, because the OFL copyright notice lists the authors of the drawings.

## Bug fixes

Fix bugs here. When the bug also exists in Public Sans and https://github.com/uswds/public-sans has no issue for it, open one.

## House style

This project follows a shared house style for wording, punctuation, and headings. It asks for concrete properties instead of claims of quality, and for facts instead of filler. Parenthetical breaks require a spaced en dash ( – ) instead of an em dash, following Swedish and British typographic standards. Headings use sentence case, as in American technical style guides. [Vale](https://vale.sh) enforces these checks via the [house-style](https://github.com/rubenluthman/house-style) package, and each rule's message gives its reason.

## Branches and commits

- Work on a branch and open a pull request into `main`.
- Use Conventional Commits.
- Run `make verify` before committing. It stops before the tests when `fonts/` is missing or older than `sources/`, because the tests read the built fonts. It runs the house style check with `vale` ([install](https://vale.sh/docs/install)), and skips it with a notice when `vale` is missing, because CI runs it too. The rules are described under [House style](#house-style).

## Releases

1. Rename `## [Unreleased]` in `CHANGELOG.md` to `## [X.Y.Z] - YYYY-MM-DD`, and update the version in `sources/*.ufo/fontinfo.plist` (`versionMajor`, `versionMinor`). Package version `0.X.Y` becomes font version `0.(X × 100 + Y)`.
2. Run `make build test qa`. The version test compares name ID 5 of every built font with `versionMajor` and `versionMinor` in the masters, so it fails on a stale build or masters that disagree.
3. Run `make specimen` to refresh `docs/specimen.png` and `make social-preview` to write `build/social-preview.png`, and upload the preview by hand.
4. Run `scripts/release_notes.sh X.Y.Z` to check the release notes before tagging: the release job fails without them, and a tag is never moved.
5. Commit the release, then tag it as an annotated tag named `vX.Y.Z` with the release commit's subject as the message (`git tag -a vX.Y.Z -m "<subject>"`), and push the tag. Tags are never moved or reused.
6. CI builds the fonts, runs the tests and Fontspector, zips `fonts/OffentligSans/` and `LICENSE` as `OffentligSans-X.Y.Z.zip` and creates a draft GitHub release with the zip attached (ADR-0002) and that version's `CHANGELOG.md` section as its notes. The release job fails if the section is missing or empty.
7. Review the draft release and publish it.

CI runs on pushes and pull requests to `main` that touch `sources/`, `tests/`, `scripts/`, `docs/proof/` (the tester text is read by a test), `Makefile`, `requirements*.txt` or `.github/`, and fails on any test failure or Fontspector FAIL. Every run that is not a tag push also builds the zip and uploads it as the `release-zip` workflow artifact, so the release job's input can be inspected without a tag. The workflow can also be started manually (`workflow_dispatch`).

A second workflow, Prose, checks for leftover conflict markers and runs the house style check on pushes and pull requests to `main` that touch `.md` or `.txt` files or `.vale.ini`. It installs a pinned Vale release and checks its SHA-256 first.

Versioning:

| Bump | When | Examples |
| --- | --- | --- |
| Patch `0.1.x` | Fixes and additions that leave existing text laid out the same | A glyph bug, a missing Unicode value, new glyphs, a new feature |
| Minor `0.x.0` | A milestone, or anything that moves existing text | Changed widths, kerning or vertical metrics, a redrawn glyph, a renamed feature, a new family |
