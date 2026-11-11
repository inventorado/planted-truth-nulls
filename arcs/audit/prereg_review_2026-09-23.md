# Pre-freeze adversarial review of the A1 prereg (draft v1 → v2), 2026-09-23

Reviewer: `asdg-skeptic` role (opus), against draft v1 and `src/asdg/` at commit 5e198b7. 20 findings.
Resolution in v2 (prereg section) or code.

| # | sev | finding (short) | resolution |
|---|---|---|---|
| 1 | BLOCKER | cascade false-alarm gate cannot fail: random S is exchangeable with G1, conjunction needs G1 | per-null-family gates on families where that null's H0 is true (§6.2, §6.4); cascade rates descriptors only |
| 2 | BLOCKER | plants not in class under test; tissue-class step (cortex/subcortex/cerebellum) failure mode absent | synthetic plants on each volumetric class's real centroids with class-step cells (§6.1); class-stratified S1c/S2c + adoption rule (§4.2) |
| 3 | BLOCKER | catch ≥ 0.80 needs ~9 p < .05 incl. coexpression-matched nulls on plants whose truth is not the gene H0 → K1 by design | catch per null family with ground truth defined against its own H0; gene plants on residualised score (§6.3); cascade catch descriptor |
| 4 | BLOCKER | J1 certified on BrainSMASH-built families (surrogate of a surrogate) | no plant uses BrainSMASH; GRF/SAR generators (§6.1); J1-vs-naive superiority claim dropped |
| 5 | MAJOR | J1's H0 misstated; pool/background mismatch | H0 stated (§4.4); pool = S's own G2 sets from the same universe; diversity + sd guards (code) |
| 6 | MAJOR | Clopper–Pearson ≤ 0.08 at n = 200 fails exactly-calibrated tests | n = 1,000, binomial test at α = 0.001 + rate ≤ 0.07 (§6.4; `cascade.fa_gate`, unit-tested: 5.0 % passes, 9.0 % fails) |
| 7 | MAJOR | 1,000 draws cap resolution; BH can never pass with m > 50 | 10,000 for every audit-level null incl. J1 M; resolution check m ≤ 500 at register freeze (§4.6) |
| 8 | MAJOR | PLS claims not operationalised | §4.7 (refit per surrogate, sign alignment, enrichment statistic, Level 0 permutation) |
| 9 | MAJOR | coexpression sampler biased (edge-piling, hub drift), S not excluded, infinite loop | Metropolis walk uniform within 4 stratified sub-bins, S excluded, restart cap → "unmatched", achieved distribution reported (code + tests: achieved mean 0.148 for target 0.150); R1 runs this sampler |
| 10 | MAJOR | G5: silent fallback, S not excluded from kNN, unscaled blocks, duplicate symbols | kNN with S excluded, blocks scaled, dedupe required, > 20 % fixed → not applicable (code + tests) |
| 11 | MAJOR | R2 p tolerance fails by chance | null-identity check first; exact if identical, else 3·√2·SE (§3.3) |
| 12 | MAJOR | R1 too loose; R3 count-only | per-test agreement in all 8 cells; R3 value check via pandas-2.2 venv (A5) |
| 13 | MAJOR | R4 / P+2 fallback contaminate ABIDE I before A2 | R4 moved to A2 after its freeze; P+2 uses Wei's own inputs; A1 opens no ABIDE file (§2, §8) |
| 14 | MAJOR | hemisphere / parcel / NaN policy unspecified | fixed in §2 (left + midline primary; bilateral multiverse; finite ∧ ≥ 1 sample; ≥ 2 donors sensitivity) |
| 15 | MAJOR | forking paths (plant direction, naive-joint pool, Level-0 mismatch, silent gene drop, undefined field, A5 either/or) | each fixed in text: +1; G1; run-and-flag rule; absent genes listed + min 5; generators defined; A5 single route |
| 16 | MINOR | must-catch set can be empty; C1 "or" contradicts max rule | C1 uses the Level-1 max rule; C1 pattern failure → K1; if not reproduced, F-mod carries must-catch |
| 17 | MINOR | plants only m = 25 | m ∈ {10, 100} descriptors in V-AAL |
| 18 | MINOR | BrainSMASH defaults unvalidated at small n | Base uses all pairs (no knn); variogram misfit logged per map; calibration decided by gates |
| 19 | MINOR | J1 no sd guard | assert sd > 1e-9 and pool Jaccard < 0.5 |
| 20 | MINOR | no data-handling statement | §8 |

Code bug found while fixing: `stratified_surrogates` (MSR branch) did not add the class mean back — caught
by the new unit test, fixed before any real-data run.

## Second pass (on v2), 2026-09-23 — resolved in v3

(a) Of the 20 first-round findings: 15 RESOLVED, 4 PARTIAL (1, 2, 15, 16), all closed by the items below.

| # | sev | finding | resolution in v3 |
|---|---|---|---|
| b1 | BLOCKER | G5 draws each member independently from its neighbours → null sets less coherent than a trajectory module → G5 gate fails by design (Fulcher mechanism) | G5 = trajectory-neighbour pool + G2's coexpression-band sampler (§4.3; code; test asserts no duplicates, S excluded) |
| b2 | BLOCKER | R1 coexp/joint cells compare our sampler with Cao's → K2 by design | R1 coexp cell uses Cao's sampler; per-test rule only for competitive/spin; our G2 on R1 is a descriptor |
| b3 | MAJOR | spatial gate pools step cells → dilutes the class-step failure | gated separately for step 0 / step 1 (n = 500 each) |
| b4 | MAJOR | no plant-active gates | naive on F-sp ≥ 0.15 and G1 on F-mod ≥ 0.10 per class, else K1 |
| b5 | MAJOR | Level 1 gated only on random-S families | also on F-mod and F-traj |
| b6 | MAJOR | C1 single gene vs MIN_SET; undefined G2/G4/J1 | C1 exempt, Level 1 + G1 + G3 only; `Universe.testable_set` enforces MIN_SET |
| b7 | MAJOR | P+2 makes no-ground-truth G2 a must-pass | must-pass = β + G1/G3 (as Wei reports); G2/G4/G5/J1 audit outcomes |
| b8 | MAJOR | J1 max-over-pair rule in code, not in prereg | stated in §4.4 |
| b9 | MAJOR | unmatched / n/a / degenerate handling undefined; assert aborts runs | gate rule (> 5 % in any cell fails); J1 returns a status, no assert |
| b10 | MINOR | background flag chosen by column order | by name + count assert (2,711) |
| b11 | MINOR | G5 duplicates on collision | gone with the b1 redesign |
| b12 | — | compute feasible (1–3 h plants; R1 spin cells on GPU) | noted |
| — | noted | ~5–8 % chance of a spurious K1 across ~40 gates | accepted and stated in §6.4 |
