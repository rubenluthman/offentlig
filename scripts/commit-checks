#!/usr/bin/env python3
"""Loader for the shared commit-checks package.

Reads .commit-checks.json (release tag and exact commit), gets that exact version from the local
package folder (git config --global commit-checks.path) or else from the settings' source URL,
checks the commit ID, and runs it. Any mismatch fails. Do not edit: `commit-checks verify` fails
when this file differs from the pinned release's template.
"""
import json
import io
import os
import subprocess
import sys
import tarfile
import tempfile


def die(message):
    sys.stderr.write("ERROR: %s\n" % message)
    sys.exit(2)


def git(args, cwd=None):
    try:
        proc = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as exc:
        die("git failed: %s" % exc)
    return proc.returncode, proc.stdout.decode("utf-8", "replace").strip(), proc.stderr.decode("utf-8", "replace").strip()


def resolve(repo, tag):
    code, out, _err = git(["rev-parse", "--verify", "--quiet", tag + "^{commit}"], cwd=repo)
    return out if code == 0 else ""


def export(repo, commit, dest):
    try:
        proc = subprocess.run(["git", "archive", "--format=tar", commit], cwd=repo, capture_output=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as exc:
        die("git archive failed: %s" % exc)
    if proc.returncode != 0:
        die("git archive failed: %s" % proc.stderr.decode("utf-8", "replace").strip()[:200])
    with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as tar:
        for member in tar.getmembers():
            name = os.path.normpath(member.name)
            if name.startswith("..") or os.path.isabs(name) or member.issym() or member.islnk():
                die("unsafe path in the package archive")
        tar.extractall(dest)
    with open(os.path.join(dest, ".commit"), "w") as fh:
        fh.write(commit + "\n")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    code, root, _ = git(["rev-parse", "--show-toplevel"], cwd=here)
    if code != 0 or not root:
        die("not inside a git repository")
    try:
        with open(os.path.join(root, ".commit-checks.json"), encoding="utf-8") as fh:
            settings = json.load(fh)
        tag, commit = settings["version"], settings["commit"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        die("cannot read version and commit from .commit-checks.json: %s" % exc)
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        die("settings: commit must be a full 40-character commit ID")
    _c, common, _e = git(["rev-parse", "--git-common-dir"], cwd=root)
    common = common if os.path.isabs(common) else os.path.normpath(os.path.join(root, common))
    cache = os.path.join(common, "commit-checks", commit)
    marker = os.path.join(cache, ".commit")
    ok = False
    if os.path.isfile(marker):
        with open(marker) as fh:
            ok = fh.read().strip() == commit and os.path.isfile(os.path.join(cache, "run_checks.py"))
    if not ok:
        local = os.environ.get("COMMIT_CHECKS_PATH") or git(["config", "--global", "--get", "commit-checks.path"])[1]
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        stage = tempfile.mkdtemp(prefix="load-", dir=os.path.dirname(cache))
        tmp_clone = None
        try:
            repo = None
            if local and os.path.isdir(local):
                repo = local
            else:
                source = settings.get("source")
                if not source:
                    die("no local package folder (git config --global commit-checks.path) and no source in settings")
                tmp_clone = tempfile.mkdtemp(prefix="clone-", dir=os.path.dirname(cache))
                code, _o, err = git(["clone", "--quiet", "--no-checkout", source, tmp_clone])
                if code != 0:
                    die("cannot fetch the package from its source: %s" % err[:200])
                repo = tmp_clone
            found = resolve(repo, tag)
            if found != commit:
                die("release %s is %s, but the settings pin %s" % (tag, found or "not found", commit))
            dest = os.path.join(stage, "pkg")
            os.mkdir(dest)
            export(repo, commit, dest)
            if os.path.isdir(cache):
                import shutil
                shutil.rmtree(cache)
            os.rename(dest, cache)
        finally:
            import shutil
            shutil.rmtree(stage, ignore_errors=True)
            if tmp_clone:
                shutil.rmtree(tmp_clone, ignore_errors=True)
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONSAFEPATH")}
    os.execve(sys.executable, [sys.executable, "-s", "-B", os.path.join(cache, "run_checks.py")] + sys.argv[1:], env)


main()
