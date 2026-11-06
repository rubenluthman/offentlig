#!/bin/sh
# Pre-commit verification: tests, relative Markdown links, house style (Vale), absolute home paths and secrets.
set -eu
cd "$(dirname "$0")/.."
fail=0

echo "== tests"
if [ -d fonts/OffentligSans/ttf ]; then
  PATH="$PWD/venv/bin:$PATH" pytest -q tests || fail=1
else
  echo "fonts/ missing: run 'make build' first" >&2
  fail=1
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

echo "== house style (Vale)"
# Wording and punctuation rules come from the shared house-style package (see docs/house-style.md).
if ! command -v vale >/dev/null 2>&1; then
  echo "vale is not installed: brew install vale" >&2
  fail=1
else
  # Resync whenever the pinned release changes, so a version bump never runs stale cached rules.
  pin="$(grep '^Packages' .vale.ini)"
  if [ "$(cat .vale/styles/HouseStyle/.pin 2>/dev/null)" != "$pin" ]; then
    if vale sync >/dev/null; then
      printf '%s\n' "$pin" > .vale/styles/HouseStyle/.pin
    else
      echo "vale sync failed: the house-style package needs network access once per pinned release" >&2
      fail=1
    fi
  fi
  if [ -d .vale/styles/HouseStyle ]; then
    prose=$(echo "$files" | grep -E '\.(md|txt)$' | grep -v -E '^(LICENSE|AUTHORS.txt|CONTRIBUTORS.txt)$' || true)
    for f in $prose; do [ -f "$f" ] && set -- "$@" "$f"; done
    if [ "$#" -gt 0 ] && ! vale --output=line "$@" >&2; then
      fail=1
    fi
  fi
fi

echo "== absolute home paths and secrets"
if echo "$files" | grep -v '^scripts/verify_commit.sh$' | xargs grep -I -n -E '/Users/[A-Za-z0-9_.-]+|/home/[A-Za-z0-9_.-]+|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|sk-[A-Za-z0-9]{20,}' ; then
  fail=1
fi

[ "$fail" -eq 0 ] && echo "verify: ok" || { echo "verify: FAILED" >&2; exit 1; }
