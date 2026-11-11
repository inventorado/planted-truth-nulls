"""WP4: pure readers of the declared G2 material forms (RUN_PLAN.md v3.1 §8 steps 3-5, §11; the DRAFT readings of
RUN_PLAN_amend_4.md R51-R64). Each reader takes bytes (or the guard's masked positions) and returns the group-level
object keyed by RUNNER-SIDE names only (abagen DK ids, the pinned HCP-MMP1 left names' positions, HGNC symbols); a
carrier-derived string never leaves a reader except as the gene-level members the frozen S-build itself writes (HGNC
symbols of a gene list). Nothing here prints or opens a file: the callers (wp4_material, inside fetch_extract's masked
stages) pass bytes. Every refusal is W4Refused carrying a fixed status of wp4_layout's vocabulary and counts.

Label normaliser (R54 / R59 / R60, draft): RUN_PLAN_amend_2 R42 (d)'s steps (forms.sd7_label_parse: casefold; strip
'_thickavg' / '_surfavg'; split on non-alphanumerics, drop 'ctx'; hemisphere markers l / r / lh / rh / left / right
as tokens or glued; the alias table), extended for G2 by
  - the marker 'm' (a bilateral MEAN, Giacomel's 'M_<region>_thickavg'), token or glued, which selects the LEFT id
    (bilateral-average maps are placed on the left parcels: RUN_PLAN R11 :684-685; prereg §2);
  - two aliases for the full structure names the TSV prints (rows 92 ...): thalamus -> thalamusproper,
    accumbens -> accumbensarea;
  - a declared side for unmarked labels (Patel's eTable 4 caption: "the 34 regions of the left hemisphere").
Fail closed as R42 (d): an unmatched label, conflicting markers, or two labels on one DK id refuse.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re

import numpy as np

from . import wp4_layout as L

G2_MARKERS = {"l": "L", "lh": "L", "left": "L", "r": "R", "rh": "R", "right": "R", "m": "M"}
G2_EXTRA_ALIASES = {"thalamus": "thalamusproper", "accumbens": "accumbensarea"}
# amend_5 v2 R54' (a), POST-EXPOSURE (the only alias added after the label was seen): used by the post-exposure
# version only (giacomel_sheet_object(amend5=True)); the primary reading keeps R54's table
AMEND5_ALIASES = {"pallidus": "pallidum"}
NUM_TOKEN = re.compile(r"^[-−–]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+−]?\d+)?$")


class W4Refused(Exception):
    """A refused read; .status is a wp4_layout status, .counts numbers only."""

    def __init__(self, status: str, counts: dict | None = None):
        super().__init__(status)
        self.status = status
        self.counts = dict(counts or {})


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ================================================================================================================
# labels -> abagen DK ids
# ================================================================================================================
def dk_frame(dk_csv: bytes):
    """abagen's DK table (the pinned dk_atlas_info.csv): id, label, hemisphere, structure; checked as forms does."""
    import pandas as pd
    from . import forms as FM
    return FM.dk_table_checked(pd.read_csv(io.BytesIO(dk_csv)))


def g2_label_parse(label, recognised: set, aliases: dict | None = None) -> dict:
    from . import forms as FM
    s = str(label).casefold().strip()
    for suf in FM.SD7_SUFFIXES:
        if s.endswith(suf):
            s = s[: -len(suf)]
            break
    tokens = [t for t in re.split(r"[\W_]+", s) if t and t not in FM.SD7_DROP_TOKENS]
    sides = [G2_MARKERS[t] for t in tokens if t in G2_MARKERS]
    name = "".join(t for t in tokens if t not in G2_MARKERS)
    glued = False
    if name and name not in recognised and name[0] in ("l", "r", "m") and name[1:] in recognised:
        sides.append(G2_MARKERS[name[0]])
        name, glued = name[1:], True
    extra = dict(G2_EXTRA_ALIASES, **(aliases or {}))
    name = FM.SD7_ALIASES.get(name, extra.get(name, name))
    return dict(name=name, sides=sides, glued_marker=glued)


def g2_normalise(labels, dk, *, unmarked: str | None, structures: tuple = ("cortex", "subcortex/brainstem"),
                 status: str, aliases: dict | None = None) -> dict:
    """Labels -> DK ids. unmarked: the side an unmarked label stands for ('L', declared), or None (an unmarked label
    refuses). 'M' (a bilateral mean) selects the left id. Lateral ventricles and global measures are dropped and
    counted (R42 (d)); anything else unmatched, a conflicting marker, a right-side label when only left ids are wanted,
    or two labels on one DK id refuses with `status`. Returns {"ids": [per label: DK id or None], "kinds": [...],
    "counts": {...}}."""
    from . import forms as FM
    t = dk
    names = set(t["label"])
    recognised = (names | set(FM.SD7_ALIASES) | set(G2_EXTRA_ALIASES) | set(aliases or {}) | {FM.SD7_LATVENT}
                  | set(FM.SD7_GLOBAL))
    ids, kinds = [], []
    n = dict(n_labels=0, n_matched=0, n_dropped_latvent=0, n_dropped_global=0, n_unmatched=0, n_conflicting=0,
             n_collisions=0, n_glued_markers=0, n_bilateral_mean=0, n_right=0)
    seen = {}
    for pos, lb in enumerate(labels):
        n["n_labels"] += 1
        p = g2_label_parse(lb, recognised, aliases)
        n["n_glued_markers"] += int(p["glued_marker"])
        name, sides = p["name"], set(p["sides"])
        if name == "" or name in FM.SD7_GLOBAL:
            ids.append(None)
            kinds.append("global measure (dropped)")
            n["n_dropped_global"] += 1
            continue
        if name == FM.SD7_LATVENT:
            ids.append(None)
            kinds.append("lateral ventricle (dropped)")
            n["n_dropped_latvent"] += 1
            continue
        if name not in names or len(sides) > 1:
            n["n_unmatched"] += 1
            n["n_conflicting"] += int(len(sides) > 1)
            ids.append(None)
            kinds.append("unmatched")
            continue
        side = next(iter(sides)) if sides else unmarked
        if side is None:
            n["n_unmatched"] += 1
            ids.append(None)
            kinds.append("unmatched (no side)")
            continue
        if side == "M":
            n["n_bilateral_mean"] += 1
            side = "L"
        rows = t[(t["label"] == name) & (t["hemisphere"] == side) & (t["structure"].isin(list(structures)))]
        if len(rows) != 1:
            n["n_unmatched"] += 1
            ids.append(None)
            kinds.append("unmatched")
            continue
        did = int(rows["id"].iloc[0])
        if side == "R":
            n["n_right"] += 1
        if did in seen:
            n["n_collisions"] += 1
        seen[did] = pos
        ids.append(did)
        kinds.append("matched")
        n["n_matched"] += 1
    if n["n_unmatched"] or n["n_collisions"]:
        raise W4Refused(status, n)
    return dict(ids=ids, kinds=kinds, counts=n)


def left_ids_of(dk, structure: str) -> list[int]:
    t = dk
    return [int(i) for i in t[(t["hemisphere"] == "L") & (t["structure"] == structure)]["id"]]


# ================================================================================================================
# R53 (draft): Patel eTable 4, PDF page index 25, the Estimate column by x-overlap
# ================================================================================================================
def _num(text: str) -> float | None:
    s = text.strip().replace("−", "-").replace("–", "-")
    if not NUM_TOKEN.match(s):
        return None
    try:
        x = float(s)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def lines_of(words, tol: float = 2.0) -> list[list]:
    """Words (x0, top, x1, bottom, text) grouped into lines: a word joins the line whose first word's top lies within
    tol points; lines in top order, words in x order."""
    lines: list[list] = []
    for w in sorted(words, key=lambda w: (w[1], w[0])):
        for ln in lines:
            if abs(ln[0][1] - w[1]) <= tol:
                ln.append(w)
                break
        else:
            lines.append([w])
    return [sorted(ln, key=lambda w: w[0]) for ln in sorted(lines, key=lambda ln: ln[0][1])]


def patel_from_words(words, dk) -> dict:
    """R53: the header word 'Estimate' exactly once on the page; every line below it whose Estimate-column word (the
    numeric word whose x-interval overlaps the header word's) exists is a table row; its label (the words left of its
    first numeric word, joined) normalised (unmarked = left, the caption's hemisphere); exactly 34 rows, the 34 left
    DK cortical labels each once. Returns {"ids", "values", "counts"} (ids ascending)."""
    st = L.STATUS_PATEL_LAYOUT
    head = [w for w in words if w[4].strip() == L.PATEL_HEADER_WORD]
    if len(head) != 1:
        raise W4Refused(st, {"n_header_words": len(head)})
    hx0, htop, hx1 = head[0][0], head[0][1], head[0][2]
    rows_lab, rows_val = [], []
    n_lines = n_no_value = 0
    for ln in lines_of([w for w in words if w[1] > htop + 2.0]):
        n_lines += 1
        nums = [(k, w) for k, w in enumerate(ln) if _num(w[4]) is not None]
        col = [w for _, w in nums if w[0] < hx1 and w[2] > hx0]
        if len(col) != 1:
            n_no_value += 1
            continue
        first = nums[0][0]
        label = " ".join(w[4] for w in ln[:first])
        rows_lab.append(label)
        rows_val.append(_num(col[0][4]))
    norm = g2_normalise(rows_lab, dk, unmarked="L", structures=("cortex",), status=st)
    want = sorted(left_ids_of(dk, "cortex"))
    got = [i for i in norm["ids"] if i is not None]
    counts = dict(norm["counts"], n_lines_below_header=n_lines, n_lines_without_estimate=n_no_value,
                  n_rows=len(rows_lab))
    if sorted(got) != want or len(got) != L.PATEL_N or norm["counts"]["n_right"]:
        raise W4Refused(st, counts)
    by = dict(zip(norm["ids"], rows_val))
    return dict(ids=want, values=[float(by[i]) for i in want], counts=counts,
                rule="RUN_PLAN_amend_4 R53 (draft): page index 25; header word 'Estimate'; the column by x-overlap")


def patel_parse(pdf_path, dk) -> dict:
    """pdfplumber 0.11.10 (L14, extended as RUN_PLAN_amend_3 R47 (b) did) on page index 25 only."""
    from . import wp3_pdf as WP
    pdfplumber = WP.assert_pdfplumber()
    with pdfplumber.open(str(pdf_path), pages=[L.PATEL_PAGE_INDEX + 1]) as pdf:
        pages = {int(p.page_number) - 1: p for p in pdf.pages}
        if L.PATEL_PAGE_INDEX not in pages:
            raise W4Refused(L.STATUS_PATEL_LAYOUT, {"n_pages_opened": len(pages)})
        words = WP._words(pages[L.PATEL_PAGE_INDEX])
    return patel_from_words(words, dk)


# ================================================================================================================
# R54 (draft): Giacomel's sheets (labels at position 0, the ASD / MDD columns by exact header)
# ================================================================================================================
GIA_ORDER_NOT_MATCHED = "registered order not matched"


def giacomel_sheet_object(labels, asd, mdd, dk, sheet: str, amend5: bool = False) -> dict:
    """Thickness: 34 labels -> the 34 left DK cortical ids (each once); Subcortical: 7 labels -> the 7 left aseg ids
    (each once). Values finite; the map is keyed BY LABEL. The Subcortical sheet's order is checked against the
    registered alphabetical order (TSV rows 92 ...) and only recorded (asdg-skeptic B4): an order that does not match
    leaves T by label and marks the misalignment descriptor alone ("registered order not matched")."""
    st = L.STATUS_GIA_LAYOUT
    structure = "cortex" if sheet == "thickness" else "subcortex/brainstem"
    # amend_5 v2 R54' (POST-EXPOSURE version only, amend5=True): (a) the 'pallidus' alias; (b) an unmarked Subcortical
    # label stands for the left aseg id - an INFERENCE from R54's "the 7 left aseg ids", not a frozen rule. The primary
    # reading (amend5=False) is R54 as frozen: an unmarked label refuses. Thickness stays marker-only in both.
    unmarked = "L" if (amend5 and sheet == "subcortical") else None
    norm = g2_normalise(labels, dk, unmarked=unmarked, structures=(structure,), status=st,
                        aliases=AMEND5_ALIASES if amend5 else None)
    ids = norm["ids"]
    if any(i is None for i in ids) or norm["counts"]["n_right"]:
        raise W4Refused(st, norm["counts"])
    want = sorted(left_ids_of(dk, structure))
    if sorted(ids) != want:
        raise W4Refused(st, norm["counts"])
    vals = {}
    for key, col in (("asd", asd), ("mdd", mdd)):
        if len(col) != len(ids) or any(isinstance(v, bool) or not isinstance(v, (int, float)) or
                                       not math.isfinite(float(v)) for v in col):
            raise W4Refused(st, dict(norm["counts"], column=key))
        vals[key] = [float(v) for v in col]
    out = dict(sheet=sheet, ids_in_sheet_order=list(ids), counts=norm["counts"])
    if sheet == "subcortical":
        name_of = {int(r["id"]): str(r["label"]) for _, r in dk.iterrows()}
        alias_back = {"thalamusproper": "thalamus", "accumbensarea": "accumbens"}
        order = [alias_back.get(name_of[i], name_of[i]) for i in ids]
        out["order_matched"] = tuple(order) == L.GIA_SUB_ORDER
        out["order_check"] = ("registered alphabetical order (TSV rows 92 ...)" if out["order_matched"]
                              else GIA_ORDER_NOT_MATCHED)
    for key in ("asd", "mdd"):
        by = dict(zip(ids, vals[key]))
        out[key] = {"ids": want, "values": [by[i] for i in want]}
        out[f"{key}_sheet_order"] = vals[key]
    return out


def giacomel_compare(gov: dict, cmp_: dict) -> dict:
    """claims_register.md:1457-1459 / RUN_PLAN.md:1470-1471: the count of differing cells only (93de089 governs)."""
    out = {}
    for sheet in ("thickness", "subcortical"):
        a, b = gov.get(sheet), cmp_.get(sheet)
        if a is None or b is None:
            out[sheet] = "not compared (a sheet not read)"
            continue
        n = 0
        tot = 0
        for key in ("asd", "mdd"):
            for x, y in zip(a[key]["values"], b[key]["values"]):
                tot += 1
                n += int(x != y)
            if a[key]["ids"] != b[key]["ids"]:
                n += len(a[key]["ids"])
        out[sheet] = {"n_cells_compared": tot, "n_cells_differing": n}
    return out


# ================================================================================================================
# delimited text (TSV / CSV) by declared headers
# ================================================================================================================
def _table(data: bytes, sep: str) -> list[list[str]]:
    text = data.decode("utf-8-sig").replace("\r\n", "\n")
    return [r for r in csv.reader(io.StringIO(text), delimiter=sep)]


def header_positions(header: list, wanted: tuple, status: str) -> dict:
    pos = {}
    for w in wanted:
        hits = [k for k, h in enumerate(header) if h.strip() == w]
        if len(hits) != 1:
            raise W4Refused(status, {"n_header_matches": len(hits)})
        pos[w] = hits[0]
    return pos


def _float(v: str, status: str) -> float | None:
    s = v.strip()
    if s == "" or s.casefold() in ("na", "nan", "n/a"):
        return None
    try:
        x = float(s)
    except ValueError:
        raise W4Refused(status, {"non_numeric": 1}) from None
    return x if math.isfinite(x) else None


# ---- R59 (draft): Liu T3 -----------------------------------------------------------------------------------------
def enigma_toolbox(data: bytes, dk, kind: str) -> dict:
    """An ENIGMA Toolbox summary-statistics CSV: the exact headers 'Structure' and 'd_icv'; rows normalised (R42 (d)
    + the G2 markers; ventricles and global rows dropped, counted); CortThick 68 rows, SubVol 16 rows. Returns
    {"by_id": {DK id: d_icv}, "counts"}."""
    st = L.STATUS_ENIGMA_LAYOUT
    rows = [r for r in _table(data, ",") if any(c.strip() for c in r)]
    if not rows:
        raise W4Refused(st, {"n_rows": 0})
    pos = header_positions(rows[0], (L.ENIGMA_LABEL_HEADER, L.ENIGMA_VALUE_HEADER), st)
    body = rows[1:]
    want_n = L.ENIGMA_N_CT if kind == "cortthick" else L.ENIGMA_N_SV
    if len(body) != want_n:
        raise W4Refused(st, {"n_rows": len(body), "expected": want_n})
    labels = [r[pos[L.ENIGMA_LABEL_HEADER]] for r in body]
    structure = "cortex" if kind == "cortthick" else "subcortex/brainstem"
    norm = g2_normalise(labels, dk, unmarked=None, structures=(structure,), status=st)
    vals = [_float(r[pos[L.ENIGMA_VALUE_HEADER]], st) for r in body]
    by = {int(i): v for i, v in zip(norm["ids"], vals) if i is not None}
    if kind == "subvol" and norm["counts"]["n_dropped_latvent"] != 2:
        raise W4Refused(st, dict(norm["counts"], why="not both lateral ventricles"))
    return dict(by_id=by, counts=norm["counts"])


def liu_t3_map(ct: dict, sv: dict, dk) -> dict:
    """R59: the L / R average per DK name (both finite, else the parcel's value is missing), placed on the left V-DK
    parcels (34 cortical + 7 subcortical; the brainstem has no ENIGMA value -> missing)."""
    t = dk
    by_name_side = {(str(r["label"]), str(r["hemisphere"])): int(r["id"]) for _, r in t.iterrows()}
    out_ids, out_vals, n_missing = [], [], 0
    both = {**ct["by_id"], **sv["by_id"]}
    for _, r in t[t["hemisphere"].isin(["L", "B"])].iterrows():
        did = int(r["id"])
        name = str(r["label"])
        lv = both.get(by_name_side.get((name, "L")))
        rv = both.get(by_name_side.get((name, "R")))
        v = (lv + rv) / 2.0 if (lv is not None and rv is not None) else None
        n_missing += int(v is None)
        out_ids.append(did)
        out_vals.append(v)
    return dict(ids=out_ids, values=out_vals, n_missing=n_missing,
                rule="RUN_PLAN_amend_4 R59 (draft): (L + R) / 2 of d_icv per DK name, on the left V-DK parcels; "
                     "lateral ventricles excluded (prereg.md:298)")


# ---- R60 (draft): Hansen --------------------------------------------------------------------------------------------
def numeric_matrix(data: bytes, *, n_rows: int, n_cols: int | None, status: str) -> dict:
    """A comma-delimited numeric matrix: no header, or one header row of non-numeric cells (its texts are never
    kept); exactly n_rows data rows (and n_cols columns if given); every cell finite."""
    rows = [r for r in _table(data, ",") if any(c.strip() for c in r)]
    has_header = bool(rows) and any(_num(c) is None for c in rows[0])
    body = rows[1:] if has_header else rows
    if len(body) != n_rows:
        raise W4Refused(status, {"n_rows": len(body), "expected": n_rows})
    widths = {len(r) for r in body}
    if len(widths) != 1 or (n_cols is not None and widths != {n_cols}):
        raise W4Refused(status, {"widths": sorted(widths)})
    M = np.empty((n_rows, widths.pop()), dtype=float)
    for i, r in enumerate(body):
        for j, c in enumerate(r):
            x = _num(c)
            if x is None:
                raise W4Refused(status, {"non_numeric": 1})
            M[i, j] = x
    return dict(matrix=M, has_header=has_header)


def hansen_ct(data: bytes) -> np.ndarray:
    m = numeric_matrix(data, n_rows=L.HANSEN_N_ROWS, n_cols=L.HANSEN_CT_SHAPE[1], status=L.STATUS_HANSEN_LAYOUT)
    if m["has_header"]:
        raise W4Refused(L.STATUS_HANSEN_LAYOUT, {"header": 1})   # "column asd (index 2)": a headerless matrix
    return m["matrix"][:, L.HANSEN_ASD_INDEX]


def hansen_pc1(data: bytes) -> np.ndarray:
    m = numeric_matrix(data, n_rows=L.HANSEN_N_ROWS, n_cols=1, status=L.STATUS_HANSEN_LAYOUT)
    return m["matrix"][:, 0]


def hansen_predictors(data: bytes, pc1: np.ndarray) -> dict:
    """R60 (draft): 68 x 7 numeric (a header row allowed); the gene PC1 column = the one column whose values equal the
    shipped gene_pc1.csv's after z-scoring (|r| > 1 - 1e-9), exactly one, else not computable."""
    m = numeric_matrix(data, n_rows=L.HANSEN_N_ROWS, n_cols=L.HANSEN_N_PREDICTORS, status=L.STATUS_HANSEN_LAYOUT)
    X = m["matrix"]
    z = (pc1 - pc1.mean()) / pc1.std()
    hits = []
    for j in range(X.shape[1]):
        c = X[:, j]
        if c.std() == 0:
            continue
        r = float(np.corrcoef(c, z)[0, 1])
        if abs(r) > 1 - 1e-9:
            hits.append(j)
    if len(hits) != 1:
        raise W4Refused("not computable (gene PC1 not identified among the shipped predictors)", {"n_hits": len(hits)})
    return dict(matrix=X, pc1_column=hits[0], has_header=m["has_header"])


def cammoun_order(data: bytes, dk) -> dict:
    """R60 (draft): the Cammoun 2012 info CSV, exact headers label / scale / hemisphere / structure; the rows of
    scale033 and structure cortex in file order: 68, the first 34 right and the last 34 left (the register's 'left
    rows 35-68'); names via the G2 normaliser with the row's hemisphere as the side; each left DK cortical id once.
    Returns {"left_row_ids": [DK id of rows 35..68 in order]}."""
    st = L.STATUS_CAMMOUN
    rows = [r for r in _table(data, ",") if any(c.strip() for c in r)]
    if not rows:
        raise W4Refused(st, {"n_rows": 0})
    pos = header_positions(rows[0], L.CAMMOUN_HEADERS, st)
    sel = [r for r in rows[1:] if r[pos["scale"]].strip() == L.CAMMOUN_SCALE
           and r[pos["structure"]].strip() == L.CAMMOUN_STRUCTURE]
    if len(sel) != L.HANSEN_N_ROWS:
        raise W4Refused(st, {"n_rows": len(sel)})
    hemi = [r[pos["hemisphere"]].strip().upper() for r in sel]
    if hemi != ["R"] * 34 + ["L"] * 34:
        raise W4Refused(st, {"hemisphere_order": "not 34 R then 34 L"})
    left_labels = [r[pos["label"]] for r in sel[34:]]
    norm = g2_normalise(left_labels, dk, unmarked="L", structures=("cortex",), status=st)
    if sorted(i for i in norm["ids"] if i is not None) != sorted(left_ids_of(dk, "cortex")):
        raise W4Refused(st, norm["counts"])
    return dict(left_row_ids=list(norm["ids"]), counts=norm["counts"])


# ---- R61 (draft): Pretzsch ----------------------------------------------------------------------------------------
def _feature_of(header: str):
    """R61 (draft): CT iff the header's alphanumeric tokens hold 'ct' or 'thickness'; SA iff they hold 'sa', or both
    'surface' and 'area'; a header naming both, or neither, names no feature."""
    toks = set(t for t in re.split(r"[^0-9a-z]+", header.casefold()) if t)
    ct = bool(toks & {"ct", "thickness"})
    sa = "sa" in toks or {"surface", "area"} <= toks
    return "CT" if (ct and not sa) else "SA" if (sa and not ct) else None


def pretzsch_csv(data: bytes, left_names: list, amend5: bool = False) -> dict:
    """R61 (draft): the derived eTable13 CSV. The label column = the one column holding all 180 pinned left HCP-MMP1
    names (each once); the CT / SA columns = the numeric columns whose header tokens name one feature ('ct' /
    'thickness'; 'sa' / 'surface' / 'area'), exactly one each; the rows = the 180 left-name rows. Returns
    {"CT": [value per left name, in left_names order], "SA": [...], "counts"}."""
    st = L.STATUS_PRE_LAYOUT
    rows = [r for r in _table(data, ",") if any(c.strip() for c in r)]
    if len(rows) < 2:
        raise W4Refused(st, {"n_rows": len(rows)})
    header, body = rows[0], rows[1:]
    # amend_5 v2 R61' (POST-EXPOSURE version only, amend5=True): a name is compared with '.' and '-' taken as equal
    # (hcp_name_key); the one-to-one match and the count of 180 are kept, and every pair matched only through the rule
    # must be exactly R's make.names of the pinned name. The primary reading (amend5=False) is R61 as frozen: exact.
    key = hcp_name_key if amend5 else (lambda x: str(x).strip())
    keys = [key(n) for n in left_names]
    if amend5 and (len(set(keys)) != len(keys) or len(keys) != L.PRE_N_LEFT):
        raise W4Refused(st, {"n_left_name_keys": len(set(keys))})
    want = set(keys)
    label_cols = [j for j in range(len(header))
                  if sum(1 for r in body if j < len(r) and key(r[j]) in want) == len(want)]
    if len(label_cols) != 1:
        raise W4Refused(st, {"n_label_columns": len(label_cols)})
    lc = label_cols[0]
    left_rows = [r for r in body if lc < len(r) and key(r[lc]) in want]
    if len(left_rows) != len(want) or len({key(r[lc]) for r in left_rows}) != len(want):
        raise W4Refused(st, {"n_left_rows": len(left_rows)})
    pinned_of = {key(n): n for n in left_names}
    pairs = [(pinned_of[key(r[lc])], r[lc].strip()) for r in left_rows if r[lc].strip() != pinned_of[key(r[lc])]]
    if amend5 and any(c != r_make_names(n) for n, c in pairs):   # only make.names' own '-' -> '.' is undone
        raise W4Refused(st, {"n_pairs_not_make_names": sum(1 for n, c in pairs if c != r_make_names(n))})
    feats = {}
    for j, h in enumerate(header):
        if j == lc:
            continue
        f = _feature_of(h)
        if f is None:
            continue
        try:
            col = [_float(r[j], st) for r in left_rows]
        except W4Refused:
            continue
        if any(v is None for v in col):
            continue
        feats.setdefault(f, []).append(col)
    if sorted(feats) != ["CT", "SA"] or any(len(v) != 1 for v in feats.values()):
        raise W4Refused(st, {"features": {k: len(v) for k, v in feats.items()}})
    by = {f: dict(zip((key(r[lc]) for r in left_rows), feats[f][0])) for f in feats}
    counts = {"n_rows": len(body), "n_left_rows": len(left_rows)}
    if amend5:
        counts.update(n_names_dot_dash=len(pairs), n_pairs_make_names=sum(1 for n, c in pairs if c == r_make_names(n)))
    return dict(CT=[by["CT"][k] for k in keys], SA=[by["SA"][k] for k in keys], counts=counts)


def r_make_names(name: str) -> str:
    """R's make.names(name) for one name (R >= 2.x, allow_ = TRUE): every character outside [A-Za-z0-9._] -> '.';
    a name not starting with a letter, or with a dot followed by a digit, gets an 'X' prefix; reserved words get a '.'
    suffix (none of these occur in HCP-MMP1 names)."""
    s = re.sub(r"[^A-Za-z0-9._]", ".", str(name))
    if not re.match(r"[A-Za-z]|\.(?![0-9])", s):
        s = "X" + s
    return s


def hcp_name_key(name) -> str:
    """amend_5 R61': an HCP-MMP1 label compared with '.' and '-' taken as equal (an R make.names-style '-' -> '.')."""
    return str(name).strip().replace(".", "-")


# ---- R55 (draft): Giacomel's repository lists ------------------------------------------------------------------------
def repo_list(data: bytes, hg) -> dict:
    """A results/<D>/<D>_<scheme>_genes_thr_<t>.tsv list: tab-delimited; the exact header gene_name (and gene, the
    Ensembl id, used first when present: claims_register.md:335-336); the weight = the first of LIST_WEIGHT_HEADERS
    present. Returns {"members": [HGNC], "weights": {HGNC: mean weight} | None, "counts", "weight_column_rule"}.
    Duplicate HGNC genes: one member, weight = the mean of its rows' weights (RUN_PLAN_amend_2 R42 (a)'s rule), counted."""
    st = L.STATUS_LIST_LAYOUT
    rows = [r for r in _table(data, "\t") if any(c.strip() for c in r)]
    if not rows:
        raise W4Refused(st, {"n_rows": 0})
    header = [h.strip() for h in rows[0]]
    if header.count(L.LIST_SYMBOL_HEADER) != 1:
        raise W4Refused(st, {"n_symbol_headers": header.count(L.LIST_SYMBOL_HEADER)})
    ps = header.index(L.LIST_SYMBOL_HEADER)
    pe = header.index(L.LIST_ENSEMBL_HEADER) if header.count(L.LIST_ENSEMBL_HEADER) == 1 else None
    wcol = next((w for w in L.LIST_WEIGHT_HEADERS if header.count(w) == 1), None)
    pw = header.index(wcol) if wcol else None
    members, w_by = [], {}
    how = {}
    n_unmapped = 0
    for r in rows[1:]:
        sym = r[ps].strip() if ps < len(r) else ""
        ens = r[pe].strip() if (pe is not None and pe < len(r)) else None
        g, h = hg.resolve("ensembl" if ens else None, ens, sym or None)
        h = h.split(" (")[0]
        how[h] = how.get(h, 0) + 1
        if g is None:
            n_unmapped += 1
            continue
        if g not in w_by:
            members.append(g)
            w_by[g] = []
        if pw is not None:
            x = _float(r[pw], st) if pw < len(r) else None
            if x is None:
                raise W4Refused(st, {"weight_missing": 1})
            w_by[g].append(x)
    weights = {g: float(np.mean(v)) for g, v in w_by.items()} if pw is not None else None
    return dict(members=members, weights=weights,
                counts=dict(n_rows=len(rows) - 1, n_members=len(members), n_unmapped=n_unmapped,
                            n_duplicate_rows=(len(rows) - 1 - n_unmapped - len(members)), hgnc_mapping=how),
                weight_column=("found" if pw is not None else "none"), weight_column_rule=L.LIST_WEIGHT_RULE)


# ---- R56 (draft): the paper's GEDAR maps -----------------------------------------------------------------------------
def gedar_map(data: bytes, dk) -> dict:
    """A results/<D>/<D>_TPRS_thr_<t>.tsv GEDAR map: tab-delimited, a header row; the label column = position 0, whose
    cells are either all abagen DK ids (integers) or all names the G2 normaliser maps to DK ids (sides required); the
    value = the one other numeric column. Returns {"by_id": {DK id: value}}; only the left ids are used downstream."""
    st = L.STATUS_GEDAR_LAYOUT
    rows = [r for r in _table(data, "\t") if any(c.strip() for c in r)]
    if len(rows) < 2:
        raise W4Refused(st, {"n_rows": len(rows)})
    body = rows[1:]
    widths = {len(r) for r in body}
    if len(widths) != 1:
        raise W4Refused(st, {"widths": sorted(widths)})
    width = widths.pop()
    numeric_cols = []
    for j in range(1, width):
        col = [_num(r[j]) for r in body]
        if all(v is not None for v in col):
            numeric_cols.append(col)
    if len(numeric_cols) != 1:
        raise W4Refused(st, {"n_numeric_columns": len(numeric_cols)})
    labels = [r[0].strip() for r in body]
    ids_known = {int(i) for i in dk["id"]}
    if all(s.isdigit() for s in labels):
        ids = [int(s) for s in labels]
        if not set(ids) <= ids_known or len(set(ids)) != len(ids):
            raise W4Refused(st, {"ids": "not abagen DK ids, each once"})
        how = "abagen DK ids"
    else:
        norm = g2_normalise(labels, dk, unmarked=None, status=st)
        ids = norm["ids"]
        how = "names (G2 normaliser)"
    by = {int(i): float(v) for i, v in zip(ids, numeric_cols[0]) if i is not None}
    return dict(by_id=by, label_form=how, n_rows=len(body))


# ---- R52 (draft): figshare 3501911 ------------------------------------------------------------------------------------
def figshare_files(meta: bytes) -> dict:
    """The article's API document: files[] with name, size, computed_md5, download_url. The volume = the one file named
    exactly HCP_VOLUME_NAME; the label list = the one file whose name is the volume's stem + '.txt'. Names are compared
    in memory; only their sha256 is recorded."""
    doc = json.loads(meta.decode("utf-8"))
    files = doc.get("files") if isinstance(doc, dict) else None
    if not isinstance(files, list):
        raise W4Refused(L.STATUS_PRE_LAYOUT, {"files": 0})
    stem = L.HCP_VOLUME_NAME[: -len(".nii.gz")]
    vol = [f for f in files if f.get("name") == L.HCP_VOLUME_NAME]
    lab = [f for f in files if f.get("name") == stem + L.HCP_LABEL_EXT]
    from . import reparcel as RP
    if len(vol) != 1 or len(lab) != 1:
        raise W4Refused(RP.STATUS_GLASSER, {"n_volume": len(vol), "n_label_list": len(lab)})
    out = {}
    for k, f in (("volume", vol[0]), ("labels", lab[0])):
        md5 = f.get("computed_md5")
        if not (isinstance(f.get("size"), int) and isinstance(md5, str) and re.fullmatch(r"[0-9a-f]{32}", md5)
                and isinstance(f.get("download_url"), str) and f["download_url"].startswith("https://")):
            raise W4Refused(RP.STATUS_GLASSER, {"file_fields": k})
        out[k] = dict(size=int(f["size"]), md5=md5, url=f["download_url"],
                      name_sha256=hashlib.sha256(str(f["name"]).encode("utf-8")).hexdigest())
    out["n_files"] = len(files)
    return out


def hcp_left_names(label_text: str) -> dict:
    """R15: the label list (RP4 form), its left ids by the 'L_' prefix (read, never assumed): 180 required."""
    from . import reparcel as RP
    lst = RP.read_label_list(label_text)
    left = RP.left_ids(lst)
    if len(left) != L.HCP_N_LEFT:
        raise RP.ReparcelRefused(RP.STATUS_GLASSER)
    name_of = dict(lst)
    return dict(label_list=lst, left_ids=left, left_names=[name_of[i] for i in left])


# ---- R58 (draft): the R script's packages and inputs ----------------------------------------------------------------
_R_LIB = re.compile(r"\b(?:library|require|requireNamespace)\s*\(\s*['\"]?([A-Za-z][A-Za-z0-9.]*)['\"]?")
_R_NS = re.compile(r"\b([A-Za-z][A-Za-z0-9.]*):::?[A-Za-z._]")
_R_READ_FUNS = (r"(?:read\.csv|read\.table|read\.delim|read_tsv|read_csv|read_excel|fread|readRDS|"
                r"read\.xlsx|read_xlsx)")
_R_READ = re.compile(r"\b" + _R_READ_FUNS + r"\s*\(\s*(?:file\s*=\s*)?['\"]([^'\"]+)['\"]")
# amend_5 R58' (b): a read call whose path is a variable assigned exactly ONE string literal at the top level
# (`twas_path <- "..."`, script line 33 / 54); the output folders the write calls name through
# paste0(<such a variable>, "<literal>") and the assigned absolute folder literals (ending in '/')
_R_READ_VAR = re.compile(r"\b" + _R_READ_FUNS + r"\s*\(\s*(?:file\s*=\s*)?([A-Za-z.][A-Za-z0-9._]*)\s*[,)]")
_R_ASSIGN = re.compile(r"^([A-Za-z.][A-Za-z0-9._]*)\s*(?:<-|=)\s*['\"]([^'\"]+)['\"]\s*$", re.M)
_R_WRITE_PASTE = re.compile(r"\b(?:write_tsv|write_csv|write_delim|write\.csv|write\.table|write\.xlsx|saveRDS|ggsave|"
                            r"pdf|png)\s*\([^\n]*?paste0\s*\(\s*([A-Za-z.][A-Za-z0-9._]*)\s*,\s*['\"]([^'\"]*)['\"]")
R_BASE = frozenset(("base", "stats", "utils", "methods", "graphics", "grDevices", "datasets", "tools", "parallel",
                    "grid", "splines", "stats4", "tcltk", "compiler"))


def r_script_requirements(text: str) -> dict:
    """R58 (draft): the packages a script names (library / require / requireNamespace calls and pkg:: references; base
    packages excluded) and the file paths its read calls name as string literals. Comments are removed first."""
    body = "\n".join(ln.split("#", 1)[0] for ln in text.splitlines())
    pk = set(_R_LIB.findall(body)) | set(_R_NS.findall(body))
    pk = sorted(p for p in pk if p not in R_BASE)
    reads = set(_R_READ.findall(body))
    assigned: dict = {}
    for var, lit in _R_ASSIGN.findall(body):
        assigned.setdefault(var, set()).add(lit)
    single = {v: next(iter(ls)) for v, ls in assigned.items() if len(ls) == 1}
    var_reads = {single[v] for v in _R_READ_VAR.findall(body) if v in single}
    out_dirs = set()
    for var, lit in _R_WRITE_PASTE.findall(body):
        if var in single:
            full = single[var] + lit
            out_dirs.add(full.rsplit("/", 1)[0] if "/" in full else "")
    out_dirs |= {v for v in single.values() if v.endswith("/") and v.startswith("/")}
    out_dirs = {d.rstrip("/") for d in out_dirs if d.strip("/")}
    return dict(packages=pk, read_paths=sorted(reads | var_reads), n_lines=len(text.splitlines()),
                n_read_vars=len(var_reads - reads), out_dirs=sorted(out_dirs),
                abs_strings=sorted({v for v in single.values() if v.startswith("/")}))


# ---- R58 (f) (draft): the post-mortem DEG sets by the TSV's definition --------------------------------------------
def ahba_hpa_pool(ahba_header_csv: bytes, hpa_tsv: bytes) -> set:
    """The authors' AHBA matrix's gene columns (its header row, the first column the parcel label) intersected with the
    HPA brain-elevated list's symbols (the first of HPA_SYMBOL_ALTERNATIVES the header holds)."""
    head = ahba_header_csv.decode("utf-8-sig").splitlines()[0]
    genes = {g.strip().strip('"') for g in head.split(",")[1:] if g.strip()}
    rows = _table(hpa_tsv, "\t")
    if not rows:
        raise W4Refused(L.STATUS_DEG, {"hpa_rows": 0})
    hdr = [h.strip() for h in rows[0]]
    col = next((hdr.index(a) for a in L.HPA_SYMBOL_ALTERNATIVES if hdr.count(a) == 1), None)
    if col is None:
        raise W4Refused(L.STATUS_DEG, {"hpa_symbol_column": 0})
    hpa = {r[col].strip() for r in rows[1:] if col < len(r) and r[col].strip()}
    return genes & hpa


def deg_set(symbols, dxs, ps, lfcs, pool: set, dx: str, thr: int) -> dict:
    """The TSV's definition: the rows of Dx == dx whose gene lies in the AHBA x HPA pool (n), ordered by p.value
    ascending (file order on ties), the top round(n x thr / 100); weights = logFC. Returns members, weights, n."""
    rows = []
    for k, (g, d, p_, w) in enumerate(zip(symbols, dxs, ps, lfcs)):
        if not isinstance(d, str) or d.strip() != dx or not isinstance(g, str) or g.strip() not in pool:
            continue
        if isinstance(p_, bool) or not isinstance(p_, (int, float)) or not isinstance(w, (int, float)):
            raise W4Refused(L.STATUS_DEG, {"non_numeric": 1})
        rows.append((float(p_), k, g.strip(), float(w)))
    n = len({r[2] for r in rows})
    if dx == "ASD" and n != L.DEG_POOL_ASD:
        raise W4Refused(L.STATUS_DEG_POOL, {"n_pool": n})
    m = int(round(n * thr / 100.0))
    top = sorted(rows)[:m]
    return {"members": [r[2] for r in top], "weights": {r[2]: r[3] for r in top}, "n_pool": n, "m": m,
            "rule": "TSV rows 109-131: Dx, AHBA x HPA, top round(n x thr) by p.value, weights logFC (R58 (f), draft)"}


# ---- R58 (f) v2 (asdg-skeptic B5): the DEG lists the paper's script writes ----------------------------------------
_THR = re.compile(r"thr[_-]?(\d+)(?![0-9])")
R17_MAP_NAME = re.compile(r"^(ASD|MDD)_literature_TPRS_thr_(1|5|10)\.tsv$")


def _delim_header(data: bytes):
    text = data.decode("utf-8-sig", "replace").replace("\r\n", "\n")
    first = text.split("\n", 1)[0]
    sep = "\t" if "\t" in first else ","
    return sep, _table(data, sep)


def deg_output_key(rel_path: str, data: bytes):
    """A created file is a DEG list of (Dx, thr) iff: its name holds exactly one of the tokens ASD / MDD and exactly one
    'thr<t>' with t in 1 / 5 / 10, and its header row holds exactly one `logFC` and a symbol column (gene_name, else the
    first of DEG_SYMBOL_ALTERNATIVES held once). Returns ((dx, thr), symbol header) or None. Names are compared in
    memory only."""
    name = rel_path.rsplit("/", 1)[-1]
    if not re.search(r"\.(tsv|csv|txt)$", name):
        return None
    toks = re.split(r"[^A-Za-z0-9]+", name)
    dxs = [t for t in toks if t in ("ASD", "MDD")]
    thr = _THR.findall(name)
    if len(dxs) != 1 or len(thr) != 1 or thr[0] not in ("1", "5", "10"):
        return None
    try:
        _sep, rows = _delim_header(data)
    except (UnicodeDecodeError, csv.Error):
        return None
    if not rows:
        return None
    hdr = [h.strip() for h in rows[0]]
    if hdr.count("logFC") != 1:
        return None
    sym = next((a for a in (L.LIST_SYMBOL_HEADER,) + L.DEG_SYMBOL_ALTERNATIVES if hdr.count(a) == 1), None)
    if sym is None:
        return None
    return (dxs[0], int(thr[0])), sym


def deg_output_key_adapted(rel_path: str, data: bytes, ad: dict):
    """Q3 (amend_4 v3): the operator's format-only adaptation (validated by wp4_material.deg_adaptation): the file name
    fullmatches name_regex with named groups dx (ASD / MDD) and thr (1 / 5 / 10); the header (delimiter given, else
    tab if the first line holds one, else comma) holds symbol_header and weight_header exactly once each. Returns
    ((dx, thr), {"symbol", "weight", "delimiter"}) or None."""
    name = rel_path.rsplit("/", 1)[-1]
    m = re.fullmatch(ad["name_regex"], name)
    if not m or m.groupdict().get("dx") not in ("ASD", "MDD") or m.groupdict().get("thr") not in ("1", "5", "10"):
        return None
    sep = ad.get("delimiter")
    try:
        if sep is None:
            sep, rows = _delim_header(data)
        else:
            rows = _table(data, sep)
    except (UnicodeDecodeError, csv.Error):
        return None
    if not rows:
        return None
    hdr = [h.strip() for h in rows[0]]
    if hdr.count(ad["symbol_header"]) != 1 or hdr.count(ad["weight_header"]) != 1:
        return None
    return (m.group("dx"), int(m.group("thr"))), {"symbol": ad["symbol_header"], "weight": ad["weight_header"],
                                                  "delimiter": sep}


def deg_list_rows(data: bytes, sym: str, weight: str = "logFC", delimiter: str | None = None) -> list:
    """The S-build's raw rows of a script DEG list: the symbol, weight = logFC (the TSV: 'weights = logFC'); a Q3
    adaptation may name the headers / delimiter (format only)."""
    if delimiter is None:
        _sep, rows = _delim_header(data)
    else:
        rows = _table(data, delimiter)
    hdr = [h.strip() for h in rows[0]]
    ps, pw = hdr.index(sym), hdr.index(weight)
    out = []
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        if max(ps, pw) >= len(r):
            raise W4Refused(L.STATUS_DEG, {"short_row": 1})
        w = _num(r[pw])
        if w is None or not r[ps].strip():
            raise W4Refused(L.STATUS_DEG, {"non_numeric": 1})
        out.append({"kind": None, "id": None, "symbol": r[ps].strip(), "weight": float(w)})
    return out


def deg_check(script_symbols, python_set: dict | None, dx: str, thr: int) -> dict:
    """The check of a script-derived DEG set (B5): m equals the TSV's round(n x thr / 100) on the AHBA x HPA pool of the
    TSV definition (the Python recompute's n; ASD's n must be the registered 3,599); the Python set recorded beside as a
    cross-check (overlap counts), never replacing S."""
    syms = list(dict.fromkeys(script_symbols))
    if python_set is None:
        return {"passed": False, "why": "the TSV definition could not be computed (the pool or the workbook)",
                "m_script": len(syms)}
    m_def = python_set["m"]
    a, b = set(syms), set(python_set["members"])
    return {"passed": len(syms) == m_def and (dx != "ASD" or python_set["n_pool"] == L.DEG_POOL_ASD),
            "m_script": len(syms), "m_definition": m_def, "n_pool": python_set["n_pool"],
            "cross_check": {"n_common": len(a & b), "n_script_only": len(a - b), "n_python_only": len(b - a),
                            "equal": a == b, "role": "cross-check only (the script's S governs)"}}
