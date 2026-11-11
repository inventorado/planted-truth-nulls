# PREREG AMENDMENT 3 — A1 `audit`: the verdict becomes an explicit fourth-corner max test (operator option d)

**v3.1 — the frozen version** (`bench.py freeze`; hash in `FROZEN.txt`). v1 and v2 were refuted by adversarial
reviews (asdg-skeptic, 2026-09-23; v1: 5 A / 11 B / 3 C findings; v2: 2 A / 9 B / 6 C new findings, 10 of v1's
resolved). v3 answered every open finding and recorded the operator's decisions. A verification pass restricted to the
v3 fixes found no A-level problem; it listed nine code/text mismatches, two incomplete text items (§0's exposure list,
§1's brain fraction) and A2's open part (pool diversity). v3.1 fixes them and was re-verified (verified; change log
§7). Amends `prereg.md` (FROZEN, sha256 a632b852…) §4.3–4.7, §6.2–6.4 and §9, as amended by `prereg_amend_1.md` and
`prereg_amend_2.md`. Everything not named here is unchanged.

## 0. Status, post-hoc elements and pre-freeze exposure (declared)
Written 2026-09-23 **after** the complete E3 battery was gated (`results/e3_gates.json` @d1043f0: K1 fired, 19 evaluated
failures). The operator chose option (d) of `ARC.md` session 3.
- **Post hoc** (decided after the battery's results were seen; reported as such in every output): the verdict change
  (§2); the demotion of the per-null gene gates (G2, G4, G5, Level 2) to descriptors; dropping the plant-active G1 gate
  (operator; its frozen failure .094 / .085 < .10 is reported in every output); the verdict threshold α/2 (operator);
  the selected-list rule (§2; operator; it repairs a hole in the frozen §4.7); treating BH below .025 as uncertified
  (operator); the partial-certification rule (§5; operator).
- **Registered before computation**: the species randomisations (§3), the plant families (§4), gates and thresholds
  (§5), and two compute decisions of the operator taken when the v3 compute estimate proved ≈ 3× too low (§6):
  G6l's window sums accumulated in float32 (§3) and the F-align maps paired across w (§4). When this file is frozen no
  G3m / G6s / G6l p-value and no F-align or C-align plant exists.
- **Pre-freeze exposure**: (i) C3 (`results/e3_c3_gradients.json`): the adopted stratified site leg rejects .10–.125 of
  sets against V-DK's A–P / I–S gradients. (ii) Non-citable exploration results used as design rationale only:
  `explore/discovery/FINDINGS.md` F-X4 (its null was within-site diagnosis permutation) and the mechanism probe
  (`explore/e3_mechanism/`). (iii) The three reviews (v1, v2, and the v3 verification pass) computed, on AHBA, public
  lists and synthetic data only — never a brain map from the plants, a plant file, a gate or a G3m/G6s/G6l p-value on
  plants: the share of random-set scores
  carried by the gene-mean profile and its component spread; PC1's R² on tissue class (.91–.97) and the gene-mean
  profile's (.25–.63); within-cortex gene-mean profile vs A–P / I–S / |x| and cortical PC1 vs A–P (.62–.76); Moran's I
  of G6s copies; the c(g, o) in-band interval counts; seed windows' between-class share, gene-mean content, dominant-
  axis alignment, pool diversity (incl. windows matched to published lists and at F-mod coherence); eligible-seed
  fractions and per-seed cost; k-means modules with the reviewers' own seeds; whole and within-class coherence of the
  rand / fill / clus populations; size, within-class coherence, gene-mean and brain-profile content of 10 public lists
  (Seidlitz 2020 classes; Velmeshev 2019 ASD DEGs incl. L2/3, AST-PP); the brain-enrichment profile d_B = μ_B^w − μ^w
  of the GAMBA brain>body background (its component spread, PC1_w alignment, and content in brain-background random
  sets, universe sets, windows and public lists); C-align signal-share descriptors; toy G6s rejection rates on
  synthetic maps; exact binomial pass probabilities; the norm of s_W among G6s copies and the copies' between/within
  energy split (observed vs copies, public lists and random sets); the offset between the cluster-uniform and
  gene-uniform mean within-class profiles (4.5 % of module deviations); and, in the verification pass, the toy unit
  tests and the gates' self-test, the registered module generator's cluster sizes on the 34-parcel replica (103–486
  genes, median 219; 21 clusters ≥ 250, 60 ≥ 125, 64 ≥ 100) and the within-class coherence q10/q50/q90 of brand and
  multi sets in V-DK, V-AAL and the replica (the reviewer's own k-means seeds); and, in the re-verification of v3.1,
  the toy unit tests and self-test again, read-only arithmetic on `results/a3_design_eligibility.json`, and G6l pools
  (`species.g6l_null`, K = 200, no map, no p-value) for 3 sets each of clus-100, brand-500, multi-500 and multi-1,000
  in V-DK, the replica and V-AAL (the reviewer's own k-means seeds; mean pairwise Jaccard .003–.044). (iv) The
  orchestrator, on AHBA only:
  the registered module generator's cluster sizes per class (median 210–243 genes; 21–31 clusters of ≥ 250 per class,
  so multi-1,000 is drawable); G6l's eligible-seed fraction, per-draw cost and the float32 window sums' error against
  float64, per atlas × registered set kind (12 sets × 300 seeds each, float64 recomputed on 10 of them;
  `arcs/audit/src/a3_design_eligibility.py`, `results/a3_design_eligibility.json`; its first run, with the v3 loop,
  `results/a3_design_eligibility_v3loop.log`), which fixed the plants' seed budget and the float32 tolerance (§3);
  synthetic benchmarks of the window loop and a toy smoke test of the paired plant path on a synthetic atlas
  (`one_plant` for every family; no real data); and toy-data unit tests of the
  species leg (`src/tests/test_species.py`: the v1 G6s flaw 0.987 vs 0.007 after centring; the v2 species max fooled by
  a synthetic brain profile at 0.325 vs 0.013 for v3), rerun after the v3.1 changes (12 tests; the original eight
  reproduce their numbers exactly) with the gates' self-test (25 planted cases).

## 1. Why
- The frozen design gated every gene null separately. The coexpression-matched nulls collapse for coherent sets
  (G2 .20–.21, G4 .40–.44 on F-mod) and G5 cannot match coherent sets half the time.
- The set-versus-map test is ecology's fourth-corner problem. An **intersection–union max test** controls type I error
  in a null scenario when the leg protecting that scenario is valid there (Dray & Legendre 2008; ter Braak et al. 2012;
  Braga et al. 2018) — robustly, not exactly (inflation .066–.11 with correlated structure on both sides; ter Braak 2017,
  2018, 2026), hence α/2.
- The tissue-class contrast is expression PC1 here (R² .91–.97). The adopted class-stratified site leg conditions the
  **between-class** alignment out. The unprotected regime is **within-class** alignment (C3). Two confounds live there
  that a species leg must absorb: a set's share of the gene-mean profile, and a set's **brain-expressed enrichment**
  (the GAMBA confound, Wei 2022, which the frozen G3 guarded against: the public lists checked span 4–59 % brain>body
  genes, the DEG and neuronal lists 40–53 %, against 16 % in the universe).

## 2. The verdict (replaces §4.6's survival rule; post hoc)
For a claim (map y, set S, statistic T of §4 / §4.7, registered direction), with α_v = .025:
- **Level 0**: parametric p of T. **Site leg**: p_site = max(p_S1c, p_S2c), the adopted class-stratified pair.
- **Species leg**: p_species = max(p_G1, p_G3m, p_G6s, p_G6l) (§3), same statistic, y fixed.
- A claim **survives iff p_L0, p_site and p_species are each < .025**; conjunction p = max. The certified result is the
  per-claim verdict at .025. Benjamini–Hochberg q-values (on the conjunction p) are **reported as descriptive**: the
  plants calibrate the verdict at .025 only, so FDR control below that level is not certified (operator decision).
- **Null hypotheses.** H0_site: S's association with y is no larger than on maps with y's within-class spatial
  autocorrelation and y's class means. H0_G1: S is exchangeable with uniformly random sets of its size. H0_G3m: S is
  exchangeable with random sets of its size and its count of brain>body genes. H0_G6s: S's within-class deviation from
  its brain-fraction-matched expected profile has sign-exchangeable coordinates on the within-class expression
  components. H0_G6l: S is exchangeable with seed-anchored windows of its size and within-class coherence. The verdict
  rejects only if every leg rejects (it tests against the union of these).
- **Conditioning.** Every species null set R is evaluated as s_B(S) + s_W(R): S's between-class part replaces R's, the
  same conditioning as the site leg and G6s.
- **Species leg uninformative**: with a_k, b_k the coordinates of y's and S's within-class deviations on the within-
  class components (§3) and w_k = |a_k b_k|, if max_k w_k / Σ_k w_k > .8 G6s's null is ±T; the claim is labelled "species
  leg uninformative" (cannot survive; reported apart). Applied identically to plants and audit: in every false-alarm
  gate (species-leg gates included) such a plant stays in the denominator as a non-rejection; in catch and power gates
  it is a miss; counts reported per gate.
- **Resolution.** A randomisation with fewer distinct null states than draws is enumerated exactly: G6l over eligible
  seeds, (k' + 1)/(N_elig + 1); G6s over all 2^rank sign patterns when 2^rank ≤ K; S2c likewise (2^(n−1) patterns).
  A leg with N null states has the smallest attainable p 1/(N + 1) (2/(N + 1) for exact G6s, whose enumeration
  contains the identity pattern); a claim whose largest leg floor is not below .025 is "resolution-limited" (cannot
  survive; reported apart; a non-rejection in plants, as above). In the plant battery no leg can bind (K = 200 and 500
  surrogates; G6l ≥ 50 accepted windows, floor ≤ .0196; every MSR stratum has ≥ 10 parcels, so ≥ 2^9 = 512 > 500 sign
  patterns); the species legs' label is computed and counted in plants (`species.py`). S2c exact enumeration and the
  verdict-level label are implemented in the audit code, with toy tests, before any claim is evaluated (§6).
- Unmatched or degenerate species randomisation (§3) → the claim cannot survive (the §4.3 convention). Level 2 (G1–G5),
  J1, the naive joint null and each species leg's own p are reported for every claim as descriptors.
- **Lists selected on imaging data** (operator decision): a set or ranking derived from any imaging map whose sample
  overlaps the claim map's sample, or of the same phenotype (e.g. a top-N list from the authors' PLS), is tested at
  component level — Levels 0–1 with the PLS refit **and the list re-selected on every permutation and surrogate** — and
  a surviving such claim is labelled "map–expression link, not set specificity". The claims register (§5.2) records
  each list's provenance. This repairs the frozen §4.7 ranking-only rule (survival probability ≈ 1 there).
- **Enrichment claims** (§4.7): the species leg acts on the z-scored set score (cascade.pls1): G6s on the within-class,
  gene-side-centred z-scored matrix; G1, G3m and G6l recompute each null set's mean PLS1 weight, weights and y fixed.

## 3. The species leg (registered)
Notation: X = the class's analysis-parcel expression (parcels × genes; §3.1 matrices); tissue class per parcel (§2);
B = the GAMBA brain>body background ∩ the universe (as the frozen G3; conflicting duplicates dropped).
X^w = X with every gene demeaned within each tissue class; μ^w = mean of X^w over all genes; μ_B^w, μ_N^w = its mean over
genes in B and not in B; X^wd = X^w − μ^w 1ᵀ = UΣVᵀ (within-class, gene-side centred).
For S (size m, f = |S ∩ B|): s = Xt/m = s_B + s_W (class means + within-class part);
μ_S = (f/m) μ_B^w + (1 − f/m) μ_N^w (S's brain-fraction-matched expected within-class profile); b = Uᵀ(s_W − μ_S).
- **G1**: uniform random sets from the universe minus S. K = 10,000 (audit), 200 (plants).
- **G3m — brain-fraction-matched random sets**: f genes uniform from B \ S and m − f uniform from the rest minus S.
  K as G1.
- **G6s — within-class gene-side Moran spectral randomisation, exact spectrum, brain-fraction centred.**
  s* = s_B + μ_S + U(ε ⊙ b), ε_k = ±1 i.i.d.; T* = T(y, s*). Preserves ‖s_W − μ_S‖ and every |b_k| (a covariance-based
  spectrum; the null "traits" are continuous, not gene sets). K as G1 (exact enumeration per §2 when 2^rank ≤ K).
- **G6l — within-class seed-anchored windows.** Within-class coexpression = Pearson r of genes over parcels on X^w;
  c_S = S's mean pairwise within-class coexpression. For a seed g ∉ S: genes not in S ∪ {g} ranked by within-class
  coexpression with g (recomputed per claim, S removed); window W(o) = {g} ∪ the m − 1 consecutive genes at offset o,
  o ∈ [0, half the ranking]; O_g = {o : |c(W(o)) − c_S| ≤ .02}; g eligible iff O_g ≠ ∅. Rankings are computed in float64;
  window sums are accumulated in float32 (operator, compute; over 6,720 sampled AHBA seed curves the largest observed
  difference from float64 is 2.4e-5, the rankings are identical, and 157 of 51.7 million in-band decisions differ,
  each necessarily within that difference of the band edge; §0 (iv)). Null set: eligible seed (uniform,
  without replacement), o uniform over O_g. Plants: seeds screened in random order until K = 200 are accepted, with a
  budget of 5·K = 1,000 seed draws; audit: every gene screened, exact enumeration if N_elig < K = 10,000. Fewer than 50
  eligible seeds → "unmatched". The budget does not bind at the registered set kinds: the eligible fraction is ≥ .49
  for every one of 672 sets drawn by the registered generator (12 per atlas × kind, 300 seeds each; median ≥ .85 in
  every cell; §0 (iv)), so a plant is unmatched only below 5 % eligibility, the audit only below 0.32 %.
  **Pool diversity** (the frozen J1 rule, `prereg.md` §4.4): a pool whose mean pairwise Jaccard overlap is ≥ .5 is
  "degenerate" — the claim cannot survive, and in plants it counts as unmatched. Reported per claim, not required:
  N_elig and the eligible fraction of the seeds screened; the pool's mean pairwise Jaccard; the pool seeds' tissue-class
  make-up = their mean between-class share of expression variance (the variance of a gene's class means over its total
  variance across parcels), beside the universe mean; the signed and |r| pool score coherence; the S–pool correlation.

## 4. Plant families (registered; `arcs/audit/src/e3_align_plants.py`)
Fields: the §6.1 generators, plant i → generator cell i mod 10. Site-leg surrogates: S1c and S2c, 500 each, per map
(shared across the set kinds evaluated on it). **Module generator** (independent of every species null): spherical
k-means of z-scored gene profiles over the class's analysis parcels (whole expression), k = 64, 20 restarts, 100
iterations, seed 20260924 + class id (aal 1, dk 2, cc200 3). Clusters are drawn uniformly over clusters large enough for
the draw; S's clusters ≠ the target's cluster. PC sign: corr(PC score, mean expression over genes) > 0.
- **F-align (scenario B).** y_w = w·z(target) + √(1 − w²)·z(field), w ∈ {.5, .9}, each w gated separately. The two w
  are **paired** (operator, compute): plant i's two maps share its generator cell, field, target, every set and every
  species null draw (common random numbers); only the site leg's surrogates are drawn per map. Each w stratum is
  still 1,000 independent plants; the two strata are dependent on each other, which no gate uses. S is never
  drawn from the target's programme (the generator's null); H0_G1 holds exactly only for rand, H0_G3m for rand and brand;
  the gates certify the species **max** under the generator's null, not each leg under its own H0.
  - Targets: **T-wmod** = a module's score — the mean expression profile of **all** genes of one cluster, drawn
    uniformly over clusters of ≥ 25 genes — demeaned within class; **T-grad** = MNI y (A–P, even i) or MNI z (I–S, odd
    i) demeaned within class (conditional scope: these two orientations only); **T-mod** = the same module score,
    undemeaned; **T-brain** = the brain-enrichment profile d_B = μ_B^w − μ^w (fixed per class; the GAMBA mirror null).
  - Set kinds (14): **rand** (uniform) m = 25 / 100 / 300; **brand** (f = round(.45 m) genes from B, the rest from the
    others; published-like brain fraction) m = 25 / 100 / 300 / 500; **fill** (a core of ⌈m/5⌉ members of one cluster plus
    uniform filler) m = 25 / 100 / 300; **clus** (m members of one cluster) m = 25 / 100; **multi** (equal parts of 4
    random clusters' members, S never from the target's cluster) m = 500 / 1,000.
  - Cells: 3 classes (V-AAL, V-DK, V-CC200) × {T-wmod, T-grad, T-mod} × 2 w × 14 kinds, plus T-brain × 2 w × {rand-100,
    rand-300, brand-25, brand-100, brand-300, brand-500, multi-500, fill-100}; n = 1,000 plants per class × target, each
    giving one map per w (every kind of that target evaluated on each map). **Cortex-only replica** (single-class maps,
    as ENIGMA-ASD thickness): V-DK left cortex (34 parcels, one class, so "within-class" = whole cortex; its k-means
    modules are computed on those 34 parcels with the V-DK seed), targets {T-mod, T-grad, T-brain} × 2 w × the same
    kinds, n = 1,000 plants per target, paired across w.
  - Descriptor cells (class-step checks, not gated): targets PC1 and PC2 of X (tissue-class contrasts, which the site leg
    and G6s condition out), n = 200 plants per class × target (paired across w) × {rand-25, clus-25}.
- **C-align (power in scenario B; gated).** y = a·z(ẽ_S) + .6·z(T-wmod target) + c·z(field), a ∈ {.3, .5, .7},
  c = √(1 − a² − .36); ẽ_S = (s_W − μ_S) residualised on the first three within-class components (the S-specific part;
  the shared profile excluded); S = rand-25, fill-100 and brand-100; V-AAL and V-DK; n = 500 per cell (unpaired
  across a).
- Per plant × set kind: naive, S1c, S2c, G1, G3m, G6s, G6l and the verdict with its status (ok, G6l unmatched or
  degenerate, uninformative, resolution-limited; §2); descriptors: each leg's p, the uninformative share, the species
  legs' floor, G6l's pool descriptors (§3), and two **reference legs that are not valid nulls** (§5 planted legs):
  G6s-v1 (v1 draft: un-centred whole-expression sign flips), on every plant, and the v2 species max (G1, universe-
  centred G6s, G6l — no brain matching), on T-brain plants only, where its G6l rescores the claim's own v3 windows
  unconditioned. G2–G5, J1 and the joint Level-1 pair are not computed for the new families (declared).
- The existing 27 cells get G3m, G6s and G6l by deterministic replay of each plant's S and y (every plant's saved r and
  p_G2 asserted); nothing else of them is recomputed.

## 5. Gates (replace the gene-level gates of §6.4; the spatial adoption of §6.4 stands)
Rates at the verdict threshold .025 unless stated. Every gate computed here (plant-active: every kind) reports its
k / n, its class-step strata (step 0 and step 1 of §6.1), its ten generator cells, and its unmatched, degenerate,
uninformative and resolution-limited counts; the carried frozen gates (naive plant-active, P+1, P+2) as recorded.
- **Species-leg false alarm** (rate of p_species < .025): every F-align and cortex-only stratum (class × target × w ×
  kind); passes iff rate ≤ .05. Computed plants only (uninformative or resolution-limited plants stay in the
  denominator as non-rejections); > 5 % unmatched or degenerate in any generator cell fails the gate.
- **Verdict false alarm** (conjunction < .025): the same strata, and F-sp / F-mod / F-traj per class and step stratum;
  passes iff rate ≤ .05. All plants in the denominator; unmatched, degenerate, uninformative or resolution-limited =
  non-rejection.
  The F-family gates cannot fail (the verdict rejects only where the adopted site leg rejects at .025); kept as checks.
- **Verdict catch**: rate ≥ .80 at a = .9 on C-sp and C-gene, V-AAL and V-DK (existing plants; denominator = computed
  plants as frozen; any status other than ok = a miss). Each leg's own catch rate is reported beside it.
- **Power in scenario B**: verdict catch ≥ .50 at a = .7 on C-align, per class × set kind (6 gates; any status other
  than ok = a miss).
- **Plant-active** (the within-class mirror null must be real): per class × target (T-wmod, T-grad, T-brain; and the
  cortex-only replica's targets) at w = .9, the **maximum over set kinds** of the site leg's rate at .025 must be ≥ .05
  (each kind has 1,000 independent maps). Every kind's site-leg rate is reported, and T-mod's in V-AAL, V-DK and
  V-CC200 (not gated). Stated in advance: a target family whose maximum is below .05 does not stress the species leg;
  its species gates are uninformative and K1 fires — in the cortex-only replica too.
  Naive Level 0 on F-sp ≥ .15 per class (unchanged, frozen threshold .05).
- **Planted legs the species-leg gate must catch** (else the gate is untested and K1 fires): (a) naive Level 0 must
  exceed .05 on rand-25 × T-wmod × w = .5 in every class; (b) G6s-v1 must exceed .05 pooled over T-mod × {rand-100,
  rand-300} × w = .9 in V-DK and in V-CC200 (reported, not required, in V-AAL, where its flaw sits mostly on one
  component); (c) the v2 species max must exceed .05 on T-brain × brand-300 × w = .9 in every class (the N1 confound).
  A reference leg that passes elsewhere is reported, not a K1 trigger.
- **Partial certification** (operator decision, registered now): if every gate passes except species-leg or verdict
  false-alarm gates confined to set kinds with m > 300, the verdict is certified for claims with m ≤ 300 and claims
  with m > 300 are labelled "uncertified (species leg)"; likewise, if the only failures are species-leg or verdict
  false-alarm gates of the cortex-only replica, single-class claims are "uncertified". The rule covers false-alarm
  gates only: a plant-active or planted-leg failure anywhere, the replica included, means a gate is untested and fires
  K1, as does any other failure.
- The G1-on-F-mod plant-active gate is dropped (operator; post hoc). P+1 and P+2 as frozen (both passed). G1–G5,
  Level 2, J1, the joint pair: reported, not gated.
- **K1 (re-armed)** fires iff a gate fails outside the partial-certification rule. For a calibrated species max (rate
  ≤ .025), a stratum fails with probability 2.4e-6 at n = 1,000 (≈ 2e-3 across the 744 false-alarm strata, a union
  bound, so it holds for the paired w strata too); the remaining risk is real
  inflation near the .05 cap. Correction recorded: the frozen §6.4's "≈ .08" understated its n = 500 strata (≈ .020
  each when calibrated; ≈ .30 across 18).

## 6. Code, tests, compute
Committed with toy-data unit tests before any run: `src/asdg/species.py` (the null builders G1, G3m, G6s, G6l with its
pool rules, drawn once per claim and scored against one or several maps; the conditioning; the uninformative rule; the
species legs' resolution floor; the reference legs), `src/asdg/modules.py`, `arcs/audit/src/e3_align_plants.py` (the
paired maps, the verdict status), `arcs/audit/src/e3_species_replay.py`, `arcs/audit/src/e3_gates_a3.py` (25 planted
toy gate cases run before every evaluation; `e3_gates.py` stays as the record of the frozen verdict), and the design
descriptor `arcs/audit/src/a3_design_eligibility.py`. `src/tests/test_species.py` (12 tests) includes: float32 window
curves against the float64 loop (identical rankings; in-band decisions identical except at the band edge);
species_many = species per map on one random stream; the pool-diversity and resolution rules. The audit code must
implement S2c exact enumeration and the verdict-level resolution label, with toy tests, before any claim is evaluated.
**Compute.** G6l's window step dominates and is memory-bandwidth-bound at 22 workers: 21 / 14 / 41 / 11 ms per seed
draw in V-AAL / V-DK / V-CC200 / the replica with the float32 genes-as-rows loop (the v3 loop: 47 / 37 / 100 / 30 ms,
`results/a3_design_eligibility_v3loop.log`), ≈ 200 draws per call, ≈ 212,000 calls: ≈ 12 h, ≈ 14 h in all on 22
workers (the v3 loop, unpaired, with the v2 leg drawing its own windows, ≈ 464,000 calls: ≈ 65 h of G6l; the v3
draft's 10–11 h assumed an uncontended cost).
Nothing downstream (claims register, audit) runs until these gates pass (or pass under the partial rule).

## 7. Change log v3 → v3.1 (the verification pass's findings; no A-level finding)
- Uninformative label applied (N6, B5): a verdict status; a non-rejection in false-alarm gates (denominator kept), a
  miss in catch and power gates; counted per gate (§2, §5).
- Class-step strata (A5): every gate reports step 0 / step 1 and its ten generator cells (§5).
- An unregistered T-mod plant-active gate in the code removed; T-mod's site-leg rates reported, not gated (§5).
- G6l budget: "5K" read as 5·K = 1,000 draws; the measured eligibility shows it never binds (§3, §0 (iv)).
- Resolution (N11): the species legs' floor is computed and counted; S2c enumeration and the verdict-level label are
  audit-code requirements; neither can bind in the plants (§2, §6).
- Pool descriptors: the signed pool coherence restored; "tissue-class make-up" defined (the seeds' between-class
  variance share) (§3). Pool diversity (A2) now required: the frozen J1 Jaccard rule, "degenerate" (§3).
- Reference legs' scope stated (G6s-v1 on every plant; the v2 max on T-brain, rescoring the claim's own windows) (§4).
- T-wmod defined: the module score is the mean over all the cluster's genes (§4).
- Partial certification covers false-alarm gates only; a plant-active or planted-leg failure anywhere, the replica
  included, fires K1 (§5).
- §0 (iii) / (iv) completed (N16, B7); §1's brain-fraction slip corrected (N1).
- Compute: the v3 estimate (10–11 h) was ≈ 3× too low. Exact-equivalent changes: G6l's window loop runs with genes as
  rows (identical windows), and the v2 reference leg reuses each claim's windows. Operator decisions: float32 window
  sums (§3) and F-align maps paired across w (§4) (§0).
- Re-verification of v3.1 (asdg-skeptic, restricted): **verified**, no A-level finding. Its three reporting-level
  residues were fixed before freezing without a further pass: status counts reported per category in every gate and
  per kind (with k / n, strata and cells) for plant-active; the float32 figure worded as an observed maximum; §0
  completed (the smoke test, the v3-loop log, the re-verification's computations).
