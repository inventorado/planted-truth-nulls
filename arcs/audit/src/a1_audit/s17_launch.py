"""The ONE launch of the RUN_PLAN.md §17 consequences before WP4 (arcs/audit/run_manifests/s17_wp4_prerun.json):
"1. P0-P26 are rerun; ... 3. every completed row whose computation passes through the changed code is rerun; 4. both
versions are reported, with the change, its commit and its reason." From a clean, pinned, detached worktree at the
commit (RUN_PLAN §2.3: created here as the earlier WP worktrees were, with the artifacts junction).

    D:\\RESEARCH\\asd-imaging-genetics\\env\\venv\\Scripts\\python.exe -X utf8 -u -m a1_audit.s17_launch --commit <sha>
        [--jobs 20] [--tag s17_wp4] [--stop-after-plants] [--resume-after-pause "<who / why>"] [--dry]
    (run from D:\\RESEARCH\\asd-imaging-genetics\\arcs\\audit\\src; Docker running for P17 / R13 and test_wp4_phase1)

Steps (each in the worktree, cwd <wt>\\arcs\\audit\\src, outputs under the MAIN repository, RUN_PLAN §2.3 :327-328):
  0 worktree D:\\tmp\\asdg_wt_a1_s17_<short>: `git worktree add --detach`, then `mklink /J <wt>\\artifacts
    <main>\\artifacts`; HEAD = --commit and `git status --porcelain` empty asserted (a present worktree at the commit is
    reused; nothing is ever removed or deleted);
  1 the test suite (a1_audit.tests.suite --require-docker): P0, P2, P9, P10, P13-P21, P23 and every module's checks;
  2 P1 in the fresh worktree (tests/p1_worktree.py);
  3 the official plant battery (a1_audit.plants.driver all --rerun-tag <tag>): P3a, P3b, P4-P8, P11, P12, P22, P24-P26;
  4 the reruns of the completed WP3 rows (a1_audit.run --gate none --rerun-tag <tag>; verdict, descriptor,
    sensitivity; resumable from checkpoints; paced by RUN_PLAN §14: exit 4 = paused, rerun this wrapper with
    --resume-after-pause "<who / why>");
  5 the comparison (a1_audit.s17_compare): old vs new per row.
The summary JSON results/a1_run/s17_<tag>_prerun_summary.json (read back) records every step's command, exit code
and times. A rerun of this wrapper skips the steps the summary records as passed at the same commit and tag.

Exit codes: 0 everything passed and no difference beyond the declared labels; 2 refused (worktree / commit / dirty);
4 a rerun pass paused (§14); 10 the suite failed; 11 P1 failed; 20 the plant battery failed (a FAIL criterion or a
refused launch); 30 a rerun pass failed; 40 the comparison flagged a difference (a DIFFERS row, or a
LABEL ONLY row outside the analysis's expected list: s17_compare exit 1; the expected label-only rows exit 0);
41 a row is missing in one version (s17_compare exit 2).
--stop-after-plants stops after step 3 (exit 0 if 1-3 passed): §17 (2) "asdg-skeptic re-reviews before any further
claim runs" can then sit between the plants and the reruns.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import subprocess
import sys
import time
from pathlib import Path

MAIN = Path(__file__).resolve().parents[4]
PY = MAIN / "env" / "venv" / "Scripts" / "python.exe"
EXIT = {"ok": 0, "refused": 2, "paused": 4, "suite": 10, "p1": 11, "plants": 20, "rerun": 30, "differs": 40,
        "missing": 41}


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def git(*args, cwd=MAIN) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def write_summary(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(doc, indent=1) + "\n").encode("utf-8")
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    if path.read_bytes() != data:
        raise OSError("read-back")


def worktree(commit: str, short: str, dry: bool) -> tuple[Path | None, str]:
    wt = Path(f"D:/tmp/asdg_wt_a1_s17_{short}")
    if wt.exists():
        head = git("rev-parse", "HEAD", cwd=wt).stdout.strip()
        if head != commit:
            return None, "a directory of that name exists at another commit"
    elif dry:
        return wt, "would be created"
    else:
        r = git("worktree", "add", "--detach", str(wt), commit)
        if r.returncode != 0:
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


def step(name: str, cmd: list, cwd: Path, log: Path, dry: bool) -> dict:
    t0 = time.time()
    rec = {"step": name, "argv": [Path(cmd[0]).name] + [str(c) for c in cmd[1:]], "started": now(), "log": str(log)}
    if dry:
        rec.update(exit=None, note="dry: not run")
        return rec
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "wb") as fh:
        r = subprocess.run([str(c) for c in cmd], cwd=str(cwd), stdout=fh, stderr=subprocess.STDOUT)
    rec.update(exit=int(r.returncode), finished=now(), seconds=round(time.time() - t0, 1))
    return rec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m a1_audit.s17_launch")
    ap.add_argument("--commit", required=True)
    ap.add_argument("--jobs", type=int, default=20)
    ap.add_argument("--tag", default="s17_wp4")
    ap.add_argument("--stop-after-plants", action="store_true")
    ap.add_argument("--resume-after-pause", default=None)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    # the plant driver's module path is run.py's reviewed hand-off constant (test_plants_wp2's isolation check allows no
    # other plants path in production code); it is run in a subprocess, never imported here
    from a1_audit.run import HANDOFF_DRIVER
    commit = git("rev-parse", "--verify", a.commit + "^{commit}").stdout.strip()
    res_root = MAIN / "arcs/audit/results/a1_run"
    summ_path = res_root / f"{a.tag}_prerun_summary.json"
    summ = json.loads(summ_path.read_bytes()) if summ_path.is_file() else {}
    if summ and (summ.get("commit") != commit or summ.get("tag") != a.tag):
        # another commit's summary is kept beside (copied, read back), never overwritten
        keep = res_root / f"{a.tag}_prerun_summary_{str(summ.get('commit') or 'unknown')[:7]}.json"
        if not a.dry and not keep.exists():
            data = summ_path.read_bytes()
            keep.write_bytes(data)
            if keep.read_bytes() != data:
                raise OSError("read-back")
        summ = {}
    done = {s["step"] for s in summ.get("steps", []) if s.get("exit") == 0}
    doc = {"what": "RUN_PLAN §17 pre-WP4 reruns (a1_audit.s17_launch)", "commit": commit, "tag": a.tag,
           "analysis": "arcs/audit/run_manifests/s17_wp4_prerun.json", "exit_codes": EXIT,
           "started": summ.get("started") or now(), "steps": [s for s in summ.get("steps", []) if s.get("exit") == 0]}
    if not commit:
        doc.update(result="refused", reason="the commit does not resolve", exit=EXIT["refused"])
        write_summary(summ_path, doc) if not a.dry else None
        return EXIT["refused"]
    short = commit[:7]
    wt, why = worktree(commit, short, a.dry)
    doc["worktree"] = {"path": str(wt) if wt else None, "state": why}
    if wt is None:
        doc.update(result="refused", reason=why, exit=EXIT["refused"])
        write_summary(summ_path, doc)
        return EXIT["refused"]
    src = wt / "arcs/audit/src"
    logs = res_root / f"rerun_{a.tag}" / "launch_logs" / short      # per commit: an earlier launch's logs stay
    plan = [
        ("suite", [PY, "-X", "utf8", "-u", "-m", "a1_audit.tests.suite", "--require-docker", "--out",
                   res_root / f"rerun_{a.tag}" / f"suite_{short}.json"], "suite"),
        ("p1", [PY, "-X", "utf8", "-u", src / "a1_audit/tests/p1_worktree.py", "--commit", commit, "--out",
                MAIN / f"arcs/audit/run_manifests/plants/rerun_{a.tag}/P1/p1_worktree_{short}.json"], "p1"),
        ("plants", [PY, "-X", "utf8", "-u", "-m", HANDOFF_DRIVER, "all", "--commit", commit, "--jobs",
                    str(a.jobs), "--rerun-tag", a.tag], "plants"),
    ]
    for pass_ in ("verdict", "descriptor", "sensitivity"):
        cmd = [PY, "-X", "utf8", "-u", "-m", "a1_audit.run", "--commit", commit, "--pass", pass_, "--gate", "none",
               "--jobs", str(a.jobs), "--rerun-tag", a.tag]
        if a.resume_after_pause:
            cmd += ["--resume-after-pause", a.resume_after_pause]
        plan.append((f"rerun_{pass_}", cmd, "rerun"))
    plan.append(("compare", [PY, "-X", "utf8", "-u", "-m", "a1_audit.s17_compare", "--old", res_root / "ungated",
                             "--new", res_root / f"rerun_{a.tag}" / "ungated", "--out",
                             res_root / f"{a.tag}_compare.json", "--manifest",
                             MAIN / "arcs/audit/run_manifests/s17_wp4_prerun.json"], "compare"))
    code = EXIT["ok"]
    for name, cmd, kind in plan:
        if a.stop_after_plants and kind in ("rerun", "compare"):
            break
        if name in done:
            continue
        rec = step(name, cmd, src, logs / f"{name}.log", a.dry)
        doc["steps"].append(rec)
        if not a.dry:
            write_summary(summ_path, doc)
        e = rec.get("exit")
        if e in (None, 0):
            continue
        if kind == "rerun" and e == 4:
            code = EXIT["paused"]
        elif kind == "compare":
            code = EXIT["missing"] if e == 2 else EXIT["differs"]
        else:
            code = EXIT[{"suite": "suite", "p1": "p1", "plants": "plants", "rerun": "rerun"}[kind]]
        break
    doc.update(finished=now(), exit=code, result="dry" if a.dry else ("passed" if code == 0 else "stopped"))
    if a.dry:
        print(json.dumps(doc, indent=1, default=str))
    else:
        write_summary(summ_path, doc)
    print(f"s17_launch: exit {code}; summary {summ_path}")
    return code


if __name__ == "__main__":
    sys.exit(main())
