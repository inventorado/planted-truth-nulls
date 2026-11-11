"""A1's form-generic verdict driver (arcs/audit/RUN_PLAN.md v3.1, FROZEN sha256 16c60232...: R1, R8, R9, §4 legs
table and dispatch; plants P8, P9, P10, P14).

What it does, leg by leg, for one claim (map y, set S or component, statistic T, direction):
- Every verdict leg comes from the claim's T-form adapter (a1_audit.adapters), which gives each leg's one-sided p in
  BOTH directions, {+1: p(+), -1: p(-)}, by (k + 1)/(n + 1) (Level 0: the parametric sf / cdf, or the component's
  permutation null). Nothing here recomputes a null.
- R1 (RUN_PLAN.md:417-454): for each direction d the site leg is max(p_S1c(d), p_S2c(d)) and the species leg
  max(p_G1(d), p_G3m(d), p_G6s(d), p_G6l(d)), with one d for every sub-leg; the claim's direction is
  d* = argmin_d max(p_L0(d), p_site(d), p_species(d)), a tie going to the sign of the observed T (+ if T = 0); each
  leg's reported p is min(1, 2 p_leg(d*)) with both one-sided p's beside it; the conjunction p is the max of the
  reported p's (= min(1, 2 min_d max_leg p_leg(d))); the literal per-leg min(1, 2 min(p(+), p(-))) is reported beside
  each leg, labelled "per-leg two-sided (not the verdict p)", and enters nothing. One-sided claims use the registered
  direction, undoubled (prereg.md:117). The resolution label uses the smallest attainable reported p: twice the
  one-sided floor for a two-sided claim (capped at 1, as a reported p is).
- Statuses (R9; RUN_PLAN.md:610-626): the engine's own functions (asdg.verdict.verdict / resolution, src/asdg/
  verdict.py:18-41, used unchanged) give the order G6l unmatched / degenerate, uninformative, resolution-limited, ok,
  fed with the REPORTED p's and the EFFECTIVE (doubled for two-sided) floors. Every status and flag is reported; the
  primary status is the register's by-construction label where one exists (claims_register.md:1462-1464), else R8's
  label (below), else the engine's. An ok status with a non-finite member is refused (RuntimeError: a code defect,
  never read as a p).
- R8 (RUN_PLAN.md:553-609): a verdict leg G1 or G3m not computable (pool < m) -> the cell reads "not auditable
  (definition not applicable: null pool smaller than S)" with every computed leg reported beside it.
- Two-cohort claims (claims_register.md:1639-1641; R1 :442-445; P14): one d* = argmin_d of the max over BOTH maps'
  legs; the claim survives iff both maps survive in d*; p = the larger conjunction p.
- Component forms (claims_register.md:292-294; prereg_amend_5.md:153-162; amendment 4 :105-106): Level 0 (parametric
  for a fixed component; parcel-label permutations with refit, leg 8, otherwise) and the site leg; R1 over those two
  legs; read "passes / does not pass at component level (Level 0 and site leg at .025)", labelled "site leg only; not
  calibrated against expression-aligned maps"; never a survival. Component p = max(Level 0, site) (R29).

Not here: A3's two-sided rule (a3_port.direction_of / p_leg / assemble_verdict / claim_verdict: the direction is the
sign of the observed T; RUN_PLAN R1 :448-449, §19) is never called. T_abs (legs 21-25) and the descriptor legs are in
a1_audit.descriptors.

Readings pinned by RUN_PLAN_amend_1.md v2.1 (FROZEN sha256 8e06d60e...; R32 (c), R36):
- R32 (c): on every exact leg (an exact site leg; exact G6s) p(d) >= the declared floor is asserted in both directions
  (check_exact_floors, in collect_legs and again in assemble_verdict_a1); a failure is a functional defect
  (adapters.FunctionalDefect) and stops the run.
- R36 (a): d* when the conjunction has no p in either direction (a species sub-leg has none: G6l unmatched /
  degenerate, or R8): d* is not defined; every computed leg's two one-sided p's (and the literal per-leg two-sided p)
  are reported, no doubled p is reported, and the status (never ok in that case) stands. As coded.
- R36 (b), adopted by the orchestrator: a two-cohort tie (equal maxima M in both directions) whose two observed T's
  have opposite signs DOES NOT SURVIVE: M >= .5 for any leg (p(+) + p(-) >= 1), so the conjunction p is
  min(1, 2M) = 1 in both directions; the claim's status is the maps' direction-free statuses (status order, floors,
  flags); d* is recorded "undefined: two-cohort tie, opposite observed T signs" and reporting follows (a). (Replaces
  e7029ed's "not auditable (definition not applicable: two-cohort tie ...)".)
- R36 (c): a component claim whose effective (doubled, two-sided) floors of Level 0 and the site leg are not below
  alpha reads "resolution-limited; does not pass" (primary status resolution-limited; reading "does not pass at
  component level ..."). As coded.
- R36 (d): descriptor legs are reported at the claim's d* (descriptors.R1_DESCRIPTOR_READING). As coded.

Fixes of the asdg-skeptic review of WP1 (61e3887):
- B1: descriptor_row_record - a descriptor row (a descriptor cell, a 'not testable as stated' pooled list, R21 / R28's
  descriptor reading) is never a verdict: survives = False, primary status = the row's TSV status, the computed record
  under 'descriptor' with every 'survives' renamed 'passes_at_alpha' and a pass at alpha labelled "descriptive (not a
  verdict)" (claims_register.md:195-196, :297-299). The runner applies it to every row it routes with descriptor = True.
- B2: a two-sided two-cohort claim whose d* is undefined because a verdict leg of one map has no p (G6l unmatched /
  degenerate, R8): R36 (a) at claim level - each map's one-sided p's reported, no doubled p, survives = False for both
  maps and the claim (reading TWO_COHORT_NO_DSTAR_READING); never the single-map 'd* undefined with status ok' refusal.
- B3: plant_seed_callables - the plant view's leg keys (seeds.plant_leg_seed; PLANT CHOICE (orchestrator, 2026-10-01):
  leg streams within a plant case).
"""
from __future__ import annotations

import math
from typing import Callable, Mapping

import numpy as np

from . import a3_port as A3  # noqa: F401  (puts src/ on sys.path before the engine import; pmax)
from . import adapters as AD
from asdg.verdict import ALPHA_V, resolution as engine_resolution, verdict as engine_verdict

DIRECTIONS = (1, -1)
R8_NOT_AUDITABLE = "not auditable (definition not applicable: null pool smaller than S)"
TWO_COHORT_TIE = "undefined: two-cohort tie, opposite observed T signs"  # RUN_PLAN_amend_1 R36 (b): d*'s record
TWO_COHORT_TIE_READING = ("does not survive (RUN_PLAN_amend_1 R36 (b): a two-cohort tie with opposite observed T signs "
                          "forces the common maximum M >= .5 in both directions; conjunction p = min(1, 2M) = 1)")
NO_DSTAR = ("d* not defined: the conjunction has no p in either direction (a verdict leg has no p); both one-sided p's "
            "of every computed leg are reported (RUN_PLAN_amend_1 R36 (a))")
TWO_COHORT_NO_DSTAR_READING = ("does not survive (RUN_PLAN_amend_1 R36 (a) at claim level: a verdict leg of one map has "
                               "no p, so the two-cohort claim's d* is undefined; every computed leg's one-sided p's are "
                               "reported, no doubled p; asdg-skeptic WP1 review B2)")
DESCRIPTIVE = "descriptive (not a verdict)"
DESCRIPTOR_ROW_RULE = ("a descriptor or 'not testable as stated' row is never a verdict (asdg-skeptic WP1 review, B1; "
                       "claims_register.md:195-196 descriptor cells 'never a claim, a survival, or part of m'; :297-299 "
                       "'not testable as stated' stays a non-survival, its T a descriptor): survives = False and the "
                       "primary status "
                       "is the row's TSV status (as read under the run's view); the computed record is kept under "
                       "'descriptor', every 'survives' in it renamed 'passes_at_alpha' and any pass at alpha labelled "
                       "'descriptive (not a verdict)'")
PER_LEG_LABEL = "per-leg two-sided (not the verdict p)"
FULL_FORMS = ("set-vs-map", "decoded-list", "PLS-enrichment")
SITE_SUBLEGS = ("S1c", "S2c")
SPECIES_SUBLEGS = tuple(AD.SPECIES_LEGS)
ENGINE_ORDER = ("g6l unmatched", "g6l degenerate", "uninformative", "resolution-limited")  # src/asdg/verdict.py:30-38
COMPONENT_LABEL = "site leg only; not calibrated against expression-aligned maps"  # prereg_amend_5.md:157-159


def _reading_alpha(alpha: float) -> str:
    return ".025" if alpha == 0.025 else f"{alpha:g}"


def component_reading(passes: bool, alpha: float = ALPHA_V) -> str:
    """prereg_amend_5.md:156: "passes / does not pass at component level (Level 0 and site leg at .025)"."""
    word = "passes" if passes else "does not pass"
    return f"{word} at component level (Level 0 and site leg at {_reading_alpha(alpha)})"


# ================================================================================================================
# small helpers
# ================================================================================================================
def _k(K, which: str) -> int:
    """K is one count for every leg (audit: 10,000) or a mapping with keys 'site', 'species', 'permutation' (plants:
    500 site surrogates, 200 species draws; RUN_PLAN §7 cost model)."""
    if isinstance(K, Mapping):
        if which not in K:
            raise ValueError(f"K mapping has no {which!r} count")
        k = K[which]
    else:
        k = K
    if isinstance(k, bool) or not isinstance(k, (int, np.integer)) or int(k) < 1:
        raise ValueError(f"K[{which}] must be a positive int, got {k!r}")
    return int(k)


def _k_record(K) -> dict | int:
    return {k: int(v) for k, v in K.items()} if isinstance(K, Mapping) else int(K)


def _check_p(p, what: str) -> dict:
    """A leg's {+1: p(+), -1: p(-)}: both keys, finite, in [0, 1] (a parametric sf may underflow to 0.0)."""
    if not isinstance(p, Mapping) or set(p) != set(DIRECTIONS):
        raise ValueError(f"{what}: p must be {{1: p(+), -1: p(-)}}, got {p!r}")
    out = {}
    for d in DIRECTIONS:
        v = float(p[d])
        if not (math.isfinite(v) and 0.0 <= v <= 1.0):
            raise ValueError(f"{what}: p({d:+d}) = {v!r} is not a p-value in [0, 1]")
        out[d] = v
    return out


def _nan_to_none(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else v


def _report(p: dict | None, d: int | None, two_sided: bool):
    """R1: the reported p of a leg in direction d: min(1, 2 p(d)) two-sided, p(d) one-sided; None when the leg has no
    p or d* is not defined."""
    if p is None or d is None:
        return None
    v = p[d]
    if isinstance(v, float) and math.isnan(v):
        return None
    return min(1.0, 2.0 * v) if two_sided else float(v)


def _per_leg_two_sided(p: dict | None):
    """R1 :440-441: the literal min(1, 2 min(p(+), p(-))), labelled PER_LEG_LABEL; never the verdict p."""
    if p is None or any(isinstance(p[d], float) and math.isnan(p[d]) for d in DIRECTIONS):
        return None
    return min(1.0, 2.0 * min(p[1], p[-1]))


def _eff_floor(floor, two_sided: bool):
    """R1 :446: the smallest attainable reported p (twice the one-sided floor for a two-sided claim, capped at 1)."""
    if floor is None:
        return None
    return min(1.0, 2.0 * float(floor)) if two_sided else float(floor)


def _sign(t: float) -> int:
    """R1 :432-433: the sign of the observed T, + if T = 0."""
    return 1 if t >= 0 else -1


def check_exact_floors(legs: dict) -> list:
    """RUN_PLAN_amend_1 R32 (c): on every exact leg of a claim's legs (an exact S1c / S2c; exact G6s), p(d) >= the
    declared floor in both directions (adapters.assert_exact_floor: a failure raises FunctionalDefect and stops the
    run). Returns the legs checked."""
    checked = []
    for leg in SITE_SUBLEGS:
        s = legs["site"][leg]
        if (s.get("info") or {}).get("exact"):
            AD.assert_exact_floor(s["p"], s["floor"], f"site {leg} (exact)")
            checked.append(leg)
    sp = legs.get("species")
    if legs.get("kind") == "full" and sp is not None and sp.get("g6s_exact"):
        AD.assert_exact_floor(sp["p"]["G6s"], sp["floors"]["G6s"], "G6s (exact)")
        checked.append("G6s")
    return checked


def _leg_record(p, floor, two_sided: bool, d, status: str = "ok", **extra) -> dict:
    rec = dict(status=status, p_one_sided=None if p is None else {k: _nan_to_none(v) for k, v in p.items()},
               p_reported=_report(p, d, two_sided))
    if two_sided:
        rec["p_per_leg_two_sided"] = _per_leg_two_sided(p)
    rec.update(floor_one_sided=floor, floor_effective=_eff_floor(floor, two_sided), **extra)
    return rec


# ================================================================================================================
# collecting the legs (the only place nulls are computed: by the adapters)
# ================================================================================================================
def adapter_kind(adapter) -> str:
    """'full' (set-vs-map, decoded-list, PLS-enrichment), 'component-parametric' (a fixed component: Level 0 = the
    parametric p of r, claims_register.md:293) or 'component-permutation' (PLS1 R^2, PLSRegression component:
    Level 0 = parcel-label permutations with refit, prereg.md:179-180). T_abs is a descriptor (descriptors.t_abs_legs);
    any other adapter is refused (no frozen reading here)."""
    if isinstance(adapter, AD.TAbs):
        raise TypeError("t-abs is a descriptor (claims_register.md:309-313): use descriptors.t_abs_legs")
    if isinstance(adapter, AD.RankRho):
        raise TypeError("the rho descriptor is a descriptor (RUN_PLAN_amend_1 R32 (b)): its site leg is RankRho.site_leg")
    if isinstance(adapter, AD.FixedComponent):
        return "component-parametric"
    if isinstance(adapter, (AD.Pls1R2, AD.PlsrComponent, AD.SelectedList)):
        return "component-permutation"  # SelectedList: Level 0 on leg 10 (RUN_PLAN_amend_1 R34)
    if isinstance(adapter, AD._Component):
        raise NotImplementedError(f"component adapter {type(adapter).__name__}: no Level-0 reading wired here")
    if getattr(adapter, "full_verdict", False) and getattr(adapter, "form", None) in FULL_FORMS:
        return "full"
    raise NotImplementedError(f"no verdict reading for adapter {type(adapter).__name__} "
                              f"(form {getattr(adapter, 'form', None)!r})")


def collect_legs(adapter, K, seed_of: Callable, *, g6l=None, chunk: int = AD.CHUNK_MAX,
                 keep_species_raw: bool = False) -> dict:
    """Every verdict leg of one claim on one map, each leg's one-sided p in both directions (the adapters' p's; no
    direction chosen, nothing doubled). seed_of(leg) -> SeedSequence for 'S1c', 'S2c', 'G1', 'G3m', 'G6s', 'G6l' and
    'permutation' (legs 0-5, 8; claims_register.md:1080-1082). g6l: this row's pre-screened (sets, info) for its G6l
    stream (RUN_PLAN §4 'Shared G6l screens'; shared_g6l). keep_species_raw: keep the adapter's species output (its
    null scores) under '_species_raw' for descriptors.level2_g1_leg (R24's single-class assertion); never written."""
    kind = adapter_kind(adapter)
    T = float(adapter.T_obs)
    if not math.isfinite(T):
        raise ValueError("observed T is not finite")
    out = dict(form=adapter.form, kind=kind, T=T, K=_k_record(K), n_parcels=int(adapter.n))
    if kind == "component-permutation":
        Kp = _k(K, "permutation")
        lp = adapter.level0_perm(Kp, seed_of, chunk)
        out["level0"] = dict(p=_check_p(lp["p"], "Level 0 (permutation)"),
                             kind=getattr(adapter, "LEVEL0_KIND", "permutation (leg 8)"),
                             floor=float(lp["floor"]), n_null=int(len(lp["null"])), K=Kp)
    else:
        out["level0"] = dict(p=_check_p(adapter.level0_both(), "Level 0"), kind="parametric", floor=None)
    Ks = _k(K, "site")
    site = adapter.site_leg(Ks, seed_of, chunk)
    out["site"] = {}
    for leg in SITE_SUBLEGS:
        s = site[leg]
        out["site"][leg] = dict(p=_check_p(s["p"], leg), floor=float(s["floor"]), seed=int(s["seed"]),
                                info=dict(s["info"]), K=Ks)
    if kind == "full":
        Kg = _k(K, "species")
        sp = adapter.species_leg(Kg, seed_of, g6l=g6l)
        p = {}
        for leg in SPECIES_SUBLEGS:
            v = sp["p"][leg]
            p[leg] = None if v is None else _check_p(v, leg)
        st = dict(sp["status"])
        if st["G6s"] != "ok" or p["G6s"] is None:
            raise RuntimeError("G6s needs no pool (RUN_PLAN R8 :576) and must always be computed")
        for leg in ("G1", "G3m"):
            if (st[leg] == "ok") != (p[leg] is not None):
                raise RuntimeError(f"{leg}: status {st[leg]!r} disagrees with its p")
        if (st["G6l"] == "ok") != (p["G6l"] is not None):
            raise RuntimeError(f"G6l: status {st['G6l']!r} disagrees with its p")
        flag, share = adapter.uninformative()
        out["species"] = dict(p=p, status=st, floors=dict(sp["floors"]), g6l=dict(sp["g6l_info"]),
                              g6s_exact=bool(sp["g6s_exact"]), n_G6s=int(sp["n_G6s"]), K=Kg,
                              conditioned=bool(sp.get("conditioned", True)), pools=dict(sp.get("pools", {})))
        if sp.get("g6s_identity") is not None:
            out["species"]["g6s_identity"] = dict(sp["g6s_identity"])
        out["uninformative"] = dict(flag=bool(flag), share=float(share))
        if keep_species_raw:
            out["_species_raw"] = sp
    check_exact_floors(out)  # RUN_PLAN_amend_1 R32 (c): a failure stops the run
    return out


def shared_g6l(ctx, S, streams: Mapping[str, np.random.SeedSequence], K: int) -> dict:
    """One exact G6l screen of (S, class, analysis parcels) serving several streams (RUN_PLAN §4 'Shared G6l screens':
    the row's leg 5 and, for decoded-list rows, its T_abs leg 25), through adapters.g6l_screen_safe (R8's no-window
    rule). Returns {stream name: (sets, info)}; stream by stream identical to an unshared screen (P0)."""
    names = list(streams)
    res = AD.g6l_screen_safe(ctx.B, S, [np.random.default_rng(streams[n]) for n in names], keep=int(K))
    return dict(zip(names, res))


# ================================================================================================================
# per-direction leg p's, d*, assembly
# ================================================================================================================
def leg_p_by_direction(legs: dict) -> dict:
    """{leg: {d: p}} for the composite verdict legs ('Level 0', 'site', and 'species' for full forms); a species
    sub-leg without a p makes the species leg NaN in both directions (a3_port.pmax: a missing leg never vanishes)."""
    out = {"Level 0": dict(legs["level0"]["p"])}
    s = legs["site"]
    out["site"] = {d: max(s["S1c"]["p"][d], s["S2c"]["p"][d]) for d in DIRECTIONS}
    if legs["kind"] == "full":
        sp = legs["species"]["p"]
        out["species"] = {d: A3.pmax(*[None if sp[leg] is None else sp[leg][d] for leg in SPECIES_SUBLEGS])
                          for d in DIRECTIONS}
    return out


def conjunction_by_direction(legs: dict) -> dict:
    """{d: max over the composite legs of p_leg(d)} (NaN if a leg has no p)."""
    by = leg_p_by_direction(legs)
    return {d: A3.pmax(*[v[d] for v in by.values()]) for d in DIRECTIONS}


def choose_direction(conj: dict, T_signs, two_sided: bool, registered_direction) -> tuple:
    """(d*, rule, reason-if-undefined). One-sided: the registered direction (prereg.md:117). Two-sided (R1):
    argmin_d conj(d); a tie goes to the sign of the observed T (+ if T = 0); several maps (two-cohort): their T signs
    must agree, else TWO_COHORT_TIE. conj NaN in both directions: d* undefined (see the module docstring)."""
    if not two_sided:
        if registered_direction not in DIRECTIONS:
            raise ValueError("a one-sided claim needs its registered direction (+1 / -1), got "
                             f"{registered_direction!r}")
        return int(registered_direction), "registered direction (one-sided; prereg.md:117)", None
    if registered_direction is not None:
        raise ValueError("a two-sided claim takes no registered direction (R1: d* is chosen from the legs)")
    fin = {d: math.isfinite(conj[d]) for d in DIRECTIONS}
    if not any(fin.values()):
        return None, None, NO_DSTAR
    if not all(fin.values()):
        raise RuntimeError("the conjunction has a p in one direction only: a code defect (a leg's p is direction-free)")
    if conj[1] < conj[-1]:
        return 1, "argmin_d max_leg p(d) (R1)", None
    if conj[-1] < conj[1]:
        return -1, "argmin_d max_leg p(d) (R1)", None
    signs = {_sign(t) for t in T_signs}
    if len(signs) == 1:
        return signs.pop(), "tie: the sign of the observed T, + if T = 0 (R1)", None
    # RUN_PLAN_amend_1 R36 (b): the fact behind the reading (p(+) + p(-) >= 1 for every leg) is asserted
    if not conj[1] >= 0.5:
        raise RuntimeError(f"two-cohort tie at M = {conj[1]!r} < .5: impossible for (k + 1)/(n + 1) or parametric legs "
                           "(RUN_PLAN_amend_1 R36 (b)); a code defect")
    return None, None, TWO_COHORT_TIE


def assemble_verdict_a1(legs: dict, *, alpha: float = ALPHA_V, two_sided: bool, registered_direction=None,
                        by_construction_label: str | None = None, direction: int | None = None,
                        direction_rule: str | None = None, direction_reason: str | None = None,
                        two_cohort_map: bool = False) -> dict:
    """The A1 verdict record from collect_legs' output (no null is recomputed). direction: a d* fixed by the caller
    (two_cohort_verdict); otherwise chosen here (choose_direction). RUN_PLAN_amend_1 R32 (c) is asserted first on
    every exact leg (check_exact_floors). two_cohort_map: this map is one map of a two-cohort claim whose d* the caller
    fixed (two_cohort_from_legs); with the claim's d* undefined (R36 (a): the OTHER map may be the one without a p) the
    map reports its one-sided p's, no doubled p, and survives = False, whatever its own direction-free status."""
    check_exact_floors(legs)
    if direction is None and direction_reason is None:
        conj = conjunction_by_direction(legs)
        direction, direction_rule, direction_reason = choose_direction(conj, [legs["T"]], two_sided,
                                                                       registered_direction)
    elif direction is not None and direction not in DIRECTIONS:
        raise ValueError(f"direction {direction!r}")
    if legs["kind"] == "full":
        return _assemble_full(legs, direction, direction_rule, direction_reason, alpha, two_sided,
                              registered_direction, by_construction_label, two_cohort_map=bool(two_cohort_map))
    if two_cohort_map:
        raise NotImplementedError("two-cohort claims are enrichment claims (claims_register.md:1639); no frozen "
                                  "two-cohort reading for component forms")
    return _assemble_component(legs, direction, direction_rule, direction_reason, alpha, two_sided,
                               registered_direction, by_construction_label)


def _head(legs, d, rule, reason, alpha, two_sided, registered_direction) -> dict:
    conj = conjunction_by_direction(legs)
    reg = int(registered_direction) if (not two_sided and registered_direction in DIRECTIONS) else None
    return dict(form=legs["form"], kind=legs["kind"], T=legs["T"], n_parcels=legs["n_parcels"], K=legs["K"],
                alpha=float(alpha), two_sided=bool(two_sided), registered_direction=reg,
                d_star=d, d_star_rule=rule, d_star_reason=reason,
                conjunction_one_sided={k: _nan_to_none(v) for k, v in conj.items()},
                labels=dict(p_per_leg_two_sided=PER_LEG_LABEL) if two_sided else {})


def _site_records(legs, d, two_sided) -> tuple[dict, float]:
    recs = {}
    for leg in SITE_SUBLEGS:
        s = legs["site"][leg]
        recs[leg] = _leg_record(s["p"], s["floor"], two_sided, d, seed=s["seed"], info=s["info"], K=s["K"])
    pd_site = leg_p_by_direction(legs)["site"]
    floor = max(legs["site"]["S1c"]["floor"], legs["site"]["S2c"]["floor"])
    recs["site"] = _leg_record(pd_site, floor, two_sided, d, rule="max(S1c, S2c) (prereg_amend_3.md:74)")
    return recs, floor


def _assemble_full(legs, d, rule, reason, alpha, two_sided, registered_direction, label, *,
                   two_cohort_map: bool = False) -> dict:
    out = _head(legs, d, rule, reason, alpha, two_sided, registered_direction)
    by = leg_p_by_direction(legs)
    rec = {"Level 0": _leg_record(legs["level0"]["p"], None, two_sided, d, kind=legs["level0"]["kind"])}
    site_recs, _ = _site_records(legs, d, two_sided)
    rec.update(site_recs)
    sp = legs["species"]
    for leg in SPECIES_SUBLEGS:
        rec[leg] = _leg_record(sp["p"][leg], sp["floors"].get(leg), two_sided, d, status=sp["status"][leg])
    sp_floor = max(sp["floors"].values())  # the species legs' floors present (src/asdg/species.py:220-224)
    species_p = None if any(sp["p"][leg] is None for leg in SPECIES_SUBLEGS) else by["species"]
    rec["species"] = _leg_record(species_p, sp_floor, two_sided, d,
                                 status="ok" if species_p is not None else "no p (a sub-leg has none)",
                                 rule="max(G1, G3m, G6s, G6l) (prereg_amend_3.md:75)")
    out["legs"] = rec

    def nanp(v):
        return float("nan") if v is None else float(v)

    # the engine's status order and resolution label, fed with the reported p's and the effective floors (R1, R9)
    site_e = dict(p_S1c=nanp(rec["S1c"]["p_reported"]), p_S2c=nanp(rec["S2c"]["p_reported"]),
                  info_S1c=dict(floor=rec["S1c"]["floor_effective"]),
                  info_S2c=dict(floor=rec["S2c"]["floor_effective"]))
    species_e = dict(p_species=nanp(rec["species"]["p_reported"]), species_min_p=rec["species"]["floor_effective"],
                     g6l_status=sp["status"]["G6l"], uninformative=legs["uninformative"]["flag"])
    v = engine_verdict(nanp(rec["Level 0"]["p_reported"]), site_e, species_e, alpha)
    r8 = [leg for leg in ("G1", "G3m") if sp["status"][leg] != "ok"]
    flags = []
    if r8:
        flags.append(R8_NOT_AUDITABLE)
    if sp["status"]["G6l"] != "ok":
        flags.append(f"g6l {sp['status']['G6l']}")
    if legs["uninformative"]["flag"]:
        flags.append("uninformative")
    if v["resolution"]["limited"]:
        flags.append("resolution-limited")
    if label is not None:
        primary, prule = str(label), "the register's by-construction label (R9; claims_register.md:1462-1464)"
    elif r8:
        primary, prule = R8_NOT_AUDITABLE, f"R8: verdict leg(s) {', '.join(r8)} not computable (pool < m)"
    else:
        primary, prule = v["status"], "asdg.verdict order (R9; src/asdg/verdict.py:30-38)"
    tie = d is None and reason == TWO_COHORT_TIE
    # asdg-skeptic WP1 review B2: a map of a two-cohort claim whose claim-level d* is undefined because a verdict leg
    # (of either map) has no p (RUN_PLAN_amend_1 R36 (a)): its one-sided p's are reported, no doubled p; not surviving
    no_claim_dstar = bool(two_cohort_map and d is None and reason == NO_DSTAR)
    if d is None and primary == "ok" and not (tie or no_claim_dstar):
        # single map: d* is undefined only when a leg has no p, never with status ok
        raise RuntimeError("d* undefined with status ok: a code defect")
    if tie:  # RUN_PLAN_amend_1 R36 (b): the map's direction-free status stands; no doubled p (R36 (a)); not surviving
        prule += "; d* undefined (two-cohort tie, opposite observed T signs: RUN_PLAN_amend_1 R36 (b))"
    if no_claim_dstar:
        prule += ("; the two-cohort claim's d* is undefined (a verdict leg has no p: RUN_PLAN_amend_1 R36 (a)): one-sided "
                  "p's reported, no doubled p; does not survive")
    members = [rec[k]["p_reported"] for k in ("Level 0", "site", "species")]
    p_conj = A3.pmax(*members)
    if primary == "ok" and not (tie or no_claim_dstar):
        if not all(m is not None and math.isfinite(m) for m in members):
            raise RuntimeError("an ok status with a non-finite member (a3_port READINGS C4): refused, never read "
                               "as a p")
        if not (v["status"] == "ok" and p_conj == v["p_verdict"]):
            raise RuntimeError(f"engine verdict disagrees: {v['status']} / {v['p_verdict']} vs {p_conj}")
    survives = bool(primary == "ok" and p_conj < alpha and not no_claim_dstar)
    if no_claim_dstar and not math.isnan(p_conj):
        raise RuntimeError("two-cohort map without a claim-level d* reported a doubled p: a code defect (R36 (a))")
    if d is not None:
        want = min(1.0, 2.0 * conjunction_by_direction(legs)[d]) if two_sided else conjunction_by_direction(legs)[d]
        if not (math.isnan(want) and math.isnan(p_conj)) and want != p_conj:
            raise RuntimeError(f"conjunction p {p_conj} != R1's min(1, 2 min_d max_leg p) {want}")
    out.update(p_conjunction=_nan_to_none(p_conj), survives=survives, primary_status=primary,
               primary_status_rule=prule, engine_status=v["status"], flags=flags,
               resolution=dict(v["resolution"]), floors_effective=dict(v["floors"]),
               uninformative=dict(legs["uninformative"]), g6l=dict(sp["g6l"]), g6s_exact=sp["g6s_exact"],
               n_G6s=sp["n_G6s"], species_conditioned=sp["conditioned"], pools=sp["pools"],
               not_computable_legs=r8)
    if no_claim_dstar:
        out["reading"] = TWO_COHORT_NO_DSTAR_READING
    return out


def _assemble_component(legs, d, rule, reason, alpha, two_sided, registered_direction, label) -> dict:
    out = _head(legs, d, rule, reason, alpha, two_sided, registered_direction)
    L0 = legs["level0"]
    rec = {"Level 0": _leg_record(L0["p"], L0["floor"], two_sided, d, kind=L0["kind"])}
    site_recs, site_floor = _site_records(legs, d, two_sided)
    rec.update(site_recs)
    out["legs"] = rec
    floors = {"site": rec["site"]["floor_effective"]}
    if L0["floor"] is not None:
        floors["level0"] = rec["Level 0"]["floor_effective"]
    res = engine_resolution(floors, alpha)
    members = [rec["Level 0"]["p_reported"], rec["site"]["p_reported"]]
    p_comp = A3.pmax(*members)
    if d is not None and not all(m is not None and math.isfinite(m) for m in members):
        raise RuntimeError("component claim with a non-finite leg p: a code defect")
    status = "resolution-limited" if res["limited"] else "ok"
    passes = bool(d is not None and status == "ok" and p_comp < alpha)
    flags = ["component-level"] + (["resolution-limited"] if res["limited"] else [])
    primary = str(label) if label is not None else status
    out.update(p_component=_nan_to_none(p_comp), p_conjunction=_nan_to_none(p_comp),
               p_rule="component-level p = max(Level 0, site leg) (R29; prereg_amend_5.md:156)",
               passes_component_level=passes, reading=component_reading(passes, alpha), label=COMPONENT_LABEL,
               survives=False, never_survives="component-level claims never count as survivals (prereg_amend_5.md:160)",
               primary_status=primary,
               primary_status_rule=("the register's by-construction label (R9)" if label is not None
                                    else "component status (resolution label; prereg_amend_3.md:94-96)"),
               status=status, flags=flags, resolution=dict(res), floors_effective=floors)
    return out


# ================================================================================================================
# entry points
# ================================================================================================================
def claim_verdict_a1(adapter, K, seed_of: Callable, *, alpha: float = ALPHA_V, two_sided: bool,
                     registered_direction: int | None = None, g6l=None, by_construction_label: str | None = None,
                     chunk: int = AD.CHUNK_MAX) -> dict:
    """A1's verdict on one claim on one map (R1, R8, R9): full verdict for set-vs-map / decoded-list / PLS-enrichment,
    component level for component forms. K: one count (audit 10,000) or {'site', 'species', 'permutation'}.
    two_sided: the TSV direction field begins with / carries "two-sided"; else registered_direction = +1 / -1.
    by_construction_label: the register's label where one exists (e.g. 'resolution-limited' for the six Giacomel
    subcortical cells, TSV rows 92, 94, 96, 98, 100, 102)."""
    legs = collect_legs(adapter, K, seed_of, g6l=g6l, chunk=chunk)
    return assemble_verdict_a1(legs, alpha=alpha, two_sided=two_sided, registered_direction=registered_direction,
                               by_construction_label=by_construction_label)


def two_cohort_from_legs(legs_a: dict, legs_b: dict, *, alpha: float = ALPHA_V, two_sided: bool,
                         registered_direction=None, map_labels=("map 0", "map 1")) -> dict:
    """R1 :442-445 / claims_register.md:1639-1641 / P14: one d* = argmin_d max over both maps' legs; each map's
    verdict assembled in d*; survives iff both survive; p = the larger conjunction p."""
    for lg in (legs_a, legs_b):
        if lg["kind"] != "full":
            raise NotImplementedError("two-cohort claims are enrichment claims (claims_register.md:1639); no frozen "
                                      "two-cohort reading for component forms")
    ca, cb = conjunction_by_direction(legs_a), conjunction_by_direction(legs_b)
    conj = {d: A3.pmax(ca[d], cb[d]) for d in DIRECTIONS}
    d, rule, reason = choose_direction(conj, [legs_a["T"], legs_b["T"]], two_sided, registered_direction)
    if d is None and reason is None:
        raise RuntimeError("unreachable")
    kw = dict(alpha=alpha, two_sided=two_sided, registered_direction=registered_direction, direction=d,
              direction_rule=rule, direction_reason=reason, two_cohort_map=True)
    ra, rb = assemble_verdict_a1(legs_a, **kw), assemble_verdict_a1(legs_b, **kw)
    per = {map_labels[0]: ra, map_labels[1]: rb}
    p = A3.pmax(_nan_to_float(ra["p_conjunction"]), _nan_to_float(rb["p_conjunction"]))
    p_rule = "the larger conjunction p (claims_register.md:1640)"
    tie = reason == TWO_COHORT_TIE
    no_dstar = d is None and reason == NO_DSTAR   # B2: a map's verdict leg has no p (R36 (a) at claim level)
    if ra["primary_status"] == "ok" and rb["primary_status"] == "ok":
        if no_dstar:
            raise RuntimeError("two-cohort claim without d* although both maps read ok: a code defect (R36 (a))")
        primary, prule = "ok", "both maps ok"
    else:
        primary, prule = _first_status([ra["primary_status"], rb["primary_status"]])
    extra = {}
    if no_dstar:  # RUN_PLAN_amend_1 R36 (a): no doubled p; every computed leg's one-sided p's (per map); not surviving
        p_rule = "no conjunction p: d* undefined (a verdict leg of a map has no p; RUN_PLAN_amend_1 R36 (a))"
        extra = dict(reading=TWO_COHORT_NO_DSTAR_READING)
    if tie:  # RUN_PLAN_amend_1 R36 (b): does not survive; conjunction p = min(1, 2M) = 1; statuses direction-free
        M = conj[1]
        p = min(1.0, 2.0 * M)
        if p != 1.0:
            raise RuntimeError(f"two-cohort tie with min(1, 2M) = {p!r} != 1: a code defect (RUN_PLAN_amend_1 R36 (b))")
        p_rule = "min(1, 2M) at a two-cohort tie, M the common maximum in both directions (RUN_PLAN_amend_1 R36 (b))"
        prule += " (direction-free statuses: status order, floors and flags; RUN_PLAN_amend_1 R36 (b))"
        extra = dict(reading=TWO_COHORT_TIE_READING, tie_common_max=float(M))
    survives = bool(not tie and not no_dstar and primary == "ok" and ra["survives"] and rb["survives"])
    if no_dstar and not (math.isnan(p) and not ra["survives"] and not rb["survives"]):
        raise RuntimeError("two-cohort claim without d*: a doubled p or a surviving map was reported (R36 (a))")
    if survives and not p < alpha:
        raise RuntimeError("two-cohort: both maps survive but the larger conjunction p is not below alpha")
    return dict(two_cohort=True, map_labels=list(map_labels), alpha=float(alpha), two_sided=bool(two_sided),
                registered_direction=None if two_sided else int(registered_direction), d_star=d, d_star_rule=rule,
                d_star_reason=reason, conjunction_one_sided={k: _nan_to_none(v) for k, v in conj.items()},
                conjunction_one_sided_per_map={map_labels[0]: {k: _nan_to_none(v) for k, v in ca.items()},
                                               map_labels[1]: {k: _nan_to_none(v) for k, v in cb.items()}},
                p_conjunction=_nan_to_none(p), p_rule=p_rule,
                survives=survives, survives_rule="survives iff both maps survive in d* (claims_register.md:1639-1641)",
                primary_status=primary, primary_status_rule=prule,
                flags=sorted({f for r in (ra, rb) for f in r["flags"]}), per_map=per, **extra)


def _nan_to_float(v):
    return float("nan") if v is None else float(v)


def _descriptive_copy(o):
    """The computed record of a descriptor row with every 'survives' renamed 'passes_at_alpha' (and 'survives_rule'
    'passes_at_alpha_rule'); a pass at alpha, or at component level, carries DESCRIPTIVE beside it."""
    if isinstance(o, Mapping):
        out = {}
        for k, v in o.items():
            if k == "survives":
                out["passes_at_alpha"] = bool(v)
                if v:
                    out["passes_at_alpha_label"] = DESCRIPTIVE
            elif k == "survives_rule":
                out["passes_at_alpha_rule"] = v
            elif k == "passes_component_level":
                out[k] = bool(v)
                if v:
                    out["passes_component_level_label"] = DESCRIPTIVE
            else:
                out[k] = _descriptive_copy(v)
        return out
    if isinstance(o, list):
        return [_descriptive_copy(v) for v in o]
    return o


def _contains_key(o, key: str) -> bool:
    if isinstance(o, Mapping):
        return key in o or any(_contains_key(v, key) for v in o.values())
    if isinstance(o, list):
        return any(_contains_key(v, key) for v in o)
    return False


def descriptor_row_record(computed: Mapping, tsv_status: str, *, status_tsv: str | None = None,
                          label: str | None = None) -> dict:
    """asdg-skeptic WP1 review, B1 (DESCRIPTOR_ROW_RULE): a descriptor row (a descriptor cell, a 'not testable as
    stated' pooled list, R21 / R28's descriptor reading) never survives. computed: the record assemble_verdict_a1 /
    two_cohort_from_legs gave the row. Returns survives = False, primary_status = tsv_status (the row's TSV status as
    read under the run's view), the claim's direction fields (the descriptor pass reports its legs at this d*,
    RUN_PLAN_amend_1 R36 (d)) and the computed record under 'descriptor' (_descriptive_copy: no 'survives' key left in
    it; a pass at alpha reads 'descriptive (not a verdict)'). No p is moved to the top level."""
    if not isinstance(tsv_status, str) or not tsv_status:
        raise ValueError("descriptor_row_record needs the row's TSV status")
    if not isinstance(computed, Mapping) or "survives" not in computed:
        raise ValueError("descriptor_row_record takes a computed verdict record")
    passes = bool(computed.get("survives")) or bool(computed.get("passes_component_level"))
    desc = _descriptive_copy(computed)
    if _contains_key(desc, "survives"):
        raise RuntimeError("descriptor row: a 'survives' key left in the descriptive record (a code defect)")
    alpha = computed.get("alpha", ALPHA_V)
    reading = (f"{DESCRIPTIVE}: passes at alpha {_reading_alpha(float(alpha))}" if passes
               else f"{DESCRIPTIVE}: does not pass at alpha {_reading_alpha(float(alpha))}")
    out = dict(descriptor_row=True, form=computed.get("form"), kind=computed.get("kind"),
               two_cohort=bool(computed.get("two_cohort", False)), T=computed.get("T"),
               alpha=float(alpha), two_sided=computed.get("two_sided"),
               registered_direction=computed.get("registered_direction"), d_star=computed.get("d_star"),
               d_star_rule=computed.get("d_star_rule"), d_star_reason=computed.get("d_star_reason"),
               survives=False, primary_status=str(tsv_status), primary_status_rule=DESCRIPTOR_ROW_RULE,
               status_tsv=status_tsv, label=label, passes_at_alpha=passes, reading=reading, descriptor=desc)
    return out


def _first_status(statuses) -> tuple[str, str]:
    """The claim-level primary status over several maps: a by-construction label or R8's label first, then the
    engine's order (R9; src/asdg/verdict.py:30-38)."""
    for s in statuses:
        if s == R8_NOT_AUDITABLE:
            return s, "R8 on a map"
    for s in ENGINE_ORDER:
        if s in statuses:
            return s, "asdg.verdict order over both maps (R9)"
    others = [s for s in statuses if s != "ok"]
    if others:
        return others[0], "a map's primary status"
    raise RuntimeError("no non-ok status found")


def two_cohort_verdict(adapter_a, adapter_b, K, seed_of_a: Callable, seed_of_b: Callable, *,
                       alpha: float = ALPHA_V, two_sided: bool, registered_direction: int | None = None,
                       g6l_a=None, g6l_b=None, map_labels=("map 0", "map 1"), chunk: int = AD.CHUNK_MAX) -> dict:
    """Mamat's two-cohort enrichment claims (P14): each map's legs on its own keys (map index 0 = ABIDE I, 1 = ABIDE II,
    claims_register.md:1077-1078), one d* over both, both must survive in d*, p = the larger."""
    la = collect_legs(adapter_a, K, seed_of_a, g6l=g6l_a, chunk=chunk)
    lb = collect_legs(adapter_b, K, seed_of_b, g6l=g6l_b, chunk=chunk)
    return two_cohort_from_legs(la, lb, alpha=alpha, two_sided=two_sided, registered_direction=registered_direction,
                                map_labels=map_labels)


# ================================================================================================================
# seed callables from a1_audit.seeds (R7, R24; claims_register.md:1076-1082)
# ================================================================================================================
LEG_ALIASES = {"permutation": "permutation / label"}  # adapters' name for leg 8
TABS_LEGS = {"S1c": "T_abs S1c", "S2c": "T_abs S2c", "G1": "T_abs G1", "G3m": "T_abs G3m", "G6l": "T_abs G6l"}


def seed_callables(target_number: int, row: int, map_index: int, cell_index: int) -> dict:
    """The callables the driver and the descriptor pass take, built on a1_audit.seeds (claim keys):
    - seed_of(leg) -> SeedSequence([20260925, 100 + target, row, leg, map index, cell index]) for the adapters' names
      'S1c', 'S2c', 'G1', 'G3m', 'G6s', 'G6l', 'permutation' (leg 8) and the register's 're-selection', 'G2', 'G4',
      'G5', 'J1', 'naive joint';
    - tabs_seed_of(leg) for the T_abs adapter's names 'S1c', 'S2c', 'G1', 'G3m', 'G6l' -> legs 21-25 (no G6s form);
    - g3_seed() -> R24's key (the first spawned child of leg 3's key; seeds.g3_seed)."""
    from . import seeds as SD

    def seed_of(leg: str) -> np.random.SeedSequence:
        name = LEG_ALIASES.get(leg, leg)
        if name.startswith("T_abs"):
            raise ValueError("T_abs legs go through tabs_seed_of")
        return SD.claim_seed(target_number, row, name, map_index, cell_index)

    def tabs_seed_of(leg: str) -> np.random.SeedSequence:
        if leg not in TABS_LEGS:
            raise ValueError(f"T_abs has no leg {leg!r} (legs 21-25: S1c, S2c, G1, G3m, G6l; no G6s form)")
        return SD.claim_seed(target_number, row, TABS_LEGS[leg], map_index, cell_index)

    def g3_seed() -> np.random.SeedSequence:
        return SD.g3_seed(target_number, row, map_index, cell_index)

    return dict(seed_of=seed_of, tabs_seed_of=tabs_seed_of, g3_seed=g3_seed,
                key=dict(target_number=int(target_number), row=int(row), map_index=int(map_index),
                         cell_index=int(cell_index)))


def plant_seed_callables(plant_id: int, case: int, class_id: int) -> dict:
    """seed_callables' callables on PLANT keys (asdg-skeptic WP1 review B3; PLANT CHOICE (orchestrator, 2026-10-01): leg
    streams within a plant case): seed_of(leg) -> SeedSequence([20260925, 900, plant_id, case, class_id, leg]) with the
    registered leg number; tabs_seed_of -> legs 21-25; g3_seed -> R24's first spawned child of the case's leg-3 key
    (seeds.plant_g3_seed). J1 / the naive joint take seed_of('J1') / seed_of('naive joint') and draw in R7's order
    inside the descriptor pass, as on claim keys."""
    from . import seeds as SD

    def seed_of(leg: str) -> np.random.SeedSequence:
        name = LEG_ALIASES.get(leg, leg)
        if name.startswith("T_abs"):
            raise ValueError("T_abs legs go through tabs_seed_of")
        return SD.plant_leg_seed(plant_id, case, class_id, name)

    def tabs_seed_of(leg: str) -> np.random.SeedSequence:
        if leg not in TABS_LEGS:
            raise ValueError(f"T_abs has no leg {leg!r} (legs 21-25: S1c, S2c, G1, G3m, G6l; no G6s form)")
        return SD.plant_leg_seed(plant_id, case, class_id, TABS_LEGS[leg])

    def g3_seed() -> np.random.SeedSequence:
        return SD.plant_g3_seed(plant_id, case, class_id)

    return dict(seed_of=seed_of, tabs_seed_of=tabs_seed_of, g3_seed=g3_seed,
                key=dict(keys="plant", plant_id=int(plant_id), case=int(case), class_id=int(class_id)))
