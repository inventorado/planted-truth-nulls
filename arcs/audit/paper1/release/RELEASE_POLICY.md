# P1 release policy

What goes into the public archive of paper P1 ("Calibrating gene-set nulls for imaging transcriptomics with planted
truths") and what never does. Enforced by `build_release.py`: the allow-list `release_files.txt` is expanded, then a
hard deny list is applied to the expansion and the build refuses on any match. Everything is read from git at a named
commit, never from the working tree.

## Included
| what | why |
|---|---|
| `prereg.md`, `prereg_amend_1..7.md`, `prereg_review_2026-09-23.md`, `FROZEN.txt`, `RUN_PLAN.md`, `RUN_PLAN_amend_1..5.md` | the preregistration and every amendment are the evidence that the design was fixed before the results; the paper says the deposit is the first public timestamp |
| `claims_register.md/.tsv`, `claims_register_tsv_build.py`, `register_freeze_manifest.json` | the register of audited claims and the freeze record the audit rows are defined by |
| `arcs/audit/src/**`, `src_register/**`, `probes/regime/**`, `src/asdg/**`, `env/requirements.lock` | the instrument, audit pipeline and plant generators: the code that produced every number |
| `register_maps/**`, `register_sets/**` (minus G1) | identity records of the audited maps (URL, size, hash, listing date) and the HGNC symbol lists of the audited gene sets; the audit cannot be checked without them |
| `results/*`, `results/a1_run/**`, `results/data_manifests/*_SOURCE.md` | the result files the paper cites, with per-row verdict/descriptor/sensitivity records and run logs |
| `run_manifests/` (plants, launch, R22_panther, repricing and S17 check of released batches) | launch records and plant cases: run provenance behind the tables |
| `paper1/figures/**`, `paper1/tables/**` | figure and table scripts with their committed outputs; `verify_release.py` re-runs them and compares |
| `paper/p1_final.md`, `p1_final.pdf`, `refs.bib` | the submitted text (provenance comments and status line stripped), its PDF, the cited bibliography only |

## Excluded, with the reason
| what | why |
|---|---|
| `arcs/audit/register_work/` | per-paper working notes on third-party publications; not a result, may quote supplements |
| `literature/` (except the generated `paper/refs.bib`) | the programme's reading notes and search logs; internal |
| `run_manifests/material/` | records of failed or aborted downloads and a deletion request to a third party; internal incident record |
| any path component containing `G1` (`run_manifests/G1/`, `register_sets/gated_G1_*`) | gate G1 (third release batch) was not run; its material must not be mistaken for a result |
| `wp5*`, `WP5_*`, `RUN_PLAN_amend_6..10`, `probes/spreg_raise/` | work package 5 / G1 build, its amendments and probes: the follow-up paper's unfinished material |
| `run_manifests/reprice_wp5.json/.md` | G1 cost repricing, one of the two `wp5` files at the paper's commit. No released code imports or reads it (`reprice.py` only writes it). Cited only in the draft's internal provenance table, which is stripped. Amendments 6 and 7 mention it, so those references dangle |
| `ARC.md`, `NEXT_SESSION.md`, `EVENTS.jsonl`, `ENTITIES.jsonl`, `CLAUDE.md`, `.claude/` | the orchestration layer: session handoff, event log, agent configuration |
| `arcs/audit/paper1/draft.md`, `OUTLINE.md`, `build_pdf.py` | the draft carries internal status, provenance comments and `src:` markers; the stripped text is released instead |
| `artifacts/`, `env/venv*` | long-job run artifacts and the Python environment: large, machine-specific, re-creatable |
| `results/data_manifests/abide1_pcp_MANIFEST.tsv` | per-participant ABIDE file listing (subject ids) |
| `arcs/replication`, `explore/`, `src/data`, `src/tests`, `docs/` | not part of P1 |
| `*.vcf*`, `*.bam`, `*.cram`, `*.fastq*`, `*.h5ad`, `*.nii*`, `.env` | individual-level genomic or imaging data, or secrets: never in a repository (programme rule 4) |
| any `.tsv/.csv` whose header has a subject/participant/sub_id/FILE_ID column; the LEAP per-participant supplement anywhere | person-level rows; only that supplement's group-level eTable 13 was extracted, its per-participant sheets were read by header only, never used, and the file was deleted |

## Third-party material
Published brain maps, and the supplement tables the gene lists were taken from, are not redistributed. `register_maps/`
holds identity records (URL, commit or ETag, byte size, sha256, listing date) and a few small transcriptions of published
figure panels. `register_sets/` holds, per gene set, the derived HGNC symbol list with the mapping rule and counts, not
the source tables. AHBA expression is public and is rebuilt with abagen; none is redistributed.

## Content scans (every released file; results in `RELEASE.json`)
* credential strings (names of API credentials, token assignments, GitHub and OpenAI-style key prefixes, password assignments, `.env` content; the exact regexes are `SECRET_PATTERNS` in `build_release.py`) and the operator's e-mail address: refuse.
* absolute local paths (`D:\`, `E:\data`, `C:\Users\`): counted per file and reported, not refused (provenance strings
  in launch records and logs).
* a person-id key in JSON/JSONL (`participant_id`, `subject_id`, `SUB_ID`, `FILE_ID`): reported for review.

## Placeholders
`{{DOI}}` and `{{REPO_URL}}` in generated files; `--final` refuses to finish while one remains.

## Gate self-test
Every run first plants offenders (a `G1` path, a `.vcf`, a subject-id header, a token, the e-mail) and asserts the
deny and scan functions catch each one; a gate that cannot fail aborts the build.
