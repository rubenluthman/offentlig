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
make test      # pytest -n 3 --dist worksteal against the built fonts (override with PYTEST_JOBS=auto)
make qa        # Fontspector universal and OpenType profiles, expected 0 FAIL
make proof     # tester page (docs/proof/allemansratten.txt) and Diffenator2 proof pages in build/proof
make specimen  # docs/specimen.png and specimen-dark.png from the built TTFs and the Allemansrätten text
make social-preview  # build/social-preview.png, 1280 x 640, uploaded by hand under Settings > General > Social preview
make diff-public-sans  # Diffenator2 comparison with Public Sans at e40fcf567 (cloned into build/public-sans-reference), in build/diff-public-sans (skipped, keeping the old report, when that folder exists: move it aside first)
make diff-main  # Diffenator2 comparison with origin/main (a plain copy of its files built in build/main-reference, rebuilt when origin/main moves), in build/diff-main
make install   # copies the OTF files to ~/Library/Fonts
make clean     # deletes fonts/ and build/
make verify    # tests, links, house style, conflict markers, paths and secrets
```

`make test` and `make verify` use `--dist worksteal`: a worker that runs out of tests takes queued ones from another, so no worker is left running the longest tests alone. Measured on `v0.5.0` with the same tests collected and passing: two workers with the default distribution took 71 minutes, with one worker idle for the last 60; three workers with `worksteal` took 33 minutes, all busy until the last 16 seconds. In a full run with three workers, each peaked between 0.8 and 1.2 GB (the pair tests now build their pair lists in chunks, which lowers the peak inside one test but not the memory a worker keeps across tests), so the local default stays at three. A later full run on the 0.8.0 development tree (10,002 passed, 111 skipped) with four workers took 53 minutes 41 seconds, slower than the three-worker run above on a smaller suite: resident memory per worker peaked at 767 MB, but the four workers together pushed swap up by about 4.4 GB (from 5.7 to 10.1 GB used) and memory pressure reached the warning level. Five workers were not tried. Raise `PYTEST_JOBS` only on a machine with memory to spare. CI uses `PYTEST_JOBS=auto`.

Each heavy step (`build`, `test`, `qa`, `proof`, `diff-public-sans`, `diff-main`, and the test step of `verify`) runs one at a time: when a `heavy-run` command is installed it queues on a shared lock, and where it is not (CI) it runs directly.

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
- Run `make verify` before committing. It stops before the tests when `fonts/` is missing or older than `sources/`, because the tests read the built fonts. It runs the house style check (through the shared commit checks) with `vale` ([install](https://vale.sh/docs/install)), and skips it with a notice when `vale` is missing, because CI runs it too. The rules are described under [House style](#house-style).

## Releases

1. Check the pull requests this fork sent to Public Sans ([#396](https://github.com/uswds/public-sans/pull/396), [#397](https://github.com/uswds/public-sans/pull/397), [#398](https://github.com/uswds/public-sans/pull/398)). When one has merged or closed, say so in `README.md` and `ROADMAP.md`, and compare the merged change with this fork's fix.
2. Rename `## [Unreleased]` in `CHANGELOG.md` to `## [X.Y.Z] - YYYY-MM-DD`, and update the version in `sources/*.ufo/fontinfo.plist` (`versionMajor`, `versionMinor`). Package version `0.X.Y` becomes font version `0.(X × 100 + Y)`.
3. Run `make build test qa`. The version test compares name ID 5 of every built font with `versionMajor` and `versionMinor` in the masters, so it fails on a stale build or masters that disagree.
4. Run `make specimen` to refresh `docs/specimen.png` and `docs/specimen-dark.png` and `make social-preview` to write `build/social-preview.png`, and upload the preview by hand.
5. Run `scripts/release_notes.sh X.Y.Z` to check the release notes before tagging: the release job fails without them, and a tag is never moved.
6. Commit the release, then tag it as an annotated tag named `vX.Y.Z` with the release commit's subject as the message (`git tag -a vX.Y.Z -m "<subject>"`), and push the tag. Tags are never moved or reused.
7. CI builds the fonts, runs the tests and Fontspector, zips `fonts/OffentligSans/` and `LICENSE` as `OffentligSans-X.Y.Z.zip` and creates a draft GitHub release with the zip attached (ADR-0002) and that version's `CHANGELOG.md` section as its notes. The release job fails if the section is missing or empty.
8. Review the draft release and publish it.

CI runs on pushes and pull requests to `main` that touch `sources/`, `tests/`, `scripts/`, `docs/proof/` (the tester text is read by a test), `Makefile`, `requirements*.txt` or `.github/`, and fails on any test failure or Fontspector FAIL. Every run that is not a tag push also builds the zip and uploads it as the `release-zip` workflow artifact, so the release job's input can be inspected without a tag. The workflow can also be started manually (`workflow_dispatch`).

A second workflow, commit-checks, runs the shared commit checks on every push and pull request to `main`: secrets, home paths, emails, private names, leftover conflict markers and the house style check on `.md` and `.txt` files (all but `LICENSE`, `AUTHORS.txt` and `CONTRIBUTORS.txt`). It installs a pinned Vale release and checks its SHA-256 first.

Versioning:

| Bump | When | Examples |
| --- | --- | --- |
| Patch `0.1.x` | Fixes and additions that leave existing text laid out the same | A glyph bug, a missing Unicode value, new glyphs, a new feature |
| Minor `0.x.0` | A milestone, or anything that moves existing text | Changed widths, kerning or vertical metrics, a redrawn glyph, a renamed feature, a new family |
