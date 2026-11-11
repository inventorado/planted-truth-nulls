"""MOR-C1..C3's R27 block under the WP3 run's code and under the pre-WP4 fix (run.component_r27), read only from the
recorded ungated verdict rows (pre-WP4 item 1; decision ev-1a12dffe1a85af7). No statistic is recomputed: the recorded
block (A3's labels, power columns and descriptors, computed at the run) is relabelled by the two versions of the
component rule only.

    python -X utf8 -m a1_audit.r27_relabel [--replace]

Writes arcs/audit/results/a1_run/ungated/r27_relabel_MOR-C.json (a NEW file; the row files are never modified), read
back. The run's own rule is checked in its blob: run.py at the run commit compares the kind to "component".
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from . import run as R

REPO = R.REPO
ROWS = {615: "MOR-C1", 616: "MOR-C2", 617: "MOR-C3"}
VERDICT_DIR = "arcs/audit/results/a1_run/ungated/verdict"
OUT = REPO / "arcs/audit/results/a1_run/ungated/r27_relabel_MOR-C.json"
RUN_COMMIT = "6b8fb62190c5b2fa105f73235ba3089315a338b7"   # the WP3 run commit (every row's provenance.run_commit)
OLD_RULE_LINE = '    if verdict_rec.get("kind") == "component":'


def git(*a) -> str:
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True).stdout.strip()


def old_rule(block: dict, vrec: dict) -> dict:
    """The WP3 run's rule (run.py r27_for_map at the run commit): the swap only when kind == "component"."""
    out = dict(block)
    if vrec.get("kind") == "component":
        out["reading_r27"] = out.pop("reading")
        out["reading"] = vrec.get("reading")
    return out


def verdict_rec_of(res: dict) -> dict:
    """The record r27_for_map is given, exactly as run._assemble_row builds it (run.r27_verdict_rec)."""
    return R.r27_verdict_rec(res["verdict"])


def build() -> dict:
    old_src = git("show", f"{RUN_COMMIT}:arcs/audit/src/a1_audit/run.py")
    if OLD_RULE_LINE not in old_src.splitlines():
        raise SystemExit("the run commit's run.py does not carry the recorded rule")
    out = {}
    for row, cell in ROWS.items():
        rel = f"{VERDICT_DIR}/row_{row:04d}.json"
        data = (REPO / rel).read_bytes()
        doc = json.loads(data.decode("utf-8"))
        if doc.get("cell_id") != cell or doc.get("provenance", {}).get("run_commit") != RUN_COMMIT:
            raise SystemExit(f"row {row}: not {cell} of the WP3 run")
        vrec = verdict_rec_of(doc["result"])
        per_map = {}
        for mi, block in doc["result"]["r27"].items():
            old = old_rule(block, {k: v for k, v in vrec.items() if k not in ("descriptor_row", "row_reading")})
            if old != block:   # apparatus: the old rule reproduces the recorded block exactly
                raise SystemExit(f"row {row}: the old rule does not reproduce the recorded block")
            new = R.component_r27(dict(block), vrec)
            per_map[mi] = dict(
                old_code=dict(reading=old.get("reading"), labels=old.get("labels")),
                new_code=dict(reading=new.get("reading"), reading_r27=new.get("reading_r27"), labels=new.get("labels"),
                              labels_notes=new.get("labels_notes"), component_reading=new.get("component_reading"),
                              component_label=new.get("component_label"), reading_rule=new.get("reading_rule")),
                unchanged=dict(power_columns=block.get("power_columns"), reading_class=block.get("reading_class"),
                               m=block["descriptors"]["m"], R2_grad=block["descriptors"]["R2_grad"]))
        out[cell] = dict(row=row, kind=vrec.get("kind"), primary_status=vrec.get("primary_status"),
                         input=dict(file=rel, sha256=hashlib.sha256(data).hexdigest(),
                                    committed_in=git("log", "-1", "--format=%H", "--", rel)),
                         per_map=per_map)
    return dict(what="MOR-C1..C3 R27 block: the WP3 run's code vs the pre-WP4 fix (run.component_r27); no statistic "
                     "recomputed (a1_audit.r27_relabel)",
                script="arcs/audit/src/a1_audit/r27_relabel.py",
                code=dict(old=f"run.py r27_for_map at the run commit {RUN_COMMIT[:7]} (kind == 'component')",
                          new="run.py component_r27 (COMPONENT_KINDS = %s), committed with this file" %
                              list(R.COMPONENT_KINDS),
                          generated_at_head=git("rev-parse", "HEAD")),
                species_label_note=R.COMPONENT_SPECIES_NOTE, descriptor_rule=R.DESCRIPTOR_COMPONENT_RULE,
                revision=("pre-WP4 review B1 / B2: a descriptor-routed row keeps its DESCRIPTIVE reading; the "
                          "species-leg label is kept in the labels with a note (it was moved out in 221691a)"),
                cells=out)


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    doc = build()
    if OUT.exists():   # this script's own output only; --replace rewrites it (the earlier version stays in git)
        if "--replace" not in a:
            raise SystemExit("the output file exists already (--replace rewrites this script's own output)")
        doc["replaces_sha256"] = hashlib.sha256(OUT.read_bytes()).hexdigest()
    data = (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    OUT.write_bytes(data)
    if OUT.read_bytes() != data:
        raise SystemExit("read-back differs")
    for cell, c in doc["cells"].items():
        for mi, b in c["per_map"].items():
            print(f"{cell} map {mi}: old '{b['old_code']['reading']}' {b['old_code']['labels']} -> new "
                  f"'{b['new_code']['reading']}' {b['new_code']['labels']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
