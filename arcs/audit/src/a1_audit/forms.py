"""A1 special claim forms: the adapters behind the runner's four former WP2 stub routes (arcs/audit/RUN_PLAN.md v3.1
§4 dispatch :353-363, §7 P15 / P16 / P17, §18 WP2; RUN_PLAN_amend_1.md v2.1 R32 (b), R36; RUN_PLAN_amend_2.md v2.1
R41, R42; all FROZEN). Nothing here opens a real map, set, matrix, carrier or sample: every input arrives through the
runner's Sources interface (the real loaders are WP3 / WP5); the synthetic providers at the end serve plants only.

1. Signed-weight descriptor (Giacomel GIA-C01 ... C06, C19 ... C24, GIA-MDD-C1 / C5 / C10, TSV rows 103-117 by their
   status; the MDD-DEG descriptor cells 120-131 by their T column, run.py U9). Frozen text (claims_register.md:1469-1473):
   "Descriptors: the paper's weighted GEDAR map ρ with y (...), our class-stratified site leg on ρ, and G1–G5 and J1 with
   S's weights carried over (each null set receives S's weight vector in a random order)"; P15 (RUN_PLAN.md:1142).
   - Verdict pass (signed_weight_site): T = Spearman rho(y, b), b = the paper's weighted GEDAR map (a source); the
     class-stratified site leg S1c [0] / S2c [1] on rho, counted exactly (adapters.RankRho; R32 (b)); the site leg =
     max(p_S1c, p_S2c) per direction (prereg.md:130-131). This registered T and its site leg are reported as
     registered (R41 'Reporting').
   - Descriptor pass (signed_weight_descriptor; RUN_PLAN_amend_2 R41, reading (i) + (b)): on the analysis class's §3.1
     matrix (the class context restricted to the analysis parcels), S's weighted score b_S = sum_g w_g X[:, g] / sum w
     gives T_S = rho(y, b_S); G1 [2], G2 [11], G3 [R24], G4 [12], G5 [13], the Level-2 max and J1 [14] with S's weights
     carried over (WeightedSetRho with observed map b_S, signed_weight_gene_legs): each leg's frozen sampler draws its
     sets exactly as the unweighted leg does, then each set receives S's weight vector in a random order (order_sets,
     U-F1, pinned by R41); a set's map is sum_j w_j X[:, R_j] / sum_j w_j on THE SAME matrix; its rho with y is
     compared with T_S exactly (rank_corr_terms / rank_corr_counts, R32 (b)). J1's z is not a rank statistic (R32 (b)):
     descriptors.j1_core on the same matrix, with R32 (a) on its exact surrogate types. The record carries the basis
     matrix's hash (sw_basis_check recomputes T_S on the class matrix; the authors'-matrix variant fails it).
     sum w = 0 -> the gene legs read "not computable (S's weights sum to 0)".
   - The registered outcome (prereg.md:296-297, "does it survive G1-G5 and J1"): answered by T_S's legs ONLY IF T_S
     passes its §4.1 reproduction check (reporting.reproduction_check, R37) against the published rho of the row's TSV
     reproduction column (TSV 103 / 105 / 107; MDD 115-117 .531 / .547 / .529, asserted against R41's pins); otherwise
     "not answered (T_S not reproduced)", the legs still reported as descriptors. A row without a numeric ±.05
     comparator for T_S (the subcortical cells' documented source defect, the rebuilt and DEG cells) has no check T_S
     can pass, so it reads "not answered (T_S not reproduced)" too.
2. Gene-set-only (Liu LIU-T1, T2, T4, T5 and the descriptor cells T2-STR / -CBC / -HIP; TSV rows 471-477; R10
   RUN_PLAN.md:628-660; P16 :1143; RUN_PLAN_amend_2 R42). liu_prepare + liu_compute:
   - Scale (R42 (a), (b)): BrainSpan values on log2(RPKM + 1) (an 'RPKM' source is transformed here; a
     'log2(RPKM+1)' source is used as given); AHBA values as abagen returns them ('abagen'). Any other scale is refused.
   - Duplicate symbols (R42 (a)): columns sharing a symbol (after the loader's HGNC mapping) are averaged per sample on
     that scale, before U_stat's rule, and counted.
   - U_stat = the data's genes restricted to the columns finite and non-constant over the samples used (the engine's
     Universe rule); both drop counts recorded. S = the merged set ∩ U_stat (< 5 -> "not testable (< 5)"). The
     coexpression (G2 / G4 / G5) is Pearson over the samples used, on the same scale (R42 (b)).
   - Samples used (R42 (c), U-F3 confirmed): T1 every sample aged in pcw / mos / yrs; the T2 family the two structure
     groups; T4 the cortical labels' samples; T5 the hippocampus label(s)' and the other labels' samples.
   - T4 / T5 labels (R42 (d), (e)): SD7's label column (a source, read through §8's wrapper before any value) is
     normalised by sd7_normalise (case-fold; '_thickavg' / '_surfavg' stripped; split on non-alphanumerics, 'ctx'
     dropped; marker tokens l / r / lh / rh / left / right anywhere; a glued l / r marker; the alias table; the abagen DK
     names); lateral ventricles and global measures dropped and counted; an unmatched label, a label on more than one DK
     label, or two labels on one DK label -> "not auditable (definition not applicable: SD7 labels unmatched)" with the
     counts. Pooled by DK name iff no SD7 label carries a marker (R10's binary rule). The label set: the DK labels
     (pooled or not) with >= 1 sample that SD7 lists; T4 its cortical labels (none -> "not auditable (definition not
     applicable: no SD7 cortical label matched)"); T5 r(hippocampus) = the mean of the hippocampus labels' values
     minus the mean of every other label's value (no hippocampus label with a sample -> "not computable (no
     hippocampus label)"). liu_label_T is the one function applied to our values and to SD7's (liu_sd7_T).
   - Per sample: the rank-biserial r of S against the rest, r = sum_{g in S} (2R_g - (G + 1)) / (m (G - m)), ranks
     average (doubled, so integers), ties exact (RUN_PLAN_amend_1 R32 (b)). A label's value is the mean over its samples
     (T4 / T5, R10 :656).
   - Every registered T is linear in the per-sample numerators, so T(R) = sum_{g in R} a_g / D with Python-int a_g and a
     D common to every set of size m: T1 / T2 (two groups A, B) a_g = n_B sum_{s in A} C_sg - n_A sum_{s in B} C_sg,
     D = n_A n_B m (G - m) (the comparison n_post sum N_pre - n_pre sum N_post); T4 D = L Λ m (G - m) and T5
     D = H L_o Λ m (G - m) (H hippocampus labels, L_o other labels) with Λ the lcm of the label sample counts. Every
     null comparison is of Python integers (adapters.rational_counts: the branch is decided by computing every
     denominator); the float T is for reporting.
   - G1 [2] (uniform from U_stat), G2 [11] (the frozen coexpression sampler; coexpression = Pearson over the same
     samples, Universe.Z), G3 [R24] (GAMBA brain>body ∩ U_stat), G4 [12] (G2's sampler inside G3's background), G5 [13]
     (BrainSpan trajectories; asdg.genesets.trajectory_matched_sets on U_stat; the register's label); Level-2 p = max
     over G1-G5. R8's pool rules as descriptors.py. The row reads "no calibrated test" whatever the legs show.
   - Sample ids: the source's frame index is checked against the metadata's and dropped at once (row positions only);
     only the declared metadata columns are accepted; no id is printed, logged or saved (R10 :654-655; §8).
3. MOR-T1 / T2 (R21) and BENK-C2-SD / -DD, PARK-C5 (R28): the decoded-list T with all its legs (Level 0, site, species,
   descriptor legs; no T_abs) through the runner's decoded-list route; this module gives their labels, R28's proxy
   direction (parse_proxy_direction), and R28's RLM: statsmodels RLM with its defaults (rlm_statsmodels) asserted equal
   to a direct iteratively reweighted Huber fit (irls_huber_direct; P17), reported as the t of the log2FC coefficient.
4. Synthetic providers for plants (SyntheticSources delegates here): signed weights and a "paper map"; BrainSpan-like and
   AHBA-like per-sample frames with planted sample ids, NaN / inf / constant columns and ties; RLM inputs.

Readings / choices this module makes where the frozen texts leave the implementation a choice (listed in the WP2
report; none changes a definition). RUN_PLAN_amend_2 pinned U-F1 (R41), U-F3 (R42 (c)) and U-F5 (R42 (b), changed:
log2(RPKM + 1)), and the three readings WP2 raised as NotImplementedError (SW_GENE_LEGS_UNPINNED -> R41;
LIU_DUPLICATE_UNPINNED -> R42 (a); LIU_T5_HIP_UNPINNED -> R42 (e)); none is raised any more.
U-F1 (pinned, R41) signed-weight weight order: each leg's sampler draws all its sets from the leg's generator (R7)
     unchanged; then, from the same generator, one rng.permutation(m) per set in set order; member R[k, perm_k[j]]
     receives w_j. J1 keeps R7's order (S1c seed, S2c seed, the G2 sets) and draws the orders after the sets.
U-F2 passes: signed-weight T + site leg in the verdict pass (§4 legs table: S1c / S2c "all forms"); its gene legs, T_S
     and the registered outcome in the descriptor pass (:377 G3 "Giacomel's signed-weight cells"); Liu entirely in the
     descriptor pass (:377 "Liu (R10)"); neither has a sensitivity pass (R11: "every claim with a verdict").
U-F3 (pinned, R42 (c)) the samples used (U_stat's finiteness / constancy and the coexpression) are the samples T
     averages over (above).
U-F4 a two-sided descriptor row without a verdict has no d*: RUN_PLAN_amend_1 R36 (d) -> (a) (both one-sided p's and the
     literal per-leg two-sided p; no doubled p).
U-F5 (pinned, R42 (b)) the coexpression is on log2(RPKM + 1) for BrainSpan and on abagen's values for AHBA.
U-F6 R28's RLM runs in the verdict pass of BENK-C2-SD / -DD and PARK-C5 and is attached to the row as "rlm"; its inputs
     (per-gene decoding t, Gandal 2018 Table S1 DGE covariates) come from a source (WP5).
U-F7 (amendment-2 implementation choices, listed in the report; none changes a definition) a duplicate column that is
     missing in a sample makes the averaged value missing there (the plain mean; U_stat's finiteness rule then drops the
     column); a negative finite RPKM value is refused (log2(RPKM + 1) needs RPKM >= 0); an SD7 label whose marker
     sides disagree, or whose marked side has no DK label of its name, is unmatched (fail closed); 'merged' is read
     literally over every SD7 label, the dropped ones included; the T5 statistic with no other label is refused;
     "answered" reports the legs' p's (Level-2 and J1, as the row's direction reads them) and leaves the survival call
     at a level to the reporting step (R41 pins no alpha for this descriptor outcome).
"""
from __future__ import annotations

import hashlib
import math
import re
from fractions import Fraction
from typing import Callable, Mapping

import numpy as np
import pandas as pd
from scipy import stats

from . import a3_port as A3  # noqa: F401  (puts src/ on sys.path before the engine imports)
from . import adapters as AD
from . import descriptors as DS
from . import reporting as RPT
from . import seeds as SD
from asdg.cascade import corr_matrix
from asdg.genesets import MIN_SET, Trajectories, Universe, coexpr_matched_sets, trajectory_matched_sets
from asdg.spatial import site_null

DIRECTIONS = (1, -1)
NOT_COMPUTABLE = AD.NOT_COMPUTABLE
UNMATCHED = DS.UNMATCHED
NOT_APPLICABLE = DS.NOT_APPLICABLE
LEVEL2_LEGS = DS.LEVEL2_LEGS
RANK_CHUNK = 256  # samples ranked per block (memory: one block of int64 ranks at a time)


class FormNotTestable(RuntimeError):
    """A form cannot be computed at use with a registered status (prereg §4: 'not testable (< 5)'; RUN_PLAN_amend_2
    R42's fail-closed SD7 statuses); .status is the row's status, .detail its counts (never a name or a value)."""

    def __init__(self, status: str, detail: dict | None = None):
        super().__init__(status)
        self.status = status
        self.detail = dict(detail or {})


def _sha(*parts) -> str:
    h = hashlib.sha256()
    for p in parts:
        a = np.ascontiguousarray(np.asarray(p))
        h.update(str(a.dtype).encode("ascii") + str(a.shape).encode("ascii"))
        h.update(a.tobytes() if a.dtype != object else repr(a.tolist()).encode("utf-8"))
    return h.hexdigest()


def _reported(rec: dict, direction, two_sided) -> dict:
    """R1 / R36 (d) through descriptors' own helper (RUN_PLAN_amend_1 R36 (a) when no d* exists)."""
    return DS._with_direction(rec, direction, two_sided)


# ================================================================================================================
# 1. the signed-weight descriptor (claims_register.md:1469-1473; P15)
# ================================================================================================================
SW_FORM = "signed-weight rho descriptor (claims_register.md:1469-1473; RUN_PLAN P15)"
SW_LABEL_CLAIM = "descriptor (not testable as stated: signed-weight set score)"   # TSV rows 103-117 (status)
SW_LABEL_CELL = "descriptor (signed-weight form, not a claim)"                    # TSV rows 120-131 (T column)
SW_SITE_RULE = ("site leg = max(p_S1c, p_S2c) per direction (the adopted class-stratified pair, prereg.md:130-131); rho "
                "counted exactly (RUN_PLAN_amend_1 R32 (b); adapters.RankRho)")
SW_NO_DSTAR = ("no verdict, so no d* (RUN_PLAN_amend_1 R36 (d) -> (a)): both one-sided p's and the literal per-leg "
               "two-sided p are reported, no doubled p (U-F4)")
SW_ORDER_RULE = ("U-F1: each null set is drawn by its leg's frozen sampler from the leg's generator (R7); then, from the "
                 "same generator, one rng.permutation(m) per set in set order; member R[k, perm_k[j]] receives S's weight "
                 "w_j (claims_register.md:1472-1473: 'each null set receives S's weight vector in a random order')")
SW_R41_READING = (
    "RUN_PLAN_amend_2 R41, (i) + (b): the null maps and the observed value on the analysis class's §3.1 matrix; T_S = "
    "rho(y, b_S), b_S = sum_g w_g X[:, g] / sum w; a null set R (its leg's frozen sampler, the class universe) receives "
    "S's weights in a random order (U-F1) and b_R = sum_j w_j X[:, R_j] / sum w is compared with T_S exactly (R32 (b)); "
    "the registered outcome is answered only if T_S passes its §4.1 check")
SW_ZERO_SUM = "not computable (S's weights sum to 0)"                       # R41 'Zero weight sum'
SW_NOT_ANSWERED = "not answered (T_S not reproduced)"                     # R41 'The registered outcome'
SW_ANSWERED = "answered (T_S reproduced; the legs answer prereg §8's question)"
SW_NO_COMPARATOR = ("the row's TSV reproduction column holds no numeric ±.05 comparator for T_S (documented source "
                    "defect, rebuilt map or a value read only from a figure)")
SW_OBSERVED_LABEL = "T_S = rho(y, S's weighted score on the class's §3.1 matrix) (RUN_PLAN_amend_2 R41)"
# R41: the published rho of the MDD combined cells (TSV rows 115-117), asserted against the row's TSV text at use
SW_MDD_PUBLISHED = {115: ".531", 116: ".547", 117: ".529"}
_SW_COMPARATOR = re.compile("vs (?:the published rho )?([\u2212-]?[0-9]*\\.[0-9]+) \\(\u00b1\\.05\\)")


def sw_published_rho(row: int, reproduction_text: str):
    """The published rho T_S is checked against (R41): the ±.05 comparator of the row's TSV reproduction column
    ('... on our matrix vs the published rho -0.150 (±.05)'; '... vs .531 (±.05)'), as its decimal text; None if the
    column holds none. Rows 115-117 are asserted equal to R41's pins (.531 / .547 / .529); a column with two comparators
    is refused."""
    hits = _SW_COMPARATOR.findall(reproduction_text or "")
    if len(hits) > 1:
        raise ValueError(f"row {row}: the reproduction column holds {len(hits)} ±.05 comparators")
    val = hits[0].replace("\u2212", "-") if hits else None
    if int(row) in SW_MDD_PUBLISHED and val != SW_MDD_PUBLISHED[int(row)]:
        raise ValueError(f"row {row}: the TSV's comparator differs from RUN_PLAN_amend_2 R41's pin")
    return val


def aligned_weights(genes, weights, universe_index: Mapping[str, int]) -> tuple[np.ndarray, np.ndarray, dict]:
    """(S column indices, their weights in the same order, counts): the source's (gene, weight) pairs mapped to the
    universe; a gene listed twice is refused (its weight would be ambiguous); absent genes are counted, never silent."""
    genes = [str(g) for g in genes]
    w = np.asarray(weights, dtype=float)
    if w.shape != (len(genes),) or not np.isfinite(w).all():
        raise ValueError("signed-weight: one finite weight per listed gene is required")
    if len(set(genes)) != len(genes):
        raise ValueError("signed-weight: a gene is listed twice (its weight would be ambiguous)")
    keep = [k for k, g in enumerate(genes) if g in universe_index]
    S = np.array([universe_index[genes[k]] for k in keep], dtype=int)
    info = dict(n_members=len(genes), n_present=int(len(keep)), n_absent=int(len(genes) - len(keep)))
    return S, w[keep], info


def weighted_maps(X, ordered, w, chunk: int = AD.CHUNK_MAX) -> np.ndarray:
    """(K, parcels): row k = sum_j w_j X[:, ordered[k, j]] / sum_j w_j (Giacomel's signed weighted mean, the TSV's
    'sum(z e) / sum(z)'). sum(w) = 0 is refused (the score is undefined)."""
    X = np.asarray(X, dtype=float)
    ordered = np.atleast_2d(np.asarray(ordered, dtype=int))
    w = np.asarray(w, dtype=float)
    if ordered.shape[1] != w.size:
        raise ValueError("weighted_maps: one weight per member position is required")
    sw = float(w.sum())
    if not (math.isfinite(sw) and sw != 0.0):
        raise ValueError("signed-weight: sum of S's weights is 0 or non-finite: the weighted score is undefined")
    out = np.empty((len(ordered), X.shape[0]))
    for a, b in AD._chunks(len(ordered), chunk):
        out[a:b] = np.einsum("pkm,m->kp", X[:, ordered[a:b]], w) / sw
    return out


def order_sets(sets, rng) -> tuple[np.ndarray, np.ndarray]:
    """U-F1: S's weight vector in a random order for every null set: one rng.permutation(m) per set, in set order
    (drawn after the sets); returns (ordered sets, permutations) with ordered[k, j] = sets[k, perm[k, j]], whose member
    receives w_j. The members of each set are unchanged."""
    sets = np.atleast_2d(np.asarray(sets, dtype=int))
    m = sets.shape[1]
    perms = np.stack([rng.permutation(m) for _ in range(len(sets))]) if len(sets) else np.empty((0, m), int)
    return np.take_along_axis(sets, perms, axis=1), perms


def _rho_float(R_rows, r_ref) -> np.ndarray:
    """Spearman rho as the Pearson r of doubled average ranks (float: J1's z and reporting only)."""
    return corr_matrix(np.atleast_2d(R_rows).astype(float), np.atleast_2d(r_ref).astype(float))


class WeightedSetRho:
    """The signed-weight gene legs' scorer on an explicit basis (P15). ctx: the class context the null sets are drawn
    from and their weighted maps built on (ctx.X, ctx.U, ctx.B.brain, ctx.D, ctx.classes); y: the map; S, w: S's
    columns and weights (same order); observed_map: the map T(S) is rho of y with (production, R41: S's weighted
    score on the same ctx, signed_weight_descriptor). Duck-typed for descriptors.j1_core (T_obs, site_input, T_sets,
    T_maps, T_sets_maps). Exact comparisons: rho_terms + adapters.rank_corr_counts."""
    form = "signed-weight rho (gene-set legs)"
    full_verdict = False
    conditioned = False

    def __init__(self, ctx, y, S, w, observed_map, *, parcel_ids, observed_label: str):
        self.ctx = ctx
        self.y = A3.align_to_context(ctx, y, parcel_ids, "signed-weight map y")
        if not (np.isfinite(self.y).all() and np.std(self.y) > 0):
            raise ValueError("signed-weight: y must be finite and non-constant on the analysis parcels")
        self.S = AD._as_set(S, ctx.G)
        self.w = np.asarray(w, dtype=float)
        if self.w.shape != self.S.shape or not np.isfinite(self.w).all() or float(self.w.sum()) == 0.0:
            raise ValueError("signed-weight: one finite weight per member of S, with a non-zero sum")
        b = A3.align_to_context(ctx, observed_map, parcel_ids, "signed-weight observed map")
        if not (np.isfinite(b).all() and np.std(b) > 0):
            raise ValueError("signed-weight: the observed map must be finite and non-constant")
        self.obs_map = b
        N0, Q0 = AD.rank_corr_terms(self.y, self.obs_map)
        self.N_obs, self.Q_obs = int(N0[0]), int(Q0[0])
        if self.Q_obs <= 0:
            raise ValueError("signed-weight: a constant rank vector")
        self.T_obs = self.N_obs / math.sqrt(self.Q_obs)
        self.observed_label = str(observed_label)
        self.n = int(ctx.n)
        self.parcel_ids = [int(i) for i in ctx.parcel_ids]
        self._ry = AD.doubled_ranks(self.y)
        self._robs = AD.doubled_ranks(self.obs_map)

    def site_input(self) -> np.ndarray:
        return self.y

    def maps(self, ordered, chunk: int = AD.CHUNK_MAX) -> np.ndarray:
        return weighted_maps(self.ctx.X, ordered, self.w, chunk)

    def s_map(self) -> np.ndarray:
        """S's own weighted map on this basis (S in its order, w unpermuted)."""
        return self.maps(self.S[None, :])[0]

    def rho_terms(self, ordered, chunk: int = AD.CHUNK_MAX) -> tuple[list, list]:
        ordered = np.atleast_2d(np.asarray(ordered, dtype=int))
        N, Q = [], []
        for a, b in AD._chunks(len(ordered), chunk):
            n_, q_ = AD.rank_corr_terms(self.y, self.maps(ordered[a:b], chunk))
            N += n_
            Q += q_
        return N, Q

    def T_sets(self, ordered, chunk: int = AD.CHUNK_MAX) -> np.ndarray:
        """Float rho(y, map of each ordered set) (J1's z only)."""
        return _rho_float(AD.doubled_ranks(self.maps(ordered, chunk)), self._ry)[:, 0]

    def T_maps(self, maps, s=None, chunk: int = AD.CHUNK_MAX) -> np.ndarray:
        """Float rho(map_i, observed map): T(S) on each surrogate (J1)."""
        return _rho_float(AD.doubled_ranks(np.atleast_2d(maps)), self._robs)[:, 0]

    def T_sets_maps(self, ordered, maps, chunk: int = AD.CHUNK_MAX) -> np.ndarray:
        """(n_maps, n_sets) float rho(map_i, map of set k) (J1)."""
        setR = AD.doubled_ranks(self.maps(ordered, chunk)).astype(float)
        return corr_matrix(AD.doubled_ranks(np.atleast_2d(maps)).astype(float), setR)


def _sw_scored(ad: WeightedSetRho, ordered, chunk, **info) -> dict:
    N, Q = ad.rho_terms(ordered, chunk)
    c = AD.rank_corr_counts(ad.N_obs, ad.Q_obs, N, Q)
    vals = np.array([n / math.sqrt(q) for n, q in zip(N, Q)], dtype=float)
    return dict(status="ok", p=c["p"], floor=1.0 / (len(N) + 1), n=int(len(N)), null_mean=float(vals.mean()),
                null_sd=float(vals.std(ddof=1)) if len(vals) > 1 else None,
                rank_rule=dict(branch=c["branch"], k_plus=c["k_plus"], k_minus=c["k_minus"], rule=c["rule"]), **info)


def sw_uniform_leg(ad: WeightedSetRho, K: int, rng, *, pool, name: str, seed_leg, chunk=AD.CHUNK_MAX,
                   return_draws: bool = False) -> dict:
    """G1 (pool = the universe) and G3 (pool = brain>body ∩ universe): uniform sets minus S with exactly the calls of
    asdg.genesets.random_sets, then U-F1's orders from the same generator."""
    m = int(ad.S.size)
    avail = np.setdiff1d(np.asarray(pool), ad.S)
    base = dict(leg=name, K=int(K), m=m, pool=int(avail.size), conditioned=False, seed_leg=seed_leg,
                weights="S's weights carried over (U-F1)")
    if avail.size < m:
        return dict(base, status=NOT_COMPUTABLE, p=None, n=0)
    sets = np.concatenate(list(DS.uniform_set_chunks(pool, m, K, rng, exclude=ad.S, chunk=chunk)))
    ordered, perms = order_sets(sets, rng)
    rec = dict(base, **_sw_scored(ad, ordered, chunk))
    if return_draws:
        rec["_draws"] = dict(sets=sets, perms=perms, ordered=ordered)
    return rec


def sw_coexpr_leg(ad: WeightedSetRho, K: int, rng, *, brain: bool, name: str, seed_leg, chunk=AD.CHUNK_MAX,
                  return_draws: bool = False) -> dict:
    """G2 (the universe) / G4 (brain>body ∩ universe): the frozen coexpression sampler (prereg.md:137-144), as
    descriptors._coexpr_leg draws it, then U-F1's orders. Pool < m -> 'unmatched' (R8)."""
    ctx, S = ad.ctx, ad.S
    m = int(S.size)
    pool_all = np.flatnonzero(ctx.B.brain) if brain else np.arange(ctx.G)
    avail = np.setdiff1d(pool_all, S).size
    base = dict(leg=name, K=int(K), m=m, pool=int(avail), conditioned=False, seed_leg=seed_leg,
                weights="S's weights carried over (U-F1)")
    if avail < m:
        return dict(base, status=UNMATCHED, p=None, n=0,
                    reason="pool < m: no sub-bin can be entered within 20 restarts (prereg.md:140-142; RUN_PLAN R8)")
    target = float(ctx.U.mean_coexpr(S))
    sets, info = coexpr_matched_sets(ctx.U, pool_all, m, target, K, rng, exclude=S)
    if sets is None:
        return dict(base, status=UNMATCHED, p=None, n=0, target=target, info=DS._sampler_info(info))
    ordered, perms = order_sets(sets, rng)
    rec = dict(base, **_sw_scored(ad, ordered, chunk, target=target, info=DS._sampler_info(info)))
    if return_draws:
        rec["_draws"] = dict(sets=sets, perms=perms, ordered=ordered)
    return rec


def sw_g5_leg(ad: WeightedSetRho, K: int, rng, traj, *, chunk=AD.CHUNK_MAX, return_draws: bool = False) -> dict:
    """G5 [13]: trajectory- and coexpression-matched sets (asdg.genesets.trajectory_matched_sets), then U-F1's orders."""
    ctx, S = ad.ctx, ad.S
    tr = DS.trajectories_for(ctx, traj)
    names = [ctx.U.genes[i] for i in S]
    sets, info = trajectory_matched_sets(ctx.U, names, tr, K, rng)
    base = dict(leg="G5", K=int(K), m=int(S.size), conditioned=False, seed_leg=13, n_trajectories=int(len(tr.names)),
                weights="S's weights carried over (U-F1)")
    if sets is None:
        st = info["status"]
        if st not in (NOT_APPLICABLE, UNMATCHED):
            raise RuntimeError(f"G5 sampler status {st!r}")
        return dict(base, status=st, p=None, n=0, info=DS._sampler_info(info))
    ordered, perms = order_sets(sets, rng)
    rec = dict(base, **_sw_scored(ad, ordered, chunk, info=DS._sampler_info(info)))
    if return_draws:
        rec["_draws"] = dict(sets=sets, perms=perms, ordered=ordered)
    return rec


def sw_j1_leg(ad: WeightedSetRho, seed_of: Callable, *, K_sets: int, K_surr: int, chunk=AD.CHUNK_MAX,
              return_draws: bool = False) -> dict:
    """J1 [14] with S's weights carried over: one generator from leg 14 (R7: S1c seed, S2c seed, then the G2 sets; then
    U-F1's orders); K_surr S1c and S2c surrogates (spatial.site_null); descriptors.j1_core on the ordered sets (z is not
    a rank statistic, R32 (b); R32 (a) on an exact type)."""
    ctx, S = ad.ctx, ad.S
    m = int(S.size)
    g = np.random.default_rng(seed_of("J1"))
    s1c = int(g.integers(2 ** 31))
    s2c = int(g.integers(2 ** 31))
    base = dict(leg="J1", seed_leg=14, seeds=dict(S1c=s1c, S2c=s2c), K_sets=int(K_sets), K_surr=int(K_surr), m=m,
                order="S1c seed, S2c seed, then the G2 sets (R7; RUN_PLAN.md:545-546), then the weight orders (U-F1)",
                conditioned=False, weights="S's weights carried over (U-F1)")
    if np.setdiff1d(np.arange(ctx.G), S).size < m:
        return dict(base, status=NOT_COMPUTABLE, p=None)
    target = float(ctx.U.mean_coexpr(S))
    sets, info = coexpr_matched_sets(ctx.U, np.arange(ctx.G), m, target, int(K_sets), g, exclude=S)
    if sets is None:
        return dict(base, status=UNMATCHED, p=None, target=target, info=DS._sampler_info(info))
    ordered, perms = order_sets(sets, g)
    sur, ex = {}, {}
    for name, method, seed in (("S1c", "brainsmash", s1c), ("S2c", "msr", s2c)):
        sur[name], si = site_null(ad.site_input(), ctx.D, ctx.classes, int(K_surr), seed, method)
        ex[name] = bool(si["exact"])
    core = DS.j1_core(ad, ordered, sur, chunk=chunk, exact=ex)
    rec = dict(base, target=target, sampler=DS._sampler_info(info), **core)
    if return_draws:
        rec["_draws"] = dict(sets=sets, perms=perms, ordered=ordered, surrogates=sur)
    return rec


def signed_weight_gene_legs(ad: WeightedSetRho, seed_of: Callable, g3_seed: Callable, *, K_sets: int, K_surr: int,
                            K_j1_sets: int, traj, direction=None, two_sided=None, chunk: int = AD.CHUNK_MAX) -> dict:
    """G1 [2], G2 [11], G3 [R24], G4 [12], G5 [13], the Level-2 max (prereg.md:154) and J1 [14] of a signed-weight row,
    with S's weights carried over (P15). The basis and the observed map are the WeightedSetRho's (production:
    signed_weight_descriptor, R41's class matrix and T_S)."""
    if not isinstance(ad, WeightedSetRho):
        raise TypeError("signed_weight_gene_legs takes a WeightedSetRho")
    legs = {"Level-2 G1": sw_uniform_leg(ad, K_sets, np.random.default_rng(seed_of("G1")), pool=np.arange(ad.ctx.G),
                                         name="Level-2 G1", seed_leg="leg 2 (G1)", chunk=chunk),
            "G2": sw_coexpr_leg(ad, K_sets, np.random.default_rng(seed_of("G2")), brain=False, name="G2", seed_leg=11,
                                chunk=chunk),
            "G3": sw_uniform_leg(ad, K_sets, np.random.default_rng(g3_seed()), pool=np.flatnonzero(ad.ctx.B.brain),
                                 name="G3", seed_leg="R24: first child of leg 3's key", chunk=chunk),
            "G4": sw_coexpr_leg(ad, K_sets, np.random.default_rng(seed_of("G4")), brain=True, name="G4", seed_leg=12,
                                chunk=chunk),
            "G5": sw_g5_leg(ad, K_sets, np.random.default_rng(seed_of("G5")), traj, chunk=chunk)}
    l2 = DS.level2_max(legs)
    j1 = sw_j1_leg(ad, seed_of, K_sets=K_j1_sets, K_surr=K_surr, chunk=chunk)
    for rec in (*legs.values(), l2, j1):
        _reported(rec, direction, two_sided)
    return dict(form=SW_FORM, T_gene_legs=float(ad.T_obs), N=int(ad.N_obs), Q=int(ad.Q_obs),
                observed=ad.observed_label, legs=legs, level2=l2, J1=j1, order_rule=SW_ORDER_RULE,
                counts=dict(K_sets=int(K_sets), K_surr=int(K_surr), K_j1_sets=int(K_j1_sets)),
                direction=direction, two_sided=two_sided,
                direction_reading=(SW_NO_DSTAR if two_sided and direction is None else DS.R1_DESCRIPTOR_READING),
                unconditioned="every descriptor leg is unconditioned (R6)")


def sw_basis_sha(ctx) -> str:
    """The identity of the matrix a signed-weight row's null maps and T_S are built on (R41: the analysis class's §3.1
    matrix on the analysis parcels): values, parcel ids and gene symbols."""
    return _sha(np.asarray(ctx.X, dtype=float), np.asarray(ctx.parcel_ids, dtype=np.int64),
                np.asarray(ctx.U.genes, dtype=str))


def sw_basis_check(rec: dict, ctx, y_ctx, S, w) -> dict:
    """R41's apparatus check (P15 extension): the record's basis is the class matrix (hash) and its T_S equals rho(y,
    S's weighted score) recomputed on that matrix by the direct formula (X[:, S] w / sum w; integer rank terms). A
    record built on another matrix (the authors' AHBA matrix) or compared with another observed value (rho with the
    paper's map) fails it."""
    S = np.asarray(S, dtype=int)
    w = np.asarray(w, dtype=float)
    b = (np.asarray(ctx.X, dtype=float)[:, S] @ w) / float(w.sum())
    N, Q = AD.rank_corr_terms(np.asarray(y_ctx, dtype=float), b)
    T = N[0] / math.sqrt(Q[0])
    checks = {"basis = the class's §3.1 matrix (hash)": (rec.get("basis") or {}).get("matrix_sha256") == sw_basis_sha(ctx),
              "T_S = rho(y, b_S) on the class matrix (direct, 1e-12)":
                  rec.get("T_S") is not None and abs(float(rec["T_S"]) - T) <= 1e-12}
    return dict(ok=all(checks.values()), checks=checks, T_S_direct=float(T))


def _p_view(rec: dict) -> dict:
    return {k: rec.get(k) for k in ("status", "p", "p_reported", "p_per_leg_two_sided")}


def signed_weight_descriptor(ctx, y, b, genes, weights, *, parcel_ids, traj, seed_of: Callable, g3_seed: Callable,
                             K_sets: int, K_surr: int, K_j1_sets: int, two_sided: bool, registered_direction, published,
                             chunk: int = AD.CHUNK_MAX) -> dict:
    """The descriptor pass of a signed-weight row (RUN_PLAN_amend_2 R41; module docstring 1). ctx: the analysis class's
    context restricted to the analysis parcels (the §3.1 matrix); y, b: the map and the paper's weighted map on
    `parcel_ids`; genes, weights: S's genes and signed weights as the source gives them (absent genes counted);
    published: the row's ±.05 comparator for T_S (sw_published_rho) or None. Returns T_S, the gene legs, the
    reproduction check and the registered outcome, with the registered T (rho with the paper's map) beside them."""
    S, w, info = aligned_weights(genes, weights, ctx.U.index)
    if len(S) < MIN_SET:
        raise FormNotTestable(f"not testable (< 5): {len(S)} columns of S in the analysis universe (U14)")
    y_ctx = A3.align_to_context(ctx, y, parcel_ids, "signed-weight map y")
    registered_T = float(AD.RankRho(ctx, y, b, parcel_ids=parcel_ids).T_obs)
    direction = None if two_sided else registered_direction
    rec = dict(form=SW_FORM, reading=SW_R41_READING, registered_T=registered_T,
               registered_T_rule="rho(y, the paper's weighted GEDAR map): the registered descriptor T, reported as "
                                 "registered; its site leg is the verdict pass's (R41 'Reporting')",
               set=info, weights=dict(n=int(w.size), sum=float(math.fsum(w.tolist())), n_negative=int((w < 0).sum())),
               basis=dict(matrix_sha256=sw_basis_sha(ctx), n_parcels=int(ctx.n), n_genes=int(ctx.G),
                          what="the analysis class's §3.1 matrix on the analysis parcels (R41 (i))"),
               published=published, two_sided=bool(two_sided), registered_direction=registered_direction,
               direction_reading=SW_NO_DSTAR if two_sided else DS.R1_DESCRIPTOR_READING, order_rule=SW_ORDER_RULE)
    if math.fsum(w.tolist()) == 0.0 or float(w.sum()) == 0.0:
        return dict(rec, T_S=None, gene_legs=dict(status=SW_ZERO_SUM), reproduction=None,
                    registered_outcome=dict(status=SW_NOT_ANSWERED, reason="T_S not computable: " + SW_ZERO_SUM))
    b_S = weighted_maps(ctx.X, S[None, :], w, chunk)[0]
    ad = WeightedSetRho(ctx, y_ctx, S, w, b_S, parcel_ids=[int(i) for i in ctx.parcel_ids],
                        observed_label=SW_OBSERVED_LABEL)
    legs = signed_weight_gene_legs(ad, seed_of, g3_seed, K_sets=K_sets, K_surr=K_surr, K_j1_sets=K_j1_sets, traj=traj,
                                   direction=direction, two_sided=two_sided, chunk=chunk)
    T_S = float(ad.T_obs)
    if published is None:
        rc, outcome = None, dict(status=SW_NOT_ANSWERED, reason=SW_NO_COMPARATOR)
    else:
        rc = RPT.reproduction_check(published, T_S, functional="signed-weight rho")
        if RPT.is_reproduced(rc):
            outcome = dict(status=SW_ANSWERED, level2=_p_view(legs["level2"]), J1=_p_view(legs["J1"]),
                           direction=direction, two_sided=bool(two_sided),
                           note="the legs' p's as the row's direction reads them; the site leg on rho is the verdict "
                                "pass's; no survival call is made here (R41 pins no alpha for this outcome)")
        else:
            outcome = dict(status=SW_NOT_ANSWERED, reason=f"T_S {rc['label']} against the published {published} (±.05)")
    rec.update(T_S=T_S, N_S=int(ad.N_obs), Q_S=int(ad.Q_obs), T_S_map_sha256=_sha(b_S), gene_legs=legs,
               reproduction=rc, registered_outcome=outcome)
    chk = sw_basis_check(rec, ctx, y_ctx, S, w)
    if not chk["ok"]:
        raise AD.FunctionalDefect(f"R41: the signed-weight record fails its basis check {chk['checks']}")
    rec["basis_check"] = chk
    return rec


def signed_weight_site(ctx, y, b, *, parcel_ids, K: int, seed_of: Callable, two_sided: bool, registered_direction,
                       chunk: int = AD.CHUNK_MAX) -> dict:
    """The verdict-pass part of a signed-weight row: T = rho(y, b) (b = the paper's weighted GEDAR map) and the
    class-stratified site leg on rho (S1c [0], S2c [1]; adapters.RankRho, exact counts, R32 (b) / (c)). No verdict:
    a two-sided row has no d* (U-F4)."""
    rr = AD.RankRho(ctx, y, b, parcel_ids=parcel_ids)
    site = rr.site_leg(int(K), seed_of, chunk)
    direction = None if two_sided else registered_direction
    legs = {}
    for leg in ("S1c", "S2c"):
        s = site[leg]
        legs[leg] = _reported(dict(p=s["p"], floor=s["floor"], seed=s["seed"], info=s["info"], seed_leg=SD.LEGS[leg],
                                   status="ok", K=int(K)), direction, two_sided)
    smax = _reported(dict(p={d: max(legs["S1c"]["p"][d], legs["S2c"]["p"][d]) for d in DIRECTIONS},
                          floor=max(legs["S1c"]["floor"], legs["S2c"]["floor"]), rule=SW_SITE_RULE, status="ok"),
                     direction, two_sided)
    return dict(form=SW_FORM, T=float(rr.T_obs), N=int(rr.N_obs), Q=int(rr.Q_obs), rule=AD.R32_RANK_RULE,
                n_parcels=int(rr.n), parcel_ids=list(rr.parcel_ids), site=dict(legs=legs, max=smax),
                two_sided=bool(two_sided), registered_direction=registered_direction,
                direction_reading=SW_NO_DSTAR if two_sided else DS.R1_DESCRIPTOR_READING,
                gene_legs="descriptor pass (U-F2)")


# ================================================================================================================
# 2. gene-set-only: Liu (R10; P16)
# ================================================================================================================
LIU_FORM = "gene-set-only (RUN_PLAN R10)"
LIU_G5_LABEL = "matching variable = tested quantity; expected null by construction"   # claims_register.md:1666-1667
LIU_READING = ("no calibrated test (prereg_amend_5.md:163-164; RUN_PLAN R10 :650): the legs are descriptors; no count "
               "moves")
LIU_ABAGEN_NOT_RUNNABLE = "not auditable (definition not applicable: abagen sample assignment not runnable)"  # R10 :659
LIU_RANK_RULE = ("per sample r = sum_{g in S} (2R_g - (G + 1)) / (m (G - m)) over U_stat (doubled average ranks, Python "
                 "integers); T(R) = sum_{g in R} a_g / D with D common to every set of size m: numerators compared "
                 "(RUN_PLAN_amend_1 R32 (b); adapters.rational_counts)")
LIU_FRONTAL = ("DFC", "VFC", "MFC", "OFC")   # claims_register.md:1672-1673
# claims_register.md:1671-1673 and the TSV's T column (rows 471-477); t_text must be in the row's T column
LIU_SPECS = {
    "LIU-T1": dict(data="brainspan", kind="two-group", by="age", a=("prenatal",), b=("postnatal",),
                   t_text="T = mean r over prenatal samples (aged in pcw) - mean r over postnatal samples (mos / yrs)"),
    "LIU-T2": dict(data="brainspan", kind="two-group", by="structure", a=("MD", "DTH"), b=LIU_FRONTAL,
                   t_text="T = mean r (thalamus samples: MD, DTH) - mean r (frontal-cortex samples: DFC, VFC, MFC, OFC)"),
    "LIU-T2-STR": dict(data="brainspan", kind="two-group", by="structure", a=("STR",), b=LIU_FRONTAL,
                       t_text="T = mean r (striatum samples: STR) - mean r (frontal-cortex samples: DFC, VFC, MFC, OFC)"),
    "LIU-T2-CBC": dict(data="brainspan", kind="two-group", by="structure", a=("CBC",), b=LIU_FRONTAL,
                       t_text="T = mean r (cerebellum samples: CBC) - mean r (frontal-cortex samples: DFC, VFC, MFC, "
                              "OFC)"),
    "LIU-T2-HIP": dict(data="brainspan", kind="two-group", by="structure", a=("HIP",), b=LIU_FRONTAL,
                       t_text="T = mean r (hippocampus samples: HIP) - mean r (frontal-cortex samples: DFC, VFC, MFC, "
                              "OFC)"),
    "LIU-T4": dict(data="ahba", kind="label-mean", t_text="T = mean r over the cortical labels"),
    "LIU-T5": dict(data="ahba", kind="label-contrast", t_text="T = r(hippocampus) - mean r(other labels)"),
}
LIU_META = {"brainspan": ("age", "structure_acronym"), "ahba": ("label",)}   # the only metadata columns accepted
# R42 (a), (b): the scale each data kind's values are used on; a source states its scale
LIU_SCALES = {"brainspan": ("RPKM", "log2(RPKM+1)"), "ahba": ("abagen",)}
LIU_SCALE_USED = {"brainspan": "log2(RPKM+1)", "ahba": "abagen (as abagen returns them)"}
LIU_DUPLICATE_RULE = ("RUN_PLAN_amend_2 R42 (a): columns sharing a symbol after the HGNC mapping averaged per sample "
                      "(BrainSpan on log2(RPKM + 1); AHBA as abagen returns them), before U_stat's rule; counted")
# R42 (d): SD7's label column
SD7_SUFFIXES = ("_thickavg", "_surfavg")
SD7_DROP_TOKENS = ("ctx",)
SD7_MARKERS = {"l": "L", "lh": "L", "left": "L", "r": "R", "rh": "R", "right": "R"}
SD7_ALIASES = {"thal": "thalamusproper", "caud": "caudate", "put": "putamen", "pal": "pallidum",
               "hippo": "hippocampus", "amyg": "amygdala", "accumb": "accumbensarea"}
SD7_LATVENT = "latvent"
SD7_GLOBAL = ("icv", "thickness", "surfarea")
SD7_UNMATCHED = "not auditable (definition not applicable: SD7 labels unmatched)"            # R42 (d)
LIU_T4_NO_CORTICAL = "not auditable (definition not applicable: no SD7 cortical label matched)"  # R42 (e)
LIU_T5_NO_HIP = "not computable (no hippocampus label)"                                       # R42 (e)
SD7_RULE = ("RUN_PLAN_amend_2 R42 (d): case-fold; strip '_thickavg' / '_surfavg'; split on non-alphanumerics and drop "
            "'ctx'; a token l / r / lh / rh / left / right is a marker; a glued l / r marker when the rest is a "
            "recognised name; the alias table; an abagen DK name; the marker's side selects the L / R label id, an "
            "unmarked name every DK label of that name; lateral ventricles and global measures dropped and counted; "
            "unmatched, multi-label or colliding labels fail closed; pooled by DK name iff no SD7 label carries a marker")
DK_COLUMNS = ("id", "label", "hemisphere", "structure")
DK_HIPPOCAMPUS = "hippocampus"
DK_CORTEX = "cortex"


def liu_spec(cell_id: str, T: str) -> dict:
    """The registered Liu form of a gene-set-only row (LookupError if the cell or its T text is not registered)."""
    spec = LIU_SPECS.get(cell_id)
    if spec is None or spec["t_text"] not in T:
        raise LookupError("gene-set-only: the T column matches no registered Liu form")
    return dict(spec, cell_id=cell_id)


def _age_class(age, pos: int) -> str:
    s = str(age).strip()
    if s.endswith(" pcw"):
        return "prenatal"
    if s.endswith(" mos") or s.endswith(" yrs"):
        return "postnatal"
    raise ValueError(f"gene-set-only: an age form other than 'pcw' / 'mos' / 'yrs' at sample position {pos} "
                     "(claims_register.md:1671-1672)")


def dk_table_checked(dk) -> pd.DataFrame:
    """abagen's DK label table (atlas-desikankilliany.csv: id, label, hemisphere, structure), checked: unique ids,
    (name, hemisphere) unique, hemispheres in L / R / B. Indexed by id."""
    if not isinstance(dk, pd.DataFrame) or sorted(map(str, dk.columns)) != sorted(DK_COLUMNS):
        raise ValueError(f"gene-set-only: the DK table must hold exactly the columns {list(DK_COLUMNS)}")
    t = pd.DataFrame({"id": [int(i) for i in dk["id"]], "label": [str(x) for x in dk["label"]],
                      "hemisphere": [str(x) for x in dk["hemisphere"]],
                      "structure": [str(x) for x in dk["structure"]]})
    if not t["id"].is_unique or t[["label", "hemisphere"]].duplicated().any():
        raise ValueError("gene-set-only: the DK table repeats an id or a (name, hemisphere)")
    if not set(t["hemisphere"]) <= {"L", "R", "B"}:
        raise ValueError("gene-set-only: DK hemispheres outside L / R / B")
    return t.set_index("id", drop=False)


def sd7_label_parse(label: str, recognised: set) -> dict:
    """One SD7 label through R42 (d) steps 1-6: (name after the alias table, marker sides). No DK lookup here."""
    s = str(label).casefold()
    for suf in SD7_SUFFIXES:
        if s.endswith(suf):
            s = s[: -len(suf)]
            break
    tokens = [t for t in re.split(r"[\W_]+", s) if t and t not in SD7_DROP_TOKENS]
    sides = [SD7_MARKERS[t] for t in tokens if t in SD7_MARKERS]
    name = "".join(t for t in tokens if t not in SD7_MARKERS)
    glued = False
    if name and name not in recognised and name[0] in ("l", "r") and name[1:] in recognised:
        sides.append(SD7_MARKERS[name[0]])
        name, glued = name[1:], True
    name = SD7_ALIASES.get(name, name)
    return dict(name=name, sides=sides, glued_marker=glued)


def sd7_normalise(labels, dk) -> dict:
    """R42 (d): SD7's label column against abagen's DK table. Returns per-label entries (position, kind, DK ids; never
    the label text), the counts, `merged` / `pooled` (R10's binary rule: pooled iff no SD7 label carries a marker) and
    the matched DK ids. Fails closed (FormNotTestable SD7_UNMATCHED, with the counts) on an unmatched label, a label
    matching more than one DK label when not merged, or two labels on one DK label."""
    t = dk_table_checked(dk)
    names = set(t["label"])
    recognised = names | set(SD7_ALIASES) | {SD7_LATVENT} | set(SD7_GLOBAL)
    parsed = [sd7_label_parse(lb, recognised) for lb in labels]
    merged = not any(p["sides"] for p in parsed)
    entries, claim = [], {}
    n = dict(n_labels=len(parsed), n_matched=0, n_dropped_latvent=0, n_dropped_global=0, n_unmatched=0,
             n_conflicting_markers=0, n_side_absent=0, n_multi_label=0, n_collisions=0, n_glued_markers=0)
    for pos, p in enumerate(parsed):
        name, sides = p["name"], set(p["sides"])
        n["n_glued_markers"] += int(p["glued_marker"])
        if name == "" or name in SD7_GLOBAL:
            entries.append(dict(position=pos, kind="global measure (dropped)", ids=[]))
            n["n_dropped_global"] += 1
            continue
        if name == SD7_LATVENT:
            entries.append(dict(position=pos, kind="lateral ventricle (dropped)", ids=[]))
            n["n_dropped_latvent"] += 1
            continue
        if name not in names:
            entries.append(dict(position=pos, kind="unmatched", ids=[]))
            n["n_unmatched"] += 1
            continue
        if len(sides) > 1:
            entries.append(dict(position=pos, kind="unmatched (conflicting markers)", ids=[]))
            n["n_unmatched"] += 1
            n["n_conflicting_markers"] += 1
            continue
        rows = t[t["label"] == name]
        if sides:
            rows = rows[rows["hemisphere"] == next(iter(sides))]
            if rows.empty:
                entries.append(dict(position=pos, kind="unmatched (no DK label of this name on the marked side)",
                                    ids=[]))
                n["n_unmatched"] += 1
                n["n_side_absent"] += 1
                continue
        ids = sorted(int(i) for i in rows["id"])
        if len(ids) > 1 and not merged:
            entries.append(dict(position=pos, kind="matches more than one DK label", ids=ids))
            n["n_multi_label"] += 1
            continue
        entries.append(dict(position=pos, kind="matched", ids=ids, side=next(iter(sides), None)))
        n["n_matched"] += 1
        for i in ids:
            claim.setdefault(i, []).append(pos)
    n["n_collisions"] = sum(1 for v in claim.values() if len(v) > 1)
    rec = dict(n, merged=merged, pooled=merged, rule=SD7_RULE)
    if n["n_unmatched"] or n["n_multi_label"] or n["n_collisions"]:
        raise FormNotTestable(SD7_UNMATCHED, detail={k: v for k, v in rec.items() if k.startswith("n_")})
    rec["entries"] = entries
    rec["matched_ids"] = sorted(claim)
    return rec


def sd7_from_record(rec: Mapping, dk) -> dict:
    """WP3: SD7's label column as the material stage normalised it in memory (wp3_material.sd7_label_transform: the
    output of sd7_normalise without its rule text, or its fail-closed status with the counts; no label string). A
    fail-closed record raises the same FormNotTestable as sd7_normalise; a matched record is checked against the DK
    table (every id a DK id; matched_ids = the matched entries' ids; pooled = merged)."""
    if rec.get("status") != "matched":
        raise FormNotTestable(str(rec.get("status")), detail=dict(rec.get("counts") or {}))
    t = dk_table_checked(dk)
    ids = sorted({int(i) for e in rec["entries"] if e["kind"] == "matched" for i in e["ids"]})
    if not set(ids) <= set(int(i) for i in t["id"]) or ids != sorted(int(i) for i in rec["matched_ids"]):
        raise ValueError("gene-set-only: the SD7 record's DK ids do not match the DK table")
    if bool(rec["pooled"]) != bool(rec["merged"]):
        raise ValueError("gene-set-only: the SD7 record's pooling differs from R10's binary rule")
    return dict(rec, rule=SD7_RULE)


def label_key(dk_id: int, t: pd.DataFrame, pooled: bool):
    """A sample's label key: the DK name when pooled (R10's binary rule), else the DK label id."""
    return str(t.at[int(dk_id), "label"]) if pooled else int(dk_id)


def liu_label_set(spec: dict, sample_ids, dk, sd7: dict) -> dict:
    """R42 (e): the label set of T4 / T5 - the DK labels (pooled or not) that carry >= 1 sample and that SD7 lists;
    T4 its cortical labels (abagen's structure 'cortex'); T5 the hippocampus label(s) first, then every other label.
    sample_ids: each sample's DK label id (None: unassigned). Fails closed / not computable as R42 (e) states."""
    t = dk_table_checked(dk)
    pooled = bool(sd7["pooled"])
    listed = {label_key(i, t, pooled) for i in sd7["matched_ids"]}
    struct, name = {}, {}
    for i in sd7["matched_ids"]:
        k = label_key(i, t, pooled)
        struct.setdefault(k, set()).add(str(t.at[int(i), "structure"]))
        name.setdefault(k, set()).add(str(t.at[int(i), "label"]))
    if any(len(v) != 1 for v in struct.values()):
        raise ValueError("gene-set-only: a pooled DK name spans two structures")
    unknown = [d for d in sample_ids if d is not None and int(d) not in t.index]
    if unknown:
        raise ValueError(f"gene-set-only: {len(unknown)} sample label(s) outside the DK table")
    n_of = {}
    for d in sample_ids:
        if d is None:
            continue
        k = label_key(int(d), t, pooled)
        if k in listed:
            n_of[k] = n_of.get(k, 0) + 1
    sampled = [k for k in sorted(listed) if n_of.get(k, 0) >= 1]   # ids (unpooled) or names (pooled)
    if spec["kind"] == "label-mean":
        keys = [k for k in sampled if next(iter(struct[k])) == DK_CORTEX]
        if not keys:
            raise FormNotTestable(LIU_T4_NO_CORTICAL, detail=dict(n_listed=len(listed), n_with_samples=len(sampled)))
        hip = []
    elif spec["kind"] == "label-contrast":
        hip = [k for k in sampled if next(iter(name[k])) == DK_HIPPOCAMPUS]
        if not hip:
            raise FormNotTestable(LIU_T5_NO_HIP, detail=dict(n_listed=len(listed), n_with_samples=len(sampled)))
        keys = hip + [k for k in sampled if k not in hip]
    else:
        raise ValueError(f"unknown Liu kind {spec['kind']!r}")
    return dict(keys=keys, hip=hip, pooled=pooled, n_listed=len(listed), n_with_samples=len(sampled),
                samples_per_key={str(k): int(n_of[k]) for k in keys})


def liu_label_T(values: Mapping, spec: dict, label_set: dict) -> float:
    """R42 (e), 'the same function is applied to SD7's values': T4 = the mean of the labels' values; T5 = the mean of
    the hippocampus labels' values minus the mean of every other label's value. values: {label key: value}."""
    keys = list(label_set["keys"])
    missing = [k for k in keys if k not in values]
    if missing:
        raise ValueError(f"gene-set-only: {len(missing)} label(s) of the set without a value")
    if spec["kind"] == "label-mean":
        return float(np.mean([float(values[k]) for k in keys]))
    hip = list(label_set["hip"])
    others = [k for k in keys if k not in hip]
    if not others:
        raise ValueError("gene-set-only: LIU-T5 without another label")
    return float(np.mean([float(values[k]) for k in hip]) - np.mean([float(values[k]) for k in others]))


def liu_sd7_T(spec: dict, sd7_labels, sd7_values, dk, label_set: dict) -> dict:
    """The statistic computed from SD7's values (claims_register.md:1680-1681) by liu_label_T on our label set: each
    matched SD7 label's value goes to its key (pooled: the DK name; else its DK id)."""
    sd7 = sd7_normalise(sd7_labels, dk)
    if bool(sd7["pooled"]) != bool(label_set["pooled"]):
        raise ValueError("gene-set-only: SD7's pooling differs from the label set's")
    t = dk_table_checked(dk)
    labels = list(sd7_labels)
    vals = list(sd7_values)
    if len(vals) != len(labels):
        raise ValueError("gene-set-only: one SD7 value per SD7 label")
    by_key = {}
    for e in sd7["entries"]:
        if e["kind"] == "matched":
            by_key[label_key(e["ids"][0], t, sd7["pooled"])] = float(vals[e["position"]])
    return dict(T=liu_label_T(by_key, spec, label_set), n_values=len(by_key), pooled=bool(sd7["pooled"]))


def _strip_ids(expr, meta, data: str):
    """R10 :654-655 / §8: the source's frame index (sample / well ids) is checked against the metadata's and dropped at
    once; only row positions remain. Only the declared metadata columns are accepted. Messages never carry an id."""
    if not isinstance(expr, pd.DataFrame) or not isinstance(meta, pd.DataFrame):
        raise TypeError("gene-set-only: the expression and the sample metadata must be pandas DataFrames")
    if len(expr) != len(meta) or not bool(expr.index.equals(meta.index)):
        raise ValueError("gene-set-only: the sample metadata rows are not the expression rows (index mismatch)")
    want = LIU_META[data]
    if sorted(str(c) for c in meta.columns) != sorted(want):
        raise ValueError(f"gene-set-only: the metadata must hold exactly the declared columns {list(want)} "
                         f"({len(meta.columns)} given)")
    genes = [str(c) for c in expr.columns]
    X = expr.to_numpy(dtype=float, copy=True)
    cols = {c: list(meta[c].to_numpy()) for c in want}
    return X, genes, cols


def liu_scale(X: np.ndarray, data: str, scale) -> tuple:
    """R42 (a), (b): BrainSpan on log2(RPKM + 1) ('RPKM' transformed here; 'log2(RPKM+1)' as given; a negative finite
    RPKM refused); AHBA as abagen returns them. Returns (values, record)."""
    if scale not in LIU_SCALES[data]:
        raise ValueError(f"gene-set-only: {data} values on scale {scale!r}; accepted {list(LIU_SCALES[data])}")
    if data == "brainspan" and scale == "RPKM":
        fin = np.isfinite(X)
        if (X[fin] < 0).any():
            raise ValueError("gene-set-only: a negative RPKM value")
        with np.errstate(invalid="ignore"):
            X = np.log2(X + 1.0)
        how = "log2(RPKM + 1) computed here"
    else:
        how = "as given"
    return X, dict(scale_given=scale, scale_used=LIU_SCALE_USED[data], transform=how)


def liu_dedup(X: np.ndarray, genes: list) -> tuple:
    """R42 (a): columns sharing a symbol averaged per sample (the plain mean: a sample missing in one duplicate column
    is missing in the average), first-occurrence order; counted."""
    order, cols = [], {}
    for j, g in enumerate(genes):
        if g not in cols:
            order.append(g)
            cols[g] = []
        cols[g].append(j)
    dup = {g: c for g, c in cols.items() if len(c) > 1}
    rec = dict(n_duplicate_symbols=len(dup), n_duplicate_columns_merged=int(sum(len(c) for c in dup.values())),
               rule=LIU_DUPLICATE_RULE)
    if not dup:
        return X, list(genes), rec
    Y = np.empty((X.shape[0], len(order)))
    for k, g in enumerate(order):
        c = cols[g]
        Y[:, k] = X[:, c[0]] if len(c) == 1 else X[:, c].mean(axis=1)
    return Y, order, rec


def liu_groups(spec: dict, meta: Mapping[str, list], inputs: Mapping) -> tuple:
    """(group of each sample position or None, the group order, the label record). two-group: 'a' / 'b'; label kinds:
    the label keys of R42 (e)'s set (T5: the hippocampus label(s) first). R42 (c): samples outside every group are not
    used."""
    n = len(next(iter(meta.values())))
    if spec["kind"] == "two-group":
        grp = [None] * n
        if spec["by"] == "age":
            for i, a in enumerate(meta["age"]):
                g = _age_class(a, i)
                grp[i] = "a" if g in spec["a"] else ("b" if g in spec["b"] else None)
        elif spec["by"] == "structure":
            for i, s in enumerate(meta["structure_acronym"]):
                s = str(s).strip()
                grp[i] = "a" if s in spec["a"] else ("b" if s in spec["b"] else None)
        else:
            raise ValueError(f"unknown grouping {spec['by']!r}")
        return grp, ["a", "b"], None
    dk = inputs.get("dk_table")
    labels = inputs.get("sd7_labels")
    pre = inputs.get("sd7_normalised")
    if dk is None or (labels is None and pre is None):
        raise ValueError("gene-set-only: T4 / T5 need the DK table and SD7's label column")
    sd7 = sd7_from_record(pre, dk) if labels is None else sd7_normalise(labels, dk)
    ids = []
    for v in meta["label"]:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            ids.append(None)
        else:
            if isinstance(v, bool) or float(v) != int(v):
                raise ValueError("gene-set-only: a sample label that is not a DK label id")
            ids.append(int(v))
    ls = liu_label_set(spec, ids, dk, sd7)
    t = dk_table_checked(dk)
    keep = set(ls["keys"])
    keys = [None if d is None else label_key(d, t, ls["pooled"]) for d in ids]
    grp = [k if (k is not None and k in keep) else None for k in keys]
    lab = dict(sd7={k: v for k, v in sd7.items() if k not in ("entries", "matched_ids")},
               n_sd7_matched_ids=len(sd7["matched_ids"]), label_set=ls)
    return grp, list(ls["keys"]), lab


def liu_prepare(spec: dict, inputs: Mapping) -> dict:
    """R10 with R42: the scale, duplicates averaged, the samples used, U_stat (finite and non-constant over them;
    counts), S ∩ U_stat, per-sample doubled centred ranks (block by block), every group's per-gene Python-int rank sums,
    the coefficients a_g and the common denominator D, the observed numerator and the per-sample r of S. No sample id
    survives this call."""
    data = spec["data"]
    if inputs.get("data") != data:
        raise ValueError(f"gene-set-only: the source gave {inputs.get('data')!r} data; {spec['cell_id']} uses {data!r}")
    X, genes, meta = _strip_ids(inputs["expr"], inputs["meta"], data)
    n_cols_given = len(genes)
    X, scale_rec = liu_scale(X, data, inputs.get("scale"))
    X, genes, dup_rec = liu_dedup(X, genes)
    n_given, n_genes_given = X.shape
    grp, order, lab = liu_groups(spec, meta, inputs)
    used = np.array([i for i, g in enumerate(grp) if g is not None], dtype=int)
    row_group = [grp[i] for i in used]
    n_of = {g: int(sum(1 for x in row_group if x == g)) for g in order}
    empty = [g for g in order if n_of[g] == 0]
    if empty or (spec["kind"] == "label-contrast" and len(order) < 2) or not order:
        raise ValueError(f"gene-set-only: {len(empty)} group(s) without samples")
    Xu = X[used]
    del X
    finite = np.isfinite(Xu).all(axis=0)
    U = Universe(pd.DataFrame(Xu[:, finite], columns=np.asarray(genes, dtype=object)[finite]))
    del Xu
    G = int(U.X.shape[1])
    s_genes = [str(g) for g in inputs["set"]]
    idx, missing = U.idx(s_genes)
    gset = set(genes)
    n_members = len(dict.fromkeys(s_genes))
    in_data = sum(1 for g in dict.fromkeys(s_genes) if g in gset)
    set_info = dict(n_members=n_members, n_present=int(len(idx)), n_absent_from_data=int(n_members - in_data),
                    n_dropped_by_U_stat=int(in_data - len(idx)))
    ustat = dict(n_samples_given=int(n_given), n_samples_used=int(used.size),
                 samples_per_group={str(k): v for k, v in n_of.items()}, n_columns_given=int(n_cols_given),
                 n_genes_given=int(n_genes_given), duplicates=dup_rec, scale=scale_rec,
                 n_dropped_nonfinite=int((~finite).sum()), n_dropped_constant=int(U.n_dropped_constant), n_U_stat=G,
                 rule="finite and non-constant over the samples used (asdg.genesets.Universe; RUN_PLAN R10 :641-643; "
                      "R42 (c))")
    if len(idx) < MIN_SET:
        raise FormNotTestable(f"not testable (< 5): {len(idx)} columns of S in U_stat (R10)")
    S = np.asarray(idx, dtype=int)
    m = int(S.size)
    acc = {g: np.zeros(G, dtype=object) for g in order}
    N_S: list[int] = []
    for a in range(0, used.size, RANK_CHUNK):
        C = AD.doubled_ranks(U.X[a: a + RANK_CHUNK]) - (G + 1)   # integers, |C| <= G - 1
        for k in range(C.shape[0]):
            row = C[k].astype(object)                             # Python ints from here on (R32 (b))
            g = row_group[a + k]
            acc[g] = acc[g] + row
            N_S.append(int(sum(row[S].tolist())))
    mm = m * (G - m)
    kind = spec["kind"]
    if kind == "two-group":
        na, nb = n_of["a"], n_of["b"]
        coef = nb * acc["a"] - na * acc["b"]
        D = na * nb * mm
        formula = "a_g = n_b sum_{s in a} C_sg - n_a sum_{s in b} C_sg; D = n_a n_b m (G - m)"
    elif kind == "label-mean":
        lam = math.lcm(*[n_of[lb] for lb in order])
        coef = sum(((lam // n_of[lb]) * acc[lb] for lb in order), np.zeros(G, dtype=object))
        D = len(order) * lam * mm
        formula = "a_g = sum_l (Lambda / n_l) sum_{s in l} C_sg; D = L Lambda m (G - m)"
    else:
        hips = list(lab["label_set"]["hip"])
        others = [lb for lb in order if lb not in hips]
        if not others:
            raise ValueError("gene-set-only: LIU-T5 without another label")
        lam = math.lcm(*[n_of[lb] for lb in order])
        coef = len(others) * sum(((lam // n_of[h]) * acc[h] for h in hips), np.zeros(G, dtype=object)) \
            - len(hips) * sum(((lam // n_of[lb]) * acc[lb] for lb in others), np.zeros(G, dtype=object))
        D = len(hips) * len(others) * lam * mm
        formula = ("a_g = L_o sum_{h in H} (Lambda / n_h) sum_{s in h} C_sg - H sum_{l not in H} (Lambda / n_l) "
                   "sum_{s in l} C_sg; D = H L_o Lambda m (G - m)")
    if not all(type(v) is int for v in coef[:8].tolist()) or type(D) is not int:
        raise AD.FunctionalDefect("R32 (b): the Liu coefficients are not Python integers")
    num0 = int(sum(coef[S].tolist()))
    r = np.array([v / mm for v in N_S], dtype=float)
    # apparatus: the exact rational equals the float statistic computed directly from the per-sample r (labels:
    # liu_label_T, the function R42 (e) also applies to SD7's values)
    gm = {g: float(np.mean([r[k] for k in range(used.size) if row_group[k] == g])) for g in order}
    direct = gm["a"] - gm["b"] if kind == "two-group" else liu_label_T(gm, spec, lab["label_set"])
    T = num0 / D
    if not abs(T - direct) <= 1e-12 * max(1.0, abs(direct)):
        raise AD.FunctionalDefect(f"R10: the integer T ({T!r}) differs from the per-sample computation ({direct!r})")
    return dict(spec=spec, U=U, G=G, S=S, m=m, coef=coef, D=D, num0=num0, T=T, formula=formula, set_info=set_info,
                ustat=ustat, per_sample_r=r, used_positions=used, row_group=row_group, group_order=order,
                group_means=gm, labels=lab, brain=inputs.get("brain") or [], traj=inputs.get("traj"))


def _liu_scored(pp: dict, sets, **info) -> dict:
    coef, D = pp["coef"], pp["D"]
    nums = [int(sum(coef[row].tolist())) for row in np.atleast_2d(sets)]
    c = AD.rational_counts(pp["num0"], D, nums, [D] * len(nums))
    vals = np.array([x / D for x in nums], dtype=float)
    return dict(status="ok", p=c["p"], floor=1.0 / (len(nums) + 1), n=int(len(nums)), null_mean=float(vals.mean()),
                null_sd=float(vals.std(ddof=1)) if len(vals) > 1 else None,
                rank_rule=dict(branch=c["branch"], k_plus=c["k_plus"], k_minus=c["k_minus"], rule=c["rule"]), **info)


def liu_legs(pp: dict, K: int, seed_of: Callable, g3_seed: Callable, *, return_draws: bool = False) -> dict:
    """G1 [2], G2 [11], G3 [R24], G4 [12], G5 [13] drawn on U_stat with the coexpression over the same samples
    (R10 :646-649); R8's labels as descriptors.py."""
    U, S, m, G = pp["U"], pp["S"], pp["m"], pp["G"]
    brain = np.array(sorted(U.index[g] for g in set(map(str, pp["brain"])) if g in U.index), dtype=int)
    allg = np.arange(G)
    legs, draws = {}, {}

    def uniform(name, pool, rng, seed_leg):
        avail = np.setdiff1d(pool, S)
        base = dict(leg=name, K=int(K), m=m, pool=int(avail.size), seed_leg=seed_leg)
        if avail.size < m:
            return dict(base, status=NOT_COMPUTABLE, p=None, n=0)
        sets = np.concatenate(list(DS.uniform_set_chunks(pool, m, K, rng, exclude=S)))
        draws[name] = sets
        return dict(base, **_liu_scored(pp, sets))

    def coexpr(name, pool, rng, seed_leg):
        avail = np.setdiff1d(pool, S).size
        base = dict(leg=name, K=int(K), m=m, pool=int(avail), seed_leg=seed_leg)
        if avail < m:
            return dict(base, status=UNMATCHED, p=None, n=0,
                        reason="pool < m: no sub-bin can be entered within 20 restarts (prereg.md:140-142; R8)")
        target = float(U.mean_coexpr(S))
        sets, info = coexpr_matched_sets(U, pool, m, target, K, rng, exclude=S)
        if sets is None:
            return dict(base, status=UNMATCHED, p=None, n=0, target=target, info=DS._sampler_info(info))
        draws[name] = sets
        return dict(base, **_liu_scored(pp, sets, target=target, info=DS._sampler_info(info)))

    legs["Level-2 G1"] = uniform("Level-2 G1", allg, np.random.default_rng(seed_of("G1")), "leg 2 (G1)")
    legs["G2"] = coexpr("G2", allg, np.random.default_rng(seed_of("G2")), 11)
    legs["G3"] = uniform("G3", brain, np.random.default_rng(g3_seed()), "R24: first child of leg 3's key")
    legs["G4"] = coexpr("G4", brain, np.random.default_rng(seed_of("G4")), 12)
    traj = pp["traj"]
    base5 = dict(leg="G5", K=int(K), m=m, seed_leg=13, label=LIU_G5_LABEL)
    if traj is None:
        raise ValueError("gene-set-only: G5 needs the BrainSpan trajectories (prereg.md:145-153)")
    if not isinstance(traj, pd.DataFrame) or traj.shape[1] != 8 or not traj.index.is_unique:
        raise ValueError("gene-set-only: trajectories must be a deduplicated genes x 8 frame (prereg.md:149-151)")
    tr = Trajectories(traj, U)
    sets, info = trajectory_matched_sets(U, [U.genes[i] for i in S], tr, K, np.random.default_rng(seed_of("G5")))
    if sets is None:
        st = info["status"]
        if st not in (NOT_APPLICABLE, UNMATCHED):
            raise RuntimeError(f"G5 sampler status {st!r}")
        legs["G5"] = dict(base5, status=st, p=None, n=0, info=DS._sampler_info(info))
    else:
        draws["G5"] = sets
        legs["G5"] = dict(base5, n_trajectories=int(len(tr.names)), **_liu_scored(pp, sets, info=DS._sampler_info(info)))
    out = dict(legs=legs, level2=DS.level2_max(legs), n_brain=int(brain.size))
    if return_draws:
        out["_draws"] = draws
    return out


def liu_compute(spec: dict, inputs: Mapping, *, K: int, seed_of: Callable, g3_seed: Callable, two_sided: bool,
                registered_direction, return_detail: bool = False) -> dict:
    """One Liu row (descriptor pass): T, the per-sample r, U_stat's counts and G1-G5 with the Level-2 max. Reported p:
    the registered direction (one-sided) or, two-sided, no d* (U-F4)."""
    pp = liu_prepare(spec, inputs)
    lg = liu_legs(pp, int(K), seed_of, g3_seed, return_draws=return_detail)
    direction = None if two_sided else registered_direction
    for rec in (*lg["legs"].values(), lg["level2"]):
        _reported(rec, direction, two_sided)
    rec = dict(form=LIU_FORM, cell_id=spec["cell_id"], data=spec["data"], kind=spec["kind"], T=float(pp["T"]),
               T_numerator=pp["num0"], T_denominator=pp["D"], formula=pp["formula"], rank_rule=LIU_RANK_RULE,
               groups=dict(order=[str(g) for g in pp["group_order"]] if spec["kind"] != "two-group" else
                           {"a": list(spec["a"]), "b": list(spec["b"])},
                           samples_per_group=pp["ustat"]["samples_per_group"],
                           mean_r={str(k): v for k, v in pp["group_means"].items()},
                           key=("DK name (pooled)" if (pp["labels"] or {}).get("label_set", {}).get("pooled") else
                                "DK label id") if spec["kind"] != "two-group" else "sample group"),
               labels=pp["labels"],
               per_sample_r=dict(values=[float(v) for v in pp["per_sample_r"]],
                                 positions=[int(i) for i in pp["used_positions"]],
                                 note="row positions in the source's order (ids dropped at load; R10 :654-655)"),
               U_stat=pp["ustat"], set=dict(pp["set_info"], m=pp["m"]), legs=lg["legs"], level2=lg["level2"],
               n_brain_in_U_stat=lg["n_brain"], K=int(K), two_sided=bool(two_sided),
               registered_direction=registered_direction,
               direction_reading=SW_NO_DSTAR if two_sided else DS.R1_DESCRIPTOR_READING,
               G5_label=LIU_G5_LABEL, reading=LIU_READING, unconditioned="every leg is unconditioned (R6)")
    if return_detail:
        rec["_detail"] = dict(prepared=pp, draws=lg.get("_draws"))
    return rec


# ================================================================================================================
# 3. MOR-T (R21), BENK-C2 / PARK-C5 (R28): labels, the proxy direction, the RLM
# ================================================================================================================
R21_LABEL = "descriptor (not testable as stated: tail-rank statistic); calibration extrapolated (class)"  # :877-878
R21_APART = "non-ASD outcome (CNV class): reported apart (RUN_PLAN R21 :878; claims_register.md:222-223)"
R21_READING = ("R21 (RUN_PLAN.md:873-878): the decoded-list T with all its legs (Level 0, site, species, descriptor legs) "
               "on native MIST64; no T_abs; values and p's, never a survival")
R28_LABEL = ("descriptor (not testable as stated: genome-wide robust regression); proxy set (Gandal 2018 ASD-down)")
R28_READING = ("R28 (RUN_PLAN.md:1025-1027): S = gandal2018_asd_down with the decoded-list T and all its legs (Level 0, "
               "site, species and descriptor legs; no T_abs), direction as the TSV; carries R27's calibration labels "
               "(the reporting step); never a survival")
R28_RLM_READING = ("statsmodels RLM(endog = per-gene decoding t, exog = [log2FC, GC %, const]) with its defaults "
                   "(HuberT(), scale by MAD); the reported value is the t of the log2FC coefficient (RUN_PLAN R28 "
                   ":996-998); rows without a finite value in a model column dropped and counted (:1023-1024); the SCZ "
                   "and BD rows run the same way; asserted equal to a direct iteratively reweighted Huber fit (P17)")
R28_PROXY_DIRECTION = re.compile("proxy descriptor ([+−]) \\(")
# the published values the RLM t is reported beside (TSV published_value_and_location, rows 518, 519, 603; R28 :998)
R28_PUBLISHED = {"BENK-C2-SD": {"ASD": 42.270, "SCZ": 18.548, "BD": 0.577},
                 "BENK-C2-DD": {"ASD": 28.099, "SCZ": 14.192, "BD": -2.014},
                 "PARK-C5": {"ASD": -34.89, "SCZ": -8.93, "BD": 5.34}}
R28_COLUMNS = ("t", "ASD.log2FC", "SCZ.log2FC", "BD.log2FC", "percentage_gene_gc_content")
HUBER_T = 1.345                     # statsmodels HuberT() default
MAD_C = float(stats.norm.ppf(0.75))  # statsmodels.robust.scale.mad's constant
RLM_TOL = 1e-8                      # the production assertion: statsmodels RLM == the direct IRLS fit (relative)


def parse_proxy_direction(text: str):
    """R28 'direction as the TSV': the proxy's sign in 'proxy descriptor − (' / 'proxy descriptor + (' -> -1 / +1;
    None if the form is absent (the runner refuses)."""
    m = R28_PROXY_DIRECTION.search(text or "")
    if not m:
        return None
    return 1 if m.group(1) == "+" else -1


def _huber_rho(z, t=HUBER_T):
    a = np.abs(z)
    return np.where(a <= t, 0.5 * z ** 2, a * t - 0.5 * t ** 2)


def _huber_psi(z, t=HUBER_T):
    return np.where(np.abs(z) <= t, z, t * np.sign(z))


def _huber_psi_deriv(z, t=HUBER_T):
    return (np.abs(z) <= t).astype(float)


def _huber_weights(z, t=HUBER_T):
    a = np.abs(z)
    return np.where(a <= t, 1.0, t / np.where(a <= t, 1.0, a))


def irls_huber_direct(endog, exog, *, t: float = HUBER_T, maxiter: int = 50, tol: float = 1e-8) -> dict:
    """A direct iteratively reweighted least-squares Huber M-fit, written from the definitions (P17's comparator of
    rlm_statsmodels): OLS start; scale = median |resid| / Phi^-1(3/4) (MAD about 0); weights min(1, t / |resid / scale|);
    weighted LS by the pseudo-inverse; scale updated each step; stop when the Huber deviance sum rho(resid / s_w)
    (s_w = the weighted LS residual variance) changes by <= tol or after maxiter fits; covariance Huber's H1:
    k^2 [sum psi(r)^2 / (n - p)] scale^2 / [mean psi'(r)]^2 (X^T X)^-1, k = 1 + p / n var(psi') / mean(psi')^2."""
    y = np.asarray(endog, dtype=float)
    X = np.asarray(exog, dtype=float)
    n, p = X.shape
    rank = int(np.linalg.matrix_rank(X))
    params = np.linalg.pinv(X) @ y
    resid = y - X @ params
    wls_scale = float(resid @ resid) / (n - p)
    scale = float(np.median(np.abs(resid))) / MAD_C
    dev = [np.inf, float(_huber_rho(resid / wls_scale, t).sum())]
    it = 1
    while True:
        if scale == 0.0:
            break
        w = _huber_weights(resid / scale, t)
        wh = np.sqrt(w)
        wX, wy = wh[:, None] * X, wh * y
        params = np.linalg.pinv(wX) @ wy
        resid = y - X @ params
        wres = wy - wX @ params
        wls_scale = float(wres @ wres) / (n - p)
        scale = float(np.median(np.abs(resid))) / MAD_C
        dev.append(float(_huber_rho(resid / wls_scale, t).sum()))
        it += 1
        if not (abs(dev[it] - dev[it - 1]) > tol and it < maxiter):
            break
    sres = resid / scale if scale != 0.0 else np.zeros_like(resid)
    pd_ = _huber_psi_deriv(sres, t)
    mean_pd, var_pd = float(pd_.mean()), float(pd_.var())
    df_resid, df_model = n - rank, rank - 1
    k = 1 + (df_model + 1) / n * var_pd / mean_pd ** 2
    ncp = np.linalg.pinv(X) @ np.linalg.pinv(X).T
    cov = k ** 2 * (float((_huber_psi(sres, t) ** 2).sum()) / df_resid * scale ** 2) / (pd_.sum() / n) ** 2 * ncp
    bse = np.sqrt(np.diag(cov))
    return dict(params=params, bse=bse, tvalues=params / bse, scale=scale, iterations=it, nobs=n)


def rlm_statsmodels(endog, exog) -> dict:
    """statsmodels RLM(endog, exog) with its defaults (M = HuberT(), fit(): scale_est 'mad', cov 'H1', conv 'dev',
    tol 1e-8, maxiter 50) - the norm Benkarim's code uses by setting none (RUN_PLAN R28 :996-997)."""
    import statsmodels.api as sm
    res = sm.RLM(np.asarray(endog, dtype=float), np.asarray(exog, dtype=float)).fit()
    return dict(params=np.asarray(res.params, dtype=float), bse=np.asarray(res.bse, dtype=float),
                tvalues=np.asarray(res.tvalues, dtype=float), scale=float(res.scale),
                iterations=int(res.fit_history["iteration"]), nobs=int(res.nobs))


def rlm_t(t_values, log2fc, gc) -> dict:
    """R28's RLM of one disorder: endog = the per-gene decoding t, exog = [log2FC, GC %, const]; rows without a finite
    value in a model column dropped and counted; the statsmodels fit asserted equal to the direct IRLS fit (relative
    RLM_TOL on the coefficients and t's; FunctionalDefect otherwise). Returns the t of the log2FC coefficient."""
    M = np.column_stack([np.asarray(t_values, float), np.asarray(log2fc, float), np.asarray(gc, float)])
    ok = np.isfinite(M).all(axis=1)
    endog = M[ok, 0]
    exog = np.column_stack([M[ok, 1], M[ok, 2], np.ones(int(ok.sum()))])
    if endog.size <= exog.shape[1]:
        raise ValueError("RLM: fewer finite rows than model columns")
    sm_ = rlm_statsmodels(endog, exog)
    dr = irls_huber_direct(endog, exog)
    for key in ("params", "tvalues"):
        a, b = sm_[key], dr[key]
        if not np.all(np.abs(a - b) <= RLM_TOL * np.maximum(1.0, np.abs(b))):
            raise AD.FunctionalDefect(f"P17: statsmodels RLM {key} differ from the direct IRLS Huber fit "
                                      f"(max |delta| {float(np.max(np.abs(a - b))):.3g})")
    return dict(t_log2fc=float(sm_["tvalues"][0]), coef_log2fc=float(sm_["params"][0]),
                bse_log2fc=float(sm_["bse"][0]), coefs=[float(v) for v in sm_["params"]],
                tvalues=[float(v) for v in sm_["tvalues"]], scale=sm_["scale"], iterations=sm_["iterations"],
                n_used=int(ok.sum()), n_dropped_nonfinite=int((~ok).sum()),
                direct_fit_max_abs_delta=dict(params=float(np.max(np.abs(sm_["params"] - dr["params"]))),
                                              tvalues=float(np.max(np.abs(sm_["tvalues"] - dr["tvalues"])))),
                exog=["log2FC", "percentage_gene_gc_content", "const"])


def rlm_record(cell_id: str, inputs: Mapping) -> dict:
    """R28's RLM descriptor of one row (ASD, SCZ and BD), beside the published values. inputs['genes']: a DataFrame
    with exactly R28_COLUMNS (gene rows by position; matched upstream by Ensembl id then HGNC, WP5)."""
    df = inputs["genes"]
    if not isinstance(df, pd.DataFrame) or sorted(map(str, df.columns)) != sorted(R28_COLUMNS):
        raise ValueError(f"RLM: the gene table must hold exactly the columns {list(R28_COLUMNS)}")
    out = {}
    for dis in ("ASD", "SCZ", "BD"):
        r = rlm_t(df["t"].to_numpy(float), df[f"{dis}.log2FC"].to_numpy(float),
                  df["percentage_gene_gc_content"].to_numpy(float))
        r["published"] = R28_PUBLISHED.get(cell_id, {}).get(dis)
        out[dis] = r
    return dict(status="computed", reading=R28_RLM_READING, per_disorder=out,
                compared_with="published t (descriptive; TSV reproduction column: no tolerance)",
                inputs={k: v for k, v in (inputs.get("hashes") or {}).items()})


# ================================================================================================================
# 4. synthetic providers (plants only; RUN_PLAN §7 'Data: synthetic maps only')
# ================================================================================================================
SYN_CASE_FORMS = {"weights": 40_000_000, "second_map": 50_000_000, "liu": 60_000_000, "rlm": 70_000_000}
SYN_LIU_CLASS_ID = {"brainspan": 15, "ahba": 16}   # synthetic class ids of the two Liu data kinds (plant seed word)
SYN_LIU_G = 300
SYN_STRUCTURES = ("DFC", "VFC", "MFC", "OFC", "MD", "DTH", "STR", "CBC", "HIP", "AMY", "V1C")
SYN_AGES = ("8 pcw", "9 pcw", "12 pcw", "13 pcw", "16 pcw", "17 pcw", "19 pcw", "21 pcw", "24 pcw", "25 pcw", "26 pcw",
            "35 pcw", "37 pcw", "4 mos", "10 mos", "1 yrs", "2 yrs", "3 yrs", "4 yrs", "8 yrs", "11 yrs", "13 yrs",
            "15 yrs", "18 yrs", "19 yrs", "21 yrs", "23 yrs", "30 yrs", "36 yrs", "37 yrs", "40 yrs")
# a DK-like label table for the synthetic AHBA-like data: abagen's DK ids and names for a subset (public atlas labels)
SYN_DK_TABLE = (
    (1, "bankssts", "L", "cortex"), (4, "cuneus", "L", "cortex"), (6, "fusiform", "L", "cortex"),
    (10, "lateraloccipital", "L", "cortex"), (12, "lingual", "L", "cortex"), (24, "precuneus", "L", "cortex"),
    (35, "thalamusproper", "L", "subcortex/brainstem"), (36, "caudate", "L", "subcortex/brainstem"),
    (40, "hippocampus", "L", "subcortex/brainstem"),
    (42, "bankssts", "R", "cortex"), (45, "cuneus", "R", "cortex"), (47, "fusiform", "R", "cortex"),
    (51, "lateraloccipital", "R", "cortex"), (53, "lingual", "R", "cortex"), (65, "precuneus", "R", "cortex"),
    (76, "thalamusproper", "R", "subcortex/brainstem"), (77, "caudate", "R", "subcortex/brainstem"),
    (81, "hippocampus", "R", "subcortex/brainstem"), (83, "brainstem", "B", "subcortex/brainstem"))
# an ENIGMA-like SD7 label column (hemisphere-split, so not pooled); precuneus and brainstem are not listed
SYN_SD7_LABELS = ("L_bankssts_thickavg", "L_cuneus_thickavg", "L_fusiform_thickavg", "L_lateraloccipital_thickavg",
                  "L_lingual_thickavg", "R_bankssts_thickavg", "R_cuneus_thickavg", "R_fusiform_thickavg",
                  "R_lateraloccipital_thickavg", "R_lingual_thickavg", "Lthal", "Rthal", "Lcaud", "Rcaud", "Lhippo",
                  "Rhippo", "LLatVent", "RLatVent", "LThickness", "RThickness", "ICV")


def synthetic_dk_table() -> pd.DataFrame:
    return pd.DataFrame(list(SYN_DK_TABLE), columns=list(DK_COLUMNS))


def synthetic_gene_weights(src, plan) -> tuple[list, np.ndarray, str]:
    """The row's synthetic S (src._genes_for) with signed weights summing to 2 (some negative)."""
    cls = plan["analysis_class"]
    genes = src._genes_for(plan["row"], cls)
    rng = src._rng(SYN_CASE_FORMS["weights"] + int(plan["row"]), cls)
    w = rng.normal(0.0, 1.0, len(genes))
    w = w + (2.0 - w.sum()) / len(w)
    return list(genes), w, _sha(np.array(genes, dtype=str), w)


def synthetic_second_map(src, plan, map_index: int):
    """A synthetic 'paper's weighted GEDAR map': S's signed weighted score on the class matrix plus noise, on every
    parcel of the class (ids as the class context's)."""
    cls = plan["analysis_class"]
    ctx = src._ctx(cls)
    genes, w, _ = synthetic_gene_weights(src, plan)
    idx = [ctx.U.index[g] for g in genes]
    b = ctx.X[:, idx] @ w / w.sum()
    rng = src._rng(SYN_CASE_FORMS["second_map"] * (int(map_index) + 1) + int(plan["row"]), cls)
    b = b + 0.3 * float(np.std(b)) * rng.standard_normal(b.size)
    ids = np.asarray(ctx.parcel_ids, dtype=np.int64)
    return b, ids, _sha(b, ids)


def synthetic_liu_frames(rng, data: str) -> tuple[dict, list]:
    """(inputs, planted sample ids). BrainSpan-like: 66 samples x 300 genes (+ 3 NaN columns, 1 inf column, 2 constant
    columns, and 2 duplicate columns re-using two symbols, one of them a member of S), ages and structure acronyms,
    handed over as RPKM (scale 'RPKM'; log2(RPKM + 1) is the drawn value rounded to 1 decimal, so ties within samples);
    AHBA-like (scale 'abagen'): 128 samples labelled by the DK ids of SYN_DK_TABLE (4 samples unassigned), the DK table
    and an ENIGMA-like SD7 label column (SYN_SD7_LABELS). S: 25 genes of the matrix, 1 NaN-column gene, 1 constant gene
    and 2 genes absent from the data. The sample ids are planted on the frame and metadata index (the adapter must drop
    them at once)."""
    genes = [f"lg{j:04d}" for j in range(SYN_LIU_G)]
    n = 66 if data == "brainspan" else 128
    ids = ["SYNSID-%s" % int(rng.integers(0, 2 ** 48)).to_bytes(6, "big").hex() for _ in range(n)]
    nan_cols, inf_col, const_cols = [10, 11, 12], 13, [14, 15]
    special = set(nan_cols) | {inf_col} | set(const_cols)
    S_core = sorted(rng.choice([g for j, g in enumerate(genes) if j not in special], 25, replace=False).tolist())
    lvl = rng.normal(5, 1.5, SYN_LIU_G)
    fac = rng.normal(0, 1, (n, 3)) @ rng.normal(0, 0.6, (3, SYN_LIU_G))
    X = lvl[None, :] + fac + rng.normal(0, 1.0, (n, SYN_LIU_G))
    sidx = [genes.index(g) for g in S_core]
    cols = list(genes)
    if data == "brainspan":
        ages = [SYN_AGES[k % len(SYN_AGES)] for k in range(n)]
        structs = [SYN_STRUCTURES[k % len(SYN_STRUCTURES)] for k in range(n)]
        pre = np.array([a.endswith(" pcw") for a in ages])
        X[np.ix_(pre, sidx)] += 0.8
        thal = np.array([s in ("MD", "DTH") for s in structs])
        X[np.ix_(thal, sidx)] -= 0.5
        meta = pd.DataFrame({"age": ages, "structure_acronym": structs}, index=ids)
        X = np.round(np.clip(X, 0.0, None), 1)
        dup_of = [sidx[0], [j for j in range(SYN_LIU_G) if j not in special and j not in sidx][0]]
        D = np.round(np.clip(X[:, dup_of] + rng.normal(0, 0.5, (n, 2)), 0.0, None), 1)
        X = np.column_stack([X, D])
        cols = genes + [genes[j] for j in dup_of]
        extra = dict(scale="RPKM")
    else:
        dk = synthetic_dk_table()
        labels = [int(SYN_DK_TABLE[k % len(SYN_DK_TABLE)][0]) for k in range(n)]
        for k in (5, 40, 77, 101):
            labels[k] = None
        hip_ids = {int(r[0]) for r in SYN_DK_TABLE if r[1] == "hippocampus"}
        hip = np.array([lb in hip_ids for lb in labels])
        X[np.ix_(hip, sidx)] += 0.7
        X = np.round(X, 1)
        meta = pd.DataFrame({"label": pd.Series(labels, index=ids, dtype=object)})
        extra = dict(scale="abagen", dk_table=dk, sd7_labels=list(SYN_SD7_LABELS))
    for j in nan_cols:
        X[rng.integers(n), j] = np.nan
    X[rng.integers(n), inf_col] = np.inf
    for j in const_cols:
        X[:, j] = 3.0
    if data == "brainspan":
        with np.errstate(over="ignore"):
            X = np.exp2(X) - 1.0   # RPKM: log2(RPKM + 1) is the drawn value (inf / NaN stay non-finite)
    S = S_core + [genes[nan_cols[0]], genes[const_cols[0]], "lgABSENT1", "lgABSENT2"]
    expr = pd.DataFrame(X, index=ids, columns=cols)
    brain = sorted(rng.choice(genes, 60, replace=False).tolist())
    t = np.linspace(0, 1, 8)
    tl = rng.normal(5, 1.5, SYN_LIU_G)[:, None] + rng.normal(0, 1.5, SYN_LIU_G)[:, None] * t \
        + 0.1 * rng.standard_normal((SYN_LIU_G, 8))
    traj = pd.DataFrame(tl, index=genes, columns=[f"bin{k}" for k in range(8)]).iloc[: SYN_LIU_G - 20]
    hashes = {"expr": _sha(X, np.array(cols, dtype=str)), "meta": _sha(np.array(meta.astype(str).to_numpy(), dtype=str)),
              "set": _sha(np.array(S, dtype=str)), "brain": _sha(np.array(brain, dtype=str)),
              "traj": _sha(traj.to_numpy())}
    if data == "ahba":
        hashes["dk_table"] = _sha(np.array(extra["dk_table"].astype(str).to_numpy(), dtype=str))
        hashes["sd7_labels"] = _sha(np.array(extra["sd7_labels"], dtype=str))
    inputs = dict(data=data, expr=expr, meta=meta, set=S, brain=brain, traj=traj, hashes=hashes, **extra)
    return inputs, ids


def _syn_rng(src, word: int, class_id: int):
    """A synthetic data generator of the sources' plant (and plant case, when the sources carry one): the sources'
    own convention (run.SyntheticSources._rng) for a class id outside its class table."""
    case = getattr(src, "case", None)
    if case is None:
        return np.random.default_rng(SD.plant_seed(src.plant_id, word, class_id))
    return np.random.default_rng(SD.plant_data_seed(src.plant_id, case, class_id, word))


def synthetic_liu_inputs(src, plan) -> dict:
    spec = plan["liu_spec"]
    rng = _syn_rng(src, SYN_CASE_FORMS["liu"] + int(plan["row"]), SYN_LIU_CLASS_ID[spec["data"]])
    return synthetic_liu_frames(rng, spec["data"])[0]


def synthetic_liu_ids(src, plan) -> list:
    """The ids synthetic_liu_inputs plants for this plan (tests grep every output for them)."""
    spec = plan["liu_spec"]
    rng = _syn_rng(src, SYN_CASE_FORMS["liu"] + int(plan["row"]), SYN_LIU_CLASS_ID[spec["data"]])
    return synthetic_liu_frames(rng, spec["data"])[1]


def synthetic_rlm_inputs(src, plan) -> dict:
    """400 synthetic genes: decoding t = 2 + 6 log2FC - 0.04 GC + heavy-tailed noise; 7 rows with a NaN in a model
    column (dropped and counted)."""
    rng = _syn_rng(src, SYN_CASE_FORMS["rlm"] + int(plan["row"]), 2)
    n = 400
    asd = rng.normal(0, 0.3, n)
    gc = rng.uniform(35, 65, n)
    tv = 2 + 6 * asd - 0.04 * gc + stats.t.rvs(3, size=n, random_state=rng)
    df = pd.DataFrame({"t": tv, "ASD.log2FC": asd, "SCZ.log2FC": 0.5 * asd + rng.normal(0, 0.3, n),
                       "BD.log2FC": rng.normal(0, 0.3, n), "percentage_gene_gc_content": gc})
    for k, c in zip(range(7), ("t", "ASD.log2FC", "SCZ.log2FC", "BD.log2FC", "percentage_gene_gc_content", "t", "t")):
        df.iloc[3 + 11 * k, df.columns.get_loc(c)] = np.nan
    return dict(genes=df, hashes={"genes": _sha(df.to_numpy())})
