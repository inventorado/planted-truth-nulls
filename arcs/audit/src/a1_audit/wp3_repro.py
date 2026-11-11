"""WP3 reproduction wiring for the ungated targets (RUN_PLAN.md v3.1 §16 "the reproduction check or descriptive
comparison"; R14, R21, R22, R27; RUN_PLAN_amend_2 R37, R42; claims_register.md §1.5 :316-332; FROZEN). Built and tested
on synthetic data in WP3 phase 1; it runs on real data only in the WP3 run (run.py writes row_<n>_repro.json beside a
real row: the verdict pass for Segura and Moreau, the descriptor pass for Liu). Every record is descriptive: no count
moves, and nothing here enters a verdict.

Segura (R22; TSV rows 1-80):
- the decoded list: the NeuroVault decoder output (mask=full; wp3_material's gene-level object), HGNC genes with any row
  at FDR q < .05, both signs. If the decoder is unavailable (its phase-2 object refused / absent after phase 2): R22's
  fallback, the per-donor recipe on V-AAL (R14's rule: the six WP2 per-donor V-AAL matrices, the re-parcellated map on
  the class's parcels, repro.per_donor_recipe_t; the paper's threshold q < .05, both signs), labelled
  "re-derived (per-donor parcel recipe, V-AAL), not the decoder".
- SEG-C1 / SEG-C2: Fisher's exact test of the decoded list against Table S4 (segura_s4's HGNC members) inside each
  reference: the primary, every gene of the GO 2024-01-17 GAF mapped by the S-build's HGNC rule; beside it "PANTHER 16.0
  reference (an older release)" (PTHR16.0_human); the paper's reference of 20,787 reported beside (U-W3-10). Two-sided
  p primary, labelled "PANTHER sidedness unverified", with repro.PANTHER_SIDEDNESS["empirical_check"] beside it; the
  one-sided p beside; sample and conditional-MLE odds ratios; the published OR / p from the TSV.
- SEG-C3a ... g, SEG-C3-D01 ... D71: the decoded list intersected with Table S4, then the GO over-representation analysis
  over every live GO 2024-01-17 biological_process term (the §1.6 GO rule) inside each reference, BH across the terms
  tested (separately per sidedness); the row's term: genes, expected, fold enrichment, both p's and q's; the TSV's
  published genes / expected / fold / FDR beside it (rows 3-9) and, for the D rows, the values transcribed from MOESM2
  p. 39 (RUN_PLAN_amend_3 R47; descriptive, no tolerance). Rows 4 and 6 (no T) are compared too (R47 (h)).
- Table S6's Jaccard (rows 1, 3-80; R47 (h)): A = HGNC(decoded list) n Table S4's HGNC members (no reference
  restriction), B = Table S6's HGNC members (MOESM2 p. 38); |A|, |B|, |A n B|, |A u B|, J beside "107"; with the
  fallback list it carries the fallback's label. A comparator that cannot be computed reads "not computable (<why>)"
  and never reaches the cell's status (amend_3 B6).
Moreau (R27, R37; TSV rows 615-619):
- MOR-C1 / C2 / C3: the authors' centred, unscaled PLS (two components, as plsregress) of the nodal profile on the set's
  columns over all 64 MIST64 parcels (claims_register.md §3.6: "all 64 = ... the reproduction setting"); cumulative R^2
  against 24.2 % / 43.2 % / 35.3 % as fractions (U-W3-11), reporting.reproduction_check (R37 (B); functional "R2").
- MOR-T1 / T2 (descriptive): per-gene Pearson r of the nodal profile with every gene of the MIST64 matrix on all 64
  parcels; the named genes' percentile ranks (U-W3-12); the tail statistic at the text's 98th and the code's 95th
  percentile, with the exact uniform-random-set tail p (hypergeometric; U-W3-12) beside the paper's p.
Liu (R10, R42; TSV rows 471-477):
- T4 / T5 (R46 (g)): on the common labels L_c (the labels of T's set whose SD7 value is present), our per-label r
  through R42 (e)'s function against the same function of SD7's values; R37 (B)'s check on that pair; "comparator on n
  of m labels (m - n without an SD7 value)" with T (all m labels) beside; "not computable (...)" otherwise.
- T1 (R48) and the T2 family (R49): "not computable (...)" with the amendment's reasons; T2*'s two group counts.
"""
from __future__ import annotations

import math
import re

import numpy as np
from scipy import stats

from . import repro as RE
from . import reporting as RPT
from . import reparcel as RP

R22_REFERENCE_PRIMARY = "GO 2024-01-17 GAF genes, HGNC-mapped (R22 primary reference)"
R22_REFERENCE_PANTHER = "PANTHER 16.0 reference (an older release)"
R22_PAPER_REFERENCE = 20787   # TSV rows 1-80 inference_level: "a uniform 20,787-gene background"
R22_FALLBACK_LABEL = RP.RECIPE_DECODER.format(cls="V-AAL")
DESCRIPTIVE = "reproduction descriptive (amendment 4 §2)"
# RUN_PLAN_amend_3 R47 (a), (d), (f): the comparators' "not computable" outcomes (R28's wording; B6)
MOESM2_CHANGED = "not computable (carrier changed: sha256 differs from the register's)"
S7_NOT = "not computable (Table S7's row values not transcribed: %s)"
S6_NOT = "not computable (Table S6 not transcribed: %s)"
# R48 (LIU-T1): both comparators
# the frozen texts verbatim (fix round 3, C (d): UTF-8 "§8" kept; reproduction records are written UTF-8)
T1_PER_SAMPLE = ("not computable (SD3's per-sample r: (age, structure acronym) is not one-to-one over BrainSpan's "
                 "samples: 79 pairs repeat, 196 of 524 samples; BrainSpan's donor columns are not read, §8)")
T1_CLUSTER = ("not computable (prenatal cluster: defined by ward.D2 over the traits' z-scored per-sample r; the other 14 "
              "traits' per-sample r are SD3 columns, and a recomputation with our ASD vector beside them would be an "
              "unregistered hybrid; the other traits' sets are not registered)")
# R49 (LIU-T2, T2-STR / -CBC / -HIP)
T2_FAMILY = ("not computable (the paper's pooled SD and FDR family span its structure annotation, which is unpublished "
             "and whose group count is not recorded; structures beyond the six the register pins are assigned to "
             "BrainSpan structure acronyms by no frozen text)")
T2_GROUPS = {"frontal cortex": ("DFC", "VFC", "MFC", "OFC"), "thalamus": ("MD", "DTH")}   # claims_register.md:1672-1675
T2_SD4_N = {"frontal cortex": 164, "thalamus": 29}       # register_work/liu2026spatiotemporal.md:49
# R46 (g)
SD7_COMMON = "comparator on %d of %d labels (%d without an SD7 value)"
SD7_NO_VALUE = "not computable (no SD7 value for %s)"
SEG_C12_PUBLISHED = {"SEG-C1": {"OR": "1.6", "p": "0.0002"}, "SEG-C2": {"OR": "1.7", "p": "0.2"}}   # TSV rows 1, 2
MOREAU_PUBLISHED = {615: ".242", 616: ".432", 617: ".353"}   # TSV 'reproduction': 24.2 %, 43.2 %, 35.3 % (U-W3-11)
# TSV rows 618 / 619 published_value_and_location (asserted against the row's text at use)
MOR_T_PUBLISHED = {
    618: dict(genes={"MVP": ("0.33", "99.76"), "KIF22": ("0.26", "98.76")}, tail_p="0.03"),
    619: dict(genes={"AIFM3": (None, "99.5"), "TBX1": (None, "98.84"), "P2RX6": (None, "98.33")}, tail_p="0.04"),
}
MOR_T_PERCENTILES = (98, 95)   # TSV notes: "Text / code threshold mismatch (98th vs 95th percentile)"
_S7 = re.compile(r"genes / expected / fold / FDR p = ([0-9.eE+-]+) / ([0-9.eE+-]+) / ([0-9.eE+-]+) / ([0-9.eE+-]+)")


# ================================================================================================================
# R22: decoded list, references, Fisher tests, the bitset ORA
# ================================================================================================================
def json_safe(o, _path: str = "", _bad: list | None = None):
    """Fix round 1 (d): a record with every non-finite float written as null, the fields listed under
    'nonfinite_as_null' (e.g. an odds ratio of a table with a zero cell, a fold enrichment with nothing expected)."""
    top = _bad is None
    bad = [] if top else _bad
    if isinstance(o, dict):
        out = {k: json_safe(v, f"{_path}/{k}", bad) for k, v in o.items()}
    elif isinstance(o, (list, tuple)):
        out = [json_safe(v, f"{_path}/{i}", bad) for i, v in enumerate(o)]
    elif isinstance(o, (float, np.floating)) and not math.isfinite(float(o)):
        bad.append(_path or "/")
        out = None
    else:
        out = o
    if top and isinstance(out, dict) and bad:
        out["nonfinite_as_null"] = {"fields": bad, "status": "not finite (written as null)"}
    return out


def decoded_from_decoder(obj: dict, q: float = 0.05) -> set:
    """HGNC genes with any decoder row at FDR q < .05, both signs (R22; U-W3-4)."""
    return {g for g, qv in zip(obj["genes"], obj["q"]) if qv is not None and qv < q}


def decoded_from_recipe(y_by_parcel: dict, donor_frames: list, hg, q: float = 0.05) -> tuple[set, dict]:
    """R22's fallback: R14's per-donor recipe on V-AAL. y_by_parcel: {parcel id: value} (the class's parcels with a
    finite map value); donor_frames: the six per-donor V-AAL frames (parcels x genes, NaN = no sample). Genes are
    abagen columns mapped by the S-build's HGNC rule (U-W3-13); a gene is decoded iff its BH q < .05, either sign."""
    ids = [i for i in sorted(y_by_parcel) if i in set(int(x) for x in donor_frames[0].index)]
    y = np.array([y_by_parcel[i] for i in ids], dtype=float)
    mats = [f.loc[ids].to_numpy(dtype=float) for f in donor_frames]
    rec = RE.per_donor_recipe_t(y, mats)
    cols = [str(c) for c in donor_frames[0].columns]
    mapped, how = hg.map_columns(cols)
    sel = np.isfinite(rec["q_bh"]) & (rec["q_bh"] < q)
    genes = {mapped[k] for k in np.flatnonzero(sel) if mapped[k]}
    info = dict(label=R22_FALLBACK_LABEL, n_parcels=len(ids), n_tested=rec["n_tested"], n_decoded_columns=int(sel.sum()),
                n_decoded_genes=len(genes), sidedness=rec["sidedness"], q_threshold=q, hgnc_mapping=how)
    return genes, info


def fisher_record(list_genes: set, term_genes: set, reference: set, sidedness: dict = RE.PANTHER_SIDEDNESS) -> dict:
    """repro.fisher_counts / fisher_p on one list x term inside a reference, with R22's primary and label."""
    cnt = RE.fisher_counts(list_genes, term_genes, reference)
    fp = RE.fisher_p(cnt["a"], cnt["b"], cnt["c"], cnt["d"])
    primary = sidedness["primary"]
    # fix round 1 (h): no Jaccard here - the registered one (Table S6) waits for RUN_PLAN_amend_3 (R47)
    return dict(cnt, **fp, p_primary=fp["p_two_sided"] if primary == "two-sided" else fp["p_greater"],
                primary=primary, label=sidedness["label"], empirical_check=dict(sidedness["empirical_check"]))


def gene_index(*gene_sets) -> dict:
    allg = sorted(set().union(*[set(s) for s in gene_sets]))
    return {g: k for k, g in enumerate(allg)}


def bits_of(genes, index: dict) -> int:
    b = 0
    for g in genes:
        k = index.get(g)
        if k is not None:
            b |= 1 << k
    return b


def ora_bits(list_bits: int, term_bits: dict, ref_bits: int, sidedness: dict = RE.PANTHER_SIDEDNESS) -> dict:
    """repro.ora on bitsets (the same 2 x 2 layout as repro.fisher_counts: L = list & R, T = term & R; a term with no
    reference gene is not tested; BH across the terms tested per sidedness; the primary per R22). tests assert equality
    with repro.ora on synthetic terms."""
    L = list_bits & ref_bits
    nL, N = L.bit_count(), ref_bits.bit_count()
    per, tested = {}, []
    for name, tb in term_bits.items():
        T = tb & ref_bits
        nT = T.bit_count()
        if nT == 0:
            per[name] = dict(status="not tested (no reference gene)", n_term=0)
            continue
        a = (L & T).bit_count()
        b, c = nL - a, nT - a
        d = N - a - b - c
        fp = RE.fisher_p(a, b, c, d)
        expected = nL * nT / N
        per[name] = dict(a=a, b=b, c=c, d=d, n_list=nL, n_term=nT, n_reference=N, **fp, expected=expected,
                         fold_enrichment=(a / expected) if expected > 0 else math.nan,
                         direction="+" if a > expected else ("-" if a < expected else "0"), status="tested")
        tested.append(name)
    q_g = RE.bh([per[n]["p_greater"] for n in tested]) if tested else []
    q_2 = RE.bh([per[n]["p_two_sided"] for n in tested]) if tested else []
    primary = sidedness["primary"]
    for i, n in enumerate(tested):
        per[n]["q_greater"] = float(q_g[i])
        per[n]["q_two_sided"] = float(q_2[i])
        per[n]["p_primary"] = per[n]["p_two_sided"] if primary == "two-sided" else per[n]["p_greater"]
        per[n]["q_primary"] = per[n]["q_two_sided"] if primary == "two-sided" else per[n]["q_greater"]
    return dict(terms=per, n_tested=len(tested), n_not_tested=len(term_bits) - len(tested), primary=primary,
                label=sidedness["label"], empirical_check=dict(sidedness["empirical_check"]),
                bh_family="the terms tested (a term with no reference gene is outside it)")


def published_s7(text: str):
    m = _S7.search(text or "")
    if not m:
        return None
    return dict(genes=m.group(1), expected=m.group(2), fold=m.group(3), fdr=m.group(4),
                source="TSV published_value_and_location (Table S7, MOESM2 p. 39)")


class SeguraContext:
    """Per-process cache of R22's inputs (references, GO term bitsets) built from a sources object with the WP3 door
    (real_sources.WP3Sources, or a synthetic stand-in exposing the same methods)."""

    def __init__(self, src):
        self.src = src
        self._c = {}

    def hg(self):
        return self.src.hgnc()

    def go(self):
        if "go" not in self._c:
            from . import wp3_genes as WG
            self._c["go"] = WG.GOTerms(self.src.repro_bytes("go_obo"), self.src.repro_bytes("go_gaf"))
        return self._c["go"]

    def references(self) -> dict:
        if "refs" not in self._c:
            from . import wp3_genes as WG
            gaf, how1 = WG.gaf_reference(self.go(), self.hg())
            pth, how2 = WG.pthr16_reference(self.src.repro_bytes("pthr16"), self.hg())
            self._c["refs"] = {R22_REFERENCE_PRIMARY: (gaf, how1), R22_REFERENCE_PANTHER: (pth, how2)}
        return self._c["refs"]

    def s4(self) -> set:
        doc, _ = self.src.set_doc("segura_s4")
        return set(doc["members_hgnc"])

    def decoded(self, image: int, y_by_parcel_fn) -> tuple[set, dict]:
        """The decoded list of an image: the decoder's (its phase-2 object extracted), else - the decoder's phase-2
        entry present but refused (fetch or declared-column read failed: "unavailable", U-W3-14) - R22's fallback, the
        per-donor recipe on V-AAL. An entry absent from the manifest (or no manifest) stays pending."""
        key = ("decoded", image)
        if key not in self._c:
            from . import fetch_extract as FE
            from . import wp3_layout as L
            from . import run as R
            from . import wp3_decoder as DC
            e = self.src._entry(L.SEGURA_DECODER_KEY[image])          # absent -> SourceUnavailable(pending)
            st = str(e.get("status"))
            if st != FE.STATUS_EXTRACTED and not st.startswith(DC.UNAVAILABLE_PREFIX):
                # fix round 3, C (f): R22's fallback is taken on R45's "unavailable" outcomes only
                raise R.SourceUnavailable(L.STATUS_STAGE_REFUSED % st, f"decoder {image}")
            if e.get("status") == FE.STATUS_EXTRACTED:
                obj, sha = self.src.decoder_genes(image)
                self._c[key] = (decoded_from_decoder(obj), dict(source="NeuroVault decoder (mask=full)",
                                                                object_sha256=sha, counts=obj.get("counts"),
                                                                q_threshold=0.05))
            else:
                mats, _, msha = self.src.perdonor_aal()
                genes, info = decoded_from_recipe(y_by_parcel_fn(), mats, self.hg())
                info.update(decoder_status=e.get("status"), per_donor_sha256=msha,     # R45 (e): the refusing stage
                            refusing_stage=e.get("refusing_stage") or e.get("failed_stage"))
                self._c[key] = (genes, info)

        return self._c[key]

    def ora(self, image: int, list_genes: set, ref_name: str) -> dict:
        key = ("ora", image, ref_name)
        if key not in self._c:
            ref = self.references()[ref_name][0]
            idx = gene_index(ref)
            tb = self._c.get(("term_bits", ref_name))
            if tb is None:
                tb = self.go().term_gene_bits(self.hg(), idx)
                self._c[("term_bits", ref_name)] = tb
            self._c[key] = ora_bits(bits_of(list_genes, idx), tb, bits_of(ref, idx))
        return self._c[key]


def jaccard_s6(src, decoded: set, s4: set, dinfo: dict) -> dict:
    """R47 (h): A = HGNC(decoded list) n Table S4's HGNC members; B = Table S6's HGNC members (MOESM2 p. 38)."""
    from . import run as R
    from . import wp3_pdf as WPDF
    try:
        s6, sha = src.moesm2("s6")
    except R.SourceUnavailable as e:
        return dict(status=e.status)
    if s6.get("status") != "transcribed":
        return dict(status=S6_NOT % s6.get("check"))
    j = WPDF.jaccard(set(decoded) & set(s4), set(s6["members_hgnc"]))
    out = dict(j, status="computed", rule="RUN_PLAN_amend_3 R47 (h): A = decoded n Table S4 (no reference "
               "restriction), B = Table S6", object_sha256=sha)
    if dinfo.get("label"):
        out["label"] = dinfo["label"]
    return out


def published_s7_row(src, cell: str):
    """R47 (d): the D rows' Table S7 values from MOESM2 p. 39 (or a "not computable (...)" status)."""
    from . import run as R
    try:
        s7, sha = src.moesm2("s7")
    except R.SourceUnavailable as e:
        return dict(status=e.status)
    if s7.get("status") != "transcribed":
        return dict(status=S7_NOT % s7.get("check"))
    r = s7["rows"].get(cell)
    if r is None:
        return dict(status=S7_NOT % "the row's cell id is not in the transcription")
    return dict(genes=r["genes"], expected=r["expected"], fold=r["fold"], FDR=r["fdr"], tokens=r["tokens"],
                source="MOESM2 p. 39, transcribed by RUN_PLAN_amend_3 R47 (c)", object_sha256=sha)


def segura_row(plan: dict, tsv_row, sc: SeguraContext, image: int, y_by_parcel_fn) -> dict:
    """The reproduction record of one Segura row (RUN_PLAN R22; amend_3 R47)."""
    decoded, dinfo = sc.decoded(image, y_by_parcel_fn)
    s4 = sc.s4()
    rec = dict(kind=DESCRIPTIVE, reading="RUN_PLAN R22", image=image, decoded_list=dict(dinfo, n_genes=len(decoded)),
               paper_reference_n=R22_PAPER_REFERENCE)
    cell = plan["cell_id"]
    if cell in ("SEG-C1", "SEG-C2"):
        out = {}
        for name, (ref, how) in sc.references().items():
            out[name] = dict(fisher_record(decoded, s4, ref), reference_n=len(ref), reference_mapping=how)
        pub = SEG_C12_PUBLISHED[cell]
        text = tsv_row["published_value_and_location"]
        if f"OR = {pub['OR']}" not in text or f"p = {pub['p']}" not in text:
            raise AssertionError("SEG-C1 / C2 published values: transcription differs from the TSV text")
        rec.update(test="decoded list vs Table S4 (Fisher's exact test inside each reference)", per_reference=out,
                   published=dict(pub, source="TSV published_value_and_location"),
                   jaccard_table_s6=jaccard_s6(sc.src, decoded, s4, dinfo) if cell == "SEG-C1" else None)
        return rec
    go_id = sc.src.set_doc(plan["set_id"])[0]["go"]["go_id"]
    lst = decoded & s4
    out = {}
    for name in sc.references():
        ora = sc.ora(image, lst, name)
        t = ora["terms"].get(go_id)
        out[name] = dict(term=t if t is not None else "term not live in the release (not tested)",
                         n_tested=ora["n_tested"], primary=ora["primary"], label=ora["label"],
                         empirical_check=ora["empirical_check"], bh_family=ora["bh_family"])
    pub = published_s7(tsv_row["published_value_and_location"])
    rec.update(test="decoded list intersected with Table S4, then the GO over-representation over every live BP term "
                    "(BH across the terms tested)", go_id=go_id, list_n=len(lst), per_reference=out,
               published=pub if pub is not None else published_s7_row(sc.src, cell),
               jaccard_table_s6=jaccard_s6(sc.src, decoded, s4, dinfo),
               t=("no T (not testable (< 5)); the descriptive comparison is reported (R47 (h))"
                  if plan.get("kind") == "no statistic" else "computed by the run"))
    return rec


# ================================================================================================================
# Moreau: the authors' centred, unscaled two-component PLS; MOR-T percentiles and tail
# ================================================================================================================
def pls_cum_r2(y, X, n_components: int = 2) -> dict:
    """Cumulative R^2 in y of a centred, unscaled PLS1 with n components (plsregress's PCTVAR(2, :) summed; for one
    response SIMPLS and NIPALS give the same fitted values): NIPALS on centred X and y, X deflated, y fitted on the
    scores. tests assert equality with sklearn PLSRegression(scale=False).score."""
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or y.shape != (X.shape[0],) or not (np.isfinite(X).all() and np.isfinite(y).all()):
        raise ValueError("pls_cum_r2: a finite parcels x genes matrix and one finite y per parcel")
    yc = y - y.mean()
    E = X - X.mean(axis=0)
    fit = np.zeros_like(yc)
    per = []
    sst = float(yc @ yc)
    if not sst > 0:
        raise ValueError("pls_cum_r2: y is constant")
    for _ in range(n_components):
        w = E.T @ yc
        nw = float(np.linalg.norm(w))
        if not nw > 0:
            raise ValueError("pls_cum_r2: no covariance left")
        w /= nw
        t = E @ w
        tt = float(t @ t)
        c = float(yc @ t) / tt
        fit = fit + c * t
        per.append(float((c * t) @ (c * t)) / sst)
        E = E - np.outer(t, (E.T @ t) / tt)
    resid = yc - fit
    return dict(R2=1.0 - float(resid @ resid) / sst, per_component=per, n_components=n_components,
                centred=True, scaled=False, n_parcels=int(X.shape[0]), n_genes=int(X.shape[1]))


def per_gene_r(y, X) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    yc = (y - y.mean()) / y.std()
    Z = (X - X.mean(axis=0)) / X.std(axis=0)
    return Z.T @ yc / y.size


def mor_t_tail(y64, M, set_columns: list, row: int, published_text: str) -> dict:
    """MOR-T1 / T2 (descriptive): percentile ranks of the named genes' r among every gene's r (weak: 100 x the share of
    genes with r <= the gene's; strict beside), and the tail statistic: the number k of S's genes whose percentile
    rank exceeds q (98th text, 95th code), with the exact uniform-random-set p P(X >= k), X ~ hypergeometric(G, K, m)
    (U-W3-12; the paper's 10,000 random sets estimate the same tail)."""
    pub = MOR_T_PUBLISHED[row]
    for g, (r, pct) in pub["genes"].items():
        if g not in published_text or pct not in published_text or (r is not None and r not in published_text):
            raise AssertionError("MOR-T published values: transcription differs from the TSV text")
    cols = [str(c) for c in M.columns]
    r = per_gene_r(y64, M.to_numpy(dtype=float))
    G = r.size
    order = np.sort(r)
    # c * 100 / G: exact at a boundary (c * 100 == q * G gives q itself), so '> q' is decided without rounding
    weak = np.searchsorted(order, r, side="right") * 100.0 / G
    strict = np.searchsorted(order, r, side="left") * 100.0 / G
    pos = {c: k for k, c in enumerate(cols)}
    named = {}
    for g, (rp, pct) in pub["genes"].items():
        k = pos.get(g)
        named[g] = (dict(r=float(r[k]), percentile_weak=float(weak[k]), percentile_strict=float(strict[k]),
                         published_r=rp, published_percentile=pct) if k is not None else "not a column of the matrix")
    S = [pos[c] for c in set_columns if c in pos]
    tails = {}
    for q in MOR_T_PERCENTILES:
        above = weak > q
        K, k = int(above.sum()), int(above[S].sum())
        p = float(stats.hypergeom.sf(k - 1, G, K, len(S)))
        tails[str(q)] = dict(threshold_percentile=q, n_genes_above=K, k_set_above=k, m=len(S), G=G, p_exact=p)
    return dict(kind=DESCRIPTIVE, reading="RUN_PLAN R21 (descriptor); TSV rows 618 / 619 reproduction", named=named,
                tails=tails, published_tail_p=pub["tail_p"], setting="all 64 MIST64 parcels (claims_register.md §3.6)")


def moreau_row(plan: dict, tsv_row, src, sheet: str) -> dict:
    prof, osha = src.moreau_profile64(sheet)
    M, pin = src.mist64_all()
    doc, _ = src.set_doc(plan["set_id"])
    cols = [c for c in doc["universe"]["MIST64"]["columns"] if c in set(map(str, M.columns))]
    ids = [int(i) for i in M.index]
    if sorted(ids) != list(range(1, 65)):
        raise ValueError("MIST64 matrix ids are not roi 1 ... 64")
    y = np.array([prof[i - 1] for i in ids], dtype=float)
    row = int(plan["row"])
    if row in MOREAU_PUBLISHED:
        pls = pls_cum_r2(y, M[cols].to_numpy(dtype=float))
        chk = RPT.reproduction_check(MOREAU_PUBLISHED[row], pls["R2"], functional="R2")
        pct = {615: "24.2 %", 616: "43.2 %", 617: "35.3 %"}[row]
        if pct not in tsv_row["reproduction"]:
            raise AssertionError("Moreau published R^2: transcription differs from the TSV text")
        return dict(kind="4.1 check (R27; R37 (B))", reading="RUN_PLAN R27: the authors' centred unscaled PLS on all 64 "
                    "parcels", pls=pls, check=chk, published_percent=pct,
                    units="published percent read as a fraction (U-W3-11)", object_sha256=osha, matrix_l7=pin)
    out = mor_t_tail(y, M, cols, row, tsv_row["published_value_and_location"])
    out.update(object_sha256=osha, matrix_l7=pin)
    return out


# ================================================================================================================
# Liu
# ================================================================================================================
def liu_row(plan: dict, res: dict, src) -> dict:
    """T4 / T5: the 4.1 check against SD7's statistic (forms.liu_label_T on the row's label set); others pending."""
    from . import forms as FM
    from . import run as R
    cell = plan["cell_id"]
    if cell == "LIU-T1":                                     # R48
        return dict(kind=DESCRIPTIVE, status=T1_PER_SAMPLE, per_sample_r=T1_PER_SAMPLE, prenatal_cluster=T1_CLUSTER,
                    T=res.get("T"), T_reading="T's sign is reported as T; it is not presented as cluster membership")
    if cell.startswith("LIU-T2"):                            # R49
        return dict(kind=DESCRIPTIVE, status=T2_FAMILY, group_counts=src.liu_group_counts(T2_GROUPS),
                    sd4_counts=dict(T2_SD4_N), T=res.get("T"))
    kind = "4.1 check (R10; R37 (B))"
    try:
        lab, sha1 = src.sd7_labels()
    except R.SourceUnavailable as e:
        return dict(kind=kind, status=e.status)
    if lab.get("status") != "matched":
        return dict(kind=kind, status=lab.get("status"), counts=lab.get("counts"))
    try:
        values, sha2 = src.sd7_values()
    except R.SourceUnavailable as e:
        return dict(kind=kind, status=e.status, T_ours=res.get("T"))
    ls = (res.get("labels") or {}).get("label_set")
    if not ls:
        return dict(kind=kind, status="not computable (the row has no label set)")
    return dict(liu_common_comparator(plan["liu_spec"], res, lab, values, FM.dk_table_checked(src.dk_table())),
                kind=kind, sd7_sha256=[sha1, sha2],
                note="the flag does not move the population (claims_register.md:1680-1681)")


def liu_common_comparator(spec: dict, res: dict, lab: dict, values: list, dk) -> dict:
    """R46 (g): the common set L_c (the labels of T's set whose SD7 value is present: pooled, the DK name's row;
    unpooled, the label id's row); ours = R42 (e)'s function of our per-label r on L_c, SD7's = the same function of
    SD7's values on L_c; R37 (B)'s check on that pair; T (all m labels) beside."""
    from . import forms as FM
    ls = res["labels"]["label_set"]
    keys, hip = list(ls["keys"]), list(ls["hip"])
    pooled = bool(lab["pooled"])
    sd7 = {}
    for e in lab["entries"]:
        if e["kind"] == "matched":
            v = values[e["position"]]
            if v is not None:
                sd7[FM.label_key(e["ids"][0], dk, pooled)] = float(v)
    ours_r = {k: float(res["groups"]["mean_r"][str(k)]) for k in keys}
    lc = [k for k in keys if k in sd7]
    m, n = len(keys), len(lc)
    out = dict(T_all_labels=float(res["T"]), m=m, n_common=n)
    if spec["kind"] == "label-mean":
        if not lc:
            return dict(out, status=SD7_NO_VALUE % "a cortical label")
        sub = {"keys": lc, "hip": []}
    else:
        hc = [k for k in hip if k in sd7]
        oc = [k for k in lc if k not in hip]
        if not hc:
            return dict(out, status=SD7_NO_VALUE % "a hippocampus label")
        if not oc:
            return dict(out, status=SD7_NO_VALUE % "another label")
        sub = {"keys": hc + oc, "hip": hc}
    t_ours = FM.liu_label_T(ours_r, spec, sub)
    t_sd7 = FM.liu_label_T(sd7, spec, sub)
    chk = RPT.reproduction_check(repr(t_sd7), t_ours, functional="rank-biserial")
    return dict(out, status="computed", label=(SD7_COMMON % (n, m, m - n)) if n < m else "comparator on all labels",
                T_ours_common=t_ours, T_sd7_common=t_sd7, check=chk)


# ================================================================================================================
# dispatch (run.py's _write_repro)
# ================================================================================================================
_SC: dict = {}


def segura_context(src) -> SeguraContext:
    k = id(src)
    if k not in _SC or _SC[k].src is not src:
        _SC.clear()
        _SC[k] = SeguraContext(src)
    return _SC[k]


def row_reproduction(plan: dict, src, res: dict | None = None) -> dict | None:
    """The reproduction record of one ungated row (None for a row without one). src: real_sources.WP3Sources (or a
    stand-in with its methods); res: the row's computed result (Liu, descriptor pass)."""
    rec = _row_reproduction(plan, src, res)
    return None if rec is None else json_safe(rec)


def _row_reproduction(plan: dict, src, res: dict | None = None) -> dict | None:
    tsv = src._rows()[int(plan["row"])]
    t = int(plan["target_no"])
    if t == 1:
        how, image = src._map_binding(plan)
        sc = segura_context(src)

        def y_by_parcel():
            obj, _, _ = src.segura_vaal(int(image))
            ids = [int(i) for i in src.context("V-AAL")[0].parcel_ids]
            by = dict(zip([int(i) for i in obj["ids"]], obj["values"]))
            return {i: float(by[i]) for i in ids if by.get(i) is not None}
        return segura_row(plan, tsv, sc, int(image), y_by_parcel)
    if t == 18:
        how, sheet = src._map_binding(plan)
        return moreau_row(plan, tsv, src, str(sheet))
    if t == 10:
        return liu_row(plan, res or {}, src)
    return None
