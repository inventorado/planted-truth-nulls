"""P25 (a) re-scored "as frozen": the v2 species max with degenerate G6l windows scored (WP2 review finding B1).

    python -X utf8 -m a1_audit.plants_p25a_rescore --cases <dir>/P25/cases_P25.jsonl [--recompute needed|all|none]
           [--limit N] [--cells SUBSTR] [--commit SHA] [--out PATH]

The finding. The plant's flawed leg (a) (plants/flaws.py:79, v2_species_max) scores the claim's own G6l windows only
when the claim's G6l status is "ok"; a "degenerate" pool (mean pairwise Jaccard >= .5) gets no G6l p, so the v2 max has
no p and the case is a non-rejection. The frozen reference leg scores degenerate windows: e3_align_plants.py:162 passes
`info.get("sets")` ("None if unmatched; the v2 draft had no pool-diversity rule, so degenerate pools stay"), and
asdg.species.WithinClassBasis.v2_species (src/asdg/species.py:267-271) returns NaN only when there are no windows
(sets None: unmatched). Re-scoring "as frozen" changes only that gate: a G6l p whenever windows exist.

What the case records hold (determined from the record format, p25.py:242-247, p24.species_record):
- G6l "ok": the plant and the frozen gate score the same windows -> the recorded (a) IS the frozen (a) (no change);
- G6l "unmatched" (no windows, R8 included): the frozen leg is NaN too -> non-rejection (no change);
- G6l "degenerate": the record holds the v2 G1 (whole) and G6s (centred on mu^w) p's but NOT the degenerate windows'
  unconditioned p (recorded None). Since p_max = max(G1, G6s, G6l) >= max(G1, G6s), a case with max(G1, G6s) p(+) >=
  .025 is a frozen non-rejection DECIDED FROM THE RECORD; a case with max(G1, G6s) p(+) < .025 needs the windows' p,
  i.e. a RECOMPUTATION of the case from its plant seed keys.
So the records suffice except for degenerate cases with max(G1, G6s) p(+) < .025.

The recomputation (--recompute needed: only those cases; all: every (a)(b) case, a reproduction check). The case is
recomputed by the plant's own code, imported read-only: p25.P25.run_case(cell, i, K) with the plant K (§8.1b, asserted
by plants.driver.plant_constants), on the case's plant keys (the construction and leg keys are functions of (plant 25,
case, class id), seeds.py). During that call plants.flaws.v2_species_max is wrapped in memory (restored after): the
wrapper returns the plant's own result unchanged and, beside it, calls the same function on the same adapter, the
same windows and the same leg streams with the frozen gate (status "ok" whenever windows exist). The recomputed
record must equal the recorded one field for field (plants_dev_compare.compare_records, per-process fields left out):
every p, decision, status and seed key exactly; a continuous number (category "number", e.g. the uninformative share)
may differ within 1e-12 relative (floating-point noise of a fresh process: found on DEV case V-AAL i0, 6.7e-16 in
correct/uninformative_share) and is listed; any other difference refuses (the reconstruction is not the recorded
case). For a G6l "ok" case the frozen-gate p's must equal the plant's.

The result is reported BESIDE the official (a), never replacing it (RUN_PLAN.md §17; RUN_PLAN_amend_2 §8.1): per
(a)(b) cell, the recorded k (official), the frozen-gate k when every case is decided, else its bounds, and the §7
criterion (criteria.p25_flawed) evaluated on the frozen-gate k, labelled "beside". The report is written once
(UTF-8, LF) and read back (rule 8). Default --out: arcs/audit/run_manifests/plants/P25a_as_frozen_<commit>.json.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from . import plants_dev_compare as DC
from .plants import criteria as CR

ALPHA = 0.025               # alpha_v (prereg_amend_3.md:73); asserted equal to plants.common.ALPHA when recomputing
PLUS = "+"
V2_LEGS = ("G1 (whole, unconditioned)", "G6s (centred on mu^w)", "G6l (own windows, unconditioned)")
DRIVER_FIELDS = ("plant", "cell", "i", "case", "class_id", "plant_id")
BASIS_OK = "identical: G6l ok, the plant and the frozen gate score the same windows"
BASIS_UNMATCHED = "identical: G6l unmatched (no windows): the frozen leg is NaN too (non-rejection)"
BASIS_DECIDED = ("decided from the record: G6l degenerate, max(G1 whole, G6s centred) p(+) >= .025, so the frozen max "
                 "is >= .025 (non-rejection)")
BASIS_NEEDS = ("needs recomputation: G6l degenerate, max(G1 whole, G6s centred) p(+) < .025; the frozen decision rests "
               "on the degenerate windows' p, which the record does not hold")
BASIS_RECOMPUTED = "recomputed from the case's plant keys (frozen gate: degenerate windows scored)"
BESIDE = ("reported BESIDE the official P25 (a), never replacing it (RUN_PLAN.md §17; RUN_PLAN_amend_2 §8.1: the "
          "plant rule is pinned)")


class Refused(Exception):
    pass


def _below(p) -> bool:
    return p is not None and p.get(PLUS) is not None and p[PLUS] < ALPHA


def _pmax(ps: list) -> dict | None:
    if any(p is None for p in ps):
        return None
    return {d: max(p[d] for p in ps) for d in ("+", "-")}


# ---- from the records ------------------------------------------------------------------------------------------------
def rescore_record(r: dict) -> dict:
    """One (a)(b) case record -> its frozen-gate decision where the record decides it (module docstring). Asserts the
    record's own consistency first (the plant rule re-derived from its p's)."""
    if r.get("plant") != "P25" or r.get("part") != "ab" or r.get("status") != "computed":
        raise Refused(f"not a computed P25 (a)(b) record: {r.get('plant')} {r.get('part')} {r.get('status')}")
    st = r["correct"]["g6l"]["status"]
    v2 = r["v2"]
    ps = [v2["p"][k] for k in V2_LEGS]
    if (st == "ok") != (ps[2] is not None):
        raise Refused(f"case {r['cell']} i={r['i']}: G6l status {st!r} disagrees with the recorded v2 G6l p")
    if v2["p_max"] != _pmax(ps) or bool(v2["rejects"]) != _below(v2["p_max"]):
        raise Refused(f"case {r['cell']} i={r['i']}: the recorded v2 max / decision is not the plant rule on its p's")
    head = dict(cell=r["cell"], i=int(r["i"]), case=int(r["case"]), g6l_status=st,
                pool_jaccard=r["correct"]["g6l"].get("pool_jaccard"), official_rejects=bool(v2["rejects"]),
                official_p_max_plus=None if v2["p_max"] is None else v2["p_max"][PLUS])
    if st == "ok":
        return dict(head, basis=BASIS_OK, frozen_rejects=bool(v2["rejects"]), frozen_p_max_plus=v2["p_max"][PLUS])
    if st == "unmatched":
        return dict(head, basis=BASIS_UNMATCHED, frozen_rejects=False, frozen_p_max_plus=None)
    if st == "degenerate":
        lb = max(ps[0][PLUS], ps[1][PLUS])
        if lb >= ALPHA:
            return dict(head, basis=BASIS_DECIDED, frozen_rejects=False, frozen_p_max_plus_lower_bound=lb)
        return dict(head, basis=BASIS_NEEDS, frozen_rejects=None, frozen_p_max_plus_lower_bound=lb)
    raise Refused(f"case {r['cell']} i={r['i']}: unknown G6l status {st!r}")


def load_ab(path: Path, cells: str | None = None) -> list:
    rows = DC.load_cases(path, "P25")
    out = [r for (cell, _), r in sorted(rows.items(), key=lambda kv: (kv[0][0], kv[1]["i"]))
           if r.get("part") == "ab" and (cells is None or cells in cell)]
    if not out:
        raise Refused(f"{path}: no P25 (a)(b) record")
    return out


# ---- recomputation ---------------------------------------------------------------------------------------------------
def plant_K() -> dict:
    """The driver's K for P25 (plants.driver.Invocation.K_for: run.PLANT_K with run.PLANT_K_OVERRIDES), after the §8.1b
    constants are asserted equal to their pinned values."""
    from . import run as R
    from .plants import common as C
    from .plants import driver as D
    D.plant_constants()
    if C.ALPHA != ALPHA:
        raise AssertionError("plants.common.ALPHA differs from this module's")
    return dict(C.K_PLANT, **(R.PLANT_K_OVERRIDES or {}).get("P25", {}))


def recompute(cell_name: str, i: int, K: dict | None = None) -> dict:
    """The case recomputed by p25.P25.run_case (module docstring) with the frozen-gate v2 max computed beside the
    plant's. Returns the recomputed record (jsonable), the frozen-gate p's and the seconds it took."""
    from . import a3_port as A3
    from .plants import common as C
    from .plants import driver as D
    from .plants import flaws as FL
    from .plants import p25
    spec = p25.PLANTS["P25"]
    cell = D.cell_of(spec, cell_name)
    if cell.get("part") != "ab":
        raise Refused(f"{cell_name}: not an (a)(b) cell")
    K = plant_K() if K is None else dict(K)
    orig = FL.v2_species_max
    seen = []

    def both(adapter, Kspecies, seed_of, g6l_sets, g6l_status):
        out = orig(adapter, Kspecies, seed_of, g6l_sets, g6l_status)
        frozen = orig(adapter, Kspecies, seed_of, g6l_sets, "ok" if g6l_sets is not None else "unmatched")
        seen.append(dict(plant=out, frozen=frozen, status=g6l_status, has_windows=g6l_sets is not None,
                         n_windows=None if g6l_sets is None else int(len(g6l_sets))))
        return out
    t0 = time.perf_counter()
    FL.v2_species_max = both
    try:
        rec = spec.run_case(cell, int(i), K)
    finally:
        FL.v2_species_max = orig
    secs = time.perf_counter() - t0
    if FL.v2_species_max is not orig or len(seen) != 1:
        raise AssertionError("the v2 wrapper was not called exactly once or not restored")
    s = seen[0]
    fp = {k: C.pdir(v) for k, v in s["frozen"]["p"].items()}
    rec = json.loads(json.dumps(A3.jsonable(rec), sort_keys=True))   # the form a cases file holds (C.write_jsonl)
    return dict(record=rec, frozen=dict(p=fp, p_max=C.pdir(s["frozen"]["p_max"]),
                                                     rejects=C.below(C.pdir(s["frozen"]["p_max"]))),
                plant_status=s["status"], has_windows=s["has_windows"], n_windows=s["n_windows"],
                seconds=round(secs, 3))


def check_reproduced(recorded: dict, rc: dict) -> tuple[list, list]:
    """The recomputed record against the recorded one (per-process and driver-added fields left out) -> (material
    differences, tolerated ones: category 'number' within 1e-12 relative)."""
    a = {k: v for k, v in recorded.items() if k not in DRIVER_FIELDS}
    diffs = DC.compare_records(a, rc["record"])
    tol = [d for d in diffs if d["category"] == "number" and d["within_rel_1e-12"]]
    return [d for d in diffs if d not in tol], tol


def rescore_recomputed(recorded: dict, rc: dict) -> dict:
    diffs, tol = check_reproduced(recorded, rc)
    if diffs:
        raise Refused(f"case {recorded['cell']} i={recorded['i']}: the recomputation differs from the record in "
                      f"{len(diffs)} field(s), first {diffs[0]['field']}")
    fr = rc["frozen"]
    st = recorded["correct"]["g6l"]["status"]
    if st == "ok" and (fr["p"] != recorded["v2"]["p"] or fr["p_max"] != recorded["v2"]["p_max"]):
        raise AssertionError(f"case {recorded['cell']} i={recorded['i']}: G6l ok but the frozen gate's p's differ")
    if (st == "unmatched") == rc["has_windows"]:
        raise AssertionError(f"case {recorded['cell']} i={recorded['i']}: status {st!r} with windows "
                             f"{rc['has_windows']}")
    return dict(frozen_rejects=bool(fr["rejects"]), frozen_p_max_plus=None if fr["p_max"] is None else fr["p_max"][PLUS],
                frozen_p_g6l_plus=(fr["p"]["G6l (own windows, unconditioned)"] or {}).get(PLUS),
                n_windows=rc["n_windows"], recompute_seconds=rc["seconds"],
                reproduced="every p, decision, status and seed key exactly; numbers within 1e-12 relative",
                tolerated_number_differences=[dict(field=d["field"], abs_diff=d["abs_diff"]) for d in tol])


# ---- the report ------------------------------------------------------------------------------------------------------
def rescore(path: Path, recompute_mode: str = "needed", limit: int | None = None, cells: str | None = None,
            K: dict | None = None) -> dict:
    if recompute_mode not in ("needed", "all", "none"):
        raise Refused(f"--recompute {recompute_mode!r}")
    recs = load_ab(path, cells)
    rows = [rescore_record(r) for r in recs]
    todo = [j for j, row in enumerate(rows) if recompute_mode == "all" or
            (recompute_mode == "needed" and row["frozen_rejects"] is None)]
    if limit is not None:
        todo = todo[: int(limit)]
    secs = []
    for j in todo:
        rc = recompute(recs[j]["cell"], recs[j]["i"], K)
        got = rescore_recomputed(recs[j], rc)
        if rows[j]["frozen_rejects"] is not None and got["frozen_rejects"] != rows[j]["frozen_rejects"]:
            raise AssertionError(f"case {recs[j]['cell']} i={recs[j]['i']}: recomputed frozen decision differs from "
                                 "the record-level one")
        rows[j] = dict(rows[j], **got, basis=rows[j]["basis"] if rows[j]["frozen_rejects"] is not None else
                       BASIS_RECOMPUTED, recomputed=True)
        secs.append(rc["seconds"])
    by_cell = {}
    for row in rows:
        c = by_cell.setdefault(row["cell"], dict(n=0, k_official=0, k_frozen_decided=0, n_undecided=0,
                                                 n_by_g6l_status={}, n_by_basis={}, n_recomputed=0,
                                                 n_decision_changed=0))
        c["n"] += 1
        c["k_official"] += row["official_rejects"]
        c["n_by_g6l_status"][row["g6l_status"]] = c["n_by_g6l_status"].get(row["g6l_status"], 0) + 1
        c["n_by_basis"][row["basis"]] = c["n_by_basis"].get(row["basis"], 0) + 1
        c["n_recomputed"] += bool(row.get("recomputed"))
        if row["frozen_rejects"] is None:
            c["n_undecided"] += 1
        else:
            c["k_frozen_decided"] += row["frozen_rejects"]
            c["n_decision_changed"] += row["frozen_rejects"] != row["official_rejects"]
    for name, c in by_cell.items():
        if c["n_undecided"]:
            c["k_frozen"] = None
            c["k_frozen_bounds"] = [c["k_frozen_decided"], c["k_frozen_decided"] + c["n_undecided"]]
            c["criterion_beside"] = dict(result=f"not decided ({c['n_undecided']} case(s) need recomputation)",
                                         kind=CR.MUST_CATCH)
        else:
            c["k_frozen"] = c["k_frozen_decided"]
            c["criterion_beside"] = CR.p25_flawed(c["k_frozen"], c["n"])
        c["official_criterion_recomputed_from_records"] = CR.p25_flawed(c["k_official"], c["n"])
        c["note"] = BESIDE
    n_und = sum(c["n_undecided"] for c in by_cell.values())
    mean_s = (sum(secs) / len(secs)) if secs else None
    return dict(what="P25 (a) v2 species max re-scored 'as frozen' (degenerate G6l windows scored; WP2 review B1)",
                beside=BESIDE, cases_file=Path(path).as_posix(), recompute=recompute_mode, limit=limit, cells=cells,
                rule=__doc__.split("\n\nThe finding. ")[1].split("\n\nThe result is reported")[0].replace("\n", " "),
                frozen_refs=["arcs/audit/src/e3_align_plants.py:162", "src/asdg/species.py:267-271"],
                plant_ref="arcs/audit/src/a1_audit/plants/flaws.py:79", by_cell=by_cell,
                n_cases=len(rows), n_undecided=n_und,
                cost=dict(n_recomputed=len(secs), seconds=secs, mean_seconds_per_case=mean_s,
                          estimated_seconds_for_undecided=None if mean_s is None else round(mean_s * n_und, 1),
                          note="single process (OMP_NUM_THREADS=1, run.py); wall seconds of P25.run_case plus one "
                               "extra v2 scoring per case"),
                cases=[row for row in rows if row["g6l_status"] != "ok" or row.get("recomputed")],
                n_cases_ok_not_listed=sum(1 for row in rows if row["g6l_status"] == "ok" and not row.get("recomputed")))


def build_parser():
    ap = argparse.ArgumentParser(prog="python -m a1_audit.plants_p25a_rescore", description=__doc__.split("\n")[0])
    ap.add_argument("--cases", required=True, help="a P25 cases file (cases_P25.jsonl)")
    ap.add_argument("--recompute", default="needed", choices=("needed", "all", "none"))
    ap.add_argument("--limit", type=int, default=None, help="recompute at most N cases (in case order)")
    ap.add_argument("--cells", default=None, help="only cells whose name contains this text")
    ap.add_argument("--commit", default=None, help="the run commit (default: the cases' plant_P25.json)")
    ap.add_argument("--out", default=None, help="default arcs/audit/run_manifests/plants/P25a_as_frozen_<commit>.json")
    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    try:
        cases = Path(a.cases)
        commit = a.commit or DC.plant_header(cases.parent.parent, "P25")["run_commit"] or "unknown"
        if not re.fullmatch(r"[0-9a-f]{7,40}|unknown", commit):
            raise Refused(f"commit {commit!r}")
        out = Path(a.out) if a.out else DC.REPO / DC.PLANTS_REL / f"P25a_as_frozen_{commit}.json"
        if out.name.startswith(("cases_", "plant_")):
            raise Refused("--out must not name a plant output file")
        doc = rescore(cases, a.recompute, a.limit, a.cells)
        doc["commit"] = commit
    except (Refused, ValueError, OSError) as e:
        print(DC.ascii_line(f"plants_p25a_rescore: refused: {e}"), flush=True)
        return 2
    sha = DC.write_report(out, doc)
    for name, c in doc["by_cell"].items():
        print(DC.ascii_line(f"{name}: n {c['n']}; official (a) k {c['k_official']}; as frozen k {c['k_frozen']} "
                            f"(undecided {c['n_undecided']}, recomputed {c['n_recomputed']}); statuses "
                            f"{c['n_by_g6l_status']}"), flush=True)
    cost = doc["cost"]
    print(DC.ascii_line(f"plants_p25a_rescore: recomputed {cost['n_recomputed']} case(s), mean "
                        f"{cost['mean_seconds_per_case']} s; wrote {out} sha256 {sha[:16]}"), flush=True)
    return 0 if not doc["n_undecided"] else 1


if __name__ == "__main__":
    sys.exit(main())
