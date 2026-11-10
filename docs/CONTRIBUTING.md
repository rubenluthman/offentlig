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
make verify    # tests, links, house style, paths and secrets
```

## Editing sources

Edit the UFO files in `sources/` with any UFO editor (see ADR-0001). The Regular master is a regular master: a change to Thin or Black must be repeated in Regular. Keep Thin, Regular and Black compatible (same contours, same point order) and keep the vertical metrics in `ARCHITECTURE.md`.

## Credits

Anyone whose drawings ship in the fonts goes in `AUTHORS.txt` as well as `CONTRIBUTORS.txt`, because the OFL copyright notice lists the authors of the drawings.

## Bug fixes

Fix bugs upstream first. Open a pull request against https://github.com/uswds/public-sans when the bug exists there, then apply the same change here.

## Branches and commits

- Work on a branch and open a pull request into `main`.
- Use Conventional Commits.
- Run `make verify` before committing. It runs the house style check with `vale` ([install](https://vale.sh/docs/install)), and skips it with a notice when `vale` is missing, because CI runs it too. The wording rules are described in [house-style.md](house-style.md).

## Releases

1. Update `CHANGELOG.md` and the version in `sources/*.ufo/fontinfo.plist` (`versionMajor`, `versionMinor`). Package version `0.X.Y` becomes font version `0.(X × 100 + Y)`.
2. Run `make build test qa`.
3. Tag `vX.Y.Z` and push the tag (tags are never moved or reused).
4. CI builds the fonts, runs the tests and Fontspector, zips `fonts/OffentligSans/` as `OffentligSans-X.Y.Z.zip` and creates a draft GitHub release with the zip attached (ADR-0002).
5. Review the draft release and publish it.

CI runs on pushes and pull requests to `main` that touch `sources/`, `tests/`, `scripts/`, `Makefile`, `requirements*.txt` or `.github/`, and fails on any test failure or Fontspector FAIL. Every run that is not a tag push also builds the zip and uploads it as the `release-zip` workflow artifact, so the release job's input can be inspected without a tag. The workflow can also be started manually (`workflow_dispatch`).

A second workflow, Prose, runs the house style check on pushes and pull requests to `main` that touch `.md` or `.txt` files or `.vale.ini`. It installs a pinned Vale release and checks its SHA-256 first.

Versioning:

| Bump | When | Examples |
| --- | --- | --- |
| Patch `0.1.x` | Fixes and additions that leave existing text laid out the same | A glyph bug, a missing Unicode value, new glyphs, a new feature |
| Minor `0.x.0` | A milestone, or anything that moves existing text | Changed widths, kerning or vertical metrics, a redrawn glyph, a renamed feature, a new family |
