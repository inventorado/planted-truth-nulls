"""A3's audit-scale helpers, copied (RUN_PLAN.md v3.1 §3 inventory row (3); §4).

Every block below a '# ported from <path>:<line> (git blob <id> at HEAD <short>)' marker is that blob's text, line for
line, from that line on; a copied block is never edited by hand (re-copy it from its blob instead). tests/test_p0.py
re-reads each blob and asserts the text identity, then the bit-identity of every copied function against the A3
function on toy data (P0 (a)). Runner code imports THIS module, never arcs/replication (§3: A3's readings, such as its
two-sided rule, differ from A1's, R1).

Lines outside the blocks are the import lines, the only lines that differ from the sources:
- h_common.py:57 ROOT = parents[3] is written here as parents[4] (this file sits one directory deeper; the same
  repository root);
- h_verdicts.py:123 "import h_common as H" is written as H = sys.modules[__name__] (the h_common copies live in this
  module, so H.<name> in the copied h_verdicts code resolves to them unchanged);
- the engine (src/asdg) is imported, never copied; e3_plants (A1's own plant module, arcs/audit/src) is imported as
  h_common.py:61 does.
A3 READINGS (not A1's verdict rule; RUN_PLAN R1, §19): direction_of, p_leg (doubled), assemble_verdict and
claim_verdict embody A3's two-sided rule (direction = sign of the observed T; that p doubled). They are copied for the
P0 bit-identity test only; their __doc__ is prefixed at import (A3_READINGS at the end) and no A1 verdict path calls
them.
"""
from __future__ import annotations

import os

# ported from arcs/replication/src/h_common.py:43 (git blob 220e5c6aafa99c007db87815e6a5a1bf3a163493 at HEAD 86edcad)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import datetime as _dt  # noqa: E402  (step3v_common.py:62)
import functools  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]  # import-line adaptation of h_common.py:57 (parents[3]): one level deeper
# ported from arcs/replication/src/h_common.py:58 (git blob 220e5c6aafa99c007db87815e6a5a1bf3a163493 at HEAD 86edcad)
for _p in (ROOT / "src", ROOT / "arcs" / "audit" / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import e3_plants as P  # noqa: E402  (h_common.py:61)
from asdg.genesets import Universe, MIN_SET  # noqa: E402,F401  (h_common.py:62)
from asdg.spatial import centroid_distance  # noqa: E402  (h_common.py:63)
from asdg.species import WithinClassBasis  # noqa: E402  (h_common.py:64)
from asdg.cascade import corr_matrix, emp_p, pls1, _rows_z  # noqa: E402,F401  (h_verdicts.py:124)
from asdg.spatial import site_null  # noqa: E402  (h_verdicts.py:125)
from asdg.verdict import verdict as a1_verdict  # noqa: E402  (h_verdicts.py:126)

H = sys.modules[__name__]  # h_verdicts.py:123 "import h_common as H": the h_common copies are in this module


# ported from arcs/replication/src/h_common.py:66 (git blob 220e5c6aafa99c007db87815e6a5a1bf3a163493 at HEAD 86edcad)
AHBA = ROOT / "artifacts" / "ahba"
ALPHA_V = 0.025
SEED0 = 20260925


# ported from arcs/replication/src/h_common.py:70 (git blob 220e5c6aafa99c007db87815e6a5a1bf3a163493 at HEAD 86edcad)
# ---- apparatus constants (prereg §3.1, §3.3; arcs/audit/results/e4_ahba_matrices.json) ----------------------------
MATRIX_SHA = {"dk": "9c66a2058896061fd3630fdad15abe121fc1148ac7160181b200cb0fb7d9b1b2",
              "aal": "0dbbb50ca9a60647b7dc49477c905dbb49631be0f42f74889039f8d8d7bb6a00",
              "ho": "e2defcbb7c6c7c841cfb488a96d41c43492da89a96e17303868fb0ff8030152a",
              "cc200": "787eaa06e43227bf9030c93ff14d2f435bae77f9e6e78e7c4604dc6325ffecfe"}
N_GENES = 15633
PROGRAMS_JSON = ROOT / "arcs" / "replication" / "frozen" / "programs.json"
PROGRAMS_SHA = "a9a7a396eea215e200c9f1f79a1f5f022abb131ba1ae797df32b4c2fa26fb90e"

# name -> (atlas, cortex only); the registered parcel counts of the prereg (§3.1 V-AAL 54; §11 aal-ctx 38; A1 dk-ctx 34)
CLASS_DEFS = {"V-DK": ("dk", False), "V-AAL": ("aal", False), "aal-ctx": ("aal", True), "dk-ctx": ("dk", True),
              "V-HO": ("ho", False), "ho-ctx": ("ho", True), "V-CC200": ("cc200", False),
              "cc200-ctx": ("cc200", True)}
REGISTERED_COUNTS = {"V-DK": 42, "V-AAL": 54, "aal-ctx": 38, "dk-ctx": 34}
# A1's construction on every class (apparatus checks; HO / CC200 counts are not prereg-registered): (parcels, of them
# midline, i.e. atlas hemisphere 'B')
A1_COUNTS = {"V-DK": (42, 1), "V-AAL": (54, 0), "aal-ctx": (38, 0), "dk-ctx": (34, 0), "V-HO": (54, 0),
             "ho-ctx": (47, 0), "V-CC200": (107, 17), "cc200-ctx": (88, 13)}
PLANTED_CLASSES = ("V-AAL", "V-DK", "V-CC200", "dk-ctx")  # amendment 5 §3; aal-ctx only after G-H1 passes (A3 §6)
CTX_REPLICA = {"dk": "dk-ctx", "aal": "aal-ctx", "ho": "ho-ctx", "cc200": "cc200-ctx"}  # all-cortical claims (READINGS)
MULTI_CLASS = {"V-DK": "dk", "V-AAL": "aal", "V-HO": "ho", "V-CC200": "cc200"}
MODULE_SEED_ATLAS = {"dk": "dk", "aal": "aal", "cc200": "cc200"}  # asdg.modules.CLASS_SEED keys (aal-ctx: V-AAL's)


# ported from arcs/replication/src/h_common.py:94 (git blob 220e5c6aafa99c007db87815e6a5a1bf3a163493 at HEAD 86edcad)
def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ported from arcs/replication/src/h_common.py:106 (git blob 220e5c6aafa99c007db87815e6a5a1bf3a163493 at HEAD 86edcad)
# ---- A1's matrices, read once per process ----------------------------------------------------------------------------
@functools.lru_cache(maxsize=None)
def _primary(atlas: str):
    expr, classes, xyz = P.primary_parcels(atlas)  # A1's reader (default float parsing, as A1's gates used)
    return expr, np.asarray(classes), np.asarray(xyz, dtype=float)


@functools.lru_cache(maxsize=None)
def atlas_info(atlas: str) -> pd.DataFrame:
    return pd.read_csv(AHBA / f"{atlas}_atlas_info.csv").set_index("id")


@functools.lru_cache(maxsize=None)
def verify_matrix(atlas: str) -> dict:
    """Apparatus assertion: the committed matrix is the prereg's (§3.1 sha256, e4_ahba_matrices.sha on a round-trip
    read; 15,633 genes). A1's own reader parses the same file with default float parsing (max |delta| 1.1e-16)."""
    path = AHBA / f"{atlas}_expr.csv.gz"
    rt = pd.read_csv(path, index_col=0, float_precision="round_trip")
    h = hashlib.sha256(pd.util.hash_pandas_object(rt, index=True).to_numpy().tobytes()).hexdigest()
    assert h == MATRIX_SHA[atlas], f"{atlas}: matrix sha256 {h} != prereg {MATRIX_SHA[atlas]}"
    assert rt.shape[1] == N_GENES, f"{atlas}: {rt.shape[1]} genes != {N_GENES}"
    expr = _primary(atlas)[0]
    assert list(expr.columns) == list(rt.columns), f"{atlas}: gene order differs between readers"
    d = float(np.nanmax(np.abs(rt.loc[expr.index].to_numpy() - expr.to_numpy())))
    assert d < 1e-12, f"{atlas}: A1 reader vs round-trip max |delta| {d}"
    return dict(matrix_sha256=h, file_sha256=sha256_file(path), reader_max_abs_delta=d, n_genes=int(rt.shape[1]))


def symbols_background(symbols):
    """A brain-background function for synthetic contexts: the given symbols' indices in a universe."""
    sym = frozenset(symbols)
    return lambda U: np.array(sorted(U.index[g] for g in sym if g in U.index), dtype=int)


# ported from arcs/replication/src/h_common.py:140 (git blob 220e5c6aafa99c007db87815e6a5a1bf3a163493 at HEAD 86edcad)
# ---- class contexts ----------------------------------------------------------------------------------------------
class ClassContext:
    """One class over its analysis parcels: X (parcels x genes, A1's Universe), tissue classes, centroids, D, the
    brain>body background B (indices into the universe; A1's e3_plants.brain_background by default) and A1's
    WithinClassBasis. Parcel order = A1's primary-parcel order (the matrix index order) whatever order parcel ids are
    given in."""

    def __init__(self, name: str, expr: pd.DataFrame, classes, xyz, info: pd.DataFrame, brain_fn=None,
                 atlas: str | None = None, report: dict | None = None):
        self.name, self.atlas = name, atlas
        self.expr = expr
        self.parcel_ids = np.asarray(expr.index, dtype=int)
        self.classes = np.asarray(classes)
        self.xyz = np.asarray(xyz, dtype=float)
        assert len(self.classes) == len(self.parcel_ids) == len(self.xyz), "parcels / classes / centroids differ"
        self.info = info.loc[self.parcel_ids, ["label", "hemisphere", "structure"]].copy()
        self.brain_fn = P.brain_background if brain_fn is None else brain_fn
        self.U = Universe(expr)
        self.X = self.U.X
        self.G = self.X.shape[1]
        self.D = centroid_distance(self.xyz)
        self.brain = np.asarray(self.brain_fn(self.U), dtype=int)
        self.B = WithinClassBasis(self.X, self.classes, brain=self.brain)
        self.report = dict(report or {})
        self.report.update(name=name, atlas=atlas, n_parcels=int(len(self.parcel_ids)),
                           class_counts={str(c): int((self.classes == c).sum()) for c in np.unique(self.classes)},
                           n_midline=int((self.info["hemisphere"].astype(str) == "B").sum()),
                           n_genes=int(self.G), n_dropped_constant=int(self.U.n_dropped_constant),
                           n_brain=int(self.brain.size), parcel_ids=[int(i) for i in self.parcel_ids])

    @property
    def n(self) -> int:
        return len(self.parcel_ids)

    def restrict(self, parcel_ids) -> "ClassContext":
        """The same class on a subset of its parcels (a claim's analysis parcels), rebuilt from the matrix rows."""
        want = {int(i) for i in parcel_ids}
        missing = sorted(want - set(self.parcel_ids.tolist()))
        assert not missing, f"{self.name}: parcels not in the class: {missing}"
        keep = np.array([i in want for i in self.parcel_ids])
        return ClassContext(self.name, self.expr.loc[keep], self.classes[keep], self.xyz[keep], self.info,
                            self.brain_fn, self.atlas,
                            {**{k: v for k, v in self.report.items() if k in ("matrix_sha256", "file_sha256")},
                             "restricted_from": int(len(self.parcel_ids))})

    def reading_class(self) -> str:
        """The class a claim here is read in (amendment 5 §4.3; module READINGS): an all-cortical claim reads in its
        atlas's cortex-only replica (dk-ctx, aal-ctx, ho-ctx, cc200-ctx) whatever class it was restricted from; any
        other single-class restriction of a multi-class class reads as '<class> (single class: <tissue>)' (outside the
        planted classes); every other claim keeps its class name. (The atlas of a synthetic context without one is
        taken from its class name.)"""
        cls = {str(c) for c in np.unique(self.classes)}
        atlas = self.atlas or MULTI_CLASS.get(self.name)
        if cls == {"cortex"} and atlas in CTX_REPLICA:
            return CTX_REPLICA[atlas]
        if len(cls) == 1 and self.name in MULTI_CLASS:
            return f"{self.name} (single class: {next(iter(cls))})"
        return self.name

    def single_class(self) -> bool:
        return len(np.unique(self.classes)) == 1

    def score(self, S) -> np.ndarray:
        return self.X[:, np.asarray(S, dtype=int)].mean(1)

    def program_set(self, name: str) -> tuple[np.ndarray | None, dict]:
        """(gene indices or None, info): the program's genes as published, present in this class universe; fewer
        than 5 -> 'not testable'."""
        entry = programs()["programs"][name]
        idx, info = self.U.testable_set(entry["genes"])
        info.update(program=name, program_index=program_index(name), m=int(info["n_present"]),
                    testable=info["status"] == "ok", n_listed=int(entry["n_listed"]))
        return idx, info

    @functools.cached_property
    def modules(self) -> list[np.ndarray]:
        """A1's k = 64 module generator on this class's parcels (asdg.modules.class_modules; aal-ctx uses V-AAL's
        seed 20260925 as prereg §10.3 states, dk-ctx V-DK's). For gate targets only; never a statistic here."""
        from asdg.modules import class_modules
        return class_modules(self.X, MODULE_SEED_ATLAS[self.atlas])


def build_context(name: str, parcel_ids=None, verify: bool = True) -> ClassContext:
    """A class context exactly as A1 builds its classes (see the module docstring)."""
    atlas, cortex_only = CLASS_DEFS[name]
    expr, classes, xyz = _primary(atlas)
    keep = np.ones(len(expr), bool)
    if cortex_only:
        keep &= classes == "cortex"
    rep = verify_matrix(atlas) if verify else {}
    ctx = ClassContext(name, expr.loc[keep], classes[keep], xyz[keep], atlas_info(atlas), None, atlas, rep)
    if name in REGISTERED_COUNTS:
        assert ctx.n == REGISTERED_COUNTS[name], f"{name}: {ctx.n} parcels != registered {REGISTERED_COUNTS[name]}"
    if name in A1_COUNTS:  # A1's construction, midline parcels included (module READINGS)
        assert (ctx.n, ctx.report["n_midline"]) == A1_COUNTS[name], \
            f"{name}: {ctx.n} parcels ({ctx.report['n_midline']} midline) != A1's {A1_COUNTS[name]}"
    if name == "V-DK":
        assert ctx.report["class_counts"] == {"cortex": 34, "subcortex/brainstem": 8}, ctx.report["class_counts"]
    if name == "V-AAL":
        assert ctx.report["class_counts"] == {"cerebellum": 9, "cortex": 38, "subcortex/brainstem": 7}
    if verify:  # apparatus: no constant gene dropped in a registered class; universe = the 15,633 genes
        assert ctx.U.n_dropped_constant == 0 and ctx.G == N_GENES, (ctx.U.n_dropped_constant, ctx.G)
    return ctx if parcel_ids is None else ctx.restrict(parcel_ids)


# ported from arcs/replication/src/h_common.py:245 (git blob 220e5c6aafa99c007db87815e6a5a1bf3a163493 at HEAD 86edcad)
# ---- programs (frozen/programs.json) -----------------------------------------------------------------------------
@functools.lru_cache(maxsize=None)
def programs() -> dict:
    data = PROGRAMS_JSON.read_bytes()
    h = sha256_bytes(data)
    assert h == PROGRAMS_SHA, f"programs.json sha256 {h} != prereg §3.3 {PROGRAMS_SHA}"
    return json.loads(data.decode("utf-8"))


def program_names() -> list[str]:
    return list(programs()["programs"])


def program_index(name: str) -> int:
    """0-based position of the program in programs.json's `programs` mapping (file order)."""
    return program_names().index(name)


# ported from arcs/replication/src/h_common.py:398 (git blob 220e5c6aafa99c007db87815e6a5a1bf3a163493 at HEAD 86edcad)
def pmax(*ps) -> float:
    """NaN-aware max of p's (conjunctions, leg maxima): NaN if any member is None or NaN, else the max. Python's
    built-in max keeps a NaN only when it comes first (max(.01, nan) = .01), so a missing leg could vanish from a
    conjunction; this never lets it."""
    if not ps:
        raise ValueError("pmax of nothing")
    vals = [float("nan") if p is None else float(p) for p in ps]
    return float("nan") if any(math.isnan(v) for v in vals) else max(vals)


# ---- maps matched to parcels by id, never by position (review finding 4) ------------------------------------------
def as_parcel_ids(parcel_ids, what: str = "map") -> np.ndarray:
    """Parcel ids as a 1-D int64 array; refuses None, non-integer, non-1-D and duplicated ids."""
    if parcel_ids is None:
        raise ValueError(f"{what}: parcel ids are required (maps are matched to parcels by id, never by position)")
    a = np.asarray(parcel_ids)
    if a.ndim != 1:
        raise ValueError(f"{what}: parcel ids must be a 1-D sequence, got shape {a.shape}")
    if a.dtype.kind not in "iu":
        try:
            f = a.astype(float)
        except (TypeError, ValueError) as e:
            raise ValueError(f"{what}: parcel ids must be integers ({e})") from None
        if not (np.isfinite(f).all() and np.array_equal(f, np.round(f))):
            raise ValueError(f"{what}: parcel ids must be integers")
        a = f
    a = a.astype(np.int64)
    u, c = np.unique(a, return_counts=True)
    if (c > 1).any():
        raise ValueError(f"{what}: duplicated parcel ids {u[c > 1].tolist()}")
    return a


def align_to_context(ctx: ClassContext, values, parcel_ids, what: str = "map") -> np.ndarray:
    """A map's values, given in the order of its own parcel ids, reordered to ctx's class order (ctx.parcel_ids).
    Refuses (ValueError) a map whose id set differs from the context's in either direction: the caller restricts the
    class to the map's parcels first (ClassContext.restrict; intersect_maps for two maps). Values are not otherwise
    touched (finiteness is the verdict's own check)."""
    v = np.asarray(values, dtype=float)
    ids = as_parcel_ids(parcel_ids, what)
    if v.ndim != 1 or v.shape != ids.shape:
        raise ValueError(f"{what}: {v.shape} values for {ids.size} parcel ids")
    want = np.asarray(ctx.parcel_ids, dtype=np.int64)
    if np.array_equal(ids, want):
        return v
    have, need = set(ids.tolist()), set(want.tolist())
    if have != need:
        raise ValueError(f"{what}: parcel ids differ from context {ctx.name} ({ctx.n} parcels): missing from the map "
                         f"{sorted(need - have)}; not in the context {sorted(have - need)}. Restrict the class to the "
                         f"map's parcels first (ClassContext.restrict / intersect_maps)")
    pos = {p: k for k, p in enumerate(ids.tolist())}
    return v[np.array([pos[p] for p in want.tolist()], dtype=int)]


# ported from arcs/replication/src/h_verdicts.py:128 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
ALPHA_V = H.ALPHA_V

# ported from arcs/replication/src/h_verdicts.py:133 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
G6L_TOL, G6L_MIN_SEEDS = 0.02, 50  # amendment 3 §3 (species.g6l_sets defaults)

# ported from arcs/replication/src/h_verdicts.py:135 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
A5_GATES_JSON = H.ROOT / "arcs" / "audit" / "results" / "e3_gates_a5.json"
A5_GATES_SHA = "6d5533b3ce27211fb46788061b4b184aea071e5ddfed22888fb2747c87fbece8"


# ported from arcs/replication/src/h_verdicts.py:142 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
def zscore(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    return (v - v.mean()) / v.std()


# ported from arcs/replication/src/h_verdicts.py:147 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
# A3 reading - not A1's verdict rule (RUN_PLAN R1); kept for the P0 bit-identity test only
def direction_of(t: float) -> int:
    """Two-sided rule: the direction is the sign of the observed statistic (T = 0 -> +1)."""
    return 1 if t >= 0 else -1


def p_leg(null, obs: float, direction: int, doubled: bool) -> float:
    """One-sided empirical p in `direction` ((k + 1)/(n + 1), cascade.emp_p), doubled and capped at 1 if two-sided."""
    null = np.asarray(null, dtype=float).ravel()
    assert np.isfinite(null).all() and np.isfinite(obs), "non-finite null or observed statistic"
    p = emp_p(null, obs, direction)
    return min(1.0, 2.0 * p) if doubled else p


# ported from arcs/replication/src/h_verdicts.py:160 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
class Resid:
    """OLS residualisation on [1, g] (g None: on [1], i.e. demeaning)."""

    def __init__(self, n: int, g=None):
        cols = [np.ones(n)] + ([] if g is None else [np.asarray(g, dtype=float)])
        assert all(c.shape == (n,) for c in cols)
        self.Q, _ = np.linalg.qr(np.column_stack(cols))
        self.n_cov = len(cols) - 1

    def __call__(self, A) -> np.ndarray:
        A = np.asarray(A, dtype=float)
        return A - (A @ self.Q) @ self.Q.T


class CorrStat:
    """T = r(y ⊥ g, s ⊥ g) (partial correlation given g; g None: the plain Pearson r of A1, prereg §4.1's default)."""

    def __init__(self, y, g=None):
        y = np.asarray(y, dtype=float)
        assert y.ndim == 1 and np.isfinite(y).all(), "map must be a finite vector"
        self.n, self.g = y.size, g
        self.R = Resid(self.n, g)
        self.y = y
        self.yr = self.R(y)

    def T(self, scores) -> np.ndarray:
        """Rows of set scores -> T per row (each row residualised on [1, g])."""
        return corr_matrix(self.R(np.atleast_2d(scores)), self.yr)[:, 0]

    def T_maps(self, maps, s) -> np.ndarray:
        """Rows of (surrogate) maps -> T against one set score (each map re-residualised on [1, g])."""
        return corr_matrix(self.R(np.atleast_2d(maps)), self.R(s))[:, 0]

    def site_input(self) -> np.ndarray:
        """The map the site leg randomises: y ⊥ g for H1 (§6); y itself for the plain r (A1)."""
        return self.y if self.g is None else self.yr

    def level0(self, r: float, direction: int) -> float:
        """One-sided parametric p of the (partial) correlation r in `direction`: t = r sqrt(df / (1 - r^2)),
        df = n - 2 - (number of covariates). For g None this is cascade.naive_p."""
        df = self.n - 2 - self.R.n_cov
        t = r * math.sqrt(df / max(1e-300, 1.0 - r * r))
        return float(stats.t.sf(direction * t, df))


# ported from arcs/replication/src/h_verdicts.py:215 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
def g1_null_chunked(B, S, K: int, rng, chunk: int = 4096) -> np.ndarray:
    """= WithinClassBasis.g1_null(S, K, rng) (same rng calls in the same order), scored in chunks (no K x m array)."""
    S = np.asarray(S, dtype=int)
    pool = np.setdiff1d(np.arange(B.G), S)
    s_b = B.parts(S)[1]
    out = np.empty((K, B.X.shape[0]))
    for a in range(0, K, chunk):
        b = min(K, a + chunk)
        sets = np.stack([rng.choice(pool, size=len(S), replace=False) for _ in range(b - a)])
        out[a:b] = s_b[None, :] + B.set_means(B.Xw, sets)
    return out


def _g3m_one(B, S, f, pb, pn, rng) -> np.ndarray:
    return np.concatenate([rng.choice(pb, size=f, replace=False), rng.choice(pn, size=len(S) - f, replace=False)])


def g3m_null_chunked(B, S, K: int, rng, chunk: int = 4096) -> np.ndarray:
    """= WithinClassBasis.g3m_null(S, K, rng), scored in chunks."""
    S = np.asarray(S, dtype=int)
    f = int(B.brain[S].sum())
    pb = np.setdiff1d(np.flatnonzero(B.brain), S)
    pn = np.setdiff1d(np.flatnonzero(~B.brain), S)
    s_b = B.parts(S)[1]
    out = np.empty((K, B.X.shape[0]))
    for a in range(0, K, chunk):
        b = min(K, a + chunk)
        sets = np.stack([_g3m_one(B, S, f, pb, pn, rng) for _ in range(b - a)])
        out[a:b] = s_b[None, :] + B.set_means(B.Xw, sets)
    return out


def g6l_screen(B, S, rngs, keep=None, tol: float = G6L_TOL, min_seeds: int = G6L_MIN_SEEDS) -> list:
    """A1's exact G6l (WithinClassBasis.g6l_sets(S, keep, rng, exact=True)) for several random streams in ONE pass:
    every gene not in S is screened in index order (ranking in float64, window sums in float32, B.window_curve); an
    eligible seed gets one window per stream, its offset drawn by that stream (rng.choice over the in-band offsets);
    then per stream: < min_seeds eligible -> 'unmatched'; more than `keep` windows -> `keep` of them without
    replacement (keep None: every eligible seed). Stream by stream identical to g6l_sets(..., exact=True).
    Returns [(sets or None, info)] with info n = eligible seeds (A1's field) and n_used = windows kept."""
    S = np.asarray(S, dtype=int)
    m, G = len(S), B.G
    c_s = B.coherence_w(S)
    not_s = np.setdiff1d(np.arange(G), S)
    n_rank = G - m - 1
    half = n_rank // 2
    C0 = np.empty((half + m, B.ZwT32.shape[1]), np.float32)
    C0[0] = 0.0
    acc = [[] for _ in rngs]
    eligible = 0
    for g in not_s:
        rank, c = B.window_curve(g, S, m, n_rank, half, C0)
        offs = np.flatnonzero(np.abs(c - c_s) <= tol)
        if offs.size:
            eligible += 1
            for a, rng in zip(acc, rngs):
                o = int(rng.choice(offs))
                a.append(np.concatenate([[g], rank[o: o + m - 1]]))
    out = []
    for a, rng in zip(acc, rngs):
        info = dict(c_s=c_s, n=len(a), draws=int(not_s.size), eligible=eligible, exact=True)
        if len(a) < min_seeds:
            out.append((None, {**info, "status": "unmatched", "n_used": 0}))
            continue
        sets = np.stack(a)
        if keep is not None and len(sets) > keep:
            sets = sets[rng.choice(len(sets), size=keep, replace=False)]
        out.append((sets, {**info, "status": "ok", "n_used": int(len(sets))}))
    return out


def g6l_pool(B, S, sets, info: dict, chunk: int = 512):
    """A1's g6l_null post-processing on given windows: conditioned scores s_B(S) + s_W(window), the pool descriptors
    (signed and |r| score coherence, S-pool correlation, mean pairwise Jaccard, seeds' between-class share) and the
    'degenerate' status (mean pairwise Jaccard >= .5). Pairwise means are accumulated in chunks: the values of A1's
    n x n computation without the n x n matrices."""
    info = dict(info)
    info["eligible_frac"] = info["eligible"] / max(info["draws"], 1)
    if sets is None:
        return None, info
    M = B.membership(sets)
    null = B.conditioned_null(S, sets, M)
    n, m = sets.shape
    Zr = _rows_z(null)
    tot = Zr.sum(0)
    npairs = n * (n - 1) / 2
    signed = float((tot @ tot - n) / (2 * npairs))
    MT = M.T.tocsr()
    abs_sum = jac_sum = 0.0
    cols = np.arange(n)
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        up = cols[None, :] > np.arange(a, b)[:, None]
        C = Zr[a:b] @ Zr.T
        abs_sum += float(np.abs(C[up]).sum())
        inter = (M[a:b] @ MT).toarray()[up]
        jac_sum += float((inter / (2 * m - inter)).sum())
    info.update(pool_coh_signed=signed, pool_coh_abs=abs_sum / npairs,
                s_pool_corr=float(corr_matrix(B.parts(S)[0], null)[0].mean()),
                pool_jaccard=jac_sum / npairs, seed_bshare=float(B.bshare[sets[:, 0]].mean()))
    if info["pool_jaccard"] >= 0.5:
        info["status"] = "degenerate"
    return null, info


def species_draws(ctx, S, K: int, seed_of, g6l=None) -> dict:
    """The y-independent species null of set S in ctx: G1, G3m (conditioned scores), G6s (A1's g6s_scores, exact
    enumeration when 2^rank <= K) and G6l (every eligible seed; more than K -> K windows), each leg on its own seeded
    stream (§4.1 legs 2-5). g6l: an already screened (sets, info) for this set and the G6l stream (shared screen)."""
    B = ctx.B
    S = np.asarray(S, dtype=int)
    rng = {leg: np.random.default_rng(seed_of(leg)) for leg in ("G1", "G3m", "G6s", "G6l")}
    null = {"G1": g1_null_chunked(B, S, K, rng["G1"]), "G3m": g3m_null_chunked(B, S, K, rng["G3m"]),
            "G6s": B.g6s_scores(S, K, rng["G6s"])}
    exact6s = B.g6s_exact(K)
    n6s = 2 ** B.U.shape[1] if exact6s else K
    sets, info = g6l if g6l is not None else g6l_screen(B, S, [rng["G6l"]], keep=K)[0]
    N6l, info = g6l_pool(B, S, sets, info)
    null["G6l"] = N6l
    floors = {"G1": 1 / (K + 1), "G3m": 1 / (K + 1), "G6s": 2 / (n6s + 1) if exact6s else 1 / (K + 1)}
    if info["status"] == "ok":
        floors["G6l"] = 1 / (info["n_used"] + 1)
    return dict(null=null, g6l_info=info, floors=floors, g6s_exact=bool(exact6s), n_G6s=int(n6s), K=int(K))


# ported from arcs/replication/src/h_verdicts.py:342 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
def _g6l_public(info: dict) -> dict:
    keys = ("status", "c_s", "n", "n_used", "draws", "eligible", "eligible_frac", "pool_coh_signed", "pool_coh_abs",
            "s_pool_corr", "pool_jaccard", "seed_bshare")
    return {k: info.get(k) for k in keys}


# ported from arcs/replication/src/h_verdicts.py:348 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
# A3 reading - not A1's verdict rule (RUN_PLAN R1); kept for the P0 bit-identity test only
def assemble_verdict(p_level0: float, p_site: dict, site_floors: dict, legs: dict, species_floors: dict,
                     g6l_status: str, uninformative: bool, alpha: float, two_sided: bool) -> dict:
    """The verdict from leg p's (already doubled when two-sided) and RAW floors: every floor is doubled for a
    two-sided test (the smallest attainable doubled p), then asdg.verdict.verdict applies A1's status order
    (G6l unmatched / degenerate, uninformative, resolution-limited: doubled largest floor >= alpha) and survival
    (status ok and max(Level 0, site, species) < alpha)."""
    mult = 2.0 if two_sided else 1.0
    p6l = legs.get("p_G6l", float("nan"))
    p_species = float("nan") if (g6l_status != "ok" or p6l is None or np.isnan(p6l)) else H.pmax(*legs.values())
    species = dict(**legs, p_species=p_species, species_min_p=mult * max(species_floors.values()),
                   g6l_status=g6l_status, uninformative=bool(uninformative))
    site = dict(p_S1c=p_site["S1c"], p_S2c=p_site["S2c"], info_S1c={"floor": mult * site_floors["S1c"]},
                info_S2c={"floor": mult * site_floors["S2c"]})
    v = a1_verdict(p_level0, site, species, alpha)
    if v["status"] == "ok" and not np.isfinite(H.pmax(p_level0, v["p_site"], p_species)):
        # A1's verdict takes max(Level 0, site, species) with Python's max, which drops a NaN that is not first
        # (READINGS C4): an ok status with a non-finite member is refused, never read as a p
        v = {**v, "status": "incomplete (NaN leg p)", "p_verdict": float("nan"), "survives": False}
    return {**v, "p_species": p_species}


def claim_verdict(ctx, y, S, K: int, seed_of, g=None, alpha: float = ALPHA_V, two_sided: bool = True,
                  direction: int | None = None, draws: dict | None = None, *, parcel_ids) -> dict:
    """A1's verdict on (y, S) in ctx: Level 0 (parametric), the class-stratified site leg (max of S1c, S2c; exact
    enumeration when the stratified randomisation has <= K patterns) and the species leg (max of G1, G3m, G6s, G6l;
    each null set conditioned s_B(S) + s_W(R)); statuses and resolution label by asdg.verdict.verdict.
    two_sided: direction = sign of the observed T; every leg p doubled (capped at 1) and every floor doubled, so the
    resolution label reads 'doubled floor not below alpha'. two_sided False: one-sided in `direction`.
    g: H1's covariate (T = r(y ⊥ g, s ⊥ g); surrogates of y ⊥ g and species scores residualised on [1, g]); g is on
    y's parcels, in y's order.
    parcel_ids (required): y's parcel ids in y's order; y (and g) are aligned to ctx's class order by id and a
    differing id set is refused (h_common.align_to_context; READINGS F4).
    seed_of(leg) -> SeedSequence of that leg (§4.1)."""
    y = H.align_to_context(ctx, y, parcel_ids, "claim map y")
    if g is not None:
        g = H.align_to_context(ctx, g, parcel_ids, "covariate g")
    S = np.asarray(S, dtype=int)
    assert y.shape == (ctx.n,), (y.shape, ctx.n)
    stat = CorrStat(y, g)
    s = ctx.score(S)
    T_obs = float(stat.T(s)[0])
    if two_sided:
        assert direction is None, "two-sided: the direction is the sign of the observed T"
        direction = direction_of(T_obs)
    assert direction in (1, -1)
    mult = 2.0 if two_sided else 1.0
    p0_one = stat.level0(T_obs, direction)
    p0 = min(1.0, mult * p0_one)
    site, site_info = {}, {}
    for leg, method in (("S1c", "brainsmash"), ("S2c", "msr")):
        seed = int(np.random.default_rng(seed_of(leg)).integers(2 ** 31))
        sur, info = site_null(stat.site_input(), ctx.D, ctx.classes, K, seed, method)
        site[leg] = p_leg(stat.T_maps(sur, s), T_obs, direction, two_sided)
        site_info[leg] = info
    dr = draws if draws is not None else species_draws(ctx, S, K, seed_of)
    g6 = dr["g6l_info"]
    legs = {f"p_{k}": (p_leg(stat.T(N), T_obs, direction, two_sided) if N is not None else float("nan"))
            for k, N in dr["null"].items()}
    if g6["status"] != "ok":
        legs["p_G6l"] = float("nan")
    unin, share = ctx.B.uninformative(S, stat.site_input() if g is not None else y)
    v = assemble_verdict(p0, site, {k: site_info[k]["floor"] for k in site}, legs, dr["floors"], g6["status"], unin,
                         alpha, two_sided)
    return dict(T=T_obs, direction=int(direction), two_sided=bool(two_sided), alpha=alpha, n_parcels=int(ctx.n),
                parcel_ids=[int(i) for i in ctx.parcel_ids], m=int(len(S)), covariate="g" if g is not None else None,
                p_level0=p0, p_level0_one_sided=p0_one, p_S1c=site["S1c"], p_S2c=site["S2c"],
                p_site=H.pmax(site["S1c"], site["S2c"]), **legs, p_species=v["p_species"],
                p_verdict=v["p_verdict"], status=v["status"], survives=v["survives"],
                floors_raw=dict(site=max(site_info["S1c"]["floor"], site_info["S2c"]["floor"]),
                                **{f"species_{k}": f for k, f in dr["floors"].items()}),
                floors_effective=v["floors"], resolution=v["resolution"],
                site_info={k: dict(exact=d["exact"], n_null=d["n_null"], n_patterns=d["n_patterns"],
                                   floor=d["floor"]) for k, d in site_info.items()},
                uninformative_share=float(share), g6l=_g6l_public(g6), g6s_exact=dr["g6s_exact"], K=int(K))



# ported from arcs/replication/src/h_verdicts.py:1103 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
class PLS1R2:
    """PLS1 R^2 of maps on all genes, cascade.pls1's definition (genes z-scored with ddof = 1; weight ∝ X^T y; score
    t = X w; R^2 = corr(t, y)^2), for many maps at once through the parcel Gram matrix (t ∝ Xz Xz^T y)."""

    def __init__(self, X):
        X = np.asarray(X, dtype=float)
        self.X = X
        Xz = (X - X.mean(0)) / X.std(0, ddof=1)
        self.K = Xz @ Xz.T

    def __call__(self, Y) -> np.ndarray:
        Y = np.atleast_2d(np.asarray(Y, dtype=float))
        T = Y @ self.K
        return np.einsum("ij,ij->i", _rows_z(T), _rows_z(Y)) ** 2


# ported from arcs/replication/src/h_verdicts.py:1154 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
def _r2(y, Xc) -> float:
    y = np.asarray(y, dtype=float)
    A = np.column_stack([np.ones(len(y)), np.asarray(Xc, dtype=float)])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    res = y - A @ beta
    tot = ((y - y.mean()) ** 2).sum()
    return float(1 - (res @ res) / tot) if tot > 0 else float("nan")


# ported from arcs/replication/src/h_verdicts.py:1163 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
def descriptors(ctx, y, S, *, parcel_ids) -> dict:
    """Per claim (amendment 5 §3-§4.2): R2_grad (y demeaned within class ~ within-class-demeaned MNI y and z), R2_|x|
    (~ within-class-demeaned |MNI x|), set size m, f / m, the hypergeometric brain-enrichment p and rule, r(y_w, d_B),
    within-class coherence c_S. y: the map the verdict tests (H1: y ⊥ g; READINGS F2), with its parcel ids (aligned to
    ctx by id; READINGS F4)."""
    B = ctx.B
    y = H.align_to_context(ctx, y, parcel_ids, "descriptor map")
    S = np.asarray(S, dtype=int)
    yw = B.within_y(y)
    gy, gz = B.within_y(ctx.xyz[:, 1]), B.within_y(ctx.xyz[:, 2])
    ax = B.within_y(np.abs(ctx.xyz[:, 0]))
    m, f = len(S), int(B.brain[S].sum())
    n_b, G = int(B.brain.sum()), int(B.G)
    f_u = n_b / G
    p_h = float(stats.hypergeom.sf(f - 1, G, n_b, m))
    enriched = bool((f / m > f_u and p_h < 0.05) or f / m >= (f_u + 0.45) / 2)
    return dict(R2_grad=_r2(yw, np.column_stack([gy, gz])), R2_absx=_r2(yw, ax[:, None]), m=m, f=f,
                f_over_m=f / m, f_U=f_u, p_hypergeom=p_h, brain_enriched=enriched,
                r_yw_dB=float(np.corrcoef(yw, B.d_B)[0, 1]), c_S=float(B.coherence_w(S)))


def a1_scope_in_force() -> dict:
    """The scope labels in force after A1 (arcs/audit/results/e3_gates_a5.json, sha256 asserted): the classes whose
    claims carry 'species leg untested (gradient)' at R2_grad >= .25 and 'brain-enrichment (N1) confound untested' on
    brain-enriched sets; the replica's planted leg (c) outcome (a failure would add dk-ctx to the N1 classes)."""
    data = A5_GATES_JSON.read_bytes()
    assert H.sha256_bytes(data) == A5_GATES_SHA, "e3_gates_a5.json changed"
    d = json.loads(data.decode("utf-8"))
    grad = sorted({lab.split(": ")[1].split(" claims")[0] for lab in d["scope_labels"]
                   if lab.startswith("species leg untested (gradient)")})
    n1 = sorted({lab.split(": ")[1].split(" claims")[0] for lab in d["scope_labels"]
                 if lab.startswith("brain-enrichment (N1)")})
    return dict(gradient_classes=grad, n1_classes=n1, K1_status=d["K1_status"], source_sha256=A5_GATES_SHA)


# ported from arcs/replication/src/h_verdicts.py:1198 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
NO_A3_GATE = "no A3 gate"  # the gate entry of a family member no A3 gate covers (H4 stage 2: §10.3) - review CR1
APPLY_GATE_KEYS = ("not_evaluated", "labels", "planted", "reason")  # apply_gate's output (a family's gate entries)


# ported from arcs/replication/src/h_verdicts.py:1202 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
def apply_gate(gate: dict | None, m: int, r2_grad: float) -> dict:
    """§10.3's consequences rule for the gate covering a claim (G-H1 for H1 on aal-ctx, G-H3 for a pair, G-H2 for a
    window). gate = None: no A3 gate covers the claim (H4: A1's planted classes). gate keys (bool): evaluated,
    false_alarm_failed, false_alarm_only_m_gt_300, site_leg_failed (G-H3 gate (ii), amendment 1 §2.6: NOT
    EVALUATED, as a false-alarm failure), status_inflation_failed (G-H3, review CR6: a generator cell's non-ok share
    > 5 % in a gated stratum: NOT EVALUATED), not_evaluated (the gate record's own flag, e.g. classify_h3's: NOT
    EVALUATED with its not_evaluated_reasons), tgrad_plant_active_failed, other_failed (any other plant-active or
    planted-leg failure); optional makes_planted (class names a passing gate plants: classify_h1 returns ['aal-ctx']
    when G-H1 is evaluated with no false-alarm, other plant-active or planted-leg failure, review CR4). Returns the
    four APPLY_GATE_KEYS - the gate entry h3_family / k4_family take per member.
    FAIL CLOSED (ABIDE II-side review AR3): a gate record must carry EXACTLY the key set of the classify_* function
    its name names (G-H1 -> gates_eval.classify_h1: name, status, evaluated, false_alarm_failed,
    false_alarm_only_m_gt_300, tgrad_plant_active_failed, other_failed, makes_planted, failed_false_alarm_gates,
    failed_other_gates, tgrad_gate, not_run, n_gates, n_false_alarm_gates; G-H3 pair a / b -> gates_eval.classify_h3:
    name, status, evaluated, false_alarm_failed, false_alarm_only_m_gt_300, site_leg_failed, status_inflation_failed,
    tgrad_plant_active_failed, other_failed, failed_false_alarm_gates, failed_site_leg_gates,
    failed_status_inflation_gates, failed_other_gates, not_evaluated, not_evaluated_reasons, not_run, n_gates), with
    every flag a bool; anything else - {'evaluated': True}, a misspelt or dropped failure key, an unknown key, a
    string flag, another gate's name - is refused (ValueError). A missing or not-run gate is classify_*'s own record of
    an empty evaluation (gates_eval.evaluate_h1 / evaluate_h3 on no rows), which reads NOT EVALUATED."""
    h1_keys = ("name", "status", "evaluated", "false_alarm_failed", "false_alarm_only_m_gt_300",
               "tgrad_plant_active_failed", "other_failed", "makes_planted", "failed_false_alarm_gates",
               "failed_other_gates", "tgrad_gate", "not_run", "n_gates", "n_false_alarm_gates")
    h3_keys = ("name", "status", "evaluated", "false_alarm_failed", "false_alarm_only_m_gt_300", "site_leg_failed",
               "status_inflation_failed", "tgrad_plant_active_failed", "other_failed", "failed_false_alarm_gates",
               "failed_site_leg_gates", "failed_status_inflation_gates", "failed_other_gates", "not_evaluated",
               "not_evaluated_reasons", "not_run", "n_gates")
    flags = ("evaluated", "false_alarm_failed", "false_alarm_only_m_gt_300", "site_leg_failed",
             "status_inflation_failed", "tgrad_plant_active_failed", "other_failed", "not_evaluated")

    def out(ne, labels, planted, reason):
        return dict(not_evaluated=bool(ne), labels=list(labels), planted=list(planted), reason=reason)

    if gate is None:
        return out(False, [], [], None)
    if not isinstance(gate, dict):
        raise ValueError(f"apply_gate: a gate record is classify_*'s dict, not {type(gate).__name__}")
    name = gate.get("name")
    if name == "G-H1":
        want = h1_keys
    elif isinstance(name, str) and name.startswith("G-H3 pair "):
        want = h3_keys
    else:
        raise ValueError(f"apply_gate: gate name {name!r} is neither 'G-H1' (classify_h1) nor 'G-H3 pair ..' "
                         f"(classify_h3); refused (fail closed, review AR3)")
    missing, extra = [k for k in want if k not in gate], sorted(set(gate) - set(want))
    if missing or extra:
        raise ValueError(f"apply_gate: {name} record is not classify_*'s output (fail closed, review AR3): missing "
                         f"{missing}, unknown {extra}; required keys {list(want)}")
    notbool = [k for k in flags if k in gate and not isinstance(gate[k], (bool, np.bool_))]
    if notbool or not isinstance(gate.get("makes_planted", []), list):
        raise ValueError(f"apply_gate: {name} flags {notbool} are not booleans (or makes_planted is not a list)")
    if not gate["evaluated"]:
        return out(True, [], [], f"{name} not evaluated")
    if gate["false_alarm_failed"] and not (gate["false_alarm_only_m_gt_300"] and m <= 300):
        return out(True, [], [], f"{name} false-alarm failure")
    if gate.get("site_leg_failed", False):  # G-H3 gate (ii), amendment 1 §2.6: that pair is NOT EVALUATED
        return out(True, [], [], f"{name} site-leg calibration failure (gate (ii), amendment 1 §2.6)")
    if gate.get("status_inflation_failed", False):  # review CR6: that pair is NOT EVALUATED
        return out(True, [], [], f"{name} status inflation (a generator cell's non-ok share > 5 % in a gated stratum)")
    if gate.get("not_evaluated", False) and not (gate["false_alarm_only_m_gt_300"] and m <= 300):
        why = "; ".join(gate.get("not_evaluated_reasons") or ["its not_evaluated flag"])
        return out(True, [], [], f"{name} NOT EVALUATED ({why})")
    labels = []
    if gate["tgrad_plant_active_failed"] and r2_grad >= 0.25:
        labels.append("species leg untested (gradient)")
    if gate["other_failed"]:
        labels.append("calibration extrapolated (untested gate)")
    return out(False, labels, gate.get("makes_planted", []), None)


# ported from arcs/replication/src/h_verdicts.py:1273 (git blob 7e8fc041baaac1b4782baafad0d2133d1bc89584 at HEAD 86edcad)
def reading(rec: dict, desc: dict | None, ctx, reparcellated: bool = False, gate: dict | None = None,
            scope: dict | None = None) -> dict:
    """The reading of one claim (amendment 5 §3-§4, A3 §6 / §10.3). rec: a verdict record (status, survives);
    desc: descriptors() of the tested map (None: the record's own 'descriptors', which h1_verdict computes on y ⊥ g);
    ctx: the claim's class (read in ctx.reading_class(); h_common READINGS); reparcellated: the map was re-parcellated
    onto the class (T2); gate: apply_gate's input for the covering A3 gate. Returns labels, power columns, planted
    flag and the reading: 'NOT EVALUATED (...)', the status as frozen, 'survives — calibrated evidence', 'survives —
    calibration extrapolated (...)' or 'not detectable at this power'. An H3 Delta record is refused: its outcome is
    h3_family's Holm over the two pairs, never a single-record flag (review CR1)."""
    if rec.get("hypothesis") == "H3" and "p_conj" in rec:
        raise ValueError("reading: an H3 Delta record's registered outcome is h3_family's Holm over the two pairs "
                         "(with the G-H3 outcomes), not a single-record reading (review CR1)")
    if desc is None:
        if "descriptors" not in rec:
            raise ValueError("reading: no descriptors given and the record carries none")
        desc = rec["descriptors"]
    scope = scope or a1_scope_in_force()
    rc = ctx.reading_class()
    m = int(desc["m"])
    g = apply_gate(gate, m, desc["R2_grad"])
    planted = rc in H.PLANTED_CLASSES or rc in g["planted"]
    single_outside = ctx.single_class() and rc != "dk-ctx" and not planted
    native_outside = rc not in H.PLANTED_CLASSES and not planted
    labels = []
    if (rc in scope["gradient_classes"] or reparcellated or native_outside or single_outside) \
            and desc["R2_grad"] >= 0.25:
        labels.append("species leg untested (gradient)")
    if (rc in scope["n1_classes"] or reparcellated or native_outside or single_outside) and desc["brain_enriched"]:
        labels.append("brain-enrichment (N1) confound untested")
    grad_extrap = []
    if desc["R2_grad"] > 0.81:
        labels.append("gradient beyond planted strength; site-leg bound extrapolated")
        grad_extrap.append("gradient")
    if desc["R2_absx"] >= 0.25:
        labels.append("gradient orientation unplanted (M-L)")
        grad_extrap.append("gradient")
    for lab in g["labels"]:
        if lab not in labels:
            labels.append(lab)
    power = [rc] if rc in ("V-AAL", "V-DK") else ["V-AAL", "V-DK"]
    if rc not in ("V-AAL", "V-DK"):
        labels.append("power not measured in this class")
    if m < 25 or m > 100:
        labels.append("power not measured at this set size")
    if g["not_evaluated"]:
        text = f"NOT EVALUATED ({g['reason']})"
    elif rec.get("status") != "ok":
        text = str(rec.get("status"))
    elif rec.get("survives"):
        why = []
        if not 25 <= m <= 1000:
            why.append("set size")
        if not planted:
            why.append("class")
        if grad_extrap:
            why.append("gradient")
        if "calibration extrapolated (untested gate)" in labels:
            why.append("untested gate")
        text = ("survives — calibrated evidence" if not why
                else f"survives — calibration extrapolated ({' / '.join(dict.fromkeys(why))})")
    else:
        text = "not detectable at this power"
    return dict(reading=text, labels=labels, power_columns=power, planted_class=planted, reading_class=rc,
                gate=g, donor_robustness=("required for a survival (A1 §3.1): computed by the caller from the "
                                          "leave-one-donor-out matrices in artifacts/ahba/loo (MANIFEST sha256 "
                                          "c7d12224…; step3v_common) and attached beside this reading"
                                          if rec.get("survives") else None))


# ported from arcs/replication/src/step3v_common.py:113 (git blob ec4566dbe5f747852ee6d6a27e8c741a06706af4 at HEAD 86edcad)
class DriverRefused(SystemExit):
    """A start condition is not met; nothing was opened (or, after opening, nothing was computed / written)."""


# ported from arcs/replication/src/step3v_common.py:121 (git blob ec4566dbe5f747852ee6d6a27e8c741a06706af4 at HEAD 86edcad)
class CheckpointError(DriverRefused):
    """A checkpoint does not belong to this run (code hash, seeds, map hash, key): the resume is refused."""


# ported from arcs/replication/src/step3v_common.py:607 (git blob ec4566dbe5f747852ee6d6a27e8c741a06706af4 at HEAD 86edcad)
def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (set, frozenset)):
        return sorted(jsonable(v) for v in o)
    if isinstance(o, np.ndarray):
        return jsonable(o.tolist())
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, Path):
        return str(o)
    if o is None or isinstance(o, (bool, int, float, str)):
        return o
    return str(o)


def canon(o):
    return json.loads(json.dumps(jsonable(o)))


def map_sha(values, ids=None) -> str:
    """The map hash a checkpoint carries: sha256 (16 hex) of the float64 values and (if given) the int64 ids."""
    h = hashlib.sha256(np.ascontiguousarray(np.asarray(values, dtype=np.float64)).tobytes())
    if ids is not None:
        h.update(np.ascontiguousarray(np.asarray([int(i) for i in ids], dtype=np.int64)).tobytes())
    return h.hexdigest()[:16]


# ported from arcs/replication/src/step3v_common.py:641 (git blob ec4566dbe5f747852ee6d6a27e8c741a06706af4 at HEAD 86edcad)
_KEY = re.compile(r"[A-Za-z0-9_.-]+")


class Checkpoints:
    """One JSON file per task in run_dir: {key, driver, code_hash, expect: {seeds, map_sha, ...}, payload}. load()
    returns the payload of a matching checkpoint, None if absent, and refuses (CheckpointError) one that does not
    belong to this run; save() writes atomically (tmp + os.replace)."""

    def __init__(self, run_dir, code_hash_: str, driver: str):
        self.dir = Path(run_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.code_hash, self.driver = code_hash_, driver

    def path(self, key: str) -> Path:
        if not _KEY.fullmatch(key):
            raise ValueError(f"checkpoint key {key!r}")
        return self.dir / f"ck_{key}.json"

    def load(self, key: str, expect: dict):
        p = self.path(key)
        if not p.exists():
            return None
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except ValueError as e:
            raise CheckpointError(f"{p.name}: unreadable checkpoint ({e!r}); remove it to recompute that task") from None
        if doc.get("key") != key or doc.get("driver") != self.driver:
            raise CheckpointError(f"{p.name}: key / driver {doc.get('key')!r} / {doc.get('driver')!r} != {key!r} / "
                                  f"{self.driver!r}")
        if doc.get("code_hash") != self.code_hash:
            raise CheckpointError(f"{p.name}: written by code {doc.get('code_hash')!r}, this run's is {self.code_hash} "
                                  f"(a checkpoint of another code version is never resumed)")
        want, got = canon(expect), doc.get("expect") or {}
        bad = [k for k in want if got.get(k) != want[k]]
        if bad:
            raise CheckpointError(f"{p.name}: {bad} differ from this run's (seeds / map hash / settings): not this run's")
        return doc["payload"]

    def save(self, key: str, expect: dict, payload) -> None:
        p = self.path(key)
        doc = dict(key=key, driver=self.driver, code_hash=self.code_hash, expect=canon(expect),
                   payload=jsonable(payload), written=_dt.datetime.now().isoformat(timespec="seconds"), pid=os.getpid())
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(doc, indent=0) + "\n", encoding="utf-8", newline="\n")
        os.replace(tmp, p)

    def run_record(self, head: dict) -> dict:
        """RUN.json: the run's identity (commit, code hash, inputs, settings, map hashes). A resumed run must present
        the same identity, else it is refused (use another --run-dir)."""
        p = self.dir / "RUN.json"
        head = canon(head)
        if p.exists():
            old = json.loads(p.read_text(encoding="utf-8"))
            if {k: old.get(k) for k in head} != head:
                diff = [k for k in head if old.get(k) != head[k]]
                raise CheckpointError(f"{p}: this run's {diff} differ from the run directory's (resume refused; use a "
                                      f"new --run-dir)")
            return old
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(head, indent=1) + "\n", encoding="utf-8", newline="\n")
        os.replace(tmp, p)
        return head


# ported from arcs/replication/src/step3v_common.py:710 (git blob ec4566dbe5f747852ee6d6a27e8c741a06706af4 at HEAD 86edcad)
def run_pending(tasks: list, store: Checkpoints, fn, jobs: int, log=print) -> dict:
    """tasks: [(key, expect, kwargs)] in dispatch order (longest first). Tasks whose checkpoint verifies are not rerun;
    the others run through fn(key, kwargs) -> (key, payload) (in-process, or a loky pool with batch_size 1 in the given
    order), each payload checkpointed as it returns. Returns {key: payload} read back from the checkpoints."""
    import time

    done = {}
    pending = []
    for key, expect, kw in tasks:
        got = store.load(key, expect)
        if got is None:
            pending.append((key, expect, kw))
        else:
            done[key] = got
    if done:
        log(f"  resume: {len(done)} task(s) verified from checkpoints, {len(pending)} to run")
    t0 = time.time()
    exp = {k: e for k, e, _ in pending}
    if pending and jobs > 1:
        from joblib import Parallel, delayed

        gen = Parallel(n_jobs=jobs, backend="loky", batch_size=1, return_as="generator_unordered")(
            delayed(fn)(k, kw) for k, _, kw in pending)
        for i, (key, payload) in enumerate(gen, 1):
            store.save(key, exp[key], payload)
            if i % 10 == 0 or i == len(pending):
                log(f"  {i}/{len(pending)} tasks ({time.time() - t0:.0f}s)")
    else:
        for i, (key, _, kw) in enumerate(pending, 1):
            k2, payload = fn(key, kw)
            assert k2 == key
            store.save(key, exp[key], payload)
    return {key: store.load(key, expect) for key, expect, _ in tasks}



# ---- end of ported code -------------------------------------------------------------------------------------------
A3_READINGS = ("direction_of", "p_leg", "assemble_verdict", "claim_verdict")
for _name in A3_READINGS:
    _f = globals()[_name]
    _f.__doc__ = ("A3 reading - not A1's verdict rule (RUN_PLAN R1); P0 bit-identity only. "
                  + (_f.__doc__ or ""))
del _name, _f

PORTED_FROM_HEAD = "86edcad"
PORTED_BLOBS = {
    "arcs/replication/src/h_common.py": "220e5c6aafa99c007db87815e6a5a1bf3a163493",
    "arcs/replication/src/h_verdicts.py": "7e8fc041baaac1b4782baafad0d2133d1bc89584",
    "arcs/replication/src/step3v_common.py": "ec4566dbe5f747852ee6d6a27e8c741a06706af4",
}
