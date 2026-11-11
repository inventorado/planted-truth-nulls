"""ASDG-AUD-E3-plants gates (prereg §6.4 as amended by prereg_amend_2: C1 is reproduction-only, not a K1 trigger).

Reads artifacts/plants/<cell>.csv.gz (e3_plants.py), artifacts/plants/j1pool_<cell>.csv.gz (e3_j1_pool_replay.py),
results/e3_p1_myelin.json, e3_p1_strat.json and e3_realplants.json. Writes arcs/audit/results/e3_gates.json (every
gate with k, n, rate, pass and its missing-plant counts; adoption decisions; K1 verdict; descriptors incl.
cascade-level rates), results/e3_gates.md (the same, rendered) and results/MANIFEST.md (prereg §7, plant half).
A plant file that is absent, or whose n differs from the registered n, makes every gate using it "incomplete"
(not pass). The gate code first runs planted failures it must catch (selftest); a missed plant aborts the run.

Conformance changes of 2026-09-23 (session 3), made before the full battery was gated (only the three V-AAL F-cells
had been seen, in the session-2 preview), each toward the frozen text:
- §6.4 "a gate fails if > 5 % of its plants in any cell are unmatched, not applicable or degenerate": applied per
  generator cell (§6.1-6.2 "cell"); previously pooled over the gate's whole population.
- §6.4 "gates use computed plants only": catch rates over computed plants (previously a missing plant counted as
  a miss); the all-plants rate is kept as a descriptor.
- §4.4 J1 "requires pool diversity (mean pairwise Jaccard < 0.5)": applied from e3_j1_pool_replay.py
  (e3_plants.py applied only the sd_k rule); a J1 gate without its replay is "incomplete".
- §6.4 P+1 "Level-1 p < 0.05 (adopted pair)": the stratified pair is measured (e3_p1_strat.py), not assumed equal.
- §6.4 "Cascade-level false-alarm and catch rates on every family are reported as descriptors": added.
- §6.4 "every count is reported": status counts per gate; §7 manifest (plant half) written; registered n checked.
- §6.4 C3 coordinate-gradient descriptor: computed by e3_c3_gradients.py (it had not been implemented), read here.
- §7 provenance: the plant-generating commit, the seed scheme and each plant file's sha256 are recorded.
- K1 is reported as fired / not fired / incomplete: an evaluated failure fires it; a gate that could not be
  evaluated (file absent, n short, J1 replay missing) is neither a pass nor a failure.
The whole set was found twice, independently: by the orchestrator and by an adversarial conformance review (asdg-skeptic,
17 items, 2026-09-23); the items that need no code are listed in DECLARED.
Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e3_gates.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
from asdg.cascade import fa_gate  # noqa: E402
from e3_plants import GENERATOR_CELLS  # noqa: E402

PL = Path(os.environ.get("E3_PLANTS_DIR", ROOT / "artifacts" / "plants"))  # overrides: code-path tests only
RES = Path(os.environ.get("E3_RESULTS_DIR", ROOT / "arcs" / "audit" / "results"))
CLASSES = ["aal", "dk", "cc200"]
CATCH_CLASSES = ["aal", "dk"]
ALPHA = 0.05
MAX_MISSING = 0.05
JACCARD_MAX = 0.5
# the registered plant factorial (prereg §6.2-6.3): (class, family, m, a) -> n
PLAN = {**{(c, f, 25, 0.0): 1000 for c in CLASSES for f in ("F-sp", "F-mod", "F-traj")},
        **{(c, f, 25, a): 300 for c in CATCH_CLASSES for f in ("C-sp", "C-gene") for a in (0.3, 0.6, 0.9)},
        **{("aal", f, m, 0.0): 300 for m in (10, 100) for f in ("F-sp", "F-mod", "F-traj")}}
STATUS_COLS = {"p_G2": ["G2_status"], "p_G4": ["G4_status"], "p_G5": ["G5_status"],
               "p_L2": ["G2_status", "G4_status", "G5_status"],
               "p_J1_joint": ["J1_status", "J1_degenerate_jaccard"],
               "p_J1_strat": ["J1_status", "J1_degenerate_jaccard"]}


def cell_name(c, f, m, a) -> str:
    return f"{c}_{f}_m{m}_a{a:g}"


def with_cells(d: pd.DataFrame) -> pd.DataFrame:
    """Generator cell of every plant from its index (plant i -> cell i mod 10, §6.2); C-gene rows that returned
    early saved none. Where a row saved its cell, it must agree."""
    gc = [GENERATOR_CELLS[int(i) % len(GENERATOR_CELLS)] for i in d["i"]]
    g, s = np.array([x[0] for x in gc]), np.array([x[1] for x in gc], dtype=float)
    if "gen" in d:
        have = d["gen"].notna().to_numpy()
        assert (d["gen"].to_numpy()[have] == g[have]).all() and (d["step"].to_numpy()[have] == s[have]).all(), \
            "saved generator cell != i mod 10"
    return d.assign(gen=g, step=s)


def with_jaccard(d: pd.DataFrame, jp: pd.DataFrame | None) -> pd.DataFrame:
    """§4.4 pool-diversity rule: J1 of a plant whose G2 pool has mean pairwise Jaccard >= 0.5 is degenerate."""
    if jp is None:
        return d.assign(J1_degenerate_jaccard=np.nan)
    assert jp["replay_ok"].all() and len(jp) == len(d) and set(jp["i"]) == set(d["i"]), "J1 replay does not cover the file"
    d = d.merge(jp[["i", "jaccard_exact"]], on="i", how="left", validate="one_to_one")
    deg = (d["jaccard_exact"] >= JACCARD_MAX).to_numpy()
    d["J1_degenerate_jaccard"] = np.where(d["jaccard_exact"].isna(), np.nan, deg)
    for col in ("p_J1_joint", "p_J1_strat"):
        if col in d:
            d.loc[deg, col] = np.nan
    return d


_CACHE: dict = {}


def load(key):
    """(data or None, meta) for one registered plant cell."""
    if key in _CACHE:
        return _CACHE[key]
    name = cell_name(*key)
    f, fj = PL / f"{name}.csv.gz", PL / f"j1pool_{name}.csv.gz"
    meta = dict(cell=name, n_registered=PLAN[key], exists=f.exists(), j1_replay=fj.exists())
    d = None
    if f.exists():
        d = with_cells(pd.read_csv(f))
        meta.update(n=int(len(d)), sha256=hashlib.sha256(f.read_bytes()).hexdigest(),
                    complete=bool(len(d) == PLAN[key] and sorted(d["i"]) == list(range(PLAN[key]))))
        d = with_jaccard(d, pd.read_csv(fj) if fj.exists() else None)
    _CACHE[key] = (d, meta)
    return d, meta


def status_counts(d: pd.DataFrame, col: str) -> dict:
    out = {"plant_status": {str(k): int(v) for k, v in d["status"].value_counts(dropna=False).items()}}
    for s in STATUS_COLS.get(col, []):
        if s in d:
            out[s] = {str(k): int(v) for k, v in d[s].value_counts(dropna=False).items()}
    return out


def evaluate(kind: str, d: pd.DataFrame, col: str, floor: float | None = None) -> dict:
    """One gate on one population. kind: 'fa' (§6.4 false-alarm), 'active' (plant-active floor), 'catch'."""
    miss = d[col].isna() if col in d else pd.Series(True, index=d.index)
    by = miss.groupby([d["gen"], d["step"]]).mean()
    at = by.idxmax()
    x = d.loc[~miss, col]
    k, n = int((x < ALPHA).sum()), int(len(x))
    out = dict(k=k, n=n, n_plants=int(len(d)), missing_n=int(miss.sum()), missing_frac=float(miss.mean()),
               missing_max_cell=float(by.max()), missing_max_cell_at=f"{at[0]}/step{at[1]:g}",
               status_counts=status_counts(d, col), status="ok")
    if n == 0:
        return {**out, "rate": float("nan"), "pass_": False, "status": "fail: no computed plants"}
    if kind == "fa":
        out.update(fa_gate(k, n))
    else:
        out.update(rate=k / n, floor=floor, pass_=bool(k / n >= floor))
        if kind == "catch":
            out["rate_all_plants"] = k / len(d)  # descriptor: a missing plant counted as a miss
    if out["missing_max_cell"] > MAX_MISSING:
        out.update(pass_=False, status=f"fail: {out['missing_max_cell']:.1%} of the plants in generator cell "
                                       f"{out['missing_max_cell_at']} unmatched / not applicable / degenerate (> 5 %)")
    return out


def gate(kind, key, col, label, floor=None, step=None, need_replay=False) -> dict:
    d, meta = load(key)
    base = dict(gate=label, kind=kind, cell=meta["cell"], col=col, step=step)
    if d is None:
        return {**base, "status": "not run", "pass_": False}
    if not meta["complete"]:
        return {**base, "status": f"incomplete: n={meta['n']} (registered {meta['n_registered']})", "pass_": False}
    if need_replay and not meta["j1_replay"]:
        return {**base, "status": "incomplete: J1 pool-diversity replay (e3_j1_pool_replay.py) not run",
                "pass_": False}
    if step is not None:
        d = d[d["step"] == step]
    return {**base, **evaluate(kind, d, col, floor)}


def cascade(d: pd.DataFrame) -> dict:
    """§6.4 descriptor: rate at which the whole cascade (Levels 0, 1, 2 [, J1]) rejects; a plant with any level
    not computed cannot survive (§4.6) and counts as not rejected."""
    out = {}
    for pair in ("joint", "strat"):
        cols = ["p_naive", f"p_L1_{pair}", "p_L2"]
        if all(c in d for c in cols):
            c0 = d[cols].max(axis=1, skipna=False)
            out[f"cascade_{pair}"] = round(float((c0 < ALPHA).mean()), 4)
            if f"p_J1_{pair}" in d:
                c1 = pd.concat([c0, d[f"p_J1_{pair}"]], axis=1).max(axis=1, skipna=False)
                out[f"cascade_{pair}_J1"] = round(float((c1 < ALPHA).mean()), 4)
    return out


def describe(d: pd.DataFrame, name: str) -> list[dict]:
    """Every p-column's rejection rate over computed plants and its missing fraction, per generator cell + ALL."""
    pcols = [c for c in d.columns if c.startswith("p_")]
    rows = []
    for (g, s), sub in [*d.groupby(["gen", "step"]), (("ALL", "ALL"), d)]:
        row = dict(file=name, gen=g, step=s, n=int(len(sub)))
        for c in pcols:
            x = sub[c].dropna()
            row[c] = round(float((x < ALPHA).mean()), 4) if len(x) else None
        row.update({f"missing_{c}": round(float(sub[c].isna().mean()), 4) for c in pcols})
        row.update(cascade(sub))
        if "coexpr" in sub:
            row["coexpr_mean"] = round(float(sub["coexpr"].mean()), 4)
        if "jaccard_exact" in sub:
            row["j1_pool_jaccard_mean"] = round(float(sub["jaccard_exact"].mean()), 4)
            row["j1_pool_jaccard_max"] = round(float(sub["jaccard_exact"].max()), 4)
        rows.append(row)
    return rows


def selftest() -> list[str]:
    """Planted failures the gate code must catch, and planted passes it must not fail."""
    def toy(n, k_reject, miss=None, jac=None):
        d = with_cells(pd.DataFrame({"i": np.arange(n), "status": "ok"}))
        p = np.full(n, 0.5)
        p[np.linspace(0, n - 1, k_reject).astype(int) if k_reject else []] = 0.01
        d["p_x"] = p
        if miss:  # (gen, step, count): that many plants of one generator cell not computed
            idx = d.index[(d["gen"] == miss[0]) & (d["step"] == miss[1]) & (d["p_x"] > ALPHA)][: miss[2]]
            d.loc[idx, "p_x"] = np.nan
        return d
    cases = [
        ("FA 50/1000 passes", evaluate("fa", toy(1000, 50), "p_x")["pass_"], True),
        ("FA 70/1000 passes (rate = 0.07)", evaluate("fa", toy(1000, 70), "p_x")["pass_"], True),
        ("FA 71/1000 fails (rate > 0.07)", evaluate("fa", toy(1000, 71), "p_x")["pass_"], False),
        ("FA fails on 6 % missing in ONE cell (0.6 % overall)",
         evaluate("fa", toy(1000, 50, miss=("grf60", 1.0, 6)), "p_x")["pass_"], False),
        ("FA passes on exactly 5 % missing in one cell", evaluate("fa", toy(1000, 50, miss=("sar9", 0.0, 5)), "p_x")["pass_"], True),
        ("CATCH 240/300 passes (0.80)", evaluate("catch", toy(300, 240), "p_x", 0.80)["pass_"], True),
        ("CATCH 239/300 fails", evaluate("catch", toy(300, 239), "p_x", 0.80)["pass_"], False),
        ("CATCH 232/300 fails (control for the computed-plants case below)",
         evaluate("catch", toy(300, 232), "p_x", 0.80)["pass_"], False),
        ("ACTIVE 150/1000 passes (0.15)", evaluate("active", toy(1000, 150), "p_x", 0.15)["pass_"], True),
        ("ACTIVE 149/1000 fails", evaluate("active", toy(1000, 149), "p_x", 0.15)["pass_"], False),
        ("no computed plants fails", evaluate("fa", toy(100, 0).assign(p_x=np.nan), "p_x")["pass_"], False),
    ]
    # catch over computed plants: 1 missing (non-rejected) plant in each of the 10 cells of a 300-plant file
    t = toy(300, 232)
    for g, s in GENERATOR_CELLS:
        t.loc[t.index[(t["gen"] == g) & (t["step"] == s) & (t["p_x"] > ALPHA)][:1], "p_x"] = np.nan
    e = evaluate("catch", t, "p_x", 0.80)
    cases.append(("CATCH 232/290 computed passes with 1 missing per cell (3.3 %)", e["pass_"], True))
    cases.append(("CATCH all-plants descriptor = 232/300", abs(e["rate_all_plants"] - 232 / 300) < 1e-12, True))
    # Jaccard rule
    j = with_jaccard(pd.DataFrame({"i": [0, 1, 2], "p_J1_joint": [0.01, 0.01, 0.5], "p_J1_strat": 0.01}),
                     pd.DataFrame({"i": [0, 1, 2], "jaccard_exact": [0.1, 0.5, 0.7], "replay_ok": True}))
    cases.append(("Jaccard >= 0.5 makes J1 missing", j["p_J1_joint"].isna().tolist(), [False, True, True]))
    # cascade: any missing level -> not rejected
    c = cascade(pd.DataFrame({"p_naive": [0.01, 0.01, 0.01, 0.2], "p_L1_joint": [0.01, 0.01, 0.2, 0.01],
                              "p_L2": [0.01, np.nan, 0.01, 0.01], "p_L1_strat": 0.01}))
    cases.append(("cascade joint = 1/4", c["cascade_joint"], 0.25))
    # gate-group state: an evaluated failure dominates; a not-evaluated gate makes the group incomplete
    ok, bad = dict(status="ok", pass_=True), dict(status="ok", pass_=False)
    missrule, notrun = dict(status="fail: 6% missing", pass_=False), dict(status="not run", pass_=False)
    cases += [("state all pass", state([ok, ok]), "pass"), ("state evaluated fail", state([ok, bad, notrun]), "fail"),
              ("state missing-rule fail", state([ok, missrule]), "fail"),
              ("state not run -> incomplete", state([ok, notrun]), "incomplete")]
    return [f"{name}: got {got}, expected {want}" for name, got, want in cases if got != want]


def computed(g: dict) -> bool:
    """A gate was evaluated on its registered population (it may still fail)."""
    return g["status"] == "ok" or g["status"].startswith("fail")


def state(gs: list[dict]) -> str:
    """'fail' if any evaluated gate fails, else 'incomplete' if any gate was not evaluated, else 'pass'."""
    if any(computed(g) and not g["pass_"] for g in gs):
        return "fail"
    return "incomplete" if any(not computed(g) for g in gs) else "pass"


def git(*args) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True).stdout.strip()


def provenance() -> dict:
    """§7: which code produced the plant files (their CSVs carry no commit) and the seed scheme."""
    paths = ["arcs/audit/src/e3_plants.py", "src/asdg"]
    files = [PL / f"{cell_name(*k)}.csv.gz" for k in PLAN]
    mt = [f.stat().st_mtime for f in files if f.exists()]
    return dict(plant_code_commit=git("log", "-1", "--format=%H %cI", "--", *paths),
                plant_code_dirty_now=bool(git("status", "--porcelain", "--", *paths)),
                plant_files_mtime_range=[pd.Timestamp(min(mt), unit="s", tz="UTC").isoformat(),
                                         pd.Timestamp(max(mt), unit="s", tz="UTC").isoformat()] if mt else None,
                seed_scheme="np.random.SeedSequence([ATLAS_ID, FAM_ID, m, round(100*a), i]); ATLAS_ID aal=1 dk=2 "
                            "cc200=3; FAM_ID F-sp=1 F-mod=2 F-traj=3 C-sp=4 C-gene=5; plant i -> generator cell i mod 10",
                j1_replay_code=git("log", "-1", "--format=%H", "--", "arcs/audit/src/e3_j1_pool_replay.py"),
                j1_replay_dirty_now=bool(git("status", "--porcelain", "--", "arcs/audit/src/e3_j1_pool_replay.py")),
                gates_code=git("log", "-1", "--format=%H", "--", "arcs/audit/src/e3_gates.py"))


DECLARED = [
    "p_naivejoint (§4.4 descriptor, Cao 2024 S17 analogue): spatial part = S1 (BrainSMASH) surrogates, the volumetric "
    "stand-in for spin; computed only for plants whose G2 matched (e3_plants.py @ef2f1ab), so it is missing wherever "
    "G2 is unmatched.",
    "p_J1_<pair> = max(p over the pair's two surrogate types) via Python max(), which returns the finite value if the "
    "second is NaN; J1_status tracks the joint pair only. A degenerate (sd_k) pool for one type but not the other "
    "cannot occur in practice; the count of J1_status == degenerate_pool is in MANIFEST.md.",
    "C-gene residualisation uses the first 3 PCs of the gene-z-scored (correlation) expression matrix; §6.3 does not "
    "say z-scored or centred.",
    "Level-1 surrogates, G-sets and J1 pools are drawn fresh per plant; C3 (e3_c3_gradients.py) shares one set of "
    "surrogates per (class, gradient) map across its sets, since the map is fixed there.",
]


def reason(g: dict) -> str:
    return f'{g["gate"]} -> FAIL (k/n={g.get("k", "-")}/{g.get("n", "-")}, rate={g.get("rate", float("nan")):.3f}, ' \
           f'missing max cell={g.get("missing_max_cell", float("nan")):.3f}, status={g["status"]})'


def render_md(out: dict) -> str:
    L = [f"# E3 gates — GENERATED by `arcs/audit/src/e3_gates.py` @ `{out['commit'][:7]}`; do not hand-edit", "",
         f"- **K1: {out['K1_status']}**; Level-1 adoption: **{out['level1_adoption']}** "
         f"(pair states {out['level1_pair_state']}); J1: **{out['j1_state']}** (adopted: {out['j1_adopted']})",
         f"- selftest: {out['selftest']}",
         f"- plant code: `{out['provenance']['plant_code_commit']}` (dirty now: {out['provenance']['plant_code_dirty_now']});"
         f" plant files written {out['provenance']['plant_files_mtime_range']}", ""]
    L += ["## K1 reasons (evaluated failures)", ""] + [f"- {r}" for r in out["K1_reasons"]] + [""]
    L += ["## Not evaluated", ""] + ([f"- {r}" for r in out["K1_incomplete"]] or ["- none"]) + [""]
    L += ["## Declared deviations", ""] + [f"- {r}" for r in out["declared_deviations"]] + [""]
    L += ["## Every gate", "", "| group | gate | k / n | rate | threshold | p_binom | missing (max cell) | pass | status |",
          "|---|---|---|---|---|---|---|---|---|"]
    for grp, gs in out["gates"].items():
        for g in gs:
            thr = "≤ .05 (α .001) and ≤ .07" if g.get("kind") == "fa" else (f"≥ {g['floor']:.2f}" if g.get("floor") else "")
            pb = f"{g['p_binom']:.2g}" if "p_binom" in g else ""
            mc = f"{g['missing_frac']:.3f} ({g['missing_max_cell']:.3f} @ {g['missing_max_cell_at']})" if "missing_frac" in g else ""
            rate = f"{g['rate']:.3f}" if isinstance(g.get("rate"), float) else ""
            L.append(f"| {grp} | {g['gate']} | {g.get('k', '')} / {g.get('n', '')} | {rate} | {thr} | {pb} | {mc} | "
                     f"{'PASS' if g['pass_'] else 'FAIL'} | {g['status']} |")
    L += ["", "## Real-data plants", "", "```", json.dumps(out["real_plants"], indent=1), "```", ""]
    allrows = [r for r in out["descriptors"] if r["gen"] == "ALL"]
    cols = ["p_naive", "p_S1", "p_S2", "p_S1c", "p_S2c", "p_L1_joint", "p_L1_strat", "p_G1", "p_G2", "p_G3", "p_G4",
            "p_G5", "p_L2", "p_J1_joint", "p_J1_strat", "p_naivejoint", "cascade_joint", "cascade_strat",
            "cascade_joint_J1", "cascade_strat_J1"]
    L += ["## Descriptors — rejection rate at .05 over computed plants, whole file (per generator cell: "
          "`e3_gates.json`)", "", "| file | n | " + " | ".join(c.replace("p_", "") for c in cols) + " |",
          "|---|---|" + "---|" * len(cols)]
    for r in allrows:
        L.append(f"| {r['file']} | {r['n']} | " + " | ".join("" if r.get(c) is None else f"{r[c]:.3f}" for c in cols) + " |")
    L += ["", "## C3 coordinate gradients (§6.4, descriptor only; no ground truth)", ""]
    if isinstance(out["c3_gradients"], str):
        L.append(out["c3_gradients"])
    else:
        c3cols = ["n", "p_naive", "p_L1_joint", "p_L1_strat", "p_G1", "p_G2", "p_G3", "p_G4", "p_G5", "p_L2",
                  "p_J1_joint", "p_J1_strat", "p_naivejoint"]
        L += ["| class | set kind | gradient | " + " | ".join(c.replace("p_", "") for c in c3cols) + " |",
              "|---|---|---|" + "---|" * len(c3cols)]
        for r in out["c3_gradients"]:
            L.append(f"| {r['atlas']} | {r['kind']} | {r['map']} | " + " | ".join(
                "" if r.get(c) is None else (str(r[c]) if c == "n" else f"{r[c]:.3f}") for c in c3cols) + " |")
    return "\n".join(L) + "\n"


def render_manifest() -> str:
    L = ["# MANIFEST — A1 `audit` factorial (prereg §7)", "",
         "GENERATED by `arcs/audit/src/e3_gates.py`; do not hand-edit. Counts are plants per generator cell.", "",
         "## Plant factorial (§6.2–6.3): class × family × size × strength × generator cell", "",
         "| class | family | m | a | generator cell | n registered | n run | G2 unmatched | G4 unmatched | "
         "G5 unmatched | G5 not applicable | J1 degenerate (sd) | J1 degenerate (Jaccard) | C-gene no G2 (no y) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key, n_reg in PLAN.items():
        d, meta = load(key)
        for g, s in GENERATOR_CELLS:
            head = f"| {key[0]} | {key[1]} | {key[2]} | {key[3]:g} | {g}/step{s:g} | {n_reg // len(GENERATOR_CELLS)} |"
            if d is None:
                L.append(head + " not run |" + " |" * 7)
                continue
            sub = d[(d["gen"] == g) & (d["step"] == s)]
            cnt = lambda col, v: int((sub[col] == v).sum()) if col in sub else 0  # noqa: E731
            jac = (str(int((sub["J1_degenerate_jaccard"] == 1).sum())) if sub["J1_degenerate_jaccard"].notna().any()
                   else "not replayed")
            L.append(head + f" {len(sub)} | {cnt('G2_status', 'unmatched')} | {cnt('G4_status', 'unmatched')} | "
                            f"{cnt('G5_status', 'unmatched')} | {cnt('G5_status', 'not applicable')} | "
                            f"{cnt('J1_status', 'degenerate_pool')} | {jac} | {cnt('status', 'unmatched_for_plant')} |")
    L += ["", "## Claims (§5)", "", "Not registered yet: the claims register (§5.2) is frozen only after the §6.4 gates "
          "allow the audit to run."]
    return "\n".join(L) + "\n"


def main():
    failed = selftest()
    if failed:
        raise SystemExit("SELFTEST FAILED (the gate code missed a planted case):\n  " + "\n  ".join(failed))
    gates = {}
    # ---- spatial adoption (§4.2 / §6.4) ----
    for pair in ("joint", "strat"):
        col = f"p_L1_{pair}"
        gates[f"level1_{pair}"] = (
            [gate("fa", (c, f, 25, 0.0), col, f"FA Level1[{pair}] {c} {f} step={s:g}", step=s)
             for c in CLASSES for f in ("F-sp", "F-mod", "F-traj") for s in (0.0, 1.0)]
            + [gate("catch", (c, "C-sp", 25, 0.9), col, f"CATCH Level1[{pair}] {c} C-sp a=0.9", floor=0.80)
               for c in CATCH_CLASSES])
    l1 = {p: state(gates[f"level1_{p}"]) for p in ("joint", "strat")}
    # joint if it passes every gate; else (joint definitively failing) strat if it passes; else K1 (§4.2)
    adopted = "joint" if l1["joint"] == "pass" else ("strat" if l1["joint"] == "fail" and l1["strat"] == "pass" else None)
    adoption = adopted or ("K1: neither pair adoptable" if l1["joint"] == l1["strat"] == "fail" else "incomplete")
    # ---- plant-active ----
    gates["plant_active"] = (
        [gate("active", (c, "F-sp", 25, 0.0), "p_naive", f"ACTIVE naive {c} F-sp", floor=0.15) for c in CLASSES]
        + [gate("active", (c, "F-mod", 25, 0.0), "p_G1", f"ACTIVE G1 {c} F-mod", floor=0.10) for c in CLASSES])
    # ---- gene-level false alarm and catch ----
    gates["gene_fa"] = ([gate("fa", (c, "F-mod", 25, 0.0), col, f"FA {col[2:]} {c} F-mod")
                         for c in CLASSES for col in ("p_L2", "p_G2", "p_G4")]
                        + [gate("fa", (c, "F-traj", 25, 0.0), "p_G5", f"FA G5 {c} F-traj") for c in CLASSES])
    gates["gene_catch"] = [gate("catch", (c, "C-gene", 25, 0.9), f"p_{g}", f"CATCH {g} {c} C-gene a=0.9", floor=0.80)
                           for c in CATCH_CLASSES for g in ("G2", "G4", "G5")]
    # ---- J1 (both pairs computed; the adopted pair's gates decide adoption) ----
    for pair in ("joint", "strat"):
        col = f"p_J1_{pair}"
        gates[f"j1_{pair}"] = ([gate("fa", (c, f, 25, 0.0), col, f"FA J1[{pair}] {c} {f}", need_replay=True)
                                for c in CLASSES for f in ("F-sp", "F-mod")]
                               + [gate("catch", (c, "C-gene", 25, 0.9), col, f"CATCH J1[{pair}] {c} C-gene a=0.9",
                                       floor=0.80, need_replay=True) for c in CATCH_CLASSES])
    j1_adopted = (state(gates[f"j1_{adopted}"]) == "pass") if adopted else False
    j1_state = state(gates[f"j1_{adopted}"]) if adopted else "undefined (no Level-1 pair adopted)"
    # ---- real-data plants (§6.4; C1 reproduction-only by prereg_amend_2) ----
    p1 = json.loads((RES / "e3_p1_myelin.json").read_text(encoding="utf-8"))
    p1s = json.loads((RES / "e3_p1_strat.json").read_text(encoding="utf-8")) if (RES / "e3_p1_strat.json").exists() else None
    rp = json.loads((RES / "e3_realplants.json").read_text(encoding="utf-8"))
    p1_by_pair = dict(joint=bool(p1["P1_pass_if_joint_adopted"]),
                      strat=None if p1s is None else bool(p1s["P1_pass_if_strat_adopted"]))
    real = dict(P1_by_pair=p1_by_pair, P1_pass=p1_by_pair.get(adopted) if adopted else None,
                P1_values=dict(rho=p1["rho"], p_L1_joint=p1["p_L1_joint"],
                               p_L1_strat=None if p1s is None else p1s["p_L1_strat"], p_S3=p1["p_S3_vasa"]),
                P2_pass=bool(rp["P2_pass"]),
                C1="reproduction only (prereg_amend_2); under v3 it failed its must-catch pattern (ASDG-AUD-F1-c1fail)")
    # ---- K1 (§6.4 as amended): fired on any evaluated failure; 'incomplete' if nothing failed but a gate is missing
    k1, k1_missing = [], []
    if l1["joint"] == l1["strat"] == "fail":
        for pair in ("joint", "strat"):
            fails = [g["gate"] for g in gates[f"level1_{pair}"] if computed(g) and not g["pass_"]]
            k1.append(f"Level-1 {pair} pair not adoptable: {len(fails)} gate(s) fail: {'; '.join(fails)}")
    elif adopted is None:
        k1_missing.append(f"Level-1 adoption undecided (joint: {l1['joint']}, strat: {l1['strat']})")
    for key in ("plant_active", "gene_fa", "gene_catch"):
        k1 += [reason(g) for g in gates[key] if computed(g) and not g["pass_"]]
        k1_missing += [f'{g["gate"]}: {g["status"]}' for g in gates[key] if not computed(g)]
    if adopted is not None and real["P1_pass"] is False:
        k1.append(f"P+1 under the adopted pair ({adopted})")
    elif adopted is not None and real["P1_pass"] is None:
        k1_missing.append(f"P+1 under the adopted pair ({adopted}) not measured")
    if not real["P2_pass"]:
        k1.append("P+2")
    k1_status = "fired" if k1 else ("incomplete" if k1_missing else "not fired")
    # ---- descriptors ----
    desc = []
    for key in PLAN:
        d, meta = load(key)
        if d is not None:
            desc += describe(d, meta["cell"])
    files = {m["cell"]: dict(n=m.get("n"), n_registered=m["n_registered"], complete=m.get("complete", False),
                             sha256=m.get("sha256"), j1_replay=m["j1_replay"])
             for m in (load(k)[1] for k in PLAN)}
    c3f = RES / "e3_c3_gradients.json"
    c3 = json.loads(c3f.read_text(encoding="utf-8"))["rates"] if c3f.exists() else "not run (e3_c3_gradients.py)"
    out = dict(adopted_level1_pair=adopted, level1_adoption=adoption, level1_pair_state=l1, j1_adopted=j1_adopted,
               j1_state=j1_state, real_plants=real, K1_status=k1_status, K1_fired=k1_status == "fired",
               K1_reasons=k1, K1_incomplete=k1_missing, selftest="pass (all planted gate cases caught)",
               gates=gates, descriptors=desc, c3_gradients=c3, declared_deviations=DECLARED, provenance=provenance(),
               plant_files=files, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               commit=git("rev-parse", "HEAD"))
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "e3_gates.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    (RES / "e3_gates.md").write_text(render_md(out), encoding="utf-8")
    (RES / "MANIFEST.md").write_text(render_manifest(), encoding="utf-8")
    back = json.loads((RES / "e3_gates.json").read_text(encoding="utf-8"))
    assert back["K1_status"] == out["K1_status"] and len(back["descriptors"]) == len(desc), "read-back mismatch"
    print(f"Level-1 adoption: {adoption} {l1}; J1: {j1_state}; K1: {k1_status}")
    for r in k1:
        print("  K1:", r)
    for r in k1_missing:
        print("  not evaluated:", r)


if __name__ == "__main__":
    main()
