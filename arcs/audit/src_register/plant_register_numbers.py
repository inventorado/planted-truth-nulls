"""Plant test of the register-number check (claims register DRAFT v6, decision R4 of the orchestrator under the operator's
standing delegation, 2026-09-26): the TSV builder parses claims_register.md's section 4 numbers and section 1.11 id lists
and must fail when one of them no longer equals the value derived from the TSV.

It runs in a scratch copy, never in the working tree: a local `git clone` of the programme repository into a temporary
directory, with the working copy's arcs/audit/ tree laid over it (the uncommitted v6 files included), so the builder's git
calls behave as in the working tree. Three builds run there:
  control  the register as it is                              -> must pass every check;
  plant 1  one section 4 number edited ('m.lower' - 1)          -> must fail with a 'register section 4 (R4)' error;
  plant 2  one id removed from a section 1.11 list (R2 list)    -> must fail with a 'register section 1.11 (R4)' error.
Nothing is written to the working tree. Prints pass / fail per case and counts only.
Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src_register\\plant_register_numbers.py [--workdir <dir>]
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT_REL = Path("arcs") / "audit"


def build(clone: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, "-X", "utf8", str(clone / AUDIT_REL / "claims_register_tsv_build.py")],
                       capture_output=True, text=True, encoding="utf-8", cwd=str(clone))
    return r.returncode, r.stdout + r.stderr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory(dir=a.workdir) as td:
        clone = Path(td) / "repo"
        subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(clone)], check=True)
        shutil.rmtree(clone / AUDIT_REL)
        shutil.copytree(ROOT / AUDIT_REL, clone / AUDIT_REL, ignore=shutil.ignore_patterns("__pycache__"))
        reg = clone / AUDIT_REL / "claims_register.md"
        original = reg.read_text(encoding="utf-8")
        results = []

        rc, out = build(clone)
        results.append(("control (register as it is)", rc == 0 and "CHECKS PASSED" in out, rc,
                        sum(1 for ln in out.splitlines() if ln.startswith("  - "))))

        m = re.search(r"^m\.lower = (\d+)$", original, re.M)
        if not m:
            print("STOP: no 'm.lower = <n>' line in the register's section 4 block")
            return 3
        planted = original[:m.start(1)] + str(int(m.group(1)) - 1) + original[m.end(1):]
        reg.write_text(planted, encoding="utf-8", newline="\n")
        rc, out = build(clone)
        hit = [ln for ln in out.splitlines() if ln.startswith("  - register section 4 (R4): 'm.lower'")]
        results.append(("plant 1: section 4 'm.lower' edited (%s -> %d)" % (m.group(1), int(m.group(1)) - 1),
                        rc != 0 and len(hit) == 1, rc, len(hit)))

        m2 = re.search(r"^(S conditional \(R2\) \[)(\d+)(\]: )([^,\n]+), ", original, re.M)
        if not m2:
            print("STOP: no 'S conditional (R2) [n]: ...' line in the register's section 1.11 block")
            return 3
        planted2 = original[:m2.start()] + m2.group(1) + str(int(m2.group(2)) - 1) + m2.group(3) + original[m2.end():]
        reg.write_text(planted2, encoding="utf-8", newline="\n")
        rc, out = build(clone)
        hit = [ln for ln in out.splitlines() if ln.startswith("  - register section 1.11 (R4): id list 'S conditional (R2)'")]
        results.append(("plant 2: section 1.11 R2 list with one id removed", rc != 0 and len(hit) == 1, rc, len(hit)))
        reg.write_text(original, encoding="utf-8", newline="\n")

    n_ok = 0
    for name, ok, rc, n in results:
        n_ok += ok
        print("[%s] %s (exit %d; %s %d)" % ("OK" if ok else "FAILED", name, rc,
                                           "failed checks" if name.startswith("control") else "matching R4 errors", n))
    print("register-number plant test: %d / %d cases as expected (scratch clone; the working tree untouched)"
          % (n_ok, len(results)))
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
