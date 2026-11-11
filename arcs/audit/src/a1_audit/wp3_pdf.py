"""WP3: Segura MOESM2 pp. 38-39 under RUN_PLAN section 8's PDF rule (RUN_PLAN_amend_3.md v2.1, FROZEN sha256
da3f3b8b..., R47; L14 extended to this ungated PDF). Nothing here prints: the callers print counts and hashes only.

- the parser is pdfplumber 0.11.10 (asserted before any parse: L14, extended); another version is an environment fault
  (PdfEnvironmentFault): the material stage stops for the operator and writes no final record (fix round 3, C (c));
- only page index 38 (Table S7) and page index 37 (Table S6) are opened (pdfplumber.open(pages=[38, 39])) and parsed,
  each the one page its comparator needs (the page-tree walk is a declared residual: PAGES_RESIDUAL);
- Table S7 (R47 (c)): a pdfplumber port of the frozen PyMuPDF rule `src_register/s_extract.segura_s7`
  (s_extract.py:152-195): the same geometry on pdfplumber's `extract_words()` (default tolerances) - the title
  assertion, the unique '#' header word, the unique '*Only' footnote word, the value tokens matching
  ^[0-9.]+(/[0-9.]+)?$, the wrap repair, 77 printed rows / 78 terms; the four value tokens are KEPT (genes, expected,
  fold enrichment, FDR, in the TSV's order); a row of k names joined by ' / ' splits EACH of its four tokens on '/' and
  a token without exactly k parts refuses the read (C7). The cross-tool test ties its names, printed rows and order to
  the frozen function's (tests/test_wp3_amend3.py, frozen leg under C:\\Python313 -E -P).
- cross-checks before saving (R47 (d)): the 78 names in printed order equal SEGURA_S7_TERMS.json's `term` fields; each
  term's printed row equals the file's `printed_row`; the 7 named terms' values equal the TSV's to its printed
  precision (|parsed - TSV| <= half a unit in the TSV text's last digit); every value finite, genes integers.
- Table S6 (R47 (f)): exactly one text line of page 37 contains 'Table S6'; the words below that line, split on ',' and
  ';', stripped of whitespace and of trailing footnote marks (* dagger double-dagger); a token is a gene iff it equals a
  symbol of Table S4's raw list exactly (the S-build's pinned input); exactly 107 distinct genes, else refused.
- the read-back (R47 (g)): a second parse (a fresh pdfplumber.open, the same rule on the same page) must equal the
  stored object read back from disk.
Every refusal is a PdfRefused carrying a fixed check label (vocabulary), never a carrier string.
"""
from __future__ import annotations

import math
import re
from decimal import Decimal
from pathlib import Path

PDFPLUMBER_VERSION = "0.11.10"          # RUN_PLAN.md L14 (:154), extended to MOESM2 by RUN_PLAN_amend_3 R47 (b)
S7_PAGE, S6_PAGE = 38, 37                # page indexes (p. 39, p. 38); s_extract.py:154
S7_TITLE = "Table S7. Genetic Ontology (GO) terms"     # s_extract.py:156
S6_CAPTION = "Table S6"
NUM = re.compile(r"^[0-9.]+(/[0-9.]+)?$")               # s_extract.py:149
VALUE_KEYS = ("genes", "expected", "fold", "fdr")       # the TSV's order: genes / expected / fold / FDR p
S7_ROWS, S7_TERMS = 77, 78
S6_N = 107                                              # TSV row 1: "Table S6 (107 genes ...)"
FOOTNOTE_MARKS = "*\u2020\u2021"
TSV_S7 = re.compile(r"genes / expected / fold / FDR p = ([0-9.eE+-]+) / ([0-9.eE+-]+) / ([0-9.eE+-]+) / "
                    r"([0-9.eE+-]+)")

# fixed check labels (the only text a refusal carries)
CHECK_VERSION = "pdfplumber version differs from 0.11.10"
CHECK_PAGES = "the PDF has no page index 38 / 37"
CHECK_TITLE = "Table S7 title not on page index 38"
CHECK_HEADER = "the number-sign header word not unique"
CHECK_FOOT = "the Only footnote word not unique"
CHECK_TOKEN = "a non-numeric token in the value columns"
CHECK_ORPHAN = "a value line without a term"
CHECK_FOUR = "a printed row without four value tokens"
CHECK_ROWS = "printed rows not 77"
CHECK_PARTS = "a value token without one part per joined name"
CHECK_TERMS = "terms not 78"
CHECK_NAMES = "term names differ from SEGURA_S7_TERMS.json"
CHECK_PRINTED_ROW = "a term on another printed row than SEGURA_S7_TERMS.json's"
CHECK_PRECISION = "a named row's value outside the TSV's printed precision"
CHECK_FINITE = "a value not finite, or genes not an integer"
CHECK_S6_CAPTION = "not exactly one line containing Table S6"
CHECK_S6_N = "Table S6: distinct genes not 107"
CHECK_READBACK = "the read-back differs from a second parse"
CHECKS = (CHECK_VERSION, CHECK_PAGES, CHECK_TITLE, CHECK_HEADER, CHECK_FOOT, CHECK_TOKEN, CHECK_ORPHAN, CHECK_FOUR,
          CHECK_ROWS, CHECK_PARTS, CHECK_TERMS, CHECK_NAMES, CHECK_PRINTED_ROW, CHECK_PRECISION, CHECK_FINITE,
          CHECK_S6_CAPTION, CHECK_S6_N, CHECK_READBACK)


class PdfRefused(Exception):
    """A refused read; .check is one of CHECKS (no carrier text)."""

    def __init__(self, check: str):
        super().__init__(check)
        self.check = check


class PdfEnvironmentFault(Exception):
    """pdfplumber is not 0.11.10: an environment fault (fix round 3, C (c)) - the stage stops for the operator; it is
    never a final record of the carrier."""


# fix round 3, C (h): pdfplumber.open(pages=...) builds pdfplumber Page objects for the two pages only (1-based numbers
# 38 and 39 = page indexes 37 and 38); pdfminer's PDFPage.create_pages still walks the page tree and builds a PDFPage
# (its dictionary) for every page on the way. No other page's content stream is parsed or interpreted.
PAGES_OPENED = (S6_PAGE + 1, S7_PAGE + 1)
PAGES_RESIDUAL = ("declared residual: pdfplumber.open(pages=[38, 39]) builds Page objects for pages 38 and 39 only; "
                  "pdfminer's page-tree walk builds a PDFPage dictionary for every page; no other page's content "
                  "stream is parsed")


def version_ok() -> bool:
    import pdfplumber
    return getattr(pdfplumber, "__version__", None) == PDFPLUMBER_VERSION


def assert_pdfplumber():
    import pdfplumber
    if getattr(pdfplumber, "__version__", None) != PDFPLUMBER_VERSION:
        raise PdfEnvironmentFault(CHECK_VERSION)
    return pdfplumber


def _open(path):
    pdfplumber = assert_pdfplumber()
    return pdfplumber.open(str(path), pages=list(PAGES_OPENED))


def _two_pages(pdf) -> dict:
    """{page index: Page} of the two pages opened (CHECK_PAGES if the PDF lacks either)."""
    got = {int(pg.page_number) - 1: pg for pg in pdf.pages}
    if set(got) != {S6_PAGE, S7_PAGE}:
        raise PdfRefused(CHECK_PAGES)
    return got


def _words(page) -> list:
    """(x0, top, x1, bottom, text) per word: PyMuPDF's (x0, y0, x1, y1, word) in pdfplumber's coordinates (both put
    the origin at the page's top left)."""
    return [(float(w["x0"]), float(w["top"]), float(w["x1"]), float(w["bottom"]), str(w["text"]))
            for w in page.extract_words()]


# ---- Table S7 (page index 38): the port of s_extract.segura_s7 with the value tokens kept -------------------------
def s7_rows_of_page(page) -> list[dict]:
    text = page.extract_text() or ""
    if S7_TITLE not in text:
        raise PdfRefused(CHECK_TITLE)
    words = _words(page)
    hdr = [w for w in words if w[4] == "#"]
    if len(hdr) != 1:
        raise PdfRefused(CHECK_HEADER)
    x_num, y_hdr = hdr[0][0], hdr[0][1]
    foot = [w for w in words if w[4].startswith("*Only")]
    if len(foot) != 1:
        raise PdfRefused(CHECK_FOOT)
    y_foot = foot[0][1]
    lines: dict[int, list] = {}
    for w in words:
        if y_hdr + 5 < w[1] < y_foot - 1:
            lines.setdefault(round((w[1] + w[3]) / 2), []).append(w)
    rows = []
    for y in sorted(lines):
        ws = sorted(lines[y], key=lambda w: w[0])
        term = [w for w in ws if w[2] < x_num - 2]
        nums = [w[4] for w in ws if w[0] >= x_num - 2]
        if not all(NUM.match(t) for t in nums):
            raise PdfRefused(CHECK_TOKEN)
        rows.append((y, " ".join(w[4] for w in term), nums))
    recs, i = [], 0
    while i < len(rows):
        y, term, nums = rows[i]
        if not term:
            raise PdfRefused(CHECK_ORPHAN)
        if len(nums) < 4 and i + 1 < len(rows) and not rows[i + 1][1]:
            nums = rows[i + 1][2] + nums
            i += 1
        if len(nums) != 4:
            raise PdfRefused(CHECK_FOUR)
        recs.append((term, nums))
        i += 1
    if len(recs) != S7_ROWS:
        raise PdfRefused(CHECK_ROWS)
    out, order = [], 0
    for r, (term, nums) in enumerate(recs, 1):
        parts = [t.strip() for t in term.split(" / ")] if " / " in term else [term]
        split = [tok.split("/") for tok in nums]
        if any(len(s) != len(parts) for s in split):          # C7: every token, not only the first
            raise PdfRefused(CHECK_PARTS)
        for j, p in enumerate(parts):
            order += 1
            out.append(dict(order=order, row=r, term=p, tokens=dict(zip(VALUE_KEYS, [s[j] for s in split]))))
    if order != S7_TERMS:
        raise PdfRefused(CHECK_TERMS)
    return out


def tsv_named_values(tsv_rows: dict, terms: list[dict]) -> dict:
    """{cell id: {genes, expected, fold, fdr} as the TSV prints them} for the 7 named terms (TSV rows 3-9), from each
    row's published_value_and_location; tsv_rows: {cell id: published text}."""
    out = {}
    for t in terms:
        if t["cell_id"] in tsv_rows:
            m = TSV_S7.search(tsv_rows[t["cell_id"]])
            if m is None:
                raise AssertionError("a named row's published values: transcription differs from the TSV form")
            out[t["cell_id"]] = dict(zip(VALUE_KEYS, m.groups()))
    return out


def half_unit(text: str) -> Decimal:
    """Half a unit in the last printed digit of a decimal or scientific text ('9.4e-6' -> 5e-8; '14' -> 0.5)."""
    d = Decimal(text)
    return Decimal(1).scaleb(d.as_tuple().exponent) / 2


def s7_object(rows: list[dict], terms: list[dict], tsv_named: dict) -> dict:
    """R47 (d)'s cross-checks, then the object saved: per cell id its GO id, printed row / order and the four values
    (floats and the printed numeric tokens); no term string."""
    if [r["term"] for r in rows] != [t["term"] for t in terms]:
        raise PdfRefused(CHECK_NAMES)
    if [r["row"] for r in rows] != [int(t["printed_row"]) for t in terms]:
        raise PdfRefused(CHECK_PRINTED_ROW)
    out = {}
    for r, t in zip(rows, terms):
        vals = {}
        for k in VALUE_KEYS:
            tok = r["tokens"][k]
            try:
                x = float(tok)
            except ValueError:
                raise PdfRefused(CHECK_FINITE) from None
            if not math.isfinite(x):
                raise PdfRefused(CHECK_FINITE)
            vals[k] = x
        if not (r["tokens"]["genes"].isdigit() and float(vals["genes"]).is_integer()):
            raise PdfRefused(CHECK_FINITE)
        pub = tsv_named.get(t["cell_id"])
        if pub is not None:
            for k in VALUE_KEYS:
                if abs(Decimal(r["tokens"][k]) - Decimal(pub[k])) > half_unit(pub[k]):
                    raise PdfRefused(CHECK_PRECISION)
        out[t["cell_id"]] = dict(go_id=t["go_id"], printed_row=r["row"], printed_order=r["order"],
                                 genes=int(vals["genes"]), expected=vals["expected"], fold=vals["fold"],
                                 fdr=vals["fdr"], tokens=dict(r["tokens"]))
    if len(tsv_named) and sum(1 for c in tsv_named if c in out) != len(tsv_named):
        raise PdfRefused(CHECK_NAMES)
    return out


# ---- Table S6 (page index 37) ------------------------------------------------------------------------------------
def s6_tokens_of_page(page) -> list[str]:
    text = page.extract_text() or ""
    if sum(1 for ln in text.split("\n") if S6_CAPTION in ln) != 1:
        raise PdfRefused(CHECK_S6_CAPTION)
    words = _words(page)
    lines: dict[int, list] = {}
    for w in words:
        lines.setdefault(round((w[1] + w[3]) / 2), []).append(w)
    cap = [y for y in lines if S6_CAPTION in " ".join(w[4] for w in sorted(lines[y], key=lambda w: w[0]))]
    if len(cap) != 1:
        raise PdfRefused(CHECK_S6_CAPTION)
    bottom = max(w[3] for w in lines[cap[0]])
    toks = []
    for w in sorted(words, key=lambda w: (round((w[1] + w[3]) / 2), w[0])):
        if w[1] > bottom:
            for piece in re.split(r"[,;]", w[4]):
                tok = piece.strip().rstrip(FOOTNOTE_MARKS).strip()
                if tok:
                    toks.append(tok)
    return toks


def s6_object(tokens: list[str], s4_raw: set, hg) -> dict:
    """R47 (f): the distinct genes (tokens equal to a Table S4 raw symbol), exactly 107; saved as an HGNC-mapped member
    set (the S-build's HGNC rule), drops and non-gene tokens counted."""
    genes = sorted({t for t in tokens if t in s4_raw})
    if len(genes) != S6_N:
        raise PdfRefused(CHECK_S6_N)
    mapped, how = hg.map_columns(genes)
    members = sorted({m for m in mapped if m})
    return dict(n_tokens=len(tokens), n_non_gene_tokens=sum(1 for t in tokens if t not in s4_raw), n_genes=len(genes),
                members_hgnc=members, n_hgnc=len(members), n_drops=sum(1 for m in mapped if not m),
                hgnc_mapping=how, rule="RUN_PLAN_amend_3 R47 (f)")


# ---- the reader (fetch_extract FE16) and the read-back -------------------------------------------------------------
def parse(path, terms: list[dict], tsv_named: dict, s4_raw: set, hg) -> dict:
    """Both pages: {"s7": {"status": "transcribed", "rows": {...}} | {"status": "not transcribed", "check": label},
    "s6": {...}}. A failure of one table never stops the other."""
    out = {}
    with _open(path) as pdf:
        pages = _two_pages(pdf)
        try:
            rows = s7_rows_of_page(pages[S7_PAGE])
            out["s7"] = {"status": "transcribed", "rows": s7_object(rows, terms, tsv_named)}
        except PdfRefused as e:
            out["s7"] = {"status": "not transcribed", "check": e.check}
        try:
            out["s6"] = dict(status="transcribed", **s6_object(s6_tokens_of_page(pages[S6_PAGE]), s4_raw, hg))
        except PdfRefused as e:
            out["s6"] = {"status": "not transcribed", "check": e.check}
    out["pages_opened"] = {"page_numbers": list(PAGES_OPENED), "residual": PAGES_RESIDUAL}
    return out


def readback(path, stored: dict, terms: list[dict], tsv_named: dict, s4_raw: set, hg) -> bool:
    """R47 (g): a second parse (a fresh pdfplumber.open of the file, the same rule on the same pages) equals the stored
    object read back from disk (a planted one-digit change in the stored object fails it)."""
    import json
    again = parse(path, terms, tsv_named, s4_raw, hg)
    return json.loads(json.dumps(again, sort_keys=True)) == json.loads(json.dumps(stored, sort_keys=True))


def jaccard(a: set, b: set) -> dict:
    """R47 (h): |A|, |B|, |A n B|, |A u B| and J = |A n B| / |A u B| (None when both are empty)."""
    a, b = set(a), set(b)
    inter, union = len(a & b), len(a | b)
    return dict(n_A=len(a), n_B=len(b), n_intersection=inter, n_union=union, J=(inter / union) if union else None,
                paper_B="107 (TSV row 1)")
