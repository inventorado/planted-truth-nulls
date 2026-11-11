"""R22: which Fisher p does PANTHER's overrepresentation test report? An empirical check (2026-10-11).

RUN_PLAN.md R22 makes the primary sidedness "the sidedness PANTHER's own documentation states"; no PANTHER document read
states it (repro.PANTHER_SIDEDNESS). This script asks PANTHER's public API (the service behind the web tool) for an
overrepresentation test on a toy list of 15 everyday human genes (no audit material), then recomputes every reported raw
p as a one-sided and a two-sided Fisher exact p on the 2 x 2 table [[a, n - a], [K - a, N - K - (n - a)]] (the reference
includes the list, as repro.fisher_counts builds it), with n and N taken from PANTHER's own expected values
(expected = K * n / N). The sidedness whose p reproduces every row is the one PANTHER reports.

Run from arcs/audit/src:
  python -X utf8 -m a1_audit.panther_sidedness_check [--fetch] [--dir ../run_manifests/R22_panther]
--fetch re-queries the API (network); otherwise the saved, gzipped responses in --dir are used.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import statistics
import subprocess
from pathlib import Path

from scipy.stats import fisher_exact

GENES = ["RPL3", "RPL4", "RPL5", "RPL7", "RPL8", "RPS3", "RPS6", "GAPDH", "ACTB", "TUBB", "INS", "ALB", "EGFR", "TP53",
         "MYC"]
API = ("https://pantherdb.org/services/oai/pantherdb/enrich/overrep?geneInputList={genes}&organism=9606"
       "&annotDataSet={ds}&enrichmentTestType=FISHER&correction=FDR")
DATASETS = {"panther_pathway": "ANNOT_TYPE_ID_PANTHER_PATHWAY", "go_bp": "GO:0008150"}
TOL = 1e-9  # relative agreement required for "reproduces"


def fetch(ds: str) -> bytes:
    """Plain curl, as on 2026-10-11 (Python's urllib is refused with HTTP 403 by the site's bot protection; it is not
    circumvented - no user-agent is changed)."""
    r = subprocess.run(["curl", "-sS", "-m", "180", "--fail", API.format(genes=",".join(GENES), ds=ds)],
                       capture_output=True, check=True)
    return r.stdout


def check(raw: bytes) -> dict:
    d = json.loads(raw)["results"]
    rows = d["result"]
    ratio = statistics.median(r["expected"] / r["number_in_reference"] for r in rows if r["number_in_reference"])
    N = 20580 if abs(ratio * 20580 - round(ratio * 20580)) < 1e-6 else None
    if N is None:
        raise ValueError("cannot recover integer n for N = 20580 from PANTHER's expected values")
    n = round(ratio * N)
    out = {"one": 0, "two": 0, "discriminating": 0, "discriminating_two": 0, "rows": 0}
    worst = {"one": 0.0, "two": 0.0}
    for r in rows:
        a, K, p, pm = r["number_in_list"], r["number_in_reference"], r["pValue"], r["plus_minus"]
        t = [[a, n - a], [K - a, N - K - (n - a)]]
        if min(min(x) for x in t) < 0:
            raise ValueError("negative cell")
        one = min(1.0, fisher_exact(t, alternative="greater" if pm == "+" else "less")[1])
        two = min(1.0, fisher_exact(t, alternative="two-sided")[1])
        out["rows"] += 1
        for k, v in (("one", one), ("two", two)):
            rel = abs(v - p) / max(p, 1e-300)
            worst[k] = max(worst[k], float(rel))
            out[k] += int(rel < TOL)
        if abs(one - two) / max(one, 1e-300) > 0.05:
            out["discriminating"] += 1
            out["discriminating_two"] += int(abs(two - p) / max(p, 1e-300) < TOL)
    return dict(n_list_mapped=n, n_reference=N, rows=out["rows"], reproduced_one_sided=out["one"],
                reproduced_two_sided=out["two"], max_rel_diff_one_sided=worst["one"],
                max_rel_diff_two_sided=worst["two"], discriminating_rows=out["discriminating"],
                discriminating_rows_reproduced_two_sided=out["discriminating_two"],
                annot_version=d.get("annot_version_release_date"), tool_release_date=d.get("tool_release_date"),
                test=d.get("enrichment_test_type"), correction=d.get("correction"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--dir", default=str(Path(__file__).resolve().parents[2] / "run_manifests" / "R22_panther"))
    a = ap.parse_args(argv)
    out_dir = Path(a.dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {"what": "R22 empirical sidedness check of PANTHER's overrepresentation test", "genes": GENES,
               "api": API, "tolerance_rel": TOL, "datasets": {}}
    for name, ds in DATASETS.items():
        gz = out_dir / f"overrep_{name}.json.gz"
        if a.fetch:
            raw = fetch(ds)
            gz.write_bytes(gzip.compress(raw, mtime=0))
        raw = gzip.decompress(gz.read_bytes())
        res = check(raw)
        res.update(response_sha256=hashlib.sha256(raw).hexdigest(), response_gz=gz.name, annotDataSet=ds)
        summary["datasets"][name] = res
        print(f"{name}: rows {res['rows']}; two-sided reproduces {res['reproduced_two_sided']} "
              f"(max rel diff {res['max_rel_diff_two_sided']:.2e}); one-sided {res['reproduced_one_sided']}; "
              f"discriminating rows {res['discriminating_rows']}, two-sided reproduces "
              f"{res['discriminating_rows_reproduced_two_sided']}")
    verdict = all(r["reproduced_two_sided"] == r["rows"] and r["discriminating_rows"] > 0
                  and r["reproduced_one_sided"] < r["rows"] for r in summary["datasets"].values())
    summary["finding"] = ("PANTHER's overrepresentation Fisher p is two-sided (reference includes the list)"
                          if verdict else "not established")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("finding:", summary["finding"])
    return 0 if verdict else 1


if __name__ == "__main__":
    raise SystemExit(main())
