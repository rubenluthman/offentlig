#!/bin/sh
# Print the CHANGELOG.md section for one version, used as the GitHub release notes.
# Usage: scripts/release_notes.sh 0.1.0
# Fails when CHANGELOG.md has no "## [0.1.0]" heading or the section is empty, so a tag never ships without notes.
set -eu
cd "$(dirname "$0")/.."

version="${1:?usage: scripts/release_notes.sh X.Y.Z}"
notes=$(awk -v heading="## [$version]" '
  index($0, heading) == 1 { found = 1; next }
  found && /^## \[/ { exit }
  found { print }
' CHANGELOG.md | sed '/./,$!d')

if [ -z "$(printf '%s' "$notes" | tr -d '[:space:]')" ]; then
  echo "CHANGELOG.md has no notes under \"## [$version]\"" >&2
  exit 1
fi
printf '%s\n' "$notes"
