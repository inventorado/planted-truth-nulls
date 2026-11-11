# PREREG — probe `ASDG-AUD-E5-regime`: where does the coexpression-matched gene null stop being calibrated?

**v3 — the frozen version** (`bench.py freeze`; hash in `arcs/audit/probes/regime/FROZEN.txt`). v1 was reviewed by
asdg-skeptic on 2026-09-24: "fix then freeze", 1 A / 6 B / 3 C findings, all adopted. The v2 verification pass left
R6 (the P5 rule), R7 (A2w was not intermediate), R8 (the regressions) and four code/text items open; all are fixed in
v3. The v3 verification returned **verified**, with three one-line code/text items fixed before freezing (§7). This
is a probe of arc A1 (`arcs/audit`): the paper-1 regime-boundary control, an operator
decision of 2026-09-24 (`literature/PRIOR_ART.md`, "Targeted novelty checks", item 1). It changes nothing in A1's
verdict.

## 0. Status and exposure (declared)
Written 2026-09-24. The two endpoints are already known and were seen.

**Cao's regime: calibrated.** `results/e4_r1_cao.json` (E4 R1) reproduced Cao 2024's calibrated cell:
- random 20–200-gene sets, 1,000 near-noise maps (Moran's I ≈ .03);
- left-cortex Desikan, 34 regions × 6,513 differentially stable genes;
- aggregation-dependent statistics.

Cao's matched sampler gives Psig .044 (Mean) / .049 (Meanabs). Our G2 sampler, run as a descriptor at Cao's tolerance
±.01, gives .036 / .051.

**Our regime: anticonservative.** `results/e3_gates.json` (E3) tested:
- tight modules: a seed plus its 24 most coexpressed genes;
- smooth fields over whole-brain parcellations: 42–107 parcels, 15,633 genes, tissue-class steps;
- T = Pearson r of the set's mean-expression score.

At α .05, G2 (±.02) gave false alarms of .196–.210, G4 of .399–.442, and G1 of .085–.116.

**Nothing between the endpoints has been computed** — no tight module in Cao's space, no smooth map there, and no
Mean / Meanabs on E3's plants — except these read-only computations:
- **Reviewer's pass** (asdg-skeptic, 2026-09-24):
  - correlations between Mean and T across Cao's maps 1–200: tight 25-modules .9994, random 25-sets .971;
  - the same on its own synthetic V-DK fields: .998 and .978;
  - coherence of tight modules: median .866;
  - Psig on R1's per-test output for this probe's subset;
  - the spread of that Psig over 400 random subsets.
- **Orchestrator:**
  - R1's Psig on the probe's exact subset, used as the P1 / P6 targets below;
  - the coherence of the registered set constructors, 40 sets per type and m in each of spaces A / A′ / A″ (matrices
    only, no maps, no nulls): A1r q10–q90 −.02–.05; A2m .02–.37, with medians by core fraction .2 / .35 / .5 / .65 of
    ≈ .03–.05 / .09–.13 / .15–.23 / .29–.34; A2 .63–.92.
- **Verification pass** (asdg-skeptic, 2026-09-24): R1's subset Psig; `classify()` applied to R1's own N1 × Mean and
  N1 × Meanabs rejections on the subset (indeterminate [.041, .084] and calibrated [.039, .061]); the coherence of
  the former window sets A2w (.39–.87, not intermediate, so replaced by A2m); the loaders' region and gene-symbol
  matches.

## 1. Question
Which factor turns the matched null from calibrated (R1) into anticonservative (E3)?
- **(A) set coherence**, at matched set size.
- **(B) map smoothness.**
- **(C) statistic**, compared only at matched sidedness. For tight modules Cao's Mean and our T are nearly the same
  statistic, so the sidedness of the p-value is a factor of its own.
- **(D) analysis space**, split into:
  - processing (Cao's ENIGMA-toolbox matrix vs our §3.1 matrix);
  - gene universe (6,513 vs 15,633);
  - whole brain with tissue-class steps vs one class.

## 2. Design (the full factorial is run and reported)

### Spaces
- **A:** Cao's matrix `GeneExp/desikan_r0.4.csv` (34 left-cortex regions × 6,513 genes; the R1 inputs, same
  sha256).
- **A′:** our V-DK left-cortex matrix: the dk-ctx replica of amendment 3 — the same 34 regions, 15,633 genes, §3.1
  processing.
- **A″:** A′ restricted to the gene symbols it shares with Cao's 6,513.
- **B:** replay of E3's V-DK cells F-sp and F-mod: whole brain, 42 parcels, two tissue classes, class steps, 1,000
  plants each. S, y and the G2 pool are replayed, and each plant's saved r and p_G2 are asserted.

Regions are matched by name.

### Sets (A, A′, A″; each set type built in its own space's matrix; each set's coherence reported)
- **A1:** 100 of Cao's shipped sets (sizes 20–200 × Cao's first 10 repetitions). Space A only; used for plants
  P1, P2, P5 and P6.
- **A1r:** 100 uniform random sets, 50 at m = 25 and 50 at m = 100.
- **A2m:** 100 graded core-plus-filler sets: a core of round(f·m) genes (a uniform seed plus its most coexpressed
  genes) plus uniform filler, with f cycling through .2 / .35 / .5 / .65. Their coherence is intermediate and spans
  the published-list range (§0 descriptor: .02–.37); 50 at m = 25 and 50 at m = 100.
- **A2:** 100 tight modules: a uniform seed plus its m − 1 most coexpressed genes; 50 at m = 25 and 50 at m = 100.
- Coexpression is Pearson r over the space's 34 regions.
- Cells are per set size (m = 25, m = 100); A1 is pooled over Cao's sizes.

### Maps (A, A′, A″)
- **B1:** Cao's shipped near-noise maps 1–500.
- **B2:** 500 smooth fields on the 34 V-DK left-cortex MNI centroids, from `prereg.md` §6.1's generators: GRF 15 / 30 /
  60 mm and SAR ρ .5 / .9, 100 each, one class, no step.
- Every map's Moran's I is reported, using inverse-distance weights on these centroids.

### Statistics × sidedness
- **C1:** Mean of per-gene Fisher-z r, in three sidedness forms:
  - **+**: one-sided, positive;
  - **±**: two-sided on |stat| (Cao's);
  - **c**: centred two-sided, |stat − null mean| ≥ |obs − null mean|.
- **C2:** Meanabs (upper tail, Cao's).
- **C3:** T = Pearson r of the map with the set's mean-expression score, in the same three forms. C3+ is E3's.

### Nulls (K = 1,000 null sets per gene set, drawn once and shared across all 1,000 maps)
- **N1:** uniform same-size sets excluding S (G1).
- **N2:** Cao's rejection sampler over all genes: accept iff |mean pairwise coexpression − S's| < .01, unique, at
  most 1e6 draws. Fewer than K accepted → "unmatched", with the acceptance count and S's coexpression z (against
  2,000 random sets) reported.
- **N3:** G2, the `prereg.md` §4.3 sampler (±.02, 4 sub-bins, 20 restarts).
- **N3′:** G2 at ±.01. A1 in space A only, for P6.

p = (k + 1)/(K + 1).

### Space B
- C1, C2 and C3 are computed on each plant's own map, in the sidedness forms above.
- **N1:** 1,000 fresh sets.
- **N2:** fresh, at most 1e6 draws.
- **N3:** the replayed E3 G2 pool of 500 sets. C3+ × N3 is E3's own p_G2.
- Every rate is also reported by class-step stratum (step 0 / step 1).

**Seeds:**
- nulls: SeedSequence([5, space id, set-type id, tag, set index]), with tag 0 = N1, 1 = N2, 2 = N3, 3 = the
  coherence reference, 4 = N3′;
- fields: [5, 0, 0, 2, map index]; set construction: [5, space id, 9, 9, 0]; bootstrap: [5, 0, 7, 7, 7];
- space B's probe nulls: SeedSequence(plant seed + [5]).

Every draw is recorded.

## 3. Plants (checked before any readout; a failure stops the probe and is reported)
- **P1, must-pass (the apparatus reproduces R1 on the same subset).** A1 × B1 × {C1±, C2} × {N1, N2}.
  - Psig must be within ±.010 of R1's values on exactly these 100 sets × 500 maps: N1 .0610 / .0490, N2 .0446 /
    .0499.
  - For N1, the per-test Spearman correlation with R1's p-values must also be ≥ .95.
- **P2, must-catch (Cao's coexpression artefact).** A1 × B1 × C1± × N1: per-set Psig regressed on set mean
  coexpression, R² ≥ .30. On the subset R² was .68 in R1 (Cao .538, R1 whole sample .541).
- **P3, must-reproduce (E3's failure).** Space B, F-mod × C3+ × N3 equals E3's p_G2 plant by plant (asserted).
- **P5, known answer: exchangeability.** A1 × B1 × {C3±, C2} × N1 must **not** be classified "anticonservative".
  Uniform random sets are exchangeable with N1's sets, so the rate is ≈ .05 on average. On one 100-set subset the
  three-way class can still be "indeterminate": R1's own C1± × N1 on this subset is [.041, .084].
- **P6, must-pass (the G2 implementation).** A1 × B1 × {C1±, C2} × N3′ within ±.010 of R1's G2 descriptor on the same
  subset: .0366 / .0526.
- **P4, power (descriptor).** 100 planted positives per set type and space on B2 maps:
  y = .5·z(score) + √.75·z(field). Two variants: the raw mean-expression score, and the mean of z-scored gene profiles.
  Every statistic × null's catch rate is reported, not gated.

## 4. Classification of each cell (one three-way rule everywhere)
- Spaces A, A′ and A″ use a two-way (sets × maps) cluster-bootstrap 99% CI of the false-alarm rate, from 1,000
  resamples. Space B uses the exact 99% binomial CI, since plants are independent.
- **Anticonservative:** lower bound > .05 and rate > .07.
- **Calibrated:** upper bound ≤ .07 and rate ≤ .06.
- **Indeterminate:** otherwise.
- Rates are reported at α .05 (the E3 and Cao level) and at .025.
- Unmatched fractions of N2 and N3 are results, not failures.

## 5. Readouts (all reported; none is a win condition)
- **O1, statistic** (C1 vs C3 at matched sidedness, + / ± / c; C2 separately). In space B, F-mod, and in A / A′ / A″
  × A2 × B2.
- **O2, smoothness.** B1 vs B2 per set type and m. Plus a linear fit of each map's rejection rate (at .05) on its
  Moran's I, within B1, within B2 and pooled, reporting slope, intercept, r and the Moran's I at which the fit crosses
  .05 (flagged if outside the data).
- **O3, coherence** (A1r vs A2m vs A2 at the same m). Plus a linear fit of each set's rejection rate (at .05) on its
  coherence, pooling A1r / A2m / A2 at one m, per space × map family × null × form, with the coherence at which the
  fit crosses .05.
- **O4, space.**
  - A vs A″ isolates processing;
  - A″ vs A′ isolates the gene universe;
  - A′ vs B isolates whole brain, tissue classes and steps, and 34 vs 42 parcels. This last one remains a bundle and
    is declared as such.
- **O5, reach.** N2 and N3 unmatched fractions and target z by set type.

**What each outcome does to the paper-1 claim** (N3 at matched sidedness):
- **O1:** if C1 and C3 agree, the failure is not about aggregation. If only C3 fails, the claim narrows to
  aggregation-independent statistics.
- **O2:** if only B2 fails, the claim is stated for smooth maps, with the Moran's I at which the regression crosses
  .05.
- **O3:** the claim is stated for coherence above the fit's crossing point. If A2m (the published-list coherence
  range) is calibrated, the paper says the failure needs module-level coherence.
- **O4** (at m = 25, the size space B has):
  - if A is calibrated where A″ / A′ are not, the failure depends on processing or universe, and the paper says so;
  - if A′ is calibrated and B is not, the failure needs whole-brain class structure;
  - if all fail alike, the claim is general.

## 6. Code, compute
**Code:**
- `arcs/audit/probes/regime/src/regime.py` covers spaces A / A′ / A″.
- `regime_replay.py` covers space B.
- Both reuse `arcs/audit/src/e4_r1_cao.py` (Cao's statistics and sampler; the ‖Σz‖² coexpression identity, which R1
  already asserts equals the pairwise mean), `e3_plants` / `e3_species_replay` (the replay), `asdg.genesets` (G2)
  and `asdg.spatial` (fields).

**Toy tests before the run** (both scripts' self-tests):
- the sidedness forms;
- the tight module constructor, the coherence ordering and the ‖Σz‖² coherence identity;
- the three-way classifiers (the bootstrap one and the exact-binomial one) on planted rates.

**Compute:** ≈ 2 h on 22 workers, after the amendment-3 battery and its gates.

**Outputs:**
- `arcs/audit/probes/regime/results/regime_A.json` (spaces A / A′ / A″) and `regime_B.json` (space B): every cell with
  rate, CI, class and unmatched counts; the plants; the Moran's I and coherence fits.
- Per-test p-values in `artifacts/regime/`.

## 7. Review record

**v3 verification: verified.** Three one-line items fixed before freezing, without a further pass:
- the self-test checks the graded constructor (A2 > A2m > A1r) in place of the retired window one;
- every map's Moran's I is written to `regime_A.json` (`moran_per_map`);
- the docstrings updated.

**v2 → v3** (verification pass):
- **R6** P5 requires "not anticonservative"; the "calibrated" rule could stop a correct run.
- **R7** A2w (module-level coherence .39–.87) replaced by A2m (graded core plus filler, .02–.37; §0 descriptor); O3
  restated.
- **R8** Moran's I and coherence fits within and across families, with intercepts and crossing points.
- Code/text items: cells per m; the seed scheme written as coded; `regime_replay.py` given its own self-test of its
  forms and its three-way rule.

**v1 → v2**
- **R1** sidedness made a factor; statistics are compared only at matched sidedness; O1 restated.
- **R2** space D split into A, A″, A′ and B.
- **R3** P1 targets taken on the same subset, plus per-test agreement.
- **R4** one three-way rule everywhere.
- **R5** size-matched random sets (A1r).
- **R6** known-answer plants P5 and P6.
- **R7** intermediate-coherence sets (then A2w, replaced in v3) and the coherence regression.
- **R8** the Moran's I regression.
- **R9** two planted-score variants.
- **R10** the G1 range corrected to .085–.116, O4 consequences registered, space B reported by step stratum, and the
  reviewer's computations declared.
