"""Carrier test engine (claims register v4 section 1.8; pre-registered before the freeze, run under each target's gate).

Applies arcs/audit/register_maps/carrier_tests.json to a set of carrier files and prints ONLY pass / fail, a reason code
and counts per map -- never a label, header, value or any other content of a carrier (register 1.10 (2)).

  run      : python -X utf8 carrier_test.py run --target <key> [--variant dk34|dk41] --carrier <file> [--carrier <file> ...]
             [--out <json>]    (under the target's gate only)
  selftest : python -X utf8 carrier_test.py selftest [--workdir <dir>]
             builds SYNTHETIC carriers (random numbers, public atlas labels) with planted passes and planted fails for
             every conditional target and asserts that every plant is classified as planted.

Rules (verbatim in carrier_tests.json "rules"): label normalisation per label space; numeric parse; label column = the
column (or hemisphere column + name column) matching the most required labels; value column per map found by header
tiers (1: map token AND object token; 2: map token; 3: sheet / table name = map token, single numeric column), columns
whose header names a p / q / FDR / SE / SD / CI / rank / coordinate / id / label are never value columns; within a tier,
candidates that hold every required label with a numeric value are 'passing'; passing candidates with identical values
merge (the same table in several carriers); two or more distinct passing candidates -> fail (ambiguous map column); no
passing candidate at any tier -> fail with the best candidate's reason.

Register DRAFT v5 section 1.11 item 8 (readings fixed before the freeze; carrier_tests.json "amendments"): a target's
"required_labels" (Romero-Garcia: the 152 left DK-308 labels) replace its label space as the required set; a target's
"index_labels" (Mamat) lets a column of integer parcel indices 1 ... n stand for the names (names win a tie); Buch's usable
ROI = numeric coordinates (in the row, or joined through an integer ROI id) + a numeric value, no ROI id required.

Register DRAFT v6 R9 (orchestrator under the operator's standing delegation, 2026-09-26): Mamat's index-only tables qualify
only if the carrier itself names the 17-network order file (index_labels.requires_order_file_named, searched in the carrier's
text: every table cell, sheet / table name, docx text, PDF page text, notebook cell text); a carrier that names no order
file, or another one (e.g. the 7-network order), gives index-only tables that do not qualify. The text is searched by
pattern only; nothing of it is printed.

Register DRAFT v6.1 (orchestrator under the operator's standing delegation, 2026-09-26): Q1 -- one source-1 criterion for every
source-1 branch (spec 'source1_lists'; run_source1; the 'source1' command): a carrier list qualifies only if the carrier
presents it as the set's membership used as input to the enrichment, never a result list (leading edge, core enrichment,
overlap / hit genes, genes of a results-table row), its length equal to any printed size. Q8 -- the PDF adapter is pinned (spec
'pdf_adapter': pdfplumber at a fixed version, refused otherwise); a page's first table continues the previous page's last
table when the column counts are equal and its first row is a repeated header or data; the self-test builds synthetic PDFs
(matplotlib) incl. a misaligned label / value case that must be caught.

Register DRAFT v6.2 (orchestrator under the operator's standing delegation, 2026-09-26): P1 -- the criterion is positive: a list
qualifies only if its own sheet name, table title or caption (docx: the paragraph just before the table; pdf: the text line just
above it) carries input wording, and a list whose heading names one of the paper's maps, subgroups or cohorts is refused; result
markers extended (driv / contribut / core / top / PLS / loading / weight). P2 -- 'source1 --cell <id>' reads the cell's name
alternatives and printed size from source1_lists.cells (a family cell whose names come from the gated table takes --name). P6 --
the result and statistics checks read only the list's own title and the table's caption (the set's own name phrases removed);
titles are read only above a column's first data row; an upper-case title equal to a registered set name is a title, not data.
Name phrases match as whole words; a heading naming two registered sets of one target names the more specific one.

Register DRAFT v6.3 (orchestrator under the operator's standing delegation, 2026-09-26): O1 -- statistics wording in ANY column
title of a list's table refuses it; '_' and '.' are read as spaces and markers match at letter boundaries ('PLS1',
'core_enrichment', 'top_genes'); a symbol-shaped header over numbers ('NES') is a title. O2 -- input wording counts in the list's
own forward-filled title as well. O3 -- every phrase of the cell's own alternatives is removed wherever it appears, and 'top N'
with N = its printed size is exempt; a list is also named by its own title and the caption together. O4 -- a printed
'[ _]Homo sapiens[ _]hsaNNNNN' suffix is split off; one run per pathway with exactly one --name. O6 -- rival names
(source1_lists.rival_names). O7 -- selftest writes its record to --workdir and compares it with the frozen
register_maps/carrier_tests_selftest.json (run stamps aside); --overwrite-frozen-record rewrites the frozen record.

Register DRAFT v6.4 (orchestrator under the operator's standing delegation, 2026-09-26): N1 -- sheet-level refusal: any cell of a
list's sheet (docx / pdf: its table and caption), other than the lists' own gene runs, with statistics, result or map wording
refuses every list on it; NA / NS / ND / NAN / N/A and marker tokens are never data -- a single token counts only when
the WHOLE token equals a registered header, marker or map name (whole_tokens), not by substring. N2 -- own title and caption
name a set together only for the Zhang family (the caption supplying 'zhang' / 'top 500'); RG-15 / RG-V23 by their own title
only. N3 -- 'enriched' is part of the Zhang names; 'weighted gene co-expression' is not 'weight'. N4 -- a family run takes the
gated table's other printed names with --rival (rival-only names).

Register DRAFT v6.5 (orchestrator under the operator's standing delegation, 2026-09-26; decided after five review rounds, v6.0 ->
v6.4, showed that the text criterion alone could not exclude result lists): (1) CORROBORATION -- the one list the text criterion
admits (now the first filter: text_result) is source 1 only if corroborated: Jaccard >= .80 with the cell's pinned external set
(register_sets, or the sources 2-3 set built under the gate: --external), by HGNC gene within the class universe
(register_sets/UNIVERSE_GENES.json); else a length equal to the cell's printed size; a cell with neither is never corroborated
(not auditable, S undefined). (2)-(3) M1-M4: space-separated cells with a registered word or phrase, and generic titles, are not
gene lists; a multi-word cell over a column of single symbols is that column's title; dashes read as spaces; single tokens are
split on punctuation / camelCase and the pieces matched against the whole-token registry; NA-like cells are dropped from members.
The self-test checks the pre-v6.5 plants on the text filter and the v6.5 corroboration plants on the final result.

Register DRAFT v6.6 (orchestrator under the operator's standing delegation, 2026-09-27; the v6.5 re-check's B1, B2, C1-C3, C6):
B1 -- the comparator of corroboration (a) is pinned per cell (set id + the committed per-set JSON's sha256 + its members'
sha256; the Romero-Garcia KEGG families: a recipe over the pinned Enrichr libraries, built here); it is read only from the
committed register_sets folder; a file whose set id, class or either sha256 differs, and every read / parse error, sends the
cell to the else branch with its reason; the record names the set id and hashes used; --external is withdrawn. C1 -- the
printed-size check counts distinct approved HGNC symbols, not rows. C2 -- approved, previous and alias HGNC symbols are never
split into pieces. C3 -- generic titles ('GENES', 'SYMBOL' ...) are titles before the symbol test. C6 -- whole-cell statistics
wording: 'r', 't', 'corr', 'correlation' (single tokens) and 't value' / 'OR (95% CI)' (whole cells).

Register DRAFT v6.7 (orchestrator under the operator's standing delegation, 2026-09-27): a registered SECONDARY VIEW,
"near-miss comparator" -- 'source1 --view near_miss' corroborates a cell against its pinned near-miss comparator
(cells[<id>].corroboration_views.near_miss: the same pins as the primary), never changing the primary run; a cell without
such a pin refuses the view. N3: the class universes (register_sets/UNIVERSE_GENES.json) and the HGNC table the engine reads
are pinned by sha256 in the spec (source1_lists.corroboration: universe_genes_sha256, hgnc_table, universe_min_genes) and
asserted and recorded inside the same try / except that routes every read / parse / pin mismatch to the else branch (a
universe restricted below universe_min_genes genes per class is refused even with its hash pinned).

Register DRAFT v6.8 (orchestrator under the operator's standing delegation, 2026-09-29; post hoc, declared): B S1 -- asdM12 moved
to the near-miss view (BUCH-E-ASDdown-S1 ... S4: mode none in the primary run, their near-miss pin Voineagu 2011's Table 14 set);
the self-test's v6.7 N1 plants become near-miss-view plants (qualifies in the view; else branch in the primary; a 30-gene subset
fails in the view). The engine is unchanged; it prints nothing of a carrier (register 1.10 (2)), so the v6.8 privacy guard
(privacy_guard.py) has nothing to mask here.
Register DRAFT v6.9 (C5; post hoc, declared): Buch's 'ASD rare de novo' moved to the near-miss view by reading (iii) applied
uniformly (BUCH-E-RDNV-S1 ... S4, descriptor cells: mode none in the primary run, their near-miss pin Sanders 2019's ASD65 set);
two self-test plants (qualifies in the view; else branch in the primary). The engine is unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import html.parser
import io
import json
import math
import random
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / "arcs" / "audit" / "register_maps" / "carrier_tests.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))
import name_match as NM  # noqa: E402  (register v6.1 Q1: the name rule's normalisation, for 'a heading naming the set')
PDF_PIN = {"version": None}  # register v6.1 Q8: set from the spec's pdf_adapter before any carrier is read

NUM_RE = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")
EXCL = re.compile(r"(^|[^a-z])(p|q)([\s_-]*(val(ue)?|fdr|adj(usted)?))?($|[^a-z])|fdr|std|(^|[^a-z])(se|sd|ci)($|[^a-z])|lower|upper|"
                  r"rank|coordinat|(^|[^a-z])(x|y|z|id)($|[^a-z])|index|"
                  r"(^|[^a-z])(label|name|region|parcel|roi|hemisphere)s?($|[^a-z])")
HEMI_TOK = re.compile(r"^(l|r|lh|rh|left|right)$")
HEMI_LEAD = re.compile(r"^(ctx[-_ .]?)?(lh|rh|left|right|l|r)[-_ .]+")
HEMI_TRAIL = re.compile(r"[-_ .(]+(lh|rh|left|right|l|r)\)?$")
DK_ALIAS = {"thalamus": "thalamusproper", "accumbens": "accumbensarea"}
TRIPLE = re.compile(r"^\(?\s*([+-]?\d+(?:\.\d+)?)\s*[,; ]\s*([+-]?\d+(?:\.\d+)?)\s*[,; ]\s*([+-]?\d+(?:\.\d+)?)\s*\)?$")
XYZ_HDR = {ax: re.compile(r"^\W*(mni\W*)?%s\W*(\(mm\)|mm)?\W*$" % ax) for ax in "xyz"}
ID_HDR = re.compile(r"roi|(^|[^a-z])id($|[^a-z])|index|node|power|number|^no\.?$|^#$")


class AdapterUnavailable(Exception):
    pass


# ----------------------------------------------------------------------------------------------------------- parsing
def parse_num(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        f = float(v)
        return f if math.isfinite(f) else None
    if isinstance(v, str):
        s = v.strip().replace("−", "-")
        if NUM_RE.match(s):
            f = float(s)
            return f if math.isfinite(f) else None
    return None


def cell_str(v) -> str:
    return "" if v is None else str(v).strip()


class _HTMLTables(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self._t, self._r, self._c = [], None, None, None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._t = []
        elif tag == "tr" and self._t is not None:
            self._r = []
        elif tag in ("td", "th") and self._r is not None:
            self._c = []

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._c is not None and self._r is not None:
            self._r.append(" ".join("".join(self._c).split()))
            self._c = None
        elif tag == "tr" and self._r is not None and self._t is not None:
            self._t.append(self._r)
            self._r = None
        elif tag == "table" and self._t is not None:
            self.tables.append(self._t)
            self._t = None

    def handle_data(self, data):
        if self._c is not None:
            self._c.append(data)


def tables_from_bytes(name: str, data: bytes, log: dict) -> list:
    suf = Path(name).suffix.lower()
    out = []
    if suf in (".xlsx", ".xlsm"):
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        for ws in wb.worksheets:
            out.append({"name": ws.title, "title": ws.title, "rows": [list(r) for r in ws.iter_rows(values_only=True)]})
        wb.close()
    elif suf in (".csv", ".tsv"):
        import csv
        txt = data.decode("utf-8-sig", errors="replace")
        delim = "\t" if (suf == ".tsv" or txt.count("\t") > txt.count(",")) else ","
        out.append({"name": Path(name).stem, "title": Path(name).stem,
                    "rows": [list(r) for r in csv.reader(io.StringIO(txt), delimiter=delim)]})
    elif suf == ".txt":
        txt = data.decode("utf-8-sig", errors="replace")
        split = (lambda l: l.split("\t")) if "\t" in txt else (lambda l: l.split())
        out.append({"name": Path(name).stem, "title": Path(name).stem, "rows": [split(l) for l in txt.splitlines() if l.strip()]})
    elif suf == ".docx":
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            raw = z.read("word/document.xml")
        if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:  # no DTD / entity expansion from a downloaded file
            raise ValueError("DTD in docx XML refused")
        root = ET.fromstring(raw)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        out.append({"name": "%s#text" % Path(name).stem, "text_only": True,  # register v6 R9: the document's text
                    "rows": [["".join(t.text or "" for t in para.iter("{%s}t" % ns["w"]))] for para in root.iter("{%s}p" % ns["w"])]})
        cap, last = {}, None  # register v6.2 P1: a body-level table's caption = the non-empty paragraph just before it
        body = root.find("w:body", ns)
        for child in (list(body) if body is not None else []):
            if child.tag == "{%s}p" % ns["w"]:
                txt = "".join(t.text or "" for t in child.iter("{%s}t" % ns["w"])).strip()
                if txt:
                    last = txt
            elif child.tag == "{%s}tbl" % ns["w"]:
                cap[id(child)] = last
        for k, tbl in enumerate(root.iter("{%s}tbl" % ns["w"])):
            rows = []
            for tr in tbl.findall("w:tr", ns):
                rows.append(["".join(t.text or "" for t in tc.iter("{%s}t" % ns["w"])).strip() for tc in tr.findall("w:tc", ns)])
            out.append({"name": "%s#table%d" % (Path(name).stem, k + 1), "rows": rows, "caption": cap.get(id(tbl))})
    elif suf == ".ipynb":
        nb = json.loads(data.decode("utf-8"))
        k = 0
        txt_rows = []  # register v6 R9: cell sources and plain-text outputs
        for cell in nb.get("cells", []):
            src = cell.get("source", "")
            txt_rows.append(["".join(src) if isinstance(src, list) else str(src)])
            for o in cell.get("outputs", []) or []:
                t = (o.get("data") or {}).get("text/plain") or o.get("text")
                if t:
                    txt_rows.append(["".join(t) if isinstance(t, list) else str(t)])
        out.append({"name": "%s#text" % Path(name).stem, "text_only": True, "rows": txt_rows})
        for cell in nb.get("cells", []):
            for o in cell.get("outputs", []) or []:
                h = (o.get("data") or {}).get("text/html")
                if h:
                    p = _HTMLTables()
                    p.feed("".join(h) if isinstance(h, list) else h)
                    for t in p.tables:
                        k += 1
                        out.append({"name": "%s#output_table%d" % (Path(name).stem, k), "rows": t})
    elif suf == ".pdf":
        try:
            import pdfplumber  # register v6.1 Q8: pinned (spec pdf_adapter); another version counts as unavailable
        except ImportError:
            raise AdapterUnavailable("pdf")
        if PDF_PIN["version"] is None or pdfplumber.__version__ != PDF_PIN["version"]:
            raise AdapterUnavailable("pdf_version")
        last = None  # the last table of the previous page (a page's first table may continue it)
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for i, page in enumerate(pdf.pages):
                found = [(ft.extract(), ft.bbox) for ft in page.find_tables()]  # = page.extract_tables(), with each bbox
                caps = []
                for t, bb in found:  # register v6.2 P1: the caption = the last text line above the table on its page
                    above = page.crop((0, 0, page.width, max(1.0, float(bb[1])))).extract_text() if bb[1] > 1 else ""
                    lines = [ln for ln in (above or "").splitlines() if ln.strip()]
                    caps.append(lines[-1].strip() if lines else None)
                tabs = [(t, c) for (t, _), c in zip(found, caps) if t]
                page_last = None
                for k, (t, cap) in enumerate(tabs):
                    head = [cell_str(v) for v in t[0]]
                    is_header = all(parse_num(v) is None for v in head)
                    if (k == 0 and last is not None and len(t[0]) == len(last["rows"][0])
                            and (head == [cell_str(v) for v in last["rows"][0]] or not is_header)):
                        last["rows"].extend(t[1:] if head == [cell_str(v) for v in last["rows"][0]] else t)
                        page_last = last
                        continue
                    ent = {"name": "%s#p%d_t%d" % (Path(name).stem, i + 1, k + 1), "rows": [list(r) for r in t], "caption": cap}
                    out.append(ent)
                    page_last = ent
                last = page_last
                out.append({"name": "%s#p%d_text" % (Path(name).stem, i + 1), "text_only": True,  # register v6 R9
                            "rows": [[ln] for ln in (page.extract_text() or "").splitlines()]})
    elif suf == ".zip":
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for m in z.infolist():
                if not m.is_dir() and Path(m.filename).suffix.lower() in (".xlsx", ".xlsm", ".csv", ".tsv", ".txt", ".docx", ".pdf"):
                    out.extend(safe_tables(m.filename, z.read(m.filename), log))
    elif suf == ".xls":
        raise AdapterUnavailable("xls")
    else:
        log["n_files_unsupported"] = log.get("n_files_unsupported", 0) + 1
    return out


def safe_tables(name, data, log) -> list:
    log["n_files"] = log.get("n_files", 0) + 1
    try:
        t = tables_from_bytes(name, data, log)
        log["n_files_parsed"] = log.get("n_files_parsed", 0) + 1
        return t
    except AdapterUnavailable as e:
        key = "n_files_adapter_unavailable_%s" % e.args[0]
        log[key] = log.get(key, 0) + 1
        return []
    except Exception as e:  # noqa: BLE001  (only the exception type is recorded; never content)
        key = "n_files_parse_error_%s" % type(e).__name__
        log[key] = log.get(key, 0) + 1
        return []


def load_tables(paths) -> tuple:
    log, tables = {}, []
    for p in paths:
        p = Path(p)
        tables.extend(safe_tables(p.name, p.read_bytes(), log))
    for t in tables:  # rectangularise
        w = max((len(r) for r in t["rows"]), default=0)
        t["rows"] = [list(r) + [None] * (w - len(r)) for r in t["rows"]]
    log["n_tables"] = len(tables)
    return tables, log


# ------------------------------------------------------------------------------------------------- normalisation
def split_hemi(s: str):
    s = s.lower().strip()
    m = HEMI_LEAD.match(s)
    if m:
        return m.group(2)[0].upper(), s[m.end():]
    m = HEMI_TRAIL.search(s)
    if m:
        return m.group(1)[0].upper(), s[:m.start()]
    return None, s


def key_dk(v, hemi_override=None):
    s = cell_str(v)
    if not s or parse_num(s) is not None:
        return None, False
    h, rest = split_hemi(s)
    if hemi_override:
        h = hemi_override
    base = re.sub(r"[^a-z0-9]", "", rest)
    base = DK_ALIAS.get(base, base)
    if not h:
        return base, True  # (unlateralised name)
    return "%s:%s" % (h, base), False


def key_dk308(v, hemi_override=None):
    s = cell_str(v)
    if not s or parse_num(s) is not None:
        return None, False
    h, rest = split_hemi(s)
    if hemi_override:
        h = hemi_override
    base = re.sub(r"[^a-z0-9_]", "", rest)
    if not h:
        return base, True
    return "%s:%s" % (h, base), False


def key_schaefer(v, hemi_override=None):
    s = cell_str(v).lower()
    if not s or parse_num(s) is not None:
        return None, False
    s = re.sub(r"^17networks[_-]", "", s)
    s = re.sub(r"[-. ]", "_", s)
    return "S:" + s, False


KEYFN = {"normalisation_dk": key_dk, "normalisation_dk308": key_dk308, "normalisation_schaefer": key_schaefer}


def carrier_text(tables) -> str:
    """register v6 R9: every table and sheet name, every cell string and every text line of the carrier (searched by pattern
    only; never printed)."""
    parts = []
    for t in tables:
        parts.append(str(t.get("name") or ""))
        for r in t["rows"]:
            parts.extend(cell_str(v) for v in r if v is not None)
    return "\n".join(parts)


def order_file_named(idx_spec: dict, text: str):
    """register v6 R9: (ok, reason code) -- the carrier names the 17-network order file and no other Schaefer order file."""
    req = idx_spec.get("requires_order_file_named")
    if not req:
        return True, "order file not required"
    p17 = re.compile(req["pattern_17"], re.I)
    pany = re.compile(req["pattern_any_order_file"], re.I)
    others = [m.group(0) for m in pany.finditer(text) if not p17.fullmatch(m.group(0))]
    if others:
        return False, "another order file named"
    if not p17.search(text):
        return False, "no order file named"
    return True, "17-network order file named"


def make_key_index(idx2key: dict):
    """register v5 section 1.11 item 8 (Mamat): an integer parcel index i stands for the i-th label of the order file."""
    def key_index(v, hemi_override=None):
        f = parse_num(v)
        if f is None or not float(f).is_integer():
            return None, False
        return idx2key.get(int(f)), False
    return key_index


def hemi_value(v):
    s = cell_str(v).lower()
    return s[0].upper() if HEMI_TOK.match(s) else None


# ---------------------------------------------------------------------------------------------- label-list tables
def label_columns(table, required: set, keyfn):
    """Best (hemi_col, label_col) for this table; returns (n_matched, hemi_col, label_col, {key: row}, n_unlat, dups)."""
    rows = table["rows"]
    ncol = len(rows[0]) if rows else 0
    hemi_cols = [j for j in range(ncol) if sum(1 for r in rows if hemi_value(r[j])) >= max(2, 0.5 * sum(1 for r in rows if cell_str(r[j])))]
    best = (0, None, None, {}, 0, set())
    for j in range(ncol):
        for h in [None] + [c for c in hemi_cols if c != j]:
            keys, unlat, dups = {}, 0, set()
            for i, r in enumerate(rows):
                k, is_unlat = keyfn(r[j], hemi_value(r[h]) if h is not None else None)
                if k is None:
                    continue
                if is_unlat:
                    unlat += 1
                    continue
                if k in required:
                    if k in keys:
                        dups.add(k)
                    else:
                        keys[k] = i
            if len(keys) > best[0]:
                best = (len(keys), h, j, keys, unlat, dups)
    return best


def header_text(table, first_data_row: int, j: int) -> str:
    parts = []
    for r in table["rows"][:first_data_row]:
        filled, last = [], None
        for v in r:  # forward-fill a header row horizontally (merged header cells)
            s = cell_str(v)
            if s:
                last = s
            filled.append(s if s else (last or ""))
        s = filled[j] if j < len(filled) else ""
        if s and parse_num(s) is None:
            parts.append(s)
    return " | ".join(parts).lower()


def candidates(tables_info, mp, tier):
    tok = re.compile(mp["map_token"], re.I)
    obj = re.compile(mp["object_token"], re.I)
    out = []
    for ti in tables_info:
        t = ti["table"]
        if tier in (1, 2):
            for j in ti["value_cols"]:
                h = ti["headers"][j]
                if not h or EXCL.search(h):
                    continue
                if tok.search(h) and (tier == 2 or obj.search(h)):
                    out.append((ti, j))
        else:
            if tok.search(t["name"] or ""):
                numeric = [j for j in ti["value_cols"] if not EXCL.search(ti["headers"][j] or "")
                           and all(parse_num(t["rows"][i][j]) is not None for i in ti["rowmap"].values())]
                if len(numeric) == 1:
                    out.append((ti, numeric[0]))
    return out


def evaluate_labels(ti, j, required_keys):
    t = ti["table"]
    present = [k for k in required_keys if k in ti["rowmap"]]
    vals = {k: parse_num(t["rows"][ti["rowmap"][k]][j]) for k in present}
    n_num = sum(1 for v in vals.values() if v is not None)
    dup_conflict = False
    for k in ti["dups"]:  # duplicate rows of a required label: conflicting values fail
        vs = {parse_num(r[j]) for i, r in enumerate(t["rows"]) if ti["keyfn"](r[ti["label_col"]], hemi_value(r[ti["hemi_col"]])
                                                                                 if ti["hemi_col"] is not None else None)[0] == k}
        if len(vs) > 1:
            dup_conflict = True
    if len(present) < len(required_keys):
        reason = "labels missing"
    elif n_num < len(required_keys):
        reason = "non-numeric values"
    elif dup_conflict:
        reason = "duplicate labels"
    else:
        reason = "ok"
    return {"reason": reason, "n_present": len(present), "n_numeric": n_num,
            "vector": tuple(vals[k] for k in required_keys) if reason == "ok" else None}


def run_label_target(spec_t, tables, required_keys, keyfn_name, text=""):
    keyfn = KEYFN[keyfn_name]
    req = set(required_keys)
    idx_spec = spec_t.get("index_labels") or {}
    keyfn_idx = None
    infos, diag = [], {"n_tables_with_labels": 0, "n_unlateralised_names": 0, "n_index_only_tables": 0,
                       "n_index_labelled_tables": 0}
    idx_ok, idx_why = False, None
    if idx_spec.get("allowed"):  # register v5 section 1.11 item 8: parcels by name OR by index (names win a tie) ...
        idx_ok, idx_why = order_file_named(idx_spec, text)  # ... v6 R9: only where the carrier names the order file
        diag["index_order_file"] = idx_why
    if idx_ok:
        lo, hi = idx_spec["range"]
        idx2key = {d["index"]: d["key"] for d in spec_t["labels_detail"] if lo <= d["index"] <= hi and d["key"] in req}
        keyfn_idx = make_key_index(idx2key)
    for t in tables:
        n, h, j, rowmap, unlat, dups = label_columns(t, req, keyfn)
        diag["n_unlateralised_names"] += unlat
        kf = keyfn
        if keyfn_idx is not None:
            ni, hi_, ji, rowmap_i, _, dups_i = label_columns(t, req, keyfn_idx)
            if ni > n:
                n, h, j, rowmap, dups, kf = ni, None, ji, rowmap_i, dups_i, keyfn_idx
                diag["n_index_labelled_tables"] += 1
        if n == 0:
            if keyfn_name == "normalisation_schaefer" and keyfn_idx is None:
                for c in range(len(t["rows"][0]) if t["rows"] else 0):
                    ints = {int(v) for v in (parse_num(r[c]) for r in t["rows"]) if v is not None and float(v).is_integer()}
                    if len(ints & set(range(1, 401))) >= 390:
                        diag["n_index_only_tables"] += 1
                        break
            continue
        diag["n_tables_with_labels"] += 1
        first = min(rowmap.values())
        ncol = len(t["rows"][0])
        vcols = [c for c in range(ncol) if c not in (j, h)]
        infos.append({"table": t, "label_col": j, "hemi_col": h, "rowmap": rowmap, "dups": dups, "keyfn": kf,
                      "value_cols": vcols, "headers": {c: header_text(t, first, c) for c in range(ncol)}})
    results = []
    for mp in spec_t["maps"]:
        best, decided = None, None
        for tier in (1, 2, 3):
            cands = candidates(infos, mp, tier)
            evals = [evaluate_labels(ti, j, required_keys) for ti, j in cands]
            passing = {e["vector"] for e in evals if e["reason"] == "ok"}
            for e in evals:
                if best is None or (e["n_present"], e["n_numeric"]) > (best[1]["n_present"], best[1]["n_numeric"]):
                    best = (tier, e, len(cands))
            if len(passing) == 1:
                decided = {"result": "pass", "reason": "ok", "tier": tier, "n_candidates": len(cands),
                           "n_passing_candidates": sum(1 for e in evals if e["reason"] == "ok"), "n_distinct_passing": 1,
                           "n_present": len(required_keys), "n_numeric": len(required_keys)}
                break
            if len(passing) > 1:
                decided = {"result": "fail", "reason": "ambiguous map column", "tier": tier, "n_candidates": len(cands),
                           "n_passing_candidates": sum(1 for e in evals if e["reason"] == "ok"),
                           "n_distinct_passing": len(passing), "n_present": len(required_keys), "n_numeric": len(required_keys)}
                break
        if decided is None:
            if best is None:
                decided = {"result": "fail", "reason": "no map column" if infos else "no labelled table", "tier": None,
                           "n_candidates": 0, "n_passing_candidates": 0, "n_distinct_passing": 0, "n_present": 0, "n_numeric": 0}
            else:
                decided = {"result": "fail", "reason": best[1]["reason"], "tier": best[0], "n_candidates": best[2],
                           "n_passing_candidates": 0, "n_distinct_passing": 0,
                           "n_present": best[1]["n_present"], "n_numeric": best[1]["n_numeric"]}
        decided.update(map_id=mp["map_id"], n_required=len(required_keys))
        if decided["result"] == "fail" and idx_spec.get("allowed") and not idx_ok and diag["n_index_only_tables"] > 0:
            decided["reason"] += " (index-only table not accepted: %s; R9)" % idx_why
        results.append(decided)
    return results, diag


# ------------------------------------------------------------------------------------------------------ Power / Buch
def xyz_cols(t, first):
    ncol = len(t["rows"][0]) if t["rows"] else 0
    hdr = {c: header_text(t, first, c) for c in range(ncol)}
    axes = {}
    for ax, rx in XYZ_HDR.items():
        hits = [c for c in range(ncol) if rx.match(hdr[c].split(" | ")[-1] if hdr[c] else "")]
        if len(hits) == 1:
            axes[ax] = hits[0]
    triple = [c for c in range(ncol) if sum(1 for r in t["rows"][first:] if TRIPLE.match(cell_str(r[c]))) >= 10]
    return hdr, axes, triple


def _int_or_none(v):
    f = parse_num(v)
    return int(f) if f is not None and float(f).is_integer() else None


def _row_xyz(r, axes, triple):
    if len(axes) == 3:
        v = [parse_num(r[axes[a]]) for a in "xyz"]
        return v if all(x is not None for x in v) else None
    if len(triple) == 1:
        m = TRIPLE.match(cell_str(r[triple[0]]))
        return [float(m.group(k)) for k in (1, 2, 3)] if m else None
    return None


def run_power_target(spec_t, tables):
    """register v5 section 1.11 item 8: a usable ROI = numeric coordinates (in the row, or joined through an integer ROI id to
    coordinates elsewhere in the carrier) + a numeric value on the map; no ROI id required. Power matching is a diagnostic."""
    power = {d["roi"]: d["mni_xyz"] for d in spec_t["labels_detail"]}
    coords, conflicts, roi_tables = {}, 0, []
    xyz_seen = {}  # every coordinate triple in the carrier (for the diagnostics), keyed by its rounded value
    for t in tables:
        rows = t["rows"]
        if not rows:
            continue
        first = next((i for i, r in enumerate(rows) if sum(1 for v in r if parse_num(v) is not None) >= 2), None)
        if first is None:
            continue
        hdr, axes, triple = xyz_cols(t, first)
        has_xyz = len(axes) == 3 or len(triple) == 1
        idc = [c for c in range(len(rows[0])) if hdr[c] and ID_HDR.search(hdr[c]) and not any(rx.match(hdr[c].split(" | ")[-1])
                                                                                               for rx in XYZ_HDR.values())]
        idc = [c for c in idc if sum(1 for r in rows[first:] if _int_or_none(r[c]) is not None) >= 10]
        ic = idc[0] if len(idc) == 1 else None
        if ic is None and not has_xyz:
            continue
        for r in rows[first:]:
            xyz = _row_xyz(r, axes, triple) if has_xyz else None
            if xyz is None:
                continue
            xyz_seen.setdefault(tuple(round(a, 3) for a in xyz), xyz)
            rid = _int_or_none(r[ic]) if ic is not None else None
            if rid is not None:
                if rid in coords and any(abs(a - b) > 1e-9 for a, b in zip(coords[rid], xyz)):
                    conflicts += 1
                coords.setdefault(rid, xyz)
        roi_tables.append({"table": t, "first": first, "id_col": ic, "has_xyz": has_xyz, "axes": axes, "triple": triple,
                           "headers": hdr,
                           "value_cols": [c for c in range(len(rows[0])) if c != ic and c not in axes.values() and c not in triple]})
    # Power matching (diagnostic only) of every coordinate triple in the carrier
    by_id = by_coord = extra = 0
    id_of = {tuple(round(a, 3) for a in xyz): rid for rid, xyz in coords.items()}
    for key, xyz in xyz_seen.items():
        rid = id_of.get(key)
        if rid is not None and rid in power and math.dist(power[rid], xyz) <= 2.0:
            by_id += 1
        elif min(math.dist(p, xyz) for p in power.values()) <= 2.0:
            by_coord += 1
        else:
            extra += 1
    diag = {"n_rois_with_coordinates": len(xyz_seen), "n_power_matched_by_id": by_id, "n_power_matched_by_coordinates": by_coord,
            "n_extra_rois_with_coordinates": extra, "n_coordinate_conflicts": conflicts, "n_roi_tables": len(roi_tables),
            "n_roi_tables_with_ids": sum(1 for ti in roi_tables if ti["id_col"] is not None)}
    need = spec_t["required_count"]
    results = []
    for mp in spec_t["maps"]:
        tok, obj = re.compile(mp["map_token"], re.I), re.compile(mp["object_token"], re.I)
        best, decided = None, None
        for tier in (1, 2, 3):
            cands = []
            for ti in roi_tables:
                if tier in (1, 2):
                    for c in ti["value_cols"]:
                        h = ti["headers"][c]
                        if h and not EXCL.search(h) and tok.search(h) and (tier == 2 or obj.search(h)):
                            cands.append((ti, c))
                elif tok.search(ti["table"]["name"] or ""):
                    num = [c for c in ti["value_cols"] if not EXCL.search(ti["headers"][c] or "")
                           and sum(1 for r in ti["table"]["rows"][ti["first"]:] if parse_num(r[c]) is not None) >= need]
                    if len(num) == 1:
                        cands.append((ti, num[0]))
            evals = []
            for ti, c in cands:
                vals, dup, n_num = {}, False, 0
                for r in ti["table"]["rows"][ti["first"]:]:
                    v = parse_num(r[c])
                    if v is None:
                        continue
                    n_num += 1
                    rid = _int_or_none(r[ti["id_col"]]) if ti["id_col"] is not None else None
                    xyz = _row_xyz(r, ti["axes"], ti["triple"]) if ti["has_xyz"] else None
                    if xyz is None and rid is not None:
                        xyz = coords.get(rid)
                    if xyz is None:
                        continue  # no coordinates for this ROI: not usable
                    key = ("id", rid) if rid is not None else ("xyz",) + tuple(round(a, 3) for a in xyz)
                    if key in vals and vals[key] != v:
                        dup = True
                    vals[key] = v
                reason = ("coordinates missing" if not xyz_seen else "duplicate labels" if dup
                          else "count below required" if len(vals) < need else "ok")
                evals.append({"reason": reason, "n_numeric": n_num, "n_usable": len(vals),
                              "vector": tuple(sorted(vals.items(), key=repr)) if reason == "ok" else None})
            for e in evals:
                if best is None or e["n_usable"] > best[1]["n_usable"]:
                    best = (tier, e, len(cands))
            passing = {e["vector"] for e in evals if e["reason"] == "ok"}
            if len(passing) >= 1:
                ok = len(passing) == 1
                decided = {"result": "pass" if ok else "fail", "reason": "ok" if ok else "ambiguous map column", "tier": tier,
                           "n_candidates": len(cands), "n_distinct_passing": len(passing),
                           "n_usable": max(e["n_usable"] for e in evals if e["reason"] == "ok")}
                break
        if decided is None:
            decided = ({"result": "fail", "reason": "coordinates missing" if not coords else "no map column", "tier": None,
                        "n_candidates": 0, "n_distinct_passing": 0, "n_usable": 0} if best is None else
                       {"result": "fail", "reason": best[1]["reason"], "tier": best[0], "n_candidates": best[2],
                        "n_distinct_passing": 0, "n_usable": best[1]["n_usable"]})
        decided.update(map_id=mp["map_id"], n_required=need, required_comparison=">=")
        results.append(decided)
    return results, diag


# ------------------------------------------------------------------------------------------------------------- run
def run(target: str, carriers, variant=None, spec=None):
    spec = spec or json.loads(SPEC.read_text(encoding="utf-8"))
    PDF_PIN["version"] = (spec.get("pdf_adapter") or {}).get("version")
    st = spec["targets"][target]
    tables, log = load_tables(carriers)
    text = carrier_text(tables)  # register v6 R9 (searched by pattern only)
    tables = [t for t in tables if not t.get("text_only")]
    log["n_tables"] = len(tables)
    if target == "buch2023asdsubgroups":
        res, diag = run_power_target(st, tables)
    else:
        if target == "rasero2023neurogenetics":
            if variant not in st["variants"]:
                raise SystemExit("rasero needs --variant dk34|dk41 (fixed from notebook 08 / the Methods before this run)")
            keys = st["variants"][variant]["labels"]
        else:
            keys = st.get("required_labels", st["labels"])  # register v5 section 1.11 item 8 (Romero-Garcia: 152 left labels)
        res, diag = run_label_target(st, tables, keys, st["normalisation"], text)
    incomplete = any(k.startswith("n_files_adapter_unavailable") or k.startswith("n_files_parse_error") for k in log)
    for r in res:
        if r["result"] == "fail" and incomplete:
            r["reason"] += " (incomplete search: a carrier file could not be parsed)"
    return {"target": target, "variant": variant, "log": log, "diagnostics": diag, "maps": res,
            "target_pass": all(r["result"] == "pass" for r in res)}


def fmt(r) -> str:
    parts = ["%s=%s" % (k, r[k]) for k in ("n_required", "n_present", "n_numeric", "n_usable", "tier", "n_candidates",
                                            "n_distinct_passing") if k in r]
    return "%-22s %-4s %-28s %s" % (r["map_id"][:22], r["result"].upper(), r["reason"][:28], " ".join(parts))


# ------------------------------------------ source-1 lists (v6.1 Q1; v6.2 P1 / P2 / P6; v6.3 O1-O4, O6; v6.4 N1-N4)
DASHES = "\u2010\u2011\u2012\u2013\u2014\u2015\u2212"  # v6.5 M2: the Unicode dashes (the ASCII hyphen is added below)


def _tx(s: str) -> str:
    """a heading or a phrase as every source-1 check reads it: '_', '.' (v6.3 O1 (b)) and every dash (v6.5 M2) as spaces, then the
    name rule's normalisation (case, UK / US spelling, singular / plural)."""
    return NM.norm(re.sub("[_.\\-%s]" % DASHES, " ", str(s or "")))


def _pieces(raw: str) -> list:
    """v6.5 M3: a single token that is not gene-symbol-shaped, split on punctuation and camelCase ('normalizedEnrichmentScore' ->
    normalized, enrichment, score; '-log10(P)' -> log, 10, p), each piece read as a heading is."""
    return [NM.norm(x) for x in re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", str(raw or ""))]


_CORR = {}  # v6.5: the HGNC reader and the class universes; v6.7 N3: cached per pinned (path, sha256) pair


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _corr_env(spec: dict):
    """v6.5 / v6.7 N3: the HGNC table and the class universes corroboration uses, each read from the path the spec pins and
    asserted equal to its pinned sha256 (the universe also at least universe_min_genes genes in every class). Any read / parse
    / pin mismatch RAISES -- the callers route it to the else branch and record it. Returns (hg, uni, used, all HGNC symbols)."""
    cc = spec["source1_lists"]["corroboration"]
    uf = ROOT / cc["universe_genes"]
    ht = cc["hgnc_table"]
    key = (str(uf), cc["universe_genes_sha256"], ht["path"], ht["sha256"], cc["universe_min_genes"])
    if key not in _CORR:
        used = {"universe_genes": str(cc["universe_genes"]), "pinned_universe_genes_sha256": cc["universe_genes_sha256"],
                "hgnc_table": ht["path"], "pinned_hgnc_sha256": ht["sha256"]}
        ub = uf.read_bytes()
        used["universe_genes_sha256"] = _sha(ub)
        if used["universe_genes_sha256"] != cc["universe_genes_sha256"]:
            raise ValueError("UNIVERSE_GENES.json sha256 differs from the pinned one")
        uni = {c: set(v) for c, v in json.loads(ub.decode("utf-8"))["classes"].items()}
        small = sorted(c for c, v in uni.items() if len(v) < cc["universe_min_genes"])
        if small or not uni:
            raise ValueError("universe too small: classes %s under %d genes" % (small, cc["universe_min_genes"]))
        h = hashlib.sha256()
        with open(ht["path"], "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        used["hgnc_sha256"] = h.hexdigest()
        if used["hgnc_sha256"] != ht["sha256"]:
            raise ValueError("the HGNC table's sha256 differs from the pinned one")
        import s_build as SB  # the S-build's HGNC rule (approved -> previous -> alias; ambiguous dropped)
        if str(SB.PIN["hgnc"][0]) != ht["path"] or SB.PIN["hgnc"][1] != ht["sha256"]:
            raise ValueError("the S-build's HGNC pin is not the spec's")
        hg = SB.HGNC()
        _CORR[key] = (hg, uni, used, set(hg.approved) | set(hg.prev) | set(hg.alias))  # v6.6 C2: never split into pieces
    hg, uni, used, allsym = _CORR[key]
    return hg, uni, dict(used), allsym


def _env_err(e: Exception) -> str:
    """v6.7 N3: a deterministic record of an environment failure -- the exception type, and the message only for the engine's own
    ValueErrors (an OS error's message carries a path, which differs between runs)."""
    return "%s: %s" % (type(e).__name__, e) if isinstance(e, ValueError) else type(e).__name__


def _hgnc_all(spec: dict) -> set:
    return _corr_env(spec)[3]


def _load_pinned(c: dict, spec: dict) -> tuple:
    """v6.6 B1: the committed comparator named by the pins, or a refusal reason. Returns (members or None, reason, used)."""
    cc = spec["source1_lists"]["corroboration"]
    f = ROOT / cc.get("sets_dir", "arcs/audit/register_sets") / (str(c.get("set_id")) + ".json")
    used = {"set_id": c.get("set_id"), "file": f.name, "pinned_json_sha256": c.get("json_sha256"),
            "pinned_members_sha256": c.get("members_sha256")}
    try:
        data = f.read_bytes()
    except OSError as e:
        return None, "comparator refused: file unreadable (%s)" % type(e).__name__, used
    used["json_sha256"] = _sha(data)
    if used["json_sha256"] != c.get("json_sha256"):
        return None, "comparator refused: file sha256 differs from the pinned committed set", used
    try:
        body = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None, "comparator refused: malformed JSON", used
    if not isinstance(body, dict) or body.get("set_id") != c.get("set_id"):
        return None, "comparator refused: set id differs from the pinned set", used
    mem = body.get("members_hgnc")
    if not isinstance(mem, list) or not all(isinstance(x, str) for x in mem):
        return None, "comparator refused: no members_hgnc list", used
    used["members_sha256"] = _sha("\n".join(mem).encode("utf-8"))
    if used["members_sha256"] != c.get("members_sha256"):
        return None, "comparator refused: members sha256 differs from the pinned set", used
    if c.get("class") not in (body.get("universe") or {}):
        return None, "comparator refused: class %s not in the committed set's universe" % c.get("class"), used
    return mem, None, used


def _kegg_recipe(c: dict, name: str | None, rivals, hg) -> tuple:
    """v6.6 B1: the Romero-Garcia KEGG family comparator, built here from the pinned Enrichr libraries by register 1.6's KEGG
    family rule (s_build.kegg_family_choice) and the name rule. Returns (members or None, reason, used)."""
    rec = c.get("recipe") or {}
    used = {"recipe": rec.get("recipe"), "name": name}
    if not name:
        return None, "comparator refused: the recipe needs the run's one --name", used
    try:
        import s_build as SB
        libs, mems = {}, {}
        src = SB.Sources()
        for lib, d in sorted((rec.get("libraries") or {}).items()):
            path = SB.PIN[d["key"]][0]
            got = _sha(Path(path).read_bytes())
            used["%s_sha256" % lib] = got
            if got != d["sha256"]:
                return None, "comparator refused: library %s sha256 differs from the pinned one" % lib, used
            terms, mem = src.enrichr(d["key"], False, SB.KEGG16_SUFFIX if lib == "KEGG_2016" else None)
            libs[lib], mems[lib] = terms, mem
        if sorted(libs) != ["KEGG_2015", "KEGG_2016"]:
            return None, "comparator refused: the recipe does not name both libraries", used
        ch = SB.kegg_family_choice([name] + [r for r in (rivals or []) if r != name], libs)
        lib, pid = ch["per_name"][name]
        used.update(chosen_library=ch["chosen"], library=lib, pathway=pid)
        if not pid:
            return None, "comparator refused: the name reaches no pathway of either library", used
        members = sorted({hg.symbol(g["symbol"])[0] for g in mems[lib][pid]} - {None})
        used["members_sha256"] = _sha("\n".join(members).encode("utf-8"))
        return members, None, used
    except Exception as e:  # noqa: BLE001  every read / parse error -> the else branch
        return None, "comparator refused: recipe error (%s)" % type(e).__name__, used


def corroborate(genes, ent: dict, spec: dict, name=None, rivals=None, view=None) -> tuple:
    """register v6.5 (1) as pinned by v6.6 B1 / C1: is the one list the text criterion admits corroborated? Returns (passed,
    record: counts, the set id and hashes used, or the refusal reason). name / rivals: a family run's --name / --rival
    (the KEGG family recipe)."""
    c = (ent or {}).get("corroboration") or {"mode": "none", "why": "no cell entry (explicit names)"}
    if view is not None:  # v6.7: the registered secondary view (its own pinned comparator; the primary is untouched)
        c = ((ent or {}).get("corroboration_views") or {}).get(view)
        if c is None:
            raise SystemExit("no '%s' view is pinned for this cell (register 1.6, v6.7)" % view)
    thr = spec["source1_lists"]["corroboration"]["threshold"]
    mode = c.get("mode")
    if mode == "none":
        return False, {"mode": mode, "why": c.get("why", "")}
    try:  # v6.7 N3: the pinned universe and HGNC table, asserted and recorded here; any failure -> the else branch
        hg, uni, env, _ = _corr_env(spec)
    except Exception as e:  # noqa: BLE001
        return False, {"mode": mode, "why": "comparator refused: the pinned universe / HGNC table could not be used (%s)"
                       % _env_err(e)}
    if mode == "printed_size":  # v6.6 C1: distinct approved HGNC symbols, not rows
        appr = {hg.symbol(g)[0] for g in genes} - {None}
        return len(appr) == c["printed_size"], {"mode": mode, "n_rows": len(genes), "n_distinct_approved": len(appr),
                                                "printed_size": c["printed_size"], "env": env}
    if mode == "external":
        mem, why, used = _load_pinned(c, spec)
    elif mode == "kegg_family_recipe":
        mem, why, used = _kegg_recipe(c, name, rivals, hg)
    else:
        return False, {"mode": mode, "why": "comparator refused: unknown corroboration mode"}
    if mem is None:
        return False, {"mode": mode, "why": why, "used": used, "env": env}
    if c.get("class") not in uni:
        return False, {"mode": mode, "why": "comparator refused: no class universe %s" % c.get("class"), "used": used, "env": env}
    u = uni[c["class"]]
    a = {hg.symbol(g)[0] for g in genes} - {None}
    a, b = a & u, set(mem) & u
    j = len(a & b) / len(a | b) if (a | b) else 0.0
    return j >= thr, {"mode": mode, "set_id": c.get("set_id"), "class": c["class"], "used": used, "n_list_in_universe": len(a),
                      "n_external_in_universe": len(b), "n_both": len(a & b), "jaccard": round(j, 4), "threshold": thr,
                      "env": env}


def _phrase_rx(ph: str):
    """a phrase of a name alternative, matched as whole words (v6.2)."""
    return re.compile(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(_tx(ph)))


def _alts_in(t_norm: str, alternatives) -> list:
    """the alternatives every phrase of which appears (whole words) in an already normalised heading."""
    return [alt for alt in (alternatives or []) if all(_phrase_rx(ph).search(t_norm) for ph in alt)]


def _alt_text(alt) -> str:
    return " ".join(_tx(ph) for ph in alt)


def _rival_wins(t: str, mine: list, rivals) -> bool:
    """v6.2 P2 / v6.3 O6: a heading that also names a rival (another registered set of the target, or a rival name) whose name
    holds every phrase of the matched alternative and is longer names the rival."""
    for other in rivals:
        for a in _alts_in(t, other):
            at = _alt_text(a)
            if any(len(at) > len(_alt_text(m)) and all(_phrase_rx(ph).search(at) for ph in m) for m in mine):
                return True
    return False


def _names_set(text: str, alternatives, rivals=()) -> bool:
    t = _tx(text)
    mine = _alts_in(t, alternatives)
    return bool(mine) and not _rival_wins(t, mine, rivals)


def _names_split(own: str, caption: str, alternatives, rivals=(), caption_phrases=()) -> bool:
    """v6.3 (O3's plant ZH1), limited by v6.4 N2: the list's own title and the caption together name the set -- every phrase of one
    alternative in the two, at least one of them in the own title, and every phrase the own title lacks one of the family's
    caption_phrases (the Zhang cells: 'zhang', 'top 500'). Without caption_phrases, never."""
    if not caption_phrases:
        return False
    allowed = {_tx(ph) for ph in caption_phrases}
    t_own, t = _tx(own), _tx(own + " | " + caption)
    mine = [a for a in _alts_in(t, alternatives)
            if any(_phrase_rx(ph).search(t_own) for ph in a)
            and all(_phrase_rx(ph).search(t_own) or _tx(ph) in allowed for ph in a)]
    return bool(mine) and not _rival_wins(t, mine, rivals)


def _strip_names(text: str, alternatives, printed_size=None) -> str:
    """v6.3 O3: the heading (as read) with every phrase of the cell's own alternatives removed wherever it appears, and 'top N'
    removed where N is the cell's printed size (a set's own name and size are not result words)."""
    t = _tx(text)
    for alt in alternatives or []:
        for ph in alt:
            t = _phrase_rx(ph).sub(" ", t)
    if printed_size:
        t = re.sub(r"(?<![a-z])top\s*%d(?![0-9])" % int(printed_size), " ", t)
    return t


def source1_names(spec: dict, cell: str | None, names=None, rival_only=None):
    """v6.2 P2: a cell's target, name alternatives and printed size from the spec (source1_lists.cells). v6.3 O4: a family cell whose
    names come from the gated table takes exactly one name per run (one pathway; the printed name as one phrase, a printed
    '[ _]Homo sapiens[ _]hsaNNNNN' suffix split off); several names for one run are refused, so no alternative accumulates across
    pathways; --name is refused for any other cell."""
    s1 = spec["source1_lists"]
    if cell is None:
        return None, names, None
    ent = s1["cells"][cell]  # KeyError: the cell has no source-1 entry
    alts = ent["names"]
    if rival_only and alts is not None:
        raise SystemExit("%s: --rival is only for a family cell whose names come from the gated table (v6.4 N4)" % cell)
    if alts is None:
        if not names:
            raise SystemExit("%s: the name comes from the gated table (%s); pass it with --name" % (cell, ent["names_from_carrier"]))
        if len(names) != 1 or len(names[0]) != 1:
            raise SystemExit("%s: one source-1 run per pathway with exactly one --name (%d names given; v6.3 O4)"
                             % (cell, sum(len(a) for a in names)))
        m = re.match(s1["kegg_suffix"], names[0][0])
        alts = [[(m.group(1) if m else names[0][0]).strip()]]
    elif names:
        raise SystemExit("%s: --name is only for a family cell whose names come from the gated table" % cell)
    return ent["target"], alts, ent.get("printed_size")


def run_source1(carriers, alternatives=None, printed_size=None, spec=None, cell=None, rival_only=None, view=None):
    """register v6.1 Q1 as revised by v6.2 P1 / P2 / P6, v6.3 O1-O4 / O6 and v6.4 N1-N4: does the carrier hold exactly one list it
    presents as the set's input membership? Returns the result ('qualifies' / 'else branch'), a reason code and counts only.
    rival_only (v6.4 N4, family cells): the gated table's other printed pathway names, rivals only (never alternatives).
    v6.6 B1: no comparator is taken from outside -- the cell's pinned set (register_sets) or the KEGG family recipe. The text
    criterion is the first filter (text_result); the result is 'qualifies' only if the admitted list is corroborated."""
    spec = spec or json.loads(SPEC.read_text(encoding="utf-8"))
    PDF_PIN["version"] = (spec.get("pdf_adapter") or {}).get("version")
    s1 = spec["source1_lists"]
    raw_alt = alternatives  # v6.6 B1: the printed --name (a family run), before the suffix is split off
    target, alternatives, spec_size = source1_names(spec, cell, alternatives, rival_only)
    ent = (s1.get("cells") or {}).get(cell, {}) if cell else {}
    fam = (s1.get("families") or {}).get(ent.get("family")) if ent.get("family") else None
    caption_phrases = fam["caption_phrases"] if fam else ()
    own_title_only = bool(ent.get("own_title_only"))
    na_like = {x.upper() for x in s1.get("na_like", [])}
    rival_extra = []
    for nm in rival_only or []:  # v6.4 N4: the suffix split off as for --name
        mm = re.match(s1["kegg_suffix"], nm)
        rival_extra.append([(mm.group(1) if mm else nm).strip()])
    if cell is not None and printed_size is None:
        printed_size = spec_size
    rm, st = re.compile(s1["result_markers"], re.I), re.compile(s1["statistics_headers"], re.I)
    inp = re.compile(s1["input_markers"], re.I)
    maps = re.compile("|".join("(?:%s)" % s1["map_names"][k] for k in ("general", target) if k in s1["map_names"]), re.I)
    sym = re.compile(s1["symbol_pattern"])
    generic = {" ".join(x.upper().split()) for x in s1.get("generic_titles", [])}
    cells_spec = s1.get("cells") or {}
    extra = (s1.get("rival_names") or {}).get(target, []) if target else []
    registered = ({_alt_text(a) for e in cells_spec.values() for a in (e.get("names") or [])} | {_alt_text(a) for a in alternatives}
                  | {_alt_text(a) for a in extra})
    rivals = []  # the other registered sets of the same target and its rival names (v6.2 P2, v6.3 O6: the more specific name wins)
    if target is not None:
        seen = {json.dumps(alternatives)}
        for e in cells_spec.values():
            if e.get("target") == target and e.get("names") and json.dumps(e["names"]) not in seen:
                seen.add(json.dumps(e["names"]))
                rivals.append(e["names"])
        rivals.extend([a] for a in extra)
        rivals.extend([a] for a in rival_extra)
    registered |= {_alt_text(a) for a in rival_extra}
    # v6.4 N1: the phrases removed before the sheet-level scan -- the cell's own, and for a family every family cell's
    strip_alts = list(alternatives)
    if fam:
        for c in fam["cells"]:
            strip_alts += [a for a in (cells_spec.get(c, {}).get("names") or []) if a not in strip_alts]

    wt = [re.compile(v, re.I) for k, v in (s1.get("whole_tokens") or {}).items() if k not in ("note", "pieces_excepted")]
    excepted = set((s1.get("whole_tokens") or {}).get("pieces_excepted", []))
    wc = [re.compile(v, re.I) for k, v in (s1.get("whole_cells") or {}).items() if k != "note"]  # v6.6 C6
    try:  # v6.6 C2; v6.7 N3: the pinned HGNC table (and universe) -- a read / parse / pin mismatch -> the else branch, recorded
        hgnc_all = _hgnc_all(spec) if s1.get("hgnc_symbols_note") else set()
    except Exception as e:  # noqa: BLE001
        why = "the pinned universe / HGNC table could not be used (%s)" % _env_err(e)
        return {"cell": cell, "target": target, "n_candidates": 0, "n_refused": 0, "n_qualifying_distinct": 0, "refused_reasons": [],
                "log": {}, "text_result": "else branch", "text_reason": why, "result": "else branch", "reason": why,
                "corroboration": {"why": "comparator refused: " + why}}

    def whole(t: str) -> bool:
        return any(r.fullmatch(t) for r in wt)

    def wcell(t: str) -> bool:
        """v6.6 C6: the WHOLE cell, as read, is a registered statistics cell ('t value', 'OR (95% CI)')."""
        t = " ".join(str(t).split())
        return bool(t) and any(r.fullmatch(t) for r in wc)

    def marker_word(v) -> bool:
        """v6.4 N1 (2) as refined: the WHOLE token, as read, equals a registered statistics header, result marker or map name
        (whole_tokens; fullmatch) -- not a substring or prefix, so P2RY12, S100P or a pseudogene '...P1' stay data; v6.5 M3: a
        token that is not gene-symbol-shaped is also split into pieces, each matched the same way."""
        raw = cell_str(v)
        t = _tx(raw).strip()
        if whole(t) or wcell(t):
            return True
        if sym.match(raw) or raw in hgnc_all:  # v6.6 C2: an HGNC symbol is never split into pieces
            return False
        return any(pc not in excepted and whole(pc) for pc in _pieces(raw))

    def wording(t: str, raw: str = "") -> bool:
        """v6.4 N1: a cell as the sheet-level scan reads it -- one token: the whole-token registry (v6.5 M3: and its pieces);
        several words: the phrases."""
        t = t.strip()
        if not t:
            return False
        if wcell(t):  # v6.6 C6
            return True
        if not re.search(r"\s", t):
            if whole(t):
                return True
            return (bool(raw) and not sym.match(raw) and raw not in hgnc_all  # v6.6 C2
                    and any(pc not in excepted and whole(pc) for pc in _pieces(raw)))
        return bool(st.search(t) or rm.search(t) or maps.search(t))

    def is_list_cell(v) -> bool:
        s = cell_str(v)
        if not s or _tx(s) in registered:  # P6: an upper-case title equal to a registered set name is a title, not data
            return False
        if s.upper() in na_like or " ".join(s.upper().split()) in generic:  # 'N/A'; v6.5 M1 / v6.6 C3: 'GENES', 'SYMBOL' ...
            return False                                                     # are titles, checked before the symbol test
        if sym.match(s):
            # v6.4 N1 (2): NA / NS / ND / NAN and marker-shaped tokens (NES, FDR, P, PLS1, SG1, CORE, TOP1 ...) are never data
            return not marker_word(s)
        parts = [x for x in re.split(r"[;,/\s]+", s) if x]
        if not (len(parts) >= 2 and all(sym.match(x) for x in parts)):
            return False
        if not re.search(r"[;,/]", s):  # v6.5 M1: words separated by spaces only -- an all-capitals heading is not a gene list
            if any(x.upper() in na_like or marker_word(x) for x in parts):
                return False
            t = _tx(s)
            if st.search(t) or rm.search(t) or maps.search(t):
                return False
        return True

    def spaced(v) -> bool:
        c_ = cell_str(v)
        return bool(c_) and not sym.match(c_) and not re.search(r"[;,/]", c_)

    def first_data(rows, j):
        """v6.3: a column's first list cell that is followed (next filled cell below) by another list cell or by nothing -- a
        symbol-shaped header over numbers ('NES', 'FDR', 'PLS1') is a title."""
        for i in range(len(rows)):
            if not is_list_cell(rows[i][j]):
                continue
            nxt = next((rows[k][j] for k in range(i + 1, len(rows)) if cell_str(rows[k][j])), None)
            if spaced(rows[i][j]) and nxt is not None and sym.match(cell_str(nxt)):
                continue  # v6.5 M1: words over a column of single symbols are that column's title
            if nxt is None or is_list_cell(nxt):
                return i
        return None

    def refusal(own_parts, caption_parts, table_titles):
        """P6 / v6.3 O1-O3: result wording and map names in the list's own title or the caption; statistics wording there or in any
        column title of its table (O1 (a)); input wording in the caption or the list's own forward-filled title (O2); the cell's
        own phrases, and 'top N' with N = its printed size, removed first (O3)."""
        near = [_strip_names(p, alternatives, printed_size) for p in own_parts + caption_parts if p]
        if any(rm.search(p) for p in near):
            return "result list (result wording)"
        if any(st.search(p) for p in near + [_strip_names(p, alternatives, printed_size) for p in table_titles if p]):
            return "result list (statistics wording)"
        if any(wcell(_tx(p)) for p in own_parts + caption_parts + table_titles if p):  # v6.6 C6
            return "result list (statistics wording)"
        if any(maps.search(p) for p in near):
            return "result list (the heading names a map, subgroup or cohort)"
        if not any(inp.search(_tx(p)) for p in caption_parts + own_parts if p):
            return "not presented as input (no input wording in the caption or the list's own title)"
        return None

    tables, log = load_tables(carriers)
    tables = [t for t in tables if not t.get("text_only")]
    cands = []  # (genes tuple, refused reason or None, heading for a size)
    for t in tables:
        rows = t["rows"]
        if not rows:
            continue
        ncol = len(rows[0])
        first = [first_data(rows, j) for j in range(ncol)]
        starts = [x for x in first if x is not None]
        if not starts:
            continue
        t_first = min(starts)
        filled_cols = sum(1 for j in range(ncol) if any(cell_str(r[j]) for r in rows))
        # title rows: above the table's first data row, exactly one filled cell (a table of >= 2 filled columns); in a one-column
        # table every filled row above the data is both the table's title and the column's own title
        title_rows = [i for i in range(t_first) if sum(1 for v in rows[i] if cell_str(v)) == 1]
        own_skip = set(title_rows) if filled_cols >= 2 else set()
        # the carrier's own names only (a sheet name, a csv / txt file name); the adapter's labels ('#table1', '#p1_t1') are not
        caption_parts = [str(t.get("title") or ""), str(t.get("caption") or "")] + \
                        [next(cell_str(v) for v in rows[i] if cell_str(v)) for i in title_rows]
        caption = " | ".join(p for p in caption_parts if p)
        # v6.3 O1 (a): the table's column titles = the cells of its header rows above its first data row
        table_titles = [cell_str(v) for i in range(t_first) if i not in own_skip for v in rows[i]
                        if cell_str(v) and parse_num(v) is None]
        # v6.4 N1 (1): the sheet-level scan -- every cell of the sheet / table except the lists' own gene runs, and the caption
        data_cells = set()
        for j in range(ncol):
            if first[j] is None:
                continue
            for i in range(first[j], len(rows)):
                c_ = cell_str(rows[i][j])
                if c_ and (sym.match(c_) or is_list_cell(c_)):
                    data_cells.add((i, j))
        for i, r in enumerate(rows):
            for j, v in enumerate(r):
                if is_list_cell(v) and not sym.match(cell_str(v)):  # delimited lists anywhere
                    data_cells.add((i, j))
        scan = [cell_str(v) for i, r in enumerate(rows) for j, v in enumerate(r)
                if (i, j) not in data_cells and cell_str(v) and parse_num(v) is None] + [p for p in caption_parts[:2] if p]
        sheet_hit = None
        for part in scan:
            t_ = _strip_names(part, strip_alts, printed_size)
            if wording(t_, part):
                sheet_hit = "result list (statistics, result or map wording on the sheet)"
                break

        def own_title(j):
            parts = []
            for i in range(first[j] if first[j] is not None else len(rows)):
                if i in own_skip:
                    continue
                last, val = None, ""
                for jj, v in enumerate(rows[i]):  # forward-fill a header row horizontally (merged header cells)
                    s = cell_str(v)
                    last = s or last
                    if jj == j:
                        val = s or (last or "")
                        break
                if val and parse_num(val) is None:
                    parts.append(val)
            return parts
        titles = {j: own_title(j) for j in range(ncol)}
        n_titled = sum(1 for j in range(ncol) if titles[j])
        for j in range(ncol):  # (A) a column of gene symbols
            if first[j] is None:
                continue
            col = [cell_str(r[j]) for r in rows[first[j]:] if cell_str(r[j]) and cell_str(r[j]).upper() not in na_like]
            own = " | ".join(titles[j])
            named = (_names_set(own, alternatives, rivals)
                     or (not own_title_only and _names_split(own, caption, alternatives, rivals, caption_phrases))
                     or (not own_title_only and n_titled <= 2 and _names_set(caption, alternatives, rivals)))
            if not all(sym.match(c) for c in col):
                if any(sym.match(c) for c in col) and named:
                    cands.append(((), "not a list of gene symbols", ""))
                continue
            if not named:
                continue
            cands.append((tuple(col), refusal(titles[j], caption_parts, table_titles) or sheet_hit, own + " | " + caption))
        for i, r in enumerate(rows):  # (B) a delimited list in a row whose first cell names the set
            cells = [cell_str(v) for v in r]
            if not cells or not _names_set(cells[0], alternatives, rivals):
                continue
            for j, c in enumerate(cells[1:], start=1):
                if not is_list_cell(c):
                    continue
                parts = [x for x in re.split(r"[;,/\s]+", c) if x and x.upper() not in na_like]
                if len(parts) >= 2 and all(sym.match(x) for x in parts):
                    cands.append((tuple(parts), refusal([cells[0]] + titles[j], caption_parts, table_titles) or sheet_hit,
                                  cells[0] + " | " + " | ".join(titles[j]) + " | " + caption))
    qual = {}
    for genes, reason, heading in cands:
        if reason is None:
            qual.setdefault(genes, heading)
    out = {"cell": cell, "target": target, "n_candidates": len(cands), "n_refused": sum(1 for c in cands if c[1]),
           "n_qualifying_distinct": len(qual), "refused_reasons": sorted({c[1] for c in cands if c[1]}), "log": log}
    if not qual:
        why = "no qualifying list" + (" (refused: %s)" % "; ".join(out["refused_reasons"]) if out["refused_reasons"] else "")
        out.update(text_result="else branch", text_reason=why, result="else branch", reason=why)
        return out
    if len(qual) > 1:
        why = "two or more distinct qualifying lists (ambiguous)"
        out.update(text_result="else branch", text_reason=why, result="else branch", reason=why)
        return out
    genes, heading = next(iter(qual.items()))
    out["n_genes"] = len(genes)
    out.update(text_result="qualifies", text_reason="ok")
    ok, rec = corroborate(genes, ent, spec, (raw_alt[0][0] if ent.get("names") is None and raw_alt else None),
                          rival_only, view)  # v6.5 (1), v6.6 B1: the family recipe takes the run's printed --name and --rival
    # names; v6.7: view = the registered secondary view (None: the primary)
    out["corroboration"] = rec
    if ok:
        out.update(result="qualifies", reason="ok (corroborated: %s)" % rec["mode"])
    elif rec["mode"] == "printed_size":
        out.update(result="else branch", reason="source 1 uncorroborated (size mismatch: the list's length differs from the printed "
                                                "size)")
    elif rec["mode"] == "none":
        out.update(result="else branch", reason="source 1 uncorroborated (mode none -- %s)" % rec.get("why", ""))
    elif "jaccard" in rec:
        out.update(result="else branch", reason="source 1 uncorroborated (Jaccard %.4f < %.2f with the pinned comparator)"
                   % (rec["jaccard"], rec["threshold"]))
    else:
        out.update(result="else branch", reason="source 1 uncorroborated (%s)" % rec["why"])
    return out


# --------------------------------------------------------------------------------------------------------- selftest
def _xlsx(path: Path, sheets: dict, merges=None):
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(name)
        for r in rows:
            ws.append(r)
        for rng in (merges or {}).get(name, []):  # v6.3: a merged super-header
            ws.merge_cells(rng)
    wb.save(path)


def _csv(path: Path, rows):
    import csv
    with open(path, "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(rows)


SELFTEST_RUN_STAMP = "run"  # register v6.3 O7: the workdir record's run stamp (time, workdir); never in the frozen record


def _diff_paths(a, b, path="", out=None) -> list:
    """key paths where two JSON values differ (paths only)."""
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        if sorted(a) != sorted(b):
            out.append((path or "/") + " (keys)")
        for k in a:
            if k in b:
                _diff_paths(a[k], b[k], "%s/%s" % (path, k), out)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append("%s (length %d vs %d)" % (path, len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            _diff_paths(x, y, "%s[%d]" % (path, i), out)
    elif a != b or type(a) is not type(b):
        out.append(path)
    return out


def _docx(path: Path, rows, caption="Table S1"):
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    esc = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")  # noqa: E731
    trs = "".join("<w:tr>%s</w:tr>" % "".join("<w:tc><w:p><w:r><w:t>%s</w:t></w:r></w:p></w:tc>" % esc(c) for c in r) for r in rows)
    xml = '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="%s"><w:body><w:p><w:r><w:t>%s</w:t></w:r></w:p><w:tbl>%s</w:tbl></w:body></w:document>' % (w, esc(caption), trs)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", xml)


def _pdf(path: Path, rows, page_text=None, per_page=40, caption=None):
    """register v6.1 Q8: a synthetic PDF with a ruled table split over pages (matplotlib, vector text)."""
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(path) as pdf:
        for start in range(0, len(rows), per_page):
            fig, ax = plt.subplots(figsize=(8.27, 11.69))
            ax.axis("off")
            ncol = len(rows[0])
            widths = [0.62] + [0.38 / (ncol - 1)] * (ncol - 1) if ncol > 1 else [1.0]  # the label column wide enough
            tab = ax.table(cellText=[[("" if v is None else str(v)) for v in r] for r in rows[start:start + per_page]],
                           loc="upper center", cellLoc="left", colWidths=widths)
            tab.auto_set_font_size(False)
            tab.set_fontsize(7)
            if page_text:
                fig.text(0.08, 0.02, page_text)
            if caption and start == 0:  # register v6.2 P1: a caption line above the table (first page only)
                fig.text(0.08, 0.93, caption)
            pdf.savefig(fig)
            plt.close(fig)


def _ipynb(path: Path, rows):
    h = "<table>" + "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows) + "</table>"
    nb = {"cells": [{"cell_type": "code", "outputs": [{"output_type": "execute_result", "data": {"text/html": [h]}}]}],
          "nbformat": 4, "nbformat_minor": 5, "metadata": {}}
    path.write_text(json.dumps(nb), encoding="utf-8")


def _ver(pkg: str):
    from importlib import metadata
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return None


def selftest(workdir: Path, overwrite_frozen: bool = False) -> int:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    PDF_PIN["version"] = (spec.get("pdf_adapter") or {}).get("version")
    rng = random.Random(20260926)
    g = lambda: round(rng.gauss(0, 1), 6)  # noqa: E731  synthetic values only
    workdir.mkdir(parents=True, exist_ok=True)
    cases = []  # (target, case, variant, files, expected {map_id: 'pass'|'fail'}, expected reason substrings)

    # ---- Rasero: DK names, FreeSurfer style, 82 regions
    ra = spec["targets"]["rasero2023neurogenetics"]
    det = ra["labels_detail"]
    fs = lambda d, h: ("ctx-%sh-%s" % (h.lower(), d["name"]) if d["structure"] == "cortex" else  # noqa: E731
                       "%s-%s" % ("Left" if h == "L" else "Right",
                                  {"thalamusproper": "Thalamus-Proper", "accumbensarea": "Accumbens-area"}.get(d["name"], d["name"].capitalize())))
    names82 = [fs(d, h) for h in ("L", "R") for d in det]
    base = [["Region", "Subtype 1 pseudo-R2", "Subtype 1 p (FDR)", "Subtype 2 pseudo-R2", "Subtype 2 p (FDR)"]] + \
           [[n, g(), abs(g()), g(), abs(g())] for n in names82]
    f = workdir / "ra_pass.xlsx"; _xlsx(f, {"MDMR": base})
    cases.append(("rasero2023neurogenetics", "planted pass (xlsx, FreeSurfer names, dk41)", "dk41", [f], {"y_S1": "pass", "y_S2": "pass"}, {}))
    rows_nb = [["", "S1 R2", "S2 R2"]] + [["lh_" + d["name"] if d["structure"] == "cortex" else "Left-" + d["name"], g(), g()]
                                          for d in det if d["structure"] == "cortex"]
    f = workdir / "ra_pass.ipynb"; _ipynb(f, rows_nb)
    cases.append(("rasero2023neurogenetics", "planted pass (ipynb output table, lh_ names, dk34)", "dk34", [f], {"y_S1": "pass", "y_S2": "pass"}, {}))
    miss = [r for r in base if r[0] != "ctx-lh-insula"]
    f = workdir / "ra_fail_missing.xlsx"; _xlsx(f, {"MDMR": miss})
    cases.append(("rasero2023neurogenetics", "planted fail: one required label absent", "dk34", [f], {"y_S1": "fail", "y_S2": "fail"},
                  {"y_S1": "labels missing", "y_S2": "labels missing"}))
    nn = [list(r) for r in base]; nn[5][3] = "n.s."
    f = workdir / "ra_fail_nonnum.xlsx"; _xlsx(f, {"MDMR": nn})
    cases.append(("rasero2023neurogenetics", "planted fail: one non-numeric value (y_S2)", "dk41", [f], {"y_S1": "pass", "y_S2": "fail"},
                  {"y_S2": "non-numeric"}))
    amb = [r + [g()] for r in base]; amb[0][-1] = "Subtype 2 pseudo-R2 (replication)"
    f = workdir / "ra_fail_amb.xlsx"; _xlsx(f, {"MDMR": amb})
    cases.append(("rasero2023neurogenetics", "planted fail: two different y_S2 columns", "dk41", [f], {"y_S1": "pass", "y_S2": "fail"},
                  {"y_S2": "ambiguous"}))
    unl = [base[0]] + [[re.sub(r"^(ctx-[lr]h-|Left-|Right-)", "", r[0])] + r[1:] for r in base[1:42]]
    f = workdir / "ra_fail_unlat.xlsx"; _xlsx(f, {"MDMR": unl})
    cases.append(("rasero2023neurogenetics", "planted fail: names without hemisphere", "dk34", [f], {"y_S1": "fail", "y_S2": "fail"},
                  {"y_S1": "no labelled table", "y_S2": "no labelled table"}))

    # ---- Buch: Power ROIs with coordinates
    bu = spec["targets"]["buch2023asdsubgroups"]
    pw = bu["labels_detail"]
    hdr = ["ROI", "X", "Y", "Z"] + ["Subgroup %d net atypical connectivity" % k for k in (1, 2, 3, 4)] + ["Subgroup 1 p"]
    rows = [hdr] + [[d["roi"]] + d["mni_xyz"] + [g() for _ in range(5)] for d in pw[:240]]
    rows += [[265 + k, 0.0, 0.0, 90.0 + 5 * k] + [g() for _ in range(5)] for k in range(7)]  # 7 extra ROIs (Buch's 277 > 264)
    for r in rows[1:11]:
        r[4:8] = [None, None, None, None]  # 10 ROIs without AHBA coverage
    f = workdir / "bu_pass.xlsx"; _xlsx(f, {"Supplementary Table 4": rows})
    cases.append(("buch2023asdsubgroups", "planted pass (237 usable ROIs, 7 extra, 10 empty)", None, [f],
                  {"y_%d" % k: "pass" for k in (1, 2, 3, 4)}, {}))
    few = [list(r) for r in rows]
    for r in few[11:19]:
        r[5] = None  # subgroup 2 loses 8 more ROIs -> 229
    f = workdir / "bu_fail_count.xlsx"; _xlsx(f, {"Supplementary Table 4": few})
    cases.append(("buch2023asdsubgroups", "planted fail: subgroup 2 has 229 usable ROIs", None, [f],
                  {"y_1": "pass", "y_2": "fail", "y_3": "pass", "y_4": "pass"}, {"y_2": "count below required"}))
    noc = [[r[0]] + r[4:] for r in rows]
    f = workdir / "bu_fail_nocoord.xlsx"; _xlsx(f, {"Supplementary Table 4": noc})
    cases.append(("buch2023asdsubgroups", "planted fail: no ROI coordinates", None, [f], {"y_%d" % k: "fail" for k in (1, 2, 3, 4)},
                  {"y_%d" % k: "coordinates missing" for k in (1, 2, 3, 4)}))
    noid = [r[1:] for r in rows]  # register v5 1.11 item 8: coordinates and values, no ROI id column
    f = workdir / "bu_pass_noid.xlsx"; _xlsx(f, {"Supplementary Table 4": noid})
    cases.append(("buch2023asdsubgroups", "planted pass: coordinates without ROI ids (237 usable ROIs)", None, [f],
                  {"y_%d" % k: "pass" for k in (1, 2, 3, 4)}, {}))

    # ---- Mamat: Schaefer-400 names, one sheet per cohort (tier 3: sheet name)
    ma = spec["targets"]["mamat2025molecular"]
    sn = [d["name"] for d in ma["labels_detail"]]
    s1 = [["Parcel", "t value"]] + [[n, g()] for n in sn]
    s2 = [["Parcel", "t value"]] + [[n.replace("17Networks_", ""), g()] for n in sn]
    f = workdir / "ma_pass.xlsx"; _xlsx(f, {"ABIDE I": s1, "ABIDE II": s2})
    cases.append(("mamat2025molecular", "planted pass (sheet-named cohorts; prefixed / unprefixed names)", None, [f],
                  {"ABIDE I FD t-map": "pass", "ABIDE II FD t-map": "pass"}, {}))
    f = workdir / "ma_fail_399.xlsx"; _xlsx(f, {"ABIDE I": s1, "ABIDE II": s2[:-1]})
    cases.append(("mamat2025molecular", "planted fail: ABIDE II map with 399 parcels", None, [f],
                  {"ABIDE I FD t-map": "pass", "ABIDE II FD t-map": "fail"}, {"ABIDE II FD t-map": "labels missing"}))
    # register v5 1.11 item 8 as revised by v6 R9: parcels by name, OR by index 1 ... 400 only where the carrier names the
    # 17-network order file
    idx = [["Parcel", "ABIDE I t", "ABIDE II t"]] + [[i + 1, g(), g()] for i in range(400)]
    readme17 = [["Parcel order: Schaefer2018_400Parcels_17Networks_order.txt (CBIG)"]]
    readme7 = [["Parcel order: Schaefer2018_400Parcels_7Networks_order.txt (CBIG)"]]
    f = workdir / "ma_pass_index.xlsx"; _xlsx(f, {"Sheet1": idx, "README": readme17})
    cases.append(("mamat2025molecular", "planted pass: parcel indices 1 ... 400; the carrier names the 17-network order file (R9)",
                  None, [f], {"ABIDE I FD t-map": "pass", "ABIDE II FD t-map": "pass"}, {}))
    f = workdir / "ma_fail_index399.xlsx"; _xlsx(f, {"Sheet1": idx[:-1], "README": readme17})
    cases.append(("mamat2025molecular", "planted fail: parcel indices 1 ... 399 (a 399-index table; 17-network order named)", None,
                  [f], {"ABIDE I FD t-map": "fail", "ABIDE II FD t-map": "fail"},
                  {"ABIDE I FD t-map": "labels missing", "ABIDE II FD t-map": "labels missing"}))
    f = workdir / "ma_fail_index_noorder.xlsx"; _xlsx(f, {"Sheet1": idx})
    cases.append(("mamat2025molecular", "planted fail: parcel indices 1 ... 400; the carrier names no order file (R9)", None, [f],
                  {"ABIDE I FD t-map": "fail", "ABIDE II FD t-map": "fail"},
                  {"ABIDE I FD t-map": "no order file named", "ABIDE II FD t-map": "no order file named"}))
    f = workdir / "ma_fail_index_7net.xlsx"; _xlsx(f, {"Sheet1": idx, "README": readme7})
    cases.append(("mamat2025molecular", "planted fail: parcel indices 1 ... 400; the carrier names the 7-network order file (R9)",
                  None, [f], {"ABIDE I FD t-map": "fail", "ABIDE II FD t-map": "fail"},
                  {"ABIDE I FD t-map": "another order file named", "ABIDE II FD t-map": "another order file named"}))

    # ---- Romero-Garcia: DK-308 names in docx tables; near-duplicate carriers merge
    rgt = spec["targets"]["romerogarcia2019synaptic"]
    rn = ["%sh_%s" % (d["hemisphere"].lower(), d["name"]) for d in rgt["labels_detail"]]
    tab = [["Region", "Discovery ΔCT", "Validation 1 ΔCT", "Validation 2 ΔCT"]] + [[n, g(), g(), g()] for n in rn]
    f1, f2 = workdir / "rg_MOESM1.docx", workdir / "rg_MOESM2.docx"
    _docx(f1, tab); _docx(f2, tab)
    cases.append(("romerogarcia2019synaptic", "planted pass (two identical docx carriers merge)", None, [f1, f2],
                  {"discovery DeltaCT": "pass", "Validation 1 DeltaCT": "pass", "Validation 2 DeltaCT": "pass"}, {}))
    tab2 = [list(r) for r in tab]; tab2[3][1] = tab2[3][1] + 1.0
    f3 = workdir / "rg_MOESM2_diff.docx"; _docx(f3, tab2)
    cases.append(("romerogarcia2019synaptic", "planted fail: carriers disagree on one discovery value", None, [f1, f3],
                  {"discovery DeltaCT": "fail", "Validation 1 DeltaCT": "pass", "Validation 2 DeltaCT": "pass"},
                  {"discovery DeltaCT": "ambiguous"}))
    # register v5 1.11 item 8: the route needs only the 152 LEFT labels; a left-only carrier qualifies, a missing left label fails
    first_left = next(i for i, n in enumerate(rn, start=1) if n.startswith("lh_"))
    f4 = workdir / "rg_151left.docx"; _docx(f4, tab[:first_left] + tab[first_left + 1:])
    cases.append(("romerogarcia2019synaptic", "planted fail: 151 of the 152 left regions (all 156 right present)", None, [f4],
                  {"discovery DeltaCT": "fail", "Validation 1 DeltaCT": "fail", "Validation 2 DeltaCT": "fail"},
                  {"discovery DeltaCT": "labels missing"}))
    tab_left = [tab[0]] + [r for r in tab[1:] if str(r[0]).startswith("lh_")]
    f5 = workdir / "rg_leftonly.docx"; _docx(f5, tab_left)
    cases.append(("romerogarcia2019synaptic", "planted pass: left-only carrier (the 152 lh labels, no rh rows)", None, [f5],
                  {"discovery DeltaCT": "pass", "Validation 1 DeltaCT": "pass", "Validation 2 DeltaCT": "pass"}, {}))

    # ---- register v6.1 Q8: synthetic-PDF plants (pdfplumber pinned; multi-page tables continue across pages)
    pages_names = [["Parcel", "ABIDE I t", "ABIDE II t"]] + [[n, g(), g()] for n in sn]
    f = workdir / "ma_pass.pdf"; _pdf(f, pages_names)
    cases.append(("mamat2025molecular", "PDF planted pass: 400 named parcels over 11 pages, both cohorts (Q8)", None, [f],
                  {"ABIDE I FD t-map": "pass", "ABIDE II FD t-map": "pass"}, {}))
    f = workdir / "ma_pass_index.pdf"; _pdf(f, idx, page_text="Parcel order: Schaefer2018_400Parcels_17Networks_order.txt")
    cases.append(("mamat2025molecular", "PDF planted pass: indices 1 ... 400; the page text names the 17-network order file (Q8, R9)",
                  None, [f], {"ABIDE I FD t-map": "pass", "ABIDE II FD t-map": "pass"}, {}))
    shifted = [pages_names[0], [sn[0], None, None]] + [[sn[i], pages_names[i][1], pages_names[i][2]] for i in range(1, 400)]
    f = workdir / "ma_fail_misaligned.pdf"; _pdf(f, shifted)
    cases.append(("mamat2025molecular", "PDF planted fail: values misaligned with labels by one row (Q8)", None, [f],
                  {"ABIDE I FD t-map": "fail", "ABIDE II FD t-map": "fail"},
                  {"ABIDE I FD t-map": "non-numeric", "ABIDE II FD t-map": "non-numeric"}))
    rows_pdf = [["Region", "Subtype 1 pseudo-R2", "Subtype 2 pseudo-R2"]] + [["lh_" + d["name"], g(), g()]
                                                                              for d in det if d["structure"] == "cortex"]
    f = workdir / "ra_pass.pdf"; _pdf(f, rows_pdf)
    cases.append(("rasero2023neurogenetics", "PDF planted pass (dk34, one page) (Q8)", "dk34", [f], {"y_S1": "pass", "y_S2": "pass"}, {}))

    n_ok, record = 0, []
    for target, case, variant, files, exp, exp_reason in cases:
        out = run(target, files, variant, spec)
        got = {r["map_id"]: r for r in out["maps"]}
        ok = all(got[m]["result"] == v for m, v in exp.items()) and all(s in got[m]["reason"] for m, s in exp_reason.items())
        n_ok += ok
        print("[%s] %s | %s" % ("CAUGHT" if ok else "MISSED", target, case))
        for r in out["maps"]:
            print("    " + fmt(r))
        record.append({"target": target, "case": case, "variant": variant, "carrier_types": sorted({Path(f).suffix for f in files}),
                       "expected": exp, "expected_reason_contains": exp_reason, "observed": out["maps"], "caught": bool(ok)})
    # ---- register v6.1 Q1 as revised by v6.2 P1 / P2 / P6: source-1 list plants (cell id -> names and printed size from the spec)
    s1_cases = []  # (case, files, cell id or None, explicit alternatives or None, expected result, expected reason substring)
    RIB = "BUCH-E-Trans-StructConstRibosome-S1"  # names [['ribosomal structure']] (Fig. 5h, asterisk dropped)
    genes = ["RPL%d" % k for k in range(3, 43)] + ["RPS%d" % k for k in range(2, 30)]
    f = workdir / "s1_pass_membership.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["Ribosomal structure", "Cytosolic ribosome"]]
              + [[genes[k], genes[k + 1] if k + 1 < len(genes) else None] for k in range(0, 40)]})
    s1_cases.append(("planted pass: a membership list under the set's name in a sheet named as input (by cell id)", [f], RIB, None,
                     "qualifies", "ok"))
    f = workdir / "s1_refuse_no_input_wording.xlsx"
    _xlsx(f, {"Sheet1": [["Ribosomal structure", "Cytosolic ribosome"]]
              + [[genes[k], genes[k + 1] if k + 1 < len(genes) else None] for k in range(0, 40)]})
    s1_cases.append(("planted refusal: the same list, no input wording in the sheet name, title or caption (v6.2 P1)", [f], RIB, None,
                     "else branch", "not presented as input"))
    f = workdir / "s1_refuse_leading_edge_row.xlsx"
    _xlsx(f, {"GSEA": [["Term", "NES", "FDR", "Leading edge genes"],
                       ["Ribosomal structure", 2.8, 0.001, ";".join(genes[:12])],
                       ["Cytosolic ribosome", 2.9, 0.001, ";".join(genes[5:15])]]})
    s1_cases.append(("planted refusal: a leading-edge list in a results-table row under the set's name (Q1)", [f], RIB, None,
                     "else branch", "result list"))
    f = workdir / "s1_refuse_leading_edge_col.xlsx"
    _xlsx(f, {"Gene set definitions": [["Ribosomal structure - leading edge"]] + [[x] for x in genes[:20]]})
    s1_cases.append(("planted refusal: a column titled with the set's name and 'leading edge' (Q1)", [f], RIB, None,
                     "else branch", "result list"))
    f = workdir / "s1_refuse_enrichr_row.xlsx"
    _xlsx(f, {"Enrichr": [["Term", "Overlap", "P-value", "Adjusted P-value", "Genes"],
                          ["Synaptic transmission (GO:0007268)", "12/433", 1e-5, 6e-5, ";".join(genes[:12])]]})
    s1_cases.append(("planted refusal: overlap genes of an enrichment-results row (Q1; v6.3 O1 (a): statistics in its table's column "
                     "titles)", [f], None, [["synaptic transmission"]], "else branch", "result list (statistics wording)"))
    # v6.6 C1: the printed size counts distinct approved HGNC symbols, so the size plants use 500 approved symbols (the first 500
    # symbol-shaped genes of the dk-ctx universe that no registered token equals)
    _uni_all = json.loads((ROOT / "arcs" / "audit" / "register_sets" / "UNIVERSE_GENES.json").read_text(encoding="utf-8"))
    _s1 = spec["source1_lists"]
    _wt = [re.compile(v, re.I) for k, v in _s1["whole_tokens"].items() if k not in ("note", "pieces_excepted")]
    _sym = re.compile(_s1["symbol_pattern"])
    approved_pool = [x for x in sorted(_uni_all["classes"]["dk-ctx"]) if _sym.match(x) and not any(r.fullmatch(_tx(x).strip())
                                                                                                  for r in _wt)]
    neuron = approved_pool[:500]
    f = workdir / "s1_pass_size500.xlsx"
    _xlsx(f, {"Gene set definitions": [["Neuron-specific genes (top 500)"]] + [[x] for x in neuron]})
    s1_cases.append(("planted pass: 500 symbols under 'Neuron-specific genes (top 500)', RG-04's printed size 500 from the spec "
                     "('top' is part of the set's name) (P2)", [f], "RG-04", None, "qualifies", "ok"))
    s1_cases.append(("planted else branch: the same carrier for RG-N05 (oligodendrocyte): no list names the set (P2)", [f], "RG-N05",
                     None, "else branch", "no qualifying list"))
    f = workdir / "s1_size499.xlsx"
    _xlsx(f, {"Gene set definitions": [["Neuron-specific genes (top 500)"]] + [[x] for x in neuron[:499]]})
    s1_cases.append(("planted else branch: 499 symbols against RG-04's printed size 500 (Q1, P2; since v6.5 corroboration (b))", [f],
                     "RG-04", None, "else branch", "size mismatch", {"level": "final"}))
    f = workdir / "s1_ambiguous.xlsx"
    _xlsx(f, {"Gene set definitions A": [["Ribosomal structure genes"]] + [[x] for x in genes[:20]],
              "Gene set definitions B": [["Ribosomal structure genes"]] + [[x] for x in genes[20:40]]})
    s1_cases.append(("planted else branch: two distinct input lists under the set's name", [f], RIB, None, "else branch",
                     "ambiguous"))
    # the reviewer's three plants (v6.2 P1), each to be refused
    f = workdir / "s1_refuse_driving_subgroup.xlsx"
    _xlsx(f, {"Genes driving the enrichment of each gene set (subgroup 1)":
              [["Ribosomal structure", "Cytosolic ribosome"]] + [[genes[k], genes[k + 20]] for k in range(0, 20)]})
    s1_cases.append(("reviewer plant 1: sheet 'Genes driving the enrichment of each gene set (subgroup 1)', one column per set (P1)",
                     [f], RIB, None, "else branch", "result list"))
    f = workdir / "s1_refuse_core_genes.xlsx"
    _xlsx(f, {"Gene set definitions": [["Ribosomal structure core genes", "Cytosolic ribosome"]]
              + [[genes[k], genes[k + 20]] for k in range(0, 20)]})
    s1_cases.append(("reviewer plant 2: a column 'Ribosomal structure core genes' (P1)", [f], RIB, None, "else branch",
                     "result list (result wording)"))
    f = workdir / "s1_refuse_subgroup_sheet.xlsx"
    _xlsx(f, {"Subgroup 1": [["Ribosomal structure"]] + [[x] for x in genes[:25]],
              "GSEA": [["Gene set", "NES", "padj"], ["Ribosomal structure", 2.8, 0.001], ["Cytosolic ribosome", 2.9, 0.001]]})
    s1_cases.append(("reviewer plant 3: sheet 'Subgroup 1' listing the set's genes, the NES / padj table on another sheet (P1)", [f],
                     RIB, None, "else branch", "no qualifying list"))
    # the Pagani layout (v6.2 P6): a result column beside an input column; an upper-case title; a 'Gene set | Genes' table
    f = workdir / "s1_pagani_layout.xlsx"
    _xlsx(f, {"Gene lists used in enrichment": [["Hypo decoded genes", "ASD DE genes", "SYNGO"]]
              + [[genes[k], "D%dGENE" % k, "S%dGENE" % k] for k in range(0, 30)]})
    s1_cases.append(("Pagani layout: 'ASD DE genes' beside 'Hypo decoded genes' -> PAG-C1 refused since v6.4 N1 (decoded / hypo on "
                     "the sheet; P6 had let it qualify)", [f], "PAG-C1", None, "else branch", "result list (statistics, result or map wording on the sheet)"))
    s1_cases.append(("Pagani layout: the upper-case title 'SYNGO' is a title, not data; PAG-C4 refused since v6.4 N1 (the sheet "
                     "holds a decoded list)", [f], "PAG-C4", None, "else branch", "result list (statistics, result or map wording on the sheet)"))
    f = workdir / "s1_pagani_rows.xlsx"
    _xlsx(f, {"Gene set definitions": [["Gene set", "Genes"], ["TGF-beta signaling", "TGFB1;TGFB2;TGFB3;SMAD2;SMAD3;SMAD4"],
                                       ["Cytokine signaling in immune system", "IL6;IL1B;TNF;CXCL8;IL10;IL4"]]})
    s1_cases.append(("Pagani layout: a 'Gene set | Genes' table, the 'TGF-beta signaling' row qualifies ('beta' is part of the name) "
                     "(P6)", [f], None, [["tgf-beta signaling"]], "qualifies", "ok"))
    s1_cases.append(("Pagani layout: the same table, PAG-C7's row qualifies (P2, P6)", [f], "PAG-C7", None, "qualifies", "ok"))
    f = workdir / "s1_docx_caption.docx"
    _docx(f, [["Pathway", "Genes"], ["Ribosome", ";".join(genes[:15])], ["Spliceosome", ";".join(genes[15:30])]],
          caption="Table S2. KEGG pathways: gene sets used in the enrichment analysis")
    s1_cases.append(("docx: a 'Pathway | Genes' table whose caption paragraph carries input wording; the family cell RG-03 with the "
                     "printed name passed (P1, P2)", [f], "RG-03", [["Ribosome"]], "qualifies", "ok"))
    f = workdir / "s1_pdf_caption.pdf"
    _pdf(f, [["Gene set", "Genes"], ["Ribosome", ";".join(genes[:6])], ["Spliceosome", ";".join(genes[6:12])]],
         caption="Supplementary Table S3. Gene sets used in the enrichment analysis")
    s1_cases.append(("PDF: the same table under a caption line with input wording; RG-V06 with the printed name passed (P1, Q8)", [f],
                     "RG-V06", [["Ribosome"]], "qualifies", "ok"))
    f = workdir / "s1_pdf_nocaption.pdf"
    _pdf(f, [["Gene set", "Genes"], ["Ribosome", ";".join(genes[:6])], ["Spliceosome", ";".join(genes[6:12])]],
         caption="Supplementary Table S3. Genes contributing to the PLS component (results)")
    s1_cases.append(("PDF: the same table under a caption naming a PLS result -> refused (P1)", [f], "RG-V06", [["Ribosome"]],
                     "else branch", "result list"))
    # ---- register v6.3 (O1-O4, O6): the reviewer's plants and the new rules' plants
    CST = "BUCH-E-Syn-ChemSynTransmission-S1"  # names [['Chemical synaptic transmission']]
    f = workdir / "s1_gap1_enrichr_export.xlsx"
    _xlsx(f, {"Enrichment of the gene sets tested": [
        ["Term", "Overlap", "P-value", "Adjusted P-value", "Odds Ratio", "Combined Score", "Genes"],
        ["Chemical synaptic transmission (GO:0007268)", "12/433", 1e-5, 6e-5, 3.1, 35.7, ";".join(genes[:12])]]})
    s1_cases.append(("GAP1: an Enrichr export (Term | Overlap | P-value | Adjusted P-value | Odds Ratio | Combined Score | Genes) on a "
                     "sheet 'Enrichment of the gene sets tested' -> refused (v6.3 O1 (a): statistics in the table's column titles)",
                     [f], CST, None, "else branch", "result list (statistics wording)"))
    f = workdir / "s1_gap2_gsea_table.xlsx"
    _xlsx(f, {"Table S5": [["Supplementary Table 5. GSEA of the gene sets used"],
                           ["Gene set", "Subgroup", "NES", "padj", "Genes"],
                           ["Ribosomal structure", 1, 2.8, 0.001, ";".join(genes[:12])],
                           ["Cytosolic ribosome", 1, 2.9, 0.001, ";".join(genes[12:24])]]})
    s1_cases.append(("GAP2: 'Supplementary Table 5. GSEA of the gene sets used', Gene set | Subgroup | NES | padj | Genes -> refused "
                     "(O1 (a); 'NES' over numbers is a title)", [f], RIB, None, "else branch", "result list (statistics wording)"))
    f = workdir / "s1_p1b_clusterprofiler.xlsx"
    _xlsx(f, {"Gene sets tested": [["Description", "NES", "p.adjust", "core_enrichment"],
                                   ["Ribosomal structure", 2.8, 0.001, "/".join(genes[:12])],
                                   ["Cytosolic ribosome", 2.9, 0.001, "/".join(genes[12:24])]]})
    s1_cases.append(("P1b: clusterProfiler Description | NES | p.adjust | core_enrichment under 'Gene sets tested' -> refused (O1 (b): "
                     "'core_enrichment' read as 'core enrichment')", [f], RIB, None, "else branch", "result list"))
    f = workdir / "s1_gap3_pls_caption.xlsx"
    _xlsx(f, {"Sheet1": [["KEGG pathways enriched in the input gene list (PLS1 Z > 3)"], ["Pathway", "Genes"],
                         ["Ribosome", ";".join(genes[:12])], ["Spliceosome", ";".join(genes[12:24])]]})
    s1_cases.append(("GAP3: a table under 'KEGG pathways enriched in the input gene list (PLS1 Z > 3)' -> refused (O1 (b): 'PLS1' "
                     "read; 'enriched' a result word)", [f], "RG-03", [["Ribosome"]], "else branch", "result list (result wording)"))
    f = workdir / "s1_gap4_top_genes.xlsx"
    _xlsx(f, {"Gene set definitions": [["Gene set", "top_genes"], ["Ribosomal structure", ";".join(genes[:12])],
                                       ["Cytosolic ribosome", ";".join(genes[12:24])]]})
    s1_cases.append(("GAP4: a 'top_genes' column -> refused (O1 (b): 'top_genes' read as 'top genes')", [f], RIB, None,
                     "else branch", "result list (result wording)"))
    f = workdir / "s1_o1b_markers.xlsx"
    mk = ["GSEA_results", "SG1", "hit_gene", "urg_list", "pls1 gene", "PLS1"]
    _xlsx(f, {"Gene set definitions": [["Ribosomal structure %s" % m for m in mk]]
              + [[genes[(k + 7 * n) % len(genes)] for n in range(len(mk))] for k in range(20)]})
    s1_cases.append(("O1 (b): six columns 'Ribosomal structure GSEA_results / SG1 / hit_gene / urg_list / pls1 gene / PLS1' -> all six "
                     "refused", [f], RIB, None, "else branch", "no qualifying list", {"n_candidates": 6, "n_refused": 6}))
    f = workdir / "s1_pag1_caption.xlsx"
    _xlsx(f, {"Supplementary Table 3": [["Brain decoded genes and gene lists used in enrichment analyses in humans"],
                                        ["Hypo decoded genes", "ASD DE genes"]]
              + [[genes[k], "D%dGENE" % k] for k in range(30)]})
    s1_cases.append(("PAG1: Table S3's index title as the caption ('decoded genes' beside 'gene lists used') -> PAG-C1 refused (stays "
                     "refused under O2)", [f], "PAG-C1", None, "else branch", "result list (result wording)"))
    f = workdir / "s1_pag3_superheader.xlsx"
    _xlsx(f, {"Supplementary Table 3": [["Hypo decoded genes", None, "Gene lists used in enrichment analyses", None],
                                        ["Hypo", "Hyper", "ASD DE genes", "SYNGO"]]
              + [[genes[k], genes[k + 30], "D%dGENE" % k, "S%dGENE" % k] for k in range(30)]},
          merges={"Supplementary Table 3": ["A1:B1", "C1:D1"]})
    s1_cases.append(("PAG3: a merged super-header 'Gene lists used in enrichment analyses' over the input columns beside decoded "
                     "columns -> PAG-C1 refused since v6.4 N1 (O2 had let it qualify)", [f], "PAG-C1", None, "else branch", "result list (statistics, result or map wording on the sheet)"))
    f = workdir / "s1_zh1_zhang.xlsx"
    classes = ["Neuron", "Astrocyte", "Oligodendrocyte", "Microglia", "Vascular"]
    _xlsx(f, {"Gene sets used in enrichment": [["Top 500 cell-type-specific genes (Zhang 2014)"], classes]
              + [["%s%dZ" % (c[:3].upper(), k) for c in classes] for k in range(500)]})
    for cid, cls in (("RG-04", "neuron"), ("RG-N04", "astrocyte"), ("RG-N05", "oligodendrocyte"), ("RG-N06", "microglia"),
                     ("RG-N07", "vascular")):
        s1_cases.append(("ZH1: 'Top 500 cell-type-specific genes (Zhang 2014)' over one column per class -> %s (%s) qualifies (O3: own "
                         "phrases stripped, 'top 500' = the printed size exempt)" % (cid, cls), [f], cid, None, "qualifies", "ok"))
    RBO = "BUCH-E-Trans-Ribosome-S1"  # names [['Ribosome']]
    f = workdir / "s1_rb1.xlsx"
    _xlsx(f, {"Gene set definitions": [["Structural constituent of ribosome"]] + [[x] for x in genes[:30]]})
    s1_cases.append(("RB1: a list headed 'Structural constituent of ribosome' is not 'Ribosome' (O6: rival name) -> else branch",
                     [f], RBO, None, "else branch", "no qualifying list"))
    f = workdir / "s1_rb2.xlsx"
    _xlsx(f, {"Gene set definitions": [["Ribosome", "Structural constituent of ribosome"]]
              + [[genes[k], genes[k + 30]] for k in range(30)]})
    s1_cases.append(("RB2: 'Ribosome' beside 'Structural constituent of ribosome' -> Ribosome qualifies with its own list only (O6)",
                     [f], RBO, None, "qualifies", "ok"))
    f = workdir / "s1_o4_suffix.xlsx"
    _xlsx(f, {"Gene set definitions": [["Pathway", "Genes"], ["Ribosome Homo sapiens hsa03010", ";".join(genes[:12])],
                                       ["Spliceosome Homo sapiens hsa03040", ";".join(genes[12:24])]]})
    s1_cases.append(("O4: RG-03 run with --name 'Ribosome_Homo_sapiens_hsa03010' (suffix split off) -> qualifies", [f], "RG-03",
                     [["Ribosome_Homo_sapiens_hsa03010"]], "qualifies", "ok"))
    s1_cases.append(("O4: one RG-03 run given two pathway names -> the run is refused (no alternative accumulates across pathways)",
                     [f], "RG-03", [["Ribosome"], ["Spliceosome"]], "run refused", "one source-1 run per pathway"))
    # ---- register v6.4 (N1-N4): the header-zone collapse closed at sheet level; family-limited naming; rival-only names
    SHEET = "result list (statistics, result or map wording on the sheet)"
    two = [["Ribosomal structure", ";".join(genes[:12])], ["Cytosolic ribosome", ";".join(genes[12:24])]]
    for tag, head, val in (("nes_na", "NES", "NA"), ("fdr_ns", "FDR", "NS"), ("p_ns", "P", "NS")):
        f = workdir / ("s1_n1_%s.xlsx" % tag)
        _xlsx(f, {"Gene set definitions": [["Gene set", head, "Genes"]] + [[r[0], val, r[1]] for r in two]})
        s1_cases.append(("N1: '%s' over '%s' beside the gene lists (xlsx) -> refused" % (head, val), [f], RIB, None, "else branch",
                         "result list"))
    f = workdir / "gene_set_definitions.csv"
    _csv(f, [["Gene set", "FDR", "Genes"]] + [[r[0], "NA", r[1]] for r in two])
    s1_cases.append(("N1: 'FDR' over 'NA' (csv named 'gene_set_definitions') -> refused", [f], RIB, None, "else branch", "result list"))
    f = workdir / "s1_n1_fdr_na_slash.docx"
    _docx(f, [["Gene set", "FDR", "Genes"]] + [[r[0], "N/A", r[1]] for r in two], caption="Gene set definitions")
    s1_cases.append(("N1: 'FDR' over 'N/A' (docx under 'Gene set definitions') -> refused", [f], RIB, None, "else branch",
                     "result list"))
    f = workdir / "s1_n1_sg_long.xlsx"
    _xlsx(f, {"Gene set definitions": [["Ribosomal structure", "SG"]] + [[genes[k], "SG%d" % (1 + k % 4)] for k in range(20)]})
    s1_cases.append(("N1: 'SG' over 'SG1' ... (long format: a gene per row with its subgroup) -> refused", [f], RIB, None,
                     "else branch", SHEET))
    f = workdir / "s1_n1_rg_p_fdr.xlsx"
    _xlsx(f, {"Gene set definitions": [["Pathway", "P", "FDR", "Genes"], ["Ribosome", 0.01, "NA", ";".join(genes[:12])],
                                       ["Spliceosome", 0.02, "NA", ";".join(genes[12:24])]]})
    s1_cases.append(("N1: RG-03 'Pathway | P | FDR | Genes' with FDR 'NA' -> refused", [f], "RG-03", [["Ribosome"]], "else branch",
                     "result list"))
    f = workdir / "s1_n1_gs_pls1.xlsx"
    _xlsx(f, {"Gene set definitions": [["Gene set", "PLS1"]] + two})
    s1_cases.append(("N1: 'Gene set | PLS1' -> refused", [f], RIB, None, "else branch", "result list"))
    f = workdir / "s1_n1_gs_sg14.xlsx"
    _xlsx(f, {"Gene set definitions": [["Gene set", "SG1", "SG2", "SG3", "SG4"]]
              + [[r[0]] + [";".join(genes[k * 6:(k + 1) * 6]) for k in range(4)] for r in two]})
    s1_cases.append(("N1: 'Gene set | SG1 ... SG4' -> refused", [f], RIB, None, "else branch", "result list"))
    for tag, tok in (("pls1", "PLS1"), ("core", "CORE")):
        f = workdir / ("s1_n1_name_over_%s.xlsx" % tag)
        _xlsx(f, {"Gene set definitions": [["Ribosomal structure"], [tok]] + [[x] for x in genes[:25]]})
        s1_cases.append(("N1: the set name over '%s' over genes -> refused" % tok, [f], RIB, None, "else branch", "result list"))
    f = workdir / "s1_n1_stacked.xlsx"
    _xlsx(f, {"Gene set definitions": [["Ribosomal structure", "Cytosolic ribosome", None, None, None]]
              + [[genes[k], genes[k + 20], None, None, None] for k in range(20)]
              + [[None] * 5, [None, None, "Term", "NES", "padj"], [None, None, "Ribosomal structure", 2.8, 0.001],
                 [None, None, "Cytosolic ribosome", 2.9, 0.001]]})
    s1_cases.append(("N1: a results table stacked under a neutral list on the same sheet -> refused", [f], RIB, None, "else branch",
                     SHEET))
    # N2: split naming only for the Zhang family; RG-15 / RG-V23 by their own title only (the reviewer's two plants: NOT qualify)
    f = workdir / "s1_n2_rg15_split.xlsx"
    _xlsx(f, {"Gene lists used in enrichment": [["Second list"], ["Genes dysregulated in autism (Parikshak 2016)", "Other genes"]]
              + [[genes[k], genes[k + 30]] for k in range(30)]})
    s1_cases.append(("N2: RG-15 -- 'second' only in the caption, 'dysregulated' in the column title -> not named, no list", [f],
                     "RG-15", None, "else branch", "no qualifying list", {"n_candidates": 0}))
    f = workdir / "s1_n2_rgv23_caption.xlsx"
    _xlsx(f, {"Second dysregulated list (input)": [["Genes"]] + [[x] for x in genes[:30]]})
    s1_cases.append(("N2: RG-V23 -- both phrases only in the sheet name (a one-column 'Genes' list) -> not named, no list", [f],
                     "RG-V23", None, "else branch", "no qualifying list", {"n_candidates": 0}))
    # N3: 'enriched' is part of the Zhang names; 'weighted gene co-expression' is not the 'weight' marker (both must qualify)
    f = workdir / "s1_n3_zhang_enriched.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["%s enriched" % c for c in classes]]
              + [["%s%dE" % (c[:3].upper(), k) for c in classes] for k in range(500)]})
    s1_cases.append(("N3: 'Neuron enriched' beside the other classes' 'X enriched' columns -> RG-04 qualifies", [f], "RG-04", None,
                     "qualifies", "ok"))
    f = workdir / "s1_n3_wgcna.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["Second list of genes dysregulated in autism (weighted gene co-expression network "
                                                "analysis)"]] + [[x] for x in genes[:30]]})
    s1_cases.append(("N3: 'Second list of genes dysregulated in autism (weighted gene co-expression network analysis)' -> RG-15 "
                     "qualifies", [f], "RG-15", None, "qualifies", "ok"))
    f = workdir / "s1_n1_pagani_inputs_only.xlsx"
    _xlsx(f, {"Supplementary Table 3": [["Gene lists used in enrichment analyses", None], ["ASD DE genes", "SYNGO"]]
              + [["D%dGENE" % k, "S%dGENE" % k] for k in range(30)]}, merges={"Supplementary Table 3": ["A1:B1"]})
    s1_cases.append(("N1 / O2: Pagani input lists on a sheet of their own (no decoded list on it) -> PAG-C1 qualifies", [f], "PAG-C1",
                     None, "qualifies", "ok"))
    # N1 (2) refined: a Zhang microglia input list whose first gene is P2RY12 (a whole token no registered header equals)
    f = workdir / "s1_n1_microglia_p2ry12.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["Microglia-specific genes (top 500)"], ["P2RY12"], ["TMEM119"], ["CX3CR1"]]
              + [["MG%dZ" % k] for k in range(497)]})
    s1_cases.append(("N1 (2) refined: a Zhang microglia input list whose first gene is P2RY12 -> RG-N06 qualifies (P2RY12 is data)",
                     [f], "RG-N06", None, "qualifies", "ok"))
    # N4: the reviewer's I7 -- 'Ribosome' beside 'Ribosome biogenesis in eukaryotes'
    f = workdir / "s1_n4_i7.xlsx"
    _xlsx(f, {"Gene set definitions": [["Pathway", "Genes"], ["Ribosome", ";".join(genes[:12])],
                                       ["Ribosome biogenesis in eukaryotes", ";".join(genes[12:24])],
                                       ["Spliceosome", ";".join(genes[24:36])]]})
    s1_cases.append(("N4 (I7) control: RG-03 'Ribosome' with no rival names -> both rows named (ambiguous)", [f], "RG-03",
                     [["Ribosome"]], "else branch", "ambiguous"))
    s1_cases.append(("N4 (I7): the same run with the table's other printed names as --rival -> 'Ribosome' resolves to its own row",
                     [f], "RG-03", [["Ribosome"]], "qualifies", "ok",
                     {"rival": ["Ribosome biogenesis in eukaryotes", "Spliceosome"]}))
    # ---- register v6.5: every case above is a TEXT-FILTER plant (checked on text_result, the first filter) unless marked final
    n_text = len(s1_cases)
    # (2)-(3) M1-M3: the reviewer's capital-letter and dash layouts, refused by the text filter
    CST = "BUCH-E-Syn-ChemSynTransmission-S1"
    f = workdir / "s1_m1_gap1_caps.xlsx"
    _xlsx(f, {"ENRICHMENT OF THE GENE SETS TESTED": [
        ["TERM", "P VALUE", "ADJUSTED P VALUE", "ODDS RATIO", "COMBINED SCORE", "GENES"],
        ["CHEMICAL SYNAPTIC TRANSMISSION (GO:0007268)", 1e-5, 6e-5, 3.1, 35.7, ";".join(genes[:12])]]})
    s1_cases.append(("M1: capital-letter GAP1 (an Enrichr export in capitals: 'P VALUE', 'ADJUSTED P VALUE', 'ODDS RATIO', "
                     "'COMBINED SCORE' over the rows) -> refused", [f], CST, None, "else branch", "result list"))
    f = workdir / "s1_m1_fgsea_words.xlsx"
    _xlsx(f, {"GENE SETS TESTED": [["NAME", "ADJUSTED P VALUE", "RANK AT MAX", "LEADING EDGE GENES"],
                                   ["RIBOSOMAL STRUCTURE", 0.01, 120, ";".join(genes[:12])],
                                   ["CYTOSOLIC RIBOSOME", 0.02, 98, ";".join(genes[12:24])]]})
    s1_cases.append(("M1: capital-letter fGSEA export with multi-word headers ('ADJUSTED P VALUE', 'RANK AT MAX', 'LEADING EDGE "
                     "GENES') -> refused", [f], RIB, None, "else branch", "result list"))
    f = workdir / "s1_m1_gap2_caps.xlsx"
    _xlsx(f, {"TABLE S5": [["SUPPLEMENTARY TABLE 5. GSEA OF THE GENE SETS USED"], ["GENE SET", "SUBGROUP", "NES", "PADJ", "GENES"],
                           ["RIBOSOMAL STRUCTURE", 1, 2.8, 0.001, ";".join(genes[:12])],
                           ["CYTOSOLIC RIBOSOME", 1, 2.9, 0.001, ";".join(genes[12:24])]]})
    s1_cases.append(("M1: capital-letter GAP2 -> refused", [f], RIB, None, "else branch", "result list"))
    f = workdir / "s1_m1_pagani_caps.xlsx"
    _xlsx(f, {"GENE LISTS USED IN ENRICHMENT": [["HYPO DECODED GENES", "ASD DE GENES", "SYNGO"]]
              + [[genes[k], "D%dGENE" % k, "S%dGENE" % k] for k in range(30)]})
    s1_cases.append(("M1: capital-letter Pagani layout -> PAG-C1 refused", [f], "PAG-C1", None, "else branch", "result list"))
    for tag, form in (("ascii", "leading-edge genes"), ("u2010", "leading‐edge genes"), ("endash", "leading–edge genes"),
                      ("camel", "leadingEdge")):
        f = workdir / ("s1_m2_le_%s.xlsx" % tag)
        _xlsx(f, {"Gene sets tested": [["Gene set", form]] + [[r[0], r[1]] for r in two]})
        s1_cases.append(("M2: a column '%s' -> refused" % form.encode("ascii", "backslashreplace").decode(), [f], RIB, None,
                         "else branch", "result list"))
    f = workdir / "s1_m1_fgsea_caps.xlsx"
    _xlsx(f, {"GENE SETS TESTED": [["PATHWAY", "PVAL", "PADJ", "LOG2ERR", "ES", "NES", "SIZE", "LEADINGEDGE"],
                                   ["RIBOSOMAL STRUCTURE", 0.001, 0.01, 0.3, 0.6, 2.1, 40, ",".join(genes[:12])],
                                   ["CYTOSOLIC RIBOSOME", 0.002, 0.02, 0.3, 0.5, 1.9, 38, ",".join(genes[12:24])]]})
    s1_cases.append(("M1: capital-letter fGSEA export -> refused", [f], RIB, None, "else branch", "result list"))
    f = workdir / "s1_m3_camel_cp.xlsx"
    _xlsx(f, {"Gene sets tested": [["Description", "GeneRatio", "BgRatio", "geneID"]]
              + [[r[0], "12/400", "80/18000", r[1].replace(";", "/")] for r in two]})
    s1_cases.append(("M3: clusterProfiler camelCase statistics only (GeneRatio, BgRatio) -> refused", [f], RIB, None, "else branch",
                     "result list"))
    f = workdir / "s1_m3_camel_metascape.xlsx"
    _xlsx(f, {"Gene sets tested": [["Description", "LogP", "-log10(FDR)", "Symbols"]]
              + [[r[0], -5.2, 3.1, r[1].replace(";", ",")] for r in two]})
    s1_cases.append(("M3: Metascape-style 'LogP' / '-log10(FDR)' -> refused", [f], RIB, None, "else branch", "result list"))
    # (1) corroboration plants (final result), on Buch's pinned fallback 'secretory vesicle' (GO:0099503) and the Zhang size 500
    SV = "BUCH-E-Syn-SecVesicle-S1"
    fb = json.loads((ROOT / "arcs" / "audit" / "register_sets" / "buch_goslim_fallback_GO0099503.json").read_text(encoding="utf-8"))
    uni_all = json.loads((ROOT / "arcs" / "audit" / "register_sets" / "UNIVERSE_GENES.json").read_text(encoding="utf-8"))
    sv = sorted(set(fb["members_hgnc"]) & set(uni_all["classes"]["V-AAL"]))
    n_sv = len(sv)
    k79 = max(k for k in range(n_sv + 1) if k / n_sv < 0.80)
    assert 0.79 <= k79 / n_sv < 0.80, (k79, n_sv)
    f = workdir / "s1_c_le_subset.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["Secretory vesicle"]] + [[x] for x in sv[:30]]})
    s1_cases.append(("(1)(a): a leading-edge-like subset (30 of the set's %d in-universe genes) in an input-worded sheet passes the "
                     "text filter and fails corroboration" % n_sv, [f], SV, None, "else branch", "uncorroborated (Jaccard",
                     {"level": "final"}))
    f = workdir / "s1_c_equal.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["Secretory vesicle"]] + [[x] for x in sv]})
    s1_cases.append(("(1)(a): an input list equal to the pinned external set -> qualifies (Jaccard 1)", [f], SV, None, "qualifies",
                     "corroborated: external", {"level": "final"}))
    f = workdir / "s1_c_equal_na.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["Secretory vesicle"]] + [[x] for x in sv[:10]] + [["NA"]] + [[x] for x in sv[10:]]
              + [["NA"]]})
    s1_cases.append(("(1)(a) / M4: the same list with NA cells among its genes -> NA dropped from the members, qualifies", [f], SV,
                     None, "qualifies", "corroborated: external", {"level": "final"}))
    f = workdir / "s1_c_j79.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["Secretory vesicle"]] + [[x] for x in sv[:k79]]})
    s1_cases.append(("(1)(a): an input list at Jaccard %.4f (%d of %d) -> fails" % (k79 / n_sv, k79, n_sv), [f], SV, None,
                     "else branch", "uncorroborated (Jaccard", {"level": "final"}))
    f = workdir / "s1_c_caps_positive.xlsx"
    _xlsx(f, {"GENE SETS USED IN ENRICHMENT": [["SECRETORY VESICLE"]] + [[x] for x in sv]})
    s1_cases.append(("positive control: a genuine all-capitals input sheet ('SECRETORY VESICLE' over its genes) -> qualifies when "
                     "corroborated", [f], SV, None, "qualifies", "corroborated: external", {"level": "final"}))
    s1_cases.append(("(1)(b): RG-04's 500-symbol list against its printed size 500 -> qualifies", [workdir / "s1_pass_size500.xlsx"],
                     "RG-04", None, "qualifies", "corroborated: printed_size", {"level": "final"}))
    f = workdir / "s1_c_size501.xlsx"
    _xlsx(f, {"Gene set definitions": [["Neuron-specific genes (top 500)"]] + [[x] for x in neuron + [approved_pool[500]]]})
    s1_cases.append(("(1)(b): 501 symbols against RG-04's printed size 500 -> fails", [f], "RG-04", None, "else branch",
                     "size mismatch", {"level": "final"}))
    s1_cases.append(("(1)(c): a cell with no external definition and no printed size ('*Ribosomal structure') -> the text filter "
                     "admits the list, the else branch applies", [workdir / "s1_pass_membership.xlsx"], RIB, None, "else branch",
                     "mode none", {"level": "final"}))
    f = workdir / "s1_c_notbuildable.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["ASD upregulated"]] + [[x] for x in genes[:30]]})
    s1_cases.append(("(1)(c) v6.6: a cell whose comparator is not buildable pre-freeze (BUCH-E-ASDup-S1) -> "
                     "the text filter admits the list, the else branch applies", [f], "BUCH-E-ASDup-S1", None, "else branch",
                     "comparator not buildable pre-freeze", {"level": "final"}))
    # v6.7 N1 built asdM12 from Voineagu 2011's Supplementary Table 14 as the focal cell's PRIMARY comparator; register v6.8 (B S1;
    # the orchestrator under the operator's standing delegation, post hoc, declared) moved it to the near-miss view (R-d applied
    # uniformly: the name 'asdM12' reaches M12 only through Parikshak 2013). The focal cell's list equal to that set qualifies in the
    # view, is sent to the else branch in the primary run, and its first 30 genes fail corroboration in the view
    m12c = spec["source1_lists"]["cells"]["BUCH-E-ASDdown-S1"]["corroboration_views"]["near_miss"]
    m12 = sorted(set(json.loads((ROOT / "arcs" / "audit" / "register_sets" / (m12c["set_id"] + ".json")).read_text(encoding="utf-8"))
                     ["members_hgnc"]) & set(uni_all["classes"][m12c["class"]]))
    f = workdir / "s1_v68_asdm12_equal.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["ASD downregulated"]] + [[x] for x in m12]})
    s1_cases.append(("v6.8 B S1: BUCH-E-ASDdown-S1, a list equal to its near-miss comparator (Voineagu 2011 Supplementary Table 14, "
                     "%d in-universe genes) -> qualifies in the near-miss view" % len(m12), [f], "BUCH-E-ASDdown-S1", None,
                     "qualifies", "corroborated: external", {"level": "final", "view": "near_miss"}))
    s1_cases.append(("v6.8 B S1: the same list for BUCH-E-ASDdown-S1 in the PRIMARY view -> else branch (comparator not buildable)",
                     [f], "BUCH-E-ASDdown-S1", None, "else branch", "comparator not buildable pre-freeze", {"level": "final"}))
    f = workdir / "s1_v68_asdm12_le30.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["ASD downregulated"]] + [[x] for x in m12[:30]]})
    s1_cases.append(("v6.8 B S1: BUCH-E-ASDdown-S1, 30 of its near-miss comparator's genes -> fails corroboration in the view", [f],
                     "BUCH-E-ASDdown-S1", None, "else branch", "uncorroborated (Jaccard", {"level": "final", "view": "near_miss"}))
    # register v6.9 (C5; the orchestrator under the operator's standing delegation, post hoc, declared): Buch's 'ASD rare de novo'
    # moved to the near-miss view by reading (iii) applied uniformly (Sanders 2019's ASD65 reached by its column note, not its
    # title). Its descriptor cell's list equal to that set qualifies in the view and is sent to the else branch in the primary run
    rdc = spec["source1_lists"]["cells"]["BUCH-E-RDNV-S1"]["corroboration_views"]["near_miss"]
    rdn = sorted(set(json.loads((ROOT / "arcs" / "audit" / "register_sets" / (rdc["set_id"] + ".json")).read_text(encoding="utf-8"))
                     ["members_hgnc"]) & set(uni_all["classes"][rdc["class"]]))
    f = workdir / "s1_v69_rdnv_equal.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["ASD rare de novo"]] + [[x] for x in rdn]})
    s1_cases.append(("v6.9 C5: BUCH-E-RDNV-S1, a list equal to its near-miss comparator (Sanders 2019 ASD65, %d in-universe genes) "
                     "-> qualifies in the near-miss view" % len(rdn), [f], "BUCH-E-RDNV-S1", None, "qualifies",
                     "corroborated: external", {"level": "final", "view": "near_miss"}))
    s1_cases.append(("v6.9 C5: the same list for BUCH-E-RDNV-S1 in the PRIMARY view -> else branch (comparator not buildable)",
                     [f], "BUCH-E-RDNV-S1", None, "else branch", "comparator not buildable pre-freeze", {"level": "final"}))
    # ---- register v6.6 B1: the comparator is the pinned committed set; nothing else is accepted
    import copy
    sets_dir = ROOT / "arcs" / "audit" / "register_sets"
    pag = spec["source1_lists"]["cells"]["PAG-C1"]["corroboration"]
    pag_body = json.loads((sets_dir / (pag["set_id"] + ".json")).read_text(encoding="utf-8"))
    pag_genes = sorted(set(pag_body["members_hgnc"]) & set(uni_all["classes"][pag["class"]]))
    f_pag = workdir / "s1_b1_pagani_asd_de.xlsx"
    _xlsx(f_pag, {"Supplementary Table 3": [["Gene lists used in enrichment analyses"], ["ASD DE genes"]] + [[x] for x in pag_genes]})
    s1_cases.append(("B1: PAG-C1, an input list equal to its pinned comparator (Gandal 2022, 24 DE modules; register_sets) -> qualifies",
                     [f_pag], "PAG-C1", None, "qualifies", "corroborated: external", {"level": "final"}))
    other = spec["source1_lists"]["cells"]["PAG-C4"]["corroboration"]  # the SynGO comparator: another committed set
    other_bytes = (sets_dir / (other["set_id"] + ".json")).read_bytes()
    genuine = (sets_dir / (pag["set_id"] + ".json")).read_bytes()

    def fake_dir(tag: str, content: bytes | None) -> Path:
        d = workdir / ("b1_sets_" + tag)
        d.mkdir(exist_ok=True)
        f_ = d / (pag["set_id"] + ".json")
        if f_.exists():
            f_.unlink()
        if content is not None:
            f_.write_bytes(content)
        return d

    def spec_with(sets_dir_=None, **pins):
        sp = copy.deepcopy(spec)
        if sets_dir_ is not None:
            sp["source1_lists"]["corroboration"]["sets_dir"] = str(sets_dir_)
        sp["source1_lists"]["cells"]["PAG-C1"]["corroboration"].update(pins)
        return sp
    self_made = json.dumps({"set_id": pag["set_id"], "members_hgnc": pag_genes[:40],
                            "universe": {pag["class"]: {}}}).encode("utf-8")
    malformed = b"{not json"
    b1 = [("wrong set: the file under PAG-C1's set id is another committed set (SynGO)",
           spec_with(fake_dir("wrong", other_bytes)), "file sha256 differs"),
          ("wrong set, file pin moved to it: the pins name PAG-C1's set id but the other set's file hash",
           spec_with(fake_dir("wrong2", other_bytes), json_sha256=_sha(other_bytes)), "set id differs"),
          ("self-made set (the list itself) under the right set id", spec_with(fake_dir("self", self_made)), "file sha256 differs"),
          ("self-made set with its file hash pinned: the members hash still differs",
           spec_with(fake_dir("self2", self_made), json_sha256=_sha(self_made)), "members sha256 differs"),
          ("missing file", spec_with(fake_dir("missing", None)), "file unreadable"),
          ("malformed JSON (its bytes pinned, so the parser is reached)", spec_with(fake_dir("bad", malformed),
                                                                                   json_sha256=_sha(malformed)), "malformed JSON"),
          ("hash mismatch: the genuine file with one byte appended", spec_with(fake_dir("hash", genuine + b"\n")),
           "file sha256 differs"),
          ("class mismatch: the pins name a class the committed set has no universe for", spec_with(**{"class": "XYZ"}),
           "class XYZ not in the committed set's universe")]
    for label, sp, why in b1:
        s1_cases.append(("B1 refused: PAG-C1 with the genuine list, %s -> else branch" % label, [f_pag], "PAG-C1", None,
                         "else branch", why, {"level": "final", "spec": sp, "spec_note": label}))
    # the Romero-Garcia KEGG family recipe (built by the engine from the pinned Enrichr libraries)
    import s_build as SB
    _src = SB.Sources()
    _libs = {"KEGG_2015": _src.enrichr("enrichr_kegg_2015", False), "KEGG_2016": _src.enrichr("enrichr_kegg_2016", False,
                                                                                             SB.KEGG16_SUFFIX)}
    _lib, _pid = SB.kegg_family_choice(["Ribosome", "Spliceosome"], {k: v[0] for k, v in _libs.items()})["per_name"]["Ribosome"]
    rib = sorted({_corr_env(spec)[0].symbol(g["symbol"])[0] for g in _libs[_lib][1][_pid]} - {None})
    rib = sorted(set(rib) & set(uni_all["classes"]["dk-ctx"]))
    f = workdir / "s1_b1_kegg_ribosome.docx"
    _docx(f, [["Pathway", "Genes"], ["Ribosome", ";".join(rib)], ["Spliceosome", ";".join(genes[:12])]],
          caption="Table S2. KEGG pathways: gene sets used in the enrichment analysis")
    s1_cases.append(("B1 recipe: RG-03 'Ribosome' (--rival 'Spliceosome'), the list equal to the pathway the family rule picks (%s "
                     "%s) -> qualifies" % (_lib, _pid), [f], "RG-03", [["Ribosome"]], "qualifies", "corroborated: kegg_family_recipe",
                     {"level": "final", "rival": ["Spliceosome"]}))
    sp_k = copy.deepcopy(spec)
    for cid in ("RG-03",):
        sp_k["source1_lists"]["cells"][cid]["corroboration"]["recipe"]["libraries"]["KEGG_2015"]["sha256"] = "0" * 64
    s1_cases.append(("B1 recipe refused: the same run with a KEGG_2015 library pin that differs -> else branch", [f], "RG-03",
                     [["Ribosome"]], "else branch", "library KEGG_2015 sha256 differs",
                     {"level": "final", "rival": ["Spliceosome"], "spec": sp_k, "spec_note": "KEGG_2015 pin changed"}))
    f = workdir / "s1_b1_kegg_noname.docx"
    _docx(f, [["Pathway", "Genes"], ["Planted pathway zeta", ";".join(rib)], ["Spliceosome", ";".join(genes[:12])]],
          caption="Table S2. KEGG pathways: gene sets used in the enrichment analysis")
    s1_cases.append(("B1 recipe refused: a printed name that reaches no pathway of either library -> else branch", [f], "RG-03",
                     [["Planted pathway zeta"]], "else branch", "reaches no pathway", {"level": "final", "rival": ["Spliceosome"]}))
    # ---- v6.6 C1: the printed size counts distinct approved HGNC symbols, not rows (the reviewer's A9 / A10)
    f = workdir / "s1_c1_dups.xlsx"
    _xlsx(f, {"Gene set definitions": [["Neuron-specific genes (top 500)"]] + [[x] for x in neuron[:400] + neuron[:100]]})
    s1_cases.append(("C1 (A9): 400 distinct approved symbols + 100 repeats = 500 rows against RG-04's printed 500 -> size mismatch",
                     [f], "RG-04", None, "else branch", "size mismatch", {"level": "final"}))
    f = workdir / "s1_c1_arbitrary.xlsx"
    _xlsx(f, {"Input gene lists": [["Neuron genes (Zhang)"]] + [["R%dK" % i] for i in range(500)]})
    s1_cases.append(("C1 (A10): 500 arbitrary symbol-shaped tokens (no HGNC symbol) under 'Neuron genes (Zhang)' -> size mismatch",
                     [f], "RG-04", None, "else branch", "size mismatch", {"level": "final"}))
    f = workdir / "s1_c1_plus_unmapped.xlsx"
    _xlsx(f, {"Gene set definitions": [["Neuron-specific genes (top 500)"]] + [[x] for x in neuron + ["R999K"]]})
    s1_cases.append(("C1: 500 distinct approved symbols and one token no HGNC symbol matches (501 rows) -> qualifies (the count is "
                     "of approved symbols)", [f], "RG-04", None, "qualifies", "corroborated: printed_size", {"level": "final"}))
    # ---- v6.6 C3: a generic title over the list is its title (the reviewer's g_GENES / g_SYMBOL)
    for tag, hdr_ in (("genes", "GENES"), ("symbol", "SYMBOL")):
        f = workdir / ("s1_c3_%s.xlsx" % tag)
        _xlsx(f, {"Gene set definitions": [["Neuron-specific genes (top 500)"], [hdr_]] + [[x] for x in neuron]})
        s1_cases.append(("C3: RG-04's 500 genes under the title and a '%s' header row -> 500 counted, qualifies" % hdr_, [f], "RG-04",
                         None, "qualifies", "corroborated: printed_size", {"level": "final"}))
    # ---- v6.6 C2: an approved pseudogene symbol in another set's column is data, not a marker (the reviewer's A6)
    imm = json.loads((ROOT / "arcs" / "audit" / "register_sets" / "buch_goslim_fallback_GO0006955.json").read_text(encoding="utf-8"))
    imm = sorted(set(imm["members_hgnc"]) & set(uni_all["classes"]["V-AAL"]))
    col2 = imm[:30] + ["C9orf78P1"]
    f = workdir / "s1_c2_a6_pseudogene.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["Secretory vesicle", "Immune response"]]
              + [[sv[i] if i < len(sv) else None, col2[i] if i < len(col2) else None] for i in range(max(len(sv), len(col2)))]})
    s1_cases.append(("C2 (A6): a genuine input sheet whose other set's column holds the approved pseudogene C9orf78P1 -> Secretory "
                     "vesicle qualifies (an HGNC symbol is never split into pieces)", [f], SV, None, "qualifies",
                     "corroborated: external", {"level": "final"}))
    # ---- v6.6 C6: whole-cell statistics wording (the reviewer's A5 family)
    for tag, head in (("tvalue", "t value"), ("tvalue_caps", "T-VALUE"), ("corr", "Correlation"), ("r", "r"),
                      ("or_ci", "OR (95% CI)")):
        f = workdir / ("s1_c6_%s.xlsx" % tag)
        _xlsx(f, {"Gene sets used in enrichment": [["Secretory vesicle", head]]
                  + [[x, round(3.1 - i * 0.01, 4)] for i, x in enumerate(sv)]})
        s1_cases.append(("C6 (A5): the list beside a '%s' column -> refused" % head, [f], SV, None, "else branch", "result list",
                         {"level": "final"}))
    # ---- the declared residual (register 1.6, v6.6 C6): a >= 80 % subset in an input-worded sheet still qualifies (the reviewer's A7)
    k85 = int(0.85 * n_sv) + 1
    f = workdir / "s1_residual_a7.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["Secretory vesicle"]] + [[x] for x in sv[:k85]]})
    s1_cases.append(("residual, declared (A7): an 85 %% subset (%d of %d) of Secretory vesicle's comparator in an input-worded sheet "
                     "-> qualifies (Jaccard >= .80)" % (k85, n_sv), [f], SV, None, "qualifies", "corroborated: external",
                     {"level": "final"}))
    # ---- register v6.7: the near-miss secondary view (its own pinned comparator; the primary never changes)
    for cid_, tag_ in (("BUCH-E-ASDup-S1", "asdM16"), ("BUCH-E-FMRP-S1", "FMRP842"), ("BUCH-E-TS-S1", "Tourette")):
        nmc = spec["source1_lists"]["cells"][cid_]["corroboration_views"]["near_miss"]
        nmb = json.loads((ROOT / "arcs" / "audit" / "register_sets" / (nmc["set_id"] + ".json")).read_text(encoding="utf-8"))
        nmg = sorted(set(nmb["members_hgnc"]) & set(uni_all["classes"][nmc["class"]]))
        head_ = " ".join(spec["source1_lists"]["cells"][cid_]["names"][0])
        f = workdir / ("s1_v67_nearmiss_%s.xlsx" % tag_)
        _xlsx(f, {"Gene sets used in enrichment": [[head_]] + [[x] for x in nmg]})
        s1_cases.append(("v6.7 near-miss view: %s, a list equal to its near-miss comparator (%s) -> qualifies in the view" % (cid_, tag_),
                         [f], cid_, None, "qualifies", "corroborated: external", {"level": "final", "view": "near_miss"}))
        s1_cases.append(("v6.7 near-miss view: the same list for %s in the PRIMARY view -> else branch (comparator not buildable)"
                         % cid_, [f], cid_, None, "else branch", "comparator not buildable pre-freeze", {"level": "final"}))
    s1_cases.append(("v6.7 near-miss view: a cell with no near-miss pin (BUCH-E-Syn-SecVesicle-S1) -> the view is refused",
                     [workdir / "s1_c_equal.xlsx"], SV, None, "run refused", "no 'near_miss' view is pinned",
                     {"level": "final", "view": "near_miss"}))
    f = workdir / "s1_v67_cns.xlsx"
    _xlsx(f, {"Gene sets used in enrichment": [["CNS autoimmune"]] + [[x] for x in genes[:30]]})
    s1_cases.append(("v6.7 near-miss view: BUCH-E-CNSauto-S1, whose near-miss comparator is not buildable either -> else branch in "
                     "the view", [f], "BUCH-E-CNSauto-S1", None, "else branch", "near-miss comparator not buildable either",
                     {"level": "final", "view": "near_miss"}))
    # ---- register v6.7 N3: the universe and the HGNC table pinned by sha256; every failure -> the else branch, recorded
    le30 = workdir / "n3_universe_leading_edge30.json"
    le30.write_text(json.dumps({"n_genes": {c: 30 for c in uni_all["classes"]},
                                "classes": {c: sv[:30] for c in uni_all["classes"]}}), encoding="utf-8", newline="\n")

    def spec_env(**kw):
        sp = copy.deepcopy(spec)
        sp["source1_lists"]["corroboration"].update(kw)
        return sp
    n3 = [("a universe restricted to the 30 leading-edge genes (pin unchanged)", spec_env(universe_genes=str(le30)),
           "UNIVERSE_GENES.json sha256 differs"),
          ("the same 30-gene universe with its own hash pinned", spec_env(universe_genes=str(le30),
                                                                          universe_genes_sha256=_sha(le30.read_bytes())),
           "universe too small"),
          ("a missing universe file", spec_env(universe_genes=str(workdir / "n3_missing_universe.json")),
           "could not be used (FileNotFoundError"),
          ("an HGNC table pin that differs", spec_env(hgnc_table={"path": spec["source1_lists"]["corroboration"]["hgnc_table"]["path"],
                                                                  "sha256": "0" * 64}),
           "the HGNC table's sha256 differs")]
    for label, sp, why in n3:
        s1_cases.append(("N3 refused: Secretory vesicle's genuine list (qualifies with the pinned tables), %s -> else branch" % label,
                         [workdir / "s1_c_equal.xlsx"], SV, None, "else branch", why,
                         {"level": "final", "spec": sp, "spec_note": "N3: " + label}))
    for idx, case in enumerate(s1_cases):
        case_, files, cell, alts, exp, exp_reason = case[:6]
        extra_ = case[6] if len(case) > 6 else {}
        level = extra_.get("level") or ("text" if idx < n_text else "final")
        exp_counts = {k: v for k, v in extra_.items() if k not in ("rival", "level", "spec", "spec_note", "view")}
        try:
            out = run_source1(files, alts, None, extra_.get("spec") or spec, cell, extra_.get("rival"), extra_.get("view"))
        except SystemExit as e:  # v6.3 O4: a refused run
            out = {"result": "run refused", "reason": str(e), "text_result": "run refused", "text_reason": str(e),
                   "n_candidates": 0, "n_refused": 0, "n_qualifying_distinct": 0}
        got, why = (out["text_result"], out["text_reason"]) if level == "text" else (out["result"], out["reason"])
        ok = got == exp and exp_reason in why and all(out.get(k) == v for k, v in exp_counts.items())
        n_ok += ok
        print("[%s] source1 (%s) | %s" % ("CAUGHT" if ok else "MISSED", level, case_))
        print("    %-12s %-50s candidates=%d refused=%d qualifying=%d" % (got, why[:50], out["n_candidates"], out["n_refused"],
                                                                        out["n_qualifying_distinct"]))
        record.append({"target": "source1_lists", "case": case_, "cell": cell, "rival_only": extra_.get("rival"), "level": level,
                       "spec_modified": extra_.get("spec_note"), "view": extra_.get("view"),
                       "carrier_types": sorted({Path(x).suffix for x in files}),
                       "expected": exp, "expected_reason_contains": exp_reason, "expected_counts": exp_counts,
                       "observed": {k: v for k, v in out.items() if k != "log"}, "caught": bool(ok)})
    cases = cases + [("source1_lists",) + tuple(c[:6]) for c in s1_cases]
    print("selftest: %d / %d cases classified as planted" % (n_ok, len(cases)))
    import hashlib
    rec = {"what": "carrier_test.py selftest on SYNTHETIC carriers (public-atlas labels, random values; seed 20260926)",
           "n_cases": len(cases), "n_caught": n_ok, "cases": record,
           "untested_adapters": ["xls", "zip (recursion; members use tested adapters)", "txt (whitespace table)"],
           "pdf_adapter": {"pdfplumber": _ver("pdfplumber"), "pdfminer.six": _ver("pdfminer.six"), "pypdfium2": _ver("pypdfium2"),
                           "pinned_in_spec": (spec.get("pdf_adapter") or {}).get("version"),
                           "pdf_writer_for_plants": "matplotlib %s (vector text, fonttype 42)" % _ver("matplotlib")},
           "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "spec_sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest()}
    # register v6.3 O7: the record goes to the workdir and is compared with the frozen one (run stamps aside); the frozen record is
    # rewritten only on request (--overwrite-frozen-record, before the freeze)
    frozen = SPEC.parent / "carrier_tests_selftest.json"
    txt = json.dumps(rec, indent=1, ensure_ascii=False)
    if overwrite_frozen:
        frozen.write_text(txt, encoding="utf-8", newline="\n")
        assert json.loads(frozen.read_text(encoding="utf-8")) == json.loads(txt)
        print("frozen record REWRITTEN (--overwrite-frozen-record): %s sha256 %s"
              % (frozen.relative_to(ROOT).as_posix(), hashlib.sha256(frozen.read_bytes()).hexdigest()))
    run_rec = dict(rec)
    run_rec[SELFTEST_RUN_STAMP] = {"utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
                                   .replace(microsecond=0).isoformat(), "workdir": str(workdir)}
    outp = workdir / "carrier_tests_selftest.json"
    outp.write_text(json.dumps(run_rec, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print("record written to the workdir: %s sha256 %s" % (outp, hashlib.sha256(outp.read_bytes()).hexdigest()))
    same = False
    if frozen.exists():
        old = json.loads(frozen.read_text(encoding="utf-8"))
        d = _diff_paths(rec, {k: v for k, v in old.items() if k != SELFTEST_RUN_STAMP})
        same = not d
        print(("record EQUAL to the frozen %s (run stamps aside)" if same else
               "record DIFFERS from the frozen %s at %d key paths: %s") % ((frozen.relative_to(ROOT).as_posix(),) if same else
                                                                          (frozen.relative_to(ROOT).as_posix(), len(d), "; ".join(d[:10]))))
    else:
        print("no frozen record at %s" % frozen.relative_to(ROOT).as_posix())
    return 0 if (n_ok == len(cases) and same) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--target", required=True)
    r.add_argument("--variant")
    r.add_argument("--carrier", action="append", required=True)
    r.add_argument("--out")
    s = sub.add_parser("selftest")
    s.add_argument("--workdir", help="the record is written here and compared with the frozen one (v6.3 O7)")
    s.add_argument("--overwrite-frozen-record", action="store_true",
                   help="rewrite register_maps/carrier_tests_selftest.json (before the freeze only, after a spec / engine change)")
    s1 = sub.add_parser("source1")  # register v6.1 Q1; v6.2 P2: by cell id (under the gate only)
    s1.add_argument("--cell", required=True, help="the TSV cell id; its names and printed size are read from the spec")
    s1.add_argument("--name", action="append", help="only for a family cell whose names come from the gated table: the printed "
                                                    "name of ONE pathway (one phrase; one run per pathway; v6.3 O4)")
    s1.add_argument("--view", choices=["near_miss"], help="v6.7: the registered secondary view (the cell's near-miss comparator)")
    s1.add_argument("--rival", action="append", help="only for a family cell: another pathway name the gated table prints (a rival "
                                                     "name, never an alternative; repeat per name; v6.4 N4)")
    s1.add_argument("--carrier", action="append", required=True)
    a = ap.parse_args()
    if a.cmd == "source1":
        out = run_source1(a.carrier, [[n] for n in a.name] if a.name else None, None, None, a.cell, a.rival, a.view)
        print("source1: %s (%s); text filter %s; candidates %d, refused %d, qualifying %d; corroboration %s"
              % (out["result"], out["reason"], out["text_result"], out["n_candidates"], out["n_refused"],
                 out["n_qualifying_distinct"], json.dumps(out.get("corroboration"))))
        return 0
    if a.cmd == "selftest":
        if a.workdir:
            return selftest(Path(a.workdir), a.overwrite_frozen_record)
        with tempfile.TemporaryDirectory() as d:
            return selftest(Path(d), a.overwrite_frozen_record)
    out = run(a.target, a.carrier, a.variant)
    print("target %s variant %s: %s" % (a.target, a.variant, "PASS" if out["target_pass"] else "FAIL"))
    print("files/tables: " + ", ".join("%s %s" % kv for kv in sorted(out["log"].items())))
    print("diagnostics: " + ", ".join("%s %s" % kv for kv in sorted(out["diagnostics"].items())))
    for m in out["maps"]:
        print("  " + fmt(m))
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
