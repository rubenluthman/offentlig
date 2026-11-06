#!/bin/sh
# Pre-commit verification: tests, relative Markdown links, marketing wording, absolute home paths and secrets.
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

echo "== marketing wording"
if echo "$files" | grep -E '\.(md|txt)$' | grep -v -E '^(LICENSE|AUTHORS.txt|CONTRIBUTORS.txt)$' | xargs grep -n -i -E 'seamless|cutting-edge|world-class|revolutionary|state-of-the-art|powerful|blazing|game-changing|unleash|robust solution|best-in-class' ; then
  fail=1
fi

echo "== em dashes"
if echo "$files" | grep -E '\.(md|txt|swift)$' | xargs grep -n "$(printf '\342\200\224')" ; then
  fail=1
fi

echo "== absolute home paths and secrets"
if echo "$files" | grep -v '^scripts/verify_commit.sh$' | xargs grep -I -n -E '/Users/[A-Za-z0-9_.-]+|/home/[A-Za-z0-9_.-]+|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY|sk-[A-Za-z0-9]{20,}' ; then
  fail=1
fi

[ "$fail" -eq 0 ] && echo "verify: ok" || { echo "verify: FAILED" >&2; exit 1; }
