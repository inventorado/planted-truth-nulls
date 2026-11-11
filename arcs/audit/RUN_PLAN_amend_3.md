# RUN PLAN AMENDMENT 3 — A1 `audit`: readings WP3 phase 1 found unpinned (pre-exposure)

> **Status: v2.1, DRAFT; NOT frozen.** v2 was written 2026-10-11 at HEAD 3900e59 (an exploration-lane commit; the A1
> code at HEAD is 629ea9d's, the WP3 phase-1 commit), and v2.1 the same day at the same HEAD. The orchestrator checks
> the v2 → v2.1 diff and freezes. The A1
> code cited is at 629ea9d (git blob ids): `wp3_layout.py` e5ec922a, `wp3_material.py` 9e66dfa6, `wp3_repro.py`
> 67159ab6, `real_sources.py` e4f351d5, `fetch_extract.py` 9092413b, `forms.py` adc5aae9, `run.py` 1864c000,
> `tests/test_wp3_phase1.py` 7220f989. The working tree holds uncommitted edits to the A1 code by another worker; this
> author did not read them, and every code line cited is 629ea9d's.
>
> This amends `RUN_PLAN.md` v3.1 (FROZEN, sha256 16c60232…) as amended by `RUN_PLAN_amend_1.md` v2.1 (FROZEN,
> 8e06d60e…) and `RUN_PLAN_amend_2.md` v2.1 (FROZEN, acdb1290…).
> - **Readings R44–R50** are in the plan's §5 format: **Text** → **Reading** → **Why now** → **Checks / fallback**.
>   Each shows the options, why the one chosen is the faithful one, and whether it moves any count.
> - **§8** classifies every reading of the WP3 phase-1 report (U-W3-1 … U-W3-21) and its listed risks as "pinned here"
>   or "implementation choice, no pin needed", as amendment 2 §8 did. **§8.1** records the Moreau quarantine and the
>   orchestrator's decision on the clone.
> - **"Changed"** lists every departure from a frozen text or frozen code, each declared; **"Not changed"** lists the
>   rest.
> - **§9** keeps v1's questions with the orchestrator's answers. **§10** answers the review of v1, finding by finding.
>
> No registered definition changes (`claims_register.md:1102-1103`), and no frozen file is edited. A cell's status
> changes only where a frozen rule already provides it: LIU-T4 / T5, fail-closed (R46). A registered comparator that
> cannot be computed reads "not computable (<why>)", as R14 and R28 do (`RUN_PLAN.md:748, :1014, :1019`). It never
> reaches the cell's status.

## Versions
| version | date | written at | sha256 | review |
|---|---|---|---|---|
| v1 | 2026-10-11 | HEAD 629ea9d | 495443100973b23f6df357b51c32fd84b91c68695be8aefbf3c9d7c3fcebd7ae (700 lines) | asdg-skeptic: **refuted** (1 A conditional / 9 B / 11 C). Its safety claims held: pre-exposure; no registered definition changed; statuses change only for LIU-T4 / T5, fail-closed |
| v2 | 2026-10-11 | HEAD 3900e59 (A1 code 629ea9d) | e22861c2ef223a0545a1a19bf5a9bc87b2a21bdf11992618089038893b6b9af5 (997 lines) | answers every finding of v1's review (§10); the orchestrator's answers to v1's §9 are written in (§9). asdg-skeptic re-check: **refuted narrowly** (0 A / 2 B / 9 C). Every v1 finding fixed or answered (C10's premise withdrawn); the waits, the 429 handling, the Last-Modified label and the cross-tool design accepted |
| v2.1 | 2026-10-11 | HEAD 3900e59 (A1 code 629ea9d) | stated at hand-off (a file cannot carry its own hash) | **v2.1: the re-check's B1–B2 and C1–C8; not re-read by the reviewer before freezing** (the orchestrator checks the diff). C9 is recorded as a residue for WP4, with no change here (§10.1) |

## 0. Authority, exposure, what was read
- **Authority:** RUN_PLAN §18: "Readings found missing later go to a frozen amendment of this plan … **Before any
  claim result exists**, such an amendment is pre-exposure for the material it bears on, provided that material is
  not yet opened" (`RUN_PLAN.md:1806-1808`).
- **Pre-exposure.**
  - No claim result exists. At HEAD 3900e59 there is no `arcs/audit/results/a1_run/`, no
    `register_maps/post_freeze/`, `register_sets/post_freeze/` or `run_manifests/material/`, and no
    `artifacts/audit/wp3/` (existence checks only, re-run for v2 on 2026-10-11). The official plant battery exists
    (a7b6e2a); plant outcomes are not claim results.
  - The WP3 phase-1 report states that phase 1 ran on synthetic stand-ins and that phase 2, which opens the ungated
    material, has not run (report :1-29, :98-105).
  - **The material these readings bear on has not been opened by this audit since the register froze** (3d1abe3,
    2026-09-30T09:05:47+02:00): Segura's two NeuroVault images and their decoder outputs; Segura MOESM2 pp. 38–39
    (Tables S6, S7); Liu's Supplementary Data workbook (SD3, SD4, SD7); Moreau's workbook. This rests on the WP3
    report and the existence checks above.
  - **Two exceptions, declared:**
    - The WP3 worker read BrainSpan's files and the GO, HGNC and GAMBA reference files to test its loaders (report
      :93-94: trajectories equal to the frozen reader; no claim statistic). R50 bears on the identity of these
      reference files. It uses none of their content, only sha256s recorded before the freeze.
    - **This author (v2), on the orchestrator's instruction (review B9),** read the two declared sample columns (age,
      structure acronym) of BrainSpan's `columns_metadata.csv`:
      - identity was checked first: sha256 = the pre-freeze pin 995a8e75…;
      - the columns were read with pandas `usecols`, as `wp3_genes.brainspan_frames` does, so the donor columns never
        entered a frame;
      - only counts were printed (`…\scratchpad\amend3\b9_pair_count.py`).

      R48 uses those counts. No SD3 cell is involved.
- **Exposure declaration (adds to RUN_PLAN §9, F2).** None of R44–R50 touches an ENIGMA-derived (G2) cell. LIU-T3 is
  untouched; T4 / T5 use AHBA samples and SD7, not an ENIGMA map.
- **The drafts are part of the register (review B2).**
  - "**The drafts are incorporated by reference** at the sha256 of §8: every per-claim field a draft gives (quote,
    location, published value, map and file hashes, set and its source, … material list) is part of this register
    unless a decision below changes it" (`claims_register.md:59-61`).
  - The three drafts read here hash to §8's values, both on disk and as LF git blobs at HEAD (checked 2026-10-11):
    - `liu2026spatiotemporal.md` fc2a25d4… (`:2210`);
    - `moreau2020mutations.md` 5b5a6a1e… (`:2212`);
    - `segura2024symptommapping.md` a3818994… (`:2220`).
  - So SD7's file hash (R46 (a)) and the Segura derived files' hash prefixes (R47) are registered fields, not mere
    notes.
- **Pre-freeze exposures that bear on these readings** (`claims_register.md:120-160`):
  - item 1 (`:121-124`): Segura Tables S4, S6, S7 (R47); Liu SD4 / SD10 ASD rows and the first data row of every SD
    sheet, SD7 included (R46, R48, R49);
  - item 2 (`:128-132`): the asdg-lit recomputation in `literature/notes/liu2026spatiotemporal.md` and A1's R2 ρ's.
    The literature note also records SD7- and SD3-derived values (below);
  - item 6 (`:142-145`): the NDA GUID printed while a worker read the sheet names of Segura's Table S8 workbook
    (MOESM3). R47 reads MOESM2 only, and no sheet names;
  - item 8 (`:148-152`): the approved re-read of Segura Table S7; the first three lines of Segura MOESM2 pp. 37–40
    (Table S5 title and group sizes; Table S6 header and first gene row); NeuroVault file-size metadata; the
    listing-level identity probes (`IDENTITY_prefreeze.json`) (R44, R45, R47).
- **Read by this author:**
  - **for v1:**
    - this programme's `CLAUDE.md`;
    - RUN_PLAN §0, §1 (L14), R10, R13, R14, R18, R21, R22, R27, §8, §10 and §16–§18; amendment 2 in full; amendment 1
      `:1-90` and its section list;
    - `claims_register.md:104-175, :326-332, :810-825, :1085-1104, :1200-1212, :1240-1246, :1258-1276, :1425-1440,
      :1655-1690, :1764-1785`;
    - TSV rows 1–4, 9–11, 80, 470–478 and 615–619, read by script (`map`, `set_S`, `T`, `direction`, `status`,
      `reproduction`, `published_value_and_location`, `inference_level`, `notes`, `verdict_counted_in_m`,
      `headline_population`, `focal`);
    - the WP3 phase-1 report (105 lines);
    - A1 code at 629ea9d: `wp3_layout.py`, `wp3_material.py` and `wp3_repro.py` (all); `real_sources.py:1-90,
      :375-476`; `forms.py:552-935`; `fetch_extract.py:1-80, :426-452, :990-1135`; the 629ea9d diffs; `identity.py`
      and `tests/test_wp3_phase1.py` by grep;
    - frozen register code and objects: `src_register/s_extract.py:1-40, :85-110, :149-195, :360-420`;
      `src_register/fetch_util.py:1-80`; `register_freeze_manifest.json` (file list, five entries' hashes);
      `register_sets/SEGURA_S7_TERMS.json` (header fields and its first two terms); `register_sets/segura_s4.json`
      (source block and counts; no member); `register_maps/IDENTITY_prefreeze.json` (header; the identity fields of
      the three ungated objects and of LIU-T3's two G2 maps);
    - pre-freeze notes: `register_work/liu2026spatiotemporal.md` (all), `register_work/segura2024symptommapping.md`
      (all), `register_work/moreau2020mutations.md:1-60`, `literature/notes/liu2026spatiotemporal.md` (all),
      `arcs/audit/results/data_manifests/brainspan_SOURCE.md` and `gamba_SOURCE.md` (committed 5e198b7);
    - third-party code fetched by plain curl (no identifier sent): NeuroVault's server code at 9a42434e and rstatix
      `R/t_test.R` at master 50881ccc.
  - **for v2:**
    - the orchestrator's summary of the review and its answers;
    - the reviewer's scratch folder (its listing and `logscan.py`; no review text is stored there);
    - `claims_register.md:50-66, :2190-2230`; RUN_PLAN `:765-806` (R16) and `:1010-1020` (R28);
      `src_register/privacy_guard.py:262-275, :300-326`; `explore/discovery/guard.py:14-58, :104-175, :238-270` (C10);
    - a grep of the frozen register JSONs and `s_build.py` for paths inside the Moreau clone;
    - `wp3_material.py:175-182` at 629ea9d (`_entrez`);
    - package versions only: pdfplumber 0.11.10 and matplotlib 3.11.2 in `env\venv`, PyMuPDF 1.27.1 in
      `C:\Python313` (user site);
    - BrainSpan's `columns_metadata.csv`, its two declared columns, counts only (above).
- **Values seen by this author (complete list; review C9).** None is used except as stated per reading.
  - **Published values of the papers:**
    - **Segura:**
      - OR 1.6, p .0002, 107 of 1,519; OR 1.7, p .2, 7,572 (TSV rows 1–2; draft `:61, :80, :106-107, :117`);
      - Table S7's seven named rows (TSV rows 3–9; draft `:132-138`).
    - **Liu:**
      - SD4's ASD p / p.adj (TSV 472, 475–477; draft `:49`; note `:29`);
      - SD10's ASD module ORs and P's (draft `:53`; note `:34`);
      - the ENIGMA ρ's of eight disorders and their P_FDR (note `:32`; TSV 478 for ASD);
      - VR-N1's P .257 (TSV 470).
    - **Moreau:**
      - 24.2 % / 43.2 % / 35.3 %, S4.1's 24.223 / 43.244, the random-gene p's .1782 / .8211 and median-r p's .31 / .36
        (TSV 615–617; register `:1776-1779`);
      - 14.5 % and p .2928 (TSV 617 notes);
      - MVP / KIF22 / AIFM3 / TBX1 / P2RX6 r and percentiles, and the tail p's .03 / .04 (TSV 618–619).
    - **Register's other targets, seen in the lines read:** VR-E1…E4's NES and LV1 p .696 (`claims_register.md:1655-1657`);
      the printed values 0 … .61 of Buch Fig. 5h (`:148`).
  - **Pre-freeze statistics:**
    - register item 2's ρ's (`claims_register.md:128-132`: e4_r2 −.022 / −.053 / .104, eda33ab −.1505 / .4125 /
      −.0534, p .252 / .073 / .423, MDD .5287 / .5466 / .5310);
    - the literature note's recomputations:
      - ENIGMA ρ −.349 / −.51 / +.08 / −.04 (`:50`; TSV 478);
      - the other traits' ρ with the ASD map (−.34, −.30, −.28, −.27; `:50`);
      - SD3-derived stage means of r (.705, .721, .663, .680, .662, .681, .688; GWAS-set r .42–.45; `:30`);
      - SD7-derived summaries: cortical r .422–.445, SD .005; lingual .445, cuneus .442; all-region SD .018; pallidum
        .343, thalamus .379 (`:32, :49`);
      - random-set r .02–.16 and P .019 (`:61`); the highest Jaccard .15 (`:31`).
  - **Facts of carriers:**
    - Segura's maps: grid 45 × 54 × 45, 4 mm; non-zero voxels 17,995 / 19,033; NeuroVault coverage 62.5 % / 66.2 %;
      the paper's mask of 10,664 voxels (Segura draft `:40-43`);
    - Moreau's block: "4,096 numeric, 0 NaN" (Moreau draft `:34`);
    - `IDENTITY_prefreeze.json`'s sizes, sha256s, git blobs and Last-Modified dates;
    - Liu's SD7 structure: 78 L/R rows; 32 cortical labels with a value; entorhinal and pericalcarine NA; 7 aseg names
      (draft `:50-51`; note `:15`);
    - SD3: "524 unique sample labels + 38 footnote rows" (draft `:48`);
    - SD4's n's: frontal 164, thalamus 29 (draft `:49`).
  - **Reference data:**
    - BrainSpan: 52,376 × 524; 42 donors; the 31 ages and 26 acronyms listed (`brainspan_SOURCE.md:12-15`);
    - GAMBA: 20,949 rows, flag sums 2,711 / 8,989 / 18,405, and the counts given in its notes (`gamba_SOURCE.md:16-20`);
    - Segura's Table S4 counts: 1,046 raw / 1,045 HGNC / 1 drop (`segura_s4.json`);
    - the MIST64 counts in TSV 615–619's notes.
  - **Computed by this author:**
    - B9's counts (R48);
    - the ratio p.adj / p of TSV 472 (R49).
- **Not opened by this author:**
  - any carrier, map, NeuroVault image, decoder output, supplement or supplement sheet (Segura MOESM2 and MOESM3; Liu
    SD1–SD15; Moreau's workbook);
  - the pre-freeze derived files under `E:\data\asdg\segura2024symptommapping\derived\` and
    `E:\data\asdg\register_sets_src\…\extract\`;
  - anything else under `E:\`, and no listing of it: the only E: file opened was BrainSpan's `columns_metadata.csv`
    (above);
  - the exploration lane's exposure-bearing files (workflow wf_a992ecba-de5). A listing of this session's scratchpad
    showed other files' names only;
  - the values of any `results/*.json`; any G1 or G2 material.
- **Evidence:**
  - `…\scratchpad\amend3\tsv_rows.py` (TSV fields);
  - `…\amend3\b9_pair_count.py` (B9);
  - `…\amend3\nv_9a42434e\` (NeuroVault's `urls.py`, `views.py` and `ahba.py` at 9a42434e, hashed);
  - `…\amend3\rstatix_src\t_test.R` (hashed).

## R44. The three ungated carriers: the existing local copies, held to every pre-freeze reference (U-W3-1)
- **Text:**
  - "**Material and identity at use (local sha256 vs `IDENTITY_prefreeze.json`).** Segura 790618 (71,440 B,
    802b4b6b…) and 781986 (75,117 B, 0c476e8e…); Moreau `Supplementary_Table_S1.xlsx` (468,991 B, c947112d…, blob
    7a8b62be…), declared sheets `1_16p11.2Del` and `3_22q11.2Del` only" (`RUN_PLAN.md:1420-1423`).
  - "**Fetch (ungated).** NeuroVault decoder outputs for 790618 and 781986 (R22)" (`:1428`).
  - §8 step 1 fetches "with the frozen `src_register/fetch_util.get` … `SOURCE.md` … under `E:\data\asdg\<key>\`";
    step 2 compares the R13 fields "against `IDENTITY_prefreeze.json`" (`:1208-1211`).
  - "byte size alone otherwise (NeuroVault serves no ETag); a copy already on disk is checked by its sha256"
    (`claims_register.md:1093`).
  - TSV rows 1–80 and 615–619 name the files' sha256 (row 1: "sha256 802b4b6b…"; row 615: "(sha256 c947112d…)").
  - `IDENTITY_prefreeze.json` (frozen, 6cbde63e…) gives each object a "local file already on disk (hashed only, not
    parsed)" probe (path, size, sha256, git blob). It also gives NeuroVault's metadata size and HEAD Content-Length for
    the images (71,440; 75,117) and the GitHub tree entry for Moreau (blob 7a8b62be…, 468,991 B).
  - FE14 / FE15 (`fetch_extract.py:70-75`): a copy under another name is used only if it is pinned.
- **Options:**
  - (A) the local copies the frozen identity record names;
  - (B) a new download into `E:\data\asdg\<key>\carrier<ext>`, then identity.
- **Reading: (A).**
  - The three carriers are used as found, at the paths of their "local file" probes (FE15). **No GET is made for any
    of them (review B7).**
  - The only network request that touches one of them is R45 (e)'s single HEAD of each image's NeuroVault file URL. No
    request touches Moreau's workbook.
  - **Identity at use: every reference in the object's record must hold:**
    - the copy's sha256 equals the probe's;
    - its size equals the probe's size and the remote size (NeuroVault's metadata and HEAD for the images; the tree
      entry for Moreau);
    - its git blob equals the probe's, and for Moreau also the tree blob 7a8b62be….

    Any failure reads "not auditable (map changed)" (`RUN_PLAN.md:1703-1704`) for that object's rows: Segura rows 1–80
    by image; MOR-C1…C3 and MOR-T1 / T2.
  - These checks run after every reference and pin check of R50 (review B8).
  - The path is recorded by the sha256 of its string only (FE15). Its file-name part is the server's name for the
    carrier, so §8's print rule applies.
- **Why faithful:**
  - §10 lists the decoder outputs alone under "Fetch (ungated)", and it states identity at use as "local sha256 vs
    `IDENTITY_prefreeze.json`". Only the local copies have a local sha256 in that record.
  - (B) adds a download whose remote identity is its size alone (`claims_register.md:1092-1093`), and the new copy would
    then be held to the same sha256 anyway.
  - For Moreau, (B) would make a second copy of a workbook that §8.1 quarantines.
- **Why now:** phase 2 has not run; this audit has opened none of the three.
- **Counts:** none move. Under either option an identity failure reads "not auditable (map changed)" (§17). For
  MOR-C1 / C2 (in m, component level) that changes only the status composition, never a survival.
- **Checks (P19 / P20 extension, functional, in `tests/`; the `plants/` blobs of amendment 2 §8.1 are unchanged):**
  - a stand-in copy whose sha256 differs, one whose size differs from the remote size, and a Moreau stand-in whose git
    blob differs are each caught as "map changed";
  - a copy of the same bytes under another path is not picked up;
  - **the network mock records zero GETs for the three carriers, exactly one HEAD per image file URL, and no request
    for Moreau** (B7).

## R45. The NeuroVault decoder: URL, format, columns, the decoded list, "unavailable", retries and the fallback (U-W3-3, -4, -13, -14)
- **Text:**
  - R22: "The decoder output for 790618 and 781986 is fetched with `mask=full`; it is ungated" (`RUN_PLAN.md:887`);
    "If the decoder is unavailable, the fallback is the per-donor recipe on V-AAL (R14's rule)" (`:900`); "Descriptive
    reproduction only; no count moves" (`:901`).
  - "Reproduction descriptive (NeuroVault decoder, `mask=full`, FDR q < .05, both signs; OR vs 1.6)"
    (`claims_register.md:1437-1438`).
  - "the paper's decoded list re-derived by its own rule — the NeuroVault decoder output for the paper's image …, else
    amendment 4 §2's per-donor parcel recipe, which is also the fallback if the decoder is unavailable — then the
    paper's enrichment test (its stated significance threshold …); OR, p and Jaccard with any published list are
    reported" (`:328-332`).
  - R14's general rule: where the paper decoded voxel- or sample-wise (Segura among them), "the recipe uses the claim's
    analysis class, labelled 're-derived (per-donor parcel recipe, <class>), not the decoder'" (`RUN_PLAN.md:744-747`).
  - Registered draft fields (`register_work/segura2024symptommapping.md`, incorporated, B2):
    - the decoder path `/images/790618/gene_expression/json?mask=full` (`:22`);
    - the paper's decoding, "FDR q < .05, **positive and negative t both kept**" (`:80-82`);
    - the 20,787-gene background ("only the count is stated (Supplement §6, repo `ns_gex_background = 20787`)",
      `:32`).
  - `IDENTITY_prefreeze.json`: each image's `file_url`, Content-Length and Last-Modified (790618: 71,440 B, "Thu, 12 Jan
    2023 15:57:34 GMT"; 781986: 75,117 B, "Wed, 18 May 2022 10:08:20 GMT").
- **Facts (NeuroVault's server code, `NeuroVault/NeuroVault` at 9a42434e50b33af8b8967dbc792cde202df4d8ba = master on
  2026-10-11, committed 2025-10-28T18:50:05Z):**

  | file | sha256 | git blob |
  |---|---|---|
  | `neurovault/apps/statmaps/urls.py` | 31c558a929822dfa62d0342caff70591d621187c4a6a53648b137cf506532203 | e8fc8b9cdc74ad3a3ab0d08fb8055f6bb71d2fd4 |
  | `neurovault/apps/statmaps/views.py` | d43d05f020bf601fdc9751344d9baf785b3221f4c89edc8663c14d8c4ab565b9 | d19c6fc63d04365833603ff88402c54dde899517 |
  | `neurovault/apps/statmaps/ahba.py` | 3af0ea2a62fd38e4fff5d2ef7a9e77ee4c51c5d723015ed241ef87b8c8edee1b | 176c9ec3aa46b08bd1db593b3b064c675c68a3eb |

  - `urls.py:348-350`: `^images/(?P<pk>\d+)/gene_expression/json$` → `gene_expression_json`.
  - `views.py:1817-1830`:
    - a thresholded image raises 404;
    - **the decoder reads the image's cached reduced representation**: it is (re)built only if absent or its file is
      missing (`:1822-1825`);
    - `mask = request.GET.get('mask', 'full')`, then `calculate_gene_expression_similarity(map_data, mask)`;
    - `to_dict("split")` with `"index"` deleted, rendered by DRF's `JSONRenderer` (`:1342-1350`).
  - `ahba.py:16-72` works per donor: it z-scores, takes the least-squares slope of each gene's sample expression on the
    map, then `ttest_1samp` over donors, then BH (`fdr_bh`) over all rows. The columns are written in this order
    (`:69-70`): `gene_symbol`, `entrez_id.1`, `gene_name`, `t`, `p`, `p (FDR corrected)`,
    `variance explained (mean)`, `variance explained (std)`.
  - **Correction:** `wp3_layout.DECODER_SOURCE` (`wp3_layout.py:67`) pins `ahba.py` as 3af0ea2a62fd38e4**ffe5**d2ef….
    The file at 9a42434e hashes to 3af0ea2a62fd38e4**fff5**d2ef… (one hex digit); `urls.py` and `views.py` match.
- **Reading:**
  - **(a) URL.** `https://neurovault.org/images/{id}/gene_expression/json?mask=full`, id ∈ {790618, 781986}, fetched
    by the frozen `fetch_util.get` (one curl, 900 s, no identifier sent).
  - **(b) Response format.** A JSON object, parsed by Python's `json.loads` (which accepts `NaN` / `Infinity`), with a
    key `columns` (a list of strings) and a key `data` (a list of rows, each a list as long as `columns`). Other keys are
    ignored and counted.
  - **(c) Declared columns, by exact text:**
    - required: `gene_symbol` and `p (FDR corrected)`, each exactly once;
    - optional: `entrez_id.1`, `t` and `p`, each at most once, used when present;
    - every other column is ignored, and its count and the sha256 of the whole column list are recorded;
    - the record is labelled "column list as NeuroVault 9a42434e's `ahba.py`" iff the list equals `ahba.py:69-70`'s
      eight texts in order, else "column list differs from NeuroVault 9a42434e (declared columns found)".
  - **(d) The decoded list. It follows `wp3_material._entrez` (629ea9d `:175-182`), which this reading adopts as
    written (review C11).**
    - An `entrez_id.1` value is an Entrez id iff it is one of:
      - an int that is not a bool;
      - a finite float with an integral value (written as its integer);
      - a text that is digits after stripping (`str.isdigit`).

      Anything else is no id.
    - A row's gene is the HGNC symbol of that id when it names one approved gene, else of `gene_symbol` through
      approved → previous → alias (exact). This is the S-build's "id given by the source, else symbol" rule
      (`wp3_genes.py:7-11`). Rows that cannot be mapped are dropped and counted.
    - A row is decoded iff its q is a finite number **< .05** (strict). The sign of t is not used (both signs); when
      `t` is present, the counts by sign are recorded.
    - A gene is in the list iff **any** of its rows is decoded. This is the same as "min q < .05". Genes with more than
      one row are counted.
    - A row whose q is null, non-finite or non-numeric is not decoded and is counted.
  - **(e) Unavailable, and the fallback.** The decoder of an image is **unavailable** iff any of these holds:
    - **Size probe (once per image per run, before that run's first GET):** the HEAD of the image's NeuroVault
      `file_url` returns a Content-Length different from the pre-freeze record (71,440 / 75,117).
      - The decoder computes on NeuroVault's copy, which would then not be the registered map. If no size is returned,
        the fetch proceeds and the record says so.
      - The HEAD's Last-Modified is recorded and compared with the pre-freeze value. A difference is **labelled** ("the
        NeuroVault image's Last-Modified differs from the pre-freeze record") and not refused; the register's identity
        fields are size, blob, MD5 and sha256, not dates (`claims_register.md:1090-1093`).
      - **Declared blind spots (review C1):** equal size does not prove equal bytes. The decoder also reads NeuroVault's
        **cached** reduced representation (`views.py:1822-1825`), which a replaced file need not refresh and which no
        request from outside can see.
      - The check reuses `identity.size_probe`, which the code applies to R16's tarball against its pinned size
        (`fetch_extract.py:1012-1016`). R16's own text records Content-Length and Last-Modified (`RUN_PLAN.md:771,
        :778`) and states no size refusal, so this refusal is this amendment's own (review C1).
    - **GET finally refused** (no retry):
      - an HTTP status other than 200, 429 or 5xx;
      - an HTML page with status 200;
      - three transport failures, counted across runs (f).
    - **Declared read refused:** (b) or (c) is violated, a row has another length, or no row carries both an HGNC gene
      and a finite q.

    Then R22's fallback applies: R14's per-donor recipe on V-AAL (`RUN_PLAN.md:744-748`).
    - It uses the claim's analysis parcels with a finite re-parcellated value and the six WP2 per-donor V-AAL matrices
      (§3.1 settings).
    - Per gene and donor it takes the OLS slope over that donor's parcels with samples (a donor with < 3 is dropped),
      then a one-sample t over donors, then BH across genes.
    - A gene is decoded at **q < .05, either sign**: Segura's own threshold ("its own rule",
      `claims_register.md:329-331`), not Pretzsch's .01. Genes are mapped by the S-build's HGNC rule.
    - The record is labelled "re-derived (per-donor parcel recipe, V-AAL), not the decoder", with the refusing stage.
  - **(f) Attempts, retries, and decided once (orchestrator's answer to Q4; reviews B8, C2; re-check B1, B2, C5).**
    - **How a failure is classified (in memory; no message text is stored; C5).** `fetch_util.get` raises in three
      ways:
      - `subprocess.CalledProcessError`, a non-zero curl exit; its `returncode` is the exit code
        (`fetch_util.py:39-43`, `check=True`);
      - `RuntimeError` for a status other than 200, with the message "HTTP <code> for <url>" (`:59-61`); the code is
        parsed from the message in memory;
      - `RuntimeError` for an HTML page (`:62-64`).

      Only the class name, the exit code or HTTP status code, the stage and the raising line are recorded.
    - **Transport failure: a whitelist (re-check B2).** It is exactly one of:
      - curl exit 6 (resolve), 7 (connect), 18 (a truncated body), 28 (timeout), 35 (TLS handshake), 52 (empty reply),
        55 (send error) or 56 (receive error);
      - HTTP 429;
      - HTTP 5xx.
    - **Any other non-zero curl exit stops the stage for the operator and consumes no attempt.** Examples are 2 (init),
      3 (malformed URL), 23 (write error), 26 (read error), 27 (out of memory) and 60 / 77 (the local CA store): local
      faults or code defects, not the server's answer. The attempt's outcome record says "stopped (local fault; not
      counted)".
    - **Attempts.**
      - Up to **3** attempts per image, for transport failures only. A 429 is a transport failure; `Retry-After` is not
        read.
      - Fixed waits apply between attempts in a run: 10 minutes after the first and 30 minutes after the second.
      - Each attempt writes to a runner-built name, `E:\data\asdg\segura_decoder_<id>\carrier.json.a<k>.part`
        (k = 1, 2, …, one per attempt; a "stopped (local fault)" attempt takes a k but is not counted toward the 3).
        It is renamed to `carrier.json` only after the read-back passes. A failed attempt's `.part` is left in place
        (nothing is deleted).
    - **Capped across runs; two records per attempt (re-check C5).**
      - Before each GET, a start record is written: `run_manifests/material/ungated/segura_decoder_<id>_attempt<k>.json`
        (FE10's folder).
      - After the GET, the outcome goes into a **second** record, `…_attempt<k>_outcome.json`. Records are never
        overwritten (FE9). The outcome is one of: extracted; final refusal; transport failure (counted); size mismatch;
        stopped (local fault; not counted).
      - The cross-run count reads both records of every attempt.
      - A recorded final refusal, a recorded size mismatch or three recorded transport failures make the decoder
        unavailable in every later run, with no new request.
    - **What is on disk at the stage's start (re-check B1; review C2; FE8).**
      - `fetch_util.get` writes the response body before it raises on a non-200 (`fetch_util.py:39-43, :59-61`), and
        `_fetch` renames the `.part` only after its read-back (`fetch_extract.py:1095-1103`). So every 5xx, 429 or 404,
        and most curl 18 / 28 partials, leave a `carrier.json.a<k>.part`.
      - The attempt records are therefore read **first**.
      - **A `.part` whose attempt has an outcome record is accounted for.** Its size and sha256 are recorded; it is
        never read or parsed; it does not stop the stage. A recorded final refusal then reads "unavailable" with no new
        request, as above.
      - **The stage stops for the operator only on a crash trace:** a `.part` with no attempt record, or an attempt
        record with no outcome record (with or without its `.part`). A stop does not make the decoder unavailable.
      - A new attempt takes the next k. If that name already exists without a record, it is a crash trace.
    - **Printed on a failure:** the exception's class name, the stage label, the raising line, and the curl exit code or
      HTTP status code (a number). Nothing else is printed.
    - **Decided once.**
      - The outcome (extracted, or unavailable with its reason) is written in the phase-2 manifest before any Segura
        reproduction is computed. The manifest is never overwritten (`wp3_material.py:388`).
      - There is no request after the outcome is recorded, and no switching between the decoder and the fallback after
        any Segura reproduction value exists.
  - **(g) If the live format differs from the repository's:**
    - a structural difference in the declared columns makes the decoder unavailable (e);
    - extra or reordered columns are used and labelled (c);
    - a difference of content (another AHBA store or FDR method) cannot be seen in the format. The output's row count
      is reported beside the paper's 20,787 (descriptive; never a refusal).
  - **(h) Identity.**
    - The decoder output's identity is recorded at download (sha256, bytes): "identity recorded at download (no
      pre-freeze identity)", as R22 fetches it after the freeze.
    - A `carrier.json` already on disk is used only if this stage's `SOURCE.md` beside it records the same sha256.
      Otherwise the stage stops for the operator; the copy does not make the decoder "unavailable".
- **Options not adopted:**
  - mapping by symbol only (against the S-build's id-first rule);
  - q ≤ .05 (the texts say "< .05");
  - keeping positive t only (against "both signs");
  - "unavailable" meaning HTTP failures only. A response the declared read cannot use is not the decoder's output for
    the registered rule, so treating it as "not auditable" would discard the fallback that the register names for
    exactly this case (`claims_register.md:330-331`);
  - an undeclared or unbounded retry.
- **Why now:** no decoder output has been fetched (phase 2 has not run). The rule uses no value of any map or list.
- **Counts:** none move (`RUN_PLAN.md:901`). Rows 1–80 are not testable as stated or are descriptor cells; none is in
  m.
- **Checks (P17 / P24 extension, functional, in `tests/`):**
  - **On a synthetic split-orient output with the eight columns:**
    - a gene at q .049 with t < 0 is decoded, and one at q = .05 is not;
    - two rows on one HGNC gene, one of them below .05, give one gene;
    - an Entrez id given as 1234, 1234.0 and " 1234 " is read as the same id, and one given as "12a4" is not;
    - an Entrez id that names another approved symbol than `gene_symbol` governs.
  - **Columns:** extra or reordered columns are accepted and labelled.
  - **Unavailable, with the stage recorded (each taking the fallback path):**
    - a missing `p (FDR corrected)`; a duplicated `gene_symbol`; a row of another length;
    - an output whose q are all null;
    - HTTP 404; an HTML page; a HEAD size of 71,441.
  - **Attempts:**
    - curl 18, 28 and 55 and HTTP 503 each count as transport failures, and so does HTTP 429;
    - curl 23 and 60 each stop the stage and consume no attempt (B2);
    - the waits are the declared ones (mocked clock);
    - a fourth attempt never happens, within or across runs. A second run after two recorded transport failures, each
      leaving its `.part` with an outcome record, does not stop and makes one GET at most (B1);
    - a recorded final refusal whose `.part` is on disk reads "unavailable" with no stop and no request (B1);
    - each of these stops the stage (B1): a `.part` with no attempt record; a start record with no outcome record; a
      pre-existing `carrier.json` without this stage's `SOURCE.md`.
  - **Must-fail variants:** a positive-t-only list, and a "≤ .05" list, each caught.

## R46. Liu SD7: the file, sheet, header row and columns, two passes, missing values, and the T4 / T5 comparator (U-W3-17)
- **Text:**
  - R10: "Hemispheres are pooled per DK name if and only if SD7's label column names hemisphere-merged labels (read from
    the ungated SD7's label column before any value)" (`RUN_PLAN.md:657-658`).
  - R42 (d): "SD7's label column is read through §8's wrapper before any value" (`RUN_PLAN_amend_2.md:327`). Its
    normaliser (`:328-341`): case-fold; strip `_thickavg` / `_surfavg`; split and drop `ctx`; markers, glued markers
    included; the alias table; an abagen DK name; the marker's side. Its drops and fail-closed rules: `:342-357`.
  - R42 (e): "The labels are the DK labels (pooled or not) that carry ≥ 1 sample **and** that SD7 lists" (`:359`); "The
    same function is applied to SD7's values" (`:362`).
  - §8 step 4: "A declaration is exact header texts or a column rule applied to a header row inside the first 20 rows
    (`claims_register.md:818`). No header row or cell is printed to find columns" (`RUN_PLAN.md:1229-1231`). Moreau's
    precedent: "It does not record their form, so the rule accepts all three" (`:1264-1265`).
  - §8 step 3: declared sheets only, names "compared with the declared names" (`:1213-1227`).
  - TSV 473–474: "the claim's statistic computed from our per-label rank-biserial r vs the same statistic computed from
    the paper's SD7 values (±.05); the flag does not move the population" (also `claims_register.md:1680-1681`).
- **What the register holds** (the Liu draft, incorporated by reference at §8's fc2a25d4…, `claims_register.md:59-61,
  :2210`; B2):
  - the file: one workbook "Supplementary Data 1-15 (xlsx)" at
    `https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-026-10045-x/MediaObjects/42003_2026_10045_MOESM3_ESM.xlsx`,
    local copy `E:\data\asdg\liu2026spatiotemporal\supplement\42003_2026_10045_MOESM3_ESM.xlsx`, **sha256
    e2bd735c0f799d8a79f1f4f72d360d1d77a0570986a2beeb9b9be08ac8661242, 1,442,234 B** (`register_work/…:21`);
  - SD7's content: "AHBA-region r mapped to ENIGMA labels" (`:21`); "SD7 gives the resulting per-label r only" (`:28`);
    "SD7 ASD column, 78 L/R rows" (`:51`);
  - its labels: "32 DK cortical labels with a value — entorhinal and pericalcarine NA — + 7 aseg: accumb, amyg, caud,
    hippo, pal, put, thal; lateral ventricles excluded" (`:50`; also `literature/notes/liu2026spatiotemporal.md:15`);
  - what was read before the freeze but not recorded: "sheet names, headers, row labels" (`:12`); "SD7 row labels and
    ASD NaN count" (`:69-70`).

  **Not recorded anywhere:** SD7's sheet name, its header row, its header texts and its label column's position.
- **Reading.** T4 / T5's computation needs (a)–(e); the comparator also needs (f)–(g).
  - **(a) File and identity (orchestrator's answer to Q1; B2).**
    - The workbook is used as found at the registered path (FE15); no request.
    - Identity at use: sha256 and size must equal **e2bd735c… / 1,442,234 B**. This is a registered file hash: the
      draft's "file hashes" are incorporated (`claims_register.md:59-61`). So this is the register's "copy already on
      disk … checked by its sha256" (`:1093`).
    - A mismatch reads "not auditable (map changed)" (`RUN_PLAN.md:1703-1704`) for **T4 and T5**, because their label
      set needs SD7 (R42 (e)).
  - **(b) Sheet: a name rule (orchestrator's answer to Q2; C3).**
    - Normalise each sheet name in memory: casefold it and remove every character that is not a letter or a digit.
      Names are recorded as sha256 only.
    - The declared sheet is the one sheet whose normalised name matches
      `^(supplementary|supplemental|suppl|supp)?(dataset|data)?(sd|s)?0*7(?![0-9])` at its start: "7" not followed by
      a digit, with anything after it (re-check C4 added "supplemental" and "dataset").
      - Matched: "Supplementary Data 7", "Supplementary Data 7 (AHBA)", "Supplemental Data 7", "Supplementary Dataset
        7", "Supp Data 7", "Data 7", "SD7", "SD 7", "S7", "7".
      - Not matched: "Supplementary Data 17", "Supplementary Data 70", "Table 7".
    - **Exactly one** sheet must match. If none or more than one does, T4 and T5 read "not auditable (definition not
      applicable: SD7's sheet not identified by the declared name rule)". There is no fallback by position or content.
      Every other sheet stays undeclared and is never fetched (SD1–SD6, SD8–SD15).
  - **(c) Header row and columns: a column rule found through the frozen guard's API, as Moreau's is (§8 step 4).**
    - For h = 0, 1, …, 19, the wrapper calls `read_openpyxl(ws, declared=<rule>, header_row=h, …)`. The first h for
      which the guard returns rows is the header row.
    - The rule returns `[]` unless row h holds **exactly one** cell that is a text equal to `asd` after stripping and
      casefolding (TSV 473: "SD7 ASD column"), at a position > 0. `ASD_SFARI_1` and the like do not match.
    - When it matches, it returns `[0]` in pass 1 (the label column is the sheet's first column, position 0) and
      `[0, <ASD position>]` in pass 2. The header text at position 0 is not used.
    - If no h qualifies, T4 and T5 read "not auditable (definition not applicable: SD7's header row not found by the
      declared column rule)".
    - **Position 0 is asserted to be the label column by R42 (d)'s normaliser itself** (orchestrator's answer to Q3,
      replacing it; review A1). Every block cell must normalise either to a DK label or to a kind R42 (d) drops
      (lateral ventricle, global measure). Any other cell fails closed with R42 (d)'s own status, "not auditable
      (definition not applicable: SD7 labels unmatched)". There is no separate share threshold.
  - **(d) Rows: the label block (B3).**
    - Empty rows after the header row (position-0 cell empty or whitespace) are skipped.
    - The block is the first run of rows whose position-0 cell is non-empty, up to the next row whose position-0 cell
      is empty.
    - **After the block,** every remaining non-empty position-0 cell is normalised in memory by the same R42 (d)
      normaliser. **If any matches a DK label**, T4 and T5 read "not auditable (definition not applicable: SD7 label
      block interrupted)".
    - Cells after the block that normalise to nothing, or to a dropped kind, are footnotes. Only counts are recorded
      (cells after the block; how many matched).
    - The block's row count is reported beside the registered 78 (`:51`). It is reported, never a refusal.
  - **(e) Pass 1: labels, used before any value (R10, R42 (d); B4).**
    - The block's labels are normalised in memory by R42 (d), unchanged. The outcome — matched, or fail-closed with its
      counts — decides pooling (R10's binary rule) and T4 / T5's label set (R42 (e)).
    - "SD7 lists" a DK label iff a label of the block matches it, **whatever its value**.
    - **T4 and T5 are computed from pass 1 alone.**
    - **What pass 1 holds in memory (declared residual):**
      - the frozen guard's read loads the sheet's cells: `read_openpyxl` builds every row (`privacy_guard.py:316`) and
        returns a clean sheet's rows whole (`:322-323`), and `classify_openpyxl` reads every row (`:268-275`);
      - so the ASD values are in memory during pass 1 (an FE2-type residual).
    - **R10's "before any value" is therefore met as an order of use.** The wrapper hands the transform position 0 only
      (a wrapper-side mask, also on a clean sheet), and logs the positions each transform consumes. Pass 1's log must
      hold position 0 alone.
  - **(f) Pass 2: values (the comparator only).**
    - The block's labels are read again and must normalise identically; the ASD column is read with them.
    - A finite number is a value.
    - These read as **missing** and are counted: an empty cell; a text that, stripped and casefolded, is `na`, `nan` or
      `n/a`; an Excel error literal (`#n/a`, `#div/0!`, `#value!`, `#num!`, `#ref!`, `#null!`, `#name?`, as openpyxl
      returns them). For this column this replaces FE4's refusal of non-numeric text ("Changed").
    - Anything else (another text, a bool, a non-finite number) refuses pass 2. The comparators then read "not
      computable (SD7's ASD column holds a non-numeric value)" (B6), and T4 and T5 stay computed.
  - **(g) The comparator, on the common labels.**
    - The common set L_c holds the labels of T's set (R42 (e)) whose SD7 value is present: pooled, the DK name's row;
      unpooled, the label id's row.
    - Ours = R42 (e)'s function of our per-label r on L_c. SD7's = the same function of SD7's values on L_c.
    - R37 (B)'s ±.05 check applies to this pair.
    - If L_c is smaller than T's set, the record reads "comparator on n of m labels (m − n without an SD7 value)", with
      T (all m labels) beside it.
    - T4 with no cortical label in L_c, or T5 with no hippocampus label or no other label in L_c, reads "not computable
      (no SD7 value for <the missing kind>)".
  - **(h) Privacy and quarantine (C4).**
    - The workbook goes through §8 steps 3–6 (FE1–FE16).
    - Label strings are never saved: only positions, kinds, DK ids and counts, as `wp3_material.sd7_label_transform`
      does.
    - The guard classifies SD7. If SD7 is identifier-bearing, or a sheet name hits the screen, step 6 quarantines the
      workbook **once, after both passes are verified**. Pass 1's target defers step 6 to the end of pass 2 (Affected
      code).
    - SD1–SD3 hold BrainSpan per-sample labels (`:48`). openpyxl's shared-string table loads them into memory (FE2's
      declared residual); nothing of them is printed or kept.
- **Why faithful:**
  - (b) and (c) are declarations built only on what the register fixes ("SD7", "ASD column"), in the form §8 step 4
    allows. Each fails closed through R42 (d)'s own normaliser (c) and through the interrupted-block check (d), which
    uses the same normaliser.
  - (e) keeps R10's order of use (labels before values) and R42 (e)'s set definition, which names listing, not values.
  - **(g), reworded (C5).** The registered comparator asks for "the same function" on both sides, and a label with no
    SD7 value cannot enter SD7's side.
    - Requiring every label of T's set to carry an SD7 value (the code at 629ea9d, `wp3_repro.py:393`) would make the
      comparator not computable whenever a listed label has no value. The register records that two cortical labels
      have no SD7 value (`:50`). Whether they are listed rows holding NA, or absent, is open: 78 = 2 × 39 fits either
      (re-check C8). If they are listed, a declared structure of SD7, not a value, would decide whether the comparator
      exists. If they are absent, they are not listed (R42 (e)) and L_c loses nothing. The rule is harmless either way.
    - Restricting **T's** set to labels with values would instead let SD7's values define the claim's statistic. That
      is against R10's "before any value", so it is not adopted.
- **Why now:** this audit has not read SD7 (no sheet name, header or cell).
  - The first data row and the row labels were seen before the freeze (`claims_register.md:121-124`;
    `register_work/liu2026spatiotemporal.md:69-70`). Their form is not recorded beyond the short subcortical names.
  - (f)–(g) were written knowing the registered statement that two cortical labels are NA. They use that structure and
    no value; Q9 below records the orchestrator's decision.
- **Counts:** none move in survival or m. T4 / T5 cannot survive (`claims_register.md:1680-1681`), and neither is in m.
  - Their status moves only through fail-closed outcomes: (a) identity, (b) sheet, (c) header, (c) / R42 (d) labels,
    (d) interrupted block, R42 (e). These read "not auditable (…)" and change the status composition by at most 2.
  - A comparator outcome never reaches the status (B6).
- **Checks (P16 extension, functional, in `tests/`, on synthetic workbooks):**
  - **Sheet rule:**
    - "Supplementary Data 7" among "Supplementary Data 1" … "15" is selected; so are "SD7", "Data 7" and
      "Supplementary Data 7 (AHBA)";
    - "Supplementary Data 17" or "70" alone is not selected;
    - "Supplementary Data 7" with "Supp Data 7" (two matches) is refused.
  - **Header:**
    - a title in row 0 and the header in row 2 is found;
    - `ASD_SFARI_1` beside `ASD` selects `ASD`, and two `ASD` cells are refused;
    - an empty position-0 header is accepted.
  - **Block:**
    - two empty rows between the header and the block are skipped;
    - footnotes after a blank row are counted and not read as labels;
    - a DK label after a blank row ("block interrupted") fails closed;
    - a non-label column at position 0 (row numbers) fails closed by R42 (d).
  - **Values and comparator:**
    - `NA`, `#N/A` and an empty cell are missing, and `n.s.` refuses pass 2 only (T4 / T5 still computed; comparator
      "not computable");
    - the comparator runs on the common labels with the "n of m" label;
    - T4's comparator with all cortical values missing is "not computable" (T4 itself is still computed; C7).
  - **Pass 1 and the position log:**
    - pass 1's log holds position 0 alone;
    - **must-fail variant:** a transform that reads the ASD position in pass 1 is caught by the position log (B4).
  - **Quarantine:** an identifier-bearing synthetic SD7 is quarantined only after pass 2 (C4).
  - **Identity:** a stand-in with the registered sha256 passes; a one-byte change reads "map changed".

## R47. Segura's published comparators: Table S6's 107 genes and Table S7's values (TSV rows 1, 3–80; U-W3-9)
- **Text:**
  - TSV row 1: "OR, p and Jaccard with Table S6 (107 genes; the 1,519-gene decoded list is unpublished) vs OR 1.6, p
    .0002".
  - TSV rows 3–9: "intersected with Table S4 (Jaccard vs Table S6's 107), then the paper's GO over-representation
    (PANTHER / AmiGO 2, whole Homo sapiens reference, FDR); fold enrichment and FDR vs Table S7". Each of these rows
    carries its four published values ("genes / expected / fold / FDR p = 14 / 1.9 / 7.35 / 9.4e-6", row 3).
  - TSV rows 10–80 (SEG-C3-D01 … D71): "as SEG-C3a-g (fold enrichment and FDR vs Table S7)". The published field names
    "Table S7 row of '<term>' (genes / expected / fold / FDR q < .05), MOESM2 p. 39" and gives no value.
  - "OR, p and Jaccard with any published list are reported" (`claims_register.md:332`).
  - R22: "Fisher's exact test and BH FDR across the terms tested"; "the primary reference is every human gene symbol in
    that GAF, mapped by the S-build's HGNC rule" (`RUN_PLAN.md:889, :896`).
  - §8's PDF rule: "parsed with pdfplumber 0.11.10 (L14) by a non-printing transcription; read-back compares the stored
    values with a second parse, printing counts and hashes; only the needed page is parsed" (`:1301-1304`).
  - L14 is "(G1 only)" (`:154`). **It is extended here to MOESM2**, an ungated PDF ("Changed").
- **What exists where:**

  | content | where | status |
  |---|---|---|
  | Table S7's 78 term names, in printed order and printed row, with their GO ids | `register_sets/SEGURA_S7_TERMS.json` (888c3468…; in the freeze manifest) | frozen |
  | Table S7's four values for the 7 named terms | TSV rows 3–9, `published_value_and_location` | frozen |
  | Table S7's values for the 71 D terms | a pre-freeze derived TSV (`register_work/segura2024symptommapping.md:27, :139`), identified by a registered 16-hex-digit sha256 prefix (1ea86a31…); the code that parsed it is not recorded. The frozen S-build kept "Term names only - no value of the table" (`s_extract.py:12-15`) | prefix registered; parse code unrecorded |
  | Table S6's 107 genes | a pre-freeze derived list (`:26`, 030c4b04…), same standing; the draft records "all 107 ⊂ Table S4"; TSV row 1 states the count | prefix registered; parse code unrecorded |
  | MOESM2 itself | `E:\data\asdg\register_sets_src\segura2025_tables\41380_2025_3205_MOESM2_ESM.pdf`, **sha256 ff55ffe904838fe59d3575261639c0ca922e4c6cfa788e4f7df28c2459a1be93** (`s_extract.py:96-97`; s_extract.py is 30a821a0… in the freeze manifest) | identity frozen |
  | Table S7's page and layout rule | `s_extract.py:152-195`, run with PyMuPDF: page index 38 ("p. 39"); the title assertion; the `#` header word; the `*Only` footnote; 77 rows × 4 value tokens matching `^[0-9.]+(/[0-9.]+)?$` (`:149`); the wrap repair; row 1's two terms split on " / " | frozen code |

- **Reading: read MOESM2 pp. 38–39 under §8's PDF rule, from the frozen-pinned copy.**
  - **(a) Identity at use:** the copy's sha256 equals `s_extract.py:96-97`'s pin. If it does not, the S6 and D-row
    comparators read "not computable (carrier changed: sha256 differs from the register's)" (R28's wording, `RUN_PLAN.md:1014`;
    B6). Rows 3–9 keep the TSV's values.
  - **(b) Parsing.**
    - pdfplumber 0.11.10 is asserted first (L14, extended).
    - Only page index 38 (Table S7) and page index 37 (Table S6) are parsed; each is the one page its comparator needs.
    - The transcription prints nothing: counts and hashes only.
    - It runs as a `fetch_extract` "file" target with a pinned copy and a reader (FE15, FE16), so it gets an R18 record
      and a read-back.
  - **(c) Table S7 (page index 38): a pdfplumber port of the frozen PyMuPDF rule (`s_extract.py:152-195`; B1).**
    - The frozen rule's geometry is applied to pdfplumber's `extract_words()` (default tolerances). The only change is
      that the four value tokens are **kept**: genes, expected, fold enrichment, FDR, in the TSV's order.
    - A row holding k names joined by " / " splits **each** of its four value tokens on "/". **If any token of that row
      lacks exactly k parts, the read is refused** (C7; the frozen rule checked only the first token). The j-th part
      belongs to the j-th name.
  - **(d) Cross-checks before saving (each fails closed):**
    1. the 78 parsed names, in printed order, equal `SEGURA_S7_TERMS.json`'s `term` fields exactly;
    2. **each parsed term's printed row equals that file's frozen `printed_row`** (B1);
    3. for each of the 7 named terms, each parsed value equals the TSV's value to the TSV's printed precision:
       |parsed − TSV| ≤ half a unit in the last digit of the TSV text;
    4. every value is finite, and genes are integers.

    A failure refuses the S7 read. The D rows' comparators then read "not computable (Table S7's row values not
    transcribed: <check>)" (B6). Rows 3–9 keep the TSV's values, which govern in any case.
  - **(e) The BH family and reference (U-W3-9, pinned).**
    - The terms tested are every GO 2024-01-17 `biological_process` term that is not obsolete in `go-basic.obo` and
      has ≥ 1 gene of the reference under §1.6's GO rule (propagation over is_a and part_of; every evidence code except
      ND; NOT-qualified annotations excluded).
    - BH runs across those terms, once per sidedness. The primary is two-sided, labelled "PANTHER sidedness
      unverified", with the empirical check (3ecffb8) beside it (R22).
    - R22's primary reference, "every human gene symbol in that GAF", is every object symbol on the GAF's lines,
      whatever their qualifier or evidence code, mapped by the S-build's HGNC rule. PANTHER 16.0's reference is
      reported beside it (R22).
    - Not adopted (no frozen text names them, and each would change every q): a family of only the terms with ≥ 1 list
      gene; a term-size window; a reference of annotated objects only.
  - **(f) Table S6 (page index 37).**
    - **Exactly one line of the page contains "Table S6"** (C7); otherwise the read is refused.
    - Tokens are the words below that line, each split on "," and ";", stripped of whitespace and of trailing footnote
      marks (`*`, `†`, `‡`).
    - A token is a gene iff it equals, exactly, a symbol of Table S4's raw list (the S-build's pinned input,
      `segura_s4.json` source: `…\segura2025_tables\tableS4_satterstrom_1046_symbols.txt`, sha256 e1f4638c…). This is
      the runner-side vocabulary; the register records the 107 as ⊂ Table S4. Other tokens are counted.
    - The distinct genes must number **exactly 107** (TSV row 1). If they do not, the read is refused, and the Jaccard
      reads "not computable (Table S6 not transcribed: <check>)" (B6).
    - The genes are saved as an HGNC-mapped member set, as the frozen S-build writes sets; drops are counted.
  - **(g) Read-back, and what is saved.**
    - Read-back: a second parse — a fresh `pdfplumber.open` of the file and the same rule on the same page — must equal
      the stored object read back from disk (§8). A planted one-digit change in the stored object must be caught.
    - S7's values are saved keyed by GO id and cell id (`SEGURA_S7_TERMS.json`'s runner-side keys); no term string is
      written.
  - **(h) The comparators.**
    - **Jaccard** (rows 1, 3–80): A = HGNC(decoded list) ∩ Table S4's HGNC members, with no reference restriction (the
      paper's 107 are decoded ∩ S4). B = Table S6's HGNC members. Reported: |A|, |B|, |A ∩ B|, |A ∪ B| and J, beside
      "107". It is the same value in every row; with the fallback list (R45 (e)) it carries the fallback's label.
    - **S7** (rows 3–80): for the row's term, ours are a, expected, fold enrichment, q (primary) and q (one-sided).
      Published: the TSV's values for rows 3–9, and the parsed values for the D rows. This is descriptive; no tolerance
      is applied.
    - **Rows 4 and 6** (SEG-C3b / d, "not testable (< 5)", no T): their descriptive comparison is reported too, because
      the ORA needs no T, and §16 reports "every registered cell, computed or not" with "the reproduction check or
      descriptive comparison" (`RUN_PLAN.md:1661, :1666`).
- **Options not adopted (reasons corrected, B2; orchestrator's answer to Q5):**
  - **The pre-freeze derived files (S6 list, S7 TSV) in place of the parse.**
    - v1's reasons were wrong. The drafts are incorporated by reference (`claims_register.md:59-61, :2220`), so the
      prefixes are registered fields, not an "unfrozen draft". A 64-bit prefix suffices to detect a change.
    - **The surviving reason:** the code that parsed them is not recorded, so their transcription cannot be reviewed or
      repeated. The PDF's identity and its S7 page rule are frozen in full.
    - The printed_row check (d 2) is the extra guard on the port.
    - The derived files are not used as a cross-check either (Q5: no).
  - **"Not computable" for both comparators without reading.** The frozen page rule and the frozen identity make the
    read declarable under §8, as the TSV's comparator asks.
- **Why now:** neither page has been parsed since the freeze, and no decoder output or ORA result exists. Table S6 / S7
  values were seen before the freeze (`claims_register.md:121`, `:148-151`). The rule uses none of them except the 7
  TSV transcriptions, as a check on the parse.
- **Counts:** none move. Rows 1 and 3–80 are not testable as stated or are descriptor cells, none is in m, and the
  reproduction is descriptive (`RUN_PLAN.md:901`).
- **Checks (P17 extension, functional, in `tests/`):**
  - **On a synthetic two-page PDF in the two layouts:**
    - 107 genes and 77 rows / 78 terms are transcribed; row 1's "/" split works.
    - Each of these is refused:
      - a term name that differs from `SEGURA_S7_TERMS.json`, or a term on another printed row;
      - a named row's value outside the TSV's precision;
      - a k-name row with a value token of the wrong part count;
      - a page without its caption, and an S6 page with two caption lines;
      - 106 genes.
    - A one-digit change in the stored object fails the read-back, and pdfplumber at another version refuses the read.
    - The Jaccard of planted lists equals its closed form.
  - **Cross-tool test (B1; re-check C3):**
    - The test writes a synthetic PDF with matplotlib (`env\venv`, 3.11.2). **The Table-S7-layout page is page
      index 38**, after 38 padding pages, because the frozen function reads `doc[38]` (`s_extract.py:154`).
    - That page satisfies every assertion of the frozen function (`s_extract.py:152-195`):
      - the exact title text "Table S7. Genetic Ontology (GO) terms" (`:156`);
      - exactly one `#` word (`:158-159`) and exactly one word beginning `*Only` (`:161-162`);
      - 77 printed rows with 78 terms (`:186, :194`); row 1 is a " / " pair with "a/b" value tokens;
      - one wrapped row whose values sit on the next line;
      - **exactly the 7 `SEGURA_NAMED` names** (`:124-125`, asserted at `:194`) among the 78 terms.
    - **The port's output (pdfplumber 0.11.10, `env\venv`) must equal the frozen `s_extract.segura_s7`'s output.**
      - The frozen leg runs unchanged as `C:\Python313\python.exe -E -P`, from a fresh empty working directory, with
        `INPUTS["segura_moesm2"]` pointed at the synthetic file.
      - `-I` cannot import `fitz`, which lives in the user site. `-E -P` imports it: checked for v2.1, PyMuPDF 1.27.1
        and `docx`, from an empty directory.
      - Equality is required on names, printed rows and order. The frozen function keeps no values, so the port's
        value tokens are checked against the planted ones.

## R48. LIU-T1's comparators: SD3's per-sample r and the prenatal cluster (worker's item 3)
- **Text:**
  - TSV 471 reproduction: "descriptive (amendment 4 §2): per-sample r vs the SD3 'ASD' column; prenatal-cluster
    membership (Fig. 2b)". Published: "ASD in the 'prenatal' cluster" and "SD3 per-sample r".
  - §8: "**BrainSpan:** only the declared sample columns (age, structure acronym) are read; donor columns are never
    read" (`RUN_PLAN.md:1306`).
  - Registered draft fields and pre-freeze notes:
    - SD3 holds "524 unique sample labels + 38 footnote rows" (`register_work/liu2026spatiotemporal.md:48`), and the
      labels' form is not recorded;
    - Liu's "sample → 11 stages / 10 structures annotation CSV is not released" (`:27`);
    - the clustering is "r values z-scored per set across samples -> ComplexHeatmap (ward.D2)" over the traits
      (`literature/notes/liu2026spatiotemporal.md:21`); "Per-sample r and P (SD1-3)" (draft `:21`).
- **B9's count (run for v2):** over BrainSpan's 524 samples, on the two declared sample columns only:
  - 407 distinct (age, structure acronym) pairs;
  - **79 pairs occur more than once, covering 196 samples**; the largest multiplicity is 3.

  Script: `…\scratchpad\amend3\b9_pair_count.py`. Input: `E:\data\asdg\brainspan\genes_matrix_csv\columns_metadata.csv`,
  sha256 995a8e75… (= the pre-freeze pin). The donor columns never entered a frame, and only counts were printed.
- **Options for the per-sample comparator:**
  - (A) pair SD3's rows with BrainSpan's samples on (age, structure acronym);
  - (B) pair by row order;
  - (C) the comparator reads "not computable".
- **Reading: (C), for both parts.**
  - **Per-sample r:** "not computable (SD3's per-sample r: (age, structure acronym) is not one-to-one over BrainSpan's
    samples: 79 pairs repeat, 196 of 524 samples; BrainSpan's donor columns are not read, §8)" (B6, B9; re-check C6).
    - **(A) fails on our side, and this is the decisive reason:** the count above.
    - (A) would also need a declared rule that parses SD3's labels into (age, structure acronym). No record gives their
      form. §8 `:1306` concerns BrainSpan's donor columns, not SD3's labels (re-check C6). Whether SD3's labels carry
      donor codes is unknown, and §8's print rule would bar recording any that did.
    - (B), a blind positional rule (SD3 row k = BrainSpan column k), cannot be verified without reading SD3's labels,
      and the count shows that even age and structure cannot confirm it for 196 samples. Not adopted.
  - **Prenatal-cluster membership:** "not computable (prenatal cluster: defined by ward.D2 over the traits' z-scored
    per-sample r; the other 14 traits' per-sample r are SD3 columns, and a recomputation with our ASD vector beside them
    would be an unregistered hybrid; the other traits' sets are not registered)" (B9).
    - T's sign is reported as T; it is not presented as cluster membership.
  - SD3 is never declared, so no SD3 cell is read.
- **Why now:** SD3 is unopened by this audit (its first data row was seen before the freeze, `claims_register.md:122`).
  The count uses BrainSpan's declared metadata only.
- **Counts:** none move. LIU-T1 is "no calibrated test"; T and its G1–G5 legs are computed as registered. The
  comparator statuses never reach the cell's status (B6).
- **Checks (functional):** the T1 record carries both statuses; no target declares an SD3 sheet (asserted on the
  targets).

## R49. LIU-T2's family: the pooled SD and the FDR family of SD4's test (worker's item 4)
- **Text:**
  - TSV 472: reproduction "p only (SD4 frontal cortex vs thalamus)"; published "p = 7.12e-05, p.adj = 0.000712";
    inference level "rstatix pairwise t-test (pooled SD, FDR) across structures, parametric".
  - TSV 475–477: "p.adj only (SD4 frontal cortex vs striatum / cerebellum / hippocampus)"; published p.adj .0863,
    .0863, .064.
  - The register's structures: frontal cortex = DFC, VFC, MFC, OFC; thalamus = MD, DTH; striatum = STR; cerebellum =
    CBC; hippocampus = HIP; amygdala = AMY (`claims_register.md:1672-1675`).
  - Registered draft fields and pre-freeze notes:
    - the paper's test, `rstatix::pairwise_t_test(r ~ structure, ref.group = "frontal_cortex", p.adjust.method =
      "fdr")` per disorder (pooled SD; brainstem dropped);
    - its input file `combine_r_rank_biserial-11structure-scaled-line.CSV`;
    - frontal cortex n = 164 and thalamus n = 29 (`register_work/liu2026spatiotemporal.md:49`);
    - the sample → structure annotation "is not released" (`:27, :65-66`; literature note `:42`);
    - the literature note names 10 structures, brainstem dropped (`:20`).
- **Facts:**
  - **rstatix** (`R/t_test.R` at master 50881cccbd052b828cdd09a676bc331dc23a744a, 2026-08-02, sha256 d3e6763f…; the
    version Liu ran is not recorded):
    - `pairwise_t_test_psd` calls `stats::pairwise.t.test(…, p.adjust.method = "none", pool.sd = TRUE)` on every group
      present in the data (`:294-297`). The pooled SD is the within-group SD over all k groups (`:328-331`: "the pooled
      variance over ALL k groups = the ANOVA residual SD").
    - With `ref.group` it keeps the comparisons against the reference (`:311-314`), then adjusts p over those kept
      (`:322-323`).
  - **The family size is not recorded (B5).**
    - From TSV 472, p.adj / p = 0.000712 / 7.12e-05 = 10.0 (computed). BH gives p.adj ≤ (m / i) · p ≤ m · p for the
      comparison of rank i, so the paper's family had **m ≥ 10** comparisons against frontal cortex.
    - That fits the input file's "-11structure-". It does not fit the literature note's 10 structures, which would give
      9.
    - So the paper's group count is not recorded reliably. v1's "10 structures … 9 comparisons" is withdrawn.
  - **Scaling does not matter.** Z-scoring r per set across samples is one affine map, which leaves every t and p
    unchanged.
- **Reading:** the comparators of LIU-T2 (raw p) and LIU-T2-STR / -CBC / -HIP (p.adj) read "not computable (the paper's
  pooled SD and FDR family span its structure annotation, which is unpublished and whose group count is not recorded;
  structures beyond the six the register pins are assigned to BrainSpan structure acronyms by no frozen text)" (B5, B6).
  - The raw p depends on the pooled SD over all of the paper's groups. Each p.adj also depends on the unpinned groups'
    p's.
  - Beside the status, our sample counts of the registered frontal and thalamus groups are reported against SD4's 164
    and 29 (counts only). They show whether the registered groups are the paper's.
  - T, its G1–G5 legs and the registered group definitions are unchanged. SD4 is never opened: its published values are
    in the TSV.
- **Options not adopted (orchestrator's answer to Q7: no):**
  - a pooled SD over the six registered groups with BH over their five contrasts;
  - Student's two-group t;
  - assigning the unpinned groups from BrainSpan's structure names (M1C, M1C-S1C, S1C, CB and URL have no stated
    group).

  Each of these is a test the paper did not run, so its p is not the paper's p.
- **Why now:** no Liu value has been computed; SD4 is unopened (its ASD rows were seen before the freeze,
  `claims_register.md:121-122`). The B5 bound uses the TSV's published p and p.adj (frozen) for their ratio only.
- **Counts:** none move. These cells are "no calibrated test"; three of them are descriptor cells. The comparator
  status never reaches the cell's status (B6).
- **Checks (functional):** the four records carry the status and the two counts; no target declares an SD4 sheet.

## R50. Identity of the reference files: pre-freeze pins, and every check before any carrier or request (U-W3-6; B8)
- **Text:**
  - §10 "Material and identity at use (local sha256 vs `IDENTITY_prefreeze.json`)" lists the carriers, BrainSpan's
    `expression_matrix.csv` (e8d98aa0…, TSV 471) and the AAL atlas (`RUN_PLAN.md:1420-1426`).
  - R18's per-object record carries "the R13 at-download comparison against `IDENTITY_prefreeze.json`" (`:842`).
  - §17: identity mismatch (`:1703-1704`).
  - FE7 refuses a copy on disk without a reference.
  - The WP3 report's U-W3-6 records `rows_metadata.csv`, `columns_metadata.csv` and GAMBA "at first phase-2 use"
    (`wp3_layout.py:88-91, :103`, pins `None`).
- **What §10 and R18 say, and do not say (C6).** They name references only in `IDENTITY_prefreeze.json` and, for the
  BrainSpan matrix, the TSV. Neither names a reference for the two metadata files or GAMBA, and
  `IDENTITY_prefreeze.json` has none. The pin below is therefore **a choice stricter than first use**, not a
  requirement of §10 or R18.
- **Facts:** pre-freeze manifests of these exact files exist. They were committed in 5e198b7 (2026-09-23T08:39:05+02:00)
  and are unchanged at the freeze commit 3d1abe3 and at HEAD. They are not drafts and are not incorporated in the
  register.
  - `arcs/audit/results/data_manifests/brainspan_SOURCE.md:22-26`:
    - `columns_metadata.csv` 995a8e75b76459ba2bdbb51ad2db8970272f546baae14ddd3a7df6bc3ac18a01, 43,050 B;
    - `rows_metadata.csv` dbfea0211aea42f6032084c3cdacb737943cbd786115dc5fde0f754708ae988b, 2,151,132 B;
    - `expression_matrix.csv` e8d98aa0…, which equals the TSV's pin.
  - `gamba_SOURCE.md:27`: `Background_genes_null_brain.csv`
    442334c3cb487625349fc6e6be6fee121dbc7bdb35b9277133c04032ee0fa53a, 268,733 B (GAMBA-MATLAB @0c012868).
- **Reading:**
  - These sha256s and sizes pin the three files in place of "recorded at first use".
  - **Ordering (B8):** before any carrier is touched or any network request is made, the stage runs every identity
    and pin check:
    - the reference files (HGNC, GO obo / GAF, PTHR16.0_human, the AAL atlas and info, the DK info);
    - the a1_builds MANIFEST, records and outputs;
    - **all three BrainSpan files alike**, `expression_matrix.csv` included;
    - GAMBA;
    - the Moreau clone assertion of §8.1.
  - **Any mismatch stops the stage** before its manifest is written. These files are shared by every class's G3 / G5
    legs and by Liu's BrainSpan rows, as L6 / L7 stop a launch for the AHBA matrices. The orchestrator decides, and
    nothing is re-pinned.
  - At 629ea9d a mismatch of `expression_matrix.csv` gave only a "map changed" record (`wp3_material.py`, BrainSpan
    identity step). That is replaced by the stop.
- **Why now:** the files' contents were read by the WP3 worker (§0), but their identity has not been checked against
  these records. The reading uses only hashes recorded on 2026-09-23.
- **Counts:** none move.
- **Checks (functional):**
  - a stand-in metadata file, matrix or GAMBA table one byte off stops the stage before any carrier or network mock is
    called;
  - the pins equal the manifests' values (asserted against the two SOURCE.md files).

## 8. WP3 phase 1's readings and risks: pin or no pin
| WP3 report item (`wp3_phase1_report.md:31-96`) | verdict | reason |
|---|---|---|
| U-W3-1 carrier copies | **pin** | R44 |
| U-W3-2 row → object binding by the TSV map text, exactly one match | no pin needed | the TSV's `map` field is the frozen binding (rows 1–80 "NeuroVault 790618 (" / "781986 ("; rows 615–619 "sheet 1_16p11.2Del" / "sheet 3_22q11.2Del"; MOR-C3's names the 22q sheet, TSV 617); no match or two matches refuse |
| U-W3-3, U-W3-4, U-W3-14 decoder URL, format, columns, list, "unavailable" | **pin** | R45 (a)–(h); the Entrez reading follows `wp3_material._entrez` (C11) |
| U-W3-5 Liu keying | no pin needed | R10's U_stat is "∩ the S-build's HGNC mapping" (`RUN_PLAN.md:641-642`), and the S-build's rule takes the source's id first (Ensembl for BrainSpan rows; abagen's columns carry symbols only); R42 (a) averages duplicates; Liu's G5 trajectories must carry U_stat's keys; the class contexts' G5 keeps the frozen `asdg.brainspan` keys |
| U-W3-6 BrainSpan metadata and GAMBA "recorded at first use" | **pin (replaced)** | R50: pre-freeze pins, and every check before any carrier or request |
| U-W3-7 AHBA sample / donor counts through the build-record chain | no pin needed | the counts are the frozen §3.1 builds' tables (R11); the chain is hashing, not a choice; checked first (R50) |
| U-W3-8 Liu's GAMBA background, HGNC-mapped | no pin needed | R10 `:647` "GAMBA brain>body ∩ U_stat" needs U_stat's HGNC keys; the brain>body rule is the class contexts' (`e3_plants.py:35, :51`) |
| U-W3-9 R22's reference and term family | **pin** | R47 (e) |
| U-W3-10 the paper's 20,787 beside, no third test | no pin needed | R22 `:898-899`, literal |
| U-W3-11 Moreau's "24.2 %" compared as .242 | no pin needed | R² is a fraction, and ±.05 is on that scale (`prereg.md:120-122`; R27 `:980-981`) |
| U-W3-12 MOR-T percentiles and tail | no pin needed | descriptive (TSV 618–619 "percentile ranks and the tail p"); every variant the TSV names is reported (98th from the text, 95th from the code; weak and strict ranks); the exact hypergeometric tail is the limit of the paper's uniform random-set null, so no K or seed is chosen; all 64 parcels (`claims_register.md:1773-1774`) |
| U-W3-13 R22's fallback | **pin** | R45 (e): Segura's own q < .05 either sign; the claim's analysis parcels |
| U-W3-15 Moreau's nodal profile | no pin needed | TSV 615's map text ("diagonal set to 0, mean over the 64 columns"), literal |
| U-W3-16 dropped Segura parcels passed as NaN | no pin needed | §1.7's < 50 % rule (`claims_register.md:1031-1034`) and prereg §2's "finite" entry rule |
| U-W3-17 SD7's two passes | **pin** | R46 |
| U-W3-18 identity of a quarantined carrier held to its phase-2 record | no pin needed | §8 step 6 forbids opening the quarantine (`RUN_PLAN.md:1273`). The carrier's use is its extraction, whose identity the phase-2 record holds; later uses read the extracted object, asserted by sha256. For Moreau the whole clone moves (§8.1); the rule is the same |
| U-W3-19 a passed launch before the material stage | no pin needed | §1 (L1–L15; L13 before any workbook) and §2.3, literal |
| U-W3-20 re-parcellation recomputed at use | no pin needed | an added equality assertion; the rule is §1.7's |
| U-W3-21 `row_<n>_repro.json` | no pin needed | bookkeeping for §16's "the reproduction check or descriptive comparison" |
| risk: Moreau quarantined in phase 2 | **decided** | §8.1 (the whole clone; decision ev-1a12b80e072f8fa) |
| risk: decoder format from the repository, not the live server | **pin** | R45 (g) |
| risk: G1 / G2 rows "not run (no WP3 loader)" | no pin needed | WP4 / WP5 (§18) |
| risk: a1_builds pinned by gitignored build records until the phase-2 manifest is committed | no pin needed | the phase-2 manifest pins them (R18) and is committed before the verdict pass |
| risk: the door test skips the venv and `.py` / `.pyc` opens | no pin needed | test scope; no material lives there |
| risk: R27's amendment-5 labels and power columns not wired into row outputs | not a reading | R27 (`RUN_PLAN.md:968-976`) and §16 (`:1667`) require them; an implementation gap, closed before the official run (Affected code) |
| found while drafting v1: `wp3_layout.DECODER_SOURCE`'s `ahba.py` sha256 | correction | R45 Facts; Affected code |
| found while drafting v1: rows 4 and 6 (SEG-C3b / d) had no comparison | **pin** | R47 (h) |
| found while drafting v1: `wp3_repro.fisher_record`'s `jaccard_list_vs_set` (decoded list vs Table S4, inside a reference) | no pin; label | not the registered Jaccard, which is R47 (h)'s; drop it or label it "not registered" |

### 8.1 Moreau's workbook: quarantine of the whole clone (orchestrator's decision ev-1a12b80e072f8fa; answer to Q8)
- **Why it is quarantined: the frozen screen hits each of the plan's five do-not-open names.**
  - §8's screen runs, in memory, on every sheet name, and "a hit makes the carrier count as identifier-bearing for
    step 6 (quarantine and the deletion request)" (`RUN_PLAN.md:1292-1295`).
  - On the plan's pinned names (no carrier opened), the frozen guard gives a V hit on each do-not-open name (`5_BIV`,
    `6_ASD`, `7_SZ`, `8_ADHD`, `9_Ranking`; `:1224-1225`) and 0 on the two declared names
    (`tests/test_wp3_phase1.py:843-852`, test G5; WP3 report :82-86).
  - The quarantine follows from this frozen name screen, not from observed participant data. The registered draft
    records the declared sheets as group-level β blocks (`register_work/moreau2020mutations.md:34`).
- **Decision.**
  1. **Before any carrier is touched** (with R50's checks), the stage asserts that no other pinned object lies inside
     the clone directory `E:\data\asdg\moreau2020mutations\repo_GeneExp_and_CNV_FCsignatures\`. "Pinned objects" are
     those of `IDENTITY_prefreeze.json`, the S-build and `register_sets` manifests, and `wp3_layout`'s pins. If any
     does, the stage stops and the orchestrator decides.
     - **Run-time pins:** a grep of the frozen register JSONs and `s_build.py` finds only the workbook itself inside the
       clone.
     - **Registered fields name other files in the clone (re-check C2):**
       - TSV rows 615–623 `set_S`: "repo data/cnv_genes_cnv16p112.csv (sha256 prefix b2b9dbfb)" and
         "…cnv22q112.csv (sha256 prefix 3838d75f)";
       - the incorporated Moreau draft (`register_work/moreau2020mutations.md:41-46`):
         - the authors' AHBA × MIST64 matrix (57fba8a4…) and `gene_set_all.csv` (5ed37bd9…);
         - the label-shuffle null maps (3bbae5ba…, 2cfa86f0…, 5f93b8cc…, dcd046ff…);
         - the random-index file (2fa0cf26…);
         - the authors' published output tables.
     - **No A1 code at 629ea9d reads any of these.** The S-build uses copies of the two locus lists from
       `E:\data\asdg\register_sets_src\moreau2020_locus\`, whose pinned sha256s (`s_build.py:243-246`: b2b9dbfb…,
       3838d75f…) carry the registered prefixes (`register_sets/moreau_16p11.2.json`, `moreau_22q11.2.json`). So the
       assertion passes on run-time pins, and the move takes these registered files with the clone.
  2. **After the declared-sheet extraction is verified,** the **whole clone directory** is moved, on the same volume,
     to `E:\data\asdg\_quarantine\ungated\moreau2020mutations\`. This replaces §8 step 6's move of "the carrier"
     (`:1272`) for this target ("Changed").
  3. **The deletion request:**
     - It names the working copy and the whole clone.
     - It names any other copy by sha256 (c947112ded237be43459c65f896c7ec1f120d6faaed0d5700ed63fb81e302e19), wherever
       it is; this author listed nothing on E:, and a submodule checkout elsewhere under `…\moreau2020mutations\` is
       possible.
     - It notes that removing blob 7a8b62be… means deleting or rewriting the clone.
     - It notes that the public GitHub original (`kkumar-iitkgp-livia/GeneExp_and_CNV_FCsignatures` @9e8af9c1)
       preserves provenance.
     - **It lists the registered materials inside the clone (C2) with their surviving copies:**
       - the locus lists: `E:\data\asdg\register_sets_src\moreau2020_locus\` (sha256 b2b9dbfb…, 3838d75f…) and
         GitHub @9e8af9c1;
       - the authors' matrix, `gene_set_all.csv`, the null maps, the random-index file and the output tables: GitHub
         @9e8af9c1 only.
     - It states that the quarantine follows the frozen name screen (V hits on the plan's do-not-open sheet names), not
       observed participant data.
     - The deletion is the operator's step (default 24, `:1279-1285`).
- **The exploration lane already refuses both locations (review C10; `explore/discovery/guard.py` at 898bb00, unchanged
  in the working tree).** No guard change is needed.
  - `moreau2020mutations` is one of `A1_TARGET_COMPONENTS` (`:45-46`). Any path with that component is refused as "A1
    TARGET" under any root (`:136-140`), before the EXCLUDED check (`classify`, `:161-163`). This covers the clone at its
    current place and inside the quarantine. The self-test plants `E:/data/asdg/_quarantine/G2/moreau2020mutations/x.xlsx`
    (`:264`).
  - `E:\data\asdg\_quarantine` is EXCLUDED (`:25-30`, `:164-168`).
  - `E:\data\asdg\moreau2020mutations` also lies outside the lane's ALLOWED roots (`:18-21`), so it is refused as
    OUTSIDE even without the component rule.
- **Consequences recorded:** MOR-C1…C3 and MOR-T1 / T2 read the extracted 64 × 64 blocks by sha256 after the move
  (U-W3-18). Re-extraction needs the operator to move the clone back.

## Changed (each a declared departure from a frozen text or frozen code; review C8)
1. **§8 step 3** compares sheet names "with the declared names" (`RUN_PLAN.md:1215`). R46 (b) declares SD7's sheet by
   a name rule (exactly one match).
2. **FE4** (`fetch_extract.py:55`) refuses non-numeric text in a declared numeric column. R46 (f) reads SD7's
   missing-value tokens as missing.
3. **L14 is "(G1 only)"** (`RUN_PLAN.md:154`), and §8's PDF rule lists three gated PDFs (`:1301`). R47 applies both to
   an ungated PDF, MOESM2.
4. **The frozen `s_extract.segura_s7`** (PyMuPDF; term names only, `s_extract.py:12-15, :152-195`) is ported to
   pdfplumber with the value tokens kept (R47 (c)). Its outputs are tied to the frozen function's by the cross-tool test.
5. **§8 step 6 moves "the carrier"** (`RUN_PLAN.md:1272`). For Moreau the whole clone directory is moved (§8.1).
6. **FE8 refuses a leftover `.part`, and `fetch_extract` makes one attempt** (`fetch_extract.py:60`). R45 (f)
   declares:
   - up to 3 attempts, counted across runs, with per-attempt `.part` names;
   - a whitelist of transport failures; any other curl exit stops the stage and consumes no attempt;
   - a `.part` accounted for by its attempt's outcome record does not stop the stage; only a crash trace does
     (re-check B1).
7. **R50 pins two files §10 and R18 name no reference for**, from records they do not name: a stricter choice. It also
   turns an `expression_matrix.csv` mismatch from a "map changed" record into a stop. That departs from §17: "the cell
   reads 'not auditable (map changed)' … The run continues for other cells" (`RUN_PLAN.md:1703-1704`; re-check C1).
8. **Not a departure, but stated:** R45 (e)'s HEAD of the two image file URLs is a request touching carriers that §10
   does not list under "Fetch". A HEAD transfers no content.
9. **FE5** (`fetch_extract.py:56`: the rows of a declared-columns read are "the rows after the header row whose declared
   cells are not all empty") is replaced for SD7 by R46 (d)'s block rule: empty rows skipped, one contiguous block,
   and the interrupted-block check (re-check C1).
10. **§8 step 6 runs "right after its extraction is verified"** (`RUN_PLAN.md:1270-1271`). For SD7, R46 (h) runs it
    once, after pass 2 is verified (re-check C1).
11. **FE15 renames a quarantined pinned copy to `carrier<ext>`** (`fetch_extract.py:72-74`). §8.1's whole-clone move
    keeps the clone's file names: the server's names, inside the quarantine folder (re-check C1). They are never
    printed or written (§8's print rule).

## Not changed
- every registered definition, threshold, seed key and status order;
- the T and legs of every cell named here, and every cell status except the fail-closed T4 / T5 outcomes of R46;
- R10, R14, R22 and R42 as frozen (applied, not altered), and R37's check;
- §8's print rule and steps 0–6, and FE1–FE16, except items 1, 2, 5, 6, 9, 10 and 11 above;
- `src/asdg`, `src_register/`, the register maps and sets, the TSV, and amendments 1 and 2;
- the `plants/` blobs (amendment 2 §8.1), the plant constants (§8.1b) and every plant's threshold, n and construction;
- the frozen gate files; G1's and G2's checks and material; the exploration lane's guard.

## Affected code (the orchestrator assigns)
| reading | module | change |
|---|---|---|
| R44 | `wp3_material.targets`, tests | as at 629ea9d (FE15 copies; every reference); add the network-mock check: zero GETs of the three carriers, one HEAD per image file URL, nothing for Moreau |
| R45 | `wp3_layout.py:65-68` | `ahba.py` sha256 → 3af0ea2a62fd38e4fff5d2ef7a9e77ee4c51c5d723015ed241ef87b8c8edee1b (one hex digit wrong at 629ea9d); add the three git blobs |
| R45 | `wp3_material.decoder_object` (`:185-236`) | the column-list label and sha256; other keys and columns ignored and counted; refuse when no row has an HGNC gene and a finite q; record the row count beside 20,787 and the t-sign counts; `_entrez` unchanged (C11) |
| R45 | `wp3_material.targets` (`:281-296`), `fetch_extract` | the HEAD size probe of each image's `file_url` (once per run, before the first GET; mismatch → unavailable; Last-Modified recorded and labelled); up to 3 attempts on transport failure (the whitelist: curl 6, 7, 18, 28, 35, 52, 55, 56; HTTP 429; 5xx), fixed waits of 10 and 30 min, per-attempt `carrier.json.a<k>.part`; any other curl exit stops the stage without consuming an attempt; a start record and a separate outcome record per attempt, both read first at the stage's start and counted across runs; a `.part` with an outcome record is accounted for (size and sha256 only), and only a crash trace (a `.part` without a record, a start record without an outcome) or a foreign `carrier.json` stops the stage; failures classified in memory (`CalledProcessError.returncode`; the status code parsed from `RuntimeError`'s message; the HTML case), no message text stored; on failure print only class, stage, line and exit / status code |
| R45 | `wp3_repro.SeguraContext.decoded` | record the refusing stage in the fallback record (threshold .05 as now) |
| R46 | `wp3_layout`, `wp3_material.sd7_targets` / `run_sd7` (`:298-322`, `:457-471`), `fetch_extract` | SD7 declared by rule, replacing the exact-text JSON declaration: the registered copy (path, sha256, bytes); the sheet-name rule (C3) with exactly one match; the header search h = 0…19 through the guard with the ASD-anchored rule (pass 1 `[0]`, pass 2 `[0, ASD]`); empty rows skipped before the block; the interrupted-block check through R42 (d)'s normaliser (B3); the missing-value tokens; the new statuses |
| R46 | `fetch_extract` (`run_target`, `_quarantine`) | step 6 deferred for pass 1's target and run once after pass 2 is verified (C4); a wrapper-side mask of declared positions also for clean sheets, and a log of the positions each transform consumes (B4) |
| R46 | `wp3_repro.liu_row` (`:364-400`), `forms.liu_sd7_T` (`:784`) | the comparator on the common labels with the "n of m" label; "not computable (…)" outcomes; T unchanged |
| R47 | `wp3_material` (new MOESM2 targets and readers), `wp3_repro.segura_row` (`:227-283`) | MOESM2 as a pinned file target (s_extract's sha256); L14 asserted; page indexes 38 and 37 only; the S7 port with values kept, the per-token part count, the printed_row check, the cross-checks and the read-back; the S6 rule (one caption line, raw S4 vocabulary, 107) and the read-back; the Jaccard (A, B); the D rows' published values; rows 4 and 6; "not computable (…)" outcomes; `PENDING_S6` / `PENDING_S7` (`:52-55`) replaced; `fisher_record`'s `jaccard_list_vs_set` dropped or labelled |
| R47 | tests | the cross-tool test: matplotlib page (`env\venv`) → pdfplumber port vs frozen `s_extract.segura_s7` under `C:\Python313` (PyMuPDF 1.27.1) |
| R48 | `wp3_repro.liu_row` | LIU-T1: the two "not computable (…)" statuses (replacing `PENDING_SD3`, `:56`) |
| R49 | `wp3_repro.liu_row`, `real_sources.liu_inputs` | LIU-T2*: the status (replacing `PENDING_SD4`, `:57`) and the two group counts |
| R50 | `wp3_layout._pins_production` (`:88-103`), `wp3_material.run_material` (`:383-`) | pins for `rows_metadata.csv` dbfea021…, `columns_metadata.csv` 995a8e75… and GAMBA 442334c3… (with sizes); `STATUS_FIRST_USE` dropped for them; every identity and pin check (references, builds, the three BrainSpan files, GAMBA, the Moreau clone assertion) moved before the first carrier or network target; any mismatch stops the stage |
| §8.1 | `fetch_extract._quarantine`, `wp3_material` | the clone assertion before any carrier (run-time pins); the whole-clone move (same volume) after the verified extraction; the deletion request's content as §8.1 states, including the registered materials inside the clone and their surviving copies (C2) |
| B6 | tests | no comparator status reaches the cell-status composition |
| §8 | `run.py` / `reporting.py` | wire R27's amendment-5 labels and power columns (`reporting.r27_reading`) into every row output |
| all | `tests/test_wp3_*.py` | the checks listed per reading (in `tests/`; the `plants/` blobs and plant constants of amendment 2 §8.1 / §8.1b unchanged) |

## 9. v1's questions, with the orchestrator's answers (bench decisions, 2026-10-11)
1. **SD7's identity reference.** v1 proposed the pre-freeze draft's full sha256 and size, with an alternative.
   **Answer: accepted.**
   - The stronger basis is register incorporation: `claims_register.md:59-61` with §8 `:2199-2221` incorporate the
     drafts by sha256, so e2bd735c… / 1,442,234 B is a registered file hash.
   - v1's alternative ("identity recorded at first post-freeze use") is withdrawn. → R46 (a).
2. **The sheet-name rule.** **Answer: kept, fail closed, widened per C3** ("0*7 not followed by a digit", exactly one
   match). → R46 (b).
3. **The label column at position 0.** **Answer: replaced (A1).**
   - The label assertion runs through R42 (d)'s normaliser (`RUN_PLAN_amend_2.md:327-341`: markers, suffixes, `ctx`,
     aliases, dropped lateral-ventricle and global names).
   - The same normaliser is repurposed as B3's interrupted-block check. There is no separate share rule.
   - → R46 (c), (d).
4. **Decoder retries.** **Answer: up to 3 attempts on transport failure only**, with:
   - declared 429 handling and fixed waits;
   - curl 18 (a truncated body) counted as a transport failure;
   - attempts capped across runs (B8);
   - runner-built per-attempt `.part` names;
   - a `.part` left by an earlier run stopping the stage for the operator (C2);
   - only the exception's class, stage, line and HTTP status code printed.

   → R45 (e), (f).
5. **The pre-freeze derived Segura files as a cross-check.** **Answer: no.** The reason is corrected per B2: the
   surviving reason is the unrecorded parse code. The printed_row check of B1 is the extra guard. → R47 "Options not
   adopted".
6. **A pairing-free SD3 comparator.** **Answer: no.** → R48.
7. **A re-derivation of LIU-T2's test over the six registered groups.** **Answer: no.** → R49.
8. **The scope and wording of Moreau's deletion request.** **Answer:**
   - the request names the working copy and the whole clone, and other copies by sha256 (c947112d…);
   - it notes that removing blob 7a8b62be… means deleting or rewriting the clone, and that the public GitHub original
     preserves provenance;
   - it states that the quarantine follows the frozen name screen, not observed participant data;
   - the whole clone is moved (decision ev-1a12b80e072f8fa).

   → §8.1.
9. **This author's exposure to the literature note's SD7 / SD3 values.** **Answer: no re-derivation.** The reviewer
   found that R46 (a)–(h) take no numeric value; (f)–(g) use the declared NA structure. → §0, R46 "Why now".

## 10. Answers to the review of v1 (asdg-skeptic: refuted, 1 A conditional / 9 B / 11 C)
The finding texts are the orchestrator's summary of the review. "v2 lines" are lines of v2 (sha256 e22861c2…); v2.1
moved them. The re-check's rows (§10.1) give v2.1 lines.

| finding | answer (fix) | v2 lines |
|---|---|---|
| A1 (conditional) position 0 as the label column | adopted as the orchestrator's Q3 answer: position 0 is asserted by R42 (d)'s normaliser; the same normaliser drives B3's interrupted-block check; no share threshold | R46 (c) :451-454, (d) :455-464; §9 item 3 :942-946 |
| B1 R47 (c) is not the frozen rule | relabelled "a pdfplumber port of the frozen PyMuPDF rule (s_extract.py:152-195)"; printed_row check against `SEGURA_S7_TERMS.json`; cross-tool test (matplotlib page; port vs the frozen function under C:\Python313, PyMuPDF 1.27.1); L14 "(G1 only)" stated and extended | R47 Text :564; (b) :580-585; (c) :586-591; (d) 2 :594; cross-tool test :663-671; Changed 3–4 :891-895 |
| B2 the drafts are incorporated | cited `claims_register.md:59-61` and §8 `:2199-2221` in §0 and R46 (a); drafts' sha256 checked equal; R47's rejected-option reasons corrected (prefixes are registered; a 64-bit prefix detects change; the surviving reason is the unrecorded parse code) | §0 :61-70; R46 :408-409, (a) :423-429; R47 table :565-575, options :637-645; §9 items 1, 5 :935-941, :956-960 |
| B3 the label block | empty rows before the block skipped; after the block every non-empty position-0 cell normalised by R42 (d); any DK match → "SD7 label block interrupted" (fail closed); counts only | R46 (d) :455-464 |
| B4 "before any value" | stated that pass 1 loads the sheet's cells (`privacy_guard.py:316, :322-323`; `classify_openpyxl` `:268-275`; FE2-type residual); "before any value" met as the order of use; wrapper-side mask and a consumed-positions log in Affected code; the must-fail test points at the log | R46 (e) :465-476; Checks (position log) :524-549; Affected code :922 |
| B5 R49's group count | the group count removed from Facts and status; "unpublished; its group count is not recorded"; the BH bound m ≥ 10 from TSV 472 (ratio 10.0) and the "-11structure-" file name stated; the conclusion stands | R49 Facts :737-744; Reading :745-753 |
| B6 comparator statuses | comparator outcomes read "not computable (<why>)" (R14 `:748`, R28 `:1014, :1019`); the "§17 entry" sentence deleted; a test that no comparator status reaches the cell-status composition | header :21-24; R46 (f) :477-484, (g) :485-493, Counts :519-523; R47 (a) :577-579, (d) :592-600, (f) :612-621; R48 :694-707; R49 :745-748; Affected code :930 |
| B7 R44's network claim | no GET of the three carriers; R45 (e)'s HEAD is the only request touching them; the test asserts zero GETs and one HEAD per image | R44 Reading :193-197; Checks :222-223; R45 (e) :296-298 |
| B8 ordering of checks; attempts across runs | every identity and pin check (references, builds, all three BrainSpan files, GAMBA, the clone assertion) before any carrier or request, a mismatch stopping the stage; R45 (f)'s attempts and refusals bind later runs | R44 :206; R45 (f) :337-343; R50 :790-802; Affected code :928 |
| B9 R48's pairing | the multiplicity count run on BrainSpan's declared columns: 79 pairs repeat (196 of 524 samples); stated as the reason; the hybrid reason added to the prenatal-cluster status | §0 :51-58; R48 count :684-689; statuses :694-707 |
| C1 the size probe | blind spots declared (equal size ≠ equal bytes; the cached reduced representation, `views.py:1822-1825`); Last-Modified recorded against the pre-freeze values and labelled; the R16 comparison corrected | R45 Text (pre-freeze dates), Facts (cached representation), (e) :296-308 |
| C2 leftover `.part` | a `.part` left by an earlier run stops the stage | R45 (f) :344-345 |
| C3 SD7's sheet regex | widened to "0*7 not followed by a digit"; exactly one match | R46 (b) :430-441 |
| C4 quarantine between the SD7 passes | step 6 deferred to after pass 2 (R46 (h); Affected code) | R46 (h) :494-502; Affected code :922 |
| C5 R46 (g)'s reason | reworded: a declared structure, not a value, would decide whether the comparator exists | R46 Why faithful :508-514 |
| C6 R50's basis | narrowed to what §10 / R18 say; the pin is a stricter choice | R50 :776-779; Changed 7 |
| C7 R47's token and caption checks | (c) refuses a k-name row whose value token lacks k parts; (f) exactly one line containing "Table S6" | R47 (c) :589-591; (f) :613 |
| C8 departures | the "Changed" list, every departure declared | Changed :886-902; Not changed :904-911 |
| C9 §0's seen values | completed | §0 :115-158 |
| C10 the lane's refusal of the clone | checked: already refused (`guard.py:45-46, :136-140, :161-163`; quarantine `:25-30, :164-168`); no guard change | §8.1 :874-882 |
| C11 R45 (d) vs `_entrez` | R45 (d) follows `wp3_material._entrez` as written | R45 (d) :279-290 |

### 10.1 Answers to the re-check of v2 (asdg-skeptic: refuted narrowly, 0 A / 2 B / 9 C)
The finding texts are the orchestrator's summary of the re-check. Lines are lines of this file (v2.1).

| finding | answer (fix) | v2.1 lines |
|---|---|---|
| B1 a failed attempt always leaves a `.part`, so "a leftover `.part` stops the stage" contradicted the cross-run cap and its own test | the attempt records are read first; a `.part` whose attempt has an outcome record is accounted for (size and sha256 recorded, never read, no stop); only a crash trace stops the stage; the tests are rewritten to match; Changed 6 | R45 (f) :362-372; Checks :412-420; Changed 6 :953-958 |
| B2 "curl exits non-zero" is too broad | transport exits whitelisted (curl 6, 7, 18, 28, 35, 52, 55, 56; HTTP 429; 5xx); any other non-zero exit stops the stage and consumes no attempt | R45 (f) :336-344; Checks :414; Affected code :988 |
| C1 omissions from "Changed" | added: FE5 replaced by R46 (d) for SD7; §8 step 6 deferred to after pass 2; the whole-clone move keeps the server's file names (FE15 renames); Changed 7 now cites §17 `:1703-1704` | Changed 7 :959-961, 9–11 :964-971; Not changed :977 |
| C2 registered files inside the Moreau clone | stated: TSV 615–623 `set_S` and the incorporated draft `:41-46` name other files in the clone; no A1 code at 629ea9d reads them; the S-build uses the locus lists' copies with the registered prefixes; the deletion request lists them with their surviving copies | §8.1 :898-911, :923-927; Affected code :998 |
| C3 the cross-tool test's synthetic PDF | the S7 page is page index 38 after 38 padding pages; it carries the exact title, unique `#` and `*Only`, 77 rows / 78 terms and the 7 `SEGURA_NAMED` names; the frozen leg runs as `C:\Python313\python.exe -E -P` from a fresh empty cwd (import of `fitz` and `docx` checked) | R47 Checks :695-710 |
| C4 the SD7 sheet regex | "supplemental" and "dataset" added | R46 (b) :460-468 |
| C5 the outcome record; failure classification | the outcome is a second record (FE9) and the count reads both; `CalledProcessError.returncode` vs `RuntimeError` ("HTTP <code>…" / HTML page) classified in memory, no message text stored | R45 (f) :327-335, :353-361, :373-374 |
| C6 R48 (A) and §8 `:1306` | reworded: `:1306` concerns BrainSpan's donor columns, not SD3's labels; the count is the decisive reason | R48 :735-740 |
| C7 the T4 test's wording | "T4's comparator with all cortical values missing is 'not computable'" | R46 Checks :575 |
| C8 R46 (g) asserted that the NA labels are listed rows | not asserted: listed-with-NA or absent is open (78 = 2 × 39); the rule is harmless either way | R46 Why faithful :538-544 |
| C9 (record only) the 629ea9d code refuses R16's tarball on a size mismatch or a missing Content-Length (`fetch_extract.py:1015-1017`), while R16's frozen text records the headers and accepts any official 7.4.1 artefact (`RUN_PLAN.md:795-798`) | **recorded as a residue for WP4; no change here.** This amendment does not bear on R16; the R16 target's size check is to be reconciled with R16's text before WP4's first download | — |
