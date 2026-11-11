"""Fetch-and-extract wrapper (arcs/audit/RUN_PLAN.md v3.1, FROZEN sha256 16c60232...: section 8 steps 0-6, the
section 2.2 gate-launcher paragraph, R16, R18; plants P19 / P20 / P21 in tests/test_material_p18_p19_p20.py).

    python -X utf8 -m a1_audit.fetch_extract --targets <targets.json> [--only KEY ...] [--repo PATH]
        [--data-root E:\\data\\asdg] [--records-root <repo>/arcs/audit/register_maps/post_freeze]
        [--artifacts-root <repo>/artifacts/audit/extracted] [--logs-root <repo>/artifacts/audit/material_logs]
        [--control-root <repo>/arcs/audit/run_manifests/material] [--quarantine-root E:\\data\\asdg\\_quarantine]

It never prints a cell and never deletes. Per target, in order:
  0 gate: before any network request or file open, the target's gate check (G2: gates.require_step3v_open, G1:
    gates.require_g1_open; ungated targets pass). Closed -> one refusal line, no request, nothing opened (P21).
    A carrier already moved to the quarantine folder is refused (re-extraction needs the operator).
  1 fetch with the frozen src_register/fetch_util.get (sha256-pinned and loaded from its verified bytes; it sends no
    identifier) into <data>/<key>/carrier<ext> (a runner-built name; via a .part file that is renamed, never
    deleted), after an HTTP HEAD that keeps only Content-Length, Last-Modified and a plain-MD5 ETag. SOURCE.md
    (URL, date, bytes, sha256, those headers) is appended beside the file. A copy already on disk is not fetched.
  2 identity: the R13 fields (identity.py) against the pre-freeze references and the pinned size / sha256;
    "not auditable (map changed)" stops the target. The R18 record goes to <records>/<gate>/<key>.json.
  3 workbooks, declared sheets only: names from wb.sheetnames (openpyxl read-only) or book.sheet_names() (xlrd,
    on_demand=True), compared in memory, screened (privacy_wrap.screen), recorded as sha256 only. A declared sheet on
    the target's do-not-open list is refused before the workbook is opened. Each declared sheet is fetched through
    one accessor that appends to an access log, classified with the frozen classify_openpyxl / classify_xlrd, and its
    dimensions recorded; an undeclared sheet is never fetched. Afterwards the access log is asserted to hold declared
    sheets only, the openpyxl package parts opened are asserted to include no undeclared worksheet part, and xlrd's
    sheet_loaded() is asserted False for every undeclared sheet.
  4 read: declared columns through privacy_guard.read_openpyxl / xlrd_cell_reader (exact header texts in a stated
    header row), or Moreau's MIST64 matrix through the header-row search (h = 0 ... 19, the column rule of section 8
    step 4) and the post-read block assertions.
  5 save: the group-level object (runner-side keys + declared cells' values) to <artifacts>/<gate>/<key>/
    <key>_extract.json, sha256, verified by read-back without printing.
  6 quarantine: a carrier with an identifier-bearing declared sheet, a screen hit on any name, or a known
    per-participant supplement is moved (same volume, os.rename, sha256 re-checked) to <quarantine>/<gate>/<key>/,
    with every extracted member that is itself identifier-bearing; a deletion request record is written at once to
    <control>/<gate>/<key>_deletion_request.json and said; the deletion is the operator's step.
  Zip carriers: members listed in memory, declared members (exact name or suffix) extracted under runner-built names
  (<key>_member<index><ext> or the declared name), undeclared members never read (asserted on the zip's opens).
  Tar streams (R16): read in order until the declared member; a link member is resolved by a second pass when its
  target is a regular member inside the archive; an unresolvable link, a link chain or any other non-regular member is
  refused; only the member is written; "tarball sha256 not computed (stream stopped at the member)".

Every line, record, SOURCE.md and saved file name goes through privacy_wrap.Emitter (the section 8 allow-list);
every carrier-touching stage runs inside privacy_wrap.stage (class name, stage label, file:line only); library
stdio, warnings and log records are guarded / counted (privacy_wrap.StdioGuard, quiet_warnings, quiet_logging).

Readings where section 8 leaves a corner open (fail closed; listed in the WP2 report):
  FE1 openpyxl 3.1.5's read-only load_workbook parses EVERY worksheet part up to its <dimension> element (and the
      whole <sheetData> when the element is absent), and reads each sheet's _rels part and every chartsheet: contrary
      to section 8 step 3's premise. The wrapper loads under _lazy_openpyxl(): ReadOnlyWorksheet._get_size is deferred
      to the accessor (declared sheets only), the sheet _rels parts (unused in read-only mode) and chartsheets are
      skipped, and every package part opened is recorded in memory. openpyxl's version is asserted (3.1.5).
  FE2 workbook-level parts are still read whole by openpyxl / xlrd: the shared-string table (it holds the text of
      every sheet), the workbook part, styles and document properties (creator names). They stay in memory and
      nothing of them is printed or written (declared residual).
  FE3 the "raising code line" is the innermost frame in the runner's own modules or the frozen guard / fetch helper.
  FE4 a declared numeric column: None / '' -> null; bool, non-finite or non-numeric text -> ValueError (refusal).
  FE5 rows of a declared-columns read: the rows after the header row whose declared cells are not all empty.
  FE6 Moreau: the 64 rows immediately after the header row form the block; further non-empty declared cells below
      are counted, not read; a whitespace-only cell is empty; a "text of digits" is ASCII digits after stripping.
  FE7 a copy on disk without a pinned / pre-freeze sha256 or size reference: identity not established -> refused.
  FE8 a .part file left by an earlier download -> refused (never overwritten: overwriting would delete).
  FE9 an existing record / saved file is never overwritten: the record takes the next free <key>.<n>.json name.
  FE10 deletion requests go to <control>/<gate>/ (R18 names run-control folders launch/, G1/, plants/ only).
  FE11 the R16 stream screens the member path strings it streams through (counts only); the tarball is not stored, so
      a screen hit (e.g. BARE_SUBJECT on a "subjects" path component) quarantines nothing and is recorded.
  FE12 an identifier-bearing carrier whose extraction is refused is not quarantined (step 6 runs "right after its
      extraction is verified"); it stays under <data>/<key>/ with its record (rule letters, screen counts).
  FE13 the frozen guard's classify / id_value_hits read the pinned HGNC table under E:/data/asdg/explore_public
      (sha256 asserted by the guard) whenever a CODE-shaped token occurs: a production read of public reference data
      under the data root; the WP2 tests preset the guard's cache and never reach it.
  FE14 the carrier's local name is runner-built (<data>/<key>/carrier<ext>); copies made before the freeze under other
      names are not picked up (WP3 / WP4 choose: download again, or pin the existing path in the target).
WP3 phase 1 (additions; the plan's steps and the print rule unchanged):
  FE15 Target.local_path pins an existing copy (WP3: the path IDENTITY_prefreeze.json's "local file" probe names): it is
      used as found (no download, no SOURCE.md written), recorded by the sha256 of its path string only (the path is
      never printed or written), and a quarantine move gives it the runner-built name carrier<ext>.
  FE16 run_target(reader=fn) reads a "file" target's carrier in the masked stage "read:file" (fn(path) -> objects, saved
      by step 5 like a workbook's); run_target(transform=fn) maps a workbook's declared-cell objects in the masked stage
      "transform" before step 5 (WP3: SD7's labels normalised in memory, never saved as strings).
  FE18 (WP3 fix round 1, B2) run_target(adopt_identical=True) (the WP3 stage only): save_object adopts an identical
      existing object (re-runs are idempotent), never overwrites a different one; the default keeps FE9's refusal.
  FE17 (WP3 fix round 1, B3; RUN_PLAN section 8 :1292-1295 "every ... carrier-derived path component") a pinned copy's
      path components below the data root are screened in memory (privacy_wrap.screen; counts only); a hit makes the
      carrier identifier-bearing for step 6.
RUN_PLAN_amend_3.md v2.1 (FROZEN, sha256 da3f3b8b...; WP3 fix round 2):
  FE19 (R45 (f), Changed 6) Target.part_name: a runner-built per-attempt .part name (carrier.json.a<k>.part); FE8's
      refusal applies to that name. A GET failure is classified in memory into rec["fetch_failure"]: the class name and
      the curl exit code (CalledProcessError.returncode) or the HTTP status code (parsed from fetch_util's "HTTP <code>
      for <url>") or html = True; no message text is stored.
  FE20 (R46, Changed 1, 2, 9) SheetDecl(mode="sd7"): the sheet declared by a name rule (name_rule, a regex on the name
      casefolded with every non-alphanumeric character removed; exactly one match, else name_status); the header row
      by the ASD-anchored column rule through the guard's read_openpyxl (h = 0 ... 19); the label block (empty rows
      skipped, one contiguous block, the interrupted-block check through R42 (d)'s normaliser; vocab: the DK names);
      a wrapper-side mask hands the transform the declared positions only (wp3_sd7.PositionView, also on a clean
      sheet); pass 2 reads the ASD column with the missing-value tokens; the positions each transform consumes are
      logged in the record and must equal the positions handed over (stage "transform:positions").
  FE21 (R46 (h), Changed 10) Target.defer_quarantine: step 6 is not run by this target (SD7's pass 1); the record says
      so; the last pass runs it once.
  FE22 (section 8.1, Changed 5, 11) Target.quarantine_dir: step 6 moves that whole directory (the Moreau clone; same
      volume; the carrier's sha256 re-checked inside it; its file names kept, never printed); deletion_extra adds the
      section 8.1 request content (fixed texts).
  FE23 (fix round 3, C (a), (e)) Target.head_before_get=False: no HEAD of the target URL (R45 (a): the decoder is one
      GET; the image file URL's size probe is wp3_decoder's); Target.url_note: a fixed note beside the URL field.
  FE24 (fix round 3, B1) run_step6: step 6 run once, after the last pass attempted, for a pinned copy whose earlier
      pass verified its extraction and deferred step 6 (FE21).
WP4 phase 1 (G2; the DRAFT RUN_PLAN_amend_4.md):
  FE25 SheetDecl(mode="labelled"): a labelled table declared by exact header texts (Giacomel's sheets: 'ASD', 'MDD';
      R54) - the header row by labelled_rule through the guard (h = 0 ... 19), the label block at position 0
      (wp3_sd7.label_block), a wrapper-side mask (PositionView) handing the transform position 0 and the declared
      positions only; the transform normalises the labels in memory (wp4_read) and saves DK-keyed values only.
  FE26 SheetDecl(mode="columns_search"): declared exact headers (and an ordered list of alternatives for one more
      column, `vocab`) found by a header-row search through the guard; the rows after it with a declared cell; a
      wrapper-side mask of the declared positions (the Sadeghi DEG workbook: R57 / R58 (f), draft).
"""
from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as _dt
import hashlib
import json
import math
import os
import posixpath
import re
import subprocess
import sys
import tarfile
import types
import zipfile
from pathlib import Path

from a1_audit import gates
from a1_audit import identity as ID
from a1_audit import privacy_wrap as PW
from a1_audit import reparcel as RP
from a1_audit import wp3_sd7 as SD7

REPO = Path(__file__).resolve().parents[4]

# ----------------------------------------------------------------------------------------------------------------
# the frozen helpers, loaded from their sha256-verified bytes (never copied, never edited)
# ----------------------------------------------------------------------------------------------------------------
GUARD_REL = "arcs/audit/src_register/privacy_guard.py"
GUARD_SHA256 = "430f86dc087ee47d3e673ba280a6a54dbf79c59fe2b006eb9e283ffe7602a366"       # freeze manifest; launch L12
FETCH_UTIL_REL = "arcs/audit/src_register/fetch_util.py"
FETCH_UTIL_SHA256 = "19cb3453fcfd878be6411d77fd4bc1b4c63248e59fdc02ac7c961f619af91498"  # freeze manifest
MIST64_REL = "arcs/audit/register_maps/mist64_classes.json"
MIST64_SHA256 = "c8310585b471944e5fbe1f6fd9d789864fdf5fa4639df824564a77f5a034885a"      # freeze manifest
OPENPYXL_VERSION = "3.1.5"


def _load_frozen(rel: str, sha256: str, modname: str) -> types.ModuleType:
    """Execute the frozen file's verified bytes (LF-normalised sha256 == pin) as a module; code objects carry the
    real path, so a raising line reads '<basename>:<line>'."""
    path = REPO / rel
    lf = path.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(lf).hexdigest() != sha256:
        raise ImportError("frozen helper differs from its pin")
    mod = types.ModuleType(modname)
    mod.__file__ = str(path)
    sys.modules[modname] = mod
    exec(compile(lf.decode("utf-8"), str(path), "exec"), mod.__dict__)
    return mod


PG = _load_frozen(GUARD_REL, GUARD_SHA256, "a1_audit._frozen_privacy_guard")
FU = _load_frozen(FETCH_UTIL_REL, FETCH_UTIL_SHA256, "a1_audit._frozen_fetch_util")

# ----------------------------------------------------------------------------------------------------------------
# pinned declarations of the plan
# ----------------------------------------------------------------------------------------------------------------
MOREAU_SHEETS = ("1_16p11.2Del", "3_22q11.2Del")                         # section 8 step 4 (second review, A3)
MOREAU_DO_NOT_OPEN = ("5_BIV", "6_ASD", "7_SZ", "8_ADHD", "9_Ranking")      # section 8 step 3
MOREAU_LAYOUT = "not auditable (definition not applicable: the declared Moreau sheet layout not matched)"
R16_URL = "https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/7.4.1/freesurfer-linux-ubuntu22_amd64-7.4.1.tar.gz"
R16_BYTES = 9484461482
R16_SUFFIX = "subjects/fsaverage/label/lh.aparc.annot"
R16_NAME = "lh.aparc.annot"
TARBALL_NOTE = "tarball sha256 not computed (stream stopped at the member)"
FIRST_NOTE = "the first member with the declared path ending is asserted (the stream stops there)"

STATUS_EXTRACTED = "extracted"
STATUS_IDENTITY_ONLY = "identity recorded (no extraction declared)"
STATUS_GATE = "refused (gate closed)"
STATUS_FAILED = "refused (stage failed)"
STATUS_DO_NOT_OPEN = "refused (do-not-open sheet declared)"
STATUS_IN_QUARANTINE = "refused (carrier in quarantine; the operator moves it back)"
STATUS_INCIDENT = "stopped (print-rule violation; ETHICS_PRIVACY incident)"
STATUS_STEP6 = "quarantined (section 8 step 6, run once after the last pass: RUN_PLAN_amend_3 R46 (h))"
HEAD_NOT_MADE = "not made (RUN_PLAN_amend_3 R45 (a): one GET)"

STAGES = ("run", "gate", "fetch:head", "fetch:get", "fetch:copy-on-disk", "source-md", "identity", "read:file", "transform",
          "sheets:do-not-open",
          "sheets:open", "sheets:names", "sheets:access", "sheets:classify", "read:declared-columns",
          "read:numeric-columns", "read:header-search", "read:moreau-layout", "read:sd7-block", "read:sd7-values",
          "transform:positions", "sheets:access-log", "zip:members",
          "zip:extract", "tar:head", "tar:stream", "tar:link", "save", "quarantine", "record")
RECORD_KEYS = (
    "schema key gate url kind status date_utc fetch source path file bytes sha256 server status_code content_length "
    "last_modified etag_md5 head_status identity facts references comparison result basis checks lf_conversion "
    "size_equal hash_equal git_blob git_blob_lf bytes_lf has_crlf md5 ref_bytes sheets n_sheets n_declared "
    "declared_found n_undeclared undeclared_not_fetched name_sha256 declared sheet_key rules n_rows n_cols "
    "n_cols_dimension_tag id_wording_cells bare_subject_headers id_value_hits_total identifier_bearing screen "
    "screen_hits access_log access_log_declared_only parts_opened_undeclared sheets_loaded_undeclared chartsheets "
    "skipped columns n_empty_rows header_row header_rows_tried form block_cells_numeric n_rows_after_block_nonempty "
    "members n_members n_dirs member_key member_index saved_path saved_sha256 undeclared_members_read extraction "
    "object_path object_sha256 quarantine quarantined moved_to deletion_request request_path failed_stage "
    "failed_class failed_where warnings logging xlrd_log_writes stdio_violations stdio_passed tar member_type "
    "member_path_sha256 link_target_path_sha256 resolved passes bytes_streamed declared_member names_streamed "
    "tarball_note first_note size_probe pinned pinned_bytes pinned_sha256 reason note register files "
    "operator_step refused_reason record_path saved stream_stopped workbooks note "
    "fetch_failure class curl_exit http_status html sheet_rule_matches positions_consumed positions_handed sd7_pass "
    "sd7_counts n_rows_skipped_before_block n_block_rows n_cells_after_block n_after_block_matching_dk "
    "n_after_block_dropped_kind n_missing_values deferred what carrier_sha256 carrier_bytes carrier_path_sha256 "
    "n_files_moved url_note head step6 reason content_type_label html page not an block_empty")
FE_PHRASES = (
    " ".join(STAGES), MOREAU_LAYOUT, TARBALL_NOTE, FIRST_NOTE, STATUS_EXTRACTED, STATUS_IDENTITY_ONLY, STATUS_GATE,
    STATUS_FAILED, STATUS_DO_NOT_OPEN, STATUS_IN_QUARANTINE, STATUS_INCIDENT, RECORD_KEYS,
    " ".join(gates.G1_REASONS), " ".join(gates.G2_REASONS),
    "fetch_extract no network request copy disk no download fetched headers available SOURCE carrier xlsx xls zip "
    "tar gz nii gii csv tsv txt json annot md pdf part tmp label mist64_matrix columns roi lh aparc mapping counts "
    "kept a1_post_freeze_identity_v1 a1_extract_v1 a1_deletion_request_v1 exact suffix workbook stream "
    "regular link hard symbolic other found not unresolvable chain absent outside target pass_1 pass_2 "
    "claims_register ARC default 24 deletion requested operator-authorised step section quarantined sha256 "
    "re-check pass fail moved files rule rules tries tried after found form block numeric x first stream stopped "
    "member members declared read not-read wrapper never deletes requested nothing quarantined screen hits "
    "streamed names deletion-request tar_member pinned copy path_sha256 local_path transform read:file components "
    "component screened screen_hits",
    "sheets selected by the declared name rule header row found after tries pass block rows cells positions handed "
    "the whole directory quarantined to files step 6 deferred to the last pass runs once RUN_PLAN_amend_3 R46 "
    "clone section 8.1 identifier-bearing (h) h",
    " ".join(SD7.STATUSES), STATUS_STEP6, HEAD_NOT_MADE,
    ID.PHRASES[0], ID.PHRASES[1], ID.PHRASES[2], ID.PHRASES[3], " ".join(ID.PHRASES[4:]),
    " ".join(RP.PHRASES[1:]))

_KEY_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)*")
_HTTP_DATE = re.compile(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun), \d{2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) "
                        r"\d{4} \d{2}:\d{2}:\d{2} GMT")


class DoNotOpen(Exception):
    """A declared sheet is on the target's do-not-open list (the declaration is refused before any open)."""


class LayoutRefused(Exception):
    """A declared layout (Moreau's MIST64 matrix, a declared member, a declared header row) was not matched."""


class MemberRefused(Exception):
    """A tar / zip member could not be taken as declared (R16: not a regular member, unresolvable link, ...)."""


class IdentityRefused(Exception):
    """Identity could not be established or did not match."""


class DownloadRefused(Exception):
    """A .part file is present, or the download did not return the pinned URL / the file it wrote."""


class QuarantineRefused(Exception):
    """A quarantine move could not be made as a same-volume rename, or its sha256 re-check failed."""


# ----------------------------------------------------------------------------------------------------------------
# declarations
# ----------------------------------------------------------------------------------------------------------------
@dataclasses.dataclass(frozen=True)
class Column:
    header: str            # exact header text (declared by the plan); never printed
    key: str               # runner-side name
    numeric: bool = False


@dataclasses.dataclass(frozen=True)
class SheetDecl:
    key: str               # runner-side key
    name: str              # declared sheet name (plan); never printed
    mode: str = "columns"  # "columns" | "mist64_matrix"
    header_row: int | None = None
    columns: tuple = ()
    vocab: tuple = ()      # mist64: ((roi, label, name), ...) from mist64_classes.json; sd7: the DK label names
    name_rule: str | None = None     # FE20: a regex on the normalised sheet name (exactly one match)
    name_status: str | None = None   # FE20: the status when the rule does not select exactly one sheet
    sd7_pass: int | None = None      # FE20: 1 (labels, position 0) or 2 (labels and the ASD column)


@dataclasses.dataclass(frozen=True)
class MemberDecl:
    key: str               # runner-side key
    match: str             # exact member name or path ending (plan); never printed
    how: str = "exact"     # "exact" | "suffix"
    ext: str = ""          # declared extension of the saved file
    save_name: str | None = None   # a declared runner name (e.g. lh.aparc.annot); else <target>_member<index><ext>
    kind: str = "file"     # "workbook" | "file"
    sheets: tuple = ()
    do_not_open: tuple = ()


@dataclasses.dataclass(frozen=True)
class Target:
    key: str
    gate: str              # "ungated" | "G2" | "G1"
    url: str
    kind: str              # "workbook" | "zip" | "tar_member" | "file"
    ext: str
    pinned_bytes: int | None = None
    pinned_sha256: str | None = None
    refs: tuple = ()       # identity references (identity.ref_from_probe dicts)
    identity_at_download: bool = False
    sheets: tuple = ()
    do_not_open: tuple = ()
    members: tuple = ()
    per_participant: bool = False
    refusal_status: str | None = None
    local_path: str | None = None   # FE15: a pinned existing copy (never printed or written; recorded by sha256)
    part_name: str | None = None    # FE19: a runner-built per-attempt .part name
    defer_quarantine: bool = False  # FE21
    quarantine_dir: str | None = None   # FE22: the directory moved whole by step 6 (it holds the pinned copy)
    deletion_extra: tuple = ()      # FE22: ((field, fixed text), ...) added to the deletion request
    head_before_get: bool = True    # FE23: False for a target whose rule is one GET (R45 (a): the decoder)
    url_note: str | None = None     # FE23: a fixed note beside the URL field (e.g. "no URL registered")


@dataclasses.dataclass
class Roots:
    repo: Path
    data: Path
    records: Path
    artifacts: Path
    logs: Path
    control: Path
    quarantine: Path

    @classmethod
    def production(cls, repo: Path = REPO) -> "Roots":
        e = Path("E:/data/asdg")
        return cls(repo=Path(repo), data=e, records=Path(repo) / "arcs/audit/register_maps/post_freeze",
                   artifacts=Path(repo) / "artifacts/audit/extracted", logs=Path(repo) / "artifacts/audit/material_logs",
                   control=Path(repo) / "arcs/audit/run_manifests/material", quarantine=e / "_quarantine")


def _check_target(t: Target) -> None:
    if not _KEY_RE.fullmatch(t.key) or t.gate not in ("ungated", "G2", "G1"):
        raise ValueError("target key / gate")
    if t.kind not in ("workbook", "zip", "tar_member", "file"):
        raise ValueError("target kind")
    if not re.fullmatch(r"(\.[a-z0-9]{1,5}){1,2}", t.ext):
        raise ValueError("target extension")
    if t.local_path is not None and t.kind not in ("workbook", "file"):
        raise ValueError("a pinned local copy is for workbook / file targets")
    if t.part_name is not None and not re.fullmatch(r"carrier(\.[a-z0-9]{1,5}){1,2}\.a[0-9]{1,3}\.part", t.part_name):
        raise ValueError("part name")
    if t.quarantine_dir is not None and (t.local_path is None or not _inside(Path(t.local_path), Path(t.quarantine_dir))):
        raise ValueError("a quarantine directory must hold the pinned copy")
    for d in list(t.sheets) + [s for m in t.members for s in m.sheets]:
        if not _KEY_RE.fullmatch(d.key) or d.mode not in ("columns", "mist64_matrix", "sd7", "labelled",
                                                            "columns_search"):
            raise ValueError("sheet declaration")
        if d.mode in ("labelled", "columns_search") and (not d.columns or d.header_row is not None):
            raise ValueError("labelled declaration")
        if d.mode == "sd7" and (d.name_rule is None or d.sd7_pass not in (1, 2)):
            raise ValueError("sd7 declaration")
        for c in d.columns:
            if not _KEY_RE.fullmatch(c.key):
                raise ValueError("column key")
    for m in t.members:
        if not _KEY_RE.fullmatch(m.key) or m.how not in ("exact", "suffix"):
            raise ValueError("member declaration")
        if m.save_name is not None and not re.fullmatch(r"[A-Za-z0-9_.\-]{1,64}", m.save_name):
            raise ValueError("member save name")


def moreau_target(url: str, refs: tuple = (), *, key: str = "moreau2020mutations", pinned_bytes=None,
                  pinned_sha256=None, vocab: tuple | None = None) -> Target:
    """Moreau Supplementary_Table_S1.xlsx: the two declared sheets read as MIST64 matrices (section 8 step 4), the
    do-not-open list of step 3. The URL / identity come from the register (WP3)."""
    voc = vocab if vocab is not None else mist64_vocab()
    sheets = (SheetDecl(key="del16p11", name=MOREAU_SHEETS[0], mode="mist64_matrix", vocab=voc),
              SheetDecl(key="del22q11", name=MOREAU_SHEETS[1], mode="mist64_matrix", vocab=voc))
    return Target(key=key, gate="ungated", url=url, kind="workbook", ext=".xlsx", pinned_bytes=pinned_bytes,
                  pinned_sha256=pinned_sha256, refs=tuple(refs), sheets=sheets, do_not_open=MOREAU_DO_NOT_OPEN,
                  refusal_status=MOREAU_LAYOUT)


def freesurfer_target(key: str = "freesurfer741_fsaverage_annot") -> Target:
    """R16: the pinned ubuntu22 tarball, streamed to its lh.aparc.annot member (G2, first step of WP4)."""
    return Target(key=key, gate="G2", url=R16_URL, kind="tar_member", ext=".tar.gz", pinned_bytes=R16_BYTES,
                  identity_at_download=True,
                  members=(MemberDecl(key="lh_aparc_annot", match=R16_SUFFIX, how="suffix", ext=".annot",
                                      save_name=R16_NAME),),
                  refusal_status=RP.STATUS_FS_NOT_REGULAR)


# ----------------------------------------------------------------------------------------------------------------
# MIST64 identifier forms and the column rule (section 8 step 4)
# ----------------------------------------------------------------------------------------------------------------
def mist64_vocab(path: Path | None = None) -> tuple:
    """((roi, label, name), ...) from register_maps/mist64_classes.json (sha256 asserted). Asserts the plan's facts:
    64 parcels, roi 1..64, labels distinct when casefolded, names distinct, no casefolded label equals a casefolded
    name."""
    p = Path(path) if path is not None else REPO / MIST64_REL
    lf = p.read_bytes().replace(b"\r\n", b"\n")
    if path is None and hashlib.sha256(lf).hexdigest() != MIST64_SHA256:
        raise AssertionError("mist64_classes.json differs from its pin")
    doc = json.loads(lf.decode("utf-8"))
    voc = tuple((int(q["roi"]), str(q["label"]), str(q["name"])) for q in doc["parcels"])
    Mist64Rule(voc)          # asserts the facts
    return voc


def _empty(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


class Mist64Rule:
    """The column rule of section 8 step 4, a function of the one row the guard passes it. Forms tried in order:
    label, name (text equal after strip + casefold), roi (an int, an integral float or a text of ASCII digits)."""

    FORMS = ("label", "name", "roi")

    def __init__(self, vocab):
        voc = tuple(vocab)
        if len(voc) != 64 or sorted(r for r, _, _ in voc) != list(range(1, 65)):
            raise AssertionError("MIST64 vocabulary: 64 parcels with roi 1..64")
        labs = [self.norm(lab) for _, lab, _ in voc]
        nams = [self.norm(nm) for _, _, nm in voc]
        if len(set(labs)) != 64 or len(set(nams)) != 64 or set(labs) & set(nams):
            raise AssertionError("MIST64 vocabulary: labels / names not distinct when casefolded")
        self.vocab = voc
        self.maps = {"label": {self.norm(lab): r for r, lab, _ in voc}, "name": {self.norm(nm): r for r, _, nm in voc}}
        self.label_of = {r: lab for r, lab, _ in voc}

    @staticmethod
    def norm(s: str) -> str:
        return s.strip().casefold()

    def match(self, form: str, v):
        if form in ("label", "name"):
            return self.maps[form].get(self.norm(v)) if isinstance(v, str) else None
        if isinstance(v, bool):
            return None
        if isinstance(v, int):
            x = v
        elif isinstance(v, float):
            if not (math.isfinite(v) and v.is_integer()):
                return None
            x = int(v)
        elif isinstance(v, str):
            s = v.strip()
            if not (s and s.isascii() and s.isdigit()):
                return None
            x = int(s)
        else:
            return None
        return x if 1 <= x <= 64 else None

    def analyse(self, row):
        """(form, {position: roi}, label column) or None."""
        cells = [(j, v) for j, v in enumerate(row) if not _empty(v)]
        for form in self.FORMS:
            hits: dict[int, list[int]] = {}
            other = []
            for j, v in cells:
                r = self.match(form, v)
                if r is None:
                    other.append(j)
                else:
                    hits.setdefault(r, []).append(j)
            if len(hits) != 64 or any(len(p) != 1 for p in hits.values()):
                continue
            pos = {p[0]: r for r, p in hits.items()}
            left = min(pos)
            if left < 1 or len(other) > 1 or (other and other[0] != left - 1):
                return None
            return form, pos, left - 1
        return None

    def __call__(self, row) -> list[int]:
        a = self.analyse(list(row))
        if a is None:
            return []
        _form, pos, label_col = a
        return sorted(pos) + [label_col]


# ----------------------------------------------------------------------------------------------------------------
# network (replaced wholesale by the tests; P21: with the gate closed none of these is called)
# ----------------------------------------------------------------------------------------------------------------
def _curl_head(url: str) -> dict:
    """HTTP HEAD (redirects followed) with fetch_util's User-Agent only; keeps Content-Length, Last-Modified (an HTTP
    date), a plain-MD5 ETag and (fix round 4, item 4) a Content-Type LABEL of the fixed vocabulary (CONTENT_TYPE_HTML
    for text/html, CONTENT_TYPE_OTHER otherwise; the header text itself is not kept) of the final response."""
    p = subprocess.run(["curl", "-sS", "-I", "-L", "-m", "120", "-A", FU.UA, url], capture_output=True, timeout=180)
    out = {"status_code": None, "content_length": None, "last_modified": None, "etag_md5": None,
           "content_type_label": None}
    if p.returncode != 0:
        return out
    blocks = [b for b in p.stdout.decode("latin-1").replace("\r\n", "\n").split("\n\n") if b.strip()]
    if not blocks:
        return out
    lines = blocks[-1].split("\n")
    m = re.match(r"HTTP/[0-9.]+ (\d{3})", lines[0])
    out["status_code"] = int(m.group(1)) if m else None
    for ln in lines[1:]:
        k, _, v = ln.partition(":")
        k, v = k.strip().lower(), v.strip()
        if k == "content-length" and re.fullmatch(r"\d{1,15}", v):
            out["content_length"] = int(v)
        elif k == "last-modified" and _HTTP_DATE.fullmatch(v):
            out["last_modified"] = v
        elif k == "etag":
            out["etag_md5"] = ID.plain_md5(v)
        elif k == "content-type":
            out["content_type_label"] = content_type_label(v)
    return out


CONTENT_TYPE_HTML = "html page"
CONTENT_TYPE_OTHER = "not an html page"


def content_type_label(value) -> str | None:
    """A Content-Type header as a label of the fixed vocabulary (fix round 4, item 4); the text is not kept."""
    if not isinstance(value, str) or not value.strip():
        return None
    return CONTENT_TYPE_HTML if value.split(";")[0].strip().casefold() == "text/html" else CONTENT_TYPE_OTHER


def _fu_get(url: str, out: Path) -> dict:
    return FU.get(url, Path(out))


@contextlib.contextmanager
def _curl_stream(url: str):
    proc = subprocess.Popen(["curl", "-sS", "-L", "-A", FU.UA, url], stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL)
    try:
        yield proc.stdout
    finally:
        with contextlib.suppress(Exception):
            proc.kill()
        with contextlib.suppress(Exception):
            proc.stdout.close()
        with contextlib.suppress(Exception):
            proc.wait(timeout=30)


NET = {"head": _curl_head, "get": _fu_get, "stream": _curl_stream}


# ----------------------------------------------------------------------------------------------------------------
# gate (step 0) and quarantine refusal
# ----------------------------------------------------------------------------------------------------------------
def gate_check(t: Target, repo: Path) -> tuple[bool, str]:
    """(open?, reason label). G1 through gates.require_g1_open, G2 through gates.require_step3v_open."""
    if t.gate == "ungated":
        return True, "open"
    who = "fetch_extract"
    try:
        if t.gate == "G1":
            gates.require_g1_open(who, repo)
        elif t.gate == "G2":
            gates.require_step3v_open(who, repo)
        else:
            return False, "exception"
    except PermissionError:
        reason = gates.g1_check(repo)[1] if t.gate == "G1" else gates.step3v_check(repo)[1]
        return False, reason if reason != "open" else "exception"
    except Exception:  # noqa: BLE001 - fail closed
        return False, "exception"
    return True, "open"


def refuse_quarantine_path(path, quarantine_root: Path | None = None) -> None:
    """Section 8 step 6: the audit runner refuses any path under _quarantine (any component, case-folded, or under
    the configured quarantine root). For run.py / WP3 loaders as well."""
    p = Path(path)
    if any(part.casefold() == "_quarantine" for part in p.parts):
        raise PermissionError("path under _quarantine")
    if quarantine_root is not None:
        with contextlib.suppress(ValueError):
            Path(os.path.abspath(p)).relative_to(Path(os.path.abspath(quarantine_root)))
            raise PermissionError("path under the quarantine root")


def refuse_quarantine_opener(path, quarantine_root: Path | None = None) -> Path:
    """WP2 review B4: the check every real-path opener outside fetch makes before it opens a file (identity.file_facts /
    load_prefreeze, reparcel.load_atlas_verified / read_annot / read_gifti_values, ahba_extras.load_r12_ds,
    run.RealSources.real_path, which WP3's loaders inherit): refuse_quarantine_path with the given quarantine root,
    default the production root (Roots.production().quarantine). Returns the path; raises PermissionError."""
    root = Roots.production().quarantine if quarantine_root is None else Path(quarantine_root)
    refuse_quarantine_path(path, root)
    return Path(path)


def sheet_key(name) -> str:
    """WP2 review C9: sheet names are compared stripped and casefolded (a do-not-open sheet declared as ' 5_biv' or
    read back as '5_BIV ' is still the do-not-open sheet)."""
    return str(name).strip().casefold()


def do_not_open_hits(names, do_not_open) -> set:
    """The names (as given) whose sheet_key equals a do-not-open name's sheet_key."""
    dno = {sheet_key(n) for n in do_not_open}
    return {n for n in names if sheet_key(n) in dno}


# ----------------------------------------------------------------------------------------------------------------
# openpyxl without touching undeclared sheet parts (FE1)
# ----------------------------------------------------------------------------------------------------------------
class _AuditZipFile(zipfile.ZipFile):
    """Records every part / member opened (in memory only)."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.a1_opened: list[str] = []

    def open(self, name, *a, **kw):
        self.a1_opened.append(name.filename if isinstance(name, zipfile.ZipInfo) else str(name))
        return super().open(name, *a, **kw)


@contextlib.contextmanager
def _lazy_openpyxl(counters: dict):
    import openpyxl
    from openpyxl.packaging.relationship import RelationshipList
    from openpyxl.reader import excel as XL
    from openpyxl.worksheet._read_only import ReadOnlyWorksheet
    if openpyxl.__version__ != OPENPYXL_VERSION:
        raise ImportError("openpyxl version differs from the one the deferral was verified on")

    class _LazyROWorksheet(ReadOnlyWorksheet):
        _a1_deferred = True

        def _get_size(self):
            if self._a1_deferred:
                return None
            return super()._get_size()

        def a1_materialise(self):
            self._a1_deferred = False
            self._get_size()

    def _no_dependents(archive, path):
        counters["rels_skipped"] = counters.get("rels_skipped", 0) + 1
        return RelationshipList()

    def _skip_chartsheet(self, sheet, rel):
        counters["chartsheets_skipped"] = counters.get("chartsheets_skipped", 0) + 1

    saved = (XL.ReadOnlyWorksheet, XL.ZipFile, XL.get_dependents, XL.ExcelReader.read_chartsheet)
    XL.ReadOnlyWorksheet, XL.ZipFile, XL.get_dependents = _LazyROWorksheet, _AuditZipFile, _no_dependents
    XL.ExcelReader.read_chartsheet = _skip_chartsheet
    try:
        yield _LazyROWorksheet
    finally:
        XL.ReadOnlyWorksheet, XL.ZipFile, XL.get_dependents, XL.ExcelReader.read_chartsheet = saved


# ----------------------------------------------------------------------------------------------------------------
# reading declared sheets
# ----------------------------------------------------------------------------------------------------------------
def _jsonable_cell(v):
    if isinstance(v, (_dt.datetime, _dt.date, _dt.time)):
        return v.isoformat()
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v


def _numeric(v):
    """FE4."""
    if _empty(v):
        return None
    if isinstance(v, bool):
        raise ValueError("boolean in a numeric column")
    if isinstance(v, (int, float)):
        x = float(v)
    elif isinstance(v, str):
        x = float(v.strip())
    else:
        raise ValueError("cell type in a numeric column")
    if not math.isfinite(x):
        raise ValueError("non-finite value in a numeric column")
    return x


def _collect(data_rows, decl: SheetDecl, pos: list[int]) -> dict:
    """FE5: the declared cells of the data rows, keyed by the runner-side column keys."""
    cols = {c.key: [] for c in decl.columns}
    n, n_empty = 0, 0
    for r in data_rows:
        cells = [r[p] if p < len(r) else None for p in pos]
        if all(_empty(v) for v in cells):
            n_empty += 1
            continue
        n += 1
        for c, v in zip(decl.columns, cells):
            cols[c.key].append(_numeric(v) if c.numeric else (None if _empty(v) else _jsonable_cell(v)))
    return {"columns": cols, "n_rows": n, "n_empty_rows": n_empty}


def _verdict_record(v: dict) -> dict:
    return {"rules": v["rules"], "identifier_bearing": bool(v["identifier_bearing"]), "n_rows": v.get("n_rows"),
            "n_cols": v.get("n_cols"), "n_cols_dimension_tag": v.get("n_cols_dimension_tag"),
            "id_wording_cells": v.get("id_wording_cells"), "bare_subject_headers": v.get("bare_subject_headers"),
            "id_value_hits_total": sum((v.get("id_value_hits") or {}).values())}


def _mist64_block(rows: list, h: int, rule: Mist64Rule) -> dict:
    """Section 8 step 4's post-read assertions on the guard's (masked) rows; LayoutRefused on any failure."""
    a = rule.analyse(list(rows[h]))
    if a is None:
        raise LayoutRefused("header")
    form, colmap, label_col = a
    body = rows[h + 1:h + 1 + 64]
    if len(body) != 64:
        raise LayoutRefused("rows")
    row_roi = []
    for r in body:
        x = rule.match(form, r[label_col] if label_col < len(r) else None)
        if x is None:
            raise LayoutRefused("row label")
        row_roi.append(x)
    if sorted(row_roi) != list(range(1, 65)):
        raise LayoutRefused("row labels not each once")
    block = [[None] * 64 for _ in range(64)]
    n_num = 0
    for i, r in enumerate(body):
        for p, croi in colmap.items():
            v = r[p] if p < len(r) else None
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)):
                raise LayoutRefused("block cell not numeric")
            block[row_roi[i] - 1][croi - 1] = float(v)
            n_num += 1
    keep = sorted(colmap) + [label_col]
    n_after = sum(1 for r in rows[h + 1 + 64:] if any(not _empty(r[p]) for p in keep if p < len(r)))
    labels = [rule.label_of[k] for k in range(1, 65)]
    return {"form": form, "header_row": h, "block_cells_numeric": n_num, "n_rows_after_block_nonempty": n_after,
            "object": {"ids": list(range(1, 65)), "labels": labels, "values": block}}


class _Book:
    """One workbook behind one accessor: names in memory, declared sheets fetched through fetch(), access log."""

    def __init__(self, path: Path, ext: str, counters: dict):
        self.ext, self.counters, self.access_log = ext, counters, []
        if ext == ".xlsx":
            import openpyxl
            with _lazy_openpyxl(counters) as lazy_cls:
                self.wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True, keep_links=False,
                                                 keep_vba=False)
            self.lazy_cls = lazy_cls
            self.names = list(self.wb.sheetnames)
            self.part_of = {ws.title: ws._worksheet_path for ws in self.wb.worksheets if isinstance(ws, lazy_cls)}
        elif ext == ".xls":
            import xlrd
            self.sink = PW.Sink()
            self.book = xlrd.open_workbook(str(path), on_demand=True, logfile=self.sink, verbosity=0,
                                           formatting_info=False, use_mmap=False)
            self.names = list(self.book.sheet_names())
        else:
            raise ValueError("workbook extension")

    def fetch(self, name: str, declared: set):
        if name not in declared:
            raise AssertionError("accessor called for an undeclared sheet")
        self.access_log.append(name)
        if self.ext == ".xlsx":
            ws = self.wb[name]
            ws.a1_materialise()
            return ws
        return self.book.sheet_by_name(name)

    def classify(self, sh) -> dict:
        return PG.classify_openpyxl(sh) if self.ext == ".xlsx" else PG.classify_xlrd(sh)

    def rows_columns(self, sh, decl: SheetDecl, verdict: dict):
        texts = [c.header for c in decl.columns]
        if decl.header_row is None or not texts:
            raise LayoutRefused("declaration")
        h = decl.header_row
        if self.ext == ".xlsx":
            rows = PG.read_openpyxl(sh, declared=texts, header_row=h, label=decl.key, verdict=verdict)
            header = list(rows[h]) if h < len(rows) else []
        else:
            cv = PG.xlrd_cell_reader(sh, declared=texts, header_row=h, label=decl.key, verdict=verdict)
            rows = [[cv(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]
            header = rows[h] if h < len(rows) else []
        pos = PG._declared_positions(header, texts, decl.key, decl.key)
        return rows[h + 1:], pos

    def rows_mist64(self, sh, rule: Mist64Rule, verdict: dict):
        """The header-row search: h = 0 ... 19 through the guard's own API; a Refused for an h that does not qualify
        is caught silently (nothing of its message is kept); only the count of rows tried is recorded."""
        tried = 0
        limit = PG.GUARD_ROWS if self.ext == ".xlsx" else min(PG.GUARD_ROWS, sh.nrows)
        for h in range(limit):
            tried += 1
            try:
                if self.ext == ".xlsx":
                    rows = PG.read_openpyxl(sh, declared=rule, header_row=h, label="mist64", verdict=verdict)
                else:
                    cv = PG.xlrd_cell_reader(sh, declared=rule, header_row=h, label="mist64", verdict=verdict)
                    rows = [[cv(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]
            except PG.Refused:
                continue
            return rows, h, tried
        return None, None, tried

    def rows_rule(self, sh, rule, verdict: dict, label: str):
        """FE20: the header-row search of a column rule (h = 0 ... 19) through the guard's own API, as rows_mist64."""
        tried = 0
        limit = PG.GUARD_ROWS if self.ext == ".xlsx" else min(PG.GUARD_ROWS, sh.nrows)
        for h in range(limit):
            tried += 1
            try:
                if self.ext == ".xlsx":
                    rows = PG.read_openpyxl(sh, declared=rule, header_row=h, label=label, verdict=verdict)
                else:
                    cv = PG.xlrd_cell_reader(sh, declared=rule, header_row=h, label=label, verdict=verdict)
                    rows = [[cv(r, c) for c in range(sh.ncols)] for r in range(sh.nrows)]
            except PG.Refused:
                continue
            return [list(r) for r in rows], h, tried
        return None, None, tried

    def undeclared_touched(self, declared: set) -> dict:
        if self.ext == ".xlsx":
            opened = set(self.wb._archive.a1_opened)
            und_parts = {p for n, p in self.part_of.items() if n not in declared}
            return {"parts_opened_undeclared": len(und_parts & opened)}
        loaded = [self.names[i] for i in range(len(self.names)) if self.book.sheet_loaded(i)]
        return {"sheets_loaded_undeclared": sum(1 for n in loaded if n not in declared)}

    def close(self):
        if self.ext == ".xlsx":
            self.wb.close()
        else:
            self.book.release_resources()


def _read_workbook(owner: str, path: Path, ext: str, decls: tuple, do_not_open: tuple, em: PW.Emitter,
                   rec: dict) -> tuple[dict, bool]:
    """Steps 3-4 for one workbook. Returns (objects keyed by sheet key, identifier-bearing?)."""
    ruled = [d for d in decls if d.name_rule]
    declared = {d.name for d in decls if not d.name_rule}

    def _dno():
        if len(declared) + len(ruled) != len(decls):
            raise LayoutRefused("duplicate declaration")
        if do_not_open_hits(declared, do_not_open):     # C9: casefolded, stripped
            raise DoNotOpen()
    PW.stage(em, "sheets:do-not-open", _dno)

    counters: dict = {}
    book = PW.stage(em, "sheets:open", _Book, path, ext, counters)
    objects, idb = {}, False
    try:
        def _names():
            names = book.names
            hits = {"V": 0, "N": 0}
            for n in names:
                for k, v in PW.screen(n, PG).items():
                    hits[k] += v
            resolved, n_match = {}, {}
            for d in ruled:                                  # FE20: in memory; the names are never printed
                rx = re.compile(d.name_rule)
                m = [n for n in names if rx.match("".join(ch for ch in str(n).casefold() if ch.isalnum()))]
                n_match[d.key] = len(m)
                if len(m) == 1:
                    resolved[d.key] = m[0]
            return names, hits, resolved, n_match
        names, hits, resolved, n_match = PW.stage(em, "sheets:names", _names)
        if ruled:
            decls = tuple(dataclasses.replace(d, name=resolved[d.key]) if (d.name_rule and d.key in resolved) else d
                          for d in decls)
            declared = {d.name for d in decls if not (d.name_rule and d.key not in resolved)}
        found = [d for d in decls if d.name in names and not (d.name_rule and d.key not in resolved)]
        srec = {"n_sheets": len(names), "n_declared": len(decls), "declared_found": len(found),
                "n_undeclared": len(names) - len(found), "undeclared_not_fetched": True,
                "name_sha256": [PW.sha256_text(n) for n in names], "screen_hits": hits, "declared": []}
        rec["sheets"] = srec
        idb = idb or hits["V"] + hits["N"] > 0
        em.say(f"fetch_extract: {owner} declared sheets {len(found)} / {len(decls)} found; undeclared "
               f"{len(names) - len(found)} (not fetched); sheet-name sha256 recorded {len(names)}; screen hits V "
               f"{hits['V']} N {hits['N']}")
        if ruled:
            rec["sheet_rule_matches"] = dict(n_match)
            em.say(f"fetch_extract: {owner} sheets selected by the declared name rule: "
                   f"{', '.join(f'{k} {v}' for k, v in sorted(n_match.items()))}")
            bad = [d for d in ruled if d.key not in resolved]
            if bad:
                _refuse(em, "sheets:names", LayoutRefused, rec, bad[0].name_status)
        if len(found) != len(decls):
            def _missing():
                raise LayoutRefused("declared sheet not found")
            PW.stage(em, "sheets:names", _missing)
        for d in decls:
            sh = PW.stage(em, "sheets:access", book.fetch, d.name, declared)
            v = PW.stage(em, "sheets:classify", book.classify, sh)
            vr = _verdict_record(v)
            idb = idb or vr["identifier_bearing"]
            drec = {"sheet_key": d.key, "name_sha256": PW.sha256_text(d.name), **vr}
            srec["declared"].append(drec)
            em.say(f"fetch_extract: {owner} sheet {d.key} rules {vr['rules'] or 'none'} rows {vr['n_rows']} cols "
                   f"{vr['n_cols']}")
            if d.mode == "columns":
                data_rows, pos = PW.stage(em, "read:declared-columns", book.rows_columns, sh, d, v)
                got = PW.stage(em, "read:numeric-columns", _collect, data_rows, d, pos)
                objects[d.key] = {"columns": got["columns"]}
                drec.update(columns=[c.key for c in d.columns], n_rows=got["n_rows"],
                            n_empty_rows=got["n_empty_rows"], header_row=d.header_row)
                em.say(f"fetch_extract: {owner} sheet {d.key} declared columns {len(d.columns)} read; rows "
                       f"{got['n_rows']}")
            elif d.mode == "sd7":
                objects[d.key] = _read_sd7(owner, book, sh, d, v, vr, drec, em, rec)
            elif d.mode == "labelled":   # FE25 (WP4, RUN_PLAN_amend_4 R54 draft)
                objects[d.key] = _read_labelled(owner, book, sh, d, v, vr, drec, em, rec)
            elif d.mode == "columns_search":   # FE26 (WP4, RUN_PLAN_amend_4 R57 / R58 (f) draft)
                objects[d.key] = _read_columns_search(owner, book, sh, d, v, vr, drec, em, rec)
            else:
                rule = Mist64Rule(d.vocab)
                rows, h, tried = PW.stage(em, "read:header-search", book.rows_mist64, sh, rule, v)
                drec["header_rows_tried"] = tried
                if rows is None:
                    em.say(f"fetch_extract: {owner} sheet {d.key} header row not found; header rows tried {tried}; "
                           f"rule {vr['rules'] or 'none'}")

                    def _no_header():
                        raise LayoutRefused("no header row")
                    PW.stage(em, "read:header-search", _no_header)
                blk = PW.stage(em, "read:moreau-layout", _mist64_block, rows, h, rule)
                objects[d.key] = blk.pop("object")
                drec.update(blk)
                em.say(f"fetch_extract: {owner} sheet {d.key} header row found after {tried} tries; form "
                       f"{blk['form']}; block 64 x 64 numeric {blk['block_cells_numeric']}; rule {vr['rules'] or 'none'}")

        def _post():
            log_ok = (all(n in declared for n in book.access_log)
                      and not do_not_open_hits(book.access_log, do_not_open))   # C9: casefolded, stripped
            touched = book.undeclared_touched(declared)
            if not log_ok or any(touched.values()):
                raise AssertionError("an undeclared sheet was touched")
            return log_ok, touched
        log_ok, touched = PW.stage(em, "sheets:access-log", _post)
        srec.update(access_log=[PW.sha256_text(n) for n in book.access_log], access_log_declared_only=log_ok,
                    **touched, chartsheets=counters.get("chartsheets_skipped", 0))
        if getattr(book, "sink", None) is not None:
            srec["xlrd_log_writes"] = book.sink.n_writes
        em.say(f"fetch_extract: {owner} access log declared sheets only: pass; undeclared sheets touched 0")
    finally:
        with contextlib.suppress(Exception):
            book.close()
    return objects, idb


def _read_sd7(owner: str, book, sh, d: SheetDecl, v: dict, vr: dict, drec: dict, em: PW.Emitter, rec: dict):
    """FE20 (RUN_PLAN_amend_3 R46 (c)-(f)): the header row by the ASD-anchored rule through the guard; the block; the
    wrapper-side mask (a PositionView of the declared positions); pass 2's values with the missing-value tokens.
    Refusals carry R46's statuses (rec["refused_reason"]); nothing of a cell is printed or kept but counts."""
    from a1_audit import wp3_sd7 as SD
    rule = SD.asd_rule(d.sd7_pass)
    rows, h, tried = PW.stage(em, "read:header-search", book.rows_rule, sh, rule, v, d.key)
    drec["header_rows_tried"] = tried
    if rows is None:
        em.say(f"fetch_extract: {owner} sheet {d.key} header row not found; header rows tried {tried}; rule "
               f"{vr['rules'] or 'none'}")
        _refuse(em, "read:header-search", LayoutRefused, rec, SD.SD7_HEADER)

    def _block():
        try:
            return SD.label_block(rows, h, set(d.vocab))
        except SD.Sd7Refused as e:
            rec["refused_reason"] = e.status
            rec["sd7_counts"] = dict(e.counts)
            raise LayoutRefused("sd7 block") from None
    blk = PW.stage(em, "read:sd7-block", _block)
    a = SD.asd_position(rows[h])
    handed = (0,) if d.sd7_pass == 1 else (0, a)
    cols = {0: [rows[i][0] for i in blk["rows"]]}          # the wrapper-side mask: declared positions only
    counts = dict(blk["counts"])
    if d.sd7_pass == 2:
        def _values():
            vals, n_missing = [], 0
            for i in blk["rows"]:
                kind, x = SD.value_of(rows[i][a] if a < len(rows[i]) else None)
                if kind == "refuse":
                    rec["refused_reason"] = SD.SD7_NON_NUMERIC
                    raise ValueError("sd7 value")
                n_missing += kind == "missing"
                vals.append(x)
            return vals, n_missing
        vals, n_missing = PW.stage(em, "read:sd7-values", _values)
        cols[a] = vals
        counts["n_missing_values"] = n_missing
    rows = None                                              # nothing of the sheet is kept past this point
    drec.update(header_row=h, positions_handed=list(handed), sd7_pass=d.sd7_pass, **counts)
    em.say(f"fetch_extract: {owner} sheet {d.key} header row found after {tried} tries; pass {d.sd7_pass}; block rows "
           f"{counts['n_block_rows']}; cells after the block {counts['n_cells_after_block']}; positions handed "
           f"{len(handed)}")
    return SD.PositionView(cols, handed)


def labelled_rule(texts: tuple):
    """FE25: the column rule of a labelled table - the header row holds each declared header text exactly once (a
    text cell equal to it after stripping), at positions > 0; returns [0, <their positions in declaration order>],
    else [] (the guard refuses that row)."""
    def rule(header) -> list[int]:
        row = list(header)
        out = [0]
        for t in texts:
            hits = [j for j, v in enumerate(row) if isinstance(v, str) and v.strip() == t]
            if len(hits) != 1 or hits[0] == 0:
                return []
            out.append(hits[0])
        return out
    return rule


def _read_labelled(owner: str, book, sh, d: SheetDecl, v: dict, vr: dict, drec: dict, em: PW.Emitter, rec: dict):
    """FE25 (WP4; RUN_PLAN_amend_4 R54, draft): a labelled table - the header row by labelled_rule through the guard
    (h = 0 ... 19, as FE20); the block of rows with a non-empty position-0 cell after it (wp3_sd7.label_block: empty
    rows skipped, an interrupted block refused); a wrapper-side mask hands the transform position 0 and the declared
    positions only (a PositionView; `declared` maps each column key to its position)."""
    from a1_audit import wp3_sd7 as SD
    texts = tuple(c.header for c in d.columns)
    rule = labelled_rule(texts)
    rows, h, tried = PW.stage(em, "read:header-search", book.rows_rule, sh, rule, v, d.key)
    drec["header_rows_tried"] = tried
    if rows is None:
        em.say(f"fetch_extract: {owner} sheet {d.key} header row not found; header rows tried {tried}; rule "
               f"{vr['rules'] or 'none'}")
        _refuse(em, "read:header-search", LayoutRefused)

    def _block():
        try:
            return SD.label_block(rows, h, set(d.vocab))
        except SD.Sd7Refused as e:
            rec["sd7_counts"] = dict(e.counts)
            raise LayoutRefused("labelled block") from None
    blk = PW.stage(em, "read:sd7-block", _block)
    pos = rule(rows[h])
    cols = {p: [rows[i][p] if p < len(rows[i]) else None for i in blk["rows"]] for p in pos}
    rows = None                                              # nothing of the sheet is kept past this point
    view = SD.PositionView(cols, tuple(pos))
    view.declared = {c.key: p for c, p in zip(d.columns, pos[1:])}
    drec.update(header_row=h, positions_handed=list(view.handed), **blk["counts"])
    em.say(f"fetch_extract: {owner} sheet {d.key} header row found after {tried} tries; block rows "
           f"{blk['counts']['n_block_rows']}; cells after the block {blk['counts']['n_cells_after_block']}; positions "
           f"handed {len(view.handed)}")
    return view


def search_rule(texts: tuple, alternatives: tuple):
    """FE26: the header row holds each declared text exactly once and, when alternatives are declared, the FIRST of
    them (in declaration order) that the row holds exactly once; returns [<the alternative's position>, <the declared
    positions>] (or the declared positions alone), else []."""
    def rule(header) -> list[int]:
        row = list(header)

        def once(t):
            hits = [j for j, v in enumerate(row) if isinstance(v, str) and v.strip() == t]
            return hits[0] if len(hits) == 1 else None
        pos = [once(t) for t in texts]
        if any(p_ is None for p_ in pos):
            return []
        if alternatives:
            alt = next((once(a) for a in alternatives if once(a) is not None), None)
            if alt is None or alt in pos:
                return []
            return [alt] + pos
        return pos
    return rule


def _read_columns_search(owner: str, book, sh, d: SheetDecl, v: dict, vr: dict, drec: dict, em: PW.Emitter, rec: dict):
    """FE26 (WP4): declared columns found by a header-row search through the guard (h = 0 ... 19); the rows are those
    after the header whose declared cells are not all empty (FE5); a PositionView hands the transform the declared
    positions only (`declared`: key -> position; 'alt' = the first declared alternative found)."""
    from a1_audit import wp3_sd7 as SD
    texts = tuple(c.header for c in d.columns)
    rule = search_rule(texts, tuple(d.vocab))
    rows, h, tried = PW.stage(em, "read:header-search", book.rows_rule, sh, rule, v, d.key)
    drec["header_rows_tried"] = tried
    if rows is None:
        em.say(f"fetch_extract: {owner} sheet {d.key} header row not found; header rows tried {tried}; rule "
               f"{vr['rules'] or 'none'}")
        _refuse(em, "read:header-search", LayoutRefused)
    pos = rule(rows[h])
    body = [r for r in rows[h + 1:] if any(not _empty(r[q]) for q in pos if q < len(r))]
    cols = {q: [r[q] if q < len(r) else None for r in body] for q in pos}
    rows = None
    view = SD.PositionView(cols, tuple(pos))
    keys = (["alt"] if d.vocab else []) + [c.key for c in d.columns]
    view.declared = dict(zip(keys, pos))
    drec.update(header_row=h, positions_handed=list(view.handed), n_rows=len(body))
    em.say(f"fetch_extract: {owner} sheet {d.key} header row found after {tried} tries; rows {len(body)}; positions "
           f"handed {len(view.handed)}")
    return view


def _refuse(em: PW.Emitter, label: str, exc_type, rec: dict | None = None, status: str | None = None):
    """A refusal decided by the runner (not by an exception elsewhere): the reading's status (if any) is noted in the
    record, then the refusal goes through the section 8 handler like any other exception. The reported line is the
    caller's (sys._getframe(1)), so the record names the site that decided the refusal."""
    if rec is not None and status is not None:
        rec["refused_reason"] = status
    f = sys._getframe(1)
    where = f"{os.path.basename(f.f_code.co_filename)}:{f.f_lineno}"
    em.say(f"{exc_type.__name__} at {label}, {where}")
    raise PW.StageFailed(exc_type.__name__, label, where)


# ----------------------------------------------------------------------------------------------------------------
# zip and tar carriers
# ----------------------------------------------------------------------------------------------------------------
def _member_matches(name: str, m: MemberDecl) -> bool:
    n = _norm(name)
    if m.how == "exact":
        return n == _norm(m.match)
    suf = _norm(m.match)
    return n == suf or n.endswith("/" + suf)


def _norm(name: str) -> str:
    n = name.replace("\\", "/")
    while n.startswith("./"):
        n = n[2:]
    return n


def _save_name(t: Target, m: MemberDecl, index: int) -> str:
    return m.save_name if m.save_name else f"{t.key}_member{index}{m.ext}"


def _read_zip(t: Target, path: Path, roots: Roots, em: PW.Emitter, rec: dict):
    """(objects, identifier-bearing?, files to quarantine besides the carrier)."""
    kdir = roots.data / t.key
    zrec = {"members": []}
    rec["zip"] = zrec
    objects, idb, q_files = {}, False, []

    zf = PW.stage(em, "zip:members", _AuditZipFile, str(path))

    def _list():
        infos = zf.infolist()
        hits = {"V": 0, "N": 0}
        for i in infos:
            for k, v in PW.screen(i.filename, PG).items():
                hits[k] += v
        picks = []
        for m in t.members:
            idx = [k for k, i in enumerate(infos) if not i.is_dir() and _member_matches(i.filename, m)]
            if len(idx) != 1:
                raise MemberRefused("declared member not found exactly once")
            picks.append((m, idx[0]))
        return infos, hits, picks
    saved = []
    try:
        infos, hits, picks = PW.stage(em, "zip:members", _list)
        zrec.update(n_members=len(infos), n_dirs=sum(1 for i in infos if i.is_dir()),
                    name_sha256=[PW.sha256_text(i.filename) for i in infos], screen_hits=hits)
        idb = hits["V"] + hits["N"] > 0
        em.say(f"fetch_extract: {t.key} zip members {len(infos)}; declared {len(picks)} / {len(t.members)} found; "
               f"member-name sha256 recorded {len(infos)}; screen hits V {hits['V']} N {hits['N']}")
        for m, k in picks:
            out = kdir / _save_name(t, m, k)
            em.allow.add_exact(out)
            sha = PW.stage(em, "zip:extract", lambda: em.save_bytes(out, zf.read(infos[k])))
            saved.append((m, k, out, sha))
            zrec["members"].append({"member_key": m.key, "member_index": k, "name_sha256":
                                    PW.sha256_text(infos[k].filename), "saved_path": out.as_posix(),
                                    "saved_sha256": sha, "bytes": infos[k].file_size})
            em.say(f"fetch_extract: {t.key} member {m.key} saved {out} sha256 {sha}")

        def _check_opens():
            wanted = {infos[k].filename for _, k in picks}
            und = [n for n in zf.a1_opened if n not in wanted]
            if und:
                raise AssertionError("an undeclared member was read")
            return len(und)
        zrec["undeclared_members_read"] = PW.stage(em, "zip:members", _check_opens)
    finally:
        zf.close()
    for m, k, out, sha in saved:
        if m.kind == "workbook":
            sub: dict = {}
            zrec.setdefault("workbooks", {})[m.key] = sub
            objs, sub_idb = _read_workbook(f"{t.key} {m.key}", out, m.ext, m.sheets, m.do_not_open, em, sub)
            objects[m.key] = objs
            if sub_idb:
                idb = True
                q_files.append(out)
    return objects, idb, q_files


class _Counting:
    """A read-only byte stream wrapper counting the bytes read."""

    def __init__(self, raw):
        self.raw, self.n = raw, 0

    def read(self, n=-1):
        b = self.raw.read(n)
        self.n += len(b)
        return b


def _member_type(m: tarfile.TarInfo) -> str:
    if m.isreg():
        return "regular"
    if m.islnk():
        return "hard link"
    if m.issym():
        return "symbolic link"
    return "other"


def _link_target(m: tarfile.TarInfo) -> str | None:
    """The link's target normalised inside the archive, or None when it points outside it."""
    ln = (m.linkname or "").replace("\\", "/")
    if not ln or ln.startswith("/") or re.match(r"^[A-Za-z]:", ln):
        return None
    if m.issym():
        p = posixpath.normpath(posixpath.join(posixpath.dirname(_norm(m.name)), ln))
    else:
        p = posixpath.normpath(_norm(ln))
    if p in (".", "..") or p.startswith("../"):
        return None
    return p


MAX_MEMBER_BYTES = 256 * 1024 * 1024


def _tar_pass(t: Target, want, em: PW.Emitter, hits: dict):
    """One streaming pass: the first member for which want(normalised name) holds -> (TarInfo facts, bytes or None,
    bytes streamed, names streamed). The stream stops at that member."""
    with NET["stream"](t.url) as raw:
        cnt = _Counting(raw)
        n_names = 0
        with tarfile.open(fileobj=cnt, mode="r|*") as tf:
            for m in tf:
                n_names += 1
                nm = _norm(m.name)
                for k, v in PW.screen(nm, PG).items():
                    hits[k] += v
                if not want(nm):
                    continue
                facts = {"member_type": _member_type(m), "path_sha256": PW.sha256_text(nm),
                         "target": _link_target(m) if (m.islnk() or m.issym()) else None}
                data = None
                if m.isreg():
                    if m.size > MAX_MEMBER_BYTES:
                        raise MemberRefused("member too large")
                    f = tf.extractfile(m)
                    data = f.read()
                    if len(data) != m.size:
                        raise MemberRefused("short member")
                return facts, data, cnt.n, n_names
    return None, None, cnt.n, n_names


def _read_tar(t: Target, roots: Roots, em: PW.Emitter, rec: dict):
    """R16. Returns (objects, identifier-bearing?, files to quarantine)."""
    if len(t.members) != 1:
        raise ValueError("a tar target declares one member")
    m = t.members[0]
    trec: dict = {"tarball_note": TARBALL_NOTE, "first_note": FIRST_NOTE, "passes": 0}
    rec["tar"] = trec
    hits = {"V": 0, "N": 0}

    head = PW.stage(em, "tar:head", NET["head"], t.url)
    rec["server"] = {"status_code": head.get("status_code"), "content_length": head.get("content_length"),
                     "last_modified": head.get("last_modified"), "etag_md5": head.get("etag_md5")}
    if t.pinned_bytes is not None:
        sp = ID.size_probe(head, t.pinned_bytes)
        trec["size_probe"] = sp
        em.say(f"fetch_extract: {t.key} size-only probe: {sp['result']} (basis {sp['basis']})")
        if sp["result"] != ID.STATUS_MATCH:
            _refuse(em, "tar:head", IdentityRefused, rec, RP.STATUS_FS_NOT_MATCHING)

    facts, data, nb, nn = PW.stage(em, "tar:stream", _tar_pass, t, lambda n: _member_matches(n, m), em, hits)
    trec.update(passes=1, bytes_streamed=[nb], names_streamed=[nn], stream_stopped=facts is not None)
    if facts is None:
        trec["declared_member"] = "not found"
        em.say(f"fetch_extract: {t.key} declared member: not found; names streamed {nn}")
        _refuse(em, "tar:stream", MemberRefused, rec, RP.STATUS_FS_NOT_MATCHING)
    trec.update(declared_member="found", member_type=facts["member_type"], member_path_sha256=facts["path_sha256"])
    em.say(f"fetch_extract: {t.key} declared member: found; member type {facts['member_type']}; bytes streamed "
           f"{nb}; names streamed {nn}")
    if facts["member_type"] in ("hard link", "symbolic link"):
        target = facts["target"]
        if target is None:
            trec["resolved"] = False
            em.say(f"fetch_extract: {t.key} link target outside the archive; unresolvable")
            _refuse(em, "tar:link", MemberRefused, rec, RP.STATUS_FS_NOT_REGULAR)
        trec["link_target_path_sha256"] = PW.sha256_text(target)
        f2, data, nb2, nn2 = PW.stage(em, "tar:link", _tar_pass, t, lambda n: n == target, em, {"V": 0, "N": 0})
        trec.update(passes=2)
        trec["bytes_streamed"].append(nb2)
        trec["names_streamed"].append(nn2)
        if f2 is None or f2["member_type"] != "regular":
            trec["resolved"] = False
            why = "absent" if f2 is None else ("chain" if f2["member_type"] in ("hard link", "symbolic link")
                                                else "other")
            em.say(f"fetch_extract: {t.key} link target {why}; unresolvable")
            _refuse(em, "tar:link", MemberRefused, rec, RP.STATUS_FS_NOT_REGULAR)
        trec["resolved"] = True
        em.say(f"fetch_extract: {t.key} link resolved by a second pass to a regular member")
    elif facts["member_type"] != "regular":
        em.say(f"fetch_extract: {t.key} declared member is not a regular member; refused")
        _refuse(em, "tar:stream", MemberRefused, rec, RP.STATUS_FS_NOT_REGULAR)
    out = roots.data / t.key / _save_name(t, m, 0)
    em.allow.add_exact(out)
    sha = PW.stage(em, "save", em.save_bytes, out, data)
    trec.update(saved_path=out.as_posix(), saved_sha256=sha, bytes=len(data), screen_hits=hits)
    em.say(f"fetch_extract: {t.key} member saved {out} bytes {len(data)} sha256 {sha}; {TARBALL_NOTE}")
    return {}, hits["V"] + hits["N"] > 0, []


# ----------------------------------------------------------------------------------------------------------------
# fetch, SOURCE.md, identity, save, quarantine
# ----------------------------------------------------------------------------------------------------------------
def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def _fetch(t: Target, roots: Roots, em: PW.Emitter, rec: dict) -> Path:
    if t.local_path is not None:                  # FE15: a pinned existing copy, used as found
        lp = Path(t.local_path)
        refuse_quarantine_path(lp, roots.quarantine)

        def _pinned():
            if not lp.is_file():
                raise IdentityRefused("pinned copy absent")
            return lp
        PW.stage(em, "fetch:copy-on-disk", _pinned)
        ph = PW.sha256_text(lp.as_posix())

        def _screen():   # FE17: every carrier-derived path component (below the data root) screened in memory
            try:
                rel = Path(os.path.relpath(os.path.abspath(lp), os.path.abspath(roots.data)))
                if rel.parts and rel.parts[0] == "..":
                    rel = Path(*lp.parts[1:])
            except ValueError:            # another drive: every component but the anchor
                rel = Path(*lp.parts[1:])
            tot = {"V": 0, "N": 0}
            for part in rel.parts:        # each component on its own (fix round 1, B3)
                h = PW.screen(part, PG)
                tot["V"] += int(h.get("V", 0))
                tot["N"] += int(h.get("N", 0))
            return tot
        hits = PW.stage(em, "fetch:copy-on-disk", _screen)
        rec["fetch"] = {"source": "pinned copy on disk", "path_sha256": ph, "screen_hits": hits}
        em.say(f"fetch_extract: {t.key} pinned copy on disk (path sha256 {ph}); no download; path components "
               f"screened: screen hits V {hits['V']} N {hits['N']}")
        return lp
    kdir = roots.data / t.key
    path = kdir / f"carrier{t.ext}"
    part = kdir / (t.part_name or f"carrier{t.ext}.part")      # FE19
    em.allow.add_exact(kdir, path, part)
    refuse_quarantine_path(path, roots.quarantine)
    if part.exists():
        em.say(f"fetch_extract: {t.key} a .part file is present at {part}; refused (operator step)")
        _refuse(em, "fetch:get", DownloadRefused)
    if path.exists():
        rec["fetch"] = {"source": "copy on disk", "path": path.as_posix()}
        em.say(f"fetch_extract: {t.key} copy on disk {path}; no download")
        return path
    if t.head_before_get:
        head = PW.stage(em, "fetch:head", NET["head"], t.url)
        rec["server"] = {"status_code": head.get("status_code"), "content_length": head.get("content_length"),
                         "last_modified": head.get("last_modified"), "etag_md5": head.get("etag_md5")}
    else:                                         # FE23: one GET, no HEAD of this URL
        rec["server"] = {"status_code": None, "content_length": None, "last_modified": None, "etag_md5": None,
                         "head": HEAD_NOT_MADE}

    def _get():
        kdir.mkdir(parents=True, exist_ok=True)
        try:
            got = NET["get"](t.url, part)
        except Exception as e:  # noqa: BLE001  FE19: classified in memory, re-raised to section 8's handler
            rec["fetch_failure"] = classify_get_failure(e)
            raise
        if got.get("url") != t.url or Path(got.get("path", "")) != part:
            raise DownloadRefused("download record")
        sha = PW.sha256_file(part)
        if sha != got.get("sha256") or part.stat().st_size != got.get("bytes"):
            raise DownloadRefused("download read-back")
        os.rename(part, path)
        return sha, path.stat().st_size
    sha, nbytes = PW.stage(em, "fetch:get", _get)
    em.register_saved(path)
    date = _utc_now()
    rec["fetch"] = {"source": "download", "path": path.as_posix(), "date_utc": date, "bytes": nbytes, "sha256": sha}
    em.say(f"fetch_extract: {t.key} fetched {nbytes} bytes sha256 {sha} to {path}")
    s = rec["server"]
    text = (f"\n## fetch_extract {date}\n- key: {t.key}\n- url: {t.url}\n- date_utc: {date}\n- bytes: {nbytes}\n"
            f"- sha256: {sha}\n- server: content_length {s['content_length'] if s['content_length'] is not None else 'none'}"
            f"; last_modified {s['last_modified'] or 'none'}; etag_md5 {s['etag_md5'] or 'none'}\n"
            f"- file: {path.as_posix()}\n")
    src = kdir / "SOURCE.md"
    em.allow.add_exact(src)
    PW.stage(em, "source-md", em.write_text, src, text, "identity", True)
    return path


def classify_get_failure(e: BaseException) -> dict:
    """FE19 (RUN_PLAN_amend_3 R45 (f)): fetch_util.get's failure as numbers only - CalledProcessError -> the curl exit
    code; RuntimeError 'HTTP <code> for <url>' -> the code (parsed in memory); RuntimeError for an HTML page -> html.
    The message text (it holds the URL) is never stored."""
    out = {"class": type(e).__name__}
    if isinstance(e, subprocess.CalledProcessError):
        out["curl_exit"] = int(e.returncode)
    elif isinstance(e, RuntimeError):
        msg = str(e)
        m = re.match(r"HTTP (\d{3}) for ", msg)
        if m:
            out["http_status"] = int(m.group(1))
        elif msg.startswith("HTML page returned for "):
            out["html"] = True
    return out


def _identity(t: Target, path: Path, em: PW.Emitter, rec: dict, roots_q: Path | None = None) -> bool:
    def _do():
        facts = ID.file_facts(path, quarantine_root=roots_q)
        refs = [dict(r) for r in t.refs]
        if t.pinned_sha256:
            refs.append({"basis": ID.BASIS_PINNED_SHA, "sha256": t.pinned_sha256, "bytes": t.pinned_bytes})
        elif t.pinned_bytes is not None:
            refs.append({"basis": ID.BASIS_PINNED_SIZE, "bytes": t.pinned_bytes})
        return facts, refs, ID.compare(facts, refs, at_download_ok=t.identity_at_download)
    facts, refs, cmp = PW.stage(em, "identity", _do)
    rec["identity"] = {"facts": facts, "references": refs, "comparison": cmp}
    bases = ", ".join(sorted({c["basis"] for c in cmp.get("checks", [])})) or "none"
    em.say(f"fetch_extract: {t.key} identity: {cmp['result']} (basis {bases})")
    return cmp["result"] in (ID.STATUS_MATCH, ID.STATUS_AT_DOWNLOAD)


def save_object(em: PW.Emitter, path: Path, obj, adopt_identical: bool = False) -> str:
    """Step 5: the group-level object (content: declared cells' values, keyed by runner-side names) -- its file name
    passes the allow-list, its content is not printed; written once, read back (bytes and parsed value). FE18 (WP3
    fix round 1, B2; opt-in, adopt_identical=True, the WP3 stage only): an object already saved with the SAME bytes (an
    earlier run's identical extraction) is adopted, never rewritten; different bytes are refused (FileExistsError). By
    default an existing object is refused as before (FE9)."""
    data = (json.dumps(obj, indent=1, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
    p = Path(path)
    if adopt_identical and p.exists():
        if PW.sha256_file(p) != PW.sha256_bytes(data):
            raise FileExistsError("saved object exists with other bytes")
        em.register_saved(p)
        return PW.sha256_file(p)
    sha = em.save_bytes(path, data)
    if json.loads(Path(path).read_bytes().decode("utf-8")) != json.loads(data.decode("utf-8")):
        raise OSError("read-back")
    return sha


def _same_volume(a: Path, b: Path) -> bool:
    b = Path(os.path.abspath(b))
    while not b.exists():
        b = b.parent
    da, db = os.path.splitdrive(os.path.abspath(a))[0].lower(), os.path.splitdrive(str(b))[0].lower()
    return da == db and os.stat(a).st_dev == os.stat(b).st_dev


def _inside(p: Path, d: Path) -> bool:
    a = os.path.normcase(os.path.abspath(p))
    b = os.path.normcase(os.path.abspath(d)).rstrip("\\/") + os.sep
    return a.startswith(b)


def source_md_quarantine_line(m: dict, date: str) -> str:
    """One SOURCE.md line for one entry of a quarantine move (fix round 5): a file move ('moved_to', 'sha256') or a
    whole-directory move (FE22: 'moved_to' - the runner-built quarantine directory -, 'carrier_sha256',
    'n_files_moved'). Raises KeyError on any other shape (inside the source-md stage)."""
    if "carrier_sha256" in m:
        return (f"- quarantined (the whole directory, RUN_PLAN_amend_3 section 8.1): {m['moved_to']} carrier sha256 "
                f"{m['carrier_sha256']}; files {m['n_files_moved']} ({date}); deletion requested\n")
    return f"- quarantined: {m['moved_to']} sha256 {m['sha256']} ({date}); deletion requested\n"


def source_md_quarantine_lines(moved: list, date: str) -> str:
    return "".join(source_md_quarantine_line(m, date) for m in moved)


def _quarantine(t: Target, roots: Roots, files: list[Path], em: PW.Emitter, rec: dict) -> None:
    qdir = roots.quarantine / t.gate / t.key
    em.allow.add_exact(qdir)
    moved = []
    if t.quarantine_dir is not None:                # FE22: the whole directory (section 8.1), same volume
        src_dir = Path(t.quarantine_dir)
        carrier = Path(t.local_path)

        def _move_dir():
            before = PW.sha256_file(carrier)
            rel = os.path.relpath(os.path.abspath(carrier), os.path.abspath(src_dir))
            if not _same_volume(src_dir, qdir):
                raise QuarantineRefused("not the same volume")
            if qdir.exists():
                raise QuarantineRefused("destination exists")
            qdir.parent.mkdir(parents=True, exist_ok=True)
            n_files = sum(1 for p in src_dir.rglob("*") if p.is_file())
            os.rename(src_dir, qdir)                # one rename on one volume: never a copy and a delete
            if src_dir.exists() or PW.sha256_file(qdir / rel) != before or \
                    sum(1 for p in qdir.rglob("*") if p.is_file()) != n_files:
                raise QuarantineRefused("sha256 re-check")
            return {"moved_to": qdir.as_posix(), "what": "the whole clone directory (RUN_PLAN_amend_3 section 8.1)",
                    "carrier_sha256": before, "carrier_bytes": (qdir / rel).stat().st_size,
                    "carrier_path_sha256": PW.sha256_text(Path(rel).as_posix()), "n_files_moved": n_files}
        moved.append(PW.stage(em, "quarantine", _move_dir))
        em.say(f"fetch_extract: {t.key} the whole directory quarantined to {qdir}; files {moved[0]['n_files_moved']}; "
               f"sha256 re-check pass")
        files = []

    def _move(f: Path):
        before = PW.sha256_file(f)
        pinned_copy = t.local_path is not None and Path(f) == Path(t.local_path)
        dest = qdir / (f"carrier{t.ext}" if pinned_copy else f.name)       # FE15: never the pinned copy's own name
        em.allow.add_exact(dest)
        if not _same_volume(f, qdir):
            raise QuarantineRefused("not the same volume")
        qdir.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            raise QuarantineRefused("destination exists")
        os.rename(f, dest)                      # a rename on one volume: never a copy and a delete
        if f.exists() or PW.sha256_file(dest) != before:
            raise QuarantineRefused("sha256 re-check")
        return {"moved_to": dest.as_posix(), "sha256": before, "bytes": dest.stat().st_size}
    for f in files:
        moved.append(PW.stage(em, "quarantine", _move, f))
        em.say(f"fetch_extract: {t.key} quarantined to {qdir}; sha256 re-check pass")
    req = {"schema": "a1_deletion_request_v1", "key": t.key, "gate": t.gate, "files": moved,
           "register": "claims_register.md:1096-1097",
           "operator_step": "deletion requested; operator-authorised step (default 24); the wrapper never deletes",
           "date_utc": _utc_now()}
    for k, v in t.deletion_extra:                   # FE22: fixed texts (section 8.1's request content)
        req[k] = v
    rpath = roots.control / t.gate / f"{t.key}_deletion_request.json"
    em.allow.add_exact(rpath)
    PW.stage(em, "quarantine", em.write_json, rpath, req, "identity")
    rec["quarantine"] = {"quarantined": moved, "deletion_request": rpath.as_posix()}
    src = roots.data / t.key / "SOURCE.md"
    if src.exists():
        em.allow.add_exact(src)
        # WP3 fix round 5: the lines are built INSIDE the stage (a fault is a recorded stage failure) and a whole-
        # directory move (FE22) has its own line - the runner-built quarantine path, the carrier's sha256, the file
        # count, the date, 'deletion requested' (no carrier-derived path component)
        PW.stage(em, "source-md", lambda: em.write_text(src, source_md_quarantine_lines(moved, _utc_now()),
                                                        "identity", True))
    em.say(f"fetch_extract: {t.key} deletion request raised (register section 1.10 (2); operator-authorised step); "
           f"record {rpath}")


# ----------------------------------------------------------------------------------------------------------------
# one target
# ----------------------------------------------------------------------------------------------------------------
def make_allow(t: Target, roots: Roots) -> PW.AllowList:
    allow = PW.AllowList(phrases=FE_PHRASES)
    keys = [t.key] + [d.key for d in t.sheets] + [m.key for m in t.members] + \
        [d.key for m in t.members for d in m.sheets] + \
        [c.key for d in list(t.sheets) + [s for m in t.members for s in m.sheets] for c in d.columns]
    allow.add_words(*keys)
    if t.url_note:             # FE23: a fixed note
        allow.add_words(*PW.words_of(t.url_note))
    if t.refusal_status:       # the target's own runner-built refusal reading is vocabulary of its record (fix round 1)
        allow.add_words(*PW.words_of(t.refusal_status))
    for d in t.sheets:          # FE20: a rule-declared sheet's status
        if d.name_status:
            allow.add_words(*PW.words_of(d.name_status))
    for k, v in t.deletion_extra:   # FE22: runner-built fixed texts
        allow.add_words(*PW.words_of(k), *PW.words_of(v))
    allow.add_identity(t.url)
    for m in t.members:
        if m.save_name:
            allow.add_exact(m.save_name)
    return allow


def refusal_status(t: Target, e: PW.StageFailed, rec: dict) -> str:
    """The status a refusal reads: a reading the runner noted at the refusal site (rec["refused_reason"]); a
    do-not-open declaration; for a target with a pinned refusal status (Moreau's layout status, R16's), any failure
    of a sheets / read / zip / tar stage; else "refused (stage failed)"."""
    if rec.get("refused_reason"):
        return rec["refused_reason"]
    if e.class_name == "DoNotOpen":
        return STATUS_DO_NOT_OPEN
    if t.refusal_status and e.stage.split(":")[0] in ("sheets", "read", "zip", "tar"):
        return t.refusal_status
    return STATUS_FAILED


def _record_path(roots: Roots, t: Target) -> Path:
    d = roots.records / t.gate
    p = d / f"{t.key}.json"
    n = 1
    while p.exists():                             # FE9
        n += 1
        p = d / f"{t.key}.{n}.json"
    return p


def run_target(t: Target, roots: Roots, *, out=None, err=None, reader=None, transform=None,
               adopt_identical: bool = False) -> dict:
    """Steps 0-6 for one target. Returns {"key", "gate", "status", ...} (vocabulary only). reader / transform: FE16."""
    _check_target(t)
    allow = make_allow(t, roots)
    em0 = PW.Emitter(allow, stream=out)
    ok, reason = gate_check(t, roots.repo)                        # step 0: before any request or file open
    if not ok:
        em0.say(f"fetch_extract: {t.key} gate {t.gate} CLOSED (reason {reason}); not fetched; no network request")
        return {"key": t.key, "gate": t.gate, "status": STATUS_GATE, "reason": reason}
    qdir = roots.quarantine / t.gate / t.key
    if qdir.exists():
        allow.add_exact(qdir)
        em0.say(f"fetch_extract: {t.key} carrier in quarantine at {qdir}; refused")
        return {"key": t.key, "gate": t.gate, "status": STATUS_IN_QUARANTINE}
    log = roots.logs / t.gate / f"{t.key}.log"
    allow.add_exact(log)
    em = PW.Emitter(allow, stream=out, log_path=log)
    em.say(f"fetch_extract: {t.key} gate {t.gate} open")
    rec: dict = {"schema": "a1_post_freeze_identity_v1", "key": t.key, "gate": t.gate, "url": t.url, "kind": t.kind,
                 "date_utc": _utc_now(), "pinned": {"pinned_bytes": t.pinned_bytes, "pinned_sha256": t.pinned_sha256}}
    if t.url_note:                                # FE23
        rec["url_note"] = t.url_note
    status = None
    result = {"key": t.key, "gate": t.gate}
    try:
        with PW.StdioGuard(allow, out=out, err=err) as sg, PW.quiet_warnings() as wc, PW.quiet_logging() as lc:
            try:
                status = PW.stage(em, "run", _body, t, roots, em, rec, reader, transform, adopt_identical)
            except PW.StageFailed as e:
                rec.update(failed_stage=e.stage, failed_class=e.class_name, failed_where=e.where)
                status = refusal_status(t, e, rec)
        rec["stdio_violations"], rec["stdio_passed"] = sg.violations, sg.passed
        rec["warnings"], rec["logging"] = dict(wc), dict(lc)
        if sg.violations:
            raise PW.PrintRuleViolation("stdio")
        rec["status"] = status
        rpath = _record_path(roots, t)
        allow.add_exact(rpath)
        PW.stage(em, "record", em.write_json, rpath, rec, "identity")
        em.say(f"fetch_extract: {t.key} record {rpath}")
        em.say(f"fetch_extract: {t.key} status {status}")
        result.update(status=status, record_path=rpath.as_posix())
    except PW.PrintRuleViolation:
        result.update(status=STATUS_INCIDENT, violations=em.n_violations)
        try:
            em.say(f"fetch_extract: {t.key} status {STATUS_INCIDENT}")
        except PW.PrintRuleViolation:
            pass
    result["written"] = [p.as_posix() for p in em.written]
    return result


def run_step6(t: Target, roots: Roots, *, reason: str, out=None, err=None) -> dict:
    """FE24 (RUN_PLAN_amend_3 R46 (h); fix round 3, B1): section 8 step 6 run ONCE for a pinned copy whose extraction an
    earlier pass verified and found identifier-bearing, after the last pass attempted (extracted, refused or skipped):
    the copy's identity re-checked (sha256 / size against the target's references), the move to the quarantine
    (same volume, sha256 re-checked), the deletion request, and an R18 record of its own (key t.key) - all inside the
    guards run_target uses (section 8's handler, the stdio guard, quiet warnings / logging)."""
    _check_target(t)
    if t.local_path is None:
        raise ValueError("step 6 alone is for a pinned copy")
    allow = make_allow(t, roots)
    allow.add_words(*PW.words_of(reason))
    log = roots.logs / t.gate / f"{t.key}.log"
    allow.add_exact(log)
    em = PW.Emitter(allow, stream=out, log_path=log)
    em.say(f"fetch_extract: {t.key} step 6 (run once after the last pass)")
    rec: dict = {"schema": "a1_post_freeze_identity_v1", "key": t.key, "gate": t.gate, "url": t.url, "kind": t.kind,
                 "date_utc": _utc_now(), "step6": reason}
    result = {"key": t.key, "gate": t.gate}
    try:
        with PW.StdioGuard(allow, out=out, err=err) as sg, PW.quiet_warnings() as wc, PW.quiet_logging() as lc:
            try:
                lp = Path(t.local_path)
                # fix round 4, item 5: a refusal of a quarantine path is a recorded stage failure, not a stop
                PW.stage(em, "quarantine", refuse_quarantine_path, lp, roots.quarantine)
                if not _identity(t, lp, em, rec, roots.quarantine):
                    status = rec["identity"]["comparison"]["result"]
                else:
                    rec["identifier_bearing"] = True
                    _quarantine(t, roots, [lp], em, rec)
                    status = STATUS_STEP6
            except PW.StageFailed as e:
                rec.update(failed_stage=e.stage, failed_class=e.class_name, failed_where=e.where)
                status = STATUS_FAILED
        rec["stdio_violations"], rec["stdio_passed"] = sg.violations, sg.passed
        rec["warnings"], rec["logging"] = dict(wc), dict(lc)
        if sg.violations:
            raise PW.PrintRuleViolation("stdio")
        rec["status"] = status
        rpath = _record_path(roots, t)
        allow.add_exact(rpath)
        PW.stage(em, "record", em.write_json, rpath, rec, "identity")
        em.say(f"fetch_extract: {t.key} record {rpath}")
        em.say(f"fetch_extract: {t.key} status {status}")
        result.update(status=status, record_path=rpath.as_posix())
    except PW.PrintRuleViolation:
        result.update(status=STATUS_INCIDENT, violations=em.n_violations)
    result["written"] = [p.as_posix() for p in em.written]
    return result


def _body(t: Target, roots: Roots, em: PW.Emitter, rec: dict, reader=None, transform=None,
          adopt_identical: bool = False) -> str:
    if t.kind == "tar_member":
        _objects, idb, _q = _read_tar(t, roots, em, rec)
        rec["identifier_bearing"] = idb
        if idb:                                   # FE11: the tarball is not stored; nothing to move
            rec["quarantine"] = {"note": "carrier not stored (stream); nothing quarantined"}
            em.say(f"fetch_extract: {t.key} screen hits on streamed names; carrier not stored (stream); nothing "
                   f"quarantined")
        return STATUS_EXTRACTED
    path = _fetch(t, roots, em, rec)
    if not _identity(t, path, em, rec, roots.quarantine):
        return rec["identity"]["comparison"]["result"]
    refuse_quarantine_path(path, roots.quarantine)
    q_files: list[Path] = []
    if t.kind == "workbook":
        objects, idb = _read_workbook(t.key, path, t.ext, t.sheets, t.do_not_open, em, rec)
    elif t.kind == "zip":
        objects, idb, q_files = _read_zip(t, path, roots, em, rec)
    elif reader is not None:                      # FE16
        objects = PW.stage(em, "read:file", reader, path)
        idb = False
    else:
        objects, idb = {}, False
    views = {k: o for k, o in (objects or {}).items() if type(o).__name__ == "PositionView"}
    if views and transform is None:               # FE20: a masked view is never saved as such
        _refuse(em, "transform:positions", LayoutRefused)
    if transform is not None and objects:         # FE16
        objects = PW.stage(em, "transform", transform, objects)
    if views:                                     # FE20: the positions each transform consumed
        rec["positions_consumed"] = {k: o.consumed() for k, o in views.items()}
        rec["positions_handed"] = {k: list(o.handed) for k, o in views.items()}
        if any(o.consumed() != list(o.handed) for o in views.values()):
            _refuse(em, "transform:positions", LayoutRefused)
    path_hits = ((rec.get("fetch") or {}).get("screen_hits") or {})
    idb = idb or t.per_participant or bool(path_hits.get("V", 0) + path_hits.get("N", 0))   # FE17
    rec["identifier_bearing"] = idb
    if objects:
        opath = roots.artifacts / t.gate / t.key / f"{t.key}_extract.json"
        em.allow.add_exact(opath)
        sha = PW.stage(em, "save", save_object, em, opath, {"schema": "a1_extract_v1", "key": t.key,
                                                             "objects": objects}, adopt_identical)
        rec["extraction"] = {"object_path": opath.as_posix(), "object_sha256": sha}
        em.say(f"fetch_extract: {t.key} saved object {opath} sha256 {sha}; read-back pass")
    if idb and t.defer_quarantine:                # FE21: the last pass runs step 6 once
        rec["quarantine"] = {"quarantined": [], "deferred": "step 6 runs once, after the last pass (R46 (h))"}
        em.say(f"fetch_extract: {t.key} identifier-bearing; step 6 deferred to the last pass")
    elif idb:
        _quarantine(t, roots, [path] + q_files, em, rec)
    return STATUS_EXTRACTED if objects else STATUS_IDENTITY_ONLY


# ----------------------------------------------------------------------------------------------------------------
# targets file and CLI
# ----------------------------------------------------------------------------------------------------------------
def _sheet_from(d: dict) -> SheetDecl:
    voc = ()
    if d.get("mode") == "mist64_matrix":
        voc = mist64_vocab(Path(d["vocab_json"])) if d.get("vocab_json") else mist64_vocab()
    return SheetDecl(key=d["key"], name=d["name"], mode=d.get("mode", "columns"), header_row=d.get("header_row"),
                     columns=tuple(Column(c["header"], c["key"], bool(c.get("numeric", False)))
                                   for c in d.get("columns", [])), vocab=voc)


def targets_from_json(path: Path, prefreeze: dict | None = None) -> list[Target]:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for d in doc["targets"]:
        refs = tuple(d.get("refs", []))
        if d.get("refs_from_prefreeze"):
            pf = prefreeze or ID.load_prefreeze(REPO / ID.IDENTITY_PREFREEZE_REL)
            refs += tuple(r for r in (ID.ref_from_probe(p) for p in ID.probes_for_url(pf, d["url"])) if r)
        members = tuple(MemberDecl(key=m["key"], match=m["match"], how=m.get("how", "exact"), ext=m.get("ext", ""),
                                   save_name=m.get("save_name"), kind=m.get("kind", "file"),
                                   sheets=tuple(_sheet_from(s) for s in m.get("sheets", [])),
                                   do_not_open=tuple(m.get("do_not_open", [])))
                        for m in d.get("members", []))
        out.append(Target(key=d["key"], gate=d["gate"], url=d["url"], kind=d["kind"], ext=d["ext"],
                          pinned_bytes=d.get("pinned_bytes"), pinned_sha256=d.get("pinned_sha256"), refs=refs,
                          identity_at_download=bool(d.get("identity_at_download", False)),
                          sheets=tuple(_sheet_from(s) for s in d.get("sheets", [])),
                          do_not_open=tuple(d.get("do_not_open", [])), members=members,
                          per_participant=bool(d.get("per_participant", False)),
                          refusal_status=d.get("refusal_status")))
    return out


def _excepthook(tp, value, tb):
    name = tp.__name__ if PW._WORD.fullmatch(tp.__name__ or "") else "UnlistedException"
    sys.__stdout__.write(f"fetch_extract: uncaught {name}; no detail printed\n")


def main(argv: list[str] | None = None) -> int:
    sys.excepthook = _excepthook
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--targets", required=True)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--repo")
    for r in ("data", "records", "artifacts", "logs", "control", "quarantine"):
        ap.add_argument(f"--{r}-root")
    a = ap.parse_args(argv)
    repo = Path(a.repo) if a.repo else (gates.git_toplevel(Path(__file__).resolve().parent) or REPO)
    roots = Roots.production(repo)
    for r in ("data", "records", "artifacts", "logs", "control", "quarantine"):
        v = getattr(a, f"{r}_root")
        if v:
            setattr(roots, r, Path(v))
    targets = targets_from_json(Path(a.targets))
    if a.only:
        targets = [t for t in targets if t.key in set(a.only)]
    code = 0
    for t in targets:
        try:
            res = run_target(t, roots)
        except KeyboardInterrupt:
            sys.__stdout__.write("fetch_extract: KeyboardInterrupt; stopped\n")
            return 130
        if res["status"] == STATUS_INCIDENT:
            return 4
        if res["status"] not in (STATUS_EXTRACTED, STATUS_IDENTITY_ONLY):
            code = 3
    return code


if __name__ == "__main__":
    sys.exit(main())
