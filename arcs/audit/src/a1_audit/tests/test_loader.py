"""Loader test (RUN_PLAN.md v3.1 §4 "Loader"; L12 :152): counts and the gated-status parse on every gated row.

Run from arcs/audit/src:  ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_loader
Exits non-zero if any check fails. Prints counts under fixed labels only; no row text is printed.

The launch record given to the loader is a preflight of L1-L3 on the main tree at HEAD (the main tree is dirty, so a
full launch refuses on L11); the loader is called with allow_unlaunched=True for that reason, and its refusal of the
same record without it is checked.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

from a1_audit import launch as L
from a1_audit import loader

REPO = Path(__file__).resolve().parents[5]
RESULTS: list[tuple[str, bool]] = []
# fixed vocabulary of the status-under-gate's leading words (labels printed instead of row text)
UNDER_LABELS = ("not testable as stated", "not testable (<", "not auditable", "resolution-limited", "no calibrated test",
                "component-level", "conditional", "auditable", "tested", "out of scope", "deferred")


def check(name: str, cond) -> bool:
    RESULTS.append((name, bool(cond)))
    print("%s  %s" % ("PASS" if cond else "FAIL", name))
    return bool(cond)


def label_of(text: str) -> str:
    for lab in UNDER_LABELS:
        if text.startswith(lab):
            return lab
    return "other"


def refused(fn) -> bool:
    try:
        fn()
        return False
    except loader.LoaderRefused:
        return True


def preflight(repo: Path, files_root=None) -> dict:
    head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip()
    ctx = L.make_ctx(repo, head, files_root)
    return {"repo_root": str(ctx.repo), "files_root": None if files_root is None else str(ctx.files),
            "run_commit": ctx.commit, "passed": False, "gate": None,
            "assertions": [L.l1_register(ctx), L.l2_tsv(ctx), L.l3_manifest(ctx)]}


def main() -> int:
    rec = preflight(REPO)
    check("preflight: L1, L2, L3 pass on the main tree at HEAD", all(a["ok"] for a in rec["assertions"]))
    check("load refused without allow_unlaunched (the launch did not pass)", refused(lambda: loader.load(REPO, rec)))
    reg = loader.load(REPO, rec, allow_unlaunched=True)
    rows = reg.rows()
    check("692 rows keyed 1..692", len(reg) == 692 and [r.row for r in rows] == list(range(1, 693)))
    raw = L.lf((REPO / loader.TSV_PATH).read_bytes()).decode("utf-8")
    data_lines = [ln for ln in raw[:-1].split("\n") if not ln.startswith("#")][1:]
    check("every row kept verbatim (fields re-joined == the TSV line; line == the file's line)",
          all("\t".join(r[c] for c in loader.COLUMNS) == r.line == ln for r, ln in zip(rows, data_lines))
          and len(data_lines) == 692)

    # ---- L12 counts
    c = reg.counts()
    block = L.parse_section4_block(L.lf((REPO / L.REGISTER_PATH).read_bytes()).decode("utf-8"))
    print("     rows %d; m lower %d, upper %d; gate %s" % (c["rows"], c["m.lower"], c["m.upper"],
                                                         ", ".join("%s %d" % kv for kv in c["gate"].items())))
    check("L12: rows 692, m 207 (upper 207)", c["rows"] == 692 and c["m.lower"] == 207 and c["m.upper"] == 207)
    check("L12: rows per gate G1 380 / G2 194 / none 115 / G1+G2 3", c["gate"] == {"G1": 380, "G2": 194, "none": 115, "G1+G2": 3})
    check("L12: m per target == the section 4 block (15 targets, sum 207)",
          c["m.target"] == {k[len("m.target."):]: v for k, v in block.items() if k.startswith("m.target.")} == L.M_PER_TARGET
          and sum(c["m.target"].values()) == 207)
    check("L12: every comparison of launch.l12_compare holds", all(L.l12_compare(c, block).values()))

    # ---- gated-status parse on every gated row
    gated = [r for r in rows if r.gate in ("G1", "G2")]
    check("every G1 / G2 row parses as 'deferred (gate Gx closed); <status>' naming its own gate (574 rows)",
          len(gated) == 574 and all(r.gated is not None and r.gated[0] == r.gate for r in gated))
    check("no 'none' or 'G1+G2' row is in the gated form", all(r.gated is None for r in rows if r.gate in ("none", "G1+G2")))
    check("the status under the gate is the text after the prefix, verbatim",
          all(r.status == "deferred (gate %s closed); %s" % r.gated for r in gated))
    by = Counter((r.gated[0], label_of(r.gated[1])) for r in gated)
    for (g, lab), n in sorted(by.items()):
        print("     %s  %-24s %d" % (g, lab, n))
    check("status-under-gate counts sum to G1 380 and G2 194",
          sum(n for (g, _), n in by.items() if g == "G1") == 380 and sum(n for (g, _), n in by.items() if g == "G2") == 194)
    check("every status under a gate falls under a fixed label (no 'other')", by.get(("G1", "other"), 0) == 0 and by.get(("G2", "other"), 0) == 0)

    # ---- effective status
    def changed(og):
        return sum(1 for r in rows if loader.effective_status(r, og) != r.status)
    check("effective_status: no gate open -> every row's status verbatim (0 changed)", changed(set()) == 0)
    check("effective_status: G2 open -> the 194 G2 rows take the status under the gate, G1 rows stay deferred",
          changed({"G2"}) == 194 and all(loader.effective_status(r, {"G2"}) == r.gated[1] for r in gated if r.gate == "G2")
          and all(loader.effective_status(r, {"G2"}) == r.status for r in gated if r.gate == "G1"))
    check("effective_status: G1 open -> 380 changed; both open -> 574 changed", changed({"G1"}) == 380 and changed({"G1", "G2"}) == 574)
    check("effective_status: Dear's G1+G2 rows (deferred pending provenance) stay verbatim with both gates open",
          all(loader.effective_status(r, {"G1", "G2"}) == r.status for r in rows if r.gate == "G1+G2"))
    try:
        loader.effective_status(rows[0], {"G3"})
        check("effective_status rejects an unknown gate", False)
    except ValueError:
        check("effective_status rejects an unknown gate", True)
    l15 = {"id": "L15", "ok": True, "status": "pass"}
    check("open_gates_from: a passed G2 launch with L15 pass -> {G2}",
          loader.open_gates_from({"passed": True, "gate": "G2", "assertions": [l15]}) == {"G2"})
    check("open_gates_from: a refused launch -> none",
          loader.open_gates_from({"passed": False, "gate": "G2", "assertions": [l15]}) == frozenset())
    check("open_gates_from: an ungated launch (L15 not applicable) -> none",
          loader.open_gates_from({"passed": True, "gate": None,
                                  "assertions": [dict(l15, status="not applicable")]}) == frozenset())
    check("open_gates_from: a passed G2 launch run with test overrides (stubs) -> none",
          loader.open_gates_from({"passed": True, "gate": "G2", "test_overrides": ["gates_module"],
                                  "assertions": [l15]}) == frozenset())
    check("load refuses a passed launch run with test overrides (no allow_unlaunched)",
          refused(lambda: loader.load(REPO, dict(rec, passed=True, test_overrides=["guard_selftest"]))))
    check("open_gates_from: L15 not 'pass' -> none",
          loader.open_gates_from({"passed": True, "gate": "G1", "assertions": [dict(l15, ok=False, status="fail")]}) == frozenset())

    # ---- exposed fields (counts only)
    forms = Counter(r.claim_form for r in rows)
    print("     claim_form: " + ", ".join("%s %d" % kv for kv in sorted(forms.items())))
    check("claim_form exposed for every row (6 forms; 692)", len(forms) == 6 and sum(forms.values()) == 692)
    tg = Counter(r.target_no for r in rows)
    check("target number exposed as int; targets 1..21 all present", sorted(tg) == list(range(1, 22)))
    mm = Counter(r.m_membership for r in rows)
    print("     m membership: " + ", ".join("%s %d" % kv for kv in sorted(mm.items())))
    check("m membership exposed: yes 207, no 485", mm == Counter({"yes": 207, "no": 485}) and sum(r.in_m for r in rows) == 207)
    dirs = Counter(r.direction for r in rows)
    print("     direction field: %d distinct values, %d empty" % (len(dirs), dirs.get("", 0)))
    check("direction exposed verbatim (str) for every row", all(isinstance(r.direction, str) for r in rows))
    check("map / cell index texts exposed; int_or_none parses only plain integers",
          loader.int_or_none("0") == 0 and loader.int_or_none("12") == 12 and loader.int_or_none("01") is None
          and loader.int_or_none("0 = ABIDE I; 1 = ABIDE II") is None and loader.int_or_none("") is None)

    # ---- planted refusals
    bad = dict(rec, assertions=[dict(a, ok=(a["id"] != "L2")) for a in rec["assertions"]])
    check("planted: a record with L2 failed is refused", refused(lambda: loader.load(REPO, bad, allow_unlaunched=True)))
    bad = dict(rec, assertions=[a for a in rec["assertions"] if a["id"] != "L3"])
    check("planted: a record without L3 is refused", refused(lambda: loader.load(REPO, bad, allow_unlaunched=True)))
    bad = dict(rec, repo_root=str(REPO / "arcs"))
    check("planted: a record naming another repository root is refused", refused(lambda: loader.load(REPO, bad, allow_unlaunched=True)))
    base = Path(os.environ.get("A1_SCRATCH") or tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="a1_loader_", dir=str(base)))
    try:
        p = scratch / loader.TSV_PATH
        p.parent.mkdir(parents=True)
        b = bytearray((REPO / loader.TSV_PATH).read_bytes())
        i = len(b) // 2
        b[i] = b[i] ^ 1
        p.write_bytes(bytes(b))
        rec_copy = dict(rec, files_root=str(scratch))  # L1-L3 passed on the real files; the loader re-hashes what it parses
        check("planted: TSV bytes changed after L2 (one byte) -> the loader's re-hash refuses",
              refused(lambda: loader.load(REPO, rec_copy, allow_unlaunched=True)))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    tsv = L.lf((REPO / loader.TSV_PATH).read_bytes())
    head_len = tsv.index(("\n" + data_lines[0] + "\n").encode("utf-8")) + 1
    hdr, body = tsv[:head_len], tsv[head_len:].decode("utf-8")
    lines = body[:-1].split("\n")

    def with_row(k: int, col: str, fn) -> bytes:
        parts = lines[k].split("\t")
        j = loader.COLUMNS.index(col)
        parts[j] = fn(parts[j])
        new = lines[:k] + ["\t".join(parts)] + lines[k + 1:]
        return hdr + ("\n".join(new) + "\n").encode("utf-8")

    k1 = next(i for i, r in enumerate(rows) if r.gate == "G1")
    kn = next(i for i, r in enumerate(rows) if r.gate == "none")
    pl = [
        ("a G1 row whose status names gate G2", with_row(k1, "status", lambda s: s.replace("gate G1 closed", "gate G2 closed", 1))),
        ("a G1 row whose status is not in the gated form", with_row(k1, "status", lambda s: s.replace("; ", " - ", 1))),
        ("a 'none' row in the gated form", with_row(kn, "status", lambda s: "deferred (gate G1 closed); " + s)),
        ("an unknown gate value", with_row(kn, "gate", lambda s: "G3")),
        ("an unregistered verdict_counted_in_m", with_row(kn, "verdict_counted_in_m", lambda s: "maybe")),
        ("row numbers out of order", with_row(5, "row", lambda s: "999")),
        ("a row with 32 fields", hdr + ("\n".join(lines[:3] + [lines[3].rsplit("\t", 1)[0]] + lines[4:]) + "\n").encode("utf-8")),
        ("a CR in the bytes", tsv.replace(b"\n", b"\r\n", 1)),
        ("a comment line after the header", hdr + ("\n".join(lines[:2] + ["# x"] + lines[2:]) + "\n").encode("utf-8")),
    ]
    for label, data in pl:
        check("planted: parse refuses %s" % label, refused(lambda d=data: loader.parse_tsv_bytes(d)))
    check("control: the unmodified bytes parse (692 rows)", len(loader.parse_tsv_bytes(tsv)[1]) == 692)
    check("parse_gated on synthetic strings",
          loader.parse_gated("deferred (gate G1 closed); a; b") == ("G1", "a; b")
          and loader.parse_gated("deferred (gate G1 closed);a") is None
          and loader.parse_gated("deferred (gate G3 closed); a") is None
          and loader.parse_gated("deferred (gate G1 closed)") is None
          and loader.parse_gated("x deferred (gate G1 closed); a") is None)

    n_fail = sum(1 for _, ok in RESULTS if not ok)
    print("test_loader: %d checks, %d passed, %d failed" % (len(RESULTS), len(RESULTS) - n_fail, n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
