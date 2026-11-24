# Agent notes

Open-source font superfamily. Offentlig Sans is a renamed fork of Public Sans (upstream commit `e40fcf567`). Python 3.14, OFL 1.1.

## Commands

- `make venv` creates `venv/` and `venv/diffenator`. Activate nothing: the Makefile puts `venv/bin` on `PATH`.
- `make build` runs gftools builder in `sources/` and writes `fonts/OffentligSans/`.
- `make test` runs `pytest -n 3 --dist worksteal` locally (`PYTEST_JOBS=auto` in CI) against the built fonts. Build first. A worker peaks between 0.8 and 1.2 GB; four workers were slower and swapped heavily, so the default stays three (see `CONTRIBUTING.md`).
- `make qa` runs Fontspector (`venv/bin/fontspector`, universal and opentype profiles). `make proof` runs Diffenator2.
- `make verify` is the pre-commit check (`scripts/verify_commit.sh`).
- Docs-only fast path: when every changed file is a doc (`docs_only` in `.commit-checks.json`), `make verify` skips the build checks and the tests. Every doc a test or script reads (`ARCHITECTURE.md`, `CHANGELOG.md`) must sit under `docs_only.except`.
- Run `scripts/install-hooks.sh` once after cloning (needs `gitleaks`). Generic commit checks (secrets, home paths, emails, private names, conflict markers) come from the shared commit-checks package at the release pinned in `.commit-checks.json`; CI runs them too.

## Boundaries

- Sources are `sources/*.designspace` and `sources/*.ufo` only (ADR-0001). Do not add `.glyphs` files.
- Never commit `fonts/` or `build/` (ADR-0002), or `docs/private/`, which holds private notes.
- Keep the vertical metrics in `ARCHITECTURE.md` (`typo`/`hhea` shared; each family sets `win` to cover its own glyphs); a test enforces them.
- Keep `docs/design-decisions.md` and `ARCHITECTURE.md` in sync with code and test changes. Superfamily feature tags follow Sans (`ss01=g`, `ss02=l`, `ss03=square dots`, `cv04=a`, `zero=slashed 0`).
- Plex Serif and Mono `sources.zip` use `1000` UPM (scale 2× to `2000` UPM) and true italics (`14°` Serif, `9.5°` Mono; Mono has no `kern` table).
- Never create tags or releases without the owner's go-ahead.
- Fix bugs here. When uswds/public-sans has no issue for the bug, open one.
- Remote CI (`ubuntu-latest`) is the only clean-build and Fontspector gate. Never remove it or gate it on repository visibility.
- One SemVer version covers all families, `0.x.y`. Never bump to `1.0.0` without the owner's authorization.
- No marketing wording; no em dashes in `.md` or `.txt` files.
- Bump the minor version for anything that moves existing text (widths, kerning, metrics, redrawn glyphs, renamed features), the patch version for fixes and additions that leave layout unchanged.
- Commits, PR descriptions and public docs state the change, its reason and its measurements, with PR and upstream links. Notes on process and review history go in `docs/private/`.

## Working rules

- Measure every claim on the built fonts before acting on it or writing it down, including the reason for each entry in a test's exemption list. A review's verdict or an approval is not a measurement.
- Apply and test every fix in all six masters, upright and italic, and with the alternate forms on.
- Check that nothing became worse than Public Sans `e40fcf567` by accident: Diffenator2 for outlines, widths, kerning and marks, plus measured counters, stroke weights and mark gaps.
- The Public Sans docs and issue history explain why a shape was drawn as it is. They inform a decision but never rule out an alternate or an improvement.
- Added slashes and bars (`zero.slash`, `Ǥ ǥ Ɨ ɨ`, currency bars) stay lighter than the main stems in Bold and Black.
- Show drawn changes to the owner as before-and-after images, with the comparison fonts, before committing them.
- Run one font build, full test run or whole-font pair scan at a time: together they run out of memory. Each heavy step (a font build, `make test`, Fontspector, Diffenator2, a scan with several worker processes) queues on a shared lock through `heavy-run`, one step per call; a script in one process runs without it. The Makefile does this where `heavy-run` is installed and runs directly where it is not (CI).
- `make diff-public-sans` skips the run and keeps the old report when `build/diff-public-sans/` exists. Move that folder aside first.

## Dependencies

gftools builder, fontmake, ufo2ft, fontTools, uharfbuzz, numpy, pytest (see `requirements.txt`). QA: Fontspector 1.9.0, Diffenator2 0.0.7. Verification: `vale` (`brew install vale`).
