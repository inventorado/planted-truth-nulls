"""WP4: the reproduction checks and descriptive comparisons of the G2 rows (RUN_PLAN.md v3.1 §16 "the reproduction
check or descriptive comparison", R13, R14, R27, R30, R37; the DRAFT RUN_PLAN_amend_4.md R53-R63). Written by run.py's
_write_repro beside a computed G2 row as row_<n>_repro.json; none enters a verdict, and no comparator status reaches a
cell's status (RUN_PLAN_amend_3 B6's rule).

- Patel (target 2; R13): the mean over S's columns of bicor(y, gene) on the analysis parcels (repro.mean_bicor), vs the
  TSV's value (R37 (B)); the null panels (descriptor cells) the same, "informational".
- Giacomel (target 3): cortical cells - Spearman rho of y with the |z|-weighted GEDAR score sum(|z| e) / sum(|z|) of
  S's member columns on our matrix (repro.gedar_abs_rho), the weights the list's TWAS z (R55); subcortical cells - the
  registered "not reproduced (documented source defect: misaligned structures)", with the misaligned pairing reproduced
  as a descriptor (y in the sheet's alphabetical order against our score in the paper's GEDAR atlas order, by position);
  the signed-weight rows' check is forms.signed_weight_descriptor's (R41), not this module's.
- Liu T3 (target 10, row 478): Spearman rho of the per-parcel rank-biserial enrichment of S with y (repro.liu_t3_rho).
- Pretzsch (target 16; R14, R30): the per-donor recipe on the paper's 180 left Glasser parcels (the perdonor-hcpmmp1
  build, R38) with y = eTable13 as published; lists pFDR < .01 split by sign; the row's list (its sign from the TSV
  direction text) against the set by repro.overlap_test on the genes the recipe tested, and beside it GeneOverlap's
  default genome size; k / OR / p vs the TSV.
- Hansen (target 19, HAN-C1): R^2_adj of the 7 shipped predictors and gene PC1's total dominance (netneurotools 0.3.0
  get_dominance_stats, use_adjusted_r_sq=True; R60, draft) on the shipped 68 rows; vs .533 / .027 (R37 (B)).
- Leyhausen (target 20; R63, draft): the NeuroVault decoder output of the row's image, the list = HGNC genes with
  nominal p < .01 (both signs), its overlap with the set by repro.overlap_test on the decoder's genes with a finite p
  (and GeneOverlap's default genome size beside); the OR vs the published OR; the decoder unavailable -> R14's per-donor
  recipe on dk-ctx (perdonor-dk), labelled "re-derived (per-donor parcel recipe, dk-ctx), not the decoder".
"""
from __future__ import annotations

import json
import re

import numpy as np

from . import reparcel as RP
from . import repro as RE
from . import reporting as RPT
from . import wp4_layout as L
from . import wp4_read as RD
from . import wp4_sets as WS

DESCRIPTIVE = "reproduction descriptive (amendment 4 §2)"
NOT_REPRO_DEFECT = "not reproduced (documented source defect: misaligned structures)"
_PUB = re.compile(r"\bvs (?:the published rho |the shipped value |R = |the published OR )?([−\-]?\d*\.\d+)")
_K = re.compile(r"\bk (\d+)")
_OR = re.compile(r"\bOR ([−\-]?\d*\.?\d+)")
_LIST = re.compile(r"\b(CT|SA)-(positive|negative) list")


def published_value(text: str) -> str | None:
    m = _PUB.search(text or "")
    return m.group(1).replace("−", "-") if m else None


def _ctx_y_S(plan, src, rule: str = "primary"):
    from . import run as R
    pr = R.prepare(plan, src, int(plan["maps"][0]), rule)
    return pr


def patel_row(plan, src, tsv) -> dict:
    pr = _ctx_y_S(plan, src)
    X = pr.ctx.X[:, pr.S]
    mb = RE.mean_bicor(pr.y, X)
    pub = published_value(tsv["reproduction"])
    kind = "4.1 check (R13; R37 (B))" if not plan.get("descriptor") else "4.1 check (descriptor, informational)"
    out = dict(kind=kind, functional="mean bicor", mean_bicor=mb, n_parcels=int(pr.ctx.n))
    if pub is not None:
        out["check"] = RPT.reproduction_check(pub, mb["mean_bicor"], functional="mean bicor")
    return out


def _abs_z_weights(plan, src, cls: str):
    doc, sha = src.set_doc4(plan["set_id"])
    w = doc.get("weights")
    cg = (doc.get("universe_column_gene") or {}).get(cls) or {}
    if not w:
        return None, None, sha
    return w, cg, sha


def giacomel_row(plan, src, tsv) -> dict:
    cell = plan["cell_id"]
    cls = plan["analysis_class"]
    if WS.GATED_CELLS.get(cell, ("", "", False))[0] == "deg" or plan.get("form_name") == "signed-weight":
        return dict(kind=DESCRIPTIVE, status="the signed-weight descriptor's own check (RUN_PLAN_amend_2 R41; forms)")
    pr = _ctx_y_S(plan, src)
    w, cg, sha = _abs_z_weights(plan, src, cls)
    if w is None:
        return dict(kind="4.1 check (R27; R37 (B))", status=L.STATUS_WEIGHT_COLUMN)
    S_cols = [str(pr.ctx.U.genes[i]) for i in pr.S]
    z = np.array([abs(float(w[cg[c]])) for c in S_cols], dtype=float)
    X = pr.ctx.X[:, pr.S]
    if cls == "V-DK-subcortex":
        if not src.giacomel_order_matched():          # R54 (B4): T stays by label; only this descriptor is marked
            return dict(kind=DESCRIPTIVE, registered=NOT_REPRO_DEFECT, status=RD.GIA_ORDER_NOT_MATCHED,
                        set_sha256=sha)
        score = RE.gedar_abs_score(X, z)
        dk = src.dk_table()
        name_of = {int(r["id"]): str(r["label"]) for _, r in dk.iterrows()}
        pos = {name_of[int(i)]: k for k, i in enumerate(pr.parcel_ids)}
        alpha = ["accumbensarea", "amygdala", "caudate", "hippocampus", "pallidum", "putamen", "thalamusproper"]
        if not (set(alpha) <= set(pos)):
            return dict(kind=DESCRIPTIVE, registered=NOT_REPRO_DEFECT, status="not computable (a subcortical parcel "
                        "outside the analysis parcels)")
        y_sheet = [pr.y[pos[n]] for n in alpha]
        s_atlas = [score[pos[n]] for n in L.GEDAR_SUB_ATLAS_ORDER]
        rho = RE.spearman_exact(np.asarray(y_sheet), np.asarray(s_atlas))
        return dict(kind=DESCRIPTIVE, registered=NOT_REPRO_DEFECT, misaligned_rho=float(rho),
                    rule="y in the sheet's alphabetical order against our |z|-weighted score in the paper's GEDAR "
                         "atlas order, paired by position (register §2.3; draft 'Defect')", set_sha256=sha)
    rho = RE.gedar_abs_rho(pr.y, X, z)
    rho = {k: v for k, v in rho.items() if k != "score"}
    pub = published_value(tsv["reproduction"])
    out = dict(kind="4.1 check (R27; R37 (B))", functional="|z|-weighted rho", gedar=rho, set_sha256=sha)
    if pub is not None:
        out["check"] = RPT.reproduction_check(pub, rho["rho"], functional="|z|-weighted rho")
    return out


def liu_t3_row(plan, src, tsv) -> dict:
    pr = _ctx_y_S(plan, src)
    in_group = np.zeros(pr.ctx.X.shape[1], dtype=bool)
    in_group[pr.S] = True
    r = RE.liu_t3_rho(pr.y, pr.ctx.X, in_group)
    r = {k: v for k, v in r.items() if k != "per_parcel_r"}
    pub = published_value(tsv["reproduction"])
    out = dict(kind="4.1 check (R27; R37 (B))", functional="rank-biserial", liu_t3=r)
    if pub is not None:
        out["check"] = RPT.reproduction_check(pub, r["rho"], functional="rank-biserial")
    return out


def hansen_row(plan, src, tsv) -> dict:
    if plan["cell_id"] != "HAN-C1":
        return dict(kind=DESCRIPTIVE, status="no published value for this component (register §3.7: a descriptor)")
    ct, _ = src.obj4(L.HANSEN_CT_KEY, "asd")
    pred, s2 = src.obj4(L.HANSEN_PRED_KEY, "predictors")
    src.identity4(L.HANSEN_PRED_KEY)
    r = hansen_dominance(np.asarray(pred["matrix"], dtype=float), np.asarray(ct["values"], dtype=float),
                         int(pred["pc1_column"]))
    return dict(kind=DESCRIPTIVE, **r, predictors_sha256=s2, blind=HAN_NOT_BLIND,
                checks={"R2_adj": RPT.reproduction_check(".533", r["r2_adj"], functional="R2_adj"),
                        "dominance": RPT.reproduction_check(".027", r["pc1_total_dominance"], functional="dominance")})


# asdg-skeptic C1 (2026-10-16): R60's functional and the 68-row model were chosen knowing the shipped R2_adj (.533)
HAN_NOT_BLIND = ("NOT BLIND (RUN_PLAN_amend_4 R60: the functional chosen knowing Hansen's shipped dominance values, the "
                 "layout facts taken from drafts written from the material): a reproduction check, not a verdict")
NNT_SOURCE = ("netneurotools 0.3.0 stats/regression.py get_dominance_stats (env/venv site-packages; its import fails "
              "under this venv's scipy, so it is ported here: OLS with an intercept, R^2 = 1 - SS_res / SS_tot, "
              "adjusted R^2 = 1 - (1 - R^2)(n - 1)/(n - k - 1); total dominance = the mean of the individual dominance "
              "and the partial dominances of every larger subset size; their sum equals the full adjusted R^2)")


def _r2(X, y, cols, adjusted: bool) -> float:
    A = np.column_stack([np.ones(len(y)), X[:, list(cols)]])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    res = y - A @ beta
    r2 = 1.0 - float(np.sum(res ** 2)) / float(np.sum((y - y.mean()) ** 2))
    return 1.0 - (1.0 - r2) * (len(y) - 1) / (len(y) - len(cols) - 1) if adjusted else r2


def dominance_stats(X: np.ndarray, y: np.ndarray, *, use_adjusted_r_sq: bool = True) -> dict:
    """The port of netneurotools 0.3.0's get_dominance_stats (NNT_SOURCE): every non-empty predictor subset's (adjusted)
    R^2; individual dominance = the one-predictor models; partial dominance at size s = the mean increase from adding
    the predictor over the subsets of size s that hold it; total = the mean over [individual; partials]."""
    from itertools import combinations
    X, y = np.asarray(X, dtype=float), np.asarray(y, dtype=float)
    p = X.shape[1]
    r2 = {c: _r2(X, y, c, use_adjusted_r_sq) for k in range(1, p + 1) for c in combinations(range(p), k)}
    ind = np.array([r2[(j,)] for j in range(p)])
    part = []
    for s in range(2, p + 1):
        row = []
        for j in range(p):
            sel = [c for c in combinations(range(p), s) if j in c]
            row.append(float(np.mean([r2[c] - r2[tuple(v for v in c if v != j)] for c in sel])))
        part.append(row)
    total = np.mean(np.vstack([ind[None, :]] + [np.array(part)]), axis=0) if part else ind
    full = r2[tuple(range(p))]
    if not np.isclose(total.sum(), full):
        raise AssertionError("dominance: the total dominances do not sum to the full R^2")
    return dict(total_dominance=total, individual_dominance=ind, full_r_sq=full)


def hansen_dominance(X: np.ndarray, y: np.ndarray, pc1_col: int) -> dict:
    """R60 (draft): netneurotools' dominance analysis (adjusted R^2) on the shipped 68 rows: full-model R^2_adj and the
    total dominance of the gene PC1 column."""
    m = dominance_stats(X, y, use_adjusted_r_sq=True)
    td = np.asarray(m["total_dominance"], dtype=float)
    return dict(r2_adj=float(m["full_r_sq"]), pc1_total_dominance=float(td[pc1_col]),
                total_dominance_sum=float(td.sum()), rule=NNT_SOURCE)


def _list_sign(tsv) -> int | None:
    m = _LIST.search(tsv["direction"] or "") or _LIST.search(tsv["set_S"] or "")
    if not m:
        return None
    return 1 if m.group(2) == "positive" else -1


def pretzsch_row(plan, src, tsv, recipe_inputs=None) -> dict:
    """recipe_inputs: (y on the 180 left parcels in the label list's left order, per-donor matrices (parcels x genes,
    rows in that order), HGNC gene names of the columns) - from WP4Sources.pretzsch_recipe_inputs (phase 2)."""
    sign = _list_sign(tsv)
    if sign is None:
        return dict(kind=DESCRIPTIVE, status="not computable (the row's list sign is not registered)")
    y, mats, genes = recipe_inputs if recipe_inputs is not None else src.pretzsch_recipe_inputs(plan)
    rec = RE.per_donor_recipe_t(y, mats)
    dl = RE.decoded_lists(rec, 0.01)
    universe = {genes[i] for i in dl["universe"]}
    decoded = {genes[i] for i in dl[sign]}
    doc, _ = src.set_doc(plan["set_id"])
    S = set(doc["members_hgnc"])
    ov = RE.overlap_test(decoded, S, universe=universe)
    ovd = RE.overlap_test(decoded, S, genome_size=RE.GENEOVERLAP["default_genome_size"])
    pub = {"k": (_K.search(tsv["reproduction"]) or [None, None])[1],
           "OR": (_OR.search(tsv["reproduction"]) or [None, None])[1]}
    return dict(kind=DESCRIPTIVE, recipe=dict(n_tested=rec["n_tested"], n_list=len(decoded), sign=sign,
                                              label="R14 per-donor parcel recipe on the paper's 180 left Glasser "
                                                    "parcels (R38's build)"),
                overlap=ov, overlap_geneoverlap_default=ovd, published=pub)


def leyhausen_row(plan, src, tsv, decoder_obj=None) -> dict:
    image = int(re.search(r"image (\d{6})", tsv["map"]).group(1))
    try:
        obj = decoder_obj if decoder_obj is not None else src.obj4(L.LEY_DECODER_KEY[image], "genes")[0]
        via = "the NeuroVault decoder (R45's form, mask=full)"
    except Exception:          # noqa: BLE001 - the decoder unavailable: R14's fallback (counts only)
        return dict(kind=DESCRIPTIVE, status=RP.RECIPE_DECODER.format(cls="dk-ctx") + " (phase 2: perdonor-dk)")
    genes = [g for g, p in zip(obj["genes"], obj["p"]) if p is not None]
    ps = [p for p in obj["p"] if p is not None]
    universe = set(genes)
    decoded = {g for g, p in zip(genes, ps) if p < L.LEY_DECODER_P}
    doc, _ = src.set_doc(plan["set_id"])
    ov = RE.overlap_test(decoded, set(doc["members_hgnc"]), universe=universe)
    ovd = RE.overlap_test(decoded, set(doc["members_hgnc"]), genome_size=RE.GENEOVERLAP["default_genome_size"])
    pub = (_OR.search(tsv["published_value_and_location"]) or [None, None])[1]
    return dict(kind=DESCRIPTIVE, via=via, list_rule="HGNC genes with nominal p < .01, both signs (TSV; R63)",
                n_list=len(decoded), paper_list_n=L.LEY_PAPER_LIST_N.get(image), overlap=ov,
                overlap_geneoverlap_default=ovd, published_OR=pub)


def row_reproduction(plan: dict, src, res: dict | None = None) -> dict | None:
    tsv = src._rows()[int(plan["row"])]
    t = int(plan["target_no"])
    fn = {2: patel_row, 3: giacomel_row, 10: liu_t3_row, 16: pretzsch_row, 19: hansen_row, 20: leyhausen_row}.get(t)
    if fn is None:
        return None
    from . import wp3_repro as WR
    return WR.json_safe(fn(plan, src, tsv))
