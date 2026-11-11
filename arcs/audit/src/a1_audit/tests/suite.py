"""The A1 test suite in one command (each module in its own process, from arcs/audit/src; RUN_PLAN §7's functional
plants P0, P2, P9, P10, P13-P21 and P23 live in these modules; WP4 phase 1 adds test_wp4_phase1).

    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.suite [--scratch DIR] [--out JSON] [--only m,m]
        [--require-docker]

Writes (and reads back) a JSON record: per module the command, exit code, seconds, the last summary line (ASCII) and
the PASS / FAIL counts it printed; exit 0 iff every module exited 0. Prints ASCII only.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1]
MODULES = ("test_ahba_builds", "test_amend1", "test_amend2", "test_forms", "test_gates_p21", "test_launch",
           "test_loader", "test_material_p18_p19_p20", "test_p0", "test_plants_scoring", "test_plants_wp2",
           "test_prewp4", "test_reprice_g1", "test_report_cells", "test_repro_p17", "test_run_p2", "test_seeds", "test_verdict",
           "test_wp1_fixes", "test_wp2r_fixes", "test_wp3_amend3", "test_wp3_phase1", "test_wp4_phase1")
SCRATCH_ARG = frozenset(("test_amend1", "test_amend2", "test_forms", "test_gates_p21", "test_material_p18_p19_p20",
                         "test_p0", "test_prewp4", "test_reprice_g1", "test_report_cells", "test_repro_p17", "test_run_p2", "test_verdict",
                         "test_wp1_fixes", "test_wp3_amend3", "test_wp3_phase1", "test_wp4_phase1"))
_PASS = re.compile(r"(?i)\b(pass|ok)\b")
_FAIL = re.compile(r"(?i)\bfail(ed)?\b")


def ascii_(s: str) -> str:
    return s.encode("ascii", "replace").decode("ascii")


def run_module(mod: str, scratch: Path, require_docker: bool, timeout: int) -> dict:
    cmd = [sys.executable, "-X", "utf8", "-u", "-m", f"a1_audit.tests.{mod}"]
    if mod in SCRATCH_ARG:
        # a short folder name: test_gates_p21 / test_material_p18_p19_p20 build scratch git repositories whose object
        # paths exceed Windows' 260-character limit under a long scratch root ("record_unreadable", 2026-10-16)
        d = scratch / f"m{MODULES.index(mod):02d}"
        d.mkdir(parents=True, exist_ok=True)
        cmd += ["--scratch", str(d)]
    if mod in ("test_repro_p17", "test_wp4_phase1") and require_docker:
        cmd.append("--require-docker")
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=str(SRC), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        code, out = r.returncode, r.stdout.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        code, out = -9, ""
    lines = [ln for ln in out.splitlines() if ln.strip()]
    scratch.mkdir(parents=True, exist_ok=True)
    log = scratch / f"{mod}.stdout.txt"                       # the module's own output, kept for inspection
    log.write_bytes(out.encode("utf-8"))
    assert log.read_bytes() == out.encode("utf-8")
    n_pass = sum(1 for ln in lines if re.match(r"^\s*(PASS|pass)\b", ln))
    n_fail = sum(1 for ln in lines if re.match(r"^\s*(FAIL|fail)\b", ln))
    return {"module": mod, "exit": int(code), "seconds": round(time.time() - t0, 1),
            "last_line": ascii_(lines[-1])[:300] if lines else "", "n_pass_lines": n_pass, "n_fail_lines": n_fail,
            "fail_lines": [ascii_(ln)[:200] for ln in lines if re.match(r"^\s*(FAIL|fail)\b", ln)][:20],
            "argv": [Path(cmd[0]).name] + cmd[1:]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", default=None)
    ap.add_argument("--require-docker", action="store_true")
    ap.add_argument("--timeout", type=int, default=14400)
    a = ap.parse_args(argv)
    import tempfile
    scratch = Path(a.scratch or tempfile.mkdtemp(prefix="a1_suite_"))
    mods = [m for m in MODULES if not a.only or m in a.only.split(",")]
    res = []
    for m in mods:
        r = run_module(m, scratch, a.require_docker, a.timeout)
        res.append(r)
        print(ascii_(f"{m}: exit {r['exit']} ({r['seconds']} s) | {r['last_line']}"), flush=True)
    doc = {"what": "A1 test suite (a1_audit.tests.suite)", "modules": res, "all_exit_0": all(r["exit"] == 0 for r in res),
           "n_modules": len(res)}
    if a.out:
        p = Path(a.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = (json.dumps(doc, indent=1) + "\n").encode("utf-8")
        p.write_bytes(data)
        if p.read_bytes() != data:
            raise OSError("read-back")
    print(f"suite: {sum(r['exit'] == 0 for r in res)} of {len(res)} modules exit 0", flush=True)
    return 0 if doc["all_exit_0"] else 1


if __name__ == "__main__":
    sys.exit(main())
