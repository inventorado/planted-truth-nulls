"""WP4 phase 2, gate G2: the ONE launcher (RUN_PLAN.md §11, §14, §16; RUN_PLAN_amend_4.md v3, FROZEN d3f72753...).

    D:\\RESEARCH\\asd-imaging-genetics\\env\\venv\\Scripts\\python.exe -X utf8 -u -m a1_audit.wp4_launch --commit <sha>
        [--jobs 20] [--stop-after-material] [--rerun-material] [--resume-after-pause "<who / why>"] [--dry]
        [--row-rerun TAG --rows ROWS]   (2026-11-02: the material stage, then the three passes on ROWS only into
        results/a1_run/rerun_TAG/G2/, then the report; summary ROW_RERUN_SUMMARY; no other row is recomputed)
    (run from D:\\RESEARCH\\asd-imaging-genetics\\arcs\\audit\\src of the MAIN tree)

Steps (each in a clean, pinned, detached worktree D:\\tmp\\asdg_wt_a1_wp4_<short> with the artifacts junction, cwd
<wt>\\arcs\\audit\\src; outputs under the MAIN repository, RUN_PLAN §2.3 :327-328):
  0 preconditions (refused, exit 2, before anything runs):
      - results/a1_run/s17_wp4_prerun_summary.json records the §17 suite, P1 and plant battery passed (exit 0) at
        PLANT_COMMIT (36a4fe6, tag s17_wp4); if it records a comparison step that did not exit 0, the §17
        classification run_manifests/s17_wp4_classify.json must read CLASSIFY_READING, list no substantive row,
        account for every flagged row and name the comparison file by its sha256 (LF bytes);
      - `git diff --name-only PLANT_COMMIT..<commit>`: every path under arcs/ or src/ (the code and records A1 can
        read) matches DIFF_ALLOWED (no plant, no ungated statistic path); paths elsewhere (explore/, literature/,
        .gitignore ...) are other work of the programme that no A1 step reads;
      - amendment 4 is frozen (wp4_layout.frozen_check at the commit: the LF / blob sha256 = the pin, FROZEN.txt's line);
      - the worktree's HEAD is the commit and its git status is empty;
      - Docker answers (`docker info`; Docker Desktop is started if it is down, up to 10 minutes; else exit 3);
  1 material: `python -m a1_audit.wp4_material run --commit <sha>` - launch(G2) and the G2 material stage in the frozen
    order (R16's lh.aparc.annot first, R15's HCP-MMP1 volume and label list, identity at download, the local copies'
    sha256 at use, the section-8 wrapper's extraction, R17's Docker run and the DEG sets, R38's env/venv_ref build, the
    gated sets by the frozen S-build, the decoders, the G2 manifest); exit 0 iff the manifest is final;
    --stop-after-material stops here (exit 0) so that the material-stage record can be read before any claim pass;
  2-4 the claim passes: `python -m a1_audit.run --commit <sha> --pass {verdict,descriptor,sensitivity} --gate G2
    --jobs N` in that order (the sensitivity pass = finite y and >= 2 donors, R11); pace's automatic pause at 2x the
    repriced estimate exits 4 (RUN_PLAN §14): rerun this launcher with --resume-after-pause "<who / why>";
  5 report: `python -m a1_audit.report_cells --gate G2 --results-root <main>/arcs/audit/results` (§16's G2 cells).
After every step the summary results/a1_run/wp4_g2_summary.json is written and read back: each step's command, exit
code and times; the G2 manifest's counts as section 8's rule prints them (statuses, door admissions), the sets'
restatement, the DEG checks, R17's deviation where amend_4 v3 Q3 applied; the R13 record's sha256 and repro pin; the
amendment-4 freeze check. A rerun skips the steps the summary records as passed at the same commit; --rerun-material
runs step 1 again (e.g. after a Q3 adaptation file is written; the earlier records stay, a new manifest version is
written). Another commit's summary is copied beside, never overwritten. twinpolis-* containers are stopped at the end
(Docker Desktop starts them). Nothing is removed or deleted.

Exit codes: 0 every step passed (or stopped after the material stage as asked); 2 refused (a precondition); 3 Docker
unavailable; 4 a claim pass paused (§14); 11 the material stage failed or its manifest is not final; 21 / 22 / 23 the
verdict / descriptor / sensitivity pass failed; 31 the report cells failed.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

MAIN = Path(__file__).resolve().parents[4]
PY = MAIN / "env" / "venv" / "Scripts" / "python.exe"
TAG = "s17_wp4"
PLANT_COMMIT = "36a4fe6"           # the orchestrator's §17 run (suite, P1, plants, --stop-after-plants)
PRERUN_SUMMARY = "arcs/audit/results/a1_run/s17_wp4_prerun_summary.json"
SUMMARY = "arcs/audit/results/a1_run/wp4_g2_summary.json"
# 2026-11-02: a row rerun (--row-rerun TAG --rows ROWS) keeps its own summary; the main summary is never touched
ROW_RERUN_SUMMARY = "arcs/audit/results/a1_run/wp4_g2_rerun_{tag}_summary.json"
DOCKER_DESKTOP = Path(r"C:\Program Files\Docker\Docker\Docker Desktop.exe")
# the files a commit after PLANT_COMMIT may touch: none is read by a plant or by an ungated row's computation
DIFF_ALLOWED = (
    re.compile(r"^arcs/audit/src/a1_audit/wp4_[a-z0-9_]+\.py$"),
    re.compile(r"^arcs/audit/src/a1_audit/s17_compare\.py$"),
    # RUN_PLAN_amend_5 v2 B4: the report writer joins the G2 labels and the post-exposure version (G2 cells only;
    # read by no plant and by no row computation)
    re.compile(r"^arcs/audit/src/a1_audit/report_cells\.py$"),
    re.compile(r"^arcs/audit/src/a1_audit/rbuild/r17\.py$"),
    re.compile(r"^arcs/audit/src/a1_audit/tests/[^/]+\.py$"),
    re.compile(r"^arcs/audit/RUN_PLAN_amend_4\.md$"),
    re.compile(r"^arcs/audit/RUN_PLAN_amend_5\.md$"),
    # an arc's ARC.md (an exposure / closeout record; 2026-10-21: A3's G2 exposure record, 7811eac): no A1 step
    # reads one (A1 ports A3's code, never imports arcs/replication)
    re.compile(r"^arcs/[a-z0-9_-]+/ARC\.md$"),
    re.compile(r"^arcs/audit/FROZEN\.txt$"),
    re.compile(r"^arcs/audit/run_manifests/s17_wp4_prerun\.(json|md)$"),
    re.compile(r"^arcs/audit/run_manifests/material/G2/[^/]+\.json$"),
    # an operator incident note (ETHICS_PRIVACY procedure; counts and field names only), read by no A1 step
    # (2026-10-20: incident_2026-10-17.md made 36a4fe6..HEAD refused)
    re.compile(r"^arcs/audit/run_manifests/material/G2/incident_\d{4}-\d{2}-\d{2}\.md$"),
    re.compile(r"^arcs/audit/run_manifests/s17_wp4_classify\.(json|py)$"),
    re.compile(r"^arcs/audit/results/a1_run/s17_wp4_(compare|prerun_summary)\.(json|md)$"),
    # 2026-11-02 (b5a75be committed the G2 run's outputs; every later commit was refused): the G2 run's OWN outputs,
    # which every A1 step reads from the MAIN tree only (wp4_layout.Roots.production: records / sets / objects from
    # main_repository; run.py's results under main_repository; X18), so a worktree's committed copy is read by no
    # step; and two documents no A1 step reads (prereg_amend_6, the paper outline)
    re.compile(r"^arcs/audit/results/a1_run/G2/.+$"),
    re.compile(r"^arcs/audit/results/a1_run/wp4_g2_summary(_[0-9a-f]{7})?\.json$"),
    re.compile(r"^arcs/audit/results/MANIFEST_claims\.md$"),
    re.compile(r"^arcs/audit/register_maps/post_freeze/G2/.+$"),
    re.compile(r"^arcs/audit/register_sets/post_freeze/G2(_a5)?/.+$"),
    re.compile(r"^arcs/audit/prereg_amend_6\.md$"),
    re.compile(r"^arcs/audit/paper1/[^/]+\.md$"),
)
A1_READ_PREFIXES = ("arcs/", "src/")        # outside these, a changed path is not read by any A1 step
CLASSIFY = "arcs/audit/run_manifests/s17_wp4_classify.json"
CLASSIFY_READING = "no statistic, p, verdict, seed or input hash changed"
EXIT = {"ok": 0, "refused": 2, "docker": 3, "paused": 4, "material": 11, "verdict": 21, "descriptor": 22,
        "sensitivity": 23, "report": 31, "sanity": 41}


def expected_rows(pass_: str, repo: Path) -> int:
    """The register's G2 rows the plan computes in this pass (run.classify with G2 open; report_cells.computing_passes
    by route; run.FORM_NO_PASS): the denominator of the pass's sanity gate."""
    sys.path.insert(0, str(Path(repo) / "arcs/audit/src"))
    from a1_audit import loader as LD
    from a1_audit import report_cells as RC
    from a1_audit import run as R
    _, rows = LD.parse_tsv_bytes(LD.lf((Path(repo) / LD.TSV_PATH).read_bytes()))
    n = 0
    for r in rows:
        if r.gate != "G2":
            continue
        p = R.classify(r, frozenset({"G2"}))
        if p["kind"] not in ("compute", "form") or (p.get("form_name"), pass_) in R.FORM_NO_PASS:
            continue
        if pass_ in set(RC.computing_passes(p["route"]).values()):
            n += 1
    return n


def expected_from_manifest(pass_: str, repo: Path, version: str | None = None, sources=None) -> dict:
    """2026-10-21 (run 7): the rows expected computed in this pass FROM THE FINAL MATERIAL MANIFEST: run.dry_dispatch
    of the G2 rows on the G2 sources (a row 'would compute' iff every source it needs is extracted / identity recorded
    / built and the register does not mark it no-statistic), restricted to the rows this pass computes (route,
    FORM_NO_PASS). Returns {"expected": n, "rows": {row: target_key}, "not_expected": {status: n}}."""
    sys.path.insert(0, str(Path(repo) / "arcs/audit/src"))
    from a1_audit import report_cells as RC
    from a1_audit import run as R
    from a1_audit import wp3_layout as W3
    from a1_audit import wp4_layout as L
    from a1_audit import wp4_sources as W4S
    rows = [r for r in R.register_for_diagnostics(Path(repo)) if r.gate == "G2"]
    src = sources or W4S.WP4Sources(L.Roots.production(repo=repo, out_repo=repo, version=version),
                                    W3.Roots.production())
    recs = {d["row"]: d for d in R.dry_dispatch(rows, frozenset({"G2"}), plant_view=False, sources=src)}
    exp, other = {}, {}
    for r in rows:
        p = R.classify(r, frozenset({"G2"}))
        if p["kind"] not in ("compute", "form") or (p.get("form_name"), pass_) in R.FORM_NO_PASS:
            continue
        if pass_ not in set(RC.computing_passes(p["route"]).values()):
            continue
        d = recs.get(r.row) or {}
        if d.get("outcome") == "would compute":
            exp[r.row] = r.target_key
        else:
            st = str(d.get("status"))
            other[st] = other.get(st, 0) + 1
    return {"expected": len(exp), "rows": exp, "not_expected": other}


def pass_sanity(pass_dir: Path, pass_: str, repo: Path, material_final: bool, version: str | None = None,
                sources=None) -> dict:
    """2026-10-21 (run 6): after a final material manifest no G2 row may read "material pending", and a pass whose
    plan expects computed rows must compute at least one. Returns {"ok", "expected", "computed", "pending",
    "n_rows", "why"} (counts only)."""
    sys.path.insert(0, str(Path(repo) / "arcs/audit/src"))
    from a1_audit import wp4_layout as L
    n = computed = pending = 0
    got: dict = {}
    for f in sorted(Path(pass_dir).glob("row_[0-9][0-9][0-9][0-9].json")):      # row_NNNN_repro.json: not a row
        d = json.loads(f.read_bytes().decode("utf-8"))
        n += 1
        if d.get("outcome") == "computed":
            computed += 1
            got[int(d.get("row") or f.name[4:8])] = d.get("cell_id")
        pending += int(d.get("status_written") == L.STATUS_PENDING)
    plan_exp = expected_rows(pass_, repo)
    if material_final:
        em = expected_from_manifest(pass_, repo, version, sources)
        exp, exp_rows = em["expected"], em["rows"]
    else:
        em, exp, exp_rows = None, plan_exp, {}
    by_target: dict = {}
    for row, tk in exp_rows.items():
        t = by_target.setdefault(tk, {"expected": 0, "computed": 0})
        t["expected"] += 1
        t["computed"] += int(row in got)
    missing = sorted(r for r in exp_rows if r not in got)
    why = None
    if material_final and pending:
        why = f"{pending} rows read '{L.STATUS_PENDING}' after a final material manifest"
    elif exp and not computed:
        why = f"0 computed rows where {exp} are expected"
    elif material_final and missing:
        why = f"{len(missing)} rows expected computed from the final manifest are not computed"
    return {"ok": why is None, "expected": exp, "expected_by_plan": plan_exp, "computed": computed, "pending": pending,
            "n_rows": n, "by_target": by_target, "missing_rows": missing[:50],
            "not_expected": (em or {}).get("not_expected"), "why": why}


def parse_row_list(text: str) -> list:
    """'478' / '1-3,478' -> [rows] (run.py --rows form; ascending, no duplicates) or ValueError."""
    out: list = []
    for part in str(text).split(","):
        m = re.fullmatch(r"(\d{1,4})(?:-(\d{1,4}))?", part.strip())
        if not m:
            raise ValueError(f"--rows: {part!r}")
        a, b = int(m.group(1)), int(m.group(2) or m.group(1))
        if not 1 <= a <= b:
            raise ValueError(f"--rows: {part!r}")
        out += list(range(a, b + 1))
    if len(set(out)) != len(out):
        raise ValueError("--rows: duplicated rows")
    return sorted(out)


def row_rerun_args(tag, rows, adopt_primary, reserved: str) -> tuple:
    """(ok, why, rows) for --row-rerun TAG --rows ROWS (2026-11-02): both or neither; TAG = run.py's form and not the
    amend_5 version's tag; no adoption (a row rerun recomputes its rows at this commit and nothing else)."""
    if tag is None and rows is None:
        return True, None, None
    if tag is None or rows is None:
        return False, "--row-rerun and --rows go together", None
    if not re.fullmatch(r"[a-z0-9][a-z0-9_]{0,39}", tag) or tag == reserved:
        return False, f"--row-rerun: TAG must match [a-z0-9][a-z0-9_]{{0,39}} and differ from {reserved!r}", None
    if adopt_primary:
        return False, "--row-rerun adopts nothing (--adopt-primary refused)", None
    try:
        return True, None, parse_row_list(rows)
    except ValueError as e:
        return False, str(e), None


def row_rerun_sanity(pass_dir: Path, rows: list, commit: str, pending_text: str) -> dict:
    """2026-11-02: a row-rerun pass wrote EXACTLY the asked rows, each at this commit, none reading material pending,
    with its RUN_SUMMARY.json present. Returns {"ok", "rows", "outcomes", "statuses", "why"} (vocabulary only)."""
    got: dict = {}
    why = None
    for f in sorted(Path(pass_dir).glob("row_[0-9][0-9][0-9][0-9].json")):
        d = json.loads(f.read_bytes().decode("utf-8"))
        n = int(d.get("row") or f.name[4:8])
        got[n] = d
        if (d.get("run_identity") or {}).get("run_commit") != commit:
            why = why or f"row {n}: run_commit is not {commit[:7]}"
        if d.get("status_written") == pending_text:
            why = why or f"row {n} reads '{pending_text}'"
    if sorted(got) != sorted(rows):
        why = f"rows written {sorted(got)} differ from the rows asked {sorted(rows)}"
    elif not (Path(pass_dir) / "RUN_SUMMARY.json").is_file():
        why = why or "RUN_SUMMARY.json absent"
    return {"ok": why is None, "rows": sorted(got), "outcomes": {n: d.get("outcome") for n, d in got.items()},
            "statuses": {n: str(d.get("status_written"))[:160] for n, d in got.items()}, "why": why}


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def git(*args, cwd=MAIN) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(doc, indent=1, default=str) + "\n").encode("utf-8")
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    if path.read_bytes() != data:
        raise OSError("read-back")


# ---- step 0 ---------------------------------------------------------------------------------------------------------
def plants_passed(summary: dict, classify: dict | None = None, compare_lf_sha256: str | None = None) -> tuple[bool, str]:
    if not str(summary.get("commit", "")).startswith(PLANT_COMMIT) or summary.get("tag") != TAG:
        return False, f"the §17 summary is not the {TAG} run at {PLANT_COMMIT}"
    passed = {s.get("step") for s in summary.get("steps", []) if s.get("exit") == 0}
    missing = [s for s in ("suite", "p1", "plants") if s not in passed]
    if missing:
        return False, "the §17 summary does not record as passed: " + ", ".join(missing)
    cmp_ = [s for s in summary.get("steps", []) if s.get("step") == "compare"]
    if cmp_ and cmp_[-1].get("exit") not in (0, None):
        ok, why = classify_explains(classify, compare_lf_sha256)
        if not ok:
            return False, "the §17 comparison flagged rows and " + why
        return True, f"suite, P1 and plants passed at {PLANT_COMMIT}; the comparison's flags explained ({why})"
    return True, "suite, P1 and plants passed at " + PLANT_COMMIT


def classify_explains(c: dict | None, compare_lf_sha256: str | None) -> tuple[bool, str]:
    """The §17 (4) classification accepted only if it reads CLASSIFY_READING, lists no substantive row, accounts for
    every flagged row by class, and names the comparison file the launcher hashes (LF bytes)."""
    if not isinstance(c, dict):
        return False, "no classification file"
    if c.get("reading") != CLASSIFY_READING:
        return False, "the classification does not read: " + CLASSIFY_READING
    if c.get("substantive_rows") != []:
        return False, "the classification lists substantive rows"
    by = c.get("by_class") or {}
    if set(by) - {"provenance", "label"} or sum(int(v) for v in by.values()) != c.get("n_flagged"):
        return False, "the classification does not account for every flagged row as provenance or label"
    if not compare_lf_sha256 or c.get("compare_sha256") != compare_lf_sha256:
        return False, "the classification names another comparison file"
    return True, f"classified: {', '.join(f'{k} {v}' for k, v in sorted(by.items()))}; 0 substantive"


# 2026-10-21 (G2 run 9): a statistic-path file admitted ONLY at one exact git blob, with the reason. descriptors.py's
# change adds one branch on an exception that would otherwise have stopped the pass (BrainSMASH on 7 parcels); no
# completed record (plants, ungated, G2 primary) can have taken it. The orchestrator decides whether this stands.
STAT_PATH_EXCEPTIONS = {
    "arcs/audit/src/a1_audit/descriptors.py": ("9ad8fec1b67b656313b72fac77fc674a91c30e35",
                                               "naive joint leg: 'not computable' when BrainSMASH itself raises"),
}


def blob_at(commit: str, path: str) -> str | None:
    r = git("rev-parse", f"{commit}:{path}")
    return r.stdout.strip() if r.returncode == 0 else None


def stat_exception_ok(commit: str, path: str) -> bool:
    pin = STAT_PATH_EXCEPTIONS.get(path)
    return pin is not None and blob_at(commit, path) == pin[0]


def diff_guard(old: str, new: str) -> tuple[bool, str, list]:
    if git("merge-base", "--is-ancestor", old, new).returncode != 0:
        return False, "the plant commit is not an ancestor of the commit", []
    r = git("diff", "--name-only", f"{old}..{new}")
    if r.returncode != 0:
        return False, "git diff failed", []
    files = sorted(f for f in r.stdout.splitlines() if f.strip())
    bad = [f for f in files if f.startswith(A1_READ_PREFIXES) and not any(rx.match(f) for rx in DIFF_ALLOWED)
           and not stat_exception_ok(new, f)]
    if bad:
        return False, f"the diff touches {len(bad)} file(s) outside DIFF_ALLOWED: " + ", ".join(bad[:10]), files
    return True, "allowed", files


def worktree(commit: str, short: str, dry: bool) -> tuple[Path | None, str]:
    wt = Path(f"D:/tmp/asdg_wt_a1_wp4_{short}")
    if wt.exists():
        if git("rev-parse", "HEAD", cwd=wt).stdout.strip() != commit:
            return None, "a directory of that name exists at another commit"
    elif dry:
        return wt, "would be created"
    elif git("worktree", "add", "--detach", str(wt), commit).returncode != 0:
        return None, "git worktree add failed"
    junction = wt / "artifacts"
    if not junction.exists() and not dry:
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(MAIN / "artifacts")], capture_output=True)
        if r.returncode != 0:
            return None, "the artifacts junction could not be made"
    if not dry:
        if git("rev-parse", "HEAD", cwd=wt).stdout.strip() != commit:
            return None, "the worktree HEAD is not the commit"
        if git("status", "--porcelain", cwd=wt).stdout.strip():
            return None, "the worktree is not clean"
    return wt, "ready"


def docker_up(wait_s: int = 600, start=True) -> bool:
    def ok():
        try:
            return subprocess.run(["docker", "info"], capture_output=True, timeout=60).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False
    if ok():
        return True
    if not start or not DOCKER_DESKTOP.is_file():
        return False
    subprocess.Popen([str(DOCKER_DESKTOP)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    t0 = time.time()
    while time.time() - t0 < wait_s:
        time.sleep(10)
        if ok():
            return True
    return False


def stop_twinpolis() -> int:
    try:
        ids = subprocess.run(["docker", "ps", "--filter", "name=twinpolis", "-q"], capture_output=True, text=True,
                             timeout=60).stdout.split()
        if ids:
            subprocess.run(["docker", "stop", *ids], capture_output=True, timeout=600)
        return len(ids)
    except (OSError, subprocess.TimeoutExpired):
        return -1


# ---- the material record (counts as section 8's rule prints them) ---------------------------------------------------
def material_record(wt: Path) -> dict:
    from a1_audit import wp4_layout as L
    roots = L.Roots.production(repo=wt, out_repo=MAIN)
    p = roots.latest_manifest()
    if p is None:
        return {"manifest": None, "partial_manifests": len(roots.partial_manifests())}
    data = Path(p).read_bytes()
    man = json.loads(data.decode("utf-8"))
    objs = man.get("objects") or {}
    deg = man.get("deg_checks") or {}
    out = {"manifest": Path(p).name, "manifest_sha256": hashlib.sha256(data).hexdigest(), "final": man.get("final"),
           "counts": man.get("counts"), "door_admitted": man.get("door_admitted"),
           "sets": man.get("sets"), "giacomel_comparison": man.get("giacomel_comparison"),
           "deg_checks": {"n": len(deg), "passed": sum(1 for v in deg.values() if v.get("passed")),
                          "statuses": sorted({str(v.get("status")) for v in deg.values()})},
           "r17": {k: (objs.get("r17") or {}).get(k) for k in ("status", "exit", "r_version", "bioc_version",
                                                                "params_sha256", "network")},
           "deviation": (objs.get("r17") or {}).get("deviation"),
           # amend_5 L130: the label every MDD-TPRS-derived G2 row carries (cells; the row records are run.py's)
           "labels": man.get("labels")}
    return out


def pins(wt: Path) -> dict:
    from a1_audit import wp4_layout as L
    from a1_audit import wp4_material as WM
    r13p = MAIN / WM.R13_RECORD_REL
    r13 = json.loads(r13p.read_bytes().decode("utf-8")) if r13p.is_file() else {}
    fc = L.frozen_check(wt)
    f5 = L.frozen_check(wt, rel=L.AMEND5_REL)
    return {"amend4": {"sha256": L.AMEND4_FROZEN_SHA256, "frozen_check_ok": fc["ok"]},
            "amend5": {"sha256": L.AMEND5_FROZEN_SHA256, "frozen_check_ok": f5["ok"]},
            "r13": {"record_sha256": hashlib.sha256(r13p.read_bytes()).hexdigest() if r13p.is_file() else None,
                    "repro_py_lf_sha256": r13.get("repro_py_lf_sha256"), "wgcna_check": r13.get("wgcna_check")}}


def step(name: str, cmd: list, cwd: Path, log: Path, dry: bool, env: dict | None = None) -> dict:
    t0 = time.time()
    rec = {"step": name, "argv": [Path(str(cmd[0])).name] + [str(c) for c in cmd[1:]], "started": now(),
           "log": str(log)}
    if env:
        rec["env"] = dict(env)
    if dry:
        rec.update(exit=None, note="dry: not run")
        return rec
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "wb") as fh:
        r = subprocess.run([str(c) for c in cmd], cwd=str(cwd), stdout=fh, stderr=subprocess.STDOUT,
                           env=dict(os.environ, **env) if env else None)
    rec.update(exit=int(r.returncode), finished=now(), seconds=round(time.time() - t0, 1))
    return rec


# 2026-10-21 (run 8): adopting another commit's PRIMARY material and passes (no recompute). The modules a commit after
# the adopted one may change: those whose change is proved not to reach a primary row by adopt_evidence (G2 loaders);
# any other changed code module (the statistic path, run.py, the S-build ...) refuses the adoption
ADOPT_STEPS = ("material", "verdict", "descriptor", "sensitivity")
ADOPT_MAY_CHANGE = frozenset({"arcs/audit/src/a1_audit/wp4_sources.py"})
ADOPT_NEVER_CODE = ("arcs/audit/src/a1_audit/tests/", "arcs/audit/src/a1_audit/wp4_launch.py",
                    "arcs/audit/src/a1_audit/report_cells.py")      # run by no pass (the launcher; the report step)


def adopt_code_check(old: str, new: str) -> tuple[bool, str, list]:
    """The code modules changed between the adopted commit and this one: each must be in ADOPT_MAY_CHANGE (tests and
    the launcher itself are not run code)."""
    r = git("diff", "--name-only", f"{old}..{new}")
    if r.returncode != 0:
        return False, "git diff failed", []
    files = sorted(f for f in r.stdout.splitlines() if f.endswith(".py") and f.startswith("arcs/audit/src/"))
    code = [f for f in files if not f.startswith(ADOPT_NEVER_CODE)]
    bad = [f for f in code if f not in ADOPT_MAY_CHANGE and not stat_exception_ok(new, f)]
    if bad:
        return False, "changed code outside ADOPT_MAY_CHANGE: " + ", ".join(bad[:10]), code
    return True, "only " + (", ".join(code) or "no code") + " changed", code


def adopt_evidence(results: Path, repo: Path, sources=None, version: str | None = None,
                   passes=("verdict", "descriptor", "sensitivity")) -> dict:
    """Every computed PRIMARY row of every adopted pass: its recorded map input hashes (row_provenance.input_hashes
    'map[...]') equal the hashes this commit's G2 sources give (the changed loader reproduces the adopted inputs)."""
    sys.path.insert(0, str(Path(repo) / "arcs/audit/src"))
    from a1_audit import run as R
    from a1_audit import wp3_layout as W3
    from a1_audit import wp4_layout as L
    from a1_audit import wp4_sources as W4S
    rows = {r.row: r for r in R.register_for_diagnostics(Path(repo)) if r.gate == "G2"}
    src = sources or W4S.WP4Sources(L.Roots.production(repo=repo, out_repo=repo,
                                                       version=version or L.VERSION_PRIMARY), W3.Roots.production())
    out = {}
    for ps in passes:
        n = same = 0
        diff = []
        for f in sorted((Path(results) / ps).glob("row_[0-9][0-9][0-9][0-9].json")):
            d = json.loads(f.read_bytes().decode("utf-8"))
            if d.get("outcome") != "computed":
                continue
            n += 1
            ih = {k: v for k, v in ((d.get("row_provenance") or {}).get("input_hashes") or {}).items()
                  if k.startswith("map[")}
            p = R.classify(rows[int(d["row"])], frozenset({"G2"}))
            try:
                mh = src.map(p, p["maps"][0])[3]
            except R.SourceUnavailable:
                mh = None
            if ih and ih == mh:
                same += 1
            else:
                diff.append(int(d["row"]))
        out[ps] = {"computed": n, "inputs_equal": same, "differing_rows": diff[:20]}
    out["ok"] = all(v["computed"] > 0 and v["computed"] == v["inputs_equal"] for v in out.values()
                    if isinstance(v, dict))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m a1_audit.wp4_launch")
    ap.add_argument("--commit", required=True)
    ap.add_argument("--jobs", type=int, default=20)
    ap.add_argument("--stop-after-material", action="store_true")
    ap.add_argument("--rerun-material", action="store_true")
    ap.add_argument("--resume-after-pause", default=None)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--adopt-primary", default=None, metavar="SHA",
                    help="adopt SHA's final material and primary verdict / descriptor / sensitivity (no recompute) "
                         "iff only ADOPT_MAY_CHANGE code changed and adopt_evidence holds")
    ap.add_argument("--row-rerun", default=None, metavar="TAG",
                    help="2026-11-02: rerun ROWS only (the material stage, then verdict / descriptor / sensitivity "
                         "--rows ROWS --rerun-tag TAG into results/a1_run/rerun_TAG/G2/, then the report); its own "
                         "summary (ROW_RERUN_SUMMARY); every other row's record stays as written")
    ap.add_argument("--rows", default=None, help="with --row-rerun: the rows (run.py --rows form, e.g. 478)")
    a = ap.parse_args(argv)
    from a1_audit import wp4_layout as L5
    ok_rr, why_rr, rr_rows = row_rerun_args(a.row_rerun, a.rows, a.adopt_primary, L5.AMEND5_RERUN_TAG)
    if not ok_rr:
        print(f"wp4_launch: refused: {why_rr}")
        return EXIT["refused"]
    commit = git("rev-parse", "--verify", a.commit + "^{commit}").stdout.strip()
    summ_path = MAIN / (ROW_RERUN_SUMMARY.format(tag=a.row_rerun) if rr_rows else SUMMARY)
    summ = json.loads(summ_path.read_bytes()) if summ_path.is_file() else {}
    if summ and summ.get("commit") != commit:
        keep = summ_path.with_name(f"{summ_path.stem}_{str(summ.get('commit') or 'unknown')[:7]}.json")
        if not a.dry and not keep.exists():
            data = summ_path.read_bytes()
            keep.write_bytes(data)
            if keep.read_bytes() != data:
                raise OSError("read-back")
        summ = {}
    done = {s["step"] for s in summ.get("steps", []) if s.get("exit") == 0}
    adopted, adopt_rec = [], None
    if a.adopt_primary:
        old = git("rev-parse", "--verify", a.adopt_primary + "^{commit}").stdout.strip()
        src_p = summ_path if json.loads(summ_path.read_bytes()).get("commit") == old else \
            summ_path.with_name(f"wp4_g2_summary_{old[:7]}.json")
        osum = json.loads(src_p.read_bytes()) if old and src_p.is_file() else {}
        steps = {st["step"]: st for st in osum.get("steps", []) if st.get("exit") == 0}
        missing = [n for n in ADOPT_STEPS if n not in steps or (n != "material" and not (steps[n].get("sanity") or
                                                                                          {}).get("ok"))]
        # also the post-exposure passes the old run completed (sanity ok), each from the commit that produced it
        # the post-exposure passes are NEVER adopted: run.py's C5 refuses a descriptor / sensitivity row whose verdict
        # record belongs to another run (commit, code hash, sources), so the three run together at this commit
        extra: list = []
        names = list(ADOPT_STEPS) + extra
        producers = {n: steps[n].get("adopted_from") or old for n in names if n in steps}
        checks = {pc: adopt_code_check(pc, commit) for pc in sorted(set(producers.values()))} if old else {}
        okc = bool(checks) and all(v[0] for v in checks.values())
        whyc = {pc[:7]: v[1] for pc, v in checks.items()}
        code = sorted({f for v in checks.values() for f in v[2]})
        fin = bool((osum.get("material") or {}).get("final"))
        ev = None
        if okc and not missing and fin:
            ev = {"primary": adopt_evidence(MAIN / "arcs/audit/results/a1_run/G2", MAIN)}
            pe_done = [n.split("_")[0] for n in extra]
            if pe_done:
                ev["amend5"] = adopt_evidence(MAIN / "arcs/audit/results/a1_run/rerun_amend5/G2", MAIN,
                                              version=L5.VERSION_AMEND5, passes=tuple(pe_done))
            ev["ok"] = all(v["ok"] for v in ev.values() if isinstance(v, dict))
        adopt_rec = {"from": old, "summary": src_p.name, "producers": {k: v[:7] for k, v in producers.items()},
                     "code_check": whyc, "changed_code": code, "missing_steps": missing, "material_final": fin,
                     "evidence": ev}
        if not (okc and not missing and fin and ev and ev["ok"]):
            print(json.dumps({"adoption": adopt_rec}, default=str, indent=1))
            return EXIT["refused"]
        adopted = [dict(steps[n], adopted_from=producers[n]) for n in names]
        done |= set(names)
        summ = dict(summ, material=osum.get("material"))
    if a.rerun_material:
        done.discard("material")
    doc = {"what": "WP4 phase 2, gate G2 (a1_audit.wp4_launch)", "commit": commit, "exit_codes": EXIT,
           "started": summ.get("started") or now(), "plant_commit": PLANT_COMMIT,
           "steps": [s for s in summ.get("steps", []) if s.get("exit") == 0 and s["step"] in done
                     and s["step"] not in {x["step"] for x in adopted}] + adopted}
    if adopt_rec is not None:
        doc["adopted"] = adopt_rec
        doc["material"] = summ.get("material")

    def finish(code: int, result: str, **kw) -> int:
        doc.update(finished=now(), exit=code, result=result, **kw)
        if a.dry:
            print(json.dumps(doc, indent=1, default=str))
        else:
            write_json(summ_path, doc)
        print(f"wp4_launch: exit {code} ({result}); summary {summ_path}")
        return code

    # 0 preconditions
    if not commit:
        return finish(EXIT["refused"], "refused", reason="the commit does not resolve")
    pre = MAIN / PRERUN_SUMMARY
    cl = MAIN / CLASSIFY
    cmp_file = MAIN / "arcs/audit/results/a1_run/s17_wp4_compare.json"
    ok, why = plants_passed(json.loads(pre.read_bytes()) if pre.is_file() else {},
                            json.loads(cl.read_bytes().decode("utf-8")) if cl.is_file() else None,
                            hashlib.sha256(cmp_file.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                            if cmp_file.is_file() else None)
    doc["precondition_s17"] = why
    if not ok:
        return finish(EXIT["refused"], "refused", reason=why)
    plant_full = git("rev-parse", "--verify", PLANT_COMMIT + "^{commit}").stdout.strip()
    ok, why, files = diff_guard(plant_full, commit)
    doc["precondition_diff"] = {"result": why, "files": files}
    if not ok:
        return finish(EXIT["refused"], "refused", reason=why)
    short = commit[:7]
    wt, why = worktree(commit, short, a.dry)
    doc["worktree"] = {"path": str(wt) if wt else None, "state": why}
    if wt is None:
        return finish(EXIT["refused"], "refused", reason=why)
    if not a.dry:
        doc["pins"] = pins(wt)
        if not doc["pins"]["amend4"]["frozen_check_ok"]:
            return finish(EXIT["refused"], "refused", reason="amendment 4's freeze check failed at the commit")
        if not doc["pins"]["amend5"]["frozen_check_ok"]:
            return finish(EXIT["refused"], "refused", reason="amendment 5's freeze check failed at the commit")
        if not docker_up():
            return finish(EXIT["docker"], "Docker unavailable")
    src = wt / "arcs/audit/src"
    logs = MAIN / "arcs/audit/results/a1_run/wp4_g2_launch_logs" / short    # beside, not inside, a1_run/G2/
    from a1_audit import wp4_layout as L5
    plan = [("material", [PY, "-X", "utf8", "-u", "-m", "a1_audit.wp4_material", "run", "--commit", commit],
             "material", None)]
    for pass_ in ("verdict", "descriptor", "sensitivity"):
        cmd = [PY, "-X", "utf8", "-u", "-m", "a1_audit.run", "--commit", commit, "--pass", pass_, "--gate", "G2",
               "--jobs", str(a.jobs)]
        if a.resume_after_pause:
            cmd += ["--resume-after-pause", a.resume_after_pause]
        plan.append((pass_, cmd, pass_, None))
    # amend_5 v2: the post-exposure version's passes (R61', R54', R58' (d)), after the primary ones, into
    # results/a1_run/rerun_amend5/G2/ (run.py --rerun-tag); the G2 sources read the manifest's post_exposure block
    for pass_ in ("verdict", "descriptor", "sensitivity"):
        cmd = [PY, "-X", "utf8", "-u", "-m", "a1_audit.run", "--commit", commit, "--pass", pass_, "--gate", "G2",
               "--jobs", str(a.jobs), "--rerun-tag", L5.AMEND5_RERUN_TAG]
        if a.resume_after_pause:
            cmd += ["--resume-after-pause", a.resume_after_pause]
        plan.append((f"{pass_}_{L5.AMEND5_RERUN_TAG}", cmd, pass_, {L5.VERSION_ENV: L5.VERSION_AMEND5}))
    if rr_rows:   # a row rerun: the material stage, then the three passes on ROWS only (primary version), then report
        doc["row_rerun"] = {"tag": a.row_rerun, "rows": rr_rows,
                            "out": f"arcs/audit/results/a1_run/rerun_{a.row_rerun}/G2/<pass>/"}
        plan = plan[:1]
        for pass_ in ("verdict", "descriptor", "sensitivity"):
            cmd = [PY, "-X", "utf8", "-u", "-m", "a1_audit.run", "--commit", commit, "--pass", pass_, "--gate", "G2",
                   "--jobs", str(a.jobs), "--rows", ",".join(map(str, rr_rows)), "--rerun-tag", a.row_rerun]
            if a.resume_after_pause:
                cmd += ["--resume-after-pause", a.resume_after_pause]
            plan.append((f"{pass_}_{a.row_rerun}", cmd, pass_, None))
    plan.append(("report", [PY, "-X", "utf8", "-u", "-m", "a1_audit.report_cells", "--gate", "G2", "--results-root",
                            MAIN / "arcs/audit/results"], "report", None))
    code, result = EXIT["ok"], "passed"
    try:
        for name, cmd, kind, env in plan:
            if name in done:
                continue
            rec = step(name, cmd, src, logs / f"{name}.log", a.dry, env)
            doc["steps"].append(rec)
            if name == "material" and not a.dry:
                doc["material"] = material_record(wt)
            if not a.dry:
                write_json(summ_path, doc)
            e = rec.get("exit")
            if name == "material" and e == 0 and not a.dry and not (doc.get("material") or {}).get("final"):
                e = rec["exit"] = 1
            if e == 0 and not a.dry and kind in ("verdict", "descriptor", "sensitivity"):
                tag = "rerun_" + L5.AMEND5_RERUN_TAG if name.endswith("_" + L5.AMEND5_RERUN_TAG) else None
                tag = f"rerun_{a.row_rerun}" if rr_rows else tag
                pdir = MAIN / "arcs/audit/results/a1_run" / (tag or "") / "G2" / kind
                fin = bool((doc.get("material") or material_record(wt) or {}).get("final"))
                if rr_rows:
                    rec["sanity"] = row_rerun_sanity(pdir, rr_rows, commit, L5.STATUS_PENDING)
                else:
                    rec["sanity"] = pass_sanity(pdir, kind, wt, fin,
                                                version=L5.VERSION_AMEND5 if tag else L5.VERSION_PRIMARY)
                write_json(summ_path, doc)
                if not rec["sanity"]["ok"]:
                    code, result = EXIT["sanity"], f"stopped: {name} sanity gate ({rec['sanity']['why']})"
                    break
            if e not in (None, 0):
                if kind in ("verdict", "descriptor", "sensitivity") and e == 4:
                    code, result = EXIT["paused"], "paused (§14): rerun with --resume-after-pause"
                else:
                    code, result = EXIT[kind], f"stopped: {name} exit {e}"
                break
            if name == "material" and a.stop_after_material:
                result = "stopped after the material stage (as asked)"
                break
    finally:
        if not a.dry:
            doc["twinpolis_stopped"] = stop_twinpolis()
    return finish(code, result)


if __name__ == "__main__":
    sys.exit(main())
