"""P2, seed-level part (RUN_PLAN.md v3.1 §7 :1128; R7 :536-551; R24 :908-934; §7 seeds :1121-1122).

Run from arcs/audit/src:  ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_seeds
Exits non-zero if any check fails. (`--emit` is the child mode: it prints the seed records of three TSV rows as JSON.)

Checks: the LEGS table against the register's list (claims_register.md:1076-1082, read from the hash-checked file)
and against the plan's §4 legs table; the entropy order; keys and integer seeds identical across two separate
processes; R24's G3 stream reproducible, equal to the first spawned child of leg 3's key and different from leg 3's;
J1 / naive-joint draw order; plant keys never collide with claim keys (target 900 does not exist).
The "bit-identical p's" part of P2 needs the runner (WP2) and is not tested here.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

from a1_audit import launch as L
from a1_audit import loader
from a1_audit import seeds as S

REPO = Path(__file__).resolve().parents[5]
RESULTS: list[tuple[str, bool]] = []
LEG_USES = {"S1c": "int", "S2c": "int", "G1": "rng", "G3m": "rng", "G6s": "rng", "G6l": "rng",
            "permutation / label": "rng", "re-selection": "rng", "G2": "rng", "G4": "rng", "G5": "rng",
            "T_abs S1c": "int", "T_abs S2c": "int", "T_abs G1": "rng", "T_abs G3m": "rng", "T_abs G6l": "rng"}


def check(name: str, cond) -> bool:
    RESULTS.append((name, bool(cond)))
    print("%s  %s" % ("PASS" if cond else "FAIL", name))
    return bool(cond)


def head() -> str:
    return subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True).stdout.decode().strip()


def register_rows():
    ctx = L.make_ctx(REPO, head())
    rec = {"repo_root": str(ctx.repo), "files_root": None, "run_commit": ctx.commit, "passed": False,
           "assertions": [L.l1_register(ctx), L.l2_tsv(ctx), L.l3_manifest(ctx)]}
    return loader.load(REPO, rec, allow_unlaunched=True).rows()


def three_rows(rows):
    """first, middle and last rows whose map_index and cell_index are plain integers."""
    ok = [r for r in rows if loader.int_or_none(r.map_index_text) is not None and loader.int_or_none(r.cell_index_text) is not None]
    return [ok[0], ok[len(ok) // 2], ok[-1]]


def state_hex(ss) -> str:
    return "".join("%08x" % int(x) for x in ss.generate_state(4))


def emit_records(rows) -> list:
    out = []
    for r in three_rows(rows):
        t, n, m, c = r.target_no, r.row, loader.int_or_none(r.map_index_text), loader.int_or_none(r.cell_index_text)
        rec = S.seed_record(t, n, m, c, LEG_USES, g3=True, j1=True, naive_joint=True)
        rec["states"] = {leg: state_hex(S.claim_seed(t, n, leg, m, c)) for leg in S.LEGS}
        g3 = S.g3_seed(t, n, m, c)
        rec["G3_state"] = state_hex(g3)
        rec["G3_first_draws"] = [int(x) for x in S.leg_rng(g3).integers(2 ** 31, size=5)]
        j = S.j1_draws(t, n, m, c)
        rec["J1_next_draws"] = [int(x) for x in j["rng"].integers(2 ** 31, size=3)]
        nj = S.naive_joint_draws(t, n, m, c)
        rec["naive_next_draws"] = [int(x) for x in nj["rng"].integers(2 ** 31, size=3)]
        out.append(rec)
    out.append({"plant": S.key_record(S.plant_seed(3, 1, 2)), "plant_seed_int": S.seed_int(S.plant_seed(3, 1, 2))})
    return out


def legs_from_register() -> tuple[dict, list[int], str]:
    raw = L.lf((REPO / L.REGISTER_PATH).read_bytes())
    assert L.sha256_bytes(raw) == L.REGISTER_SHA256
    lines = raw.decode("utf-8").split("\n")
    start = [i for i, ln in enumerate(lines) if ln.startswith("- Seeds: `numpy.random.SeedSequence(")]
    assert len(start) == 1
    i0 = start[0]
    j = i0
    while not lines[j].rstrip().endswith("25 T_abs G6l."):
        j += 1
    para = " ".join(ln.strip() for ln in lines[i0:j + 1])
    m = re.search(r"legs (.+)\.$", para)
    legs = {}
    for item in m.group(1).split(", "):
        num, name = item.split(" ", 1)
        legs[name] = int(num)
    return legs, [i0 + 1, j + 1], para


def main() -> int:
    if "--emit" in sys.argv:
        print(json.dumps(emit_records(register_rows()), sort_keys=True))
        return 0

    # ---- the LEGS table against the frozen texts
    reg_legs, lines, para = legs_from_register()
    print("     register seed paragraph at claims_register.md:%d-%d" % tuple(lines))
    check("LEGS == the register's list (claims_register.md seed paragraph), names and numbers", reg_legs == S.LEGS)
    check("the register's key order: [20260925, 100 + target number, row number of the cell in claims_register.tsv, "
          "leg, map index, cell index]",
          "SeedSequence([20260925, 100 + target number, row number of the cell in claims_register.tsv, leg, map index, "
          "cell index])" in para)
    plan = L.lf((REPO / L.PLAN_PATH).read_bytes()).decode("utf-8").split("\n")
    a = next(i for i, ln in enumerate(plan) if ln.startswith("- **Legs (register"))
    b = next(i for i, ln in enumerate(plan) if ln.startswith("- **Checkpoints:**"))
    nums = {int(x) for ln in plan[a:b] for x in re.findall(r"\[(\d+)\]", ln)}
    check("the plan's §4 legs table brackets (RUN_PLAN.md:%d-%d) hold exactly the LEGS numbers" % (a + 1, b), nums == set(S.LEGS.values()))
    check("leg 8's name: register 'permutation / label' (plan §4: 'component Level 0 permutation [8]')",
          S.LEG_NAMES[8] == "permutation / label")

    # ---- entropy order and conventions
    ss = S.claim_seed(5, 7, "G1", 1, 2)
    check("claim_seed entropy == [20260925, 105, 7, 2, 1, 2] for target 5, row 7, leg G1, map 1, cell 2",
          list(ss.entropy) == [20260925, 105, 7, 2, 1, 2] and tuple(ss.spawn_key) == ())
    check("leg by name == leg by number", S.same_seed_sequence(S.claim_seed(5, 7, "G6l", 0, 0), S.claim_seed(5, 7, 5, 0, 0)))
    check("seed_int == int(default_rng(SS).integers(2**31))",
          S.seed_int(ss) == int(np.random.default_rng(np.random.SeedSequence([20260925, 105, 7, 2, 1, 2])).integers(2 ** 31)))

    # ---- two separate processes
    outs = []
    for _ in range(2):
        r = subprocess.run([sys.executable, "-X", "utf8", "-m", "a1_audit.tests.test_seeds", "--emit"],
                           cwd=str(REPO / "arcs" / "audit" / "src"), capture_output=True, timeout=600)
        outs.append(r.stdout.decode("utf-8").strip() if r.returncode == 0 else None)
    rows = register_rows()
    here = json.dumps(emit_records(rows), sort_keys=True)
    check("keys and integer seeds identical across two separate processes (3 rows x 16 legs, G3, J1, naive joint, a plant)",
          outs[0] is not None and outs[0] == outs[1] == here)
    recs = json.loads(here)
    print("     rows used: %s" % ", ".join(str(x["row"]) for x in recs[:3]))
    check("each row record lists every leg's key; 'int' legs carry seed_int, 'rng' legs do not",
          all(len(x["legs"]) == len(LEG_USES) and all(("seed_int" in l) == (l["use"] == "int") for l in x["legs"]) for x in recs[:3]))
    check("each row's leg keys read [20260925, 100 + target, row, leg, map, cell]",
          all(l["key"]["entropy"] == [20260925, 100 + x["target_number"], x["row"], l["leg_no"], x["map_index"], x["cell_index"]]
              for x in recs[:3] for l in x["legs"]))

    # ---- R24
    t, n = recs[0]["target_number"], recs[0]["row"]
    m, c = recs[0]["map_index"], recs[0]["cell_index"]
    leg3 = S.claim_seed(t, n, 3, m, c)
    g3 = S.g3_seed(t, n, m, c)
    check("R24: G3 key == SeedSequence(entropy=[20260925, 100+t, row, 3, map, cell], spawn_key=(0,))",
          list(g3.entropy) == [20260925, 100 + t, n, 3, m, c] and tuple(g3.spawn_key) == (0,))
    check("R24: G3 key == the first spawned child of leg 3's key", S.same_seed_sequence(g3, S.claim_seed(t, n, 3, m, c).spawn(1)[0]))
    check("R24: g3_seed leaves a leg-3 SeedSequence unadvanced (n_children_spawned 0)", leg3.n_children_spawned == 0)
    d3 = [int(x) for x in S.leg_rng(leg3).integers(2 ** 31, size=5)]
    check("R24: the G3 stream differs from leg 3's (state and first draws)",
          state_hex(g3) != state_hex(leg3) and recs[0]["G3_first_draws"] != d3)
    check("R24: the G3 stream is reproducible (same first draws in this process and both children)",
          [int(x) for x in S.leg_rng(S.g3_seed(t, n, m, c)).integers(2 ** 31, size=5)] == recs[0]["G3_first_draws"])

    # ---- J1 / naive joint order (R7)
    j = S.j1_draws(t, n, m, c)
    g = np.random.default_rng(S.claim_seed(t, n, 14, m, c))
    s1c, s2c = int(g.integers(2 ** 31)), int(g.integers(2 ** 31))
    check("J1 (leg 14): S1c seed = the generator's first integer draw, S2c seed the second, then the G2 sets' draws",
          j["S1c_seed"] == s1c and j["S2c_seed"] == s2c
          and np.array_equal(j["rng"].integers(2 ** 31, size=5), g.integers(2 ** 31, size=5)))
    check("J1's S1c seed == seed_int(leg-14 key) (the same call, first draw)", j["S1c_seed"] == S.seed_int(S.claim_seed(t, n, 14, m, c)))
    nj = S.naive_joint_draws(t, n, m, c)
    g = np.random.default_rng(S.claim_seed(t, n, 15, m, c))
    s1 = int(g.integers(2 ** 31))
    check("naive joint (leg 15): S1 seed first, then the G1 sets' draws",
          nj["S1_seed"] == s1 and np.array_equal(nj["rng"].integers(2 ** 31, size=5), g.integers(2 ** 31, size=5)))

    # ---- plants never collide with claim keys
    check("plant key == [20260925, 900, plant_id, case, class_id]", list(S.plant_seed(3, 1, 2).entropy) == [20260925, 900, 3, 1, 2])
    tns = sorted({r.target_no for r in rows})
    check("TSV targets are 1..21, so 100 + target is 101..121 and never 900", tns == list(range(1, 22)))
    claim_states, claim_ent = set(), set()
    n_keys = 0
    for r in rows:
        cells = {0}
        ci = loader.int_or_none(r.cell_index_text)
        if ci is not None:
            cells.add(ci)
        for leg in S.LEGS.values():
            for mi in (0, 1):
                for cc in cells:
                    k = S.claim_seed(r.target_no, r.row, leg, mi, cc)
                    claim_states.add(state_hex(k))
                    claim_ent.add(tuple(k.entropy))
                    n_keys += 1
        for mi in (0, 1):
            for cc in cells:
                claim_states.add(state_hex(S.g3_seed(r.target_no, r.row, mi, cc)))
                n_keys += 1
    plant_states = {state_hex(S.plant_seed(p, cs, cl)) for p in range(27) for cs in range(20) for cl in range(10)}
    print("     claim keys %d (distinct states %d); plant keys %d" % (n_keys, len(claim_states), len(plant_states)))
    check("no plant key's state equals any claim or G3 key's state (all TSV rows x 18 legs x map 0/1 x cells; P0-P26 x 20 cases x 10 classes)",
          not (claim_states & plant_states) and len(plant_states) == 27 * 20 * 10)
    check("claim keys are pairwise distinct (no state collision)", len(claim_states) == n_keys)
    check("no claim entropy carries 900 in the target position", all(e[1] != S.PLANT_WORD for e in claim_ent))

    # ---- validation (fail closed)
    def refused(fn) -> bool:
        try:
            fn()
            return False
        except (ValueError, TypeError):
            return True
    check("target 800 (100 + target = 900) refused", refused(lambda: S.claim_seed(800, 1, 0, 0, 0)))
    check("targets 0 and 22 refused; rows 0 and 693 refused",
          all(refused(f) for f in (lambda: S.claim_seed(0, 1, 0, 0, 0), lambda: S.claim_seed(22, 1, 0, 0, 0),
                                   lambda: S.claim_seed(1, 0, 0, 0, 0), lambda: S.claim_seed(1, 693, 0, 0, 0))))
    check("unregistered leg numbers 6, 7, 9, 16, 20, 26 and the name 'G3' refused",
          all(refused(lambda l=l: S.claim_seed(1, 1, l, 0, 0)) for l in (6, 7, 9, 16, 20, 26, "G3")))
    check("negative, bool and float indices refused",
          all(refused(f) for f in (lambda: S.claim_seed(1, 1, 0, -1, 0), lambda: S.claim_seed(1, 1, 0, 0, True),
                                   lambda: S.claim_seed(1, 1, 0, 0, 1.0), lambda: S.plant_seed(-1, 0, 0))))
    check("seed_record refuses J1 / naive joint through the legs mapping (R7's draw order is recorded apart)",
          refused(lambda: S.seed_record(1, 1, 0, 0, {"J1": "int"})) and refused(lambda: S.seed_record(1, 1, 0, 0, {"naive joint": "rng"})))
    check("seed_record refuses an unknown use", refused(lambda: S.seed_record(1, 1, 0, 0, {"S1c": "both"})))

    n_fail = sum(1 for _, ok in RESULTS if not ok)
    print("test_seeds: %d checks, %d passed, %d failed" % (len(RESULTS), len(RESULTS) - n_fail, n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
