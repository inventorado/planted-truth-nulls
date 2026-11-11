"""Plants of RUN_PLAN_amend_1.md v2.1 (FROZEN sha256 8e06d60e...; arcs/audit/FROZEN.txt) on synthetic data.

    cd arcs/audit/src
    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_amend1 [--scratch DIR] [--toys N]

P9 extension (R32, functional). P9's V-DK-subcortex plant (tests/test_verdict.py's construction) and 40 synthetic
     single-class 7-parcel toys x 3 maps (strong +, strong -, the + map with a tie y[1] = y[0]) through the production
     path, every exact leg of every form: set-vs-map, decoded-list, PLS-enrichment (S1c, S2c over 5,040 permutations;
     G6s over 64 sign patterns); T_abs (S1c, S2c); component site legs (fixed component, PLS1 R^2); J1's exact types
     (K_surr = 10,000 > 5,040); a rho form (the rho descriptor's site leg, adapters.RankRho, with and without the tie).
     Checked in both directions: every one-sided p >= its declared floor; the change from the UNAMENDED code (the a1_audit
     modules at e7029ed, blobs adapters 79381f75 / verdict d2c46a2e / descriptors e1cc4cb3, loaded from git into a
     scratch package) is exactly (identity rows not counted there)/(N + 1) and 0 for every other pattern (bitwise);
     rho counts equal an independent integer recomputation (scipy rankdata, Python Fractions); d* and every reported p
     of the two-sided verdict compared with the unamended code (a difference allowed only where the fixed count flips
     d*: listed, C1); one-sided p's of sampled legs bit-identical (7-parcel toys at K_site 2,000 and K_species 50;
     34-parcel toys at plant K). Must-fail variants: a wrong identity index (site legs: row 1; G6s: row 0), refused on
     10 / 10 toys each; the unamended count, caught by R32 (c)'s assertion (verdict.check_exact_floors) on some toys;
     a batch-normalised float rho (cascade.corr_matrix of rank rows), miscounting on some toys. Also R32 (b)'s
     exact-rational branch (a 12-parcel field class, y with a tie, continuous surrogates: denominators differ) against
     the independent recomputation and Fractions, R10's rank-biserial terms against scipy's Mann-Whitney U, and the
     stop on an exact MSR enumeration of a tied map (the gap: its identity row's ranks differ from y's).
P10 extension (R33). G = 150 toys: for m in {5, 12, 30, 50} on 12 toys x 2 streams the range screen
     (adapters.g6l_screen_range) gives sets, info and window curves bit-identical to the frozen a3_port.g6l_screen /
     WithinClassBasis.window_curve; g6l_sets_range equals the engine's g6l_sets (plant and exact modes); partial
     m = 51 / 60 / 75 through g6l_screen_safe raise nothing, every window has m distinct genes outside S at an offset
     <= n_rank - m + 1; m = 80 reads 'unmatched' (R8). Must-fail: truncated windows (caught by the m-genes check);
     float64 window sums (caught by the curve check; the sets alone would not catch it).
P12 extension (R34). The leg-8 null equals an independent re-implementation (row-wise rng.permutation loop, then T)
     bit for bit; every row is a permutation of y; the known-answer sha256 a36f3604...; loop equality at K = 5 and
     1,000 (n = 7 and 34); the n <= 7 assertion fires on a 7-parcel map (and not on 8). Must-fail: a within-class
     permutation, caught on a multi-class toy (no row moves a value across classes).
P13 extension (R34). A synthetic selected-list claim: Level-0 rows = SS(leg 10)'s construction, not SS(leg 8)'s; site
     surrogates = site_null from SS(leg 0) / SS(leg 1)'s integer seeds; a seed spy shows leg 8 never requested; the
     Level-0 generator's state after the refits = its state after the draws alone; a rule holding a generator and a
     rule drawing from numpy's global state are refused; an empty list gives T = 0.
P8 / P14 extensions (R36). (a) a G6l-unmatched claim: no doubled p, every one-sided p reported; (b) a constructed
     two-cohort tie with opposite T signs: "does not survive", p = 1, d* undefined (and the impossible M < .5 refused);
     (c) a component claim at plant K = 30 permutations and surrogates: "resolution-limited; does not pass"; (d)
     descriptor reported p's at d* equal 2 p(d*) (one-sided: p(d)); (d') legs favouring the other direction are
     reported at d* (asdg-skeptic WP1 review B5).
asdg-skeptic review of WP1 (61e3887): B2 (P14 extension) a two-sided two-cohort claim whose map b has no species p
     (G6l unmatched / degenerate, R8; stubs and a synthetic module toy) - no exception, d* undefined, one-sided p's per
     map, no doubled p, nothing survives; one-sided: d* = the registered direction. C7 build_context_checked builds
     V-DK-subcortex and MIST64 on synthetic atlas files (pins patched to the synthetic hashes, restored after), with
     R35's first-use check; must-fail: a JSON tissue class changed, a JSON primary parcel missing, a wrong L7 pin. C8
     class parcels absent from the map are counted as dropped; a map parcel outside the class is refused.

Synthetic data only: e3_plants' GAMBA / AHBA paths point at a non-existent scratch path before anything is imported.
Seeds: test-local plant-style keys SeedSequence([20260925, 900, plant, case, cls, leg]) (target 900 does not exist).
Exits non-zero on any failure. Prints ASCII only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import time
import traceback
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
for _p in (ROOT / "src", ROOT / "arcs" / "audit" / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

ap = argparse.ArgumentParser()
ap.add_argument("--scratch", default=None, help="scratch directory (default: a new temporary directory)")
ap.add_argument("--toys", type=int, default=40, help="number of synthetic 7-parcel toys (P9 extension: 40)")
ARGS, _ = ap.parse_known_args()
SCRATCH = Path(ARGS.scratch or tempfile.mkdtemp(prefix="a1_amend1_")).resolve()
SCRATCH.mkdir(parents=True, exist_ok=True)
NO_DATA = SCRATCH / "no_such_data_dir"  # never created: an unpatched data read fails here
assert not NO_DATA.exists()

import e3_plants  # noqa: E402

e3_plants.GAMBA_CSV = NO_DATA / "gamba.csv"
e3_plants.AHBA = NO_DATA

import a1_audit.a3_port as A  # noqa: E402
import a1_audit.adapters as AD  # noqa: E402
import a1_audit.descriptors as DS  # noqa: E402
import a1_audit.verdict as V  # noqa: E402
from asdg.cascade import corr_matrix  # noqa: E402
from asdg.spatial import site_null  # noqa: E402

A.AHBA = NO_DATA

# ----------------------------------------------------------------------------------------------------------------
# the unamended code: a1_audit at e7029ed (RUN_PLAN_amend_1 §0's blobs), loaded from git into a scratch package
# ----------------------------------------------------------------------------------------------------------------
UNAMENDED_COMMIT = "e7029ed"
UNAMENDED_BLOBS = {"adapters.py": "79381f75", "verdict.py": "d2c46a2e", "descriptors.py": "e1cc4cb3",
                   "a3_port.py": "a9c2f3ab"}


def git(*a) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, check=True).stdout


def load_unamended():
    pkg = SCRATCH / "unamended_pkg" / "a1_unamended"
    pkg.mkdir(parents=True, exist_ok=True)
    for name, prefix in UNAMENDED_BLOBS.items():
        rel = f"arcs/audit/src/a1_audit/{name}"
        bid = git("rev-parse", f"{UNAMENDED_COMMIT}:{rel}").decode().strip()
        assert bid.startswith(prefix), (name, bid)
    # a3_port is unchanged by the amendment: the working copy's blob is e7029ed's, so the shim re-uses the module
    assert git("hash-object", str(ROOT / "arcs/audit/src/a1_audit/a3_port.py")).decode().strip().startswith(
        UNAMENDED_BLOBS["a3_port.py"]), "a3_port.py changed"
    (pkg / "__init__.py").write_bytes(b"")
    (pkg / "a3_port.py").write_bytes(b"import sys\nfrom a1_audit import a3_port as _m\nsys.modules[__name__] = _m\n")
    for name in ("adapters.py", "verdict.py", "descriptors.py"):
        data = git("show", f"{UNAMENDED_COMMIT}:arcs/audit/src/a1_audit/{name}")
        (pkg / name).write_bytes(data)
        assert (pkg / name).read_bytes() == data  # a writer reads back what it wrote
    sys.path.insert(0, str(pkg.parent))
    import a1_unamended.adapters as AD0
    import a1_unamended.descriptors as DS0
    import a1_unamended.verdict as V0
    assert AD0.A3 is A and AD0 is not AD and not hasattr(AD0, "identity_rows")
    return AD0, V0, DS0


AD0, V0, DS0 = load_unamended()

RESULTS: dict = {}
FAILED: list = []
CHECKS: list = []
LEGNO = {"S1c": 0, "S2c": 1, "G1": 2, "G3m": 3, "G6s": 4, "G6l": 5, "permutation": 8, "re-selection": 10, "G2": 11,
         "G4": 12, "G5": 13, "J1": 14, "naive joint": 15, "T_abs S1c": 21, "T_abs S2c": 22, "T_abs G1": 23,
         "T_abs G3m": 24, "T_abs G6l": 25}
TABS = {"S1c": "T_abs S1c", "S2c": "T_abs S2c", "G1": "T_abs G1", "G3m": "T_abs G3m", "G6l": "T_abs G6l"}


def keys(plant: int, case: int, cls: int = 0, spy: list | None = None):
    def seed_of(leg):
        if spy is not None:
            spy.append(leg)
        return np.random.SeedSequence([20260925, 900, plant, case, cls, LEGNO[leg]])

    def tabs_seed_of(leg):
        return seed_of(TABS[leg])
    return seed_of, tabs_seed_of


def check(name):
    def deco(fn):
        def run():
            t0 = time.time()
            try:
                measured = fn() or {}
                RESULTS[name] = dict(result="pass", seconds=round(time.time() - t0, 2), **measured)
                print(f"PASS {name} ({time.time() - t0:.1f}s) {json.dumps(A.jsonable(measured))[:1500]}", flush=True)
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


def raises(exc, f, *a, **k) -> str:
    try:
        f(*a, **k)
    except exc as e:  # noqa: BLE001
        return f"{type(e).__name__}: {str(e)[:90]}"
    raise AssertionError(f"{getattr(f, '__name__', f)} did not raise {exc.__name__}")


# ================================================================================================================
# toys (as tests/test_verdict.py)
# ================================================================================================================
def toy_inputs(seed=1, sizes=(24, 14, 8), G=300, scale=(0.2, 5.0), module=None, names=None, n_brain=50):
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
    brain = sorted(genes[i] for i in rng.choice(G, n_brain, replace=False))
    return dict(expr=expr, classes=cl, xyz=xyz, info=info, brain=brain, f=f, rng=rng)


def ctx_of(inp, name, atlas=None):
    return A.ClassContext(name, inp["expr"].copy(), inp["classes"].copy(), inp["xyz"].copy(), inp["info"].copy(),
                          A.symbols_background(inp["brain"]), atlas)


def field(ctx, rng, length=35.0):
    L = np.linalg.cholesky(np.exp(-(ctx.D / length) ** 2) + 1e-6 * np.eye(ctx.n))
    return L @ rng.standard_normal(ctx.n)


z = A.zscore
SUB = ("subcortex/brainstem",)
K_EXACT = {"site": 10000, "species": 200}
FULL = ((AD.SetVsMap, "SetVsMap"), (AD.DecodedList, "DecodedList"), (AD.PlsEnrichment, "PlsEnrichment"))


def battery_toys(n: int):
    """[(label, ctx, S, maps)]: P9's plant (tests/test_verdict.py t_p9's construction) and n synthetic toys."""
    out = []
    inp = toy_inputs(41, sizes=(7,), names=SUB)
    c = ctx_of(inp, "V-DK-subcortex", "dk")
    y = field(c, np.random.default_rng(42)) + 0.3 * np.random.default_rng(43).standard_normal(c.n)
    yt = y.copy()
    yt[1] = yt[0]
    out.append(("P9 plant", c, np.arange(25), [("P9 map", y), ("P9 map, tie", yt)]))
    for i in range(n):
        inp = toy_inputs(5000 + i, sizes=(7,), G=120, names=SUB, n_brain=30)
        c = ctx_of(inp, "V-DK-subcortex", "dk")
        r = np.random.default_rng(6000 + i)
        S = np.sort(r.choice(c.G, 10, replace=False))
        s = c.score(S)
        y0 = z(s) + 0.05 * z(r.standard_normal(c.n))
        y1 = -z(s) + 0.3 * z(r.standard_normal(c.n))
        y2 = y0.copy()
        y2[1] = y2[0]
        out.append((f"toy {i}", c, S, [("+", y0), ("-", y1), ("+ tie", y2)]))
    return out


def bit_rows(rows, i) -> np.ndarray:
    """Independent of adapters.identity_rows: the indices of rows whose bytes equal row i's."""
    R = np.ascontiguousarray(np.atleast_2d(np.asarray(rows, dtype=np.float64)))
    ref = R[i].tobytes()
    return np.array([j for j in range(len(R)) if R[j].tobytes() == ref], dtype=int)


class Tally:
    def __init__(self):
        self.evals = 0
        self.missed_any = 0
        self.unamended_below_floor = 0
        self.dup_rows = 0
        self.per_leg: dict = {}

    def add(self, key, missed, below, dups):
        self.evals += 1
        t = self.per_leg.setdefault(key, [0, 0, 0])
        t[0] += 1
        t[1] += int(missed)
        t[2] += int(below)
        self.missed_any += int(missed)
        self.unamended_below_floor += int(below)
        self.dup_rows += int(dups)


def check_exact_leg(T: Tally, key: str, null_am, null_un, rows, obs, p_am, p_un, floor):
    """R32 (a) / (c) on one exact leg: amended vs unamended counts, both directions (see the module docstring)."""
    null_am, null_un = np.asarray(null_am, dtype=float), np.asarray(null_un, dtype=float)
    N = null_un.size
    assert null_am.size == N and rows.size >= 1
    other = np.setdiff1d(np.arange(N), rows)
    assert np.array_equal(null_am[other].view(np.uint64), null_un[other].view(np.uint64)), \
        f"{key}: a non-identity pattern moved"
    assert np.all(null_am[rows] == obs), f"{key}: identity rows not set to the observed statistic"
    missed_any = below_any = False
    for d in (1, -1):
        assert p_am[d] >= floor, f"{key}: amended p({d:+d}) {p_am[d]} < floor {floor}"
        k_am = int(np.sum(d * null_am >= d * obs))
        k_un = int(np.sum(d * null_un >= d * obs))
        missed = int(np.sum(~(d * null_un[rows] >= d * obs)))
        assert k_am - k_un == missed, f"{key}: count change {k_am - k_un} != identity rows missed {missed}"
        assert p_am[d] == (k_am + 1) / (N + 1) and p_un[d] == (k_un + 1) / (N + 1), f"{key}: p != (k + 1)/(N + 1)"
        missed_any |= missed > 0
        below_any |= p_un[d] < floor
    T.add(key, missed_any, below_any, len(rows) - 1)


# ================================================================================================================
# P9 extension (R32)
# ================================================================================================================
def rho_independent(y, b, maps):
    """k(+), k(-) of Spearman rho counted with scipy's rankdata (x 2, as integers) and Python Fractions of
    sign(rho) rho^2: an implementation independent of adapters.rank_corr_terms / rank_corr_counts."""
    def terms(v, w):
        a = [int(round(2 * x)) - (len(v) + 1) for x in stats.rankdata(v)]
        c = [int(round(2 * x)) - (len(w) + 1) for x in stats.rankdata(w)]
        n_ = sum(x * u for x, u in zip(a, c))
        q = sum(x * x for x in a) * sum(u * u for u in c)
        return Fraction(n_ * abs(n_), q)
    o = terms(y, b)
    vals = [terms(m, b) for m in maps]
    return sum(1 for v in vals if v >= o), sum(1 for v in vals if v <= o)


@check("P9ext_R32_identity_battery")
def t_p9ext():
    toys = battery_toys(ARGS.toys)
    T = Tally()
    c1, dstar_same = [], 0
    rho_rows, rho_float_miscount_toys, rho_spearmanr_miss = 0, set(), 0
    rho_float_caught_by_r32c = set()
    j1_types = 0
    j1_status = {}
    reported_compared = 0
    for t_i, (label, c, S, maps) in enumerate(toys):
        comp = field(c, np.random.default_rng(7000 + t_i))
        for m_i, (mlabel, y) in enumerate(maps):
            seed_of, tabs_seed_of = keys(9, 100 * t_i + m_i)
            tag = f"{label} map {mlabel}"
            # ---- full forms: site S1c / S2c and G6s
            for cls, cname in FULL:
                cls0 = getattr(AD0, cname)
                ad, ad0 = cls(c, y, S, parcel_ids=c.parcel_ids), cls0(c, y, S, parcel_ids=c.parcel_ids)
                assert ad.T_obs == ad0.T_obs
                s_am = ad.site_leg(10000, seed_of, return_surrogates=True)
                s_un = ad0.site_leg(10000, seed_of)
                for leg in ("S1c", "S2c"):
                    a, u = s_am[leg], s_un[leg]
                    assert a["info"]["exact"] and a["info"]["n_null"] == 5040 and a["floor"] == 2 / 5041
                    rows = bit_rows(a["surrogates"], 0)
                    assert a["info"]["identity"]["rows_counted_as_identity"] == len(rows)
                    check_exact_leg(T, f"{cname} {leg}", a["null"], u["null"], rows, ad.T_obs, a["p"], u["p"],
                                    a["floor"])
                sp_am = ad.species_leg(200, seed_of)
                sp_un = ad0.species_leg(200, seed_of)
                Bd = c.B if cls is AD.SetVsMap else AD.z_basis(c)
                N6 = Bd.g6s_scores(S, 200, np.random.default_rng(0))  # exact: every sign pattern, no draw
                assert sp_am["g6s_exact"] and len(N6) == 64
                rows = bit_rows(N6, len(N6) - 1)
                assert sp_am["g6s_identity"]["rows_counted_as_identity"] == len(rows)
                check_exact_leg(T, f"{cname} G6s", sp_am["null"]["G6s"], sp_un["null"]["G6s"], rows,
                                sp_am["species_obs"], sp_am["p"]["G6s"], sp_un["p"]["G6s"], sp_am["floors"]["G6s"])
                for leg in ("G1", "G3m", "G6l"):  # sampled species legs: bit-identical
                    assert A.jsonable(sp_am["p"][leg]) == A.jsonable(sp_un["p"][leg]), (cname, leg)
                # ---- the two-sided verdict: d* and every reported p against the unamended code (C1)
                legs = V.collect_legs(ad, K_EXACT, seed_of)
                legs0 = V0.collect_legs(ad0, K_EXACT, seed_of)
                ra = V.assemble_verdict_a1(legs, two_sided=True)
                ru = V0.assemble_verdict_a1(legs0, two_sided=True)
                if ra["d_star"] == ru["d_star"]:
                    dstar_same += 1
                    d = ra["d_star"]
                    for leg in ("Level 0", "G1", "G3m", "G6l"):
                        assert ra["legs"][leg]["p_reported"] == ru["legs"][leg]["p_reported"], (tag, cname, leg)
                        reported_compared += 1
                    for leg in ("S1c", "S2c", "G6s"):
                        pa, pu = ra["legs"][leg], ru["legs"][leg]
                        if d is not None:
                            assert pa["p_reported"] == min(1.0, 2.0 * pa["p_one_sided"][d])
                            assert pu["p_reported"] == min(1.0, 2.0 * pu["p_one_sided"][d])
                        reported_compared += 1
                else:
                    c1.append(dict(toy=label, map=mlabel, form=cname, d_star_amended=ra["d_star"],
                                   d_star_unamended=ru["d_star"], p_amended=ra["p_conjunction"],
                                   p_unamended=ru["p_conjunction"]))
                # ---- J1's exact types
                j = DS.j1_leg(ad, seed_of, K_sets=40, K_surr=10000, return_draws=True)
                j1_status[j["status"]] = j1_status.get(j["status"], 0) + 1
                if j["status"] == "ok":
                    dr = j["_draws"]
                    ex = {k: v["exact"] for k, v in j["types"].items()}
                    assert all(ex.values())
                    za = DS.j1_core(ad, dr["sets"], dr["surrogates"], exact=ex, return_z=True)
                    zu = DS.j1_core(ad, dr["sets"], dr["surrogates"], exact=None, return_z=True)
                    j0 = DS0.j1_leg(ad0, seed_of, K_sets=40, K_surr=10000)
                    for name in ("S1c", "S2c"):
                        assert za["types"][name]["p"] == j["types"][name]["p"]
                        assert zu["types"][name]["p"] == j0["types"][name]["p"]  # exact=None = the unamended count
                        rows = bit_rows(dr["surrogates"][name], 0)
                        check_exact_leg(T, f"{cname} J1 {name}", za["_z"][name], zu["_z"][name], rows, za["z_obs"],
                                        za["types"][name]["p"], zu["types"][name]["p"], za["types"][name]["floor"])
                        j1_types += 1
            # ---- T_abs site legs (legs 21 / 22)
            tb, tb0 = AD.TAbs(c, y, S, parcel_ids=c.parcel_ids), AD0.TAbs(c, y, S, parcel_ids=c.parcel_ids)
            s_am, s_un = tb.site_leg(10000, tabs_seed_of, return_surrogates=True), tb0.site_leg(10000, tabs_seed_of)
            for leg in ("S1c", "S2c"):
                check_exact_leg(T, f"TAbs {leg}", s_am[leg]["null"], s_un[leg]["null"],
                                bit_rows(s_am[leg]["surrogates"], 0), tb.T_obs, s_am[leg]["p"], s_un[leg]["p"],
                                s_am[leg]["floor"])
            tl = DS.t_abs_legs(tb, {"site": 10000, "species": 200}, tabs_seed_of)
            assert tl["legs"]["S1c"]["p"] == s_am["S1c"]["p"]
            # ---- component site legs (fixed component; PLS1 R^2)
            for cname, mk in (("FixedComponent", lambda M: M.FixedComponent(c, y, comp, parcel_ids=c.parcel_ids)),
                              ("Pls1R2", lambda M: M.Pls1R2(c, y, parcel_ids=c.parcel_ids))):
                a1, a0 = mk(AD), mk(AD0)
                s_am, s_un = a1.site_leg(10000, seed_of, return_surrogates=True), a0.site_leg(10000, seed_of)
                for leg in ("S1c", "S2c"):
                    check_exact_leg(T, f"{cname} {leg}", s_am[leg]["null"], s_un[leg]["null"],
                                    bit_rows(s_am[leg]["surrogates"], 0), a1.T_obs, s_am[leg]["p"], s_un[leg]["p"],
                                    s_am[leg]["floor"])
            # ---- the rho form (R32 (b)): exact counts = independent recomputation; float-batch variant must fail
            b = c.score(S)
            rr = AD.RankRho(c, y, b, parcel_ids=c.parcel_ids)
            assert abs(rr.T_obs - stats.spearmanr(y, b).statistic) < 1e-12
            ex_ = rr.site_leg(10000, seed_of, return_surrogates=True)
            try:  # the must-fail variant: its miscount is caught by the count comparison or by R32 (c)'s assertion
                fb = rr.site_leg(10000, seed_of, _comparison="float-batch")
            except AD.FunctionalDefect:
                fb = None
                rho_float_caught_by_r32c.add(label)
            for leg in ("S1c", "S2c"):
                sur = ex_[leg]["surrogates"]
                kp, km = rho_independent(y, b, sur)
                rinfo = ex_[leg]["info"]["rank_rule"]
                assert (rinfo["k_plus"], rinfo["k_minus"]) == (kp, km), (tag, leg, rinfo, kp, km)
                assert ex_[leg]["p"] == {1: (kp + 1) / 5041, -1: (km + 1) / 5041}
                assert min(ex_[leg]["p"].values()) >= 2 / 5041
                if fb is None or fb[leg]["p"] != ex_[leg]["p"]:
                    rho_float_miscount_toys.add(label)
                if leg == "S1c":
                    sr = np.array([stats.spearmanr(m_, b).statistic for m_ in sur])
                    o = stats.spearmanr(y, b).statistic
                    rho_spearmanr_miss += int((int(np.sum(sr >= o)), int(np.sum(sr <= o))) != (kp, km))
                rho_rows += 1
    assert T.evals > 0 and T.missed_any > 0, "the battery never exercised a missed identity (the plant is inert)"
    assert dstar_same + len(c1) > 0
    assert len(rho_float_miscount_toys) >= 1, "the batch-normalised float rho variant was not caught"
    return dict(toys=len(toys), exact_leg_evaluations=T.evals,
                evaluations_where_unamended_missed_the_identity=T.missed_any,
                evaluations_where_unamended_p_below_floor=T.unamended_below_floor,
                bit_identical_duplicate_identity_rows=T.dup_rows,
                per_leg_evals_missed_below={k: v for k, v in sorted(T.per_leg.items())},
                verdicts_compared=dstar_same + len(c1), d_star_unchanged=dstar_same,
                reported_p_compared=reported_compared, C1_d_star_flips=c1, J1_status=j1_status,
                J1_exact_types_checked=j1_types, rho_legs_checked=rho_rows,
                rho_float_batch_miscount_toys=f"{len(rho_float_miscount_toys)} / {len(toys)}",
                rho_float_batch_toys_stopped_by_R32c=f"{len(rho_float_caught_by_r32c)} / {len(toys)}",
                rho_scipy_spearmanr_per_surrogate_mismatch=rho_spearmanr_miss)


@check("P9ext_R32_must_fail_and_sampled_legs")
def t_p9ext_mustfail():
    toys = battery_toys(ARGS.toys)[1:]
    wrong_site = wrong_g6s = caught_unamended = 0
    first10 = toys[:10]
    for t_i, (label, c, S, maps) in enumerate(first10):
        y = maps[0][1]  # no tie (a wrong index could otherwise hit a bit-identical duplicate)
        seed_of, _ = keys(9, 900 + t_i)
        ad = AD.SetVsMap(c, y, S, parcel_ids=c.parcel_ids)
        try:
            ad.site_leg(10000, seed_of, _identity_index=1)
        except AD.FunctionalDefect:
            wrong_site += 1
        try:
            ad.species_leg(200, seed_of, _identity_index=0)
        except AD.FunctionalDefect:
            wrong_g6s += 1
        # the unamended count, through R32 (c)'s assertion (the driver's check_exact_floors)
        for cls0, cname in ((AD0.SetVsMap, "s"), (AD0.DecodedList, "d")):
            legs0 = V0.collect_legs(cls0(c, y, S, parcel_ids=c.parcel_ids), K_EXACT, seed_of)
            try:
                V.check_exact_floors(legs0)
            except AD.FunctionalDefect:
                caught_unamended += 1
                break
    assert wrong_site == len(first10) and wrong_g6s == len(first10), (wrong_site, wrong_g6s)
    assert caught_unamended >= 1, "R32 (c) never caught the unamended count"
    # sampled legs bit-identical: 7-parcel toys at K_site 2,000 (< 5,040) and K_species 50 (< 64)
    n_site = n_g6s = 0
    for t_i, (label, c, S, maps) in enumerate(toys):
        y = maps[0][1]
        seed_of, _ = keys(9, 2000 + t_i)
        for cname in ("SetVsMap", "DecodedList"):
            ad, ad0 = getattr(AD, cname)(c, y, S, parcel_ids=c.parcel_ids), getattr(AD0, cname)(c, y, S,
                                                                                               parcel_ids=c.parcel_ids)
            sa, su = ad.site_leg(2000, seed_of), ad0.site_leg(2000, seed_of)
            for leg in ("S1c", "S2c"):
                assert not sa[leg]["info"]["exact"] and "identity" not in sa[leg]["info"]
                assert sa[leg]["p"] == su[leg]["p"] and np.array_equal(sa[leg]["null"], su[leg]["null"])
                n_site += 1
            ga, gu = ad.species_leg(50, seed_of), ad0.species_leg(50, seed_of)
            assert not ga["g6s_exact"] and ga["g6s_identity"] is None
            assert ga["p"]["G6s"] == gu["p"]["G6s"]
            n_g6s += 1
    # 34-parcel toys at plant K (500 / 200): S1c, S2c, G1, G3m, G6s
    n34 = 0
    for i in range(3):
        c = ctx_of(toy_inputs(8100 + i, sizes=(34,), names=("cortex",)), "dk-ctx", "dk")
        y = field(c, np.random.default_rng(8200 + i))
        S = np.arange(20, 45)
        seed_of, _ = keys(9, 3000 + i)
        ad, ad0 = AD.SetVsMap(c, y, S, parcel_ids=c.parcel_ids), AD0.SetVsMap(c, y, S, parcel_ids=c.parcel_ids)
        sa, su = ad.site_leg(500, seed_of), ad0.site_leg(500, seed_of)
        ga, gu = ad.species_leg(200, seed_of), ad0.species_leg(200, seed_of)
        for leg in ("S1c", "S2c"):
            assert sa[leg]["p"] == su[leg]["p"]
            n34 += 1
        for leg in ("G1", "G3m", "G6s"):
            assert ga["p"][leg] == gu["p"][leg]
            n34 += 1
    return dict(wrong_identity_index_refused=dict(site=f"{wrong_site} / {len(first10)}",
                                                  G6s=f"{wrong_g6s} / {len(first10)}"),
                unamended_count_caught_by_R32c=f"{caught_unamended} / {len(first10)} toys",
                sampled_bit_identical=dict(site_K2000=n_site, G6s_K50=n_g6s, legs_34_parcels=n34))


@check("R32b_rational_branch_and_rank_biserial")
def t_r32b():
    # a 12-parcel single class (a field class: S1c BrainSMASH, S2c MSR over 2^11 = 2,048 sign patterns); y with a
    # tie: the continuous surrogates break it, so their rank denominators differ from y's -> the exact-rational branch
    inp = toy_inputs(9100, sizes=(12,), G=80, names=SUB, n_brain=20)
    c = ctx_of(inp, "toy-12", None)
    y = field(c, np.random.default_rng(9101))
    y[3] = y[7]
    b = c.score(np.arange(8))
    rr = AD.RankRho(c, y, b, parcel_ids=c.parcel_ids)
    sl = rr.site_leg(1000, keys(32, 1)[0], return_surrogates=True)  # both legs sampled (2,048 > 1,000)
    branches = {}
    for leg in ("S1c", "S2c"):
        info = sl[leg]["info"]
        kp, km = rho_independent(y, b, sl[leg]["surrogates"])
        assert (info["rank_rule"]["k_plus"], info["rank_rule"]["k_minus"]) == (kp, km)
        assert not info["exact"]
        branches[leg] = dict(exact=info["exact"], n=info["n_null"], branch=info["rank_rule"]["branch"])
    # BrainSMASH (resample=True) re-uses y's values, the tie included: common denominators; MSR's continuous
    # surrogates break the tie: the branch is decided by computing, never by the type of null
    assert branches["S2c"]["branch"] == AD.RANK_BRANCH_RATIONAL, branches
    # at K 10,000 S2c is exact (2,048 MSR patterns): its identity row reconstructs y only to rounding, which breaks
    # y's tie, so the identity state's ranks differ from y's. R32 (b)'s "equal-valued states are then bit-equal" does
    # not hold for an exact MSR enumeration of a tied map (unreachable at the registered sizes: the only exact rank
    # legs are the 7-parcel V-DK-subcortex permutations); the runner stops rather than miscount (a gap, reported).
    try:
        rr.site_leg(10000, keys(32, 1)[0])
        msr_tie = "no stop (the reconstruction kept the tie on this toy)"
    except AD.FunctionalDefect as e:
        msr_tie = f"FunctionalDefect: {str(e)[:70]}"
    branches["S2c exact, tie in y"] = msr_tie
    # direct comparator checks against Fractions (both branches), large integers included (no int64 anywhere)
    rng = np.random.default_rng(9102)
    big = 10 ** 30
    N0, Q0 = 7 * big, 50 * big * big
    N = [int(x) * big for x in rng.integers(-10, 10, 200)]
    Q = [int(x) * big * big for x in rng.integers(40, 60, 200)]
    c_ = AD.rank_corr_counts(N0, Q0, N, Q)
    key = lambda n, q: Fraction(n * abs(n), q)  # noqa: E731
    assert c_["k_plus"] == sum(key(n, q) >= key(N0, Q0) for n, q in zip(N, Q))
    assert c_["k_minus"] == sum(key(n, q) <= key(N0, Q0) for n, q in zip(N, Q))
    assert c_["branch"] == AD.RANK_BRANCH_RATIONAL
    # R10's rank-biserial: (num, den) = (2 U1 - n1 n2, n1 n2); vs scipy's Mann-Whitney U; rational_counts' branches
    vals = rng.integers(0, 6, 15).astype(float)
    grp = np.zeros(15, bool)
    grp[:6] = True
    num, den = AD.rank_biserial_terms(vals, grp)
    U1 = stats.mannwhitneyu(vals[grp], vals[~grp]).statistic
    assert Fraction(num, den) == Fraction(2 * Fraction(U1).limit_denominator(4) - den, den)
    nums, dens = [], []
    for k in range(300):
        g = np.zeros(15, bool)
        g[rng.choice(15, 6 + (k % 3), replace=False)] = True
        n_, d_ = AD.rank_biserial_terms(rng.permutation(vals), g)
        nums.append(n_)
        dens.append(d_)
    rc = AD.rational_counts(num, den, nums, dens)
    assert rc["branch"] == AD.RANK_BRANCH_RATIONAL
    assert rc["k_plus"] == sum(Fraction(n_, d_) >= Fraction(num, den) for n_, d_ in zip(nums, dens))
    rc2 = AD.rational_counts(num, den, nums[::3], dens[::3])
    assert rc2["branch"] == AD.RANK_BRANCH_COMMON
    return dict(rho_12_parcels=branches, rank_biserial=dict(num=num, den=den, k_plus=rc["k_plus"]))


# ================================================================================================================
# P10 extension (R33)
# ================================================================================================================
@check("P10ext_R33_partial_window")
def t_p10ext():
    n_toys, Ms = 12, (5, 12, 30, 50)
    full_streams = full_same = curves_same = curves_n = 0
    f64_curves_differ = f64_sets_differ = f64_n = 0
    sets_range_same = 0
    partial = {}
    trunc_caught = trunc_n = 0
    for t in range(n_toys):
        c = ctx_of(toy_inputs(9200 + t, G=150, n_brain=30), "toy-150", None)
        B = c.B
        r = np.random.default_rng(9300 + t)
        for m in Ms:
            S = np.sort(r.choice(B.G, m, replace=False))
            n_rank, half = B.G - m - 1, (B.G - m - 1) // 2
            assert AD.pool_status(B, S)["G6l"] == "ok" and AD.g6l_offset_max(B.G, m) == half
            seeds = [9400 + 10 * t + m, 9401 + 10 * t + m]
            frozen = A.g6l_screen(B, S, [np.random.default_rng(s) for s in seeds], keep=60)
            got, det = AD.g6l_screen_range(B, S, [np.random.default_rng(s) for s in seeds], keep=60,
                                           return_detail=True)
            for (fs, fi), (gs, gi) in zip(frozen, got):
                full_streams += 1
                same_sets = (fs is None and gs is None) or (fs is not None and gs is not None and np.array_equal(fs, gs))
                full_same += int(same_sets and fi == gi and list(fi) == list(gi))
            # window curves against the engine's WithinClassBasis.window_curve, every seed
            C0 = np.empty((half + m, B.ZwT32.shape[1]), np.float32)
            C0[0] = 0.0
            ok = True
            for g, cv in det["curves"].items():
                _, ce = B.window_curve(g, S, m, n_rank, half, C0)
                ok &= cv.shape == ce.shape and np.array_equal(cv.view(np.uint64), ce.view(np.uint64))
            curves_n += 1
            curves_same += int(ok)
            # must-fail: float64 window sums (curves differ; sets may not)
            f64, d64 = AD.g6l_screen_range(B, S, [np.random.default_rng(s) for s in seeds], keep=60,
                                           return_detail=True, _variant="float64")
            f64_n += 1
            f64_curves_differ += int(any(not np.array_equal(d64["curves"][g], det["curves"][g]) for g in det["curves"]))
            f64_sets_differ += int(any(not ((a is None and b_ is None) or (a is not None and b_ is not None
                                                                         and np.array_equal(a, b_)))
                                       for (a, _), (b_, _) in zip(f64, got)))
            # the engine's g6l_sets (plant mode and exact) = g6l_sets_range where the full range fits
            if t < 3:
                for exact in (False, True):
                    e = B.g6l_sets(S, 40, np.random.default_rng(seeds[0]), exact=exact)
                    q = AD.g6l_sets_range(B, S, 40, np.random.default_rng(seeds[0]), exact=exact)
                    sets_range_same += int(((e[0] is None and q[0] is None) or np.array_equal(e[0], q[0]))
                                           and e[1] == q[1])
        # partial range: m = 51, 60, 75 (no exception; windows of m distinct genes outside S; offsets in range)
        for m in (51, 60, 75):
            S = np.sort(r.choice(B.G, m, replace=False))
            n_rank = B.G - m - 1
            assert AD.pool_status(B, S)["G6l"] == "partial"
            o_max = AD.g6l_offset_max(B.G, m)
            assert o_max == n_rank - m + 1 < n_rank // 2
            res = AD.g6l_screen_safe(B, S, [np.random.default_rng(9500 + t)], keep=60)
            (sets, info), = res
            _, det = AD.g6l_screen_range(B, S, [np.random.default_rng(9500 + t)], keep=None, return_detail=True)
            assert all(0 <= o <= o_max for o in det["offsets"][0])
            if sets is not None:
                for w in sets:
                    assert w.size == m and np.unique(w).size == m and not np.isin(w, S).any()
                    rr = B.ZwT @ B.ZwT[w[0]]
                    rr[S] = -np.inf
                    rr[w[0]] = -np.inf
                    rank = np.argsort(-rr, kind="stable")[:n_rank]
                    pos = [o for o in range(o_max + 1) if np.array_equal(rank[o: o + m - 1], w[1:])]
                    assert pos, "a window is not {g} + rank[o : o + m - 1] for an offset in range"
            partial.setdefault(m, []).append(dict(status=info["status"], eligible=info["eligible"], o_max=o_max))
            # must-fail: truncated windows (o over [0, half]) -> the m-genes check
            tr = AD.g6l_screen_range(B, S, [np.random.default_rng(9500 + t)], keep=None, min_seeds=1,
                                     _variant="truncated")
            (ts, _ti), = tr
            trunc_n += 1
            if ts is not None and any(len(w) != m for w in ts):
                trunc_caught += 1
        # no window: m = 80 -> 'unmatched' (R8)
        S = np.sort(r.choice(B.G, 80, replace=False))
        (s80, i80), = AD.g6l_screen_safe(B, S, [np.random.default_rng(1)], keep=60)
        assert s80 is None and i80["status"] == "unmatched" and AD.pool_status(B, S)["G6l"] == "no window"
    assert full_same == full_streams == n_toys * len(Ms) * 2, (full_same, full_streams)
    assert curves_same == curves_n == n_toys * len(Ms)
    assert sets_range_same == 3 * len(Ms) * 2
    assert f64_curves_differ >= 1, "the float64 variant was not caught by the curve check"
    assert trunc_caught >= 1, "the truncated-window variant was not caught by the m-genes check"
    return dict(full_range_streams_identical=f"{full_same} / {full_streams}",
                window_curves_identical=f"{curves_same} / {curves_n}",
                g6l_sets_range_equals_engine=f"{sets_range_same} / {3 * len(Ms) * 2}",
                float64_variant=dict(curves_differ=f"{f64_curves_differ} / {f64_n}",
                                     sets_differ=f"{f64_sets_differ} / {f64_n}"),
                truncated_variant_caught=f"{trunc_caught} / {trunc_n}",
                partial={m: [d["status"] for d in v] for m, v in partial.items()},
                partial_eligible={m: [d["eligible"] for d in v] for m, v in partial.items()})


# ================================================================================================================
# P12 / P13 extensions (R34)
# ================================================================================================================
KNOWN_ANSWER = "a36f360469243fefb9a36e2e67da0b5adc3f888d85195d597a3c9179bd85bec5"


@check("P12ext_R34_leg8_construction")
def t_p12ext():
    out = {}
    a = np.random.default_rng(np.random.SeedSequence([20260925, 990, 0, 8])).permuted(np.tile(np.arange(34),
                                                                                             (1000, 1)), axis=1)
    h = hashlib.sha256(a.astype(np.int64).tobytes()).hexdigest()
    assert h == KNOWN_ANSWER, h
    out["known_answer_sha256"] = h[:16] + "..."
    # equality with the row-wise loop at K = 5 and 1,000 (n = 7 and 34)
    for n in (7, 34):
        y = np.random.default_rng(n).standard_normal(n)
        for Kk in (5, 1000):
            ss = np.random.SeedSequence([20260925, 900, 12, n, Kk, 8])
            P1 = np.random.default_rng(ss).permuted(np.tile(y, (Kk, 1)), axis=1)
            g = np.random.default_rng(ss)
            P2 = np.stack([g.permutation(y) for _ in range(Kk)])
            assert np.array_equal(P1, P2), (n, Kk)
    out["loop_equality"] = "K 5 and 1,000; n 7 and 34"
    # the production null (leg 8) = an independent re-implementation, bit for bit; every row a permutation of y
    cm = ctx_of(toy_inputs(9600), "V-AAL", "aal")
    y = field(cm, np.random.default_rng(9601))
    seed_of, _ = keys(12, 1)
    p1 = AD.Pls1R2(cm, y, parcel_ids=cm.parcel_ids)
    lp = p1.level0_perm(1000, seed_of, return_maps=True)
    g = np.random.default_rng(seed_of("permutation"))
    indep = np.stack([g.permutation(y) for _ in range(1000)])
    assert np.array_equal(lp["maps"], indep)
    assert np.array_equal(lp["null"], p1.T_maps(indep))
    assert np.array_equal(np.sort(lp["maps"], axis=1), np.tile(np.sort(y), (1000, 1)))
    assert lp["seed_leg"] == "permutation" and lp["p"] == AD0.Pls1R2(cm, y, parcel_ids=cm.parcel_ids).level0_perm(
        1000, seed_of)["p"]  # = the e7029ed construction (A3's B0)
    # must-fail: a within-class permutation never moves a value across classes; the production draw does
    cls = cm.classes

    def moves_across(P):
        src = {v: cls[i] for i, v in enumerate(y)}
        return any(src[v] != cls[j] for row in P for j, v in enumerate(row))

    wc = np.empty_like(lp["maps"])
    g = np.random.default_rng(seed_of("permutation"))
    for k in range(len(wc)):
        wc[k] = y
        for cc in np.unique(cls):
            idx = np.flatnonzero(cls == cc)
            wc[k, idx] = g.permutation(y[idx])
    assert moves_across(lp["maps"]) and not moves_across(wc)
    out["within_class_variant_caught"] = True
    # the n <= 7 assertion (C3): fires on a 7-parcel map, not on 8
    c7 = ctx_of(toy_inputs(9602, sizes=(7,), G=120, names=SUB, n_brain=30), "toy-7", None)
    y7 = field(c7, np.random.default_rng(9603))
    out["n7_refused"] = raises(AD.FunctionalDefect, AD.Pls1R2(c7, y7, parcel_ids=c7.parcel_ids).level0_perm, 100,
                               seed_of)
    c8 = ctx_of(toy_inputs(9604, sizes=(8,), G=120, names=SUB, n_brain=30), "toy-8", None)
    y8 = field(c8, np.random.default_rng(9605))
    AD.Pls1R2(c8, y8, parcel_ids=c8.parcel_ids).level0_perm(100, seed_of)
    out["n8_runs"] = True
    # the driver records the construction's key
    legs = V.collect_legs(p1, {"site": 50, "permutation": 100}, seed_of)
    assert legs["level0"]["kind"] == "permutation (leg 8)"
    return out


def sel_rule_factory(Z, thr=0.35):
    """The synthetic 'paper's rule': genes whose Pearson r with the map exceeds thr (Z: z-scored genes, ddof 0)."""
    n = Z.shape[0]

    def select(v):
        vh = (v - v.mean()) / v.std()
        r = Z.T @ vh / n
        return np.flatnonzero(r > thr)

    def stat(v, genes):
        vh = (v - v.mean()) / v.std()
        return float((Z[:, genes].T @ vh / n).mean())
    return select, stat


@check("P13ext_R34_selected_list_keys")
def t_p13ext():
    c = ctx_of(toy_inputs(9700, sizes=(34,), names=("cortex",)), "dk-ctx", "dk")
    y = 0.8 * z(c.X[:, :6].mean(1)) + 0.6 * z(field(c, np.random.default_rng(9701)))
    Z = AD.zscore_genes(c.X)
    select, stat = sel_rule_factory(Z)
    spy: list = []
    seed_of, _ = keys(13, 1, spy=spy)
    sl = AD.SelectedList(c, y, select, stat, parcel_ids=c.parcel_ids)
    assert sl.selected.size > 0 and sl.T_obs == stat(y, select(y))
    Kp, Ks = 300, 200
    lp = sl.level0_perm(Kp, seed_of, return_maps=True)
    ss10, ss8 = seed_of("re-selection"), seed_of("permutation")
    spy.clear()
    lp = sl.level0_perm(Kp, seed_of, return_maps=True)
    want10 = np.random.default_rng(ss10).permuted(np.tile(y, (Kp, 1)), axis=1)
    want8 = np.random.default_rng(ss8).permuted(np.tile(y, (Kp, 1)), axis=1)
    assert np.array_equal(lp["maps"], want10) and not np.array_equal(lp["maps"], want8)
    g = np.random.default_rng(ss10)
    g.permuted(np.tile(y, (Kp, 1)), axis=1)
    assert lp["generator_state_after"] == g.bit_generator.state  # re-selection drew nothing from it
    n_empty = int(sum(select(mp).size == 0 for mp in lp["maps"]))
    assert np.array_equal(lp["null"], np.array([0.0 if select(mp).size == 0 else stat(mp, select(mp))
                                                for mp in lp["maps"]]))
    # site leg: site_null from SS(leg 0) / SS(leg 1)'s integer seeds, re-selection on each surrogate
    site = sl.site_leg(Ks, seed_of, return_surrogates=True)
    for leg, method in AD.SITE_LEGS:
        seed = int(np.random.default_rng(seed_of(leg)).integers(2 ** 31))
        sur, _ = site_null(y, c.D, c.classes, Ks, seed, method)
        assert site[leg]["seed"] == seed and np.array_equal(site[leg]["surrogates"], sur)
    # the seed spy over the whole driver: leg 8 never requested
    spy.clear()
    rec = V.claim_verdict_a1(sl, {"site": Ks, "permutation": Kp}, seed_of, two_sided=True)
    assert "permutation" not in spy and set(spy) == {"re-selection", "S1c", "S2c"}, sorted(set(spy))
    assert rec["legs"]["Level 0"]["kind"] == AD.SelectedList.LEVEL0_KIND and rec["survives"] is False
    # an empty list gives T = 0
    sl_hi = AD.SelectedList(c, y, sel_rule_factory(Z, thr=0.999)[0], stat, parcel_ids=c.parcel_ids)
    assert sl_hi.selected.size == 0 and sl_hi.T_obs == 0.0
    # must-fail: rules given (or holding) a generator, and a rule drawing from numpy's global state
    gen = np.random.default_rng(1)
    refusals = [raises(AD.FunctionalDefect, AD.SelectedList, c, y, lambda v, rng=None: select(v), stat,
                       parcel_ids=c.parcel_ids),
                raises(AD.FunctionalDefect, AD.SelectedList, c, y, lambda v: select(v)[: 1 + int(gen.integers(3))],
                       stat, parcel_ids=c.parcel_ids),
                raises(AD.FunctionalDefect, AD.SelectedList, c, y,
                       lambda v: select(v)[: 1 + int(np.random.random() * 3)], stat, parcel_ids=c.parcel_ids)]
    return dict(selected=int(sl.selected.size), T=sl.T_obs, level0_empty_lists=n_empty, spy=sorted(set(spy)),
                reading=rec["reading"], refusals=refusals)


# ================================================================================================================
# P8 / P14 extensions (R36)
# ================================================================================================================
class StubFull:
    """A full-verdict adapter stub returning given one-sided p's (assembly checks only; as tests/test_verdict.py)."""
    form = "set-vs-map"
    full_verdict = True
    n = 34

    def __init__(self, T, L0, site, species):
        self.T_obs, self._L0, self._site, self._sp = T, L0, site, species

    def level0_both(self):
        return dict(self._L0)

    def site_leg(self, K, seed_of, chunk=1000):
        return {k: dict(p=dict(v), floor=1 / 501, seed=1, info=dict(exact=False, n_null=500, n_patterns=float("inf"),
                                                                     floor=1 / 501)) for k, v in self._site.items()}

    def species_leg(self, K, seed_of, g6l=None):
        return dict(p={k: dict(v) for k, v in self._sp.items()}, status={k: "ok" for k in AD.SPECIES_LEGS},
                    floors={k: 1 / 201 for k in AD.SPECIES_LEGS}, g6l_info=dict(status="ok"), g6s_exact=False,
                    n_G6s=200, conditioned=True, pools={})

    def uninformative(self):
        return False, 0.3


def P(pp, pm):
    return {1: pp, -1: pm}


@check("P8P14ext_R36")
def t_r36():
    out = {}
    # (a) a G6l-unmatched claim (real adapter; S found by search on a module toy): no doubled p, one-sided p's reported
    c = ctx_of(toy_inputs(11, sizes=(34,), module=(25, 5.0), names=("cortex",)), "dk-ctx", "dk")
    y = field(c, np.random.default_rng(9801)) + 0.5 * z(c.X[:, :25].mean(1))
    found = None
    for S in (np.arange(25), np.arange(5, 20)):  # a strong module: c_S ~ .82, no window reaches it
        ad = AD.SetVsMap(c, y, S, parcel_ids=c.parcel_ids)
        legs = V.collect_legs(ad, {"site": 200, "species": 200}, keys(36, 1)[0])
        if legs["species"]["status"]["G6l"] == "unmatched" and legs["species"]["status"]["G1"] == "ok":
            found = (S, legs)
            break
    assert found is not None, "no G6l-unmatched set found on the toy"
    S, legs = found
    rec = V.assemble_verdict_a1(legs, two_sided=True)
    assert rec["d_star"] is None and rec["d_star_reason"] == V.NO_DSTAR and rec["survives"] is False
    assert rec["primary_status"] == "g6l unmatched"
    for leg, lr in rec["legs"].items():
        assert lr["p_reported"] is None, leg
        if leg not in ("G6l", "species"):
            assert lr["p_one_sided"] is not None and set(lr["p_one_sided"]) == {1, -1}, leg
            assert lr["p_per_leg_two_sided"] is not None
    assert rec["legs"]["G6l"]["p_one_sided"] is None and rec["p_conjunction"] is None
    out["a"] = dict(m=int(S.size), status=rec["primary_status"], d_star=rec["d_star"])
    # (b) a constructed two-cohort tie with opposite observed T signs
    tie = dict(L0=P(0.6, 0.6), site={"S1c": P(0.7, 0.7), "S2c": P(0.55, 0.55)},
               species={k: P(0.8, 0.8) for k in AD.SPECIES_LEGS})
    lt1 = V.collect_legs(StubFull(0.2, tie["L0"], tie["site"], tie["species"]), 500, None)
    lt2 = V.collect_legs(StubFull(-0.3, tie["L0"], tie["site"], tie["species"]), 500, None)
    tt = V.two_cohort_from_legs(lt1, lt2, two_sided=True)
    assert tt["survives"] is False and tt["p_conjunction"] == 1.0 and tt["d_star"] is None
    assert tt["d_star_reason"] == V.TWO_COHORT_TIE == "undefined: two-cohort tie, opposite observed T signs"
    assert tt["reading"].startswith("does not survive") and tt["primary_status"] == "ok"
    for lab in tt["map_labels"]:
        pm = tt["per_map"][lab]
        assert pm["survives"] is False and pm["p_conjunction"] is None
        assert all(lr["p_reported"] is None for lr in pm["legs"].values())
    # the same tie with the same T signs is not a two-cohort tie: d* = the common sign
    ts = V.two_cohort_from_legs(lt1, V.collect_legs(StubFull(0.4, tie["L0"], tie["site"], tie["species"]), 500,
                                                    None), two_sided=True)
    assert ts["d_star"] == 1
    # the impossible tie at M < .5 is refused (the fact behind the reading is asserted)
    low = dict(L0=P(0.3, 0.3), site={"S1c": P(0.3, 0.3), "S2c": P(0.3, 0.3)},
               species={k: P(0.3, 0.3) for k in AD.SPECIES_LEGS})
    out["b_impossible"] = raises(RuntimeError, V.two_cohort_from_legs,
                                 V.collect_legs(StubFull(0.2, low["L0"], low["site"], low["species"]), 500, None),
                                 V.collect_legs(StubFull(-0.2, low["L0"], low["site"], low["species"]), 500, None),
                                 two_sided=True)
    out["b"] = dict(survives=tt["survives"], p=tt["p_conjunction"], d_star=tt["d_star_reason"])
    # (c) a component claim at plant K = 30 permutations and surrogates: resolution-limited; does not pass
    cm = ctx_of(toy_inputs(9802), "V-AAL", "aal")
    yc = 0.9 * z(cm.X[:, :5].mean(1)) + 0.4 * z(field(cm, np.random.default_rng(9803)))
    p1 = AD.Pls1R2(cm, yc, parcel_ids=cm.parcel_ids)
    for two in (True, False):
        kw = dict(two_sided=True) if two else dict(two_sided=False, registered_direction=1)
        rc = V.claim_verdict_a1(p1, {"site": 30, "permutation": 30}, keys(36, 3)[0], **kw)
        assert rc["primary_status"] == "resolution-limited" and rc["passes_component_level"] is False
        assert rc["reading"].startswith("does not pass") and rc["resolution"]["limited"] is True
        assert rc["legs"]["Level 0"]["floor_one_sided"] == 1 / 31
    out["c"] = dict(status=rc["primary_status"], reading=rc["reading"])
    # (d) descriptor reported p's at d* = 2 p(d*) (two-sided) / p(d) (one-sided)
    dk = ctx_of(toy_inputs(9804, sizes=(34,), names=("cortex",)), "dk-ctx", "dk")
    S = np.arange(30, 55)
    yd = 0.7 * z(dk.score(S)) + 0.7 * z(field(dk, np.random.default_rng(9805)))
    ad = AD.DecodedList(dk, yd, S, parcel_ids=dk.parcel_ids)
    so, _ = keys(36, 4)
    g3 = lambda: np.random.SeedSequence(entropy=[20260925, 900, 36, 4, 0, 3], spawn_key=(0,))  # noqa: E731
    vr = V.claim_verdict_a1(ad, {"site": 200, "species": 200}, so, two_sided=True)
    t = np.linspace(0, 1, 8)
    rng = np.random.default_rng(9806)
    traj = pd.DataFrame(rng.normal(5, 1, (dk.G, 1)) + rng.normal(0, 1, (dk.G, 1)) * t, index=list(dk.U.genes),
                        columns=[f"b{k}" for k in range(8)])
    n_checked = 0
    for two, d in ((True, vr["d_star"]), (False, -1)):
        desc = DS.descriptor_pass(ad, so, g3, K_sets=60, K_surr=60, K_j1_sets=30, traj=traj, direction=d,
                                  two_sided=two)
        for rec_ in (*desc["legs"].values(), desc["level2"], desc["J1"], desc["naive_joint"]):
            p = rec_.get("p")
            if p is None or d is None:
                assert rec_["p_reported"] is None
                continue
            assert rec_["p_reported"] == (min(1.0, 2.0 * p[d]) if two else p[d])
            if two:
                assert rec_["p_per_leg_two_sided"] == min(1.0, 2.0 * min(p[1], p[-1]))
            n_checked += 1
    # (d') asdg-skeptic WP1 review B5: legs favouring the direction OPPOSITE the claim's d* are reported at d*,
    # min(1, 2 p(d*)), never 2 min_d p(d) (the claim's own d*, and the same legs read for a claim of the other d*)
    n_opp = {}
    for d in (vr["d_star"], -vr["d_star"]):
        desc = DS.descriptor_pass(ad, so, g3, K_sets=60, K_surr=60, K_j1_sets=30, traj=traj, direction=d,
                                  two_sided=True)
        n_opp[d] = 0
        for rec_ in (*desc["legs"].values(), desc["level2"], desc["J1"], desc["naive_joint"]):
            p = rec_.get("p")
            if p is None:
                continue
            assert rec_["p_reported"] == min(1.0, 2.0 * p[d]), (rec_.get("leg"), d)
            if p[-d] < p[d]:
                n_opp[d] += 1
                assert rec_["p_reported"] == min(1.0, 2.0 * p[d]) != rec_["p_per_leg_two_sided"]
    assert n_opp[vr["d_star"]] + n_opp[-vr["d_star"]] >= 1 and n_opp[-vr["d_star"]] >= 1
    out["d"] = dict(d_star=vr["d_star"], descriptor_legs_checked=n_checked,
                    legs_favouring_the_other_direction={str(k): v for k, v in n_opp.items()})
    return out


class StubStatus(StubFull):
    """StubFull whose species legs `nop` have no p and the given statuses (G6l unmatched / degenerate; R8)."""

    def __init__(self, T, L0, site, species, status: dict, nop=()):
        super().__init__(T, L0, site, species)
        self._status, self._nop = status, tuple(nop)

    def species_leg(self, K, seed_of, g6l=None):
        rec = super().species_leg(K, seed_of, g6l)
        rec["status"].update(self._status)
        for k in self._nop:
            rec["p"][k] = None
        rec["g6l_info"] = dict(status=rec["status"]["G6l"])
        return rec


@check("P14ext_B2_two_cohort_without_claim_dstar")
def t_b2():
    """asdg-skeptic WP1 review B2: a two-sided two-cohort claim where one map has no species p (G6l unmatched /
    degenerate, R8): R36 (a) at claim level - no exception, d* undefined, each map's one-sided p's reported, no
    doubled p, neither map nor the claim survives; one-sided: d* = the registered direction, no exception."""
    out = {}
    strong = dict(L0=P(1e-6, 1 - 1e-6), site={"S1c": P(0.002, 0.998), "S2c": P(0.002, 0.998)},
                  species={k: P(0.004, 0.996) for k in AD.SPECIES_LEGS})
    la = V.collect_legs(StubFull(0.5, strong["L0"], strong["site"], strong["species"]), 500, None)
    alone = V.assemble_verdict_a1(la, two_sided=True)
    assert alone["primary_status"] == "ok" and alone["survives"] is True   # map a alone survives
    cases = (("G6l unmatched", {"G6l": "unmatched"}, ("G6l",), "g6l unmatched"),
             ("G6l degenerate", {"G6l": "degenerate"}, ("G6l",), "g6l degenerate"),
             ("R8 (G3m pool < m)", {"G3m": AD.NOT_COMPUTABLE}, ("G3m",), V.R8_NOT_AUDITABLE))
    for name, status, nop, want in cases:
        lb = V.collect_legs(StubStatus(0.4, strong["L0"], strong["site"], strong["species"], status, nop), 500, None)
        for labels, pair in ((("a", "b"), (la, lb)), (("b", "a"), (lb, la))):
            tc = V.two_cohort_from_legs(*pair, two_sided=True, map_labels=labels)   # no exception (B2)
            assert tc["d_star"] is None and tc["d_star_reason"] == V.NO_DSTAR, tc["d_star_reason"]
            assert tc["survives"] is False and tc["p_conjunction"] is None
            assert tc["reading"] == V.TWO_COHORT_NO_DSTAR_READING and tc["primary_status"] == want, tc["primary_status"]
            for lab in labels:
                pm = tc["per_map"][lab]
                assert pm["survives"] is False and pm["p_conjunction"] is None and pm["d_star"] is None
                for leg, lr in pm["legs"].items():
                    assert lr["p_reported"] is None, (lab, leg)
                    if lr["p_one_sided"] is not None:
                        assert set(lr["p_one_sided"]) == {1, -1} and lr["p_per_leg_two_sided"] is not None
            pa = tc["per_map"]["a"]
            assert pa["primary_status"] == "ok" and pa["reading"] == V.TWO_COHORT_NO_DSTAR_READING
            assert pa["legs"]["species"]["p_one_sided"] == {1: 0.004, -1: 0.996}
        t1 = V.two_cohort_from_legs(la, lb, two_sided=False, registered_direction=1, map_labels=("a", "b"))
        assert t1["d_star"] == 1 and t1["survives"] is False and t1["per_map"]["a"]["survives"] is True
        assert t1["per_map"]["b"]["primary_status"] == want and t1["primary_status"] == want
        out[name] = dict(two_sided=tc["primary_status"], one_sided_p=t1["p_conjunction"])
    # synthetic data: map b = (a)'s G6l-unmatched construction (module toy, strong module S), map a on the same class
    c = ctx_of(toy_inputs(11, sizes=(34,), module=(25, 5.0), names=("cortex",)), "dk-ctx", "dk")
    yb = field(c, np.random.default_rng(9801)) + 0.5 * z(c.X[:, :25].mean(1))
    lb = None
    for S in (np.arange(25), np.arange(5, 20)):
        legs = V.collect_legs(AD.SetVsMap(c, yb, S, parcel_ids=c.parcel_ids), {"site": 200, "species": 200},
                              keys(36, 1)[0])
        if legs["species"]["status"]["G6l"] == "unmatched" and legs["species"]["status"]["G1"] == "ok":
            lb = legs
            break
    assert lb is not None, "no G6l-unmatched set found on the toy"
    Sa = np.arange(100, 125)
    ya = 0.8 * z(c.score(Sa)) + 0.6 * z(field(c, np.random.default_rng(9811)))
    la2 = V.collect_legs(AD.SetVsMap(c, ya, Sa, parcel_ids=c.parcel_ids), {"site": 200, "species": 200},
                         keys(36, 11)[0])
    assert la2["species"]["status"]["G6l"] == "ok", "precondition: map a's G6l is computed"
    tc = V.two_cohort_from_legs(la2, lb, two_sided=True)
    assert tc["d_star"] is None and tc["survives"] is False and tc["primary_status"] == "g6l unmatched"
    assert all(tc["per_map"][k]["survives"] is False for k in tc["map_labels"])
    out["synthetic"] = dict(primary=tc["primary_status"], d_star_reason=tc["d_star_reason"],
                            map_a_alone=V.assemble_verdict_a1(la2, two_sided=True)["primary_status"])
    return out


# ----------------------------------------------------------------------------------------------------------------
# asdg-skeptic WP1 review C7 / C8 (synthetic files only)
# ----------------------------------------------------------------------------------------------------------------
def _write_atlas(d: Path, atlas: str, rows: list, G: int, seed: int) -> tuple[pd.DataFrame, list]:
    """A synthetic <atlas>_expr.csv.gz / _atlas_info.csv / _centroids.csv in d. rows: (id, hemisphere, structure)."""
    rng = np.random.default_rng(seed)
    ids = [r[0] for r in rows]
    genes = [f"SYNG{j:04d}" for j in range(G)]
    X = rng.standard_normal((len(ids), G)) * rng.uniform(0.2, 3.0, G) + rng.uniform(-2, 2, G)
    expr = pd.DataFrame(X, index=pd.Index(ids, name="id"), columns=genes)
    expr.to_csv(d / f"{atlas}_expr.csv.gz", compression="gzip")
    pd.DataFrame({"id": ids, "label": [f"syn{i}" for i in ids], "hemisphere": [r[1] for r in rows],
                  "structure": [r[2] for r in rows]}).to_csv(d / f"{atlas}_atlas_info.csv", index=False)
    xyz = rng.uniform(-70, 70, (len(ids), 3))
    pd.DataFrame({"id": ids, "x": xyz[:, 0], "y": xyz[:, 1], "z": xyz[:, 2]}).to_csv(d / f"{atlas}_centroids.csv",
                                                                                    index=False)
    return expr, genes


def _clear_a3_caches():
    for f in (A._primary, A.atlas_info, A.verify_matrix):
        f.cache_clear()


@check("C7_class_contexts_VDK_subcortex_and_MIST64_synthetic")
def t_c7():
    import a1_audit.launch as LA
    out = {}
    d = SCRATCH / "c7_ahba"
    d.mkdir(parents=True, exist_ok=True)
    G = 80
    dk_rows = ([(1000 + i, "L", "cortex") for i in range(1, 35)] + [(1034 + i, "L", "subcortex/brainstem")
                                                                     for i in range(1, 8)]
               + [(1042, "B", "subcortex/brainstem")] + [(1042 + i, "R", "cortex") for i in range(1, 6)])
    mi_rows = ([(i, "L", "cortex") for i in range(1, 34)] + [(33 + i, "B" if i == 1 else "L", "subcortex")
                                                             for i in range(1, 6)]
               + [(38 + i, "L", "cerebellum") for i in range(1, 9)] + [(46 + i, "R", "cortex") for i in range(1, 19)])
    dk_expr, genes = _write_atlas(d, "dk", dk_rows, G, 7001)
    mi_expr, _ = _write_atlas(d, "mist64", mi_rows, G, 7002)
    js = d / "mist64_classes.json"

    def write_json(parcels):
        js.write_text(json.dumps({"parcels": parcels}), encoding="utf-8", newline="\n")
        assert json.loads(js.read_text(encoding="utf-8"))["parcels"] == parcels
    good = [{"roi": r[0], "tissue_class": r[2], "primary": r[1] in ("L", "B")} for r in mi_rows]
    write_json(good)
    rt = {a: hashlib.sha256(pd.util.hash_pandas_object(pd.read_csv(d / f"{a}_expr.csv.gz", index_col=0,
                                                                   float_precision="round_trip"),
                                                       index=True).to_numpy().tobytes()).hexdigest()
          for a in ("dk", "mist64")}
    brain = genes[:20]
    saved = dict(ahba_p=e3_plants.AHBA, ahba_a=A.AHBA, sha=dict(A.MATRIX_SHA), n=A.N_GENES, pin=LA.AHBA_MATRIX,
                 js=AD.MIST64_CLASSES_JSON, bb=e3_plants.brain_background)
    try:
        e3_plants.AHBA, A.AHBA = d, d
        A.MATRIX_SHA["dk"], A.N_GENES = rt["dk"], G
        LA.AHBA_MATRIX = tuple((k, rt["mist64"] if k == "mist64" else v) for k, v in saved["pin"])
        AD.MIST64_CLASSES_JSON = js
        e3_plants.brain_background = A.symbols_background(brain)
        _clear_a3_caches()
        assert "V-DK-subcortex" not in A.CLASS_DEFS and "MIST64" not in A.CLASS_DEFS   # a3_port's blocks untouched
        sub = AD.build_context_checked("V-DK-subcortex")
        want_ids = [1034 + i for i in range(1, 8)]
        assert sub.name == "V-DK-subcortex" and [int(i) for i in sub.parcel_ids] == want_ids
        assert sub.report["class_counts"] == {"subcortex/brainstem": 7} and sub.report["n_midline"] == 0
        assert float(np.max(np.abs(sub.X - dk_expr.loc[want_ids].to_numpy()))) <= 1e-12
        assert sub.single_class() and sub.B.G == G and "a1_class_rule" in sub.report
        mi = AD.build_context_checked("MIST64")
        prim = [r[0] for r in mi_rows if r[1] in ("L", "B")]
        assert mi.name == "MIST64" and [int(i) for i in mi.parcel_ids] == prim and mi.n == 46
        assert mi.report["class_counts"] == {"cerebellum": 8, "cortex": 33, "subcortex/brainstem": 5}
        assert mi.report["matrix_sha256"] == rt["mist64"]
        assert float(np.max(np.abs(mi.X - mi_expr.loc[prim].to_numpy()))) <= 1e-12
        part = AD.build_context_checked("MIST64", parcel_ids=prim[:40])
        assert part.n == 40
        files = {Path(r["file"]).name for r in LA.first_use_records()}
        assert {"dk_expr.csv.gz", "mist64_expr.csv.gz"} <= files   # R35's first-use check ran on both
        # the synthetic contexts run the verdict legs (a 7-parcel single class: exact site leg, as P9)
        y = field(sub, np.random.default_rng(7003))
        lg = V.collect_legs(AD.SetVsMap(sub, y, np.arange(30, 55), parcel_ids=sub.parcel_ids),
                            {"site": 10000, "species": 100}, keys(70, 0)[0])
        assert lg["site"]["S1c"]["info"]["exact"] is True and lg["site"]["S1c"]["info"]["n_null"] == 5040
        # must-fail: a JSON tissue class changed, a JSON primary parcel missing, a wrong L7 pin
        bad = [dict(p) for p in good]
        bad[0]["tissue_class"] = "cerebellum"
        write_json(bad)
        out["json_class_changed"] = raises(AssertionError, AD.build_context_checked, "MIST64")
        write_json([p for p in good if p["roi"] != 2])
        out["json_parcel_missing"] = raises(AssertionError, AD.build_context_checked, "MIST64")
        write_json(good)
        LA.AHBA_MATRIX = tuple((k, "0" * 64 if k == "mist64" else v) for k, v in saved["pin"])
        out["wrong_L7_pin"] = raises(AssertionError, AD.build_context_checked, "MIST64")
        out["unknown_class"] = raises(KeyError, AD.build_context_checked, "V-NOPE")
        out.update(v_dk_subcortex=dict(n=sub.n, classes=sub.report["class_counts"]),
                   mist64=dict(n=mi.n, classes=mi.report["class_counts"]))
    finally:
        e3_plants.AHBA, A.AHBA = saved["ahba_p"], saved["ahba_a"]
        A.MATRIX_SHA.clear()
        A.MATRIX_SHA.update(saved["sha"])
        A.N_GENES, LA.AHBA_MATRIX, AD.MIST64_CLASSES_JSON = saved["n"], saved["pin"], saved["js"]
        e3_plants.brain_background = saved["bb"]
        _clear_a3_caches()
    assert A.AHBA == NO_DATA and A.N_GENES == 15633
    return out


@check("C8_analysis_parcels_counts_absent_class_parcels")
def t_c8():
    cls_ids = np.arange(101, 114)
    ids = cls_ids[:10]
    y = np.random.default_rng(7101).standard_normal(ids.size)
    y[2] = np.nan
    counts = {int(i): 2 for i in cls_ids}
    counts[106] = 0
    old = AD.analysis_parcels(y, counts, parcel_ids=ids)
    new = AD.analysis_parcels(y, counts, parcel_ids=ids, class_parcel_ids=cls_ids)
    assert old["n_dropped"] == 2 and "n_class" not in old   # the map's own parcels as the base (unchanged)
    assert new["parcel_ids"] == old["parcel_ids"] and new["n_kept"] == 8
    assert new["n_class"] == 13 and new["n_absent_from_map"] == 3 and new["dropped_absent_from_map"] == [111, 112, 113]
    assert new["n_dropped"] == 5 and new["n_kept"] + new["n_dropped"] == new["n_class"]
    r = raises(ValueError, AD.analysis_parcels, y, {**counts, 999: 1}, parcel_ids=np.r_[ids[:-1], 999],
               class_parcel_ids=cls_ids)
    assert "not parcels of the class" in r
    return dict(n_class=new["n_class"], n_kept=new["n_kept"], n_dropped=new["n_dropped"],
                absent=new["dropped_absent_from_map"], outside_refused=r)


def main() -> int:
    t0 = time.time()
    print(f"RUN_PLAN_amend_1 plants: scratch {SCRATCH}; toys {ARGS.toys}", flush=True)
    for run in CHECKS:
        run()
    out = SCRATCH / "test_amend1_results.json"
    out.write_text(json.dumps(A.jsonable(dict(results=RESULTS, failed=FAILED, seconds=round(time.time() - t0, 1))),
                              indent=1) + "\n", encoding="utf-8", newline="\n")
    back = json.loads(out.read_text(encoding="utf-8"))
    assert back["failed"] == FAILED
    print(f"{len(CHECKS) - len(FAILED)} of {len(CHECKS)} checks passed ({time.time() - t0:.0f}s); results {out}",
          flush=True)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
