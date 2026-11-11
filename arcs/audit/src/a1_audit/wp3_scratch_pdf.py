"""WP3 (RUN_PLAN_amend_3 R47 checks): a SYNTHETIC two-table MOESM2 stand-in written with matplotlib (env\\venv 3.11.2),
39 pages: 37 padding pages, page index 37 in Table S6's layout and page index 38 in Table S7's layout - the layout the
frozen `s_extract.segura_s7` asserts (s_extract.py:152-195): the exact title text, exactly one '#' word, exactly one
word beginning '*Only', 77 printed rows holding the 78 terms of SEGURA_S7_TERMS.json in printed order (row 1 a ' / '
pair with 'a/b' value tokens; one wrapped row whose values sit on the next line), the 7 SEGURA_NAMED names among them.
The named rows carry the TSV's published values (rows 3-9), printed as plain decimals; the D rows carry planted values.
Nothing here opens MOESM2 or any carrier; the term names are the frozen register file's (public GO names).

variants (each one change, for the refusal checks): 'name' (a term name changed), 'row' (a term on another printed
row), 'precision' (a named value off by more than the TSV's precision), 'parts' (a joined row's token with the wrong part
count), 'no_title' (the S7 caption removed), 's6_two_captions', 'genes106'.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import wp3_layout as L

S7_TERMS_REL = "arcs/audit/register_sets/SEGURA_S7_TERMS.json"
PAGE_W, PAGE_H = 612.0, 792.0          # points (8.5 x 11 in)
X_TERM, X_NUM, X_STEP = 36.0, 400.0, 48.0
FONT = 5.5
LINE = 8.6


def s7_terms(repo: Path | None = None) -> list[dict]:
    doc = json.loads((Path(repo or L.REPO) / S7_TERMS_REL).read_text(encoding="utf-8"))
    return list(doc["terms"])


def _dec(text: str) -> str:
    """A TSV value printed as a plain decimal token matching ^[0-9.]+$ ('9.4e-6' -> '0.0000094')."""
    from decimal import Decimal
    d = Decimal(text)
    s = format(d, "f")
    return s


def planted_values(terms: list[dict], tsv_named: dict) -> dict:
    """{cell id: {genes, expected, fold, fdr} as printed tokens}: the TSV's for the named terms, planted for the rest."""
    out = {}
    for k, t in enumerate(terms):
        pub = tsv_named.get(t["cell_id"])
        if pub is not None:
            out[t["cell_id"]] = {key: _dec(v) for key, v in pub.items()}
        else:
            out[t["cell_id"]] = dict(genes=str(3 + k % 9), expected=f"{0.11 + 0.03 * k:.2f}",
                                     fold=f"{2.5 + 0.17 * k:.2f}", fdr=f"{0.001 + 0.0004 * k:.4f}")
    return out


def _page_lines(terms: list[dict], vals: dict, wrap_row: int, variant: str | None) -> list[tuple]:
    """[(term text, [4 tokens])] per printed line of the S7 page (a wrapped row: its term line, then a value line)."""
    by_row: dict[int, list] = {}
    for t in terms:
        by_row.setdefault(int(t["printed_row"]), []).append(t)
    lines = []
    for r in sorted(by_row):
        ts = by_row[r]
        name = " / ".join(t["term"] for t in ts)
        toks = ["/".join(vals[t["cell_id"]][k] for t in ts) for k in ("genes", "expected", "fold", "fdr")]
        if variant == "parts" and len(ts) > 1:
            toks[2] = vals[ts[0]["cell_id"]]["fold"]          # a joined row's fold token with one part only
        if r == wrap_row:
            lines.append((name, []))
            lines.append(("", toks))
        else:
            lines.append((name, toks))
    return lines


def write_moesm2(path: Path, s4_genes: list[str], *, repo: Path | None = None, tsv_named: dict | None = None,
                 variant: str | None = None, s6_genes: list[str] | None = None) -> dict:
    """Write the synthetic MOESM2 stand-in; returns {'s6_genes': [...], 'values': {cell id: tokens}, 'wrap_row': r}."""
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["font.family"] = "DejaVu Sans"
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.pyplot as plt
    terms = [dict(t) for t in s7_terms(repo)]
    vals = planted_values(terms, dict(tsv_named or {}))
    if variant == "name":
        terms[20]["term"] = terms[20]["term"] + " process"
    if variant == "row":
        terms[1]["printed_row"] = 2      # row 1 holds one term, row 2 two: 77 rows, the names in order, a row moved
    if variant == "precision":
        named = [t for t in terms if t["cell_id"] in (tsv_named or {})]
        c = named[2]["cell_id"]
        vals[c]["fold"] = f"{float(vals[c]['fold']) + 0.02:.2f}"
    wrap_row = 40
    genes = list(s6_genes) if s6_genes is not None else list(s4_genes[:107])
    if variant == "genes106":
        genes = genes[:106]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    def text(fig, x, y, s):          # x, y in points from the top left
        fig.text(x / PAGE_W, 1.0 - y / PAGE_H, s, fontsize=FONT, ha="left", va="baseline")
    with PdfPages(str(path)) as pdf:
        for k in range(37):
            fig = plt.figure(figsize=(PAGE_W / 72, PAGE_H / 72))
            text(fig, X_TERM, 60, f"Supplementary padding page {k + 1}")
            pdf.savefig(fig)
            plt.close(fig)
        fig = plt.figure(figsize=(PAGE_W / 72, PAGE_H / 72))       # page index 37: Table S6
        text(fig, X_TERM, 50, "Table S6. Genes of the decoded list in the SFARI set (synthetic stand-in)")
        if variant == "s6_two_captions":
            text(fig, X_TERM, 64, "continued from Table S6 above")
        y = 80.0
        row = []
        for k, g in enumerate(genes):
            row.append(g + ("*" if k == 4 else ""))
            if len(row) == 10:
                text(fig, X_TERM, y, ", ".join(row) + ",")
                y += LINE
                row = []
        if row:
            text(fig, X_TERM, y, ", ".join(row))
            y += LINE
        text(fig, X_TERM, y + LINE, "Note: synthetic list; genes marked * are planted footnotes")
        pdf.savefig(fig)
        plt.close(fig)
        fig = plt.figure(figsize=(PAGE_W / 72, PAGE_H / 72))       # page index 38: Table S7
        if variant != "no_title":
            text(fig, X_TERM, 30, "Table S7. Genetic Ontology (GO) terms enriched in the decoded list (synthetic)")
        text(fig, X_TERM, 50, "GO biological process complete")
        for j, h in enumerate(("# genes", "expected", "Fold Enrichment", "FDR")):
            text(fig, X_NUM + j * X_STEP, 50, h)
        y = 60.0
        for name, toks in _page_lines(terms, vals, wrap_row, variant):
            if name:
                text(fig, X_TERM, y, name)
            for j, tok in enumerate(toks):
                text(fig, X_NUM + j * X_STEP, y, tok)
            y += LINE
        text(fig, X_TERM, y + LINE, "*Only terms with FDR < 0.05 are shown (synthetic stand-in)")
        pdf.savefig(fig)
        plt.close(fig)
    return {"s6_genes": genes, "values": vals, "wrap_row": wrap_row}


def add_tf_operand(pdf: bytes, page_index: int, operand: bytes) -> bytes:
    """Fix round 3, A1 (the reviewer's x7.py, ported): an incremental update giving page `page_index` one extra content
    stream 'BT /F1 /<operand> Tf ET' - no text is drawn (the extracted words are unchanged), but pdfminer LOGS a warning
    naming the operand ("... is an invalid float value") through its own module logger while it interprets the page."""
    import io
    import re
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfpage import PDFPage
    from pdfminer.pdfparser import PDFParser
    doc = PDFDocument(PDFParser(io.BytesIO(pdf)))
    pid = list(PDFPage.create_pages(doc))[page_index].pageid
    m = re.search(rb"(?:^|\n)%d 0 obj\s*(<<.*?>>)\s*endobj" % pid, pdf, re.S)
    body = m.group(1)
    cm = re.search(rb"/Contents (\d+) 0 R", body)
    old_xref = int(re.findall(rb"startxref\s+(\d+)", pdf)[-1])
    tr = re.findall(rb"trailer\s*<<(.*?)>>\s*startxref", pdf, re.S)[-1]
    size = int(re.search(rb"/Size (\d+)", tr).group(1))
    root = re.search(rb"/Root (\d+ \d+ R)", tr).group(1)
    info = re.search(rb"/Info (\d+ \d+ R)", tr)
    content = b"BT /F1 /" + operand + b" Tf ET\n"
    newobj = size
    out = bytearray(pdf if pdf.endswith(b"\n") else pdf + b"\n")
    off_stream = len(out)
    out += b"%d 0 obj\n<< /Length %d >>\nstream\n" % (newobj, len(content)) + content + b"endstream\nendobj\n"
    newbody = body.replace(cm.group(0), b"/Contents [" + cm.group(1) + b" 0 R %d 0 R]" % newobj)
    off_page = len(out)
    out += b"%d 0 obj\n" % pid + newbody + b"\nendobj\n"
    xref_off = len(out)
    out += b"xref\n0 1\n0000000000 65535 f \n%d 1\n%010d 00000 n \n%d 1\n%010d 00000 n \n" % (
        pid, off_page, newobj, off_stream)
    out += b"trailer\n<< /Size %d /Root %s%s /Prev %d >>\nstartxref\n%d\n" % (
        newobj + 1, root, (b" /Info " + info.group(1)) if info else b"", old_xref, xref_off)
    out += b"%%EOF\n"
    return bytes(out)


def plant_tf_operand(roots, operand: bytes = b"NDARINVAB123CDE"):
    """Rewrite a scratch layout's MOESM2 stand-in with add_tf_operand on page index 38; returns the roots with its pin
    (sha256, size) updated."""
    import dataclasses
    import hashlib
    path, _ = roots.pin("segura_moesm2")
    b = add_tf_operand(path.read_bytes(), 38, operand)
    path.write_bytes(b)
    pins = tuple((k, (v[0], v[1], hashlib.sha256(b).hexdigest(), len(b)) if k == "segura_moesm2" else v)
                 for k, v in roots.pins)
    return dataclasses.replace(roots, pins=pins)
