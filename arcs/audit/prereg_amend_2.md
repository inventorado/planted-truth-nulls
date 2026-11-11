# PREREG AMENDMENT 2 — A1 `audit`: C1 demoted from must-catch to reproduction (operator decision)

Amends `prereg.md` (FROZEN, sha256 a632b852…) §6.4 and §9, as already amended by `prereg_amend_1.md`.
Written 2026-09-23, **after** C1 was run and failed its must-catch pattern. This is a post-hoc rule change,
declared as such; it is the operator's decision (option (b) of the three listed in `ARC.md`), not the
analyst's.

## What was observed under the frozen rule (unchanged, stays on the record)
C1 (APOE × GAMBA `alzheimers_ALE.nii.gz`, 57 DK-114 left cortical parcels): β = 0.679 (Wei 0.631; within the
frozen ±0.10 "same map" band), Level-1 p = 1e-4, **G3 p = 0.014** (the pattern required ≥ 0.05). Under
`prereg.md` §6.4 this fired `ASDG-AUD-K1-plantfail`; recorded as `ASDG-AUD-F1-c1fail`
(`results/e3_realplants.json`, commit 0c2390f). That finding is not withdrawn: in every report C1 is shown as
"failed its registered must-catch pattern under v3; demoted by amendment 2".

## Why
1. `prereg.md` §8 already states that Wei 2022's example pairs have no ground truth. "APOE's association with
   the AD map is not gene-specific" is Wei's reading of their own data, not a property known by construction,
   so C1 cannot certify that a null *catches* a false positive — only whether we *reproduce* Wei.
2. Our input is not Wei's input: the GAMBA example ALE resampled by nilearn, versus Wei's FSL-coregistered
   BrainMap AD map. β differs by 0.048. Whether the G3 outcome differs because the map differs or because
   the null differs cannot be separated from this one pair.
3. The must-catch role the check was meant to carry — "a null must reject a coexpression-driven false
   positive" — is carried by synthetic families whose H0 is true by construction: F-mod (coexpressed modules
   × independent fields) with the plant-active gate (G1 false-alarm ≥ 0.10 per class) and the G2 / G4 / Level-2
   false-alarm gates, all already frozen in §6.4 and all K1 triggers.

## Change
- §6.4 C1 is a **reproduction**, not a must-catch: it reports β vs Wei, Level-1 p and G1 / G3 p, with no gate.
  The clause "C1 fails its pattern (when reproduced)" is removed from the K1 trigger list in §6.4 and §9.
- K1's other triggers are unchanged (P+1, P+2, plant-active gates, false-alarm gates for Level 1 / Level 2 /
  G2 / G4 / G5, catch gates for Level 1 / G2 / G4 / G5). The arc's K1 is **re-armed** under this amendment;
  whether the audit (§5) may run is decided by the §6.4 gates on the synthetic battery.
- The C1 discrepancy (our G3 p = 0.014 vs Wei's non-significant brain-gene null) is reported in P1 as an
  unresolved reproduction difference, with both candidate causes named.
- Nothing else changes.
