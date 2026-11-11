"""A1 claims register DRAFT v6.8 / v6.9 -- the privacy guard every register builder applies to every workbook sheet it reads (B S2
of the v6.7 final re-check: the v6.7 guard detected identifier WORDING only, not identifier-VALUED headers; decided by the
orchestrator under the operator's standing delegation, 2026-09-29).

The rule (register 1.6, "Individual-level data in supplements", as tightened by v6.8). A sheet is IDENTIFIER-BEARING if
  (W) it is wider than WIDE_COLS = 50 columns (sample IDs can be the column headers), or
  (N) a cell of its header zone (its first GUARD_ROWS rows: 6 in v6.8, 20 since v6.9) carries identifier WORDING (ID_WORDING: sample / individual /
      subject / proband / family / donor / patient / participant / person / brain + id / ids / identifier / code / no /
      number; IID, FID, sampleid ...; = v6.7's ID_HEADER), or
  (V) a cell of its header zone holds an identifier-VALUED token (ID_VALUE, the documented set below).
For an identifier-bearing sheet a builder (1) prints nothing of it but its name and dimensions -- a refusal names the sheet
and the rule letter, never a cell -- and (2) reads from it only the columns it DECLARES by exact header text in a stated
header row, each found exactly once; every other cell reads as None (positions kept, so a builder's indexing is unchanged).
The guard itself returns booleans, counts and pattern names only, never a cell of the header zone.

ID_VALUE -- a string cell is split into tokens on white space and , ; | / ( ) [ ] { } and quotes; a token wholly matching an
EXEMPT pattern is skipped; the patterns below are searched in the rest, a match bounded by non-alphanumerics ('_', '-', '.'
count as boundaries, so 'HSB999_QX' and 'AN99999_qx9_99' are caught):
  HSB       HSB<digits>                          BrainSpan / Kang 2011 donor codes (case-insensitive)
  UMB       UMB<digits>                          NIH NeuroBioBank (University of Maryland) brain codes (case-insensitive)
  AN        AN<3+ digits>                        Autism Tissue Program / Harvard Brain Tissue Resource Center codes
  NUM_CODE  <digits>_<letter>...                 a brain / sample number joined to a region or batch code ('9999_QX9'); not
                                                 after '.', '_' or '-' (the HGNC clone-name aliases 'hRPC.1050_D_4',
                                                 'hRPK-465_F_21'; Brodmann-pair headers such as 'ASD_BA41_42_FDR')
  NDAR      NDAR<8 alphanumerics>                NIMH Data Archive GUIDs
  SSC       <5 digits>.<p1|p2|s1|s2|mo|fa>        Simons Simplex Collection individuals
  SPARK     SP<7 digits>                         SPARK participants
  GTEX      GTEX-<4-6 alphanumerics>             GTEx donors
  TCGA      TCGA-<2>-<4>                          TCGA participants
  BIDS      sub-<alphanumerics with a digit>     BIDS subject labels (not a word such as 'sub-cellular')
  GEO_SAMPLE  GSM / SRR / SRS / SRX / ERR / ERS / DRR<digits>   public sample / run accessions (per-sample columns)
  CODE      <1-5 capitals>[-_]?<3-6 digits>[<capital>]  a generic letters+digits code (Q9999, QZB-9999, QZ0000; a longer digit
            run -- e.g. a letter + 8 digits -- is read as a database accession, declared); a match that
            is an HGNC approved, previous or alias symbol (the pinned HGNC table, loaded only when a CODE-shaped token occurs)
            is exempt, and so is one shaped as a UniProt accession ([OPQ]<digit><3 alphanumerics><digit>) or a CCDS id
  EXEMPT (whole token): Ensembl ids (ENS[A-Z]*<11 digits>[.v]), RefSeq (NM_ NR_ XM_ XR_ NP_ XP_), Illumina (ILMN_<digits>),
            Affymetrix probe sets (<digits>[_<x>]_at, AFFX-...), KEGG (hsa<5 digits>), Reactome (R-HSA-<digits>), MeSH
            (MESH:D<digits>, D<6 digits>), GO / DOID / HP / MONDO ids, dbSNP (rs<digits>), LOC / FLJ / KIAA / LINC / MIR /
            SNORD<digits>, GEO series / platforms (GSE / GPL<digits>), years 19xx / 20xx.
Not detected (declared): purely numeric identifiers (e.g. ABIDE's five-digit subject numbers) -- a number cannot be told from a
value; such a sheet is caught only by (W) or (N) (v6.9: also by a bare subject word heading its column).

Register DRAFT v6.9 (C1 of the v6.8 re-check; the orchestrator under the operator's standing delegation, 2026-09-30):
  - the header zone is the first GUARD_ROWS = 20 rows (v6.8: 6);
  - the width is the POPULATED width (one past the last non-empty cell of any row), not the file's dimension tag, which may
    claim empty columns (Parikshak 2016 Supplementary Table 4's TableS4a: tag 53, populated 8); n_rows is the populated height;
  - HSB / UMB / AN / BTB codes may carry a '.', '-' or '_' separator, or a space (searched in the whole cell: SPACED); a number
    of 4+ digits joined to a region code by '.', '-' or a space (e.g. '9999-QX9');
  - NDA GUIDs also in the NDAR_INV<8> / NDARINV<8> forms;
  - identifier wording also 'brain bank' / 'biobank' / 'tissue bank' / 'specimen' + id / code / number ('Brain bank ID');
  - (N) also a BARE subject word (Individual / Donor / Subject / Patient / Sample / Proband / Participant, plural allowed) as a
    cell whose column below holds a number or a short code (1-16 letters / digits / . _ - with a digit).
  Every example in this module and its self-test is SYNTHETIC (all-9 / all-0 digit runs, invented letter parts such as 'QX',
  'QZB'); v6.8's examples used real-format codes and were replaced (v6.9, B NEW-PII).

Register DRAFT v6.10 (C1-width / C1-coverage of the v6.9 re-check; the orchestrator under the operator's standing delegation,
2026-09-30):
  - a read-only openpyxl sheet is read by its CELLS, not by the dimension tag in its XML: classify_openpyxl and read_openpyxl
    call ws.reset_dimensions() first (_by_cells), so an UNDERSTATED tag (e.g. 'A1:C2' over 60 populated columns) no longer
    truncates rows and columns, and an overstated one no longer pads the width; read_openpyxl still pads every row to the
    wider of the tag and the cells, so a builder's indexing is unchanged where the tag was right or overstated;
  - numbered-subject wording: sample / patient / subject / individual / donor / case + a number ('Patient 1', 'Subject_1',
    'Case 9'), and 'Ind' + a number ('Ind1'; case-sensitive -- 'IND1' is an HGNC alias);
  - bare 'ID' and 'Case' headers join the bare subject words; a number below a bare header always counts, and so does a short
    code.
Register DRAFT v6.11 (C1-regression of the v6.10 re-check): v6.10 exempted HGNC symbols and EXEMPT ids under EVERY bare
subject word, which hid subject columns v6.9 caught ('Sample' over S1 ... S19, 'Donor' over B-codes, 'Individual' over H-codes
-- all HGNC symbols or aliases). The exemption now applies ONLY under a bare 'ID' header, and there only when EVERY short code
below it is an HGNC approved / previous / alias symbol or an EXEMPT database id -- a year (19xx / 20xx) does not count as
exempt there (a bare 'ID' over text years is a subject column). Under every other bare subject word no code is exempt (v6.9).

Self-test: python -X utf8 privacy_guard.py selftest [--record <json>] -- planted sheets the guard must catch (identifier-valued
headers of each family, a 51-column sheet, identifier wording, a masked read that must hide undeclared columns, reads that must
be refused) and clean gene sheets it must pass (a 50-column sheet, gene symbols shaped like codes, database ids); plus the check
that no HGNC approved / previous / alias symbol is flagged by the specific patterns. Prints case names and caught / passed only.
Works under the programme venv and the system Python (openpyxl; xlrd optional).
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

GUARD_ROWS = 20  # v6.9 (C1): the header zone is the first 20 rows (v6.8: 6)
WIDE_COLS = 50
ID_WORDING = re.compile(r"(?i)(?<![a-z])(sample|individual|subject|proband|family|donor|patient|participant|person|"
                        r"brain[\s_.-]*bank|bio[\s_.-]*bank|tissue[\s_.-]*bank|brain|specimen)"  # v6.9: + '... bank', specimen
                        r"[\s_.-]*(id|ids|identifier|code|no|number)(?![a-z])|(?<![a-z])(iid|fid|sampleid|subjectid|individualid|"
                        r"brainid|donorid|patientid)(?![a-z])|(?<![a-z])(sample|patient|subject|individual|donor|case)[\s_.-]?\d+"
                        r"(?![a-z0-9])|(?<![A-Za-z])(?-i:Ind)[\s_.-]?\d+(?![A-Za-z0-9])")  # v6.7 ID_HEADER, extended (v6.10: numbered subjects)
# v6.9 (C1): a bare subject word heading a column of numbers or short codes
BARE_SUBJECT = re.compile(r"(?i)^(individual|donor|subject|patient|sample|proband|participant|case|id)s?$")  # v6.10: + case, id
SHORT_CODE = re.compile(r"^(?=.*\d)[A-Za-z0-9._\-]{1,16}$")
_B, _E = r"(?<![A-Za-z0-9])", r"(?![A-Za-z0-9])"
_SEP = r"[._-]?"  # v6.9 (C1): a brain-bank / sample code may carry a '.', '-' or '_' separator inside a token
ID_VALUE = [  # (name, compiled pattern) -- searched in each non-exempt token
    ("HSB", re.compile(_B + r"HSB" + _SEP + r"\d+" + _E, re.I)),
    ("UMB", re.compile(_B + r"UMB" + _SEP + r"\d+" + _E, re.I)),
    ("AN", re.compile(_B + r"(?:(?i:AN)\d{3,}|AN[._-]\d{3,})" + _E)),
    ("BTB", re.compile(_B + r"BTB" + _SEP + r"\d{3,}" + _E, re.I)),
    ("NUM_CODE", re.compile(r"(?<![A-Za-z0-9._\-])\d+_[A-Za-z][A-Za-z0-9]*")),  # not after '.', '_' or '-'
    ("NUM_CODE", re.compile(r"(?<![A-Za-z0-9._\-])\d{4,}[.-][A-Z]{1,3}\d{1,3}" + _E)),  # v6.9: '.' / '-' separated
    ("NDAR", re.compile(_B + r"NDAR(?:_?INV)?[A-Z0-9]{8}" + _E, re.I)),  # v6.9: + NDAR_INV... / NDARINV...
    ("SSC", re.compile(_B + r"\d{5}\.(p1|p2|s1|s2|mo|fa)" + _E, re.I)),
    ("SPARK", re.compile(_B + r"SP\d{7}" + _E)),
    ("GTEX", re.compile(_B + r"GTEX-[A-Z0-9]{4,6}" + _E, re.I)),
    ("TCGA", re.compile(_B + r"TCGA-[A-Z0-9]{2}-[A-Z0-9]{4}", re.I)),
    ("BIDS", re.compile(_B + r"sub-[A-Za-z]*\d[A-Za-z0-9]*" + _E)),  # a label with a digit (not "sub-cellular")
    ("GEO_SAMPLE", re.compile(_B + r"(GSM|SRR|SRS|SRX|ERR|ERS|DRR)\d{3,}" + _E)),
]
CODE = re.compile(_B + r"[A-Z]{1,5}[-_.]?\d{3,6}[A-Z]?" + _E)  # 3-6 digits: a longer run is a database accession
# v6.9 (C1): codes whose separator is a SPACE span two tokens -- searched in the whole cell text
SPACED = [
    ("HSB", re.compile(_B + r"HSB \d+" + _E, re.I)),
    ("UMB", re.compile(_B + r"UMB \d+" + _E, re.I)),
    ("AN", re.compile(_B + r"AN \d{3,}" + _E)),
    ("BTB", re.compile(_B + r"BTB \d{3,}" + _E, re.I)),
    ("NUM_CODE", re.compile(r"(?<![A-Za-z0-9._\-])\d{4,} [A-Z]{1,3}\d{1,3}" + _E)),
]
EXEMPT = re.compile(r"(?i)^(ENS[A-Z]*\d{11}(\.\d+)?|[NX][MRP]_\d+(\.\d+)?|ILMN_\d+|\d+(_[a-z]+)*_at|AFFX-.*|hsa\d{5}|R-HSA-\d+|"
                    r"MESH:D\d+|D\d{6}|GO:\d+|DOID:\d+|HP:\d+|MONDO:\d+|rs\d+|LOC\d+|FLJ\d+|KIAA\d+|LINC\d+|MIR\d+[A-Z]*|"
                    r"SNORD\d+[A-Z]*|GSE\d+|GPL\d+|(19|20)\d\d)$")
CODE_EXEMPT = re.compile(r"^([OPQ]\d[A-Z0-9]{3}\d|CCDS\d+)$")  # UniProt accessions (O / P / Q form), CCDS ids
TOKEN_SPLIT = re.compile(r"[\s,;|/()\[\]{}\"']+")
HGNC_FILE = Path(r"E:\data\asdg\explore_public\hgnc_complete_set\hgnc_complete_set_2026-09-04.txt")
HGNC_SHA = "6f43d6ff43aa9fdfa5fb2f20a20a7cace66e6e02e2a0dcf19d9b726e2e248d20"
_HGNC: set | None = None


class Refused(SystemExit):
    """a builder's read the guard refuses; its text names the workbook, the sheet and the rule, never a cell."""


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def hgnc_symbols() -> set:
    """every HGNC approved, previous and alias symbol of the pinned table (sha256 asserted); loaded once."""
    global _HGNC
    if _HGNC is None:
        assert _sha256(HGNC_FILE) == HGNC_SHA, "HGNC table differs from its pin"
        out = set()
        with open(HGNC_FILE, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f, delimiter="\t"):
                out.add(r["symbol"].strip())
                for col in ("prev_symbol", "alias_symbol"):
                    out.update(t.strip() for t in (r.get(col) or "").split("|") if t.strip())
        _HGNC = out
    return _HGNC


def _cell_text(v) -> str | None:
    """a header-zone cell as text for the tests; numbers, booleans, dates and empty cells are not tested (declared)."""
    if isinstance(v, str):
        return " ".join(v.split()) or None
    return None


def id_value_hits(text: str) -> list[str]:
    """the ID_VALUE pattern names a string cell matches (one name per hit)."""
    hits = [name for name, pat in SPACED if pat.search(text)]
    for tok in TOKEN_SPLIT.split(text):
        if not tok or EXEMPT.match(tok):
            continue
        for name, pat in ID_VALUE:
            if pat.search(tok):
                if name == "NUM_CODE" and re.fullmatch(r"\d+(_[a-z]+)*_at", tok):
                    continue
                hits.append(name)
        for m in CODE.finditer(tok):
            if not (EXEMPT.match(m.group(0)) or CODE_EXEMPT.match(m.group(0)) or m.group(0) in hgnc_symbols()):
                hits.append("CODE")
    return hits


YEAR = re.compile(r"(19|20)\d\d")


def _gene_or_db_id(s: str) -> bool:
    """v6.11: an HGNC approved / previous / alias symbol, or an EXEMPT database id other than a year."""
    return s in hgnc_symbols() or bool(EXEMPT.match(s) and not YEAR.fullmatch(s))


def _bare_subject_hit(word: str, below: list) -> bool:
    """v6.9 / v6.11: a bare subject word over a column holding a number or a short code (1-16 letters / digits / . _ - with a
    digit). Under a bare 'ID' only (v6.11), a column whose short codes are ALL gene symbols or database ids (no year) is a
    gene column, not a subject column; under every other bare word no code is exempt."""
    if any(isinstance(x, (int, float)) and not isinstance(x, bool) for x in below):
        return True
    codes = [x.strip() for x in below if isinstance(x, str) and SHORT_CODE.match(x.strip())]
    if not codes:
        return False
    if word.lower().rstrip("s") == "id":
        return not all(_gene_or_db_id(c) for c in codes)
    return True


def classify(zone_rows, n_cols: int) -> dict:
    """zone_rows: the values of the sheet's first GUARD_ROWS rows; n_cols: its width. Returns booleans and counts only."""
    wording, bare, value = 0, 0, {}
    zone = [list(r) for r in list(zone_rows)[:GUARD_ROWS]]
    for i, r in enumerate(zone):
        for j, v in enumerate(r):
            t = _cell_text(v)
            if t is None:
                continue
            if ID_WORDING.search(t):
                wording += 1
            if BARE_SUBJECT.match(t):  # v6.9 (C1): a bare subject word over numbers / short codes in its column
                below = [zone[k][j] for k in range(i + 1, len(zone)) if j < len(zone[k]) and zone[k][j] not in (None, "")]
                if _bare_subject_hit(t, below):  # v6.11: the gene-symbol exemption under a bare 'ID' only
                    bare += 1
            for h in id_value_hits(t):
                value[h] = value.get(h, 0) + 1
    wide = n_cols > WIDE_COLS
    rules = "".join(x for x, on in (("W", wide), ("N", wording + bare > 0), ("V", bool(value))) if on)
    return {"identifier_bearing": bool(rules), "rules": rules, "n_cols": n_cols, "wide": wide,
            "id_wording_cells": wording, "bare_subject_headers": bare, "id_value_hits": dict(sorted(value.items()))}


# ------------------------------------------------------------------------------------------------ openpyxl adapter
def _content_width(rows) -> int:
    """v6.9 (C1): the populated width -- one past the last non-empty cell of any row (not the file's dimension tag)."""
    n = 0
    for r in rows:
        last = max((j for j, v in enumerate(r) if v is not None and v != ""), default=-1)
        n = max(n, last + 1)
    return n


def _ws_width(ws) -> int:
    return _content_width(ws.iter_rows(values_only=True))


def _ws_rows(ws) -> int:
    """the populated height (one past the last row holding a non-empty cell)."""
    n = 0
    for i, r in enumerate(ws.iter_rows(values_only=True), 1):
        if any(v is not None and v != "" for v in r):
            n = i
    return n


def _by_cells(ws) -> tuple:
    """v6.10 (C1-width): read a sheet by its cells, not by its dimension tag -- ws.reset_dimensions() on a read-only sheet (an
    understated tag truncates rows and columns, an overstated one pads them). Returns the tag (max_row, max_column) as the
    file states it, read once before the reset and kept on the sheet object for later calls."""
    tag = getattr(ws, "_guard_dimension_tag", None)
    if tag is None:
        tag = (getattr(ws, "max_row", None), getattr(ws, "max_column", None))
        if hasattr(ws, "reset_dimensions"):
            ws.reset_dimensions()
        try:
            ws._guard_dimension_tag = tag
        except AttributeError:
            pass
    return tag


def classify_openpyxl(ws) -> dict:
    tag = _by_cells(ws)  # v6.10
    zone = [list(r) for r in ws.iter_rows(min_row=1, max_row=GUARD_ROWS, values_only=True)]
    width, height = 0, 0
    for i, r in enumerate(ws.iter_rows(values_only=True), 1):  # one pass: populated width and height
        last = max((j for j, v in enumerate(r) if v is not None and v != ""), default=-1)
        if last >= 0:
            width, height = max(width, last + 1), i
    out = classify(zone, width)
    out["n_rows"] = height
    out["n_cols_dimension_tag"] = tag[1]
    return out


def guard_workbook_openpyxl(wb) -> dict:
    """{sheet name: verdict} for every sheet of an open openpyxl workbook (names and verdicts only)."""
    return {ws.title: classify_openpyxl(ws) for ws in wb.worksheets}


def _declared_positions(header: list, declared, label: str, sheet: str) -> list[int]:
    """declared: exact header texts (each must occur exactly once in the header row) or a column rule -- a function of the
    header row returning column positions (the builder's own programmatic rule; nothing is printed)."""
    if callable(declared):
        pos = list(declared(list(header)))
        if not pos or len(set(pos)) != len(pos) or not all(isinstance(j, int) and 0 <= j < len(header) for j in pos):
            raise Refused("REFUSED: %s sheet '%s': the declared column rule returned invalid positions; no row is read or "
                          "printed" % (label, sheet))
        return pos
    pos = []
    for d in declared:
        idx = [j for j, v in enumerate(header) if isinstance(v, str) and v == d]
        if len(idx) != 1:
            raise Refused("REFUSED: %s sheet '%s': a declared column is found %d times in the declared header row (it must be "
                          "exactly once); no row is read or printed" % (label, sheet, len(idx)))
        pos.append(idx[0])
    return pos


def read_openpyxl(ws, declared=None, header_row: int | None = None, label: str = "", verdict: dict | None = None) -> list[tuple]:
    """every row of one sheet (values_only). An identifier-bearing sheet needs `declared` (exact header texts, or a column rule
    on the header row) and `header_row` (0-based, inside the guard's header zone): only those columns are kept -- the mask is
    applied row by row as the sheet is read, every other cell reads as None; otherwise the read is refused. Declared columns
    are checked on a clean sheet too (its rows are returned whole)."""
    tag = _by_cells(ws)  # v6.10: every row, by the cells
    v = verdict or classify_openpyxl(ws)
    if v["identifier_bearing"] and (declared is None or header_row is None or header_row >= GUARD_ROWS):
        raise Refused("REFUSED: %s sheet '%s' is identifier-bearing (rule %s) and the builder declared no columns in its header "
                      "zone; no row is read or printed" % (label, ws.title, v["rules"]))
    rows = [list(r) for r in ws.iter_rows(values_only=True)]
    width = max([tag[1] or 0] + [len(r) for r in rows])  # the wider of the tag and the cells: indexing as before the reset
    rows = [r + [None] * (width - len(r)) for r in rows]
    keep = None
    if declared is not None:
        keep = set(_declared_positions(rows[header_row] if header_row < len(rows) else [], declared, label, ws.title))
    if not v["identifier_bearing"]:
        return [tuple(r) for r in rows]
    return [tuple(x if j in keep else None for j, x in enumerate(r)) for r in rows]


# ------------------------------------------------------------------------------------------------ xlrd adapter
def classify_xlrd(sh) -> dict:
    zone = [sh.row_values(r) for r in range(min(GUARD_ROWS, sh.nrows))]
    width, height = 0, 0  # v6.9 (C1): the populated width / height, from the cells
    for r in range(sh.nrows):
        vals = sh.row_values(r)
        last = max((j for j, v in enumerate(vals) if v is not None and v != ""), default=-1)
        if last >= 0:
            width, height = max(width, last + 1), r + 1
    out = classify(zone, width)
    out["n_rows"] = height
    out["n_cols_dimension_tag"] = sh.ncols
    return out


def xlrd_cell_reader(sh, declared=None, header_row: int | None = None, label: str = "", verdict: dict | None = None):
    """a cell_value(r, c) function over one xlrd sheet that honours the guard: an identifier-bearing sheet needs declared
    columns (exact header texts in header_row) and every other cell reads as '' (xlrd's empty cell); else the read is
    refused."""
    v = verdict or classify_xlrd(sh)
    if v["identifier_bearing"] and (declared is None or header_row is None or header_row >= GUARD_ROWS):
        raise Refused("REFUSED: %s sheet '%s' is identifier-bearing (rule %s) and the builder declared no columns in its header "
                      "zone; no row is read or printed" % (label, sh.name, v["rules"]))
    keep = None
    if declared is not None:
        keep = set(_declared_positions(sh.row_values(header_row), declared, label, sh.name))
    if v["identifier_bearing"]:
        return lambda r, c: sh.cell_value(r, c) if c in keep else ""
    return sh.cell_value


# ------------------------------------------------------------------------------------------------ the self-test
def _selftest(record: Path | None) -> int:
    import tempfile
    import openpyxl

    def wb_with(rows, title="Sheet1"):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = title
        for r in rows:
            ws.append(list(r))
        return wb

    def verdict_of(rows):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "t.xlsx"
            wb_with(rows).save(p)
            wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
            v = classify_openpyxl(wb.worksheets[0])
            wb.close()
        return v

    data = [["ZNF804A", 0.51, 0.012, "M12"], ["LINC00473", -0.3, 0.04, "M16"], ["KIAA0100", 0.2, 0.2, "M2"],
            ["SLC6A4", 1.1, 0.001, "M3"]]
    cases = []  # (name, rows, expect identifier-bearing, expected rule letters)
    cases.append(("planted: identifier-valued header, BrainSpan donor codes joined to a region", [["Gene", "HSB999_QX", "HSB999_QX"]]
                  + [[d[0], 1.0, 2.0] for d in data], True, "V"))
    cases.append(("planted: identifier-valued header, brain-bank codes (UMB / AN, lower-case region suffix)",
                  [["gene_symbol", "UMB9999_QX9", "AN99999_qx9_99"]] + [[d[0], 1.0, 2.0] for d in data], True, "V"))
    cases.append(("planted: identifier-valued header, sample number + region code", [["Gene", "9999_QX9", "9999_QX99"]]
                  + [[d[0], 1.0, 2.0] for d in data], True, "V"))
    cases.append(("planted: identifier-valued header, generic letters+digits codes", [["Gene", "Q9999", "QZB-9999", "QZ0000"]]
                  + [[d[0], 1.0, 2.0, 3.0] for d in data], True, "V"))
    cases.append(("planted: identifier-valued header, lower-case donor codes", [["gene", "hsb999", "hsb999"]]
                  + [[d[0], 1.0, 2.0] for d in data], True, "V"))
    cases.append(("planted: identifier values in the first data rows (NDA GUIDs, SSC, SPARK), neutral header",
                  [["subjectkey", "x", "y"], ["NDARQQ999999", 1, 2], ["99999.p1", 1, 2], ["SP9999999", 1, 2]], True, "V"))
    cases.append(("planted: per-sample GEO accessions as headers", [["ID_REF", "GSM999999", "GSM000000"], ["ILMN_1234567", 1.0, 2.0]],
                  True, "V"))
    cases.append(("planted: GTEx / TCGA / BIDS labels as headers", [["gene", "GTEX-99999", "TCGA-QQ-9999", "sub-9999999"]], True, "V"))
    cases.append(("planted: a 51-column sheet with neutral headers", [["c%d" % k for k in range(51)], list(range(51))], True, "W"))
    cases.append(("planted: identifier wording in the header", [["Sample ID", "Gene", "log2FC"], ["x", "SLC6A4", 0.1]], True, "N"))
    cases.append(("planted: identifier wording in a title row above the header", [["Brain code by region"], ["Gene", "log2FC"]]
                  + [[d[0], d[1]] for d in data], True, "N"))
    cases.append(("clean: a gene-level sheet (symbols shaped like codes: ZNF804A, LINC00473, KIAA0100)",
                  [["Table S1. Genes"], ["Gene", "log2FC", "FDR", "Module"]] + data, False, ""))
    cases.append(("clean: database ids (Ensembl, Affymetrix, Illumina, RefSeq, Reactome, MeSH, KEGG, GEO series, dbSNP)",
                  [["Data from GSE28521 (2011)", "", ""], ["ensembl", "probe", "other"], ["ENSG00000123456", "1552256_a_at", "R-HSA-112315"],
                   ["ENSG00000123457.5", "ILMN_1234567", "MESH:D012559"], ["ENSG00000123458", "1007_s_at", "hsa04010"],
                   ["ENSG00000123459", "NM_001234", "rs123456"], ["sub-cellular fraction", "P01234567", "Mdev13"],
                   ["P12345", "CCDS12345", "ASD_BA41_42_FDR"]], False, ""))
    cases.append(("clean: a 50-column sheet (the edge)", [["c%d" % k for k in range(50)], list(range(50))], False, ""))
    # v6.9 (C1) plants -- synthetic codes only (all-9 / all-0 digit runs; invented letter parts)
    cases.append(("planted v6.9: brain-bank codes with '.', '-' separators", [["Gene", "UMB-9999", "HSB.999", "AN.99999"]]
                  + [[d[0], 1.0, 2.0, 3.0] for d in data], True, "V"))
    cases.append(("planted v6.9: brain-bank codes with a space separator", [["Gene", "UMB 9999", "HSB 999", "AN 99999"]]
                  + [[d[0], 1.0, 2.0, 3.0] for d in data], True, "V"))
    cases.append(("planted v6.9: sample number + region code with '-' / space", [["Gene", "9999-QX9", "0000 QX99"]]
                  + [[d[0], 1.0, 2.0] for d in data], True, "V"))
    cases.append(("planted v6.9: NDA GUIDs in the NDAR_INV / NDARINV forms", [["id", "x"], ["NDAR_INVQQ999999", 1], ["NDARINVQQ000000", 2]],
                  True, "V"))
    cases.append(("planted v6.9: identifier wording 'Brain bank ID'", [["Brain bank ID", "Gene"], ["x", "SLC6A4"]], True, "N"))
    cases.append(("planted v6.9: a bare subject word over a numeric column", [["Donor", "Gene", "log2FC"], [9999, "SLC6A4", 0.1],
                                                                             [99999, "ZNF804A", 0.2]], True, "N"))
    cases.append(("planted v6.9: a bare subject word over short codes", [["Individual", "Gene"], ["QQ99", "SLC6A4"], ["QQ00", "ZNF804A"]],
                  True, "N"))
    cases.append(("planted v6.9: identifier wording below row 6 (header zone of 20 rows)", [["Table S9. Samples"]] + [[None]] * 10
                  + [["Sample ID", "Gene"], ["x", "SLC6A4"]], True, "N"))
    cases.append(("clean v6.9: subject words that are not bare (a 'Sample size' column, 'subject to' text)",
                  [["Gene", "Sample size", "Note"], ["SLC6A4", 9999, "subject to change"], ["ZNF804A", 99, "none"]], False, ""))
    # v6.10 (C1-coverage) plants -- synthetic only
    cases.append(("planted v6.10: numbered-subject headers ('Patient 9', 'Subject_9')", [["Gene", "Patient 9", "Subject_9"]]
                  + [[d[0], 1.0, 2.0] for d in data], True, "N"))
    cases.append(("planted v6.10: numbered-subject headers ('Ind9', 'Donor 99', 'Case 9')", [["Gene", "Ind9", "Donor 99", "Case 9"]]
                  + [[d[0], 1.0, 2.0, 3.0] for d in data], True, "N"))
    cases.append(("planted v6.10: a bare 'ID' header over a numeric column", [["ID", "Gene", "log2FC"], [9999, "SLC6A4", 0.1],
                                                                             [99999, "ZNF804A", 0.2]], True, "N"))
    cases.append(("planted v6.10: a bare 'Case' header over short codes", [["Case", "Gene"], ["QQ99", "SLC6A4"], ["QQ00", "ZNF804A"]],
                  True, "N"))
    # v6.11 (C1-regression) plants -- synthetic; the codes collide with HGNC symbols / aliases on purpose
    cases.append(("planted v6.11: 'Sample' over S1 ... S19 (HGNC symbols / aliases)", [["Sample", "Gene", "log2FC"]]
                  + [["S%d" % k, "SLC6A4", 0.1] for k in range(1, 20)], True, "N"))
    cases.append(("planted v6.11: 'Donor' over HGNC-colliding B-codes", [["Donor", "Gene"], ["B9", "SLC6A4"], ["B99", "ZNF804A"]],
                  True, "N"))
    cases.append(("planted v6.11: 'Individual' over an HGNC-colliding H-code", [["Individual", "Gene"], ["H9", "SLC6A4"]], True, "N"))
    cases.append(("planted v6.11: a bare 'ID' over text years", [["ID", "Gene"], ["1999", "SLC6A4"], ["2000", "ZNF804A"]], True, "N"))
    cases.append(("clean v6.10: a bare 'ID' header over gene symbols and Ensembl ids (not a subject column)",
                  [["ID", "Symbol", "log2FC"], ["ENSG00000123456", "ZNF804A", 0.1], ["ENSG00000123457", "SLC6A4", 0.2]]
                  + [[None, "KIAA0100", 0.3]], False, ""))
    results = []
    for name, rows, want, letters in cases:
        v = verdict_of(rows)
        ok = v["identifier_bearing"] == want and (not want or letters in v["rules"])
        results.append({"case": name, "expect": "identifier-bearing (%s)" % letters if want else "clean",
                        "got_rules": v["rules"] or "clean", "ok": ok})
    # v6.9 (C1): the width comes from the cells, not the file's dimension tag -- a 3-column sheet whose tag claims 60 columns
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "dim.xlsx"
        wb = wb_with([["Gene", "log2FC", "FDR"]] + [[d[0], d[1], d[2]] for d in data])
        wb.active.cell(row=1, column=60)  # an empty cell: the saved dimension tag spans 60 columns
        wb.save(p)
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
        v = classify_openpyxl(wb.worksheets[0])
        tag = v["n_cols_dimension_tag"]  # v6.10: the tag as the file states it, kept before the reset
        wb.close()
    ok = (tag or 0) > WIDE_COLS and v["n_cols"] == 3 and not v["identifier_bearing"]
    results.append({"case": "clean v6.9: a 3-column sheet whose dimension tag claims more than 50 columns (width from the cells)",
                    "expect": "clean", "got_rules": (v["rules"] or "clean") if ok else "tag %s / width %s" % (tag, v["n_cols"]),
                    "ok": ok})
    # v6.10 (C1-width): an UNDERSTATED tag -- 60 populated columns under a tag 'A1:C2' -- must still be W, and a read must
    # return all 60 columns and every row (the XML's dimension element rewritten after the save)
    import zipfile
    with tempfile.TemporaryDirectory() as td:
        p0, p1 = Path(td) / "u0.xlsx", Path(td) / "u1.xlsx"
        wb_with([["c%d" % k for k in range(60)]] + [list(range(60)) for _ in range(4)]).save(p0)
        with zipfile.ZipFile(p0) as zi, zipfile.ZipFile(p1, "w", zipfile.ZIP_DEFLATED) as zo:
            for it in zi.infolist():
                b = zi.read(it.filename)
                if it.filename == "xl/worksheets/sheet1.xml":
                    b = re.sub(rb'<dimension ref="[^"]*"', b'<dimension ref="A1:C2"', b, count=1)
                zo.writestr(it, b)
        wb = openpyxl.load_workbook(p1, read_only=True, data_only=True)
        ws = wb.worksheets[0]
        v = classify_openpyxl(ws)
        rows = read_openpyxl(ws, declared=lambda h: [0], header_row=0, label="plant")
        wb.close()
    ok = (v["n_cols_dimension_tag"] == 3 and v["n_cols"] == 60 and "W" in v["rules"] and len(rows) == 5
          and all(len(r) == 60 for r in rows) and rows[4][0] == 0)
    results.append({"case": "planted v6.10: an understated dimension tag (A1:C2 over 60 populated columns) -> W, read whole",
                    "expect": "identifier-bearing (W)", "got_rules": (v["rules"] or "clean") if ok else "tag %s / width %s / rows %d"
                    % (v["n_cols_dimension_tag"], v["n_cols"], len(rows)), "ok": ok})
    # reads: the masked read hides undeclared columns; undeclared / missing / duplicated declarations are refused
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "r.xlsx"
        wb_with([["Gene", "HSB999_QX", "HSB999_QX"]] + [[d[0], 1.5, 2.5] for d in data]).save(p)
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
        ws = wb.worksheets[0]
        rows = read_openpyxl(ws, declared=["Gene"], header_row=0, label="plant")
        hidden = all(r[1] is None and r[2] is None for r in rows) and [r[0] for r in rows[1:]] == [d[0] for d in data]
        results.append({"case": "planted: a masked read of an identifier-bearing sheet returns only the declared column",
                        "expect": "undeclared cells None", "got_rules": "masked" if hidden else "LEAK", "ok": hidden})
        rows = read_openpyxl(ws, declared=lambda h: [h.index("Gene")], header_row=0, label="plant")
        hidden = all(r[1] is None and r[2] is None for r in rows) and [r[0] for r in rows[1:]] == [d[0] for d in data]
        results.append({"case": "planted: a masked read by a column rule (a function of the header row) hides the other columns",
                        "expect": "undeclared cells None", "got_rules": "masked" if hidden else "LEAK", "ok": hidden})
        for nm, kw in (("no declared columns", {}), ("a declared column missing", {"declared": ["Symbol"], "header_row": 0}),
                       ("no header row stated", {"declared": ["Gene"]}),
                       ("a header row outside the guard's zone", {"declared": ["Gene"], "header_row": GUARD_ROWS}),
                       ("a column rule returning an invalid position", {"declared": lambda h: [99], "header_row": 0})):
            try:
                read_openpyxl(ws, label="plant", **kw)
                got = "read (NOT refused)"
            except Refused:
                got = "refused"
            results.append({"case": "planted: a read of an identifier-bearing sheet with %s" % nm, "expect": "refused",
                            "got_rules": got, "ok": got == "refused"})
        wb.close()
        p2 = Path(td) / "d.xlsx"
        wb_with([["Gene", "Gene", "x"], ["A", "B", 1]]).save(p2)
        wb = openpyxl.load_workbook(p2, read_only=True, data_only=True)
        try:
            read_openpyxl(wb.worksheets[0], declared=["Gene"], header_row=0, label="plant")
            got = "read (NOT refused)"
        except Refused:
            got = "refused"
        wb.close()
        results.append({"case": "planted: a declared column found twice (clean sheet)", "expect": "refused", "got_rules": got,
                        "ok": got == "refused"})

    class FakeXlrd:  # the xlrd adapter, on a duck-typed sheet (xlrd cannot write .xls)
        def __init__(self, rows):
            self.rows, self.name = rows, "fake"
            self.nrows, self.ncols = len(rows), max(len(r) for r in rows)

        def row_values(self, r):
            return list(self.rows[r]) + [""] * (self.ncols - len(self.rows[r]))

        def cell_value(self, r, c):
            return self.row_values(r)[c]
    fx = FakeXlrd([["Module", "Color", "Size", "UMB9999"], ["M1", "turquoise", 120.0, 3.0]])
    vx = classify_xlrd(fx)
    cv = xlrd_cell_reader(fx, declared=["Module", "Color", "Size"], header_row=0, label="plant")
    okx = vx["identifier_bearing"] and cv(1, 0) == "M1" and cv(1, 3) == "" and cv(0, 3) == ""
    results.append({"case": "planted: xlrd adapter -- an identifier-valued header flagged and masked", "expect": "V, masked",
                    "got_rules": vx["rules"] if okx else "LEAK", "ok": okx})
    fc = FakeXlrd([["Module", "Color", "Size"], ["M1", "turquoise", 120.0]])
    okc = not classify_xlrd(fc)["identifier_bearing"]
    results.append({"case": "clean: xlrd adapter -- a gene-level module table", "expect": "clean",
                    "got_rules": "clean" if okc else "FLAGGED", "ok": okc})
    # no HGNC approved / previous / alias symbol is flagged by the specific patterns (CODE exempts them by construction)
    syms = hgnc_symbols()
    flagged = sum(1 for s in syms if any(pat.search(s) for _, pat in ID_VALUE))
    results.append({"case": "check: HGNC approved / previous / alias symbols flagged by a specific ID_VALUE pattern",
                    "expect": "0", "got_rules": str(flagged), "ok": flagged == 0, "n_symbols": len(syms)})
    flagged_w = sum(1 for s in syms if ID_WORDING.search(s))  # v6.10: the widened wording must not catch a gene symbol
    results.append({"case": "check v6.10: HGNC approved / previous / alias symbols matched by the identifier wording",
                    "expect": "0", "got_rules": str(flagged_w), "ok": flagged_w == 0, "n_symbols": len(syms)})
    n_ok = sum(1 for r in results if r["ok"])
    planted = [r for r in results if r["case"].startswith("planted")]
    for r in results:
        print("  %-7s %s -> %s" % ("ok" if r["ok"] else "FAILED", r["case"], r["got_rules"]))
    print("privacy guard self-test: %d / %d (planted failures caught %d / %d)" % (n_ok, len(results),
                                                                                 sum(r["ok"] for r in planted), len(planted)))
    if record is not None:
        rec = {"what": ("register DRAFT v6.8 (B S2) as revised by v6.9 / v6.10 (C1): the privacy guard's self-test "
                        "(arcs/audit/src_register/privacy_guard.py); v6.11: the exemption under a bare 'ID' only"),
               "guard_sha256": _sha256(Path(__file__)), "guard_rows": GUARD_ROWS, "wide_cols": WIDE_COLS,
               "id_value_patterns": [n for n, _ in ID_VALUE] + ["CODE"], "n_cases": len(results), "n_ok": n_ok,
               "n_planted": len(planted), "n_planted_caught": sum(r["ok"] for r in planted), "cases": results}
        txt = json.dumps(rec, indent=1, ensure_ascii=False) + "\n"
        record.write_bytes(txt.encode("utf-8"))
        assert record.read_bytes().decode("utf-8") == txt
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "selftest":
        rp = Path(sys.argv[sys.argv.index("--record") + 1]) if "--record" in sys.argv else None
        sys.exit(_selftest(rp))
    print(__doc__.split("\n")[0])
