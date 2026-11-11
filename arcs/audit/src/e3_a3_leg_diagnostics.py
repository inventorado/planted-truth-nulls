"""Diagnostics for the amendment-3 gates (reported, not gated): which leg of the verdict limits catch and power.

Per C-align plant file (a = .3 / .5 / .7; V-AAL, V-DK) and set kind: rejection rates at alpha_v = .025 of Level 0
(naive), the site leg, each species leg (G1, G3m, G6s, G6l), the species max, the pairwise conjunctions and the
verdict (status ok only, as the gates count it). C-gene a = .9 leg catches are copied from e3_gates_a3.json
(`leg_catch`, computed by e3_gates_a3.py). Reads artifacts/plants_a3/*_C-align_wmod_*.csv.gz and
arcs/audit/results/e3_gates_a3.json; writes arcs/audit/results/e3_a3_leg_diagnostics.json.
Run (programme root): env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e3_a3_leg_diagnostics.py
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


def main():
    rows, sha = [], {}
    for c in ("aal", "dk"):
        for a in ("0.3", "0.5", "0.7"):
            f = A3 / f"{c}_C-align_wmod_{a}.csv.gz"
            sha[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
            d = pd.read_csv(f)
            for k, g in d.groupby("kind"):
                r = {leg: float((g[f"p_{leg}"] < ALPHA_V).mean()) for leg in
                     ("naive", "site", "G1", "G3m", "G6s", "G6l", "species")}
                r.update(naive_and_site=float(((g.p_naive < ALPHA_V) & (g.p_site < ALPHA_V)).mean()),
                         site_and_species=float(((g.p_site < ALPHA_V) & (g.p_species < ALPHA_V)).mean()),
                         verdict=float(((g.p_verdict < ALPHA_V) & (g.verdict_status == "ok")).mean()))
                rows.append(dict(cls=c, a=float(a), kind=k, n=int(len(g)), **{x: round(v, 4) for x, v in r.items()}))
    gates = json.loads((RES / "e3_gates_a3.json").read_text(encoding="utf-8"))
    cgene = {g["gate"]: dict(verdict=round(g["rate"], 4), **{k: round(v, 4) for k, v in g["leg_catch"].items()})
             for g in gates["gates"]["verdict_catch"]}
    out = dict(status="diagnostics for the amendment-3 gates; reported, not gated", alpha_v=ALPHA_V,
               c_align=rows, verdict_catch_legs=cgene, inputs_sha256=sha,
               gates_json_sha256=hashlib.sha256((RES / "e3_gates_a3.json").read_bytes()).hexdigest(),
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               commit=subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                                     text=True).stdout.strip())
    (RES / "e3_a3_leg_diagnostics.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(pd.DataFrame(rows).to_string(index=False))
    for k, v in cgene.items():
        print(k, v)


if __name__ == "__main__":
    main()
