"""WP4 (RUN_PLAN.md v3.1 §11, §18 WP4; FROZEN): the fixed layout of gate G2 shared by the material stage
(wp4_material.py, phase 2), the gated set builder (wp4_sets.py), the loaders (wp4_sources.py) and the reproduction
wiring (wp4_repro.py): runner-built paths, object keys, the identity references, the declarations every G2 carrier is
read with, and the status vocabulary. Nothing here opens a carrier; Roots.production() names paths only.

DRAFT READINGS. The declarations below that no frozen text pins are the readings of the DRAFT
arcs/audit/RUN_PLAN_amend_4.md (R51 ...; written in WP4 phase 1, BEFORE any G2 target material was opened, and not
frozen). Each constant names its reading. Until the orchestrator freezes the amendment, the material stage refuses a
production run (DRAFT_GUARD below); scratch runs (tests, the phase-1 demonstration) are unaffected.

Paths (R18 RUN_PLAN.md:826-847; fetch_extract FE10):
  records   <main repo>/arcs/audit/register_maps/post_freeze/G2/<key>.json   one R18 record per object (committed)
  manifest  <main repo>/arcs/audit/register_maps/post_freeze/G2/wp4_material_manifest.json   (never overwritten;
            later versions wp4_material_manifest.<n>.json)
  sets      <main repo>/arcs/audit/register_sets/post_freeze/G2/<set_id>.json + MANIFEST_G2.json   (R18)
  objects   <main repo>/artifacts/audit/wp4/G2/<key>/<key>_extract.json   (§8 step 5; artifacts/ is git-ignored)
  control   <main repo>/arcs/audit/run_manifests/material/G2/   deletion requests (FE10), the R13 / R17 records
  logs      <main repo>/artifacts/audit/material_logs/G2/<key>.log
  data      E:/data/asdg (pinned local copies stay where the pre-freeze identity record found them; downloads go to
            E:/data/asdg/<key>/carrier<ext>)
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
GATE = "G2"

# the draft amendment these readings come from (its sha256 is pinned at the freeze; until then production refuses)
AMEND4_REL = "arcs/audit/RUN_PLAN_amend_4.md"
# RUN_PLAN_amend_4.md v3, FROZEN by the orchestrator 2026-10-16 (commit 1c5143d; its FROZEN.txt line)
AMEND4_FROZEN_SHA256 = "d3f7275364847de88069f1ff815093adc1ca3dacf8f414eba98179920e6b4ac1"
FROZEN_REL = "arcs/audit/FROZEN.txt"
PRODUCTION_DATA = Path("E:/data/asdg")
DRAFT_GUARD = ("refused: RUN_PLAN_amend_4.md (the WP4 readings R51 ...) is a DRAFT; the G2 material stage runs in "
               "production only after the orchestrator freezes it (wp4_layout.AMEND4_FROZEN_SHA256)")
# RUN_PLAN_amend_5.md (DRAFT, POST-EXPOSURE, format-only: R54', R58', R61', the line-130 label, the path-screen
# exemption): the code below implements its readings; production refuses until the orchestrator freezes it and pins
# its sha256 here (AMEND5_FROZEN_SHA256) and in FROZEN.txt
AMEND5_REL = "arcs/audit/RUN_PLAN_amend_5.md"
# RUN_PLAN_amend_5.md v2, FROZEN by the orchestrator 2026-10-21 (commit f6f8cbf; its FROZEN.txt line)
AMEND5_FROZEN_SHA256: str | None = "554f4e09a0f9e72141235d53f810ba300200d1c210e14692e50e372355ab1257"
DRAFT_GUARD5 = ("refused: RUN_PLAN_amend_5.md (the post-exposure format-only readings R54', R58', R61') is a DRAFT; the "
                "G2 material stage runs in production only after the orchestrator freezes it "
                "(wp4_layout.AMEND5_FROZEN_SHA256)")
# amend_5 E1: the path screen's declared exemption - the publisher file names of pinned GROUP-LEVEL copies (ENIGMA
# Toolbox summary statistics), each with the pinned copy's sha256; the name is exempt only while the bytes are these
SCREEN_EXEMPT = {
    "liu_t3_cortthick": ("asd_meta-analysis_case-controls_CortThick.csv",
                         "ee076971be6688bc99106fce4a7198a3bd927d183adb245f9810d6f71efe4f29"),
    "liu_t3_subvol": ("asd_meta-analysis_case-controls_SubVol.csv",
                      "b2b0b02c260ec87c6ab22f40e6162ab8a475dab373390be1edd465910ca62066"),
}
# amend_5 R58' (d): the paper's script reads 'mmc2(1).xlsx' (a browser's duplicate-download suffix on the Sadeghi
# supplement's name); it is the Sadeghi workbook only if the staged file is the pinned Sadeghi copy (sha256 equal)
SADEGHI_DUP_NAME = __import__("re").compile(r"^mmc2 ?\(\d+\)\.xlsx$")
# amend_5 L130: the paper's script writes gw_asd into the MDD TPRS files (literature_gwas_analysis.R line 130); the
# script runs as published and every row derived from an MDD TPRS file carries this label
LINE130_LABEL = "the paper's script writes the ASD values into the MDD TPRS files (line 130)"
# amend_5 R54' changes what these targets' objects hold; saved objects are never overwritten (FE9 / FE18), so the
# amended extraction is saved under <key>_a5 (the manifest entry keeps <key> and names the object by object_key, as
# R17's run-indexed objects do); the carrier already on disk is used, never fetched again
AMEND5_OBJECT_SUFFIX = "_a5"
AMEND5_OBJECT_KEYS = ("giacomel_xlsx_93de089", "giacomel_xlsx_c022a29", "pretzsch_etable13")
# amend_5 v2 (asdg-skeptic A; RUN_PLAN §18 :1812): R61', R54' and R58' (d) could only apply to material already
# opened, so their computation is a SECOND version beside the frozen primary status (§17 (4) "both versions are
# reported"); it never enters the interim headline population or a tested-only denominator
VERSION_PRIMARY = "primary"
VERSION_AMEND5 = "amend5"
VERSION_ENV = "A1_G2_VERSION"           # the claim passes' version (run.py builds the G2 sources from the production
#                                         roots; the version travels in the roots spec to every worker)
AMEND5_VERSION_LABEL = "post-exposure version (amend_5)"
AMEND5_PE_READINGS = ("R61' (Pretzsch '.' = '-')", "R54' (pallidus alias; unmarked Subcortical -> left)",
                      "R58' (d) (mmc2(<n>).xlsx = the pinned Sadeghi copy)")
AMEND5_RERUN_TAG = "amend5"             # run.py --rerun-tag: results/a1_run/rerun_amend5/G2/<pass>/

# ---- status vocabulary (TSV / plan strings and the WP4 phase-1 additions, each cited) --------------------------------
STATUS_PENDING = "not run (phase 2 G2 material pending)"
STATUS_NOT_FINAL = "not run (phase 2 G2 material not final: the G2 manifest is partial)"
STATUS_MAP_CHANGED = "not auditable (map changed)"                                   # RUN_PLAN §17 :1703-1704
STATUS_OBJECT_CHANGED = "refused: a G2 phase-2 object differs from the G2 manifest (sha256)"
STATUS_STAGE_REFUSED = "not run (the G2 material stage refused this object: %s)"
STATUS_NO_LOADER = "not run (no WP4 loader binds this row's map text)"
STATUS_QUARANTINE = "refused: a source path lies under the quarantine (RUN_PLAN section 8 step 6)"
# R53 (draft): Patel eTable 4
STATUS_PATEL_LAYOUT = "not auditable (definition not applicable: the declared eTable 4 layout not matched)"
# R54 (draft): Giacomel's sheets
STATUS_GIA_LAYOUT = "not auditable (definition not applicable: the declared Giacomel sheet layout not matched)"
# R59 (draft): Liu T3's ENIGMA Toolbox tables
STATUS_ENIGMA_LAYOUT = "not auditable (definition not applicable: the declared ENIGMA Toolbox layout not matched)"
# R60 (draft): Hansen's shipped files
STATUS_HANSEN_LAYOUT = "not auditable (definition not applicable: the declared Hansen file layout not matched)"
STATUS_CAMMOUN = ("not auditable (definition not applicable: the Cammoun scale033 order could not be matched to the "
                  "DK names)")
# R61 (draft): Pretzsch's derived eTable13 CSV
STATUS_PRE_LAYOUT = "not auditable (definition not applicable: the declared eTable13 layout not matched)"
# R55 / R56 (draft): Giacomel's repository files
STATUS_LIST_LAYOUT = "not auditable (S undefined: the declared repository list layout not matched)"
STATUS_GEDAR_LAYOUT = "not computable (the paper's GEDAR map layout not matched)"
STATUS_WEIGHT_COLUMN = "not computable (no declared weight column in the repository list)"
# R57 (draft): the Sadeghi DEG workbook
STATUS_SADEGHI_ABSENT = "not computable (the Sadeghi DEG workbook is not under the declared folder and not obtainable)"
# R17 fallback (RUN_PLAN.md:822-824, verbatim)
STATUS_R17 = "not auditable (definition not applicable: the paper's code not runnable here)"
# 2026-10-21 (run 5): a status may blame the paper or a layout only when that specific check ran and failed; a
# failure before it (a stage, an identity, an upstream object, our parameter step) reads this instead
STATUS_UPSTREAM = "refused (stage failed upstream)"
# R13 (RUN_PLAN.md:722-726): the bicor check must exist before any G2 map is read
STATUS_R13_MISSING = ("refused (preflight: R13's bicor check record is absent or not passed; RUN_PLAN.md:722 'before "
                      "this audit reads any G2 map')")
STATUS_PREFLIGHT = "refused (preflight: a check that touches no carrier failed; no carrier was touched)"

# ---- object keys ------------------------------------------------------------------------------------------------
PATEL_KEY = "patel_etable4"
GIA_GOV_KEY = "giacomel_xlsx_93de089"           # downloaded; governs (claims_register.md:1457-1459)
GIA_CMP_KEY = "giacomel_xlsx_c022a29"           # the local copy compared (count of differing cells only)
HANSEN_CT_KEY = "hansen_enigma_ct"
HANSEN_PC1_KEY = "hansen_gene_pc1"
HANSEN_PRED_KEY = "hansen_local_biol_predictors"
HANSEN_INFO_KEY = "hansen_cammoun_info"
LIU_CT_KEY = "liu_t3_cortthick"
LIU_SV_KEY = "liu_t3_subvol"
PRE_KEY = "pretzsch_etable13"
LEY_IMAGES = (777428, 777429, 777430)
LEY_LH_KEY = {777428: "leyhausen_777428_lh", 777429: "leyhausen_777429_lh", 777430: "leyhausen_777430_lh"}
LEY_VOL_KEY = {777428: "leyhausen_777428_vol", 777429: "leyhausen_777429_vol", 777430: "leyhausen_777430_vol"}
LEY_DECODER_KEY = {777428: "leyhausen_decoder_777428", 777429: "leyhausen_decoder_777429",
                   777430: "leyhausen_decoder_777430"}
FS_KEY = "freesurfer741_fsaverage_annot"          # fetch_extract.freesurfer_target's default key (R16)
HCP_VOL_KEY = "hcpmmp1_volume"
HCP_LIST_KEY = "hcpmmp1_labels"
HCP_META_KEY = "hcpmmp1_figshare_metadata"
SADEGHI_KEY = "sadeghi2022_deg"
R17_SCRIPT_KEY = "giacomel_literature_gwas_script"
R17_AHBA_KEY = "giacomel_ahba_no_norm"
R17_HPA_KEY = "giacomel_ahpa_brain"
MANIFEST_NAME = "wp4_material_manifest.json"
PARTIAL_PREFIX = "wp4_material_manifest.partial"
MANIFEST_SCHEMA = "a1_wp4_material_manifest_v1"
SET_MANIFEST_NAME = "MANIFEST_G2.json"

# ---- the pre-freeze identity record (IDENTITY_prefreeze.json, frozen 6cbde63e...): object fields, exact -------------
IDENTITY_OBJECT = {
    PATEL_KEY: "eTable 4 (supplement PDF p. 26)",
    GIA_GOV_KEY: "ENIGMA_structural_organised.xlsx @93de089 (Thickness / Subcortical / MDD; governs)",
    GIA_CMP_KEY: "ENIGMA_structural_organised.xlsx @c022a29 (compared with 93de089; local copy)",
    HANSEN_CT_KEY: "enigma_ct.csv (y: column asd)",
    HANSEN_PC1_KEY: "gene_pc1.csv (component)",
    LIU_CT_KEY: "LIU-T3 y: ENIGMA Toolbox asd meta-analysis CortThick",
    LIU_SV_KEY: "LIU-T3 y: ENIGMA Toolbox asd meta-analysis SubVol",
    PRE_KEY: "eTable13 loadings (Supplement 2; Europe PMC supplementary archive; derived CSV on disk)",
    LEY_LH_KEY[777428]: "NeuroVault 12301 image 777428 (MSD)",
    LEY_LH_KEY[777429]: "NeuroVault 12301 image 777429 (PF)",
    LEY_LH_KEY[777430]: "NeuroVault 12301 image 777430 (RF)",
}
# R62 (draft): Leyhausen's map is the left fsaverage GIFTI (claims_register.md §3.8, TSV rows 626-692 'map'); §11
# (RUN_PLAN.md:1466) lists the VOLUMES' sha256s under the name "lh GIFTIs". Both are held to their references.
LEY_LH_SHA256 = {777428: "5889a68733b8d541d7969bdfa8d31c859d75f646a5586839d4a539c71f2680e4",   # TSV 'map' fields
                 777429: "1299426288ba4938872621c2bac06dac39bcf2ec473dd284e5c2ef41a18fc47a",
                 777430: "e6478fdab840f63ba2df5e72d817cfe388d8eecf003847cd027a238cb2344934"}
LEY_VOL_SHA256 = {777428: "3c5dfc21681e2aa279623ab7d6d2f31e98ee1fbd05ca0a4e8fb58e7e76708aff",   # RUN_PLAN.md:1466
                  777429: "4429d1da1981770588e1c37e072d67d51e7843694aa92462c0ac24d77a6a561d",
                  777430: "9436a9e9061aced63eb0fcd3f54212f399722ffe8e042d0e078e3ede9932119e"}
LEY_SURFACE_FIELD = "surface_left_file"          # the NeuroVault metadata field of the lh GIFTI probe
LEY_VOLUME_FIELD = "file"

# R60 (draft): registered sha256 PREFIXES of files the incorporated drafts name (claims_register.md:59-61; 64-bit
# prefixes, RUN_PLAN_amend_3 R47's precedent "a 64-bit prefix detects change"); the local paths the drafts give
PREFIX_PINS = {
    HANSEN_PRED_KEY: (r"E:\data\asdg\hansen2022local\repo\data\local_biol_predictors.csv", "d73853619b543bf9",
                      "register_work/hansen2022local.md section 1 row 4"),
    HANSEN_INFO_KEY: (r"E:\data\asdg\hansen2022local\external\cammoun2012\MNI152NLin2009aSym"
                      r"\atl-Cammoun2012_space-MNI152NLin2009aSym_info.csv", "348246e7d997c395",
                      "register_work/hansen2022local.md section 1 row 6"),
    SADEGHI_KEY: (r"E:\data\asdg\giacomel2026cartography\external\sadeghi2022_csbj\mmc2.xlsx", "ef4aee97e746b5e4",
                  "register_work/giacomel2026cartography.md section 1 row 13"),
}
# §11 (RUN_PLAN.md:1453-1455): the Sadeghi workbook's folder, checked by listing its names IN MEMORY
SADEGHI_FOLDER = r"E:\data\asdg\giacomel2026cartography\external"
SADEGHI_DECLARED_REL = ("sadeghi2022_csbj", "mmc2.xlsx")      # the declared relative path (draft row 13)
# R57 (draft): if absent, the Europe PMC supplementary archive of PMC9428860 (the draft's source), member '*mmc2.xlsx'
SADEGHI_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9428860/supplementaryFiles"
SADEGHI_MEMBER_SUFFIX = "mmc2.xlsx"
# R17 inputs (draft rows 5, 11 of the Giacomel draft): repository paths at e045bc5 and the registered prefixes
R17_INPUT_PATHS = {R17_AHBA_KEY: ("data/AHBA/AHBA_data_no_norm.csv", "4b4ace458d392366"),
                   R17_HPA_KEY: ("data/AHBA/AHPA_mrna_brain.tsv", "1b85136a7dc582ad")}
R17_SCRIPT_SUFFIX = "/literature_gwas_analysis.R"                # claims_register.md:1471 (one tree entry, R58)
# R58 (f) (draft): the DEG sets by the TSV's own definition (rows 109-131 set_S: "Supplementary_Data1 (mmc2.xlsx), Dx = ASD
# (20,256 rows) ∩ AHBA ∩ HPA = 3,599 genes, top round(n x thr) by p.value, thr 1 % -> m = 36; weights = logFC")
DEG_SHEET_RULE = r"^(supplementarydata|supplementary|data|sheet)0*1(?![0-9])"
DEG_HEADERS = ("Dx", "p.value", "logFC")
DEG_SYMBOL_ALTERNATIVES = ("gene", "Gene", "gene_name", "GeneSymbol", "symbol", "Symbol", "hgnc_symbol",
                           "external_gene_name")
DEG_POOL_ASD = 3599                       # TSV row 109 set_S (the corroboration of the pool)
HPA_SYMBOL_ALTERNATIVES = ("Gene", "Gene name", "gene", "gene_name", "symbol")
STATUS_DEG = "not computable (the post-mortem DEG set: the declared workbook / pool layout not matched)"
STATUS_DEG_POOL = "not computable (the post-mortem DEG set: the AHBA x HPA pool of ASD is not the registered 3,599)"

# R58 (f) v2 (asdg-skeptic B5): S re-derived by the script's run; the TSV definition is the check
STATUS_DEG_CHECK = ("not computable (the post-mortem DEG set: the script's set does not match the registered "
                    "definition - m or the 3,599 ASD pool)")
STATUS_DEG_NOT_FOUND = "not computable (the post-mortem DEG set: the script wrote no identifiable list for this cell)"
# RUN_PLAN_amend_4 v3, answer to Q3: a FORMAT-ONLY adaptation of the parser that locates the script's DEG lists (file
# names, header tokens, delimiters), recorded as a deviation labelled post-exposure; R58 (f)'s content check (m, the
# ASD pool 3,599) unchanged. The adaptation is a JSON file the operator writes under control/G2/ after seeing the
# script's output; its keys are exactly DEG_ADAPTATION_KEYS ("why" free text, kept by sha256 only).
DEG_ADAPTATION_NAME = "deg_list_adaptation.json"
DEG_ADAPTATION_KEYS = ("name_regex", "symbol_header", "weight_header", "delimiter", "why")
DEG_DEVIATION_LABEL = ("post-exposure deviation (RUN_PLAN_amend_4 v3 Q3): a format-only adaptation of the parser that "
                       "locates the script's DEG lists; the content check unchanged")
GH_COMMIT_API = "https://api.github.com/repos/{repo}/commits/{commit}"
R17_COMMIT_KEY = "gia_commit_e045bc5"
R17_RVERSIONS_KEY = "r17_rhub_rversions"
R17_BIOC_KEY = "r17_bioc_config"
R17_DECL_KEYS = {"renv.lock": ("r17_decl_renv_lock", ".json"), ".R-version": ("r17_decl_r_version", ".txt")}

# ---- repositories (commits as the register names them) -------------------------------------------------------------
GIA_REPO = "alegiac95/METAXCAN_TWAS_ANALYSIS"
GIA_93DE089 = "93de089b614f72bda25f441518ad04b1e938fb9b"
GIA_C022A29 = "c022a29bb74009f870a14abc1e0e6c1c8fcfb81c"
GIA_E045BC5 = "e045bc51961b0425f51bbdf54672d59222cfa8b9"
GIA_EDA33AB = "eda33abddd5acd396caa0ace2817a0bcd427cfe5"
GIA_XLSX_PATH = "data/ENIGMA/ENIGMA_structural_organised.xlsx"
# R55 (draft): the raw form of a pinned blob URL (identity is the git blob, independent of the URL)
RAW_URL = "https://raw.githubusercontent.com/{repo}/{commit}/{path}"
TREE_API = "https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1"
# claims_register.md §2.3 / TSV rows 91-131: the list files per cell family (thresholds 1, 5, 10 %)
GIA_ASD_LISTS = {f"ASD_{scheme}_genes_thr_{t}": f"results/ASD/ASD_{scheme}_genes_thr_{t}.tsv"
                 for scheme in ("top", "top_pos", "top_neg") for t in (1, 5, 10)}
GIA_MDD_PATHS_REL = "arcs/audit/register_maps/gia_mdd_paths.json"
GIA_MDD_PATHS_SHA256 = None    # read through the freeze manifest (register_maps/*.json are in it): see wp4_material

# ---- Patel eTable 4 (R53, draft) -------------------------------------------------------------------------------
PATEL_PAGE_INDEX = 25            # "PDF p. 26" (RUN_PLAN.md:1469; claims_register.md:1449) = page index 25
PATEL_HEADER_WORD = "Estimate"   # the TSV's "column Estimate"
PATEL_N = 34                     # "34 left DK values"

# ---- Giacomel's workbook (R54, draft) ------------------------------------------------------------------------------
GIA_SHEETS = {"thickness": "Thickness", "subcortical": "Subcortical"}     # RUN_PLAN.md:1470 (exact names)
GIA_HEADERS = ("ASD", "MDD")                                               # TSV 'map' "column ASD" / "column MDD"
GIA_SUB_ORDER = ("accumbens", "amygdala", "caudate", "hippocampus", "pallidum", "putamen", "thalamus")   # TSV rows 92..
# the paper's GEDAR subcortical rows (atlas order; register_work/giacomel2026cartography.md 'Defect'), by abagen DK name
GEDAR_SUB_ATLAS_ORDER = ("thalamusproper", "caudate", "putamen", "pallidum", "accumbensarea", "hippocampus", "amygdala")

# ---- Giacomel repository lists (R55, draft) ------------------------------------------------------------------------
LIST_SYMBOL_HEADER = "gene_name"                 # TSV set_S: "HGNC symbols (gene_name)"
LIST_ENSEMBL_HEADER = "gene"                     # draft: "Ensembl in gene" (used first if present, §1.6)
LIST_WEIGHT_HEADERS = ("z_mean", "zscore")       # R55: the TWAS z column, first found in this order
LIST_WEIGHT_RULE = ("RUN_PLAN_amend_4 R55 (draft): the weight column is the first of the exact headers z_mean "
                    "(S-MultiXcan's mean z) and zscore (S-PrediXcan's z) the list carries; no other column is read; "
                    "a list carrying neither reads 'not computable (no declared weight column ...)' for the "
                    "weighted functionals only")

# ---- Liu T3 (R59, draft) ----------------------------------------------------------------------------------------------
ENIGMA_LABEL_HEADER = "Structure"
ENIGMA_VALUE_HEADER = "d_icv"
ENIGMA_N_CT, ENIGMA_N_SV = 68, 16                # 68 DK rows; 16 SubVol rows incl. both lateral ventricles (prereg :298)

# ---- Hansen (R60, draft) ----------------------------------------------------------------------------------------------
HANSEN_N_ROWS = 68
HANSEN_CT_SHAPE = (68, 13)                       # register_work/hansen2022local.md section 0: "shape (68 x 13)"
HANSEN_ASD_INDEX = 2                             # TSV row 624: "column asd (index 2 ...)"
HANSEN_LEFT_ROWS = tuple(range(34, 68))          # "left rows (Cammoun 2012 scale033 order 35-68)" (0-based 34..67)
HANSEN_N_PREDICTORS = 7                          # draft row 4: "7 z-scored maps"
CAMMOUN_HEADERS = ("label", "scale", "hemisphere", "structure")
CAMMOUN_SCALE, CAMMOUN_STRUCTURE = "scale033", "cortex"

# ---- Pretzsch (R61, draft) ----------------------------------------------------------------------------------------------
PRE_N_LEFT = 180
PRE_FEATURE_TOKENS = {"CT": ("ct", "thickness"), "SA": ("sa", "surface+area")}   # wp4_read._feature_of
PRE_MAP_PREFIX = {"CT": "y_CT:", "SA": "y_SA:"}  # TSV rows 523-594 'map' (the binding text)

# ---- R15 (draft R52): figshare 3501911 ----------------------------------------------------------------------------------
HCP_ARTICLE_API = "https://api.figshare.com/v2/articles/3501911"
HCP_VOLUME_NAME = "HCP-MMP1_on_MNI152_ICBM2009a_nlin.nii.gz"      # claims_register.md:1036-1037 (exact)
HCP_LABEL_EXT = ".txt"
HCP_N_LEFT = 180

# ---- R16 (draft R51): the FreeSurfer 7.4.1 directory and the fallback order of official artefacts -------------------
FS_DIR = "https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.4.1/"
FS_TARBALLS = ("freesurfer-linux-ubuntu22_amd64-7.4.1.tar.gz", "freesurfer-linux-ubuntu20_amd64-7.4.1.tar.gz",
               "freesurfer-linux-ubuntu18_amd64-7.4.1.tar.gz", "freesurfer-linux-centos8_x86_64-7.4.1.tar.gz",
               "freesurfer-linux-centos7_x86_64-7.4.1.tar.gz")
FS_PROBE = {"content_length": 9484461482, "last_modified_date": "2023-06-27"}   # R16 :771-773 (2026-10-01 probe)

# ---- Leyhausen's decoder (R63, draft): R45's URL and declared columns, the paper's nominal p < .01 ------------------
LEY_DECODER_P = 0.01
LEY_PAPER_LIST_N = {777428: 480, 777429: 382, 777430: 322}      # TSV 'reproduction' (the paper's list sizes)

# ---- the TSV map texts that bind a row to its G2 object ----------------------------------------------------------
MAP_BINDINGS = (
    ("patel", "eTable 4, column Estimate"),
    ("giacomel_thickness", "sheet Thickness, column ASD"),
    ("giacomel_thickness_mdd", "sheet Thickness, column MDD"),
    ("giacomel_subcortical", "sheet Subcortical, column ASD"),
    ("giacomel_subcortical_mdd", "sheet Subcortical, column MDD"),
    ("liu_t3", "ENIGMA-ASD meta-analysis d_icv: cortical thickness"),
    ("pretzsch_CT", "y_CT:"),
    ("pretzsch_SA", "y_SA:"),
    ("hansen", "data/enigma_ct.csv, column asd"),
    ("leyhausen_777428", "NeuroVault 12301 image 777428"),
    ("leyhausen_777429", "NeuroVault 12301 image 777429"),
    ("leyhausen_777430", "NeuroVault 12301 image 777430"),
)


# ---- file pins of reference files the stage checks first (R50's ordering applied to G2) -----------------------------
def _pins_production() -> dict:
    from . import ahba_builds as AB
    from . import wp3_layout as W3
    base = dict(W3._pins_production())
    keep = ("dk_info", "hgnc", "gamba", "brainspan_expr", "brainspan_rows", "brainspan_cols")
    out = {k: base[k] for k in keep}
    # the DK atlas volume abagen 0.1.3 bundles (RUN_PLAN.md:652 R10's pin; R15's Glasser -> DK majority rule)
    out["dk_atlas"] = ("env/venv/Lib/site-packages/abagen/data/atlas-desikankilliany.nii.gz", "main",
                       AB.ATLAS["dk"]["nii_sha256"], None)
    return out


@dataclasses.dataclass(frozen=True)
class Roots:
    repo: str            # register files (TSV, register_sets, register_maps) are read from here
    data: str            # carriers and public reference files (E:/data/asdg)
    artifacts: str       # fetch_extract artifacts root: objects at <artifacts>/G2/<key>/<key>_extract.json
    records: str         # register_maps/post_freeze (R18)
    sets: str            # register_sets/post_freeze (R18)
    control: str         # run_manifests/material (FE10)
    logs: str
    quarantine: str
    ahba: str
    builds: str
    identity_json: str
    identity_frozen: bool
    pins: tuple
    prefix_pins: tuple = ()                  # ((key, (path, sha256 prefix, source)), ...)
    sadeghi_folder: str = ""
    scratch: bool = False
    ley_sha: tuple = ()                      # ((image, lh GIFTI sha256, volume sha256), ...); production: R62's pins
    mdd_paths_json: str = ""                 # scratch: a stand-in of register_maps/gia_mdd_paths.json
    r17_prefix: tuple = ()                   # ((key, registered sha256 prefix), ...) of the R17 inputs
    hcp_build: str = ""                      # R38's output directory (the perdonor-hcpmmp1 build)
    version: str = "primary"                 # amend_5 v2: "primary" or "amend5" (the post-exposure version)

    @classmethod
    def production(cls, repo: Path | None = None, out_repo: Path | None = None, version: str | None = None) -> "Roots":
        import os
        version = version or os.environ.get(VERSION_ENV) or VERSION_PRIMARY
        if version not in (VERSION_PRIMARY, VERSION_AMEND5):
            raise ValueError("Roots.production: an unknown G2 version")
        repo = Path(repo or REPO)
        # 2026-10-21 (run 6): the post-freeze records, sets and objects live in the MAIN tree only (untracked; a
        # worktree holds none), so a worktree's out_repo resolves to its main tree: run.py builds the G2 sources with
        # out_repo = its own (worktree) REPO, which made every G2 row read "material pending"
        out = main_repository(Path(out_repo or repo))
        data = Path("E:/data/asdg")
        return cls(repo=str(repo), data=str(data), artifacts=str(out / "artifacts/audit/wp4"),
                   records=str(out / "arcs/audit/register_maps/post_freeze"),
                   sets=str(out / "arcs/audit/register_sets/post_freeze"),
                   control=str(out / "arcs/audit/run_manifests/material"),
                   logs=str(out / "artifacts/audit/material_logs"), quarantine=str(data / "_quarantine"),
                   ahba=str(repo / "artifacts/ahba"), builds=str(repo / "artifacts/ahba/a1_builds"),
                   identity_json=str(repo / "arcs/audit/register_maps/IDENTITY_prefreeze.json"), identity_frozen=True,
                   pins=tuple(sorted(_pins_production().items())),
                   prefix_pins=tuple(sorted((k, tuple(v)) for k, v in PREFIX_PINS.items())),
                   sadeghi_folder=SADEGHI_FOLDER, scratch=False,
                   ley_sha=tuple((i, LEY_LH_SHA256[i], LEY_VOL_SHA256[i]) for i in LEY_IMAGES),
                   r17_prefix=tuple(sorted((k, v[1]) for k, v in R17_INPUT_PATHS.items())),
                   hcp_build=str(repo / "artifacts/ahba/a1_builds/perdonor-hcpmmp1"), version=version)

    @classmethod
    def scratch_layout(cls, root: Path, *, pins: dict, identity_json: Path, prefix_pins: dict, ley_sha: dict,
                       repo: Path | None = None, builds: Path | None = None, mdd_paths_json: Path | None = None,
                       r17_prefix: dict | None = None) -> "Roots":
        root = Path(root)
        repo = Path(repo or REPO)
        return cls(repo=str(repo), data=str(root / "data"), artifacts=str(root / "out/artifacts/audit/wp4"),
                   records=str(root / "out/arcs/audit/register_maps/post_freeze"),
                   sets=str(root / "out/arcs/audit/register_sets/post_freeze"),
                   control=str(root / "out/arcs/audit/run_manifests/material"),
                   logs=str(root / "out/artifacts/audit/material_logs"), quarantine=str(root / "data/_quarantine"),
                   ahba=str(repo / "artifacts/ahba"), builds=str(builds or (repo / "artifacts/ahba/a1_builds")),
                   identity_json=str(identity_json), identity_frozen=False,
                   pins=tuple(sorted((k, tuple(v) + (None,) * (4 - len(v))) for k, v in pins.items())),
                   prefix_pins=tuple(sorted((k, tuple(v)) for k, v in prefix_pins.items())),
                   sadeghi_folder=str(root / "data" / "giacomel_external"), scratch=True,
                   ley_sha=tuple((int(i), v[0], v[1]) for i, v in sorted(ley_sha.items())),
                   mdd_paths_json=str(mdd_paths_json or ""),
                   r17_prefix=tuple(sorted((r17_prefix or {}).items())),
                   hcp_build=str(root / "out/builds/perdonor-hcpmmp1"))

    @property
    def decoder_gate(self) -> str:
        """wp3_decoder's attempt records go to <control>/G2 for this layout."""
        return GATE

    def to_spec(self) -> dict:
        d = dataclasses.asdict(self)
        d["pins"] = [[k, list(v)] for k, v in self.pins]
        d["prefix_pins"] = [[k, list(v)] for k, v in self.prefix_pins]
        d["ley_sha"] = [list(v) for v in self.ley_sha]
        d["r17_prefix"] = [list(v) for v in self.r17_prefix]
        return d

    @classmethod
    def from_spec(cls, d: dict) -> "Roots":
        d = dict(d)
        # asdg-skeptic C10: a scratch layout never points into the production data root (E:/data/asdg)
        if d.get("scratch") and _under(Path(d.get("data", "")), PRODUCTION_DATA):
            raise ValueError("a scratch roots spec whose data root lies under the production data root")
        d["pins"] = tuple((k, tuple(v)) for k, v in d["pins"])
        d["prefix_pins"] = tuple((k, tuple(v)) for k, v in d.get("prefix_pins", ()))
        d["ley_sha"] = tuple(tuple(v) for v in d.get("ley_sha", ()))
        d["r17_prefix"] = tuple(tuple(v) for v in d.get("r17_prefix", ()))
        return cls(**d)

    # ---- paths ----------------------------------------------------------------------------------------------
    def pin(self, key: str) -> tuple[Path, str | None]:
        hits = [v for k, v in self.pins if k == key]
        if len(hits) != 1:
            raise KeyError(key)
        rel, root, sha = hits[0][:3]
        base = main_repository(Path(self.repo)) if root == "main" else \
            {"data": self.data, "ahba": self.ahba, "repo": self.repo}[root]
        return Path(base) / rel, sha

    def pin_bytes(self, key: str) -> int | None:
        hits = [v for k, v in self.pins if k == key]
        if len(hits) != 1:
            raise KeyError(key)
        return hits[0][3] if len(hits[0]) > 3 else None

    def prefix_pin(self, key: str) -> tuple[Path, str, str]:
        hits = [v for k, v in self.prefix_pins if k == key]
        if len(hits) != 1:
            raise KeyError(key)
        return Path(hits[0][0]), str(hits[0][1]), str(hits[0][2])

    def manifest_versions(self) -> list:
        d = Path(self.records) / GATE
        out = []
        if (d / MANIFEST_NAME).exists():
            out.append((1, d / MANIFEST_NAME))
        if d.is_dir():
            for p in d.glob("wp4_material_manifest.*.json"):
                mid = p.name[len("wp4_material_manifest."):-len(".json")]
                if mid.isdigit() and int(mid) > 1:
                    out.append((int(mid), p))
        return sorted(out)

    def latest_manifest(self) -> Path | None:
        v = self.manifest_versions()
        return v[-1][1] if v else None

    def next_manifest_path(self) -> Path:
        v = self.manifest_versions()
        d = Path(self.records) / GATE
        return d / MANIFEST_NAME if not v else d / f"wp4_material_manifest.{v[-1][0] + 1}.json"

    def partial_manifests(self) -> list:
        d = Path(self.records) / GATE
        return sorted(d.glob(PARTIAL_PREFIX + ".*.json")) if d.is_dir() else []

    def record_path(self, key: str) -> Path:
        return Path(self.records) / GATE / f"{key}.json"

    def object_path(self, key: str) -> Path:
        return Path(self.artifacts) / GATE / key / f"{key}_extract.json"

    def set_dir(self) -> Path:
        """The gated sets' folder: G2 (primary) or G2_a5 (amend_5's post-exposure version, never mixed)."""
        if self.version not in (VERSION_PRIMARY, VERSION_AMEND5):
            raise ValueError("Roots: an unknown G2 version")
        return Path(self.sets) / (GATE if self.version == VERSION_PRIMARY else GATE + AMEND5_OBJECT_SUFFIX)

    def fe_roots(self):
        from . import fetch_extract as FE
        return FE.Roots(repo=Path(self.repo), data=Path(self.data), records=Path(self.records),
                        artifacts=Path(self.artifacts), logs=Path(self.logs), control=Path(self.control),
                        quarantine=Path(self.quarantine))


def main_repository(repo: Path) -> Path:
    """The main working tree of `repo` (git's common dir): env/ (gitignored) lives only there, never in a worktree."""
    import subprocess
    r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                       capture_output=True, timeout=60)
    common = Path(r.stdout.decode("utf-8").strip())
    if r.returncode != 0 or common.name != ".git":
        raise RuntimeError("the main repository could not be found through git's common dir")
    return common.parent.resolve()


def _under(p: Path, root: Path) -> bool:
    try:
        Path(p).resolve().relative_to(Path(root).resolve())
        return True
    except (ValueError, OSError):
        return str(p).replace("\\", "/").casefold().startswith(str(root).replace("\\", "/").casefold())


def frozen_check(repo: Path | None = None, pin: str | None = None, rel: str | None = None) -> dict:
    """Amendment 4's freeze, asserted as launch.l5c_amendment asserts amendment 3's (L5a-L5c): the sha256 of the
    worktree file's LF bytes and of its blob at HEAD equal the pin, the blob holds no CR, and FROZEN.txt holds exactly
    one RUN_PLAN_amend_4.md line, with the pin. Returns {"ok", "checks"}."""
    import hashlib
    import subprocess
    repo = Path(repo or REPO)
    rel = rel or AMEND4_REL
    if pin is None:
        pin = AMEND4_FROZEN_SHA256 if rel == AMEND4_REL else AMEND5_FROZEN_SHA256 if rel == AMEND5_REL else None
    checks = {"a pin is set": isinstance(pin, str) and len(pin) == 64}
    p = repo / rel
    raw = p.read_bytes() if p.is_file() else None
    checks["worktree file present"] = raw is not None
    if raw is not None:
        checks["sha256(LF bytes of the worktree file) == pin"] = hashlib.sha256(
            raw.replace(b"\r\n", b"\n")).hexdigest() == pin
    r = subprocess.run(["git", "-C", str(repo), "show", f"HEAD:{rel}"], capture_output=True, timeout=60)
    checks["blob present at HEAD"] = r.returncode == 0
    if r.returncode == 0:
        checks["sha256(blob at HEAD) == pin"] = hashlib.sha256(r.stdout).hexdigest() == pin
        checks["the blob holds no CR"] = b"\r" not in r.stdout
    fz = repo / FROZEN_REL
    lines = fz.read_bytes().decode("utf-8").replace("\r\n", "\n").split("\n") if fz.is_file() else []
    name = rel.rsplit("/", 1)[-1]
    hits = [ln.split() for ln in lines if ln.strip().endswith(" " + name) or ln.strip().endswith("\t" + name)]
    checks[f"FROZEN.txt has exactly one {name} line, with the pin"] = len(hits) == 1 and len(hits[0]) >= 3 and \
        hits[0][1] == pin and hits[0][-1] == name
    return {"ok": all(checks.values()), "checks": checks, "pin": pin}


def production_allowed(repo: Path | None = None) -> tuple[bool, str]:
    """The DRAFT guard: production runs of the G2 material stage (and the G2 sources) need amendment 4 frozen
    (frozen_check). Scratch layouts are never guarded."""
    if AMEND4_FROZEN_SHA256 is None:
        return False, DRAFT_GUARD
    if not frozen_check(repo)["ok"]:
        return False, DRAFT_GUARD
    if AMEND5_FROZEN_SHA256 is None or not frozen_check(repo, rel=AMEND5_REL)["ok"]:      # amend_5 (draft)
        return False, DRAFT_GUARD5
    return True, "frozen"


# ---- identity references (IDENTITY_prefreeze.json; frozen) --------------------------------------------------------------
def identity_records(roots: Roots, read_bytes) -> dict:
    """{object key: {"refs": [identity.ref_from_probe dicts], "local_path": str | None, "url": str | None, ...}} for the
    G2 objects of the pre-freeze identity record. Leyhausen (R62, draft): the lh GIFTI's references are its own local
    probe (selected by the TSV's sha256) and its HEAD Content-Length (the surface_left_file probe); the volume's are its
    local probe (selected by §11's sha256) and NeuroVault's metadata file_size / HEAD (the 'file' probe)."""
    from . import identity as ID
    import hashlib
    raw = read_bytes(Path(roots.identity_json))
    lf = raw.replace(b"\r\n", b"\n")
    if roots.identity_frozen and hashlib.sha256(lf).hexdigest() != ID.IDENTITY_PREFREEZE_SHA256:
        raise AssertionError("IDENTITY_prefreeze.json differs from its freeze-manifest entry")
    doc = json.loads(lf.decode("utf-8"))
    by_obj = {}
    for r in doc.get("records", []):
        by_obj.setdefault(r.get("object"), []).append(r)
    out = {}
    for key, obj in IDENTITY_OBJECT.items():
        recs = by_obj.get(obj, [])
        if len(recs) != 1:
            raise AssertionError(f"identity references: {len(recs)} records for object key {key}")
        probes = [p for p in recs[0].get("probes", []) if p.get("status") == "ok"]
        if key in LEY_LH_KEY.values():
            image = [i for i, k in LEY_LH_KEY.items() if k == key][0]
            pins = {int(i): (a, b) for i, a, b in roots.ley_sha}
            for sub, sha, field in ((key, pins[image][0], LEY_SURFACE_FIELD),
                                    (LEY_VOL_KEY[image], pins[image][1], LEY_VOLUME_FIELD)):
                loc = [p for p in probes if str(p.get("method", "")).startswith("local") and p.get("sha256") == sha]
                nv = [p for p in probes if str(p.get("method", "")).startswith("NeuroVault") and p.get("field") == field]
                if len(loc) != 1 or len(nv) != 1:
                    raise AssertionError(f"identity references: object key {sub} lacks its local / NeuroVault probe")
                refs = [ID.ref_from_probe(loc[0]), ID.ref_from_probe(nv[0])]
                if isinstance(loc[0].get("git_blob_sha"), str):
                    refs.append({"basis": ID.BASIS_GIT, "bytes": loc[0]["size"], "git_blob": loc[0]["git_blob_sha"]})
                if field == LEY_VOLUME_FIELD and isinstance(nv[0].get("api_file_size"), int):
                    refs.append({"basis": ID.BASIS_SIZE, "bytes": nv[0]["api_file_size"]})   # §11 file_size equality
                out[sub] = {"refs": [r for r in refs if r is not None], "local_path": str(loc[0]["path"]),
                            "url": nv[0].get("file_url"), "image": image,
                            "content_length": nv[0].get("content_length"), "last_modified": nv[0].get("last_modified")}
            continue
        refs, local, urls = [], [], []
        for p in probes:
            r = ID.ref_from_probe(p)
            if r is not None and not str(p.get("method", "")).startswith("HTTP HEAD"):
                refs.append(r)
            method = str(p.get("method", ""))
            if method.startswith("local"):
                local.append(str(p["path"]))
                lf_blob = p.get("git_blob_sha_crlf_to_lf")
                # a CRLF checkout of an LF blob: the tree probe already holds the LF blob (compared after conversion)
                if isinstance(p.get("git_blob_sha"), str) and not isinstance(lf_blob, str):
                    refs.append({"basis": ID.BASIS_GIT, "bytes": p["size"], "git_blob": p["git_blob_sha"]})
            for k in ("url", "file_url"):
                if isinstance(p.get(k), str) and p[k].startswith("https://"):
                    urls.append(p[k])
                    break
        if key == GIA_GOV_KEY:
            if local or len(refs) != 1:
                raise AssertionError("identity references: the 93de089 workbook has a local copy or not one tree probe")
            out[key] = {"refs": refs, "local_path": None, "url": urls[0]}
            continue
        if len(local) != 1 or not refs:
            raise AssertionError(f"identity references: object key {key} lacks a local copy or a reference")
        out[key] = {"refs": refs, "local_path": local[0], "url": urls[0] if urls else None}
    return out


def gia_mdd_paths(roots: Roots, read_bytes) -> dict:
    """register_maps/gia_mdd_paths.json (frozen: its sha256 is asserted through the freeze manifest by the caller):
    {path: (blob, size, commit)} of the MDD list files @e045bc5 and the GEDAR maps @eda33ab."""
    src = Path(roots.mdd_paths_json) if roots.mdd_paths_json else Path(roots.repo) / GIA_MDD_PATHS_REL
    doc = json.loads(read_bytes(src).replace(b"\r\n", b"\n").decode("utf-8"))
    out = {}
    for e in doc.get("e045bc5_sets", []):
        if e.get("present") is not True:
            raise AssertionError("gia_mdd_paths: a listed MDD set is absent")
        out[e["path"]] = (e["blob_sha"], int(e["size"]), GIA_E045BC5)
    for k in ("eda33ab_asd_counterparts", "eda33ab_mdd_maps"):
        for e in doc.get(k, []):
            out[e["path"]] = (e["blob_sha"], int(e["size"]), GIA_EDA33AB)
    return out
