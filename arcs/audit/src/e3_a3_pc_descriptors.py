"""Amendment 3 §4 descriptor cells (class-step checks, not gated): targets PC1 and PC2 of X, the tissue-class
contrasts that the site leg and G6s condition out; n = 200 plants per class × target, paired across w, × {rand-25,
clus-25}. Reports, per class × target × w × set kind and by class-step stratum, the rejection rates at alpha_v = .025
of Level 0 (naive), the site leg, each species leg, the species max and the verdict (status ok only, as the gates count
it), plus the status counts. Nothing is gated. Reads artifacts/plants_a3/*_F-align-pc_*.csv.gz; writes
arcs/audit/results/e3_a3_pc_descriptors.json.
Run (programme root): env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e3_a3_pc_descriptors.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
A3, RES = ROOT / "artifacts" / "plants_a3", ROOT / "arcs" / "audit" / "results"
ALPHA_V = 0.025
LEGS = ("naive", "site", "G1", "G3m", "G6s", "G6l", "species")


def rates(g: pd.DataFrame) -> dict:
    r = {leg: round(float((g[f"p_{leg}"] < ALPHA_V).mean()), 4) for leg in LEGS}
    r["verdict"] = round(float(((g.p_verdict < ALPHA_V) & (g.verdict_status == "ok")).mean()), 4)
    return r


def main():
    rows, sha = [], {}
    for c in ("aal", "dk", "cc200"):
        for t in ("pc1", "pc2"):
            for w in ("0.5", "0.9"):
                f = A3 / f"{c}_F-align-pc_{t}_{w}.csv.gz"
                sha[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
                d = pd.read_csv(f)
                for k, g in d.groupby("kind"):
                    row = dict(cls=c, target=t, w=float(w), kind=k, n=int(len(g)), **rates(g),
                               status=g.verdict_status.value_counts().to_dict())
                    for s, gs in g.groupby("step"):
                        row[f"step{int(s)}"] = rates(gs)
                    rows.append(row)
    out = dict(status="amendment 3 §4 descriptor cells (PC1 / PC2 targets); reported, not gated", alpha_v=ALPHA_V,
               cells=rows, inputs_sha256=sha, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               commit=subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                                     text=True).stdout.strip())
    (RES / "e3_a3_pc_descriptors.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    t = pd.DataFrame([{k: v for k, v in r.items() if k not in ("status", "step0", "step1")} |
                      {"site_s0": r["step0"]["site"], "site_s1": r["step1"]["site"],
                       "verdict_s0": r["step0"]["verdict"], "verdict_s1": r["step1"]["verdict"]} for r in rows])
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
