"""Completeness check of an OFFICIAL WP2 plant battery's outputs (WP2 review finding B3).

    python -X utf8 -m a1_audit.plants_official_check [--root <main repo>/arcs/audit/run_manifests/plants] [--out PATH]

Why. plants.driver.Invocation.write_plant returns exit code 1 only when a criterion FAILs; a criterion left "not
evaluated" (a cell run below its §7 n) or a plant that never wrote its file does not change the driver's exit code.
That exit-code fix is DEFERRED: driver.py is pinned by blob (RUN_PLAN_amend_2 §8.1, b217a14d...; the only change
allowed after the pin is §8.1b's constants block), so it is not edited here. This checker is the stand-in: it reads
the official run's plant_<id>.json files and fails unless every plant is complete.

A plant passes iff:
  1. <root>/<id>/plant_<id>.json exists for every id of plants.driver.ORDER (P3a ... P26) and names that plant;
  2. its mode is "OFFICIAL" and it carries no DEV stamp;
  3. no criterion anywhere in it reads "not evaluated": outcome.n_not_evaluated == 0, and an independent walk of the
     cell summaries (base.PlantSpec.finish's rule: keys 'criterion' / 'criteria' at any depth) finds none either and
     finds the same number of criteria as outcome.n_criteria; every criterion's result is one of PASS / FAIL / CAUGHT /
     NOT CAUGHT / reported (none unclassified), and the plant has at least one criterion;
  4. every cell ran its official n (n_run == n_official);
  5. its cases file exists, its sha256 equals cases_file.sha256 and its line count equals cases_file.n;
  6. its header's plant_constants.values equal plants.driver.PINNED_CONSTANTS (RUN_PLAN_amend_2 §8.1b, by value).
FAIL / NOT CAUGHT criteria are outcomes, not completeness failures: they are counted and printed, never decided here.

Writes nothing unless --out is given (then UTF-8 / LF JSON, read back, rule 8). Exit 0: every plant complete; 1: any
plant missing or incomplete; 2: refused (bad arguments).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from . import plants_dev_compare as DC

RESULT_PREFIXES = ("PASS", "FAIL", "CAUGHT", "NOT CAUGHT", "not evaluated", "reported")


def walk_criteria(cells: dict) -> list:
    """(where, criterion) for every criterion record in the cell summaries (base.PlantSpec.finish's walk)."""
    found = []

    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "criterion" and isinstance(v, dict) and "result" in v:
                    found.append((" / ".join(path), v))
                elif k == "criteria" and isinstance(v, dict):
                    for kk, vv in v.items():
                        if isinstance(vv, dict) and "result" in vv:
                            found.append((" / ".join(path + [kk]), vv))
                else:
                    walk(v, path + [k])
    for name, s in cells.items():
        walk(s, [name])
    return found


def classify(result: str) -> str | None:
    r = str(result)
    if r.startswith("NOT CAUGHT"):
        return "NOT CAUGHT"
    for p in RESULT_PREFIXES:
        if r.startswith(p):
            return p
    return None


def check_plant(root: Path, pid: str, pinned: dict) -> dict:
    f = Path(root) / pid / f"plant_{pid}.json"
    out = dict(plant=pid, file=f.as_posix(), problems=[])
    P = out["problems"]
    if not f.is_file():
        P.append("missing: no plant file")
        return out
    try:
        doc = json.loads(f.read_bytes().decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        P.append(f"unreadable plant file ({type(e).__name__})")
        return out
    if (doc.get("plant") or {}).get("id") != pid:
        P.append(f"plant file names {(doc.get('plant') or {}).get('id')!r}")
    if doc.get("mode") != "OFFICIAL" or doc.get("stamp") is not None:
        P.append(f"not an official run (mode {doc.get('mode')!r}, stamp {str(doc.get('stamp'))[:40]!r})")
    oc = doc.get("outcome") or {}
    cells = doc.get("cells") or {}
    found = walk_criteria(cells)
    kinds = [classify(c["result"]) for _, c in found]
    n_ne = sum(k == "not evaluated" for k in kinds)
    out["counts"] = {k: sum(x == k for x in kinds) for k in RESULT_PREFIXES}
    out["outcome"] = {k: v for k, v in oc.items() if k != "criteria"}
    if oc.get("n_not_evaluated") != 0:
        P.append(f"outcome.n_not_evaluated = {oc.get('n_not_evaluated')!r}")
    if n_ne:
        P.append(f"{n_ne} criterion / criteria 'not evaluated' in the cell summaries: "
                 f"{[w for (w, _), k in zip(found, kinds) if k == 'not evaluated'][:5]}")
    if not found:
        P.append("no criterion in the cell summaries")
    if oc.get("n_criteria") != len(found):
        P.append(f"outcome.n_criteria {oc.get('n_criteria')!r} != {len(found)} found in the cells")
    if any(k is None for k in kinds):
        P.append(f"unclassified criterion result(s): {[c['result'][:40] for (_, c), k in zip(found, kinds) if k is None]}")
    short = {name: (c.get("n_run"), c.get("n_official")) for name, c in cells.items()
             if c.get("n_run") is None or c.get("n_run") != c.get("n_official")}
    if not cells:
        P.append("no cell summaries")
    if short:
        P.append(f"cells not at their official n (n_run, n_official): {short}")
    cf = doc.get("cases_file") or {}
    cpath = f.parent / str(cf.get("name"))
    if not cf.get("name") or not cpath.is_file():
        P.append("cases file missing")
    else:
        data = cpath.read_bytes()
        if hashlib.sha256(data).hexdigest() != cf.get("sha256"):
            P.append("cases file sha256 differs from the header's")
        n_lines = len(data.decode("utf-8").splitlines())
        if n_lines != cf.get("n"):
            P.append(f"cases file has {n_lines} line(s), header says {cf.get('n')!r}")
    pc = (doc.get("plant_constants") or {}).get("values")
    canon = lambda o: json.dumps(o, sort_keys=True)  # noqa: E731
    if pc is None:
        P.append("no plant_constants in the header (RUN_PLAN_amend_2 §8.1b)")
    else:
        bad = [k for k in pinned if canon(pc.get(k)) != canon(pinned[k])] + [k for k in pc if k not in pinned]
        if bad:
            P.append(f"plant_constants differ from §8.1b's pinned values: {bad}")
    return out


def check(root: Path, order: tuple | None = None, pinned: dict | None = None) -> dict:
    if order is None or pinned is None:
        from .plants import driver as D
        order = D.ORDER if order is None else order
        pinned = D.PINNED_CONSTANTS if pinned is None else pinned
    root = Path(root)
    plants = [check_plant(root, pid, pinned) for pid in order]
    bad = [p["plant"] for p in plants if p["problems"]]
    tot = {k: sum((p.get("counts") or {}).get(k, 0) for p in plants) for k in RESULT_PREFIXES}
    return dict(what="completeness check of an official WP2 plant battery (WP2 review B3)", root=root.as_posix(),
                order=list(order), plants=plants, incomplete=bad, criteria_totals=tot,
                result="every plant complete" if not bad else f"incomplete: {bad}",
                driver_exit_code_note="plants.driver exits 1 only on FAIL, never on 'not evaluated' or a missing plant; "
                                      "the fix is deferred (driver.py pinned, RUN_PLAN_amend_2 §8.1 / §8.1b)")


def build_parser():
    ap = argparse.ArgumentParser(prog="python -m a1_audit.plants_official_check", description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=str(DC.REPO / DC.PLANTS_REL), help="the official plants directory")
    ap.add_argument("--out", default=None, help="write the check as JSON here (read back)")
    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    root = Path(a.root)
    if not root.is_dir():
        print(DC.ascii_line(f"plants_official_check: refused: not a directory: {root}"), flush=True)
        return 2
    doc = check(root)
    for p in doc["plants"]:
        c = p.get("counts") or {}
        print(DC.ascii_line(f"{p['plant']}: {'complete' if not p['problems'] else 'INCOMPLETE'}; criteria "
                            f"{json.dumps(c)}" + ("" if not p["problems"] else f"; {'; '.join(p['problems'])}")),
              flush=True)
    print(DC.ascii_line(f"plants_official_check: {doc['result']}; totals {json.dumps(doc['criteria_totals'])}"),
          flush=True)
    if a.out:
        sha = DC.write_report(Path(a.out), doc)
        print(DC.ascii_line(f"plants_official_check: wrote {a.out} sha256 {sha[:16]}"), flush=True)
    return 0 if not doc["incomplete"] else 1


if __name__ == "__main__":
    sys.exit(main())
