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
make verify    # tests, links, wording, paths and secrets
```

## Editing sources

Edit the UFO files in `sources/` with any UFO editor (see ADR-0001). The Regular master is a regular master: a change to Thin or Black must be repeated in Regular. Keep Thin, Regular and Black compatible (same contours, same point order) and keep the vertical metrics in `ARCHITECTURE.md`.

## Bug fixes

Fix bugs upstream first. Open a pull request against https://github.com/uswds/public-sans when the bug exists there, then apply the same change here.

## Branches and commits

- Work on a branch and open a pull request into `main`.
- Use Conventional Commits.
- Run `make verify` before committing.

## Releases

1. Update `CHANGELOG.md` and the version in `sources/*.ufo/fontinfo.plist` (`versionMajor`, `versionMinor`). Package version `0.X.Y` becomes font version `0.(X × 100 + Y)`.
2. Run `make build test qa`.
3. Tag `vX.Y.Z` (tags are never moved or reused).
4. Attach a zip of `fonts/OffentligSans/` to the GitHub release (ADR-0002).

Versioning:

| Bump | When | Examples |
| --- | --- | --- |
| Patch `0.1.x` | Fixes and additions that leave existing text laid out the same | A glyph bug, a missing Unicode value, new glyphs, a new feature |
| Minor `0.x.0` | A milestone, or anything that moves existing text | Changed widths, kerning or vertical metrics, a redrawn glyph, a renamed feature, a new family |
