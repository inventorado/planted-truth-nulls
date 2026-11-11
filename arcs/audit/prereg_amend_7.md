# PREREG AMENDMENT 7 — A1 `audit`: P1 / P2 split (supersedes amendment 6 §1)

**v1** (2026-11-03). Written before any gate-G1 claim statistic exists and before any G1 material is opened. As of
commit 5993012 the G1 path is unbuilt: a dry dispatch computes 0 of 380 rows, and the only G1 output is the repricing
`run_manifests/reprice_wp5.json` (about 1,209 process-h, 6.83× the frozen 177). Changes no statistic, leg, reading,
label or population rule.

## 0. Status (declared)
This amendment is post hoc with respect to the ungated and G2 results (0 of 16 units survive, 1 can;
`results/a1_run/G2/headline.json`) and to the G1 repricing. It is pre hoc with respect to G1.

**Decided by the operator on 2026-11-03** ("option 2"), on these grounds:
- the cost of the unbuilt G1 work package (material stage, loaders, the `run.py` hook, a §17-type pre-run check, a
  run-plan amendment);
- token scarcity;
- the 2026-11-01 direction to finish A1 as its own paper.

## 1. The rule (replaces `prereg_amend_6.md` §1)
1. **P1** reports:
   - the instrument: E3, F4 / probe E5, F3, amendments 3 and 5;
   - the audit of the gates that have run, ungated + G2, as a worked demonstration.
2. P1's audit headline is the frozen-11 survival fraction over ungated + G2, called **"interim (ungated + G2)"**, never
   "final". P1 states in the same sentence that G1's 196 population units have not run and are counted neither way, and
   that Dear (3 rows) and Vairam / Roy (6 rows) are deferred. No sentence of P1 describes this fraction as the
   literature's survival rate.
3. **P2** is the full audit. Amendment 6's rule ("final" once ungated + G2 + G1 have run; Vairam / Roy and Dear listed
   apart) applies to P2 unchanged.
4. Whatever G1 shows, it cannot move P1's reported numbers. If P1 is still unsubmitted when G1 results exist, they are
   not added to P1.

## 2. Unchanged
`prereg_amend_6.md` §0, §1.2–§1.4 (as applied to P2) and §2, and every reading of amendments 3–5.
