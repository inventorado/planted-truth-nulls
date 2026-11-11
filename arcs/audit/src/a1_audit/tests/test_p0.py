"""P0 (arcs/audit/RUN_PLAN.md v3.1 §7 row P0) and the early value checks of the T-form adapters (P5, P7, P11, P12).

(a) the ported A3 helpers (a1_audit.a3_port) against the A3 functions (arcs/replication/src; imported HERE ONLY, never
    by runner code): first the text of every copied block against its git blob, then every function on toy data with
    identical inputs and generator states (np.array_equal / dict equality, NaN-aware, types included): zscore,
    direction_of, p_leg, Resid, CorrStat, the h_common helpers and ClassContext (+ build_context on patched toy
    loaders), g1_null_chunked, g3m_null_chunked, g6l_screen, g6l_pool, species_draws, _g6l_public, assemble_verdict,
    claim_verdict, PLS1R2, descriptors, apply_gate, a1_scope_in_force, reading, jsonable / canon / map_sha, and the
    Checkpoints / run_pending round trip (in-process and loky) in a scratch directory; shared vs unshared G6l screens
    (g6l_screen's multi-stream pass, §4 "Shared G6l screens") give bit-identical sets and p's.
(b) set-vs-map T = r(y, X[:, S].mean(1)) on the UNSTANDARDISED matrix to 1e-12, on a toy matrix whose gene variances
    differ, where the z-scored score gives an r that differs by > 1e-6 (so the check can fail); the SetVsMap legs equal
    A3's claim_verdict one-sided legs in both directions (bit for bit).
Value checks: DecodedList T = mean per-gene r; Welch Level 0 = scipy; site leg = per-gene r recomputed; species null
= <y^, s_B(S) + s_W(R)>/n from the per-gene decomposition r_g = r_g^B + r_g^W (R2), conditioned = unconditioned on a
single class (P5), and a case where Pearson-r scoring (the engine's WithinClassBasis._p) gives a different p;
PlsEnrichment T and refit T* = direct, species p = DecodedList's (P7); TAbs values = direct (P11); component forms
refit = direct / sklearn (P12); R8 pool checks; R24 Level-2 G1; analysis_parcels / prepare_matrix (§4).

Synthetic data only. No gated or audit-target material is opened: e3_plants' GAMBA / AHBA paths are pointed at a
non-existent scratch path before anything runs, and build_context runs on patched toy loaders. The only repository
file read besides code is arcs/audit/results/e3_gates_a5.json (A1's synthetic gate results; sha256 asserted by
a1_scope_in_force) and the A3 git blobs.

Run (from arcs/audit/src):
  ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_p0 [--scratch DIR]
Exits non-zero on any failure. Prints ASCII only.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
for _p in (ROOT / "src", ROOT / "arcs" / "audit" / "src", ROOT / "arcs" / "replication" / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

ap = argparse.ArgumentParser()
ap.add_argument("--scratch", default=None, help="scratch directory (default: a new temporary directory)")
ap.add_argument("--no-loky", action="store_true", help="skip run_pending's jobs > 1 path")
ARGS, _ = ap.parse_known_args()
SCRATCH = Path(ARGS.scratch or tempfile.mkdtemp(prefix="a1_p0_")).resolve()
SCRATCH.mkdir(parents=True, exist_ok=True)
NO_DATA = SCRATCH / "no_such_data_dir"  # never created: an unpatched data read fails here, never reaches E: / artifacts
assert not NO_DATA.exists()

import e3_plants  # noqa: E402  (A1's plant module; only its data paths are neutralised)

e3_plants.GAMBA_CSV = NO_DATA / "gamba.csv"
e3_plants.AHBA = NO_DATA

import a1_audit.a3_port as A  # noqa: E402
import a1_audit.adapters as AD  # noqa: E402
import h_common as H  # noqa: E402  (A3, tests only)
import h_verdicts as V  # noqa: E402  (A3, tests only)
import step3v_common as SV  # noqa: E402  (A3, tests only)
from asdg.cascade import corr_matrix, emp_p, naive_p, pls1  # noqa: E402
from asdg.genesets import random_sets  # noqa: E402
from asdg.spatial import site_null  # noqa: E402

A.AHBA = NO_DATA
H.AHBA = NO_DATA

RESULTS: dict = {}
FAILED: list = []
LEG_NO = {"S1c": 0, "S2c": 1, "G1": 2, "G3m": 3, "G6s": 4, "G6l": 5, "permutation": 8}
K = 200


def seeds(case: int):
    """Plant-style keys (RUN_PLAN §7: SeedSequence([20260925, 900, plant_id, case, ...]); P0 = plant 0) + the leg."""
    return lambda leg: np.random.SeedSequence([20260925, 900, 0, int(case), LEG_NO[leg]])


def check(name):
    def deco(fn):
        def run():
            t0 = time.time()
            try:
                measured = fn() or {}
                RESULTS[name] = dict(result="pass", seconds=round(time.time() - t0, 2), **measured)
                print(f"PASS {name} ({time.time() - t0:.1f}s) {json.dumps(measured, default=_num)}", flush=True)
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


CHECKS: list = []


def _num(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return str(o)


def same(a, b, path="$"):
    """Bit-identity, NaN-aware, types included (dicts: same keys in the same order)."""
    if isinstance(a, dict) or isinstance(b, dict):
        assert isinstance(a, dict) and isinstance(b, dict), f"{path}: {type(a)} vs {type(b)}"
        assert list(a) == list(b), f"{path}: keys {list(a)} vs {list(b)}"
        for k in a:
            same(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        assert type(a) is type(b) and len(a) == len(b), f"{path}: {type(a)} {len(a)} vs {type(b)} {len(b)}"
        for i, (x, z) in enumerate(zip(a, b)):
            same(x, z, f"{path}[{i}]")
    elif isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        a2, b2 = np.asarray(a), np.asarray(b)
        assert a2.shape == b2.shape and a2.dtype == b2.dtype, f"{path}: {a2.shape}/{a2.dtype} vs {b2.shape}/{b2.dtype}"
        eq = np.array_equal(a2, b2, equal_nan=a2.dtype.kind in "fc")
        assert eq, f"{path}: arrays differ (max |d| {np.nanmax(np.abs(a2.astype(float) - b2.astype(float)))})"
    elif isinstance(a, pd.DataFrame) or isinstance(b, pd.DataFrame):
        assert a.equals(b), f"{path}: frames differ"
    elif isinstance(a, float) or isinstance(b, float):
        assert type(a) is type(b), f"{path}: {type(a)} vs {type(b)}"
        assert (math.isnan(a) and math.isnan(b)) or a == b, f"{path}: {a!r} vs {b!r}"
    else:
        assert type(a) is type(b) and a == b, f"{path}: {a!r} ({type(a)}) vs {b!r} ({type(b)})"


def close(a, b, tol, what):
    d = float(np.max(np.abs(np.asarray(a, dtype=float) - np.asarray(b, dtype=float))))
    assert d <= tol, f"{what}: max |d| {d:.3g} > {tol:g}"
    return d


def raises_same(f_a, f_b, *args, **kw):
    """Both raise; same exception type and message."""
    out = []
    for f in (f_a, f_b):
        try:
            f(*args, **kw)
        except BaseException as e:  # noqa: BLE001 (CheckpointError is a SystemExit)
            out.append((type(e).__name__, str(e)))
            continue
        raise AssertionError(f"{getattr(f, '__qualname__', f)} did not raise")
    assert out[0] == out[1], f"different refusals: {out}"
    return out[0][0]


# ================================================================================================================
# toy inputs (two builds of the same context: A3's ClassContext and the port's)
# ================================================================================================================
CLASS_NAMES = ("cortex", "subcortex/brainstem", "cerebellum")


def toy_inputs(seed=1, sizes=(24, 14, 8), G=300, scale=(0.2, 5.0), module=None):
    """parcels in len(sizes) tissue classes, genes = class offsets + 5 smooth factors + noise, then every gene scaled
    and shifted by its own factor (gene variances differ); a random brain>body subset of 50 genes. module = (m, load):
    genes 0..m-1 share a within-class pattern f (returned)."""
    rng = np.random.default_rng(seed)
    cl = np.concatenate([[c] * k for c, k in zip(CLASS_NAMES, sizes)])
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


def both_ctx(inp, name="toy", atlas=None):
    a = A.ClassContext(name, inp["expr"].copy(), inp["classes"].copy(), inp["xyz"].copy(), inp["info"].copy(),
                       A.symbols_background(inp["brain"]), atlas)
    h = H.ClassContext(name, inp["expr"].copy(), inp["classes"].copy(), inp["xyz"].copy(), inp["info"].copy(),
                       H.symbols_background(inp["brain"]), atlas)
    return a, h


def field(ctx, rng, length=35.0):
    L = np.linalg.cholesky(np.exp(-(ctx.D / length) ** 2) + 1e-6 * np.eye(ctx.n))
    return L @ rng.standard_normal(ctx.n)


INP = toy_inputs(1)
CA, CH = both_ctx(INP, name="V-AAL", atlas="aal")
Y = field(CA, np.random.default_rng(2)) + 0.4 * CA.X[:, :10].mean(1) / CA.X[:, :10].mean(1).std()
S25 = np.arange(5, 30)


def git(*a) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, check=True).stdout


# ================================================================================================================
# (a) text identity of the copies
# ================================================================================================================
MARK = re.compile(r"^# ported from (arcs/replication/src/\S+):(\d+) \(git blob ([0-9a-f]{40}) at HEAD ([0-9a-f]+)\)$")
END = "# ---- end of ported code"


def text_identity(lines: list) -> dict:
    """Every '# ported from' block equals its blob's lines from the marked line on; only import lines lie between
    blocks; every top-level def / class lies inside a copied block. Raises AssertionError otherwise."""
    assert not any("\r" in ln for ln in lines), "a3_port.py must be LF"
    marks = [(i, MARK.match(ln)) for i, ln in enumerate(lines) if ln.startswith("# ported from")]
    assert marks and all(m for _, m in marks), "malformed marker"
    end = next(i for i, ln in enumerate(lines) if ln.startswith(END))
    blobs, spans, n_lines = {}, [], 0
    allowed = re.compile(r"^(import |from |H = sys\.modules|ROOT = Path)")
    for j, (i, m) in enumerate(marks):
        path, start, blob, head = m.group(1), int(m.group(2)), m.group(3), m.group(4)
        assert blob == A.PORTED_BLOBS[path] and head == A.PORTED_FROM_HEAD, (path, blob, head)
        if blob not in blobs:
            blobs[blob] = git("cat-file", "-p", blob).decode("utf-8").split("\n")
            # the A3 file the tests import is this blob (else the bit-identity below compares other code)
            now = git("hash-object", str(ROOT / path)).decode().strip()
            assert now == blob, f"{path}: working copy {now} != copied blob {blob}"
        nxt = marks[j + 1][0] if j + 1 < len(marks) else end
        body = lines[i + 1: nxt]
        k = 1 if body and body[0].startswith("# A3 reading") else 0  # the marker's own annotation line
        body = body[k:]
        src = blobs[blob]
        n = 0  # the copied block = the longest prefix of body equal to the source from `start` on
        while n < len(body) and start - 1 + n < len(src) and body[n] == src[start - 1 + n]:
            n += 1
        rest = [ln for ln in body[n:] if ln.strip()]
        assert n > 0 and all(allowed.match(ln) for ln in rest), f"{path}:{start}: non-copied lines: {rest[:2]}"
        spans.append((i + 1, i + 1 + k + n))
        n_lines += n
    tree = ast.parse("\n".join(lines))
    defs = [(nd.name, nd.lineno) for nd in tree.body if isinstance(nd, (ast.FunctionDef, ast.ClassDef))]
    outside = [d for d, ln in defs if not any(a < ln <= b for a, b in spans)]
    assert not outside, f"definitions outside copied blocks: {outside}"
    return dict(blocks=len(marks), copied_lines=n_lines, definitions=len(defs))


@check("P0a_text_identity")
def t_text():
    lines = (HERE.parent / "a3_port.py").read_text(encoding="utf-8").split("\n")
    out = text_identity(lines)
    # planted failures the check must catch: one character changed inside a copied function; a hand-written def
    i = next(k for k, ln in enumerate(lines) if ln.startswith("def g6l_screen("))
    mut = list(lines)
    mut[i + 20] = mut[i + 20].replace("<=", "<") if "<=" in mut[i + 20] else mut[i + 20] + " "
    caught = 0
    for bad in (mut, lines[:i] + ["def extra():", "    return 1", ""] + lines[i:]):
        try:
            text_identity(bad)
        except AssertionError:
            caught += 1
    assert caught == 2, f"text-identity check caught {caught} of 2 planted edits"
    return dict(out, planted_edits_caught=caught, blobs={p: b[:8] for p, b in A.PORTED_BLOBS.items()},
                head=A.PORTED_FROM_HEAD)


@check("comparator_planted_failures")
def t_same():
    a = np.linspace(0, 1, 11)
    b = a.copy()
    b[3] = np.nextafter(b[3], 2.0)  # one ulp
    caught = 0
    for x, z in ((a, b), (dict(p=1, q=2), dict(q=2, p=1)), (0.5, np.float64(0.5)), ([1, 2], (1, 2)),
                 (np.arange(3), np.arange(3.0)), (dict(p=float("nan")), dict(p=0.0))):
        try:
            same(x, z)
        except AssertionError:
            caught += 1
    assert caught == 6, f"comparator caught {caught} of 6 planted differences"
    same(dict(p=float("nan"), v=np.array([np.nan, 1.0])), dict(p=float("nan"), v=np.array([np.nan, 1.0])))
    return dict(planted_differences_caught=caught)


# ================================================================================================================
# (a) bit-identity of the functions
# ================================================================================================================
@check("P0a_small_helpers")
def t_small():
    rng = np.random.default_rng(3)
    v = rng.standard_normal(40)
    same(A.zscore(v), V.zscore(v))
    for t in (-1.5, 0.0, -0.0, 2.0):
        same(A.direction_of(t), V.direction_of(t))
    null = rng.standard_normal(300)
    for d in (1, -1):
        for dbl in (True, False):
            same(A.p_leg(null, 0.4, d, dbl), V.p_leg(null, 0.4, d, dbl))
    raises_same(A.p_leg, V.p_leg, np.r_[null, np.nan], 0.1, 1, False)
    g = rng.standard_normal(40)
    M = rng.standard_normal((7, 40))
    for gg in (None, g):
        ra, rh = A.Resid(40, gg), V.Resid(40, gg)
        same(ra.Q, rh.Q)
        same(ra.n_cov, rh.n_cov)
        same(ra(M), rh(M))
        ca, ch = A.CorrStat(v, gg), V.CorrStat(v, gg)
        same(ca.T(M), ch.T(M))
        same(ca.T_maps(M, M[0]), ch.T_maps(M, M[0]))
        same(ca.site_input(), ch.site_input())
        r = float(ca.T(M[1])[0])
        for d in (1, -1):
            same(ca.level0(r, d), ch.level0(r, d))
    for ps in ((0.1, 0.2), (0.1, None), (float("nan"), 0.3), (0.3, float("nan")), (0.05,)):
        same(A.pmax(*ps), H.pmax(*ps))
    raises_same(A.pmax, H.pmax)
    for ids in ([3, 1, 2], np.array([3.0, 1.0]), (5,)):
        same(A.as_parcel_ids(ids), H.as_parcel_ids(ids))
    n_ref = 0
    for bad in (None, [[1, 2]], [1.5, 2], ["a", "b"], [1, 1, 2]):
        raises_same(A.as_parcel_ids, H.as_parcel_ids, bad)
        n_ref += 1
    perm = np.random.default_rng(4).permutation(CA.n)
    same(A.align_to_context(CA, Y[perm], CA.parcel_ids[perm]), H.align_to_context(CH, Y[perm], CH.parcel_ids[perm]))
    same(A.align_to_context(CA, Y[perm], CA.parcel_ids[perm]), Y)
    raises_same(lambda: A.align_to_context(CA, Y[:-1], CA.parcel_ids[:-1]),
                lambda: H.align_to_context(CH, Y[:-1], CH.parcel_ids[:-1]))
    raises_same(lambda: A.align_to_context(CA, Y, CA.parcel_ids + 1000),
                lambda: H.align_to_context(CH, Y, CH.parcel_ids + 1000))
    same(A.sha256_bytes(b"p0"), H.sha256_bytes(b"p0"))
    fp = SCRATCH / "sha_probe.bin"
    fp.write_bytes(b"\x00p0\n" * 1000)
    same(A.sha256_file(fp), H.sha256_file(fp))
    same(A.symbols_background(["g3", "g1", "zz"])(CA.U), H.symbols_background(["g3", "g1", "zz"])(CH.U))
    obj = dict(a=np.arange(3), b=np.float64(1.5), c={2, 1}, d=(np.bool_(True), None, Path("x")), e=np.int64(4))
    same(A.jsonable(obj), SV.jsonable(obj))
    same(A.canon(obj), SV.canon(obj))
    same(A.map_sha(Y, CA.parcel_ids), SV.map_sha(Y, CH.parcel_ids))
    same(A.map_sha(Y), SV.map_sha(Y))
    return dict(refusals_compared=n_ref + 2)


def _ctx_same(a, h):
    for k in ("name", "atlas", "parcel_ids", "classes", "xyz", "X", "G", "D", "brain", "report", "n"):
        same(getattr(a, k), getattr(h, k), f"ctx.{k}")
    same(a.info, h.info, "ctx.info")
    same(a.expr, h.expr, "ctx.expr")
    for k in ("X", "Xw", "U", "Zw", "ZwT32", "mu_w", "mu_B", "mu_N", "d_B", "bshare", "brain", "classes"):
        same(getattr(a.B, k), getattr(h.B, k), f"ctx.B.{k}")
    same(a.U.genes, h.U.genes)
    same(a.U.Z, h.U.Z)
    same(a.reading_class(), h.reading_class())
    same(a.single_class(), h.single_class())


@check("P0a_ClassContext_build_context")
def t_ctx():
    _ctx_same(CA, CH)
    same(CA.score(S25), CH.score(S25))
    keep = CA.parcel_ids[::2]
    _ctx_same(CA.restrict(keep), CH.restrict(keep))
    # reading classes: single-class restrictions
    ctx_ids = CA.parcel_ids[CA.classes == "cortex"]
    _ctx_same(CA.restrict(ctx_ids), CH.restrict(ctx_ids))
    one = toy_inputs(7, sizes=(30,))
    a1, h1 = both_ctx(one, name="dk-ctx", atlas="dk")
    _ctx_same(a1, h1)
    # build_context on patched toy loaders (never the real AHBA / GAMBA files)
    sizes = (34, 8)
    tin = toy_inputs(9, sizes=sizes)
    info = tin["info"].copy()
    info.loc[info.index[-1], "hemisphere"] = "B"  # the midline parcel is brainstem (A1_COUNTS V-DK (42, 1))
    tin["info"] = info
    saved = (e3_plants.primary_parcels, e3_plants.brain_background, A.atlas_info, H.atlas_info)
    calls = []

    def fake_primary(atlas):
        calls.append(atlas)
        return tin["expr"].copy(), tin["info"]["structure"].to_numpy(), tin["xyz"].copy()

    def fake_bg(U):
        return np.array(sorted(U.index[g] for g in tin["brain"] if g in U.index))

    def fake_info(atlas):
        return info.copy()

    try:
        e3_plants.primary_parcels, e3_plants.brain_background = fake_primary, fake_bg
        A.atlas_info, H.atlas_info = fake_info, fake_info
        A._primary.cache_clear()
        H._primary.cache_clear()
        for name in ("V-DK", "dk-ctx"):
            _ctx_same(A.build_context(name, verify=False), H.build_context(name, verify=False))
        sub = tin["expr"].index[:30]
        _ctx_same(A.build_context("V-DK", parcel_ids=sub, verify=False),
                  H.build_context("V-DK", parcel_ids=sub, verify=False))
    finally:
        e3_plants.primary_parcels, e3_plants.brain_background, A.atlas_info, H.atlas_info = saved
        A._primary.cache_clear()
        H._primary.cache_clear()
    return dict(contexts_compared=8, loader_calls=len(calls))


@check("P0a_chunked_species_builders")
def t_chunked():
    Ba, Bh = CA.B, CH.B
    for chunk in (64, 4096):
        same(A.g1_null_chunked(Ba, S25, 300, np.random.default_rng(9), chunk=chunk),
             V.g1_null_chunked(Bh, S25, 300, np.random.default_rng(9), chunk=chunk))
        same(A.g3m_null_chunked(Ba, S25, 300, np.random.default_rng(10), chunk=chunk),
             V.g3m_null_chunked(Bh, S25, 300, np.random.default_rng(10), chunk=chunk))
        f = int(Ba.brain[S25].sum())
        pb = np.setdiff1d(np.flatnonzero(Ba.brain), S25)
        pn = np.setdiff1d(np.flatnonzero(~Ba.brain), S25)
        same(A._g3m_one(Ba, S25, f, pb, pn, np.random.default_rng(11)),
             V._g3m_one(Bh, S25, f, pb, pn, np.random.default_rng(11)))
    # against the engine's unchunked builders (same rng calls)
    d1 = close(A.g1_null_chunked(Ba, S25, 300, np.random.default_rng(9), chunk=64),
               Ba.g1_null(S25, 300, np.random.default_rng(9)), 1e-12, "g1 vs engine")
    d3 = close(A.g3m_null_chunked(Ba, S25, 300, np.random.default_rng(10), chunk=64),
               Ba.g3m_null(S25, 300, np.random.default_rng(10)), 1e-12, "g3m vs engine")
    # the adapters' set generators reproduce the frozen draws bit for bit
    sets1 = np.concatenate(list(AD.g1_set_chunks(Ba.G, S25, 300, np.random.default_rng(9), chunk=37)))
    same(sets1, random_sets(np.arange(Ba.G), len(S25), 300, np.random.default_rng(9), exclude=S25))
    same(Ba.parts(S25)[1][None, :] + Ba.set_means(Ba.Xw, sets1),
         A.g1_null_chunked(Ba, S25, 300, np.random.default_rng(9), chunk=300))
    sets3 = np.concatenate(list(AD.g3m_set_chunks(Ba.brain, S25, 300, np.random.default_rng(10), chunk=37)))
    same(sets3, Ba.g3m_sets(S25, 300, np.random.default_rng(10)))
    same(Ba.parts(S25)[1][None, :] + Ba.set_means(Ba.Xw, sets3),
         A.g3m_null_chunked(Ba, S25, 300, np.random.default_rng(10), chunk=300))
    return dict(engine_g1_max_abs=d1, engine_g3m_max_abs=d3)


@check("P0a_g6l_screen_pool_shared")
def t_g6l():
    Ba, Bh = CA.B, CH.B
    (sa, ia), = A.g6l_screen(Ba, S25, [np.random.default_rng(11)], keep=60)
    (sh, ih), = V.g6l_screen(Bh, S25, [np.random.default_rng(11)], keep=60)
    same(sa, sh)
    same(ia, ih)
    # engine's exact g6l_sets, stream by stream (as A3's docstring states)
    se, ie = Ba.g6l_sets(S25, 60, np.random.default_rng(11), exact=True)
    same(sa, se)
    two_a = A.g6l_screen(Ba, S25, [np.random.default_rng(12), np.random.default_rng(13)], keep=K)
    two_h = V.g6l_screen(Bh, S25, [np.random.default_rng(12), np.random.default_rng(13)], keep=K)
    same(two_a, two_h)
    for (st, it), sd in zip(two_a, (12, 13)):
        (s1, i1), = A.g6l_screen(Ba, S25, [np.random.default_rng(sd)], keep=K)
        same(st, s1)
        same(it, i1)
    same(A.g6l_pool(Ba, S25, sa, ia), V.g6l_pool(Bh, S25, sh, ih))
    same(A.g6l_pool(Ba, S25, None, dict(ia, status="unmatched")),
         V.g6l_pool(Bh, S25, None, dict(ih, status="unmatched")))
    # shared vs unshared screens through the adapters: one screen on ctx.B serves two rows' streams (legs 5 and 25)
    sd_a, sd_b = seeds(31), seeds(32)
    shared = AD.g6l_screen_safe(CA.B, S25, [np.random.default_rng(sd_a("G6l")), np.random.default_rng(sd_b("G6l"))],
                                keep=K)
    rows = []
    for cls, sd, g6 in ((AD.DecodedList, sd_a, shared[0]), (AD.TAbs, sd_b, shared[1]),
                        (AD.SetVsMap, sd_a, shared[0]), (AD.PlsEnrichment, sd_a, shared[0])):
        ad = cls(CA, Y, S25, parcel_ids=CA.parcel_ids)
        un = ad.species_leg(K, sd)
        sh2 = ad.species_leg(K, sd, g6l=g6)
        same(un["p"], sh2["p"], f"{cls.__name__}.p")
        same(un["null"], sh2["null"], f"{cls.__name__}.null")
        same(un["g6l_info"], sh2["g6l_info"], f"{cls.__name__}.g6l_info")
        rows.append((cls.__name__, un["p"]["G6l"][1], un["g6l_info"]["n"]))
    # planted: the TAbs row served by the OTHER row's stream must differ (so the identity above can fail)
    tb = AD.TAbs(CA, Y, S25, parcel_ids=CA.parcel_ids)
    wrong = tb.species_leg(K, sd_b, g6l=shared[0])
    assert not np.array_equal(wrong["null"]["G6l"], tb.species_leg(K, sd_b)["null"]["G6l"]), "swap not detected"
    return dict(n_eligible=int(ia["eligible"]), draws=int(ia["draws"]), shared_rows=rows, swapped_stream_detected=True)


@check("P0a_species_draws")
def t_species_draws():
    out = {}
    for case, S in ((41, S25), (42, np.arange(40, 140, 2))):
        da = A.species_draws(CA, S, K, seeds(case))
        dh = V.species_draws(CH, S, K, seeds(case))
        same(da, dh)
        g6 = A.g6l_screen(CA.B, S, [np.random.default_rng(seeds(case)("G6l"))], keep=K)[0]
        same(A.species_draws(CA, S, K, seeds(case), g6l=g6), da)
        # the adapters' leg-by-leg version (R8 checks) is the same computation
        ds = AD.species_null_scores(CA.B, S, K, seeds(case), screen_basis=CA.B)
        for k in ("null", "floors", "g6s_exact", "n_G6s", "K"):
            same(ds[k], da[k], f"species_null_scores.{k}")
        same(ds["g6l_info"], da["g6l_info"])
        out[f"m{len(S)}"] = dict(g6l=da["g6l_info"]["status"], n6l=da["g6l_info"]["n_used"], g6s_exact=da["g6s_exact"])
    # exact G6s enumeration (2^rank <= K) on a small single-class context
    tiny = toy_inputs(13, sizes=(7,), G=120)
    ta, th = both_ctx(tiny)
    St = np.arange(10)
    same(A.species_draws(ta, St, K, seeds(43)), V.species_draws(th, St, K, seeds(43)))
    out["tiny_g6s_exact"] = bool(ta.B.g6s_exact(K))
    return out


@check("P0a_assemble_claim_verdict")
def t_verdict():
    same(A._g6l_public(dict(status="ok", n=3, extra=1)), V._g6l_public(dict(status="ok", n=3, extra=1)))
    legs = dict(p_G1=0.01, p_G3m=0.02, p_G6s=0.004, p_G6l=0.003)
    sf = {"S1c": 1 / 201, "S2c": 2 / 65}
    spf = dict(G1=1 / 201, G3m=1 / 201, G6s=1 / 201, G6l=1 / 81)
    cases = [(0.01, dict(S1c=0.02, S2c=0.01), sf, legs, spf, "ok", False, 0.025, True),
             (0.01, dict(S1c=0.02, S2c=0.01), sf, legs, spf, "ok", False, 0.025, False),
             (0.01, dict(S1c=0.02, S2c=0.01), sf, legs, spf, "unmatched", False, 0.025, True),
             (0.01, dict(S1c=0.02, S2c=float("nan")), {"S1c": 1 / 201, "S2c": 1 / 201}, legs, spf, "ok", False,
              0.025, False),
             (0.01, dict(S1c=0.002, S2c=0.001), {"S1c": 1 / 201, "S2c": 1 / 201}, legs, spf, "ok", True, 0.025,
              True)]
    for c in cases:
        same(A.assemble_verdict(*c), V.assemble_verdict(*c))
    statuses = []
    g = field(CA, np.random.default_rng(44))
    for kw in (dict(two_sided=True), dict(two_sided=False, direction=1), dict(two_sided=False, direction=-1),
               dict(two_sided=True, g=g)):
        ra = A.claim_verdict(CA, Y, S25, K, seeds(45), parcel_ids=CA.parcel_ids, **kw)
        rh = V.claim_verdict(CH, Y, S25, K, seeds(45), parcel_ids=CH.parcel_ids, **kw)
        same(ra, rh)
        statuses.append((ra["status"], round(ra["p_verdict"], 4) if np.isfinite(ra["p_verdict"]) else None))
    perm = np.random.default_rng(46).permutation(CA.n)
    same(A.claim_verdict(CA, Y[perm], S25, K, seeds(45), parcel_ids=CA.parcel_ids[perm]),
         A.claim_verdict(CA, Y, S25, K, seeds(45), parcel_ids=CA.parcel_ids))
    assert A.claim_verdict.__doc__.startswith("A3 reading")
    return dict(claim_verdict_status_p=statuses)


@check("P0a_PLS1R2_descriptors_reading")
def t_pls_desc():
    rng = np.random.default_rng(47)
    maps = rng.standard_normal((9, CA.n))
    fa, fh = A.PLS1R2(CA.X), V.PLS1R2(CH.X)
    same(fa.K, fh.K)
    same(fa(maps), fh(maps))
    d = close(fa(maps), pls1(CA.X, maps)[1], 1e-12, "PLS1R2 vs cascade.pls1")
    same(A._r2(Y, CA.xyz[:, :2]), V._r2(Y, CA.xyz[:, :2]))
    da = A.descriptors(CA, Y, S25, parcel_ids=CA.parcel_ids)
    same(da, V.descriptors(CH, Y, S25, parcel_ids=CH.parcel_ids))
    gate = dict(name="G-H1", status="evaluated", evaluated=True, false_alarm_failed=False,
                false_alarm_only_m_gt_300=False, tgrad_plant_active_failed=True, other_failed=False,
                makes_planted=["aal-ctx"], failed_false_alarm_gates=[], failed_other_gates=[], tgrad_gate="x",
                not_run=[], n_gates=4, n_false_alarm_gates=2)
    for gt, m, r2 in ((None, 25, 0.1), (gate, 25, 0.3), (dict(gate, evaluated=False), 25, 0.1),
                      (dict(gate, false_alarm_failed=True), 400, 0.1)):
        same(A.apply_gate(gt, m, r2), V.apply_gate(gt, m, r2))
    bad = dict(gate)
    bad.pop("other_failed")
    raises_same(A.apply_gate, V.apply_gate, bad, 25, 0.1)
    raises_same(A.apply_gate, V.apply_gate, dict(gate, name="G-X"), 25, 0.1)
    same(A.NO_A3_GATE, V.NO_A3_GATE)
    same(A.APPLY_GATE_KEYS, V.APPLY_GATE_KEYS)
    # A3's a1_scope_in_force pins the CRLF form of e3_gates_a5.json (h_verdicts.py:136, copied verbatim); a fresh
    # worktree checks the file out LF (.gitattributes eol=lf). Both copies read the CRLF form of the SAME blob: built
    # here from the LF-normalised bytes, held first to L8's LF pin and then to A3's CRLF pin (2026-10-16).
    from a1_audit import launch as LA
    lf = (A.A5_GATES_JSON).read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(lf).hexdigest() == LA.GATES_A5[1], "e3_gates_a5.json differs from L8's LF pin"
    crlf = lf.replace(b"\n", b"\r\n")
    assert hashlib.sha256(crlf).hexdigest() == A.A5_GATES_SHA == LA.GATES_A5[2]
    tmp = SCRATCH / "e3_gates_a5.crlf.json"
    tmp.write_bytes(crlf)
    keep = (A.A5_GATES_JSON, V.A5_GATES_JSON)
    A.A5_GATES_JSON = V.A5_GATES_JSON = tmp
    try:
        scope = A.a1_scope_in_force()
        same(scope, V.a1_scope_in_force())
        rec = A.claim_verdict(CA, Y, S25, K, seeds(48), parcel_ids=CA.parcel_ids)
        for r in (rec, dict(rec, status="ok", survives=True), dict(rec, status="resolution-limited", survives=False)):
            for gt in (None, gate):
                for sc in (scope, None, dict(gradient_classes=["V-AAL"], n1_classes=["V-AAL"])):
                    same(A.reading(r, da, CA, gate=gt, scope=sc), V.reading(r, da, CH, gate=gt, scope=sc))
    finally:
        A.A5_GATES_JSON, V.A5_GATES_JSON = keep
    one = toy_inputs(7, sizes=(30,))
    a1, h1 = both_ctx(one, name="dk-ctx", atlas="dk")
    y1 = field(a1, np.random.default_rng(49))
    d1 = A.descriptors(a1, y1, S25, parcel_ids=a1.parcel_ids)
    same(d1, V.descriptors(h1, y1, S25, parcel_ids=h1.parcel_ids))
    same(A.reading(dict(status="ok", survives=True), d1, a1, reparcellated=True, scope=scope),
         V.reading(dict(status="ok", survives=True), d1, h1, reparcellated=True, scope=scope))
    try:
        A.reading(dict(hypothesis="H3", p_conj=0.1), d1, a1)
        raise AssertionError("H3 record not refused")
    except ValueError:
        pass
    return dict(pls1r2_vs_pls1_max_abs=d, scope_K1=scope["K1_status"])


def _task_fn(key, kw):
    i = kw["i"]
    v = np.random.default_rng(i).standard_normal(4)
    return key, dict(i=i, v=v, s=float(v.sum()), flag=np.bool_(i % 2 == 0))


@check("P0a_Checkpoints_run_pending")
def t_checkpoints():
    quiet = lambda *a, **k: None  # noqa: E731
    vals = np.arange(5, dtype=float)
    res, docs = {}, {}
    jobs_list = (1,) if ARGS.no_loky else (1, 2)
    for impl_name, impl in (("a3", SV), ("port", A)):
        for jobs in jobs_list:
            d = SCRATCH / f"ck_{impl_name}_j{jobs}"
            if d.exists():
                for p in d.iterdir():
                    p.unlink()
            store = impl.Checkpoints(d, "codehash0123", "p0driver")
            tasks = [(f"t{i}", dict(seeds=[i, 9], map_sha=impl.map_sha(vals + i)), dict(i=i)) for i in range(6)]
            out1 = impl.run_pending(tasks, store, _task_fn, jobs, log=quiet)
            out2 = impl.run_pending(tasks, store, _task_fn, jobs, log=quiet)  # resume: every task from its checkpoint
            same(out1, out2)
            res[(impl_name, jobs)] = out1
            docs[(impl_name, jobs)] = {p.name: {k: v for k, v in json.loads(p.read_text(encoding="utf-8")).items()
                                                if k not in ("written", "pid")} for p in sorted(d.glob("ck_*.json"))}
            head = dict(commit="abc", code="codehash0123")
            same(store.run_record(head), canon_impl(impl, head))
            same(store.run_record(head), canon_impl(impl, head))  # resumed: the same identity
    base = res[("a3", 1)]
    for k, v in res.items():
        same(v, base, f"payloads {k}")
        same(docs[k], docs[("a3", 1)], f"checkpoint files {k}")
    # refusals: other expect / other code hash / other driver / unreadable file / other run identity
    da, dh = SCRATCH / "ck_port_j1", SCRATCH / "ck_a3_j1"
    sa, sh = A.Checkpoints(da, "codehash0123", "p0driver"), SV.Checkpoints(dh, "codehash0123", "p0driver")
    n = 0
    raises_same(sa.load, sh.load, "t1", dict(seeds=[1, 8], map_sha="x")); n += 1
    raises_same(A.Checkpoints(da, "other", "p0driver").load, SV.Checkpoints(dh, "other", "p0driver").load, "t1",
                dict(seeds=[1, 9])); n += 1
    raises_same(A.Checkpoints(da, "codehash0123", "drv2").load, SV.Checkpoints(dh, "codehash0123", "drv2").load,
                "t1", {}); n += 1
    raises_same(sa.path, sh.path, "bad key!"); n += 1
    for d in (da, dh):
        (d / "ck_t9.json").write_text("{not json", encoding="utf-8")
    raises_same(sa.load, sh.load, "t9", {}); n += 1
    msgs = []
    for st, d in ((sa, da), (sh, dh)):
        try:
            st.run_record(dict(commit="other", code="codehash0123"))
            raise AssertionError("run_record with another identity not refused")
        except SV.CheckpointError if st is sh else A.CheckpointError as e:
            msgs.append((type(e).__name__, str(e).replace(str(d / "RUN.json"), "<RUN.json>")))
    assert msgs[0] == msgs[1], msgs
    n += 1
    same(sa.load("t0", dict(seeds=[0, 9])), sh.load("t0", dict(seeds=[0, 9])))
    assert sa.load("t_absent", {}) is None and sh.load("t_absent", {}) is None
    return dict(tasks=6, jobs=list(jobs_list), refusals_compared=n, scratch=str(SCRATCH))


def canon_impl(impl, head):
    return impl.canon(head)


# ================================================================================================================
# (b) the set-vs-map statistic on the unstandardised matrix; SetVsMap = A3's claim_verdict legs
# ================================================================================================================
@check("P0b_set_vs_map_statistic")
def t_setvsmap():
    inp = toy_inputs(21, scale=(0.05, 20.0))
    ca, ch = both_ctx(inp, name="V-AAL", atlas="aal")
    sd = ca.X.std(0)
    y = field(ca, np.random.default_rng(22)) + 0.5 * ca.X[:, 3:9].mean(1) / ca.X[:, 3:9].mean(1).std()
    S = np.arange(0, 50, 2)
    ad = AD.SetVsMap(ca, y, S, parcel_ids=ca.parcel_ids)
    direct = float(np.corrcoef(y, ca.X[:, S].mean(1))[0, 1])
    d = abs(ad.T_obs - direct)
    assert d <= 1e-12, f"set-vs-map T {ad.T_obs} != r(y, X[:, S].mean(1)) {direct}"
    rz = float(np.corrcoef(y, AD.zscore_genes(ca.X)[:, S].mean(1))[0, 1])
    assert abs(rz - ad.T_obs) > 1e-6, "the z-scored score gives the same r: the check could not fail"
    # the planted failure: an adapter that z-scored would be caught
    assert abs(rz - direct) > 1e-12
    # SetVsMap legs = A3 claim_verdict one-sided, each direction, bit for bit (production = frozen engine path)
    site = ad.site_leg(K, seeds(23))
    sp = ad.species_leg(K, seeds(23))
    for dr in (1, -1):
        rec = V.claim_verdict(ch, y, S, K, seeds(23), two_sided=False, direction=dr, parcel_ids=ch.parcel_ids)
        same(ad.level0(ad.T_obs, dr), rec["p_level0"])
        same(ad.level0_both()[dr], rec["p_level0"])
        same(site["S1c"]["p"][dr], rec["p_S1c"])
        same(site["S2c"]["p"][dr], rec["p_S2c"])
        for leg in AD.SPECIES_LEGS:
            same(sp["p"][leg][dr], rec[f"p_{leg}"])
        same(ad.T_obs, rec["T"])
        same(sp["floors"], {k[len("species_"):]: v for k, v in rec["floors_raw"].items() if k.startswith("species_")})
        same(max(site["S1c"]["floor"], site["S2c"]["floor"]), rec["floors_raw"]["site"])
        same(float(ad.uninformative()[1]), rec["uninformative_share"])
    return dict(T=ad.T_obs, r_direct=direct, r_zscored_score=rz, abs_diff_z=abs(rz - ad.T_obs),
                gene_sd_range=[float(sd.min()), float(sd.max())], spearman=ad.spearman())


# ================================================================================================================
# value checks: decoded-list (P5), PLS-enrichment (P7), T_abs (P11)
# ================================================================================================================
def per_gene_r(y, X):
    return np.array([np.corrcoef(y, X[:, g])[0, 1] for g in range(X.shape[1])])


def decomp(ad):
    """R2: r_g = r_g^B + r_g^W, the between-class (class means of z_g) and within-class parts."""
    Z, cl = ad.Z, ad.ctx.classes
    Zb = np.empty_like(Z)
    for c in np.unique(cl):
        Zb[cl == c] = Z[cl == c].mean(0)
    rB = Zb.T @ ad.yh / ad.n
    rW = (Z - Zb).T @ ad.yh / ad.n
    return rB, rW


@check("P5_decoded_list")
def t_decoded():
    ad = AD.DecodedList(CA, Y, S25, parcel_ids=CA.parcel_ids)
    rg = per_gene_r(Y, CA.X)
    d_T = close(ad.T_obs, rg[S25].mean(), 1e-12, "T vs mean per-gene r")
    close(ad.r, rg, 1e-12, "per-gene r")
    out = dict(T=ad.T_obs, T_minus_mean_r=d_T)
    rest = np.setdiff1d(np.arange(CA.G), S25)
    for dr, alt in ((1, "greater"), (-1, "less")):
        ref = stats.ttest_ind(rg[S25], rg[rest], equal_var=False, alternative=alt).pvalue
        close(ad.level0(ad.T_obs, dr), ref, 1e-12, f"Welch Level 0 {alt}")
    out["level0"] = ad.level0_both()
    # site leg: every per-gene r recomputed per surrogate (chunked), against direct per-gene Pearson r
    seed = int(np.random.default_rng(seeds(51)("S1c")).integers(2 ** 31))
    sur, _ = site_null(Y, CA.D, CA.classes, 25, seed, "brainsmash")
    Tn = ad.T_maps(sur, chunk=7)
    direct = np.array([per_gene_r(s, CA.X[:, S25]).mean() for s in sur])
    out["site_vs_direct"] = close(Tn, direct, 1e-12, "site T* vs direct per-gene r")
    close(Tn[0], AD.A3.zscore(sur[0]) @ ad.s_z / ad.n, 1e-12, "site T*[0] vs <z(y*), s_z>/n")
    close(ad.T_maps(sur, chunk=1000), Tn, 1e-14, "chunk invariance")
    # species: values = the per-gene decomposition (R2), legs on their own streams
    sd = seeds(52)
    sp = ad.species_leg(K, sd)
    rB, rW = decomp(ad)
    bS = rB[S25].mean()
    sets = {"G1": np.concatenate(list(AD.g1_set_chunks(CA.G, S25, K, np.random.default_rng(sd("G1"))))),
            "G3m": np.concatenate(list(AD.g3m_set_chunks(CA.B.brain, S25, K, np.random.default_rng(sd("G3m"))))),
            "G6l": AD.g6l_screen_safe(CA.B, S25, [np.random.default_rng(sd("G6l"))], keep=K)[0][0]}
    for leg, R in sets.items():
        want = bS + rW[R].mean(1)
        out[f"species_{leg}_vs_decomposition"] = close(sp["null"][leg], want, 1e-12, f"{leg} null vs decomposition")
    Bz = ad.basis
    sstar = Bz.g6s_scores(S25, K, np.random.default_rng(sd("G6s")))
    out["species_G6s_vs_direct"] = close(sp["null"]["G6s"], sstar @ ad.yh / ad.n, 1e-12, "G6s null")
    # the engine's species objects on the z-scored matrix are the decomposition's (s_B(S) + s_W(R))
    close(Bz.parts(S25)[1] @ ad.yh / ad.n, bS, 1e-12, "<y^, s_B(S)>/n = mean r^B")
    # bit-identity of the z-basis draws with the copied species_draws on that basis (screen on ctx.B shared)
    zc = type("Zctx", (), {"B": Bz})()
    g6 = A.g6l_screen(CA.B, S25, [np.random.default_rng(sd("G6l"))], keep=K)[0]
    ref = A.species_draws(zc, S25, K, sd, g6l=g6)
    dz = AD.species_null_scores(Bz, S25, K, sd, screen_basis=CA.B)
    for k in ("null", "floors", "g6s_exact", "n_G6s"):
        same(dz[k], ref[k], f"z-basis draws {k}")
    out["species_p_plus"] = {k: (None if v is None else v[1]) for k, v in sp["p"].items()}
    out["uninformative_share"] = float(ad.uninformative()[1])
    return out


@check("P5_single_class_and_pearson_scoring")
def t_decoded_cond():
    # single class: conditioned = unconditioned (1e-12); R24 Level-2 G1 = species G1
    one = toy_inputs(61, sizes=(34,))
    c1, _ = both_ctx(one, name="dk-ctx", atlas="dk")
    y1 = field(c1, np.random.default_rng(62))
    ad = AD.DecodedList(c1, y1, S25, parcel_ids=c1.parcel_ids)
    sd = seeds(63)
    sp = ad.species_leg(K, sd)
    R1 = np.concatenate(list(AD.g1_set_chunks(c1.G, S25, K, np.random.default_rng(sd("G1")))))
    d_unc = close(sp["null"]["G1"], ad.T_sets(R1), 1e-12, "conditioned vs unconditioned (single class)")
    R3 = np.concatenate(list(AD.g3m_set_chunks(c1.B.brain, S25, K, np.random.default_rng(sd("G3m")))))
    close(sp["null"]["G3m"], ad.T_sets(R3), 1e-12, "G3m conditioned vs unconditioned (single class)")
    l2 = AD.level2_g1(ad, K, sd)
    close(l2["null"], sp["null"]["G1"], 1e-12, "Level-2 G1 vs species G1 (decoded, single class)")
    sv = AD.SetVsMap(c1, y1, S25, parcel_ids=c1.parcel_ids)
    l2s, sps = AD.level2_g1(sv, K, sd), sv.species_leg(K, sd)
    d_l2 = close(l2s["null"], sps["null"]["G1"], 1e-12, "Level-2 G1 vs species G1 (set-vs-map, single class)")
    # multi-class: they differ (the conditioning is in force)
    adm = AD.DecodedList(CA, Y, S25, parcel_ids=CA.parcel_ids)
    spm = adm.species_leg(K, sd)
    Rm = np.concatenate(list(AD.g1_set_chunks(CA.G, S25, K, np.random.default_rng(sd("G1")))))
    diff_multi = float(np.max(np.abs(spm["null"]["G1"] - adm.T_sets(Rm))))
    assert diff_multi > 1e-6, "multi-class: conditioned == unconditioned (conditioning not in force?)"
    # a case where Pearson-r scoring of the same conditioned nulls (the engine's WithinClassBasis._p) gives another p:
    # a coherent module S, y = strong between-class profile of s_B(S) + a weak within-class module pattern
    mod = toy_inputs(5, module=(25, 1.5))
    cm, _ = both_ctx(mod)
    Sm = np.arange(25)
    Bz = AD.z_basis(cm)
    rng = mod["rng"]
    ym = 3.0 * A.zscore(Bz.parts(Sm)[1]) + 0.3 * A.zscore(mod["f"]) + 0.5 * rng.standard_normal(cm.n)
    adp = AD.DecodedList(cm, ym, Sm, parcel_ids=cm.parcel_ids)
    sdp = seeds(64)
    spp = adp.species_leg(K, sdp)
    dz = AD.species_null_scores(Bz, Sm, K, sdp, screen_basis=cm.B)
    r_obs = corr_matrix(ym, adp.s_z)[0, 0]
    pear = {leg: emp_p(corr_matrix(dz["null"][leg], ym)[:, 0], r_obs, 1) for leg in ("G1", "G3m")}
    ours = {leg: spp["p"][leg][1] for leg in ("G1", "G3m")}
    assert any(abs(pear[k] - ours[k]) > 0.05 for k in pear), f"Pearson scoring gives the same p: {pear} {ours}"
    # the engine's own _p gives the Pearson numbers (so the comparison is against the frozen scorer)
    same(Bz._p(Sm, ym, dz["null"]["G1"], 1), pear["G1"])
    return dict(single_class_cond_minus_uncond=d_unc, level2_vs_species_setvsmap=d_l2,
                multi_class_cond_minus_uncond=diff_multi, p_dot=ours, p_pearson=pear)


@check("P7_pls_enrichment")
def t_pls():
    ad = AD.PlsEnrichment(CA, Y, S25, parcel_ids=CA.parcel_ids)
    dec = AD.DecodedList(CA, Y, S25, parcel_ids=CA.parcel_ids)
    # direct: w = Xz^T y_c / ||.|| with genes z-scored (ddof 1), oriented corr(score, y) > 0
    X = CA.X
    Xz = (X - X.mean(0)) / X.std(0, ddof=1)
    w = Xz.T @ (Y - Y.mean())
    w /= np.linalg.norm(w)
    w *= np.sign(np.corrcoef(Xz @ w, Y)[0, 1])
    out = dict(T=ad.T_obs, T_vs_direct=close(ad.T_obs, w[S25].mean(), 1e-12, "PLS T"))
    close(ad.w, w, 1e-12, "PLS1 weights")
    close(ad.w, dec.r / np.linalg.norm(dec.r), 1e-12, "w = r / ||r||")
    # refit on surrogates (chunk 7) = direct per surrogate
    seed = int(np.random.default_rng(seeds(71)("S2c")).integers(2 ** 31))
    sur, _ = site_null(Y, CA.D, CA.classes, 30, seed, "msr")
    Tn = ad.T_maps(sur, chunk=7)
    direct = []
    for s in sur:
        ws = Xz.T @ (s - s.mean())
        ws /= np.linalg.norm(ws)
        ws *= np.sign(np.corrcoef(Xz @ ws, s)[0, 1])
        direct.append(ws[S25].mean())
    out["refit_vs_direct"] = close(Tn, direct, 1e-12, "PLS refit T*")
    # species p = decoded-list species p (constant factor), bit for bit and within 1e-12
    sd = seeds(72)
    sp, sq = ad.species_leg(K, sd), dec.species_leg(K, sd)
    same(sp["p"], sq["p"], "PLS vs decoded species p")
    for leg in AD.SPECIES_LEGS:
        close(sp["null"][leg], ad.kappa * sq["null"][leg], 1e-15, f"{leg} null = kappa x decoded null")
    for dr in (1, -1):
        close(ad.level0(ad.T_obs, dr), dec.level0(dec.T_obs, dr), 1e-12, "PLS Level 0 = decoded Level 0")
    out["species_p_equal"] = True
    other = ad.species_leg(K, seeds(73))  # planted: another row's streams give other p's (the equality can fail)
    assert any(other["p"][leg] != sq["p"][leg] for leg in AD.SPECIES_LEGS), "other streams gave identical p's"
    out["level0_pls_vs_decoded"] = abs(ad.level0(ad.T_obs, 1) - dec.level0(dec.T_obs, 1))
    return out


@check("P11_t_abs")
def t_tabs():
    ad = AD.TAbs(CA, Y, S25, parcel_ids=CA.parcel_ids)
    rg = np.abs(per_gene_r(Y, CA.X))
    out = dict(T=ad.T_obs, T_vs_direct=close(ad.T_obs, rg[S25].mean(), 1e-12, "T_abs"))
    rest = np.setdiff1d(np.arange(CA.G), S25)
    for dr, alt in ((1, "greater"), (-1, "less")):
        close(ad.level0(ad.T_obs, dr), stats.ttest_ind(rg[S25], rg[rest], equal_var=False, alternative=alt).pvalue,
              1e-12, f"T_abs Level 0 {alt}")
    seed = int(np.random.default_rng(seeds(81)("S1c")).integers(2 ** 31))
    sur, _ = site_null(Y, CA.D, CA.classes, 20, seed, "brainsmash")
    out["site_vs_direct"] = close(ad.T_maps(sur, chunk=3),
                                  [np.abs(per_gene_r(s, CA.X[:, S25])).mean() for s in sur], 1e-12, "T_abs site")
    sd = seeds(82)
    sp = ad.species_leg(K, sd, chunk=50)
    assert set(sp["null"]) == {"G1", "G3m", "G6l"} and sp["conditioned"] is False
    R1 = random_sets(np.arange(CA.G), len(S25), K, np.random.default_rng(sd("G1")), exclude=S25)
    R3 = CA.B.g3m_sets(S25, K, np.random.default_rng(sd("G3m")))
    R6 = AD.g6l_screen_safe(CA.B, S25, [np.random.default_rng(sd("G6l"))], keep=K)[0][0]
    for leg, R in (("G1", R1), ("G3m", R3), ("G6l", R6)):
        out[f"{leg}_vs_direct"] = close(sp["null"][leg], rg[R].mean(1), 1e-12, f"T_abs {leg}")
        for dr in (1, -1):  # p in both directions = (k + 1)/(n + 1) on the direct values
            k = int(np.sum(dr * rg[R].mean(1) >= dr * ad.T_obs))
            close(sp["p"][leg][dr], (k + 1) / (len(R) + 1), 0.0, f"T_abs {leg} p({dr})")
    assert AD.TAbs.registered_direction() == 1 and AD.TAbs.registered_direction(depletion=True) == -1
    out["p_upper"] = {k: v[1] for k, v in sp["p"].items()}
    return out


@check("P12_component_forms")
def t_components():
    from sklearn.cross_decomposition import PLSRegression
    rng = np.random.default_rng(91)
    comp = field(CA, rng)
    fc = AD.FixedComponent(CA, Y, comp, parcel_ids=CA.parcel_ids)
    out = dict(fixed_r=fc.T_obs, fixed_vs_direct=close(fc.T_obs, np.corrcoef(Y, comp)[0, 1], 1e-12, "fixed r"))
    for dr in (1, -1):
        close(fc.level0(fc.T_obs, dr), naive_p(fc.T_obs, CA.n, dr), 1e-15, "fixed Level 0 = naive_p")
    seed = int(np.random.default_rng(seeds(92)("S1c")).integers(2 ** 31))
    sur, _ = site_null(Y, CA.D, CA.classes, 12, seed, "brainsmash")
    close(fc.T_maps(sur), [np.corrcoef(s, comp)[0, 1] for s in sur], 1e-12, "fixed r on surrogates")
    p1 = AD.Pls1R2(CA, Y, parcel_ids=CA.parcel_ids)
    out["pls1_r2"] = p1.T_obs
    close(p1.T_obs, pls1(CA.X, Y)[1][0], 1e-12, "PLS1 R2 vs cascade.pls1")
    out["pls1_refit_vs_direct"] = close(p1.T_maps(sur, chunk=5), pls1(CA.X, sur)[1], 1e-12, "PLS1 R2 refit")
    pn = p1.permutation_null(15, np.random.default_rng(93))
    Yp = np.random.default_rng(93).permuted(np.tile(Y, (15, 1)), axis=1)
    close(pn, pls1(CA.X, Yp)[1], 1e-12, "PLS1 R2 permutation refit")
    lp = p1.level0_perm(15, seeds(94))
    assert set(lp["p"]) == {1, -1}
    one = AD.PlsrComponent(CA, Y, parcel_ids=CA.parcel_ids, n_components=1, component=1)
    close(one.T_obs, p1.T_obs, 1e-12, "PLSRegression(1) component 1 = PLS1 R2")
    worst = 0.0
    genes = np.arange(0, 120, 3)  # a gene subset (MOR-like: the locus genes)
    for Kc, k, cum, gs in ((3, 3, False, None), (3, 2, False, None), (2, None, True, None), (2, None, True, genes)):
        pr = AD.PlsrComponent(CA, Y, parcel_ids=CA.parcel_ids, n_components=Kc, component=k, cumulative=cum,
                              genes=gs)
        Xm = CA.X if gs is None else CA.X[:, gs]
        maps = np.vstack([Y, sur[:5], Yp[:5]])
        got = pr.T_maps(maps, chunk=4)
        want = []
        for mp in maps:
            m = PLSRegression(Kc, scale=True).fit(Xm, mp)
            r2 = [np.corrcoef(m.x_scores_[:, j], mp)[0, 1] ** 2 for j in range(Kc)]
            want.append(sum(r2) if cum else r2[k - 1])
            if cum:  # the cumulative R2 is the fitted model's R2
                pred = m.predict(Xm).ravel()
                close(sum(r2), 1 - ((mp - pred) ** 2).sum() / ((mp - mp.mean()) ** 2).sum(), 1e-12, "cum R2 = model R2")
        worst = max(worst, close(got, want, 1e-12, f"PLSR K={Kc} k={k} cum={cum}"))
    out["plsr_vs_sklearn_max_abs"] = worst
    for bad in (dict(n_components=2), dict(n_components=2, component=3), dict(n_components=2, component=1,
                                                                               cumulative=True)):
        try:
            AD.PlsrComponent(CA, Y, parcel_ids=CA.parcel_ids, **bad)
            raise AssertionError(f"PLSR {bad} not refused")
        except ValueError:
            pass
    for f in (lambda: fc.species_leg(K, seeds(1)), lambda: fc.permutation_null(5, rng), lambda: p1.level0_both()):
        try:
            f()
            raise AssertionError("component misuse not refused")
        except TypeError:
            pass
    return out


@check("R8_pools_never_crash")
def t_r8():
    out = {}
    big = np.arange(160)  # m > G/2: G1 pool < m and no G6l window fits
    st = AD.pool_status(CA.B, big)
    assert not st["G1"] and st["G6l"] == "no window", st
    for cls in (AD.SetVsMap, AD.DecodedList, AD.TAbs):
        ad = cls(CA, Y, big, parcel_ids=CA.parcel_ids)
        sp = ad.species_leg(K, seeds(101))
        assert sp["null"]["G1"] is None and sp["status"]["G1"] == AD.NOT_COMPUTABLE
        assert sp["status"]["G6l"] == "unmatched" and sp["null"]["G6l"] is None
        if cls is not AD.TAbs:
            assert sp["null"]["G6s"] is not None and sp["p"]["G6s"] is not None  # G6s needs no pool
        out[cls.__name__] = dict(sp["status"])
        assert ad.site_leg(50, seeds(101))["S1c"]["p"][1] > 0  # every computable leg is still computed
    assert AD.level2_g1(AD.SetVsMap(CA, Y, big, parcel_ids=CA.parcel_ids), K, seeds(101))["status"] == AD.NOT_COMPUTABLE
    # G3m: f > |B \ S| (all 50 brain genes of the toy in S, plus 10 others: f = 50, |B \ S| = 0)
    Sb2 = np.concatenate([np.flatnonzero(CA.B.brain), np.flatnonzero(~CA.B.brain)[:10]])
    stb = AD.pool_status(CA.B, Sb2)
    assert stb["G1"] and not stb["G3m"], stb
    sp = AD.DecodedList(CA, Y, Sb2, parcel_ids=CA.parcel_ids).species_leg(K, seeds(102))
    assert sp["null"]["G3m"] is None and sp["status"]["G3m"] == AD.NOT_COMPUTABLE and sp["null"]["G1"] is not None
    out["G3m_case"] = dict(sp["status"])
    # a window that fits only part of [0, half]: RUN_PLAN_amend_1 R33 -> offsets o <= n_rank - m + 1, no exception
    mid = np.arange(120)  # G = 300: n_rank 179, half 89, half + m - 1 = 208 > 179 >= m - 1; o_max = 60
    assert AD.pool_status(CA.B, mid)["G6l"] == "partial"
    (sets, info), = AD.g6l_screen_safe(CA.B, mid, [np.random.default_rng(1)], keep=K)
    assert info["offsets"]["o_max"] == 60 and info["offsets"]["partial"] is True, info.get("offsets")
    if sets is not None:
        assert sets.shape[1] == mid.size and all(np.unique(w).size == mid.size and not np.isin(w, mid).any()
                                                 for w in sets)
    out["partial_window"] = dict(status=info["status"], eligible=info["eligible"], o_max=info["offsets"]["o_max"])
    return out


@check("descriptor_scoring_T_sets_maps_pairs")
def t_descriptor_scoring():
    rng = np.random.default_rng(111)
    sets = np.stack([rng.choice(CA.G, 25, replace=False) for _ in range(6)])
    seed = int(np.random.default_rng(seeds(112)("S1c")).integers(2 ** 31))
    maps, _ = site_null(Y, CA.D, CA.classes, 6, seed, "brainsmash")
    X = CA.X
    Xz = (X - X.mean(0)) / X.std(0, ddof=1)
    out = {}
    for cls in (AD.SetVsMap, AD.DecodedList, AD.PlsEnrichment, AD.TAbs):
        ad = cls(CA, Y, S25, parcel_ids=CA.parcel_ids)

        def T_direct(R, mp):
            if cls is AD.SetVsMap:
                return np.corrcoef(mp, X[:, R].mean(1))[0, 1]
            if cls is AD.PlsEnrichment:
                ws = Xz.T @ (mp - mp.mean())
                ws /= np.linalg.norm(ws)
                return (ws * np.sign(np.corrcoef(Xz @ ws, mp)[0, 1]))[R].mean()
            r = per_gene_r(mp, X[:, R])
            return (np.abs(r) if cls is AD.TAbs else r).mean()

        close(ad.T_sets(sets, chunk=4), [T_direct(R, Y) for R in sets], 1e-12, f"{cls.__name__} T_sets")
        TM = ad.T_sets_maps(sets, maps, chunk=4)
        close(TM, [[T_direct(R, mp) for R in sets] for mp in maps], 1e-12, f"{cls.__name__} T_sets_maps")
        close(ad.T_pairs(sets, maps, chunk=4), [T_direct(R, mp) for R, mp in zip(sets, maps)], 1e-12,
              f"{cls.__name__} T_pairs")
        close(ad.T_sets(S25[None, :]), ad.T_obs, 1e-12, f"{cls.__name__} T_sets(S) = T")
        out[cls.__name__] = "ok"
    return out


@check("analysis_parcels_prepare_matrix")
def t_parcels():
    ids = INP["expr"].index.to_numpy()
    yv = pd.Series(Y.copy(), index=ids)
    yv.iloc[[2, 5]] = np.nan
    counts = {int(i): 3 for i in ids}
    counts[int(ids[7])] = 0
    counts[int(ids[5])] = 0
    rep = AD.analysis_parcels(yv, counts)
    assert rep["n_given"] == len(ids) and rep["n_kept"] == len(ids) - 3, rep
    assert rep["n_dropped_nonfinite"] == 2 and rep["n_dropped_no_sample"] == 2 and rep["n_dropped"] == 3
    assert rep["parcel_ids"] == [int(i) for i in ids if i not in (ids[2], ids[5], ids[7])]
    rep2 = AD.analysis_parcels(Y, {**counts, int(ids[0]): 1}, parcel_ids=ids, min_count=2)
    assert rep2["n_dropped_no_sample"] == 3 and rep2["n_kept"] == len(ids) - 3
    for bad in (dict(y=yv, c={int(i): 1 for i in ids[1:]}), dict(y=yv, c={**counts, int(ids[0]): -1}),
                dict(y=yv, c={**counts, int(ids[0]): 1.5})):
        try:
            AD.analysis_parcels(bad["y"], bad["c"])
            raise AssertionError("bad counts not refused")
        except ValueError:
            pass
    expr = INP["expr"].copy()
    expr["const"] = 1.0
    keep = rep["parcel_ids"]
    sv, info_sv = AD.prepare_matrix("set-vs-map", expr, keep)
    assert info_sv["n_dropped_constant"] == 1 and "const" not in sv.columns
    same(sv.to_numpy(), expr.loc[keep].drop(columns="const").to_numpy())
    dl, info_dl = AD.prepare_matrix("decoded-list", expr, keep)
    close(dl.to_numpy().mean(0), 0, 1e-12, "z-scored mean")
    close(dl.to_numpy().std(0), 1, 1e-12, "z-scored sd")
    # the adapters' z-scored matrix is prepare_matrix's on the same parcels
    sub = CA.restrict(keep)
    same(AD.z_matrix(sub), AD.prepare_matrix("decoded-list", INP["expr"], keep)[0].to_numpy())
    same(AD.prepare_matrix("component", expr, keep)[0].to_numpy(), sv.to_numpy())
    for f in ("PLS-enrichment", "t-abs"):
        same(AD.prepare_matrix(f, expr, keep)[0].to_numpy(), dl.to_numpy())
    try:
        AD.prepare_matrix("set-vs-map", expr, [999999])
        raise AssertionError("unknown parcel not refused")
    except ValueError:
        pass
    return dict(kept=rep["n_kept"], dropped=rep["n_dropped"], nonfinite=rep["n_dropped_nonfinite"],
                no_sample=rep["n_dropped_no_sample"], scaling={k: v["scaling"][:40] for k, v in
                                                                (("set-vs-map", info_sv), ("decoded-list", info_dl))})


def main() -> int:
    t0 = time.time()
    print(f"P0 test: scratch {SCRATCH}; HEAD {git('rev-parse', '--short', 'HEAD').decode().strip()}", flush=True)
    for run in CHECKS:
        run()
    out = SCRATCH / "test_p0_results.json"
    out.write_text(json.dumps(dict(results=RESULTS, failed=FAILED, seconds=round(time.time() - t0, 1)),
                              indent=1, default=_num) + "\n", encoding="utf-8", newline="\n")
    back = json.loads(out.read_text(encoding="utf-8"))
    assert back["failed"] == FAILED
    print(f"{len(CHECKS) - len(FAILED)} of {len(CHECKS)} checks passed ({time.time() - t0:.0f}s); results {out}",
          flush=True)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
