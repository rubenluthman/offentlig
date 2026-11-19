#!/bin/sh
# Points git at the tracked hooks. Run once after cloning.
set -eu
cd "$(git rev-parse --show-toplevel)"
git config core.hooksPath .githooks
chmod +x .githooks/* scripts/commit-checks
echo "hooks installed (core.hooksPath = .githooks)"
