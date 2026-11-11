"""A1 WP2 statistical plants (arcs/audit/RUN_PLAN.md v3.1 §7, FROZEN sha256 16c60232...; RUN_PLAN_amend_1.md v2.1,
FROZEN sha256 8e06d60e...): P3a, P3b, P4, P5 (catch rate), P6, P7 (catch rate), P8 (survival counts), P11, P12
(statistical part), P22 (multiverse plumbing, R11), P24, P25, P26.

Material (§7 "Data"): synthetic maps only, built on each class's centroids (asdg.spatial.FieldGenerator) and on its
§3.1 matrix; the AHBA matrices, atlas info and centroids under artifacts/ahba, the GAMBA brain>body background and the
BrainSpan trajectories the frozen code reads, register_maps/mist64_classes.json, and amendment 3's frozen generator
arcs/audit/src/e3_align_plants.py (imported, never edited). No audit map is used.

Code path (§7): every claim a plant builds goes through the functions a1_audit.run's rows execute - run.prepare (the
§4 analysis-parcel rule, ClassContext.restrict, adapters.make_adapter), plant_mode.streams_screen (amendment 3's
plant-mode G6l), run.g_legs (verdict.collect_legs), verdict.assemble_verdict_a1, run.g_descriptors / descriptors -
through a Sources implementation (common.CaseSources, run.Sources' interface). The TSV-row dispatcher of run.py is not
used: a plant claim has no TSV row (see driver.py's docstring for the change run.py would need to host these plants
behind `--plant`).

Modules: common (ids, seed mapping, class contexts, the per-claim production calls, record compaction), criteria (the
§7 thresholds, re-derived from the tails §7 states and asserted at import), construct (the constructions), flaws
(the plant-only flawed legs of P25 (a)-(c) and P26, behind flags a real run refuses), p03 (P3a, P3b), p04, p05, p06,
p07, p08, p11, p12, p22, p24, p25, p26 (one module per plant), driver (CLI: one plant or `all`; DEV / official modes;
jobs, longest-first ordering, checkpoints, resume; per-plant JSON).

Every choice §7 leaves open is written in the code as "PLANT CHOICE (not in §7): ..." and collected in each plant's
output (`plant_choices`).
"""
