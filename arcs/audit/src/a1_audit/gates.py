"""Gate checks of the A1 runner (arcs/audit/RUN_PLAN.md v3.1, FROZEN; section 2.1 G2, section 2.2 G1).

- step3v_open(repo): section 2.1 -- the logic of explore/discovery/guard.py:53-67 (step3v_recorded) COPIED here, not
  imported, plus the plan's extra clause "4efbae5 is also an ancestor of HEAD".
- g1_open(repo): section 2.2 -- exactly the plan's pseudo-code and its Definitions (route (ii) only).
- require_g1_open(who, repo) / require_step3v_open(who, repo): raise PermissionError("G1 CLOSED (<who>): ...") /
  ("G2 CLOSED (<who>): ...") when the check is not True.

Both checks are fail closed: anything unexpected (any exception included) -> False. Every git call is
`git -C <repo> ...` in a subprocess with captured output; git objects are decoded as strict UTF-8. The checks never
write anything and never read gated material: they read only the two gate records, A3's ARC.md and NEXT_SESSION.md
from git objects, and commit metadata.

Readings this module makes where the frozen text leaves a corner open (each fail closed; reported in the WP1 report):
  * Session headings: a line counts as a heading of session n when it fullmatches the plan's regex
    `^### (\\d{4}-\\d{2}-\\d{2}) - session (\\d+)$` (Python str regex, so \\d also matches non-ASCII digits) and
    int(group 2) == n. Exactly one such line must exist, AND it must be canonical (group 2 == str(n), the date in
    ASCII digits): "session 010" or a non-ASCII-digit heading counts as a duplicate but never as THE heading.
  * NOTICE / session-message walks: a commit whose file is absent, or whose session-9 section is not defined
    (heading count != 1), does not "hold" the string and the walk moves on; a blob that is not valid UTF-8 raises
    (-> False).
  * JSON records: a duplicated key is refused (the record would be ambiguous).
  * The step-3 (v) record is read from the working copy, as guard.py:55-57 reads it (section 2.1 copies that logic;
    section 2.2's "HEAD's tree" rule is G1's). In a clean worktree (L11) the two are the same bytes.
  * Supersession normalisation deletes `*`, `_` and the backtick first, then collapses each run of white space
    (Python \\s, Unicode) to one space (section 2.2). RUN_PLAN_amend_1.md v2.1 Correction 1 (FROZEN sha256
    8e06d60e...): after that normalisation every white-space character (Python `re` \\s on str, Unicode: tab, NBSP, em
    space included) is deleted, and both the line and the marker are case-folded (str.casefold) before the containment
    test (supersession_key). The record block's own checks are unchanged: marker lines are exact whole-line matches,
    attestation lines keep their regexes, the session-n block stays byte-identical. Declared residual (not matched):
    a fullwidth colon, fullwidth letters, a non-breaking hyphen or an en dash in "b-ii" (no NFKC, no dash folding).
  * git runs with the inherited GIT_* environment variables removed and GIT_NO_REPLACE_OBJECTS=1, so `-C <repo>`
    names the repository read and replace refs cannot substitute objects. HEAD is resolved once per check and every
    "HEAD" of the plan's pseudo-code is that commit (no moving target between git calls).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

# ----------------------------------------------------------------------------------------------------------------
# Constants (RUN_PLAN.md v3.1 section 2.1 / 2.2; the NOTICE and due strings verified byte-wise from git:
# `git show 4fd7942:arcs/replication/ARC.md` line 576 and `git show 1a8e46e:NEXT_SESSION.md` line 54)
# ----------------------------------------------------------------------------------------------------------------
STEP3V_RECORD_REL = "arcs/replication/results/step3v_record.json"   # guard.py:35
G2_ANCHOR = "4efbae5"                                                # section 2.1: also an ancestor of HEAD

G1_RECORD_REL = "arcs/audit/run_manifests/G1/g1_open_record.json"
A3_ARC_REL = "arcs/replication/ARC.md"
NEXT_SESSION_REL = "NEXT_SESSION.md"

MARKER_DECLINED = "RECORD: (b-ii) declined"
MARKER_NO_ABIDE2 = "RECORD: no ABIDE II analysis will run"
NOTICE_STRING = "(amendment 2 §4b) - the (b-ii)-declined record"   # U+00A7 section sign, ASCII hyphen-minus
DUE_STRING = '"(b-ii) declined" record is due in the next operator-opened session'
SUPERSESSION_MARKERS = ("RECORD: (b-ii) commissioned", "RECORD: delegation revoked")
NOTICE_SESSION_N = 9          # the section that holds the NOTICE string
MIN_RECORD_SESSION = 10       # register :97-100: a session after the session-9 NOTICE

HEADING_RE = re.compile(r"^### (\d{4}-\d{2}-\d{2}) - session (\d+)$")
NEXT_HEADING_RE = re.compile(r"^#{1,3} ")
ASCII_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
NOTICE_SESSION_RE = re.compile(r"^NOTICE-SESSION: ([^;\s]+)$")
OPERATOR_OPENED_RE = re.compile(
    r"^OPERATOR-OPENED: session ([^;\s]+); opened ([^;\s]+); message sha256 ([0-9a-f]{64})$")
HEX40_RE = re.compile(r"[0-9a-f]{40}")
EMPHASIS_RE = re.compile(r"[*_`]")
WS_RUN_RE = re.compile(r"\s+")
WS_ANY_RE = re.compile(r"\s")  # RUN_PLAN_amend_1 Correction 1: every white-space character (str pattern: Unicode)

GIT_TIMEOUT_S = 120

# Fixed vocabulary of g1_check reasons (the only strings a caller may print besides True / False).
G1_REASONS = (
    "open", "record_unreadable", "route_or_record", "session_number", "bii_commit_not_hex", "bii_commit_unknown",
    "bii_commit_not_ancestor", "arc_unreadable", "section_missing_at_c", "marker_missing", "notice_session_line",
    "operator_opened_line", "session_ids_equal", "no_notice_commit", "no_session_message_commit",
    "opened_unparseable", "opened_no_offset", "opened_too_early", "opened_too_late", "marker_in_parent",
    "section_not_unique_at_head", "section_changed_at_head", "notice_missing_at_head", "superseded", "exception")
G2_REASONS = ("open", "record_unreadable", "record_malformed", "commit_unknown", "commit_not_ancestor",
              "anchor_unresolved", "anchor_not_ancestor", "exception")


class _Closed(Exception):
    """Internal: a named refusal (reason from the fixed vocabulary)."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


# ----------------------------------------------------------------------------------------------------------------
# git plumbing
# ----------------------------------------------------------------------------------------------------------------
def _git_env() -> dict:
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), "-c", "log.showSignature=false", *args],
                          capture_output=True, env=_git_env(), timeout=GIT_TIMEOUT_S)


def _git_ok(repo: Path, *args: str) -> bool:
    return _git(repo, *args).returncode == 0


def _git_bytes(repo: Path, *args: str) -> bytes:
    """stdout of a git command that must succeed (else _Closed is raised by the caller's mapping)."""
    p = _git(repo, *args)
    if p.returncode != 0:
        raise FileNotFoundError("git " + args[0] + " failed")
    return p.stdout


def _show_text(repo: Path, rev: str, rel: str) -> str | None:
    """The blob <rev>:<rel> as strict UTF-8 text, or None if git cannot show it (absent path / revision)."""
    p = _git(repo, "show", f"{rev}:{rel}")
    if p.returncode != 0:
        return None
    return p.stdout.decode("utf-8")          # strict: a non-UTF-8 blob raises -> fail closed


def _lines(text: str) -> list[str]:
    """Blobs are split on LF (Definitions: Lines)."""
    return text.split("\n")


def _commit_time(repo: Path, commit: str) -> _dt.datetime:
    s = _git_bytes(repo, "show", "-s", "--format=%cI", commit).decode("utf-8").strip()
    t = _dt.datetime.fromisoformat(s)
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("commit time without offset")
    return t


def _no_dup_keys(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate key in record")
    return dict(pairs)


def _loads(text: str):
    return json.loads(text, object_pairs_hook=_no_dup_keys)


def _resolve_commit(repo: Path, rev: str) -> str | None:
    p = _git(repo, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
    if p.returncode != 0:
        return None
    full = p.stdout.decode("ascii").strip()
    return full if HEX40_RE.fullmatch(full) else None


def _is_ancestor(repo: Path, commit: str, of: str) -> bool:
    return _git_ok(repo, "merge-base", "--is-ancestor", commit, of)


def git_toplevel(cwd: Path | None = None) -> Path | None:
    """The git toplevel of cwd (None if cwd is not inside a repository)."""
    try:
        p = subprocess.run(["git", "-C", str(cwd or Path.cwd()), "rev-parse", "--show-toplevel"],
                           capture_output=True, env=_git_env(), timeout=GIT_TIMEOUT_S)
        if p.returncode != 0:
            return None
        return Path(p.stdout.decode("utf-8").strip())
    except Exception:  # noqa: BLE001
        return None


# ----------------------------------------------------------------------------------------------------------------
# Section 2.1: G2 (step 3 (v) recorded)
# ----------------------------------------------------------------------------------------------------------------
def step3v_check(repo: Path, *, anchor_rev: str = G2_ANCHOR) -> tuple[bool, str, dict]:
    """(open?, reason, info). guard.py:53-67 copied (record path relative to `repo`), plus the anchor clause.

    `anchor_rev` exists for the scratch tests (a "4efbae5-equivalent"); production callers use the default.
    """
    info: dict = {}
    try:
        repo = Path(repo)
        rec = repo / STEP3V_RECORD_REL
        try:
            doc = _loads(rec.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return False, "record_unreadable", info
        c = str(doc["step3v_commit"])
        if doc.get("step") != "3 (v)" or not HEX40_RE.fullmatch(c):
            return False, "record_malformed", info
        info["step3v_commit"] = c
        head = _resolve_commit(repo, "HEAD")                 # HEAD resolved once (no moving target between calls)
        if head is None:
            return False, "exception", info
        if not _git_ok(repo, "cat-file", "-e", f"{c}^{{commit}}"):
            return False, "commit_unknown", info
        if not _is_ancestor(repo, c, head):
            return False, "commit_not_ancestor", info
        anchor = _resolve_commit(repo, anchor_rev)
        if anchor is None:
            return False, "anchor_unresolved", info
        info["anchor"] = anchor
        if not _is_ancestor(repo, anchor, head):
            return False, "anchor_not_ancestor", info
        return True, "open", info
    except Exception:  # noqa: BLE001 - fail closed
        return False, "exception", info


def step3v_open(repo: Path, *, anchor_rev: str = G2_ANCHOR) -> bool:
    """RUN_PLAN.md section 2.1. True iff A3's step 3 (v) record is valid and an ancestor of HEAD and 4efbae5 is too."""
    try:
        return step3v_check(repo, anchor_rev=anchor_rev)[0] is True
    except Exception:  # noqa: BLE001
        return False


def require_step3v_open(who: str, repo: Path) -> None:
    ok, reason, _ = step3v_check(repo)
    if ok is not True:
        raise PermissionError(f"G2 CLOSED ({who}): step3v_open() is False (reason {reason}; RUN_PLAN.md s2.1: "
                              f"A3's step 3 (v) record must be valid, its commit and 4efbae5 ancestors of HEAD)")


# ----------------------------------------------------------------------------------------------------------------
# Section 2.2: G1 (route (ii), the "(b-ii) declined" record)
# ----------------------------------------------------------------------------------------------------------------
def section_of_session(lines: list[str], n: int) -> tuple[int, list[str]] | None:
    """Definitions, "Section of session n": (index of the heading, the section's lines), or None when the heading of
    session n does not occur exactly once (or the single occurrence is not canonical; see the module docstring)."""
    hits = []
    for i, line in enumerate(lines):
        m = HEADING_RE.fullmatch(line)
        if m is not None and int(m.group(2)) == n:
            hits.append((i, m))
    if len(hits) != 1:
        return None
    i, m = hits[0]
    if m.group(2) != str(n) or not ASCII_DATE_RE.fullmatch(m.group(1)):
        return None
    j = i + 1
    while j < len(lines) and NEXT_HEADING_RE.match(lines[j]) is None:
        j += 1
    return i, lines[i:j]


def _section_sha256(sec: list[str]) -> str:
    return hashlib.sha256("\n".join(sec).encode("utf-8")).hexdigest()


def _holds_notice(arc_text: str) -> bool:
    sec = section_of_session(_lines(arc_text), NOTICE_SESSION_N)
    return sec is not None and NOTICE_STRING in "\n".join(sec[1])


def _first_commit(repo: Path, c: str, rel: str, pred) -> str | None:
    """First commit of `git rev-list --reverse --topo-order c -- rel` whose blob at rel satisfies pred."""
    out = _git_bytes(repo, "rev-list", "--reverse", "--topo-order", c, "--", rel).decode("ascii")
    for cid in out.split():
        if not HEX40_RE.fullmatch(cid):
            raise ValueError("rev-list output")
        text = _show_text(repo, cid, rel)
        if text is not None and pred(text):
            return cid
    return None


def normalise_line(line: str) -> str:
    """Supersession match normalisation (section 2.2): delete * _ ` then collapse white-space runs to one space."""
    return WS_RUN_RE.sub(" ", EMPHASIS_RE.sub("", line))


def supersession_key(text: str) -> str:
    """RUN_PLAN_amend_1 Correction 1: section 2.2's normalisation, then every white-space character (Python re \\s on
    str, Unicode) deleted, then str.casefold. Applied to the line and to the marker alike."""
    return WS_ANY_RE.sub("", normalise_line(text)).casefold()


SUPERSESSION_KEYS = tuple(supersession_key(mk) for mk in SUPERSESSION_MARKERS)


def superseding_lines(text: str) -> int:
    """Number of lines of `text` whose key (supersession_key: section 2.2's normalisation, then Correction 1's
    white-space deletion and case folding) contains a supersession marker's key."""
    return sum(1 for ln in _lines(text) if any(mk in supersession_key(ln) for mk in SUPERSESSION_KEYS))


def _g1_check(repo: Path, info: dict) -> str:
    repo = Path(repo)
    head = _resolve_commit(repo, "HEAD")                     # HEAD resolved once; every "HEAD" below is this commit
    if head is None:
        raise _Closed("record_unreadable")
    info["head"] = head
    # the record, from HEAD's tree (never the working copy)
    try:
        doc = _loads(_git_bytes(repo, "show", f"{head}:{G1_RECORD_REL}").decode("utf-8"))
        if not isinstance(doc, dict):
            raise ValueError("record is not an object")
        route, record = doc["route"], doc["record"]
        n, c = doc["a3_arc_session"], doc["bii_commit"]
    except Exception:  # noqa: BLE001
        raise _Closed("record_unreadable")
    if not (route == "ii" and record == "(b-ii) declined"):
        raise _Closed("route_or_record")
    if not (type(n) is int and n >= MIN_RECORD_SESSION):
        raise _Closed("session_number")
    if not (isinstance(c, str) and HEX40_RE.fullmatch(c)):
        raise _Closed("bii_commit_not_hex")
    if not _git_ok(repo, "cat-file", "-e", f"{c}^{{commit}}"):
        raise _Closed("bii_commit_unknown")
    if not _is_ancestor(repo, c, head):
        raise _Closed("bii_commit_not_ancestor")
    info["bii_commit"] = c

    arc_c = _show_text(repo, c, A3_ARC_REL)
    arc_p = _show_text(repo, f"{c}^", A3_ARC_REL)
    arc_h = _show_text(repo, head, A3_ARC_REL)
    if arc_c is None or arc_p is None or arc_h is None:
        raise _Closed("arc_unreadable")
    lines_c, lines_p, lines_h = _lines(arc_c), _lines(arc_p), _lines(arc_h)

    sec = section_of_session(lines_c, n)
    if sec is None:
        raise _Closed("section_missing_at_c")
    blk_start, blk = sec
    info["section_at_c_first_line"] = blk_start + 1          # 1-based line number in ARC.md at c
    info["section_at_c_lines"] = len(blk)
    if MARKER_DECLINED not in blk or MARKER_NO_ABIDE2 not in blk:
        raise _Closed("marker_missing")

    ns = [ln for ln in blk if ln.startswith("NOTICE-SESSION:")]
    if len(ns) != 1 or NOTICE_SESSION_RE.fullmatch(ns[0]) is None:
        raise _Closed("notice_session_line")
    oo = [ln for ln in blk if ln.startswith("OPERATOR-OPENED:")]
    if len(oo) != 1 or OPERATOR_OPENED_RE.fullmatch(oo[0]) is None:
        raise _Closed("operator_opened_line")
    notice_session = NOTICE_SESSION_RE.fullmatch(ns[0]).group(1)
    m_oo = OPERATOR_OPENED_RE.fullmatch(oo[0])
    opened_session, opened_s = m_oo.group(1), m_oo.group(2)
    if notice_session == opened_session:
        raise _Closed("session_ids_equal")

    k = _first_commit(repo, c, A3_ARC_REL, _holds_notice)
    if k is None:
        raise _Closed("no_notice_commit")
    s = _first_commit(repo, c, NEXT_SESSION_REL, lambda t: any(DUE_STRING in ln for ln in _lines(t)))
    if s is None:
        raise _Closed("no_session_message_commit")
    info["notice_commit"], info["session_message_commit"] = k, s

    try:
        opened = _dt.datetime.fromisoformat(opened_s)
    except ValueError:
        raise _Closed("opened_unparseable")
    if opened.tzinfo is None or opened.utcoffset() is None:
        raise _Closed("opened_no_offset")
    t_k, t_s, t_c = _commit_time(repo, k), _commit_time(repo, s), _commit_time(repo, c)
    info["time_notice_commit"], info["time_session_message_commit"] = t_k.isoformat(), t_s.isoformat()
    info["time_bii_commit"], info["opened"] = t_c.isoformat(), opened.isoformat()
    if not max(t_k, t_s) < opened:
        raise _Closed("opened_too_early")
    if not opened <= t_c:
        raise _Closed("opened_too_late")

    if MARKER_DECLINED in lines_p or MARKER_NO_ABIDE2 in lines_p:
        raise _Closed("marker_in_parent")

    sec_h = section_of_session(lines_h, n)
    if sec_h is None:
        raise _Closed("section_not_unique_at_head")
    if _section_sha256(sec_h[1]) != _section_sha256(blk):
        raise _Closed("section_changed_at_head")
    info["section_sha256"] = _section_sha256(blk)

    if not _holds_notice(arc_h):
        raise _Closed("notice_missing_at_head")
    if superseding_lines(arc_h) != 0:
        raise _Closed("superseded")
    return "open"


def g1_check(repo: Path) -> tuple[bool, str, dict]:
    """(open?, reason, info). reason is from G1_REASONS; info holds commit ids, times and line counts only."""
    info: dict = {}
    try:
        reason = _g1_check(Path(repo), info)
        return reason == "open", reason, info
    except _Closed as e:
        return False, e.reason, info
    except Exception:  # noqa: BLE001 - fail closed
        return False, "exception", info


def g1_open(repo: Path) -> bool:
    """RUN_PLAN.md section 2.2 (route (ii) only). Anything unexpected -> False."""
    try:
        return g1_check(repo)[0] is True
    except Exception:  # noqa: BLE001
        return False


def require_g1_open(who: str, repo: Path) -> None:
    ok, reason, _ = g1_check(repo)
    if ok is not True:
        raise PermissionError(f"G1 CLOSED ({who}): g1_open() is False (reason {reason}; RUN_PLAN.md s2.2: route (ii) "
                              f"record at HEAD missing, malformed, early, late, edited, superseded or self-attesting)")
