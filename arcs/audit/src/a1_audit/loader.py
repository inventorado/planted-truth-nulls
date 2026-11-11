"""A1 loader: the frozen claims register's TSV, keyed by row (RUN_PLAN.md v3.1 §4 "Loader", FROZEN sha256 16c60232...).

RUN_PLAN.md §4 (:350-352): "parses the TSV after L1-L3 and keys every row by its `row` number (the seed key, `:1817-1819`).
The status of a gated row reads "deferred (gate Gx closed); <status under the gate>". Once Gx's check passes, the runner
applies the part after "; ". Otherwise the row stays deferred."

- `load(repo_root, launch_record)` refuses unless the launch record holds L1, L2 and L3 as passed (and, unless
  `allow_unlaunched=True` is given explicitly, the whole launch passed); it re-hashes the bytes it parses (sha256 of the
  LF-normalised bytes == the L2 pin) before parsing them.
- Every field is kept verbatim (a str, never stripped or re-typed); typed views (row, target number, m membership, the
  gated-status parse) are properties beside the verbatim text.
- A gated row (gate G1 or G2) whose status is not in the registered form, or names the other gate, is refused at load
  (fail closed: its effective status would be undefined).
- `effective_status(row, open_gates)` returns the part after "; " iff the row's gate is in `open_gates`, else the
  verbatim deferred text. `open_gates_from(launch_record)` derives the open gate from a passed launch's L15 only
  (never from a launch run with test overrides).

Nothing here prints row text. No statistic is computed here.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterable, Iterator, Mapping

TSV_PATH = "arcs/audit/claims_register.tsv"
# RUN_PLAN.md:30 (§0.1) and register_freeze_manifest.json files[0]; L2 uses this pin
TSV_SHA256 = "d6499b5d10eed39fc5bfcd8033fc5f7c7beea88f1d4b4c30fd21fed632bf8058"
N_ROWS = 692  # RUN_PLAN.md:152 (L12); claims_register.md:1851 ("rows = 692")
# the TSV's column header (claims_register.tsv, the first non-comment line; 33 columns), asserted at parse
COLUMNS = ("row", "target_no", "target_key", "frozen11_row", "cell_id", "cell_class", "claim_form", "map", "set_S",
           "set_id", "set_size_in_class_universe", "set_sha256", "set_rule_labels", "set_status", "T", "direction",
           "analysis_class", "route", "inference_level", "status", "headline_population", "reproduction",
           "published_value_and_location", "gate", "focal", "verdict_counted_in_m", "dependencies", "notes", "n_cells",
           "map_index", "cell_index", "secondary_view_near_miss_status", "secondary_view_near_miss_set_id")
GATE_VALUES = ("G1", "G2", "none", "G1+G2")
GATED_GATES = ("G1", "G2")
# RUN_PLAN.md:351 "deferred (gate Gx closed); <status under the gate>"
GATED_STATUS = re.compile(r"\Adeferred \(gate (G1|G2) closed\); (.+)\Z", re.S)
M_UPPER_PREFIX = "yes (upper bound only"  # claims_register.md:1825-1826 (the upper bound's value form)


class LoaderRefused(RuntimeError):
    """The loader's preconditions (L1-L3 passed; bytes equal to the pin; the registered row form) are not met."""


def _refuse(msg: str):
    raise LoaderRefused("loader refused: " + msg)


def lf(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


def parse_gated(status: str) -> tuple[str, str] | None:
    """(gate, status under the gate) for the registered gated form, else None. The status under the gate is the
    whole text after the first "; " that follows the prefix, verbatim."""
    if not isinstance(status, str):
        return None
    m = GATED_STATUS.match(status)
    return (m.group(1), m.group(2)) if m else None


class Row:
    """One TSV row: `fields` verbatim (str), keyed by column name; typed views as properties."""

    __slots__ = ("_f", "_line", "_gated")

    def __init__(self, fields: Mapping[str, str], line: str):
        self._f = dict(fields)
        self._line = line
        self._gated = parse_gated(self._f["status"])

    # verbatim access
    @property
    def fields(self) -> Mapping[str, str]:
        return dict(self._f)

    @property
    def line(self) -> str:
        """the row's TSV line, verbatim (without its LF)."""
        return self._line

    def __getitem__(self, column: str) -> str:
        return self._f[column]

    # typed views
    @property
    def row(self) -> int:
        return int(self._f["row"])

    @property
    def target_no(self) -> int:
        return int(self._f["target_no"])

    @property
    def target_key(self) -> str:
        return self._f["target_key"]

    @property
    def cell_id(self) -> str:
        return self._f["cell_id"]

    @property
    def claim_form(self) -> str:
        return self._f["claim_form"]

    @property
    def direction(self) -> str:
        """the direction field, verbatim."""
        return self._f["direction"]

    @property
    def status(self) -> str:
        """the status field, verbatim (the deferred text for a gated row)."""
        return self._f["status"]

    @property
    def gate(self) -> str:
        return self._f["gate"]

    @property
    def map_index_text(self) -> str:
        return self._f["map_index"]

    @property
    def cell_index_text(self) -> str:
        return self._f["cell_index"]

    @property
    def m_membership(self) -> str:
        """'yes' (counted in m), 'upper bound only' (counted in m's upper bound only) or 'no'."""
        v = self._f["verdict_counted_in_m"]
        if v == "yes":
            return "yes"
        if v.startswith(M_UPPER_PREFIX):
            return "upper bound only"
        if v == "no":
            return "no"
        raise LoaderRefused("loader refused: row %s: verdict_counted_in_m is not of a registered form" % self._f["row"])

    @property
    def in_m(self) -> bool:
        """counted in m's lower bound (verdict_counted_in_m == 'yes'; claims_register.md:1823-1826)."""
        return self.m_membership == "yes"

    @property
    def gated(self) -> tuple[str, str] | None:
        """(gate, status under the gate) iff the status is in the registered gated form."""
        return self._gated


def int_or_none(text: str) -> int | None:
    """A plain non-negative decimal integer field -> int; any other text (the register's prose forms) -> None. The
    caller decides from the register's text; this helper never interprets prose."""
    return int(text) if isinstance(text, str) and re.fullmatch(r"(0|[1-9][0-9]*)", text) else None


def parse_tsv_bytes(data: bytes) -> tuple[list[str], list[Row]]:
    """Parse the TSV's LF bytes: a leading block of '#' comment lines, the column header, then one line per row; the
    file ends with one LF. Refuses any other shape (a '#' line after the header, an empty line, a field count other
    than 33, a row number out of sequence, an unknown gate value, a gated row not in the registered form)."""
    if not isinstance(data, (bytes, bytearray)):
        _refuse("TSV bytes expected")
    if b"\r" in data:
        _refuse("TSV bytes hold a CR (LF bytes expected)")
    text = bytes(data).decode("utf-8")  # strict
    if not text.endswith("\n"):
        _refuse("TSV does not end with LF")
    lines = text[:-1].split("\n")
    i = 0
    while i < len(lines) and lines[i].startswith("#"):
        i += 1
    if i >= len(lines):
        _refuse("TSV has no header line")
    header = lines[i].split("\t")
    if tuple(header) != COLUMNS:
        _refuse("TSV header differs from the registered 33 columns")
    rows: list[Row] = []
    for k, ln in enumerate(lines[i + 1:], start=1):
        if ln == "" or ln.startswith("#"):
            _refuse("TSV line %d after the header is empty or a comment" % (i + 1 + k))
        parts = ln.split("\t")
        if len(parts) != len(COLUMNS):
            _refuse("TSV row %d has %d fields, not %d" % (k, len(parts), len(COLUMNS)))
        f = dict(zip(COLUMNS, parts))
        if f["row"] != str(k):
            _refuse("TSV row numbers are not 1..n in order (position %d)" % k)
        if not re.fullmatch(r"[1-9][0-9]*", f["target_no"]):
            _refuse("row %d: target_no is not a positive integer" % k)
        if f["gate"] not in GATE_VALUES:
            _refuse("row %d: gate value not in %s" % (k, "/".join(GATE_VALUES)))
        r = Row(f, ln)
        g = r.gated
        if f["gate"] in GATED_GATES:
            if g is None:
                _refuse("row %d: gate %s but the status is not 'deferred (gate %s closed); <status>'" % (k, f["gate"], f["gate"]))
            if g[0] != f["gate"]:
                _refuse("row %d: the status names gate %s, the gate column %s" % (k, g[0], f["gate"]))
        elif g is not None:
            _refuse("row %d: gate %s but the status is in the gated form of %s" % (k, f["gate"], g[0]))
        _ = r.m_membership  # refuses an unregistered form
        rows.append(r)
    return header, rows


def register_counts(rows: Iterable[Row]) -> dict:
    """The numbers L12 re-counts (RUN_PLAN.md:152): rows, m (lower / upper), m per target_key, rows per gate.
    "m.target" counts verdict_counted_in_m == 'yes' (the lower bound), as the §4 block's "m.target.<key>" lines do
    (the frozen builder, claims_register_tsv_build.py:3452-3459, :3645); upper-only rows are counted apart."""
    rows = list(rows)
    per_target: dict[str, int] = {}
    upper_only: dict[str, int] = {}
    per_gate = {g: 0 for g in GATE_VALUES}
    m_lower = m_upper = 0
    for r in rows:
        per_gate[r.gate] += 1
        mm = r.m_membership
        if mm == "yes":
            m_lower += 1
            per_target[r.target_key] = per_target.get(r.target_key, 0) + 1
        if mm == "upper bound only":
            upper_only[r.target_key] = upper_only.get(r.target_key, 0) + 1
        if mm in ("yes", "upper bound only"):
            m_upper += 1
    return {"rows": len(rows), "m.lower": m_lower, "m.upper": m_upper, "m.target": dict(sorted(per_target.items())),
            "m.upper_only.target": dict(sorted(upper_only.items())), "gate": per_gate}


def effective_status(row: Row, open_gates: Iterable[str]) -> str:
    """RUN_PLAN.md:351-352: the part after "; " iff that gate's check passed (the gate is in `open_gates`), else the
    deferred text verbatim. Rows not in the gated form (ungated rows; Dear's G1+G2 rows, deferred pending provenance)
    return their status verbatim."""
    og = frozenset(open_gates)
    bad = [g for g in og if g not in GATED_GATES]
    if bad:
        raise ValueError("open_gates holds values other than G1 / G2: %r" % sorted(bad))
    g = row.gated
    if g is None:
        return row.status
    return g[1] if g[0] in og else row.status


def open_gates_from(launch_record: Mapping) -> frozenset:
    """The gate a passed launch opened: its `gate` (G1 / G2) iff the launch passed, ran without test overrides, and
    its L15 check passed; else none."""
    if not isinstance(launch_record, Mapping) or launch_record.get("passed") is not True:
        return frozenset()
    if launch_record.get("test_overrides") or launch_record.get("files_root"):
        return frozenset()
    gate = launch_record.get("gate")
    if gate not in GATED_GATES:
        return frozenset()
    l15 = [a for a in launch_record.get("assertions", []) if isinstance(a, Mapping) and a.get("id") == "L15"]
    if len(l15) != 1 or l15[0].get("ok") is not True or l15[0].get("status") != "pass":
        return frozenset()
    return frozenset({gate})


class Register:
    """The parsed TSV keyed by row number (RUN_PLAN.md:350; claims_register.md:1817-1819 'its row numbers key the
    seeds')."""

    def __init__(self, header: list[str], rows: list[Row], sha256: str, run_commit: str | None, source: str):
        self.header = list(header)
        self._rows = {r.row: r for r in rows}
        if len(self._rows) != len(rows):
            _refuse("duplicate row numbers")
        self.sha256 = sha256
        self.run_commit = run_commit
        self.source = source

    def __getitem__(self, row: int) -> Row:
        return self._rows[row]

    def __iter__(self) -> Iterator[Row]:
        return iter(self._rows[k] for k in sorted(self._rows))

    def __len__(self) -> int:
        return len(self._rows)

    def rows(self) -> list[Row]:
        return list(self)

    def counts(self) -> dict:
        return register_counts(self)


def _assertion(record: Mapping, aid: str) -> Mapping | None:
    hits = [a for a in record.get("assertions", []) if isinstance(a, Mapping) and a.get("id") == aid]
    return hits[0] if len(hits) == 1 else None


def load(repo_root, launch_record: Mapping, *, allow_unlaunched: bool = False) -> Register:
    """Parse the TSV of `repo_root` after L1-L3 (RUN_PLAN.md:350). The launch record must name this repository and
    hold L1, L2 and L3 with ok True; unless `allow_unlaunched` is passed explicitly (tests, diagnostics), the launch
    must have passed as a whole. The parsed bytes are re-hashed against the pin before parsing."""
    if not isinstance(launch_record, Mapping):
        _refuse("a launch record (dict) is required")
    repo = Path(repo_root).resolve()
    rec_root = launch_record.get("repo_root")
    if not rec_root or Path(rec_root).resolve() != repo:
        _refuse("the launch record names another repository root")
    for aid in ("L1", "L2", "L3"):
        a = _assertion(launch_record, aid)
        if a is None or a.get("ok") is not True:
            _refuse("%s did not pass in the launch record" % aid)
    if launch_record.get("passed") is not True and not allow_unlaunched:
        _refuse("the launch did not pass (allow_unlaunched not given)")
    if (launch_record.get("test_overrides") or launch_record.get("files_root")) and not allow_unlaunched:
        _refuse("the launch ran with test overrides (allow_unlaunched not given)")
    files = Path(launch_record.get("files_root") or repo)
    p = files / TSV_PATH
    if not p.is_file():
        _refuse("TSV absent")
    data = lf(p.read_bytes())
    sha = hashlib.sha256(data).hexdigest()
    if sha != TSV_SHA256:
        _refuse("TSV bytes read now differ from the L2 pin")
    header, rows = parse_tsv_bytes(data)
    if len(rows) != N_ROWS:
        _refuse("TSV holds %d rows, not %d" % (len(rows), N_ROWS))
    return Register(header, rows, sha, launch_record.get("run_commit"), TSV_PATH)
