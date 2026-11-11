"""Tests of the WP2 plant apparatus (a1_audit.plants; RUN_PLAN.md v3.1 §7). Plain script; exits non-zero on failure.

    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_plants_wp2 [--slow]

(1) criteria: every §7 threshold re-derived from the tail §7 states (asserted at import) and flipped exactly at its
    boundary (criteria.self_test: 22 planted counts).
(2) seeds: plant keys through seeds.py's plant interface; every (plant id, case, class id) of every plant's cells is
    unique over the official n and a replacement margin of n more; P3a / P3b inside their case ranges; leg keys =
    the decided six words; G3 = the first spawned child of the leg-3 key; construction keys (five words) are never leg
    keys (six); plant-only leg words are not registered leg numbers; no plant key carries a claim key's target word.
(3) plant-only flags: every flawed leg refuses without its flag, a 'real' run kind refuses every flag, a flag refuses
    another plant; a1_audit.run's CLI refuses an unknown plant-flaw option (argparse exit 2).
(3b) isolation (WP2 review C3): no production module of a1_audit has a route into a1_audit.plants - neither an import
    statement nor importlib.import_module / __import__ of a plants name (a literal, or a module constant holding one),
    nor an import of the plant-side tools (PLANT_TOOLS); the static scan (regex + AST) must catch planted sources of
    each kind. The one allowed route is run.py's hand-off (HANDOFF_DRIVER = 'a1_audit.plants.driver', imported in
    driver_order and plants_handoff only); every other dynamic import is in a reviewed list (none reaches plants), and
    the hand-off imports the driver only when --plant names a WP2 battery plant (recorded on real-run, P2 and battery
    argv).
(4) driver: an official run refuses DEV options; a DEV --out inside the repository is refused; --commit required.
(5) multiverse: CellSources refuses an unknown cell and a partly missing parcel row.
(6) --slow: construct.cgene reproduces the frozen battery's C-gene plant (e3_plants.one_plant: r to 1e-12) for the
    frozen seeds of one plant in V-AAL and in V-DK.
"""
from __future__ import annotations

import argparse
import ast
import importlib
import json
import re
import sys
import time
import traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
A1 = HERE.parent
ROOT = HERE.parents[4]

ap = argparse.ArgumentParser()
ap.add_argument("--slow", action="store_true")
ARGS, _ = ap.parse_known_args()

from a1_audit import run as R  # noqa: E402
from a1_audit import seeds as SD  # noqa: E402
from a1_audit import multiverse as MV  # noqa: E402
from a1_audit.plants import common as C  # noqa: E402
from a1_audit.plants import criteria as CR  # noqa: E402
from a1_audit.plants import flaws as FL  # noqa: E402
from a1_audit.plants import driver as D  # noqa: E402

RESULTS, FAILED = {}, []


def check(name):
    def deco(fn):
        t0 = time.time()
        try:
            out = fn() or {}
            RESULTS[name] = dict(result="pass", seconds=round(time.time() - t0, 2), **out)
            print(f"PASS {name} {json.dumps(out)[:400]}", flush=True)
        except Exception as e:  # noqa: BLE001
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
        return type(e).__name__
    raise AssertionError(f"{getattr(f, '__name__', f)} did not raise {exc.__name__}")


@check("criteria_derivations_and_boundaries")
def t_criteria():
    lines = CR.self_test()
    assert len(lines) == 22, len(lines)
    d = CR.derivations()
    assert d["P24"]["max"] == 24 and d["P25"]["flawed_min"] == 22 and d["P25"]["correct_max"] == 37
    assert d["P26"]["planted_min"] == 15 and d["P3b"]["V-AAL"]["threshold"] == 52 and d["P3b"]["V-DK"]["threshold"] == 44
    return dict(n_boundaries=len(lines), p3b_tails={c: round(v["tail_at"], 4) for c, v in d["P3b"].items()})


@check("seed_keys_unique_and_decided_rule")
def t_seeds():
    C.require_seed_interface()
    n_keys = 0
    for pid, spec in D.REG.items():
        seen = {}
        for cell in spec.cells():
            n = spec.n_official(cell)
            for i in range(2 * n):
                k = spec.keys(cell, i)
                t = (k.plant_id, k.case, k.class_id)
                assert t not in seen, f"{pid}: key {t} of {cell.name} i={i} also used by {seen[t]}"
                seen[t] = (cell.name, i)
                n_keys += 1
        # claim-level keys inside a case (P24 / P25 kinds) never meet a map key of the same plant
        if pid in ("P24", "P25"):
            from a1_audit.plants import p24
            for cell in spec.cells():
                if pid == "P25" and cell.get("part") != "ab":
                    continue
                for i in range(2 * spec.n_official(cell)):
                    m = spec.case_of(cell, i)
                    for kind in (p24.KINDS if pid == "P24" else ("brand-300",)):
                        t = (spec.plant_id, p24.claim_case(m, kind), C.class_id(cell.cls))
                        assert t not in seen, f"{pid}: claim key {t} collides"
                        seen[t] = ("claim", i)
    for pid, lo_hi in (("P3a", (0, 1000)), ("P3b", (1000, None))):
        spec = D.REG[pid]
        for cell in spec.cells():
            for i in range(2 * spec.n_official(cell)):
                SD.check_plant_case(pid, spec.case_of(cell, i))
    k = C.PlantKeys(3, 1000, C.class_id("V-AAL"))
    for name, no in (("S1c", 0), ("S2c", 1), ("G1", 2), ("G3m", 3), ("G6s", 4), ("G6l", 5), ("permutation", 8),
                     ("G2", 11), ("J1", 14), ("naive joint", 15)):
        ss = k.seed_of(name)
        assert [int(x) for x in ss.entropy] == [20260925, 900, 3, 1000, 11, no], (name, ss.entropy)
        assert SD.same_seed_sequence(ss, SD.plant_leg_seed(3, 1000, 11, no))
    for name, no in (("S1c", 21), ("S2c", 22), ("G1", 23), ("G3m", 24), ("G6l", 25)):
        assert [int(x) for x in k.tabs_seed_of(name).entropy] == [20260925, 900, 3, 1000, 11, no]
    g3 = k.g3_seed()
    assert SD.same_seed_sequence(g3, np.random.SeedSequence([20260925, 900, 3, 1000, 11, 3]).spawn(1)[0])
    assert len(k.construction.entropy) == 5 and all(len(k.leg(n).entropy) == 6 for n in (0, 5, 90))
    assert not (set(C.PLANT_ONLY_LEGS.values()) & set(SD.LEG_NAMES)) and SD.PLANT_DATA_WORD not in C.PLANT_ONLY_LEGS.values()
    pw = k.seed_of("within-class permutation (plant only)")
    assert [int(x) for x in pw.entropy] == [20260925, 900, 3, 1000, 11, 90]
    rec = k.record()
    assert rec["keys"] == "plant" and rec["plant_only_legs"] and rec["G3"]
    raises(ValueError, SD.check_plant_case, "P3a", 1000)
    raises(ValueError, SD.check_plant_case, "P3b", 999)
    assert 900 not in range(SD.TARGET_OFFSET + 1, SD.TARGET_OFFSET + SD.N_TARGETS + 1)
    return dict(n_keys_checked=n_keys)


@check("plant_only_flags_refused_outside_their_plant")
def t_flags():
    out = {}
    out["v2"] = raises(FL.PlantOnlyRefused, FL.v2_species_max, None, 10, None, None, "ok")
    out["min"] = raises(FL.PlantOnlyRefused, FL.species_min, {})
    out["uncond"] = raises(FL.PlantOnlyRefused, FL.unconditioned_g1_g3m, None, 10, None)
    out["perm"] = raises(FL.PlantOnlyRefused, FL.within_class_permutation, None, 10, np.random.SeedSequence(1))
    for flag, plant in FL.FLAGS.items():
        def enter(f=flag, p=plant, kind="real"):
            with FL.enabled(f, p, kind):
                pass
        raises(FL.PlantOnlyRefused, enter)
        other = "P26" if plant == "P25" else "P25"
        raises(FL.PlantOnlyRefused, enter, flag, other, "plant")
        with FL.enabled(flag, plant, "plant"):
            assert flag in FL._ENABLED
        assert flag not in FL._ENABLED
    # a1_audit.run has no option reaching the flawed legs: argparse refuses an unknown option (exit 2)
    base = ["--commit", "0" * 40, "--pass", "verdict", "--gate", "none"]
    try:
        R.build_parser().parse_args(base + ["--plant-flaw", "v2-species-max"])
        raise AssertionError("run.py accepted --plant-flaw")
    except SystemExit as e:
        assert e.code == 2
    return out


# ---- (3b) isolation: no production route into a1_audit.plants (WP2 review C3) ---------------------------------------
# the plant-side tools beside the production modules (WP2 review B1-B3): they import plants; no production module may
# import them
PLANT_TOOLS = ("plants_dev_compare", "plants_official_check", "plants_p25a_rescore")
ISOLATION_RE = re.compile(r"(from\s+\.?\s*plants\b|import\s+a1_audit\.plants|from\s+a1_audit\.plants|flaws|"
                          r"import_module\(\s*[\"']a1_audit\.plants|__import__\(\s*[\"']a1_audit\.plants|"
                          + "|".join(PLANT_TOOLS) + ")")
PLANTS_PATH = re.compile(r"a1_audit\.plants(\.\w+)*")
ALLOWED_HANDOFF = [("run.py", "driver_order", "HANDOFF_DRIVER", "a1_audit.plants.driver"),
                   ("run.py", "plants_handoff", "HANDOFF_DRIVER", "a1_audit.plants.driver")]
# reviewed dynamic imports of production modules (none can name plants): ahba_builds' version probe over a literal
# tuple of third-party packages; launch's gates module; launch's `preload` (no caller passes it: asserted below)
KNOWN_DYNAMIC = {("ahba_builds.py", "environment", "mod"), ("launch.py", "_gates_module", "__package__ + '.gates'"),
                 ("launch.py", "launch", "m")}


def scan_source(src: str, fname: str) -> dict:
    """Static scan of one module's source: 'bad' (a direct route into plants or the plant tools), 'handoffs' (a dynamic
    import of a module constant naming plants: (file, function, constant, value)), 'dynamic' (a dynamic import whose
    argument is not a literal or a module constant: (file, function, argument)), 'paths' (string literals that are a
    plants module path), and 'regex' (the widened text check)."""
    tree = ast.parse(src)
    consts = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    consts[t.id] = n.value.value
    out = dict(bad=[], handoffs=[], dynamic=[], paths=[], regex=bool(ISOLATION_RE.search(src)))

    def plantish(mod: str) -> bool:
        parts = mod.split(".")
        return "plants" in parts or any(p in PLANT_TOOLS for p in parts)

    def visit(node, func):
        for ch in ast.iter_child_nodes(node):
            f = ch.name if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)) else func
            if isinstance(ch, ast.ImportFrom):
                mod = ch.module or ""
                names = [a.name for a in ch.names]
                if plantish(mod) or (mod in ("", "a1_audit") and any(plantish(x) for x in names)):
                    out["bad"].append((fname, f, f"from {'.' * ch.level}{mod} import {', '.join(names)}"))
            elif isinstance(ch, ast.Import):
                for a in ch.names:
                    if plantish(a.name):
                        out["bad"].append((fname, f, f"import {a.name}"))
            elif isinstance(ch, ast.Call):
                fn = ch.func.attr if isinstance(ch.func, ast.Attribute) else getattr(ch.func, "id", None)
                if fn in ("import_module", "__import__") and ch.args:
                    a0 = ch.args[0]
                    if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                        if plantish(a0.value):
                            out["bad"].append((fname, f, f"{fn}({a0.value!r})"))
                    elif isinstance(a0, ast.Name) and a0.id in consts:
                        if plantish(consts[a0.id]):
                            out["handoffs"].append((fname, f, a0.id, consts[a0.id]))
                    else:
                        out["dynamic"].append((fname, f, ast.unparse(a0)))
            elif isinstance(ch, ast.Constant) and isinstance(ch.value, str) and PLANTS_PATH.fullmatch(ch.value):
                out["paths"].append((fname, ch.value))
            visit(ch, f)
    visit(tree, None)
    return out


def violations(scans: list) -> list:
    v = []
    for s in scans:
        v += [("regex", s["file"])] if s["regex"] else []
        v += [("bad",) + b for b in s["bad"]]
        v += [("dynamic",) + d for d in s["dynamic"] if d not in KNOWN_DYNAMIC]
    hand = sorted(h for s in scans for h in s["handoffs"])
    if hand != sorted(ALLOWED_HANDOFF):
        v.append(("handoffs", tuple(hand)))
    paths = sorted(p for s in scans for p in s["paths"])
    if paths and paths != [("run.py", "a1_audit.plants.driver")]:
        v.append(("paths", tuple(paths)))
    return v


@check("isolation_no_production_route_into_plants")
def t_isolation():
    prod = [f for f in sorted(A1.glob("*.py")) if f.stem not in PLANT_TOOLS]
    assert len(prod) >= 20 and (A1 / "run.py") in prod and (A1 / "plant_mode.py") in prod
    scans = []
    for f in prod:
        s = scan_source(f.read_text(encoding="utf-8"), f.name)
        s["file"] = f.name
        scans.append(s)
    v = violations(scans)
    assert not v, f"production routes into a1_audit.plants: {v}"
    hand = sorted(h for s in scans for h in s["handoffs"])
    assert hand == sorted(ALLOWED_HANDOFF) and R.HANDOFF_DRIVER == "a1_audit.plants.driver"
    assert not [f.name for f in prod if re.search(r"preload\s*=", f.read_text(encoding="utf-8"))
                and f.name != "launch.py"], "a caller passes launch(preload=...)"
    # planted sources: each kind must be caught by the AST half alone (and the literal kinds by the regex too)
    planted = {
        "import_module literal": 'import importlib\nimportlib.import_module("a1_audit.plants.flaws")\n',
        "import_module attr chain": 'import importlib as il\ndef f():\n    return il.import_module("a1_audit.plants")\n',
        "__import__ literal": 'm = __import__("a1_audit.plants.p25")\n',
        "constant handoff elsewhere": 'import importlib\nX = "a1_audit.plants.p25"\ndef f():\n'
                                      '    return importlib.import_module(X)\n',
        "unresolved dynamic": 'import importlib\ndef g(n):\n    return importlib.import_module(n)\n',
        "relative from": "from .plants import flaws\n",
        "relative package": "from . import plants\n",
        "absolute import": "import a1_audit.plants.driver as D\n",
        "plant tool": "from a1_audit import plants_p25a_rescore\n",
    }
    caught = {}
    for name, src in planted.items():
        s = scan_source(src, "planted.py")
        s["file"] = "planted.py"
        regex_hit = s["regex"]
        s["regex"] = False                     # the AST half must catch it on its own
        caught[name] = bool(violations(scans + [s]))
        caught[name + " (regex)"] = regex_hit
    missed = [k for k, v in caught.items() if not v and not k.endswith("(regex)")]
    assert not missed, f"the AST scan missed planted routes: {missed}"
    assert caught["import_module literal (regex)"] and caught["__import__ literal (regex)"], caught
    # behaviour: the hand-off imports the driver only under --plant <WP2 battery plant>
    calls = []
    orig = importlib.import_module

    def rec(name, *a, **k):
        calls.append(name)
        return orig(name, *a, **k)
    importlib.import_module = rec
    try:
        real = ["--commit", "0" * 40, "--pass", "verdict", "--gate", "none"]
        for argv in (real, real + ["--K", "site=500"], real + ["--rows", "1-3", "--jobs", "2"], ["--commit", "x"],
                     real + ["--plant", "P2", "--K", "plant"]):
            got = R.plants_handoff(argv)
            assert got is None, (argv, got)
        no_plant_calls = [c for c in calls if "plants" in c]
        assert not no_plant_calls, f"plants imported without a battery --plant: {no_plant_calls}"
        rc = R.plants_handoff(real + ["--plant", "P4", "--rows", "1"])    # a battery plant with a run.py-only option
        assert rc == 2 and calls.count(R.HANDOFF_DRIVER) == 1, (rc, calls)
    finally:
        importlib.import_module = orig
    assert importlib.import_module is orig
    return dict(production_modules=len(prod), handoffs=[h[1] for h in hand], planted_caught=len(planted),
                dynamic_reviewed=sorted(d[0] + ":" + d[1] for s in scans for d in s["dynamic"]))


@check("driver_mode_refusals")
def t_driver():
    p = D.build_parser()
    out = {}
    for argv, what in ((["P4"], "no commit"), (["P4", "--commit", "x", "--out", "D:/tmp/x"], "official with --out"),
                       (["P4", "--commit", "x", "--n", "3"], "official with --n"),
                       (["P4", "--commit", "x", "--dev"], "dev without --out"),
                       (["P4", "--commit", "x", "--dev", "--out", str(ROOT / "arcs" / "audit" / "x")], "dev out in repo"),
                       (["P4", "--commit", "x", "--dev", "--out", "D:/tmp/x", "--n", "0"], "dev n 0")):
        a = p.parse_args(argv)
        try:
            D.validate(a)
            raise AssertionError(f"not refused: {what}")
        except SystemExit as e:
            out[what] = str(e.code)[:60]
    D.validate(p.parse_args(["P4", "--commit", "x", "--dev", "--out", "D:/tmp/a1_wp2_dev_x"]))
    est = D.estimate(D.costs())
    assert set(est) == set(D.ORDER) | {"total"}
    return dict(refused=len(out), estimate_total_h=est["total"])


@check("multiverse_cell_sources_refusals")
def t_multiverse():
    import pandas as pd
    raises(ValueError, MV.CellSources, None, "no such cell", pd.DataFrame())
    ctx = C.class_context("dk-ctx")
    e = ctx.expr.copy()
    e.iloc[3, 5] = np.nan
    src = MV.CellSources(C.CaseSources("dk-ctx", np.zeros(ctx.n)), MV.CELLS[0], e)
    raises(R.SourceUnavailable, src.context, "dk-ctx")
    e2 = ctx.expr.drop(index=ctx.expr.index[0])
    raises(R.SourceUnavailable, MV.CellSources(C.CaseSources("dk-ctx", np.zeros(ctx.n)), MV.CELLS[1], e2).context,
           "dk-ctx")
    assert len(MV.CELLS) == 10
    return dict(cells=len(MV.CELLS))


if ARGS.slow:
    @check("cgene_reproduces_frozen_battery")
    def t_cgene():
        import e3_plants as P
        from a1_audit.plants import construct as CO
        out = {}
        for atlas, cls in (("aal", "V-AAL"), ("dk", "V-DK")):
            ectx = P.Ctx(atlas)
            i = 3
            seed = np.random.SeedSequence([P.ATLAS_ID[atlas], P.FAM_ID["C-gene"], 25, 90, i])
            row = P.one_plant(ectx, "C-gene", 25, 0.9, seed, i)
            c = CO.cgene(cls, np.random.default_rng(np.random.SeedSequence([P.ATLAS_ID[atlas], P.FAM_ID["C-gene"], 25,
                                                                             90, i])), i)
            ctx = C.class_context(cls)
            r = float(np.corrcoef(c["y"], ctx.U.scores(c["S"])[0])[0, 1])
            assert row["status"] == c["status"] == "ok"
            assert abs(r - row["r"]) <= 1e-12, (cls, r, row["r"])
            out[cls] = dict(r=r, r_frozen=float(row["r"]))
        return out


def main() -> int:
    n = len(RESULTS)
    print(f"{n - len(FAILED)} of {n} checks passed", flush=True)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
