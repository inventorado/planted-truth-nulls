"""A1 pre-freeze S-build, stage 2 (claims register DRAFT v4 §1.6 "S-build runs before the freeze", §1.10 (0)).

Builds every gene set S that the register / TSV rows define from an external database or an external publication's
table (no map, no gated carrier), maps it to HGNC approved symbols by the §1.6 rule, intersects it with the class
universes of the §3.1 AHBA matrices (dk-ctx, V-DK, V-AAL, MIST64), and writes
    arcs/audit/register_sets/<set_id>.json         one file per set (built, or "not auditable (S undefined)")
    arcs/audit/register_sets/SEGURA_S7_TERMS.json  Segura Table S7's 78 terms -> GO id (release 2024-01-17)
    arcs/audit/register_sets/MANIFEST.json         every set: id, sha256 of its json, TSV cell ids, status; every
                                                   TSV row: which set it uses (or why none is built now)
Sets inside a gated carrier are only listed ("built under gate Gx"); none of their carriers is opened.

Run (programme venv; stage 1 `s_extract.py` must have run under the system Python first):
    env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src_register\\s_build.py
Deterministic: no timestamps, sorted members; every input asserted by sha256; every output read back.
Prints counts and hashes only.

Register DRAFT v5 (TSV rebuilt: 692 rows, PRE-DG split into PRE-DG-01 ... 06): the manifest's "tsv" block records the
sha256 of the TSV columns this script reads (not the file's -- the TSV header records this manifest's sha256), and every
run asserts, before writing, that each set's membership and content (row references aside) equal the S-build on disk
(check_invariance; --allow-set-changes overrides, never used pre-freeze).

§1.6 HGNC rule as implemented: an identifier given by the source (Ensembl gene id; for KEGG / WebGestalt the Entrez
id; for GO annotations the UniProtKB accession) resolves through the HGNC column of that id when it names exactly one
approved gene; otherwise, and for symbol-only sources, the symbol resolves as approved symbol -> previous symbol ->
alias (exact string); a symbol (or id) matching two or more approved genes at the first tier where it matches is
dropped; every drop is listed. The AHBA universe columns are mapped by the same symbol rule.

Register DRAFT v6 (decisions of the orchestrator under the operator's standing delegation, 2026-09-26; every one taken
after the v5 S-build outcome was seen):
  R1  one name-matching rule for every GO, KEGG, MSigDB, Reactome and figure-label mapping (name_match.py): (a) exact
      name, (b) a synonym of any scope / a former name identifying one live term, (c) case / UK-US / singular-plural
      normalisation identifying one term, else S undefined; the tier and label are recorded per cell
      ('name_match_by_cell'), since cells sharing a set may reach it by different tiers;
  R2  an S-undefined set whose source 1 could lie inside a gated carrier gets the conditional form 'S from <carrier>
      (source 1) if present, by the pre-registered criterion ...; else not auditable (S undefined)' (Zhang, PGC MAGMA,
      Buch's '*Ribosomal structure');
  R3  the pSI token reading ('query tokens <= column tokens') and 'the human brain-region table' = pSI.data
      human$young.adulthood are S-build readings; the mouse cell-type table -> 'not auditable (definition not
      applicable: v4 pinned a mouse table without an orthology rule)';
  R5  the universe is the class matrix's 15,633 columns: a set's members are all columns mapped to its HGNC genes, the
      < 5 / > 1,000 rules count columns, unmapped columns stay in the universe and are never members;
  R12 Enrichr's dated libraries: KEGG_2021_Human for Vairam / Roy (the library the paper names), GO_Biological_Process_2015
      for Romero-Garcia (the one Enrichr GO BP library naming both of the paper's printed terms: the release it used);
  R13 MANIFEST.json records repo files by repo-relative path (external data keep their absolute E:\\data\\asdg paths,
      identical for every clone on this box), so a clean-clone re-run reproduces its hash.

Register DRAFT v6.7 (the orchestrator under the operator's standing delegation, 2026-09-27): the uniform archive rule
(sfari_release_choice: Liu's and Xing's SFARI cells from the Wayback captures, read by the release label each serves, N2;
kegg_archived_releases: complete archived KEGG REST releases count for KEGG rule (ii)); s_build_v66.py builds asdM12 (N1),
re-pins RGD / CTD / Buch's SFARI and builds the near-miss view, whose pins this script writes into MANIFEST.json
(comparators_v6_6.near_miss_view_v6_7).

Register DRAFT v6.8 (the orchestrator under the operator's standing delegation, 2026-09-29, on the v6.7 final re-check; post hoc,
declared): B S2 -- every workbook sheet read passes privacy_guard.py (xlsx_rows / sheet_rows: an identifier-bearing sheet --
wider than 50 columns, or identifier wording / values in its first 6 rows -- is read in declared columns only; Lake 2018 Table
S3 so); Parikshak 2013 supplement 02, Parikshak 2016 Supplementary Table 2 and Kang 2011 MOESM50 were deleted after their
gene-level reductions (reduce_v68.py), which this script reads (REDUCED_V68), the per-set provenance still naming the
original by path and sha256; B S1 -- asdM12 in the near-miss view (s_build_v66.py); C -- Xing's date its first journal
submission (2026-08-31).

Register DRAFT v6.9 (the orchestrator's skeptic re-check 0 A / 2 B / 5 C, under the operator's standing delegation, 2026-09-30;
post hoc, declared): C1 -- the guard's header zone is 20 rows and its widths the populated ones (privacy_guard.py); S2-residual
-- Velmeshev Data S4 (read by s_extract.py) reduced and deleted, the extract unchanged (x_velmeshev), extract_manifest.json
re-pinned; C3 / C5 -- the near-miss label adds '/ name bridge' and Buch's 'ASD rare de novo' moves to the near-miss view
(s_build_v66.py).
Register DRAFT v6.10 (the orchestrator's v6.9 re-check 0 A / 1 B / 4 C; post hoc, declared): the guard reads a sheet by its cells
(ws.reset_dimensions(); read_openpyxl pads rows to the wider of the tag and the cells, so this script's reads are unchanged)
and its wording / bare headers are wider; the near-miss label adds '/ note reading' (s_build_v66.py).
Register DRAFT v6.11 (the v6.10 re-check 0 A / 0 B / 4 C): the guard's gene-symbol exemption under a bare 'ID' only; the PAG
near-miss sets' route text (s_build_v66.py).
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import re
import sys
import tarfile
import tempfile
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
import rdata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import name_match as NM  # noqa: E402  register v6 R1
import privacy_guard as G  # noqa: E402  register v6.8 (B S2): the guard on every workbook sheet read
import reduce_v68 as RV  # noqa: E402  register v6.8 (B S2): the gene-level reductions of the three deleted originals
import s_build_v66 as V66  # noqa: E402  register v6.6 / v6.7: the comparators, the near-miss view, the served-label reading

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

ROOT = Path(__file__).resolve().parents[3]
SRC = Path(r"E:\data\asdg\register_sets_src")
OUT = ROOT / "arcs" / "audit" / "register_sets"
TSV = ROOT / "arcs" / "audit" / "claims_register.tsv"
AHBA = ROOT / "artifacts" / "ahba"
HGNC_FILE = Path(r"E:\data\asdg\explore_public\hgnc_complete_set\hgnc_complete_set_2026-09-04.txt")
VELMESHEV_XLS = Path(r"E:\data\asdg\explore_public\celltype_velmeshev2019\pmc_author_manuscript_suppl"
                     r"\NIHMS1053005-supplement-Data_S4.xls")
CLASSES = ("dk-ctx", "V-DK", "V-AAL", "MIST64")
MIN_SET, BIG_SET = 5, 1000  # register v6 R5: counted in columns of the class matrix
# register v6 R2: the conditional form of an S-undefined set whose source 1 could lie inside a gated carrier
R2_STATUS = "S conditional (source 1 in a gated carrier; else not auditable (S undefined))"
# register v6.1 Q2 as revised by v6.2 P5 / P7 (a): Romero-Garcia's KEGG families (their cells are named in gated tables; per cell
# source 1, else the Enrichr KEGG library chosen by the section 1.6 rule -- KEGG_2015 or KEGG_2016 -- by the name rule)
RG_FAMILY_STATUS = ("S conditional (cells named in a gated carrier; per cell source 1, else the Enrichr KEGG library chosen by "
                    "section 1.6 (KEGG_2015 or KEGG_2016) by the name rule; not auditable if the gated table naming the cells is "
                    "absent or no name reaches that library)")
RG_KEGG_FAMILIES = {"RG-03": "Table S2", "RG-V06": "Supplementary Table S3", "RG-V07": "Supplementary Table S4"}
# register v6.1 Q7, v6.2 P3: Buch's GO-slim fallback sets, built before the freeze from PANTHER 16.0's own annotation as served
BUCH_FALLBACK_STATUS = "built (fallback: used only if MOESM3, source 1 under G1, holds no qualifying list)"
# register v6.1 Q1: the one source-1 criterion (every source-1 branch: Buch, the R2 rows, the RG families, Pagani Supp Table 3)
SOURCE1_CRITERION = ("the source-1 criterion (register 1.6, v6.1 Q1 as revised by v6.2 P1 / P2 / P6, v6.3 O1-O4 / O6 and v6.4 "
                     "N1-N4): a carrier "
                     "list qualifies only if the carrier presents it as the set's membership used as input to the enrichment -- "
                     "a list of gene symbols under a heading naming the set (the cell's pinned name alternatives; rival names "
                     "win when more specific), its sheet name, table title, caption or its own title carrying input wording; "
                     "refused if its own title or the caption carries result wording or names one of the paper's maps, "
                     "subgroups or cohorts (leading edge, core, driving, top, PLS, loading, weight, enriched, decoded, overlap "
                     "or hit genes; '_' and '.' read as spaces), or if its own title, the caption or any column title of its "
                     "table carries statistics wording, or if any cell of its sheet (docx / pdf: its table and caption) other "
                     "than the lists' own genes carries statistics, result or map wording (v6.4 N1); where the paper prints a set "
                     "size the list length must equal it; "
                     "exactly one qualifying list, else the else branch (carrier_tests.json source1_lists, cells keyed by cell "
                     "id; carrier_test.py source1 --cell, one run per pathway for a family); and (v6.5) the list must be "
                     "corroborated: Jaccard >= .80 with the cell's pinned external definition (in the class universe, by HGNC "
                     "gene), else its length equal to the cell's printed size; a cell with neither is never corroborated")
# register v6.5 (1) (orchestrator under the operator's standing delegation, after five review rounds v6.0 -> v6.4): a carrier list
# that passes the text criterion is source 1 only if corroborated -- Jaccard >= .80 with the pinned external definition (in the
# class universe, by HGNC gene), else its length equal to the printed size; a cell with neither can never be corroborated
UNCORROBORATED = ("register v6.5 (1) (orchestrator under the operator's standing delegation; decided after five review rounds, "
                  "v6.0 -> v6.4, showed that the text criterion alone could not exclude result lists): source 1 must be "
                  "corroborated -- Jaccard >= .80 with a pinned external definition of the set (sources 2-3), else a length equal "
                  "to a printed size; this cell has neither, so no carrier list can be corroborated: not auditable (S undefined: "
                  "source 1 uncorroborated)")
R2_REASON = ("register v6 R2 (orchestrator under the operator's standing delegation, 2026-09-26): S from %s (source 1) if "
             "present, by " + SOURCE1_CRITERION + " -- the set named here by %s; built under that gate by the 1.6 rules")
UNIVERSE_CONVENTION = (
    "register v6 R5 (orchestrator under the operator's standing delegation, 2026-09-26; decided after the v5 S-build "
    "outcome was seen): the universe of a class is its matrix's 15,633 columns (abagen gene columns, as A1's calibrated "
    "engine and its plants use them); a set's members are all columns mapped to its HGNC genes (a gene with two columns "
    "contributes both); the 259 unmapped columns stay in the universe (in null pools) and can never be set members; the "
    "< 5 / > 1,000 rules count columns. Consequences declared: 259 unmapped columns, and sets with more columns than HGNC "
    "genes wherever a member gene has two columns (7 genes have two)")

# ---------------------------------------------------------------- pinned inputs (sha256 asserted before use)
PIN = {
    "hgnc": (HGNC_FILE, "6f43d6ff43aa9fdfa5fb2f20a20a7cace66e6e02e2a0dcf19d9b726e2e248d20"),
    "ahba_dk_expr": (AHBA / "dk_expr.csv.gz", "949aeb011a202eeae768d954e868175759de1f9e9f38c54deab88b0d48fd85bf"),
    "ahba_dk_info": (AHBA / "dk_atlas_info.csv", "abb69a9bf976a153b749eb5333e92cf03d4f61f2ce3efd34e49ea6e82f18729b"),
    "ahba_aal_expr": (AHBA / "aal_expr.csv.gz", "44ef457c99e39a5d72586f52dcc1974c5f317b665739978382683d1eb3ccd33c"),
    "ahba_aal_info": (AHBA / "aal_atlas_info.csv", "22e758a7fd525b641ef099028f9329f932a3ff3c1acf65416a8b4574795bf0ee"),
    # MIST64 (register §3.6), built 2026-09-26 08:36 by arcs/audit/src_register/mist64_ahba_matrix.py (another pre-freeze
    # task); its meta.json records the same csv.gz sha256
    "ahba_mist64_expr": (AHBA / "mist64_expr.csv.gz", "7a7a6e22ab9f4e2238e122c609b3d77ea584eb42295afd5d70cc531b0514e153"),
    "ahba_mist64_info": (AHBA / "mist64_atlas_info.csv",
                         "4dafc820bad33634666f37e0b20ee7cd0358ce67005af96bba87e6cc4fe3fcca"),
    # register v6 R12: Enrichr's dated libraries (fetch_v6.py); R1: PANTHER 16.0 GO-slim for Buch's figure labels
    "enrichr_gobp_2013": (SRC / "enrichr_2026-09-26" / "GO_Biological_Process_2013.txt",
                          "df4163623f6e4bfaa05771f2db282b27359fa946c5368948ce4bcf578756f9be"),
    "enrichr_gobp_2015": (SRC / "enrichr_2026-09-26" / "GO_Biological_Process_2015.txt",
                          "f3694d24f39d849e29e7cc29b18e0bdbe509020a94a0b00f16da23d6aa621fe1"),
    "enrichr_gobp_2017": (SRC / "enrichr_2026-09-26" / "GO_Biological_Process_2017.txt",
                          "0a5475d4c682f143d649e8e3282a99cb7198009f5ce8b781b28bfba17ac7cb70"),
    "enrichr_gobp_2017b": (SRC / "enrichr_2026-09-26" / "GO_Biological_Process_2017b.txt",
                           "a4e3800eef2ffe8f7c213b53263b7976b7c298335c0178db4a49468cb629b59b"),
    "enrichr_gobp_2018": (SRC / "enrichr_2026-09-26" / "GO_Biological_Process_2018.txt",
                          "06bdcda19760baecb8bc23c711496b9e682c1ac25fd9e5b8c347bbf3b4a09e91"),
    # register v6.1 Q2 / Q3 / Q7: KEGG release rules (Enrichr snapshots count as releases); Buch's GO-slim fallback annotations
    "enrichr_kegg_2015": (SRC / "enrichr_2026-09-26" / "KEGG_2015.txt",
                          "ac721aed19bbc618c766cf1a76cc3dfa99c1df13055073ebc3d3e112fbf69369"),
    "enrichr_kegg_2026": (SRC / "enrichr_2026-09-26" / "KEGG_2026.txt",
                          "ff014e36320a8e4e09962f81ee7a720fb0001d3c349d021c118766b69fd78139"),
    "enrichr_catalogue": (SRC / "enrichr_2026-09-26" / "datasetStatistics.json",
                          "5add47c2cda081364397d8b91cd2bf6a26c4c8f7b38dfef912bbb561b8644749"),
    "go_2021-11-16_obo": (SRC / "go_2021-11-16" / "go-basic.obo",
                          "dd5f9adc35b6309412161c43f7b39d23dc1954bcb81ff035ffddd379de3e1031"),
    "go_2021-11-16_gaf": (SRC / "go_2021-11-16" / "goa_human.gaf.gz",
                          "125c115aa0d2ccabb9eab61490ec6774dd804d89e84698a58a6ff160a6645d93"),
    "enrichr_kegg_2021_human": (SRC / "enrichr_2026-09-26" / "KEGG_2021_Human.txt",
                                "566763b3402ee1f06612cc48b57e2a0f3f92a9a9e7d1871cc2da9f940e2d609a"),
    "panther_16.0_goslim": (SRC / "panther_16.0_goslim" / "PANTHERGOslim.obo",
                            "fa0bd2db717e387e151334447a4585837e69d417ad7f506ce9a8624eedd5bc46"),
    # register v6.2 P3: PANTHER 16.0's gene -> GO-slim annotation as served; P5: the second Romero-Garcia KEGG candidate
    "panther_16.0_pthr_human": (SRC / "panther_16.0_goslim" / "PTHR16.0_human",
                                "d605cf6019298892dd0de04c51190879a3df25a2e1c26d23cbca6890c8d2590a"),
    "enrichr_kegg_2016": (SRC / "enrichr_2026-09-26" / "KEGG_2016.txt",
                          "a501968146264e4a7ba2b2fb06ff8b9c0cb9a209655f31c095ece502e04d61f5"),
    "go_2024-01-17_obo": (SRC / "go_2024-01-17" / "go-basic.obo",
                          "e078d5406cc78976941578e984e0e3809bc6f4642f8fce404990f5f7c19b0c07"),
    "go_2024-01-17_gaf": (SRC / "go_2024-01-17" / "goa_human.gaf.gz",
                          "3ccc83fe9e18f8c41374787b0cd3b4fb9737a849096b1be5b9f1d3de9ffa7d27"),
    "go_2024-06-17_obo": (SRC / "go_2024-06-17" / "go-basic.obo",
                          "052250ec468b4acc7236edc13e17d39b5975e86990dd2d20b816516d7b17448d"),
    "go_2024-06-17_gaf": (SRC / "go_2024-06-17" / "goa_human.gaf.gz",
                          "a3255148daa387a6f20266175583d55daa6057b7a5a720009ab9d9ab2e8ef604"),
    "gandal2018": (SRC / "gandal2018_science362" / "NIHMS1007359-supplement-Table_S1.xlsx",
                   "e6f9c6ebab41974972f55af09708d565e3fb658e4dc1a6e6e194bed54726ce72"),
    "parikshak2016": (SRC / "parikshak2016" / "NIHMS1050915-supplement-SuppTable2.xlsx",
                      "99faa2965932acf1a0cf1638e3d2812c808109a302904d80ba9acbb99550bf28"),
    "parikshak2013": (SRC / "parikshak2013" / "NIHMS545068-supplement-02.xlsx",
                      "0ba7494ac7a0c883e97e4f571d0a3ed6e15a49b411b0f31d581e26d1ca94bfd2"),
    "polioudakis2019": (SRC / "polioudakis2019" / "NIHMS1534343-supplement-5.xlsx",
                        "bfd5778a54807a395aea6b4e6b881c5158dcdc25c1d023693e09666f155b9dcb"),
    "satterstrom2020": (SRC / "satterstrom2020" / "NIHMS1569306-supplement-Table_S2.xlsx",
                        "f7fc4fe13a768d217577df85fc866a0cff941c29ab383456aab32b0000c279f7"),
    "sanders2015": (SRC / "sanders2015" / "NIHMS723829-supplement-8.xlsx",
                    "aefe5a64139bc4a7a4bc29299efd8f728db412fc167b25264d4c48e558f1a6d0"),
    "sfari_2026-07-12": (SRC / "sfari_gene" / "SFARI-Gene_genes_07-12-2026release_09-25-2026export.csv",
                         "ec3b830ab3f4e185d4d912b6e46a9bca79db39fafd107b37d8b48421be4772d2"),
    "kegg_info": (SRC / "kegg_rest_2026-09-26" / "info_pathway.txt",
                  "2f4ca1bf4da926aff84f219f3b6577a16b338c5f935f65f9bcb013b30d6bfc2d"),
    "kegg_list_pathway": (SRC / "kegg_rest_2026-09-26" / "list_pathway_hsa.txt",
                          "345290b203a665fa7604f36ba51d78095a712c6c02820fb09fde82a5a90c0a3a"),
    "kegg_link": (SRC / "kegg_rest_2026-09-26" / "link_hsa_pathway.txt",
                  "5f03e3ffc03547d065cffb8c4a538007a143648e48b8de37ae528e87459f11b1"),
    "kegg_list_hsa": (SRC / "kegg_rest_2026-09-26" / "list_hsa.txt",
                      "ec3c5896ed611b526b681d40a95ac593b802954574a36e357bf1827e70db94e3"),
    "msigdb_c5_gobp_2023.1": (SRC / "msigdb_2023.1.Hs" / "c5.go.bp.v2023.1.Hs.symbols.gmt",
                              "4f684f8c901249b2b822c0a5c196c1dc50ed305299e98803cf2b50eaec7fbf57"),
    "wg_reactome_gmt": (SRC / "webgestalt_current" / "hsapiens_pathway_Reactome_entrezgene.gmt",
                        "33f64f360ae9fa8a6b69633e8f33b28364bb7009cd79cacbb8e28f6f3d160e2f"),
    "wg_reactome_des": (SRC / "webgestalt_current" / "hsapiens_pathway_Reactome_entrezgene.des",
                        "931cbef24697daf13f40482d6dda83b4c5528302a0f5ca36d2c8320930736dc4"),
    "wg_gobp_gmt": (SRC / "webgestalt_current" / "hsapiens_geneontology_Biological_Process_entrezgene.gmt",
                    "183e39da97a9ec8adb11d161ec7d3ad631a4335b37ee18f0d482a45031a34d43"),
    "wg_gobp_des": (SRC / "webgestalt_current" / "hsapiens_geneontology_Biological_Process_entrezgene.des",
                    "b3561694255dac0018716dce917791ac59215002dcbf68ff3d7b9f1e4d04963a"),
    "tissueenrich_1.24.1": (SRC / "tissueenrich_bioc3.19" / "TissueEnrich_1.24.1.tar.gz",
                            "35fe1f957a49ab8819dd2be0b11e007b08c388b224c2ceb5e860ece2d4a65509"),
    "psi_data_1.0": (SRC / "psi_data" / "pSI.data_1.0.tar_.gz",
                     "41387b14bf8d951c9d5d8e7c7bf1964c4112cc178dbd65561f45b029da75a5a4"),
    "lake2018": (SRC / "lake2018" / "41587_2018_BFnbt4038_MOESM11_ESM.xlsx",
                 "6960f9aefa7397c4814cd3a6b9e9ac4b2ee137d4d1fac0f36d6b48cdba78ec85"),
    "moreau_16p": (SRC / "moreau2020_locus" / "cnv_genes_cnv16p112.csv",
                   "b2b9dbfbb556a465049451d3950a64bdba6f3e54145ded8de8e5284828d4e8a0"),
    "moreau_22q": (SRC / "moreau2020_locus" / "cnv_genes_cnv22q112.csv",
                   "3838d75f5495c876d178003e48335ef721c40d2378e19495f4d5594bec2f4a5f"),
    "segura_s4": (SRC / "segura2025_tables" / "tableS4_satterstrom_1046_symbols.txt",
                  "e1f4638c61e7fbc82a9867ffaff9c8ce8aa6683d88d784fcf9ffc81415721bea"),
    "kang2011_moesm50": (SRC / "kang2011" / "41586_2011_BFnature10523_MOESM50_ESM.xls",
                         "b2bd90951735c6db29070c774aa0c6d65158e7adc3cdd7e00da440e6286a673e"),
    "extract_manifest": (SRC / "extract_manifest.json",  # v6.7: + Voineagu Table 14 (N1), Darnell Table S2A (N7); v6.8: the
                         "639d55a90c8a6618157d10f00aaddf1748e57da3bf1dff1c71e01a26f1f6fe90"),  # reductions (B S2); v6.9: Velmeshev S4 reduced
    # stage-1 extracts (s_extract.py)
    "x_segura_s7": (SRC / "segura2025_tables" / "extract" / "tableS7_terms.tsv",
                    "3d0e38e39acd4cbaf6d9049379ed50ba31d5708ff81a20c6d2c651bef0da73d0"),
    "x_velmeshev": (SRC / "velmeshev2019" / "extract" / "data_s4_ASD_DEGs.tsv",
                    "8700dfafce49c9fd704b123f0fa4949ea00884cd6fbda22412a73178f34d7156"),
    "x_shin": (SRC / "shin2018" / "extract" / "tableS1_panels.tsv",
               "53bf0dafa901c757e799a8c558d0f90b1a4b2221869e4a515af65022d175d0de"),
    "x_grove": (SRC / "grove2019_magma" / "extract" / "table10_top25.tsv",
                "9dc6438776556f22b5fc5944ca22ec7b398491382c2ffa52c3650bbac6846696"),
    "x_kang_modules": (SRC / "kang2011" / "extract" / "table9_modules.tsv",
                       "0e086e5a90eda1dec9a6ccea1a1f9f9c39cd33cc3bddc9ef47b97a3c280ac7a2"),
    # register v6.7 (2) / N2: the uniform archive rule -- every SFARI genes-CSV capture with a distinct content digest, the
    # release label each capture serves, the KEGG REST files as captured 2024-09-16 and their CDX listings
    "sfari_cap_20201031090127": (SRC / "sfari_wayback_captures" / "SFARI-Gene_genes_capture_20201031090127.csv",
                               "7e83a3a4ee4cd6c73619ea5e04eba904bc9b554b1b47c896844e0acc201ade43"),
    "sfari_cap_20210516060025": (SRC / "sfari_wayback_captures" / "SFARI-Gene_genes_capture_20210516060025.csv",
                               "f0b9474f4c13a516a538dfc8d82f2438497950587b53ef5145d108d4d1a5fe3f"),
    "sfari_cap_20210731184201": (SRC / "sfari_wayback_captures" / "SFARI-Gene_genes_capture_20210731184201.csv",
                               "63a97d183e63722e16bb32d0f4ddcca1498f9b00b84c75d3d75f275355b28588"),
    "sfari_cap_20211022034409": (SRC / "sfari_wayback_captures" / "SFARI-Gene_genes_capture_20211022034409.csv",
                               "68a98e1f69076f4996eedd0db4e7ca20c8a7eac3a9c4f6d395be33a78466583d"),
    "sfari_cap_20220124104055": (SRC / "sfari_wayback_captures" / "SFARI-Gene_genes_capture_20220124104055.csv",
                               "243f622811940b18db900a079d34dccc6f32d08d6adb5ea3334c9dd34bb44714"),
    "sfari_cap_20220701200121": (SRC / "sfari_wayback_captures" / "SFARI-Gene_genes_capture_20220701200121.csv",
                               "adcba4705640d1fbd23a7a39a033326c7c6c962a498aa569306e6dbb67f3b1e5"),
    "sfari_cap_20221206204848": (SRC / "sfari_wayback_captures" / "SFARI-Gene_genes_capture_20221206204848.csv",
                               "5f13a84995509cf55ae727ac8f93d52a3cfc724a678e0c265e20df5e3ffbcdcb"),
    "sfari_cap_20230320190240": (SRC / "sfari_wayback_captures" / "SFARI-Gene_genes_capture_20230320190240.csv",
                               "5b51c7cd25970de9ccc8bbb0a82154b6d05c5e56e004956b5844d29ea084ab3c"),
    "sfari_cap_20231010173503": (SRC / "sfari_wayback_captures" / "SFARI-Gene_genes_capture_20231010173503.csv",
                               "f49be0bd6867d4085cbe4c3676855d03388438542da150c6936eaaeb2e9e8561"),
    "sfari_cap_20231205085030": (SRC / "sfari_wayback_captures" / "SFARI-Gene_genes_capture_20231205085030.csv",
                               "c0b1ca022a2c200501827f0aa840879a23e7d40f073404d957972e8e284a43e7"),
    "sfari_cap_20240324110733": (SRC / "sfari_wayback_captures" / "SFARI-Gene_genes_capture_20240324110733.csv",
                               "ccfaa57d46cdaa7bf3715c84e05325cfdae71451f5f3f4cea20a3ad151e3b739"),
    "sfari_cap_20240515204151": (SRC / "sfari_wayback_captures" / "SFARI-Gene_genes_capture_20240515204151.csv",
                               "753a6c59fe6e016f7d2f6f157860af1ad00b77ffefc1b5f6cd0ba678992a683f"),
    "sfari_labels": (SRC / "sfari_wayback_captures" / "served_labels.json",
                     "8c74b895630f95f31aa8b3bb6fda62f3ce149f9da1b3d5b5490e4f6c1488bab3"),
    "kegg_wb_link": (SRC / "kegg_wayback_2024-09-16" / "link_hsa_pathway.txt",
                     "0230fd31788465166e20d7e54bbe8991510f66081b06aa0088dfc672f5bdeba0"),
    "kegg_wb_list": (SRC / "kegg_wayback_2024-09-16" / "list_pathway_hsa.txt",
                     "5248ec4d3e7c1d9e18e4afd753031136a66422347f761a92ea1a18b249d6dd95"),
    "kegg_cdx_link": (SRC / "kegg_wayback_2024-09-16" / "cdx_link_hsa_pathway.json",
                      "3c9c6004f5e8d6056c9c27c552d07232113601da142c41f9625f846315844eee"),
    "kegg_cdx_list": (SRC / "kegg_wayback_2024-09-16" / "cdx_list_pathway_hsa.json",
                      "44d0984dd42f3b000c1606933b7d5381bee4f8d712da76f24e3320aedd080dc1"),
}
# where each pinned input came from (full provenance: E:\data\asdg\register_sets_src\<source>\SOURCE.md)
URL = {
    "gandal2018": "https://pmc.ncbi.nlm.nih.gov/articles/instance/6443102/bin/NIHMS1007359-supplement-Table_S1.xlsx",
    "parikshak2016": "https://pmc.ncbi.nlm.nih.gov/articles/instance/7102905/bin/NIHMS1050915-supplement-SuppTable2.xlsx",
    "parikshak2013": "https://pmc.ncbi.nlm.nih.gov/articles/instance/3934107/bin/NIHMS545068-supplement-02.xlsx",
    "polioudakis2019": "https://pmc.ncbi.nlm.nih.gov/articles/instance/6831089/bin/NIHMS1534343-supplement-5.xlsx",
    "satterstrom2020": "https://pmc.ncbi.nlm.nih.gov/articles/instance/7250485/bin/NIHMS1569306-supplement-Table_S2.xlsx",
    "sanders2015": "https://pmc.ncbi.nlm.nih.gov/articles/instance/4624267/bin/NIHMS723829-supplement-8.xlsx",
    "sfari_2026-07-12": "https://gene.sfari.org/wp-content/themes/sfari-gene/utilities/download-csv.php?api-endpoint=genes",
    "kegg": "https://rest.kegg.jp/{info/pathway,list/pathway/hsa,link/hsa/pathway,list/hsa}",
    "msigdb_c5_gobp_2023.1": "https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2023.1.Hs/c5.go.bp.v2023.1.Hs.symbols.gmt",
    "webgestalt": "https://www.webgestalt.org/api/geneset?organism=hsapiens&database=<db>&standardId=entrezgene&fileType=<gmt|des>",
    "tissueenrich_1.24.1": "https://bioconductor.org/packages/3.19/bioc/src/contrib/TissueEnrich_1.24.1.tar.gz",
    "psi_data_1.0": "https://sites.wustl.edu/doughertylab/files/2014/01/pSI.data_1.0.tar_.gz",
    "lake2018": "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fnbt.4038/MediaObjects/41587_2018_BFnbt4038_MOESM11_ESM.xlsx",
    "go": "https://release.geneontology.org/<release>/{ontology/go-basic.obo,annotations/goa_human.gaf.gz}",
    "shin2018": "https://pmc.ncbi.nlm.nih.gov/articles/instance/13017599/bin/cercor_28_9_3267_s1.zip",
    "grove2019": "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41588-019-0344-8/MediaObjects/41588_2019_344_MOESM1_ESM.pdf",
    "velmeshev2019": "https://pmc.ncbi.nlm.nih.gov/articles/instance/7678724/bin/NIHMS1053005-supplement-Data_S4.xls",
    "kang2011": "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fnature10523/MediaObjects/41586_2011_BFnature10523_MOESM50_ESM.xls",
    "moreau2020": "https://github.com/kkumar-iitkgp-livia/GeneExp_and_CNV_FCsignatures @ 9e8af9c1 data/cnv_genes_cnv{16p112,22q112}.csv",
    "segura2025": "Europe PMC PMC12700815 supplementaryFiles (MOESM2 pdf); Table S4 parsed 2026-09-24 (segura2024symptommapping/SOURCE.md)",
    "enrichr": "https://maayanlab.cloud/Enrichr/geneSetLibrary?mode=text&libraryName=<name> (fetched 2026-09-26; no identifier sent)",
    "panther_16.0_goslim": "https://data.pantherdb.org/PANTHER16.0/ontology/PANTHERGOslim.obo",
    "panther_16.0_pthr_human": ("https://data.pantherdb.org/ftp/sequence_classifications/16.0/PANTHER_Sequence_Classification_files/"
                                "PTHR16.0_human (fetched 2026-09-26; no identifier sent)"),
}


def relpath(p) -> str:
    """register v6 R13: a repo file by its repo-relative POSIX path; external data keep their absolute path."""
    p = Path(p)
    try:
        return p.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(p)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# register v6.8 (B S2; the orchestrator under the operator's standing delegation): three originals held identifier-bearing sheets
# and were deleted after their gene-level reductions (reduce_v68.py, JSON sheet dumps beside them); the build reads the
# reduction, pinned here, whose record names the original's sha256 (asserted equal to PIN). The per-set provenance ('files')
# keeps naming the original -- the published file the rows come from -- by path and sha256, as for the v6.6 / v6.7 extracts.
REDUCED_V68 = {
    "parikshak2016": (RV.reduced_path("parikshak2016"), "8febe6e62db4f123a6d3adbf69842399c54b500051ea1cf771cf176d3e894ae3"),
    "parikshak2013": (RV.reduced_path("parikshak2013"), "2f2ea75c554c9df1d44b11e299d44c0ba5c943c8e209fe3c636e21e6e8199ebc"),
    "kang2011_moesm50": (RV.reduced_path("kang2011"), "a4575d50cf8f875307f030b9ab2af64cb208675e95ecfd4693e49e9e0acb4303"),
    # v6.8 round 2 (the orchestrator under the operator's standing delegation): every flagged workbook a builder reads, reduced
    # to exactly the sheets and columns read (kept columns at their original positions)
    "gandal2018": (RV.reduced_path("gandal2018"), "c540d1e1e5fcaf319d73b56f64e64684baae8b37e91bc97a2588c462f4609b07"),
    "polioudakis2019": (RV.reduced_path("polioudakis2019"), "21dbf05341a94010ef6a0c2f398e7d01317f744f1a88a18c3692d7c81f18c8c7"),
    "satterstrom2020": (RV.reduced_path("satterstrom2020"), "89472a90dd770eb48687f446abc0c4d118c8bb91ee34eb5a33a311c181d9dce7"),
    "lake2018": (RV.reduced_path("lake2018"), "c65fff703128cc512029d8828315ea803daf9fcc076403c0180a0382f7e535a7"),
}


def pinned(key: str) -> Path:
    if key in REDUCED_V68:  # v6.8 (B S2): the reduction (sha256) and its record of the original (PIN's sha256)
        p, h = REDUCED_V68[key]
        RV.load(p, h, PIN[key][1])
        return p
    p, h = PIN[key]
    got = sha256(p)
    assert got == h, f"{key}: sha256 {got} != pinned {h} ({p})"
    return p


def fileref(*keys: str) -> list[dict]:
    return [{"path": relpath(PIN[k][0]), "sha256": PIN[k][1]} for k in keys]


def read_tsv(p: Path) -> list[dict]:
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_json(p: Path, obj) -> str:
    txt = json.dumps(obj, indent=1, ensure_ascii=False) + "\n"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(txt.encode("utf-8"))
    assert p.read_bytes().decode("utf-8") == txt, f"read-back differs: {p}"
    assert json.loads(p.read_text(encoding="utf-8")) == json.loads(txt)
    return sha256(p)


# ---------------------------------------------------------------- HGNC (§1.6)
def _split(x) -> list[str]:
    return [t.strip() for t in str(x).split("|") if t.strip()] if isinstance(x, str) else []


class HGNC:
    def __init__(self):
        cs = pd.read_csv(pinned("hgnc"), sep="\t", dtype=str, keep_default_na=False)
        assert cs["symbol"].is_unique and cs["hgnc_id"].is_unique and (cs["status"] == "Approved").all()
        self.n = len(cs)
        self.approved = set(cs["symbol"])
        self.prev, self.alias = defaultdict(set), defaultdict(set)
        self.ids = {k: defaultdict(set) for k in ("ensembl", "entrez", "uniprot", "rnacentral", "hgnc")}
        for sym, hid in zip(cs["symbol"], cs["hgnc_id"]):  # register v6.2 P3: PANTHER names genes by HGNC id
            self.ids["hgnc"][hid.strip()].add(sym)
        for sym, prev, alias, ens, ent, uni, rnc in zip(cs["symbol"], cs["prev_symbol"], cs["alias_symbol"],
                                                        cs["ensembl_gene_id"], cs["entrez_id"], cs["uniprot_ids"],
                                                        cs["rna_central_id"]):
            for u in _split(rnc):
                self.ids["rnacentral"][u].add(sym)
            for p in _split(prev):
                self.prev[p].add(sym)
            for a in _split(alias):
                self.alias[a].add(sym)
            if ens.strip():
                self.ids["ensembl"][ens.strip()].add(sym)
            if ent.strip():
                self.ids["entrez"][ent.strip()].add(sym)
            for u in _split(uni):
                self.ids["uniprot"][u].add(sym)

    def symbol(self, s) -> tuple[str | None, str]:
        if s is None:
            return None, "no symbol given"
        if not isinstance(s, str):
            return None, f"non-string cell ({type(s).__name__}; e.g. an Excel date)"
        s = s.strip()
        if not s:
            return None, "empty"
        if s in self.approved:
            return s, "approved"
        for tab, how in ((self.prev, "previous"), (self.alias, "alias")):
            if s in tab:
                t = tab[s]
                if len(t) == 1:
                    return next(iter(t)), how
                return None, f"ambiguous {how} symbol ({len(t)} approved genes)"
        return None, "unmapped symbol"

    def resolve(self, kind: str | None, ident, sym) -> tuple[str | None, str]:
        if kind and isinstance(ident, str) and ident.strip():
            key = ident.strip()
            if kind == "ensembl":
                key = key.split(".")[0]
            if kind == "uniprot":
                key = key.split("-")[0]
            if kind == "rnacentral":
                key = key.split("_")[0]
            if kind == "nongene":
                return None, "non-gene object (ComplexPortal complex)"
            hit = self.ids[kind].get(key, set())
            if len(hit) == 1:
                return next(iter(hit)), f"{kind} id"
            s, how = self.symbol(sym)
            if s:
                return s, f"{how} (symbol; {kind} id {'ambiguous' if hit else 'not in HGNC'})"
            return None, f"{kind} id {'ambiguous' if hit else 'not in HGNC'}; symbol: {how}"
        return self.symbol(sym)


# ---------------------------------------------------------------- class universes (§3.1 matrices, A1 loaders)
def load_universes(hg: HGNC) -> tuple[dict, dict]:
    uni, meta = {}, {}
    for base, key_e, key_i in (("dk", "ahba_dk_expr", "ahba_dk_info"), ("aal", "ahba_aal_expr", "ahba_aal_info"),
                               ("mist64", "ahba_mist64_expr", "ahba_mist64_info")):
        expr = pd.read_csv(pinned(key_e), index_col=0)
        info = pd.read_csv(pinned(key_i)).set_index("id")
        keep = [i for i in expr.index if info.loc[i, "hemisphere"] in ("L", "B") and not expr.loc[i].isna().all()]
        e = expr.loc[keep]
        classes = info.loc[keep, "structure"].to_numpy()
        variants = {"dk": [("V-DK", np.ones(len(e), bool)), ("dk-ctx", classes == "cortex")],
                    "aal": [("V-AAL", np.ones(len(e), bool))],
                    "mist64": [("MIST64", np.ones(len(e), bool))]}[base]
        for cname, mask in variants:
            X = e.loc[mask]
            assert not X.isna().any().any()
            sd = X.to_numpy(float).std(0, ddof=1)
            cols = list(np.asarray(X.columns)[sd > 1e-12])
            a2c, how = defaultdict(list), Counter()
            unmapped = []
            for c in cols:
                s, h = hg.symbol(c)
                how[h.split(" (")[0]] += 1
                if s:
                    a2c[s].append(c)
                else:
                    unmapped.append({"column": c, "reason": h})
            coll = {k: v for k, v in a2c.items() if len(v) > 1}
            uni[cname] = {k: sorted(v) for k, v in a2c.items()}
            meta[cname] = {"matrix": relpath(PIN[key_e][0]), "matrix_sha256": PIN[key_e][1], "n_parcels": int(mask.sum()),
                           "n_genes": len(cols), "n_columns": len(cols),
                           "n_columns_mapped": sum(len(v) for v in a2c.values()),
                           "n_constant_dropped": int((sd <= 1e-12).sum()),
                           "hgnc_mapping": dict(sorted(how.items())), "n_unmapped": len(unmapped),
                           "unmapped": unmapped, "n_approved_distinct": len(a2c),
                           "approved_with_several_columns": dict(sorted(coll.items()))}
    return uni, meta


# ---------------------------------------------------------------- GO
def read_obo(path: Path) -> tuple[dict, str | None]:
    """terms of an .obo file: id -> {name, ns, obsolete, parents (is_a, part_of), syn_all [(text, scope)]}."""
    terms, cur, dv = {}, None, None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("data-version:"):
                dv = line.split(":", 1)[1].strip()
            if line == "[Term]":
                cur = {"parents": set(), "syn": [], "syn_all": [], "obsolete": False}
                continue
            if line.startswith("[") and line.endswith("]"):
                cur = None
                continue
            if cur is None or not line:
                if not line and cur is not None and "id" in cur:
                    terms[cur["id"]] = cur
                    cur = None
                continue
            k, _, v = line.partition(": ")
            if k == "id":
                cur["id"] = v
            elif k == "name":
                cur["name"] = v
            elif k == "namespace":
                cur["ns"] = v
            elif k == "is_obsolete" and v == "true":
                cur["obsolete"] = True
            elif k == "is_a":
                cur["parents"].add(v.split(" ! ")[0].strip())
            elif k == "relationship" and v.startswith("part_of "):
                cur["parents"].add(v.split()[1])
            elif k == "synonym":
                mm = re.match(r'"(.*)"\s+(EXACT|BROAD|NARROW|RELATED)', v)
                cur["syn_all"].append((mm.group(1), mm.group(2)))
                if mm.group(2) == "EXACT":
                    cur["syn"].append(mm.group(1))
    if cur is not None and "id" in cur:
        terms[cur["id"]] = cur
    return terms, dv


def obo_candidates(terms: dict, ns: str | None) -> list[dict]:
    """register v6 R1: the name rule's candidates (live = not obsolete; within the namespace the paper names, if any)."""
    return [{"id": t, "name": d["name"], "synonyms": d["syn_all"], "live": not d["obsolete"]}
            for t, d in sorted(terms.items()) if "name" in d and (ns is None or d.get("ns") == ns)]


class GO:
    def __init__(self, release: str):
        self.release = release
        self.terms = {}
        cur = None
        with open(pinned(f"go_{release}_obo"), encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if line.startswith("data-version:"):
                    self.data_version = line.split(":", 1)[1].strip()
                if line == "[Term]":
                    cur = {"parents": set(), "syn": [], "obsolete": False}
                    continue
                if line.startswith("[") and line.endswith("]"):
                    cur = None
                    continue
                if cur is None or not line:
                    if not line and cur is not None and "id" in cur:
                        self.terms[cur["id"]] = cur
                        cur = None
                    continue
                k, _, v = line.partition(": ")
                if k == "id":
                    cur["id"] = v
                elif k == "name":
                    cur["name"] = v
                elif k == "namespace":
                    cur["ns"] = v
                elif k == "is_obsolete" and v == "true":
                    cur["obsolete"] = True
                elif k == "is_a":
                    cur["parents"].add(v.split(" ! ")[0].strip())
                elif k == "relationship" and v.startswith("part_of "):
                    cur["parents"].add(v.split()[1])
                elif k == "synonym":
                    mm = re.match(r'"(.*)"\s+(EXACT|BROAD|NARROW|RELATED)', v)
                    cur.setdefault("syn_all", []).append((mm.group(1), mm.group(2)))
                    if mm.group(2) == "EXACT":
                        cur["syn"].append(mm.group(1))
        if cur is not None and "id" in cur:
            self.terms[cur["id"]] = cur
        self.children = defaultdict(set)
        for t, d in self.terms.items():
            for p in d["parents"]:
                self.children[p].add(t)
        self.ann = defaultdict(set)  # GO id -> {(db, object id, symbol)}
        self.n_ann = Counter()
        with gzip.open(pinned(f"go_{release}_gaf"), "rt", encoding="utf-8") as f:
            for line in f:
                if line.startswith("!"):
                    if line.startswith("!date-generated") or line.startswith("!Generated"):
                        self.gaf_generated = line.strip()
                    continue
                c = line.rstrip("\n").split("\t")
                if "NOT" in c[3].split("|"):
                    self.n_ann["excluded NOT"] += 1
                    continue
                if c[6] == "ND":
                    self.n_ann["excluded ND"] += 1
                    continue
                self.ann[c[4]].add((c[0], c[1], c[2]))
                self.n_ann["kept"] += 1

    def resolve(self, name: str, ns: str | None) -> tuple[str | None, dict]:
        """register v6 R1: the one name rule (name_match.py), among live terms of the namespace the paper names."""
        if not hasattr(self, "_cand"):
            self._cand = {}
        if ns not in self._cand:
            self._cand[ns] = [{"id": t, "name": d["name"], "synonyms": d.get("syn_all", []), "live": not d["obsolete"]}
                              for t, d in sorted(self.terms.items()) if "name" in d and (ns is None or d.get("ns") == ns)]
        rec = NM.match(name, self._cand[ns])
        return rec["id"], rec

    def members(self, term: str) -> tuple[list[dict], int]:
        seen, stack = {term}, [term]
        while stack:
            for c in self.children.get(stack.pop(), ()):
                if c not in seen:
                    seen.add(c)
                    stack.append(c)
        objs = set()
        for t in seen:
            objs |= self.ann.get(t, set())
        kind = {"UniProtKB": "uniprot", "RNAcentral": "rnacentral", "ComplexPortal": "nongene"}
        raw = [{"kind": kind.get(db), "id": oid, "symbol": sym, "db": db} for db, oid, sym in sorted(objs)]
        return raw, len(seen)


GO_NS = {"BP": "biological_process", "CC": "cellular_component", "MF": "molecular_function"}


# ---------------------------------------------------------------- source loaders
def xlsx_rows(path: Path, sheet: str, declared=None, header_row: int | None = None, label: str = "") -> list[tuple]:
    """register v6.8 (B S2): every sheet read passes the privacy guard -- an identifier-bearing sheet (wider than 50 columns, or
    identifier wording / values in its first 6 rows) is read only in its declared columns (every other cell None), else the
    read is refused; nothing of a sheet is printed."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = G.read_openpyxl(wb[sheet], declared, header_row, label or path.name)
    wb.close()
    return rows


def sheet_rows(key: str, sheet: str, declared=None, header_row: int | None = None) -> list[tuple]:
    """a pinned workbook's sheet through the guard; for the three deleted originals, their reductions (v6.8, B S2)."""
    if key in REDUCED_V68:
        p, h = REDUCED_V68[key]
        return RV.rows(RV.load(p, h, PIN[key][1]), sheet, declared, header_row, label=key + " (reduced)")
    return xlsx_rows(pinned(key), sheet, declared, header_row, key)


def _fdr_p16(h: list) -> int:
    """Parikshak 2016 TableS2a's ASD vs CTL FDR column: the one header starting 'FDR-adjusted P value, ASD vs C' (v6.7 read
    index 10 of the original, asserted; its reduction keeps exactly that column)."""
    j = [k for k, x in enumerate(h) if isinstance(x, str) and x.startswith("FDR-adjusted P value, ASD vs C")]
    assert len(j) == 1, len(j)
    return j[0]


def _lake_block(h: list) -> list[int]:
    """Lake 2018 Table S3 (wider than 50 columns): the 'All Clusters' block's gene column and its cluster column (+ 6)."""
    j = [k for k, x in enumerate(h) if x == "All Clusters"]
    assert len(j) == 1, len(j)
    return [j[0], j[0] + 6]


class Sources:
    def __init__(self):
        self._c = {}

    def get(self, key, fn):
        if key not in self._c:
            self._c[key] = fn()
        return self._c[key]

    def gandal(self):
        def f():
            rows = sheet_rows("gandal2018", "DGE")
            h = list(rows[0])
            ie, isym, ifc, iq = (h.index(c) for c in ("ensembl_gene_id", "gene_name", "ASD.log2FC", "ASD.fdr"))
            down, up, n = [], [], 0
            for r in rows[1:]:
                if r[ie] is None:
                    continue
                n += 1
                q, fc = r[iq], r[ifc]
                if isinstance(q, (int, float)) and q < 0.05 and isinstance(fc, (int, float)):
                    rec = {"kind": "ensembl", "id": r[ie], "symbol": r[isym]}
                    (down if fc < 0 else up if fc > 0 else []).append(rec)
            return {"down": down, "up": up, "n_rows": n}
        return self.get("gandal", f)

    def parikshak2016(self):
        def f():
            # v6.8 (B S2): the reduction of Supplementary Table 2 (TableS2a is wider than 50 columns: its five declared columns)
            rows = sheet_rows("parikshak2016", "TableS2a", declared=lambda h: [
                h.index("ENSEMBL ID"), h.index("HGNC Symbol"), h.index("log2(FC) ASD vs CTL"), _fdr_p16(h),
                h.index("WGCNA Module Label")], header_row=1)
            h = list(rows[1])
            ie, isym = h.index("ENSEMBL ID"), h.index("HGNC Symbol")
            ifc, iq, im = h.index("log2(FC) ASD vs CTL"), _fdr_p16(h), h.index("WGCNA Module Label")
            out = {"up": [], "down": [], "mod": defaultdict(list), "n_rows": 0}
            for r in rows[2:]:
                if r[ie] is None:
                    continue
                out["n_rows"] += 1
                rec = {"kind": "ensembl", "id": r[ie], "symbol": r[isym]}
                if isinstance(r[iq], (int, float)) and r[iq] < 0.05:
                    if r[ifc] > 0:
                        out["up"].append(rec)
                    elif r[ifc] < 0:
                        out["down"].append(rec)
                out["mod"][int(r[im])].append(rec)
            return out
        return self.get("p16", f)

    def parikshak2013(self):
        def f():
            # v6.8 (B S2): the reduction of supplement 02 (TableS1A is wider than 50 columns: its three declared columns)
            cols = ["ENSEMBL GENE ID", "Gene Symbol", "Module Label"]
            rows = sheet_rows("parikshak2013", "TableS1A", declared=cols, header_row=2)
            h = list(rows[2])
            i0, i1, i6 = (h.index(c) for c in cols)
            mod = defaultdict(list)
            for r in rows[3:]:
                if r[i0] is None:
                    continue
                mod[str(r[i6]).strip()].append({"kind": "ensembl", "id": r[i0], "symbol": r[i1]})
            return mod
        return self.get("p13", f)

    def polioudakis(self):
        def f():
            rows = sheet_rows("polioudakis2019", "Cluster enriched genes")
            assert list(rows[0][:3]) == ["Ensembl", "Gene", "Cluster"]
            cl = defaultdict(list)
            for r in rows[1:]:
                if r[2] is None:
                    continue
                cl[str(r[2])].append({"kind": "ensembl", "id": r[0], "symbol": r[1]})
            return cl
        return self.get("pol", f)

    def velmeshev(self):
        def f():
            rows = read_tsv(pinned("x_velmeshev"))
            assert all(float(r["q_value"]) < 0.05 for r in rows)
            return [{"kind": "ensembl", "id": r["gene_id"], "symbol": r["gene_name"]} for r in rows], len(rows)
        return self.get("vel", f)

    def satterstrom(self):
        def f():
            rows = sheet_rows("satterstrom2020", "102_ASD")
            h = list(rows[0])
            ig, ie = h.index("gene"), h.index("ensembl_gene_id")
            out = [{"kind": "ensembl", "id": r[ie], "symbol": r[ig]} for r in rows[1:] if r[ig] and r[ie]]
            assert len(out) == 102, len(out)
            return out
        return self.get("sat", f)

    def sfari(self):
        def f():
            with open(pinned("sfari_2026-07-12"), encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            return rows
        return self.get("sfari", f)

    def sanders(self):
        def f():
            rows = sheet_rows("sanders2015", "TADA_Scores")
            h = list(rows[0])
            iq, isym = h.index("tadaFdrAscSscExomeSscAgpSmallDel"), h.index("TadaGeneName")
            out = [{"kind": None, "id": None, "symbol": r[isym]} for r in rows[1:]
                   if isinstance(r[iq], (int, float)) and r[iq] <= 0.1]
            assert len(out) == 65, len(out)
            return out
        return self.get("san", f)

    def kegg(self):
        def f():
            names = {}
            for line in open(pinned("kegg_list_pathway"), encoding="utf-8"):
                pid, nm = line.rstrip("\n").split("\t")
                names[pid] = nm.replace(" - Homo sapiens (human)", "")
            sym = {}
            for line in open(pinned("kegg_list_hsa"), encoding="utf-8"):
                c = line.rstrip("\n").split("\t")
                sym[c[0].split(":")[1]] = c[3].split(";")[0].split(",")[0].strip() if len(c) > 3 else None
            mem = defaultdict(list)
            for line in open(pinned("kegg_link"), encoding="utf-8"):
                p, g = line.rstrip("\n").split("\t")
                eid = g.split(":")[1]
                mem[p.split(":")[1]].append({"kind": "entrez", "id": eid, "symbol": sym.get(eid)})
            info = open(pinned("kegg_info"), encoding="utf-8").read()
            rel = re.search(r"Last update (\S+)", info).group(1)
            return names, mem, rel
        return self.get("kegg", f)

    def msigdb(self):
        def f():
            d = {}
            for line in open(pinned("msigdb_c5_gobp_2023.1"), encoding="utf-8"):
                c = line.rstrip("\n").split("\t")
                d[c[0]] = [{"kind": None, "id": None, "symbol": s} for s in c[2:] if s]
            return d
        return self.get("msig", f)

    def webgestalt(self, db: str):
        def f():
            gm, de = {"reactome": ("wg_reactome_gmt", "wg_reactome_des"), "gobp": ("wg_gobp_gmt", "wg_gobp_des")}[db]
            cand = []  # register v6 R1: the name rule's candidates (id, name as served; no synonyms)
            for line in open(pinned(de), encoding="utf-8"):
                c = line.rstrip("\n").split("\t")
                cand.append({"id": c[0], "name": c[1], "synonyms": [], "live": True})
            mem = {}
            for line in open(pinned(gm), encoding="utf-8"):
                c = line.rstrip("\n").split("\t")
                mem[c[0]] = [{"kind": "entrez", "id": x, "symbol": None} for x in c[2:] if x]
            return cand, mem
        return self.get("wg_" + db, f)

    def _rda_from_tar(self, key: str, member: str, obj: str):
        with tarfile.open(pinned(key), "r:gz") as tf:
            data = tf.extractfile(member).read()
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.rda"
            p.write_bytes(data)
            return rdata.read_rda(str(p))[obj]

    def tissueenrich(self):
        return self.get("te", lambda: self._rda_from_tar("tissueenrich_1.24.1",
                                                         "TissueEnrich/inst/extdata/combine-expression.rda", "dataset"))

    def psi_human(self):
        return self.get("psih", lambda: self._rda_from_tar("psi_data_1.0", "pSI.data/data/human.rda", "human"))

    def psi_mouse(self):
        return self.get("psim", lambda: self._rda_from_tar("psi_data_1.0", "pSI.data/data/mouse.rda", "mouse"))

    def enrichr(self, key: str, go: bool, suffix: str | None = None):
        """register v6 R12: an Enrichr library as served ('term<TAB><TAB>gene<TAB>gene ...'; a gene may carry ',weight').
        GO libraries name terms 'name (GO:nnnnnnn)': the id is split off, the name is what the name rule reads. v6.2 P5: KEGG_2016
        names terms '<name> Homo sapiens <hsa id>' (suffix): the id is split off the same way. A blank line is not a term."""
        def f():
            terms, mem = [], {}
            for line in open(pinned(key), encoding="utf-8"):
                c = line.rstrip("\n").split("\t")
                if not c[0].strip():
                    continue
                m = (re.match(r"^(.*) \((GO:\d{7})\)$", c[0]) if go else re.match(suffix, c[0]) if suffix else None)
                tid = m.group(2) if m else c[0]
                assert tid not in mem, (key, tid)
                terms.append({"id": tid, "name": m.group(1) if m else c[0], "synonyms": [], "live": True})
                mem[tid] = [{"kind": None, "id": None, "symbol": s.split(",")[0].strip()} for s in c[2:] if s.strip()]
            return terms, mem
        return self.get("enr_" + key, f)

    def panther(self):
        def f():
            terms, dv = read_obo(pinned("panther_16.0_goslim"))
            return obo_candidates(terms, None)
        return self.get("panther", f)

    def panther_annotation(self):
        """register v6.2 P3: PANTHER 16.0's gene -> GO-slim annotation as served (PTHR16.0_human: 11 tab-separated columns; gene id
        'HUMAN|HGNC=<n>|UniProtKB=<acc>' (else Ensembl= / GeneID= / another id); GO-slim MF / BP / CC in columns 7 / 8 / 9 as
        'name#GO:id;...'). A gene is a member of a GO-slim term iff the term is listed in its row (the file as served; no
        propagation added). Genes: HGNC id -> HGNC, else Ensembl / Entrez id, else the UniProt accession, else the symbol."""
        def f():
            members, names, cols, kinds = defaultdict(list), {}, defaultdict(set), Counter()
            n_genes = n_annotated = 0
            for line in open(pinned("panther_16.0_pthr_human"), encoding="utf-8"):
                c = line.rstrip("\n").split("\t")
                assert len(c) == 11, len(c)
                n_genes += 1
                ids = dict(x.split("=", 1) for x in c[0].split("|")[1:] if "=" in x)
                if "HGNC" in ids:
                    rec = {"kind": "hgnc", "id": "HGNC:" + ids["HGNC"], "symbol": c[2]}
                elif "Ensembl" in ids:
                    rec = {"kind": "ensembl", "id": ids["Ensembl"], "symbol": c[2]}
                elif "GeneID" in ids:
                    rec = {"kind": "entrez", "id": ids["GeneID"], "symbol": c[2]}
                else:
                    rec = {"kind": "uniprot", "id": c[1], "symbol": c[2]}
                kinds[rec["kind"]] += 1
                any_term = False
                for k, col in ((6, "MF"), (7, "BP"), (8, "CC")):
                    for x in c[k].split(";"):
                        if x:
                            nm, gid = x.rsplit("#", 1)
                            members[gid].append(rec)
                            names.setdefault(gid, nm)
                            cols[gid].add(col)
                            any_term = True
                n_annotated += any_term
            return {"members": members, "names": names, "columns": cols, "n_genes": n_genes, "n_genes_annotated": n_annotated,
                    "gene_id_kinds": dict(sorted(kinds.items()))}
        return self.get("pthr", f)

    def lake(self):
        def f():
            # v6.8 (B S2): Table S3 is wider than 50 columns -- only the 'All Clusters' block's two columns are read
            rows = sheet_rows("lake2018", "Table S3", declared=_lake_block, header_row=3)
            assert str(rows[1][1]).startswith("Table S3. Differentially expressed genes between all snDrop-seq clusters")
            blocks = [(j, v) for j, v in enumerate(rows[3]) if v is not None]
            j = [j for j, v in blocks if v == "All Clusters"]
            assert len(j) == 1
            j = j[0]
            cl = defaultdict(list)
            for r in rows[5:]:
                g = r[j] if j < len(r) else None
                if g is None:
                    continue
                cl[str(r[j + 6])].append({"kind": None, "id": None, "symbol": g})
            return cl
        return self.get("lake", f)


# ---------------------------------------------------------------- KEGG release rule (register 1.6, v6.1 Q2 / Q3)
KEGG_DOWNLOAD_DATE = "2026-09-26"  # the Enrichr catalogue and libraries were fetched on this day (fetch_v6.py)
KEGG_REFERENCE_DATES = {  # the date the rule measures from: the paper's KEGG retrieval date, else its submission date
    "leyhausen2024intrinsic": ("2021-12-14", "retrieval date the paper states (KEGG retrieved 2021-12-14)"),
    "mamat2025molecular": ("2024-08-14", "submission date (Molecular Autism, received 2024-08-14; no retrieval date stated; "
                                         "Metascape's library release is not obtainable)"),
}


SFARI_CAPTURES = ["20201031090127", "20210516060025", "20210731184201", "20211022034409", "20220124104055", "20220701200121",
                  "20221206204848", "20230320190240", "20231010173503", "20231205085030", "20240324110733", "20240515204151"]
SFARI_STATED = {  # register 1.6 SFARI rule: the paper's stated count and its submission date
    "liu2026spatiotemporal": {"count": ("score1", 233), "submission": "2025-09-23",
                              "why": "Liu: 'SFARI score 1' count 233; received 2025-09-23"},
    # v6.8 (C; the orchestrator under the operator's standing delegation, after the v6.7 final re-check -- declared): Xing's date is
    # its first journal submission, 2026-08-31 (the Research Square In-Review timeline: 'first submitted to journal 31 Aug 2026';
    # literature/notes/xing2026interpretable.md); v6.7 used the preprint's posted date 2026-09-18. Same release, same state.
    "xing2026interpretable": {"count": ("all", 1277), "submission": "2026-08-31",
                              "why": "Xing: 'Of the 1,277 genes in the SFARI dataset'; its first journal submission, 31 Aug 2026 "
                                     "(BMC Psychiatry, the Research Square In-Review timeline; v6.8 -- v6.7 read the preprint's "
                                     "posted date 2026-09-18)"},
}


def _sfari_rows(path: Path) -> list[dict]:
    b = path.read_bytes()
    if b[:2] == b"\x1f\x8b":  # one capture is stored as served, gzip-encoded
        b = gzip.decompress(b)
    return list(csv.DictReader(io.StringIO(b.decode("utf-8"))))


def sfari_release_choice() -> dict:
    """register v6.7 (2) and N2 -- the uniform archive rule, the served release label read (a clarification made after the v6.6
    build, post hoc: known which cells it affects; no carrier or result seen): the SFARI states are the Wayback captures of the
    genes CSV (each serving a release label '<release>release_<export>export') and the current download; per paper, the section
    1.6 SFARI rule -- the earliest RELEASE with a state whose stated count equals the paper's (its earliest such state), else the
    last release before the submission, in its state at that date (the most recent capture at or before it serving that
    release; none archived -> the earliest state after it, 'state substituted')."""
    labels = json.loads(pinned("sfari_labels").read_text(encoding="utf-8"))
    cur_name = PIN["sfari_2026-07-12"][0].name
    m = re.fullmatch(r"SFARI-Gene_genes_(\d\d)-(\d\d)-(\d{4})release_(\d\d)-(\d\d)-(\d{4})export\.csv", cur_name)
    cur = {"capture": "download (sfari_gene/, fetched 2026-09-25)", "day": "%s-%s-%s" % (m.group(6), m.group(4), m.group(5)),
           "release": "%s-%s-%s" % (m.group(3), m.group(1), m.group(2)), "export": "%s-%s-%s" % (m.group(6), m.group(4), m.group(5)),
           "digest": None, "served_file_name": cur_name, "pin": "sfari_2026-07-12"}
    states = V66.sfari_states(labels, cur)
    dig2pin = {labels[ts]["digest"]: "sfari_cap_%s" % ts for ts in SFARI_CAPTURES}
    for st in states:
        st.setdefault("pin", None)
        if st["pin"] is None:
            st["pin"] = dig2pin[st["digest"]]  # a capture with the digest of a downloaded one has its content
        rows_ = _sfari_rows(pinned(st["pin"]))
        st.update(all=len(rows_), score1=sum(1 for r in rows_ if r["gene-score"] == "1"),
                  syndromic=sum(1 for r in rows_ if r["syndromic"] == "1"))
    out = {"rule": ("register 1.6 SFARI rule (the earliest release whose stated count equals the paper's, else the last release "
                    "before its submission), applied by v6.7's uniform archive rule to the states the Wayback Machine holds "
                    "(every HTTP-200 capture of the genes CSV, read by the release label it serves -- N2) and the current "
                    "download; v6 ... v6.6 had ruled 'no archived release obtainable (archive.org offline)'"),
           "states": states}
    for paper, st in SFARI_STATED.items():
        cat, n = st["count"]
        hit = None
        for r in sorted({x["release"] for x in states}):
            ok = [x for x in states if x["release"] == r and x[cat] == n]
            if ok:
                hit = ok[0]
                how = ("the earliest release whose %s count equals the paper's %d: release %s, its earliest state with that "
                       "count (capture %s, export %s)" % (cat, n, r, hit["capture"], hit["export"]))
                subst = False
                break
        if hit is None:
            before = sorted({x["release"] for x in states if x["release"] < st["submission"]})
            rb = V66.release_by_labels([x for x in states if x["release"] <= before[-1]], st["submission"])
            hit, subst = rb["state"], rb["substituted"]
            how = ("no archived or current state has %s = %d; the last release before the submission (%s) is %s; %s"
                   % (cat, n, st["submission"], before[-1], rb["outcome"]))
        out[paper] = {"stated": st["why"], "chosen_release": hit["release"], "chosen_state": hit["capture"],
                      "export": hit["export"], "served_file_name": hit["served_file_name"], "pin": hit["pin"],
                      "counts": {k: hit[k] for k in ("all", "score1", "syndromic")}, "state_substituted": subst, "how": how}
    return out


def kegg_archived_releases() -> list[dict]:
    """register v6.7 (2), the uniform archive rule: complete KEGG REST releases the Wayback Machine holds -- the days on which
    both link/hsa/pathway and list/pathway/hsa were captured (HTTP 200); from the pinned CDX listings."""
    days = []
    for key in ("kegg_cdx_link", "kegg_cdx_list"):
        rows_ = json.loads(pinned(key).read_text(encoding="utf-8"))
        hdr = rows_[0]
        days.append({r[hdr.index("timestamp")][:8] for r in rows_[1:] if r[hdr.index("statuscode")] == "200"})
    both = sorted(days[0] & days[1])
    return [{"release": "KEGG REST (archived %s-%s-%s)" % (d[:4], d[4:6], d[6:]), "kind": "KEGG REST as the Wayback Machine "
             "captured it (link/hsa/pathway and list/pathway/hsa on one day)", "span": ["%s-%s-%s" % (d[:4], d[4:6], d[6:])] * 2,
             "numTerms": None} for d in both]


def kegg_release_choice(src) -> dict:
    """register 1.6 KEGG rule (ii), v6.1: the obtainable KEGG release closest in date to the reference date; Enrichr snapshots
    count as releases. A year-named Enrichr snapshot is dated to its year (1 January ... 31 December, capped at the download
    date) and its distance is to the nearest day of that span (0 inside it); KEGG REST is dated by its 'Last update'. Ties go
    to the earlier release (register 1.6). Human libraries only (names KEGG_<year> or KEGG_<year>_Human)."""
    import datetime as _dt
    cat = json.loads(pinned("enrichr_catalogue").read_text(encoding="utf-8"))
    dl = _dt.date.fromisoformat(KEGG_DOWNLOAD_DATE)
    cands = []
    for s in cat["statistics"]:
        m = re.fullmatch(r"KEGG_(\d{4})(_Human)?", s["libraryName"])
        if m:
            y = int(m.group(1))
            lo, hi = _dt.date(y, 1, 1), min(_dt.date(y, 12, 31), dl)
            cands.append({"release": s["libraryName"], "kind": "Enrichr snapshot", "span": [lo.isoformat(), hi.isoformat()],
                          "numTerms": s.get("numTerms")})
    info = pinned("kegg_info").read_text(encoding="utf-8")
    rest = _dt.date.fromisoformat(re.search(r"Last update (\d{4})/(\d{2})/(\d{2})", info).expand(r"\1-\2-\3"))
    cands.append({"release": "KEGG REST", "kind": "KEGG REST (fetched 2026-09-26)", "span": [rest.isoformat(), rest.isoformat()],
                  "numTerms": None})
    cands.extend(kegg_archived_releases())  # register v6.7 (2): the uniform archive rule
    out = {"rule": ("register 1.6 KEGG rule (ii) (v6.1 Q2 / Q3, the orchestrator under the operator's standing delegation): "
                    "the obtainable KEGG release closest in date to the paper's retrieval, else submission, date; Enrichr "
                    "snapshots count as releases, a year-named snapshot dated to its year (distance to the nearest day of "
                    "1 January ... 31 December, capped at the download date %s; 0 inside it), KEGG REST dated by its 'Last "
                    "update'; ties to the earlier release; v6.7 (the uniform archive rule): the complete KEGG REST releases "
                    "the Wayback Machine holds count too (link/hsa/pathway and list/pathway/hsa captured on one day)"
                    % KEGG_DOWNLOAD_DATE), "candidates": cands}
    for key, (d, why) in KEGG_REFERENCE_DATES.items():
        ref = _dt.date.fromisoformat(d)
        rows_ = []
        for c in cands:
            lo, hi = (_dt.date.fromisoformat(x) for x in c["span"])
            dist = 0 if lo <= ref <= hi else (lo - ref).days if ref < lo else (ref - hi).days
            far = max(abs((lo - ref).days), abs((hi - ref).days))
            rows_.append({"release": c["release"], "days_nearest": dist, "days_farthest": far, "span_start": c["span"][0]})
        rows_.sort(key=lambda x: (x["days_nearest"], x["span_start"]))
        out[key] = {"reference_date": d, "reference": why, "distances": rows_, "chosen": rows_[0]["release"],
                    "runner_up": rows_[1]["release"]}
    return out


KEGG_FAMILY_RULE = (
    "register 1.6 KEGG rule for Romero-Garcia's KEGG families (v6.2 P5, the orchestrator under the operator's standing delegation): "
    "the candidates are Enrichr KEGG_2015 and KEGG_2016 (both served while the paper's GO_Biological_Process_2015 was current); "
    "take the library that reaches every pathway name of the gated table by the name rule; both -> KEGG_2015; neither -> the one "
    "reaching more names; a tie -> KEGG_2015. Per cell, the chosen library's pathway the printed name reaches; a name the chosen "
    "library does not reach but the other does takes the other's pathway (reading of 'a name reached by neither -> S undefined'); "
    "a name reached by neither -> that cell not auditable (S undefined); the family not auditable if the gated table naming the "
    "cells is absent or no name reaches the chosen library (P7 (a)). KEGG_2016 terms are read as '<name> Homo sapiens <hsa id>' "
    "(the id split off, as for the GO libraries' '(GO:id)'). v6.3 O4: a printed name carrying '[ _]Homo sapiens[ _]hsaNNNNN' is "
    "read with the suffix split off, and a printed hsa id selects KEGG_2016 (its pathway by that id where KEGG_2016 has it, else "
    "by the name rule); one source-1 run per pathway with one --name, the table's other printed names passed as rival-only "
    "names (--rival; v6.4 N4)")
KEGG16_SUFFIX = r"^(.*) Homo sapiens (hsa\d{5})$"
PRINTED_KEGG_SUFFIX = r"^(.*?)[ _]+Homo[ _]+sapiens[ _]+(hsa\d{5})\s*$"  # register v6.3 O4 (as carrier_tests.json kegg_suffix)


def kegg_family_choice(names: list[str], libs: dict) -> dict:
    """register v6.2 P5: libs = {'KEGG_2015': terms, 'KEGG_2016': terms} (name-rule candidates). Returns the chosen library and
    per name the library and pathway id used (None, None -> S undefined). Run under G1 on the gated table's names; before the
    freeze only on the plants below (public library names)."""
    order = ("KEGG_2015", "KEGG_2016")
    split = {}  # v6.3 O4: a printed '[ _]Homo sapiens[ _]hsaNNNNN' suffix split off
    for n in names:
        m = re.match(PRINTED_KEGG_SUFFIX, n)
        split[n] = (m.group(1).strip(), m.group(2)) if m else (n, None)
    ids16 = {t["id"] for t in libs["KEGG_2016"]}
    reach = {lib: {n: NM.match(split[n][0], libs[lib])["id"] for n in names} for lib in order}
    for n in names:  # a printed hsa id reaches KEGG_2016's pathway of that id
        if split[n][1] in ids16:
            reach["KEGG_2016"][n] = split[n][1]
    full = [lib for lib in order if names and all(reach[lib][n] for n in names)]
    if any(split[n][1] for n in names):  # v6.3 O4: a printed hsa id selects KEGG_2016
        chosen = "KEGG_2016"
    elif full:
        chosen = full[0]
    else:
        cnt = {lib: sum(1 for n in names if reach[lib][n]) for lib in order}
        chosen = "KEGG_2016" if cnt["KEGG_2016"] > cnt["KEGG_2015"] else "KEGG_2015"
    other = order[1 - order.index(chosen)]
    per = {n: ((chosen, reach[chosen][n]) if reach[chosen][n] else (other, reach[other][n]) if reach[other][n] else (None, None))
           for n in names}
    return {"chosen": chosen, "per_name": per, "family_auditable": any(reach[chosen][n] for n in names)}


KEGG_FAMILY_PLANTS = [  # (public pathway names, expected chosen library, expected per-name library)
    (["Ribosome", "Calcium signaling pathway"], "KEGG_2015", {"Ribosome": "KEGG_2015", "Calcium signaling pathway": "KEGG_2015"}),
    (["Ribosome", "AMPK signaling pathway"], "KEGG_2016", {"Ribosome": "KEGG_2016", "AMPK signaling pathway": "KEGG_2016"}),
    (["Ribosome", "Alanine and aspartate metabolism", "Long-term potentiation"], "KEGG_2015",
     {"Ribosome": "KEGG_2015", "Alanine and aspartate metabolism": "KEGG_2015", "Long-term potentiation": "KEGG_2016"}),
    (["Spliceosome", "AMPK signaling pathway", "Alanine and aspartate metabolism"], "KEGG_2016",
     {"Spliceosome": "KEGG_2016", "AMPK signaling pathway": "KEGG_2016", "Alanine and aspartate metabolism": "KEGG_2015"}),
    (["Ribosome", "Pathways of neurodegeneration - multiple diseases"], "KEGG_2015",
     {"Ribosome": "KEGG_2015", "Pathways of neurodegeneration - multiple diseases": None}),
    # v6.3 O4: printed hsa ids select KEGG_2016; the suffix is split off (space or underscore)
    (["Ribosome Homo sapiens hsa03010", "Calcium signaling pathway_Homo_sapiens_hsa04020"], "KEGG_2016",
     {"Ribosome Homo sapiens hsa03010": "KEGG_2016", "Calcium signaling pathway_Homo_sapiens_hsa04020": "KEGG_2016"}),
    (["Ribosome_Homo_sapiens_hsa03010", "Alanine and aspartate metabolism"], "KEGG_2016",
     {"Ribosome_Homo_sapiens_hsa03010": "KEGG_2016", "Alanine and aspartate metabolism": "KEGG_2015"}),
]


def goslim_children(path: Path) -> tuple[dict, dict]:
    """register v6.3 O5: the GO-slim ontology's is_a and part_of edges, parent -> children, kept apart."""
    isa, partof, cur, in_term = defaultdict(set), defaultdict(set), None, False
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("["):
                cur, in_term = None, line == "[Term]"
                continue
            if in_term and line.startswith("id: "):
                cur = line[4:].strip()
            elif cur and line.startswith("is_a: "):
                isa[line[6:].split(" ! ")[0].strip()].add(cur)
            elif cur and line.startswith("relationship: part_of "):
                partof[line.split()[2]].add(cur)
    return isa, partof


def _descendants(term: str, edges: list) -> set:
    seen, stack = {term}, [term]
    while stack:
        t = stack.pop()
        for e in edges:
            for c in e.get(t, ()):
                if c not in seen:
                    seen.add(c)
                    stack.append(c)
    return seen


def kegg_truncation_evidence(src, k21: list, k21mem: dict) -> dict:
    """register v6.2 P4: why LEY-K4 reaches nothing -- Enrichr KEGG_2021_Human truncates KEGG names at ' - ' (counted against the
    pinned KEGG REST list), and the library's 'Pathways of neurodegeneration' entry is closest to hsa05022 (a descriptor)."""
    names, mem, rel = src.kegg()
    enr_names = {t["name"] for t in k21}
    dash = {pid: nm for pid, nm in names.items() if " - " in nm}
    full = sum(1 for nm in dash.values() if nm in enr_names)
    pre = sum(1 for nm in dash.values() if nm not in enr_names and nm.split(" - ")[0] in enr_names)
    e = {g["symbol"] for g in k21mem["Pathways of neurodegeneration"]}
    rest_sym = {pid: {g["symbol"] for g in gl if g["symbol"]} for pid, gl in mem.items()}
    best = sorted(((len(e & g) / len(e | g), pid) for pid, g in rest_sym.items() if g), key=lambda x: (-x[0], x[1]))[:2]
    return {"kegg_rest": "KEGG REST list/pathway/hsa (Last update %s; pinned)" % rel,
            "rest_names_with_dash": len(dash), "in_kegg_2021_human_in_full": full,
            "in_kegg_2021_human_only_as_the_part_before_dash": pre, "in_neither_form": len(dash) - full - pre,
            "kegg_2021_human_names_with_dash": sum(1 for nm in enr_names if " - " in nm),
            "hsa05022_rest_name": names.get("hsa05022"),
            "kegg_2021_human_entry": "Pathways of neurodegeneration", "entry_n_genes": len(e),
            "closest_rest_pathways_by_symbol_jaccard": [{"id": pid, "jaccard": round(j, 3), "n_genes": len(rest_sym[pid])}
                                                         for j, pid in best]}


# ---------------------------------------------------------------- set building
def build_set(hg: HGNC, uni: dict, raw: list[dict]) -> dict:
    how, drops, members, disagree = Counter(), {}, set(), 0
    seen = set()
    for r in raw:
        key = (r.get("kind"), str(r.get("id")), str(r.get("symbol")))
        if key in seen:
            continue
        seen.add(key)
        s, h = hg.resolve(r.get("kind"), r.get("id"), r.get("symbol"))
        how[h] += 1
        if s:
            members.add(s)
            if r.get("kind") and h.endswith(" id") and isinstance(r.get("symbol"), str):
                s2, _ = hg.symbol(r["symbol"])
                if s2 and s2 != s:
                    disagree += 1
        else:
            label = r.get("symbol") if isinstance(r.get("symbol"), str) else repr(r.get("symbol"))
            if r.get("id"):
                label = f"{label} [{r.get('id')}]"
            drops[label] = h
    # a raw entry dropped under one id but resolved under another spelling is not a gene drop; keep all drops listed
    mem = sorted(members)
    per = {}
    for c in CLASSES:
        # register v6 R5: the members are all columns mapped to S's HGNC genes; the < 5 / > 1,000 rules count columns
        cols = sorted(col for m in mem for col in uni[c].get(m, []))
        n_in = len({m for m in mem if m in uni[c]})
        per[c] = {"n_in_universe": n_in, "n_columns": len(cols), "columns": cols,
                  "outcome": ("not testable (< 5 columns in the class universe)" if len(cols) < MIN_SET else
                              "testable; > 1,000 columns (recorded)" if len(cols) > BIG_SET else "testable")}
    return {"n_raw_unique": len(seen), "n_hgnc": len(mem), "members_hgnc": mem,
            "mapping": dict(sorted(how.items())), "n_id_symbol_disagreements": disagree,
            "n_drops": len(drops), "drops": [{"raw": k, "reason": v} for k, v in sorted(drops.items())],
            "universe": per}


TSV_READ_COLS = ("row", "cell_id", "target_key", "set_S", "analysis_class", "n_cells")  # every TSV column this script reads
ROWREF_KEYS = ("cells", "cells_detail")  # the parts of a per-set JSON that reference TSV rows


def _content_sha(body: dict) -> str:
    """sha256 of a set's record without its TSV row references (definition, source, rule, labels, members, universe ...)."""
    return hashlib.sha256(json.dumps({k: v for k, v in body.items() if k not in ROWREF_KEYS}, sort_keys=True,
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def _members_sha(body: dict) -> str:
    return hashlib.sha256("\n".join(body.get("members_hgnc", [])).encode("utf-8")).hexdigest()


def _cell_ids(cells: list[str]) -> list[str]:
    """cell ids of a set, v4's stand-ins normalised: 'PRE-DG-01 (PRE-DG)' -> PRE-DG-01; v4's unit row 'PRE-DG' dropped."""
    return sorted({c.split(" (")[0] for c in cells} - {"PRE-DG"})


def check_invariance(manifest_sets: list[dict], bodies: dict, rest_ids: set, allow: bool) -> str:
    """Register v5 (TSV rebuilt, PRE-DG split into PRE-DG-01 ... 06): re-pointing the S-build at a rebuilt TSV may move
    only its TSV row references (per-set 'cells' / 'cells_detail', the manifest's cell lists and rows). Every set's
    membership (members_hgnc) and its content without row references must equal the S-build on disk, the set list and
    statuses too; the cell lists may differ only by v4's PRE-DG unit. Runs before anything is written; stops on a
    difference unless --allow-set-changes is given. Returns a one-line summary (counts only)."""
    old_man_p = OUT / "MANIFEST.json"
    if not old_man_p.exists():
        return "no previous S-build on disk (first build): not checked"
    old = json.loads(old_man_p.read_text(encoding="utf-8"))
    old_sets = {e["set_id"]: e for e in old["sets"]}
    new_sets = {e["set_id"]: e for e in manifest_sets}
    errs = []
    if sorted(old_sets) != sorted(new_sets):
        errs.append("set ids differ: %s" % sorted(set(old_sets) ^ set(new_sets)))
    n_members = n_content = n_file_same = n_file_moved = 0
    for sid in sorted(set(old_sets) & set(new_sets)):
        o, n = old_sets[sid], new_sets[sid]
        if (o["status"], o.get("reason"), o.get("sizes"), o.get("json")) != (n["status"], n.get("reason"), n.get("sizes"), n.get("json")):
            errs.append(f"{sid}: status / reason / sizes / file differ")
        if _cell_ids(o["cells"]) != _cell_ids(n["cells"]):
            errs.append(f"{sid}: cells differ beyond v4's PRE-DG unit")
        if not n.get("json"):
            continue
        if not o.get("json"):
            errs.append(f"{sid}: a per-set JSON now, none before")
            continue
        ob = json.loads((OUT / o["json"]).read_text(encoding="utf-8"))
        if hashlib.sha256((OUT / o["json"]).read_bytes()).hexdigest() != o["sha256"]:
            errs.append(f"{sid}: the file on disk differs from the previous manifest")
        nb = bodies[sid]
        if _members_sha(ob) != _members_sha(nb):
            errs.append(f"{sid}: membership differs")
        else:
            n_members += 1
        if _content_sha(ob) != _content_sha(nb):
            errs.append(f"{sid}: content without row references differs")
        else:
            n_content += 1
        txt = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
        if hashlib.sha256(txt.encode("utf-8")).hexdigest() == o["sha256"]:
            n_file_same += 1
        else:
            n_file_moved += 1
    if sorted(old.get("rows_without_a_set_now", {})) != sorted(rest_ids):
        errs.append("rows without a set differ")
    summary = (f"{len(new_sets)} sets (ids, statuses, sizes and cell ids equal: {'yes' if not errs else 'no'}); "
               f"{n_members} per-set JSONs with identical membership (members_hgnc) and {n_content} with "
               f"identical content without row references, of {sum(1 for e in manifest_sets if e.get('json'))}; file bytes "
               f"unchanged {n_file_same}, changed (row references) {n_file_moved}")
    if errs:
        if not allow:
            raise AssertionError("S-build invariance failed (nothing written): " + "; ".join(errs[:20]))
        summary += "; DIFFERENCES ALLOWED by --allow-set-changes: " + "; ".join(errs[:20])
    return summary


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    em = json.loads(pinned("extract_manifest").read_text(encoding="utf-8"))
    for k, v in em["extracts"].items():
        assert sha256(Path(v["path"])) == v["sha256"], f"extract {k} changed"
    hg = HGNC()
    uni, umeta = load_universes(hg)
    src = Sources()
    with open(TSV, encoding="utf-8", newline="") as f:
        lines = [l for l in f if not l.startswith("#")]
    rows = list(csv.DictReader(lines, delimiter="\t"))
    by_id = {r["cell_id"]: r for r in rows}
    assert len(by_id) == len(rows)
    assert [int(r["row"]) for r in rows] == list(range(1, len(rows) + 1)), "TSV row numbers not 1 ... n"
    tsv_view_sha = hashlib.sha256("\n".join("\t".join(r[c] for c in TSV_READ_COLS) for r in rows)
                                  .encode("utf-8")).hexdigest()

    sets: dict[str, dict] = {}          # set_id -> record (built / S undefined / gated / not built)
    cell_set: dict[str, str] = {}       # cell id -> set_id

    def assign(set_id: str, cells: list[str]):
        for c in cells:
            assert c in by_id, f"cell {c} not in TSV"
            family = by_id[c]["n_cells"] not in ("1", "")
            assert c not in cell_set or cell_set[c] == set_id or family,                 f"cell {c} assigned twice ({cell_set.get(c)}, {set_id})"
            cell_set[c] = set_id if c not in cell_set or cell_set[c] == set_id else cell_set[c] + "|" + set_id
        sets[set_id].setdefault("cells", [])
        sets[set_id]["cells"] = sorted(set(sets[set_id]["cells"]) | set(cells), key=lambda c: int(by_id[c]["row"]))

    def cells_where(target: str, pat: str, flags=0) -> list[str]:
        return [r["cell_id"] for r in rows if r["target_key"] == target and re.search(pat, r["set_S"], flags)]

    def add_built(set_id, cells, raw, definition, source, rule, labels=(), paper_size=None, extra=None,
                  status="built", source1=False):
        labels = list(labels)
        if not source1 and "S re-derived" not in labels:
            labels.insert(0, "S re-derived")  # §1.6: sources 2 and 3 are labelled
        rec = {"set_id": set_id, "status": status, "definition": definition, "source": source, "rule": rule,
               "labels": labels, "paper_size": paper_size}
        rec.update(build_set(hg, uni, raw))
        if extra:
            rec.update(extra)
        sets[set_id] = rec
        assign(set_id, cells)

    def add_status(set_id, cells, status, definition, reason, extra=None):
        rec = {"set_id": set_id, "status": status, "definition": definition, "reason": reason}
        if extra:
            rec.update(extra)
        sets[set_id] = rec
        assign(set_id, cells)

    names: dict[str, dict] = {}  # register v6 R1: cell id -> the name rule's record (NAME_MATCHES.json)

    def record_match(cell: str, rec: dict, release: str, what: str, printed: str | None = None):
        assert cell in by_id, cell
        assert cell not in names, f"{cell}: two name-rule records"
        names[cell] = {"cell": cell, "row": int(by_id[cell]["row"]), "target_key": by_id[cell]["target_key"],
                       "mapping": what, "release": release, "printed": printed if printed is not None else rec["query"],
                       "query": rec["query"], "tier": rec["tier"], "id": rec["id"], "name": rec["name"],
                       "label": rec["label"], "tier_hits": {k: len(v) for k, v in rec["tiers"].items()},
                       "summary": NM.label_short(rec)}

    # ======================= Segura (target 1, ungated): Table S4, GO 2024-01-17 terms ∩ S4
    go24a = GO("2024-01-17")
    s4_raw = [{"kind": None, "id": None, "symbol": l.strip()}
              for l in open(pinned("segura_s4"), encoding="utf-8") if l.strip()]
    assert len(s4_raw) == 1046
    seg_src = {"source_id": "segura2025_tableS4", "files": fileref("segura_s4"), "url": URL["segura2025"],
               "release": "Table S4 (MOESM2 pp. 4-36), source 1 (the paper's own list)"}
    add_built("segura_s4", ["SEG-C1", "SEG-C2"], s4_raw, "Segura 2025 Table S4 (1,046 symbols)", seg_src,
              "§1.6 source 1; HGNC rule", paper_size=1046, source1=True)
    s4_set = set(sets["segura_s4"]["members_hgnc"])
    go_src24a = {"source_id": "go_2024-01-17", "files": fileref("go_2024-01-17_obo", "go_2024-01-17_gaf"),
                 "url": URL["go"].replace("<release>", "2024-01-17"), "release": go24a.data_version}
    GO_RULE = ("annotations to the term or any descendant over is_a and part_of, all evidence codes except ND, "
               "NOT-qualified annotations excluded (§1.6)")

    def go_set(go: GO, term: str, ns: str | None):
        gid, rec = go.resolve(term, ns)  # register v6 R1: the name rule
        if gid is None:
            return None, rec, None
        raw, n_desc = go.members(gid)
        return raw, rec, {"go_id": gid, "go_name": go.terms[gid]["name"], "name_match": rec["label"],
                          "n_terms_with_descendants": n_desc}

    def go_intersect_s4(raw):
        b = build_set(hg, uni, raw)
        keep = [m for m in b["members_hgnc"] if m in s4_set]
        return [{"kind": None, "id": None, "symbol": m} for m in keep], b["n_hgnc"]

    s7 = read_tsv(pinned("x_segura_s7"))
    assert len(s7) == 78
    s7_out = []
    others = [r for r in s7 if r["named"] == "other"]
    assert len(others) == 71
    for r in s7:
        term = r["term"]
        raw, how, gi = go_set(go24a, term, "biological_process")
        ent = {"printed_order": int(r["printed_order"]), "printed_row": int(r["printed_row"]), "term": term,
               "named": r["named"]}
        if r["named"] == "other":
            k = others.index(r) + 1
            ent["cell_id"] = f"SEG-C3-D{k:02d}"
        else:
            m = [c for c in cells_where("segura2024symptommapping", rf"GO BP '{re.escape(term)}' at GO release")]
            assert len(m) == 1, (term, m)
            ent["cell_id"] = m[0]
        record_match(ent["cell_id"], how, "GO 2024-01-17 (biological_process)", "GO (Segura Table S7 term)")
        sid = f"segura_go_{gi['go_id'].replace(':', '')}" if gi else f"segura_s7_{ent['printed_order']:02d}_unresolved"
        if gi:
            inter, n_term = go_intersect_s4(raw)
            ent.update({"go_id": gi["go_id"], "go_name": gi["go_name"], "resolved_by": how["label"]})
            add_built(sid, [ent["cell_id"]], inter,
                      f"GO BP '{term}' ({gi['go_id']}) at GO release 2024-01-17, intersected with Table S4",
                      {**go_src24a, "also": seg_src}, GO_RULE + "; S = GO term ∩ Table S4 (register §2.1)",
                      extra={"go": gi, "n_hgnc_term_before_intersection": n_term}, source1=False)
        else:
            ent.update({"go_id": None, "resolved_by": "unresolved: " + NM.label_short(how)})
            add_status(sid, [ent["cell_id"]], "not auditable (S undefined)", f"Table S7 term '{term}'",
                       f"no GO BP term at release 2024-01-17 by the name rule ({NM.label_short(how)})")
        ent["set_id"] = sid
        s7_out.append(ent)

    # ======================= Patel (target 2; claims under G2; external set: Shin 2018 Table S1)
    shin = read_tsv(pinned("x_shin"))
    panels = defaultdict(list)
    for r in shin:
        panels[r["cell_type"]].append({"kind": None, "id": None, "symbol": r["gene_symbol"]})
    for r in rows:
        if r["target_key"] != "patel2021virtual":
            continue
        m = re.search(r"Shin 2018 Table S1 '([^']+)' panel", r["set_S"])
        if not m:
            continue
        p = m.group(1)
        sid = "shin2018_" + re.sub(r"\W+", "_", p.lower()).strip("_")
        size = int(re.search(r"panel(?: \([^)]*\))?: (\d+)", r["set_S"]).group(1))
        if sid not in sets:
            assert len(panels[p]) == size, (p, len(panels[p]), size)
            add_built(sid, [r["cell_id"]], panels[p], f"Shin 2018 (Cereb Cortex 28:3267) Table S1 '{p}' panel",
                      {"source_id": "shin2018", "files": fileref("x_shin"), "url": URL["shin2018"],
                       "extract_of": str(SRC / "shin2018" / "cercor_28_9_3267_s1.zip")},
                      "§1.6 source 2 (primary publication the paper cites); HGNC rule", labels=["S re-derived"],
                      paper_size=size)
        else:
            assign(sid, [r["cell_id"]])

    # ======================= GO BP sets of Romero-Garcia: the Enrichr GO_Biological_Process library the paper used
    # (register v6 R12, orchestrator under the operator's standing delegation, decided after the v5 outcome was seen): the
    # paper names Enrichr (version unstated); of the Enrichr GO BP libraries up to and just after its submission
    # (2017-10-24), the release it used is the one that names every GO BP term the paper prints (register 1.6)
    rg_q = []
    for r in rows:
        m = re.search(r"GO BP '([^']+)' \(Enrichr GO_Biological_Process_2015", r["set_S"])
        if m and r["target_key"] == "romerogarcia2019synaptic":
            rg_q.append((r["cell_id"], m.group(1)))
    assert sorted(c for c, _ in rg_q) == ["RG-02", "RG-V03", "RG-V04", "RG-V05"], rg_q
    printed = sorted({q for _, q in rg_q})
    ident = {}
    for yr in ("2013", "2015", "2017", "2017b", "2018"):
        terms_y, _ = src.enrichr(f"enrichr_gobp_{yr}", go=True)
        ident[f"GO_Biological_Process_{yr}"] = {
            q: {"tier": rr["tier"], "id": rr["id"], "label": rr["label"]} for q in printed for rr in [NM.match(q, terms_y)]}
    naming_all = [lib for lib, d in ident.items() if all(v["id"] for v in d.values())]
    assert naming_all == ["GO_Biological_Process_2015"], naming_all
    e15, e15mem = src.enrichr("enrichr_gobp_2015", go=True)
    e15_src = {"source_id": "enrichr_2026-09-26", "files": fileref("enrichr_gobp_2015"), "url": URL["enrichr"],
               "release": "Enrichr GO_Biological_Process_2015 (served by name 2026-09-26)",
               "why_this_release": ("register 1.6 source 3 at the release the paper used (R12): the paper names Enrichr, "
                                    "version unstated; of the Enrichr GO BP libraries 2013, 2015, 2017, 2017b and 2018, "
                                    "only GO_Biological_Process_2015 names every GO BP term the paper prints ('Synaptic "
                                    "Transmission', 'Membrane depolarization') under the name rule (register 1.1 / 1.6)"),
               "release_identification": ident,
               "also_checked": fileref("enrichr_gobp_2013", "enrichr_gobp_2017", "enrichr_gobp_2017b", "enrichr_gobp_2018")}
    for cid, q in rg_q:
        rr = NM.match(q, e15)
        record_match(cid, rr, "Enrichr GO_Biological_Process_2015", "GO BP (Enrichr library term)")
        assert rr["id"], (cid, q)
        sid = "enrichr_gobp2015_" + rr["id"].replace(":", "")
        if sid in sets:
            assign(sid, [cid])
            continue
        add_built(sid, [cid], e15mem[rr["id"]], f"Enrichr GO_Biological_Process_2015 term '{rr['name']} ({rr['id']})'",
                  e15_src, "the library's gene list for the term as served (Enrichr's own set; the 1.6 GO annotation rule "
                  "does not apply to a library set); symbol -> HGNC (approved, previous, alias)", ["S re-derived"],
                  extra={"enrichr_term": {"id": rr["id"], "name": rr["name"], "library": "GO_Biological_Process_2015"}})

    # ======================= Mamat GO terms (Metascape, version unstated; received 2024-08-14 -> 2024-06-17)
    go24b = GO("2024-06-17")
    go_src24b = {"source_id": "go_2024-06-17", "files": fileref("go_2024-06-17_obo", "go_2024-06-17_gaf"),
                 "url": URL["go"].replace("<release>", "2024-06-17"), "release": go24b.data_version,
                 "why_this_release": "§1.6 source 3: the release in force at the paper's submission (Mol Autism, "
                                     "received 2024-08-14; the latest GO archive release on or before it)"}
    for r in rows:
        if r["target_key"] != "mamat2025molecular":
            continue
        m = re.match(r"GO (BP|CC|MF) '([^']+)' \(the paper's words; name rule", r["set_S"])
        if not m:
            continue
        ont, term = m.groups()
        raw, how, gi = go_set(go24b, term, GO_NS[ont])
        record_match(r["cell_id"], how, "GO 2024-06-17 (%s)" % GO_NS[ont], "GO %s (Mamat text)" % ont)
        sid = f"mamat_go2024-06-17_{gi['go_id'].replace(':', '') if gi else re.sub(r'\W+', '_', term)}"
        if gi:
            add_built(sid, [r["cell_id"]], raw, f"GO {ont} '{term}' at GO release 2024-06-17 ({gi['go_id']} "
                      f"{gi['go_name']})", go_src24b, GO_RULE, labels=["S re-derived"], extra={"go": gi})
        else:
            add_status(sid, [r["cell_id"]], "not auditable (S undefined)", f"GO {ont} '{term}'", NM.label_short(how))

    # ======================= Parikshak 2016 (DE lists; cortex WGCNA modules)
    p16 = src.parikshak2016()
    p16_src = {"source_id": "parikshak2016", "files": fileref("parikshak2016"), "url": URL["parikshak2016"],
               "release": "Supplementary Table 2, sheet TableS2a (cortex analysis)"}
    add_built("parikshak2016_asd_dysregulated", ["RG-05"], p16["up"] + p16["down"],
              "Parikshak 2016 ASD vs CTL cortex, FDR-adjusted P < .05 (up or down)", p16_src,
              "TableS2a 'FDR-adjusted P value, ASD vs CTL' < .05, any sign; §1.6 source 2", ["S re-derived"], 1143)
    add_built("parikshak2016_asd_down", ["RG-06", "RG-V10", "RG-V11"], p16["down"],
              "Parikshak 2016 ASD-downregulated (FDR < .05, log2FC < 0)", p16_src,
              "TableS2a FDR < .05 and 'log2(FC) ASD vs CTL' < 0; §1.6 source 2", ["S re-derived"], 558)
    add_built("parikshak2016_asd_up", ["RG-N01"], p16["up"], "Parikshak 2016 ASD-upregulated (FDR < .05, log2FC > 0)",
              p16_src, "TableS2a FDR < .05 and log2FC > 0; §1.6 source 2", ["S re-derived"], 584)
    mod_cells = defaultdict(list)
    for r in rows:
        m = (re.search(r"Parikshak 2016 \(Nature 540\) module M(\d+)", r["set_S"]) or
             re.search(r"adult module M(\d+)(?: \(upregulated\))?,? \(?Parikshak 2016", r["set_S"]) or
             re.search(r"^as RG-0\d: adult module M(\d+) \(Parikshak 2016\)", r["set_S"]))
        if m and r["target_key"] in ("romerogarcia2019synaptic", "leyhausen2024intrinsic", "seelemeyer2025decomposing"):
            mod_cells[int(m.group(1))].append(r["cell_id"])
    for r in rows:  # RG-N09 / N10 are phrased "adult module M19 (upregulated), Parikshak 2016" or "adult module M19"
        if r["target_key"] == "romerogarcia2019synaptic" and r["cell_id"] in ("RG-N09", "RG-N10"):
            mm = re.search(r"adult module M(\d+)", r["set_S"])
            if r["cell_id"] not in mod_cells[int(mm.group(1))]:
                mod_cells[int(mm.group(1))].append(r["cell_id"])
    for mno, cells in sorted(mod_cells.items()):
        add_built(f"parikshak2016_ctx_M{mno}", cells, p16["mod"][mno],
                  f"Parikshak 2016 cortex WGCNA module M{mno} (all genes assigned to it)", p16_src,
                  "TableS2a 'WGCNA Module Label' == %d (register §1.6 pinned: module assignments)" % mno)

    # ======================= Parikshak 2013 fetal modules
    p13 = src.parikshak2013()
    for mod, cells in (("M13", ["RG-10", "RG-V17", "RG-V20"]), ("M16", ["RG-11", "RG-V18", "RG-V21"]),
                       ("M17", ["RG-12", "RG-V19", "RG-V22"]), ("M2", ["RG-13"]), ("M3", ["RG-14"])):
        for c in cells:
            assert f"Mdev{mod[1:]}" in by_id[c]["set_S"], (c, mod)
        add_built(f"parikshak2013_{mod}", cells, p13[mod], f"Parikshak 2013 (Cell 155) fetal module {mod} (Mdev{mod[1:]})",
                  {"source_id": "parikshak2013", "files": fileref("parikshak2013"), "url": URL["parikshak2013"],
                   "release": "Table S1A 'Module Label'"}, "Table S1A 'Module Label' == %s; §1.6 source 2" % mod,
                  ["S re-derived"])

    # ======================= Sanders 2015 (65 genes)
    add_built("sanders2015_tada65", ["RG-N02"], src.sanders(), "Sanders 2015 (Neuron 87) 65 TADA genes (FDR <= .1)",
              {"source_id": "sanders2015", "files": fileref("sanders2015"), "url": URL["sanders2015"],
               "release": "TADA_Scores sheet, 'tadaFdrAscSscExomeSscAgpSmallDel' <= 0.1"},
              "§1.6 source 2; the 65 = combined TADA q <= 0.1 (the sheet's '65genes' flag column also marks 4 genes "
              "above 0.1 and is not used)", ["S re-derived"], 65)

    # ======================= Gandal 2018 (Science 362) up / down
    g = src.gandal()
    g_src = {"source_id": "gandal2018_science362", "files": fileref("gandal2018"), "url": URL["gandal2018"],
             "release": "Table S1 sheet DGE (gene-level)"}
    down_cells = [r["cell_id"] for r in rows if re.search(r"Gandal 2018", r["set_S"]) and
                  re.search(r"log2FC < 0", r["set_S"]) and r["target_key"] not in ("berto2022connectivity",)
                  and r["cell_id"] != "PRE-DG"] + ["PARK-C5"]
    assert "Gandal 2018 ASD-down" in by_id["PARK-C5"]["set_S"]
    up_cells = [r["cell_id"] for r in rows if re.search(r"Gandal 2018", r["set_S"]) and
                re.search(r"log2FC > 0", r["set_S"]) and r["target_key"] not in ("berto2022connectivity",)
                and r["cell_id"] != "PRE-DG"]
    add_built("gandal2018_asd_down", down_cells, g["down"], "Gandal 2018 ASD-downregulated genes", g_src,
              "DGE: ASD.fdr < .05 and ASD.log2FC < 0 (§1.6 pinned)", [],
              extra={"paper_sizes": {"Pretzsch K (ASD_downregulatedgenes)": 764}})
    add_built("gandal2018_asd_up", up_cells, g["up"], "Gandal 2018 ASD-upregulated genes", g_src,
              "DGE: ASD.fdr < .05 and ASD.log2FC > 0 (§1.6 pinned)", [],
              extra={"paper_sizes": {"Pretzsch K (ASD_upregulated)": 1111}})

    # ======================= Velmeshev 2019 Data S4 union
    vel, nvel = src.velmeshev()
    vel_cells = [r["cell_id"] for r in rows if "Velmeshev 2019 (Science 364) Data S4" in r["set_S"]]
    add_built("velmeshev2019_asd_degs_union", vel_cells, vel, "Velmeshev 2019 Data S4 ASD_DEGs, union over cell types",
              {"source_id": "velmeshev2019", "files": fileref("x_velmeshev"), "url": URL["velmeshev2019"],
               "extract_of": str(VELMESHEV_XLS) + " (sheet ASD_DEGs only)"},
              f"all {nvel} ASD_DEGs rows (every q < .05), union over cell types (§1.6 pinned)")

    # ======================= KEGG (register v6.1 Q2 / Q3; orchestrator under the operator's standing delegation): the release
    # rules of register 1.6 -- (i) a tool library: that library's release (Vairam / Roy name KEGG_2021_Human; Romero-Garcia's
    # families take the Enrichr vintage of its GO_Biological_Process_2015, KEGG_2015, under G1); (ii) KEGG itself (or a tool
    # whose library release is unobtainable): the obtainable KEGG release closest in date to the retrieval, else submission,
    # date, Enrichr snapshots counting as releases (Leyhausen: retrieved 2021-12-14; Mamat: received 2024-08-14)
    kegg_choice = kegg_release_choice(src)
    # register v6.2 P5: the Romero-Garcia KEGG family rule, its candidates pinned and its plants run on public library names
    k15, _ = src.enrichr("enrichr_kegg_2015", go=False)
    k16, _ = src.enrichr("enrichr_kegg_2016", go=False, suffix=KEGG16_SUFFIX)
    fam_plants = []
    for names_, want, want_per in KEGG_FAMILY_PLANTS:
        got = kegg_family_choice(names_, {"KEGG_2015": k15, "KEGG_2016": k16})
        ok = got["chosen"] == want and {n: v[0] for n, v in got["per_name"].items()} == want_per
        fam_plants.append({"names": names_, "expected": want, "chosen": got["chosen"], "per_name_library":
                           {n: v[0] for n, v in got["per_name"].items()}, "caught": ok})
    assert all(x["caught"] for x in fam_plants), fam_plants
    kegg_choice["romerogarcia2019synaptic_families"] = {
        "rule": KEGG_FAMILY_RULE, "candidates": [
            {"library": "KEGG_2015", "file": fileref("enrichr_kegg_2015")[0], "n_terms": len(k15)},
            {"library": "KEGG_2016", "file": fileref("enrichr_kegg_2016")[0], "n_terms": len(k16),
             "n_terms_read_by_suffix": sum(1 for t in k16 if re.fullmatch(r"hsa\d{5}", t["id"]))}],
        "choice": "made under G1, when the gated tables' pathway names are read (sealed now)",
        "plants": fam_plants}
    assert kegg_choice["leyhausen2024intrinsic"]["chosen"] == "KEGG_2021_Human", kegg_choice["leyhausen2024intrinsic"]
    k21, k21mem = src.enrichr("enrichr_kegg_2021_human", go=False)
    trunc = kegg_truncation_evidence(src, k21, k21mem)  # register v6.2 P4
    assert trunc["in_kegg_2021_human_in_full"] == 0 and trunc["kegg_2021_human_names_with_dash"] == 0, trunc
    assert trunc["closest_rest_pathways_by_symbol_jaccard"][0]["id"] == "hsa05022", trunc
    for r in rows:
        m = re.search(r"KEGG '([^']+)' \(Enrichr KEGG_2021_Human", r["set_S"])
        if not m or r["target_key"] not in ("vairam2026hyperhypo", "leyhausen2024intrinsic"):
            continue
        name, vr = m.group(1), r["target_key"] == "vairam2026hyperhypo"
        rr = NM.match(name, k21)
        record_match(r["cell_id"], rr, "Enrichr KEGG_2021_Human",
                     "KEGG (Vairam / Roy GSEA term)" if vr else "KEGG (Leyhausen Fig. 3B label)")
        if rr["id"] is None:
            assert not vr, (r["cell_id"], name)
            sid = "enrichr_kegg2021_" + re.sub(r"\W+", "_", name.lower()).strip("_") + "_unresolved"
            add_status(sid, [r["cell_id"]], "not auditable (S undefined)", f"KEGG '{name}' (Enrichr KEGG_2021_Human)",
                       "the printed name reaches no pathway of Enrichr KEGG_2021_Human (the obtainable KEGG release closest "
                       "in date to the paper's retrieval, 2021-12-14; register 1.6 KEGG rule (ii), v6.1 Q3) by the name rule: "
                       + NM.label_short(rr) + "; Leyhausen's own list (source 1) lies in no gated carrier (its supplements were "
                       "read before the register), so the conditional form does not apply. Cause (v6.2 P4): Enrichr KEGG_2021_Human "
                       "truncates KEGG names at ' - ' (of the %d KEGG REST names holding ' - ', %d appear in full, %d only as the "
                       "part before ' - '); the pathway was hsa05022 at retrieval (the library's 'Pathways of neurodegeneration' "
                       "entry, %d genes, is closest to hsa05022: symbol Jaccard %.3f)"
                       % (trunc["rest_names_with_dash"], trunc["in_kegg_2021_human_in_full"],
                          trunc["in_kegg_2021_human_only_as_the_part_before_dash"], trunc["entry_n_genes"],
                          trunc["closest_rest_pathways_by_symbol_jaccard"][0]["jaccard"]),
                       extra={"cause_v6_2_P4": trunc})
            continue
        sid = "enrichr_kegg2021_" + re.sub(r"\W+", "_", rr["id"].lower()).strip("_")
        if sid in sets:
            assign(sid, [r["cell_id"]])
            continue
        add_built(sid, [r["cell_id"]], k21mem[rr["id"]], f"Enrichr KEGG_2021_Human '{rr['id']}'",
                  {"source_id": "enrichr_2026-09-26", "files": fileref("enrichr_kegg_2021_human"), "url": URL["enrichr"],
                   "release": ("Enrichr KEGG_2021_Human (served by name 2026-09-26): for Vairam / Roy the library the paper "
                               "names ('KEGG 2021 Human' via gseapy prerank; register 1.6 KEGG rule (i), R12); for Leyhausen "
                               "the obtainable KEGG release closest in date to its retrieval, 2021-12-14 (rule (ii), v6.1 Q3)")},
                  "the library's gene list for the pathway as served; symbol -> HGNC (approved, previous, alias); the "
                  "pathway reached by the name rule (register 1.1 / 1.6; per cell: NAME_MATCHES.json)",
                  ["S re-derived"] + (["deferred target (Vairam / Roy): built, not run"] if vr else ["release substituted"]))

    # ======================= Kang 2011 modules: no membership table published -> S undefined
    kmods = {r["module"]: int(r["size"]) for r in read_tsv(pinned("x_kang_modules"))}
    pinned("kang2011_moesm50")
    kang_cells = defaultdict(list)
    for r in rows:
        m = re.search(r"Kang 2011 \(Nature 478\) module (M\d+) membership table", r["set_S"])
        if m:
            kang_cells[m.group(1)].append(r["cell_id"])
    for mod, cells in sorted(kang_cells.items(), key=lambda x: int(x[0][1:])):
        add_status(f"kang2011_{mod}", cells, "not auditable (S undefined)",
                   f"Kang 2011 (Nature 478) module {mod} membership (register §1.6 pinned: 'module membership table')",
                   "Kang 2011 publishes no module-membership table: Supplementary Table 9 gives each of the 29 modules' "
                   f"colour, size ({mod}: {kmods[mod]} genes), hub genes and DAVID-term gene hits only; the Nature ESM "
                   "(MOESM50 .xls, = the PMC NIHMS321722 tables and the hbatlas.org copy) holds no gene-by-module list. "
                   "R2 examined (register v6): no gated carrier of Leyhausen or Seelemeyer can hold the paper's own "
                   "module list -- their gated objects are NeuroVault images, and their supplements (mmc1.pdf, "
                   "Leyhausen's mmc2.xlsx Key Resources Table) were read before the register and publish no membership "
                   "(register_work drafts, section 1) -- so the conditional form does not apply",
                   extra={"source_checked": fileref("kang2011_moesm50", "x_kang_modules"), "url": URL["kang2011"],
                          "module_size": kmods[mod]})

    # ======================= Polioudakis 2019 clusters
    pol = src.polioudakis()
    for r in rows:
        m = re.search(r"Polioudakis 2019 \(Neuron 103\) cluster-enriched genes table, all rows for cluster (\S+)",
                      r["set_S"])
        if not m:
            continue
        cl = m.group(1)
        sid = f"polioudakis2019_{cl}"
        if sid in sets:
            assign(sid, [r["cell_id"]])
            continue
        assert cl in pol, cl
        add_built(sid, [r["cell_id"]], pol[cl], f"Polioudakis 2019 cluster-enriched genes, cluster {cl}",
                  {"source_id": "polioudakis2019", "files": fileref("polioudakis2019"), "url": URL["polioudakis2019"],
                   "release": "Table S4 sheet 'Cluster enriched genes'"}, "all rows of the cluster (§1.6 pinned)")

    # ======================= MSigDB C5 GOBP 2023.1.Hs (Pretzsch)
    ms = src.msigdb()
    mscand = [{"id": k, "name": k, "synonyms": [], "live": True} for k in sorted(ms)]
    for r in rows:
        m = re.search(r"MSigDB C5 GOBP 2023\.1\.Hs '(GOBP_[A-Z0-9_]+)' \(K = (\d+) in the paper", r["set_S"])
        if not m:
            continue
        q, k = m.group(1), int(m.group(2))
        rr = NM.match(q, mscand)
        record_match(r["cell_id"], rr, "MSigDB 2023.1.Hs C5 GO:BP", "MSigDB (Pretzsch eTable 5 name)")
        nm = rr["id"] or q
        sid = "msigdb2023_" + nm
        if sid in sets:
            assign(sid, [r["cell_id"]])
            continue
        if rr["id"] is None:
            add_status(sid, [r["cell_id"]], "not auditable (S undefined)", q, NM.label_short(rr))
            continue
        add_built(sid, [r["cell_id"]], ms[nm], f"MSigDB C5 GOBP 2023.1.Hs {nm}",
                  {"source_id": "msigdb_2023.1.Hs", "files": fileref("msigdb_c5_gobp_2023.1"),
                   "url": URL["msigdb_c5_gobp_2023.1"], "release": "2023.1.Hs"},
                  "the GMT row with this exact name (§1.6 pinned)", paper_size=k,
                  extra={"n_listed_in_gmt": len(ms[nm])})

    # ======================= WebGestalt categories (Rasero; the ∩ brain-specific list is under gate G1)
    for r in rows:
        # v4 TSV: "(WebGestalt 2022 GMT; ..."; v5 TSV: "(WebGestalt GMT, ... 'release substituted' ..." (same categories)
        m = re.search(r"(Reactome|GO BP) '([^']+)' \(WebGestalt (?:2022 )?GMT", r["set_S"])
        if not m or r["target_key"] != "rasero2023neurogenetics":
            continue
        db, name = m.groups()
        wcand, mem = src.webgestalt("reactome" if db == "Reactome" else "gobp")
        rr = NM.match(name, wcand)
        record_match(r["cell_id"], rr, "WebGestalt %s (server as fetched 2026-09-26)" % db,
                     "%s (Rasero Fig. 4A label)" % db)
        hit = [rr["id"]] if rr["id"] else []
        sid = f"webgestalt_{'reactome' if db == 'Reactome' else 'gobp'}_" + (hit[0].replace(':', '') if len(hit) == 1
                                                                             else re.sub(r"\W+", "_", name.lower()))
        if sid in sets:
            assign(sid, [r["cell_id"]])
            continue
        if len(hit) != 1:
            add_status(sid, [r["cell_id"]], "not auditable (S undefined)", f"WebGestalt {db} '{name}'",
                       NM.label_short(rr))
            continue
        add_built(sid, [r["cell_id"]], mem[hit[0]], f"WebGestalt {db} category '{name}' ({hit[0]})",
                  {"source_id": "webgestalt_current", "url": URL["webgestalt"],
                   "files": fileref("wg_reactome_gmt", "wg_reactome_des") if db == "Reactome" else
                   fileref("wg_gobp_gmt", "wg_gobp_des"),
                   "release": "WebGestalt server as fetched 2026-09-26 (no version string served; the 2022 release "
                              "is not obtainable: 2022.webgestalt.org does not resolve)"},
                  "the category reached by the name rule (register 1.1 / 1.6; per cell: NAME_MATCHES.json); Entrez id "
                  "-> HGNC",
                  ["S re-derived", "release substituted"],
                  status="built (category only; S = this category ∩ the paper's 2,587 HPA brain-specific genes "
                         "(repo data/brain-specific_genes.txt) is completed under gate G1)")

    # ======================= HPA TissueEnrich 'cerebral cortex' (Mamat)
    te_all = src.tissueenrich()
    te = te_all["Protein-Atlas"]["tissueSpecificGenes"]
    te_sym = dict(zip(te_all["humanGeneMapping"]["Gene"], te_all["humanGeneMapping"]["Gene.name"]))
    groups = ("Tissue-Enriched", "Tissue-Enhanced", "Group-Enriched")
    sel = te[(te["Tissue"] == "Cerebral.Cortex") & te["Group"].isin(groups)]
    add_built("tissueenrich_hpa_cerebral_cortex", ["MAMAT-E-Tissue-URG", "MAMAT-E-Tissue-DRG"],
              [{"kind": "ensembl", "id": gname, "symbol": te_sym.get(gname)} for gname in sel["Gene"]],
              "HPA TissueEnrich tissue-specific genes, 'Cerebral Cortex' (Tissue-Enriched, Tissue-Enhanced, "
              "Group-Enriched: the package default)",
              {"source_id": "tissueenrich_bioc3.19", "files": fileref("tissueenrich_1.24.1"),
               "url": URL["tissueenrich_1.24.1"],
               "release": "TissueEnrich 1.24.1 (Bioconductor 3.19, released 2024-05; in force at Mamat's submission "
                          "2024-08-14); dataset 'Protein-Atlas' of inst/extdata/combine-expression.rda"},
              "dataset$`Protein-Atlas`$tissueSpecificGenes, Tissue == 'Cerebral.Cortex', Group in the default "
              "tissueSpecificGeneType = 1 groups; Ensembl id -> HGNC (symbol fallback: the package's humanGeneMapping)",
              ["S re-derived"],
              extra={"group_counts": dict(sorted(Counter(sel["Group"]).items()))})

    # ======================= pSI.data CSEA / SEA tables
    ph = src.psi_human()
    dev = ph["developmental.periods"]["psi.out"]
    ya = ph["young.adulthood"]["psi.out"]
    psi_src = {"source_id": "psi_data_1.0", "files": fileref("psi_data_1.0"), "url": URL["psi_data_1.0"],
               "release": "pSI.data 1.0 (2013-12-03; the Dougherty laboratory's distribution; not on CRAN; the "
                          "register's '1.1' is the pSI package version, pSI.data exists as 1.0 only)"}

    def toks(s: str) -> set[str]:
        return {t for t in re.split(r"[^a-z0-9]+", s.lower()) if t}

    def psi_col(df, query: str) -> tuple[str | None, list[str]]:
        q = toks(query)
        hit = [c for c in df.columns if q <= toks(c)]
        return (hit[0] if len(hit) == 1 else None), hit

    def psi_members(df, col):
        v = df[col]
        return [{"kind": None, "id": None, "symbol": g} for g in v.index[(v < 0.05).to_numpy()]]

    for r in rows:
        m = re.search(r"human BrainSpan developmental table .*?region '([^']+)' and period '([^']+)'", r["set_S"])
        if not m:
            continue
        reg, per = m.groups()
        col, hits = psi_col(dev, f"{reg} {per}")
        sid = f"psi_dev_{reg.lower()}_{re.sub(r'[^a-z0-9]+', '_', per.lower()).strip('_')}"
        if sid in sets:
            assign(sid, [r["cell_id"]])
            continue
        if col is None:
            add_status(sid, [r["cell_id"]], "not auditable (S undefined)", f"pSI dev {reg} x {per}",
                       f"{len(hits)} matching columns ({hits})")
            continue
        add_built(sid, [r["cell_id"]], psi_members(dev, col), f"pSI.data human developmental.periods column "
                  f"'{col}', pSI < .05", psi_src, "column by case-insensitive token match of region and period "
                  "(query tokens ⊆ column tokens, exactly one column: an S-build reading, register 1.6 R3); genes "
                  "with pSI < .05 (§1.6 pinned)",
                  extra={"psi_column": col, "table": "human$developmental.periods$psi.out"})
    for r in rows:
        m = re.search(r"human brain-region table.*?, at pSI < \.05: the column found by case-insensitive token match "
                      r"of region '([^']+)'", r["set_S"])
        if not m:
            continue
        reg = m.group(1)
        col, hits = psi_col(ya, reg)
        sid = f"psi_region_{reg.lower()}"
        if col is None:
            add_status(sid, [r["cell_id"]], "not auditable (S undefined)", f"pSI region {reg}", f"{len(hits)} columns")
            continue
        add_built(sid, [r["cell_id"]], psi_members(ya, col), f"pSI.data human young.adulthood (brain-region) column "
                  f"'{col}', pSI < .05", psi_src, "column by case-insensitive token match of the region (query tokens ⊆ "
                  "column tokens, exactly one column: an S-build reading, register 1.6 R3); 'the human brain-region "
                  "table' read as pSI.data human$young.adulthood (an S-build reading, register 1.6 R3); genes with "
                  "pSI < .05 (§1.6 pinned)",
                  extra={"psi_column": col, "table": "human$young.adulthood$psi.out"})
    pm = src.psi_mouse()["psi.out"]
    for r in rows:
        m = re.search(r"mouse cell-type table \(TRAP\), at pSI < \.05: the column found by case-insensitive token "
                      r"match of cell type '([^']+)'", r["set_S"])
        if not m:
            continue
        ct = m.group(1)
        col, hits = psi_col(pm, ct)
        near = sorted(c for c in pm.columns if toks(c) & toks(ct))
        sid = "psi_mouse_" + re.sub(r"[^a-z0-9]+", "_", ct.lower()).strip("_")
        # register v6 R3 (orchestrator under the operator's standing delegation; decided after the v5 outcome was seen)
        add_status(sid, [r["cell_id"]], "not auditable (definition not applicable)",
                   f"pSI.data mouse TRAP cell type '{ct}'",
                   "v4 pinned a mouse table without an orthology rule (register v6 R3; the table holds mouse symbols and "
                   "section 1.6 pins no mouse -> human orthology mapping). Recorded, not "
                   f"used: the token rule matches {len(hits)} of the 35 mouse columns (column names are abbreviations, "
                   f"e.g. 'Ctx.pnoc', 'Cpu.Chat'; columns sharing any token: {near})",
                   extra={"source_checked": fileref("psi_data_1.0"), "n_mouse_columns": int(pm.shape[1])})

    # ======================= Lake 2018 (Park C6 family): 13 excitatory subtypes, 'All Clusters' block
    lk = src.lake()
    ex = sorted([c for c in lk if re.fullmatch(r"Ex\d+[a-e]?", c)], key=lambda c: (int(re.search(r"\d+", c).group()), c))
    assert len(ex) == 13, ex
    for c in ex:
        add_built(f"lake2018_{c}", ["PARK-C6"], lk[c], f"Lake 2018 Table S3 'All Clusters' block, cluster {c}",
                  {"source_id": "lake2018", "files": fileref("lake2018"), "url": URL["lake2018"],
                   "release": "Supplementary Table S3, block 'All Clusters' (each cluster vs all others)"},
                  "all rows of the cluster in the 'All Clusters' block (the register names 'the marker table'; the "
                  "block choice is recorded as an issue); §1.6 source 2", ["S re-derived"],
                  extra={"family": "PARK-C6", "family_cell_index": ex.index(c) + 1})

    # ======================= Moreau locus genes (source 1)
    for key, sid, cells in (("moreau_16p", "moreau_16p11.2", ["MOR-C1", "MOR-C3", "MOR-T1", "MOR-R1", "MOR-R4"]),
                            ("moreau_22q", "moreau_22q11.2", ["MOR-C2", "MOR-T2", "MOR-R2", "MOR-R3"])):
        raw = [{"kind": None, "id": None, "symbol": l.strip()} for l in open(pinned(key), encoding="utf-8")
               if l.strip()]
        add_built(sid, cells, raw, f"Moreau 2020 {sid.split('_')[1]} locus genes (repo data file)",
                  {"source_id": "moreau2020_locus", "files": fileref(key), "url": URL["moreau2020"]},
                  "§1.6 source 1 (the paper's own list)", paper_size={"moreau_16p": 24, "moreau_22q": 37}[key],
                  source1=True,
                  extra={"note": "native class MIST64 (primary parcels: left + midline by the atlas_info hemisphere "
                                 "column of the MIST64 matrix)"})

    # ======================= Liu merged ASD set; Xing SFARI sets
    sf = src.sfari()
    sfc = sfari_release_choice()  # register v6.7 (2) / N2: the uniform archive rule, by the served release label
    assert sfc["liu2026spatiotemporal"]["pin"] == "sfari_cap_20240515204151", sfc["liu2026spatiotemporal"]
    assert sfc["xing2026interpretable"]["pin"] == "sfari_2026-07-12" and sfc["xing2026interpretable"]["state_substituted"], \
        sfc["xing2026interpretable"]
    import datetime as _dt  # v6.8 (C): Xing's date is its first journal submission; the state's lag computed, not typed
    x_lag = (_dt.date.fromisoformat(sfc["xing2026interpretable"]["export"])
             - _dt.date.fromisoformat(SFARI_STATED["xing2026interpretable"]["submission"])).days
    sf_src = {"source_id": "sfari_gene", "files": fileref("sfari_2026-07-12", "sfari_labels"), "url": URL["sfari_2026-07-12"],
              "release": ("SFARI Gene release 07-12-2026, export 09-25-2026 (fetched 2026-09-25; re-checked 2026-09-26: "
                          "unchanged) -- the release current at Xing's date (its first journal submission, %s; v6.8), in a state "
                          "%d days after it (no archived state)" % (SFARI_STATED["xing2026interpretable"]["submission"], x_lag))}
    liu_sf = _sfari_rows(pinned(sfc["liu2026spatiotemporal"]["pin"]))
    score1 = [{"kind": "ensembl", "id": r["ensembl-id"], "symbol": r["gene-symbol"]} for r in liu_sf if r["gene-score"] == "1"]
    assert len(score1) == 233
    grove = [{"kind": None, "id": None, "symbol": r["gene"]} for r in read_tsv(pinned("x_grove"))]
    sat = src.satterstrom()
    liu_cells = [r["cell_id"] for r in rows if r["set_S"].startswith("merged ASD = Satterstrom 2020 (102)")]
    add_built("liu_merged_asd", liu_cells, sat + grove + score1,
              "Satterstrom 2020 (102) ∪ Grove 2019 MAGMA top 25 ∪ SFARI Gene score 1",
              {"source_id": "liu_components", "files": fileref("satterstrom2020", "x_grove", "sfari_cap_20240515204151",
                                                               "sfari_labels"),
               "url": {"satterstrom2020": URL["satterstrom2020"], "grove2019": URL["grove2019"],
                       "sfari": ("https://web.archive.org/web/20240515204151id_/https://gene.sfari.org/wp-content/themes/sfari-gene/"
                                 "utilities/download-csv.php?api-endpoint=genes")},
               "release": "SFARI Gene release 03-28-2024, export 05-15-2024 (Wayback capture 20240515204151)"},
              "§1.6 SFARI rule, applied by v6.7's uniform archive rule (sfari_releases_v6_7; the served release label read, "
              "N2): %s (release 01-16-2024 has 232); v6 ... v6.6 had used the 2026-07-12 release ('release substituted', "
              "245) for want of an archive" % sfc["liu2026spatiotemporal"]["how"], ["S re-derived"],
              paper_size=None,
              extra={"components": {"satterstrom2020_102": len(sat), "grove2019_magma_top25": len(grove),
                                    "sfari_score1_03-28-2024": len(score1)},
                     "paper_component_sizes": {"satterstrom": 102, "grove_magma": 25, "sfari_score1": 233}})
    for sid, pat, filt, desc in (
            ("sfari_all", r"SFARI Gene, all genes", lambda r: True, "all genes"),
            ("sfari_score1_high_confidence", r"SFARI Gene, high-confidence genes", lambda r: r["gene-score"] == "1",
             "score 1 ('High Confidence')"),
            ("sfari_syndromic", r"SFARI Gene, syndromic genes", lambda r: r["syndromic"] == "1", "syndromic == 1")):
        cells = [r["cell_id"] for r in rows if r["target_key"] == "xing2026interpretable" and re.search(pat, r["set_S"])]
        add_built(sid, cells, [{"kind": "ensembl", "id": r["ensembl-id"], "symbol": r["gene-symbol"]}
                               for r in sf if filt(r)],
                  f"SFARI Gene {desc}", sf_src, "§1.6 SFARI rule, applied by v6.7's uniform archive rule "
                  "(sfari_releases_v6_7; the served release label read, N2): %s -- the release is the one current at the "
                  "date, its state %d days later (v6 ... v6.6: 'release substituted' for want of an archive); categories as "
                  "the release defines them" % (sfc["xing2026interpretable"]["how"], x_lag),
                  ["state substituted"], paper_size=1277 if sid == "sfari_all" else None)

    # ======================= sets not built now: gated carriers, undefined rules, rows not auditable for other reasons
    def mark(sid, cells, status, definition, reason):
        add_status(sid, cells, status, definition, reason)

    # Buch's figure labels (Fig. 5f-h; register v6 R1): Buch's own definition in MOESM3 first (source 1, under G1); the
    # fallback (sources 2-3) is the PANTHER 16.0 GO-slim term the printed label reaches by the name rule. A label that
    # reaches no term has no fallback: R2's conditional form (S from MOESM3 if it defines the set, else S undefined).
    pan = src.panther()
    buch_fallback: dict[str, dict] = {}
    for r in rows:
        if r["target_key"] != "buch2023asdsubgroups":
            continue
        m = re.search(r"Fig\. 5([fgh]) label '([^']+)' \(as printed\)", r["set_S"])
        if not m:
            continue
        printed_lab = m.group(2)
        q = printed_lab.lstrip("*").strip()  # a leading asterisk is a mark (unexplained in the legend), not the name
        rr = NM.match(q, pan)
        record_match(r["cell_id"], rr, "PANTHER 16.0 GO-slim (PANTHERGOslim.obo)", "figure label (Buch Fig. 5%s)"
                     % m.group(1), printed=printed_lab)
        c = r["cell_id"]
        if rr["id"] is None:
            mark(f"uncorroborated_{c}", [c], "not auditable (S undefined)", r["set_S"][:160],
                 UNCORROBORATED + ": the printed label '%s' reaches no name, synonym or normalised name of PANTHER 16.0 GO-slim "
                 "(the release the paper names) under the name rule (register 1.1 / 1.6, R1), so sources 2-3 define no set, and "
                 "the paper prints no size (v5-v6.4: S conditional on MOESM3, R2)" % q)
        else:
            buch_fallback.setdefault(rr["id"], {"name": rr["name"], "cells": []})["cells"].append(c)
    # register v6.1 Q7 as revised by v6.2 P3 (orchestrator under the operator's standing delegation): the fallback of Buch's GO-slim
    # cells is built now (it needs no gated carrier) from PANTHER 16.0's own gene -> GO-slim annotation as served (PTHR16.0_human,
    # the named tool's library: register 1.6 R12 logic), the term being the PANTHER 16.0 GO-slim term the printed label reaches by
    # the name rule. Source 1 (Buch's own list in MOESM3, by the source-1 criterion) is still checked first, under G1. v6.1's GO
    # 2021-11-16 annotation of the same terms is kept only as a descriptor (overlap).
    pthr = src.panther_annotation()
    go21 = GO("2021-11-16")
    pthr_src = {"source_id": "panther_16.0_goslim", "files": fileref("panther_16.0_pthr_human", "panther_16.0_goslim"),
                "url": URL["panther_16.0_pthr_human"],
                "release": "PANTHER 16.0 sequence classification, human (PTHR16.0_human; the release Buch names)",
                "why_this_release": ("register v6.2 P3: Buch ran PANTHER 16.0 GO-slim enrichment; the fallback is that tool's own "
                                     "gene -> GO-slim annotation as served (R12 logic), the terms those of PANTHERGOslim.obo (pinned) "
                                     "the printed labels reach by the name rule"),
                "file_counts": {"n_genes": pthr["n_genes"], "n_genes_with_a_goslim_term": pthr["n_genes_annotated"],
                                "gene_id_kinds": pthr["gene_id_kinds"]}}
    fb_summary = []
    isa_ch, partof_ch = goslim_children(pinned("panther_16.0_goslim"))  # register v6.3 O5

    def rows_of(terms_):
        return {(r["kind"], r["id"], r["symbol"]) for t_ in terms_ for r in pthr["members"].get(t_, [])}
    for gid, info in sorted(buch_fallback.items()):
        raw = pthr["members"].get(gid, [])
        assert raw, (gid, "no gene carries this GO-slim term in PTHR16.0_human")
        col = sorted(pthr["columns"][gid])
        t21 = go21.terms.get(gid)
        raw21, _ = go21.members(gid)
        b21 = build_set(hg, uni, raw21)
        bp = build_set(hg, uni, raw)
        both = len(set(bp["members_hgnc"]) & set(b21["members_hgnc"]))
        union = len(set(bp["members_hgnc"]) | set(b21["members_hgnc"]))
        desc = {"what": "descriptor (v6.2 P3): v6.1's fallback -- the same GO id annotated at GO release 2021-11-16 (GAF + obo, "
                        "section 1.6 GO rule) -- compared with this set by HGNC gene",
                "go_2021-11-16_name": t21["name"] if t21 else None, "n_hgnc_go_2021": b21["n_hgnc"], "n_hgnc_both": both,
                "jaccard": round(both / union, 4) if union else None,
                "columns_go_2021": {c: b21["universe"][c]["n_columns"] for c in CLASSES}}
        served, c_isa = rows_of([gid]), rows_of(_descendants(gid, [isa_ch]))
        c_all = rows_of(_descendants(gid, [isa_ch, partof_ch]))
        b_all = build_set(hg, uni, [{"kind": k, "id": i, "symbol": sy} for k, i, sy in sorted(c_all)])
        closure = {"what": ("descriptor (v6.3 O5): the served annotation against its closures over the GO-slim ontology "
                            "(PANTHERGOslim.obo): genes (PTHR16.0_human rows) listing the term, any is_a descendant, or any is_a / "
                            "part_of descendant"),
                   "n_genes_served": len(served), "n_genes_is_a_closure": len(c_isa), "n_genes_is_a_part_of_closure": len(c_all),
                   "served_equals_is_a_closure": served == c_isa,
                   "part_of_increase_pct": round(100.0 * (len(c_all) - len(served)) / len(served), 2),
                   "n_hgnc_is_a_part_of_closure": b_all["n_hgnc"]}
        sid = "buch_goslim_fallback_" + gid.replace(":", "")
        add_built(sid, info["cells"], raw,
                  f"Buch GO-slim fallback: PANTHER 16.0 GO-slim term {gid} '{pthr['names'][gid]}' (PTHR16.0_human, as served; "
                  f"the term the printed label reaches: '{info['name']}')", pthr_src,
                  "PANTHER 16.0's gene -> GO-slim annotation as served: the genes whose PTHR16.0_human row lists the term (column "
                  + "/".join(col) + "; no propagation added); HGNC id -> HGNC (else Ensembl / Entrez / UniProt id, else the symbol); "
                  "the fallback of Buch's GO-slim cells: used only if MOESM3 (source 1, under G1) holds no list meeting "
                  + SOURCE1_CRITERION,
                  ["S re-derived"], status=BUCH_FALLBACK_STATUS,
                  extra={"panther_goslim": {"go_id": gid, "name_as_served": pthr["names"][gid], "goslim_obo_name": info["name"],
                                            "columns": col},
                         "descriptor_overlap_go_2021-11-16": desc, "descriptor_closure_v6_3_O5": closure})
        fb_summary.append({"set_id": sid, "go_id": gid, "n_hgnc": sets[sid]["n_hgnc"],
                           "V-AAL_columns": sets[sid]["universe"]["V-AAL"]["n_columns"],
                           "outcome_V-AAL": sets[sid]["universe"]["V-AAL"]["outcome"],
                           "n_hgnc_go_2021": b21["n_hgnc"], "jaccard_go_2021": desc["jaccard"],
                           "n_genes_served": closure["n_genes_served"],
                           "served_equals_is_a_closure": closure["served_equals_is_a_closure"],
                           "n_genes_is_a_part_of_closure": closure["n_genes_is_a_part_of_closure"],
                           "part_of_increase_pct": closure["part_of_increase_pct"]})
    # ======================= register v6.6 (B2 / C5; the orchestrator under the operator's standing delegation, 2026-09-27): the
    # comparators of Buch's non-GO sets and Pagani's sets, built now by register 1.6's resolution rule (s_build_v66.py); every Buch
    # Fig. 5c-e cell and every Pagani cell gets its comparator (or 'not auditable (S undefined: comparator not buildable
    # pre-freeze)') here, so the gated loop below no longer marks them 'built under gate G1'
    comparators = V66.build(V66.Ctx(hg=hg, NM=NM, add_built=add_built, add_status=add_status, record_match=record_match,
                                    read_obo=read_obo, obo_candidates=obo_candidates, descendants=_descendants,
                                    sha256=sha256, relpath=relpath, uni=uni))  # v6.8: the universes (asdM12's V-AAL Jaccard)
    gated_g1 = {"pagani2026crossspecies": ("Pagani Supplementary Table 3 (MOESM4_ESM.xlsx): the list it presents as the set's "
                                           "input membership, by " + SOURCE1_CRITERION + "; else register 1.6's sources 2-3 "
                                           "in order (its decoded genes never qualify)"),
                "buch2023asdsubgroups": ("Buch MOESM3.xlsx (Buch's own definitions, source 1, first, by " + SOURCE1_CRITERION
                                         + "); else register 1.6's sources 2-3")}
    for tk, what in gated_g1.items():
        for r in rows:
            if r["target_key"] == tk and r["cell_id"] not in cell_set and not r["set_S"].startswith("none"):
                assert "no defined source" not in r["set_S"], (r["cell_id"], "v6.6 C5: every Buch set names its source")
                if tk == "buch2023asdsubgroups" and "no defined source" in r["set_S"]:
                    mark(f"uncorroborated_{r['cell_id']}", [r["cell_id"]], "not auditable (S undefined)", r["set_S"][:160],
                         UNCORROBORATED + ": the draft names no source for this set (sources 2-3 define none) and the paper "
                         "prints no size (v5-v6.4: conditional on MOESM3 defining it)")
                    continue
                mark(f"gated_G1_{r['cell_id']}", [r["cell_id"]], "built under gate G1", r["set_S"][:160], what)
    rg_carrier_g1 = ("Romero-Garcia's mixed supplements (MOESM1 / MOESM2 docx, the Apollo record's SI .txt and "
                     "Figures_Tables.zip; gate G1)")
    for r in rows:
        c = r["cell_id"]
        if c in cell_set:
            continue
        t, s = r["target_key"], r["set_S"]
        if t == "giacomel2026cartography" and not s.startswith("H-MAGMA"):
            mark(f"gated_G2_{c}", [c], "built under gate G2", s[:160], "Giacomel repository lists / rebuilt DEG sets "
                 "(repo_e045bc5, results/MDD, the paper's AHBA ∩ HPA pool)")
        elif t == "romerogarcia2019synaptic" and s.startswith("FAMILY") and c in RG_KEGG_FAMILIES:
            # register v6.1 Q2 (i): the cells are the KEGG pathways a gated table names; per cell source 1 by the criterion,
            # else Enrichr KEGG_2015 (the vintage of the paper's GO_Biological_Process_2015) by the name rule
            mark(f"gated_G1_{c}", [c], RG_FAMILY_STATUS, s[:160],
                 "register v6.1 Q1 / Q2 as revised by v6.2 P5 / P7 (a) (orchestrator under the operator's standing "
                 "delegation): the family's cells are the KEGG pathways %s names (Romero-Garcia's mixed supplements, gate G1); "
                 "per cell, S = the list the carrier presents as that pathway's input membership, by %s; else the gene list of "
                 "the pathway the printed name reaches in the Enrichr KEGG library chosen by %s (pinned sha256: KEGG_2015 %s, "
                 "KEGG_2016 %s); not auditable if the gated table naming the cells is absent or no name reaches that library"
                 % (RG_KEGG_FAMILIES[c], SOURCE1_CRITERION, KEGG_FAMILY_RULE, PIN["enrichr_kegg_2015"][1],
                    PIN["enrichr_kegg_2016"][1]))
        elif t == "romerogarcia2019synaptic" and s.startswith("FAMILY"):
            mark(f"uncorroborated_{c}", [c], "not auditable (S undefined)", s[:160],
                 UNCORROBORATED + ": the 'second list of genes dysregulated in autism' is identified only in the supplement "
                 "(no external definition is pinned) and the paper prints no size (v6-v6.4: S conditional on the supplements, R2)")
        elif t == "romerogarcia2019synaptic" and re.search(r"MOESM3", s):
            mark(f"gated_G1_{c}", [c], "built under gate G1", s[:160], "Romero-Garcia supplement / MOESM3 (sealed-mixed)")
        elif t == "rasero2023neurogenetics" and re.search(r"repo results/desikan", s):
            mark(f"gated_G1_{c}", [c], "built under gate G1", s[:160], "Rasero repository result lists (selected lists)")
        elif t == "mamat2025molecular" and "Supplementary Table 2" in s:
            mark(f"gated_G1_{c}", [c], "built under gate G1", s[:160],
                 "Mamat Fig. 4B KEGG terms (Supplementary Table 2); per cell the gene list of the %s pathway the "
                 "printed name reaches by the name rule (register 1.6 KEGG rule (ii): the obtainable KEGG release closest in "
                 "date to the paper's submission, 2024-08-14; v6.1 Q2; v6.7 (2): the complete archived KEGG REST releases "
                 "count -- the files pinned: kegg_wb_link %s, kegg_wb_list %s) -- a descriptor family"
                 % (kegg_choice["mamat2025molecular"]["chosen"], PIN["kegg_wb_link"][1], PIN["kegg_wb_list"][1]))
    # register v6 R2 (orchestrator under the operator's standing delegation; decided after the v5 outcome was seen): an
    # S-undefined set whose source 1 (the paper's own list) could lie inside a gated carrier -> the conditional form
    rg_carrier = ("Romero-Garcia's mixed supplements (MOESM1 / MOESM2 docx, the Apollo record's SI .txt and "
                  "Figures_Tables.zip; gate G1)")
    zhang = {"RG-04": "neuron", "RG-V08": "neuron", "RG-V09": "neuron", "RG-N04": "astrocyte",
             "RG-N05": "oligodendrocyte", "RG-N06": "microglia", "RG-N07": "vascular"}
    for cls in ("neuron", "astrocyte", "oligodendrocyte", "microglia", "vascular"):
        cells = [c for c, k in zhang.items() if k == cls]
        mark(f"zhang2014_top500_{cls}", cells, R2_STATUS,
             f"Zhang 2014 (J Neurosci) top 500 {cls}-specific genes among 5 classes (mouse)",
             R2_REASON % (rg_carrier, "the cell class ('%s') together with 'specific', 'top 500', 'Zhang' or 'enriched' (the "
                                      "paper prints the size: 500 symbols; v6.5: the list is corroborated only if its length is "
                                      "500)" % cls)
             + "; else not auditable (S undefined): the rule does not determine a set from sources 2-3 -- Zhang 2014 "
               "publishes FPKM per cell type, not a 'top 500 by specificity' list; the specificity statistic and the "
               "mouse -> human orthology mapping are stated neither by Romero-Garcia nor by §1.6; the journal supplement "
               "is also not obtainable by script (jneurosci.org answers with a Cloudflare challenge)")
    mark("pgc_asd_magma_common_variant", ["RG-N03"], "not auditable (S undefined)",
         "common-variant genes, PGC ASD (5,305 trios) MAGMA",
         UNCORROBORATED + ": no gene list or gene-level threshold is published by the primary source (the set would require "
         "running MAGMA on PGC summary statistics with an unstated threshold), so no external definition is pinned, and the "
         "paper prints no size (v6-v6.4: S conditional on the supplements, R2)")
    fuma = [r["cell_id"] for r in rows if r["set_S"].startswith("FUMA GENE2FUNC BrainSpan DEG set")]
    mark("fuma_brainspan_deg", fuma, "not auditable (S undefined)", "FUMA GENE2FUNC BrainSpan DEG sets (PRE-B01..B14)",
         "FUMA does not distribute its BrainSpan DEG gene sets and its version is unstated; a re-derivation needs "
         "FUMA's expression filter / normalisation, which the register does not pin. R2 examined (register v6): the sets "
         "are FUMA's, not the paper's own, and Pretzsch's article and supplements (read before the register) publish no "
         "gene names at all (register_work draft, section 1), so no gated carrier could hold source 1; the conditional "
         "form does not apply")
    for r in rows:
        c = r["cell_id"]
        if c in cell_set:
            continue
        if r["target_key"] == "berto2022connectivity":
            mark(f"notbuilt_{c}", [c], "not built (row not auditable for a reason other than S)", r["set_S"][:160],
                 "the tested list needs controlled PsychENCODE expression / is a repository list under G1 "
                 "(register §2.5); building S changes no status")
    # PRE-DG (PRE_DG_ROWS.json, written by pre_dg_rows.py): since the v5 TSV (692 rows) the six rows PRE-DG-01 ... 06 are
    # TSV rows of their own and reach the two Gandal sets through the set_S rule above; v4's single 'PRE-DG' unit row (and
    # its '<id> (PRE-DG)' stand-ins) no longer exists. Assert that the routing equals PRE_DG_ROWS.json.
    pdg = json.loads((OUT / "PRE_DG_ROWS.json").read_text(encoding="utf-8"))
    assert pdg["n_other_rows"] == 6
    assert "PRE-DG" not in by_id, "v4's PRE-DG unit row is back in the TSV"
    for direction, sid in (("down", "gandal2018_asd_down"), ("up", "gandal2018_asd_up")):
        want = sorted(x["proposed_cell_id"] for x in pdg["rows"] if x["gandal_direction"] == direction)
        got = sorted(c for c in sets[sid]["cells"] if c.startswith("PRE-DG"))
        assert got == want, (sid, got, want)

    # ======================= remaining TSV rows: no set to build now (component claims, 'none', already not auditable)
    rest = {}
    for r in rows:
        if r["cell_id"] in cell_set:
            continue
        s = r["set_S"]
        why = ("no gene set (component / 'none' claim)" if s.lower().startswith("none") else
               "S already undefined / unpublished in the register (row not auditable or not testable as stated)")
        rest[r["cell_id"]] = {"row": int(r["row"]), "target_key": r["target_key"], "why": why, "set_S": s[:200]}

    # ======================= write (bodies first; the invariance check below runs before anything is written)
    bodies = {}
    manifest_sets = []
    for sid in sorted(sets):
        rec = sets[sid]
        cells = rec.get("cells", [])
        per_cell = []
        for c in cells:
            base = c.split(" ")[0]
            r = by_id[base]
            ac = r["analysis_class"].split(" ")[0]
            oc = None
            if "universe" in rec:
                oc = (rec["universe"][ac]["outcome"] if ac in rec["universe"] else
                      "no class universe (analysis class 'none'; the three / four class universes are reported)"
                      if ac == "none" else f"class {ac}: see universe")
            per_cell.append({"cell": c, "row": int(r["row"]), "analysis_class": r["analysis_class"], "outcome": oc})
        rec["cells_detail"] = per_cell
        body = {k: v for k, v in rec.items() if k not in ("cells",)}
        body["cells"] = cells
        write_this = rec["status"].startswith(("built", "not auditable", "S conditional"))
        # register v6 R5: sizes in columns of each class universe (HGNC genes beside them)
        ent = {"set_id": sid, "status": rec["status"], "cells": cells,
               "sizes": ({"n_hgnc": rec["n_hgnc"], **{c: rec["universe"][c]["n_columns"] for c in CLASSES},
                          "genes_in_class": {c: rec["universe"][c]["n_in_universe"] for c in CLASSES},
                          "paper_size": rec.get("paper_size")} if "universe" in rec else None)}
        if not rec["status"].startswith("built") or "reason" in rec:
            ent["reason"] = rec.get("reason")
        if write_this and not rec["status"].startswith("built under gate"):
            ent["json"] = f"{sid}.json"
            bodies[sid] = body
        manifest_sets.append(ent)
    invariance = check_invariance(manifest_sets, bodies, set(rest), "--allow-set-changes" in sys.argv[1:])
    for ent in manifest_sets:
        if ent.get("json"):
            ent["sha256"] = write_json(OUT / ent["json"], bodies[ent["set_id"]])
    s7_sha = write_json(OUT / "SEGURA_S7_TERMS.json", {
        "what": "Segura 2025 Table S7 (MOESM2 p. 39): the 78 GO BP terms (77 printed rows; row 1 holds two terms) in "
                "printed order; the 71 terms other than SEG-C3a-g are the descriptor cells SEG-C3-D01 ... D71 in this "
                "order. GO id by the register's name rule (v6 R1: exact name, else a synonym of any scope, else case / "
                "UK-US / singular-plural normalisation, each identifying exactly one live term) among the "
                "biological_process terms of GO release 2024-01-17; unresolved -> 'not auditable (S undefined)'.",
        "go_release": go24a.data_version, "go_files": fileref("go_2024-01-17_obo", "go_2024-01-17_gaf"),
        "extract": fileref("x_segura_s7"), "n_terms": len(s7_out),
        "n_resolved": sum(1 for e in s7_out if e["go_id"]), "n_unresolved": sum(1 for e in s7_out if not e["go_id"]),
        "terms": s7_out})
    ug_sha = write_json(OUT / "UNIVERSE_GENES.json", {
        "what": ("register v6.5 (1): the HGNC genes of each class universe (genes with >= 1 column of the class matrix, R5) -- the "
                 "universe in which carrier_test.py computes a source-1 list's Jaccard with the cell's external definition"),
        "n_genes": {c: len(uni[c]) for c in CLASSES}, "classes": {c: sorted(uni[c]) for c in CLASSES}})
    nm_rows = sorted(names.values(), key=lambda e: e["row"])
    nm_sha = write_json(OUT / "NAME_MATCHES.json", {
        "what": ("register DRAFT v6 R1 (orchestrator under the operator's standing delegation, 2026-09-26; fixed after the "
                 "v5 S-build outcome was seen, replacing a reading applied unevenly -- v5 section 1.11 item 2): every GO, "
                 "KEGG, MSigDB, Reactome and figure-label mapping of the register, one record per TSV cell: the name as "
                 "printed, the query, the pinned release, the tier of the name rule that identified exactly one live "
                 "term ((a) exact name; (b) synonym of any scope / former name; (c) case, UK-US spelling or "
                 "singular-plural normalisation) or 'S undefined', and the label written into the TSV"),
        "rule": {"module": "arcs/audit/src_register/name_match.py", "sha256": sha256(Path(NM.__file__))},
        "n_cells": len(nm_rows), "tier_counts": dict(sorted(Counter(str(e["tier"]) for e in nm_rows).items())),
        "cells": nm_rows})
    for e in comparators["sets"]:  # register v6.6 (B1): the pins carrier_tests.json takes (set id, file sha256, members sha256)
        me = next(x for x in manifest_sets if x["set_id"] == e["set_id"])
        e["status"] = me["status"]
        if e["outcome"] == "built":
            e["json"], e["json_sha256"] = me["json"], me["sha256"]
            e["members_sha256"] = _members_sha(bodies[e["set_id"]])
            e["n_hgnc"] = me["sizes"]["n_hgnc"]
            e["columns"] = {c: me["sizes"][c] for c in CLASSES}
    for e in comparators["near_miss_view_v6_7"]["sets"]:  # register v6.7 (1): the near-miss view's pins
        if e["outcome"] == "built":
            me = next(x for x in manifest_sets if x["set_id"] == e["set_id"])
            e["status"] = me["status"]
            e["json"], e["json_sha256"] = me["json"], me["sha256"]
            e["members_sha256"] = _members_sha(bodies[e["set_id"]])
            e["n_hgnc"] = me["sizes"]["n_hgnc"]
            e["columns"] = {c: me["sizes"][c] for c in CLASSES}
    man = {"what": "A1 claims register DRAFT v6.11 pre-freeze S-build manifest (register §1.6, §1.10 (0), §1.11)",
           "builder": "arcs/audit/src_register/s_build.py", "stage1": "arcs/audit/src_register/s_extract.py",
           "builder_sha256": sha256(Path(__file__)), "stage1_sha256": sha256(ROOT / "arcs/audit/src_register/s_extract.py"),
           "comparators_module_sha256": sha256(Path(V66.__file__)),
           "paths": ("register v6 R13: repo files by repo-relative path; external data by their absolute path under "
                     "E:\\data\\asdg (outside the repo, identical for every clone on this box), so a clean-clone re-run "
                     "reproduces this file's hash"),
           "universe_convention": UNIVERSE_CONVENTION,
           "name_rule": {"module": "arcs/audit/src_register/name_match.py", "sha256": sha256(Path(NM.__file__)),
                         "records": "NAME_MATCHES.json"},
           "tsv": {"path": "arcs/audit/claims_register.tsv", "register_version": "DRAFT v6.11", "rows": len(rows),
                   "columns_read": list(TSV_READ_COLS), "columns_read_sha256": tsv_view_sha,
                   "note": ("the S-build reads only these columns of the TSV; their sha256 (one line per row, the columns "
                            "tab-joined in this order, lines joined by LF, UTF-8) is recorded instead of the file's, because "
                            "the TSV header records this manifest's sha256 and a file hash in both directions could never "
                            "settle; a TSV rebuild that leaves these columns unchanged leaves this manifest unchanged")},
           "hgnc": {"path": str(HGNC_FILE), "sha256": PIN["hgnc"][1], "n_approved": hg.n},
           "rule_hgnc": "id given by the source (Ensembl; Entrez for KEGG / WebGestalt; UniProtKB for GO) -> HGNC when it "
                        "names one approved gene, else symbol: approved -> previous -> alias (exact); a symbol or id "
                        "matching >= 2 approved genes at the first matching tier is dropped; drops listed per set",
           "classes": umeta, "min_set": MIN_SET, "big_set": BIG_SET,
           "go_annotation_counts": {g.release: dict(g.n_ann) for g in (go21, go24a, go24b)},
           "kegg_release_rule": kegg_choice,
           "sfari_releases_v6_7": sfc,
           "kegg_2021_human_truncation_v6_2_P4": trunc,
           "buch_goslim_fallback_v6_2_P3": {
               "source": "PANTHER 16.0 PTHR16.0_human as served (register v6.2 P3)", "n_sets": len(fb_summary),
               "n_lt5_V-AAL": sum(1 for x in fb_summary if x["V-AAL_columns"] < MIN_SET),
               "n_gt1000_V-AAL": sum(1 for x in fb_summary if x["V-AAL_columns"] > BIG_SET),
               "V-AAL_columns_min_max": [min(x["V-AAL_columns"] for x in fb_summary), max(x["V-AAL_columns"] for x in fb_summary)],
               "closure_v6_3_O5": {
                   "n_served_equals_is_a_closure": sum(1 for x in fb_summary if x["served_equals_is_a_closure"]),
                   "changed_by_part_of_closure": [{"go_id": x["go_id"], "n_genes_served": x["n_genes_served"],
                                                   "n_genes_is_a_part_of_closure": x["n_genes_is_a_part_of_closure"],
                                                   "increase_pct": x["part_of_increase_pct"]}
                                                  for x in fb_summary if x["n_genes_is_a_part_of_closure"] != x["n_genes_served"]]},
               "sets": fb_summary},
           "source1_criterion": SOURCE1_CRITERION,
           "comparators_v6_6": comparators,
           "segura_s7_terms": {"file": "SEGURA_S7_TERMS.json", "sha256": s7_sha},
           "name_matches": {"file": "NAME_MATCHES.json", "sha256": nm_sha},
           "universe_genes": {"file": "UNIVERSE_GENES.json", "sha256": ug_sha},
           "pre_dg_rows": {"file": "PRE_DG_ROWS.json", "sha256": sha256(OUT / "PRE_DG_ROWS.json")},
           "n_sets": len(manifest_sets),
           "status_counts": dict(sorted(Counter(e["status"] for e in manifest_sets).items())),
           "sets": manifest_sets,
           "rows_without_a_set_now": rest}
    msha = write_json(OUT / "MANIFEST.json", man)
    # per-set JSONs of sets no longer in the S-build (v6: sets replaced by the name rule / Enrichr) are removed, so the folder
    # holds exactly the manifest's files
    keep = {e["json"] for e in manifest_sets if e.get("json")} | {"MANIFEST.json", "SEGURA_S7_TERMS.json", "PRE_DG_ROWS.json",
                                                                  "NAME_MATCHES.json", "UNIVERSE_GENES.json"}
    orphans = sorted(q.name for q in OUT.glob("*.json") if q.name not in keep)
    for q in orphans:
        (OUT / q).unlink()
    print("per-set JSONs removed (no longer in the S-build):", orphans if orphans else "none")
    print("sets:", len(manifest_sets), dict(man["status_counts"]))
    print("rows with no set to build now:", len(rest))
    print("SEGURA_S7_TERMS.json", s7_sha, "resolved", sum(1 for e in s7_out if e["go_id"]), "of", len(s7_out))
    print("NAME_MATCHES.json", nm_sha, len(nm_rows), "cells; tiers", dict(Counter(str(e["tier"]) for e in nm_rows)))
    more_cols = sum(1 for s in sets.values() if "universe" in s
                    and any(v["n_columns"] != v["n_in_universe"] for v in s["universe"].values()))
    print("sets with more columns than HGNC genes (R5):", more_cols, "; unmapped columns per class:",
          {c: umeta[c]["n_unmapped"] for c in CLASSES})
    print("TSV read:", len(rows), "rows; columns_read_sha256", tsv_view_sha)
    print("invariance vs the S-build on disk:", invariance)
    print("MANIFEST.json", msha)


if __name__ == "__main__":
    main()
