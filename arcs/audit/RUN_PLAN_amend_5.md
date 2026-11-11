# RUN PLAN AMENDMENT 5 — A1 `audit`: R17's placement fixed; three post-exposure readings as a second version (POST-EXPOSURE)

> **Status: v2 DRAFT, POST-EXPOSURE. Not frozen.**
> - v1 was written 2026-10-21 by the WP4 worker at HEAD 7768bc0, after run 4 of the G2 material stage
>   (`wp4_launch --commit 7768bc0 --stop-after-material`, exit 0, final manifest `11cf23ce…`).
> - v2 applies asdg-skeptic's review of v1 (grade A, plus B and C findings) and the orchestrator's session-15 decisions.
>
> **POST-EXPOSURE.** Every mismatch below was seen before this text was written:
> - the R17 run's error and script lines;
> - the Pretzsch name counts;
> - the Giacomel Subcortical label forms;
> - the Liu T3 file names.
>
> No G2 claim pass has run. No G2 map value, set member, correlation, p or verdict was seen.
>
> **v2's rule (RUN_PLAN §18 `:1812`).** "A reading that could only apply to material already opened reads 'not auditable
> (definition not applicable)' instead." R61', R54' and R58' (d) are such readings, so they never replace the primary:
> - the **primary** status of their cells is the frozen "not auditable (definition not applicable: …)" (§6 entries
>   A7–A9 below);
> - their computation is a **second version**, labelled "post-exposure version (amend_5)", reported beside the
>   primary (§17 (4) "both versions are reported");
> - the second version never enters the interim headline population, a tested-only denominator, a composition count or
>   a BH family.
>
> R58' (a)–(c) and (e) are **defect fixes**: they implement R58 as written, so they are primary.
>
> Until the orchestrator freezes this file (sha256 in `FROZEN.txt` and `wp4_layout.AMEND5_FROZEN_SHA256`),
> `wp4_layout.production_allowed()` refuses a production run of the G2 material stage and the G2 sources (DRAFT_GUARD5).
> This amends `RUN_PLAN.md` v3.1 as amended by `RUN_PLAN_amend_1.md`–`_4.md` (FROZEN).

## Versions
| version | date | written at | sha256 | review |
|---|---|---|---|---|
| v1 | 2026-10-21 | 7768bc0 + the code of 4d20eb6 / c8d746b / 759c39c | aa93e0fbdfc82801… | asdg-skeptic: A (R61' / R54' / R58' (d) replace the primary on opened material, against §18 `:1812`), B (R54's left mapping is an inference; the line-130 label must reach the §16 cells), C (does line 130 bite; are the 6 pairs make.names) |
| v2 | 2026-10-21 | 759c39c + the code of the commit that adds v2 | stated at hand-off | A, B and C applied; awaiting the orchestrator |

## 0. Authority, exposure, what was read
- **Authority:** RUN_PLAN §18 `:1806-1812`, and the orchestrator's session-15 decisions, quoted in each reading's Text.
- **Exposure.** The worker saw the following, each as counts, code locations or the code's own vocabulary:
  - R17's stderr: the error class, the script's line 36, and the form of its paths. These are absolute paths on the
    author's machine under two roots; the author's name in them is never written here.
  - The script's lines 33–40, 54 and 101–141: the read paths, the variable-held path, the write calls and line 130.
  - Pretzsch's derived CSV: 360 names in one column, 174 of the 180 pinned left names exact. The other 6 differ only
    by '-' (label list) against '.' (CSV), and each of the 6 is exactly R's `make.names` of the pinned name (C, below).
  - Giacomel's Subcortical sheet, at both commits: 7 labels without a side marker. 6 are DK subcortical names; 1 reads
    "Pallidus".
  - The Liu T3 pinned copies: their publisher file names hold the token "case" (from "case-controls"), which the
    frozen guard's BARE_SUBJECT pattern matches.
  - eda33ab's six GEDAR files: their sha256s only. MDD differs from ASD at all three thresholds (C, below).
- **Not seen:** no G2 map value, set member, weight, correlation, p or verdict. Every check above went through the
  wrapper on scratch roots, which saved no value.

## 1. Classification (v2)
| reading | kind | version | why |
|---|---|---|---|
| R58' (a) absolute read paths placed by the unique longest tree suffix, both roots mounted | defect fix | primary | R58: the inputs "are placed at the paths its read calls name"; v1's code placed them only at repository-relative paths |
| R58' (b) variable-held read paths followed | defect fix | primary | the same clause: line 54's read call names its path through a variable assigned one literal |
| R58' (c) the script's output folders pre-created | defect fix | primary | the run's environment, as the mounts are: the folders exist on the author's machine; nothing in the script is edited |
| R58' (e) containment of every third-party folder, path and root | defect fix (security) | primary | refuses, never widens |
| E1 the path-screen exemption for two declared group-level publisher names | handling | primary | a privacy-screen false positive, not a reading of any value; the content screen is unchanged |
| R61' Pretzsch '.' = '-' | post-exposure reading | second version | could only apply to the CSV already opened (§18 `:1812`) |
| R54' (a) the 'pallidus' alias; (b) unmarked Subcortical → left | post-exposure reading | second version | as R61' |
| R58' (d) `mmc2(<n>).xlsx` = the pinned Sadeghi copy | post-exposure reading | second version | as R61' |
| L130 the line-130 label | label | both versions | changes no value |

**R17 on the primary path.** Without (d), the script's line 54 cannot read its workbook. The primary R17 run therefore
fails, and the 18 post-mortem DEG cells read the frozen "not auditable (definition not applicable: the paper's code not
runnable here)" (R17's fallback). The R17 rebuild with (d) is the post-exposure version.

## 2. §6 entries added (RUN_PLAN §6's form; the primary cells read these until an amendment decides otherwise)
| id | item | frozen text | until an amendment, the cells read (primary) |
|---|---|---|---|
| A7 | Pretzsch eTable13 label match (R61') | R61: "the one column holding all 180 left names of R52's label list, each once" | "not auditable (definition not applicable: the declared eTable13 layout not matched)" — the Pretzsch rows |
| A8 | Giacomel Subcortical labels (R54') | R54: the alias table (thalamus, accumbens); "fail closed as R42 (d)" | "not auditable (definition not applicable: the declared Giacomel sheet layout not matched)" — every row on a Giacomel Subcortical map (ASD or MDD column) |
| A9 | R17's Sadeghi workbook name (R58' (d)) | R58: "the Sadeghi workbook for a read path ending in its declared file name" | "not auditable (definition not applicable: the paper's code not runnable here)" — the 18 post-mortem DEG cells |

- A7–A9 move counts only through the frozen statuses, which already provide them. Their second versions move no count.
- The rows they bear on are listed by `wp4_sources.amend5_readings`. In the synthetic report test that is 98 G2 cells:
  18 DEG cells, the Pretzsch rows, and every row on a Giacomel Subcortical map.

## R61'. Pretzsch's label match: '.' and '-' are equal — SECOND VERSION ONLY
- **Text:** "R61': HCP-MMP1 label match treats '.' and '-' as equal, keeping the one-to-one check and the count of 180";
  v2: "the PRIMARY status stays the frozen 'not auditable (definition not applicable: …)' … the amend_5 computation
  is produced as a SECOND version".
- **Reading:**
  - **Primary:** R61 as frozen (`pretzsch_csv(amend5=False)`, an exact match). On run 4's CSV no label column holds
    the 180 names, so the primary is A7's status.
  - **Second version** (`amend5=True`): names compared through `hcp_name_key` ('.' → '-'). The pinned names' keys
    must be 180 and distinct. The label column is the one column holding all 180 keys, each once.
  - **C:** every pair matched only through the rule must be exactly R's `make.names` of the pinned name
    (`r_make_names`: every character outside `[A-Za-z0-9._]` becomes '.'); otherwise the second version refuses too.
  - On run 4's CSV: 180 of 180 rows, 6 pairs, all 6 `make.names` pairs.
- **Why outcome-neutral:** it undoes only `make.names`' own transcription; the one-to-one match and the 180 count
  decide; it is a second version and counts nowhere.
- **Checks:** X7, which covers:
  - the primary refusing the 6 pairs;
  - the second version passing them;
  - refusals: a missing name, two pinned names on one key, 179 names, and a pair that is not `make.names`.

## R54'. Giacomel's Subcortical labels — SECOND VERSION ONLY
- **Text:** "R54': 'pallidus' aliases to pallidum, and unmarked subcortical labels map to the left aseg ids (as R54's
  '7 left aseg ids' implies)"; v2 as R61'.
- **Reading:**
  - **Primary:** R54 as frozen (`giacomel_sheet_object(amend5=False)`). An unmarked label refuses, and R54's alias
    table is unchanged (thalamus, accumbens). On run 4's sheets, 0 of 7 labels match, so the primary is A8's status,
    and the c022a29 comparison reads "not compared (a sheet not read)".
  - **Second version** (`amend5=True`):
    - (a) `pallidus` → `pallidum` (`wp4_read.AMEND5_ALIASES`);
    - (b) an unmarked Subcortical label stands for the left aseg id.
  - Thickness stays marker-only in both versions. On run 4's sheets the second version matches 7 of 7, and the
    registered order matches.
- **B (stated):**
  - (b)'s left mapping is an **inference** from R54's "Subcortical: the 7 left aseg ids each once". R54 states no rule
    for an unmarked label.
  - 'pallidus' is the **only** alias added after the label was seen. R54's thalamus and accumbens aliases were fixed
    before any material was opened.
- **Why outcome-neutral:** it places the sheet's one value per structure on the parcel R54 names; it is a second
  version and counts nowhere.
- **Checks:** X8, which covers:
  - the primary refusing the run-4 forms;
  - the second version reading them;
  - refusals: an unknown name, a right marker, an unmarked Thickness label;
  - the marked form reading in both versions.

## R58'. R17's placement of the paper's inputs
- **Text:** "match each absolute path to the e045bc5 tree by its unique longest suffix (refuse if ambiguous), mount
  the staged copy at both absolute roots, pre-create the output folders, and make r_script_requirements follow
  variable-held paths (line 54 twas_path). The DK file is fetched from e045bc5 by blob id. mmc2(1).xlsx is accepted as
  the Sadeghi workbook only if the staged file is the pinned Sadeghi copy (sha256 match); record it"; v2: "(a) and (b)
  are DEFECT FIXES … primary".
- **Reading (primary: (a), (b), (c), (e)):**
  - (a) **Absolute read paths.** A read path starting with '/' is placed by the longest repository path of the
    e045bc5 tree that is its suffix. The path minus that suffix is an absolute **root**, and the roots' last component
    anchors the script's other absolute strings (the second root).
    - Refused: two equal-length suffixes, nested roots, and a root that is not a plain absolute path.
    - Each root is mounted onto the one repository copy (`docker run -v <copy>:<root>`, beside `/work`).
    - Nothing in the script is edited. `--network none` and the working-directory rule are unchanged.
  - (b) **Variable-held paths.** A read call whose path argument is a variable assigned exactly one string literal is
    read as that literal (line 54). The count is `n_read_vars`.
  - (c) **Output folders.** Folders the write calls name through `paste0(<such a variable>, "<literal>")`, and the
    assigned absolute folder literals, are created under the copy before the run. The count is `n_out_dirs`.
  - (e) **Containment.** Every folder, staged path and root taken from the script must pass two checks; else it
    refuses by a fixed `REFUSALS` text:
    - no '\', ':' or NUL, no leading '/', and no empty, '.' or '..' component;
    - `(copy / rel).resolve()` lies inside `copy.resolve()`.
    Roots are plain absolute posix paths, never '/', `/work` or below it.
  - Tree files the placement resolves (the DK file) are downloaded from e045bc5 by blob id with R55's identity.
  - The roots and folders are never recorded, because they hold the author's name; the manifest records only their
    counts.
- **Reading (second version only: (d)):** a read path whose file name is `mmc2(<n>).xlsx` stands for the Sadeghi
  workbook only if the staged file's sha256 equals the pinned Sadeghi copy's. The record holds
  `sadeghi_dup_name {applied, sha256_match, sha256}`.
  - The primary run never applies (d): its line 54 fails, and its 18 DEG cells read A9's status.
  - The second version's run rebuilds the DEG lists and maps; its sets are built by the same frozen S-build into
    `register_sets/post_freeze/G2_a5/`.
- **Why outcome-neutral:**
  - (a)–(c) are R58's own clause.
  - The inputs are the same identity-checked bytes, and the script, the image, the packages and R58 (f)'s content
    check (m, the 3,599 ASD pool) are unchanged.
  - (d) is a second version and counts nowhere.
- **Checks:** X9 (placement, (b), (c), the name rule, nested roots, a Docker run with both roots), X13 (containment),
  R1, A5.

## L130. The paper's line 130 runs as published; its rows are labelled
- **Text:** "The paper's line-130 bug (gw_asd written into the MDD TPRS files) runs AS PUBLISHED. Add the label 'the
  paper's script writes the ASD values into the MDD TPRS files (line 130)' to every MDD-TPRS-derived row, and do not
  fix the paper's code"; v2 (B): "report_cells.py joins wp4_sources.row_labels so the line-130 label reaches every
  affected §16 cell".
- **Reading:**
  - The script is not edited.
  - The label rows are the cells whose second map is a file line 130 writes, `MDD_literature_TPRS_thr_<t>.tsv`
    (R17's rebuild). These are the **6 MDD-set DEG cells** (GIA-MDD-DEG-MDDset-{01,05,10}-{ctx,sub};
    `wp4_material.line130_cells`).
  - `report_cells` joins `wp4_sources.row_labels`, so each such §16 cell carries the label (`labels_g2`). The
    manifest's `labels.line130` and the launcher's summary carry it too.
  - v1 also labelled the MDD list cells; v2 drops them (see C below).
- **B (stated):**
  - The MDD-set DEG cells' second maps are **descriptor-only**: all 6 cells are not in m (TSV
    `verdict_counted_in_m` = no).
  - **No MDD-vs-ASD contrast rests on them.** No G2 row of the TSV contrasts MDD with ASD (a search of every G2 row's
    fields for an MDD/ASD contrast found 0), and the ASD-set and MDD-set cells are separate rows.
- **C (line 130 bites?).** Checked by sha256 equality only:
  - **eda33ab:** the repository's GEDAR files are `results/<D>/<D>_TPRS_thr_<t>.tsv`, another file family than line
    130's `<D>_literature_TPRS_thr_<t>.tsv`. Their MDD and ASD sha256s **differ at all three thresholds** (run 4's
    records). Line 130 does not bite there, which is why the MDD list cells carry no label.
  - **R17's rebuild:** recorded at the run as `labels.line130.r17_mdd_equals_asd` ({t: true/false/null}) in each
    version's block. It is null on the primary path, where no file is written.
- **Checks:** X11, and test_report_cells "g2_line130_labels_and_the_post_exposure_version_beside_never_counted".

## E1. The path screen's declared exemption for pinned group-level copies (primary; FE17's application)
- **Text:** "add a declared exemption to the path screen for the publisher file names of pinned group-level copies (an
  explicit list of pinned sha256 + file name, here the two Liu T3 files). Every other name is still screened. Do NOT
  move the files."
- **Reading:**
  - `wp4_layout.SCREEN_EXEMPT` holds the two Liu T3 files, each as a name and a sha256.
  - Only with that exact name and those bytes is the wrapper handed a runner-built hard link (`<data>/<key>/carrier.csv`,
    the same bytes), so the publisher name is not screened.
  - Every other component, the link's path and the content are screened as before.
  - `fetch_extract.py` is unchanged; plants P18–P21 read it.
- **Operator step:** move each `carrier.csv` back to its pinned path, then remove the two folders under
  `E:\data\asdg\_quarantine\G2\`.
- **Checks:** X10.

## 3. How the two versions are produced and reported
- **Material stage:** one run writes both versions.
  - The manifest's `objects` hold the primary entries, under the frozen readings.
  - Its `post_exposure` block holds `{label, readings, objects, sets, deg_checks, giacomel_comparison, labels}`:
    - the amended objects are saved under `<key>_a5`, the entry naming them by `object_key`;
    - their carriers are used as found, with nothing fetched again.
  - Saved objects are never overwritten: the primary objects of run 4 are adopted byte for byte.
- **Claim passes:** `wp4_launch` runs the primary passes, then the same three passes with `A1_G2_VERSION=amend5` and
  `--rerun-tag amend5`. Their outputs go to `results/a1_run/rerun_amend5/G2/`. The G2 sources read the
  `post_exposure` block only under that version; the roots' `version` travels in the sources spec.
- **Report:** `report_cells` (G2 cells only) attaches the post-exposure version beside each affected primary cell
  (`post_exposure_version`, with `counted` = excluded), plus a "Labels and post-exposure versions" section in
  `cells.md`. It does so after the cells are built and before any composition. The test asserts that the composition,
  the headline and the BH families are identical with and without the second version, and that every primary cell is
  unchanged.

## Changed (each a declared departure from a frozen text or frozen code)
1. R58's placement (R17 (h)): (a) absolute roots, (b) variable-held paths, (c) output folders, (e) containment.
   These are primary. Code: `rbuild/r17.py` `placement`, `absolute_placement`, `out_dirs_rel`, `safe_rel`,
   `contained`, `check_abs_root`, `run_script`, `DockerR17.run`; `wp4_read.r_script_requirements`;
   `wp4_material.r17_facts`, `run_r17`.
2. A second version for R61', R54' and R58' (d), beside the frozen primary (§6 entries A7–A9).
   - Code: `wp4_read.pretzsch_csv(amend5)`, `r_make_names`, `hcp_name_key`, `AMEND5_ALIASES`,
     `giacomel_sheet_object(amend5)`, `g2_normalise(aliases)`.
   - Code: `wp4_material.run_material` (the `post_exposure` block), `run_amended`, `r17_facts(post_exposure)`;
     `wp4_layout.Roots.version`, `set_dir`, `VERSION_*`, `AMEND5_*`.
   - Code: `wp4_sources.WP4Sources._m4` (the overlay), `amend5_readings`; `wp4_launch` (the `_amend5` passes).
3. L130's label: the MDD-set DEG cells only, and the bite record. Code: `wp4_material.line130_cells`, `line130_record`;
   `wp4_sources.row_labels`; `report_cells.annotate_g2`, `g2_md`.
4. `report_cells.py` joins the G2 labels and the post-exposure version. `wp4_launch.DIFF_ALLOWED` now admits
   `report_cells.py`: the report writer is read by no plant and by no row computation, and the change touches G2
   cells only (the ungated report is unchanged, as the test checks).
5. E1. Code: `wp4_layout.SCREEN_EXEMPT`, `wp4_material.screen_exempt_target`.
6. The DRAFT guard for this file. Code: `wp4_layout.AMEND5_*`, `DRAFT_GUARD5`, `frozen_check(rel=)`,
   `production_allowed`; `wp4_launch.pins`, the amend_5 freeze refusal, and DIFF_ALLOWED for this file.

## Not changed
- Every registered definition, threshold, seed key, null, status text and status order (`claims_register.md:1102-1103`).
- The primary readings R54, R61, and R58's Sadeghi name rule.
- R58 (f)'s content check, and R17's image, packages, Bioconductor rule and network none.
- The paper's script, which runs as published.
- `fetch_extract.py`, `privacy_wrap.py`, the frozen privacy guard, `run.py`, and the plants.

## Open for the orchestrator (found while writing v2; not changed)
- `wp4_material.rows_by_cell_of` reads `in_m` as `bool(r.m_membership)`. The field is the text "yes"/"no", so every G2
  cell's set file records `in_m` true, and the restatement's `n_in_m_not_testable_lt5` would overcount (run 4: 0
  not testable, so 0 either way).
- The fix (`r.in_m`) changes the set files' bytes. Set files are never overwritten, so it needs your decision: a set
  manifest version, or the field read at use from the TSV.

## Affected code
| reading | file | functions / constants | test |
|---|---|---|---|
| R61' | `wp4_read.py` | `pretzsch_csv(amend5)`, `hcp_name_key`, `r_make_names` | X7, A4 |
| R54' | `wp4_read.py` | `AMEND5_ALIASES`, `g2_label_parse`, `g2_normalise`, `giacomel_sheet_object(amend5)` | X8, A1, A3 |
| R58' | `rbuild/r17.py`, `wp4_read.py`, `wp4_material.py` | `placement`, `absolute_placement`, `out_dirs_rel`, `safe_rel`, `contained`, `check_abs_root`, `run_script`, `DockerR17.run`, `r_script_requirements`, `r17_facts`, `run_r17` | X9, X13, R1, A5 |
| two versions | `wp4_material.py`, `wp4_layout.py`, `wp4_sources.py`, `wp4_launch.py` | `run_material`, `run_amended`, `Roots.version`, `set_dir`, `_m4`, `amend5_readings`, the `_amend5` passes | X14, X15, W4 |
| L130 | `wp4_material.py`, `wp4_sources.py`, `report_cells.py` | `line130_cells`, `line130_record`, `row_labels`, `annotate_g2`, `g2_md` | X11, test_report_cells (g2) |
| E1 | `wp4_layout.py`, `wp4_material.py` | `SCREEN_EXEMPT`, `screen_exempt_target` | X10 |
| guard | `wp4_layout.py`, `wp4_launch.py` | `AMEND5_*`, `DRAFT_GUARD5`, `frozen_check`, `production_allowed`, `pins` | X12, A5 |
