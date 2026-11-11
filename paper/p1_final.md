---
title: "Calibrating gene-set nulls for imaging transcriptomics with planted truths: where coexpression-matched and spatial nulls fail, a fourth-corner fix, and a preregistered demonstration on autism claims"
short-title: "Calibrating imaging-transcriptomic nulls with planted truths"
author: "Radoslav Lovecký"
affiliation: "Arperon"
hero: figures/fig0_hero.pdf
hero-caption: "Summary. (a) Worst false-alarm rate over planted-negative strata for each null; dashes mark the nominal level (.05; .025 for the max test). (b) Catch rate for the strongest planted gene-set signal, map-side leg alone versus the full max test. (c) Interim audit (first two release batches): the 16 population units by category. The third batch's 196 units have not run and are counted neither way; 9 rows (Dear et al., 3; Vairam, Roy et al., 6) are deferred."
bibliography: ../../../literature/citations.bib
---


# Abstract

**Background.** Imaging-transcriptomic studies guard map–gene-set correlations with spatial and gene nulls, the strongest common gene null being coexpression-matched sampling. Neither has been calibrated with planted positives in the tissue-class and coherent-set regime where published claims sit.

**Methods.** On Allen Human Brain Atlas expression, we planted maps and gene sets of known truth and measured false-alarm and catch rates under a frozen, amended preregistration.

**Results.** Joint spatial surrogates were anticonservative where tissue classes differed in mean (false-alarm rate .078–.120); class-stratified surrogates were nominal. Coexpression-matched gene nulls were anticonservative for coherent sets (.196–.210; within a brain background, .399–.442), also in Cao et al.'s own regime, above the fitted coherence crossing for published-like sets. Ecology's fourth-corner max test, with constrained map-side and gene-side legs (α = .025), stayed ≤ .019 in all 390 verdict strata (gene-side leg alone ≤ .022 in 372 more), calibrated on every informative planted stratum within stated scope limits, but caught .585–.666 of strong gene-specific plants. On a preregistered register of published autism claims, the interim result (two of three release batches) is 0 of 16 population units surviving; the third batch's 196 units have not run and are counted neither way, and 9 rows (Dear et al., 3; Vairam, Roy et al., 6) are deferred. The one tested unit could not have survived (gene-side null uninformative; power unmeasured in its class).

**Conclusions.** Gene-set nulls need planted-truth calibration in the coherence regime of the sets they test; a max test holds its level there, at measured cost in power.

# 1 Introduction

Imaging transcriptomics asks whether the spatial pattern of a brain phenotype follows the regional expression of a set of genes. In autism, published claims of this kind link case–control maps of cortical thickness, connectivity or maturation to risk genes, cell-type markers or developmental programmes. Almost all rest on one operation: correlate a map with the mean expression profile of a gene set across parcels, then ask whether the correlation exceeds what a null distribution allows.

Two sources of false positives are well documented. Brain maps are spatially autocorrelated, so a parcel-label permutation is anticonservative, and spatial surrogates that preserve autocorrelation have become standard [@alexanderbloch2018spin; @burt2020brainsmash; @markello2021comparing]. Gene sets are coexpressed, so a set's mean profile is smoother and more extreme than that of a random set, and random-gene nulls are anticonservative for coherent sets [@fulcher2021overcoming]. Fulcher and colleagues showed that category false-positive rates rise with a category's within-category coexpression, and proposed phenotype-randomising ensembles as an alternative [@fulcher2021overcoming].

The field's response has been to require both kinds of null. Wei et al. recommended a sequence: a spatial null first, then a coexpression-matched gene null for multi-gene sets, then a brain-expressed background [@wei2022statisticaltesting]. Cao et al. compared eight test statistics under competitive and self-contained nulls and reported that a coexpression-matched competitive null removes the coexpression bias of the competitive null on random sets [@cao2024unraveling]. Coexpression-matched sampling now ships in toolboxes [@wei2022statisticaltesting; @cao2026brainenrich]. Applied studies treat a result as a finding when both a spatial and a gene null are passed (for example, [@lariviere2022epilepsy]), and intersection–union max-p rules have appeared in brain-map testing [@hillman2026netdom]. A recent preprint found a spin-significant enrichment of EEG alpha-power genes that a size-matched random-gene-set null fully explained, and recommended reporting a gene-set null beside the spatial null [@schenetti2026enrichment] (preprint) — independent support for gene-side nulls, though it did not test coexpression-matched nulls, tissue-class surrogates, a combined test or planted power. 

What is missing is calibration with planted positives in the tissue-class and coherent-set regime where published claims sit. Spatial nulls have been stress-tested with planted network-level signals, where spin and BrainSMASH over-rejected when an association was present everywhere but not specific [@hillman2026netdom]; the coexpression-matched gene null was calibrated on null data — random sets and near-noise maps [@cao2024unraveling].  Published autism gene sets are not random: many are coherent modules, cell-type markers or brain-enriched lists. Published maps are not white noise: volumetric maps span cortex, subcortex and cerebellum, whose expression differs sharply in mean. A null that is calibrated on random sets and near-noise maps may not be calibrated there, and a combination of two nulls, each valid under its own hypothesis, is only as good as its legs in the scenario where the other leg fails [@terbraak2017glm].

This paper does three things. First, it measures where the two standard defences fail, using maps and gene sets with known ground truth on real expression data, including a reproduction of Cao et al.'s own calibration regime. Second, it recasts the two-null problem as ecology's fourth-corner problem — testing a link between species traits and site environments through a species-by-site table [@legendre1997fourthcorner; @dray2008fourthcorner] — and adopts its max-test solution with constraints on both legs, calibrating the resulting rule on planted null and signal families and pricing its loss of power. Third, it applies the rule to a preregistered register of published autism imaging-transcriptomic claims, as a worked demonstration. That audit is interim: only two of its three data-release batches have run, and we report the result with that limitation in the same sentence wherever it appears.

# 2 Methods

## 2.1 Preregistration and amendments

The study was preregistered before any planted-truth gate was computed. The protocol and each amendment were frozen by SHA-256 hash before the analyses they govern; hashes and freeze times are listed in a manifest committed with the code.  Seven amendments followed. Each declares which of its elements were decided after results were seen; Table 1 summarises them. A separate preregistration governs the regime-boundary probe (Section 2.6). 

**Table 1. Preregistration and amendments.**

| document | frozen | what it changes | decided after seeing results? |
|---|---|---|---|
| protocol | 2026-09-23 | design, nulls, plants, gates, stop rule, audit targets; two adoption rules: the class-stratified spatial pair replaces the joint pair if the joint pair fails its gates (it did, and was replaced); the Level-3 null J1 becomes verdict-bearing only if it passes its gates at α = .05 (it did not, and was not adopted) | — |
| amendment 1 | 2026-09-23 | software environment for expression processing; cross-check | no |
| amendment 2 | 2026-09-23 | single-gene must-catch control (APOE × Alzheimer map) demoted to reproduction-only | yes (after it failed) |
| amendment 3 | 2026-09-23 | verdict becomes the fourth-corner max test at α = .025; per-null gene gates become descriptors; one plant-active gate dropped | yes (after the first gate battery) |
| amendment 4 | 2026-09-24 | nine audit targets added; only the frozen-11 fraction is a headline | before any audit statistic |
| amendment 5 | 2026-09-24 | catch and power become registered descriptors; untested plant families become scope labels; readings fixed | yes (after the second gate battery) |
| amendment 6 | 2026-11-02 | headline rule for the full audit | yes (after the interim audit result) |
| amendment 7 | 2026-11-03 | splits reporting: this paper reports the instrument and the interim audit | yes (after the interim audit result; before the third batch) |

## 2.2 Expression data and parcellations

Expression came from the six-donor Allen Human Brain Atlas, processed with abagen 0.1.3 at its defaults [@markello2021abagen]. The loader asserted the donor count, the gene count of the Desikan–Killiany volumetric matrix (15,633 genes), the parcels left empty by sampling (dropped and listed), and read-back equality; a second environment recomputed the matrix and agreed to within floating-point error. 

We used three volumetric parcellation classes, each assigning every parcel a tissue class (cortex, subcortex/brainstem, cerebellum): AAL-116 (primary), the Desikan–Killiany volumetric atlas shipped with abagen, and CC200 (false-alarm gates only). A cortex-only replica — 34 left Desikan–Killiany cortical parcels, a single tissue class, the format of ENIGMA case–control thickness maps — was added for the max test. 

## 2.3 Planted maps and gene sets

Null maps were drawn from five spatial field generators independent of every null's own generator: Gaussian random fields with length scales of 15, 30 and 60 mm, and simultaneous-autoregressive fields with ρ = .5 and .9. Each generator ran with a class step of 0 or 1 (a random N(0, 1) offset per tissue class, in field-SD units), giving ten generator × step combinations ("generator cells") represented equally. No spatial surrogate generator was used to build any plant. 

Null families (ground truth: no association between map and set):

- **Spatial null family.** Map = field; set = 25 random genes.
- **Coherent-module family.** Map = field; set = a random seed gene plus its 24 most coexpressed neighbours, never selected on the map.
- **Trajectory family.** Map = field; set = a seed plus its 24 nearest developmental-trajectory neighbours.
- **Expression-aligned family** (for the max test). Map = w·z(target) + √(1 − w²)·z(field), w ∈ {.5, .9}, where the target is a within-class module score, a coordinate gradient, an undemeaned module score or the brain-enrichment profile; 14 set kinds (random, brain-fraction-matched, cluster-cored, single-cluster and multi-cluster) from m = 25 to m = 1,000, never drawn from the target's module.

Catch families (ground truth: an association exists):

- **Spatial signal.** Map = a·z(set score) + √(1 − a²)·field.
- **Gene-specific signal.** As above with the set's score residualised on the mean score of its matched null sets and on the first three expression principal components.
- **Expression-aligned signal.** Map = a·z(set-specific within-class score) + .6·z(module target) + c·z(field), a ∈ {.3, .5, .7}.

Each null family had n = 1,000 plants per parcellation class at m = 25 (plus m = 10 and m = 100 in AAL as descriptors); catch families had n = 300 (spatial and gene-specific) or n = 500 (expression-aligned) per cell. 

## 2.4 Nulls evaluated

Map-side (spatial) nulls: variogram-matched surrogates [@burt2020brainsmash] and Moran spectral randomisation [@wagner2015moranspectralrandomization], each either joint across tissue classes or class-stratified (map demeaned within class, surrogates generated within class, class means added back). A pair's p-value is the larger of its two. 

The protocol also registered a stronger gene null, J1, as an additional verdict level (Level 3), to be required on top of Levels 0–2. J1 scores a set's correlation with the map against its coexpression-matched sets (a z-score) and compares that z with the same z computed on spatial surrogates of the map, so that the set must beat its matched sets by more than it does on maps with the same spatial structure. J1 was to become verdict-bearing only if it passed its false-alarm gates (spatial and coherent-module null families, every class) and its catch gate (strong gene-specific signal, AAL and Desikan–Killiany) at α = .05. 

Gene-side nulls: uniform random sets; brain-background random sets; coexpression-matched sets (mean pairwise coexpression within ±.02 of the set's, following [@wei2022statisticaltesting]); coexpression-matched sets within the brain background; and developmental-trajectory- and coexpression-matched sets. 

## 2.5 The fourth-corner max test

In ecology's fourth-corner problem a trait–environment link is tested through a species × site abundance table. Permuting sites alone, or species alone, protects against one kind of spurious link but not the other; the remedy is to test both ways and take the larger p-value, the max test [@terbraak2012maxtest; @dray2008fourthcorner; @terbraak2017glm]. The imaging-transcriptomic test has the same structure: parcels are sites, genes are species, the map is the environment and set membership is the trait.

The verdict for a claim (map y, set S, statistic T, registered direction) — the "full verdict", as opposed to a component-level test of a fixed expression component — requires three p-values each below α = .025:

1. a parametric p-value for T;
2. a **map-side leg**: the class-stratified spatial pair, p = max(variogram-matched, Moran spectral);
3. a **gene-side leg**: p = max of four gene-side nulls, each holding y fixed —
   - uniform random sets of S's size;
   - random sets matched on S's number of brain-enriched genes (genes expressed more highly in brain than in other body tissues);
   - a within-class gene-side Moran spectral randomisation: S's within-class profile, centred on its brain-fraction-matched expectation, is projected on the within-class expression components and its coordinates are sign-flipped (exact enumeration when the number of sign patterns is at most the draw count);
   - seed-anchored windows of genes ranked by within-class coexpression with a seed, matched to S's within-class coherence.

The conjunction p is the maximum of the three. A claim whose gene-side spectral null is dominated by one component (share > .8) is labelled "gene-side leg uninformative" and cannot survive. The level α/2 is borrowed from ter Braak et al.'s empirical correction for the max test, which was designed for 20–100 units per side [@terbraak2017glm]; here the gene side has 15,633 genes (Desikan–Killiany matrix), far outside that range, so α/2 is justified only by the planted calibration in Section 3.5, not by that correction.  Benjamini–Hochberg q-values on the conjunction p are reported as descriptive only. 

The audit used 10,000 draws per leg.  Spatial legs were enumerated exactly when the number of distinct within-class permutations did not exceed the draw count. 

## 2.6 Gates, stop rule and readings

Each family was gated against a preregistered threshold (false alarm ≤ .05, with a binomial bound; catch ≥ .80; plant-active ≥ .10 or ≥ .05 as stated, a plant-active gate requiring that a reference test known to be fooled by the planted confound is in fact fooled, so that the plants exercise it; and a matching limit: a gate fails if more than 5 % of the plants in any generator cell could not be served a matched null set).  A preregistered stop rule halted all downstream work whenever a gate failed, until a frozen amendment resolved it. 

The regime-boundary probe reproduced Cao et al.'s simulation (their expression matrix and gene universe, 34 left cortical parcels, near-white-noise maps, 1,000 maps × 500 random sets, eight cells) and extended it with tight coexpression modules, published-like gene sets, smooth maps, three test statistics (Mean, Meanabs and a t-type statistic) in one-sided, two-sided and centred forms, three gene nulls (uniform, Cao's rejection sampler, our coexpression-matched sampler) and four expression spaces. Cells were classified as anticonservative when the 99 % confidence interval of the rejection rate lay above the nominal level. 

Audit readings were fixed before any audit statistic: a survival reads "survives — calibrated evidence" only inside the planted regime (25 ≤ m ≤ 1,000, a planted parcellation class, no extrapolated gradient), otherwise "survives — calibration extrapolated"; a non-survival with no status flag reads "not detectable at this power", never "refuted"; component-level claims read "passes / does not pass at component level" and never count as survivals. 

## 2.7 The audit register

The register was frozen before any audit statistic. It lists every claim of 11 publications named in the protocol (the "frozen 11") and of nine targets added by amendment 4, with each claim's map, set, statistic, direction and the inference level the authors reached. The headline is the survival fraction over the frozen-11 population. A population unit is one registered positive autism claim of a frozen-11 publication (a family of claims counts once); descriptor rows and published nulls are not units, and units of unopened batches are listed apart and counted neither way.  Claims are classified as tested with the full verdict, not testable as stated, without a calibrated test, or not auditable (for example, unpublished inputs). A full-verdict claim whose published statistic our reconstruction does not reproduce leaves the population. 

Material was released in three batches, with material withheld to protect a separate preregistered analysis: (i) targets with open material; (ii) a second group, released after that analysis's tests were committed; (iii) a third group, still closed. 

# 3 Results — the instrument

## 3.1 Apparatus checks and reproductions

Cao et al.'s calibrated simulation was reproduced: all eight registered cells passed the ±.010 criterion on the proportion of significant tests.  On the same random sets, our coexpression-matched sampler gave proportions of .0363 (Mean) and .0515 (Meanabs).  A second published analysis [@giacomel2026cartography] reproduced exactly after we traced a difference to the authors' own later overwrite of their input maps; with the maps at the commit used for publication, the nulls were bit-identical. 

Two real-data positive controls passed: the principal axis of cortical expression against the T1w/T2w (myelin-sensitive) map (ρ = −0.811 on 34 left cortical parcels; class-stratified spatial p = .0017), and Wei et al.'s supragranular-gene example (β .678 / .637 / .450, reproducing the published values). 

The single-gene must-catch control did not pass. For APOE against an Alzheimer's atrophy map, our regression reproduced the published slope within the preregistered band (0.679 against 0.631), and the spatial null rejected, but the brain-background gene null also rejected (p = .014), contrary to the expected pattern. The control was demoted to reproduction-only by a declared post-hoc amendment and is reported as an unresolved reproduction difference (Section 5.3). 

## 3.2 Joint spatial surrogates fail at tissue-class steps

With no class step, both spatial pairs were nominal. With a class step, the joint pair was anticonservative in all nine class × family strata, at .078–.120. The class-stratified pair was nominal in every stratum (.008–.048) and caught strong spatial signal at 1.000 (Figure 2). 

## 3.3 Coexpression-matched gene nulls fail for coherent sets

Against independent smooth fields, the coexpression-matched null rejected .196–.210 of coherent 25-gene modules across the three parcellation classes, and its brain-background variant .399–.442. The trajectory-matched null was anticonservative on trajectory modules (.082–.093) and could not build matched sets for 46–55 % of coherent-module plants in at least one generator cell per class. 

The preregistered Level-3 null J1 was the strong baseline. With the adopted class-stratified spatial pair, its false-alarm rates on spatial and coherent-module null families were .024–.041 at α = .05 (all six gates passed), and it caught .986 (AAL) and .910 (Desikan–Killiany) of strong gene-specific plants (a = .9). It was not adopted because its AAL catch gate failed the matching limit (6.7 % of plants in one generator cell unmatched, > 5 %), not its rate. With the joint spatial pair, J1's false alarms were .027–.037 and its catch .774 and .702, below .80. Because J1 would have been an additional condition, not an alternative, the like-for-like comparison is the preregistered verdict with J1 included: it caught .623 (AAL) and .600 (Desikan–Killiany) of the same plants at α = .05, against .666 and .585 for the adopted max test at α = .025.  Its non-adoption is a gate outcome under the frozen rule, not a choice. J1 was not computed on the expression-aligned null families (declared in amendment 3), so its false-alarm rate where the max test was stressed is unknown. 

The failure grows with module size. In AAL, the coexpression-matched null rejected .159, .196 and .287 of coherent modules at m = 10, 25 and 100 (rejection at .05; descriptors, not gates). 

## 3.4 The failure holds in Cao et al.'s own regime and scales with coherence

The regime-boundary probe passed all its planted checks, including the reproduction of Cao et al.'s calibrated cell.  Its readouts locate the failure (Figure 3).

**Not aggregation.** At matched sidedness, the Mean and t-type statistics failed together under our coexpression-matched null. In the registered cell (tight modules, smooth maps, three expression spaces, m = 25 and 100), one-sided rejection rates were .1904–.2802 (Mean) and .1926–.2820 (t-type). 

**Not smooth maps.** Cao et al.'s near-noise maps and smooth fields gave similar rates (for example .2331 against .2122, Cao's space, m = 25, t-type).  On 34 parcels, however, the smooth fields were only mildly smoother than the near-noise maps (median Moran's I .056 against .025), so this contrast is weak. 

**Coherence.** The rejection rate rose with a set's mean pairwise coexpression. Every one of the 25 coherence fits that crossed .05 inside the observed data did so at a mean coexpression of .04 or below; the other 59 crossed below the data. 

**Cao et al.'s own sampler.** Their rejection sampler accepted none of the tight modules in any space or size.  Where it did match published-like sets, it was anticonservative for Meanabs in every cell (for example .1435–.1931 in Cao's space).  Its two-sided Mean cells at m = 25 in Cao's own space were indeterminate, at .0598 and .0605. 

So the coexpression-matched gene null [@wei2022statisticaltesting; @cao2024unraveling] is anticonservative for coherent gene sets in Cao et al.'s own calibration regime, above the fitted coherence crossing for published-like sets. Their calibration on random sets is correct for random sets and does not extend to coherent ones.

## 3.5 The max test: calibration

The max test was gated on the expression-aligned null family across three classes and the cortex-only replica (Figure 4, left).

- **Gene-side leg alone.** All 372 false-alarm strata passed; the largest rate was .022 (step strata ≤ .036). 
- **Full verdict, expression-aligned families.** All 372 strata passed; largest rate .019 (step strata ≤ .024). 
- **Full verdict, original null families.** All 18 strata passed; largest rate .004. 

In total, the full rule is at or below .019 in all 390 verdict strata (372 expression-aligned + 18 original), and the gene-side leg alone is at or below .022 in 372 more. 

Rates are k / 1,000 per stratum, and plants whose gene-side leg was blocked (its spectral null uninformative or resolution-limited) count as non-rejections in that denominator. There were 3,980 such plants across the 372 expression-aligned strata, up to 116 per 1,000 in one stratum (and 65 across the 18 original strata, up to 15 per 500). With them excluded from the denominator (k / (1,000 − blocked)), the worst-case rates are .020 for the full rule (19 / 964) and .022 for the gene-side leg alone (20 / 906); every stratum stays below .025. 

We call the rule "calibrated on every informative planted stratum, within stated scope limits", with four qualifications:

1. Coordinate-gradient targets did not stress the gene-side leg in AAL and CC200: the map-side leg fired on them at only .028 and .036. There the map-side leg bounds the verdict at those rates. 
2. In CC200, the brain-enrichment plant did not produce the confound it was built to produce (reference leg .023), so that confound is untested there. 
3. The 18 original-family strata cannot fail by construction; they are kept as checks. 
4. On the cortex-only replica, two reference tests known to be fooled by the planted confounds rejected at .150 and .131 (threshold > .05), so the plants did exercise those confounds there. 

These qualifications are carried into the audit as scope labels on the claims they affect. 

## 3.6 The max test: power and its price

**Table 2. Verdict catch rates at α = .025 (registered descriptors).**

| planted signal | a | AAL | Desikan–Killiany |
|---|---|---|---|
| spatial | .3 / .6 / .9 | .047 / .323 / .970 | .047 / .433 / .970 |
| gene-specific | .3 / .6 / .9 | .073 / .415 / .666 | .064 / .284 / .585 |
| expression-aligned | .3 / .5 / .7 | range over both classes and three set kinds: .018–.074 / .060–.196 / .106–.352 | |

Where the power goes (Figure 4, right):

- **Gene-specific signal, AAL.** The parametric leg binds: .709, against .959 for the map-side leg and .922 for the gene-side leg; verdict .666.
- **Gene-specific signal, Desikan–Killiany.** Every leg loses a little (.766 / .813 / .736) and the conjunction compounds it; verdict .585. 
- **Expression-aligned signal, a = .7.** The gene-side leg binds in 5 of 6 class × set-kind cells (.234–.434, against .438–.724 for the map-side leg and .230–.590 for the parametric leg); in the sixth (AAL, brain-fraction-matched random sets of 100 genes) the parametric leg binds (.230 against .254 for the gene-side leg). 

Relative to the class-stratified map-side leg alone, the full rule costs 28–31 % of gene-specific catch at a = .9, 43–83 % of expression-aligned power at a = .7, and at most 3 % on spatial signal at a = .9. 

Against the preregistered sequential cascade at α = .05, gene-specific catch at a = .9 moved from .627 to .666 in AAL and from .610 to .585 in Desikan–Killiany. The two are not directly comparable: the α levels differ (.05 against .025) and so do the denominators (300 against 296 and 299, after excluding plants the matched null could not serve). 

## 3.7 The stop rule, as it fired

The preregistered stop rule fired three times; we report each as it happened (Figure 2 and Figure 4 show the gates).

1. **The single-gene control** (Section 3.1). Resolved by demoting it to reproduction-only (amendment 2, post hoc). 
2. **The first gate battery**, with 19 evaluated failures: nine gene-null false-alarm gates (coexpression-matched, brain-background coexpression-matched and trajectory-matched, in each class), three matching-limit failures (more than 5 % of plants in a generator cell without a matched null set), five gene-catch gates, and two plant-active gates (the uniform gene null on coherent modules, .094 and .085 against a threshold of .10 in AAL and Desikan–Killiany). Two preregistered adoption rules acted beside the stop rule. The joint spatial pair failed its gates and the class-stratified pair was adopted in its place; J1 passed all six false-alarm gates (.024–.041 at α = .05) but failed its AAL catch gate on the matching limit (catch .986 AAL, .910 Desikan–Killiany), so it was not adopted (Section 3.3). Neither adoption outcome fired the stop rule, and neither was a choice. Resolved by amendment 3, which adopted the max test and dropped that plant-active gate (post hoc; its frozen failure is reported here). 
3. **The max test's own gates**, with 11 hard failures: two gene-specific catch gates, six expression-aligned power gates, two plant-active gates and one planted-confound gate. No false-alarm gate failed. Resolved by amendment 5, which made catch and power registered descriptors and turned the three untested plant families into scope labels (post hoc). 

Under amendment 5 the stop rule did not fire: 789 retained gates passed. 

# 4 Results — the audit as a worked demonstration

## 4.1 Interim headline

Interim (first two release batches): 0 of the 16 frozen-11 population units survive (0 / 16), and 1 of the 16 could be tested with the full verdict; the third batch's 196 population units have not run and are counted neither way, and the rows of Dear et al. [@dear2024corticalgene] (3 rows) and Vairam, Roy et al. [@vairam2026hyperhypo] (preprint; 6 rows) are deferred.  This is an interim figure for a partial audit. It is not an estimate of how often published autism imaging-transcriptomic claims hold.

**Table 3. Composition of the 16 population units** (Figure 5). "As registered" is each unit's category in the frozen register; "at use" is its category after the preregistered run-time checks (reproduction of the published statistic, matching of region labels).

| category | at use | as registered |
|---|---|---|
| tested (full verdict) | 1 | 3 |
| no calibrated test | 2 | 4 |
| not testable as stated | 6 | 6 |
| not auditable | 7 | 5 |

As registered, the categories cover 18 units, including the two later removed (below).

Four units changed category at use:

- Two of the three full-verdict claims (Patel et al. [@patel2021virtual], claims 1 and 2) left the population because our reconstruction did not reproduce the published statistic, as the preregistered reproduction check requires.
- Two claims of Liu et al. [@liu2026spatiotemporal] became not auditable because the published region labels could not be matched to the atlas.

## 4.2 The one tested claim

The remaining full-verdict claim (Patel et al., claim 3) received the full verdict and did not survive. The parametric and map-side legs rejected (p = 3.077e-07 and .0005), but the gene-side leg did not (p = .06909), and its gene-side spectral null was flagged uninformative (dominant-component share .8208 > .8). Its reading is therefore the status "uninformative", not "not detectable at this power". No unit could have survived here: an uninformative gene-side null blocks survival whatever the p-values, and the claim was analysed on the cortex-only replica (34 left cortical parcels), where false alarms were gated but power was not measured (power was measured in AAL and Desikan–Killiany only).  The tested-only fraction is 0 / 1. 

No unit was component-level in form and auditable; no survival exists to carry a "calibrated evidence" or "calibration extrapolated" reading. 

## 4.3 Descriptors beside the headline

Across the frozen 11 and the nine added targets, the register holds 333 claims; 31 have received a verdict, none survives, and 226 have not yet run. 

The 31 claims that have received a verdict come from three papers and cluster in one: 27 are from Leyhausen et al. [@leyhausen2024intrinsic], an added target. For 30 of the 31, power was not measured in the claim's class. 

**Table 4. Claims with a verdict, by paper.**

| paper | register | paper's own inference level | with a verdict | survive | reading | power in the claim's class |
|---|---|---|---|---|---|---|
| Leyhausen et al. | added target | gene null only (uniform) | 27 | 0 | 27 not detectable at this power | not measured (cortex-only replica; nor at the claim's set size) |
| Patel et al. | frozen 11 | gene null only (uniform) | 3 | 0 | 2 not detectable at this power (claims 1–2, later out of the population as not reproduced); 1 uninformative (claim 3) | not measured (cortex-only replica) |
| Hansen et al. [@hansen2022local] | added target | none | 1 | 0 | does not pass at component level | not applicable (fixed expression component, no gene set) |

*Note.* Of the 27 Leyhausen claims, 24 also carry the scope label "brain-enrichment confound untested" and 8 "gene-side leg untested (gradient)". The register run so far has 42 verdict-bearing rows across all cell classes; 11 are not claims (spatial null only 8, none 1, other 2), so Table 4 counts the 31 claims only (class definition: `arcs/audit/src/a1_audit/report_cells.py:1667-1686`). 

Benjamini–Hochberg q-values were computed over an interim family of 30 rows as descriptors; final q-values wait for the third batch. 

Every non-surviving claim without a status flag reads "not detectable at this power". None is evidence against the published claim, and for 30 of the 31 claims power was not measured in the claim's class.

# 5 Discussion

## 5.1 What the planted truths show

The two defences in current use each fail in a regime that published claims occupy. Joint spatial surrogates are anticonservative when tissue classes differ in mean, a common feature of volumetric maps that span cortex and subcortex. Coexpression-matched gene nulls are anticonservative for coherent gene sets, and the failure scales with coherence. The second result holds in Cao et al.'s own calibration regime — their matrix, near-noise maps and statistics — so it is not an artefact of our processing or of smooth maps. Their recommendation is sound for the random sets on which it was calibrated [@cao2024unraveling].

We do not claim that random-gene nulls are inflated by coexpression [@fulcher2021overcoming], or that spatial nulls are inflated on smooth fields [@markello2021comparing]; both are established. Requiring both nulls is not new either [@wei2022statisticaltesting; @hillman2026netdom; @lariviere2022epilepsy; @schenetti2026enrichment], nor are intersection–union tests in neuroimaging [@nichols2005conjunction; @winkler2016npc]. Randomising phenotypes within anatomical divisions was suggested by Fulcher et al. [@fulcher2021overcoming]. What is new here is quantitative: the class-step failure of joint surrogates and the calibration of class-stratified ones; the coherence regime in which the coexpression-matched null fails; and planted-positive catch rates for imaging-transcriptomic gene-set nulls, which we have not found in prior work.

## 5.2 A fourth-corner fix, and its price

We recast the field's two-null practice as the fourth-corner problem and adopted its max-test solution with constraints on both legs. The gene-side leg adds a gene-side Moran spectral randomisation — to our knowledge its first use in gene-set testing — and the rule is, to our knowledge, the first such rule calibrated on planted null families built so that one leg alone is fooled and the other must hold. The α/2 level is borrowed from ter Braak et al. [@terbraak2017glm], whose correction was designed for far fewer units per side than our 15,633 genes; here it rests on the planted calibration alone.

The rule is calibrated on every informative planted stratum, within stated scope limits (Section 3.5). Calibration costs power. At α = .025, strong gene-specific signals (a = .9) are caught at .585 (Desikan–Killiany) and .666 (AAL); expression-aligned signals at a = .7 at .106–.352 (AAL and Desikan–Killiany). The preregistered verdict with its additional Level-3 null J1 would have caught .623 (AAL) and .600 (Desikan–Killiany) of the same strong signals at α = .05, no more than the max test; J1 was not adopted under its frozen gate (Section 3.3) and was never tested on the expression-aligned null families.  A survival under this rule is therefore informative; a non-survival is weak evidence of anything, which is why the audit reads non-survival as "not detectable at this power".

## 5.3 Limitations

**Post-hoc amendments.** Five of the seven amendments were written after results were seen: three changed the design (2, 3, 5), two the reporting (6, 7). The design changes were the demotion of the single-gene control (2), the adoption of the max test with α/2 (3), and the move of catch and power from gates to descriptors (5). Each is declared as post hoc in its own text, with the frozen failure it answered reported beside it (Table 1; Section 3.7). The test was not changed a third time after its behaviour was seen. Amendment 6 fixed the headline rule for the full audit after the interim audit result; amendment 7 split reporting between this paper and the full audit after that result and before the third batch. 

**The stop rule fired three times.** We report each firing and its resolution as they happened, not as a clean pipeline. A reader who discounts post-hoc resolutions should read Section 3 as a measurement of failure modes, which needs no resolution.

**The single-gene control is unresolved.** The APOE × Alzheimer control reproduced the published slope within the preregistered band but not exactly (0.679 against 0.631). Our map was resampled from a public meta-analysis map rather than the authors' coregistered input. The cause of the unexpected gene-null rejection is not established. 

**Scope.** Expression comes from six adult post-mortem donors. Calibration is measured in three volumetric classes and one cortical replica; outside them, and outside 25 ≤ m ≤ 1,000, a survival would read "calibration extrapolated". Coordinate-gradient plants did not stress the gene-side leg in two classes, and the brain-enrichment confound is untested in CC200.

**The audit is partial.** Only 1 of 16 population units could be tested with the full verdict, the third batch (196 units) has not run, and 9 rows (Dear et al., 3; Vairam, Roy et al., 6) are deferred. The third release batch is reported in a follow-up and cannot change any number in this paper. 

**Exposure.** The register lists everything seen before the protocol was frozen. This includes published values of the audited papers, a literature note that recomputed correlations on the ENIGMA-ASD map shared by several targets, our reproduction of Giacomel et al.'s statistics, an exploratory analysis of ABIDE I, and incidents in which material was fetched or inspected and then deleted unused. 

**Preregistration timestamps.** Freeze hashes are listed in the deposited `FROZEN.txt`, and freeze times were recorded in the project's private version history. The protocol was not registered with a third party before analysis, so the deposit's own date is its first public timestamp. The preregistration and all amendments are deposited at https://doi.org/10.5281/zenodo.24130310.

## 5.4 Recommendations

1. Report which null each leg uses, and its calibration in the coherence and tissue-class regime of the claim at hand.
2. For volumetric maps spanning tissue classes, generate spatial surrogates within class.
3. Do not rely on coexpression-matched sampling for coherent sets; report the set's mean coexpression beside its gene-null p.
4. Where both nulls are required, combine them as a max test and calibrate the combination with planted pairs, including signals aligned with dominant expression gradients.
5. Report power on planted positives beside every non-survival.

# 6 Data and code availability

Code, frozen protocol and amendments, the claims register, result files and figure scripts are available at https://github.com/inventorado/planted-truth-nulls, archived at https://doi.org/10.5281/zenodo.24130310. The Allen Human Brain Atlas is public. No individual-level data were used, and no controlled-access data were requested or accessed. The instrument analyses use public expression data and simulated maps. Audit inputs are group-level maps and gene lists as published by their authors and openly downloadable (journal supplements, NeuroVault, GitHub/Zenodo), named in the register; some summarise cohorts whose individual-level data are access-controlled (EU-AIMS LEAP) or registration-only (ABIDE, via ENIGMA-ASD). One public supplement (Pretzsch et al., Supplement 2) also contains per-participant LEAP tables. Only its group-level loadings were extracted, the per-participant sheets were inspected by header only and never used, and the file was then deleted.

**Use of AI tools.** The analysis code, documentation and manuscript text were developed with the assistance of a large language model (Claude, Anthropic), working under the author's direction. Every number reported comes from code that was run and can be traced to a result file in the deposit; no statistic was supplied by the model. The author reviewed the text and takes responsibility for it.

# Figures

**Figure 1.** Schematic. A brain map (parcels × value) and a gene set (genes × parcels) meet in a set-versus-map statistic. The map-side leg randomises the map within tissue class; the gene-side leg randomises the set with the map held fixed. The fourth-corner max test rejects only if both legs and the parametric test reject at α = .025. (figures/fig1)

**Figure 2.** False-alarm rate by null, parcellation class and class step. Joint spatial surrogates exceed nominal at a class step in every stratum; class-stratified surrogates stay nominal; coexpression-matched gene nulls exceed nominal on coherent modules in every class. (figures/fig2)

**Figure 3.** Rejection rate against gene-set coherence across expression spaces, under the coexpression-matched null, with Cao et al.'s calibrated cell (random sets, near-noise maps) marked. (figures/fig3)

**Figure 4.** Left: the calibration map of the max test over 390 verdict strata and 372 gene-side-leg strata, with the scope-labelled strata marked. Right: catch and power curves for spatial, gene-specific and expression-aligned signals, with each leg's rate and the cost relative to the map-side leg alone. (figures/fig4)

**Figure 5.** Interim audit (first two release batches): composition of the 16 population units by category, beside the third batch (196 units, not run) and the deferred rows. (figures/fig5)

# References

::: {#refs}
:::
