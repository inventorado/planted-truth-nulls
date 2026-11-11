"""ASDG-AUD-E3 gates under prereg_amend_3 §5 (draft v3; the fourth-corner max-test verdict). `e3_gates.py` stays as the
record of the frozen §6.4 verdict; this file evaluates the amended one.

Verdict at alpha_v = .025: survives iff Level 0, the class-stratified site leg (max of S1c, S2c) and the species leg
(max of G1, G3m, G6s, G6l; every null set conditioned on S's between-class part) each have p < .025 and its status is
ok — G6l unmatched or degenerate, 'species leg uninformative' and 'resolution-limited' are non-rejections (misses in
catch and power gates); the uninformative / resolution-limited plants stay in the species-leg false-alarm denominator
as non-rejections (§2). Reads artifacts/plants_a3/*.csv.gz (e3_align_plants.py), the existing
artifacts/plants/<cell>.csv.gz with artifacts/plants/a3species_<cell>.csv.gz (e3_species_replay.py), and the frozen
e3_gates.json (naive plant-active, P+1, P+2). Writes arcs/audit/results/e3_gates_a3.json and .md: every gate with
k / n, its class-step strata (step 0, step 1) and generator cells, missing and blocked counts. Missing input -> the gate
is "not run"; K1 is fired / not fired / not fired (partial certification) / incomplete. Partial certification covers
false-alarm gates only; a plant-active or planted-leg failure anywhere (the replica included) fires K1. Planted toy gate
cases run before every evaluation.
Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e3_gates_a3.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from e3_plants import GENERATOR_CELLS, N_SURR as N_SURR_E3  # noqa: E402
import e3_align_plants as AP  # noqa: E402

PL, A3 = ROOT / "artifacts" / "plants", ROOT / "artifacts" / "plants_a3"
RES = ROOT / "arcs" / "audit" / "results"
ALPHA_V, CAP, CATCH, POWER, ACTIVE, MAX_MISSING = 0.025, 0.05, 0.80, 0.50, 0.05, 0.05
assert ALPHA_V == AP.ALPHA_V
CLASSES, CATCH_CLASSES, WS = ["aal", "dk", "cc200"], ["aal", "dk"], [0.5, 0.9]
TARGETS = {"aal": ["wmod", "grad", "mod", "brain"], "dk": ["wmod", "grad", "mod", "brain"],
           "cc200": ["wmod", "grad", "mod", "brain"], "dk-ctx": ["mod", "grad", "brain"]}  # false-alarm strata
PA_TARGETS = {c: ["wmod", "grad", "brain"] for c in CLASSES} | {"dk-ctx": ["mod", "grad", "brain"]}  # §5 plant-active
LARGE = {"brand-500", "multi-500", "multi-1000"}


def git(*args) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True).stdout.strip()


INPUTS: dict[str, str] = {}


def kinds(target: str) -> list[str]:
    return AP.BRAIN_KINDS if target == "brain" else AP.ALL_KINDS


def read(f: Path) -> pd.DataFrame:
    INPUTS[f.relative_to(ROOT).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    return pd.read_csv(f)


def add_verdict(d: pd.DataFrame, site_col: str, site_floor: float) -> pd.DataFrame:
    """The amended verdict (§2) from its legs: p_verdict_a3 is NaN unless the status is ok."""
    st = [AP.verdict_status(r, site_floor) for r in
          d[["g6l_status", "uninformative", "resolution_limited"]].to_dict("records")]
    p = pd.concat([d["p_naive"], d[site_col], d["p_species"]], axis=1).max(axis=1, skipna=False)
    d = d.assign(verdict_status_a3=st,
                 species_blocked=d["uninformative"].astype(bool) | d["resolution_limited"].astype(bool))
    return d.assign(p_verdict_a3=p.where(d["verdict_status_a3"] == "ok"))


def load_a3(atlas, family, target, wa):
    f = A3 / f"{atlas}_{family}_{target}_{wa:g}.csv.gz"
    if not f.exists():
        return None
    d = add_verdict(read(f), "p_site", 1 / (AP.N_SURR + 1))
    assert (d["verdict_status_a3"] == d["verdict_status"]).all(), f"{f.name}: verdict status drift"
    assert np.allclose(d["p_verdict_a3"], d["p_verdict"], rtol=0, atol=0, equal_nan=True), f"{f.name}: verdict drift"
    return d


def load_existing(cell):
    f, fs = PL / f"{cell}.csv.gz", PL / f"a3species_{cell}.csv.gz"
    if not (f.exists() and fs.exists()):
        return None
    d = read(f)
    s = read(fs)
    assert s["replay_ok"].all() and len(s) == len(d), f"{cell}: species replay incomplete or unfaithful"
    keep = ["i", "p_G1", "p_G3m", "p_G6s", "p_G6l", "p_species", "uninformative", "resolution_limited", "g6l_status"]
    d = d.merge(s[keep].rename(columns={"p_G1": "p_G1c"}), on="i", how="left", validate="one_to_one")
    gc = [GENERATOR_CELLS[int(i) % len(GENERATOR_CELLS)] for i in d["i"]]
    d["gen"], d["step"] = [g for g, _ in gc], [st for _, st in gc]
    return add_verdict(d, "p_L1_strat", 1 / (N_SURR_E3 + 1))


def rate_gate(d, col, label, kind, *, floor=None, computed_only=True, missing_rule=False, meta=None, block=None,
              status_col=None):
    """kind: 'fa' (rate <= CAP), 'catch' (rate >= floor), 'mustfail' (rate > CAP: a planted flawed leg is caught).
    A missing p (NaN) is never a rejection; computed_only drops it from the denominator. block: a boolean column of
    computed plants that cannot reject (§2 labels): kept in the denominator as non-rejections (misses in catch gates).
    Reported with the whole-stratum k / n: the class-step strata (step 0, step 1) and every generator cell."""
    base = dict(gate=label, kind=kind, **(meta or {}))
    if d is None or len(d) == 0:
        return {**base, "status": "not run", "pass_": False}
    x = d[col]
    miss = x.isna()
    blocked = (d[block].astype(bool) & ~miss) if block else pd.Series(False, index=d.index)
    t = pd.DataFrame({"gen": d["gen"].to_numpy(), "step": d["step"].to_numpy(), "miss": miss.to_numpy(),
                      "rej": ((x < ALPHA_V) & ~blocked).to_numpy(), "blocked": blocked.to_numpy()})

    def kn(g):
        n_ = int((~g["miss"]).sum()) if computed_only else int(len(g))
        k_ = int(g["rej"].sum())
        return dict(k=k_, n=n_, rate=k_ / n_ if n_ else float("nan"), missing=int(g["miss"].sum()),
                    blocked=int(g["blocked"].sum()))

    w = kn(t)
    out = {**base, "k": w["k"], "n": w["n"], "n_plants": int(len(t)), "missing_n": w["missing"],
           "blocked_n": w["blocked"], "missing_max_cell": float(t.groupby(["gen", "step"])["miss"].mean().max()),
           "by_step": {f"{s:g}": kn(g) for s, g in t.groupby("step")},
           "by_cell": {f"{a}|{s:g}": kn(g) for (a, s), g in t.groupby(["gen", "step"])}, "status": "ok"}
    if status_col:
        out["status_counts"] = {str(k): int(v) for k, v in d[status_col].value_counts().items()}
    if w["n"] == 0:
        return {**out, "rate": float("nan"), "pass_": False, "status": "fail: no computed plants"}
    r = w["rate"]
    out["rate"] = r
    out["pass_"] = bool(r <= CAP) if kind == "fa" else bool(r >= floor) if kind == "catch" else bool(r > CAP)
    if missing_rule and out["missing_max_cell"] > MAX_MISSING:
        out.update(pass_=False, status=f"fail: {out['missing_max_cell']:.1%} unmatched in a generator cell (> 5 %)")
    return out


def selftest() -> list[str]:
    def toy(n, k, miss=0):
        gc = [GENERATOR_CELLS[i % 10] for i in range(n)]
        p = np.full(n, 0.5)
        p[np.linspace(0, n - 1, k).astype(int) if k else []] = 0.01
        d = pd.DataFrame({"p": p, "gen": [g for g, _ in gc], "step": [s for _, s in gc]})
        if miss:
            d.loc[d.index[(d["gen"] == "grf15") & (d["step"] == 0.0) & (d["p"] > 0.1)][:miss], "p"] = np.nan
        return d
    fa = lambda d, **kw: rate_gate(d, "p", "", "fa", **kw)  # noqa: E731
    cases = [("FA 50/1000 passes", fa(toy(1000, 50))["pass_"], True),
             ("FA 51/1000 fails", fa(toy(1000, 51))["pass_"], False),
             ("FA with 6 % unmatched in a cell fails", fa(toy(1000, 10, miss=6), missing_rule=True)["pass_"], False),
             ("verdict FA: all plants in the denominator", fa(toy(1000, 50, miss=30), computed_only=False)["n"], 1000),
             ("CATCH 800/1000 passes", rate_gate(toy(1000, 800), "p", "", "catch", floor=CATCH)["pass_"], True),
             ("CATCH 799/1000 fails", rate_gate(toy(1000, 799), "p", "", "catch", floor=CATCH)["pass_"], False),
             ("MUSTFAIL at .06 caught", rate_gate(toy(1000, 60), "p", "", "mustfail")["pass_"], True),
             ("MUSTFAIL at .05 not caught", rate_gate(toy(1000, 50), "p", "", "mustfail")["pass_"], False)]
    # the §2 block: blocked rejections are non-rejections in false-alarm gates (denominator kept) and misses in catch
    # gates; class-step strata are reported and sum to the whole
    tb = toy(1000, 60)
    tb["blk"] = False
    tb.loc[tb.index[tb["p"] < 0.1][:10], "blk"] = True
    g_fa = fa(tb, block="blk")
    g_c = rate_gate(toy(1000, 800).assign(blk=lambda d: d.index < 5), "p", "", "catch", floor=CATCH, block="blk")
    cases += [("blocked FA: 60 rejections, 10 blocked -> 50 / 1000 passes", (g_fa["k"], g_fa["n"], g_fa["pass_"]),
               (50, 1000, True)),
              ("blocked catch: 800 minus blocked rejections < .80 fails", g_c["pass_"], False),
              ("step strata reported", sorted(g_fa["by_step"]), ["0", "1"]),
              ("step strata sum to the whole", sum(v["k"] for v in g_fa["by_step"].values()), g_fa["k"]),
              ("generator cells reported", len(g_fa["by_cell"]), 10)]
    # the verdict's status rule (§2) and its application to a frame
    vs = lambda st, un=False, rl=False, floor=1 / 501: AP.verdict_status(  # noqa: E731
        dict(g6l_status=st, uninformative=un, resolution_limited=rl), floor)
    cases += [("status: unmatched G6l", vs("unmatched"), "g6l unmatched"),
              ("status: degenerate G6l", vs("degenerate"), "g6l degenerate"),
              ("status: uninformative", vs("ok", un=True), "uninformative"),
              ("status: species floor", vs("ok", rl=True), "resolution-limited"),
              ("status: site floor", vs("ok", floor=0.03), "resolution-limited"),
              ("status: ok", vs("ok"), "ok")]
    fr = pd.DataFrame(dict(p_naive=[0.001, 0.001, 0.001], p_site=[0.01, 0.01, 0.2], p_species=[0.02, 0.02, np.nan],
                           g6l_status=["ok", "ok", "unmatched"], uninformative=[False, True, False],
                           resolution_limited=[False, False, False]))
    fv = add_verdict(fr, "p_site", 1 / 501)
    cases += [("verdict: max of the legs when ok; NaN when blocked or unmatched",
               [None if np.isnan(v) else v for v in fv["p_verdict_a3"]], [0.02, None, None]),
              ("species_blocked marks the uninformative plant", fv["species_blocked"].tolist(), [False, True, False])]
    # partial-certification classifier
    g_large = dict(gate="x", status="ok", pass_=False, group="species_fa", atlas="aal", kind_set="multi-1000")
    g_ctx = dict(gate="y", status="ok", pass_=False, group="species_fa", atlas="dk-ctx", kind_set="rand-25")
    g_other = dict(gate="z", status="ok", pass_=False, group="species_fa", atlas="aal", kind_set="rand-25")
    g_ctx_pa = dict(gate="w", status="ok", pass_=False, group="plant_active", atlas="dk-ctx")
    cases += [("partial: large-only failure", classify([g_large])[0], "not fired (partial certification)"),
              ("partial: replica-only failure", classify([g_ctx])[0], "not fired (partial certification)"),
              ("other failure fires K1", classify([g_large, g_other])[0], "fired"),
              ("replica plant-active failure fires K1", classify([g_ctx, g_ctx_pa])[0], "fired")]
    return [f"{a}: got {b}, expected {c}" for a, b, c in cases if b != c]


def computed(g) -> bool:
    return g["status"] == "ok" or g["status"].startswith("fail")


def classify(all_gates: list[dict]) -> tuple[str, list[str], list[str], list[str]]:
    """(K1 status, K1 reasons, partial labels, not evaluated). Partial certification (§5) covers species-leg and
    verdict false-alarm failures confined to m > 300 kinds or to the cortex-only replica; any other failure fires K1."""
    fails = [g for g in all_gates if computed(g) and not g["pass_"]]
    missing = [g["gate"] for g in all_gates if not computed(g)]
    fa_groups = {"species_fa", "verdict_fa_align"}
    partial, hard = set(), []
    for g in fails:
        if g.get("group") in fa_groups and g.get("kind_set") in LARGE:
            partial.add("claims with m > 300: uncertified (species leg)")
        elif g.get("group") in fa_groups and g.get("atlas") == "dk-ctx":
            partial.add("single-class claims: uncertified")
        else:
            hard.append(f"{g.get('group')}: {g['gate']} ({g['status']}; rate={g.get('rate', float('nan')):.3f})")
    if hard:
        return "fired", hard + [f"(also) {p}" for p in sorted(partial)], sorted(partial), missing
    if missing:
        return "incomplete", [], sorted(partial), missing
    return ("not fired (partial certification)" if partial else "not fired"), [], sorted(partial), missing


def main():
    failed = selftest()
    if failed:
        raise SystemExit("SELFTEST FAILED:\n  " + "\n  ".join(failed))
    gates = {k: [] for k in ("species_fa", "verdict_fa_align", "verdict_fa_existing", "verdict_catch", "power",
                             "plant_active", "planted_legs")}
    descriptors = {"site_rate_T-mod_not_gated": []}
    frames = {}
    for c, targets in TARGETS.items():
        for t in targets:
            for w in WS:
                d = load_a3(c, "F-align", t, w)
                frames[(c, t, w)] = d
                for kd in kinds(t):
                    sub = None if d is None else d[d["kind"] == kd]
                    meta = dict(atlas=c, target=t, w=w, kind_set=kd)
                    lab = f"{c} {t} w={w:g} {kd}"
                    gates["species_fa"].append(rate_gate(sub, "p_species", f"SPECIES FA {lab}", "fa",
                                                         missing_rule=True, block="species_blocked",
                                                         status_col="verdict_status_a3",
                                                         meta={**meta, "group": "species_fa"}))
                    gates["verdict_fa_align"].append(rate_gate(sub, "p_verdict_a3", f"VERDICT FA {lab}", "fa",
                                                               computed_only=False, status_col="verdict_status_a3",
                                                               meta={**meta, "group": "verdict_fa_align"}))
            d9 = frames.get((c, t, 0.9))
            gated = t in PA_TARGETS[c]
            lab = f"ACTIVE {c} {t} w=.9 (max over kinds)"
            if d9 is None:
                if gated:
                    gates["plant_active"].append(dict(gate=lab, status="not run", pass_=False, group="plant_active",
                                                      atlas=c))
                continue
            per = {}  # every kind's site-leg rate with its k / n, class-step strata, generator cells, status counts
            for kd, g in d9.groupby("kind"):
                rg = rate_gate(g, "p_site", "", "fa", computed_only=False, status_col="verdict_status_a3")
                per[kd] = {k: rg[k] for k in ("k", "n", "rate", "missing_n", "by_step", "by_cell", "status_counts")}
            best = max(per, key=lambda kd: per[kd]["rate"])
            entry = dict(gate=lab, rate=float(per[best]["rate"]), k=per[best]["k"], n=per[best]["n"],
                         missing_n=per[best]["missing_n"], by_step=per[best]["by_step"], best_kind=best, per_kind=per,
                         status="ok", pass_=bool(per[best]["rate"] >= ACTIVE), group="plant_active", atlas=c, target=t)
            if gated:
                gates["plant_active"].append(entry)
            else:
                descriptors["site_rate_T-mod_not_gated"].append({**entry, "pass_": None})
    for c in CLASSES:
        for fam in ("F-sp", "F-mod", "F-traj"):
            d = load_existing(f"{c}_{fam}_m25_a0")
            for st in (0.0, 1.0):
                sub = None if d is None else d[d["step"] == st]
                gates["verdict_fa_existing"].append(rate_gate(sub, "p_verdict_a3",
                                                              f"VERDICT FA {c} {fam} step={st:g}", "fa",
                                                              computed_only=False, status_col="verdict_status_a3",
                                                              meta={"group": "verdict_fa_existing", "atlas": c}))
        d = frames.get((c, "wmod", 0.5))  # plant (a): naive
        gates["planted_legs"].append(rate_gate(None if d is None else d[d["kind"] == "rand-25"], "p_naive",
                                               f"PLANT a naive {c} wmod w=.5 rand-25", "mustfail",
                                               status_col="verdict_status_a3", meta={"group": "planted_legs"}))
        d = frames.get((c, "mod", 0.9))  # plant (b): v1 G6s, pooled rand-100 / rand-300
        g = rate_gate(None if d is None else d[d["kind"].isin(["rand-100", "rand-300"])], "p_g6s_v1",
                      f"PLANT b v1-G6s {c} mod w=.9 rand-100/300", "mustfail", status_col="verdict_status_a3",
                      meta={"group": "planted_legs"})
        if c == "aal":
            g = {**g, "gate": g["gate"] + " (reported, not required)", "pass_": True, "required": False}
        gates["planted_legs"].append(g)
        d = frames.get((c, "brain", 0.9))  # plant (c): the v2 species max on the brain mirror null
        gates["planted_legs"].append(rate_gate(None if d is None else d[d["kind"] == "brand-300"], "p_v2_species",
                                               f"PLANT c v2-species {c} brain w=.9 brand-300", "mustfail",
                                               status_col="verdict_status_a3", meta={"group": "planted_legs"}))
    for c in CATCH_CLASSES:
        for fam in ("C-sp", "C-gene"):
            d = load_existing(f"{c}_{fam}_m25_a0.9")
            if d is not None:
                d = d[d["status"] == "ok"]  # frozen convention: plants never generated stay excluded
            g = rate_gate(d, "p_verdict_a3", f"VERDICT CATCH {c} {fam} a=.9", "catch", floor=CATCH,
                          computed_only=False, status_col="verdict_status_a3", meta={"group": "verdict_catch"})
            if d is not None:
                g["leg_catch"] = {col: float((d[col] < ALPHA_V).mean())
                                  for col in ("p_naive", "p_L1_strat", "p_G1c", "p_G3m", "p_G6s", "p_G6l", "p_species")}
            gates["verdict_catch"].append(g)
        d = load_a3(c, "C-align", "wmod", 0.7)
        for kd in ("rand-25", "fill-100", "brand-100"):
            gates["power"].append(rate_gate(None if d is None else d[d["kind"] == kd], "p_verdict_a3",
                                            f"POWER {c} C-align a=.7 {kd}", "catch", floor=POWER,
                                            computed_only=False, status_col="verdict_status_a3",
                                            meta={"group": "power"}))
    frozen = json.loads((RES / "e3_gates.json").read_text(encoding="utf-8"))
    naive_active = [dict(g, group="frozen_naive_active") for g in frozen["gates"]["plant_active"]
                    if g["gate"].startswith("ACTIVE naive")]
    real = frozen["real_plants"]
    all_gates = [g for gs in gates.values() for g in gs] + naive_active
    if not real["P2_pass"] or real.get("P1_by_pair", {}).get("strat") is False:
        all_gates.append(dict(gate="P+1 / P+2", status="ok", pass_=False, group="real_plants"))
    k1, reasons, partial, missing = classify(all_gates)
    out = dict(amendment="prereg_amend_3 (Level 0 & stratified site leg & max(G1, G3m, G6s, G6l), alpha_v .025)",
               K1_status=k1, K1_reasons=reasons, partial_certification=partial, K1_incomplete=missing,
               selftest="pass", gates=gates, descriptors=descriptors,
               frozen_carried=dict(naive_active=naive_active, real_plants=real,
                                   G1_plant_active="dropped (amendment 3, operator; frozen failure .094 / .085 < .10)"),
               inputs_sha256=INPUTS, script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               commit=git("rev-parse", "HEAD"), dirty=bool(git("status", "--porcelain")))
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "e3_gates_a3.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    lines = [f"# E3 gates under prereg_amend_3 — GENERATED by e3_gates_a3.py @ {out['commit'][:7]}; do not hand-edit",
             "", f"**K1: {k1}**; partial certification: {partial or 'none'}; {len(reasons)} hard failures; "
             f"{len(missing)} not evaluated", ""]
    def f3(v):
        return f"{v:.3f}" if isinstance(v, float) and v == v else ""

    for grp, gs in gates.items():
        lines += [f"## {grp}", "", "| gate | k / n | rate | step 0 | step 1 | missing | blocked | pass | status |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for g in gs:
            bs = g.get("by_step", {})
            lines.append(f"| {g['gate']} | {g.get('k', '')} / {g.get('n', '')} | {f3(g.get('rate'))} | "
                         f"{f3(bs.get('0', {}).get('rate'))} | {f3(bs.get('1', {}).get('rate'))} | "
                         f"{g.get('missing_n', '')} | {g.get('blocked_n', '')} | "
                         f"{'PASS' if g['pass_'] else 'FAIL'} | {g['status']} |")
        lines.append("")
    lines += ["## descriptors: T-mod site-leg rates in V-AAL / V-DK / V-CC200 (reported, not gated; §5)", ""]
    lines += [f"- {g['gate']}: max {g['rate']:.3f} ({g['best_kind']})" for g in descriptors["site_rate_T-mod_not_gated"]]
    (RES / "e3_gates_a3.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"K1 (amendment 3): {k1}; partial: {partial or 'none'}; hard failures {len(reasons)}; "
          f"not evaluated {len(missing)}")
    for r in reasons[:40]:
        print("  FAIL", r)


if __name__ == "__main__":
    main()
