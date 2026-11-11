"""Scoring tests of the WP2 plants that kill the WP2 review's mutations M1-M7 (plain script; exits non-zero on failure).

    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_plants_scoring [--slow]

plants/ and plant_mode.py are pinned (RUN_PLAN_amend_2 §8.1): they are imported read-only. Every mutant is an
in-memory patch (the function's source with one snippet replaced, compiled in its own module's globals, set on its
module / class, restored in a finally); no file is written except the write_plant check's outputs in a temp directory.
Synthetic inputs only (no class context is loaded, except under --slow).

Checks:
 (1) species_rejects: max (not min) over G1, G3m, G6s, G6l in the asked direction; a missing leg, an uninformative claim
     or a floor >= .025 is a non-rejection; through p24.species_record (the production caller).          [M1, M2]
 (2) below: reads the asked direction ('+' for PLUS, '-' for MINUS), strict < .025, a missing p is no rejection; and
     base.leg_rates counts in the asked direction.                                                          [M3]
 (3) P3b: survivors and the criterion's k count the ONE-SIDED '+' verdicts (two-sided R1 reported beside).   [M4]
 (4) driver.write_plant (replace_unmatched): unmatched cases are kept in the written cases but never count towards n:
     n computed = n wanted, the cases written stop at the n-th computed one.                                 [M5]
 (5) P26: the site p = max(p_S1c, p_S2c) per direction (prereg_amend_3.md:74), site_rejects on it; run_case with a
     synthetic adapter (C.prepare / construct patched in memory).                                            [M6]
 (6) run.validate on a REAL run (no --plant): every --K other than the registered counts is refused, not only the
     literal 'plant' (site=500, species=200, a mixed list, ...); 'audit' and no --K pass.                      [M7]
 (7) mutants: each of M1, M2, M3, M4a, M4b, M5a, M5b, M6, M7 applied in memory must make its check fail; the check
     passes again after the restore.
 (8) --slow: P26.run_case on the real dk-ctx context reproduces the DEV record of case 0 (dev3) field for field.
"""
from __future__ import annotations

import __future__
import argparse
import inspect
import json
import shutil
import sys
import tempfile
import textwrap
import time
import traceback
import types
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--slow", action="store_true")
ap.add_argument("--dev-dir", default=None, help="--slow: a DEV output directory holding P26/cases_P26.jsonl")
ARGS, _ = ap.parse_known_args()

from a1_audit import run as R  # noqa: E402
from a1_audit.plants import base as BS  # noqa: E402
from a1_audit.plants import common as C  # noqa: E402
from a1_audit.plants import construct as CO  # noqa: E402
from a1_audit.plants import criteria as CR  # noqa: E402
from a1_audit.plants import driver as D  # noqa: E402
from a1_audit.plants import p03, p24, p26  # noqa: E402

RESULTS, FAILED = {}, []
LEGS4 = ("G1", "G3m", "G6s", "G6l")


def check(name):
    def deco(fn):
        t0 = time.time()
        try:
            out = fn() or {}
            RESULTS[name] = dict(result="pass", seconds=round(time.time() - t0, 2), **out)
            print(R.ascii_line(f"PASS {name} {json.dumps(out)[:400]}"), flush=True)
        except (Exception, SystemExit) as e:  # noqa: BLE001  (run.RunRefused is a SystemExit)
            FAILED.append(name)
            RESULTS[name] = dict(result="FAIL", error=f"{type(e).__name__}: {e}")
            print(R.ascii_line(f"FAIL {name}: {type(e).__name__}: {e}"), flush=True)
            print(R.ascii_line(traceback.format_exc()), flush=True)
        return fn
    return deco


# ---- (1) species_rejects ---------------------------------------------------------------------------------------------
def sp_of(plus: dict, unin: bool = False, floor: float = 1 / 201) -> dict:
    """A species_only-shaped record: p's {PLUS: p, MINUS: 1 - p} per leg (None: no p), floors, the flag."""
    return dict(p={k: (None if v is None else {C.PLUS: float(v), C.MINUS: 1.0 - float(v)}) for k, v in plus.items()},
                floors={k: floor for k in LEGS4}, uninformative=unin, uninformative_share=0.3,
                status={k: "ok" for k in LEGS4}, g6l=dict(status="ok", n_used=200, draws=200, eligible=200))


def chk_species_rejects() -> dict:
    out = {}
    cases = [  # (name, plus p's, uninformative, floor, want(+))
        ("all below", dict(G1=.01, G3m=.01, G6s=.01, G6l=.01), False, 1 / 201, True),
        ("max above (min below)", dict(G1=.001, G3m=.002, G6s=.003, G6l=.03), False, 1 / 201, False),
        ("max exactly .025", dict(G1=.001, G3m=.025, G6s=.003, G6l=.004), False, 1 / 201, False),
        ("uninformative", dict(G1=.001, G3m=.002, G6s=.003, G6l=.004), True, 1 / 201, False),
        ("G6l without p", dict(G1=.001, G3m=.002, G6s=.003, G6l=None), False, 1 / 201, False),
        ("floor at .025", dict(G1=.001, G3m=.002, G6s=.003, G6l=.004), False, .025, False),
    ]
    for name, plus, unin, floor, want in cases:
        sp = sp_of(plus, unin, floor)
        got = C.species_rejects(sp, C.PLUS)
        assert got is want or got == want, f"species_rejects {name}: {got} != {want}"
        rec = p24.species_record(sp)          # the production caller (P24 / P25 records)
        assert rec["rejects"] == want, f"p24.species_record {name}: rejects {rec['rejects']} != {want}"
        out[name] = bool(got)
    # direction: small p(-) rejects in MINUS only
    sp = sp_of(dict(G1=.995, G3m=.99, G6s=.98, G6l=.999))
    assert C.species_rejects(sp, C.MINUS) and not C.species_rejects(sp, C.PLUS), "direction"
    sp = sp_of(dict(G1=.995, G3m=.99, G6s=.98, G6l=.5))          # max p(-) = .5
    assert not C.species_rejects(sp, C.MINUS), "MINUS uses the max over the legs"
    return out


# ---- (2) below ---------------------------------------------------------------------------------------------------------
def chk_below() -> dict:
    lo_plus, lo_minus = {"+": .01, "-": .99}, {"+": .99, "-": .01}
    assert C.below(lo_plus) is True and C.below(lo_plus, C.PLUS) is True, "below({'+': .01, '-': .99}) in +"
    assert C.below(lo_plus, C.MINUS) is False, "below({'+': .01, '-': .99}) in -"
    assert C.below(lo_minus, C.MINUS) is True and C.below(lo_minus) is False, "below({'+': .99, '-': .01})"
    assert C.below(None) is False and C.below({"+": None, "-": .01}) is False
    assert C.below({"+": .025, "-": .5}) is False, "strict < .025"
    assert C.below({"+": .0249, "-": .5}) is True
    # base.leg_rates counts in the asked direction (P4 / P5 / P3b summaries)
    recs = [dict(legs={"Level 0": lo_plus, "S1c": lo_plus}, verdicts={"+": dict(survives=True)}),
            dict(legs={"Level 0": lo_minus, "S1c": lo_plus}, verdicts={"+": dict(survives=False)}),
            dict(legs={"Level 0": lo_minus, "S1c": None}, verdicts={"+": dict(survives=False)})]
    plus = BS.leg_rates(recs, "+", C.PLUS, legs=("Level 0", "S1c"))
    minus = BS.leg_rates(recs, "+", C.MINUS, legs=("Level 0", "S1c"))
    assert (plus["Level 0"]["k"], plus["S1c"]["k"]) == (1, 2), plus
    assert (minus["Level 0"]["k"], minus["S1c"]["k"]) == (2, 0), minus
    return dict(leg_rates_plus=[plus["Level 0"]["k"], plus["S1c"]["k"]],
                leg_rates_minus=[minus["Level 0"]["k"], minus["S1c"]["k"]])


# ---- (3) P3b counts the one-sided '+' survivors -------------------------------------------------------------------------
def p3b_records(n_comp=100, n_plus=60, n_two=30, n_unmatched=5) -> list:
    recs = []
    for j in range(n_comp):
        plus, two = j < n_plus, j < n_two
        legs = {k: {"+": .01 if plus else .5, "-": .9} for k in ("Level 0", "S1c", "S2c", "site", "G1", "G3m", "G6s",
                                                                 "G6l", "species")}
        recs.append(dict(status="computed", case=1000 + j, i=j, claim=dict(
            legs=legs, verdicts={"+": dict(survives=plus, primary_status="ok"),
                                 "two": dict(survives=two, primary_status="ok")})))
    recs += [dict(status="unmatched for plant", case=2000 + j, i=1000 + j) for j in range(n_unmatched)]
    return recs


def chk_p3b() -> dict:
    spec = p03.PLANTS["P3b"]
    cell = [c for c in spec.cells() if c.cls == "V-AAL"][0]
    recs = p3b_records()
    s = spec.summarise(cell, recs, CR.P3B_N)
    assert s["direction"] == "+", s["direction"]
    assert s["n_computed"] == 100 and s["n_unmatched_for_plant"] == 5, (s["n_computed"], s["n_unmatched_for_plant"])
    assert s["survivors"] == 60, f"survivors {s['survivors']} (one-sided '+': 60; two-sided: 30)"
    assert s["criterion"]["k"] == 60 and s["criterion"]["n"] == 100, s["criterion"]
    assert s["criterion"]["result"] == "PASS", s["criterion"]["result"]          # 60 > 52
    assert s["two_sided_R1_survivors (reported, no threshold)"]["k"] == 30
    assert p03._surv(recs) == (60, 100), p03._surv(recs)
    # V-DK at its boundary: 44 '+' survivors fail, 45 pass, whatever the two-sided count
    vdk = [c for c in spec.cells() if c.cls == "V-DK"][0]
    r44 = spec.summarise(vdk, p3b_records(n_plus=44, n_two=80), CR.P3B_N)["criterion"]["result"]
    r45 = spec.summarise(vdk, p3b_records(n_plus=45, n_two=10), CR.P3B_N)["criterion"]["result"]
    assert r44.startswith("FAIL") and r45 == "PASS", (r44, r45)
    return dict(survivors=s["survivors"], criterion=s["criterion"]["result"], vdk_44=r44[:4], vdk_45=r45)


# ---- (4) write_plant keeps unmatched cases out of n -------------------------------------------------------------------
def wp_record(i: int, computed: bool) -> dict:
    base = dict(i=i, case=1000 + i, seconds=1.0, cpu_seconds=1.0, memory_defect=False, peak_working_set_bytes=1)
    if not computed:
        return dict(base, status="unmatched for plant")
    legs = {k: {"+": .5, "-": .5} for k in ("Level 0", "S1c", "S2c", "site", "G1", "G3m", "G6s", "G6l", "species")}
    return dict(base, status="computed", claim=dict(legs=legs, verdicts={
        "+": dict(survives=bool(i % 2), primary_status="ok"), "two": dict(survives=False, primary_status="ok")}))


def chk_write_plant() -> dict:
    spec = D.REG["P3b"]
    assert spec.replace_unmatched
    cell = [c for c in spec.cells() if c.cls == "V-AAL"][0]
    pattern = [False, True, False, True, True, True, False, True]   # i0 unmatched, i1 computed, ...
    store = types.SimpleNamespace(dir=Path("synthetic_store"))
    got = {(str(store.dir), f"{cell.slug}_i{i:04d}"): wp_record(i, c) for i, c in enumerate(pattern)}
    tmp = Path(tempfile.mkdtemp(prefix="a1_plants_scoring_wp_"))
    inv = object.__new__(D.Invocation)
    inv.dev, inv.out, inv.launch_rec, inv.K = True, tmp, {}, dict(C.K_PLANT)
    inv.constants = dict(values="synthetic (test_plants_scoring)")
    logs = []
    inv.log = logs.append
    saved = C.context_report
    C.context_report = lambda cls: {"synthetic": cls}     # no class context is loaded
    try:
        rc = inv.write_plant(spec, store, got, {("P3b", cell.name): 3}, {"synthetic": True}, "DEV (test)", [])
        doc = json.loads((tmp / "P3b" / "plant_P3b.json").read_bytes().decode("utf-8"))
        rows = [json.loads(x) for x in (tmp / "P3b" / "cases_P3b.jsonl").read_bytes().decode("utf-8").splitlines()]
    finally:
        C.context_report = saved
        shutil.rmtree(tmp, ignore_errors=True)
    s = doc["cells"][cell.name]
    assert rc == 0
    assert [r["i"] for r in rows] == [0, 1, 2, 3, 4], f"cases written {[r['i'] for r in rows]} (want i0..i4)"
    assert sum(r["status"] == "computed" for r in rows) == 3, "computed cases written != n wanted (3)"
    assert s["n_computed"] == 3 and s["n_unmatched_for_plant"] == 2 and s["n_cases"] == 5, \
        (s["n_computed"], s["n_unmatched_for_plant"], s["n_cases"])
    assert s["n_run"] == 3 and doc["cases_file"]["n"] == 5 and doc["timing"][cell.name]["n"] == 5
    return dict(cases_written=[r["i"] for r in rows], n_computed=s["n_computed"], n_unmatched=s["n_unmatched_for_plant"])


# ---- (5) P26: site p = max(S1c, S2c) -----------------------------------------------------------------------------------
class FakeAdapter:
    """The adapter surface P26.run_case and flaws.within_class_permutation read; the site p's are set by the test."""

    def __init__(self, n: int, p1: tuple, p2: tuple):
        self.y = np.linspace(-1.0, 1.0, n)
        self.ctx = types.SimpleNamespace(classes=np.array(["a"] * (n // 2) + ["b"] * (n - n // 2)))
        self.T_obs = 0.1
        self._p = {"S1c": p1, "S2c": p2}

    def site_leg(self, K, seed_of):
        return {leg: dict(p={1: float(p[0]), -1: float(p[1])}, seed=int(np.random.default_rng(seed_of(leg))
                                                                        .integers(2 ** 31)), info=dict(exact=False))
                for leg, p in self._p.items()}

    def T_maps(self, Y):
        return np.asarray(Y, dtype=float)[:, 0] * 0.0 + np.linspace(0.0, 0.2, len(Y))


def p26_case(p1: tuple, p2: tuple) -> dict:
    spec = p26.PLANTS["P26"]
    cell = [c for c in spec.cells() if c.cls == "V-AAL"][0]
    n = 20
    saved = (C.prepare, CO.random_set, CO.field_kind)
    C.prepare = lambda form, cls, y, S: types.SimpleNamespace(adapter=FakeAdapter(n, p1, p2))
    CO.random_set = lambda cls, rng, m=25: np.arange(m)
    CO.field_kind = lambda cls, rng, gen, step: rng.standard_normal(n)
    try:
        return spec.run_case(cell, 0, dict(C.K_PLANT))
    finally:
        C.prepare, CO.random_set, CO.field_kind = saved


def chk_p26_site() -> dict:
    out = {}
    for name, p1, p2, want_site, want_rej in (
            ("S1c low, S2c high", (.01, .99), (.20, .80), {"+": .20, "-": .99}, False),
            ("S1c high, S2c low", (.30, .70), (.001, .999), {"+": .30, "-": .999}, False),
            ("both low", (.01, .99), (.02, .98), {"+": .02, "-": .99}, True)):
        rec = p26_case(p1, p2)
        for form in p26.FORMS:
            f = rec["forms"][form]
            assert f["site"] == want_site, f"{name} {form}: site {f['site']} != max(S1c, S2c) {want_site}"
            assert f["site_rejects"] is want_rej, f"{name} {form}: site_rejects {f['site_rejects']}"
            assert f["S1c"] == {"+": p1[0], "-": p1[1]} and f["S2c"] == {"+": p2[0], "-": p2[1]}
        out[name] = rec["forms"]["decoded-list"]["site"]["+"]
    return out


# ---- (6) run.validate on a real run: K other than the registered counts refused ----------------------------------------
REAL = ["--commit", "0" * 40, "--pass", "verdict", "--gate", "none"]


def chk_validate_K() -> dict:
    refused, passed = {}, []
    for k in ("plant", "site=500", "species=200", "site=500,species=200", "permutation=500", "j1_sets=100",
              "sets=200,surr=500", "site=9999"):
        a = R.build_parser().parse_args(REAL + ["--K", k])
        try:
            R.validate(a)
        except R.RunRefused as e:
            refused[k] = str(e.code if hasattr(e, "code") else e)[:50]
            continue
        raise AssertionError(f"a real run accepted --K {k}")
    for argv in (REAL, REAL + ["--K", "audit"], REAL + ["--K", "site=10000"]):
        R.validate(R.build_parser().parse_args(argv))
        passed.append(" ".join(argv[len(REAL):]) or "(no --K)")
    return dict(refused=sorted(refused), passed=passed)


# ---- (7) the mutants ---------------------------------------------------------------------------------------------------
def mutate(owner, name: str, old: str, new: str):
    """(original, mutant) of owner.<name>: its source with `old` (exactly once) replaced by `new`, compiled in the
    function's own module globals (the mutant's def lands in a scratch namespace, not in the module)."""
    fn = inspect.unwrap(getattr(owner, name))
    src = textwrap.dedent(inspect.getsource(fn))
    if src.count(old) != 1:
        raise AssertionError(f"mutant snippet found {src.count(old)} times in {name}: {old!r}")
    ns: dict = {}
    flags = __future__.annotations.compiler_flag   # the modules' own `from __future__ import annotations`
    exec(compile(src.replace(old, new), f"<mutant of {name}>", "exec", flags=flags, dont_inherit=True), fn.__globals__,
         ns)
    return getattr(owner, name), ns[name]


MUTANTS = [
    ("M1", "species_rejects takes the min", C, "species_rejects",
     "return max(p[d] for p in ps) < alpha", "return min(p[d] for p in ps) < alpha", chk_species_rejects),
    ("M2", "species_rejects ignores the uninformative flag", C, "species_rejects",
     'if any(p is None for p in ps) or sp["uninformative"]:', "if any(p is None for p in ps):", chk_species_rejects),
    ("M3", "below reads the other direction", C, "below",
     'v = p["+" if d == PLUS else "-"]', 'v = p["-" if d == PLUS else "+"]', chk_below),
    ("M4a", "P3b counts two-sided survivors (_surv)", p03, "_surv",
     'r["claim"]["verdicts"]["+"]["survives"]', 'r["claim"]["verdicts"]["two"]["survives"]', chk_p3b),
    ("M4b", "P3b summarises the two-sided verdict", p03.P3b, "summarise",
     'CR.p3b(cell.cls, *_surv(recs)), "+")', 'CR.p3b(cell.cls, *_surv(recs)), "two")', chk_p3b),
    ("M5a", "write_plant counts unmatched cases towards n", D.Invocation, "write_plant",
     'k += r["status"] == "computed"', "k += 1", chk_write_plant),
    ("M5b", "write_plant takes the first n cases whatever their status", D.Invocation, "write_plant",
     "if spec.replace_unmatched:", "if False:", chk_write_plant),
    ("M6", "P26 site p = min(S1c, S2c)", p26.P26, "run_case",
     'max(site["S1c"]["p"][d], site["S2c"]["p"][d])', 'min(site["S1c"]["p"][d], site["S2c"]["p"][d])', chk_p26_site),
    ("M7", "run.validate refuses only the literal --K plant", R, "validate",
     "if K != AUDIT_K:", 'if args.K == "plant":', chk_validate_K),
]


@check("species_rejects_max_flags_floors [M1 M2]")
def t1():
    return chk_species_rejects()


@check("below_direction_and_leg_rates [M3]")
def t2():
    return chk_below()


@check("p3b_counts_one_sided_plus [M4]")
def t3():
    return chk_p3b()


@check("write_plant_unmatched_outside_n [M5]")
def t4():
    return chk_write_plant()


@check("p26_site_is_max_of_S1c_S2c [M6]")
def t5():
    return chk_p26_site()


@check("run_validate_real_run_K [M7]")
def t6():
    return chk_validate_K()


@check("mutants_killed")
def t7():
    out = {}
    for mid, what, owner, name, old, new, chk in MUTANTS:
        orig, mut = mutate(owner, name, old, new)
        setattr(owner, name, mut)
        try:
            try:
                chk()
                killed = None
            except AssertionError as e:   # only the check's own assertion counts as a kill
                killed = f"{type(e).__name__}: {str(e)[:70]}"
        finally:
            setattr(owner, name, orig)
        if killed is None:
            raise AssertionError(f"{mid} ({what}) survived its check {chk.__name__}")
        chk()   # the restored code passes again
        out[mid] = killed
        print(R.ascii_line(f"  {mid} ({what}) killed by {chk.__name__}: {killed}"), flush=True)
    return dict(killed=sorted(out))


if ARGS.slow:
    @check("p26_real_case_reproduces_dev_record")
    def t8():
        """P26.run_case on the real dk-ctx context, case 0, against the DEV record of the same case (DEV keys are the
        official keys, RUN_PLAN_amend_2 §8.2): every field equal, the site p the max of S1c and S2c."""
        from a1_audit import a3_port as A3
        from a1_audit import plants_dev_compare as DC
        dev = Path(ARGS.dev_dir) if ARGS.dev_dir else (Path(__file__).resolve().parents[3] / "run_manifests" / "plants" / "DEV"
                                                         / "dev3")  # DEV records committed (RUN_PLAN_amend_2 §8.2)
        rows = DC.load_cases(dev / "P26" / "cases_P26.jsonl", "P26")
        spec = p26.PLANTS["P26"]
        cell = [c for c in spec.cells() if c.cls == "dk-ctx"][0]
        recd = rows[(cell.name, 0)]
        rec = json.loads(json.dumps(A3.jsonable(spec.run_case(cell, 0, D.Invocation.K_for(
            types.SimpleNamespace(K=dict(C.K_PLANT)), "P26"))), sort_keys=True))
        diffs = DC.compare_records({k: v for k, v in recd.items() if k not in ("plant", "cell", "i", "case", "class_id",
                                                                             "plant_id")}, rec)
        assert not diffs, f"{len(diffs)} difference(s), first {diffs[0]}"
        for form in p26.FORMS:
            f = rec["forms"][form]
            assert f["site"] == {d: max(f["S1c"][d], f["S2c"][d]) for d in ("+", "-")}
        return dict(dev_dir=dev.as_posix(), fields_equal="all", site_plus={f: rec["forms"][f]["site"]["+"]
                                                                            for f in p26.FORMS})


def main() -> int:
    n = len(RESULTS)
    print(f"{n - len(FAILED)} of {n} checks passed", flush=True)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
