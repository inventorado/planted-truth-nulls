"""Driver of the WP2 statistical plants (RUN_PLAN.md v3.1 §7, §14, §17, §18 WP2; R18 :846-847).

    python -X utf8 -u -m a1_audit.plants.driver <P3a|P3b|P4|P5|P6|P7|P8|P11|P12|P22|P24|P25|P26|id,id,...|all>
           --commit <sha> [--jobs 20] [--dev --out DIR [--n N] [--cells SUBSTR]]
    python -X utf8 -m a1_audit.plants.driver all --estimate            (process-hours from costs.json; no run)
    python -X utf8 -m a1_audit.plants.driver all --costs-from DIR[,DIR] (write costs.json from DEV runs; no run)

Two modes.
- OFFICIAL (no --dev): §7's n and plant K, nothing overridable. The launch (launch.launch: L1-L15, L5a) must pass at
  --commit (a clean pinned worktree, §2.3); a refusal stops the run before any statistic (exit 3). Outputs (R18 "plant
  outputs ... go to arcs/audit/run_manifests/ (... plants/)"): arcs/audit/run_manifests/plants/<id>/plant_<id>.json (the
  summary: every rate, threshold, pass / fail, seeds rule, PLANT CHOICES, provenance), cases_<id>.jsonl (one record
  per case: its keys, inputs' hashes, legs, verdicts), launch_record.json, run.log; checkpoints under
  artifacts/audit/a1_plants/<id>/ (gitignored); both in the MAIN repository when run from a pinned worktree (git's
  common dir; §2.3 :327-328), so the worktree stays clean.
- DEV (--dev --out DIR): tiny n (--n, default 2 per cell; never above §7's n), the same K; the launch is run with the
  privacy guard's self-test replaced by run.dev_guard_not_run (it reads under E:\\data\\asdg\\, which no dev run opens),
  so it is refused and every output is stamped "DEV (launch refused: <ids>)"; outputs and checkpoints only under DIR,
  which must lie outside the repository (and outside the main repository of a worktree). A DEV criterion reads "not evaluated (DEV run
  at n = ...)": DEV numbers are not results.
`all` runs every plant in one pool; every case of every plant is a task, dispatched longest first (§14 "longest-
processing-time ordering") by its per-case cost (the COSTS table measured in DEV, else the plant's default); a plant
with replace_unmatched draws further cases in case order until n are computed. Checkpoints: one per case (a3_port.
Checkpoints: atomic, refuses another run's or another code version's checkpoint); a rerun resumes from them. Jobs:
loky, OMP_NUM_THREADS=1 (run.py forces it at import). --estimate prints the per-plant process-hours from COSTS x §7's n
(no launch, no statistic).

Not run.py's dispatcher: a plant claim has no TSV row, run.py's --plant view routes TSV rows through toy contexts
(run.SyntheticSources: G = 300 genes, not the §3.1 matrix §7 requires) and refuses lettered ids. The claim-level code
path is the one a run.py row executes (run.prepare, plant_mode.streams_screen, run.g_legs, verdict.assemble_verdict_a1,
run.g_descriptors / g_tabs); see the WP2 report for the run.py hook that would let `a1_audit.run --plant` delegate here.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import importlib
import json
import os
import sys
import time
from pathlib import Path

from .. import run as R  # noqa: F401  (OMP_NUM_THREADS=1 first)
from .. import a3_port as A3
from .. import launch as LA
from .. import seeds as SD
from . import common as C
from . import criteria as CR

MODULES = ("p03", "p04", "p05", "p06", "p07", "p08", "p11", "p12", "p22", "p24", "p25", "p26")
ORDER = ("P3a", "P3b", "P4", "P5", "P6", "P7", "P8", "P11", "P12", "P22", "P24", "P25", "P26")
DRIVER = "a1_audit.plants.driver"
PLANTS_REL = R.PLANTS_REL          # arcs/audit/run_manifests/plants (R18)
CK_PLANT_REL = R.CK_PLANT_REL      # artifacts/audit/a1_plants
FORBIDDEN_OUT = R.FORBIDDEN_OUT
COSTS_FILE = Path(__file__).with_name("costs.json")
MAX_WAVES = 8
# RUN_PLAN_amend_2.md v2.1 §8.1b (FROZEN acdb1290...): the plant constants pinned by value; asserted at launch (run) and
# written into every plant header (write_plant). The only change to this module after its §8.1 pin (b217a14d).
PINNED_CONSTANTS = dict(
    PLANT_K={"site": 500, "species": 200, "permutation": 500, "sets": 200, "surr": 500, "j1_sets": 100},
    PLANT_K_OVERRIDES={"P12": {"permutation": 10000}},
    PLANT_WORD=900,
    PLANT_CLASS_IDS={"dk-ctx": 2, "V-AAL": 11, "V-DK": 12, "V-DK-subcortex": 13, "MIST64": 14, "V-CC200": 17},
    plant_int={"P3a": 3, "P3b": 3, "P4": 4, "P5": 5, "P6": 6, "P7": 7, "P8": 8, "P11": 11, "P12": 12, "P22": 22,
               "P24": 24, "P25": 25, "P26": 26},
    PLANT_CASE_RANGES={"P3a": [0, 1000], "P3b": [1000, None]},
    PLANT_DATA_WORD=1000)


def plant_constants() -> dict:
    """§8.1b: the constants as the code holds them now (run.PLANT_K, run.PLANT_K_OVERRIDES, the driver's K, seeds.
    PLANT_WORD, seeds.PLANT_CLASS_IDS, seeds.plant_int over ORDER with the case ranges, seeds.PLANT_DATA_WORD), asserted
    equal BY VALUE (canonical JSON, so 500 and 500.0 differ) to PINNED_CONSTANTS; AssertionError otherwise."""
    now = dict(PLANT_K=dict(R.PLANT_K), PLANT_K_OVERRIDES={k: dict(v) for k, v in R.PLANT_K_OVERRIDES.items()},
               PLANT_WORD=SD.PLANT_WORD, PLANT_CLASS_IDS=dict(SD.PLANT_CLASS_IDS),
               plant_int={p: SD.plant_int(p) for p in ORDER},
               PLANT_CASE_RANGES={k: list(v) for k, v in SD.PLANT_CASE_RANGES.items()},
               PLANT_DATA_WORD=SD.PLANT_DATA_WORD)
    canon = lambda o: json.dumps(o, sort_keys=True)  # noqa: E731
    bad = [k for k in PINNED_CONSTANTS if canon(now.get(k)) != canon(PINNED_CONSTANTS[k])]
    if canon(dict(C.K_PLANT)) != canon(PINNED_CONSTANTS["PLANT_K"]):
        bad.append("plants.common.K_PLANT")
    if bad:
        raise AssertionError(f"RUN_PLAN_amend_2 §8.1b: plant constants differ from their pinned values: {bad}")
    return dict(values=now, asserted="equal by value to RUN_PLAN_amend_2.md v2.1 §8.1b", source="RUN_PLAN_amend_2.md §8.1b")


def main_repository() -> Path:
    """The main repository of this checkout (git's common dir's parent): the main tree itself, or the tree a pinned
    worktree belongs to (RUN_PLAN §2.3 :327-328: outputs under the main repository; the worktree stays clean)."""
    import subprocess
    out = subprocess.run(["git", "-C", str(R.REPO), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                         capture_output=True, text=True, check=True).stdout.strip()
    return Path(out).resolve().parent


def plant_ids(text: str) -> list:
    """'all' (every plant, ORDER) or a comma-separated list of plant ids (each in ORDER), in ORDER's order."""
    if text == "all":
        return list(ORDER)
    ids = [t.strip() for t in text.split(",") if t.strip()]
    bad = [t for t in ids if t not in ORDER]
    if bad or not ids or len(set(ids)) != len(ids):
        raise SystemExit(f"refused: plant ids {bad or text!r} (one of {', '.join(ORDER)}, a comma list, or all)")
    return sorted(ids, key=ORDER.index)


def registry() -> dict:
    reg = {}
    for m in MODULES:
        mod = importlib.import_module(f"a1_audit.plants.{m}")
        for pid, spec in mod.PLANTS.items():
            if pid in reg:
                raise RuntimeError(f"plant {pid} defined twice")
            reg[pid] = spec
    if tuple(sorted(reg, key=ORDER.index)) != ORDER:
        raise RuntimeError(f"registry {sorted(reg)} != {ORDER}")
    return reg


REG = registry()


def cell_of(spec, name: str):
    hits = [c for c in spec.cells() if c.name == name]
    if len(hits) != 1:
        raise KeyError(f"{spec.id}: cell {name!r}")
    return hits[0]


def costs() -> dict:
    """{plant id: {cell name: seconds per case}} measured in DEV (costs.json beside this module), if present."""
    if COSTS_FILE.is_file():
        return json.loads(COSTS_FILE.read_text(encoding="utf-8")).get("seconds_per_case", {})
    return {}


def case_cost(spec, cell, table: dict) -> float:
    return float((table.get(spec.id) or {}).get(cell.name, spec.cost_s))


# ---- the task (module level: loky pickles it by reference) ---------------------------------------------------------
def task(key: str, kw: dict):
    spec = REG[kw["plant"]]
    cell = cell_of(spec, kw["cell"])
    t0, c0 = time.perf_counter(), time.process_time()
    started = LA.now_iso()
    rec = spec.run_case(cell, int(kw["i"]), dict(kw["K"]))
    rec = A3.jsonable(rec)
    rec.update(plant=spec.id, cell=cell.name, i=int(kw["i"]), case=int(kw["case"]), class_id=int(kw["class_id"]),
               plant_id=int(kw["plant_id"]), started=started, finished=LA.now_iso(),
               seconds=round(time.perf_counter() - t0, 3), cpu_seconds=round(time.process_time() - c0, 3),
               peak_working_set_bytes=R.process_peak_working_set(), pid=os.getpid())
    ws = rec["peak_working_set_bytes"]
    rec["memory_defect"] = bool(ws is not None and ws > R.JOB_LIMIT_BYTES)
    return key, rec


def run_tasks(tasks: list, jobs: int, log) -> dict:
    """tasks: [(store, key, expect, kw)] longest first. Verified checkpoints are not rerun; the rest run in a loky pool
    (batch size 1, in the given order) or in-process (jobs 1), each payload checkpointed as it returns. Returns
    {(store dir, key): payload} read back from the checkpoints."""
    pending, n_done = [], 0
    for store, key, expect, kw in tasks:
        if store.load(key, expect) is None:
            pending.append((store, key, expect, kw))
        else:
            n_done += 1
    if n_done:
        log(f"  resume: {n_done} task(s) verified from checkpoints, {len(pending)} to run")
    by_key = {(str(s.dir), k): (s, e) for s, k, e, _ in pending}
    t0 = time.time()
    if pending and jobs > 1:
        from joblib import Parallel, delayed
        gen = Parallel(n_jobs=jobs, backend="loky", batch_size=1, return_as="generator_unordered")(
            delayed(task)(f"{kw['store']}|{k}", kw) for _, k, _, kw in pending)
        for j, (skey, payload) in enumerate(gen, 1):
            sdir, key = skey.split("|", 1)
            store, expect = by_key[(sdir, key)]
            store.save(key, expect, payload)
            if j % 20 == 0 or j == len(pending):
                log(f"  {j}/{len(pending)} tasks ({time.time() - t0:.0f}s)")
    else:
        for j, (store, key, expect, kw) in enumerate(pending, 1):
            _, payload = task(f"{kw['store']}|{key}", kw)
            store.save(key, expect, payload)
            log(f"  {j}/{len(pending)} {key} ({payload['seconds']:.1f}s)")
    return {(str(s.dir), k): s.load(k, e) for s, k, e, _ in tasks}


# ---- one invocation ---------------------------------------------------------------------------------------------------
class Invocation:
    def __init__(self, args):
        self.args = args
        self.dev = bool(args.dev)
        self.ids = plant_ids(args.plant)
        self.K = dict(C.K_PLANT)          # plant K (RUN_PLAN §7 cost model; run.PLANT_K)
        if self.dev:
            self.out = Path(args.out).resolve()
            self.ck_root = self.out / "_ck"
        else:  # a worktree run writes under the MAIN repository (§2.3 :327-328; run.py's WP1-review fix C3)
            main = main_repository()
            tag = getattr(args, "rerun_tag", None)     # WP4 (§17 (1)): a rerun's own folders, the first run untouched
            self.out = main / PLANTS_REL if not tag else main / PLANTS_REL / f"rerun_{tag}"
            self.ck_root = main / CK_PLANT_REL if not tag else main / CK_PLANT_REL / f"rerun_{tag}"
        name = "all_run.log" if args.plant == "all" else (f"{self.ids[0]}/run.log" if len(self.ids) == 1 else
                                                         f"run_{'_'.join(self.ids)}.log")
        self.log = R.Log(self.out / name, "DEV " if self.dev else "")
        self.table = costs()

    def K_for(self, pid: str) -> dict:
        """Plant K with run.py's per-plant overrides where §7 pins a count (run.PLANT_K_OVERRIDES: P12's 10,000
        component permutations, RUN_PLAN.md:1139)."""
        return dict(self.K, **(getattr(R, "PLANT_K_OVERRIDES", {}) or {}).get(pid, {}))

    def n_for(self, spec, cell) -> int:
        n = spec.n_official(cell)
        return min(n, int(self.args.n)) if self.dev else n

    def launch(self) -> tuple[dict, list, str | None]:
        kw = {"guard_selftest": R.dev_guard_not_run} if self.dev else {}
        try:
            rec = LA.launch(R.REPO, self.args.commit, None, **kw)
            refused = []
        except LA.LaunchRefused as e:
            rec, refused = e.record, list(e.record.get("failed", []))
            if not self.dev:
                self.log("launch refused: failed " + ", ".join(refused))
                for ln in LA.summary_lines(rec):
                    self.log("  " + ln)
                raise SystemExit(3)
        stamp = None
        if self.dev:
            stamp = ("DEV (launch refused: %s)" % ", ".join(refused)) if refused else "DEV (launch passed; dev run)"
        return rec, refused, stamp

    def provenance(self, rec: dict, refused: list, stamp) -> dict:
        mods, foreign = LA.code_modules(R.REPO)
        now = {rel: LA.sha256_bytes(LA.lf(p.read_bytes())) for rel, p in mods.items()}
        if not self.dev:
            block = LA.provenance_block(rec, R.REPO)
        else:
            l11 = [a for a in rec.get("assertions", []) if a.get("id") == "L11"]
            block = {"DEV": stamp, "run_commit": rec.get("run_commit"), "worktree": str(R.REPO),
                     "plan_sha256": rec.get("plan_sha256"), "amendment_sha256": rec.get("amendment_sha256"),
                     "launch_failed": refused, "launch_assertions": [dict(a) for a in rec.get("assertions", [])],
                     "code_at_launch": (l11[0].get("observed") or {}).get("code_hash") if l11 else None,
                     "launch_started": rec.get("started"), "launch_finished": rec.get("finished"),
                     "host": rec.get("host")}
        block["code_now"] = {"modules": now, "code_hash": LA.code_hash(now), "foreign": foreign}
        block["matrix_first_use"] = LA.first_use_records()
        return block

    def run(self) -> int:
        a = self.args
        self.log(f"plants {','.join(self.ids)} mode {'DEV' if self.dev else 'OFFICIAL'} K {self.K} jobs {a.jobs}")
        C.require_seed_interface()
        crit_self = CR.self_test()
        self.constants = plant_constants()   # RUN_PLAN_amend_2 §8.1b: asserted at launch
        rec, refused, stamp = self.launch()
        self.launch_rec = rec
        for pid in self.ids:
            (self.out / pid).mkdir(parents=True, exist_ok=True)
            R.write_json_atomic(self.out / pid / "launch_record.json", dict(stamp=stamp, launch_record=rec))
        # contexts, readers and modules loaded before the code snapshot (L11's precedent: every module the run uses)
        for cls in ("dk-ctx", "V-DK", "V-AAL", "V-DK-subcortex", "MIST64"):
            C.class_context(cls)
        importlib.import_module("e3_align_plants")
        importlib.import_module("asdg.brainspan")   # P22's G5 trajectories (imported only; read in the workers)
        prov = self.provenance(rec, refused, stamp)
        code_hash = prov["code_now"]["code_hash"]
        stores, plan = {}, {}
        tasks = []
        for pid in self.ids:
            spec = REG[pid]
            store = A3.Checkpoints(self.ck_root / pid, code_hash, f"{DRIVER}:{pid}")
            store.run_record(dict(plant=pid, plant_id=spec.plant_id, mode="DEV" if self.dev else "OFFICIAL",
                                  K=self.K_for(pid), g6l_mode=C.G6L_MODE, code_hash=code_hash,
                                  run_commit=rec.get("run_commit")))
            stores[pid] = store
            for cell in spec.cells():
                if a.cells and a.cells not in cell.name:
                    continue
                n = self.n_for(spec, cell)
                plan[(pid, cell.name)] = n
                tasks += [self.task_entry(spec, cell, i, store) for i in range(n)]
        tasks.sort(key=lambda t: -t[3]["cost"])
        self.log(f"wave 1: {len(tasks)} case(s)")
        got = run_tasks(tasks, a.jobs, self.log)
        for wave in range(2, MAX_WAVES + 1):
            more = []
            for pid in self.ids:
                spec = REG[pid]
                if not spec.replace_unmatched:
                    continue
                for cell in spec.cells():
                    if (pid, cell.name) not in plan:
                        continue
                    recs = self.records(spec, cell, stores[pid], got)
                    n_comp = sum(r["status"] == "computed" for r in recs)
                    need = plan[(pid, cell.name)] - n_comp
                    if need > 0:
                        start = len(recs)
                        more += [self.task_entry(spec, cell, i, stores[pid]) for i in range(start, start + need)]
            if not more:
                break
            more.sort(key=lambda t: -t[3]["cost"])
            self.log(f"wave {wave}: {len(more)} replacement case(s) (unmatched plants replaced in case order)")
            got.update(run_tasks(more, a.jobs, self.log))
            tasks += more
        else:
            raise RuntimeError(f"replacement waves did not reach n after {MAX_WAVES} waves")
        rc = 0
        for pid in self.ids:
            rc |= self.write_plant(REG[pid], stores[pid], got, plan, prov, stamp, crit_self)
        return rc

    def task_entry(self, spec, cell, i: int, store):
        case = spec.case_of(cell, i)
        cid = C.class_id(cell.cls)
        key = f"{cell.slug}_i{i:04d}"
        K = self.K_for(spec.id)
        kw = dict(plant=spec.id, cell=cell.name, i=i, case=case, class_id=cid, plant_id=spec.plant_id, K=K,
                  store=str(store.dir), cost=case_cost(spec, cell, self.table))
        expect = dict(plant=spec.id, plant_id=spec.plant_id, cell=cell.name, i=i, case=case, class_id=cid, K=K,
                      g6l_mode=C.G6L_MODE, construction_key=[SD.ROOT_ENTROPY, SD.PLANT_WORD, spec.plant_id, case, cid])
        return (store, key, expect, kw)

    def records(self, spec, cell, store, got) -> list:
        """The cell's case records in case order: i = 0, 1, ... up to the first n computed (with any unmatched before)."""
        out = []
        i = 0
        while True:
            r = got.get((str(store.dir), f"{cell.slug}_i{i:04d}"))
            if r is None:
                return out
            out.append(r)
            i += 1

    def write_plant(self, spec, store, got, plan, prov, stamp, crit_self) -> int:
        cells, cases, timing = {}, [], {}
        for cell in spec.cells():
            if (spec.id, cell.name) not in plan:
                continue
            n_want = plan[(spec.id, cell.name)]
            recs = self.records(spec, cell, store, got)
            if spec.replace_unmatched:
                used, k = [], 0
                for r in recs:
                    used.append(r)
                    k += r["status"] == "computed"
                    if k == n_want:
                        break
            else:
                used = recs[:n_want]
            n_official = spec.n_official(cell)
            summ = spec.summarise(cell, used, n_official)
            summ["n_official"] = n_official
            summ["n_run"] = n_want
            cells[cell.name] = summ
            cases += used
            secs = [r["seconds"] for r in used]
            cpus = [r["cpu_seconds"] for r in used]
            timing[cell.name] = dict(n=len(secs), mean_seconds=sum(secs) / len(secs) if secs else None,
                                     max_seconds=max(secs) if secs else None,
                                     mean_cpu_seconds=sum(cpus) / len(cpus) if cpus else None,
                                     n_official_cases=n_official,
                                     memory_defects=sum(bool(r.get("memory_defect")) for r in used),
                                     max_peak_working_set_bytes=max((r.get("peak_working_set_bytes") or 0)
                                                                    for r in used) if used else None)
        outdir = self.out / spec.id
        if not self.dev:  # before a write (launch.recheck_code; A3 precedent step3v_common.recheck): code unchanged
            prov = dict(prov, code_recheck_at_write=LA.recheck_code(self.launch_rec))
        cases_sha = C.write_jsonl(outdir / f"cases_{spec.id}.jsonl", cases)
        doc = dict(what=f"A1 WP2 plant {spec.id} (RUN_PLAN.md v3.1 §7); every number from this driver's run",
                   stamp=stamp, mode="DEV" if self.dev else "OFFICIAL", plant=spec.describe(),
                   plant_constants=self.constants,   # RUN_PLAN_amend_2 §8.1b: in every plant header
                   seeds=dict(rule=C.SEED_RULE, plant_id=spec.plant_id, class_ids={c.cls: C.class_id(c.cls)
                                                                                for c in spec.cells()},
                              seed_interface=C.seed_interface_record()),
                   K=self.K_for(spec.id), g6l_mode=C.G6L_MODE, alpha=C.ALPHA,
                   criteria_derivations=CR.derivations(),
                   criteria_self_test=crit_self, cells=cells, outcome=spec.finish(cells), timing=timing,
                   contexts={c.cls: C.context_report(c.cls) for c in spec.cells()},
                   cases_file=dict(name=f"cases_{spec.id}.jsonl", sha256=cases_sha, n=len(cases)),
                   provenance=prov, driver=DRIVER, written=LA.now_iso(),
                   argv=sys.argv[1:])
        sha = C.write_json(outdir / f"plant_{spec.id}.json", doc)
        oc = doc["outcome"]
        self.log(f"{spec.id}: {len(cases)} case(s); criteria PASS {oc['n_PASS']} FAIL {oc['n_FAIL']} CAUGHT "
                 f"{oc['n_CAUGHT']} NOT CAUGHT {oc['n_NOT_CAUGHT']} not evaluated {oc['n_not_evaluated']} reported "
                 f"{oc['n_reported']}; plant_{spec.id}.json sha256 {sha[:16]}")
        return 1 if (oc["n_FAIL"] and not self.dev) else 0


def costs_from_dirs(text: str) -> dict:
    """costs_from over a comma-separated list of DEV directories: per plant, the directory whose cases file holds
    the most cases of that plant."""
    docs = [costs_from(Path(t.strip())) for t in text.split(",") if t.strip()]
    out = dict(seconds_per_case={}, n_dev_cases={}, warmup_excess_seconds={}, source=[], rule=docs[0]["rule"])
    for pid in ORDER:
        best = None
        for d in docs:
            n = sum(v["n_steady"] + v["n_first"] for v in (d["n_dev_cases"].get(pid) or {}).values())
            if pid in d["seconds_per_case"] and (best is None or n > best[0]):
                best = (n, d)
        if best:
            d = best[1]
            out["seconds_per_case"][pid] = d["seconds_per_case"][pid]
            out["n_dev_cases"][pid] = d["n_dev_cases"][pid]
            if pid in d["warmup_excess_seconds"]:
                out["warmup_excess_seconds"][pid] = d["warmup_excess_seconds"][pid]
            out["source"].append(dict(plant=pid, dir=d["source"]))
    return out


def costs_from(dev_dir: Path) -> dict:
    """Seconds per case from a DEV run's cases_<id>.jsonl (measured under the DEV run's job count): per cell, the
    median wall seconds of the STEADY-STATE cases - each worker process's first case of a (plant, class) pays the
    per-process builds (class contexts, R35 reader checks, e3_align_plants' k-means modules, BrainSpan) and is left out
    when the cell has later cases - and, beside it, the warm-up excess (median first-case minus steady-state seconds) per
    (plant, class), which an official run pays once per worker. Written to costs.json beside this module (LPT ordering
    and --estimate)."""
    import statistics
    out, meta, warm = {}, {}, {}
    for pid in ORDER:
        f = Path(dev_dir) / pid / f"cases_{pid}.jsonl"
        if not f.is_file():
            continue
        rows = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()]
        spec = REG[pid]
        cls_of = {c.name: c.cls for c in spec.cells()}
        first = {}
        for r in sorted(rows, key=lambda r: r["started"]):
            first.setdefault((r["pid"], cls_of[r["cell"]]), id(r))
        by, firsts = {}, {}
        for r in rows:
            is_first = first[(r["pid"], cls_of[r["cell"]])] == id(r)
            (firsts if is_first else by).setdefault(r["cell"], []).append(float(r["seconds"]))
        out[pid], meta[pid] = {}, {}
        for cell in sorted(set(by) | set(firsts)):
            sib = [s for c, v in by.items() if c != cell and cls_of[c] == cls_of[cell] for s in v]
            if by.get(cell):
                steady, rule = by[cell], "steady cases of the cell"
            elif sib:   # every case of this cell was some worker's first of its class: its class siblings' steady cases
                steady, rule = sib, "steady cases of the same plant's cells of the same class (same work per case)"
            else:
                steady, rule = firsts[cell], "first cases (no steady case of this plant x class; includes warm-up)"
            out[pid][cell] = round(statistics.median(steady), 2)
            meta[pid][cell] = dict(n_steady=len(by.get(cell, [])), n_first=len(firsts.get(cell, [])), rule=rule)
            if firsts.get(cell) and rule != meta[pid][cell]["rule"][:0] + "first cases (no steady case of this plant x class; includes warm-up)":
                warm.setdefault(pid, {})[cell] = round(statistics.median(firsts[cell]) - out[pid][cell], 2)
    return dict(seconds_per_case=out, n_dev_cases=meta, warmup_excess_seconds=warm, source=str(dev_dir),
                rule="median wall seconds per case of each cell over the steady-state DEV cases (each worker's first "
                     "case of a (plant, class) left out when later cases exist), under the DEV run's job count")


def estimate(table: dict) -> dict:
    """Process-hours per plant: §7's n (replacement plants: n / (1 - unmatched share measured, else n)) x the per-case
    seconds measured in DEV (costs.json) or the plant's default."""
    out, tot = {}, 0.0
    for pid in ORDER:
        spec = REG[pid]
        s = 0.0
        for cell in spec.cells():
            s += spec.n_official(cell) * case_cost(spec, cell, table)
        out[pid] = round(s / 3600.0, 2)
        tot += s
    out["total"] = round(tot / 3600.0, 2)
    return out


def build_parser():
    ap = argparse.ArgumentParser(prog=f"python -m {DRIVER}", description="A1 WP2 plants (RUN_PLAN §7)")
    ap.add_argument("plant", help="a plant id (%s), a comma-separated list of them, or all" % ", ".join(ORDER))
    ap.add_argument("--commit", default=None, help="the run commit (L11: HEAD must equal it)")
    ap.add_argument("--jobs", type=int, default=20)
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--out", default=None, help="DEV: the only directory written")
    ap.add_argument("--n", type=int, default=2, help="DEV: cases per cell (capped at §7's n)")
    ap.add_argument("--cells", default=None, help="DEV: only cells whose name contains this text")
    ap.add_argument("--estimate", action="store_true", help="print the cost estimate (no launch, no statistic)")
    ap.add_argument("--costs-from", default=None, help="write costs.json from a DEV run's output directory, then exit")
    ap.add_argument("--rerun-tag", dest="rerun_tag", default=None,
                    help="OFFICIAL reruns under RUN_PLAN §17 (1): outputs under run_manifests/plants/rerun_<TAG>/")
    return ap


def validate(args) -> None:
    if args.estimate or args.costs_from:
        return
    plant_ids(args.plant)
    if not args.commit:
        raise SystemExit("refused: --commit is required (L11)")
    if args.jobs < 1:
        raise SystemExit("refused: --jobs must be >= 1")
    tag = getattr(args, "rerun_tag", None)
    if tag is not None:
        import re as _re
        if args.dev or not _re.fullmatch(r"[a-z0-9][a-z0-9_]{0,39}", tag):
            raise SystemExit("refused: --rerun-tag is for official runs, TAG = [a-z0-9][a-z0-9_]{0,39}")
    if args.dev:
        if not args.out:
            raise SystemExit("refused: --dev needs --out")
        out = Path(args.out).resolve()
        for root in {R.REPO.resolve(), main_repository()}:
            if R._under(out, root):
                raise SystemExit(f"refused: --out must lie outside the repository ({root}; run.py's fix C9)")
        if args.n < 1:
            raise SystemExit("refused: --n must be >= 1")
    else:
        if args.out or args.cells or args.n != 2:
            raise SystemExit("refused: --out / --n / --cells are DEV options (an official run uses §7's n and cells)")


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        validate(args)
    except SystemExit as e:
        print(R.ascii_line(f"{DRIVER}: {e.code}"), flush=True)
        return 2
    if args.costs_from:
        doc = costs_from_dirs(args.costs_from)
        C.write_json(COSTS_FILE, doc)
        print(json.dumps(estimate(doc["seconds_per_case"]), indent=1), flush=True)
        return 0
    if args.estimate:
        print(json.dumps(estimate(costs()), indent=1), flush=True)
        return 0
    try:
        return Invocation(args).run()
    except SystemExit as e:
        return int(e.code) if isinstance(e.code, int) else 3


if __name__ == "__main__":
    sys.exit(importlib.import_module("a1_audit.plants.driver").main())
