#!/bin/sh
# Fails when a tracked or new file still holds git conflict markers, which
# a merge can leave in Markdown and text files without breaking the build.
# Run by verify_commit.sh and .github/workflows/prose.yaml.
#
# xargs runs grep in several batches and fails as a whole when any batch
# has no match, so the result is judged by grep's output, not its status.
set -eu
cd "$(dirname "$0")/.."
found=$(git ls-files -z --cached --others --exclude-standard \
  | xargs -0 grep -I -n -E '^(<<<<<<<|>>>>>>>)( |$)' || true)
if [ -n "$found" ]; then
  printf '%s\n' "$found"
  echo "conflict markers found" >&2
  exit 1
fi
