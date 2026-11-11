"""P1, fresh-worktree part (RUN_PLAN.md v3.1 §7 :1127, §1 :151 and :157-164, §2.3): run by the orchestrator INSIDE a
freshly created detached worktree at a commit (with its artifacts junction, §2.3).

  <main>\\env\\venv\\Scripts\\python.exe -X utf8 <wt>\\arcs\\audit\\src\\a1_audit\\tests\\p1_worktree.py --commit <sha> --out <json>
  (or, from <wt>\\arcs\\audit\\src:  ... -X utf8 -m a1_audit.tests.p1_worktree --commit <sha> --out <json>)

It
- checks it runs in a linked worktree (git dir != common dir), on a detached HEAD equal to --commit, with this
  package imported from that worktree, and that --out lies outside the worktree (so the tree stays clean);
- runs launch() twice, gate G2 and gate G1, with the real assertions (privacy guard self-test, env/venv_ref matrix
  hashes, gates.step3v_open / gates.g1_open), and asserts L1-L13 and L15 pass and L14 reads
  "not exercised (no G1 carrier stage)";
- shows that a check on the main tree's CRLF working-copy hash alone fails in the worktree: the sha256 of the
  worktree's bytes of e3_gates_a5.json (and of e3_catch_curves_a5.json and e3_gates_a3.json) differs from the CRLF pin,
  while the LF and blob checks pass;
- writes everything to --out (UTF-8, LF, read back) and exits 0 iff every expectation holds.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
SRC = HERE.parents[2]
WT = HERE.parents[5]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a1_audit import launch as L  # noqa: E402


def git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(WT), "-c", "core.quotepath=off", *args], capture_output=True)


def _under(p: Path, root: Path) -> bool:
    return p == root or root in p.parents


def prechecks(commit: str, out: Path) -> dict:
    gd = git("rev-parse", "--path-format=absolute", "--git-dir").stdout.decode().strip()
    cd = git("rev-parse", "--path-format=absolute", "--git-common-dir").stdout.decode().strip()
    head = git("rev-parse", "HEAD").stdout.decode().strip()
    want = git("rev-parse", "--verify", "--quiet", commit + "^{commit}").stdout.decode().strip()
    detached = git("symbolic-ref", "-q", "HEAD").returncode != 0
    pkg = Path(L.__file__).resolve()
    return {
        "a linked worktree (git dir != common dir)": bool(gd) and bool(cd) and Path(gd).resolve() != Path(cd).resolve(),
        "HEAD detached": detached,
        "HEAD == --commit": bool(want) and head == want,
        "a1_audit imported from this worktree": _under(pkg, WT.resolve()),
        "--out outside the worktree": not _under(out.resolve(), WT.resolve()),
        "artifacts present (junction)": (WT / "artifacts" / "ahba").is_dir(),
    }


def crlf_demo() -> dict:
    """RUN_PLAN.md :157-164: in an LF checkout the raw bytes' sha256 is not the CRLF pin; the LF and blob checks hold."""
    head = git("rev-parse", "HEAD").stdout.decode().strip()
    out = {}
    for path, (blob_id, lf_sha, crlf_sha) in ((L.GATES_A5_PATH, L.GATES_A5), (L.CATCH_PATH, L.CATCH),
                                              (L.GATES_A3_PATH, L.GATES_A3)):
        raw = (WT / path).read_bytes()
        raw_sha = hashlib.sha256(raw).hexdigest()
        bid = git("rev-parse", "%s:%s" % (head, path)).stdout.decode().strip()
        out[path] = {
            "worktree_cr": raw.count(b"\r"),
            "worktree_raw_sha256": raw_sha,
            "crlf_pin": crlf_sha,
            "check on the CRLF working-copy hash alone passes": raw_sha == crlf_sha,
            "LF check passes": hashlib.sha256(L.lf(raw)).hexdigest() == lf_sha,
            "blob check passes": bid == blob_id,
            "CRLF rebuilt from the LF bytes == the CRLF pin": hashlib.sha256(L.crlf_from_lf(L.lf(raw))).hexdigest() == crlf_sha,
        }
    return out


def run_gate(commit: str, gate: str) -> tuple[dict, dict]:
    try:
        rec = L.launch(WT, commit, gate)
    except L.LaunchRefused as e:
        rec = e.record
    st = {a["id"]: a for a in rec["assertions"]}
    exp = {"L%d pass" % i: st["L%d" % i]["status"] == "pass" and st["L%d" % i]["ok"] for i in range(1, 14)}
    exp["L14 reported 'not exercised (no G1 carrier stage)'"] = (
        st["L14"]["status"] == "not exercised" and st["L14"]["observed"] == L.NOT_EXERCISED_L14 and st["L14"]["ok"])
    exp["L15 pass (%s)" % ("gates.step3v_open" if gate == "G2" else "gates.g1_open")] = (
        st["L15"]["status"] == "pass" and st["L15"]["ok"])
    exp["launch passed"] = rec["passed"] is True and rec["failed"] == []
    return rec, exp


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    started = L.now_iso()
    pre = prechecks(a.commit, out)
    doc = {"what": "P1 fresh-worktree check (RUN_PLAN.md v3.1 §7 P1; §1 L1-L15; line endings :157-164)",
           "plan_sha256": L.PLAN_SHA256, "commit_arg": a.commit, "worktree": str(WT), "started": started,
           "prechecks": pre}
    ok = all(pre.values())
    if not pre["--out outside the worktree"]:
        print("p1_worktree: refused: --out lies inside the worktree")
        return 2
    if ok:
        launches, expect = {}, {}
        for gate in ("G2", "G1"):
            rec, exp = run_gate(a.commit, gate)
            launches[gate] = rec
            expect[gate] = exp
        demo = crlf_demo()
        demo_ok = all(d["worktree_cr"] == 0 and d["check on the CRLF working-copy hash alone passes"] is False
                      and d["LF check passes"] and d["blob check passes"] and d["CRLF rebuilt from the LF bytes == the CRLF pin"]
                      for d in demo.values())
        doc.update(launch=launches, expectations=expect, crlf_demonstration=demo,
                   crlf_demonstration_as_expected=demo_ok)
        ok = ok and all(all(e.values()) for e in expect.values()) and demo_ok
    doc["finished"] = L.now_iso()
    doc["passed"] = bool(ok)
    sha = L.write_record(doc, out)
    for k, v in pre.items():
        print("%-4s precheck: %s" % ("ok" if v else "FAIL", k))
    for gate, exp in (doc.get("expectations") or {}).items():
        for k, v in exp.items():
            print("%-4s %s: %s" % ("ok" if v else "FAIL", gate, k))
    for path, d in (doc.get("crlf_demonstration") or {}).items():
        print("%-4s CRLF demo %s: raw sha256 %s.. vs CRLF pin %s.. (CRLF-only check passes: %s); LF %s; blob %s"
              % ("ok" if (d["check on the CRLF working-copy hash alone passes"] is False and d["LF check passes"]
                          and d["blob check passes"]) else "FAIL", path.rsplit("/", 1)[-1], d["worktree_raw_sha256"][:12],
                 d["crlf_pin"][:8], d["check on the CRLF working-copy hash alone passes"], d["LF check passes"],
                 d["blob check passes"]))
    print("p1_worktree: %s; record %s sha256 %s" % ("PASSED" if ok else "FAILED", out.name, sha))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
