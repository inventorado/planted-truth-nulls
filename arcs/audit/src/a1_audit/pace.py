"""RUN_PLAN §14 overrun rule at the checkpoint level (pre-WP4, §17; bench ev-1a13e2bfff7bdb6): "at more than 2x the
block estimate the run pauses at the next checkpoint and reports. Nothing is dropped." (RUN_PLAN.md §14, Schedule).

- The block of a pass is (gate directory, pass), e.g. "G2/descriptor". Its estimate (process-h) is read from the PINNED
  repriced file `arcs/audit/run_manifests/reprice_wp4.json` (written by `a1_audit.reprice`; its LF sha256 is pinned
  here as ESTIMATES_SHA256 and carried by the launch record, run.py). A real pass whose block has no estimate there is
  refused (G1: RUN_PLAN §12 reprices G1 before WP5).
- Process-h = the sum of the `_meta.seconds` of every checkpointed task of the pass (the row tasks, the G6l screens
  and the form rows; tasks verified from earlier invocations included), the quantity the WP3 records report.
- At every checkpoint written, if that sum exceeds PAUSE_FACTOR x the estimate (strictly; at or below never), the
  runner stops dispatching: the jobs already running finish and are checkpointed, then `Paused` is raised with the
  report (block, estimate, threshold, elapsed, jobs done / remaining in the batch and over the pass so far, projected
  total). run.py writes it to the pass's output directory (PAUSES.json) and exits with EXIT_PAUSED.
- Resume is explicit: `--resume-after-pause "<who / why>"` (run.py) records the decision beside the pause; a pass whose
  last pause (same run commit, code hash and block) has no decision is refused; the decision lifts the pause for the
  rest of that pass (reading made here: §14 says the run "pauses ... and reports"; what follows a report is the
  orchestrator's decision, and the decision string is that decision). Finished jobs are never recomputed: their
  checkpoints verify and load (A3 Checkpoints).
- `run_jobs` replaces a3_port.run_pending for the runner: the same checkpoint store semantics (load-verify first, save
  as each returns, read everything back), the same LPT dispatch order, a loky process pool for jobs > 1 (workers
  inherit the runner's forced OMP / OPENBLAS / MKL = 1); a task's result depends only on its arguments (its seeds), so
  the order of completion never enters a statistic.
"""
from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import FIRST_COMPLETED, wait
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

EXIT_PAUSED = 4
PAUSE_FACTOR = 2.0
ESTIMATES_REL = "arcs/audit/run_manifests/reprice_wp4.json"
ESTIMATES_SHA256 = "95a7745a42cc2e63158b3b70c464175df1f7266320b30288144fd0d6534fc2a5"  # reprice_wp4.json (a1_audit.reprice), LF bytes
PAUSES_FILE = "PAUSES.json"
PAUSE_RULE = ("RUN_PLAN §14 (Schedule, Overrun): 'at more than 2x the block estimate the run pauses at the next "
              "checkpoint and reports. Nothing is dropped.' Process-h = sum of every checkpointed task's seconds in "
              "this pass; the trigger is strictly above PAUSE_FACTOR x the estimate")


class Paused(Exception):
    """Raised by run_jobs after the running jobs finished and were checkpointed; .report is the pause report."""

    def __init__(self, report: dict):
        super().__init__("paused (RUN_PLAN §14 overrun)")
        self.report = report


class EstimatesError(RuntimeError):
    pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def lf(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


def load_estimates(path: Path, pin: str | None = ESTIMATES_SHA256) -> tuple[dict, str]:
    """(document, LF sha256). With a pin, the bytes must equal it (a real run); pin None = a dev run's file."""
    data = lf(Path(path).read_bytes())
    sha = sha256_bytes(data)
    if pin is not None and sha != pin:
        raise EstimatesError("the block-estimate file differs from its pin (pace.ESTIMATES_SHA256)")
    doc = json.loads(data.decode("utf-8"))
    if not isinstance(doc.get("blocks"), dict):
        raise EstimatesError("the block-estimate file has no 'blocks' table")
    return doc, sha


def block_estimate(doc: dict, block: str) -> float:
    """The pause estimate (process-h) of a block; EstimatesError if the file names none (or not a positive number)."""
    b = (doc.get("blocks") or {}).get(block) or {}
    est = b.get("pause_estimate_process_h")
    if isinstance(est, bool) or not isinstance(est, (int, float)) or not est > 0:
        raise EstimatesError(f"no repriced estimate for block {block} (RUN_PLAN §14; G1: §12 reprices it before WP5)")
    return float(est)


def seconds_of(payload) -> float:
    meta = payload.get("_meta") if isinstance(payload, dict) else None
    s = (meta or {}).get("seconds")
    if isinstance(s, bool) or not isinstance(s, (int, float)):
        raise ValueError("a task payload without _meta.seconds (the pause cannot count it)")
    return float(s)


@dataclass
class Pacer:
    """Cumulative process-seconds of one pass against PAUSE_FACTOR x its estimate. armed False = the pause was lifted
    by a recorded decision (resume) or the run is not paced; counting continues either way."""
    block: str
    estimate_h: float
    factor: float = PAUSE_FACTOR
    armed: bool = True
    seconds: Callable[[Any], float] = seconds_of
    cum_s: float = 0.0
    counted: set = field(default_factory=set)
    paused: bool = False
    trigger: dict | None = None
    batch: dict = field(default_factory=dict)

    @property
    def threshold_s(self) -> float:
        return self.factor * self.estimate_h * 3600.0

    def start_batch(self, name: str, n_total: int) -> None:
        self.batch = dict(name=name, n_total=int(n_total), n_done=0, cum_at_start_s=self.cum_s, s=0.0)

    def count(self, key: str, payload) -> None:
        """Add a checkpointed task's seconds once (keys of different stores are distinct by their group prefix)."""
        if key in self.counted:
            return
        s = self.seconds(payload)
        self.counted.add(key)
        self.cum_s += s
        if self.batch:
            self.batch["n_done"] += 1
            self.batch["s"] += s

    def check(self) -> bool:
        """At a checkpoint: True (and paused) iff armed and the cumulative seconds exceed the threshold."""
        if self.armed and not self.paused and self.cum_s > self.threshold_s:
            self.paused = True
            self.trigger = dict(cum_process_h=self.cum_s / 3600.0, tasks_counted=len(self.counted))
        return self.paused

    def report(self, n_running_finished: int = 0) -> dict:
        b = dict(self.batch)
        done, total = int(b.get("n_done", 0)), int(b.get("n_total", 0))
        prior_s = float(b.get("cum_at_start_s", 0.0))
        proj = None
        if done:
            proj = (prior_s + b["s"] * total / done) / 3600.0
        return dict(what="A1 pause report (RUN_PLAN §14 overrun)", rule=PAUSE_RULE, block=self.block,
                    estimate_process_h=self.estimate_h, factor=self.factor, threshold_process_h=self.threshold_s / 3600.0,
                    elapsed_process_h=self.cum_s / 3600.0, trigger=self.trigger,
                    batch=dict(name=b.get("name"), jobs_done=done, jobs_remaining=total - done, jobs_total=total,
                               running_jobs_finished_after_trigger=int(n_running_finished)),
                    tasks_checkpointed_in_pass=len(self.counted),
                    projected_total_process_h=proj,
                    projection_rule=("tasks of this pass done before this batch + this batch's mean seconds per task x "
                                     "its task count; batches not yet built (later phases) are not in it"))


@dataclass
class Job:
    key: str
    expect: dict
    kw: dict
    store: Any          # a3_port.Checkpoints
    fn: Callable        # module-level fn(key, kw) -> (key, payload) (loky pickles it by reference)


def run_jobs(jobs: list, n_jobs: int, log=print, pacer: Pacer | None = None, name: str = "batch") -> dict:
    """Run the jobs whose checkpoints do not verify; {key: payload} read back from the checkpoints. With a pacer, the
    pause check runs at every checkpoint written; once it fires no further job is dispatched, the running ones finish
    and are checkpointed, and Paused is raised."""
    done, pending = {}, []
    if pacer is not None:
        pacer.start_batch(name, len(jobs))
    for j in jobs:
        got = j.store.load(j.key, j.expect)
        if got is None:
            pending.append(j)
        else:
            done[j.key] = got
            if pacer is not None:
                pacer.count(j.key, got)
    if done:
        log(f"  resume: {len(done)} task(s) verified from checkpoints, {len(pending)} to run")
    t0 = time.time()
    state = dict(finished=0, after_trigger=0)

    def save(j: Job, payload) -> None:
        was = pacer is not None and pacer.paused
        j.store.save(j.key, j.expect, payload)
        state["finished"] += 1
        if pacer is not None:
            pacer.count(j.key, payload)
            if was:
                state["after_trigger"] += 1
            elif pacer.check():
                log(f"  PAUSE: block {pacer.block} at {pacer.cum_s / 3600.0:.3f} process-h > "
                    f"{pacer.factor:g} x {pacer.estimate_h:g} (RUN_PLAN §14); no further job dispatched")
        if state["finished"] % 10 == 0 or state["finished"] == len(pending):
            log(f"  {state['finished']}/{len(pending)} tasks ({time.time() - t0:.0f}s)")

    def stop() -> bool:
        return pacer is not None and pacer.paused

    if pending and n_jobs > 1 and not stop():
        from joblib.externals.loky import get_reusable_executor
        ex = get_reusable_executor(max_workers=int(n_jobs))
        it = iter(pending)
        inflight: dict = {}

        def submit_next() -> bool:
            j = next(it, None)
            if j is None:
                return False
            inflight[ex.submit(j.fn, j.key, j.kw)] = j
            return True

        for _ in range(int(n_jobs)):
            if not submit_next():
                break
        error = None
        while inflight:
            fin, _ = wait(list(inflight), return_when=FIRST_COMPLETED)
            for f in fin:
                j = inflight.pop(f)
                try:
                    k2, payload = f.result()
                except BaseException as e:   # the running jobs still finish and are checkpointed; then it is raised
                    error = error or e
                    continue
                if k2 != j.key:
                    error = error or RuntimeError(f"task returned key {k2!r} for {j.key!r}")
                    continue
                save(j, payload)
            while error is None and not stop() and len(inflight) < int(n_jobs):
                if not submit_next():
                    break
        if error is not None:
            raise error
    else:
        for j in pending:
            if stop():
                break
            k2, payload = j.fn(j.key, j.kw)
            if k2 != j.key:
                raise RuntimeError(f"task returned key {k2!r} for {j.key!r}")
            save(j, payload)
    if stop():
        raise Paused(pacer.report(state["after_trigger"]))
    return {j.key: j.store.load(j.key, j.expect) for j in jobs}


# ---- the pass's pause records (PAUSES.json in the pass's output directory) -------------------------------------
def read_pauses(results_dir: Path) -> list:
    p = Path(results_dir) / PAUSES_FILE
    if not p.is_file():
        return []
    doc = json.loads(p.read_bytes().decode("utf-8"))
    ev = doc.get("events") if isinstance(doc, dict) else None
    if not isinstance(ev, list):
        raise RuntimeError(f"{PAUSES_FILE}: no events list")
    return ev


def write_pauses(results_dir: Path, events: list) -> str:
    """Write and read back (rule 8); returns the sha256 of the bytes written."""
    p = Path(results_dir) / PAUSES_FILE
    p.parent.mkdir(parents=True, exist_ok=True)
    doc = {"what": "A1 pause / resume records of this pass (RUN_PLAN §14; a1_audit.pace)", "events": events}
    data = (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    tmp = p.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(p)
    back = p.read_bytes()
    if back != data or json.loads(back.decode("utf-8")) != doc:
        raise RuntimeError(f"{PAUSES_FILE}: read-back differs from what was written")
    return sha256_bytes(back)


def same_identity(ev: dict, identity: dict) -> bool:
    return all(ev.get("identity", {}).get(k) == v for k, v in identity.items())


def unresolved(events: list, identity: dict) -> dict | None:
    """The last pause of this identity without a resume decision, or None."""
    mine = [e for e in events if same_identity(e, identity)]
    if mine and mine[-1].get("resumed") is None:
        return mine[-1]
    return None


def lifted(events: list, identity: dict) -> dict | None:
    """The decision that lifted the pause of this identity (the last resumed pause), or None."""
    mine = [e for e in events if same_identity(e, identity) and e.get("resumed") is not None]
    return mine[-1]["resumed"] if mine else None
