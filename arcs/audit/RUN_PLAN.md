# RUN PLAN — A1 `audit`: how the frozen claims register (v6.11) is run

> **Status: v3.1 - reviewed (re-check of v3.1 and a pre-freeze check answered, §15 rows N-*, PF-*); to be frozen.** v1 was written 2026-10-01 by a worker for the orchestrator (file first
> written 14:40:51 local time, edits until 14:41:56). Two asdg-skeptic reviews of v1 the same day returned
> "not-verified" (2 A / 9 B / 3 C) and "refuted" (4 A / 8 B / 5 C). v2 answered every finding. The asdg-skeptic re-check
> of v2 returned "verified-with-residues" (0 A / 0 B / 8 C). v3, the same day, answered the 8 C points, filled in the G1
> record commit and the actual exposure facts (§0.3, §0.4, §9), and fixed the `g1_open()` specification after simulating
> it against the real record (§2.2). The asdg-skeptic review of v3 returned "not-verified" (0 A / 2 B / 6 C). v3.1
> answers all eight: F6's false premise about ABIDE II (§18), one print rule for every gated script (§8; P20), the
> exposure details (§9), the A1 ARC's count of the first review (§15), Moreau's header search through the guard's own
> API (§8 step 4), G5's unchecked pools (R8), a non-regular tar member (R16), and the supersession and time-bound
> checks of `g1_open()`, re-simulated (§2.2). §15 lists every finding and how it was answered; §19 holds the rebuttals
> with their frozen quotes. Once frozen, its sha256 becomes a launch assertion (L5). No author or reviser of this plan
> opened any gated carrier, map, supplement, NeuroVault image or decoder output (§0.4). The programme's exploration
> lane opened the ENIGMA-ASD tables before v1 was written (§9).
>
> **What this file is.** This file records *readings*: where the frozen texts leave the runner a choice, it says which
> choice the runner makes. It never changes a registered definition. If an item could only be settled by changing a
> definition, it is listed in §6 as **"needs a frozen amendment (not this plan)"**, and until that amendment exists its
> cells read "not auditable (definition not applicable: <why>)". Each pinned reading cites the frozen text it reads
> (`file:line`) and says why it was chosen before this audit opened any gated material (the exploration lane's earlier
> exposure, and the readings written after it, are in §9).

## 0. Status, authority, inputs

### 0.1 Frozen inputs (sha256; `arcs/audit/FROZEN.txt`, `register_freeze_manifest.json`)
| file | sha256 |
|---|---|
| `claims_register.md` (v6.11, frozen 2026-09-30T09:05:05) | 897b2112d25455b330e2ae2adac659180d46f4825ae765b6a791d110873abdd3 |
| `claims_register.tsv` (692 rows; hashed inside the freeze manifest) | d6499b5d10eed39fc5bfcd8033fc5f7c7beea88f1d4b4c30fd21fed632bf8058 |
| `register_freeze_manifest.json` (36 files) | 38c2a507b057bf50b74c5ec348f03354afb3f4fd439ef73c295568a1e3155052 |
| `prereg.md` | a632b852637cc9b7d104d3d225fa9c618ce6204ed3d0d7181aff6cc665ff2114 |
| `prereg_amend_1.md` … `_5.md` | 7a0dd383…, 29c1ffdc…, d19f0f10…, 25114b65…, 023bc880… (full values in `FROZEN.txt` lines 2–6) |

### 0.2 Authority and precedence (quoted)
- The register implements the amended prereg: "Implements `prereg.md` §5.2 … as amended by `prereg_amend_1.md` …
  `prereg_amend_5.md` (verdict: amendment 3 §2; targets: prereg §5.1 + amendment 4 §1; readings, labels and headline:
  amendment 5 §3–§4)" (`claims_register.md:57-58`).
- Its own precedence rule: "Where this file, the TSV and a draft disagree, this file governs, then the TSV"
  (`claims_register.md:63-64`). For numbers: "where a number in the prose repeats one of the fenced blocks of §4 or §1.11,
  the block governs" (`:52`).
- Its limit: "A registered definition that cannot be applied as written → 'not auditable (definition not applicable:
  <why>)', never a redefinition without a frozen amendment" (`:1102-1103`).
- Its section heading: "After the freeze (nothing is decided later)" (`:1087`). This plan's readings are fixed before
  the material they apply to is opened **by this audit**: no A1 run, download or extraction has opened any of it, and no
  author or reviser of this plan (v1, v2, v3, v3.1) opened it. That claim covers this audit and those people only. The
  programme's exploration lane is not this audit: its "protocol" judge opened the ENIGMA-ASD thickness tables behind
  Patel, Giacomel, Hansen and Liu T3 at 14:25–14:30 on 2026-10-01 and printed per-file descriptives, and the lane's
  proposer and two judges read its committed ENIGMA manifest table (per-file effect min / max). Every reading in this
  plan was written after that (v1 was first written at 14:40:51), and none uses those values; the facts and the
  orchestrator's declaration are in §9. The declaration covers every reading that bears on a G2 target. The readings
  that touch the ENIGMA-derived cells (Patel, Giacomel, Hansen, Liu T3, and Level 4's sibling-disorder maps) are R1, R9,
  R11, R12, R13, R17, R24, R25, R27 and R29. The general readings R2–R7 also apply to them, as to every claim (§9, F2).
- The orchestrator decides under the operator's standing delegation (2026-09-26). Each orchestrator default this plan
  adopts is marked **[default n]**. Where a frozen text contradicts a default, the plan says so, quotes the text and pins
  the faithful reading instead. This happens at R8 (the frozen G6l rule kept), R10 (all of G1–G5, as the register asks)
  and R24 (one G3 seed rule for every use). R1 pins a reading of an ambiguous text. R11 extends its default where prereg
  §2 and §7 ask for more.

### 0.3 Gate state at writing (v1 and v2: HEAD 3d1abe3; v3 and v3.1: HEAD e49a024)
- **G2 is open.** A3's step-3 (v) record (`arcs/replication/results/step3v_record.json`, `step3v_commit` f0d5556…,
  committed 4efbae5) is an ancestor of HEAD. Re-checked at e49a024 for v3 with `git merge-base --is-ancestor`: the
  record's commit and 4efbae5 are both ancestors.
- **G1 is open at 4fd7942ece3743d75741fa37c75212a9a6d2a520** (route (ii), `claims_register.md:95-100`). That commit is
  A3's "(b-ii) declined" record: the A3 `ARC.md` block "### 2026-10-01 - session 10", with the marker lines and the two
  attestation lines of §2.2. It was committed 2026-10-01T16:10:42+02:00, after the session-9 NOTICE (introduced in
  6b855c9, 2026-09-29T16:55:40+02:00) and the session-9 handoff message (1a8e46e, 2026-09-30T08:06:53+02:00). A1's
  record file `arcs/audit/run_manifests/G1/g1_open_record.json`, naming that commit, was written in e49a024
  (2026-10-01T16:12:00+02:00). The §2.2 check returns True on this record at e49a024 (simulated for v3 and again for
  v3.1, §2.2). **That block is never edited:** `g1_open()` pins it byte-identical.
- **No G1 material has been opened.** A3's record and A1's ARC entry (e49a024) both state it, and this plan opens none
  before it is frozen and the runner and plants are reviewed (§18).
- **Dear stays deferred** pending provenance (`:1736`). **Vairam / Roy stays deferred** (`:1648-1653`).

### 0.4 What the v1 author and the v2, v3 and v3.1 revisers saw, and did not see; the exposure before v1
- **Read:**
  - the frozen texts above;
  - TSV rows, read by script (fields and counts only);
  - engine and A3 code;
  - the listing-level `register_maps/IDENTITY_prefreeze.json`;
  - result headers: `e3_gates_a5.json`, `e3_gates.md`, `e4_ahba_matrices.json`;
  - abagen 0.1.3 source in `env/venv_ref`;
  - `docs/ETHICS_PRIVACY.md`;
  - the exploration lane's `artifacts/explore/opened_paths.log` (counts and file names only, §9);
  - the scout's inventory (`…/scratchpad/scout/a1-runplan-inputs.md`).
- **Probed:** `docker version` (client and server 28.1.1, 2026-10-01). Rscript is absent from PATH.
- **v2 reviser (2026-10-01), additionally read:**
  - the two reviews;
  - `results/e3_gates_a3.md` (the frozen battery's rates);
  - the A3 step-3 (v) checkpoint timings (`seconds` of the 79 `ck_test*.json` files);
  - the Moreau, Benkarim, Park and Pretzsch drafts in `register_work/`;
  - the four kept column headers of the Gandal 2018 DGE reduction (no row);
  - `register_maps/mist64_classes.json`;
  - `opened_paths.log` through a masked script (counts, timestamps and the 19 ENIGMA Toolbox CortThick file names only);
  - the first four docstring lines of the lane's `fetch_enigma_sumstats.py`, and the first 30 file names of
    `explore/discovery/results/` (none named for ENIGMA);
  - the FreeSurfer 7.4.1 download directory and its HEAD responses (R16).
- **v3 reviser (2026-10-01), additionally read:**
  - the re-check and its eight C points;
  - through read-only git: the A3 `ARC.md` at 4fd7942, at its parent and at HEAD e49a024 (the session-9 NOTICE, the
    session-10 block and the two `###` sections that e49a024 appended to A3's Results), and the A1 `ARC.md` entry of
    e49a024;
  - `run_manifests/G1/g1_open_record.json` (four fields, no data) and `step3v_record.json` (`step` and
    `step3v_commit` only);
  - the cited lines of the register, the prereg, amendment 5, `register_work/moreau2020mutations.md`, A1's `ARC.md`, and
    `privacy_guard.py` (`_declared_positions`, `read_openpyxl`, `xlrd_cell_reader`);
  - the field names and roi range of `register_maps/mist64_classes.json`, and the source block of
    `register_sets/gandal2018_asd_down.json` (URL and sha256);
  - `opened_paths.log` through a masked script that printed counts and timestamps only (§9).
- **v3.1 reviser (2026-10-01), additionally read:**
  - the review of v3 and its eight points;
  - the cited lines of the register (`:66-120`, `:140-146`, `:812-823`, `:1087-1103`), the prereg (`:134-150`), A1's
    `ARC.md` (`:574-576`, `:836-843`) and `privacy_guard.py` (its docstring `:1-80`, and `:200-356`: `classify`,
    `_declared_positions`, `read_openpyxl`, `xlrd_cell_reader`); the v2 reviser's scratch `feas.py`;
  - counts over the `label`, `name` and `roi` fields of `register_maps/mist64_classes.json` (no value printed);
  - through read-only git: the commit times of 6b855c9, 1a8e46e, 4fd7942 and e49a024, the "(b-ii)" lines of
    `NEXT_SESSION.md` at 1a8e46e, the A3 `ARC.md` at HEAD and in the working copy (supersession-marker counts only), and
    the listing of `arcs/audit/` (no A1 run output exists, §18 F6);
  - `opened_paths.log` through masked scripts that printed counts and timestamps only (§9);
  - the timestamps of the Write / Edit tool inputs on this file in this session's subagent transcripts. The lane run's
    transcript folder (`…\subagents\workflows\wf_a992ecba-de5\`) was skipped unread.
- **Not opened by any of them:**
  - any gated carrier, map, supplement, NeuroVault image or decoder output;
  - any exploration-lane result or table on the ENIGMA-ASD maps, including the committed manifest table
    `explore/discovery/data_manifests/enigma_toolbox_sumstats_table.csv`;
  - the per-file descriptives that the lane's protocol judge printed at 14:30 (§9). No author or reviser of this plan
    saw them; the orchestrator printed the judge's commands, not their output (A3 `ARC.md` at HEAD, "Post-freeze
    exposure");
  - the lane run's workflow record and agent transcripts, which hold some of those values (§9). The review of v3 found
    that no plan author or reviser had read the workflow record (its C1 (c)).
- **Exposure order.** The ENIGMA-ASD tables were opened by the lane at 14:25:16 (path check only), 14:30:13 and
  14:30:43 on 2026-10-01, and the manifest table was read between 13:56 and 14:25:29 (§9). v1 of this plan was first
  written at 14:40:51, and every reading in it, v2, v3 and v3.1 was written after that (§9).

## 1. Launch assertions (the runner refuses to start unless every one holds)
Every assertion is written into each output's provenance block. A failed assertion stops the run before any statistic is
computed.

| # | assertion | expected value | source |
|---|---|---|---|
| L1 | register sha256 | 897b2112… (§0.1) | `FROZEN.txt` |
| L2 | TSV sha256 (the header's line-2 text "DRAFT … NOT frozen" is ignored; only the hash counts) | d6499b5d… | freeze manifest |
| L3 | freeze manifest sha256 | 38c2a507…; each of its 36 entries equal at the run commit | `FROZEN.txt` / manifest |
| L4 | prereg + amendments 1–5 | `FROZEN.txt` lines 1–6 | `FROZEN.txt` |
| L5 | this plan | its `FROZEN.txt` line, once frozen; committed with 0 CR, so the LF blob has the same hash | `FROZEN.txt` |
| L6 | AHBA matrix files | `dk_expr.csv.gz` 949aeb01…, `aal_expr.csv.gz` 44ef457c…, `mist64_expr.csv.gz` 7a7a6e22…; atlas info `dk` abb69a9b…, `aal` 22e758a7…, `mist64` 4dafc820… | frozen `src_register/s_build.py:155-163` |
| L7 | AHBA matrix identity (`hash_pandas_object`, checked in `env/venv_ref`, once per launch) | dk 9c66a205…, aal 0dbbb50c…, mist64 7f750213… | `results/e4_ahba_matrices.json`; `register_maps/mist64_ahba_matrix.json` |
| L8 | K1 under amendment 5 | `results/e3_gates_a5.json`: git blob 18530868… at the run commit; sha256 of its LF bytes 3952430c…, and of the same bytes with every LF written as CRLF 6d5533b3… (v1's pin, the main tree's CRLF copy); `K1_status` "not fired", `stop` false, `dirty` false, `partial_certification` []; its `gates_json` sha256 105e81f1… equals the CRLF form of `results/e3_gates_a3.json` (blob fb41a15e…, LF 918606d8…; amendment 5 pins 105e81f1…, `prereg_amend_5.md:23`) | amendment 5 §0, §5 |
| L9 | catch curves present | `results/e3_catch_curves_a5.json`: blob 82fa016f…; LF sha256 c9d8d900…; CRLF form b9ff7fed… | amendment 5 §3 |
| L10 | scope labels in force | exactly the three `scope_labels` of `e3_gates_a5.json` (gradient: V-AAL, V-CC200; N1: V-CC200); replica (a) 150/1000, (c) 131/1000 → no dk-ctx N1 label from §4.4 | amendment 5 §4 |
| L11 | clean pinned worktree | `git status --porcelain` empty (untracked files included); HEAD = the commit named on the command line; the code hash of every imported module is recorded (A3 precedent `step3v_common.py:277` `launch_check`); L1–L15 are exercised in a freshly created worktree by P1 | §2.3 |
| L12 | register numbers the runner uses | m 207 overall; m per target as the §4 block (`:1849-1896`); rows 692; per-gate rows G1 380 / G2 194 / none 115 / G1+G2 3 | TSV (re-counted) |
| L13 | privacy guard | `privacy_guard.py` sha256 430f86dc… (manifest); its self-test re-run passes 46 / 46 before any workbook is opened | `:832-833` |
| L14 | carrier engine (G1 only) | `carrier_test.py selftest --workdir <dir>` equal to the frozen record (`:1288-1291`); pdfplumber == 0.11.10 before any PDF carrier (`:1301-1302`); `carrier_test.py` is started only by the gate launcher (§2.2) | register §1.11 item 8 |
| L15 | gate checks | G2: the step-3 (v) record valid and an ancestor of HEAD (§2.1). G1: `g1_open()` true (§2.2). Each check runs before the gate's first network request, carrier test or file open | register §0 (`:116-117`: a gate covers "downloads, opening carriers, …") |

**Line endings (both reviews: L8 and L9 as v1 wrote them could not pass in the worktree L11 requires).** The repository
checks text out with LF (`.gitattributes` `* text=auto eol=lf`). The main tree's working copies of the three JSON files
above are CRLF (340, 865 and 103,653 CR), so a clean worktree holds bytes whose sha256 differs from v1's pins. Every
text-file assertion is therefore made on the git blob id and on LF-normalised bytes. Where a frozen text or v1 pinned the
CRLF hash, the runner also rebuilds the CRLF form from the LF bytes (each LF written as CRLF) and checks that hash. On
2026-10-01 the rebuild reproduced all three CRLF hashes exactly, and `git cat-file --filters HEAD:<path>` gave the LF
values above. Every other pinned text file (L1–L4, L13) has 0 CR in both forms. The gate files are never regenerated: a
regeneration is a re-evaluation, which re-arms K1 (`prereg_amend_5.md:274-275`).

## 2. Gate checks, worktree, provenance

### 2.1 G2 check
`step3v_open()` is the logic of `explore/discovery/guard.py:53-67` (`step3v_recorded`), copied into the runner, not
imported:
- the record JSON parses, has `step` "3 (v)" and a 40-hex `step3v_commit`;
- that commit exists (`git cat-file -e <c>^{commit}`) and is an ancestor of HEAD;
- 4efbae5 is also an ancestor of HEAD.

Anything else → False (fail closed).

### 2.2 FAIL-CLOSED G1 check (every script that downloads or opens a G1 carrier, map, supplement, decoder output or set)
It is modelled on `step3v_recorded()`. The record file is `arcs/audit/run_manifests/G1/g1_open_record.json`. The
orchestrator wrote it in e49a024, after A3's record was committed in 4fd7942, with
`{"record": "(b-ii) declined", "route": "ii", "bii_commit": "4fd7942ece3743d75741fa37c75212a9a6d2a520",
"a3_arc_session": 10}`. The check reads the record **from HEAD's tree** (`git show HEAD:<path>`), never from the working
copy, so an uncommitted or locally edited record opens nothing. A non-hex value in `bii_commit` (such as the
placeholder v1 and v2 carried) fails the hex test.

**Routes.** The register opens G1 by one of three routes (`claims_register.md:92-103`). `g1_open()` implements route (ii)
only. Under route (i) (A3's ABIDE II results committed) or route (iii) (another A3 path ending ABIDE II analysis) it
returns False, so G1 stays closed until a frozen amendment of this plan adds that route's check.

**A3's record block** (written by the orchestrator in a new A3 ARC session the operator opens) carries, besides the two
marker lines, two attestation lines:
- `NOTICE-SESSION: <id of the session that gave the session-9 notice>`;
- `OPERATOR-OPENED: session <id>; opened <ISO-8601 time with a UTC offset>; message sha256 <64 hex>`, where the hash is
  that of the operator's opening message of the recording session, so the operator can verify it without the message
  being copied.

**Definitions used by the check** (v3, each missing or ambiguous in v2; the session-message commit and the supersession
match added in v3.1; see "Simulated" below):
- **Section of session n** in an ARC text: the line equal to `### <YYYY-MM-DD> - session <n>` (regex
  `^### (\d{4}-\d{2}-\d{2}) - session (\d+)$`), through the line before the next heading of level 1–3 (regex `^#{1,3} `),
  or to the end of the file. A deeper heading (`####`) stays inside the section. The heading must occur exactly once.
- **Lines:** the git blob is split on LF; a marker or attestation line is a whole line, compared exactly.
- **The NOTICE string** is `(amendment 2 §4b) - the (b-ii)-declined record` (A3 `ARC.md` line 576 at 4fd7942 and at
  e49a024, in the section of session 9).
- **The NOTICE commit** k: the first commit of `git rev-list --reverse --topo-order c -- arcs/replication/ARC.md` whose
  `ARC.md` holds the NOTICE string inside the section of session 9. On the real history this is 6b855c9.
- **The session-message commit** s (v3.1; review of v3, C6): the register's notice is the "ARC entry and session
  message" (`claims_register.md:98`). s is the first commit of `git rev-list --reverse --topo-order c -- NEXT_SESSION.md`
  whose `NEXT_SESSION.md` has a line containing the string `"(b-ii) declined" record is due in the next operator-opened
  session`. On the real history this is 1a8e46e (2026-09-30T08:06:53+02:00), the session-9 handoff. No such commit →
  False.
- **The lower time bound** is the later of the commit times of k and s.
- **Supersession match** (v3.1; review of v3, C6): a line is normalised by deleting the markdown emphasis characters `*`,
  `_` and `` ` `` and collapsing runs of white space to one space. It supersedes if the normalised line contains
  `RECORD: (b-ii) commissioned` or `RECORD: delegation revoked` anywhere. Consequence, accepted as fail-closed: an A3 ARC
  line that merely quotes a supersession marker closes G1, so A3 ARC entries never quote one (on 2026-10-01, 0 lines of
  A3 `ARC.md` match at HEAD and 0 in the working copy).
- **Times** are compared as timezone-aware instants. The OPERATOR-OPENED time is parsed by `datetime.fromisoformat`
  (`Z` or `±hh:mm`); a time without a UTC offset is refused. Commit times are the committer dates (`git show -s
  --format=%cI`), which carry their offset.

```
def g1_open() -> bool:                       # anything unexpected (any exception included) -> False
    doc = json.loads(git show HEAD:arcs/audit/run_manifests/G1/g1_open_record.json)   # HEAD's tree, not the working copy
    require doc["route"] == "ii" and doc["record"] == "(b-ii) declined"
    n = doc["a3_arc_session"]; require type(n) is int and n >= 10   # a session after the session-9 NOTICE (register :97-100)
    c = doc["bii_commit"]; require re.fullmatch(r"[0-9a-f]{40}", c)  # a non-hex placeholder fails here
    require git cat-file -e c^{commit}  and  git merge-base --is-ancestor c HEAD
    arc_c = git show c:arcs/replication/ARC.md ; arc_p = git show c^:arcs/replication/ARC.md
    arc_h = git show HEAD:arcs/replication/ARC.md
    blk = the section of session n in arc_c                     # heading exactly once (Definitions)
    require "RECORD: (b-ii) declined" and "RECORD: no ABIDE II analysis will run" are lines of blk
    require blk has exactly one line starting "NOTICE-SESSION:" and one starting "OPERATOR-OPENED:", each matching
        ^NOTICE-SESSION: ([^;\s]+)$  and  ^OPERATOR-OPENED: session ([^;\s]+); opened ([^;\s]+); message sha256 ([0-9a-f]{64})$
    require the two session ids differ
    k = the NOTICE commit; s = the session-message commit       # each found by its walk over c's history; none -> False
    require max(commit_time(k), commit_time(s)) < opened <= commit_time(c)   # timezone-aware (Definitions)
    require neither marker line is a line of arc_p              # commit c itself introduces the record
    require the section of session n in arc_h exists exactly once and sha256(it) == sha256(blk)   # byte-identical
    require arc_h's section of session 9 still holds the NOTICE string
    require no normalised line of arc_h contains "RECORD: (b-ii) commissioned" or "RECORD: delegation revoked"
    return True
def require_g1_open(who): if not g1_open(): raise PermissionError(f"G1 CLOSED ({who}): ...")
```

**Simulated before the freeze** (v3: scratch `…/scratchpad/runplan_v3/g1sim.py`; v3.1:
`…/scratchpad/runplan_v31/g1sim_v31.py`, output beside it; programme venv, read-only git on the real repository).
- **On the real record** (HEAD e49a024; record file read from HEAD, equal to the working copy), `g1_open()` returns
  **True** under the v3.1 spec, as under v3's:
  - the section of session 10 at 4fd7942 is A3 `ARC.md` lines 611–639 (29 lines), and its sha256 is the same at HEAD;
  - the NOTICE commit found by the walk is 6b855c9 (2026-09-29T16:55:40+02:00), and the session-message commit is
    1a8e46e (2026-09-30T08:06:53+02:00);
  - OPERATOR-OPENED 2026-10-01T11:43:09Z lies after both and before 4fd7942's commit time (2026-10-01T16:10:42+02:00);
  - no line of A3 `ARC.md` matches a supersession marker after normalisation, at HEAD or in the working copy.
- **v3.1 changes (review of v3, C6).** v3 matched a supersession marker only at the start of a line, so a later
  "**RECORD: (b-ii) commissioned** by the operator" left G1 open; the match is now anywhere in a normalised line. v3's
  lower time bound was the NOTICE commit only; it is now the later of the NOTICE commit and the session-message commit,
  as the register's notice is both. Re-run in scratch, the v3 spec opens G1 on all 7 cases added below; the v3.1 spec
  refuses them.
- **Spec fixes the v3 simulation forced** (the ARC is not touched):
  - **Block extent.** Read literally, v2's "the section … under the heading" ran to the next *session* heading or to the
    end of the file. At 4fd7942 no session heading follows session 10, so that block ran through `## Results` and
    `## Closeout` (147 lines). e49a024 then appended two `###` sections to A3's Results (167 lines at HEAD), so the
    byte-identity check failed and v2's check returned **False on the real record**. v3 ends a section at the next
    heading of level 1–3, which the A3 ARC uses for every session and for `## Results`.
  - **Timezone.** v2 left the comparison unstated. The attestation is in UTC (`Z`) and the commit dates in +02:00. A
    local-clock string comparison happens to give the right answer on the real record. In a scratch repository, though,
    it refused a valid attestation at 15:30Z against a 16:55:40+02:00 notice. v3 compares timezone-aware instants and
    refuses an attestation time that carries no offset.
  - **The NOTICE commit** is now defined (the rev-list walk above), and an upper bound is added: the operator-opened
    session must have been opened no later than the record's commit.
  - **Record source.** v2 read the working copy, so an uncommitted record opened G1 in the scratch test. v3 reads HEAD's
    tree.
  - **Supersession** is checked on every line of HEAD's ARC, not only "after blk", and the session heading must occur
    exactly once at c and at HEAD.
- **P21 in scratch git repositories (v3.1 re-run):** 35 / 35 cases as expected. The scratch history is the NOTICE
  commit (2026-09-29T16:55:40+02:00), the session-message commit (2026-09-30T08:06:53+02:00), the record commit
  (2026-10-01T16:10:42+02:00) and the record file. Three correct records open: the standard one (2026-10-01T11:43:09Z),
  an attestation at 2026-09-30T06:30:00Z (a local-clock string comparison would refuse it), and one at
  2026-09-30T08:30:00+02:00. (v3's two other positives, 2026-09-29T15:30Z and 2026-09-29T17:00+02:00, lie before the
  session message; the second is now a refusal case.) These 32 are refused:
  - the placeholder; an upper-case id; a 39-hex id; an unknown commit; a non-ancestor (an unmerged branch);
  - a3_arc_session 9; a record block under a session-9 heading; the block edited at HEAD;
  - a missing marker; a block already in c^ (the record names the next commit);
  - a missing OPERATOR-OPENED line; a missing NOTICE-SESSION line; two OPERATOR-OPENED lines; equal session ids;
  - an attestation before the NOTICE commit (2026-09-29T16:50+02:00, and 14:00Z); after the NOTICE commit but before
    the session-message commit (2026-09-29T17:00+02:00, and 2026-09-30T08:00+02:00); no session message in c's history;
    a session message committed only after the record; an attestation without a UTC offset; an attestation after the
    record commit;
  - a later "(b-ii) commissioned" and a later "delegation revoked", each at a line start; a marker mid-line in bold, one
    with emphasis inside it ("**RECORD:** (b-ii) commissioned"), and one mid-line in backticks; route "i"; route "iii";
  - a record not committed; the session-9 NOTICE removed at HEAD; the session-10 heading twice at HEAD.

  WP1 ports this logic into `a1_audit` and re-runs it as P21.
- The marker lines are what route (ii) of `claims_register.md:95-100` requires: "A3 records that no ABIDE II analysis will
  run **and** the (b-ii) fallback is recorded as declined". The orchestrator writes them into A3's record. A record without
  them keeps G1 closed.
- **Necessary, not sufficient.** No code can see whether the operator opened the recording session, or whether it is a
  continuation, loop or scheduled run of the notifying session (register `:97-100`). The attestation lines are the
  orchestrator's statement, checkable by the operator through the hash. A false attestation is a process incident,
  reported to the operator; the check only refuses records that are malformed, early, edited, superseded or
  self-attesting.
- **Gate launcher.** `a1_audit.gate_launch <gate> -- <command>` runs the gate's check (`step3v_open()` or
  `require_g1_open()`) and only then starts the command in a subprocess. The frozen `carrier_test.py`, which holds no gate
  check, is run only through it. `fetch_extract.py` (§8) calls the same check before its first network request.
- **Plants (P21):**
  - each of the 32 refusal cases listed under "Simulated" is refused;
  - with G1 closed, `fetch_extract.py` makes no network request (its fetch function replaced by one that raises if
    called) and the launcher refuses to start `carrier_test.py`;
  - the three correct records in a scratch git repository open, and the real record at the run commit opens.
- **The A3 record block is never edited** (A3 `ARC.md`, "### 2026-10-01 - session 10"). An edit would close G1 under
  this check. Every later A3 entry goes into a new section.

### 2.3 Worktree rule (claim-bearing runs only from a clean, pinned, detached worktree)
- **Create:** `git worktree add --detach D:\tmp\asdg_wt_a1_<gate>_<short> <commit>`. Then create the artifacts junction
  `mklink /J <wt>\artifacts D:\RESEARCH\asd-imaging-genetics\artifacts`, as the existing A3 worktrees have (for example
  `D:\tmp\asdg_wt_s3v_66c8e17\artifacts` is a JUNCTION to the main `artifacts\`).
- **Junction warning:** a plain `git worktree remove` on such a worktree deletes the **main** artifacts through the
  junction. To remove one:
  1. unlink the junction itself, without recursion (`cmd /c rmdir <wt>\artifacts`; never `rmdir /s`,
     `Remove-Item -Recurse` or `--force`);
  2. verify that `D:\RESEARCH\asd-imaging-genetics\artifacts\ahba\aal_expr.csv.gz` still exists and still hashes to
     44ef457c…;
  3. only then run `git worktree remove <wt>`.

  Removing a worktree is the orchestrator's or operator's step, never a worker's.
- The launch assertions read the worktree's own LF bytes (§1, line endings).
- Outputs are written under the main repository's `arcs/audit/results/a1_run/` (through the run directory), and the
  orchestrator commits them.

### 2.4 Provenance per output
Every output records:
- the run commit and the worktree path;
- the code hashes, the launch-assertion values and the gate-check result;
- per row: the row's SeedSequence keys and integer seeds (R7), the input hashes, the start and end times, and the host.

## 3. Inventory against register §1.10 (0)–(5) (`claims_register.md:1088-1103`)
| step | exists (reuse) | this plan builds (WP §18) |
|---|---|---|
| (0) pre-freeze | S-build (374 entries, `register_sets/MANIFEST.json`); MIST64 classes and matrix; carrier spec and self-test; `IDENTITY_prefreeze.json` (41 objects / 79 probes) | — |
| (1)/(2) material | Segura NIfTIs, Moreau xlsx, BrainSpan matrix, PCP AAL atlas on E:; G2 local copies (Patel PDF, Hansen CSVs, Liu T3 CSVs, Pretzsch derived CSV, Leyhausen GIFTIs) | the fetch-and-extract wrapper (§8); downloads under each gate; post-freeze manifests in `register_maps/post_freeze/<gate>/` and `register_sets/post_freeze/<gate>/` (R18) |
| (3) runner | `src/asdg/` (cascade, spatial incl. `site_null` exact enumeration, genesets, species, verdict, brainspan); A3's audit-scale helpers (`h_verdicts.py` `g1_null_chunked` / `g3m_null_chunked` :215-244, `g6l_screen` :247, `g6l_pool` :285, `species_draws` :319, `assemble_verdict` :348, `claim_verdict` :369, `PLS1R2` :1103, `descriptors` :1163, `reading` :1273; `h_common.ClassContext` :141; `step3v_common.Checkpoints` :644, `run_pending` :710) | `arcs/audit/src/a1_audit/` (§4): loader, seeds, gate checks, T-form adapters, descriptor legs, map loaders and re-parcellation, reproduction functionals, readings and labels (amendment 5 §3–§4), results writer, plants. A3 helpers are **copied** (not imported; A3's readings such as its two-sided rule differ, R1), each with a bit-identity test against the A3 function on toy data (P0) |
| (4) run | — | §14 schedule; order §18 |
| (5) results | — | §16 |

**Placement rule.** New code goes in `arcs/audit/src/a1_audit/`, never in `src_register/`. The freeze manifest describes
itself as holding "every register_maps/*.json and every src_register/*.py" (`register_freeze_manifest.json` "what"), so a
new file there would falsify that description. `prereg.md:11-12` puts run code in `arcs/audit/src/`.

## 4. Runner architecture
- **Loader:** parses the TSV after L1–L3 and keys every row by its `row` number (the seed key, `:1817-1819`). The status of
  a gated row reads "deferred (gate Gx closed); <status under the gate>". Once Gx's check passes, the runner applies the
  part after "; ". Otherwise the row stays deferred.
- **Dispatch by `claim_form`:**
  - set-vs-map, decoded-list, PLS-enrichment and component go to their adapters (R3);
  - gene-set-only goes to the Liu adapter (R10);
  - "other" goes to its registered descriptor form (MOR-T1/T2: R21; BENK-C2-SD/-DD and PARK-C5: R28);
  - Giacomel's signed-weight cells (GIA-C01 … C06, C19 … C24, GIA-MDD-C1 / C5 / C10; TSV rows 103–117) carry
    `claim_form` set-vs-map in the TSV and the status "not testable as stated: signed-weight set score". The dispatcher
    routes them by that status to the signed-weight descriptor adapter (register §2.3, `:1469-1473`; P15), never to the
    set-vs-map verdict;
  - rows whose status is not auditable, not testable (< 5), deferred, out of scope, or "not testable as stated" without a
    registered T form ("none for count or composition claims", `:298-299`) are written with their TSV status and no
    statistic.
- **Legs (register §1.9, `:1068-1082`; seed leg numbers in brackets):**

  | pass | leg | count | applies to |
  |---|---|---|---|
  | verdict | Level 0 (parametric) | — | all full-verdict forms |
  | verdict | S1c [0], S2c [1] (exact if ≤ 10,000 patterns, `spatial.site_null`) | 10,000 | all forms incl. component |
  | verdict | G1 [2], G3m [3], G6s [4] (exact if 2^rank ≤ 10,000), G6l [5] (every eligible seed; 10,000 sampled if more) | 10,000 | full-verdict forms |
  | verdict | component Level 0 permutation [8]; re-selection [10] | 10,000 | component / selected lists |
  | descriptor | G2 [11], G4 [12], G5 [13] | 10,000 | full-verdict forms |
  | descriptor | J1 [14] (K = 1,000 G2 sets + 10,000 S1c + 10,000 S2c) | — | full-verdict forms |
  | descriptor | naive joint [15] (10,000 G1 sets + 10,000 S1) | — | full-verdict forms |
  | descriptor | T_abs: S1c [21], S2c [22], G1 [23], G3m [24], G6l [25] | 10,000 | decoded-list claims and pooled lists (`:309-313`) |
  | descriptor | Level-2 G1, unconditioned (R24) | the leg-2 sets | full-verdict forms |
  | descriptor | G3 [first spawned child of leg 3's key, R24] | 10,000 | Level 2 of full-verdict forms; Liu (R10); Giacomel's signed-weight cells |
  | sensitivity | the verdict legs on the ≥ 2-donor parcel set (R11) | as the verdict pass | every claim with a verdict |

- **Checkpoints:** one per row × leg (A3 `Checkpoints` / `run_pending`, resumable). Logs are unbuffered (`python -u`).
  Runs use 20 jobs with `OMP_NUM_THREADS=1`.
- **Memory:** surrogate refits (the decoded-list and PLS site legs, J1, the naive joint) form Zᵀ Y* in chunks of at most
  1,000 surrogates (15,633 × 1,000 float64 ≈ 125 MB; all 20,000 at once would be ≈ 2.5 GB per job). Each job's peak
  working set is logged per row, and a job above 2.5 GB is a defect: 20 jobs × 2.5 GB = 50 GB of this box's 63.8 GB
  (i9-12900K, 16 cores / 24 threads; checked 2026-10-01).
- **Shared G6l screens:** the exact screen (which seeds are eligible, and their offset sets O_g) depends only on
  (S, class, analysis parcels). It is computed once per such triple and serves every row's own G6l stream (legs 5 and 25)
  through `g6l_screen`'s multi-stream pass (`h_verdicts.py:247`). Every per-row stream and seed stays as registered; P0
  shows that shared and unshared screens give bit-identical p's.
- **Analysis parcels:** a parcel enters iff y is finite there and the parcel has ≥ 1 AHBA sample (`prereg.md:57-58`).
  Primary parcels are left + midline (`:55-56`); dk-ctx means the 34 left DK cortical parcels. Counts of parcels kept and
  dropped are written per map.
- **Gene scaling, by form** (v1's unqualified "genes are z-scored" would have changed the set-vs-map statistic; both
  reviews):
  - **set-vs-map** (51 TSV rows, 18 in m): T, Level 0, its site leg, its species legs (as frozen in
    `src/asdg/species.py`) and its descriptor legs use the §3.1 abagen-normalised values **unchanged**. The set score is
    the per-parcel mean of the member columns: "set score (per-parcel mean of the member genes' abagen-normalised
    expression)" (`prereg.md:113-114`); "set score = per-parcel mean of the set's genes on the §3.1 matrix"
    (`claims_register.md:283-284`); `genesets.Universe.scores` averages the unstandardised X. Nothing is z-scored for
    this form;
  - **decoded-list, PLS-enrichment and T_abs**, with their legs: genes are z-scored over the claim's analysis parcels
    ("⟨ŷ, s_z⟩", `claims_register.md:285-286`; "weights ∝ Xᵀy on z-scored genes", `prereg.md:177`; "the species leg acts
    on the z-scored set score", `prereg_amend_3.md:107`);
  - **component forms:** as prereg §4.7 (`cascade.pls1` z-scores internally; `PLSRegression(scale=True)`); a fixed
    component's r uses the component as given.

  P0 (b) asserts the set-vs-map case.

## 5. Readings pinned now (the 23 items, then the further ones the drafting and the reviews found)
Format: **Text** (quoted, `file:line`) → **Reading** → **Why now** → **Plant / fallback**. Every reading was chosen on
2026-10-01, before this audit opened any G2 or G1 map, carrier, supplement, NeuroVault image or decoder output, and no
author or reviser of this plan opened any. None of them depends on a value of any audit map. All of them were written
after the exploration lane's protocol judge opened the ENIGMA-ASD tables (14:25–14:30; the plan was first written at
14:40:51). None uses the per-file descriptives it printed or the manifest table's effect ranges the lane read: no
author or reviser saw them, and the orchestrator did not see the values. The facts and the declaration are in §9.

**R1. Two-sided p and resolution floors [default 1, read for the claim's direction].**
- **Text:**
  - "two-sided (p = 2·min, capped at 1), labelled (prereg §4.7)" (`claims_register.md:295-296`);
  - "the test is two-sided (p = 2·min of the one-sided p's)" (`prereg.md:184-185`);
  - "All p-values are one-sided in the registered direction, (k + 1)/(n + 1)" (`prereg.md:117`);
  - the verdict is taken "For a claim (map y, set S, statistic T …, registered direction)" (`prereg_amend_3.md:73`), and a
    claim is "(map y, set S or component, statistic T, direction)" (`claims_register.md:187`);
  - floors: "A leg with N null states has the smallest attainable p 1/(N + 1) (2/(N + 1) for exact G6s …)"
    (`prereg_amend_3.md:94-95`);
  - Giacomel subcortex: "floor 2/65 ≈ .031 ≥ .025; two-sided" (`claims_register.md:1462-1463`).
- **Reading** (a reading of an ambiguous text, not an addition to it; v1's wording "the text adds a requirement" is
  withdrawn):
  - For each direction d ∈ {+, −}, every leg and sub-leg gives its one-sided p_leg(d) by (k + 1)/(n + 1); Level 0 uses
    the parametric sf or cdf. The site leg is max(p_S1c(d), p_S2c(d)) and the species leg max(p_G1(d), p_G3m(d),
    p_G6s(d), p_G6l(d)), with one d for every sub-leg.
  - The claim's direction is d* = argmin_d max(p_L0(d), p_site(d), p_species(d)). A tie goes to the sign of the observed
    T (+ if T = 0).
  - Each leg's **reported p** is min(1, 2·p_leg(d*)), with both one-sided p's beside it. The **conjunction p** is the max
    of the reported p's, i.e. min(1, 2·min_d max_leg p_leg(d)): "p = 2·min of the one-sided p's" (`prereg.md:184-185`) applied
    to the claim's p. Amendment 3 §2's "survives iff p_L0, p_site and p_species are each < .025; conjunction p = max"
    (`prereg_amend_3.md:76`) and `verdict.py`'s rule (survives = status ok and max(p) < α) then hold as frozen, and the
    conjunction p is the one BH uses (R29). Under H0 the rule is a Bonferroni bound over the two directions: its
    false-alarm rate is at most the sum, over d, of the one-sided verdict's rate at .0125.
  - The literal per-leg min(1, 2·min(p(+), p(−))) is reported beside each leg, labelled "per-leg two-sided (not the
    verdict p)". It never enters the verdict, the conjunction p or BH.
  - **Two-cohort claims** (Mamat's two-sided claims on the ABIDE I and ABIDE II maps; `claims_register.md:1639-1641`; P14):
    the claim has one d* = argmin_d of the max over both maps' legs, and both maps must survive in d*. A claim is
    "(map y, set S or component, statistic T, direction)" (`claims_register.md:187`), so a two-cohort claim has one
    direction.
  - The resolution label uses the smallest attainable reported p, twice the leg's one-sided floor.
  - Giacomel's §2.3 figure of 2/65 is the one-sided floor. Its conclusion is unchanged under doubling (4/65 ≈ .062 ≥ .025).
  - A3's rule (the direction is the sign of the observed T; that p is doubled; `h_verdicts.py:147-157`) belongs to another
    arc and is not used. It gives the same d* whenever the observed T's sign minimises the conjunction (§19).
- **Why now:** this changes resolution statuses near the floor and the two-sided survivals. 77 of the 207 claims in m
  carry "two-sided" in their TSV direction field (75 begin with it; Leyhausen 27). G2 holds 24 Giacomel published-null
  cells, Liu T3, 27 Leyhausen claims and Patel's 6 null panels, so the reading must be fixed before this audit reads
  any G2 map (§9 for the lane's earlier exposure).
- **Plants:** P8 (a) to (c); P9.

**R2. Decoded-list species leg on multi-class spaces (V-AAL; [default 2]).**
- **Text:**
  - the register's decoded-list T: "species leg per amendment 3 §2's enrichment rule (G1, G3m, G6l = mean over each null
    set, per-gene r and y fixed; G6s on the z-scored matrix; every null conditioned s_B(S) + s_W(R))"
    (`claims_register.md:287-289`);
  - amendment 3: "Every species null set R is evaluated as s_B(S) + s_W(R): S's between-class part replaces R's"
    (`prereg_amend_3.md:85-86`), and "G1, G3m and G6l recompute each null set's mean PLS1 weight, weights and y fixed"
    (`:107-108`);
  - amendment 4: "G1, G3m and G6l recompute the mean over each null set, with the per-gene statistics and y fixed"
    (`prereg_amend_4.md:96-97`);
  - precedence: the register governs the TSV and the drafts (`:63-64`) but implements amendments 3–5 (`:57-58`) and may
    not redefine them (`:1102-1103`).
- **Reading:** the clauses are not in conflict once each per-gene r is decomposed. With z_g the gene's profile, z-scored
  over the analysis parcels, and ŷ the standardised y:
  - r_g = ⟨ŷ, z_g⟩ / n = r_g^B + r_g^W, the between-class part (class means of z_g) plus the within-class part;
  - the species null statistic is T*(R) = mean_{g∈S} r_g^B + mean_{g∈R} r_g^W.

  This equals ⟨ŷ, s_B(S) + s_W(R)⟩ / n on the z-scored matrix, so "every null conditioned" holds. It is "the mean over
  each null set" of a per-gene statistic that is fixed with y, so the amendment-4 clause holds as well.
  - On a single class r_g^B ≡ 0, and the two forms coincide exactly. That is why dk-ctx cells are unaffected.
  - The same decomposition applies to the PLS-enrichment weights (w ∝ Zᵀy is linear in z_g).
  - G6s acts on the within-class, gene-side-centred z-scored matrix (`prereg_amend_3.md:107-108`).
  - T_abs legs are explicitly unconditioned ("unconditioned G1, G3m, G6l", `claims_register.md:311`). That contrast
    confirms that the signed decoded-list legs are conditioned.
- **Why now:** this bears on Segura (ungated, V-AAL) and on Buch and Pagani (G1, V-AAL).
- **Plants:** P5. The unconditioned "mean of whole r over R" is computed **in plants only**, as a reference leg (amendment
  3's precedent for reference legs that are not valid nulls, `prereg_amend_3.md:174-178`), never on a claim. P5 shows
  equality on single-class maps (to 1e-12). On a multi-class between-class plant, P25 (c) requires the unconditioned
  G1 / G3m legs to reject and the conditioned leg to stay calibrated.

**R3. The registered T forms are built and planted [default 3].**
- **Text:**
  - decoded-list T = "mean over S of the per-gene Pearson r between y and the gene's expression (= ⟨ŷ, s_z⟩); Level 0 =
    Welch t of S's per-gene r against the rest of the universe; site leg recomputes every per-gene r on each surrogate"
    (`claims_register.md:285-287`; `prereg_amend_4.md:86-90`);
  - PLS enrichment: "T = mean PLS1 weight of S's genes, component oriented so corr(score, y) > 0; Level 0 Welch t; PLS1
    refit on every surrogate" (`:290-291`), with "Level 3 = J1 with r replaced by the mean weight (refit per surrogate)"
    (`prereg.md:188-189`).
- **Reading:**
  - **Decoded-list:** T = ⟨ŷ, s_z(S)⟩ / n with s_z(S) **not** re-standardised. The engine's scorer
    `WithinClassBasis._p` takes the Pearson r of each null score with y (`src/asdg/species.py:102-104`). That is the
    set-vs-map statistic, a different one, and the decoded-list adapter does not use it.
  - **PLS-enrichment:** w = Zᵀy / ‖Zᵀy‖ over the full universe (`cascade.pls1`, `src/asdg/cascade.py:69-81`), and
    T = mean_{g∈S} w_g. Each surrogate y* refits w*. Species legs hold y fixed, so their p equals the decoded-list p (a
    constant factor), as amendment 4 states (`:88-90`).
  - **Descriptor legs** (G2–G5, J1, naive joint) score the row's own registered T, in place of r (`prereg.md:188-189`).
  - **Level 0, two-sided:** see R1.
  - Gene scaling: §4.
- **Plants:** P5, P7, P23, and P24–P26 for the new adapters' species and site legs.

**R4. J1 draws its own sets and surrogates [default 4].**
- **Text:**
  - "J1 with K = 1,000 G2 sets and 10,000 surrogates of each adopted type" with its own seed leg "14 J1"
    (`claims_register.md:1072-1073, :1081`);
  - "R_k = the claim's G2 sets (K = 1,000) … Null: z over the adopted Level-1 surrogates" (`prereg.md:157-160`).
  - The plant code reused both the site surrogates and the G2 pool (`arcs/audit/src/e3_plants.py:139-144`).
- **Reading:** J1 has its own seed leg in the register, which is meaningful only if J1 draws its own. From leg 14 it draws
  1,000 sets with the claim's G2 sampler (the same definition, so "the claim's G2 sets"), plus 10,000 S1c and 10,000 S2c
  (the adopted pair; `e3_gates.md:3` "Level-1 adoption: strat").
  - p_J1 = the larger of the two surrogate types' p (`prereg.md:160-161`).
  - J1 is unconditioned (R6) and keeps its pool-diversity and sd rules ("degenerate pool", `prereg.md:161-162`).
  - The plants' reuse is a plant-battery economy, not a definition; the register's own leg governs (`:63-64`).

**R5. Naive joint: fresh G1 pool and unstratified S1 [default 5].**
- **Text:**
  - "The naive spin+shuffle joint null (Cao 2024 S17; pool G1) is computed as a descriptor" (`prereg.md:163`);
  - "the naive joint null 10,000", seed leg "15 naive joint" (`claims_register.md:1073, :1081`);
  - the frozen plant code pairs it with S1 (`e3_plants.py:145`: `naive_joint(y, …sets["G1"]…, surr["S1"], …)`).
- **Reading:** from leg 15: 10,000 fresh G1 sets and 10,000 unstratified BrainSMASH S1 surrogates (`prereg.md:125-126`),
  paired one-to-one (`cascade.naive_joint`). The surrogate type follows the plant precedent; the text leaves it unstated.

**R6. Descriptor legs are unconditioned (decoded-list and PLS T included) [default 6].**
- **Text:**
  - amendment 3 conditions the species legs only ("Every **species** null set R …", `prereg_amend_3.md:85`);
  - it leaves the rest as frozen: "Level 2 (G1–G5), J1, the naive joint null and each species leg's own p are reported for
    every claim as descriptors" (`:100-101`);
  - their definitions (`prereg.md:134-163`, `:186-189`) carry no conditioning.
- **Reading:** G2, G4, G5, J1, the naive joint and Level-2 G1 (R24) score unconditioned null sets with the row's T. The
  species legs G1, G3m, G6s and G6l are conditioned (R2). T_abs legs are unconditioned (`:311`).

**R7. Integer seeds [default 7].**
- **Text:**
  - "`numpy.random.SeedSequence([20260925, 100 + target number, row number …, leg, map index, cell index])`"
    (`claims_register.md:1076-1082`);
  - `spatial.site_null` takes an integer seed (`src/asdg/spatial.py:170-171`).
- **Reading:**
  - A leg that needs one integer seed takes
    `seed_int = int(np.random.default_rng(SS).integers(2**31))` (A3's convention, `h_verdicts.py:398`).
  - A leg that needs a Generator takes `np.random.default_rng(SS)`.
  - A leg that needs both takes **one** generator `g = default_rng(SS)` and draws in a fixed order:
    - J1 (leg 14): S1c seed, then S2c seed, then the G2 sets;
    - naive joint (leg 15): S1 seed, then the G1 sets.
  - Multiverse, leave-one-out and ≥ 2-donor cells reuse the claim's keys (common random numbers; R11).
  - G3, which has no leg number in the register's list, uses R24's spawned key.
  - Every row records SS keys and integer seeds.
- **Plants:** P2.

**R8. Null pool smaller than S never crashes [default 8, corrected: G6l keeps its frozen rule].**
- **Text:**
  - no rule exists for G1, G3m or the J1 / naive-joint draws in this case (G2's sub-bin rule, below, covers G2 and G4,
    whose sampler is G2's: "G4 brain + coexpression: G2's sampler inside G3's background", `prereg.md:144`);
  - `rng.choice(..., replace=False)` raises (`src/asdg/genesets.py:105`, `species.py:109, :116`);
  - G6l: "Fewer than 50 eligible seeds → 'unmatched'" (`prereg_amend_3.md:131-132`);
  - G2: "If a sub-bin cannot be entered within 20 restarts the claim's G2 is 'unmatched'" (`prereg.md:140-142`);
  - G5: "pool < 2m genes → 'not applicable'" (`:148`; v3 cited `:147`, review of v3, C4);
  - "Every level's p is in the table for every claim, including after an earlier failure" (`prereg.md:173-174`);
  - the register's fallback (`claims_register.md:1102-1103`).
- **Reading:**
  - A leg with no frozen rule for this case, whose pool cannot supply a set, reads "not computable (pool < m)". This
    covers G1 (needs |U \ S| ≥ m), G3m (needs both |(B ∩ U) \ S| ≥ f and |U \ (B ∪ S)| ≥ m − f), Level-2 G3
    ("uniform from GAMBA-2,711 ∩ universe", `prereg.md:143`; needs |(B ∩ U) \ S| ≥ m, as G4 does; added in v3.1), and
    the J1 and naive-joint draws (drawn from G2 and G1 sets).
  - **G2 and G4 keep their frozen label.** G2 needs |U \ S| ≥ m, and G4 (G2's sampler inside G3's background,
    `prereg.md:144`) needs |(B ∩ U) \ S| ≥ m. A pool smaller than m means no sub-bin can be entered, so the frozen rule
    applies: "If a sub-bin cannot be entered within 20 restarts the claim's G2 is 'unmatched'" (`prereg.md:140-142`).
    G2 reads "unmatched", and G4 reads "unmatched" through G2's sampler. v2's "not computable" for G2 in the table, P10
    and §12 was a relabelling of a frozen status, and it is withdrawn (re-check, C1).
  - **G6l keeps its frozen rule.** When no window of size m fits the ranking, no seed is eligible, so the set has fewer
    than 50 eligible seeds and G6l reads "unmatched" (cannot survive), as frozen. v1's "not computable" relabelling is
    withdrawn.
  - **G6s needs no pool** (sign flips on b; `species.py:126-136`). It is computed and reported for every row.
  - **Every computable leg is computed and reported** (Level 0, the site leg, G6s, and every descriptor leg that can be
    drawn).
  - **A verdict leg G1 or G3m not computable:** the cell reads "not auditable (definition not applicable: null pool
    smaller than S)" (`claims_register.md:1102-1103`), with every computed leg beside it.
  - **Descriptor legs:** G2 and G4 read "unmatched" and G5 "not applicable" (pool < 2m), as prereg §4.3 states them
    (`prereg.md:140-148`). J1 (drawn from G2 sets) and the naive joint (drawn from G1 sets) read "not computable
    (pool < m)" where those sets cannot be drawn.
- **Affected rows.** Computed 2026-10-01 by `feas.py` (the reviser's scratch script) over the 489 TSV rows with a built
  set and a class. U = the 15,633 columns; B = GAMBA brain>body with conflicting duplicates dropped, ∩ U = 2,489 columns.

  | TSV rows | cells | in m | m (columns) | f | \|(B∩U) \ S\| | not computable | unmatched / not applicable (frozen labels) |
  |---|---|---|---|---|---|---|---|
  | 453, 454 | MAMAT-E-Tissue-URG / -DRG | yes (frozen-11 row 7) | 1,393 | 1,286 | 1,203 | G3m (verdict) | G4 "unmatched" |
  | 441 | MAMAT-E-URG-BP-2 | yes (frozen-11 row 7) | 3,619 | 774 | 1,715 | — | G4 "unmatched" |
  | 494, 495 | PAG-C1 / C2 | yes (added target) | 4,406 | 1,028 | 1,461 | — | G4 "unmatched" |
  | 332, 333, 367, 368 | BUCH-E-SZ-S1 … S4 | no (descriptor cells) | 14,607 | 2,421 | 68 | G1, G3m (verdict); J1, naive joint (descriptor) | G6l "unmatched" (verdict); G2, G4 "unmatched"; G5 "not applicable" (its pool < 2m = 29,214 > \|U\| = 15,633) (descriptor) |

  Every other of the 489 rows, PRE-GO-07 (1,497 columns) and PRE-GO-15 (1,430) included, has pools large enough for G1,
  G2 and G4 (|U \ S| and |(B∩U) \ S| ≥ m), G3m, G6l (a window of size m fits the ranking) and the J1 and naive-joint
  draws; G6s needs no pool. **G5 was not checked** (review of v3, C4; v3 said "feasible on every leg"): its pool, the
  union of the members' 20 BrainSpan nearest neighbours (`prereg.md:145-148`), is computed only when G5 is built, and
  `feas.py` has no BrainSpan step. Large sets may fall short of 2m (for example PAG-C1 / C2 need ≥ 8,812 pool genes,
  MAMAT-E-URG-BP-2 ≥ 7,238). Where a pool is < 2m, the frozen label "not applicable" applies automatically; no
  definition changes, and G5 is a descriptor leg, so no verdict moves. Level-2 G3 needs the same pool as G4, so on
  every row of the table (|(B∩U) \ S| < m) it also reads "not computable (pool < m)" (a descriptor; noticed while
  writing v3.1, and v3's §12 "every other leg is computed" corrected). Sets built under a gate are checked by the same
  rules, G5 included, when they are built.
- **Consequence (v1 missed it; first review, B1).** MAMAT-E-Tissue-URG and -DRG enter the headline population as
  full-verdict claims once G1 opens (TSV `headline_population`: "on opening: in: full-verdict claim (§1.2)"). Under this
  reading they would count as "not auditable", not as tested claims, which also removes them from the tested-only
  fraction's denominator. §6 A6 is therefore not optional (§6; §18, F4).
- **Plants:** P10.

**R9. Status precedence [default 9].**
- **Text:**
  - "A claim may carry several flags …; all are reported" (`claims_register.md:1056-1057`);
  - amendment 5: "A claim with a status, flag or label … is reported by it, as frozen" (`prereg_amend_5.md:150-152`);
  - §1.8's order "deferred > not testable (< 5) > not auditable > not testable as stated > component-level > no calibrated
    test" governs "the composition of the population" (`:1058-1062`);
  - the verdict code's order is G6l unmatched/degenerate, then uninformative, then resolution-limited
    (`src/asdg/verdict.py:30-38`, committed under amendment 3 §6);
  - the six Giacomel subcortical cells are pre-labelled "resolution-limited by construction" (`:1462-1464`; TSV rows 92,
    94, 96, 98, 100, 102).
- **Reading:**
  - Every status and flag is computed and reported.
  - A cell's *primary* status follows the register's by-construction label where one exists (the six Giacomel subcortical
    cells: "resolution-limited", with any computed status beside it). Otherwise it follows `verdict.py`'s order.
  - The population composition follows §1.8.
  - Every non-ok status already means "cannot survive" (`prereg_amend_5.md:101`), so the order changes no count.
- **Plant:** P9.

**R10. Liu gene-set-only legs [default 10, extended to G1–G5 as the register asks].**
- **Text:**
  - "G1–G5 descriptors on the paper's per-sample statistic (G5 labelled 'matching variable = tested quantity; expected
    null by construction')" (`claims_register.md:1666-1667`; TSV rows 471–477);
  - TSV rows 471–477: "analysis class 'none': no class universe of its own";
  - G1 "uniform from the matrix universe" (`prereg.md:136`);
  - G3 "uniform from GAMBA-2,711 ∩ universe" (`:143`);
  - G2 and G4 need "mean pairwise coexpression" (`:137-144`);
  - **G5** "sets are drawn from that pool with G2's sampler at S's mean coexpression ±0.02" (`:145-148`).
- **One standard (first review, B4).** v1 pinned the universe from the statistic's own data but declared the
  coexpression basis undefined, so G2, G4 and G5 (and the register's G5 label) had nothing to act on. v2 takes both from
  the same expression data the statistic is computed on.
- **Reading:**
  - **U_stat** = the genes of the expression data the statistic uses, ∩ the S-build's HGNC mapping, restricted to the
    columns that are finite and non-constant over the samples used (the engine's `Universe` rule; the count is recorded).
    The data are the BrainSpan samples for T1, T2 and the T2 descriptor cells, and the AHBA per-sample matrix (below) for
    T4 and T5. For T4/T5 the 15,633 columns are the starting set, not an asserted count.
  - S = the merged set ∩ U_stat.
  - **Coexpression** (for G2, G4 and G5) = the Pearson correlation of genes over those same samples.
  - **G1, G2, G3** (GAMBA brain>body ∩ U_stat), **G4** (G2's sampler inside G3's background) and **G5** (BrainSpan
    trajectories, G2's sampler at S's coexpression ± .02, with the register's label) all run; Level-2 p = max over G1–G5.
    G3's seed: R24.
  - The cells read "no calibrated test" whatever the legs show (`prereg_amend_5.md:163-164`), so no count moves.
- **T4/T5 sample assignment** (unstated in the text): abagen 0.1.3 in `env/venv_ref`,
  `get_expression_data(atlas=atlas-desikankilliany.nii.gz (0a28c93f…), atlas_info=its info, region_agg=None, <every other
  argument at the frozen §3.1 values>)`. With region_agg=None the function returns per-sample rows labelled by DK label
  (`abagen/allen.py:517`). The returned frame is also indexed by AHBA sample (well) ids (`allen.py:517-523`). The runner
  replaces that index by row positions at once and never prints, logs or saves those ids (§8).
  - Each sample's rank-biserial r of S against the rest is computed; a label's value is the mean over its samples.
  - Hemispheres are pooled per DK name if and only if SD7's label column names hemisphere-merged labels (read from the
    ungated SD7's label column before any value).
  - If the call fails: "not auditable (definition not applicable: abagen sample assignment not runnable)".

**R11. Mini-multiverse, leave-one-donor-out, the ≥ 2-donor sensitivity [default 11, extended by prereg §2 and §7].**
- **Text:**
  - "Mini-multiverse (reported): gene_norm ∈ {srs, zscore}; norm_matched ∈ {True, False}; leave-one-donor-out ×6;
    bilateral cell. A surviving audit claim is 'donor-robust' iff its statistic keeps its sign in ≥ 5/6" (`prereg.md:75-77`);
  - the register restricts the mini-multiverse and leave-one-donor-out to "every surviving claim"
    (`claims_register.md:1073-1075`);
  - prereg §7: MANIFEST lists "every planned (claim × level × null × parcellation × multiverse cell)" (`prereg.md:289-290`);
  - the parcel policy's "(sensitivity: ≥ 2 donors)" (`prereg.md:57-58`), which no frozen text restricts to any subset of
    claims.
- **Reading:**
  - **≥ 2-donor sensitivity: every claim with a verdict** (full or component level; v1 ran it for survivors only, without
    a textual basis). Per class, the parcels with samples from ≥ 2 donors come from abagen `return_counts=True` at the
    §3.1 settings in `env/venv_ref` (counts only recorded; donor columns are read by position, never printed). If a
    claim's parcel set is unchanged, the result is the primary one, recorded "parcel set unchanged". Otherwise every
    verdict leg and the verdict are re-run on the reduced parcels with the claim's own keys. Reported beside the primary;
    it never changes it.
  - **Mini-multiverse: every surviving claim** (`claims_register.md:1073-1075`). The two normalisation factors are
    crossed, as prereg §3.1 lists them: (srs, True) is the primary, and the cells are (zscore, True), (srs, False) and
    (zscore, False). Add the bilateral cell and leave-one-out × 6: 10 cells. Each cell re-runs **every leg** (T, Level
    0, the site leg, the species leg and the descriptor legs) with the claim's own keys (common random numbers). v1
    dropped the crossed (zscore, False) cell without saying so.
  - "Donor-robust" is decided by T's sign alone (≥ 5 of 6). Multiverse outcomes are descriptors; they never change the
    primary verdict.
  - The bilateral cell is "not applicable (map defined on the left hemisphere only)" for left-only maps: bilateral-average
    maps placed on the left, Pretzsch, Leyhausen.
  - **Matrices** (built before any claim runs; build hashes recorded, in `env/venv_ref`): the three non-primary
    normalisation cells and the bilateral cell (lr_mirror 'bidirectional') for V-AAL and V-DK; the ≥ 2-donor counts for
    V-AAL, V-DK and MIST64 (dk-ctx and V-DK-subcortex are subsets of V-DK). The leave-one-out matrices already exist
    (verified as A3 did, `arcs/replication/src/ahba_loo.py`).
- **Why now:** survivors are unknown, so the rule cannot be bent toward them. Cost and the pause point: §14.

**R12. HAN-C1-ourPC1, "our §3.1 gene PC1 (DS > .1)" [default 12].**
- **Text:** "our §3.1 PC1 (DS > .1) a descriptor" (`claims_register.md:1782-1783`; TSV row 625).
- **Reading:**
  - DS is the differential stability of `abagen.correct.keep_stable_genes(expression=<per-donor list>, threshold=0.1,
    percentile=False, rank=True, return_stability=True)` (`env/venv_ref/.../abagen/correct.py:556-615`): the mean over
    donor pairs of the Spearman correlation of a gene's regional profile, over the regions both donors cover. This is the
    differential-stability measure of Hawrylycz et al. 2015 as abagen implements it.
  - It is computed on per-donor V-DK matrices (§3.1 settings, `return_donors=True`, built in `env/venv_ref`; build hashes
    recorded), restricted to the 34 left DK cortical parcels.
  - PC1 is `sklearn` PCA (columns centred, not scaled) of the dk-ctx §3.1 matrix over the genes with DS > .1. Its sign
    follows amendment 3's convention: "corr(PC score, mean expression over genes) > 0" (`prereg_amend_3.md:146`).
  - It is a descriptor at component level, two-sided.
  - The register names "our §3.1 PC1 (DS > .1)" but fixes neither the PCA's centring nor the parcels DS is computed over.
    The choices above are conventions. They were fixed before this audit, or any author or reviser of this plan, saw any
    G2 material or Hansen's code. They act on AHBA matrices only, not on Hansen's map. They were written after the
    lane's 14:30 descriptives of the ENIGMA-ASD map (§9), which they do not use. The output labels them "convention
    (pre-exposure)", where the exposure meant is this audit's; the lane's earlier exposure is declared beside the label
    (§9).

**R13. Patel's mean bicor [default 13].**
- **Text:**
  - "the mean bicor for Patel" (`claims_register.md:318`); "§4.1 check against the mean bicor on our matrix
    (−.201 / −.226 / −.212)" (`:1451-1452`);
  - a "not reproduced" full-verdict claim leaves the population (`:234-235`).
- **Reading:**
  - The functional is the mean over the panel's genes of the biweight midcorrelation between y (34 left DK values) and
    the gene's expression.
  - bicor follows the WGCNA defaults: `bicor(x, y, robustX = TRUE, robustY = TRUE, maxPOutliers = 1,
    pearsonFallback = "individual")`, with u = (x − med x)/(9·MAD x) and MAD the raw median absolute deviation.
    Weights are (1 − u²)² for |u| < 1. A column with MAD 0 falls back to Pearson.
  - It is implemented and unit-tested **before this audit reads any G2 map** (P17):
    - on closed-form small cases and invariances;
    - on the fallback;
    - against `WGCNA::bicor` on 1,000 synthetic vector pairs (agreement to 1e-10) if the Docker R environment of R17
      builds. If it does not build, this is declared and the closed-form tests stand.

**R14. Pretzsch's per-donor recipe [default 14].**
- **Text:**
  - "the decoded lists re-derived by amendment 4 §2's per-donor parcel recipe (the paper used abagen + a per-gene LME …),
    pFDR < .01, split by sign" (TSV rows 523–526);
  - the recipe is "the one-sample t of the six per-donor slopes, on per-donor parcel matrices under §3.1 settings"
    (`prereg_amend_4.md:91-93`);
  - "the paper's decoded list re-derived by its own rule" (`claims_register.md:329`);
  - "Re-running a claim in a parcellation other than the paper's is labelled 're-parcellated' and never counted as a
    reproduction" (`prereg.md:213-214`).
- **Reading:**
  - The recipe runs on the **paper's own parcellation**: 180 left Glasser parcels, through the pinned HCP-MMP1 MNI volume
    (R15), using per-donor abagen matrices built in `env/venv_ref` (§3.1 settings, `return_donors=True`).
  - y is the eTable13 loadings as published, not re-parcellated.
  - Per gene and donor, the OLS slope of expression on y is taken over that donor's parcels with samples; a donor with
    fewer than 3 such parcels is dropped and reported.
  - A one-sample t (df = number of donors − 1) is taken over donors, then BH across genes.
  - The general rule, used for every descriptive reproduction:
    - where the paper decoded on parcels, the recipe uses the paper's parcellation;
    - where it decoded voxel- or sample-wise (NeuroVault decoder fallbacks: Segura, Leyhausen, Pagani, Park), the
      recipe uses the claim's analysis class, labelled "re-derived (per-donor parcel recipe, <class>), not the decoder".
  - If the atlas check fails: "not computable (atlas identity)". This is a descriptive reproduction only, so it moves no
    count.
  - Benkarim, whose parcellation is unnamed: R31.

**R15. HCP-MMP1 → dk-ctx [default 15/16].**
- **Text:** "Glasser-360 through `HCP-MMP1_on_MNI152_ICBM2009a_nlin.nii.gz` (Horn 2016, figshare 3501911) … each source
  parcel is assigned to the DK label holding the majority of its voxels …; left hemisphere only"
  (`claims_register.md:1036-1041`).
- **Reading:**
  - The volume and its label list are both taken from figshare 3501911; URL, bytes and sha256 are recorded.
  - The left-label indices are read from the label list, not assumed.
  - Assert a one-to-one match of the list's 180 left names to eTable13's 180 `L_*_ROI` names. The names are read from the
    derived CSV's label column under G2, and are not values. They are compared in memory and reported as match counts
    only (§8's print rule).
  - Any failure: Pretzsch's cells read "not auditable (definition not applicable: the pinned HCP-MMP1 atlas could not be
    matched to eTable13)".

**R16. fsaverage annot [default 15/16].**
- **Text:** "FreeSurfer's fsaverage `lh.aparc.annot` (the FreeSurfer 7.4.1 distribution file, sha256 recorded at
  download) … labels `unknown` and `corpuscallosum` excluded; DK labels matched to the abagen DK names"
  (`claims_register.md:1033-1035`).
- **Reading:**
  - **Pinned tarball:** `freesurfer-linux-ubuntu22_amd64-7.4.1.tar.gz` from
    `https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.4.1/`. Probed 2026-10-01 at 13:30 UTC (directory listing and
    HEAD only; no gated material): HTTP 200, 9,484,461,482 bytes, Last-Modified 2023-06-27, `Accept-Ranges: bytes`, so an
    interrupted download resumes by byte range. The directory also lists the centos7, centos8, ubuntu18 and ubuntu20
    tarballs and the macOS artefacts; HEAD probes of the centos7 and macOS tarballs returned no response at that time.
  - The file is the one member whose path ends in `subjects/fsaverage/label/lh.aparc.annot`. The gzip stream is read in
    order until that member is found (up to the whole 9.5 GB), only the member is written, and the stream then stops.
    Member paths are matched in memory against that declared suffix and never printed or written (§8's print rule).
    - **Recorded:** the URL; the Content-Length and Last-Modified headers; the bytes streamed; "declared member: found";
      the sha256 of the member's path string, its size and its content sha256; and "tarball sha256 not computed
      (stream stopped at the member)".
    - **A link member is resolved by a second streaming pass; any other non-regular member is refused** (v3.1 review
      N-C2, replacing v3.1's outright refusal). A hard-link or symbolic-link member (`TarInfo.islnk()` / `issym()`) names
      its target (`linkname`, normalised inside the archive); a second pass streams the tarball again and takes that
      target as a regular member, recorded the same way. Only an unresolvable link (target absent, outside the
      archive, or itself not regular) or another non-regular member is refused and never resolved; its member
      type (hard link, symbolic link or other) and the sha256 of its path string
      are recorded, nothing is written, and the Leyhausen cells read "not auditable (definition not applicable: the
      FreeSurfer 7.4.1 distribution annot is not a regular member of the stream)". The stream runs as the first step of
      WP4, so this is known before any other G2 work.
    - The register asks for the sha256 of the distribution file `lh.aparc.annot` ("sha256 recorded at download",
      `claims_register.md:1033-1035`), and the member's sha256 is that hash.
    - Because the stream stops, a second member with the same path ending later in the tarball would go unseen. The
      member asserted is the first, and the record says so. v2's "the tarball's sha256" could not be had without
      reading the whole stream, and it is withdrawn (re-check, C5).
  - If the pinned tarball cannot be obtained, any other official 7.4.1 artefact from the same directory is accepted, and
    its member's sha256 recorded. If two artefacts are read and their members differ, that is recorded and the ubuntu22
    member governs. The register names "the FreeSurfer 7.4.1 distribution file" (`:1033-1034`), which every official
    7.4.1 artefact carries; only a non-official copy is refused.
  - Assert:
    - the GIFTI vertex count equals the annot's vertex count (both read from the files; no number is assumed);
    - exactly 34 annot names match the abagen DK cortical names after the two exclusions.
  - Any failure, including no official artefact being obtainable: the Leyhausen cells read "not auditable (definition
    not applicable: the FreeSurfer 7.4.1 distribution annot not obtainable / not matching)". This would move Leyhausen's
    27 claims in m, so the download is the first step of WP4.

**R17. R for Giacomel's rebuilt DEG maps [default 17].**
- **Text:** "C19–C24 rebuilt with the paper's code `literature_gwas_analysis.R` on the authors' AHBA matrix, labelled
  'rebuilt from the paper's code'" (`claims_register.md:1470-1472`).
- **Environment:**
  - Rscript is absent and there is no R install.
  - Docker is listed in `D:\RESEARCH\CAPABILITIES.md:6`, but that probe dates from 2026-07-24, more than a month ago, so it
    was re-probed: 28.1.1 client and server on 2026-10-01.
- **Reading:**
  - The script runs in a Docker R image pinned by digest. Use `rocker/r-ver`, whose CRAN is date-locked; `r-base` only if
    rocker is unavailable.
  - The R version is the one the repository declares; if it declares none, the R release current at the commit date.
  - CRAN packages come from the Posit Package Manager snapshot of the commit date; Bioconductor from the release matching
    that R.
  - It runs at the repository commit. Inputs and outputs are hashed; the image digest and the session info are recorded.
  - This is a declared environment addition.
  - The script is read under G2 only for its package list and inputs.
- **Fallback:** if the script cannot run, those descriptor and published-null cells (C19–C24, the 12 MDD-DEG cells) read
  "not auditable (definition not applicable: the paper's code not runnable here)". None of them is in m (TSV
  `verdict_counted_in_m` = no).

**R18. Post-freeze manifests [default 18, corrected to the register's folders].**
- **Text:**
  - "Every object is hashed into `register_maps/` and `register_sets/` manifests and committed" (`:1098-1099`);
  - "After the freeze none of these files is edited" (`:53-55`), where "these files" are the register, the TSV, the
    S-build manifest and the freeze manifest; the freeze manifest describes itself as holding "every
    register_maps/*.json".
- **Reading:** the register names the folders, and adding new files to them edits none of the frozen files, so the text
  leaves no choice (first review, B6; v1 moved the records elsewhere on a tension that does not exist). Records go to
  subfolders that no frozen glob reaches:
  - `register_maps/post_freeze/<gate>/` for maps, carriers and extractions;
  - `register_sets/post_freeze/<gate>/` for gated sets;
  - `<gate>` ∈ {ungated, G2, G1}.

  The freeze-manifest builder globs `register_maps/*.json` non-recursively (`claims_register_tsv_build.py:3298, :4211`),
  so a subfolder never enters it, and the manifest's self-description stays true. One record per object:
  - URL, bytes, sha256, git blob (LF) and served MD5;
  - the R13 at-download comparison against `IDENTITY_prefreeze.json`;
  - the result ("identity match" or "not auditable (map changed)"), declared-sheet match counts and dimensions, the
    sha256 of every sheet, member or file name read from the carrier (never the name itself, §8), and extraction hashes.

  The frozen manifests are never touched. Run-control records (launch assertions, gate records, plant outputs) are not
  object manifests; they go to `arcs/audit/run_manifests/` (`launch/`, `G1/`, `plants/`).

**R19. Order of steps [default 19].**
- **Text:** "(1) After the freeze, ungated targets. (2) Under each gate: downloads … (3) The audit runner, with planted
  cases per T form …, reviewed by asdg-skeptic before any claim runs. (4) The run in gate order." (`:1094-1101`).
- **Reading:**
  - Steps (1) and (2) concern material. Step (3) is a precondition of any claim.
  - The order is:
    - (a) runner, adapters and plants for **every** gate, G1's included, then the asdg-skeptic review;
    - (b) ungated material and rows;
    - (c) G2 material and rows;
    - (d) G1 material and rows.
  - "Gate order" means the order of opening.
  - Within a gate, the verdict legs run as a first pass and the descriptor legs as a second.
- **Why:** G1's plants and readings are fixed before any G2 outcome exists, so G2 cannot shape them.

**R20. Dear and Vairam / Roy stay deferred [default 20]** (§6 A1, A2; §13).

**R21. MOR-T1/T2, "computed as a descriptor" [default 21].**
- **Text:**
  - "its T is computed as a descriptor where a registered T form exists" (`claims_register.md:297-299`);
  - TSV rows 618–619: "computed as a descriptor: the decoded-list-type mean per-gene Pearson r of S";
  - descriptor cells are "computed with the same machinery, reported in full" (`:195-196`);
  - "Every claim is reported at every level" (`prereg.md:17-18`);
  - T_abs applies to "every decoded-list claim and every 'not testable as stated' pooled list" (`:309`). MOR-T1/T2 are
    tail-rank cells, not pooled lists.
- **Reading:**
  - The decoded-list T, with all its legs (Level 0, site, species, descriptor legs) on native MIST64 (46 primary parcels;
    subcortex 5 and cerebellum 8 are permuted within class, `prereg.md:128-129`).
  - No T_abs.
  - Reported as values and p's labelled "descriptor (not testable as stated: tail-rank statistic); calibration extrapolated
    (class)"; never a survival. They are non-ASD outcomes, reported apart (`:222-223`).

**R22. Segura's reproduction [default 22].**
- **Text:**
  - "Reproduction descriptive (NeuroVault decoder, `mask=full`, FDR q < .05, both signs; OR vs 1.6)"
    (`claims_register.md:1437-1438`);
  - the paper's GO over-representation analysis "PANTHER / AmiGO 2, whole Homo sapiens reference, FDR" (TSV rows 3–9);
  - S uses "GO release 2024-01-17 (the release the paper names)" (TSV row 3).
- **Reading:**
  - The decoder output for 790618 and 781986 is fetched with `mask=full`; it is ungated.
  - The over-representation analysis is run locally:
    - Fisher's exact test and BH FDR across the terms tested;
    - **sidedness, not verified at writing:** PANTHER's help page returned HTTP 403 on 2026-10-01 and no primary PANTHER
      text was found. Both the one-sided (over-representation) and the two-sided Fisher p are computed. The primary is
      the sidedness PANTHER's own documentation states, read and recorded before WP3. If no PANTHER document states it,
      the two-sided p is primary (the larger p) and the output is labelled "PANTHER sidedness unverified";
    - on the GO release 2024-01-17 files already on E: (`goa_human.gaf.gz` 3ccc83fe…, `go-basic.obo` e078d540…), with
      §1.6's GO rule;
    - the primary reference is every human gene symbol in that GAF, mapped by the S-build's HGNC rule (the release the
      paper names). Beside it, PANTHER 16.0's own `PTHR16.0_human` (on E:, sha256 d605cf60…, 19,670 genes;
      `claims_register.md:1243`) is run as a sensitivity, labelled "PANTHER 16.0 reference (an older release)". Both are
      reported beside the paper's reference of 20,787 (TSV row 3 `inference_level`).
  - If the decoder is unavailable, the fallback is the per-donor recipe on V-AAL (R14's rule).
  - Descriptive reproduction only; no count moves.

**R23. Buch's count in m [default 23].**
- **Text:** "80 in m" (`claims_register.md:1589`); the §4 block's `m.target.buch2023asdsubgroups = 84` (`:1859`); "the
  block governs" (`:52`).
- **Reading:** 84, which is 80 PLS-enrichment claims plus the 4 component claims BUCH-C1…C4 (TSV count).

**R24. Level 2's G1 and G3; one G3 seed rule for every use (found while drafting; made consistent in v2).**
- **Text:**
  - amendment 3 lists "Level 2 (G1–G5)" among the descriptors reported for every claim, beside "each species leg's own p"
    (`prereg_amend_3.md:100-101`);
  - Level 2 = max over G1–G5, with G1 uniform from the universe and G3 uniform from GAMBA ∩ universe (`prereg.md:136-154`);
  - Liu: "G1–G5 descriptors on the paper's per-sample statistic" (`claims_register.md:1666-1667`);
  - Giacomel's signed-weight cells: "G1–G5 and J1 with S's weights carried over" (`claims_register.md:1472`), which also
    answer prereg §8's registered MDD question (`:1476-1478`);
  - the register's descriptor legs are only "G2, G4, G5 … J1 … the naive joint null … T_abs" (`:1072-1073`), and §1.9
    gives G3 no seed leg (`:1080-1082`).
- **The inconsistency v1 had (first review, B4):** v1 ran Liu's G3 but declared Level-2 G3 not auditable for want of a
  seed leg, and left Giacomel's weighted G3 unaddressed. v2 applies one rule to all three uses.
- **Reading:**
  - **Level-2 G1:** the leg-2 G1 sets (the same distribution, uniform from U \ S) scored unconditioned. No new seed is
    needed, and on single-class maps the result is identical to the species G1 (asserted).
  - **G3, every use.** G3 is fully defined ("uniform from GAMBA-2,711 ∩ universe", `prereg.md:143`) and three frozen texts
    require it; what is missing is a key in the seed list, not a definition. G3 sets are drawn from
    `SeedSequence(entropy=[20260925, 100 + target number, row number, 3, map index, cell index], spawn_key=(0,))`: the
    first child of the G3m leg's key (leg 3). It is an independent stream and leaves leg 3's own stream untouched. The
    rule serves Level-2 G3 and the Level-2 max for every full-verdict claim, Liu's G3 (R10), and the G3 leg of Giacomel's
    signed-weight cells (GIA-C01 … C06, GIA-C19 … C24, GIA-MDD-C1 / C5 / C10; TSV rows 103–117) and of any other cell
    whose registered legs include G3.
  - This is a seed reading fixed before this audit opens any material; it changes no statistic's definition, and no
    value of any map enters it (the lane's earlier exposure of the ENIGMA-ASD maps behind Giacomel is declared in §9). If the orchestrator
    prefers the amendment route (§6 A3), every G3 use reads "not auditable (definition not applicable: no registered seed
    leg for G3)" together, never one use computed and another not.
- **Plant:** P2 (the G3 stream is reproducible and differs from leg 3's).

**R25. Prereg §4.5 Level 4 (found while drafting).**
- **Text:**
  - "For ENIGMA structural ASD maps: S's J1 z (or Level-2 z if J1 is not adopted) on the ASD map is ranked among the same
    z on the sibling disorders' maps in the same ENIGMA Toolbox release" (`prereg.md:165-167`);
  - J1 was not adopted (`results/e3_gates.md:3`: "J1: **fail** (adopted: False)");
  - the register never enumerates Level 4 (no match in register or TSV).
- **Reading:** the descriptor applies to Patel, Giacomel and Liu T3. It does not apply to Hansen: HAN-C1 is a component
  claim with no S, and the descriptor ranks "S's … z". "Level-2 z" is defined nowhere; see §6 A4. Until then it reads
  "not auditable (definition not applicable: prereg §4.5's 'Level-2 z' is undefined and J1 is not adopted)".
- **Exposure condition (settled in v3 from the record, §9).** The lane's protocol judge read 11 comparator-disorder
  tables and the 22q11 table, which are among the sibling maps Level 4 ranks against, and printed per-file
  descriptives. At 14:30:13 it printed, for the 15 tables it read, the count of non-null `se_icv`, the median `se_icv`,
  the SD of `d_icv` and the left-right r. At 14:30:43 it printed, for 13 of them, var(`d_icv`), the mean sampling
  variance and a per-hemisphere reliability ratio. Before that, the lane's novelty judge printed the committed manifest
  table's effect min / max for 18 CortThick files (both ASD tables among them), and the protocol judge printed manifest
  rows (§9). That is no set × map statistic and no claim statistic. It is still a look at the spread of the sibling
  maps, and that spread is what a rank of z's among them depends on. So the conservative branch is taken: any A4 is
  declared post-exposure, with that listing; until then Level 4 stays not auditable. **Exposure-bearing files:** the
  lane run's workflow record `wf_a992ecba-de5.json` and that run's agent transcripts (both paths in §9). The record's
  stored result carries the judge's per-hemisphere reliability table and median `se_icv` values; the transcripts store
  the commands' output. No author or reviewer of A4, and no audit or plan agent, reads them (§9).

**R26. Where the claim factorial is written (found while drafting).**
- **Text:** "`arcs/audit/results/MANIFEST.md` lists every planned (claim × level × null × parcellation × multiverse cell)"
  (`prereg.md:289-291`). That file's own header reads "GENERATED by `arcs/audit/src/e3_gates.py`; do not hand-edit".
- **Reading:**
  - The runner generates `arcs/audit/results/MANIFEST_claims.md` for the claim factorial.
  - The e3 file stays untouched. The pair is the prereg §7 manifest; each names the other.
  - **Declared deviation (file name only):** prereg §7 names `results/MANIFEST.md` for the claim factorial too. Writing
    the claims into that generated file would hand-edit it, so they go to a second file. The content is prereg §7's; only
    the file name deviates, and the A1 ARC records the deviation.

**R27. Ungated reproduction functionals, labels and readings.**
- **Amendment 5 §3–§4 labels** come from a port of A3's `reading()` / `descriptors()` (`h_verdicts.py:1163, :1273`), with
  A3's gate logic removed:
  - the power columns, "power not measured in this class" for dk-ctx and single-class claims, and "power not measured at
    this set size" for m < 25 or m > 100 (`prereg_amend_5.md:130-136`);
  - R²_grad, R²_|x|, f/m, the hypergeometric p and c_S;
  - "calibrated evidence" versus "calibration extrapolated (set size / class / gradient)" (`:138-147`);
  - for re-parcellated claims in any class, "species leg untested (gradient)" when R²_grad ≥ .25 and "brain-enrichment (N1)
    confound untested" when the set is brain-enriched (`:230-232`);
  - single-class claims outside dk-ctx read "calibration extrapolated (class)" (`:236-239`).
- **Reproduction functionals** follow §1.5 (`claims_register.md:316-332`): Pearson; Spearman; the paper's R²; mean bicor
  (R13); |z|-weighted GEDAR ρ (Giacomel); rank-biserial (Liu T3/T4/T5); the authors' centred unscaled PLS on all 64 parcels
  (Moreau); R²_adj and dominance with the shipped predictors (Hansen). The check is |ours − published| ≤ .05, with sign
  opposite → "not reproduced (sign)".

**R28. BENK-C2-SD / -DD and PARK-C5 descriptors (first review, B7 (a)).**
- **Text:**
  - "descriptors: the paper's RLM on our decoding (reproduction) and a Gandal 2018 ASD-down set proxy (labelled)"
    (`claims_register.md:1732-1733`); PARK-C5 "descriptors as BENK-C2" (`:1762`);
  - TSV rows 518, 519, 603: "the Gandal 2018 ASD-down set proxy with the decoded-list T (labelled)", set
    `gandal2018_asd_down`, direction − (BENK) and + (PARK);
  - Benkarim's code: `sm.RLM(y = gene t, x = [log2FC, percentage_gene_gc_content, const])`, reported `tvalues[0]`
    (`register_work/benkarim2021connectivity.md:79-80`); Park: "A robust linear regression model … (GC) content was
    controlled" (`register_work/park2021subcortico.md:85-87`).
- **Reading:**
  - **Decoding (one t per AHBA column).** BENK: amendment 4 §2's per-donor parcel recipe on dk-ctx (R31). PARK: the
    NeuroVault decoder output for image 396720, fetched under G1 (register §1.5), else the same per-donor recipe on
    dk-ctx, labelled.
  - **RLM:** statsmodels `RLM(endog = per-gene t, exog = [log2FC, GC %, const])` with its defaults (`HuberT()`, scale by
    MAD), the norm the authors' code uses by setting none. The reported value is the t of the log2FC coefficient,
    compared with t = 42.270 / 28.099 (BENK) and T = −34.89 (PARK). The SCZ and BD rows are run the same way.
  - **Inputs:** log2FC and GC % come from Gandal 2018 Table S1, sheet DGE. That is the S-build's source
    (`register_sets/gandal2018_asd_down.json`: URL
    `https://pmc.ncbi.nlm.nih.gov/articles/instance/6443102/bin/NIHMS1007359-supplement-Table_S1.xlsx`, sha256
    e6f9c6ebab41974972f55af09708d565e3fb658e4dc1a6e6e194bed54726ce72; 61,253,282 bytes, `claims_register.md:788`).
  - **This re-fetch reverses a recorded deletion (declared; re-check, C3).** The register lists this workbook as an
    original deleted under §1.6, because its DTE and DTU sheets are identifier-bearing (V) (`claims_register.md:783`,
    `:788`). It also records that "`fetch_v66.py` never re-fetches a deleted original" (`:2293`). The reason for the
    re-fetch: the v6.8 reduction kept exactly the columns the S-build read (`ensembl_gene_id`, `gene_name`,
    `ASD.log2FC`, `ASD.fdr`; "reduced to exactly the sheets and columns read", `:2293`). The RLM's covariates were
    therefore never kept, and no other source holds them. The register's own rule for such a workbook is that it "is
    kept whole only if it holds no identifier-bearing sheet" (`:820-821`). So the re-fetched copy is held only between
    download and verified extraction, then quarantined, and its deletion is requested in the same session (§8 step 6).
  - **Procedure:**
    - fetched in WP5 by the §8 wrapper, after `require_g1_open()` (BENK-C2 and PARK-C5 are G1 rows);
    - at download, the bytes and sha256 must equal the register's (61,253,282 B; e6f9c6eb…ce72). On a mismatch the read
      is refused, the file is quarantined unread with its deletion requested, and the RLM reads "not computable (carrier
      changed: sha256 differs from the register's)";
    - only the DGE sheet is declared (clean by the guard's rule, `:788`), with the exact headers `ensembl_gene_id`,
      `ASD.log2FC`, `SCZ.log2FC`, `BD.log2FC` and `percentage_gene_gc_content`. No other sheet is touched, and DTE and
      DTU are on the do-not-open list (§8 step 3);
    - a header that is not found means the read is refused, and the RLM reads "not computable (covariate not in the
      carrier)";
    - the declared columns are saved as a gene-level reduction with its sha256 (§8 step 5). The workbook is then
      quarantined and its deletion requested in the same session (§8 step 6).
  - Genes are matched by Ensembl id, then by the S-build's HGNC rule. Rows without a finite value in a model column are
    dropped and counted.
  - **Proxy:** S = `gandal2018_asd_down` with the decoded-list T and all its legs (Level 0, site, species and descriptor
    legs; no T_abs, as R21), direction as the TSV. It is labelled "descriptor (not testable as stated: genome-wide robust
    regression); proxy set (Gandal 2018 ASD-down)", carries R27's calibration labels, and is never a survival.
- **Plants:** P17 (the RLM on synthetic data equals a direct iteratively reweighted Huber fit); the proxy runs through
  P5's decoded-list path.

**R29. The BH family for the descriptive q-values (first review, B7 (b)).**
- **Text:** "Benjamini–Hochberg q < 0.05 across all testable reproduced claims on the conjunction p" (`prereg.md:171-172`);
  "Benjamini–Hochberg q-values (on the conjunction p) are reported as descriptive" (`prereg_amend_3.md:77`); m is "kept
  for the descriptive BH" (`claims_register.md:1083`).
- **Reading:**
  - The family is the claims in m (TSV `verdict_counted_in_m` = yes; 207 rows) that receive a conjunction p and are not
    flagged "not reproduced". "Reproduction descriptive" claims stay in. Component claims in m enter with their
    component-level p (the max of Level 0 and the site leg).
  - The conjunction p is R1's for two-sided claims.
  - A claim whose status is not ok (unmatched, degenerate, uninformative, resolution-limited) enters with p = 1: it takes
    a slot and cannot draw a small q, since it cannot survive (amendment 3 §2).
  - Claims of m without a conjunction p (not auditable, deferred, not testable) are outside the family, listed, and the
    family's size is reported.
  - The final q's are computed once, after every gate has run. Per-gate interim q's are reported beside them, labelled
    interim. A q is never worded as a detection.

**R30. Pretzsch's overlap test (first review, B7 (c)).**
- **Text:** TSV rows 523–526: "the decoded lists re-derived by amendment 4 §2's per-donor parcel recipe …, pFDR < .01,
  split by sign; then GeneOverlap"; the draft: "Enrichment: GeneOverlap (hypergeometric/Fisher; background not stated)"
  (`register_work/pretzsch2024patterns.md:63-64`).
- **Reading:** the overlap test is Fisher's exact test of the re-derived list against the set, in the direction
  GeneOverlap's `testGeneOverlap` runs it (read from the package source in the R image of R17 and recorded with its
  version). The primary universe is the genes the per-donor recipe tested (HGNC genes with a finite t, R14), from which
  the decoded list is drawn. Beside it, the p at GeneOverlap's own default genome size (read from the same source),
  labelled "GeneOverlap default background". OR, p and k are reported against the paper's (PRE-D1: k 38, OR 3.7).
  Descriptive only.

**R31. Benkarim's per-donor recipe parcellation (first review, B7 (d)).**
- **Text:** R14's rule (the paper's parcellation where the paper decoded on parcels); the Benkarim draft: the code uses
  "surface parcels whose atlas is not named in text or code" (`register_work/benkarim2021connectivity.md:37-38`), and the
  list was made by "per-donor regression of each gene on the map, one-sample t across the six donor slopes" (`:40-41`).
- **Reading:** the paper decoded on parcels, but its parcellation is unnamed, so R14's first branch cannot be applied.
  The recipe runs on the claim's analysis class, dk-ctx (the NeuroVault volumes re-parcellated by §1.7's volume rule),
  labelled "re-derived (per-donor parcel recipe, dk-ctx; the paper's parcellation unnamed)". Everything else follows R14.

## 6. Needs a frozen amendment (not this plan)
| id | item | frozen text | until an amendment, the cells read |
|---|---|---|---|
| A1 | Dear's provenance | "The deferral is lifted only by provenance, recorded in the register" (`prereg_amend_4.md:40-43`); the register is frozen (`:53-55`) | "deferred pending provenance" (3 rows; 2 in m, listed apart) |
| A2 | Vairam / Roy status | "Changing its status needs an amendment" (`claims_register.md:1653`) | "deferred" (6 rows) |
| A3 | **withdrawn in v2** (was: a seed leg for Level-2 G3) | R24 pins one G3 seed rule for every use | if the orchestrator prefers the amendment route instead: every G3 use (Level 2, Liu, Giacomel's weighted cells) and the Level-2 max read "not auditable (definition not applicable: no registered seed leg for G3)" together |
| A4 | a definition of prereg §4.5's "Level-2 z" (J1 not adopted) | `prereg.md:165-167`; `e3_gates.md:3` (R25) | Level 4 for the ENIGMA-ASD maps: "not auditable (definition not applicable: 'Level-2 z' undefined; J1 not adopted)". Any A4 is declared post-exposure: the lane printed per-file descriptives of the sibling tables and the manifest table's effect min / max (R25, §9). The lane run's workflow record `wf_a992ecba-de5.json` and its agent transcripts hold some of those values; no author or reviewer of A4 reads them, and the A4 listing repeats this |
| A5 | **withdrawn in v2** (was: a coexpression matrix for gene-set-only claims) | R10 takes the coexpression basis from the statistic's own expression data, as it takes the universe | — |
| A6 | **not optional:** a rule for verdict legs whose pool is smaller than S | `claims_register.md:1102-1103` (R8) | "not auditable (definition not applicable: null pool smaller than S)"; the cells are MAMAT-E-Tissue-URG / -DRG (in m) and BUCH-E-SZ-S1 … S4 (descriptor cells) |

- A1 and A2 are listed apart and move no count.
- A3 and A5 are settled by readings in v2 (R24, R10).
- **A6 decides the status of two frozen-11 headline claims.** Under R8, MAMAT-E-Tissue-URG and -DRG (frozen-11 row 7, in
  the headline population once G1 opens) count as "not auditable" rather than as tested claims, which also changes the
  tested-only fraction's denominator. v1's statement that none of A1–A6 changes the primary population was wrong for A6.
  Before any G1 material is opened (§18, F4), the orchestrator either commissions A6 and freezes it, or records under the
  standing delegation that "not auditable (definition not applicable: null pool smaller than S)" is accepted as a change
  to the population's composition.
- A4 touches a descriptor only.

## 7. Planted cases (register §1.10 (3): "a planted set on a synthetic map survives; a random set does not; a pooled-sign plant defeats the signed T")
- **Data:** synthetic maps only, built on each class's centroids (`spatial.FieldGenerator`, `prereg.md:224-228`) and on
  its §3.1 matrix. No audit map is used.
- **Code path:** every plant runs through the production code path (`a1_audit.run`, flag `--plant`).
- **Cost model:**
  - functional plants with real-size inputs run at audit K (10,000; exact G6l) where they say so, else at plant K;
  - plant K = 500 surrogates per site null and K = 200 species draws, with G6l in amendment 3's plant mode (K = 200
    accepted, budget 1,000 seeds; `prereg_amend_3.md:130-131`): the frozen battery's scale.
- **Two kinds of plant.**
  - **Functional** (P0–P2, P3a, P5, P7, P9–P11, P13–P23, and the value checks inside every other plant): exact
    assertions. A failure is a code defect.
  - **Statistical** (P3b, P4, P6, P12, P24–P26): each has n and a threshold fixed now from a rate already measured on
    the frozen code (`results/e3_gates_a3.md`; amendment 5 §3) or from a gate cap. Each is set so that a runner behaving
    as measured fails with probability ≤ .01. The tails were computed 2026-10-01 with scipy 1.18.1, and each row states
    its basis. Where the basis is a measured count, not a cap, the tail is the predictive one: beta-binomial, from a
    uniform prior updated by the frozen count, so the frozen rate's own sampling error is included (re-check, C6).
    - For P3b this moves the thresholds.
    - For P4 the predictive tail at the worst frozen strata (2 / 500, e.g. `e3_gates_a3.md:763`) is 5.4e-7, so its
      threshold stands.
    - P6, P12, P24 and P26 rest on caps.
    v1's P3 ("≥ 4 of 5 survive") had no basis: a correct runner would have failed it about half the time (both reviews).
    Rates reported without a threshold (P5's and P7's catch rates, P8's survival counts, P12's two-gene map) never
    trigger a code change.
  - **Two consequences of a statistical failure, fixed now before any run (re-check, C7):**
    - **Correct-leg tests** bound a correct leg's behaviour: P3b, P4, P6, P12, P24, P26's site-leg test, and P25 (c)'s
      correct-leg test. A failure with no defect named blocks the claims of that form × class (§17).
    - **Must-catch tests** check that the plant regime can see a planted flaw: P25 (a)–(c)'s flawed legs and P26's
      planted permutation leg. Their bases are rates measured on the set-vs-map adapter (P25 (a): .086 / .133) or on
      naive Level 0 (P26: ≥ .15), carried over to adapters where they were never measured. A failure to catch with no
      defect named is reported as **"plant regime insensitive for this form × class"** and does not block claims: the
      correct leg's rate is still bounded by P24 / P26's correct-leg tests, so no false survival can follow from it.
  - A statistical failure is not presumed to be a code defect: it gets a written diagnosis and the skeptic's review, and
    code is changed only for a defect the diagnosis names (§17).
  - None of them is a new calibration gate of the verdict; calibration stays amendment 3 / 5's. P24–P26 test that the
    new adapters' legs behave as the frozen set-vs-map legs were measured to behave.
- **Seeds:** `SeedSequence([20260925, 900, plant_id, case, class_id])`, kept apart from every claim key (target 900 does
  not exist).

| id | what | form × class | expected / pass |
|---|---|---|---|
| P0 | (a) ported A3 helpers vs A3 functions; shared vs unshared G6l screens. (b) set-vs-map statistic (§4) | toy | (a) bit-identical. (b) set-vs-map T = r(y, X[:, S].mean(1)) on the unstandardised matrix to 1e-12, on a toy matrix whose gene variances differ, where the z-scored score gives a different r (so the check can fail) |
| P1 | launch assertions | copies with one byte changed; dirty tree; K1 text changed; a freshly created worktree (LF checkout) | each corrupted case refused before any statistic; the fresh worktree passes L1–L15, and a check on the CRLF working-copy hash alone is shown to fail there |
| P2 | seeds | 2 reruns of 3 rows | bit-identical p's; keys and integer seeds recorded; R24's G3 stream reproducible and different from leg 3's |
| P3a | production path = frozen engine (functional) | C-gene plants (prereg §6.3 construction, m = 25, a = .9), 20 per class: V-AAL, V-DK, dk-ctx replica; set-vs-map | the production runner and the frozen engine functions (`src/asdg` spatial, species and verdict, called directly as A3's `h_verdicts` does), given identical generator states, return bit-identical leg p's, statuses and verdicts |
| P3b | catch rate (statistical; correct-leg test) | the same construction, n = 100 per class, plant K | V-AAL fails iff ≤ 52 / 100 survive and V-DK iff ≤ 44 / 100. Basis: the frozen verdict catch 197 / 296 (.666) and 175 / 299 (.585) (`prereg_amend_5.md:85, :127`). The threshold is the largest k whose predictive tail is ≤ .01: P(X ≤ k) under the beta-binomial(100, 198, 100) for V-AAL and (100, 176, 125) for V-DK is .0064 at 52 and .0075 at 44 (at 53 and 45: .0103 and .0119). Treating the rates as exact gives .0018 and .0024. v2's thresholds (≤ 54 / ≤ 46) had predictive tails of .016 / .018 and are withdrawn (re-check, C6). A runner whose catch is .15 lower fails with probability about .58 (.575 / .579). dk-ctx: reported only (no frozen rate). v1's construction (a = 1, no field, "≥ 4 of 5") is withdrawn |
| P4 | random sets on independent fields (n = 100 per cell) | every form × class used (set-vs-map dk-ctx / V-DK / V-AAL / V-DK-subcortex; decoded-list dk-ctx / V-DK / V-AAL / MIST64; PLS-enrichment V-AAL / dk-ctx) | verdict rejections ≤ 9 / 100; the frozen set-vs-map verdict false-alarm rate on the F families is ≤ .004 in V-AAL, V-DK and V-CC200 (`e3_gates_a3.md`), so for a runner at that rate P(fail) ≈ 1e-11, and at the .05 cap P(fail) = .028. Every leg's rate reported. **Scope:** this cannot test the species or site leg, because a correct site leg alone holds the verdict count ("The F-family gates cannot fail", `prereg_amend_3.md:192`); P24–P26 test those legs |
| P5 | decoded-list T and conditioning (R2, R3) | dk-ctx, V-DK, V-AAL | T = mean per-gene r (1e-12); species null = ⟨ŷ, s_B(S)+s_W(R)⟩/n (1e-12); conditioned = unconditioned on single class (1e-12); Pearson-r scoring gives a different p (adapter in use); P3's construction run for this form, catch rate reported (no frozen rate exists for it). The between-class plant moved to P25 (c), with a criterion |
| P6 | pooled-sign plant: S = S₊ ∪ S₋, y = z(ẽ_{S₊}) − z(ẽ_{S₋}) | decoded-list dk-ctx, V-DK, V-AAL; n = 20 per class | signed T survives in ≤ 3 of 20 (for a verdict at the .025 cap, P(≥ 4 of 20) = .0014); T_abs values = direct computation; T_abs Level 0 p reported (T_abs is uncalibrated by registration, `claims_register.md:311-313`) |
| P7 | PLS-enrichment refit | V-AAL, dk-ctx | T = mean normalised weight; surrogate T* = direct refit (1e-12); species p = decoded-list species p (1e-12), so P24–P25 cover the PLS species leg; its site leg is P26's; catch rate of P3's construction reported |
| P8 | two-sided (R1) | dk-ctx | (a) 20 planted negative-signal maps: wherever d* = −, the two-sided conjunction p = 2 × the one-sided "−" conjunction p (exact); survival counts of both reported. (b) A constructed case in which Level 0's minimising direction differs from the species leg's: d* = argmin_d max_leg p(d), reported legs = 2·p(d*), the literal per-leg 2·min beside them (exact). (c) A two-cohort case: one d* over both maps (exact) |
| P9 | resolution (R1, R9) | V-DK-subcortex (7 parcels, single class) | site leg exact (7! = 5,040 permutations), G6s exact (64); status "resolution-limited"; doubled floor 4/65 recorded; any uninformative flag beside |
| P10 | pool < m (R8) | V-AAL, dk-ctx | m > \|U \ S\| → G1, J1 and the naive joint "not computable (pool < m)", G2 "unmatched" (the frozen prereg §4.3 label), G6l "unmatched" (no eligible seed), G6s computed; f or m − f beyond the G3m pools → G3m "not computable", cell "not auditable (definition not applicable: null pool smaller than S)" with every computable leg reported; m > \|(B∩U) \ S\| → G4 "unmatched" and Level-2 G3 "not computable (pool < m)"; G5 pool < 2m → "not applicable"; no exception |
| P11 | T_abs | dk-ctx, V-DK, V-AAL | unconditioned legs 21–25; upper tail (lower for a stated depletion); values = direct computation |
| P12 | component forms | MIST64 (PLSRegression(2) cumulative R², refit on 10,000 permutations and on S1c/S2c, classes < 10 permuted); dk-ctx fixed component r (parametric Level 0); PLS1 R²; component k of PLSRegression(K, scale=True) | refit equals direct (1e-12). A map built from two genes' profiles: results reported, no threshold (component tests are weak by design: PLS1 also fits surrogates well). 20 independent fields: ≤ 4 pass at component level (for a site leg at the gate cap .05, P(≥ 5 of 20) = .0026) |
| P13 | selected-list re-selection (G1: RA-11…14; `prereg_amend_3.md:102-106`) | dk-ctx | list re-selected on every permutation and surrogate; empty list → T = 0 |
| P14 | two-cohort conjunction (Mamat; `claims_register.md:1639-1641`) | dk-ctx | survives iff both maps survive; p = the larger |
| P15 | signed-weight descriptor (Giacomel; `:1469-1473`) | dk-ctx | null sets receive S's weight vector in random order |
| P16 | gene-set-only (R10) | synthetic BrainSpan-like matrix and a synthetic per-sample matrix with NaN columns | per-sample rank-biserial; U_stat drops non-finite and constant columns and records the count; G1–G5 drawn on U_stat with coexpression over the same samples; G3 on R24's stream; G5 carries the register's label; sample ids never reach any output |
| P17 | reproduction functionals | synthetic | bicor (R13; closed form, invariances, fallback, WGCNA via Docker if built); \|z\|-weighted ρ; rank-biserial; per-donor recipe t (R14); Fisher + BH over-representation analysis, both sidednesses (R22); the RLM equals a direct iteratively reweighted Huber fit (R28); the overlap test against a hand-computed hypergeometric tail (R30) |
| P18 | re-parcellation (`:1028-1048`) | synthetic volumes / surfaces | known parcel means recovered; a parcel at < 50 % coverage dropped and reported; annot labels; Glasser → DK majority; sphere → AAL centroid rule |
| P19 | identity at download / use | synthetic files | one byte changed → "not auditable (map changed)"; CRLF copy vs LF blob compared after LF conversion (Hansen's case); size-only probe |
| P20 | privacy wrapper (§8) | synthetic workbooks (.xlsx and .xls), zips and a tar stream with W / N / V sheets; synthetic identifier-shaped strings generated at test time from digit runs of 9 (none is written into this plan) | **One criterion for every run of the wrapper** (v3.1; review of v3, B2; ungated carriers take the same code path, so there is no gated / ungated split). Everything the run emits (stdout, stderr, log files, every record it writes, and the names of the files it saves) is captured. (i) It holds none of the synthetic carriers' strings: no header or label cell, sheet name, zip or tar member name, extracted file name, or cell outside the declared ones, the planted identifier-shaped ones included (searched for each); the step-5 object holds the declared cells' values only, keyed by runner-side names. (ii) Every emitted line of stdout, stderr, logs and records parses as tokens from the print rule's allow-list only (§8): numbers, hex digests, runner-built paths, `file:line`, labels of the runner's fixed vocabulary, and in identity records the pinned URL, dates and the server's headers; no cell value is printed. Also: declared sheets classified and reported as match counts plus name sha256s; an undeclared sheet whose part raises if parsed is never touched, and the access log holds declared sheets only; a do-not-open sheet is refused even if declared by mistake; a non-numeric code in a declared numeric column yields "ValueError at <stage>, <file>:<line>" and nothing else; a guard refusal prints its class, stage and code line only (the guard's own message, which names the sheet, never appears); a 64 × 64 Moreau-like sheet is read through the header-row search of §8 step 4, including a mixed-case label row and a `roi` row of floats; a tar link member whose target is a regular member is resolved by a second pass and recorded like a regular member (with the link's type noted), while a link whose target is absent, outside the archive or not regular, a link chain, and any other non-regular member are refused (R16; v3.1 review N-C2); xlrd opens with `on_demand=True` and loads only declared sheets |
| P21 | G1 fail-closed check and gate launcher (§2.2) | scratch git repo; the real repository read-only | the 32 refusal cases of §2.2 (malformed, early, late, unattested, uncommitted, edited, superseded or self-attesting states, a missing session message, and supersession markers anywhere in a line) refused; with G1 closed, no network request and no carrier test; the three correct scratch records open; the real record (4fd7942, record file of e49a024) opens at the run commit |
| P22 | multiverse plumbing (R11) | dk-ctx, V-AAL | primary matrix through the multiverse path reproduces the primary result; keys common |
| P23 | J1 / naive joint (R4, R5) | dk-ctx | own draws on legs 14 / 15; T substitution equals direct; degenerate pool → status |
| P24 | species leg of the decoded-list adapter on expression-aligned maps (statistical; second review, A1) | V-AAL, V-DK, dk-ctx replica; amendment 3 §4's F-align targets T-wmod and T-brain at w = .9, built by its frozen generator (`e3_align_plants.py`); kinds rand-25, brand-100 and brand-300 scored on every map; n = 300 maps per class × target; plant K | per stratum (class × target × kind), the species-leg rate at .025 passes iff the one-sided binomial test of rate ≤ .05 is not rejected at α = .01 (≤ 24 of 300). Basis: the frozen set-vs-map species-leg rate is ≤ .022 in every amendment-3 stratum (`e3_gates_a3.md`), so P(fail \| a leg at .022) ≈ 2e-8; a leg at .10 fails with probability .86, at .15 with ≈ 1. The set-vs-map leg on the same maps and sets is reported beside it. The PLS species leg equals this one exactly (P7) |
| P25 | planted flawed species legs the P24 regime must catch (statistical; must-catch for (a)–(c)'s flawed legs, correct-leg test for (c)'s correct leg) | the decoded-list adapter through the production path, each flaw behind a plant-only flag; V-AAL and V-DK; n = 500 each: (a) the v2 species max (G1, universe-centred G6s, G6l; no brain matching: amendment 3 §4's reference leg) on T-brain × brand-300 × w = .9; (b) the minimum instead of the maximum over the four species legs, on (a)'s maps; (c) unconditioned G1 and G3m nulls on a between-class plant: S = 25 members of the module-generator cluster (amendment 3 §4) whose mean profile has the largest between-class share of variance, y = z(s_B(S) − s̄_B) + z(a within-class field), with s̄_B the mean class profile over all genes | each flawed leg must reject "rate ≤ .025" at α = .01 (≥ 22 of 500). Basis: (a) the frozen v2 rate on this stratum is .086 (V-AAL) and .133 (V-DK) (`e3_gates_a3.md`, planted leg (c)), so P(caught) ≈ 1; (b) the minimum rejects whenever G1 does, and G1 rejects at least as often as the v2 maximum that contains it; (c) a random null set's between-class deviation shrinks with averaging while S's members share theirs, so unconditioned G1 / G3m sets cannot reach T(S), whereas the conditioned nulls carry s_B(S) and are exchangeable. The correct legs' rates on the same maps are reported, and (c)'s correct species leg must pass P24's test at n = 500 (≤ 37 of 500). **The (a) basis is borrowed:** .086 / .133 were measured on the set-vs-map adapter, not this one. If the decoded-list v2 leg ran at .04 here, P(caught) would be .36. A flawed leg not caught with no defect named reads "plant regime insensitive for this form × class" and blocks nothing (§7, §17; re-check, C7) |
| P26 | site leg of the new adapters (statistical) | decoded-list (per-gene r recomputed per surrogate) and PLS-enrichment (refit) × V-AAL, V-DK, dk-ctx; independent fields (§6.1 generators) with class step 1 (step 0 in dk-ctx); S = rand-25; n = 300 per class; 500 surrogates each of S1c and S2c | the site-leg rate at .025 passes iff ≤ 24 of 300 (P24's criterion); basis: the adopted class-stratified pair passed prereg §6.4's false-alarm gates in every class and step stratum (`e3_gates.md:3`, adoption "strat"). Planted flaw (must-catch): within-class parcel-label permutation in place of S1c / S2c must reject "rate ≤ .025" at α = .01 (≥ 15 of 300). Basis: naive Level 0 on these fields is ≥ .15 per class (prereg §6.4's plant-active gate, retained by amendment 5 and passed: K1 "not fired", L8), measured for set-vs-map, so it is borrowed for these adapters. At .05, P(caught) is .54. Not caught with no defect named → "plant regime insensitive for this form × class", which blocks nothing; the site-leg test above stays a correct-leg test (§7, §17; re-check, C7) |

**Review:** after P0–P26 pass, asdg-skeptic reviews the runner and the plants (register §1.10 (3)) before any claim runs.
- A functional failure is a code defect: a written diagnosis, the fix, all plants rerun, then the skeptic re-checks.
- A statistical failure (probability ≤ .01 for a runner behaving as measured) gets a written diagnosis and the skeptic's
  review before anything is changed or rerun. Code is changed only for a defect the diagnosis names; then all plants are
  rerun and the skeptic re-checks.
- If no code defect is found:
  - after a **correct-leg test**, the claims of that form × class do not run until a frozen amendment says how they are
    read (amendment 5 §2: "The test is not changed a third time after its behaviour was seen",
    `prereg_amend_5.md:103-104`);
  - after a **must-catch test** (P25's flawed legs, P26's planted permutation leg), the result is reported as "plant
    regime insensitive for this form × class", beside the claims of that form × class, and they run.
- No rule, threshold or construction of a plant is changed after its result is seen (§17).

## 8. Privacy procedure (binding: `docs/ETHICS_PRIVACY.md` §2, §5; register §1.10 (2) `:1095-1098` and §1.6's guard `:802-823`)
- **One print rule for every gated script** (v3.1; review of v3, B2: v3 also let P20 and the screening step print
  screened sheet and member names, a second, looser rule). The wrapper applies the same rule to ungated carriers, so
  every carrier goes through one code path.
  - **Printed or written (stdout, stderr, logs, records, manifests): only** counts; runner-built paths (built from
    pinned keys, such as `E:\data\asdg\<key>\…`); line numbers (`file:line`); hashes; and labels from the runner's own
    fixed vocabulary (stage labels, the guard's rule letters W / N / V, "found" / "not found" and pass / fail, exception
    class names, and the status strings of the TSV and this plan). Identity records (R13, R18, `SOURCE.md`) also carry
    the URL pinned in the register or this plan, dates and times, and the server's size, date and checksum headers
    (Content-Length, Last-Modified, a plain-MD5 ETag); none of these comes from a carrier's content.
  - **Never printed or written:** any string derived from a carrier. That covers header cells, label cells, sheet names,
    zip and tar member names, extracted file names and carrier-derived path components. It also covers any participant,
    sample, donor or AHBA sample (well) id, BIDS subject label, NDA GUID, or token of those formats.
  - **How a carrier-derived string is used:** it is compared in memory with the declared names (this plan's
    declarations, such as Moreau's two sheet names, or a runner-side vocabulary, below). The result is reported as
    pass / fail counts plus the sha256 of the string (UTF-8). Example: "declared sheets 2 / 2 found; undeclared 7 (not
    fetched); sheet-name sha256 …".
  - **Extracted content.** Cell content is never printed. It is written only as the needed group-level or gene-level
    object (step 5; gated sets built by the frozen §1.6 rules, "only the needed gene-level content is kept",
    `claims_register.md:819-820`), never as a carrier's header, label or sheet strings. Values are keyed by the
    runner-side names the carrier's labels were matched to in memory (the abagen DK names, the pinned HCP-MMP1 label
    list, the MIST64 identifiers of `mist64_classes.json`, the S-build's HGNC / Ensembl mapping, the universe's
    columns). Gene sets are written as the frozen S-build writes them (HGNC-mapped members, mapping counts, drop lists).
    A carrier label that matches nothing is counted and its sha256 recorded.
  - **Files saved from a carrier** (an extracted member, a reduction) take runner-built names: the declared name (for
    example `lh.aparc.annot`, R16) or `<key>_member<index>` with the declared extension, never the member's own name.
  - **Exception handlers** print the exception's class name, the stage label and the raising code line only. They never
    print the message text, a traceback or a local value (details under "Screening" below).
  - **Relation to the register.** Register §1.10 (2) asks for gated work "by scripts that print nothing but counts and
    hashes: carriers are inspected by header and sheet names only" (`claims_register.md:1095-1096`). This plan reads
    "counts and hashes" as excluding everything a carrier supplies. A runner-built path, a line number, a label of the
    runner's own vocabulary, and an identity record's pinned URL, dates and server headers (the identity fields the
    register itself asks for, `:1090-1094`) carry nothing from a carrier; these are the only additions, declared here.
    Inspection by header and sheet names happens in memory, as the register says. The pre-freeze builder rule, which
    let a refusal name its sheet (§1.6, `:816-817`), is not used for gated work.
  - Workers return the same.
- **Fetch-and-extract wrapper** (new: `arcs/audit/src/a1_audit/fetch_extract.py`). It never prints a cell and never
  deletes. In order:
  0. **gate:** before any network request or file open, the target's gate check runs (`step3v_open()` for G2,
     `require_g1_open()` for G1; ungated targets pass). A closed gate means a refusal and no request (P21);
  1. **fetch** with the frozen `src_register/fetch_util.get`, which sends no identifier and returns sha256. It writes
     `SOURCE.md` (URL, date, bytes, sha256) beside the file under `E:\data\asdg\<key>\`;
  2. **identity:** compare the R13 fields (`claims_register.md:1090-1094`) against `IDENTITY_prefreeze.json` and write
     the record into `register_maps/post_freeze/<gate>/` (R18). A mismatch means "not auditable (map changed)";
  3. **workbooks: declared sheets only** (both reviews: v1 classified every sheet, and the guard's classifier reads a
     sheet's cells, so v1's step 3 would have opened Moreau's ABIDE sheets):
     - sheet names come from `wb.sheetnames` (openpyxl read-only, from the workbook part) or `book.sheet_names()` (xlrd
       with `on_demand=True`, which loads no sheet). Each name stays in memory, is compared with the declared names and
       screened (below), and is recorded only as its sha256 (the print rule above);
     - each **declared** sheet is fetched by name through one accessor that appends to an access log, then classified
       with the frozen `privacy_guard.classify_openpyxl` / `classify_xlrd` (rule letters W/N/V and counts only), and its
       dimensions are recorded;
     - an **undeclared** sheet is never fetched: no cell and no dimension (openpyxl reads a sheet's dimension from that
       sheet's own part); only the sha256 of its name is recorded, and the undeclared sheets are counted.
       `guard_workbook_openpyxl`, which iterates every sheet, is never called;
     - after the read, the wrapper asserts that the access log holds declared sheets only and nothing from the target's
       **do-not-open list**. Moreau `Supplementary_Table_S1.xlsx`: `5_BIV`, `6_ASD`, `7_SZ`, `8_ADHD`, `9_Ranking`
       (not opened before the freeze, `register_work/moreau2020mutations.md:24-25`; "the workbook's ABIDE sheets stay
       unopened", `claims_register.md:1778-1779`; "No ABIDE data (I or II) … are read in A1", `prereg.md:45`). Its other
       undeclared sheets are not touched either;
  4. **read:** declared sheets and declared columns only, through `privacy_guard.read_openpyxl` / `xlrd_cell_reader`. An
     identifier-bearing sheet needs declared columns, else the guard refuses. A declaration is exact header texts or a
     column rule applied to a header row inside the first 20 rows (`claims_register.md:818`). No header row or cell is
     printed to find columns.
     - **Moreau's declaration (pinned now; second review, A3).** Sheets `1_16p11.2Del` and `3_22q11.2Del`. Each holds
       "64 row × 64 column labels + 64×64 numeric block" (`register_work/moreau2020mutations.md:34`), so its populated
       width (≥ 65) exceeds 50 and the guard classifies it W.
       - **Identifier forms** (from `register_maps/mist64_classes.json`, whose 64 parcels each carry `roi` (int 1–64),
         `label` and `name`), tried in this order:
         1. `label`, matched by a text cell equal to it **case-insensitively** (both sides stripped of surrounding
            whitespace and casefolded);
         2. `name`, matched the same way;
         3. `roi`, matched by a cell of **any type** that equals the integer: an int, a float with an integral value, or
            a text of digits.

         Case-insensitive since v3.1 (review of v3, C3 (b)). 49 of the 64 labels and 41 of the 64 names are mixed
         case, and the draft never recorded the workbook's label form, so an exact-case match could refuse the read
         over a formatting quirk. Casefolding loses nothing: the 64 labels stay distinct when casefolded, so do the 64
         names, and no casefolded label equals a casefolded name (counted 2026-10-01; no value printed).
       - **Header row: found through the frozen guard's own API** (v3.1; review of v3, C3 (a)). The guard applies a
         column rule to one caller-given row, `rows[header_row]` (`privacy_guard.py:306-324`, `_declared_positions`
         `:287-295`), and refuses when the rule returns no positions. v3's "applied to the zone's values in memory"
         would have meant reading the first 20 rows outside the guard. Instead the wrapper loops `header_row` = 0, 1, …,
         19 and calls `read_openpyxl(ws, declared=<the column rule>, header_row=h, label=…)` for each h. The first h for
         which the guard returns rows is the header row. A `Refused` raised for an h that does not qualify is caught by
         the §8 handler, and nothing of its message is printed; only the count of rows tried is recorded. If no h in
         0–19 qualifies, the read is refused.
       - **The column rule** (a function of the one row the guard passes it; nothing is printed) returns `[]` unless that
         row's cells, of any type, hold all 64 identifiers of one form, each in exactly one cell, with at most one other
         non-empty cell (a corner label), which must sit in the row-label column. Otherwise it returns the 64 matched
         positions plus the row-label column: the position immediately left of the leftmost matched position, which must
         exist. (Re-check of v2, C4: v2's "exactly 64 non-empty texts" could never reach the `roi` form and refused a
         corner label.)
       - After the read, the wrapper asserts that the row-label column of the following rows holds the same 64
         identifiers in the same form (matched as above), each once, and that all 4,096 block cells (those rows × the 64
         columns) are numeric.
       - The pre-freeze draft read these sheets' row and column labels without printing a value
         (`register_work/moreau2020mutations.md:20-22`). It does not record their form, so the rule accepts all three.
       - Any failure means a refusal, and MOR-C1 … C3 and MOR-T1 / T2 read "not auditable (definition not applicable:
         the declared Moreau sheet layout not matched)". Only counts and the rule's letter are printed;
  5. **save:** the extracted group-level object (runner-side labels + values, as the print rule above says) goes to
     `artifacts/` or `E:` with its sha256, verified by read-back without printing;
  6. **flag and quarantine** (second review, B7). This applies to a carrier with any identifier-bearing sheet, or a known
     per-participant supplement, right after its extraction is verified:
     - the carrier is moved (same volume; sha256 re-checked) to `E:\data\asdg\_quarantine\<gate>\<key>\`;
     - the audit runner refuses any path under `_quarantine`, and the orchestrator puts that folder on the exploration
       lane's refusal list before the first extraction (§18, F5);
     - re-extraction needs the operator to move the file back;
     - the wrapper raises the deletion request at once, in the same session (an A1 ARC entry and a line in the session
       report), citing register §1.10 (2): a carrier holding participant-level data "has only the needed group-level
       object extracted once, then is deleted" (`claims_register.md:1096-1097`);
     - **the deletion is an operator-authorised step [default 24, declared; re-check, C2].** The register requires the
       deletion but does not say who deletes. Its own §1.6 practice had the builders delete identifier-bearing originals
       under the v6.8 rule (§19). For this audit the orchestrator sets a stricter default under the standing delegation:
       the wrapper and workers never delete; the deletion is carried out by the operator, or under an authorisation the
       operator gives through the permission system. The reason is recorded: in this session (2026-10-01, the
       orchestrator's record) the permission system refused agent deletions. The deletion is recorded with the
       carrier's sha256 in its SOURCE.md and the A1 ARC.
- **Screening of names, members, paths and exception text** (second review, A4; narrowed in v3.1). The guard screens
  header-zone cells, not sheet names, zip-member names or paths. The register has already recorded one incident by that
  route: "an NDA GUID printed once to a worker's console while it read the sheet names of Segura's Table S8 workbook",
  declared an ETHICS_PRIVACY §2 incident (`claims_register.md:142-145`).
  - Since v3.1 no carrier-derived string is printed or written, screened or not (the print rule above). v3's rule,
    "screened before it is printed, logged or recorded", is withdrawn (review of v3, B2).
  - `screen(s)` still runs, in memory, on every sheet name, zip or tar member name, extracted file name and
    carrier-derived path component. It applies the frozen guard's `id_value_hits(s)`, `ID_WORDING.search(s)` and
    `BARE_SUBJECT.match` to each token. Only its hit counts per rule letter (V or N) are recorded. A hit makes the
    carrier count as identifier-bearing for step 6 (quarantine and the deletion request).
  - Paths the runner builds from pinned keys (`E:\data\asdg\<key>\…`) are printed as built.
  - **Exceptions:** every carrier-touching stage runs inside a handler that prints only the exception's class name, a
    stage label and the raising code line (for example "ValueError at read:declared-columns, fetch_extract.py:212").
    Message text, tracebacks and local values are suppressed and never stored. This includes the guard's own `Refused`
    messages, which name the sheet.
- **PDFs** (Patel eTable 4; Rasero mmc1; Mamat Additional file 1):
  - parsed with pdfplumber 0.11.10 (L14) by a non-printing transcription;
  - read-back compares the stored values with a second parse, printing counts and hashes;
  - only the needed page is parsed.
- **Other carriers:**
  - **BrainSpan:** only the declared sample columns (age, structure acronym) are read; donor columns are never read.
  - **AHBA per-donor builds:** donor ids are never printed; files are saved by position index, with the mapping kept in a
    JSON that is never printed. `artifacts/ahba/loo` file names are not listed in any output. AHBA sample (well) ids in
    abagen's per-sample output (R10) are replaced by row positions at once and never printed, logged or saved; donor
    columns of abagen's sample counts (R11) are read by position.
  - **G1 carriers:** carriers go through `carrier_test.py` unchanged, started only by the gate launcher (§2.2), which
    runs `require_g1_open()` first. It prints nothing of a carrier, and it is "not wired to the guard" by design
    (`:779-781`). The wrapper's classification of declared sheets is recorded beside it, without altering the criterion.
- **Incidents:** if an identifier is printed:
  1. stop;
  2. propagate nothing (no copy into any file or message);
  3. record it in the A1 ARC as an ETHICS_PRIVACY incident with counts only;
  4. tell the operator.

  A transcript cannot be scrubbed; that is declared.
- **Self-tests:** the guard's own self-test (46 / 46) runs before the first workbook of each gate (L13). P20 and P21 run
  before any carrier.

## 9. Exposure bookkeeping
- **Each gate's results go to A3's ARC.** "Results of gated targets are recorded in A3's ARC as post-freeze exposures
  (LEAP included)" (`claims_register.md:116-118`). After each gate's rows run, the orchestrator records the targets, maps,
  cells, the results commit and the counts there.
- **LEAP maps (Pretzsch, Leyhausen)** are exposures for any future A5 (`prereg_amend_4.md:50-51`). Seelemeyer's GIFTIs
  are not used and stay unread.
- **Segura** is an exposure for any later A3 HBN amendment (`claims_register.md:114-115`).
- **The exploration lane opened the ENIGMA-ASD tables before this plan was written (post-freeze exposure, recorded in
  e49a024 in both ARCs: A3 `ARC.md` Results, "Post-freeze exposure", and the A1 `ARC.md` entry of session 10).** All
  times are local, 2026-10-01. The tables were opened by the unconstrained discovery lane's propose phase (workflow run
  wf_a992ecba-de5, the "protocol" judge), reading through `explore/discovery/guard.py`:
  - **14:25:16, path check only: 20 log records.** They are 19 CortThick-named files (18 case-control tables, both ASD
    tables among them, and the lifespan table) and the `E:\data\asdg\enigma_asd` folder. No content was read. (v3 wrote
    "19 CortThick tables, the lifespan table and the folder", which counted the lifespan table twice; review of v3,
    C1 (a).)
  - **14:30:13, read:** 15 tables (the ASD mega- and meta-analysis CortThick tables, 11 comparator disorders, 22q11 and
    the lifespan table). It printed, per file, the count of non-null `se_icv`, the median `se_icv`, the SD of `d_icv`
    across the 68 rows, and the left-right correlation of `d_icv`.
  - **14:30:43, read:** 13 of them, both ASD tables included. It printed, per file, var(`d_icv`), the mean sampling
    variance from the n columns, and a per-hemisphere reliability ratio.
  - **Not computed:** any correlation with a gene set, expression map or other brain map, and any claim statistic.
    Hemisphere-averaged maps were built in memory and not printed.
  - **Who read the committed manifest table** `explore/discovery/data_manifests/enigma_toolbox_sumstats_table.csv`
    (per-file n, effect min / max, CI flags). v3 listed the proposer only (review of v3, C1 (b)):
    - the "cross-disorder" proposer, 13:56–14:05. It also read A3's committed `step3v_results.md` (14:01);
    - the novelty judge, 14:24:00–14:24:07. It printed the table's head, the effect min / max of 18 CortThick files
      (both ASD tables among them) and the sumstats summary JSON;
    - the protocol judge, 14:25:22–14:25:29. It printed manifest rows.

    These reads are not in `opened_paths.log`: v3.1 found 0 records naming a manifest, a summary file or
    `step3v_results.md` between 13:50 and 14:45. They are known from the agents' tool inputs, which the review of v3
    scanned with every digit masked (`…/scratchpad/skeptic_final/wfcmds.py`, `wfscan.py`). The v3.1 reviser did not
    re-run that scan, so as not to open the run's transcripts.
  - **Who saw the values** (review of v3, C1 (c)):
    - the per-file descriptives of 14:30: the protocol judge only;
    - the manifest table's effect ranges: the proposer and the two judges.

    The orchestrator printed the commands, not their output, and the review of v3 found no value-bearing phrase in its
    transcript. No author or reviser of this plan saw any of these values.
  - **Exposure-bearing files** (v3.1; review of v3, C1 (c)). The values persist in three places. No audit or plan agent,
    and no author or reviewer of A4, reads them. `<P>` is the orchestrator session's Claude Code project folder,
    `C:\Users\info\.claude\projects\d--RESEARCH\<session id>\`; the run id `wf_a992ecba-de5` identifies the files, and
    the session id is not copied into this plan.
    - the workflow record `<P>\workflows\wf_a992ecba-de5.json`. The protocol judge wrote its per-hemisphere reliability
      table (ASD mega-analysis and comparators) and median `se_icv` values into its structured output, which the record
      stores (`result.panel[1].scores[6].required_changes`, `result.ranked[5].notes[1]`, `result.ranked[7].notes[1]`);
    - that run's agent transcripts, `<P>\subagents\workflows\wf_a992ecba-de5\`, which store each command's output;
    - the committed manifest table named above (per-file effect min / max).
  - **Afterwards:** the discovery run phase chosen uses no ENIGMA map (bench decision ev-1a0f778987167ed).
  - **The log agrees.** It was tabulated by masked scripts that printed counts and timestamps only: v2's tabulation,
    reproduced by the re-check; v3's re-count at 27,091 lines (last entry 16:19:41); the review of v3's at 27,152 lines
    (to 16:31:37); and v3.1's at 27,449 non-empty lines (last entry 17:03:36; `…/scratchpad/runplan_v31/logcount.py`).
    - On 2026-10-01 there are 48 ENIGMA-keyword records: 20 at 14:25:16 (19 CortThick-named, 1 of them lifespan-named
      and 2 ASD-named, and 1 folder record), 15 at 14:30:13 (2 ASD-named, 1 lifespan-named) and 13 at 14:30:43 (2
      ASD-named, no lifespan) (v3.1).
    - So there are 47 CortThick open records of 19 distinct names: 19 at 14:25 and 28 at 14:30 (15 + 13).
    - The two ASD tables have 6 records together, 3 each (v2: lines 17905–17906, 17960–17961 and 17980–17981).
    - There is one folder record, and no ENIGMA record after 14:30:43 (v3, v3.1).
    - No path names LEAP, EU-AIMS, Patel, Giacomel, Hansen, Liu, Pretzsch or Leyhausen (v2, re-check).
  - **Status:** allowed (after G2 opened at 4efbae5 and after the register froze). It is declared as an exposure of the
    ENIGMA-ASD maps behind Patel, Giacomel, Hansen and Liu T3, and of Level 4's sibling-disorder maps.
- **The orchestrator's declaration for this plan (F2).** Every reading in this plan was written after that exposure:
  v1 was first written at 14:40:51 (edits until 14:41:56; v3 said "created 14:41:56", review of v3, C1 (d)), and v2,
  v3 and v3.1 were written later the same day. That covers all of R1–R31, the §6 items, the plants and the thresholds.
  - **None of them uses those values** (the 14:30 descriptives or the manifest table's effect ranges). The plan's author
    and revisers never saw them, and the orchestrator did not see the values.
  - **The declaration covers every reading that bears on a G2 target.** Those that touch the ENIGMA-derived cells are:
    - R1 (two-sided p: Giacomel's published nulls, Liu T3, Patel's panels);
    - R9 (Giacomel's six subcortical cells);
    - R11 (the ≥ 2-donor sensitivity on every claim with a verdict);
    - R12 (Hansen's PC1);
    - R13 (Patel's mean bicor);
    - R17 (Giacomel's rebuilt DEG maps);
    - R24 (Giacomel's weighted G3, and Level-2 G3);
    - R25 (Level 4 on the ENIGMA-ASD maps);
    - R27 (the reproduction functionals and labels: Patel, Giacomel, Hansen, Liu T3);
    - R29 (the BH family);
    - the general readings R2–R7, which apply to them as to every claim.
  - **The one reading these values could bear on is Level 4,** which ranks against the sibling maps whose spread and
    effect ranges were printed. It stays "not auditable" (R25), and any A4 is declared post-exposure, with this listing
    and the exposure-bearing files repeated before A4 is frozen.
  - The record in both ARCs (e49a024) carries the facts above as v3 stated them. The line added to the A1 ARC when the
    plan is frozen (F2) names these readings and carries v3.1's corrections: 20 records at 14:25:16; the two judges'
    manifest reads; the exposure-bearing files; v1 first written at 14:40:51.
- **Prior exposures** stay as declared (register §0 items 1–9, `:120-182`), including R2 on Giacomel and the Liu-note
  recomputation.

## 10. Ungated targets (Segura 1, Moreau 18, Liu 10 minus T3; Xing 11 and Vairam / Roy 9 reported by status)
**Rows.** 115 rows: Segura 80, Vairam / Roy 6, Liu 8, Xing 12, Moreau 9. Counted from the TSV.
- **Segura (78 computed):** SEG-C1, SEG-C3a/c/e/f/g, SEG-C3-D01…D71 and SEG-C2. SEG-C3b and SEG-C3d are "not testable
  (< 5)". All are signed decoded-list descriptors with their verdict legs plus T_abs, two-sided, on V-AAL (TSV row 3 `T`).
- **Moreau:** MOR-C1/C2 (component, in m), MOR-C3 (descriptor) and MOR-T1/T2 (R21) are computed; MOR-R1…R4 are not
  testable as stated (no T); MOR-G is excluded.
- **Liu:** T1, T2, T4, T5 and the descriptor cells T2-STR/-CBC/-HIP are computed (R10); T6 is not auditable.
- **Xing:** all 12 rows are not auditable. **Vairam / Roy:** deferred.

**Material and identity at use (local sha256 vs `IDENTITY_prefreeze.json`).**
- Segura 790618 (71,440 B, 802b4b6b…) and 781986 (75,117 B, 0c476e8e…);
- Moreau `Supplementary_Table_S1.xlsx` (468,991 B, c947112d…, blob 7a8b62be…), declared sheets `1_16p11.2Del` and
  `3_22q11.2Del` only;
- BrainSpan `expression_matrix.csv` (e8d98aa0…, TSV row 471);
- PCP AAL atlas (40b1edfa…, `:1030`);
- MIST64 matrix and classes (L6, L7).

**Fetch (ungated).** NeuroVault decoder outputs for 790618 and 781986 (R22).

**Builds (`env/venv_ref`).**
- per-donor V-AAL matrices (R14 / R22 fallback);
- Liu T4/T5 sample assignment (R10);
- the multiverse matrices (R11).

**Re-parcellation.** Volume → V-AAL by the §1.7 volume rule (voxels = 0 missing; < 50 % coverage dropped). Moreau uses
native MIST64 (46 primary parcels: cortex 33, subcortex 5, cerebellum 8; `:1269-1274`).

**Plants used.** P3–P6 (V-AAL decoded-list), P11, P12 (MIST64), P16, P17, P20 (Moreau's declaration), P24–P26 (V-AAL).

**Compute.** About 50 process-h: verdict legs about 21, descriptor legs about 29, Segura about 46 of the total. At about
18.75 effective jobs that is about 2.7 wall-h (§14). The ≥ 2-donor sensitivity (R11) adds at most the verdict legs again
(≤ about 21 process-h), and nothing for classes whose parcel set does not change.

## 11. Gate G2 (Patel 2, Giacomel 3, Liu T3, Pretzsch 16, Hansen 19, Leyhausen 20; Seelemeyer 21 not auditable)
**Rows.** 194 rows; m = 50 (Patel 3, Giacomel 14, Liu 1, Pretzsch 4, Hansen 1, Leyhausen 27). The population adds 4 units
(PAT-C1…C4; `:1890`). About 126 rows run through the verdict machinery, plus 2 component rows (Hansen); PAT-C4 is not
auditable (`:1453-1454`).

**Downloads, with identity fields at download (R13, `:1090-1094`; probes in `IDENTITY_prefreeze.json`).**
- Giacomel `ENIGMA_structural_organised.xlsx` @93de089: size 16,073 + blob 46323903…;
- the repository lists at e045bc5 and the eda33ab GEDAR maps, by blob ids from the tree listings
  (`register_maps/gia_mdd_paths.json`);
- the Sadeghi DEG workbook, if it is not already under `E:\data\asdg\giacomel2026cartography\external\` (checked by
  listing that folder's names in memory and comparing them with the declared file name; reported as found / not found,
  with name sha256s, §8's print rule);
- FreeSurfer 7.4.1 `lh.aparc.annot` (R16; the first download of WP4);
- HCP-MMP1 volume and label list (R15);
- NeuroVault decoder outputs for 777428–777430 (descriptive reproduction).

**Local copies checked by sha256 at use.**
- Giacomel @c022a29 (16,118 B, a4d4fe…);
- Hansen `enigma_ct.csv` (3140921…; blob caebb2c0… after LF) and `gene_pc1.csv` (a078a86d…; blob a5caaf68…);
- Liu T3 CortThick (ee076971…, blob 6eb2c4c8…) and SubVol (b2b0b02c…, blob 0ec6cb15…);
- Patel supplement PDF (2,545,816 B, d9da0b80…);
- Pretzsch derived CSV (26,343 B, 0ef57d23…);
- Leyhausen lh GIFTIs (3c5dfc21…, 4429d1da…, 9436a9e9…), plus the NeuroVault `file_size` equality.

**Extraction (wrapper §8; counts and hashes printed).**
- Patel: eTable 4 Estimate, 34 left DK values (PDF p. 26; `:1449-1450`);
- Giacomel: sheets `Thickness` / `Subcortical`, ASD and MDD columns at 93de089. The c022a29 comparison records the count
  of differing cells only, and 93de089 governs (`:1457-1459`);
- Liu T3: L/R average, d_icv, left V-DK; ventricles dropped (`prereg.md:298`);
- Hansen: left rows, Cammoun order 35–68 → DK;
- Pretzsch: 180 left Glasser loadings → dk-ctx (R15);
- Leyhausen: lh GIFTI → dk-ctx (R16).

**Gated sets (built under G2 by the frozen §1.6 rules).**
- Giacomel's repository lists for GIA-C07…C18 and GIA-MDD-U1/D10. Columns < 5 → "not testable (< 5)", and the population
  is restated (`:260-262`);
- the MDD-DEG and ASD-DEG descriptor sets and the rebuilt DEG maps (R17).

**Before any G2 map is read.** The Patel bicor (R13) is pinned and tested.

**Plants used.** P3/P4 (dk-ctx, V-DK, V-DK-subcortex), P8, P9 (subcortex resolution-limited), P5/P6 (dk-ctx
decoded-list), P15, P12 (fixed component), P17, P18, P19, P24–P26 (dk-ctx, V-DK).

**Seelemeyer.** 34 rows "not auditable" (NeuroVault 13397 rejected, `:1810`). The GIFTIs on disk are never opened.

**Compute.** About 118 process-h: verdict legs about 22, descriptor legs about 97. Pretzsch is about 77 of it (G2/G4/G5
on sets of up to 1,679 columns), Leyhausen about 22, Giacomel about 13, Patel about 3, Liu T3 about 0.6, Hansen about 0.3.
v1's 115 priced the dk-ctx G6l screen from amendment 3's per-seed figure; at the measured audit-scale screen time (§14)
the verdict pass rises by about 3 process-h (the second review's estimate). That is about 6.3 wall-h. The ≥ 2-donor
sensitivity adds at most the verdict legs again (≤ about 22 process-h).

## 12. Gate G1 (Romero-Garcia 4, Berto 5, Rasero 6, Buch 7, Mamat 8, Wan 12, Pagani 13, Benkarim 14, Park 17)
**Rows.** 380 rows; m = 153 (Romero-Garcia 3, Rasero 14, Buch 84, Mamat 22, Pagani 10, Benkarim 12, Park 8). The
population adds ≤ 196 units (`:1889`). About 273 rows run through the verdict machinery, plus 14 component rows.

**Precondition.** `require_g1_open()` (§2.2) in every script and before every G1 download; every G1 plant and reading is
already reviewed (R19); A6 is decided (§6; §18, F4).

**Carriers (conditional, `:1052-1053`; carrier tests pre-registered, printing pass/fail and counts).**
- Rasero: notebook 05 / `mmc1.pdf`; its dk34 / dk41 choice fixed from notebook 08 by §2.6's rule;
- Buch: `MOESM3.xlsx`, ≥ 230 usable ROIs with coordinates (sphere rule);
- Mamat: Additional files 1–4, 400 Schaefer-400 / 17-network parcels by name, or by index only if the carrier names the
  17-network order file (R9 of v6);
- Romero-Garcia: MOESM1/2 docx, the Apollo SI `.txt` and `Figures_Tables.zip`, needing 152 left DK-308 labels; MOESM3.

**Source-1 runs.** 233 cells (Buch 208, Romero-Garcia 13, Pagani 12) with `carrier_test.py source1` and corroboration (and
`--view near_miss` for the secondary view). Family cell counts are fixed when their tables are read (`:199-201`).

**Maps and identity.**
- Pagani: GitHub @ef58cf1, asserted byte-equal to NeuroVault 14698 (GitHub governs);
- Benkarim: 8667 (404555, 404554);
- Park: 743 (396720; 319367 as descriptor);
- each by the R13 fields.

**Re-parcellation.** Schaefer-400 → dk-ctx (nilearn `fetch_atlas_schaefer_2018(400, 17, 1)`; version and sha256
recorded); DK-308 → dk-ctx (`lh.500.aparc.annot` @e351b3cf); Power spheres → V-AAL.

**Rows with pools smaller than S** (R8).
- BUCH-E-SZ-S1 … S4 (descriptor cells, not in m): G1, G3m, Level-2 G3, J1 and the naive joint are "not computable
  (pool < m)";
  G6l, G2 and G4 are "unmatched" (their frozen labels, R8); G5 is "not applicable" (pool < 2m); Level 0, the site leg
  and G6s are computed (scout model: about 81 process-h falls to about 0.3).
- MAMAT-E-Tissue-URG / -DRG (in m): G3m is not computable, so the cells read "not auditable (definition not applicable:
  null pool smaller than S)" unless A6 says otherwise; G4 is "unmatched"; Level-2 G3 is "not computable (pool < m)";
  every other leg is computed if its pool check passes (G5 needs a pool of at least 2m = 2,786 genes, not checked
  yet: if it fails, G5 reads "not applicable", its frozen label; v3.1 review N-C1).
- PAG-C1/C2 and MAMAT-E-URG-BP-2: G4 is "unmatched" and Level-2 G3 "not computable (pool < m)".

**Plants used.** P7 (PLS refit), P13, P14, P18 (Schaefer, DK-308, spheres), P4–P6, P11 and P24–P26 on V-DK for Rasero's
conditional V-DK class (34 cortical + 7 subcortical parcels: the subcortex is permuted within class while the cortex uses
S1c / S2c), with the KEGG-family runs under §1.6's rule.

**Compute.** About 177 process-h without the four SZ rows (scout model 259 with them), about 9.5 wall-h. Its dk-ctx rows
(Mamat, Benkarim, Park, Romero-Garcia, Rasero) were also priced from amendment 3's per-seed G6l figure; they are repriced
at the measured screen time (§14) before WP5, and the ≥ 2-donor sensitivity adds at most G1's verdict legs again.

## 13. Deferred targets
- **Dear (target 15; G1+G2):** it runs only after a frozen amendment records provenance (A1): BrainChart SI19 showing that
  none of the 381 ASD cases come from ABIDE II or HBN (`prereg_amend_4.md:40-43`). Then both gates must be open. Its cost
  is about 1 process-h.
- **Vairam / Roy (target 9):** deferred (A2). Running it would open ABIDE II imaging, which A1 never does (`:1650-1653`).

## 14. Compute budget and scheduling
- **Model and sources:**
  - the scout's cost model (`a1-runplan-inputs.md` §4), from A3's audit-scale timings
    (`artifacts/replication/step3v/h2k3_run_66c8e1757612_4e320100/ck_test*.json` "seconds"; `run_step3v.log` 48,892
    process-s over 2,607 wall-s ≈ 18.75 effective jobs; contention ≈ 2.5–2.6×, `gates_h2_smoke_timing.json`);
  - a single-process G2-sampler bench (≈ 0.6–0.65·m s per 10,000 sets);
  - G6l at 21 / 14 / 11 ms per seed (`prereg_amend_3.md:232-233`) for plant mode only;
  - **audit-scale G6l (v2, second review C2):** the exact screen is priced at the A3 audit-scale times measured under
    20-job contention, from the `seconds` of the 79 `ck_test*.json` files of the h2k3 run: median 279.5 s at 33 parcels
    (7 files), 340.1 s at 40 (33), 345.9 s at 41 (7) and 483.9 s at 49 (32); the site draw's median is 201–223 s. dk-ctx
    (34 parcels) is priced at ≈ 280 s per (S, class, parcels) screen.
- **Uncertainty:** estimates may be off by about 2×. Nothing uses the GPU (no torch or cupy in the venv).
- **Memory:** chunked refits, ≤ 2.5 GB per job (§4).

| block | process-h | wall-h (≈ 18.75 jobs) |
|---|---|---|
| plants P0–P23 (P3a / P3b, P5–P7: ≈ 45 plant batches × ≈ 0.2–0.4 h; P4: ≈ 40 s × 100 plants × 10 cells ≈ 11 h; the rest small) | ≈ 20–30 | ≈ 1.1–1.6 |
| plants P24–P26 (P24: 1,800 maps × 3 kinds at plant K, G6l plant mode ≈ 2–4 s per set; P25: 2,000 maps; P26: 1,800 fields × 2 adapters at 500 surrogates; contention ≈ 2.5×) | ≈ 20–30 | ≈ 1.1–1.6 |
| `venv_ref` builds (3 normalisation cells + bilateral for V-AAL and V-DK = 8; per-donor ×3–4; sample counts ×3; Liu samples ×1; 140–205 s each, `artifacts/ahba/loo/build_all.log`) | ≈ 1 serial | ≈ 1 |
| ungated (verdict ≈ 21 / descriptor ≈ 29) | ≈ 50 | ≈ 2.7 |
| G2 (verdict ≈ 22 / descriptor ≈ 97) | ≈ 118 | ≈ 6.3 |
| G1 (without the SZ rows' infeasible legs; repriced before WP5) | ≈ 177 | ≈ 9.5 |
| ≥ 2-donor sensitivity (R11): the verdict legs again, only for classes whose parcel set changes | ≤ the verdict passes (≤ ≈ 21 / 22 / G1's) | — |
| survivors' multiverse (R11): 10 cells × (0.3–2.4) per survivor | 3–24 per survivor | — |

- **Schedule:**
  - 20 jobs, `OMP_NUM_THREADS=1`;
  - checkpoints per row × leg;
  - the verdict pass first, then the descriptor pass, per gate;
  - G2's descriptor pass (≈ 5 wall-h) and G1's verdict pass run as overnight windows;
  - longest-processing-time ordering (A3 `lpt_makespan`).
- **Overrun:** at more than 2× the block estimate the run pauses at the next checkpoint and reports. Nothing is dropped.
- **Multiverse cap:** the survivors' multiverse runs in batches of at most 25 process-h. After each batch it pauses at a
  checkpoint and reports (survivors done, cells done, hours used), and the orchestrator releases the next batch. Nothing
  is dropped; the order is fixed in advance (survivors by TSV row, cells in R11's order).

## 15. Review record
Two asdg-skeptic reviews of v1 (2026-10-01): **S1** "not-verified" (2 A / 9 B / 3 C) and **S2** "refuted" (4 A / 8 B / 5 C).
Every A and B finding is fixed in v2. Every C finding is fixed too, because each fix was cheap. Where v2 adopts a fix in
part, the part not adopted is rebutted in §19 with its frozen quote.

The asdg-skeptic **re-check of v2** (2026-10-01; **RC**) returned "verified-with-residues" (0 A / 0 B / 8 C). None of
the earlier A or B findings is still open, and the revision added no new A or B problem, so F1 is met. v3 answers the
eight C points (rows RC-C1 … RC-C8, at the end of the table). It also carries the orchestrator's v3 items: the record
commit, the exposure facts, and the `g1_open()` simulation (§0.3, §0.4, §2.2, §9).

The asdg-skeptic **review of v3** (2026-10-01; **V3**) returned "not-verified" (0 A / 2 B / 6 C). It reproduced
`g1_open()` on the real record, the 25 P21 refusals, the attestation hash, the record commit, the plant tails, the L8 /
L9 hashes, and the quotes of the readings it checked against their frozen lines. Its two B findings are F6's false
premise about ABIDE II and a second, looser print rule for gated scripts. v3.1 answers both and the six C points (rows
V3-B1 … V3-C6, at the end of the table).

**Correction to the A1 ARC (review of v3, C2).** The A1 `ARC.md` entry written in e49a024 (`ARC.md:842`) gives the
first review as "fidelity 2 A / 7 B / 3 C". The review record, the header and this table have **2 A / 9 B / 3 C** (rows
S1-A1, S1-A2, S1-B1 … S1-B9, S1-C1 … S1-C3). The orchestrator corrects it in the A1 ARC.

| id | sev | finding (short) | how it was answered (where) |
|---|---|---|---|
| S1-A1 | A | §8 step 3 classified every sheet by reading its cells, which opens Moreau's ABIDE sheets; step 4 said the opposite | fixed: declared sheets only, undeclared sheets never fetched (no cell, no dimension), do-not-open list checked against an access log (§8 steps 3–4); P20 |
| S1-A2 | A | "genes are z-scored" unqualified would change the set-vs-map statistic (51 rows, frozen-11 included) | fixed: gene scaling stated by form, set-vs-map on the unchanged §3.1 values (§4); P0 (b) |
| S1-B1 | B | R8 missed MAMAT-E-Tissue-URG / -DRG; relabelled G6l's frozen "unmatched"; G6s and computable legs not reported; §6's "no population effect" false | fixed: R8 rewritten with a per-row table (`feas.py`); G6l keeps "unmatched"; G6s and every computable leg reported; A6 not optional (§6; §18, F4) |
| S1-B2 | B | R1's direction requirement contradicted amendment 3's "iff … each < .025; conjunction p = max"; two-cohort direction open | fixed: d* = argmin_d max_leg p(d), reported leg p = 2·p(d*), conjunction p = 2·min_d max_leg p(d), used by BH; one d* for two-cohort claims; "adds a requirement" withdrawn (R1); P8 |
| S1-B3 | B | L8 / L9 pinned CRLF working-copy hashes that a clean LF worktree cannot match | fixed: blob ids and LF hashes asserted, CRLF forms rebuilt and checked (§1, line endings); P1 runs in a fresh worktree |
| S1-B4 | B | R10 ran Liu's G3 while R24 said no G3 seed leg may be created; Giacomel / MDD weighted G3 not drawn; universe pinned but coexpression basis declared undefined | fixed: one G3 seed rule for every use (R24); Liu's universe and coexpression both from the statistic's own data, G1–G5 run (R10); A3 and A5 withdrawn (§6); affected Giacomel cells listed (R24) |
| S1-B5 | B | ≥ 2-donor sensitivity restricted to survivors without basis; multiverse not crossed | fixed: ≥ 2-donor sensitivity for every claim with a verdict; the crossed (zscore, False) cell added (R11); cost in §14 |
| S1-B6 | B | R18 moved manifests away from the register's named folders on a tension that does not exist | fixed: `register_maps/post_freeze/<gate>/` and `register_sets/post_freeze/<gate>/`, outside every frozen glob (R18) |
| S1-B7 | B | readings missing for BENK-C2 / PARK-C5, the BH family, the GeneOverlap universe, Benkarim's parcellation | fixed: R28, R29, R30, R31 |
| S1-B8 | B | P3's "≥ 4 of 5" was a power requirement with no measured basis; the stop rule then pressed for code changes | fixed: P3a functional (production = frozen engine), P3b thresholds from the frozen catch rates; plant kinds and stop rules (§7, §17) |
| S1-B9 | B | pre-exposure claim overstated; the lane opened the ENIGMA-ASD tables 3 times each, not once; orchestrator exposure undeclared | fixed: §0.2 and §5 restricted to the author and reviser; counts corrected (§9); orchestrator declaration a freeze precondition (§18, F2) |
| S1-C1 | C | FreeSurfer tarball feasibility unverified | fixed: probed 2026-10-01 (HTTP 200, 9,484,461,482 bytes, resumable) and pinned (R16) |
| S1-C2 | C | R12 conventions unlabelled; R22's PANTHER sidedness unchecked and GAF reference; Hansen under Level 4 | fixed: R12 labelled "convention (pre-exposure)"; R22 computes both sidednesses with a pre-WP3 rule (PANTHER's page returned 403) and runs `PTHR16.0_human` beside; Hansen dropped from Level 4 (R25) |
| S1-C3 | C | five small items: g1_open routes; Giacomel's claim_form; MANIFEST_claims deviation; AHBA well ids; U_stat after dropna | fixed: routes stated (§2.2); dispatch by status (§4); deviation declared (R26); well ids never printed (R10, §8); U_stat counted after the `Universe` rule (R10) |
| S2-A1 | A | no plant can catch a liberal species or site leg in the new adapters; P4 is masked by the site leg | fixed: P24 (species leg on aligned maps), P25 (planted flawed legs that must be caught), P26 (site legs and a planted permutation leg); P4's scope stated. T_abs part rebutted (§19) |
| S2-A2 | A | P3 unattainable for a correct runner (≈ .15 in all three classes); "fixed in code" pushes towards liberal p's; P12 and the form-level P3 runs without basis | fixed as S1-B8; P6 and P12 thresholds set so that a correct runner fails with probability ≤ .01; P8 made exact; a statistical failure is not presumed a code defect, and code changes only for a defect a written diagnosis names (§7, §17) |
| S2-A3 | A | step 3 vs step 4; Moreau's 64 × 64 claim sheets are W with no declared columns; xlrd loads every sheet | fixed: declared sheets only; Moreau column rule pinned; xlrd `on_demand=True` (§8); P20 |
| S2-A4 | A | sheet names, zip members, paths and exception text unscreened (a GUID was printed this way before) | fixed: `screen()` on every carrier-derived string; exception handler prints class, stage and code line only (§8); P20. Tightened in v3.1: no carrier-derived string is printed or written at all (V3-B2) |
| S2-B1 | B | L8 / L9 CRLF hashes cannot pass in the worktree | fixed as S1-B3 |
| S2-B2 | B | z-scoring would change set-vs-map T and Level 0 | fixed as S1-A2 |
| S2-B3 | B | no plants for decoded-list on V-DK (Rasero's conditional class) | fixed: V-DK added to P4, P5, P6, P11 and P24–P26 (§7, §12) |
| S2-B4 | B | downloads and `carrier_test.py` ran with no gate check | fixed: the wrapper's step 0 and the gate launcher (§2.2, §8); P21 |
| S2-B5 | B | `g1_open()` could not tell an operator-opened session from a continuation; did not check that c introduces the block or that nothing supersedes it | fixed: attestation lines, c^ check, supersession check, stated as necessary not sufficient (§2.2); P21 |
| S2-B6 | B | code fixes and plan amendments allowed after results are seen | fixed: post-result code changes rerun plants, re-review and rerun affected rows (§17); post-result amendments labelled post-exposure, all gates, re-reviewed (§18) |
| S2-B7 | B | participant-level carrier kept on disk without bound | fixed in part: immediate quarantine, refusal by both lanes, immediate deletion request (§8 step 6). Deletion by the wrapper or a worker is not adopted; the deletion is an operator-authorised step (§8 step 6, §19; v3 reasons: RC-C2) |
| S2-B8 | B | exposure record wrong (3 opens each, not one) and deferred too late; the lane opened the sibling-disorder tables behind Level 4 | fixed as S1-B9; A4 post-exposure condition (R25, §9). The count of disorder tables refined (§19) |
| S2-C1 | C | sub-legs' common direction and which p enters BH unstated | fixed: one d for every sub-leg; the conjunction p of R1 enters BH (R1, R29). The sign-of-T variant not adopted (§19) |
| S2-C2 | C | dk-ctx G6l underpriced; memory unbudgeted; multiverse uncapped | fixed: measured screen times, chunked refits ≤ 2.5 GB per job, capped multiverse batches (§4, §14) |
| S2-C3 | C | BUCH-E-SZ's G6s is computable | fixed (R8, §12) |
| S2-C4 | C | (b-ii) record could follow the G2 results | fixed: ordering precondition F6 (§18) |
| S2-C5 | C | FreeSurfer tarball unpinned; identical bytes from another artefact refused | fixed: tarball pinned; any official 7.4.1 artefact with the member's hash recorded is accepted (R16) |
| RC-C1 | C | R8 gave G2 two labels; the table, P10 and §12 relabelled the frozen "unmatched" as "not computable" | fixed: G2 (and G4, through G2's sampler) reads "unmatched" everywhere, as `prereg.md:140-142` gives it; "not computable (pool < m)" is kept for G1, G3m, J1 and the naive joint only (R8 reading and table, P10, §12) |
| RC-C2 | C | the §19 rebuttal "only the operator deletes data files" quoted nothing; the register records builder deletion under the v6.8 rule | fixed: the claim is dropped. §19 now quotes the register's practice (`claims_register.md:783`, `:819-820`, `:2293`; A1 `ARC.md:698-709`). Carrier deletion after extraction is an operator-authorised step, an orchestrator default under the delegation (default 24), declared with its reason: this session's permission system refused agent deletions (§8 step 6, §17, §19). The quarantine fix stands |
| RC-C3 | C | R28 re-fetches Gandal 2018 Table S1, a recorded deleted original, without saying so or asserting its bytes | fixed: R28 declares the reversal and its reason (the RLM covariates were not kept by the v6.8 reduction). It asserts 61,253,282 B and sha256 e6f9c6eb…ce72 at download, refusing on a mismatch, reduces to the declared columns, then quarantines and requests deletion in the same session (R28) |
| RC-C4 | C | Moreau's header-row finder ("exactly 64 non-empty texts") could not reach the `roi` form and refused a corner label | fixed: the header row is the first guard-zone row whose cells of any type hold all 64 identifiers of one form, with at most one corner cell in the row-label column; `roi` matches ints, integral floats and digit texts; post-read assertions kept (§8 step 4) |
| RC-C5 | C | R16 stopped the stream at the member yet recorded the tarball's sha256 | fixed: only the member's sha256 is recorded (it is the register's "sha256 recorded at download"), with "tarball sha256 not computed (stream stopped at the member)" (R16) |
| RC-C6 | C | P3b treated the frozen catch rates as exact; the predictive failure probability was .016 / .018 | fixed: thresholds from the beta-binomial predictive tail, V-AAL ≤ 52 and V-DK ≤ 44, with predictive tails .0064 / .0075 (scratch `…/scratchpad/runplan_v3/tails.py`, scipy 1.18.1); the re-check's suggestion of 51 / 43 was recomputed as asked (§7, P3b) |
| RC-C7 | C | P25 (and P26's flaw) borrowed set-vs-map rates for the new adapters; a failure with no defect would block the decoded-list and PLS claims | fixed: these are must-catch tests. A failure to catch with no defect named is reported as "plant regime insensitive for this form × class" and blocks nothing; the correct-leg tests (P24, P26's site leg, P25 (c)'s correct leg) keep the block. Declared before any run (§7, P25, P26, §17) |
| RC-C8 | C | the exposure declaration's list of G2-bearing readings left out R24, R9, R17 | fixed: the declaration covers every reading bearing on a G2 target. The ENIGMA-touching readings are listed: R1, R9, R11, R12, R13, R17, R24, R25, R27, R29, plus the general R2–R7 (§0.2, §9) |
| V3-B1 | B | F6 said "G2's maps are not ABIDE II-derived", against the register (`:72-73`) and the A1 ARC (`:574-576`): every ENIGMA-ASD map includes ABIDE II cohorts, so the ordering rule (`:104-105`) applies to G2's ENIGMA half | fixed: F6 now quotes both texts, states the ordering as a required precondition for the ENIGMA half (the LEAP maps are not ABIDE-derived), and records the check: no statistic of the audit's runner on a G2 target exists before 4fd7942ece3743d75741fa37c75212a9a6d2a520, or at all, at e49a024; the pre-freeze statistics are declared (register 'Seen before writing' item 2) (§18, F6; v3.1 review N-B1) |
| V3-B2 | B | two print rules for gated scripts: §8 allowed counts, paths, line numbers and hashes; P20 and the screening step also let screened sheet and member names be printed, against register §1.10 (2) "print nothing but counts and hashes" | fixed: one print rule (§8). Only counts, runner-built paths, line numbers, hashes and the runner's fixed labels are printed or written (identity records also carry the pinned URL, dates and the server's headers, as the register asks). Carrier-derived strings (sheet names, zip and tar member names, header and label cells, extracted file names) are never printed or written: they are compared in memory with the declared names and reported as pass / fail counts plus a sha256. Extracted content is written only as the needed object, keyed by runner-side names; saved files take runner-built names. Exception handlers print class, stage and code line only. The wrapper applies the rule to ungated carriers too. The register's "counts and hashes" reading is declared. P20's criterion is one criterion for every run: captured output holds no carrier string and parses against the allow-list. Step 3, step 5, R15, R16, R18 and §11 updated; v3's screen-before-print withdrawn, `screen()` kept in memory for counts and step 6 |
| V3-C1 | C | exposure details: 14:25:16 counted the lifespan table twice; the novelty and protocol judges' manifest reads missing; the judge's values stored in the workflow record; v1 was first written at 14:40:51, not "created 14:41:56" | fixed: 20 records (19 CortThick-named files incl. the lifespan table, and the folder); who read the manifest table, and when; who saw which values; the workflow record and the run's transcripts named exposure-bearing and barred to audit, plan and A4 agents (§9, R25, §6 A4); 14:40:51 in the header, §0.2, §0.4, §5 and §9; the corrections go into F2's ARC line (§9, §18) |
| V3-C2 | C | the A1 ARC (e49a024) states the first review as "fidelity 2 A / 7 B / 3 C" | recorded: it is 2 A / 9 B / 3 C; the orchestrator corrects the ARC (§15 above) |
| V3-C3 | C | Moreau's header search read the zone outside the frozen guard; label and name matched only in exact case although MIST64 labels are mixed case | fixed: the wrapper loops `header_row` 0–19 through `read_openpyxl`; the column rule returns [] unless the row qualifies, and the guard's `Refused` is caught by the §8 handler; label and name match case-insensitively (casefolded forms stay distinct, counted) (§8 step 4) |
| V3-C4 | C | R8's "feasible on every leg" did not check G5's pool; G5 cited as prereg `:147` | fixed: pools large enough on G1, G2, G4, G3m, G6l and the J1 / naive draws; G5 pools are checked when built, the frozen "not applicable" applying automatically if < 2m; citation `:148` (R8). Noticed while fixing it: Level-2 G3 needs G4's pool, so it reads "not computable (pool < m)" on every row of R8's table, which v3 left unstated (R8, P10, §12) |
| V3-C5 | C | streaming the tar member: a hard-link or symlink member cannot be resolved in stream mode, and the plan did not say what happens | fixed in v3.1, then superseded by N-C2 below (a link member is resolved by a second pass). v3.1's text: the member must be a regular file; a non-regular member is refused, never resolved, recorded by type and path sha256, and the Leyhausen cells read "not auditable" (R16) |
| V3-C6 | C | `g1_open()` caught a supersession marker only at a line start; its lower time bound used the ARC NOTICE commit only, while the register's notice is the ARC entry and the session message (1a8e46e) | fixed: markers match anywhere in a normalised line; the lower bound is the later of the NOTICE commit and the session-message commit (found by its own walk). Re-simulated: True on the real record; P21 35 / 35 (3 open, 32 refused), the 7 new cases opened under v3's spec (§2.2) |
| N-B1 | B | F6 claimed no G2 audit statistic exists 'at all', against A1's pre-freeze R2 on Giacomel and the asdg-lit Liu recomputation (register 'Seen before writing' item 2) | fixed: F6's check scoped to this audit's runner; the two pre-freeze statistics declared with their register citation (§18) |
| N-C1 | C | the MAMAT-E-Tissue bullet's 'every other leg is computed' ignored G5's unchecked pool (2m = 2,786) | fixed: computed only if the pool check passes; else the frozen 'not applicable' (§12) |
| N-C2 | C | R16 refused tar link members outright although a second streaming pass can resolve them | fixed: a link to a regular member is resolved by a second pass and recorded; only unresolvable links and other non-regular members are refused (R16) |
| PF-B1 | B | pre-freeze check: N-B1 left the V3-B1 row and F6's precondition / conclusion unscoped | fixed: 'gated (post-freeze; `claims_register.md:116`)' at both places; V3-B1 row restated (§15, §18) |
| PF-B2 | B | pre-freeze check: P20 still expected every tar link member to be refused, against R16 as amended | fixed: P20 plants both the resolution path and the refusals (§7 P20) |
| PF-C1 | C | pre-freeze check: N-B1's parenthesis cited items 2-3 and attributed the asdg-lit recomputation to A1 | fixed: item 2 (`claims_register.md:128-132`), attribution corrected (§18) |
| PF-C2 | C | pre-freeze check: §15 lacked the v3.1 re-check rows; V3-C5 row stale; header / sign-off silent on the re-check | fixed: rows N-* and PF-* added; V3-C5 marked superseded; sign-off updated |

## 16. Results and reporting
- **Per cell** (`arcs/audit/results/a1_run/<gate>/cells.jsonl`, plus `.md`):
  - every registered cell, computed or not, with its TSV status and every flag;
  - T; each leg's one-sided p(+) and p(−), the claim's d*, each leg's reported p = 2·p(d*) and the literal per-leg 2·min
    beside it (R1); the conjunction p and its BH q (R29);
  - the ≥ 2-donor sensitivity beside the primary (R11);
  - floors and statuses; descriptor legs;
  - the reproduction check or descriptive comparison;
  - amendment 5 labels and power columns (R27);
  - m, f/m, c_S, R²_grad, R²_|x|;
  - seeds, inputs and commit.

  Non-ASD outcomes and not-ASD claims are reported apart. The secondary view (m′ 223) is reported beside m 207 and never
  in it (`:1831-1838`).
- **Headline:** the frozen-11 survival fraction over the population (`:227-262`). Every statement of it carries, in the
  same sentence:
  - the curves (C-sp .970; C-gene .585–.666; C-align .018–.074 / .060–.196 / .106–.352);
  - gates 1–11 "failed as gates under amendment 3" (`prereg_amend_5.md:96-97`);
  - the number of survivals reading "calibrated evidence", and per scope label;
  - the composition by §1.8 precedence, with the component × not-auditable cross-tab and the provisional (S conditional)
    rows, and A6's outcome for MAMAT-E-Tissue-URG / -DRG (§6);
  - the tested-only fraction.

  A low fraction is worded "few published claims are detectable by a calibrated test at this power", never "few are
  true". The forbidden words for non-survivals are "refuted", "fails", "does not replicate" and "not supported"
  (`prereg_amend_5.md:148-149`).
- **Interim** until every gate's claims have run (`:256-262`):
  - after the ungated rows: 0 of 14 units can survive (all 14 are not testable as stated, not auditable, or no calibrated
    test; `:1870-1873`);
  - after G2: ≤ 18 units;
  - G1's 196 units are listed apart and counted neither way; Dear and Vairam / Roy are listed apart;
  - the < 5 outcomes of gated sets are reported, and the population is restated.
- **Registered descriptors:** the per-row focal view (`:1931-1945`); per-target "any survives"; the added nine and their
  union; the verdict table stratified by inference level; BH q-values (descriptive, `prereg_amend_3.md:76-78`; family:
  R29).
- **Files:**
  - per-gate JSON/MD;
  - `results/MANIFEST_claims.md`, the claim × level × null × parcellation × multiverse factorial with status (R26; a
    declared file-name deviation from prereg §7);
  - the A1 ARC entry, and the A3 ARC exposure record (§9).
- **Every number** names its script, input and commit.

## 17. Stop rules and incidents
- **Launch assertion fails** (L1–L15): no run, and the cause is reported.
- **Identity mismatch at download or use:** the cell reads "not auditable (map changed)" (`:1090`). The run continues for
  other cells.
- **A crash** is fixed in code, and that row and leg rerun from the checkpoint. A crash never changes a rule.
- **Any code change on a statistic path once a claim result exists** (a crash fix included; second review, B6):
  1. P0–P26 are rerun;
  2. asdg-skeptic re-reviews before any further claim runs;
  3. every completed row whose computation passes through the changed code is rerun;
  4. both versions are reported, with the change, its commit and its reason.
- **A plant fails** (no claim runs until it is resolved):
  - functional: a code defect, with a written diagnosis, the fix, all plants rerun and the skeptic's re-check;
  - statistical (thresholds set from `e3_gates_a3.md`, amendment 5 §3 or a gate cap, §7): a written diagnosis and the
    skeptic's review before anything is changed or rerun; code is changed only for a defect the diagnosis names. If no
    defect is found:
    - a **correct-leg test** (P3b, P4, P6, P12, P24, P26's site-leg test, P25 (c)'s correct leg): the claims of that
      form × class do not run until a frozen amendment says how they are read, and the test itself is not changed ("The
      test is not changed a third time after its behaviour was seen", `prereg_amend_5.md:103-104`);
    - a **must-catch test** (P25's flawed legs, P26's planted permutation leg): reported as "plant regime insensitive for
      this form × class", beside every claim of that form × class, and those claims run. This consequence is fixed here
      before any plant has run (re-check, C7);
  - a rate reported without a threshold never triggers a code change;
  - no plant's threshold, n or construction is changed after its result is seen.
- **A rule turns out not to apply as written:** "not auditable (definition not applicable: <why>)" and a §6 entry. No
  redefinition.
- **Privacy incident:** §8.
- **The G1 check fails:** G1 scripts and downloads refuse.
- **K1:** amendment 5 re-arms K1 on any re-evaluation of the gates (`prereg_amend_5.md:274-275`). This plan runs none.
  If a gate file's blob or LF hash differs from L8 / L9, the run stops and the orchestrator decides; the file is never
  regenerated to make it match.
- **Compute overrun:** §14.
- **Deletions and removals:** neither the wrapper nor a worker deletes a data file, carrier or workbook, or removes a
  worktree (§2.3, §8). A carrier's deletion after verified extraction is requested in the same session and carried out
  as an operator-authorised step (§8 step 6; default 24).

## 18. Order of work, review and sign-off
| WP | content | gate material | precondition |
|---|---|---|---|
| WP0 | this plan → two asdg-skeptic reviews (2026-10-01) → v2 → re-check (0 A / 0 B / 8 C) → v3 (the 8 C answered; record commit, exposure facts, `g1_open()` simulated) → review of v3 (0 A / 2 B / 6 C) → v3.1 (all eight answered; `g1_open()` re-simulated) → F1–F3 → `bench.py freeze RUN_PLAN.md` (orchestrator) | none | — |
| WP1 | `a1_audit` runner core: loader, seeds, gate checks and launcher, adapters, ported helpers + P0–P2 | none | WP0 frozen |
| WP2 | plants P3–P26 for every gate incl. G1's; bicor (R13) with WGCNA via Docker if built; R image built (R17) on synthetic data; `venv_ref` builds (R11 incl. sample counts, R12 per-donor V-DK, R14, R10); PANTHER sidedness read (R22) | none | WP1 |
| WP2r | asdg-skeptic review of runner and plants (register §1.10 (3)) | none | WP2 |
| WP3 | ungated material (identity, decoder fetch, re-parcellation, Moreau's declared-sheet read) → verdict pass → descriptor pass | ungated | WP2r; F5 |
| WP4 | G2 downloads (FreeSurfer first), identity, extraction, gated sets, manifests → verdict pass (interim headline) → descriptor pass → A3 ARC exposure record | G2 | WP2r; §2.1; F5; F6 |
| WP5 | G1 carrier tests, source-1 runs, extraction, family counts → verdict pass → descriptor pass → A3 ARC record | G1 | WP2r; `g1_open()`; F4 |
| WP6 | survivors' multiverse (R11, in capped batches, §14); final headline; closeout inputs | — | WP3–WP5 |

**Freeze preconditions (WP0).**
- **F1:** no A or B finding is open. The re-check of v2 returned "verified-with-residues" (0 A / 0 B / 8 C), and v3
  answered the 8 C points. The review of v3 returned "not-verified" (0 A / 2 B / 6 C); v3.1 answers both B findings
  and the six C points (§15, rows V3-B1 … V3-C6).
- **F2:** the exposure listing and the orchestrator's own exposure declaration are written into the A1 ARC, beside the
  G2-bearing readings (both reviews; re-check, C8).
  - **Facts recorded:** in e49a024, in both ARCs. The A1 entry states the facts and that the orchestrator printed the
    commands, not their output.
  - **Declaration:** in §9 of this plan. It covers every reading bearing on a G2 target, names the ENIGMA-touching ones,
    and states that all of them were written after the exposure and none uses the lane's values.
  - **To do at freeze:** the orchestrator adds one A1 ARC line naming those readings and citing §9. The line carries
    v3.1's corrections of the e49a024 facts: 20 log records at 14:25:16 (19 CortThick-named files including the lifespan
    table, and the folder); the novelty and protocol judges' manifest reads; the workflow record `wf_a992ecba-de5.json`
    and that run's agent transcripts named exposure-bearing and barred to audit, plan and A4 agents; v1 first written at
    14:40:51. The orchestrator also corrects the first review's count in the same ARC (§15).
- **F3:** the orchestrator records which route it takes for R24 (the G3 seed reading, or amendment A3).

**Preconditions before gated material.**
- **F4 (before any G1 material is opened):** A6 decided (§6): commissioned and frozen, or the composition change accepted
  and recorded.
- **F5 (before the first extraction of any gate):** `E:\data\asdg\_quarantine\` is on the exploration lane's refusal list
  (§8 step 6).
- **F6 (ordering; second review, C4; corrected in v3.1, review of v3, B1; met):** A3's "(b-ii) declined" record (or
  another A3 route's record) is committed before any gated (post-freeze; `claims_register.md:116`) G2 audit
  statistic exists.
  - **Why it is required.** The register's rule is that "no A3 ABIDE II decision may remain downstream of the audit's
    exposure to ABIDE II-derived maps" (`claims_register.md:104-105`). G2's ENIGMA-ASD maps are ABIDE II-derived:
    - the A1 ARC: "**Every ENIGMA-ASD map includes ABIDE II cohorts.** van Rooij 2018 pools 16 ABIDE and 17 ABIDE-II
      cohorts of 49, and Patel 2021's own meta-analysis lists ABIDE2. By amendment 4 §0's rule ("maps derived from
      ABIDE II or HBN"), Patel, Giacomel, Hansen and Liu T3 are sealed" (A1 `ARC.md:574-576`);
    - the register: "Amendment 4 §0 defers 'maps derived from ABIDE II or HBN' …; the register pass extended the
      deferral to the ENIGMA-ASD maps" (`claims_register.md:72-73`).

    So for the ENIGMA half of G2 (Patel, Giacomel, Hansen, Liu T3) the ordering is required, not a declaration. The
    LEAP maps (Pretzsch, Leyhausen; "T2 / EU-AIMS LEAP", `claims_register.md:108-109`) are not ABIDE-derived. v3 said
    "G2's maps are not ABIDE II-derived, so this precondition was a declaration, not a block"; that was false and is
    withdrawn.
  - **Met.** The record was committed in 4fd7942ece3743d75741fa37c75212a9a6d2a520 (2026-10-01T16:10:42+02:00).
  - **Checked for v3.1 (2026-10-01, HEAD e49a024): no statistic of this audit's runner on a G2 target exists
    before 4fd7942ece3743d75741fa37c75212a9a6d2a520, nor at all.** (Two statistics on G2 targets' maps
    predate the register's freeze: A1's R2 on Giacomel's ASD combined cortical cells
    (`arcs/audit/results/e4_r2_giacomel.json`) and the asdg-lit recomputation in
    `literature/notes/liu2026spatiotemporal.md`. Both are declared in the register's 'Seen before writing' item 2
    (`claims_register.md:128-132`) and precede both the freeze and 4fd7942; v3.1 review N-B1, pre-freeze check C1.) Neither the A1 runner (`arcs/audit/src/a1_audit/`), nor a
    run output (`arcs/audit/results/a1_run/`), nor a post-freeze manifest (`register_maps/post_freeze/`,
    `register_sets/post_freeze/`) exists in the working tree or in any commit of the history. The only commits under
    `arcs/audit/` since the register froze (3d1abe3) are deaedb0 and e49a024, and neither touches `arcs/audit/results/`.
    The first G2 statistic of this audit can exist only after WP1–WP2r, so every gated (post-freeze; `claims_register.md:116`) G2 audit statistic will be
    downstream of 4fd7942.
  - **The lane's earlier look** at the ENIGMA-ASD tables (14:25–14:30, §9) is not this audit's exposure and computed no
    claim statistic (§0.2, §9). The decision 4fd7942 records had been announced before it: in the session-9 NOTICE
    (6b855c9, 2026-09-29) and the session-9 handoff (1a8e46e, 2026-09-30).

**Sign-off.** Before this audit opened any gated material, this plan was reviewed twice by asdg-skeptic, v2 was
re-checked (0 A / 0 B / 8 C), and v3 was reviewed (0 A / 2 B / 6 C). v3 answered the re-check's C points; v3.1 answers
the review of v3; v3.1 was re-checked (0 A / 1 B / 2 C) and a pre-freeze check of those three edits followed
(0 A / 2 B / 2 C); both are answered in §15 (rows N-* and PF-*). The orchestrator then freezes v3.1 (`bench.py freeze`; L5) and logs it as decided under the standing
delegation. The runner and plants get a further asdg-skeptic review before any claim runs (WP2r).
- Readings found missing later go to a frozen amendment of this plan (`RUN_PLAN_amend_<n>.md`).
- **Before any claim result exists**, such an amendment is pre-exposure for the material it bears on, provided that
  material is not yet opened.
- **After the first claim result exists** (second review, B6), an amendment is labelled post-exposure. It applies to the
  cells of every gate it bears on, already-run cells included (rerun under both versions, both reported), and is reviewed
  by asdg-skeptic before it is frozen.
- A reading that could only apply to material already opened reads "not auditable (definition not applicable)" instead.

## 19. Review answers (the parts of findings not adopted, each with the frozen text it rests on)
- **S2-A1, the T_abs part (plants for T_abs legs):** not adopted. T_abs is registered as uncalibrated and can never yield
  a survival: "Labelled 'unsigned descriptor, uncalibrated (no plant for |r|; |r| favours smooth, brain-enriched
  genes)'; its results are reported as values and p's, never as 'detects' or 'survives'" (`claims_register.md:311-313`).
  P11 (values equal direct computation) stays its only plant.
- **S2-B7, "cite the frozen register as the authorisation and delete":** not adopted as stated; v3 restates the reason
  (re-check, C2).
  - **What the register says.** It requires the deletion: a carrier "has only the needed group-level object extracted
    once, then is deleted" (`claims_register.md:1096-1097`). It does not say who deletes.
  - **The register's own practice was builder deletion.** The §1.6 table lists the identifier-bearing originals as
    "original (deleted; v6.8 unless marked v6.9 …)" (`:783`). The §1.6 rule states "a sheet with identifier headers is
    deleted with its file without display" (`:819-820`). Round 2 records "the eight originals deleted" (`:2293`). The
    audit ARC records workers that "then deleted the files", and the rule "delete identifier-bearing sheets without
    display" (A1 `ARC.md:698-709`). Only the deletion of Pretzsch's public LEAP supplement was an operator decision
    (A1 `ARC.md:586`).
  - **Withdrawn.** v2's ground, "in this programme only the operator deletes data files", quoted nothing and runs against
    that record.
  - **v3's ground.** For this audit the deletion is an operator-authorised step: an orchestrator default under the
    standing delegation (default 24, §8 step 6), stricter than the register's practice and declared as such. The reason:
    in this session (2026-10-01, the orchestrator's record) the permission system refused agent deletions. A data-file
    deletion therefore needs the operator's authorisation in any case, and the plan makes that the rule rather than an
    accident.
  - **What stands.** The plan still quarantines the carrier right after verified extraction and requests the deletion in
    the same session (§8 step 6). The re-check judged that sufficient.
- **S2-C1, d* = the sign of the observed T:** not adopted. "the test is two-sided (p = 2·min of the one-sided p's)"
  (`prereg.md:184-185`) names a minimum, not the sign of T. R1 applies that minimum to the claim's conjunction p, which is
  S1-B2's fix. The two rules agree whenever the observed sign minimises the conjunction.
- **S1-A1, "record the name and at most the dimension tag" of an undeclared sheet:** the stricter S2-A3 is adopted (no
  dimension either), because openpyxl reads a sheet's dimension from that sheet's own part. Since v3.1 the name itself
  is not recorded either, only its sha256 (§8's print rule; review of v3, B2).
- **S2-B8, "the 19 disorder CortThick tables":** the finding stands; only the count is refined. The log holds 19
  distinct ENIGMA Toolbox CortThick file names: 2 ASD tables, 16 other disorders' case-control tables and one lifespan
  normative table (masked tabulation, §9).
