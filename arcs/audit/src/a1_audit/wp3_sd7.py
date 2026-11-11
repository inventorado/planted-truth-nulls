"""WP3: Liu SD7 declared by rule (RUN_PLAN_amend_3.md v2.1, FROZEN sha256 da3f3b8b..., R46). Pure rules, used by
fetch_extract's SD7 read (section 8 steps 3-4 through the frozen guard) and by the WP3 material stage; nothing here
opens a file or prints.

(a) the registered copy: wp3_layout.SD7_REGISTERED (path, sha256 e2bd735c..., 1,442,234 B); a mismatch reads
    "not auditable (map changed)" for T4 and T5.
(b) the sheet: each sheet name normalised in memory (casefold; every character that is not a letter or a digit
    removed) and matched at its start by SHEET_RULE; exactly one sheet must match (else SD7_SHEET).
(c) the header row: h = 0 ... 19 through the guard's read_openpyxl with the ASD-anchored column rule (asd_rule): the
    row holds exactly one cell that is a text equal to 'asd' after stripping and casefolding, at a position > 0; pass 1
    returns [0], pass 2 [0, ASD]; the header text at position 0 is not used; no h qualifies -> SD7_HEADER. Position 0 is
    asserted to be the label column by R42 (d)'s normaliser itself (forms.sd7_normalise fails closed, SD7_UNMATCHED).
(d) the label block: empty rows (position-0 cell empty / whitespace) after the header skipped; the block is the first
    run of rows with a non-empty position-0 cell; after it every non-empty position-0 cell is normalised by R42 (d)'s
    normaliser, and any that matches a DK label refuses (SD7_INTERRUPTED); the others are footnotes (counted).
(e) pass 1 hands the transform position 0 only (a wrapper-side mask, also on a clean sheet) and logs the positions each
    transform consumes (PositionView); pass 1's log must hold position 0 alone.
(f) pass 2: the ASD column; a finite number is a value; an empty cell, 'na' / 'nan' / 'n/a' (stripped, casefolded) and
    an Excel error literal read as missing (counted); anything else refuses pass 2 (SD7_NON_NUMERIC, the comparator's
    status; T4 / T5 stay computed).
"""
from __future__ import annotations

import math
import re

SHEET_RULE = re.compile(r"^(supplementary|supplemental|suppl|supp)?(dataset|data)?(sd|s)?0*7(?![0-9])")
MISSING_TEXTS = ("na", "nan", "n/a")
EXCEL_ERRORS = ("#n/a", "#div/0!", "#value!", "#num!", "#ref!", "#null!", "#name?")
HEADER_ROWS = 20          # the guard's header zone (privacy_guard.GUARD_ROWS; RUN_PLAN section 8 step 4)

SD7_SHEET = "not auditable (definition not applicable: SD7's sheet not identified by the declared name rule)"
SD7_HEADER = "not auditable (definition not applicable: SD7's header row not found by the declared column rule)"
SD7_INTERRUPTED = "not auditable (definition not applicable: SD7 label block interrupted)"
SD7_NON_NUMERIC = "not computable (SD7's ASD column holds a non-numeric value)"
SD7_NO_COPY = "not run (no SD7 copy in this scratch layout)"          # scratch layouts only; production has one
STATUSES = (SD7_SHEET, SD7_HEADER, SD7_INTERRUPTED, SD7_NON_NUMERIC, SD7_NO_COPY)


class Sd7Refused(Exception):
    """A refusal with its R46 status (fixed vocabulary)."""

    def __init__(self, status: str, counts: dict | None = None):
        super().__init__(status)
        self.status = status
        self.counts = dict(counts or {})


class PositionRefused(Exception):
    """A transform asked for a position the wrapper did not hand over."""


def normalise_sheet_name(name) -> str:
    return "".join(ch for ch in str(name).casefold() if ch.isalnum())


def sheet_matches(names) -> list[int]:
    """Indexes of the sheet names the rule selects (in memory; names are never printed)."""
    return [k for k, n in enumerate(names) if SHEET_RULE.match(normalise_sheet_name(n))]


def _is_asd(v) -> bool:
    return isinstance(v, str) and v.strip().casefold() == "asd"


def asd_position(header) -> int | None:
    hits = [j for j, v in enumerate(header) if _is_asd(v)]
    if len(hits) != 1 or hits[0] == 0:
        return None
    return hits[0]


def asd_rule(pass_no: int):
    """The column rule handed to the guard (a function of the header row returning positions; [] refuses)."""
    if pass_no not in (1, 2):
        raise ValueError("SD7 pass")

    def rule(header) -> list[int]:
        a = asd_position(list(header))
        if a is None:
            return []
        return [0] if pass_no == 1 else [0, a]
    rule.sd7_pass = pass_no
    return rule


def _empty(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def dk_kind(label, dk_names: set) -> str:
    """R42 (d)'s normaliser on one cell: 'dk' (matches a DK label), 'dropped' (lateral ventricle / global measure) or
    'nothing'."""
    from . import forms as FM
    recognised = set(dk_names) | set(FM.SD7_ALIASES) | {FM.SD7_LATVENT} | set(FM.SD7_GLOBAL)
    p = FM.sd7_label_parse(str(label), recognised)
    if p["name"] == "" or p["name"] in FM.SD7_GLOBAL or p["name"] == FM.SD7_LATVENT:
        return "dropped"
    return "dk" if p["name"] in dk_names else "nothing"


def label_block(rows: list, h: int, dk_names: set) -> dict:
    """R46 (d) on the guard's rows: the block's row indexes; after the block, the non-empty position-0 cells counted
    and checked (a DK match refuses: SD7_INTERRUPTED)."""
    i = h + 1
    n_skipped = 0
    while i < len(rows) and _empty(rows[i][0] if rows[i] else None):
        i += 1
        n_skipped += 1
    start = i
    while i < len(rows) and not _empty(rows[i][0] if rows[i] else None):
        i += 1
    block = list(range(start, i))
    after = [r[0] for r in rows[i:] if r and not _empty(r[0])]
    kinds = [dk_kind(v, dk_names) for v in after]
    counts = dict(n_rows_skipped_before_block=n_skipped, n_block_rows=len(block), n_cells_after_block=len(after),
                  n_after_block_matching_dk=sum(1 for k in kinds if k == "dk"),
                  n_after_block_dropped_kind=sum(1 for k in kinds if k == "dropped"))
    if not block:
        # fix round 4, item 2: an empty block lists no label - R42 (d)'s frozen fail-closed outcome, 'SD7 labels
        # unmatched' (no new status string); the count says the block was empty
        from . import forms as FM
        raise Sd7Refused(FM.SD7_UNMATCHED, dict(counts, block_empty=True))
    if counts["n_after_block_matching_dk"]:
        raise Sd7Refused(SD7_INTERRUPTED, counts)
    return dict(rows=block, counts=counts)


def value_of(v) -> tuple[str, float | None]:
    """R46 (f): ('value', x) | ('missing', None) | ('refuse', None)."""
    if v is None:
        return "missing", None
    if isinstance(v, bool):
        return "refuse", None
    if isinstance(v, (int, float)):
        x = float(v)
        return ("value", x) if math.isfinite(x) else ("refuse", None)
    if isinstance(v, str):
        s = v.strip().casefold()
        if s == "" or s in MISSING_TEXTS or s in EXCEL_ERRORS:
            return "missing", None
    return "refuse", None


class PositionView:
    """The declared positions of the block handed to a transform (a wrapper-side mask: other positions are never
    handed over, also on a clean sheet) with a log of the positions each transform consumes."""

    def __init__(self, columns: dict, handed: tuple):
        self._cols = {int(k): list(v) for k, v in columns.items() if int(k) in set(handed)}
        self.handed = tuple(sorted(int(k) for k in handed))
        self.log: list[int] = []

    def column(self, pos: int) -> list:
        self.log.append(int(pos))
        if int(pos) not in self._cols:
            raise PositionRefused("a position the wrapper did not hand over")
        return list(self._cols[int(pos)])

    def consumed(self) -> list[int]:
        return sorted(set(self.log))
