"""P2 through the runner (arcs/audit/RUN_PLAN.md v3.1 §7 :1128 "2 reruns of 3 rows: bit-identical p's; keys and integer
seeds recorded; R24's G3 stream reproducible and different from leg 3's"), the dispatcher over all 692 TSV rows (dry,
no statistic), plant-mode G6l, the L14 glue, and the runner's refusals.

Run from arcs/audit/src:
    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_run_p2 [--scratch DIR] [--keep]
Exits non-zero if any check fails. Prints ASCII only.

Part A  P2. The keys of three real TSV rows - 478 (set-vs-map, V-DK, two-sided), 10 (decoded-list, V-AAL, two-sided,
        cell index 1, T_abs) and 241 (PLS-enrichment, V-AAL, one-sided -) - with SYNTHETIC maps, sets and class contexts
        (run.SyntheticSources, plant seeds) at plant K, G6l in plant mode. The dispatcher runs twice in separate
        processes (`--plant P2 --dev --out <scratch>`, run A with --jobs 1, run B with --jobs 3), each the verdict pass
        then the descriptor pass. Asserted: per-row statuses, every leg's p's, d*, the conjunction p and the recorded
        seeds bit-identical across the runs; every SeedSequence key = [20260925, 100 + target, row, leg, map, cell] and
        every integer seed recorded (R7); R24's G3 key = the first spawned child of leg 3's key, its stream reproducible
        and different from leg 3's; the runner's records equal an in-process recomputation through the library
        functions (verdict.claim_verdict_a1, descriptors.descriptor_pass / t_abs_legs) on the same synthetic inputs;
        a descriptor row (row 10, a descriptor cell) written through verdict.descriptor_row_record (B1: survives False,
        its TSV status, the conjunction p under 'descriptor');
        every output stamped DEV and written only under --out (the repository's status unchanged); a resumed run
        verifies its checkpoints and reproduces its records; a tampered checkpoint is refused; the >= 2-donor
        sensitivity pass reuses the claim's keys (R11); memory logged per row.
Part B  The dispatcher over all 692 rows in dry mode (views: gates closed, G2 open, G1 open, plant view), in-process
        and through the CLI: counts per route and per status-with-no-statistic, no stub left (WP2's forms.py replaced
        the four; the stub mechanism stays), no unexpected exception; the counts it must reproduce (re-verified from
        the dry dispatcher after WP2: gates closed 90 'not run (WP3 loader pending)', signed-weight route 27 rows under
        G2, plant view 483 + 24, CLI dry 507 would compute).
Part C  Plant-mode G6l (plant_mode.py) = the engine's g6l_sets(exact=False) bit for bit; the budget binds (5 K draws);
        a planted wrong budget is caught; exact mode is adapters.g6l_screen_safe unchanged (and tests/test_p0.py);
        RUN_PLAN_amend_1 R33: adapters.g6l_sets_range = the engine where the full range fits, and plant mode uses it
        in the partial-window range (no exception; windows valid).
Part D  L14 glue (l14_glue.py) against a FAKE carrier_test.py in a scratch git repository whose G1 record opens (P21's
        builder): its output passes launch.l14_compare; a planted differing record, a closed gate and a non-empty
        workdir are refused. The real carrier_test.py is never run.
Part A' exact-mode G6l through the runner (verdict.shared_g6l): row 10 and the two-cohort row 440 (one d* over
        both maps, P14) equal the library functions in-process; one screen per (S, class, parcels) serves every
        stream of the triple (legs 5 and 25 of both maps).
Part A'' component rows through the runner (PLSRegression(2) cumulative on S's columns, a fixed component, PLS1
        R2) equal verdict.claim_verdict_a1 in-process; their descriptor pass writes "no descriptor legs".
Part A''' the selected-list route (RA-11, row 208; RUN_PLAN_amend_1 R34) through the runner with a synthetic
        selection rule: equals verdict.claim_verdict_a1(adapters.SelectedList) in-process; a seed spy shows legs 0,
        1, 10 drawn and leg 8 never; Level 0 = SS(leg 10)'s permutation construction with re-selection.
Part E  CLI refusals before any launch (dev without plant, --out under arcs/audit/results, plant K on a real run, an
        unmapped lettered plant id, a row-keyed plant without --case, a WP2 battery plant with a run.py-only option,
        --case with P2, --out inside the repository).
Part F  the 2.5 GB memory defect flag (a planted low limit must flag); a --gate G2 dev dry run (the gate check runs
        and passes before any row is dispatched).

No real map, set, carrier or gated file is opened: the synthetic sources point every engine data path at a
non-existent directory, and a dev run never runs the privacy guard's self-test (it reads E:\\data\\asdg\\).
"""
from __future__ import annotations

import os

for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_k] = "1"   # as the runner forces it: bit-identity with the subprocesses' BLAS

import argparse  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1]
REPO = HERE.parents[4]
for _p in (REPO / "src", SRC):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from a1_audit import a3_port as A3  # noqa: E402
from a1_audit import adapters as AD  # noqa: E402
from a1_audit import descriptors as DS  # noqa: E402
from a1_audit import gate_launch  # noqa: E402
from a1_audit import l14_glue as LG  # noqa: E402
from a1_audit import launch as LA  # noqa: E402
from a1_audit import plant_mode as PM  # noqa: E402
from a1_audit import run as R  # noqa: E402
from a1_audit import seeds as SD  # noqa: E402
from a1_audit import verdict as V  # noqa: E402

ROWS = (478, 10, 241)
ROWS_ARG = ",".join(str(r) for r in ROWS)
RESULTS: list[tuple[str, bool]] = []
SEP = "-" * 100


def check(name: str, cond, detail: str = "") -> bool:
    ok = bool(cond)
    RESULTS.append((name, ok))
    print(R.ascii_line("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  [" + detail + "]") if detail else "")),
          flush=True)
    return ok


def canon(o) -> str:
    return json.dumps(A3.jsonable(o), sort_keys=True)


def git(*args) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True).stdout.decode("utf-8", "replace")


def head() -> str:
    return git("rev-parse", "HEAD").strip()


def porcelain() -> str:
    """The git status of every repository folder a runner could write results, records or manifests into (source
    folders are left out: other agents may edit code concurrently)."""
    return git("status", "--porcelain", "--untracked-files=all", "--", "arcs/audit/results", "arcs/audit/run_manifests",
               "arcs/audit/register_maps", "arcs/audit/register_sets", "artifacts")


def listing() -> list[str]:
    """Every file under the runner's real / plant output roots (they must not change in a dev run)."""
    out = []
    for rel in (R.RESULTS_REL, R.PLANTS_REL, R.CK_REAL_REL, R.CK_PLANT_REL, R.LAUNCH_REL):
        base = REPO / rel
        if base.exists():
            out += sorted(str(p.relative_to(REPO)) for p in base.rglob("*"))
    return out


def cli(args: list[str], timeout: int = 3600) -> tuple[int, list[str], str]:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, "-X", "utf8", "-u", "-m", "a1_audit.run", *args], cwd=str(SRC),
                       capture_output=True, env=env, timeout=timeout)
    return r.returncode, r.stdout.decode("utf-8", "replace").splitlines(), r.stderr.decode("utf-8", "replace")


def p2_run(out: Path, pass_: str, jobs: int, rows: str = ROWS_ARG, extra=()) -> tuple[int, list[str], str]:
    return cli(["--commit", HEAD, "--pass", pass_, "--gate", "none", "--rows", rows, "--plant", "P2", "--dev",
                "--out", str(out), "--jobs", str(jobs), *extra])


def load(out: Path, pass_: str, row: int) -> dict:
    return json.loads((out / "ungated" / pass_ / f"row_{row:04d}.json").read_bytes().decode("utf-8"))


def stat_view(doc: dict) -> dict:
    """What P2 compares across runs: outcome, statuses, the full result (every p), seeds and input hashes; never the
    times, host, paths, memory or provenance."""
    return dict(outcome=doc["outcome"], status_written=doc["status_written"], route=doc["route"],
                status_effective=doc["status_effective"], result=doc["result"],
                seeds=doc["row_provenance"]["seeds"], input_hashes=doc["row_provenance"]["input_hashes"],
                K=doc["K"], g6l_mode=doc["g6l_mode"])


# ================================================================================================================
# Part A: P2
# ================================================================================================================
def check_keys(doc: dict, pass_: str) -> list[str]:
    """R7: every key = [20260925, 100 + target, row, leg, map index, cell index]; integer seeds where used."""
    bad = []
    t, row = doc["target_number"], doc["row"]
    sd = doc["row_provenance"]["seeds"]
    if sd.get("row") != row or sd.get("target_number") != t or not sd.get("per_map"):
        return ["seed record head"]
    for rec in sd["per_map"]:
        mi, ci = rec["map_index"], rec["cell_index"]
        for leg in rec["legs"]:
            if leg["key"]["entropy"] != [20260925, 100 + t, row, leg["leg_no"], mi, ci] or leg["key"]["spawn_key"]:
                bad.append(f"{leg['leg']} key")
            if leg["use"] == "int" and not (isinstance(leg.get("seed_int"), int) and 0 <= leg["seed_int"] < 2 ** 31):
                bad.append(f"{leg['leg']} integer seed")
        names = {leg["leg"] for leg in rec["legs"]}
        if pass_ == "verdict" and not {"S1c", "S2c", "G1", "G3m", "G6s", "G6l"} <= names:
            bad.append("verdict legs missing")
        if pass_ == "descriptor":
            if not {"G1", "G2", "G4", "G5"} <= names:
                bad.append("descriptor legs missing")
            g3 = rec["G3"]["key"]
            if g3["entropy"] != [20260925, 100 + t, row, 3, mi, ci] or g3["spawn_key"] != [0]:
                bad.append("G3 key (R24)")
            if rec["J1"]["key"]["entropy"][3] != 14 or not all(isinstance(rec["J1"][k], int) for k in ("S1c_seed",
                                                                                                         "S2c_seed")):
                bad.append("J1 key / seeds")
            if rec["naive_joint"]["key"]["entropy"][3] != 15 or not isinstance(rec["naive_joint"]["S1_seed"], int):
                bad.append("naive joint key / seed")
    return bad


def part_a(scratch: Path) -> dict:
    print(SEP + "\nPart A: P2 through the runner (rows %s; synthetic sources; plant K; G6l plant mode)" % ROWS_ARG)
    rows = R.register_for_diagnostics(REPO)
    plans = {r: R.classify(rows[r - 1], plant_view=True) for r in ROWS}
    forms = {r: plans[r]["form"] for r in ROWS}
    check("A0 the three rows route to set-vs-map, decoded-list and PLS-enrichment (plant view)",
          [forms[r] for r in ROWS] == ["set-vs-map", "decoded-list", "PLS-enrichment"]
          and all(plans[r]["kind"] == "compute" for r in ROWS), json.dumps(forms))
    before = porcelain()
    before_listing = listing()
    outA, outB = scratch / "runA", scratch / "runB"
    runs = {}
    t0 = time.time()
    for name, out, jobs in (("A", outA, 1), ("B", outB, 3)):
        for pass_ in ("verdict", "descriptor"):
            code, lines, err = p2_run(out, pass_, jobs)
            runs[(name, pass_)] = (code, lines)
            check(f"A1 run {name} {pass_} (jobs {jobs}) exits 0", code == 0, err.strip().splitlines()[-1][:200]
                  if code and err.strip() else "")
            check(f"A1 run {name} {pass_}: console lines ASCII, every log line marked DEV",
                  all(ln.isascii() for ln in lines) and all("] DEV " in ln for ln in lines if ln.startswith("[")))
    print("  four runs: %.0f s" % (time.time() - t0))
    check("A2 the git status of results / run_manifests / register_maps / register_sets is unchanged (dev runs write "
          "only under --out)",
          porcelain() == before)
    check("A2 nothing written under arcs/audit/results/a1_run, run_manifests/plants or artifacts/audit",
          listing() == before_listing)
    docs = {(n, p_, r): load(o, p_, r) for n, o in (("A", outA), ("B", outB)) for p_ in ("verdict", "descriptor")
            for r in ROWS}
    stamps = {d["stamp"] for d in docs.values()}
    st = next(iter(stamps))
    # L11 (clean tree, HEAD = the commit) fails only where the tree is dirty (the main tree; a fresh worktree is clean)
    dirty = bool(git("status", "--porcelain", "--untracked-files=all").strip())
    check("A3 every row record stamped 'DEV (launch refused: ...)' with L13 among the failures (L11 iff the tree is "
          "dirty)", len(stamps) == 1 and st.startswith("DEV (launch refused: ") and "L13" in st
          and (("L11" in st) == dirty), f"{st} (dirty {dirty})")
    for out in (outA, outB):
        for p_ in ("verdict", "descriptor"):
            sm = json.loads((out / "ungated" / p_ / "RUN_SUMMARY.json").read_bytes().decode("utf-8"))
            lr = json.loads((out / "ungated" / p_ / "launch_record.json").read_bytes().decode("utf-8"))
            check(f"A3 {out.name} {p_}: summary and launch record stamped DEV; L13 not run (dev)",
                  sm["stamp"] == st and lr["stamp"] == st and sm["outcomes"] == {"computed": 3}
                  and "not run (dev run" in json.dumps([a["detail"] for a in lr["launch_record"]["assertions"]
                                                        if a["id"] == "L13"]))
    for r in ROWS:
        for p_ in ("verdict", "descriptor"):
            a, b = docs[("A", p_, r)], docs[("B", p_, r)]
            check(f"A4 row {r} {p_}: bit-identical across the two runs (p's, statuses, seeds, inputs)",
                  canon(stat_view(a)) == canon(stat_view(b)) and a["outcome"] == "computed")
            bad = check_keys(a, p_)
            check(f"A5 row {r} {p_}: keys [20260925, 100 + t, row, leg, map, cell] and integer seeds recorded",
                  not bad, ", ".join(bad))
            check(f"A5 row {r} {p_}: threads forced to 1, memory logged, no 2.5 GB defect",
                  set(a["threads"].values()) == {"1"} and a["memory"]["max_task_peak_bytes"] > 0
                  and a["memory"]["defect"] is False and a["memory"]["method"].startswith(("tracemalloc", "psutil")))
        v = docs[("A", "verdict", r)]["result"]["verdict"]
        print(R.ascii_line("  row %d %s: T %.6g d* %s p_conj %s status %s" % (
            r, forms[r], v["T"], v["d_star"], (v.get("descriptor") or v)["p_conjunction"], v["primary_status"])))
    # R24: the G3 stream
    for r in ROWS:
        fa = docs[("A", "descriptor", r)]["result"]["per_map"]["0"]["stream_fingerprints"]
        fb = docs[("B", "descriptor", r)]["result"]["per_map"]["0"]["stream_fingerprints"]
        g3n, l3n = "G3 (R24: first spawned child of leg 3's key)", "G3m (leg 3)"
        p = plans[r]
        want_g3 = R.stream_fingerprint(SD.g3_seed(p["target_no"], r, 0, p["cell_index"]))
        want_l3 = R.stream_fingerprint(SD.claim_seed(p["target_no"], r, 3, 0, p["cell_index"]))
        ga = docs[("A", "descriptor", r)]["result"]["per_map"]["0"]["legs"]["G3"]
        gb = docs[("B", "descriptor", r)]["result"]["per_map"]["0"]["legs"]["G3"]
        check(f"A6 row {r}: R24's G3 stream reproducible across runs and different from leg 3's",
              fa == fb and fa[g3n] == want_g3 and fa[l3n] == want_l3 and fa[g3n] != fa[l3n]
              and canon(ga) == canon(gb) and ga["status"] == "ok")
    # the runner's records = the library functions on the same synthetic inputs (in-process)
    src = R.SyntheticSources(2, scratch / "_no_data_direct")
    K = dict(R.PLANT_K)
    for r in ROWS:
        p = plans[r]
        pr = R.prepare(p, src, 0, "primary")
        sc = R.seeds_of(p, 0)
        streams = {"l5": R.stream_seed(p, 0, 5)}
        if p["t_abs"]:
            streams["l25"] = R.stream_seed(p, 0, 25)
        scr = PM.streams_screen(PM.MODE_PLANT, pr.ctx, pr.S, streams, K["species"])
        v = V.claim_verdict_a1(pr.adapter, R.verdict_K(K), sc["seed_of"], two_sided=p["two_sided"],
                               registered_direction=p["registered_direction"], g6l=scr["l5"],
                               by_construction_label=p["by_construction_label"])
        got_v = docs[("A", "verdict", r)]["result"]["verdict"]
        check(f"A7 row {r}: runner verdict == verdict.claim_verdict_a1 in-process (bit-identical; a descriptor row "
              "through verdict.descriptor_row_record, B1)", canon(R.verdict_for_plan(p, v)) == canon(got_v)
              and (not p["descriptor"] or (got_v["survives"] is False and got_v["primary_status"] == p["status_effective"]
                                           and got_v["descriptor"]["p_conjunction"] == v["p_conjunction"]
                                           and got_v["descriptor"]["passes_at_alpha"] == v["survives"])),
              "conjunction p %s (%s)" % ((got_v.get("descriptor") or got_v).get("p_conjunction"),
                                         "under 'descriptor' (B1)" if p["descriptor"] else "top level"))
        d = v["d_star"] if p["two_sided"] else p["registered_direction"]
        traj, _ = src.trajectories(p["analysis_class"])
        ds = DS.descriptor_pass(pr.adapter, sc["seed_of"], sc["g3_seed"], K_sets=K["sets"], K_surr=K["surr"],
                                K_j1_sets=K["j1_sets"], traj=traj, species=None, direction=d,
                                two_sided=p["two_sided"])
        got_d = docs[("A", "descriptor", r)]["result"]["per_map"]["0"]
        check(f"A7 row {r}: runner descriptors == descriptors.descriptor_pass in-process (bit-identical)",
              canon(ds) == canon({k: got_d[k] for k in ds}))
        if p["t_abs"]:
            tb = AD.TAbs(pr.ctx, pr.y, pr.S, parcel_ids=pr.parcel_ids)
            ta = DS.t_abs_legs(tb, {"site": K["site"], "species": K["species"]}, sc["tabs_seed_of"],
                               depletion=p["depletion"], g6l=scr["l25"])
            check(f"A7 row {r}: runner T_abs == descriptors.t_abs_legs in-process; leg 25 served by the verdict "
                  "pass's shared screen", canon(ta) == canon(got_d["T_abs"])
                  and got_d["T_abs_g6l_screen"] == "verdict pass shared screen")
    # resume: verified from checkpoints, same records
    code, lines, err = p2_run(outA, "verdict", 1)
    resumed = [ln for ln in lines if "resume:" in ln]
    check("A8 a resumed run verifies every checkpoint (0 to run) and reproduces its records",
          code == 0 and len(resumed) == 2 and all(" 0 to run" in ln for ln in resumed)
          and all(canon(stat_view(load(outA, "verdict", r))) == canon(stat_view(docs[("A", "verdict", r)]))
                  for r in ROWS), " | ".join(x.split("] ", 1)[-1] for x in resumed))
    # planted: a tampered checkpoint (another run's seeds) is refused
    outT = scratch / "runT"
    shutil.copytree(outA, outT)
    ck = outT / "_ck" / "ungated" / "verdict" / "ck_r0010_m0_legs.json"
    doc = json.loads(ck.read_text(encoding="utf-8"))
    doc["expect"]["seeds"]["S1c"]["entropy"][2] = 11
    ck.write_text(json.dumps(doc), encoding="utf-8")
    code, lines, err = p2_run(outT, "verdict", 1)
    check("A9 planted: a checkpoint with other seeds is refused (CheckpointError), nothing resumed from it",
          code != 0 and "not this run's" in err, err.strip().splitlines()[-1][:160] if err.strip() else "")
    # sensitivity (R11): >= 2-donor parcels, the claim's own keys
    code, lines, err = p2_run(outA, "sensitivity", 1, rows="478")
    sdoc = load(outA, "sensitivity", 478)
    vdoc = docs[("A", "verdict", 478)]
    prim = vdoc["inputs"]["parcel_ids"]["0"]
    red = (sdoc.get("inputs") or {}).get("parcel_ids", {}).get("0", [])
    check("A10 sensitivity pass (row 478): >= 2-donor parcels (a strict subset here), the verdict re-run with the "
          "claim's keys (common random numbers, R11)",
          code == 0 and sdoc["outcome"] == "computed" and sdoc["inputs"]["rule"] == "donors>=2"
          and set(red) < set(prim) and canon(sdoc["row_provenance"]["seeds"]) == canon(vdoc["row_provenance"]["seeds"])
          and sdoc["result"]["parcel_set"] == "changed" and "verdict" in sdoc["result"],
          f"parcels {len(red)} of {len(prim)}")
    return dict(plans=plans)


# ================================================================================================================
# Part A': exact-mode G6l through the runner, a two-cohort row, one shared screen for several streams
# ================================================================================================================
def part_a_exact(scratch: Path) -> None:
    print(SEP + "\nPart A': exact-mode G6l (verdict.shared_g6l) through the runner; two-cohort row 440 (P14)")
    rows = R.register_for_diagnostics(REPO)
    out = scratch / "runC"
    code, lines, err = p2_run(out, "verdict", 2, rows="10,440", extra=("--g6l", "exact"))
    check("A'1 exact-mode run (rows 10, 440) exits 0", code == 0, err.strip().splitlines()[-1][:200]
          if code and err.strip() else "")
    if code:
        return
    src = R.SyntheticSources(2, scratch / "_no_data_exact")
    K = dict(R.PLANT_K)
    p = R.classify(rows[9], plant_view=True)
    pr = R.prepare(p, src, 0, "primary")
    sc = R.seeds_of(p, 0)
    sh = V.shared_g6l(pr.ctx, pr.S, {"l5": R.stream_seed(p, 0, 5), "l25": R.stream_seed(p, 0, 25)}, K["species"])
    v = V.claim_verdict_a1(pr.adapter, R.verdict_K(K), sc["seed_of"], two_sided=True, g6l=sh["l5"])
    got = load(out, "verdict", 10)
    check("A'2 row 10, exact G6l: runner verdict == claim_verdict_a1 with verdict.shared_g6l (bit-identical); the "
          "screen is exact; descriptor row: the conjunction p under 'descriptor' (B1)",
          canon(R.verdict_for_plan(p, v)) == canon(got["result"]["verdict"])
          and got["result"]["verdict"]["descriptor"]["p_conjunction"] == v["p_conjunction"]
          and got["result"]["verdict"]["survives"] is False and v["g6l"]["status"] in ("ok", "unmatched",
                                                                                                    "degenerate")
          and got["g6l_mode"] == "exact")
    p4 = R.classify(rows[439], plant_view=True)
    check("A'3 row 440 is a two-cohort decoded-list row (map index '0 = ABIDE I; 1 = ABIDE II'), one-sided",
          p4["two_cohort"] and p4["maps"] == [0, 1] and p4["form"] == "decoded-list" and p4["two_sided"] is False)
    prs = {mi: R.prepare(p4, src, mi, "primary") for mi in (0, 1)}
    scs = {mi: R.seeds_of(p4, mi) for mi in (0, 1)}
    shs = {mi: V.shared_g6l(prs[mi].ctx, prs[mi].S, {"l5": R.stream_seed(p4, mi, 5)}, K["species"])["l5"]
           for mi in (0, 1)}
    tc = V.two_cohort_verdict(prs[0].adapter, prs[1].adapter, R.verdict_K(K), scs[0]["seed_of"], scs[1]["seed_of"],
                              two_sided=False, registered_direction=p4["registered_direction"], g6l_a=shs[0],
                              g6l_b=shs[1], map_labels=("map 0 = ABIDE I", "map 1 = ABIDE II"))
    got4 = load(out, "verdict", 440)
    check("A'4 row 440: runner two-cohort verdict == verdict.two_cohort_verdict in-process (bit-identical); one d*; "
          "each map on its own keys (map index 0 / 1)", canon(tc) == canon(got4["result"]["verdict"])
          and [m["map_index"] for m in got4["row_provenance"]["seeds"]["per_map"]] == [0, 1],
          "survives %s, p %s" % (tc["survives"], tc["p_conjunction"]))
    ck = sorted((out / "_ck" / "ungated" / "verdict").glob("ck_g6l_*.json"))
    streams = [sorted(json.loads(f.read_text(encoding="utf-8"))["payload"]["streams"]) for f in ck]
    want = sorted(R.stream_name(440, mi, leg) for mi in (0, 1) for leg in (5, 25))
    check("A'5 one exact screen per (S, class, parcels) served every stream of the triple (row 440: legs 5 and 25 of "
          "both maps in ONE screen)", want in streams and len(ck) == 2, json.dumps(streams))


def part_a_components(scratch: Path) -> None:
    print(SEP + "\nPart A'': component rows through the runner (615 PLSRegression(2) cumulative on S's columns, 624 "
          "fixed component, 133 PLS1 R2)")
    rows = R.register_for_diagnostics(REPO)
    out = scratch / "runD"
    code, lines, err = p2_run(out, "verdict", 2, rows="615,624,133")
    code2, _, _ = p2_run(out, "descriptor", 1, rows="615,624,133")
    check("A''1 component runs exit 0 (verdict, descriptor)", code == 0 and code2 == 0,
          err.strip().splitlines()[-1][:200] if code and err.strip() else "")
    if code or code2:
        return
    src = R.SyntheticSources(2, scratch / "_no_data_comp")
    K = dict(R.PLANT_K)
    kinds = {}
    for r in (615, 624, 133):
        p = R.classify(rows[r - 1], plant_view=True)
        kinds[r] = p["component"]["kind"]
        pr = R.prepare(p, src, 0, "primary")
        sc = R.seeds_of(p, 0)
        v = V.claim_verdict_a1(pr.adapter, R.verdict_K(K), sc["seed_of"], two_sided=p["two_sided"],
                               registered_direction=p["registered_direction"])
        got = load(out, "verdict", r)
        d = load(out, "descriptor", r)
        check(f"A''2 row {r} ({p['component']['kind']}): runner component verdict == claim_verdict_a1 in-process; "
              "never a survival; descriptor pass writes 'no descriptor legs'",
              canon(v) == canon(got["result"]["verdict"]) and got["result"]["verdict"]["survives"] is False
              and d["status_written"] == R.NO_DESCRIPTOR_COMPONENT, got["result"]["verdict"]["reading"])
    check("A''3 the three component kinds were exercised (plsr on S's columns, fixed, pls1-r2)",
          kinds == {615: "plsr", 624: "fixed", 133: "pls1-r2"}, json.dumps(kinds))


def part_a_selected(scratch: Path) -> None:
    print(SEP + "\nPart A''': the selected-list route (RA-11, TSV row 208; RUN_PLAN_amend_1 R34; P13-style) through the "
          "runner")
    rows = R.register_for_diagnostics(REPO)
    p = R.classify(rows[207], plant_view=True)
    check("A'''0 row 208 routes to adapters.SelectedList (component, one-sided -, conditional class)",
          p["route"] == "verdict: component (selected list)" and p["registered_direction"] == -1
          and "class" in p["preconditions"] and "carrier" in p["preconditions"])
    out = scratch / "runE"
    code, lines, err = p2_run(out, "verdict", 1, rows="208")
    code2, _, _ = p2_run(out, "descriptor", 1, rows="208")
    check("A'''1 selected-list runs exit 0 (verdict, descriptor)", code == 0 and code2 == 0,
          err.strip().splitlines()[-1][:200] if code and err.strip() else "")
    if code or code2:
        return
    doc, ddoc = load(out, "verdict", 208), load(out, "descriptor", 208)
    src = R.SyntheticSources(2, scratch / "_no_data_sel")
    K = dict(R.PLANT_K)
    q = R.resolve_class(p, src)
    pr = R.prepare(q, src, 0, "primary")
    asked = []
    sc = R.seeds_of(q, 0)

    def spy(leg):
        asked.append(leg)
        return sc["seed_of"](leg)
    v = V.claim_verdict_a1(pr.adapter, R.verdict_K(K), spy, two_sided=False, registered_direction=-1)
    check("A'''2 runner verdict == verdict.claim_verdict_a1(SelectedList) in-process (bit-identical); Level-0 kind = "
          "SelectedList.LEVEL0_KIND; never a survival",
          canon(v) == canon(doc["result"]["verdict"]) and isinstance(pr.adapter, AD.SelectedList)
          and doc["result"]["verdict"]["legs"]["Level 0"]["kind"] == AD.SelectedList.LEVEL0_KIND
          and doc["result"]["verdict"]["survives"] is False, doc["result"]["verdict"]["reading"])
    check("A'''3 seed spy: legs 0, 1 and 10 requested; leg 8 ('permutation') never", set(asked) == {
        "S1c", "S2c", "re-selection"}, json.dumps(sorted(set(asked))))
    legs = {d["leg"]: d for d in doc["row_provenance"]["seeds"]["per_map"][0]["legs"]}
    check("A'''4 recorded keys: re-selection = [20260925, 100 + target, 208, 10, 0, 0]; no leg-8 key; S1c / S2c "
          "integer seeds", legs["re-selection"]["key"]["entropy"] == [20260925, 100 + p["target_no"], 208, 10, 0, 0]
          and "permutation / label" not in legs and all(isinstance(legs[k].get("seed_int"), int) for k in ("S1c", "S2c")))
    y = pr.y
    Kp = K["permutation"]
    perm10 = np.random.default_rng(sc["seed_of"]("re-selection")).permuted(np.tile(y, (Kp, 1)), axis=1)
    perm8 = np.random.default_rng(sc["seed_of"]("permutation")).permuted(np.tile(y, (Kp, 1)), axis=1)
    lp = pr.adapter.level0_perm(Kp, sc["seed_of"])
    check("A'''5 Level-0 rows = SS(leg 10)'s construction (refit with re-selection), not SS(leg 8)'s; empty lists "
          "reached (T = 0) or not, recorded", np.array_equal(lp["null"], pr.adapter.T_maps(perm10))
          and not np.array_equal(perm10, perm8),
          f"empty-list maps in the Level-0 null: {int(np.sum(lp['null'] == 0.0))} of {Kp}")
    check("A'''6 plant view notes recorded (carrier taken as passed; class taken as dk-ctx); the selection rule hashed",
          any("carrier test taken as passed" in n for n in doc.get("notes", []))
          and any("dk-ctx" in n for n in doc.get("notes", [])) and "selection_rule" in doc["inputs"]["hashes"]
          and ddoc["status_written"] == R.NO_DESCRIPTOR_COMPONENT)
    idc = doc["result"]["identity_counts"]["0"]
    check("A'''7 identity counts carried into the output (R32 (a); sampled legs at plant K: None)",
          set(idc) == {"S1c", "S2c", "G6s"}, json.dumps(idc))


# ================================================================================================================
# Part F: the memory defect flag (planted) and a gated dev dry run (the gate check before any material)
# ================================================================================================================
def part_f(scratch: Path) -> None:
    print(SEP + "\nPart F: memory defect flag (planted limit) and a --gate G2 dev dry run")
    with R.MemProbe() as mp:
        x = np.ones((1000, 1000))
        del x
    ok_normal = mp.result["defect"] is False and mp.result["task_peak_bytes"] >= 8_000_000
    keep = R.JOB_LIMIT_BYTES
    R.JOB_LIMIT_BYTES = 1000
    try:
        with R.MemProbe() as mp2:
            y = np.ones((100, 100))
            del y
    finally:
        R.JOB_LIMIT_BYTES = keep
    check("F1 MemProbe measures a task (8 MB array seen) and flags a job above the limit (planted 1 kB limit)",
          ok_normal and mp2.result["defect"] is True,
          f"method {mp.result['method']}; process peak WS {mp.result['process_peak_working_set_bytes']}")
    out = scratch / "g2dry"
    before = porcelain()
    code, lines, err = cli(["--commit", HEAD, "--pass", "verdict", "--gate", "G2", "--rows", "81-131", "--plant", "P2",
                            "--dev", "--out", str(out), "--jobs", "1", "--dry"])
    f = out / "G2" / "verdict" / "DISPATCH.json"
    doc = json.loads(f.read_bytes().decode("utf-8")) if f.is_file() else {}
    lr = json.loads((out / "G2" / "verdict" / "launch_record.json").read_bytes().decode("utf-8")) if f.is_file() else {}
    l15 = [a for a in (lr.get("launch_record") or {}).get("assertions", []) if a["id"] == "L15"]
    check("F2 --gate G2 dev dry run: the G2 check passed before any row (L15 pass; require_step3v_open), rows "
          "81-131 dispatched, results under G2/, repo untouched",
          code == 0 and doc.get("gate") == "G2" and doc["counts"]["n"] == 51 and l15 and l15[0]["status"] == "pass"
          and porcelain() == before, json.dumps(doc.get("counts", {}).get("by_outcome")))


# ================================================================================================================
# Part B: the dispatcher over all 692 rows
# ================================================================================================================
def part_b(scratch: Path) -> None:
    print(SEP + "\nPart B: the dispatcher over all 692 TSV rows (dry: no statistic)")
    rows = R.register_for_diagnostics(REPO)
    check("B0 TSV parsed at the L2 pin: 692 rows", len(rows) == 692)
    views = {"gates closed": (frozenset(), False), "G2 open": (frozenset({"G2"}), False),
             "G1 open": (frozenset({"G1"}), False), "plant view": (frozenset(), True)}
    allc, allr = {}, {}
    for name, (og, pv) in views.items():
        try:
            recs = R.dry_dispatch(rows, og, plant_view=pv, sources=R.RealSources())
            exc = None
        except Exception as e:  # noqa: BLE001
            recs, exc = [], f"{type(e).__name__}: {e}"
        check(f"B1 {name}: every row dispatched, no unexpected exception", exc is None and len(recs) == 692, exc or "")
        c = R.dispatch_counts(recs)
        allc[name] = c
        allr[name] = recs
        print("  %s: outcomes %s" % (name, json.dumps(c["by_outcome"])))
        for k, v in c["by_route"].items():
            print(R.ascii_line("     %4d  %s" % (v, k)))
        print("     -- not computed, by status:")
        for k, v in c["no_statistic_by_status"].items():
            print(R.ascii_line("     %4d  %s" % (v, k[:150])))
        stubs = [r for r in recs if r["outcome"] == "stub"]
        check(f"B2 {name}: every stub raised its named NotImplementedError (WP2 ...)",
              all(r["status"].startswith("not run (stub: WP2: ") for r in stubs), f"{len(stubs)} stubs")
        check(f"B2 {name}: outcomes sum to 692", sum(c["by_outcome"].values()) == 692)
    print("  index forms (all rows): map %s; cell %s" % (json.dumps(allc["gates closed"]["index_forms"]["map"]),
                                                         json.dumps(allc["gates closed"]["index_forms"]["cell"])))
    cl, g1, g2, pl = (allc[k] for k in ("gates closed", "G1 open", "G2 open", "plant view"))
    check("B3 gates closed: 583 deferred (G1 380 + G2 194 + G1+G2 3 + Vairam / Roy 6)",
          cl["by_route"].get("no statistic: deferred") == 583)
    wp3_closed = sorted(r["row"] for r in allr["gates closed"] if r["status"] == R.NOT_RUN_WP3
                        and r["route"] not in ("verdict: decoded-list", "verdict: component (plsr)"))
    check("B3 gates closed: ungated computing rows = Segura 78 decoded-list + MOR-C1..C3 + Liu 7 (TSV 471-477, R10) + "
          "MOR-T 2 (TSV 618-619, R21) = 90, all 'not run (WP3 loader pending)' (WP2 replaced the stubs)",
          cl["by_route"].get("verdict: decoded-list") == 78
          and cl["by_route"].get("verdict: component (plsr)") == 3
          and cl["by_route"].get(R.ROUTE_FORM["liu"]) == 7
          and cl["by_route"].get("verdict: decoded-list (" + R.ROUTE_NOTE_R21 + ")") == 2
          and wp3_closed == [471, 472, 473, 474, 475, 476, 477, 618, 619]
          and cl["no_statistic_by_status"].get(R.NOT_RUN_WP3) == 90, json.dumps(wp3_closed))
    sw_route = sorted(r["row"] for r in allr["G2 open"] if r["route"] == R.ROUTE_FORM["signed-weight"])
    check("B3 signed-weight route (forms.py, P15): 27 rows (103-117 by the status; 120-131 by the T column, U9) under "
          "G2; no stub route left", g2["by_route"].get(R.ROUTE_FORM["signed-weight"]) == 27
          and sw_route == list(range(103, 118)) + list(range(120, 132))
          and not any(k.startswith("stub") for k in g2["by_route"]))
    sw = [r.row for r in rows if R.LD.effective_status(r, {"G2"}).startswith(R.SIGNED_WEIGHT_STATUS)]
    check("B3 the signed-weight status is held by exactly TSV rows 103-117 (RUN_PLAN §4 :357-360)",
          sw == list(range(103, 118)))
    rl = [r.row for r in rows if R.LD.effective_status(r, {"G2"}).startswith(R.RESLIM_STATUS)]
    check("B3 the by-construction resolution-limited status is held by exactly rows 92, 94, ..., 102 (R9)",
          rl == [92, 94, 96, 98, 100, 102])
    check("B3 G1 open: conditional rows wait for their carrier test (WP5)",
          g1["no_statistic_by_status"].get(R.NOT_RUN_CONDITIONAL, 0) > 0)
    pw = {}
    for r in allr["plant view"]:
        if r["status"] == R.NOT_RUN_WP3 and (r["route"] in R.ROUTE_FORM.values() or "descriptor: " in r["route"]):
            pw[r["route"]] = pw.get(r["route"], 0) + 1
    check("B3 plant view: no row reaches a statistic with real sources (483 'not run (WP3 loader pending)' = the 444 "
          "verdict-route rows + signed-weight 27 + Liu 7 + R28 3 + R21 2, 24 'not run (analysis class conditional "
          "...)': real sources determine no class)",
          pl["by_outcome"].get("would compute", 0) == 0 and pl["no_statistic_by_status"].get(R.NOT_RUN_WP3) == 483
          and pw == {R.ROUTE_FORM["signed-weight"]: 27, R.ROUTE_FORM["liu"]: 7,
                     "verdict: decoded-list (" + R.ROUTE_NOTE_R28 + ")": 3,
                     "verdict: decoded-list (" + R.ROUTE_NOTE_R21 + ")": 2}
          and pl["no_statistic_by_status"].get(R.NOT_RUN_CLASS) == 24, json.dumps(pw))
    sel = [r.row for r in rows if R.classify(r, frozenset({"G1"}))["route"] == "verdict: component (selected list)"]
    check("B3 the selected-list route (adapters.SelectedList, RUN_PLAN_amend_1 R34) holds exactly TSV rows 208-211; no "
          "re-selection stub remains", sel == [208, 209, 210, 211] and not any("re-selection" in k for k in
                                                                                g1["by_route"]))
    # the CLI's dry mode (plant view, synthetic sources): every computing row 'would compute'
    out = scratch / "dry"
    before = porcelain()
    code, lines, err = cli(["--commit", HEAD, "--pass", "verdict", "--gate", "none", "--rows", "1-692", "--plant", "P2",
                            "--dev", "--out", str(out), "--jobs", "1", "--dry"])
    ok = code == 0 and (out / "ungated" / "verdict" / "DISPATCH.json").is_file()
    doc = json.loads((out / "ungated" / "verdict" / "DISPATCH.json").read_bytes().decode("utf-8")) if ok else {}
    c = doc.get("counts", {})
    check("B4 CLI --dry (plant view, synthetic sources): 692 rows dispatched; 507 would compute (the 483 + the 24 rows "
          "whose conditional class the plant view resolves, U2); stamped DEV; repo "
          "untouched", ok and c.get("n") == 692 and c["by_outcome"].get("would compute") == 507
          and doc.get("stamp", "").startswith("DEV (launch refused") and porcelain() == before,
          json.dumps(c.get("by_outcome")))


# ================================================================================================================
# Part C: plant-mode G6l
# ================================================================================================================
def part_c(scratch: Path) -> None:
    print(SEP + "\nPart C: plant-mode G6l (prereg_amend_3.md:130-132) vs the engine; exact mode untouched")
    from asdg.species import WithinClassBasis
    src = R.SyntheticSources(9, scratch / "_no_data_c")
    ctx, _, _ = src.context("dk-ctx")
    S = np.arange(40, 65)
    for seed in (1, 2):
        a = PM.g6l_plant_screen(ctx.B, S, [np.random.default_rng(seed)], 200)[0]
        b = ctx.B.g6l_sets(S, 200, np.random.default_rng(seed), exact=False)
        same = (a[0] is None and b[0] is None) or (a[0] is not None and b[0] is not None
                                                   and np.array_equal(a[0], b[0]))
        check(f"C1 plant screen (seed {seed}) == engine g6l_sets(exact=False): sets and info",
              same and all(a[1][k] == b[1][k] for k in b[1]) and a[1]["n_used"] == (0 if a[0] is None else len(a[0])),
              f"status {a[1]['status']}, n {a[1]['n']}, draws {a[1]['draws']}")
    # the budget binds: a larger synthetic basis where S is a tight module (c_S high) and no window of noise genes
    # reaches it, so the screen runs to its budget of 5 K seed draws
    rng = np.random.default_rng(3)
    P, G, m = 30, 1500, 25
    cl = np.array(["cortex"] * P)
    X = rng.standard_normal((P, 5)) @ rng.standard_normal((5, G)) * 0.3 + rng.standard_normal((P, G))
    X[:, :m] += 3.0 * rng.standard_normal(P)[:, None]
    B = WithinClassBasis(X, cl, brain=np.arange(0, 300))
    S2 = np.arange(m)
    K = 200
    sets, info = PM.g6l_plant_screen(B, S2, [np.random.default_rng(4)], K)[0]
    eng = B.g6l_sets(S2, K, np.random.default_rng(4), exact=False)
    check("C2 plant mode: the budget binds (draws = 5 K = 1,000 < the 1,475 candidate seeds) and the result equals "
          "the engine's", info["draws"] == 5 * K == info["budget"] and all(info[k] == eng[1][k] for k in eng[1])
          and ((sets is None and eng[0] is None) or np.array_equal(sets, eng[0])),
          f"c_S {info['c_s']:.3f}, draws {info['draws']}, eligible {info['eligible']}, status {info['status']}")
    wrong = B.g6l_sets(S2, K, np.random.default_rng(4), budget_factor=4, exact=False)
    check("C3 planted: a wrong budget (4 K) gives another screen (fewer draws), so the equality check catches it",
          wrong[1]["draws"] == 4 * K != info["draws"], f"wrong-budget draws {wrong[1]['draws']}")
    # RUN_PLAN_amend_1 R33: adapters.g6l_sets_range equals the engine where the full range fits (asserted on a
    # synthetic case), and plant mode uses it where a window fits only part of the offset range
    full = AD.g6l_sets_range(ctx.B, S, 200, np.random.default_rng(7), exact=False)
    eng = ctx.B.g6l_sets(S, 200, np.random.default_rng(7), exact=False)
    check("C6 R33: adapters.g6l_sets_range == the engine's g6l_sets (plant mode) where the full offset range fits",
          ((full[0] is None and eng[0] is None) or np.array_equal(full[0], eng[0])) and full[1] == eng[1],
          f"status {full[1]['status']}")
    rng = np.random.default_rng(8)
    Pp, Gp = 20, 150
    Xp = rng.standard_normal((Pp, 3)) @ rng.standard_normal((3, Gp)) + 0.5 * rng.standard_normal((Pp, Gp))
    Bp = WithinClassBasis(Xp, np.array(["cortex"] * Pp), brain=np.arange(0, 30))
    for mp in (51, 60, 75):
        Sp = np.arange(mp)
        st = AD.pool_status(Bp, Sp)["G6l"]
        a = PM.g6l_plant_screen(Bp, Sp, [np.random.default_rng(9)], 200)[0]
        b = AD.g6l_sets_range(Bp, Sp, 200, np.random.default_rng(9), exact=False)
        omax = AD.g6l_offset_max(Gp, mp)
        ok_sets = a[0] is None or all(len(set(w.tolist())) == mp and not set(w.tolist()) & set(Sp.tolist())
                                      for w in a[0])
        check(f"C7 R33 plant mode, partial window (G 150, m {mp}): no exception; = adapters.g6l_sets_range; every "
              "window has m distinct genes outside S", st == "partial" and ok_sets
              and ((a[0] is None and b[0] is None) or np.array_equal(a[0], b[0]))
              and all(a[1][k] == b[1][k] for k in b[1]) and a[1]["offset_range"].endswith(f"[0, {omax}]"),
              f"status {a[1]['status']}, eligible {a[1]['eligible']}, draws {a[1]['draws']}")
    ex = PM.screen(PM.MODE_EXACT, ctx.B, S, [np.random.default_rng(5), np.random.default_rng(6)], 200)
    ref = AD.g6l_screen_safe(ctx.B, S, [np.random.default_rng(5), np.random.default_rng(6)], keep=200)
    check("C4 exact mode = adapters.g6l_screen_safe (untouched)",
          all(((x[0] is None and y[0] is None) or np.array_equal(x[0], y[0])) and x[1] == y[1] for x, y in zip(ex, ref)))
    try:
        PM.screen("other", ctx.B, S, [np.random.default_rng(1)], 200)
        check("C5 an unknown G6l mode is refused", False)
    except ValueError:
        check("C5 an unknown G6l mode is refused", True)


# ================================================================================================================
# Part D: L14 glue
# ================================================================================================================
FAKE_CARRIER = r'''
import json, pathlib, sys
args = sys.argv[1:]
assert args[0] == "selftest" and args[1] == "--workdir" and len(args) == 3, args
w = pathlib.Path(args[2])
(w / "fake_carrier_sentinel.txt").write_bytes(b"fake carrier ran")
rec = {"n_cases": 46, "n_caught": 46, "pdf_adapter": {"pdfplumber": "0.11.10"}, "cases": ["synthetic"] * 3,
       "variant": VARIANT, "run": {"utc": "2026-10-01T00:00:00Z", "workdir": str(w)}}
(w / "carrier_tests_selftest.json").write_text(json.dumps(rec), encoding="utf-8")
print("synthetic case line")
print("selftest: 46 / 46 cases classified as planted")
print("record EQUAL to the frozen arcs/audit/register_maps/carrier_tests_selftest.json (run stamps aside)")
'''


def part_d(scratch: Path) -> None:
    print(SEP + "\nPart D: L14 glue (gate launcher --carrier-test output -> launch.l14_compare), FAKE carrier only")
    from a1_audit.tests import test_gates_p21 as P21
    root = scratch / "l14"
    root.mkdir()
    g = P21.Git(root)
    open_repo, closed_repo = root / "open", root / "closed"
    P21.build(g, open_repo, P21.Spec(), fake_carrier=True)
    P21.build(g, closed_repo, P21.Spec(record_over={"a3_arc_session": 9}), fake_carrier=True)
    for rp in (open_repo, closed_repo):
        (rp / gate_launch.CARRIER_TEST_REL).write_text(FAKE_CARRIER.replace("VARIANT", "1"), encoding="utf-8")
    wd = root / "wd1"
    out = LG.carrier_selftest_via_launcher(open_repo, wd)
    frozen = {k: v for k, v in (out["record"] or {}).items() if k != "run"}
    cmp = LA.l14_compare({k: out[k] for k in ("returncode", "stdout", "record")}, frozen, LA.PDFPLUMBER)
    check("D1 G1 open (scratch): the launcher started the FAKE carrier; its output passes launch.l14_compare",
          out["carrier_started"] and (wd / "fake_carrier_sentinel.txt").is_file() and all(cmp.values())
          and not any(ln.startswith("gate_launch: ") for ln in out["stdout"].splitlines()),
          ", ".join(k for k, v in cmp.items() if not v))
    (open_repo / gate_launch.CARRIER_TEST_REL).write_text(FAKE_CARRIER.replace("VARIANT", "2"), encoding="utf-8")
    out2 = LG.carrier_selftest_via_launcher(open_repo, root / "wd2")
    cmp2 = LA.l14_compare({k: out2[k] for k in ("returncode", "stdout", "record")}, frozen, LA.PDFPLUMBER)
    check("D2 planted: a self-test record differing from the frozen one fails L14's record check",
          out2["carrier_started"] and cmp2["workdir record == frozen record, run stamp aside (types included)"] is False)
    out3 = LG.carrier_selftest_via_launcher(closed_repo, root / "wd3")
    cmp3 = LA.l14_compare({k: out3[k] for k in ("returncode", "stdout", "record")}, frozen, LA.PDFPLUMBER)
    check("D3 planted: G1 closed -> the launcher refuses (exit 3), the carrier never starts, L14 fails",
          out3["gate_refused"] and not out3["carrier_started"] and out3["returncode"] == 3
          and out3["record"] is None and not (root / "wd3" / "fake_carrier_sentinel.txt").exists()
          and not all(cmp3.values()))
    wd4 = root / "wd4"
    wd4.mkdir()
    (wd4 / "carrier_tests_selftest.json").write_text("{}", encoding="utf-8")
    try:
        LG.carrier_selftest_via_launcher(open_repo, wd4)
        check("D4 planted: a non-empty workdir (a stale record) is refused before anything starts", False)
    except LG.GlueRefused:
        check("D4 planted: a non-empty workdir (a stale record) is refused before anything starts",
              not (wd4 / "fake_carrier_sentinel.txt").exists())
    real = REPO / "arcs" / "audit" / "src_register" / "carrier_test.py"
    check("D5 the real carrier_test.py was never started (every run resolved to a scratch repository)",
          all(str(p).startswith(str(root)) for p in (open_repo, closed_repo)) and real.is_file())


# ================================================================================================================
# Part E: CLI refusals before any launch
# ================================================================================================================
def part_e(scratch: Path) -> None:
    print(SEP + "\nPart E: CLI refusals before any launch")
    base = ["--commit", HEAD, "--pass", "verdict", "--gate", "none"]
    cases = [("--dev without --plant", base + ["--dev", "--out", str(scratch / "e1")]),
             ("--out under arcs/audit/results", base + ["--plant", "P2", "--dev", "--rows", "10", "--out",
                                                         str(REPO / "arcs" / "audit" / "results" / "x")]),
             ("plant K on a real run", base + ["--K", "plant"]),
             ("plant-mode G6l on a real run", base + ["--g6l", "plant"]),
             ("an unmapped lettered plant id (P3c; seeds.LETTERED_PLANTS maps P3a / P3b only)",
              base + ["--plant", "P3c", "--dev", "--out", str(scratch / "e5"), "--rows", "10", "--case", "0"]),
             ("a row-keyed plant other than P2 (P14, outside the WP2 battery) without --case (B3)",
              base + ["--plant", "P14", "--dev", "--out", str(scratch / "e7"), "--rows", "10"]),
             ("a WP2 battery plant (P11) with a run.py-only option (--rows): refused before the hand-off",
              ["--commit", HEAD, "--plant", "P11", "--dev", "--out", str(scratch / "e9"), "--rows", "10"]),
             ("--case with P2 (P2 keeps the claim keys)",
              base + ["--plant", "P2", "--dev", "--out", str(scratch / "e8"), "--rows", "10", "--case", "0"]),
             ("--out inside the repository (C9)",
              base + ["--plant", "P2", "--dev", "--rows", "10", "--out", str(REPO / "explore" / "a1_out_x")])]
    for name, args in cases:
        t = time.time()
        code, lines, err = cli(args, timeout=300)
        check(f"E {name}: refused (exit 2) before any launch", code == 2 and any("refused" in ln for ln in lines)
              and time.time() - t < 30 and not (REPO / "arcs" / "audit" / "results" / "x").exists()
              and not (REPO / "explore" / "a1_out_x").exists())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", default=None)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    scratch = Path(a.scratch or tempfile.mkdtemp(prefix="a1_run_p2_")).resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    global HEAD
    HEAD = head()
    print("test_run_p2: HEAD %s, scratch %s" % (HEAD[:12], R.ascii_line(str(scratch))))
    for part in (part_e, part_c, part_f, part_d, part_b, part_a, part_a_exact, part_a_components, part_a_selected):
        try:
            part(scratch)
        except Exception as e:  # noqa: BLE001
            check(f"{part.__name__} raised", False, f"{type(e).__name__}: {e}")
            print(R.ascii_line(traceback.format_exc()))
    n_ok = sum(ok for _, ok in RESULTS)
    print(SEP + "\ntest_run_p2: %d / %d checks passed" % (n_ok, len(RESULTS)))
    if n_ok == len(RESULTS) and not a.keep:
        shutil.rmtree(scratch, ignore_errors=True)
    return 0 if n_ok == len(RESULTS) else 1


HEAD = ""

if __name__ == "__main__":
    sys.exit(main())
