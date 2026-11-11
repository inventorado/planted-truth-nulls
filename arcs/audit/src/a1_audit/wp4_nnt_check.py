"""asdg-skeptic C2 (2026-10-16): the dominance port (wp4_repro.dominance_stats, RUN_PLAN_amend_4 R60) cross-checked
ONCE against netneurotools 0.3.0's own get_dominance_stats, run in a throwaway Docker container (python:3.11-slim,
`pip install netneurotools==0.3.0 "numpy<2" "scipy<1.12"`: the installed venv's scipy breaks its import), on synthetic
data only (three seeded regressions; no G2 material). The pin: arcs/audit/run_manifests/material/G2/
dominance_port_check.json (written, read back), holding the image digest, the package versions the container
reported, the data's sha256 and the largest absolute difference per statistic.

    python -X utf8 -m a1_audit.wp4_nnt_check --work <empty scratch folder>      # needs Docker and the network (pip)

Exit 0 iff every total / individual dominance and full R^2 agrees within 1e-10.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from . import wp4_layout as L
from . import wp4_repro as RP4

PIN_REL = "arcs/audit/run_manifests/material/G2/dominance_port_check.json"
IMAGE = "python:3.11-slim"
SEEDS = ((20261016, 68, 7), (20261017, 40, 4), (20261018, 100, 5))
TOL = 1e-10
NNT_SCRIPT = '''import json, numpy as np, netneurotools, scipy
from netneurotools.stats import get_dominance_stats
d = json.load(open("/io/data.json"))
res = []
for e in d:
    for adj in (True, False):
        m, _ = get_dominance_stats(np.array(e["X"]), np.array(e["y"]), use_adjusted_r_sq=adj)
        res.append({"seed": e["seed"], "adjusted": adj, "total_dominance": np.asarray(m["total_dominance"]).tolist(),
                    "full_r_sq": float(m["full_r_sq"]),
                    "individual_dominance": np.asarray(m["individual_dominance"]).tolist()})
json.dump({"netneurotools": netneurotools.__version__, "scipy": scipy.__version__, "numpy": np.__version__,
           "results": res}, open("/io/nnt_out.json", "w"))
'''


def synthetic() -> list:
    out = []
    for seed, n, p in SEEDS:
        rng = np.random.RandomState(seed)
        X = rng.normal(size=(n, p))
        X[:, 1] += 0.5 * X[:, 0]
        y = X @ rng.normal(size=p) + rng.normal(size=n)
        out.append({"seed": seed, "n": n, "p": p, "X": X.tolist(), "y": y.tolist()})
    return out


def compare(data: list, nnt: dict) -> dict:
    by = {e["seed"]: e for e in data}
    worst = {"total_dominance": 0.0, "individual_dominance": 0.0, "full_r_sq": 0.0}
    for r in nnt["results"]:
        e = by[r["seed"]]
        ours = RP4.dominance_stats(np.array(e["X"]), np.array(e["y"]), use_adjusted_r_sq=r["adjusted"])
        for k in worst:
            # netneurotools returns individual_dominance as (1, M); compared as flat vectors
            a, b = np.asarray(ours[k], dtype=float).ravel(), np.asarray(r[k], dtype=float).ravel()
            if a.shape != b.shape:
                worst[k] = float("inf")
            else:
                worst[k] = max(worst[k], float(np.max(np.abs(a - b))))
    return {"max_abs_difference": worst, "tolerance": TOL, "n_comparisons": len(nnt["results"]),
            "result": "PASS" if all(v <= TOL for v in worst.values()) else "FAIL"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m a1_audit.wp4_nnt_check")
    ap.add_argument("--work", required=True)
    a = ap.parse_args(argv)
    work = Path(a.work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    if any(work.iterdir()):
        print("wp4_nnt_check: the work folder is not empty")
        return 2
    data = synthetic()
    db = json.dumps(data).encode("utf-8")
    (work / "data.json").write_bytes(db)
    (work / "nnt_run.py").write_text(NNT_SCRIPT, encoding="utf-8", newline="\n")
    cmd = ["docker", "run", "--rm", "-v", f"{work}:/io", IMAGE, "sh", "-c",
           'pip install -q "netneurotools==0.3.0" "numpy<2" "scipy<1.12" >/dev/null 2>&1 && python /io/nnt_run.py']
    r = subprocess.run(cmd, capture_output=True, timeout=3600)
    if r.returncode != 0 or not (work / "nnt_out.json").is_file():
        print(f"wp4_nnt_check: the container run failed (exit {r.returncode})")
        return 1
    nnt = json.loads((work / "nnt_out.json").read_bytes().decode("utf-8"))
    dig = subprocess.run(["docker", "image", "inspect", "--format", "{{index .RepoDigests 0}}", IMAGE],
                         capture_output=True, text=True).stdout.strip()
    cmp_ = compare(data, nnt)
    rec = {"what": "asdg-skeptic C2: wp4_repro.dominance_stats vs netneurotools 0.3.0 get_dominance_stats, synthetic "
                   "data, a throwaway container", "script": "arcs/audit/src/a1_audit/wp4_nnt_check.py",
           "image": IMAGE, "image_repo_digest": dig, "container_versions": {k: nnt[k] for k in
                                                                             ("netneurotools", "scipy", "numpy")},
           "seeds": [list(s) for s in SEEDS], "data_sha256": hashlib.sha256(db).hexdigest(),
           "port_source": "wp4_repro.dominance_stats", **cmp_}
    p = L.REPO / PIN_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    out = (json.dumps(rec, indent=1) + "\n").encode("utf-8")
    p.write_bytes(out)
    if p.read_bytes() != out:
        raise OSError("read-back")
    print(f"wp4_nnt_check: {cmp_['result']}; comparisons {cmp_['n_comparisons']}; max abs difference "
          f"{max(cmp_['max_abs_difference'].values()):.3e}")
    return 0 if cmp_["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
