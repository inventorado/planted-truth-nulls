"""RUN_PLAN §17 (4), session 14: classify every row flagged by a1_audit.s17_compare (results/a1_run/s17_wp4_compare.json).

The comparator flags a row if any field differs. This sorts each differing field into:
  provenance  - the rerun's own identity (output roots, rerun tag / rule); expected for a rerun from another worktree
  label       - a reading / label text the pre-WP4 change was meant to change (sensitivity rule text, R27 component labels,
                and primary_result_sha256, whose payload contains those labels)
  substantive - anything else (statistics, p, verdicts, seeds, input hashes, ...)
and writes run_manifests/s17_wp4_classify.json. Run from arcs/audit:  python run_manifests/s17_wp4_classify.py
"""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CMP = HERE.parent / "results" / "a1_run" / "s17_wp4_compare.json"
OUT = HERE / "s17_wp4_classify.json"
PROVENANCE = (".rerun_rule", ".rerun_tag", ".run_identity.sources.roots.")
LABEL = (".inputs.analysis_parcels.0.rule", ".result.r27.0.component_label", ".result.r27.0.component_reading",
         ".result.r27.0.reading", ".result.r27.0.reading_r27", ".result.r27.0.reading_rule", ".result.r27.0.labels_notes",
         ".result.primary_result_sha256")


def kind(field: str) -> str:
    if field.startswith(PROVENANCE):
        return "provenance"
    if field in LABEL:
        return "label"
    return "substantive"


def main() -> None:
    raw = CMP.read_bytes()
    d = json.loads(raw)
    per_row, fields = [], collections.Counter()
    for it in d["flagged"]:
        ks = collections.Counter(kind(f) for f in it["differing_fields"])
        cls = "substantive" if ks["substantive"] else ("label" if ks["label"] else "provenance")
        per_row.append(dict(pass_=it["pass"], file=it["file"], cls=cls, **{f"n_{k}": ks[k] for k in ("provenance", "label", "substantive")}))
        for f in it["differing_fields"]:
            if kind(f) != "provenance":
                fields[f] += 1
    by = collections.Counter(r["cls"] for r in per_row)
    by_pass = collections.Counter((r["pass_"], r["cls"]) for r in per_row)
    out = dict(what="RUN_PLAN §17 (4) classification of s17_compare's flagged rows (session 14)",
               compare_file=str(CMP.relative_to(HERE.parent)), compare_sha256=hashlib.sha256(raw).hexdigest(),
               n_files=d["n_files"], n_flagged=len(per_row), by_class=dict(by),
               by_pass={f"{p}|{c}": n for (p, c), n in sorted(by_pass.items())},
               non_provenance_fields=dict(fields.most_common()),
               substantive_rows=[r for r in per_row if r["cls"] == "substantive"],
               reading=("no statistic, p, verdict, seed or input hash changed" if by["substantive"] == 0 else
                        "SUBSTANTIVE DIFFERENCES: see substantive_rows"),
               rows=per_row)
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("n_files", "n_flagged", "by_class", "by_pass", "non_provenance_fields", "reading")}, indent=1))


if __name__ == "__main__":
    main()
