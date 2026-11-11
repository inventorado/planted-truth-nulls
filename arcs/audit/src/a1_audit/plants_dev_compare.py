"""DEV-vs-OFFICIAL comparison of the WP2 plant case records (RUN_PLAN_amend_2.md v2.1, FROZEN acdb1290..., §8.2
:533-537: "DEV keys are the official keys ... the DEV records are the outcomes of the first official cases ... The
official battery recomputes those cases, and any difference from the DEV record is reported").

    python -X utf8 -m a1_audit.plants_dev_compare --dev DIR[,DIR...] --official DIR [--plants P24,P25] [--commit SHA]
           [--out PATH]

- --dev: DEV output directories (the plants driver's --dev --out DIRs: dev1 ... dev4), each holding
  <plant>/cases_<plant>.jsonl.
- --official: an official run's plant directory (arcs/audit/run_manifests/plants of the main repository), the same
  layout. Only the cases files are read, plus each plant_<id>.json's mode and run commit (for the report's header).
- --out: the JSON report; default arcs/audit/run_manifests/plants/DEV_vs_OFFICIAL_<commit>.json in this repository
  (commit: --commit, else the official plant headers' provenance.run_commit).

Rule. Records are matched on (plant, cell, case) - the case number the driver records (spec.case_of; P24 / P25: the map
case; P3b: 1000 + i), unique within a cell (asserted on both sides). Every recorded field is compared except the
per-process ones (VOLATILE: wall / CPU seconds, start / finish times, worker pid, peak working set and the memory flag
derived from it): every per-case decision (booleans, statuses), every p and every other number, and the recorded seed
keys (the `seeds` records: construction and leg entropies, integer site seeds). A record is flattened to leaf paths
(dict keys joined by '/', list items by index; a list of scalars is one leaf); values are compared exactly (JSON
equality; NaN equals NaN), and a numeric difference carries |dev - official| and whether it is within 1e-12 relative
(REL_TOL: floating-point noise, e.g. a share computed through BLAS in another process; reported like every other
difference, and counted apart from the material ones). Each difference is reported with its
plant, cell, case, i, field path, category (seed key / decision / p / number / other), the DEV value, the official
value and the DEV pass it came from; a field present on one side only is a difference (value "<absent>"). A DEV
record with no official record of the same (plant, cell, case) is listed as DEV-only (not a difference: the official
cases file holds the cases the official run used), and a plant whose official cases file is missing is flagged.
The DEV passes are also compared among themselves on the cases they share (they must agree: same keys, same code).

Writes the report once (UTF-8, LF), reads it back and compares (rule 8). Exit 0 when no difference, 1 when any
difference or a missing official cases file, 2 on a refusal (bad arguments, malformed input).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PLANTS_REL = "arcs/audit/run_manifests/plants"
SPEC = "RUN_PLAN_amend_2.md v2.1 (FROZEN acdb1290...) §8.2 :533-537"
VOLATILE = ("started", "finished", "seconds", "cpu_seconds", "peak_working_set_bytes", "pid", "memory_defect")
ABSENT = "<absent>"
KEY_FIELDS = ("plant", "cell", "case", "i", "status")
PLANT_RE = re.compile(r"P[0-9]+[a-z]?")
CATEGORIES = ("seed key", "decision", "p", "number", "other")
REL_TOL = 1e-12


class Refused(Exception):
    pass


# ---- reading ---------------------------------------------------------------------------------------------------------
def plant_order(pid: str) -> tuple:
    m = re.fullmatch(r"P([0-9]+)([a-z]?)", pid)
    return (int(m.group(1)), m.group(2)) if m else (10 ** 9, pid)


def plants_in(d: Path) -> list[str]:
    """Plant ids with a cases file under d (<pid>/cases_<pid>.jsonl)."""
    out = [p.name for p in Path(d).iterdir() if p.is_dir() and PLANT_RE.fullmatch(p.name)
           and (p / f"cases_{p.name}.jsonl").is_file()]
    return sorted(out, key=plant_order)


def load_cases(path: Path, pid: str) -> dict:
    """{(cell, case): record} of one cases file; asserts every line parses, names this plant, carries the key fields,
    and that (cell, case) is unique."""
    out = {}
    text = Path(path).read_bytes().decode("utf-8")
    for n, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            raise Refused(f"{path}: empty line {n}")
        r = json.loads(line)
        missing = [k for k in KEY_FIELDS if k not in r]
        if missing:
            raise Refused(f"{path}: line {n} lacks {missing}")
        if r["plant"] != pid:
            raise Refused(f"{path}: line {n} is a record of {r['plant']!r}, not {pid!r}")
        key = (str(r["cell"]), int(r["case"]))
        if key in out:
            raise Refused(f"{path}: (cell, case) {key} twice")
        out[key] = r
    return out


def plant_header(d: Path, pid: str) -> dict:
    """mode / run commit / stamp of <d>/<pid>/plant_<pid>.json (None values if the file is absent)."""
    f = Path(d) / pid / f"plant_{pid}.json"
    if not f.is_file():
        return dict(mode=None, run_commit=None, stamp=None)
    doc = json.loads(f.read_bytes().decode("utf-8"))
    return dict(mode=doc.get("mode"), run_commit=(doc.get("provenance") or {}).get("run_commit"),
                stamp=doc.get("stamp"))


# ---- flattening and comparing ----------------------------------------------------------------------------------------
def _scalar(v) -> bool:
    return v is None or isinstance(v, (bool, int, float, str))


def flatten(o, prefix: str = "") -> dict:
    """Leaf paths of a JSON value: dict keys joined by '/', list items by index; a list of scalars is one leaf."""
    out = {}
    if isinstance(o, dict):
        if not o and prefix:
            out[prefix] = {}
        for k, v in o.items():
            out.update(flatten(v, f"{prefix}/{k}" if prefix else str(k)))
    elif isinstance(o, list) and not all(_scalar(v) for v in o):
        for j, v in enumerate(o):
            out.update(flatten(v, f"{prefix}/{j}"))
    else:
        out[prefix] = o
    return out


def same(a, b) -> bool:
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        return True
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def category(path: str, v) -> str:
    parts = path.split("/")
    if any(p in ("seeds", "site_seeds", "construction_key", "keys_common") for p in parts):
        return "seed key"
    if isinstance(v, (bool, str)):
        return "decision"
    last = parts[-1]
    if isinstance(v, (int, float)) and (last in ("+", "-", "p") or last.startswith("p_") or
                                        any(p == "p" or p.startswith("p_") for p in parts)):
        return "p"
    if isinstance(v, (int, float)):
        return "number"
    return "other"


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def compare_records(dev: dict, off: dict) -> list[dict]:
    """The differences of one DEV record from the official record (VOLATILE fields left out)."""
    a = flatten({k: v for k, v in dev.items() if k not in VOLATILE})
    b = flatten({k: v for k, v in off.items() if k not in VOLATILE})
    out = []
    for path in sorted(set(a) | set(b)):
        va, vb = a.get(path, ABSENT), b.get(path, ABSENT)
        if path in a and path in b and same(va, vb):
            continue
        d = dict(field=path, category=category(path, vb if va is ABSENT else va), dev=va, official=vb)
        if _num(va) and _num(vb):
            d["abs_diff"] = abs(float(va) - float(vb))
            d["within_rel_1e-12"] = d["abs_diff"] <= REL_TOL * max(1.0, abs(float(va)), abs(float(vb)))
        else:
            d["within_rel_1e-12"] = False
        out.append(d)
    return out


def compare(dev_dirs: list, official_dir: Path, plants: list | None = None) -> dict:
    dev_dirs = [Path(d) for d in dev_dirs]
    names = [d.name for d in dev_dirs]
    if len(set(names)) != len(names):
        raise Refused(f"DEV directories must have distinct names: {names}")
    official_dir = Path(official_dir)
    for d in dev_dirs + [official_dir]:
        if not d.is_dir():
            raise Refused(f"not a directory: {d}")
    found = sorted({p for d in dev_dirs for p in plants_in(d)}, key=plant_order)
    if plants:
        bad = [p for p in plants if not PLANT_RE.fullmatch(p)]
        if bad:
            raise Refused(f"plant ids {bad}")
        found = [p for p in found if p in plants]
    rep_plants, totals = {}, dict(dev_records=0, compared=0, dev_only=0, differences=0, records_with_differences=0,
                                  differences_within_rel_1e_12=0, differences_material=0)
    by_cat = {c: 0 for c in CATEGORIES}
    headers = {}
    for pid in found:
        devs = {}
        for d in dev_dirs:
            f = d / pid / f"cases_{pid}.jsonl"
            if f.is_file():
                devs[d.name] = load_cases(f, pid)
        off_file = official_dir / pid / f"cases_{pid}.jsonl"
        off = load_cases(off_file, pid) if off_file.is_file() else None
        headers[pid] = dict(official=plant_header(official_dir, pid),
                            dev={d.name: plant_header(d, pid) for d in dev_dirs if (d / pid).is_dir()})
        # the DEV passes among themselves (same keys, same code: they must agree)
        dev_disagree = []
        passes = sorted(devs)
        for x in range(len(passes)):
            for y in range(x + 1, len(passes)):
                A, B = devs[passes[x]], devs[passes[y]]
                for key in sorted(set(A) & set(B)):
                    for diff in compare_records(A[key], B[key]):
                        dev_disagree.append(dict(dev_a=passes[x], dev_b=passes[y], cell=key[0], case=key[1], **{
                            k: v for k, v in diff.items() if k not in ("dev", "official")}, value_a=diff["dev"],
                            value_b=diff["official"]))
        diffs, dev_only, n_dev, n_cmp, recs_diff = [], [], 0, 0, 0
        for src in passes:
            for key, r in sorted(devs[src].items()):
                n_dev += 1
                if off is None or key not in off:
                    dev_only.append(dict(dev_source=src, cell=key[0], case=key[1], i=r["i"]))
                    continue
                n_cmp += 1
                dd = compare_records(r, off[key])
                if dd:
                    recs_diff += 1
                for d in dd:
                    diffs.append(dict(dev_source=src, cell=key[0], case=key[1], i=r["i"], **d))
                    by_cat[d["category"]] += 1
        rep_plants[pid] = dict(dev_records=n_dev, dev_passes={p: len(devs[p]) for p in passes},
                               official_cases_file=off_file.as_posix() if off is not None else None,
                               official_missing=off is None, official_records=None if off is None else len(off),
                               compared=n_cmp, dev_only=dev_only, n_dev_only=len(dev_only),
                               records_with_differences=recs_diff, n_differences=len(diffs), differences=diffs,
                               dev_passes_disagree=dev_disagree, n_dev_passes_disagree=len(dev_disagree))
        totals["dev_records"] += n_dev
        totals["compared"] += n_cmp
        totals["dev_only"] += len(dev_only)
        totals["differences"] += len(diffs)
        totals["records_with_differences"] += recs_diff
        totals["differences_within_rel_1e_12"] += sum(bool(d["within_rel_1e-12"]) for d in diffs)
        totals["differences_material"] += sum(not d["within_rel_1e-12"] for d in diffs)
    missing = [p for p, v in rep_plants.items() if v["official_missing"]]
    n_dis = sum(v["n_dev_passes_disagree"] for v in rep_plants.values())
    return dict(what="DEV vs OFFICIAL plant case records (RUN_PLAN_amend_2 §8.2: any difference from the DEV record is "
                     "reported)", spec=SPEC, rule=__doc__.split("Rule. ")[1].split("\n\nWrites")[0].replace("\n", " "),
                dev_dirs=[d.as_posix() for d in dev_dirs], official_dir=official_dir.as_posix(), plants=found,
                excluded_fields=list(VOLATILE), headers=headers, totals=totals, differences_by_category=by_cat,
                plants_official_missing=missing, n_dev_passes_disagree=n_dis,
                result=("no difference" if not totals["differences"] and not missing and not n_dis else
                        f"{totals['differences']} difference(s) ({totals['differences_material']} material, "
                        f"{totals['differences_within_rel_1e_12']} within 1e-12 relative) in "
                        f"{totals['records_with_differences']} record(s); "
                        f"official cases missing for {missing or 'none'}; DEV passes disagree in {n_dis} field(s)"),
                by_plant=rep_plants)


# ---- writing -----------------------------------------------------------------------------------------------------------
def write_report(path: Path, doc: dict) -> str:
    """UTF-8 / LF JSON, written to a tmp file and replaced, read back and compared (rule 8)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=False) + "\n").encode("utf-8")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    back = path.read_bytes()
    if back != data or json.loads(back.decode("utf-8")) != json.loads(data.decode("utf-8")):
        raise RuntimeError(f"read-back of {path.name} differs")
    return hashlib.sha256(back).hexdigest()


def default_out(commit: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{7,40}|unknown", commit):
        raise Refused(f"commit {commit!r}")
    return REPO / PLANTS_REL / f"DEV_vs_OFFICIAL_{commit}.json"


def build_parser():
    ap = argparse.ArgumentParser(prog="python -m a1_audit.plants_dev_compare", description=__doc__.split("\n")[0])
    ap.add_argument("--dev", required=True, help="DEV output directories, comma-separated")
    ap.add_argument("--official", required=True, help="the official run's plants directory")
    ap.add_argument("--plants", default=None, help="only these plant ids (comma-separated)")
    ap.add_argument("--commit", default=None, help="the official run commit (default: from the plant headers)")
    ap.add_argument("--out", default=None, help="the report (default run_manifests/plants/DEV_vs_OFFICIAL_<commit>.json)")
    return ap


def ascii_line(s: str) -> str:
    return s.encode("ascii", "replace").decode("ascii")


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    try:
        dev = [Path(t.strip()) for t in a.dev.split(",") if t.strip()]
        plants = [t.strip() for t in a.plants.split(",") if t.strip()] if a.plants else None
        doc = compare(dev, Path(a.official), plants)
        commit = a.commit
        if commit is None:
            commits = {h["official"]["run_commit"] for h in doc["headers"].values() if h["official"]["run_commit"]}
            if len(commits) > 1:
                raise Refused(f"official plant headers carry different run commits: {sorted(commits)}")
            commit = commits.pop() if commits else "unknown"
        doc["commit"] = commit
        out = Path(a.out) if a.out else default_out(commit)
        if out.name.startswith("cases_") or out.name.startswith("plant_"):
            raise Refused("--out must not name a plant output file")
    except (Refused, ValueError, OSError) as e:
        print(ascii_line(f"plants_dev_compare: refused: {e}"), flush=True)
        return 2
    sha = write_report(out, doc)
    t = doc["totals"]
    print(ascii_line(f"plants_dev_compare: {len(doc['plants'])} plant(s); DEV records {t['dev_records']}, compared "
                     f"{t['compared']}, DEV-only {t['dev_only']}; differences {t['differences']} (material "
                     f"{t['differences_material']}, within 1e-12 relative {t['differences_within_rel_1e_12']}) in "
                     f"{t['records_with_differences']} record(s) {doc['differences_by_category']}; official missing "
                     f"{doc['plants_official_missing']}; DEV passes disagree {doc['n_dev_passes_disagree']}"), flush=True)
    for pid, v in doc["by_plant"].items():
        print(ascii_line(f"  {pid}: compared {v['compared']}, differences {v['n_differences']}"), flush=True)
    print(ascii_line(f"plants_dev_compare: wrote {out} sha256 {sha[:16]}"), flush=True)
    return 0 if doc["result"] == "no difference" else 1


if __name__ == "__main__":
    sys.exit(main())
