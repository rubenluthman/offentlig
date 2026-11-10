# Agent notes

Open-source font superfamily. Offentlig Sans is a renamed fork of Public Sans (upstream commit `e40fcf567`). Python 3.14, OFL 1.1.

## Commands

- `make venv` creates `venv/` and `venv/diffenator`. Activate nothing: the Makefile puts `venv/bin` on `PATH`.
- `make build` runs gftools builder in `sources/` and writes `fonts/OffentligSans/`.
- `make test` runs pytest against the built fonts. Build first.
- `make qa` runs Fontspector (`venv/bin/fontspector`, universal and opentype profiles). `make proof` runs Diffenator2.
- `make verify` is the pre-commit check (`scripts/verify_commit.sh`).

## Boundaries

- Sources are `sources/*.designspace` and `sources/*.ufo` only (ADR-0001). Do not add `.glyphs` files.
- Never commit `fonts/` or `build/` (ADR-0002), or `docs/private/`, which holds private notes.
- Keep the vertical metrics in `ARCHITECTURE.md`; a test enforces them.
- Never create tags or releases, and never make the repository public, without the owner's go-ahead.
- Bug fixes go upstream to uswds/public-sans first.
- Remote CI (`ubuntu-latest`) stays on while the repository is private: it is the only clean-build and Fontspector gate. Never gate it on repository visibility or remove it.
- One SemVer version covers all families, `0.x.y`. Never bump to `1.0.0` without the owner's authorization.
- No marketing wording; no em dashes in `.md` or `.txt` files.

## Dependencies

gftools builder, fontmake, ufo2ft, fontTools, uharfbuzz, pytest (see `requirements.txt`). QA: Fontspector 1.9.0, Diffenator2 0.0.7. Verification: `vale` (`brew install vale`).
