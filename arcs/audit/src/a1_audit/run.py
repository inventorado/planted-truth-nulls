"""A1 runner integration (arcs/audit/RUN_PLAN.md v3.1, FROZEN sha256 16c60232...: §1, §2.3, §2.4, §4, §7, §14, §16,
§17; R7, R9, R11, R19, R24; WP1 of §18).

    python -X utf8 -u -m a1_audit.run --commit <sha> --pass {verdict,descriptor,sensitivity} --gate {none,G1,G2}
           [--rows 1-80,478] [--jobs 20] [--K audit|plant|site=500,species=200,...] [--g6l exact|plant]
           [--plant P<n> [--case N|A-B] [--dev --out DIR]] [--dry]

Order (nothing is computed before 1-3 hold):
1. Launch: launch.launch(repo, commit, gate) (L1-L15) first. A non-plant run refuses on LaunchRefused (exit 3; no
   override). An official plant run (--plant without --dev) also requires the launch to pass (a pinned worktree, §2.3).
   `--plant P<n> --dev --out DIR` may continue after a refusal: every output is stamped "DEV (launch refused: <ids>)"
   and written only under DIR, which must lie outside arcs/audit/results and arcs/audit/run_manifests. A dev run never
   runs the privacy guard's self-test (it reads the HGNC table under E:\\data\\asdg\\, which no dev run opens), so its
   L13 is always recorded "not run" and its launch is always refused.
2. Gate: --gate G1 -> gates.require_g1_open(), --gate G2 -> gates.require_step3v_open(), before anything touches the
   gate's material (L15). A closed gate refuses every run, dev included.
3. Loader: loader.load (after L1-L3; a dev run passes allow_unlaunched). Open gates come from a passed launch only.

Dispatch (RUN_PLAN §4 :353-363), by the row's effective status, then its claim_form and its registered T text:
- deferred / not testable (< 5) / not auditable / out of scope / "not testable as stated" without a registered T form
  -> written with the TSV status and no statistic;
- "not testable as stated: signed-weight set score" (TSV rows 103-117) -> the signed-weight descriptor (P15; forms.py);
- set-vs-map / decoded-list / PLS-enrichment / component (auditable, conditional, by-construction resolution-limited,
  or a pooled "not testable as stated" list with a registered descriptor T) -> the adapters and the verdict driver
  (verdict pass), the descriptor legs (descriptor pass), the >= 2-donor verdict legs (sensitivity pass, R11);
- selected lists (RA-11 ... 14, TSV rows 208-211) -> adapters.SelectedList (RUN_PLAN_amend_1 R34: Level 0 = the
  permutation null with re-selection on leg 10, site legs 0 / 1; the paper's selection rule and statistic come from a
  source, given no generator);
- gene-set-only ("no calibrated test") -> the Liu route (R10; forms.py); "other" -> MOR-T (R21) / BENK-C2, PARK-C5 (R28):
  the decoded-list route with their labels (no T_abs; R28's proxy direction; R28's RLM written beside the row as
  row_<n>_rlm.json in the verdict pass). WP2 (§18) replaced the four stubs; the stub mechanism stays (none is routed).
  A form's reading that no frozen text pins raises NotImplementedError naming it; the row reads "not run (<message>)".
- anything the runner cannot read (a status, T text, direction, analysis class or map / cell index form not pinned
  below) -> "refused: <reason>" with no statistic (fail closed).
A computing row then needs: its carrier test passed if its status is conditional (WP5; "not run (conditional: ...)"),
its analysis class determined (WP5), and its sources. Map / set / context / selection-rule sources are an interface
(Sources); only SYNTHETIC implementations exist (real loaders, identity checks and re-parcellation are WP3; the real
context hook names adapters.build_context_checked, RUN_PLAN_amend_1 R35's first-use check), so a real row whose sources
are not implemented reads "not run (WP3 loader pending)".

Seeds: verdict.seed_callables(target, row, map index, cell index) (claims_register.md:1076-1082; R7; R24). Map / cell
indices are read from the TSV's forms (claims_register.md §1.9 :1077-1080): an integer; "0 = ABIDE I; 1 = ABIDE II
(§1.9)" -> maps 0 and 1 (two-cohort, P14); "UNDETERMINED: 1 ... n, one per cell ..." -> refused until the build records
the index; "n/a: no registered T ..." -> no statistic; anything else -> refused (counted per form, no row text).

Legs and checkpoints (§4 :364-381): one checkpoint per row x map x library entry point - the verdict legs
(verdict.collect_legs: Level 0 incl. the component permutation leg 8, the site legs 0-1, the species legs 2-5), the
descriptor legs (descriptors.descriptor_pass: Level-2 G1 [2], G2 [11], G3 [R24], G4 [12], G5 [13], J1 [14], naive joint
[15]) and T_abs (descriptors.t_abs_legs: 21-25) - plus one G6l screen per (S, class, analysis parcels) serving every
row's leg-5 and leg-25 streams (§4 'Shared G6l screens'; verdict.shared_g6l in exact mode, plant_mode in plant mode).
The runner never re-implements a library step: whatever the library asserts (e.g. RUN_PLAN_amend_1's R32 (c) floor
checks inside collect_legs / descriptor_pass / t_abs_legs) runs on every row. a3_port.Checkpoints / run_pending (resumable, atomic,
refusing another run's checkpoint); jobs with OMP_NUM_THREADS=1; log lines flushed one by one. Every task's peak memory
is measured (psutil if present, else tracemalloc; on Windows also the process peak working set), and a job above
2.5 GB is flagged "DEFECT" (§4 memory).

Results: one JSON per row x pass, atomic (tmp + os.replace) and read back, with the provenance block (§2.4;
launch.provenance_block for a passed launch) and launch.row_provenance (keys, integer seeds, input hashes, start / end,
host). Real runs: arcs/audit/results/a1_run/<ungated|G1|G2>/<pass>/; official plant runs: arcs/audit/run_manifests/
plants/<plant>/... (R18 :846-847: "Run-control records (launch assertions, gate records, plant outputs) ... go to
arcs/audit/run_manifests/ (launch/, G1/, plants/)"); dev runs: only under --out. Checkpoints of real / plant runs go
under artifacts/audit/ (gitignored), of dev runs under --out.

Readings this module makes where the frozen texts leave the runner a choice (each listed in the WP1 report):
U1 checkpoint granularity = row x map x library entry point (above; §4 :380 says "one per row x leg"); U2 plant view: a plant run takes each row's own gate
as open, a conditional row's carrier test as passed, and a conditional analysis class ("dk-ctx | V-DK (conditional:
...)") as its first named option (synthetic material only, nothing gated is touched); U3 a real
run processes the rows whose gate column equals its --gate (Dear's G1+G2 rows in the G1 run); U4 result folder name
'ungated' for --gate none (R18's vocabulary); U5 official plant outputs under run_manifests/plants (R18), not
results/; U6 plant-scale descriptor counts (G1-G5 200, J1 100 sets x 500 surrogates, naive joint 500, component
permutations 500): §7 pins site 500 / species 200 only; U7 T_abs is computed iff the T column names T_abs, its tail is
lower iff the direction column says "T_abs lower tail"; U8 component PLS1-R2 / PLSRegression on S's columns when the
row has a built set (MOR), else on all genes (adapters.py docstring, not a frozen line; a selected list re-selects
its own genes); U9 rows 120-131 (T column "signed-weight form") go to the signed-weight descriptor (forms.py), not
the set-vs-map verdict; U10 direction: "two-sided..." ->
two-sided, "+ (" / "\\u2212 (" -> one-sided, anything else refused; U11 memory measure as above, 2.5 GB = 2.5e9 bytes;
U12 the descriptor pass takes d* from the verdict pass's result file and leg 25's windows from the verdict pass's
shared screen (recomputed, stream by stream identical, if absent); U13 sensitivity: finite y and >= 2 donors, "parcel
set unchanged" when equal to the primary parcels; U14 set members absent from the analysis universe are counted, < 5
present -> "not testable (< 5)" at use; U15 a dev launch never runs the guard self-test.

Fixes of the asdg-skeptic review of WP1 (61e3887; the non-stub parts of this module):
- B1: every row routed with descriptor = True (descriptor cells, "not testable as stated" pooled lists, R21 / R28's
  descriptor readings) is written through verdict.descriptor_row_record (verdict_for_plan): survives = False, primary
  status = the row's TSV status under the run's view, the computed record under 'descriptor' ("descriptive (not a
  verdict)" beside any pass at alpha); verdict and sensitivity passes alike.
- B3: PLANT CHOICE (orchestrator, 2026-10-01): leg streams within a plant case. In plant view every leg of a plant case
  draws from SeedSequence([20260925, 900, plant_id, case, class_id, leg]) with the claim leg numbers; R24's G3 = the
  first spawned child of that case's leg-3 key; J1 / naive joint in R7's fixed order (verdict.plant_seed_callables,
  seeds.plant_seed_record); class_id = seeds.plant_class_id (one fixed integer per class), plant_id = seeds.plant_int
  (P3a / P3b share 3 and are kept apart by their case ranges, seeds.PLANT_CASE_RANGES). --case N or A-B names the
  case(s); each case writes under its own case_<n> folder and its synthetic data come from seeds.plant_data_seed.
  Within one case every row (and both maps of a two-cohort row) of a class draws the same leg streams (common random
  numbers inside a case; the rows' maps and sets differ). P2 keeps the claim keys (the declared P2-only exception: its
  purpose is the claim keys, RUN_PLAN §7 :1128) and takes no --case. WP2r (orchestrator's list, 2026-10-02): the
  signed-weight / gene-set-only form rows (forms.py) draw from and record the plant case's keys too (seeds.plant_leg_seed
  through seeds_of / seed_record_for); a gene-set-only row's class word is its synthetic Liu data kind's id
  (plant_class_word).
- RUN_PLAN_amend_2 R41: the signed-weight rows' descriptor pass computes T_S, the gene legs with S's weights carried
  over and the registered outcome (forms.signed_weight_descriptor; the row's ±.05 comparator from its TSV reproduction
  column, forms.sw_published_rho); a fail-closed form status carries its counts ('status_detail', R42 (d)).
- C3: a worktree run writes under the MAIN repository (main_repository: git's common dir), RUN_PLAN §2.3 :327-328, so
  the worktree stays clean and a second pass from it is not refused by L11.
- C4: plant K follows a plant's registered counts where §7 pins them (PLANT_K_OVERRIDES: P12's 10,000 component
  permutations, RUN_PLAN.md:1139), recorded in every header; --K key=value still overrides.
- C5: the descriptor and sensitivity passes use a verdict-pass file only if its run identity (run commit, code hash,
  K, G6l mode, sources, seed view) equals this run's (else the row is refused), and reuse the verdict pass's G6l screens
  only if that pass's checkpoint RUN.json has the same identity.
- C8: analysis parcels are counted against the class's parcels (adapters.analysis_parcels(class_parcel_ids=...)).
- C9: --out may not lie anywhere inside the repository (the worktree or the main repository).
- WP3 phase 1 (RUN_PLAN §18 WP3; the WP3 phase-1 report): a real (non-plant) run's sources are
  real_sources.WP3Sources (the ungated loaders; every file through RealSources.real_path; the phase-2 manifest read
  before any carrier; "not run (phase 2 material pending)" until wp3_material has run); the WP2 base RealSources stays
  the refuse-all interface (dry_dispatch's default). Spec kind "real-wp3" rebuilds them in the workers. A real run
  writes row_<n>_repro.json beside a computed ungated row (wp3_repro: Segura and Moreau in the verdict pass, Liu in
  the descriptor pass; RUN_PLAN §16 "the reproduction check or descriptive comparison"); a gene-set-only row's
  record carries its loader record (counts of the HGNC mapping and samples).
- Pre-WP4 (§17; after the WP3 run): r27_for_map recognises the component kinds records carry (COMPONENT_KINDS;
  component_r27; a descriptor-routed component row keeps its DESCRIPTIVE reading; the species-leg label is kept,
  with a note); the form rows run in the phase-2 process pool (§4 memory: the WP3 run computed them in the parent);
  pace.py's §14 pause-and-report at every checkpoint (EXIT_PAUSED; --resume-after-pause "<decision>"; the pinned
  block estimates of run_manifests/reprice_wp4.json, their hash in the launch record; --block-estimates for dev runs);
  PASS_MODULES preloaded before the launch so L11's code hash covers wp3_repro / repro (code_coverage asserts it at the
  end of a pass); the >= 2-donor parcel rule is recorded as '>= 2 donors'.
- Hand-off (ORCHESTRATOR DECISION, 2026-10-02; RUN_PLAN §7 :1089 "every plant runs through the production code path
  (a1_audit.run, flag --plant)"): `--plant <id>` with id in a1_audit.plants.driver.ORDER (the WP2 battery, lettered
  P3a / P3b included: accepted for this hand-off only) is handed to the plants driver's main (plant, --commit, --jobs,
  --dev, --out; --estimate forwarded) and its exit code returned; a run.py-only option given with such a plant is
  refused. Row-keyed plants (P2; any other P<n>) stay on this module's --plant path (plants_handoff, HANDOFF_RULE).
"""
from __future__ import annotations

import os

_THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
THREAD_ENV_BEFORE = {k: os.environ.get(k) for k in _THREAD_VARS}
for _k in _THREAD_VARS:  # RUN_PLAN §4 :381 "Runs use 20 jobs with OMP_NUM_THREADS=1" (forced, recorded)
    os.environ[_k] = "1"
os.environ["PYTHONUNBUFFERED"] = "1"

import argparse  # noqa: E402
import datetime as _dt  # noqa: E402
import functools  # noqa: E402
import hashlib  # noqa: E402
import importlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
import tracemalloc  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import a3_port as A3  # noqa: E402  (puts src/ on sys.path; e3_plants imported here)
from . import adapters as AD  # noqa: E402
from . import descriptors as DS  # noqa: E402
from . import gates as GT  # noqa: E402
from . import launch as LA  # noqa: E402
from . import loader as LD  # noqa: E402
from . import plant_mode as PM  # noqa: E402
from . import seeds as SD  # noqa: E402
from . import verdict as V  # noqa: E402
from . import pace as PACE  # noqa: E402
from asdg.genesets import MIN_SET  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
DRIVER = "a1_audit.run"
RESULTS_REL = "arcs/audit/results/a1_run"
PLANTS_REL = "arcs/audit/run_manifests/plants"      # R18 :846-847
LAUNCH_REL = "arcs/audit/run_manifests/launch"      # R18 :846-847
CK_REAL_REL = "artifacts/audit/a1_run"
CK_PLANT_REL = "artifacts/audit/a1_plants"
FORBIDDEN_OUT = ("arcs/audit/results", "arcs/audit/run_manifests")
PASSES = ("verdict", "descriptor", "sensitivity")
GATE_ARGS = ("none", "G1", "G2")
GATE_DIR = {"none": "ungated", "G1": "G1", "G2": "G2"}
JOB_LIMIT_BYTES = 2_500_000_000  # §4 :382-385 "a job above 2.5 GB is a defect" (15,633 x 20,000 float64 = 2.5e9 B)

AUDIT_K = {"site": 10000, "species": 10000, "permutation": 10000, "sets": 10000, "surr": 10000, "j1_sets": 1000}
PLANT_K = {"site": 500, "species": 200, "permutation": 500, "sets": 200, "surr": 500, "j1_sets": 100}
# C4: a plant's registered counts where RUN_PLAN §7 pins them (an explicit override of PLANT_K, recorded per header)
PLANT_K_OVERRIDES = {"P12": {"permutation": 10000}}   # RUN_PLAN.md:1139 P12 "refit on 10,000 permutations"
PLANT_K_OVERRIDE_SOURCES = {"P12": "RUN_PLAN.md:1139 (P12: 'refit on 10,000 permutations')"}
RUN_IDENTITY_FIELDS = ("run_commit", "code_hash", "K", "g6l_mode", "sources", "seed_view")   # C5
RERUN_RULE = ("RUN_PLAN §17 (3)-(4): every completed row whose computation passes through a changed statistic-path "
              "function is rerun; both versions are reported (the first run's rows stay where they were written)")

# ---- fixed vocabulary ------------------------------------------------------------------------------------------
NOT_RUN_WP3 = "not run (WP3 loader pending)"
NOT_RUN_CONDITIONAL = "not run (conditional: the carrier test result is pending, WP5)"
NOT_RUN_CLASS = "not run (analysis class conditional on a carrier: pending, WP5)"
NOT_RUN_VERDICT_ABSENT = "not run (the verdict pass result of this row is absent or has no verdict)"
REFUSED_VERDICT_IDENTITY = "refused: the verdict pass result of this row belongs to another run (differs in: %s; C5)"
NO_DESCRIPTOR_COMPONENT = "no descriptor legs (component form; RUN_PLAN §4 legs table)"
PARCELS_UNCHANGED = "parcel set unchanged (the primary result stands; R11)"
REFUSED_STATUS = "refused: status form not pinned for the runner"
REFUSED_T = "refused: the T column matches no registered adapter of its claim_form"
REFUSED_DIRECTION = "refused: direction form not pinned for the runner"
REFUSED_CLASS = "refused: analysis class not pinned for the runner"
REFUSED_NO_SET = "refused: a set form without a built set"
REFUSED_INDEX_UNDETERMINED = ("refused: cell index UNDETERMINED (fixed when (and if) the cells are enumerated; "
                              "claims_register.md:1078-1080)")
REFUSED_INDEX_OTHER = "refused: map / cell index form not pinned for the runner"
REFUSED_SIGNED_ROWS = "refused: signed-weight status outside RUN_PLAN §4's rows 103-117"
REFUSED_RESLIM_ROWS = "refused: by-construction resolution-limited status outside claims_register.md:1462-1464's rows"
PLANT_CLASS_NOTE = "analysis class conditional: taken as its first named option, %s (plant view, U2)"
REFUSED_TWO_COHORT_COMPONENT = "refused: two-cohort component claim (no frozen two-cohort component reading)"

ROUTE_NO = {"deferred": "no statistic: deferred", "lt5": "no statistic: not testable (< 5)",
            "na": "no statistic: not auditable", "ntas": "no statistic: not testable as stated (no registered T form)",
            "oos": "no statistic: out of scope"}
STUBS: dict = {}       # WP2 (§18) replaced the four stubs (signed-weight P15, gene-set-only R10, MOR-T R21, BENK / PARK R28)
ROUTE_STUB: dict = {}
# WP2 form routes (a1_audit/forms.py)
ROUTE_FORM = {"signed-weight": "descriptor: signed-weight rho (P15)", "liu": "descriptor: gene-set-only (R10)"}
FORM_NAMES = {"signed-weight": "signed-weight", "liu": "gene-set-only"}
ROUTE_NOTE_R21 = "descriptor: MOR-T, R21"
ROUTE_NOTE_R28 = "descriptor: BENK-C2 / PARK-C5 proxy, R28"
NOT_RUN_READING = "not run (%s)"
REFUSED_FORM_TWO_COHORT = "refused: two-cohort index on a signed-weight / gene-set-only row (no frozen reading)"
FORM_NO_PASS = {
    ("signed-weight", "sensitivity"): "no statistic: signed-weight descriptor without a verdict (R11 re-runs the verdict "
                                      "legs of claims with a verdict; forms.py U-F2)",
    ("liu", "verdict"): "no statistic: gene-set-only (R10) has no verdict legs; its G1-G5 run in the descriptor pass "
                        "(RUN_PLAN §4 :377; forms.py U-F2)",
    ("liu", "sensitivity"): "no statistic: gene-set-only (R10): no parcels and no verdict (R11; forms.py U-F2)",
}

SIGNED_WEIGHT_STATUS = "not testable as stated: signed-weight set score"
SIGNED_WEIGHT_ROWS = frozenset(range(103, 118))           # RUN_PLAN §4 :357-360 (TSV rows 103-117)
RESLIM_STATUS = "resolution-limited: by construction"
RESLIM_ROWS = frozenset((92, 94, 96, 98, 100, 102))       # RUN_PLAN R9 :618-619
KNOWN_CLASSES = ("dk-ctx", "V-AAL", "V-DK", "V-DK-subcortex", "MIST64")
CLASS_CONDITIONAL_PREFIX = "dk-ctx | V-DK (conditional:"
FULL_FORMS = ("set-vs-map", "decoded-list", "PLS-enrichment")

SIG_SET_VS_MAP = ("T = Pearson r(y, set score)", "T = Pearson r(y, unweighted set score)")
SIG_DECODED = ("T = mean over S of the per-gene Pearson r(y, gene expression)", "the signed decoded-list T")
SIG_PLS = ("T = mean PLS1 weight of S's genes", "signed T (mean PLS1 weight of S")
SIG_SIGNED_WEIGHT = "signed-weight"
SIG_SELECTED = "selected list"
SIG_FIXED = "for a fixed component"
SIG_PLSR_CUM2 = "T = cumulative R\u00b2 of two components with prereg \u00a74.7's PLSRegression(2, scale=True)"
SIG_PLS1_R2 = "T = R\u00b2 of PLS1 (cascade.pls1)"
SIG_PLSR_K3 = "T = R\u00b2 of PLS component 3 (prereg \u00a74.7 PLSRegression(n_components=3, scale=True)"
SIG_TAIL_RANK = "tail-rank statistic"
SIG_RLM = "robust regression"

IDX_NA_T = "n/a: no registered T (never computed; no seed)"
IDX_TWO_COHORT = "0 = ABIDE I; 1 = ABIDE II (\u00a71.9)"
IDX_UNDETERMINED = re.compile(r"\AUNDETERMINED: 1 \.\.\. (n|[1-9][0-9]*), one per cell in the defining table's order, "
                              r"fixed when \(and if\) the cells are enumerated under the gate \(\u00a71\.9\)\Z")
IDX_FORMS = ("integer", "two-cohort (0 = ABIDE I; 1 = ABIDE II)", "n/a: no registered T",
             "UNDETERMINED (one per cell, fixed when enumerated)", "other (not pinned for the runner)")


class SourceUnavailable(RuntimeError):
    """A source (map, set, context, ...) has no implementation for this row (real loaders are WP3)."""

    def __init__(self, status: str, what: str):
        super().__init__(f"{status}: {what}")
        self.status, self.what = status, what


class NotTestableAtUse(RuntimeError):
    def __init__(self, status: str):
        super().__init__(status)
        self.status = status


class RunRefused(SystemExit):
    pass


# ================================================================================================================
# small helpers
# ================================================================================================================
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_json(o) -> str:
    return sha256_bytes(json.dumps(A3.jsonable(o), sort_keys=True, separators=(",", ":")).encode("utf-8"))


def arr_sha(*arrays) -> str:
    h = hashlib.sha256()
    for a in arrays:
        a = np.ascontiguousarray(np.asarray(a))
        h.update(str(a.dtype).encode("ascii") + str(a.shape).encode("ascii"))
        h.update(a.tobytes())
    return h.hexdigest()


def ascii_line(s: str) -> str:
    return s.encode("ascii", "replace").decode("ascii")


def int_dir_keys(o):
    """JSON turned the direction keys {1, -1} into {'1', '-1'}: turn them back (only dicts whose keys are exactly
    those two; every such dict in a leg payload is a direction dict)."""
    if isinstance(o, dict):
        if set(o.keys()) == {"1", "-1"}:
            return {1: int_dir_keys(o["1"]), -1: int_dir_keys(o["-1"])}
        return {k: int_dir_keys(v) for k, v in o.items()}
    if isinstance(o, list):
        return [int_dir_keys(v) for v in o]
    return o


def write_json_atomic(path: Path, obj) -> str:
    """UTF-8 / LF JSON, written to a tmp file and os.replace'd, then read back and compared (rule 8)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(A3.jsonable(obj), indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    back = path.read_bytes()
    if back != data or json.loads(back.decode("utf-8")) != json.loads(data.decode("utf-8")):
        raise RuntimeError(f"read-back of {path.name} differs from what was written")
    return sha256_bytes(back)


def stream_fingerprint(ss: np.random.SeedSequence) -> str:
    """sha256 of the first 16 int64 draws of default_rng(ss) (P2: the G3 stream vs leg 3's)."""
    return sha256_bytes(np.random.default_rng(ss).integers(0, 2 ** 62, size=16, dtype=np.int64).tobytes())


# ================================================================================================================
# TSV forms: direction, map / cell indices (claims_register.md §1.9 :1076-1082)
# ================================================================================================================
def parse_direction(text: str):
    """(two_sided, registered_direction) or None (refused). U10."""
    if text.startswith("two-sided"):
        return True, None
    if text.startswith("+ ("):
        return False, 1
    if text.startswith("\u2212 ("):
        return False, -1
    return None


def index_form(text: str) -> str:
    if LD.int_or_none(text) is not None:
        return IDX_FORMS[0]
    if text == IDX_TWO_COHORT:
        return IDX_FORMS[1]
    if text == IDX_NA_T:
        return IDX_FORMS[2]
    if IDX_UNDETERMINED.match(text):
        return IDX_FORMS[3]
    return IDX_FORMS[4]


def parse_indices(row) -> dict:
    """{maps, cell, two_cohort, refusal, forms}. Map: integer -> [it]; IDX_TWO_COHORT -> [0, 1]; n/a -> no statistic;
    else refused. Cell: integer; UNDETERMINED -> refused until the build records the index; n/a; else refused."""
    mt, ct = row["map_index"], row["cell_index"]
    mf, cf = index_form(mt), index_form(ct)
    out = dict(forms={"map": mf, "cell": cf}, maps=None, cell=None, two_cohort=False, refusal=None, no_t=False)
    if mf == IDX_FORMS[2] or cf == IDX_FORMS[2]:
        out["no_t"] = True
        return out
    if mf == IDX_FORMS[0]:
        out["maps"] = [LD.int_or_none(mt)]
    elif mf == IDX_FORMS[1]:
        out["maps"], out["two_cohort"] = [0, 1], True
    else:
        out["refusal"] = REFUSED_INDEX_OTHER
        return out
    if cf == IDX_FORMS[0]:
        out["cell"] = LD.int_or_none(ct)
    elif cf == IDX_FORMS[3]:
        out["refusal"] = REFUSED_INDEX_UNDETERMINED
    else:
        out["refusal"] = REFUSED_INDEX_OTHER
    return out


# ================================================================================================================
# dispatch (RUN_PLAN §4 :353-363)
# ================================================================================================================
def view_status(row, open_gates, plant_view: bool) -> tuple[str, str]:
    if plant_view and row.gated is not None:
        return row.gated[1], f"plant view: gate {row.gated[0]} taken as open (synthetic material only; U2)"
    og = sorted(open_gates)
    return LD.effective_status(row, open_gates), "launch view: open gates " + (", ".join(og) if og else "none")


def _head(row, status: str, view: str) -> dict:
    return dict(row=row.row, target_no=row.target_no, cell_id=row.cell_id, claim_form=row.claim_form, gate=row.gate,
                status_tsv=row.status, status_effective=status, view=view, route=None, kind=None,
                status_written=None, stub=None, form=None, component=None, descriptor=False, label=None,
                t_abs=False, depletion=False, two_sided=None, registered_direction=None, maps=None, cell_index=None,
                two_cohort=False, analysis_class=row["analysis_class"], preconditions=[],
                by_construction_label=None, has_set=not row["set_id"].startswith("none"), set_id=row["set_id"],
                index_forms={"map": index_form(row["map_index"]), "cell": index_form(row["cell_index"])},
                in_m=row.m_membership)


def _done(p: dict, route: str, kind: str, status: str | None = None, **kw) -> dict:
    p.update(route=route, kind=kind, status_written=status, **kw)
    return p


def _component_spec(T: str) -> dict | None:
    if SIG_FIXED in T:
        return dict(kind="fixed")
    if SIG_PLSR_CUM2 in T:
        return dict(kind="plsr", n_components=2, cumulative=True)
    if SIG_PLS1_R2 in T:
        return dict(kind="pls1-r2")
    if SIG_PLSR_K3 in T:
        return dict(kind="plsr", n_components=3, component=3)
    return None


def _by_form(p: dict, row, s: str) -> dict:
    form, T = row.claim_form, row["T"]
    p["descriptor"] = bool(p["descriptor"] or T.startswith("descriptor") or "(descriptor" in s)
    if s.startswith("conditional") or "conditional on the carrier" in s:
        p["preconditions"].append("carrier")
    if form == "set-vs-map":
        if SIG_SIGNED_WEIGHT in T:  # U9
            return _form_plan(p, row, "signed-weight", _forms().SW_LABEL_CELL,
                              "by the T column ('signed-weight form'); U9")
        if not any(sig in T for sig in SIG_SET_VS_MAP):
            return _done(p, "refused", "refused", REFUSED_T)
    elif form == "decoded-list":
        if not any(sig in T for sig in SIG_DECODED):
            return _done(p, "refused", "refused", REFUSED_T)
    elif form == "PLS-enrichment":
        if not any(sig in T for sig in SIG_PLS):
            return _done(p, "refused", "refused", REFUSED_T)
    elif form == "component":
        spec = dict(kind="selected") if SIG_SELECTED in T else _component_spec(T)  # R34: adapters.SelectedList
        if spec is None:
            return _done(p, "refused", "refused", REFUSED_T)
        spec["genes_from_set"] = bool(p["has_set"]) and spec["kind"] in ("pls1-r2", "plsr")  # U8
        p["component"] = spec
    elif form == "other":
        FM = _forms()
        if SIG_TAIL_RANK in T:   # R21 (RUN_PLAN.md:873-878): the decoded-list T with all its legs; no T_abs
            form = "decoded-list"
            p.update(descriptor=True, label=FM.R21_LABEL, reading="R21", route_note=ROUTE_NOTE_R21)
        elif SIG_RLM in T:       # R28 (:1025-1027): the Gandal ASD-down proxy, decoded-list T, direction as the TSV
            form = "decoded-list"
            p.update(descriptor=True, label=FM.R28_LABEL, reading="R28", route_note=ROUTE_NOTE_R28, rlm=True)
            pdir = FM.parse_proxy_direction(row["direction"])
            if pdir is None:
                return _done(p, "refused", "refused", REFUSED_DIRECTION)
            p["_direction"] = (False, pdir)
        else:
            return _done(p, "refused", "refused", REFUSED_T)
    else:
        return _done(p, "refused", "refused", REFUSED_T)
    p["form"] = form
    p["t_abs"] = bool("T_abs" in T and form in ("decoded-list", "PLS-enrichment"))   # U7
    p["depletion"] = bool(p["t_abs"] and "T_abs lower tail" in row["direction"])
    d = p.pop("_direction", None) or parse_direction(row["direction"])   # R28: the proxy's direction
    if d is None:
        return _done(p, "refused", "refused", REFUSED_DIRECTION)
    p["two_sided"], p["registered_direction"] = d
    cls = row["analysis_class"]
    if cls.startswith(CLASS_CONDITIONAL_PREFIX):
        p["preconditions"].append("class")
    elif cls not in KNOWN_CLASSES:
        return _done(p, "refused", "refused", REFUSED_CLASS)
    ix = parse_indices(row)
    if ix["no_t"]:
        return _done(p, ROUTE_NO["ntas"], "no statistic", s)
    if ix["refusal"]:
        return _done(p, "refused", "refused", ix["refusal"])
    if form in FULL_FORMS and not p["has_set"]:
        return _done(p, "refused", "refused", REFUSED_NO_SET)
    if ix["two_cohort"] and form == "component":
        return _done(p, "refused", "refused", REFUSED_TWO_COHORT_COMPONENT)
    p.update(maps=ix["maps"], cell_index=ix["cell"], two_cohort=ix["two_cohort"])
    kind = form if form != "component" else "component (%s)" % (
        "selected list" if p["component"]["kind"] == "selected" else p["component"]["kind"])
    if p.get("route_note"):   # R21 / R28 (WP2)
        kind += f" ({p['route_note']})"
    return _done(p, f"verdict: {kind}", "compute")


def classify(row, open_gates=frozenset(), *, plant_view: bool = False) -> dict:
    """The row's route under the view (no statistic, nothing loaded). See the module docstring."""
    s, view = view_status(row, open_gates, plant_view)
    p = _head(row, s, view)
    T = row["T"]
    if s.startswith("deferred"):
        return _done(p, ROUTE_NO["deferred"], "no statistic", s)
    if s.startswith("not testable (< 5)"):
        return _done(p, ROUTE_NO["lt5"], "no statistic", s)
    if s.startswith("not auditable"):
        return _done(p, ROUTE_NO["na"], "no statistic", s)
    if s.startswith("out of scope"):  # RUN_PLAN §4 :361-363 (no TSV row carries it: out-of-scope claims are not registered)
        return _done(p, ROUTE_NO["oos"], "no statistic", s)
    if s.startswith(SIGNED_WEIGHT_STATUS):
        if row.row not in SIGNED_WEIGHT_ROWS:
            return _done(p, "refused", "refused", REFUSED_SIGNED_ROWS)
        return _form_plan(p, row, "signed-weight", _forms().SW_LABEL_CLAIM, "by the status (RUN_PLAN §4 :357-360)")
    if s.startswith("not testable as stated"):
        if T.startswith("none") or row["map_index"] == IDX_NA_T:
            return _done(p, ROUTE_NO["ntas"], "no statistic", s)
        p["descriptor"], p["label"] = True, "descriptor (not testable as stated)"
        return _by_form(p, row, s)
    if s.startswith("no calibrated test"):
        if row.claim_form != "gene-set-only":
            return _done(p, "refused", "refused", REFUSED_STATUS)
        return _form_plan(p, row, "liu", _forms().LIU_READING, "by the claim form and status (RUN_PLAN §4 :355)")
    if s.startswith(RESLIM_STATUS):
        if row.row not in RESLIM_ROWS:
            return _done(p, "refused", "refused", REFUSED_RESLIM_ROWS)
        p["by_construction_label"] = "resolution-limited"
        return _by_form(p, row, s)
    if s.startswith("auditable") or s.startswith("conditional"):
        return _by_form(p, row, s)
    return _done(p, "refused", "refused", REFUSED_STATUS)


def run_stub(name: str, plan: dict):
    """Every stub raises its named NotImplementedError (the WP2 item)."""
    raise NotImplementedError(STUBS[name])


# ================================================================================================================
# WP2 form routes (RUN_PLAN §4 :355-360; §18 WP2): the adapters are a1_audit/forms.py
# ================================================================================================================
def _forms():
    from . import forms
    return forms


def _form_plan(p: dict, row, name: str, label: str, detail: str) -> dict:
    """A signed-weight (P15) or gene-set-only (R10) row: direction, class, indices and set read as for every form (fail
    closed); kind 'form' (run by _run_form_row; probed by _probe_form)."""
    d = parse_direction(row["direction"])
    if d is None:
        return _done(p, "refused", "refused", REFUSED_DIRECTION)
    cls = row["analysis_class"]
    if name == "signed-weight" and cls not in KNOWN_CLASSES:
        return _done(p, "refused", "refused", REFUSED_CLASS)
    if name == "liu":
        if cls != "none":   # TSV rows 471-477: "analysis class 'none': no class universe of its own"
            return _done(p, "refused", "refused", REFUSED_CLASS)
        try:
            p["liu_spec"] = _forms().liu_spec(row.cell_id, row["T"])
        except LookupError:
            return _done(p, "refused", "refused", REFUSED_T)
    ix = parse_indices(row)
    if ix["no_t"]:
        return _done(p, ROUTE_NO["ntas"], "no statistic", p["status_effective"])
    if ix["refusal"]:
        return _done(p, "refused", "refused", ix["refusal"])
    if ix["two_cohort"]:
        return _done(p, "refused", "refused", REFUSED_FORM_TWO_COHORT)
    if not p["has_set"]:
        return _done(p, "refused", "refused", REFUSED_NO_SET)
    p.update(form=FORM_NAMES[name], form_name=name, maps=ix["maps"], cell_index=ix["cell"], two_sided=d[0],
             registered_direction=d[1], label=label)
    if name == "signed-weight":   # RUN_PLAN_amend_2 R41: the ±.05 comparator T_S is checked against (TSV reproduction)
        p["sw_published"] = _forms().sw_published_rho(p["row"], row["reproduction"])
    p["descriptor"] = bool(p["descriptor"] or name == "signed-weight" or row["T"].startswith("descriptor")
                           or "descriptor cell" in p["status_effective"])
    return _done(p, ROUTE_FORM[name], "form", detail=detail)


_FORM_SOURCE_WHAT = {
    "second_map": "the paper's weighted GEDAR map (eda33ab; C19-C24 and the MDD-DEG cells rebuilt by R17): WP3",
    "gene_weights": "S's signed weights (TWAS z / logFC) from the gated set build: WP3",
    "liu_inputs": "BrainSpan expression_matrix.csv with its sample metadata, or the AHBA per-sample abagen assignment "
                  "(R10; env/venv_ref): WP3",
    "rlm_inputs": "per-gene decoding t (R31 per-donor recipe / NeuroVault decoder) and Gandal 2018 Table S1 DGE "
                  "covariates (R28 fetch): WP5",
}


def _src(sources, name: str, plan: dict, *a):
    """A WP2 source: the sources' own method if it has one (a WP3 / WP5 loader adds it); synthetic sources use the
    forms.py providers; anything else is not yet implemented (SourceUnavailable, 'not run (WP3 loader pending)')."""
    fn = getattr(sources, name, None)
    if callable(fn):
        return fn(plan, *a)
    if getattr(sources, "synthetic", False):
        FM = _forms()
        syn = {"second_map": FM.synthetic_second_map, "gene_weights": FM.synthetic_gene_weights,
               "liu_inputs": FM.synthetic_liu_inputs, "rlm_inputs": FM.synthetic_rlm_inputs}
        return syn[name](sources, plan, *a)
    raise SourceUnavailable(NOT_RUN_WP3, _FORM_SOURCE_WHAT[name])


def _probe_form(p: dict, plant_view: bool, sources) -> dict:
    """Dry dispatch of a form row: preconditions, then its computing pass's sources (signed-weight: the class context,
    the map, the paper's map; Liu: its per-sample data)."""
    st, _ = check_preconditions(p, plant_view)
    if st is not None:
        return dict(outcome="refused" if st.startswith("refused") else "not run", status=st)
    try:
        if p["form_name"] == "signed-weight":
            sources.context(p["analysis_class"])
            sources.map(p, p["maps"][0])
            _src(sources, "second_map", p, p["maps"][0])
            _src(sources, "gene_weights", p)   # the descriptor pass's S weights (RUN_PLAN_amend_2 R41)
        else:
            _src(sources, "liu_inputs", p)
    except SourceUnavailable as e:
        return dict(outcome="not run", status=e.status)
    return dict(outcome="would compute", status="sources available")


_FORM_INPUTS: dict = {}


def _form_inputs(plan: dict, sources, pass_: str) -> tuple[dict, dict]:
    """(inputs, input hashes) of a form row for its computing pass (cached per process). signed-weight: the class
    context restricted to the analysis parcels (§4: finite y and >= 1 AHBA sample), y and the paper's map b on them;
    in the descriptor pass also S's genes and signed weights and the class's BrainSpan trajectories (G5) (RUN_PLAN_amend_2
    R41); Liu (descriptor pass): the source's per-sample data (ids dropped by forms.liu_prepare)."""
    key = (json.dumps(sources.spec(), sort_keys=True), plan["row"], pass_)
    if key in _FORM_INPUTS:
        return _FORM_INPUTS[key]
    if len(_FORM_INPUTS) > 8:
        _FORM_INPUTS.clear()
    if plan["form_name"] == "signed-weight":
        cls, mi = plan["analysis_class"], plan["maps"][0]
        base, counts, ctx_sha = sources.context(cls)
        y, ids, mcls, mh = sources.map(plan, mi)
        if mcls != cls:
            raise RuntimeError(f"map source returned class {mcls}, the row's class is {cls}")
        b, bids, bsha = _src(sources, "second_map", plan, mi)
        ids, bids = A3.as_parcel_ids(ids, "map"), A3.as_parcel_ids(bids, "second map")
        ap = AD.analysis_parcels(y, counts, parcel_ids=ids, min_count=PARCEL_RULES["primary"],
                                 class_parcel_ids=base.parcel_ids)   # C8 (as prepare)
        keep = ap["parcel_ids"]
        bpos = {int(q): k for k, q in enumerate(bids.tolist())}
        if not set(keep) <= set(bpos):
            raise RuntimeError("the paper's map lacks an analysis parcel (re-parcellation is the loader's job)")
        pos = {int(q): k for k, q in enumerate(ids.tolist())}
        inp = dict(ctx=base.restrict(keep), y=np.asarray(y, float)[[pos[q] for q in keep]],
                   b=np.asarray(b, float)[[bpos[q] for q in keep]], parcel_ids=keep, analysis_parcels=ap)
        hashes = {"context": ctx_sha, **mh, f"second_map[{int(mi)}]": bsha}
        if pass_ == "descriptor":   # RUN_PLAN_amend_2 R41: S's signed weights; G5's trajectories
            genes, w, wsha = _src(sources, "gene_weights", plan)
            traj, tsha = sources.trajectories(cls)
            inp.update(genes=list(genes), weights=np.asarray(w, dtype=float), traj=traj)
            hashes.update(gene_weights=wsha, trajectories=tsha)
    else:
        inp = _src(sources, "liu_inputs", plan)
        hashes = dict(sorted((inp.get("hashes") or {}).items()))
    _FORM_INPUTS[key] = (inp, hashes)
    return inp, hashes


def form_task(key: str, kw: dict):
    """run_pending's fn for one form row (module level, so loky pickles it by reference)."""
    t0 = time.perf_counter()
    started = LA.now_iso()
    with MemProbe() as mp:
        plan, K, FM = kw["plan"], kw["K"], _forms()
        inp, hashes = _form_inputs(plan, sources_from_spec(kw["sources"]), kw["pass_"])
        if hashes != kw["expect_hashes"]:
            raise RuntimeError(f"{key}: the worker loaded other inputs than the parent saw")
        sc = seeds_of(plan, plan["maps"][0])
        try:
            if plan["form_name"] == "signed-weight" and kw["pass_"] == "verdict":
                res = FM.signed_weight_site(inp["ctx"], inp["y"], inp["b"], parcel_ids=inp["parcel_ids"],
                                            K=int(K["site"]), seed_of=sc["seed_of"], two_sided=bool(plan["two_sided"]),
                                            registered_direction=plan["registered_direction"], chunk=AD.CHUNK_MAX)
            elif plan["form_name"] == "signed-weight":   # descriptor pass: RUN_PLAN_amend_2 R41
                res = FM.signed_weight_descriptor(inp["ctx"], inp["y"], inp["b"], inp["genes"], inp["weights"],
                                                  parcel_ids=inp["parcel_ids"], traj=inp["traj"],
                                                  seed_of=sc["seed_of"], g3_seed=sc["g3_seed"],
                                                  K_sets=int(K["sets"]), K_surr=int(K["surr"]),
                                                  K_j1_sets=int(K["j1_sets"]), two_sided=bool(plan["two_sided"]),
                                                  registered_direction=plan["registered_direction"],
                                                  published=plan.get("sw_published"), chunk=AD.CHUNK_MAX)
            else:
                res = FM.liu_compute(plan["liu_spec"], inp, K=int(K["sets"]), seed_of=sc["seed_of"],
                                     g3_seed=sc["g3_seed"], two_sided=bool(plan["two_sided"]),
                                     registered_direction=plan["registered_direction"])
            payload = dict(outcome="computed", result=res)
        except FM.FormNotTestable as e:
            payload = dict(outcome="no statistic", status=e.status)
            if e.detail:   # counts only (RUN_PLAN_amend_2 R42 (d): fail closed 'with the count')
                payload["status_detail"] = dict(e.detail)
        except NotImplementedError as e:   # a reading no frozen text pins (named in the message)
            payload = dict(outcome="not run", status=NOT_RUN_READING % e)
    payload = A3.jsonable(payload)
    payload["_meta"] = dict(started=started, finished=LA.now_iso(), seconds=round(time.perf_counter() - t0, 3),
                            memory=mp.result, pid=os.getpid())
    return key, payload


def _form_job(run: "Run", p: dict, note):
    """One signed-weight / gene-set-only row in this pass (forms.py U-F2): signed-weight - the verdict pass computes T
    and the site leg on rho; the descriptor pass computes T_S, the gene legs with S's weights carried over and the
    registered outcome (RUN_PLAN_amend_2 R41; forms.signed_weight_descriptor); no sensitivity pass. Liu - the
    descriptor pass computes T and G1-G5; no verdict or sensitivity pass. One checkpoint per row x pass (A3 Checkpoints
    under <ck>/forms, resumable). Records carry survives = False (descriptive p's). In a plant case the row draws from
    the plant case's keys (WP2r: seeds.plant_leg_seed through seed_record_for / seeds_of; run.plant_class_word), as
    every other row of the case does.
    Returns the row file's sha256 when the row is written without a statistic, else the row's job (pace.Job plus what
    _form_finish needs). Pre-WP4 (RUN_PLAN §4 memory; §14): the job runs in the pass's process pool with the other
    tasks (the WP3 run ran each form row alone, in the parent process, whose own peak working set was then the job
    measure); the computation, its inputs and its seeds are unchanged."""
    name = p["form_name"]
    st, notes = check_preconditions(p, run.plant_view)
    if st is not None:
        out = "refused" if st.startswith("refused") else "not run"
        note(out)
        return run.write_row(p, out, st)
    why = FORM_NO_PASS.get((name, run.pass_))
    if why is not None:
        note("no statistic")
        return run.write_row(p, "no statistic", why)
    if run.seed_view is not None:   # WP2r: a plant case's leg keys (real runs and P2: the claim keys)
        p = dict(p, seed_view=dict(run.seed_view))
    try:
        inp, hashes = _form_inputs(p, run.sources, run.pass_)
    except SourceUnavailable as e:
        note("not run")
        return run.write_row(p, "not run", e.status, extra={"source_detail": e.what})
    light = {k: inp.get(k) for k in ("parcel_ids", "analysis_parcels", "loader_record")}   # the parent keeps no matrix
    _FORM_INPUTS.pop((json.dumps(run.sources.spec(), sort_keys=True), p["row"], run.pass_), None)
    spec = run.sources.spec()
    store = run.form_store()
    sw_site = name == "signed-weight" and run.pass_ == "verdict"
    gene_legs = {"G1": "rng", "G2": "rng", "G4": "rng", "G5": "rng"}
    uses = {"S1c": "int", "S2c": "int"} if sw_site else gene_legs
    sr = seed_record_for(p, p["maps"][0], uses, g3=not sw_site, j1=(name == "signed-weight" and not sw_site))
    key = f"r{p['row']:04d}_m{p['maps'][0]}_form"
    expect = dict(form=name, seeds=sr, inputs=hashes, K=run.K, pass_name=run.pass_)
    kw = dict(plan=p, sources=spec, pass_=run.pass_, K=run.K, expect_hashes=hashes)
    return dict(job=PACE.Job(key, expect, kw, store, form_task), plan=p, sr=sr, hashes=hashes, light=light,
                notes=notes, sw_site=sw_site)


def _form_finish(run: "Run", fj: dict, payload: dict, note) -> str:
    """The row record of a computed form job (its checkpointed payload)."""
    p, sr, hashes, inp, notes, sw_site = fj["plan"], fj["sr"], fj["hashes"], fj["light"], fj["notes"], fj["sw_site"]
    name = p["form_name"]
    got = dict(payload)
    meta = got.pop("_meta")
    if got["outcome"] != "computed":
        note(got["outcome"])
        extra = {"status_detail": got["status_detail"]} if got.get("status_detail") else None
        return run.write_row(p, got["outcome"], got["status"], extra=extra)
    res = int_dir_keys(got["result"])
    if sw_site:
        ints = {d["leg"]: d.get("seed_int") for d in sr["legs"]}
        for leg in ("S1c", "S2c"):  # the integer seeds used are the ones recorded (R7)
            if int(res["site"]["legs"][leg]["seed"]) != ints[leg]:
                raise RuntimeError(f"row {p['row']}: {leg} seed used != recorded")
    elif name == "signed-weight" and isinstance((res.get("gene_legs") or {}).get("J1"), dict):
        j1 = res["gene_legs"]["J1"]["seeds"]   # J1's integer seeds drawn in R7's order are the ones recorded
        if (int(j1["S1c"]), int(j1["S2c"])) != (int(sr["J1"]["S1c_seed"]), int(sr["J1"]["S2c_seed"])):
            raise RuntimeError(f"row {p['row']}: J1 seeds used != recorded")
    if name == "signed-weight":
        inputs = dict(hashes=hashes, parcel_ids={str(p["maps"][0]): [int(i) for i in inp["parcel_ids"]]},
                      analysis_parcels={str(p["maps"][0]): dict(inp["analysis_parcels"])},
                      analysis_class=p["analysis_class"], rule="primary")
    else:
        inputs = dict(hashes=hashes, set=res["set"], U_stat=res["U_stat"], analysis_class=p["analysis_class"],
                      loader=inp.get("loader_record"))   # WP3: the loader's mapping / sample counts
    res.update(survives=False, survival_rule="descriptive p's only, never a survival (a descriptor / 'no calibrated "
                                             "test' row; RUN_PLAN R10 :650; claims_register.md:195-196, :1469-1473)")
    seeds = {"row": p["row"], "target_number": p["target_no"], "per_map": [sr]}
    mem = dict(meta["memory"], seconds=meta["seconds"])
    if mem.get("defect"):
        run.log(f"DEFECT row {p['row']}: a job above 2.5 GB (RUN_PLAN §4 memory)")
    note("computed")
    sha = run.write_row(p, "computed", p["status_effective"], result=res, inputs=inputs, seeds=seeds,
                        times=(meta["started"], meta["finished"]), memory=mem,
                        extra={"notes": notes} if notes else None)
    run.log(f"row {p['row']} ({p['route']}) written")
    if name == "liu" and run.pass_ == "descriptor":
        _write_repro(run, p, res)      # WP3: R10 / R42's 4.1 check (T4 / T5) or its pending status
    return sha


def _write_rlm(run: "Run", p: dict) -> str:
    """R28's RLM descriptor of a BENK-C2 / PARK-C5 row (verdict pass), written as row_<n>_rlm.json beside the row's
    record (forms.py U-F6); 'not run (...)' while its inputs are pending (WP5)."""
    FM = _forms()
    try:
        rec = FM.rlm_record(p["cell_id"], _src(run.sources, "rlm_inputs", p))
    except SourceUnavailable as e:
        rec = dict(status=e.status, what=e.what, reading=FM.R28_RLM_READING)
    doc = dict(run.header(), what="R28 RLM descriptor of one row (RUN_PLAN R28 :996-998; forms.py U-F6)", row=p["row"],
               target_number=p["target_no"], cell_id=p["cell_id"], label=p["label"], route=p["route"], rlm=rec,
               provenance=run.provenance())
    sha = write_json_atomic(run.results_dir / f"row_{p['row']:04d}_rlm.json", doc)
    run.log(f"row {p['row']} R28 RLM: {rec['status']}")
    return sha


def _wp3_sources(out_root):
    """WP3: a real run's sources - the ungated loaders on the production layout. Fix round 1 (c): the phase-2
    records and manifest are read from THIS tree (REPO): in a claim-bearing run that is the pinned worktree, which L11
    holds clean at the run commit, so the loaders read the manifest as committed at the run commit (the orchestrator
    commits phase 2's records before the run commit); its sha256 enters every row's input hashes. The gitignored
    objects are read through REPO/artifacts (the junction to the main artifacts, RUN_PLAN §2.3) and asserted against
    that manifest. out_root is unused (kept for the call site)."""
    from . import real_sources as RS
    from . import wp3_layout as WL
    return RS.WP3Sources(WL.Roots.production(repo=REPO, out_repo=REPO))


def _real_sources(out_root, gate_arg: str):
    """WP4: a real run's sources by its gate - G2: wp4_sources.WP4Sources (the G2 loaders on the production layouts);
    any other gate: _wp3_sources, unchanged (the ungated loaders)."""
    if gate_arg == "G2":
        from . import wp4_layout as W4L
        from . import wp4_sources as W4S
        from . import wp3_layout as WL
        return W4S.WP4Sources(W4L.Roots.production(repo=REPO, out_repo=REPO),
                              WL.Roots.production(repo=REPO, out_repo=REPO))
    return _wp3_sources(out_root)


def _is_wp3(sources) -> bool:
    from . import real_sources as RS
    return isinstance(sources, RS.WP3Sources)


def _write_repro(run: "Run", p: dict, res=None) -> str | None:
    """WP3: the reproduction check or descriptive comparison of a computed ungated row (RUN_PLAN §16; wp3_repro),
    written as row_<n>_repro.json beside the row's record; real WP3 sources only (plants have none)."""
    if not _is_wp3(run.sources) or p.get("gate") not in ("none", "G2"):
        return None
    if p.get("gate") == "G2" and getattr(run.sources, "kind", None) != "real-wp4":
        return None
    from . import wp3_repro as WR
    holder: dict = {}

    def call():
        try:
            if p.get("gate") == "G2":         # WP4: the G2 reproduction records (wp4_repro)
                from . import wp4_repro as W4R
                holder["rec"] = W4R.row_reproduction(p, run.sources, res)
            else:
                holder["rec"] = WR.row_reproduction(p, run.sources, res)
        except SourceUnavailable as e:
            holder["rec"] = dict(status=e.status, what=e.what)
    try:   # fix round 1 (b): inside section 8's handler; a raise never aborts execute (class, stage, file:line kept)
        run.sources.guarded("repro", call)
    except SourceUnavailable as e:
        holder["rec"] = dict(status=REPRO_FAILED, what=e.what)
    rec = holder.get("rec")
    if rec is None:
        return None
    rec = WR.json_safe(rec)            # fix round 1 (d): no bare NaN / Infinity in a record
    doc = dict(run.header(), what="reproduction check or descriptive comparison of one row (RUN_PLAN §16; WP3)",
               row=p["row"], target_number=p["target_no"], cell_id=p["cell_id"], reproduction=rec,
               provenance=run.provenance())
    sha = write_json_atomic(run.results_dir / f"row_{p['row']:04d}_repro.json", doc)
    run.log(f"row {p['row']} reproduction record written")
    return sha


REPRO_FAILED = "not run (the reproduction raised: section 8 handler; class, stage and file:line recorded)"


def r27_scope(repo: Path = REPO) -> dict:
    """R27's scope labels in force (a3_port.a1_scope_in_force's parse of results/e3_gates_a5.json), its bytes asserted
    on the LF form (L8's LF pin) so a worktree's LF checkout passes as the main tree's CRLF copy does (RUN_PLAN §1 line
    endings); a3_port's own check pins the CRLF form only."""
    b = (Path(repo) / LA.GATES_A5_PATH).read_bytes().replace(b"\r\n", b"\n")
    if sha256_bytes(b) != LA.GATES_A5[1]:
        raise RuntimeError("e3_gates_a5.json differs from L8's LF pin")
    d = json.loads(b.decode("utf-8"))
    grad = sorted({lab.split(": ")[1].split(" claims")[0] for lab in d["scope_labels"]
                   if lab.startswith("species leg untested (gradient)")})
    n1 = sorted({lab.split(": ")[1].split(" claims")[0] for lab in d["scope_labels"]
                 if lab.startswith("brain-enrichment (N1)")})
    return dict(gradient_classes=grad, n1_classes=n1, K1_status=d["K1_status"], source_lf_sha256=LA.GATES_A5[1])


def r27_for_map(prep: "Prep", verdict_rec: dict, *, reparcellated: bool, scope: dict) -> dict:
    """RUN_PLAN §16 :1667 / R27 :968-977: amendment 5's labels and power columns of one map of a verdict row -
    a3_port.descriptors on the analysis parcels (R2_grad, R2_|x|, m, f / m, the hypergeometric p, c_S) and
    reporting.r27_reading (A3's reading with its gate logic removed). The reading is fed the row's primary status and
    survival; a component row keeps its component reading (verdict record) beside the labels. A row without a set (a
    fixed component) has no set descriptors: 'not applicable'."""
    from . import reporting as RPT
    if prep.S is None:
        return dict(status="not applicable (no set S: a fixed component)")
    desc = A3.descriptors(prep.ctx, prep.y, prep.S, parcel_ids=prep.parcel_ids)
    rec = {"status": verdict_rec.get("primary_status"), "survives": bool(verdict_rec.get("survives"))}
    out = RPT.r27_reading(rec, desc, prep.ctx, reparcellated=bool(reparcellated), scope=scope)
    out["descriptors"] = {k: (float(v) if isinstance(v, (float, np.floating)) else v) for k, v in desc.items()}
    out["reparcellated"] = bool(reparcellated)
    return component_r27(out, verdict_rec)


# pre-WP4 (§17; decision ev-1a12dffe1a85af7): the kinds a component verdict record carries (verdict.adapter_kind); the
# WP3 code compared the kind to "component", which no record carries, so a component row kept A3's full-verdict reading
COMPONENT_KINDS = ("component-permutation", "component-parametric")
SPECIES_GRADIENT_LABEL = "species leg untested (gradient)"
COMPONENT_SPECIES_NOTE = ("not meaningful for a component claim (no species leg; prereg_amend_5.md:153-159: the "
                          "component test is Level 0 and the site leg at .025); kept among the labels because a routing "
                          "choice cannot remove a label (prereg_amend_5.md:199, :230; orchestrator decision on the "
                          "pre-WP4 review, B2)")
DESCRIPTOR_COMPONENT_RULE = ("a descriptor-routed component row (verdict.descriptor_row_record): the reading is the row's "
                             "own descriptive reading (verdict.DESCRIPTIVE marker); the inner component reading is kept "
                             "beside it as component_reading, marked DESCRIPTIVE the same way")


def r27_verdict_rec(verdict: dict) -> dict:
    """The record r27_for_map is given for a verdict-pass row (run._assemble_row; r27_relabel uses the same): a
    descriptor row's inner computed record with the row's primary status, survival, descriptor_row flag and its own
    (DESCRIPTIVE-marked) reading."""
    inner = verdict.get("descriptor") if verdict.get("descriptor_row") else verdict
    out = dict(inner or {}, primary_status=verdict.get("primary_status"), survives=verdict.get("survives"))
    if verdict.get("descriptor_row"):
        out.update(descriptor_row=True, row_reading=verdict.get("reading"))
    return out


def component_r27(out: dict, verdict_rec: dict) -> dict:
    """A component row's R27 block (prereg_amend_5.md:153-162): the reading is the verdict record's component reading
    (never A3's full-verdict reading, kept beside as reading_r27); for a descriptor-routed row it is the row's own
    descriptive reading (never an unmarked 'passes at component level'). The labels are kept as A3 gives them; a
    'species leg untested (gradient)' label gets a note (labels_notes). m, f/m, c_S, R2_grad, R2_|x| and the power
    columns stand. Any other row's block is returned unchanged. Pure: it reads only the block and the verdict record
    (r27_relabel applies it to a recorded block)."""
    if verdict_rec.get("kind") not in COMPONENT_KINDS:
        return out
    out = dict(out)
    out["reading_r27"] = out.pop("reading")
    if verdict_rec.get("descriptor_row"):
        row_reading = verdict_rec.get("row_reading")
        if not (isinstance(row_reading, str) and row_reading.startswith(V.DESCRIPTIVE)):
            raise RuntimeError("R27: a descriptor-routed component row without its DESCRIPTIVE reading")
        out["reading"] = row_reading
        out["component_reading"] = f"{V.DESCRIPTIVE}: {verdict_rec.get('reading')}"
        out["reading_rule"] = DESCRIPTOR_COMPONENT_RULE
    else:
        out["reading"] = verdict_rec.get("reading")
        out["reading_rule"] = "component level: the component reading (prereg_amend_5.md:156) beside R27's labels"
    if SPECIES_GRADIENT_LABEL in (out.get("labels") or []):
        out["labels_notes"] = {SPECIES_GRADIENT_LABEL: COMPONENT_SPECIES_NOTE}
    out["component_label"] = verdict_rec.get("label")
    return out


def check_preconditions(p: dict, plant_view: bool) -> tuple[str | None, list]:
    """(status if the row cannot run now, notes). U2: a plant view takes a conditional row's carrier test as passed;
    a conditional analysis class is refused in a plant (the synthetic context needs a determined class)."""
    notes = []
    if "carrier" in p["preconditions"]:
        if not plant_view:
            return NOT_RUN_CONDITIONAL, notes
        notes.append("conditional: carrier test taken as passed (plant view, U2)")
    if "class" in p["preconditions"] and not plant_view:
        return NOT_RUN_CLASS, notes
    return None, notes


def resolve_class(p: dict, sources) -> dict:
    """A plan whose analysis class is conditional gets the class the sources determine (synthetic: the first named
    option, U2; real: WP5's determination, refused until it exists). The TSV text is kept beside it."""
    if "class" not in p["preconditions"]:
        return p
    q = dict(p)
    q["analysis_class_tsv"] = p["analysis_class"]
    q["analysis_class"] = sources.resolve_class(p)
    return q


# ================================================================================================================
# sources (interface; synthetic implementations only: real loaders are WP3)
# ================================================================================================================
class Sources:
    """Interface. context(class) -> (ClassContext, AHBA sample counts {parcel id: n}, sha256); map(plan, map index) ->
    (y, parcel ids, class, {name: sha256}); gene_set(plan) -> (member columns (gene symbols), sha256); component(plan)
    -> (values, parcel ids, sha256); trajectories(class) -> (genes x 8 frame, sha256); donor_counts(class) ->
    ({parcel id: donors}, sha256). Every method may raise SourceUnavailable."""
    kind = "abstract"
    synthetic = False

    def spec(self) -> dict:
        raise NotImplementedError

    def context(self, cls: str):
        raise NotImplementedError

    def map(self, plan: dict, map_index: int):
        raise NotImplementedError

    def gene_set(self, plan: dict):
        raise NotImplementedError

    def component(self, plan: dict):
        raise NotImplementedError

    def trajectories(self, cls: str):
        raise NotImplementedError

    def donor_counts(self, cls: str):
        raise NotImplementedError

    def selection_rule(self, plan: dict, ctx):
        """(select(map values) -> gene indices, stat(map values, genes) -> float, sha256): a selected list's rule and
        statistic (RUN_PLAN_amend_1 R34: given no generator)."""
        raise NotImplementedError

    def resolve_class(self, plan: dict) -> str:
        raise NotImplementedError


class RealSources(Sources):
    """The real loaders are WP3 (identity at use, re-parcellation, decoder fetch, carriers): every source refuses.
    WP2 review B4: every file a real loader opens goes through real_path (fetch_extract.refuse_quarantine_path via
    refuse_quarantine_opener, with quarantine_root; None = the production root), so WP3's loaders inherit the
    quarantine refusal."""
    kind = "real"
    quarantine_root = None     # None: fetch_extract.Roots.production().quarantine

    def real_path(self, path) -> Path:
        """The one door a real loader opens a file through: a path under the quarantine raises PermissionError."""
        from . import fetch_extract as FE
        return FE.refuse_quarantine_opener(path, self.quarantine_root)

    def spec(self) -> dict:
        return {"kind": "real"}

    def _no(self, what):
        raise SourceUnavailable(NOT_RUN_WP3, what)

    def context(self, cls):
        try:
            return self.real_context(cls)
        except NotImplementedError as e:
            raise SourceUnavailable(NOT_RUN_WP3, str(e)) from None

    @staticmethod
    def real_context(cls):
        """WP3 hook. Real class contexts are built through adapters.build_context_checked (RUN_PLAN_amend_1 R35: the
        1e-12 first-use reader check, then a3_port.build_context with its L7 pin), with the AHBA sample counts."""
        raise NotImplementedError(f"WP3: class context {cls} through adapters.build_context_checked (RUN_PLAN_amend_1 "
                                  "R35 first-use check) and its AHBA sample counts")

    def selection_rule(self, plan, ctx):
        self._no("the paper's selection rule and statistic (RA-11 ... 14; WP3 / WP5)")

    def resolve_class(self, plan):
        raise SourceUnavailable(NOT_RUN_CLASS, "the analysis class is determined from a G1 carrier (WP5)")

    def map(self, plan, map_index):
        self._no("map (identity at download / use, re-parcellation: WP3)")

    def gene_set(self, plan):
        self._no("set (register_sets manifests / gated sets: WP3)")

    def component(self, plan):
        self._no("component (shipped PC1 / R12 build: WP2-WP3)")

    def trajectories(self, cls):
        self._no("BrainSpan trajectories (WP3)")

    def donor_counts(self, cls):
        self._no("donor counts (R11 venv_ref build: WP2)")


SYN_G, SYN_BRAIN, SYN_M, SYN_A = 300, 50, 25, 0.5
# synthetic stand-ins of the analysis classes (class sizes as the registered classes; ids are synthetic)
SYN_CLASSES = {   # class_id: seeds.plant_class_id (one fixed integer per class; B3) - the values WP1 gave them
    "dk-ctx": dict(sizes=(34,), names=("cortex",), class_id=SD.plant_class_id("dk-ctx")),
    "V-DK": dict(sizes=(34, 8), names=("cortex", "subcortex/brainstem"), class_id=SD.plant_class_id("V-DK")),
    "V-AAL": dict(sizes=(38, 7, 9), names=("cortex", "subcortex/brainstem", "cerebellum"),
                  class_id=SD.plant_class_id("V-AAL")),
    "V-DK-subcortex": dict(sizes=(7,), names=("subcortex/brainstem",), class_id=SD.plant_class_id("V-DK-subcortex")),
    "MIST64": dict(sizes=(33, 5, 8), names=("cortex", "subcortex", "cerebellum"), class_id=SD.plant_class_id("MIST64")),
}
assert {k: v["class_id"] for k, v in SYN_CLASSES.items()} == {"dk-ctx": 2, "V-DK": 12, "V-AAL": 11,
                                                              "V-DK-subcortex": 13, "MIST64": 14}
SYN_CASE = {"context": 0, "map": 100_000, "set": 10_000_000, "component": 20_000_000, "traj": 30_000_000}


def synthetic_guard(no_data_dir: Path) -> None:
    """Point every engine data path at a directory that does not exist, so a synthetic run can read no real data
    (an unpatched read fails there). As tests/test_verdict.py does."""
    import e3_plants
    nd = Path(no_data_dir)
    if nd.exists():
        raise RuntimeError("the no-data directory exists")
    e3_plants.GAMBA_CSV = nd / "gamba.csv"
    e3_plants.AHBA = nd
    A3.AHBA = nd


class SyntheticSources(Sources):
    """Synthetic maps, sets and class contexts for plants (RUN_PLAN §7 'Data: synthetic maps only'): every value is
    drawn from SeedSequence([20260925, 900, plant_id, case, class_id]) (seeds.plant_seed; target 900 does not exist).
    Contexts: G = 300 genes, class offsets + 5 smooth spatial factors + noise, each gene scaled and shifted (so gene
    variances differ), a brain>body background of 50 genes, AHBA sample counts 1-5 per parcel with the first parcel at 0
    (dropped by §4's rule) and donor counts 1-3. Maps: y = a z(set score of the row's synthetic S) + sqrt(1 - a^2)
    z(field), a = .5 unless given, the last parcel NaN (dropped). Sets: 25 genes.
    case (B3): None (P2, and every caller made before the review) - the data word is the 5-word key's case word,
    seeds.plant_seed(plant_id, word, class_id), as before; an integer plant case - seeds.plant_data_seed(plant_id, case,
    class_id, word) (7 words, 1000 in the leg position: never a leg or G3 stream), so every case has its own data."""
    kind = "synthetic"
    synthetic = True

    def __init__(self, plant_id: int, no_data_dir, case: int | None = None, a: float = SYN_A):
        self.plant_id = int(plant_id)
        self.no_data_dir = str(no_data_dir)
        self.case = None if case is None else int(case)
        self.a = float(a)
        if not 0.0 <= self.a < 1.0:
            raise ValueError("synthetic signal weight a must lie in [0, 1)")
        synthetic_guard(Path(self.no_data_dir))

    def spec(self) -> dict:
        seed = ("seeds.plant_seed(plant_id, data word, class_id)" if self.case is None else
                "seeds.plant_data_seed(plant_id, case, class_id, data word)")
        return {"kind": "synthetic", "plant_id": self.plant_id, "no_data_dir": self.no_data_dir, "case": self.case,
                "G": SYN_G, "brain": SYN_BRAIN, "m": SYN_M, "a": self.a, "seed": seed}

    def _rng(self, case: int, cls: str):
        """The generator of one synthetic data kind (its word: SYN_CASE[kind] + row ...; the name `case` is kept for
        the callers, forms.py included)."""
        cid = SYN_CLASSES[cls]["class_id"]
        if self.case is None:
            return np.random.default_rng(SD.plant_seed(self.plant_id, case, cid))
        return np.random.default_rng(SD.plant_data_seed(self.plant_id, self.case, cid, case))

    def _cls(self, cls: str) -> dict:
        if cls not in SYN_CLASSES:
            raise SourceUnavailable(REFUSED_CLASS, f"no synthetic class {cls}")
        return SYN_CLASSES[cls]

    @functools.lru_cache(maxsize=None)
    def _raw(self, cls: str):
        spec = self._cls(cls)
        rng = self._rng(SYN_CASE["context"], cls)
        cl = np.concatenate([[c] * k for c, k in zip(spec["names"], spec["sizes"])])
        P, G = cl.size, SYN_G
        xyz = rng.uniform(-70, 70, (P, 3))
        D = np.sqrt(((xyz[:, None] - xyz[None]) ** 2).sum(-1))
        L = np.linalg.cholesky(np.exp(-(D / 40) ** 2) + 1e-6 * np.eye(P))
        facs = np.column_stack([L @ rng.standard_normal(P) for _ in range(5)])
        off = {c: rng.standard_normal(G) for c in spec["names"]}
        X = np.stack([off[c] for c in cl]) + facs @ rng.standard_normal((5, G)) + 0.7 * rng.standard_normal((P, G))
        X = X * rng.uniform(0.2, 5.0, G) + rng.uniform(-3, 3, G)
        ids = np.arange(1001, 1001 + P, dtype=np.int64)
        genes = [f"sg{j:04d}" for j in range(G)]
        brain = sorted(genes[i] for i in rng.choice(G, SYN_BRAIN, replace=False))
        counts = rng.integers(1, 6, P)
        counts[0] = 0
        donors = np.minimum(rng.integers(1, 4, P), counts)  # a parcel's donors never exceed its samples
        expr = pd.DataFrame(X, index=ids, columns=genes)
        info = pd.DataFrame({"label": [f"sp{i}" for i in ids], "hemisphere": "L", "structure": cl}, index=ids)
        sha = arr_sha(X, ids, np.array(cl, dtype=str), xyz, np.array(brain, dtype=str))
        return dict(expr=expr, classes=cl, xyz=xyz, info=info, brain=brain, ids=ids,
                    counts={int(i): int(c) for i, c in zip(ids, counts)},
                    donors={int(i): int(c) for i, c in zip(ids, donors)}, sha=sha)

    @functools.lru_cache(maxsize=None)
    def _ctx(self, cls: str):
        r = self._raw(cls)
        return A3.ClassContext(cls, r["expr"].copy(), r["classes"].copy(), r["xyz"].copy(), r["info"].copy(),
                               A3.symbols_background(r["brain"]), None)

    def context(self, cls):
        r = self._raw(cls)
        return self._ctx(cls), dict(r["counts"]), r["sha"]

    def _genes_for(self, row: int, cls: str) -> list[str]:
        rng = self._rng(SYN_CASE["set"] + int(row), cls)
        return sorted(f"sg{j:04d}" for j in rng.choice(SYN_G, SYN_M, replace=False))

    def gene_set(self, plan):
        genes = self._genes_for(plan["row"], plan["analysis_class"])
        return genes, sha256_bytes("\n".join(genes).encode("utf-8"))

    def map(self, plan, map_index):
        cls = plan["analysis_class"]
        r = self._raw(cls)
        ctx = self._ctx(cls)
        rng = self._rng(SYN_CASE["map"] * (int(map_index) + 1) + int(plan["row"]), cls)
        idx = [ctx.U.index[g] for g in self._genes_for(plan["row"], cls)]
        sig = A3.zscore(ctx.X[:, idx].mean(1))
        Lc = np.linalg.cholesky(np.exp(-(ctx.D / 35.0) ** 2) + 1e-6 * np.eye(ctx.n))
        fld = A3.zscore(Lc @ rng.standard_normal(ctx.n))
        y = self.a * sig + math.sqrt(1 - self.a ** 2) * fld
        y[-1] = np.nan
        ids = np.asarray(ctx.parcel_ids, dtype=np.int64)
        return y, ids, cls, {f"map[{int(map_index)}]": arr_sha(y, ids)}

    def component(self, plan):
        cls = plan["analysis_class"]
        ctx = self._ctx(cls)
        rng = self._rng(SYN_CASE["component"] + int(plan["row"]), cls)
        Lc = np.linalg.cholesky(np.exp(-(ctx.D / 35.0) ** 2) + 1e-6 * np.eye(ctx.n))
        c = Lc @ rng.standard_normal(ctx.n)
        ids = np.asarray(ctx.parcel_ids, dtype=np.int64)
        return c, ids, arr_sha(c, ids)

    @functools.lru_cache(maxsize=None)
    def _traj(self, cls: str):
        rng = self._rng(SYN_CASE["traj"], cls)
        genes = list(self._raw(cls)["expr"].columns)
        t = np.linspace(0, 1, 8)
        lvl = rng.normal(5, 1.5, len(genes))[:, None]
        slope = rng.normal(0, 1.5, len(genes))[:, None]
        cen = rng.uniform(0, 1, len(genes))[:, None]
        bump = rng.normal(0, 1.0, len(genes))[:, None] * np.exp(-((t - cen) / .25) ** 2)
        vals = lvl + slope * t + bump + 0.1 * rng.standard_normal((len(genes), 8))
        df = pd.DataFrame(vals, index=genes, columns=[f"bin{k}" for k in range(8)])
        return df, arr_sha(vals, np.array(genes, dtype=str))

    def trajectories(self, cls):
        df, sha = self._traj(cls)
        return df.copy(), sha

    def donor_counts(self, cls):
        r = self._raw(cls)
        return dict(r["donors"]), arr_sha(np.array(sorted(r["donors"].items()), dtype=np.int64))

    def resolve_class(self, plan):
        text = plan["analysis_class"]
        if not text.startswith(CLASS_CONDITIONAL_PREFIX):
            raise SourceUnavailable(REFUSED_CLASS, "not a conditional class of the registered form")
        return "dk-ctx"  # the first named option (U2; the real determination is WP5's)

    def selection_rule(self, plan, ctx):
        """A synthetic selection rule for plants (R34's interface; no generator anywhere): the up to 25 genes whose
        per-gene Pearson r with the map is largest in the list's sign and above .1 in that sign (possibly none, so
        the empty-list rule T = 0 is reached); statistic = Pearson r(map, mean of the selected columns)."""
        sign = -1 if plan["registered_direction"] == -1 else 1
        X = np.asarray(ctx.X, dtype=float)
        Z = (X - X.mean(0)) / X.std(0)
        n = X.shape[0]

        def select(v):
            v = np.asarray(v, dtype=float)
            sd = v.std()
            if not sd > 0:
                return np.array([], dtype=int)
            r = Z.T @ ((v - v.mean()) / sd) / n
            top = np.argsort(-sign * r, kind="stable")[:SYN_M]
            return top[sign * r[top] > 0.1]

        def stat(v, genes):
            return float(np.corrcoef(np.asarray(v, dtype=float), X[:, genes].mean(1))[0, 1])

        desc = ("synthetic selection rule: <= 25 genes, largest sign * per-gene r, sign * r > .1; statistic Pearson "
                "r(map, mean of the selected columns); sign %+d" % sign)
        return select, stat, sha256_bytes(desc.encode("utf-8") + arr_sha(X).encode("ascii"))


@functools.lru_cache(maxsize=8)
def _sources_cached(spec_json: str) -> Sources:
    spec = json.loads(spec_json)
    if spec["kind"] == "real":
        return RealSources()
    if spec["kind"] == "real-wp3":   # WP3: the ungated loaders (real_sources.py), rebuilt from their layout
        from . import real_sources as RS
        from . import wp3_layout as WL
        return RS.WP3Sources(WL.Roots.from_spec(spec["roots"]))
    if spec["kind"] == "real-wp4":   # WP4: the G2 loaders (wp4_sources.py), rebuilt from their layouts
        from . import wp4_layout as W4L
        from . import wp4_sources as W4S
        from . import wp3_layout as WL
        return W4S.WP4Sources(W4L.Roots.from_spec(spec["roots4"]), WL.Roots.from_spec(spec["roots"]))
    if spec["kind"] == "synthetic":
        return SyntheticSources(spec["plant_id"], spec["no_data_dir"], case=spec.get("case"),
                                a=spec.get("a", SYN_A))
    raise ValueError(f"unknown sources kind {spec['kind']!r}")


def sources_from_spec(spec: dict) -> Sources:
    return _sources_cached(json.dumps(spec, sort_keys=True))


# ================================================================================================================
# preparation: class context restricted to the analysis parcels, y, S, the adapter (§4)
# ================================================================================================================
PARCEL_RULES = {"primary": 1, "donors>=2": 2}
PARCEL_COUNT_UNIT = {"primary": "samples", "donors>=2": "donors"}   # pre-WP4: the rule text names what is counted


class Prep:
    __slots__ = ("plan", "map_index", "rule", "ctx", "y", "parcel_ids", "S", "adapter", "hashes", "parcels", "set_info",
                 "triple", "component")


def prepare(plan: dict, sources: Sources, map_index: int, rule: str = "primary") -> Prep:
    """§4 'Analysis parcels': a parcel enters iff y is finite there and it has >= 1 AHBA sample (rule 'primary'), or
    >= 2 donors (R11 sensitivity, rule 'donors>=2'). The class context is restricted to them (ClassContext.restrict)."""
    cls = plan["analysis_class"]
    base, counts, ctx_sha = sources.context(cls)
    y, ids, mcls, mh = sources.map(plan, map_index)
    if mcls != cls:
        raise RuntimeError(f"map source returned class {mcls}, the row's class is {cls}")
    ids = A3.as_parcel_ids(ids, "map")
    if not set(ids.tolist()) <= set(int(i) for i in base.parcel_ids):
        raise RuntimeError("the map holds parcels outside its class (re-parcellation is the loader's job)")
    hashes = {"context": ctx_sha, **mh}
    if rule == "donors>=2":
        counts, dsha = sources.donor_counts(cls)
        hashes["donor_counts"] = dsha
    ap = AD.analysis_parcels(y, counts, parcel_ids=ids, min_count=PARCEL_RULES[rule],
                             class_parcel_ids=base.parcel_ids,   # C8: class parcels absent from the map are dropped
                             count_unit=PARCEL_COUNT_UNIT[rule])
    keep = ap["parcel_ids"]
    ctx = base.restrict(keep)
    pos = {int(p): k for k, p in enumerate(ids.tolist())}
    yk = np.asarray(y, dtype=float)[[pos[int(p)] for p in keep]]
    pr = Prep()
    pr.plan, pr.map_index, pr.rule, pr.ctx, pr.parcels = plan, int(map_index), rule, ctx, ap
    pr.parcel_ids = np.asarray(keep, dtype=np.int64)
    pr.y = yk
    pr.S, pr.set_info, pr.component = None, None, None
    if plan["has_set"] and (plan["form"] in FULL_FORMS or (plan["component"] or {}).get("genes_from_set")):
        genes, ssha = sources.gene_set(plan)
        hashes["set"] = ssha
        idx, missing = ctx.U.idx(genes)
        pr.set_info = dict(n_members=len(dict.fromkeys(genes)), n_present=int(len(idx)), n_absent=int(len(missing)))
        if len(idx) < MIN_SET:
            raise NotTestableAtUse(f"not testable (< 5): {len(idx)} columns of S in the analysis universe (U14)")
        pr.S = np.asarray(idx, dtype=int)
    form = plan["form"]
    if form in FULL_FORMS:
        pr.adapter = AD.make_adapter(form, ctx, yk, parcel_ids=pr.parcel_ids, S=pr.S)
    else:
        spec = plan["component"]
        kw = {}
        if spec["kind"] == "selected":  # RUN_PLAN_amend_1 R34
            select, stat, rsha = sources.selection_rule(plan, ctx)
            hashes["selection_rule"] = rsha
            pr.adapter = AD.SelectedList(ctx, yk, select, stat, parcel_ids=pr.parcel_ids)
        elif spec["kind"] == "fixed":
            c, cids, csha = sources.component(plan)
            hashes["component"] = csha
            cpos = {int(p): k for k, p in enumerate(A3.as_parcel_ids(cids, "component").tolist())}
            kw["component"] = np.asarray(c, dtype=float)[[cpos[int(p)] for p in keep]]
            pr.component = kw["component"]
        else:
            if spec.get("genes_from_set"):
                kw["genes"] = pr.S
            if spec["kind"] == "plsr":
                kw["n_components"] = spec["n_components"]
                if spec.get("cumulative"):
                    kw["cumulative"] = True
                else:
                    kw["component"] = spec["component"]
        if spec["kind"] != "selected":
            pr.adapter = AD.make_adapter("component", ctx, yk, parcel_ids=pr.parcel_ids, component_kind=spec["kind"],
                                         **kw)
    pr.hashes = hashes
    pr.triple = None
    if form in FULL_FORMS:
        pr.triple = sha256_json([cls, ctx_sha, [int(i) for i in pr.parcel_ids], sorted(int(s) for s in pr.S)])
    return pr


_PREP_CACHE: dict = {}


def prepare_cached(plan: dict, spec: dict, map_index: int, rule: str) -> Prep:
    key = (json.dumps(spec, sort_keys=True), plan["row"], int(map_index), rule)
    if key not in _PREP_CACHE:
        if len(_PREP_CACHE) > 16:
            _PREP_CACHE.clear()
        _PREP_CACHE[key] = prepare(plan, sources_from_spec(spec), map_index, rule)
    return _PREP_CACHE[key]


# ================================================================================================================
# memory (§4 :382-385)
# ================================================================================================================
def process_peak_working_set() -> int | None:
    """Windows: PeakWorkingSetSize of this process (GetProcessMemoryInfo); None elsewhere or on failure."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        k32, psapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        ok = psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
        return int(pmc.PeakWorkingSetSize) if ok else None
    except Exception:
        return None


class MemProbe:
    """Peak memory of one task: psutil (RSS sampled every 20 ms) if importable, else tracemalloc (allocations traced
    during the task; numpy reports its buffers to tracemalloc). On Windows also the process peak working set."""

    def __enter__(self):
        self.method = None
        try:
            import psutil  # noqa: F401
            self._ps = psutil.Process()
            self.method = "psutil RSS sampled every 20 ms"
            self._peak, self._stop = self._ps.memory_info().rss, threading.Event()

            def sample():
                while not self._stop.is_set():
                    self._peak = max(self._peak, self._ps.memory_info().rss)
                    self._stop.wait(0.02)
            self._th = threading.Thread(target=sample, daemon=True)
            self._th.start()
        except ImportError:
            self.method = "tracemalloc (allocations traced during the task)"
            self._own = not tracemalloc.is_tracing()
            if self._own:
                tracemalloc.start()
            tracemalloc.reset_peak()
            self._base = tracemalloc.get_traced_memory()[0]
        return self

    def __exit__(self, *exc):
        if self.method.startswith("psutil"):
            self._stop.set()
            self._th.join()
            peak = int(self._peak)
        else:
            peak = int(tracemalloc.get_traced_memory()[1] - self._base)
            if self._own:
                tracemalloc.stop()
        ws = process_peak_working_set()
        job = ws if ws is not None else peak
        self.result = {"method": self.method, "task_peak_bytes": peak, "process_peak_working_set_bytes": ws,
                       "job_measure": "process peak working set" if ws is not None else self.method,
                       "defect": bool(job > JOB_LIMIT_BYTES),
                       "defect_rule": "a job above 2.5 GB (2.5e9 B) is a defect (RUN_PLAN §4 :382-385)"}
        return False


# ================================================================================================================
# leg groups (each one checkpoint; mirrors verdict.collect_legs / descriptors.descriptor_pass exactly)
# ================================================================================================================
VERDICT_GROUPS = ("legs",)
DESCRIPTOR_GROUPS = ("descriptors",)


def verdict_K(K: dict) -> dict:
    return {"site": int(K["site"]), "species": int(K["species"]), "permutation": int(K["permutation"])}


def plant_class_word(plan: dict) -> int:
    """The class word of a plant key for this plan: seeds.plant_class_id of the row's analysis class; a gene-set-only
    row (analysis class 'none': "no class universe of its own", TSV rows 471-477) takes the id of its synthetic Liu data
    kind, forms.SYN_LIU_CLASS_ID (BrainSpan-like 15, AHBA-like 16; seeds.PLANT_CLASS_IDS_TAKEN), asserted outside
    seeds.PLANT_CLASS_IDS (WP2r: form rows draw plant keys)."""
    if plan.get("form_name") == "liu" and plan["analysis_class"] == "none":
        cid = int(_forms().SYN_LIU_CLASS_ID[plan["liu_spec"]["data"]])
        if cid not in SD.PLANT_CLASS_IDS_TAKEN or cid in SD.PLANT_CLASS_IDS.values():
            raise ValueError(f"plant class word {cid} of a gene-set-only row is not a reserved Liu data id")
        return cid
    return SD.plant_class_id(plan["analysis_class"])


def seeds_of(plan: dict, map_index: int) -> dict:
    """The row's seed callables: claim keys (verdict.seed_callables; real runs and P2), or, when the plan carries a
    plant seed view (B3; set by execute in a plant case run, and for form rows by _run_form_row, WP2r), the plant
    case's keys (verdict.plant_seed_callables with plant_class_word; no map or cell index enters a plant key)."""
    sv = plan.get("seed_view")
    if not sv or sv.get("kind") == "claim":
        return V.seed_callables(plan["target_no"], plan["row"], int(map_index), int(plan["cell_index"]))
    if sv.get("kind") == "plant":
        return V.plant_seed_callables(sv["plant_id"], sv["case"], plant_class_word(plan))
    raise ValueError(f"unknown seed view {sv!r}")


def seed_record_for(plan: dict, map_index: int, uses, **flags) -> dict:
    """R7's seed record of one row x map under the plan's seed view: seeds.seed_record (claim keys) or
    seeds.plant_seed_record (plant keys; B3), the same layout."""
    sv = plan.get("seed_view")
    if not sv or sv.get("kind") == "claim":
        return SD.seed_record(plan["target_no"], plan["row"], int(map_index), int(plan["cell_index"]), uses, **flags)
    if sv.get("kind") == "plant":
        return SD.plant_seed_record(sv["plant_id"], sv["case"], plant_class_word(plan), uses,
                                    row=int(plan["row"]), map_index=int(map_index), cell_index=int(plan["cell_index"]),
                                    **flags)
    raise ValueError(f"unknown seed view {sv!r}")


def verdict_for_plan(plan: dict, computed: dict) -> dict:
    """B1: a row routed with descriptor = True is written through verdict.descriptor_row_record (survives False; the
    primary status is the row's TSV status under the run's view; the computed record under 'descriptor'); any other
    row's record is returned unchanged."""
    if not plan.get("descriptor"):
        return computed
    return V.descriptor_row_record(computed, plan["status_effective"], status_tsv=plan.get("status_tsv"),
                                   label=plan.get("label"))


def level0_seed_leg(adapter) -> str | None:
    """The Level-0 permutation key of a component adapter (RUN_PLAN_amend_1 R34): 'permutation' (leg 8) or
    're-selection' (leg 10, selected lists), read from the adapter (LEVEL0_SEED_LEG); None for a parametric Level 0."""
    if isinstance(adapter, AD.FixedComponent) or not isinstance(adapter, AD._Component):
        return None
    return adapter.LEVEL0_SEED_LEG


def group_seed_keys(plan: dict, map_index: int, group: str, adapter=None) -> dict:
    """The SeedSequence keys a group draws from (checkpoint identity; R7)."""
    sc = seeds_of(plan, map_index)
    so, tso = sc["seed_of"], sc["tabs_seed_of"]
    if group == "legs":
        names = ["S1c", "S2c"] + (["G1", "G3m", "G6s", "G6l"] if plan["form"] in FULL_FORMS else [])
        lz = level0_seed_leg(adapter)
        if lz is not None:
            names.append(lz)
        return {k: SD.key_record(so(k)) for k in names}
    if group == "descriptors":
        out = {k: SD.key_record(so(k)) for k in ("G1", "G2", "G4", "G5", "J1", "naive joint")}
        out["G3 (R24)"] = SD.key_record(sc["g3_seed"]())
        return out
    if group == "tabs":
        return {f"T_abs {k}": SD.key_record(tso(k)) for k in ("S1c", "S2c", "G1", "G3m", "G6l")}
    raise ValueError(f"unknown group {group!r}")


def g_legs(pr: Prep, K: dict, seed_of, g6l) -> dict:
    """The verdict legs of one claim on one map: verdict.collect_legs, unchanged (no direction chosen here)."""
    out = dict(legs=V.collect_legs(pr.adapter, verdict_K(K), seed_of, g6l=g6l, chunk=AD.CHUNK_MAX))
    if isinstance(pr.adapter, AD.SetVsMap):
        out["spearman"] = pr.adapter.spearman()  # 'Spearman beside it' (claims_register.md:284)
    return out


def g_descriptors(pr: Prep, K: dict, sc: dict, traj, direction, two_sided) -> dict:
    """descriptors.descriptor_pass, unchanged, with the verdict's d* (two-sided) or the registered direction; plus the
    G3 / leg-3 stream fingerprints (P2, R24)."""
    rec = DS.descriptor_pass(pr.adapter, sc["seed_of"], sc["g3_seed"], K_sets=int(K["sets"]), K_surr=int(K["surr"]),
                             K_j1_sets=int(K["j1_sets"]), traj=traj, species=None, direction=direction,
                             two_sided=two_sided, chunk=AD.CHUNK_MAX)
    fp = {"G3 (R24: first spawned child of leg 3's key)": stream_fingerprint(sc["g3_seed"]()),
          "G3m (leg 3)": stream_fingerprint(sc["seed_of"]("G3m"))}
    return dict(record=rec, stream_fingerprints=fp, g3_key=SD.key_record(sc["g3_seed"]()),
                leg3_key=SD.key_record(sc["seed_of"]("G3m")))


def g_tabs(pr: Prep, K: dict, sc: dict, g6l) -> dict:
    """descriptors.t_abs_legs, unchanged, on this row's leg-25 windows."""
    tb = AD.TAbs(pr.ctx, pr.y, pr.S, parcel_ids=pr.parcel_ids)
    return DS.t_abs_legs(tb, {"site": int(K["site"]), "species": int(K["species"])}, sc["tabs_seed_of"],
                         depletion=bool(pr.plan["depletion"]), g6l=g6l, chunk=AD.CHUNK_MAX)


# ---- G6l screens (one per triple, files beside the checkpoints) ------------------------------------------------
def stream_name(row: int, map_index: int, leg: int) -> str:
    return f"r{int(row):04d}_m{int(map_index)}_l{int(leg)}"


def stream_seed(plan: dict, map_index: int, leg: int) -> np.random.SeedSequence:
    sc = seeds_of(plan, map_index)
    return sc["seed_of"]("G6l") if leg == 5 else sc["tabs_seed_of"]("G6l")


def g6l_screen_task(kw: dict) -> dict:
    """One screen of (S, class, parcels) for every stream named in kw['streams'] ([(plan, map_index, leg)]); windows
    saved as int32 .npy beside the checkpoints, sha256 recorded."""
    plan0, mi0 = kw["streams"][0][0], kw["streams"][0][1]
    pr = prepare_cached(plan0, kw["sources"], mi0, kw["rule"])
    if pr.triple != kw["triple"]:
        raise RuntimeError("g6l screen: the rebuilt triple differs from the parent's")
    names, sss = [], []
    for plan, mi, leg in kw["streams"]:
        names.append(stream_name(plan["row"], mi, leg))
        sss.append(stream_seed(plan, mi, leg))
    res = PM.streams_screen(kw["g6l_mode"], pr.ctx, pr.S, dict(zip(names, sss)), int(kw["K"]["species"]))
    out = {}
    gdir = Path(kw["ck_dir"]) / "g6l"
    gdir.mkdir(parents=True, exist_ok=True)
    for name, (sets, info) in res.items():
        rec = dict(info=A3.jsonable(info), file=None, sha256=None, n_sets=0)
        if sets is not None:
            f = gdir / f"{kw['triple'][:16]}_{name}.npy"
            tmp = f.with_name(f.name + ".tmp.npy")
            np.save(tmp, np.asarray(sets, dtype=np.int32))
            os.replace(tmp, f)
            rec.update(file=f.name, sha256=sha256_bytes(f.read_bytes()), n_sets=int(len(sets)))
        out[name] = rec
    return dict(triple=kw["triple"], mode=kw["g6l_mode"], streams=out)


def load_screen(ck_dir: Path, rec: dict):
    """(sets or None, info) from a screen record; the file's sha256 must equal the record's."""
    info = dict(rec["info"])
    if rec["file"] is None:
        return None, info
    f = Path(ck_dir) / "g6l" / rec["file"]
    data = f.read_bytes()
    if sha256_bytes(data) != rec["sha256"]:
        raise RuntimeError(f"G6l screen file {f.name}: sha256 differs from its record")
    sets = np.load(f).astype(np.int64)
    if len(sets) != rec["n_sets"]:
        raise RuntimeError("G6l screen file: set count differs from its record")
    return sets, info


# ---- the task function (run_pending's fn; module level so loky pickles it by reference) ------------------------
def task(key: str, kw: dict):
    t0 = time.perf_counter()
    started = LA.now_iso()
    with MemProbe() as mp:
        if kw["group"] == "g6l":
            payload = g6l_screen_task(kw)
        else:
            pr = prepare_cached(kw["plan"], kw["sources"], kw["map_index"], kw["rule"])
            if pr.hashes != kw["expect_hashes"] or [int(i) for i in pr.parcel_ids] != kw["parcel_ids"]:
                raise RuntimeError(f"{key}: the worker loaded other inputs than the parent saw (hash / parcels)")
            sc = seeds_of(kw["plan"], kw["map_index"])
            g, K = kw["group"], kw["K"]
            if g == "legs":
                screen = load_screen(kw["screen_dir"], kw["screen"]) if kw.get("screen") is not None else None
                payload = g_legs(pr, K, sc["seed_of"], screen)
            elif g == "descriptors":
                traj, tsha = sources_from_spec(kw["sources"]).trajectories(kw["plan"]["analysis_class"])
                if tsha != kw["traj_sha"]:
                    raise RuntimeError("trajectories differ from the parent's")
                payload = g_descriptors(pr, K, sc, traj, kw["direction"], kw["two_sided"])
            elif g == "tabs":
                payload = g_tabs(pr, K, sc, load_screen(kw["screen_dir"], kw["screen"]))
            else:
                raise ValueError(f"unknown group {g!r}")
    payload = A3.jsonable(payload)
    payload["_meta"] = dict(started=started, finished=LA.now_iso(), seconds=round(time.perf_counter() - t0, 3),
                            memory=mp.result, pid=os.getpid())
    return key, payload


# ================================================================================================================
# assembly (no null recomputed)
# ================================================================================================================
def seed_uses(plan: dict, pass_: str, adapter=None) -> tuple[dict, dict]:
    """(legs -> use, flags) for seeds.seed_record, the legs this pass draws (R7: 'Every row records SS keys and integer
    seeds'); a component's Level-0 key is the adapter's (R34: leg 8, or leg 10 for a selected list)."""
    if pass_ in ("verdict", "sensitivity"):
        if plan["form"] in FULL_FORMS:
            return {"S1c": "int", "S2c": "int", "G1": "rng", "G3m": "rng", "G6s": "rng", "G6l": "rng"}, {}
        uses = {"S1c": "int", "S2c": "int"}
        lz = level0_seed_leg(adapter)
        if lz is not None:
            uses[V.LEG_ALIASES.get(lz, lz)] = "rng"
        return uses, {}
    uses = {"G1": "rng", "G2": "rng", "G4": "rng", "G5": "rng"}
    if plan["t_abs"]:
        uses.update({"T_abs S1c": "int", "T_abs S2c": "int", "T_abs G1": "rng", "T_abs G3m": "rng", "T_abs G6l": "rng"})
    return uses, dict(g3=True, j1=True, naive_joint=True)


# ================================================================================================================
# the run
# ================================================================================================================
class Log:
    def __init__(self, path: Path | None, prefix: str = ""):
        self.path, self.prefix = path, prefix
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, msg: str) -> None:
        line = "[%s] %s%s" % (_dt.datetime.now().strftime("%H:%M:%S"), self.prefix, ascii_line(msg))
        print(line, flush=True)
        if self.path is not None:
            with open(self.path, "a", encoding="utf-8", newline="\n") as f:
                f.write(line + "\n")
                f.flush()


def parse_rows(text: str | None) -> list[int] | None:
    if not text:
        return None
    out: list[int] = []
    for part in text.split(","):
        part = part.strip()
        m = re.fullmatch(r"([1-9][0-9]*)(?:-([1-9][0-9]*))?", part)
        if not m:
            raise ValueError(f"--rows: {part!r}")
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        if b < a:
            raise ValueError(f"--rows: {part!r}")
        out.extend(range(a, b + 1))
    if len(set(out)) != len(out) or not all(1 <= r <= LD.N_ROWS for r in out):
        raise ValueError("--rows: duplicated or out-of-range rows")
    return out


def plant_K(plant_name: str | None = None) -> dict:
    """PLANT_K with the plant's registered counts where §7 pins them (C4: PLANT_K_OVERRIDES, e.g. P12's 10,000
    component permutations, RUN_PLAN.md:1139)."""
    return {**PLANT_K, **PLANT_K_OVERRIDES.get(plant_name or "", {})}


def parse_K(text: str | None, plant: bool, plant_name: str | None = None) -> dict:
    """--K: '' / None -> the run's base (audit K, or the plant's K: plant_K(plant_name)); 'audit'; 'plant' (the
    plant's K, overrides included); 'key=value,...' on that base (an explicit override, e.g. permutation=500)."""
    base = plant_K(plant_name) if plant else dict(AUDIT_K)
    if text in (None, ""):
        return base
    if text == "audit":
        return dict(AUDIT_K)
    if text == "plant":
        return plant_K(plant_name)
    for part in text.split(","):
        k, sep, v = part.partition("=")
        if not sep or k not in base or not re.fullmatch(r"[1-9][0-9]*", v):
            raise ValueError(f"--K: {part!r} (keys {sorted(base)})")
        base[k] = int(v)
    return base


def parse_plant(text: str | None) -> tuple[str, int] | None:
    """(plant name, integer plant_id) of a ROW-KEYED plant run by this module: P<n> -> n (seeds.plant_int). Lettered
    ids (P3a / P3b) are WP2 battery plants, accepted only for the hand-off to a1_audit.plants.driver (plants_handoff);
    here they are refused, as is any other non-P<n> id (NotImplementedError, as before)."""
    if text is None:
        return None
    if text in SD.LETTERED_PLANTS:
        raise NotImplementedError(f"plant id {text!r}: a lettered plant runs through the WP2 plants driver only "
                                  "(a1_audit.plants.driver; run.plants_handoff)")
    try:
        return text, SD.plant_int(text)
    except ValueError as e:
        raise NotImplementedError(f"plant id {text!r}: {e} (RUN_PLAN §7 :1121-1122)") from None


# ---- the WP2 plant battery: hand-off to a1_audit.plants.driver ----------------------------------------------------
HANDOFF_DRIVER = "a1_audit.plants.driver"
HANDOFF_RULE = ("ORCHESTRATOR DECISION (2026-10-02): RUN_PLAN §7 :1089 'every plant runs through the production code "
                "path (a1_audit.run, flag --plant)'; a plant of the WP2 battery (a1_audit.plants.driver.ORDER) has no "
                "TSV row, so `a1_audit.run --plant <id>` hands it to the driver (which calls run.prepare / run.g_legs / "
                "verdict.assemble_verdict_a1 / run.g_tabs / run.g_descriptors); row-keyed plants (P2, and any P<n> "
                "outside the battery) stay on this module's --plant path")
HANDOFF_RUN_ONLY = ("pass_", "gate", "rows", "K", "g6l", "case", "dry")   # run.py options the driver does not take


def driver_order() -> tuple:
    """a1_audit.plants.driver.ORDER (the WP2 battery's plant ids)."""
    return tuple(importlib.import_module(HANDOFF_DRIVER).ORDER)


def handoff_argv(argv: list) -> list | None:
    """The plants driver's argv when --plant names a WP2 battery plant (driver_order), else None (P2 and other
    row-keyed plants, real runs). Forwarded: the plant, --commit, --jobs, --dev, --out, --estimate (the driver's
    no-launch cost estimate). A run.py-only option given with a battery plant is refused (RunRefused), never ignored."""
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--plant", default=None)
    a, _ = pre.parse_known_args(argv)
    if a.plant is None or a.plant == SD.P2_CLAIM_KEYS or a.plant not in driver_order():
        return None
    ap = argparse.ArgumentParser(prog="python -m a1_audit.run --plant <WP2 battery plant>", add_help=False)
    for name in ("--plant", "--commit", "--out", "--pass", "--gate", "--rows", "--K", "--g6l", "--case"):
        ap.add_argument(name, default=None, dest=None if name != "--pass" else "pass_")
    ap.add_argument("--jobs", type=int, default=20)
    for name in ("--dev", "--dry", "--estimate"):
        ap.add_argument(name, action="store_true")
    h, rest = ap.parse_known_args(argv)
    given = [k for k in HANDOFF_RUN_ONLY if getattr(h, k) not in (None, False)]
    if rest or given:
        raise RunRefused(f"--plant {h.plant} is a WP2 battery plant (a1_audit.plants.driver): run.py-only option(s) "
                         f"{', '.join(given + rest)} not taken by the driver")
    out = [h.plant]
    if h.commit:
        out += ["--commit", h.commit]
    out += ["--jobs", str(h.jobs)]
    if h.dev:
        out.append("--dev")
    if h.out:
        out += ["--out", h.out]
    if h.estimate:
        out.append("--estimate")
    return out


def plants_handoff(argv: list) -> int | None:
    """HANDOFF_RULE: the driver's exit code for a WP2 battery plant, None otherwise (this module runs the request)."""
    try:
        dargv = handoff_argv(argv)
    except RunRefused as e:
        print(ascii_line(f"a1_audit.run: refused: {e.code}"), flush=True)
        return 2
    if dargv is None:
        return None
    print(ascii_line(f"a1_audit.run: --plant {dargv[0]} is a WP2 battery plant: handed off to {HANDOFF_DRIVER} "
                     "(RUN_PLAN §7 :1089)"), flush=True)
    return int(importlib.import_module(HANDOFF_DRIVER).main(dargv))


def parse_cases(text: str | None, plant: tuple | None) -> list:
    """B3: --case N or A-B (inclusive) -> the plant cases, each in the plant's range (seeds.check_plant_case). A real
    run and P2 (the declared exception: claim keys) take no case -> [None]; every other plant must name its case(s)."""
    if plant is None or plant[0] == SD.P2_CLAIM_KEYS:
        if text not in (None, ""):
            raise ValueError("--case is for plant runs other than P2 (P2 keeps the claim keys; a real run has no case)")
        return [None]
    if text in (None, ""):
        raise ValueError(f"plant {plant[0]}: name its case(s) with --case N or A-B (B3: leg streams within a plant case)")
    m = re.fullmatch(r"([0-9]+)(?:-([0-9]+))?", text)
    if not m:
        raise ValueError(f"--case: {text!r} (N or A-B)")
    a, b = int(m.group(1)), int(m.group(2) or m.group(1))
    if b < a:
        raise ValueError(f"--case: {text!r}")
    return [SD.check_plant_case(plant[0], c) for c in range(a, b + 1)]


@functools.lru_cache(maxsize=4)
def main_repository(repo: Path = REPO) -> Path:
    """C3 (RUN_PLAN §2.3 :327-328: "Outputs are written under the main repository's arcs/audit/results/a1_run/"): the
    main working tree of `repo`'s repository, found through git's common dir (`git rev-parse --git-common-dir` is
    <main>/.git for the main tree and for every linked worktree). Equal to `repo` in the main tree itself."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                       capture_output=True, env=env, timeout=60)
    if r.returncode != 0:
        raise RuntimeError("main_repository: git rev-parse --git-common-dir failed")
    common = Path(r.stdout.decode("utf-8").strip()).resolve()
    if common.name != ".git" or not common.is_dir():
        raise RuntimeError(f"main_repository: git's common dir is not <main>/.git ({common.name})")
    main = common.parent
    top = subprocess.run(["git", "-C", str(main), "rev-parse", "--path-format=absolute", "--show-toplevel"],
                         capture_output=True, env=env, timeout=60)
    if top.returncode != 0 or Path(top.stdout.decode("utf-8").strip()).resolve() != main.resolve():
        raise RuntimeError("main_repository: the common dir's parent is not the main working tree")
    if not (main / LD.TSV_PATH).is_file():
        raise RuntimeError("main_repository: the main working tree lacks the register TSV")
    return main.resolve()


def register_for_diagnostics(repo: Path = REPO) -> list:
    """The TSV's rows for a diagnostic (no launch): the bytes must equal the L2 pin (as loader.load asserts)."""
    data = LD.lf((Path(repo) / LD.TSV_PATH).read_bytes())
    if sha256_bytes(data) != LD.TSV_SHA256:
        raise RuntimeError("TSV bytes differ from the L2 pin")
    _, rows = LD.parse_tsv_bytes(data)
    if len(rows) != LD.N_ROWS:
        raise RuntimeError("TSV row count differs")
    return rows


def dry_dispatch(rows, open_gates=frozenset(), *, plant_view: bool = False, sources: Sources | None = None) -> list:
    """Every row through the dispatcher without a statistic: classify, run stubs (each must raise its named
    NotImplementedError), check preconditions and the sources (real sources refuse). Returns one record per row;
    an unexpected exception propagates (the caller counts it)."""
    sources = sources or RealSources()
    out = []
    for row in rows:
        p = classify(row, open_gates, plant_view=plant_view)
        rec = dict(row=p["row"], route=p["route"], kind=p["kind"], index_forms=p["index_forms"], outcome=None,
                   status=None)
        if p["kind"] == "no statistic":
            rec.update(outcome="no statistic", status=p["status_written"])
        elif p["kind"] == "refused":
            rec.update(outcome="refused", status=p["status_written"])
        elif p["kind"] == "stub":
            try:
                run_stub(p["stub"], p)
                raise RuntimeError(f"stub {p['stub']} did not raise")
            except NotImplementedError as e:
                if str(e) != STUBS[p["stub"]]:
                    raise
                rec.update(outcome="stub", status=f"not run (stub: {e})")
        elif p["kind"] == "form":   # WP2: signed-weight (P15) / gene-set-only (R10)
            rec.update(_probe_form(p, plant_view, sources))
        else:
            st, notes = check_preconditions(p, plant_view)
            if st is not None:
                rec.update(outcome="refused" if st.startswith("refused") else "not run", status=st)
            else:
                try:
                    p = resolve_class(p, sources)
                    sources.context(p["analysis_class"])
                    sources.map(p, p["maps"][0])
                    if p["has_set"] and p["form"] in FULL_FORMS:
                        sources.gene_set(p)
                    rec.update(outcome="would compute", status="sources available")
                except SourceUnavailable as e:
                    rec.update(outcome="not run", status=e.status)
        out.append(rec)
    return out


def dispatch_counts(recs: list) -> dict:
    by_route, by_outcome, by_status, forms = {}, {}, {}, {"map": {}, "cell": {}}
    for r in recs:
        by_route[r["route"]] = by_route.get(r["route"], 0) + 1
        by_outcome[r["outcome"]] = by_outcome.get(r["outcome"], 0) + 1
        if r["outcome"] != "would compute":
            key = r["status"] if r["outcome"] != "no statistic" else r["route"]
            by_status[key] = by_status.get(key, 0) + 1
        for k in ("map", "cell"):
            f = r["index_forms"][k]
            forms[k][f] = forms[k].get(f, 0) + 1
    return dict(n=len(recs), by_route=dict(sorted(by_route.items())), by_outcome=dict(sorted(by_outcome.items())),
                no_statistic_by_status=dict(sorted(by_status.items())), index_forms=forms)


def dev_guard_not_run(path) -> dict:
    return {"status": "not run (dev run: the privacy guard self-test reads the HGNC table under E:\\data\\asdg\\, "
                      "which no dev run opens; U15)"}


def _under(p: Path, root: Path) -> bool:
    p, root = p.resolve(), root.resolve()
    return p == root or root in p.parents


class Run:
    """One pass of the runner (state shared by the steps)."""

    def __init__(self, args, launch_record: dict, refused: list, case: int | None = None):
        self.args = args
        self.pass_ = args.pass_
        self.gate_arg = args.gate
        self.gate_dir = GATE_DIR[args.gate]
        self.launch_record = launch_record
        self.refused = refused
        self.dev = bool(args.dev)
        self.plant = parse_plant(args.plant)
        self.plant_view = self.plant is not None
        self.stamp = ("DEV (launch refused: %s)" % ", ".join(refused)) if self.dev else None
        if self.dev and not refused:
            self.stamp = "DEV (launch passed; dev run)"
        self.K = parse_K(args.K, self.plant_view, self.plant[0] if self.plant else None)
        self.K_overrides = ({k: v for k, v in PLANT_K_OVERRIDES.get(self.plant[0], {}).items() if self.K.get(k) == v}
                            if self.plant else {})
        self.g6l_mode = args.g6l or (PM.MODE_PLANT if self.plant_view else PM.MODE_EXACT)
        # B3: a plant case (P2 and real runs: none; then the claim keys)
        if case is not None and (not self.plant_view or self.plant[0] == SD.P2_CLAIM_KEYS):
            raise RunRefused("a case is for plant runs other than P2")
        if self.plant_view and self.plant[0] != SD.P2_CLAIM_KEYS and case is None:
            raise RunRefused(f"plant {self.plant[0]}: a plant case is required (B3)")
        self.case = None if case is None else SD.check_plant_case(self.plant[0], case)
        self.seed_view = (None if self.case is None else
                          dict(kind="plant", plant=self.plant[0], plant_id=int(self.plant[1]), case=int(self.case)))
        case_dir = () if self.case is None else (f"case_{self.case:06d}",)
        self.out_root = None if self.dev else main_repository(REPO)   # C3: the main repository's tree
        self.rerun_tag = getattr(args, "rerun_tag", None)               # WP4 (§17): a rerun's own output folder
        if self.dev:
            out = Path(args.out).resolve()
            self.results_dir = out.joinpath(*case_dir, self.gate_dir, self.pass_)
            self.ck_root = out.joinpath("_ck", *case_dir, self.gate_dir)
            no_data = out / "_no_such_data_dir"
        elif self.plant_view:
            self.results_dir = (self.out_root / PLANTS_REL / self.plant[0]).joinpath(*case_dir, self.gate_dir,
                                                                                    self.pass_)
            self.ck_root = (self.out_root / CK_PLANT_REL / self.plant[0]).joinpath(*case_dir, self.gate_dir)
            no_data = self.out_root / CK_PLANT_REL / "_no_such_data_dir"
        else:
            tag = () if not self.rerun_tag else (f"rerun_{self.rerun_tag}",)
            self.results_dir = (self.out_root / RESULTS_REL).joinpath(*tag, self.gate_dir, self.pass_)
            self.ck_root = (self.out_root / CK_REAL_REL).joinpath(*tag, self.gate_dir)
            no_data = None
        self.ck_dir = self.ck_root / self.pass_
        self.verdict_results = self.results_dir.parent / "verdict"
        self.sources: Sources = (SyntheticSources(self.plant[1], no_data, case=self.case) if self.plant_view
                                 else _real_sources(self.out_root, self.gate_arg))
        self.log = Log(self.results_dir / "run.log", "DEV " if self.dev else "")
        self.code_hash = ((self._a("L11").get("observed") or {}).get("code_hash")) or "unknown"
        self.open_gates = LD.open_gates_from(launch_record)
        self._prov = None
        self.pacer = None          # pace.Pacer (main: a real pass, or a dev pass given --block-estimates)
        self.pauses = []           # this pass's pause / resume events (pace.PAUSES_FILE), set by main
        self._form_store = None

    def form_store(self):
        """The forms' checkpoint store (<ck>/forms; one RUN.json per pass)."""
        if self._form_store is None:
            spec = self.sources.spec()
            store = A3.Checkpoints(self.ck_dir / "forms", self.code_hash, f"{DRIVER}:{self.pass_}:forms")
            ident = {k: v for k, v in spec.items() if k != "no_data_dir"}
            store.run_record(dict(run_commit=self.launch_record.get("run_commit"), code_hash=self.code_hash,
                                  pass_name=self.pass_, gate=self.gate_arg, K=self.K, sources=ident, stamp=self.stamp))
            self._form_store = store
        return self._form_store

    def pause_identity(self) -> dict:
        """What a pause belongs to: this pass's block under this run commit and code hash."""
        return dict(run_commit=self.launch_record.get("run_commit"), code_hash=self.code_hash,
                    block=f"{self.gate_dir}/{self.pass_}")

    def identity(self) -> dict:
        """C5: what a verdict-pass file must share with a later descriptor / sensitivity pass (RUN_IDENTITY_FIELDS)."""
        spec = self.sources.spec()
        return dict(run_commit=self.launch_record.get("run_commit"), code_hash=self.code_hash, K=dict(self.K),
                    g6l_mode=self.g6l_mode, sources={k: v for k, v in spec.items() if k != "no_data_dir"},
                    seed_view=self.seed_view)

    def _a(self, aid):
        hits = [a for a in self.launch_record.get("assertions", []) if a.get("id") == aid]
        return hits[0] if len(hits) == 1 else {}

    # -- provenance --------------------------------------------------------------------------------------------------
    def provenance(self) -> dict:
        if self._prov is None:
            if not self.refused and not self.dev:
                self._prov = LA.provenance_block(self.launch_record, REPO)
            else:
                l11 = self._a("L11")
                mods, _ = LA.code_modules(REPO)
                now = {rel: LA.sha256_bytes(LA.lf(p.read_bytes())) for rel, p in mods.items()}
                envs = (self._a("L7").get("detail") or {}).get("environments")
                self._prov = {
                    "DEV": self.stamp, "run_commit": self.launch_record.get("run_commit"), "worktree": str(REPO),
                    "plan_sha256": self.launch_record.get("plan_sha256"),
                    "amendment_sha256": self.launch_record.get("amendment_sha256"),
                    "environments": envs, "matrix_first_use": LA.first_use_records(),
                    "gate": self.launch_record.get("gate"),
                    "code": {"modules": (l11.get("observed") or {}).get("modules"),
                             "code_hash": (l11.get("observed") or {}).get("code_hash")},
                    "code_now": {"modules": now, "code_hash": LA.code_hash(now),
                                 "note": "dev run: modules are not committed, so launch.recheck_code is not applied"},
                    "launch_assertions": [dict(a) for a in self.launch_record.get("assertions", [])],
                    "launch_failed": list(self.refused), "gate_check": dict(self._a("L15")),
                    "launch_started": self.launch_record.get("started"),
                    "launch_finished": self.launch_record.get("finished"), "host": self.launch_record.get("host")}
        return self._prov

    def header(self) -> dict:
        plant = None if self.plant is None else {"id": self.plant[0], "plant_id": self.plant[1],
                                                 "sources": self.sources.spec()}
        mode_text = PM.MODE_TEXT if self.g6l_mode == PM.MODE_PLANT else "exact (every gene screened; RUN_PLAN §4)"
        if plant is not None:
            plant.update(case=self.case, seed_view=self.seed_view or dict(kind="claim", rule=(
                "P2-only exception: P2's purpose is the claim keys (RUN_PLAN §7 :1128)")))
        return {"what": "A1 run result, one row x pass (RUN_PLAN v3.1 §16; provenance §2.4)", "stamp": self.stamp,
                "pass": self.pass_, "gate": self.gate_arg, "plant": plant, "K": self.K, "g6l_mode": self.g6l_mode,
                "K_plant_overrides": ({k: dict(value=v, source=PLANT_K_OVERRIDE_SOURCES.get(self.plant[0]))
                                       for k, v in self.K_overrides.items()} or None),
                "g6l_mode_text": mode_text, "threads": {k: os.environ.get(k) for k in _THREAD_VARS},
                "threads_before": THREAD_ENV_BEFORE, "run_identity": self.identity(),
                "output_root": "dev --out" if self.dev else str(self.out_root),
                **({"rerun_tag": self.rerun_tag, "rerun_rule": RERUN_RULE} if self.rerun_tag else {})}

    def write_row(self, p: dict, outcome: str, status: str | None, result=None, inputs=None, seeds=None,
                  times=None, memory=None, extra=None) -> str:
        times = times or (LA.now_iso(), LA.now_iso())
        sd = seeds or {"row": p["row"], "target_number": p["target_no"], "legs": [],
                       "note": "no statistic: no seed drawn"}
        rp = LA.row_provenance(p["row"], p["target_no"], sd, (inputs or {}).get("hashes", {}), times[0], times[1])
        rec = dict(self.header())
        rec.update(row=p["row"], target_number=p["target_no"], cell_id=p["cell_id"], claim_form=p["claim_form"],
                   gate_column=p["gate"], status_tsv=p["status_tsv"], status_effective=p["status_effective"],
                   view=p["view"], route=p["route"], outcome=outcome, status_written=status,
                   descriptor=p["descriptor"], label=p["label"], in_m=p["in_m"], index_forms=p["index_forms"],
                   result=result, inputs=inputs, memory=memory, provenance=self.provenance(), row_provenance=rp)
        if extra:
            rec.update(extra)
        return write_json_atomic(self.results_dir / f"row_{p['row']:04d}.json", rec)


def _rows_for(run: Run, rows: list) -> list:
    """U3: a real run takes the rows of its gate (G1+G2 in the G1 run); a plant run takes the rows named."""
    want = parse_rows(run.args.rows)
    if run.plant_view:
        if want is None:
            raise RunRefused("a plant run names its rows (--rows)")
        return [r for r in rows if r.row in set(want)]
    gate_rows = [r for r in rows if r.gate == run.gate_arg or (run.gate_arg == "G1" and r.gate == "G1+G2")]
    return [r for r in gate_rows if want is None or r.row in set(want)]


def _verdict_record(run: Run, row: int) -> dict | None:
    f = run.verdict_results / f"row_{row:04d}.json"
    if not f.is_file():
        return None
    doc = json.loads(f.read_bytes().decode("utf-8"))
    if doc.get("outcome") != "computed" or not doc.get("result"):
        return None
    doc["_sha256"] = sha256_bytes(f.read_bytes())
    return doc


def _canon_json(o):
    return json.loads(json.dumps(A3.jsonable(o), sort_keys=True))


def verdict_identity_mismatch(run: Run, vrec: dict) -> list:
    """C5: the RUN_IDENTITY_FIELDS in which a verdict-pass file's run identity differs from this run's (run commit,
    code hash, K, G6l mode, sources, seed view); [] if equal. A file without a run identity differs in every field."""
    theirs = vrec.get("run_identity") if isinstance(vrec.get("run_identity"), dict) else {}
    mine = _canon_json(run.identity())
    return [k for k in RUN_IDENTITY_FIELDS if _canon_json(theirs.get(k)) != mine.get(k)]


def execute(run: Run, rows: list) -> dict:
    log = run.log
    log(f"pass {run.pass_} gate {run.gate_arg} rows {len(rows)} K {run.K} g6l {run.g6l_mode}"
        + (f" [{run.stamp}]" if run.stamp else ""))
    plans = [classify(r, run.open_gates, plant_view=run.plant_view) for r in rows]
    counts: dict[str, int] = {}
    files: dict[int, str] = {}

    def note(outcome):
        counts[outcome] = counts.get(outcome, 0) + 1

    compute, form_jobs = [], []
    for p in plans:
        if p["kind"] == "no statistic":
            files[p["row"]] = run.write_row(p, "no statistic", p["status_written"])
            note("no statistic")
            if run.pass_ == "verdict" and p["target_no"] == 1:
                # RUN_PLAN_amend_3 R47 (h): SEG-C3b / d (rows 4, 6; no T) get their descriptive comparison too (its
                # record beside the row's; the row's status is written above and never read back from it: B6)
                _write_repro(run, p)
            continue
        if p["kind"] == "refused":
            files[p["row"]] = run.write_row(p, "refused", p["status_written"])
            note("refused")
            continue
        if p["kind"] == "stub":
            try:
                run_stub(p["stub"], p)
                raise RuntimeError("stub did not raise")
            except NotImplementedError as e:
                files[p["row"]] = run.write_row(p, "stub", f"not run (stub: {e})")
            note("stub")
            continue
        if p["kind"] == "form":   # WP2: signed-weight (P15) / gene-set-only (R10), forms.py
            fj = _form_job(run, p, note)    # pre-WP4: computed rows join the pass's pool (phase 2)
            if isinstance(fj, str):
                files[p["row"]] = fj
            else:
                form_jobs.append(fj)
            continue
        if p.get("rlm") and run.pass_ == "verdict":   # R28's RLM (forms.py U-F6): its own record beside the row's
            _write_rlm(run, p)
        if run.pass_ == "descriptor" and p["component"] is not None:
            files[p["row"]] = run.write_row(p, "no statistic", NO_DESCRIPTOR_COMPONENT)
            note("no statistic")
            continue
        st, notes = check_preconditions(p, run.plant_view)
        if st is not None:
            files[p["row"]] = run.write_row(p, "refused" if st.startswith("refused") else "not run", st)
            note("refused" if st.startswith("refused") else "not run")
            continue
        try:
            p = resolve_class(p, run.sources)
        except SourceUnavailable as e:
            files[p["row"]] = run.write_row(p, "not run", e.status)
            note("not run")
            continue
        if "analysis_class_tsv" in p:
            notes.append(PLANT_CLASS_NOTE % p["analysis_class"])
        if run.seed_view is not None:   # B3: a plant case's leg keys (real runs and P2: the claim keys)
            p = dict(p, seed_view=dict(run.seed_view))
        vrec = None
        if run.pass_ in ("descriptor", "sensitivity"):
            vrec = _verdict_record(run, p["row"])
            if vrec is None:
                files[p["row"]] = run.write_row(p, "not run", NOT_RUN_VERDICT_ABSENT)
                note("not run")
                continue
            bad = verdict_identity_mismatch(run, vrec)   # C5: never another run's d* / screens
            if bad:
                files[p["row"]] = run.write_row(p, "refused", REFUSED_VERDICT_IDENTITY % ", ".join(bad))
                note("refused")
                continue
        rule = "donors>=2" if run.pass_ == "sensitivity" else "primary"
        try:
            preps = {mi: prepare(p, run.sources, mi, rule) for mi in p["maps"]}
        except SourceUnavailable as e:
            files[p["row"]] = run.write_row(p, "not run", e.status, extra={"source_detail": e.what})
            note("not run")
            continue
        except NotTestableAtUse as e:
            files[p["row"]] = run.write_row(p, "no statistic", e.status)
            note("no statistic")
            continue
        if run.pass_ == "sensitivity":
            prim = {int(k): v for k, v in (vrec.get("inputs") or {}).get("parcel_ids", {}).items()}
            if all(prim.get(mi) == [int(i) for i in preps[mi].parcel_ids] for mi in p["maps"]):
                files[p["row"]] = run.write_row(p, "computed", PARCELS_UNCHANGED,
                                                result=dict(sensitivity="R11 >= 2-donor parcel set",
                                                            parcel_set="unchanged",
                                                            primary_result_sha256=sha256_json(vrec["result"])),
                                                inputs=_inputs(preps, p))
                note("computed")
                continue
        compute.append(dict(plan=p, preps=preps, notes=notes, vrec=vrec))
    log(f"dispatch: {len(compute)} row(s) to compute; written so far {dict(sorted(counts.items()))}")
    if form_jobs:
        log(f"dispatch: {len(form_jobs)} form row(s) to compute (forms.py; in the phase-2 pool)")
    if compute or form_jobs:
        _compute(run, compute, files, note, form_jobs)
        if run.pass_ == "verdict":       # WP3: reproduction records of the computed ungated rows (Segura, Moreau)
            for c in compute:            # WP4: and of the computed G2 rows (wp4_repro; _write_repro gates by sources)
                if c["plan"]["target_no"] in (1, 18) or c["plan"].get("gate") == "G2":
                    _write_repro(run, c["plan"])
    summary = dict(run.header())
    cov = code_coverage(run)
    summary.update(what="A1 run summary (one pass)", n_rows=len(rows), outcomes=dict(sorted(counts.items())),
                   routes=_count_by(plans, "route"), files={str(k): v for k, v in sorted(files.items())},
                   launch_failed=run.refused, provenance=run.provenance(), code_coverage=cov,
                   pacing=pacing_summary(run))
    write_json_atomic(run.results_dir / "RUN_SUMMARY.json", summary)
    log(f"done: outcomes {dict(sorted(counts.items()))}")
    if cov.get("loaded_not_in_launch_hash"):
        log("DEFECT: module(s) loaded during the pass are not in the launch's code hash: "
            + ", ".join(cov["loaded_not_in_launch_hash"]))
        raise LA.ProvenanceError("code coverage: a module the pass loaded is in no code hash (RUN_SUMMARY.json)")
    return summary


def code_coverage(run: "Run") -> dict:
    """Pre-WP4 (§17; WP3 verification residue): every repository module loaded by the end of the pass must be in the
    launch's L11 code hash (main preloads PASS_MODULES before the launch). A pass whose launch did not pass (dev) has
    no L11 hash to cover: recorded as not applicable."""
    l11 = (run._a("L11").get("observed") or {}).get("modules")
    if run.refused or run.dev or not isinstance(l11, dict):
        return dict(status="not applicable (no passed launch: dev run)", loaded_not_in_launch_hash=[])
    mods, foreign = LA.code_modules(REPO)
    missing = sorted(set(mods) - set(l11))
    return dict(status="ok" if not (missing or foreign) else "DEFECT", n_launch_hashed=len(l11), n_loaded=len(mods),
                loaded_not_in_launch_hash=missing + sorted(foreign), rule=CODE_COVERAGE_RULE)


def pacing_summary(run: "Run") -> dict | None:
    pc = run.pacer
    est = run.launch_record.get("block_estimates")
    if pc is None and not est:
        return None
    return dict(block_estimates=est, block=None if pc is None else pc.block,
                estimate_process_h=None if pc is None else pc.estimate_h,
                threshold_process_h=None if pc is None else pc.threshold_s / 3600.0,
                process_h_checkpointed=None if pc is None else pc.cum_s / 3600.0,
                armed=None if pc is None else pc.armed, pauses=list(run.pauses), rule=PACE.PAUSE_RULE)


def _count_by(plans, key) -> dict:
    out: dict = {}
    for p in plans:
        out[p[key]] = out.get(p[key], 0) + 1
    return dict(sorted(out.items()))


def _inputs(preps: dict, p: dict) -> dict:
    hashes = {}
    for mi, pr in preps.items():
        for k, v in pr.hashes.items():
            hashes[k if k.startswith("map[") or len(preps) == 1 else f"{k} (map {mi})"] = v
    return dict(hashes=dict(sorted(hashes.items())),
                parcel_ids={str(mi): [int(i) for i in pr.parcel_ids] for mi, pr in preps.items()},
                analysis_parcels={str(mi): {k: v for k, v in pr.parcels.items()} for mi, pr in preps.items()},
                set=next(iter(preps.values())).set_info, analysis_class=p["analysis_class"],
                rule=next(iter(preps.values())).rule)


def _verdict_ck_identity_ok(run: Run, vck: Path, head: dict) -> bool:
    """C5: the verdict pass's checkpoint directory belongs to this run (its RUN.json's run commit, code hash, K, G6l
    mode and sources equal this pass's head); only then are its G6l screens reused (U12)."""
    f = Path(vck) / "RUN.json"
    if not f.is_file():
        return False
    try:
        old = json.loads(f.read_text(encoding="utf-8"))
    except ValueError:
        return False
    keys = ("run_commit", "code_hash", "K", "g6l_mode", "sources")
    return all(_canon_json(old.get(k)) == _canon_json(head.get(k)) for k in keys)


def _compute(run: Run, compute: list, files: dict, note, form_jobs: list = ()) -> None:
    log, K, spec = run.log, run.K, run.sources.spec()
    pacer = run.pacer   # RUN_PLAN §14 overrun (pace.py): None = not paced (plant / dry / dev without estimates)
    rule = "donors>=2" if run.pass_ == "sensitivity" else "primary"
    screens: dict[str, dict] = {}   # stream name -> (screen record, ck dir)
    jobs2: list = []
    tasks2: list = []
    if compute:
        store = A3.Checkpoints(run.ck_dir, run.code_hash, f"{DRIVER}:{run.pass_}")
        ident = {k: v for k, v in spec.items() if k != "no_data_dir"}  # a path is not part of the run's identity
        head = dict(run_commit=run.launch_record.get("run_commit"), code_hash=run.code_hash, pass_name=run.pass_,
                    gate=run.gate_arg, K=K, g6l_mode=run.g6l_mode, sources=ident, stamp=run.stamp,
                    rows=sorted(c["plan"]["row"] for c in compute))
        store.run_record(head)
        # ---- phase 1: G6l screens per (S, class, parcels) -----------------------------------------------------
        triples: dict[str, list] = {}
        for c in compute:
            p = c["plan"]
            if p["form"] not in FULL_FORMS:
                continue
            legs = []
            if run.pass_ in ("verdict", "sensitivity"):
                legs.append(5)
                if run.pass_ == "verdict" and p["t_abs"]:
                    legs.append(25)
            elif p["t_abs"]:
                legs.append(25)
            for mi in p["maps"]:
                for leg in legs:
                    triples.setdefault(c["preps"][mi].triple, []).append((p, mi, leg))
        vck = run.ck_root / "verdict"
        vrun_ok = run.pass_ == "descriptor" and _verdict_ck_identity_ok(run, vck, head)   # C5: that pass's RUN.json
        if run.pass_ == "descriptor" and not vrun_ok and triples:
            log("U12: the verdict pass's checkpoint RUN.json is absent or of another run (C5): screens recomputed")
        if vrun_ok:  # U12: leg 25 from the verdict pass's shared screen when it exists
            for tri in list(triples):
                f = vck / f"ck_g6l_{tri[:16]}.json"
                if f.is_file():
                    doc = json.loads(f.read_text(encoding="utf-8"))
                    pay = doc.get("payload") or {}
                    if doc.get("code_hash") == run.code_hash and pay.get("triple") == tri \
                            and pay.get("mode") == run.g6l_mode \
                            and (doc.get("expect") or {}).get("K_species") == int(K["species"]):
                        have = pay.get("streams") or {}
                        need = [stream_name(p["row"], mi, leg) for p, mi, leg in triples[tri]]
                        if all(n in have for n in need):
                            for n in need:
                                screens[n] = dict(rec=have[n], dir=str(vck), source="verdict pass shared screen")
                            del triples[tri]
        tasks1 = []
        for tri, streams in triples.items():
            key = f"g6l_{tri[:16]}"
            expect = dict(triple=tri, mode=run.g6l_mode, K_species=int(K["species"]),
                          streams={stream_name(p["row"], mi, leg): SD.key_record(stream_seed(p, mi, leg))
                                   for p, mi, leg in streams})
            tasks1.append((key, expect, dict(group="g6l", streams=streams, triple=tri, sources=spec, rule=rule,
                                             g6l_mode=run.g6l_mode, K=K, ck_dir=str(run.ck_dir))))
        if tasks1:
            log(f"phase 1: {len(tasks1)} G6l screen(s) ({run.g6l_mode} mode)")
            got = PACE.run_jobs([PACE.Job(k, e, kw, store, task) for k, e, kw in tasks1], run.args.jobs, log=log,
                                pacer=pacer, name="phase 1 (G6l screens)")
            for key, _, kw in tasks1:
                meta = got[key].get("_meta") or {}
                if (meta.get("memory") or {}).get("defect"):
                    log(f"DEFECT G6l screen {key}: a job above 2.5 GB (RUN_PLAN §4 memory)")
                for n, rec in got[key]["streams"].items():
                    screens[n] = dict(rec=rec, dir=str(run.ck_dir), meta=meta,
                                      source="this pass's screen" + (" (verdict pass screen absent)"
                                                                     if run.pass_ == "descriptor" else ""))
        # ---- phase 2: leg groups --------------------------------------------------------------------------------
        order = {"descriptors": 0, "legs": 1, "tabs": 2}
        for c in compute:
            p = c["plan"]
            if run.pass_ in ("verdict", "sensitivity"):
                groups = VERDICT_GROUPS
            else:
                groups = DESCRIPTOR_GROUPS + (("tabs",) if p["t_abs"] else ())
            for mi in p["maps"]:
                pr = c["preps"][mi]
                for g in groups:
                    key = f"r{p['row']:04d}_m{mi}_{g}"
                    kw = dict(group=g, plan=p, sources=spec, map_index=mi, rule=rule, K=K, expect_hashes=pr.hashes,
                              parcel_ids=[int(i) for i in pr.parcel_ids])
                    expect = dict(group=g, seeds=group_seed_keys(p, mi, g, pr.adapter), inputs=pr.hashes, rule=rule,
                                  parcels=sha256_json(kw["parcel_ids"]), K=K, g6l_mode=run.g6l_mode)
                    if (g == "legs" and p["form"] in FULL_FORMS) or g == "tabs":
                        n = stream_name(p["row"], mi, 5 if g == "legs" else 25)
                        s = screens[n]
                        kw.update(screen=s["rec"], screen_dir=s["dir"])
                        expect["screen_sha256"] = s["rec"]["sha256"]
                    if g == "descriptors":
                        _, tsha = run.sources.trajectories(p["analysis_class"])
                        v = c["vrec"]["result"]["verdict"]
                        direction = v.get("d_star") if p["two_sided"] else p["registered_direction"]
                        kw.update(traj_sha=tsha, direction=direction, two_sided=bool(p["two_sided"]))
                        expect.update(traj_sha=tsha, direction=direction, two_sided=bool(p["two_sided"]))
                    tasks2.append((order[g], key, expect, kw))
        tasks2.sort(key=lambda t: t[0])  # costliest groups first (longest-processing-time order, §14)
        jobs2 = [PACE.Job(k, e, kw, store, task) for _, k, e, kw in tasks2]
    # pre-WP4 (RUN_PLAN §4 memory, §14): the form rows (one task each; hours at audit K) lead the phase-2 batch in the
    # pool (longest-processing-time order); the WP3 run computed them one by one in the parent process
    jobs2 = [fj["job"] for fj in form_jobs] + jobs2
    log(f"phase 2: {len(tasks2)} leg-group task(s)" + (f" + {len(form_jobs)} form row(s)" if form_jobs else "")
        + f", jobs {run.args.jobs}")
    got = PACE.run_jobs(jobs2, run.args.jobs, log=log, pacer=pacer, name="phase 2 (leg groups and form rows)")
    for fj in form_jobs:
        files[fj["plan"]["row"]] = _form_finish(run, fj, got[fj["job"].key], note)
    # ---- assembly ----------------------------------------------------------------------------------------------
    for c in compute:
        p = c["plan"]
        try:
            res, seeds, times, mem = _assemble_row(run, c, got, screens)
        except Exception as e:  # a code defect: recorded and raised after the row is written
            files[p["row"]] = run.write_row(p, "refused", f"refused: assembly raised {type(e).__name__}",
                                            inputs=_inputs(c["preps"], p))
            note("refused")
            raise
        extra = {"notes": c["notes"]} if c["notes"] else {}
        if c["vrec"] is not None:
            extra["verdict_file_sha256"] = c["vrec"]["_sha256"]
        files[p["row"]] = run.write_row(p, "computed", None, result=res, inputs=_inputs(c["preps"], p),
                                        seeds=seeds, times=times, memory=mem, extra=extra or None)
        note("computed")
        if mem.get("defect"):
            log(f"DEFECT row {p['row']}: a job above 2.5 GB (RUN_PLAN §4 memory)")
        log(f"row {p['row']} ({p['route']}) written; peak task memory {mem['max_task_peak_bytes']} B")


def _assemble_row(run: Run, c: dict, got: dict, screens: dict):
    p, K = c["plan"], run.K
    metas, seeds_maps = [], []
    per_map = {}
    for mi in p["maps"]:
        pre = f"r{p['row']:04d}_m{mi}_"
        pay = {k[len(pre):]: dict(v) for k, v in got.items() if k.startswith(pre)}
        metas += [v.pop("_meta") for v in pay.values()]   # times / memory: never part of a statistic record
        uses, flags = seed_uses(p, run.pass_, c["preps"][mi].adapter)
        sr = seed_record_for(p, mi, uses, **flags)   # claim keys, or the plant case's keys (B3)
        ints = {d["leg"]: d.get("seed_int") for d in sr["legs"]}
        if run.pass_ in ("verdict", "sensitivity"):
            legs = int_dir_keys(pay["legs"]["legs"])
            for leg in ("S1c", "S2c"):  # the integer seeds used are the ones recorded (R7)
                if int(legs["site"][leg]["seed"]) != ints[leg]:
                    raise RuntimeError(f"row {p['row']}: {leg} seed used != recorded")
            ad = c["preps"][mi].adapter
            if level0_seed_leg(ad) is not None and legs["level0"]["kind"] != ad.LEVEL0_KIND:
                raise RuntimeError(f"row {p['row']}: Level-0 kind {legs['level0']['kind']!r} != the adapter's "
                                   f"{ad.LEVEL0_KIND!r} (R34)")
            per_map[mi] = legs
            per_map[mi]["_spearman"] = pay["legs"].get("spearman")
        else:
            rec = pay["descriptors"]["record"]
            if rec["J1"].get("seeds") != {"S1c": sr["J1"]["S1c_seed"], "S2c": sr["J1"]["S2c_seed"]} or \
                    rec["naive_joint"].get("seeds") != {"S1": sr["naive_joint"]["S1_seed"]}:
                raise RuntimeError(f"row {p['row']}: J1 / naive-joint seeds used != recorded (R7 order)")
            if p["t_abs"]:
                for leg in ("S1c", "S2c"):
                    if int(pay["tabs"]["legs"][leg]["seed"]) != ints[f"T_abs {leg}"]:
                        raise RuntimeError(f"row {p['row']}: T_abs {leg} seed used != recorded")
            per_map[mi] = pay
            sr["stream_fingerprints"] = pay["descriptors"]["stream_fingerprints"]
            if pay["descriptors"]["g3_key"] != sr["G3"]["key"]:
                raise RuntimeError("G3 key used != R24's key recorded")
        seeds_maps.append(sr)
    seeds = {"row": p["row"], "target_number": p["target_no"], "per_map": seeds_maps}
    if run.pass_ in ("verdict", "sensitivity"):
        kw = dict(two_sided=bool(p["two_sided"]), registered_direction=p["registered_direction"])
        spear = {mi: per_map[mi].pop("_spearman") for mi in p["maps"]}
        if p["two_cohort"]:
            res = V.two_cohort_from_legs(per_map[0], per_map[1], map_labels=("map 0 = ABIDE I", "map 1 = ABIDE II"),
                                         **kw)
        else:
            res = V.assemble_verdict_a1(per_map[p["maps"][0]], by_construction_label=p["by_construction_label"], **kw)
        res = verdict_for_plan(p, res)   # B1: a descriptor row is never a verdict (survives False; the TSV status)
        ident = {str(mi): dict(S1c=per_map[mi]["site"]["S1c"]["info"].get("identity"),
                               S2c=per_map[mi]["site"]["S2c"]["info"].get("identity"),
                               G6s=(per_map[mi].get("species") or {}).get("g6s_identity")) for mi in p["maps"]}
        res = dict(verdict=res, identity_counts=ident, identity_rule="RUN_PLAN_amend_1 R32 (a): exact enumerations "
                   "count their identity pattern (None: a sampled leg)",
                   spearman_beside_level0={str(k): v for k, v in spear.items() if v is not None} or None,
                   g6l_screen={str(mi): screens[stream_name(p["row"], mi, 5)]["source"]
                               for mi in p["maps"] if p["form"] in FULL_FORMS} or None)
        if run.pass_ == "sensitivity":
            res.update(sensitivity="R11 >= 2-donor parcel set", parcel_set="changed",
                       primary_result_sha256=sha256_json(c["vrec"]["result"]))
        if run.pass_ == "verdict" and not run.plant_view:   # §16 :1667, R27: amendment 5's labels and power columns
            scope = r27_scope(REPO)
            rp = getattr(run.sources, "reparcellated", None)
            vrec = r27_verdict_rec(res["verdict"])   # pre-WP4 review B1: a descriptor row keeps its marked reading
            res["r27"] = {str(mi): r27_for_map(c["preps"][mi], vrec, reparcellated=bool(rp(p)) if rp else False,
                                                scope=scope) for mi in p["maps"]}
    else:
        v = c["vrec"]["result"]["verdict"]
        two_sided = bool(p["two_sided"])
        direction = v.get("d_star") if two_sided else p["registered_direction"]
        res = {"direction_from_verdict": dict(d_star=v.get("d_star"), registered_direction=p["registered_direction"],
                                              two_sided=two_sided,
                                              verdict_result_sha256=sha256_json(c["vrec"]["result"])),
               "per_map": {}}
        for mi in p["maps"]:
            pay = per_map[mi]
            rec = int_dir_keys(pay["descriptors"]["record"])
            if rec.get("direction") != direction or rec.get("two_sided") != two_sided:
                raise RuntimeError(f"row {p['row']}: descriptor record's direction differs from the verdict's")
            if p["t_abs"]:
                rec["T_abs"] = int_dir_keys(pay["tabs"])
                rec["T_abs_g6l_screen"] = screens[stream_name(p["row"], mi, 25)]["source"]
            rec["stream_fingerprints"] = pay["descriptors"]["stream_fingerprints"]
            res["per_map"][str(mi)] = rec
    times = (min(m["started"] for m in metas), max(m["finished"] for m in metas))
    scr_metas = [screens[n]["meta"] for n in {stream_name(p["row"], mi, leg) for mi in p["maps"] for leg in (5, 25)}
                 if n in screens and screens[n].get("meta")]
    mems = [m["memory"] for m in metas + scr_metas]   # the row's tasks and the G6l screens serving it
    mem = dict(tasks=len(mems), method=mems[0]["method"],
               max_task_peak_bytes=max(m["task_peak_bytes"] for m in mems),
               max_process_peak_working_set_bytes=max((m["process_peak_working_set_bytes"] or 0) for m in mems) or None,
               defect=any(m["defect"] for m in mems), defect_rule=mems[0]["defect_rule"],
               seconds=round(sum(m.get("seconds", 0) for m in metas), 3), screen_tasks=len(scr_metas))
    return res, seeds, times, mem


# ================================================================================================================
# CLI
# ================================================================================================================
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m a1_audit.run", description="A1 runner (RUN_PLAN v3.1 WP1)")
    ap.add_argument("--commit", required=True, help="the run commit (L11: HEAD must equal it)")
    ap.add_argument("--pass", dest="pass_", required=True, choices=PASSES)
    ap.add_argument("--gate", required=True, choices=GATE_ARGS)
    ap.add_argument("--rows", default=None, help="e.g. 1-80,478 (a plant run must name its rows)")
    ap.add_argument("--jobs", type=int, default=20)
    ap.add_argument("--K", default=None, help="audit | plant | key=value,... (keys: %s)" % ", ".join(AUDIT_K))
    ap.add_argument("--g6l", default=None, choices=PM.MODES, help="G6l mode (plant mode only in plant runs)")
    ap.add_argument("--plant", default=None, help="plant id P<n> (P3a / P3b): synthetic sources through the "
                                                  "production path")
    ap.add_argument("--case", default=None, help="plant case(s) N or A-B (every plant but P2: its leg streams, B3)")
    ap.add_argument("--dev", action="store_true", help="with --plant: continue after a launch refusal (stamped DEV)")
    ap.add_argument("--out", default=None, help="dev runs: the only directory written (outside the repository)")
    ap.add_argument("--dry", action="store_true", help="dispatch only (no statistic)")
    ap.add_argument("--resume-after-pause", dest="resume_after_pause", default=None, metavar="DECISION",
                    help="resume a pass paused by the RUN_PLAN §14 overrun rule; DECISION = who decided and why "
                         "(recorded beside the pause)")
    ap.add_argument("--block-estimates", dest="block_estimates", default=None, metavar="JSON",
                    help="dev runs only: a block-estimate file in place of the pinned one (pace.ESTIMATES_REL)")
    ap.add_argument("--rerun-tag", dest="rerun_tag", default=None, metavar="TAG",
                    help="a real pass rerun under RUN_PLAN §17 (3): outputs under results/a1_run/rerun_<TAG>/ and "
                         "checkpoints under artifacts/audit/a1_run/rerun_<TAG>/ (the completed rows stay untouched)")
    return ap


def validate(args) -> None:
    if args.jobs < 1:
        raise RunRefused("--jobs must be >= 1")
    if args.dev and not args.plant:
        raise RunRefused("--dev needs --plant (a dev run is a plant run)")
    if args.dev and not args.out:
        raise RunRefused("--dev needs --out")
    if args.out and not args.dev:
        raise RunRefused("--out is for dev runs only")
    tag = getattr(args, "rerun_tag", None)
    if tag is not None and (args.plant or args.dev or not re.fullmatch(r"[a-z0-9][a-z0-9_]{0,39}", tag)):
        raise RunRefused("--rerun-tag is for real passes, TAG = [a-z0-9][a-z0-9_]{0,39}")
    if getattr(args, "block_estimates", None) and not args.dev:
        raise RunRefused("--block-estimates is for dev runs only (a real pass reads the pinned file)")
    rap = getattr(args, "resume_after_pause", None)
    if rap is not None and args.dry:
        raise RunRefused("--resume-after-pause resumes a computing pass, not a dry dispatch")
    if rap is not None and not (isinstance(rap, str) and rap.strip() and rap.isascii() and len(rap) <= 500):
        raise RunRefused("--resume-after-pause needs a decision string (ASCII, 1-500 characters: who / why)")
    if args.out:
        out = Path(args.out).resolve()
        for rel in FORBIDDEN_OUT:
            if _under(out, REPO / rel):
                raise RunRefused(f"--out must lie outside {rel}")
        try:
            roots = {REPO.resolve(), main_repository(REPO)}
        except RuntimeError:
            roots = {REPO.resolve()}
        if any(_under(out, root) for root in roots):   # C9: nowhere inside the repository (worktree or main tree)
            raise RunRefused("--out must lie outside the repository (C9)")
    try:
        plant = parse_plant(args.plant)
        K = parse_K(args.K, bool(args.plant), plant[0] if plant else None)
        parse_cases(getattr(args, "case", None), plant)
    except (NotImplementedError, ValueError) as e:
        raise RunRefused(str(e)) from None
    if not args.plant:
        if K != AUDIT_K:
            raise RunRefused("a real run uses the registered counts (claims_register.md:1069-1073): --K audit only")
        if args.g6l == PM.MODE_PLANT:
            raise RunRefused("plant-mode G6l is for plants only (prereg_amend_3.md:130-131)")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    code = plants_handoff(argv)   # a WP2 battery plant: a1_audit.plants.driver (HANDOFF_RULE)
    if code is not None:
        return code
    args = build_parser().parse_args(argv)
    try:
        validate(args)
    except RunRefused as e:
        print(ascii_line(f"a1_audit.run: refused: {e.code}"), flush=True)
        return 2
    gate = None if args.gate == "none" else args.gate
    preload_pass_modules()   # pre-WP4: L11's code hash covers every module a pass may import
    # 1. launch (L1-L15) before anything else
    kw = {"guard_selftest": dev_guard_not_run} if args.dev else {}
    refused: list = []
    try:
        rec = LA.launch(REPO, args.commit, gate, **kw)
    except LA.LaunchRefused as e:
        rec, refused = e.record, list(e.record.get("failed", []))
        if not (args.plant and args.dev):
            print(ascii_line("a1_audit.run: launch refused: failed " + ", ".join(refused)), flush=True)
            for ln in LA.summary_lines(rec):
                print(ascii_line("  " + ln), flush=True)
            return 3
    # 2. the gate check before any of the gate's material is touched (L15)
    try:
        if gate == "G1":
            GT.require_g1_open(DRIVER, REPO)
        elif gate == "G2":
            GT.require_step3v_open(DRIVER, REPO)
    except PermissionError as e:
        print(ascii_line(f"a1_audit.run: {type(e).__name__}: gate {gate} closed"), flush=True)
        return 3
    # 2b. RUN_PLAN §14: the block estimates (pinned for a real pass; a dev pass may name its own); the launch record
    # carries the file's hash
    try:
        est_doc, est_rec = block_estimates_for(args)
    except (PACE.EstimatesError, OSError, ValueError) as e:
        print(ascii_line(f"a1_audit.run: refused: {e}"), flush=True)
        return 2
    if est_rec is not None:
        rec["block_estimates"] = est_rec
    # 3. loader (after L1-L3)
    reg = LD.load(REPO, rec, allow_unlaunched=bool(args.dev))
    cases = parse_cases(args.case, parse_plant(args.plant))   # B3: [None] for real runs and P2
    for case in cases:
        run = Run(args, rec, refused, case=case)
        launch_copy = (run.results_dir / "launch_record.json")
        write_json_atomic(launch_copy, dict(stamp=run.stamp, launch_record=rec))
        if not args.dev and not args.plant:
            stamp = _dt.datetime.now().strftime("%Y%m%dT%H%M%S")
            write_json_atomic(run.out_root / LAUNCH_REL / f"{run.gate_dir}_{run.pass_}_"
                              f"{(rec.get('run_commit') or 'x')[:12]}_{stamp}.json", rec)   # C3: the main tree
        try:
            rows = _rows_for(run, reg.rows())
        except RunRefused as e:
            print(ascii_line(f"a1_audit.run: refused: {e.code}"), flush=True)
            return 2
        if args.dry:
            recs = dry_dispatch(rows, run.open_gates, plant_view=run.plant_view, sources=run.sources)
            doc = dict(run.header(), what="A1 dry dispatch (no statistic)", counts=dispatch_counts(recs), rows=recs,
                       provenance=run.provenance())
            write_json_atomic(run.results_dir / "DISPATCH.json", doc)
            run.log(f"dry dispatch: {json.dumps(dispatch_counts(recs)['by_outcome'])}")
            continue
        try:
            arm_pacer(run, est_doc, args.resume_after_pause)
        except RunRefused as e:
            print(ascii_line(f"a1_audit.run: refused: {e.code}"), flush=True)
            return 2
        try:
            execute(run, rows)
        except PACE.Paused as e:
            write_pause(run, e.report)
            print(ascii_line(f"a1_audit.run: PAUSED (RUN_PLAN §14 overrun): block {e.report['block']} at "
                             f"{e.report['elapsed_process_h']:.3f} process-h > {e.report['threshold_process_h']:.3f}; "
                             f"report in {PACE.PAUSES_FILE}; resume with --resume-after-pause \"<who / why>\""),
                  flush=True)
            return PACE.EXIT_PAUSED
    return 0


# ================================================================================================================
# pre-WP4 (§17): code coverage of the launch hash; RUN_PLAN §14 pause-and-report
# ================================================================================================================
# every module a pass may import (lazy imports included: wp3_repro / repro were imported after the WP3 run's
# code_recheck and hashed in no record); imported before the launch so L11 hashes them
PASS_MODULES = ("a1_audit.pace", "a1_audit.forms", "a1_audit.reporting", "a1_audit.real_sources", "a1_audit.wp3_layout",
                "a1_audit.wp3_material", "a1_audit.wp3_genes", "a1_audit.wp3_sd7", "a1_audit.wp3_decoder",
                "a1_audit.wp3_pdf", "a1_audit.wp3_repro", "a1_audit.repro", "a1_audit.reparcel",
                "a1_audit.fetch_extract", "a1_audit.identity", "a1_audit.ahba_builds", "a1_audit.privacy_wrap",
                "a1_audit.wp4_layout", "a1_audit.wp4_read", "a1_audit.wp4_sets", "a1_audit.wp4_sources",
                "a1_audit.wp4_repro")       # WP4: the G2 loaders and reproduction wiring
CODE_COVERAGE_RULE = ("every repository module loaded by the end of the pass is in the launch's L11 code hash "
                      "(run.PASS_MODULES are imported before the launch); a module outside it fails the pass after its "
                      "summary is written")


def preload_pass_modules() -> list:
    """Import PASS_MODULES (literal imports: no dynamic import in a production module, test_plants_wp2's isolation
    scan) and assert each is loaded."""
    from . import (ahba_builds, fetch_extract, forms, identity, pace, privacy_wrap, real_sources,  # noqa: F401
                   reparcel, reporting, repro, wp3_decoder, wp3_genes, wp3_layout, wp3_material, wp3_pdf, wp3_repro,
                   wp3_sd7, wp4_layout, wp4_read, wp4_repro, wp4_sets, wp4_sources)
    missing = [m for m in PASS_MODULES if m not in sys.modules]
    if missing:
        raise RuntimeError(f"preload: {missing} not loaded")
    return list(PASS_MODULES)


def block_estimates_for(args) -> tuple[dict | None, dict | None]:
    """(estimates document, the launch record's block_estimates entry) - a real pass (not plant, not dry): the pinned
    file (pace.ESTIMATES_REL, sha256 pace.ESTIMATES_SHA256; its block must have an estimate); a dev pass: the file
    named by --block-estimates (recorded unpinned) or none (not paced); a plant run or a dry run: none."""
    block = f"{GATE_DIR[args.gate]}/{args.pass_}"
    if args.dev and args.block_estimates:
        path = Path(args.block_estimates)
        doc, sha = PACE.load_estimates(path, pin=None)
        est = PACE.block_estimate(doc, block)
        return doc, dict(file="dev --block-estimates", sha256=sha, pinned=False, block=block,
                         pause_estimate_process_h=est, factor=PACE.PAUSE_FACTOR)
    if args.plant or args.dry or args.dev:
        return None, None
    doc, sha = PACE.load_estimates(REPO / PACE.ESTIMATES_REL, pin=PACE.ESTIMATES_SHA256)
    est = PACE.block_estimate(doc, block)
    return doc, dict(file=PACE.ESTIMATES_REL, sha256=sha, pinned=True, block=block, pause_estimate_process_h=est,
                     factor=PACE.PAUSE_FACTOR)


def arm_pacer(run: "Run", est_doc: dict | None, decision: str | None) -> None:
    """The pass's pacer, and the explicit resume rule: an unresolved pause of this pass (same run commit, code hash,
    block) refuses a run without --resume-after-pause; the flag without such a pause is refused; with both, the
    decision is recorded beside the pause (PAUSES.json, read back) and lifts it for the rest of the pass."""
    events = PACE.read_pauses(run.results_dir)
    ident = run.pause_identity()
    open_pause = PACE.unresolved(events, ident)
    if open_pause is not None and decision is None:
        raise RunRefused(f"this pass is paused (RUN_PLAN §14; {PACE.PAUSES_FILE}): resume only with "
                         "--resume-after-pause \"<who / why>\"")
    if decision is not None and open_pause is None:
        raise RunRefused("--resume-after-pause given, but this pass has no unresolved pause")
    if open_pause is not None:
        open_pause["resumed"] = dict(decision=decision, at=LA.now_iso(),
                                     effect="pause lifted for the rest of this pass (pace.py)")
        PACE.write_pauses(run.results_dir, events)
        run.log(f"RESUME after pause by decision: {ascii_line(decision)}")
    run.pauses = [e for e in events if PACE.same_identity(e, ident)]
    if est_doc is None:
        return
    block = ident["block"]
    run.pacer = PACE.Pacer(block=block, estimate_h=PACE.block_estimate(est_doc, block),
                           armed=PACE.lifted(events, ident) is None)


def write_pause(run: "Run", report: dict) -> str:
    events = PACE.read_pauses(run.results_dir)
    ev = dict(identity=run.pause_identity(), paused_at=LA.now_iso(), report=report, resumed=None,
              block_estimates=run.launch_record.get("block_estimates"))
    events.append(ev)
    sha = PACE.write_pauses(run.results_dir, events)
    run.log(f"PAUSED (RUN_PLAN §14): {json.dumps(A3.jsonable(report))}")
    return sha


if __name__ == "__main__":
    # fix round 1 (A2): an uncaught exception prints its class and the innermost a1_audit frame only (never a message or
    # a traceback: a message or frame may name a carrier's path)
    importlib.import_module("a1_audit.privacy_wrap").install_excepthook("a1_audit.run")
    # run everything inside the importable module object (a1_audit.run), so loky pickles `task` by reference
    sys.exit(importlib.import_module("a1_audit.run").main())
