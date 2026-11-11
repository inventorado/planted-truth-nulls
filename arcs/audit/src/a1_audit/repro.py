"""A1 reproduction functionals (arcs/audit/RUN_PLAN.md v3.1 FROZEN: R13, R14, R22, R27, R28, R30; plant P17 in
`tests/test_repro_p17.py`). Pure functions of arrays and gene-name collections: nothing here opens a file, a carrier, a
map or a network resource, and nothing here chooses a claim, a direction or a verdict.

Functionals (each is a reproduction descriptor; none enters a verdict):

- R13 (Patel's mean bicor): `bicor`, `bicor_columns`, `mean_bicor`. The biweight midcorrelation with WGCNA's defaults
  as R13 pins them: bicor(x, y, robustX = TRUE, robustY = TRUE, maxPOutliers = 1, pearsonFallback = "individual");
  u = (x - med x) / (9 MAD x) with MAD the RAW median absolute deviation; weights (1 - u^2)^2 for |u| < 1, else 0; the
  weighted, median-centred vector normalised to unit length; bicor = the inner product of the two. A column with MAD 0
  "falls back to Pearson" (R13): that column is mean-centred and normalised (WGCNA's "individual" fallback acts per
  column; the other column keeps its biweight form). Only maxPOutliers = 1 and pearsonFallback = "individual" are
  implemented (R13's pinned values); any other value is refused. A constant column is refused (bicor undefined).
- R27 (Giacomel): `gedar_abs_score`, `gedar_abs_rho`. "rho of the |z|-weighted GEDAR score"
  (claims_register.md:319): score_p = sum_g |z_g| X[p, g] / sum_g |z_g| over S's genes; rho = Spearman(y, score).
  Spearman is computed from integer rank terms (adapters.rank_corr_terms: doubled average ranks centred by n + 1, so
  the rank arithmetic is exact) and one final float division. The signed-weight score of the descriptor rows is P15's
  adapter, not this one.
- R27 (Liu T3) / R10 (T4, T5): `rank_biserial`, `rank_biserial_rows`, `liu_t3_rho`, `label_mean_rank_biserial`. The
  rank-biserial r of S against the rest, (U1 - U2) / (n1 n2), from adapters.rank_biserial_terms (exact numerator and
  denominator in Python integers; ties take average ranks); per parcel (T3: rho(y, per-parcel r)) or per sample with a
  label's value = the mean over its samples (R10).
- R14 (per-donor recipe): `per_donor_slopes`, `per_donor_recipe_t`, `decoded_lists`. Per gene and donor, the OLS slope
  of expression on y over that donor's parcels with a finite value; a donor with fewer than 3 such parcels is dropped
  for that gene and counted; a one-sample t over the donors kept (df = donors kept - 1); BH across genes. The per-gene
  p is TWO-SIDED, p = 2 sf(|t|, df) ("pFDR < .01, split by sign", TSV rows 523-526), pinned by RUN_PLAN_amend_2 R38
  ("R14's per-gene p is two-sided ... as repro.py reads it") and asserted at every call (R14_SIDEDNESS).
  A gene with fewer than 2 donors kept, or a non-finite t, is not tested (counted; outside the BH family and outside
  R30's universe, "HGNC genes with a finite t").
- R40 (differential stability for Benkarim and Park; RUN_PLAN_amend_2 R40): `benkarim_ds_genes`, `park_ds_genes`. The
  DS vector is R12's (abagen.correct.keep_stable_genes on the per-donor V-DK matrices' 34 left DK cortical parcels,
  ahba_extras.r12_ds; read with its hash by ahba_extras.load_r12_ds). Benkarim: R12's vector (its hash asserted equal to
  R12's), kept iff DS >= .5. Park: kept iff DS > .5, on the decoder output's own DS column if it carries one, else on
  R12's vector (also the per-donor fallback, R28); decoder genes absent from R12's vector, or with a non-finite DS,
  are excluded and counted.
- R22 (Segura's over-representation analysis): `ora`, `fisher_counts`, `bh`. Fisher's exact test per term with the
  one-sided (over-representation, P(X >= a)) and the two-sided p (the standard definition: the sum of the
  probabilities of every table no more probable than the observed one; scipy.stats.fisher_exact), BH across the terms
  tested, separately for each sidedness. The primary sidedness follows PANTHER_SIDEDNESS (below): unverified, so the
  two-sided p is primary and every output carries the label "PANTHER sidedness unverified" (R22's rule).
- R28 (BENK-C2, PARK-C5): `rlm_log2fc_t` delegates to forms.rlm_t, the production RLM (statsmodels RLM with its
  defaults: HuberT(t = 1.345), scale_est = "mad", cov = "H1", conv = "dev", tol = 1e-8, maxiter = 50; the reported
  value is tvalues[0], the log2FC coefficient's t). `huber_irls` is an independent direct iteratively reweighted Huber
  fit written here (statsmodels' stopping rule replicated, or iterated to a fixed point); P17 compares statsmodels,
  forms.irls_huber_direct and huber_irls.
- R30 (Pretzsch's overlap test): `overlap_test`. Fisher's exact test of the re-derived list against the set in the
  direction GeneOverlap's testGeneOverlap runs it, GENEOVERLAP (below; read from the package source in the R image,
  `rbuild/`), on the primary universe (the genes the per-donor recipe tested; list and set intersected with it), and
  beside it on GeneOverlap's own construction with its default genome size.

Readings this module had to make where the frozen text is silent are listed in IMPLEMENTATION_READINGS (each is
reported as a gap to the orchestrator; none changes a registered definition).
"""
from __future__ import annotations

import math
from fractions import Fraction

import numpy as np
from scipy import stats

from .adapters import rank_biserial_terms, rank_corr_terms

# ================================================================================================================
# records fixed before WP3 (R22) and read from the R image's package source (R30)
# ================================================================================================================
PANTHER_SIDEDNESS = dict(
    reading="R22: the primary is the sidedness PANTHER's own documentation states; if no PANTHER document states it, "
            "the two-sided p is primary and the output is labelled 'PANTHER sidedness unverified'",
    fetched_utc="2026-10-01",
    sources=[
        dict(url="https://www.pantherdb.org/help/PANTHERhelp.jsp",
             result="HTTP 403 (Cloudflare challenge, header Cf-Mitigated: challenge); not readable by script; "
                    "not circumvented. Same for https://pantherdb.org/help/PANTHERhelp.jsp, "
                    "https://www.pantherdb.org/tips/tips_statistics.jsp, "
                    "https://www.pantherdb.org/news/news20171205.jsp, https://pantherdb.org/services/details.jsp"),
        dict(url="https://academic.oup.com/nar/article/47/D1/D419/5165346",
             what="PANTHER version 14 (NAR 2019; the PANTHER team's release paper)",
             quotes=["the overrepresentation test now uses Fisher's exact test by default, rather than the binomial "
                     "test",
                     "performs a statistical test for over- and underrepresentation: is a given (functional) class "
                     "found statistically more (or less) often in the input list, than expected by chance?"],
             result="no statement of one- or two-sidedness"),
        dict(url="https://academic.oup.com/nar/article/49/D1/D394/6027812",
             what="PANTHER version 16 (NAR 2021; the PANTHER team's release paper)",
             quotes=["Fisher's Exact test with option of FDR or Bonferroni correction",
                     "compare a list of genes to a reference list to statistically determine over- or "
                     "under-representation of a specified ontology class"],
             result="no statement of one- or two-sidedness"),
        dict(url="https://github.com/pantherdb/pantherapi-pyclient",
             what="PANTHER's own API client README (pantherdb GitHub organisation)",
             quotes=["FISHER (for Fisher's Exact test) or BINOMIAL (for binomial distribution test)"],
             result="no statement of one- or two-sidedness"),
    ],
    finding="unverified: no PANTHER document read states the sidedness of the overrepresentation test's Fisher p; "
            "PANTHER's help pages could not be read (HTTP 403, Cloudflare challenge). 2026-10-11: the operator read the "
            "PANTHER help page in a browser (FAQ/Help/Tutorial; text pasted into the session): it does not state the sidedness "
            "either. PANTHER's own API "
            "output is reproduced exactly by the TWO-sided Fisher p (empirical_check below), which agrees with this "
            "primary; R22's label stays because no PANTHER document states it",
    primary="two-sided",
    label="PANTHER sidedness unverified",
    # 2026-10-11 (orchestrator; a1_audit/panther_sidedness_check.py; evidence run_manifests/R22_panther/): PANTHER 19.0's
    # public API (curl; not circumvented) on a toy list of 15 everyday human genes (no audit material). Every reported
    # raw p recomputed on [[a, n - a], [K - a, N - K - (n - a)]] (reference includes the list, as fisher_counts builds
    # it; n 16 mapped, N 20,580, both from PANTHER's expected values).
    empirical_check=dict(
        date="2026-10-11", script="a1_audit/panther_sidedness_check.py", evidence="run_manifests/R22_panther/",
        panther_release="PANTHER version 19.0 Released 2024-06-20", tolerance_rel=1e-9,
        panther_pathway=dict(rows=160, two_sided_reproduced=160, one_sided_reproduced=23, discriminating_rows=14,
                             response_sha256="1ce9f7203f8232e9f1a891bc59e7025e9f0cfccc78ffd846db121edfe2b49f70"),
        go_bp=dict(rows=13761, two_sided_reproduced=13761, one_sided_reproduced=1048, discriminating_rows=1055),
        result="PANTHER's overrepresentation Fisher p is two-sided, with the reference including the list",
    ),
)

# GeneOverlap (Bioconductor) facts used by R30, read from the package source in the R image (rbuild/; image manifest
# sha256:dddaa4689efa0baa712ea647fa2086cc8438a28d114b0f011980d1c5479af32e, config sha256:9fe7ce75f4083beec8741770942c58
# 13450a705d6ac4d1e1f289c8988888efce; built 2026-10-01; rbuild/image_lock.json). The deparsed
# namespace is kept as rbuild/logs/geneoverlap_1.42.0_source.txt (sha256 180c0a1729c59327ddce63fef82ccc53d66b556b7600f2d5
# dcb213d89857af98). The P17 Docker check `P17.geneoverlap_docker` re-reads both facts from the image and fails on any
# difference. Quoted:
#   newGeneOverlap: function (listA, listB, genome.size = NULL, spec = c("mm9.gene", "hg19.gene", "rn4.gene")) ...
#       genome.size <- switch(spec, mm9.gene = 23000, hg19.gene = 25000, rn4.gene = 17000)
#   testGeneOverlap: object@cont.tbl <- matrix(c(object@genome.size - length(object@union),
#       sizeB - length(object@intersection), sizeA - length(object@intersection), length(object@intersection)), ncol = 2)
#       res.fisher <- try(fisher.test(object@cont.tbl, alternative = "greater"), silent = TRUE)
#       object@odds.ratio <- setNames(res.fisher$estimate, NULL)   (the conditional MLE)
# NB: the default genome size is the FIRST spec choice, "mm9.gene" = 23,000 (a mouse gene count); hg19.gene is 25,000.
GENEOVERLAP = dict(
    package_version="1.42.0",
    alternative="greater",
    default_spec="mm9.gene",
    default_genome_size=23000,
    odds_ratio="fisher.test estimate (conditional MLE)",
    image_manifest="sha256:dddaa4689efa0baa712ea647fa2086cc8438a28d114b0f011980d1c5479af32e",
    status="read from GeneOverlap 1.42.0 source in the R image (manifest sha256:dddaa4689efa...; Bioconductor 3.20)",
)

IMPLEMENTATION_READINGS = (
    "R14: the per-gene p of the one-sample t is two-sided (from 'pFDR < .01, split by sign'); pinned by "
    "RUN_PLAN_amend_2 R38.",
    "R14: a gene with < 2 donors kept (t undefined) or a non-finite t is not tested: outside BH and outside R30's "
    "universe ('HGNC genes with a finite t').",
    "R14: a donor-gene pair whose y has zero variance over that donor's finite parcels has no slope (dropped, counted).",
    "R22: list genes outside the reference are dropped and counted; terms are intersected with the reference; a term "
    "with no reference gene is not tested (outside the BH family, counted).",
    "R30: on the primary universe the set is intersected with the universe; the decoded list must lie inside it "
    "(asserted).",
    "R13: a constant column (MAD 0 and zero variance) is refused (bicor undefined; WGCNA returns NA).",
)

R14_SIDEDNESS = "two-sided, p = 2 sf(|t|, df) ('pFDR < .01, split by sign'; RUN_PLAN_amend_2 R38)"
R13_DEFAULTS = dict(robustX=True, robustY=True, maxPOutliers=1, pearsonFallback="individual")
BICOR_MAD_SCALE = 9.0
HUBER_T = 1.345


# ================================================================================================================
# R13: biweight midcorrelation (WGCNA defaults)
# ================================================================================================================
def _finite_1d(v, what: str) -> np.ndarray:
    a = np.asarray(v, dtype=np.float64)
    if a.ndim != 1 or a.size < 2 or not np.isfinite(a).all():
        raise ValueError(f"{what}: a finite 1-D vector of length >= 2 is required")
    return a


def bicor_prepare(v, *, _mad_constant: float = 1.0) -> tuple[np.ndarray, str]:
    """The unit-length column of v that enters bicor, and its mode ('biweight' | 'pearson-fallback').
    _mad_constant: PLANT ONLY (1.4826 = R's mad() default, the must-differ variant of the raw MAD R13 pins)."""
    a = _finite_1d(v, "bicor column")
    med = np.median(a)
    mad = np.median(np.abs(a - med)) * _mad_constant
    if mad == 0:
        c = a - a.mean()
        mode = "pearson-fallback"
    else:
        u = (a - med) / (BICOR_MAD_SCALE * mad)
        w = np.where(np.abs(u) < 1.0, (1.0 - u * u) ** 2, 0.0)
        c = (a - med) * w
        mode = "biweight"
    nrm = math.sqrt(float(np.dot(c, c)))
    if not nrm > 0:
        raise ValueError("bicor: a constant column (bicor undefined)")
    return c / nrm, mode


def _check_defaults(max_p_outliers, pearson_fallback) -> None:
    if max_p_outliers != 1 or pearson_fallback != "individual":
        raise NotImplementedError("bicor: only R13's pinned maxPOutliers = 1, pearsonFallback = 'individual' exist here")


def bicor(x, y, *, max_p_outliers: float = 1, pearson_fallback: str = "individual") -> float:
    """WGCNA::bicor(x, y) at R13's pinned defaults (module docstring)."""
    _check_defaults(max_p_outliers, pearson_fallback)
    a, _ = bicor_prepare(x)
    b, _ = bicor_prepare(y)
    if a.size != b.size:
        raise ValueError("bicor: vectors of different length")
    return float(np.dot(a, b))


def bicor_columns(y, X, *, max_p_outliers: float = 1, pearson_fallback: str = "individual") -> np.ndarray:
    """bicor(y, X[:, g]) for every column g (parcels x genes), vectorised; equals the scalar `bicor` (P17)."""
    _check_defaults(max_p_outliers, pearson_fallback)
    b, _ = bicor_prepare(y)
    M = np.asarray(X, dtype=np.float64)
    if M.ndim != 2 or M.shape[0] != b.size or not np.isfinite(M).all():
        raise ValueError("bicor_columns: a finite parcels x genes matrix matching y is required")
    med = np.median(M, axis=0)
    mad = np.median(np.abs(M - med), axis=0)
    fb = mad == 0
    safe = np.where(fb, 1.0, mad)
    U = (M - med) / (BICOR_MAD_SCALE * safe)
    C = np.where(np.abs(U) < 1.0, (1.0 - U * U) ** 2, 0.0) * (M - med)
    if fb.any():
        C[:, fb] = M[:, fb] - M[:, fb].mean(axis=0)
    nrm = np.sqrt((C * C).sum(axis=0))
    if not (nrm > 0).all():
        raise ValueError("bicor_columns: a constant column (bicor undefined)")
    return (C / nrm).T @ b


def mean_bicor(y, X, genes=None) -> dict:
    """Patel's functional (R13): the mean over the panel's genes (columns of X, or the `genes` index subset) of
    bicor(y, gene). Returns the mean and the per-gene values' count and fallback count."""
    M = np.asarray(X, dtype=np.float64)
    if genes is not None:
        M = M[:, np.asarray(genes)]
    v = bicor_columns(y, M)
    n_fb = int((np.median(np.abs(M - np.median(M, axis=0)), axis=0) == 0).sum())
    return dict(mean_bicor=float(v.mean()), n_genes=int(v.size), n_pearson_fallback_columns=n_fb,
                defaults=dict(R13_DEFAULTS), mad="raw median absolute deviation (R13)")


# ================================================================================================================
# Spearman rho from exact rank terms (shared by R27's functionals)
# ================================================================================================================
def spearman_exact(a, b) -> float:
    """Spearman rho as N / sqrt(Q) from adapters.rank_corr_terms (integer rank arithmetic, average ranks for ties)."""
    a, b = _finite_1d(a, "spearman a"), _finite_1d(b, "spearman b")
    if a.size != b.size:
        raise ValueError("spearman: vectors of different length")
    N, Q = rank_corr_terms(a, b)
    if Q[0] <= 0:
        raise ValueError("spearman: a constant rank vector (rho undefined)")
    return N[0] / math.sqrt(Q[0])


# ================================================================================================================
# R27: Giacomel's |z|-weighted GEDAR score and its rho
# ================================================================================================================
def gedar_abs_score(X, z, genes=None) -> np.ndarray:
    """score_p = sum_g |z_g| X[p, g] / sum_g |z_g| over the columns `genes` (default: all) of X (parcels x genes);
    z carries one value per column of X."""
    M = np.asarray(X, dtype=np.float64)
    w = np.abs(np.asarray(z, dtype=np.float64))
    if M.ndim != 2 or w.shape != (M.shape[1],):
        raise ValueError("gedar_abs_score: one weight per column of X")
    if genes is not None:
        idx = np.asarray(genes)
        M, w = M[:, idx], w[idx]
    if M.ndim != 2 or w.shape != (M.shape[1],) or not (np.isfinite(M).all() and np.isfinite(w).all()):
        raise ValueError("gedar_abs_score: a finite parcels x genes matrix and one finite weight per gene")
    sw = float(w.sum())
    if not sw > 0:
        raise ValueError("gedar_abs_score: the weights sum to 0")
    return (M @ w) / sw


def gedar_abs_rho(y, X, z, genes=None) -> dict:
    s = gedar_abs_score(X, z, genes)
    n_genes = np.asarray(z).size if genes is None else np.asarray(genes).size
    return dict(rho=spearman_exact(y, s), score=s, n_parcels=int(s.size), n_genes=int(n_genes),
                weighting="|z|-weighted mean (claims_register.md:319)")


# ================================================================================================================
# R27 / R10: rank-biserial r (Liu T3 / T4 / T5)
# ================================================================================================================
def rank_biserial(values, in_group) -> float:
    num, den = rank_biserial_terms(values, in_group)
    return num / den


def rank_biserial_fraction(values, in_group) -> Fraction:
    num, den = rank_biserial_terms(values, in_group)
    return Fraction(num, den)


def rank_biserial_rows(X, in_group) -> np.ndarray:
    """The rank-biserial r of the genes in `in_group` (boolean over columns) against the rest, for every row of X
    (parcels or samples x genes); each row's genes ranked by that row's values."""
    M = np.asarray(X, dtype=np.float64)
    g = np.asarray(in_group, dtype=bool)
    if M.ndim != 2 or g.shape != (M.shape[1],):
        raise ValueError("rank_biserial_rows: a rows x genes matrix and one group flag per gene")
    return np.array([rank_biserial(M[i], g) for i in range(M.shape[0])], dtype=float)


def liu_t3_rho(y, X, in_group) -> dict:
    """LIU-T3's comparator (claims_register.md:1677-1679): Spearman rho of y with the per-parcel rank-biserial
    enrichment of S (rows of X = parcels, aligned with y)."""
    r = rank_biserial_rows(X, in_group)
    return dict(rho=spearman_exact(y, r), per_parcel_r=r, n_parcels=int(r.size), n_in_group=int(np.sum(in_group)))


def label_mean_rank_biserial(X_samples, labels, in_group) -> dict:
    """R10 (T4 / T5): each sample's rank-biserial r of S against the rest; a label's value = the mean over its samples.
    Sample rows are positional only (no sample id enters or leaves). Returns {label: (mean r, n samples)}."""
    r = rank_biserial_rows(X_samples, in_group)
    lab = np.asarray(labels)
    if lab.shape != (r.size,):
        raise ValueError("label_mean_rank_biserial: one label per sample row")
    out = {}
    for L in sorted(set(lab.tolist())):
        m = lab == L
        out[L] = (float(r[m].mean()), int(m.sum()))
    return out


# ================================================================================================================
# BH (R14, R22)
# ================================================================================================================
def bh(p) -> np.ndarray:
    """Benjamini-Hochberg q-values (step-up; q_(i) = min_{j >= i} m p_(j) / j, capped at 1). Non-finite entries are
    outside the family (m = the finite count) and stay NaN."""
    p = np.asarray(p, dtype=np.float64)
    q = np.full(p.shape, np.nan)
    ok = np.isfinite(p)
    if not ok.any():
        return q
    pv = p[ok]
    if (pv < 0).any() or (pv > 1).any():
        raise ValueError("bh: p outside [0, 1]")
    m = pv.size
    order = np.argsort(pv, kind="mergesort")
    ranked = pv[order] * m / np.arange(1, m + 1)
    qs = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(qs, 1.0)
    q[ok] = out
    return q


# ================================================================================================================
# R14: per-donor recipe t
# ================================================================================================================
MIN_DONOR_PARCELS = 3  # R14: "a donor with fewer than 3 such parcels is dropped and reported"


def per_donor_slopes(y, donor_mats, min_parcels: int = MIN_DONOR_PARCELS) -> dict:
    """Per gene and donor, the OLS slope of expression on y over that donor's parcels with a finite value.
    y: (P,) finite; donor_mats: sequence of (P, G) arrays (NaN = no sample in that parcel for that donor).
    Returns slopes (D, G) with NaN where dropped, the per-pair parcel counts, and the drop counts."""
    yv = _finite_1d(y, "per-donor recipe y")
    mats = [np.asarray(M, dtype=np.float64) for M in donor_mats]
    if not mats:
        raise ValueError("per_donor_slopes: no donor")
    P, G = mats[0].shape
    if P != yv.size or any(M.shape != (P, G) for M in mats):
        raise ValueError("per_donor_slopes: every donor matrix must be parcels x genes, aligned with y")
    D = len(mats)
    slopes = np.full((D, G), np.nan)
    counts = np.zeros((D, G), dtype=np.int64)
    dropped_few = np.zeros(D, dtype=np.int64)
    dropped_flat_y = np.zeros(D, dtype=np.int64)
    for d, M in enumerate(mats):
        F = np.isfinite(M)
        n = F.sum(axis=0)
        counts[d] = n
        Yb = np.where(F, yv[:, None], 0.0)
        Xb = np.where(F, M, 0.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            ybar = Yb.sum(axis=0) / n
            xbar = Xb.sum(axis=0) / n
            dy = np.where(F, yv[:, None] - ybar, 0.0)
            dx = np.where(F, M - xbar, 0.0)
            syy = (dy * dy).sum(axis=0)
            sxy = (dy * dx).sum(axis=0)
            b = sxy / syy
        few = n < int(min_parcels)
        flat = (~few) & ~(syy > 0)
        b[few | flat] = np.nan
        slopes[d] = b
        dropped_few[d] = int(few.sum())
        dropped_flat_y[d] = int(flat.sum())
    return dict(slopes=slopes, parcel_counts=counts, dropped_lt_min_parcels=dropped_few,
                dropped_flat_y=dropped_flat_y, min_parcels=int(min_parcels), n_donors=D, n_genes=G)


def per_donor_recipe_t(y, donor_mats, min_parcels: int = MIN_DONOR_PARCELS) -> dict:
    """R14: the one-sample t of the per-donor slopes (df = donors kept - 1), its two-sided p, BH across the genes
    tested. A gene with < 2 donors kept or a non-finite t is not tested (NaN p and q; counted)."""
    sl = per_donor_slopes(y, donor_mats, min_parcels)
    S = sl["slopes"]
    k = np.isfinite(S).sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean = _nanmean(S)
        sd = _nanstd1(S)
        t = mean / (sd / np.sqrt(k))
    df = (k - 1).astype(float)
    tested = (k >= 2) & np.isfinite(t)
    p = np.full(t.shape, np.nan)
    p[tested] = 2.0 * stats.t.sf(np.abs(t[tested]), df[tested])
    # RUN_PLAN_amend_2 R38: R14's per-gene p is two-sided; asserted against 2 min(cdf, sf) of the signed t
    alt = np.minimum(1.0, 2.0 * np.minimum(stats.t.cdf(t[tested], df[tested]), stats.t.sf(t[tested], df[tested])))
    if not np.allclose(p[tested], alt, rtol=1e-9, atol=0.0):
        raise AssertionError("R38: R14's per-gene p is not the two-sided p 2 sf(|t|, df)")
    q = bh(p)
    t_out = np.where(tested, t, np.nan)
    return dict(t=t_out, df=np.where(tested, df, np.nan), p_two_sided=p, q_bh=q, n_donors_kept=k,
                tested=tested, n_tested=int(tested.sum()), n_not_tested=int((~tested).sum()),
                n_not_tested_lt2_donors=int((k < 2).sum()),
                n_not_tested_nonfinite_t=int(((k >= 2) & ~np.isfinite(t)).sum()),
                slopes=sl, sidedness=R14_SIDEDNESS)


def _nanmean(S: np.ndarray) -> np.ndarray:
    F = np.isfinite(S)
    k = F.sum(axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(F, S, 0.0).sum(axis=0) / k


def _nanstd1(S: np.ndarray) -> np.ndarray:
    F = np.isfinite(S)
    k = F.sum(axis=0)
    m = _nanmean(S)
    with np.errstate(invalid="ignore", divide="ignore"):
        dev = np.where(F, S - m, 0.0)
        return np.sqrt((dev * dev).sum(axis=0) / (k - 1))


def decoded_lists(recipe: dict, q_threshold: float = 0.01) -> dict:
    """The decoded list by R14's rule: q_BH < threshold (TSV rows 523-526: pFDR < .01), split by the sign of t.
    Returns column indices {+1: [...], -1: [...]} and the universe (the genes tested, R30's primary universe)."""
    q, t = recipe["q_bh"], recipe["t"]
    sel = np.isfinite(q) & (q < q_threshold)
    return {1: np.flatnonzero(sel & (t > 0)), -1: np.flatnonzero(sel & (t < 0)),
            "universe": np.flatnonzero(recipe["tested"]), "q_threshold": q_threshold}


# ================================================================================================================
# R22: Fisher + BH over-representation analysis
# ================================================================================================================
def fisher_counts(list_genes, term_genes, reference) -> dict:
    """2 x 2 counts of a list against a term inside a reference: a = |L & T|, b = |L - T|, c = |T - L|,
    d = |R| - a - b - c, with L = list & R (genes outside R dropped and counted) and T = term & R."""
    R = set(reference)
    L0 = set(list_genes)
    L = L0 & R
    T = set(term_genes) & R
    a = len(L & T)
    b = len(L) - a
    c = len(T) - a
    d = len(R) - a - b - c
    if min(a, b, c, d) < 0:
        raise ValueError("fisher_counts: negative cell")
    return dict(a=a, b=b, c=c, d=d, n_list=len(L), n_term=len(T), n_reference=len(R),
                list_dropped_outside_reference=len(L0 - R))


def fisher_p(a: int, b: int, c: int, d: int) -> dict:
    """One-sided (greater: P(X >= a), over-representation) and two-sided Fisher p of [[a, b], [c, d]] (rows: in list /
    not; columns: in term / not), the sample odds ratio and the conditional MLE odds ratio (R's fisher.test estimate)."""
    tbl = np.array([[a, b], [c, d]], dtype=np.int64)
    p_g = float(stats.hypergeom.sf(a - 1, a + b + c + d, a + c, a + b))
    p_two = float(stats.fisher_exact(tbl, alternative="two-sided").pvalue)
    p_g_scipy = float(stats.fisher_exact(tbl, alternative="greater").pvalue)
    sample_or = (a * d / (b * c)) if b * c > 0 else (math.inf if a * d > 0 else math.nan)
    try:
        cond_or = float(stats.contingency.odds_ratio(tbl, kind="conditional").statistic)
    except Exception:  # noqa: BLE001 - degenerate margins: reported as NaN, never a p
        cond_or = math.nan
    return dict(p_greater=p_g, p_greater_fisher_exact=p_g_scipy, p_two_sided=p_two, odds_ratio_sample=sample_or,
                odds_ratio_conditional_mle=cond_or)


def ora(list_genes, terms: dict, reference, *, sidedness: dict = PANTHER_SIDEDNESS) -> dict:
    """R22: Fisher's exact test of the list against every term (dict name -> genes) inside the reference; BH across the
    terms tested, separately for the one-sided and the two-sided p; the primary per `sidedness` (R22's rule)."""
    per, tested = {}, []
    not_tested = 0
    for name in terms:
        cnt = fisher_counts(list_genes, terms[name], reference)
        if cnt["n_term"] == 0:
            not_tested += 1
            per[name] = dict(cnt, status="not tested (no reference gene)")
            continue
        fp = fisher_p(cnt["a"], cnt["b"], cnt["c"], cnt["d"])
        expected = cnt["n_list"] * cnt["n_term"] / cnt["n_reference"]
        per[name] = dict(cnt, **fp, expected=expected,
                         fold_enrichment=(cnt["a"] / expected) if expected > 0 else math.nan,
                         direction="+" if cnt["a"] > expected else ("-" if cnt["a"] < expected else "0"),
                         status="tested")
        tested.append(name)
    q_g = bh([per[n]["p_greater"] for n in tested]) if tested else []
    q_2 = bh([per[n]["p_two_sided"] for n in tested]) if tested else []
    primary = sidedness["primary"]
    if primary not in ("two-sided", "one-sided (greater)"):
        raise ValueError(f"ora: unknown primary sidedness {primary!r}")
    for i, n in enumerate(tested):
        per[n]["q_greater"] = float(q_g[i])
        per[n]["q_two_sided"] = float(q_2[i])
        per[n]["p_primary"] = per[n]["p_two_sided"] if primary == "two-sided" else per[n]["p_greater"]
        per[n]["q_primary"] = per[n]["q_two_sided"] if primary == "two-sided" else per[n]["q_greater"]
    return dict(terms=per, n_tested=len(tested), n_not_tested=not_tested, primary=primary, label=sidedness["label"],
                bh_family="the terms tested (a term with no reference gene is outside it)")


# ================================================================================================================
# R28: robust linear model (statsmodels defaults) and a direct IRLS Huber fit
# ================================================================================================================
def _design(columns) -> np.ndarray:
    cols = [np.asarray(c, dtype=np.float64) for c in columns]
    return np.column_stack(cols + [np.ones_like(cols[0])])


def rlm_statsmodels(endog, columns, **fit_kw):
    """P17 comparator: statsmodels RLM(endog, [columns..., const]) with its defaults (HuberT(), scale_est='mad',
    cov='H1'); fit_kw only for P17's tightened (fixed-point) comparison. Production uses forms.rlm_t."""
    import statsmodels.api as sm
    X = _design(columns)
    y = np.asarray(endog, dtype=np.float64)
    res = sm.RLM(y, X).fit(**fit_kw)
    if res.fit_options["norm"] != "HuberT" or res.fit_options["cov"] != "H1":
        raise RuntimeError("rlm_statsmodels: statsmodels defaults changed (norm / cov)")
    return res


def rlm_log2fc_t(gene_t, log2fc, gc) -> dict:
    """R28: the production RLM is forms.rlm_t (the forms worker's module, RUN_PLAN §18 WP2: statsmodels RLM(endog =
    per-gene t, exog = [log2FC, GC %, const]) with its defaults, asserted there equal to forms.irls_huber_direct;
    reported value tvalues[0]; non-finite rows dropped and counted). This module does not keep a second production
    RLM: it delegates (imported lazily, so repro's other functionals never depend on forms' import). P17 checks
    forms.rlm_t, forms.rlm_statsmodels and forms.irls_huber_direct against `huber_irls` below, an independent third
    implementation, and against statsmodels directly."""
    from . import forms
    return forms.rlm_t(gene_t, log2fc, gc)


_PHI_INV_075 = float(stats.norm.ppf(0.75))


def _huber_rho(z, t):
    az = np.abs(z)
    return np.where(az <= t, 0.5 * z * z, t * az - 0.5 * t * t)


def _wls(y, X, w):
    sw = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    return beta


def huber_irls(endog, columns, *, t: float = HUBER_T, stop: str = "statsmodels-dev", tol: float = 1e-8,
               maxiter: int = 50) -> dict:
    """A direct iteratively reweighted Huber fit of endog on [columns..., const], written independently of
    statsmodels: start at OLS; scale s = median(|r|) / Phi^-1(3/4) (MAD about 0); weights min(1, t / |r / s|); WLS;
    scale re-estimated after every fit. stop = 'statsmodels-dev' replicates the default stopping rule of
    statsmodels RLM (|D_k - D_k-1| <= tol on D = sum rho_Huber(r / sigma2_WLS), sigma2_WLS the current weighted
    fit's residual variance, or maxiter); stop = 'fixed-point' iterates until max |delta beta| <= tol (1 + max |beta|)
    and |delta s| <= tol s. The H1 covariance (Huber 1981, as statsmodels documents it) gives bse and t."""
    X = _design(columns)
    y = np.asarray(endog, dtype=np.float64)
    n, p = X.shape
    rank = np.linalg.matrix_rank(X)
    df_resid, df_model = n - rank, rank - 1

    def mad0(r):
        return float(np.median(np.abs(r))) / _PHI_INV_075

    def wls_var(beta, w):
        r = y - X @ beta
        return float(np.sum(w * r * r)) / (n - p)

    w = np.ones(n)
    beta = _wls(y, X, w)
    r = y - X @ beta
    s = mad0(r)
    hist = [math.inf, float(_huber_rho(r / wls_var(beta, w), t).sum())]
    it = 1
    while True:
        if s == 0.0:
            break
        z = r / s
        w = np.where(np.abs(z) <= t, 1.0, t / np.abs(z))
        beta_new = _wls(y, X, w)
        r = y - X @ beta_new
        s_new = mad0(r)
        it += 1
        if stop == "statsmodels-dev":
            hist.append(float(_huber_rho(r / wls_var(beta_new, w), t).sum()))
            beta, s = beta_new, s_new
            if not (abs(hist[-1] - hist[-2]) > tol and it < maxiter):
                break
        elif stop == "fixed-point":
            db = float(np.max(np.abs(beta_new - beta)))
            ds = abs(s_new - s)
            beta, s = beta_new, s_new
            if (db <= tol * (1.0 + float(np.max(np.abs(beta)))) and ds <= tol * s) or it >= maxiter:
                break
        else:
            raise ValueError(f"huber_irls: unknown stop rule {stop!r}")
    sr = r / s
    psi = np.clip(sr, -t, t)
    dpsi = (np.abs(sr) <= t).astype(float)
    m = dpsi.mean()
    k = 1.0 + (df_model + 1) / n * dpsi.var() / m ** 2
    XtX_inv = np.linalg.pinv(X.T @ X)
    cov = k ** 2 * (np.sum(psi ** 2) * s ** 2 / df_resid) / (dpsi.sum() / n) ** 2 * XtX_inv
    bse = np.sqrt(np.diag(cov))
    return dict(params=beta, scale=s, bse=bse, tvalues=beta / bse, iterations=it, stop=stop,
                converged_before_maxiter=it < maxiter, weights=w)


# ================================================================================================================
# R30: the overlap test (GeneOverlap's direction)
# ================================================================================================================
def overlap_counts_universe(decoded, gene_set, universe) -> dict:
    """Primary universe (R30): U = the genes the recipe tested; the decoded list must lie inside U (asserted); the set
    is intersected with U. Counts of [[k, |L - S|], [|S - L|, rest]]."""
    U = set(universe)
    L = set(decoded)
    if not L <= U:
        raise ValueError("overlap_test: the decoded list is not inside the universe")
    S0 = set(gene_set)
    S = S0 & U
    k = len(L & S)
    return dict(a=k, b=len(L) - k, c=len(S) - k, d=len(U) - len(L | S), n_list=len(L), n_set=len(S),
                n_universe=len(U), set_outside_universe=len(S0 - U), background="primary (genes tested, R30)")


def overlap_counts_genome(decoded, gene_set, genome_size: int) -> dict:
    """GeneOverlap's own construction (newGeneOverlap / testGeneOverlap as read from the package source): the lists as
    given (unique), the genome size as the background: [[|A & B|, |A - B|], [|B - A|, genome - |A | B|]]."""
    A, B = set(decoded), set(gene_set)
    k = len(A & B)
    rest = int(genome_size) - len(A | B)
    if rest < 0:
        raise ValueError("overlap_test: the union of the lists exceeds the genome size")
    return dict(a=k, b=len(A) - k, c=len(B) - k, d=rest, n_list=len(A), n_set=len(B), genome_size=int(genome_size),
                background=("GeneOverlap default background" if int(genome_size) == GENEOVERLAP["default_genome_size"]
                            else f"genome size {int(genome_size)} (GeneOverlap's construction)"))  # R30's label


def overlap_test(decoded, gene_set, *, universe=None, genome_size=None, alternative: str | None = None) -> dict:
    """R30: Fisher's exact test of the decoded list against the set, in GeneOverlap's direction
    (GENEOVERLAP['alternative']), on the primary universe (universe=...) or on GeneOverlap's construction with a genome
    size (genome_size=...). Returns k, OR (conditional MLE, as R's fisher.test; and the sample OR), p and Jaccard."""
    if (universe is None) == (genome_size is None):
        raise ValueError("overlap_test: give exactly one of universe, genome_size")
    alt = alternative or GENEOVERLAP["alternative"]
    cnt = (overlap_counts_universe(decoded, gene_set, universe) if universe is not None
           else overlap_counts_genome(decoded, gene_set, genome_size))
    fp = fisher_p(cnt["a"], cnt["b"], cnt["c"], cnt["d"])
    if alt == "greater":
        p = fp["p_greater"]
    elif alt == "two.sided":
        p = fp["p_two_sided"]
    else:
        raise ValueError(f"overlap_test: alternative {alt!r}")
    union = cnt["a"] + cnt["b"] + cnt["c"]
    return dict(cnt, k=cnt["a"], p=p, alternative=alt, odds_ratio=fp["odds_ratio_conditional_mle"],
                odds_ratio_sample=fp["odds_ratio_sample"], jaccard=(cnt["a"] / union) if union else math.nan,
                geneoverlap_status=GENEOVERLAP["status"])


# ================================================================================================================
# R40: differential stability for Benkarim and Park (RUN_PLAN_amend_2 R40)
# ================================================================================================================
DS_BENKARIM_MIN = 0.5   # TSV rows 506-517: "DS >= .5"
DS_PARK_ABOVE = 0.5     # TSV rows 595-614: "DS > .5"
R40_RULE = ("RUN_PLAN_amend_2 R40: DS = abagen.correct.keep_stable_genes as abagen implements it (R12's build: the "
            "per-donor V-DK matrices' 34 left DK cortical parcels); Benkarim: R12's DS vector, DS >= .5; Park: DS > .5 "
            "on the decoder output's own DS column if it carries one, else on R12's vector (also the per-donor "
            "fallback); decoder genes absent from R12's vector excluded and counted")


def _ds_map(ds) -> dict:
    """{gene symbol: DS} from a pandas Series (index = genes) or a mapping; repeated genes refused."""
    if hasattr(ds, "index") and hasattr(ds, "to_numpy"):
        genes = [str(g) for g in ds.index]
        vals = np.asarray(ds.to_numpy(), dtype=np.float64)
    else:
        genes = [str(g) for g in ds]
        vals = np.asarray([ds[g] for g in ds], dtype=np.float64)
    if len(set(genes)) != len(genes):
        raise ValueError("DS: a gene listed twice")
    return dict(zip(genes, vals.tolist()))


def ds_vector_sha(ds) -> str:
    """The identity of a DS vector: sha256 over its genes (in order) and its float64 values."""
    import hashlib
    m = _ds_map(ds)
    h = hashlib.sha256()
    h.update("\n".join(m).encode("utf-8") + b"\0")
    h.update(np.asarray(list(m.values()), dtype="<f8").tobytes())
    return h.hexdigest()


def benkarim_ds_genes(ds, *, r12_sha256: str) -> dict:
    """R40, Benkarim: R12's DS vector (asserted: its hash equals R12's), genes with DS >= .5, in the vector's order."""
    sha = ds_vector_sha(ds)
    if sha != r12_sha256:
        raise AssertionError("R40: Benkarim's DS vector is not R12's (hash differs)")
    m = _ds_map(ds)
    kept = [g for g, v in m.items() if math.isfinite(v) and v >= DS_BENKARIM_MIN]
    return dict(genes=kept, n_kept=len(kept), n_vector=len(m), threshold=">= .5", ds_sha256=sha, source="R12's DS vector",
                n_nonfinite=sum(1 for v in m.values() if not math.isfinite(v)), rule=R40_RULE)


def park_ds_genes(decoder_genes, *, r12_ds, r12_sha256: str, decoder_ds=None) -> dict:
    """R40, Park: DS > .5. Branch 1 (the decoder output carries the DS it filtered on): that column (`decoder_ds`,
    {gene: DS}); a decoder gene without a finite value there is excluded and counted. Branch 2 (no such column, and the
    per-donor fallback): R12's DS vector (hash asserted); decoder genes absent from it are excluded and counted. Kept
    genes in the decoder's order."""
    genes = [str(g) for g in decoder_genes]
    if len(set(genes)) != len(genes):
        raise ValueError("R40: a decoder gene listed twice")
    if decoder_ds is not None:
        col = _ds_map(decoder_ds)
        absent = [g for g in genes if g not in col or not math.isfinite(col[g])]
        kept = [g for g in genes if g in col and math.isfinite(col[g]) and col[g] > DS_PARK_ABOVE]
        return dict(genes=kept, n_kept=len(kept), n_decoder=len(genes), n_excluded_no_ds=len(absent),
                    branch="the decoder output's DS column", threshold="> .5", rule=R40_RULE)
    if ds_vector_sha(r12_ds) != r12_sha256:
        raise AssertionError("R40: Park's fallback DS vector is not R12's (hash differs)")
    r12 = _ds_map(r12_ds)
    absent = [g for g in genes if g not in r12]
    kept = [g for g in genes if g in r12 and math.isfinite(r12[g]) and r12[g] > DS_PARK_ABOVE]
    return dict(genes=kept, n_kept=len(kept), n_decoder=len(genes), n_excluded_absent_from_r12=len(absent),
                n_excluded_nonfinite=sum(1 for g in genes if g in r12 and not math.isfinite(r12[g])),
                branch="R12's DS vector (no DS column in the decoder output)", threshold="> .5",
                ds_sha256=r12_sha256, rule=R40_RULE)


# ================================================================================================================
# hand computations (exact rationals) used by P17 as the independent references
# ================================================================================================================
def hypergeom_pmf_exact(x: int, a_plus_b: int, a_plus_c: int, total: int) -> Fraction:
    """P(X = x), X = the top-left cell of a 2 x 2 table with row sum a_plus_b, column sum a_plus_c and total, exact."""
    return Fraction(math.comb(a_plus_c, x) * math.comb(total - a_plus_c, a_plus_b - x), math.comb(total, a_plus_b))


def fisher_exact_hand(a: int, b: int, c: int, d: int) -> dict:
    """Exact rationals: the upper tail P(X >= a) and the two-sided p (every table with P <= P(observed))."""
    r1, c1, N = a + b, a + c, a + b + c + d
    lo, hi = max(0, r1 + c1 - N), min(r1, c1)
    pm = {x: hypergeom_pmf_exact(x, r1, c1, N) for x in range(lo, hi + 1)}
    p_obs = pm[a]
    upper = sum((pm[x] for x in range(a, hi + 1)), Fraction(0))
    lower = sum((pm[x] for x in range(lo, a + 1)), Fraction(0))
    two = sum((v for v in pm.values() if v <= p_obs), Fraction(0))
    return dict(greater=upper, less=lower, two_sided=min(two, Fraction(1)))
