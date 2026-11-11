"""Writes SOURCE.md into every E:\\data\\asdg\\register_sets_src\\<source>\\ folder of the A1 pre-freeze S-build
(URL, date, sha256, bytes, licence as stated). Sizes and hashes are computed here; nothing is typed by hand.
Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src_register\\s_sources_md.py
"""
from __future__ import annotations

import hashlib
from pathlib import Path

SRC = Path(r"E:\data\asdg\register_sets_src")
F = "fetched 2026-09-26 by arcs/audit/src_register/fetch_util.py (curl; PMC proof-of-work solved; no login, no e-mail)"
PMC_LIC = ("PMC author manuscript (Europe PMC isOpenAccess = N): publisher copyright; local research use only, "
           "do not redistribute")
F66_ = ("fetched 2026-09-27 by arcs/audit/src_register/fetch_v66.py (fetch_util.get: plain curl; the PMC proof-of-work "
        "solved; no login, no e-mail, no identifier sent)")
META = {
    "gandal2018_science362": ("Gandal et al. 2018, Science 362:eaat8127 (doi 10.1126/science.aat8127; PMC6443102), "
                              "Table S1 (DGE sheet = gene-level ASD / SCZ / BD differential expression)",
                              ["https://pmc.ncbi.nlm.nih.gov/articles/instance/6443102/bin/NIHMS1007359-supplement-Table_S1.xlsx"],
                              F, PMC_LIC),
    "polioudakis2019": ("Polioudakis et al. 2019, Neuron 103:785 (doi 10.1016/j.neuron.2019.06.011; PMC6831089), "
                        "Table S4 'Cluster analysis' (sheet 'Cluster enriched genes')",
                        ["https://pmc.ncbi.nlm.nih.gov/articles/instance/6831089/bin/NIHMS1534343-supplement-5.xlsx"],
                        F + "; Table S3 (per-cell metadata) not fetched", PMC_LIC),
    "satterstrom2020": ("Satterstrom et al. 2020, Cell 180:568 (doi 10.1016/j.cell.2019.12.036; PMC7250485), Table S2 "
                        "(sheet '102_ASD')",
                        ["https://pmc.ncbi.nlm.nih.gov/articles/instance/7250485/bin/NIHMS1569306-supplement-Table_S2.xlsx"],
                        F, PMC_LIC),
    "sanders2015": ("Sanders et al. 2015, Neuron 87:1215 (doi 10.1016/j.neuron.2015.09.016; PMC4624267), the TADA_Scores "
                    "table (gene level; the 65 genes = tadaFdrAscSscExomeSscAgpSmallDel <= 0.1)",
                    ["https://pmc.ncbi.nlm.nih.gov/articles/instance/4624267/bin/NIHMS723829-supplement-8.xlsx"],
                    F + "; supplements 3-7 (per-individual variant / CNV / sample tables) were fetched while locating the "
                        "gene table, identified by sheet name and size only, and deleted without their cells being read",
                    PMC_LIC),
    "go_2017-10-01": ("Gene Ontology release 2017-10-01 (go-basic.obo + goa_human.gaf.gz): the release in force at "
                      "Romero-Garcia 2019's submission (received 2017-10-24)",
                      ["https://release.geneontology.org/2017-10-01/ontology/go-basic.obo",
                       "https://release.geneontology.org/2017-10-01/annotations/goa_human.gaf.gz"], F,
                      "CC BY 4.0 (Gene Ontology Consortium)"),
    "go_2024-06-17": ("Gene Ontology release 2024-06-17: the release in force at Mamat 2025's submission (received "
                      "2024-08-14)",
                      ["https://release.geneontology.org/2024-06-17/ontology/go-basic.obo",
                       "https://release.geneontology.org/2024-06-17/annotations/goa_human.gaf.gz"], F,
                      "CC BY 4.0 (Gene Ontology Consortium)"),
    "go_2024-01-17": ("Gene Ontology release 2024-01-17 (the release Segura 2025 names); copied from "
                      "E:\\data\\asdg\\segura2024symptommapping\\external\\go_release_2024-01-17 (fetched 2026-09-24)",
                      ["https://release.geneontology.org/2024-01-17/ontology/go-basic.obo",
                       "https://release.geneontology.org/2024-01-17/annotations/goa_human.gaf.gz"],
                      "copied 2026-09-26 (sha256 equal to the Segura SOURCE.md)", "CC BY 4.0 (Gene Ontology Consortium)"),
    "kegg_rest_2026-09-26": ("KEGG REST, human pathways: info/pathway ('Last update 2026/09/25'), list/pathway/hsa, "
                             "link/hsa/pathway, list/hsa. The paper's 2021 retrieval is not obtainable -> 'release "
                             "substituted' (register §1.6)",
                             ["https://rest.kegg.jp/info/kegg", "https://rest.kegg.jp/info/pathway",
                              "https://rest.kegg.jp/list/pathway/hsa", "https://rest.kegg.jp/link/hsa/pathway",
                              "https://rest.kegg.jp/list/hsa"], F,
                             "KEGG API: provided for academic use by academic users; no redistribution"),
    "msigdb_2023.1.Hs": ("MSigDB 2023.1.Hs C5 GO:BP gene sets (symbols GMT), the release register §1.6 pins for Pretzsch",
                         ["https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2023.1.Hs/c5.go.bp.v2023.1.Hs.symbols.gmt"],
                         F + " (anonymous download; no registration used)",
                         "MSigDB terms of use (C5 derives from GO, CC BY 4.0); not re-read, no redistribution"),
    "webgestalt_current": ("WebGestalt server gene sets (Reactome; GO Biological_Process; GO Biological_Process_noRedundant; "
                           "GMT with Entrez ids + .des names; summary json). The WebGestalt 2022 release is not "
                           "obtainable (2022.webgestalt.org does not resolve; the server serves no version string) -> "
                           "'release substituted'",
                           ["https://www.webgestalt.org/api/summary/geneset?organism=hsapiens",
                            "https://www.webgestalt.org/api/geneset?organism=hsapiens&database=<pathway_Reactome|"
                            "geneontology_Biological_Process|geneontology_Biological_Process_noRedundant>&standardId="
                            "entrezgene&fileType=<gmt|des>"], F, "not stated by the server"),
    "tissueenrich_bioc3.19": ("TissueEnrich 1.24.1 (Bioconductor 3.19, Date/Publication 2024-05-09; in force at Mamat's "
                              "submission 2024-08-14); inst/extdata/combine-expression.rda read from the tarball "
                              "(dataset 'Protein-Atlas' tissueSpecificGenes)",
                              ["https://bioconductor.org/packages/3.19/bioc/src/contrib/TissueEnrich_1.24.1.tar.gz"], F,
                              "MIT + file LICENSE (package DESCRIPTION)"),
    "psi_data": ("pSI.data 1.0 (Xu, Wells, O'Brien, Nehorai, Dougherty; Date 2013-12-03; the Dougherty laboratory's "
                 "distribution; NOT on CRAN: https://cran.r-project.org/src/contrib/Archive/pSI.data/ returns 404). "
                 "human.rda (BrainSpan: developmental.periods 6 regions x 10 periods; young.adulthood 6 regions) and "
                 "mouse.rda (35 bacTRAP cell types) read from the tarball",
                 ["https://sites.wustl.edu/doughertylab/psi_package-page/ (download link)",
                  "https://sites.wustl.edu/doughertylab/files/2014/01/pSI.data_1.0.tar_.gz"], F,
                 "GPL (>= 2) (package DESCRIPTION)"),
    "lake2018": ("Lake et al. 2018, Nat Biotechnol 36:70 (doi 10.1038/nbt.4038), Supplementary Tables 1-13 xlsx (Table S3 "
                 "'All Clusters' block used); copied from E:\\data\\asdg\\explore_public\\celltype_lake2018\\journal_esm "
                 "(fetched 2026-09-23)",
                 ["https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fnbt.4038/MediaObjects/"
                  "41587_2018_BFnbt4038_MOESM11_ESM.xlsx"], "copied 2026-09-26",
                 "no open licence stated; local research use, no redistribution"),
    "shin2018": ("Shin et al. 2018, Cereb Cortex 28:3267 (doi 10.1093/cercor/bhx197; PMC13017599) supplementary zip; "
                 "Table S1 (docx) = the 9 cell-type panels; extract/ made by s_extract.py",
                 ["https://pmc.ncbi.nlm.nih.gov/articles/instance/13017599/bin/cercor_28_9_3267_s1.zip"], F,
                 "(c) The Author 2017, OUP, all rights reserved; local research copy only"),
    "grove2019_magma": ("Grove et al. 2019, Nat Genet 51:431 (doi 10.1038/s41588-019-0344-8), Supplementary PDF (Table 10 "
                        "= top 25 MAGMA genes, p. 68); copied from E:\\data\\asdg\\a3_programs\\grove2019_magma "
                        "(fetched 2026-09-25); extract/ made by s_extract.py",
                        ["https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41588-019-0344-8/"
                         "MediaObjects/41588_2019_344_MOESM1_ESM.pdf"], "copied 2026-09-26",
                        "(c) 2019 The Author(s), under exclusive licence to Springer Nature; local research use"),
    "kang2011": ("Kang et al. 2011, Nature 478:483 (doi 10.1038/nature10523) Supplementary Tables 1-17 (.xls). Checked for "
                 "a module-membership table: none (Table 9 = module, colour, size, hub genes, DAVID term hits). The PMC "
                 "copy (NIHMS321722-supplement-7.xlsx, sha256 cac83a06048b881a7b6f05616b9f8609240f8d1d2972a8fa9e20372a04b9a27f) "
                 "and the hbatlas.org copy (nature10523-s2.xls, identical sha256 to this file) were fetched and deleted; "
                 "hbatlas.org NCTX_Modules.xls / Regional_Modules.xls were fetched, found to be Johnson et al. 2009 "
                 "modules (not Kang 2011), and deleted. extract/ made by s_extract.py. v6.8 (B S2): MOESM50 held "
                 "identifier-bearing sheets (Supplementary Tables 1-4: donor codes; Tables 15-16 wider than 50 columns), so "
                 "it was reduced to 'Supple Table 9.' (the one sheet s_extract.py reads, clean, kept whole) and deleted; "
                 "its sha256, bytes and sheet names + dimensions are in the table below and in extract_manifest.json",
                 ["https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fnature10523/"
                  "MediaObjects/41586_2011_BFnature10523_MOESM50_ESM.xls",
                  "https://hbatlas.org/pages/data"], F, "Nature supplementary material; local research use"),
    "moreau2020_locus": ("Moreau et al. 2020 locus gene lists, repo data/cnv_genes_cnv16p112.csv and cnv_genes_cnv22q112.csv "
                         "@ 9e8af9c1ea094247ba1ee8824daeb7339a0a0d0e; copied from E:\\data\\asdg\\moreau2020mutations"
                         "\\repo_GeneExp_and_CNV_FCsignatures\\data (fetched 2026-09-24; Moreau is ungated)",
                         ["https://github.com/kkumar-iitkgp-livia/GeneExp_and_CNV_FCsignatures"], "copied 2026-09-26",
                         "MIT (repo LICENSE)"),
    "segura2025_tables": ("Segura et al. 2025 (Mol Psychiatry; PMC12700815) MOESM2 supplementary tables PDF (p. 39 = Table "
                          "S7, read by s_extract.py; nothing else of the PDF is read) and the Table S4 1,046-symbol list "
                          "parsed 2026-09-24 (segura2024symptommapping/derived); copied from "
                          "E:\\data\\asdg\\segura2024symptommapping (Segura is ungated)",
                          ["https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12700815/supplementaryFiles"],
                          "copied 2026-09-26", "CC BY-NC-ND 4.0 (Europe PMC licence field)"),
    "sfari_gene": ("SFARI Gene Human Gene Module export, 2026 Q2 release (07-12-2026), export 09-25-2026; copied from "
                   "E:\\data\\asdg\\a3_programs\\sfari_gene. Re-checked 2026-09-26: the live download is still the "
                   "07-12-2026 release. No archived release is obtainable (web.archive.org CDX offline; "
                   "gene-archive.sfari.org redirects to gene.sfari.org; release notes are PDFs of changes, not gene lists)",
                   ["https://gene.sfari.org/wp-content/themes/sfari-gene/utilities/download-csv.php?api-endpoint=genes"],
                   "copied 2026-09-26", "(c) SFARI Gene, all rights reserved; do not redistribute"),
    "velmeshev2019": ("Velmeshev et al. 2019, Science 364:685 Data S4 (the .xls was never copied here; it stood at "
                      "E:\\data\\asdg\\explore_public\\celltype_velmeshev2019\\pmc_author_manuscript_suppl). extract/ = sheet "
                      "'ASD_DEGs' only, made by s_extract.py. v6.9 (S2-residual): the .xls (sha256 53c9b418...8e12, 487936 B; "
                      "its per-individual sheet 'Individual_specific_DEGs' classified by the privacy guard, never read) was "
                      "reduced by reduce_v68.py to 'ASD_DEGs' columns 1-7 (the reduction beside where it stood) and deleted on "
                      "2026-09-30; s_extract.py reads the reduction, the extract unchanged",
                      ["https://pmc.ncbi.nlm.nih.gov/articles/instance/7678724/bin/NIHMS1053005-supplement-Data_S4.xls"],
                      "extract written 2026-09-26", "Science copyright; PMC author manuscript; local research use"),
    # register DRAFT v6 (decisions R1, R12 of the orchestrator under the operator's standing delegation; fetch_v6.py)
    "enrichr_2026-09-26": ("Enrichr gene-set libraries served by name (geneSetLibrary?mode=text&libraryName=<name>; every "
                           "attempt returned HTTP 200 with a tab-separated library): KEGG_2021_Human (the library "
                           "Vairam / Roy name: 'KEGG 2021 Human' via gseapy prerank; since v6.1 also Leyhausen's, by "
                           "the closest-in-date rule), KEGG_2015 (Romero-Garcia's KEGG families: the Enrichr vintage of its "
                           "GO_Biological_Process_2015, v6.1 Q2), KEGG_2016 (v6.2 P5: the second Romero-Garcia KEGG candidate, "
                           "also served while GO_Biological_Process_2015 was current), KEGG_2026 (Mamat's KEGG family: the "
                           "obtainable KEGG release closest in date to its submission, v6.1 Q2) and GO_Biological_Process_2013, "
                           "_2015, _2017, _2017b, _2018 (the Enrichr GO BP libraries up to and just after Romero-Garcia's "
                           "submission, 2017-10-24; fetched to identify the release the paper used: register 1.6, R12); "
                           "datasetStatistics.json = Enrichr's current catalogue (it lists GO_Biological_Process_2021 / "
                           "2023 / 2025 / 2026 and KEGG_2021_Human; the older GO BP libraries are not listed but are "
                           "still served by name)",
                           ["https://maayanlab.cloud/Enrichr/geneSetLibrary?mode=text&libraryName=<name>",
                            "https://maayanlab.cloud/Enrichr/datasetStatistics"],
                           "fetched 2026-09-26 by arcs/audit/src_register/fetch_v6.py (fetch_util.get: plain curl; no "
                           "login, no e-mail, no identifier sent)",
                           "Enrichr: free for academic use (Ma'ayan Laboratory); libraries derive from GO (CC BY 4.0) and "
                           "KEGG (academic use); local research copy, no redistribution"),
    "go_2021-11-16": ("Gene Ontology release 2021-11-16 (go-basic.obo + goa_human.gaf.gz): the release in force at Buch "
                      "2023's submission (Nature Neuroscience, received 2021-11-29; the latest GO archive release on or before "
                      "it); the annotations of Buch's PANTHER 16.0 GO-slim fallback sets (register v6.1 Q7)",
                      ["https://release.geneontology.org/2021-11-16/ontology/go-basic.obo",
                       "https://release.geneontology.org/2021-11-16/annotations/goa_human.gaf.gz"],
                      "fetched 2026-09-26 by arcs/audit/src_register/fetch_v6.py (fetch_util.get: plain curl; no login, no "
                      "e-mail, no identifier sent)", "CC BY 4.0 (Gene Ontology Consortium)"),
    "panther_16.0_goslim": ("PANTHER 16.0 GO-slim ontology (PANTHERGOslim.obo, Last-Modified 2020-12-04): the release Buch "
                            "2023 names; used to map Buch's printed figure labels to terms by the register's name "
                            "rule (register 1.1 / 1.6, R1); and (v6.2 P3) PANTHER 16.0's own gene-to-GO-slim annotation "
                            "as served (PTHR16.0_human: 11 tab-separated columns, gene id 'HUMAN|HGNC=<n>|UniProtKB=<acc>', "
                            "GO-slim MF / BP / CC in columns 7 / 8 / 9 as 'name#GO:id;...'), from which the 27 Buch "
                            "GO-slim fallback sets are built (the sets that apply when MOESM3 fails the source-1 "
                            "criterion; MOESM3 itself stays under gate G1)",
                            ["https://data.pantherdb.org/PANTHER16.0/ontology/PANTHERGOslim.obo",
                             "https://data.pantherdb.org/ftp/sequence_classifications/16.0/"
                             "PANTHER_Sequence_Classification_files/PTHR16.0_human"],
                            "fetched 2026-09-26 by arcs/audit/src_register/fetch_v6.py (fetch_util.get: plain curl; no "
                            "login, no e-mail, no identifier sent)",
                            "PANTHER: GO-derived content (GO: CC BY 4.0); PANTHER terms of use; local research copy"),
    # register DRAFT v6.6 (B2 / C5; orchestrator under the operator's standing delegation): the comparators' sources, fetched after
    # register 1.6's resolution rule was written (2026-09-27T02:56:44Z); fetch_v66.py
    "parikshak2013": ("Parikshak et al. 2013, Cell 155:1008 (doi 10.1016/j.cell.2013.10.031; PMC3934107): Table S1 (supplement 02; "
                      "TableS1A = gene-level module labels of the fetal network) and, since v6.6, extract/tableS1D_gene_lists.tsv = "
                      "supplement 03's sheet TableS2A ('Table S1D - Gene lists used in enrichment analyses': ID All, asdM12 / asdM16 "
                      "from Voineagu, FMRP interactors from Darnell ...), every non-empty cell as (row, col, text). Supplement 03 "
                      "(sha256 c12bc55c9f5f22cf6899555de8ae99ecf8a65245a1c0c8fbf2ad2dcf94a2062b, 253,279 B) also holds a "
                      "per-individual variant sheet (TableS2C); it was deleted after the extract (while locating the list, "
                      "TableS2C's header row and one row and some TableS2D rows were displayed once; nothing of them is kept or "
                      "used). Supplements 04 / 05: not kept. v6.7: supplement 01 (Extended Experimental Procedures, where "
                      "'asdM12 (444 genes) and adsM16 (386 genes)' are named) and the article page (the naming sentence) -- the "
                      "near-miss view's evidence. The extract cannot be rebuilt from this folder (the original was deleted for "
                      "privacy; only its sha256 is kept: v6.7 N11). v6.8 (B S2): supplement 02 held identifier-bearing sheets "
                      "(TableS1B: BrainSpan sample codes as column headers; TableS1C: sample metadata; TableS1A itself wider than "
                      "50 columns), so it was reduced to TableS1A's three columns s_build.py reads ('ENSEMBL GENE ID', 'Gene "
                      "Symbol', 'Module Label') and deleted; its sha256, bytes and sheet names + dimensions are in the table below "
                      "and in extract_manifest.json",
                      ["https://pmc.ncbi.nlm.nih.gov/articles/instance/3934107/bin/NIHMS545068-supplement-02.xlsx",
                       "https://pmc.ncbi.nlm.nih.gov/articles/instance/3934107/bin/NIHMS545068-supplement-03.xlsx",
                       "https://pmc.ncbi.nlm.nih.gov/articles/instance/3934107/bin/NIHMS545068-supplement-01.pdf",
                       "https://pmc.ncbi.nlm.nih.gov/articles/PMC3934107/"],
                      F + "; supplement 03 fetched 2026-09-27 by fetch_v66.py", PMC_LIC),
    "parikshak2016": ("Parikshak et al. 2016, Nature 540:423 (doi 10.1038/nature20612; PMC7102905), Supplementary Table 2 "
                      "(TableS2a = cortex DGE + WGCNA module labels) and, since v6.6, Supplementary Table 4 (its CTX.M12 / CTX.M16 "
                      "are its own rWGCNA modules: no list named asdM12 / asdM16 -- evidence for register 1.6 R-e). v6.8 (B S2): "
                      "Supplementary Table 2 held identifier-bearing sheets (TableS2c: brain-bank sample codes; TableS2d and "
                      "TableS2a wider than 50 columns), so it was reduced to TableS2a's five columns s_build.py reads and deleted; "
                      "its sha256, bytes and sheet names + dimensions are in the table below and in extract_manifest.json. "
                      "Supplementary Table 4 is kept whole (sha256 only; no builder reads it) although its TableS4a is wider than "
                      "50 columns (identifier-bearing by the v6.8 rule W; gene-level) -- register 1.6 lists it",
                      ["https://pmc.ncbi.nlm.nih.gov/articles/instance/7102905/bin/NIHMS1050915-supplement-SuppTable2.xlsx",
                       "https://pmc.ncbi.nlm.nih.gov/articles/instance/7102905/bin/NIHMS1050915-supplement-SuppTable4.xlsx"],
                      F + "; Table 4 fetched 2026-09-27 by fetch_v66.py (Tables 1 / 3 were fetched, searched for 'asdM' and "
                          "deleted)", PMC_LIC),
    "voineagu2011": ("Voineagu et al. 2011, Nature 474:380 (PMC3607626), Supplementary Table 2 (.xls): module membership kME of "
                     "every probe for 18 colour-named modules (no module assignment); the article page (v6.7: it names the "
                     "modules M12 / M16, never 'asdM'); and, since v6.7 N1, extract/table14_M12_genes.tsv = the Supplementary "
                     "Information's 'Supplementary Table 14. M12 module genes and associated GWAS p values' (pp. 19-23, 380 gene "
                     "symbols; s_extract.py, the pages located by the caption). The Supplementary Information PDF "
                     "(NIHMS313080-supplement-1.pdf, sha256 59f2ded45c95b73af0f4c0152da530f2196d0b8e371ca7897d5444c4c6f9cfd5, "
                     "12,443,046 B) also holds per-individual tables: only the Table 14 pages were read into the extract, no "
                     "other page's text was displayed (the caption search and the p. 10 module-colour assertions are "
                     "programmatic; while the parser was written, p. 19's first lines and the Table 14 pages' non-symbol "
                     "tokens were displayed); the PDF was deleted after the extract, its sha256 kept",
                     ["https://pmc.ncbi.nlm.nih.gov/articles/instance/3607626/bin/NIHMS313080-supplement-2.xls",
                      "https://pmc.ncbi.nlm.nih.gov/articles/instance/3607626/bin/NIHMS313080-supplement-1.pdf (deleted)",
                      "https://pmc.ncbi.nlm.nih.gov/articles/PMC3607626/"], "fetched 2026-09-27 by arcs/audit/src_register/fetch_v66.py (fetch_util.get: plain curl; the PMC proof-of-work solved; no login, no e-mail, no identifier sent)",
                     PMC_LIC),
    "steinberg2013_fmrp": ("Steinberg & Webber 2013, Am J Hum Genet 93:825 (PMC3824119), Document S1 (mmc1.pdf): Figures S1-S5, "
                           "Tables S1-S16; no list of the 842 FMRP targets (only subsets disrupted in probands, Table S14) -- "
                           "evidence for register 1.6 R-e (Buch FMRP)",
                           ["https://pmc.ncbi.nlm.nih.gov/articles/instance/3824119/bin/mmc1.pdf"], "fetched 2026-09-27 by arcs/audit/src_register/fetch_v66.py (fetch_util.get: plain curl; the PMC proof-of-work solved; no login, no e-mail, no identifier sent)",
                           "Elsevier / AJHG (open access article); local research use"),
    "spark2018": ("SPARK Consortium 2018, Neuron 97:488 (PMC7444276): the SPARK gene list it links (SPARK_gene_list.pdf; 'updated "
                  "July 2019'; 153 single genes, 19 CNVs; extract/spark_single_genes.tsv by s_extract.py) and the Wayback CDX "
                  "listings of its two URLs (the S3 copy's captures of 2021-08-10 and 2021-12-22 carry the downloaded file's "
                  "SHA-1 digest PUEVM3POAT2EPUG6INRSRYGPIDXOANNZ: the release current at Buch's submission, 2021-11-29). The "
                  "article's supplementary PDF (the consortium member list) was fetched and deleted unread beyond its first page",
                  ["https://spark-sf.s3.amazonaws.com/SPARK_gene_list.pdf",
                   "https://web.archive.org/cdx/search/cdx?url=<the two URLs>&output=json&filter=statuscode:200&to=20260926"],
                  "fetched 2026-09-27 by arcs/audit/src_register/fetch_v66.py (fetch_util.get: plain curl; the PMC proof-of-work solved; no login, no e-mail, no identifier sent)", "SPARK / Simons Foundation participant material; local research use"),
    "sanders2019_rgd": ("Sanders et al. 2019, Nat Med 25:1477 (PMC8656349): Tables S1 / S2 / S4 (.xlsx; gene- and CNV-level) and the "
                        "supplemental PDF; extract/table_s1_flags.tsv = Table S1's gene ids and its three disorder-gene flags "
                        "(ASD65, DDD93, CHD253)",
                        ["https://pmc.ncbi.nlm.nih.gov/articles/instance/8656349/bin/NIHMS1754502-supplement-Tables_S1__S2__S4.xlsx",
                         "https://pmc.ncbi.nlm.nih.gov/articles/instance/8656349/bin/NIHMS1754502-supplement-Supplemental_info_"
                         "and_Tables_S3__S5.pdf"], "fetched 2026-09-27 by arcs/audit/src_register/fetch_v66.py (fetch_util.get: plain curl; the PMC proof-of-work solved; no login, no e-mail, no identifier sent)", PMC_LIC),
    "nair2009_psoriasis": ("Nair et al. 2009, Nat Genet 41:199 (PMC2745122): the article page (Table 2: loci with 'notable nearby "
                           "genes') and the supplement PDF (Supplementary Tables 1-7) -- evidence for register 1.6 R-e (no gene list)",
                           ["https://pmc.ncbi.nlm.nih.gov/articles/PMC2745122/",
                            "https://pmc.ncbi.nlm.nih.gov/articles/instance/2745122/bin/NIHMS83342-supplement-1.pdf"],
                           "fetched 2026-09-27 by arcs/audit/src_register/fetch_v66.py (fetch_util.get: plain curl; the PMC proof-of-work solved; no login, no e-mail, no identifier sent)", PMC_LIC),
    "pfenning2014_vocal": ("Pfenning et al. 2014, Science 346:1256846 (PMC4385736): the supplement PDF (materials, methods, table "
                           "captions) and, since v6.7 N4, science_download/pfenning-tables-s1-to-s8.zip = Tables S1-S8 as "
                           "science.org serves them (8 gene-level workbooks; every sheet passed the identifier-header guard; only "
                           "sheet names, dimensions and counts were displayed): Table S3's nine region sheets and Table S6's one "
                           "cross-species sheet, none named 'vocal learning' -- evidence for register 1.6 R-e on the contents",
                           ["https://pmc.ncbi.nlm.nih.gov/articles/instance/4385736/bin/NIHMS666880-supplement-Supplemental_"
                            "material.pdf",
                            "https://www.science.org/doi/suppl/10.1126/science.1256846/suppl_file/pfenning-tables-s1-to-s8.zip"],
                           "the PDF fetched 2026-09-27 by fetch_v66.py (plain curl; no identifier sent); the zip on 2026-09-27 in a "
                           "real Chrome browser started with a FRESH, EMPTY profile and driven over the DevTools protocol (plain "
                           "HTTPS meets a Cloudflare bot challenge, HTTP 403; the Wayback Machine holds no capture; Europe PMC does "
                           "not serve it; the chrome-devtools MCP could not start, its profile being in use) -- the challenge "
                           "passed by the browser itself; no login, no cookie carried in, no e-mail or other identifier entered or "
                           "sent; verified by sha256 in fetch_v66.py (MANUAL)",
                           "Science (AAAS) supplementary material; publisher copyright; local research use only"),
    "pua2016_cardiac": ("Pua et al. 2016, J Cardiovasc Transl Res 9:3 (PMC4767849): extract/st1_gene_list.tsv = ESM1's sheet 'ST1 "
                        "List of genes' only, every non-empty cell as (row, col, text). ESM1 (sha256 "
                        "6a3c322a81aa7fce36c533d6997ff7efa23c3038b63c4b5f2cdd42479caf902f, 204,623 B) also holds a per-sample sheet "
                        "(ST5); it was deleted after the extract (rows of its ST5 / ST6 sheets were displayed once while "
                        "locating the list; nothing of them is kept or used). The extract cannot be rebuilt from this folder (the "
                        "original was deleted for privacy; only its sha256 is kept: v6.7 N11)",
                        ["https://pmc.ncbi.nlm.nih.gov/articles/instance/4767849/bin/12265_2016_9673_MOESM1_ESM.xlsx"], "fetched 2026-09-27 by arcs/audit/src_register/fetch_v66.py (fetch_util.get: plain curl; the PMC proof-of-work solved; no login, no e-mail, no identifier sent)",
                        "CC BY (open access article, Springer)"),
    "sfari_wayback_2022-01-24": ("SFARI Gene genes CSV (the Human Gene Module export) as the Wayback Machine captured it on "
                                 "2022-01-24 (capture 20220124104055; raw 'id_' form), and the CDX listing of the endpoint's "
                                 "captures: the capture before Buch's submission (2021-10-22) and this one differ in digest, so "
                                 "this is the earliest archived release after 2021-11-29 (register 1.6 R-b, v6.6's digest reading); "
                                 "v6.7 N2: both captures serve the SAME release (09-02-2021), so the comparator is the 10-22-2021 "
                                 "export (sfari_wayback_captures/); this capture is kept as the evidence of the within-release "
                                 "change",
                                 ["https://web.archive.org/web/20220124104055id_/https://gene.sfari.org/wp-content/themes/sfari-"
                                  "gene/utilities/download-csv.php?api-endpoint=genes",
                                  "https://web.archive.org/cdx/search/cdx?url=gene.sfari.org/wp-content/themes/sfari-gene/utilities/"
                                  "download-csv.php?api-endpoint=genes&output=json&filter=statuscode:200&to=20260926"],
                                 "fetched 2026-09-27 by arcs/audit/src_register/fetch_v66.py (fetch_util.get: plain curl; the PMC proof-of-work solved; no login, no e-mail, no identifier sent)", "(c) SFARI Gene, all rights reserved; do not redistribute"),
    "diseases_v2_2022-02-09": ("DISEASES v2 (Jensen lab; figshare, published 2022-02-09): the filtered knowledge, experiments and "
                               "text-mining channel files and the dictionary; and the Wayback CDX listings of the weekly files "
                               "(per file, on different dates; no weekly set archived near 2021-11-29: register 1.6 R-b)",
                               ["https://ndownloader.figshare.com/files/34018280 (knowledge filtered)",
                                "https://ndownloader.figshare.com/files/34018298 (experiments filtered)",
                                "https://ndownloader.figshare.com/files/34018313 (text mining filtered)",
                                "https://ndownloader.figshare.com/files/34018265 (dictionary)",
                                "https://web.archive.org/cdx/search/cdx?url=download.jensenlab.org/human_disease_<channel>_filtered"
                                ".tsv&output=json&filter=statuscode:200&to=20260926"], "fetched 2026-09-27 by arcs/audit/src_register/fetch_v66.py (fetch_util.get: plain curl; the PMC proof-of-work solved; no login, no e-mail, no identifier sent)", "CC BY 4.0 (figshare)"),
    "rgd_2026-09-19": ("RGD: human gene -> RDO disease annotations (GAF 2.2, generated 2026-09-19) and RDO.obo (releases/2026-09-19); "
                       "the release obtainable at download (RGD archives its ontology weekly, not its annotation files); v6.7: "
                       "superseded by rgd_wayback_2024-07-24/ (the uniform archive rule), kept as v6.6's record",
                       ["https://download.rgd.mcw.edu/data_release/annotations/human_genes_rdo.gaf.gz",
                        "https://download.rgd.mcw.edu/ontology/disease/RDO.obo"], "fetched 2026-09-27 by arcs/audit/src_register/fetch_v66.py (fetch_util.get: plain curl; the PMC proof-of-work solved; no login, no e-mail, no identifier sent)",
                       "RGD data: free for research use (RGD terms); local research copy"),
    "ctd_2026-08-28": ("Comparative Toxicogenomics Database, report created 2026-08-28: CTD_genes_diseases.tsv.gz (the gene-disease "
                       "file of its downloads page; 3.2 GB) and CTD_diseases.tsv.gz (MEDIC); extract/schizophrenia_rows.tsv = the "
                       "rows of MESH:D012559 and its MEDIC descendants. CTD's web pages sit behind a human-verification page; the "
                       "files do not. v6.7: superseded by ctd_wayback_2024-02-10/ (the uniform archive rule), kept as v6.6's record",
                       ["https://ctdbase.org/reports/CTD_genes_diseases.tsv.gz", "https://ctdbase.org/reports/CTD_diseases.tsv.gz"],
                       "fetched 2026-09-27 (CTD_genes_diseases.tsv.gz by curl -C - with a two-hour limit, fetch_v66.py's big-file "
                       "path; no login, no e-mail, no identifier sent)",
                       "CTD terms (file header): cite CTD; notify CTD of published use -- to be settled by the operator before "
                       "any publication; local research copy"),
    "gandal2022_nature611": ("Gandal et al. 2022, Nature 611:532 (PMC9668748): Supplementary Data 5 (MOESM7: WGCNA module "
                             "membership, gene and isoform level; extract/gene_level_modules.tsv = Gene_Level's ids and module) and "
                             "6 (MOESM8: module functional characterisation incl. the ASD association per region), Fig. 3 and Fig. 4 "
                             "(the printed module labels). MOESM3 / MOESM9 / MOESM10 (donor / sample / cell metadata) and MOESM4-6 "
                             "were fetched while locating the tables and deleted (a few rows of MOESM3 'datMeta_datSeq', MOESM9 "
                             "'MethylCTD_Props' and MOESM10 'snRNAseq_metadata' were displayed once; nothing kept or used). v6.7 "
                             "N6: the article page (the Results text describing GeneM3 and GeneM5)",
                             ["https://pmc.ncbi.nlm.nih.gov/articles/instance/9668748/bin/41586_2022_5377_MOESM7_ESM.xlsx",
                              "https://pmc.ncbi.nlm.nih.gov/articles/instance/9668748/bin/41586_2022_5377_MOESM8_ESM.xlsx",
                              "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/af98/9668748/ab4c8e9bb88f/41586_2022_5377_Fig3_HTML.jpg",
                              "https://cdn.ncbi.nlm.nih.gov/pmc/blobs/af98/9668748/85cfc3a5c3a3/41586_2022_5377_Fig4_HTML.jpg",
                              "https://pmc.ncbi.nlm.nih.gov/articles/PMC9668748/"],
                             "fetched 2026-09-27 by arcs/audit/src_register/fetch_v66.py (fetch_util.get: plain curl; the PMC proof-of-work solved; no login, no e-mail, no identifier sent)", "CC BY 4.0 (open access article)"),
    "reactome_v92": ("Reactome release 92 (files dated 2025-03-27; release 93 is dated 2025-06-17): ReactomePathways.gmt.zip and "
                     "ReactomePathways.txt from Reactome's per-release archive",
                     ["https://download.reactome.org/92/ReactomePathways.gmt.zip",
                      "https://download.reactome.org/92/ReactomePathways.txt"], "fetched 2026-09-27 by arcs/audit/src_register/fetch_v66.py (fetch_util.get: plain curl; the PMC proof-of-work solved; no login, no e-mail, no identifier sent)", "CC BY 4.0 (Reactome)"),
    "syngo_1.2_20231201": ("SynGO release 1.2 (= release '20231201'; 'released in 2023 ... 4218 annotations against 1602 unique "
                           "human genes') as the portal serves it now (syngo1.2_complete_data.zip, repackaged 2025-03-29), and two "
                           "Wayback captures of the portal's home page (2025-04-06, 2025-11-18) listing '20231201' as the newest "
                           "release (register 1.6 R-b: current at Pagani's submission, 2025-04-17)",
                           ["https://www.syngoportal.org/data/syngo1.2_complete_data.zip",
                            "https://web.archive.org/web/20250406180025id_/https://syngoportal.org/",
                            "https://web.archive.org/web/20251118230922id_/https://syngoportal.org/"], "fetched 2026-09-27 by arcs/audit/src_register/fetch_v66.py (fetch_util.get: plain curl; the PMC proof-of-work solved; no login, no e-mail, no identifier sent)",
                           "SynGO: CC BY 4.0 (portal); local research copy"),
    "buch2023_aam": ("Buch et al. 2023 (Nat Neurosci 26:650), the accepted author manuscript (Apollo, University of Cambridge "
                     "repository; 45 pp.), read for the Methods' 'Gene set lists' (p. 31) and references 19, 61, 117-131 (register "
                     "v6.6 C5: every Fig. 5c-e set names its source)",
                     ["https://www.repository.cam.ac.uk/bitstreams/32fb39c5-edbc-4ff3-b1e4-6a02695e2e83/download"],
                     "fetched 2026-09-27 (plain curl; no login, no e-mail, no identifier sent)",
                     "accepted manuscript, repository licence as stated there; local research use"),
    # register DRAFT v6.7 ((2) the uniform archive rule; N1 / N2 / N4 / N6 / N7): fetch_v66.py FILES67 and MANUAL
    "sfari_wayback_captures": ("SFARI Gene genes CSV (the Human Gene Module export) as the Wayback Machine captured it: every "
                               "capture with a distinct content digest, 2020-10-31 ... 2024-05-15 (12 files; the 2024-03-24 "
                               "capture is stored gzip-encoded, as served), and served_labels.json = the release label each of "
                               "the 17 HTTP-200 captures serves (its Content-Disposition file name '<release>release_<export>"
                               "export'; HEAD requests) -- the uniform archive rule for Liu's / Xing's SFARI cells and Buch's "
                               "(v6.7 (2), N2)",
                               ["https://web.archive.org/web/<timestamp>id_/https://gene.sfari.org/wp-content/themes/sfari-gene/"
                                "utilities/download-csv.php?api-endpoint=genes"], F66_,
                               "(c) SFARI Gene, all rights reserved; do not redistribute"),
    "kegg_wayback_2024-09-16": ("KEGG REST link/hsa/pathway and list/pathway/hsa as the Wayback Machine captured them on 2024-09-16 "
                                "(the complete archived KEGG REST release nearest Mamat's submission, 2024-08-14) and the CDX "
                                "listings of both endpoints (v6.7 (2): KEGG rule (ii))",
                                ["https://web.archive.org/web/20240916203812id_/https://rest.kegg.jp/link/hsa/pathway",
                                 "https://web.archive.org/web/20240916190349id_/https://rest.kegg.jp/list/pathway/hsa"], F66_,
                                "KEGG: academic use per the KEGG REST terms; local research copy"),
    "rgd_wayback_2024-07-24": ("RGD's human RDO annotation file (annotated_rgd_objects_by_ontology/homo_genes_rdo, GAF 2.2, "
                               "'date-generated: 2024-07-20') as the Wayback Machine captured it on 2024-07-24 -- the earliest "
                               "COMPLETE capture after 2021-11-29 (the 2023-06-06 and 2024-05-26 captures are cut short by the "
                               "crawler: capture_lengths.json, HEAD requests) -- with RDO_20240720_v1.283 from RGD's own weekly "
                               "ontology archive (extract/ = the ontology decompressed) and the CDX listing (v6.7 (2))",
                               ["https://web.archive.org/web/20240724223811id_/https://download.rgd.mcw.edu/ontology/"
                                "annotated_rgd_objects_by_ontology/homo_genes_rdo",
                                "https://download.rgd.mcw.edu/ontology/disease/2024/RDO_20240720_v1.283.obo.gz"], F66_,
                               "RGD data: free for research use (RGD terms); local research copy"),
    "ctd_wayback_2024-02-10": ("Comparative Toxicogenomics Database, 'Report created: Wed Jan 31 12:01:18 EST 2024': "
                               "CTD_genes_diseases.tsv.gz (2.7 GB) and CTD_diseases.obo.gz (MEDIC, dated 31:01:2024) as the "
                               "Wayback Machine captured them on 2024-02-10 -- the earliest day after 2021-11-29 with a gene-"
                               "disease file and its vocabulary both captured -- the seven CDX listings (exact URLs; v6.6's "
                               "'not in the Wayback Machine' came from a malformed query) and extract/ (the vocabulary "
                               "decompressed; schizophrenia_rows.tsv = the rows of MESH:D012559 and its 5 MEDIC descendants, "
                               "97,378 rows) (v6.7 (2))",
                               ["https://web.archive.org/web/20240210030103id_/https://ctdbase.org/reports/CTD_genes_diseases.tsv.gz",
                                "https://web.archive.org/web/20240210030137id_/https://ctdbase.org/reports/CTD_diseases.obo.gz"],
                               "fetched 2026-09-27 by fetch_v66.py (the big file by curl -C - with a two-hour limit; no login, no "
                               "e-mail, no identifier sent)",
                               "CTD terms (file header): cite CTD; link to CTD; 'You must notify CTD, and describe your use of our "
                               "data'; periodic access to the publication -- CTD must be notified before any result using it is "
                               "published (register 1.6 and 6, v6.7 (4)); local research copy"),
    "darnell2011_fmrp": ("Darnell et al. 2011, Cell 146:247 (PMC3232425): Tables S2A-C (.xls; S2A 'FMRP Targets (842)', gene "
                         "level; every sheet passed the identifier-header guard; only sheet names, dimensions, gene-type header "
                         "cells and counts were displayed) and the article page ('a stringent set of 842 FMRP target "
                         "transcripts (FDR < 0.01) (Tables S2A-S2C)'); extract/tableS2A_842_targets.tsv by s_extract.py -- the "
                         "near-miss view's FMRP comparator (v6.7 N7)",
                         ["https://pmc.ncbi.nlm.nih.gov/articles/instance/3232425/bin/NIHMS314927-supplement-Suppl_Table_S2A-C.xls",
                          "https://pmc.ncbi.nlm.nih.gov/articles/PMC3232425/"], F66_, PMC_LIC),
    "pagani2026_text": ("Pagani et al. 2026 (Nat Neurosci; PMC13246445): the Europe PMC full-text XML, read for the wording of "
                        "its module sets ('co-expression modules of known biological function (n = 10)'; 'vesicle transport and "
                        "release', 'synaptic vesicles and plasticity') -- the near-miss view's evidence (v6.7 N6); no "
                        "supplement, map or source data",
                        ["https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13246445/fullTextXML"], F66_,
                        "CC BY 4.0 (open access article)"),
    "romerogarcia2019_article": ("Romero-Garcia et al. 2019, Mol Psychiatry 24:1053 (PMC6755982): the article PDF, for the "
                                 "verbatim location of the printed size '500' (register 1.6, v6.6 C1: p. 1056, Materials and methods, "
                                 "'Genetic modules and enrichment analyses')",
                                 ["https://pmc.ncbi.nlm.nih.gov/articles/PMC6755982/pdf/41380_2018_Article_23.pdf"],
                                 "fetched 2026-09-27 with fetch_util.get (plain curl; no identifier sent)",
                                 "CC BY 4.0 (open access article)"),
}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


V68_R2 = (". v6.8 round 2 (the orchestrator under the operator's standing delegation; one rule for every flagged workbook a "
          "register builder reads): %s reduced by reduce_v68.py to exactly the sheets and columns the builders read, the builders' "
          "outputs shown byte-identical, and the original deleted -- its sha256, bytes and sheet names + dimensions in the table "
          "below, in extract_manifest.json and in register 1.6")
V68_NOTES = {
    "gandal2018_science362": V68_R2 % "Table S1 (DGE's four columns kept)",
    "polioudakis2019": V68_R2 % "Table S4 ('Cluster enriched genes', its first three columns kept)",
    "satterstrom2020": V68_R2 % "Table S2 (sheet '102_ASD', its columns 'gene' and 'ensembl_gene_id' kept)",
    "lake2018": V68_R2 % ("MOESM11 (Table S3's 'All Clusters' gene and cluster columns kept); the copy in "
                          "E:\\data\\asdg\\explore_public\\celltype_lake2018\\journal_esm was reduced by the same rule in v6.9 "
                          "(to what the exploration scripts read: Table S3's seven blocks and the sheet names) and deleted, "
                          "its exploration summaries shown byte-identical"),
    "gandal2022_nature611": V68_R2 % ("MOESM7 (Gene_Level's four columns kept) and MOESM8 (GeneModules' module name and ASD "
                                      "FDR / logFC columns kept)"),
    "sanders2019_rgd": V68_R2 % "the Tables S1 / S2 / S4 workbook (sheet 'S1 single gene RGDs', its seven flag / id columns kept)",
    "pfenning2014_vocal": V68_R2 % "the Tables S1-S8 zip (the builders read its workbooks' sheet names only; the names kept)",
    "voineagu2011": (". v6.8 round 2: extract/table14_M12_genes.tsv rewritten by s_extract.py with text_order 1 ... 380 (v6.7 "
                     "numbered 1, 3, 5 ... per page; gene column unchanged); Supplementary Table 2 is left whole -- no builder "
                     "reads it (sha256 only)"),
}


def main(only=None) -> None:
    """only: write the SOURCE.md of these folders alone (register v6: fetch_v6.py); the index is always rewritten."""
    for folder, (desc, urls, when, lic) in META.items():
        if only is not None and folder not in only:
            continue
        desc = desc + V68_NOTES.get(folder, "")
        d = SRC / folder
        assert d.is_dir(), d
        files = sorted(p for p in d.rglob("*") if p.is_file() and p.name != "SOURCE.md")
        lines = [f"# SOURCE: {folder}", "", f"- **description**: {desc}", "- **url(s)**:"]
        lines += [f"  - {u}" for u in urls]
        lines += [f"- **date / how**: {when}", f"- **licence**: {lic}",
                  "- **used by**: arcs/audit/src_register/s_build.py (register §1.6 pre-freeze S-build); every file below "
                  "is asserted by sha256 before use", "", "## Files", "", "| sha256 | bytes | path |", "|---|---:|---|"]
        lines += [f"| {sha(p)} | {p.stat().st_size} | {p.relative_to(d).as_posix()} |" for p in files]
        red = sorted(d.rglob("*.reduced_v68.json"))  # register v6.8 (B S2): originals deleted after their reduction
        if red:
            lines += ["", "## Originals deleted for privacy (register v6.8, B S2; reduce_v68.py)", "",
                      "| file | sha256 | bytes | present | sheets (name: rows x columns, guard) | kept -> reduction |",
                      "|---|---|---:|---|---|---|"]
            for rp in red:
                import json as _json
                rec = _json.loads(rp.read_text(encoding="utf-8"))
                o = rec["original"]
                sh = "; ".join("%s%s: %s x %s, %s" % ((s["member"] + " :: ") if s.get("member") else "", s["sheet"].strip(),
                                                      s["n_rows"], s["n_cols"], s["guard"]) for s in o["sheets"])
                kept = "; ".join("%s (%d rows, columns %s of %d)" % (k["sheet"], k["n_rows"], k["columns_kept"], k["n_cols_original"])
                                 for k in rec["kept"])
                if "zip_sheet_names" in rec:
                    kept = "the sheet names of its %d workbooks (no cell)" % len(rec["zip_sheet_names"])
                lines.append(f"| {o['file']} | {o['sha256']} | {o['bytes']} | {'yes' if (d / o['file']).exists() else 'no (deleted)'} "
                             f"| {sh} | {kept} -> {rp.relative_to(d).as_posix()} |")
        txt = "\n".join(lines) + "\n"
        (d / "SOURCE.md").write_text(txt, encoding="utf-8", newline="\n")
        assert (d / "SOURCE.md").read_text(encoding="utf-8") == txt
        print(folder, len(files), "files")
    idx = ["# register_sets_src - sources of the A1 pre-freeze S-build (register §1.6)", "",
           "One folder per source, each with its SOURCE.md (URL, date, sha256, licence). Builder: "
           "arcs/audit/src_register/s_extract.py (stage 1, system Python) and s_build.py (stage 2, programme venv). "
           "extract_manifest.json = stage-1 outputs and their hashes.", ""]
    idx += [f"- `{k}/` - {v[0][:150]}" for k, v in META.items()]
    (SRC / "SOURCE.md").write_text("\n".join(idx) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
