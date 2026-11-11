# PREREG AMENDMENT 4 — A1 `audit`: nine audit targets added to §5.1 (operator decision)

**v4 — the frozen version** (`bench.py freeze`; hash in `FROZEN.txt`). v1 was reviewed by asdg-skeptic (2026-09-24:
"fix then freeze"; 2 A / 6 B / 2 C findings, all adopted). The v2 verification pass left M2 partly open and noted two
clarifications. The v3 verification found M2's T still nonlinear (Fisher-z) and flagged Dear 2024's cohort
provenance. v4 applies both exactly as the verifier prescribed, without a further pass (§4). Amends `prereg.md` (FROZEN, sha256 a632b852…) §5.1, as amended by `prereg_amend_1.md` to
`prereg_amend_3.md`. Everything not named here is unchanged. In particular, the claims register (§5.2) is still to be
written and frozen before any statistic touches an ASD map, and the verdict is amendment 3's.

## 0. Status and exposure (declared)
**Timing.** Written 2026-09-24, **before any statistic on any ASD map or claim.** The audit has not run; the
amendment-3 plant battery is running and none of its gates has been read. The targets were recommended by a
literature pass (asdg-lit, 2026-09-24; `literature/PRIOR_ART.md`, "Targeted novelty checks", item 4). That pass
screened 44 ASD imaging-transcriptomic claim papers for:
- influence;
- auditability (public map, gene list, code);
- claim classes the frozen list does not cover.

The operator accepted all its recommendations.

**Selection is not blind to the published nulls, and it cuts both ways.** The pass recorded each paper's own nulls.
- Toward failure: "no spatial or gene null" is among the reasons given for Pagani 2026 and Pretzsch 2024.
- Toward survival: Moreau 2020 was proposed as a "known-answer" target, Hansen 2022 as a "nuisance anchor", and the
  Pagani and Benkarim notes call those pipelines positive controls.

Registered now:
1. The **only headline survival fraction is the frozen 11 targets'**. The added targets, and their union with the
   frozen 11, are reported descriptively.
2. Every table is **stratified by the claim's own inference level, taken at its final inferential step**: none /
   spatial null only / gene null only / both / other. The level is recorded in the claims register, from the paper,
   before any statistic.

**Sealed cohorts.** The following are audited **only after A3's hypotheses are frozen**: maps derived from ABIDE II or
HBN, and the frozen target Romero-Garcia 2019's ABIDE II validation claims. This is the PLAN.md seal; A1 §2 applies the
same rule to ABIDE I ahead of A2. The maps concerned:
- Park 2021: ABIDE II.
- Benkarim 2021: ABIDE I and II.
- Pagani 2026: ABIDE I and II plus a Child Mind Institute collection; overlap with HBN is unverified, so it is treated
  as HBN.
- Dear 2024: its ASD centile map comes from BrainChart (n_ASD = 381, no cohort named in the paper), and BrainChart's
  open datasets include ABIDE and HBN. Unverified overlap is treated as sealed, as for Pagani. The deferral is lifted
  only by provenance, recorded in the register: BrainChart's study list (its SI19) showing that none of the 381 ASD
  cases come from ABIDE II or HBN.

Until then these claims stand in the register as "deferred (sealed cohort)"; their definitions and public material
are still registered before any statistic. While Romero-Garcia's ABIDE II claims are deferred, the frozen-11 fraction
is reported as **interim**: the deferred claims are listed apart and counted neither as survivals nor as failures.
The final headline includes them once they have run.

**LEAP exposure.** Pretzsch 2024, Leyhausen 2024 and Seelemeyer 2025 are LEAP group maps. Auditing them exposes A5's
contingent LEAP cohort at group level. If A5 opens, its prereg lists these audit results as seen.

**NeuroVault attributions** below were inferred by the pass. Each is confirmed or rejected only by:
- provenance (DOI or paper links, collection and image metadata);
- author confirmation;
- a visual match to a published figure.

No statistic on a map is allowed before the register is frozen. A target without its public material is "not
auditable" and stays in the denominator (§5.1, unchanged).

**Parcellations outside the planted classes** (Schaefer-200, Glasser-360, MIST64, voxelwise). Each such claim is run
either:
- natively, labelled "calibration extrapolated: parcellation outside the planted classes"; or
- re-parcellated onto V-DK, dk-ctx or V-AAL, labelled "re-parcellated".

The register fixes the choice per claim.

## 1. Added targets (§5.1 table, rows appended)

| target (key) | status | claim class | public material to check |
|---|---|---|---|
| Pagani 2026 (pagani2026crossspecies) — deferred (sealed cohort) | peer-reviewed | hypo/hyper-subtype voxelwise global-connectivity maps → AHBA NeuroVault decoding → hypergeometric enrichment (ASD DE modules, SynGO, Reactome); no spatial or gene null | subtype Cohen's-d NIfTI maps (GitHub `functional-neuroimaging/biological_subtyping`; NeuroVault 14698, inferred) — which map was decoded to be confirmed; decoded gene lists (Supp Tables 2–3); code |
| Benkarim 2021 (benkarim2021connectivity) — deferred (sealed cohort) | peer-reviewed | ABIDE idiosyncrasy t-map → AHBA donor-slope decoding, 1,000 spins → CSEA enrichment | t-map (NeuroVault 8667, inferred); gene list (Supp Table 4 / Data 1); code (MICA-MNI/micaopen) |
| Dear 2024 (dear2024corticalgene) — deferred (sealed cohort) pending provenance | peer-reviewed | autism cortical-volume centile map (Desikan-Killiany 34) × AHBA components C1–C3 (HCP-MMP gene weights, projected to DK), 5,000 spins | map (Supp Table 4); component weights (Supp Table 1); code (richardajdear/AHBA_gradients) |
| Pretzsch 2024 (pretzsch2024patterns) | peer-reviewed | LEAP longitudinal maturation PCA/PLS loading maps (Glasser-360) → AHBA donor-LME decoding → GeneOverlap with ASD-downregulated genes; spatial null declined | loading maps (Supplement 2 eTables 10–13; NeuroVault 12188 / 12203, inferred); decoded gene list (partial) |
| Park 2021 (park2021subcortico) — deferred (sealed cohort) | peer-reviewed | diffusion-connectome manifold case–control t-map (Schaefer-200; ABIDE II) → AHBA NeuroVault decoding (FDR, 100-rotation spin per gene, DS > 0.5) → CSEA / BrainSpan enrichment | t-map (Nature Source Data file); gene list (Supplementary Data 1) |
| Moreau 2020 (moreau2020mutations) | peer-reviewed | 16p11.2 / 22q11.2 CNV FC beta profiles (MIST64) × expression of the locus genes: PLSR R² with a label-shuffle null; the paper's own size-matched random-gene null failed (p = .31 / .36, "not gene-specific"); **CNV class, not idiopathic autism** | profiles (Supp Data 1, GitHub); gene correlations (Supp Data 4); code (surchs/Neuropsychiatric_CNV_code_supplement) |
| Hansen 2022 (hansen2022local) | peer-reviewed | ENIGMA-ASD cortical-thickness map (DK-68) × AHBA gene PC1 within a 7-predictor multilinear model (6 non-expression maps), 1,000 spins | ENIGMA thickness map and gene-PC1 map (GitHub netneurolab/hansen_crossdisorder_vulnerability); code |
| Leyhausen 2024 (leyhausen2024intrinsic) | peer-reviewed | LEAP intrinsic grey-matter connectivity t-maps → AHBA GEDA / NeuroVault decoding → enrichment | t-maps (NeuroVault 12301, inferred); gene lists only by re-decoding (then "re-derived") |
| Seelemeyer 2025 (seelemeyer2025decomposing) | peer-reviewed | LEAP behaviour-domain × CT/SA t-maps → AHBA GEDA decoding → enrichment; no spatial null | t-maps (NeuroVault 13397, inferred); gene lists as Leyhausen 2024 |

## 2. How the added claim classes enter the frozen claim classes

**Decoded-list enrichment** (Pagani, Benkarim, Park, Pretzsch, Leyhausen, Seelemeyer). The tested set S is the
external set: an ASD DE module, a SynGO or Reactome class, a CSEA class, the ASD-downregulated genes, and so on. It is
not selected on the claim's map, so these claims take amendment 3 §2's **enrichment rule and the full verdict**.
- **T** = the mean over S's genes of the per-gene **Pearson r** (not Fisher-z) between the claim's map and the gene's
  expression on the §3.1 matrix, for every decoded-list claim. This equals ⟨ŷ, s_z⟩, so it is linear in the set's
  z-scored score, the form G6s needs. It is also amendment 3 §2's mean PLS1 weight up to a positive per-map constant,
  so every leg gives the same p-values. Two quantities are recomputed as **reproduction descriptors only**:
  - the mean Fisher-z r;
  - the paper's own decoding statistic (for NeuroVault / GEDA donor-LME decoding, the one-sample t of the six
    per-donor slopes, on per-donor parcel matrices under §3.1 settings).

  Neither has a G6s form: arctanh is nonlinear, and each gene's donor SD sits in the t's denominator.
- **Null legs** (amendment 3 §2):
  - G1, G3m and G6l recompute the mean over each null set, with the per-gene statistics and y fixed;
  - G6s acts on the gene-side-centred z-scored matrix;
  - the site leg recomputes every per-gene statistic on each surrogate map.
- **Reproduction targets.** The paper's own statistic (hypergeometric OR, GeneOverlap, CSEA p) and its decoded list,
  compared descriptively: Jaccard of the lists, and the OR.
- **Labels.** These claims are "re-derived" (a continuous T in place of a thresholded list), and "re-parcellated"
  where that applies.

**Map × expression-component claims** are tested at Level 0 and with the site leg only, labelled "component-level
(species leg not applicable)". They are never counted as surviving the full verdict. The claims:
- **Dear 2024**: the DK-34 centile map × C1–C3.
- **Hansen 2022**, sub-claim: T = r of the ENIGMA-ASD thickness map with AHBA gene PC1. The full-model R² and the
  dominance statistics are reproduction descriptors. The map is the same one used by the frozen Patel and Giacomel
  targets, so these claims are flagged as dependent.
- **Moreau 2020**: the PLSR R² as the paper states it, with §4.7's refit applied on every permutation and every
  surrogate. Its own failed gene-specificity test is recorded. MIST64 has no §3.1 matrix, so the register fixes the
  route: a MIST64 matrix built under §3.1 settings, or re-parcellated. The CNV class is reported apart from the
  idiopathic-ASD counts.

## 3. Unchanged
m (the number of claims) is fixed when the claims register is frozen (§5.2), which now covers the frozen and the added
targets. The verdict, its threshold (α_v = .025 per claim; BH descriptive) and every gate are amendment 3's.

## 4. Review record

**v3 → v4** (verification pass; the fixes are the verifier's own):
- **M2** T is the mean per-gene Pearson r, equal to ⟨ŷ, s_z⟩. The mean Fisher-z r is a descriptor, because arctanh
  breaks G6s's linearity and |arctanh r| ≥ |r| would inflate the observed T.
- **Out-of-scope A** Dear 2024 is deferred (sealed cohort) pending BrainChart provenance.

**v2 → v3** (verification pass):
- **M2** T is the mean Fisher-z r for every decoded-list claim; the donor-LME t becomes a reproduction descriptor.
- **M1** the interim frozen-11 fraction while Romero-Garcia's ABIDE II claims are deferred.
- **M5** §4.7's refit on every permutation and surrogate for Moreau's R².

**v1 → v2**
- **M1** sealed-cohort deferral: Park, Benkarim, Pagani, and Romero-Garcia's ABIDE II claims.
- **M2** decoded-list claims routed through the enrichment rule (full verdict) instead of component level.
- **M3** reproduction comparisons made class-appropriate, and the added targets kept out of the headline.
- **M4** resolved by the continuous T: no list is re-selected on surrogates.
- **M5** Moreau restated as the component-level claim the paper makes.
- **M6** Hansen's T defined; the shared map flagged.
- **M7** NeuroVault confirmation by provenance only.
- **M8** only the frozen-11 fraction is a headline; selection declared in both directions; inference level taken at
  the final step.
- **M9** Dear's map is DK-34.
- **M10** LEAP exposure and out-of-class parcellations declared.
