#!/bin/sh
# Fails when a tracked or new file still holds git conflict markers, which
# a merge can leave in Markdown and text files without breaking the build.
# Run by verify_commit.sh and .github/workflows/prose.yaml.
set -eu
cd "$(dirname "$0")/.."
if git ls-files -z --cached --others --exclude-standard \
  | xargs -0 grep -I -n -E '^(<<<<<<<|>>>>>>>)( |$)' ; then
  echo "conflict markers found" >&2
  exit 1
fi
