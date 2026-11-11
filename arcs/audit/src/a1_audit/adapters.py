"""A1 T-form adapters (arcs/audit/RUN_PLAN.md v3.1, FROZEN: §4 "Gene scaling, by form", "Analysis parcels", "Memory",
"Shared G6l screens"; R1, R2, R3, R6, R8, R24; plants P0, P5, P7, P11, P12).

Every registered T form is a class with A3's CorrStat duck-typed interface (a3_port.CorrStat: T(scores), T_maps(maps,
s), site_input(), level0(t, direction)), extended so that the form-generic verdict driver (a later WP1 task) can apply
R1: every leg returns its one-sided p in BOTH directions, {+1: p(+), -1: p(-)}, by (k + 1)/(n + 1) (cascade.emp_p;
prereg.md:117), and Level 0 by the parametric sf (+) / cdf (-) where Level 0 is parametric. Nothing here chooses a
direction, doubles a p, applies a floor rule or assigns a verdict status: that is the driver's job (R1, R8, R9).

Forms (claim_form in the TSV -> class):
- set-vs-map -> SetVsMap: T = Pearson r(y, s), s = per-parcel mean of S's columns of the abagen-normalised matrix
  UNCHANGED (prereg.md:113-114; claims_register.md:283-284; §4: nothing is z-scored for this form). Level 0, site
  leg and species legs exactly as A3's claim_verdict builds them (a3_port.CorrStat, species_draws on ctx.B).
- decoded-list -> DecodedList: genes z-scored over the claim's analysis parcels (ddof 0); y standardised (ddof 0);
  T = <y^, s_z(S)> / n with s_z(S) the mean of S's z-scored columns, NOT re-standardised (= the mean per-gene Pearson
  r; claims_register.md:285-286; R3). Level 0 = Welch t of S's per-gene r against the rest of the universe. Site
  leg: every per-gene r of S recomputed on each surrogate (chunks of <= 1,000 surrogates, §4 memory). Species legs:
  amendment 3 §2's conditioned null scores s_B(S) + s_W(R) built on the z-scored matrix, scored <y^, .> / n (R2) -
  NOT the engine's Pearson scorer WithinClassBasis._p (src/asdg/species.py:102-104). The conditioned scores are the
  engine's own: asdg.species.WithinClassBasis built, unchanged, on the z-scored matrix (z_basis), driven by the
  copied A3 builders (a3_port.g1_null_chunked / g3m_null_chunked / g6l_pool; G6s = WithinClassBasis.g6s_scores on
  the z-scored basis, "G6s on the z-scored matrix", claims_register.md:288, prereg_amend_3.md:107).
- PLS-enrichment -> PlsEnrichment: w = PLS1 weight of cascade.pls1 (Z^T y / ||Z^T y|| over the full universe,
  oriented corr(score, y) > 0); T = mean_{g in S} w_g. w = r / ||r|| exactly (r the per-gene Pearson r vector), so
  with y fixed every species null is DecodedList's times the constant 1 / ||r|| and the species p's equal
  DecodedList's (prereg_amend_4.md:88-90; R3; P7). Site leg: PLS1 refit on every surrogate (cascade.pls1, chunks of
  <= 1,000). Level 0 = Welch t of S's weights against all others (prereg.md:187).
- T_abs descriptor -> TAbs (claims_register.md:309-313): T = mean over S of |per-gene r|; upper tail (lower for a
  stated depletion); Level 0 Welch t of |r|; site leg (per-gene r recomputed per surrogate); UNCONDITIONED G1, G3m,
  G6l (sets scored by mean |r|); no G6s.
- component -> FixedComponent (T = r(y, component as given); parametric Level 0), Pls1R2 (a3_port.PLS1R2 = cascade.
  pls1's R^2; Level 0 = parcel-label permutations with refit), PlsrComponent (sklearn PLSRegression(K, scale=True):
  R^2 of component k, or the cumulative R^2 of the K components; refit through the parcel Gram matrix, equal to
  sklearn to 1e-12 in tests/test_p0.py). Component forms have no species leg (prereg.md:180-181).

The species legs read the ports' seed convention: seed_of(leg) -> numpy SeedSequence, leg in ('S1c', 'S2c', 'G1',
'G3m', 'G6s', 'G6l') (A3's names; the driver maps T_abs's legs 21-25 and the component permutation leg 8 onto them,
§4 legs table). A leg that needs an integer seed takes int(default_rng(SS).integers(2**31)), a leg that needs a
Generator default_rng(SS) (R7; h_verdicts.py:398).

R8 (pool smaller than S never crashes): G1 needs |U \\ S| >= m, G3m |(B n U) \\ S| >= f and |U \\ (B u S)| >= m - f;
otherwise that leg's null is None with status 'not computable (pool < m)'. G6l keeps its frozen rule: when no window
of size m fits the ranking (m - 1 > G - m - 1) no seed is eligible and G6l reads 'unmatched'.

RUN_PLAN_amend_1.md v2.1 (FROZEN sha256 8e06d60e...; arcs/audit/FROZEN.txt), implemented here:
- R32 (a): every exact enumeration that contains the identity pattern (site_null with exact true: row 0, in every
  form's site leg, T_abs's and the components' included; exact G6s: the last row) has its identity row located by
  index, its reconstruction of the observed input asserted to 1e-9 x max(1, max |input|) (identity_rows; a failure
  raises FunctionalDefect and stops the run), and the null statistic of that row and of every row whose null input is
  bit-identical to it set to the observed statistic (count_identity), before (k + 1)/(N + 1). Sampled legs untouched.
- R32 (b): a rank statistic (Spearman rho; R10's rank-biserial r) is compared exactly, never through a float: doubled
  average ranks centred by n + 1, numerators and denominators in Python integers; the branch (common denominator ->
  numerators; else exact rationals, sign(N) N^2 Q' cross-products for a correlation) is decided by computing every
  state's denominator (rank_corr_terms / rank_corr_counts / rational_counts). RankRho is the rho descriptor's site leg.
- R32 (c): on every exact leg p(d) >= the declared floor in both directions is asserted (assert_exact_floor; also in
  the verdict driver and the descriptor pass).
- R33: a G6l window that fits only part of the offset range: O_g over o in [0, min(half, n_rank - m + 1)]
  (g6l_screen_range / g6l_sets_range beside the frozen a3_port.g6l_screen, which still serves every full-range case).
- R34: component Level 0 = T refit on default_rng(SS).permuted(tile(y, (K, 1)), axis=1) (leg 8; selected lists: leg
  10, SelectedList); a component map with n! <= 10,000 is refused (the unreachable-case assertion); the selected-list
  rule and statistic are given no generator (asserted).

asdg-skeptic review of WP1 (61e3887): C7 - build_context_checked also builds V-DK-subcortex and MIST64 (A1_CLASS_DEFS:
A1-side definitions; a3_port's verbatim CLASS_DEFS is not edited), with R35's first-use check; C8 - analysis_parcels
counts a class parcel the map does not hold as dropped when given the class's parcels (class_parcel_ids).
"""
from __future__ import annotations

import functools
import inspect
import math

import numpy as np
import pandas as pd
from scipy import stats

from . import a3_port as A3
from asdg.cascade import corr_matrix, emp_p, pls1, _rows_z
from asdg.genesets import Universe
from asdg.spatial import site_null
from asdg.species import WithinClassBasis

CHUNK_MAX = 1000  # §4 memory: surrogate refits form Z^T Y* in chunks of at most 1,000 surrogates
DIRECTIONS = (1, -1)
NOT_COMPUTABLE = "not computable (pool < m)"  # R8
SITE_LEGS = (("S1c", "brainsmash"), ("S2c", "msr"))  # the adopted class-stratified pair (h_verdicts.py:397)
SPECIES_LEGS = ("G1", "G3m", "G6s", "G6l")
FORMS = ("set-vs-map", "decoded-list", "PLS-enrichment", "t-abs", "component")
COMPONENT_KINDS = ("fixed", "pls1-r2", "plsr")
R32_RTOL = 1e-9          # RUN_PLAN_amend_1 R32 (a) step 2: reconstruction to 1e-9 x max(1, max |input|)
R34_ENUM_LIMIT = 10_000  # RUN_PLAN_amend_1 R34 (C3): n! <= 10,000 would be "enumerated exactly" (prereg_amend_3.md:92)
R32_IDENTITY_RULE = ("R32 (a): identity row located by index, its reconstruction asserted, its null statistic and that "
                     "of every bit-identical row set to the observed statistic (RUN_PLAN_amend_1.md)")
R32_RANK_RULE = ("R32 (b): rank statistic compared exactly (doubled average ranks centred by n + 1; Python integers; "
                 "branch decided per null state by the denominators)")
RANK_BRANCH_COMMON = "common denominator: numerators compared (Python integers)"
RANK_BRANCH_RATIONAL = "denominators differ: exact rationals (Python integers)"
SCALING = {"set-vs-map": "none: abagen-normalised values unchanged (RUN_PLAN §4; prereg.md:113-114)",
           "decoded-list": "genes z-scored over the analysis parcels, ddof 0 (claims_register.md:285-286)",
           "PLS-enrichment": "genes z-scored over the analysis parcels, ddof 0 (prereg.md:177)",
           "t-abs": "genes z-scored over the analysis parcels, ddof 0 (as decoded-list; claims_register.md:309-310)",
           "component": "none here: cascade.pls1 / PLSRegression(scale=True) z-score internally; a fixed component "
                        "is used as given (RUN_PLAN §4)"}


# ================================================================================================================
# p-values in both directions (R1)
# ================================================================================================================
def p_both(null, obs: float) -> dict:
    """One-sided empirical p in both directions, {+1: p(+), -1: p(-)}, each (k + 1)/(n + 1) (cascade.emp_p). Refuses a
    non-finite null or observed statistic (as a3_port.p_leg does)."""
    null = np.asarray(null, dtype=float).ravel()
    if null.size == 0 or not (np.isfinite(null).all() and np.isfinite(obs)):
        raise ValueError("p_both: empty or non-finite null, or non-finite observed statistic")
    return {d: emp_p(null, float(obs), d) for d in DIRECTIONS}


# ================================================================================================================
# RUN_PLAN_amend_1 R32 (a), (c): the identity pattern of an exact enumeration; the floor assertion
# ================================================================================================================
class FunctionalDefect(RuntimeError):
    """A functional-defect assertion of RUN_PLAN_amend_1 (R32 (a) reconstruction, R32 (c) floor, R34's n! and
    no-generator assertions): it stops the run; never caught and read as a p."""


def _row_bits(rows) -> np.ndarray:
    A = np.ascontiguousarray(np.atleast_2d(np.asarray(rows, dtype=np.float64)))
    return A.view(np.uint64)


def identity_rows(inputs, index: int, observed, what: str) -> tuple[np.ndarray, float]:
    """R32 (a) steps 1-3 on an exact enumeration's null INPUTS (rows): the identity row is located by `index` (site
    legs: 0; exact G6s: -1, the last row); its reconstruction of the observed input is asserted to 1e-9 x max(1,
    max |input|) (else FunctionalDefect: the run stops); returns (the indices of that row and of every row
    bit-identical to it, the reconstruction's max |delta|)."""
    X = np.atleast_2d(np.asarray(inputs, dtype=np.float64))
    n = X.shape[0]
    i = int(index)
    if not -n <= i < n:
        raise FunctionalDefect(f"R32 (a): {what}: identity index {i} outside the {n} enumerated rows; the run stops")
    i %= n
    obs = np.asarray(observed, dtype=np.float64).ravel()
    if obs.shape != (X.shape[1],):
        raise FunctionalDefect(f"R32 (a): {what}: observed input of length {obs.size} for rows of {X.shape[1]}")
    scale = max(1.0, float(np.max(np.abs(obs))))
    dev = float(np.max(np.abs(X[i] - obs)))
    if not dev <= R32_RTOL * scale:
        raise FunctionalDefect(f"R32 (a): {what}: row {i} does not reconstruct the observed input (max |delta| "
                               f"{dev:.3g} > 1e-9 x {scale:.3g}); the run stops")
    B = _row_bits(X)
    rows = np.flatnonzero((B == B[i]).all(axis=1))
    if i not in set(rows.tolist()):
        raise FunctionalDefect(f"R32 (a): {what}: the identity row is not bit-identical to itself")
    return rows, dev


def count_identity(null, rows, obs: float) -> np.ndarray:
    """R32 (a) step 3: the null statistic of the identity row and of its bit-identical duplicates := the observed
    statistic (a copy; the other rows are untouched)."""
    out = np.array(null, dtype=np.float64, copy=True).ravel()
    out[np.asarray(rows, dtype=int)] = float(obs)
    return out


def identity_record(index: int, rows, dev: float, n_null: int) -> dict:
    return dict(index=int(index), rows_counted_as_identity=int(len(rows)), bit_identical_duplicates=int(len(rows) - 1),
                reconstruction_max_abs=float(dev), n_null=int(n_null), rule=R32_IDENTITY_RULE)


def assert_exact_floor(p, floor, what: str) -> None:
    """R32 (c): on an exact leg, p(d) >= the declared floor in BOTH directions; a failure is a functional defect and
    stops the run (FunctionalDefect)."""
    fl = float(floor)
    for d in DIRECTIONS:
        v = float(p[d])
        if not v >= fl:
            raise FunctionalDefect(f"R32 (c): {what}: exact leg p({d:+d}) = {v!r} < its declared floor {fl!r}: a "
                                   "functional defect; the run stops")


# ================================================================================================================
# RUN_PLAN_amend_1 R32 (b): rank statistics compared exactly (Python integers; exact rationals)
# ================================================================================================================
def doubled_ranks(values) -> np.ndarray:
    """Average ranks (1..n) DOUBLED, so every rank is an integer (a tie of positions s..e, 0-based in sorted order,
    gets s + e + 2), for each row of `values` (rows x n; a 1-D input is one row). Ties are exact float equality."""
    A = np.atleast_2d(np.asarray(values, dtype=np.float64))
    if not np.isfinite(A).all():
        raise ValueError("doubled_ranks: non-finite value")
    K, n = A.shape
    order = np.argsort(A, axis=1, kind="stable")
    sv = np.take_along_axis(A, order, axis=1)
    pos = np.broadcast_to(np.arange(n, dtype=np.int64), (K, n))
    new = np.ones((K, n), bool)
    new[:, 1:] = sv[:, 1:] != sv[:, :-1]
    start = np.maximum.accumulate(np.where(new, pos, 0), axis=1)
    last = np.ones((K, n), bool)
    last[:, :-1] = new[:, 1:]
    end = np.minimum.accumulate(np.where(last, pos, n - 1)[:, ::-1], axis=1)[:, ::-1]
    out = np.empty((K, n), np.int64)
    np.put_along_axis(out, order, start + end + 2, axis=1)
    return out


def centred_ranks(values) -> np.ndarray:
    """2R - (n + 1) per row, as an object array of Python ints (every later product and sum in Python integers)."""
    R = doubled_ranks(values)
    return (R - (R.shape[1] + 1)).astype(object)


def rank_corr_terms(a_rows, b_rows) -> tuple[list, list]:
    """Spearman rho of each state (row of a with row of b; a 1-row side is broadcast) as N / sqrt(Q) with
    N = sum (2R_a - (n + 1))(2R_b - (n + 1)) and Q = sum (2R_a - (n + 1))^2 x sum (2R_b - (n + 1))^2, both Python ints."""
    A, B = centred_ranks(a_rows), centred_ranks(b_rows)
    if A.shape[1] != B.shape[1]:
        raise ValueError("rank_corr_terms: rows of different length")
    if len(A) != len(B):
        if len(A) == 1:
            A = np.repeat(A, len(B), axis=0)
        elif len(B) == 1:
            B = np.repeat(B, len(A), axis=0)
        else:
            raise ValueError("rank_corr_terms: row counts differ")
    N = [int(v) for v in (A * B).sum(axis=1)]
    SA = [int(v) for v in (A * A).sum(axis=1)]
    SB = [int(v) for v in (B * B).sum(axis=1)]
    return N, [a * b for a, b in zip(SA, SB)]


def _signed_square(x: int) -> int:
    return x * x if x >= 0 else -(x * x)


def rank_corr_counts(N0: int, Q0: int, N, Q) -> dict:
    """R32 (b) for a correlation of ranks: k(+) = #{rho_k >= rho_obs}, k(-) = #{rho_k <= rho_obs} counted exactly.
    The branch is decided by computing: every state's denominator Q equal to the observed one -> numerators compared;
    otherwise exact rationals through sign(N) N^2 Q' cross-products (rho >= rho0 <=> sign(N) N^2 Q0 >= sign(N0) N0^2 Q).
    p by (k + 1)/(n + 1) in both directions."""
    N0, Q0 = int(N0), int(Q0)
    N, Q = [int(x) for x in N], [int(x) for x in Q]
    if len(N) != len(Q) or not N:
        raise ValueError("rank_corr_counts: empty or mismatched null")
    if Q0 <= 0 or any(q <= 0 for q in Q):
        raise ValueError("rank_corr_counts: a constant rank vector (rho undefined)")
    if all(q == Q0 for q in Q):
        branch = RANK_BRANCH_COMMON
        kp = sum(1 for x in N if x >= N0)
        km = sum(1 for x in N if x <= N0)
    else:
        branch = RANK_BRANCH_RATIONAL
        L0 = _signed_square(N0)
        lhs = [_signed_square(x) * Q0 for x in N]
        rhs = [L0 * q for q in Q]
        kp = sum(1 for a, b in zip(lhs, rhs) if a >= b)
        km = sum(1 for a, b in zip(lhs, rhs) if a <= b)
    n = len(N)
    return dict(k_plus=kp, k_minus=km, n=n, p={1: (kp + 1) / (n + 1), -1: (km + 1) / (n + 1)}, branch=branch,
                rule=R32_RANK_RULE)


def rational_counts(num0: int, den0: int, nums, dens) -> dict:
    """R32 (b) for a rank statistic that is a ratio num / den of Python ints (e.g. R10's rank-biserial r =
    sum over group 1 of (2R - (n + 1)) / (n1 n2)): every denominator equal to the observed -> numerators compared;
    otherwise exact rationals (cross-multiplication, den > 0)."""
    num0, den0 = int(num0), int(den0)
    nums, dens = [int(x) for x in nums], [int(x) for x in dens]
    if den0 <= 0 or any(d <= 0 for d in dens) or len(nums) != len(dens) or not nums:
        raise ValueError("rational_counts: non-positive denominator or mismatched null")
    if all(d == den0 for d in dens):
        branch = RANK_BRANCH_COMMON
        kp = sum(1 for x in nums if x >= num0)
        km = sum(1 for x in nums if x <= num0)
    else:
        branch = RANK_BRANCH_RATIONAL
        kp = sum(1 for x, d in zip(nums, dens) if x * den0 >= num0 * d)
        km = sum(1 for x, d in zip(nums, dens) if x * den0 <= num0 * d)
    n = len(nums)
    return dict(k_plus=kp, k_minus=km, n=n, p={1: (kp + 1) / (n + 1), -1: (km + 1) / (n + 1)}, branch=branch,
                rule=R32_RANK_RULE)


def rank_biserial_terms(values, in_group) -> tuple[int, int]:
    """R10's rank-biserial r = (U1 - U2) / (n1 n2) as (numerator, denominator) Python ints: numerator = the doubled
    rank sum of group 1 centred by n + 1 (= 2 U1 - n1 n2), denominator n1 n2. values: one row of finite values."""
    A = centred_ranks(np.asarray(values, dtype=np.float64)[None, :])[0]
    g = np.asarray(in_group, dtype=bool)
    if g.shape != A.shape:
        raise ValueError("rank_biserial_terms: group mask of another length")
    n1, n2 = int(g.sum()), int((~g).sum())
    if n1 < 1 or n2 < 1:
        raise ValueError("rank_biserial_terms: an empty group")
    return int(sum(A[g])), n1 * n2


def welch_t(a, b) -> tuple[float, float]:
    """Welch's t of mean(a) - mean(b) (sample variances, ddof 1) and its Welch-Satterthwaite df."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.size < 2 or b.size < 2:
        raise ValueError(f"Welch t needs >= 2 values per group ({a.size}, {b.size})")
    va, vb = a.var(ddof=1) / a.size, b.var(ddof=1) / b.size
    t = (a.mean() - b.mean()) / math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (a.size - 1) + vb ** 2 / (b.size - 1))
    return float(t), float(df)


def t_p(t: float, df: float, direction: int) -> float:
    """One-sided p of a t statistic: sf (+), cdf (-) (computed as sf(-t))."""
    if direction not in DIRECTIONS:
        raise ValueError(f"direction {direction!r}")
    return float(stats.t.sf(direction * t, df))


def _chunks(n: int, chunk: int):
    if not 1 <= int(chunk) <= CHUNK_MAX:
        raise ValueError(f"chunk {chunk} outside 1..{CHUNK_MAX} (RUN_PLAN §4 memory)")
    for a in range(0, n, int(chunk)):
        yield a, min(n, a + int(chunk))


def _as_set(S, G: int) -> np.ndarray:
    S = np.asarray(S, dtype=int)
    if S.ndim != 1 or S.size < 1 or np.unique(S).size != S.size or S.min() < 0 or S.max() >= G:
        raise ValueError("S must be distinct gene indices of the class universe")
    return S


# ================================================================================================================
# analysis parcels and gene scaling (§4)
# ================================================================================================================
PARCEL_COUNT_UNITS = {"samples": ("AHBA sample(s)", "prereg.md:57-58; RUN_PLAN §4"),
                      "donors": ("donors", "RUN_PLAN R11 >= 2-donor sensitivity; §4")}


def analysis_parcels(y, ahba_sample_counts, *, parcel_ids=None, min_count: int = 1, class_parcel_ids=None,
                     count_unit: str = "samples") -> dict:
    """§4 / prereg.md:57-58: a parcel enters iff y is finite there and the parcel has >= min_count AHBA samples
    (min_count 1: the primary rule; the >= 2-donor sensitivity of R11 passes per-parcel donor counts and 2, with
    count_unit 'donors' so the recorded rule names what was counted: pre-WP4, the WP3 sensitivity records read
    '>= 2 AHBA sample(s)' for donor counts).
    y: a pandas Series indexed by parcel id, or values with parcel_ids (the class's primary parcels; the caller has
    already restricted the map to the class). ahba_sample_counts: per-parcel counts (Series or dict by parcel id).
    A parcel of y absent from the counts, or a non-finite / negative / non-integer count, is refused (a wiring
    error, never a silent drop). Returns the kept ids (in y's order) and the counts kept / dropped, by reason.
    class_parcel_ids (asdg-skeptic WP1 review C8; §4 'kept / dropped per map'): the class's parcels; a class parcel
    the map does not hold is DROPPED (counted in n_dropped, listed in dropped_absent_from_map); a map parcel outside
    the class is refused (re-parcellation is the loader's job). Without it the map's own parcels are the base."""
    if isinstance(y, pd.Series):
        if parcel_ids is not None:
            raise ValueError("analysis_parcels: give parcel ids either as the Series index or as parcel_ids")
        vals, ids = y.to_numpy(dtype=float), A3.as_parcel_ids(y.index.to_numpy(), "map y")
    else:
        vals, ids = np.asarray(y, dtype=float), A3.as_parcel_ids(parcel_ids, "map y")
    if vals.ndim != 1 or vals.shape != ids.shape:
        raise ValueError(f"analysis_parcels: {vals.shape} values for {ids.size} parcel ids")
    if count_unit not in PARCEL_COUNT_UNITS:
        raise ValueError(f"analysis_parcels: count_unit {count_unit!r} not in {sorted(PARCEL_COUNT_UNITS)}")
    counts = dict(ahba_sample_counts.items()) if hasattr(ahba_sample_counts, "items") else None
    if counts is None:
        raise ValueError("analysis_parcels: ahba_sample_counts must map parcel id -> count")
    counts = {int(k): v for k, v in counts.items()}
    missing = [int(i) for i in ids if int(i) not in counts]
    if missing:
        raise ValueError(f"analysis_parcels: parcels {missing} have no AHBA sample count (wiring error)")
    c = np.array([counts[int(i)] for i in ids], dtype=float)
    if not (np.isfinite(c).all() and (c >= 0).all() and np.array_equal(c, np.round(c))):
        raise ValueError("analysis_parcels: sample counts must be finite non-negative integers")
    fin = np.isfinite(vals)
    sampled = c >= int(min_count)
    keep = fin & sampled
    out = dict(parcel_ids=[int(i) for i in ids[keep]], n_given=int(ids.size), n_kept=int(keep.sum()),
               n_dropped=int((~keep).sum()), n_dropped_nonfinite=int((~fin).sum()),
               n_dropped_no_sample=int((~sampled).sum()), dropped_nonfinite=[int(i) for i in ids[~fin]],
               dropped_no_sample=[int(i) for i in ids[~sampled]], min_count=int(min_count),
               rule=f"finite y and >= {int(min_count)} {PARCEL_COUNT_UNITS[count_unit][0]} "
                    f"({PARCEL_COUNT_UNITS[count_unit][1]})")
    if class_parcel_ids is not None:   # C8: class parcels absent from the map are dropped and counted
        cls_ids = A3.as_parcel_ids(class_parcel_ids, "class parcels")
        cset, mset = set(int(i) for i in cls_ids), set(int(i) for i in ids)
        outside = sorted(mset - cset)
        if outside:
            raise ValueError(f"analysis_parcels: map parcels {outside} are not parcels of the class (wiring error)")
        absent = [int(i) for i in cls_ids if int(i) not in mset]
        out.update(n_class=int(cls_ids.size), n_absent_from_map=len(absent), dropped_absent_from_map=absent,
                   n_dropped=int((~keep).sum()) + len(absent),
                   rule=out["rule"] + "; class parcels absent from the map are dropped and counted (C8)")
        if out["n_kept"] + out["n_dropped"] != out["n_class"]:
            raise RuntimeError("analysis_parcels: kept + dropped != the class's parcels (a code defect)")
    return out


# A1-side class definitions of the two analysis classes a3_port.CLASS_DEFS (A3's verbatim blocks, not edited) lacks
# (asdg-skeptic WP1 review C7). Class labels are the other atlases' ('subcortex/brainstem' for MIST64's 'subcortex', as
# a1_audit/plants/common.py writes it).
MIST64_CLASSES_JSON = A3.ROOT / "arcs" / "audit" / "register_maps" / "mist64_classes.json"
MIST64_CLASS_LABEL = {"cortex": "cortex", "cerebellum": "cerebellum", "subcortex": "subcortex/brainstem",
                      "subcortex/brainstem": "subcortex/brainstem"}
A1_CLASS_DEFS = {
    "V-DK-subcortex": dict(
        atlas="dk", base="V-DK", class_counts={"subcortex/brainstem": 7},
        rule=("V-DK's subcortical parcels, single class (claims_register.md:1026 'a subcortex-only map -> V-DK's "
              "subcortical parcels, single class'; RUN_PLAN.md:1136 P9 'V-DK-subcortex (7 parcels, single class)'): the "
              "V-DK context (a3_port.build_context, L7 pin) restricted to structure 'subcortex/brainstem' and hemisphere "
              "L, i.e. without the midline brainstem (hemisphere B), 7 parcels")),
    "MIST64": dict(
        atlas="mist64", class_counts={"cerebellum": 8, "cortex": 33, "subcortex/brainstem": 5},
        rule=("native MIST64, 46 primary parcels: cortex 33, subcortex 5, cerebellum 8 (RUN_PLAN.md:1436; "
              "claims_register.md:1026 'MIST64 -> native MIST64'): A1's reader (e3_plants.primary_parcels, L + B rows) "
              "with the tissue classes of register_maps/mist64_classes.json (its 'primary' parcels; 'subcortex' written "
              "'subcortex/brainstem'), the partition asserted equal to the atlas info's; identity = the L7 pin of the "
              "round-trip read (launch.AHBA_MATRIX)")),
}


def _pin(table, key: str) -> str:
    hits = [v for k, v in table if k == key]
    if len(hits) != 1:
        raise KeyError(key)
    return hits[0]


def _mist64_classes(ids) -> np.ndarray:
    import json
    doc = json.loads(MIST64_CLASSES_JSON.read_text(encoding="utf-8"))
    prim = {int(p["roi"]): str(p["tissue_class"]) for p in doc["parcels"] if p["primary"]}
    if sorted(prim) != sorted(int(i) for i in ids):
        raise AssertionError("MIST64: the reader's primary parcels differ from mist64_classes.json's primary parcels")
    return np.array([MIST64_CLASS_LABEL[prim[int(i)]] for i in ids])


def _build_a1_class(name: str, parcel_ids=None):
    """V-DK-subcortex and MIST64 (A1_CLASS_DEFS), with R35's first-use check before the matrix's first use."""
    from . import launch as LA
    spec = A1_CLASS_DEFS[name]
    atlas = spec["atlas"]
    path = A3.AHBA / f"{atlas}_expr.csv.gz"
    expr, classes_atlas, xyz = A3._primary(atlas)
    first = LA.matrix_first_use(path, used=expr)
    if name == "V-DK-subcortex":
        base = A3.build_context(spec["base"], None, verify=True)    # V-DK: L7 pin, counts (42; 34 + 8) asserted
        hemi = base.info["hemisphere"].astype(str).to_numpy()
        keep = (base.classes == "subcortex/brainstem") & (hemi == "L")
        report = {k: base.report[k] for k in ("matrix_sha256", "file_sha256", "reader_max_abs_delta", "n_genes")
                  if k in base.report}
        ctx = A3.ClassContext(name, base.expr.loc[keep], base.classes[keep], base.xyz[keep], A3.atlas_info(atlas),
                              None, atlas, report)
    else:   # MIST64
        pin = _pin(LA.AHBA_MATRIX, atlas)
        if first["sha256_round_trip"] != pin:
            raise AssertionError(f"MIST64: round-trip read hash {first['sha256_round_trip']} != the L7 pin {pin}")
        classes = _mist64_classes(expr.index)
        norm = np.array([MIST64_CLASS_LABEL.get(str(c), f"?{c}") for c in classes_atlas])
        if not np.array_equal(classes, norm):
            raise AssertionError("MIST64: mist64_classes.json's tissue classes differ from the atlas info's")
        ctx = A3.ClassContext(name, expr, classes, xyz, A3.atlas_info(atlas), None, atlas,
                              dict(matrix_sha256=first["sha256_round_trip"], file_sha256=A3.sha256_file(path),
                                   reader_max_abs_delta=first["max_abs_delta"]))
    got = {str(c): int((ctx.classes == c).sum()) for c in np.unique(ctx.classes)}
    if got != spec["class_counts"]:
        raise AssertionError(f"{name}: class counts {got} != {spec['class_counts']} ({spec['rule']})")
    if ctx.report["n_midline"] != 0 and name == "V-DK-subcortex":
        raise AssertionError("V-DK-subcortex: a midline parcel kept")
    ctx.report["a1_class_rule"] = spec["rule"]
    return ctx if parcel_ids is None else ctx.restrict(parcel_ids)


def build_context_checked(name: str, parcel_ids=None):
    """The class-context builder with RUN_PLAN_amend_1 R35's first-use check: before the matrix's first use in this
    process, launch.matrix_first_use reads the file with float_precision='round_trip' and asserts identical index and
    gene order and max |delta| < 1e-12 against the frame A1's reader handed over (a3_port._primary, rows = the class's
    primary parcels); then a3_port.build_context (unchanged: its verify_matrix asserts the L7 pin). For the real
    loaders (WP3); the check itself is tested on synthetic files (tests/test_amend1.py). V-DK-subcortex and MIST64,
    which a3_port.CLASS_DEFS lacks, are built from A1_CLASS_DEFS (_build_a1_class; C7)."""
    from . import launch as LA
    if name in A1_CLASS_DEFS:
        return _build_a1_class(name, parcel_ids)
    atlas, _ = A3.CLASS_DEFS[name]
    expr = A3._primary(atlas)[0]
    LA.matrix_first_use(A3.AHBA / f"{atlas}_expr.csv.gz", used=expr)
    return A3.build_context(name, parcel_ids, verify=True)


def zscore_genes(X) -> np.ndarray:
    """Every gene (column) z-scored over the rows given (the analysis parcels), ddof 0, so <y^, z_g> / n is the
    Pearson r of gene g with y when y^ is standardised with ddof 0. A constant column is refused."""
    X = np.asarray(X, dtype=float)
    sd = X.std(0)
    if not (np.isfinite(X).all() and (sd > 0).all()):
        raise ValueError("zscore_genes: non-finite value or constant gene (restrict to analysis parcels and drop "
                         "constant genes first: asdg.genesets.Universe)")
    return (X - X.mean(0)) / sd


def _form(form: str) -> str:
    f = {"pls-enrichment": "PLS-enrichment", "tabs": "t-abs", "t_abs": "t-abs", "T_abs": "t-abs"}.get(form, form)
    if f not in FORMS:
        raise ValueError(f"unknown T form {form!r} (one of {FORMS})")
    return f


def prepare_matrix(form: str, X: pd.DataFrame, analysis_parcels) -> tuple[pd.DataFrame, dict]:
    """§4 gene scaling by form, on the claim's analysis parcels. X: the class's §3.1 matrix (parcels x genes, index =
    parcel ids). Rows are restricted to the analysis parcels (in X's row order, as ClassContext.restrict keeps them);
    genes constant there are dropped by asdg.genesets.Universe's rule (counted). set-vs-map and component: values
    unchanged; decoded-list, PLS-enrichment and t-abs: z-scored over those parcels (zscore_genes)."""
    f = _form(form)
    want = [int(i) for i in A3.as_parcel_ids(analysis_parcels, "analysis parcels")]
    have = set(int(i) for i in X.index)
    missing = sorted(set(want) - have)
    if missing:
        raise ValueError(f"prepare_matrix: analysis parcels {missing} are not rows of the matrix")
    wanted = set(want)
    keep = np.array([int(i) in wanted for i in X.index])
    U = Universe(X.loc[keep])
    vals = U.X if f in ("set-vs-map", "component") else zscore_genes(U.X)
    out = pd.DataFrame(vals, index=X.index[keep], columns=U.genes)
    return out, dict(form=f, scaling=SCALING[f], n_parcels=int(keep.sum()), n_genes=int(out.shape[1]),
                     n_dropped_constant=int(U.n_dropped_constant))


def z_matrix(ctx) -> np.ndarray:
    """The class context's matrix (ctx.X: the analysis parcels x the universe's genes, values unchanged) z-scored over
    its parcels (zscore_genes); cached on the context."""
    Z = ctx.__dict__.get("_a1_z")
    if Z is None:
        Z = zscore_genes(ctx.X)
        ctx.__dict__["_a1_z"] = Z
    return Z


def z_basis(ctx) -> WithinClassBasis:
    """asdg.species.WithinClassBasis, unchanged, built on the z-scored matrix (same classes, same brain>body genes):
    its parts / conditioned_null / g6s_scores / uninformative are the species objects of the z-scored set score
    (R2; prereg_amend_3.md:107). Cached on the context."""
    B = ctx.__dict__.get("_a1_zbasis")
    if B is None:
        B = WithinClassBasis(z_matrix(ctx), ctx.classes, brain=ctx.brain)
        ctx.__dict__["_a1_zbasis"] = B
    return B


# ================================================================================================================
# species draws (y-independent) with R8's pool checks
# ================================================================================================================
def pool_status(B, S) -> dict:
    """R8's feasibility of each species leg for S on basis B: G1 needs |U \\ S| >= m; G3m |(B n U) \\ S| >= f and
    |U \\ (B u S)| >= m - f; G6l a window of size m in the ranking of the G - m - 1 other genes."""
    S = _as_set(S, B.G)
    m, f = S.size, int(B.brain[S].sum())
    nb = int(B.brain.sum())
    n_rank = B.G - m - 1
    half = n_rank // 2
    if m - 1 > n_rank:
        g6l = "no window"
    elif half + m - 1 > n_rank:
        g6l = "partial"
    else:
        g6l = "ok"
    return dict(m=m, f=f, G1=bool(B.G - m >= m), G3m=bool(nb - f >= f and (B.G - nb) - (m - f) >= m - f), G6l=g6l)


def g6l_offset_max(G: int, m: int) -> int | None:
    """RUN_PLAN_amend_1 R33: the largest offset whose window W(o) = {g} u rank[o : o + m - 1] exists in the ranking of
    the n_rank = G - m - 1 other genes, min(half, n_rank - m + 1), half = n_rank // 2 (src/asdg/species.py:156-157);
    None when no window of size m fits (R8: m - 1 > n_rank)."""
    n_rank = int(G) - int(m) - 1
    if int(m) - 1 > n_rank:
        return None
    return min(n_rank // 2, n_rank - int(m) + 1)


def window_curve_range(B, g, S, m: int, n_rank: int, o_max: int, C0, *, _variant: str | None = None):
    """WithinClassBasis.window_curve (src/asdg/species.py:136-145) over the offsets o = 0 .. o_max (R33): seed g's
    ranking (float64 within-class r over the genes not in S or g), and c(W(o)) with the window sums accumulated in
    float32 in the preallocated buffer C0 ((o_max + m) x parcels, row 0 = 0). With o_max = half it is the engine's
    computation line for line (bit-identical: a cumulative sum's prefixes do not depend on its length).
    _variant (PLANT ONLY, the must-fail variants of the P10 extension): 'float64' accumulates the window sums in
    float64; 'truncated' lets o run to half with windows truncated at the end of the ranking."""
    r = B.ZwT @ B.ZwT[g]
    r[S] = -np.inf
    r[g] = -np.inf
    rank = np.argsort(-r, kind="stable")[:n_rank]
    if _variant == "float64":
        C = np.zeros((o_max + m, B.ZwT.shape[1]))
        np.cumsum(B.ZwT[rank[: o_max + m - 1]], axis=0, out=C[1:])
        v = C[m - 1: m - 1 + o_max + 1] - C[: o_max + 1]
        v += B.ZwT[g]
    elif _variant == "truncated":
        k = min(o_max + m - 1, n_rank)
        np.cumsum(B.ZwT32[rank[:k]], axis=0, out=C0[1: k + 1])
        C0[k + 1:] = C0[k]
        v = C0[m - 1: m - 1 + o_max + 1] - C0[: o_max + 1]
        v += B.ZwT32[g]
    elif _variant is None:
        np.cumsum(B.ZwT32[rank[: o_max + m - 1]], axis=0, out=C0[1:])
        v = C0[m - 1: m - 1 + o_max + 1] - C0[: o_max + 1]
        v += B.ZwT32[g]
    else:
        raise ValueError(f"window_curve_range: unknown variant {_variant!r}")
    return rank, (np.einsum("ij,ij->i", v, v, dtype=np.float64) - m) / (m * (m - 1))


def g6l_screen_range(B, S, rngs, keep=None, tol: float = A3.G6L_TOL, min_seeds: int = A3.G6L_MIN_SEEDS, *,
                     return_detail: bool = False, _variant: str | None = None):
    """RUN_PLAN_amend_1 R33: a3_port.g6l_screen (A1's exact G6l, one pass serving several streams) with the offsets
    restricted to the windows that exist: O_g = {o in [0, min(half, n_rank - m + 1)] : |c(W(o)) - c_S| <= .02}. Every
    frozen rule then applies unchanged (o uniform over O_g by each stream's rng.choice; < 50 eligible seeds ->
    'unmatched'; more than `keep` windows -> `keep` without replacement). Where the full range fits it computes exactly
    what a3_port.g6l_screen computes (sets, info and window curves bit-identical: tests/test_amend1.py); production
    calls it only in the partial range (g6l_screen_safe). The info of a partial screen carries 'offsets'.
    return_detail: also {seed: window curve} and per-stream offsets (tests)."""
    S = np.asarray(S, dtype=int)
    m, G = len(S), B.G
    n_rank = G - m - 1
    half = n_rank // 2
    o_max = g6l_offset_max(G, m)
    if o_max is None:
        raise ValueError("g6l_screen_range: no window of size m fits the ranking (R8: 'unmatched'; g6l_screen_safe)")
    if _variant == "truncated":
        o_max = half
    partial = o_max < half
    c_s = B.coherence_w(S)
    not_s = np.setdiff1d(np.arange(G), S)
    C0 = np.empty((o_max + m, B.ZwT32.shape[1]), np.float32)
    C0[0] = 0.0
    acc = [[] for _ in rngs]
    offs_acc = [[] for _ in rngs]
    curves = {}
    eligible = 0
    for g in not_s:
        rank, c = window_curve_range(B, g, S, m, n_rank, o_max, C0, _variant=_variant)
        if return_detail:
            curves[int(g)] = c
        offs = np.flatnonzero(np.abs(c - c_s) <= tol)
        if offs.size:
            eligible += 1
            for a, oa, rng in zip(acc, offs_acc, rngs):
                o = int(rng.choice(offs))
                a.append(np.concatenate([[g], rank[o: o + m - 1]]))
                oa.append(o)
    out = []
    for a, rng in zip(acc, rngs):
        info = dict(c_s=c_s, n=len(a), draws=int(not_s.size), eligible=eligible, exact=True)
        if partial:
            info["offsets"] = dict(o_max=int(o_max), half=int(half), n_rank=int(n_rank), partial=bool(partial),
                                   rule="R33: o in [0, min(half, n_rank - m + 1)] (RUN_PLAN_amend_1.md)")
        if len(a) < min_seeds:
            out.append((None, {**info, "status": "unmatched", "n_used": 0}))
            continue
        if len({len(w) for w in a}) != 1:   # only a truncated (plant) variant gives ragged windows
            out.append((list(a), {**info, "status": "ok", "n_used": int(len(a))}))
            continue
        sets = np.stack(a)
        if keep is not None and len(sets) > keep:
            sets = sets[rng.choice(len(sets), size=keep, replace=False)]
        out.append((sets, {**info, "status": "ok", "n_used": int(len(sets))}))
    if return_detail:
        return out, dict(curves=curves, offsets=[list(oa) for oa in offs_acc], o_max=int(o_max), half=int(half),
                         n_rank=int(n_rank))
    return out


def g6l_sets_range(B, S, K: int, rng, tol: float = 0.02, budget_factor: int = 5, min_seeds: int = 50,
                   exact: bool = False):
    """RUN_PLAN_amend_1 R33 for asdg.species.WithinClassBasis.g6l_sets (src/asdg/species.py:147-176, line for line,
    plant mode included: exact=False screens rng.permutation(non-S genes)[: budget_factor * K] and stops at K accepted)
    with the offsets restricted to o in [0, min(half, n_rank - m + 1)]. Equal to the engine's g6l_sets wherever the
    full range fits (tests/test_amend1.py); for plant_mode's partial-range case. No window -> ValueError (R8 is the
    caller's)."""
    S = np.asarray(S)
    m, G = len(S), B.G
    o_max = g6l_offset_max(G, m)
    if o_max is None:
        raise ValueError("g6l_sets_range: no window of size m fits the ranking (R8)")
    c_s = B.coherence_w(S)
    not_s = np.setdiff1d(np.arange(G), S)
    seeds = not_s if exact else rng.permutation(not_s)[: budget_factor * K]
    accepted, draws, eligible = [], 0, 0
    n_rank = G - m - 1
    C0 = np.empty((o_max + m, B.ZwT32.shape[1]), np.float32)
    C0[0] = 0.0
    for g in seeds:
        draws += 1
        rank, c = window_curve_range(B, g, S, m, n_rank, o_max, C0)
        offs = np.flatnonzero(np.abs(c - c_s) <= tol)
        if offs.size:
            eligible += 1
            o = int(rng.choice(offs))
            accepted.append(np.concatenate([[g], rank[o: o + m - 1]]))
            if not exact and len(accepted) >= K:
                break
    info = dict(c_s=c_s, n=len(accepted), draws=draws, eligible=eligible, exact=exact)
    if len(accepted) < min_seeds:
        return None, {**info, "status": "unmatched"}
    sets = np.stack(accepted)
    if exact and len(sets) > K:
        sets = sets[rng.choice(len(sets), size=K, replace=False)]
    return sets, {**info, "status": "ok"}


def g6l_screen_safe(B, S, rngs, keep=None) -> list:
    """a3_port.g6l_screen (A1's exact G6l, one pass serving several streams: RUN_PLAN §4 'Shared G6l screens') with
    R8's rule: no window of size m fits the ranking -> no eligible seed -> 'unmatched' for every stream (the frozen
    'fewer than 50 eligible seeds', prereg_amend_3.md:131-132), never a crash. RUN_PLAN_amend_1 R33: a window that fits
    only part of the offset range [0, half] -> g6l_screen_range (offsets o <= n_rank - m + 1); where the full range
    fits the frozen a3_port.g6l_screen is used unchanged."""
    S = _as_set(S, B.G)
    st = pool_status(B, S)
    if st["G6l"] == "partial":
        return g6l_screen_range(B, S, list(rngs), keep=keep)
    if st["G6l"] == "no window":
        info = dict(c_s=float(B.coherence_w(S)), n=0, draws=int(B.G - S.size), eligible=0, exact=True,
                    status="unmatched", n_used=0,
                    reason="no window of size m fits the ranking: no eligible seed (RUN_PLAN R8)")
        return [(None, dict(info)) for _ in rngs]
    return A3.g6l_screen(B, S, list(rngs), keep=keep)


def species_null_scores(Bd, S, K: int, seed_of, *, screen_basis=None, g6l=None) -> dict:
    """a3_port.species_draws (h_verdicts.py:319), leg by leg on the same seeded streams, with R8's pool checks (a leg
    whose pool cannot supply a set is None with status NOT_COMPUTABLE; G6l 'unmatched' when no window fits).
    Bd: the WithinClassBasis the conditioned null scores s_B(S) + s_W(R) are built on (ctx.B for set-vs-map;
    z_basis(ctx) for decoded-list / PLS-enrichment). screen_basis: the basis the G6l windows are screened on (default
    Bd; the adapters pass ctx.B, whose within-class Pearson coexpression is the frozen definition on X^w and is
    invariant to per-gene z-scoring, so one screen serves every form: §4 'Shared G6l screens'). g6l: an already
    screened (sets, info) for this row's G6l stream. Equal to species_draws(ctx, ...) bit for bit when every pool
    suffices and screen_basis is Bd (tests/test_p0.py)."""
    S = _as_set(S, Bd.G)
    rng = {leg: np.random.default_rng(seed_of(leg)) for leg in SPECIES_LEGS}
    st = pool_status(Bd, S)
    status = {}
    null = {}
    null["G1"] = A3.g1_null_chunked(Bd, S, K, rng["G1"]) if st["G1"] else None
    status["G1"] = "ok" if st["G1"] else NOT_COMPUTABLE
    null["G3m"] = A3.g3m_null_chunked(Bd, S, K, rng["G3m"]) if st["G3m"] else None
    status["G3m"] = "ok" if st["G3m"] else NOT_COMPUTABLE
    null["G6s"] = Bd.g6s_scores(S, K, rng["G6s"])
    status["G6s"] = "ok"
    exact6s = Bd.g6s_exact(K)
    n6s = 2 ** Bd.U.shape[1] if exact6s else K
    sb = Bd if screen_basis is None else screen_basis
    sets, info = g6l if g6l is not None else g6l_screen_safe(sb, S, [rng["G6l"]], keep=K)[0]
    N6l, info = A3.g6l_pool(Bd, S, sets, info)
    null["G6l"] = N6l
    status["G6l"] = info["status"]
    floors = {}
    if st["G1"]:
        floors["G1"] = 1 / (K + 1)
    if st["G3m"]:
        floors["G3m"] = 1 / (K + 1)
    floors["G6s"] = 2 / (n6s + 1) if exact6s else 1 / (K + 1)
    if info["status"] == "ok":
        floors["G6l"] = 1 / (info["n_used"] + 1)
    # RUN_PLAN_amend_1 R32 (a): the exact G6s enumeration's identity row (the last: all signs +) reconstructs S's set
    # score on the leg's basis, s_B + mu_S + U U^T (s_W - mu_S) = s
    return dict(null=null, status=status, g6l_info=info, g6l_sets=sets, floors=floors, g6s_exact=bool(exact6s),
                n_G6s=int(n6s), K=int(K), pools=st, g6s_identity_input=Bd.parts(S)[0])


def g1_set_chunks(G: int, S, K: int, rng, chunk: int = CHUNK_MAX):
    """G1 sets (uniform from the universe minus S) in chunks, with EXACTLY the rng calls of a3_port.g1_null_chunked /
    WithinClassBasis.g1_null (one rng.choice(pool, m, replace=False) per set, in order)."""
    S = np.asarray(S, dtype=int)
    pool = np.setdiff1d(np.arange(G), S)
    for a, b in _chunks(K, chunk):
        yield np.stack([rng.choice(pool, size=len(S), replace=False) for _ in range(b - a)])


def g3m_set_chunks(brain_mask, S, K: int, rng, chunk: int = CHUNK_MAX):
    """G3m sets (f from B \\ S, m - f from the rest minus S) in chunks, with exactly the rng calls of
    a3_port.g3m_null_chunked / WithinClassBasis.g3m_sets."""
    S = np.asarray(S, dtype=int)
    brain = np.asarray(brain_mask, dtype=bool)
    f = int(brain[S].sum())
    pb = np.setdiff1d(np.flatnonzero(brain), S)
    pn = np.setdiff1d(np.flatnonzero(~brain), S)
    for a, b in _chunks(K, chunk):
        yield np.stack([np.concatenate([rng.choice(pb, size=f, replace=False),
                                        rng.choice(pn, size=len(S) - f, replace=False)]) for _ in range(b - a)])


# ================================================================================================================
# the adapters
# ================================================================================================================
class _Form:
    form = None
    full_verdict = True
    conditioned = True

    def __init__(self, ctx, y, *, parcel_ids, what: str):
        y = A3.align_to_context(ctx, y, parcel_ids, what)
        if y.shape != (ctx.n,) or not np.isfinite(y).all():
            raise ValueError(f"{what}: the map must be finite on the analysis parcels ({y.shape}, ctx {ctx.n})")
        if not np.std(y) > 0:
            raise ValueError(f"{what}: the map is constant on the analysis parcels")
        self.ctx, self.y, self.n = ctx, y, int(ctx.n)
        self.parcel_ids = [int(i) for i in ctx.parcel_ids]

    # -- interface shared by every form ---------------------------------------------------------------------------
    def site_input(self) -> np.ndarray:
        """The map the site leg randomises (y itself for every A1 form)."""
        return self.y

    def level0_both(self) -> dict:
        return {d: self.level0(self.T_obs, d) for d in DIRECTIONS}

    def site_leg(self, K: int, seed_of, chunk: int = CHUNK_MAX, *, return_surrogates: bool = False,
                 _identity_index=None) -> dict:
        """S1c and S2c (spatial.site_null: class-stratified; exact enumeration when the randomisation has <= K
        patterns), each scored with this form's T (refit where the form refits) and given p in both directions.
        seed_of(leg) -> SeedSequence; the integer seed is int(default_rng(SS).integers(2**31)) (R7).
        RUN_PLAN_amend_1 R32 (a) / (c) on an exact leg: the identity row (row 0 of spatial.stratified_exact) must
        reconstruct site_input(); its null statistic and that of every bit-identical row := T_obs; p >= the declared
        floor 2/(N + 1) asserted; the count is recorded in info['identity']. Sampled legs are untouched.
        return_surrogates: keep each leg's surrogate maps (tests, P13). _identity_index: PLANT ONLY (the wrong-index
        must-fail variant)."""
        out = {}
        for leg, method in SITE_LEGS:
            seed = int(np.random.default_rng(seed_of(leg)).integers(2 ** 31))
            sur, info = site_null(self.site_input(), self.ctx.D, self.ctx.classes, K, seed, method)
            null = self.T_maps(sur, chunk=chunk)
            rinfo = dict(exact=bool(info["exact"]), n_null=int(info["n_null"]), n_patterns=float(info["n_patterns"]),
                         floor=float(info["floor"]))
            if info["exact"]:
                idx = 0 if _identity_index is None else int(_identity_index)
                rows, dev = identity_rows(sur, idx, self.site_input(), f"{self.form} {leg} (exact)")
                null = count_identity(null, rows, self.T_obs)
                rinfo["identity"] = identity_record(idx % len(sur), rows, dev, len(sur))
            p = p_both(null, self.T_obs)
            if info["exact"]:
                assert_exact_floor(p, info["floor"], f"{self.form} {leg} (exact)")
            out[leg] = dict(null=null, p=p, floor=float(info["floor"]), seed=seed, info=rinfo)
            if return_surrogates:
                out[leg]["surrogates"] = sur
        return out

    def record(self) -> dict:
        return dict(form=self.form, T=float(self.T_obs), n_parcels=self.n, parcel_ids=self.parcel_ids,
                    full_verdict=self.full_verdict, conditioned_species=self.conditioned)


class SetVsMap(_Form):
    """set-vs-map (claims_register.md:283-284; RUN_PLAN §4): T = Pearson r(y, s), s = ctx.score(S) = per-parcel mean of
    S's columns of the matrix UNCHANGED; Level 0 = parametric p of r (a3_port.CorrStat.level0 = cascade.naive_p); site
    leg r(y*, s); species legs as A3's claim_verdict builds them (a3_port.species_draws on ctx.B, scored by
    CorrStat.T, the engine's Pearson scorer)."""
    form = "set-vs-map"

    def __init__(self, ctx, y, S, *, parcel_ids):
        super().__init__(ctx, y, parcel_ids=parcel_ids, what="set-vs-map map y")
        self.S = _as_set(S, ctx.G)
        self.stat = A3.CorrStat(self.y)
        self.s = ctx.score(self.S)
        self.T_obs = float(self.stat.T(self.s)[0])

    @property
    def basis(self):
        return self.ctx.B

    def T(self, scores) -> np.ndarray:
        return self.stat.T(scores)

    def T_maps(self, maps, s=None, chunk: int = CHUNK_MAX) -> np.ndarray:
        s = self.s if s is None else s
        maps = np.atleast_2d(maps)
        return np.concatenate([self.stat.T_maps(maps[a:b], s) for a, b in _chunks(len(maps), chunk)])

    def level0(self, t: float, direction: int) -> float:
        return self.stat.level0(t, direction)

    def spearman(self) -> float:
        """Spearman's rho beside Level 0 (claims_register.md:284)."""
        return float(stats.spearmanr(self.y, self.s).statistic)

    def species_leg(self, K: int, seed_of, g6l=None, *, _identity_index=None) -> dict:
        dr = species_null_scores(self.ctx.B, self.S, K, seed_of, screen_basis=self.ctx.B, g6l=g6l)
        return _score_species(self, dr, self.T_obs, _identity_index=_identity_index)

    def uninformative(self) -> tuple[bool, float]:
        return self.ctx.B.uninformative(self.S, self.y)

    def T_sets(self, sets, chunk: int = CHUNK_MAX) -> np.ndarray:
        """Unconditioned null sets scored with T (descriptor legs, R6; Level-2 G1, R24): r(y, mean of R's columns)."""
        sets = np.atleast_2d(np.asarray(sets, dtype=int))
        B = self.ctx.B
        return np.concatenate([self.stat.T(B.set_means(B.X, sets[a:b])) for a, b in _chunks(len(sets), chunk)])

    def T_sets_maps(self, sets, maps, chunk: int = CHUNK_MAX) -> np.ndarray:
        """(n_maps, n_sets): T of every set on every map (J1, R4)."""
        sets = np.atleast_2d(np.asarray(sets, dtype=int))
        sc = self.ctx.B.set_means(self.ctx.B.X, sets)
        maps = np.atleast_2d(maps)
        return np.concatenate([corr_matrix(maps[a:b], sc) for a, b in _chunks(len(maps), chunk)])

    def T_pairs(self, sets, maps, chunk: int = CHUNK_MAX) -> np.ndarray:
        """T(set_i, map_i) for paired rows (the naive joint, R5; cascade.naive_joint's pairing)."""
        sets = np.atleast_2d(np.asarray(sets, dtype=int))
        maps = np.atleast_2d(maps)
        assert len(sets) == len(maps)
        out = []
        for a, b in _chunks(len(maps), chunk):
            sc = self.ctx.B.set_means(self.ctx.B.X, sets[a:b])
            out.append(np.einsum("ij,ij->i", _rows_z(maps[a:b]), _rows_z(sc)))
        return np.concatenate(out)


class DecodedList(_Form):
    """decoded-list (claims_register.md:285-289; prereg_amend_4.md:86-97; RUN_PLAN R2, R3): genes z-scored over the
    analysis parcels, y^ standardised; T = <y^, s_z(S)> / n (s_z not re-standardised) = mean_{g in S} r_g."""
    form = "decoded-list"

    def __init__(self, ctx, y, S, *, parcel_ids):
        super().__init__(ctx, y, parcel_ids=parcel_ids, what=f"{self.form} map y")
        self.S = _as_set(S, ctx.G)
        self.Z = z_matrix(ctx)
        self.yh = A3.zscore(self.y)
        self.r = self.Z.T @ self.yh / self.n  # every gene's Pearson r with y
        self.in_S = np.zeros(ctx.G, bool)
        self.in_S[self.S] = True
        self.s_z = self.Z[:, self.S].mean(1)
        self.T_dec = float(DecodedList.T(self, self.s_z)[0])  # <y^, s_z(S)> / n (the subclasses keep it)
        self.T_obs = self.T_dec

    @property
    def basis(self) -> WithinClassBasis:
        return z_basis(self.ctx)

    def T(self, scores) -> np.ndarray:
        """Rows of z-scored set scores (the conditioned species nulls) -> <y^, score> / n (no re-standardisation)."""
        return np.atleast_2d(np.asarray(scores, dtype=float)) @ self.yh / self.n

    def gene_r_maps(self, maps, genes=None, chunk: int = CHUNK_MAX) -> np.ndarray:
        """Per-gene Pearson r of every map row with the given genes (default all), recomputed per map: z(map) Z / n,
        in chunks of <= 1,000 maps (§4 memory: Z^T Y*). (n_maps, n_genes)."""
        maps = np.atleast_2d(np.asarray(maps, dtype=float))
        Zg = self.Z if genes is None else self.Z[:, np.asarray(genes, dtype=int)]
        out = np.empty((len(maps), Zg.shape[1]))
        for a, b in _chunks(len(maps), chunk):
            Yh = maps[a:b] - maps[a:b].mean(1, keepdims=True)
            Yh /= Yh.std(1, keepdims=True)
            out[a:b] = Yh @ Zg / self.n
        return out

    def _gene_stat(self, R):
        return R

    def T_maps(self, maps, s=None, chunk: int = CHUNK_MAX) -> np.ndarray:
        """Site leg: every per-gene r of S recomputed on each map, then T (the mean over S)."""
        if s is not None:
            raise ValueError(f"{self.form}: T_maps recomputes the per-gene statistic on each map; no set score taken")
        maps = np.atleast_2d(maps)
        return np.concatenate([self._gene_stat(self.gene_r_maps(maps[a:b], self.S, chunk)).mean(1)
                               for a, b in _chunks(len(maps), chunk)])

    def _level0_values(self):
        return self.r

    def level0_t(self) -> tuple[float, float]:
        v = self._level0_values()
        return welch_t(v[self.in_S], v[~self.in_S])

    def level0(self, t: float, direction: int) -> float:
        """Welch t of S's per-gene statistic against the rest of the universe (prereg §4.7's enrichment Level 0),
        one-sided in `direction` (sf / cdf). t must be this claim's observed T (the Welch t does not depend on it)."""
        if not abs(float(t) - self.T_obs) <= 1e-12 * max(1.0, abs(self.T_obs)):
            raise ValueError(f"{self.form}: level0 takes the observed T ({self.T_obs}), got {t}")
        tw, df = self.level0_t()
        return t_p(tw, df, direction)

    def species_leg(self, K: int, seed_of, g6l=None, *, _identity_index=None) -> dict:
        """Conditioned species legs on the z-scored matrix: null scores s_B(S) + s_W(R) of z_basis (G1, G3m, G6l
        windows screened on ctx.B; G6s on z_basis), each scored <y^, .> / n (R2)."""
        dr = species_null_scores(self.basis, self.S, K, seed_of, screen_basis=self.ctx.B, g6l=g6l)
        return _score_species(self, dr, self._species_obs(), _identity_index=_identity_index)

    def _species_obs(self) -> float:
        return self.T_obs

    def uninformative(self) -> tuple[bool, float]:
        """Amendment 3 §2's rule on G6s's components, here those of the z-scored matrix (G6s's basis)."""
        return self.basis.uninformative(self.S, self.y)

    def T_sets(self, sets, chunk: int = CHUNK_MAX) -> np.ndarray:
        """Unconditioned null sets scored with T: mean of the per-gene statistic over R (descriptor legs, R6)."""
        sets = np.atleast_2d(np.asarray(sets, dtype=int))
        v = self._set_values()
        return np.concatenate([v[sets[a:b]].mean(1) for a, b in _chunks(len(sets), chunk)])

    def _set_values(self):
        return self.r

    def T_sets_maps(self, sets, maps, chunk: int = CHUNK_MAX) -> np.ndarray:
        """(n_maps, n_sets): every set's T on every map, the per-gene statistic recomputed per map (J1, R4)."""
        sets = np.atleast_2d(np.asarray(sets, dtype=int))
        M = self.ctx.B.membership(sets)
        maps = np.atleast_2d(maps)
        out = []
        for a, b in _chunks(len(maps), chunk):
            R = self._gene_stat(self._all_gene_stat_maps(maps[a:b], chunk))
            out.append(np.asarray(M @ R.T).T / sets.shape[1])
        return np.concatenate(out)

    def _all_gene_stat_maps(self, maps, chunk):
        return self.gene_r_maps(maps, None, chunk)

    def T_pairs(self, sets, maps, chunk: int = CHUNK_MAX) -> np.ndarray:
        """T(set_i, map_i) for paired rows (the naive joint, R5)."""
        sets = np.atleast_2d(np.asarray(sets, dtype=int))
        maps = np.atleast_2d(maps)
        assert len(sets) == len(maps)
        out = []
        for a, b in _chunks(len(maps), chunk):
            R = self._gene_stat(self._all_gene_stat_maps(maps[a:b], chunk))
            out.append(np.take_along_axis(R, sets[a:b], axis=1).mean(1))
        return np.concatenate(out)

    def mean_fisher_z(self) -> float:
        """Reproduction descriptor only (prereg_amend_4.md §2): the mean Fisher-z of S's per-gene r."""
        return float(np.arctanh(self.r[self.S]).mean())


class PlsEnrichment(DecodedList):
    """PLS-enrichment (claims_register.md:290-291; prereg.md:186-189; RUN_PLAN R3): w = cascade.pls1's PLS1 weight
    (Z^T y / ||Z^T y|| over the full universe, oriented corr(score, y) > 0), T = mean_{g in S} w_g; PLS1 refit on every
    surrogate; Level 0 = Welch t of S's weights against all others. w = r / ||r||, so the species nulls are
    DecodedList's times 1 / ||r|| and the species p's are DecodedList's (P7)."""
    form = "PLS-enrichment"

    def __init__(self, ctx, y, S, *, parcel_ids):
        super().__init__(ctx, y, S, parcel_ids=parcel_ids)
        W, R2 = pls1(ctx.X, self.y)
        self.w, self.R2 = W[0], float(R2[0])
        self.kappa = 1.0 / float(np.linalg.norm(self.r))
        dev = float(np.max(np.abs(self.w - self.r * self.kappa)))
        if not dev < 1e-10:  # apparatus: the engine's weight is the normalised per-gene r (orientation +)
            raise AssertionError(f"PLS1 weight != r / ||r|| (max |delta| {dev})")
        self.T_obs = float(self.w[self.S].mean())
        if not abs(self.T_obs - self._species_obs()) < 1e-12:
            raise AssertionError("PLS T != kappa * decoded-list T")

    def T(self, scores) -> np.ndarray:
        """Species null scores -> kappa * <y^, score> / n (each null set's mean weight, weights and y fixed)."""
        return self.kappa * super().T(scores)

    def _species_obs(self) -> float:
        # the species legs compare kappa * (DecodedList's null) with kappa * (DecodedList's observed T): a positive
        # constant factor, so the counts are DecodedList's (P7); equal to T_obs to < 1e-12 (asserted above)
        return float(self.kappa * self.T_dec)

    def T_maps(self, maps, s=None, chunk: int = CHUNK_MAX) -> np.ndarray:
        """Site leg: PLS1 refit on every map (cascade.pls1 on chunks of <= 1,000 maps), T* = mean_{g in S} w*_g."""
        if s is not None:
            raise ValueError("PLS-enrichment: T_maps refits PLS1 on each map; no set score is taken")
        maps = np.atleast_2d(maps)
        return np.concatenate([pls1(self.ctx.X, maps[a:b])[0][:, self.S].mean(1) for a, b in _chunks(len(maps), chunk)])

    def _level0_values(self):
        return self.w

    def _set_values(self):
        return self.w

    def _all_gene_stat_maps(self, maps, chunk):
        return pls1(self.ctx.X, maps)[0]


class TAbs(DecodedList):
    """T_abs descriptor (claims_register.md:309-313; RUN_PLAN P11): T = mean over S of |per-gene r|; upper tail (lower
    tail for a stated depletion); Level 0 Welch t of |r|; site leg (per-gene r recomputed per surrogate); unconditioned
    G1, G3m, G6l; no G6s. Labelled 'unsigned descriptor, uncalibrated ...'; never 'detects' or 'survives'."""
    form = "t-abs"
    full_verdict = False
    conditioned = False
    LABEL = ("unsigned descriptor, uncalibrated (no plant for |r|; |r| favours smooth, brain-enriched genes)")
    SPECIES = ("G1", "G3m", "G6l")

    def __init__(self, ctx, y, S, *, parcel_ids):
        super().__init__(ctx, y, S, parcel_ids=parcel_ids)
        self.absr = np.abs(self.r)
        self.T_obs = float(self.absr[self.S].mean())

    @staticmethod
    def registered_direction(depletion: bool = False) -> int:
        """Upper tail; lower tail for a stated depletion (claims_register.md:310)."""
        return -1 if depletion else 1

    def T(self, scores):
        raise TypeError("t-abs has no set-score form (|r| does not decompose); its species legs score sets (T_sets)")

    def _gene_stat(self, R):
        return np.abs(R)

    def _level0_values(self):
        return self.absr

    def _set_values(self):
        return self.absr

    def uninformative(self):
        raise TypeError("t-abs has no G6s (claims_register.md:311), so the uninformative rule does not apply")

    def species_leg(self, K: int, seed_of, g6l=None, chunk: int = CHUNK_MAX) -> dict:
        """Unconditioned G1, G3m and G6l, each on its own seeded stream (seed_of names 'G1', 'G3m', 'G6l'; the driver
        maps them onto legs 23, 24, 25): every null set R scored mean_{g in R} |r_g|. G1 / G3m sets are drawn with the
        rng calls of the frozen builders (g1_set_chunks / g3m_set_chunks); G6l windows come from the shared screen on
        ctx.B (g6l: this row's (sets, info), else screened here on the 'G6l' stream); its status (unmatched /
        degenerate) by a3_port.g6l_pool."""
        B = self.ctx.B
        st = pool_status(B, self.S)
        null, status, floors = {}, {}, {}
        for leg, gen in (("G1", lambda rng: g1_set_chunks(B.G, self.S, K, rng, chunk)),
                         ("G3m", lambda rng: g3m_set_chunks(B.brain, self.S, K, rng, chunk))):
            if st[leg]:
                rng = np.random.default_rng(seed_of(leg))
                null[leg] = np.concatenate([self.T_sets(c, chunk) for c in gen(rng)])
                status[leg], floors[leg] = "ok", 1 / (K + 1)
            else:
                null[leg], status[leg] = None, NOT_COMPUTABLE
        sets, info = g6l if g6l is not None else g6l_screen_safe(
            B, self.S, [np.random.default_rng(seed_of("G6l"))], keep=K)[0]
        _, info = A3.g6l_pool(B, self.S, sets, info)
        status["G6l"] = info["status"]
        null["G6l"] = self.T_sets(sets, chunk) if (sets is not None and info["status"] == "ok") else None
        if info["status"] == "ok":
            floors["G6l"] = 1 / (info["n_used"] + 1)
        p = {leg: (p_both(N, self.T_obs) if N is not None else None) for leg, N in null.items()}
        return dict(null=null, p=p, status=status, floors=floors, g6l_info=g6l_public(info), conditioned=False,
                    K=int(K), pools=st, label=self.LABEL)


def g6l_public(info: dict) -> dict:
    """a3_port._g6l_public (the copied A3 block, unchanged) plus, for a partial-range screen, R33's offset record."""
    pub = A3._g6l_public(info)
    if "offsets" in info:
        pub["offsets"] = dict(info["offsets"])
    return pub


def _score_species(ad, dr: dict, obs: float, *, _identity_index=None) -> dict:
    """Score the conditioned species null scores with the form's T and give every computable leg's p in both
    directions; a leg whose null is None (R8, or G6l not ok) has p None. RUN_PLAN_amend_1 R32 (a) / (c) on an exact
    G6s: the identity row (the last; _identity_index: PLANT ONLY, the wrong-index must-fail variant) and its
    bit-identical duplicates are counted with the observed statistic, and p >= the declared floor is asserted."""
    null, p = {}, {}
    ident = None
    g6_ok = dr["g6l_info"]["status"] == "ok"
    for leg in SPECIES_LEGS:
        N = dr["null"][leg]
        if N is None or (leg == "G6l" and not g6_ok):
            null[leg], p[leg] = None, None
        else:
            null[leg] = ad.T(N)
            exact = leg == "G6s" and dr["g6s_exact"]
            if exact:
                idx = -1 if _identity_index is None else int(_identity_index)
                rows, dev = identity_rows(N, idx, dr["g6s_identity_input"], f"{ad.form} G6s (exact)")
                null[leg] = count_identity(null[leg], rows, obs)
                ident = identity_record(idx % len(N), rows, dev, len(N))
            p[leg] = p_both(null[leg], obs)
            if exact:
                assert_exact_floor(p[leg], dr["floors"]["G6s"], f"{ad.form} G6s (exact)")
    return dict(null=null, p=p, status=dict(dr["status"]), floors=dict(dr["floors"]),
                g6l_info=g6l_public(dr["g6l_info"]), g6s_exact=dr["g6s_exact"], n_G6s=dr["n_G6s"], K=dr["K"],
                conditioned=True, pools=dr["pools"], species_obs=float(obs), g6s_identity=ident)


def level2_g1(ad, K: int, seed_of, chunk: int = CHUNK_MAX) -> dict:
    """R24: Level-2 G1 = the leg-2 G1 sets (seed_of('G1'), the same stream as the species G1) scored UNCONDITIONED
    with the row's T (ad.T_sets); p in both directions. On a single-class map it equals the species G1 (asserted in
    tests/test_p0.py). R8: pool < m -> NOT_COMPUTABLE."""
    B = ad.ctx.B
    if not pool_status(B, ad.S)["G1"]:
        return dict(null=None, p=None, status=NOT_COMPUTABLE)
    rng = np.random.default_rng(seed_of("G1"))
    null = np.concatenate([ad.T_sets(c, chunk) for c in g1_set_chunks(B.G, ad.S, K, rng, chunk)])
    return dict(null=null, p=p_both(null, ad.T_obs), status="ok", floor=1 / (K + 1))


# ================================================================================================================
# component forms (prereg §4.7; claims_register.md:292-294; amendment 4 §2; RUN_PLAN P12)
# ================================================================================================================
R34_CONSTRUCTION = ("R34: T refit on the rows of default_rng(SS).permuted(np.tile(y, (K, 1)), axis=1): independent uniform "
                    "permutations of all analysis parcels, in the class's parcel order (not within class; identity not "
                    "excluded; with replacement); p = (k + 1)/(K + 1) per direction (RUN_PLAN_amend_1.md)")


def assert_not_enumerable(n: int, what: str = "component map") -> None:
    """RUN_PLAN_amend_1 R34 (C3), the unreachable-case assertion: a component map with n! <= 10,000 (n <= 7) would fall
    under amendment 3 §2's 'enumerated exactly'; the registered component classes have >= 34 parcels, so the runner
    asserts n! > 10,000 and stops otherwise (reaching it needs a frozen amendment)."""
    if not math.factorial(int(n)) > R34_ENUM_LIMIT:
        raise FunctionalDefect(f"R34 (C3): {what} with n = {int(n)} parcels has n! = {math.factorial(int(n))} <= "
                               f"{R34_ENUM_LIMIT:,}: amendment 3 §2 would enumerate it exactly; unreachable at the "
                               "registered sizes (>= 34 parcels) and needs a frozen amendment; the run stops")


class _Component(_Form):
    full_verdict = False
    conditioned = False
    LABEL = "site leg only; not calibrated against expression-aligned maps"
    LEVEL0_SEED_LEG = "permutation"  # leg 8 (R34: the Level-0 permutation key of the non-selected component claims)
    LEVEL0_KIND = "permutation (leg 8)"

    def species_leg(self, *a, **k):
        raise TypeError(f"{self.form}: component-level claims have no species leg (prereg.md:180-181)")

    def permutation_maps(self, K: int, rng) -> np.ndarray:
        """R34's construction (A3's B0 draws, h_verdicts.py:1134-1135): K independent uniform permutations of all the
        analysis parcels, rng.permuted on K stacked copies of y (axis 1). The n! > 10,000 assertion first (C3)."""
        assert_not_enumerable(self.n, f"{self.form} map")
        return rng.permuted(np.tile(self.y, (int(K), 1)), axis=1)

    def permutation_null(self, K: int, rng, chunk: int = CHUNK_MAX) -> np.ndarray:
        """Level 0: K parcel-label permutations of y with refit (prereg.md:179-180), drawn as A3's B0 draws them
        (rng.permuted on K stacked copies of y, h_verdicts.py:1135); T refit on each (R34)."""
        return self.T_maps(self.permutation_maps(K, rng), chunk=chunk)

    def level0_perm(self, K: int, seed_of, chunk: int = CHUNK_MAX, *, return_maps: bool = False) -> dict:
        """Level 0 by permutation, p in both directions. Key (R34, the §4 legs table read row by row): leg 8,
        seed_of('permutation'), for the non-selected component claims; leg 10, seed_of('re-selection'), for selected
        lists (SelectedList). One generator per leg; after the T refits its state is asserted equal to its state after
        the permutation draws alone (the refit, re-selection included, draws nothing from it)."""
        rng = np.random.default_rng(seed_of(self.LEVEL0_SEED_LEG))
        Yp = self.permutation_maps(K, rng)
        state = rng.bit_generator.state
        null = self.T_maps(Yp, chunk=chunk)
        if rng.bit_generator.state != state:
            raise FunctionalDefect("R34: the Level-0 generator moved during the refits (re-selection drew from it)")
        rec = dict(null=null, p=p_both(null, self.T_obs), floor=1 / (K + 1), seed_leg=self.LEVEL0_SEED_LEG,
                   kind=self.LEVEL0_KIND, construction=R34_CONSTRUCTION)
        if return_maps:  # tests (P12 / P13 extensions): the permuted maps and the generator's state after the refits
            rec["maps"] = Yp
            rec["generator_state_after"] = rng.bit_generator.state
        return rec


class FixedComponent(_Component):
    """A fixed component (HAN-C1, DEAR-C1..3): T = Pearson r(y, component as given); Level 0 = parametric p of r;
    class-stratified site leg r(y*, component)."""
    form = "component (fixed)"

    def __init__(self, ctx, y, component, *, parcel_ids):
        super().__init__(ctx, y, parcel_ids=parcel_ids, what="component claim map y")
        c = A3.align_to_context(ctx, component, parcel_ids, "fixed component")
        if not (np.isfinite(c).all() and np.std(c) > 0):
            raise ValueError("fixed component: non-finite or constant on the analysis parcels")
        self.component = c
        self.stat = A3.CorrStat(self.y)
        self.T_obs = float(self.stat.T(c)[0])

    def T_maps(self, maps, s=None, chunk: int = CHUNK_MAX) -> np.ndarray:
        maps = np.atleast_2d(maps)
        c = self.component if s is None else s
        return np.concatenate([self.stat.T_maps(maps[a:b], c) for a, b in _chunks(len(maps), chunk)])

    def level0(self, t: float, direction: int) -> float:
        return self.stat.level0(t, direction)

    def permutation_null(self, *a, **k):
        raise TypeError("a fixed component's Level 0 is the parametric p of r (claims_register.md:293)")


class Pls1R2(_Component):
    """PLS1 R^2 (RG-01, BUCH-C1..4, MAMAT-C1 / C3): T = R^2 of cascade.pls1, computed for many maps at once by the
    copied a3_port.PLS1R2 (h_verdicts.py:1103; asserted against cascade.pls1 on y); Level 0 = permutations with
    refit; site leg refit on every surrogate. genes: column indices of ctx.X (default all)."""
    form = "component (PLS1 R2)"

    def __init__(self, ctx, y, *, parcel_ids, genes=None):
        super().__init__(ctx, y, parcel_ids=parcel_ids, what="PLS1 R2 map y")
        self.genes = None if genes is None else np.asarray(genes, dtype=int)
        self.X = ctx.X if self.genes is None else ctx.X[:, self.genes]
        self.f = A3.PLS1R2(self.X)
        self.T_obs = float(self.f(self.y)[0])
        ref = float(pls1(self.X, self.y)[1][0])
        if not abs(self.T_obs - ref) < 1e-10:
            raise AssertionError(f"PLS1R2 {self.T_obs} != cascade.pls1 {ref}")

    def T_maps(self, maps, s=None, chunk: int = CHUNK_MAX) -> np.ndarray:
        maps = np.atleast_2d(maps)
        return np.concatenate([self.f(maps[a:b]) for a, b in _chunks(len(maps), chunk)])

    def level0(self, t, direction):
        raise TypeError("PLS1 R^2: Level 0 is the permutation null (level0_perm), not parametric")

    def level0_both(self):
        raise TypeError("PLS1 R^2: Level 0 is the permutation null (level0_perm), not parametric")


class PlsrComponent(_Component):
    """sklearn PLSRegression(n_components=K, scale=True) (prereg.md:178-179): T = R^2 of component k (the share of
    y's variance carried by component k's x-score, corr(t_k, y)^2), or, cumulative=True, the K components' cumulative
    R^2 (sum over k; the fitted model's R^2: MOR-C1 / C2, VR-C1). For one response, NIPALS gives t_k proportional to
    P_{k-1} G P_{k-1} y with G = X_s X_s^T (X_s centred, scaled ddof 1) and P_{k-1} the projector orthogonal to t_1 ..
    t_{k-1}; computed here for many maps at once (refit per map) and asserted equal to sklearn on y (tests: to 1e-12
    on y, surrogates and permutations). genes: the model's columns of ctx.X (MOR: the locus genes; default all)."""
    form = "component (PLSRegression)"

    def __init__(self, ctx, y, *, parcel_ids, n_components: int, component: int | None = None,
                 cumulative: bool = False, genes=None):
        super().__init__(ctx, y, parcel_ids=parcel_ids, what="PLSR component map y")
        if cumulative == (component is not None):
            raise ValueError("PLSR: give exactly one of component=k or cumulative=True")
        self.K = int(n_components)
        self.k = None if component is None else int(component)
        if self.K < 1 or (self.k is not None and not 1 <= self.k <= self.K):
            raise ValueError(f"PLSR: component {self.k} of n_components {self.K}")
        self.cumulative = bool(cumulative)
        self.genes = None if genes is None else np.asarray(genes, dtype=int)
        X = ctx.X if self.genes is None else ctx.X[:, self.genes]
        sd = X.std(0, ddof=1)
        Xs = (X - X.mean(0)) / np.where(sd > 0, sd, 1.0)  # sklearn _center_scale_xy (scale=True)
        self.G0 = Xs @ Xs.T
        self.X = X
        self.T_obs = float(self.T_maps(self.y[None, :])[0])

    def r2_components(self, maps) -> np.ndarray:
        """(n_maps, K): corr(t_k, y)^2 for k = 1 .. K, each map refit."""
        Y = np.atleast_2d(np.asarray(maps, dtype=float))
        Yc = Y - Y.mean(1, keepdims=True)
        yy = np.einsum("ij,ij->i", Yc, Yc)
        yk = Yc.copy()
        Ts, out = [], np.empty((len(Y), self.K))
        for k in range(self.K):
            t = yk @ self.G0
            for tj in Ts:
                t -= tj * (np.einsum("ij,ij->i", tj, t) / np.einsum("ij,ij->i", tj, tj))[:, None]
            tt = np.einsum("ij,ij->i", t, t)
            out[:, k] = np.einsum("ij,ij->i", t, Yc) ** 2 / (tt * yy)
            yk = yk - t * (np.einsum("ij,ij->i", t, yk) / tt)[:, None]
            Ts.append(t)
        return out

    def T_maps(self, maps, s=None, chunk: int = CHUNK_MAX) -> np.ndarray:
        maps = np.atleast_2d(maps)
        out = []
        for a, b in _chunks(len(maps), chunk):
            R = self.r2_components(maps[a:b])
            out.append(R.sum(1) if self.cumulative else R[:, self.k - 1])
        return np.concatenate(out)

    def level0(self, t, direction):
        raise TypeError("PLSR component: Level 0 is the permutation null (level0_perm), not parametric")

    def level0_both(self):
        raise TypeError("PLSR component: Level 0 is the permutation null (level0_perm), not parametric")


_GENERATOR_TYPES = (np.random.Generator, np.random.RandomState, np.random.SeedSequence, np.random.BitGenerator)
_GENERATOR_NAMES = {"rng", "seed", "seeds", "generator", "random_state", "randomstate", "gen", "seed_seq", "bitgen"}


def assert_no_generator(f, what: str) -> None:
    """RUN_PLAN_amend_1 R34: the paper's re-selection rule (and the statistic) is given no generator. Refuses
    (FunctionalDefect) a callable with a parameter named like a generator or seed, a default / bound argument / closure
    cell / partial keyword holding a numpy Generator, RandomState, SeedSequence or BitGenerator."""
    if not callable(f):
        raise FunctionalDefect(f"R34: {what} is not callable")
    vals = []
    g = f
    while isinstance(g, functools.partial):
        vals += list(g.args) + list((g.keywords or {}).values())
        g = g.func
    try:
        sig = inspect.signature(f)
    except (TypeError, ValueError):
        sig = None
    if sig is not None:
        for name, prm in sig.parameters.items():
            if name.lower() in _GENERATOR_NAMES:
                raise FunctionalDefect(f"R34: {what} takes a parameter {name!r}: re-selection is given no generator")
            if prm.default is not inspect.Parameter.empty:
                vals.append(prm.default)
    for cell in (getattr(g, "__closure__", None) or ()):
        try:
            vals.append(cell.cell_contents)
        except ValueError:
            pass
    vals += list(getattr(g, "__defaults__", None) or ())
    vals += list((getattr(g, "__kwdefaults__", None) or {}).values())
    if getattr(g, "__self__", None) is not None:
        vals.append(g.__self__)
    if any(isinstance(v, _GENERATOR_TYPES) for v in vals):
        raise FunctionalDefect(f"R34: {what} holds a random generator: re-selection is given no generator")


def _legacy_state_key():
    s = np.random.get_state(legacy=True)
    return (s[0], s[1].tobytes(), s[2], s[3], s[4])


class SelectedList(_Component):
    """A selected-list component claim (RA-11 ... 14, TSV rows 208-211; prereg_amend_3.md:102-106; RUN_PLAN_amend_1 R34):
    T(map) = stat(map, select(map)), the list re-selected by the paper's rule on the observed map, on every permuted map
    and on every surrogate; an empty list gives T = 0. Level 0 = R34's construction from SS(leg 10)
    (seed_of('re-selection')); site leg = spatial.site_null with S1c's integer seed from SS(leg 0) and S2c's from SS(leg
    1) (R7, as every form); SS(leg 8) is never drawn. select(map values) -> gene indices and stat(map values, genes) ->
    float are the paper's rule and statistic (their code's ML_Lag weights live inside them); neither is given a
    generator (assert_no_generator at construction; numpy's legacy global state asserted unmoved across every
    re-selection pass; the Level-0 generator's state asserted unmoved by the refits)."""
    form = "component (selected list)"
    LEVEL0_SEED_LEG = "re-selection"  # leg 10 (R34)
    LEVEL0_KIND = "permutation with re-selection (leg 10)"

    def __init__(self, ctx, y, select, stat, *, parcel_ids):
        super().__init__(ctx, y, parcel_ids=parcel_ids, what="selected-list map y")
        assert_no_generator(select, "the selection rule")
        assert_no_generator(stat, "the selected-list statistic")
        self.select, self.stat = select, stat
        self.selected = self._select(self.y)
        self.T_obs = float(self.T_maps(self.y[None, :])[0])

    def _select(self, v) -> np.ndarray:
        genes = np.asarray(self.select(np.array(v, dtype=float, copy=True)), dtype=int).ravel()
        if genes.size and (np.unique(genes).size != genes.size or genes.min() < 0 or genes.max() >= self.ctx.G):
            raise ValueError("selection rule: genes must be distinct column indices of the class universe")
        return genes

    def _T_one(self, v) -> float:
        genes = self._select(v)
        if genes.size == 0:
            return 0.0  # R34: an empty list gives T = 0
        t = float(self.stat(np.array(v, dtype=float, copy=True), genes))
        if not math.isfinite(t):
            raise ValueError("selected-list statistic is not finite")
        return t

    def T_maps(self, maps, s=None, chunk: int = CHUNK_MAX) -> np.ndarray:
        """T on each map with the list re-selected on that map (no generator; legacy global state asserted unmoved)."""
        if s is not None:
            raise ValueError("selected list: T_maps re-selects on each map; no set score is taken")
        maps = np.atleast_2d(np.asarray(maps, dtype=float))
        before = _legacy_state_key()
        out = np.array([self._T_one(mp) for mp in maps], dtype=float)
        if _legacy_state_key() != before:
            raise FunctionalDefect("R34: re-selection drew a random number (numpy's global state moved)")
        return out

    def level0(self, t, direction):
        raise TypeError("selected list: Level 0 is the permutation null with re-selection (level0_perm, leg 10)")

    def level0_both(self):
        raise TypeError("selected list: Level 0 is the permutation null with re-selection (level0_perm, leg 10)")


# ================================================================================================================
# RUN_PLAN_amend_1 R32 (b): the rho descriptor's site leg (rank T compared exactly)
# ================================================================================================================
class RankRho(_Form):
    """Spearman rho between the map y and a second map b fixed on the analysis parcels (the rho of Giacomel's descriptor
    rows, `claims_register.md:1469-1473`, has b = the weighted GEDAR map, built by the P15 signed-weight adapter: not
    built here). Site leg: spatial.site_null on y (S1c / S2c keys as every form); every state's rho is compared with the
    observed one EXACTLY (R32 (b): rank_corr_terms / rank_corr_counts; equal-valued states are then equal, the identity
    included, so R32 (a) is not applied; the identity row's ranks are asserted equal to y's on an exact leg). The float
    rho is for reporting only. Descriptor: never a verdict."""
    form = "rho descriptor"
    full_verdict = False
    conditioned = False

    def __init__(self, ctx, y, b, *, parcel_ids):
        super().__init__(ctx, y, parcel_ids=parcel_ids, what="rho descriptor map y")
        b = A3.align_to_context(ctx, b, parcel_ids, "rho descriptor second map")
        if not (np.isfinite(b).all() and np.std(b) > 0):
            raise ValueError("rho descriptor: the second map must be finite and non-constant on the analysis parcels")
        self.b = b
        N0, Q0 = rank_corr_terms(self.y, self.b)
        self.N_obs, self.Q_obs = N0[0], Q0[0]
        if self.Q_obs <= 0:
            raise ValueError("rho descriptor: a constant rank vector")
        self.T_obs = self.N_obs / math.sqrt(self.Q_obs)

    def T_maps(self, maps, s=None, chunk: int = CHUNK_MAX) -> np.ndarray:
        """The float rho of each map with b (REPORTING ONLY: never compared)."""
        N, Q = rank_corr_terms(maps, self.b)
        return np.array([n / math.sqrt(q) for n, q in zip(N, Q)], dtype=float)

    def site_leg(self, K: int, seed_of, chunk: int = CHUNK_MAX, *, return_surrogates: bool = False,
                 _comparison: str = "exact") -> dict:
        """S1c / S2c of rho, counted exactly (R32 (b)); R32 (c) asserted on an exact leg. _comparison: PLANT ONLY,
        'float-batch' = the must-fail batch-normalised float rho (cascade.corr_matrix of rank rows)."""
        out = {}
        yr = doubled_ranks(self.y)
        for leg, method in SITE_LEGS:
            seed = int(np.random.default_rng(seed_of(leg)).integers(2 ** 31))
            sur, info = site_null(self.site_input(), self.ctx.D, self.ctx.classes, K, seed, method)
            rinfo = dict(exact=bool(info["exact"]), n_null=int(info["n_null"]), n_patterns=float(info["n_patterns"]),
                         floor=float(info["floor"]))
            if info["exact"] and not np.array_equal(doubled_ranks(sur[0]), yr):
                raise FunctionalDefect(f"R32 (b): {self.form} {leg}: the identity row's ranks differ from y's")
            if _comparison == "exact":
                N, Q = [], []
                for a in range(0, len(sur), int(chunk)):
                    n_, q_ = rank_corr_terms(sur[a: a + int(chunk)], self.b)
                    N += n_
                    Q += q_
                c = rank_corr_counts(self.N_obs, self.Q_obs, N, Q)
                p = c["p"]
                rinfo["rank_rule"] = dict(branch=c["branch"], k_plus=c["k_plus"], k_minus=c["k_minus"],
                                          rule=c["rule"])
            elif _comparison == "float-batch":
                rb = doubled_ranks(self.b).astype(float)
                null = corr_matrix(doubled_ranks(sur).astype(float), rb)[:, 0]
                p = p_both(null, float(corr_matrix(yr.astype(float), rb)[0, 0]))
                rinfo["rank_rule"] = dict(branch="PLANT: batch-normalised float rho (must fail)")
            else:
                raise ValueError(f"rho site leg: unknown comparison {_comparison!r}")
            if info["exact"]:
                assert_exact_floor(p, info["floor"], f"{self.form} {leg} (exact)")
            out[leg] = dict(p=p, floor=float(info["floor"]), seed=seed, info=rinfo)
            if return_surrogates:
                out[leg]["surrogates"] = sur
        return out

    def record(self) -> dict:
        return dict(form=self.form, T=float(self.T_obs), N=int(self.N_obs), Q=int(self.Q_obs), n_parcels=self.n,
                    parcel_ids=self.parcel_ids, full_verdict=False, rule=R32_RANK_RULE)


# ================================================================================================================
# dispatch (RUN_PLAN §4 "Dispatch by claim_form"; the TSV's claim_form values)
# ================================================================================================================
def make_adapter(claim_form: str, ctx, y, *, parcel_ids, S=None, component_kind: str | None = None, **kw):
    """claim_form: the TSV's 'set-vs-map' | 'decoded-list' | 'PLS-enrichment' | 'component', or 't-abs' for the T_abs
    descriptor. component_kind (component only): 'fixed' (kw component=...), 'pls1-r2' (kw genes=...), 'plsr' (kw
    n_components, component | cumulative, genes). 'gene-set-only' (R10) and 'other' (R21 / R28; the signed-weight
    descriptor, P15) have their own adapters elsewhere."""
    f = _form(claim_form)
    if f == "set-vs-map":
        return SetVsMap(ctx, y, S, parcel_ids=parcel_ids)
    if f == "decoded-list":
        return DecodedList(ctx, y, S, parcel_ids=parcel_ids)
    if f == "PLS-enrichment":
        return PlsEnrichment(ctx, y, S, parcel_ids=parcel_ids)
    if f == "t-abs":
        return TAbs(ctx, y, S, parcel_ids=parcel_ids)
    if component_kind == "fixed":
        return FixedComponent(ctx, y, kw.pop("component"), parcel_ids=parcel_ids, **kw)
    if component_kind == "pls1-r2":
        return Pls1R2(ctx, y, parcel_ids=parcel_ids, **kw)
    if component_kind == "plsr":
        return PlsrComponent(ctx, y, parcel_ids=parcel_ids, **kw)
    raise ValueError(f"component claim: component_kind must be one of {COMPONENT_KINDS}, got {component_kind!r}")
