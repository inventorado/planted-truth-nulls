# RUN PLAN AMENDMENT 2 — A1 `audit`: readings WP2 found unpinned

> **Status: v2.1, FROZEN by the orchestrator (2026-10-02; `FROZEN.txt`).** The re-check of v2 returned 0 A / 1 B / 5 C;
> v2.1 answers all six and was not re-read by the skeptic before freezing (orchestrator, standing delegation; the global
> names `thickness` / `surfarea` in R42 (d) confirmed by the orchestrator). v1 was written on 2026-10-02 at HEAD
> d7cb388. The asdg-skeptic review of v1 returned "not-verified" (0 A / 4 B / 7 C), and confirmed that:
> - the amendment is pre-exposure and the blobs match;
> - R37, R38's G2 placement, R39's L + R + B and R40 are faithful.
>
> v2 answers every finding; the closing table lists them. It was written at HEAD 05646de. The A1 code cited is at
> 4ad80ec: `forms.py` 7b680f04, `multiverse.py` 564aa4c5, `run.py` 0db874d9, `plants/` as in §8.1.
>
> **v2 → v2.1.** The re-check of v2 returned "not-verified" (0 A / 1 B / 5 C). v2.1 makes these changes:
> - it corrects §8.2's orchestrator statement, which was partly false;
> - it adds `plant_mode.py` to §8.1 and pins the plant constants by value (§8.1b);
> - it declares that DEV keys are the official keys, re-scores dev2's P24 / P25 records (§8.2), tightens R42 (d)'s
>   label rules and corrects R38's citation.
>
> This amends `RUN_PLAN.md` v3.1 (FROZEN, sha256 16c60232…) as amended by `RUN_PLAN_amend_1.md` v2.1 (FROZEN, 8e06d60e…).
> - **Readings R37–R43** are in the plan's §5 format: **Text** → **Reading** → **Why now** → **Plant**. Each also shows the
>   options and why the one chosen is the faithful one.
> - **§8** classifies every implementation choice WP2 listed, pins `plants/` by blob (§8.1) and declares the DEV passes
>   (§8.2).
>
> No registered definition changes (`claims_register.md:1102-1103`), and no frozen file is edited.

## 0. Authority, exposure, what was read
- **Authority:** RUN_PLAN §18 (`RUN_PLAN.md:1806-1808`): a reading found missing goes to a frozen amendment, which is
  pre-exposure for material not yet opened, provided no claim result exists.
- **Pre-exposure.**
  - No claim result and no official plant result exist. At 05646de there is no `arcs/audit/results/a1_run/`, no
    `register_maps/post_freeze/` or `register_sets/post_freeze/`, and `run_manifests/plants/` holds P1 only (existence
    checks only).
  - The orchestrator states that this audit has opened no gated material.
  - None of R37–R43 uses a value of any map, set, carrier, supplement, matrix or sample.
- **Exposure declaration (adds to RUN_PLAN §9, F2, `:1390-1401`).** Every reading here was written after the
  exploration lane's 14:25–14:30 exposure (2026-10-01) and uses none of its values.
  - **ENIGMA-touching readings:**
    - R37 (the §4.1 checks of Patel, Giacomel and Liu T3);
    - R41 (Giacomel's signed-weight cells, ASD and MDD);
    - R40, through R12 (HAN-C1-ourPC1);
    - R39 and R43, which apply to every claim as R2–R7 do.
  - **Readings that touch no ENIGMA-derived cell:**
    - R38: Pretzsch, LEAP;
    - R42: Liu T1, T2, T4, T5 (ungated; T3 is untouched).
  - **Pre-freeze exposures that bear on them** (`claims_register.md:120-135`):
    - item 1: Patel's eTable rows (R37);
    - item 1: Giacomel's shipped result tables and Tables S1–S3, ASD and MDD rows (R37, R41);
    - item 1: Liu SD4 / SD10 ASD rows and the first data row of every SD sheet, SD7 included (R42);
    - item 1: Pretzsch eTables 3–5 and the first rows of eTables 12–13 (R38);
    - item 1: Hansen's shipped dominance results (R40);
    - item 2: the Liu-note recomputation (R37);
    - **item 2: A1's R2** (`results/e4_r2_giacomel.json`, computed before the freeze): the eda33ab-map ρ's of the MDD
      cells, .5287 / .5466 / .5310, and of the ASD combined cortical cells, −.1505 / .4125 / −.0534 (R41).

    None of these values is used.
- **Read by this author:**
  - this programme's `CLAUDE.md`;
  - RUN_PLAN R10–R15, R24, R27, R31, §7, §14 and §18;
  - amendment 1;
  - `prereg.md:44-77, :115-156, :290-300`;
  - `claims_register.md:104-118, :120-135, :280-332, :1007-1050, :1266-1275, :1462-1478, :1550-1565, :1655-1682,
    :1727-1745, :1764-1783, :1947-1972`;
  - TSV fields, read by script (row, cell_id, claim_form, T, direction, set_S / set_id, reproduction,
    published_value_and_location, analysis_class, status, verdict_counted_in_m);
  - the engine `src/asdg/{brainspan,genesets}.py`;
  - `a1_audit/{forms,multiverse,run,repro,reparcel,fetch_extract,ahba_builds}.py` (docstrings and the code cited) and
    `plants/*` (PLANT CHOICE lines);
  - `e4_ahba_matrices.py`, `e3_plants.py:42-47`;
  - abagen 0.1.3's `allen.py`, `matching.py`, `samples_.py`, `correct.py` and its bundled `atlas-desikankilliany.csv`
    (labels only);
  - the DEV plant outputs (`…\scratchpad\wp2\dev1…dev4`, provenance blocks only: synthetic plant runs).
- **Not opened:**
  - any carrier, map, supplement (SD7 included), NeuroVault image, decoder output, AHBA matrix or sample frame;
  - anything under `E:\data\asdg\`;
  - `register_work/` and `explore/discovery/results/`;
  - the ENIGMA manifest table;
  - the values of any `results/*.json`.
- **Evidence.** Four synthetic scripts in `…\scratchpad\amend2\` (session 94ea0193):
  - `ds_gloss.py` (`env/venv_ref`: abagen 0.1.3, pandas 1.5.3, numpy 1.24.4);
  - `dev_verify.py` (the DEV outputs' provenance against git);
  - `c1_keys.py` (DEV keys recomputed with `seeds.py`, v2.1);
  - `c2_rescore.py` (dev2's P24 / P25 records re-scored, v2.1).

  Figures attributed to WP2 are quoted from the orchestrator's messages of 2026-10-02 and not recomputed, because no
  matrix was opened.

## R37. The reproduction check: the sign label applies to misses only (item 1)
- **Text:**
  - "Reproduction check: our T must equal the paper's reported value ±0.05 (r, ρ, R², β). A miss … is flagged 'not
    reproduced'" (`prereg.md:120-122`).
  - "|ours − published| ≤ .05 → **reproduced**, else **not reproduced** (a sign opposite to the published one is 'not
    reproduced (sign)'; no re-orientation after the fact)" (`claims_register.md:321-322`).
  - Dear: "(an opposite sign → 'not reproduced (sign)')" (`:1742-1743`).
  - R27: "The check is |ours − published| ≤ .05, with sign opposite → 'not reproduced (sign)'" (`RUN_PLAN.md:980-981`).
    R27's wording reads like (A); the register governs (`:63-64`).
  - Open: opposite signs with |ours − published| ≤ .05. This is possible only when |published| ≤ .05.
- **Options:**
  - (A) the sign overrides the tolerance;
  - (B) the tolerance decides, and the sign sub-labels misses.
- **Reading: (B).**
  - The claim is reproduced iff |ours − published| ≤ .05.
  - A miss is "not reproduced (sign)" iff both values are non-zero and of opposite sign; otherwise it is "not
    reproduced". A value of exactly 0 has no sign.
  - Ours is never re-oriented. For R², R²_adj and dominance (non-negative) the sign label never applies.
- **Why faithful:**
  - Prereg §4.1 defines the check as the tolerance alone. The register implements the prereg (`:57-58`) and may not
    redefine it (`:1102-1103`), and its parenthesis hangs on "else not reproduced".
  - For |published| > .05, (A) and (B) coincide.
  - (A) would add a failure condition, decided by the sign of noise near 0. That matters because an unreproduced
    full-verdict claim leaves the headline population (`:322-323`).
- **Which cells it can affect** (published values from the TSV; ours not computed: pre-exposure):
  - one in-m cell, GIA-C17 (published ρ .001);
  - the descriptor cells PAT-N1, N2, N3 and N5 (published mean bicor .019 / .034 / −.002 / .021). PAT-N4 (−.067) and
    PAT-N6 (−.079) lie outside .05.

  Giacomel's subcortical cells carry "not reproduced (documented source defect)" by registration (`:1464-1465`).
  Comparators read under a gate (RG-V01 / V02, Liu T4 / T5 from SD7, DEAR-C3) are not known yet.
- **Why now:** no reproduction value exists.
- **Plant: P17 extension (functional).** Each pair is (published, ours):
  - (+.03, −.01) → reproduced;
  - (+.03, −.03) → not reproduced (sign);
  - (+.20, +.26) → not reproduced;
  - (−.28, −.23) → reproduced;
  - (0, +.04) → reproduced;
  - (0, −.06) → not reproduced, with no sign label;
  - an R² pair never gets the sign label.

  **Must-fail variant:** an (A) labeller, caught on (+.03, −.01).

## R38. Pretzsch's per-donor HCP-MMP1 build: atlas_info, all parcels, the atlas's gate (item 2)
- **Text:**
  - "atlas_info as in §2" (`prereg.md:68`). §2 says: "Tissue class per parcel … and hemisphere (L / R / B, B = centroid
    |x| < 2 mm) are assigned … from atlas labels … before any expression is computed" (`:51-53`); the primary parcels
    are L + B (`:55`).
  - R14 (`RUN_PLAN.md:738-739`) and R15 (`:757-763`).
  - "A gate covers **everything** of its targets after the freeze: downloads, …, re-parcellation"
    (`claims_register.md:116`); "Material (after the freeze, each under its gate …): … HCP-MMP1 MNI volume"
    (`:1947-1953`).
  - §18's WP2 row lists "`venv_ref` builds (… R14 …)" (`RUN_PLAN.md:1741`).
  - TSV 523–526: "pFDR < .01, split by sign".
- **Facts.**
  - abagen matches a sample only to parcels whose hemisphere and structure agree (`matching.py:365-370`). With
    `norm_matched=True` it normalises over each donor's matched samples (`allen.py:474-489`). So the parcels handed to
    abagen change the left parcels' values.
  - Every frozen matrix was built on the whole atlas, with the primary rows taken afterwards (`e4_ahba_matrices.py:72,
    :108`; `e3_plants.py:42-47`). MIST64 applied "prereg §2's centroid rule as written" (`claims_register.md:1269-1272`).
  - The register's only HCP-MMP1 uses are Pretzsch's (`:1036-1041`, `:1746`).
  - abagen 0.1.3 classes AHBA hippocampal-formation samples as "subcortex/brainstem" (`samples_.py:21`). An HCP-MMP1
    parcel classed "cortex" therefore cannot receive them.
- **Reading.**
  - **Parcels handed to abagen:** the whole volume, every parcel of its label list (360 by the atlas's definition;
    counted from the list).
  - **atlas_info:**
    - hemisphere by §2's centroid rule, with centroids computed as `e4_ahba_matrices.centroids` does;
    - structure "cortex";
    - a centroid hemisphere that disagrees with the name's L_ / R_ prefix is counted, and the centroid rule governs.
  - **Build settings:** §3.1, `return_donors=True`, in `env/venv_ref`.
  - **Analysis parcels:** the 180 left parcels, by R15's name match.
  - **HCP-MMP1 parcels with no sample** (for example hippocampal-area parcels, after `samples_.py:21`) are counted and
    reported per donor. They are excluded by R14's own clause, which takes the slope "over that donor's parcels with
    samples" (`RUN_PLAN.md:741-742`). This bears on R14's descriptive reproduction only.
  - **The volume's gate:**
    - the volume and its label list are fetched **under G2 in WP4**, through §8's wrapper after `step3v_open()`, before
      eTable13 is read (R16's precedent for the annot);
    - **this moves the HCP-MMP1 part of R14's build from §18's WP2 row (`:1741`) to WP4.** The other per-donor builds
      stay in WP2;
    - `perdonor-hcpmmp1` follows the fetch in WP4. Its code path and plants are reviewed in WP2r on a synthetic volume.
  - **R14's per-gene p** is two-sided ("pFDR < .01, split by sign"; as `repro.py` reads it).
  - **Not adopted:**
    - a left-masked volume (it changes matched samples and normalisation relative to every frozen matrix);
    - label-prefix hemispheres (against the MIST64 precedent);
    - ungated fetching (`:116`, `:1947`).
- **Why now:** neither the volume nor eTable13 has been fetched.
- **Plant: P18 extension (synthetic).** A toy two-hemisphere cortical volume:
  - |x| = 1.5 mm → B;
  - an L_-named parcel with x > 2 mm → R, counted;
  - every structure is cortex;
  - every label reaches abagen's call (asserted on the arguments);
  - a parcel given no sample is counted and dropped;
  - the left set is selected by name.

  **Must-fail variant:** a left-masked volume. In addition, R14's p = 2·sf(|t|, df).

## R39. Multiverse cells: their parcels and counts; no crossing with ≥ 2 donors; MIST64 (item 3)
- **Text:**
  - "Primary: parcels with hemisphere L or B … Multiverse cell: bilateral (L, R, B) with abagen
    `lr_mirror='bidirectional'`. A parcel enters an analysis iff the map value is finite and the parcel has ≥ 1 AHBA
    sample (sensitivity: ≥ 2 donors). Counts … are reported per atlas × map" (`prereg.md:55-58`).
  - The cells (`:75-77`); "every surviving claim" (`claims_register.md:1073-1075`).
  - R11 (`RUN_PLAN.md:671-689`).
  - Component-level claims never survive (`prereg_amend_5.md:160`).
- **Facts.**
  - `multiverse.py` (564aa4c5) keeps the claim's primary parcels in every cell, the bilateral cell included
    (`:11-14`, `:63-80`).
  - WP2 reports that the dk leave-one-out cell without donor 10021 loses parcel 31.
  - None of MIST64's 9 rows (TSV 615–623) can survive.
- **Reading.**
  - **Each cell is an analysis.** A parcel enters iff y is finite there and **the cell's own matrix** has ≥ 1 sample
    there. The cells' counts:
    - the normalisation cells: the primary's counts;
    - a leave-one-out cell: the per-donor counts without the left-out donor;
    - the bilateral cell: those of its bidirectional build.

    Kept and dropped parcels are reported per cell.
  - **Parcel universe:**
    - the normalisation and leave-one-out cells: the primary parcels (L + B);
    - **the bilateral cell: every parcel of the class's tissue classes, L, R and B**, with atlas_info classes and
      centroids. A left-only map's cell is "not applicable" (R11).
  - **Not crossed** with the ≥ 2-donor sensitivity (prereg `:57`; R11 "beside the primary"). There are 10 cells.
  - **MIST64:** no cell is ever run, so R11's matrix list is complete; MIST64's ≥ 2-donor counts stay.
  - **A parcel-set change in a cell** (a parcel lost, or the bilateral cell's additions) can change a leg's exactness.
    Amendment 1's R32 then applies. For example, a bilateral subcortex-only class of 14 parcels has S2c over
    2^13 = 8,192 patterns and G6s at rank 13 → 8,192, both exact; S1c stays sampled.
- **Why faithful:** prereg `:56-57` defines the bilateral cell by its parcels (L, R, B), and the entry rule per analysis.
- **Why now:** survivors are unknown.
- **Plant: P22 extension.**
  - A leave-one-out cell with a planted all-missing row drops it (count 0, reported).
  - The bilateral cell runs on L + R + B. A cell restricted to the primary parcels must fail the parcel-set check.
  - The normalisation cells keep the primary parcels.
  - No ≥ 2-donor × cell record exists.
  - A MIST64 claim requests no cell.
  - A 14-parcel bilateral subcortical toy reports S2c and G6s exact and passes R32's floor assertion.

## R40. Differential stability: R12 confirmed; Benkarim's and Park's DS (item 4)
- **Text:**
  - R12 (`RUN_PLAN.md:695-700`): DS is `abagen.correct.keep_stable_genes(…, threshold=0.1, percentile=False, rank=True,
    return_stability=True)` "as abagen implements it", on per-donor V-DK restricted to the 34 left DK cortical parcels.
  - R31 (`:1062-1064`).
  - Benkarim: "DS ≥ .5" (TSV 506–517); Park: "DS > .5" on the decoder output (TSV 595–614).
- **Facts.**
  - abagen ranks each donor's profile over that donor's own regions (`correct.py:601`), then correlates the ranks over
    the regions both donors cover (`:606-609`).
  - R12's gloss (a Spearman correlation re-ranked over the shared regions) equals abagen's value iff coverage is equal.
    In `ds_gloss.py` the maximum difference is 2.2e-16 with equal coverage and .0184 without.
  - On the real matrices, WP2 reports a maximum difference of .0078, with 44 dk-ctx genes on opposite sides of .1.
- **Reading.**
  - **R12:** the DS is abagen's function, as named; this is confirmed.
  - **Benkarim:** R12's DS vector (the same function, per-donor V-DK, dk-ctx's 34 parcels), with the threshold ≥ .5.
  - **Park, threshold > .5:**
    - if the decoder output carries the DS it filtered on, that column;
    - otherwise, and for the per-donor fallback (R28), R12's DS vector. Decoder genes absent from R12's 15,633-gene
      vector are excluded and counted.
  - **Not adopted:**
    - DS over every V-DK region;
    - re-ranking within the shared regions.
- **Why now:** no decoded list has been re-derived (G1).
- **Plant: P17 extension.**
  - With unequal coverage, the runner's DS equals `keep_stable_genes` bit for bit. Must-fail variant: the re-ranked
    gloss.
  - Benkarim's vector has the same hash as R12's.
  - A DS of exactly .5 is kept by ≥ and dropped by >.
  - **Park, both branches:**
    - a synthetic decoder output **with** its own DS column (that column is used);
    - one **without** it (R12's vector is used, and a planted decoder gene absent from the vector is excluded and
      counted).

## R41. The signed-weight gene legs: matrix, observed value, registered outcome, weight order (item 5; U-F1)
- **Text:**
  - "Descriptors: the paper's weighted GEDAR map ρ with y (…), our class-stratified site leg on ρ, and G1–G5 and J1 with
    S's weights carried over (each null set receives S's weight vector in a random order)"
    (`claims_register.md:1469-1473`; MDD `:1474-1478`).
  - TSV 115–117 (GIA-MDD-C1 / C5 / C10): "prereg §8's question 'does it survive G1-G5 and J1' answered by descriptor
    legs with S's weights carried over, plus the class-stratified site leg on rho, on the eda33ab MDD GEDAR map". Their
    reproduction is "Spearman rho of the MDD map with the TWAS-z-weighted GEDAR score on our matrix vs .531 / .547 /
    .529 (±.05)".
  - The ASD combined cells' reproduction is "… on our matrix vs the published rho (±.05)" (TSV 103, 105, 107).
  - "whether Giacomel's MDD/ASD results survive G1–G5 and J1 is a registered audit outcome" (`prereg.md:296-297`).
  - "G1 random: uniform from the matrix universe" (`prereg.md:136`).
  - Set scores are on "the §3.1 matrix of the analysis class" (`claims_register.md:283-284`).
  - R24 (`RUN_PLAN.md:914-915, :927-929`).
- **Options:**
  - the null maps' matrix: (i) the class's §3.1 matrix, or (ii) the authors' AHBA matrix;
  - the observed value: (a) ρ(y, b) with the paper's map, or (b) T_S = ρ(y, b_S), S's weighted score on the nulls'
    matrix.
- **Reading: (i) + (b), with the registered outcome conditioned on reproduction.**
  - **Null maps.** A null set R, drawn by its leg's frozen sampler from the class universe, receives S's weights in a
    random order. Its map is b_R = Σ_j w_j X[:, R_j] / Σ_j w_j on the class's §3.1 matrix, and ρ(y, b_R) is compared
    exactly (amendment 1, R32 (b)).
  - **Observed value.** It is T_S = ρ(y, b_S), b_S = Σ_{g∈S} w_g X[:, g] / Σ w_g on the same matrix. J1 is computed on
    the same matrix.
  - **The registered outcome** (prereg `:296-297`). "Does it survive G1–G5 and J1" is answered by T_S's legs **only if
    T_S passes its §4.1 reproduction check**: T_S is the reproduction functional of TSV 103 / 105 / 107 and 115–117,
    checked against the published ρ (MDD .531 / .547 / .529). Otherwise the cell reads **"not answered (T_S not
    reproduced)"**, and its legs are still reported as descriptors. A T_S that is not the paper's value does not test
    the paper's result.
  - **Reporting.** The registered descriptor T (ρ with the paper's map) and its site leg are reported as registered, with
    T_S beside them.
  - **Zero weight sum.** If Σ w = 0, the gene legs read "not computable (S's weights sum to 0)".
  - **Weight order (U-F1, pinned).** Each leg's sampler draws all its sets from the leg's generator unchanged (R7). Then,
    from the same generator, it draws one `rng.permutation(m)` per set in set order, and member R[k, perm_k[j]] receives
    w_j. J1 keeps R7's order, then draws the orders.
- **Why faithful.**
  - A null is a null for the value it is compared with only if both are built the same way. The gene legs draw from the
    class universe, which the authors' matrix need not contain.
  - The registered question concerns the paper's result. Our legs answer it only where our functional reproduces that
    result.
- **Why now:** no Giacomel material has been opened by this audit, and the reading uses no value.
- **Plant: P15 extension (synthetic).**
  - The null maps and T_S are built on the class matrix (hash).
  - The (ii) + (a) variant is caught on a toy whose "authors' matrix" carries a planted gene-wise offset.
  - Σ w = 0 → "not computable".
  - A T_S outside ±.05 of a planted published value → "not answered (T_S not reproduced)"; one inside it → the outcome is
    answered.
  - The weight orders are drawn after the sets (a variant drawing them before is caught).

## R42. Liu's gene-set-only build: duplicates, scale, samples, SD7's labels, T4 / T5 label sets (item 6; U-F3, U-F5)
- **Text:**
  - R10 (`RUN_PLAN.md:641-646, :656-658`): U_stat; the coexpression "over those same samples"; "a label's value is the
    mean over its samples"; "Hemispheres are pooled per DK name if and only if SD7's label column names
    hemisphere-merged labels (read from the ungated SD7's label column before any value)".
  - `prereg.md:149-151` (log2(RPKM + 1); "duplicate BrainSpan symbols averaged"), and `:298` ("ENIGMA subcortical CSVs
    have 16 rows incl. both lateral ventricles; the ventricles are dropped"); `brainspan.py:31-41`.
  - TSV 473–474 (T4, T5).
  - "the same statistic computed from the paper's SD7 values" (`claims_register.md:1680-1681`).
- **Reading.**
  - **(a) Duplicate symbols.** Columns sharing a symbol after the HGNC mapping are averaged per sample (BrainSpan on the
    log2(RPKM + 1) scale; AHBA as abagen returns them), before U_stat's rule, and counted.
    - Not adopted: dropping duplicates, keeping the first, or keeping both.
  - **(b) Coexpression scale (U-F5).** Pearson over the samples used, of log2(RPKM + 1) for BrainSpan and of abagen's
    per-sample values for AHBA.
  - **(c) Samples used (U-F3, confirmed):**
    - T1: every sample aged in pcw / mos / yrs;
    - the T2 family: the two structure groups;
    - T4: the cortical labels' samples;
    - T5: the hippocampus label(s)' and the other labels' samples.
  - **(d) Reading SD7's labels.** SD7's label column is read through §8's wrapper before any value, with counts printed
    only. Each label is normalised as follows:
    1. case-fold;
    2. strip the suffixes `_thickavg` and `_surfavg`;
    3. split on non-alphanumerics and drop the token `ctx`;
    4. **hemisphere marker:** any token in {l, r, lh, rh, left, right}, wherever it stands, is a marker and is removed;
    5. **glued marker:** if the remaining name is not a recognised name, but its first letter is l or r and the rest is a
       recognised name, that letter is a marker (for example "Lhippo", "Lthal" and "LLatVent"). "lateraloccipital"
       therefore stays a DK name. The recognised names are the abagen DK names, the aliases of step 6, `latvent`, and the
       global names `icv`, `thickness` and `surfarea`;
    6. **alias table (ENIGMA short subcortical names):** thal → thalamusproper; caud → caudate; put → putamen;
       pal → pallidum; hippo → hippocampus; amyg → amygdala; accumb → accumbensarea;
    7. the name must then equal an abagen DK name (`atlas-desikankilliany.csv`);
    8. **the marker's side selects the DK label id:** l, lh and left give the left id, and r, rh and right give the right
       id. An unmarked name stands for every DK label of that name.
  - **(d) Dropped labels (dropped and counted, never fail-closed).**
    - **Lateral ventricles:** `latvent`, with or without a marker (prereg `:298`'s ENIGMA rule).
    - **Global measures:** a label empty after normalisation (for example `L_thickavg`), or named `icv`, `thickness` or
      `surfarea` (ENIGMA's intracranial and whole-hemisphere rows, for example `ICV`, `LThickness`, `RSurfArea`). They
      are global measures, not regions.
  - **(d) Fail closed, with the count.** T4 and T5 read "not auditable (definition not applicable: SD7 labels
    unmatched)" when any of these occurs:
    - any other label matches no DK name;
    - a label matches more than one DK label (for example an unmarked bilateral name when SD7 is not merged);
    - **two SD7 labels map to one DK label.**
  - **(d) Declared:** a FreeSurfer-style `Left-Lateral-Ventricle` normalises to `lateralventricle`, which is neither
    `latvent` nor a DK name, so it fails closed. This is accepted: such a label signals a format the table does not
    cover.
  - **(d) Pooling: R10's frozen binary rule.** Hemispheres are pooled by DK name iff no SD7 label carries a marker
    (merged); otherwise they are not pooled. The per-sample build (DK label ids, both hemispheres) is the same in both
    cases; pooling groups its samples at analysis time.
  - **(e) The label sets of T4 and T5.**
    - The labels are the DK labels (pooled or not) that carry ≥ 1 sample **and** that SD7 lists. "Cortical" means
      abagen's DK structure "cortex".
    - Unpooled: r(hippocampus) is the mean of the hippocampus labels' values, and "other labels" means every other
      label, one value each. The same function is applied to SD7's values.
    - **T4 with no matched cortical label fails closed** ("not auditable (definition not applicable: no SD7 cortical
      label matched)").
    - T5 with no hippocampus label, or no sample in it, reads "not computable (no hippocampus label)".
    - Not adopted: pooling samples when SD7 is not merged, the left hemisphere only, and two T5 values.
- **Why now:** this audit has not read SD7's label column (its first data row was seen before the freeze, `:120-124`).
  The normalisation, the alias table and the binary rule are fixed before any SD7 label is read.
- **Plant: P16 extension (synthetic).**
  - Duplicates are averaged and counted; T equals the direct value.
  - Log2 coexpression (a raw-RPKM variant is caught).
  - SD7 label formats:
    - `L_bankssts`, `Lhippo`, `L_bankssts_thickavg`, `ctx-lh-bankssts`, and merged `bankssts` / `hippocampus`;
    - `LLatVent`, `L_thickavg` and `ICV` (dropped, counted);
    - `lateraloccipital` (not split);
    - `Left-Lateral-Ventricle` and one other unmatched label (fail closed);
    - two labels on one DK label (fail closed);
    - L / R markers selecting the left / right ids.
  - Pooled iff merged.
  - Unpooled T5 is the mean of the two hippocampus values.
  - A T4 with zero matched cortical labels fails closed.

## R43. Re-parcellation corners (item 7: RP1, RP2, RP3, RP7 of `reparcel.py`)
- **Text:**
  - The register's re-parcellation rules (`claims_register.md:1028-1048`).
  - Parcel values → dk-ctx: "each source parcel is assigned to the DK label holding the majority of its voxels (a parcel
    whose majority is outside every DK cortical label is dropped and reported); the DK value is the voxel-count-weighted
    mean of its assigned parcels; left hemisphere only" (`:1039-1041`).
  - The volume rule cites "A3's T2 rule" (`:1032`).
- **Reading:**
  - **RP1:** surface labels have no coverage threshold (the 50 % rule is the volume rule). A label with no finite vertex
    is dropped, and its share is reported.
  - **RP2, literal:** "the DK label holding the majority of its voxels" means a left DK cortical label holding **more
    than 50 %** of the source parcel's voxels. Otherwise the parcel is dropped and reported; this covers outside-majority
    parcels and parcels split with no label above 50 %.
    - This bears on Mamat's Schaefer-400 → dk-ctx cells (in m, G1; `:1295-1296`, `:1645`) and Pretzsch's
      Glasser → dk-ctx.
    - **`reparcel.py` changes after the freeze:** its plurality rule is replaced by the > 50 % rule.
  - **RP3:** the weight is the source parcel's own voxel count on its native grid.
  - **RP7:** nearest neighbour is A3's rule unchanged (index floor(v + .5)).
- **Why now:** no map has been re-parcellated.
- **Plant: P18 (22 / 22 at 9addaab), plus these cases:**
  - 55 / 45 → the 55 % label;
  - 40 / 35 / 25 → dropped (no label above 50 %);
  - 50 / 50 → dropped;
  - outside 55 % → dropped;
  - RP3's weights equal the source parcels' voxel counts;
  - the plurality variant (the code at 9addaab) must fail the 40 / 35 / 25 case.

## 8. WP2's implementation choices: pin or no pin (item 7)
| choice | verdict | reason |
|---|---|---|
| run.py U1, U4, U5, U11, U15 | no pin needed | bookkeeping and locations |
| U2 plant view | no pin needed | plant-only |
| U6 plant-scale descriptor counts | no pin needed | they feed no statistical plant's threshold. P12 uses component Level-0 permutations at the frozen 10,000 (`p12.py`; `RUN_PLAN.md:1139`), not U6's 500; P23, P10 and P22 are functional |
| U3 (G1+G2 rows in the G1 run) | no pin needed | moot while Dear is deferred (R20). If lifted, both gate checks must pass (`:1736`) |
| U7 (T_abs iff the T column names it) | no pin needed | checked: every computable decoded-list row (305) and 45 PLS pooled-list rows name it; the 25 without it are not auditable |
| U8, U9, U12, U13, U14 | no pin needed | register `:1769`, `:1474-1478`; amendment 1 R36 (d); R11; prereg §4 |
| U10 (direction parsing) | no pin needed | TSV: 429 two-sided, 246 one-sided, 15 n/a; the 2 conditional Dear rows are deferred |
| forms U-F1 | **pin** | R41 |
| U-F2, U-F4, U-F6 | no pin needed | pass placement; amendment 1 R36; R28 |
| U-F3; U-F5 | **pin** | R42 (c), (b) |
| SW_GENE_LEGS_UNPINNED; LIU_DUPLICATE_UNPINNED; LIU_T5_HIP_UNPINNED | **pin** | R41; R42 |
| fetch_extract FE1–FE14 | no pin needed | privacy, identity and storage; FE4–FE6 are literal reads checked by label matches and counts |
| reparcel RP1, RP2, RP3, RP7 | **pin** | R43 (RP2 changes to > 50 %) |
| RP4, RP5, RP6 | no pin needed | fail-closed format checks; RP6 is the register's rule |
| repro: R14 sidedness | **pin** | R38 |
| repro: other IMPLEMENTATION_READINGS | no pin needed | literal |
| plants' PLANT CHOICES | **pinned by blob (§8.1)**, with the DEV passes declared (§8.2) | they bear on plants, not claim statistics; the blobs fix them before any official result |
| venv_ref gaps: MIST64 multiverse; `perdonor-hcpmmp1` | no build; WP4 | R39; R38 |

### 8.1 `plants/` pinned by blob (git blob ids at 4ad80ec)
| file | blob |
|---|---|
| `plants/__init__.py` | cad6ccbc7e81da1d910edae0ec5d69a1209a81d9 |
| `plants/base.py` | 6329ae3bd24af15b2ca69a041849087d701d5ef7 |
| `plants/common.py` | 9338716fbdcdb2d410135b6bc2ac66e3209cca8e |
| `plants/construct.py` | de89fb89a518be5ee3ec1b6126582c2be65e92f1 |
| `plants/costs.json` | ac5d0d325c68dc992235b81cb40d8709108ec201 (sha256 7b1a72887de0c497…) |
| `plants/criteria.py` | b6081ac569bb28b90c92ecb3acb9f29cfeb7917b |
| `plants/driver.py` | b217a14d0532444cd6c121ee798c72b3326df079 |
| `plants/flaws.py` | eaedbb6ac96484d5a3743e4e3584234cc76fed81 |
| `plants/p03.py` | 80cc77b3693140961d9900a143264b2673c3ba42 |
| `plants/p04.py` | 3a13e27f56b205f8c972cf618e9dc8f2a602e553 |
| `plants/p05.py` | ffdc135fa6b4b28b70095ac6142d37bab31ea0cb |
| `plants/p06.py` | a4cbcd3d0079f57768e91006df9086a79cd1482c |
| `plants/p07.py` | 48bf4d93a6d3763e8465f0091005411341b6346d |
| `plants/p08.py` | d412c963846ab77760acf8d0a16a954ea7542438 |
| `plants/p11.py` | 932e2c48358561b8c16e9ae2bdf202ed9b5b129e |
| `plants/p12.py` | 8db69e50ccbff479e7c11eb88610bc1219404eb4 |
| `plants/p22.py` | 2b1912320d1836c75ee39699d7d2b43e22d7ad4a |
| `plants/p24.py` | 843cfbf83a97160e0b28f89f94722c749b05119f |
| `plants/p25.py` | bd6b19ee302f3b4a73c13beede86177c1c58bc00 |
| `plants/p26.py` | 2e3473877090dfbd591a14c8f329ff1d4744b347 |
| `multiverse.py` | 564aa4c5d282a1eaeffc7c56c3b875c9cd450a1a |
| `plant_mode.py` (plant-only code; added in v2.1) | 636fc486fa23b4e3de14a36e09bea657973c9e10 |

### 8.1b Plant constants pinned by value (they live outside `plants/`; read at 05646de = 4ad80ec)
| constant | value | where |
|---|---|---|
| `run.PLANT_K` | site 500, species 200, permutation 500, sets 200, surr 500, j1_sets 100 | `run.py:165` (imported by `plants/common.py:44`) |
| `run.PLANT_K_OVERRIDES` | P12: permutation 10,000 | `run.py:167` (also asserted in `p12.py:26, :81`) |
| `seeds.PLANT_WORD` | 900 | `seeds.py:51` |
| `seeds.PLANT_CLASS_IDS` | dk-ctx 2, V-AAL 11, V-DK 12, V-DK-subcortex 13, MIST64 14, V-CC200 17 (15 and 16 taken by forms' synthetic Liu data) | `seeds.py:141-144`; `run.SYN_CLASSES` uses them (asserted, `run.py:864`) |
| plant-integer mapping (`seeds.plant_int`) | P<n> → n; P3a and P3b → 3, kept apart by case ranges P3a [0, 1000), P3b [1000, ∞) | `seeds.py:145-146` and the function |
| `seeds.PLANT_DATA_WORD` | 1000 (the synthetic-data word) | `seeds.py:147` |

**Implementation after the freeze:** the official plant driver asserts these values at launch and writes them into every
plant header. The official battery runs the §8.1 blobs and these values unchanged. A change to either after an official
result is seen falls under §17.

### 8.2 DEV declaration: plant passes before the plants commit
Each statement is marked **verified** (by `dev_verify.py` against the DEV outputs' provenance and git) or **worker's
statement** (the plants worker's factual statement, relayed by the orchestrator on 2026-10-02).

- **The four DEV passes (verified).** All four ran from the working tree with the launch refused ("DEV (launch refused:
  L11, L13)" in every plant file), with outputs in the session scratchpad (`wp2/dev1…dev4`).

  | pass | n | HEAD | code hash | times |
  |---|---|---|---|---|
  | dev1 | 2 | c0ba47f | 5058c00685b0e5f3… | launch 23:34:40, written 23:40:09 (2026-10-01) |
  | dev2 | 6 | c0ba47f | 273be4e04e71be3e… | 23:41:16 – 23:52:17 |
  | dev3 | 20, P24–P26 | acda1ed | 48d5a99d2f5d3383… | 23:53:33 – 00:03:27 |
  | dev4 | 1 | 9addaab | b17d7b9739d6d46b… | 00:04:36 – 00:08:19 (2026-10-02) |
- **What changed between passes, by module (verified, by the modules' sha256 in each pass's code hash).**
  - dev1 → dev2: `plants/driver.py` only.
  - dev2 → dev3: `plants/driver.py`, `flaws.py`, `p24.py` and `p25.py` only.
  - dev3 → dev4: `plants/driver.py` only.
- **What the changes were (worker's statement).**
  - dev1 → dev2: the provenance import of `asdg.brainspan` and the cost table.
  - dev2 → dev3: re-checking the code against the launch before each write; a comma list; a multi-directory cost table;
    P24 / P25 summaries print a rate beside k / n (counts and rules unchanged); one docstring line in `flaws.py`.
  - dev3 → dev4: the cost-table fallback and `costs.json`.
  - Before dev1, single-case scratch runs led to one change: the MIST64 class label "subcortex" → "subcortex/brainstem"
    (an assertion crash; no outcome).
  - Changes that rest on orchestrator instructions, not outcomes: the plant keys through `seeds.py`'s plant interface
    and P12's 10,000 permutations. **Corrected in v2.1:** the key equality with the provisional values is checked in
    `tests/test_wp1_fixes.py:156-158`, not inside `plants/`.
- **No outcome-driven change (worker's statement).** After dev1's outcomes no plant construction, choice, counting or
  rejection rule, threshold, n, K or flag changed. No change was motivated by a DEV count: P26's planted catch (≈ .05),
  P25 (a) and P3b's survivors were seen, and nothing changed.
- **dev4 against 4ad80ec.**
  - **Verified:** every `plants/` module and `multiverse.py` at 4ad80ec has the sha256 dev4 recorded (39 of dev4's 41
    module hashes are equal).
  - **Verified, and not in the worker's statement:** the other two, `run.py` and `seeds.py`, differ. 4ad80ec carries
    the versions committed in dbfbdc2 (WP1 review fixes + WP2 special forms, 2026-10-02T00:49:05) after dev4.
    - What those two changes touch is not established by diff (dev4 recorded hashes only, not the files).
    - The official battery's code hash will differ from dev4's.
    - **Orchestrator's statement (2026-10-02), corrected in v2.1: it was partly false (re-check of v2, B1).** It said
      the key formulas are asserted inside `plants/`, and that no plant K lives in `run.py` or `seeds.py` other than
      `PLANT_K_OVERRIDES`. Both are false:
      - the key equality is checked in `tests/test_wp1_fixes.py:156-158`; `plants/common.py:113-123` only asserts that
        the class ids are distinct;
      - every plant K lives in `run.py:165` (`PLANT_K`), the class ids in `seeds.PLANT_CLASS_IDS` and
        `run.SYN_CLASSES`, and the plant ids in `seeds.plant_int`. Only P12's K is asserted inside the pinned blobs.

      These constants are now pinned by value (§8.1b). The rest of the statement is kept as the orchestrator's, as
      follows. The later `run.py` / `seeds.py` edits are the WP1 review fixes
      (B1-B5, C1-C9), the plants hand-off from `run.main` (§7 :1089) and the `test_run_p2` updates, made by a worker
      that did not see the plant DEV outputs, for reasons recorded in the review and in dbfbdc2's message; none was
      motivated by a plant DEV count. The plant-key formulas are asserted equal to the provisional ones inside
      `plants/` and checked by `tests/test_wp1_fixes.py` (B3). No plant construction, counting / rejection rule,
      threshold, n, K or flag lives in `run.py` or `seeds.py` other than `PLANT_K_OVERRIDES` (P12's 10,000, set from
      the orchestrator's instruction before `p12.py` existed). `costs.json` orders tasks only (each case draws only from
      its own keys), so it cannot move a plant result.
  - `costs.json`'s sha256 at 4ad80ec is 7b1a7288… as stated. The DEV outputs do not record it, so its equality with
    dev4's is the worker's statement.
- **The constants did not change across DEV (verified in v2.1).**
  - Every dev1–dev4 plant header records K = site 500, species 200, permutation 500, sets 200, surr 500, j1_sets 100,
    with P12's permutation 10,000 in every pass, dev1 included.
  - All 1,256 DEV case records' construction keys and 4,614 leg keys recompute identically with `seeds.py` at 4ad80ec
    (`…\scratchpad\amend2\c1_keys.py`).
- **DEV keys are the official keys (declared, v2.1).** The plant ids, class ids and case numbering are the official
  ones, so the DEV records are the outcomes of the first official cases, and they have been seen. Examples: dev3's 20
  cases per cell for P24–P26; dev2's 6 per cell; dev4's case 0.
  - This holds subject only to changes in `run.py` between the DEV passes and the official battery.
  - The official battery recomputes those cases, and any difference from the DEV record is reported.
- **dev2's P24 / P25 decisions re-scored with the pinned rejection functions (verified, v2.1).** The functions are
  `plants/common.py` `species_rejects` / `below` at 4ad80ec, as `p24.py` / `p25.py` call them, extracted from the blob
  and run alone on dev2's stored p's, floors and flags (`…\scratchpad\amend2\c2_rescore.py`). Re-scored equals
  recorded in:
  - P24 species-leg rejections (decoded-list and set-vs-map, per kind): 216 of 216;
  - P25's correct species leg: 24 of 24;
  - P25 (a), the v2 species max: 12 of 12;
  - P25 (b), the minimum: 12 of 12;
  - P25 (c), unconditioned G1 and G3m: 12 of 12 each.
- **Consequence.**
  - The DEV outcomes are declared as seen, as the first official cases' outcomes.
  - The official battery runs the §8.1 blobs and the §8.1b values unchanged.
  - Any later change to either after an official result is seen falls under §17.

## Affected code (the orchestrator assigns)
| reading | module | change |
|---|---|---|
| R37 | `repro.py` (or the reading writer) | the labeller as (B) |
| R38 | `fetch_extract.py` (the G2 fetch in WP4), `ahba_builds.py` (`perdonor-hcpmmp1`) | WP4; whole-volume atlas_info; parcels without samples counted |
| R39 | `multiverse.py` | per-cell parcel universe (bilateral L + R + B) and counts |
| R40 | `ahba_builds.py`, `repro.py` | Benkarim's and Park's DS; missing genes counted |
| R41 | `forms.py` | lift SW_GENE_LEGS_UNPINNED as (i) + (b); "not answered (T_S not reproduced)"; Σ w = 0 |
| R42 | `forms.py` (Liu), the BrainSpan / SD7 loaders (WP3) | duplicates; log2 coexpression; SD7 normalisation, alias table, fail-closed rules; label sets |
| R43 | `reparcel.py` | RP2 → > 50 %; P18 cases |

## Not changed
- every registered definition, floor, seed key and status order;
- `src/asdg`, `src_register/`, the register maps and sets, and amendment 1;
- R8 and R11's cell list;
- the frozen gate files;
- G1's and G2's checks;
- every plant's frozen §7 threshold.

## Answers to the review of v1 (asdg-skeptic: not-verified, 0 A / 4 B / 7 C)
| finding | answer | where |
|---|---|---|
| B1 R41's registered outcome | adopted: TSV 115–117 and prereg `:296-297` cited; the outcome is answered for T_S only if T_S passes its §4.1 check (MDD .531 / .547 / .529; ASD as TSV 103 / 105 / 107), else "not answered (T_S not reproduced)"; register item 2 (R2's eda33ab ρ's) added to the exposure line | R41, §0 |
| B2 R42 SD7 labels | adopted: markers in any token or glued (Lhippo), the alias table, the suffix strip, the `ctx` token; unmatched → fail closed with a count; R10's binary rule kept ("mixed → not auditable" dropped); T4 with zero matched labels fails closed; P16 formats. **One addition, adopted by the orchestrator (2026-10-02):** the lateral ventricles are dropped and counted (prereg `:298`'s ENIGMA rule), so that ENIGMA-style SD7 rows do not fail closed on a label that has no DK counterpart by construction | R42 (d), (e) |
| B3 RP2 literal | adopted: > 50 %, else dropped; bears on Mamat (Schaefer-400, in m) and Pretzsch (Glasser); `reparcel.py` changes. The quoted text is at `claims_register.md:1039-1040` (the finding cited `:1043-1044`, which is the DK-308 rule) | R43 |
| B4 plants pinned; DEV declaration | adopted: §8.1 (20 `plants/` blobs + `multiverse.py` at 4ad80ec); §8.2 written from the worker's statement, each item marked verified or worker's statement. **Found while verifying:** `run.py` and `seeds.py` at 4ad80ec differ from dev4's | §8.1, §8.2 |
| C1 R37's reach | adopted: GIA-C17 (in m) and PAT-N1, N2, N3, N5 (PAT-N4 −.067 lies outside .05); R27's wording noted, the register governs | R37 |
| C2 HCP-MMP1 parcels without samples | adopted (`samples_.py:21`); counted; descriptive only | R38 |
| C3 WP2 → WP4 | stated | R38 |
| C4 parcel-set change; bilateral 14-parcel class | adopted | R39 |
| C5 U6's reason | fixed (P12 runs the frozen 10,000) | §8 |
| C6 Park | missing genes excluded and counted; both branches planted | R40 |
| C7 refs | HEAD 05646de; `plants/` and `multiverse.py` at 4ad80ec | header, §8.1 |

## Answers to the re-check of v2 (asdg-skeptic: not-verified, 0 A / 1 B / 5 C)
| finding | answer | where |
|---|---|---|
| B1 §8.2's statement partly false | corrected and said so: the key equality is checked in `tests/test_wp1_fixes.py:156-158`; the plant constants live in `run.py` / `seeds.py`; `plant_mode.py` (636fc486…) added to §8.1; the constants pinned by value (§8.1b), asserted by the official driver and written into every plant header (after the freeze); verified unchanged across DEV | §8.1, §8.1b, §8.2 |
| C1 DEV keys = official keys | declared; verified on 1,256 records and 4,614 leg keys; DEV records are the first official cases' outcomes, seen, subject only to `run.py` changes | §8.2 |
| C2 re-score dev2 P24 / P25 | done: re-scored = recorded in 216 / 216 (P24) and 24 / 24, 12 / 12, 12 / 12, 12 / 12, 12 / 12 (P25) | §8.2 |
| C3 R42 (d) | `latvent` is glued-marker eligible; the marker's side selects the L / R id; two SD7 labels on one DK label fail closed; empty and global labels (`L_thickavg`, `ICV`; also `thickness`, `surfarea`) are dropped and counted as global measures | R42 (d) |
| C4 Left-Lateral-Ventricle | declared: it fails closed (accepted) | R42 (d) |
| C5 R38's citation | R14's "over that donor's parcels with samples" (`:741-742`) | R38 |
