"""Summarize a Fontspector JSON report: FAIL counts per check id with one sample message."""
import collections, json, sys

d = json.load(open(sys.argv[1]))["results"]
sev = sys.argv[2] if len(sys.argv) > 2 else "FAIL"
c = collections.defaultdict(lambda: [0, set(), ""])
for res in d.values():
    for section in res.values():
        for r in section:
            for s in r.get("subresults", []):
                if s.get("severity") == sev:
                    e = c[r["check_id"]]
                    e[0] += 1
                    e[1].add(r["filename"].rsplit("/", 1)[-1])
                    e[2] = s.get("message", "").replace("\n", " ")
for k, (n, files, m) in sorted(c.items(), key=lambda x: -x[1][0]):
    print(f"{n:4d} {k} ({len(files)} files) | {m[:260]}")
