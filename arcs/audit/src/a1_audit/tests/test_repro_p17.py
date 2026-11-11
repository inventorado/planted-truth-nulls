"""P17 of arcs/audit/RUN_PLAN.md v3.1 (FROZEN; §7 row P17): the reproduction functionals on SYNTHETIC data.

    cd arcs/audit/src
    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_repro_p17 [--scratch DIR] [--require-docker]

P17: "bicor (R13; closed form, invariances, fallback, WGCNA via Docker if built); |z|-weighted rho; rank-biserial;
per-donor recipe t (R14); Fisher + BH over-representation analysis, both sidednesses (R22); the RLM equals a direct
iteratively reweighted Huber fit (R28); the overlap test against a hand-computed hypergeometric tail (R30)".
R28's production RLM is forms.rlm_t (the forms worker's; repro.rlm_log2fc_t delegates): it is checked here against
statsmodels and against two direct IRLS fits (forms.irls_huber_direct and repro.huber_irls, written independently).

Every functional of a1_audit/repro.py is checked against a closed form, a direct computation or a hand computation
(exact rationals: fractions.Fraction, square roots in decimal at 60 digits), each with its tolerance stated in TOL
below, fixed before any result was seen. Each check carries a must-differ variant (a plausible wrong implementation the
check would catch), so no check passes vacuously (rule 8).

Docker-dependent checks (WGCNA::bicor, R's fisher.test, GeneOverlap, the R17 image exercise, the image record) run in
the image built by a1_audit/rbuild/docker_r.py; if it is not available they print "SKIP <check>: not built: <why>",
never pass, and are listed in the summary. --require-docker turns a skip into a failure.

Synthetic data only: nothing under E:\\data, no carrier, map or supplement is read; the R image gets a scratch
directory only, with no network. Seeds: SeedSequence([20260925, 900, 17, case, item]) (plant 17; target 900 does not
exist; RUN_PLAN §7). Exits non-zero on any failure. Prints ASCII only.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import struct
import sys
import tempfile
import time
import traceback
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
for _p in (ROOT / "src", ROOT / "arcs" / "audit" / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

ap = argparse.ArgumentParser()
ap.add_argument("--scratch", default=None, help="scratch directory (default: a new temporary directory)")
ap.add_argument("--require-docker", action="store_true", help="a Docker check that cannot run is a FAILURE")
ARGS, _ = ap.parse_known_args()
SCRATCH = Path(ARGS.scratch or tempfile.mkdtemp(prefix="a1_p17_")).resolve()
SCRATCH.mkdir(parents=True, exist_ok=True)

import a1_audit.a3_port as A  # noqa: E402
import a1_audit.repro as R  # noqa: E402
from a1_audit.rbuild import docker_r as DR  # noqa: E402

getcontext().prec = 60

# tolerances (fixed before any run; absolute unless "rel")
TOL = dict(
    closed_form=1e-14,        # float functional vs an exact-rational / 60-digit evaluation of the same formula
    invariance=1e-12,         # affine / permutation invariances (float re-evaluation of a transformed input)
    vector_loop=1e-14,        # vectorised vs scalar loop of the same float formula
    sum_order=1e-13,          # a Python-loop sum vs a matrix product over up to 200 terms (summation order differs)
    scipy_rel=1e-12,          # vs scipy / statsmodels re-computations (relative)
    p_hand_rel=1e-10,         # Fisher / hypergeometric p vs exact rationals (relative; + 1e-300 absolute)
    wgcna=1e-10,              # R13: "agreement to 1e-10" with WGCNA::bicor
    r_p_rel=1e-10,            # R's fisher.test / GeneOverlap p vs ours (relative)
    r_or_rel=1e-3,            # R's conditional-MLE odds ratio (uniroot, tol ~ 1.2e-4) vs scipy's (relative)
    r_score=1e-12,            # R17 exercise: R's weighted score and Spearman rho vs ours
    rlm_same_rule_rel=1e-10,  # R28: statsmodels RLM vs the direct IRLS under the same stopping rule (relative)
    rlm_fixed_point_rel=1e-9,  # R28: both iterated to a fixed point (tol 1e-13) (relative)
    must_differ=1e-6,         # a must-differ variant must move the checked value by more than this
)

RESULTS: dict = {}
FAILED: list = []
SKIPPED: list = []
CHECKS: list = []


def ss(case: int, item: int = 0) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([20260925, 900, 17, case, item]))


def check(name, docker: bool = False):
    def deco(fn):
        def run():
            t0 = time.time()
            if docker:
                try:
                    DR.image_status()
                except DR.NotBuilt as e:
                    why = f"not built: {e}"
                    if ARGS.require_docker:
                        FAILED.append(name)
                        RESULTS[name] = dict(result="FAIL", error=why)
                        print(f"FAIL {name}: {why} (--require-docker)", flush=True)
                    else:
                        SKIPPED.append(name)
                        RESULTS[name] = dict(result="SKIP", reason=why)
                        print(f"SKIP {name}: {why}", flush=True)
                    return
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
        return type(e).__name__
    raise AssertionError(f"{getattr(f, '__name__', f)} did not raise {exc.__name__}")


def rel(a: float, b: float) -> float:
    a, b = float(a), float(b)
    if a == b:
        return 0.0
    return abs(a - b) / max(abs(a), abs(b), 1e-300)


def dec(fr: Fraction) -> Decimal:
    return Decimal(fr.numerator) / Decimal(fr.denominator)


def run_record(script: str, work: Path, inputs, outputs) -> dict:
    """R17: "Inputs and outputs are hashed; the image digest and the session info are recorded" (per R run)."""
    return dict(image=DR.image_status()["image"]["id"], script=script, script_sha256=DR.sha256_file(DR.R_DIR / script),
                inputs_sha256={n: DR.sha256_file(work / n) for n in inputs},
                outputs_sha256={n: DR.sha256_file(work / n) for n in outputs})


# ----------------------------------------------------------------------------------------------------------------
# exact references
# ----------------------------------------------------------------------------------------------------------------
def _median_frac(vals: list) -> Fraction:
    s = sorted(vals)
    n = len(s)
    return (s[(n - 1) // 2] + s[n // 2]) / 2


def bicor_exact(x, y) -> Decimal:
    """bicor from first principles in exact rationals (60-digit square root): R13's formula."""
    def prep(v):
        F = [Fraction(float(a)) for a in v]
        med = _median_frac(F)
        mad = _median_frac([abs(a - med) for a in F])
        if mad == 0:
            mu = sum(F, Fraction(0)) / len(F)
            return [a - mu for a in F]
        out = []
        for a in F:
            u = (a - med) / (9 * mad)
            w = (1 - u * u) ** 2 if abs(u) < 1 else Fraction(0)
            out.append((a - med) * w)
        return out
    cx, cy = prep(x), prep(y)
    num = sum((a * b for a, b in zip(cx, cy)), Fraction(0))
    qx = sum((a * a for a in cx), Fraction(0))
    qy = sum((b * b for b in cy), Fraction(0))
    return dec(num) / (dec(qx) * dec(qy)).sqrt()


def spearman_formula_exact(a, b) -> Fraction:
    """rho = 1 - 6 sum d^2 / (n (n^2 - 1)) for untied vectors (exact)."""
    ra = stats.rankdata(a)
    rb = stats.rankdata(b)
    assert len(set(ra)) == len(ra) and len(set(rb)) == len(rb)
    n = len(ra)
    d2 = sum(int(x - y) ** 2 for x, y in zip(ra, rb))
    return 1 - Fraction(6 * d2, n * (n * n - 1))


def mixed_vector(rng, n: int, kind: int) -> np.ndarray:
    if kind == 0:
        return rng.normal(size=n)
    if kind == 1:
        return rng.standard_t(2, size=n)
    if kind == 2:
        return rng.lognormal(size=n)
    if kind == 3:
        v = rng.normal(size=n)
        k = rng.choice(n, size=min(2, n), replace=False)
        v[k] = np.sign(rng.normal(size=k.size)) * rng.uniform(30, 80, size=k.size)
        return v
    return np.round(rng.normal(size=n) * 3) / 3  # ties


# ================================================================================================================
# R13: bicor
# ================================================================================================================
@check("P17.bicor.closed_form")
def t_bicor_closed_form():
    x, y = [1, 2, 3, 4, 5], [1, 2, 3, 4, 100]
    # by hand: med 3, MAD 1 in both; u = d / 9; y's 100 has u = 97/9 >= 1, weight 0
    w1, w2 = (1 - Fraction(1, 81)) ** 2, (1 - Fraction(4, 81)) ** 2
    cx = [-2 * w2, -w1, 0, w1, 2 * w2]
    cy = [-2 * w2, -w1, 0, w1, 0]
    num = sum((a * b for a, b in zip(cx, cy)), Fraction(0))
    hand = dec(num) / (dec(sum(a * a for a in cx)) * dec(sum(b * b for b in cy))).sqrt()
    ours = R.bicor(x, y)
    d0 = abs(Decimal(ours) - hand)
    assert d0 <= Decimal(TOL["closed_form"]), (ours, hand)
    # 60 random small vectors: the float functional vs the exact-rational evaluation of R13's formula
    rng = ss(1, 0)
    worst = Decimal(0)
    for i in range(60):
        n = int(rng.integers(5, 13))
        a, b = mixed_vector(rng, n, i % 5), mixed_vector(rng, n, (i + 2) % 5)
        worst = max(worst, abs(Decimal(R.bicor(a, b)) - bicor_exact(a, b)))
    assert worst <= Decimal(TOL["closed_form"]), worst
    # self and negation
    assert abs(R.bicor(x, x) - 1.0) <= TOL["closed_form"] and abs(R.bicor(x, [-v for v in x]) + 1.0) <= TOL[
        "closed_form"]
    # must differ: Pearson, and the MAD scaled by R's mad() constant 1.4826 (R13 pins the raw MAD)
    pearson = float(np.corrcoef(x, y)[0, 1])
    a_s, _ = R.bicor_prepare(x, _mad_constant=1.4826)
    b_s, _ = R.bicor_prepare(y, _mad_constant=1.4826)
    scaled = float(a_s @ b_s)
    # (first run: a 0.1 threshold for Pearson was arbitrary and failed at 0.058; every must-differ threshold is now
    # 1e-6, eight orders above the check's tolerance, which is all a must-differ variant has to show)
    assert abs(pearson - ours) > TOL["must_differ"] and abs(scaled - ours) > TOL["must_differ"], (pearson, scaled, ours)
    return dict(hand_case=dict(ours=ours, hand=str(hand)[:22], abs_diff=float(d0)), random_60_max_abs_diff=float(worst),
                must_differ=dict(pearson=pearson, scaled_mad=scaled))


@check("P17.bicor.invariances")
def t_bicor_invariances():
    rng = ss(2, 0)
    worst = dict(sym=0.0, affine_pos=0.0, affine_neg=0.0, self=0.0, perm=0.0, bound=0.0)
    for i in range(200):
        x, y = mixed_vector(rng, 34, i % 5), mixed_vector(rng, 34, (i + 1) % 5)
        b0 = R.bicor(x, y)
        a, c = float(rng.uniform(0.1, 10)), float(rng.normal() * 5)
        perm = rng.permutation(34)
        worst["sym"] = max(worst["sym"], abs(b0 - R.bicor(y, x)))
        worst["affine_pos"] = max(worst["affine_pos"], abs(b0 - R.bicor(a * x + c, y)))
        worst["affine_neg"] = max(worst["affine_neg"], abs(-b0 - R.bicor(-a * x + c, y)))
        worst["self"] = max(worst["self"], abs(1.0 - R.bicor(x, x)))
        worst["perm"] = max(worst["perm"], abs(b0 - R.bicor(x[perm], y[perm])))
        worst["bound"] = max(worst["bound"], abs(b0) - 1.0)
    assert worst["bound"] <= TOL["closed_form"]
    assert all(worst[k] <= TOL["invariance"] for k in ("sym", "affine_pos", "affine_neg", "self", "perm")), worst
    # an outlier (|u| >= 1) moved further out on its side: median and MAD unchanged, weight 0 -> bit-identical bicor
    x = rng.normal(size=34)
    y = rng.normal(size=34)
    med = np.median(x)
    mad = np.median(np.abs(x - med))
    x1, x2 = x.copy(), x.copy()
    k = int(np.argmax(x))
    x1[k], x2[k] = med + 20 * mad, med + 55 * mad
    same = R.bicor(x1, y) == R.bicor(x2, y)
    pear_move = abs(float(np.corrcoef(x1, y)[0, 1] - np.corrcoef(x2, y)[0, 1]))
    assert same and pear_move > 1e-3, (same, pear_move)
    return dict(max_abs=worst, outlier_move_bit_identical=bool(same), must_differ_pearson_move=pear_move)


@check("P17.bicor.fallback")
def t_bicor_fallback():
    rng = ss(3, 0)
    x = np.array([0, 0, 0, 0, 0, 1, 2, 3, -1], dtype=float)  # median 0, MAD 0
    y = rng.normal(size=9)
    ax, mode_x = R.bicor_prepare(x)
    _, mode_y = R.bicor_prepare(y)
    assert mode_x == "pearson-fallback" and mode_y == "biweight"
    ours = R.bicor(x, y)
    hand = bicor_exact(x, y)  # exact reference: MAD-0 column mean-centred, the other biweight
    d1 = abs(Decimal(ours) - hand)
    assert d1 <= Decimal(TOL["closed_form"]), (ours, hand)
    # both columns MAD 0 -> plain Pearson
    z = np.array([5, 5, 5, 5, 5, 2, 7, 1, 9], dtype=float)
    both = R.bicor(x, z)
    pear = float(np.corrcoef(x, z)[0, 1])
    assert abs(both - pear) <= TOL["closed_form"], (both, pear)
    # must differ: the MAD-0 column NOT falling back (median-centred, unweighted) gives another value
    c = x - np.median(x)
    nofb = float((c / np.linalg.norm(c)) @ R.bicor_prepare(y)[0])
    assert abs(nofb - ours) > 1e-6
    refused = [raises(ValueError, R.bicor, np.ones(9), y),
               raises(NotImplementedError, R.bicor, x, y, max_p_outliers=0.05),
               raises(NotImplementedError, R.bicor, x, y, pearson_fallback="none")]
    return dict(fallback_vs_exact=float(d1), both_mad0_vs_pearson=abs(both - pear), must_differ_no_fallback=nofb,
                refused=refused)


@check("P17.bicor.vectorised_and_mean")
def t_bicor_vector():
    rng = ss(4, 0)
    X = rng.normal(size=(34, 500))
    X[:, 7] = np.r_[np.zeros(20), rng.normal(size=14)]          # MAD 0 columns
    X[:, 99] = np.r_[np.full(18, 2.0), rng.normal(size=16)]
    X[:, 321] = np.r_[np.full(25, -1.0), rng.normal(size=9)]
    X[:, 5] = mixed_vector(rng, 34, 3)
    y = mixed_vector(rng, 34, 1)
    v = R.bicor_columns(y, X)
    loop = np.array([R.bicor(y, X[:, g]) for g in range(500)])
    d = float(np.max(np.abs(v - loop)))
    mb = R.mean_bicor(y, X)
    sub = R.mean_bicor(y, X, genes=np.arange(0, 500, 7))
    assert d <= TOL["vector_loop"] and abs(mb["mean_bicor"] - loop.mean()) <= TOL["vector_loop"]
    assert abs(sub["mean_bicor"] - loop[::7].mean()) <= TOL["vector_loop"]
    assert mb["n_pearson_fallback_columns"] == 3 and mb["n_genes"] == 500
    return dict(max_abs_vector_vs_loop=d, mean_bicor=mb["mean_bicor"], fallback_columns=mb["n_pearson_fallback_columns"])


def _wgcna_pairs():
    rng = ss(5, 0)
    pairs = []
    for i in range(1000):  # R13: 1,000 synthetic vector pairs
        n = 34 if i < 600 else int((8, 15, 50, 100, 200)[i % 5])
        pairs.append((mixed_vector(rng, n, i % 5), mixed_vector(rng, n, (i // 5) % 5)))
    extra = []
    for i in range(20):  # MAD-0 columns (fallback), reported beside the 1,000
        n = 34
        a = np.r_[np.full(20, float(i % 3)), rng.normal(size=14)]
        b = mixed_vector(rng, n, i % 5) if i % 2 else np.r_[np.full(19, 1.0), rng.normal(size=15)]
        extra.append((rng.permutation(a), b))
    return pairs, extra


def _write_pairs(path: Path, pairs) -> None:
    with open(path, "wb") as fh:
        fh.write(struct.pack("<i", len(pairs)))
        fh.write(struct.pack(f"<{len(pairs)}i", *[len(x) for x, _ in pairs]))
        for x, y in pairs:
            fh.write(np.asarray(x, dtype="<f8").tobytes())
            fh.write(np.asarray(y, dtype="<f8").tobytes())


@check("P17.bicor.wgcna_docker", docker=True)
def t_bicor_wgcna():
    pairs, extra = _wgcna_pairs()
    work = SCRATCH / "wgcna"
    work.mkdir(exist_ok=True)
    _write_pairs(work / "pairs.bin", pairs + extra)
    r = DR.run_r("wgcna_bicor.R", ["/work/pairs.bin", "/work/out.bin", "/work/meta.txt"], work)
    if r.returncode != 0:
        raise RuntimeError(f"Rscript exited {r.returncode}: {r.stderr.decode('ascii', 'replace')[-400:]}")
    out = np.fromfile(work / "out.bin", dtype="<f8").reshape(-1, 2)
    assert out.shape == (1020, 2)
    meta = dict(ln.split("\t", 1) for ln in (work / "meta.txt").read_text(encoding="utf-8").splitlines()
                if not ln.startswith("formal"))
    ours = np.array([R.bicor(x, y) for x, y in pairs + extra])
    explicit, defaults = out[:, 0], out[:, 1]
    assert np.array_equal(explicit, defaults), "WGCNA::bicor with R13's values differs from its defaults"
    d_main = float(np.max(np.abs(ours[:1000] - explicit[:1000])))
    d_extra = float(np.max(np.abs(ours[1000:] - explicit[1000:])))
    fl = [ln.split("\t") for ln in (work / "meta.txt").read_text(encoding="utf-8").splitlines() if ln.startswith("formal")]
    fdict = {a[1]: a[2] for a in fl}
    assert fdict.get("maxPOutliers") == "1" and fdict.get("pearsonFallback") == '"individual"' and \
        fdict.get("robustX") == "TRUE" and fdict.get("robustY") == "TRUE", fdict
    scaled = np.array([float(R.bicor_prepare(x, _mad_constant=1.4826)[0] @ R.bicor_prepare(y, _mad_constant=1.4826)[0])
                       for x, y in pairs])
    d_scaled = float(np.max(np.abs(scaled - explicit[:1000])))
    assert d_main <= TOL["wgcna"] and d_extra <= TOL["wgcna"], (d_main, d_extra)
    assert d_scaled > TOL["wgcna"], "must-differ variant (scaled MAD) agreed with WGCNA: the comparison cannot fail"
    return dict(wgcna_version=meta.get("WGCNA"), r_version=meta.get("R"), n_pairs=1000, max_abs_diff_1000=d_main,
                n_fallback_pairs=20, max_abs_diff_fallback=d_extra, wgcna_formals=fdict,
                must_differ_scaled_mad_max_abs_diff=d_scaled,
                run=run_record("wgcna_bicor.R", work, ["pairs.bin"], ["out.bin", "meta.txt"]))


# ================================================================================================================
# R27: |z|-weighted GEDAR rho (Giacomel)
# ================================================================================================================
@check("P17.gedar_abs_rho")
def t_gedar():
    X = np.array([[1, 2], [3, 1], [2, 5], [4, 0]], dtype=float)
    z = np.array([1.0, -3.0])
    y = np.array([0.1, 0.4, 0.2, 0.3])
    s = R.gedar_abs_score(X, z)
    hand_s = np.array([7, 6, 17, 4]) / 4.0  # (x1 + 3 x2) / 4
    assert np.array_equal(s, hand_s), s
    rho = R.gedar_abs_rho(y, X, z)["rho"]
    hand_rho = spearman_formula_exact(y, hand_s)  # ranks y 1,4,2,3; score 3,2,4,1 -> 1 - 6*16/60 = -3/5
    assert hand_rho == Fraction(-3, 5) and abs(rho - float(hand_rho)) <= TOL["closed_form"], rho
    rng = ss(6, 0)
    worst = dict(loop=0.0, equal_w=0.0, scale_w=0.0, scipy=0.0, subset=0.0)
    sign_free_identical = monotone_identical = True
    diffs_signed = []
    for i in range(100):
        P, G = 34, int((5, 25, 200)[i % 3])
        Xr = rng.normal(size=(P, G))
        zr = rng.normal(size=G) * 3
        yr = mixed_vector(rng, P, i % 5)
        sc = R.gedar_abs_score(Xr, zr)
        loop = np.array([sum(abs(zr[g]) * Xr[p, g] for g in range(G)) / sum(abs(zr[g]) for g in range(G))
                         for p in range(P)])
        worst["loop"] = max(worst["loop"], float(np.max(np.abs(sc - loop))))
        worst["equal_w"] = max(worst["equal_w"], float(np.max(np.abs(R.gedar_abs_score(Xr, np.ones(G)) - Xr.mean(1)))))
        worst["scale_w"] = max(worst["scale_w"], float(np.max(np.abs(R.gedar_abs_score(Xr, 7.5 * zr) - sc))))
        sign_free_identical &= bool(np.array_equal(R.gedar_abs_score(Xr, -zr), sc))
        r1 = R.gedar_abs_rho(yr, Xr, zr)["rho"]
        worst["scipy"] = max(worst["scipy"], rel(r1, stats.spearmanr(yr, sc).statistic))
        monotone_identical &= R.gedar_abs_rho(np.exp(yr), Xr, zr)["rho"] == r1
        gi = np.sort(rng.choice(G, size=max(2, G // 2), replace=False))
        worst["subset"] = max(worst["subset"], float(np.max(np.abs(R.gedar_abs_score(Xr, zr, gi)
                                                                    - R.gedar_abs_score(Xr[:, gi], zr[gi])))))
        signed = (Xr @ zr) / zr.sum()
        diffs_signed.append(abs(stats.spearmanr(yr, signed).statistic - r1))
    assert worst["loop"] <= TOL["sum_order"]
    assert worst["equal_w"] <= TOL["vector_loop"] and worst["scale_w"] <= TOL["vector_loop"]
    assert worst["scipy"] <= TOL["scipy_rel"] and worst["subset"] == 0.0 and sign_free_identical and monotone_identical
    assert max(diffs_signed) > 1e-3, "must differ: the signed weighting gave the same rho everywhere"
    return dict(hand=dict(score=hand_s, rho=rho, exact=str(hand_rho)), max_diffs=worst,
                must_differ_signed_weights_max_abs=float(max(diffs_signed)))


def _gedar_cases():
    rng = ss(7, 0)
    cases = []
    for i in range(20):
        P, G = 34, int((10, 100, 1000)[i % 3])
        cases.append((rng.normal(size=(P, G)), np.abs(rng.normal(size=G) * 2) + 1e-3, mixed_vector(rng, P, i % 5)))
    return cases


@check("P17.r17_image_exercise_docker", docker=True)
def t_gedar_docker():
    cases = _gedar_cases()
    work = SCRATCH / "gedar"
    work.mkdir(exist_ok=True)
    with open(work / "in.bin", "wb") as fh:
        fh.write(struct.pack("<i", len(cases)))
        for X, w, y in cases:
            fh.write(struct.pack("<2i", *X.shape))
            fh.write(np.ascontiguousarray(X, dtype="<f8").tobytes())
            fh.write(np.asarray(w, dtype="<f8").tobytes())
            fh.write(np.asarray(y, dtype="<f8").tobytes())
    r = DR.run_r("gedar_synthetic.R", ["/work/in.bin", "/work/out.bin"], work)
    if r.returncode != 0:
        raise RuntimeError(f"Rscript exited {r.returncode}: {r.stderr.decode('ascii', 'replace')[-400:]}")
    out = np.fromfile(work / "out.bin", dtype="<f8")
    pos, ds, dr = 0, 0.0, 0.0
    for X, w, y in cases:
        P = X.shape[0]
        s_r, rho_r = out[pos: pos + P], out[pos + P]
        pos += P + 1
        res = R.gedar_abs_rho(y, X, w)
        ds = max(ds, float(np.max(np.abs(res["score"] - s_r))))
        dr = max(dr, abs(res["rho"] - rho_r))
    assert pos == out.size and ds <= TOL["r_score"] and dr <= TOL["r_score"], (ds, dr)
    return dict(n_cases=len(cases), max_abs_score_diff=ds, max_abs_rho_diff=dr,
                run=run_record("gedar_synthetic.R", work, ["in.bin"], ["out.bin"]),
                note="the image exercised on synthetic data; the paper's script is read under G2 only (R17)")


# ================================================================================================================
# R27 / R10: rank-biserial (Liu)
# ================================================================================================================
@check("P17.rank_biserial")
def t_rank_biserial():
    v = np.arange(1, 7, dtype=float)
    top, bottom, ends = (np.isin(np.arange(6), idx) for idx in ([4, 5], [0, 1], [0, 5]))
    hand = [R.rank_biserial_fraction(v, top), R.rank_biserial_fraction(v, bottom), R.rank_biserial_fraction(v, ends)]
    assert hand == [Fraction(1), Fraction(-1), Fraction(0)], hand
    tie_v = np.array([1.0, 2.0, 2.0, 3.0])
    tie_g = np.array([False, True, False, True])  # ranks 1, 2.5, 2.5, 4: group sum 6.5, U1 = 3.5, r = 2*3.5/4 - 1
    assert R.rank_biserial_fraction(tie_v, tie_g) == Fraction(3, 4)
    # must differ: ordinal (non-averaged) ranks on the tied case
    ordr = stats.rankdata(tie_v, method="ordinal")
    n1, n2 = 2, 2
    u1_ord = ordr[tie_g].sum() - n1 * (n1 + 1) / 2
    ord_r = 2 * u1_ord / (n1 * n2) - 1
    assert ord_r != 0.75
    rng = ss(8, 0)
    n_exact = 0
    for i in range(300):
        n = int(rng.integers(6, 60))
        vals = mixed_vector(rng, n, 4 if i % 2 else i % 5)
        g = np.zeros(n, bool)
        g[rng.choice(n, size=int(rng.integers(1, n)), replace=False)] = True
        fr = R.rank_biserial_fraction(vals, g)
        u1 = stats.mannwhitneyu(vals[g], vals[~g], alternative="two-sided", method="asymptotic").statistic
        n1, n2 = int(g.sum()), int((~g).sum())
        two_u1 = 2 * u1
        assert two_u1 == int(two_u1)
        assert fr == Fraction(int(two_u1) - n1 * n2, n1 * n2), (fr, u1)
        assert R.rank_biserial_fraction(vals, ~g) == -fr
        assert R.rank_biserial_fraction(np.exp(vals / 10) * 3 + 1, g) == fr  # strictly increasing transform
        n_exact += 1
    return dict(hand=[str(h) for h in hand], tie_case="3/4", n_exact_vs_mannwhitney=n_exact,
                must_differ_ordinal_ranks=ord_r)


@check("P17.liu_t3_and_r10")
def t_liu():
    rng = ss(9, 0)
    P, G = 34, 300
    X = rng.normal(size=(P, G))
    g = np.zeros(G, bool)
    g[rng.choice(G, 25, replace=False)] = True
    y = rng.normal(size=P)
    X_pl = X.copy()
    X_pl[:, g] += 1.5 * y[:, None]  # S's genes rise with y
    res = R.liu_t3_rho(y, X_pl, g)
    loop = np.array([R.rank_biserial(X_pl[p], g) for p in range(P)])
    mw = np.array([2 * stats.mannwhitneyu(X_pl[p, g], X_pl[p, ~g], method="asymptotic").statistic
                   / (g.sum() * (~g).sum()) - 1 for p in range(P)])
    assert np.array_equal(res["per_parcel_r"], loop)
    d_mw = float(np.max(np.abs(loop - mw)))
    d_sp = rel(res["rho"], stats.spearmanr(y, loop).statistic)
    assert d_mw <= 1e-15 and d_sp <= TOL["scipy_rel"], (d_mw, d_sp)
    assert res["rho"] > 0.5 and R.liu_t3_rho(-y, X_pl, g)["rho"] == -res["rho"]
    # R10: per-sample r, a label's value = the mean over its samples
    Xs = rng.normal(size=(120, G))
    labels = rng.integers(0, 10, size=120)
    lm = R.label_mean_rank_biserial(Xs, labels, g)
    rs = R.rank_biserial_rows(Xs, g)
    worst = 0.0
    for L in range(10):
        m = labels == L
        assert lm[L][1] == int(m.sum())
        worst = max(worst, abs(lm[L][0] - float(np.mean(rs[m]))))
    assert worst <= 1e-15
    # must differ: the plain mean-difference "enrichment" in place of the rank-biserial r
    md = X_pl[:, g].mean(1) - X_pl[:, ~g].mean(1)
    d_md = abs(stats.spearmanr(y, md).statistic - res["rho"])
    assert d_md > 1e-6
    return dict(planted_rho=res["rho"], max_abs_vs_mannwhitney=d_mw, rel_vs_scipy_spearman=d_sp,
                r10_label_mean_max_abs=worst, must_differ_mean_difference=float(d_md))


# ================================================================================================================
# R14: per-donor recipe t; BH
# ================================================================================================================
def _recipe_data():
    rng = ss(10, 0)
    D, P, G = 6, 40, 300
    y = rng.normal(size=P)
    true = rng.normal(scale=0.05, size=G)
    true[:20] = 1.0
    true[20:40] = -1.0
    mats = []
    for d in range(D):
        M = 5 + np.outer(y, true) + rng.normal(scale=0.2, size=(P, G))
        miss = rng.random(P) < 0.3
        M[miss, :] = np.nan
        mats.append(M)
    mats[5][:] = np.nan
    mats[5][:2, :] = 5 + rng.normal(size=(2, G))      # donor 6: 2 parcels -> dropped for every gene
    for d in range(1, 5):                              # gene 299: only donor 1 kept -> not tested
        mats[d][:, 299] = np.nan
    mats[2][:, 150] = np.nan                           # gene 150: donor 3 missing
    mats[3][np.flatnonzero(np.isfinite(mats[3][:, 151]))[3:], 151] = np.nan  # gene 151: donor 4 has 3 parcels
    mats[4][np.flatnonzero(np.isfinite(mats[4][:, 152]))[2:], 152] = np.nan  # gene 152: donor 5 has 2 -> dropped
    return y, mats


@check("P17.per_donor_recipe_t")
def t_recipe():
    y, mats = _recipe_data()
    res = R.per_donor_recipe_t(y, mats)
    sl = res["slopes"]
    S = sl["slopes"]
    worst_slope = 0.0
    for d, M in enumerate(mats):
        for g in range(M.shape[1]):
            f = np.isfinite(M[:, g])
            if f.sum() >= 3:
                b = np.polyfit(y[f], M[f, g], 1)[0]
                worst_slope = max(worst_slope, abs(b - S[d, g]))
            else:
                assert np.isnan(S[d, g])
    assert worst_slope <= 1e-12, worst_slope
    assert int(sl["dropped_lt_min_parcels"][5]) == 300
    hand_drop = [int(sum(np.isfinite(M[:, g]).sum() < 3 for g in range(300))) for M in mats]
    assert list(map(int, sl["dropped_lt_min_parcels"])) == hand_drop
    assert np.isnan(S[4, 152]) and np.isfinite(S[3, 151]) and int(res["n_donors_kept"][150]) == 4
    assert not res["tested"][299] and res["n_not_tested_lt2_donors"] == 1
    worst_t = worst_p = 0.0
    for g in np.flatnonzero(res["tested"]):
        v = S[:, g][np.isfinite(S[:, g])]
        tt = stats.ttest_1samp(v, 0.0)
        worst_t = max(worst_t, rel(res["t"][g], tt.statistic))
        worst_p = max(worst_p, rel(res["p_two_sided"][g], tt.pvalue))
        assert res["df"][g] == v.size - 1
    assert worst_t <= TOL["scipy_rel"] and worst_p <= 1e-9, (worst_t, worst_p)
    from statsmodels.stats.multitest import multipletests
    tested = res["tested"]
    q_sm = multipletests(res["p_two_sided"][tested], method="fdr_bh")[1]
    d_q = float(np.max(np.abs(q_sm - res["q_bh"][tested])))
    assert d_q <= 1e-15 and np.isnan(res["q_bh"][~tested]).all()
    lists = R.decoded_lists(res, 0.01)
    up, down = set(lists[1].tolist()), set(lists[-1].tolist())
    assert set(range(20)) <= up and set(range(20, 40)) <= down, "planted genes not recovered"
    fp = len(up - set(range(20))) + len(down - set(range(20, 40)))
    assert set(lists["universe"].tolist()) == set(np.flatnonzero(tested).tolist())
    # must differ: ddof 0 in the t's SD; one pooled OLS over all donors' parcels
    g0 = 0
    v0 = S[:, g0][np.isfinite(S[:, g0])]
    t_ddof0 = v0.mean() / (v0.std(ddof=0) / math.sqrt(v0.size))
    yy = np.concatenate([y[np.isfinite(M[:, g0])] for M in mats])
    xx = np.concatenate([M[np.isfinite(M[:, g0]), g0] for M in mats])
    t_pooled = stats.linregress(yy, xx).slope / stats.linregress(yy, xx).stderr
    assert rel(t_ddof0, res["t"][g0]) > 1e-3 and rel(t_pooled, res["t"][g0]) > 1e-3
    return dict(max_abs_slope_vs_polyfit=worst_slope, rel_t_vs_scipy=worst_t, rel_p_vs_scipy=worst_p,
                max_abs_q_vs_statsmodels=d_q, dropped_per_donor=hand_drop, n_tested=res["n_tested"],
                n_not_tested=res["n_not_tested"], planted_recovered="40 / 40", false_positives_reported=fp,
                must_differ=dict(t_ddof0=t_ddof0, t_pooled=t_pooled, t=res["t"][g0]))


@check("P17.bh")
def t_bh():
    p = [0.01, 0.04, 0.03, 0.5]
    hand = [Fraction(4, 100), Fraction(16, 300), Fraction(16, 300), Fraction(1, 2)]  # by hand, step-up
    q = R.bh(p)
    assert max(abs(Decimal(float(a)) - dec(b)) for a, b in zip(q, hand)) <= Decimal(1e-16), q
    from statsmodels.stats.multitest import multipletests
    rng = ss(11, 0)
    worst = 0.0
    for i in range(50):
        pv = rng.random(1000) ** 3
        pv[rng.choice(1000, 50)] = pv[0]  # ties
        pv[rng.choice(1000, 20)] = np.nan
        q = R.bh(pv)
        ok = np.isfinite(pv)
        worst = max(worst, float(np.max(np.abs(q[ok] - multipletests(pv[ok], method="fdr_bh")[1]))))
        assert np.isnan(q[~ok]).all()
    assert worst <= 1e-15
    bonf = np.minimum(np.array(p) * 4, 1)
    assert np.max(np.abs(bonf - R.bh(p))) > 1e-3
    return dict(hand_case=[float(v) for v in R.bh(p)], max_abs_vs_statsmodels=worst, must_differ_bonferroni=bonf)


# ================================================================================================================
# R22: Fisher + BH over-representation analysis
# ================================================================================================================
def _random_tables(n: int = 60):
    rng = ss(12, 0)
    tabs = []
    for i in range(n):
        N = int((200, 2000, 20000)[i % 3])
        r1 = int(rng.integers(5, min(300, N // 4)))
        c1 = int(rng.integers(5, min(500, N // 3)))
        lo, hi = max(0, r1 + c1 - N), min(r1, c1)
        mean = r1 * c1 / N
        if i % 4 == 0:
            a = min(hi, int(mean + 3 * math.sqrt(mean) + 2))      # over-represented
        elif i % 4 == 1:
            a = max(lo, int(mean - 2 * math.sqrt(mean)))          # under-represented
        else:
            a = int(rng.integers(lo, min(hi, int(mean * 3) + 2) + 1))
        tabs.append((a, r1 - a, c1 - a, N - r1 - c1 + a))
    tabs += [(0, 10, 10, 80), (10, 0, 0, 90), (3, 3, 3, 3), (1, 0, 0, 1)]
    return tabs


@check("P17.ora_fisher_bh")
def t_ora():
    ref = [f"g{i:05d}" for i in range(1, 21)]
    cnt = R.fisher_counts(ref[:5] + ["x_not_in_ref"], ref[3:8] + ["y_not_in_ref"], ref)
    assert (cnt["a"], cnt["b"], cnt["c"], cnt["d"], cnt["list_dropped_outside_reference"]) == (2, 3, 3, 12, 1), cnt
    worst_g = worst_2 = 0.0
    n_over = n_under_differ = 0
    for (a, b, c, d) in _random_tables():
        fp = R.fisher_p(a, b, c, d)
        h = R.fisher_exact_hand(a, b, c, d)
        worst_g = max(worst_g, rel(fp["p_greater"], float(h["greater"])))
        worst_g = max(worst_g, rel(fp["p_greater_fisher_exact"], float(h["greater"])))
        worst_2 = max(worst_2, rel(fp["p_two_sided"], float(h["two_sided"])))
        r1, c1, N = a + b, a + c, a + b + c + d
        mode = math.floor((r1 + 1) * (c1 + 1) / (N + 2))
        if a > mode:
            n_over += 1
            assert h["two_sided"] >= h["greater"], (a, b, c, d)
        if a < mode and h["greater"] > h["two_sided"]:
            n_under_differ += 1
    assert worst_g <= TOL["p_hand_rel"] and worst_2 <= TOL["p_hand_rel"], (worst_g, worst_2)
    assert n_under_differ > 0, "must differ: one-sided and two-sided p never differed on an under-represented term"
    # ORA over terms: BH per sidedness across the terms tested; primary per PANTHER_SIDEDNESS
    rng = ss(12, 1)
    reference = [f"g{i:05d}" for i in range(5000)]
    lst = list(rng.choice(reference, 300, replace=False)) + ["q_outside"]
    terms = {f"T{j:03d}": list(rng.choice(reference, int(rng.integers(5, 400)), replace=False)) for j in range(80)}
    for j in range(5):  # planted over-representation
        terms[f"T{j:03d}"] = list(set(terms[f"T{j:03d}"]) | set(lst[: 30 + 5 * j]))
    terms["T_empty"] = ["z_outside_1", "z_outside_2"]
    res = R.ora(lst, terms, reference)
    tested = [k for k in terms if res["terms"][k]["status"] == "tested"]
    assert res["n_not_tested"] == 1 and res["terms"]["T_empty"]["status"].startswith("not tested")
    qg = R.bh([res["terms"][k]["p_greater"] for k in tested])
    q2 = R.bh([res["terms"][k]["p_two_sided"] for k in tested])
    assert all(res["terms"][k]["q_greater"] == qg[i] and res["terms"][k]["q_two_sided"] == q2[i]
               for i, k in enumerate(tested))
    assert res["primary"] == "two-sided" and res["label"] == "PANTHER sidedness unverified"
    assert all(res["terms"][k]["p_primary"] == res["terms"][k]["p_two_sided"] for k in tested)
    assert all(res["terms"][k]["list_dropped_outside_reference"] == 1 for k in tested)
    planted_q = [res["terms"][f"T{j:03d}"]["q_primary"] for j in range(5)]
    assert max(planted_q) < 0.05
    return dict(contingency_hand="(2, 3, 3, 12), 1 list gene outside the reference dropped",
                n_tables=len(_random_tables()), rel_greater_vs_hand=worst_g, rel_two_sided_vs_hand=worst_2,
                over_represented_two_sided_ge_greater=n_over, must_differ_under_represented=n_under_differ,
                ora_terms_tested=len(tested), planted_q_primary=planted_q, primary=res["primary"],
                label=res["label"])


@check("P17.fisher_r_docker", docker=True)
def t_fisher_docker():
    tabs = _random_tables()
    work = SCRATCH / "fisher"
    work.mkdir(exist_ok=True)
    lines = ["case\ta\tb\tc\td"] + [f"t{i}\t{a}\t{b}\t{c}\t{d}" for i, (a, b, c, d) in enumerate(tabs)]
    (work / "tables.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    r = DR.run_r("fisher.R", ["/work/tables.tsv", "/work/out.tsv"], work)
    if r.returncode != 0:
        raise RuntimeError(f"Rscript exited {r.returncode}: {r.stderr.decode('ascii', 'replace')[-400:]}")
    rows = [ln.split("\t") for ln in (work / "out.tsv").read_text(encoding="utf-8").splitlines()[1:]]
    assert len(rows) == len(tabs)
    w2 = wg = wor = 0.0
    n_or = 0
    for (a, b, c, d), row in zip(tabs, rows):
        fp = R.fisher_p(a, b, c, d)
        p2, pg, est = float(row[1]), float(row[2]), float(row[4])
        w2 = max(w2, rel(fp["p_two_sided"], p2))
        wg = max(wg, rel(fp["p_greater"], pg))
        if math.isfinite(est) and est > 0 and math.isfinite(fp["odds_ratio_conditional_mle"]):
            wor = max(wor, rel(fp["odds_ratio_conditional_mle"], est))
            n_or += 1
    assert w2 <= TOL["r_p_rel"] and wg <= TOL["r_p_rel"] and wor <= TOL["r_or_rel"], (w2, wg, wor)
    return dict(n_tables=len(tabs), rel_two_sided_vs_R=w2, rel_greater_vs_R=wg, rel_conditional_or_vs_R=wor,
                n_or_compared=n_or, run=run_record("fisher.R", work, ["tables.tsv"], ["out.tsv"]))


@check("P17.panther_sidedness_record")
def t_panther():
    rec = R.PANTHER_SIDEDNESS
    assert rec["fetched_utc"] == "2026-10-01" and rec["primary"] == "two-sided"
    assert rec["label"] == "PANTHER sidedness unverified" and rec["finding"].startswith("unverified")
    urls = [s["url"] for s in rec["sources"]]
    assert urls[0] == "https://www.pantherdb.org/help/PANTHERhelp.jsp" and "403" in rec["sources"][0]["result"]
    assert all("no statement of one- or two-sidedness" == s["result"] for s in rec["sources"][1:])
    # 2026-10-11 empirical check (panther_sidedness_check.py): the saved summary must agree with the record, and the
    # two-sided p must reproduce every row (and every discriminating row) in both annotation sets
    emp = rec["empirical_check"]
    summ = json.loads((Path(R.__file__).resolve().parents[2] / "run_manifests" / "R22_panther" / "summary.json")
                      .read_text(encoding="utf-8"))
    for name in ("panther_pathway", "go_bp"):
        s = summ["datasets"][name]
        assert s["reproduced_two_sided"] == s["rows"] == emp[name]["rows"] == emp[name]["two_sided_reproduced"]
        assert s["reproduced_one_sided"] == emp[name]["one_sided_reproduced"] < s["rows"]
        assert s["discriminating_rows"] == emp[name]["discriminating_rows"] > 0
        assert s["discriminating_rows_reproduced_two_sided"] == s["discriminating_rows"]
    assert summ["finding"].startswith("PANTHER's overrepresentation Fisher p is two-sided")
    assert emp["panther_pathway"]["response_sha256"] == summ["datasets"]["panther_pathway"]["response_sha256"]
    return dict(finding=rec["finding"], primary=rec["primary"], label=rec["label"], sources=urls,
                empirical=emp["result"])


# ================================================================================================================
# R28: RLM vs a direct IRLS Huber fit
# ================================================================================================================
def _rlm_data(i: int, n: int):
    rng = ss(13, i)
    a = rng.normal(size=n)
    gc = rng.uniform(35, 65, size=n)
    t = 2.0 * a + 0.05 * (gc - 50) + rng.standard_t(3, size=n)
    k = rng.choice(n, size=max(1, n // 20), replace=False)
    t[k] += rng.normal(scale=25, size=k.size)  # 5 % gross outliers
    return t, a, gc


@check("P17.rlm_vs_direct_irls")
def t_rlm():
    """statsmodels RLM (defaults) == repro.huber_irls (independent direct IRLS) == forms.irls_huber_direct (the forms
    worker's direct fit, which forms.rlm_t asserts in production); forms.rlm_t's reported t == statsmodels'."""
    import statsmodels.api as sm
    from a1_audit import forms as FM
    worst = dict(params=0.0, scale=0.0, bse=0.0, t=0.0)
    worst_forms = dict(params=0.0, scale=0.0, bse=0.0, t=0.0)
    worst_fp = 0.0
    default_vs_fp = 0.0
    iters = []
    for i in range(30):
        n = int((200, 2000, 15000)[i % 3])
        t, a, gc = _rlm_data(i, n)
        sm_res = R.rlm_statsmodels(t, [a, gc])
        di = R.huber_irls(t, [a, gc])
        worst["params"] = max(worst["params"], max(rel(u, v) for u, v in zip(sm_res.params, di["params"])))
        worst["scale"] = max(worst["scale"], rel(sm_res.scale, di["scale"]))
        worst["bse"] = max(worst["bse"], max(rel(u, v) for u, v in zip(sm_res.bse, di["bse"])))
        worst["t"] = max(worst["t"], max(rel(u, v) for u, v in zip(sm_res.tvalues, di["tvalues"])))
        assert sm_res.fit_history["iteration"] == di["iterations"]
        iters.append(di["iterations"])
        fdi = FM.irls_huber_direct(t, np.column_stack([a, gc, np.ones_like(a)]))
        worst_forms["params"] = max(worst_forms["params"], max(rel(u, v) for u, v in zip(fdi["params"], di["params"])))
        worst_forms["scale"] = max(worst_forms["scale"], rel(fdi["scale"], di["scale"]))
        worst_forms["bse"] = max(worst_forms["bse"], max(rel(u, v) for u, v in zip(fdi["bse"], di["bse"])))
        worst_forms["t"] = max(worst_forms["t"], max(rel(u, v) for u, v in zip(fdi["tvalues"], di["tvalues"])))
        assert fdi["iterations"] == di["iterations"]
        tight = R.rlm_statsmodels(t, [a, gc], tol=1e-13, maxiter=1000)
        fp = R.huber_irls(t, [a, gc], stop="fixed-point", tol=1e-13, maxiter=1000)
        assert fp["converged_before_maxiter"]
        worst_fp = max(worst_fp, max(rel(u, v) for u, v in zip(tight.tvalues, fp["tvalues"])))
        default_vs_fp = max(default_vs_fp, rel(sm_res.tvalues[0], fp["tvalues"][0]))
    assert all(v <= TOL["rlm_same_rule_rel"] for v in worst.values()), worst
    assert all(v <= TOL["rlm_same_rule_rel"] for v in worst_forms.values()), worst_forms
    assert worst_fp <= TOL["rlm_fixed_point_rel"], worst_fp
    # rlm_log2fc_t: non-finite rows dropped and counted; the reported value is tvalues[0]
    t, a, gc = _rlm_data(99, 2000)
    t2, a2 = t.copy(), a.copy()
    t2[:7] = np.nan
    a2[7:10] = np.inf
    out = R.rlm_log2fc_t(t2, a2, gc)
    ref = R.rlm_statsmodels(t[10:], [a[10:], gc[10:]])
    assert out["n_dropped_nonfinite"] == 10 and out["n_used"] == 1990 and out["t_log2fc"] == float(ref.tvalues[0])
    # must differ: OLS on the contaminated data; a Huber t of 2.0 in place of 1.345
    ols = sm.OLS(t, np.column_stack([a, gc, np.ones_like(a)])).fit()
    h2 = R.huber_irls(t, [a, gc], t=2.0)
    assert rel(ols.tvalues[0], out["t_log2fc"]) > 1e-3 and rel(h2["tvalues"][0], ref.tvalues[0]) > 1e-3
    return dict(rel_same_rule=worst, rel_forms_direct_vs_huber_irls=worst_forms, iterations_equal=True,
                production="forms.rlm_t (repro.rlm_log2fc_t delegates)", iterations_range=[min(iters), max(iters)],
                rel_fixed_point_t=worst_fp, rel_default_vs_fixed_point_t_log2fc=default_vs_fp,
                dropped=10, t_log2fc=out["t_log2fc"],
                must_differ=dict(ols_t=float(ols.tvalues[0]), huber2_t=float(h2["tvalues"][0])))


# ================================================================================================================
# R30: overlap test vs a hand-computed hypergeometric tail; GeneOverlap in the R image
# ================================================================================================================
def _overlap_case(seed_item: int, U: int = 2000, nL: int = 120, nS: int = 150, k: int = 25):
    rng = ss(14, seed_item)
    uni = [f"g{i:05d}" for i in range(U)]
    perm = list(rng.permutation(U))
    L = [uni[i] for i in perm[:nL]]
    S = [uni[i] for i in perm[nL - k: nL - k + nS]]  # k shared
    return uni, L, S


@check("P17.overlap_test_hand")
def t_overlap():
    uni, L, S = _overlap_case(0)
    res = R.overlap_test(L, S + ["s_outside_1", "s_outside_2"], universe=uni)
    assert res["k"] == 25 and res["set_outside_universe"] == 2 and res["n_set"] == 150
    hand = Fraction(0)
    for x in range(25, 121):
        hand += Fraction(math.comb(150, x) * math.comb(2000 - 150, 120 - x), math.comb(2000, 120))
    d_p = rel(res["p"], float(hand))
    assert res["alternative"] == "greater" and d_p <= TOL["p_hand_rel"], (res["p"], float(hand))
    assert res["jaccard"] == 25 / (120 + 150 - 25)
    assert (res["a"], res["b"], res["c"], res["d"]) == (25, 95, 125, 2000 - 245)
    raises(ValueError, R.overlap_test, L + ["outside_list"], S, universe=uni)
    # GeneOverlap's construction with a genome size (lists as given; background = genome - |A u B|)
    g = R.overlap_test(L, S + ["s_outside_1"], genome_size=5000)
    assert (g["a"], g["b"], g["c"], g["d"]) == (25, 95, 126, 5000 - 246)
    hand_g = sum((Fraction(math.comb(151, x) * math.comb(5000 - 151, 120 - x), math.comb(5000, 120))
                  for x in range(25, 121)), Fraction(0))
    d_g = rel(g["p"], float(hand_g))
    assert d_g <= TOL["p_hand_rel"]
    raises(ValueError, R.overlap_test, L, S, genome_size=200)
    # must differ: the two-sided p on an under-overlapping case
    uni2, L2, S2 = _overlap_case(1, k=1)
    o = R.overlap_test(L2, S2, universe=uni2)
    o2 = R.overlap_test(L2, S2, universe=uni2, alternative="two.sided")
    assert rel(o["p"], o2["p"]) > 1e-3
    return dict(k=25, p=res["p"], rel_vs_hand=d_p, genome5000_rel_vs_hand=d_g, odds_ratio_cond=res["odds_ratio"],
                odds_ratio_sample=res["odds_ratio_sample"], must_differ=dict(greater=o["p"], two_sided=o2["p"]),
                geneoverlap_status=R.GENEOVERLAP["status"])


def _source_facts(src: str) -> dict:
    """R30's two facts from the deparsed GeneOverlap source: the fisher.test alternative in testGeneOverlap and the
    default genome size of newGeneOverlap (the first `spec` choice)."""
    blocks = re.split(r"^## (?:function|method) ", src, flags=re.M)
    test_blk = [b for b in blocks if b.startswith("testGeneOverlap")]
    new_blk = [b for b in blocks if b.startswith("newGeneOverlap")]
    alts = sorted(set(m for b in test_blk for m in re.findall(r"fisher\.test\([^)]*alternative\s*=\s*\"(\w+(?:\.\w+)?)\"",
                                                                    b)))
    spec = [re.search(r"spec\s*=\s*c\(\"([\w.]+)\"", b) for b in new_blk]
    first = next((m.group(1) for m in spec if m), None)
    size = None
    for b in new_blk:
        m = re.search(re.escape(first) + r"\s*=\s*([0-9]+)", b) if first else None
        if m:
            size = int(m.group(1))
    version = re.match(r"# GeneOverlap (\S+);", src)
    return dict(alternatives=alts, default_spec=first, default_genome_size=size,
                version=version.group(1) if version else None)


@check("P17.geneoverlap_docker", docker=True)
def t_geneoverlap():
    work = SCRATCH / "geneoverlap"
    work.mkdir(exist_ok=True)
    cases = []
    for i in range(12):
        uni, L, S = _overlap_case(10 + i, U=int((2000, 8000, 15000)[i % 3]), nL=int((60, 120, 400)[i % 3]),
                                  nS=int((80, 150, 600)[(i + 1) % 3]), k=int((2, 10, 25, 40)[i % 4]))
        cases.append((f"u{i}", str(len(uni)), L, S, uni))
    for i in range(4):
        _, L, S = _overlap_case(30 + i, nL=100, nS=200, k=int((1, 8, 20, 35)[i]))
        cases.append((f"d{i}", "NA", L, S, None))
    lines = ["case\tgenome_size\tlist_a\tlist_b"] + [f"{c}\t{g}\t{','.join(L)}\t{','.join(S)}"
                                                     for c, g, L, S, _ in cases]
    (work / "cases.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    r = DR.run_r("geneoverlap.R", ["/work/cases.tsv", "/work/out.tsv", "/work/source.txt"], work)
    if r.returncode != 0:
        raise RuntimeError(f"Rscript exited {r.returncode}: {r.stderr.decode('ascii', 'replace')[-400:]}")
    src = (work / "source.txt").read_text(encoding="utf-8")
    facts = _source_facts(src)
    assert facts["alternatives"] == [R.GENEOVERLAP["alternative"]], facts
    assert facts["default_genome_size"] is not None and facts["version"] is not None, facts
    # repro.GENEOVERLAP was written from this source: every recorded fact must still be what the image's source says
    assert (R.GENEOVERLAP["default_genome_size"], R.GENEOVERLAP["package_version"], R.GENEOVERLAP["default_spec"]) == \
        (facts["default_genome_size"], facts["version"], facts["default_spec"]), facts
    if DR.sha256_file(DR.LOG_DIR / "geneoverlap_1.42.0_source.txt") != DR.sha256_file(work / "source.txt"):
        raise AssertionError("the image's GeneOverlap source differs from the dump repro.GENEOVERLAP cites")
    rows = {ln.split("\t")[0]: ln.split("\t") for ln in (work / "out.tsv").read_text(encoding="utf-8").splitlines()[1:]}
    wp = wor = 0.0
    for c, g, L, S, uni in cases:
        row = rows[c]
        gs = int(float(row[5]))
        if g == "NA":
            assert gs == facts["default_genome_size"]
        ours = R.overlap_test(L, S, universe=uni) if uni is not None else R.overlap_test(L, S, genome_size=gs)
        assert int(row[3]) == ours["k"] and int(row[4]) == ours["a"] + ours["b"] + ours["c"]
        wp = max(wp, rel(ours["p"], float(row[1])))
        if float(row[2]) > 0 and math.isfinite(float(row[2])):
            wor = max(wor, rel(ours["odds_ratio"], float(row[2])))
        assert abs(ours["jaccard"] - float(row[6])) <= 1e-15
    assert wp <= TOL["r_p_rel"] and wor <= TOL["r_or_rel"], (wp, wor)
    keep = DR.LOG_DIR / f"geneoverlap_{facts['version']}_source.txt"
    keep.write_text(src, encoding="utf-8", newline="\n")
    assert keep.read_text(encoding="utf-8") == src
    lines_alt = [ln.strip() for ln in src.splitlines() if "fisher.test(" in ln]
    lines_spec = [ln.strip() for ln in src.splitlines() if "genome.size <-" in ln or facts["default_spec"] + " =" in ln]
    return dict(geneoverlap_version=facts["version"], alternative=facts["alternatives"][0],
                default_spec=facts["default_spec"], default_genome_size=facts["default_genome_size"],
                source_lines=dict(fisher=lines_alt[:4], genome=lines_spec[:6]),
                source_dump=dict(path=keep.relative_to(DR.HERE).as_posix(), sha256=DR.sha256_file(keep)),
                n_cases=len(cases), rel_p_vs_geneoverlap=wp, rel_or_vs_geneoverlap=wor,
                run=run_record("geneoverlap.R", work, ["cases.tsv"], ["out.tsv", "source.txt"]))


@check("P17.r_image_record", docker=True)
def t_image_record():
    rec = DR.image_status()
    df = DR.DOCKERFILE.read_text(encoding="utf-8")
    assert f"ARG BASE={DR.BASE_REF}@{DR.BASE_DIGEST}" in df and rec["base"]["digest"] == DR.BASE_DIGEST
    assert rec["r_version"] == "4.4.3" and rec["bioc_version"] == DR.BIOC_VERSION and rec["cran"] == DR.CRAN_SNAPSHOT
    assert rec["packages"]["named"].get("WGCNA") and rec["packages"]["named"].get("GeneOverlap")
    for b in rec["build_logs"]:
        assert DR.sha256_file(DR.HERE / b["path"]) == b["sha256"] and b["exit"] == 0
    vlog = DR.HERE / rec["lock_verify"]["path"]
    assert DR.sha256_file(vlog) == rec["lock_verify"]["sha256"]
    assert "A1 rbuild verify: pass;" in vlog.read_text(encoding="utf-8")
    live = DR._in_image(rec["image"]["id"], "Rscript", "/opt/a1_rbuild/install_packages.R", "verify",
                        "/opt/a1_rbuild/packages.lock.tsv")
    assert "A1 rbuild verify: pass;" in live  # the lock verified again, now, in the recorded image
    sess = DR.HERE / rec["session_info"]["path"]
    assert DR.sha256_file(sess) == rec["session_info"]["sha256"]
    # the content-stable identity (manifest digest) is the one repro.GENEOVERLAP cites; a rebuilt image (WP4) with
    # other content fails here until the R30 facts are re-read from it
    assert rec["image"]["exported_digests"]["manifest"] == R.GENEOVERLAP["image_manifest"], rec["image"]
    n_lock = len(DR.LOCK_TSV.read_text(encoding="utf-8").splitlines()) - 1
    assert n_lock == rec["packages"]["n_installed"] and n_lock > 0
    return dict(image=rec["image"]["id"], exported=rec["image"]["exported_digests"], base=rec["base"]["digest"],
                r=rec["r_version"], bioc=rec["bioc_version"], lock_verify_live=live.strip()[:80],
                cran=rec["cran"], named=rec["packages"]["named"], n_locked_packages=n_lock,
                build_logs=[b["path"] for b in rec["build_logs"]], status=rec["status"])


def main() -> int:
    t0 = time.time()
    print(f"P17 reproduction functionals: scratch {SCRATCH}", flush=True)
    for run in CHECKS:
        run()
    out = SCRATCH / "test_repro_p17_results.json"
    payload = dict(results=RESULTS, failed=FAILED, skipped=SKIPPED, tolerances=TOL, seconds=round(time.time() - t0, 1),
                   implementation_readings=list(R.IMPLEMENTATION_READINGS))
    out.write_text(json.dumps(A.jsonable(payload), indent=1) + "\n", encoding="utf-8", newline="\n")
    back = json.loads(out.read_text(encoding="utf-8"))
    assert back["failed"] == FAILED and back["skipped"] == SKIPPED
    n = len(CHECKS)
    print(f"{n - len(FAILED) - len(SKIPPED)} of {n} checks passed, {len(FAILED)} failed, {len(SKIPPED)} skipped "
          f"({time.time() - t0:.0f}s); results {out}", flush=True)
    for s in SKIPPED:
        print(f"  skipped {s}: {RESULTS[s]['reason']}", flush=True)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
