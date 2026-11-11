"""Tests of the WP2 review fixes that change no plant rule (plain script; exits non-zero on failure).

    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_wp2r_fixes [--slow] [--dev-root DIR]

Material: synthetic data and the DEV plant records (the plants worker's scratchpad wp2/dev1 ... dev4, declared seen in
RUN_PLAN_amend_2 §8.2); never an official output. Everything written goes to a temp directory, removed at the end.

 B2  plants_dev_compare: dev2 vs dev3 on their shared cases (P24-P26) -> no difference; a synthetic official-like copy
     of dev3 with planted differences (a p, a decision, a seed key, a removed field, a removed case, a 1e-16 change)
     -> exactly those reported, with category, values and the tolerance flag; a planted DEV-pass disagreement found;
     malformed input refused; the report read back; exit codes.
 B3  plants_official_check: the DEV outputs (dev4) are refused (DEV mode, 'not evaluated'); a synthetic official tree
     built from dev4's headers passes; each planted defect (missing plant, a 'not evaluated' criterion, an outcome
     count, a short cell, a cases-file hash, a cases-file line count, a §8.1b constant, a DEV stamp) fails exactly
     that plant.
 B1  plants_p25a_rescore, record level: every DEV (a)(b) record (G6l ok) re-scores to its recorded decision; synthetic
     degenerate / unmatched records follow the decided / needs-recomputation rule; inconsistent records refused.
     --slow: three DEV cases recomputed from their plant keys (p25.P25.run_case, frozen gate beside): every p,
     decision, status and seed key reproduced, frozen gate = plant for G6l ok; one case with the G6l status patched
     to 'degenerate' in memory: the plant leg loses its G6l p, the frozen gate keeps it; the cost per case reported.
 B4  every real-path opener outside fetch refuses a path under a (scratch) quarantine root and any '_quarantine'
     component: identity.file_facts / load_prefreeze, reparcel.load_atlas_verified / read_annot / read_gifti_values,
     ahba_extras.load_r12_ds, run.RealSources.real_path (and a WP3-style subclass loader through it); a path outside
     passes the check; fetch's own identity step passes its roots' quarantine root.
 C9  fetch_extract's do-not-open check compares casefolded, stripped names (both sites: the declaration check and
     the access-log check), with planted variants.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--slow", action="store_true")
ap.add_argument("--dev-root", default=None, help="the DEV outputs' parent (holding dev1 ... dev4)")
ARGS, _ = ap.parse_known_args()

from a1_audit import run as R  # noqa: E402
from a1_audit import plants_dev_compare as DC  # noqa: E402
from a1_audit import plants_official_check as OC  # noqa: E402
from a1_audit import plants_p25a_rescore as RS  # noqa: E402

DEV_ROOT = Path(ARGS.dev_root) if ARGS.dev_root else (Path(__file__).resolve().parents[3] / "run_manifests" / "plants" / "DEV")  # committed DEV records (amend_2 §8.2)
TMP = Path(tempfile.mkdtemp(prefix="a1_wp2r_fixes_"))
RESULTS, FAILED = {}, []


def check(name):
    def deco(fn):
        t0 = time.time()
        try:
            out = fn() or {}
            RESULTS[name] = dict(result="pass", seconds=round(time.time() - t0, 2), **out)
            print(R.ascii_line(f"PASS {name} {json.dumps(out)[:500]}"), flush=True)
        except (Exception, SystemExit) as e:  # noqa: BLE001
            FAILED.append(name)
            RESULTS[name] = dict(result="FAIL", error=f"{type(e).__name__}: {e}")
            print(R.ascii_line(f"FAIL {name}: {type(e).__name__}: {e}"), flush=True)
            print(R.ascii_line(traceback.format_exc()), flush=True)
        return fn
    return deco


def raises(exc, f, *a, **k) -> str:
    try:
        f(*a, **k)
    except exc as e:  # noqa: BLE001
        return f"{type(e).__name__}: {str(e)[:60]}"
    raise AssertionError(f"{getattr(f, '__name__', f)} did not raise {exc.__name__}")


def read_rows(path: Path) -> list:
    return [json.loads(x) for x in Path(path).read_bytes().decode("utf-8").splitlines()]


def write_rows(path: Path, rows: list) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_bytes(("\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n").encode("utf-8"))


def dev(name: str) -> Path:
    d = DEV_ROOT / name
    if not d.is_dir():
        raise FileNotFoundError(f"DEV directory {d}")
    return d


# ================================================================================================================
# B2: plants_dev_compare
# ================================================================================================================
@check("B2_dev2_vs_dev3_shared_cases_no_difference")
def t_b2_devdev():
    out = TMP / "b2_devdev.json"
    rc = DC.main(["--dev", str(dev("dev2")), "--official", str(dev("dev3")), "--plants", "P24,P25,P26",
                  "--out", str(out)])
    doc = json.loads(out.read_bytes().decode("utf-8"))
    assert rc == 0 and doc["result"] == "no difference", (rc, doc["result"])
    cmp = {p: v["compared"] for p, v in doc["by_plant"].items()}
    assert cmp == {"P24": 36, "P25": 24, "P26": 18}, cmp
    assert doc["totals"]["differences"] == 0 and doc["n_dev_passes_disagree"] == 0
    assert doc["headers"]["P25"]["official"]["mode"] == "DEV"     # the 'official' side here is a DEV pass (recorded)
    return dict(compared=cmp, compare_result=doc["result"])


def plant_differences(src: Path, dst: Path) -> list:
    """Copy src's P24 / P25 / P26 into dst with planted differences; returns [(plant, cell, case, field, kind)]."""
    planted = []
    for pid in ("P24", "P25", "P26"):
        shutil.copytree(src / pid, dst / pid)
    f25 = dst / "P25" / "cases_P25.jsonl"
    rows = read_rows(f25)
    by = {(r["cell"], r["i"]): r for r in rows}
    a0 = by[("V-AAL / (a)(b) T-brain brand-300", 2)]
    a0["v2"]["p_max"]["+"] = a0["v2"]["p_max"]["+"] + 0.01
    planted.append(("P25", a0["cell"], a0["case"], "v2/p_max/+", "p"))
    a1 = by[("V-DK / (a)(b) T-brain brand-300", 1)]
    a1["correct"]["rejects"] = not a1["correct"]["rejects"]
    planted.append(("P25", a1["cell"], a1["case"], "correct/rejects", "decision"))
    a2 = by[("V-AAL / (c) between-class", 3)]
    a2["correct"]["uninformative_share"] = a2["correct"]["uninformative_share"] * (1 + 1e-15)
    planted.append(("P25", a2["cell"], a2["case"], "correct/uninformative_share", "number (within 1e-12)"))
    a3 = by[("V-DK / (c) between-class", 0)]
    del a3["cluster"]["share"]
    planted.append(("P25", a3["cell"], a3["case"], "cluster/share", "absent"))
    gone = by[("V-AAL / (a)(b) T-brain brand-300", 4)]
    rows = [r for r in rows if r is not gone]
    write_rows(f25, rows)
    f26 = dst / "P26" / "cases_P26.jsonl"
    rows26 = read_rows(f26)
    b0 = [r for r in rows26 if r["cell"] == "V-DK" and r["i"] == 5][0]
    b0["seeds"]["legs"][0]["key"]["entropy"][3] += 1
    planted.append(("P26", b0["cell"], b0["case"], "seeds/legs/0/key/entropy", "seed key"))
    write_rows(f26, rows26)
    return planted, (gone["cell"], gone["case"])


@check("B2_planted_differences_reported_exactly")
def t_b2_planted():
    off = TMP / "b2_official_like"
    planted, gone = plant_differences(dev("dev3"), off)
    out = TMP / "b2_planted.json"
    rc = DC.main(["--dev", f"{dev('dev2')},{dev('dev1')}", "--official", str(off), "--plants", "P24,P25,P26",
                  "--out", str(out), "--commit", "abc1234"])
    doc = json.loads(out.read_bytes().decode("utf-8"))
    assert rc == 1 and doc["commit"] == "abc1234"
    diffs = [(p, d["cell"], d["case"], d["field"]) for p, v in doc["by_plant"].items() for d in v["differences"]]
    want = {(p, c, k, f) for p, c, k, f, _ in planted}
    got = set(diffs)
    # a planted case may be in dev1 and dev2 (dev1: i < 2): each DEV pass reports it
    assert got == want, f"reported {sorted(got - want)} extra, {sorted(want - got)} missing"
    cats = {(d["field"]): (d["category"], d["within_rel_1e-12"], d["dev"], d["official"])
            for v in doc["by_plant"].values() for d in v["differences"]}
    assert cats["v2/p_max/+"][0] == "p" and not cats["v2/p_max/+"][1]
    assert abs(cats["v2/p_max/+"][3] - cats["v2/p_max/+"][2] - 0.01) < 1e-12
    assert cats["correct/rejects"][0] == "decision" and cats["correct/rejects"][2] != cats["correct/rejects"][3]
    assert cats["correct/uninformative_share"][0] == "number" and cats["correct/uninformative_share"][1] is True
    assert cats["cluster/share"][3] == DC.ABSENT and cats["cluster/share"][0] == "number"
    assert cats["seeds/legs/0/key/entropy"][0] == "seed key"
    t = doc["totals"]
    assert t["differences_within_rel_1e_12"] == sum(1 for v in doc["by_plant"].values() for d in v["differences"]
                                                    if d["within_rel_1e-12"])
    gone_only = [x for x in doc["by_plant"]["P25"]["dev_only"] if (x["cell"], x["case"]) == gone]
    assert gone_only and all(x["dev_source"] == "dev2" for x in gone_only), gone_only   # dev1 holds i < 2 only
    assert doc["by_plant"]["P24"]["n_differences"] == 0
    return dict(planted=len(planted), reported=len(diffs), records_with_differences=t["records_with_differences"],
                within_1e12=t["differences_within_rel_1e_12"], material=t["differences_material"])


@check("B2_dev_pass_disagreement_and_refusals")
def t_b2_refusals():
    d1 = TMP / "b2_dev1x" / "dev1x"
    shutil.copytree(dev("dev1") / "P24", d1 / "P24")
    f = d1 / "P24" / "cases_P24.jsonl"
    rows = read_rows(f)
    rows[0]["kinds"]["rand-25"]["decoded_list"]["rejects"] = not rows[0]["kinds"]["rand-25"]["decoded_list"]["rejects"]
    write_rows(f, rows)
    doc = DC.compare([d1, dev("dev2")], dev("dev3"), ["P24"])
    dis = doc["by_plant"]["P24"]["dev_passes_disagree"]
    assert len(dis) == 1 and dis[0]["field"] == "kinds/rand-25/decoded_list/rejects", dis
    assert doc["by_plant"]["P24"]["n_differences"] == 1                  # dev1x vs dev3 as well
    out = {}
    dup = TMP / "b2_dup" / "P24"
    dup.mkdir(parents=True)
    write_rows(dup / "cases_P24.jsonl", rows + rows[:1])
    out["duplicate"] = raises(DC.Refused, DC.load_cases, dup / "cases_P24.jsonl", "P24")
    out["other plant"] = raises(DC.Refused, DC.load_cases, f, "P25")
    bad = dict(rows[0])
    del bad["case"]
    write_rows(dup / "cases_P24.jsonl", [bad])
    out["no case"] = raises(DC.Refused, DC.load_cases, dup / "cases_P24.jsonl", "P24")
    assert DC.main(["--dev", str(d1), "--official", str(TMP / "nowhere"), "--out", str(TMP / "x.json")]) == 2
    assert DC.main(["--dev", str(d1), "--official", str(dev("dev3")), "--out", str(TMP / "cases_P24.jsonl")]) == 2
    p = DC.default_out("abc1234")
    assert p == DC.REPO / "arcs/audit/run_manifests/plants/DEV_vs_OFFICIAL_abc1234.json", p
    raises(DC.Refused, DC.default_out, "../x")
    return out


# ================================================================================================================
# B3: plants_official_check
# ================================================================================================================
def official_like(src: Path, dst: Path, pinned: dict) -> None:
    """A synthetic official tree from a DEV pass's plant files: mode OFFICIAL, no stamp, every criterion evaluated
    (a DEV 'not evaluated' rewritten 'PASS' with the outcome recounted), n_run = n_official, §8.1b constants."""
    for pd in sorted(p for p in src.iterdir() if p.is_dir() and DC.PLANT_RE.fullmatch(p.name)):
        pid = pd.name
        (dst / pid).mkdir(parents=True)
        doc = json.loads((pd / f"plant_{pid}.json").read_bytes().decode("utf-8"))
        doc["mode"], doc["stamp"] = "OFFICIAL", None
        for _, c in OC.walk_criteria(doc["cells"]):
            if str(c["result"]).startswith("not evaluated"):
                c["result"] = "PASS"
        for c in doc["cells"].values():
            c["n_run"] = c["n_official"]
        kinds = [OC.classify(c["result"]) for _, c in OC.walk_criteria(doc["cells"])]
        doc["outcome"] = dict(n_criteria=len(kinds), n_PASS=kinds.count("PASS"), n_FAIL=kinds.count("FAIL"),
                              n_CAUGHT=kinds.count("CAUGHT"), n_NOT_CAUGHT=kinds.count("NOT CAUGHT"),
                              n_not_evaluated=kinds.count("not evaluated"), n_reported=kinds.count("reported"),
                              criteria=[])
        doc["plant_constants"] = dict(values=copy.deepcopy(pinned))
        data = (pd / f"cases_{pid}.jsonl").read_bytes()
        (dst / pid / f"cases_{pid}.jsonl").write_bytes(data)
        doc["cases_file"] = dict(name=f"cases_{pid}.jsonl", sha256=hashlib.sha256(data).hexdigest(),
                                 n=len(data.decode("utf-8").splitlines()))
        (dst / pid / f"plant_{pid}.json").write_bytes(json.dumps(doc, indent=1).encode("utf-8"))


def edit_plant(root: Path, pid: str, fn) -> None:
    f = root / pid / f"plant_{pid}.json"
    doc = json.loads(f.read_bytes().decode("utf-8"))
    fn(doc)
    f.write_bytes(json.dumps(doc, indent=1).encode("utf-8"))


@check("B3_official_check_dev_refused_synthetic_passes_planted_defects_fail")
def t_b3():
    from a1_audit.plants import driver as D
    docd = OC.check(dev("dev4"))
    assert set(docd["incomplete"]) == set(D.ORDER), docd["incomplete"]
    assert all(any(pr.startswith("not an official run") for pr in p["problems"]) for p in docd["plants"])
    assert sum("n_not_evaluated" in " ".join(p["problems"]) for p in docd["plants"]) == 11   # P5, P7: 0 in DEV too
    base = TMP / "b3_base"
    official_like(dev("dev4"), base, D.PINNED_CONSTANTS)
    good = OC.check(base)
    assert not good["incomplete"], [(p["plant"], p["problems"]) for p in good["plants"] if p["problems"]]
    assert OC.main(["--root", str(base), "--out", str(TMP / "b3_good.json")]) == 0
    back = json.loads((TMP / "b3_good.json").read_bytes().decode("utf-8"))
    assert back["result"] == "every plant complete"

    def nev(doc):
        c = OC.walk_criteria(doc["cells"])[0][1]
        c["result"] = "not evaluated (DEV run at n = 1; the criterion is stated for n = 300)"

    def short(doc):
        next(iter(doc["cells"].values()))["n_run"] = 299

    def oc(doc):
        doc["outcome"]["n_not_evaluated"] = 1

    def const(doc):
        doc["plant_constants"]["values"]["PLANT_K"]["site"] = 501

    def sha(doc):
        doc["cases_file"]["sha256"] = "0" * 64

    def nlines(doc):
        doc["cases_file"]["n"] += 1

    def stamp(doc):
        doc["stamp"] = "DEV (launch refused: L11)"

    def unclassified(doc):
        OC.walk_criteria(doc["cells"])[0][1]["result"] = "maybe"

    plants = dict(missing="P26", not_evaluated="P24", outcome_count="P25", short_cell="P4", constants="P12",
                  cases_sha="P3a", cases_lines="P8", dev_stamp="P11", unclassified="P22")
    edits = dict(not_evaluated=nev, outcome_count=oc, short_cell=short, constants=const, cases_sha=sha,
                 cases_lines=nlines, dev_stamp=stamp, unclassified=unclassified)
    out = {}
    for what, pid in plants.items():
        root = TMP / f"b3_{what}"
        shutil.copytree(base, root)
        if what == "missing":
            shutil.rmtree(root / pid)
        else:
            edit_plant(root, pid, edits[what])
        doc = OC.check(root)
        assert doc["incomplete"] == [pid], (what, doc["incomplete"])
        assert OC.main(["--root", str(root)]) == 1
        out[what] = next(p["problems"] for p in doc["plants"] if p["plant"] == pid)[0][:60]
    assert OC.main(["--root", str(TMP / "nowhere")]) == 2
    assert "deferred" in OC.__doc__.lower() and "driver.py is pinned" in OC.__doc__
    return out


# ================================================================================================================
# B1: P25 (a) as frozen, record level
# ================================================================================================================
@check("B1_dev_records_rescore_to_recorded")
def t_b1_dev():
    out = {}
    for name in ("dev1", "dev2", "dev3", "dev4"):
        doc = RS.rescore(dev(name) / "P25" / "cases_P25.jsonl", "none")
        for cell, c in doc["by_cell"].items():
            assert c["n_undecided"] == 0 and c["k_frozen"] == c["k_official"] and c["n_decision_changed"] == 0, c
            assert c["n_by_g6l_status"] == {"ok": c["n"]} and c["n_by_basis"] == {RS.BASIS_OK: c["n"]}
            assert "BESIDE" in c["note"]
        out[name] = sum(c["n"] for c in doc["by_cell"].values())
    return dict(ab_records=out, total=sum(out.values()), g6l_status="ok in every record")


def synthetic_ab(base: dict, status: str, g1: float, g6s: float) -> dict:
    r = copy.deepcopy(base)
    r["correct"]["g6l"]["status"] = status
    r["correct"]["g6l"]["pool_jaccard"] = .6 if status == "degenerate" else None
    r["correct"]["p"]["G6l"] = None
    r["v2"]["p"]["G1 (whole, unconditioned)"] = {"+": g1, "-": 1 - g1}
    r["v2"]["p"]["G6s (centred on mu^w)"] = {"+": g6s, "-": 1 - g6s}
    r["v2"]["p"]["G6l (own windows, unconditioned)"] = None
    r["v2"]["p_max"] = None
    r["v2"]["rejects"] = False
    return r


@check("B1_record_rules_degenerate_unmatched_refusals")
def t_b1_rules():
    rows = read_rows(dev("dev3") / "P25" / "cases_P25.jsonl")
    base = [r for r in rows if r["part"] == "ab"][0]
    a = RS.rescore_record(synthetic_ab(base, "degenerate", .30, .01))
    assert a["basis"] == RS.BASIS_DECIDED and a["frozen_rejects"] is False and a["frozen_p_max_plus_lower_bound"] == .30
    b = RS.rescore_record(synthetic_ab(base, "degenerate", .001, .02))
    assert b["basis"] == RS.BASIS_NEEDS and b["frozen_rejects"] is None
    c = RS.rescore_record(synthetic_ab(base, "unmatched", .001, .001))
    assert c["basis"] == RS.BASIS_UNMATCHED and c["frozen_rejects"] is False
    ok = RS.rescore_record(base)
    assert ok["basis"] == RS.BASIS_OK and ok["frozen_rejects"] == base["v2"]["rejects"]
    refusals = {}
    bad = copy.deepcopy(base)
    bad["v2"]["p"]["G6l (own windows, unconditioned)"] = None              # ok status without a G6l p
    refusals["ok without p"] = raises(RS.Refused, RS.rescore_record, bad)
    bad = copy.deepcopy(base)
    bad["v2"]["rejects"] = not bad["v2"]["rejects"]                          # decision not the rule on its p's
    refusals["decision"] = raises(RS.Refused, RS.rescore_record, bad)
    bad = synthetic_ab(base, "weird", .3, .3)
    refusals["status"] = raises(RS.Refused, RS.rescore_record, bad)
    refusals["part c"] = raises(RS.Refused, RS.rescore_record, [r for r in rows if r["part"] == "c"][0])
    # a synthetic cases file: 1 ok + decided + needs -> bounds, no criterion
    f = TMP / "b1_syn" / "P25" / "cases_P25.jsonl"
    syn = [base, dict(synthetic_ab(base, "degenerate", .30, .01), i=1, case=1),
           dict(synthetic_ab(base, "degenerate", .001, .02), i=2, case=2)]
    write_rows(f, syn)
    doc = RS.rescore(f, "none")
    c = doc["by_cell"][base["cell"]]
    assert c["n"] == 3 and c["n_undecided"] == 1 and c["k_frozen"] is None
    assert c["k_frozen_bounds"] == [int(base["v2"]["rejects"]), int(base["v2"]["rejects"]) + 1]
    assert c["criterion_beside"]["result"].startswith("not decided")
    assert RS.main(["--cases", str(f), "--recompute", "none", "--out", str(TMP / "b1_syn.json")]) == 1  # undecided
    assert RS.main(["--cases", str(f), "--recompute", "none", "--out", str(TMP / "cases_x.json")]) == 2
    return dict(refusals=refusals, bounds=c["k_frozen_bounds"])


if ARGS.slow:
    @check("B1_recompute_three_dev_cases_and_degenerate_branch")
    def t_b1_recompute():
        from a1_audit.plants import common as C
        rows = DC.load_cases(dev("dev3") / "P25" / "cases_P25.jsonl", "P25")
        picks = [("V-AAL / (a)(b) T-brain brand-300", 0), ("V-AAL / (a)(b) T-brain brand-300", 1),
                 ("V-DK / (a)(b) T-brain brand-300", 0)]
        out, secs = {}, []
        for cell, case in picks:
            rec = rows[(cell, case)]
            rc = RS.recompute(rec["cell"], rec["i"])
            got = RS.rescore_recomputed(rec, rc)     # refuses unless p's, decisions, statuses, seed keys reproduce
            assert got["frozen_rejects"] == rec["v2"]["rejects"] and rc["frozen"]["p"] == rec["v2"]["p"]
            secs.append(rc["seconds"])
            out[f"{cell[:6]} i{rec['i']}"] = dict(seconds=rc["seconds"], n_windows=rc["n_windows"],
                                                  tolerated=[d["field"] for d in got["tolerated_number_differences"]])
        # the degenerate branch: species_only patched in memory to report the G6l pool 'degenerate'
        rec = rows[picks[0]]
        orig = C.species_only

        def degenerate(*a, **k):
            sp = orig(*a, **k)
            sp["g6l"] = dict(sp["g6l"], status="degenerate")
            sp["status"] = dict(sp["status"], G6l="degenerate")
            sp["p"] = dict(sp["p"], G6l=None)
            return sp
        C.species_only = degenerate
        try:
            rc = RS.recompute(rec["cell"], rec["i"])
        finally:
            C.species_only = orig
        assert C.species_only is orig
        plant_v2 = rc["record"]["v2"]
        assert rc["plant_status"] == "degenerate" and plant_v2["p"]["G6l (own windows, unconditioned)"] is None
        assert plant_v2["p_max"] is None and plant_v2["rejects"] is False           # the pinned plant rule
        assert rc["frozen"]["p"] == rec["v2"]["p"] and rc["frozen"]["p_max"] == rec["v2"]["p_max"]   # frozen gate
        mean = sum(secs) / len(secs)
        return dict(cases=out, mean_seconds=round(mean, 2), degenerate_branch="plant G6l None, frozen G6l kept",
                    note="seconds of a fresh single process (contexts cached after the first case)")


# ================================================================================================================
# B4: quarantine refusal in every real-path opener outside fetch
# ================================================================================================================
@check("B4_real_path_openers_refuse_quarantine")
def t_b4():
    from a1_audit import ahba_extras as AX
    from a1_audit import fetch_extract as FE
    from a1_audit import identity as ID
    from a1_audit import reparcel as RP
    q = TMP / "b4" / "qroot"              # a scratch quarantine root (no '_quarantine' in its name)
    inside = q / "G2" / "k" / "carrier.nii.gz"
    inside.parent.mkdir(parents=True)
    inside.write_bytes(b"synthetic")
    outside = TMP / "b4" / "data" / "file.bin"
    outside.parent.mkdir(parents=True)
    outside.write_bytes(b"synthetic\r\n")
    comp = TMP / "b4" / "x" / "_Quarantine" / "f.bin"
    comp.parent.mkdir(parents=True)
    comp.write_bytes(b"synthetic")
    openers = {
        "identity.file_facts": lambda p, root: ID.file_facts(p, quarantine_root=root),
        "identity.load_prefreeze": lambda p, root: ID.load_prefreeze(p, quarantine_root=root),
        "reparcel.load_atlas_verified": lambda p, root: RP.load_atlas_verified(p, "0" * 64, quarantine_root=root),
        "reparcel.read_annot": lambda p, root: RP.read_annot(p, quarantine_root=root),
        "reparcel.read_gifti_values": lambda p, root: RP.read_gifti_values(p, quarantine_root=root),
        "ahba_extras.load_r12_ds": lambda p, root: AX.load_r12_ds(p.parent, quarantine_root=root),
        "run.RealSources.real_path": lambda p, root: type("RS", (R.RealSources,), {"quarantine_root": root})()
        .real_path(p),
    }
    out = {}
    for name, f in openers.items():
        a = raises(PermissionError, f, inside, q)
        b = raises(PermissionError, f, comp, None)
        out[name] = [a[:40], b[:40]]
    # a path outside passes the check (the opener goes on to its own work / refusal, never a PermissionError)
    facts = ID.file_facts(outside, quarantine_root=q)
    assert facts["bytes"] == 11 and facts["has_crlf"]
    assert R.RealSources().real_path(outside) == outside
    for name in ("reparcel.load_atlas_verified",):
        raises(RP.ReparcelRefused, openers[name], outside, q)        # passes the check, then its sha256 refusal
    raises(AX.AB.BuildError, openers["ahba_extras.load_r12_ds"], outside, q)   # passes, then 'no build record'

    class WP3Like(R.RealSources):           # a WP3 loader inherits the check through real_path
        quarantine_root = q

        def map(self, plan, map_index):
            return self.real_path(inside).read_bytes()
    raises(PermissionError, WP3Like().map, {}, 0)
    # the default root is the production quarantine root
    assert FE.Roots.production().quarantine == Path("E:/data/asdg/_quarantine")
    raises(PermissionError, FE.refuse_quarantine_opener, Path("E:/data/asdg/_quarantine/G2/k/c.xlsx"))
    raises(PermissionError, FE.refuse_quarantine_opener, Path("E:/DATA/ASDG/_QUARANTINE/G2/k/c.xlsx"))
    assert FE.refuse_quarantine_opener(outside) == outside
    # fetch's identity step hands its roots' quarantine root to identity.file_facts
    import inspect
    assert "ID.file_facts(path, quarantine_root=roots_q)" in inspect.getsource(FE._identity)
    assert "_identity(t, path, em, rec, roots.quarantine)" in inspect.getsource(FE._body)
    return out


# ================================================================================================================
# C9: do-not-open names casefolded and stripped
# ================================================================================================================
@check("C9_do_not_open_casefold_strip")
def t_c9():
    from a1_audit import fetch_extract as FE
    dno = FE.MOREAU_DO_NOT_OPEN
    out = {}
    for name in ("5_BIV", "5_biv", " 5_BIV", "5_Biv\t", "\u00a06_asd", "9_RANKING "):
        hits = FE.do_not_open_hits({name}, dno)
        assert hits == {name}, (name, hits)
        out[repr(name)] = "refused"
    for name in ("1_16p11.2Del", "3_22q11.2Del", "5_BIV_extra", "x5_BIV"):
        assert not FE.do_not_open_hits({name}, dno), name
    # both sites of fetch_extract use it (the declaration check and the access-log check)
    import inspect
    src = inspect.getsource(FE._read_workbook)
    assert src.count("do_not_open_hits(") == 2, src.count("do_not_open_hits(")
    assert "declared & set(do_not_open)" not in src and "& set(do_not_open)" not in src
    return out


def main() -> int:
    n = len(RESULTS)
    print(f"{n - len(FAILED)} of {n} checks passed", flush=True)
    shutil.rmtree(TMP, ignore_errors=True)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
