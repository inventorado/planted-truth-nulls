# PREREG AMENDMENT 5 — A1 `audit`: K1 under amendment 3 resolved by scope — catch and power become registered descriptors

**v4 — the frozen version** (`bench.py freeze`; hash in `FROZEN.txt`). v1 was reviewed by asdg-skeptic (2026-09-24, "fix
then freeze"; 2 A / 11 B / 9 C). The verification of v2 found those fixes largely in place, with 2 A / 6 B / 10 C new
or residual findings ("not verified"). The re-verification of v3 resolved them but for one new A-level finding and four
C residues; v4 applies them (§8).

Amends `prereg.md` (FROZEN, sha256 a632b852…), as amended by `prereg_amend_1.md` to `prereg_amend_4.md`:
- §1: how Q-primary's outcomes are read;
- §4.7: the reading and headline counting of component claims (the test is unchanged);
- §4.6 as replaced by `prereg_amend_3.md` §2: the reading of a verdict (not the verdict), including amendment 3 §2's
  reading of a passing selected list;
- §6.4 / §9 as replaced by `prereg_amend_3.md` §5: which gate failures fire K1, and planted legs (a) and (c) in the
  cortex-only replica;
- `prereg_amend_4.md` §0 / §2: the labels and headline counting of its component-level and out-of-class claims.

Everything not named here is unchanged. "Set size m" below is the number of S's genes present in the class matrix; the
number of claims is written out.

## 0. Status, post-hoc elements and exposure (declared)
**The whole amendment is post hoc.** It was written 2026-09-24 (A1 session 5), **after** the complete amendment-3 battery
was gated and after that section of `ARC.md` was revised by independent verification (r1; r2 in this session):
- `results/e3_gates_a3.json` (sha256 105e81f1674aaf600af8c22cefd3fc547badd74f2dba27e10f6f8315bfc857b0) / `.md`, script
  `src/e3_gates_a3.py` @0472a74 (clean; self-test pass): K1 fired, 11 hard failures, partial certification none (finding
  `ASDG-AUD-F3-a3power`);
- `results/e3_a3_leg_diagnostics.json` (sha256 f898c90fc97a1d3c319a58510eb10182688257a9e1f533048d56a8d1f4f1fbdf; script
  committed f6b46c3);
- `ARC.md` revision r1 (commit 3924822) and r2 (commit dabae57, this session: r1's "C-gene catch did not fall"
  corrected for V-DK).

**Who decided.** The operator delegated the K1 decision to the orchestrator ("decide it"). The decision — option 3 with
the three untested plant gates resolved by declared scope limits, no rerun — was recorded in `ARC.md`, "K1 decision"
(commit 54b0ccb), before this file was drafted. **Added by the orchestrator in writing it (post hoc)**, each marked
"(orchestrator)" where it appears; **the operator confirmed them before the freeze (recorded in §8)**:
1. the label conditions (§4.1 R²_grad and R²_|x|; §4.2 brain-enriched) and the two further gradient labels of §4.1;
2. the rule for which power table a claim carries; the set-size, class and gradient limits of "calibrated evidence" (§3);
3. the readings and headline counting of component-level claims (the frozen 11 included) and of claims without a map
   (§3);
4. §4.3 (labels for re-parcellated, out-of-class and single-class claims);
5. §4.4 (planted legs (a) and (c) in the cortex-only replica, omitted by the gate code) and their consequences; for (c)
   this departs from decision point 5 (a failure gives a label, not K1);
6. keeping verdict catch on C-sp as a K1 gate (§5; the decision's point 2 names catch in general);
7. the C-sp / C-gene descriptors at a = .3 and .6 and their script (§3);
8. the reporting rules: "failed as gates under amendment 3", the forbidden words, the headline sentence, the frozen
   values (§1, §3);
9. the mechanical check `e3_gates_a5.py`, its plants and its stop semantics (§5).

**Seen before writing (the complete list):**
1. every gate of `e3_gates_a3.json` / `.md`: k / n, step strata, generator cells, status counts, per-kind plant-active
   rates;
2. the leg diagnostics (per-leg catch at a = .9; per-leg power at a = .3 / .5 / .7 by class × set kind);
3. the PC1 / PC2 descriptor cells `results/e3_a3_pc_descriptors.json`;
4. session 3's gates and descriptors `results/e3_gates.json` (sha256
   5c4dfb652d18d4d79e7fb3e506756ef276d0268347c84126c38cae324e2fbecf): among them the frozen cascade's catch and Level 0,
   site-pair and G1 rates on C-sp and C-gene at a = .3 / .6 / .9 at α .05;
5. C3, `results/e3_c3_gradients.json` (sha256 e33b495fc4d9928ee05e28f5c8e5c77cfdc366777dc0ebc3b6b9b7da66ca9d6a):
   site-pair rates against coordinate gradients;
6. probe `ASDG-AUD-E5-regime`, every cell (`probes/regime/results/regime_cells.md`; `ASDG-AUD-F4-coherencenull`);
7. session 1's R2 (`results/e4_r2_giacomel.json`): Giacomel 2026's ASD claim reproduced at spin level — at the pinned
   commit ρ −.022 / −.053 / .104, p .476 / .446 / .397 (overall R2 fail), and with the authors' eda33ab maps ρ −.1505 /
   .4125 / −.0534, p .252 / .073 / .423. These are statistics on an audit target's claim, taken before the A1 rule's
   register;
8. amendment 3 §0 (iii): the reviewers' size, within-class coherence and brain>body content of 10 public lists (Seidlitz
   2020 classes; Velmeshev 2019 DEGs), some of which may become audit sets;
9. the audit-target notes (`literature/notes/`, amendment 4's literature pass): each target's parcellation and set size;
10. the exploration lane `explore/discovery/FINDINGS.md` F-X1 … F-X8 (ABIDE I only; non-citable; the ENIGMA-ASD map was
    not touched, "on hold" there);
11. in drafting this file the orchestrator read back, from `e3_gates_a3.json`, `e3_gates.json` and `e3_c3_gradients.json`
    only: the per-kind site-leg rates of T-grad (every class) and of T-brain in V-CC200, the maximum verdict and
    species-leg false-alarm rate per class × target × w, the frozen cascade's C-gene catch, C3's stratified-pair rates
    and the replica files' recorded sha256; and, from `src/e3_align_plants.py` and `src/e3_gates_a3.py` (code only),
    that the replica's T-brain plants carry the v2 reference column and how planted legs are computed. No plant file was
    opened and nothing was computed.

**Not seen:** no amendment-3 verdict leg, R²_grad, R²_|x|, brain-enrichment p or other label condition has been computed
on any audit claim; the exceptions above (items 7–9) are listed. The verdict's catch rates on C-sp and C-gene at a = .3 /
.6 and planted legs (a) and (c) in the replica have never been computed.

## 1. What amendment 3's gates showed (unchanged; stays on the record)
K1 (`ASDG-AUD-K1-plantfail`) fired under amendment 3 on 11 hard failures. Every false-alarm gate passed: 762 strata;
species leg max .022, verdict max .019 (step strata ≤ .036 and ≤ .024).

| # | gate (amendment 3 §5; threshold) | k / n (rate) | class under this amendment |
|---|---|---|---|
| 1 | verdict catch, V-AAL C-gene a = .9 (≥ .80) | 197 / 296 (.666) | descriptor (§3) |
| 2 | verdict catch, V-DK C-gene a = .9 (≥ .80) | 175 / 299 (.585) | descriptor (§3) |
| 3–5 | power, V-AAL C-align a = .7 (≥ .50), rand-25 / fill-100 / brand-100 | 174 / 500 (.348), 91 / 500 (.182), 53 / 500 (.106) | descriptor (§3) |
| 6–8 | power, V-DK C-align a = .7 (≥ .50), rand-25 / fill-100 / brand-100 | 176 / 500 (.352), 99 / 500 (.198), 106 / 500 (.212) | descriptor (§3) |
| 9 | plant-active, V-AAL T-grad w = .9, max over kinds (≥ .05) | 28 / 1000 (.028) | scope label (§4.1) |
| 10 | plant-active, V-CC200 T-grad w = .9, max over kinds (≥ .05) | 36 / 1000 (.036) | scope label (§4.1) |
| 11 | planted leg (c), V-CC200 v2 species max, T-brain × brand-300 × w = .9 (> .05) | 23 / 1000 (.023) | scope label (§4.2) |

**Frozen values (orchestrator).** The values quoted in §1, §3, §4 and §6 are those of the four files named in §0
(`e3_gates_a3.json`, `e3_a3_leg_diagnostics.json`, `e3_gates.json`, `e3_c3_gradients.json`, with their sha256), and they
are frozen with this amendment. A later re-evaluation (a code fix, a corrected plant file) is reported **beside** them
with its commit and reason, never in place of them. A label of §4 is removed only by a later frozen amendment. Every
output that reports an audit result reports gates 1–11 with the words "failed as gates under amendment 3".

## 2. The verdict is unchanged
Level 0 ∧ the class-stratified site leg ∧ the species leg max(G1, G3m, G6s, G6l), each < α_v = .025 (amendment 3 §2).
Unchanged with it: the statuses (unmatched, degenerate, uninformative, resolution-limited) and their rule that such a
claim cannot survive; BH q-values descriptive; the selected-list test (read as in §3); the enrichment rule; the partial-
certification rule; amendment 4's routing of the added targets. The test is not changed a third time after its behaviour
was seen.

## 3. Catch and power: registered descriptors
Gates 1–8 of §1 are no longer gates; their thresholds (.80, .50) are kept as reference values in the tables. Verdict
catch on C-sp stays a K1 gate (§5; orchestrator): it passed, so keeping it adds a trigger and helps no claim, and without
it no gate would test that the verdict can catch anything.

**The power table (registered content).** Verdict rates at .025, from the amendment-3 battery:

| plant | a | V-AAL | V-DK |
|---|---|---|---|
| C-sp (m = 25, random) | .9 | .970 | .970 |
| C-gene (m = 25, random) | .9 | .666 | .585 |
| C-align rand-25 / fill-100 / brand-100 | .3 | .070 / .034 / .018 | .074 / .048 / .028 |
| C-align rand-25 / fill-100 / brand-100 | .5 | .176 / .128 / .060 | .196 / .114 / .068 |
| C-align rand-25 / fill-100 / brand-100 | .7 | .348 / .182 / .106 | .352 / .198 / .212 |

Beside it: each leg's own rate (Level 0, site, G1, G3m, G6s, G6l, species max) from `e3_a3_leg_diagnostics.json`, and
for C-align the Level 0 ∧ site conjunction (`c_align[].naive_and_site`).
**Added (orchestrator):** `arcs/audit/src/e3_catch_curves_a5.py` computes, from the existing replayed plant files, the
verdict, each leg's rate and the Level 0 ∧ site conjunction on C-sp and C-gene at a = .3, .6 and .9, by the rule of
amendment 3 §5 (denominator = computed plants; any status other than ok = a miss). It runs after the freeze and before
any claim is evaluated, and its output is reported whatever it shows. It first asserts that at a = .9 it reproduces the
verdict catch of §1 and §3 exactly (C-gene 197 / 296 and 175 / 299; C-sp 291 / 300 in both classes); a mismatch stops
it.

**Which table a claim carries (orchestrator).** No single power number is selected for a claim.
- Every claim row reports its class's columns (V-AAL or V-DK) and its own set size m, f / m (brain>body fraction, §4.2)
  and c_S (within-class coherence, amendment 3 §3), so a reader can place it among the rand, fill and brand kinds.
- A claim analysed in any other class (V-CC200, the cortex-only class dk-ctx, a single-class claim outside dk-ctx
  (§4.3), or natively outside the planted classes) carries both columns and the label "power not measured in this
  class".
- A claim with m < 25 or m > 100 carries "power not measured at this set size".

**How an outcome is read.**
- **Survival** (status ok; Level 0, site and species each < .025), with 25 ≤ m ≤ 1,000, in a planted class (V-AAL, V-DK,
  V-CC200, dk-ctx; a re-parcellated claim is in its target class) and without either label of the next bullet:
  "survives — calibrated evidence". That means a verdict false-alarm rate of at most .05 (the gate cap; measured maximum
  .019, step strata ≤ .024) in every informative planted stratum, subject to the claim's scope labels (§4).
- **Survival outside those limits** (orchestrator): m < 25, m > 1,000, natively outside the planted classes, a
  single-class claim outside dk-ctx (§4.3), or carrying "gradient beyond planted strength; site-leg bound extrapolated"
  or "gradient orientation unplanted (M–L)" (§4.1).
  The reading is "survives — calibration extrapolated (set size / class / gradient)", naming which, never "calibrated
  evidence": no false-alarm stratum exists there.
- **Non-survival with status ok:** "not detectable at this power". Never "refuted", "fails", "does not replicate" or
  "not supported". No non-survival is presented as evidence against a claim, whatever its power column shows.
- **A claim with a status, flag or label** (unmatched, degenerate, uninformative, resolution-limited, not testable, not
  reproduced, not auditable, deferred; amendment 3 §5's partial-certification labels "uncertified (species leg)" and
  "uncertified" for single-class claims, should a re-evaluation ever invoke them) is reported by it, as frozen.
- **Component-level claims** (orchestrator): prereg §4.7 component claims of any target (the frozen 11 included),
  amendment 4's component-level claims (Dear, Hansen, Moreau) and amendment 3 §2's lists selected on imaging data.
  - The test is unchanged: Levels 0–1 with refit, and list re-selection where amendment 3 §2 requires it.
  - The reading is "passes / does not pass at component level (Level 0 and site leg at .025)". A passing selected list
    adds amendment 3 §2's "map–expression link, not set specificity". Every such claim carries the label "site leg only;
    not calibrated against expression-aligned maps": at w = .9 the site leg alone rejects up to .158–.330 of T-wmod
    plants (maximum over kinds, per class) and up to .312 of T-brain plants.
  - They are never "survives" or "calibrated evidence" and never count as survivals. Amendment 4 already rules so for
    its component-level claims; this extends the rule to the frozen 11 and replaces amendment 3 §2's words "a surviving
    such claim".
- **A claim without a spatial map** (prereg §5.1: Liu 2026, Level 2 only) has no amendment-3 verdict. Its gene-null
  p-values are descriptors, read "no calibrated test" (orchestrator; a consequence of amendment 3 §2).

**Headline.** The frozen-11 survival fraction stays the only headline (amendment 4; interim while Romero-Garcia's ABIDE II
claims are deferred). Component-level claims and claims read "no calibrated test" stay in its denominator as
non-survivals, each with its flag (as a target without public material does, prereg §5.1). Every statement of the
fraction carries, beside it:
- the curves: C-sp .970 at a = .9; C-gene .585–.666 at a = .9; C-align .018–.074 / .060–.196 / .106–.352 at
  a = .3 / .5 / .7;
- how many survivals carry each scope label, and how many read "calibration extrapolated";
- how many denominator claims are component-level (and how many of those pass at component level), "no calibrated
  test", not auditable, or deferred.

The fraction counts every survival; the number of survivals reading "calibrated evidence" is stated beside it. A low
fraction is stated as "few published claims are detectable by a calibrated test at this power", never as "few are
true".

**What changes and what does not.** Where a verdict is computed it is identical to amendment 3's: the verdict and α_v are
unchanged, so no claim can gain a survival from this amendment. What changes is that the audit may run, and what may be
concluded from a non-survival or a component-level pass.

## 4. The untested plant gates: scope labels, no rerun
### 4.1 T-grad in V-AAL and V-CC200 (gates 9–10)
- **What failed.** Amendment 3 §5: a target family whose site-leg maximum over kinds is below .05 "does not stress the
  species leg". Measured at w = .9: V-AAL .028 (per kind .001–.028), V-CC200 .036 (per kind .010–.036).
- **On the T-grad plants, the verdict is calibrated.** The verdict rejects only where the site leg rejects (conjunction),
  on the same maps with the same denominator. At w = .9 its false-alarm rate is therefore at most the site leg's rate at
  .025: ≤ .028 in V-AAL and ≤ .036 in V-CC200, in every set kind, below the .05 cap, whatever the species leg does. (The
  site leg's rate at w = .5 is not a registered output and was not read.) Measured directly on every T-grad stratum
  (both w, 14 kinds): verdict ≤ .003 (V-AAL) and ≤ .006 (V-CC200); species leg ≤ .015 and ≤ .019.
- **What stays untested.** The species leg's own protection on gradient-aligned maps in these two classes: whether it
  would hold where the site leg is fooled. The bound itself covers only the planted range: w ≤ .9, the A–P and I–S
  orientations, the five field generators and the 14 set kinds.
- **Labels (orchestrator).** R²_grad is the R² of the claim's map, demeaned within tissue class, regressed jointly on the
  within-class-demeaned MNI y and MNI z centroid coordinates over the claim's analysis parcels. R²_|x| is the same with
  within-class-demeaned |MNI x|. Both are reported for every claim in every class.
  - "species leg untested (gradient)": a claim in V-AAL or V-CC200 with R²_grad ≥ .25. The .25 is a conservative
    convention: w² at the smaller planted w, ignoring the field's own projection on the coordinates, so w = .5 plants
    are expected to sit near or above it (not measured).
  - "gradient beyond planted strength; site-leg bound extrapolated": any claim, in any class, with R²_grad > .81 (w² at
    the larger planted w). Its survival reads "calibration extrapolated (gradient)" (§3).
  - "gradient orientation unplanted (M–L)": any claim, in any class, with R²_|x| ≥ .25. Amendment 3 §4 already limits the
    gradient plants to A–P and I–S; non-linear gradients are unplanted in every class too (C3 is a descriptor only). Its
    survival reads "calibration extrapolated (gradient)" (§3).
- **Why no rerun (a judgement, not a measurement).** In V-AAL and V-CC200 the class-stratified site leg responds only
  weakly to coordinate gradients, even at full strength. C3 (m = 25, the gradient maps themselves with no field, α .05)
  gives stratified-pair rates of .0225–.07 (V-AAL; .07 = module sets against A–P) and .035–.065 (V-CC200) against A–P
  and I–S. A stronger gradient plant would therefore still hardly stress the species leg there. In V-DK it does respond
  (C3 .075–.125; plant-active .068), and there the gate was tested and passed.

### 4.2 T-brain × brand-300 × w = .9 in V-CC200 (gate 11)
- **What failed.** The reference leg (the v2 species max: no brain-fraction matching, so exposed to the brain-enrichment
  confound, "N1" in amendment 3's review record: a brain-profile-aligned map paired with a brain-enriched set) rejected
  at only .023 there. The plant did not produce the confound in V-CC200, so the species-leg gate's sensitivity to it is
  untested in V-CC200. It passed in V-AAL (.086) and V-DK (.133).
- **What passed on the same plants.** Verdict false alarm ≤ .008 and species-leg false alarm ≤ .017 on every V-CC200
  T-brain stratum (both w, 8 kinds).
- **Label.** A V-CC200 claim whose set is brain-enriched carries "brain-enrichment (N1) confound untested".
  **Brain-enriched (orchestrator):** with U the class universe, B as amendment 3 §3, f_U = |B ∩ U| / |U| and f = |S ∩ B|,
  S is brain-enriched iff f / m > f_U with a one-sided hypergeometric p < .05 (population U, successes B ∩ U, draws m),
  **or** f / m ≥ (f_U + .45) / 2 (the midpoint to the planted brand fraction, so small sets at that fraction are not
  missed). The label depends on the set only, as decided. f / m and the p are reported for every claim in every class;
  r(y_w, d_B) (the within-class map against the brain-enrichment profile) is reported as a descriptor only.

### 4.3 Re-parcellated, out-of-class and single-class claims (orchestrator)
No audit target is known to use CC200. Prereg §2 makes V-CC200 a false-alarm class only, and amendment 4 re-parcellates
onto V-DK, dk-ctx or V-AAL. So the labels of §4.1–4.2 reach claims mainly through these rules:
- A claim re-parcellated onto any class, or run natively outside the planted classes, carries "species leg untested
  (gradient)" if R²_grad ≥ .25 and "brain-enrichment (N1) confound untested" if its set is brain-enriched, whatever the
  class (conservative: applied also where the gate was tested). The register's routing choice cannot remove a label.
- A claim on the Desikan–Killiany cortical parcels (a native DK map such as ENIGMA's DK-68, or a map re-parcellated onto
  V-DK or dk-ctx) whose analysis parcels are all cortical is read as a dk-ctx claim: dk-ctx's calibration and labels,
  §4.4's included, whatever class the register names. Prereg §2 already analyses such maps on that class only.
- Any other claim whose analysis parcels are all of one tissue class (cortex-only in V-AAL; a subcortex-only map such
  as ENIGMA's subcortical volumes; a single-class map run natively outside the planted classes, e.g. Schaefer, Glasser
  or DK-308) has no planted stratum of its kind. Its survival reads "survives — calibration extrapolated (class)", and
  it carries the first bullet's labels.
- For re-parcellated and out-of-class claims, the parcel centroids and tissue classes used for R²_grad and R²_|x| are
  those the claims register fixes for the claim's spatial nulls, before any statistic.

### 4.4 Planted legs (a) and (c) in the cortex-only replica (orchestrator)
Amendment 3 §5 requires planted legs (a) and (c) "in every class", and makes a planted-leg failure "anywhere, the replica
included" a K1 trigger. `e3_gates_a3.py` evaluated both in V-AAL, V-DK and V-CC200 only (`CLASSES`, line 38; loop from
line 261). That omission is declared here. The replica's plants carry the needed columns (p_naive; p_v2_species on
T-brain plants), so both gates are computable without new plants. `e3_gates_a5.py` (§5) evaluates them, once per run of
the check, before any audit claim is evaluated. Each file's sha256 is first asserted equal to its entry in
`e3_gates_a3.json` `inputs_sha256`. The rules below are registered before either value is read.
- **(a) in the replica:** naive Level 0 on rand-25 × T-mod × w = .5 (`dk-ctx_F-align_mod_0.5.csv.gz`; in one class
  T-mod is the within-class module map, the replica's analogue of T-wmod) must exceed .05. The call is the one
  `e3_gates_a3.py` makes for (a) in the other classes. A failure fires K1 (decision point 5).
- **(c) in the replica:** the v2 species max on T-brain × brand-300 × w = .9 (`dk-ctx_F-align_brain_0.9.csv.gz`), by the
  call `e3_gates_a3.py` makes for (c) in the other classes: `rate_gate` on p_v2_species, kind "mustfail", denominator =
  plants with a computed p_v2_species, verdict status not applied. The rate over all plants, with non-ok statuses as
  non-rejections, is reported beside it.
  - If the rate is > .05, the gate passes and joins the retained gates (§5).
  - If it is ≤ .05, the logic of §4.2 applies, not K1. Every claim in dk-ctx (including those §4.3 assigns there) whose
    set is brain-enriched then carries "brain-enrichment (N1) confound untested". This departs from decision point 5
    (orchestrator; declared): the same failure type in V-CC200 was resolved by a label. It matters because dk-ctx is the
    class of the ENIGMA-ASD thickness targets (Patel, Giacomel). Hansen's sub-claim is site-leg only (§3), so the label
    does not apply to it.
- Both are reported either way, with k / n, step strata and generator cells.

## 5. K1 re-armed on everything else
- **Retained gates** (amendment 3 §5; all passed in `e3_gates_a3.json` unless marked):
  - every species-leg and verdict false-alarm stratum of F-align and the cortex-only replica (372 + 372);
  - verdict false alarm on F-sp / F-mod / F-traj per class and step stratum (18);
  - verdict catch on C-sp, V-AAL and V-DK (2; orchestrator, §3);
  - plant-active: T-wmod and T-brain in every class, T-grad in V-DK, and the replica's three targets (10);
  - planted legs: (a) in every class (3) and in the replica (§4.4, not yet evaluated); (b) in V-DK and V-CC200 (2;
    V-AAL reported, not required, as frozen); (c) in V-AAL and V-DK (2), and in the replica if it passes (§4.4);
  - naive plant-active on F-sp in every class (3); P+1 and P+2.
- **K1 fires** if a retained gate fails outside amendment 3 §5's partial-certification rule (unchanged), or if the check
  stops on an input assertion (below), on the one evaluation below or on any re-evaluation: a rerun after a code fix, a corrected plant file, or a plant family added by
  a later amendment (gated by the same rules). Gates 1–11 are not triggers: 1–8 are descriptors (§3), 9–11 scope labels
  (§4). On a re-evaluation they are classed by identity (gate name), whatever their new values, and those values are
  reported beside §1's.
- **Mechanical check (registered; written after the freeze, run before the claims register is frozen).**
  `arcs/audit/src/e3_gates_a5.py` reads `results/e3_gates_a3.json` and asserts its sha256 (§0). It classes every gate as
  retained, descriptor or scope, evaluates §4.4's two gates, and writes `results/e3_gates_a5.json` / `.md` with K1's
  status under this amendment.
  - **Inventory.** It asserts the gate inventory: species_fa 372, verdict_fa_align 372, verdict_fa_existing 18,
    verdict_catch 4, power 6, plant_active 12, planted_legs 9 (+2 from §4.4), and the carried frozen gates (naive
    plant-active 3, P+1, P+2). Asserted present but not gates: `frozen_carried.G1_plant_active` (dropped by amendment 3;
    reported, never a trigger) and `descriptors.site_rate_T-mod_not_gated` (3). A missing, extra or not-evaluated gate
    stops the script.
  - **The 11.** It matches gates 1–11 by name and k / n exactly as in §1 (197/296, 175/299, 174/500, 91/500, 53/500,
    176/500, 99/500, 106/500, 28/1000, 36/1000, 23/1000). The value match applies only to this one evaluation of the
    file with the §0 sha256. Any other failing gate outside the partial-certification rule means K1 fires.
  - **Stops.** On any stop the script first writes "K1 = fired" with the reason. A stop on an assertion about the inputs
    (sha256, inventory, value match) fires K1 and stands until a later frozen amendment. An exception in the check's own
    code is fixed and the check rerun; both runs are reported.
  - **Self-test first**, on planted copies of the JSON. In the self-test the JSON's sha256 assertion is pointed at each
    copy's own hash (except in p0), the value match is always against §1's values, and the §4.4 rates are injected, not
    read from the plant files; unless a plant says otherwise, they are injected as .06 (passing). A plant passes only if
    both its status and its reason string match. Every plant must pass before the real evaluation is written.
    - (p0) one byte of a copy changed, expected hash kept → stop; K1 fired; reason: sha256 (gates JSON).
    - (p0b) a plant file's recorded hash in `inputs_sha256` altered → stop; K1 fired; reason: sha256 (plant file).
    - (p1) an existing species false-alarm stratum (m ≤ 300, not dk-ctx) given a failing k; no stratum added → K1
      fired; reason: retained gate failed, <gate name>.
    - (p1b) an existing false-alarm stratum confined to dk-ctx, or to a kind with m > 300, given a failing k → "not
      fired (partial certification)", with the label "uncertified" (single-class claims) or "uncertified (species leg)"
      (m > 300); reason: partial certification, <gate name>.
    - (p2) the V-DK T-grad plant-active gate set to fail → K1 fired (the scope covers V-AAL and V-CC200 only); reason:
      retained gate failed, <gate name>.
    - (p3) planted leg (c) set to fail in V-AAL → K1 fired; reason: retained gate failed, <gate name>.
    - (p4) one catch k / n among gates 1–11 changed → stop; K1 fired; reason: value mismatch, gate N.
    - (p5) the unmodified JSON → K1 not fired; reason: none.
    - (p6) a retained gate deleted → stop; K1 fired; reason: inventory.
    - (p7) P+2 set to fail → K1 fired; reason: retained gate failed, P+2.
    - (p8) C-sp catch set to .79 → K1 fired; reason: retained gate failed, <gate name>.
    - (p9) the replica's T-grad plant-active gate set to fail → K1 fired; reason: retained gate failed, <gate name>.
    - (p10) gate 9 set to .060 (60 / 1000) → stop; K1 fired; reason: value mismatch, gate 9.
    - (p11) the §4.4 (c) rate injected as .04 and as .05 → K1 not fired, the dk-ctx label switched on; reason: scope
      label, replica (c). Injected as .06 → a retained gate, passing; reason: none.
    - (p11b) the §4.4 (a) rate injected as .04 and as .05 → K1 fired; reason: retained gate failed, replica (a).
      Injected as .06 → passing; reason: none.
    - (p12) a gate entry added → stop; K1 fired; reason: inventory.
    - (p13) a retained gate with status "not run" → stop; K1 fired; reason: inventory. (A "fail: …" status is an
      evaluated failure, not a stop.)

## 6. Paper 1: the trade-off is the instrument finding
`ASDG-AUD-F3-a3power` (the calibration–power trade-off) is reported in paper 1 as an instrument finding, beside E3
(session 3) and `ASDG-AUD-F4-coherencenull`, with:
- the full gate table and the leg diagnostics;
- the cost of the full conjunction relative to the stratified site leg alone: 28–31 % of C-gene catch, 43–83 % of
  C-align power at a = .7, ≤ 3 % on C-sp;
- the comparison with the frozen E3 cascade, at different α levels and denominators: at α .05 the frozen cascade caught
  C-gene at .627 (V-AAL, 188 / 300) and .610 (V-DK, 183 / 300); the verdict at α_v .025 catches .666 (197 / 296; +.039)
  and .585 (175 / 299; −.025);
- the dropped G1 plant-active gate's frozen failure (.094 / .085 < .10).

Wording rule for instrument-level statements (the per-claim reading is §3's): "calibrated on every informative stratum",
with the qualifications of §4 and the 18 F-family strata that cannot fail by construction. Never "calibrated" without
them.

## 7. Unchanged
- The claims register (`prereg.md` §5.2, with amendment 4's targets and deferrals) is written and frozen before any
  statistic touches an ASD map. The number of claims is fixed there.
- S2c exact enumeration and the verdict-level resolution label are implemented in the audit code, with toy tests, before
  any claim is evaluated (amendment 3 §2, §6).
- Every other rule of `prereg.md` and amendments 1–4.

## 8. Review record
**v3 → v4** (re-verification, 2026-09-24: "not verified"; N1–N18 and the B2 / B5 residues resolved; every number and
code fact confirmed; findings adopted):
- **NF1 (A)** §4.3's single-class rule let native cortex-only parcellations (Schaefer, Glasser, DK-308) read as dk-ctx
  and so "calibrated evidence". Now only Desikan–Killiany cortical claims are read as dk-ctx; every other single-class
  claim reads "calibration extrapolated (class)" (§3, §4.3).
- **NF2** the headline states how many survivals read "calibrated evidence".
- **NF3** K1 also fires on an input-assertion stop ("if", not "iff").
- **NF4** self-test: reason strings on every plant; p13 limited to status "not run"; boundary .05 in p11b; p0b (plant
  file hash); the value match always against §1; `e3_catch_curves_a5.py` asserts that a = .9 reproduces §1 / §3.
- **NF5** prereg §4.7 added to the "Amends" list; `ARC.md` r2 committed (dabae57) and cited.

Final check of v4 (restricted to §3, §4.3 and the NF2–NF5 residues): **verified with residues**; no new contradiction.
Its three C residues were applied without a further pass: single-class claims outside dk-ctx carry "power not measured
in this class" (R1); the self-test's default injected §4.4 rates (R2); N4's record marked as narrowed (R3).

**v2 → v3** (verification pass, 2026-09-24: "not verified"; all numbers correct; findings adopted):
- **N1 (A)** survivals carrying "gradient beyond planted strength" or "gradient orientation unplanted (M–L)" read
  "calibration extrapolated (gradient)" (§3, §4.1).
- **N2 (A)** component-level claims of any target, the frozen 11 included, have a reading and never count as survivals;
  they and "no calibrated test" claims stay in the headline denominator with their flags (§3).
- **N3** §4.4 (c) uses the call applied to (c) in the other classes; the file's sha256 is asserted.
- **N4** single-class (cortex) claims take dk-ctx's calibration and labels whatever class the register names (§4.3)
  (narrowed by NF1 in v4).
- **N5** planted leg (a) in the replica added (failure → K1); the departure from decision point 5 for (c) declared (§0,
  §4.4).
- **N6** self-test: hashes and value match pointed at each copy; reasons matched; p0 added; p1 / p1b change existing
  strata only.
- **N7** stop semantics (§5).
- **N8** the operator confirms the orchestrator's additions before the freeze (§0; recorded below).
- **B2 residue** the inventory names the two non-gate entries; p12, p13 added.
- **B5 residue** `ARC.md` r2 applied before the freeze.
- **N9–N18 (C)** all four source files named with full hashes; R2's pinned-commit values added; "(not measured)" on the
  .25 convention; Hansen excluded from the N1 label; the C-sp / C-gene conjunction and its script named; denominators
  stated in §6; "(conservative)" on §4.3; partial-certification labels listed; the "Amends" list completed; p11
  boundary, injected rates and "once per run".

**v1 → v2** (asdg-skeptic, 2026-09-24: "fix then freeze"; every number checked against the artifacts, all correct except
one inherited from `ARC.md` r1). All findings adopted:
- **A1** planted leg (c) was never evaluated in the replica → §4.4, registered before the value is read.
- **A2** "calibrated evidence" had no set-size or class limit → 25 ≤ m ≤ 1,000 in a planted class; otherwise
  "calibration extrapolated" (§3).
- **B1** the partial-certification exception restored; the value match limited to the one evaluation (§5).
- **B2** inventory assertion; match by name and k / n; more plants (§5).
- **B3** exposure list completed; the false "no statistic on any target's claim" replaced.
- **B4** the orchestrator's additions listed and marked; C-sp catch declared as kept as a gate.
- **B5** "no loss against the frozen cascade" was false in V-DK (−.025); restated with both α levels (§6); `ARC.md` r2.
- **B6** the bound's range stated; labels for gradients beyond planted strength and for M–L; "why no rerun" limited to
  V-AAL and V-CC200, with C3's evidence, as a judgement (§4.1).
- **B7** brain-enriched: count/fraction slip fixed; the small-set clause added (§4.2).
- **B8** §4.3 covers re-parcellated claims, whatever the class; centroids and classes fixed by the register.
- **B9** readings for site-leg-only claims and for claims without a map (§3).
- **B10** frozen values; re-evaluations reported beside them; no non-survival used against a claim (§1, §3).
- **B11** the headline carries every curve of decision point 2 (§3).
- **C1–C9** "not detectable" (the decision's words); the verdict's own maximum quoted; "m" disambiguated; N1 glossed;
  "cannot create a survival" reworded; C-sp / C-gene a = .3 / .6 α .05 exposure declared; species false alarm not
  claimed for F-families; §6 scoped to instrument-level statements; label counts in the headline.

**Operator confirmation of the orchestrator's additions (§0 items 1–9):** confirmed 2026-09-24 ("Freeze v4 as written"),
including (a) verdict catch on C-sp kept as a K1 gate, (b) component-level claims never counted as survivals and kept in
the headline denominator with their flags, and (c) the replica's planted leg (c) giving a scope label rather than K1.
Neither replica value (§4.4) had been read.
