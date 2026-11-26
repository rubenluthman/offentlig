#!/usr/bin/env python3
"""Write tests/data/floor-baseline.json.gz: the pairs under the nearest-ink floor in the built fonts, per static and suite.

`tests/test_ink_floor.py` lets a pair listed here stay under the floor, and fails when one gets more than a unit closer or
when a pair that is not listed falls under it. Run it after a build once the pairs you fixed are fixed:

    heavy-run venv/bin/python scripts/write_floor_baseline.py [--jobs 3]

The file keeps, for each pair, the smallest distance over the feature sets of its suite.
"""
import argparse
import gzip
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

import test_ink_floor as T  # noqa: E402
from test_spacing import ALL_FONTS  # noqa: E402


def collect(font):
    weight, italic = font
    out = {}
    for suite, key in T.suites():
        for text, d in T.suite_found(suite, weight, italic, key):
            held = out.setdefault(suite, {})
            held[text] = min(d, held.get(text, d))
    return T.static_id(weight, italic), {s: dict(sorted(v.items())) for s, v in sorted(out.items())}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--jobs", type=int, default=3)
    args = parser.parse_args()
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        result = dict(sorted(pool.map(collect, ALL_FONTS)))
    T.BASELINE.parent.mkdir(parents=True, exist_ok=True)
    # mtime=0 keeps the bytes the same for the same content
    with open(T.BASELINE, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as f:
        f.write(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    for static, suites in result.items():
        print(static, {s: len(v) for s, v in suites.items()})


if __name__ == "__main__":
    main()
