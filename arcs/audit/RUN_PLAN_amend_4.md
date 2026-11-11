# RUN PLAN AMENDMENT 4 — A1 `audit`: readings WP4 phase 1 found unpinned (gate G2; material not opened)

> **Status: v3, FROZEN by the orchestrator 2026-10-16 (session 14; sha256 in `FROZEN.txt`). The text below the
> Versions table is v2's, with v3's answers added under "Questions for the orchestrator".** v1 written 2026-10-16 by the WP4 phase-1 worker at HEAD 6fe112e with the WP4
> phase-1 code of the commit that adds this file (wp4_layout.py, wp4_read.py, wp4_material.py, wp4_sets.py,
> wp4_sources.py, wp4_repro.py, rbuild/r17.py; the FE25 / FE26 modes of fetch_extract.py; ahba_extras' R38 build).
> The orchestrator reviews and freezes; until then `wp4_layout.production_allowed()` refuses a production run of the
> G2 material stage (the code's DRAFT guard). This amends `RUN_PLAN.md` v3.1 (FROZEN, sha256 16c60232…) as amended by
> `RUN_PLAN_amend_1.md`, `_2.md` and `_3.md` (FROZEN).
> - **Readings R51–R63** are in the plan's §5 format: **Text** → **Options** → **Reading** → **Why** → **Checks**. Each is
>   decided WITHOUT the G2 material: no G2 carrier, map, workbook, repository list, GEDAR map, supplement, decoder
>   output or Seelemeyer file was downloaded, opened, hashed or listed by its author (§0).
> - **§8** classifies the phase-1 implementation choices as "pinned here" or "no pin needed", as amendments 2 and 3 did.
> - **"Changed"** lists every departure from a frozen text, each declared; **"Not changed"** the rest; **"Affected code"**
>   maps every reading to the code that implements it (already written in phase 1, on synthetic stand-ins).
>
> No registered definition, threshold, seed key or status order changes (`claims_register.md:1102-1103`). A cell's
> status changes only where a frozen rule already provides it (fail-closed layouts read "not auditable (definition not
> applicable: …)", as RUN_PLAN §17 `:1724-1725` and amendment 3's R46 do; a comparator that cannot be computed reads
> "not computable (…)", never a cell status).

## Versions
| version | date | written at | sha256 | review |
|---|---|---|---|---|
| v1 | 2026-10-16 | HEAD 6fe112e + the WP4 phase-1 code (85dfc48) | e2a7fc24c70536dd… | asdg-skeptic 2026-10-16 on 6fe112e..ea7f936: 0 A / 5 B / 8 C |
| v2 | 2026-10-16 | ea7f936 + the review fixes (committed with this file) | stated at hand-off | the review's B4 (R54), B5 (R58 (f)), C1 (§0, R60), C2 (R60), C4 / C5 ("Changed" 7-8) and B3 / C3 / C8 (§8) applied; awaiting the orchestrator's re-check |
| v3 | 2026-10-16 | 36a4fe6 + the orchestrator's answers to Q2 / Q3 (session 14) | in FROZEN.txt | re-check on ea7f936..36a4fe6: 0 A, B1–B5 closed, C9–C11 noted; frozen by the orchestrator |

## 0. Authority, exposure, what was read
- **Authority:** RUN_PLAN §18 `:1806-1812`. Claim results exist (A1's WP3 ungated rows, ARC session 12), so this
  amendment is **labelled post-exposure** (`:1809`): "It applies to the cells of every gate it bears on, already-run
  cells included (rerun under both versions, both reported), and is reviewed by asdg-skeptic before it is frozen."
  - **It bears on G2 cells only** (Patel, Giacomel, Liu T3, Pretzsch, Hansen, Leyhausen; Seelemeyer stays not
    auditable). No reading here touches an ungated cell, so no already-run cell is rerun under it.
  - **The G2 material is unopened.** Every reading is fixed before this audit downloads, opens, hashes or lists any G2
    target file (the operator's rule for WP4 phase 1). So, for the material it bears on, it is pre-exposure in the sense
    of `:1807-1808`; the label "post-exposure" is the formal one `:1809` requires.
- **The ENIGMA-ASD exposure of 2026-10-01** (RUN_PLAN §9 `:1331-1407`) stands as declared. None of R51–R63 uses a value
  of any ENIGMA table; the exposure-bearing files (`wf_a992ecba-de5`) were not read.
- **Read by this author:** this programme's `CLAUDE.md`; RUN_PLAN §1–§2.1, §4, §5 (R1–R31), §6, §7, §8, §9, §11, §14,
  §16–§18; amendment 3 §0, R44, R50, §8–§10; the A1 ARC entries of sessions 12 and 13; the A1 code of `src/a1_audit`
  (run.py, fetch_extract.py, identity.py, reparcel.py, real_sources.py, wp3_*.py, repro.py, forms.py (parts), pace.py,
  ahba_builds.py / ahba_extras.py (parts), plants/driver.py (parts)); `claims_register.md:59-61, :334-499, :1028-1048,
  :1440-1490, :1664-1683, :1745-1812`; the TSV's G2 rows 81-132, 478, 523-692 (fields map, set_S, set_id, set_status, T,
  direction, status, reproduction, published_value_and_location, map / cell index; read by script); the incorporated
  drafts `register_work/patel2021virtual.md`, `giacomel2026cartography.md`, `hansen2022local.md` (all),
  `pretzsch2024patterns.md:1-140`, `leyhausen2024intrinsic.md:1-60`, `liu2026spatiotemporal.md` (by grep);
  `register_maps/IDENTITY_prefreeze.json` (the G2 objects' probes: sizes, sha256s, git blobs, local paths, NeuroVault
  metadata), `register_maps/gia_mdd_paths.json`, `register_sets/MANIFEST.json` (the 41 "built under gate G2" entries),
  `register_sets/UNIVERSE_GENES.json` (keys), `src_register/s_build.py:75-170, :364-400, :464-503, :1178-1214`;
  abagen's `dk_atlas_info.csv` (pinned) and the AHBA dk matrix's header; the installed `netneurotools` 0.3.0
  `stats/regression.py` (`get_dominance_stats`; a public package, no G2 material); the completed WP3 row files'
  structure (keys) and counts, and `run_manifests/reprice_wp4.json`.
- **Values seen by this author (complete list).** Published values in the TSV rows read (Patel's mean bicors −.201 /
  −.226 / −.212 and the null panels' values; Giacomel's published ρ per cell and R2's eda33ab ρ's; LIU-T3's −.34;
  Pretzsch's k / OR / p per row; Hansen's R²_adj .533 and dominance .027; Leyhausen's ORs); the drafts' recorded facts
  (Patel: "the first two rows of eTable 4 (bankssts, caudal anterior cingulate)" — names only, no value; Giacomel's set
  sizes and shipped-vs-supplement differences; Hansen's 68 × 13 shape and the dominance values; Pretzsch's list sizes);
  one WP3 claim value printed while reading a row file's structure (`results/a1_run/ungated/verdict/row_0010.json`, a
  Segura descriptor row: T = −0.0632); the R13 check's counts (18 / 18, synthetic pairs). None of these enters a
  reading below.
- **Not opened or listed by this author:** any G2 carrier or map (Patel's PDF; both Giacomel workbooks; the repository
  lists, GEDAR maps and code; the Sadeghi workbook and its folder; Liu T3's two CSVs; Hansen's files and the Cammoun
  info; Pretzsch's derived CSV; Leyhausen's volumes and GIFTIs; NeuroVault 777428–777430 and their decoder output;
  Seelemeyer's files); the FreeSurfer tarball and figshare 3501911 (deferred to phase 2, below); anything under
  `E:\data\asdg\` except the HGNC table (hashed by the phase-1 tests' reference pins) and nothing under `_quarantine`.
- **What is not blind (v2, asdg-skeptic C1).** The readings are decided without opening the G2 material, but several
  LAYOUT facts they rely on come from the incorporated drafts, which were written from the material by their authors:
  Giacomel's `M_<region>_thickavg` labels and the alphabetical Subcortical order (R54), Hansen's headerless 68 × 13
  `enigma_ct.csv`, the 7 predictors and "rows 1–34 right / 35–68 left" (R60), Pretzsch's 180 + 180 names (R61), the
  Sadeghi file name and prefix (R57). They fix the readers' declarations, not any value. **R60's functional was chosen
  knowing Hansen's shipped dominance results** (R²_adj .533 = the sum of total dominance, .027 for gene PC1): the HAN
  reproduction is therefore labelled **NOT BLIND** (`wp4_repro.HAN_NOT_BLIND`) and is a reproduction check, never a
  verdict (it moves no count; the claim's T is unaffected).
- **Reference atlases deferred.** RUN_PLAN / amendment 3 R50 give neither the FreeSurfer annot nor the HCP-MMP1 files
  a pre-freeze content pin (R16 pins the tarball's URL, size and date; R15 only "URL, bytes and sha256 are recorded"),
  and the register lists the HCP-MMP1 volume as G2 material (`claims_register.md:1947-1953`; amendment 2 R38 "fetched
  under G2 in WP4"). Both are fetched in phase 2 as its first steps (R16 first), under R51 / R52.

## R51. R16's tarball: the headers are recorded, never a refusal; the order of official artefacts (amendment 3 C9)
- **Text:** R16 (`RUN_PLAN.md:770-804`): the pinned ubuntu22 tarball "Probed 2026-10-01 … HTTP 200, 9,484,461,482 bytes,
  Last-Modified 2023-06-27"; "Recorded: the URL; the Content-Length and Last-Modified headers; the bytes streamed …";
  "If the pinned tarball cannot be obtained, any other official 7.4.1 artefact from the same directory is accepted, and
  its member's sha256 recorded … only a non-official copy is refused." Amendment 3 §10.1 C9: the WP2 code refused the
  tarball on a size mismatch or a missing Content-Length (`fetch_extract.py:1166-1171`), against R16's text.
- **Options:** (A) a size mismatch refuses (the WP2 code); (B) the headers are recorded and compared with the probe,
  the difference labelled, the member's sha256 the identity (R16's "Recorded"; any official artefact accepted).
- **Reading: (B).** The headers of each artefact tried are recorded; for ubuntu22 the Content-Length is compared with
  the 2026-10-01 probe and labelled "as the 2026-10-01 probe" / "differs from the 2026-10-01 probe (recorded, R51)";
  nothing refuses on it. The identity is the member's sha256 recorded at download (R16 `:790-791`).
  - **Order of artefacts** when one cannot be obtained (an HTTP / transport failure, the member absent): ubuntu22, then
    ubuntu20, ubuntu18, centos8, centos7 (the tarballs R16's probe listed; the macOS artefacts are not tar streams);
    the first that yields the member governs (R16 `:796-797`: "the ubuntu22 member governs" when two are read).
  - A **non-regular member** (R16 `:781-788`) ends the step with R16's status; no further artefact is tried.
- **Why:** R16's text records the headers and accepts every official artefact; refusing on a size header would turn a
  re-packed but official distribution into "not obtainable", which R16 excludes.
- **Checks:** `test_wp4_phase1` F1 (a link member: one artefact tried, R16's status), F2 (a Content-Length differing
  from the probe: labelled, the member taken).

## R52. R15's figshare files: which file is "its label list", and their identity at download
- **Text:** R15 (`RUN_PLAN.md:752-763`): "The volume and its label list are both taken from figshare 3501911; URL,
  bytes and sha256 are recorded. The left-label indices are read from the label list, not assumed." The register names
  the volume `HCP-MMP1_on_MNI152_ICBM2009a_nlin.nii.gz` (`claims_register.md:1036-1037`). R13's fields: "byte size plus
  the served MD5 where the server gives a plain MD5" (`claims_register.md:1090-1094`).
- **Options:** the label list = (A) the file named as the volume with `.txt`; (B) any `.txt` of the article.
- **Reading: (A).** The article's public API record (`https://api.figshare.com/v2/articles/3501911`, one GET, no
  identifier) gives each file's name, size, `computed_md5` and download URL. The volume is the one file named exactly
  `HCP-MMP1_on_MNI152_ICBM2009a_nlin.nii.gz`; the label list the one named `HCP-MMP1_on_MNI152_ICBM2009a_nlin.txt`.
  Not exactly one of each → R15's status ("… could not be matched to eTable13"). Each is downloaded from its API URL
  and held at download to its **size and served MD5** (`computed_md5`, a plain MD5: R13's second basis); the sha256 is
  recorded. File names are compared in memory and recorded by sha256 only (§8's print rule).
  - The label list must be RP4's form ("<integer> <name>" per line); its left ids are those whose name starts with
    `L_`; exactly 180, else R15's status. The 180 left names are the runner-side names of R15 (§8 `:1189`).
- **Why:** (B) could pick a list belonging to another variant of the volume; (A) is the pair the article ships for the
  registered file. The MD5 is the strongest identity the server gives (R13's rule).
- **Checks:** `test_wp4_phase1` A5 (two volumes named alike → refused), S1 (the stand-in article).

## R53. Patel's eTable 4: the transcription rule (page index 25; the Estimate column; the region names)
- **Text:** "eTable 4 Estimate, 34 left DK values (PDF p. 26)" (`RUN_PLAN.md:1469`); "transcribed by a non-printing
  script with read-back" (TSV row 81 `map`); §8 PDFs (`:1301-1304`): pdfplumber 0.11.10, "only the needed page is
  parsed", "read-back compares the stored values with a second parse". The draft: the caption "… across the 34 regions
  of the left hemisphere", columns "estimate, SE, p, FDR p, N", region names as "bankssts, caudal anterior cingulate"
  (`register_work/patel2021virtual.md` §0, §3).
- **Options:** the page: PDF page 26 (index 25) or the printed folio 26; the column: (A) the numeric word whose x-range
  overlaps the header word "Estimate", (B) the first number of each row; the names: exact DK names, or a normaliser.
- **Reading:** page **index 25** (the 26th page of the file; amendment 3 R47's precedent read "pp. 38–39" as indexes 37
  and 38); the header word "Estimate" exactly once on the page; every line below it whose numeric word overlaps that
  word's x-range is a table row (**(A)**); the row's label = its words left of its first numeric word, normalised by
  R42 (d)'s steps (amendment 2) with **unmarked labels standing for the left hemisphere** (the caption's declaration);
  minus signs U+2212 / U+2013 read as "−". Exactly 34 rows, the 34 left DK cortical labels each once, else "not
  auditable (definition not applicable: the declared eTable 4 layout not matched)". The read-back is a second parse of
  the same page, equal value for value. pdfplumber 0.11.10 is asserted (L14, extended as amendment 3 R47 (b) did).
- **Why:** (B) breaks if a row's label carries a digit or the column order differs from the draft's; the x-overlap
  ties the value to the declared header. Unmarked = left is the caption's statement, not an inference from values.
- **Checks:** `test_wp4_phase1` A2 (a missing row, two header words → refused), S1 (a 26-page stand-in, U+2212 minus).

## R54. Giacomel's sheets: the declaration, the label normaliser, the order check, the download form
- **Text:** "Giacomel: sheets `Thickness` / `Subcortical`, ASD and MDD columns at 93de089. The c022a29 comparison records
  the count of differing cells only, and 93de089 governs" (`RUN_PLAN.md:1470-1471`); the TSV: "column ASD: ENIGMA-ASD
  Cohen's d, bilateral mean (M_<region>_thickavg), 34 DK regions"; subcortical "7 structures (accumbens, amygdala,
  caudate, hippocampus, pallidum, putamen, thalamus; alphabetical sheet order; no ventricles)"; download identity
  "16,073 B; git blob 46323903…" from the GitHub blob URL (TSV row 91 `map`).
- **Options:** the label column: position 0 or a named column; the "M_" prefix: a marker or a name part; the order:
  asserted or ignored; the download URL: the blob page or the raw form.
- **Reading:**
  - a **labelled table** (fetch_extract FE25): the header row is the first of rows 0–19 (through the guard, §8 step 4)
    holding the exact texts `ASD` and `MDD` once each at positions > 0; the label column is **position 0**; the block is
    the run of rows with a non-empty position-0 cell after it (amendment 3 R46 (d)'s block rule); a wrapper-side mask
    hands only positions 0, ASD and MDD to the transform;
  - the labels are normalised in memory by **R42 (d) extended for G2**: the token or glued letter `m` is a marker for a
    bilateral **mean** and selects the left id (bilateral maps are placed on the left parcels: R11 `:684-685`,
    `claims_register.md:1048`); `thalamus` → `thalamusproper` and `accumbens` → `accumbensarea` join the alias table (the
    TSV's own names); fail closed as R42 (d) (unmatched, conflicting markers, two labels on one id);
  - Thickness: the 34 left DK cortical ids each once; Subcortical: the 7 left aseg ids each once; values finite; the
    map is keyed **by label**, so T never depends on the sheet's row order;
  - (v2, asdg-skeptic B4) the Subcortical sheet's order is compared with the registered alphabetical order and
    **recorded**, never a refusal: when it does not match, T is still computed by label and only the misalignment
    descriptor (which pairs y in the sheet's alphabetical order with the score in the GEDAR atlas order, by position)
    reads "registered order not matched" (not computed);
  - a sheet that fails is saved as its fail-closed status with counts (amendment 3 R46's precedent) and its rows read
    "not auditable (definition not applicable: the declared Giacomel sheet layout not matched)";
  - the 93de089 workbook is downloaded from `https://raw.githubusercontent.com/<repo>/<commit>/<path>` (the raw form of
    the pinned blob URL; the identity is the git blob and size, independent of the URL);
  - the c022a29 copy (the pinned local file, R44's form) is read by the same declaration; the record holds the counts of
    compared and differing cells per sheet; 93de089's values are the map.
- **Why:** the draft records that the sheet's labels are "M_<region>_thickavg" in the left-hemisphere GEDAR row order;
  the `m` marker is the only reading of "M_" consistent with "bilateral mean" in the TSV.
- **Checks:** `test_wp4_phase1` A1, A3 (a swap of two subcortical labels → recorded, the value placed by label; a
  duplicated label → refused), S1 (one planted differing cell).

## R55. Giacomel's repository lists: identity, declared columns, the weights, duplicates
- **Text:** "the repository lists at e045bc5 and the eda33ab GEDAR maps, by blob ids from the tree listings
  (`register_maps/gia_mdd_paths.json`)" (`RUN_PLAN.md:1451-1452`); TSV set_S: "HGNC symbols (gene_name)"; "weights =
  TWAS z"; the draft: "Identifier: HGNC symbol (`gene_name`; Ensembl in `gene`)"; §1.6's mapping takes "Ensembl IDs where
  given" (`claims_register.md:335-336`).
- **Facts:** `gia_mdd_paths.json` holds the blob ids of the five MDD lists and the six GEDAR maps only; the pre-freeze
  identity record of the e045bc5 tree stores its entry count, not its entries.
- **Reading:**
  - every list is downloaded in its raw form at the commit; its identity at download is **git blob + size**: from
    `gia_mdd_paths.json` (MDD lists, GEDAR maps) or, for the nine ASD lists and R58's files, from the commit's **tree
    listing fetched at download** (GitHub's public API, one GET, no identifier; `truncated` false required). A commit's
    tree cannot change, so the blob ids name the bytes the commit holds;
  - declared columns: `gene_name` exactly once (the symbol); `gene` when present (the Ensembl id, used first by §1.6);
    the **weight** = the first of the exact headers `z_mean` (S-MultiXcan's mean z) and `zscore` (S-PrediXcan's z) that
    the list carries; a list with neither reads "not computable (no declared weight column …)" for the weighted
    functionals only (the unweighted T needs no weight);
  - the rows become the S-build's raw form (kind / id / symbol) and the set is built by **the frozen S-build itself**
    (`src_register/s_build.py` loaded from its verified bytes; `build_set`; §1.6's HGNC rule, the class universes,
    "< 5 columns → not testable"); a gene on several rows takes the mean of their weights (amendment 2 R42 (a)'s rule),
    counted.
- **Why:** a choice of weight column made without the file; a wrong choice cannot create a result, because the
  registered outcome of the weighted cells is conditioned on reproducing the published ρ (amendment 2 R41: "not
  answered (T_S not reproduced)"), and the |z|-weighted 4.1 check is a check, not a statistic.
- **Checks:** `test_wp4_phase1` A4, S1 (lists with `z_mean` and `zscore`; a 3-gene list → "< 5", restated).

## R56. The paper's GEDAR maps (eda33ab): the declared layout
- **Text:** "the paper's weighted GEDAR map (eda33ab version) ρ with y" (TSV rows 103-108); the draft: "row order
  identical to the left-hemisphere GEDAR rows (checked label by label)".
- **Reading:** a tab-delimited table with a header row; the label column is position 0, whose cells are either all
  abagen DK ids (integers of the pinned atlas info) or all names the G2 normaliser maps to DK ids (sides required); the
  value is the **one other column that is numeric on every row**; only the left ids are used. Otherwise "not computable
  (the paper's GEDAR map layout not matched)" (a descriptor; no count moves).
- **Checks:** `test_wp4_phase1` A4 (id and name forms).

## R57. The Sadeghi DEG workbook: found or not, its identity, its declared sheet and columns
- **Text:** "the Sadeghi DEG workbook, if it is not already under `E:\data\asdg\giacomel2026cartography\external\`
  (checked by listing that folder's names in memory and comparing them with the declared file name; reported as found /
  not found, with name sha256s, §8's print rule)" (`RUN_PLAN.md:1453-1455`); the draft's row 13:
  `…\external\sadeghi2022_csbj\mmc2.xlsx`, sha256 prefix ef4aee97e746b5e4, source "PMC9428860 supplementaryFiles
  (mmc2.xlsx)"; the TSV: "Supplementary_Data1 (mmc2.xlsx), Dx = ASD (20,256 rows) … top … by p.value … weights = logFC".
- **Reading:**
  - the declared name is the relative path `sadeghi2022_csbj/mmc2.xlsx` under that folder (names at depth ≤ 2 compared
    in memory; recorded as sha256s);
  - found: its identity is the draft's **registered sha256 prefix** (64 bits; amendment 3 R47's precedent), then its full
    sha256 pins the wrapper's own identity step, so the bytes read are the bytes checked;
  - not found: phase 2 takes the Europe PMC archive of PMC9428860 (the draft's source), the one member ending
    `mmc2.xlsx`, held to the same prefix; else "not computable (… not obtainable)" for the 18 DEG cells (none in m);
  - the declared sheet (FE26): the one sheet whose name, casefolded with non-alphanumerics removed, starts with
    `supplementarydata1`, `supplementary1`, `data1` or `sheet1`; its header row (rows 0–19, through the guard) holds `Dx`,
    `p.value` and `logFC` exactly once and the first of `gene`, `Gene`, `gene_name`, `GeneSymbol`, `symbol`, `Symbol`,
    `hgnc_symbol`, `external_gene_name`; only those four columns are handed over, and only the rows of Dx ASD and MDD
    are saved (gene-level content).
- **Checks:** `test_wp4_phase1` S1 (the stand-in in the declared folder; an undeclared sheet untouched).

## R58. R17: the parameters, the run, the DEG sets
- **Text:** R17 (`RUN_PLAN.md:806-824`) quoted in `rbuild/r17.py`; the TSV's DEG set definition (rows 109-131).
- **Reading:**
  - (a) the commit is **e045bc5** (the commit the register names for the lists and the code); its date is the
    **committer** date (GitHub's commit record);
  - (b) "the R version the repository declares": `renv.lock`'s R version, else a top-level `.R-version` holding one
    version; a DESCRIPTION's `Depends: R (>= x)` is a floor, not a declaration;
  - (c) otherwise "the R release current at the commit date": the latest release dated on or before it in the r-hub
    R versions API (public; its bytes' sha256 recorded);
  - (d) the image `rocker/r-ver:<version>` pulled and pinned by digest; its Ubuntu codename read from the image;
  - (e) CRAN = `https://p3m.dev/cran/__linux__/<codename>/<commit date>`;
  - (f-bioc) Bioconductor: of the releases whose R version (Bioconductor's `config.yaml`) equals the R minor, the one
    released last on or before the commit date, else the earliest;
  - (g) packages: the script's `library` / `require` / `requireNamespace` calls and `pkg::` references, base packages
    excluded, installed with BiocManager at (e) / (f-bioc);
  - (h) the run: `Rscript <the script's repository path>` in a scratch copy of the repository layout holding the script
    and the identity-checked inputs at the paths its read calls name; `--network none`; nothing under `E:\data`
    mounted; stdout / stderr to files, never printed (line counts and sha256 only); every file the run creates hashed;
    the rebuilt GEDAR maps are its outputs named `<DX>_literature_TPRS_thr_<t>.tsv` (the register names the MDD ones),
    read by R56's layout; a non-zero exit or an absent declared output → R17's fallback status, verbatim;
  - (f) [v2, asdg-skeptic B5: follow the TSV, "rebuilt with the paper's code literature_gwas_analysis.R ('S
    re-derived')"] **S of each DEG cell is the list the paper's script writes in the R17 run**: a file the run created
    whose name holds exactly one of the tokens ASD / MDD and exactly one `thr<t>` (t = 1 / 5 / 10), and whose header
    holds exactly one `logFC` and a symbol column (`gene_name`, else the first of the R57 alternatives held once); the
    weights = its logFC (the TSV); a key two files claim, or no such file → "not computable (the post-mortem DEG set:
    the script wrote no identifiable list for this cell)" (R17's own status when the run failed). The set is built by
    the frozen `build_set` (R55);
  - **the check** is the TSV's definition computed in Python on the workbook rows and the authors' two files: the rows
    of Dx whose gene lies in the AHBA matrix's columns ∩ the HPA list's symbols (`Gene` or the first of `Gene name`,
    `gene`, `gene_name`, `symbol`), ordered by p.value (file order on ties), the top round(n × thr). The script's set
    must have that **m**, and **the ASD pool must be the registered 3,599** (TSV row 109); else the cell reads "not
    computable (the post-mortem DEG set: the script's set does not match the registered definition - m or the 3,599
    ASD pool)". The Python set is **recorded beside as a cross-check only** (common / script-only / Python-only counts,
    equal or not; `deg_checks` in the G2 manifest); it never replaces S;
  - the script's inputs are placed at the paths its read calls name (R17 (h)): the two prefix-held authors' files at
    their repository paths, every other read path the commit's tree holds (downloaded by blob, R55's identity), and the
    Sadeghi workbook for a read path ending in its declared file name; the working directory is the repository root or
    the script's directory, whichever resolves more of the read paths (ties: the root); unresolved paths are counted
    (the script then fails or not on its own);
  - the run's rebuilt maps `<DX>_literature_TPRS_thr_<t>.tsv` are saved through the wrapper (R56's layout) as the DEG
    descriptors' second maps;
  - the builder is `rbuild/r17.py` `DockerR17` (production: `docker pull` of rocker/r-ver:<version>, the digest from
    `RepoDigests`, `FROM <image>@<digest>`, `docker build`, the image id and the session info's sha256 recorded); the
    run's outputs are held to the sha256 and size the run recorded when they are read.
  - the authors' two input files are downloaded at e045bc5 by tree blob (R55) and also held to the draft's registered
    prefixes (4b4ace458d392366, 1b85136a7dc582ad).
- **Why:** each reading fixes a source that R17 names only by kind ("the R release current at the commit date",
  "the release matching that R"); (f) follows the TSV ("S re-derived" by the paper's code) and keeps the TSV's own
  definition and count as the check, so a script that writes another set cannot pass silently.
- **Checks:** `test_wp4_phase1` A5 (params: declared / API / Bioconductor), R1 (the run in the WP2 R image with network
  none on a synthetic script; a missing input → R17's status; DockerR17's command sequence with an injected runner;
  an unpinned base refused), S1 (the whole stage with DockerR17 on the WP2 R image as a test-only base: the stand-in
  script's lists become S, m 36 / pool 3,599, MDD m 90, the cross-check equal), V5 (a planted wrong-size list →
  STATUS_DEG_CHECK; the name / header rule).

## R59. Liu T3: the ENIGMA Toolbox tables and the L / R map
- **Text:** "Liu T3: L/R average, d_icv, left V-DK; ventricles dropped (`prereg.md:298`)" (`RUN_PLAN.md:1472`); the
  TSV's CortThick / SubVol files and hashes (row 478).
- **Reading:** the exact headers `Structure` and `d_icv`; CortThick 68 rows, SubVol 16 rows (both lateral ventricles
  dropped, counted — fail closed otherwise); labels by R42 (d) (its own ENIGMA formats `L_<region>_thickavg`, `Lthal`,
  `LLatVent`); per DK name the mean of the L and R values when both are present, else missing; placed on the left V-DK
  parcels (the brainstem has no ENIGMA value: missing, dropped by §4's finite rule). Otherwise "not auditable
  (definition not applicable: the declared ENIGMA Toolbox layout not matched)".
- **Checks:** `test_wp4_phase1` A4 (an unmatched label → refused).

## R60. Hansen: the shipped files, the Cammoun order, the dominance functional
- **Text:** "Hansen: left rows, Cammoun order 35–68 → DK" (`RUN_PLAN.md:1473`); TSV row 624: "column asd (index 2 …)";
  "R²_adj .533 and gene PC1's dominance .027 recomputed with the shipped predictors (local_biol_predictors.csv, sha256
  prefix d73853619b543bf9)"; the draft: `enigma_ct.csv` 68 × 13; `local_biol_predictors.csv` "7 z-scored maps"; the
  Cammoun 2012 info CSV `…\external\cammoun2012\…_info.csv` (prefix 348246e7d997c395); "rows 1–34 right, 35–68 left".
- **Reading:**
  - `enigma_ct.csv`: a headerless 68 × 13 numeric matrix; y = column index 2; `gene_pc1.csv`: 68 × 1;
  - the predictors: 68 × 7 numeric (a header row allowed, never kept); the gene PC1 column is the **one column whose
    values equal the shipped gene_pc1's after z-scoring** (|r| > 1 − 1e-9), else "not computable";
  - the **Cammoun order** comes from the draft's info CSV (held to its registered prefix): the rows with `scale`
    scale033 and `structure` cortex, in file order, 68 of them, 34 R then 34 L (asserted), the left names normalised to
    the 34 left DK ids; rows 35–68 of the shipped files take those ids. Otherwise "not auditable (definition not
    applicable: the Cammoun scale033 order could not be matched to the DK names)";
  - the reproduction (R27 "R²_adj and dominance with the shipped predictors") is computed **on the shipped 68 rows** (the
    paper's model, both hemispheres) with **netneurotools' dominance analysis on adjusted R²**: OLS with an intercept;
    total dominance = the mean of the individual and the partial dominances over subset sizes (its sum is the full
    R²_adj). netneurotools 0.3.0 (installed) does not import under this venv's scipy, so its `get_dominance_stats` is
    ported (`wp4_repro.dominance_stats`) and tested against a brute-force Shapley value.
- **Why:** netneurotools is the authors' lab's implementation, and the draft's "R²_adj = 0.533 (sum of total dominance)"
  is exactly its efficiency property; the claim's own T stays on the left 34 rows (dk-ctx).
- **Not blind (v2, C1):** the functional and the 68-row model were chosen knowing the shipped .533 / .027 (§0); the
  reproduction is labelled NOT BLIND and is a reproduction check, not a verdict.
- **The port cross-checked (v2, C2):** once, against netneurotools 0.3.0 itself in a throwaway container
  (python:3.11-slim, numpy 1.26.4, scipy 1.11.4; `wp4_nnt_check.py`), on three seeded synthetic regressions, adjusted
  and unadjusted: the largest absolute difference 4.4e-16 (tolerance 1e-10); pinned in
  `run_manifests/material/G2/dominance_port_check.json`.
- **Checks:** `test_wp4_phase1` A4, A5 (the port = Shapley; efficiency), S1, U2 (the NOT BLIND label), V6 (the pin).

## R61. Pretzsch's derived eTable13 CSV: the label and feature columns
- **Text:** "Pretzsch: 180 left Glasser loadings → dk-ctx (R15)" (`RUN_PLAN.md:1474`); R15's name match ("read from the
  derived CSV's label column … compared in memory … reported as match counts only"); the draft: "180 LH (`L_*_ROI`) +
  180 RH names … 4 × 180 numeric loadings … hemisphere column added"; the TSV binds rows by "y_CT:" / "y_SA:".
- **Reading:** the label column = the one column holding all 180 left names of R52's label list, each once (the
  one-to-one match of R15); the rows = those 180; the feature columns = the columns numeric on those rows whose header
  tokens name exactly one feature: CT iff `ct` or `thickness`; SA iff `sa`, or both `surface` and `area`; exactly one
  of each, else "not auditable (definition not applicable: the declared eTable13 layout not matched)". The values are
  taken as published, then mapped to dk-ctx by R15's majority rule at use (amendment 2 R43).
- **Checks:** `test_wp4_phase1` A4 (a missing left name → refused), S1, U2.

## R62. Leyhausen: the identity of the volumes and of the lh GIFTIs
- **Text:** §11 (`RUN_PLAN.md:1466`): "Leyhausen lh GIFTIs (3c5dfc21…, 4429d1da…, 9436a9e9…), plus the NeuroVault
  `file_size` equality"; the TSV (rows 626-692): "left fsaverage GIFTI t-map_m.fsaverage.lh.func.gii sha256 5889a687…
  (NIfTI sha256 3c5dfc21…)"; the register: "uploaded as surfaces → the left fsaverage GIFTIs → dk-ctx (surface rule)".
- **Facts:** the three hashes §11 lists are the **volumes'** (IDENTITY_prefreeze.json's local probes); NeuroVault's
  `file_size` belongs to the volume (the GIFTIs carry none; their HEAD Content-Length is recorded).
- **Reading:** both are held at use: each **volume** to §11's sha256, its size and NeuroVault's `file_size`; each **lh
  GIFTI** to the TSV's sha256, its size and its HEAD Content-Length. A mismatch of either reads "not auditable (map
  changed)" for that image's rows. The map is read from the lh GIFTI only (R16's annot; the surface rule).
- **Why:** §11's label and its hashes disagree; holding both is the reading that satisfies every frozen text.
- **Checks:** `test_wp4_phase1` S1 (both identities), U3 (tampering).

## R63. Leyhausen's decoder: the list, the overlap universe, the fallback
- **Text:** "NeuroVault decoder outputs for 777428–777430 (descriptive reproduction)" (`RUN_PLAN.md:1458`); the TSV:
  "NeuroVault decoder output for image 777428 (fetched under G2), nominal p < .01 (the paper's list size 480), then
  GeneOverlap; OR and p vs the published OR"; R30's overlap rule (Pretzsch); R14's general rule for decoder fallbacks.
- **Reading:** amendment 3 R45's decoder form unchanged (the URL with `mask=full`, one GET, the declared columns, up to 3
  transport attempts across runs, decided once; attempt records under `run_manifests/material/G2/`); the list = the
  HGNC genes with a finite p < .01, **both signs pooled** (the draft: "treated as unsigned"); the overlap is R30's
  (`repro.overlap_test`, GeneOverlap's direction) on the **genes the decoder returned with a finite p** (R30's "genes the
  recipe tested", transferred), GeneOverlap's default genome size beside; the decoder unavailable → R14's per-donor
  recipe on dk-ctx (perdonor-dk), labelled "re-derived (per-donor parcel recipe, dk-ctx), not the decoder", list
  p < .01 two-sided. Descriptive; no count moves.
- **Checks:** `test_wp4_phase1` S1 (three decoders, one GET each), U2 (the overlap record).

## 8. WP4 phase 1's implementation choices: pin or no pin
| item | verdict | reason |
|---|---|---|
| Pretzsch's list sign per row (CT / SA × positive / negative) | no pin needed | the TSV's direction and set_S texts name it ("SA-negative list", "the CT-negative … list"); a row without it reads "not computable" |
| V-DK-subcortex member columns of a gated set = V-DK's | no pin needed | the same matrix; the class context's Universe rule drops constant columns at use (U14); the S-build has no V-DK-subcortex class |
| the gated sets built by the frozen `s_build.build_set` loaded from verified bytes | no pin needed | §11 "by the frozen §1.6 rules", literal |
| R13's bicor record as a G2 preflight condition (`run_manifests/material/G2/r13_bicor_check.json`) | no pin needed | §11 `:1482` "Before any G2 map is read … pinned and tested"; recorded 2026-10-16: 18 / 18 with Docker, WGCNA PASS |
| a G2 run's sources (`run._real_sources`: WP4Sources for --gate G2) | no pin needed | routing; the ungated branch is unchanged |
| the material stage refuses production until this amendment is frozen | no pin needed | the order RUN_PLAN §18 `:1806-1812` requires |
| reruns under §17 write `results/a1_run/rerun_<tag>/` (`run.py --rerun-tag`, the plant driver's too) | no pin needed | §17 (4) "both versions are reported": the first run's rows stay in place |
| R38's build in `artifacts/ahba/a1_builds/perdonor-hcpmmp1` (outside the WP2 MANIFEST; its record's sha256 in the G2 manifest) | no pin needed | amendment 2 R38, literal (the build follows the fetch in WP4) |
| (v2, B3) `wp4_material r38-build` refuses (exit 2, nothing read) before the HCP volume is read unless: the draft guard is lifted and gate G2 is open (production roots), R13's record passed, the paths are the layout's; the R15 download sha256s of the volume and the label list are passed through and checked by `build_perdonor_hcpmmp1` before any parse, and recorded in the build record | no pin needed | the volume is G2 material (§11's order: gate, R13, identity before any read) |
| (v2, C3) the G2 sources (`WP4Sources._m4`) refuse a production read until this amendment is frozen, and any manifest whose `scratch` flag differs from the roots' | no pin needed | a scratch manifest never feeds a production row |
| (v2, C8) Pretzsch's recipe uses the R38 build only if its record's `volume_sha256` and `label_list_sha256` equal the R15 downloads' sha256 (G2 manifest) | no pin needed | the build is the one made from the downloaded atlas |

## Changed (each a declared departure from a frozen text or frozen code)
1. **R16's tarball check** (`fetch_extract.py:1166-1171`, WP2 code): a size header no longer refuses (R51; amendment 3
   C9's residue).
2. **§11 `:1451-1452`** names `gia_mdd_paths.json` as the source of the lists' blob ids; it holds the MDD lists and the
   GEDAR maps only, so the nine ASD lists' (and R58's files') blob ids come from the commit's tree listing fetched at
   download (R55).
3. **§11 `:1466`** lists the volumes' sha256s as the "lh GIFTIs"'; both are held (R62).
4. **L14 is "(G1 only)"** (`RUN_PLAN.md:154`); pdfplumber 0.11.10 is asserted before Patel's PDF (R53; amendment 3's
   precedent for MOESM2).
5. **§11's local copies** (`:1460-1466`) do not list Hansen's predictors file, the Cammoun info or the Sadeghi workbook;
   they are held to the drafts' registered prefixes (R57, R60).
6. **The Hansen reproduction** runs a port of netneurotools 0.3.0's dominance analysis, not the installed package
   (R60); cross-checked once against the package in a throwaway container (v2, C2).
7. **(v2, C4) R63's overlap universe** is "the genes the decoder returned with a finite p", a transfer of R30's "genes
   the recipe tested" (R30 is written for Pretzsch's recipe, not for a decoder); GeneOverlap's default genome size is
   reported beside.
8. **(v2, C5) R55's duplicate genes** take the mean of their weights, carrying amendment 2 R42 (a)'s rule (written
   for the ungated sets) over to the repository lists; the number of duplicated genes is counted.
9. **(v2, B5) R58 (f)** v1 built the DEG sets by the TSV's definition in Python; v2 follows the TSV ("S re-derived" by
   the paper's script) and keeps the definition as the check (v1's computation is the cross-check).

## Not changed
- every registered definition, threshold, seed key and status order; R1–R50 as frozen; §8's print rule and steps 0–6;
- the T and legs of every G2 cell; the plants' blobs, constants, thresholds, n and constructions;
- the frozen gate files, G1's check and material; `src/asdg`, `src_register/`, the register maps and sets, the TSV;
- Seelemeyer: not auditable, its files never opened; Level 4 (R25): not auditable until an A4.

## Affected code (written in WP4 phase 1, on synthetic stand-ins; `tests/test_wp4_phase1.py`)
| reading | module | function |
|---|---|---|
| R51 | `wp4_material.py` | `r16_annot` (FS_TARBALLS order; headers recorded; `freesurfer_target(pinned_bytes=None)`) |
| R52 | `wp4_read.py`, `wp4_material.py` | `figshare_files`, `hcp_left_names`; `r15_hcp` |
| R53 | `wp4_read.py`, `wp4_material.py` | `patel_from_words`, `patel_parse`; `patel_reader` (the second parse) |
| R54 | `fetch_extract.py` (FE25), `wp4_read.py`, `wp4_material.py`, `wp4_sources.py` | `labelled_rule`, `_read_labelled`; `g2_label_parse`, `g2_normalise`, `giacomel_sheet_object`, `giacomel_compare`; `giacomel_target`, `giacomel_transform`; `g2_map` |
| R55 | `wp4_material.py`, `wp4_sets.py` | the list targets (tree / gia_mdd_paths refs), `raw_list_reader`, `raws_of`; `frozen_s_build`, `build_one`, `build_all`, `restate` |
| R56 | `wp4_read.py`, `wp4_sources.py` | `gedar_map`; `second_map` |
| R57 | `fetch_extract.py` (FE26), `wp4_material.py` | `search_rule`, `_read_columns_search`; `sadeghi_listing`, `prefix_target`, `deg_sheet`, `deg_transform` |
| R58 | `rbuild/r17.py`, `wp4_read.py`, `wp4_material.py` | `declared_r_version`, `r_release_at`, `bioc_for`, `r17_params`, `dockerfile_text`, `run_script`, `placement`, `DockerR17`; `r_script_requirements`, `ahba_hpa_pool`, `deg_set`, `deg_output_key`, `deg_list_rows`, `deg_check`; `r17_facts`, `run_r17`, `r17_outputs`, `deg_raws` (R17 now runs before the sets) |
| R59 | `wp4_read.py`, `wp4_sources.py` | `enigma_toolbox`, `liu_t3_map`; `g2_map` |
| R60 | `wp4_read.py`, `wp4_repro.py`, `wp4_sources.py`, `wp4_nnt_check.py` | `hansen_ct`, `hansen_pc1`, `hansen_predictors`, `cammoun_order`; `dominance_stats`, `hansen_dominance`, `HAN_NOT_BLIND`; `component`; the C2 cross-check |
| §8 (v2) | `wp4_material.py`, `ahba_extras.py`, `wp4_sources.py` | `r38_build_cli`, `r38_build`, `entry` (the download sha256); `build_perdonor_hcpmmp1(label_list_sha256=)`; `_m4`, `pretzsch_recipe_inputs`, `giacomel_order_matched` |
| R61 | `wp4_read.py`, `wp4_sources.py` | `pretzsch_csv`; `pretzsch_dk`, `pretzsch_recipe_inputs` |
| R62 | `wp4_layout.py`, `wp4_sources.py` | `identity_records` (both probes); `identity4` |
| R63 | `wp4_material.py`, `wp3_decoder.py`, `wp4_repro.py` | `run_decoders` (`run_decoder(key=)`); `leyhausen_row` |

## Questions for the orchestrator
1. (v1 Q1-Q4 answered 2026-10-16: R55, R60 and the atlas deferral accepted; R58 (f) changed as B5 asks.)
2. **R58 (f)'s failed check**: a script set whose m (or the ASD pool) differs from the definition leaves the cell
   "not computable"; the alternative is to keep the script's S and only label the mismatch. Confirm before freezing.
   **Answer (orchestrator, session 14, 2026-10-16): "not computable".** A set that does not meet the registered
   definition is not the registered test. Not taken: keeping S with a mismatch label.
3. **R58 (f)'s list rule** (Dx token + `thr<t>` + a `logFC` header) is chosen without the script; if the script
   writes its DEG lists in another form, the 18 cells read "not computable (… no identifiable list …)".
   **Answer (orchestrator, session 14, 2026-10-16): a format-only parser adaptation is allowed.** If the script writes
   its DEG lists in a different layout (file names, header tokens, delimiters), the parser may be adapted to locate the
   same lists. The adaptation is recorded as a deviation and labelled post-exposure (it is chosen after the script's
   output is seen). The R58 (f) content check (m, and the ASD pool = 3,599) is unchanged and must pass; a failed check
   still reads "not computable" (answer 2). Why: the content check pins what the list is, so a layout-only adaptation
   cannot steer an outcome. Not taken: 18 cells "not computable" for a file-layout difference alone.
