"""Claims register DRAFT v6.6 pre-freeze downloads (B2 / C5 of the orchestrator under the operator's standing delegation,
2026-09-27): the sources of the comparators of Buch's non-GO sets and Pagani's sets, resolved by the register section 1.6
rule R-a ... R-e (written into the register at 2026-09-27T02:56:44Z). v6.7 N5 (correction): the rule preceded every
COMPARATOR SOURCE below (the first, steinberg2013_fmrp/mmc1.pdf, at 03:21:39Z), but not every file: buch2023_aam.pdf,
the target paper's accepted manuscript (read for its Methods' 'Gene set lists' and references), was downloaded at
02:52:40Z, four minutes before the rule was written. The order is self-attested (file times on this box and the register's
own time stamp) and lands in one commit, so no outside record witnesses it (register 1.6). Public, ungated sources;
plain HTTPS (fetch_util: curl, the PMC proof-of-work solved; no login, no e-mail, no API key, no identifier sent);
archived releases through the Internet Archive's Wayback Machine (CDX listings and 'id_' raw captures), which serves
them without an account.

Folders (E:\\data\\asdg\\register_sets_src\\<folder>\\; every file recorded by sha256 in its SOURCE.md, s_sources_md.py):
  parikshak2013/            + supplement 03 -> extract/tableS1D_gene_lists.tsv (sheet TableS2A = 'Table S1D - Gene lists
                              used in enrichment analyses' only; the file also holds a per-individual variant sheet, so the
                              xlsx is deleted after the extract, its sha256 kept in SOURCE.md)
  voineagu2011/             Supplementary Table 2 (.xls; module membership kME only: evidence for R-e)
  parikshak2016/            + Supplementary Table 4 (CTX.M12 / CTX.M16 are its own rWGCNA modules: evidence for R-e)
  steinberg2013_fmrp/       Document S1 (mmc1.pdf; no list of the 842 FMRP targets: evidence for R-e)
  spark2018/                the SPARK gene list PDF (S3 copy; identical content digest to the Wayback captures that
                              bracket Buch's submission date) + the two CDX listings
  sanders2019_rgd/          Tables S1 / S2 / S4 (.xlsx) + the supplemental PDF -> extract/table_s1_flags.tsv (Table S1's
                              gene ids and its three disorder-gene flags ASD65 / DDD93 / CHD253)
  nair2009_psoriasis/       the supplement PDF + the article page (Table 2; evidence for R-e)
  pfenning2014_vocal/       the supplement PDF (Tables S1-S8 are on science.org only, HTTP 403: evidence for R-e)
  pua2016_cardiac/          ESM1 -> extract/st1_gene_list.tsv (sheet 'ST1 List of genes' only; the file also holds a
                              per-sample sheet, so the xlsx is deleted after the extract)
  sfari_wayback_2022-01-24/ the SFARI Gene genes CSV as captured 2022-01-24 (the earliest capture after 2021-11-29;
                              the capture before it, 2021-10-22, differs) + the CDX listing
  diseases_v2_2022-02-09/   DISEASES v2 (figshare, the Jensen lab's archived release): the three filtered channel files
                              and the dictionary; + the CDX listings of the weekly files (evidence for R-b)
  rgd_2026-09-19/           RGD human gene -> RDO annotations (GAF) and RDO.obo (the release obtainable at download)
  ctd_2026-08-28/           CTD_genes_diseases.tsv.gz (3.2 GB, curl -C - with a long timeout) and CTD_diseases.tsv.gz
                              -> extract/schizophrenia_rows.tsv (the rows of MESH:D012559 and its MEDIC descendants)
  gandal2022_nature611/     Supplementary Data 5 (MOESM7 -> extract/gene_level_modules.tsv) and 6 (MOESM8); Fig. 3 and
                              Fig. 4 images (the module labels, transcribed in register_maps/gandal2022_module_labels.json)
  reactome_v92/             Reactome release 92 (2025-03-27; release 93 is dated 2025-06-17): ReactomePathways.gmt.zip,
                              ReactomePathways.txt
  syngo_1.2_20231201/       SynGO release 1.2 (= 20231201) as the portal serves it + two archived portal pages
Register DRAFT v6.7 (orchestrator under the operator's standing delegation, 2026-09-27) adds (FILES67):
  parikshak2013/            + supplement 01 (Extended Experimental Procedures, PDF: where 'asdM12' / 'asdM16' are named)
                              and the article page (the near-miss view's evidence)
  voineagu2011/             + the article page (Voineagu names its modules M12 / M16; no 'asdM' in its text)
  sfari_wayback_captures/   every Wayback capture of the SFARI genes CSV with a distinct content digest, 2020-10-31 ...
                              2024-05-15 (the uniform archive rule: Liu's 'earliest release whose score-1 count equals 233')
  kegg_wayback_2024-09-16/  KEGG REST link/hsa/pathway and list/pathway/hsa as captured on 2024-09-16 (the one complete
                              archived KEGG REST release nearest Mamat's 2024-08-14) + the CDX listings of both files
  rgd_wayback_2024-07-24/   RGD's human RDO annotations as captured 2024-07-24 (generated 2024-07-20; the earliest COMPLETE
                              capture after 2021-11-29 -- earlier ones are cut at 1 MiB) + RDO_20240720 (RGD's own weekly
                              archive) + the CDX listing and each capture's archived length (capture_lengths.json)
  ctd_wayback_2024-02-10/   CTD_genes_diseases.tsv.gz and CTD_diseases.obo.gz as captured on 2024-02-10 (the earliest date
                              after 2021-11-29 with both captured) + the CDX listings -> extract/schizophrenia_rows.tsv
  voineagu2011/             + the Supplementary Information PDF (N1: Supplementary Table 14, the M12 module genes); it
                              also holds per-individual tables, so s_extract.py extracts ONLY the pages its caption
                              locates (-> extract/table14_M12_genes.tsv) and deletes the PDF, its sha256 kept
  darnell2011_fmrp/         Darnell 2011 (Cell 146:247) Tables S2A-C (.xls: the 842 FMRP CLIP targets; N7, the near-miss
                              view's FMRP source) + the article page; s_extract.py reads the target sheet only
  sfari_wayback_captures/   + served_labels.json: the release label each capture serves (its Content-Disposition file
                              name '<release>release_<export>export'; N2, HEAD requests only)
MANUAL (not fetchable by script; verified by sha256 when present, never re-fetched):
  pfenning2014_vocal/science_download/pfenning-tables-s1-to-s8.zip  Pfenning 2014 Tables S1-S8 as science.org serves
                              them (N4): plain HTTPS gets a Cloudflare bot challenge (HTTP 403), the Wayback Machine holds
                              no capture and Europe PMC does not serve the supplement; obtained 2026-09-27 in a real Chrome
                              browser started with a FRESH, EMPTY profile (no login, no cookie, no e-mail, no identifier
                              entered or sent), driven over the DevTools protocol, the challenge passed by the browser itself

Individual-level data (v6.7, (3), tightened by the N-additions; the rule, enforced here): a supplement is opened by its
sheet names and dimensions only -- the ONLY things ever printed about a sheet; the first GUARD_ROWS rows of each sheet
are read, never printed, to test for a sample / individual / subject / proband / family / donor / patient / participant
identifier header (ID_HEADER); a sheet wider than WIDE_COLS columns never has its header row printed, because sample IDs
can be the column headers; the gene column is found programmatically (GENE_HEADER); a sheet carrying identifier headers is
never printed and is deleted with its file, without display; only the needed gene-level sheet is kept (extracted), and if
the needed sheet itself carries such headers the script prints a refusal instead of any row and stops. A workbook kept
whole must hold no such sheet.
Register DRAFT v6.8 (B S2; the orchestrator under the operator's standing delegation): the guard is privacy_guard.py -- a
sheet wider than WIDE_COLS, or with identifier wording OR an identifier-valued cell (brain-bank / sample / subject codes, the
documented ID_VALUE set) in its first GUARD_ROWS rows, is identifier-bearing; a builder reads such a sheet only in declared
columns. Under it several workbooks listed in KEPT_WHOLE / MANUAL hold identifier-bearing sheets (by width, or by code-shaped
accessions), so main() now stops at them with a refusal until they are reduced (register 1.6, v6.8: listed there; their
reduction needs the operator's authorisation for their folders).

Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src_register\\fetch_v66.py
Idempotent: a file already present is not fetched again. Prints counts and hashes only.
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_util  # noqa: E402
import privacy_guard as G  # noqa: E402  register v6.8 (B S2): the guard -- width, identifier wording AND identifier values
import reduce_v68 as RV  # noqa: E402  register v6.8: originals reduced to what the builders read, then deleted (never re-fetched)

SRC = Path(r"E:\data\asdg\register_sets_src")
PMC = "https://pmc.ncbi.nlm.nih.gov/articles/instance/%s/bin/%s"
WB = "https://web.archive.org/web/%sid_/%s"
CDX = "https://web.archive.org/cdx/search/cdx?url=%s&output=json&filter=statuscode:200&to=20260926"
FS = "https://ndownloader.figshare.com/files/%s"
SFARI_CSV = "https://gene.sfari.org/wp-content/themes/sfari-gene/utilities/download-csv.php?api-endpoint=genes"
FILES = [  # (folder, file name, url, big)
    ("parikshak2013", "NIHMS545068-supplement-03.xlsx", PMC % ("3934107", "NIHMS545068-supplement-03.xlsx"), False),
    ("voineagu2011", "NIHMS313080-supplement-2.xls", PMC % ("3607626", "NIHMS313080-supplement-2.xls"), False),
    ("parikshak2016", "NIHMS1050915-supplement-SuppTable4.xlsx", PMC % ("7102905", "NIHMS1050915-supplement-SuppTable4.xlsx"),
     False),
    ("steinberg2013_fmrp", "mmc1.pdf", PMC % ("3824119", "mmc1.pdf"), False),
    ("spark2018", "SPARK_gene_list.pdf", "https://spark-sf.s3.amazonaws.com/SPARK_gene_list.pdf", False),
    ("spark2018", "cdx_spark-sf_s3.json", CDX % "spark-sf.s3.amazonaws.com/SPARK_gene_list.pdf", False),
    ("spark2018", "cdx_sparkforautism.json", CDX % "sparkforautism.org/downloads/SPARK_gene_list.pdf", False),
    ("sanders2019_rgd", "NIHMS1754502-supplement-Tables_S1__S2__S4.xlsx",
     PMC % ("8656349", "NIHMS1754502-supplement-Tables_S1__S2__S4.xlsx"), False),
    ("sanders2019_rgd", "NIHMS1754502-supplement-Supplemental_info_and_Tables_S3__S5.pdf",
     PMC % ("8656349", "NIHMS1754502-supplement-Supplemental_info_and_Tables_S3__S5.pdf"), False),
    ("nair2009_psoriasis", "NIHMS83342-supplement-1.pdf", PMC % ("2745122", "NIHMS83342-supplement-1.pdf"), False),
    ("nair2009_psoriasis", "PMC2745122.html", "https://pmc.ncbi.nlm.nih.gov/articles/PMC2745122/", False),
    ("pfenning2014_vocal", "NIHMS666880-supplement-Supplemental_material.pdf",
     PMC % ("4385736", "NIHMS666880-supplement-Supplemental_material.pdf"), False),
    ("pua2016_cardiac", "12265_2016_9673_MOESM1_ESM.xlsx", PMC % ("4767849", "12265_2016_9673_MOESM1_ESM.xlsx"), False),
    ("sfari_wayback_2022-01-24", "SFARI-Gene_genes_capture_20220124104055.csv", WB % ("20220124104055", SFARI_CSV), False),
    ("sfari_wayback_2022-01-24", "cdx_sfari_genes_csv.json",
     CDX % "gene.sfari.org/wp-content/themes/sfari-gene/utilities/download-csv.php?api-endpoint=genes", False),
    ("diseases_v2_2022-02-09", "human_disease_knowledge_filtered.tsv.gz", FS % "34018280", False),
    ("diseases_v2_2022-02-09", "human_disease_experiments_filtered.tsv.gz", FS % "34018298", False),
    ("diseases_v2_2022-02-09", "human_disease_textmining_filtered.tsv.gz", FS % "34018313", False),
    ("diseases_v2_2022-02-09", "diseases_dictionary.tar.gz", FS % "34018265", False),
    ("diseases_v2_2022-02-09", "cdx_knowledge_filtered.json",
     CDX % "download.jensenlab.org/human_disease_knowledge_filtered.tsv", False),
    ("diseases_v2_2022-02-09", "cdx_experiments_filtered.json",
     CDX % "download.jensenlab.org/human_disease_experiments_filtered.tsv", False),
    ("diseases_v2_2022-02-09", "cdx_textmining_filtered.json",
     CDX % "download.jensenlab.org/human_disease_textmining_filtered.tsv", False),
    ("rgd_2026-09-19", "human_genes_rdo.gaf.gz",
     "https://download.rgd.mcw.edu/data_release/annotations/human_genes_rdo.gaf.gz", False),
    ("rgd_2026-09-19", "RDO.obo", "https://download.rgd.mcw.edu/ontology/disease/RDO.obo", False),
    ("ctd_2026-08-28", "CTD_diseases.tsv.gz", "https://ctdbase.org/reports/CTD_diseases.tsv.gz", False),
    ("ctd_2026-08-28", "CTD_genes_diseases.tsv.gz", "https://ctdbase.org/reports/CTD_genes_diseases.tsv.gz", True),
    ("gandal2022_nature611", "41586_2022_5377_MOESM7_ESM.xlsx", PMC % ("9668748", "41586_2022_5377_MOESM7_ESM.xlsx"), False),
    ("gandal2022_nature611", "41586_2022_5377_MOESM8_ESM.xlsx", PMC % ("9668748", "41586_2022_5377_MOESM8_ESM.xlsx"), False),
    ("gandal2022_nature611", "41586_2022_5377_Fig3_HTML.jpg",
     "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/af98/9668748/ab4c8e9bb88f/41586_2022_5377_Fig3_HTML.jpg", False),
    ("gandal2022_nature611", "41586_2022_5377_Fig4_HTML.jpg",
     "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/af98/9668748/85cfc3a5c3a3/41586_2022_5377_Fig4_HTML.jpg", False),
    ("reactome_v92", "ReactomePathways.gmt.zip", "https://download.reactome.org/92/ReactomePathways.gmt.zip", False),
    ("reactome_v92", "ReactomePathways.txt", "https://download.reactome.org/92/ReactomePathways.txt", False),
    ("syngo_1.2_20231201", "syngo1.2_complete_data.zip", "https://www.syngoportal.org/data/syngo1.2_complete_data.zip", False),
    ("syngo_1.2_20231201", "portal_capture_20250406180025.html", WB % ("20250406180025", "https://syngoportal.org/"), False),
    ("syngo_1.2_20231201", "portal_capture_20251118230922.html", WB % ("20251118230922", "https://syngoportal.org/"), False),
    ("buch2023_aam", "buch2023_aam.pdf",  # v6.6 C5: the Methods' 'Gene set lists' and references 19, 61, 117-131
     "https://www.repository.cam.ac.uk/bitstreams/32fb39c5-edbc-4ff3-b1e4-6a02695e2e83/download", False),
    ("romerogarcia2019_article", "41380_2018_Article_23.pdf",
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC6755982/pdf/41380_2018_Article_23.pdf", False),  # v6.6 C1: the '500' location
]
# xlsx that hold a per-individual / per-sample sheet: only the named sheet is read; the file is deleted after the extract
EXTRACT_THEN_DELETE = {
    ("parikshak2013", "NIHMS545068-supplement-03.xlsx"): ("TableS2A", "extract/tableS1D_gene_lists.tsv"),
    ("pua2016_cardiac", "12265_2016_9673_MOESM1_ESM.xlsx"): ("ST1 List of genes", "extract/st1_gene_list.tsv"),
}
CTD_SZ = "MESH:D012559"  # Schizophrenia (CTD MEDIC)
SFARI_CAPTURES = ["20201031090127", "20210516060025", "20210731184201", "20211022034409", "20220124104055", "20220701200121",
                  "20221206204848", "20230320190240", "20231010173503", "20231205085030", "20240324110733", "20240515204151"]
RGD_ANN = "https://download.rgd.mcw.edu/ontology/annotated_rgd_objects_by_ontology/homo_genes_rdo"
RGD_CAPTURES = ["20230606133203", "20240526215239", "20240724223811", "20240908071549", "20250324170409", "20260308044433"]
CDX_ALL = "https://web.archive.org/cdx/search/cdx?url=%s&output=json&to=20260926"
FILES67 = [  # register v6.7 (FILES as above: folder, name, url, big)
    ("parikshak2013", "NIHMS545068-supplement-01.pdf", PMC % ("3934107", "NIHMS545068-supplement-01.pdf"), False),
    ("parikshak2013", "PMC3934107.html", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3934107/", False),
    ("voineagu2011", "PMC3607626.html", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3607626/", False),
    ("kegg_wayback_2024-09-16", "link_hsa_pathway.txt", WB % ("20240916203812", "https://rest.kegg.jp/link/hsa/pathway"), False),
    ("kegg_wayback_2024-09-16", "list_pathway_hsa.txt", WB % ("20240916190349", "https://rest.kegg.jp/list/pathway/hsa"), False),
    ("kegg_wayback_2024-09-16", "cdx_link_hsa_pathway.json", CDX_ALL % "rest.kegg.jp/link/hsa/pathway", False),
    ("kegg_wayback_2024-09-16", "cdx_list_pathway_hsa.json", CDX_ALL % "rest.kegg.jp/list/pathway/hsa", False),
    ("rgd_wayback_2024-07-24", "homo_genes_rdo", WB % ("20240724223811", RGD_ANN), False),
    ("rgd_wayback_2024-07-24", "RDO_20240720_v1.283.obo.gz",
     "https://download.rgd.mcw.edu/ontology/disease/2024/RDO_20240720_v1.283.obo.gz", False),
    ("rgd_wayback_2024-07-24", "cdx_homo_genes_rdo.json", CDX_ALL % RGD_ANN.split("://")[1], False),
    ("ctd_wayback_2024-02-10", "CTD_diseases.obo.gz", WB % ("20240210030137", "https://ctdbase.org/reports/CTD_diseases.obo.gz"),
     False),
    ("ctd_wayback_2024-02-10", "CTD_genes_diseases.tsv.gz",
     WB % ("20240210030103", "https://ctdbase.org/reports/CTD_genes_diseases.tsv.gz"), True),
] + [("ctd_wayback_2024-02-10", "cdx_%s.json" % u.replace("ctdbase.org/reports/", "").replace(".", "_"), CDX_ALL % u, False)
     for u in ("ctdbase.org/reports/CTD_genes_diseases.tsv.gz", "ctdbase.org/reports/CTD_genes_diseases.csv.gz",
               "ctdbase.org/reports/CTD_genes_diseases.xml.gz", "ctdbase.org/reports/CTD_diseases.tsv.gz",
               "ctdbase.org/reports/CTD_diseases.csv.gz", "ctdbase.org/reports/CTD_diseases.xml.gz",
               "ctdbase.org/reports/CTD_diseases.obo.gz")] + [
    ("sfari_wayback_captures", "SFARI-Gene_genes_capture_%s.csv" % ts,
     WB % (ts, "https://gene.sfari.org/wp-content/themes/sfari-gene/utilities/download-csv.php?api-endpoint=genes"), False)
    for ts in SFARI_CAPTURES] + [
    # the N-additions (v6.7): N1 Voineagu's Supplementary Information (extracted by s_extract.py, then deleted); N7 Darnell 2011
    ("voineagu2011", "NIHMS313080-supplement-1.pdf", PMC % ("3607626", "NIHMS313080-supplement-1.pdf"), False),
    ("darnell2011_fmrp", "NIHMS314927-supplement-Suppl_Table_S2A-C.xls",
     PMC % ("3232425", "NIHMS314927-supplement-Suppl_Table_S2A-C.xls"), False),
    ("darnell2011_fmrp", "PMC3232425.html", "https://pmc.ncbi.nlm.nih.gov/articles/PMC3232425/", False),
    # N6: the texts the PAG-C9 / C10 near misses are read from (Gandal 2022's module descriptions; Pagani's own wording)
    ("gandal2022_nature611", "PMC9668748.html", "https://pmc.ncbi.nlm.nih.gov/articles/PMC9668748/", False),
    ("pagani2026_text", "PMC13246445_fullTextXML.xml",
     "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13246445/fullTextXML", False)]
# a PDF holding per-individual tables: s_extract.py reads only the caption-located pages and deletes it; not re-fetched once
# its extract exists (sha256 kept in SOURCE.md and s_extract.py)
PDF_EXTRACTED_THEN_DELETED = {("voineagu2011", "NIHMS313080-supplement-1.pdf"): "extract/table14_M12_genes.tsv"}
MANUAL = [  # (folder, relative path, where it is served, sha256): obtained by a browser (docstring), verified here
    ("pfenning2014_vocal", "science_download/pfenning-tables-s1-to-s8.zip",
     "https://www.science.org/doi/suppl/10.1126/science.1256846/suppl_file/pfenning-tables-s1-to-s8.zip",
     "9a7037b135e9848cc342b74d1ff3d8791782fc3e397e1926ff159ae570da616f")]
SFARI_ALL_CAPTURES_CDX = SRC / "sfari_wayback_2022-01-24" / "cdx_sfari_genes_csv.json"  # every HTTP-200 capture to 2026-09-26

# ---- register v6.7 (3): individual-level data -- the guard every supplement workbook passes through; register v6.8 (B S2): the
# v6.7 test read identifier WORDING only; the guard is now privacy_guard.py -- a sheet wider than WIDE_COLS, or with identifier
# wording or an identifier-VALUED cell (brain-bank / sample / subject codes) in its first GUARD_ROWS rows, is identifier-bearing
GUARD_ROWS = G.GUARD_ROWS
ID_HEADER = G.ID_WORDING
WIDE_COLS = G.WIDE_COLS  # a sheet wider than this is identifier-bearing (v6.8; v6.7: its header row was never printed)
GENE_HEADER = re.compile(r"(?i)^\s*(gene|genes|gene[\s_.]?symbols?|symbols?|hgnc[\s_.]?symbol|human[\s_.]?gene[\s_.]?"
                         r"symbol|official[\s_.]?symbol|gene[\s_.]?name)\s*$")


def big_get(url: str, out: Path) -> None:
    """curl with resume and a two-hour limit (CTD's 3.2 GB file)."""
    for _ in range(5):
        r = subprocess.run(["curl", "-sS", "-L", "-C", "-", "-m", "7200", "-A", fetch_util.UA, "-o", str(out), url])
        if r.returncode == 0:
            return
    raise RuntimeError("download failed: " + url)


def get(url: str, out: Path) -> dict:
    """fetch_util.get with retries (the Wayback CDX server answers 5xx under load)."""
    err = None
    for k in range(6):
        try:
            return fetch_util.get(url, out)
        except (RuntimeError, subprocess.CalledProcessError) as e:
            err = e
            if out.exists():
                out.unlink()
            time.sleep(10 * (k + 1))
    raise RuntimeError("failed after retries: %s (%s)" % (url, err))


def write_tsv(path: Path, header: list, rows: list) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = "\t".join(header) + "\n" + "".join("\t".join(str(x) for x in r) + "\n" for r in rows)
    path.write_bytes(txt.encode("utf-8"))
    assert path.read_bytes().decode("utf-8") == txt
    return fetch_util.sha256(path)


def _cell(v) -> str:
    return "" if v is None else " ".join(str(v).split())


def guard_workbook(xlsx, keep: str | None, label: str | None = None) -> dict:
    """register v6.7 (3), v6.8 (B S2): the sheet names and, per sheet, the privacy guard's verdict (privacy_guard.classify:
    wider than WIDE_COLS, identifier wording, identifier values in the first GUARD_ROWS rows). The rows are read, never
    printed; only sheet names and verdicts are returned. keep: the needed sheet (it must be clean, else a refusal stops the
    run) or None for a workbook kept whole (every sheet must be clean). xlsx: a path or a file-like object (a zip member;
    label names it)."""
    label = label or Path(xlsx).name
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    verdict = {}
    for ws in wb.worksheets:
        v = G.classify_openpyxl(ws)
        verdict[ws.title] = ("identifier-bearing (rule %s): rows never printed" % v["rules"]) if v["identifier_bearing"] \
            else "clean"
    wb.close()
    bad = [t for t, v in verdict.items() if v != "clean"]
    if keep is not None and keep in bad:
        raise SystemExit("REFUSED: %s sheet '%s' carries identifier headers; no row of it is read or printed" % (label, keep))
    if keep is None and bad:
        raise SystemExit("REFUSED: %s is to be kept whole but holds identifier-bearing sheets %s; extract the needed sheet "
                         "and delete the file" % (label, bad))
    return verdict


def overview(xlsx) -> list[tuple]:
    """the tightened rule (v6.7): what may be printed about a workbook -- each sheet's name and dimensions, nothing else."""
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    out = [(ws.title, ws.max_row, ws.max_column) for ws in wb.worksheets]
    wb.close()
    return out


def gene_column(xlsx, sheet: str) -> tuple | None:
    """the tightened rule (v6.7): the gene column of one sheet, found programmatically -- (row, column) of the first cell of
    its first GUARD_ROWS rows matching GENE_HEADER; nothing is printed, and the header row of a sheet wider than WIDE_COLS is
    never returned or shown."""
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb[sheet]
    hit = None
    for i, r in enumerate(ws.iter_rows(values_only=True), 1):
        if i > GUARD_ROWS or hit:
            break
        for j, v in enumerate(r, 1):
            if v is not None and GENE_HEADER.match(_cell(v)):
                hit = (i, j)
                break
    wb.close()
    return hit


def sfari_served_labels() -> dict:
    """v6.7 N2: the release label every archived SFARI genes-CSV capture serves -- the Content-Disposition file name
    'SFARI-Gene_genes_<MM-DD-YYYY>release_<MM-DD-YYYY>export.csv' -- for each HTTP-200 capture of the pinned CDX listing;
    HEAD requests only."""
    rows = json.loads(SFARI_ALL_CAPTURES_CDX.read_text(encoding="utf-8"))
    hdr = rows[0]
    out = {}
    for r in rows[1:]:
        c = dict(zip(hdr, r))
        if c["statuscode"] != "200":
            continue
        ts = c["timestamp"]
        name = None
        for k in range(6):
            p = subprocess.run(["curl", "-sS", "-I", "-m", "180", "-A", fetch_util.UA, WB % (ts, SFARI_CSV)],
                               capture_output=True, text=True)
            m = re.search(r"(?im)^content-disposition:.*?filename=\"?([^\";\r\n]+)", p.stdout)
            if m:
                name = m.group(1).strip()
                break
            time.sleep(10 * (k + 1))
        lab = re.fullmatch(r"SFARI-Gene_genes_(\d\d)-(\d\d)-(\d{4})release_(\d\d)-(\d\d)-(\d{4})export\.csv", name or "")
        assert lab, (ts, name)
        out[ts] = {"served_file_name": name, "digest": c["digest"],
                   "release": "%s-%s-%s" % (lab.group(3), lab.group(1), lab.group(2)),
                   "export": "%s-%s-%s" % (lab.group(6), lab.group(4), lab.group(5))}
    return out


def extract_sheet(xlsx: Path, sheet: str) -> tuple[list, list]:
    """every non-empty cell of ONE sheet, as (row, column, text); no other sheet is opened. v6.7 (3): only after the guard
    (the needed sheet clean); the file is deleted afterwards by main, identifier-bearing sheets with it, never displayed."""
    guard_workbook(xlsx, sheet)
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb[sheet]
    rows = []
    for i, r in enumerate(G.read_openpyxl(ws, label=Path(xlsx).name), 1):
        for j, v in enumerate(r, 1):
            if _cell(v):
                rows.append([i, j, _cell(v)])
    wb.close()
    return ["row", "col", "text"], rows


def sheet_rows(xlsx: Path, sheet: str, declared=None, header_row=None, label: str = "") -> list[tuple]:
    """v6.8: one sheet through the privacy guard -- from the workbook's reduction (reduce_v68.py; original column positions)
    where one exists, else from the workbook itself."""
    k = RV.key_of(xlsx)
    if k is not None and RV.reduced_path(k).exists():
        red = RV.reduced_path(k)
        return RV.rows(RV.load(red, fetch_util.sha256(red), RV.ORIGINALS[k]["sha"]), sheet, declared, header_row, label)
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    out = G.read_openpyxl(wb[sheet], declared, header_row, label)
    wb.close()
    return out


def gandal_gene_level(xlsx: Path) -> tuple[list, list]:
    want = ("ensembl_gene_id", "WGCNA_module", "external_gene_name", "hgnc_symbol")
    it = iter(sheet_rows(xlsx, "Gene_Level", declared=list(want), header_row=0, label="gandal2022 MOESM7"))  # v6.8
    hdr = list(next(it))
    ix = [hdr.index(c) for c in want]
    rows = [[_cell(r[k]) for k in ix] for r in it if r and r[ix[0]]]
    return ["ensembl_gene_id", "WGCNA_module", "external_gene_name", "hgnc_symbol"], rows


def sanders_flags(xlsx: Path) -> tuple[list, list]:
    """Sanders 2019 Table S1 ('S1 single gene RGDs'): the gene identifiers and the three disorder-gene flag columns only."""
    cols = ("symbol", "hgnc_id", "entrez_id", "ensembl_gene_id", "ASD65", "DDD93", "CHD253")
    # v6.8 (B S2): the sheet is identifier-bearing by the guard (wider than 50 columns), so it is read in declared columns
    # only -- first its column 1 alone, to find the header row ('symbol'), then the seven declared columns
    first = sheet_rows(xlsx, "S1 single gene RGDs", declared=lambda h: [0], header_row=0, label="sanders2019 S1")
    hr = next(i for i, r in enumerate(first) if r and r[0] == "symbol")
    all_rows = sheet_rows(xlsx, "S1 single gene RGDs", declared=list(cols), header_row=hr, label="sanders2019 S1")
    hdr = list(all_rows[hr])
    ix = [hdr.index(c) for c in cols]
    rows = [[_cell(r[k]) for k in ix] for r in all_rows[hr + 1:] if r and r[ix[0]]]
    return list(cols), rows


def ctd_rows(genes_gz: Path, diseases_gz: Path) -> tuple[list, list, list]:
    """the CTD gene-disease rows of Schizophrenia and its MEDIC descendants (CTD aggregates descendants in its own
    displays; the CTD_diseases ParentIDs column gives the hierarchy)."""
    kids = {}
    with gzip.open(diseases_gz, "rt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            for par in (p[4].split("|") if len(p) > 4 and p[4] else []):
                kids.setdefault(par, set()).add(p[1])
    want, todo = {CTD_SZ}, [CTD_SZ]
    while todo:
        for k in kids.get(todo.pop(), ()):
            if k not in want:
                want.add(k)
                todo.append(k)
    rows = []
    with gzip.open(genes_gz, "rt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) > 3 and p[3] in want:
                rows.append(p[:7])
    rows.sort()
    return ["GeneSymbol", "GeneID", "DiseaseName", "DiseaseID", "DirectEvidence", "InferenceChemicalName", "InferenceScore"], \
        rows, sorted(want)


def ctd_rows_obo(genes_gz: Path, obo_gz: Path) -> tuple[list, list, list]:
    """v6.7: as ctd_rows, the hierarchy from CTD_diseases.obo.gz (MEDIC is_a lines) -- the vocabulary file captured with the
    2024-02-10 gene-disease file."""
    kids, cur = {}, None
    with gzip.open(obo_gz, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("id: "):
                cur = line[4:].strip()
            elif line.startswith("is_a: ") and cur:
                kids.setdefault(line[6:].split(" ! ")[0].strip(), set()).add(cur)
            elif line.startswith("["):
                cur = None
    want, todo = {CTD_SZ}, [CTD_SZ]
    while todo:
        for k in kids.get(todo.pop(), ()):
            if k not in want:
                want.add(k)
                todo.append(k)
    rows = []
    with gzip.open(genes_gz, "rt", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) > 3 and p[3] in want:
                rows.append(p[:7])
    rows.sort()
    return ["GeneSymbol", "GeneID", "DiseaseName", "DiseaseID", "DirectEvidence", "InferenceChemicalName", "InferenceScore"], \
        rows, sorted(want)


def capture_lengths() -> dict:
    """v6.7: each RGD annotation capture's served length and the archive's original-length header (x-archive-orig-x-crawler-
    content-length marks a capture the crawler cut short); HEAD requests only."""
    out = {}
    for ts in RGD_CAPTURES:
        r = subprocess.run(["curl", "-sS", "-I", "-L", "-m", "180", "-A", fetch_util.UA, WB % (ts, RGD_ANN)],
                           capture_output=True, text=True)
        h = {k.strip().lower(): v.strip() for k, _, v in (ln.partition(":") for ln in r.stdout.splitlines()) if _}
        out[ts] = {"content_length": h.get("content-length"),
                   "x_archive_orig_content_length": h.get("x-archive-orig-content-length"),
                   "x_archive_orig_x_crawler_content_length": h.get("x-archive-orig-x-crawler-content-length"),
                   "complete": h.get("x-archive-orig-x-crawler-content-length") is None}
    return out


def fetch_list(files) -> None:
    for folder, name, url, big in files:
        out = SRC / folder / name
        key = (folder, name)
        if key in EXTRACT_THEN_DELETE and (SRC / folder / EXTRACT_THEN_DELETE[key][1]).exists():
            print("extract present %s/%s" % (folder, EXTRACT_THEN_DELETE[key][1]))
            continue
        if key in PDF_EXTRACTED_THEN_DELETED and (SRC / folder / PDF_EXTRACTED_THEN_DELETED[key]).exists():
            print("extract present %s/%s (the PDF deleted after s_extract.py)" % (folder, PDF_EXTRACTED_THEN_DELETED[key]))
            continue
        rk = RV.key_of(out)
        if rk is not None and RV.reduced_path(rk).exists() and not out.exists():  # v6.8: never re-fetch a deleted original
            print("reduction present %s/%s (the original deleted for privacy, v6.8; not re-fetched)"
                  % (folder, RV.reduced_path(rk).name))
            continue
        if out.exists():
            print("present %s/%s %d B sha256 %s" % (folder, name, out.stat().st_size, fetch_util.sha256(out)))
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            if big:
                big_get(url, out)
                print("fetched %s/%s %d B sha256 %s" % (folder, name, out.stat().st_size, fetch_util.sha256(out)))
            else:
                r = get(url, out)
                print("fetched %s/%s %d B sha256 %s" % (folder, name, r["bytes"], r["sha256"]))
        if key in EXTRACT_THEN_DELETE:
            sheet, rel = EXTRACT_THEN_DELETE[key]
            print("  original sha256 %s (deleted after the extract)" % fetch_util.sha256(out))
            hdr, rows = extract_sheet(out, sheet)
            h = write_tsv(SRC / folder / rel, hdr, rows)
            print("  extract %s/%s %d cells sha256 %s" % (folder, rel, len(rows), h))
            out.unlink()


KEPT_WHOLE = [("gandal2022_nature611", "41586_2022_5377_MOESM7_ESM.xlsx"),
              ("gandal2022_nature611", "41586_2022_5377_MOESM8_ESM.xlsx"),
              ("sanders2019_rgd", "NIHMS1754502-supplement-Tables_S1__S2__S4.xlsx"),
              ("parikshak2016", "NIHMS1050915-supplement-SuppTable4.xlsx")]
# v6.8 round 2 (the orchestrator under the operator's standing delegation): workbooks NO register builder reads (sha256 only) are
# left whole, identifier-bearing or not, and listed in register 1.6 -- reported here, not refused
LEFT_WHOLE_V68 = {("parikshak2016", "NIHMS1050915-supplement-SuppTable4.xlsx")}


def main() -> None:
    fetch_list(FILES)
    fetch_list(FILES67)
    for folder, name in KEPT_WHOLE:  # v6.7 (3): a workbook kept whole holds no identifier-bearing sheet
        rk = RV.key_of(SRC / folder / name)
        if rk is not None and RV.reduced_path(rk).exists() and not (SRC / folder / name).exists():
            print("reduced %s/%s (v6.8: the builders read its reduction; the original deleted)" % (folder, name))
            continue
        if (folder, name) in LEFT_WHOLE_V68:
            wb = openpyxl.load_workbook(SRC / folder / name, read_only=True, data_only=True)
            rules = {ws.title: G.classify_openpyxl(ws)["rules"] or "clean" for ws in wb.worksheets}
            wb.close()
            print("left whole %s/%s (v6.8: no builder reads it; register 1.6 lists it): %s" % (folder, name, rules))
            continue
        v = guard_workbook(SRC / folder / name, None)
        print("guard %s/%s: %d sheets, all clean" % (folder, name, len(v)))
    for folder, rel, url, h in MANUAL:  # v6.7 N4: a file a browser obtained -- verified, and its workbooks guarded
        f = SRC / folder / rel
        rk = RV.key_of(f)
        if rk is not None and RV.reduced_path(rk).exists() and not f.exists():
            print("manual %s/%s reduced (v6.8: the sheet names the builders read kept; the original deleted)" % (folder, rel))
            continue
        if not f.exists():
            print("MANUAL %s/%s absent: obtain it from %s in a browser with a fresh profile (docstring)" % (folder, rel, url))
            continue
        got = fetch_util.sha256(f)
        assert got == h, ("MANUAL", rel, got, h)
        print("manual %s/%s %d B sha256 %s (verified)" % (folder, rel, f.stat().st_size, got))
        import zipfile
        with zipfile.ZipFile(f) as z:
            for m in sorted(n for n in z.namelist() if n.lower().endswith(".xlsx")):
                b = io.BytesIO(z.read(m))
                v = guard_workbook(b, None, "%s:%s" % (f.name, m))
                print("  guard %s: %d sheets, all clean; sheets (name, rows, cols): %s" % (m, len(v), overview(b)))
    sl = SRC / "sfari_wayback_captures" / "served_labels.json"
    if not sl.exists():  # v6.7 N2: the served release label of every capture
        txt = json.dumps(sfari_served_labels(), indent=1, sort_keys=True) + "\n"
        sl.write_bytes(txt.encode("utf-8"))
    print("sfari served_labels.json sha256 %s" % fetch_util.sha256(sl))
    cl = SRC / "rgd_wayback_2024-07-24" / "capture_lengths.json"
    if not cl.exists():
        txt = json.dumps(capture_lengths(), indent=1, sort_keys=True) + "\n"
        cl.write_bytes(txt.encode("utf-8"))
        print("rgd capture_lengths.json sha256 %s" % fetch_util.sha256(cl))
    for folder, gz, out in (("rgd_wayback_2024-07-24", "RDO_20240720_v1.283.obo.gz", "RDO_20240720_v1.283.obo"),
                            ("ctd_wayback_2024-02-10", "CTD_diseases.obo.gz", "CTD_diseases.obo")):
        o = SRC / folder / "extract" / out
        if not o.exists():  # v6.7: the ontologies decompressed (deterministic), for the S-build's obo reader
            o.parent.mkdir(parents=True, exist_ok=True)
            o.write_bytes(gzip.decompress((SRC / folder / gz).read_bytes()))
            print("extract %s/extract/%s sha256 %s" % (folder, out, fetch_util.sha256(o)))
    cx7 = SRC / "ctd_wayback_2024-02-10" / "extract" / "schizophrenia_rows.tsv"
    if not cx7.exists():
        hdr, rows, ids = ctd_rows_obo(SRC / "ctd_wayback_2024-02-10" / "CTD_genes_diseases.tsv.gz",
                                      SRC / "ctd_wayback_2024-02-10" / "CTD_diseases.obo.gz")
        print("extract ctd (2024-02-10) schizophrenia_rows.tsv %d rows (%d disease ids) sha256 %s"
              % (len(rows), len(ids), write_tsv(cx7, hdr, rows)))
    g7 = SRC / "gandal2022_nature611" / "41586_2022_5377_MOESM7_ESM.xlsx"
    gx = SRC / "gandal2022_nature611" / "extract" / "gene_level_modules.tsv"
    if not gx.exists():
        hdr, rows = gandal_gene_level(g7)
        print("extract gandal2022 gene_level_modules.tsv %d rows sha256 %s" % (len(rows), write_tsv(gx, hdr, rows)))
    sx = SRC / "sanders2019_rgd" / "extract" / "table_s1_flags.tsv"
    if not sx.exists():
        hdr, rows = sanders_flags(SRC / "sanders2019_rgd" / "NIHMS1754502-supplement-Tables_S1__S2__S4.xlsx")
        print("extract sanders2019 table_s1_flags.tsv %d rows sha256 %s" % (len(rows), write_tsv(sx, hdr, rows)))
    cx = SRC / "ctd_2026-08-28" / "extract" / "schizophrenia_rows.tsv"
    if not cx.exists():
        hdr, rows, ids = ctd_rows(SRC / "ctd_2026-08-28" / "CTD_genes_diseases.tsv.gz",
                                  SRC / "ctd_2026-08-28" / "CTD_diseases.tsv.gz")
        print("extract ctd schizophrenia_rows.tsv %d rows (%d disease ids) sha256 %s" % (len(rows), len(ids),
                                                                                      write_tsv(cx, hdr, rows)))


if __name__ == "__main__":
    main()
