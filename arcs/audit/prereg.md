# PREREG — A1 `audit`: null-cascade audit of published ASD imaging-transcriptomic claims

Arc `ASDG-AUD` (asd-imaging-genetics/audit). Programme kills K1–K6 in `PROGRAMME.md` apply.
Written 2026-09-23, before any measurement on AHBA-derived matrices, any plant, and any ASD map.
Draft v1 was attacked by an adversarial review (20 findings, 4 blockers) before freeze; this is v2. The
findings and how each was addressed are in `arcs/audit/prereg_review_2026-09-23.md`; a second pass on v2
(12 items) is recorded there too and resolved in this v3.
Entities: `ASDG-AUD-E1-nullengine`, `ASDG-AUD-E2-survival` (the survival table; the plan calls it "E3 audit"),
`ASDG-AUD-E3-plants`, `ASDG-AUD-E4-apparatus`, kills `ASDG-AUD-K1-plantfail`, `ASDG-AUD-K2-reprofail`.
Amendments are new frozen files (`prereg_amend_<n>.md`); this file is never edited after freeze.
Code: `src/asdg/` (engine) and `arcs/audit/src/` (runs), at the commit that freezes this file unless an
amendment says otherwise.

## 1. Questions

**Q-primary (sign-independent, the P1 paper).** Of the published ASD imaging-transcriptomic claims that can
be re-run from public material, what fraction survives the full cascade (§4) applied to the authors' own
maps and gene sets? Every claim is reported at every level, pass or fail.

**Q-instrument (the D05 residual).** Does each null family reach its nominal false-alarm rate on data where
its own null hypothesis is true by construction, and catch planted associations that violate exactly that
hypothesis, at volumetric parcellations with subcortex (and cerebellum), from generators independent of
the null's own generator? Curves per family and per class are reported whatever they show.

**What is a WIN vs a PREREQUISITE.**
- PREREQUISITE (not a result): the AHBA matrices pass A1–A5 (§3.1); the plant gates pass (§6.4); the
  reproductions R1–R3 land within tolerance (§3.3). None of these is a finding.
- WIN for P1: the survival table itself, complete, with each claim's level-by-level p-values — whether 0 %
  or 100 % survive. The audit has no favourable sign.
- WIN for the instrument: per-family false-alarm and catch curves across ≥ 3 parcellation classes, ≥ 5
  field generators and 3 set sizes, including the tissue-class-step failure mode. No comparative claim
  "J1 beats the naive joint null" is registered (the naive joint null is reported as a descriptor only).

## 2. Data (all open; provenance in each `E:\data\asdg\<resource>\SOURCE.md`, copies in `results/data_manifests/`)

| role | resource |
|---|---|
| adult spatial transcriptome | AHBA microarray, 6 donors, via abagen 0.1.3 |
| gene backgrounds | GAMBA `Background_genes_null_brain.csv` (@0c012868): 2,711 brain>body (primary), 8,989 brain≥body, 18,405 brain non-zero. The paper says 2,711 / 8,989 / 16,743 and the `.mat` indices 2,655 / 8,296 / 16,778 — recorded, not reconciled; the CSV is used. The 39 duplicated symbols with conflicting flags are dropped. |
| developmental trajectories | BrainSpan RNA-seq Gencode v10 gene matrix (gene matching only, never a spatial map) |
| real-data plants | GAMBA bundle (Wei 2022 inputs: DK-114 left-cortex expression, HSE list, nodal-strength vectors, AD ALE map); HCP S1200 T1w/T2w (neuromaps) |
| synthetic plants | independent GRF / SAR fields on each class's parcel centroids (§6.1) |
| audit targets | §5 |

**No ABIDE data (I or II) and no HBN data are read in A1.** The ABIDE I PCP time series are downloaded
(for A2) but not opened by any A1 script. The Vairam/Roy reproduction (former R4) moves to A2, after the A2
prereg is frozen, so that no ABIDE I case-control map or gene loading is seen before A2's hypotheses are.

**Parcellation classes.** V-AAL: PCP AAL-116 (cortex + subcortex + cerebellum) — primary. V-DK: abagen's
Desikan-Killiany volumetric atlas (cortex + subcortex + brainstem). V-CC200: PCP CC200 (false-alarm gates
only). Tissue class per parcel (cortex / subcortex-brainstem / cerebellum / other) and hemisphere (L / R / B,
B = centroid |x| < 2 mm) are assigned by `arcs/audit/src/e4_ahba_matrices.py` from atlas labels (CC200: its
majority AAL label, else its majority HO label) before any expression is computed.

**Parcel and hemisphere policy (fixed).** Primary: parcels with hemisphere L or B (left hemisphere +
midline, all tissue classes). Multiverse cell: bilateral (L, R, B) with abagen `lr_mirror='bidirectional'`.
A parcel enters an analysis iff the map value is finite and the parcel has ≥ 1 AHBA sample (sensitivity:
≥ 2 donors). Counts of parcels kept/dropped per atlas × map are reported. Audit maps defined bilaterally are
analysed on their left + midline parcels (as Patel 2021 and Giacomel 2026 did); maps defined only for one
tissue class use only that class.

## 3. Apparatus assertion (`ASDG-AUD-E4-apparatus`) — runs first

### 3.1 AHBA matrices
abagen 0.1.3 `get_expression_data` with **frozen defaults** (ibf_threshold 0.5, probe_selection
'diff_stability', donor_probes 'aggregate', lr_mirror None, missing None, tolerance 2, sample_norm 'srs',
gene_norm 'srs', norm_matched True, norm_structures False, region_agg 'donors', agg_metric 'mean',
corrected_mni True, reannotated True), all 6 donors, report saved verbatim; atlas_info as in §2.
- A1: 6 donors loaded.
- A2: V-DK yields **exactly 15,633 genes** (Markello 2021; Giacomel 2026). Otherwise → K2 (definitions).
- A3: no all-NaN gene column; parcels without samples listed and dropped (never interpolated).
- A4: every saved matrix is read back and compared (max |Δ| < 1e-12).
- A5: V-DK matrix recomputed in a second venv with pandas 2.2.3 (`env/venv_pd22`, lock in
  `env/requirements_pd22.lock`): max |Δ| < 1e-6 and identical gene list, else K2.
- Mini-multiverse (reported): gene_norm ∈ {srs, zscore}; norm_matched ∈ {True, False}; leave-one-donor-out
  ×6; bilateral cell. A surviving audit claim is "donor-robust" iff its statistic keeps its sign in ≥ 5/6
  leave-one-donor-out runs.

### 3.2 Plants — §6

### 3.3 Reproductions (failure → `ASDG-AUD-K2-reprofail` unless reconciled to a documented source difference)
- **R1 Cao 2024** (cao2024unraveling; note `literature/notes/cao2024unraveling.md`), "Main" + S5 + S17.
  Inputs: authors' shipped files (repo `zh1peng/paper_code` @54c690f8): `GeneExp/desikan_r0.4.csv`,
  `BrainDat/desikan_sim_spatial0.03.csv` (1,000 maps), `GeneSets/desikan_r0.4_Sim.rds` (500 sets),
  `desikan_spin_brain_perm_id.rds`. Reference = per-test p-values in the shipped
  `results/Res_desikan_r0.4_sim_spatial0.03_Sim_{random_gene, spin_brain, random_gene_coexp, spin_random_mixed}_pearson_sim1000.csv`.
  Read-check first: reference Psig (share of 500,000 tests with p < .05) must match the figure-read values
  in the note (competitive Mean .053 / Meanabs .049; spin .061 / .096; coexp .049 / .049; joint .069 / .093)
  to ±0.005, else we misread their files and stop. Our re-implementation (their definitions: gene-level
  Pearson r with the map, Fisher z; Mean = mean z over the set; Meanabs = mean |z|; two-sided
  p = (#{|null| ≥ |obs|} + 1)/(n + 1); 5,000 nulls; competitive = same-size random sets; spin = their
  permutation ids; coexp-matched = **Cao's own sampler** re-implemented from their code (rejection
  sampling, ±0.01 on mean coexpression, ≤ 1e6 draws); joint = their spin ids + a fresh random set per
  iteration) must, for each of the 8 cells {Mean, Meanabs} × {competitive, spin, coexp, joint}:
  |Psig_ours − Psig_ref| ≤ 0.010; and, for the competitive and spin cells only, per-test
  Spearman(p_ours, p_ref) ≥ 0.95 (≥ 0.99 for spin, which shares permutation ids) and ≥ 95 % of tests with
  |p_ours − p_ref| ≤ 3·√(2·p̄(1−p̄)/5000). Our G2 sampler is run on the same tests as a descriptor (how much
  the sampler choice moves Psig), never as a tolerance check.
  Also, competitive-Mean: R² of per-set Psig-G on set mean coexpression within ±5 percentage points of the
  same regression on the reference file. Random draws may be shared across maps (a stated deviation).
- **R2 Giacomel 2026** (giacomel2026cartography) spin level, from their shipped GEDAR maps, ENIGMA d-vectors
  and null files `*_corr_<thr>.tsv`. Step 1: generate the null with their procedure (netneurotools
  `gen_spinsamples`, 'vasa', 1,000 rotations, seed 2024, DK fsaverage5 left centroids) and compare it to
  their shipped null values. If identical (max |Δ| ≤ 1e-6): ρ and p_spin must match exactly (±0.001).
  If not identical: ρ must match ±0.001 and each p_spin within 3·√2·√(p(1−p)/1000). Cells: MDD combined
  cortical 10/5/1 % (ρ .529/.546/.531, p .005/.003/.003) and ASD combined cortical 1/5/10 % (ρ −.150/.413/−.053,
  p .252/.073/.423).
- **R3 abagen**: A2 + A5.

## 4. The cascade (`ASDG-AUD-E1-nullengine`)

A **claim** is (map y over parcels, gene set S or gene ranking, statistic T, published direction), fixed in
the claims register (§5.2) before any statistic on it. **Set-vs-map statistic**: T = Pearson r between y and
the set score (per-parcel mean of the member genes' abagen-normalised expression); Spearman reported
alongside. A set with < 5 genes present in the matrix is "not testable" (enforced in code); absent genes
are listed per claim. Single-gene reproductions (C1) are exempt and run Level 1 + G1 + G3 only.
All p-values are one-sided in the registered direction, (k + 1)/(n + 1). Plants use direction +1.

### 4.1 Level 0 — naive
Parametric p of T. Reproduction check: our T must equal the paper's reported value ±0.05 (r, ρ, R², β). A
miss does not stop the claim: it runs through every level, is flagged "not reproduced", and is counted in a
separate column; the headline survival count uses reproduced claims only.

### 4.2 Level 1 — spatial nulls on y (10,000 surrogates each at audit level)
- S1 BrainSMASH `Base` (all pairs; Euclidean centroid distance, mm; `resample=True`; defaults otherwise).
  Variogram misfit (relative RMS over the bottom 25 % of distances) is logged per map, not gating.
- S2 Moran spectral randomisation, singleton, w_ij = 1/d_ij.
- S1c, S2c class-stratified variants: y demeaned within tissue class, surrogates generated within class
  (classes with < 10 parcels permuted within class), class means added back.
- **Adoption rule (fixed now, decided by §6):** Level-1 p = max(p_S1, p_S2) if that pair passes the §6
  spatial gates in every class; else max(p_S1c, p_S2c) if that pair passes; else K1.
  S3 (spin, `netneurotools` 'vasa') is a comparator on surface-defined audit maps only.

### 4.3 Level 2 — gene (competitive) nulls on S (10,000 sets each at audit level)
All draws exclude the members of S.
- G1 random: uniform from the matrix universe.
- G2 coexpression-matched: mean pairwise coexpression within ±0.02 of S's; sampler = band split into 4 equal
  sub-bins, per sub-bin a greedy entry followed by a Metropolis walk (uniform member ↔ uniform non-member
  swap, accepted iff the set stays in the sub-bin), thinned every 10·m proposals; equal samples per sub-bin
  (so the achieved coexpression is centred on S's, not piled at the easy edge). If a sub-bin cannot be
  entered within 20 restarts the claim's G2 is "unmatched" (reported; the claim cannot survive). The
  achieved coexpression distribution is reported per claim.
- G3 brain background: uniform from GAMBA-2,711 ∩ universe (sensitivity 8,989; 18,405).
- G4 brain + coexpression: G2's sampler inside G3's background.
- G5 developmental-trajectory- **and coexpression**-matched: the pool is the union of each member's 20
  nearest neighbours in BrainSpan trajectory space (neighbours computed with all members of S excluded);
  sets are drawn from that pool with G2's sampler at S's mean coexpression ±0.02, so G5 sets are as coherent
  as S (pool < 2m genes → "not applicable"; unmatched band → "unmatched"). Features per
  gene: mean log2(RPKM+1) in 8 stage bins (8–12 pcw, 13–21 pcw, 22–37 pcw, 0–1 y, 1–6 y, 6–12 y, 12–20 y,
  20–40 y; cortical samples) = level block, and the same vector z-scored across bins = shape block; each
  block centred and scaled to unit mean squared norm; duplicate BrainSpan symbols averaged. Members without
  a trajectory contribute no neighbours; > 20 % without → G5 "not applicable" for that claim (it then
  cannot survive).
- Level-2 p = max over G1–G5.

### 4.4 Level 3 — J1 (surrogate-calibrated competitive null)
z(map) = (r(S, map) − mean_k r(R_k, map)) / sd_k r(R_k, map), R_k = the claim's G2 sets (K = 1,000), same
universe as S. Null: z over the adopted Level-1 surrogates of y (M = 10,000 at audit level), computed
separately with each of the adopted pair's two surrogate types; p_J1 = the max of the two
(#{z_m ≥ z_obs} + 1)/(M + 1) values — the Level-1 max rule, used identically in plants and audit. **H0 of J1**: S's advantage over its coexpression-matched sets on y is
no larger than its advantage on maps with y's spatial structure. J1 requires pool diversity (mean pairwise
Jaccard < 0.5) and sd_k > 1e-9; a violation is the status "degenerate pool" (the claim cannot survive). J1 is verdict-bearing only if adopted by §6.4; otherwise the verdict uses
Levels 0–2 and says so. The naive spin+shuffle joint null (Cao 2024 S17; pool G1) is computed as a descriptor.

### 4.5 Level 4 — cross-trait specificity (descriptor)
For ENIGMA structural ASD maps: S's J1 z (or Level-2 z if J1 is not adopted) on the ASD map is ranked among
the same z on the sibling disorders' maps in the same ENIGMA Toolbox release. "ASD-specific" = rank 1.

### 4.6 Verdict
A claim **survives** iff Levels 0, 1, 2 (and 3 if adopted) each have p < 0.05; conjunction p = max of the
level p-values. Headline: Benjamini–Hochberg q < 0.05 across all testable reproduced claims on the
conjunction p. Resolution check (done when the claims register is frozen): m claims require
1/(10,001) < 0.05/m, i.e. m ≤ 500; if m > 500 the register amendment raises the null counts first. Every
level's p is in the table for every claim, including after an earlier failure.

### 4.7 PLS / PLSR claims
- **Component claims** ("PLS1 explains X % of variance of y"): T = R² of PLS1 (weights ∝ Xᵀy on z-scored
  genes; `src/asdg/cascade.pls1`); for claims about component k > 1, sklearn `PLSRegression(n_components =
  paper's K, scale=True)`, component k. Level 0 = 10,000 parcel-label permutations of y with refit (the null
  most papers used). Level 1 = refit on every adopted surrogate. Levels 2–3 do not apply; such claims are
  labelled "component-level" and their verdict is Levels 0–1.
- **Sign**: every fitted component (on y, permutations and surrogates) is oriented so corr(score, y) > 0.
  The published direction of an enrichment is mapped to this orientation using the paper's reported
  orientation (e.g. "positive weights = higher in ASD"); if the mapping cannot be made from the paper, the
  test is two-sided (p = 2·min of the one-sided p's) and labelled so.
- **Enrichment claims** ("set S is enriched among top PLS1 genes"): T = mean PLS1 weight of S's genes (raw
  weights; the authors' bootstrap z is a stated deviation). Level 0 = Welch t of S's weights vs all others.
  Level 1 = refit on surrogates, recompute T. Level 2 = G1–G5 sets' T on y. Level 3 = J1 with r replaced by
  the mean weight (refit per surrogate).
- **Ranking-only claims** (a published ranked list with no set): the top-N list the paper reports is the set;
  N as published.

## 5. Audit targets (`ASDG-AUD-E2-survival`)

### 5.1 Targets and the public material each needs (obtainability recorded before any statistic)

| target (key) | status | claim class | public material to check |
|---|---|---|---|
| Segura 2024/25 (segura2024symptommapping) | preprint→journal | ADOS-2-total × MFG-seed iFC map (both diagnoses pooled) → AHBA decoded genes | NeuroVault 790618; 781986 (the authors' negative-control seed map, run as a within-paper control); decoded gene list |
| ENIGMA-ASD thickness / subcortical volume (patel2021virtual; giacomel2026cartography) | peer-reviewed | cell-type panels × ΔCT; TWAS-weighted maps × Δ | ENIGMA Toolbox CSVs (ventricle rows dropped: no volumetric label); Patel panels (supp.); Giacomel repo |
| Romero-Garcia 2019 (romerogarcia2019synaptic) | peer-reviewed | PLS of ΔCT (DK-308) × AHBA; synaptic / downregulated enrichment | ΔCT vector; PLS gene lists (supp.) |
| Berto 2022 (berto2022connectivity) | peer-reviewed | fALFF/ReHo × regional expression, 11 Brodmann areas | regional imaging values; gene lists (supp.) |
| Rasero 2023 (rasero2023neurogenetics) | peer-reviewed | subtype FC maps × AHBA | subtype maps; gene lists |
| Buch 2023 (buch2023asdsubgroups) | peer-reviewed | subgroup PLS × AHBA (Power-247) | code/maps; gene lists |
| Mamat 2025 (mamat2025molecular) | peer-reviewed | FD t-map (Schaefer-400) PLSR × AHBA | t-map; PLS gene ranks (supp.) |
| Vairam/Roy 2026 (vairam2026hyperhypo) | preprint | ΔFC node strength PLSR, AAL3 | code only; **deferred to A2** (needs an ABIDE map) — listed as "deferred" in the table |
| Liu 2026 (liu2026spatiotemporal) | peer-reviewed | risk-gene hot-spots in BrainSpan/AHBA (no spatial map) | Supp Data gene sets — Level 2 only, on their per-sample statistic |
| Xing 2026 (xing2026interpretable) | preprint | ABIDE I AAL-116 region-set expression contrast | region sets; gene lists (no ABIDE data needed if the region sets are published) |
| Wan 2026 (wan2026abide2multiplex) | peer-reviewed, abstract-only read | multiplex GM+WM × AHBA | only if maps/gene lists are obtained from the authors |

A target without its public material is **not auditable** (what was tried is recorded) and stays in the
survival table's denominator as such; it is never replaced by a reconstruction presented as theirs.
Re-running a claim in a parcellation other than the paper's is labelled "re-parcellated" and never counted
as a reproduction.

### 5.2 Claims register — frozen before any ASD statistic
`arcs/audit/claims_register.md`: per claim — map file and hash, parcellation (native or re-parcellated),
set/ranking and its source, T, direction and how it was derived from the paper, the paper's reported value
(table/figure id), claim class (§4 / §4.7). Frozen with `bench.py freeze` before the cascade touches any of
them; m is fixed there (§4.6 resolution check).

## 6. Plants and gates (`ASDG-AUD-E3-plants`) — run before §5; `ASDG-AUD-K1-plantfail` fires on any gate failure

### 6.1 Generators (all independent of the nulls' own generators: no BrainSMASH surrogates are used to build any plant)
Fields on each class's analysis-parcel centroids (`src/asdg/spatial.FieldGenerator`): Gaussian-kernel GRF
with length 15, 30, 60 mm; SAR (6-nearest-neighbour row-normalised W) with ρ = 0.5, 0.9 — five generators;
each with class step 0 or 1 (a random N(0, 1) offset per tissue class, in field-SD units) — ten generator
cells, equally represented. Gene sets are built from the class's own AHBA matrix (§3.1, primary parcels).

### 6.2 Families (H0 true by construction for the null families gated on them)
- **F-sp** (spatial H0: y independent of expression): y = field; S = random 25-gene set. Gates Level 1.
- **F-mod** (gene H0: y independent of expression; S coexpressed): y = field; S = a random seed gene plus
  its 24 highest-coexpression neighbours (never selected on y). Gates Level 2 (as a whole), G2, G4, J1.
- **F-traj**: y = field; S = a random seed gene plus its 24 nearest trajectory neighbours. Gates G5.
- Generator cells are assigned in rotation (plant i → cell i mod 10), so every cell has n/10 plants.
- n = 1,000 plants per family per class (V-AAL, V-DK, V-CC200) at m = 25; plus n = 300 at m = 10 and
  m = 100 in V-AAL (descriptors, not gates). Per plant: 500 surrogates per spatial null, 500 sets per gene
  null, J1 with M = K = 500.

### 6.3 Catch families (ground truth defined against each null's own H0)
- **C-sp** (violates the spatial H0): y = a·z(score_S) + √(1−a²)·field, S random, a ∈ {0.3, 0.6, 0.9}.
  Gates Level 1.
- **C-gene** (violates the gene H0): y = a·z(ẽ_S) + √(1−a²)·field, where ẽ_S = score_S residualised on the
  mean score of S's G2 sets and on the first 3 PCs of the class's expression matrix; S random;
  a ∈ {0.3, 0.6, 0.9}. Gates G2, G4, G5, J1.
- n = 300 per (family, a, class) for V-AAL and V-DK at m = 25.

### 6.4 Gates (each quoted with its measured value)
- **False-alarm gate** for a null family on a family where its H0 is true: pass iff the one-sided binomial
  test of rate ≤ 0.05 is not rejected at α = 0.001 **and** the rate ≤ 0.07. Applied per class to: Level 1
  (as adopted, §4.2) on F-sp, F-mod and F-traj, **separately for step = 0 and step = 1 cells** (n = 500
  each); Level 2, G2, G4, J1 on F-mod; G5 on F-traj; J1 also on F-sp (n = 1,000). With ~40 gates each
  failing a calibrated null with probability ≈ 0.002, a spurious K1 has probability ≈ 0.08; accepted.
- **Plant-active gates** (the plants must show the failure each null exists to catch; else K1): naive
  Level-0 false-alarm on F-sp ≥ 0.15 and G1 false-alarm on F-mod ≥ 0.10, per class.
- **Unmatched / not applicable / degenerate plants**: gates use computed plants only; a gate fails if > 5 %
  of its plants in any cell are unmatched, not applicable or degenerate; every count is reported.
  Each individual spatial null (S1, S2, S1c, S2c) and G1, G3 are reported on every family, not gated.
- **Catch gate**: rate ≥ 0.80 at a = 0.9, for Level 1 on C-sp and for G2, G4, G5, J1 each on C-gene, in
  V-AAL and V-DK.
- **Spatial adoption** (§4.2) is decided by these gates: the joint pair if it passes every Level-1
  false-alarm gate (both step strata, all three F families, every class) and C-sp; else the class-stratified
  pair under the same gates; else K1.
- **J1 adoption**: J1 is verdict-bearing iff it passes its false-alarm gates (F-sp, F-mod, every class) and
  its catch gate (C-gene, V-AAL and V-DK). Not adopted is not K1; it is reported as an instrument finding.
- Cascade-level false-alarm and catch rates on every family are reported as descriptors (they are not
  informative as gates because G1 alone controls random-S families; see the review).
- **Real-data plants** (in addition):
  - **P+1 (must pass)** AHBA expression PC1 over V-DK left cortical parcels × HCP T1w/T2w parcellated with the
    DK fsaverage/fsLR annotation: |ρ| ∈ [0.3, 0.9] and Level-1 p < 0.05 (adopted pair) and S3 p < 0.05.
  - **P+2 (must pass)** HSE genes (19, GAMBA list) × Wei 2022 nodal strength on Wei's own DK-114 left-cortex
    inputs (GAMBA bundle): β (standardised regression of the map on set-mean expression, NaNs handled as
    GAMBA's code) = 0.678 (NOS) / 0.637 (SD) / 0.450 (FC) to ±0.05; and G1 and G3 p < 0.05 for NOS and SD
    (Wei reports both). G2, G4, G5 and J1 on P+2 are registered audit outcomes, not must-pass.
  - **C1 (reproduction + must-catch; single gene: Level 1 + G1 + G3 only)** APOE × GAMBA `alzheimers_ALE.nii.gz` parcellated to the 57 DK-114 left
    cortical parcels (parcel mean): if β reproduces Wei's AD β = 0.631 to ±0.10, it must show Level-1 p < 0.05
    (the Level-1 max rule) and G3 p ≥ 0.05; failing that pattern → K1. If β does not reproduce, C1 is
    recorded as "not the same map" and the must-catch role rests on F-mod (the Fulcher failure mode),
    enforced by the plant-active gate on G1 and the G2/G4 false-alarm gates.
  - **C2** (Grove genes × BrainMap Asperger map): not run — neither is in the GAMBA bundle (INVENTORY.md).
  - **C3** coordinate gradients (A–P, I–S, |x|) × 400 random and 400 coexpressed-module sets per class:
    descriptor only (a module can genuinely track a gradient, so there is no ground truth).
- **K1** fires iff P+1 or P+2 fails, C1 fails its pattern (when reproduced), a plant-active gate fails, any
  false-alarm gate fails for Level 1 (both pairs), Level 2, G2, G4 or G5, or any catch gate fails for Level 1,
  G2, G4 or G5 (J1 failures only block J1's adoption). K1 is an
  instrument finding reported in full; fixes are amendments.

## 7. Factorial and reporting
`arcs/audit/results/MANIFEST.md` lists every planned (claim × level × null × parcellation × multiverse
cell) and (plant family × generator cell × class × size × strength) with its status (done / failed / not
applicable / unmatched / not obtainable). Every number names script, input and commit; seeds fixed and
recorded per run.

## 8. Contamination, deviations, data handling — declared in advance
- A1 opens no ABIDE, ABIDE II or HBN file. A2's prereg inherits a clean ABIDE I.
- Wei 2022's example pairs and Giacomel's MDD hit have no ground truth: they are reproductions (R2, P+2, C1),
  and whether Giacomel's MDD/ASD results survive G1–G5 and J1 is a registered audit outcome.
- ENIGMA subcortical CSVs have 16 rows incl. both lateral ventricles; the ventricles are dropped.
- **Pre-freeze exposure (toy data only, no real map)**: Moran spectral randomisation on synthetic Gaussian
  fields over 116 random centroids gave false-alarm 0.062 / 0.048 / 0.050 / 0.102 at kernel lengths
  15 / 25 / 40 / 60 mm (n = 600 each); a BrainSMASH check at 25 and 60 mm was started (result appended to
  `results/pre_freeze_toy_calibration.txt` when it finishes, whatever it shows). This is why S2 alone never
  carries the Level-1 verdict. The coexpression sampler's band-edge bias (achieved mean 0.133 for target
  0.150 under uniform-over-band sampling) was found in unit tests and fixed by sub-bin stratification (§4.3).
  A second toy MSR draw at 40 mm gave 39/400 = 0.098 (naive 0.37) — a further reason S2 never stands alone.
- Data handling: all downloaded data stay on `E:\data\asdg\` and derived matrices under `artifacts/`
  (gitignored); no participant-level data are read in A1; nothing controlled or individual-level enters git,
  prompts or logs (`docs/ETHICS_PRIVACY.md`).

## 9. Kills
- `ASDG-AUD-K1-plantfail` (§6.4).
- `ASDG-AUD-K2-reprofail`: R1, R2 or R3 misses tolerance and is not reconciled to a documented source
  difference → the audit (§5) does not run until reconciled; reported.
- Programme K1 (`ASDG-K1-plantfail`) is the programme-level image of the arc K1.
