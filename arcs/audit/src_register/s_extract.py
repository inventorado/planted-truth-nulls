"""A1 pre-freeze S-build, stage 1 (register §1.6, §1.10 (0)): plain-text extracts of the few source tables that are
not machine-readable by the programme venv (PDF, legacy .xls, .docx). Run with the system Python 3.13 that carries
PyMuPDF / xlrd / python-docx (the programme venv has none of them):

    C:\\Python313\\python.exe -X utf8 arcs\\audit\\src_register\\s_extract.py

Reads ONLY the named table / sheet / page of each source (never another sheet), asserts every input's sha256, and
writes deterministic UTF-8 TSVs under E:\\data\\asdg\\register_sets_src\\<source>\\extract\\. Prints counts and hashes
only. Stage 2 (s_build.py, programme venv) asserts the extract hashes written to extract_manifest.json.

Extracts:
  segura2025_tables/extract/tableS7_terms.tsv   Segura 2025 MOESM2 p. 39 (Table S7): the GO BP term names in printed
                                                order; the 77-row / 78-term parse repaired (row 1 holds two terms
                                                joined by ' / '; one term's numbers wrap to the next line). Term names
                                                only - no value of the table is kept.
  velmeshev2019/extract/data_s4_ASD_DEGs.tsv   Velmeshev 2019 Data S4, sheet 'ASD_DEGs' only (group-level cell-type
                                                DEGs); the per-patient sheet is never opened.
  shin2018/extract/tableS1_panels.tsv          Shin 2018 Table S1 (docx in the supplement zip): 9 cell-type panels.
  grove2019_magma/extract/table10_top25.tsv    Grove 2019 Supplementary Table 10 (PDF p. 68): the 25 gene names.
  kang2011/extract/table9_modules.tsv          Kang 2011 Supplementary Table 9: module id, colour, size (documents that
                                                the table holds no module-membership list).
  spark2018/extract/spark_single_genes.tsv     (register v6.6, B2) the SPARK gene list PDF p. 4 'The SPARK Gene List':
                                                the single genes (the printed column block right of the CNV column; a
                                                bracketed former name such as '(SUV420H1)' is not a gene); asserted
                                                equal in number to the printed '153 single genes'.
  voineagu2011/extract/table14_M12_genes.tsv   (register v6.7 N1) Voineagu 2011 Supplementary Information: ONLY the
                                                pages of 'Supplementary Table 14. M12 module genes and associated GWAS p
                                                values', located by that caption (p. 19) and followed while its symbol /
                                                p-value rows continue (pp. 19-23); gene symbols only. The PDF also holds
                                                per-individual tables: no other page is extracted or printed (the caption
                                                search and the p. 10 module-colour assertions are programmatic), and the
                                                PDF is deleted after the extract, its sha256 kept (DELETED_AFTER_EXTRACT);
                                                a later run re-reads the extract instead.
  darnell2011_fmrp/extract/tableS2A_842_targets.tsv  (register v6.7 N7) Darnell 2011 Table S2A 'FMRP Targets (842)': per
                                                target its 'Gene Symbol' (upper case), 'Symbol from mm9' (the mouse
                                                symbol) and mouse 'Entrez Gene ID'; every sheet passes the identifier-
                                                header guard first. (Table S2C's 'human gene symbol' column is filled for
                                                117 of the 842 only, so it is not used.)

Register DRAFT v6.8 (the orchestrator under the operator's standing delegation, 2026-09-29):
  B S2  every sheet this script reads passes privacy_guard.py (a sheet wider than 50 columns, or with identifier wording or an
        identifier-valued cell in its first 6 rows, is identifier-bearing: nothing of it is printed, only declared columns
        are read); Kang 2011 MOESM50 held four identifier-bearing sheets (Supplementary Tables 1-4) and was deleted after
        its gene-level reduction (reduce_v68.py: 'Supple Table 9.' whole) -- kang_modules reads the reduction; the
        original's sha256, bytes and sheet names + dimensions are recorded in extract_manifest.json ('originals_deleted_v68',
        with Parikshak 2013 supplement 02 and Parikshak 2016 Supplementary Table 2, read by s_build.py).
  C     the Voineagu extract's text_order column: v6.7 numbered rows with a list length read while the list grew (1, 3, 5
        ... restarting per page: 213 distinct values for 380 rows); fixed here (1 ... 380 in row order, the text order) --
        the stored extract is rewritten only by a run of that job (its folder is outside this session's authorisation;
        register 1.6). The S-build reads only its gene column.
  --only <job> [<job> ...]  runs those jobs and rewrites only their extracts and extract_manifest.json (the other entries
        are kept, their files asserted unchanged); --verify runs every job in memory, writes nothing and prints, per job,
        whether its output equals the stored extract.
  Round 2 (the orchestrator's decisions on round 1's report): the Voineagu extract rewritten by
        `env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src_register\\s_extract.py --only voineagu_table14_m12` (the
        programme venv: the job re-reads its extract and needs no PDF / xls / docx library, so those are imported only if
        present; an --only run keeps the full run's "python" / "libs" and records its own interpreter under "only_runs");
        "originals_deleted_v68" lists every workbook reduce_v68.py reduced (round 1 and round 2).
Register DRAFT v6.9 (the orchestrator's skeptic re-check, 2026-09-30):
  S2-residual  velmeshev reads the reduction of Data S4 ('ASD_DEGs' columns 1-7; reduce_v68.py key velmeshev2019) and the
        original is deleted; "originals_deleted_v68" also lists the two exploration-lane copies reduced in v6.9 (Velmeshev
        Data S4, the exploration copy of Lake 2018 MOESM11), each at its own path.
  C4    xlrd 2.0.2 is a declared addition to the programme venv (env/README.md): the .xls jobs (velmeshev, darnell_s2a_842,
        kang_table9_modules) and voineagu_table14_m12 run under the venv; segura_s7 / grove_table10 / spark_single_genes
        (PyMuPDF) and shin_tableS1 (python-docx) still need the system Python, which carries those libraries.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path

try:  # v6.8 round 2: absent in the programme venv, where only jobs needing none of them run (--only voineagu_table14_m12,
    import docx  # python-docx  #   which re-reads its extract; kang_table9_modules, which reads its reduction)
    import fitz  # PyMuPDF
except ImportError:
    docx = fitz = None
try:  # v6.9 (C4): xlrd 2.0.2 is a declared addition to the programme venv (env/README.md); imported on its own
    import xlrd
except ImportError:
    xlrd = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
import privacy_guard as G  # noqa: E402  register v6.8 (B S2)
import reduce_v68 as RV  # noqa: E402  register v6.8 (B S2): the gene-level reductions of the deleted originals

SRC = Path(r"E:\data\asdg\register_sets_src")
VELMESHEV_XLS = Path(r"E:\data\asdg\explore_public\celltype_velmeshev2019\pmc_author_manuscript_suppl"
                     r"\NIHMS1053005-supplement-Data_S4.xls")
INPUTS = {
    "segura_moesm2": (SRC / "segura2025_tables" / "41380_2025_3205_MOESM2_ESM.pdf",
                      "ff55ffe904838fe59d3575261639c0ca922e4c6cfa788e4f7df28c2459a1be93"),
    "velmeshev_s4": (VELMESHEV_XLS, "53c9b41814c829ef578137385892926c9d3db54afadd404c85b9441117348e12"),
    "shin_zip": (SRC / "shin2018" / "cercor_28_9_3267_s1.zip",
                 "3b1c30d9287c649f69073260e08bc7f5939c67c863b045f97bcf6b9a0cf225e2"),
    "grove_pdf": (SRC / "grove2019_magma" / "41588_2019_344_MOESM1_ESM.pdf",
                  "0de06bc6576481404a98e11702872620f924231e4dbfc1f04bf910a5e6b151e7"),
    "kang_xls": (SRC / "kang2011" / "41586_2011_BFnature10523_MOESM50_ESM.xls",
                 "b2bd90951735c6db29070c774aa0c6d65158e7adc3cdd7e00da440e6286a673e"),
    # register v6.6 (B2): the SPARK gene list (fetch_v66.py)
    "spark_pdf": (SRC / "spark2018" / "SPARK_gene_list.pdf", "16c6b1c170511bf050e73b047cd149e51e639b2db95a9963c8997ddc0c77ee76"),
    # register v6.7 N1 / N7 (fetch_v66.py)
    "voineagu_si_pdf": (SRC / "voineagu2011" / "NIHMS313080-supplement-1.pdf",
                        "59f2ded45c95b73af0f4c0152da530f2196d0b8e371ca7897d5444c4c6f9cfd5"),
    "darnell_s2_xls": (SRC / "darnell2011_fmrp" / "NIHMS314927-supplement-Suppl_Table_S2A-C.xls",
                       "30495d3d31e8bdf513cc45b222312dcf71652247b962a17198f256c70521cafb"),
}
# inputs holding per-individual material: deleted once their extract exists (v6.7 N1); sha256 kept above; a later run
# re-reads the extract (path) instead of the input
DELETED_AFTER_EXTRACT = {"voineagu_si_pdf": SRC / "voineagu2011" / "extract" / "table14_M12_genes.tsv"}
# register v6.8 (B S2): inputs deleted for privacy after their gene-level reduction (reduce_v68.py); the job reads the reduction,
# pinned here (its own record names the original's sha256, asserted equal to INPUTS)
REDUCED_V68 = {"kang_xls": ("kang2011", RV.reduced_path("kang2011"),
                            "a4575d50cf8f875307f030b9ab2af64cb208675e95ecfd4693e49e9e0acb4303"),
               # v6.9 (S2-residual): Velmeshev Data S4 reduced to 'ASD_DEGs' columns 1-7 (exploration-lane copy on E:)
               "velmeshev_s4": ("celltype_velmeshev2019", RV.reduced_path("velmeshev2019"),
                                "8fbd16ad114ca20b0a930edfafc1f1c5ad310573467b43c16f72d00ab59af68b")}
ID_HEADER = G.ID_WORDING  # v6.7's identifier-wording test, now one part of the v6.8 guard (privacy_guard.py)
SEGURA_NAMED = ["axonogenesis", "axonogenesis involved in innervation", "neuron projection morphogenesis",
                "dendritic spine morphogenesis", "axon extension", "axon guidance", "regulation of axonogenesis"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def tsv_text(header: list[str], rows: list[list]) -> str:
    return "\t".join(header) + "\n" + "".join("\t".join(str(x) for x in r) + "\n" for r in rows)


def write_tsv(path: Path, header: list[str], rows: list[list]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = tsv_text(header, rows)
    path.write_bytes(txt.encode("utf-8"))
    back = path.read_bytes().decode("utf-8")
    assert back == txt, f"read-back differs: {path}"
    return sha256(path)


NUM = re.compile(r"^[0-9.]+(/[0-9.]+)?$")


def segura_s7() -> list[list]:
    doc = fitz.open(str(INPUTS["segura_moesm2"][0]))
    page = doc[38]  # p. 39
    text = page.get_text()
    assert "Table S7. Genetic Ontology (GO) terms" in text, "p. 39 is not Table S7"
    words = page.get_text("words")  # x0, y0, x1, y1, word, block, line, wno
    hdr = [w for w in words if w[4] == "#"]
    assert len(hdr) == 1, "header '# genes' not unique"
    x_num, y_hdr = hdr[0][0], hdr[0][1]
    foot = [w for w in words if w[4].startswith("*Only")]
    assert len(foot) == 1
    y_foot = foot[0][1]
    lines: dict[int, list] = {}
    for w in words:
        if y_hdr + 5 < w[1] < y_foot - 1:
            lines.setdefault(round((w[1] + w[3]) / 2), []).append(w)
    rows = []  # (y, term_words, numeric_tokens, x_indent)
    for y in sorted(lines):
        ws = sorted(lines[y], key=lambda w: w[0])
        term = [w for w in ws if w[2] < x_num - 2]
        nums = [w[4] for w in ws if w[0] >= x_num - 2]
        assert all(NUM.match(t) for t in nums), f"non-numeric token in the value columns at y={y}"
        rows.append((y, " ".join(w[4] for w in term), nums, term[0][0] if term else None))
    # repair: a term line whose values wrapped to the next (term-less) line
    recs, i = [], 0
    while i < len(rows):
        y, term, nums, x = rows[i]
        assert term, f"value line without a term at y={y}"
        if len(nums) < 4 and i + 1 < len(rows) and not rows[i + 1][1]:
            nums = rows[i + 1][2] + nums
            i += 1
        assert len(nums) == 4, f"row '{term}' has {len(nums)} values"
        recs.append((term, nums, x))
        i += 1
    assert len(recs) == 77, f"{len(recs)} printed rows (expected 77)"
    out, order = [], 0
    for r, (term, nums, x) in enumerate(recs, 1):
        parts = [t.strip() for t in term.split(" / ")] if " / " in term else [term]
        assert len(parts) == len(nums[0].split("/")), f"row {r}: {len(parts)} names vs {nums[0]!r}"
        for p in parts:
            order += 1
            out.append([order, r, p, "named (SEG-C3a-g)" if p in SEGURA_NAMED else "other"])
    assert order == 78 and sum(o[3] != "other" for o in out) == 7, "78 terms / 7 named expected"
    return out


def velmeshev() -> list[list]:
    """v6.9 (S2-residual): read from the reduction of Data S4 ('ASD_DEGs' columns 1-7 as xlrd returned them: text -> str,
    number -> float, empty -> ''), through the guard with the five declared columns; the original is deleted (v6.8: the
    original's 'ASD_DEGs' through G.xlrd_cell_reader, the same cells)."""
    folder, p, h_ = REDUCED_V68["velmeshev_s4"]
    want = ["Cell type", "gene ID", "Gene name", "Fold change", "q value"]
    rows = RV.rows(RV.load(p, h_, INPUTS["velmeshev_s4"][1]), "ASD_DEGs", declared=want, header_row=0,
                   label="velmeshev Data S4 (reduction)")
    h = list(rows[0])
    idx = [h.index(c) for c in want]
    return [[str(r[j]).strip() for j in idx] for r in rows[1:]]


def shin() -> list[list]:
    z = zipfile.ZipFile(INPUTS["shin_zip"][0])
    d = docx.Document(io.BytesIO(z.read("TableS1.docx")))
    out = []
    for t in d.tables:
        assert [c.text.strip() for c in t.rows[0].cells] == ["Cell Type", "Gene Symbols"]
        for row in t.rows[1:]:
            ct, genes = row.cells[0].text.strip(), row.cells[1].text
            for g in [x.strip() for x in re.split(r"[,\s]+", genes) if x.strip()]:
                out.append([ct, g])
    return out


def grove() -> list[list]:
    doc = fitz.open(str(INPUTS["grove_pdf"][0]))
    t = doc[67].get_text()
    assert "Supplementary Table 10: Top 25 results from Magma" in t
    toks = [x.strip() for x in t.split("\n")]
    a = toks.index("Bonf P") + 1
    b = next(i for i, x in enumerate(toks) if x.startswith("Supplementary Table 11"))
    body = [x for x in toks[a:b] if x]
    assert len(body) == 250, len(body)
    return [[k + 1, body[10 * k]] for k in range(25)]


def kang_modules() -> list[list]:
    """v6.8 (B S2): read from the gene-level reduction of MOESM50 (its 'Supple Table 9.' as xlrd returned it: text -> str,
    number -> float, empty -> ''), through the guard with the three declared columns; the original is deleted."""
    folder, p, h_ = REDUCED_V68["kang_xls"]
    rows = RV.rows(RV.load(p, h_, INPUTS["kang_xls"][1]), "Supple Table 9.", declared=["Module", "Color", "Size"],
                   header_row=1, label="kang2011 MOESM50 (reduced)")
    h = list(rows[1])
    assert h[:3] == ["Module", "Color", "Size"], "Supple Table 9. header"
    seen, out = set(), []
    for r in range(2, len(rows)):
        m = str(rows[r][0]).strip()
        if m and m not in seen:
            seen.add(m)
            out.append([m, str(rows[r][1]).strip(), int(float(rows[r][2]))])
    return out


def spark() -> list[list]:
    """register v6.6 (B2): the SPARK gene list's single genes (p. 4): every word below the 'Single Genes' header, right of
    the CNV column and above the 'This list was updated' line; bracketed former names are not genes."""
    doc = fitz.open(str(INPUTS["spark_pdf"][0]))
    page = doc[3]
    text = page.get_text()
    assert "The SPARK gene list contains 153 single genes" in " ".join(text.split()), "p. 4 is not the SPARK gene list"
    words = page.get_text("words")
    single = [w for w in words if w[4] == "Single"]
    upd = [w for w in words if w[4] == "This"]
    assert len(single) == 1 and len(upd) == 1
    x0, y0, y1 = single[0][0] - 2, single[0][3], upd[0][1]
    body = sorted((w for w in words if w[0] >= x0 and y0 < w[1] < y1), key=lambda w: (round(w[0]), w[1]))
    genes = [w[4] for w in body if not (w[4].startswith("(") and w[4].endswith(")"))]
    assert all(re.match(r"^[A-Z0-9][A-Z0-9-]*$", g) for g in genes), [g for g in genes if not re.match(r"^[A-Z0-9-]+$", g)]
    assert len(genes) == len(set(genes)) == 153, len(genes)
    return [[k + 1, g] for k, g in enumerate(genes)]


def voineagu_table14() -> list[list]:
    """register v6.7 N1: Voineagu 2011 Supplementary Table 14 ('M12 module genes and associated GWAS p values'): the pages
    its caption locates, followed while its gene-symbol / p-value rows continue; gene symbols only (text order). Nothing of
    the PDF is printed; the caption search and the p. 10 module-colour mapping are asserted programmatically. After the
    first extract the PDF is deleted (privacy: it holds per-individual tables) and a later run re-reads the extract."""
    out_p = DELETED_AFTER_EXTRACT["voineagu_si_pdf"]
    pdf = INPUTS["voineagu_si_pdf"][0]
    if not pdf.exists():
        with open(out_p, encoding="utf-8", newline="") as f:
            body = list(csv.reader(f, delimiter="\t"))
        assert body[0] == ["text_order", "page", "gene"], body[0]
        # v6.8 (C): the rows are in text order; text_order is renumbered 1 ... n (v6.7 wrote 1, 3, 5 ... per page)
        return [[k + 1, int(b), c] for k, (a, b, c) in enumerate(body[1:])]
    doc = fitz.open(str(pdf))
    flat = [" ".join(p.get_text().split()) for p in doc]
    cap = [i for i, t in enumerate(flat)
           if re.search(r"Supplementary Table 14\. M12 module genes and associated GWAS p values", t)]
    assert cap == [18], cap  # p. 19
    t10 = flat[9]  # p. 10: M12 = the pink module (432 genes), M16 = the tan module (377)
    assert re.search(r"M12\W+pink|pink\W+(\(?432\)?\W+)?M12", t10) and re.search(r"M16\W+tan|tan\W+(\(?377\)?\W+)?M16", t10)
    assert "432" in t10 and "377" in t10
    m16 = [i for i, t in enumerate(flat)  # a printed M16 / tan gene table: none (asdM16 stays not buildable)
           if re.search(r"Supplementary Table \d+\.? *[^.]{0,30}(tan|M16)[^.]{0,20}(module )?genes", t, re.I)]
    assert m16 == [], m16
    sym = re.compile(r"^[A-Z][A-Z0-9]*(?:orf[0-9]+)?(?:[-.][A-Z0-9]+)*$")
    num = re.compile(r"^[0-9.]+(E-?\d+)?$")
    out, pages, pg = [], [], cap[0]
    while pg < len(doc):
        if pg > cap[0] and re.search(r"Supplementary Table \d+\.", flat[pg]):
            break
        L = [x.strip() for x in doc[pg].get_text().split("\n")]
        pairs = [L[k] for k in range(len(L) - 1) if sym.match(L[k]) and num.match(L[k + 1])]
        if not pairs:
            break
        base = len(out)  # v6.8 (C): v6.7 read len(out) inside the generator while out grew (1, 3, 5 ... per page)
        out.extend([base + k + 1, pg + 1, g] for k, g in enumerate(pairs))
        pages.append(pg + 1)
        pg += 1
    doc.close()
    assert pages == [19, 20, 21, 22, 23], pages
    assert len(out) == len({r[2] for r in out}) == 380, len(out)  # 76 + 86 + 86 + 86 + 46 rows
    return out


def darnell_s2a() -> list[list]:
    """register v6.7 N7: Darnell 2011 Table S2A 'FMRP Targets (842)': its 'Gene Symbol' (upper case), 'Symbol from mm9'
    (mouse) and 'Entrez Gene ID' columns; the identifier-header guard on every sheet first (rows never printed)."""
    b = xlrd.open_workbook(str(INPUTS["darnell_s2_xls"][0]), on_demand=True)
    for n in b.sheet_names():  # v6.8: the whole guard (width, identifier wording and values) on every sheet
        v = G.classify_xlrd(b.sheet_by_name(n))
        assert not v["identifier_bearing"], ("Darnell sheet identifier-bearing", n, v["rules"])
    sa = b.sheet_by_name(next(n for n in b.sheet_names() if n.strip() == "Table S2A"))
    assert str(sa.cell_value(0, 0)).startswith("Table S2A. FMRP Targets (842)")
    h = [str(x).strip() for x in sa.row_values(1)]
    ig, im, ie = h.index("Gene Symbol"), h.index("Symbol from mm9"), h.index("Entrez Gene ID")
    out = []
    for r in range(2, sa.nrows):
        e = sa.cell_value(r, ie)
        out.append([r - 1, str(sa.cell_value(r, ig)).strip(), str(sa.cell_value(r, im)).strip(),
                    str(int(e)) if isinstance(e, float) else str(e).strip()])
    b.release_resources()
    assert len(out) == len({x[3] for x in out}) == 842, len(out)
    return out


def originals_v68() -> dict:
    """register v6.8 (B S2): the three originals deleted after their gene-level reductions -- read from each reduction's
    'original' block (sha256, bytes, sheet names with rows / columns and the guard's rule letters), with the reduction's path
    and sha256 and what reads it. Nothing typed by hand."""
    out = {}
    for key in RV.ORIGINALS:
        p = RV.reduced_path(key)
        rec = json.loads(p.read_text(encoding="utf-8"))
        o = rec["original"]
        orig = RV.original_path(key)  # v6.9: an exploration-lane original sits under its own root
        out[key] = {"original_path": str(orig), "sha256": o["sha256"], "bytes": o["bytes"],
                    "sheets_name_rows_cols_guard": [[(s["member"] + "::" if s.get("member") else "") + s["sheet"], s["n_rows"],
                                                     s["n_cols"], s["guard"]] for s in o["sheets"]],
                    "kept_sheet_rows_cols_columns": [[k["sheet"], k["n_rows"], k["n_cols_kept"], k["columns_kept"]]
                                                     for k in rec["kept"]],
                    "reduced_path": str(p), "reduced_sha256": sha256(p), "deleted": not orig.exists(),
                    "read_by": RV.ORIGINALS[key]["read_by"]}
        if "zip_sheet_names" in rec:  # a zip of workbooks: the builders read its sheet names only (kept)
            out[key]["kept_zip_sheet_names"] = {m: len(v) for m, v in rec["zip_sheet_names"].items()}
    return out


def main() -> None:
    args = sys.argv[1:]
    verify = "--verify" in args  # v6.8: every job in memory, nothing written
    only = [a for a in args[args.index("--only") + 1:] if not a.startswith("--")] if "--only" in args else None
    for k, (p, h) in INPUTS.items():
        if k in REDUCED_V68:  # v6.8 (B S2): the reduction and its record of the original, asserted
            RV.load(REDUCED_V68[k][1], REDUCED_V68[k][2], h)
            if p.exists():
                assert sha256(p) == h, f"{k}: sha256 differs"
            continue
        if k in DELETED_AFTER_EXTRACT and not p.exists():
            assert DELETED_AFTER_EXTRACT[k].exists(), f"{k}: input deleted and no extract"
            continue  # v6.7 N1: deleted after its extract (privacy); sha256 kept in INPUTS
        got = sha256(p)
        assert got == h, f"{k}: sha256 {got} != {h}"
    libs = ({"pymupdf": fitz.VersionBind, "xlrd": xlrd.__VERSION__, "python-docx": getattr(docx, "__version__", "?")}
            if fitz is not None else {"xlrd": xlrd.__VERSION__} if xlrd is not None else None)  # v6.9: the venv's xlrd
    man = {"script": "arcs/audit/src_register/s_extract.py", "python": sys.version.split()[0], "libs": libs,
           "inputs": {k: {"path": str(p), "sha256": h} for k, (p, h) in INPUTS.items()}, "extracts": {}}
    for k, (_, rp, rh) in REDUCED_V68.items():
        man["inputs"][k].update({"deleted_v68": not INPUTS[k][0].exists(), "reduced_v68": {"path": str(rp), "sha256": rh}})
    man["originals_deleted_v68"] = originals_v68()
    jobs = [
        ("segura_s7", SRC / "segura2025_tables" / "extract" / "tableS7_terms.tsv",
         ["printed_order", "printed_row", "term", "named"], segura_s7),
        ("velmeshev_asd_degs", SRC / "velmeshev2019" / "extract" / "data_s4_ASD_DEGs.tsv",
         ["cell_type", "gene_id", "gene_name", "fold_change", "q_value"], velmeshev),
        ("shin_tableS1", SRC / "shin2018" / "extract" / "tableS1_panels.tsv", ["cell_type", "gene_symbol"], shin),
        ("grove_table10", SRC / "grove2019_magma" / "extract" / "table10_top25.tsv", ["rank", "gene"], grove),
        ("kang_table9_modules", SRC / "kang2011" / "extract" / "table9_modules.tsv", ["module", "color", "size"],
         kang_modules),
        ("spark_single_genes", SRC / "spark2018" / "extract" / "spark_single_genes.tsv", ["printed_order", "gene"], spark),
        ("voineagu_table14_m12", DELETED_AFTER_EXTRACT["voineagu_si_pdf"], ["text_order", "page", "gene"], voineagu_table14),
        ("darnell_s2a_842", SRC / "darnell2011_fmrp" / "extract" / "tableS2A_842_targets.tsv",
         ["printed_order", "gene_symbol", "symbol_mm9", "entrez_mouse"], darnell_s2a),
    ]
    mp = SRC / "extract_manifest.json"
    if only is not None:  # v6.8: only these jobs; every other extract entry kept, its file asserted unchanged
        assert only and set(only) <= {j[0] for j in jobs}, f"unknown job in {only}"
        old = json.loads(mp.read_text(encoding="utf-8"))
        for name, v in old["extracts"].items():
            if name not in only:
                assert sha256(Path(v["path"])) == v["sha256"], f"extract {name} changed on disk"
                man["extracts"][name] = v
        # the libraries and Python of the full run that made the other extracts are kept; this run's interpreter per job
        man["python"], man["libs"] = old["python"], old["libs"]
        man["only_runs"] = dict(old.get("only_runs", {}))
        for j in only:
            man["only_runs"][j] = {"python": sys.version.split()[0],
                                   "interpreter": "programme venv" if "venv" in sys.executable.lower() else "system Python",
                                   "libs": libs}
    for name, path, header, fn in jobs:
        if only is not None and name not in only:
            continue
        rows = fn()
        if verify:
            h = hashlib.sha256(tsv_text(header, rows).encode("utf-8")).hexdigest()
            stored = sha256(path) if path.exists() else None
            print(f"{name}: {len(rows)} rows, sha256 {h}; equal to the stored extract: {'yes' if h == stored else 'NO'}")
            continue
        h = write_tsv(path, header, rows)
        man["extracts"][name] = {"path": str(path), "rows": len(rows), "sha256": h}
        print(f"{name}: {len(rows)} rows, sha256 {h}")
    if verify:
        return
    for k, out_p in DELETED_AFTER_EXTRACT.items():  # v6.7 N1: delete the input once its extract is written
        p = INPUTS[k][0]
        if p.exists():
            assert out_p.exists()
            p.unlink()
            print(f"{k}: deleted after the extract (sha256 {INPUTS[k][1]} kept)")
        man["inputs"][k]["deleted_after_extract"] = True
    txt = json.dumps(man, indent=1, sort_keys=True) + "\n"
    mp.write_text(txt, encoding="utf-8", newline="\n")
    assert mp.read_text(encoding="utf-8") == txt
    print("extract_manifest.json sha256", sha256(mp))


if __name__ == "__main__":
    main()
