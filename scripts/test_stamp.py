#!/usr/bin/env python3
"""Stamp of a green full test run: a hash of everything the tests read.

`make test` writes `build/test-stamp` after pytest passes; `scripts/verify_commit.sh` skips pytest only when the hash of the
tree it sees is the same. Any change to a source, a test, the requirements, the Makefile, a document a test reads or a built
font makes the hashes differ, so the tests run again. Commands: `hash` (print it), `write`, `check` (exit 0 on a match).
"""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAMP = ROOT / "build" / "test-stamp"
# What the tests read: tracked and untracked (not ignored) files here, and the built fonts, which git ignores.
TRACKED = ["sources", "tests", "requirements.txt", "Makefile", "ARCHITECTURE.md", "docs/proof"]
BUILT = "fonts/OffentligSans"


def files():
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *TRACKED],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout.decode().split("\0")
    names = {n for n in listed if n}
    names |= {p.relative_to(ROOT).as_posix() for p in (ROOT / BUILT).rglob("*") if p.is_file()}
    return sorted(names)


def tree_hash():
    digest = hashlib.sha256()
    for name in files():
        path = ROOT / name
        digest.update(name.encode() + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest() if path.is_file() else b"missing")
    return digest.hexdigest()


def main(argv):
    command = argv[1] if len(argv) > 1 else ""
    if command == "hash":
        print(tree_hash())
    elif command == "write":
        STAMP.parent.mkdir(exist_ok=True)
        STAMP.write_text(tree_hash() + "\n")
    elif command == "check":
        return 0 if STAMP.is_file() and STAMP.read_text().strip() == tree_hash() else 1
    else:
        print("usage: test_stamp.py hash|write|check", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
