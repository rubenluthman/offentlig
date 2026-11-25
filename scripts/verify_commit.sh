#!/bin/sh
# Pre-commit verification: tests (skipped when build/test-stamp shows a green `make test` on this exact tree), relative Markdown links and the shared commit checks (which include the house style check with Vale).
set -eu
cd "$(dirname "$0")/.."
fail=0

# Only the test step is heavy: it queues on the machine-wide lock where `heavy-run` is installed (not in CI).
heavy() { if command -v heavy-run >/dev/null 2>&1; then heavy-run "$@"; else "$@"; fi; }

# Docs-only changes skip the build checks and the tests. The command prints its own reason.
if scripts/commit-checks docs-only; then DOCS_ONLY=1; else DOCS_ONLY=0; fi

echo "== tests"
built=fonts/OffentligSans/ttf/OffentligSans-Regular.ttf
if [ "$DOCS_ONLY" = 1 ]; then
  echo "Skipped (fonts/ build checks and pytest): docs-only change."
elif [ ! -f "$built" ]; then
  echo "fonts/ missing: run 'make build' first" >&2
  fail=1
elif [ -n "$(git ls-files -z --cached --others --exclude-standard sources | xargs -0 sh -c 'find "$@" -prune -newer "$0" 2>/dev/null' "$built" | head -n 1)" ]; then
  # The tests read the built fonts, so a build older than sources/ reports false failures.
  # Only source files count: the build writes ignored files (build.ninja, instance_ufos/) into sources/.
  echo "fonts/ is older than sources/: run 'make build' first" >&2
  fail=1
elif [ -z "${CI:-}" ] && python3 scripts/test_stamp.py check; then
  # `make test` passed on exactly this tree (sources, tests, requirements, Makefile, ARCHITECTURE.md, proof text and built fonts).
  echo "Skipped pytest: build/test-stamp matches this tree, so the last green 'make test' covers it."
else
  PATH="$PWD/venv/bin:$PATH" heavy pytest -q -n "${PYTEST_JOBS:-4}" --dist worksteal tests || fail=1
fi

files=$(git ls-files --cached --others --exclude-standard)

echo "== relative Markdown links"
for f in $(echo "$files" | grep '\.md$'); do
  dir=$(dirname "$f")
  grep -o '\](\([^)#]*\)\(#[^)]*\)\{0,1\})' "$f" | sed 's/^](//; s/)$//; s/#.*//' | while read -r target; do
    case "$target" in ''|http*|mailto:*) continue ;; esac
    [ -e "$dir/$target" ] || { echo "$f: broken link $target" >&2; exit 1; }
  done || fail=1
done

echo "== shared commit checks (house style with Vale, secrets, home paths, emails, private names, conflict markers, hooks)"
./scripts/commit-checks verify || fail=1

[ "$fail" -eq 0 ] && echo "verify: ok" || { echo "verify: FAILED" >&2; exit 1; }
