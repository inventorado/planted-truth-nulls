"""L14 glue (arcs/audit/RUN_PLAN.md v3.1, FROZEN: §1 L14 :154; §2.2 "Gate launcher" :302-304).

L14: "`carrier_test.py selftest --workdir <dir>` equal to the frozen record (`:1288-1291`); pdfplumber == 0.11.10 before
any PDF carrier (`:1301-1302`); `carrier_test.py` is started only by the gate launcher (§2.2)".

This module is the only place the A1 runner obtains the carrier self-test's output, and it obtains it ONLY by starting
the gate launcher (`python -m a1_audit.gate_launch G1 --repo <repo> --carrier-test selftest --workdir <dir>`) in a
subprocess: the launcher runs `require_g1_open()` and only then starts `<repo>/arcs/audit/src_register/carrier_test.py`.
It never starts carrier_test.py itself, never passes any argument but `selftest --workdir <dir>` (in particular never
`--overwrite-frozen-record`), and returns what launch.l14_compare reads:

    {"returncode": int, "stdout": <the carrier's stdout, the launcher's own lines removed>,
     "record": <the JSON the self-test wrote to <workdir>/carrier_tests_selftest.json, or None>}

plus bookkeeping fields (the launcher's fixed-vocabulary lines, whether the carrier was started, whether the gate
refused). The workdir must be empty (or absent) before the call, so a stale record can never be read as this run's.

`launch_carrier_stage(repo, commit, workdir, ...)` runs the glue and passes its output to launch.launch(...,
carrier_stage=True, carrier_selftest=...): the L14 comparison of launch.py, unchanged.

Tests: tests/test_run_p2.py part L14 drives the glue against a FAKE carrier_test.py in a scratch git repository whose G1
record opens (P21's scratch builder), with a planted differing record and a closed gate that the comparison must refuse.
The real carrier_test.py is never run by WP1.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from . import launch as LA

RECORD_NAME = "carrier_tests_selftest.json"   # carrier_test.py:2097 (outp = workdir / "carrier_tests_selftest.json")
LAUNCHER_PREFIX = "gate_launch: "
SRC_DIR = Path(__file__).resolve().parents[1]  # arcs/audit/src (the a1_audit package's parent)


class GlueRefused(RuntimeError):
    """A precondition of the glue failed (workdir not empty, ...); nothing was started."""


def carrier_selftest_via_launcher(repo, workdir, *, python: str | None = None, src_dir=None,
                                  timeout: int = 7200) -> dict:
    """Start the gate launcher's --carrier-test selftest for `repo` with `workdir`; return launch.l14_compare's input
    (returncode, stdout, record) and bookkeeping. Raises GlueRefused if workdir is not empty."""
    repo = Path(repo).resolve()
    wd = Path(workdir).resolve()
    if wd.exists() and any(wd.iterdir()):
        raise GlueRefused("the carrier self-test workdir must be empty (a stale record would be read as this run's)")
    wd.mkdir(parents=True, exist_ok=True)
    src = Path(src_dir).resolve() if src_dir else SRC_DIR
    env = dict(os.environ)
    env["PYTHONPATH"] = str(src)
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [python or sys.executable, "-X", "utf8", "-m", "a1_audit.gate_launch", "G1", "--repo", str(repo),
           "--carrier-test", "selftest", "--workdir", str(wd)]
    r = subprocess.run(cmd, cwd=str(src), capture_output=True, env=env, timeout=timeout)
    lines = r.stdout.decode("utf-8", "replace").splitlines()
    launcher = [ln for ln in lines if ln.startswith(LAUNCHER_PREFIX)]
    child = [ln for ln in lines if not ln.startswith(LAUNCHER_PREFIX)]
    rec_path = wd / RECORD_NAME
    record = None
    record_error = None
    if rec_path.is_file():
        try:
            record = json.loads(rec_path.read_bytes().decode("utf-8"))
        except ValueError as e:
            record_error = type(e).__name__
    started = any(ln == LAUNCHER_PREFIX + "starting carrier_test.py" for ln in launcher)
    refused = any(" CLOSED " in ln for ln in launcher)
    return {"returncode": r.returncode, "stdout": "\n".join(child) + ("\n" if child else ""), "record": record,
            "record_error": record_error, "launcher_lines": launcher, "carrier_started": started,
            "gate_refused": refused, "stderr_bytes": len(r.stderr)}


def launch_carrier_stage(repo, run_commit: str, workdir, *, python: str | None = None, src_dir=None,
                         **launch_kw) -> dict:
    """A G1 carrier stage's launch: the glue's output into launch.launch(..., carrier_stage=True, ...) (L14). Raises
    launch.LaunchRefused (with the record) if any assertion fails, as launch() does."""
    out = carrier_selftest_via_launcher(repo, workdir, python=python, src_dir=src_dir)
    return LA.launch(repo, run_commit, "G1", carrier_stage=True,
                     carrier_selftest={k: out[k] for k in ("returncode", "stdout", "record")}, **launch_kw)
