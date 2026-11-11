"""P11 (functional): T_abs (RUN_PLAN.md v3.1 §7 P11: "T_abs | dk-ctx, V-DK, V-AAL | unconditioned legs 21-25; upper
tail (lower for a stated depletion); values = direct computation"; claims_register.md:309-313).

Production side: run.g_tabs (descriptors.t_abs_legs on adapters.TAbs, built from the prepared decoded-list claim as
run.g_tabs builds it), its leg-25 windows from plant_mode.streams_screen on the T_abs G6l stream; run once with the
upper tail and once with a stated depletion (the same keys). Direct side, computed independently of the adapters:
every per-gene r by np.corrcoef; S1c / S2c surrogates by asdg.spatial.site_null on the leg-21 / 22 integer seeds; G1
/ G3m sets by asdg.genesets.random_sets / an explicit loop on the leg-23 / 24 streams; G6l = the leg-25 windows; every
null = mean |r| over the set (UNCONDITIONED); p = (k + 1)/(n + 1) in both directions.
"""
from __future__ import annotations

import numpy as np
from scipy import stats

from .. import run as R
from .. import seeds as SD
from asdg.genesets import random_sets
from asdg.spatial import site_null
from . import base as BS
from . import common as C
from . import construct as CO
from . import criteria as CR

TIE = 1e-10


class P11(BS.PlantSpec):
    id = "P11"
    module = "p11"
    kind = CR.FUNCTIONAL
    row = ("RUN_PLAN §7 P11: T_abs, dk-ctx / V-DK / V-AAL: unconditioned legs 21-25; upper tail (lower for a stated "
           "depletion); values = direct computation")
    construction = "C-gene (prereg §6.3), m = 25, a = .9; T_abs legs at plant K through run.g_tabs; direct recomputation"
    choices = (
        "PLANT CHOICE (not in §7): n = 5 maps per class (a functional plant: exact assertions), P3's C-gene "
        "construction (a = .9; plant id 11, cases 0..4, an unmatched plant replaced by the next case).",
        "PLANT CHOICE (not in §7): p's compared exactly (==); a null value within 1e-10 of the observed T (a float tie "
        "between the two computations) is counted and reported, and only then may the two p's differ by the tied "
        "states (k / (n + 1)).",
    )
    replace_unmatched = True
    cost_s = 20.0

    def cells(self):
        return [BS.Cell(c, c, "t-abs") for c in ("dk-ctx", "V-DK", "V-AAL")]

    def n_official(self, cell):
        return 5

    def case_of(self, cell, i):
        return int(i)

    def run_case(self, cell, i, K):
        keys = self.keys(cell, i)
        c = CO.cgene(cell.cls, keys.rng(), i)
        if c["status"] != "ok":
            return dict(status="unmatched for plant", S=BS.gene_list(c["S"]), seeds=keys.record())
        S = np.asarray(c["S"], dtype=int)
        pr = C.prepare("decoded-list", cell.cls, c["y"], S)
        screen = C.g6l_screen(pr, keys, K, stream="T_abs G6l")
        sc = keys.callables()
        runs = {}
        for dep in (False, True):
            pr.plan["depletion"] = dep
            runs[dep] = R.g_tabs(pr, K, sc, screen)
        direct = direct_tabs(pr, S, keys, K, screen)
        problems = check(runs, direct, keys)
        if problems:
            raise AssertionError("P11: " + "; ".join(problems))
        up = runs[False]
        return dict(status="computed", S=BS.gene_list(S), T=float(up["T"]), T_direct=direct["T"],
                    legs={k: dict(p=C.pdir(v["p"]), seed_leg=v.get("seed_leg"), status=v.get("status"))
                          for k, v in up["legs"].items()},
                    near_ties=direct["near_ties"], tails=dict(upper=up["tail_direction"],
                                                              depletion=runs[True]["tail_direction"]),
                    checks="all held", seeds=keys.record())

    def summarise(self, cell, recs, n_official):
        comp = [r for r in recs if r["status"] == "computed"]
        res = "PASS" if len(comp) == n_official else CR.NOT_EVALUATED_DEV % (len(comp), n_official)
        return dict(n_cases=len(recs), n_computed=len(comp), near_ties=sum(sum(r["near_ties"].values()) for r in comp),
                    criterion=dict(kind=CR.FUNCTIONAL, result=res, threshold="every assertion holds on every map "
                                   "(a failed assertion stops the plant: a code defect)"))


def _p_direct(null, obs) -> tuple[dict, dict]:
    null = np.asarray(null, dtype=float)
    n = null.size
    ties = int(np.sum(np.abs(null - obs) < TIE))
    return ({1: (int(np.sum(null >= obs)) + 1) / (n + 1), -1: (int(np.sum(null <= obs)) + 1) / (n + 1)},
            dict(ties=ties, n=int(n)))


def direct_tabs(pr, S, keys, K, screen) -> dict:
    ctx, y = pr.ctx, np.asarray(pr.y, dtype=float)
    r = np.array([np.corrcoef(y, ctx.X[:, g])[0, 1] for g in range(ctx.G)])
    ar = np.abs(r)
    T = float(ar[S].mean())
    a, b = ar[S], np.delete(ar, S)
    t, _ = stats.ttest_ind(a, b, equal_var=False)
    va, vb = a.var(ddof=1) / a.size, b.var(ddof=1) / b.size
    df = (va + vb) ** 2 / (va ** 2 / (a.size - 1) + vb ** 2 / (b.size - 1))
    out = dict(T=T, p={"Level 0": {1: float(stats.t.sf(t, df)), -1: float(stats.t.cdf(t, df))}}, near_ties={},
               n_null={})
    Xs = ctx.X[:, S]
    for leg, no, method in (("S1c", 21, "brainsmash"), ("S2c", 22, "msr")):
        seed = SD.seed_int(keys.leg(no))
        sur, info = site_null(y, ctx.D, ctx.classes, int(K["site"]), seed, method)
        null = np.array([np.mean([abs(np.corrcoef(s, Xs[:, j])[0, 1]) for j in range(len(S))]) for s in sur])
        out["p"][leg], _nt = _p_direct(null, T)
        out["near_ties"][leg], out["n_null"][leg] = _nt["ties"], _nt["n"]
        out[f"{leg}_seed"] = seed
    m, Kg = len(S), int(K["species"])
    g1 = random_sets(np.arange(ctx.G), m, Kg, np.random.default_rng(keys.leg(23)), exclude=S)
    out["p"]["G1"], _nt = _p_direct(ar[g1].mean(1), T)
    out["near_ties"]["G1"], out["n_null"]["G1"] = _nt["ties"], _nt["n"]
    brain = np.zeros(ctx.G, bool)
    brain[ctx.brain] = True
    f = int(brain[S].sum())
    pb = np.setdiff1d(np.flatnonzero(brain), S)
    pn = np.setdiff1d(np.flatnonzero(~brain), S)
    rng = np.random.default_rng(keys.leg(24))
    g3 = np.stack([np.concatenate([rng.choice(pb, size=f, replace=False), rng.choice(pn, size=m - f, replace=False)])
                   for _ in range(Kg)])
    out["p"]["G3m"], _nt = _p_direct(ar[g3].mean(1), T)
    out["near_ties"]["G3m"], out["n_null"]["G3m"] = _nt["ties"], _nt["n"]
    sets = screen[0]
    if sets is not None:
        out["p"]["G6l"], _nt = _p_direct(ar[np.asarray(sets, dtype=int)].mean(1), T)
        out["near_ties"]["G6l"], out["n_null"]["G6l"] = _nt["ties"], _nt["n"]
    return out


def check(runs: dict, direct: dict, keys) -> list:
    bad = []
    up, dn = runs[False], runs[True]
    if not abs(up["T"] - direct["T"]) <= 1e-12:
        bad.append(f"T {up['T']} != direct {direct['T']}")
    if up["tail_direction"] != 1 or dn["tail_direction"] != -1:
        bad.append("tails: upper must be +1, a stated depletion -1")
    for leg, want_no in (("S1c", 21), ("S2c", 22), ("G1", 23), ("G3m", 24), ("G6l", 25)):
        if up["legs"][leg].get("seed_leg") != want_no:
            bad.append(f"{leg}: seed leg {up['legs'][leg].get('seed_leg')} != {want_no}")
    for leg in ("S1c", "S2c"):
        if int(up["legs"][leg]["seed"]) != direct[f"{leg}_seed"]:
            bad.append(f"{leg}: integer seed differs from SD.seed_int(leg {21 if leg == 'S1c' else 22})")
    if set(up["legs"]) != {"Level 0", "S1c", "S2c", "G1", "G3m", "G6l"}:
        bad.append(f"legs {sorted(up['legs'])}: T_abs has no G6s")
    for leg, rec in up["legs"].items():
        if rec.get("conditioned") not in (None, False):
            bad.append(f"{leg}: marked conditioned")
        p = rec["p"]
        if rec["p"] != dn["legs"][leg]["p"]:
            bad.append(f"{leg}: the depletion run's p's differ (same keys)")
        if p is None:
            if leg in direct["p"] and leg != "G6l":
                bad.append(f"{leg}: no p")
            continue
        if rec["p_registered_tail"] != p[1] or dn["legs"][leg]["p_registered_tail"] != p[-1]:
            bad.append(f"{leg}: registered-tail p is not the upper (resp. lower) one-sided p")
        if leg not in direct["p"]:
            bad.append(f"{leg}: no direct p")
            continue
        for d in (1, -1):
            a, b = float(p[d]), float(direct["p"][leg][d])
            if leg == "Level 0":
                if not abs(a - b) <= 1e-12:
                    bad.append(f"Level 0 ({d:+d}) {a} != direct {b}")
            elif a != b:
                tol = direct["near_ties"].get(leg, 0) / (direct["n_null"][leg] + 1)
                if not abs(a - b) <= tol + 1e-15:
                    bad.append(f"{leg} ({d:+d}) {a} != direct {b} (near ties {direct['near_ties'].get(leg, 0)})")
    return bad


PLANTS = {"P11": P11()}
