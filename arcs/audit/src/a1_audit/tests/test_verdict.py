"""Value checks of A1's verdict driver (a1_audit.verdict) and descriptor pass (a1_audit.descriptors) on synthetic data
(arcs/audit/RUN_PLAN.md v3.1 §7 rows P8, P9, P10, P14, P23; R1, R4, R5, R7, R8, R9, R24).

(i)   P8 (a) 20 planted negative-signal maps (dk-ctx-like toy): wherever d* = -, the two-sided conjunction p and every
      leg's reported p equal 2 x the one-sided "-" values (exact); survival counts of both. (b) a constructed case in
      which Level 0's minimising direction differs from the species leg's: d* = argmin_d max_leg p(d), reported legs =
      min(1, 2 p(d*)), the literal per-leg 2 min beside them (exact); tie and one-sided rules on stub legs; a planted
      'ok status with a non-finite member' refused. (c) / P14 two-cohort: one d* over both maps (exact), survives iff
      both survive, p = the larger.
(ii)  P9-like: a 7-parcel single-class toy: site leg exact (7! = 5,040), G6s exact (64), status 'resolution-limited'
      with the doubled floor 4/65 recorded; any uninformative flag beside. RUN_PLAN_amend_1 R32: every exact leg
      counts its identity row and no exact p falls below its declared floor (asserted; the full P9 extension battery
      is tests/test_amend1.py).
(iii) P10: pool < m -> R8's labels, no exception.
(iv)  P23: J1 / naive joint draw their own sets and surrogates from legs 14 / 15 in R7's order; T substitution equals
      direct computation (cascade.joint_j1 / naive_joint for set-vs-map; per-gene r by hand for decoded-list; 1e-12);
      degenerate pool -> status.
(v)   R24: Level-2 G1 = species G1 on a single class (asserted; a tampered species G1 is caught); the G3 stream from
      R24's key is reproducible and differs from leg 3's.
Also: component forms (parametric / permutation Level 0), T_abs legs 21-25 (shared G6l screen), and the seed bridge
(verdict.seed_callables) against a1_audit.seeds (key arithmetic only: no claim key touches data here).
asdg-skeptic review of WP1 (61e3887): B1 a strong synthetic plant whose computed verdict survives (set-vs-map,
decoded-list, two-cohort, component) read as a descriptor row (verdict.descriptor_row_record): survives False, the TSV
status, "descriptive (not a verdict)", no 'survives' key left; B4 stub and synthetic-data plants with one dominant
within-class component (y = the basis's leading component): primary status "uninformative", survives False, one- and
two-sided; B5 descriptor legs favouring the direction opposite the claim's d* reported at min(1, 2 p(d*)); B3 the plant
keys of verdict.plant_seed_callables.

Synthetic data only: e3_plants' GAMBA / AHBA paths are pointed at a non-existent scratch path before anything is
imported; contexts are built from toy matrices with a toy brain background; BrainSpan-like trajectories are synthetic.
Seeds: test-local plant-style keys SeedSequence([20260925, 900, plant, case, class, leg]) (target 900 does not exist).

Run (from arcs/audit/src):
  ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_verdict [--scratch DIR]
Exits non-zero on any failure. Prints ASCII only.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
for _p in (ROOT / "src", ROOT / "arcs" / "audit" / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

ap = argparse.ArgumentParser()
ap.add_argument("--scratch", default=None, help="scratch directory (default: a new temporary directory)")
ARGS, _ = ap.parse_known_args()
SCRATCH = Path(ARGS.scratch or tempfile.mkdtemp(prefix="a1_verdict_")).resolve()
SCRATCH.mkdir(parents=True, exist_ok=True)
NO_DATA = SCRATCH / "no_such_data_dir"  # never created: an unpatched data read fails here
assert not NO_DATA.exists()

import e3_plants  # noqa: E402

e3_plants.GAMBA_CSV = NO_DATA / "gamba.csv"
e3_plants.AHBA = NO_DATA

import a1_audit.a3_port as A  # noqa: E402
import a1_audit.adapters as AD  # noqa: E402
import a1_audit.descriptors as DS  # noqa: E402
import a1_audit.seeds as SD  # noqa: E402
import a1_audit.verdict as V  # noqa: E402
from asdg.cascade import emp_p, joint_j1, naive_joint  # noqa: E402
from asdg.genesets import coexpr_matched_sets, random_sets  # noqa: E402
from asdg.spatial import brainsmash_surrogates, site_null  # noqa: E402

A.AHBA = NO_DATA

RESULTS: dict = {}
FAILED: list = []
CHECKS: list = []
LEGNO = dict(SD.LEGS)
LEGNO["permutation"] = 8
KP = {"site": 500, "species": 200}  # plant K (RUN_PLAN §7 cost model)


def plant_keys(plant: int, case: int, cls: int = 0):
    """(seed_of, g3_seed, tabs_seed_of) on test-local plant-style keys."""
    def seed_of(leg):
        return np.random.SeedSequence([20260925, 900, plant, case, cls, LEGNO[leg]])

    def g3_seed():
        return np.random.SeedSequence(entropy=[20260925, 900, plant, case, cls, 3], spawn_key=(0,))

    def tabs_seed_of(leg):
        if leg not in V.TABS_LEGS:
            raise ValueError(leg)
        return seed_of(V.TABS_LEGS[leg])
    return seed_of, g3_seed, tabs_seed_of


def check(name):
    def deco(fn):
        def run():
            t0 = time.time()
            try:
                measured = fn() or {}
                RESULTS[name] = dict(result="pass", seconds=round(time.time() - t0, 2), **measured)
                print(f"PASS {name} ({time.time() - t0:.1f}s) {json.dumps(A.jsonable(measured))[:900]}", flush=True)
            except Exception as e:  # noqa: BLE001
                FAILED.append(name)
                RESULTS[name] = dict(result="FAIL", error=f"{type(e).__name__}: {e}")
                msg = f"{type(e).__name__}: {e}".encode("ascii", "replace").decode("ascii")
                print(f"FAIL {name}: {msg}", flush=True)
                print(traceback.format_exc().encode("ascii", "replace").decode("ascii"), flush=True)
        run.__name__ = fn.__name__
        CHECKS.append(run)
        return run
    return deco


def canon(rec) -> str:
    return json.dumps(A.jsonable(rec), sort_keys=True)


def raises(exc, f, *a, **k) -> str:
    try:
        f(*a, **k)
    except exc as e:  # noqa: BLE001
        return f"{type(e).__name__}: {str(e)[:80]}"
    raise AssertionError(f"{getattr(f, '__name__', f)} did not raise {exc.__name__}")


# ================================================================================================================
# toy inputs
# ================================================================================================================
def toy_inputs(seed=1, sizes=(24, 14, 8), G=300, scale=(0.2, 5.0), module=None, names=None):
    """As tests/test_p0.toy_inputs: parcels in len(sizes) tissue classes, genes = class offsets + 5 smooth factors +
    noise, every gene scaled and shifted by its own factor; a random brain>body subset of 50 genes; module = (m, load):
    genes 0..m-1 share a within-class pattern f."""
    names = names or ("cortex", "subcortex/brainstem", "cerebellum")
    rng = np.random.default_rng(seed)
    cl = np.concatenate([[c] * k for c, k in zip(names, sizes)])
    P = cl.size
    xyz = rng.uniform(-70, 70, (P, 3))
    D = np.sqrt(((xyz[:, None] - xyz[None]) ** 2).sum(-1))
    L = np.linalg.cholesky(np.exp(-(D / 40) ** 2) + 1e-6 * np.eye(P))
    facs = np.column_stack([L @ rng.standard_normal(P) for _ in range(5)])
    off = {c: rng.standard_normal(G) for c in np.unique(cl)}
    X = np.stack([off[c] for c in cl]) + facs @ rng.standard_normal((5, G)) + 0.7 * rng.standard_normal((P, G))
    f = None
    if module is not None:
        m, load = module
        f = rng.standard_normal(P)
        for c in np.unique(cl):
            f[cl == c] -= f[cl == c].mean()
        X[:, :m] += load * np.outer(f, np.ones(m))
    X = X * rng.uniform(*scale, G) + rng.uniform(-3, 3, G)
    ids = np.arange(101, 101 + P)
    genes = [f"g{j}" for j in range(G)]
    expr = pd.DataFrame(X, index=ids, columns=genes)
    info = pd.DataFrame({"label": [f"p{i}" for i in ids], "hemisphere": "L", "structure": cl}, index=ids)
    brain = sorted(genes[i] for i in rng.choice(G, 50, replace=False))
    return dict(expr=expr, classes=cl, xyz=xyz, info=info, brain=brain, f=f, rng=rng)


def ctx_of(inp, name, atlas=None):
    return A.ClassContext(name, inp["expr"].copy(), inp["classes"].copy(), inp["xyz"].copy(), inp["info"].copy(),
                          A.symbols_background(inp["brain"]), atlas)


def field(ctx, rng, length=35.0):
    L = np.linalg.cholesky(np.exp(-(ctx.D / length) ** 2) + 1e-6 * np.eye(ctx.n))
    return L @ rng.standard_normal(ctx.n)


def traj_frame(genes, seed=7):
    """Synthetic BrainSpan-like trajectories: per gene, mean log2(RPKM + 1) over 8 stage bins (smooth curves)."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, 8)
    lvl = rng.normal(5, 1.5, len(genes))[:, None]
    slope = rng.normal(0, 1.5, len(genes))[:, None]
    bump = rng.normal(0, 1.0, len(genes))[:, None] * np.exp(-((t - rng.uniform(0, 1, len(genes))[:, None]) / .25) ** 2)
    vals = lvl + slope * t + bump + 0.1 * rng.standard_normal((len(genes), 8))
    return pd.DataFrame(vals, index=list(genes), columns=[f"bin{k}" for k in range(8)])


z = A.zscore
DK = toy_inputs(11, sizes=(34,), module=(25, 1.5), names=("cortex",))
CDK = ctx_of(DK, "dk-ctx", "dk")
SMOD = np.arange(25)


def direct_conj(legs, d):
    by = V.leg_p_by_direction(legs)
    return A.pmax(*[v[d] for v in by.values()])


# ================================================================================================================
# (i) P8
# ================================================================================================================
@check("P8a_two_sided_eq_2x_one_sided_minus")
def t_p8a():
    n_minus = n_cap = 0
    surv_two = surv_minus = 0
    rows = []
    for i in range(20):
        a = 0.3 + 0.6 * i / 19
        y = -a * z(CDK.score(SMOD)) + math.sqrt(1 - a * a) * z(field(CDK, np.random.default_rng(1000 + i)))
        cls = AD.SetVsMap if i % 2 == 0 else AD.DecodedList
        ad = cls(CDK, y, SMOD, parcel_ids=CDK.parcel_ids)
        seed_of = plant_keys(8, i)[0]
        legs = V.collect_legs(ad, KP, seed_of)
        two = V.assemble_verdict_a1(legs, two_sided=True)
        one_m = V.assemble_verdict_a1(legs, two_sided=False, registered_direction=-1)
        one_p = V.assemble_verdict_a1(legs, two_sided=False, registered_direction=1)
        # R1: the two-sided conjunction p = min(1, 2 min_d max_leg p(d)) always
        assert two["p_conjunction"] == min(1.0, 2.0 * min(one_m["p_conjunction"], one_p["p_conjunction"]))
        cm, cp = direct_conj(legs, -1), direct_conj(legs, 1)
        want_d = -1 if cm < cp else 1 if cp < cm else (1 if legs["T"] >= 0 else -1)
        assert two["d_star"] == want_d, (two["d_star"], want_d)
        if two["d_star"] == -1:
            n_minus += 1
            assert two["p_conjunction"] == min(1.0, 2.0 * one_m["p_conjunction"]), "P8 (a): conjunction"
            n_cap += int(2.0 * one_m["p_conjunction"] > 1.0)
            for leg, rec in two["legs"].items():
                o = one_m["legs"][leg]["p_reported"]
                if o is None:
                    assert rec["p_reported"] is None
                else:
                    assert rec["p_reported"] == min(1.0, 2.0 * o), f"P8 (a): leg {leg}"
                assert rec["p_one_sided"] == one_m["legs"][leg]["p_one_sided"]
                assert rec["floor_effective"] == (None if rec["floor_one_sided"] is None
                                                  else min(1.0, 2.0 * rec["floor_one_sided"]))
        surv_two += int(two["survives"])
        surv_minus += int(one_m["survives"])
        rows.append(dict(a=round(a, 3), form=ad.form, d_star=two["d_star"], p2=two["p_conjunction"],
                         p_minus=one_m["p_conjunction"], status=two["primary_status"]))
        if i < 2:  # an independent full rerun gives the same record (reproducible from the keys)
            again = V.claim_verdict_a1(cls(CDK, y, SMOD, parcel_ids=CDK.parcel_ids), KP, seed_of, two_sided=True)
            assert canon(again) == canon(two), "rerun differs"
    assert n_minus >= 1, "no d* = - case among the negative plants"
    return dict(n_maps=20, n_dstar_minus=n_minus, n_capped=n_cap, survive_two_sided=surv_two,
                survive_one_sided_minus=surv_minus, rows=rows[:4])


class StubFull:
    """A full-verdict adapter stub returning given one-sided p's (assembly checks only)."""
    form = "set-vs-map"
    full_verdict = True
    n = 34

    def __init__(self, T, L0, site, species, floors=None, status=None, unin=False):
        self.T_obs, self._L0, self._site, self._sp, self._unin = T, L0, site, species, unin
        self._floors = floors or {"G1": 1 / 201, "G3m": 1 / 201, "G6s": 1 / 201, "G6l": 1 / 201}
        self._status = status or {k: "ok" for k in AD.SPECIES_LEGS}

    def level0_both(self):
        return dict(self._L0)

    def site_leg(self, K, seed_of, chunk=1000):
        return {k: dict(p=dict(v), floor=1 / 501, seed=1, info=dict(exact=False, n_null=500, n_patterns=float("inf"),
                                                                     floor=1 / 501)) for k, v in self._site.items()}

    def species_leg(self, K, seed_of, g6l=None):
        return dict(p={k: (None if v is None else dict(v)) for k, v in self._sp.items()}, status=dict(self._status),
                    floors=dict(self._floors), g6l_info=dict(status=self._status["G6l"]), g6s_exact=False, n_G6s=200,
                    conditioned=True, pools={})

    def uninformative(self):
        return self._unin, 0.3


def P(pp, pm):
    return {1: pp, -1: pm}


@check("P8b_level0_vs_species_direction")
def t_p8b():
    out = {}
    # (1) synthetic data: every gene loads positively on one shared smooth profile (as AHBA's gene-mean profile);
    # S = 25 genes with a weak loading; y = that profile + noise. T = r(y, s_S) > 0, so Level 0 favours +, while
    # random sets (strong loadings) sit above T, so the species leg favours -.
    rng = np.random.default_rng(31)
    P_, G_ = 34, 300
    xyz = rng.uniform(-70, 70, (P_, 3))
    Dm = np.sqrt(((xyz[:, None] - xyz[None]) ** 2).sum(-1))
    prof = np.linalg.cholesky(np.exp(-(Dm / 40) ** 2) + 1e-6 * np.eye(P_)) @ rng.standard_normal(P_)
    prof = z(prof)
    w = rng.uniform(0.6, 1.4, G_)
    S = np.arange(40, 65)
    w[S] = 0.15
    X = np.outer(prof, w) + rng.standard_normal((P_, G_))
    X[:, S] += 0.9 * np.outer(z(rng.standard_normal(P_)), np.ones(S.size))  # S coherent (G6l windows can match it)
    ids = np.arange(101, 101 + P_)
    genes = [f"g{j}" for j in range(G_)]
    inp = dict(expr=pd.DataFrame(X, index=ids, columns=genes), classes=np.array(["cortex"] * P_), xyz=xyz,
               info=pd.DataFrame({"label": [f"p{i}" for i in ids], "hemisphere": "L", "structure": "cortex"},
                                 index=ids),
               brain=sorted(genes[i] for i in rng.choice(G_, 50, replace=False)))
    c = ctx_of(inp, "dk-ctx", "dk")
    y = prof + 0.3 * rng.standard_normal(P_)
    ad = AD.SetVsMap(c, y, S, parcel_ids=c.parcel_ids)
    legs = V.collect_legs(ad, {"site": 300, "species": 200}, plant_keys(8, 100)[0])
    by = V.leg_p_by_direction(legs)
    l0_min = min((1, -1), key=lambda d: by["Level 0"][d])
    sp_min = min((1, -1), key=lambda d: by["species"][d])
    assert all(math.isfinite(by["species"][d]) for d in (1, -1)), ("precondition: species p", legs["species"]["status"])
    assert ad.T_obs > 0 and l0_min == 1 and sp_min == -1, ("precondition", ad.T_obs, l0_min, sp_min)
    found = (None, S, ad, legs, l0_min, sp_min)
    lo, S, ad, legs, l0_min, sp_min = found
    rec = V.assemble_verdict_a1(legs, two_sided=True)
    cm, cp = direct_conj(legs, -1), direct_conj(legs, 1)
    d = -1 if cm < cp else 1 if cp < cm else (1 if legs["T"] >= 0 else -1)
    assert rec["d_star"] == d
    for leg, lr in rec["legs"].items():
        p = lr["p_one_sided"]
        if p is None:
            continue
        assert lr["p_reported"] == min(1.0, 2.0 * p[d]), leg
        assert lr["p_per_leg_two_sided"] == min(1.0, 2.0 * min(p[1], p[-1])), leg
    assert rec["p_conjunction"] == min(1.0, 2.0 * min(cm, cp))
    assert rec["labels"]["p_per_leg_two_sided"] == "per-leg two-sided (not the verdict p)"
    out["data_case"] = dict(T=legs["T"], level0_argmin=l0_min, species_argmin=sp_min, d_star=rec["d_star"],
                            conj={1: cp, -1: cm}, p_conjunction=rec["p_conjunction"],
                            reported={k: v["p_reported"] for k, v in rec["legs"].items()},
                            per_leg_two_sided={k: v.get("p_per_leg_two_sided") for k, v in rec["legs"].items()})
    # (2) stub legs with exact values: Level 0 + strongly, species - ; d* = + (max .02 vs .99)
    st = StubFull(0.4, P(1e-4, 0.9999), {"S1c": P(0.004, 0.996), "S2c": P(0.002, 0.998)},
                  {"G1": P(0.02, 0.985), "G3m": P(0.01, 0.99), "G6s": P(0.015, 0.99), "G6l": P(0.012, 0.991)})
    rs = V.claim_verdict_a1(st, 500, None, two_sided=True)
    assert rs["d_star"] == 1 and rs["p_conjunction"] == 0.04 and rs["survives"] is False
    assert rs["legs"]["G1"]["p_reported"] == 0.04 and rs["legs"]["Level 0"]["p_reported"] == 2e-4
    assert rs["legs"]["G1"]["p_per_leg_two_sided"] == 0.04
    st2 = StubFull(0.4, P(1e-4, 0.9999), {"S1c": P(0.004, 0.996), "S2c": P(0.002, 0.998)},
                   {"G1": P(0.995, 0.006), "G3m": P(0.99, 0.01), "G6s": P(0.97, 0.03), "G6l": P(0.99, 0.01)})
    r2 = V.claim_verdict_a1(st2, 500, None, two_sided=True)
    # + : max(.0001, .004, .995) = .995; - : max(.9999, .998, .03) = .9999 -> d* = +; literal per-leg 2 min beside
    assert r2["d_star"] == 1 and r2["p_conjunction"] == 1.0
    assert r2["legs"]["G1"]["p_reported"] == 1.0 and r2["legs"]["G1"]["p_per_leg_two_sided"] == 0.012
    assert r2["legs"]["Level 0"]["p_per_leg_two_sided"] == 2e-4
    # ties -> sign of T (+ if T = 0)
    tie = dict(L0=P(0.5, 0.5), site={"S1c": P(0.5, 0.5), "S2c": P(0.5, 0.5)},
               species={k: P(0.5, 0.5) for k in AD.SPECIES_LEGS})
    for T, want in ((-0.2, -1), (0.0, 1), (0.3, 1)):
        rt = V.claim_verdict_a1(StubFull(T, tie["L0"], tie["site"], tie["species"]), 500, None, two_sided=True)
        assert rt["d_star"] == want and rt["d_star_rule"].startswith("tie"), (T, rt["d_star"])
    # one-sided: the registered direction, undoubled, whatever the legs favour
    r1 = V.claim_verdict_a1(st, 500, None, two_sided=False, registered_direction=-1)
    assert r1["d_star"] == -1 and r1["p_conjunction"] == 0.9999 and "p_per_leg_two_sided" not in r1["legs"]["G1"]
    raises(ValueError, V.claim_verdict_a1, st, 500, None, two_sided=True, registered_direction=1)
    raises(ValueError, V.claim_verdict_a1, st, 500, None, two_sided=False)
    # planted defect: an ok status with a non-finite member is refused (never read as a p)
    bad = V.collect_legs(st, 500, None)
    bad["species"]["p"]["G3m"] = None  # status still "ok": the legs record lies
    out["refusal_two_sided"] = raises(RuntimeError, V.assemble_verdict_a1, bad, two_sided=True)
    out["refusal_one_sided"] = raises(RuntimeError, V.assemble_verdict_a1, bad, two_sided=False,
                                      registered_direction=1)
    assert "non-finite member" in out["refusal_one_sided"]
    out["stub_d_star"] = [rs["d_star"], r2["d_star"]]
    return out


@check("P8c_P14_two_cohort")
def t_p8c():
    s = CDK.score(SMOD)
    ya = 0.9 * z(s) + math.sqrt(1 - 0.81) * z(field(CDK, np.random.default_rng(201)))
    yb = -0.3 * z(s) + math.sqrt(1 - 0.09) * z(field(CDK, np.random.default_rng(202)))
    yc = 0.9 * z(s) + math.sqrt(1 - 0.81) * z(field(CDK, np.random.default_rng(203)))
    keys = {k: plant_keys(14, 0, k)[0] for k in (0, 1)}
    la = V.collect_legs(AD.SetVsMap(CDK, ya, SMOD, parcel_ids=CDK.parcel_ids), KP, keys[0])
    lb = V.collect_legs(AD.SetVsMap(CDK, yb, SMOD, parcel_ids=CDK.parcel_ids), KP, keys[1])
    lc = V.collect_legs(AD.SetVsMap(CDK, yc, SMOD, parcel_ids=CDK.parcel_ids), KP, keys[1])
    ra, rb = V.assemble_verdict_a1(la, two_sided=True), V.assemble_verdict_a1(lb, two_sided=True)
    assert ra["d_star"] == 1 and rb["d_star"] == -1, ("precondition: the maps alone choose opposite d*",
                                                      ra["d_star"], rb["d_star"])
    tc = V.two_cohort_from_legs(la, lb, two_sided=True, map_labels=("ABIDE I", "ABIDE II"))
    conj = {d: max(direct_conj(la, d), direct_conj(lb, d)) for d in (1, -1)}
    want = 1 if conj[1] < conj[-1] else -1 if conj[-1] < conj[1] else None
    assert want is not None and tc["d_star"] == want, (tc["d_star"], conj)
    for lab, legs in (("ABIDE I", la), ("ABIDE II", lb)):
        rec = tc["per_map"][lab]
        assert rec["d_star"] == want
        for leg, lr in rec["legs"].items():
            p = lr["p_one_sided"]
            if p is not None:
                assert lr["p_reported"] == min(1.0, 2.0 * p[want]), (lab, leg)
        assert rec["p_conjunction"] == min(1.0, 2.0 * direct_conj(legs, want))
    pa, pb = tc["per_map"]["ABIDE I"]["p_conjunction"], tc["per_map"]["ABIDE II"]["p_conjunction"]
    assert tc["p_conjunction"] == max(pa, pb)
    assert tc["survives"] == (tc["per_map"]["ABIDE I"]["survives"] and tc["per_map"]["ABIDE II"]["survives"])
    assert tc["survives"] is False
    # both maps strong: both survive -> the claim survives, p = the larger
    t2 = V.two_cohort_from_legs(la, lc, two_sided=True)
    s2 = [t2["per_map"][k]["survives"] for k in t2["map_labels"]]
    assert t2["survives"] == all(s2) and t2["p_conjunction"] == max(t2["per_map"][k]["p_conjunction"]
                                                                     for k in t2["map_labels"])
    # one-sided two-cohort (registered +): d* = +, no doubling
    t1 = V.two_cohort_from_legs(la, lc, two_sided=False, registered_direction=1)
    assert t1["d_star"] == 1 and t1["p_conjunction"] == max(direct_conj(la, 1), direct_conj(lc, 1))
    # end to end from the adapters on the maps' own keys = from the legs
    e2e = V.two_cohort_verdict(AD.SetVsMap(CDK, ya, SMOD, parcel_ids=CDK.parcel_ids),
                               AD.SetVsMap(CDK, yb, SMOD, parcel_ids=CDK.parcel_ids), KP, keys[0], keys[1],
                               two_sided=True, map_labels=("ABIDE I", "ABIDE II"))
    assert canon(e2e) == canon(tc)
    # a tie between directions with opposite T signs: RUN_PLAN_amend_1 R36 (b) -> does not survive, p = 1, d* undefined
    tie = dict(L0=P(0.5, 0.5), site={"S1c": P(0.5, 0.5), "S2c": P(0.5, 0.5)},
               species={k: P(0.5, 0.5) for k in AD.SPECIES_LEGS})
    lt1 = V.collect_legs(StubFull(0.2, tie["L0"], tie["site"], tie["species"]), 500, None)
    lt2 = V.collect_legs(StubFull(-0.2, tie["L0"], tie["site"], tie["species"]), 500, None)
    tt = V.two_cohort_from_legs(lt1, lt2, two_sided=True)
    assert tt["d_star"] is None and tt["d_star_reason"] == V.TWO_COHORT_TIE and tt["survives"] is False
    assert tt["p_conjunction"] == 1.0 and tt["reading"] == V.TWO_COHORT_TIE_READING
    assert tt["primary_status"] == "ok" and not tt["primary_status"].startswith("not auditable")
    return dict(d_star_alone=[ra["d_star"], rb["d_star"]], d_star_joint=tc["d_star"], conj_joint=conj,
                p_maps=[pa, pb], p=tc["p_conjunction"], survives=tc["survives"], both_strong_survive=s2,
                both_strong_claim=t2["survives"], tie_status=tt["primary_status"])


# ================================================================================================================
# (ii) P9-like resolution
# ================================================================================================================
@check("P9_resolution_7_parcels")
def t_p9():
    inp = toy_inputs(41, sizes=(7,), names=("subcortex/brainstem",))
    c = ctx_of(inp, "V-DK-subcortex", "dk")
    y = field(c, np.random.default_rng(42)) + 0.3 * np.random.default_rng(43).standard_normal(c.n)
    out, below = {}, []
    for cls in (AD.SetVsMap, AD.DecodedList):
        ad = cls(c, y, np.arange(25), parcel_ids=c.parcel_ids)
        legs = V.collect_legs(ad, {"site": 10000, "species": 200}, plant_keys(9, 0)[0])
        for leg in ("S1c", "S2c"):
            info = legs["site"][leg]["info"]
            assert info["exact"] is True and info["n_null"] == 5040 and info["n_patterns"] == 5040.0, (leg, info)
            assert legs["site"][leg]["floor"] == 2 / 5041
        sp = legs["species"]
        assert sp["g6s_exact"] is True and sp["n_G6s"] == 64 and sp["floors"]["G6s"] == 2 / 65, sp["n_G6s"]
        lab = V.assemble_verdict_a1(legs, two_sided=True, by_construction_label="resolution-limited")
        raw = V.assemble_verdict_a1(legs, two_sided=True)
        assert lab["legs"]["G6s"]["floor_effective"] == 4 / 65
        assert lab["legs"]["species"]["floor_effective"] == 4 / 65
        assert lab["resolution"]["limited"] is True and lab["resolution"]["max_floor"] == 4 / 65
        assert lab["resolution"]["binding"] == ["species"]
        assert lab["primary_status"] == "resolution-limited" and "resolution-limited" in lab["flags"]
        assert lab["survives"] is False and raw["survives"] is False
        if sp["status"]["G6l"] == "ok" and not legs["uninformative"]["flag"]:
            assert raw["primary_status"] == "resolution-limited"
        # one-sided floors are not doubled
        one = V.assemble_verdict_a1(legs, two_sided=False, registered_direction=1)
        assert one["resolution"]["max_floor"] == 2 / 65 and one["resolution"]["limited"] is True
        # RUN_PLAN_amend_1 R32: the identity is counted, so no exact leg's p falls below its declared floor (the
        # driver's R32 (c) assertion would have stopped the run; asserted below as well)
        for leg in ("S1c", "S2c"):
            assert legs["site"][leg]["info"]["identity"]["rows_counted_as_identity"] >= 1
        assert sp["g6s_identity"]["rows_counted_as_identity"] >= 1
        for leg, fl in (("S1c", 2 / 5041), ("S2c", 2 / 5041)):
            for d in (1, -1):
                pv = legs["site"][leg]["p"][d]
                if pv < fl:
                    below.append(dict(form=ad.form, leg=leg, d=d, p=pv, floor=fl))
        for d in (1, -1):
            pv = sp["p"]["G6s"][d]
            if pv < 2 / 65:
                below.append(dict(form=ad.form, leg="G6s", d=d, p=pv, floor=2 / 65))
        out[ad.form] = dict(primary_with_label=lab["primary_status"], computed_status=raw["primary_status"],
                            flags=lab["flags"], doubled_floor=lab["resolution"]["max_floor"],
                            g6l=sp["status"]["G6l"], g6l_n_used=sp["g6l"].get("n_used"),
                            uninformative=legs["uninformative"], p_conjunction=raw["p_conjunction"])
    out["exact_p_below_declared_floor"] = below
    assert below == [], below  # RUN_PLAN_amend_1 R32 (a) / (c)
    return out


# ================================================================================================================
# (iii) P10 pool < m
# ================================================================================================================
@check("P10_pool_smaller_than_S")
def t_p10():
    out = {}
    tiny_k = {"site": 50, "species": 50}
    va = toy_inputs(51)
    contexts = {"V-AAL": ctx_of(va, "V-AAL", "aal"), "dk-ctx": ctx_of(toy_inputs(52, sizes=(34,), names=("cortex",)),
                                                                      "dk-ctx", "dk")}
    for cname, c in contexts.items():
        traj = traj_frame(c.U.genes, seed=53)
        y = field(c, np.random.default_rng(54))
        brain = np.flatnonzero(c.B.brain)
        nonb = np.flatnonzero(~c.B.brain)
        cases = {"m>|U\\S|": np.arange(160), "f>|B\\S|": np.concatenate([brain, nonb[:10]])}
        for case, S in cases.items():
            st = AD.pool_status(c.B, S)
            for cls in (AD.SetVsMap, AD.DecodedList):
                ad = cls(c, y, S, parcel_ids=c.parcel_ids)
                sk = plant_keys(10, len(out), 0)
                rec = V.claim_verdict_a1(ad, tiny_k, sk[0], two_sided=True)
                desc = DS.descriptor_pass(ad, sk[0], sk[1], K_sets=50, K_surr=50, K_j1_sets=30, traj=traj,
                                          direction=rec["d_star"], two_sided=True)
                L = rec["legs"]
                assert rec["primary_status"] == V.R8_NOT_AUDITABLE and rec["survives"] is False
                assert L["G6s"]["status"] == "ok" and L["G6s"]["p_one_sided"] is not None
                assert L["Level 0"]["p_one_sided"] is not None and L["site"]["p_one_sided"] is not None
                g = desc["legs"]
                if case == "m>|U\\S|":
                    assert not st["G1"] and not st["G3m"] and st["G6l"] == "no window", st
                    assert L["G1"]["status"] == AD.NOT_COMPUTABLE and L["G3m"]["status"] == AD.NOT_COMPUTABLE
                    assert L["G6l"]["status"] == "unmatched" and "g6l unmatched" in rec["flags"]
                    assert g["Level-2 G1"]["status"] == AD.NOT_COMPUTABLE
                    assert g["G2"]["status"] == "unmatched"
                    assert desc["J1"]["status"] == AD.NOT_COMPUTABLE
                    assert desc["naive_joint"]["status"] == AD.NOT_COMPUTABLE
                    assert g["G5"]["status"] == "not applicable"
                else:
                    assert st["G1"] and not st["G3m"], st
                    assert L["G1"]["status"] == "ok" and L["G1"]["p_one_sided"] is not None
                    assert L["G3m"]["status"] == AD.NOT_COMPUTABLE
                    assert g["Level-2 G1"]["status"] == "ok"
                assert g["G3"]["status"] == AD.NOT_COMPUTABLE and g["G4"]["status"] == "unmatched"
                assert desc["level2"]["p"] is None
                assert rec["d_star"] is None and L["G6s"]["p_reported"] is None
                assert L["G6s"]["p_per_leg_two_sided"] is not None
                out[f"{cname} {case} {ad.form}"] = dict(
                    primary=rec["primary_status"], flags=rec["flags"],
                    verdict_legs={k: L[k]["status"] for k in ("G1", "G3m", "G6s", "G6l")},
                    descriptor={k: v["status"] for k, v in g.items()}, J1=desc["J1"]["status"],
                    naive_joint=desc["naive_joint"]["status"], level2=desc["level2"]["status"][:70])
    # G5 pool < 2m with every other leg drawable: trajectories for S's 25 members + 20 other genes only
    c = contexts["dk-ctx"]
    y = field(c, np.random.default_rng(55))
    S = np.arange(100, 125)
    ad = AD.DecodedList(c, y, S, parcel_ids=c.parcel_ids)
    small = traj_frame([c.U.genes[i] for i in list(S) + list(range(200, 220))], seed=56)
    g5 = DS.g5_leg(ad, 50, plant_keys(10, 90)[0], small)
    assert g5["status"] == "not applicable" and g5["p"] is None, g5
    # > 20 % of members without a trajectory -> not applicable
    part = traj_frame([c.U.genes[i] for i in list(S[:15]) + list(range(126, 299))], seed=57)
    g5b = DS.g5_leg(ad, 50, plant_keys(10, 91)[0], part)
    assert g5b["status"] == "not applicable" and g5b["info"]["n_fixed"] == 10, g5b
    full = DS.g5_leg(ad, 50, plant_keys(10, 92)[0], traj_frame(c.U.genes, seed=58))
    out["G5_small_pool"] = dict(status=g5["status"], pool=g5["info"].get("pool_size"))
    out["G5_missing_trajectories"] = dict(status=g5b["status"], n_fixed=g5b["info"]["n_fixed"])
    out["G5_full"] = dict(status=full["status"], pool=full["info"].get("pool_size"))
    return out


# ================================================================================================================
# (iv) P23 J1 / naive joint
# ================================================================================================================
def gene_r(maps, X):
    """Per-gene Pearson r of every map row with every column of X (direct formula)."""
    maps = np.atleast_2d(maps)
    Ym = maps - maps.mean(1, keepdims=True)
    Xm = X - X.mean(0)
    return (Ym @ Xm) / np.outer(np.linalg.norm(Ym, axis=1), np.linalg.norm(Xm, axis=0))


@check("P23_J1_naive_joint")
def t_p23():
    out = {}
    SMOD = np.arange(100, 125)  # an unstructured set: its coexpression band is reachable by the G2 sampler
    s = CDK.score(SMOD)
    y = 0.5 * z(s) + math.sqrt(0.75) * z(field(CDK, np.random.default_rng(301)))
    seed_of = plant_keys(23, 0)[0]
    m, G = SMOD.size, CDK.G
    # ---- J1, set-vs-map: own draws (leg 14, R7 order) and T substitution = cascade.joint_j1 ----
    sv = AD.SetVsMap(CDK, y, SMOD, parcel_ids=CDK.parcel_ids)
    rec = DS.j1_leg(sv, seed_of, K_sets=100, K_surr=100, return_draws=True)
    g = np.random.default_rng(seed_of("J1"))
    s1, s2 = int(g.integers(2 ** 31)), int(g.integers(2 ** 31))
    assert rec["seeds"] == dict(S1c=s1, S2c=s2)
    sets_ref, _ = coexpr_matched_sets(CDK.U, np.arange(G), m, CDK.U.mean_coexpr(SMOD), 100, g, exclude=SMOD)
    assert np.array_equal(rec["_draws"]["sets"], sets_ref), "J1 sets are not leg 14's after the two seeds"
    assert rec["status"] == "ok", rec.get("reason")
    worst = 0.0
    for name, method, sd in (("S1c", "brainsmash", s1), ("S2c", "msr", s2)):
        sur, _ = site_null(y, CDK.D, CDK.classes, 100, sd, method)
        assert np.array_equal(sur, rec["_draws"]["surrogates"][name])
        z_obs, p_ref, z_null = joint_j1(y, s, CDK.U.scores(sets_ref), sur, 1)
        worst = max(worst, abs(rec["z_obs"] - z_obs))
        assert abs(rec["z_obs"] - z_obs) <= 1e-12
        assert abs(rec["types"][name]["p"][1] - p_ref) <= 1e-12, (name, rec["types"][name]["p"][1], p_ref)
        assert abs(rec["types"][name]["p"][-1] - emp_p(z_null, z_obs, -1)) <= 1e-12
    assert rec["p"] == {d: max(rec["types"]["S1c"]["p"][d], rec["types"]["S2c"]["p"][d]) for d in (1, -1)}
    out["J1_setvsmap"] = dict(z_obs=rec["z_obs"], p=rec["p"], jaccard=rec["pool_jaccard"], max_abs_z=worst)
    # leg separation: J1's seeds / sets are not the site leg's or G2's (leg 11)
    site_seeds = [int(np.random.default_rng(seed_of(k)).integers(2 ** 31)) for k in ("S1c", "S2c")]
    assert {s1, s2}.isdisjoint(site_seeds)
    g2 = DS.g2_leg(sv, 100, seed_of)
    g2sets, _ = coexpr_matched_sets(CDK.U, np.arange(G), m, CDK.U.mean_coexpr(SMOD), 100,
                                    np.random.default_rng(seed_of("G2")), exclude=SMOD)
    assert not np.array_equal(g2sets, sets_ref) and g2["status"] == "ok"
    # ---- J1, decoded-list: T substitution = direct per-gene r ----
    dl = AD.DecodedList(CDK, y, SMOD, parcel_ids=CDK.parcel_ids)
    rd = DS.j1_leg(dl, seed_of, K_sets=100, K_surr=100, return_draws=True)
    assert np.array_equal(rd["_draws"]["sets"], sets_ref)  # the same leg-14 draws (the sampler is y-free)
    R0 = gene_r(y, CDK.X)[0]
    T_sets_y = R0[sets_ref].mean(1)
    z_obs = (R0[SMOD].mean() - T_sets_y.mean()) / T_sets_y.std(ddof=1)
    assert abs(rd["z_obs"] - z_obs) <= 1e-12
    dd = 0.0
    for name in ("S1c", "S2c"):
        Rs = gene_r(rd["_draws"]["surrogates"][name], CDK.X)
        TS = Rs[:, SMOD].mean(1)
        TM = np.stack([Rs[:, R].mean(1) for R in sets_ref], axis=1)
        zn = (TS - TM.mean(1)) / TM.std(1, ddof=1)
        for d in (1, -1):
            dd = max(dd, abs(rd["types"][name]["p"][d] - emp_p(zn, z_obs, d)))
    assert dd <= 1e-12
    out["J1_decoded"] = dict(z_obs=rd["z_obs"], p=rd["p"], max_abs_p_vs_direct=dd)
    # ---- naive joint: own draws (leg 15, R7 order), cascade.naive_joint semantics ----
    rn = DS.naive_joint_leg(sv, seed_of, K=120, return_draws=True)
    g = np.random.default_rng(seed_of("naive joint"))
    s1n = int(g.integers(2 ** 31))
    assert rn["seeds"] == dict(S1=s1n)
    sets_n = random_sets(np.arange(G), m, 120, g, exclude=SMOD)
    assert np.array_equal(rn["_draws"]["sets"], sets_n)
    sur_n = brainsmash_surrogates(y, CDK.D, 120, s1n)
    assert np.array_equal(rn["_draws"]["surrogates"], sur_n)
    p_ref = naive_joint(y, CDK.U.scores(sets_n), sur_n, s, 1, g)
    assert abs(rn["p"][1] - p_ref) <= 1e-12, (rn["p"][1], p_ref)
    rnd = DS.naive_joint_leg(dl, seed_of, K=120, return_draws=True)
    j = rnd["_draws"]["pairing"]
    Rp = gene_r(sur_n, CDK.X)
    null = np.array([Rp[i, sets_n[j[i]]].mean() for i in range(120)])
    dn = max(abs(rnd["p"][d] - emp_p(null, dl.T_obs, d)) for d in (1, -1))
    assert dn <= 1e-12
    out["naive_joint"] = dict(p_setvsmap=rn["p"], p_ref=p_ref, p_decoded=rnd["p"], max_abs_p_vs_direct=dn)
    # ---- degenerate pool -> status ----
    same_sets = np.tile(np.arange(200, 225), (20, 1))
    sur_small = {"S1c": rec["_draws"]["surrogates"]["S1c"][:20], "S2c": rec["_draws"]["surrogates"]["S2c"][:20]}
    d1 = DS.j1_core(sv, same_sets, sur_small)
    assert d1["status"] == DS.DEGENERATE and d1["p"] is None and "Jaccard" in d1["reason"] and "sd_k" in d1["reason"]
    rng = np.random.default_rng(302)
    overlap = np.stack([np.sort(rng.choice(np.arange(100, 130), 25, replace=False)) for _ in range(20)])
    d2 = DS.j1_core(sv, overlap, sur_small)
    assert d2["status"] == DS.DEGENERATE and d2["pool_jaccard"] >= 0.5 and "sd_k" not in d2["reason"]
    healthy = np.stack([rng.choice(np.arange(25, 300), 25, replace=False) for _ in range(20)])
    d3 = DS.j1_core(sv, healthy, sur_small)
    assert d3["status"] == "ok" and d3["pool_jaccard"] < 0.5
    # the exact Jaccard = brute force
    bf = np.mean([len(set(a) & set(b)) / len(set(a) | set(b)) for i, a in enumerate(overlap) for b in overlap[i + 1:]])
    assert abs(d2["pool_jaccard"] - bf) <= 1e-12
    out["degenerate"] = dict(identical=d1["reason"], overlapping=d2["reason"], jaccard_overlap=d2["pool_jaccard"],
                             jaccard_healthy=d3["pool_jaccard"])
    return out


@check("descriptor_pass_end_to_end")
def t_desc_pass():
    c = ctx_of(toy_inputs(91, sizes=(34,), names=("cortex",)), "dk-ctx", "dk")
    S = np.arange(150, 175)
    y = 0.6 * z(c.score(S)) + 0.8 * z(field(c, np.random.default_rng(92)))
    seed_of, g3_seed, _ = plant_keys(6, 0)
    out = {}
    for cls in (AD.SetVsMap, AD.DecodedList, AD.PlsEnrichment):
        ad = cls(c, y, S, parcel_ids=c.parcel_ids)
        legs = V.collect_legs(ad, {"site": 100, "species": 100}, seed_of, keep_species_raw=True)
        ver = V.assemble_verdict_a1(legs, two_sided=True)
        d = ver["d_star"]
        ds = DS.descriptor_pass(ad, seed_of, g3_seed, K_sets=100, K_surr=100, K_j1_sets=60,
                                traj=traj_frame(c.U.genes, seed=93), species=legs["_species_raw"], direction=d,
                                two_sided=True)
        st = {k: v["status"] for k, v in ds["legs"].items()}
        for k, v in ds["legs"].items():
            assert v["conditioned"] is False
            if v["p"] is not None:
                assert v["p_reported"] == min(1.0, 2.0 * v["p"][d]) and v["p_per_leg_two_sided"] == min(
                    1.0, 2.0 * min(v["p"][1], v["p"][-1])), k
        assert st["Level-2 G1"] == "ok" and st["G3"] == "ok", st
        if all(s_ == "ok" for s_ in st.values()):
            assert ds["level2"]["p"] == {e: max(ds["legs"][k]["p"][e] for k in DS.LEVEL2_LEGS) for e in (1, -1)}
        else:
            assert ds["level2"]["p"] is None
        assert ds["J1"]["status"] in ("ok", "unmatched", DS.DEGENERATE)
        assert ds["naive_joint"]["status"] == "ok"
        # one-sided: the registered direction, undoubled
        d1 = DS.descriptor_pass(ad, seed_of, g3_seed, K_sets=100, K_surr=100, K_j1_sets=60,
                                traj=traj_frame(c.U.genes, seed=93), direction=1, two_sided=False)
        assert d1["legs"]["G3"]["p_reported"] == d1["legs"]["G3"]["p"][1]
        assert "p_per_leg_two_sided" not in d1["legs"]["G3"]
        assert d1["legs"]["G3"]["p"] == ds["legs"]["G3"]["p"]  # same keys -> same draws
        out[ad.form] = dict(d_star=d, statuses=st, level2=ds["level2"]["p"], J1=ds["J1"]["status"],
                            J1_p=ds["J1"].get("p"), naive_joint=ds["naive_joint"]["p"])
    return out


# ================================================================================================================
# (v) R24: Level-2 G1 and G3
# ================================================================================================================
@check("R24_level2_G1_and_G3_stream")
def t_r24():
    out = {}
    inp = toy_inputs(61, sizes=(34,), names=("cortex",))
    c = ctx_of(inp, "dk-ctx", "dk")
    y = field(c, np.random.default_rng(62))
    S = np.arange(5, 30)
    seed_of, g3_seed, _ = plant_keys(24, 0)
    for cls in (AD.SetVsMap, AD.DecodedList, AD.PlsEnrichment):
        ad = cls(c, y, S, parcel_ids=c.parcel_ids)
        legs = V.collect_legs(ad, {"site": 50, "species": 200}, seed_of, keep_species_raw=True)
        l2 = DS.level2_g1_leg(ad, 200, seed_of, species=legs["_species_raw"])
        l2b = DS.level2_g1_leg(ad, 200, seed_of)  # the species G1 recomputed on the same stream
        assert l2["p"] == l2b["p"] and l2["single_class_equals_species_G1_max_abs"] <= 1e-12
        out[f"p_equal_{ad.form}"] = l2["p"] == legs["species"]["p"]["G1"]  # values equal to 1e-12 (asserted)
        tam = dict(legs["_species_raw"])
        tam["null"] = dict(tam["null"])
        tam["null"]["G1"] = tam["null"]["G1"] + 1e-6  # planted: a species G1 that is not this leg's
        out[f"tampered_{ad.form}"] = raises(AssertionError, DS.level2_g1_leg, ad, 200, seed_of, species=tam)
        out[f"max_abs_{ad.form}"] = l2["single_class_equals_species_G1_max_abs"]
    # multi-class: Level-2 G1 (unconditioned) differs from the conditioned species G1, and nothing is asserted
    cm = ctx_of(toy_inputs(63), "V-AAL", "aal")
    ym = field(cm, np.random.default_rng(64))
    adm = AD.DecodedList(cm, ym, S, parcel_ids=cm.parcel_ids)
    spm = adm.species_leg(200, seed_of)
    l2m = DS.level2_g1_leg(adm, 200, seed_of, species=spm)
    l2null = AD.level2_g1(adm, 200, seed_of)["null"]
    diff = float(np.max(np.abs(l2null - spm["null"]["G1"])))
    assert diff > 1e-6 and "single_class_equals_species_G1_max_abs" not in l2m
    out["multi_class_level2_vs_species_G1_max_abs"] = diff
    # G3: R24's stream, reproducible, and not leg 3's
    ad = AD.SetVsMap(c, y, S, parcel_ids=c.parcel_ids)
    a1, a2 = DS.g3_leg(ad, 200, g3_seed), DS.g3_leg(ad, 200, g3_seed)
    assert a1 == a2 and a1["status"] == "ok"
    pool = np.setdiff1d(np.flatnonzero(c.B.brain), S)
    g3sets = np.concatenate(list(DS.uniform_set_chunks(pool, S.size, 200, np.random.default_rng(g3_seed()))))
    l3sets = np.concatenate(list(DS.uniform_set_chunks(pool, S.size, 200, np.random.default_rng(seed_of("G3m")))))
    assert not np.array_equal(g3sets, l3sets)
    assert np.array_equal(g3sets, random_sets(np.flatnonzero(c.B.brain), S.size, 200,
                                              np.random.default_rng(g3_seed()), exclude=S))
    direct = np.array([np.corrcoef(y, c.X[:, R].mean(1))[0, 1] for R in g3sets])
    assert a1["p"] == AD.p_both(direct, ad.T_obs) or max(abs(a1["p"][d] - AD.p_both(direct, ad.T_obs)[d])
                                                         for d in (1, -1)) <= 1e-12
    # the bridge's G3 key is R24's: the first spawned child of leg 3's claim key, not leg 3's key
    br = V.seed_callables(3, 92, 0, 0)
    k3, kg = br["seed_of"]("G3m"), br["g3_seed"]()
    assert SD.same_seed_sequence(kg, np.random.SeedSequence(list(k3.entropy)).spawn(1)[0])
    assert not np.array_equal(kg.generate_state(4), k3.generate_state(4))
    out["G3"] = dict(p=a1["p"], pool=a1["pool"], reproducible=True, differs_from_leg3=True)
    return out


# ================================================================================================================
# components, T_abs, seed bridge
# ================================================================================================================
@check("component_forms_driver")
def t_components():
    cm = ctx_of(toy_inputs(71), "V-AAL", "aal")
    rng = np.random.default_rng(72)
    comp = field(cm, rng)
    y = 0.6 * z(comp) + 0.8 * z(field(cm, rng))
    seed_of = plant_keys(12, 0)[0]
    out = {}
    fc = AD.FixedComponent(cm, y, comp, parcel_ids=cm.parcel_ids)
    r = V.claim_verdict_a1(fc, 200, seed_of, two_sided=True)
    legs = V.collect_legs(fc, 200, seed_of)
    cp, cm_ = direct_conj(legs, 1), direct_conj(legs, -1)
    assert r["d_star"] == (1 if cp < cm_ else -1 if cm_ < cp else (1 if fc.T_obs >= 0 else -1))
    assert r["p_component"] == min(1.0, 2.0 * min(cp, cm_)) and r["survives"] is False
    assert r["label"] == V.COMPONENT_LABEL and "component-level" in r["flags"]
    assert r["reading"] == V.component_reading(r["passes_component_level"])
    assert r["legs"]["Level 0"]["kind"] == "parametric" and r["legs"]["Level 0"]["floor_one_sided"] is None
    out["fixed"] = dict(T=fc.T_obs, d_star=r["d_star"], p=r["p_component"], reading=r["reading"])
    p1 = AD.Pls1R2(cm, y, parcel_ids=cm.parcel_ids)
    r1 = V.claim_verdict_a1(p1, {"site": 100, "permutation": 100}, seed_of, two_sided=False, registered_direction=1)
    lp = p1.level0_perm(100, seed_of)
    assert r1["legs"]["Level 0"]["p_one_sided"] == lp["p"] and r1["legs"]["Level 0"]["floor_one_sided"] == 1 / 101
    assert r1["p_component"] == max(lp["p"][1], r1["legs"]["site"]["p_one_sided"][1]) and r1["survives"] is False
    out["pls1_r2"] = dict(T=p1.T_obs, p=r1["p_component"], reading=r1["reading"])
    out["tabs_refused"] = raises(TypeError, V.claim_verdict_a1, AD.TAbs(cm, y, np.arange(25), parcel_ids=cm.parcel_ids),
                                 100, seed_of, two_sided=True)
    return out


@check("T_abs_legs_21_25_shared_g6l")
def t_tabs():
    cm = ctx_of(toy_inputs(81), "V-AAL", "aal")
    y = field(cm, np.random.default_rng(82))
    S = np.arange(30, 55)
    seed_of, _, tabs_seed_of = plant_keys(11, 0)
    tb = AD.TAbs(cm, y, S, parcel_ids=cm.parcel_ids)
    r = DS.t_abs_legs(tb, {"site": 60, "species": 100}, tabs_seed_of)
    for leg, no in (("S1c", 21), ("S2c", 22)):
        assert r["legs"][leg]["seed"] == int(np.random.default_rng(seed_of(f"T_abs {leg}")).integers(2 ** 31))
        assert r["legs"][leg]["seed_leg"] == no
    rg = np.abs(gene_r(y, cm.X)[0])
    R1 = random_sets(np.arange(cm.G), S.size, 100, np.random.default_rng(seed_of("T_abs G1")), exclude=S)
    k = int(np.sum(rg[R1].mean(1) >= tb.T_obs))
    assert r["legs"]["G1"]["p"][1] == (k + 1) / 101 and r["legs"]["G1"]["p_registered_tail"] == (k + 1) / 101
    assert "G6s" not in r["legs"] and r["tail_direction"] == 1 and r["label"] == AD.TAbs.LABEL
    rdep = DS.t_abs_legs(tb, {"site": 60, "species": 100}, tabs_seed_of, depletion=True)
    assert rdep["tail_direction"] == -1 and rdep["legs"]["G1"]["p_registered_tail"] == rdep["legs"]["G1"]["p"][-1]
    # one shared G6l screen for the row's leg 5 and leg 25 = unshared screens
    sh = V.shared_g6l(cm, S, {"G6l": seed_of("G6l"), "T_abs G6l": tabs_seed_of("G6l")}, 100)
    rs = DS.t_abs_legs(tb, {"site": 60, "species": 100}, tabs_seed_of, g6l=sh["T_abs G6l"])
    assert rs["legs"]["G6l"]["p"] == r["legs"]["G6l"]["p"]
    dl = AD.DecodedList(cm, y, S, parcel_ids=cm.parcel_ids)
    v_sh = V.claim_verdict_a1(dl, {"site": 60, "species": 100}, seed_of, two_sided=True, g6l=sh["G6l"])
    v_un = V.claim_verdict_a1(dl, {"site": 60, "species": 100}, seed_of, two_sided=True)
    assert canon(v_sh) == canon(v_un)
    return dict(T=r["T"], p_upper={k: v["p_registered_tail"] for k, v in r["legs"].items()},
                g6l_status=r["legs"]["G6l"]["status"])


@check("seed_bridge_against_seeds_py")
def t_bridge():
    t, row, mi, ci = 8, 453, 1, 0  # key arithmetic only; no data is touched with a claim key
    b = V.seed_callables(t, row, mi, ci)
    for name, no in (("S1c", 0), ("S2c", 1), ("G1", 2), ("G3m", 3), ("G6s", 4), ("G6l", 5), ("permutation", 8),
                     ("re-selection", 10), ("G2", 11), ("G4", 12), ("G5", 13), ("J1", 14), ("naive joint", 15)):
        ss = b["seed_of"](name)
        assert list(ss.entropy) == [20260925, 100 + t, row, no, mi, ci], (name, ss.entropy)
        assert SD.same_seed_sequence(ss, SD.claim_seed(t, row, no, mi, ci))
    for name, no in (("S1c", 21), ("S2c", 22), ("G1", 23), ("G3m", 24), ("G6l", 25)):
        assert list(b["tabs_seed_of"](name).entropy) == [20260925, 100 + t, row, no, mi, ci]
    raises(ValueError, b["tabs_seed_of"], "G6s")
    raises(ValueError, b["seed_of"], "T_abs S1c")
    raises(ValueError, b["seed_of"], "G3")
    assert SD.same_seed_sequence(b["g3_seed"](), SD.g3_seed(t, row, mi, ci))
    jd = SD.j1_draws(t, row, mi, ci)
    g = np.random.default_rng(b["seed_of"]("J1"))
    assert [int(g.integers(2 ** 31)), int(g.integers(2 ** 31))] == [jd["S1c_seed"], jd["S2c_seed"]]
    assert jd["rng"].bit_generator.state == g.bit_generator.state  # the G2 sets come next from the same state
    nd = SD.naive_joint_draws(t, row, mi, ci)
    g = np.random.default_rng(b["seed_of"]("naive joint"))
    assert int(g.integers(2 ** 31)) == nd["S1_seed"] and nd["rng"].bit_generator.state == g.bit_generator.state
    return dict(key=b["key"], j1=[jd["S1c_seed"], jd["S2c_seed"]], naive_joint=nd["S1_seed"])


# ================================================================================================================
# asdg-skeptic review of WP1 (61e3887): B1 (descriptor rows), B4 (uninformative), B5 (descriptor legs at d*),
# B3 (plant keys of the verdict bridge)
# ================================================================================================================
NTAS_STATUS = ("not testable as stated: the decoded list pools positive and negative associations (synthetic status "
               "text of a pooled-list row)")


def no_survives_key(o) -> bool:
    if isinstance(o, dict):
        return "survives" not in o and all(no_survives_key(v) for v in o.values())
    if isinstance(o, list):
        return all(no_survives_key(v) for v in o)
    return True


def strong_plant(cls, seed0: int, key_case: int, n_try: int = 12):
    """A strong synthetic plant on the dk-ctx toy (y = .95 z(s_S) + .31 z(field), S = the module genes) whose computed
    two-sided verdict SURVIVES (searched over fields; the precondition of the B1 checks)."""
    s = CDK.score(SMOD)
    for j in range(n_try):
        y = 0.95 * z(s) + math.sqrt(1 - 0.95 ** 2) * z(field(CDK, np.random.default_rng(seed0 + j)))
        ad = cls(CDK, y, SMOD, parcel_ids=CDK.parcel_ids)
        legs = V.collect_legs(ad, KP, plant_keys(101, key_case + j)[0])
        comp = V.assemble_verdict_a1(legs, two_sided=True)
        if comp["survives"]:
            return y, ad, legs, comp
    raise AssertionError(f"precondition: no surviving strong {cls.__name__} plant in {n_try} fields")


@check("B1_descriptor_row_never_survives")
def t_b1():
    out = {}
    for cls in (AD.SetVsMap, AD.DecodedList):
        y, ad, legs, comp2 = strong_plant(cls, 1101, 0)
        comp1 = V.assemble_verdict_a1(legs, two_sided=False, registered_direction=comp2["d_star"])
        for comp in (comp2, comp1):
            assert comp["survives"] is True and comp["primary_status"] == "ok"   # the computed verdict survives
            rec = V.descriptor_row_record(comp, NTAS_STATUS, status_tsv=NTAS_STATUS,
                                          label="descriptor (not testable as stated)")
            assert rec["survives"] is False and rec["primary_status"] == NTAS_STATUS
            assert rec["primary_status_rule"] == V.DESCRIPTOR_ROW_RULE and rec["descriptor_row"] is True
            assert rec["passes_at_alpha"] is True and rec["reading"].startswith(V.DESCRIPTIVE + ": passes")
            assert rec["d_star"] == comp["d_star"] and rec["two_sided"] == comp["two_sided"]
            assert "p_conjunction" not in rec   # no p at the top of a descriptor row's record
            d = rec["descriptor"]
            assert d["passes_at_alpha"] is True and d["passes_at_alpha_label"] == V.DESCRIPTIVE and no_survives_key(d)
            assert {k: v for k, v in d.items() if k not in ("passes_at_alpha", "passes_at_alpha_label")} == \
                {k: v for k, v in comp.items() if k != "survives"}, "the computed record is kept unchanged otherwise"
        out[ad.form] = dict(d_star=comp2["d_star"], p_two_sided=comp2["p_conjunction"], p_one_sided=comp1["p_conjunction"])
    # two-cohort: both maps strong -> the computed claim survives; the descriptor row's record does not
    ya, _, la, _ = strong_plant(AD.SetVsMap, 1201, 100)
    yb, _, lb, _ = strong_plant(AD.SetVsMap, 1301, 200)
    tc = V.two_cohort_from_legs(la, lb, two_sided=True)
    assert tc["survives"] is True
    rt = V.descriptor_row_record(tc, NTAS_STATUS)
    assert rt["survives"] is False and rt["two_cohort"] is True and no_survives_key(rt["descriptor"])
    assert all(rt["descriptor"]["per_map"][k]["passes_at_alpha"] is True for k in tc["map_labels"])
    # a component descriptor row passing at component level: labelled descriptive, never a survival
    for j, yy in enumerate((ya, yb)):
        fc = AD.FixedComponent(CDK, yy, CDK.score(SMOD), parcel_ids=CDK.parcel_ids)
        rc = V.claim_verdict_a1(fc, 200, plant_keys(101, 300 + j)[0], two_sided=True)
        if rc["passes_component_level"]:
            break
    assert rc["passes_component_level"] is True, ("precondition: the component passes", rc["p_component"])
    rcd = V.descriptor_row_record(rc, NTAS_STATUS)
    assert rcd["survives"] is False and rcd["passes_at_alpha"] is True
    assert rcd["descriptor"]["passes_component_level_label"] == V.DESCRIPTIVE and no_survives_key(rcd["descriptor"])
    # a non-passing row reads "does not pass"; refusals
    weak = V.claim_verdict_a1(StubFull(0.1, P(0.4, 0.6), {"S1c": P(0.4, 0.6), "S2c": P(0.4, 0.6)},
                                       {k: P(0.4, 0.6) for k in AD.SPECIES_LEGS}), 500, None, two_sided=True)
    rw = V.descriptor_row_record(weak, NTAS_STATUS)
    assert rw["passes_at_alpha"] is False and rw["reading"].startswith(V.DESCRIPTIVE + ": does not pass")
    out["refused_empty_status"] = raises(ValueError, V.descriptor_row_record, tc, "")
    out["refused_not_a_record"] = raises(ValueError, V.descriptor_row_record, {"p": 1}, NTAS_STATUS)
    out["two_cohort"] = dict(p=tc["p_conjunction"], d_star=tc["d_star"])
    return out


def leading_component_plant(cls, ctx, seed0: int, key_case: int, n_try: int = 12):
    """y = the leading within-class component of the form's species basis (ctx.B for set-vs-map, the z-scored basis for
    decoded-list): one component dominates w_k = |a_k b_k| (a_k = 0 for k > 1), so the species leg is uninformative
    (amendment 3 §2; src/asdg/species.py:79-84). S random; searched until G1, G3m and G6l are computed and ok."""
    basis = ctx.B if cls is AD.SetVsMap else AD.z_basis(ctx)
    y = np.asarray(basis.U[:, 0], dtype=float).copy()
    for j in range(n_try):
        S = np.sort(np.random.default_rng(seed0 + j).choice(np.arange(25, ctx.G), 25, replace=False))
        ad = cls(ctx, y, S, parcel_ids=ctx.parcel_ids)
        flag, share = ad.uninformative()
        if not flag:
            continue
        legs = V.collect_legs(ad, KP, plant_keys(104, key_case + j)[0])
        st = legs["species"]["status"]
        if all(st[k] == "ok" for k in ("G1", "G3m", "G6l")):
            return ad, legs, share
    raise AssertionError(f"precondition: no uninformative {cls.__name__} plant with G6l ok in {n_try} sets")


@check("B4_uninformative_status_one_and_two_sided")
def t_b4():
    out = {}
    legs_ok = dict(L0=P(1e-6, 1 - 1e-6), site={"S1c": P(0.002, 0.998), "S2c": P(0.002, 0.998)},
                   species={k: P(0.005, 0.995) for k in AD.SPECIES_LEGS})
    for kw in (dict(two_sided=True), dict(two_sided=False, registered_direction=1)):
        r = V.claim_verdict_a1(StubFull(0.5, legs_ok["L0"], legs_ok["site"], legs_ok["species"], unin=True), 500, None,
                               **kw)
        assert r["primary_status"] == "uninformative" and r["engine_status"] == "uninformative", r["primary_status"]
        assert r["survives"] is False and "uninformative" in r["flags"] and r["uninformative"]["flag"] is True
        ok = V.claim_verdict_a1(StubFull(0.5, legs_ok["L0"], legs_ok["site"], legs_ok["species"], unin=False), 500,
                                None, **kw)
        assert ok["primary_status"] == "ok" and ok["survives"] is True   # the flag alone holds the verdict
        out["stub_" + ("two" if kw["two_sided"] else "one")] = dict(p_conj=r["p_conjunction"], flags=r["flags"])
    for cls in (AD.SetVsMap, AD.DecodedList):
        ad, legs, share = leading_component_plant(cls, CDK, 1401, 0)
        assert legs["uninformative"]["flag"] is True and legs["uninformative"]["share"] > 0.8
        for kw in (dict(two_sided=True), dict(two_sided=False, registered_direction=1),
                   dict(two_sided=False, registered_direction=-1)):
            r = V.assemble_verdict_a1(legs, **kw)
            assert r["primary_status"] == "uninformative" and r["survives"] is False and "uninformative" in r["flags"]
            assert r["engine_status"] == "uninformative"
        out[ad.form] = dict(share=share, T=legs["T"], status=r["primary_status"])
    return out


@check("B5_descriptor_leg_opposite_to_dstar")
def t_b5():
    out = {}
    # (1) the reading on a leg that favours -: reported at d* = + is min(1, 2 p(+)), never 2 min_d p(d)
    r = DS._with_direction(dict(p={1: 0.4, -1: 0.01}), 1, True)
    assert r["p_reported"] == 0.8 and r["p_per_leg_two_sided"] == 0.02
    r = DS._with_direction(dict(p={1: 0.7, -1: 0.01}), 1, True)
    assert r["p_reported"] == 1.0
    r = DS._with_direction(dict(p={1: 0.4, -1: 0.01}), 1, False)
    assert r["p_reported"] == 0.4 and "p_per_leg_two_sided" not in r
    # (2) descriptor_pass at a claim's d*: legs favouring the other direction are reported at d*, doubled
    c = ctx_of(toy_inputs(95, sizes=(34,), names=("cortex",)), "dk-ctx", "dk")
    S = np.arange(150, 175)
    y = 0.5 * z(c.score(S)) + 0.85 * z(field(c, np.random.default_rng(96)))
    seed_of, g3_seed, _ = plant_keys(105, 0)
    ad = AD.DecodedList(c, y, S, parcel_ids=c.parcel_ids)
    ver = V.assemble_verdict_a1(V.collect_legs(ad, {"site": 100, "species": 100}, seed_of), two_sided=True)
    d_claim = ver["d_star"]
    traj = traj_frame(c.U.genes, seed=97)
    n_opp, n_all = {}, {}
    for d in (d_claim, -d_claim):   # -d_claim: the same legs read for a claim whose d* is the other direction
        ds = DS.descriptor_pass(ad, seed_of, g3_seed, K_sets=100, K_surr=100, K_j1_sets=60, traj=traj, direction=d,
                                two_sided=True)
        n_opp[d] = n_all[d] = 0
        for rec in (*ds["legs"].values(), ds["level2"], ds["J1"], ds["naive_joint"]):
            p = rec.get("p")
            if p is None:
                continue
            n_all[d] += 1
            assert rec["p_reported"] == min(1.0, 2.0 * p[d]), (rec.get("leg"), d)
            assert rec["p_per_leg_two_sided"] == min(1.0, 2.0 * min(p[1], p[-1]))
            if p[-d] < p[d]:   # this leg favours the direction opposite the claim's d*
                n_opp[d] += 1
                assert rec["p_reported"] != rec["p_per_leg_two_sided"]
    assert n_opp[d_claim] >= 1, "no descriptor leg favoured the direction opposite the claim's own d*"
    assert n_opp[-d_claim] >= 1, "no descriptor leg favoured the direction opposite the swapped d*"
    out.update(d_star=d_claim, opposite_legs={str(k): v for k, v in n_opp.items()},
               legs_with_p={str(k): v for k, v in n_all.items()})
    return out


@check("B3_plant_seed_callables_vs_claim_keys")
def t_b3_bridge():
    """verdict.plant_seed_callables: the plant case's keys [20260925, 900, plant, case, class, leg]; G3 = R24's child;
    no plant stream equals the claim stream of the same leg (key arithmetic only)."""
    b = V.plant_seed_callables(8, 3, SD.plant_class_id("V-DK"))
    for name, no in (("S1c", 0), ("S2c", 1), ("G1", 2), ("G3m", 3), ("G6s", 4), ("G6l", 5), ("permutation", 8),
                     ("re-selection", 10), ("G2", 11), ("G4", 12), ("G5", 13), ("J1", 14), ("naive joint", 15)):
        assert list(b["seed_of"](name).entropy) == [20260925, 900, 8, 3, 12, no], name
    for name, no in (("S1c", 21), ("S2c", 22), ("G1", 23), ("G3m", 24), ("G6l", 25)):
        assert list(b["tabs_seed_of"](name).entropy) == [20260925, 900, 8, 3, 12, no]
    k3, kg = b["seed_of"]("G3m"), b["g3_seed"]()
    assert SD.same_seed_sequence(kg, np.random.SeedSequence(list(k3.entropy)).spawn(1)[0])
    raises(ValueError, b["tabs_seed_of"], "G6s")
    raises(ValueError, b["seed_of"], "T_abs S1c")
    c = V.seed_callables(8, 453, 0, 0)
    assert not np.array_equal(b["seed_of"]("S1c").generate_state(8), c["seed_of"]("S1c").generate_state(8))
    return dict(key=b["key"])


def main() -> int:
    t0 = time.time()
    print(f"A1 verdict / descriptor tests: scratch {SCRATCH}", flush=True)
    for run in CHECKS:
        run()
    out = SCRATCH / "test_verdict_results.json"
    out.write_text(json.dumps(A.jsonable(dict(results=RESULTS, failed=FAILED, seconds=round(time.time() - t0, 1))),
                              indent=1) + "\n", encoding="utf-8", newline="\n")
    back = json.loads(out.read_text(encoding="utf-8"))
    assert back["failed"] == FAILED
    print(f"{len(CHECKS) - len(FAILED)} of {len(CHECKS)} checks passed ({time.time() - t0:.0f}s); results {out}",
          flush=True)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
