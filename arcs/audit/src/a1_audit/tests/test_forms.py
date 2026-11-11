"""P15, P16 and the R21 / R28 value checks of the special claim forms (a1_audit/forms.py and run.py's WP2 routes;
arcs/audit/RUN_PLAN.md v3.1 §4 :353-363, §7 :1142-1144, R10, R21, R28; RUN_PLAN_amend_1.md v2.1 R32 (b), R36; FROZEN).

    cd arcs/audit/src
    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_forms [--scratch DIR] [--keep] [--no-cli]

Part P15  signed-weight descriptor on a synthetic dk-ctx class (and the V-DK-subcortex class for the exact site leg):
          every gene leg (G1, G2, G3 on R24's stream, G4, G5, J1) draws exactly the sets its unweighted sampler draws
          from the same key, then gives each null set S's weight vector in a random order (U-F1), recomputed
          independently (same members; the multiset of weights is S's; the orders equal an independent replay); every
          null map equals a direct loop sum_j w_j X[:, R_j] / sum(w); rho counts equal an independent integer
          recomputation (scipy ranks, Python integers); must-fail: unpermuted weights give other maps. The site leg on
          rho (verdict pass): T = scipy's Spearman, S1c / S2c counts recomputed from the regenerated surrogates (sampled
          on dk-ctx; exact on V-DK-subcortex, identity counted, p >= 2/(N + 1)). sum(w) = 0 refused.
Part P15 / R41 (RUN_PLAN_amend_2 R41): the descriptor pass on the class matrix - T_S, the legs (= the machinery with
          T_S as the observed map), the basis hash, the (ii) + (a) variant caught, sum w = 0, the registered outcome
          answered iff T_S is within ±.05 of the published value, U-F1's order (an orders-first variant caught), the
          TSV comparators (R41's MDD pins).
Part P16  gene-set-only (R10) on synthetic BrainSpan-like and AHBA-like per-sample frames with NaN / inf / constant
          columns, ties and planted sample ids: per-sample rank-biserial r = scipy's Mann-Whitney U form; U_stat's
          drop counts equal an independent count over the samples used; T (Python-int numerator / denominator) equals
          an independent Fraction computation; G1-G5 drawn on U_stat with the coexpression over the same samples
          (np.corrcoef); G3 on R24's stream (and not leg 3's); every leg's integer comparison recomputed independently
          (T1 / T2: n_post sum N_pre - n_pre sum N_post); G5 carries the register's label; refusals (an undeclared
          metadata column, a misaligned index, an unknown age form, an undeclared scale, a negative RPKM); no sample id
          in the record, and (CLI) in no output file, stdout or stderr of a runner dev run. RUN_PLAN_amend_2 R42:
          BrainSpan on log2(RPKM + 1) with duplicate symbols averaged and counted (a raw-RPKM coexpression caught);
          SD7's label formats, drops and fail-closed cases; pooled iff merged; unpooled T5 = the mean of the two
          hippocampus values; a T4 with no matched cortical label fails closed.
Part R    R21 (MOR-T1 / T2) and R28 (BENK-C2-SD / -DD, PARK-C5): routes, labels, proxy directions; through a runner
          dev run, T = the directly computed mean per-gene Pearson r of S, no T_abs, the descriptor legs present, the
          RLM attached to the BENK / PARK rows; the RLM equals statsmodels and a direct IRLS Huber fit, its NaN rows
          dropped and counted; must-fail: a wrong Huber constant is caught by rlm_t's assertion.
Part D    the dispatcher over all 692 TSV rows (four views): no exception, no stub left, the new routes' counts.

Synthetic data only: run.SyntheticSources points every engine data path at a non-existent directory. Exits non-zero on
any failure. Prints ASCII only.
"""
from __future__ import annotations

import os

for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_k] = "1"

import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
import traceback  # noqa: E402
from fractions import Fraction  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1]
REPO = HERE.parents[4]
for _p in (REPO / "src", SRC):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from a1_audit import adapters as AD  # noqa: E402
from a1_audit import descriptors as DS  # noqa: E402
from a1_audit import forms as FM  # noqa: E402
from a1_audit import run as R  # noqa: E402
from a1_audit import seeds as SD  # noqa: E402
from a1_audit import verdict as V  # noqa: E402
from asdg.genesets import coexpr_matched_sets, trajectory_matched_sets  # noqa: E402
from asdg.spatial import site_null  # noqa: E402

RESULTS: list[tuple[str, bool]] = []
SEP = "-" * 100
LIU_ROWS = {"LIU-T1": 471, "LIU-T2": 472, "LIU-T4": 473, "LIU-T5": 474, "LIU-T2-STR": 475, "LIU-T2-CBC": 476,
            "LIU-T2-HIP": 477}
SW_ROWS = (103, 104, 117, 120, 121)
R_ROWS = (518, 519, 603, 618, 619)
CLI_K = "site=120,species=40,permutation=120,sets=40,surr=120,j1_sets=30"


class SynSrc:
    """The plant / case words run.SyntheticSources gives the forms.py providers (case None: no plant case named)."""

    def __init__(self, plant_id: int, case=None):
        self.plant_id, self.case = int(plant_id), case


SRC16, SRC17 = SynSrc(16), SynSrc(17)


def check(name: str, cond, detail: str = "") -> bool:
    ok = bool(cond)
    RESULTS.append((name, ok))
    print(R.ascii_line("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  [" + detail + "]") if detail else "")),
          flush=True)
    return ok


def raises(fn, exc, contains: str | None = None) -> bool:
    try:
        fn()
    except exc as e:  # noqa: PERF203
        return contains is None or contains in str(e)
    except Exception:  # noqa: BLE001
        return False
    return False


# ----------------------------------------------------------------------------------------------------------------
# independent exact arithmetic (scipy ranks -> Python integers; never the module under test)
# ----------------------------------------------------------------------------------------------------------------
def int_centred_ranks(v) -> list[int]:
    r = stats.rankdata(np.asarray(v, dtype=float), method="average")
    d = [int(round(2 * x)) for x in r]
    assert all(abs(2 * x - k) < 1e-9 for x, k in zip(r, d))
    n = len(d)
    return [x - (n + 1) for x in d]


def rho_terms_indep(a, b) -> tuple[int, int]:
    A, B = int_centred_ranks(a), int_centred_ranks(b)
    return sum(x * y for x, y in zip(A, B)), sum(x * x for x in A) * sum(y * y for y in B)


def rho_ge(N, Q, N0, Q0) -> bool:
    """N / sqrt(Q) >= N0 / sqrt(Q0), exactly."""
    if N >= 0 > N0:
        return True
    if N < 0 <= N0:
        return False
    if N >= 0:
        return N * N * Q0 >= N0 * N0 * Q
    return N * N * Q0 <= N0 * N0 * Q


def rho_le(N, Q, N0, Q0) -> bool:
    return rho_ge(-N, Q, -N0, Q0)


def rho_counts_indep(y, maps, obs_map) -> tuple[int, int]:
    """Gene legs: the null states are rho(y, null map) against rho(y, observed map)."""
    N0, Q0 = rho_terms_indep(y, obs_map)
    kp = km = 0
    for mp in np.atleast_2d(maps):
        N, Q = rho_terms_indep(y, mp)
        kp += rho_ge(N, Q, N0, Q0)
        km += rho_le(N, Q, N0, Q0)
    return kp, km


def rho_counts_site(y, surrogates, b) -> tuple[int, int]:
    """Site legs: the null states are rho(surrogate of y, b) against rho(y, b)."""
    N0, Q0 = rho_terms_indep(y, b)
    kp = km = 0
    for v in np.atleast_2d(surrogates):
        N, Q = rho_terms_indep(v, b)
        kp += rho_ge(N, Q, N0, Q0)
        km += rho_le(N, Q, N0, Q0)
    return kp, km


# ----------------------------------------------------------------------------------------------------------------
# synthetic class pieces
# ----------------------------------------------------------------------------------------------------------------
def sw_pieces(src, cls: str, row: int):
    plan = dict(row=row, analysis_class=cls)
    ctx, counts, _ = src.context(cls)
    y, ids, _, _ = src.map(plan, 0)
    ap = AD.analysis_parcels(y, counts, parcel_ids=ids)
    keep = ap["parcel_ids"]
    c2 = ctx.restrict(keep)
    pos = {int(p): k for k, p in enumerate(ids)}
    yk = np.asarray(y, float)[[pos[p] for p in keep]]
    b, bids, _ = FM.synthetic_second_map(src, plan, 0)
    bpos = {int(p): k for k, p in enumerate(bids)}
    bk = b[[bpos[p] for p in keep]]
    genes, w, _ = FM.synthetic_gene_weights(src, plan)
    S, ws, info = FM.aligned_weights(genes, w, c2.U.index)
    return dict(ctx=c2, y=yk, b=bk, keep=keep, S=S, w=ws, info=info, plan=plan)


# ================================================================================================================
# Part P15
# ================================================================================================================
def p15_leg_checks(tag: str, ad, rec, replay_sets, rng_after, K: int) -> None:
    """rec: a leg record with _draws; replay_sets: the unweighted sampler's sets from a fresh generator of the same key;
    rng_after: that fresh generator, advanced past the sets (U-F1's orders follow)."""
    d = rec["_draws"]
    sets, perms, ordered = d["sets"], d["perms"], d["ordered"]
    m = ad.S.size
    check(f"P15 {tag}: the null sets are exactly the unweighted sampler's sets from the same key",
          replay_sets is not None and np.array_equal(sets, replay_sets), f"{len(sets)} sets")
    exp_perms = np.stack([rng_after.permutation(m) for _ in range(len(sets))])
    check(f"P15 {tag}: the weight orders equal an independent replay (one permutation per set, after the sets; U-F1)",
          np.array_equal(perms, exp_perms))
    same_members = all(sorted(o.tolist()) == sorted(s.tolist()) for o, s in zip(ordered, sets))
    multiset = all(sorted(ad.w.tolist()) == sorted(ad.w[np.argsort(p)].tolist()) for p in perms)
    distinct = len({tuple(p.tolist()) for p in perms})
    moved = float(np.mean([not np.array_equal(p, np.arange(m)) for p in perms]))
    check(f"P15 {tag}: each null set receives S's weight vector in a random order (same members; weights = S's; "
          f"{distinct} distinct orders of {len(perms)}; {moved:.2f} non-identity)",
          same_members and multiset and distinct == len(perms) and moved == 1.0)
    X, w = ad.ctx.X, ad.w
    direct = np.stack([sum(w[j] * X[:, o[j]] for j in range(m)) / w.sum() for o in ordered])
    got = ad.maps(ordered)
    check(f"P15 {tag}: null maps = sum_j w_j X[:, R_j] / sum(w) (direct loop, 1e-12)",
          float(np.max(np.abs(got - direct))) <= 1e-12 * max(1.0, float(np.max(np.abs(direct)))))
    unperm = ad.maps(sets)
    differ = float(np.mean(np.max(np.abs(unperm - got), axis=1) > 1e-9))
    check(f"P15 {tag} must-fail: unpermuted weights give other maps ({differ:.2f} of sets differ)", differ >= 0.9)
    kp, km = rho_counts_indep(ad.y, got, ad.obs_map)
    rr = rec["rank_rule"]
    n = len(ordered)
    check(f"P15 {tag}: rho counts = an independent integer recomputation (k+ {kp}, k- {km}; {rr['branch'][:20]})",
          rr["k_plus"] == kp and rr["k_minus"] == km and rec["p"][1] == (kp + 1) / (n + 1)
          and rec["p"][-1] == (km + 1) / (n + 1) and rec["n"] == K == n)


def part_p15(scratch: Path) -> None:
    print(SEP + "\nPart P15: signed-weight descriptor (claims_register.md:1469-1473; RUN_PLAN P15 :1142)")
    src = R.SyntheticSources(15, scratch / "_no_data_p15")
    pc = sw_pieces(src, "dk-ctx", 103)
    c2, yk, bk, keep, S, w = pc["ctx"], pc["y"], pc["b"], pc["keep"], pc["S"], pc["w"]
    sc = V.seed_callables(3, 103, 0, 0)
    K = 150
    check("P15 setup: synthetic dk-ctx, S of 25 with signed weights (some negative, sum 2)",
          c2.n >= 30 and S.size == 25 and (w < 0).any() and abs(w.sum() - 2.0) < 1e-12, f"n {c2.n}")
    s_map = FM.weighted_maps(c2.X, S[None, :], w)[0]
    direct_s = (c2.X[:, S] * w).sum(1) / w.sum()
    check("P15 S's weighted score = sum(w e) / sum(w) on the basis (1e-12)", np.max(np.abs(s_map - direct_s)) < 1e-12)
    traj, _ = src.trajectories("dk-ctx")
    for observed, obs in (("the paper map", bk), ("S's weighted score on the basis", s_map)):
        ad = FM.WeightedSetRho(c2, yk, S, w, obs, parcel_ids=keep, observed_label=observed)
        check(f"P15 [{observed}] T(S) = scipy Spearman rho(y, observed map) (1e-12)",
              abs(ad.T_obs - stats.spearmanr(yk, obs).statistic) < 1e-12, f"{ad.T_obs:.6f}")
        tag = f"[{observed}]"
        # G1 (leg 2)
        rec = FM.sw_uniform_leg(ad, K, np.random.default_rng(sc["seed_of"]("G1")), pool=np.arange(c2.G),
                                name="Level-2 G1", seed_leg=2, return_draws=True)
        g = np.random.default_rng(sc["seed_of"]("G1"))
        rep = np.stack([g.choice(np.setdiff1d(np.arange(c2.G), S), size=S.size, replace=False) for _ in range(K)])
        p15_leg_checks(f"{tag} G1", ad, rec, rep, g, K)
        # G3 (R24's stream)
        rec = FM.sw_uniform_leg(ad, K, np.random.default_rng(sc["g3_seed"]()), pool=np.flatnonzero(c2.B.brain),
                                name="G3", seed_leg="R24", return_draws=True)
        g = np.random.default_rng(SD.g3_seed(3, 103, 0, 0))
        pool = np.setdiff1d(np.flatnonzero(c2.B.brain), S)
        rep = np.stack([g.choice(pool, size=S.size, replace=False) for _ in range(K)])
        p15_leg_checks(f"{tag} G3 (R24 stream)", ad, rec, rep, g, K)
        leg3 = np.random.default_rng(SD.claim_seed(3, 103, 3, 0, 0))
        rep3 = np.stack([leg3.choice(pool, size=S.size, replace=False) for _ in range(5)])
        check(f"P15 {tag} G3: R24's stream differs from leg 3's", not np.array_equal(rep3, rec["_draws"]["sets"][:5]))
        # G2 / G4 (coexpression)
        for name, brain, leg in (("G2", False, "G2"), ("G4", True, "G4")):
            rec = FM.sw_coexpr_leg(ad, K, np.random.default_rng(sc["seed_of"](leg)), brain=brain, name=name,
                                   seed_leg=SD.LEGS[leg], return_draws=True)
            if rec["status"] != "ok":
                check(f"P15 {tag} {name}: sampler reached ok", False, rec["status"])
                continue
            g = np.random.default_rng(sc["seed_of"](leg))
            pa = np.flatnonzero(c2.B.brain) if brain else np.arange(c2.G)
            rep, _ = coexpr_matched_sets(c2.U, pa, S.size, float(c2.U.mean_coexpr(S)), K, g, exclude=S)
            p15_leg_checks(f"{tag} {name}", ad, rec, rep, g, K)
        # G5
        rec = FM.sw_g5_leg(ad, K, np.random.default_rng(sc["seed_of"]("G5")), traj, return_draws=True)
        if rec["status"] == "ok":
            g = np.random.default_rng(sc["seed_of"]("G5"))
            tr = DS.trajectories_for(c2, traj)
            rep, _ = trajectory_matched_sets(c2.U, [c2.U.genes[i] for i in S], tr, K, g)
            p15_leg_checks(f"{tag} G5", ad, rec, rep, g, K)
        else:
            check(f"P15 {tag} G5: sampler reached ok", False, rec["status"])
        # J1 (leg 14: S1c seed, S2c seed, G2 sets, then the orders)
        rec = FM.sw_j1_leg(ad, sc["seed_of"], K_sets=60, K_surr=150, return_draws=True)
        g = np.random.default_rng(SD.claim_seed(3, 103, 14, 0, 0))
        s1c, s2c = int(g.integers(2 ** 31)), int(g.integers(2 ** 31))
        rep, _ = coexpr_matched_sets(c2.U, np.arange(c2.G), S.size, float(c2.U.mean_coexpr(S)), 60, g, exclude=S)
        d = rec["_draws"]
        perms_rep = np.stack([g.permutation(S.size) for _ in range(60)])
        check(f"P15 {tag} J1: R7's order (S1c seed, S2c seed, the G2 sets), then the orders (U-F1), replayed",
              rec["seeds"] == dict(S1c=s1c, S2c=s2c) and np.array_equal(d["sets"], rep)
              and np.array_equal(d["perms"], perms_rep) and rec["status"] == "ok")
        zs = []
        for sur in (d["surrogates"]["S1c"][:5],):
            for v in sur:
                ts = stats.spearmanr(v, obs).statistic
                tm = np.array([stats.spearmanr(v, mp).statistic for mp in ad.maps(d["ordered"])])
                zs.append((ts - tm.mean()) / tm.std(ddof=1))
        z_obs_direct = (ad.T_obs - np.mean([stats.spearmanr(yk, mp).statistic for mp in ad.maps(d["ordered"])])) / \
            np.std([stats.spearmanr(yk, mp).statistic for mp in ad.maps(d["ordered"])], ddof=1)
        check(f"P15 {tag} J1: z_obs = (rho(S) - mean rho(R_k)) / sd rho(R_k) with weighted R_k (scipy, 1e-9)",
              abs(rec["z_obs"] - z_obs_direct) < 1e-9, f"{rec['z_obs']:.4f}")
        full = FM.signed_weight_gene_legs(ad, sc["seed_of"], sc["g3_seed"], K_sets=K, K_surr=150, K_j1_sets=60,
                                          traj=traj, direction=None, two_sided=True)
        l2 = full["level2"]
        ok_max = l2.get("p") is not None and all(
            l2["p"][dd] == max(full["legs"][n]["p"][dd] for n in DS.LEVEL2_LEGS) for dd in (1, -1))
        check(f"P15 {tag}: Level-2 p = max over G1-G5 per direction; two-sided without d*: no doubled p, the per-leg "
              "two-sided p reported (R36 (a))", ok_max and l2.get("p_reported") is None
              and all(r.get("p_reported") is None and r.get("p_per_leg_two_sided") is not None
                      for r in full["legs"].values()))
    w0 = np.zeros(S.size)
    w0[:4] = (1.0, -1.0, 2.5, -2.5)
    check("P15 sum(w) = 0 is refused (the weighted score is undefined)",
          raises(lambda: FM.weighted_maps(c2.X, S[None, :], w0), ValueError, "sum of S's weights")
          and raises(lambda: FM.WeightedSetRho(c2, yk, S, w0, bk, parcel_ids=keep, observed_label="x"), ValueError))
    # the site leg on rho (verdict pass)
    for cls, row, Ks in (("dk-ctx", 103, 300), ("V-DK-subcortex", 104, 10_000)):
        pc = sw_pieces(src, cls, row)
        scr = V.seed_callables(3, row, 0, 0)
        for two_sided, reg in ((True, None), (False, 1)):
            rec = FM.signed_weight_site(pc["ctx"], pc["y"], pc["b"], parcel_ids=pc["keep"], K=Ks,
                                        seed_of=scr["seed_of"], two_sided=two_sided, registered_direction=reg)
            okT = abs(rec["T"] - stats.spearmanr(pc["y"], pc["b"]).statistic) < 1e-12
            okc, exact = True, []
            for leg, method in (("S1c", "brainsmash"), ("S2c", "msr")):
                L = rec["site"]["legs"][leg]
                seed = SD.seed_int(SD.claim_seed(3, row, leg, 0, 0))
                sur, info = site_null(pc["y"], pc["ctx"].D, pc["ctx"].classes, Ks, seed, method)
                kp, km = rho_counts_site(pc["y"], sur, pc["b"])
                n = len(sur)
                okc &= (L["seed"] == seed and L["p"][1] == (kp + 1) / (n + 1) and L["p"][-1] == (km + 1) / (n + 1))
                exact.append(bool(info["exact"]))
                if info["exact"]:
                    okc &= min(L["p"][1], L["p"][-1]) >= 2 / (n + 1) and L["floor"] == 2 / (n + 1)
                if two_sided:
                    okc &= L["p_reported"] is None and L["p_per_leg_two_sided"] == min(1.0, 2 * min(L["p"].values()))
                else:
                    okc &= L["p_reported"] == L["p"][1]
            check(f"P15 site leg on rho [{cls}, {'two-sided' if two_sided else 'one-sided +'}]: T = scipy Spearman; "
                  f"S1c / S2c counts = independent recomputation on the regenerated surrogates (exact: {exact}); R36",
                  okT and okc and (exact == [True, True]) == (cls == "V-DK-subcortex"))


def part_p15_r41(scratch: Path) -> None:
    """RUN_PLAN_amend_2 R41's P15 extension (synthetic): the null maps and T_S on the class matrix (hash); the (ii) + (a)
    variant caught on an 'authors' matrix' with a planted gene-wise offset; sum w = 0 -> not computable; a T_S outside
    ±.05 of a planted published value -> 'not answered (T_S not reproduced)', inside -> answered; the weight orders
    drawn after the sets (a variant drawing them before is caught); the TSV's comparators read as R41 pins them."""
    print(SEP + "\nPart P15 / R41: signed-weight descriptor pass (RUN_PLAN_amend_2 R41; class matrix, T_S, outcome)")
    src = R.SyntheticSources(15, scratch / "_no_data_p15r41")
    pc = sw_pieces(src, "dk-ctx", 115)
    c2, yk, bk, keep, S, w = pc["ctx"], pc["y"], pc["b"], pc["keep"], pc["S"], pc["w"]
    genes, w_all, _ = FM.synthetic_gene_weights(src, pc["plan"])
    traj, _ = src.trajectories("dk-ctx")
    sc = V.seed_callables(3, 115, 0, 0)
    Ks, Kv, Kj = 80, 100, 40
    kw = dict(parcel_ids=keep, traj=traj, seed_of=sc["seed_of"], g3_seed=sc["g3_seed"], K_sets=Ks, K_surr=Kv,
              K_j1_sets=Kj, two_sided=False, registered_direction=1)
    b_S = (c2.X[:, S] @ w) / w.sum()
    T_S = float(stats.spearmanr(yk, b_S).statistic)
    inside, outside = "%.3f" % (T_S + 0.03), "%.3f" % (T_S - 0.08)
    rec = FM.signed_weight_descriptor(c2, yk, bk, genes, w_all, published=inside, **kw)
    ref_ad = FM.WeightedSetRho(c2, yk, S, w, b_S, parcel_ids=keep, observed_label="ref")
    ref = FM.signed_weight_gene_legs(ref_ad, sc["seed_of"], sc["g3_seed"], K_sets=Ks, K_surr=Kv, K_j1_sets=Kj,
                                     traj=traj, direction=1, two_sided=False)
    same = json.dumps(R.A3.jsonable(rec["gene_legs"]["legs"]), sort_keys=True) == \
        json.dumps(R.A3.jsonable(ref["legs"]), sort_keys=True) and \
        json.dumps(R.A3.jsonable(rec["gene_legs"]["J1"]), sort_keys=True) == json.dumps(R.A3.jsonable(ref["J1"]),
                                                                                       sort_keys=True)
    check("P15 R41: T_S = scipy Spearman rho(y, S's weighted score on the class matrix) (1e-12); the gene legs and J1 = "
          "the machinery on the class matrix with T_S as the observed map (identical records); basis hash = the class "
          "matrix's", abs(rec["T_S"] - T_S) < 1e-12 and same
          and rec["basis"]["matrix_sha256"] == FM.sw_basis_sha(c2) and rec["basis_check"]["ok"], f"T_S {T_S:+.4f}")
    check("P15 R41: the registered T (rho with the paper's map) is reported beside T_S, as registered",
          abs(rec["registered_T"] - stats.spearmanr(yk, bk).statistic) < 1e-12 and rec["registered_T"] != rec["T_S"])
    check(f"P15 R41: T_S inside ±.05 of a planted published value ({inside}) -> the registered outcome is answered "
          "(the Level-2 and J1 p's of T_S's legs)", rec["reproduction"]["label"] == "reproduced"
          and rec["registered_outcome"]["status"] == FM.SW_ANSWERED
          and rec["registered_outcome"]["level2"]["p_reported"] == rec["gene_legs"]["level2"]["p_reported"]
          and rec["registered_outcome"]["J1"]["p_reported"] == rec["gene_legs"]["J1"]["p_reported"])
    rec_o = FM.signed_weight_descriptor(c2, yk, bk, genes, w_all, published=outside, **kw)
    check(f"P15 R41: T_S outside ±.05 of a planted published value ({outside}) -> '{FM.SW_NOT_ANSWERED}', the legs "
          "still reported", rec_o["registered_outcome"]["status"] == FM.SW_NOT_ANSWERED
          and rec_o["reproduction"]["label"].startswith("not reproduced")
          and json.dumps(R.A3.jsonable(rec_o["gene_legs"]["legs"]), sort_keys=True)
          == json.dumps(R.A3.jsonable(rec["gene_legs"]["legs"]), sort_keys=True))
    rec_n = FM.signed_weight_descriptor(c2, yk, bk, genes, w_all, published=None, **kw)
    check("P15 R41: no ±.05 comparator for T_S (a source-defect / rebuilt / figure-only cell) -> not answered",
          rec_n["registered_outcome"]["status"] == FM.SW_NOT_ANSWERED and rec_n["reproduction"] is None)
    # (ii) + (a): the authors' matrix with a planted gene-wise offset (a per-gene multiple of one parcel pattern), the
    # null maps built on it and compared with rho(y, the paper's map) -> fails the basis check
    rng = np.random.default_rng(4141)
    u = rng.standard_normal(c2.n)
    off = rng.normal(0.0, 2.0, c2.G)
    ctx_auth = R.A3.ClassContext(c2.name, pd.DataFrame(c2.X + np.outer(u, off), index=c2.parcel_ids,
                                                       columns=list(c2.U.genes)),
                                 c2.classes, c2.xyz, c2.info, c2.brain_fn, c2.atlas)
    ad_v = FM.WeightedSetRho(ctx_auth, yk, S, w, bk, parcel_ids=keep, observed_label="variant (ii) + (a)")
    variant = dict(basis=dict(matrix_sha256=FM.sw_basis_sha(ctx_auth)), T_S=float(ad_v.T_obs))
    v_chk = FM.sw_basis_check(variant, c2, yk, S, w)
    maps_c = ref_ad.maps(np.atleast_2d(np.arange(S.size) + 40))
    maps_a = ad_v.maps(np.atleast_2d(np.arange(S.size) + 40))
    check("P15 R41 must-fail: the (ii) + (a) variant (authors' matrix with a gene-wise offset; T = rho with the paper's "
          "map) fails the basis check (hash and T_S); its null maps differ in rank",
          not v_chk["ok"] and not any(v_chk["checks"].values())
          and stats.spearmanr(maps_c[0], maps_a[0]).statistic < 1 - 1e-9 and FM.sw_basis_check(rec, c2, yk, S, w)["ok"])
    # sum w = 0
    w0 = np.array([1.25, -1.25] * 12 + [0.0])          # signed weights summing to exactly 0
    rec_0 = FM.signed_weight_descriptor(c2, yk, bk, genes, w0, published=inside, **kw) \
        if math.fsum(w0.tolist()) == 0.0 else None
    check(f"P15 R41: sum w = 0 -> the gene legs read '{FM.SW_ZERO_SUM}', the outcome not answered",
          rec_0 is not None and rec_0["gene_legs"]["status"] == FM.SW_ZERO_SUM and rec_0["T_S"] is None
          and rec_0["registered_outcome"]["status"] == FM.SW_NOT_ANSWERED)
    # U-F1 pinned by R41: the orders are drawn after the sets; a variant drawing them before is caught
    ad = ref_ad
    lg = FM.sw_uniform_leg(ad, Ks, np.random.default_rng(sc["seed_of"]("G1")), pool=np.arange(c2.G),
                           name="Level-2 G1", seed_leg=2, return_draws=True)
    g = np.random.default_rng(sc["seed_of"]("G1"))
    rep = np.stack([g.choice(np.setdiff1d(np.arange(c2.G), S), size=S.size, replace=False) for _ in range(Ks)])
    gb = np.random.default_rng(sc["seed_of"]("G1"))
    _ = [gb.permutation(S.size) for _ in range(Ks)]    # the variant: orders first
    rep_b = np.stack([gb.choice(np.setdiff1d(np.arange(c2.G), S), size=S.size, replace=False) for _ in range(Ks)])
    check("P15 R41 (U-F1): the sets equal the unweighted sampler's from the leg's key (orders drawn after them); the "
          "orders-first variant draws other sets (caught)",
          np.array_equal(lg["_draws"]["sets"], rep) and not np.array_equal(rep_b, rep))
    # the comparators R41 reads from the TSV
    rows = R.register_for_diagnostics(REPO)
    sw_rows = list(range(103, 118)) + list(range(120, 132))   # the signed-weight route (RUN_PLAN §4; run.py U9)
    got = {r: FM.sw_published_rho(r, rows[r - 1]["reproduction"]) for r in sw_rows}
    want = {103: "-0.150", 105: "0.413", 107: "-0.053", 115: ".531", 116: ".547", 117: ".529"}
    check("P15 R41: the ±.05 comparators of the signed-weight rows (103-117, 120-131): 103 / 105 / 107; MDD 115-117 = "
          "R41's .531 / .547 / .529; none elsewhere", {k: v for k, v in got.items() if v is not None} == want)
    check("P15 R41: a TSV comparator differing from R41's MDD pin is refused",
          raises(lambda: FM.sw_published_rho(115, "... on our matrix vs .530 (±.05); beside it ..."), ValueError, "R41"))
    check("P15 R41: the production descriptor pass no longer raises (SW_GENE_LEGS_UNPINNED and its guard are gone)",
          not hasattr(FM, "require_sw_gene_legs_pinned") and not hasattr(FM, "SW_GENE_LEGS_UNPINNED"))


# ================================================================================================================
# Part P16
# ================================================================================================================
def liu_plan(cell: str) -> dict:
    return dict(row=LIU_ROWS[cell], liu_spec=dict(FM.LIU_SPECS[cell], cell_id=cell), form_name="liu",
                analysis_class="none")


# the synthetic SD7 label column's DK ids, read by hand from forms.SYN_SD7_LABELS and forms.SYN_DK_TABLE (independent
# of forms.sd7_normalise): hemisphere-split, so not pooled; the ventricles and the three global rows dropped
SYN_SD7_CORTICAL = (1, 4, 6, 10, 12, 42, 45, 47, 51, 53)
SYN_SD7_HIP = (40, 81)
SYN_SD7_OTHER_SUB = (35, 76, 36, 77)


def indep_prepare(spec, inputs) -> dict:
    """An independent rebuild of R10 / R42's inputs: the scale (log2(RPKM + 1) for BrainSpan), duplicate symbols
    averaged per sample (a plain loop), the samples used and their groups (labels from the hand-read DK ids above)."""
    X = inputs["expr"].to_numpy(float)
    cols = [str(c) for c in inputs["expr"].columns]
    if spec["data"] == "brainspan":
        with np.errstate(invalid="ignore"):
            X = np.log2(X + 1.0)
    pos: dict = {}
    for j, g in enumerate(cols):
        pos.setdefault(g, []).append(j)
    genes = list(pos)
    Xd = np.column_stack([X[:, pos[g]].sum(axis=1) / len(pos[g]) for g in genes])
    n_dup = sum(1 for v in pos.values() if len(v) > 1)
    meta = inputs["meta"]
    grp = {}
    for i in range(len(meta)):
        if spec["kind"] == "two-group":
            if spec["by"] == "age":
                a = str(meta["age"].iloc[i])
                c = "prenatal" if a.endswith("pcw") else "postnatal"
            else:
                c = str(meta["structure_acronym"].iloc[i])
            g = "a" if c in spec["a"] else ("b" if c in spec["b"] else None)
        else:
            lb = meta["label"].iloc[i]
            if lb is None or (isinstance(lb, float) and math.isnan(lb)):
                g = None
            elif spec["kind"] == "label-mean":
                g = int(lb) if int(lb) in SYN_SD7_CORTICAL else None
            else:
                g = int(lb) if int(lb) in SYN_SD7_CORTICAL + SYN_SD7_HIP + SYN_SD7_OTHER_SUB else None
        if g is not None:
            grp[i] = g
    return dict(X=Xd, genes=genes, n_dup=n_dup, used=sorted(grp), grp=grp)


def part_p16(scratch: Path) -> None:
    print(SEP + "\nPart P16: gene-set-only (R10; RUN_PLAN P16 :1143; RUN_PLAN_amend_2 R42), synthetic per-sample frames")
    K = 120
    for cell, row in LIU_ROWS.items():
        plan = liu_plan(cell)
        spec = plan["liu_spec"]
        inputs = FM.synthetic_liu_inputs(SRC16, plan)
        ids = FM.synthetic_liu_ids(SRC16, plan)
        sc = V.seed_callables(10, row, 0, 0)
        two_sided = cell in ("LIU-T2-STR", "LIU-T2-CBC", "LIU-T2-HIP")
        reg = None if two_sided else (-1 if cell == "LIU-T2" else 1)
        rec = FM.liu_compute(spec, inputs, K=K, seed_of=sc["seed_of"], g3_seed=sc["g3_seed"], two_sided=two_sided,
                             registered_direction=reg, return_detail=True)
        det = rec.pop("_detail")
        pp, draws = det["prepared"], det["draws"]
        tag = f"[{cell}]"
        ip = indep_prepare(spec, inputs)
        used, grp = ip["used"], ip["grp"]
        # R42 (a) / (b): scale and duplicates
        if spec["data"] == "brainspan":
            check(f"P16 {tag}: R42 (a) the RPKM source is used on log2(RPKM + 1); duplicate symbols averaged per sample "
                  f"and counted ({ip['n_dup']} symbols)",
                  rec["U_stat"]["scale"]["scale_used"] == "log2(RPKM+1)" and ip["n_dup"] == 2
                  and rec["U_stat"]["duplicates"]["n_duplicate_symbols"] == 2
                  and rec["U_stat"]["duplicates"]["n_duplicate_columns_merged"] == 4)
        else:
            check(f"P16 {tag}: R42 (a) the AHBA source is used as abagen returns it; no duplicate symbol",
                  rec["U_stat"]["scale"]["scale_used"].startswith("abagen")
                  and rec["U_stat"]["duplicates"]["n_duplicate_symbols"] == 0)
        X = ip["X"][used]
        fin = np.isfinite(X).all(0)
        sd = X[:, fin].std(0, ddof=1)
        n_const = int((sd <= 1e-12).sum())
        check(f"P16 {tag}: samples used = the samples T averages over (R42 (c)); U_stat drops non-finite "
              f"({int((~fin).sum())}) and constant ({n_const}) columns over them, counts recorded",
              list(pp["used_positions"]) == used and rec["U_stat"]["n_dropped_nonfinite"] == int((~fin).sum())
              and rec["U_stat"]["n_dropped_constant"] == n_const == 2
              and rec["U_stat"]["n_U_stat"] == int(fin.sum()) - n_const)
        genes = np.asarray(ip["genes"])[fin][sd > 1e-12]
        Xs = X[:, fin][:, sd > 1e-12]
        gi = {g: k for k, g in enumerate(genes)}
        Sg = [g for g in dict.fromkeys(inputs["set"]) if g in gi]
        Sidx = np.array([gi[g] for g in Sg])
        G, m = len(genes), len(Sidx)
        check(f"P16 {tag}: S = merged set ∩ U_stat ({m} of {len(dict.fromkeys(inputs['set']))}: 2 absent from the data, "
              "the dropped columns' members excluded)",
              list(pp["U"].genes) == list(genes) and np.array_equal(pp["S"], Sidx) and rec["set"]["m"] == m
              and rec["set"]["n_absent_from_data"] == 2)
        inS = np.zeros(G, bool)
        inS[Sidx] = True
        r_sc = np.array([2 * stats.mannwhitneyu(Xs[k, inS], Xs[k, ~inS]).statistic / (m * (G - m)) - 1
                         for k in range(Xs.shape[0])])
        check(f"P16 {tag}: per-sample rank-biserial r = scipy Mann-Whitney U form (ties included; 1e-12)",
              float(np.max(np.abs(r_sc - pp["per_sample_r"]))) <= 1e-12
              and rec["per_sample_r"]["values"] == [float(v) for v in pp["per_sample_r"]])
        Cs = [int_centred_ranks(Xs[k]) for k in range(Xs.shape[0])]
        groups = {}
        for k, i in enumerate(used):
            groups.setdefault(grp[i], []).append(k)

        def T_frac(idx):
            r = [Fraction(sum(Cs[k][j] for j in idx), m * (G - m)) for k in range(len(Cs))]
            mean = {g: sum(r[k] for k in ks) / len(ks) for g, ks in groups.items()}
            if spec["kind"] == "two-group":
                return mean["a"] - mean["b"]
            if spec["kind"] == "label-mean":
                return sum(mean.values()) / len(mean)
            hip = [mean[h] for h in SYN_SD7_HIP]
            oth = [v for g, v in mean.items() if g not in SYN_SD7_HIP]
            return sum(hip) / len(hip) - sum(oth) / len(oth)
        T0 = T_frac(Sidx)
        check(f"P16 {tag}: T = an independent Fraction computation from scipy ranks (exact; {float(T0):+.5f})"
              + ("; unpooled T5: r(hippocampus) = the mean of the two hippocampus labels' values (R42 (e))"
                 if spec["kind"] == "label-contrast" else ""),
              Fraction(rec["T_numerator"], rec["T_denominator"]) == T0 and rec["T"] == float(T0))
        if spec["kind"] != "two-group":
            ls = rec["labels"]["label_set"]
            want = sorted(g for g in groups)
            check(f"P16 {tag}: R42 (e) the label set = the listed DK labels with >= 1 sample (unpooled ids; "
                  f"{len(want)} labels; hippocampus {list(ls['hip'])})",
                  sorted(ls["keys"]) == want and ls["pooled"] is False
                  and list(ls["hip"]) == ([] if spec["kind"] == "label-mean" else list(SYN_SD7_HIP))
                  and rec["labels"]["sd7"]["n_dropped_latvent"] == 2 and rec["labels"]["sd7"]["n_dropped_global"] == 3)
        if spec["kind"] == "two-group":
            na, nb = len(groups["a"]), len(groups["b"])
            N = [sum(Cs[k][j] for j in Sidx) for k in range(len(Cs))]
            num = nb * sum(N[k] for k in groups["a"]) - na * sum(N[k] for k in groups["b"])
            check(f"P16 {tag}: the integer comparison is n_b sum N_a - n_a sum N_b over n_a n_b m (G - m)",
                  rec["T_numerator"] == num and rec["T_denominator"] == na * nb * m * (G - m))
        brain = {gi[g] for g in inputs["brain"] if g in gi}
        okd = True
        for name, leg in rec["legs"].items():
            if leg["status"] != "ok":
                okd = False
                continue
            sets = draws[name]
            within = all(len(set(s.tolist())) == m and not (set(s.tolist()) & set(Sidx.tolist()))
                         and max(s) < G for s in sets)
            if name in ("G3", "G4"):
                within &= all(set(s.tolist()) <= brain for s in sets)
            kp = km = 0
            for s in sets:
                v = T_frac(s)
                kp += v >= T0
                km += v <= T0
            okd &= within and leg["rank_rule"]["k_plus"] == kp and leg["rank_rule"]["k_minus"] == km \
                and leg["p"][1] == (kp + 1) / (len(sets) + 1) and leg["rank_rule"]["branch"] == AD.RANK_BRANCH_COMMON
        check(f"P16 {tag}: G1-G5 drawn on U_stat (size m, S excluded; G3 / G4 in brain>body ∩ U_stat); every leg's "
              "counts = an independent exact recomputation (integer branch)", okd,
              json.dumps({n: L["status"] for n, L in rec["legs"].items()}))
        Zc = np.corrcoef(Xs.T)

        def coex(Z, s):
            sub = Z[np.ix_(s, s)]
            return (sub.sum() - len(s)) / (len(s) * (len(s) - 1))
        cS = coex(Zc, Sidx)
        okc = all(abs(coex(Zc, s) - cS) <= 0.02 + 1e-12 for n in ("G2", "G4") if n in draws for s in draws[n])
        okt = abs(rec["legs"]["G2"]["target"] - cS) <= 1e-12
        diff_txt = ""
        if spec["data"] == "brainspan":   # R42 (b): a raw-RPKM coexpression is caught
            raw = inputs["expr"].to_numpy(float)
            rawd = np.column_stack([raw[:, [j for j, c in enumerate(inputs["expr"].columns) if str(c) == g]].mean(axis=1)
                                    for g in ip["genes"]])[used][:, fin][:, sd > 1e-12]
            cS_raw = coex(np.corrcoef(rawd.T), Sidx)
            okt &= abs(rec["legs"]["G2"]["target"] - cS_raw) > 1e-6
            diff_txt = f"; raw-RPKM c_S {cS_raw:.4f} differs (caught)"
        check(f"P16 {tag}: G2 / G4 coexpression within S's +- .02, Pearson over the same samples on the log2 / abagen "
              "scale (np.corrcoef; R42 (b))", okc and okt and "G2" in draws and "G4" in draws,
              f"c_S {cS:.4f}{diff_txt}")
        g = np.random.default_rng(SD.g3_seed(10, row, 0, 0))
        pool = np.setdiff1d(np.array(sorted(brain)), Sidx)
        rep = np.stack([g.choice(pool, size=m, replace=False) for _ in range(K)])
        g3l = np.random.default_rng(SD.claim_seed(10, row, 3, 0, 0))
        rep3 = np.stack([g3l.choice(pool, size=m, replace=False) for _ in range(K)])
        check(f"P16 {tag}: G3 on R24's stream (replayed; not leg 3's)",
              np.array_equal(draws["G3"], rep) and not np.array_equal(draws["G3"], rep3))
        l2 = rec["level2"]
        check(f"P16 {tag}: G5 carries the register's label; Level-2 p = max over G1-G5; reading 'no calibrated test'",
              rec["legs"]["G5"]["label"] == "matching variable = tested quantity; expected null by construction"
              and l2.get("p") is not None
              and all(l2["p"][d] == max(rec["legs"][n]["p"][d] for n in DS.LEVEL2_LEGS) for d in (1, -1))
              and rec["reading"].startswith("no calibrated test"))
        text = json.dumps(R.A3.jsonable(rec))
        check(f"P16 {tag}: no planted sample id in the record ({len(ids)} ids searched)",
              not any(i in text for i in ids) and "SYNSID" not in text)
    part_p16_sd7()
    # refusals
    plan = liu_plan("LIU-T1")
    spec = plan["liu_spec"]
    base = FM.synthetic_liu_inputs(SRC16, plan)
    ids = FM.synthetic_liu_ids(SRC16, plan)
    bad = dict(base, meta=base["meta"].assign(donor_name=ids))
    check("P16 refusal: a metadata column outside the declared ones (an identifier column) is refused",
          raises(lambda: FM.liu_prepare(spec, bad), ValueError, "declared columns"))
    bad = dict(base, meta=base["meta"].iloc[::-1])
    msg = ""
    try:
        FM.liu_prepare(spec, bad)
    except ValueError as e:
        msg = str(e)
    check("P16 refusal: a metadata index not aligned with the matrix is refused; the message names no id",
          "index mismatch" in msg and not any(i in msg for i in ids))
    m2 = base["meta"].copy()
    m2.iloc[0, m2.columns.get_loc("age")] = "8 weeks"
    check("P16 refusal: an age form other than pcw / mos / yrs is refused (position only)",
          raises(lambda: FM.liu_prepare(spec, dict(base, meta=m2)), ValueError, "sample position 0"))
    check("P16 refusal (R42 (a)): a source without a declared scale, or with another one, is refused",
          raises(lambda: FM.liu_prepare(spec, {k: v for k, v in base.items() if k != "scale"}), ValueError, "scale")
          and raises(lambda: FM.liu_prepare(spec, dict(base, scale="abagen")), ValueError, "scale"))
    e2 = base["expr"].copy()
    e2.iloc[3, 20] = -2.0
    check("P16 refusal (R42 (a)): a negative RPKM value is refused (log2(RPKM + 1) needs RPKM >= 0)",
          raises(lambda: FM.liu_prepare(spec, dict(base, expr=e2)), ValueError, "negative RPKM"))
    check("P16 refusal: a set with < 5 columns in U_stat reads 'not testable (< 5)'",
          raises(lambda: FM.liu_prepare(spec, dict(base, set=base["set"][:4])), FM.FormNotTestable, "not testable"))
    check("P16: the readings WP2 left unpinned are gone (R42 pins duplicates and the T5 hippocampus rule)",
          not hasattr(FM, "LIU_DUPLICATE_UNPINNED") and not hasattr(FM, "LIU_T5_HIP_UNPINNED"))


def _fails(fn, status):
    try:
        fn()
    except FM.FormNotTestable as e:
        return e.status == status, e.detail
    return False, None


def part_p16_sd7() -> None:
    """RUN_PLAN_amend_2 R42 (d) / (e): SD7's label formats on the synthetic DK table (abagen ids and names)."""
    dk = FM.synthetic_dk_table()
    rec = set(dk["label"]) | set(FM.SD7_ALIASES) | {"latvent", "icv", "thickness", "surfarea"}
    P = FM.sd7_label_parse
    forms = {"L_bankssts": ("bankssts", ["L"]), "Lhippo": ("hippocampus", ["L"]),
             "L_bankssts_thickavg": ("bankssts", ["L"]), "ctx-lh-bankssts": ("bankssts", ["L"]),
             "R_Lingual_SurfAvg": ("lingual", ["R"]), "Right-Hippocampus": ("hippocampus", ["R"]),
             "LLatVent": ("latvent", ["L"]), "L_thickavg": ("", ["L"]), "ICV": ("icv", []),
             "LThickness": ("thickness", ["L"]), "RSurfArea": ("surfarea", ["R"]),
             "lateraloccipital": ("lateraloccipital", []), "Left-Lateral-Ventricle": ("lateralventricle", ["L"]),
             "bankssts": ("bankssts", []), "Rthal": ("thalamusproper", ["R"])}
    got = {lb: P(lb, rec) for lb in forms}
    bad = [lb for lb, (nm, sd) in forms.items() if (got[lb]["name"], got[lb]["sides"]) != (nm, sd)]
    check("P16 SD7 (R42 (d)): label formats normalised - markers in any token or glued (Lhippo, LLatVent, "
          "LThickness), suffixes stripped, 'ctx' dropped, case-folded, the alias table; 'lateraloccipital' not split; "
          "'Left-Lateral-Ventricle' -> 'lateralventricle'", not bad, f"{len(forms) - len(bad)} / {len(forms)}")
    a = FM.sd7_normalise(["L_bankssts", "Rhippo", "L_cuneus_thickavg", "ctx-rh-fusiform", "Lhippo", "LLatVent",
                          "RLatVent", "L_thickavg", "ICV", "RSurfArea"], dk)
    ids = [e["ids"] for e in a["entries"] if e["kind"] == "matched"]
    check("P16 SD7: L / R markers select the left / right DK ids; ventricles and global measures dropped and counted; "
          "hemisphere-split -> not pooled", ids == [[1], [81], [4], [47], [40]] and a["n_dropped_latvent"] == 2
          and a["n_dropped_global"] == 3 and a["merged"] is False and a["pooled"] is False and a["n_matched"] == 5)
    b = FM.sd7_normalise(["bankssts", "hippocampus", "lateraloccipital", "ICV"], dk)
    check("P16 SD7: merged labels (no marker anywhere) -> pooled by DK name; an unmarked name stands for every DK label "
          "of that name", b["merged"] is True and b["pooled"] is True
          and [e["ids"] for e in b["entries"] if e["kind"] == "matched"] == [[1, 42], [40, 81], [10, 51]])
    for name, labels, key in (("Left-Lateral-Ventricle", ["L_bankssts", "Left-Lateral-Ventricle"], "n_unmatched"),
                              ("another unmatched label", ["L_bankssts", "L_superfrontalx"], "n_unmatched"),
                              ("two labels on one DK label", ["L_bankssts", "ctx-lh-bankssts"], "n_collisions"),
                              ("an unmarked bilateral name in a split table", ["L_bankssts", "cuneus"],
                               "n_multi_label")):
        ok, detail = _fails(lambda: FM.sd7_normalise(labels, dk), FM.SD7_UNMATCHED)
        check(f"P16 SD7: {name} -> fail closed '{FM.SD7_UNMATCHED}' with the count",
              ok and detail is not None and detail.get(key) == 1, json.dumps(detail))
    # pooled T4 / T5 through liu_prepare (merged SD7): keys are DK names; unpooled ones are ids (the main loop)
    for cell in ("LIU-T4", "LIU-T5"):
        plan = liu_plan(cell)
        inp = FM.synthetic_liu_inputs(SRC16, plan)
        merged = ["bankssts", "cuneus", "fusiform", "lateraloccipital", "lingual", "thalamusproper", "caudate",
                  "hippocampus", "ICV"]
        pp = FM.liu_prepare(plan["liu_spec"], dict(inp, sd7_labels=merged))
        ls = pp["labels"]["label_set"]
        want = (["bankssts", "cuneus", "fusiform", "lateraloccipital", "lingual"] if cell == "LIU-T4" else
                ["hippocampus", "bankssts", "caudate", "cuneus", "fusiform", "lateraloccipital", "lingual",
                 "thalamusproper"])
        n_hip = sum(1 for r in FM.SYN_DK_TABLE if r[1] == "hippocampus")
        check(f"P16 SD7 [{cell}]: merged SD7 -> pooled by DK name (both hemispheres' samples in one label); label set "
              "= the listed names with samples" + ("; one hippocampus label" if cell == "LIU-T5" else ""),
              ls["pooled"] is True and list(ls["keys"]) == want
              and (cell == "LIU-T4" or (ls["hip"] == ["hippocampus"] and n_hip == 2)))
    # T4 with zero matched cortical labels; T5 without a hippocampus label
    p4, p5 = liu_plan("LIU-T4"), liu_plan("LIU-T5")
    i4, i5 = FM.synthetic_liu_inputs(SRC16, p4), FM.synthetic_liu_inputs(SRC16, p5)
    ok4, d4 = _fails(lambda: FM.liu_prepare(p4["liu_spec"], dict(i4, sd7_labels=["Lhippo", "Rhippo", "Lthal"])),
                     FM.LIU_T4_NO_CORTICAL)
    check(f"P16 SD7: a T4 with zero matched cortical labels fails closed ('{FM.LIU_T4_NO_CORTICAL}')", ok4,
          json.dumps(d4))
    ok5, d5 = _fails(lambda: FM.liu_prepare(p5["liu_spec"], dict(i5, sd7_labels=["Lthal", "Rthal", "L_bankssts"])),
                     FM.LIU_T5_NO_HIP)
    check(f"P16 SD7: a T5 without a hippocampus label reads '{FM.LIU_T5_NO_HIP}'", ok5, json.dumps(d5))
    # liu_label_T: the one function for our values and SD7's
    ls = dict(keys=[40, 81, 35, 76], hip=[40, 81], pooled=False)
    T = FM.liu_label_T({40: 0.3, 81: 0.1, 35: 0.05, 76: -0.15}, dict(kind="label-contrast"), ls)
    sd7_labels = ["Lhippo", "Rhippo", "Lthal", "Rthal", "LLatVent"]
    s7 = FM.liu_sd7_T(dict(kind="label-contrast"), sd7_labels, [0.3, 0.1, 0.05, -0.15, 9.9], dk, ls)
    check("P16 SD7 (R42 (e)): unpooled T5 = mean of the two hippocampus values - mean of the others (.2 - (-.05)); the "
          "same function on SD7's values (the ventricle's value unused)", abs(T - 0.25) < 1e-15 and abs(s7["T"] - T) < 1e-15
          and s7["n_values"] == 4)


# ================================================================================================================
# Part R: R21 / R28
# ================================================================================================================
def part_r(scratch: Path) -> None:
    print(SEP + "\nPart R: R21 (MOR-T) and R28 (BENK-C2 / PARK-C5) value checks; the RLM (P17's R28 item)")
    rows = R.register_for_diagnostics(REPO)
    exp = {618: (1, FM.R21_LABEL), 619: (1, FM.R21_LABEL), 518: (-1, FM.R28_LABEL), 519: (-1, FM.R28_LABEL),
           603: (1, FM.R28_LABEL)}
    for r, (d, lab) in exp.items():
        p = R.classify(rows[r - 1], frozenset({"G1"}))
        note = R.ROUTE_NOTE_R21 if r in (618, 619) else R.ROUTE_NOTE_R28
        check(f"R route row {r} ({p['cell_id']}): decoded-list compute, one-sided {d:+d}, no T_abs, label "
              f"{'R21' if r > 600 and r != 603 else 'R28'}",
              p["kind"] == "compute" and p["form"] == "decoded-list" and p["route"] == f"verdict: decoded-list ({note})"
              and p["two_sided"] is False and p["registered_direction"] == d and not p["t_abs"] and p["label"] == lab
              and p["descriptor"] and bool(p.get("rlm")) == (r not in (618, 619)), p["route"])
    check("R28 proxy direction: '− (' -> -1, '+ (' -> +1, absent -> None",
          FM.parse_proxy_direction(rows[517]["direction"]) == -1 and FM.parse_proxy_direction(rows[602]["direction"]) == 1
          and FM.parse_proxy_direction("n/a: not testable as stated") is None)
    # the RLM
    inp = FM.synthetic_rlm_inputs(SRC17, dict(row=518))
    df = inp["genes"]
    rec = FM.rlm_record("BENK-C2-SD", inp)
    import statsmodels.api as sm
    okv = True
    for dis in ("ASD", "SCZ", "BD"):
        cols = ["t", f"{dis}.log2FC", "percentage_gene_gc_content"]
        sub = df[cols].to_numpy(float)
        ok = np.isfinite(sub).all(1)
        res = sm.RLM(sub[ok, 0], np.column_stack([sub[ok, 1], sub[ok, 2], np.ones(int(ok.sum()))]),
                     M=sm.robust.norms.HuberT()).fit(scale_est="mad")
        dr = FM.irls_huber_direct(sub[ok, 0], np.column_stack([sub[ok, 1], sub[ok, 2], np.ones(int(ok.sum()))]))
        r_ = rec["per_disorder"][dis]
        okv &= (abs(r_["t_log2fc"] - float(res.tvalues[0])) <= 1e-12 * max(1, abs(float(res.tvalues[0])))
                and abs(dr["tvalues"][0] - float(res.tvalues[0])) <= 1e-10 * max(1, abs(float(res.tvalues[0])))
                and np.max(np.abs(dr["params"] - res.params)) <= 1e-10 and r_["n_dropped_nonfinite"] == int((~ok).sum())
                and r_["n_used"] == int(ok.sum()) and r_["published"] == FM.R28_PUBLISHED["BENK-C2-SD"][dis])
    check("R28 RLM: t of log2FC = statsmodels RLM (HuberT, MAD) = a direct IRLS Huber fit (1e-10); NaN rows dropped and "
          "counted; the published values beside", okv,
          json.dumps({k: round(v["t_log2fc"], 4) for k, v in rec["per_disorder"].items()}))
    ols = sm.OLS(df["t"], sm.add_constant(df[["ASD.log2FC", "percentage_gene_gc_content"]]), missing="drop").fit()
    check("R28 RLM differs from OLS on heavy-tailed noise (the robust fit is in use)",
          abs(rec["per_disorder"]["ASD"]["t_log2fc"] - float(ols.tvalues["ASD.log2FC"])) > 1e-3)
    orig = FM.irls_huber_direct
    try:
        FM.irls_huber_direct = lambda e, x, **k: orig(e, x, t=2.0)
        caught = raises(lambda: FM.rlm_record("BENK-C2-SD", inp), R.AD.FunctionalDefect, "P17")
    finally:
        FM.irls_huber_direct = orig
    check("R28 must-fail: a direct fit with another Huber constant (2.0) is caught by rlm_t's P17 assertion", caught)
    check("R28 RLM refuses a gene table with other columns",
          raises(lambda: FM.rlm_record("PARK-C5", dict(genes=df.assign(gene_name="x"))), ValueError, "exactly"))


# ================================================================================================================
# Part D: the dispatcher
# ================================================================================================================
def part_d(scratch: Path) -> None:
    print(SEP + "\nPart D: the dispatcher over all 692 TSV rows (dry): the WP2 routes")
    rows = R.register_for_diagnostics(REPO)
    views = {"gates closed": (frozenset(), False), "G2 open": (frozenset({"G2"}), False),
             "G1 open": (frozenset({"G1"}), False), "plant view": (frozenset(), True)}
    allc = {}
    for name, (og, pv) in views.items():
        try:
            recs = R.dry_dispatch(rows, og, plant_view=pv, sources=R.RealSources())
            exc = None
        except Exception as e:  # noqa: BLE001
            recs, exc = [], f"{type(e).__name__}: {e}"
        c = R.dispatch_counts(recs)
        allc[name] = c
        check(f"D {name}: 692 rows dispatched, no exception, no stub left", exc is None and len(recs) == 692
              and not any(r["outcome"] == "stub" for r in recs), exc or json.dumps(c["by_outcome"]))
    g2, g1, cl, pl = allc["G2 open"], allc["G1 open"], allc["gates closed"], allc["plant view"]
    check("D G2 open: the signed-weight route holds 27 rows (103-117 by status, 120-131 by T)",
          g2["by_route"].get(R.ROUTE_FORM["signed-weight"]) == 27)
    sw = [r.row for r in rows if R.classify(r, frozenset({"G2"}))["route"] == R.ROUTE_FORM["signed-weight"]]
    check("D the signed-weight route = TSV rows 103-117 and 120-131", sw == list(range(103, 118)) + list(range(120, 132)))
    check("D gene-set-only route = TSV rows 471-477 (ungated)",
          [r.row for r in rows if R.classify(r)["route"] == R.ROUTE_FORM["liu"]] == list(range(471, 478))
          and cl["by_route"].get(R.ROUTE_FORM["liu"]) == 7)
    check("D MOR-T (R21) route = rows 618, 619; BENK / PARK (R28) = 518, 519, 603 under G1",
          cl["by_route"].get(f"verdict: decoded-list ({R.ROUTE_NOTE_R21})") == 2
          and g1["by_route"].get(f"verdict: decoded-list ({R.ROUTE_NOTE_R28})") == 3)
    check("D plant view, real sources: every WP2 row reads 'not run (WP3 loader pending)'",
          pl["by_outcome"].get("would compute", 0) == 0 and pl["by_outcome"].get("stub", 0) == 0)
    src = R.SyntheticSources(15, scratch / "_no_data_d")
    recs = R.dry_dispatch([rows[r - 1] for r in (*SW_ROWS, *LIU_ROWS.values(), *R_ROWS)], frozenset(), plant_view=True,
                          sources=src)
    check("D plant view, synthetic sources: every WP2 row 'would compute'",
          all(r["outcome"] == "would compute" for r in recs), json.dumps(R.dispatch_counts(recs)["by_outcome"]))


# ================================================================================================================
# Part CLI: the WP2 rows through the runner (dev plant runs; synthetic sources)
# ================================================================================================================
def cli(args: list[str], timeout: int = 3600) -> tuple[int, list[str], str]:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, "-X", "utf8", "-u", "-m", "a1_audit.run", *args], cwd=str(SRC),
                       capture_output=True, env=env, timeout=timeout)
    return r.returncode, r.stdout.decode("utf-8", "replace").splitlines(), r.stderr.decode("utf-8", "replace")


def head() -> str:
    return subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip()


CLI_CASE = 0   # the plant case of the dev runs (run.py B3: a plant other than P2 names its case)


def load(out: Path, pass_: str, row: int) -> dict:
    hits = sorted(out.rglob(f"ungated/{pass_}/row_{row:04d}.json"))
    if len(hits) != 1:
        raise FileNotFoundError(f"{len(hits)} result files for row {row}, pass {pass_}")
    return json.loads(hits[0].read_bytes().decode("utf-8"))


def run_passes(out: Path, plant: str, rows: str) -> dict:
    res = {}
    for pass_ in ("verdict", "descriptor", "sensitivity"):
        code, lines, err = cli(["--commit", head(), "--pass", pass_, "--gate", "none", "--rows", rows, "--plant", plant,
                                "--case", str(CLI_CASE), "--dev", "--out", str(out), "--jobs", "2", "--K", CLI_K])
        res[pass_] = (code, lines, err)
        check(f"CLI {plant} {pass_} (rows {rows}) exits 0", code == 0, (err.strip().splitlines() or [""])[-1][:200])
    return res


def part_cli(scratch: Path) -> None:
    print(SEP + "\nPart CLI: the WP2 rows through the runner (dev plant runs, synthetic sources, small K)")
    K = R.parse_K(CLI_K, True)
    src16, src17 = SynSrc(16, CLI_CASE), SynSrc(17, CLI_CASE)
    # --- P16: Liu rows; no sample id anywhere
    out = scratch / "cli_p16"
    res = run_passes(out, "P16", "471-477")
    ids = []
    for cell, row in LIU_ROWS.items():
        ids += FM.synthetic_liu_ids(src16, liu_plan(cell))
        v, dsc, sen = (load(out, p_, row) for p_ in ("verdict", "descriptor", "sensitivity"))
        plan = liu_plan(cell)
        cid = FM.SYN_LIU_CLASS_ID[plan["liu_spec"]["data"]]
        sc = V.plant_seed_callables(16, CLI_CASE, cid)   # WP2r: the plant case's keys (class word: the Liu data kind)
        two_sided = cell in ("LIU-T2-STR", "LIU-T2-CBC", "LIU-T2-HIP")
        reg = None if two_sided else (-1 if cell == "LIU-T2" else 1)
        ref = FM.liu_compute(plan["liu_spec"], FM.synthetic_liu_inputs(src16, plan), K=K["sets"], seed_of=sc["seed_of"],
                             g3_seed=sc["g3_seed"], two_sided=two_sided, registered_direction=reg)
        got = dsc.get("result") or {}
        same = got.get("T") == ref["T"] and all(
            (got["legs"][n].get("p") or {}).get(str(dd)) == (ref["legs"][n].get("p") or {}).get(dd)
            for n in DS.LEVEL2_LEGS for dd in (1, -1))
        sr = ((dsc.get("row_provenance") or {}).get("seeds") or {}).get("per_map", [{}])[0]
        plant_keys = (sr.get("keys") == "plant" and sr.get("plant_id") == 16 and sr.get("case") == CLI_CASE
                      and sr.get("class_id") == cid
                      and sr["G3"]["key"]["entropy"] == [20260925, 900, 16, CLI_CASE, cid, 3])
        check(f"CLI P16 row {row} ({cell}): descriptor pass computed = in-process liu_compute on the PLANT keys (WP2r; "
              f"class word {cid}); verdict / sensitivity passes write no statistic; status 'no calibrated test'",
              dsc["outcome"] == "computed" and same and plant_keys and v["outcome"] == "no statistic"
              and sen["outcome"] == "no statistic" and dsc["status_written"].startswith("no calibrated test"),
              f"{dsc['outcome']} / {v['outcome']} / {sen['outcome']}")
    blob = []
    for f in out.rglob("*"):
        if f.is_file():
            blob.append(f.read_bytes().decode("utf-8", "replace"))
            blob.append(f.name)
    for code, lines, err in res.values():
        blob += lines + [err]
    text = "\n".join(blob)
    check(f"CLI P16: no planted sample id in any output file, file name, stdout or stderr ({len(ids)} ids, "
          f"{sum(1 for f in out.rglob('*') if f.is_file())} files)", not any(i in text for i in ids)
          and "SYNSID" not in text)
    # --- P15: signed-weight rows (plant view: G2 taken as open)
    out = scratch / "cli_p15"
    run_passes(out, "P15", ",".join(map(str, SW_ROWS)))
    src = R.SyntheticSources(15, scratch / "_no_data_cli15", case=CLI_CASE)
    rows = R.register_for_diagnostics(REPO)
    for row in SW_ROWS:
        v, dsc, sen = (load(out, p_, row) for p_ in ("verdict", "descriptor", "sensitivity"))
        p = R.classify(rows[row - 1], plant_view=True)
        pc = sw_pieces(src, p["analysis_class"], row)
        cid = SD.plant_class_id(p["analysis_class"])
        sc = V.plant_seed_callables(15, CLI_CASE, cid)   # WP2r: the plant case's keys
        ref = FM.signed_weight_site(pc["ctx"], pc["y"], pc["b"], parcel_ids=pc["keep"], K=K["site"],
                                    seed_of=sc["seed_of"], two_sided=p["two_sided"],
                                    registered_direction=p["registered_direction"])
        got = v.get("result") or {}
        same = got.get("T") == ref["T"] and all(
            got["site"]["legs"][leg]["p"][str(dd)] == ref["site"]["legs"][leg]["p"][dd]
            for leg in ("S1c", "S2c") for dd in (1, -1))
        genes, w_all, _ = FM.synthetic_gene_weights(src, pc["plan"])
        refd = FM.signed_weight_descriptor(pc["ctx"], pc["y"], pc["b"], genes, w_all, parcel_ids=pc["keep"],
                                           traj=src.trajectories(p["analysis_class"])[0], seed_of=sc["seed_of"],
                                           g3_seed=sc["g3_seed"], K_sets=K["sets"], K_surr=K["surr"],
                                           K_j1_sets=K["j1_sets"], two_sided=p["two_sided"],
                                           registered_direction=p["registered_direction"],
                                           published=p.get("sw_published"))
        gd = dsc.get("result") or {}
        l2g = (gd.get("gene_legs") or {}).get("level2") or {}
        l2r = refd["gene_legs"].get("level2") or {}
        same_d = (gd.get("T_S") == refd["T_S"]
                  and all((l2g.get("p") or {}).get(str(dd)) == (l2r.get("p") or {}).get(dd) for dd in (1, -1))
                  and (gd.get("registered_outcome") or {}).get("status") == refd["registered_outcome"]["status"])
        srs = [((x.get("row_provenance") or {}).get("seeds") or {}).get("per_map", [{}])[0] for x in (v, dsc)]
        plant_keys = (all(s_.get("keys") == "plant" and s_.get("plant_id") == 15 and s_.get("class_id") == cid
                          for s_ in srs)
                      and srs[1]["J1"]["key"]["entropy"] == [20260925, 900, 15, CLI_CASE, cid, 14])
        check(f"CLI P15 row {row}: verdict pass = in-process signed_weight_site (T, S1c / S2c); descriptor pass = "
              f"in-process signed_weight_descriptor (T_S, Level-2, outcome '{refd['registered_outcome']['status']}'; "
              "RUN_PLAN_amend_2 R41); both on the PLANT keys (WP2r); sensitivity no statistic",
              v["outcome"] == "computed" and same and dsc["outcome"] == "computed" and same_d and plant_keys
              and sen["outcome"] == "no statistic", f"{v['outcome']} / {dsc['outcome']} / {sen['outcome']}")
    # --- R21 / R28 rows
    out = scratch / "cli_r"
    run_passes(out, "P17", ",".join(map(str, R_ROWS)))
    src = R.SyntheticSources(17, scratch / "_no_data_cli17", case=CLI_CASE)
    for row in R_ROWS:
        v, dsc = load(out, "verdict", row), load(out, "descriptor", row)
        p = R.resolve_class(R.classify(rows[row - 1], plant_view=True), src)
        pr = R.prepare(p, src, 0, "primary")
        Z = AD.zscore_genes(pr.ctx.X)
        yh = (pr.y - pr.y.mean()) / pr.y.std()
        T_direct = float(np.mean([Z[:, j] @ yh / pr.ctx.n for j in pr.S]))
        Tv = ((v.get("result") or {}).get("verdict") or {}).get("T")
        okT = Tv is not None and abs(Tv - T_direct) <= 1e-12 and abs(
            T_direct - np.mean([stats.pearsonr(pr.ctx.X[:, j], pr.y).statistic for j in pr.S])) < 1e-12
        rlm_files = sorted(out.rglob(f"row_{row:04d}_rlm.json"))
        if row in (618, 619):
            okx = not rlm_files and v["label"] == FM.R21_LABEL and v["descriptor"] is True
        else:
            rl = json.loads(rlm_files[0].read_bytes().decode("utf-8"))["rlm"] if len(rlm_files) == 1 else None
            ref = FM.rlm_record(p["cell_id"], FM.synthetic_rlm_inputs(src17, p))
            okx = rl is not None and rl["status"] == "computed" and v["label"] == FM.R28_LABEL and all(
                rl["per_disorder"][d_]["t_log2fc"] == ref["per_disorder"][d_]["t_log2fc"] for d_ in ("ASD", "SCZ", "BD"))
            okx &= "/verdict/" in rlm_files[0].as_posix()
        dres = (dsc.get("result") or {}).get("per_map", {}).get("0", {})
        okd = dsc["outcome"] == "computed" and "T_abs" not in dres and "J1" in dres and "naive_joint" in dres
        check(f"CLI R row {row} ({p['cell_id']}): T = direct mean per-gene Pearson r of S (1e-12); "
              f"{'R21 label, no RLM' if row in (618, 619) else 'R28 label; RLM file beside the row = in-process'}; "
              "descriptor legs, no T_abs", okT and okx and okd and v["route"] == p["route"],
              f"T {Tv} vs {T_direct}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", default=None)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--no-cli", action="store_true", help="skip the runner dev runs (Part CLI)")
    a = ap.parse_args()
    scratch = Path(a.scratch or tempfile.mkdtemp(prefix="a1_forms_")).resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    print("test_forms: scratch %s" % R.ascii_line(str(scratch)))
    parts = [part_p15, part_p15_r41, part_p16, part_r, part_d] + ([] if a.no_cli else [part_cli])
    for part in parts:
        try:
            part(scratch)
        except Exception as e:  # noqa: BLE001
            check(f"{part.__name__} raised", False, f"{type(e).__name__}: {e}")
            print(R.ascii_line(traceback.format_exc()))
    n_ok = sum(ok for _, ok in RESULTS)
    print(SEP + "\ntest_forms: %d / %d checks passed" % (n_ok, len(RESULTS)))
    if n_ok == len(RESULTS) and not a.keep:
        shutil.rmtree(scratch, ignore_errors=True)
    return 0 if n_ok == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
