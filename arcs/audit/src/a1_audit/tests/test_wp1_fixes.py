"""Checks of the fixes of the asdg-skeptic review of WP1 (61e3887) that live in run.py / seeds.py (the verdict-level
fixes are in tests/test_verdict.py, tests/test_amend1.py and tests/test_gates_p21.py).

Run from arcs/audit/src:
    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_wp1_fixes [--scratch DIR] [--keep]
Exits non-zero if any check fails. Prints ASCII only. Synthetic data only (run.SyntheticSources; every engine data path
points at a non-existent directory); no real map, set, carrier or gated file is opened.

Part B3  PLANT CHOICE (orchestrator, 2026-10-01): leg streams within a plant case (row-keyed plant id P14: the WP2
         battery ids, plants.driver.ORDER, are handed off to the driver).
         (a) keys: every plant leg / G3 / data key of P0-P30 (P3a / P3b by their case ranges) x 10 cases x the six
             class ids never generates the state of any claim key (all 692 TSV rows x 18 legs x map 0 / 1 x cells, and
             R24's G3 keys); plant leg, G3 and data keys are pairwise distinct; the class-id table and the lettered ids.
         (b) the runner: `--plant P14 --case 0-1 --dev` on rows 478 (set-vs-map, V-DK) and 10 (decoded-list, V-AAL,
             a descriptor cell), verdict then descriptor pass: each case under its own case_<n> folder; every recorded
             key = [20260925, 900, 14, case, class_id, leg] (G3: R24's child of the case's leg-3 key; J1 / naive joint in
             R7's order), the integer seeds used = recorded; no recorded key's state equals a claim key's; the two cases
             differ (data, keys, p's); a rerun in a second process (another --out, other --jobs) is bit-identical;
             the runner equals verdict.claim_verdict_a1 with verdict.plant_seed_callables in-process.
Part B1  a strong synthetic plant (a = .97) on a "not testable as stated" pooled-list row (TSV row 1, decoded-list,
         V-AAL) through run.execute in-process: the computed verdict survives (in-process recomputation), the row's
         record does not (survives False, primary status = the row's TSV status, "descriptive (not a verdict)").
Part C3  main_repository on a scratch repository and a linked worktree of it (git's common dir): a Run made inside the
         worktree writes under the MAIN tree and the worktree's git status stays empty.
Part C4  P12's plant K: 10,000 component permutations (RUN_PLAN.md:1139), recorded as an override in the header; an
         explicit --K permutation=500 still wins; other plants keep 500.
Part C5  a descriptor / sensitivity pass refuses a verdict file of another run identity (K, G6l mode, code hash), and
         reuses the verdict pass's G6l screens only when that pass's checkpoint RUN.json matches.
Part C8  run.prepare counts a class parcel the map lacks as dropped (a source whose map omits two class parcels).
Part C9  --out inside the repository (any folder) is refused; outside it is accepted.
Part HO  ORCHESTRATOR DECISION (2026-10-02): `a1_audit.run --plant <a1_audit.plants.driver.ORDER id>` hands off to the
         plants driver (in-process with the driver's main replaced by a spy: argv and exit code; the CLI with the
         driver's --estimate: reached, nothing run); P2 / P14 stay on run.py; a run.py-only option is refused.
"""
from __future__ import annotations

import os

for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_k] = "1"

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
from a1_audit import loader as LD  # noqa: E402
from a1_audit import plant_mode as PM  # noqa: E402
from a1_audit import run as R  # noqa: E402
from a1_audit import seeds as SD  # noqa: E402
from a1_audit import verdict as V  # noqa: E402

RESULTS: list[tuple[str, bool]] = []
SEP = "-" * 100
HEAD = ""


def check(name: str, cond, detail: str = "") -> bool:
    ok = bool(cond)
    RESULTS.append((name, ok))
    print(R.ascii_line("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  [" + detail + "]") if detail else "")),
          flush=True)
    return ok


def canon(o) -> str:
    return json.dumps(A3.jsonable(o), sort_keys=True)


def git(*args, repo: Path = REPO) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, env=env)


def cli(args: list[str], timeout: int = 3600) -> tuple[int, list[str], str]:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, "-X", "utf8", "-u", "-m", "a1_audit.run", *args], cwd=str(SRC),
                       capture_output=True, env=env, timeout=timeout)
    return r.returncode, r.stdout.decode("utf-8", "replace").splitlines(), r.stderr.decode("utf-8", "replace")


def state_hex(ss) -> str:
    return "".join("%08x" % int(x) for x in ss.generate_state(4))


def stat_view(doc: dict) -> dict:
    return dict(outcome=doc["outcome"], status_written=doc["status_written"], route=doc["route"],
                status_effective=doc["status_effective"], result=doc["result"],
                seeds=doc["row_provenance"]["seeds"], input_hashes=doc["row_provenance"]["input_hashes"],
                K=doc["K"], g6l_mode=doc["g6l_mode"])


def claim_states(rows) -> tuple[set, int]:
    out, n = set(), 0
    for r in rows:
        cells = {0}
        ci = LD.int_or_none(r["cell_index"])
        if ci is not None:
            cells.add(ci)
        for mi in (0, 1):
            for cc in cells:
                for leg in SD.LEGS.values():
                    out.add(state_hex(SD.claim_seed(r.target_no, r.row, leg, mi, cc)))
                out.add(state_hex(SD.g3_seed(r.target_no, r.row, mi, cc)))
                n += len(SD.LEGS) + 1
    return out, n


def tail(err: str) -> str:
    return err.strip().splitlines()[-1][:200] if err.strip() else ""


# ================================================================================================================
# B3 (a): keys
# ================================================================================================================
def part_b3_keys(rows) -> set:
    print(SEP + "\nPart B3 (a): plant keys vs claim keys (692 rows)")
    claims, n_claims = claim_states(rows)
    check("B3a claim keys enumerated (all 692 rows x 18 legs + G3 x map 0/1 x cells), pairwise distinct",
          len(rows) == 692 and len(claims) == n_claims, f"{n_claims} claim keys, {len(claims)} distinct states")
    plant, n = set(), 0
    plants = [f"P{i}" for i in range(31) if i != 3] + ["P3a", "P3b"]
    for name in plants:
        pid = SD.plant_int(name)
        lo, _ = SD.plant_case_range(name)
        for case in range(lo, lo + 10):
            for cid in SD.PLANT_CLASS_IDS.values():
                for leg in SD.LEGS.values():
                    plant.add(state_hex(SD.plant_leg_seed(pid, case, cid, leg)))
                    n += 1
                plant.add(state_hex(SD.plant_g3_seed(pid, case, cid)))
                n += 1
                for word in (0, 100_001, 200_010, 10_000_478, 20_000_615, 30_000_000):
                    plant.add(state_hex(SD.plant_data_seed(pid, case, cid, word)))
                    n += 1
    check("B3a no plant leg / G3 / data key generates a claim key's state", not (plant & claims),
          f"{n} plant keys ({len(plant)} distinct states) vs {len(claims)} claim states")
    check("B3a plant leg, G3 and data keys pairwise distinct (no state collision)", len(plant) == n)
    check("B3a class ids fixed: dk-ctx 2, V-AAL 11, V-DK 12, V-DK-subcortex 13, MIST64 14, V-CC200 17; run.SYN_CLASSES "
          "uses them", SD.PLANT_CLASS_IDS == {"dk-ctx": 2, "V-AAL": 11, "V-DK": 12, "V-DK-subcortex": 13, "MIST64": 14,
                                              "V-CC200": 17}
          and all(R.SYN_CLASSES[k]["class_id"] == SD.plant_class_id(k) for k in R.SYN_CLASSES))
    refused = []
    for f in (lambda: SD.plant_int("P3c"), lambda: SD.plant_int("Q1"), lambda: SD.plant_int("P3"),
              lambda: SD.check_plant_case("P3a", 1000),
              lambda: SD.check_plant_case("P3b", 999), lambda: SD.plant_class_id("V-HO")):
        try:
            f()
            refused.append(False)
        except ValueError:
            refused.append(True)
    check("B3a lettered ids: P3a / P3b -> 3 (cases [0, 1000) / [1000, inf)); P3c, Q1, plain P3 (its word is P3a / P3b's), "
          "out-of-range cases and an unlisted class refused", SD.plant_int("P3a") == SD.plant_int("P3b") == 3 and SD.plant_int("P12") == 12
          and all(refused), str(refused))
    g = SD.plant_g3_seed(8, 0, 12)
    check("B3a plant G3 = the first spawned child of the case's leg-3 key, not leg 3's stream",
          SD.same_seed_sequence(g, SD.plant_leg_seed(8, 0, 12, 3).spawn(1)[0])
          and state_hex(g) != state_hex(SD.plant_leg_seed(8, 0, 12, 3)))
    return claims


# ================================================================================================================
# B3 (b): the runner's plant cases
# ================================================================================================================
B3_ROWS = (478, 10)


def load(out: Path, case: int | None, pass_: str, row: int) -> dict:
    base = out if case is None else out / f"case_{case:06d}"
    return json.loads((base / "ungated" / pass_ / f"row_{row:04d}.json").read_bytes().decode("utf-8"))


B3_PLANT, B3_PID = "P14", 14   # a row-keyed plant id outside the WP2 battery (plants.driver.ORDER: handed off)


def plant_run(out: Path, pass_: str, jobs: int, cases: str = "0-1", rows: str = "478,10", extra=()):
    return cli(["--commit", HEAD, "--pass", pass_, "--gate", "none", "--rows", rows, "--plant", B3_PLANT, "--case", cases,
                "--dev", "--out", str(out), "--jobs", str(jobs), *extra])


def part_b3_runner(scratch: Path, rows, claims: set) -> Path:
    print(SEP + "\nPart B3 (b): plant cases through the runner (--plant P14 --case 0-1; rows 478, 10)")
    outX, outY = scratch / "b3x", scratch / "b3y"
    for out, jobs in ((outX, 1), (outY, 2)):
        for pass_ in ("verdict", "descriptor"):
            code, lines, err = plant_run(out, pass_, jobs)
            check(f"B3b run {out.name} {pass_} (jobs {jobs}) exits 0", code == 0, tail(err) if code else "")
    docs = {(o.name, c, p_, r): load(o, c, p_, r) for o in (outX, outY) for c in (0, 1)
            for p_ in ("verdict", "descriptor") for r in B3_ROWS}
    plans = {r: R.classify(rows[r - 1], plant_view=True) for r in B3_ROWS}
    bad_keys, bad_seed, used = [], [], set()
    for (o, c, p_, r), doc in docs.items():
        cid = SD.plant_class_id(plans[r]["analysis_class"])
        for rec in doc["row_provenance"]["seeds"]["per_map"]:
            if rec.get("keys") != "plant" or rec.get("case") != c or rec.get("plant_id") != B3_PID:
                bad_keys.append((o, c, p_, r, "head"))
            for leg in rec["legs"]:
                if leg["key"]["entropy"] != [20260925, 900, B3_PID, c, cid, leg["leg_no"]] or leg["key"]["spawn_key"]:
                    bad_keys.append((o, c, p_, r, leg["leg"]))
                ss = np.random.SeedSequence(leg["key"]["entropy"])
                used.add(state_hex(ss))
                if leg["use"] == "int" and leg.get("seed_int") != SD.seed_int(ss):
                    bad_seed.append((o, c, p_, r, leg["leg"]))
            if p_ == "descriptor":
                g3 = rec["G3"]["key"]
                if g3["entropy"] != [20260925, 900, B3_PID, c, cid, 3] or g3["spawn_key"] != [0]:
                    bad_keys.append((o, c, p_, r, "G3"))
                j1 = SD.plant_j1_draws(B3_PID, c, cid)
                nj = SD.plant_naive_joint_draws(B3_PID, c, cid)
                if (rec["J1"]["S1c_seed"], rec["J1"]["S2c_seed"], rec["naive_joint"]["S1_seed"]) != (
                        j1["S1c_seed"], j1["S2c_seed"], nj["S1_seed"]):
                    bad_seed.append((o, c, p_, r, "J1 / naive joint"))
                used.add(state_hex(SD.plant_g3_seed(B3_PID, c, cid)))
    check("B3b every recorded key = [20260925, 900, 14, case, class_id, leg]; G3 = R24's child of the case's leg-3 key",
          not bad_keys, str(bad_keys[:4]))
    check("B3b integer seeds recorded = the plant keys' (R7); J1 / naive joint seeds in R7's order", not bad_seed,
          str(bad_seed[:4]))
    check("B3b no stream the runner drew equals any claim key's stream (692 rows)", used and not (used & claims),
          f"{len(used)} plant streams")
    same = all(canon(stat_view(docs[("b3x", c, p_, r)])) == canon(stat_view(docs[("b3y", c, p_, r)]))
               for c in (0, 1) for p_ in ("verdict", "descriptor") for r in B3_ROWS)
    check("B3b reruns identical: a second process (other --out, jobs 2) gives bit-identical records per case", same)
    for r in B3_ROWS:
        a, b = docs[("b3x", 0, "verdict", r)], docs[("b3x", 1, "verdict", r)]
        check(f"B3b row {r}: cases 0 and 1 differ (data hashes, keys, the verdict record)",
              a["row_provenance"]["input_hashes"] != b["row_provenance"]["input_hashes"]
              and canon(a["row_provenance"]["seeds"]) != canon(b["row_provenance"]["seeds"])
              and canon(a["result"]["verdict"]) != canon(b["result"]["verdict"]))
    # in-process: the library functions on the plant keys and the case's synthetic sources
    K = R.plant_K(B3_PLANT)
    for c in (0, 1):
        src = R.SyntheticSources(B3_PID, scratch / f"_no_data_b3_{c}", case=c)
        for r in B3_ROWS:
            p = dict(plans[r], seed_view=dict(kind="plant", plant=B3_PLANT, plant_id=B3_PID, case=c))
            pr = R.prepare(p, src, 0, "primary")
            sc = R.seeds_of(p, 0)
            streams = {"l5": R.stream_seed(p, 0, 5)}
            scr = PM.streams_screen(PM.MODE_PLANT, pr.ctx, pr.S, streams, K["species"])
            v = V.claim_verdict_a1(pr.adapter, R.verdict_K(K), sc["seed_of"], two_sided=p["two_sided"],
                                   registered_direction=p["registered_direction"], g6l=scr["l5"],
                                   by_construction_label=p["by_construction_label"])
            got = docs[("b3x", c, "verdict", r)]["result"]["verdict"]
            check(f"B3b case {c} row {r}: runner verdict == verdict.claim_verdict_a1 on plant_seed_callables "
                  "in-process" + (" (descriptor row: descriptor_row_record)" if p["descriptor"] else ""),
                  canon(R.verdict_for_plan(p, v)) == canon(got))
    hdr = docs[("b3x", 0, "verdict", 478)]
    check("B3b header records the plant case and its seed view; output under case_000000",
          hdr["plant"]["case"] == 0 and hdr["plant"]["seed_view"]["kind"] == "plant"
          and (outX / "case_000000" / "ungated" / "verdict" / "row_0478.json").is_file())
    return outX


# ================================================================================================================
# B1: a strong plant on a pooled-list row through the runner
# ================================================================================================================
def fake_launch() -> tuple[dict, list]:
    return ({"run_commit": HEAD, "assertions": [], "failed": ["L11", "L13"], "gate": None, "repo_root": str(REPO)},
            ["L11", "L13"])


def part_b1(scratch: Path, rows) -> None:
    print(SEP + "\nPart B1: a strong synthetic plant on TSV row 1 ('not testable as stated', pooled list) via execute")
    row = rows[0]
    p0 = R.classify(row, plant_view=True)
    check("B1 row 1 routes to the decoded-list verdict with descriptor = True ('not testable as stated')",
          p0["kind"] == "compute" and p0["descriptor"] is True and p0["status_effective"].startswith(
              "not testable as stated"), p0["route"])
    K = R.plant_K("P90")
    found = None
    for c in range(16):   # the computed verdict must survive (the precondition): search the plant's cases
        src = R.SyntheticSources(90, scratch / f"_no_data_b1_{c}", case=c, a=0.97)
        p = dict(p0, seed_view=dict(kind="plant", plant="P90", plant_id=90, case=c))
        pr = R.prepare(p, src, 0, "primary")
        sc = R.seeds_of(p, 0)
        scr = PM.streams_screen(PM.MODE_PLANT, pr.ctx, pr.S, {"l5": R.stream_seed(p, 0, 5)}, K["species"])
        v = V.claim_verdict_a1(pr.adapter, R.verdict_K(K), sc["seed_of"], two_sided=p["two_sided"],
                               registered_direction=p["registered_direction"], g6l=scr["l5"])
        if v["survives"]:
            found = (c, v)
            break
    check("B1 precondition: the strong plant's computed verdict survives in-process", found is not None,
          "" if found is None else f"case {found[0]}, p {found[1]['p_conjunction']}")
    if found is None:
        return
    c, v = found
    out = scratch / "b1"
    args = R.build_parser().parse_args(["--commit", HEAD, "--pass", "verdict", "--gate", "none", "--rows", "1",
                                        "--plant", "P90", "--case", str(c), "--dev", "--out", str(out), "--jobs", "1"])
    R.validate(args)
    rec, refused = fake_launch()
    run = R.Run(args, rec, refused, case=c)
    run.sources = R.SyntheticSources(90, out / "_no_such_data_dir_b1", case=c, a=0.97)
    R.execute(run, [row])
    doc = load(out, c, "verdict", 1)
    got = doc["result"]["verdict"]
    check("B1 the runner's record: survives False; primary status = the row's TSV status; computed record under "
          "'descriptor' passing at alpha, labelled 'descriptive (not a verdict)'; no 'survives' inside",
          doc["outcome"] == "computed" and got["survives"] is False and got["primary_status"] == p0["status_effective"]
          and (got.get("descriptor") or {}).get("passes_at_alpha") is True
          and got["descriptor"]["passes_at_alpha_label"] == V.DESCRIPTIVE and "survives" not in json.dumps(
              got["descriptor"]) and got["reading"].startswith(V.DESCRIPTIVE),
          f"survives {got.get('survives')}, computed p {(got.get('descriptor') or got).get('p_conjunction')}")
    p = dict(p0, seed_view=dict(kind="plant", plant="P90", plant_id=90, case=c))
    check("B1 the runner's record = verdict.descriptor_row_record of the in-process verdict (bit-identical)",
          canon(R.verdict_for_plan(p, v)) == canon(got))


# ================================================================================================================
# C3: the main repository from a worktree
# ================================================================================================================
def part_c3(scratch: Path) -> None:
    print(SEP + "\nPart C3: outputs of a worktree run go to the MAIN repository (git's common dir)")
    main = scratch / "c3_main"
    wt = scratch / "c3_wt"
    main.mkdir()
    cfg = scratch / "c3_gitconfig"
    cfg.write_text("", encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=str(cfg), GIT_CONFIG_NOSYSTEM="1", GIT_AUTHOR_NAME="synthetic",
               GIT_AUTHOR_EMAIL="synthetic@invalid", GIT_COMMITTER_NAME="synthetic",
               GIT_COMMITTER_EMAIL="synthetic@invalid")

    def g(*a, cwd=main):
        r = subprocess.run(["git", *a], cwd=str(cwd), capture_output=True, env=env)
        if r.returncode:
            raise RuntimeError(f"git {a[0]}: {r.stderr.decode('utf-8', 'replace')[:200]}")
        return r.stdout.decode("utf-8", "replace")
    g("init", "-q")
    tsv = main / LD.TSV_PATH
    tsv.parent.mkdir(parents=True)
    tsv.write_text("synthetic\n", encoding="utf-8", newline="\n")
    (main / ".gitignore").write_text("artifacts/\narcs/audit/run_manifests/\n", encoding="utf-8", newline="\n")
    g("add", "-A")
    g("commit", "-q", "-m", "synthetic")
    g("worktree", "add", "--detach", "-q", str(wt))
    R.main_repository.cache_clear()
    mw, mm = R.main_repository(wt), R.main_repository(main)
    check("C3 main_repository(worktree) = main_repository(main) = the main tree; the real repository maps to itself",
          mw == mm == main.resolve() and R.main_repository(REPO) == Path(subprocess.run(
              ["git", "-C", str(REPO), "rev-parse", "--path-format=absolute", "--git-common-dir"], capture_output=True,
              text=True).stdout.strip()).parent.resolve(), f"{mw.name} / {mm.name}")
    keep = R.REPO
    try:
        R.REPO = wt
        args = R.build_parser().parse_args(["--commit", HEAD, "--pass", "verdict", "--gate", "none", "--rows", "478",
                                            "--plant", "P2", "--jobs", "1"])
        rec, _ = fake_launch()
        run = R.Run(args, rec, [], case=None)
        run.log("C3 synthetic log line")
    finally:
        R.REPO = keep
    st = g("status", "--porcelain", "--untracked-files=all", cwd=wt)
    check("C3 a Run made in the worktree writes under the MAIN tree (run_manifests/plants/P2/...); the worktree's git "
          "status stays empty", R._under(run.results_dir, main) and not R._under(run.results_dir, wt)
          and (run.results_dir / "run.log").is_file() and st.strip() == "" and run.out_root == main.resolve(),
          st.strip()[:120])
    g("worktree", "remove", "--force", str(wt))   # the test's own scratch worktree (no junction inside it)


# ================================================================================================================
# C4, C9
# ================================================================================================================
def part_c4_c9(scratch: Path) -> None:
    print(SEP + "\nPart C4 / C9: P12's permutation count; --out inside the repository")
    k12, k8 = R.parse_K(None, True, "P12"), R.parse_K(None, True, "P8")
    kx = R.parse_K("permutation=500", True, "P12")
    check("C4 P12's plant K: permutation 10,000 (RUN_PLAN.md:1139); other plants 500; --K permutation=500 overrides",
          k12["permutation"] == 10000 and k8["permutation"] == 500 and kx["permutation"] == 500
          and {k: v for k, v in k12.items() if k != "permutation"} == {k: v for k, v in R.PLANT_K.items()
                                                                       if k != "permutation"})
    args = R.build_parser().parse_args(["--commit", HEAD, "--pass", "verdict", "--gate", "none", "--rows", "615",
                                        "--plant", "P12", "--case", "0", "--dev", "--out", str(scratch / "c4"),
                                        "--jobs", "1"])
    rec, refused = fake_launch()
    run = R.Run(args, rec, refused, case=0)
    hd = run.header()
    check("C4 the header records the override and its source",
          hd["K"]["permutation"] == 10000 and hd["K_plant_overrides"]["permutation"]["value"] == 10000
          and "RUN_PLAN.md:1139" in hd["K_plant_overrides"]["permutation"]["source"], json.dumps(
              hd["K_plant_overrides"]))
    base = ["--commit", HEAD, "--pass", "verdict", "--gate", "none", "--plant", "P2", "--dev", "--rows", "10"]
    res = {}
    for name, out in (("explore", REPO / "explore" / "x"), ("arcs/audit/src", SRC / "x"), ("root", REPO / "x"),
                      ("outside", scratch / "c9_ok")):
        try:
            R.validate(R.build_parser().parse_args(base + ["--out", str(out)]))
            res[name] = "accepted"
        except R.RunRefused as e:
            res[name] = "refused" if "outside the repository" in str(e.code) else f"other: {e.code}"
    check("C9 --out inside the repository refused (explore/, arcs/audit/src/, the root); outside accepted",
          res == {"explore": "refused", "arcs/audit/src": "refused", "root": "refused", "outside": "accepted"},
          json.dumps(res))


# ================================================================================================================
# C5: verdict-file identity
# ================================================================================================================
def _fields(status: str | None) -> set:
    """The RUN_IDENTITY_FIELDS a REFUSED_VERDICT_IDENTITY status names."""
    head, sep, rest = (status or "").partition("(differs in: ")
    return set(x.strip() for x in rest.split(";")[0].split(",")) if sep else set()


def part_c5(scratch: Path, outX: Path | None = None) -> None:
    """C5 on a verdict pass made here, just before (case 0, rows 478 and 10), so a code change elsewhere in the run
    (the code hash is part of the identity) cannot leak in; each refusal must NAME the field changed (code_hash may
    be named beside it if the repository's code changed meanwhile, which is itself the C5 behaviour)."""
    print(SEP + "\nPart C5: the descriptor / sensitivity passes check the verdict file's run identity")
    base = scratch / "c5_base"
    code, lines, err = plant_run(base, "verdict", 2, cases="0", rows="478,10")
    check("C5 fresh verdict pass (case 0, rows 478, 10) exits 0", code == 0, tail(err) if code else "")
    out = scratch / "c5"
    shutil.copytree(base, out)
    code, lines, err = plant_run(out, "descriptor", 1, cases="0", rows="478", extra=("--K", "sets=150"))
    doc = load(out, 0, "descriptor", 478)
    check("C5 descriptor pass with another K: the row is refused, naming K; nothing computed",
          code == 0 and doc["outcome"] == "refused" and "K" in _fields(doc["status_written"])
          and _fields(doc["status_written"]) <= {"K", "code_hash"} and doc["result"] is None, doc["status_written"])
    code, lines, err = plant_run(out, "sensitivity", 1, cases="0", rows="478", extra=("--g6l", "exact"))
    doc = load(out, 0, "sensitivity", 478)
    check("C5 sensitivity pass with another G6l mode: refused, naming g6l_mode",
          code == 0 and doc["outcome"] == "refused" and "g6l_mode" in _fields(doc["status_written"])
          and _fields(doc["status_written"]) <= {"g6l_mode", "code_hash"}, doc["status_written"])
    vf = out / "case_000000" / "ungated" / "verdict" / "row_0478.json"
    vd = json.loads(vf.read_bytes().decode("utf-8"))
    vd["run_identity"]["code_hash"] = "0" * 64
    R.write_json_atomic(vf, vd)
    code, lines, err = plant_run(out, "descriptor", 1, cases="0", rows="478")
    doc = load(out, 0, "descriptor", 478)
    check("C5 a verdict file of another code hash: refused (exactly code_hash)",
          code == 0 and doc["outcome"] == "refused" and _fields(doc["status_written"]) == {"code_hash"},
          doc["status_written"])
    # U12: the verdict pass's screens are reused only if its checkpoint RUN.json matches (row 10: leg 25)
    ref_out = scratch / "c5_ref"
    shutil.copytree(base, ref_out)
    code_r, _, err_r = plant_run(ref_out, "descriptor", 1, cases="0", rows="10")   # reuse allowed (control)
    out2 = scratch / "c5b"
    shutil.copytree(base, out2)
    rj = out2 / "_ck" / "case_000000" / "ungated" / "verdict" / "RUN.json"
    hd = json.loads(rj.read_text(encoding="utf-8"))
    hd["code_hash"] = "1" * 64
    rj.write_text(json.dumps(hd, indent=1) + "\n", encoding="utf-8", newline="\n")
    code, lines, err = plant_run(out2, "descriptor", 1, cases="0", rows="10")
    doc, ref = load(out2, 0, "descriptor", 10), load(ref_out, 0, "descriptor", 10)
    got = ((doc.get("result") or {}).get("per_map") or {}).get("0") or {}
    want = ((ref.get("result") or {}).get("per_map") or {}).get("0") or {}
    check("C5 U12 control: with the verdict pass's own RUN.json, leg 25's screen is reused",
          code_r == 0 and want.get("T_abs_g6l_screen") == "verdict pass shared screen", tail(err_r) if code_r else "")
    check("C5 U12: a verdict checkpoint RUN.json of another run -> leg 25's screen recomputed, not reused (the row "
          "itself computes: its verdict file matches)",
          code == 0 and doc["outcome"] == "computed" and str(got.get("T_abs_g6l_screen", "")).startswith(
              "this pass's screen") and any("screens recomputed" in ln for ln in lines),
          f"{doc['outcome']}: {got.get('T_abs_g6l_screen', doc.get('status_written'))}")
    check("C5 U12: the recomputed screen gives the same descriptor record as the reused one (stream by stream)",
          bool(got) and canon({k: v for k, v in got.items() if k != "T_abs_g6l_screen"})
          == canon({k: v for k, v in want.items() if k != "T_abs_g6l_screen"}))


# ================================================================================================================
# C8: run.prepare counts class parcels the map lacks
# ================================================================================================================
class HoleSources(R.SyntheticSources):
    """SyntheticSources whose map omits the class's 3rd and 4th parcels (a map that does not cover its class)."""

    def map(self, plan, map_index):
        y, ids, cls, h = super().map(plan, map_index)
        keep = np.ones(ids.size, bool)
        keep[[2, 3]] = False
        return y[keep], ids[keep], cls, {k: R.arr_sha(y[keep], ids[keep]) for k in h}


def part_c8(scratch: Path, rows) -> None:
    print(SEP + "\nPart C8: run.prepare counts a class parcel absent from the map as dropped")
    src = HoleSources(2, scratch / "_no_data_c8")
    p = R.classify(rows[477], plant_view=True)
    pr = R.prepare(p, src, 0, "primary")
    ap = pr.parcels
    ctx, _, _ = src.context(p["analysis_class"])
    check("C8 two class parcels absent from the map: counted as dropped (n_absent_from_map 2), kept + dropped = the "
          "class's parcels", ap["n_absent_from_map"] == 2 and ap["n_class"] == ctx.n
          and ap["n_kept"] + ap["n_dropped"] == ctx.n and len(ap["dropped_absent_from_map"]) == 2
          and not set(ap["dropped_absent_from_map"]) & set(int(i) for i in pr.parcel_ids), json.dumps(
              {k: ap[k] for k in ("n_class", "n_kept", "n_dropped", "n_absent_from_map")}))


# ================================================================================================================
# hand-off of the WP2 battery plants to a1_audit.plants.driver (ORCHESTRATOR DECISION 2026-10-02)
# ================================================================================================================
def part_handoff(scratch: Path) -> None:
    print(SEP + "\nPart HO: `a1_audit.run --plant <WP2 battery plant>` hands off to a1_audit.plants.driver")
    import importlib
    drv = importlib.import_module(R.HANDOFF_DRIVER)
    out = scratch / "ho"
    calls = []
    keep = drv.main
    try:
        drv.main = lambda argv=None: (calls.append(list(argv)), 0)[1]
        code = R.main(["--plant", "P11", "--dev", "--out", str(out), "--commit", HEAD])
        code_p3a = R.main(["--plant", "P3a", "--commit", HEAD, "--jobs", "4"])
        code_bad = R.main(["--plant", "P11", "--dev", "--out", str(out), "--commit", HEAD, "--rows", "10"])
    finally:
        drv.main = keep
    check("HO in-process: `--plant P11 --dev --out <scratch> --commit <HEAD>` reaches the driver's main with "
          "[P11, --commit, HEAD, --jobs, 20, --dev, --out, <scratch>] and returns its exit code; the lettered P3a is "
          "accepted for the hand-off; a run.py-only option (--rows) is refused before the driver (exit 2)",
          code == 0 and code_p3a == 0 and code_bad == 2 and calls == [
              ["P11", "--commit", HEAD, "--jobs", "20", "--dev", "--out", str(out)],
              ["P3a", "--commit", HEAD, "--jobs", "4"]] and not out.exists(), json.dumps(calls)[:200])
    check("HO row-keyed plants stay on run.py's path: P2 and P14 not handed off; P3a refused there (parse_plant)",
          R.handoff_argv(["--plant", "P2", "--commit", "x"]) is None
          and R.handoff_argv(["--plant", "P14", "--commit", "x"]) is None and set(drv.ORDER) >= {"P3a", "P11", "P12"}
          and _raises(NotImplementedError, R.parse_plant, "P3a"))
    code, lines, err = cli(["--plant", "P11", "--dev", "--out", str(out), "--commit", HEAD, "--estimate"], timeout=600)
    body = "\n".join(ln for ln in lines if not ln.startswith("a1_audit.run:"))
    try:
        est = json.loads(body)
    except ValueError:
        est = None
    check("HO CLI `python -m a1_audit.run --plant P11 --dev --out <scratch> --commit <HEAD> --estimate` reaches the "
          "driver (its no-launch cost estimate printed; nothing written)",
          code == 0 and any("handed off to a1_audit.plants.driver" in ln for ln in lines) and isinstance(est, dict)
          and not out.exists(), tail(err) if code else (lines[0] if lines else ""))


def _raises(exc, f, *a) -> bool:
    try:
        f(*a)
    except exc:
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", default=None)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    scratch = Path(a.scratch or tempfile.mkdtemp(prefix="a1_wp1_fixes_")).resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    if R._under(scratch, REPO):
        print("the scratch directory must lie outside the repository")
        return 2
    global HEAD
    HEAD = git("rev-parse", "HEAD").stdout.decode("ascii").strip()
    print("test_wp1_fixes: HEAD %s" % HEAD[:12])
    rows = R.register_for_diagnostics(REPO)
    t0 = time.time()
    claims, outX = set(), None
    try:
        claims = part_b3_keys(rows)
    except Exception as e:  # noqa: BLE001
        check("part_b3_keys raised", False, f"{type(e).__name__}: {e}")
        print(R.ascii_line(traceback.format_exc()))
    for part in (lambda: part_b3_runner(scratch, rows, claims), lambda: part_b1(scratch, rows),
                 lambda: part_c3(scratch), lambda: part_c4_c9(scratch), lambda: part_c8(scratch, rows),
                 lambda: part_handoff(scratch)):
        try:
            got = part()
            if isinstance(got, Path):
                outX = got
        except Exception as e:  # noqa: BLE001
            check("a part raised", False, f"{type(e).__name__}: {e}")
            print(R.ascii_line(traceback.format_exc()))
    if True:
        try:
            part_c5(scratch)
        except Exception as e:  # noqa: BLE001
            check("part_c5 raised", False, f"{type(e).__name__}: {e}")
            print(R.ascii_line(traceback.format_exc()))
    n_ok = sum(ok for _, ok in RESULTS)
    print(SEP + "\ntest_wp1_fixes: %d / %d checks passed (%.0f s)" % (n_ok, len(RESULTS), time.time() - t0))
    if n_ok == len(RESULTS) and not a.keep:
        shutil.rmtree(scratch, ignore_errors=True)
    return 0 if n_ok == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
