"""POST HOC descriptor (2026-11-11; not registered, not a gate): what the planted strength `a` looks like to a reader.

For every catch plant already on disk it reads the plant's observed map-set correlation `r` (the Pearson correlation
between the planted map and the set's raw mean-expression score, the statistic a study reports; e3_plants.py:114 and
the C-align generator) and reports

  (1) the distribution of observed r per class x family x a (C-sp, C-gene; V-AAL, V-DK) and per class x set kind x a
      (C-align), beside the registered verdict catch of the same cell;
  (2) verdict catch by bin of observed r, per class x family, split by planted strength a and pooled over a. r is
      signed in the registered direction (+1 for every plant family), so a plant with a negative observed r sits in
      the lowest bin. The pooled rows depend on the design's equal numbers of plants per a; the split rows show that
      at one observed r the catch rate rises with a.
  (3) the parametric leg's floor per class: the largest stored r whose one-sided parametric p is >= alpha_v and the
      smallest whose p is < alpha_v. No plant below the floor can be caught, whatever its other legs do.

No plant is rerun and no p-value is recomputed. The script reads the same files as e3_catch_curves_a5.py and
e3_a3_leg_diagnostics.py, through e3_gates_a3.load_existing (C-sp, C-gene) or directly (C-align), and stops unless
  - each input's sha256 equals the one recorded in e3_catch_curves_a5.json / e3_a3_leg_diagnostics.json, and
  - each cell's verdict catch equals the committed descriptor (k / n for C-sp and C-gene; the 4-dp rate for C-align).
Catch rule (amendment 3 section 5, as e3_gates_a3.py): plants never generated (status != ok) are excluded; every other
plant is in the denominator; a verdict status other than ok is a miss.

Reading limits: a bin pools plants of different planted strength, and every plant in it carries a true signal; the
table says how often a planted positive with that observed correlation is caught, not how likely an observed
correlation is to be real.

Writes arcs/audit/results/e3_observed_r_a5.json and .md.
Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e3_observed_r_a5.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e3_gates_a3 as G  # noqa: E402

A_CATCH = [0.3, 0.6, 0.9]
A_ALIGN = ["0.3", "0.5", "0.7"]
FAMS = ["C-sp", "C-gene"]
EDGES = [-1.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0000001]
LABELS = ["< .2", ".2-.3", ".3-.4", ".4-.5", ".5-.6", ".6-.7", ">= .7"]
QS = [10, 25, 50, 75, 90]


def quantiles(r: np.ndarray) -> dict:
    q = np.percentile(r, QS)
    return dict(p10=float(q[0]), q25=float(q[1]), median=float(q[2]), q75=float(q[3]), p90=float(q[4]),
                share_r_le_0=float((r <= 0).mean()))


def bins(r: np.ndarray, hit: np.ndarray) -> list:
    out = []
    for lo, hi, lab in zip(EDGES[:-1], EDGES[1:], LABELS):
        m = (r >= lo) & (r < hi)
        n, k = int(m.sum()), int(hit[m].sum())
        out.append(dict(bin=lab, k=k, n=n, rate=(k / n if n else None)))
    assert sum(b["n"] for b in out) == len(r)
    return out


def main():
    cc = json.loads((G.RES / "e3_catch_curves_a5.json").read_text(encoding="utf-8"))
    dg = json.loads((G.RES / "e3_a3_leg_diagnostics.json").read_text(encoding="utf-8"))
    assert cc["alpha_v"] == G.ALPHA_V == dg["alpha_v"]
    reg = {(c["cls"], c["family"], c["a"]): (c["k"], c["n"]) for c in cc["curves"]}
    reg_align = {(c["cls"], c["kind"], c["a"]): (c["verdict"], c["n"]) for c in dg["c_align"]}

    floor_r = {c: dict(rej=[], not_rej=[]) for c in ("aal", "dk")}

    def note_floor(c, r, p_naive):
        rej = p_naive < G.ALPHA_V
        floor_r[c]["rej"].append(r[rej])
        floor_r[c]["not_rej"].append(r[~rej])

    cells, pooled = [], {}
    for c in G.CATCH_CLASSES:
        for fam in FAMS:
            rs, hs = [], []
            for a in A_CATCH:
                d = G.load_existing(f"{c}_{fam}_m25_a{a:g}")
                if d is None:
                    raise SystemExit(f"missing plant file for {c} {fam} a={a:g}")
                d = d[d["status"] == "ok"]
                r = d["r"].to_numpy(float)
                assert np.isfinite(r).all()
                hit = ((d["p_verdict_a3"] < G.ALPHA_V) & (d["verdict_status_a3"] == "ok")).to_numpy()
                k, n = int(hit.sum()), int(len(d))
                if (k, n) != reg[(c, fam, a)]:
                    raise SystemExit(f"{c} {fam} a={a:g}: verdict catch {k} / {n} differs from e3_catch_curves_a5.json "
                                     f"{reg[(c, fam, a)]}")
                cells.append(dict(cls=c, family=fam, a=a, k=k, n=n, rate=k / n, r=quantiles(r), bins=bins(r, hit)))
                note_floor(c, r, d["p_naive"].to_numpy(float))
                rs.append(r)
                hs.append(hit)
            pooled[f"{c}|{fam}"] = bins(np.concatenate(rs), np.concatenate(hs))
    for name, sha in G.INPUTS.items():  # the files load_existing read
        want = cc["inputs_sha256"].get(name)
        if want != sha:
            raise SystemExit(f"{name}: sha256 differs from e3_catch_curves_a5.json")
    assert len(G.INPUTS) == 24, len(G.INPUTS)

    align, align_sha, pooled_align, align_by_a = [], {}, {}, []
    for c in ("aal", "dk"):
        rs, hs = [], []
        for a in A_ALIGN:
            f = G.A3 / f"{c}_C-align_wmod_{a}.csv.gz"
            align_sha[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
            if dg["inputs_sha256"].get(f.name) != align_sha[f.name]:
                raise SystemExit(f"{f.name}: sha256 differs from e3_a3_leg_diagnostics.json")
            d = pd.read_csv(f)
            ra = d["r"].to_numpy(float)
            ha = ((d["p_verdict"] < G.ALPHA_V) & (d["verdict_status"] == "ok")).to_numpy()
            align_by_a.append(dict(cls=c, family="C-align", a=float(a), n=int(len(d)), k=int(ha.sum()),
                                   bins=bins(ra, ha)))  # the three set kinds pooled
            note_floor(c, ra, d["p_naive"].to_numpy(float))
            for kind, g in d.groupby("kind"):
                r = g["r"].to_numpy(float)
                assert np.isfinite(r).all()
                hit = ((g["p_verdict"] < G.ALPHA_V) & (g["verdict_status"] == "ok")).to_numpy()
                want, n_want = reg_align[(c, kind, float(a))]
                if round(float(hit.mean()), 4) != want or len(g) != n_want:
                    raise SystemExit(f"{c} C-align {kind} a={a}: verdict catch differs from e3_a3_leg_diagnostics.json")
                align.append(dict(cls=c, family="C-align", kind=kind, a=float(a), k=int(hit.sum()), n=int(len(g)),
                                  rate=float(hit.mean()), r=quantiles(r)))
                rs.append(r)
                hs.append(hit)
        pooled_align[f"{c}|C-align"] = bins(np.concatenate(rs), np.concatenate(hs))

    floor = {}
    for c, v in floor_r.items():
        rej, nrej = np.concatenate(v["rej"]), np.concatenate(v["not_rej"])
        lo, hi = float(nrej.max()), float(rej.min())
        assert lo < hi, f"{c}: the parametric p is not monotone in r ({lo} >= {hi})"  # one n per class
        floor[c] = dict(largest_r_not_rejecting=lo, smallest_r_rejecting=hi, n_plants=int(len(rej) + len(nrej)))
    out = dict(
        status="POST HOC descriptor (2026-11-11): observed map-set correlation of the stored catch plants and verdict "
               "catch by observed r; not registered, not a gate; no plant rerun, no p-value recomputed",
        parametric_floor=floor, c_align_bins_by_a=align_by_a,
        alpha_v=G.ALPHA_V, r_definition="Pearson correlation of the planted map with the set's raw mean-expression "
                                        "score, signed in the registered direction (+1); e3_plants.py:114",
        bin_edges=EDGES[:-1] + [1.0], bin_labels=LABELS,
        reproduces=dict(e3_catch_curves_a5="k / n equal in all 12 cells", e3_a3_leg_diagnostics="verdict rate (4 dp) "
                        "and n equal in all 18 cells"),
        cells=cells, catch_by_observed_r=pooled, c_align_cells=align, c_align_catch_by_observed_r=pooled_align,
        inputs_sha256=dict(G.INPUTS, **{f"artifacts/plants_a3/{k}": v for k, v in align_sha.items()}),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        commit=G.git("rev-parse", "HEAD"), dirty=bool(G.git("status", "--porcelain")))
    (G.RES / "e3_observed_r_a5.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")

    def f3(x):
        return "-" if x is None else f"{x:.3f}"

    L = [f"# Observed map-set correlation of the catch plants — GENERATED by e3_observed_r_a5.py @ {out['commit'][:7]}; "
         "do not hand-edit", "",
         "POST HOC descriptor (2026-11-11; not registered, not a gate). r = Pearson correlation of the planted map with "
         "the set's raw mean-expression score. Verdict catch at alpha_v = .025, asserted equal to "
         "e3_catch_curves_a5.json (C-sp, C-gene) and e3_a3_leg_diagnostics.json (C-align).", "",
         "## 1. Observed r by planted strength", "",
         "| class | plant | set kind | a | verdict k / n | verdict | r p10 | r q25 | r median | r q75 | r p90 | share r <= 0 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for x in cells + align:
        q = x["r"]
        L.append(f"| {x['cls']} | {x['family']} | {x.get('kind', 'rand-25')} | {x['a']:g} | {x['k']} / {x['n']} | "
                 f"{x['rate']:.3f} | {q['p10']:.3f} | {q['q25']:.3f} | {q['median']:.3f} | {q['q75']:.3f} | "
                 f"{q['p90']:.3f} | {q['share_r_le_0']:.3f} |")
    L += ["", "## 2. Verdict catch by observed r (signed; k / n and rate), by planted strength a and pooled", "",
          "The pooled rows depend on the equal numbers of plants per a. C-align rows pool the three set kinds.", "",
          "| class | plant | a | " + " | ".join(LABELS) + " |", "|---|---|---|" + "---|" * len(LABELS)]

    def brow(bs):
        return " | ".join(f"{b['k']} / {b['n']} ({f3(b['rate'])})" for b in bs)

    for c in ("aal", "dk"):
        for fam in FAMS + ["C-align"]:
            for x in (cells if fam != "C-align" else align_by_a):
                if (x["cls"], x["family"]) == (c, fam):
                    L.append(f"| {c} | {fam} | {x['a']:g} | {brow(x['bins'])} |")
            L.append(f"| {c} | {fam} | pooled | {brow((pooled if fam != 'C-align' else pooled_align)[f'{c}|{fam}'])} |")
    L += ["", "## 3. The parametric leg's floor (one-sided p at alpha_v, from the stored p_naive)", "",
          "| class | largest r not rejecting | smallest r rejecting | plants |", "|---|---|---|---|"]
    for c, v in floor.items():
        L.append(f"| {c} | {v['largest_r_not_rejecting']:.4f} | {v['smallest_r_rejecting']:.4f} | {v['n_plants']} |")
    (G.RES / "e3_observed_r_a5.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    for x in L[4:]:
        print(x)


if __name__ == "__main__":
    main()
