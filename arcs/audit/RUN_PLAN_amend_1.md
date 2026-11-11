# RUN PLAN AMENDMENT 1 — A1 `audit`: readings WP1 found missing, and one correction of the G1 check

> **Status: v2.1, FROZEN by the orchestrator (2026-10-01; `FROZEN.txt`).** v1 was written on 2026-10-01 at HEAD
> 898bb00. The asdg-skeptic review of v1 returned "not-verified" (0 A / 6 B / 9 C). It confirmed that no registered
> definition changes, that the amendment is pre-exposure, that the frozen gate files moved 0 counts, that R33 is
> consistent with R8, and that the G1 match only adds refusals. v2 answers every finding; the closing table lists them.
>
> **v2 → v2.1.** The re-check of v2 returned "verified-with-residues" (0 A / 0 B / 6 C). v2.1 applies its six C fixes:
> the rank-rule branch is decided per null state, in Python integers (R32 (b)); R36 (b)'s bound covers any leg, and
> R36 (b) is adopted; DEAR-C1…C3 are listed (§0); and the reader chain is closed to the L7 pin (R35). Before freezing, the orchestrator computed the default-reader
> hashes (hash only) and wrote them into R35 as pins in place of "recorded at the first launch".
>
> The A1 code cited is at e7029ed (`a1_audit` is unchanged at HEAD ad7a346, the HEAD at writing). This amends
> `RUN_PLAN.md` v3.1 (FROZEN, sha256 16c6023296fab612…).
> - **Readings R32–R36** are in the plan's §5 format: **Text** → **Reading** → **Why now** → **Plant**. Authority: RUN_PLAN
>   §18.
> - **Correction 1** corrects §2.2's G1 check so that it implements the register's rule. Authority: the register (Corr. 1).
>
> No registered definition changes (`claims_register.md:1102-1103`), and no frozen file is edited.

## 0. Authority, exposure, what was read
- **Authority.**
  - RUN_PLAN §18: "Readings found missing later go to a frozen amendment of this plan (`RUN_PLAN_amend_<n>.md`).
    **Before any claim result exists**, such an amendment is pre-exposure for the material it bears on, provided that
    material is not yet opened" (`RUN_PLAN.md:1806-1808`).
  - For Correction 1, the register's G1 rule (`claims_register.md:101-102`), which the plan's check must implement.
- **Pre-exposure.**
  - No claim result exists. At ad7a346 there is no `arcs/audit/results/a1_run/`, `register_maps/post_freeze/` or
    `register_sets/post_freeze/` (existence checks only).
  - The orchestrator states that this audit has opened no gated material.
  - No reading or correction uses a map value. They act on:
    - the counting arithmetic of nulls;
    - set-size geometry;
    - the construction of the draws and their seed keys;
    - matrix parsing;
    - verdict bookkeeping;
    - string matching.
- **Exposure declaration (adds to RUN_PLAN §9, F2, `:1385-1404`).** Every reading here was written after the
  exploration lane's 14:25–14:30 exposure (RUN_PLAN §9) and uses none of its values.
  - **Readings that touch ENIGMA-derived cells**, to be added to the F2 list (`:1390-1401`):
    - R32: Giacomel's 18 V-DK-subcortex rows, including the rank rule for their ρ descriptors;
    - R33: only where a G2 set built under the gate falls in the partial-window range;
    - R35 and R36: these apply to every claim, as R2–R7 do. R36 (a) and (d) bear on Giacomel's two-sided
      published-null cells, Liu T3 and Patel's panels; R36 (b) bears on Mamat's two-cohort claims (G1).

    R34 touches no G2 cell. G2's component rows are:
    - PAT-C4, which is not auditable;
    - HAN-C1 and HAN-C1-ourPC1, fixed components with a parametric Level 0;
    - DEAR-C1…C3 (TSV rows 520–522; G1 + G2), fixed components, deferred pending provenance.

    Correction 1 bears on G1 only.
  - **Pre-freeze exposures that bear on R32's cells** (`claims_register.md:120-135`):
    - item 1: Giacomel's shipped result tables and supplement Tables S1–S3, ASD and MDD rows. These carry the published
      subcortical ρ's.
    - item 2: the Liu note's ENIGMA-ASD subcortex ρ, and A1's R2 on Giacomel's cortical cells;
    - item 3: the ENIGMA-ASD L_amygdala row.

    The same workbook was opened before the freeze by `arcs/audit/src/e4_r2_giacomel.py:8, :189`, which read the
    Thickness sheet only. **None of these values is used** by any reading here.
- **Read by this author:**
  - this programme's `CLAUDE.md`;
  - RUN_PLAN §0–§2.2, §4, R1, R7, R8, §6, §7, §9 and §16–§18;
  - `prereg_amend_3.md:60-180`, `prereg_amend_5.md:150-165`;
  - `prereg.md:115-118, :168-190`;
  - `claims_register.md:99-103, :118-136, :185-188, :280-316, :1005-1104, :1440-1485, :1550-1565, :1636-1642`;
  - TSV fields, read by script: `row`, `cell_id`, `claim_form`, `T`, `direction`, `analysis_class`, `inference_level`,
    `status`, `notes` and `verdict_counted_in_m`;
  - the engine `src/asdg/{spatial,species,cascade,verdict}.py`;
  - `a1_audit/{adapters,a3_port,gates,descriptors,verdict,seeds}.py`, `launch.py:75-90, :480-500`, parts of
    `tests/test_p0.py` and grep hits in `run.py`;
  - in A3's code: `h_verdicts.py:1119-1150`, `h_common.py:76-87, :237-239` and `gates_h2.py:108-114`;
  - `explore/discovery/guard.py:40-80`;
  - `e4_r2_giacomel.py:1-12, :185-192`;
  - the `e3_*.py` plant scripts (code only);
  - WP1's scratch `identity_tie*.py`;
  - the package metadata of `env/venv` and `env/venv_ref`;
  - A3 `ARC.md`, through scripts that printed counts of marker lines only.
- **Not opened:**
  - any carrier, map, supplement, NeuroVault image or decoder output;
  - any AHBA matrix;
  - anything under `E:\data\asdg\`;
  - `register_work/` and `explore/discovery/results/`;
  - the ENIGMA manifest table;
  - the values of any `results/*.json`;
  - A3's results.
- **Evidence.** Every number below comes from synthetic toys. The scripts are in `…\scratchpad\amend1\` (session
  94ea0193); v1 used `a_*.py`, `b_partial.py` and `d_supersession_counts.py`, and v2 adds `v2_rank.py` and
  `v2_misc.py`. They ran on 2026-10-01 at 898bb00 (v1) and ad7a346 (v2), with numpy 2.4.6 and scipy 1.18.1.
  - Code blobs: `spatial.py` 93e3aca0, `species.py` 39459999, `cascade.py` d23441bd, `src/asdg/verdict.py` 41f6be39;
    `a1_audit/` `adapters.py` 79381f75, `a3_port.py` a9c2f3ab, `gates.py` b740f3eb, `descriptors.py` e1cc4cb3,
    `verdict.py` d2c46a2e, `launch.py` 104ebcbe.

**Launch assertion added (the L5 extension; its own row).**

| # | assertion | expected value | source |
|---|---|---|---|
| L5a | this amendment | its `FROZEN.txt` line, once frozen; committed with 0 CR (LF blob = file hash) | `FROZEN.txt` |

## R32. Exact enumerations count their identity pattern; rank statistics count their ties (WP1 gap a; B1)
- **Text:**
  - "All p-values are one-sided in the registered direction, (k + 1)/(n + 1)" (`prereg.md:117`).
  - "A randomisation with fewer distinct null states than draws is enumerated exactly … S2c likewise … A leg with N
    null states has the smallest attainable p 1/(N + 1) (2/(N + 1) for exact G6s, whose enumeration contains the
    identity pattern)" (`prereg_amend_3.md:92-95`).
  - "S1c, S2c (exact enumeration when patterns ≤ 10,000), … G6s (exact when 2^rank ≤ 10,000)"
    (`claims_register.md:1069-1070`).
  - "Spearman for ρ" (`:318`). The Giacomel descriptor rows' T is "the weighted GEDAR map's ρ with y …; our
    class-stratified site leg on ρ" (`:1469-1473`; TSV rows 104–114 even and 121–131 odd).
  - The engine: "The identity pattern is included, so with p = (k + 1)/(N + 1) the smallest attainable p is 2/(N + 1)"
    (`src/asdg/spatial.py:145-146`); "exact: identity pattern counts" (`species.py:221`; `verdict.py:6-8`). The count
    is `sign·null ≥ sign·obs` (`cascade.py:22-24`).
- **Facts** (synthetic):
  - **Where the engine enumerates.** There are two places.
    - `site_null` → `stratified_exact`: within-class permutations and MSR signs, combined by `meshgrid("ij")`. The
      identity is **row 0** (`spatial.py:153, :157, :162-163`).
    - Exact G6s: the identity is the **last row** (`species.py:129-130`).

    G6l has no identity: its windows exclude S (`species.py:139-141`).
  - **The identity tie (non-rank T)** (`a_identity_repro.py`). 40 single-class 7-parcel toys × 3 maps × 7 forms give
    2,040 exact-leg evaluations: S1c and S2c over 5,040 patterns, and G6s over 64.
    - In 1,141 of them the identity's T* ≠ T_obs, so it is missed in one direction. The gap is ≤ 1.7e-13 relative;
      the nearest other pattern is ≥ 4.1e-7 away (`a_tol.py`).
    - In 135 evaluations a one-sided p falls below the declared floor. Per 120 evaluations (missed / below floor):
      - set-vs-map: G6s 85 / 16, S1c and S2c 59 / 13 each;
      - decoded-list: G6s 106 / 31, S1c and S2c 80 / 16 each;
      - PLS-enrichment: G6s 104 / 30, site 59 / 0;
      - T_abs site: 37 / 0;
      - components: 49–75 / 0.
    - A3's `claim_verdict` port gives p_G6s = 1/65 against a floor of 2/65 in 10 of 40 own-score toys.
    - Ties: a tie in y (y[1] = y[0]) makes the swap a second, bit-identical identity row. Counting by index alone
      leaves it uncounted in 22 of 40 toys (`a_tie2.py`).
  - **Rank T** (`v2_rank.py`; ρ between a 7-value y and a fixed second map, over `site_null`'s 5,040 permutations).
    - In exact arithmetic the 5,040 patterns fall into 57 equal-ρ groups per toy: 2,280 over 40 toys.
    - A batch-normalised float ρ (`corr_matrix` of rank rows) splits 2,096 of them. It miscounts k in 40 of 40 toys,
      by up to 168 patterns short in one direction.
    - With a tie in y it miscounts in 38 of 40 toys, by up to 90.
    - `scipy.stats.spearmanr`, applied per surrogate, missed 0 of 40, but nothing guarantees that.
    - The integer form below counts every equal-ρ group exactly; the identity is counted in 40 of 40 toys.
    - No rank-statistic null exists in the code at e7029ed: Spearman appears only beside Level 0, with no null
      (`adapters.py:390-392`).
  - **Which legs can be exact on the registered classes** (`a_classes.py`; stand-ins with the registered class sizes).
    - None on dk-ctx (34), V-DK (34 + 8), V-AAL (38 + 7 + 9) or MIST64 (33 + 5 + 8).
    - V-DK subcortex (7 parcels) is exact: S1c = S2c = 5,040 patterns, and G6s = 64. These are the 18 Giacomel rows:
      - rows 92–102 even: in m, resolution-limited by construction (`:1462-1463`);
      - rows 104–114 even and 121–131 odd: ρ descriptors with their site legs, G1–G5 and J1.
    - In general:
      - S1c is exact only if every class has fewer than 10 parcels;
      - S2c is exact iff the engine's pattern product is ≤ 10,000;
      - G6s is exact iff n − n_classes ≤ 13.
- **Reading.**
  - **(a) Non-rank T: the identity counted.**
    - **Where it applies:**
      - every null that is an exact enumeration containing the identity: `site_null` with `exact` true (legs 0, 1, 21
        and 22; J1's surrogate types, leg 14; every descriptor site leg);
      - exact G6s (leg 4);
      - these again in the ≥ 2-donor and multiverse re-runs.
    - **The rule, applied after T is computed:**
      1. Locate the identity row by index (site: row 0; G6s: the last row).
      2. Assert that this row reconstructs the observed input (`site_input()`, or S's set score on the leg's basis) to
         1e-9 × max(1, max |input|). A failure stops the run.
      3. Set the null statistic of that row, and of every row whose null input is bit-identical to it, to the
         observed statistic (T_obs, `species_obs` or J1's z_obs).
      4. Form (k + 1)/(N + 1) as frozen.
  - **(b) Rank T: ties counted exactly, on every leg.**
    - **What counts as a rank statistic:** a statistic that is a function of ranks only, such as Spearman ρ (the 12
      Giacomel descriptor rows; the ρ of the §4.1 checks is a value with no null) or the rank-biserial r of R10.
    - **How its null is compared:** exactly, never through a float.
      - All arithmetic is in Python integers, never int64: T4 / T5's common denominators can overflow int64.
      - Ranks are average ranks doubled, so every rank is an integer, and centred by n + 1.
      - The numerator N = Σ (2R_a − (n + 1))(2R_b − (n + 1)) is formed; a rank-sum uses the analogous doubled sum.
      - **The branch is decided by computing.** The runner computes the denominator D of the observed state and of
        every null state. If all are equal, the numerators are compared. Otherwise the values are compared as exact
        rationals (`fractions.Fraction`; for a correlation, sign(N)·N²·D′ cross-products).
      - The type of null never decides the branch. For example, S1c's permutation null has a constant denominator,
        but S2c's does not when y has ties. Exact-rational comparison is always valid and may be used throughout.
      - The float statistic is for reporting only.
    - **Where it applies:** every leg that compares the rank statistic itself, exact or sampled: site legs and
      gene-set legs. Equal-valued states are then bit-equal, and the identity is counted without (a). J1's z is not a
      rank statistic; its exact surrogate types keep (a).
    - **Not changed by (b):** non-rank T, and Spearman beside Level 0.
  - **(c) Assertion.** On every exact leg, the verdict driver asserts p(d) ≥ the declared floor in both directions. A
    failure is a functional defect and stops the run.
  - **What does not change:**
    - the non-identity patterns of a non-rank T;
    - every sampled leg of a non-rank T;
    - every floor.
  - **Residuals (declared):**
    - A pattern equal to the identity's only mathematically, not bitwise, is not caught by (a). An example is an MSR
      flip on a coefficient that is zero only up to rounding.
    - A **sampled** leg of a non-rank T can draw the identity and miss it in the same way (`v2_misc.py`, 40 toys,
      K = 10,000):
      - one 8-parcel class (8! > 10,000; S1c and S2c both sampled): drawn 21 times, uncounted 6 times;
      - one 15-parcel class, S2c (2^14 sampled): drawn 25 times, uncounted 20 times;
      - the same class, G6s: drawn 21 times, uncounted 19 times.

      At the registered sizes no sampled leg is affected:
      - V-DK subcortex (7 parcels) is exact;
      - every other registered class has a cortex class of ≥ 33 parcels, so a whole-map identity has probability
        ≤ 2^-32 per draw (S2c, G6s), and never occurs for S1c.
- **Why the frozen text already requires this.** k counts every null state ≥ T_obs, and the floor 2/(N + 1) presumes
  the identity among them. (a) and (b) pin how that is done in floating point.
- **Option (ii), a tie tolerance, is not adopted.**
  - For non-rank T it needs a constant chosen now and still rests on rounding.
  - For rank T the ties are exact by construction under (b).
- **Option (iii), a tolerance on every leg, is not adopted:** it changes "≥" on every sampled non-rank leg.
- **Effect on the toys (non-rank T).** (a) moves exactly (identity rows)/(N + 1) where the identity had been missed, in
  2,040 of 2,040 evaluations, and leaves 0 p's below their floor.
  - One-sided p's of sampled legs are bit-identical: 160 / 160 site legs at K = 2,000 and 80 / 80 G6s at K = 50 on the
    7-parcel toys, and 15 / 15 legs on 34-parcel toys.
  - **Reported (doubled) p's are not always unchanged.** On a two-sided row, one fixed count on an exact leg can flip
    d*, and with it the direction reported for every leg, sampled legs included (C1).
- **What this changes, and what it does not.**
  - **No verdict count in m moves.** The six in-m V-DK-subcortex cells are resolution-limited by construction, and the
    twelve other rows are descriptors.
  - **A1's frozen gate files are not regenerated**, because a regeneration re-arms K1 (`RUN_PLAN.md:163-164`;
    `prereg_amend_5.md:274-275`). The defect moved 0 counts in them:
    - their site surrogates came from `stratified_surrogates`, never from `site_null` (`e3_align_plants.py:141-142`,
      `e3_plants.py:118-119`, `e3_c3_gradients.py:60-61`, `e3_p1_strat.py:80-81`);
    - their species legs ran at K = 200 on classes of ≥ 34 parcels (`e3_align_plants.py:50, :161`;
      `e3_species_replay.py:34, :76`).
  - **A3 (closed), settled from code; no A3 file is edited.** A3 used the same engine paths (`h_verdicts.py`
    `claim_verdict` → `site_null` and exact G6s; `b0`'s site leg at `:1139-1141`). Its classes are:
    - `h_common.py:79-87, :237-239`: V-DK 34 + 8; V-AAL 38 + 7 + 9; cortex-only classes of ≥ 34;
    - `gates_h2.py:111-112`: V-DK 34 + 7.

    Each has a cortex class of ≥ 34 parcels, so none admits an exact leg unless a claim's analysis parcels shrank to a
    single class of ≤ 7 (site leg) or to n − n_classes ≤ 13 (G6s). Whether any A3 cell did is a question for A3's
    results, which were not opened.
- **Why now:** no claim result exists, and this audit has not opened Giacomel's subcortical map (G2). The readings fix
  counting arithmetic and use no value.
- **Plant: P9 extension (functional).** It runs on P9's V-DK-subcortex plant and on 40 synthetic single-class 7-parcel
  toys × 3 maps, through the production path, for every exact leg of every form:
  - set-vs-map, decoded-list and PLS-enrichment: S1c, S2c and G6s;
  - T_abs: S1c and S2c;
  - component site legs;
  - J1's exact types;
  - a **ρ form**: the ρ descriptor's site leg, over the same 5,040 permutations, with and without a tie in y.

  It checks, in both directions:
  - every one-sided p is ≥ its declared floor;
  - the change from the unamended count is exactly (identity rows)/(N + 1), and 0 elsewhere;
  - ρ counts equal an independent integer recomputation;
  - **d* and every reported p** are compared with the unamended code. A difference is allowed only where the fixed
    count flips d*, and it is listed (C1);
  - one-sided p's of sampled legs are bit-identical.

  **Must-fail variants:**
  - a wrong identity index (refused 10 / 10 and 10 / 10 in scratch);
  - the unamended count (p < floor on 5 of 10 toys);
  - a batch-normalised float ρ (miscounts on 40 of 40).

  P9's existing checks stand.

## R33. G6l when a window fits only part of the offset range (WP1 gap b)
- **Text:**
  - "window W(o) = {g} ∪ the m − 1 consecutive genes at offset o, o ∈ [0, half the ranking]; O_g = {o : |c(W(o)) − c_S|
    ≤ .02}; g eligible iff O_g ≠ ∅" (`prereg_amend_3.md:124-126`).
  - "Fewer than 50 eligible seeds → 'unmatched'" (`:131-132`).
  - H0_G6l: "windows of its size" (`:82-83`).
  - R8: "When no window of size m fits the ranking, no seed is eligible … 'unmatched'" (`RUN_PLAN.md:573-575`).
- **Facts** (`b_partial.py`):
  - The engine uses n_rank = G − m − 1 and half = n_rank // 2 (`species.py:141-145, :156-157`).
  - At G = 15,633 every offset fits for m ≤ 5,211. Offsets fit only partly for m = 5,212–7,816, and none fit for
    m ≥ 7,817.
  - In the partial range the engine's screen raises a ValueError (the cumsum buffer is longer than the ranking), and
    `adapters.g6l_screen_safe` raises NotImplementedError.
  - No built registered set falls in this range. The only no-window rows are 332, 333, 367 and 368, at m = 14,607.
  - Sets built under a gate have no m yet.
- **Reading.**
  - An offset whose window does not exist is not an offset, so O_g = {o ∈ [0, min(half, n_rank − m + 1)] :
    |c(W(o)) − c_S| ≤ .02}.
  - Every frozen rule then applies unchanged:
    - o is uniform over O_g;
    - fewer than 50 eligible seeds → "unmatched";
    - a mean pairwise Jaccard ≥ .5 → "degenerate";
    - the exact / sampled rule.
  - R8 is the special case in which O_g = ∅ for every g.
  - Where the full range fits, the screen stays the frozen `a3_port.g6l_screen`.
  - Not adopted:
    - truncated windows (smaller than m);
    - wrap-around (no text supports it);
    - "unmatched" for the whole range, which would be the kind of relabelling R8 withdrew.
- **Why now:** before any gated set is built. The reading uses no set's composition.
- **Plant: P10 extension (functional).**
  - At toy G = 150 the full range fits for m ≤ 50. For m ∈ {5, 12, 30, 50} on 12 toys × 2 streams (96 streams), the
    screen's sets, info **and window curves** are bit-identical to the frozen screen's (scratch: sets and info
    96 / 96).
  - Partial m = 51 / 60 / 75 give no exception. Every window has m distinct genes outside S and an offset
    ≤ n_rank − m + 1.
  - m = 80 gives "unmatched".
  - **Must-fail variants:**
    - truncated windows, caught by the m-genes check;
    - **float64 window sums**, caught by the curve check. In scratch the curves differ in 48 of 48 screens, while the
      in-band offset sets differ in 0 of 48 (`v2_misc.py`), so sets alone would not catch this variant.

## R34. Component Level-0 permutations and the selected-list keys (WP1 gap c; B2)
- **Text:**
  - "Level 0 = 10,000 parcel-label permutations of y with refit" (`prereg.md:179-180`; `claims_register.md:292-293`).
  - Seed legs: "8 permutation / label, 10 re-selection" (`:1081`); "component Level 0 10,000 permutations; re-selection
    loops at the same count" (`:1071`).
  - RA-11…14 (TSV rows 208–211): "re-selection by the paper's rule on every permutation and surrogate"
    (`:1561-1563`), with "Level 0 = 10,000 parcel-label permutations with re-selection; class-stratified site leg with
    re-selection" (TSV `T`).
  - "The test is unchanged: Levels 0–1 with refit, and list re-selection where amendment 3 §2 requires it"
    (`prereg_amend_5.md:155`).
  - RUN_PLAN §4 legs table: "S1c [0], S2c [1] … all forms incl. component" (`:369`), and "component Level 0
    permutation [8]; re-selection [10] | 10,000 | component / selected lists" (`:371`).
  - R7: "A leg that needs a Generator takes `np.random.default_rng(SS)`" (`:544`).
  - None of these says how the permutations are drawn, or which key a selected list's two loops use.
- **Reading.**
  - **Construction.** A permutation null is T refit on the rows of
    `default_rng(SS).permuted(np.tile(y, (10_000, 1)), axis=1)`. This is A3's B0 construction (`h_verdicts.py:1134-1135`)
    and is implemented at `adapters.py:690-699`.
    - The draws are independent uniform permutations of **all** analysis parcels, in the class's parcel order: not
      within class, the identity not excluded, with replacement over the n! permutations.
    - p = (k + 1)/10,001 per direction (R1).
    - A fixed component keeps the parametric Level 0.
    - In numpy 2.4.6 this is bit-identical to a row-wise `rng.permutation(y)` loop (`v2_misc.py`: K = 5 and 1,000; n = 7
      and 34). The numpy version is recorded per row.
  - **Keys (B2).** The §4 legs table is read row by row. Leg 8 is the Level-0 permutation key of the other component
    claims; leg 10 is the Level-0 permutation key of selected lists (which are component-level too); legs 0 and 1 are
    the site leg of every form.
    - **Non-selected components:** Level 0 from SS(leg 8); site leg from SS(leg 0) and SS(leg 1), as every form.
    - **Selected lists (RA-11…14):**
      - Level 0 = the construction above from SS(leg 10). The paper's rule re-selects the list on each permuted map,
        and an empty list gives T = 0.
      - Site leg = `site_null` with S1c's integer seed from SS(leg 0) and S2c's from SS(leg 1) (R7), with the list
        re-selected on each surrogate.
      - SS(leg 8) is not drawn for these rows.
      - Each leg has its own generator, so no order between legs arises.
      - Re-selection draws no random number. The paper's rule, with the ML_Lag weights of its code (`:1561-1563`), is
        given no generator, and this is asserted.
  - **Unreachable-case assertion (C3), not a rule.** A component map with n! ≤ 10,000 (n ≤ 7) would fall under amendment
    3 §2's "enumerated exactly" (`prereg_amend_3.md:92`). The smallest component class is 34 parcels (dk-ctx; V-AAL 54,
    MIST64 46), so the runner asserts n! > 10,000 and stops if that fails. Reaching it would need a frozen amendment.
- **Why now:** no component result exists, and the construction and keys must not be chosen after p's are seen.
- **Plant: P12 extension (functional).**
  - The leg-8 null equals an independent re-implementation bit for bit.
  - Every row is a permutation of y.
  - A known-answer sha256 of `default_rng(SeedSequence([20260925, 990, 0, 8])).permuted(np.tile(np.arange(34),
    (1000, 1)), axis=1)` as int64 bytes = a36f360469243fefb9a36e2e67da0b5adc3f888d85195d597a3c9179bd85bec5.
  - Equality with the row-wise loop at K = 5 and 1,000.
  - The n ≤ 7 assertion fires on a 7-parcel map.
  - **Must-fail variant:** a within-class permutation, caught on a multi-class toy (no row moves a value across
    classes).
- **Plant: P13 extension (functional).** On a synthetic selected-list claim:
  - the Level-0 rows equal SS(leg 10)'s construction and differ from SS(leg 8)'s;
  - the site surrogates equal `site_null` from SS(leg 0) and SS(leg 1)'s integer seeds;
  - a seed spy shows leg 8 never requested;
  - each generator's state after its draws equals its state after the draws alone (re-selection drew nothing).

## R35. The two AHBA matrix readers (B5)
- **Text:**
  - L6: "AHBA matrix files"; L7: "AHBA matrix identity (`hash_pandas_object`, checked in `env/venv_ref`, once per
    launch)" (`RUN_PLAN.md:146-147`).
  - Neither names the parser, nor the reader the statistics use.
- **Facts:**
  - The pins are reproduced by `read_csv(index_col=0, float_precision='round_trip')`. pandas' default float parser does
    not reproduce them (`launch.py:82-84`; the L7 script at `:486-497` runs in `env/venv_ref`, pandas 1.5.3).
  - The statistics read the matrices with A1's reader (`e3_plants.primary_parcels`: `read_csv(index_col=0)`, the
    default parser), in `env/venv` (pandas 3.0.6). `a3_port.verify_matrix` checks that reader against a round-trip read:
    same gene order, max |Δ| < 1e-12 (`a3_port.py:105-128`).
- **Reading.** For dk, aal and mist64:
  - **identity:** L7 in `env/venv_ref` with the round-trip reader; the sha256 of `hash_pandas_object(df, index=True)`
    bytes must equal the pins;
  - **the chain to the pin, in `env/venv`, at launch:**
    - the round-trip read's `hash_pandas_object` sha256 is asserted equal to the L7 pin;
    - the default reader's sha256 is computed in both environments and asserted equal across them and to its pin.
      The orchestrator computed both readers' hashes before freezing (2026-10-01, the main tree's `artifacts/ahba/`,
      hash only; pandas 3.0.6 in `env/venv` and 1.5.3 in `env/venv_ref` gave identical values; the round-trip values
      equal the L7 pins). Default-reader pins (sha256 of `hash_pandas_object(df, index=True)` bytes):
      dk 6707881c6b5d9e12858f654cdfb6ec9b416d352f74f36fe59c11d2088c6daebe,
      aal ef455efb83f38a234f34dbd0e66153a8c48f6f1ac6f12bbab9d8bd1e0d3e9eac,
      mist64 13aa6f7df6020d6f19a37f3130b332f80f4511d9f542d2f1760f4de2a7a97997;
  - **values:** A1's default-parser reader in `env/venv`. Before a matrix's first use in a process, the same file is
    read in the same environment with `float_precision='round_trip'`, and the runner asserts identical index and gene
    order and max |Δ| < 1e-12 over the rows used. A failure stops the run;
  - **provenance:** each environment's pandas, numpy and Python versions are recorded per output (§2.4).
- **Why now:** every statistic reads these matrices, so the readers are pinned before any claim runs.
- **Plant: P1 extension.**
  - L7 recomputed in `env/venv_ref` equals the pins.
  - The round-trip read's hash in `env/venv` equals the pin. On a synthetic frame, both readers' hashes are equal
    across pandas 3.0.6 and 1.5.3.
  - The 1e-12 check passes on a synthetic `.csv.gz` read both ways, and fails on a copy with one value moved by 1e-9.
  - Both environments' versions appear in the provenance block.

## R36. Four verdict readings WP1 part 2 needed (B6)
These are pinned as faithful readings. Each cites the frozen text that leaves it open. The code is
`a1_audit/verdict.py:35-43` and `descriptors.py:38-44, :66-67`.
- **(a) d* when the conjunction has no p in either direction.**
  - **Text:** d* = argmin_d max(p_L0(d), p_site(d), p_species(d)) (R1, `RUN_PLAN.md:432`). This is undefined when a
    composite leg has no p in either direction: G6l unmatched or degenerate, or R8. "Every level's p is in the table for
    every claim, including after an earlier failure" (`prereg.md:173-174`).
  - **Reading:**
    - d* is not defined, and no doubled p is reported;
    - both one-sided p's of every computed leg, and the literal per-leg two-sided p, are reported;
    - the status, which in these cases is never ok (G6l unmatched or degenerate, or R8's label), stands.
  - **Why faithful:** a d* chosen from a subset of the legs would be a new definition, while every p the prereg asks
    for is still reported. This is as coded.
- **(b) A two-cohort tie with opposite observed signs.**
  - **Text:** "A tie goes to the sign of the observed T" (R1 `:432-433`). A two-cohort claim has one d*, and "both maps
    must survive in d*" (`:442-445`; `claims_register.md:1639-1641`). With two opposite signs the tie-break cannot be
    applied.
  - **Fact:** a tie cannot occur at a surviving value.
    - For any empirical leg, p(+) + p(−) = (k₊ + k₋ + 2)/(n + 1) > 1, since k₊ + k₋ ≥ n. For a parametric leg the
      sum is 1.
    - Under a tie the common maximum M is ≥ both one-sided p's of every leg, so 2M ≥ 1 and M ≥ .5. Neither direction
      survives.
    - No parametric Level 0 is needed for this. (All 25 two-cohort rows, TSV 440–464, are decoded-list.)
  - **Reading:** the claim **does not survive**:
    - its conjunction p is min(1, 2M) = 1 (`prereg.md:184-185`'s 2·min, which is defined);
    - its status is the maps' direction-free statuses (status order, floors and flags);
    - d* is recorded "undefined: two-cohort tie, opposite observed T signs", and reporting follows (a).
  - **Why faithful:** the verdict and the conjunction p are the same in both directions. The register's "not auditable
    (definition not applicable)" (`:1102-1103`) applies only when a definition cannot be applied, and here the verdict
    can be applied.
  - **Adopted by the orchestrator under the standing delegation (2026-10-01).** It replaces the code's reading at
    e7029ed: "not auditable (definition not applicable: two-cohort tie …)" (`verdict.py:39-40, :58-59, :368-371,
    :458-459`). That reading would have moved such a claim out of the tested population; it bears on the 19 in-m Mamat
    rows.
- **(c) A component claim whose floors are not below α.**
  - **Text:** "a claim whose largest leg floor is not below .025 is 'resolution-limited' (cannot survive …)"
    (`prereg_amend_3.md:95-96`); the component reading is "passes / does not pass at component level"
    (`prereg_amend_5.md:156`).
  - **Reading:** the label applies to component claims, with the effective (doubled, two-sided) floors of Level 0 and
    the site leg (R1 `:446`). Such a claim reads "resolution-limited; does not pass". This is as coded
    (`verdict.py:404-410`).
  - It is unreachable at the registered sizes, where the floors are ≤ 2/10,001.
- **(d) R1 on descriptor legs.**
  - **Text:** "every leg and sub-leg gives its one-sided p_leg(d) … Each leg's reported p is min(1, 2·p_leg(d*))"
    (R1 `:429-436`). Descriptors are reported for every claim (`prereg_amend_3.md:100-101`), and a claim has one
    direction (`claims_register.md:187`).
  - **Reading:** each descriptor leg is reported at the claim's d* (two-sided, doubled) or at its registered direction
    (one-sided), with both one-sided p's and the literal per-leg two-sided p beside it. With d* undefined, (a)
    applies. This is as coded (`descriptors.py:127-137, :66-67`).
  - **Why faithful:** a separate direction for each descriptor would give one claim several directions.
- **Why now:** no claim result exists, and none of the four uses a map value.
- **Plant: P8 / P14 extensions (functional).**
  - (a) A G6l-unmatched case: no doubled p, every one-sided p reported.
  - (b) A constructed two-cohort tie with opposite T signs: "does not survive", p = 1, d* undefined.
  - (c) A component claim at plant K = 30 permutations and surrogates (floor 1/31 ≥ .025): "resolution-limited; does
    not pass".
  - (d) Descriptor reported p's at d* equal 2·p(d*).

## Correction 1. The G1 supersession match is case- and white-space-insensitive (WP1 gap d; B3, C6)
- **Authority.** This is a correction of the plan, not a missing reading.
  - RUN_PLAN `:212-216` and `:240` define the match exactly, and case-sensitively, and `gates.py:25-26` implements it
    so.
  - The register says "If (b-ii) is commissioned instead, G1 stays closed" (`claims_register.md:101-102`). A
    case-sensitive match fails open against that rule: a lower-case "record: (b-ii) commissioned" would leave G1 open.
  - The plan's check must implement the register: "The register opens G1 by one of three routes" (`RUN_PLAN.md:185`),
    and the plan "never changes a registered definition" (`:17-18`).
- **Facts** (`d_supersession_counts.py`, `v2_misc.py`).
  - Five variants leave G1 open under the frozen rule:
    - "record: (b-ii) commissioned";
    - "Record: Delegation Revoked";
    - "\*\*RECORD:\*\* (B-II) COMMISSIONED by the operator";
    - "RECORD:(b-ii) commissioned";
    - "RECORD : delegation revoked".
  - Under the frozen rule, under case folding, and under case folding with white space deleted, 0 lines of A3 `ARC.md`
    match. This holds at HEAD ad7a346 (re-counted for v2), in the working copy and at 4fd7942, and for the 29-line
    session-10 block in each.
- **Correction.**
  - After §2.2's normalisation, every white-space character (Python `re` `\s` on str, Unicode: tab, NBSP and em space
    included) is deleted. Both the line and the marker are then case-folded (`str.casefold`) before the containment
    test.
  - The record block's own checks are unchanged: its marker lines are exact whole-line matches, its attestation lines
    keep their regexes, and the session-10 block stays byte-identical.
  - The correction only adds refusals.
  - **Authoring rule, widened:** A3 ARC entries never quote a supersession marker, in any case or spacing.
- **Residual (declared).** These variants are **not** matched (`v2_misc.py`):
  - a fullwidth colon (U+FF1A);
  - fullwidth letters;
  - a non-breaking hyphen (U+2011) or an en dash (U+2013) in "b-ii".

  NFKC and dash folding are not added. The markers are written by the orchestrator or the operator, under the
  authoring rule.
- **Recorded, not changed.** §2.1's G2 check reads the record from the working copy (`gates.py:23-24`). This needs no
  change:
  - G2 opens only on commit ancestry (the named commit and 4efbae5), which no working-copy edit can supply;
  - claim runs use a clean worktree (L11).
- **Plant: P21 extension.** P21's frozen list grows from 35 to **40** cases: 3 correct records and 37 refusals. The 5
  added refusals are the five variants above. The real record still opens at the run commit.

## Affected code (the orchestrator assigns)
| item | module | change |
|---|---|---|
| R32 (a) | `adapters.py` (`_Form.site_leg`, `_score_species`), `descriptors.py` (`j1_core` exact types; descriptor site legs) | locate, assert and count the identity rows after T |
| R32 (b) | the ρ descriptor (P15 / signed-weight adapter, not yet built) and R10's rank-biserial | integer rank arithmetic for every leg |
| R32 (c) | `verdict.py` | assert p ≥ floor on every exact leg |
| R33 | `adapters.py` (`pool_status`, `g6l_screen_safe`) | partial-range screen beside `a3_port.g6l_screen` (its copied block is never edited) |
| R34 | `adapters.py` (`_Component`), `run.py` (selected-list route, P13) | the n ≤ 7 assertion; leg-10 Level 0 for selected lists; no generator passed to re-selection |
| R35 | `launch.py`, the context builder | at launch, both readers' hashes in both environments (round-trip = L7 pin; default = the R35 pins); the 1e-12 check in `env/venv`; versions in provenance |
| R36 (b) | `verdict.py` (`TWO_COHORT_TIE` branch) | changes to: does not survive, conjunction p = 1, d* undefined |
| Corr. 1 | `gates.py` (`normalise_line`, `superseding_lines`), `tests/test_gates_p21.py` | the match; 40 cases |
| L5a | `launch.py` | this file's `FROZEN.txt` hash |

## Not changed
- every registered definition, floor, seed key and status order;
- `src/asdg`, `src_register/`, the register maps and sets, and `a3_port`'s copied blocks;
- the sampled legs of non-rank T;
- R8;
- G6l's offset range wherever the windows fit;
- the frozen gate files (not regenerated);
- A3's session-10 block and G1's positive markers;
- G2's check;
- the map and cell indices of the seed keys. These are pinned by `claims_register.md:1076-1082` and need no reading
  (C7); WP1's resolver is being built in `run.py`.

## Answers to the review of v1 (asdg-skeptic: not-verified, 0 A / 6 B / 9 C)
| finding | answer | where |
|---|---|---|
| B1 rank-statistic ties | adopted: integer rank arithmetic on every leg that compares a rank T (site and gene-set legs); identity rule kept for non-rank T; P9 ρ form with a batch-ρ must-fail; tolerance rationale dropped for rank T. Reproduced: 2,096 / 2,280 groups split, up to 168 short, 40 / 40 toys miscounted | R32 facts, (b), plant |
| B2 leg 10 unpinned | adopted: selected lists draw Level 0 from leg 10 and the site leg from legs 0 / 1 (the §4 table read row by row); leg 8 not drawn; re-selection draws nothing; P13 asserts the keys | R34 |
| B3 R35 is a change | adopted: relabelled Correction 1, authority `claims_register.md:101-102`; P21 35 → 40 (five cases named); authoring rule widened | Corr. 1 |
| B4 exposure record | adopted: F2 additions (R32, R33, R35, R36), register `:120-135` items 1–3, `e4_r2_giacomel.py:8, :189` (Thickness only); none used | §0 |
| B5 matrix readers | adopted: both readers, the 1e-12 assertion and versions pinned; v2.1 closes the chain to the L7 pin | R35 |
| B6 four readings | (a), (c), (d) pinned as coded. **(b) pinned as "does not survive" rather than the coded "not auditable"**: a tie forces M ≥ .5 for any leg, so the verdict is the same in both directions. (b) was adopted by the orchestrator (v2.1) | R36 |
| C1 d* flip | adopted: P9 compares d* and reported p's; "unchanged" restricted to one-sided p's | R32 |
| C2 sampled identity | declared, with v2's own counts; registered sizes unaffected | R32 residuals |
| C3 n ≤ 7 refusal | relabelled an unreachable-case assertion | R34 |
| C4 stream test | adopted: loop equality and a known-answer hash | R34, P12 |
| C5 m range; float64 | corrected to m ∈ {5, 12, 30, 50}; float64 must-fail added, caught by curves (sets 0 / 48 differ) | R33 |
| C6 Unicode | white space = Python `\s`; NFKC / dash / colon residual declared | Corr. 1 |
| C7 map / cell indices | no reading needed (`:1076-1082`) | Not changed |
| C8 refs; assertion; L5 row | HEAD / blobs updated; R32 (c); L5a row | §0, R32 |
| C9 A3 note | settled from A3's code; no A3 file edited | R32 |
