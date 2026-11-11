"""P21 (arcs/audit/RUN_PLAN.md v3.1 section 7 row P21; section 2.2 "Simulated", "Plants (P21)"): the G1 fail-closed check
and the gate launcher, plus the G2 check (section 2.1).

    cd arcs/audit/src
    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_gates_p21 [--scratch DIR] [--repo PATH] [--keep]

Part A  the 40 cases of P21 as extended by RUN_PLAN_amend_1.md v2.1 Correction 1 (35 -> 40): the 35 of section 2.2
        "P21 in scratch git repositories (v3.1 re-run)" plus the amendment's five supersession variants (R33-R37);
        3 correct records open, 37 refused; each case is a fresh scratch git repository (NOTICE commit
        2026-09-29T16:55:40+02:00, session-message commit 2026-09-30T08:06:53+02:00, record commit
        2026-10-01T16:10:42+02:00, record-file commit). Each case also names the check step expected to refuse it, so a
        case refused for the wrong reason fails.
Part A' extra cases for the readings gates.py makes where the frozen text leaves a corner open (not counted in 40).
Part B  the gate launcher: with G1 closed it starts nothing (a sentinel command would create a file; --carrier-test
        resolves to a FAKE scratch carrier_test.py that would also create one); with G1 open it runs them.
Part C  G2: step3v_open on scratch repositories.
Part D  the REAL repository, read-only: g1_open and step3v_open True at the current HEAD.
Part E  fetch_extract.py with G1 closed: deferred (WP3, section 8).
Part F  the 35 cases against an emulation of v3's spec: exactly the 7 cases v3.1 added must flip (the cases catch a
        gate with v3's defects; section 2.2 lines 254-258).
Part G  the 40 cases against an emulation of the frozen v3.1 match (case-sensitive, white space collapsed, not
        deleted): exactly the 5 cases Correction 1 added must flip (the cases catch a gate without Correction 1). Also
        Correction 1's declared residual (fullwidth colon, fullwidth letters, U+2011 / U+2013 in "b-ii") is shown NOT
        matched, and the record block's own checks stay exact (a lower-case marker line inside the block is refused).
Part H  (asdg-skeptic WP1 review, C1) Correction 1's Unicode white space: extra cases X19-X23 (tab, NBSP, em space,
        ideographic space, thin space and U+2028 placed where the marker has no white space) are refused; the v3.1
        emulation opens all five, an ASCII-only white-space Correction 1 opens every non-ASCII case (X20-X23, X07,
        X13; the tab case X19 stays refused), and a supersession scan on Unicode line boundaries opens X23.

All scratch repositories live under --scratch (default: a new temporary directory) and are removed on success unless
--keep. Every text is synthetic; no participant or sample identifier of any form is written or printed. The scratch
commits use a synthetic identity and an empty global git config. Exit code 0 iff every check passed.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from a1_audit import gate_launch, gates

SRC_DIR = Path(__file__).resolve().parents[2]          # arcs/audit/src
FAILS: list[str] = []

# The strings below are typed here independently of gates.py's constants (so a wrong constant there is caught by the
# real-repository part D and by these scratch histories disagreeing with it).
NOTICE_LINE = "**NOTICE (amendment 2 §4b) - the (b-ii)-declined record, synthetic notice text of session 9.**"
DUE_LINE = ('   the "(b-ii) declined" record is due in the next operator-opened session (synthetic NOTICE given '
            '2026-09-29, A3 ARC).')
M1, M2 = "RECORD: (b-ii) declined", "RECORD: no ABIDE II analysis will run"
MSG_SHA = hashlib.sha256(b"synthetic operator opening message (P21 scratch)").hexdigest()
STD_OPENED = "2026-10-01T11:43:09Z"
T_NOTICE, T_MSG, T_RECORD = "2026-09-29T16:55:40+02:00", "2026-09-30T08:06:53+02:00", "2026-10-01T16:10:42+02:00"
T_MSG_LATE, T_NEXT, T_RECFILE = "2026-10-01T16:11:00+02:00", "2026-10-01T16:11:30+02:00", "2026-10-01T16:12:00+02:00"
BLOCK_FIRST_TEXT = "Synthetic: operator-opened session; the record follows."


def check(cond: bool, label: str) -> bool:
    if not cond:
        FAILS.append(label)
        print(f"  FAIL {label}")
    return cond


# ----------------------------------------------------------------------------------------------------------------
# scratch git plumbing (the test's own git: synthetic identity, no system / global config, dates pinned)
# ----------------------------------------------------------------------------------------------------------------
class Git:
    def __init__(self, scratch: Path):
        self.scratch = scratch
        cfg = scratch / "empty_global_gitconfig"
        cfg.write_bytes(b"")
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
        env.update(GIT_CONFIG_GLOBAL=str(cfg), GIT_CONFIG_NOSYSTEM="1", GIT_AUTHOR_NAME="p21 scratch",
                   GIT_AUTHOR_EMAIL="p21@scratch.invalid", GIT_COMMITTER_NAME="p21 scratch",
                   GIT_COMMITTER_EMAIL="p21@scratch.invalid", GIT_TERMINAL_PROMPT="0")
        self.env = env

    def run(self, repo: Path, *args: str, date: str | None = None) -> str:
        env = dict(self.env)
        if date is not None:
            env.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
        p = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, env=env, timeout=120)
        if p.returncode != 0:
            raise RuntimeError(f"scratch git {args[0]} failed: {p.stderr.decode('utf-8', 'replace')[:300]}")
        return p.stdout.decode("utf-8")

    def init(self, repo: Path) -> None:
        repo.mkdir(parents=True)
        self.run(repo, "init", "-q", "-b", "master")
        self.run(repo, "config", "core.autocrlf", "false")
        self.run(repo, "config", "commit.gpgsign", "false")

    def commit(self, repo: Path, date: str, msg: str, files: dict[str, bytes | None]) -> str:
        for rel, data in files.items():
            p = repo / rel
            if data is None:
                p.unlink()
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
                if p.read_bytes() != data:                         # a writer reads back what it wrote
                    raise RuntimeError("scratch write read-back")
        self.run(repo, "add", "-A")
        self.run(repo, "commit", "-q", "--no-verify", "-m", msg, date=date)
        cid = self.run(repo, "rev-parse", "HEAD").strip()
        got = self.run(repo, "show", "-s", "--format=%cI", cid).strip()
        if got != date:                                             # the pinned committer date is what git holds
            raise RuntimeError(f"scratch commit date {got} != {date}")
        return cid


def lf(lines: list[str]) -> bytes:
    return "\n".join(lines).encode("utf-8")


def insert_before_results(lines: list[str], new: list[str]) -> list[str]:
    i = lines.index("## Results")
    return lines[:i] + new + lines[i:]


def replace_line(old: str, new: str | None) -> Callable[[list[str]], list[str]]:
    def f(lines: list[str]) -> list[str]:
        if old not in lines:
            raise RuntimeError("scratch transform: line not found")
        out = []
        for ln in lines:
            if ln == old:
                if new is not None:
                    out.append(new)
            else:
                out.append(ln)
        return out
    return f


def add_session(heading: str, body: list[str]) -> Callable[[list[str]], list[str]]:
    return lambda lines: insert_before_results(lines, [heading, *body, ""])


@dataclass
class Spec:
    opened: str = STD_OPENED
    notice_sid: str = "synthetic-notice-session-a"
    opened_sid: str = "synthetic-opened-session-b"
    block_fn: Callable[[list[str]], list[str]] | None = None
    msg_has_due: bool = True
    msg_after_record: bool = False
    record_over: dict = field(default_factory=dict)
    bii_fn: Callable[[str], object] | None = None
    raw_record: str | None = None          # literal JSON text; "{c}" -> the record commit id
    commit_record: bool = True
    placeholder_then_local_edit: bool = False
    record_names_next: bool = False
    side_branch: bool = False
    crlf_at_c: bool = False
    after: list[Callable[[list[str]], list[str]] | str] = field(default_factory=list)   # "delete_arc" allowed


ARC = "arcs/replication/ARC.md"
NEXT = "NEXT_SESSION.md"
REC = "arcs/audit/run_manifests/G1/g1_open_record.json"


def base_arc() -> list[str]:
    return ["# A3 - scratch arc (P21 simulation; synthetic text)", "", "## Prereg", "Synthetic prereg line.", "",
            "## Post-freeze record", "", "### 2026-09-26 - session 8", "Synthetic session-8 line.", "",
            "### 2026-09-29 - session 9", "Synthetic session-9 line.", NOTICE_LINE,
            "#### A deeper heading inside session 9", "Synthetic line inside session 9.", ""]


def block(spec: Spec) -> list[str]:
    b = ["### 2026-10-01 - session 10", BLOCK_FIRST_TEXT, "", M1, M2, "",
         f"NOTICE-SESSION: {spec.notice_sid}",
         f"OPERATOR-OPENED: session {spec.opened_sid}; opened {spec.opened}; message sha256 {MSG_SHA}",
         "#### A deeper heading inside session 10 (stays inside the section)", "Synthetic line.", ""]
    return spec.block_fn(b) if spec.block_fn else b


RESULTS = ["## Results", "### P4 synthetic result", "Synthetic result line.", ""]
NEXT_SESSION_TEXT = ["# Next session (synthetic)", "", "2. **ABIDE II (b-ii).** Synthetic text.", None,
                     "   (synthetic handoff continues)", ""]


def build(g: Git, repo: Path, spec: Spec, fake_carrier: bool = False) -> dict:
    """Build one scratch history; returns the commit ids it made."""
    g.init(repo)
    ids: dict[str, str] = {}
    arc = base_arc()
    ids["notice"] = g.commit(repo, T_NOTICE, "NOTICE commit (synthetic session 9)", {ARC: lf(arc)})
    msg_lines = [ln if ln is not None else (DUE_LINE if spec.msg_has_due else "   (synthetic: no due line)")
                 for ln in NEXT_SESSION_TEXT]
    if not spec.msg_after_record:
        ids["msg"] = g.commit(repo, T_MSG, "session-message commit (synthetic handoff)", {NEXT: lf(msg_lines)})
    if spec.side_branch:
        g.run(repo, "checkout", "-q", "-b", "side")
    arc_c = arc + block(spec) + RESULTS                         # session 9 ends with "", the block, ## Results
    data_c = lf(arc_c)
    if spec.crlf_at_c:
        data_c = data_c.replace(b"\n", b"\r\n")
    ids["record"] = g.commit(repo, T_RECORD, "record commit (synthetic session 10 block)", {ARC: data_c})
    arc_now = arc_c
    if spec.side_branch:
        g.run(repo, "checkout", "-q", "master")
        arc_now = arc
    if spec.msg_after_record:
        ids["msg"] = g.commit(repo, T_MSG_LATE, "session-message commit after the record", {NEXT: lf(msg_lines)})
    named = ids["record"]
    if spec.record_names_next:
        arc_now = arc_now + ["### Synthetic next results entry", "Synthetic line.", ""]
        ids["next"] = g.commit(repo, T_NEXT, "a commit after the record", {ARC: lf(arc_now)})
        named = ids["next"]
    bii = spec.bii_fn(named) if spec.bii_fn else named
    doc = {"record": "(b-ii) declined", "route": "ii", "bii_commit": bii, "a3_arc_session": 10}
    doc.update(spec.record_over)
    rec_text = (spec.raw_record.replace("{c}", named) if spec.raw_record is not None
                else json.dumps(doc, indent=1) + "\n")
    arc_now = arc_now + ["### G1 synthetic later results entry", "Synthetic line.", ""]   # as e49a024 did
    files: dict[str, bytes | None] = {ARC: lf(arc_now)}
    if spec.placeholder_then_local_edit:
        ph = dict(doc, bii_commit="<commit of the record, filled by the orchestrator>")
        files[REC] = (json.dumps(ph, indent=1) + "\n").encode("utf-8")
    elif spec.commit_record:
        files[REC] = rec_text.encode("utf-8")
    ids["recfile"] = g.commit(repo, T_RECFILE, "record-file commit", files)
    if spec.placeholder_then_local_edit or not spec.commit_record:
        (repo / REC).parent.mkdir(parents=True, exist_ok=True)
        (repo / REC).write_bytes(rec_text.encode("utf-8"))      # the working copy only
    for i, fn in enumerate(spec.after):
        date = f"2026-10-02T09:{i:02d}:00+02:00"
        if fn == "delete_arc":
            g.commit(repo, date, "later commit deleting ARC.md", {ARC: None})
            continue
        arc_now = fn(arc_now)
        g.commit(repo, date, "later A3 ARC commit", {ARC: lf(arc_now)})
    if fake_carrier:
        p = repo / gate_launch.CARRIER_TEST_REL
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"import pathlib, sys\n"
                      b"w = pathlib.Path(sys.argv[sys.argv.index('--workdir') + 1])\n"
                      b"(w / 'carrier_sentinel.txt').write_bytes(b'fake carrier ran')\n")
    ids["head"] = g.run(repo, "rev-parse", "HEAD").strip()
    return ids


# ----------------------------------------------------------------------------------------------------------------
# Part A: the 35 cases (RUN_PLAN.md section 2.2, lines 275-291) and Part A': extra readings
# ----------------------------------------------------------------------------------------------------------------
def unknown_id(c: str) -> str:
    return ("0" if c[0] != "0" else "1") + c[1:]


def cases_35() -> list[tuple[str, str, Spec, bool, str]]:
    sess = lambda h: add_session(h, ["Synthetic later session line."])   # noqa: E731
    return [
        ("P01", "standard record, opened 2026-10-01T11:43:09Z", Spec(), True, "open"),
        ("P02", "opened 2026-09-30T06:30:00Z (local-clock string compare would refuse)",
         Spec(opened="2026-09-30T06:30:00Z"), True, "open"),
        ("P03", "opened 2026-09-30T08:30:00+02:00", Spec(opened="2026-09-30T08:30:00+02:00"), True, "open"),
        ("R01", "placeholder bii_commit", Spec(bii_fn=lambda c: "<40-hex commit of A3's (b-ii)-declined record>"),
         False, "bii_commit_not_hex"),
        ("R02", "upper-case id", Spec(bii_fn=lambda c: c.upper()), False, "bii_commit_not_hex"),
        ("R03", "39-hex id", Spec(bii_fn=lambda c: c[:39]), False, "bii_commit_not_hex"),
        ("R04", "unknown commit (40-hex, not in the repository)", Spec(bii_fn=unknown_id), False,
         "bii_commit_unknown"),
        ("R05", "non-ancestor (record commit on an unmerged branch)", Spec(side_branch=True), False,
         "bii_commit_not_ancestor"),
        ("R06", "a3_arc_session 9", Spec(record_over={"a3_arc_session": 9}), False, "session_number"),
        ("R07", "record block under a session-9 heading",
         Spec(block_fn=lambda b: ["### 2026-10-01 - session 9"] + b[1:]), False, "section_missing_at_c"),
        ("R08", "block edited at HEAD", Spec(after=[replace_line(BLOCK_FIRST_TEXT, BLOCK_FIRST_TEXT[:-1] +
                                                                   " (edited at HEAD).")]),
         False, "section_changed_at_head"),
        ("R09", "missing marker line", Spec(block_fn=replace_line(M2, None)), False, "marker_missing"),
        ("R10", "block already in c^ (record names the next commit)", Spec(record_names_next=True), False,
         "marker_in_parent"),
        ("R11", "missing OPERATOR-OPENED line",
         Spec(block_fn=lambda b: [x for x in b if not x.startswith("OPERATOR-OPENED:")]), False,
         "operator_opened_line"),
        ("R12", "missing NOTICE-SESSION line",
         Spec(block_fn=lambda b: [x for x in b if not x.startswith("NOTICE-SESSION:")]), False,
         "notice_session_line"),
        ("R13", "two OPERATOR-OPENED lines",
         Spec(block_fn=lambda b: [y for x in b for y in ([x, x.replace("11:43:09Z", "11:50:00Z")]
                                                         if x.startswith("OPERATOR-OPENED:") else [x])]),
         False, "operator_opened_line"),
        ("R14", "equal session ids", Spec(opened_sid="synthetic-notice-session-a"), False, "session_ids_equal"),
        ("R15", "opened before the NOTICE commit (2026-09-29T16:50+02:00)", Spec(opened="2026-09-29T16:50+02:00"),
         False, "opened_too_early"),
        ("R16", "opened before the NOTICE commit (2026-09-29T14:00Z)", Spec(opened="2026-09-29T14:00Z"), False,
         "opened_too_early"),
        ("R17", "after NOTICE, before session message (2026-09-29T17:00+02:00)",
         Spec(opened="2026-09-29T17:00+02:00"), False, "opened_too_early"),
        ("R18", "after NOTICE, before session message (2026-09-30T08:00+02:00)",
         Spec(opened="2026-09-30T08:00+02:00"), False, "opened_too_early"),
        ("R19", "no session message in c's history", Spec(msg_has_due=False), False, "no_session_message_commit"),
        ("R20", "session message committed only after the record", Spec(msg_after_record=True), False,
         "no_session_message_commit"),
        ("R21", "attestation without a UTC offset", Spec(opened="2026-10-01T11:43:09"), False, "opened_no_offset"),
        ("R22", "attestation after the record commit (2026-10-01T14:30:00Z)", Spec(opened="2026-10-01T14:30:00Z"),
         False, "opened_too_late"),
        ("R23", "later '(b-ii) commissioned' at a line start",
         Spec(after=[add_session("### 2026-10-02 - session 11", ["RECORD: (b-ii) commissioned"])]), False,
         "superseded"),
        ("R24", "later 'delegation revoked' at a line start",
         Spec(after=[add_session("### 2026-10-02 - session 11", ["RECORD: delegation revoked"])]), False,
         "superseded"),
        ("R25", "marker mid-line in bold",
         Spec(after=[add_session("### 2026-10-02 - session 11",
                                 ["The operator wrote: **RECORD: (b-ii) commissioned** by the operator."])]),
         False, "superseded"),
        ("R26", "marker with emphasis inside it",
         Spec(after=[add_session("### 2026-10-02 - session 11", ["**RECORD:** (b-ii) commissioned"])]), False,
         "superseded"),
        ("R27", "marker mid-line in backticks",
         Spec(after=[add_session("### 2026-10-02 - session 11",
                                 ["Quoted mid-line: `RECORD: delegation revoked` in backticks."])]), False,
         "superseded"),
        ("R28", "route 'i'", Spec(record_over={"route": "i"}), False, "route_or_record"),
        ("R29", "route 'iii'", Spec(record_over={"route": "iii"}), False, "route_or_record"),
        ("R30", "record not committed (working copy only)", Spec(commit_record=False), False, "record_unreadable"),
        ("R31", "session-9 NOTICE removed at HEAD",
         Spec(after=[replace_line(NOTICE_LINE, "Synthetic session-9 line (the notice was removed).")]), False,
         "notice_missing_at_head"),
        ("R32", "session-10 heading twice at HEAD",
         Spec(after=[sess("### 2026-10-01 - session 10")]), False, "section_not_unique_at_head"),
    ]


# RUN_PLAN_amend_1.md v2.1 Correction 1, "Facts": the five variants that leave G1 open under the frozen rule
AMEND1_VARIANTS = ("record: (b-ii) commissioned", "Record: Delegation Revoked",
                   "**RECORD:** (B-II) COMMISSIONED by the operator", "RECORD:(b-ii) commissioned",
                   "RECORD : delegation revoked")


def cases_amend1() -> list[tuple[str, str, Spec, bool, str]]:
    """The 5 refusals RUN_PLAN_amend_1 Correction 1 adds to P21 (35 -> 40)."""
    return [(f"R{33 + i}", f"Correction 1 variant {i + 1}: later {v!r}",
             Spec(after=[add_session("### 2026-10-02 - session 11", [v])]), False, "superseded")
            for i, v in enumerate(AMEND1_VARIANTS)]


def cases_40() -> list[tuple[str, str, Spec, bool, str]]:
    return cases_35() + cases_amend1()


def cases_extra() -> list[tuple[str, str, Spec, bool, str]]:
    sess = lambda h, body: add_session(h, body)   # noqa: E731
    return [
        ("X01", "heading 'session 010' at c (non-canonical form)",
         Spec(block_fn=lambda b: ["### 2026-10-01 - session 010"] + b[1:]), False, "section_missing_at_c"),
        ("X02", "second session-10 heading at HEAD with another date",
         Spec(after=[sess("### 2026-10-02 - session 10", ["Synthetic."])]), False, "section_not_unique_at_head"),
        ("X03", "session-10 heading in non-ASCII digits added at HEAD",
         Spec(after=[sess("### 2026-10-02 - session ١٠", ["Synthetic."])]), False,
         "section_not_unique_at_head"),
        ("X04", "duplicate JSON key in the record ('route' twice)",
         Spec(raw_record='{"record": "(b-ii) declined", "route": "iii", "route": "ii", "bii_commit": "{c}", '
                         '"a3_arc_session": 10}\n'), False, "record_unreadable"),
        ("X05", "a3_arc_session 10.0 (not an int)", Spec(record_over={"a3_arc_session": 10.0}), False,
         "session_number"),
        ("X06", "HEAD holds a placeholder record, working copy edited to a valid one",
         Spec(placeholder_then_local_edit=True), False, "bii_commit_not_hex"),
        ("X07", "supersession marker with NBSP and a white-space run",
         Spec(after=[sess("### 2026-10-02 - session 11", ["RECORD:  (b-ii)\t  commissioned"])]), False,
         "superseded"),
        ("X08", "ARC.md with CRLF line endings at c", Spec(crlf_at_c=True), False, "section_missing_at_c"),
        ("X09", "unparseable OPERATOR-OPENED time", Spec(opened="yesterday-afternoon"), False, "opened_unparseable"),
        ("X10", "lower-case 'record: (b-ii) commissioned' at HEAD (RUN_PLAN_amend_1 Correction 1: case-insensitive; "
                "e7029ed opened it)", Spec(after=[sess("### 2026-10-02 - session 11",
                                                       ["record: (b-ii) commissioned"])]),
         False, "superseded"),
        ("X11", "A3 ARC.md deleted at HEAD", Spec(after=["delete_arc"]), False, "arc_unreadable"),
        ("X12", "a3_arc_session true (bool)", Spec(record_over={"a3_arc_session": True}), False, "session_number"),
        # RUN_PLAN_amend_1 Correction 1: Unicode white space deleted (em space, tab, NBSP) -> refused
        ("X13", "marker with an em space, a tab and an NBSP (Correction 1: every \\s deleted)",
         Spec(after=[sess("### 2026-10-02 - session 11", ["RECORD: (b-ii)\t commissioned"])]), False,
         "superseded"),
        # Correction 1's declared residual (NOT matched; NFKC and dash folding not added): documents the reading
        ("X14", "residual: fullwidth colon U+FF1A (declared, not matched)",
         Spec(after=[sess("### 2026-10-02 - session 11", ["RECORD： (b-ii) commissioned"])]), True, "open"),
        ("X15", "residual: fullwidth letters (declared, not matched)",
         Spec(after=[sess("### 2026-10-02 - session 11", ["ＲＥＣＯＲＤ: (b-ii) commissioned"])]),
         True, "open"),
        ("X16", "residual: non-breaking hyphen U+2011 in 'b-ii' (declared, not matched)",
         Spec(after=[sess("### 2026-10-02 - session 11", ["RECORD: (b‑ii) commissioned"])]), True, "open"),
        ("X17", "residual: en dash U+2013 in 'b-ii' (declared, not matched)",
         Spec(after=[sess("### 2026-10-02 - session 11", ["RECORD: (b–ii) commissioned"])]), True, "open"),
        # Correction 1 leaves the record block's own checks exact: a lower-case marker line in the block is refused
        ("X18", "record block's marker line in lower case (block checks stay exact)",
         Spec(block_fn=replace_line(M1, M1.lower())), False, "marker_missing"),
    ] + cases_unicode_ws()


# asdg-skeptic WP1 review C1: Correction 1's white-space deletion with tab, NBSP, em space and other Unicode white
# space placed where the marker has NO white space (so only the deletion, not section 2.2's collapse, makes them match)
UNICODE_WS_VARIANTS = (
    ("X19", "tab before the colon", "RECORD\t: (b-ii) commissioned"),
    ("X20", "NBSP (U+00A0) before the colon", "RECORD : delegation revoked"),
    ("X21", "em space (U+2003) after the colon, no space before 'commissioned', lower case",
     "record: (b-ii)commissioned"),
    ("X22", "em space, tab, NBSP inside '(b-ii)' and an ideographic space (U+3000), mixed case",
     "Record :\t(B- II)　Commissioned"),
    ("X23", "line separator (U+2028, white space inside an LF line) and thin space (U+2009)",
     "RECORD :delegation revoked"),
)


def cases_unicode_ws() -> list[tuple[str, str, Spec, bool, str]]:
    return [(cid, f"Correction 1, Unicode white space: {desc}",
             Spec(after=[add_session("### 2026-10-02 - session 11", [text])]), False, "superseded")
            for cid, desc, text in UNICODE_WS_VARIANTS]


def run_cases(g: Git, root: Path, cases, title: str) -> tuple[int, int, dict[str, Path]]:
    print(f"\n{title}")
    print(f"  {'id':<4} {'expected':<8} {'observed':<8} {'reason (observed)':<28} {'as expected':<11} case")
    n_ok, repos = 0, {}
    for cid, desc, spec, exp_open, exp_reason in cases:
        repo = root / cid
        ids = build(g, repo, spec, fake_carrier=True)
        ok, reason, info = gates.g1_check(repo)
        pub = gates.g1_open(repo)
        good = (ok is exp_open and pub is exp_open and reason == exp_reason and reason in gates.G1_REASONS)
        if exp_open:   # apparatus: the walk found the scratch NOTICE and session-message commits, c is the record
            good = good and info.get("notice_commit") == ids["notice"] and \
                info.get("session_message_commit") == ids["msg"] and info.get("bii_commit") == ids["record"]
        n_ok += good
        repos[cid] = repo
        print(f"  {cid:<4} {'open' if exp_open else 'refused':<8} {'open' if ok else 'refused':<8} "
              f"{reason:<28} {'yes' if good else 'NO':<11} {desc}")
        check(good, f"{cid} expected {'open' if exp_open else 'refused'}/{exp_reason}, got {ok}/{reason}")
    print(f"  -> {n_ok} / {len(cases)} as expected")
    return n_ok, len(cases), repos


# ----------------------------------------------------------------------------------------------------------------
# Part B: the launcher
# ----------------------------------------------------------------------------------------------------------------
_NAME = r"(?:[A-Za-z0-9._+-]+|<unprintable-name>)"
LAUNCH_LINE = re.compile(r"^gate_launch: (gate G[12] open|gate G[12] CLOSED \(reason [a-z_]+\); command not started|"
                         rf"starting {_NAME}|{_NAME} exit code -?\d+|{_NAME} could not be started|usage: .*)$")


def launch(args: list[str], cwd: Path = SRC_DIR) -> tuple[int, list[str]]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC_DIR)
    p = subprocess.run([sys.executable, "-X", "utf8", "-m", "a1_audit.gate_launch", *args], cwd=str(cwd),
                       capture_output=True, env=env, timeout=300)
    out = p.stdout.decode("utf-8", "replace").splitlines()
    check(all(LAUNCH_LINE.fullmatch(x) for x in out), "launcher printed a line outside its fixed vocabulary")
    check(b"Traceback" not in p.stderr, "launcher raised")
    return p.returncode, out


def sentinel_cmd(path: Path) -> list[str]:
    return [sys.executable, "-c", "import pathlib, sys; pathlib.Path(sys.argv[1]).write_bytes(b'ran')", str(path)]


def part_b(scratch: Path, closed_repo: Path, open_repo: Path, real_repo: Path, g2_closed_repo: Path) -> None:
    print("\nPart B: gate launcher (python -m a1_audit.gate_launch)")
    sd = scratch / "sentinels"
    sd.mkdir()

    s1 = sd / "b1.txt"
    code, out = launch(["G1", "--repo", str(closed_repo), "--", *sentinel_cmd(s1)])
    r = check(code == gate_launch.EXIT_REFUSED and not s1.exists(), "B1 G1 closed: sentinel command refused")
    print(f"  B1 G1 closed (R23 repo), sentinel command: exit {code}, sentinel created {s1.exists()} -> "
          f"{'refused, no subprocess' if r else 'FAIL'}")

    w2 = sd / "b2"
    w2.mkdir()
    code, out = launch(["G1", "--repo", str(closed_repo), "--carrier-test", "selftest", "--workdir", str(w2)])
    made = (w2 / "carrier_sentinel.txt").exists()
    r = check(code == gate_launch.EXIT_REFUSED and not made, "B2 G1 closed: --carrier-test refused")
    print(f"  B2 G1 closed, --carrier-test (FAKE scratch carrier_test.py): exit {code}, sentinel created {made} -> "
          f"{'refused, not started' if r else 'FAIL'}")

    # in-process: the spawn function raises if called; a refusal never reaches it
    calls: list[list[str]] = []
    orig = gate_launch._spawn

    def raiser(cmd):
        calls.append(cmd)
        raise AssertionError("spawn called with the gate closed")
    gate_launch._spawn = raiser
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            c1 = gate_launch.main(["G1", "--repo", str(closed_repo), "--", "x"])
            c2 = gate_launch.main(["G1", "--repo", str(closed_repo), "--carrier-test", "selftest"])
    finally:
        gate_launch._spawn = orig
    r = check(c1 == c2 == gate_launch.EXIT_REFUSED and calls == [], "B3 in-process: spawn not called when closed")
    print(f"  B3 in-process, spawn replaced by a raiser, G1 closed: exits {c1}/{c2}, spawn calls {len(calls)} -> "
          f"{'ok' if r else 'FAIL'}")

    s4 = sd / "b4.txt"
    code, out = launch(["G1", "--repo", str(open_repo), "--", *sentinel_cmd(s4)])
    r = check(code == 0 and s4.exists(), "B4 G1 open: sentinel command ran")
    print(f"  B4 G1 open (P01 repo), sentinel command: exit {code}, sentinel created {s4.exists()} -> "
          f"{'ran' if r else 'FAIL'}")

    w5 = sd / "b5"
    w5.mkdir()
    code, out = launch(["G1", "--repo", str(open_repo), "--carrier-test", "selftest", "--workdir", str(w5)])
    made = (w5 / "carrier_sentinel.txt").exists()
    r = check(code == 0 and made and "gate_launch: starting carrier_test.py" in out,
              "B5 G1 open: --carrier-test resolved to <repo>/arcs/audit/src_register/carrier_test.py and ran")
    print(f"  B5 G1 open, --carrier-test (FAKE scratch carrier_test.py): exit {code}, sentinel created {made} -> "
          f"{'resolved and ran' if r else 'FAIL'}")

    code, out = launch(["G1", "--repo", str(open_repo), "--", sys.executable, "-c", "import sys; sys.exit(7)"])
    r = check(code == 7 and out[-1].endswith("exit code 7"), "B6 child exit code returned")
    print(f"  B6 G1 open, child exits 7: launcher exit {code} -> {'propagated' if r else 'FAIL'}")

    s7 = sd / "b7.txt"
    code, out = launch(["G1", "--", *sentinel_cmd(s7)], cwd=closed_repo)
    s8 = sd / "b8.txt"
    code8, out8 = launch(["G1", "--", *sentinel_cmd(s8)], cwd=open_repo)
    r = check(code == gate_launch.EXIT_REFUSED and not s7.exists() and code8 == 0 and s8.exists(),
              "B7 default repo = git toplevel of the CWD")
    print(f"  B7 no --repo (CWD = closed repo / open repo): exits {code}/{code8}, sentinels {s7.exists()}/"
          f"{s8.exists()} -> {'ok' if r else 'FAIL'}")

    s9 = sd / "b9.txt"
    code, out = launch(["G2", "--repo", str(g2_closed_repo), "--", *sentinel_cmd(s9)])
    r = check(code == gate_launch.EXIT_REFUSED and not s9.exists(), "B8 G2 closed: refused")
    print(f"  B8 G2 closed (scratch, no 4efbae5): exit {code}, sentinel created {s9.exists()} -> "
          f"{'refused' if r else 'FAIL'}")

    s10 = sd / "b10.txt"
    code, out = launch(["G2", "--repo", str(real_repo), "--", *sentinel_cmd(s10)])
    r = check(code == 0 and s10.exists(), "B9 G2 open on the real repository (read-only check)")
    print(f"  B9 G2 on the REAL repository (read-only check), sentinel in scratch: exit {code}, sentinel created "
          f"{s10.exists()} -> {'ran' if r else 'FAIL'}")

    bad = [["G2", "--repo", str(open_repo), "--carrier-test", "selftest"], ["G1", "--repo", str(open_repo), "x"],
           ["G3", "--", "x"], [], ["G1", "--repo", str(open_repo), "--"]]
    codes = [launch(a)[0] for a in bad]
    r = check(all(c == gate_launch.EXIT_USAGE for c in codes), "B10 malformed command lines refused")
    print(f"  B10 malformed command lines (G2 --carrier-test, no '--', unknown gate, empty, empty command): exits "
          f"{codes} -> {'usage refusals' if r else 'FAIL'}")


# ----------------------------------------------------------------------------------------------------------------
# Part C: G2 scratch
# ----------------------------------------------------------------------------------------------------------------
def part_c(g: Git, root: Path) -> Path:
    print("\nPart C: G2 step3v_open on scratch repositories (anchor = a scratch '4efbae5-equivalent' short id)")
    S3V = gates.STEP3V_RECORD_REL

    def mk(name: str, record: dict | str | None, side: str | None = None, anchor_on_side: bool = False):
        repo = root / name
        g.init(repo)
        files = {"README.txt": b"synthetic\n"}
        base = g.commit(repo, "2026-09-29T22:32:00+02:00", "base", files)
        if anchor_on_side:
            g.run(repo, "checkout", "-q", "-b", "side2")
            anchor = g.commit(repo, "2026-09-30T07:17:06+02:00", "anchor on a side branch", {"a.txt": b"a\n"})
            g.run(repo, "checkout", "-q", "master")
        else:
            anchor = None
        results = g.commit(repo, "2026-09-30T07:16:49+02:00", "results", {"r.txt": b"r\n"})
        if side:
            g.run(repo, "checkout", "-q", "-b", "side")
            results = g.commit(repo, "2026-09-30T07:16:50+02:00", "results on an unmerged branch", {"s.txt": b"s\n"})
            g.run(repo, "checkout", "-q", "master")
        if record is None:
            text = None
        elif isinstance(record, str):
            text = record
        else:
            text = json.dumps({k: (results if v == "{c}" else v) for k, v in record.items()}, indent=1) + "\n"
        f2 = {"b.txt": b"b\n"}
        if text is not None:
            f2[S3V] = text.encode("utf-8")
        a2 = g.commit(repo, "2026-09-30T07:17:06+02:00", "record", f2)
        if anchor is None:
            anchor = a2
        return repo, anchor[:7], base

    good = {"step": "3 (v)", "step3v_commit": "{c}"}
    cases = []
    repo, short, _ = mk("G2_valid", good)
    cases.append(("C1", "valid record, anchor an ancestor", repo, short, True, "open"))
    repo, short, _ = mk("G2_nonhex", {"step": "3 (v)", "step3v_commit": "<filled by the orchestrator>"})
    cases.append(("C2", "non-hex step3v_commit", repo, short, False, "record_malformed"))
    repo, short, _ = mk("G2_missing", None)
    cases.append(("C3", "record file missing", repo, short, False, "record_unreadable"))
    repo, short, _ = mk("G2_nonanc", good, side="side")
    cases.append(("C4", "step3v_commit on an unmerged branch", repo, short, False, "commit_not_ancestor"))
    repo_default, short, _ = mk("G2_noanchor", good)
    cases.append(("C5", "4efbae5-equivalent missing (production default '4efbae5')", repo_default, None, False,
                  "anchor_unresolved"))
    repo, short, _ = mk("G2_anchor_side", good, anchor_on_side=True)
    cases.append(("C6", "4efbae5-equivalent not an ancestor of HEAD", repo, short, False, "anchor_not_ancestor"))
    repo, short, _ = mk("G2_step", {"step": "3 (iv)", "step3v_commit": "{c}"})
    cases.append(("C7", "step is not '3 (v)'", repo, short, False, "record_malformed"))
    repo, short, base = mk("G2_unknown", {"step": "3 (v)", "step3v_commit": "0" * 40})
    cases.append(("C8", "unknown 40-hex commit", repo, short, False, "commit_unknown"))
    repo, short, _ = mk("G2_upper", {"step": "3 (v)", "step3v_commit": "{c}"})
    (repo / S3V).write_text(json.dumps({"step": "3 (v)", "step3v_commit": json.loads(
        (repo / S3V).read_text(encoding="utf-8"))["step3v_commit"].upper()}), encoding="utf-8")
    cases.append(("C9", "upper-case step3v_commit (working copy)", repo, short, False, "record_malformed"))
    repo, short, _ = mk("G2_badjson", '{"step": "3 (v)", "step3v_commit": ')
    cases.append(("C10", "record JSON does not parse", repo, short, False, "record_unreadable"))

    print(f"  {'id':<4} {'expected':<8} {'observed':<8} {'reason (observed)':<22} {'as expected':<11} case")
    n_ok = 0
    for cid, desc, repo, short, exp, exp_reason in cases:
        kw = {} if short is None else {"anchor_rev": short}
        ok, reason, _ = gates.step3v_check(repo, **kw)
        pub = gates.step3v_open(repo, **kw)
        good = ok is exp and pub is exp and reason == exp_reason and reason in gates.G2_REASONS
        n_ok += good
        print(f"  {cid:<4} {'open' if exp else 'refused':<8} {'open' if ok else 'refused':<8} {reason:<22} "
              f"{'yes' if good else 'NO':<11} {desc}")
        check(good, f"G2 {cid} expected {exp}/{exp_reason}, got {ok}/{reason}")
    try:
        gates.require_step3v_open("p21", repo_default)
        raised = False
    except PermissionError as e:
        raised = str(e).startswith("G2 CLOSED (p21): ")
    check(raised, "require_step3v_open raises 'G2 CLOSED (<who>): ...'")
    print(f"  require_step3v_open on a closed scratch repo raises 'G2 CLOSED (p21): ...': {raised}")
    print(f"  -> {n_ok} / {len(cases)} as expected")
    return repo_default


# ----------------------------------------------------------------------------------------------------------------
# Part D: the real repository, read-only
# ----------------------------------------------------------------------------------------------------------------
def part_d(real: Path) -> None:
    print("\nPart D: the REAL repository (read-only git; record read from HEAD's tree)")
    head = subprocess.run(["git", "-C", str(real), "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip()
    print(f"  HEAD {head}")
    ok, reason, info = gates.g1_check(real)
    print(f"  g1_open: {gates.g1_open(real)} (reason {reason})")
    for k in ("bii_commit", "notice_commit", "time_notice_commit", "session_message_commit",
              "time_session_message_commit", "opened", "time_bii_commit", "section_at_c_first_line",
              "section_at_c_lines", "section_sha256"):
        print(f"    {k}: {info.get(k)}")
    check(ok is True and gates.g1_open(real) is True, "real g1_open True")
    # the plan's simulated values (RUN_PLAN.md section 2.2, lines 247-253)
    check(info.get("bii_commit") == "4fd7942ece3743d75741fa37c75212a9a6d2a520", "real bii_commit = 4fd7942")
    check(str(info.get("notice_commit", "")).startswith("6b855c9"), "real NOTICE commit = 6b855c9")
    check(str(info.get("session_message_commit", "")).startswith("1a8e46e"), "real session-message commit = 1a8e46e")
    check(info.get("section_at_c_first_line") == 611 and info.get("section_at_c_lines") == 29,
          "real section of session 10 at 4fd7942 = lines 611-639 (29 lines)")
    check(info.get("opened") == "2026-10-01T11:43:09+00:00", "real OPERATOR-OPENED = 2026-10-01T11:43:09Z")
    try:
        gates.require_g1_open("p21", real)
        r1 = True
    except PermissionError:
        r1 = False
    check(r1, "real require_g1_open does not raise")
    ok2, reason2, info2 = gates.step3v_check(real)
    print(f"  step3v_open: {gates.step3v_open(real)} (reason {reason2}); step3v_commit {info2.get('step3v_commit')}; "
          f"4efbae5 resolves to {info2.get('anchor')}")
    check(ok2 is True and gates.step3v_open(real) is True, "real step3v_open True")
    try:
        gates.require_step3v_open("p21", real)
        r2 = True
    except PermissionError:
        r2 = False
    check(r2, "real require_step3v_open does not raise")


# ----------------------------------------------------------------------------------------------------------------
# Part F: the cases discriminate v3's spec (RUN_PLAN.md section 2.2 "v3.1 changes", lines 254-258)
# ----------------------------------------------------------------------------------------------------------------
V3_OPENS = {"R17", "R18", "R19", "R20", "R25", "R26", "R27"}


def part_f(repos: dict[str, Path]) -> None:
    """v3 matched a supersession marker only at a line start and bounded the opening time below by the NOTICE commit
    only. Emulated by patching two gates.py functions (restored afterwards): the v3 emulation must open exactly the 7
    cases v3.1 added and leave every other case as in Part A -- i.e. P21 catches a gate with v3's defects."""
    print("\nPart F: P21 against an emulation of v3's spec (line-start supersession; NOTICE-only lower bound)")
    orig_first, orig_sup = gates._first_commit, gates.superseding_lines

    def v3_first(repo, c, rel, pred):
        if rel == gates.NEXT_SESSION_REL:
            return orig_first(repo, c, gates.A3_ARC_REL, gates._holds_notice)
        return orig_first(repo, c, rel, pred)

    def v3_sup(text):
        return sum(1 for ln in gates._lines(text) if ln.startswith(gates.SUPERSESSION_MARKERS))

    gates._first_commit, gates.superseding_lines = v3_first, v3_sup
    try:
        flipped = set()
        for cid, _desc, _spec, exp_open, _r in cases_35():
            if gates.g1_check(repos[cid])[0] is not exp_open:
                flipped.add(cid)
    finally:
        gates._first_commit, gates.superseding_lines = orig_first, orig_sup
    r = check(flipped == V3_OPENS, "Part F: the v3 emulation opens exactly the 7 cases v3.1 added")
    print(f"  cases whose outcome differs under the v3 emulation: {sorted(flipped)} ({len(flipped)}); expected "
          f"{sorted(V3_OPENS)} -> {'P21 catches the v3 defects' if r else 'FAIL'}")
    check(gates.g1_check(repos["R25"])[1] == "superseded", "Part F: gates.py restored after the emulation")


# ----------------------------------------------------------------------------------------------------------------
# Part G: the 40 cases discriminate the frozen v3.1 match from Correction 1's (RUN_PLAN_amend_1.md v2.1)
# ----------------------------------------------------------------------------------------------------------------
AMEND1_ADDED = {f"R{33 + i}" for i in range(5)}


def part_g(repos: dict[str, Path]) -> None:
    """The frozen v3.1 supersession match (section 2.2: normalised line contains the marker, case-sensitive) emulated by
    patching gates.superseding_lines (restored afterwards): it must open exactly the 5 cases Correction 1 added and
    leave the other 35 as in Part A -- i.e. P21 catches a gate without Correction 1."""
    print("\nPart G: P21 (40 cases) against an emulation of the frozen v3.1 match (case-sensitive)")
    orig_sup = gates.superseding_lines

    def v31_sup(text):
        return sum(1 for ln in gates._lines(text)
                   if any(mk in gates.normalise_line(ln) for mk in gates.SUPERSESSION_MARKERS))

    gates.superseding_lines = v31_sup
    try:
        flipped = set()
        for cid, _desc, _spec, exp_open, _r in cases_40():
            if gates.g1_check(repos[cid])[0] is not exp_open:
                flipped.add(cid)
    finally:
        gates.superseding_lines = orig_sup
    r = check(flipped == AMEND1_ADDED, "Part G: the v3.1 emulation opens exactly the 5 cases Correction 1 added")
    print(f"  cases whose outcome differs under the v3.1 emulation: {sorted(flipped)} ({len(flipped)}); expected "
          f"{sorted(AMEND1_ADDED)} -> {'P21 catches a gate without Correction 1' if r else 'FAIL'}")
    check(gates.g1_check(repos["R33"])[1] == "superseded", "Part G: gates.py restored after the emulation")
    # the keys themselves (no git): the five variants and the two markers match; the residual does not
    keys = {v: gates.supersession_key(v) for v in AMEND1_VARIANTS}
    check(all(any(mk in k for mk in gates.SUPERSESSION_KEYS) for k in keys.values()),
          "Part G: every Correction 1 variant's key contains a marker key")
    check(gates.SUPERSESSION_KEYS == ("record:(b-ii)commissioned", "record:delegationrevoked"),
          "Part G: marker keys = the markers with white space deleted, case-folded")
    check(gates.superseding_lines("RECORD: (b–ii) commissioned\nRECORD： delegation revoked") == 0,
          "Part G: declared residual (en dash, fullwidth colon) not matched")


def part_h(xrepos: dict[str, Path]) -> None:
    """asdg-skeptic WP1 review C1: Correction 1's Unicode white-space cases (X19-X23; X07 / X13 beside them). Each is
    refused by gates.py (Part A'); this part shows what they catch: (i) the frozen v3.1 match (collapse, no deletion,
    case-sensitive) opens every one of X19-X23 (they test the deletion, not section 2.2's collapse); (ii) a Correction 1
    whose white-space classes are ASCII only (WS_RUN_RE and WS_ANY_RE compiled with re.ASCII) opens every case with a
    non-ASCII white space (X20-X23, X07, X13) and keeps the tab case X19 refused; (iii) a supersession scan whose lines are
    split on str.splitlines (Unicode line boundaries) instead of LF (gates._lines; RUN_PLAN section 2.2 Definitions:
    Lines) opens X23. gates.py
    is restored after each emulation (checked)."""
    print("\nPart H: Correction 1's Unicode white space (tab, NBSP, em space, ideographic space, U+2028) - C1")
    new = [cid for cid, _, _ in UNICODE_WS_VARIANTS]
    check(all(gates.g1_check(xrepos[c])[1] == "superseded" for c in new + ["X07", "X13"]),
          "Part H: X19-X23, X07 and X13 refused (superseded) by gates.py")
    for cid, _, text in UNICODE_WS_VARIANTS:
        key = gates.supersession_key(text)
        check(any(mk in key for mk in gates.SUPERSESSION_KEYS) and gates.superseding_lines(text) == 1,
              f"Part H: {cid}'s key contains a marker key; one superseding line")
        check(not any(mk in gates.normalise_line(text) for mk in gates.SUPERSESSION_MARKERS),
              f"Part H: {cid} is not matched by section 2.2's collapse alone (it tests Correction 1's deletion)")

    def flips(patch: dict, cids: list[str]) -> set:
        saved = {k: getattr(gates, k) for k in patch}
        for k, v in patch.items():
            setattr(gates, k, v)
        try:
            return {c for c in cids if gates.g1_check(xrepos[c])[0] is True}
        finally:
            for k, v in saved.items():
                setattr(gates, k, v)

    def v31_sup(text):
        return sum(1 for ln in gates._lines(text)
                   if any(mk in gates.normalise_line(ln) for mk in gates.SUPERSESSION_MARKERS))
    opened = flips({"superseding_lines": v31_sup}, new)
    print(f"  v3.1 emulation (collapse only, case-sensitive) opens {sorted(opened)}; expected {new}")
    check(opened == set(new), f"Part H: the v3.1 emulation opens X19-X23 (opened {sorted(opened)})")
    import re as _re
    ascii_ws = {"WS_RUN_RE": _re.compile(r"\s+", _re.ASCII), "WS_ANY_RE": _re.compile(r"\s", _re.ASCII)}
    keys_now = gates.SUPERSESSION_KEYS
    opened = flips(ascii_ws, new + ["X07", "X13"])
    want = {"X20", "X21", "X22", "X23", "X07", "X13"}
    print(f"  ASCII-only white-space Correction 1 opens {sorted(opened)}; expected {sorted(want)}")
    check(opened == want, f"Part H: an ASCII-only white-space Correction 1 opens {sorted(want)} (opened "
                          f"{sorted(opened)}); the tab case X19 stays refused")
    def sup_splitlines(text):   # the supersession scan with Unicode line boundaries (str.splitlines) instead of LF
        return sum(1 for ln in text.splitlines() if any(mk in gates.supersession_key(ln) for mk in gates.SUPERSESSION_KEYS))
    opened = flips({"superseding_lines": sup_splitlines}, new)
    print(f"  supersession scan on Unicode line boundaries opens {sorted(opened)}; expected ['X23']")
    check(opened == {"X23"}, f"Part H: Unicode line splitting (str.splitlines) opens X23 only (opened {sorted(opened)})")
    check(gates.SUPERSESSION_KEYS == keys_now and gates.WS_ANY_RE.flags & _re.ASCII == 0
          and all(gates.g1_check(xrepos[c])[1] == "superseded" for c in new),
          "Part H: gates.py restored after the emulations")


def _rm(path: Path) -> None:
    def onexc(func, p, exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)
    shutil.rmtree(path, onexc=onexc)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", help="directory under which a fresh run directory is created")
    ap.add_argument("--repo", help="the real repository (default: the git toplevel of this file)")
    ap.add_argument("--keep", action="store_true", help="keep the scratch repositories")
    a = ap.parse_args(argv)
    real = Path(a.repo) if a.repo else gates.git_toplevel(Path(__file__).resolve().parent)
    if real is None:
        print("cannot find the real repository")
        return 2
    base = Path(a.scratch) if a.scratch else Path(tempfile.mkdtemp(prefix="a1_p21_"))
    scratch = base / time.strftime("p21_%Y%m%dT%H%M%S")
    scratch.mkdir(parents=True)
    print(f"P21 (RUN_PLAN.md v3.1 s2.2 / s7); scratch run directory created; real repository given")
    g = Git(scratch)

    n40, t40, repos = run_cases(g, scratch / "g1", cases_40(),
                                "Part A: the 40 cases of P21 (s2.2's 35 + RUN_PLAN_amend_1 Correction 1's 5; "
                                "3 open, 37 refused)")
    n_pos = sum(1 for c in cases_40() if c[3])
    check(t40 == 40 and n_pos == 3 and len(cases_35()) == 35, "case list is 40 = 3 + 37 (35 + 5)")
    nx, tx, xrepos = run_cases(g, scratch / "g1x", cases_extra(),
                               "Part A': extra cases (readings of gates.py; not in 40)")
    g2_closed = part_c(g, scratch / "g2")
    part_b(scratch, repos["R23"], repos["P01"], real, g2_closed)
    part_d(real)
    part_f(repos)
    part_g(repos)
    part_h(xrepos)
    print("\nPart E: deferred: fetch_extract.py not yet written (WP3, RUN_PLAN.md s8); its 'no network request with "
          "G1 closed' plant runs when it exists")

    print(f"\nSUMMARY: Part A {n40} / {t40} as expected; Part A' {nx} / {tx}; failures {len(FAILS)}")
    if FAILS:
        for f in FAILS:
            print(f"  FAILED: {f}")
        print(f"  scratch kept for inspection")
        return 1
    if not a.keep:
        _rm(scratch)
    print("P21 PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
