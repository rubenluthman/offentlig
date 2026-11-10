#!/bin/sh
# House style check (Vale) on the tracked prose files. Run by verify_commit.sh and by the prose CI workflow.
# Wording and punctuation rules come from the shared house-style package (see docs/house-style.md).
set -eu
cd "$(dirname "$0")/.."

if ! command -v vale >/dev/null 2>&1; then
  if [ -n "${CI:-}" ]; then
    echo "vale is not installed" >&2
    exit 1
  fi
  echo "vale is not installed: skipping the house style check, which CI runs. Install it from https://vale.sh/docs/install"
  exit 0
fi

# Resync whenever the pinned release changes, so a version bump never runs stale cached rules.
pin="$(grep '^Packages' .vale.ini)"
if [ "$(cat .vale/styles/HouseStyle/.pin 2>/dev/null)" != "$pin" ]; then
  if ! vale sync >/dev/null; then
    echo "vale sync failed: the house-style package needs network access once per pinned release" >&2
    exit 1
  fi
  printf '%s\n' "$pin" > .vale/styles/HouseStyle/.pin
fi

files=$(git ls-files --cached --others --exclude-standard -- '*.md' '*.txt' | grep -v -E '^(LICENSE|AUTHORS.txt|CONTRIBUTORS.txt)$' || true)
for f in $files; do [ -f "$f" ] && set -- "$@" "$f"; done
[ "$#" -eq 0 ] || vale --output=line "$@" >&2
