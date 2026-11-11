"""A1 claims register DRAFT v6.8 (B S2 of the v6.7 final re-check; the orchestrator's decision under the operator's standing
delegation, 2026-09-29): three whole workbooks on E: held identifier-bearing sheets -- Kang 2011 MOESM50, Parikshak 2013
supplement 02 and Parikshak 2016 Supplementary Table 2. Each is REDUCED to the gene-level content the register builders read,
written beside the original as a JSON sheet dump (deterministic bytes; cell values with their Python types, exactly as the
builders' reader returned them), and the original is deleted once the builders' outputs are shown byte-identical (register
1.6; its sha256, byte size and sheet names + dimensions are kept in the reduction's 'original' block, in extract_manifest.json
and in SOURCE.md).

  reduce   python -X utf8 reduce_v68.py reduce [key ...]   (the programme venv since v6.9, xlrd 2.0.2 a declared addition;
           v6.8 ran the .xls under the system Python -- register 1.6, C4)
           every sheet of each original passes the privacy guard (privacy_guard.py: names, dimensions and rule letters only);
           the kept sheet is read through the guard with its declared columns; a reduction the guard still flags is read
           in declared columns only
  delete   python -X utf8 reduce_v68.py delete    deletes an original only if its sha256 is the pinned one and its reduction
           exists with that sha256 recorded (run after the builders' outputs were compared)
  inventory python -X utf8 reduce_v68.py inventory  (the programme venv) the guard's verdict on every sheet of every workbook the
           builders read or pin -> arcs/audit/register_maps/privacy_inventory_v68.json (names, dimensions, rule letters)
  (import) load(path, sha256, original_sha256) / rows(rec, sheet, declared, header_row): what the builders call

Kept (the builders' reads, s_extract.kang_modules, s_build.Sources.parikshak2013 / parikshak2016):
  kang2011       'Supple Table 9.' whole (clean: 912 x 17 -- module, colour, size, hub genes, DAVID term hits), xlrd values
  parikshak2013  'TableS1A' (wider than 50 columns, so identifier-bearing by rule W): only columns 'ENSEMBL GENE ID', 'Gene
                 Symbol', 'Module Label' (header row 3), openpyxl values
  parikshak2016  'TableS2a' (wider than 50 columns): only 'ENSEMBL ID', 'HGNC Symbol', 'log2(FC) ASD vs CTL', the FDR column the
                 builder reads (index 10, 'FDR-adjusted P value, ASD vs C...') and 'WGCNA Module Label' (header row 2)
Round 2 of v6.8 (the orchestrator under the operator's standing delegation, on round 1's report -- one uniform rule, no per-flag
judgement): every flagged workbook a register builder reads is reduced to exactly the sheets and columns the builders read
(ORIGINALS: Gandal 2018 Table S1, Polioudakis 2019 Table S4, Satterstrom 2020 Table S2, Lake 2018's tables, Gandal 2022
Supplementary Data 5 / 6, Sanders 2019 Tables S1 / S2 / S4; Pfenning 2014 Tables S1-S8, of which the builders read the sheet
NAMES only). rows() returns a kept column at its original position (the other columns empty), so the builders' indexing is the
original's; a reduction the guard still flags (e.g. an accession-like header such as 'CHD253') is read in declared columns only.
Runs under the programme venv (openpyxl) for .xlsx / .zip originals; an .xls needs xlrd.
Nothing of any sheet is printed but its name, dimensions and the guard's rule letters.

Register DRAFT v6.9 (the orchestrator's skeptic re-check, S2-residual, under the operator's standing delegation, 2026-09-30):
the same rule for the two exploration-lane copies under E:\\data\\asdg\\explore_public (ORIGINALS 'root'):
  velmeshev2019     Velmeshev 2019 Data S4 (.xls; its per-individual sheet 'Individual_specific_DEGs' is classified by the
                    guard like every sheet -- rule letters only -- and nothing of it is kept or printed): kept
                    'ASD_DEGs' columns 1-7 (the exploration ingest's S4_COLS, asserted; s_extract.velmeshev reads five of
                    them), xlrd values; an .xls sheet may now be kept in declared columns (v6.8: whole and clean only)
  lake2018_explore  the exploration copy of Lake 2018 MOESM11 (the same file as the register's deleted copy): kept 'Table S3''s
                    seven blocks (the columns under each block name of row 4, seven per block; the gap columns are empty) --
                    what fetch_celltype_lake2018.py and fetch_celltype_seidlitz2020.py read -- and every sheet's name
The explore scripts read these reductions (and the sheet names / dimensions recorded before deletion) with their summaries
shown byte-identical (their --check modes).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import privacy_guard as G  # noqa: E402

SRC = Path(r"E:\data\asdg\register_sets_src")
EXPLORE = Path(r"E:\data\asdg\explore_public")  # v6.9: the exploration lane's copies
SCRIPT = "arcs/audit/src_register/reduce_v68.py"
SUFFIX = ".reduced_v68.json"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------------------------------------- the columns each builder reads
# (each a column rule on the declared header row, returning the original column positions the builder reads; asserted)
def cols_gandal2018(h: list) -> list[int]:
    """s_build.Sources.gandal: DGE's 'ensembl_gene_id', 'gene_name', 'ASD.log2FC', 'ASD.fdr' (h.index, first occurrence)."""
    return sorted({h.index(c) for c in ("ensembl_gene_id", "gene_name", "ASD.log2FC", "ASD.fdr")})


def cols_polioudakis(h: list) -> list[int]:
    """s_build.Sources.polioudakis: the first three columns, asserted 'Ensembl', 'Gene', 'Cluster'."""
    assert list(h[:3]) == ["Ensembl", "Gene", "Cluster"]
    return [0, 1, 2]


def cols_satterstrom(h: list) -> list[int]:
    """s_build.Sources.satterstrom: '102_ASD''s 'gene' and 'ensembl_gene_id'."""
    return sorted({h.index("gene"), h.index("ensembl_gene_id")})


def cols_lake(h: list) -> list[int]:
    """s_build.Sources.lake: the 'All Clusters' block (header row 4) -- its gene column and its cluster column (+ 6)."""
    j = [k for k, x in enumerate(h) if x == "All Clusters"]
    assert len(j) == 1
    return [j[0], j[0] + 6]


def cols_gene_level(h: list) -> list[int]:
    """fetch_v66.gandal_gene_level: Gene_Level's 'ensembl_gene_id', 'WGCNA_module', 'external_gene_name', 'hgnc_symbol'."""
    return sorted({h.index(c) for c in ("ensembl_gene_id", "WGCNA_module", "external_gene_name", "hgnc_symbol")})


def cols_genemodules(h: list) -> list[int]:
    """s_build_v66 (Pagani): GeneModules' module name (column 1), the whole-cortex / regional ASD FDR columns and the logFC column
    before each."""
    fc = [j for j, x in enumerate(h) if x == "Whole.Cortex_ASD_FDR" or (x and x.startswith("ASD_BA") and x.endswith("_FDR"))]
    return sorted({0} | set(fc) | {j - 1 for j in fc})


def cols_sanders2019(h: list) -> list[int]:
    """fetch_v66.sanders_flags: 'S1 single gene RGDs''s symbol, hgnc_id, entrez_id, ensembl_gene_id, ASD65, DDD93, CHD253."""
    return sorted({h.index(c) for c in ("symbol", "hgnc_id", "entrez_id", "ensembl_gene_id", "ASD65", "DDD93", "CHD253")})


def cols_p13(h: list) -> list[int]:
    """s_build.Sources.parikshak2013 (v6.7): h[0] 'ENSEMBL GENE ID', h[1] 'Gene Symbol', h[6] 'Module Label'."""
    assert h[0] == "ENSEMBL GENE ID" and h[1] == "Gene Symbol" and h[6] == "Module Label"
    return [0, 1, 6]


def cols_p16(h: list) -> list[int]:
    """s_build.Sources.parikshak2016 (v6.7): 'ENSEMBL ID', 'HGNC Symbol', 'log2(FC) ASD vs CTL', index 10 (asserted to start
    'FDR-adjusted P value, ASD vs C'), 'WGCNA Module Label' (h.index: the first occurrence, as the builder read them)."""
    ix = [h.index("ENSEMBL ID"), h.index("HGNC Symbol"), h.index("log2(FC) ASD vs CTL"), 10, h.index("WGCNA Module Label")]
    assert str(h[10]).startswith("FDR-adjusted P value, ASD vs C")
    assert len(set(ix)) == 5
    return ix


VEL_S4_COLS = ["Cell type", "gene ID", "Gene name", "Gene biotype", "Fold change", "Sample fold change", "q value"]


def cols_velmeshev(h: list) -> list[int]:
    """v6.9: ASD_DEGs' first seven columns, asserted equal to the exploration ingest's S4_COLS (ingest_celltype_velmeshev2019.py
    reads them by name; s_extract.velmeshev reads 'Cell type', 'gene ID', 'Gene name', 'Fold change', 'q value')."""
    assert [str(x).strip() for x in h[:7]] == VEL_S4_COLS
    return list(range(7))


def cols_lake_blocks(h: list) -> list[int]:
    """v6.9: Table S3's block-name row (row 4): the seven columns under each block name (fetch_celltype_lake2018.py reads every
    block's seven columns and the title in column 2; fetch_celltype_seidlitz2020.py reads the 'All Clusters' block's gene and
    cluster columns). Seven blocks, 'All Clusters' first at column 2, asserted."""
    starts = [j for j, x in enumerate(h) if x is not None]
    assert len(starts) == 7 and starts[0] == 1 and h[1] == "All Clusters"
    return sorted({j + k for j in starts for k in range(7)})


# key -> the original (folder, file relative to it, the sha256 the builders pin), its reader, the sheets kept with their header
# row (0-based; 'find:<text>' = the first of the guard's rows whose column 1 reads <text>) and column rule ('whole' = every
# column), and what reads it. 'zip_names': a zip of workbooks of which the builders read SHEET NAMES only -- kept: the names.
ORIGINALS = {
    # round 1 of v6.8 (B S2): the three workbooks the v6.7 re-check named
    "kang2011": {"folder": "kang2011", "file": "41586_2011_BFnature10523_MOESM50_ESM.xls",
                 "sha": "b2bd90951735c6db29070c774aa0c6d65158e7adc3cdd7e00da440e6286a673e", "reader": "xlrd",
                 "keep": [("Supple Table 9.", 1, "whole")], "read_by": "s_extract.py kang_modules"},
    "parikshak2013": {"folder": "parikshak2013", "file": "NIHMS545068-supplement-02.xlsx",
                      "sha": "0ba7494ac7a0c883e97e4f571d0a3ed6e15a49b411b0f31d581e26d1ca94bfd2", "reader": "openpyxl",
                      "keep": [("TableS1A", 2, cols_p13)], "read_by": "s_build.py Sources.parikshak2013"},
    "parikshak2016": {"folder": "parikshak2016", "file": "NIHMS1050915-supplement-SuppTable2.xlsx",
                      "sha": "99faa2965932acf1a0cf1638e3d2812c808109a302904d80ba9acbb99550bf28", "reader": "openpyxl",
                      "keep": [("TableS2a", 1, cols_p16)], "read_by": "s_build.py Sources.parikshak2016"},
    # round 2 of v6.8 (the orchestrator under the operator's standing delegation, on round 1's report): every flagged workbook a
    # register builder reads, reduced by one rule to exactly the sheets and columns the builders read
    "gandal2018": {"folder": "gandal2018_science362", "file": "NIHMS1007359-supplement-Table_S1.xlsx",
                   "sha": "e6f9c6ebab41974972f55af09708d565e3fb658e4dc1a6e6e194bed54726ce72", "reader": "openpyxl",
                   "keep": [("DGE", 0, cols_gandal2018)], "read_by": "s_build.py Sources.gandal"},
    "polioudakis2019": {"folder": "polioudakis2019", "file": "NIHMS1534343-supplement-5.xlsx",
                        "sha": "bfd5778a54807a395aea6b4e6b881c5158dcdc25c1d023693e09666f155b9dcb", "reader": "openpyxl",
                        "keep": [("Cluster enriched genes", 0, cols_polioudakis)], "read_by": "s_build.py Sources.polioudakis"},
    "satterstrom2020": {"folder": "satterstrom2020", "file": "NIHMS1569306-supplement-Table_S2.xlsx",
                        "sha": "f7fc4fe13a768d217577df85fc866a0cff941c29ab383456aab32b0000c279f7", "reader": "openpyxl",
                        "keep": [("102_ASD", 0, cols_satterstrom)], "read_by": "s_build.py Sources.satterstrom"},
    "lake2018": {"folder": "lake2018", "file": "41587_2018_BFnbt4038_MOESM11_ESM.xlsx",
                 "sha": "6960f9aefa7397c4814cd3a6b9e9ac4b2ee137d4d1fac0f36d6b48cdba78ec85", "reader": "openpyxl",
                 "keep": [("Table S3", 3, cols_lake)], "read_by": "s_build.py Sources.lake"},
    "gandal2022_moesm7": {"folder": "gandal2022_nature611", "file": "41586_2022_5377_MOESM7_ESM.xlsx",
                          "sha": "a48802c835c07e872bf3f30730a304bc62e3fd60782ef80b7e1df5b78d4c03e5", "reader": "openpyxl",
                          "keep": [("Gene_Level", 0, cols_gene_level)],
                          "read_by": "fetch_v66.py gandal_gene_level (its extract); s_build_v66.py (sha256)"},
    "gandal2022_moesm8": {"folder": "gandal2022_nature611", "file": "41586_2022_5377_MOESM8_ESM.xlsx",
                          "sha": "d746b3ed5336987c5e2b1415b5ccd7ac42d4bef57b06222d87fdd7691ef3d22f", "reader": "openpyxl",
                          "keep": [("GeneModules", 1, cols_genemodules)], "read_by": "s_build_v66.py (Pagani's DE modules)"},
    "sanders2019": {"folder": "sanders2019_rgd", "file": "NIHMS1754502-supplement-Tables_S1__S2__S4.xlsx",
                    "sha": "9848de1d41925218a090f4275f91f20d170d1fd9fd7dd1cf258b484ca37045a1", "reader": "openpyxl",
                    "keep": [("S1 single gene RGDs", "find:symbol", cols_sanders2019)],
                    "read_by": "fetch_v66.py sanders_flags (its extract); s_build_v66.py (sha256)"},
    "pfenning2014": {"folder": "pfenning2014_vocal", "file": "science_download/pfenning-tables-s1-to-s8.zip",
                     "sha": "9a7037b135e9848cc342b74d1ff3d8791782fc3e397e1926ff159ae570da616f", "reader": "zip_names",
                     "keep": [], "read_by": "s_build_v66.py (vocal learning, R-e: the workbooks' sheet names only)"},
    # v6.9 (S2-residual of the orchestrator's skeptic re-check): the exploration lane's copies, by the same rule
    "velmeshev2019": {"root": EXPLORE, "folder": "celltype_velmeshev2019/pmc_author_manuscript_suppl",
                      "file": "NIHMS1053005-supplement-Data_S4.xls", "round": "v6.9",
                      "sha": "53c9b41814c829ef578137385892926c9d3db54afadd404c85b9441117348e12", "reader": "xlrd",
                      "keep": [("ASD_DEGs", 0, cols_velmeshev)],
                      "read_by": "s_extract.py velmeshev (5 columns); explore ingest_celltype_velmeshev2019.py (ASD_DEGs, "
                                 "7 columns; the sheet names and dimensions from "
                                 "explore/discovery/data_manifests/celltype_velmeshev2019_S4_dimensions.json)"},
    "lake2018_explore": {"root": EXPLORE, "folder": "celltype_lake2018/journal_esm",
                         "file": "41587_2018_BFnbt4038_MOESM11_ESM.xlsx", "round": "v6.9",
                         "sha": "6960f9aefa7397c4814cd3a6b9e9ac4b2ee137d4d1fac0f36d6b48cdba78ec85", "reader": "openpyxl",
                         "keep": [("Table S3", 3, cols_lake_blocks)],
                         "read_by": "explore fetch_celltype_lake2018.py (sheet names; Table S3's seven blocks) and "
                                    "fetch_celltype_seidlitz2020.py (Table S3's 'All Clusters' gene and cluster columns)"},
}


def reduced_path(key: str) -> Path:
    o = ORIGINALS[key]
    return o.get("root", SRC) / o["folder"] / (o["file"] + SUFFIX)


def original_path(key: str) -> Path:
    o = ORIGINALS[key]
    return o.get("root", SRC) / o["folder"] / o["file"]


def key_of(path: Path) -> str | None:
    """the ORIGINALS key of an original's path (None if it is not one)."""
    for k in ORIGINALS:
        if original_path(k).resolve() == Path(path).resolve():
            return k
    return None


# ---------------------------------------------------------------------------------------------- JSON cell encoding (exact)
def _enc(v):
    if v is None or isinstance(v, (str, bool, int)):
        return v
    if isinstance(v, float):
        assert math.isfinite(v), "non-finite float"
        return v
    if isinstance(v, _dt.datetime):
        return {"$datetime": v.isoformat()}
    if isinstance(v, _dt.date):
        return {"$date": v.isoformat()}
    if isinstance(v, _dt.time):
        return {"$time": v.isoformat()}
    raise TypeError("cell type %s not encodable" % type(v).__name__)


def _dec(v):
    if isinstance(v, dict):
        if "$datetime" in v:
            return _dt.datetime.fromisoformat(v["$datetime"])
        if "$date" in v:
            return _dt.date.fromisoformat(v["$date"])
        if "$time" in v:
            return _dt.time.fromisoformat(v["$time"])
        raise ValueError("unknown cell encoding")
    return v


def _same(a, b) -> bool:
    return type(a) is type(b) and a == b


# ---------------------------------------------------------------------------------------------- reading a reduction
def load(path: Path, sha: str, original_sha: str) -> dict:
    """a reduction, its sha256 and the original's sha256 it records asserted; cells decoded to their Python types."""
    got = sha256(path)
    assert got == sha, "%s: sha256 %s != pinned %s" % (path.name, got, sha)
    rec = json.loads(path.read_text(encoding="utf-8"))
    assert rec["original"]["sha256"] == original_sha, "%s does not record the pinned original" % path.name
    for k in rec["kept"]:
        k["rows"] = [[_dec(v) for v in r] for r in k["rows"]]
    return rec


def rows(rec: dict, sheet: str, declared=None, header_row: int | None = None, label: str = "") -> list[tuple]:
    """the kept sheet's rows at their ORIGINAL column positions (v6.8 round 2: a kept column sits where it stood in the original,
    every column not kept reads empty -- None, or '' for an xlrd reduction -- so a builder's indexing is the original's), through
    the privacy guard: the guard classifies the reduction's own content; if that is identifier-bearing the builder must declare
    its columns (a header row inside the guard's rows), else the read is refused; declared columns are checked either way."""
    ks = [k for k in rec["kept"] if k["sheet"] == sheet]
    assert len(ks) == 1, "%s: sheet %r not kept in the reduction" % (label, sheet)
    k = ks[0]
    v = G.classify(k["rows"][:G.GUARD_ROWS], k["n_cols_kept"])
    if v["identifier_bearing"] and (declared is None or header_row is None or header_row >= G.GUARD_ROWS):
        raise G.Refused("REFUSED: %s reduction sheet '%s' is identifier-bearing (rule %s) and the builder declared no columns"
                        % (label, sheet, v["rules"]))
    cols, n = k["columns_kept"], k["n_cols_original"]
    if cols == list(range(n)):
        out = [tuple(r) for r in k["rows"]]
    else:
        fill = "" if rec["reader"].startswith("xlrd") else None
        out = []
        for r in k["rows"]:
            full = [fill] * n
            for i, j in enumerate(cols):
                full[j] = r[i]
            out.append(tuple(full))
    if declared is not None:
        keep = set(G._declared_positions(list(out[header_row]), declared, label, sheet))
        if v["identifier_bearing"]:
            out = [tuple(x if j in keep else None for j, x in enumerate(r)) for r in out]
    return out


def zip_sheet_names(rec: dict) -> dict:
    """a 'zip_names' reduction: {workbook member: its sheet names in workbook order} -- all the builders read of it."""
    return {m: list(v) for m, v in rec["zip_sheet_names"].items()}


# ---------------------------------------------------------------------------------------------- reduce
def _find_header(ws, text: str, label: str) -> int:
    """the 0-based index of the first of the guard's rows whose column 1 reads `text` (column 1 alone is read to find it)."""
    col1 = G.read_openpyxl(ws, declared=lambda h: [0], header_row=0, label=label)
    hit = [i for i, r in enumerate(col1[:G.GUARD_ROWS]) if r and r[0] == text]
    assert hit, "%s: no header row '%s' in the guard's rows" % (label, text)
    return hit[0]


def reduce_one(key: str) -> dict:
    o = ORIGINALS[key]
    folder, name, osha, reader = o["folder"], o["file"], o["sha"], o["reader"]
    src = original_path(key)
    got = sha256(src)
    assert got == osha, "%s: sha256 %s != pinned %s" % (name, got, osha)
    sheets, kept = [], []
    want = {s: (h, rule) for s, h, rule in o["keep"]}
    if reader == "xlrd":
        import xlrd
        b = xlrd.open_workbook(str(src), on_demand=True)
        for n in b.sheet_names():
            sh = b.sheet_by_name(n)
            v = G.classify_xlrd(sh)
            e = {"sheet": n, "n_rows": sh.nrows, "n_cols": sh.ncols, "guard": v["rules"] or "clean"}
            if o.get("round") == "v6.9":  # v6.9 (C1): xlrd's nrows / ncols as before, and the populated width
                e["n_cols_populated"] = v["n_cols"]
            sheets.append(e)
            if n in want:
                hrow, rule = want[n]
                if rule == "whole":
                    assert not v["identifier_bearing"], "an xls sheet is kept whole only when clean"
                    cols = list(range(sh.ncols))
                    cv = G.xlrd_cell_reader(sh, verdict=v, label=name)
                else:  # v6.9: declared columns (a column rule on the header row, read programmatically, never printed)
                    cols = G._declared_positions(sh.row_values(hrow), rule, name, n)
                    cv = G.xlrd_cell_reader(sh, declared=rule, header_row=hrow, label=name, verdict=v)
                ctypes = {sh.cell_type(r, c) for r in range(sh.nrows) for c in cols}
                assert ctypes <= {xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_TEXT, xlrd.XL_CELL_NUMBER, xlrd.XL_CELL_BLANK}, ctypes
                body = [[cv(r, c) for c in cols] for r in range(sh.nrows)]
                kept.append((n, hrow, rule, cols, sh.ncols, body))
            b.unload_sheet(n)
        b.release_resources()
    elif reader == "openpyxl":
        import openpyxl
        wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
        for ws in wb.worksheets:
            v = G.classify_openpyxl(ws)
            e = {"sheet": ws.title, "n_rows": ws.max_row, "n_cols": v["n_cols"], "guard": v["rules"] or "clean"}
            if o.get("round") == "v6.9":  # v6.9 (C1): n_cols is the populated width; the dimension tag beside it
                e["n_cols_dimension_tag"] = v["n_cols_dimension_tag"]
            sheets.append(e)
            if ws.title in want:
                hrow, rule = want[ws.title]
                if isinstance(hrow, str):
                    hrow = _find_header(ws, hrow.split(":", 1)[1], name)
                full = G.read_openpyxl(ws, declared=rule, header_row=hrow, label=name, verdict=v)
                cols = rule(list(full[hrow]))
                body = [[r[j] if j < len(r) else None for j in cols] for r in full]
                kept.append((ws.title, hrow, rule, cols, v["n_cols"], body))
        wb.close()
    else:  # zip_names: the sheet names of every workbook in the zip (all the builders read of it)
        import io
        import zipfile
        import openpyxl
        names = {}
        with zipfile.ZipFile(src) as z:
            members = sorted(z.namelist())
            for m in [n for n in members if n.lower().endswith(".xlsx")]:
                wb = openpyxl.load_workbook(io.BytesIO(z.read(m)), read_only=True, data_only=True)
                names[m] = [ws.title for ws in wb.worksheets]
                for ws in wb.worksheets:
                    v = G.classify_openpyxl(ws)
                    sheets.append({"member": m, "sheet": ws.title, "n_rows": ws.max_row, "n_cols": v["n_cols"],
                                   "guard": v["rules"] or "clean"})
                wb.close()
    for s, _, _ in o["keep"]:
        assert [x["sheet"] for x in sheets].count(s) == 1, s
    rnd = ("register DRAFT v6.9 (S2-residual): the reduction of the exploration-lane copy %s/%s to exactly what the register "
           "builders and the exploration scripts read" if o.get("round") == "v6.9" else
           "register DRAFT v6.8 (B S2): the reduction of %s/%s to exactly what the register builders read")
    rec = {"what": ((rnd + " -- %s. Every "
                    "other sheet and column was dropped unread beyond the guard's first %d rows (never printed). The original "
                    "is deleted after the builders' outputs were shown byte-identical; its sha256, byte size and sheet names and "
                    "dimensions are kept below.") % (folder, name, (
                        "the sheet names of its workbooks (no cell is read)" if reader == "zip_names" else
                        "; ".join("sheet '%s', %s" % (s, "whole" if r == "whole" else "the declared columns") for s, _, r in
                                  o["keep"])), G.GUARD_ROWS)),
           "script": SCRIPT, "guard": {"module": "arcs/audit/src_register/privacy_guard.py", "rows": G.GUARD_ROWS,
                                        "wide_cols": G.WIDE_COLS},
           "reader": ("xlrd cell_value (text -> str, number -> float, empty -> '')" if reader == "xlrd" else
                      "openpyxl values_only (read-only, data_only)" if reader == "openpyxl" else
                      "zip member names and openpyxl sheet titles (no cell kept)"),
           "read_by": o["read_by"],
           "original": {"folder": folder, "file": name, "sha256": osha, "bytes": src.stat().st_size, "sheets": sheets},
           "kept": []}
    for s, hrow, rule, cols, ncol, body in kept:
        vk = G.classify(body[:G.GUARD_ROWS], len(cols))
        rec["kept"].append({"sheet": s, "header_row": hrow, "n_rows": len(body), "n_cols_original": ncol, "columns_kept": cols,
                            "n_cols_kept": len(cols),
                            "header_texts": ([str(x) for x in body[hrow]] if rule != "whole" else None),
                            "guard_of_reduction": vk["rules"] or "clean", "rows": [[_enc(x) for x in r] for r in body]})
    if reader == "zip_names":
        rec["original"]["members"] = members
        rec["zip_sheet_names"] = names
    out = reduced_path(key)
    txt = json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    out.write_bytes(txt.encode("utf-8"))
    assert out.read_bytes().decode("utf-8") == txt
    back = load(out, sha256(out), osha)
    for (s, _, _, _, _, body), k in zip(kept, back["kept"]):
        assert len(k["rows"]) == len(body) and all(
            len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b)) for a, b in zip(k["rows"], body)), "read-back differs"
    return {"key": key, "original": name, "bytes": rec["original"]["bytes"],
            "sheets": [((s.get("member", "") + "::" if s.get("member") else "") + s["sheet"], s["n_rows"], s["n_cols"],
                        s["guard"]) for s in sheets],
            "kept": [(k["sheet"], k["n_rows"], k["n_cols_kept"], k["columns_kept"] if k["n_cols_kept"] < 30 else "...",
                      k["guard_of_reduction"]) for k in rec["kept"]],
            "reduced": out.name, "reduced_sha256": sha256(out)}


# ---------------------------------------------------------------------------------------------- the inventory (every workbook)
VEL = Path(r"E:\data\asdg\explore_public\celltype_velmeshev2019\pmc_author_manuscript_suppl\NIHMS1053005-supplement-Data_S4.xls")
WORKBOOKS = [  # (path, zip member or None, what the builders do with it, the sheets they read)
    (VEL, None, "s_extract.py velmeshev (read; only this sheet is opened)", ["ASD_DEGs"]),
    (SRC / "darnell2011_fmrp" / "NIHMS314927-supplement-Suppl_Table_S2A-C.xls", None,
     "s_extract.py darnell_s2a (read; every sheet guarded); s_build_v66.py (sha256)", ["Table S2A"]),
    (SRC / "voineagu2011" / "NIHMS313080-supplement-2.xls", None, "s_build_v66.py (sha256 only; kept whole)", []),
    (SRC / "gandal2018_science362" / "NIHMS1007359-supplement-Table_S1.xlsx", None, "s_build.py gandal (read)", ["DGE"]),
    (SRC / "polioudakis2019" / "NIHMS1534343-supplement-5.xlsx", None, "s_build.py polioudakis (read)",
     ["Cluster enriched genes"]),
    (SRC / "satterstrom2020" / "NIHMS1569306-supplement-Table_S2.xlsx", None, "s_build.py satterstrom (read)", ["102_ASD"]),
    (SRC / "sanders2015" / "NIHMS723829-supplement-8.xlsx", None, "s_build.py sanders (read)", ["TADA_Scores"]),
    (SRC / "lake2018" / "41587_2018_BFnbt4038_MOESM11_ESM.xlsx", None,
     "s_build.py lake (read: Table S3 in declared columns -- the 'All Clusters' block's gene and cluster columns)", ["Table S3"]),
    (SRC / "gandal2022_nature611" / "41586_2022_5377_MOESM7_ESM.xlsx", None,
     "fetch_v66.py gandal_gene_level (read only when its extract is absent); s_build_v66.py (sha256); kept whole",
     ["Gene_Level"]),
    (SRC / "gandal2022_nature611" / "41586_2022_5377_MOESM8_ESM.xlsx", None,
     "s_build_v66.py (read: GeneModules in declared columns); kept whole", ["GeneModules"]),
    (SRC / "sanders2019_rgd" / "NIHMS1754502-supplement-Tables_S1__S2__S4.xlsx", None,
     "fetch_v66.py sanders_flags (read in declared columns only when its extract is absent); s_build_v66.py (sha256); kept "
     "whole", ["S1 single gene RGDs"]),
    (SRC / "parikshak2016" / "NIHMS1050915-supplement-SuppTable4.xlsx", None, "s_build_v66.py (sha256 only); kept whole", []),
    (SRC / "syngo_1.2_20231201" / "syngo1.2_complete_data.zip", "genes.xlsx", "s_build_v66.py syngo (read)", ["Sheet1"]),
    (SRC / "syngo_1.2_20231201" / "syngo1.2_complete_data.zip", "annotations.xlsx", "not read (in the pinned zip)", []),
    (SRC / "syngo_1.2_20231201" / "syngo1.2_complete_data.zip", "ontologies.xlsx", "not read (in the pinned zip)", []),
] + [(SRC / "pfenning2014_vocal" / "science_download" / "pfenning-tables-s1-to-s8.zip", m,
      "s_build_v66.py (sheet names only; no cell read); kept whole", []) for m in (
          "SuppTable1-Region_Abbreviations V25.xlsx", "SuppTable2-GeneMapping V25.xlsx",
          "SuppTable3-Finch_Gene_Specializations V25.xlsx", "SuppTable4-CrossSpeciesLMCSimiarlity V25.xlsx",
          "SuppTable5-GeneOntologyResults V25.xlsx", "SuppTable6-CrossSpecies_Specializations V25.xlsx",
          "SuppTable7-Proteomics V25.xlsx", "SuppTable8-InsituClone IDs V25.xlsx")]


def inventory(out: Path) -> dict:
    """the privacy guard's verdict on every sheet of every workbook the register builders read or pin (names, dimensions and
    rule letters only; the Velmeshev workbook's other sheets are named, never opened), plus the three deleted originals from
    their reductions. Written to register_maps/privacy_inventory_v68.json."""
    import io
    import zipfile
    try:
        import xlrd  # in the programme venv since v6.9 (C4); absent before
    except ImportError:
        xlrd = None
    prev = {}  # an earlier inventory by the same guard: an unchanged .xls keeps its verdicts when xlrd is absent (venv run)
    if out.exists():
        old = json.loads(out.read_text(encoding="utf-8"))
        if old.get("guard_sha256") == sha256(Path(G.__file__)):
            prev = {(w["workbook"], w["sha256"]): w["sheets"] for w in old["workbooks"]}
    recs = []
    for path, member, role, read in WORKBOOKS:
        k_ = key_of(path)
        if k_ is not None and reduced_path(k_).exists():
            continue  # reduced (v6.8): recorded below from its reduction
        sheets = []
        if path.suffix == ".xls" and xlrd is None:
            sheets = prev[(str(path), sha256(path))]  # KeyError: no verdict by this guard for this file -> run with xlrd
        elif path.suffix == ".xls":  # v6.9: every sheet classified (the Velmeshev per-individual sheet included, C S2-residual)
            b = xlrd.open_workbook(str(path), on_demand=True)
            for n in b.sheet_names():
                v = G.classify_xlrd(b.sheet_by_name(n))
                sheets.append({"sheet": n, "n_rows": v["n_rows"], "n_cols": v["n_cols"], "n_cols_dimension_tag":
                               v["n_cols_dimension_tag"], "guard": v["rules"] or "clean"})
                b.unload_sheet(n)
            b.release_resources()
        else:
            import openpyxl
            src = io.BytesIO(zipfile.ZipFile(path).read(member)) if member else path
            wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
            for ws in wb.worksheets:
                v = G.classify_openpyxl(ws)
                sheets.append({"sheet": ws.title, "n_rows": v["n_rows"], "n_cols": v["n_cols"], "n_cols_dimension_tag":
                               v["n_cols_dimension_tag"], "guard": v["rules"] or "clean"})
            wb.close()
        flagged = [s["sheet"] for s in sheets if s["guard"] not in ("clean", "not opened")]
        recs.append({"workbook": str(path) + ("::" + member if member else ""), "sha256": sha256(path), "role": role,
                     "sheets_read": read, "sheets": sheets, "identifier_bearing_sheets": flagged,
                     "read_sheets_identifier_bearing": [s for s in read if s in flagged]})
    for key in ORIGINALS:
        if not reduced_path(key).exists():
            continue
        rec = json.loads(reduced_path(key).read_text(encoding="utf-8"))
        o = rec["original"]
        recs.append({"workbook": str(original_path(key)), "sha256": o["sha256"],
                     "role": "%s (%s); the builders read its reduction %s (%s)" % (
                         "DELETED" if not original_path(key).exists() else "REDUCED, original present",
                         "v6.9, S2-residual" if ORIGINALS[key].get("round") == "v6.9" else "v6.8, B S2",
                         reduced_path(key).name, ORIGINALS[key]["read_by"]),
                     "sheets_read": [k["sheet"] for k in rec["kept"]] or ["(sheet names only)"],
                     "sheets": o["sheets"],
                     "identifier_bearing_sheets": [(s.get("member", "") + "::" if s.get("member") else "") + s["sheet"]
                                                   for s in o["sheets"] if s["guard"] != "clean"],
                     "kept": [{"sheet": k["sheet"], "columns_kept": k["columns_kept"], "n_rows": k["n_rows"],
                               "guard_of_reduction": k["guard_of_reduction"],
                               "guard_of_reduction_now": G.classify([[_dec(x) for x in r] for r in k["rows"][:G.GUARD_ROWS]],
                                                                    k["n_cols_kept"])["rules"] or "clean"}
                              for k in rec["kept"]],
                     "widths_note": ("widths of the deleted original recorded from its dimension tag (openpyxl max_column / "
                                     "xlrd ncols) by v6.8; the populated width may be smaller (v6.9 C1)"
                                     if rec.get("guard", {}).get("rows", 6) < 20 else "populated widths (v6.9)"),
                     "read_sheets_identifier_bearing": [], "reduction_sha256": sha256(reduced_path(key))})
    doc = {"what": ("register DRAFT v6.8 (B S2): the privacy guard's verdict (privacy_guard.py; W = wider than %d columns, N = "
                    "identifier wording, V = an identifier-valued cell, in the first %d rows) on every sheet of every workbook "
                    "the register builders read or pin -- sheet names, dimensions and rule letters only" % (G.WIDE_COLS,
                                                                                                         G.GUARD_ROWS)),
           "script": SCRIPT + " inventory", "guard_sha256": sha256(Path(G.__file__)), "workbooks": recs}
    txt = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    out.write_bytes(txt.encode("utf-8"))
    assert out.read_bytes().decode("utf-8") == txt
    return doc


def delete_one(key: str, reduced_sha: str | None = None) -> str:
    name, osha = ORIGINALS[key]["file"], ORIGINALS[key]["sha"]
    src, red = original_path(key), reduced_path(key)
    if not src.exists():
        return "%s: already deleted (sha256 %s kept)" % (name, osha)
    assert sha256(src) == osha
    rec = json.loads(red.read_text(encoding="utf-8"))
    assert rec["original"]["sha256"] == osha and rec["original"]["bytes"] == src.stat().st_size
    if reduced_sha:
        assert sha256(red) == reduced_sha
    src.unlink()
    assert not src.exists()
    return "%s: deleted (sha256 %s, %d B kept in %s)" % (name, osha, rec["original"]["bytes"], red.name)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    keys = [a for a in sys.argv[2:] if not a.startswith("--")] or list(ORIGINALS)
    assert all(k in ORIGINALS for k in keys), keys
    if cmd == "reduce":  # only originals still present (a deleted original's reduction is never rewritten)
        for k in keys:
            if not original_path(k).exists():
                print("%s: original deleted; its reduction is kept as it is" % ORIGINALS[k]["file"])
                continue
            r = reduce_one(k)
            print("%s: %d B; sheets (name, rows, cols, guard): %s" % (r["original"], r["bytes"], r["sheets"]))
            print("  kept (sheet, rows, cols, columns, guard of the reduction) %s -> %s (sha256 %s)"
                  % (r["kept"], r["reduced"], r["reduced_sha256"]))
    elif cmd == "delete":
        for k in keys:
            print(delete_one(k))
    elif cmd == "inventory":
        o = Path(__file__).resolve().parents[1] / "register_maps" / "privacy_inventory_v68.json"
        d = inventory(o)
        for w in d["workbooks"]:
            print("%s\n  role: %s\n  identifier-bearing sheets: %s; of them read: %s" % (
                w["workbook"].replace(str(SRC) + "\\", ""), w["role"],
                [(s["sheet"], s["n_rows"], s["n_cols"], s["guard"]) for s in w["sheets"] if s["sheet"] in w["identifier_bearing_sheets"]],
                w["read_sheets_identifier_bearing"]))
        print("written", o.name, sha256(o))
    else:
        print(__doc__)
