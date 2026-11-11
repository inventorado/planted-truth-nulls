"""A1's descriptor pass (arcs/audit/RUN_PLAN.md v3.1, FROZEN sha256 16c60232...: §4 legs table, R3, R4, R5, R6, R7,
R8, R24; plants P10, P11, P23).

Every leg here is a DESCRIPTOR: it never enters the verdict, the conjunction p or BH (prereg_amend_3.md:100-101). All
are UNCONDITIONED (R6, RUN_PLAN.md:527-534) and score the row's own registered T (R3 :501; prereg.md:188-189) through
the adapter's T_sets / T_sets_maps / T_pairs (adapters.py). Each leg gives its one-sided p in both directions by
(k + 1)/(n + 1); every leg takes its count(s) as parameters (plant K vs audit K).

Legs (seed leg numbers of claims_register.md:1080-1082 in brackets; the caller's seed_of(name) gives the key):
- Level-2 G1 (R24 :921-922): the leg-2 G1 sets [2] (the species G1 stream) scored unconditioned; on a single-class
  map it equals the species G1 (asserted here, to 1e-12, always).
- G2 [11]: prereg §4.3's coexpression-matched sampler (asdg.genesets.coexpr_matched_sets, the frozen G2 sampler) over
  the class universe minus S, target S's mean pairwise coexpression (asdg.genesets.Universe.mean_coexpr). Pool < m ->
  "unmatched" (no sub-bin can be entered: prereg.md:140-142; R8 :568-572); a sub-bin not entered -> "unmatched".
- G3 [R24's key: the first spawned child of leg 3's key; the caller's g3_seed()]: uniform from GAMBA brain>body
  ∩ universe (prereg.md:143; the context's brain background), S excluded; pool < m -> "not computable (pool < m)"
  (R8 :566-567).
- G4 [12]: G2's sampler inside G3's background (prereg.md:144; e3_plants.py:127); pool < m -> "unmatched".
- G5 [13]: BrainSpan trajectory- and coexpression-matched (asdg.genesets.trajectory_matched_sets): pool < 2m or > 20 %
  of members without a trajectory -> "not applicable"; band not entered -> "unmatched" (prereg.md:145-153).
- Level-2 p = max over G1-G5 per direction (prereg.md:154); a leg without a p leaves it without one (the frozen plant
  code's rule, e3_plants.py:136-137: NaN if any of G1-G5 is NaN), with the reasons listed.
- J1 [14] (R4 :506-517; R7 :545-547): ONE generator g = default_rng(SS_14): the S1c seed, then the S2c seed, then
  K_sets = 1,000 G2 sets (the claim's G2 sampler); K_surr surrogates of each adopted type (S1c BrainSMASH, S2c MSR;
  asdg.spatial.site_null, the audit-level generator: exact enumeration when the stratified randomisation has <= K_surr
  patterns, as the verdict's site leg); z(map) = (T(S, map) - mean_k T(R_k, map)) / sd_k T(R_k, map) (sd ddof 1, as
  cascade.joint_j1); p per type by (#{z_m >= z_obs} + 1)/(M + 1) in each direction; p_J1 = the larger of the two
  types (prereg.md:157-161). Degenerate pool (prereg.md:161-162): mean pairwise Jaccard >= .5 (computed exactly over
  all pairs) or sd_k <= 1e-9 on any map -> "degenerate pool". Pool < m -> "not computable (pool < m)" (R8 :582-583);
  the G2 sampler unmatched -> "unmatched" (e3_plants.py:132-133).
  DECLARED (asdg-skeptic WP1 review, C6): J1's Jaccard here is the EXACT mean over all n(n - 1)/2 pairs of the K_sets
  G2 sets (mean_pairwise_jaccard), the quantity prereg.md:161 names ("mean pairwise Jaccard < 0.5"), NOT the engine's
  sampled estimate (asdg.cascade.pool_diversity: 2,000 random pairs drawn from default_rng(0), a Monte-Carlo estimate
  of the same mean). The two can differ near .5 (the estimate's sampling error); this pass's "degenerate pool" status
  follows the exact mean. The value is reported as pool_jaccard with pool_jaccard_rule "exact mean over all pairs".
- Naive joint [15] (R5 :519-525; R7 :547): ONE generator g = default_rng(SS_15): the S1 seed, then K G1 sets (uniform
  from U \\ S, the calls of asdg.genesets.random_sets), K unstratified BrainSMASH S1 surrogates
  (asdg.spatial.brainsmash_surrogates), paired one to one exactly as cascade.naive_joint pairs them (a permutation of
  the sets drawn from g after the sets), with T substituted for r. Pool < m -> "not computable (pool < m)".
- T_abs [21-25] (claims_register.md:309-313; P11): the T_abs adapter's Level 0 (Welch t of |r|), site leg (S1c [21],
  S2c [22]) and unconditioned G1 [23], G3m [24], G6l [25]; the registered tail (upper; lower for a stated depletion);
  labelled "unsigned descriptor, uncalibrated ..."; never "detects" or "survives".

Reported p at the claim's direction: R1 (RUN_PLAN.md:429-436) reads "every leg and sub-leg gives its one-sided
p_leg(d) ... Each leg's reported p is min(1, 2 p_leg(d*))", and a claim has one direction (claims_register.md:187).
The descriptor pass applies that to its legs when given the verdict's d* (two-sided) or the registered direction
(one-sided); both one-sided p's are always beside it, and the literal per-leg two-sided p is reported for two-sided
claims. If d* is not defined, no reported p is given. Pinned as coded by RUN_PLAN_amend_1.md R36 (d) (and (a)).

RUN_PLAN_amend_1 R32 (a) / (c): J1's exact surrogate types count their identity pattern (j1_core) and every exact
descriptor leg (J1's exact types; T_abs's exact site legs) asserts p >= its declared floor. The rho descriptor's site
leg (R32 (b)) is adapters.RankRho.site_leg.
"""
from __future__ import annotations

from typing import Callable, Mapping

from pathlib import Path

import numpy as np
import pandas as pd

from . import a3_port as A3  # noqa: F401  (src/ on sys.path; pmax)
from . import adapters as AD
from asdg.genesets import Trajectories, coexpr_matched_sets, trajectory_matched_sets
from asdg.spatial import brainsmash_surrogates, site_null

NOT_COMPUTABLE = AD.NOT_COMPUTABLE  # "not computable (pool < m)" (R8)
# 2026-10-21 (G2 run 9): BrainSMASH's Base cannot fit its variogram on a class this small (7 parcels: V-DK-subcortex);
# the naive joint leg (R5, unstratified S1 surrogates) then reads this status - a leg status, never a silent skip
NOT_COMPUTABLE_SMASH = "not computable (BrainSMASH S1 surrogates undefined on this class's parcels)"
UNMATCHED = "unmatched"
NOT_APPLICABLE = "not applicable"
DEGENERATE = "degenerate pool"
SD_MIN = 1e-9  # prereg.md:162; cascade.joint_j1
JACCARD_MAX = 0.5  # prereg.md:161
LEVEL2_LEGS = ("Level-2 G1", "G2", "G3", "G4", "G5")
PER_LEG_LABEL = "per-leg two-sided (not the verdict p)"
R1_DESCRIPTOR_READING = ("R1 applied to descriptor legs: reported p = min(1, 2 p(d*)) at the verdict's d* (two-sided), "
                         "p(d) in the registered direction (one-sided); RUN_PLAN.md:429-436, claims_register.md:187")
FULL_FORMS = ("set-vs-map", "decoded-list", "PLS-enrichment")


# ================================================================================================================
# helpers
# ================================================================================================================
def _full(adapter):
    if isinstance(adapter, AD.TAbs) or not getattr(adapter, "full_verdict", False) or adapter.form not in FULL_FORMS:
        raise TypeError(f"descriptor legs G1-G5, J1 and the naive joint are for full-verdict forms (RUN_PLAN §4 legs "
                        f"table); got {type(adapter).__name__}")
    return adapter


def _count(k, name) -> int:
    if isinstance(k, bool) or not isinstance(k, (int, np.integer)) or int(k) < 1:
        raise ValueError(f"{name} must be a positive int, got {k!r}")
    return int(k)


def _pool(n_genes: int, S) -> np.ndarray:
    return np.setdiff1d(np.arange(int(n_genes)), np.asarray(S, dtype=int))


def _brain_pool(ctx, S) -> np.ndarray:
    """(B ∩ U) \\ S: the class context's brain>body background (GAMBA, prereg.md:143) minus S."""
    return np.setdiff1d(np.flatnonzero(ctx.B.brain), np.asarray(S, dtype=int))


def uniform_set_chunks(pool, m: int, K: int, rng, exclude=(), chunk: int = AD.CHUNK_MAX):
    """K uniform size-m sets from pool minus exclude, in chunks, with exactly the rng calls of
    asdg.genesets.random_sets (one rng.choice(pool, m, replace=False) per set, in order)."""
    pool = np.setdiff1d(np.asarray(pool), np.asarray(exclude, dtype=int))
    for a in range(0, int(K), int(chunk)):
        b = min(int(K), a + int(chunk))
        yield np.stack([rng.choice(pool, size=m, replace=False) for _ in range(b - a)])


def mean_pairwise_jaccard(sets, chunk: int = 256) -> float:
    """The exact mean pairwise Jaccard overlap over all pairs of rows of `sets` (each row a set of distinct indices),
    the definition the engine's sampled cascade.pool_diversity estimates (prereg.md:161-162)."""
    sets = np.atleast_2d(np.asarray(sets, dtype=int))
    n, m = sets.shape
    if n < 2:
        raise ValueError("Jaccard needs >= 2 sets")
    if any(np.unique(r).size != m for r in sets):
        raise ValueError("a set has repeated members")
    cols = np.unique(sets)
    pos = np.searchsorted(cols, sets)
    M = np.zeros((n, cols.size), dtype=np.float32)  # exact integer counts (m < 2^24)
    M[np.repeat(np.arange(n), m), pos.ravel()] = 1.0
    tot, idx = 0.0, np.arange(n)
    for a in range(0, n, chunk):
        b = min(n, a + chunk)
        inter = (M[a:b] @ M.T).astype(np.float64)
        up = idx[None, :] > np.arange(a, b)[:, None]
        tot += float((inter[up] / (2 * m - inter[up])).sum())
    return tot / (n * (n - 1) / 2)


def _with_direction(rec: dict, direction, two_sided) -> dict:
    """Adds R1's reported p (R1_DESCRIPTOR_READING) and, for two-sided claims, the literal per-leg two-sided p."""
    p = rec.get("p")
    if two_sided is None:
        return rec
    if p is None or direction is None:
        rec["p_reported"] = None
    else:
        rec["p_reported"] = min(1.0, 2.0 * p[direction]) if two_sided else float(p[direction])
    if two_sided:
        rec["p_per_leg_two_sided"] = None if p is None else min(1.0, 2.0 * min(p[1], p[-1]))
    return rec


def _scored(adapter, sets, chunk, **info) -> dict:
    null = np.asarray(adapter.T_sets(sets, chunk), dtype=float)
    return dict(status="ok", p=AD.p_both(null, adapter.T_obs), floor=1.0 / (null.size + 1), n=int(null.size),
                null_mean=float(null.mean()), null_sd=float(null.std(ddof=1)) if null.size > 1 else None, **info)


def _sampler_info(info: dict | None) -> dict:
    if not info:
        return {}
    return {k: (float(v) if isinstance(v, (float, np.floating)) else
                [float(x) for x in v] if isinstance(v, tuple) else v)
            for k, v in info.items() if k != "sets"}


# ================================================================================================================
# Level 2 (G1-G5) and its max
# ================================================================================================================
def level2_g1_leg(adapter, K: int, seed_of: Callable, *, species: dict | None = None,
                  chunk: int = AD.CHUNK_MAX) -> dict:
    """R24: the leg-2 G1 sets (seed_of('G1'), the species G1 stream) scored UNCONDITIONED with T (adapters.level2_g1).
    On a single-class map the result equals the species G1 (R24 :921-922: asserted): against species['null']['G1'] if
    a species leg is given (it must have been drawn with the same K and stream), else against the conditioned G1 null
    recomputed on the same stream (asdg's builders through a3_port.g1_null_chunked, scored with the adapter's T)."""
    _full(adapter)
    K = _count(K, "K")
    r = AD.level2_g1(adapter, K, seed_of, chunk)
    rec = dict(leg="Level-2 G1", seed_leg="leg 2 (the species G1 sets; R24)", status=r["status"], p=r["p"],
               floor=r.get("floor"), n=K if r["status"] == "ok" else 0, K=K, conditioned=False)
    if r["status"] == "ok" and adapter.ctx.single_class():
        if species is not None:
            ref = species["null"]["G1"]
            if ref is None or len(ref) != K:
                raise AssertionError("R24: the species G1 given is not this leg's (missing or another K)")
        else:
            N = A3.g1_null_chunked(adapter.basis, adapter.S, K, np.random.default_rng(seed_of("G1")))
            ref = adapter.T(N)
        d = float(np.max(np.abs(np.asarray(ref, dtype=float) - r["null"])))
        if not d <= 1e-12:
            raise AssertionError(f"R24: Level-2 G1 differs from the species G1 on a single-class map (max |d| {d:.3g})")
        rec["single_class_equals_species_G1_max_abs"] = d
    return rec


def g2_leg(adapter, K: int, seed_of: Callable, *, chunk: int = AD.CHUNK_MAX) -> dict:
    """G2 [11]: coexpression-matched sets (prereg.md:137-142; the frozen sampler), unconditioned, scored with T."""
    _full(adapter)
    return _coexpr_leg(adapter, _count(K, "K"), np.random.default_rng(seed_of("G2")), "G2", brain=False, chunk=chunk)


def g4_leg(adapter, K: int, seed_of: Callable, *, chunk: int = AD.CHUNK_MAX) -> dict:
    """G4 [12]: G2's sampler inside G3's background (prereg.md:144)."""
    _full(adapter)
    return _coexpr_leg(adapter, _count(K, "K"), np.random.default_rng(seed_of("G4")), "G4", brain=True, chunk=chunk)


def _coexpr_leg(adapter, K, rng, name, *, brain: bool, chunk) -> dict:
    ctx, S = adapter.ctx, adapter.S
    m = int(S.size)
    pool_all = np.flatnonzero(ctx.B.brain) if brain else np.arange(ctx.G)
    avail = np.setdiff1d(pool_all, S).size
    base = dict(leg=name, K=K, m=m, pool=int(avail), conditioned=False)
    if avail < m:  # R8: no sub-bin can be entered -> the frozen label
        return dict(base, status=UNMATCHED, p=None, n=0,
                    reason="pool < m: no sub-bin can be entered within 20 restarts (prereg.md:140-142; RUN_PLAN R8)")
    target = float(ctx.U.mean_coexpr(S))
    sets, info = coexpr_matched_sets(ctx.U, pool_all, m, target, K, rng, exclude=S)
    if sets is None:
        return dict(base, status=UNMATCHED, p=None, n=0, target=target, info=_sampler_info(info))
    return dict(base, **_scored(adapter, sets, chunk, target=target, info=_sampler_info(info)))


def g3_leg(adapter, K: int, g3_seed: Callable, *, chunk: int = AD.CHUNK_MAX) -> dict:
    """Level-2 G3 (prereg.md:143) on R24's stream (g3_seed() -> the first spawned child of leg 3's key)."""
    _full(adapter)
    K = _count(K, "K")
    ctx, S = adapter.ctx, adapter.S
    m = int(S.size)
    pool = _brain_pool(ctx, S)
    base = dict(leg="G3", K=K, m=m, pool=int(pool.size), conditioned=False, seed_leg="R24: first child of leg 3's key")
    if pool.size < m:
        return dict(base, status=NOT_COMPUTABLE, p=None, n=0)
    rng = np.random.default_rng(g3_seed())
    null = np.concatenate([adapter.T_sets(c, chunk) for c in uniform_set_chunks(pool, m, K, rng, chunk=chunk)])
    return dict(base, status="ok", p=AD.p_both(null, adapter.T_obs), floor=1.0 / (K + 1), n=K)


def trajectories_for(ctx, traj) -> Trajectories:
    """asdg.genesets.Trajectories on the context's universe from a deduplicated BrainSpan-like frame (gene symbol x
    8 stage bins, prereg.md:148-151), or a Trajectories already built (its genes must all be in the universe)."""
    if isinstance(traj, Trajectories):
        missing = [g for g in traj.names if g not in ctx.U.index]
        if missing:
            raise ValueError(f"Trajectories built on another universe ({len(missing)} genes not in this one)")
        return traj
    if not isinstance(traj, pd.DataFrame):
        raise TypeError("traj: a BrainSpan-like DataFrame (genes x stage bins) or asdg.genesets.Trajectories")
    if traj.shape[1] != 8:
        raise ValueError(f"traj: {traj.shape[1]} stage bins, prereg.md:149-150 registers 8")
    return Trajectories(traj, ctx.U)


def g5_leg(adapter, K: int, seed_of: Callable, traj, *, chunk: int = AD.CHUNK_MAX) -> dict:
    """G5 [13]: trajectory- and coexpression-matched sets (prereg.md:145-153; asdg.genesets.trajectory_matched_sets)."""
    _full(adapter)
    K = _count(K, "K")
    ctx, S = adapter.ctx, adapter.S
    tr = trajectories_for(ctx, traj)
    names = [ctx.U.genes[i] for i in S]
    rng = np.random.default_rng(seed_of("G5"))
    sets, info = trajectory_matched_sets(ctx.U, names, tr, K, rng)
    base = dict(leg="G5", K=K, m=int(S.size), conditioned=False, n_trajectories=int(len(tr.names)))
    if sets is None:
        st = info["status"]
        if st not in (NOT_APPLICABLE, UNMATCHED):
            raise RuntimeError(f"G5 sampler status {st!r}")
        return dict(base, status=st, p=None, n=0, info=_sampler_info(info))
    return dict(base, **_scored(adapter, sets, chunk, info=_sampler_info(info)))


def level2_max(legs: Mapping[str, dict]) -> dict:
    """Level-2 p = max over G1-G5, per direction (prereg.md:154); without a p if any leg has none
    (e3_plants.py:136-137)."""
    missing = {n: legs[n]["status"] for n in LEVEL2_LEGS if legs[n].get("p") is None}
    if missing:
        return dict(p=None, status="no p: " + "; ".join(f"{n} {s}" for n, s in missing.items()), missing=missing)
    p = {d: max(legs[n]["p"][d] for n in LEVEL2_LEGS) for d in (1, -1)}
    return dict(p=p, status="ok", binding={d: [n for n in LEVEL2_LEGS if legs[n]["p"][d] == p[d]] for d in (1, -1)})


# ================================================================================================================
# J1 (R4) and the naive joint (R5)
# ================================================================================================================
def j1_core(adapter, sets, surrogates: Mapping[str, np.ndarray], *, chunk: int = AD.CHUNK_MAX,
            exact: Mapping[str, bool] | None = None, _identity_index=None, return_z: bool = False) -> dict:
    """J1 on given draws (prereg.md:157-162 with T substituted for r, R3 :501): z(map) = (T(S, map) - mean_k
    T(R_k, map)) / sd_k T(R_k, map), sd ddof 1; null = z over each surrogate type; p_J1 = the larger p of the types.
    Degenerate pool: exact mean pairwise Jaccard >= .5, or sd <= 1e-9 on y or on any surrogate -> DEGENERATE.
    RUN_PLAN_amend_1 R32 (a) / (c) on an exact surrogate type (exact[name] true: spatial.site_null's enumeration, the
    identity at row 0): the identity row must reconstruct adapter.site_input(); its z and that of every bit-identical
    surrogate := z_obs; p >= the declared floor 2/(N + 1) asserted. _identity_index: PLANT ONLY."""
    sets = np.atleast_2d(np.asarray(sets, dtype=int))
    jac = mean_pairwise_jaccard(sets)
    obs = np.asarray(adapter.T_sets(sets, chunk), dtype=float)
    mu0, sd0 = float(obs.mean()), float(obs.std(ddof=1))
    out = dict(n_sets=int(len(sets)), pool_jaccard=jac, pool_jaccard_rule="exact mean over all pairs (prereg.md:161)",
               sd_obs=sd0, types={})
    sd_ok = sd0 > SD_MIN
    z = {}
    for name, sur in surrogates.items():
        sur = np.atleast_2d(np.asarray(sur, dtype=float))
        zs, sd_min = np.empty(len(sur)), np.inf
        for a in range(0, len(sur), int(chunk)):
            b = min(len(sur), a + int(chunk))
            TS = np.asarray(adapter.T_maps(sur[a:b], chunk=chunk), dtype=float)
            TM = np.asarray(adapter.T_sets_maps(sets, sur[a:b], chunk), dtype=float)
            sd = TM.std(1, ddof=1)
            sd_min = min(sd_min, float(sd.min()))
            with np.errstate(divide="ignore", invalid="ignore"):
                zs[a:b] = (TS - TM.mean(1)) / sd
        sd_ok = sd_ok and sd_min > SD_MIN
        z[name] = zs
        out["types"][name] = dict(n_null=int(len(sur)), sd_min=sd_min,
                                  exact=None if exact is None else bool(exact[name]))
    degenerate = (not sd_ok) or jac >= JACCARD_MAX
    if degenerate:
        why = []
        if jac >= JACCARD_MAX:
            why.append(f"mean pairwise Jaccard {jac:.4f} >= .5")
        if not sd_ok:
            why.append("sd_k <= 1e-9 on y or on a surrogate")
        return dict(out, status=DEGENERATE, reason="; ".join(why), p=None, z_obs=None)
    z_obs = (adapter.T_obs - mu0) / sd0
    z_used = {}
    for name, zs in z.items():
        t = out["types"][name]
        if t["exact"]:  # RUN_PLAN_amend_1 R32 (a): count the identity pattern (and its bit-identical duplicates)
            idx = 0 if _identity_index is None else int(_identity_index)
            sur = np.atleast_2d(np.asarray(surrogates[name], dtype=float))
            rows, dev = AD.identity_rows(sur, idx, adapter.site_input(), f"J1 {name} (exact)")
            zs = AD.count_identity(zs, rows, z_obs)
            t["identity"] = AD.identity_record(idx % len(sur), rows, dev, len(sur))
        z_used[name] = zs
        t["p"] = AD.p_both(zs, z_obs)
        # an exact enumeration contains the identity pattern (z = z_obs): floor 2/(N + 1), as spatial.site_null's
        t["floor"] = (2.0 if t["exact"] else 1.0) / (len(zs) + 1)
        if t["exact"]:
            AD.assert_exact_floor(t["p"], t["floor"], f"J1 {name} (exact)")  # RUN_PLAN_amend_1 R32 (c)
    p = {d: max(out["types"][n]["p"][d] for n in surrogates) for d in (1, -1)}
    rec = dict(out, status="ok", z_obs=float(z_obs), p=p, p_rule="the larger of the two types' p (prereg.md:160)")
    if return_z:  # tests: each type's z values as compared (after R32 (a) on an exact type)
        rec["_z"] = {name: np.asarray(zs, dtype=float) for name, zs in z_used.items()}
    return rec


def j1_leg(adapter, seed_of: Callable, *, K_sets: int, K_surr: int, chunk: int = AD.CHUNK_MAX,
           return_draws: bool = False) -> dict:
    """J1 [14] (R4, R7): one generator from leg 14: S1c seed, S2c seed, then K_sets G2 sets; K_surr S1c and K_surr S2c
    (site_null, the adopted class-stratified pair: e3_gates.md:3 'Level-1 adoption: strat')."""
    _full(adapter)
    K_sets, K_surr = _count(K_sets, "K_sets"), _count(K_surr, "K_surr")
    ctx, S = adapter.ctx, adapter.S
    m = int(S.size)
    g = np.random.default_rng(seed_of("J1"))
    s1c = int(g.integers(2 ** 31))
    s2c = int(g.integers(2 ** 31))
    base = dict(leg="J1", seed_leg=14, seeds=dict(S1c=s1c, S2c=s2c),
                order="S1c seed, S2c seed, then the G2 sets (R7; RUN_PLAN.md:545-546)", K_sets=K_sets, K_surr=K_surr,
                m=m, conditioned=False)
    if _pool(ctx.G, S).size < m:
        return dict(base, status=NOT_COMPUTABLE, p=None)
    target = float(ctx.U.mean_coexpr(S))
    sets, info = coexpr_matched_sets(ctx.U, np.arange(ctx.G), m, target, K_sets, g, exclude=S)
    if sets is None:
        return dict(base, status=UNMATCHED, p=None, target=target, info=_sampler_info(info))
    sur, ex = {}, {}
    for name, method, seed in (("S1c", "brainsmash", s1c), ("S2c", "msr", s2c)):
        sur[name], si = site_null(adapter.site_input(), ctx.D, ctx.classes, K_surr, seed, method)
        ex[name] = bool(si["exact"])
    core = j1_core(adapter, sets, sur, chunk=chunk, exact=ex)
    rec = dict(base, target=target, sampler=_sampler_info(info), **core)
    if return_draws:
        rec["_draws"] = dict(sets=sets, surrogates=sur)
    return rec


def _raised_in_brainsmash(e: BaseException) -> bool:
    """The exception came from inside the brainsmash package (a frame of its own files)."""
    import traceback
    return any("brainsmash" in Path(t.filename).parts for t in traceback.extract_tb(e.__traceback__))


def naive_joint_leg(adapter, seed_of: Callable, *, K: int, chunk: int = AD.CHUNK_MAX,
                    return_draws: bool = False) -> dict:
    """Naive joint [15] (R5, R7): one generator from leg 15: the S1 seed, then K G1 sets; K unstratified BrainSMASH S1
    surrogates; set j_i paired with surrogate i, j = g.permutation(K)[:n] drawn after the sets (cascade.naive_joint's
    pairing); null_i = T(set j_i, surrogate i)."""
    _full(adapter)
    K = _count(K, "K")
    ctx, S = adapter.ctx, adapter.S
    m = int(S.size)
    g = np.random.default_rng(seed_of("naive joint"))
    s1 = int(g.integers(2 ** 31))
    base = dict(leg="naive joint", seed_leg=15, seeds=dict(S1=s1), order="S1 seed, then the G1 sets (R7; :547)",
                K=K, m=m, conditioned=False)
    pool = _pool(ctx.G, S)
    if pool.size < m:
        return dict(base, status=NOT_COMPUTABLE, p=None)
    sets = np.concatenate(list(uniform_set_chunks(pool, m, K, g, chunk=chunk)))
    try:
        sur = brainsmash_surrogates(adapter.site_input(), ctx.D, K, s1)
    except ValueError as e:                   # only BrainSMASH's own failure (its frames); any other ValueError raises
        if not _raised_in_brainsmash(e):
            raise
        return dict(base, status=NOT_COMPUTABLE_SMASH, p=None, n_parcels=int(np.asarray(ctx.D).shape[0]))
    n = min(len(sur), len(sets))
    j = g.permutation(len(sets))[:n]
    null = np.asarray(adapter.T_pairs(sets[j], sur[:n], chunk), dtype=float)
    rec = dict(base, status="ok", p=AD.p_both(null, adapter.T_obs), floor=1.0 / (n + 1), n=int(n))
    if return_draws:
        rec["_draws"] = dict(sets=sets, surrogates=sur, pairing=j)
    return rec


# ================================================================================================================
# T_abs (legs 21-25)
# ================================================================================================================
def t_abs_legs(tabs, K, tabs_seed_of: Callable, *, depletion: bool = False, g6l=None,
               chunk: int = AD.CHUNK_MAX) -> dict:
    """T_abs descriptor (claims_register.md:309-313): Level 0 (Welch t of |r|), the site leg on tabs_seed_of('S1c' /
    'S2c') = legs 21 / 22, and the unconditioned G1 / G3m / G6l on tabs_seed_of('G1' / 'G3m' / 'G6l') = legs 23 / 24 /
    25 (the caller's mapping; verdict.seed_callables builds it). g6l: this row's pre-screened leg-25 windows
    (verdict.shared_g6l). K: one count or {'site', 'species'}. Reported in the registered tail only."""
    if not isinstance(tabs, AD.TAbs):
        raise TypeError("t_abs_legs takes the T_abs adapter (adapters.TAbs)")
    Ks = int(K["site"]) if isinstance(K, Mapping) else _count(K, "K")
    Kg = int(K["species"]) if isinstance(K, Mapping) else _count(K, "K")
    tail = AD.TAbs.registered_direction(depletion)
    legs = {"Level 0": dict(p=tabs.level0_both(), kind="Welch t of |r|", status="ok", floor=None)}
    site = tabs.site_leg(Ks, tabs_seed_of, chunk)
    for name, no in (("S1c", 21), ("S2c", 22)):
        s = site[name]
        if s["info"].get("exact"):  # RUN_PLAN_amend_1 R32 (c) (the adapter counted the identity: R32 (a))
            AD.assert_exact_floor(s["p"], s["floor"], f"T_abs {name} (exact)")
        legs[name] = dict(p=s["p"], floor=s["floor"], seed=s["seed"], info=s["info"], seed_leg=no, status="ok", K=Ks)
    sp = tabs.species_leg(Kg, tabs_seed_of, g6l=g6l, chunk=chunk)
    for name, no in (("G1", 23), ("G3m", 24), ("G6l", 25)):
        legs[name] = dict(p=sp["p"][name], floor=sp["floors"].get(name), status=sp["status"][name], seed_leg=no,
                          K=Kg, conditioned=False)
    for rec in legs.values():
        rec["p_registered_tail"] = None if rec["p"] is None else float(rec["p"][tail])
    return dict(form="t-abs", T=float(tabs.T_obs), tail=("lower (stated depletion)" if depletion else "upper"),
                tail_direction=tail, label=AD.TAbs.LABEL, legs=legs, g6l=dict(sp["g6l_info"]),
                never="reported as values and p's, never as 'detects' or 'survives' (claims_register.md:312-313)")


# ================================================================================================================
# the descriptor pass of one full-verdict claim
# ================================================================================================================
def descriptor_pass(adapter, seed_of: Callable, g3_seed: Callable, *, K_sets: int, K_surr: int, K_j1_sets: int,
                    traj, species: dict | None = None, direction: int | None = None, two_sided: bool | None = None,
                    chunk: int = AD.CHUNK_MAX) -> dict:
    """Level 2 (G1-G5 and its max), J1 and the naive joint of one full-verdict claim. Audit counts (claims_register.md:
    1072-1073): K_sets = 10,000 (G1-G5), K_surr = 10,000 (each J1 surrogate type; the naive joint's sets and S1
    surrogates), K_j1_sets = 1,000. species: the verdict's species leg (adapter.species_leg at K_sets, same stream) for
    R24's single-class assertion. direction / two_sided: the verdict's d* (two-sided) or the registered direction
    (one-sided), for R1_DESCRIPTOR_READING."""
    _full(adapter)
    if two_sided is not None and not two_sided and direction not in (1, -1):
        raise ValueError("one-sided: the registered direction is required")
    legs = {"Level-2 G1": level2_g1_leg(adapter, K_sets, seed_of, species=species, chunk=chunk),
            "G2": g2_leg(adapter, K_sets, seed_of, chunk=chunk),
            "G3": g3_leg(adapter, K_sets, g3_seed, chunk=chunk),
            "G4": g4_leg(adapter, K_sets, seed_of, chunk=chunk),
            "G5": g5_leg(adapter, K_sets, seed_of, traj, chunk=chunk)}
    l2 = level2_max(legs)
    j1 = j1_leg(adapter, seed_of, K_sets=K_j1_sets, K_surr=K_surr, chunk=chunk)
    nj = naive_joint_leg(adapter, seed_of, K=K_surr, chunk=chunk)
    for rec in (*legs.values(), l2, j1, nj):
        _with_direction(rec, direction, two_sided)
    return dict(form=adapter.form, T=float(adapter.T_obs), legs=legs, level2=l2, J1=j1, naive_joint=nj,
                counts=dict(K_sets=int(K_sets), K_surr=int(K_surr), K_j1_sets=int(K_j1_sets)),
                direction=direction, two_sided=two_sided,
                direction_reading=R1_DESCRIPTOR_READING if two_sided is not None else None,
                labels=dict(p_per_leg_two_sided=PER_LEG_LABEL) if two_sided else {},
                unconditioned="every descriptor leg is unconditioned (R6)")
