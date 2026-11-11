"""A1 results writer: RUN_PLAN §16 assembly (arcs/audit/RUN_PLAN.md v3.1, FROZEN sha256 16c60232...; R1, R11, R26,
R27, R29; RUN_PLAN_amend_3.md B6). ASSEMBLY ONLY: no statistic is computed here. The one piece of arithmetic is R29's
descriptive Benjamini-Hochberg q over conjunction p's the runner wrote (prereg_amend_3.md:77, "descriptive").

    python -X utf8 -m a1_audit.report_cells --gate {ungated,G2,G1} [--incomplete {refuse,skip}]
           [--results-root DIR] [--out DIR] [--repo DIR]

Reads, for the gate named and (for the headline and the factorial) for every other gate present:
  <results-root>/a1_run/<ungated|G2|G1>/<verdict|descriptor|sensitivity>/  (run.py's writer: row_NNNN.json,
  row_NNNN_repro.json, row_NNNN_rlm.json, RUN_SUMMARY.json, launch_record.json)
and the frozen claims register (claims_register.tsv through loader.parse_tsv_bytes, its bytes asserted against the L2
pin; claims_register.md's section-4 R4 block and prereg_amend_5.md's headline text, each asserted against FROZEN.txt).
Writes (each written to a tmp file, os.replace'd, read back and compared; rule 8):
  <out>/a1_run/<gate>/cells.jsonl   one line per TSV row of the gate (computed or not), every §16 field the records hold
  <out>/a1_run/<gate>/cells.md      a readable table per target; non-ASD outcomes and not-ASD claims apart; m' beside m
  <out>/a1_run/<gate>/headline.json the interim headline (§16 :1673-1690) for the gates that have run, its composition
  <out>/MANIFEST_claims.md          R26: the claim x level x null x parcellation x multiverse factorial with status
<out> defaults to <results-root> (= arcs/audit/results). A field absent because a pass has not run reads "pass not run".

Apparatus (rule 8), each refusing with ReportRefused:
- loader: a pass is read only when complete (RUN_SUMMARY.json present); its row files must be exactly the summary's
  files with the summary's sha256; every record names its pass, gate, row, cell id, TSV status, run identity and a
  provenance whose run commit / code hash are the identity's; a DEV / plant / launch-refused record is refused; every
  pass of a gate shares one run identity (RUN_IDENTITY_FIELDS: run commit, code hash, K, G6l mode, sources, seed view);
  a descriptor / sensitivity record that names its verdict result by sha256 must name the one read;
- R1: every leg's reported p must equal min(1, 2 p(d*)) (two-sided) / p(d) (one-sided) and the literal per-leg
  min(1, 2 min(p(+), p(-))) must equal its formula; the conjunction p must equal R1's (tests plant a broken record);
- B6: the population composition is built only from TSV fields and the pass records' outcome / status fields; a
  status taken from a reproduction record is refused (assert_b6; a planted comparator status must be caught);
- wording: the headline sentences and every composed reading are checked for the forbidden words of
  prereg_amend_5.md:148-149 ("refuted", "fails", "does not replicate", "not supported"); so is all of cells.md;
- the register: the TSV-derived population numbers must equal claims_register.md's R4 block (rows, m, m', population
  interim / full, lower view, gate units, cross-tab); the interim "0 of 14 can survive" is DERIVED from the TSV and the
  results and asserted against that block, never written as a constant.

Readings this writer makes where §16 leaves the assembly a choice (U-RC; listed in the hand-off):
U-RC1 a pass without RUN_SUMMARY.json is incomplete: refused by default; with --incomplete skip it is not read and its
  fields read "pass not run (pass incomplete: RUN_SUMMARY.json absent; not read)".
U-RC2 a row of the gate absent from a complete pass's RUN_SUMMARY reads "pass not run (row not in this pass)".
U-RC3 "a low fraction" (§16 :1685) = survivals fewer than half the population units in view.
U-RC4 a two-cohort survival reads "calibrated evidence" iff every map's R27 reading does.
U-RC5 a published-null cell with a verdict reads as claims_register.md:216-220 ("detectable by the verdict (the published
  analysis reported none)" / "not detectable at this power (as published)") with its R27 labels.
U-RC6 a component cell's reading is the verdict record's component reading (prereg_amend_5.md:156); the record's
  r27 'reading' is kept beside it as recorded (run.py r27_for_map tests kind == "component", component records carry
  "component-permutation" / "component-parametric", so its swap never applies: reported, not fixed here).
U-RC7 the population in view = the TSV's 'in' rows plus the 'on opening: in' rows of every gate whose verdict pass is
  complete; the other gates' units are listed apart and counted neither way (claims_register.md:256-262).
U-RC8 run-time flags entering the composition: a record status "not testable (< 5)" (at use: out of the population,
  listed); a record status or primary status beginning "not auditable" (flag not auditable, §1.8 precedence); a pass
  outcome "not run" / "refused" / "stub" on a row whose route computes (pending: no §1.8 category; stated). A TSV
  reproduction "not reproduced ..." or an R37 check labelled "not reproduced ..." on a row whose TSV reproduction is a
  4.1 check flags it (R29; the population drops it only if it is a full-verdict claim, §1.2).
U-RC9 inference-level strata: "gene null only (uniform)", "gene null only (structured)", else the text before ':'.
U-RC10 per-target "any survives" and the added nine count cell_class 'claim' rows only.
U-RC11 BH: per-gate interim q over the gate's family members (labelled interim); the final q only when all three gates'
  verdict passes are complete, over the union (R29 :1041-1042).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

from . import loader as LD

SCRIPT_REL = "arcs/audit/src/a1_audit/report_cells.py"
REPO = Path(__file__).resolve().parents[4]
GATES = ("ungated", "G2", "G1")
GATE_ARG = {"ungated": "none", "G2": "G2", "G1": "G1"}            # run.py GATE_DIR inverted
GATE_ROWS = {"ungated": ("none",), "G2": ("G2",), "G1": ("G1", "G1+G2")}   # run.py U3 (Dear's G1+G2 rows in G1)
NOMINAL_OPEN = {"ungated": frozenset(), "G2": frozenset({"G2"}), "G1": frozenset({"G1"})}
PASSES = ("verdict", "descriptor", "sensitivity")                 # run.py PASSES
RUN_IDENTITY_FIELDS = ("run_commit", "code_hash", "K", "g6l_mode", "sources", "seed_view")   # run.py C5
PNR = "pass not run"
PNR_INCOMPLETE = "pass not run (pass incomplete: RUN_SUMMARY.json absent; not read)"
PNR_ROW = "pass not run (row not in this pass)"
FORBIDDEN = ("refuted", "fails", "does not replicate", "not supported")   # prereg_amend_5.md:148-149; RUN_PLAN :1686
FORBIDDEN_RE = re.compile(r"\b(" + "|".join(re.escape(w) for w in FORBIDDEN) + r")\b", re.I)
# the frozen texts the headline quotes (asserted present in their frozen files at load)
CURVES = ("C-sp .970 at a = .9; C-gene .585–.666 at a = .9; C-align .018–.074 / .060–.196 / "
          ".106–.352 at a = .3 / .5 / .7")                  # prereg_amend_5.md:170-171
FAILED_AS_GATES = "failed as gates under amendment 3"            # prereg_amend_5.md:96-97
LOW_FRACTION = "few published claims are detectable by a calibrated test at this power"   # prereg_amend_5.md:176-177
A6_CELLS = ("MAMAT-E-Tissue-URG", "MAMAT-E-Tissue-DRG")          # RUN_PLAN §16 :1679 names them; §6 A6
A6_DECISION = ("ARC.md:863-868 (orchestrator, standing delegation): no small-pool amendment; a verdict leg whose null "
               "pool is smaller than S reads 'not auditable (definition not applicable: null pool smaller than S)'")
# register v6 R8 / §1.8 precedence, ported from the frozen builder (claims_register_tsv_build.py:3237-3264, blob of
# the freeze manifest); the port is checked against the register's R4 block at every run (check_register_numbers)
PRECEDENCE = ("deferred", "not testable (< 5)", "not auditable", "not testable as stated", "component-level",
              "no calibrated test")
R2_FLAG = "S conditional (§1.6 R2)"   # builder normalize(R2_FLAG)
TESTED = "tested (full verdict)"
ON_OPENING = "; on opening: "
M_PRIME_YES = "counted in m' (the view's m): yes"
CHECK_PREFIX = "4.1 check"
TSV_NOT_REPRODUCED = "not reproduced"
ENGINE_NOT_OK = ("g6l unmatched", "g6l degenerate", "unmatched", "degenerate", "uninformative", "resolution-limited")
PENDING_OUTCOMES = ("not run", "refused", "stub")
# at-use statuses a pass record can write that move a cell's category, with the frozen rule that writes each (texts
# asserted equal to forms / wp3_sd7 / wp3_layout / verdict constants in tests/test_report_cells.py; an unknown text
# reads "as the record states")
STATUS_RULES = {
    "not auditable (definition not applicable: SD7 labels unmatched)": "RUN_PLAN_amend_2 R42 (d)",
    "not auditable (definition not applicable: no SD7 cortical label matched)": "RUN_PLAN_amend_2 R42 (e)",
    "not auditable (definition not applicable: abagen sample assignment not runnable)": "RUN_PLAN R10 :659",
    "not auditable (definition not applicable: SD7's sheet not identified by the declared name rule)":
        "RUN_PLAN_amend_3 R46 (b)",
    "not auditable (definition not applicable: SD7's header row not found by the declared column rule)":
        "RUN_PLAN_amend_3 R46 (c)",
    "not auditable (definition not applicable: SD7 label block interrupted)": "RUN_PLAN_amend_3 R46 (d)",
    "not auditable (map changed)": "RUN_PLAN §17 :1703-1704",
    "not auditable (definition not applicable: the declared Moreau sheet layout not matched)": "RUN_PLAN §8 step 4",
    "not auditable (definition not applicable: null pool smaller than S)": "RUN_PLAN R8 (A6: ARC.md:863-868)",
}
# the WP4 / G2 run-time statuses (texts asserted equal to wp4_layout / fetch_extract constants in
# tests/test_report_cells.py). Each one, written by a pass record of the row, outranks the register status at use
# (at_use_status: the first pass in PASSES order that wrote one) - it states what the run found, the register only
# what was planned. They move no count: the composition reads only the 'not auditable' flag (record_run_flags), as
# before (RUN_PLAN_amend_5 §6: "A7-A9 move counts only through the frozen statuses").
_G2_STAGE = "not run (the G2 material stage refused this object: %s)"           # wp4_layout.STATUS_STAGE_REFUSED
_UPSTREAM_RULE = "RUN_PLAN §8 (a stage refusal; text fixed in wp4_layout at run 5, 2026-10-21; no frozen text of its own)"
G2_RUNTIME_RULES = {
    "not auditable (definition not applicable: the declared eTable13 layout not matched)":
        "RUN_PLAN_amend_4 R61 (A7: RUN_PLAN_amend_5 §6)",
    "not auditable (definition not applicable: the declared Giacomel sheet layout not matched)":
        "RUN_PLAN_amend_4 R54 (A8: RUN_PLAN_amend_5 §6)",
    "not computable (the paper's GEDAR map layout not matched)": "RUN_PLAN_amend_4 R56",
    "not auditable (definition not applicable: the paper's code not runnable here)":
        "RUN_PLAN_amend_4 R58 (h) (R17 fallback, RUN_PLAN.md:822-824; A9: RUN_PLAN_amend_5 §6)",
    "refused (stage failed upstream)": _UPSTREAM_RULE,
    _G2_STAGE % "refused (stage failed upstream)": _UPSTREAM_RULE,
    _G2_STAGE % "refused (stage failed)": "RUN_PLAN §8 (the G2 material stage refused this object)",
    _G2_STAGE % "refused (carrier in quarantine; the operator moves it back)":
        "RUN_PLAN §8 step 6 (RUN_PLAN.md:1270-1273: the runner refuses any path under _quarantine)",
}
STATUS_RULES.update(G2_RUNTIME_RULES)
LT5_AT_USE_RULE = "prereg §4 / RUN_PLAN U14 (fewer than 5 columns of S at use)"
COMPONENT_R27_NOTE = ("R27 block NOT TO BE QUOTED: for a component claim the recorded R27 reading (A3's full-verdict "
                      "reading, e.g. 'not detectable at this power') and its species-leg label do not apply (a component "
                      "claim has no species leg); the reading is run.py r27_for_map's label defect (it tests kind == "
                      "'component', component records carry 'component-permutation' / 'component-parametric'; decision "
                      "ev-1a12dffe1a85af7). The cell's reading is the verdict record's component reading "
                      "(prereg_amend_5.md:156); m, f/m, c_S, R2_grad and R2_|x| are set / map descriptors and stand.")
REGISTER_CATS = ("not auditable", "not testable as stated", "component-level", "no calibrated test",
                 "tested (full verdict)", "tested (full verdict) [conditional on its carrier]")
FROZEN_FILES = {"claims_register.md": "arcs/audit/claims_register.md",
                "prereg_amend_5.md": "arcs/audit/prereg_amend_5.md",
                "RUN_PLAN.md": "arcs/audit/RUN_PLAN.md",
                "RUN_PLAN_amend_3.md": "arcs/audit/RUN_PLAN_amend_3.md"}


class ReportRefused(RuntimeError):
    """A precondition of the writer is not met (incomplete or mixed inputs, a broken identity, a forbidden word ...)."""


def refuse(msg: str):
    raise ReportRefused("report_cells refused: " + msg)


# ================================================================================================================
# small helpers
# ================================================================================================================
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def lf(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


def sha256_json(o) -> str:
    """run.py sha256_json on a loaded JSON object (A3.jsonable is the identity on loaded JSON)."""
    return sha256_bytes(json.dumps(o, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def canon(o):
    return json.loads(json.dumps(o, sort_keys=True))


def read_json(p: Path) -> tuple[dict, str, bytes]:
    b = p.read_bytes()
    try:
        return json.loads(b.decode("utf-8")), sha256_bytes(b), b
    except (UnicodeDecodeError, ValueError) as e:
        refuse(f"{p.name}: not UTF-8 JSON ({type(e).__name__})")


def dget(o, *path, default=None):
    for k in path:
        if isinstance(o, dict) and k in o:
            o = o[k]
        else:
            return default
    return o


def pdir(p: dict | None) -> tuple:
    """(p(+), p(-)) from a JSON direction dict ({'1': .., '-1': ..}); (None, None) when absent."""
    if not isinstance(p, dict):
        return None, None
    return p.get("1", p.get(1)), p.get("-1", p.get(-1))


def fnum(v, nd: int = 4) -> str:
    if v is None:
        return "-"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (int, float)):
        if isinstance(v, float) and not math.isfinite(v):
            return str(v)
        return f"{v:.{nd}g}"
    return str(v)


def short(text, n: int = 70) -> str:
    s = "" if text is None else str(text).replace("|", "/").replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def check_wording(text: str, where: str) -> None:
    """prereg_amend_5.md:148-149 / RUN_PLAN §16 :1686: none of the forbidden words in a composed statement."""
    m = FORBIDDEN_RE.search(text or "")
    if m:
        refuse(f"forbidden word {m.group(1)!r} in {where} (prereg_amend_5.md:148-149)")


def frozen_pins(repo: Path) -> dict:
    """{file name: sha256} from arcs/audit/FROZEN.txt (the last entry per file)."""
    out = {}
    for ln in (repo / "arcs/audit/FROZEN.txt").read_text(encoding="utf-8").splitlines():
        parts = ln.split()
        if len(parts) == 3:
            out[parts[2]] = parts[1]
    return out


def read_frozen(repo: Path, name: str) -> tuple[str, str]:
    """(text, sha256 of LF bytes) of a FROZEN file, asserted against FROZEN.txt."""
    pins = frozen_pins(repo)
    b = lf((repo / FROZEN_FILES[name]).read_bytes())
    sha = sha256_bytes(b)
    if pins.get(name) != sha:
        refuse(f"{name}: sha256 {sha[:12]}... differs from FROZEN.txt's pin")
    return b.decode("utf-8"), sha


def collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text)


# ================================================================================================================
# the register: TSV (loader), the R4 block, the frozen headline texts
# ================================================================================================================
class Register:
    def __init__(self, repo: Path):
        self.repo = repo
        p = repo / LD.TSV_PATH
        data = lf(p.read_bytes())
        self.tsv_sha256 = sha256_bytes(data)
        if self.tsv_sha256 != LD.TSV_SHA256:
            refuse("claims_register.tsv bytes differ from the L2 pin (loader.TSV_SHA256)")
        _, rows = LD.parse_tsv_bytes(data)
        if len(rows) != LD.N_ROWS:
            refuse(f"TSV holds {len(rows)} rows, not {LD.N_ROWS}")
        self.rows = {r.row: r for r in rows}
        reg_text, self.register_sha256 = read_frozen(repo, "claims_register.md")
        self.r4 = parse_r4_block(reg_text)
        a5_text, self.amend5_sha256 = read_frozen(repo, "prereg_amend_5.md")
        a5 = collapse(a5_text)
        for frag in (CURVES, FAILED_AS_GATES, LOW_FRACTION):
            if collapse(frag) not in a5:
                refuse(f"the frozen headline text {frag[:40]!r}... is not in prereg_amend_5.md")
        for w in FORBIDDEN:
            if f'"{w}"' not in a5:
                refuse(f"the forbidden word {w!r} is not listed in prereg_amend_5.md")
        _, self.run_plan_sha256 = read_frozen(repo, "RUN_PLAN.md")
        _, self.amend3_sha256 = read_frozen(repo, "RUN_PLAN_amend_3.md")
        by_id = {}
        for r in rows:
            by_id.setdefault(r.cell_id, []).append(r.row)
        self.by_cell_id = by_id

    def gate_rows(self, gate: str) -> list:
        return [r for r in self.rows.values() if r.gate in GATE_ROWS[gate]]

    def gate_of_row(self, r) -> str:
        for g, cols in GATE_ROWS.items():
            if r.gate in cols:
                return g
        refuse(f"row {r.row}: gate column {r.gate!r} maps to no results gate")


def parse_r4_block(text: str) -> dict:
    """claims_register.md section 4's fenced R4 block ("key = integer" lines)."""
    lines = text.split("\n")
    try:
        start = next(i for i, ln in enumerate(lines) if ln.startswith("R4: section 4 numbers"))
    except StopIteration:
        refuse("claims_register.md: the R4 block is absent")
    out = {}
    for ln in lines[start + 1:]:
        if ln.startswith("```"):
            break
        m = re.fullmatch(r"(.+?) = (\d+)", ln.strip())
        if m:
            out[m.group(1)] = int(m.group(2))
    if "population.interim" not in out or "m.lower" not in out:
        refuse("claims_register.md: the R4 block lacks population.interim / m.lower")
    return out


# --- the builder port (claims_register_tsv_build.py:3218-3264), on loader Rows --------------------------------
def base_status(r) -> str:
    """the status under the row's gate (loader.parse_gated), else verbatim (Dear / Vairam-Roy keep their deferral)."""
    g = r.gated
    return g[1] if g is not None else r.status


def row_flags(r, extra: set | None = None) -> set:
    """builder row_flags: the status flags a row carries (primary and every 'also ...'), component form; R2 aside."""
    s = r.status
    b = base_status(r)
    f = set()
    if b != s or s.startswith("deferred"):
        f.add("deferred")
    for flag in ("not testable (< 5)", "not auditable", "not testable as stated", "no calibrated test"):
        if b.startswith(flag) or ("; also " + flag) in b or (" also " + flag) in b:
            f.add(flag)
    if r.claim_form == "component":
        f.add("component-level")
    if extra:
        f |= extra
    return f


def pop_category(r, view: str = "upper", extra: set | None = None) -> str:
    """builder pop_category (§1.2; R8 precedence) on the population on opening; extra = run-time flags (U-RC8)."""
    f = row_flags(r, extra) - {"deferred"}
    if view == "lower" and R2_FLAG in r.status:
        f.add("not auditable")
    for p in PRECEDENCE[1:]:
        if p in f:
            return p
    return TESTED + (" [conditional on its carrier]" if base_status(r).startswith("conditional") else "")


def hl_final(r) -> str:
    hp = r["headline_population"]
    return hp.split(ON_OPENING, 1)[1] if hp.startswith("out (interim)") else hp


def population_rows(reg: Register, gates_run: set) -> tuple[list, dict]:
    """U-RC7: (rows in view, {gate: rows listed apart}). 'in' = the interim population; a gate's 'out (interim)'
    rows whose on-opening text begins 'in' join once that gate has run. Added targets never (builder :3920-3925)."""
    interim = [r for r in reg.rows.values() if r["frozen11_row"] != "added" and r["headline_population"].startswith("in")]
    apart = {}
    view = list(interim)
    for g in ("G1", "G2"):
        rows = [r for r in reg.rows.values() if r["frozen11_row"] != "added"
                and r["headline_population"].startswith(f"out (interim): deferred (gate {g} closed")
                and hl_final(r).startswith("in")]
        if g in gates_run:
            view += rows
        else:
            apart[g] = rows
    return sorted(view, key=lambda r: r.row), apart


def register_numbers(reg: Register) -> dict:
    """The R4 numbers from the TSV (builder register_numbers :3448-3480, the keys the block holds)."""
    rows = list(reg.rows.values())
    interim, _ = population_rows(reg, set())
    final, _ = population_rows(reg, {"G1", "G2"})
    _, apart = population_rows(reg, set())
    d = {"rows": len(rows),
         "m.lower": sum(1 for r in rows if r.m_membership == "yes"),
         "m.upper": sum(1 for r in rows if r.m_membership in ("yes", "upper bound only")),
         "population.interim": len(interim), "population.full (at most)": len(final),
         "gate.G1.units": len(apart["G1"]), "gate.G2.units": len(apart["G2"])}
    d["m.secondary.near_miss"] = d["m.lower"] + sum(1 for r in rows if M_PRIME_YES in r["secondary_view_near_miss_status"])
    for r in interim:
        k = "population.interim.%s" % pop_category(r)
        d[k] = d.get(k, 0) + 1
    for r in final:
        k = "population.full.%s" % pop_category(r)
        d[k] = d.get(k, 0) + 1
        k = "population.full.lower view.%s" % pop_category(r, "lower")
        d[k] = d.get(k, 0) + 1
    d["population.full.provisional (S conditional, R2)"] = sum(1 for r in final if R2_FLAG in r.status)
    d["population.full.not auditable and also not testable as stated"] = sum(
        1 for r in final if {"not auditable", "not testable as stated"} <= row_flags(r))
    for form in ("component-level in form", "other form"):
        for na in ("not auditable", "auditable"):
            d["crosstab.%s.%s" % (form, na)] = sum(
                1 for r in final if (r.claim_form == "component") == (form == "component-level in form")
                and ("not auditable" in row_flags(r)) == (na == "not auditable"))
    for r in rows:
        if r.m_membership == "yes":
            k = "m.target.%s" % r.target_key
            d[k] = d.get(k, 0) + 1
    d["buch.units"] = sum(1 for r in final if r.target_key == "buch2023asdsubgroups")
    return d


def check_register_numbers(reg: Register) -> dict:
    """Every R4 block number must equal the TSV-derived one (the builder port and the population view asserted)."""
    got = register_numbers(reg)
    bad = {k: (v, got.get(k)) for k, v in reg.r4.items() if got.get(k, 0) != v}
    extra = {k: v for k, v in got.items() if k not in reg.r4 and v != 0}
    if bad or extra:
        refuse(f"TSV-derived register numbers differ from claims_register.md's R4 block: {bad} {extra}")
    return dict(checked=len(reg.r4), equal=True)


# ================================================================================================================
# loading the passes
# ================================================================================================================
class PassData:
    def __init__(self, gate: str, name: str, d: Path):
        self.gate, self.name, self.dir = gate, name, d
        self.state = "absent"
        self.summary = None
        self.summary_sha = None
        self.launch = None
        self.launch_sha = None
        self.identity = None
        self.rows: dict[int, dict] = {}
        self.row_sha: dict[int, str] = {}
        self.repro: dict[int, tuple] = {}
        self.rlm: dict[int, tuple] = {}
        self.unread: list[str] = []
        self.note = None
        self.incomplete_identities: list[str] = []
        self.n_files_present = 0

    def complete(self) -> bool:
        return self.state == "complete"

    def ident(self) -> dict:
        return {k: canon(self.identity.get(k)) for k in RUN_IDENTITY_FIELDS} if self.identity is not None else None


ROW_RE = re.compile(r"\Arow_(\d{4})(?:_(repro|rlm))?\.json\Z")


def _check_header(rec: dict, pd_: PassData, what: str):
    if rec.get("stamp") is not None:
        refuse(f"{pd_.gate}/{pd_.name}/{what}: a DEV-stamped record ({rec.get('stamp')!r}) is not a claim result")
    if rec.get("plant") is not None:
        refuse(f"{pd_.gate}/{pd_.name}/{what}: a plant record is not a claim result")
    if rec.get("pass") != pd_.name:
        refuse(f"{pd_.gate}/{pd_.name}/{what}: the record names pass {rec.get('pass')!r}")
    if rec.get("gate") != GATE_ARG[pd_.gate]:
        refuse(f"{pd_.gate}/{pd_.name}/{what}: the record names gate {rec.get('gate')!r}")
    ri = rec.get("run_identity")
    if not isinstance(ri, dict) or any(k not in ri for k in RUN_IDENTITY_FIELDS):
        refuse(f"{pd_.gate}/{pd_.name}/{what}: no run identity")
    mine = {k: canon(ri.get(k)) for k in RUN_IDENTITY_FIELDS}
    if mine != pd_.ident():
        diff = [k for k in RUN_IDENTITY_FIELDS if mine[k] != pd_.ident()[k]]
        refuse(f"{pd_.gate}/{pd_.name}/{what}: mixed run identities within the pass (differs in: {', '.join(diff)})")
    prov = rec.get("provenance") or {}
    if prov.get("run_commit") != ri.get("run_commit"):
        refuse(f"{pd_.gate}/{pd_.name}/{what}: provenance names commit {str(prov.get('run_commit'))[:12]}, "
               f"the run identity {str(ri.get('run_commit'))[:12]}")
    ch = dget(prov, "code", "code_hash")
    if ch != ri.get("code_hash"):
        refuse(f"{pd_.gate}/{pd_.name}/{what}: provenance code hash differs from the run identity's")


def load_pass(results_root: Path, gate: str, name: str, reg: Register, incomplete: str,
              base: Path | None = None) -> PassData:
    d = (base if base is not None else results_root / "a1_run" / gate) / name
    pd_ = PassData(gate, name, d)
    if not d.is_dir():
        return pd_
    files = sorted(p.name for p in d.iterdir() if p.is_file())
    if "RUN_SUMMARY.json" not in files:
        if incomplete == "refuse":
            refuse(f"{gate}/{name}: pass incomplete (RUN_SUMMARY.json absent); rerun when it has finished or pass "
                   "--incomplete skip")
        pd_.state = "incomplete"
        pd_.note = PNR_INCOMPLETE
        # identity of what is there is still checked: a gate folder never mixes runs
        ids = set()
        for fn in files:
            if ROW_RE.match(fn):
                rec, _, _ = read_json(d / fn)
                ids.add(json.dumps({k: canon((rec.get("run_identity") or {}).get(k)) for k in RUN_IDENTITY_FIELDS},
                                   sort_keys=True))
        pd_.incomplete_identities = sorted(ids)
        pd_.n_files_present = sum(1 for fn in files if ROW_RE.match(fn))
        return pd_
    pd_.state = "complete"
    pd_.summary, pd_.summary_sha, _ = read_json(d / "RUN_SUMMARY.json")
    s = pd_.summary
    pd_.identity = s.get("run_identity")
    if not isinstance(pd_.identity, dict):
        refuse(f"{gate}/{name}: RUN_SUMMARY.json has no run identity")
    _check_header(s, pd_, "RUN_SUMMARY.json")
    if s.get("launch_failed"):
        refuse(f"{gate}/{name}: the launch failed ({s.get('launch_failed')}): not a claim-bearing pass")
    if "launch_record.json" not in files:
        refuse(f"{gate}/{name}: launch_record.json absent")
    lr, pd_.launch_sha, _ = read_json(d / "launch_record.json")
    if lr.get("stamp") is not None:
        refuse(f"{gate}/{name}: the launch record is DEV-stamped")
    pd_.launch = lr.get("launch_record") or {}
    L = pd_.launch
    if L.get("passed") is not True or L.get("test_overrides") or L.get("files_root"):
        refuse(f"{gate}/{name}: the launch did not pass as a claim-bearing launch")
    if L.get("run_commit") != pd_.identity.get("run_commit"):
        refuse(f"{gate}/{name}: the launch record names another commit than the run identity")
    l2 = [a for a in L.get("assertions", []) if a.get("id") == "L2"]
    if len(l2) != 1 or l2[0].get("ok") is not True or dget(l2[0], "observed", "lf_sha256") != LD.TSV_SHA256:
        refuse(f"{gate}/{name}: L2 does not record the TSV pin")
    listed = {int(k): v for k, v in (s.get("files") or {}).items()}
    if s.get("n_rows") != len(listed) or sum((s.get("outcomes") or {}).values()) != len(listed):
        refuse(f"{gate}/{name}: RUN_SUMMARY n_rows / outcomes disagree with its file list")
    present = {}
    for fn in files:
        m = ROW_RE.match(fn)
        if not m:
            if fn not in ("RUN_SUMMARY.json", "launch_record.json", "run.log"):
                pd_.unread.append(fn)
            continue
        present.setdefault(m.group(2) or "row", {})[int(m.group(1))] = fn
    rows_present = present.get("row", {})
    if set(rows_present) != set(listed):
        refuse(f"{gate}/{name}: row files {sorted(set(rows_present) ^ set(listed))[:8]} are not the RUN_SUMMARY's "
               "file list (U-RC2: every row file must be listed)")
    allowed = {r.row for r in reg.gate_rows(gate)}
    if not set(listed) <= allowed:
        refuse(f"{gate}/{name}: rows {sorted(set(listed) - allowed)[:8]} are not rows of gate {gate}")
    for n, fn in sorted(rows_present.items()):
        rec, sha, raw = read_json(d / fn)
        if sha != listed[n] and sha256_bytes(lf(raw)) != listed[n]:
            refuse(f"{gate}/{name}/{fn}: sha256 differs from the RUN_SUMMARY's (a record changed after the pass)")
        _check_header(rec, pd_, fn)
        r = reg.rows[n]
        if rec.get("row") != n or dget(rec, "row_provenance", "row") != n:
            refuse(f"{gate}/{name}/{fn}: the record names another row")
        if rec.get("cell_id") != r.cell_id or rec.get("target_number") != r.target_no:
            refuse(f"{gate}/{name}/{fn}: cell id / target differ from the TSV's")
        if rec.get("status_tsv") != r.status or rec.get("gate_column") != r.gate:
            refuse(f"{gate}/{name}/{fn}: TSV status / gate column differ from the TSV's")
        pd_.rows[n], pd_.row_sha[n] = rec, listed[n]
    for kind, store in (("repro", pd_.repro), ("rlm", pd_.rlm)):
        for n, fn in sorted(present.get(kind, {}).items()):
            rec, sha, _ = read_json(d / fn)
            _check_header(rec, pd_, fn)
            if n not in pd_.rows or rec.get("row") != n or rec.get("cell_id") != reg.rows[n].cell_id:
                refuse(f"{gate}/{name}/{fn}: names another row or sits beside no row record of this pass")
            store[n] = (rec, sha)
    return pd_


class GateData:
    def __init__(self, gate: str, passes: dict):
        self.gate = gate
        self.passes = passes          # name -> PassData
        self.rel = f"a1_run/{gate}"   # the folder the records' 'file' fields name (a row rerun: a1_run/rerun_TAG/<gate>)
        complete = [p for p in passes.values() if p.complete()]
        self.identity = complete[0].ident() if complete else None
        self.raw_identity = complete[0].identity if complete else None

    def verdict_complete(self) -> bool:
        return self.passes["verdict"].complete()

    def any_present(self) -> bool:
        return any(p.state != "absent" for p in self.passes.values())

    def open_gates(self) -> frozenset:
        v = self.passes["verdict"]
        return LD.open_gates_from(v.launch) if v.complete() else NOMINAL_OPEN[self.gate]


def load_gate(results_root: Path, gate: str, reg: Register, incomplete: str, base: Path | None = None) -> GateData:
    passes = {name: load_pass(results_root, gate, name, reg, incomplete, base) for name in PASSES}
    gd = GateData(gate, passes)
    ids = {name: p.ident() for name, p in passes.items() if p.complete()}
    first = next(iter(ids.values()), None)
    for name, i in ids.items():
        if i != first:
            diff = [k for k in RUN_IDENTITY_FIELDS if i[k] != first[k]]
            refuse(f"gate {gate}: mixed run identities across passes ({name} differs in: {', '.join(diff)})")
    for name, p in passes.items():   # a skipped (incomplete) pass must not belong to another run either
        if p.state == "incomplete" and first is not None:
            want = json.dumps(first, sort_keys=True)
            if any(s != want for s in getattr(p, "incomplete_identities", [])):
                refuse(f"gate {gate}: the incomplete {name} pass holds records of another run identity")
    # cross-pass links: a descriptor / sensitivity record names the verdict result it used (run.py C5 / U12)
    v = passes["verdict"]
    for name in ("descriptor", "sensitivity"):
        p = passes[name]
        if not p.complete():
            continue
        for n, rec in p.rows.items():
            want = (dget(rec, "result", "direction_from_verdict", "verdict_result_sha256")
                    or dget(rec, "result", "primary_result_sha256"))
            if want is None:
                continue
            if not v.complete() or n not in v.rows:
                refuse(f"gate {gate}: {name} row {n} names a verdict result, but no verdict record of it was read")
            if sha256_json(v.rows[n].get("result")) != want:
                refuse(f"gate {gate}: {name} row {n} names a verdict result other than the one read (sha256)")
    return gd


# ================================================================================================================
# leg views and the R1 identities
# ================================================================================================================
LEG_KEYS = ("p_reported", "p_per_leg_two_sided", "p_registered_tail", "floor_one_sided", "floor_effective", "floor",
            "n", "n_null", "kind", "seed_leg", "seed", "K", "rule", "pool", "m", "target", "label", "reason")


def leg_view(rec: dict) -> dict:
    p = rec.get("p_one_sided", rec.get("p"))
    pp, pm = pdir(p)
    out = {"status": rec.get("status"), "p_plus": pp, "p_minus": pm}
    for k in LEG_KEYS:
        if k in rec and not isinstance(rec[k], (dict, list)):
            out[k] = rec[k]
    return out


def legs_view(legs) -> dict:
    if not isinstance(legs, dict):
        return {}
    return {k: leg_view(v) for k, v in legs.items() if isinstance(v, dict)}


def check_r1_leg(where: str, lv: dict, d, two_sided: bool) -> None:
    """R1 :429-441: reported p = min(1, 2 p(d*)) two-sided / p(d) one-sided; literal per-leg min(1, 2 min) beside."""
    pp, pm = lv.get("p_plus"), lv.get("p_minus")
    if "p_reported" not in lv:
        return
    rep = lv["p_reported"]
    if pp is None or pm is None or d is None:
        if rep is not None:
            refuse(f"{where}: a reported p without both one-sided p's / without d* (R1, R36 (a))")
    else:
        p = {1: pp, -1: pm}[d]
        want = min(1.0, 2.0 * p) if two_sided else float(p)
        if rep != want:
            refuse(f"{where}: reported p {rep!r} != R1's {want!r} (d* = {d}, two-sided {two_sided})")
    if two_sided:
        lit = lv.get("p_per_leg_two_sided")
        want = None if (pp is None or pm is None) else min(1.0, 2.0 * min(pp, pm))
        if lit != want:
            refuse(f"{where}: per-leg two-sided p {lit!r} != the literal min(1, 2 min) {want!r} (R1 :440-441)")
    elif lv.get("p_per_leg_two_sided") is not None:
        refuse(f"{where}: a one-sided claim carries a per-leg two-sided p")


def verdict_core(v: dict) -> tuple[dict, bool]:
    """(the computed record, is a descriptor row): a descriptor row keeps its computed record under 'descriptor'."""
    if v.get("descriptor_row"):
        return v.get("descriptor") or {}, True
    return v, False


def check_r1_verdict(where: str, v: dict) -> None:
    core, _ = verdict_core(v)
    two = bool(core.get("two_sided"))
    if core.get("two_cohort"):
        for lab, mv in (core.get("per_map") or {}).items():
            for k, lv in legs_view(mv.get("legs")).items():
                check_r1_leg(f"{where} [{lab}] leg {k}", lv, core.get("d_star"), two)
        ps = [mv.get("p_conjunction") for mv in (core.get("per_map") or {}).values()]
        if core.get("p_conjunction") is not None and all(p is not None for p in ps) and \
                core.get("p_conjunction") != max(ps) and not core.get("tie_common_max"):
            refuse(f"{where}: two-cohort p {core.get('p_conjunction')!r} != the larger map p (claims_register.md:1640)")
        return
    d = core.get("d_star")
    lvs = legs_view(core.get("legs"))
    for k, lv in lvs.items():
        check_r1_leg(f"{where} leg {k}", lv, d, two)
    pc = core.get("p_conjunction")
    if pc is None or d is None:
        return
    members = ("Level 0", "site", "species") if core.get("kind") == "full" else ("Level 0", "site")
    reps = [lvs.get(m, {}).get("p_reported") for m in members]
    if any(r is None for r in reps) or pc != max(reps):
        refuse(f"{where}: conjunction p {pc!r} != the max of the reported p's {reps!r} (R1)")
    conj = pdir(core.get("conjunction_one_sided"))
    c = {1: conj[0], -1: conj[1]}[d]
    if c is not None:
        want = min(1.0, 2.0 * c) if two else float(c)
        if pc != want:
            refuse(f"{where}: conjunction p {pc!r} != R1's min(1, 2 min_d max_leg p) {want!r}")


# ================================================================================================================
# reproduction checks (R27 / R37) and the B6 guard
# ================================================================================================================
def find_checks(o, path: str = "") -> list:
    """Every R37 check record (reporting.reproduction_check: a 'label' and R37's rule text) inside o."""
    from . import reporting as RPT
    out = []
    if isinstance(o, dict):
        if o.get("rule") == RPT.R37_RULE and isinstance(o.get("label"), str):
            out.append((path or "/", o))
        for k, v in o.items():
            out += find_checks(v, f"{path}/{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out += find_checks(v, f"{path}/{i}")
    return out


def comparator_statuses(o) -> set:
    """Every 'not computable (...)' / 'not run (...)' status text inside a reproduction record (B6's comparators)."""
    out = set()
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, str) and (v.startswith("not computable") or v.startswith("not run")
                                        or v.startswith("not auditable")):
                out.add(v)
            else:
                out |= comparator_statuses(v)
    elif isinstance(o, list):
        for v in o:
            out |= comparator_statuses(v)
    return out


def assert_b6(row: int, basis: list, repro_statuses: set) -> None:
    """RUN_PLAN_amend_3 B6: no comparator status reaches the cell-status composition. basis: [(value, source)] of
    every status the composition read; a source naming a reproduction record, or a value that only a reproduction
    record holds, is refused."""
    for value, source in basis:
        if "repro" in source or "rlm" in source:
            refuse(f"row {row}: the composition read a status from {source} (B6: comparator statuses never reach it)")
        if value in repro_statuses and not source.startswith(("tsv:", "record:")):
            refuse(f"row {row}: the composition read the comparator status {value[:50]!r} (B6)")


# ================================================================================================================
# one cell
# ================================================================================================================
def _route_plan(row, open_gates):
    from . import run as RN   # the runner's own dispatch (pure: nothing loaded, no statistic)
    return RN.classify(row, open_gates)


def computing_passes(route: str) -> dict:
    """{field: pass} by route (RUN_PLAN §4 legs table; run.py FORM_NO_PASS)."""
    if route.startswith("verdict: component"):
        return dict(T="verdict", legs="verdict", descriptor=None, sensitivity="sensitivity")
    if route.startswith("verdict:"):
        return dict(T="verdict", legs="verdict", descriptor="descriptor", sensitivity="sensitivity")
    if route == "descriptor: gene-set-only (R10)":
        return dict(T="descriptor", legs=None, descriptor="descriptor", sensitivity=None)
    if route == "descriptor: signed-weight rho (P15)":
        return dict(T="verdict", legs="verdict", descriptor="descriptor", sensitivity=None)
    return dict(T=None, legs=None, descriptor=None, sensitivity=None)


def _pass_entry(gd: GateData, name: str, n: int) -> dict:
    p = gd.passes[name]
    if p.state == "absent":
        return {"state": PNR}
    if p.state == "incomplete":
        return {"state": PNR_INCOMPLETE}
    rec = p.rows.get(n)
    if rec is None:
        return {"state": PNR_ROW}
    return {"state": "read", "outcome": rec.get("outcome"), "status_written": rec.get("status_written"),
            "route": rec.get("route"), "file": f"{gd.rel}/{name}/row_{n:04d}.json", "sha256": p.row_sha[n]}


def _not_there(entry: dict, rec) -> str | None:
    """the text a field reads when its pass has no computed record for the row (never a guess)."""
    if entry["state"] != "read":
        return entry["state"]
    if rec.get("outcome") != "computed":
        return outcome_text(rec)
    return None


def outcome_text(rec: dict) -> str:
    """'<outcome>: <status written>', without repeating an outcome the status already begins with."""
    oc, st = str(rec.get("outcome")), str(rec.get("status_written"))
    return st if st.startswith(oc) else f"{oc}: {st}"


def r27_fields(res: dict) -> dict:
    r27 = res.get("r27") if isinstance(res, dict) else None
    if not isinstance(r27, dict) or not r27:
        return {}
    out = {}
    for mi, b in r27.items():
        if not isinstance(b, dict):
            continue
        desc = b.get("descriptors") or {}
        out[mi] = {"reading_as_recorded": b.get("reading"), "reading_r27": b.get("reading_r27"),
                   "labels": b.get("labels"), "power_columns": b.get("power_columns"),
                   "planted_class": b.get("planted_class"), "reading_class": b.get("reading_class"),
                   "reparcellated": b.get("reparcellated"), "status": b.get("status"),
                   "m": desc.get("m"), "f": desc.get("f"), "f_over_m": desc.get("f_over_m"), "c_S": desc.get("c_S"),
                   "R2_grad": desc.get("R2_grad"), "R2_absx": desc.get("R2_absx"),
                   "p_hypergeom": desc.get("p_hypergeom"), "brain_enriched": desc.get("brain_enriched"),
                   "f_U": desc.get("f_U")}
    return out


def published_null_reading(survives: bool, primary: str) -> str:
    """claims_register.md:216-220 (U-RC5)."""
    if primary != "ok":
        return str(primary)
    return ("detectable by the verdict (the published analysis reported none)" if survives
            else "not detectable at this power (as published)")


def compose_reading(row, core: dict, is_desc: bool, verdict: dict, r27: dict) -> str:
    """The cell's reading, from the records only (U-RC4..6); never a forbidden word (checked)."""
    if is_desc:
        return str(verdict.get("reading"))
    if str(core.get("kind", "")).startswith("component"):
        return str(core.get("reading"))
    primary = str(verdict.get("primary_status"))
    survives = bool(verdict.get("survives"))
    if row["cell_class"] == "published-null":
        return published_null_reading(survives, primary)
    readings = [b.get("reading_as_recorded") for b in r27.values()]
    if verdict.get("two_cohort"):
        if survives:
            if readings and all(r == "survives — calibrated evidence" for r in readings):
                return "survives — calibrated evidence"
            whys = []
            for r in readings:
                m = re.search(r"calibration extrapolated \((.+)\)", r or "")
                if m:
                    whys += m.group(1).split(" / ")
            return "survives — calibration extrapolated (%s)" % " / ".join(dict.fromkeys(whys) or ["map"])
        return "not detectable at this power" if primary == "ok" else primary
    if len(readings) == 1 and readings[0]:
        return readings[0]
    if primary != "ok":
        return primary
    return "survives" if survives else "not detectable at this power"


def descriptor_view(res: dict) -> dict:
    """The descriptor legs of a descriptor-pass record (full forms: per map; Liu; signed-weight), generic."""
    out = {}
    if "per_map" in res and "direction_from_verdict" in res:
        out["direction_from_verdict"] = res["direction_from_verdict"]
        for mi, rec in (res.get("per_map") or {}).items():
            m = {"T": rec.get("T"), "legs": legs_view(rec.get("legs")),
                 "level2": leg_view(rec["level2"]) if isinstance(rec.get("level2"), dict) else None,
                 "J1": leg_view(rec["J1"]) if isinstance(rec.get("J1"), dict) else None,
                 "naive_joint": leg_view(rec["naive_joint"]) if isinstance(rec.get("naive_joint"), dict) else None,
                 "direction": rec.get("direction"), "two_sided": rec.get("two_sided"),
                 "direction_reading": rec.get("direction_reading"), "counts": rec.get("counts")}
            if isinstance(rec.get("T_abs"), dict):
                ta = rec["T_abs"]
                m["T_abs"] = {"T": ta.get("T"), "tail": ta.get("tail"), "label": ta.get("label"),
                              "legs": legs_view(ta.get("legs"))}
            out[str(mi)] = m
        return out
    if res.get("form", "").startswith("gene-set-only"):
        return {"T": res.get("T"), "legs": legs_view(res.get("legs")),
                "level2": leg_view(res["level2"]) if isinstance(res.get("level2"), dict) else None,
                "direction_reading": res.get("direction_reading"), "reading": res.get("reading"),
                "G5_label": res.get("G5_label"), "set": res.get("set"), "U_stat_counts": dget(res, "U_stat")}
    if "gene_legs" in res:
        gl = res.get("gene_legs") or {}
        return {"T_S": res.get("T_S"), "registered_T": res.get("registered_T"),
                "legs": legs_view(gl.get("legs")) if isinstance(gl, dict) else {},
                "level2": leg_view(gl["level2"]) if isinstance(gl.get("level2"), dict) else None,
                "J1": leg_view(gl["J1"]) if isinstance(gl.get("J1"), dict) else None,
                "status": gl.get("status") if isinstance(gl, dict) else None,
                "reproduction": res.get("reproduction"), "registered_outcome": res.get("registered_outcome")}
    return {"record_keys": sorted(res.keys())}


def check_r1_descriptor(where: str, dv: dict) -> None:
    dfv = dv.get("direction_from_verdict")
    if dfv is None:
        return
    two = bool(dfv.get("two_sided"))
    for mi, m in dv.items():
        if mi == "direction_from_verdict":
            continue
        d = m.get("direction")
        for k, lv in list(m.get("legs", {}).items()) + [("level2", m.get("level2")), ("J1", m.get("J1")),
                                                          ("naive_joint", m.get("naive_joint"))]:
            if isinstance(lv, dict):
                check_r1_leg(f"{where} descriptor map {mi} {k}", lv, d, two)


def build_cell(reg: Register, gd: GateData, row) -> dict:
    n = row.row
    open_gates = gd.open_gates()
    entries = {name: _pass_entry(gd, name, n) for name in PASSES}
    vrec = gd.passes["verdict"].rows.get(n) if gd.passes["verdict"].complete() else None
    plan = _route_plan(row, open_gates)
    route = (vrec or {}).get("route") or plan["route"]
    route_check = ("equal to run.classify at the report commit" if vrec is None or vrec.get("route") == plan["route"]
                   else f"differs from run.classify at the report commit ({plan['route']}); the record's route is used")
    cp = computing_passes(route)
    cell = {
        "what": "A1 cell (RUN_PLAN v3.1 §16): assembled from the run records; no statistic computed here",
        "row": n, "cell_id": row.cell_id, "target_no": row.target_no, "target_key": row.target_key,
        "frozen11_row": row["frozen11_row"], "cell_class": row["cell_class"], "claim_form": row.claim_form,
        "gate_column": row.gate, "results_gate": gd.gate,
        "status_tsv": row.status,
        "status_effective": LD.effective_status(row, open_gates),
        "view": "launch view: open gates " + (", ".join(sorted(open_gates)) or "none"),
        "headline_population_tsv": row["headline_population"],
        "in_m": row.m_membership,
        "focal": row["focal"],
        "inference_level": row["inference_level"],
        "reproduction_tsv": row["reproduction"],
        "secondary_view": {"status_tsv": row["secondary_view_near_miss_status"],
                           "set_id_tsv": row["secondary_view_near_miss_set_id"],
                           "counted_in_m_prime": M_PRIME_YES in row["secondary_view_near_miss_status"],
                           "computed": "no secondary-view record (the runner writes none for the near-miss view)",
                           "rule": "m' (223) is reported beside m (207), never in it (claims_register.md:1831-1838)"},
        "flags": {"tsv": sorted(row_flags(row) | ({"provisional (S conditional, R2)"} if R2_FLAG in row.status
                                                  else set())),
                  "cell_class": row["cell_class"]},
        "route": route, "route_source": "verdict record" if vrec is not None else "run.classify (no verdict record)",
        "route_check": route_check,
        "passes": entries,
        "tsv": row.fields,
    }
    # ---- the verdict pass: T, d*, legs, conjunction, statuses, R27 ------------------------------------------------
    fields_pnr = {}
    tpass = cp["T"]
    v_missing = _not_there(entries["verdict"], vrec) if vrec is not None else entries["verdict"]["state"]
    r27 = {}
    if cp["legs"] == "verdict" and v_missing is None:
        res = vrec.get("result") or {}
        verdict = res.get("verdict") if isinstance(res.get("verdict"), dict) else None
        if verdict is None and route == "descriptor: signed-weight rho (P15)":
            verdict = None
            cell["T"] = res.get("T")
            cell["direction"] = {"two_sided": res.get("two_sided"), "registered_direction": res.get("registered_direction"),
                                 "d_star": None, "direction_reading": res.get("direction_reading")}
            cell["legs"] = legs_view(dget(res, "site", "legs"))
            cell["legs"]["site (max)"] = leg_view(dget(res, "site", "max") or {})
            for k, lv in cell["legs"].items():
                check_r1_leg(f"row {n} signed-weight leg {k}", lv, None if res.get("two_sided") else
                             res.get("registered_direction"), bool(res.get("two_sided")))
            cell["conjunction"] = "no conjunction (signed-weight descriptor: no verdict; U-F4)"
            cell["verdict"] = {"survives": res.get("survives"), "survival_rule": res.get("survival_rule"),
                               "reading": "descriptive (not a verdict)"}
            cell["reading"] = "descriptive (not a verdict)"
        elif verdict is None:
            refuse(f"row {n}: a computed verdict record without a verdict")
        else:
            check_r1_verdict(f"row {n}", verdict)
            core, is_desc = verdict_core(verdict)
            r27 = r27_fields(res)
            if core.get("two_cohort"):
                cell["T"] = {lab: mv.get("T") for lab, mv in (core.get("per_map") or {}).items()}
                cell["legs"] = {lab: legs_view(mv.get("legs")) for lab, mv in (core.get("per_map") or {}).items()}
            else:
                cell["T"] = core.get("T")
                cell["legs"] = legs_view(core.get("legs"))
            cell["direction"] = {k: core.get(k) for k in ("two_sided", "registered_direction", "d_star", "d_star_rule",
                                                           "d_star_reason")}
            cell["labels_R1"] = {"p_reported": "min(1, 2 p(d*)) for two-sided claims, p(d) one-sided (R1; the "
                                               "verdict p)",
                                 "p_per_leg_two_sided": "per-leg two-sided (not the verdict p): min(1, 2 min(p(+), "
                                                        "p(-))) (R1 :440-441)"}
            cell["conjunction"] = {"p": core.get("p_conjunction"), "p_component": core.get("p_component"),
                                   "one_sided": dict(zip(("+", "-"), pdir(core.get("conjunction_one_sided")))),
                                   "rule": core.get("p_rule") or ("min(1, 2 min_d max_leg p(d)) (R1)" if
                                                                  core.get("two_sided") else "max_leg p(d) (one-sided)"),
                                   "descriptive": bool(is_desc)}
            vk = ("kind", "form", "two_cohort", "survives", "passes_at_alpha", "passes_component_level",
                  "primary_status", "primary_status_rule", "engine_status", "status", "flags", "resolution",
                  "floors_effective", "uninformative", "g6l", "pools", "not_computable_legs", "reading", "label",
                  "never_survives", "g6s_exact", "n_G6s", "species_conditioned", "n_parcels", "K", "alpha")
            cell["verdict"] = {k: core.get(k) for k in vk if k in core}
            if core.get("two_cohort"):
                cell["verdict"]["kind"] = "full (two-cohort)"
            cell["verdict"].update(descriptor_row=bool(is_desc), survives=bool(verdict.get("survives")),
                                   primary_status=verdict.get("primary_status"),
                                   primary_status_rule=verdict.get("primary_status_rule"))
            if is_desc:
                cell["verdict"]["reading"] = verdict.get("reading")
                cell["verdict"]["label"] = verdict.get("label")
            if core.get("two_cohort"):
                cell["verdict"]["per_map"] = {lab: {k: mv.get(k) for k in ("primary_status", "survives",
                                                                            "p_conjunction", "flags", "resolution")}
                                              for lab, mv in (core.get("per_map") or {}).items()}
            cell["floors_and_statuses"] = {
                "per_leg": {k: {kk: lv[kk] for kk in ("status", "floor_one_sided", "floor_effective", "floor") if kk in lv}
                            for k, lv in (cell["legs"].items() if not core.get("two_cohort") else
                                          ((f"{lab}:{kk}", vv) for lab, lm in cell["legs"].items()
                                           for kk, vv in lm.items()))},
                "resolution": core.get("resolution"), "floors_effective": core.get("floors_effective"),
                "flags": core.get("flags"), "primary_status": verdict.get("primary_status"),
                "engine_status": core.get("engine_status"), "not_computable_legs": core.get("not_computable_legs")}
            cell["reading"] = compose_reading(row, core, is_desc, verdict, r27)
            if str(core.get("kind", "")).startswith("component"):
                cell["reading_rule"] = ("component reading of the verdict record (prereg_amend_5.md:156; U-RC6); "
                                        "the r27 block's 'reading' is kept beside it as recorded")
            cell["identity_counts"] = res.get("identity_counts")
            cell["g6l_screen"] = res.get("g6l_screen")
            cell["spearman_beside_level0"] = res.get("spearman_beside_level0")
    elif cp["legs"] == "verdict":
        for f in ("T", "direction", "legs", "conjunction", "verdict", "floors_and_statuses", "reading"):
            fields_pnr[f] = v_missing
    elif cp["T"] is None:   # no statistic / refused rows: the record (or the plan) gives the status
        st = (vrec or {}).get("status_written") if vrec is not None else None
        oc = (vrec or {}).get("outcome")
        txt = (entries["verdict"]["state"] if vrec is None else
               str(st) if str(st).startswith(str(oc)) else f"{oc}: {st}")
        for f in ("T", "direction", "legs", "conjunction", "verdict", "floors_and_statuses"):
            cell[f] = txt
        cell["reading"] = st if vrec is not None else entries["verdict"]["state"]
    # ---- R27 (verdict pass) ---------------------------------------------------------------------------------------
    if r27:
        cell["r27"] = r27
        first = next(iter(r27.values()))
        for k in ("m", "f_over_m", "c_S", "R2_grad", "R2_absx"):
            vals = {mi: b.get(k) for mi, b in r27.items()}
            cell[k] = first.get(k) if len(vals) == 1 else vals
        cell["r27_rule"] = "R27 / §16 :1667: amendment 5 labels and power columns as the verdict pass recorded them"
    else:
        why = (v_missing if (cp["legs"] == "verdict" and v_missing is not None) else
               "not applicable: no statistic for this row" if cp["T"] is None else
               "absent from the runner's record (the form route writes no R27 block: run.py _run_form_row)"
               if route.startswith("descriptor:") else
               "absent from the verdict record")
        if vrec is None and entries["verdict"]["state"] != "read":
            why = entries["verdict"]["state"]
        cell["r27"] = why
        for k in ("m", "f_over_m", "c_S", "R2_grad", "R2_absx"):
            cell[k] = why
    # ---- the descriptor pass --------------------------------------------------------------------------------------
    dpass = gd.passes["descriptor"]
    drec = dpass.rows.get(n) if dpass.complete() else None
    if cp["descriptor"] is None:
        cell["descriptor_legs"] = ("no descriptor legs (component form; RUN_PLAN §4 legs table)"
                                   if route.startswith("verdict: component") else
                                   "not applicable: no statistic for this row")
        if drec is not None and drec.get("outcome") != "computed":
            cell["descriptor_legs"] = outcome_text(drec)
    else:
        miss = _not_there(entries["descriptor"], drec) if drec is not None else entries["descriptor"]["state"]
        if miss is not None:
            cell["descriptor_legs"] = miss
            if tpass == "descriptor":
                for f in ("T", "direction", "legs", "conjunction", "verdict", "floors_and_statuses", "reading"):
                    fields_pnr.setdefault(f, miss)
        else:
            dres = drec.get("result") or {}
            dv = descriptor_view(dres)
            check_r1_descriptor(f"row {n}", dv)
            if route == "descriptor: gene-set-only (R10)":
                for k, lv in (dv.get("legs") or {}).items():
                    check_r1_leg(f"row {n} Liu leg {k}", lv, None if dres.get("two_sided") else
                                 dres.get("registered_direction"), bool(dres.get("two_sided")))
                cell["T"] = dres.get("T")
                cell["direction"] = {"two_sided": dres.get("two_sided"),
                                     "registered_direction": dres.get("registered_direction"), "d_star": None,
                                     "direction_reading": dres.get("direction_reading")}
                cell["legs"] = "no verdict legs (gene-set-only, R10: the G1-G5 legs are descriptors, below)"
                cell["conjunction"] = "no conjunction (no calibrated test: no verdict; R10)"
                cell["verdict"] = {"survives": dres.get("survives"), "survival_rule": dres.get("survival_rule"),
                                   "reading": dres.get("reading")}
                cell["floors_and_statuses"] = {"per_leg": {k: {kk: lv.get(kk) for kk in ("status", "floor")}
                                                           for k, lv in (dv.get("legs") or {}).items()}}
                cell["reading"] = dres.get("reading")
            cell["descriptor_legs"] = dv
            cell["descriptor_file"] = {"file": entries["descriptor"]["file"], "sha256": entries["descriptor"]["sha256"]}
    # ---- the sensitivity pass (R11) -------------------------------------------------------------------------------
    spass = gd.passes["sensitivity"]
    srec = spass.rows.get(n) if spass.complete() else None
    if cp["sensitivity"] is None:
        cell["sensitivity_ge2_donors"] = ("not applicable: no verdict for this row (R11 runs the verdict legs of "
                                          "claims with a verdict)")
        if srec is not None and srec.get("outcome") != "computed":
            cell["sensitivity_ge2_donors"] = outcome_text(srec)
    else:
        miss = _not_there(entries["sensitivity"], srec) if srec is not None else entries["sensitivity"]["state"]
        if miss is not None:
            cell["sensitivity_ge2_donors"] = miss
        else:
            sres = srec.get("result") or {}
            if sres.get("parcel_set") == "unchanged":
                cell["sensitivity_ge2_donors"] = {"parcel_set": "unchanged", "reading": srec.get("status_written"),
                                                  "primary_result_sha256": sres.get("primary_result_sha256")}
            else:
                sv = sres.get("verdict") or {}
                check_r1_verdict(f"row {n} (sensitivity)", sv)
                score, sdesc = verdict_core(sv)
                cell["sensitivity_ge2_donors"] = {
                    "parcel_set": sres.get("parcel_set"), "T": score.get("T"), "d_star": score.get("d_star"),
                    "legs": legs_view(score.get("legs")) if not score.get("two_cohort") else
                    {lab: legs_view(mv.get("legs")) for lab, mv in (score.get("per_map") or {}).items()},
                    "p_conjunction": score.get("p_conjunction"), "survives": bool(sv.get("survives")),
                    "primary_status": sv.get("primary_status"), "flags": score.get("flags"),
                    "descriptor_row": bool(sdesc), "rule": "R11: reported beside the primary; it never changes it",
                    "parcel_ids": dget(srec, "inputs", "parcel_ids")}
            cell["sensitivity_file"] = {"file": entries["sensitivity"]["file"],
                                        "sha256": entries["sensitivity"]["sha256"]}
    for f, txt in fields_pnr.items():
        cell[f] = txt
    # ---- reproduction / RLM records -------------------------------------------------------------------------------
    repro = []
    for name in PASSES:
        p = gd.passes[name]
        if p.complete():
            for store, kind in ((p.repro, "reproduction"), (p.rlm, "rlm")):
                if n in store:
                    rec, sha = store[n]
                    repro.append({"kind": kind, "pass": name, "file": f"{gd.rel}/{name}/row_{n:04d}_"
                                  f"{'repro' if kind == 'reproduction' else 'rlm'}.json", "sha256": sha,
                                  "record": rec.get("reproduction") if kind == "reproduction" else rec.get("rlm")})
    not_run = [name for name in PASSES if not gd.passes[name].complete()]
    if repro:
        cell["reproduction"] = repro
    else:
        cell["reproduction"] = ("no reproduction record in the passes read; " +
                                (f"pass(es) not run: {', '.join(not_run)}" if not_run else
                                 "the runner wrote none for this row"))
    checks = []
    for e in repro:
        checks += [(e["file"] + p, c) for p, c in find_checks(e["record"])]
    if vrec is not None:
        checks += [(f"verdict row record{p}", c) for p, c in find_checks(vrec.get("result"))]
    if drec is not None:
        checks += [(f"descriptor row record{p}", c) for p, c in find_checks(drec.get("result"))]
    cell["reproduction_checks"] = [{"where": w, "label": c.get("label"), "published": c.get("published"),
                                    "ours": c.get("ours"), "functional": c.get("functional")} for w, c in checks]
    cell["reproduction_flag"] = reproduction_flag(row, checks)
    cell["comparator_statuses"] = sorted(comparator_statuses([e["record"] for e in repro]))
    # ---- seeds, inputs, commit -----------------------------------------------------------------------------------
    seeds, inputs = {}, {}
    for name in PASSES:
        p = gd.passes[name]
        rec = p.rows.get(n) if p.complete() else None
        if rec is None:
            seeds[name] = inputs[name] = entries[name]["state"] if entries[name]["state"] != "read" else PNR_ROW
            continue
        seeds[name] = dget(rec, "row_provenance", "seeds")
        inputs[name] = {"input_hashes": dget(rec, "row_provenance", "input_hashes"),
                        "analysis_class": dget(rec, "inputs", "analysis_class"),
                        "parcels": {mi: {k: v.get(k) for k in ("n_given", "n_kept", "n_dropped", "rule")}
                                    for mi, v in (dget(rec, "inputs", "analysis_parcels") or {}).items()}
                        if isinstance(dget(rec, "inputs", "analysis_parcels"), dict) else None,
                        "set": dget(rec, "inputs", "set"),
                        "started": dget(rec, "row_provenance", "started"),
                        "finished": dget(rec, "row_provenance", "finished")}
    cell["seeds"], cell["inputs"] = seeds, inputs
    # B2: every flag - the run-time flags of every pass's record, and the effective status they imply (U-RC8)
    rf = record_run_flags(row, gd)
    cell["flags"]["run"] = sorted(rf["engine"] | rf["extra"] | ({"not testable (< 5) at use"} if rf["lt5"] else set()))
    cell["flags"]["run_detail"] = rf["details"]
    cell["flags"]["pending"] = rf["pending"]
    cell["status_effective_tsv"] = cell["status_effective"]
    cell["status_effective"], cell["status_effective_source"] = at_use_status(row, cell["status_effective"], rf)
    if isinstance(cell.get("verdict"), dict) and str(cell["verdict"].get("kind", "")).startswith("component") \
            and isinstance(cell.get("r27"), dict) \
            and any(isinstance(b, dict) and b.get("reading_r27") is None for b in cell["r27"].values()):
        # residue C3: only blocks written before the pre-WP4 fix (run.component_r27 always sets reading_r27)
        cell["r27_note"] = COMPONENT_R27_NOTE
    ri = gd.raw_identity or {}
    cell["commit"] = ri.get("run_commit") if ri else PNR
    cell["code_hash"] = ri.get("code_hash") if ri else PNR
    if cell.get("reading") is not None:
        check_wording(str(cell["reading"]), f"row {n} reading")
    return cell


def reproduction_flag(row, checks: list) -> dict:
    """U-RC8: the §1.5 flag. TSV 'not reproduced ...' (documented pre-freeze) flags; an R37 check flags only where the
    TSV reproduction is a 4.1 check; checks that disagree refuse (no frozen reading picks one)."""
    tsv = row["reproduction"]
    if tsv.startswith(TSV_NOT_REPRODUCED):
        return {"flag": "not reproduced", "source": "tsv: reproduction column (pre-freeze, documented)"}
    labels = sorted({c.get("label") for _, c in checks})
    if not tsv.startswith(CHECK_PREFIX):
        return {"flag": None, "source": "tsv: reproduction descriptive (never flagged)",
                "check_labels": labels or None}
    if not labels:
        return {"flag": None, "source": "4.1 check not in the records read (not flagged)"}
    if len(labels) > 1:
        refuse(f"row {row.row}: R37 checks disagree ({labels}); no frozen reading picks one")
    lab = labels[0]
    return {"flag": "not reproduced" if lab.startswith("not reproduced") else None, "label": lab,
            "source": "record: R37 check (RUN_PLAN_amend_2 R37 (B))"}


# ================================================================================================================
# BH (R29)
# ================================================================================================================
def bh_q(ps: list) -> list:
    """Benjamini-Hochberg step-up q-values (descriptive; prereg_amend_3.md:77)."""
    n = len(ps)
    if n == 0:
        return []
    order = sorted(range(n), key=lambda i: ps[i])
    q = [0.0] * n
    prev = 1.0
    for rank in range(n, 0, -1):
        i = order[rank - 1]
        prev = min(prev, ps[i] * n / rank)
        q[i] = min(1.0, prev)
    return q


def bh_entry(row, cell: dict) -> dict:
    """R29 :1033-1040: membership and the p entered."""
    if row.m_membership != "yes":
        return {"family": "outside: not in m"}
    if (cell.get("reproduction_flag") or {}).get("flag") == "not reproduced":
        return {"family": "outside: flagged not reproduced (R29)"}
    v = cell.get("verdict")
    if not isinstance(v, dict):
        return {"family": f"outside: no conjunction p ({short(v, 90)})"}
    if v.get("descriptor_row"):
        refuse(f"row {row.row}: a descriptor row in m (no frozen reading for its BH entry)")
    if "kind" not in v:
        refuse(f"row {row.row}: a form row in m (no frozen reading for its BH entry)")
    primary = str(v.get("primary_status"))
    if primary.startswith("not auditable"):
        return {"family": f"outside: {primary}"}
    if primary in ENGINE_NOT_OK or primary.startswith(("g6l ", "unmatched", "degenerate")):
        return {"family": "in", "p_entered": 1.0, "rule": f"status {primary}: enters with p = 1 (R29)"}
    comp = str(v.get("kind", "")).startswith("component")
    p = cell["conjunction"].get("p_component") if comp else cell["conjunction"].get("p")
    if primary != "ok":
        refuse(f"row {row.row}: primary status {primary!r} has no R29 reading")
    if p is None:
        return {"family": "outside: no conjunction p (d* undefined)"}
    return {"family": "in", "p_entered": float(p),
            "rule": "component-level p = max(Level 0, site) (R29)" if comp else "conjunction p (R1)"}


def apply_bh(cells: list, label: str, key: str) -> dict:
    fam = [c for c in cells if isinstance(c.get("bh"), dict) and c["bh"].get("family") == "in"]
    q = bh_q([c["bh"]["p_entered"] for c in fam])
    for c, qq in zip(fam, q):
        c["bh"][key] = qq
        c["bh"][key + "_label"] = label
    return {"family_size": len(fam), "rows": [c["row"] for c in fam],
            "outside": {c["row"]: c["bh"]["family"] for c in cells
                        if isinstance(c.get("bh"), dict) and c["bh"].get("family", "").startswith("outside")
                        and c["bh"]["family"] != "outside: not in m"}}


# ================================================================================================================
# the headline (§16 :1673-1690)
# ================================================================================================================
def status_rule(st: str) -> str:
    return STATUS_RULES.get(st, "as the record states")


def short_reason(st: str) -> str:
    """'SD7 labels unmatched' from 'not auditable (definition not applicable: SD7 labels unmatched)'."""
    m = re.fullmatch(r"not auditable \((.*)\)", st or "")
    return m.group(1).replace("definition not applicable: ", "") if m else short(st, 60)


def short_rule(rule: str) -> str:
    return re.sub(r"\ARUN_PLAN(_amend_\d)? ", "", rule)


def record_run_flags(row, gd) -> dict:
    """U-RC8 (B2 fix): the run-time flags of one row from EVERY pass's record (verdict, descriptor, sensitivity):
    extra = composition flags ('not auditable'); engine = the verdict records' own flags; basis = [(value, source)]
    for B6; lt5 = 'not testable (< 5)' at use; pending = pass outcomes not run / refused / stub; details = one entry
    per flag with its pass, field, status text, file and the frozen rule that writes it."""
    out = dict(extra=set(), engine=set(), lt5=[], pending=[], details=[], runtime=[],
               basis=[(row.status, "tsv: status"), (row["headline_population"], "tsv: headline_population")])
    if gd is None:
        return out
    if gd.verdict_complete() and row.row not in gd.passes["verdict"].rows:
        out["pending"].append(f"verdict: {PNR_ROW}")
    for name in PASSES:
        p = gd.passes[name]
        rec = p.rows.get(row.row) if p.complete() else None
        if rec is None:
            continue
        f = f"{gd.rel}/{name}/row_{row.row:04d}.json"
        st = rec.get("status_written") or ""
        out["basis"].append((st, f"record: {name} status_written"))
        v = dget(rec, "result", "verdict")
        prim = v.get("primary_status") if isinstance(v, dict) else None
        if prim is not None:
            out["basis"].append((prim, f"record: {name} primary_status"))
        if isinstance(v, dict):
            core, _ = verdict_core(v)
            out["engine"] |= set(core.get("flags") or []) | set(v.get("flags") or [])
        for txt, field in ((st, "status_written"), (prim or "", "primary_status")):
            if txt.startswith("not auditable"):
                out["extra"].add("not auditable")
                out["details"].append({"flag": "not auditable", "pass": name, "field": field, "status": txt,
                                       "file": f, "rule": status_rule(txt)})
        if st in G2_RUNTIME_RULES:
            out["runtime"].append({"pass": name, "field": "status_written", "status": st, "file": f,
                                   "rule": G2_RUNTIME_RULES[st]})
        if rec.get("outcome") == "no statistic" and st.startswith("not testable (< 5)") and \
                not row.status.startswith("not testable (< 5)"):
            out["lt5"].append(f"{name}: {st}")
            out["details"].append({"flag": "not testable (< 5)", "pass": name, "field": "status_written",
                                   "status": st, "file": f, "rule": LT5_AT_USE_RULE})
        if rec.get("outcome") in PENDING_OUTCOMES:
            out["pending"].append(f"{name}: {rec.get('outcome')}: {st}")
    return out


def run_flags(cells_by_row: dict, gates: dict, row) -> tuple[set, list, list, list]:
    """(extra flags, basis, lt5-at-use notes, pending notes) of record_run_flags, for the composition."""
    g = gates.get(REG_GATE[0].gate_of_row(row)) if REG_GATE else None
    r = record_run_flags(row, g)
    return r["extra"], r["basis"], r["lt5"], r["pending"]


def _rank(flags) -> int:
    ranks = [PRECEDENCE.index(f) for f in flags if f in PRECEDENCE]
    return min(ranks) if ranks else len(PRECEDENCE)


def moving_details(row, details: list) -> list:
    """The run-time flags that outrank every flag the row's TSV status carries (\u00a71.8 precedence): the ones that
    move its category (or take it out of the population, < 5 at use)."""
    tsv_rank = _rank(row_flags(row))
    return [d for d in details if PRECEDENCE.index(d["flag"]) < tsv_rank]


def at_use_status(row, tsv_effective: str, rf: dict) -> tuple[str, str]:
    """(effective status at use, its source): a record status whose flag outranks the TSV status's flags replaces it
    (the same precedence the composition uses); otherwise the TSV status under the launch view."""
    mv = sorted(moving_details(row, rf["details"]), key=lambda d: (PRECEDENCE.index(d["flag"]), PASSES.index(d["pass"])))
    if mv:
        d = mv[0]
        return d["status"], f"{d['pass']} record at use ({d['file']}; {d['field']}; {d['rule']})"
    if rf.get("runtime"):   # a WP4 / G2 run-time status outranks the register status (G2_RUNTIME_RULES)
        d = rf["runtime"][0]
        return d["status"], f"{d['pass']} record at use ({d['file']}; {d['field']}; {d['rule']})"
    return tsv_effective, "TSV status under the launch view (no run-time flag outranks it)"


REG_GATE: list = []   # the Register in use (set by compose); run_flags maps a row to its results gate through it


def compose(reg: Register, gates: dict, cells_by_row: dict) -> dict:
    """The population in view and its composition (§1.2, §1.8; U-RC7, U-RC8), the survivals and their readings."""
    REG_GATE[:] = [reg]
    run_gates = {g for g, gd in gates.items() if gd.verdict_complete()}
    tsv_gates = {g for g in run_gates if g in ("G1", "G2")}
    view, apart = population_rows(reg, tsv_gates)
    units = []
    for r in view:
        extra, basis, lt5, pending = run_flags(cells_by_row, gates, r)
        repro_st = comparator_statuses([e["record"] for e in (cells_by_row.get(r.row) or {}).get("reproduction", [])
                                        if isinstance(e, dict)]) if isinstance(
            (cells_by_row.get(r.row) or {}).get("reproduction"), list) else set()
        assert_b6(r.row, basis, repro_st)
        cat = pop_category(r, "upper", extra)
        lower = pop_category(r, "lower", extra)
        cat_reg = pop_category(r, "upper")
        g_ = gates.get(reg.gate_of_row(r))
        movers = moving_details(r, record_run_flags(r, g_)["details"]) if g_ is not None else []
        cell = cells_by_row.get(r.row) or {}
        rflag = (cell.get("reproduction_flag") or {}).get("flag")
        out_reason = None
        if lt5:
            out_reason = "not testable (< 5) at use"
        elif cat.startswith(TESTED) and rflag == "not reproduced":
            out_reason = "full-verdict claim flagged not reproduced (§1.5 check)"
        gate_ran = reg.gate_of_row(r) in run_gates
        v = cell.get("verdict") if isinstance(cell.get("verdict"), dict) else None
        received = bool(gate_ran and v is not None and not v.get("descriptor_row")
                        and cat.startswith(TESTED) and str(v.get("kind", "")).startswith("full"))
        survives = bool(received and v.get("survives"))
        comp_pass = bool(cat == "component-level" and v is not None and v.get("passes_component_level"))
        moved = None
        if out_reason is not None or cat != cat_reg:
            moved = dict(to=f"out of the population ({out_reason})" if out_reason else cat,
                         reasons=movers if movers else [{"status": out_reason, "rule": "§1.2 / §1.5",
                                                         "pass": "verdict", "file": None}])
        u = dict(row=r.row, cell_id=r.cell_id, target_key=r.target_key, gate=r.gate, category=cat,
                 category_register=cat_reg, register_category_rule="pop_category on the TSV status alone (§1.8)",
                 moved=moved,
                 category_lower_view=lower, provisional=R2_FLAG in r.status, run_flags=sorted(extra),
                 out_of_population=out_reason, pending=pending, lt5_at_use=lt5, received_verdict=received,
                 survives=survives, passes_component_level=comp_pass,
                 component_form=r.claim_form == "component", not_auditable_flag="not auditable" in row_flags(r, extra),
                 reading=cell.get("reading") if survives else None,
                 r27_labels=sorted({lab for b in (cell.get("r27") or {}).values() if isinstance(b, dict)
                                    for lab in (b.get("labels") or [])}) if survives and isinstance(cell.get("r27"), dict)
                 else [],
                 composition_basis=[f"{src}: {short(val, 80)}" for val, src in basis])
        units.append(u)
    inpop = [u for u in units if u["out_of_population"] is None]
    cats_reg = {}
    for u in units:   # the register's composition counts every unit of the view (the TSV alone)
        cats_reg[u["category_register"]] = cats_reg.get(u["category_register"], 0) + 1
    moved_units = [dict(row=u["row"], cell_id=u["cell_id"], category_register=u["category_register"],
                        category_at_use=u["moved"]["to"], reasons=u["moved"]["reasons"]) for u in units if u["moved"]]
    if len(run_gates) == 1 and run_gates == {"ungated"}:
        reg_label = "register R4 interim"
    elif run_gates == set(GATES):
        reg_label = "register R4 full"
    else:
        reg_label = "register (TSV-derived) for the gates run"
    cats = {}
    for u in inpop:
        cats[u["category"]] = cats.get(u["category"], 0) + 1
    lower = {}
    for u in inpop:
        lower[u["category_lower_view"]] = lower.get(u["category_lower_view"], 0) + 1
    tested = [u for u in inpop if u["category"].startswith(TESTED)]
    surv = [u for u in inpop if u["survives"]]
    calibrated = [u for u in surv if u["reading"] == "survives — calibrated evidence"]
    extrap = {}
    for u in surv:
        m = re.search(r"calibration extrapolated \((.+)\)", u["reading"] or "")
        if m:
            extrap[m.group(1)] = extrap.get(m.group(1), 0) + 1
    per_label, power_labels = {}, {}
    for u in surv:   # amendment 5 §4's scope labels; §3's power labels counted apart (prereg_amend_5.md:172)
        for lab in u["r27_labels"]:
            tgt = power_labels if lab.startswith("power not measured") else per_label
            tgt[lab] = tgt.get(lab, 0) + 1
    received = [u for u in tested if u["received_verdict"]]
    crosstab = {f: {na: sum(1 for u in inpop if u["component_form"] == (f == "component-level in form")
                            and u["not_auditable_flag"] == (na == "not auditable"))
                    for na in ("not auditable", "auditable")} for f in ("component-level in form", "other form")}
    a6 = []
    for cid in A6_CELLS:
        for rn in reg.by_cell_id.get(cid, []):
            r = reg.rows[rn]
            g = reg.gate_of_row(r)
            c = cells_by_row.get(rn)
            if g not in run_gates or c is None:
                a6.append(dict(cell_id=cid, row=rn, outcome=f"pending (gate {r.gate} not run)", decision=A6_DECISION))
            else:
                v = c.get("verdict")
                a6.append(dict(cell_id=cid, row=rn, outcome=(v.get("primary_status") if isinstance(v, dict) else v),
                               decision=A6_DECISION))
    listed_apart = {
        "gates not run": {g: dict(units=len(rows), rows=[r.row for r in rows]) for g, rows in apart.items()},
        "dear (deferred pending provenance)": [r.row for r in reg.rows.values() if r.gate == "G1+G2"],
        "vairam / roy (deferred)": [r.row for r in reg.rows.values() if r.target_key.startswith("vairam")],
    }
    lt5_rows = [dict(row=u["row"], cell_id=u["cell_id"], at_use=u["lt5_at_use"]) for u in units if u["lt5_at_use"]]
    gated_lt5 = []
    for g in ("G2", "G1"):
        if g in run_gates:
            for c in cells_by_row.values():
                if c.get("results_gate") == g and any("not testable (< 5)" in str((e or {}).get("status_written", ""))
                                                      for e in c.get("passes", {}).values()):
                    gated_lt5.append(c["row"])
    passes_read = {g: [n for n in PASSES if gd.passes[n].complete()] for g, gd in gates.items()
                   if g in run_gates}
    return dict(gates_run=sorted(run_gates, key=GATES.index), passes_read=passes_read, units=units,
                population_units=len(inpop),
                out_of_population=[dict(row=u["row"], cell_id=u["cell_id"], reason=u["out_of_population"])
                                   for u in units if u["out_of_population"]],
                composition=dict(sorted(cats.items())), composition_lower_view=dict(sorted(lower.items())),
                composition_register=dict(sorted(cats_reg.items())), composition_register_label=reg_label,
                composition_at_use_rule=("§1.8 precedence over the TSV flags and the run-time flags of every pass's "
                                         "record (U-RC8); the register composition is the TSV's alone"),
                moved_units=moved_units,
                provisional=[u["row"] for u in inpop if u["provisional"]],
                crosstab_component_x_not_auditable=crosstab,
                component_level=cats.get("component-level", 0),
                component_level_passing=sum(1 for u in inpop if u["passes_component_level"]),
                tested_units=len(tested), can_survive=len(tested), received_verdict=len(received),
                pending=[dict(row=u["row"], cell_id=u["cell_id"], pending=u["pending"]) for u in inpop if u["pending"]],
                survivals=len(surv), calibrated_evidence=len(calibrated), calibration_extrapolated=extrap,
                survivals_per_scope_label=per_label, survivals_per_power_label=power_labels, a6=a6,
                listed_apart=listed_apart,
                lt5_at_use=lt5_rows, gated_lt5_rows=sorted(gated_lt5))


def compress_ids(ids: list) -> str:
    """'LIU-T4 / T5' from ['LIU-T4', 'LIU-T5'] (the common prefix up to its last '-' written once)."""
    if len(ids) < 2:
        return " / ".join(ids)
    pre = ids[0].rsplit("-", 1)[0] + "-"
    if all(i.startswith(pre) for i in ids):
        return " / ".join([ids[0]] + [i[len(pre):] for i in ids[1:]])
    return " / ".join(ids)


def headline_sentences(comp: dict) -> dict:
    N, s = comp["population_units"], comp["survivals"]
    cats = comp["composition"]
    order = ["not auditable", "not testable as stated", "component-level", "no calibrated test"]
    tested_n = sum(v for k, v in cats.items() if k.startswith(TESTED))
    parts = [f"{cats.get(k, 0)} {k}" + (f" ({comp['component_level_passing']} pass at component level)"
                                        if k == "component-level" else "") for k in order]
    parts.append(f"{tested_n} {TESTED}")
    ct = comp["crosstab_component_x_not_auditable"]
    frac = (s / N) if N else None
    tested_frac = (f"{s} / {comp['received_verdict']} = {s / comp['received_verdict']:.3f}"
                   if comp["received_verdict"] else
                   f"undefined ({comp['received_verdict']} full-verdict claims received a verdict)")
    per_label = ("; ".join(f"{k}: {v}" for k, v in sorted(comp["survivals_per_scope_label"].items()))
                 if comp["survivals_per_scope_label"] else "none")
    extrap = sum(comp["calibration_extrapolated"].values())
    a6 = "; ".join(f"{a['cell_id']}: {a['outcome']}" for a in comp["a6"]) or "no such cell"
    gates = ", ".join(f"{g} [passes read: {', '.join(comp['passes_read'].get(g, []))}]"
                      for g in comp["gates_run"]) or "none"
    pend = f"; {len(comp['pending'])} pending (a run record not computed)" if comp["pending"] else ""
    others = [f"{cats[k]} {k}" for k in order if cats.get(k)]
    why = (f" (only full-verdict claims can; the other {N - tested_n} are, at use, " + ", ".join(others) + ")") \
        if others else ""
    regc = comp["composition_register"]
    cat_order = [k for k in REGISTER_CATS if regc.get(k) or cats.get(k)]
    reg_txt = " / ".join(f"{regc.get(k, 0)} {k}" for k in cat_order)
    if comp["moved_units"]:
        groups: dict = {}
        for m in comp["moved_units"]:
            r0 = m["reasons"][0]
            key = (m["category_at_use"], short_reason(r0["status"] or ""), short_rule(r0["rule"]))
            groups.setdefault(key, []).append(m["cell_id"])
        moves = "; ".join(f"{compress_ids(ids)} {to} ({why_}, {rule})" for (to, why_, rule), ids in groups.items())
        at_txt = " / ".join(str(cats.get(k, 0)) for k in cat_order)
        reg_clause = f" ({comp['composition_register_label']}: {reg_txt}; at use: {moves} -> {at_txt})"
    else:
        reg_clause = f" ({comp['composition_register_label']}: {reg_txt}; no unit moved at use)"
    s1 = (f"Interim headline (gates run: {gates}; RUN_PLAN §16, claims_register.md:256-262): {s} of the {N} "
          f"frozen-11 population units survive (survival fraction {s} / {N}"
          + (f" = {frac:.3f}" if frac is not None else "") + f") and {comp['can_survive']} of the {N} can survive"
          f"{why}, beside the curves ({CURVES}), with gates 1–11 \"{FAILED_AS_GATES}\", {comp['calibrated_evidence']} "
          f"of the {s} survivals reading \"calibrated evidence\" and {extrap} \"calibration extrapolated\" "
          f"(scope labels: {per_label}), "
          f"the composition by §1.8 precedence at use of {', '.join(parts)}{reg_clause}{pend}, the "
          f"component-level-in-form × "
          f"not-auditable cross-tab {ct['component-level in form']['not auditable']} / "
          f"{ct['component-level in form']['auditable']} (other form {ct['other form']['not auditable']} / "
          f"{ct['other form']['auditable']}; not auditable / auditable), {len(comp['provisional'])} provisional "
          f"(S conditional) rows, A6's outcome for MAMAT-E-Tissue-URG / -DRG ({a6}), and the tested-only fraction "
          f"{tested_frac}")
    low = frac is not None and s * 2 < N   # U-RC3
    s1 += (f": {LOW_FRACTION}." if low else ".")
    la = comp["listed_apart"]
    gnr = "; ".join(f"{g}'s {v['units']} population units (gate not run)" for g, v in la["gates not run"].items())
    s2 = (f"Listed apart and counted neither way: {gnr or 'no gate'}; Dear's {len(la['dear (deferred pending provenance)'])} "
          f"rows (deferred pending provenance) and Vairam / Roy's {len(la['vairam / roy (deferred)'])} rows (deferred).")
    out = {"headline": s1, "listed_apart": s2}
    if comp["out_of_population"]:
        out["population_restated"] = ("Population restated: " + "; ".join(
            f"{o['cell_id']} ({o['reason']})" for o in comp["out_of_population"]) + ".")
    for k, t in out.items():
        check_wording(t, f"headline sentence {k}")
    return out


def register_block_composition(r4: dict, prefix: str) -> dict:
    return {k[len(prefix):]: v for k, v in r4.items() if k.startswith(prefix) and k[len(prefix):] in REGISTER_CATS}


def assert_interim(reg: Register, comp: dict) -> dict:
    """\u00a716 :1681-1683 derived, never hard-coded (B1 fix). The TSV-derived composition of the units in view (TSV
    statuses alone) must equal the register's R4 block, category by category: the interim block when only the ungated
    rows have run, the full block (upper and lower views) when every gate has run. The at-use composition (run-time
    flags, U-RC8) is derived separately and stated beside it with every unit that moved; the number that can survive
    must not exceed what the block leaves."""
    r4 = reg.r4
    regc = comp["composition_register"]
    moved = [dict(cell_id=m["cell_id"], row=m["row"], register=m["category_register"], at_use=m["category_at_use"],
                  reason=m["reasons"][0]["status"], rule=m["reasons"][0]["rule"]) for m in comp["moved_units"]]
    if comp["gates_run"] == ["ungated"]:
        want = register_block_composition(r4, "population.interim.")
        if regc != want:
            refuse(f"the TSV-derived interim composition {regc} differs from the register's R4 block {want} "
                   "(claims_register.md:1870-1873)")
        if sum(regc.values()) != r4["population.interim"] or \
                comp["population_units"] + len(comp["out_of_population"]) != r4["population.interim"]:
            refuse("interim population units differ from the register's population.interim")
        tsv_tested = sum(v for k, v in want.items() if k.startswith(TESTED))
        if comp["can_survive"] > tsv_tested:
            refuse("more units can survive than the register's interim block allows")
        return dict(rule="after the ungated rows: the register's interim composition (R4 block, asserted equal to the "
                         "TSV-derived one) and the units that can survive (RUN_PLAN \u00a716 :1681-1682)",
                    register_population_interim=r4["population.interim"], register_composition=want,
                    at_use_composition=comp["composition"], moved_at_use=moved, register_can_survive=tsv_tested,
                    derived_can_survive=comp["can_survive"], derived_units=comp["population_units"])
    if set(comp["gates_run"]) == set(GATES):
        want = register_block_composition(r4, "population.full.")
        want_lower = register_block_composition(r4, "population.full.lower view.")
        lower_reg = {}
        for u in comp["units"]:
            k = pop_category(REG_GATE[0].rows[u["row"]], "lower")
            lower_reg[k] = lower_reg.get(k, 0) + 1
        if regc != want or lower_reg != want_lower:
            refuse(f"the TSV-derived full composition {regc} / lower view {lower_reg} differs from the R4 block "
                   f"{want} / {want_lower}")
        return dict(rule="every gate run: the register's full composition (R4 block) asserted equal to the TSV-derived "
                         "one; the at-use composition beside it", register_composition=want,
                    at_use_composition=comp["composition"], moved_at_use=moved, derived_units=comp["population_units"])
    if set(comp["gates_run"]) == {"ungated", "G2"}:
        bound = r4["population.interim"] + r4["gate.G2.units"]
        if comp["population_units"] > bound:
            refuse(f"after G2 the population exceeds {bound} units (RUN_PLAN \u00a716 :1683)")
        return dict(rule="after G2: <= the interim plus G2's units (\u00a716 :1683)", bound=bound,
                    register_composition_tsv=regc, at_use_composition=comp["composition"], moved_at_use=moved,
                    derived_units=comp["population_units"])
    return dict(rule="no interim bound applies to this set of gates", gates_run=comp["gates_run"],
                register_composition_tsv=regc, at_use_composition=comp["composition"], moved_at_use=moved)


# ================================================================================================================
# registered descriptors (§16 :1691-1693)
# ================================================================================================================
def stratum(level: str) -> str:
    """U-RC9."""
    if level.startswith("gene null only (uniform"):
        return "gene null only (uniform)"
    if level.startswith("gene null only (structured"):
        return "gene null only (structured)"
    return level.split(":")[0].strip()


def cell_state(c: dict | None, row, gates: dict) -> str:
    if c is None:
        g = REG_GATE[0].gate_of_row(row)
        gd = gates.get(g)
        return (f"deferred (gate {row.gate} not run)" if row.gated is not None else PNR) \
            if gd is None or not gd.verdict_complete() else PNR_ROW
    v = c.get("verdict")
    if isinstance(v, dict):
        if v.get("descriptor_row"):
            return str(v.get("reading"))
        return str(c.get("reading"))
    return str(v)


def registered_descriptors(reg: Register, gates: dict, cells_by_row: dict) -> dict:
    rows = list(reg.rows.values())
    focal = [dict(row=r.row, cell_id=r.cell_id, frozen11_row=r["frozen11_row"], target_key=r.target_key,
                  state=cell_state(cells_by_row.get(r.row), r, gates)) for r in rows if r["focal"] == "yes"]
    per_target = {}
    for r in rows:
        t = per_target.setdefault(r.target_key, dict(frozen11_row=r["frozen11_row"], claims=0, with_verdict=0,
                                                     survivals=0, not_yet_run=0))
        if r["cell_class"] != "claim":
            continue
        t["claims"] += 1
        c = cells_by_row.get(r.row)
        v = c.get("verdict") if c else None
        if isinstance(v, dict) and "kind" in v and not v.get("descriptor_row"):
            t["with_verdict"] += 1
            t["survivals"] += int(bool(v.get("survives")))
        elif c is None:
            t["not_yet_run"] += 1
    for t in per_target.values():
        t["any_survives"] = ("yes" if t["survivals"] else
                             "not determinable yet" if t["not_yet_run"] else
                             "no claim cell" if not t["claims"] else
                             "no claim received a verdict" if not t["with_verdict"] else "no")
    added = {k: v for k, v in per_target.items() if v["frozen11_row"] == "added"}
    union = dict(claims=sum(v["claims"] for v in per_target.values()),
                 with_verdict=sum(v["with_verdict"] for v in per_target.values()),
                 survivals=sum(v["survivals"] for v in per_target.values()),
                 not_yet_run=sum(v["not_yet_run"] for v in per_target.values()))
    strata = {}
    for r in rows:
        c = cells_by_row.get(r.row)
        v = c.get("verdict") if c else None
        if not (isinstance(v, dict) and "kind" in v and not v.get("descriptor_row")):
            continue
        s = strata.setdefault(stratum(r["inference_level"]), dict(with_verdict=0, survives=0,
                                                                   not_detectable_ok=0, other_status={}))
        s["with_verdict"] += 1
        if v.get("survives"):
            s["survives"] += 1
        elif str(v.get("primary_status")) == "ok":
            s["not_detectable_ok"] += 1
        else:
            k = str(v.get("primary_status"))
            s["other_status"][k] = s["other_status"].get(k, 0) + 1
    return dict(per_row_focal=focal, per_target_any_survives=per_target,
                added_nine=dict(targets=added, n_targets=len(added),
                                rule="descriptive, never headline (amendment 4 §0.1); cell_class 'claim' (U-RC10)"),
                union_frozen11_and_added=union, verdict_table_by_inference_level=strata)


# ================================================================================================================
# writing (tmp + os.replace + read-back)
# ================================================================================================================
def write_checked(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    back = path.read_bytes()
    if back != data:
        refuse(f"read-back of {path.name} differs from what was written")
    return sha256_bytes(back)


def jsonl_text(cells: list) -> str:
    return "".join(json.dumps(c, ensure_ascii=False, sort_keys=False) + "\n" for c in cells)


def check_jsonl_back(path: Path, cells: list) -> None:
    lines = path.read_text(encoding="utf-8").split("\n")
    if lines[-1] != "" or len(lines) - 1 != len(cells):
        refuse(f"{path.name}: line count differs from the cells written")
    for ln, c in zip(lines, cells):
        if json.loads(ln) != json.loads(json.dumps(c)):
            refuse(f"{path.name}: a line read back differs from its cell")


def report_code(repo: Path) -> dict:
    p = repo / SCRIPT_REL
    out = {"script": SCRIPT_REL, "sha256": sha256_bytes(lf(p.read_bytes())) if p.is_file() else None}
    try:
        out["repo_head"] = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True,
                                          text=True, timeout=30).stdout.strip() or None
        st = subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--", SCRIPT_REL], capture_output=True,
                            text=True, timeout=30).stdout.strip()
        out["script_state_at_head"] = "committed, unchanged" if not st else f"uncommitted ({st[:2].strip()})"
    except (OSError, subprocess.SubprocessError) as e:
        out["repo_head"] = f"unavailable ({type(e).__name__})"
    return out


# ================================================================================================================
# cells.md
# ================================================================================================================
def _legcell(lv, two_sided) -> str:
    if not isinstance(lv, dict):
        return "-"
    rep = fnum(lv.get("p_reported"))
    if two_sided:
        return f"{rep} [{fnum(lv.get('p_per_leg_two_sided'))}]"
    return rep


def _md_row(c: dict) -> str:
    v = c.get("verdict")
    computed = isinstance(v, dict)
    legs = c.get("legs")
    two = bool((c.get("direction") or {}).get("two_sided")) if isinstance(c.get("direction"), dict) else False
    dash = "-"
    if computed and isinstance(legs, dict) and legs and all(isinstance(x, dict) and "status" in x
                                                            for x in legs.values()):
        l0, site, sp = (_legcell(legs.get("Level 0"), two), _legcell(legs.get("site"), two),
                        _legcell(legs.get("species"), two))
    elif computed and isinstance(legs, dict) and legs:
        l0 = site = sp = "per map (jsonl)"
    else:
        l0 = site = sp = dash
    conj = c.get("conjunction")
    cj = (fnum(conj.get("p")) + (" (descriptive)" if conj.get("descriptive") else "")) if isinstance(conj, dict)         else dash
    bh = c.get("bh") or {}
    q = fnum(bh.get("q_interim_gate")) if "q_interim_gate" in bh else short(bh.get("family"), 30)
    sens = c.get("sensitivity_ge2_donors")
    sens = ("parcel set unchanged" if isinstance(sens, dict) and sens.get("parcel_set") == "unchanged" else
            f"p {fnum(sens.get('p_conjunction'))}; {sens.get('primary_status')}" if isinstance(sens, dict) else
            short(sens, 40))
    dl = c.get("descriptor_legs")
    if isinstance(dl, dict):
        maps = [m for k, m in dl.items() if k != "direction_from_verdict" and isinstance(m, dict) and "legs" in m]
        src = maps[0] if maps else dl
        l2 = src.get("level2") or {}
        j1 = src.get("J1") or {}
        dl = (f"L2 max {fnum(l2.get('p_reported'))} ({l2.get('status')})" +
              (f"; J1 {fnum(j1.get('p_reported'))} ({j1.get('status')})" if j1 else "")) if l2 else "see jsonl"
    else:
        dl = short(dl, 40)
    rp = c.get("reproduction")
    if isinstance(rp, list):
        flag = (c.get("reproduction_flag") or {})
        labs = [ch.get("label") for ch in c.get("reproduction_checks", [])]
        rp = (f"{len(rp)} record(s)" + (f"; check {', '.join(sorted(set(map(str, labs))))}" if labs else "")
              + (f"; flag {flag.get('flag')}" if flag.get("flag") else ""))
    else:
        rp = short(rp, 40)
    r27 = c.get("r27")
    labels = ("; ".join(sorted({lab for b in r27.values() if isinstance(b, dict) for lab in (b.get("labels") or [])}))
              if isinstance(r27, dict) else dash)
    if c.get("r27_note"):
        labels = "R27 block not to be quoted (run.py label defect; decision ev-1a12dffe1a85af7)"
    st = short(c["status_tsv"], 60)
    if c.get("status_effective") != c.get("status_effective_tsv"):
        st += " -> at use: " + short(c["status_effective"], 70)
    rr = c.get("row_rerun")
    if isinstance(rr, dict):
        st += (f" [row rerun {rr['tag']} ({rr['records']}); primary at use: "
               f"{short(rr['primary']['status_effective'], 50)}]" if rr.get("state") == "read"
               else f" [row rerun {rr['tag']}: {rr['state']}]")
    T = c.get("T")
    T = fnum(T) if isinstance(T, (int, float)) else ("per map" if isinstance(T, dict) else dash)
    d = (c.get("direction") or {}).get("d_star") if isinstance(c.get("direction"), dict) else None
    ve = c["passes"]["verdict"]
    outcome = ve.get("outcome") or ve["state"]
    reading = c.get("reading")

    def num(k):
        x = c.get(k)
        return fnum(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else dash
    return ("| " + " | ".join([
        str(c["row"]), c["cell_id"], c["cell_class"], c["claim_form"], st,
        short(f"{c['route']} / {outcome}", 50), T, fnum(d) if d is not None else dash, l0, site, sp, cj, q, sens,
        dl, rp, short(reading, 70), short(labels, 60), num("m"), num("f_over_m"), num("c_S"), num("R2_grad"),
        num("R2_absx")]) + " |")


MD_HEAD = ("| row | cell | class | form | status (TSV; at use if different) | route / outcome | T | d* | Level 0: 2p(d*) [2min] | site | species "
           "| conj. p | BH q (interim) | >= 2-donor (R11) | descriptor legs | reproduction | reading | R27 labels | m "
           "| f/m | c_S | R2_grad | R2_absx |\n" + "|" + "---|" * 23)


def cells_md(gate: str, cells: list, meta: dict, head: dict, comp: dict, desc: dict, bh: dict, reg: Register) -> str:
    L = [f"# A1 run cells — gate {gate} (RUN_PLAN v3.1 §16)", "",
         f"GENERATED by `{SCRIPT_REL}`; do not hand-edit. Assembly only: every value comes from the run records "
         "named below (script, input, commit); the one arithmetic step is R29's descriptive BH q. A field whose pass "
         "has not run reads \"pass not run\".", "", "## Run identity and inputs", ""]
    for k, v in meta["identity"].items():
        L.append(f"- {k}: `{short(json.dumps(v, sort_keys=True), 140)}`")
    for name, p in meta["passes"].items():
        L.append(f"- pass {name}: {p['state']}" + (f" ({p['n_rows']} rows; RUN_SUMMARY sha256 {p['summary_sha256']})"
                                                  if p.get("n_rows") is not None else ""))
    L += [f"- TSV `{LD.TSV_PATH}` sha256 {reg.tsv_sha256}; register sha256 {reg.register_sha256}; "
          f"prereg_amend_5 sha256 {reg.amend5_sha256}",
          f"- report code: {json.dumps(meta['report_code'])}", "",
          "## Interim headline (§16 :1673-1690)", "", head["headline"], "", head["listed_apart"], ""]
    if head.get("population_restated"):
        L += [head["population_restated"], ""]
    L += [f"| category (§1.8 precedence) | {comp['composition_register_label']} (TSV statuses) | at use "
          "(run-time flags of every pass) |", "|---|---|---|"]
    for k in [k for k in REGISTER_CATS if comp["composition_register"].get(k) or comp["composition"].get(k)]:
        L.append(f"| {k} | {comp['composition_register'].get(k, 0)} | {comp['composition'].get(k, 0)} |")
    if comp["moved_units"]:
        L += ["", "Units whose category moved at use:", "", "| row | cell | register | at use | status (pass record) | "
              "rule |", "|---|---|---|---|---|---|"]
        for m in comp["moved_units"]:
            r0 = m["reasons"][0]
            L.append(f"| {m['row']} | {m['cell_id']} | {m['category_register']} | {m['category_at_use']} | "
                     f"{short(r0['status'], 90)} ({r0['pass']}: {r0['file']}) | {r0['rule']} |")
    L += ["", "| category | units (lower view: S conditional counted not auditable) |", "|---|---|"]
    for k, v in comp["composition_lower_view"].items():
        L.append(f"| {k} | {v} |")
    L += ["", f"Interim check: {json.dumps(meta['interim_check'], ensure_ascii=False)}", "",
          "## Registered descriptors (never headline)", "", "### Per-row focal view (claims_register.md:1931-1945)", "",
          "| frozen-11 row | target | focal cell | state now |", "|---|---|---|---|"]
    for f in desc["per_row_focal"]:
        L.append(f"| {f['frozen11_row']} | {f['target_key']} | {f['cell_id']} (TSV row {f['row']}) | "
                 f"{short(f['state'], 90)} |")
    L += ["", "### Per-target \"any registered claim survives\" (not multiplicity-controlled; cell_class claim)", "",
          "| target | frozen-11 row | claims | with a verdict | survivals | not yet run | any survives |",
          "|---|---|---|---|---|---|---|"]
    for k, t in desc["per_target_any_survives"].items():
        L.append(f"| {k} | {t['frozen11_row']} | {t['claims']} | {t['with_verdict']} | {t['survivals']} | "
                 f"{t['not_yet_run']} | {t['any_survives']} |")
    u = desc["union_frozen11_and_added"]
    L += ["", f"The added nine ({desc['added_nine']['n_targets']} targets; rows 'added' above) and their union with the "
          f"frozen 11: {u['claims']} claims, {u['with_verdict']} with a verdict, {u['survivals']} survivals, "
          f"{u['not_yet_run']} not yet run.", "", "### Verdict table stratified by inference level", "",
          "| inference level | with a verdict | survive | not detectable at this power (ok) | other statuses |",
          "|---|---|---|---|---|"]
    for k, s in desc["verdict_table_by_inference_level"].items():
        L.append(f"| {k} | {s['with_verdict']} | {s['survives']} | {s['not_detectable_ok']} | "
                 f"{short(json.dumps(s['other_status']), 80)} |")
    L += ["", "### BH q-values (descriptive; R29; a q is never a detection)", "",
          f"Interim (this gate): family {bh['interim']['family_size']} rows {bh['interim']['rows']}; outside "
          f"(in m, no conjunction p or flagged): {len(bh['interim']['outside'])}. Final: {bh['final_status']}.", "",
          "## m and the secondary view (claims_register.md:1831-1838)", "",
          f"m = {reg.r4['m.lower']} (TSV verdict_counted_in_m = yes); the secondary near-miss view m′ = "
          f"{reg.r4['m.secondary.near_miss']} is reported beside m, never in it. Rows of this gate counted in m′ only: "
          f"{[c['row'] for c in cells if c['secondary_view']['counted_in_m_prime']] or 'none'}. The runner writes no "
          "secondary-view record.", ""]
    groups = {"asd": [], "non-ASD-outcome": [], "not-ASD-claim": []}
    for c in cells:
        hp = c["headline_population_tsv"]
        if c["cell_class"] == "not-ASD-claim" or "not an ASD claim" in hp:
            groups["not-ASD-claim"].append(c)
        elif c["cell_class"] == "non-ASD-outcome" or "non-ASD" in hp:
            groups["non-ASD-outcome"].append(c)
        else:
            groups["asd"].append(c)
    comp_rows = [c for c in cells if c.get("r27_note")]
    if comp_rows:
        L += ["## R27 blocks of component rows (residue C3)", "",
              f"Rows {', '.join(c['cell_id'] for c in comp_rows)}: {COMPONENT_R27_NOTE} Recorded (not to be quoted): "
              + "; ".join(f"{c['cell_id']}: reading '{b.get('reading_as_recorded')}', labels "
                          f"{'; '.join(b.get('labels') or []) or 'none'}" for c in comp_rows
                          for b in c["r27"].values() if isinstance(b, dict)) + ".", ""]
    L += ["## Cells by target (ASD cells)", ""]
    for tk in sorted({c["target_key"] for c in groups["asd"]}, key=lambda t: min(c["row"] for c in cells
                                                                                 if c["target_key"] == t)):
        cs = [c for c in groups["asd"] if c["target_key"] == tk]
        L += [f"### {tk} (target {cs[0]['target_no']}; frozen-11 row {cs[0]['frozen11_row']})", "", MD_HEAD]
        L += [_md_row(c) for c in cs] + [""]
    for key, title in (("non-ASD-outcome", "Non-ASD registered outcomes (reported apart from every ASD count)"),
                       ("not-ASD-claim", "Not-ASD claims (reported apart; kept out of the ASD headline)")):
        L += [f"## {title}", ""]
        if groups[key]:
            L += [MD_HEAD] + [_md_row(c) for c in groups[key]] + [""]
        else:
            L += ["none in this gate", ""]
    if gate == "G2":
        L += g2_md(cells)
    text = "\n".join(L) + "\n"
    check_wording(text, "cells.md")
    return text


# ================================================================================================================
# MANIFEST_claims.md (R26)
# ================================================================================================================
VERDICT_LEGS_FULL = ("Level 0", "S1c", "S2c", "G1", "G3m", "G6s", "G6l")
DESC_LEGS = ("Level-2 G1", "G2", "G3", "G4", "G5", "J1", "naive joint")
MANIFEST_COLS = VERDICT_LEGS_FULL + DESC_LEGS + ("T_abs",)


def planned_legs(plan: dict) -> dict:
    """{column: pass or None} for one row's route (RUN_PLAN §4 legs table; run.py FORM_NO_PASS)."""
    out = {c: None for c in MANIFEST_COLS}
    route = plan["route"]
    if route.startswith("verdict:"):
        if plan.get("component") is not None or route.startswith("verdict: component"):
            for c in ("Level 0", "S1c", "S2c"):
                out[c] = "verdict"
        else:
            for c in VERDICT_LEGS_FULL:
                out[c] = "verdict"
            for c in DESC_LEGS:
                out[c] = "descriptor"
            if plan.get("t_abs"):
                out["T_abs"] = "descriptor"
    elif route == "descriptor: gene-set-only (R10)":
        for c in ("Level-2 G1", "G2", "G3", "G4", "G5"):
            out[c] = "descriptor"
    elif route == "descriptor: signed-weight rho (P15)":
        out["S1c"] = out["S2c"] = "verdict"
        for c in ("Level-2 G1", "G2", "G3", "G4", "G5", "J1"):
            out[c] = "descriptor"
    return out


def _leg_status_from(rec: dict, col: str, pass_: str) -> str:
    res = rec.get("result") or {}
    if pass_ in ("verdict", "sensitivity"):
        v = res.get("verdict")
        if not isinstance(v, dict):
            site = dget(res, "site", "legs") or {}
            return str((site.get(col) or {}).get("status", "n/a"))
        core, _ = verdict_core(v)
        legs = core.get("legs") if not core.get("two_cohort") else \
            next(iter((core.get("per_map") or {}).values()), {}).get("legs")
        lv = (legs or {}).get(col)
        return str(lv.get("status")) if isinstance(lv, dict) else "n/a"
    if "per_map" in res:
        m = next(iter(res["per_map"].values()), {})
        if col in ("J1", "naive joint"):
            x = m.get("J1" if col == "J1" else "naive_joint") or {}
            return str(x.get("status"))
        if col == "T_abs":
            ta = m.get("T_abs") or {}
            return "ok" if ta else "n/a"
        return str(((m.get("legs") or {}).get(col) or {}).get("status"))
    legs = res.get("legs") or (res.get("gene_legs") or {}).get("legs") or {}
    if col == "J1":
        return str(((res.get("gene_legs") or {}).get("J1") or {}).get("status"))
    return str((legs.get(col) or {}).get("status"))


def manifest_line(reg: Register, gates: dict, row, parcellation: str, survivors: set) -> str:
    """One claim x parcellation line: the legs planned for the row's route under its gate (run.classify with the
    row's own gate open: the plan, nothing loaded) and the status each pass recorded."""
    g = reg.gate_of_row(row)
    gd = gates.get(g)
    plan = _route_plan(row, frozenset({row.gated[0]}) if row.gated is not None else frozenset())
    legs = planned_legs(plan)
    gate_run = gd is not None and gd.verdict_complete()
    cells = []
    for col in MANIFEST_COLS:
        pass_ = legs[col]
        if parcellation != "primary":
            pass_ = "sensitivity" if (pass_ == "verdict" and plan["route"].startswith("verdict:")) else None
        if pass_ is None:
            cells.append("n/a")
            continue
        p = gd.passes[pass_] if gd is not None else None
        if p is None or p.state == "absent":
            cells.append(f"deferred ({row.gated[0]} not run)" if row.gated is not None and not gate_run else PNR)
            continue
        if p.state == "incomplete":
            cells.append("pass not run (incomplete)")
            continue
        rec = p.rows.get(row.row)
        if rec is None:
            cells.append("pass not run (row)")
        elif rec.get("outcome") != "computed":
            cells.append(str(rec.get("outcome")))
        elif pass_ == "sensitivity" and dget(rec, "result", "parcel_set") == "unchanged":
            cells.append("= primary")
        else:
            st = _leg_status_from(rec, col, pass_)
            cells.append("computed" if st == "ok" else st)
    vrec = gd.passes["verdict"].rows.get(row.row) if gate_run else None
    if parcellation == "primary":
        if row.row in survivors:
            mv = "pass not run (WP6: 10 cells, R11)"
        elif plan["kind"] in ("no statistic", "refused") or plan["route"].startswith("descriptor:"):
            mv = "n/a (no verdict)"
        elif vrec is not None and vrec.get("outcome") == "computed":
            mv = "n/a (not a survivor; R11)"
        else:
            mv = "pending (no verdict yet)"
    else:
        mv = "-"
    if vrec is not None:
        sw = str(vrec.get("status_written"))
        status = (vrec.get("outcome") if vrec.get("outcome") == "computed" else
                  sw if sw.startswith(str(vrec.get("outcome"))) else f"{vrec.get('outcome')}: {sw}")
    elif row.gated is not None and not gate_run:
        status = f"deferred (gate {row.gated[0]} not run)"
    else:
        status = PNR if not gate_run else PNR_ROW
    return "| " + " | ".join([str(row.row), row.cell_id, row.gate, row.claim_form, parcellation] + cells +
                             [mv, short(status, 70)]) + " |"


def manifest_md(reg: Register, gates: dict, cells_by_row: dict, meta: dict) -> str:
    survivors = {n for n, c in cells_by_row.items() if isinstance(c.get("verdict"), dict)
                 and c["verdict"].get("survives")}
    L = ["# MANIFEST_claims — A1 `audit` claim factorial (prereg §7; RUN_PLAN R26)", "",
         f"GENERATED by `{SCRIPT_REL}`; do not hand-edit. The claim × level × null × parcellation × "
         "multiverse factorial with status (prereg.md:289-291). Declared file-name deviation (R26): prereg §7 names "
         "`results/MANIFEST.md`, GENERATED by `arcs/audit/src/e3_gates.py` for the plant factorial; the pair of files is "
         "prereg §7's manifest and each names the other.", "",
         "Columns: the verdict legs (Level 0; site S1c, S2c; species G1, G3m, G6s, G6l), the descriptor legs (Level-2 "
         "G1, G2, G3, G4, G5, J1, naive joint, T_abs) and the multiverse (R11: 10 cells, surviving claims only), on the "
         "primary parcels and the >= 2-donor parcel set (R11: the verdict legs again). Status: 'computed' (the leg's "
         "status ok), else the leg's own status ('unmatched', 'not computable (pool < m)', 'not applicable', 'degenerate "
         "pool', ...); 'n/a' = not a leg of the row's form or parcellation; 'pass not run' (incomplete: the pass has "
         "not finished; row: the row is not in the pass); 'deferred (Gx not run)'; 'no statistic' / 'not run' / "
         "'refused' = the pass's outcome for the row, its status in the last column ('not auditable ...', 'not "
         "testable ...', ...); '= primary' = the >= 2-donor parcel set is unchanged (R11).", ""]
    for g in GATES:
        gd = gates.get(g)
        if gd is None:
            L.append(f"- gate {g}: no pass present")
            continue
        st = ", ".join(f"{n} {p.state}" for n, p in gd.passes.items())
        ident = gd.raw_identity or {}
        L.append(f"- gate {g}: {st}; run commit {ident.get('run_commit', '-')}; code hash {ident.get('code_hash', '-')}")
    for tag in sorted({t for t, _ in ROW_RERUN_GATES.values()}):
        rows_ = sorted(n for n, (t, _) in ROW_RERUN_GATES.items() if t == tag)
        gdr = ROW_RERUN_GATES[rows_[0]][1]
        ident = gdr.raw_identity or {}
        L.append(f"- row rerun {tag} ({gdr.rel}; rows {', '.join(map(str, rows_))}: their lines below read these "
                 f"records): run commit {ident.get('run_commit', '-')}; code hash {ident.get('code_hash', '-')}")
    L += [f"- TSV sha256 {reg.tsv_sha256}; report code {json.dumps(meta['report_code'])}", "",
          "| row | cell | gate | form | parcellation | " + " | ".join(MANIFEST_COLS) + " | multiverse | status |",
          "|" + "---|" * (5 + len(MANIFEST_COLS) + 2)]
    for r in sorted(reg.rows.values(), key=lambda x: x.row):
        for par in ("primary", ">= 2 donors"):
            gs = ({reg.gate_of_row(r): ROW_RERUN_GATES[r.row][1]} if r.row in ROW_RERUN_GATES and
                  isinstance(cells_by_row.get(r.row), dict) and "row_rerun" in cells_by_row[r.row] else gates)
            L.append(manifest_line(reg, gs, r, par, survivors))
    text = "\n".join(L) + "\n"
    check_wording(text, "MANIFEST_claims.md")
    return text


# ================================================================================================================
# main
# ================================================================================================================
def assemble(repo: Path, results_root: Path, gate: str, incomplete: str = "refuse") -> dict:
    reg = Register(repo)
    REG_GATE[:] = [reg]
    reg_check = check_register_numbers(reg)
    gates = {g: load_gate(results_root, g, reg, incomplete) for g in GATES}
    gates = {g: gd for g, gd in gates.items() if gd.any_present()}
    if gate not in gates:
        refuse(f"no pass of gate {gate} is present under {results_root / 'a1_run' / gate}")
    cells_all = {}
    per_gate_cells = {}
    for g, gd in gates.items():
        if not any(p.complete() for p in gd.passes.values()):
            continue
        cs = [build_cell(reg, gd, r) for r in sorted(reg.gate_rows(g), key=lambda x: x.row)]
        for c in cs:
            c["bh"] = bh_entry(reg.rows[c["row"]], c)
            cells_all[c["row"]] = c
        per_gate_cells[g] = cs
    if gate not in per_gate_cells:
        refuse(f"gate {gate}: no complete pass (incomplete passes skipped)")
    apply_row_reruns(reg, results_root, gates, per_gate_cells, cells_all)
    if "G2" in per_gate_cells:                    # RUN_PLAN_amend_5 v2: labels and the post-exposure version (G2 only)
        annotate_g2(reg, results_root, per_gate_cells["G2"], incomplete)
    bh_gate = {g: apply_bh(cs, f"interim (BH within gate {g}; R29)", "q_interim_gate")
               for g, cs in per_gate_cells.items()}
    all_done = all(g in gates and gates[g].verdict_complete() for g in GATES)
    if all_done:
        bh_final = apply_bh(list(cells_all.values()), "final (R29: once, after every gate has run)", "q_final")
        final_status = f"computed over {bh_final['family_size']} rows"
    else:
        missing = [g for g in GATES if g not in gates or not gates[g].verdict_complete()]
        final_status = ("not computed (R29: the final q's are computed once, after every gate has run; not run: "
                        + ", ".join(missing) + ")")
        for c in cells_all.values():
            if isinstance(c.get("bh"), dict):
                c["bh"]["q_final"] = final_status
    comp = compose(reg, gates, cells_all)
    units = {u["row"]: u for u in comp["units"]}
    for n, c in cells_all.items():
        u = units.get(n)
        c["population"] = ({k: u[k] for k in ("category_register", "category", "moved", "out_of_population",
                                              "provisional", "run_flags", "pending")} | {"unit": True}
                           if u is not None else {"unit": False, "headline_population_tsv": c["headline_population_tsv"],
                                                  "note": "not a population unit in this view (§1.2; U-RC7)"})
        if u is not None and not set(u["run_flags"]) <= set(c["flags"]["run"]):
            refuse(f"row {n}: the cell's run flags {c['flags']['run']} lack the composition's {u['run_flags']} (B2)")
    interim_check = assert_interim(reg, comp)
    head = headline_sentences(comp)
    desc = registered_descriptors(reg, gates, cells_all)
    gd = gates[gate]
    meta = {"identity": {k: (gd.raw_identity or {}).get(k) for k in ("run_commit", "code_hash", "K", "g6l_mode")}
            | {"sources.kind": dget(gd.raw_identity or {}, "sources", "kind")},
            "passes": {n: {"state": (p.note or p.state) if p.state != "absent" else PNR,
                           "n_rows": len(p.rows) if p.complete() else None,
                           "summary_sha256": p.summary_sha, "launch_record_sha256": p.launch_sha,
                           "unread_files": p.unread} for n, p in gd.passes.items()},
            "report_code": report_code(repo), "register_check": reg_check, "interim_check": interim_check}
    return dict(reg=reg, gates=gates, cells=per_gate_cells[gate], cells_all=cells_all, comp=comp, head=head,
                desc=desc, bh=dict(interim=bh_gate[gate], final_status=final_status), meta=meta)


# 2026-11-02: row reruns (wp4_launch --row-rerun TAG --rows ROWS, run.py --rows --rerun-tag): rows recomputed at a later
# commit after their carrier came back from quarantine (RUN_PLAN §8 step 6; the refusal reads "the operator moves it
# back"). The rerun's cell replaces the primary cell at use; the primary records stay where they were written and are
# named in the cell (row_rerun.primary). Only rows that are no population unit may be rerun this way (no count moves);
# the rerun's passes must all be complete, of one run identity, and hold exactly the declared rows.
ROW_RERUNS = (("G2", "liu_t3", (478,),
               "the two Liu T3 carriers (liu_t3_cortthick, liu_t3_subvol) moved back from quarantine to their pinned "
               "paths by the operator; the G2 material stage rerun at the rerun's commit (RUN_PLAN §8 step 6)"),)
ROW_RERUN_NOTE = ("the records' rerun_rule field is run.py's fixed --rerun-tag text (RUN_PLAN §17 (3)-(4)); this rerun's "
                  "reason is the carrier's return from quarantine (RUN_PLAN §8 step 6), not a changed statistic path")


def apply_row_reruns(reg: Register, results_root: Path, gates: dict, per_gate_cells: dict, cells_all: dict) -> list:
    """Replace each declared row-rerun row's cell by the cell built from its rerun records (ROW_RERUNS); a rerun not
    yet present leaves the primary cell and records 'pending'. Before any BH and composition."""
    done = []
    ROW_RERUN_GATES.clear()
    run_gates = {g for g, gd in gates.items() if gd.verdict_complete()}
    view, _ = population_rows(reg, {g for g in run_gates if g in ("G1", "G2")})
    units = {r.row for r in view}
    for g, tag, rows, why in ROW_RERUNS:
        if g not in per_gate_cells:
            continue
        base = results_root / "a1_run" / f"rerun_{tag}" / g
        if not base.is_dir():
            for n in rows:
                cells_all[n]["row_rerun"] = {"tag": tag, "state": "pending (no rerun records)", "reason": why}
            continue
        gdr = load_gate(results_root, g, reg, "skip", base=base)
        gdr.rel = f"a1_run/rerun_{tag}/{g}"
        running = [name for name, p in gdr.passes.items() if p.state == "incomplete"]
        if running:   # a rerun still running (or stopped): the primary cell stands, the rerun reads pending
            for n in rows:
                cells_all[n]["row_rerun"] = {"tag": tag, "state": "pending (rerun passes incomplete: "
                                             + ", ".join(running) + ")", "reason": why}
            continue
        if not gdr.verdict_complete():
            refuse(f"row rerun {tag}: its verdict pass is absent")
        for name, p in gdr.passes.items():
            if p.state == "absent" and gates[g].passes[name].state == "absent":
                continue   # a pass the primary run has not run either
            if not p.complete():
                refuse(f"row rerun {tag}: the {name} pass is not complete ({p.state})")
            if sorted(p.rows) != sorted(rows):
                refuse(f"row rerun {tag}: the {name} pass holds rows {sorted(p.rows)}, not the declared {sorted(rows)}")
        for n in rows:
            if n in units:
                refuse(f"row rerun {tag}: row {n} is a population unit (a row rerun may not move a count)")
            row = reg.rows[n]
            prim = cells_all[n]
            new = build_cell(reg, gdr, row)
            new["bh"] = bh_entry(row, new)
            new["row_rerun"] = {
                "tag": tag, "state": "read", "reason": why, "note": ROW_RERUN_NOTE, "records": gdr.rel,
                "identity": {k: (gdr.raw_identity or {}).get(k) for k in ("run_commit", "code_hash")},
                "primary": {"status_effective": prim["status_effective"],
                            "status_effective_source": prim["status_effective_source"],
                            "reading": prim.get("reading"), "commit": prim.get("commit"),
                            "passes": {k: {kk: (prim["passes"].get(k) or {}).get(kk)
                                           for kk in ("outcome", "status_written", "file", "sha256")} for k in PASSES}}}
            cs = per_gate_cells[g]
            cs[[c["row"] for c in cs].index(n)] = new
            cells_all[n] = new
            ROW_RERUN_GATES[n] = (tag, gdr)
            done.append(n)
    return done


ROW_RERUN_GATES: dict = {}   # row -> (tag, GateData of its rerun), set by apply_row_reruns; read by manifest_md


PE_EXCLUDED = ("excluded: never in the interim headline population, a tested-only denominator, a composition count "
               "or a BH family (RUN_PLAN_amend_5 v2; RUN_PLAN §17 (4) both versions reported)")


PE_PENDING = "pending (the amend_5 post-exposure passes have not completed)"


def annotate_g2(reg: Register, results_root: Path, cells: list, incomplete: str) -> None:
    """RUN_PLAN_amend_5 v2, G2 only, after the cells are built and BEFORE any composition (so nothing here can move
    a count): (1) each cell carries wp4_sources.row_labels (L130's line-130 label on the MDD-set DEG cells);
    (2) a cell an amend_5 post-exposure reading bears on (wp4_sources.amend5_readings) carries its SECOND version
    beside the primary one, read from results/a1_run/rerun_amend5/G2/ (the passes run with A1_G2_VERSION=amend5),
    labelled "post-exposure version (amend_5)" and excluded from every count (PE_EXCLUDED). The primary cell (its
    status, verdict, flags, population) is never changed."""
    from . import wp4_layout as W4L
    from . import wp4_sources as W4S
    base = results_root / "a1_run" / f"rerun_{W4L.AMEND5_RERUN_TAG}" / "G2"
    # the second version may be partly run: its incomplete passes are skipped (read "pass not run"), never refused,
    # and the primary report is produced whatever its state (2026-10-21)
    gd5 = load_gate(results_root, "G2", reg, "skip", base=base) if base.is_dir() else None
    if gd5 is not None and not any(p.complete() for p in gd5.passes.values()):
        gd5 = None
    for c in cells:
        row = reg.rows[c["row"]]
        c["labels_g2"] = W4S.row_labels(row.cell_id)
        rd = W4S.amend5_readings(row.cell_id, row["map"])
        if not rd:
            continue
        pe = {"label": W4L.AMEND5_VERSION_LABEL, "readings": rd, "primary_status_effective": c["status_effective"],
              "counted": PE_EXCLUDED}
        if gd5 is None:
            pe["state"] = PE_PENDING
        else:
            c5 = build_cell(reg, gd5, row)
            pe.update(state="read", status_effective=c5["status_effective"], reading=c5.get("reading"),
                      labels=W4S.row_labels(row.cell_id, W4L.VERSION_AMEND5),
                      passes={n: (c5["passes"][n].get("outcome") or c5["passes"][n].get("state")) for n in PASSES},
                      commit=c5.get("commit"),
                      pending_passes=[n for n in PASSES if not gd5.passes[n].complete()])
        c["post_exposure_version"] = pe


def g2_md(cells: list) -> list:
    """The G2 cells' labels and post-exposure versions (RUN_PLAN_amend_5 v2), as their own section of cells.md."""
    lab = [c for c in cells if c.get("labels_g2")]
    pe = [c for c in cells if c.get("post_exposure_version")]
    if not lab and not pe:
        return []
    out = ["## Labels and post-exposure versions (RUN_PLAN_amend_5 v2; G2)", ""]
    if lab:
        out += ["| row | cell | labels |", "|---|---|---|"]
        out += [f"| {c['row']} | {c['cell_id']} | {'; '.join(c['labels_g2'])} |" for c in lab] + [""]
    if pe:
        out += [f"Each row below keeps its primary status; its post-exposure version is reported beside it. "
                f"{PE_EXCLUDED}.", "",
                "| row | cell | primary (at use) | readings | post-exposure version (amend_5) |", "|---|---|---|---|---|"]
        for c in pe:
            v = c["post_exposure_version"]
            got = (short(str(v.get("status_effective")), 70) + "; verdict pass " + str((v.get("passes") or {}).get(
                "verdict"))) if v.get("state") == "read" else v.get("state")
            out.append(f"| {c['row']} | {c['cell_id']} | {short(str(v['primary_status_effective']), 70)} | "
                       f"{'; '.join(v['readings'])} | {got} |")
        out.append("")
    return out


def write_outputs(a: dict, out_root: Path, gate: str) -> dict:
    reg = a["reg"]
    gdir = out_root / "a1_run" / gate
    for name in PASSES:   # never into a pass folder
        if (gdir / name).resolve() == gdir.resolve():
            refuse("output folder is a pass folder")
    cells = a["cells"]
    p_jsonl = gdir / "cells.jsonl"
    sha_jsonl = write_checked(p_jsonl, jsonl_text(cells))
    check_jsonl_back(p_jsonl, cells)
    md = cells_md(gate, cells, a["meta"], a["head"], a["comp"], a["desc"], a["bh"], reg)
    sha_md = write_checked(gdir / "cells.md", md)
    headline = {"what": "A1 interim headline (RUN_PLAN §16 :1673-1690); GENERATED by " + SCRIPT_REL,
                "sentences": a["head"], "composition": {k: v for k, v in a["comp"].items() if k != "units"},
                "units": a["comp"]["units"], "registered_descriptors": a["desc"], "bh": a["bh"],
                "meta": a["meta"], "inputs": {"cells.jsonl": sha_jsonl, "tsv": reg.tsv_sha256,
                                              "register": reg.register_sha256, "prereg_amend_5": reg.amend5_sha256}}
    htxt = json.dumps(headline, ensure_ascii=False, indent=1) + "\n"
    sha_h = write_checked(gdir / "headline.json", htxt)
    if json.loads((gdir / "headline.json").read_text(encoding="utf-8")) != json.loads(htxt):
        refuse("headline.json read back differs")
    man = manifest_md(reg, a["gates"], a["cells_all"], a["meta"])
    sha_m = write_checked(out_root / "MANIFEST_claims.md", man)
    return {"cells.jsonl": sha_jsonl, "cells.md": sha_md, "headline.json": sha_h, "MANIFEST_claims.md": sha_m}


def summary_counts(a: dict) -> dict:
    cells = a["cells"]
    by_route, by_outcome, repro = {}, {}, 0
    for c in cells:
        by_route[c["route"]] = by_route.get(c["route"], 0) + 1
        o = c["passes"]["verdict"].get("outcome") or c["passes"]["verdict"]["state"]
        by_outcome[o] = by_outcome.get(o, 0) + 1
        repro += sum(1 for e in c["reproduction"] if e["kind"] == "reproduction") if isinstance(
            c["reproduction"], list) else 0
    return dict(cells=len(cells), by_route=by_route, by_verdict_outcome=by_outcome, reproduction_records=repro)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="A1 results writer (RUN_PLAN §16; assembly only)")
    ap.add_argument("--gate", required=True, choices=GATES)
    ap.add_argument("--incomplete", choices=("refuse", "skip"), default="refuse")
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--results-root", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    repo = Path(a.repo).resolve()
    results_root = Path(a.results_root).resolve() if a.results_root else repo / "arcs/audit/results"
    out_root = Path(a.out).resolve() if a.out else results_root
    try:
        res = assemble(repo, results_root, a.gate, a.incomplete)
        shas = write_outputs(res, out_root, a.gate)
    except ReportRefused as e:
        print(str(e).encode("ascii", "replace").decode("ascii"))
        return 3
    counts = summary_counts(res)
    print(json.dumps(dict(gate=a.gate, out=str(out_root), written=shas, counts=counts,
                          composition=res["comp"]["composition"], population_units=res["comp"]["population_units"],
                          survivals=res["comp"]["survivals"], can_survive=res["comp"]["can_survive"],
                          interim_check=res["meta"]["interim_check"]), ensure_ascii=True, indent=1))
    print(res["head"]["headline"].encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
