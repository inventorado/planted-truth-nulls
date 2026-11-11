"""Tests of A1's results writer (a1_audit.report_cells; RUN_PLAN v3.1 §16, R1, R11, R26, R27, R29;
RUN_PLAN_amend_3 B6) on SYNTHETIC run outputs: a scratch results tree built here, record by record, in run.py's
writer schema (Run.header / write_row / _assemble_row / _write_repro / RUN_SUMMARY), with verdict records made by the
production verdict driver (verdict.assemble_verdict_a1 / descriptor_row_record on stub legs), descriptor legs by
descriptors._with_direction / level2_max, R27 blocks by reporting.r27_reading on a stub class, and reproduction checks
by reporting.reproduction_check. The frozen TSV / register are read (text only); no map, set, matrix or claim result is
opened, and nothing is written outside the scratch directory.

Checks (each a must-pass or a planted failure the writer must catch):
- full_tree: a complete synthetic verdict pass of every ungated row; descriptor / sensitivity absent -> "pass not run";
  the interim headline derived (0 of 14 can survive) and asserted against the register; outputs read back.
- missing_pass_rows: a pass that ran on a row subset (U-RC2) and a descriptor pass filling the descriptor legs and
  Liu's T; an incomplete pass refused by default, skipped (read "pass not run (pass incomplete ...)") on request.
- mixed_identities: another code hash / commit across passes, a row provenance naming another commit, a row edited
  after its RUN_SUMMARY, a DEV stamp, an incomplete pass of another run, a sensitivity record naming another verdict
  result: each refused.
- b6_comparators: comparator statuses (Liu SD7, Segura S6) never move the composition; a fail-closed CELL status in
  the row record does; a planted composition reading a comparator status is caught.
- forbidden_words: each forbidden word planted is caught; the generated headline passes; a planted headline is refused.
- r1_columns: 2 p(d*) and the literal 2 min side by side where they differ; planted p_reported / per-leg / conjunction
  edits refused.
- bh: q = statsmodels' fdr_bh; R29 membership (not in m, flagged not reproduced, status not ok -> p = 1, R8 not
  auditable outside, component p); the synthetic tree's family q's.
- register_and_interim: the TSV-derived numbers equal the R4 block; a planted block edit and a planted interim excess
  are refused.
- readback: a planted edit after writing is caught.
- sensitivity: "parcel set unchanged" vs a changed parcel set beside the primary.
- B1 (skeptic): the register's R4 interim composition asserted category by category, the at-use composition and the
  units that moved stated beside it; planted register / merged compositions refused.
- B2 (skeptic): run flags and the effective status at use from every pass's record (a sensitivity-only status
  included), consistent with headline.json's units; a planted composition flag the cell lacks refused.
- STATUS_RULES equal the modules' status constants (the WP4 / G2 run-time statuses included); a G2 run-time status
  outranks the register status at use (a text outside the rules does not); C3: component rows' R27 blocks marked not to be quoted.

Run (from arcs/audit/src):
  ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_report_cells [--scratch DIR]
Exits non-zero on any failure. Prints ASCII only.
"""
from __future__ import annotations

import argparse
import copy
import shutil
import json
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
for _p in (ROOT / "src", ROOT / "arcs" / "audit" / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

ap = argparse.ArgumentParser()
ap.add_argument("--scratch", default=None, help="scratch directory (default: a new temporary directory)")
ARGS, _ = ap.parse_known_args()
SCRATCH = Path(ARGS.scratch or tempfile.mkdtemp(prefix="a1_report_cells_")).resolve()
SCRATCH.mkdir(parents=True, exist_ok=True)
NO_DATA = SCRATCH / "no_such_data_dir"  # never created: an unpatched data read fails here
assert not NO_DATA.exists()

import e3_plants  # noqa: E402

e3_plants.GAMBA_CSV = NO_DATA / "gamba.csv"
e3_plants.AHBA = NO_DATA

import a1_audit.a3_port as A3  # noqa: E402
import a1_audit.descriptors as DS  # noqa: E402
import a1_audit.loader as LD  # noqa: E402
import a1_audit.report_cells as RC  # noqa: E402
import a1_audit.reporting as RPT  # noqa: E402
import a1_audit.run as RN  # noqa: E402
import a1_audit.verdict as V  # noqa: E402

A3.AHBA = NO_DATA
RESULTS: dict = {}
FAILED: list = []
CHECKS: list = []
REG = RC.Register(ROOT)
SCOPE = {"gradient_classes": ["V-AAL"], "n1_classes": ["V-AAL"]}


def check(name):
    def deco(fn):
        def run():
            t0 = time.time()
            try:
                measured = fn() or {}
                RESULTS[name] = dict(result="pass", seconds=round(time.time() - t0, 2), **measured)
                print(f"  pass  {name} ({time.time() - t0:.1f}s)", flush=True)
            except Exception as e:  # noqa: BLE001
                FAILED.append(name)
                RESULTS[name] = dict(result="FAIL", error=f"{type(e).__name__}: {e}"[:600],
                                     trace=traceback.format_exc()[-2000:])
                print(f"  FAIL  {name}: {type(e).__name__}: {str(e)[:300]}".encode("ascii", "replace").decode(),
                      flush=True)
        CHECKS.append(run)
        return fn
    return deco


def raises(exc, fn, *a, **kw) -> str:
    try:
        fn(*a, **kw)
    except exc as e:
        return str(e)
    raise AssertionError(f"{getattr(fn, '__name__', fn)} did not raise {exc.__name__}")


# ================================================================================================================
# synthetic run outputs in run.py's writer schema
# ================================================================================================================
K = {"site": 500, "species": 200, "permutation": 500, "sets": 200, "surr": 500, "j1_sets": 100}


def identity(commit="a" * 40, code_hash="b" * 64):
    return dict(run_commit=commit, code_hash=code_hash, K=dict(K), g6l_mode="exact",
                sources={"kind": "synthetic-report-test"}, seed_view=None)


def header(pass_, ident, gate="none"):
    return {"what": "A1 run result, one row x pass (RUN_PLAN v3.1 §16; provenance §2.4)", "stamp": None,
            "pass": pass_, "gate": gate, "plant": None, "K": dict(K), "g6l_mode": "exact", "K_plant_overrides": None,
            "g6l_mode_text": "exact", "threads": {}, "threads_before": {}, "run_identity": copy.deepcopy(ident),
            "output_root": "synthetic"}


def provenance(ident):
    return {"run_commit": ident["run_commit"], "code": {"modules": {}, "code_hash": ident["code_hash"]}}


def launch(ident, gate=None):
    return {"stamp": None, "launch_record": {
        "passed": True, "run_commit": ident["run_commit"], "repo_root": "synthetic", "files_root": None,
        "test_overrides": [], "gate": gate,
        "assertions": [{"id": "L2", "ok": True, "status": "pass", "observed": {"lf_sha256": LD.TSV_SHA256}},
                       {"id": "L15", "ok": True, "status": "pass" if gate else "not applicable"}]}}


def P(pp, pm):
    return {1: pp, -1: pm}


def full_legs(T, L0, site, species, form="decoded-list"):
    return dict(form=form, kind="full", T=T, K={"site": 500, "species": 200}, n_parcels=34,
                level0=dict(p=dict(L0), kind="parametric", floor=None),
                site={k: dict(p=dict(v), floor=1 / 501, seed=11 + i, K=500,
                              info=dict(exact=False, n_null=500, n_patterns=float("inf"), floor=1 / 501))
                      for i, (k, v) in enumerate(site.items())},
                species=dict(p={k: dict(v) for k, v in species.items()}, status={k: "ok" for k in species},
                             floors={k: 1 / 201 for k in species}, g6l=dict(status="ok"), g6s_exact=False, n_G6s=200,
                             K=200, conditioned=True, pools={}),
                uninformative=dict(flag=False, share=0.3))


def component_legs(T, L0, site):
    return dict(form="component (PLSRegression)", kind="component-permutation", T=T, K=dict(K), n_parcels=46,
                level0=dict(p=dict(L0), kind="permutation (leg 8)", floor=1 / 501, n_null=500, K=500),
                site={k: dict(p=dict(v), floor=1 / 501, seed=21 + i, K=500,
                              info=dict(exact=False, n_null=500, n_patterns=float("inf"), floor=1 / 501))
                      for i, (k, v) in enumerate(site.items())})


SPECIES_WEAK = {"G1": P(0.4, 0.6), "G3m": P(0.45, 0.55), "G6s": P(0.5, 0.5), "G6l": P(0.42, 0.58)}
SITE_WEAK = {"S1c": P(0.3, 0.7), "S2c": P(0.35, 0.65)}


class StubCtx:
    """reporting.r27_reading's class interface (reading_class / single_class) for a synthetic class."""
    def __init__(self, name, single=False):
        self.name, self.single = name, single

    def reading_class(self):
        return self.name

    def single_class(self):
        return self.single


def r27_block(m=70, survives=False, status="ok", cls="V-AAL", R2_grad=0.12, kind=None):
    desc = dict(R2_grad=R2_grad, R2_absx=0.08, m=m, f=int(m * 0.4), f_over_m=0.4, f_U=0.16, p_hypergeom=0.01,
                brain_enriched=False, r_yw_dB=-0.1, c_S=0.04)
    out = RPT.r27_reading({"status": status, "survives": survives}, desc, StubCtx(cls), scope=SCOPE)
    out["descriptors"] = desc
    out["reparcellated"] = False
    return out


def verdict_result(plan, verdict, r27=None):
    res = dict(verdict=RN.verdict_for_plan(plan, verdict), identity_counts={"0": {"S1c": None, "S2c": None, "G6s": None}},
               identity_rule="synthetic", spearman_beside_level0=None, g6l_screen=None)
    res["r27"] = r27 if r27 is not None else {"0": r27_block(status=res["verdict"].get("primary_status"),
                                                             survives=bool(res["verdict"].get("survives")))}
    return res


def plan_of(row, open_gates=frozenset()):
    return RN.classify(row, open_gates)


def record(row, plan, pass_, ident, outcome, status, result=None, gate="none", inputs=None):
    rec = header(pass_, ident, gate)
    rec.update(row=row.row, target_number=row.target_no, cell_id=row.cell_id, claim_form=row.claim_form,
               gate_column=row.gate, status_tsv=row.status, status_effective=plan["status_effective"],
               view=plan["view"], route=plan["route"], outcome=outcome, status_written=status,
               descriptor=plan["descriptor"], label=plan["label"], in_m=plan["in_m"], index_forms=plan["index_forms"],
               result=result, inputs=inputs or {"analysis_class": row["analysis_class"]}, memory=None,
               provenance=provenance(ident),
               row_provenance={"row": row.row, "target_number": row.target_no,
                               "seeds": {"row": row.row, "target_number": row.target_no,
                                         "per_map": [{"legs": [{"leg": "S1c", "leg_no": 0, "seed_int": 11}]}]},
                               "input_hashes": {"map[0]": "0" * 64}, "started": "t0", "finished": "t1", "host": {}})
    return rec


def sw_site_result(plan):
    """forms.signed_weight_site's record shape (the verdict pass of a signed-weight row), via forms._reported."""
    import a1_audit.forms as FM
    two, reg = plan["two_sided"], plan["registered_direction"]
    direction = None if two else reg
    legs = {k: FM._reported(dict(p=dict(v), floor=1 / 501, seed=11, info={}, seed_leg=i, status="ok", K=500),
                            direction, two) for i, (k, v) in enumerate(SITE_WEAK.items())}
    smax = FM._reported(dict(p={d: max(legs["S1c"]["p"][d], legs["S2c"]["p"][d]) for d in (1, -1)}, floor=1 / 501,
                             rule="synthetic", status="ok"), direction, two)
    return dict(form=FM.SW_FORM, T=0.3, N=10, Q=5, rule="synthetic", n_parcels=34, parcel_ids=[], site=dict(
        legs=legs, max=smax), two_sided=two, registered_direction=reg, direction_reading="synthetic",
        gene_legs="descriptor pass (U-F2)", survives=False, survival_rule="descriptive p's only")


def default_verdict(row, plan, strong=False):
    """The synthetic verdict-pass record of one row, by run.classify's plan."""
    if plan["kind"] in ("no statistic", "refused"):
        return "no statistic" if plan["kind"] == "no statistic" else "refused", plan["status_written"], None
    if plan["kind"] == "form":
        if plan["form_name"] == "signed-weight":
            return "computed", plan["status_effective"], sw_site_result(plan)
        return "no statistic", RN.FORM_NO_PASS[(plan["form_name"], "verdict")], None
    two, reg = plan["two_sided"], plan["registered_direction"]
    if plan.get("component") is not None:
        legs = component_legs(0.24, P(0.07, 0.93), SITE_WEAK)
        v = V.assemble_verdict_a1(legs, two_sided=two, registered_direction=reg,
                                  by_construction_label=plan.get("by_construction_label"))
    else:
        if strong:   # strong in the registered direction (or +, two-sided)
            f = (lambda pp: P(pp[-1], pp[1])) if reg == -1 else (lambda pp: pp)
            legs = full_legs(0.5 * (reg or 1), f(P(1e-5, 1 - 1e-5)), {"S1c": f(P(0.001, 0.999)),
                                                                      "S2c": f(P(0.002, 0.998))},
                             {"G1": f(P(0.003, 0.997)), "G3m": f(P(0.002, 0.998)), "G6s": f(P(0.004, 0.996)),
                              "G6l": f(P(0.001, 0.999))})
        else:
            legs = full_legs(-0.06 + 0.001 * (row.row % 7), P(0.6, 0.4), SITE_WEAK, SPECIES_WEAK)
        v = V.assemble_verdict_a1(legs, two_sided=two, registered_direction=reg,
                                  by_construction_label=plan.get("by_construction_label"))
    st = v.get("primary_status")
    r27 = {"0": r27_block(m=70, survives=bool(v.get("survives")) and not plan.get("descriptor"),
                          status=(plan["status_effective"] if plan.get("descriptor") else "ok") if st == "ok" else st,
                          cls=row["analysis_class"] if row["analysis_class"] in RN.KNOWN_CLASSES else "V-DK")}
    return "computed", None, verdict_result(plan, v, r27)


def dump(obj) -> bytes:
    return (json.dumps(A3.jsonable(obj), indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def write_pass(root: Path, gate: str, pass_: str, records: dict, ident, repro: dict | None = None,
               summary: bool = True, gate_arg: str = "none"):
    d = root / "a1_run" / gate / pass_
    d.mkdir(parents=True, exist_ok=True)
    (d / "launch_record.json").write_bytes(dump(launch(ident, None if gate_arg == "none" else gate_arg)))
    files, outcomes = {}, {}
    for n, rec in sorted(records.items()):
        b = dump(rec)
        (d / f"row_{n:04d}.json").write_bytes(b)
        files[str(n)] = RC.sha256_bytes(b)
        outcomes[rec["outcome"]] = outcomes.get(rec["outcome"], 0) + 1
    for n, rec in (repro or {}).items():
        (d / f"row_{n:04d}_repro.json").write_bytes(dump(rec))
    if summary:
        s = header(pass_, ident, gate_arg)
        s.update(what="A1 run summary (one pass)", n_rows=len(records), outcomes=outcomes, routes={}, files=files,
                 launch_failed=[], provenance=provenance(ident))
        (d / "RUN_SUMMARY.json").write_bytes(dump(s))
    (d / "run.log").write_text("synthetic\n", encoding="utf-8")
    return d


def repro_record(row, pass_, ident, rep):
    rec = header(pass_, ident)
    rec.update(what="reproduction check or descriptive comparison of one row (RUN_PLAN §16; WP3)", row=row.row,
               target_number=row.target_no, cell_id=row.cell_id, reproduction=rep, provenance=provenance(ident))
    return rec


def ungated_verdict_records(ident, rows=None):
    recs, plans = {}, {}
    for r in REG.gate_rows("ungated"):
        if rows is not None and r.row not in rows:
            continue
        p = plan_of(r)
        out, st, res = default_verdict(r, p)
        recs[r.row] = record(r, p, "verdict", ident, out, st, res)
        plans[r.row] = p
    return recs, plans


def ungated_repros(ident, recs, extra=None):
    """Segura / Moreau reproduction records beside their computed rows (verdict pass), Moreau's with an R37 check."""
    out = {}
    for n, rec in recs.items():
        r = REG.rows[n]
        if rec["outcome"] != "computed" or r.target_no not in (1, 18):
            continue
        rep = {"kind": "reproduction descriptive (amendment 4 §2)", "reading": "synthetic"}
        if r.cell_id in ("MOR-C1", "MOR-C2"):
            rep = {"kind": "4.1 check (R27; R37 (B))", "check": RPT.reproduction_check(".242", 0.23, functional="R2")}
        out[n] = repro_record(r, "verdict", ident, rep)
    for n, rep in (extra or {}).items():
        out[n] = repro_record(REG.rows[n], "verdict", ident, rep)
    return out


def descriptor_record(row, plan, ident, vrec):
    """A descriptor-pass record: full forms (run.py _assemble_row's descriptor branch), Liu (forms.liu_compute)."""
    if plan["kind"] in ("no statistic", "refused"):
        return record(row, plan, "descriptor", ident, "no statistic", plan["status_written"])
    if plan.get("component") is not None:
        return record(row, plan, "descriptor", ident, "no statistic", RN.NO_DESCRIPTOR_COMPONENT)
    two, reg = plan["two_sided"], plan["registered_direction"]
    legs = {name: dict(leg=name, K=200, m=25, status="ok", p={1: 0.3 + 0.01 * i, -1: 0.7 - 0.01 * i},
                       floor=1 / 201, n=200) for i, name in enumerate(DS.LEVEL2_LEGS)}
    if plan["kind"] == "form":   # Liu
        direction = None if two else reg
        l2 = DS.level2_max(legs)
        for rec in (*legs.values(), l2):
            DS._with_direction(rec, direction, two)
        res = dict(form="gene-set-only (RUN_PLAN R10)", cell_id=row.cell_id, T=0.11, legs=legs, level2=l2,
                   two_sided=two, registered_direction=reg, reading="no calibrated test (synthetic)",
                   survives=False, survival_rule="descriptive p's only")
        return record(row, plan, "descriptor", ident, "computed", plan["status_effective"], res)
    v = vrec["result"]["verdict"]
    direction = v.get("d_star") if two else reg
    l2 = DS.level2_max(legs)
    j1 = dict(status="ok", p={1: 0.2, -1: 0.8})
    nj = dict(status="ok", p={1: 0.25, -1: 0.75})
    for rec in (*legs.values(), l2, j1, nj):
        DS._with_direction(rec, direction, two)
    per = dict(form=plan["form"], T=v.get("T"), legs=legs, level2=l2, J1=j1, naive_joint=nj,
               counts=dict(K_sets=200, K_surr=500, K_j1_sets=100), direction=direction, two_sided=two,
               direction_reading=DS.R1_DESCRIPTOR_READING, labels={}, unconditioned="synthetic")
    res = {"direction_from_verdict": dict(d_star=v.get("d_star"), registered_direction=reg, two_sided=two,
                                          verdict_result_sha256=RC.sha256_json(json.loads(dump(vrec["result"])))),
           "per_map": {"0": per}}
    return record(row, plan, "descriptor", ident, "computed", plan["status_effective"], res)


def fresh(name) -> Path:
    d = SCRATCH / name
    if d.exists():
        import shutil
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d


# ================================================================================================================
# checks
# ================================================================================================================
@check("full_tree_verdict_only")
def t_full():
    root = fresh("full")
    ident = identity()
    recs, _ = ungated_verdict_records(ident)
    write_pass(root, "ungated", "verdict", recs, ident, repro=ungated_repros(ident, recs))
    a = RC.assemble(ROOT, root, "ungated")
    shas = RC.write_outputs(a, root / "out", "ungated")
    cells = a["cells"]
    assert len(cells) == len(REG.gate_rows("ungated")) == 115
    by = {c["row"]: c for c in cells}
    # a computed full row: descriptor / sensitivity read "pass not run"
    c10 = by[10]
    assert c10["descriptor_legs"] == RC.PNR and c10["sensitivity_ge2_donors"] == RC.PNR, c10["descriptor_legs"]
    assert c10["passes"]["descriptor"]["state"] == RC.PNR
    # Liu: T comes from the descriptor pass, which has not run
    assert by[471]["T"] == RC.PNR and by[471]["descriptor_legs"] == RC.PNR
    # the interim headline: derived 0 of 14
    comp = a["comp"]
    assert comp["population_units"] == REG.r4["population.interim"] and comp["can_survive"] == 0
    assert comp["composition"] == {k[len("population.interim."):]: v for k, v in REG.r4.items()
                                   if k.startswith("population.interim.")}
    h = a["head"]["headline"]
    for frag in (RC.CURVES, RC.FAILED_AS_GATES, RC.LOW_FRACTION, "tested-only fraction", "A6's outcome"):
        assert frag in h, frag
    assert "0 of the 14 can survive" in h
    # outputs read back
    out = root / "out"
    for rel, sha in (("a1_run/ungated/cells.jsonl", shas["cells.jsonl"]), ("a1_run/ungated/cells.md", shas["cells.md"]),
                     ("a1_run/ungated/headline.json", shas["headline.json"]), ("MANIFEST_claims.md",
                                                                              shas["MANIFEST_claims.md"])):
        assert RC.sha256_bytes((out / rel).read_bytes()) == sha, rel
    man = (out / "MANIFEST_claims.md").read_text(encoding="utf-8")
    lines = [ln for ln in man.split("\n") if ln.startswith("| ") and ln[2:3].isdigit()]
    assert len(lines) == 2 * LD.N_ROWS, len(lines)
    assert "deferred (G1 not run)" in man and "deferred (G2 not run)" in man
    # CLI on the same tree
    rc = RC.main(["--gate", "ungated", "--results-root", str(root), "--out", str(root / "out_cli"), "--repo", str(ROOT)])
    assert rc == 0
    return dict(cells=len(cells), composition=comp["composition"], survivals=comp["survivals"])


@check("missing_pass_rows_and_incomplete_pass")
def t_missing():
    root = fresh("missing")
    ident = identity()
    subset = {1, 2, 3, 10, 11, 471, 472, 473, 474, 615, 616}
    recs, _ = ungated_verdict_records(ident, rows=subset)
    write_pass(root, "ungated", "verdict", recs, ident)
    a = RC.assemble(ROOT, root, "ungated")
    by = {c["row"]: c for c in a["cells"]}
    assert by[12]["passes"]["verdict"]["state"] == RC.PNR_ROW and by[12]["T"] == RC.PNR_ROW, by[12]["T"]
    assert by[12]["legs"] == RC.PNR_ROW and by[12]["r27"] == RC.PNR_ROW
    # a descriptor pass of some rows fills the descriptor legs and Liu's T
    drecs = {}
    for n in (10, 471, 615):
        r = REG.rows[n]
        drecs[n] = descriptor_record(r, plan_of(r), ident, recs[n])
    write_pass(root, "ungated", "descriptor", drecs, ident)
    a = RC.assemble(ROOT, root, "ungated")
    by = {c["row"]: c for c in a["cells"]}
    assert isinstance(by[10]["descriptor_legs"], dict) and "0" in by[10]["descriptor_legs"]
    assert by[471]["T"] == 0.11 and isinstance(by[471]["descriptor_legs"], dict)
    assert by[615]["descriptor_legs"].startswith("no descriptor legs") or \
        by[615]["descriptor_legs"].startswith("no statistic")
    assert by[11]["descriptor_legs"] == RC.PNR_ROW
    assert by[10]["sensitivity_ge2_donors"] == RC.PNR
    # an incomplete pass (no RUN_SUMMARY): refused by default, skipped on request
    write_pass(root, "ungated", "sensitivity", {10: record(REG.rows[10], plan_of(REG.rows[10]), "sensitivity", ident,
                                                           "computed", RN.PARCELS_UNCHANGED,
                                                           dict(sensitivity="R11", parcel_set="unchanged",
                                                                primary_result_sha256="0"))},
               ident, summary=False)
    msg = raises(RC.ReportRefused, RC.assemble, ROOT, root, "ungated")
    assert "incomplete" in msg
    a = RC.assemble(ROOT, root, "ungated", incomplete="skip")
    by = {c["row"]: c for c in a["cells"]}
    assert by[10]["sensitivity_ge2_donors"] == RC.PNR_INCOMPLETE
    return dict(refusal=msg[:120])


@check("mixed_identities_refused")
def t_mixed():
    out = {}
    ident = identity()
    rows = {10, 471, 615}
    recs, _ = ungated_verdict_records(ident, rows=rows)

    def tree(name):
        root = fresh(name)
        write_pass(root, "ungated", "verdict", recs, ident)
        return root
    # (a) another code hash in the descriptor pass
    root = tree("mixed_a")
    other = identity(code_hash="c" * 64)
    drecs = {n: descriptor_record(REG.rows[n], plan_of(REG.rows[n]), other, recs[n]) for n in rows}
    write_pass(root, "ungated", "descriptor", drecs, other)
    out["a"] = raises(RC.ReportRefused, RC.assemble, ROOT, root, "ungated")
    assert "mixed run identities across passes" in out["a"] and "code_hash" in out["a"]
    # (b) another commit
    root = tree("mixed_b")
    other = identity(commit="d" * 40)
    drecs = {n: descriptor_record(REG.rows[n], plan_of(REG.rows[n]), other, recs[n]) for n in rows}
    write_pass(root, "ungated", "descriptor", drecs, other)
    out["b"] = raises(RC.ReportRefused, RC.assemble, ROOT, root, "ungated")
    assert "run_commit" in out["b"]
    # (c) a row whose provenance names another commit
    root = fresh("mixed_c")
    bad = copy.deepcopy(recs)
    bad[10]["provenance"]["run_commit"] = "e" * 40
    write_pass(root, "ungated", "verdict", bad, ident)
    out["c"] = raises(RC.ReportRefused, RC.assemble, ROOT, root, "ungated")
    assert "provenance names commit" in out["c"]
    # (d) a row file edited after its RUN_SUMMARY
    root = tree("mixed_d")
    f = root / "a1_run/ungated/verdict/row_0010.json"
    f.write_bytes(f.read_bytes().replace(b'"output_root": "synthetic"', b'"output_root": "edited"'))
    out["d"] = raises(RC.ReportRefused, RC.assemble, ROOT, root, "ungated")
    assert "sha256 differs" in out["d"]
    # (e) a DEV-stamped record
    root = fresh("mixed_e")
    bad = copy.deepcopy(recs)
    bad[471]["stamp"] = "DEV (launch refused: L11)"
    write_pass(root, "ungated", "verdict", bad, ident)
    out["e"] = raises(RC.ReportRefused, RC.assemble, ROOT, root, "ungated")
    assert "DEV" in out["e"]
    # (f) an incomplete pass holding another run's records, even when skipped
    root = tree("mixed_f")
    other = identity(code_hash="f" * 64)
    write_pass(root, "ungated", "descriptor",
               {10: descriptor_record(REG.rows[10], plan_of(REG.rows[10]), other, recs[10])}, other, summary=False)
    out["f"] = raises(RC.ReportRefused, RC.assemble, ROOT, root, "ungated", incomplete="skip")
    assert "another run identity" in out["f"]
    # (g) a sensitivity record naming another verdict result
    root = tree("mixed_g")
    srec = record(REG.rows[10], plan_of(REG.rows[10]), "sensitivity", ident, "computed", RN.PARCELS_UNCHANGED,
                  dict(sensitivity="R11", parcel_set="unchanged", primary_result_sha256="0" * 64))
    write_pass(root, "ungated", "sensitivity", {10: srec}, ident)
    out["g"] = raises(RC.ReportRefused, RC.assemble, ROOT, root, "ungated")
    assert "names a verdict result other than the one read" in out["g"]
    return {k: v[:100] for k, v in out.items()}


@check("b6_comparator_statuses_never_reach_the_composition")
def t_b6():
    ident = identity()
    recs, plans = ungated_verdict_records(ident)
    # baseline
    root0 = fresh("b6_base")
    write_pass(root0, "ungated", "verdict", recs, ident, repro=ungated_repros(ident, recs))
    a0 = RC.assemble(ROOT, root0, "ungated")
    # comparator statuses in reproduction records: Segura S6 (row 3, verdict pass) and Liu SD7 (row 473, descriptor)
    s6 = "not computable (Table S6 not transcribed: 106 genes)"
    sd7 = "not computable (SD7's ASD column holds a non-numeric value)"
    rep3 = {"kind": "reproduction descriptive (amendment 4 §2)", "jaccard_table_s6": {"status": s6}}
    root = fresh("b6_comp")
    write_pass(root, "ungated", "verdict", recs, ident, repro=ungated_repros(ident, recs, extra={3: rep3}))
    drecs = {n: descriptor_record(REG.rows[n], plans[n], ident, recs[n]) for n in recs}
    drepro = {473: repro_record(REG.rows[473], "descriptor", ident,
                                {"kind": "4.1 check (R46 (g))", "comparator": {"status": sd7}})}
    write_pass(root, "ungated", "descriptor", drecs, ident, repro=drepro)
    a1 = RC.assemble(ROOT, root, "ungated")
    by = {c["row"]: c for c in a1["cells"]}
    assert sd7 in by[473]["comparator_statuses"] and s6 in by[3]["comparator_statuses"]
    assert a1["comp"]["composition"] == a0["comp"]["composition"], (a1["comp"]["composition"],
                                                                     a0["comp"]["composition"])
    u = {x["row"]: x for x in a1["comp"]["units"]}
    assert u[473]["category"] == "no calibrated test" and u[3]["category"] == "not testable as stated"
    assert by[473]["status_tsv"] == REG.rows[473].status
    # a fail-closed CELL status in the row record (R46) does move the composition (not a comparator)
    root2 = fresh("b6_cell")
    write_pass(root2, "ungated", "verdict", recs, ident, repro=ungated_repros(ident, recs))
    d2 = dict(drecs)
    d2[474] = record(REG.rows[474], plans[474], "descriptor", ident, "no statistic",
                     "not auditable (definition not applicable: SD7 labels unmatched)")
    write_pass(root2, "ungated", "descriptor", d2, ident)
    a2 = RC.assemble(ROOT, root2, "ungated")
    u2 = {x["row"]: x for x in a2["comp"]["units"]}
    assert u2[474]["category"] == "not auditable", u2[474]
    assert a2["comp"]["composition"]["not auditable"] == a0["comp"]["composition"]["not auditable"] + 1
    # planted: a composition that read a comparator status is caught
    planted = [(REG.rows[473].status, "tsv: status"), (sd7, "repro: descriptor row_0473_repro.json comparator")]
    m1 = raises(RC.ReportRefused, RC.assert_b6, 473, planted, {sd7})
    m2 = raises(RC.ReportRefused, RC.assert_b6, 473, [(sd7, "derived")], {sd7})
    orig = RC.run_flags

    def leaky(cells_by_row, gates, row):
        extra, basis, lt5, pending = orig(cells_by_row, gates, row)
        c = cells_by_row.get(row.row) or {}
        for st in c.get("comparator_statuses", []):
            basis.append((st, "repro: comparator"))
        return extra, basis, lt5, pending
    RC.run_flags = leaky
    try:
        m3 = raises(RC.ReportRefused, RC.assemble, ROOT, root, "ungated")
    finally:
        RC.run_flags = orig
    assert "B6" in m1 and "B6" in m2 and "B6" in m3
    return dict(caught=[m1[:80], m3[:80]])


@check("forbidden_words")
def t_words():
    for w in RC.FORBIDDEN:
        for form in (w, w.upper(), w.capitalize()):
            raises(RC.ReportRefused, RC.check_wording, f"the claim {form} at this power", "planted")
    RC.check_wording('gates 1-11 "failed as gates under amendment 3"; not detectable at this power', "ok")
    RC.check_wording("refutedness failsafe", "ok (not whole words)")
    root = fresh("words")
    ident = identity()
    recs, _ = ungated_verdict_records(ident, rows={1, 471, 615})
    write_pass(root, "ungated", "verdict", recs, ident)
    a = RC.assemble(ROOT, root, "ungated")
    for t in a["head"].values():
        RC.check_wording(t, "generated")
    orig = RC.LOW_FRACTION
    RC.LOW_FRACTION = "few published claims are not supported"
    try:
        msg = raises(RC.ReportRefused, RC.headline_sentences, a["comp"])
    finally:
        RC.LOW_FRACTION = orig
    assert "not supported" in msg
    # a planted reading in a record is caught when the cell is built
    bad = copy.deepcopy(recs)
    bad[615]["result"]["verdict"]["reading"] = "fails at component level"
    root2 = fresh("words2")
    write_pass(root2, "ungated", "verdict", bad, ident)
    m2 = raises(RC.ReportRefused, RC.assemble, ROOT, root2, "ungated")
    assert "forbidden word" in m2
    return dict(caught=[msg[:80], m2[:80]])


@check("r1_two_p_dstar_and_literal_two_min")
def t_r1():
    # a two-sided stub where d* = + while G1's own minimum is - (test_verdict's st2 values)
    sp = {"G1": P(0.995, 0.006), "G3m": P(0.99, 0.01), "G6s": P(0.97, 0.03), "G6l": P(0.99, 0.01)}
    legs = full_legs(0.4, P(1e-4, 0.9999), {"S1c": P(0.004, 0.996), "S2c": P(0.002, 0.998)}, sp)
    v = V.assemble_verdict_a1(legs, two_sided=True)
    assert v["d_star"] == 1
    # SEG-C3-D01 (row 10) is a two-sided decoded-list descriptor cell: its record carries the computed legs
    r = REG.rows[10]
    plan = plan_of(r)
    assert plan["two_sided"] is True
    ident = identity()
    recs, _ = ungated_verdict_records(ident, rows={10, 615})
    recs[10] = record(r, plan, "verdict", ident, "computed", None, verdict_result(plan, v))
    root = fresh("r1")
    write_pass(root, "ungated", "verdict", recs, ident)
    a = RC.assemble(ROOT, root, "ungated")
    c = {x["row"]: x for x in a["cells"]}[10]
    g1 = c["legs"]["G1"]
    assert g1["p_reported"] == 1.0 and g1["p_per_leg_two_sided"] == 0.012, g1
    assert g1["p_plus"] == 0.995 and g1["p_minus"] == 0.006
    assert c["legs"]["Level 0"]["p_reported"] == 2e-4 and c["conjunction"]["p"] == 1.0
    assert "per-leg two-sided (not the verdict p)" in c["labels_R1"]["p_per_leg_two_sided"]
    md = (RC.cells_md("ungated", a["cells"], a["meta"], a["head"], a["comp"], a["desc"], a["bh"], REG))
    # Level 0 and the species leg side by side: 2 p(d*) [literal 2 min]; the species leg differs (1 vs .06)
    assert "| 0.0002 [0.0002] |" in md and "| 1 [0.06] |" in md
    caught = {}
    for what, path, val in (("p_reported", ("legs", "G1", "p_reported"), 0.012),
                            ("per_leg", ("legs", "G1", "p_per_leg_two_sided"), 1.0),
                            ("conjunction", ("p_conjunction",), 0.5)):
        bad = copy.deepcopy(recs)
        tgt = bad[10]["result"]["verdict"]["descriptor"]
        for k in path[:-1]:
            tgt = tgt[k]
        tgt[path[-1]] = val
        root2 = fresh(f"r1_{what}")
        write_pass(root2, "ungated", "verdict", bad, ident)
        caught[what] = raises(RC.ReportRefused, RC.assemble, ROOT, root2, "ungated")[:90]
    # one-sided: no per-leg two-sided p allowed
    lv = {"status": "ok", "p_plus": 0.1, "p_minus": 0.9, "p_reported": 0.1, "p_per_leg_two_sided": 0.2}
    caught["one_sided"] = raises(RC.ReportRefused, RC.check_r1_leg, "planted", lv, 1, False)[:90]
    return dict(caught=caught)


@check("bh_recomputed_and_r29_family")
def t_bh():
    from statsmodels.stats.multitest import multipletests
    rng = np.random.default_rng(7)
    ps = list(rng.uniform(0, 1, 50)) + [0.01, 0.01, 0.5, 1.0, 0.0001]
    q = RC.bh_q(ps)
    ref = multipletests(ps, method="fdr_bh")[1]
    assert max(abs(a - b) for a, b in zip(q, ref)) < 1e-12
    assert RC.bh_q([]) == []
    # R29 membership on synthetic cells
    in_m = next(r for r in REG.rows.values() if r.m_membership == "yes" and r["reproduction"].startswith("descr"))
    not_m = next(r for r in REG.rows.values() if r.m_membership == "no")
    flagged = next(r for r in REG.rows.values() if r.m_membership == "yes"
                   and r["reproduction"].startswith("not reproduced"))

    def cell(primary, p=0.01, kind="full", comp=None):
        return {"verdict": {"kind": kind, "primary_status": primary, "survives": False, "descriptor_row": False},
                "conjunction": {"p": p, "p_component": comp}, "reproduction_flag": {"flag": None}}
    assert RC.bh_entry(not_m, cell("ok"))["family"] == "outside: not in m"
    assert RC.bh_entry(flagged, dict(cell("ok"), reproduction_flag=RC.reproduction_flag(flagged, [])))["family"] \
        .startswith("outside: flagged not reproduced")
    assert RC.bh_entry(in_m, cell("ok"))["p_entered"] == 0.01
    assert RC.bh_entry(in_m, cell("resolution-limited", p=0.001))["p_entered"] == 1.0
    assert RC.bh_entry(in_m, cell("g6l unmatched", p=None))["p_entered"] == 1.0
    assert RC.bh_entry(in_m, cell(V.R8_NOT_AUDITABLE, p=None))["family"].startswith("outside: not auditable")
    assert RC.bh_entry(in_m, cell("ok", p=0.3, kind="component-permutation", comp=0.3))["p_entered"] == 0.3
    assert RC.bh_entry(in_m, {"verdict": "pass not run", "reproduction_flag": {}})["family"].startswith("outside")
    raises(RC.ReportRefused, RC.bh_entry, in_m, dict(cell("ok"), verdict=dict(cell("ok")["verdict"],
                                                                                descriptor_row=True)))
    # the synthetic tree: m rows of the ungated gate (MOR-C1, MOR-C2) get BH(q) of their component p's
    root = fresh("bh")
    ident = identity()
    recs, _ = ungated_verdict_records(ident)
    recs[616]["result"]["verdict"]["p_component"] = recs[616]["result"]["verdict"]["p_conjunction"]
    write_pass(root, "ungated", "verdict", recs, ident, repro=ungated_repros(ident, recs))
    a = RC.assemble(ROOT, root, "ungated")
    fam = [c for c in a["cells"] if (c.get("bh") or {}).get("family") == "in"]
    assert sorted(c["row"] for c in fam) == sorted(r.row for r in REG.gate_rows("ungated") if r.m_membership == "yes")
    want = RC.bh_q([c["bh"]["p_entered"] for c in fam])
    assert [c["bh"]["q_interim_gate"] for c in fam] == want
    assert all(str(c["bh"]["q_final"]).startswith("not computed") for c in fam)
    return dict(max_abs_diff_vs_statsmodels=float(max(abs(a - b) for a, b in zip(q, ref))), family=len(fam))


@check("register_numbers_and_interim_derivation")
def t_register():
    got = RC.check_register_numbers(REG)
    assert got["equal"] and got["checked"] == len(REG.r4)
    reg2 = copy.copy(REG)
    reg2.r4 = dict(REG.r4)
    reg2.r4["population.interim.not auditable"] += 1
    m1 = raises(RC.ReportRefused, RC.check_register_numbers, reg2)
    root = fresh("interim")
    ident = identity()
    recs, _ = ungated_verdict_records(ident)
    write_pass(root, "ungated", "verdict", recs, ident)
    a = RC.assemble(ROOT, root, "ungated")
    comp = dict(a["comp"], can_survive=1)
    m2 = raises(RC.ReportRefused, RC.assert_interim, REG, comp)
    comp = dict(a["comp"], population_units=13)
    m3 = raises(RC.ReportRefused, RC.assert_interim, REG, comp)
    ok = RC.assert_interim(REG, a["comp"])
    assert ok["derived_can_survive"] == 0 == ok["register_can_survive"]
    return dict(caught=[m1[:80], m2[:80], m3[:80]], interim=ok)


@check("g2_line130_labels_and_the_post_exposure_version_beside_never_counted")
def t_g2_amend5():
    """RUN_PLAN_amend_5 v2 (B4, A): every G2 cell joins wp4_sources.row_labels (the line-130 label on the 6 MDD-set
    DEG cells); a cell an amend_5 post-exposure reading bears on carries its second version from
    results/a1_run/rerun_amend5/G2/ beside the primary one, and the composition, the headline, the BH families and the
    primary cells are identical with and without that second version (never counted)."""
    from a1_audit import wp4_layout as W4L
    from a1_audit import wp4_sources as W4S
    root = fresh("g2_amend5")
    ident = identity()
    recs_u, _ = ungated_verdict_records(ident)
    write_pass(root, "ungated", "verdict", recs_u, ident, repro=ungated_repros(ident, recs_u))
    og = frozenset({"G2"})
    g2 = {}
    for r in REG.gate_rows("G2"):
        p = plan_of(r, og)
        out, st, res = default_verdict(r, p)
        g2[r.row] = record(r, p, "verdict", ident, out, st, res, gate="G2")
    write_pass(root, "G2", "verdict", g2, ident, gate_arg="G2")
    a0 = RC.assemble(ROOT, root, "G2")
    cells0 = {c["row"]: c for c in a0["cells"]}
    lab = [c for c in a0["cells"] if c["labels_g2"]]
    assert sorted(c["cell_id"] for c in lab) == sorted(f"GIA-MDD-DEG-MDDset-{t}-{k}" for t in ("01", "05", "10")
                                                       for k in ("ctx", "sub"))
    assert all(c["labels_g2"] == [W4L.LINE130_LABEL] for c in lab)
    pe0 = [c for c in a0["cells"] if c.get("post_exposure_version")]
    assert pe0 and all(c["post_exposure_version"]["state"] == RC.PE_PENDING for c in pe0)
    assert all(W4S.amend5_readings(c["cell_id"], REG.rows[c["row"]]["map"]) for c in pe0)
    assert not any(W4S.amend5_readings(c["cell_id"], REG.rows[c["row"]]["map"]) for c in a0["cells"]
                   if not c.get("post_exposure_version"))
    n_deg = sum(1 for c in pe0 if W4L.AMEND5_PE_READINGS[2] in c["post_exposure_version"]["readings"])
    assert n_deg == 18, n_deg
    # the second version: the same synthetic records under rerun_amend5/G2 (a different outcome on one affected row)
    g2b = copy.deepcopy(g2)
    probe = pe0[0]["row"]
    g2b[probe]["outcome"] = "computed" if g2b[probe]["outcome"] != "computed" else g2b[probe]["outcome"]
    write_pass(root, f"rerun_{W4L.AMEND5_RERUN_TAG}/G2", "verdict", g2b, ident, gate_arg="G2")
    a1 = RC.assemble(ROOT, root, "G2")
    pe1 = {c["row"]: c["post_exposure_version"] for c in a1["cells"] if c.get("post_exposure_version")}
    assert set(pe1) == {c["row"] for c in pe0} and all(v["state"] == "read" for v in pe1.values())
    assert all(v["label"] == W4L.AMEND5_VERSION_LABEL and v["counted"] == RC.PE_EXCLUDED for v in pe1.values())
    assert a1["comp"] == a0["comp"] and a1["head"] == a0["head"] and a1["bh"] == a0["bh"]   # never counted
    for c in a1["cells"]:                                            # the primary cell is unchanged
        c0 = cells0[c["row"]]
        assert {k: v for k, v in c.items() if k != "post_exposure_version"} == \
            {k: v for k, v in c0.items() if k != "post_exposure_version"}, c["row"]
    # an INCOMPLETE second-version pass (no RUN_SUMMARY) is skipped, never refused; the primary report stands
    inc = root / "a1_run" / f"rerun_{W4L.AMEND5_RERUN_TAG}" / "G2" / "descriptor"
    inc.mkdir(parents=True, exist_ok=True)
    (inc / "row_0001.json").write_bytes(dump(g2b[probe]))
    a2 = RC.assemble(ROOT, root, "G2")
    v2 = [c["post_exposure_version"] for c in a2["cells"] if c.get("post_exposure_version")]
    assert all(v["state"] == "read" and "descriptor" in v["pending_passes"] for v in v2)
    assert a2["comp"] == a0["comp"] and a2["head"] == a0["head"]
    shutil.rmtree(inc)
    shas = RC.write_outputs(a1, root / "out", "G2")
    md = (root / "out" / "a1_run" / "G2" / "cells.md").read_text(encoding="utf-8")
    assert "## Labels and post-exposure versions (RUN_PLAN_amend_5 v2; G2)" in md and W4L.LINE130_LABEL in md
    assert W4L.AMEND5_VERSION_LABEL in md and RC.sha256_bytes((root / "out" / "a1_run" / "G2" / "cells.md")
                                                            .read_bytes()) == shas["cells.md"]
    a_u = RC.assemble(ROOT, root, "ungated")                         # the ungated report carries none of it
    assert not any("labels_g2" in c or "post_exposure_version" in c for c in a_u["cells"])
    return dict(n_labelled=len(lab), n_post_exposure=len(pe0), n_deg=n_deg)


@check("row_rerun_replaces_its_row_only_and_moves_no_count")
def t_row_rerun():
    """2026-11-02 (Liu T3 restored from quarantine): a declared row rerun (ROW_RERUNS; results/a1_run/rerun_TAG/G2/,
    another run identity) replaces that row's cell at use and names the primary records; every other cell, the
    composition and the headline are unchanged; an incomplete rerun pass leaves the primary cell, reading 'pending'.
    Planted: a rerun pass holding an undeclared row, a rerun declared on a population unit - each refused."""
    from a1_audit import fetch_extract as FE
    from a1_audit import wp4_layout as W4L
    root = fresh("row_rerun")
    ident, other = identity(), identity(commit="c" * 40, code_hash="d" * 64)
    recs_u, _ = ungated_verdict_records(ident)
    write_pass(root, "ungated", "verdict", recs_u, ident, repro=ungated_repros(ident, recs_u))
    og = frozenset({"G2"})
    g2 = {}
    for r in REG.gate_rows("G2"):
        p = plan_of(r, og)
        out, st, res = default_verdict(r, p)
        g2[r.row] = record(r, p, "verdict", ident, out, st, res, gate="G2")
    n = RC.ROW_RERUNS[0][2][0]
    row = REG.rows[n]
    quar = W4L.STATUS_STAGE_REFUSED % FE.STATUS_IN_QUARANTINE
    g2[n] = record(row, plan_of(row, og), "verdict", ident, "not run", quar, gate="G2")
    write_pass(root, "G2", "verdict", g2, ident, gate_arg="G2")
    a0 = RC.assemble(ROOT, root, "G2")
    c0 = {c["row"]: c for c in a0["cells"]}
    assert c0[n]["status_effective"] == quar and c0[n]["row_rerun"]["state"].startswith("pending"), c0[n]["row_rerun"]
    p = plan_of(row, og)
    out, st, res = default_verdict(row, p)
    tag = RC.ROW_RERUNS[0][1]
    write_pass(root, f"rerun_{tag}/G2", "verdict", {n: record(row, p, "verdict", other, out, st, res, gate="G2")},
               other, gate_arg="G2")
    a1 = RC.assemble(ROOT, root, "G2")
    c1 = {c["row"]: c for c in a1["cells"]}
    rr = c1[n]["row_rerun"]
    assert rr["state"] == "read" and rr["primary"]["status_effective"] == quar and rr["identity"]["run_commit"] == "c" * 40
    assert c1[n]["passes"]["verdict"]["file"] == f"a1_run/rerun_{tag}/G2/verdict/row_{n:04d}.json"
    assert c1[n]["passes"]["verdict"]["outcome"] == out and c1[n]["status_effective"] != quar
    assert a1["comp"] == a0["comp"] and a1["head"] == a0["head"]                 # no count moves
    for m, c in c1.items():                                                     # every other cell's record unchanged
        if m != n:
            assert c["passes"] == c0[m]["passes"] and c["status_effective"] == c0[m]["status_effective"], m
    man = RC.manifest_md(a1["reg"], a1["gates"], a1["cells_all"], a1["meta"])
    assert f"- row rerun {tag}" in man
    # planted: an undeclared row in the rerun pass
    d = root / "a1_run" / f"rerun_{tag}" / "G2"
    m2 = next(m for m in sorted(g2) if m != n)
    p2 = plan_of(REG.rows[m2], og)
    o2, s2, r2 = default_verdict(REG.rows[m2], p2)
    shutil.rmtree(d)
    write_pass(root, f"rerun_{tag}/G2", "verdict", {n: record(row, p, "verdict", other, out, st, res, gate="G2"),
                                                    m2: record(REG.rows[m2], p2, "verdict", other, o2, s2, r2,
                                                               gate="G2")}, other, gate_arg="G2")
    assert "not the declared" in raises(RC.ReportRefused, RC.assemble, ROOT, root, "G2")
    # planted: an incomplete rerun pass
    shutil.rmtree(d)
    write_pass(root, f"rerun_{tag}/G2", "verdict", {n: record(row, p, "verdict", other, out, st, res, gate="G2")},
               other, gate_arg="G2")
    (d / "verdict" / "RUN_SUMMARY.json").unlink()
    a2 = RC.assemble(ROOT, root, "G2")                                          # still running: primary stands
    c2 = {c["row"]: c for c in a2["cells"]}
    assert c2[n]["status_effective"] == quar and "incomplete: verdict" in c2[n]["row_rerun"]["state"],         c2[n]["row_rerun"]
    shutil.rmtree(d)
    # planted: a rerun declared on a population unit
    unit = next(u["row"] for u in a0["comp"]["units"] if u["row"] in g2)
    orig = RC.ROW_RERUNS
    RC.ROW_RERUNS = (("G2", "unit_probe", (unit,), "probe"),)
    try:
        pu = plan_of(REG.rows[unit], og)
        ou, su, ru = default_verdict(REG.rows[unit], pu)
        write_pass(root, "rerun_unit_probe/G2", "verdict", {unit: record(REG.rows[unit], pu, "verdict", other, ou, su,
                                                                         ru, gate="G2")}, other, gate_arg="G2")
        msg = raises(RC.ReportRefused, RC.assemble, ROOT, root, "G2")
    finally:
        RC.ROW_RERUNS = orig
    assert "population unit" in msg, msg
    return dict(row=n, outcome=out)


@check("writer_readback")
def t_readback():
    root = fresh("readback")
    cells = [{"row": 1, "x": "§ 1"}, {"row": 2, "x": [1, 2.5]}]
    p = root / "c.jsonl"
    sha = RC.write_checked(p, RC.jsonl_text(cells))
    RC.check_jsonl_back(p, cells)
    assert sha == RC.sha256_bytes(p.read_bytes())
    p.write_text(p.read_text(encoding="utf-8").replace("2.5", "2.6"), encoding="utf-8", newline="\n")
    m = raises(RC.ReportRefused, RC.check_jsonl_back, p, cells)
    return dict(caught=m[:80])


@check("sensitivity_unchanged_and_changed")
def t_sens():
    root = fresh("sens")
    ident = identity()
    recs, plans = ungated_verdict_records(ident, rows={10, 615})
    write_pass(root, "ungated", "verdict", recs, ident)
    vsha = {n: RC.sha256_json(json.loads(dump(recs[n]["result"]))) for n in recs}
    s10 = record(REG.rows[10], plans[10], "sensitivity", ident, "computed", RN.PARCELS_UNCHANGED,
                 dict(sensitivity="R11 >= 2-donor parcel set", parcel_set="unchanged", primary_result_sha256=vsha[10]))
    legs = component_legs(0.2, P(0.2, 0.8), SITE_WEAK)
    sv = V.assemble_verdict_a1(legs, two_sided=False, registered_direction=1)
    sres = dict(verdict=sv, identity_counts={}, identity_rule="synthetic", spearman_beside_level0=None, g6l_screen=None,
                sensitivity="R11 >= 2-donor parcel set", parcel_set="changed", primary_result_sha256=vsha[615])
    s615 = record(REG.rows[615], plans[615], "sensitivity", ident, "computed", plans[615]["status_effective"], sres)
    write_pass(root, "ungated", "sensitivity", {10: s10, 615: s615}, ident)
    a = RC.assemble(ROOT, root, "ungated")
    by = {c["row"]: c for c in a["cells"]}
    assert by[10]["sensitivity_ge2_donors"]["parcel_set"] == "unchanged"
    s = by[615]["sensitivity_ge2_donors"]
    assert s["parcel_set"] == "changed" and s["p_conjunction"] == sv["p_conjunction"] and s["survives"] is False
    assert by[615]["conjunction"]["p"] == recs[615]["result"]["verdict"]["p_conjunction"]   # primary unchanged
    return dict(changed_p=s["p_conjunction"])


@check("readings_published_null_and_two_cohort")
def t_readings():
    assert RC.published_null_reading(True, "ok").startswith("detectable by the verdict")
    assert RC.published_null_reading(False, "ok") == "not detectable at this power (as published)"
    assert RC.published_null_reading(False, "resolution-limited") == "resolution-limited"
    row = next(r for r in REG.rows.values() if r["cell_class"] == "claim")
    v = {"two_cohort": True, "survives": True, "primary_status": "ok"}
    r27 = {"0": {"reading_as_recorded": "survives — calibrated evidence"},
           "1": {"reading_as_recorded": "survives — calibration extrapolated (set size)"}}
    got = RC.compose_reading(row, v, False, v, r27)
    assert got == "survives — calibration extrapolated (set size)", got
    r27["1"]["reading_as_recorded"] = "survives — calibrated evidence"
    assert RC.compose_reading(row, v, False, v, r27) == "survives — calibrated evidence"
    v2 = {"two_cohort": True, "survives": False, "primary_status": "ok"}
    assert RC.compose_reading(row, v2, False, v2, r27) == "not detectable at this power"
    return {}


@check("after_G2_headline_survival_flag_and_restated_population")
def t_g2():
    """Two gates run (ungated, G2): the population joins G2's units (<= 18, RUN_PLAN \u00a716 :1683); one synthetic
    survival with an R27 'calibrated evidence' reading; a full-verdict claim flagged 'not reproduced' leaves the
    population and the BH family; the tested-only fraction; per-gate interim q's; G2 rows in the factorial."""
    root = fresh("g2")
    ident = identity()
    recs, _ = ungated_verdict_records(ident)
    write_pass(root, "ungated", "verdict", recs, ident, repro=ungated_repros(ident, recs))
    ident2 = identity(commit="9" * 40, code_hash="8" * 64)   # another gate may run at another commit
    og = frozenset({"G2"})
    rid = {REG.rows[n].cell_id: n for n in REG.rows}
    strong = {rid["PAT-C1"], rid["PAT-C3"]}
    g2 = {}
    for r in REG.gate_rows("G2"):
        p = plan_of(r, og)
        out, st, res = default_verdict(r, p, strong=r.row in strong)
        g2[r.row] = record(r, p, "verdict", ident2, out, st, res, gate="G2")
    for n in strong:
        assert g2[n]["result"]["verdict"]["survives"] is True, n
    bad = RPT.reproduction_check(".30", -0.2, functional="mean bicor")
    assert bad["label"] == "not reproduced (sign)"
    good = RPT.reproduction_check(".30", 0.31, functional="mean bicor")
    rep2 = {rid["PAT-C3"]: repro_record(REG.rows[rid["PAT-C3"]], "verdict", ident2, {"kind": "4.1 check", "check": bad}),
            rid["PAT-C1"]: repro_record(REG.rows[rid["PAT-C1"]], "verdict", ident2, {"kind": "4.1 check", "check": good})}
    for rr in rep2.values():
        rr["gate"] = "G2"
    write_pass(root, "G2", "verdict", g2, ident2, repro=rep2, gate_arg="G2")
    a = RC.assemble(ROOT, root, "G2")
    comp = a["comp"]
    assert comp["gates_run"] == ["ungated", "G2"] and comp["passes_read"] == {"ungated": ["verdict"], "G2": ["verdict"]}
    assert comp["population_units"] == REG.r4["population.interim"] + REG.r4["gate.G2.units"] - 1 == 17
    assert [o["cell_id"] for o in comp["out_of_population"]] == ["PAT-C3"]
    assert comp["survivals"] == 1 and comp["calibrated_evidence"] == 1 and comp["received_verdict"] == 2
    h = a["head"]
    assert "1 of the 17 frozen-11 population units survive" in h["headline"], h["headline"][:200]
    assert "tested-only fraction 1 / 2 = 0.500" in h["headline"] and RC.LOW_FRACTION in h["headline"]
    assert "PAT-C3" in h["population_restated"] and "G1's 196 population units" in h["listed_apart"]
    assert a["meta"]["interim_check"]["bound"] == 18
    by = {c["row"]: c for c in a["cells"]}
    assert by[rid["PAT-C3"]]["bh"]["family"].startswith("outside: flagged not reproduced")
    assert by[rid["PAT-C1"]]["reading"] == "survives \u2014 calibrated evidence"
    fam = [c for c in a["cells"] if (c.get("bh") or {}).get("family") == "in"]
    assert fam and [c["bh"]["q_interim_gate"] for c in fam] == RC.bh_q([c["bh"]["p_entered"] for c in fam])
    sw = next(c for c in a["cells"] if c["route"] == "descriptor: signed-weight rho (P15)")
    assert sw["reading"] == "descriptive (not a verdict)" and "S1c" in sw["legs"]
    shas = RC.write_outputs(a, root / "out", "G2")
    man = (root / "out" / "MANIFEST_claims.md").read_text(encoding="utf-8")
    assert "deferred (G2 not run)" not in man and "deferred (G1 not run)" in man
    return dict(units=comp["population_units"], survivals=comp["survivals"], family=len(fam), written=len(shas))


def sd7_tree(name, sens_extra=None):
    """An ungated tree with every pass: LIU-T4 / T5's descriptor records read R42 (d)'s fail-closed status (as the
    real descriptor pass fcbf98f does); optional extra sensitivity records {row: (outcome, status)}."""
    import a1_audit.forms as FM
    root = fresh(name)
    ident = identity()
    recs, plans = ungated_verdict_records(ident)
    write_pass(root, "ungated", "verdict", recs, ident, repro=ungated_repros(ident, recs))
    drecs = {n: descriptor_record(REG.rows[n], plans[n], ident, recs[n]) for n in recs}
    for cid in ("LIU-T4", "LIU-T5"):
        n = REG.by_cell_id[cid][0]
        drecs[n] = record(REG.rows[n], plans[n], "descriptor", ident, "no statistic", FM.SD7_UNMATCHED)
    write_pass(root, "ungated", "descriptor", drecs, ident)
    srecs = {}
    for n, rec in recs.items():
        p_ = plans[n]
        if rec["outcome"] == "computed" and p_["route"].startswith("verdict:"):
            srecs[n] = record(REG.rows[n], p_, "sensitivity", ident, "computed", RN.PARCELS_UNCHANGED,
                              dict(sensitivity="R11 >= 2-donor parcel set", parcel_set="unchanged",
                                   primary_result_sha256=RC.sha256_json(json.loads(dump(rec["result"])))))
        else:
            srecs[n] = record(REG.rows[n], p_, "sensitivity", ident, "no statistic",
                              rec["status_written"] or "no statistic: synthetic")
    for n, (out, st) in (sens_extra or {}).items():
        srecs[n] = record(REG.rows[n], plans[n], "sensitivity", ident, out, st)
    write_pass(root, "ungated", "sensitivity", srecs, ident)
    return root


CLAUSE_SD7 = ("(register R4 interim: 4 not auditable / 6 not testable as stated / 4 no calibrated test; at use: "
              "LIU-T4 / T5 not auditable (SD7 labels unmatched, R42 (d)) -> 6 / 6 / 2)")


@check("B1_register_interim_composition_asserted_and_at_use_stated")
def t_b1():
    """Skeptic B1: the register's interim composition (R4: 4 / 6 / 4) is asserted category by category, the at-use
    composition (LIU-T4 / T5 not auditable by R42 (d) -> 6 / 6 / 2) is derived apart, and the headline states both with
    the units that moved. Planted: a register block with the same total but other counts, and a composition whose
    'register' side was taken from the at-use flags, must both be refused (the old assert_interim passed both)."""
    root = sd7_tree("b1")
    a = RC.assemble(ROOT, root, "ungated")
    comp = a["comp"]
    caught = {}
    # planted 1 (behavioural, first): a register block with the same total (14) and the same can-survive (0) but the
    # at-use counts; the 4aa058a assert_interim compared the total and can-survive only, and let it through
    reg2 = copy.copy(REG)
    reg2.r4 = dict(REG.r4)
    reg2.r4["population.interim.not auditable"] = 6
    reg2.r4["population.interim.no calibrated test"] = 2
    caught["block"] = raises(RC.ReportRefused, RC.assert_interim, reg2, comp)[:110]
    # the headline states the register's composition and the at-use one, with the units that moved
    assert CLAUSE_SD7 in a["head"]["headline"], a["head"]["headline"]
    r4c = {k[len("population.interim."):]: v for k, v in REG.r4.items() if k.startswith("population.interim.")}
    assert r4c == {"not auditable": 4, "not testable as stated": 6, "no calibrated test": 4}, r4c
    assert RC.register_block_composition(REG.r4, "population.interim.") == r4c
    assert comp["composition_register"] == r4c, comp["composition_register"]
    assert comp["composition"] == {"not auditable": 6, "not testable as stated": 6, "no calibrated test": 2}
    assert [(m["cell_id"], m["category_register"], m["category_at_use"], m["reasons"][0]["rule"])
            for m in comp["moved_units"]] == [("LIU-T4", "no calibrated test", "not auditable", "RUN_PLAN_amend_2 R42 (d)"),
                                              ("LIU-T5", "no calibrated test", "not auditable", "RUN_PLAN_amend_2 R42 (d)")]
    ic = a["meta"]["interim_check"]
    assert ic["register_composition"] == r4c and ic["at_use_composition"] == comp["composition"]
    assert [m["cell_id"] for m in ic["moved_at_use"]] == ["LIU-T4", "LIU-T5"]
    RC.write_outputs(a, root / "out", "ungated")
    h = json.loads((root / "out/a1_run/ungated/headline.json").read_text(encoding="utf-8"))
    assert h["composition"]["composition_register"] == r4c and h["composition"]["composition"]["not auditable"] == 6
    assert [m["row"] for m in h["composition"]["moved_units"]] == [REG.by_cell_id["LIU-T4"][0],
                                                                  REG.by_cell_id["LIU-T5"][0]]
    md = (root / "out/a1_run/ungated/cells.md").read_text(encoding="utf-8")
    assert "| no calibrated test | 4 | 2 |" in md and "Units whose category moved at use" in md
    # planted 2: the register side read from the at-use flags (one composition for both)
    caught["merged"] = raises(RC.ReportRefused, RC.assert_interim, REG,
                              dict(comp, composition_register=dict(comp["composition"])))[:110]
    # no unit moved: the clause says so
    root0 = fresh("b1_none")
    ident = identity()
    recs, _ = ungated_verdict_records(ident)
    write_pass(root0, "ungated", "verdict", recs, ident)
    a0 = RC.assemble(ROOT, root0, "ungated")
    assert "(register R4 interim: 4 not auditable / 6 not testable as stated / 4 no calibrated test; no unit moved " \
           "at use)" in a0["head"]["headline"]
    return dict(caught=caught, composition=comp["composition"])


@check("B2_flags_and_status_at_use_from_every_pass")
def t_b2():
    """Skeptic B2: a cell's run flags come from every pass's record (descriptor and sensitivity too), and its effective
    status at use agrees with headline.json's units. A not-auditable status written only by the sensitivity pass
    (SEG-C3a, row 3) must reach the cell's flags, its status and the composition; a planted composition flag the
    cell does not carry is refused."""
    n3 = REG.by_cell_id["SEG-C3a"][0]
    root = sd7_tree("b2", sens_extra={n3: ("no statistic", "not auditable (map changed)")})
    a = RC.assemble(ROOT, root, "ungated")
    by = {c["row"]: c for c in a["cells"]}
    import a1_audit.forms as FM
    for cid in ("LIU-T4", "LIU-T5"):
        c = by[REG.by_cell_id[cid][0]]
        assert "not auditable" in c["flags"]["run"], c["flags"]
        assert [(d["pass"], d["status"]) for d in c["flags"]["run_detail"]] == [("descriptor", FM.SD7_UNMATCHED)]
        assert c["status_effective"] == FM.SD7_UNMATCHED and c["status_effective_tsv"] == REG.rows[c["row"]].status
        assert c["status_effective_source"].startswith("descriptor record at use")
        assert c["population"]["category"] == "not auditable" and c["population"]["category_register"] == \
            "no calibrated test"
    c3 = by[n3]
    assert "not auditable" in c3["flags"]["run"] and c3["status_effective"] == "not auditable (map changed)"
    assert c3["status_effective_source"].startswith("sensitivity record at use") and "\u00a717" in \
        c3["status_effective_source"]
    assert a["comp"]["composition"]["not auditable"] == 7 and a["comp"]["composition"]["not testable as stated"] == 5
    # every unit of headline.json agrees with its cell (flags and status at use)
    for u in a["comp"]["units"]:
        c = by[u["row"]]
        assert set(u["run_flags"]) <= set(c["flags"]["run"]), (u["row"], u["run_flags"], c["flags"]["run"])
        if u["moved"]:
            assert c["status_effective"] == u["moved"]["reasons"][0]["status"], u["row"]
        else:
            assert c["status_effective"] == c["status_effective_tsv"], u["row"]
    # a TSV not-auditable row keeps its TSV status (the records agree; nothing outranks it)
    c6 = by[REG.by_cell_id["LIU-T6"][0]]
    assert c6["status_effective"] == c6["status_effective_tsv"] and "not auditable" in c6["flags"]["run"]
    # planted: the composition reads a flag the cell does not carry
    orig = RC.run_flags

    def extra_flag(cells_by_row, gates, row):
        e, b, l5, pend = orig(cells_by_row, gates, row)
        if row.cell_id == "XING-FPV-all":
            e = set(e) | {"no calibrated test"}
        return e, b, l5, pend
    RC.run_flags = extra_flag
    try:
        msg = raises(RC.ReportRefused, RC.assemble, ROOT, root, "ungated")
    finally:
        RC.run_flags = orig
    assert "B2" in msg
    return dict(caught=msg[:110], composition=a["comp"]["composition"])


@check("status_rules_match_the_module_constants")
def t_rules():
    import a1_audit.forms as FM
    import a1_audit.wp3_layout as WL
    import a1_audit.wp3_sd7 as W7
    want = {FM.SD7_UNMATCHED: "RUN_PLAN_amend_2 R42 (d)", FM.LIU_T4_NO_CORTICAL: "RUN_PLAN_amend_2 R42 (e)",
            FM.LIU_ABAGEN_NOT_RUNNABLE: "RUN_PLAN R10 :659", W7.SD7_SHEET: "RUN_PLAN_amend_3 R46 (b)",
            W7.SD7_HEADER: "RUN_PLAN_amend_3 R46 (c)", W7.SD7_INTERRUPTED: "RUN_PLAN_amend_3 R46 (d)",
            WL.STATUS_MAP_CHANGED: "RUN_PLAN \u00a717 :1703-1704", WL.STATUS_LAYOUT: "RUN_PLAN \u00a78 step 4",
            V.R8_NOT_AUDITABLE: "RUN_PLAN R8 (A6: ARC.md:863-868)"}
    import a1_audit.wp4_layout as W4L
    import a1_audit.fetch_extract as FE
    stage = W4L.STATUS_STAGE_REFUSED
    want_g2 = {W4L.STATUS_PRE_LAYOUT: "R61", W4L.STATUS_GIA_LAYOUT: "R54", W4L.STATUS_GEDAR_LAYOUT: "R56",
               W4L.STATUS_R17: "R58", W4L.STATUS_UPSTREAM: "RUN_PLAN §8", stage % W4L.STATUS_UPSTREAM: "RUN_PLAN §8",
               stage % FE.STATUS_FAILED: "RUN_PLAN §8", stage % FE.STATUS_IN_QUARANTINE: "§8 step 6"}
    assert set(RC.G2_RUNTIME_RULES) == set(want_g2), set(RC.G2_RUNTIME_RULES) ^ set(want_g2)
    for st, frag in want_g2.items():
        assert frag in RC.G2_RUNTIME_RULES[st], (st, RC.G2_RUNTIME_RULES[st])
    for st, a7 in ((W4L.STATUS_PRE_LAYOUT, "A7"), (W4L.STATUS_GIA_LAYOUT, "A8"), (W4L.STATUS_R17, "A9")):
        assert a7 in RC.G2_RUNTIME_RULES[st]
    want.update(RC.G2_RUNTIME_RULES)
    assert RC.STATUS_RULES == want, set(RC.STATUS_RULES) ^ set(want)
    assert RC.short_reason(FM.SD7_UNMATCHED) == "SD7 labels unmatched"
    assert RC.short_rule("RUN_PLAN_amend_2 R42 (d)") == "R42 (d)" and RC.compress_ids(["LIU-T4", "LIU-T5"]) == \
        "LIU-T4 / T5"
    return {}


class _StubPass:
    def __init__(self, rows):
        self.rows = rows

    def complete(self):
        return True


class _StubGate:
    gate = "G2"
    rel = "a1_run/G2"

    def __init__(self, recs: dict):
        self.passes = {n: _StubPass(recs.get(n, {})) for n in RC.PASSES}

    def verdict_complete(self):
        return True


@check("g2_runtime_status_outranks_the_register_status_at_use")
def t_g2_runtime():
    """Skeptic (2026-11-02): a WP4 / G2 run-time status (eTable13 / Giacomel layout, GEDAR layout, R17 fallback,
    upstream refusal, quarantine) replaces the register status at use and cites its rule; the composition flags are
    unchanged by it. Planted: a status outside the rules keeps the register status."""
    import a1_audit.wp4_layout as W4L
    import a1_audit.fetch_extract as FE
    deferred = [r for r in REG.gate_rows("G2") if r.status.startswith("deferred") and "auditable (under G2)" in r.status
                and "not " not in r.status.split(";", 1)[-1]]
    assert deferred, "no deferred 'auditable (under G2)' row in the register"
    row = deferred[0]
    tsv = LD.effective_status(row, {"G2"})
    cases = [("verdict", W4L.STATUS_PRE_LAYOUT, "R61"), ("verdict", W4L.STATUS_GIA_LAYOUT, "R54"),
             ("descriptor", W4L.STATUS_GEDAR_LAYOUT, "R56"), ("descriptor", W4L.STATUS_R17, "R58"),
             ("verdict", W4L.STATUS_STAGE_REFUSED % FE.STATUS_IN_QUARANTINE, "step 6"),
             ("verdict", W4L.STATUS_UPSTREAM, "§8")]
    for pass_, st, frag in cases:
        recs = {pass_: {row.row: {"outcome": "not run", "status_written": st}}}
        if pass_ != "verdict":
            recs["verdict"] = {row.row: {"outcome": "no statistic", "status_written": "no statistic: x"}}
        rf = RC.record_run_flags(row, _StubGate(recs))
        got, src = RC.at_use_status(row, tsv, rf)
        assert got == st and frag in src and pass_ in src, (st, got, src)
        assert rf["extra"] == ({"not auditable"} if st.startswith("not auditable") else set()), rf["extra"]
    # the first pass in PASSES order wins
    recs = {"verdict": {row.row: {"outcome": "not run", "status_written": W4L.STATUS_PRE_LAYOUT}},
            "descriptor": {row.row: {"outcome": "not run", "status_written": RN.NOT_RUN_VERDICT_ABSENT}},
            "sensitivity": {row.row: {"outcome": "not run", "status_written": W4L.STATUS_GEDAR_LAYOUT}}}
    got, _ = RC.at_use_status(row, tsv, RC.record_run_flags(row, _StubGate(recs)))
    assert got == W4L.STATUS_PRE_LAYOUT, got
    # planted: a text outside the rules (the derivative 'verdict pass absent') keeps the register status
    recs = {"verdict": {row.row: {"outcome": "not run", "status_written": RN.NOT_RUN_VERDICT_ABSENT}}}
    got, src = RC.at_use_status(row, tsv, RC.record_run_flags(row, _StubGate(recs)))
    assert got == tsv and src.startswith("TSV"), (got, src)
    return dict(row=row.row, cases=len(cases))


@check("C3_component_r27_block_marked_not_to_be_quoted")
def t_c3():
    root = fresh("c3")
    ident = identity()
    recs, _ = ungated_verdict_records(ident)
    write_pass(root, "ungated", "verdict", recs, ident)
    a = RC.assemble(ROOT, root, "ungated")
    comp_cells = [c for c in a["cells"] if c.get("r27_note")]
    assert sorted(c["cell_id"] for c in comp_cells) == ["MOR-C1", "MOR-C2", "MOR-C3"]
    md = RC.cells_md("ungated", a["cells"], a["meta"], a["head"], a["comp"], a["desc"], a["bh"], REG)
    assert "## R27 blocks of component rows" in md and "ev-1a12dffe1a85af7" in md and "NOT TO BE QUOTED" in md
    for c in comp_cells:
        line = next(ln for ln in md.split("\n") if ln.startswith(f"| {c['row']} | {c['cell_id']} |"))
        assert "R27 block not to be quoted" in line, line
        assert c["reading"].startswith("does not pass at component level") or c["verdict"].get("descriptor_row"), \
            c["reading"]
        assert "species leg untested" not in line and "not detectable at this power" not in line, line
    return dict(rows=[c["cell_id"] for c in comp_cells])


def main() -> int:
    t0 = time.time()
    print(f"A1 report_cells tests: scratch {SCRATCH}", flush=True)
    for run in CHECKS:
        run()
    out = SCRATCH / "test_report_cells_results.json"
    out.write_text(json.dumps(A3.jsonable(dict(results=RESULTS, failed=FAILED, seconds=round(time.time() - t0, 1))),
                              indent=1) + "\n", encoding="utf-8", newline="\n")
    back = json.loads(out.read_text(encoding="utf-8"))
    assert back["failed"] == FAILED
    print(f"{len(CHECKS) - len(FAILED)} of {len(CHECKS)} checks passed ({time.time() - t0:.0f}s); results {out}",
          flush=True)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
