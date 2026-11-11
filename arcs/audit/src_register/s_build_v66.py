"""A1 pre-freeze S-build, register DRAFT v6.6 (B2 / C5 of the orchestrator under the operator's standing delegation,
2026-09-27): the comparators of Buch's non-GO sets (Fig. 5c-e, 24 sets x 4 subgroups) and of Pagani's twelve sets, built
before the freeze by register section 1.6's resolution rule R-a ... R-e -- written into the register at
2026-09-27T02:56:44Z (rule text sha256 RULE_SHA), before any comparator source was downloaded (fetch_v66.py; v6.7 N5: the
target paper's own manuscript, buch2023_aam.pdf, was fetched at 02:52:40Z, before the rule; the first comparator source
at 03:21:39Z; self-attested, one commit) -- and its application notes (register 1.6, v6.6). Called by s_build.py (main);
no map and no gated carrier is read.

Register DRAFT v6.7 (the orchestrator under the operator's standing delegation, 2026-09-27; the rule text unchanged):
  N1   asdM12 is built from Voineagu 2011's Supplementary Table 14 (the M12 module genes; s_extract.py, the PDF deleted
       for privacy); asdM16 stays not buildable (no printed M16 / tan table);
  (2)  the uniform archive rule: every cell ruled 'no archived release' / 'release substituted' for want of an archive is
       re-examined in the Wayback Machine -- RGD (2024-07-24 capture), CTD (2024-02-10 capture); SFARI read by the SERVED
       RELEASE LABEL (N2, a post hoc clarification: the state current at the date is the most recent capture at or before
       it whose served release is the release current at the date);
  (1)  a registered SECONDARY VIEW, 'near-miss comparator' (NEAR_MISS_LABEL): per cell without a buildable comparator, a
       comparator from a near-miss source (not the cited reference) or reached by a declared name normalisation; built as
       sets with no primary cells (the view's cells in 'secondary_view_cells'); it never changes a primary status;
  N7 / N6 / N4  FMRP's near miss from Darnell 2011 Table S2A; PAG-C9 / C10's from Gandal 2022's text; vocal learning by
       Pfenning 2014's Tables S1-S8 (obtained by a browser; R-e on their contents);
  N8 / N9 / N11  declarations (very wide comparators; Pua's counts) and literal sha256 asserts (CTD, Grove).

Register DRAFT v6.8 (the orchestrator under the operator's standing delegation, 2026-09-29, on the v6.7 final re-check 0 A / 2 B /
4 C; every item decided after that outcome was seen -- post hoc, declared):
  B S1 R-d applied uniformly: 'asdM12' reaches Voineagu's M12 only through Parikshak 2013's name (not cited by Buch for the set),
       so BUCH-E-ASDdown-S1 ... S4 are not auditable in the primary view (comparator not buildable pre-freeze) and asdM12's set
       (Voineagu's Table 14, kept built and pinned, now nm68_buch_voineagu2011_M12_table14) is their near-miss comparator;
  B S2 every workbook sheet read passes privacy_guard.py (GeneModules of Gandal 2022 MOESM8 is wider than 50 columns: its
       declared columns only); SynGO's genes.xlsx through the guard; Pfenning's workbooks: sheet names only;
  C    the HGNC overlap of Table 14 with Parikshak 2013's asdM12 and its V-AAL Jaccard recomputed; Table 14's 380 vs p. 10's 432
       and the extract's text_order defect declared; CTD's archive alternative computed; PAG-C9 / C10's modules found by a
       content-word search with a uniqueness assert (content_word_search).
Register DRAFT v6.9 (the orchestrator's skeptic re-check 0 A / 2 B / 5 C, under the operator's standing delegation, 2026-09-30;
post hoc, declared):
  C3   NEAR_MISS_LABEL adds '/ name bridge' (the ASDdown comparator is Voineagu's own list reached through a name bridge);
       v6.10: and '/ note reading' (RDNV's column note; PAG-C9 / C10's Results text); v6.11: PAG-C9 / C10's near-miss
       records describe that route (their reading and R-a_source), no longer 'a near-miss NAME source';
  C5   reading (iii) applied uniformly: Sanders 2019 Table S1 presents several gene flags and names none 'rare de novo', ASD65
       was reached by a semantic reading of its column note -- BUCH-E-RDNV-S1 ... S4 (descriptor cells) are not auditable in
       the primary view and the same 65 genes (nm69_buch_sanders2019_asd65) are their near-miss comparator; m and m' unchanged.

Each Buch token / Pagani cell gets ONE outcome:
  built          a per-set JSON (status COMP_STATUS): the else-branch S of its cells, and the pinned comparator of
                 corroboration (a) (carrier_tests.json cells[<id>].corroboration: set id + sha256);
  not buildable  status NOT_BUILDABLE: its cells read "not auditable (S undefined: comparator not buildable pre-freeze)"
                 and their corroboration mode is none.
Every set records its source, URL, release / version and the rule's outcome for it (R-b), its threshold (R-c), the
names the paper gives it and the name rule's record (R-d), the access date and every input's sha256.
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import re
import tarfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl

import privacy_guard as G  # register v6.8 (B S2): every workbook sheet read passes the guard (s_build.py puts this folder on sys.path)
import reduce_v68 as RV  # register v6.8 round 2: the workbooks reduced to what the builders read (their originals deleted)

RULE_SHA ="43cefdcc81bee3cecb1d764150f9a6d39bf814f98525fd65006a4c0bbd3fa1a1"
RULE_UTC = "2026-09-27T02:56:44Z"
ACCESS = "2026-09-27"
COMP_STATUS = ("built (comparator, v6.6: the else-branch S and the pinned set of corroboration (a); source 1 in the gated "
               "carrier is checked first, under G1)")
NOT_BUILDABLE = "not auditable (S undefined: comparator not buildable pre-freeze)"
# register v6.7 (1); v6.9 (C3): '/ name bridge' added (v6.8's ASDdown comparator reaches Voineagu's list by a name bridge);
# v6.10 (C3 / C5): '/ note reading' added (a list of the cited source reached through a note or its text, not its title or
# printed label: RDNV's ASD65 by its column note; PAG-C9 / C10's modules by Gandal's Results text)
NEAR_MISS_LABEL = ("comparator from a near-miss source (not the cited reference) / normalised name / name bridge / "
                   "note reading")
NM_STATUS = ("built (near-miss view, v6.7: %s; a registered SECONDARY view only -- no primary cell uses this set)"
             % NEAR_MISS_LABEL)
NORMALISE_V67 = {  # register v6.7 (1): the declared name normalisation, applied to these two names ONLY
    "CNSauto": ("expand 'CNS' to 'central nervous system'", lambda s: re.sub(r"\bCNS\b", "central nervous system", s)),
    "TS": ("strip the possessive \"'s\"", lambda s: re.sub(r"'s\b", "", s))}
SRC = Path(r"E:\data\asdg\register_sets_src")
ROOT = Path(__file__).resolve().parents[3]
BUCH_D, PAGANI_D = "2021-11-29", "2025-04-17"  # the 'Received' dates the articles print (R-b)

PIN66 = {
    "parikshak2013_s1d": (SRC / "parikshak2013" / "extract" / "tableS1D_gene_lists.tsv",
                          "82a20c51c061d8b32c29cc5761e13b336ac13fb33dad2a094ed049c95834b017"),
    "voineagu2011_s2": (SRC / "voineagu2011" / "NIHMS313080-supplement-2.xls",
                        "d8030112218aa69216f0429a522d90399b44b861e47bf92953726cfc8513f83a"),
    "parikshak2016_s4": (SRC / "parikshak2016" / "NIHMS1050915-supplement-SuppTable4.xlsx",
                         "7e672596530a7cae6430511e1703e9ebf9e51eaf87c83325fbe5598f41a05578"),
    "steinberg2013_mmc1": (SRC / "steinberg2013_fmrp" / "mmc1.pdf",
                           "4d335bd0da3e8804560ae1642c01d4027e05c28e2429b95a452e9be2aa2e8e3c"),
    "spark_pdf": (SRC / "spark2018" / "SPARK_gene_list.pdf",
                  "16c6b1c170511bf050e73b047cd149e51e639b2db95a9963c8997ddc0c77ee76"),
    "spark_cdx_s3": (SRC / "spark2018" / "cdx_spark-sf_s3.json",
                     "b3f68aba3281e8817b2912062f0ae5a695d38ab83ab963d9add841c0c5dc4f8f"),
    "spark_cdx_site": (SRC / "spark2018" / "cdx_sparkforautism.json",
                       "656dc77c2bfbd866ccf11d2021e85239d34d301f10b5fca8f2766b94eb8bceae"),
    "x_spark": (SRC / "spark2018" / "extract" / "spark_single_genes.tsv",
                "4af14ca2074109b84371468db9d3f8ac40d519f604f77aae84626a3e3d3baab7"),
    "sanders2019_flags": (SRC / "sanders2019_rgd" / "extract" / "table_s1_flags.tsv",
                          "c5792cf57dfa8c38803c15df6b50110cf054ea107cb2f828f1394c94c3ebcb08"),
    "sanders2019_xlsx": (SRC / "sanders2019_rgd" / "NIHMS1754502-supplement-Tables_S1__S2__S4.xlsx",
                         "9848de1d41925218a090f4275f91f20d170d1fd9fd7dd1cf258b484ca37045a1"),
    "nair2009_html": (SRC / "nair2009_psoriasis" / "PMC2745122.html",
                      "86064dc9cd427c52c5c94df978ba89b2689336241aba0c9518bff3a04aaa8de4"),
    "nair2009_supp": (SRC / "nair2009_psoriasis" / "NIHMS83342-supplement-1.pdf",
                      "00067a4800987d4cb47f4fd8637d291a903dc1163a5a84f7befe49aa360280c0"),
    "pfenning2014_supp": (SRC / "pfenning2014_vocal" / "NIHMS666880-supplement-Supplemental_material.pdf",
                          "8c41e7c42657e39e9529d74bde8ecc70319576dfc4a7aa6fd6bed4b3384a9c4a"),
    "pua2016_st1": (SRC / "pua2016_cardiac" / "extract" / "st1_gene_list.tsv",
                    "a30bea013ce4e5a94afcaa663194c5aec621ad2f12d7d911b482d6e531ec8070"),
    "sfari_20220124": (SRC / "sfari_wayback_2022-01-24" / "SFARI-Gene_genes_capture_20220124104055.csv",
                       "243f622811940b18db900a079d34dccc6f32d08d6adb5ea3334c9dd34bb44714"),
    "sfari_cdx": (SRC / "sfari_wayback_2022-01-24" / "cdx_sfari_genes_csv.json",
                  "31ebe78ed27d0fc9338bffa24d0ab94c42c61b81dcf33c4921f32f7cf770c902"),
    "diseases_knowledge": (SRC / "diseases_v2_2022-02-09" / "human_disease_knowledge_filtered.tsv.gz",
                           "1bbc88fdefefd5c0b3643d8cb7f0594015e3e899c332f8ef2cd360941c21ec9a"),
    "diseases_experiments": (SRC / "diseases_v2_2022-02-09" / "human_disease_experiments_filtered.tsv.gz",
                             "a20892ce3fd30f856a3b14d63785620e55920117d9966aa29d91e95550fc90f4"),
    "diseases_textmining": (SRC / "diseases_v2_2022-02-09" / "human_disease_textmining_filtered.tsv.gz",
                            "a567aa9159e9aaa9b0dac1d77cd1c7f08076d9ae89ed06c53428d58b0b014e24"),
    "diseases_dictionary": (SRC / "diseases_v2_2022-02-09" / "diseases_dictionary.tar.gz",
                            "66154a233d48455b21605294bdc135e9b6327b7358b09ec65e117beb1cc25fba"),
    "diseases_cdx_knowledge": (SRC / "diseases_v2_2022-02-09" / "cdx_knowledge_filtered.json",
                               "a5c2d4de370d02d4809daad567a172946cbef436b41f903423175f69b6d4bc41"),
    "diseases_cdx_experiments": (SRC / "diseases_v2_2022-02-09" / "cdx_experiments_filtered.json",
                                 "bf4bf2f15c35ad92941a744a8624f67b1108de5964e2378628342bc3f8c0b712"),
    "diseases_cdx_textmining": (SRC / "diseases_v2_2022-02-09" / "cdx_textmining_filtered.json",
                                "7f22a4616564889ecf6095e6c0dc5bfc3c25956f19b8ff8519efa427b4b9e377"),
    # register v6.7 (2), the uniform archive rule: RGD's annotations as captured 2024-07-24 (+ its own weekly RDO archive),
    # CTD's report of 2024-01-31 as captured 2024-02-10 (literal sha256 of the 2.7 GB file asserted, N11)
    "rgd_ann_20240724": (SRC / "rgd_wayback_2024-07-24" / "homo_genes_rdo",
                         "d64b8ea7ec1eacd4997f77a0332c92a0d3fbc1b3983e5de4588780fb786cd83c"),
    "rgd_rdo_20240720": (SRC / "rgd_wayback_2024-07-24" / "extract" / "RDO_20240720_v1.283.obo",
                         "808671d49b5d17c05c64a822f7e703e48232b01f3c2e651df654e9a7c00e0d27"),
    "rgd_rdo_20240720_gz": (SRC / "rgd_wayback_2024-07-24" / "RDO_20240720_v1.283.obo.gz",
                            "eb2a299f090abf4df7d20e3cf1ffabba65523369220d71feeccc352db15d9847"),
    "rgd_cdx": (SRC / "rgd_wayback_2024-07-24" / "cdx_homo_genes_rdo.json",
                "21c640388a0dec9eca67a61470629d8d033cd051da0558fd08be795913f24633"),
    "rgd_capture_lengths": (SRC / "rgd_wayback_2024-07-24" / "capture_lengths.json",
                            "43ffe0efd48b7e691bc8bc8fd14bb58fe6c811f5574a97618637318d9c55ed69"),
    "ctd_gd_20240210": (SRC / "ctd_wayback_2024-02-10" / "CTD_genes_diseases.tsv.gz",
                        "b4be217d9f302ed3347b9d191b675ce6fdddddd1256a019600f9114245903c76"),
    "ctd_obo_20240210": (SRC / "ctd_wayback_2024-02-10" / "extract" / "CTD_diseases.obo",
                         "873afd9a087027a2073e2c5d8328b7b726ac1909a0d36403b4f98b3ce750290e"),
    "ctd_obo_20240210_gz": (SRC / "ctd_wayback_2024-02-10" / "CTD_diseases.obo.gz",
                            "0729bae41982b1aec42ad4793baf64ebbaef025f257b317c73554b73ad3bc001"),
    "ctd_sz_rows_20240210": (SRC / "ctd_wayback_2024-02-10" / "extract" / "schizophrenia_rows.tsv",
                             "8e3a86ba497ef507c467a1fda6cff8cbe4852bcf67caa34e2fb73ac5a003cf2e"),
    "ctd_cdx_gd_tsv": (SRC / "ctd_wayback_2024-02-10" / "cdx_CTD_genes_diseases_tsv_gz.json",
                       "e86c4d31f48d87fd0559ade32a22b33aeda8fcde27c9df414bbdfb6ad407ae4b"),
    "ctd_cdx_gd_csv": (SRC / "ctd_wayback_2024-02-10" / "cdx_CTD_genes_diseases_csv_gz.json",
                       "97db4fb74e44194f946efadda5258aa6299d60c92b6564c65837c3c80820bcb7"),
    "ctd_cdx_gd_xml": (SRC / "ctd_wayback_2024-02-10" / "cdx_CTD_genes_diseases_xml_gz.json",
                       "7b456f79eb22d494260f6e2d6453935f9a2d8e497747e279f0a3fef6b997b7ef"),
    "ctd_cdx_d_tsv": (SRC / "ctd_wayback_2024-02-10" / "cdx_CTD_diseases_tsv_gz.json",
                      "c0f26e0eb8018eec1147b21a006a25227ed9b77641442356cab0a23c6a211848"),
    "ctd_cdx_d_csv": (SRC / "ctd_wayback_2024-02-10" / "cdx_CTD_diseases_csv_gz.json",
                      "d8b5c114c14ae53f9b77306bd3a78d0c7eb5721e79e45909e537dc8804205846"),
    "ctd_cdx_d_xml": (SRC / "ctd_wayback_2024-02-10" / "cdx_CTD_diseases_xml_gz.json",
                      "cb492c933273c054f82b2566b690bd9052b2c7241c4d8c231398b2e70a0054fd"),
    "ctd_cdx_d_obo": (SRC / "ctd_wayback_2024-02-10" / "cdx_CTD_diseases_obo_gz.json",
                      "70c834e34805cd7cc71e2c290e8ba823ec82bf728d594d718d597ad3e0369943"),
    # N11: the Grove PDF by its literal sha256 (R-e's evidence)
    "grove_pdf": (SRC / "grove2019_magma" / "41588_2019_344_MOESM1_ESM.pdf",
                  "0de06bc6576481404a98e11702872620f924231e4dbfc1f04bf910a5e6b151e7"),
    # N1: Voineagu's Supplementary Table 14 (extract; the SI PDF deleted, its sha256 kept in VOINEAGU_SI_SHA) and the article
    "voineagu2011_t14": (SRC / "voineagu2011" / "extract" / "table14_M12_genes.tsv",
                         "b7bdefacaae389406669e8d92f2a47566edc42a67ed8519c80ddc10ad53e5d82"),  # v6.8: text_order 1 ... 380
    "voineagu2011_html": (SRC / "voineagu2011" / "PMC3607626.html",
                          "20396beb644b85ca2da27a71d905dd93eb976fd9e42b3d08b1425463f03a0eec"),
    # (1) the near-miss view's evidence: Parikshak 2013 (the 'asdM12' / 'asdM16' names), Darnell 2011 (N7), Gandal 2022's text
    # and Pagani's (N6), SFARI's served labels (N2), Pfenning's tables (N4)
    "parikshak2013_html": (SRC / "parikshak2013" / "PMC3934107.html",
                           "7afe6a87955740167737d7f41a916b8004e7070b8ece932ac955c739faadab8e"),
    "parikshak2013_supp01": (SRC / "parikshak2013" / "NIHMS545068-supplement-01.pdf",
                             "b4eba2e965430696cdc8d1d00be190759ecc2e5e0adafe30c7f913b18ba57feb"),
    "darnell2011_s2a": (SRC / "darnell2011_fmrp" / "extract" / "tableS2A_842_targets.tsv",
                        "4b0918f7acab2eb422346b3cc09ad096aa7ea5fa8201044fa2cc96b23e5674b3"),
    "darnell2011_xls": (SRC / "darnell2011_fmrp" / "NIHMS314927-supplement-Suppl_Table_S2A-C.xls",
                        "30495d3d31e8bdf513cc45b222312dcf71652247b962a17198f256c70521cafb"),
    "darnell2011_html": (SRC / "darnell2011_fmrp" / "PMC3232425.html",
                         "21d1c20ec04fdc840471a11a340ddad8db9a921a1cb1b2b15b325d873f8cf9fa"),
    "gandal2022_html": (SRC / "gandal2022_nature611" / "PMC9668748.html",
                        "4d165e681745c285aceb67e3a8fb39560ddb288fc7f1b57c3f2ea549600d53ff"),
    "pagani_text": (SRC / "pagani2026_text" / "PMC13246445_fullTextXML.xml",
                    "191247e42ebf7e7971a9214e842635099a8f806a642e0df911aed52d3c9f7ec8"),
    "sfari_labels": (SRC / "sfari_wayback_captures" / "served_labels.json",
                     "8c74b895630f95f31aa8b3bb6fda62f3ce149f9da1b3d5b5490e4f6c1488bab3"),
    "sfari_20211022": (SRC / "sfari_wayback_captures" / "SFARI-Gene_genes_capture_20211022034409.csv",
                       "68a98e1f69076f4996eedd0db4e7ca20c8a7eac3a9c4f6d395be33a78466583d"),
    "pfenning2014_zip": (SRC / "pfenning2014_vocal" / "science_download" / "pfenning-tables-s1-to-s8.zip",
                         "9a7037b135e9848cc342b74d1ff3d8791782fc3e397e1926ff159ae570da616f"),
    "gandal2022_modules": (SRC / "gandal2022_nature611" / "extract" / "gene_level_modules.tsv",
                           "ebeaaf745e32ff9a75642a70b911f11b4ae36a914c19db2f7965ed9bd6026857"),
    "gandal2022_moesm7": (SRC / "gandal2022_nature611" / "41586_2022_5377_MOESM7_ESM.xlsx",
                          "a48802c835c07e872bf3f30730a304bc62e3fd60782ef80b7e1df5b78d4c03e5"),
    "gandal2022_moesm8": (SRC / "gandal2022_nature611" / "41586_2022_5377_MOESM8_ESM.xlsx",
                          "d746b3ed5336987c5e2b1415b5ccd7ac42d4bef57b06222d87fdd7691ef3d22f"),
    "gandal2022_labels": (ROOT / "arcs" / "audit" / "register_maps" / "gandal2022_module_labels.json", None),
    "reactome92_gmt": (SRC / "reactome_v92" / "ReactomePathways.gmt.zip",
                       "023760f44afd73f5f99030c55c2c10690aee979284af36b34ba43286e1b8d0fc"),
    "reactome92_txt": (SRC / "reactome_v92" / "ReactomePathways.txt",
                       "80d79741501ab164402e9ce64abab880fc7f4fe0473950d9a19109ec74ca87b0"),
    "syngo12_zip": (SRC / "syngo_1.2_20231201" / "syngo1.2_complete_data.zip",
                    "9adbccea59da4c66d77696c71bb4b383fcd89e8a0d4dde0c5d1a389d0e57b4ba"),
    "syngo_portal_20250406": (SRC / "syngo_1.2_20231201" / "portal_capture_20250406180025.html",
                              "7942988cece924fcf46791e5f606c543629431c1bcb19d1e03a568c0ac404399"),
    "syngo_portal_20251118": (SRC / "syngo_1.2_20231201" / "portal_capture_20251118230922.html",
                              "bad98d583c105ef13ce7ce1f8b58a0d0f0140cb6a42fd6a979ec5b1bad979465"),
}
PMC = "https://pmc.ncbi.nlm.nih.gov/articles/instance/%s/bin/%s"
VOINEAGU_SI_SHA = "59f2ded45c95b73af0f4c0152da530f2196d0b8e371ca7897d5444c4c6f9cfd5"  # N1: deleted after its extract (privacy)
PARIKSHAK13_S03_SHA = "c12bc55c9f5f22cf6899555de8ae99ecf8a65245a1c0c8fbf2ad2dcf94a2062b"  # deleted after its extract (v6.6)
PUA_ESM1_SHA = "6a3c322a81aa7fce36c533d6997ff7efa23c3038b63c4b5f2cdd42479caf902f"  # deleted after its extract (v6.6)
SFARI_CSV = "https://gene.sfari.org/wp-content/themes/sfari-gene/utilities/download-csv.php?api-endpoint=genes"


# register v6.8 round 2 (the orchestrator under the operator's standing delegation): PIN66 keys whose original workbook was
# reduced to what the builders read and deleted -> (reduce_v68 key, the reduction's sha256); ctx.pinned asserts the reduction and
# the original's sha256 it records (PIN66's); ctx.ref keeps naming the original by path and sha256 (the published file)
REDUCED66 = {
    "gandal2022_moesm7": ("gandal2022_moesm7", "bb5369c3b650acf87bbca5a6927744fd65d07c9931b1032ac625501b0c3930f2"),
    "gandal2022_moesm8": ("gandal2022_moesm8", "63e7f9c9493208b453f1eabf723b5dfa49ec0e33991fa4daebd0ca5833650876"),
    "sanders2019_xlsx": ("sanders2019", "50cf17b799b243e3d64ad7be64c636e74ad4bd350219fc8da1d54e60ab4121da"),
    "pfenning2014_zip": ("pfenning2014", "1ab2a57cea026371f9fc1549a976fd84d9fe20cd3ad5002e4c484a792bb904bc"),
}


class Ctx:
    """what s_build.main hands over: the HGNC reader, the set / status / name-record callbacks, the TSV rows."""

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def pinned(self, key: str) -> Path:
        if key in REDUCED66:  # v6.8 round 2: the reduction, and its record of the original (PIN66's sha256)
            rk, rh = REDUCED66[key]
            RV.load(RV.reduced_path(rk), rh, PIN66[key][1])
            return RV.reduced_path(rk)
        p, h = PIN66[key]
        if h is None:
            return p
        got = self.sha256(p)
        assert got == h, f"{key}: sha256 {got} != pinned {h} ({p})"
        return p

    def reduction(self, key: str) -> dict:
        rk, rh = REDUCED66[key]
        return RV.load(RV.reduced_path(rk), rh, PIN66[key][1])

    def sheet_rows(self, key: str, sheet: str, declared=None, header_row=None, label: str = "") -> list[tuple]:
        """a pinned workbook's sheet through the privacy guard -- its reduction's rows (original column positions) if reduced."""
        if key in REDUCED66:
            return RV.rows(self.reduction(key), sheet, declared, header_row, label or key)
        wb = openpyxl.load_workbook(self.pinned(key), read_only=True, data_only=True)
        out = G.read_openpyxl(wb[sheet], declared, header_row, label or key)
        wb.close()
        return out

    def ref(self, *keys: str) -> list[dict]:
        return [{"path": self.relpath(PIN66[k][0]), "sha256": PIN66[k][1] or self.sha256(PIN66[k][0])} for k in keys]


def _tsv(p: Path) -> list[dict]:
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def _sheet_cells(p: Path) -> dict:
    """(row, col) -> text of a fetch_v66 sheet extract."""
    return {(int(r["row"]), int(r["col"])): r["text"] for r in _tsv(p)}


def _cdx(p: Path) -> list[dict]:
    rows = json.loads(p.read_text(encoding="utf-8"))
    hdr = rows[0]
    return [dict(zip(hdr, r)) for r in rows[1:]]


def release_by_captures(caps: list[dict], d: str) -> dict:
    """register 1.6 v6.6 application of R-b to web-archive captures: a capture on or before the date shows the release
    current at the date only if a capture on or after it has the same content digest (the release spans the date);
    otherwise the earliest capture after the date is 'the earliest archived release after that date'."""
    dd = d.replace("-", "")
    caps = sorted((c for c in caps if c.get("statuscode") == "200"), key=lambda c: c["timestamp"])
    before = [c for c in caps if c["timestamp"][:8] <= dd]
    after = [c for c in caps if c["timestamp"][:8] >= dd]
    out = {"date": d, "last_capture_on_or_before": before[-1]["timestamp"] if before else None,
           "first_capture_on_or_after": after[0]["timestamp"] if after else None}
    if before and after and before[-1]["digest"] == after[0]["digest"]:
        out.update(outcome="release current at the date (bracketing captures, identical content digest %s)"
                   % before[-1]["digest"], digest=before[-1]["digest"], bracketed=True)
    elif after:
        out.update(outcome="earliest archived release after the date (capture %s; the capture before it differs)"
                   % after[0]["timestamp"], digest=after[0]["digest"], bracketed=False)
    else:
        out.update(outcome="no capture after the date", digest=None, bracketed=False)
    return out


def _day(ts: str) -> str:
    return "%s-%s-%s" % (ts[:4], ts[4:6], ts[6:8])


def sfari_states(labels: dict, current: dict | None = None) -> list[dict]:
    """register v6.7 N2: the SFARI Gene states the archive (and the current download) holds -- one per capture, each with the
    release its served label names, its export date and its content digest; sorted by capture date."""
    st = [{"capture": ts, "day": _day(ts), "release": v["release"], "export": v["export"], "digest": v["digest"],
           "served_file_name": v["served_file_name"]} for ts, v in sorted(labels.items())]
    if current:
        st.append(dict(current))
    return sorted(st, key=lambda s: (s["day"], s["capture"]))


def release_by_labels(states: list[dict], d: str) -> dict:
    """register v6.7 N2 -- a clarification of R-b reading (i) made after the v6.6 build (post hoc: known which cells it
    affects; no carrier or result seen): where the source serves a release label, R-b reads the SERVED RELEASE LABEL, not
    the content digest alone. The release current at the date is the latest release the labels name with a release date on
    or before it; the comparator is the STATE current at the date: the most recent capture at or before the date that serves
    that release (else, none archived, the earliest state after the date serving it: 'state substituted')."""
    rel = sorted({s["release"] for s in states})
    cur = [r for r in rel if r <= d]
    if not cur:
        return {"date": d, "outcome": "no release on or before the date is named by any label", "release": None, "state": None}
    r0 = cur[-1]
    on = [s for s in states if s["release"] == r0 and s["day"] <= d]
    later = [s for s in states if s["release"] == r0 and s["day"] > d]
    nxt = [r for r in rel if r > d]
    out = {"date": d, "release_current_at_date": r0, "next_release_named": nxt[0] if nxt else None,
           "states_of_that_release": [s["capture"] for s in states if s["release"] == r0]}
    if on:
        out.update(state=on[-1], substituted=False,
                   outcome=("release %s current at the date (the next release the labels name is %s); its state at the date: "
                            "the most recent capture at or before it serving that release, %s (export %s)"
                            % (r0, out["next_release_named"], on[-1]["capture"], on[-1]["export"])))
    else:
        out.update(state=later[0] if later else None, substituted=True,
                   outcome=("release %s current at the date; no archived state of it at or before the date -- state "
                            "substituted: %s (export %s)" % (r0, later[0]["capture"], later[0]["export"])) if later else
                   "release %s current at the date; no state of it obtainable" % r0)
    return out


def names_rule(NM, names: list[str], cands: list[dict]) -> tuple:
    """register 1.6 v6.6 application of R-d: every name the paper gives the set (the Methods' 'Gene set lists' name and
    the figure's row label) is tried by the name rule; the set is named iff at least one reaches a term and all that
    reach one reach the same term. Returns (term id or None, the chosen record, all records, why)."""
    recs = [NM.match(n, cands) for n in names]
    ids = sorted({r["id"] for r in recs if r["id"]})
    if len(ids) == 1:
        chosen = next(r for r in recs if r["id"] == ids[0])
        return ids[0], chosen, recs, None
    if not ids:
        return None, recs[0], recs, "no name the paper gives reaches a term of the source by the name rule"
    return None, recs[0], recs, "the paper's names reach different terms (%s)" % ", ".join(ids)


def _rec_short(NM, r: dict) -> dict:
    return {"query": r["query"], "tier": r["tier"], "id": r["id"], "name": r["name"], "label": r["label"],
            "summary": NM.label_short(r)}


# --------------------------------------------------------------------------------------------- the Buch token table
# (token, Methods 'Gene set lists' name, Fig. 5 row label as printed, reference as the Methods cite it)
BUCH = [
    ("ASDdown", "ASD transcriptionally downregulated (asdM12 from 118) extracted from 119", "ASD downregulated", "118, 119"),
    ("ASDup", "ASD transcriptionally upregulated (asdM16 from 118) extracted from 119", "ASD upregulated", "118, 119"),
    ("FMRP", "FMRP-interacting", "FMRP-interacting", "122"),
    ("SFARIsyn", "Simons Foundation Autism Research Initiative (syndromic SFARI)", "Syndromic (SFARI)", "125"),
    ("SPARK", "ASD SPARK", "ASD SPARK", "121"),
    ("RDNV", "ASD rare de novo", "ASD RDNV", "120"),
    ("Grove", "Grove et. al, ASD common variants", "ASD Grove et al.", "19"),
    ("CNSauto", "CNS autoimmune", "CNS autoimmune", "129"),
    ("Osteo", "osteoarthritis", "Osteoarthritis", "129"),
    ("MSA", "multiple system atrophy", "MSA", "129"),
    ("Dementia", "dementia", "Dementia", "129"),
    ("HeartDisease", "heart disease", "Heart disease", "127"),
    ("Psoriasis", "psoriasis", "Psoriasis", "124"),
    ("Vocal", "vocal learning", "Vocal learning", "61"),
    ("ADHD", "ADHD", "ADHD", "128"),
    ("TS", "Tourette's syndrome", "Tourette's", "128"),
    ("SZ", "schizophrenia", "Schizophrenia", "126"),
    ("MDD", "Major Depressive Disorder", "MDD", "128"),
    ("GAD", "Generalized Anxiety Disorder", "GAD", "128"),
    ("ID", "intellectual disability (\"ID All\")", "ID", "123"),
    ("Aphasia", "aphasia", "Aphasia", "128"),
    ("ConductDisorder", "conduct disorder", "Conduct disorder", "128"),
    ("AntisocialPD", "antisocial personality disorder", "Antisocial PD", "128"),
    ("NeuroticDisorder", "neurotic disorder", "Neurotic disorder", "128"),
]
BUCH_REFS = {  # the Methods' references (the accepted manuscript's list, pp. 35-37)
    "19": "Grove et al. 2019, Nat Genet 51:431", "61": "Pfenning et al. 2014, Science 346:1256846",
    "118": "Voineagu et al. 2011, Nature 474:380", "119": "Parikshak et al. 2016, Nature 540:423",
    "120": "Sanders et al. 2019, Nat Med 25:1477", "121": "SPARK Consortium 2018, Neuron 97:488",
    "122": "Steinberg & Webber 2013, Am J Hum Genet 93:825", "123": "Parikshak et al. 2013, Cell 155:1008",
    "124": "Nair et al. 2009, Nat Genet 41:199", "125": "Abrahams et al. 2013, Mol Autism 4:36 (SFARI Gene 2.0)",
    "126": "Davis et al. 2019, Nucleic Acids Res 47:D948 (CTD)", "127": "Pua et al. 2016, J Cardiovasc Transl Res 9:3",
    "128": "Pletscher-Frankild et al. 2015, Methods 74:83 (DISEASES)",
    "129": "Shimoyama et al. 2015, Nucleic Acids Res 43:D743 (RGD disease ontology)",
}
DISEASES_TOKENS = ("ADHD", "TS", "MDD", "GAD", "Aphasia", "ConductDisorder", "AntisocialPD", "NeuroticDisorder")
RGD_TOKENS = ("CNSauto", "Osteo", "MSA", "Dementia")
# Pagani: (cells, the set name as the register transcribes it, source)
PAGANI = [
    (["PAG-C1", "PAG-C2"], "ASD DE genes", "gandal_de"),
    (["PAG-C3"], "transmission across chemical synapses", "reactome"),
    (["PAG-C4"], "SynGO", "syngo"),
    (["PAG-C5"], "protein-protein interaction at synapses", "reactome"),
    (["PAG-C6"], "membrane trafficking", "reactome"),
    (["PAG-C7"], "cytokine signaling in immune system", "reactome"),
    (["PAG-C8"], "innate immune system", "reactome"),
    (["PAG-C9"], "vesicle transport and release", "gandal_label"),
    (["PAG-C10"], "synaptic vesicles and plasticity", "gandal_label"),
    (["PAG-C11"], "immune response", "gandal_label"),
    (["PAG-C12"], "reactive microglia", "gandal_label"),
]
# register v6.7 N6 picked PAG-C9 / C10's modules by hand (GeneM3 / GeneM5, quoting Gandal 2022's Results); v6.8 (C) finds them
# by content_word_search (below) and only records whether the search agrees with that pick -- nothing here selects a module
NM_PAGANI_V67_PICK = {"PAG-C9": "GeneM3", "PAG-C10": "GeneM5"}


def content_word_search(text: str, name: str) -> dict:
    """register v6.8 (C; the orchestrator under the operator's standing delegation, after the v6.7 final re-check): the near-miss
    module of a Pagani set name, found by search, not by hand -- every sentence of Gandal 2022's article page (flattened text,
    split at sentence ends) that names exactly ONE gene module (GeneM<n>) and carries every content word of the name as a word
    ('and' dropped; a trailing 's' dropped on both sides: singular / plural); the modules found must be exactly one (the
    caller asserts it). Sentences naming several modules are counted, never used."""
    def norm(w: str) -> str:
        return w[:-1] if w.endswith("s") else w
    words = {norm(w) for w in re.findall(r"[a-z]+", name.lower()) if w != "and"}
    sents = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text)
    hits, multi = {}, 0
    for s in sents:
        mods = sorted(set(re.findall(r"\bGeneM(\d+)\b", s)), key=int)
        if words <= {norm(w) for w in re.findall(r"[a-z]+", s.lower())}:
            if len(mods) == 1:
                hits.setdefault("GeneM" + mods[0], []).append(s.strip())
            elif len(mods) > 1:
                multi += 1
    return {"name": name, "content_words": sorted(words), "searched": "Gandal 2022 article page (PMC9668748.html), flattened",
            "n_sentences": len(sents), "modules_found": {k: len(v) for k, v in sorted(hits.items())},
            "sentences": {k: v for k, v in sorted(hits.items())}, "n_multi_module_sentences_with_every_word": multi}


def build(ctx: Ctx) -> dict:
    """builds every comparator (or records why it is not buildable); returns the manifest block 'comparators_v6_6'."""
    NM = ctx.NM
    out = []

    def cells_of(tok: str) -> list[str]:
        return ["BUCH-E-%s-S%d" % (tok, k) for k in (1, 2, 3, 4)]

    def prov(paper, received, names, ref, source, url, release, rb, rc, rd, files, extra=None):
        p = {"paper": paper, "paper_received": received, "names_in_paper": names, "reference": ref,
             "R-a_source": source, "url": url, "release": release, "R-b_release_outcome": rb, "R-c_threshold": rc,
             "R-d_names": rd, "access_date": ACCESS, "files": files}
        if extra:
            p.update(extra)
        return p

    def built(key, sid, cells, raw, definition, p, labels=(), paper_size=None, extra=None):
        src = {"source_id": sid, "files": p["files"], "url": p["url"], "release": p["release"]}
        e = {"comparator_v6_6": p}
        if extra:
            e.update(extra)
        ctx.add_built(sid, cells, raw, definition, src,
                      "register 1.6 resolution rule (v6.6, R-a ... R-e; rule text sha256 %s, written %s before any "
                      "download): R-a %s; R-b %s; R-c %s" % (RULE_SHA, RULE_UTC, p["R-a_source"], p["R-b_release_outcome"],
                                                              p["R-c_threshold"]),
                      labels, paper_size=paper_size, extra=e, status=COMP_STATUS)
        out.append({"key": key, "cells": cells, "outcome": "built", "set_id": sid, "provenance": p})

    def not_buildable(key, cells, why, p):
        sid = "notbuildable66_" + key.replace(":", "_")
        ctx.add_status(sid, cells, NOT_BUILDABLE, "comparator of %s (%s)" % (key, "; ".join(
            "%s: %s" % (k, v) for k, v in p["names_in_paper"].items())),
            "comparator not buildable pre-freeze -- register 1.6 resolution rule (v6.6): " + why,
            extra={"comparator_v6_6": dict(p, **{"R-e": why})})
        out.append({"key": key, "cells": cells, "outcome": "not buildable", "set_id": sid, "why": why, "provenance": p})

    nm_out = []  # register v6.7 (1): the near-miss view

    def near_miss_built(key, view_cells, sid, raw, definition, p):
        """a near-miss comparator: a set with NO primary cells (its cells are the view's, 'secondary_view_cells')."""
        src = {"source_id": sid, "files": p["files"], "url": p["url"], "release": p["release"]}
        ctx.add_built(sid, [], raw, definition, src,
                      "register 1.6, v6.7 (1): the registered secondary view '%s' -- %s" % (NEAR_MISS_LABEL, p["reading"]),
                      [NEAR_MISS_LABEL], extra={"near_miss_view_v6_7": p, "secondary_view_cells": view_cells}, status=NM_STATUS)
        nm_out.append({"key": key, "cells": view_cells, "outcome": "built", "set_id": sid, "label": NEAR_MISS_LABEL,
                       "provenance": p})

    def near_miss_none(key, view_cells, why, p):
        nm_out.append({"key": key, "cells": view_cells, "outcome": "not buildable", "set_id": None, "label": NEAR_MISS_LABEL,
                       "why": why, "provenance": p})

    def flat_html(key: str) -> str:
        import html as _html
        t = ctx.pinned(key).read_text(encoding="utf-8")
        return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", t)))

    # ------------------------------------------------ Buch (received 2021-11-29)
    hg = ctx.hg
    tok = {t: (m, f, r) for t, m, f, r in BUCH}

    def bnames(t):
        return {"methods": tok[t][0], "figure": tok[t][1]}

    def bref(t):
        return {r.strip(): BUCH_REFS[r.strip()] for r in tok[t][2].split(",")}

    # asdM12 / asdM16 (refs 118 via 119): R-a -> R-e
    ctx.pinned("voineagu2011_s2"), ctx.pinned("parikshak2016_s4"), ctx.pinned("parikshak2013_s1d")
    s1d = _sheet_cells(ctx.pinned("parikshak2013_s1d"))
    s1d_cols = {c: s1d[(3, c)] for (r, c) in s1d if r == 3}
    s1d_lists = {s1d_cols[c]: [s1d[(r, c2)] for (r, c2) in sorted(s1d) if c2 == c and r > 3] for c in s1d_cols}
    assert s1d[(1, 1)].startswith("Table S1D - Gene lists used in enrichment analyses")
    near = {"asdM12 from Voineagu et al 2011": "ASDdown", "asdM16 from Vioneagu et al 2011": "ASDup",
            "FMRP interactors from Darnell et al 2012": "FMRP"}
    # the 'asdM12' / 'asdM16' names are Parikshak 2013's for Voineagu 2011's M12 / M16 (register v6.7 (1): verified, quoted)
    p13 = flat_html("parikshak2013_html")
    Q_P13 = ("We obtained asdM12 and adsM16 from a prior, independent gene expression study that profiled expression changes "
             "in ASD cortex and applied WGCNA to identify modules of dysregulated genes ASD ( Voineagu et al., 2011 )")
    assert Q_P13 in p13, "Parikshak 2013's naming sentence"
    v11 = flat_html("voineagu2011_html")
    assert "asdM" not in v11 and len(re.findall(r"\bM12\b", v11)) > 0 and len(re.findall(r"\bM16\b", v11)) > 0
    assert (len(s1d_lists["asdM12 from Voineagu et al 2011"]), len(s1d_lists["asdM16 from Vioneagu et al 2011"])) == (444, 386)
    naming = {"parikshak2013_quote": Q_P13.replace("( Voineagu et al., 2011 )", "(Voineagu et al., 2011)"),
              "parikshak2013_supplement01_quote": ("'We obtained asdM12 (444 genes) and adsM16 (386 genes) from an independent "
                                                   "gene expression study ...' (Extended Experimental Procedures; the list "
                                                   "lengths 444 / 386 = Table S1D's columns, asserted)"),
              "voineagu2011_article": "names its modules M12 / M16; 'asdM' occurs 0 times in its text (asserted)",
              "files": ctx.ref("parikshak2013_html", "parikshak2013_supp01", "voineagu2011_html")}
    # N1 (v6.7): Voineagu 2011's Supplementary Table 14 prints the M12 module genes (extracted by s_extract.py). v6.8 (B S1; the
    # orchestrator under the operator's standing delegation, decided after the v6.7 final re-check -- post hoc, declared): R-d
    # applied uniformly -- the paper's name 'asdM12' reaches Voineagu's M12 only through Parikshak 2013's naming (ref 123, which
    # Buch does not cite for this set), the standard that sends Tourette's, CNS autoimmune and PAG-C9 / C10 to the secondary
    # view; so asdM12 is not buildable in the PRIMARY view and its set (kept built and pinned) is the near-miss view's comparator
    t14_rows = _tsv(ctx.pinned("voineagu2011_t14"))
    t14 = [r["gene"] for r in t14_rows]
    assert len(t14) == len(set(t14)) == 380
    t14_order = [int(r["text_order"]) for r in t14_rows]  # v6.8 (C): the stored column is v6.7's defective numbering
    p12_rows = s1d_lists["asdM12 from Voineagu et al 2011"]
    p12 = set(p12_rows)
    p16 = set(s1d_lists["asdM16 from Vioneagu et al 2011"])
    assert (len(set(t14) & p12), len(set(t14) & p16)) == (312, 0), (len(set(t14) & p12), len(set(t14) & p16))

    def _hgnc(symbols):  # the S-build's section 1.6 symbol rule (approved -> previous -> alias; ambiguous dropped)
        return {s for s in (ctx.hg.resolve(None, None, g)[0] for g in symbols) if s}
    h14, h12 = _hgnc(t14), _hgnc(p12_rows)
    u_aal = set(ctx.uni["V-AAL"])
    j_aal = len(h14 & h12 & u_aal) / len((h14 | h12) & u_aal)
    overlap = {"symbols_shared": len(set(t14) & p12), "parikshak2013_rows": len(p12_rows), "parikshak2013_distinct": len(p12),
               "hgnc_table14": len(h14), "hgnc_parikshak2013": len(h12), "hgnc_shared": len(h14 & h12),
               "V-AAL_genes_table14": len(h14 & u_aal), "V-AAL_genes_parikshak2013": len(h12 & u_aal),
               "V-AAL_genes_shared": len(h14 & h12 & u_aal), "jaccard_V-AAL": round(j_aal, 4),
               "how": ("both lists mapped by the S-build's section 1.6 HGNC symbol rule; the Jaccard within the V-AAL class universe "
                       "(UNIVERSE_GENES.json), as carrier_test.py computes corroboration (a); v6.8 C: recomputed here (the v6.7 "
                       "final re-check reported 364 / .842)")}
    p = prov("buch2023asdsubgroups", BUCH_D, bnames("ASDdown"), bref("ASDdown"),
             "refs 118 (Voineagu 2011: its module M12) and 119 (Parikshak 2016: 'extracted from')",
             [PMC % ("3607626", "NIHMS313080-supplement-1.pdf"), PMC % ("7102905", "NIHMS1050915-supplement-SuppTable4.xlsx")],
             "n/a (article supplements)", "n/a", "n/a", "n/a",
             ctx.ref("voineagu2011_t14", "parikshak2016_s4") + [
                 {"path": ctx.relpath(SRC / "voineagu2011" / "NIHMS313080-supplement-1.pdf"), "sha256": VOINEAGU_SI_SHA,
                  "note": "deleted after the Table 14 extract (it also holds per-individual tables); only its sha256 is kept"}],
             {"naming": naming})
    not_buildable("BUCH:ASDdown", cells_of("ASDdown"),
                  "R-d (v6.8, applied uniformly -- the orchestrator under the operator's standing delegation, decided after the "
                  "v6.7 final re-check, post hoc, declared): the paper's names for the set ('asdM12 from 118', 'ASD "
                  "downregulated') reach no list under the cited sources' own names -- ref 118 (Voineagu 2011) calls the module "
                  "'M12' and prints its genes (Supplementary Table 14), and 'asdM12' is Parikshak 2013's name for it (ref 123, "
                  "which Buch cites for 'ID All', not for this set); ref 119 (Parikshak 2016) holds no list named asdM12 (its "
                  "CTX.M12 is its own rWGCNA module). The bridge 'asdM12' -> M12 rests on a reference the paper does not cite for "
                  "the set -- the standard that sends Tourette's, CNS autoimmune and PAG-C9 / C10 to the secondary view; v6.7 N1 "
                  "had admitted it to the primary view. Table 14's list is the near-miss view's comparator (register 1.6, v6.8)",
                  p)
    near_miss_built("BUCH:ASDdown", cells_of("ASDdown"), "nm68_buch_voineagu2011_M12_table14",
                    [{"kind": None, "id": None, "symbol": g} for g in t14],
                    "Voineagu 2011 Supplementary Table 14: the M12 module genes (asdM12 by Parikshak 2013's name; near-miss view)",
                    prov("buch2023asdsubgroups", BUCH_D, bnames("ASDdown"), bref("ASDdown"),
                         "ref 118 (Voineagu 2011): Supplementary Information, 'Supplementary Table 14. M12 module genes and "
                         "associated GWAS p values' (pp. 19-23; p. 10 maps M12 to the pink module, printed with 432, and M16 to "
                         "tan, 377)", PMC % ("3607626", "NIHMS313080-supplement-1.pdf"), "n/a (article supplement)", "n/a",
                         "every gene the table lists (380 gene symbols; its GWAS p-values and 'ASD candidate gene' marks are "
                         "annotations of the list, not a threshold of it)",
                         "the Methods' 'asdM12 from 118' reaches ref 118's module M12 only through Parikshak 2013's name "
                         "'asdM12' (quoted; Voineagu's own text says M12)",
                         ctx.ref("voineagu2011_t14") + [{"path": ctx.relpath(SRC / "voineagu2011" / "NIHMS313080-supplement-1.pdf"),
                                                         "sha256": VOINEAGU_SI_SHA, "note": "deleted after the extract (it also "
                                                         "holds per-individual tables); only its sha256 is kept"}],
                         {"reading": ("a near-miss NAME bridge (v6.8, B S1): the cited source's own list (ref 118's Supplementary "
                                      "Table 14, the M12 genes), reached from the paper's name 'asdM12' only through Parikshak "
                                      "2013's naming (ref 123, not cited by Buch for this set)"),
                          "naming": naming, "n_rows": len(t14), "rows_per_page": {"19": 76, "20": 86, "21": 86, "22": 86, "23": 46},
                          "overlap_with_parikshak2013_asdM12": overlap,
                          "overlap_with_parikshak2013_asdM16": len(set(t14) & p16),
                          "count_note": ("the v6.6 re-check parsed 382 genes; this parse finds 380 symbol / p-value rows (76 + 86 "
                                         "+ 86 + 86 + 46), consistent with the two 'ASD' header cells of p. 19 ('ASD candidate "
                                         "gene', one per column block) counted as symbols: 380 + 2 = 382"),
                          "size_note_v6_8": ("declared (v6.8 C): the table lists 380 genes while p. 10 prints 432 for M12 (the "
                                             "pink module; asserted by s_extract.py when the extract was made, v6.7 -- the PDF "
                                             "has since been deleted); the table may list only the genes with a GWAS p value "
                                             "(its caption: 'M12 module genes and associated GWAS p values') -- not verified; "
                                             "the comparator is the table as distributed"),
                          "extract_text_order_v6_8": (("v6.8 C: the extract's text_order is 1 ... %d in row order (the text "
                                                       "order), rewritten by s_extract.py in round 2; v6.7 had numbered 1, 3, 5 ... "
                                                       "restarting per page (213 distinct values for 380 rows); the gene column is "
                                                       "unchanged and is all the S-build reads" % len(t14_order))
                                                      if t14_order == list(range(1, len(t14_order) + 1)) else
                                                      ("declared (v6.8 C): the stored extract's text_order column is v6.7's "
                                                       "defective numbering (%d distinct values for %d rows)"
                                                       % (len(set(t14_order)), len(t14_order)))),
                          "m16_table": ("no printed M16 / tan gene table in the Supplementary Information (caption search: 0; "
                                        "asserted by s_extract.py)"),
                          "supersedes": ("v6.7's cmp67_buch_voineagu2011_M12_table14 (the same list, then the primary view's "
                                         "comparator, N1); v6.6's 'not buildable (R-a / R-e: Voineagu gives kME only)'")}))
    # asdM16: still not buildable in the primary view (no printed M16 list); the near-miss view: Parikshak 2013's list
    p = prov("buch2023asdsubgroups", BUCH_D, bnames("ASDup"), bref("ASDup"),
             "refs 118 (Voineagu 2011: the module, asdM16 = M16) and 119 (Parikshak 2016: 'extracted from')",
             [PMC % ("3607626", "NIHMS313080-supplement-2.xls"), PMC % ("3607626", "NIHMS313080-supplement-1.pdf"),
              PMC % ("7102905", "NIHMS1050915-supplement-SuppTable4.xlsx")],
             "n/a (article supplements)", "n/a", "n/a", "n/a",
             ctx.ref("voineagu2011_s2", "parikshak2016_s4") + [
                 {"path": ctx.relpath(SRC / "voineagu2011" / "NIHMS313080-supplement-1.pdf"), "sha256": VOINEAGU_SI_SHA,
                  "note": "deleted after the Table 14 extract; its caption search found no M16 / tan gene table"}],
             {"naming": naming})
    not_buildable("BUCH:ASDup", cells_of("ASDup"),
                  "R-a / R-e: the sources the paper cites for asdM16 distribute no list of its members -- ref 118 (Voineagu "
                  "2011) prints the M12 genes (Supplementary Table 14) but no M16 / tan gene table, and its Supplementary "
                  "Table 2 gives module membership kME only, no assignment; ref 119 (Parikshak 2016) holds no list named "
                  "asdM16 (its CTX.M16 is its own rWGCNA module); the list 'asdM16 from Vioneagu et al 2011' is distributed by "
                  "Parikshak 2013 Table S1D (ref 123, cited by Buch for 'ID All', not for this set) -- R-a does not reach it; "
                  "it is the near-miss view's comparator (register 1.6, v6.7)", p)
    col16 = "asdM16 from Vioneagu et al 2011"
    near_miss_built("BUCH:ASDup", cells_of("ASDup"), "nm67_buch_parikshak2013_asdM16",
                    [{"kind": None, "id": None, "symbol": g} for g in s1d_lists[col16]],
                    "Parikshak 2013 Table S1D 'asdM16 from Vioneagu et al 2011' (near-miss view)",
                    prov("buch2023asdsubgroups", BUCH_D, bnames("ASDup"), bref("ASDup"),
                         "Parikshak 2013 (ref 123, cited by Buch for 'ID All', not for this set): Table S1D, the column "
                         "'asdM16 from Vioneagu et al 2011' (as printed)", PMC % ("3934107", "NIHMS545068-supplement-03.xlsx"),
                         "n/a (article supplement)", "n/a", "every gene the named list carries (386 rows, %d distinct)"
                         % len(set(s1d_lists[col16])), "Parikshak 2013's own name for Voineagu's M16 (quoted in 'naming')",
                         ctx.ref("parikshak2013_s1d"),
                         {"reading": "a near-miss SOURCE: the list the paper's name 'asdM16' designates, distributed by a "
                                     "reference Buch does not cite for this set", "naming": naming,
                          "original_file_sha256": PARIKSHAK13_S03_SHA}))
    # FMRP (ref 122): not buildable; the near-miss view takes Darnell 2011's own list of the 842 targets (N7)
    ctx.pinned("steinberg2013_mmc1")
    p = prov("buch2023asdsubgroups", BUCH_D, bnames("FMRP"), bref("FMRP"),
             "ref 122 (Steinberg & Webber 2013: the 842 FMRP targets of Darnell 2011)", [PMC % ("3824119", "mmc1.pdf")],
             "n/a (article supplement)", "n/a", "n/a", "n/a", ctx.ref("steinberg2013_mmc1"))
    not_buildable("BUCH:FMRP", cells_of("FMRP"),
                  "R-a / R-e: ref 122 (Steinberg & Webber 2013) uses the 842 FMRP targets of Darnell 2011 but distributes no "
                  "list of them (Document S1: Figures S1-S5, Tables S1-S16 -- only subsets disrupted in probands, Table "
                  "S14); Darnell 2011 (Cell 146:247), which Buch does not cite, distributes the 842 in its Table S2A -- R-a "
                  "does not reach it; it is the near-miss view's comparator (register 1.6, v6.7 N7)", p)
    dn = _tsv(ctx.pinned("darnell2011_s2a"))
    ctx.pinned("darnell2011_xls")
    dt = flat_html("darnell2011_html")
    Q_DN = "We identified a stringent set of 842 FMRP target transcripts (FDR <0.01) ( Tables S2A–S2C )"
    assert Q_DN in dt and len(dn) == 842
    pf = s1d_lists["FMRP interactors from Darnell et al 2012"]
    near_miss_built("BUCH:FMRP", cells_of("FMRP"), "nm67_buch_darnell2011_fmrp842",
                    [{"kind": None, "id": None, "symbol": r["gene_symbol"]} for r in dn],
                    "Darnell 2011 Table S2A: the 842 FMRP targets, by the table's 'Gene Symbol' column (near-miss view)",
                    prov("buch2023asdsubgroups", BUCH_D, bnames("FMRP"), bref("FMRP"),
                         "Darnell et al. 2011, Cell 146:247 (PMC3232425; not cited by Buch; the list ref 122 says it used): "
                         "Table S2A 'FMRP Targets (842)'", PMC % ("3232425", "NIHMS314927-supplement-Suppl_Table_S2A-C.xls"),
                         "n/a (article supplement)", "n/a",
                         "every target the table lists (842; its FDR < 0.01 is the source's own threshold, as its text states)",
                         "the table's 'Gene Symbol' column (upper case; the mouse symbol is a separate column 'Symbol from "
                         "mm9') read by the section 1.6 HGNC symbol rule; no orthology table is added",
                         ctx.ref("darnell2011_s2a", "darnell2011_xls", "darnell2011_html"),
                         {"reading": ("a near-miss SOURCE (N7): ref 122 says it used Darnell 2011's 842 FMRP targets and "
                                      "distributes none; Darnell 2011's own supplement distributes them, so the view uses it "
                                      "instead of Parikshak 2013's 'FMRP interactors from Darnell et al 2012' (Table S1D, "
                                      "%d rows, %d distinct; %d of its genes are in Darnell's 'Gene Symbol' column)"
                                      % (len(pf), len(set(pf)), len({r["gene_symbol"] for r in dn} & set(pf)))),
                          "darnell_quote": Q_DN.replace("( Tables S2A–S2C )", "(Tables S2A–S2C)"),
                          "table_s2c_note": "Table S2C's 'human gene symbol' column is filled for 117 of the 842 only; not "
                                            "used"}))
    # SFARI syndromic (ref 125): the SFARI Gene genes CSV -- R-b by the SERVED RELEASE LABEL (v6.7 N2, post hoc clarification)
    caps = _cdx(ctx.pinned("sfari_cdx"))
    labels = json.loads(ctx.pinned("sfari_labels").read_text(encoding="utf-8"))
    assert sorted(labels) == sorted(c["timestamp"] for c in caps if c["statuscode"] == "200")
    assert all(labels[c["timestamp"]]["digest"] == c["digest"] for c in caps if c["statuscode"] == "200")
    rbl = release_by_labels(sfari_states(labels), BUCH_D)
    assert rbl["release_current_at_date"] == "2021-09-02" and rbl["state"]["capture"] == "20211022034409", rbl
    rb = release_by_captures(caps, BUCH_D)  # v6.6's digest reading, recorded beside
    sf = list(csv.DictReader(open(ctx.pinned("sfari_20211022"), encoding="utf-8", newline="")))
    sf2 = {r["gene-symbol"]: r for r in csv.DictReader(open(ctx.pinned("sfari_20220124"), encoding="utf-8", newline=""))}
    sf1 = {r["gene-symbol"]: r for r in sf}
    within = {"flip_syndromic_0_to_1": sum(1 for g in sf1 if g in sf2 and sf1[g]["syndromic"] == "0" and sf2[g]["syndromic"] == "1"),
              "flip_syndromic_1_to_0": sum(1 for g in sf1 if g in sf2 and sf1[g]["syndromic"] == "1" and sf2[g]["syndromic"] == "0"),
              "gene_score_changed": sum(1 for g in sf1 if g in sf2 and sf1[g]["gene-score"] != sf2[g]["gene-score"]),
              "genes_only_in_10-22": sum(1 for g in sf1 if g not in sf2), "genes_only_in_01-24": sum(1 for g in sf2 if g not in sf1),
              "syndromic_10-22-2021_export": sum(1 for r in sf if r["syndromic"] == "1"),
              "syndromic_01-24-2022_export": sum(1 for r in sf2.values() if r["syndromic"] == "1")}
    assert (within["syndromic_10-22-2021_export"], within["syndromic_01-24-2022_export"]) == (143, 230), within
    raw = [{"kind": "ensembl", "id": r["ensembl-id"], "symbol": r["gene-symbol"]} for r in sf if r["syndromic"] == "1"]
    st0 = rbl["state"]
    p = prov("buch2023asdsubgroups", BUCH_D, bnames("SFARIsyn"), bref("SFARIsyn"),
             "ref 125 (SFARI Gene): the genes CSV (Human Gene Module export)",
             "https://web.archive.org/web/%sid_/%s" % (st0["capture"], SFARI_CSV),
             "SFARI Gene release %s, the export of %s as the Wayback Machine captured it (%s; served as %s; %d genes)"
             % (st0["release"], st0["export"], st0["capture"], st0["served_file_name"], len(sf)),
             rbl["outcome"] + " (v6.7 N2: the rule reads the served release label -- a clarification made after the v6.6 "
             "build, post hoc: known which cells it affects; no carrier or result seen)",
             "the source's own category: syndromic == 1", "the SFARI 'syndromic' category the paper names (no term to map)",
             ctx.ref("sfari_20211022", "sfari_labels", "sfari_cdx", "sfari_20220124"),
             {"release_by_labels": {k: v for k, v in rbl.items() if k != "state"}, "state": st0,
              "v6_6_digest_reading": rb["outcome"],
              "within_release_change": dict(within, note=("the 10-22-2021 and 01-24-2022 exports serve the SAME release "
                                                          "(09-02-2021) but differ: declared (v6.7 N2)")),
              "supersedes": "v6.6's cmp66_buch_sfari_syndromic_20220124 (the 01-24-2022 export, 230 syndromic: the digest "
                            "reading took the first capture after the date as a new release)"})
    built("BUCH:SFARIsyn", "cmp67_buch_sfari_syndromic_20211022", cells_of("SFARIsyn"), raw,
          "SFARI Gene syndromic genes (syndromic == 1), release 09-02-2021 as exported 10-22-2021", p, ["S re-derived"])
    # SPARK (ref 121)
    ctx.pinned("spark_pdf")
    caps_s3 = _cdx(ctx.pinned("spark_cdx_s3"))
    rb = release_by_captures(caps_s3, BUCH_D)
    assert rb["bracketed"], rb
    import base64
    import hashlib
    dig = base64.b32encode(hashlib.sha1(PIN66["spark_pdf"][0].read_bytes()).digest()).decode()
    assert dig == rb["digest"], (dig, rb["digest"])
    ctx.pinned("spark_cdx_site")
    sp = [r["gene"] for r in _tsv(ctx.pinned("x_spark"))]
    assert len(sp) == len(set(sp)) == 153
    p = prov("buch2023asdsubgroups", BUCH_D, bnames("SPARK"), bref("SPARK"),
             "ref 121 (SPARK Consortium 2018): the SPARK gene list it links (SPARK_gene_list.pdf)",
             "https://spark-sf.s3.amazonaws.com/SPARK_gene_list.pdf (the article's link sparkforautism.org/downloads/"
             "SPARK_gene_list.pdf answers 403; its 2022-2025 captures carry the same digest)",
             "SPARK gene list 'updated July 2019' (153 single genes, 19 CNVs)",
             rb["outcome"] + " (captures %s / %s); the file downloaded 2026-09-27 has that digest (SHA-1 base32 %s), so it "
             "is the release current at the date" % (rb["last_capture_on_or_before"], rb["first_capture_on_or_after"], dig),
             "every single gene the list carries (the 19 CNVs are loci, not genes)", "the list the paper names (no term)",
             ctx.ref("spark_pdf", "x_spark", "spark_cdx_s3", "spark_cdx_site"))
    built("BUCH:SPARK", "cmp66_buch_spark_gene_list_2019", cells_of("SPARK"),
          [{"kind": None, "id": None, "symbol": g} for g in sp], "SPARK gene list (updated July 2019): 153 single genes", p,
          ["S re-derived"], paper_size=None, extra={"source_printed_size": 153})
    # RDNV (ref 120)
    fl = _tsv(ctx.pinned("sanders2019_flags"))
    ctx.pinned("sanders2019_xlsx")
    raw = [{"kind": "hgnc", "id": r["hgnc_id"], "symbol": r["symbol"]} for r in fl if r["ASD65"] == "1"]
    assert len(raw) == 65
    # v6.9 (C5 of the orchestrator's skeptic re-check, under the operator's standing delegation -- post hoc, declared): reading
    # (iii) applied uniformly. Table S1 presents several gene flags (ASD65, DDD93, CHD253 and imported sfari* columns) and
    # names none 'rare de novo'; ASD65 was chosen by a semantic reading of its column note (v6.6-v6.8), the standard that sends
    # a list reached by description (PAG-C9 / C10) to the near-miss view. RDNV is not buildable in the PRIMARY view; the same
    # 65 genes are the near-miss view's comparator. Its four cells are descriptor cells (Fig. 5c 'ns' in every subgroup): m and
    # m' are unaffected.
    p = prov("buch2023asdsubgroups", BUCH_D, bnames("RDNV"), bref("RDNV"),
             "ref 120 (Sanders 2019 Nat Med): Table S1 'List of genes', column ASD65 ('If the gene is associated with autism "
             "spectrum disorder: Sanders et al. Neuron 2015')",
             PMC % ("8656349", "NIHMS1754502-supplement-Tables_S1__S2__S4.xlsx"), "n/a (article supplement)", "n/a",
             "the source's own flag: ASD65 == 1 (its only list of ASD genes from rare de novo evidence; its sfari* columns "
             "import SFARI Gene)", "the paper's 'ASD rare de novo' is the source's one ASD rare-variant gene flag",
             ctx.ref("sanders2019_flags", "sanders2019_xlsx"))
    not_buildable("BUCH:RDNV", cells_of("RDNV"),
                  "R-e by reading (iii) (v6.9 C5, applied uniformly -- the orchestrator under the operator's standing "
                  "delegation, decided after the v6.8 skeptic re-check, post hoc, declared): ref 120's Table S1 presents several "
                  "gene flags (ASD65, DDD93, CHD253 and the sfari* columns it imports) and names none as the set the paper "
                  "names ('ASD rare de novo' / 'ASD RDNV'); v6.6-v6.8 took ASD65 by a semantic reading of its column note "
                  "('associated with autism spectrum disorder: Sanders et al. Neuron 2015') -- a list reached by description, "
                  "the standard that sends PAG-C9 / C10 to the secondary view. ASD65's 65 genes are the near-miss view's "
                  "comparator (register 1.6, v6.9); the four cells are descriptor cells (m, m' unchanged)", p)
    near_miss_built("BUCH:RDNV", cells_of("RDNV"), "nm69_buch_sanders2019_asd65", raw,
                    "Sanders 2019 Table S1 ASD65 == 1 (65 genes; near-miss view, v6.9)",
                    dict(p, reading=("a near-miss SEMANTIC reading (v6.9 C5): the cited source's column ASD65, reached from the "
                                     "paper's 'ASD rare de novo' through the column's note, not its title (reading (iii) names "
                                     "a list by its title or column only); the same 65 genes as v6.6-v6.8's primary "
                                     "comparator cmp66_buch_sanders2019_asd65"), source_printed_size=65))
    # Grove (ref 19): several gene lists, none named for the set (v6.7 N11: the PDF's literal sha256 asserted)
    ctx.pinned("grove_pdf")
    p = prov("buch2023asdsubgroups", BUCH_D, bnames("Grove"), bref("Grove"),
             "ref 19 (Grove 2019 Supplementary Information)", "https://media.springernature.com/original/springer-static/"
             "esm/art%3A10.1038%2Fs41588-019-0344-8/MediaObjects/41588_2019_344_MOESM1_ESM.pdf", "n/a", "n/a", "n/a", "n/a",
             ctx.ref("grove_pdf"))
    not_buildable("BUCH:Grove", cells_of("Grove"),
                  "R-e: ref 19 distributes several gene lists and none as the set the paper names ('ASD common variants') -- "
                  "Supplementary Table 4 (the protein-coding genes of the top loci), Table 10 (the top 25 MAGMA genes; red = "
                  "Bonferroni-significant) and Table 16 (credible-SNP / Hi-C genes); the list cannot be read unambiguously", p)
    # RGD disease ontology (ref 129): CNSauto, Osteo, MSA, Dementia -- v6.7 (2), the uniform archive rule: the Wayback
    # Machine's captures of RGD's human annotation file; the earliest COMPLETE capture after the date (2024-07-24,
    # 'date-generated: 2024-07-20') with the RDO release of the same week from RGD's own weekly archive (RDO_20240720)
    ctx.pinned("rgd_rdo_20240720_gz")
    rgd_caps = [c for c in _cdx(ctx.pinned("rgd_cdx")) if c["statuscode"] == "200"]
    lens = json.loads(ctx.pinned("rgd_capture_lengths").read_text(encoding="utf-8"))
    after = sorted(c["timestamp"] for c in rgd_caps if c["timestamp"][:8] >= BUCH_D.replace("-", ""))
    complete = [ts for ts in after if (lens.get(ts) or {}).get("complete")]
    assert complete and complete[0] == "20240724223811" and all(ts in lens for ts in after[:after.index(complete[0])]), \
        (after, complete)
    cut = [ts for ts in after[:after.index(complete[0])]]
    assert all(not lens[ts]["complete"] for ts in cut)
    assert ctx.pinned("rgd_ann_20240724").stat().st_size == int(lens["20240724223811"]["content_length"])  # the whole file
    ann_txt = ctx.pinned("rgd_ann_20240724").read_text(encoding="utf-8")
    gen_date = re.search(r"^!date-generated: (\S+)", ann_txt, re.M).group(1)
    assert gen_date == "2024-07-20", gen_date
    rdo_terms, rdo_dv = ctx.read_obo(ctx.pinned("rgd_rdo_20240720"))
    rdo_c = ctx.obo_candidates(rdo_terms, None)
    kids = defaultdict(set)
    for tid, d in rdo_terms.items():
        for par in d["parents"]:
            kids[par].add(tid)
    gaf = defaultdict(set)
    n_noassoc = 0
    for line in ann_txt.splitlines():
        if line.startswith("!") or not line.strip():
            continue
        c = line.split("\t")
        if c[3] == "no_association":  # the annotation says the gene is NOT associated
            n_noassoc += 1
            continue
        gaf[c[4]].add(c[2])
    rgd_rb = ("earliest archived release after the date (the uniform archive rule, v6.7 (2)): the Wayback captures of the "
              "annotation file after 2021-11-29 are %s; %s %s cut short by the crawler (x-archive-orig-x-crawler-content-"
              "length), so the earliest COMPLETE capture, %s ('date-generated: %s'), is the earliest obtainable release; the "
              "ontology of the same week from RGD's own weekly archive, RDO %s (v6.6: 'release substituted', 2026-09-19, when "
              "the one capture examined was a truncated one)"
              % (", ".join(after), ", ".join(cut), "is" if len(cut) == 1 else "are", complete[0], gen_date, rdo_dv))
    for t in RGD_TOKENS:
        names = [tok[t][0], tok[t][1]]
        tid, rec, recs, why = names_rule(NM, names, rdo_c)
        base = prov("buch2023asdsubgroups", BUCH_D, bnames(t), bref(t),
                    "ref 129 (RGD disease ontology): RGD's human gene -> RDO annotations (GAF 2.2) and RDO.obo",
                    "https://web.archive.org/web/20240724223811id_/https://download.rgd.mcw.edu/ontology/"
                    "annotated_rgd_objects_by_ontology/homo_genes_rdo; https://download.rgd.mcw.edu/ontology/disease/2024/"
                    "RDO_20240720_v1.283.obo.gz",
                    "RGD annotations generated %s (Wayback capture 20240724223811); RDO %s" % (gen_date, rdo_dv), rgd_rb,
                    "every gene annotated to the term or a descendant (is_a / part_of; RGD's ontology report shows a "
                    "term's descendants' annotations by default -- 'show annotations for term's descendants' is checked), "
                    "all evidence codes; a row qualified 'no_association' is not an association (%d such rows)" % n_noassoc,
                    [_rec_short(NM, r) for r in recs],
                    ctx.ref("rgd_ann_20240724", "rgd_rdo_20240720", "rgd_rdo_20240720_gz", "rgd_cdx", "rgd_capture_lengths"))
        for c in cells_of(t):
            ctx.record_match(c, rec, "RGD RDO %s" % rdo_dv, "set name (Buch Methods / Fig. 5d label)", printed=names[0])
        if tid is None:
            near_ = {"CNSauto": "DOID:0060004"}.get(t)
            if near_:
                base["near_miss_term_not_reached"] = {"term": near_, "name": rdo_terms[near_]["name"],
                                                      "why_not": "the name rule makes no word-order normalisation"}
            not_buildable("BUCH:" + t, cells_of(t), "R-d: %s (%s)" % (why, "; ".join(
                "%r: tiers %s" % (r["query"], {k: len(v) for k, v in r["tiers"].items()}) for r in recs)), base)
            if t in NORMALISE_V67:  # register v6.7 (1): the near-miss view's declared normalisation (this name only)
                what, fn = NORMALISE_V67[t]
                nn = [fn(x) for x in names]
                tid2, rec2, recs2, why2 = names_rule(NM, nn, rdo_c)
                pnm = dict(base, reading="the declared normalisation '%s' applied to this set's names only: %s -> %s"
                           % (what, names, nn), normalised_names=nn, name_rule_records=[_rec_short(NM, r) for r in recs2])
                if tid2 is None:
                    near_miss_none("BUCH:" + t, cells_of(t), "R-d after the declared normalisation (%s): %s (%s)" % (
                        what, why2, "; ".join("%r: tiers %s" % (r["query"], {k: len(v) for k, v in r["tiers"].items()})
                                              for r in recs2)), pnm)
                else:
                    desc2 = ctx.descendants(tid2, [kids])
                    near_miss_built("BUCH:" + t, cells_of(t), "nm67_buch_rgd_%s" % tid2.replace(":", ""),
                                    [{"kind": None, "id": None, "symbol": s} for term in sorted(desc2)
                                     for s in sorted(gaf.get(term, ()))],
                                    "RGD human genes annotated to RDO %s '%s' or a descendant (near-miss view)"
                                    % (tid2, rdo_terms[tid2]["name"]), dict(pnm, term={"id": tid2}))
            continue
        desc = ctx.descendants(tid, [kids])
        raw = [{"kind": None, "id": None, "symbol": s} for term in sorted(desc) for s in sorted(gaf.get(term, ()))]
        base["term"] = {"id": tid, "name": rdo_terms[tid]["name"], "n_terms_with_descendants": len(desc),
                        "n_genes_term_only": len(gaf.get(tid, ()))}
        base["supersedes"] = "v6.6's cmp66_buch_rgd_%s (RGD 2026-09-19, 'release substituted')" % tid.replace(":", "")
        built("BUCH:" + t, "cmp67_buch_rgd_%s_20240720" % tid.replace(":", ""), cells_of(t), raw,
              "RGD human genes annotated to RDO %s '%s' or a descendant (annotations of 2024-07-20)" % (tid, rdo_terms[tid]["name"]),
              base, ["S re-derived"])
    # heart disease (ref 127): Pua 2016 Table S1
    st1 = _sheet_cells(ctx.pinned("pua2016_st1"))
    assert st1[(1, 1)].startswith("Table S1 Full ICCv1 (n=169) gene list and additional genes (n=5) in ICCv2 panel")
    assert st1[(251, 1)].startswith("a ICC gene (n=30) listed in ACMG"), "the footnote defining the marker 'a'"
    genes = []
    for (r, c) in sorted(st1):
        if c == 1 and r > 2 and (r, 2) in st1:
            g = st1[(r, 1)]
            genes.append(g[:-1] if g.endswith("a") else g)  # the table's one footnote marker 'a' (row 251)
    # v6.7 N9: Pua's printed counts against the table's rows (declared, not repaired)
    maxr = max(r for r, _ in st1)
    secs = [(r, st1[(r, 1)]) for r in range(3, maxr + 1) if (r, 1) in st1 and (r, 2) not in st1]
    printed_vs_rows = {}
    for i, (r, t) in enumerate(secs):
        m_ = re.search(r"\((\w+)\) - (\d+) genes", t)
        if m_:
            end = secs[i + 1][0] if i + 1 < len(secs) else maxr + 1
            printed_vs_rows[m_.group(1)] = (int(m_.group(2)), sum(1 for rr in range(r + 1, end) if (rr, 1) in st1 and (rr, 2) in st1))
    assert printed_vs_rows["HCM"] == (48, 47) and printed_vs_rows["DCM"] == (51, 50), printed_vs_rows
    assert "(n=169 + 5)" in st1[(250, 1)] and (len(genes), len(set(genes))) == (212, 132)
    p = prov("buch2023asdsubgroups", BUCH_D, bnames("HeartDisease"), bref("HeartDisease"),
             "ref 127 (Pua 2016): ESM1 Table S1, the one table the source presents as its gene list",
             PMC % ("4767849", "12265_2016_9673_MOESM1_ESM.xlsx"), "n/a (article supplement)", "n/a",
             "every gene of the table (ICCv1 and the five ICCv2 additions; a trailing footnote marker 'a' removed)",
             "the list the paper cites (no term)", ctx.ref("pua2016_st1"),
             {"original_file_sha256": PUA_ESM1_SHA, "n_rows": len(genes), "n_distinct": len(set(genes)),
              "declared_counts_v6_7": {
                  "printed": "the table prints 'n = 169 + 5' genes (its footnote) and per-condition headers '<condition> - <n> "
                             "genes'", "rows_listed": len(genes), "distinct_genes": len(set(genes)),
                  "printed_vs_rows_by_condition": {k: {"printed": a, "rows": b} for k, (a, b) in printed_vs_rows.items()},
                  "mismatches": {k: {"printed": a, "rows": b} for k, (a, b) in printed_vs_rows.items() if a != b},
                  "note": ("genes recur across conditions, so 212 rows hold 132 distinct genes; the HCM and DCM headers print 48 "
                           "/ 51 against 47 / 50 rows (v6.7 N9: declared, the table taken as distributed)")},
              "not_rebuildable_from_register_sets_src": ("the original ESM1 xlsx was deleted after the extract (it also holds "
                                                         "a per-sample sheet); only its sha256 is kept (v6.7 N11)")})
    built("BUCH:HeartDisease", "cmp66_buch_pua2016_icc_genes", cells_of("HeartDisease"),
          [{"kind": None, "id": None, "symbol": g} for g in sorted(set(genes))],
          "Pua 2016 Table S1: the inherited cardiac condition genes (ICCv1 + ICCv2 additions)", p, ["S re-derived"])
    # psoriasis (ref 124)
    ctx.pinned("nair2009_html"), ctx.pinned("nair2009_supp")
    p = prov("buch2023asdsubgroups", BUCH_D, bnames("Psoriasis"), bref("Psoriasis"),
             "ref 124 (Nair 2009): the article's tables and its supplement",
             "https://pmc.ncbi.nlm.nih.gov/articles/PMC2745122/", "n/a", "n/a", "n/a", "n/a",
             ctx.ref("nair2009_html", "nair2009_supp"))
    not_buildable("BUCH:Psoriasis", cells_of("Psoriasis"),
                  "R-e: ref 124 distributes loci, not a gene list -- Table 2 lists the loci followed up with their 'notable "
                  "nearby genes' (18 loci, 10 with support, 7 confirmed) and Supplementary Table 4 the seven confirmed loci; "
                  "the list cannot be read unambiguously", p)
    # vocal learning (ref 61): v6.7 N4 -- Tables S1-S8 obtained (science.org, in a browser with a fresh profile); R-e on
    # their CONTENTS: the sheet names (read programmatically) name region specialisations, none 'vocal learning'
    ctx.pinned("pfenning2014_supp")
    ctx.pinned("pfenning2014_zip")
    sheets = {}  # v6.8 (B S2): sheet NAMES only -- no cell of these workbooks is read; round 2: from the zip's reduction
    zn = RV.zip_sheet_names(ctx.reduction("pfenning2014_zip"))
    for m in sorted(n for n in zn if n.lower().endswith(".xlsx")):
        sheets[m] = [t.strip() for t in zn[m]]
    lists = {m: s for m, s in sheets.items() if re.search(r"SuppTable(3|6)-", m)}
    assert sorted(lists) == ["SuppTable3-Finch_Gene_Specializations V25.xlsx", "SuppTable6-CrossSpecies_Specializations V25.xlsx"]
    assert len(lists["SuppTable3-Finch_Gene_Specializations V25.xlsx"]) == 9 and \
        len(lists["SuppTable6-CrossSpecies_Specializations V25.xlsx"]) == 1
    assert not any(re.search(r"(?i)vocal", s) for ss in sheets.values() for s in ss)
    p = prov("buch2023asdsubgroups", BUCH_D, bnames("Vocal"), bref("Vocal"),
             "ref 61 (Pfenning 2014): Tables S1-S8 ('zipped folder, Excel format'), obtained from science.org (v6.7 N4)",
             "https://www.science.org/doi/suppl/10.1126/science.1256846/suppl_file/pfenning-tables-s1-to-s8.zip (plain HTTPS "
             "meets a Cloudflare bot challenge, HTTP 403; no Wayback capture; Europe PMC does not serve it; fetched 2026-09-27 "
             "by a real Chrome browser started with a fresh, empty profile -- no login, cookie or identifier)",
             "n/a", "n/a", "n/a", "n/a", ctx.ref("pfenning2014_supp", "pfenning2014_zip"),
             {"sheets": sheets, "gene_lists": {
                 "Table S3 (9 sheets)": "zebra finch (A-F) and macaque (G-I) region specialisations shared with human regions",
                 "Table S6 (1 sheet)": "genes with common specialisations between avian RA analogues and human LMC / LSC, "
                                       "broken into sections"}})
    not_buildable("BUCH:Vocal", cells_of("Vocal"),
                  "R-e (v6.7 N4, on the tables' contents): Tables S1-S8 distribute several specialisation lists -- Table S3's "
                  "nine region sheets (A.Striatum ... F.LMAN, G-I macaque) and Table S6's cross-species RA-analogue / LMC "
                  "list -- and name none of them 'vocal learning' genes (no sheet name carries 'vocal'); the list cannot be "
                  "read unambiguously (v6.6 read the captions only: the tables were then unobtainable)", p)
    near_miss_none("BUCH:Vocal", cells_of("Vocal"),
                   "no near-miss source or name normalisation reaches a single list: the cited source itself distributes the "
                   "candidates (Table S3's region lists, Table S6's convergent RA / LMC list) and picking one of them is the "
                   "choice R-e forbids; not auditable in both views (register 1.6, v6.7 N4; the orchestrator's instruction "
                   "added the claims to the view only if the tables stayed unobtainable)", p)
    # DISEASES (ref 128): v2 (figshare 2022-02-09), filtered channel files
    for k in ("diseases_cdx_knowledge", "diseases_cdx_experiments", "diseases_cdx_textmining"):
        ctx.pinned(k)
    cdx_rb = {k.split("_")[-1]: release_by_captures(_cdx(ctx.pinned(k)), BUCH_D)
              for k in ("diseases_cdx_knowledge", "diseases_cdx_experiments", "diseases_cdx_textmining")}
    tf = tarfile.open(ctx.pinned("diseases_dictionary"))
    ent = {}
    for line in tf.extractfile("diseases_entities.tsv").read().decode("utf-8").splitlines():
        p_ = line.split("\t")
        if len(p_) >= 3 and p_[1] == "-26":
            ent[p_[0]] = p_[2]
    pref = {}
    for line in tf.extractfile("diseases_preferred.tsv").read().decode("utf-8").splitlines():
        p_ = line.split("\t")
        if len(p_) >= 2 and p_[0] in ent:
            pref[ent[p_[0]]] = p_[1]
    syn = defaultdict(list)
    for line in tf.extractfile("diseases_names.tsv").read().decode("utf-8").splitlines():
        p_ = line.split("\t")
        if len(p_) >= 2 and p_[0] in ent:
            syn[ent[p_[0]]].append((p_[1], "DISEASES dictionary"))
    d_c = [{"id": i, "name": pref.get(i, i), "synonyms": syn.get(i, []), "live": True} for i in sorted(set(ent.values()))]
    chan = {}
    for ch in ("knowledge", "experiments", "textmining"):
        rows_ = defaultdict(set)
        with gzip.open(ctx.pinned("diseases_" + ch), "rt", encoding="utf-8") as f:
            for line in f:
                c = line.rstrip("\n").split("\t")
                if len(c) >= 4:
                    rows_[c[2]].add(c[1])
        chan[ch] = rows_
    for t in DISEASES_TOKENS:
        names = [tok[t][0], tok[t][1]]
        tid, rec, recs, why = names_rule(NM, names, d_c)
        base = prov("buch2023asdsubgroups", BUCH_D, bnames(t), bref(t),
                    "ref 128 (DISEASES): the three filtered channel files (knowledge, experiments, text mining)",
                    "https://figshare.com/authors/Lars_Juhl_Jensen/96428 (DISEASES v2, 2022-02-09: items 19146077 / "
                    "19146101 / 19146107; dictionary 19146044)",
                    "DISEASES v2 (figshare, published 2022-02-09)",
                    "DISEASES is rebuilt weekly and no weekly set of its channel files is archived near the date: the "
                    "Wayback captures are per file and on different dates (knowledge: %s; experiments: %s; text mining: "
                    "%s), none brackets 2021-11-29; the Jensen lab's own archived release DISEASES v2 (2022-02-09) is the "
                    "earliest archived release after the date" % tuple(
                        "last on or before %s, first after %s" % (cdx_rb[x]["last_capture_on_or_before"],
                                                                 cdx_rb[x]["first_capture_on_or_after"])
                        for x in ("knowledge", "experiments", "textmining")),
                    "the source's documented default: the filtered files ('the non-redundant associations shown within "
                    "the web interface'), every association of the term in the three channels (the interface shows the "
                    "three on the disease's page); associations as distributed (DISEASES already backtracks child terms' "
                    "evidence to their parents)",
                    [_rec_short(NM, r) for r in recs], ctx.ref("diseases_knowledge", "diseases_experiments",
                                                                "diseases_textmining", "diseases_dictionary",
                                                                "diseases_cdx_knowledge", "diseases_cdx_experiments",
                                                                "diseases_cdx_textmining"))
        for c in cells_of(t):
            ctx.record_match(c, rec, "DISEASES v2 (2022-02-09)", "set name (Buch Methods / Fig. 5e label)", printed=names[0])
        if tid is None:
            if t == "TS":
                base["near_miss_term_not_reached"] = {"term": "DOID:11119", "name": pref.get("DOID:11119"),
                                                      "why_not": "the source's names ('Tourette syndrome', 'Tourette "
                                                                 "disorder', ...) carry no possessive; the name rule "
                                                                 "normalises no punctuation"}
            not_buildable("BUCH:" + t, cells_of(t), "R-d: %s (%s)" % (why, "; ".join(
                "%r: tiers %s" % (r["query"], {k: len(v) for k, v in r["tiers"].items()}) for r in recs)), base)
            if t in NORMALISE_V67:  # register v6.7 (1): the near-miss view's declared normalisation (this name only)
                what, fn = NORMALISE_V67[t]
                nn = [fn(x) for x in names]
                tid2, rec2, recs2, why2 = names_rule(NM, nn, d_c)
                pnm = dict(base, reading="the declared normalisation '%s' applied to this set's names only: %s -> %s"
                           % (what, names, nn), normalised_names=nn, name_rule_records=[_rec_short(NM, r) for r in recs2])
                if tid2 is None:
                    near_miss_none("BUCH:" + t, cells_of(t), "R-d after the declared normalisation (%s): %s" % (what, why2), pnm)
                else:
                    per2 = {ch: sorted(chan[ch].get(tid2, ())) for ch in chan}
                    pnm["term"] = {"id": tid2, "name": pref.get(tid2), "n_genes_per_channel": {ch: len(v) for ch, v in per2.items()}}
                    near_miss_built("BUCH:" + t, cells_of(t), "nm67_buch_diseases_%s" % tid2.replace(":", ""),
                                    [{"kind": None, "id": None, "symbol": s} for s in sorted(set().union(*per2.values()))],
                                    "DISEASES v2 %s '%s': the genes of its filtered knowledge, experiments and text-mining "
                                    "associations (near-miss view)" % (tid2, pref.get(tid2)), pnm)
            continue
        per = {ch: sorted(chan[ch].get(tid, ())) for ch in chan}
        base["term"] = {"id": tid, "name": pref.get(tid), "n_genes_per_channel": {ch: len(v) for ch, v in per.items()}}
        built("BUCH:" + t, "cmp66_buch_diseases_%s" % tid.replace(":", ""), cells_of(t),
              [{"kind": None, "id": None, "symbol": s} for s in sorted(set().union(*per.values()))],
              "DISEASES v2 %s '%s': the genes of its filtered knowledge, experiments and text-mining associations" %
              (tid, pref.get(tid)), base, ["S re-derived"])
    # schizophrenia (ref 126): CTD -- v6.7 (2), the uniform archive rule: v6.6's 'not in the Wayback Machine' came from a
    # malformed CDX query (a wildcard mid-URL); exact-URL listings show captures; the earliest capture day after the date
    # holding BOTH a gene-disease file and its disease vocabulary is taken (a release is a set of files of one date)
    ctx.pinned("ctd_obo_20240210_gz")
    dd = BUCH_D.replace("-", "")
    days = {}
    for k in ("ctd_cdx_gd_tsv", "ctd_cdx_gd_csv", "ctd_cdx_gd_xml", "ctd_cdx_d_tsv", "ctd_cdx_d_csv", "ctd_cdx_d_xml",
              "ctd_cdx_d_obo"):
        days[k] = sorted({c["timestamp"][:8] for c in _cdx(ctx.pinned(k)) if c["statuscode"] == "200" and c["timestamp"][:8] >= dd})
    gd_days = set(days["ctd_cdx_gd_tsv"]) | set(days["ctd_cdx_gd_csv"]) | set(days["ctd_cdx_gd_xml"])
    voc_days = set(days["ctd_cdx_d_tsv"]) | set(days["ctd_cdx_d_csv"]) | set(days["ctd_cdx_d_xml"]) | set(days["ctd_cdx_d_obo"])
    both = sorted(gd_days & voc_days)
    assert both and both[0] == "20240210" and "20240210" in days["ctd_cdx_gd_tsv"] and "20240210" in days["ctd_cdx_d_obo"], \
        (both[:3], days)
    # v6.8 (C): the reading 'a release is a set of files of one date' was taken while building, the outcome known (v6.7); its
    # alternative -- the gene-disease file alone, its earliest capture day after the date -- named here (computed, not typed)
    ctd_alt = {"reading": ("a release is a set of files of one date: a gene-disease file and its disease vocabulary captured the "
                           "same day (register 1.6 reading (i); v6.7) -- taken while building, outcome known (tagged v6.8)"),
               "alternative_gene_disease_file_alone": _day(min(gd_days)), "earliest_vocabulary_capture": _day(min(voc_days)),
               "chosen_both_on_one_day": _day(both[0])}
    ctd_terms, _ = ctx.read_obo(ctx.pinned("ctd_obo_20240210"))
    obo_head = ctx.pinned("ctd_obo_20240210").read_text(encoding="utf-8")[:400]
    obo_date = re.search(r"^date: (\S+)", obo_head, re.M).group(1)
    ctd_c = ctx.obo_candidates(ctd_terms, None)
    ctd_kids = defaultdict(set)
    for t_, d_ in ctd_terms.items():
        for par in d_["parents"]:
            ctd_kids[par].add(t_)
    with gzip.open(ctx.pinned("ctd_gd_20240210"), "rt", encoding="utf-8") as f:  # N11: the 2.7 GB file's literal sha256 asserted
        head = [next(f) for _ in range(30)]
    created = next(ln for ln in head if ln.startswith("# Report created:")).split(":", 1)[1].strip()
    assert created == "Wed Jan 31 12:01:18 EST 2024", created
    lic = "".join(ln for ln in head if ln.startswith("#"))
    assert "You must notify CTD" in lic
    names = [tok["SZ"][0], tok["SZ"][1]]
    tid, rec, recs, why = names_rule(NM, names, ctd_c)
    assert tid == "MESH:D012559", (tid, why)
    desc = ctx.descendants(tid, [ctd_kids])
    rows_ = _tsv(ctx.pinned("ctd_sz_rows_20240210"))
    assert {r["DiseaseID"] for r in rows_} <= desc
    for c in cells_of("SZ"):
        ctx.record_match(c, rec, "CTD (report created 2024-01-31; captured 2024-02-10)", "set name (Buch Methods / Fig. 5e "
                         "label)", printed=names[0])
    p = prov("buch2023asdsubgroups", BUCH_D, bnames("SZ"), bref("SZ"),
             "ref 126 (CTD): CTD_genes_diseases.tsv.gz, the gene-disease file its downloads page lists, and its disease "
             "vocabulary (MEDIC, CTD_diseases.obo.gz)",
             "https://web.archive.org/web/20240210030103id_/https://ctdbase.org/reports/CTD_genes_diseases.tsv.gz; "
             "https://web.archive.org/web/20240210030137id_/https://ctdbase.org/reports/CTD_diseases.obo.gz",
             "CTD report created %s (the file's own header), vocabulary dated %s; both captured 2024-02-10" % (created, obo_date),
             "earliest archived release after the date (the uniform archive rule, v6.7 (2)): the capture days after "
             "2021-11-29 holding both a gene-disease file and a disease vocabulary begin %s (earliest %s); v6.6's 'not in the "
             "Wayback Machine' came from a malformed CDX query and is withdrawn" % (", ".join(both[:4]), both[0]),
             "every gene the term or a MEDIC descendant carries in the gene-disease file (curated and inferred rows; CTD's "
             "displays aggregate descendants); CTD's term pages sit behind a human-verification page, the files do not",
             [_rec_short(NM, r) for r in recs],
             ctx.ref("ctd_gd_20240210", "ctd_obo_20240210", "ctd_obo_20240210_gz", "ctd_sz_rows_20240210", "ctd_cdx_gd_tsv",
                     "ctd_cdx_gd_csv", "ctd_cdx_gd_xml", "ctd_cdx_d_tsv", "ctd_cdx_d_csv", "ctd_cdx_d_xml", "ctd_cdx_d_obo"),
             {"term": {"id": tid, "descendants": sorted(desc), "n_rows": len(rows_),
                       "n_rows_curated": sum(1 for r in rows_ if r["DirectEvidence"])},
              "licence": ("CTD's terms (the file header): cite CTD; link to CTD's pages; 'You must notify CTD, and describe "
                          "your use of our data'; give CTD periodic access to the publication -- CTD must be notified before "
                          "any result using this set is published (register 1.6 and 6, v6.7 (4))"),
              "supersedes": "v6.6's cmp66_buch_ctd_MESHD012559 (CTD 2026-08-28, 'release substituted')",
              "archive_reading_v6_8": ctd_alt})
    built("BUCH:SZ", "cmp67_buch_ctd_MESHD012559_20240131", cells_of("SZ"),
          [{"kind": "entrez", "id": r["GeneID"], "symbol": r["GeneSymbol"]} for r in rows_],
          "CTD genes of Schizophrenia (MESH:D012559) and its MEDIC descendants (curated and inferred; report of 2024-01-31)",
          p, ["S re-derived"])
    # intellectual disability (ref 123): Parikshak 2013 Table S1D 'ID All'
    ida = s1d_lists["ID All"]
    p = prov("buch2023asdsubgroups", BUCH_D, bnames("ID"), bref("ID"),
             "ref 123 (Parikshak 2013): Table S1D 'Gene lists used in enrichment analyses', the column 'ID All'",
             PMC % ("3934107", "NIHMS545068-supplement-03.xlsx"), "n/a (article supplement)", "n/a",
             "every gene the named list carries", "the paper quotes the list's own name, 'ID All' (exact)",
             ctx.ref("parikshak2013_s1d"),
             {"original_file_sha256": PARIKSHAK13_S03_SHA,
              "not_rebuildable_from_register_sets_src": ("the original supplement-03 xlsx was deleted after the extract (it "
                                                         "also holds a per-individual sheet); only its sha256 is kept (v6.7 "
                                                         "N11)")})
    built("BUCH:ID", "cmp66_buch_parikshak2013_id_all", cells_of("ID"),
          [{"kind": None, "id": None, "symbol": g} for g in ida], "Parikshak 2013 Table S1D 'ID All'", p, ["S re-derived"])

    # ------------------------------------------------ Pagani (received 2025-04-17)
    gm = _tsv(ctx.pinned("gandal2022_modules"))
    ctx.pinned("gandal2022_moesm7")
    def _fdr_cols(h):
        return [j for j, x in enumerate(h) if x == "Whole.Cortex_ASD_FDR" or (x and x.startswith("ASD_BA") and x.endswith("_FDR"))]
    # v6.8 (B S2): GeneModules is wider than 50 columns -- the guard reads only the declared columns: the module name, the
    # whole-cortex / regional ASD FDR columns and the logFC column before each; round 2: read from MOESM8's reduction (those
    # columns only, at their original positions)
    mr = ctx.sheet_rows("gandal2022_moesm8", "GeneModules",
                        declared=lambda h: sorted({0} | set(_fdr_cols(h)) | {j - 1 for j in _fdr_cols(h)}),
                        header_row=1, label="gandal2022 MOESM8")
    h = list(mr[1])
    fc = _fdr_cols(h)
    de, n_up, n_down = [], 0, 0
    for r in mr[2:]:
        if not r[0]:
            continue
        sig = [j for j in fc if r[j] is not None and float(r[j]) < 0.05]
        if sig:
            de.append(r[0])
            sg = {1 if float(r[j - 1]) > 0 else -1 for j in sig}
            assert len(sg) == 1
            n_up += sg == {1}
            n_down += sg == {-1}
    assert (len(de), n_up, n_down) == (24, 15, 9), (len(de), n_up, n_down)
    mods = {m.replace("Gene", "", 1) for m in de}
    labels = json.loads(ctx.pinned("gandal2022_labels").read_text(encoding="utf-8"))
    size = Counter(r["WGCNA_module"] for r in gm)
    for lab in labels["labels"]:
        if lab["module"].startswith("GeneM") and lab["printed_n_genes"]:
            mm = next(m for m in size if m.split("_")[0] == lab["module"][4:])
            assert size[mm] == lab["printed_n_genes"], (lab, size[mm])
    gref = ctx.ref("gandal2022_modules", "gandal2022_moesm7", "gandal2022_moesm8")
    g_url = [PMC % ("9668748", "41586_2022_5377_MOESM7_ESM.xlsx"), PMC % ("9668748", "41586_2022_5377_MOESM8_ESM.xlsx")]
    gnote = ("Pagani's human Methods cite [25] (Shofty 2019) for the modules, its Results and Fig. 5 ref. 16 (Gandal 2022); "
             "the register takes ref. 16 (register 3.1)")
    lab_c = [{"id": lab["module"], "name": lab["label"], "synonyms": [], "live": True}
             for lab in labels["labels"] if lab["module"].startswith("GeneM")]
    rx_c, rx_mem = [], {}
    for line in open(ctx.pinned("reactome92_txt"), encoding="utf-8"):
        c = line.rstrip("\n").split("\t")
        if len(c) >= 3 and c[2] == "Homo sapiens":
            rx_c.append({"id": c[0], "name": c[1], "synonyms": [], "live": True})
    z = zipfile.ZipFile(ctx.pinned("reactome92_gmt"))
    for line in z.read("ReactomePathways.gmt").decode("utf-8").splitlines():
        c = line.split("\t")
        rx_mem[c[1]] = [s for s in c[2:] if s]
    gtext = flat_html("gandal2022_html")  # v6.7 N6: Gandal's own text and Pagani's wording (the near-miss view)
    ptext = flat_html("pagani_text")
    pm = re.search(r"Only co-expression modules of known biological function \( n = 10[^)]*\) were considered", ptext)
    assert pm, "Pagani's 'known biological function (n = 10)' sentence"
    pq = "Only co-expression modules of known biological function (n = 10) were considered"
    for cells, qname, kind in PAGANI:
        pn = {"register": qname}
        if kind == "gandal_de":
            raw = [{"kind": "ensembl", "id": r["ensembl_gene_id"], "symbol": r["hgnc_symbol"] or r["external_gene_name"]}
                   for r in gm if r["WGCNA_module"] in mods]
            p = prov("pagani2026crossspecies", PAGANI_D, pn, {"16": "Gandal et al. 2022, Nature 611:532"},
                     "ref. 16 (Gandal 2022): Supplementary Data 5 (module membership, Gene_Level) and 6 (module-ASD "
                     "association, GeneModules)", g_url, "n/a (article supplement)", "n/a",
                     "the paper's own definition: all genes of the 24 co-expression modules reported DE in ASD -- the "
                     "source's gene modules with an ASD association at FDR < .05 in the whole cortex or any of its 11 "
                     "regions: 24 (15 up, 9 down), as the source prints ('Nine modules were downregulated and 15 were "
                     "upregulated')", "the paper's own definition (no term)", gref,
                     {"modules": sorted(de, key=lambda m: int(re.match(r"GeneM(\d+)", m).group(1))), "note": gnote})
            built("PAGANI:PAG-C1", "cmp66_pagani_gandal2022_24_de_modules", cells, raw,
                  "Gandal 2022: all genes of the 24 gene co-expression modules DE in ASD", p, ["S re-derived"],
                  extra={"source_printed_size": None})
        elif kind == "syngo":
            zz = zipfile.ZipFile(ctx.pinned("syngo12_zip"))
            ctx.pinned("syngo_portal_20250406"), ctx.pinned("syngo_portal_20251118")
            ws = openpyxl.load_workbook(io.BytesIO(zz.read("genes.xlsx")), read_only=True, data_only=True).worksheets[0]
            it = iter(G.read_openpyxl(ws, label="syngo genes.xlsx"))  # v6.8 (B S2): the guard (the sheet is clean)
            hh = list(next(it))
            ih, isy = hh.index("hgnc_id"), hh.index("hgnc_symbol")
            raw = [{"kind": "hgnc", "id": r[ih], "symbol": r[isy]} for r in it if r and r[ih]]
            assert len(raw) == 1602, len(raw)
            p = prov("pagani2026crossspecies", PAGANI_D, pn, {"101 (mouse Methods)": "Koopmans et al. 2019, Neuron 103:217"},
                     "SynGO (the manually curated synaptic genes; Pagani's mouse Methods ref. 101)",
                     "https://www.syngoportal.org/data/syngo1.2_complete_data.zip",
                     "SynGO release 1.2 = release '20231201' (the portal: 'released in 2023 ... 4218 annotations against 1602 "
                     "unique human genes')",
                     "release current at the date: the archived portal pages of 2025-04-06 and 2025-11-18 both list "
                     "release '20231201' as the newest (release 1.3, 'released in 2025', appears only on the 2026 portal); "
                     "the 20231201 zip itself is no longer served, the portal serves it repackaged as syngo1.2_complete_data",
                     "every gene the resource annotates (genes.xlsx: 1,602)", "the paper's 'SynGO' is the resource (no term)",
                     ctx.ref("syngo12_zip", "syngo_portal_20250406", "syngo_portal_20251118"))
            built("PAGANI:PAG-C4", "cmp66_pagani_syngo_1.2_20231201", cells, raw, "SynGO release 1.2 (20231201): all 1,602 "
                  "annotated genes", p, ["S re-derived"], extra={"source_printed_size": 1602})
        elif kind == "reactome":
            tid, rec, recs, why = names_rule(NM, [qname], rx_c)
            for c in cells:
                ctx.record_match(c, rec, "Reactome release 92", "set name (Pagani, as the register transcribes it)")
            p = prov("pagani2026crossspecies", PAGANI_D, pn, {"36 (mouse Methods)": "Jiang et al. 2022 (pathways)"},
                     "Reactome (https://reactome.org/, as Pagani's Methods state): ReactomePathways.gmt and ReactomePathways.txt",
                     "https://download.reactome.org/92/ReactomePathways.gmt.zip; https://download.reactome.org/92/"
                     "ReactomePathways.txt",
                     "Reactome release 92 (files dated 2025-03-27; release 93 is dated 2025-06-17)",
                     "release current at the date: Reactome's archive serves each release; release 92 (2025-03-27) was "
                     "current on 2025-04-17",
                     "every gene the pathway carries in the release's GMT (the pathway and its sub-pathways, as Reactome "
                     "distributes it)", [_rec_short(NM, r) for r in recs], ctx.ref("reactome92_gmt", "reactome92_txt"))
            assert tid, (qname, why)
            p["term"] = {"id": tid, "name": rec["name"]}
            built("PAGANI:" + cells[0], "cmp66_pagani_reactome92_%s" % tid.replace("-", ""), cells,
                  [{"kind": None, "id": None, "symbol": s} for s in rx_mem[tid]],
                  "Reactome 92 %s '%s'" % (tid, rec["name"]), p, ["S re-derived"])
        else:  # gandal_label
            tid, rec, recs, why = names_rule(NM, [qname], lab_c)
            for c in cells:
                ctx.record_match(c, rec, "Gandal 2022 module labels (Fig. 3a / 4a)", "set name (Pagani, as the register "
                                 "transcribes it)")
            p = prov("pagani2026crossspecies", PAGANI_D, pn, {"16": "Gandal et al. 2022, Nature 611:532"},
                     "ref. 16 (Gandal 2022): the module the paper's name reaches among the labels Gandal prints (Fig. 3a / "
                     "4a; register_maps/gandal2022_module_labels.json), its members from Supplementary Data 5", g_url,
                     "n/a (article supplement)", "n/a", "every gene of the module (Supplementary Data 5, Gene_Level)",
                     [_rec_short(NM, r) for r in recs], gref + ctx.ref("gandal2022_labels"), {"note": gnote})
            if tid is None:
                not_buildable("PAGANI:" + cells[0], cells,
                              "R-d: %s -- the labels Gandal prints are %s" % (why, "; ".join(
                                  "%s '%s'" % (lab["module"], lab["label"]) for lab in labels["labels"])), p)
                # register v6.7 N6: the near-miss view -- the module whose description in Gandal's own text carries the
                # name's content words (the figure labels are not the only module descriptions the source gives); v6.8 (C):
                # found by content_word_search, its uniqueness asserted (v6.7 had hand-coded the module and its quote)
                srch = content_word_search(gtext, qname)
                assert len(srch["modules_found"]) == 1, (cells[0], "the content-word search must find exactly one module",
                                                         srch["modules_found"])
                mod = next(iter(srch["modules_found"]))
                quote = srch["sentences"][mod][0]
                srch["same_module_as_v6_7_hand_pick"] = mod == NM_PAGANI_V67_PICK[cells[0]]
                mm2 = next(m for m in size if m.split("_")[0] == mod[4:])
                assert any(x.split("_")[0] == mod[4:] for x in mods), (mod, "one of Gandal's 24 ASD-DE modules")
                near_miss_built("PAGANI:" + cells[0], cells, "nm67_pagani_gandal2022_%s" % mod,
                                [{"kind": "ensembl", "id": r["ensembl_gene_id"], "symbol": r["hgnc_symbol"] or r["external_gene_name"]}
                                 for r in gm if r["WGCNA_module"] == mm2],
                                "Gandal 2022 %s, the module its Results text describes with '%s''s words (near-miss view)"
                                % (mod, qname),
                                dict(p, reading=("a NOTE READING (v6.11 wording; v6.7 N6 called it a near-miss name source): the "
                                                 "cited source's own module -- ref. 16, Gandal 2022, the reference Pagani cites -- "
                                                 "reached through Gandal's Results text, not its printed label: Pagani's '%s' is no "
                                                 "label Gandal's figures print (R-d, the primary record); Gandal's text describes %s "
                                                 "as '%s' -- every content word of the name (plural / singular normalised) occurs in "
                                                 "that description; v6.8 (C): the module is the one a content-word search of "
                                                 "Gandal's article finds (exactly one, asserted); Pagani used 'co-expression "
                                                 "modules of known biological function (n = 10)' (quoted)" % (qname, mod, quote)),
                                     **{"R-a_source": ("ref. 16 (Gandal 2022, the reference Pagani cites): the module whose "
                                                       "description in Gandal's Results text holds every content word of the "
                                                       "paper's name (content_word_search: exactly one module, asserted) -- a note "
                                                       "/ text route, not a printed label (no label of Fig. 3a / 4a is reached: "
                                                       "R-d); its members from Supplementary Data 5 (v6.11: this text replaces "
                                                       "the primary record's 'the module the paper's name reaches among the "
                                                       "labels Gandal prints')")},
                                     gandal_quote=quote, content_word_search_v6_8=srch, pagani_quote=pq, figure_label=next(
                                         lab["label"] for lab in labels["labels"] if lab["module"] == mod),
                                     term={"module": mod, "wgcna_module": mm2, "n_genes": size[mm2]},
                                     files=p["files"] + ctx.ref("gandal2022_html", "pagani_text")))
                continue
            mm = next(m for m in size if m.split("_")[0] == tid[4:])
            p["term"] = {"module": tid, "label": rec["name"], "wgcna_module": mm, "n_genes": size[mm]}
            built("PAGANI:" + cells[0], "cmp66_pagani_gandal2022_%s" % tid, cells,
                  [{"kind": "ensembl", "id": r["ensembl_gene_id"], "symbol": r["hgnc_symbol"] or r["external_gene_name"]}
                   for r in gm if r["WGCNA_module"] == mm],
                  "Gandal 2022 %s '%s'" % (tid, rec["name"]), p, ["S re-derived"])
    n_built = sum(1 for e in out if e["outcome"] == "built")
    nm_built = [e for e in nm_out if e["outcome"] == "built"]
    view = {"what": ("register DRAFT v6.7 (1) (the orchestrator under the operator's standing delegation): the registered "
                     "SECONDARY VIEW 'near-miss comparator', fixed before G1 opens and declared as chosen knowing which cells "
                     "it affects -- for the cells whose comparator is not buildable, a comparator from a near-miss source (not "
                     "the cited reference) or reached by a declared name normalisation; it never changes a primary status, and "
                     "it is labelled '%s' wherever it is reported. DRAFT v6.8 (B S1, post hoc, declared): asdM12 (BUCH-E-ASDdown-"
                     "S1 ... S4) joins the view -- the cited source's list reached through a name bridge from a reference not "
                     "cited for the set (Parikshak 2013). DRAFT v6.9 (C5, post hoc, declared): 'ASD rare de novo' (BUCH-E-RDNV-S1 "
                     "... S4, descriptor cells) joins it by reading (iii) applied uniformly -- Sanders 2019's ASD65, reached by a "
                     "semantic reading of its column note; C3: the label adds '/ name bridge'. DRAFT v6.10 (post hoc, "
                     "declared): the label adds '/ note reading' -- a list of the cited source reached through a note or its "
                     "text, not its title or printed label (RDNV; PAG-C9 / C10, filed under 'near-miss source' by v6.7 ... "
                     "v6.9 although Gandal 2022 is the reference Pagani cites)" % NEAR_MISS_LABEL),
            "label": NEAR_MISS_LABEL, "status_built": NM_STATUS,
            "normalisation": {k: {"what": v[0], "applies_to": "this set's names only"} for k, v in NORMALISE_V67.items()},
            "n_sets": len(nm_out), "n_built": len(nm_built), "n_not_buildable": len(nm_out) - len(nm_built),
            "n_cells_built": sum(len(e["cells"]) for e in nm_built),
            "n_cells_not_buildable": sum(len(e["cells"]) for e in nm_out if e["outcome"] != "built"),
            "sets": nm_out}
    return {"what": ("register DRAFT v6.6 (B2 / C5; the orchestrator under the operator's standing delegation) as revised by "
                     "DRAFT v6.7 (N1: asdM12 built; (2) the uniform archive rule: RGD, CTD and SFARI (by the served release "
                     "label, N2) re-pinned; (1) the near-miss view) and DRAFT v6.8 (B S1: asdM12 not buildable in the primary "
                     "view by R-d applied uniformly, its set the near-miss view's comparator; C: the PAG content-word search, "
                     "CTD's archive alternative) and DRAFT v6.9 (C5: Buch's 'ASD rare de novo' not buildable in the primary "
                     "view by reading (iii) applied uniformly, Sanders 2019's ASD65 the near-miss view's comparator): the "
                     "comparators of Buch's non-GO sets and Pagani's sets, "
                     "built before the freeze by register 1.6's resolution rule R-a ... R-e and its application notes; per "
                     "set: the outcome, the source, URL, release and the rule's outcome for it, the threshold, the names and "
                     "the name rule's records, the access date and every input's sha256 (the per-set JSON holds the full "
                     "record)"),
            "rule": {"text_sha256": RULE_SHA, "written_utc": RULE_UTC, "module": "arcs/audit/src_register/s_build_v66.py"},
            "status_built": COMP_STATUS, "status_not_buildable": NOT_BUILDABLE,
            "n_sets": len(out), "n_built": n_built, "n_not_buildable": len(out) - n_built,
            "n_cells_built": sum(len(e["cells"]) for e in out if e["outcome"] == "built"),
            "n_cells_not_buildable": sum(len(e["cells"]) for e in out if e["outcome"] != "built"),
            "sets": out, "near_miss_view_v6_7": view}
