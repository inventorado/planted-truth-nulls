"""Pre-WP4 code changes (RUN_PLAN §17; bench ev-1a12dffe1a85af7, ev-1a13e2bfff7bdb6) on SYNTHETIC stand-ins only.
No claim map, set, carrier or ungated material is opened; the recorded WP3 row files are read (never written).

Checks (each fails on the WP3 code, 069ca7b; the failure it shows there is named):
- r27_component_kind: run.r27_for_map on a component verdict record (kind 'component-permutation' / '-parametric',
  the kinds verdict.adapter_kind writes) reads the component reading, keeps A3's reading beside as reading_r27 and
  keeps 'species leg untested (gradient)' among the labels with a note (review B2); a full-verdict record and the
  bare literal 'component' (no record carries it) are left as A3 reads them. [old: the swap never applies]
- r27_relabel_file: a1_audit.r27_relabel rebuilds results/a1_run/ungated/r27_relabel_MOR-C.json's cells from the
  recorded verdict rows (old rule = the recorded block, exactly). [old: no module, no file]
- r27_descriptor_component_marked (review B1): a descriptor-routed component row that PASSES at component level
  (verdict.descriptor_row_record) reads its DESCRIPTIVE reading through run.r27_verdict_rec / r27_for_map, never an
  unmarked 'passes at component level'. [221691a: the unmarked inner reading]
- pacer_threshold: pace.Pacer triggers strictly above 2 x the estimate, never at or below; a key counts once.
- run_jobs_pause_pool / _inprocess: a synthetic block (12 tasks, injected 100 s each, 3 workers / in-process): the pause
  fires at the first checkpoint above 2x, no task is dispatched after it, the running ones finish and are checkpointed,
  Paused carries the report; resume (decision lifts the pause) completes, no finished task is recomputed, the values
  equal an uninterrupted run's; at exactly 2x nothing pauses. [old: no pace module]
- runner_pause_resume (dev P2 runs through the CLI, --block-estimates): exit pace.EXIT_PAUSED with PAUSES.json; a rerun
  without --resume-after-pause is refused (exit 2); the flag without a pause is refused; the resume records the
  decision, recomputes no checkpointed task and gives rows identical to an uninterrupted run. [old: unknown flags]
- block_estimates_pinned: a real pass reads the pinned reprice_wp4.json (sha256 = pace.ESTIMATES_SHA256) and its
  block's estimate; G1 has none (refused); a planted byte change is refused; the launch record of a dev pass carries
  the estimates' hash. Flag validation (dev-only file, empty decision, --dry). [old: no pin]
- form_rows_in_pool: dev P16 descriptor pass (Liu rows 471-477) with --jobs 3: every form row's checkpoint payload was
  computed in a worker (its pid differs from the saving parent's), the records equal a --jobs 1 run's and in-process
  forms.liu_compute. [old: computed in the parent, pid equal]
- preload_and_coverage: the dev run's launch L11 hashes wp3_repro.py, repro.py and pace.py (run.PASS_MODULES preloaded
  before the launch); run.code_coverage reports a planted module missing from L11 as DEFECT. [old: not hashed]
- sensitivity_rule_donors: run.prepare with rule 'donors>=2' records '>= 2 donors' (never 'AHBA sample(s)'); the
  primary rule keeps '>= 1 AHBA sample(s)'. [old: '>= 2 AHBA sample(s)']

Run (from arcs/audit/src):
  ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_prewp4 [--scratch DIR]
Exits non-zero on any failure. Prints ASCII only.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import traceback
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SRC = ROOT / "arcs" / "audit" / "src"
for _p in (ROOT / "src", SRC):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

ap = argparse.ArgumentParser()
ap.add_argument("--scratch", default=None)
ARGS, _ = ap.parse_known_args()
SCRATCH = Path(ARGS.scratch or tempfile.mkdtemp(prefix="a1_prewp4_")).resolve()
SCRATCH.mkdir(parents=True, exist_ok=True)

import a1_audit.a3_port as A3  # noqa: E402
import a1_audit.run as R  # noqa: E402

RESULTS: dict = {}
FAILED: list = []
CHECKS: list = []
HEAD = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
CLI_K = "site=120,species=40,permutation=120,sets=40,surr=120,j1_sets=30"
COMP_READING = "does not pass at component level (Level 0 and site leg at .025)"
COMP_LABEL = "site leg only; not calibrated against expression-aligned maps"


def check(name):
    def deco(fn):
        def run():
            t0 = time.time()
            try:
                measured = fn() or {}
                RESULTS[name] = dict(result="pass", seconds=round(time.time() - t0, 2), **measured)
                print(f"  pass  {name} ({time.time() - t0:.1f}s)", flush=True)
            except Exception as e:  # noqa: BLE001
                FAILED.append(name)
                RESULTS[name] = dict(result="FAIL", error=f"{type(e).__name__}: {e}"[:600],
                                     trace=traceback.format_exc()[-2000:])
                print(f"  FAIL  {name}: {type(e).__name__}: {str(e)[:300]}".encode("ascii", "replace").decode(),
                      flush=True)
        CHECKS.append(run)
        return fn
    return deco


def cli(args: list, timeout: int = 3600) -> tuple:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, "-X", "utf8", "-u", "-m", "a1_audit.run", *args], cwd=str(SRC),
                       capture_output=True, env=env, timeout=timeout)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


def p2(out: Path, jobs: int, extra=()) -> tuple:
    return cli(["--commit", HEAD, "--pass", "verdict", "--gate", "none", "--rows", "10,241,478", "--plant", "P2",
                "--dev", "--out", str(out), "--jobs", str(jobs), *extra])


def rowdoc(out: Path, pass_: str, row: int) -> dict:
    hits = sorted(out.rglob(f"ungated/{pass_}/row_{row:04d}.json"))
    assert len(hits) == 1, f"{len(hits)} files for row {row}"
    return json.loads(hits[0].read_bytes().decode("utf-8"))


def stat_view(d: dict) -> dict:
    return dict(outcome=d["outcome"], status=d["status_written"], result=d["result"],
                seeds=(d.get("row_provenance") or {}).get("seeds"), hashes=(d.get("inputs") or {}).get("hashes"))


# ================================================================================================================
# item 1
# ================================================================================================================
@check("r27_component_kind")
def _r27_component_kind():
    import a1_audit.reporting as RPT
    desc = dict(m=37, R2_grad=0.45, R2_absx=0.1, f=6, f_over_m=0.16, f_U=0.16, p_hypergeom=0.5, brain_enriched=False,
                r_yw_dB=0.0, c_S=0.03)
    a3_block = dict(reading="not detectable at this power",
                    labels=["species leg untested (gradient)", "power not measured in this class"],
                    power_columns=["V-AAL", "V-DK"], planted_class=False, reading_class="MIST64", donor_robustness=None,
                    gate_logic="removed")
    saved = (R.A3.descriptors, RPT.r27_reading)
    R.A3.descriptors = lambda ctx, y, S, parcel_ids=None: dict(desc)
    RPT.r27_reading = lambda rec, d, ctx, reparcellated=False, scope=None: dict(a3_block)
    try:
        prep = types.SimpleNamespace(S=[1, 2, 3], ctx=None, y=None, parcel_ids=None)
        out = {}
        for kind in ("component-permutation", "component-parametric", "full", "component"):
            vrec = dict(kind=kind, reading=COMP_READING, label=COMP_LABEL, primary_status="ok", survives=False)
            out[kind] = R.r27_for_map(prep, vrec, reparcellated=False, scope={})
    finally:
        R.A3.descriptors, RPT.r27_reading = saved
    for kind in ("component-permutation", "component-parametric"):
        b = out[kind]
        assert b["reading"] == COMP_READING, (kind, b["reading"])
        assert b["reading_r27"] == "not detectable at this power"
        assert b["labels"] == ["species leg untested (gradient)", "power not measured in this class"], b["labels"]
        assert "labels_not_applicable" not in b
        assert "not meaningful for a component claim" in b["labels_notes"]["species leg untested (gradient)"]
        assert b["component_label"] == COMP_LABEL and b["power_columns"] == ["V-AAL", "V-DK"]
        assert b["descriptors"]["m"] == 37
    for kind in ("full", "component"):   # never loosened beyond the kinds records carry
        b = out[kind]
        assert b["reading"] == "not detectable at this power" and "reading_r27" not in b
        assert "species leg untested (gradient)" in b["labels"] and "labels_notes" not in b
    return {}


@check("r27_descriptor_component_marked")
def _r27_descriptor_component_marked():
    import a1_audit.reporting as RPT
    import a1_audit.verdict as V
    computed = dict(form="component (PLSRegression)", kind="component-permutation", T=0.5, alpha=0.025,
                    two_sided=False, registered_direction=1, d_star=1, survives=False, passes_component_level=True,
                    reading="passes at component level (Level 0 and site leg at .025)", label=COMP_LABEL)
    verdict = V.descriptor_row_record(computed, "auditable (ungated)")
    assert verdict["descriptor_row"] and verdict["reading"].startswith(V.DESCRIPTIVE)
    saved = (R.A3.descriptors, RPT.r27_reading)
    R.A3.descriptors = lambda ctx, y, S, parcel_ids=None: dict(m=24, R2_grad=0.1)
    RPT.r27_reading = lambda rec, d, ctx, reparcellated=False, scope=None: dict(
        reading=str(rec["status"]), labels=["power not measured in this class"])
    try:
        prep = types.SimpleNamespace(S=[1, 2, 3], ctx=None, y=None, parcel_ids=None)
        b = R.r27_for_map(prep, R.r27_verdict_rec(verdict), reparcellated=False, scope={})
    finally:
        R.A3.descriptors, RPT.r27_reading = saved
    assert b["reading"] == verdict["reading"] and b["reading"].startswith(V.DESCRIPTIVE), b["reading"]
    texts = [v for k, v in b.items() if isinstance(v, str) and "passes at component level" in v]
    assert texts and all(t.startswith(V.DESCRIPTIVE) for t in texts), texts
    # a planted unmarked row reading is refused (fail closed)
    bad = dict(R.r27_verdict_rec(verdict), row_reading="passes at component level")
    try:
        R.component_r27(dict(reading="x", labels=[]), bad)
        raise AssertionError("an unmarked descriptor-row reading was accepted")
    except RuntimeError:
        pass
    return {"reading": b["reading"]}


@check("r27_relabel_file")
def _r27_relabel_file():
    import a1_audit.r27_relabel as RL
    f = ROOT / "arcs/audit/results/a1_run/ungated/r27_relabel_MOR-C.json"
    doc = json.loads(f.read_bytes().decode("utf-8"))
    rebuilt = RL.build()
    assert rebuilt["cells"] == doc["cells"], "the committed relabel file differs from a rebuild"
    got = {c: (v["per_map"]["0"]["old_code"]["reading"], v["per_map"]["0"]["new_code"]["reading"])
           for c, v in doc["cells"].items()}
    assert got == {"MOR-C1": ("not detectable at this power", COMP_READING),
                   "MOR-C2": ("not detectable at this power", COMP_READING),
                   "MOR-C3": ("auditable (ungated)", "descriptive (not a verdict): does not pass at alpha .025")}, got
    for c, v in doc["cells"].items():   # review B2: the labels are kept exactly as recorded
        assert v["per_map"]["0"]["new_code"]["labels"] == v["per_map"]["0"]["old_code"]["labels"], c
    return {"cells": got}


# ================================================================================================================
# item 2
# ================================================================================================================
def _jobs(tag: str, n: int, seconds: float, sleep: float, store_dir: Path, log: Path):
    from a1_audit import pace as PACE
    from a1_audit.tests import pace_child as PC
    store = A3.Checkpoints(store_dir, "codehash-test", "prewp4:pace")
    return [PACE.Job(f"t{k:02d}", dict(seed=1000 + k), dict(seed=1000 + k, seconds=seconds, sleep=sleep, log=str(log)),
                     store, PC.fake_task) for k in range(n)]


def _values(got: dict) -> dict:
    return {k: v["value"] for k, v in got.items()}


def _invocations(log: Path) -> dict:
    """{key: number of invocations} from pace_child's one-file-per-invocation marks."""
    out: dict = {}
    if log.exists():
        for f in log.iterdir():
            k = f.name.split(".")[0]
            out[k] = out.get(k, 0) + 1
    return out


@check("pacer_threshold")
def _pacer_threshold():
    from a1_audit import pace as PACE
    pc = PACE.Pacer(block="G2/descriptor", estimate_h=1.0)
    pc.count("a", {"_meta": {"seconds": 3600.0}})
    pc.count("a", {"_meta": {"seconds": 3600.0}})   # the same key counts once
    assert pc.cum_s == 3600.0 and not pc.check()
    pc.count("b", {"_meta": {"seconds": 3600.0}})
    assert pc.cum_s == 7200.0 and pc.check() is False, "triggered AT 2x"
    pc.count("c", {"_meta": {"seconds": 0.5}})
    assert pc.check() is True and pc.trigger["tasks_counted"] == 3, "not triggered above 2x"
    lifted = PACE.Pacer(block="x", estimate_h=1.0, armed=False)
    lifted.count("a", {"_meta": {"seconds": 1e6}})
    assert lifted.check() is False
    try:
        pc.count("d", {"_meta": {}})
        raise AssertionError("a payload without seconds was counted")
    except ValueError:
        pass
    return {}


def _pause_block(n_jobs: int, tag: str):
    from a1_audit import pace as PACE
    base = SCRATCH / f"pace_{tag}"
    log_u, log_p = base / "u_marks", base / "p_marks"
    # uninterrupted reference
    ref = PACE.run_jobs(_jobs(tag, 12, 100.0, 0.2, base / "u", log_u), n_jobs, log=lambda m: None)
    # at exactly 2x: 12 x 100 s = 1200 s = 2 x 600 s -> no pause
    exact = PACE.Pacer(block="t", estimate_h=600.0 / 3600.0)
    PACE.run_jobs(_jobs(tag, 12, 100.0, 0.0, base / "x", base / "x_marks"), n_jobs, log=lambda m: None, pacer=exact)
    assert not exact.paused and abs(exact.cum_s - 1200.0) < 1e-9
    # above 2x at the 9th checkpoint: estimate 400 s -> threshold 800 s
    pc = PACE.Pacer(block="t", estimate_h=400.0 / 3600.0)
    jobs = _jobs(tag, 12, 100.0, 0.2, base / "p", log_p)
    try:
        PACE.run_jobs(jobs, n_jobs, log=lambda m: None, pacer=pc)
        raise AssertionError("no pause above 2x")
    except PACE.Paused as e:
        rep = e.report
    done = rep["batch"]["jobs_done"]
    assert 9 <= done <= 9 + (n_jobs - 1), done
    assert rep["batch"]["jobs_remaining"] == 12 - done and rep["elapsed_process_h"] * 3600 >= 900 - 1e-9
    assert rep["threshold_process_h"] * 3600 == 800.0 and rep["projected_total_process_h"] * 3600 > 1199
    inv = _invocations(log_p)
    on_disk = sorted(p.name for p in (base / "p").glob("ck_t*.json"))
    assert len(on_disk) == done == sum(inv.values()), (len(on_disk), done, inv)   # nothing dispatched after the trigger
    # resume: the decision lifts the pause; finished tasks load from their checkpoints
    resumed = PACE.Pacer(block="t", estimate_h=400.0 / 3600.0, armed=False)
    got = PACE.run_jobs(_jobs(tag, 12, 100.0, 0.0, base / "p", log_p), n_jobs, log=lambda m: None, pacer=resumed)
    inv = _invocations(log_p)
    assert all(v == 1 for v in inv.values()) and len(inv) == 12, inv
    assert _values(got) == _values(ref)
    return {"jobs_done_at_pause": done}


@check("run_jobs_pause_pool")
def _pause_pool():
    return _pause_block(3, "pool")


@check("run_jobs_pause_inprocess")
def _pause_inprocess():
    return _pause_block(1, "inproc")


@check("runner_pause_resume")
def _runner_pause_resume():
    from a1_audit import pace as PACE
    tiny = SCRATCH / "tiny_estimates.json"
    tiny.write_text(json.dumps({"blocks": {"ungated/verdict": {"pause_estimate_process_h": 0.0001}}}),
                    encoding="utf-8")
    u, p, fresh = SCRATCH / "rp_u", SCRATCH / "rp_p", SCRATCH / "rp_fresh"
    code, out, err = p2(u, 2)
    assert code == 0, err[-500:]
    code, out, err = p2(p, 2, ["--block-estimates", str(tiny)])
    assert code == PACE.EXIT_PAUSED, (code, out[-500:], err[-500:])
    rd = p / "ungated" / "verdict"
    ev = json.loads((rd / PACE.PAUSES_FILE).read_bytes().decode("utf-8"))["events"]
    assert len(ev) == 1 and ev[0]["resumed"] is None
    rep = ev[0]["report"]
    for k in ("block", "estimate_process_h", "threshold_process_h", "elapsed_process_h", "batch",
              "projected_total_process_h"):
        assert k in rep, k
    assert rep["block"] == "ungated/verdict" and rep["elapsed_process_h"] > rep["threshold_process_h"]
    cks = {f.name: json.loads(f.read_bytes().decode("utf-8")) for f in (p / "_ck").rglob("ck_*.json")}
    assert cks, "no checkpoint before the pause"
    code, out, err = p2(p, 2, ["--block-estimates", str(tiny)])
    assert code == 2 and "paused" in out, (code, out[-300:])
    code, out, err = p2(fresh, 2, ["--block-estimates", str(tiny), "--resume-after-pause", "test: no pause here"])
    assert code == 2 and "no unresolved pause" in out, (code, out[-300:])
    code, out, err = p2(p, 2, ["--block-estimates", str(tiny), "--resume-after-pause", "test: synthetic resume"])
    assert code == 0, (code, out[-500:], err[-500:])
    ev = json.loads((rd / PACE.PAUSES_FILE).read_bytes().decode("utf-8"))["events"]
    assert ev[0]["resumed"]["decision"] == "test: synthetic resume"
    summ = json.loads((rd / "RUN_SUMMARY.json").read_bytes().decode("utf-8"))
    assert summ["pacing"]["pauses"][0]["resumed"]["decision"] == "test: synthetic resume"
    assert summ["pacing"]["armed"] is False
    after = {f.name: json.loads(f.read_bytes().decode("utf-8")) for f in (p / "_ck").rglob("ck_*.json")}
    for name, d in cks.items():   # finished before the pause: never recomputed (same bytes of record, same writer)
        assert after[name]["written"] == d["written"] and after[name]["pid"] == d["pid"], name
    for row in (10, 241, 478):
        assert stat_view(rowdoc(u, "verdict", row)) == stat_view(rowdoc(p, "verdict", row)), row
    lr = json.loads((rd / "launch_record.json").read_bytes().decode("utf-8"))["launch_record"]
    assert lr["block_estimates"]["pinned"] is False and len(lr["block_estimates"]["sha256"]) == 64
    return {"checkpoints_before_pause": len(cks)}


@check("block_estimates_pinned")
def _block_estimates_pinned():
    from a1_audit import pace as PACE
    from a1_audit import reprice as RP

    def args(**kw):
        base = dict(gate="G2", pass_="descriptor", plant=None, dry=False, dev=False, block_estimates=None)
        base.update(kw)
        return types.SimpleNamespace(**base)
    doc, rec = R.block_estimates_for(args())
    assert rec["pinned"] and rec["sha256"] == PACE.ESTIMATES_SHA256 and rec["block"] == "G2/descriptor"
    assert rec["pause_estimate_process_h"] == doc["blocks"]["G2/descriptor"]["pause_estimate_process_h"] > 97
    for p_ in ("verdict", "descriptor", "sensitivity"):
        try:
            R.block_estimates_for(args(gate="G1", pass_=p_))
            raise AssertionError("a G1 pass got an estimate")
        except PACE.EstimatesError:
            pass
        R.block_estimates_for(args(gate="none", pass_=p_))
    assert R.block_estimates_for(args(plant="P2")) == (None, None)
    bad = SCRATCH / "tampered.json"
    data = (ROOT / PACE.ESTIMATES_REL).read_bytes().replace(b"\r\n", b"\n")
    bad.write_bytes(data.replace(b'"pause_estimate_process_h": 7', b'"pause_estimate_process_h": 8', 1))
    assert bad.read_bytes() != data
    try:
        PACE.load_estimates(bad)
        raise AssertionError("a tampered estimate file was accepted")
    except PACE.EstimatesError:
        pass
    fresh = RP.build()   # the pinned estimates are what the script computes from the records now
    for k, v in fresh["blocks"].items():
        assert doc["blocks"][k]["pause_estimate_process_h"] == v["pause_estimate_process_h"], k
    ap_ = R.build_parser()
    for argv, why in ((["--block-estimates", "x.json"], "dev runs only"), (["--resume-after-pause", " "], "decision"),
                      (["--resume-after-pause", "ok", "--dry"], "dry")):
        a = ap_.parse_args(["--commit", "x", "--pass", "verdict", "--gate", "none", *argv])
        try:
            R.validate(a)
            raise AssertionError(f"accepted {argv}")
        except R.RunRefused as e:
            assert why in str(e.code), (argv, e.code)
    return {"G2/descriptor": rec["pause_estimate_process_h"]}


# ================================================================================================================
# item 3
# ================================================================================================================
@check("form_rows_in_pool")
def _form_rows_in_pool():
    import a1_audit.forms as FM
    import a1_audit.verdict as V
    outs = {}
    for jobs in (1, 3):
        out = SCRATCH / f"forms_j{jobs}"
        code, so, err = cli(["--commit", HEAD, "--pass", "descriptor", "--gate", "none", "--rows", "471-477",
                             "--plant", "P16", "--case", "0", "--dev", "--out", str(out), "--jobs", str(jobs),
                             "--K", CLI_K])
        assert code == 0, err[-500:]
        outs[jobs] = out
    K = R.parse_K(CLI_K, True)
    src = R.SyntheticSources(16, SCRATCH / "_no_data16", case=0)
    rows = R.register_for_diagnostics(ROOT)
    n_worker = 0
    for row in range(471, 478):
        a, b = rowdoc(outs[1], "descriptor", row), rowdoc(outs[3], "descriptor", row)
        assert stat_view(a) == stat_view(b), row
        ck = list(outs[3].rglob(f"ck_r{row:04d}_m0_form.json"))
        assert len(ck) == 1
        d = json.loads(ck[0].read_bytes().decode("utf-8"))
        assert d["pid"] != d["payload"]["_meta"]["pid"], f"row {row} computed in the parent"
        n_worker += 1
        if b["outcome"] == "computed":
            p = R.classify(rows[row - 1], plant_view=True)
            spec = p["liu_spec"]
            cid = FM.SYN_LIU_CLASS_ID[spec["data"]]
            sc = V.plant_seed_callables(16, 0, cid)
            ref = FM.liu_compute(spec, FM.synthetic_liu_inputs(src, p), K=K["sets"], seed_of=sc["seed_of"],
                                 g3_seed=sc["g3_seed"], two_sided=bool(p["two_sided"]),
                                 registered_direction=p["registered_direction"])
            ref = json.loads(json.dumps(A3.jsonable(ref)))
            got = b["result"]
            assert got["T"] == ref["T"] and got["legs"] == ref["legs"] and got["level2"] == ref["level2"], row
    return {"form_rows_in_workers": n_worker}


# ================================================================================================================
# item 4
# ================================================================================================================
@check("preload_and_coverage")
def _preload_and_coverage():
    out = SCRATCH / "rp_u"
    if not out.exists():
        code, _, err = p2(out, 2)
        assert code == 0, err[-300:]
    lr = json.loads((out / "ungated" / "verdict" / "launch_record.json").read_bytes().decode("utf-8"))["launch_record"]
    l11 = [a for a in lr["assertions"] if a["id"] == "L11"][0]
    mods = set((l11.get("observed") or {}).get("modules") or {})
    for m in ("wp3_repro.py", "repro.py", "pace.py", "real_sources.py", "forms.py", "reporting.py"):
        assert f"arcs/audit/src/a1_audit/{m}" in mods, m
    # a planted gap: L11 without repro.py -> DEFECT
    import a1_audit.launch as LA
    R.preload_pass_modules()
    loaded, _ = LA.code_modules(R.REPO)
    full = {k: "x" for k in loaded}
    gap = {k: v for k, v in full.items() if not k.endswith("a1_audit/repro.py")}
    for l11m, want in ((full, "ok"), (gap, "DEFECT")):
        fake = types.SimpleNamespace(refused=[], dev=False,
                                     _a=lambda aid, m=l11m: {"observed": {"modules": m}} if aid == "L11" else {})
        cov = R.code_coverage(fake)
        assert cov["status"] == want, (want, cov)
    assert cov["loaded_not_in_launch_hash"] == ["arcs/audit/src/a1_audit/repro.py"]
    return {"l11_modules": len(mods)}


@check("sensitivity_rule_donors")
def _sensitivity_rule_donors():
    src = R.SyntheticSources(2, SCRATCH / "_no_data2")
    rows = R.register_for_diagnostics(ROOT)
    p = R.classify(rows[477], plant_view=True)   # TSV row 478 (set-vs-map, V-DK)
    p = R.resolve_class(p, src)
    prim = R.prepare(p, src, p["maps"][0], "primary")
    sens = R.prepare(p, src, p["maps"][0], "donors>=2")
    assert ">= 2 donors" in sens.parcels["rule"] and "AHBA sample" not in sens.parcels["rule"], sens.parcels["rule"]
    assert ">= 1 AHBA sample(s)" in prim.parcels["rule"], prim.parcels["rule"]
    return {"rule": sens.parcels["rule"]}


def main() -> int:
    t0 = time.time()
    print(f"A1 pre-WP4 tests: scratch {SCRATCH}", flush=True)
    for run in CHECKS:
        run()
    out = SCRATCH / "test_prewp4_results.json"
    out.write_text(json.dumps(A3.jsonable(dict(results=RESULTS, failed=FAILED, seconds=round(time.time() - t0, 1))),
                              indent=1) + "\n", encoding="utf-8", newline="\n")
    back = json.loads(out.read_text(encoding="utf-8"))
    assert back["failed"] == FAILED
    print(f"{len(CHECKS) - len(FAILED)} of {len(CHECKS)} checks passed ({time.time() - t0:.0f}s)", flush=True)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
