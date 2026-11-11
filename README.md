# Calibrating gene-set nulls for imaging transcriptomics with planted truths: where coexpression-matched and spatial nulls fail, a fourth-corner fix, and a preregistered demonstration on autism claims

Archive of the code, frozen protocol, result files and manuscript for paper P1: Calibrating gene-set nulls for imaging transcriptomics with planted truths: where coexpression-matched and spatial nulls fail, a fourth-corner fix, and a preregistered demonstration on autism claims.
Author: Radoslav Lovecký (Arperon). Archived at https://doi.org/10.5281/zenodo.24130310; repository https://github.com/inventorado/planted-truth-nulls.

This is a curated release of one study (the "A1 audit" arc) of a larger private research repository. It was built
from git commit `0606369` (code and results) and `14a1d12` (manuscript) by
`arcs/audit/paper1/release/build_release.py`, with the policy in `arcs/audit/paper1/release/RELEASE_POLICY.md`.
Repository-relative paths are kept, so the paths written in the manuscript and in the result files resolve here.

## What is in the archive
| path | content |
|---|---|
| `paper/` | `p1_final.pdf`, `p1_final.md` (the submitted text), `refs.bib` (cited references only) |
| `arcs/audit/prereg.md`, `prereg_amend_1..7.md`, `FROZEN.txt` | the frozen preregistration, its seven amendments (amendments 2, 3, 5, 6, 7 are declared post hoc in their own text) and the freeze timestamps and hashes |
| `arcs/audit/RUN_PLAN*.md`, `claims_register.md/.tsv` | the run plan with amendments 1-5 and the register of audited claims |
| `arcs/audit/src/`, `src_register/`, `probes/regime/`, `src/asdg/` | the instrument, the audit pipeline (`a1_audit`), the planted-truth generators, the regime probe |
| `arcs/audit/results/` | result files (`e3_*`, `e4_*`), `a1_run/` per-row records of the ungated and G2 passes, source notes of data used |
| `arcs/audit/run_manifests/` | launch records and plant cases |
| `arcs/audit/register_maps/`, `register_sets/` | records of the audited maps and gene sets (see below) |
| `arcs/audit/paper1/figures/`, `tables/` | figure and table scripts and their outputs |
| `arcs/audit/paper1/release/` | how this archive was made: policy, allow-list, `build_release.py`, `verify_release.py` |
| `MANIFEST.sha256`, `RELEASE.json` | sha256 of every file; commits, date, counts and scan results |

## Reproducing the figures and tables
Python 3.13; package versions in `env/requirements.lock`. From the archive root, with the lock installed:

    python -X utf8 arcs/audit/paper1/figures/make_figures.py
    git init && git config core.autocrlf false && git add -A && git -c user.name=x -c user.email=x@x commit -qm snapshot
    python -X utf8 arcs/audit/paper1/tables/derive_numbers.py

`make_figures.py` asserts the sha256 of every result file it reads and rewrites `figures/fig*.pdf/png`.
`derive_numbers.py` reads the same result files and records, for each, the last git commit that touched it, and it
refuses files that are not committed: that is why the archive must be a git repository first (the `git init` line).
The recorded `last_commit` values then differ from the original ones; the derived numbers do not.
`python -X utf8 arcs/audit/paper1/release/verify_release.py --tree .` does exactly this in a scratch copy, imports every
module and compares the outputs with the shipped ones. The audit itself (`arcs/audit/src/a1_audit/`, launched through `launch.py` / `run.py`) needs the
third-party maps, which are not redistributed; the per-row outputs it produced are in `results/a1_run/`.

## Line endings
Do not let git or an editor normalise line endings: hashes recorded in the archive name the exact bytes. The repository
stores text with LF, but 13 result files were hashed (by `make_figures.py`, `derived_numbers.json`) in their CRLF form
and are shipped in that form (`RELEASE.json`, `eol_restored_to_crlf`). `.gitattributes` sets `* -text`; use
`git config core.autocrlf false`. `MANIFEST.sha256` (`sha256sum -c MANIFEST.sha256`) checks every file.

## What is not included, and why
* **Third-party published brain maps and the supplement tables the gene lists came from are not redistributed** (licences
  differ or are unclear). `register_maps/` holds identity records only: URL, commit or ETag, byte size, sha256 and listing date,
  plus a few small transcriptions of published figure panels (for example `buch_fig5h_grid.json`). `register_sets/` holds,
  per audited gene set, the derived HGNC symbol list (`members_hgnc`), the mapping rule and counts, not the source tables.
  The register records of Giacomel et al.'s shipped result tables (`gated_G2_GIA-C01`..`C18`, `GIA-MDD-C1/C5/C10/D10/U1`)
  carry the authors' per-gene values and are left out, because their repository has no licence; their sets computed here by
  running the authors' script (`GIA-C19`..`C24`, `GIA-MDD-DEG-*`) are included.
  To re-run the audit, download each map from the URL in its record and check the sha256.
* **Allen Human Brain Atlas** expression is public and is not redistributed; it is rebuilt with abagen.
* **No individual-level data** of any kind. The archive contains no subject-level table. One public supplement (Pretzsch
  et al., Supplement 2) also contains per-participant tables of a cohort with controlled access (EU-AIMS LEAP): only its
  group-level eTable 13 loadings were extracted, the per-participant sheets were inspected by header only and never used,
  and the file was then deleted; none of it is here. Data manifests from other lanes of the wider programme (for example
  `abide1_pcp_SOURCE.md`) describe downloads that no analysis in this paper uses.
* `src/a1_audit/rbuild/logs/` keeps the R image's build and session logs, without the deparsed GPL source of GeneOverlap.
* Run records carry the authors' machine name (`"node"`) as provenance.
* **Gate G1 / the third release batch (196 population units) was not run.** Its material, run plan amendments 6-10 and
  work package 5 are not in the archive, and no number in the paper depends on them.
* The programme's literature notes, working notes on single papers, session handoff and event logs, and the draft with
  its internal provenance comments are internal and not included.
* Local absolute paths (`D:\...`, `E:\data\...`) remain in launch records and logs as provenance strings; they point to the
  authors' machine and do not resolve here.

## Licence
Code: MIT (`LICENSE`). Text, protocol, results, figures: CC BY 4.0 (`LICENSE-DOCS`). Third-party material is under its
owners' terms. Cite as in `CITATION.cff`.
