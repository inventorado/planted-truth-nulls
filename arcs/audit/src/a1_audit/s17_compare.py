"""RUN_PLAN.md §17 (4) "both versions are reported, with the change, its commit and its reason": the old vs new
comparison of every completed row after the §17 reruns (WP4 pre-run; arcs/audit/run_manifests/s17_wp4_prerun.json).

    python -X utf8 -m a1_audit.s17_compare --old <results/a1_run/ungated> --new <results/a1_run/rerun_<tag>/ungated>
        --out <results/a1_run/s17_<tag>_compare.json> [--manifest arcs/audit/run_manifests/s17_wp4_prerun.json]

Per pass (verdict, descriptor, sensitivity) and row file row_<n>.json (and its row_<n>_repro.json / _rlm.json
beside), both versions are read and summarised: outcome, written status, the statistic T, the conjunction p (and
each leg's reported p), the verdict (survives, primary status, reading) and the label (R27's reading and labels).
The WHOLE row document is compared (asdg-skeptic B2, 2026-10-16) after removing only the fields that differ by
construction between two runs: VOLATILE (timings, memory, process ids, checkpoint paths, stamps, run commit, code
hash, provenance; row_provenance except its seeds and input_hashes, C9) at any depth and the run-header keys RUN_HEADER at the top level (stamp, output_root, threads,
threads_before, the verdict file's hash a sensitivity row carries, and run_identity's run_commit / code_hash). Every
other field - label, status_effective, route, K, g6l_mode, view, inputs, result ... - is compared, field by field
(dotted paths). Nothing is recomputed here: it reads row files only.

A differing field is a LABEL only if its path is one of LABEL_PATTERNS (B1: R27's `.result.r27.<k>.reading` /
`.labels[...]`, never its numeric descriptors; the sensitivity parcel rule text `.inputs.analysis_parcels.<k>.rule`).
A row whose differences are all labels is "LABEL ONLY (expected)" when the §17 analysis lists (pass, row, pattern)
as expected (s17_wp4_prerun.json "label_only_expected": the verdict rows 615-617 MOR-C1..C3, R27's reading; the
sensitivity pass's computed rows, the parcel rule text), else "LABEL ONLY (not expected)", which counts as a
difference. Any other difference is "DIFFERS".

Exit codes (C6): 0 no difference beyond the EXPECTED label-only rows; 1 a DIFFERS row or an unexpected label-only row
(s17_launch maps it to its exit 40); 2 a row of one version is missing from the other (s17_launch: 41). Without
--manifest no label-only row is expected (every one exits 1).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

PASSES = ("verdict", "descriptor", "sensitivity")
VOLATILE = frozenset(("seconds", "started", "finished", "memory", "pid", "elapsed", "timing", "wall", "_meta",
                      "peak_working_set", "peak_bytes", "stamp", "screen_dir", "ck_dir", "dir", "path", "written",
                      "run_commit", "code_hash", "provenance", "row_provenance", "launch_record", "date_utc"))
SUMMARY_KEYS = ("T", "conjunction_p", "survives", "primary_status", "reading", "passes_at_alpha", "d_star")
RUN_HEADER = frozenset(("stamp", "output_root", "threads", "threads_before", "verdict_file_sha256"))
RUN_IDENTITY_VOLATILE = frozenset(("run_commit", "code_hash"))
# B1: the paths whose change is a LABEL (full-path patterns): R27's reading and labels per map (never R27's numeric
# descriptors: p_hypergeom, R2_grad, f, m, c_S, r_yw_dB ...); the sensitivity parcel rule's text
LABEL_PATTERNS = {"r27_reading": re.compile(r"^\.result\.r27\.[^.\[]+\.(reading|labels)(\[\d+\]|\[len\])?$"),
                  "parcel_rule_text": re.compile(r"^\.inputs\.analysis_parcels\.[^.\[]+\.rule$")}


def _canon(o, path=""):
    if isinstance(o, dict):
        return {k: _canon(v, f"{path}.{k}") for k, v in sorted(o.items()) if k not in VOLATILE}
    if isinstance(o, list):
        return [_canon(v, f"{path}[{i}]") for i, v in enumerate(o)]
    if isinstance(o, float) and not math.isfinite(o):
        return repr(o)
    return o


def diff_paths(a, b, path: str = "", out: list | None = None, limit: int = 50) -> list:
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if type(a) is not type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        out.append(path or "<root>")
        return out
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}.{k}")
            else:
                diff_paths(a[k], b[k], f"{path}.{k}", out, limit)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{path}[len]")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                diff_paths(x, y, f"{path}[{i}]", out, limit)
    elif a != b:
        out.append(path or "<root>")
    return out


def _first(o, key):
    """The first value of `key` in a depth-first walk (dict keys in sorted order)."""
    if isinstance(o, dict):
        if key in o and not isinstance(o[key], (dict, list)):
            return o[key]
        for k in sorted(o):
            v = _first(o[k], key)
            if v is not None:
                return v
    elif isinstance(o, list):
        for v in o:
            r = _first(v, key)
            if r is not None:
                return r
    return None


def summary(doc: dict) -> dict:
    res = doc.get("result") or {}
    r27 = (res.get("r27") or {}).get("0") or {}
    out = {"outcome": doc.get("outcome"), "status_written": doc.get("status_written")}
    for k in SUMMARY_KEYS:
        out[k] = _first(res.get("verdict") if k in ("survives", "primary_status", "reading") and res.get("verdict")
                        else res, k)
    out["r27_reading"] = r27.get("reading")
    out["r27_labels"] = r27.get("labels")
    return out


def _load(p: Path) -> dict | None:
    if not p.is_file():
        return None
    return json.loads(p.read_bytes().decode("utf-8"))


def canon_doc(d: dict) -> dict:
    """The whole row document minus the run-header keys and VOLATILE fields (B2)."""
    d = {k: v for k, v in d.items() if k not in RUN_HEADER}
    # asdg-skeptic C9: row_provenance is VOLATILE as a whole (timings, host), but its seeds and input hashes are
    # compared (a different seed or input is a different computation)
    rp = d.get("row_provenance")
    if isinstance(rp, dict):
        d["row_provenance_compared"] = {"seeds": rp.get("seeds"), "input_hashes": rp.get("input_hashes")}
    if isinstance(d.get("run_identity"), dict):
        d["run_identity"] = {k: v for k, v in d["run_identity"].items() if k not in RUN_IDENTITY_VOLATILE}
    return _canon(d)


def label_kind(path: str) -> str | None:
    for k, rx in LABEL_PATTERNS.items():
        if rx.match(path):
            return k
    return None


def expected_labels(manifest: dict | None) -> dict:
    """{(pass, row): {pattern names}} from the §17 analysis's machine-readable "label_only_expected"."""
    out = {}
    for e in (manifest or {}).get("label_only_expected", []):
        for r in e["rows"]:
            out.setdefault((e["pass"], int(r)), set()).add(e["pattern"])
    return out


def _row_of(name: str) -> int:
    return int(name.split("_")[1].split(".")[0])


def compare_dirs(old: Path, new: Path, manifest: dict | None = None) -> dict:
    rows, n_diff, n_missing, n_label, n_label_unexp = [], 0, 0, 0, 0
    expected = expected_labels(manifest)
    commits = {}
    for pass_ in PASSES:
        od, nd = Path(old) / pass_, Path(new) / pass_
        names = sorted({p.name for p in od.glob("row_*.json")} | {p.name for p in nd.glob("row_*.json")})
        for name in names:
            a, b = _load(od / name), _load(nd / name)
            ent = {"pass": pass_, "file": name}
            if a is None or b is None:
                ent.update(flag="MISSING in " + ("old" if a is None else "new"))
                n_missing += 1
                rows.append(ent)
                continue
            for tag, d in (("old", a), ("new", b)):
                ri = d.get("run_identity") or {}
                commits.setdefault(tag, set()).add((ri.get("run_commit"), ri.get("code_hash")))
            key = "reproduction" if name.endswith("_repro.json") else ("rlm" if name.endswith("_rlm.json") else "result")
            ca, cb = canon_doc(a), canon_doc(b)
            dp = diff_paths(ca, cb, limit=10 ** 6)
            ent.update(old=summary(a) if key == "result" else None, new=summary(b) if key == "result" else None,
                       equal=not dp, differing_fields=dp,
                       old_sha256=hashlib.sha256(json.dumps(ca, sort_keys=True).encode()).hexdigest(),
                       new_sha256=hashlib.sha256(json.dumps(cb, sort_keys=True).encode()).hexdigest())
            if dp:
                kinds = [label_kind(f) for f in dp]
                if all(kinds):
                    ok = name.count("_") == 1 and set(kinds) <= expected.get((pass_, _row_of(name)), set())
                    ent["flag"] = "LABEL ONLY (expected)" if ok else "LABEL ONLY (not expected)"
                    ent["label_kinds"] = sorted(set(kinds))
                    n_label += int(ok)
                    n_label_unexp += int(not ok)
                else:
                    ent["flag"] = "DIFFERS"
                    n_diff += 1
                ent["differing_fields"] = dp[:200]
                ent["n_differing_fields"] = len(dp)
            rows.append(ent)
    return {"what": "RUN_PLAN §17 (4): old vs new per completed row (a1_audit.s17_compare)",
            "old": str(old), "new": str(new), "volatile_fields_removed": sorted(VOLATILE),
            "runs": {k: sorted([list(x) for x in v], key=str) for k, v in commits.items()},
            "n_files": len(rows), "n_differing": n_diff, "n_label_only_expected": n_label,
            "n_label_only_not_expected": n_label_unexp, "n_missing": n_missing,
            "run_header_removed": sorted(RUN_HEADER), "label_patterns": {k: v.pattern for k, v in LABEL_PATTERNS.items()},
            "exit": 2 if n_missing else (1 if (n_diff or n_label_unexp) else 0),
            "flagged": [r for r in rows if r.get("flag")], "rows": rows}


def write_md(doc: dict, path: Path) -> None:
    lines = ["# §17 old vs new (GENERATED by a1_audit.s17_compare; do not hand-edit)", "",
             f"old `{doc['old']}`; new `{doc['new']}`; files {doc['n_files']}; differing {doc['n_differing']}; "
             f"label-only expected {doc['n_label_only_expected']}, not expected {doc['n_label_only_not_expected']}; "
             f"missing {doc['n_missing']}; exit {doc['exit']}", "", "| pass | file | outcome old / new | T old / new | conjunction p old / new |"
             " survives old / new | R27 reading equal | flag |", "|---|---|---|---|---|---|---|---|"]
    for r in doc["rows"]:
        o, n = r.get("old") or {}, r.get("new") or {}
        lines.append(f"| {r['pass']} | {r['file']} | {o.get('outcome')} / {n.get('outcome')} | {o.get('T')} / "
                     f"{n.get('T')} | {o.get('conjunction_p')} / {n.get('conjunction_p')} | {o.get('survives')} / "
                     f"{n.get('survives')} | {o.get('r27_reading') == n.get('r27_reading')} | {r.get('flag', '')} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", default=None, help="the §17 analysis (its sha256 is recorded)")
    a = ap.parse_args(argv)
    man = json.loads(Path(a.manifest).read_bytes().decode("utf-8")) if a.manifest else None
    doc = compare_dirs(Path(a.old), Path(a.new), man)
    if a.manifest:
        doc["s17_analysis_sha256"] = hashlib.sha256(Path(a.manifest).read_bytes()).hexdigest()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(doc, indent=1, ensure_ascii=True) + "\n").encode("utf-8")
    out.write_bytes(data)
    if out.read_bytes() != data:
        raise OSError("read-back")
    write_md(doc, out.with_suffix(".md"))
    print(f"s17_compare: files {doc['n_files']}; differing {doc['n_differing']}; label-only expected "
          f"{doc['n_label_only_expected']}, not expected {doc['n_label_only_not_expected']}; missing {doc['n_missing']}")
    return doc["exit"]


if __name__ == "__main__":
    sys.exit(main())
