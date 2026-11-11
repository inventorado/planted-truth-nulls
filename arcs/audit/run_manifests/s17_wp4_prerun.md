# RUN_PLAN §17 analysis before WP4 (GENERATED from s17_wp4_prerun.json; do not hand-edit)

> RUN_PLAN.md:1706-1710: 'Any code change on a statistic path once a claim result exists (a crash fix included): 1. P0-P26 are rerun; 2. asdg-skeptic re-reviews before any further claim runs; 3. every completed row whose computation passes through the changed code is rerun; 4. both versions are reported, with the change, its commit and its reason.'

**Definition used.** statistic path = code that computes, selects or transforms a value entering a statistic, a p, a verdict or their inputs (map, set, matrix, parcels, seeds), OR that carries those values from the computation to the row record (dispatch, checkpoint save / load, payload-to-row assignment). Not a statistic path: a label or reading text, a recorded rule text, pacing (when to stop dispatching), hashing / provenance, output locations, plant or test scaffolding, a material-stage branch no completed row read.

**Classification.** CONSERVATIVE: the executor (pace.run_jobs and run._compute / _form_job / _form_finish) is on the statistic path; every computed WP3 row passes through it, so every computed row is rerun. The narrower reading (an executor that computes nothing and checks the key of every payload is not a statistic path) would rerun no row: an orchestrator decision (cost below).

| commit | module | function | statistic path | reason | completed WP3 rows |
|---|---|---|---|---|---|
| 221691a | pace.py | run_jobs | yes | the executor every computed task now passes through (replaces a3_port.run_pending in run._compute): dispatch, loky pool, checkpoint save / load and the key-to-payload assignment; a defect here could put one task's payload under another row | all computed rows of every pass |
| 221691a | pace.py | Pacer, seconds_of, load_estimates, block_estimate, read_pauses, write_pauses, unresolved, lifted, same_identity, Paused | no | pacing: decides when dispatching stops and records pauses; no value | none |
| 221691a | run.py | _compute | yes | restructured around pace.run_jobs; form rows joined to the phase-2 batch (their payloads now pass through it) | all computed rows of every pass |
| 221691a | run.py | _form_job (was _run_form_row), _form_finish, Run.form_store, execute (form branch) | yes | the gene-set-only form rows now computed in a pool worker and assembled from the checkpointed payload by _form_finish (was: computed in the parent); same form_task, inputs and seeds | the 5 computed Liu form rows (descriptor pass; rows 471, 472, 475-477) |
| 221691a | run.py | prepare (count_unit=PARCEL_COUNT_UNIT[rule]) | no | passes the rule text's unit only; the kept / dropped parcels are unchanged | label: the >= 2-donor rule text |
| 221691a | adapters.py | analysis_parcels (count_unit, PARCEL_COUNT_UNITS) | no | the recorded rule text names donors for the sensitivity rule; an unknown unit raises; parcels unchanged | label: 'finite y and >= 2 donors' in the 83 computed sensitivity rows |
| 221691a | run.py | r27_for_map, component_r27, COMPONENT_KINDS | no | R27 reading / label assembly (no statistic): a component record's reading | label: MOR-C1..C3 (rows 615-617) |
| 221691a | run.py | code_coverage, preload_pass_modules, PASS_MODULES | no | hashing / provenance | none |
| 221691a | run.py | block_estimates_for, arm_pacer, write_pause, pacing_summary, build_parser, validate, main | no | pacing and CLI | none |
| 221691a | reprice.py | (new module) | no | reads checkpoint timings, writes estimates | none |
| 221691a | r27_relabel.py | (new module) | no | relabels recorded rows (no statistic) | label: MOR-C1..C3 |
| 221691a | report_cells.py | (6 lines) | no | the §16 writer: assembly of recorded values only | none |
| e2610d5 | run.py | r27_verdict_rec, component_r27 (review B1, B2) | no | R27 reading of a descriptor-routed component row; the species-gradient label kept with a note | label: MOR-C3 |
| e2610d5 | r27_relabel.py | (B1, B2) | no | relabel of recorded rows | label: MOR-C1..C3 |
| 4aa058a, 09e93a9 | report_cells.py | (the §16 writer and its fixes) | no | assembly only (no statistic): it reads the row files | none |
| WP4 phase 1 | wp4_layout.py | (new module) | yes | the G2 loaders / readers / gated sets / reproduction wiring: on the statistic path of G2 rows (none computed yet); imported by every pass (run.preload_pass_modules) for L11's hash, but no ungated computation calls it | none (G2 only) |
| WP4 phase 1 | wp4_read.py | (new module) | yes | the G2 loaders / readers / gated sets / reproduction wiring: on the statistic path of G2 rows (none computed yet); imported by every pass (run.preload_pass_modules) for L11's hash, but no ungated computation calls it | none (G2 only) |
| WP4 phase 1 | wp4_sets.py | (new module) | yes | the G2 loaders / readers / gated sets / reproduction wiring: on the statistic path of G2 rows (none computed yet); imported by every pass (run.preload_pass_modules) for L11's hash, but no ungated computation calls it | none (G2 only) |
| WP4 phase 1 | wp4_sources.py | (new module) | yes | the G2 loaders / readers / gated sets / reproduction wiring: on the statistic path of G2 rows (none computed yet); imported by every pass (run.preload_pass_modules) for L11's hash, but no ungated computation calls it | none (G2 only) |
| WP4 phase 1 | wp4_repro.py | (new module) | yes | the G2 loaders / readers / gated sets / reproduction wiring: on the statistic path of G2 rows (none computed yet); imported by every pass (run.preload_pass_modules) for L11's hash, but no ungated computation calls it | none (G2 only) |
| WP4 phase 1 | wp4_material.py | (new module) | yes | the G2 loaders / readers / gated sets / reproduction wiring: on the statistic path of G2 rows (none computed yet); imported by every pass (run.preload_pass_modules) for L11's hash, but no ungated computation calls it | none (G2 only) |
| WP4 phase 1 | rbuild/r17.py | (new module) | yes | the G2 loaders / readers / gated sets / reproduction wiring: on the statistic path of G2 rows (none computed yet); imported by every pass (run.preload_pass_modules) for L11's hash, but no ungated computation calls it | none (G2 only) |
| WP4 phase 1 | run.py | _real_sources, _sources_cached ('real-wp4'), _write_repro (G2 branch), execute (verdict-pass repro loop condition) | yes | routes G2 rows to WP4Sources / wp4_repro; for gate none every branch returns exactly what it did | none (the ungated branch is unchanged) |
| WP4 phase 1 | run.py | Run.__init__ / header (--rerun-tag), build_parser, validate, RERUN_RULE | no | output location of a rerun and its label | none |
| WP4 phase 1 | run.py | PASS_MODULES, preload_pass_modules (the wp4 modules) | no | hashing coverage | none |
| WP4 phase 1 | fetch_extract.py | SheetDecl mode 'labelled', labelled_rule, _read_labelled, _check_target | yes | G2 extraction (Giacomel's sheets); a new branch no WP3 object used (WP3 rows read their saved objects) | none (G2 only) |
| WP4 phase 1 | wp3_decoder.py | run_decoder (key=), _gate | no | material-stage keys for Leyhausen; defaults unchanged; no completed row runs it at use | none |
| WP4 phase 1 | ahba_extras.py | build_perdonor_hcpmmp1, hcpmmp1_atlas_info, hcpmmp1_call | yes | R38's build (Pretzsch's R14 reproduction inputs); G2 only | none (G2 only) |
| WP4 phase 1 | privacy_wrap.py | RUNNER_FILES (wp4 file names) | no | print-rule vocabulary (file:line) | none |
| WP4 phase 1 | plants/driver.py | Invocation (--rerun-tag), build_parser, validate | no | output location of an official rerun | none |
| WP4 phase 1 | s17_compare.py, s17_launch.py, wp4_scratch.py, tests/* | (new) | no | comparison / launch / synthetic stand-ins / tests | none |

## Completed WP3 rows

| pass | computed (rerun) | no statistic (relabel only) |
|---|---|---|
| verdict | 83 | 32 |
| descriptor | 85 | 30 |
| sensitivity | 83 | 32 |

Expected label-only differences: verdict MOR-C1..C3 (rows 615-617): R27 component reading (221691a / e2610d5); already regenerated in results/a1_run/ungated/r27_relabel_MOR-C.json; sensitivity, 83 computed rows: the parcel rule text 'finite y and >= 2 donors' (was '>= 2 AHBA sample(s)'); kept / dropped parcels unchanged; no-statistic rows (32 / 30 / 32): rewritten by the rerun passes with their TSV status; no statistic

Compute: about 290 process-h, about 18-19 wall-h (§14: estimates may be off by about 2x); the narrower reading: about 35 process-h, about 3.5 wall-h (suite + P1 + plants)

§17 (2) puts asdg-skeptic's re-review before any further claim run; s17_launch --stop-after-plants allows plants -> review -> reruns. Run straight through, the reruns reproduce completed rows (no new claim); the orchestrator decides.
