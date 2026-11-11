"""A1 seeds (RUN_PLAN.md v3.1 R7, R24, §7; FROZEN sha256 16c60232...).

The registered key (claims_register.md:1076-1082, quoted):
  "Seeds: `numpy.random.SeedSequence([20260925, 100 + target number, row number of the cell in claims_register.tsv,
  leg, map index, cell index])` ... legs 0 S1c, 1 S2c, 2 G1, 3 G3m, 4 G6s, 5 G6l, 8 permutation / label,
  10 re-selection, 11 G2, 12 G4, 13 G5, 14 J1, 15 naive joint, 21 T_abs S1c, 22 T_abs S2c, 23 T_abs G1,
  24 T_abs G3m, 25 T_abs G6l."
R7 (RUN_PLAN.md:536-551) quotes it as "[20260925, 100 + target number, row number ..., leg, map index, cell index]";
its "..." stands for "of the cell in claims_register.tsv". The order of the six entropy words is therefore
[20260925, 100 + target, row, leg, map index, cell index].

- `seed_int(ss)` = int(np.random.default_rng(ss).integers(2**31)) (R7; A3's convention, h_verdicts.py:398).
- `leg_rng(ss)` = np.random.default_rng(ss) (R7: "A leg that needs a Generator").
- J1 (leg 14) and the naive joint (leg 15) take ONE generator and draw in a fixed order (R7):
  J1: S1c seed, then S2c seed, then the G2 sets; naive joint: S1 seed, then the G1 sets. Each integer seed is drawn
  with the same call as `seed_int` (g.integers(2**31)), from the shared generator.
- G3 (R24, RUN_PLAN.md:920-929): SeedSequence(entropy=[20260925, 100 + target, row, 3, map index, cell index],
  spawn_key=(0,)), asserted equal to the first spawned child of leg 3's key; leg 3's own stream is untouched.
- Plants (§7, RUN_PLAN.md:1121-1122): SeedSequence([20260925, 900, plant_id, case, class_id]); target 900 does not
  exist (claim keys carry 100 + target, targets 1..21, so 101..121).

Plant keys of the runner's plant view (asdg-skeptic WP1 review, B3; RUN_PLAN §7 :1121-1122 "kept apart from every claim
key"). PLANT CHOICE (orchestrator, 2026-10-01): leg streams within a plant case.
- Every null leg of a plant case draws from SeedSequence([20260925, 900, plant_id, case, class_id, leg]) with the
  registered leg number (plant_leg_seed); R24's G3 = the first spawned child of that case's leg-3 key (plant_g3_seed);
  J1 and the naive joint draw in R7's fixed order from their leg-14 / leg-15 keys (plant_j1_draws /
  plant_naive_joint_draws). plant_seed_record records them in seed_record's layout.
- class_id: one fixed integer per class, PLANT_CLASS_IDS (plant_class_id): dk-ctx 2, V-AAL 11, V-DK 12, V-DK-subcortex
  13, MIST64 14, V-CC200 17 (the first five are the ids WP1 gave the synthetic classes, run.SYN_CLASSES, kept so every
  plant made so far keeps its streams; 15 and 16 are taken by forms.SYN_LIU_CLASS_ID's synthetic Liu data kinds).
- plant_id: P<n> -> n; the lettered plants share their number and are kept apart by disjoint case ranges
  (LETTERED_PLANTS, PLANT_CASE_RANGES: P3a cases 0..999, P3b cases 1000 and up; a1_audit/plants uses P3a 0..19 and
  P3b 1000 + j); plant_int / check_plant_case.
- Synthetic data of a plant case (run.SyntheticSources with a case): SeedSequence([20260925, 900, plant_id, case,
  class_id, 1000, data word]) (plant_data_seed): seven words with 1000 in the leg position, so no data stream is a leg
  stream (six words) or a G3 stream (assembled entropy [..., 3, 0]).
- P2 is the declared exception: its purpose is the claim keys (RUN_PLAN §7 P2 :1128), so P2 runs keep them.

Map and cell indices are integers the caller resolves from the TSV row (`map_index` / `cell_index` hold the
register's text where a row is a family or a two-cohort claim); this module never interprets that text.
"""
from __future__ import annotations

import re
from typing import Iterable, Mapping

import numpy as np

ROOT_ENTROPY = 20260925
TARGET_OFFSET = 100
PLANT_WORD = 900
N_TARGETS = 21   # targets 1..21 (claims_register.tsv header: "all 21 targets"; TSV target_no 1..21)
N_ROWS = 692     # RUN_PLAN.md:152 (L12)

# claims_register.md:1080-1082 (names as the register writes them; leg 8 is "permutation / label", which RUN_PLAN.md
# §4 :371 calls "component Level 0 permutation [8]")
LEGS: dict[str, int] = {
    "S1c": 0, "S2c": 1, "G1": 2, "G3m": 3, "G6s": 4, "G6l": 5,
    "permutation / label": 8, "re-selection": 10,
    "G2": 11, "G4": 12, "G5": 13, "J1": 14, "naive joint": 15,
    "T_abs S1c": 21, "T_abs S2c": 22, "T_abs G1": 23, "T_abs G3m": 24, "T_abs G6l": 25,
}
LEG_NAMES: dict[int, str] = {v: k for k, v in LEGS.items()}
G3M_LEG = 3
J1_LEG = 14
NAIVE_JOINT_LEG = 15


def _nonneg_int(x, name: str) -> int:
    if isinstance(x, bool) or not isinstance(x, (int, np.integer)) or int(x) < 0:
        raise ValueError("%s must be a non-negative int, got %r" % (name, x))
    return int(x)


def _leg_no(leg) -> int:
    if isinstance(leg, str):
        if leg not in LEGS:
            raise ValueError("unknown leg name %r (claims_register.md:1080-1082)" % leg)
        return LEGS[leg]
    n = _nonneg_int(leg, "leg")
    if n not in LEG_NAMES:
        raise ValueError("leg %d is not a registered leg number (claims_register.md:1080-1082)" % n)
    return n


def _claim_words(target_number, row, leg, map_index, cell_index) -> list[int]:
    t = _nonneg_int(target_number, "target_number")
    if not 1 <= t <= N_TARGETS:
        raise ValueError("target_number %d outside the register's targets 1..%d" % (t, N_TARGETS))
    r = _nonneg_int(row, "row")
    if not 1 <= r <= N_ROWS:
        raise ValueError("row %d outside the TSV rows 1..%d" % (r, N_ROWS))
    return [ROOT_ENTROPY, TARGET_OFFSET + t, r, _leg_no(leg), _nonneg_int(map_index, "map_index"),
            _nonneg_int(cell_index, "cell_index")]


def claim_seed(target_number, row, leg, map_index, cell_index) -> np.random.SeedSequence:
    """SeedSequence([20260925, 100 + target number, row, leg, map index, cell index]) (claims_register.md:1076-1082).
    `leg` is a registered leg number or name."""
    return np.random.SeedSequence(_claim_words(target_number, row, leg, map_index, cell_index))


def seed_int(ss: np.random.SeedSequence) -> int:
    """R7: int(np.random.default_rng(SS).integers(2**31))."""
    if not isinstance(ss, np.random.SeedSequence):
        raise TypeError("a SeedSequence is required")
    return int(np.random.default_rng(ss).integers(2 ** 31))


def leg_rng(ss: np.random.SeedSequence) -> np.random.Generator:
    """R7: np.random.default_rng(SS)."""
    if not isinstance(ss, np.random.SeedSequence):
        raise TypeError("a SeedSequence is required")
    return np.random.default_rng(ss)


def same_seed_sequence(a: np.random.SeedSequence, b: np.random.SeedSequence) -> bool:
    """Equal entropy, spawn key and pool size, and equal generated state (8 words)."""
    return (list(np.atleast_1d(a.entropy)) == list(np.atleast_1d(b.entropy)) and tuple(a.spawn_key) == tuple(b.spawn_key)
            and a.pool_size == b.pool_size and bool(np.array_equal(a.generate_state(8), b.generate_state(8))))


def g3_seed(target_number, row, map_index, cell_index) -> np.random.SeedSequence:
    """R24: SeedSequence(entropy=[20260925, 100 + target, row, 3, map index, cell index], spawn_key=(0,)), the first
    child of the G3m leg's key; asserted equal to `claim_seed(..., 3, ...).spawn(1)[0]` (on a fresh parent, so no
    caller's leg-3 SeedSequence is advanced)."""
    words = _claim_words(target_number, row, G3M_LEG, map_index, cell_index)
    ss = np.random.SeedSequence(entropy=words, spawn_key=(0,))
    child = np.random.SeedSequence(words).spawn(1)[0]
    assert same_seed_sequence(ss, child), "R24: the G3 key is not the first spawned child of leg 3's key"
    return ss


def plant_seed(plant_id, case, class_id) -> np.random.SeedSequence:
    """§7: SeedSequence([20260925, 900, plant_id, case, class_id])."""
    return np.random.SeedSequence([ROOT_ENTROPY, PLANT_WORD, _nonneg_int(plant_id, "plant_id"), _nonneg_int(case, "case"),
                                   _nonneg_int(class_id, "class_id")])


# ---- plant keys of the runner's plant view (module docstring; PLANT CHOICE (orchestrator, 2026-10-01)) -------------
PLANT_CLASS_IDS: dict[str, int] = {"dk-ctx": 2, "V-AAL": 11, "V-DK": 12, "V-DK-subcortex": 13, "MIST64": 14,
                                   "V-CC200": 17}
PLANT_CLASS_IDS_TAKEN: dict[int, str] = {15: "forms.SYN_LIU_CLASS_ID['brainspan'] (synthetic Liu BrainSpan-like data)",
                                         16: "forms.SYN_LIU_CLASS_ID['ahba'] (synthetic Liu AHBA-like data)"}
LETTERED_PLANTS: dict[str, int] = {"P3a": 3, "P3b": 3}
PLANT_CASE_RANGES: dict[str, tuple] = {"P3a": (0, 1000), "P3b": (1000, None)}   # [lo, hi); None: no upper bound
PLANT_DATA_WORD = 1000   # the synthetic-data word in the leg position (never a registered leg number)
P2_CLAIM_KEYS = "P2"     # the declared exception: P2's purpose is the claim keys (RUN_PLAN §7 :1128)
assert len(set(PLANT_CLASS_IDS.values())) == len(PLANT_CLASS_IDS)
assert not set(PLANT_CLASS_IDS.values()) & set(PLANT_CLASS_IDS_TAKEN)
assert PLANT_DATA_WORD not in LEG_NAMES


def plant_class_id(cls: str) -> int:
    """The fixed integer of a class in plant keys (PLANT_CLASS_IDS); any other class is refused."""
    if cls not in PLANT_CLASS_IDS:
        raise ValueError("no plant class id for %r (PLANT_CLASS_IDS: %s)" % (cls, ", ".join(PLANT_CLASS_IDS)))
    return PLANT_CLASS_IDS[cls]


def plant_int(plant: str) -> int:
    """The integer plant_id of a plant name: P<n> -> n; a lettered plant (LETTERED_PLANTS) -> its number; anything
    else refused (ValueError)."""
    if not isinstance(plant, str):
        raise ValueError("plant id must be a string such as 'P12', got %r" % (plant,))
    if plant in LETTERED_PLANTS:
        return LETTERED_PLANTS[plant]
    m = re.fullmatch(r"P([0-9]+)", plant)
    if not m:
        raise ValueError("plant id %r: P<integer> or one of the mapped lettered ids %s" % (plant, sorted(LETTERED_PLANTS)))
    if int(m.group(1)) in LETTERED_PLANTS.values():   # P3's word belongs to P3a / P3b (kept apart by case ranges)
        raise ValueError("plant id %r: its number is the lettered plants' %s (use one of them)"
                         % (plant, sorted(k for k, v in LETTERED_PLANTS.items() if v == int(m.group(1)))))
    return int(m.group(1))


def plant_case_range(plant: str) -> tuple:
    """[lo, hi) of the case numbers a plant may use (hi None: unbounded); P3a / P3b are kept apart this way."""
    plant_int(plant)
    return PLANT_CASE_RANGES.get(plant, (0, None))


def check_plant_case(plant: str, case) -> int:
    """The case number if it lies in the plant's range (plant_case_range), else ValueError."""
    c = _nonneg_int(case, "case")
    lo, hi = plant_case_range(plant)
    if c < lo or (hi is not None and c >= hi):
        raise ValueError("plant %s: case %d outside its range [%d, %s)" % (plant, c, lo, "inf" if hi is None else hi))
    return c


def _plant_words(plant_id, case, class_id) -> list[int]:
    return [ROOT_ENTROPY, PLANT_WORD, _nonneg_int(plant_id, "plant_id"), _nonneg_int(case, "case"),
            _nonneg_int(class_id, "class_id")]


def plant_leg_seed(plant_id, case, class_id, leg) -> np.random.SeedSequence:
    """SeedSequence([20260925, 900, plant_id, case, class_id, leg]) with the registered leg number (name or number)."""
    return np.random.SeedSequence(_plant_words(plant_id, case, class_id) + [_leg_no(leg)])


def plant_g3_seed(plant_id, case, class_id) -> np.random.SeedSequence:
    """R24 in a plant case: SeedSequence(entropy=[20260925, 900, plant_id, case, class_id, 3], spawn_key=(0,)), asserted
    equal to the first spawned child of the case's leg-3 key."""
    words = _plant_words(plant_id, case, class_id) + [G3M_LEG]
    ss = np.random.SeedSequence(entropy=words, spawn_key=(0,))
    child = np.random.SeedSequence(words).spawn(1)[0]
    assert same_seed_sequence(ss, child), "R24: the plant G3 key is not the first spawned child of leg 3's key"
    return ss


def plant_data_seed(plant_id, case, class_id, word) -> np.random.SeedSequence:
    """Synthetic data of a plant case: SeedSequence([20260925, 900, plant_id, case, class_id, 1000, word])."""
    return np.random.SeedSequence(_plant_words(plant_id, case, class_id) + [PLANT_DATA_WORD, _nonneg_int(word, "word")])


def plant_j1_draws(plant_id, case, class_id) -> dict:
    """R7's J1 order on the plant case's leg-14 key: S1c seed, S2c seed, then the G2 sets (the returned `rng`)."""
    key = plant_leg_seed(plant_id, case, class_id, J1_LEG)
    g = np.random.default_rng(key)
    s1c = int(g.integers(2 ** 31))
    s2c = int(g.integers(2 ** 31))
    return {"key": key, "S1c_seed": s1c, "S2c_seed": s2c, "rng": g}


def plant_naive_joint_draws(plant_id, case, class_id) -> dict:
    """R7's naive-joint order on the plant case's leg-15 key: S1 seed, then the G1 sets (the returned `rng`)."""
    key = plant_leg_seed(plant_id, case, class_id, NAIVE_JOINT_LEG)
    g = np.random.default_rng(key)
    s1 = int(g.integers(2 ** 31))
    return {"key": key, "S1_seed": s1, "rng": g}


def j1_draws(target_number, row, map_index, cell_index) -> dict:
    """R7, J1 (leg 14): one generator g = default_rng(SS_14); S1c seed, then S2c seed, then the G2 sets (the returned
    `rng`, already advanced past the two seeds)."""
    key = claim_seed(target_number, row, J1_LEG, map_index, cell_index)
    g = np.random.default_rng(key)
    s1c = int(g.integers(2 ** 31))
    s2c = int(g.integers(2 ** 31))
    return {"key": key, "S1c_seed": s1c, "S2c_seed": s2c, "rng": g}


def naive_joint_draws(target_number, row, map_index, cell_index) -> dict:
    """R7, naive joint (leg 15): one generator g = default_rng(SS_15); S1 seed, then the G1 sets (the returned `rng`)."""
    key = claim_seed(target_number, row, NAIVE_JOINT_LEG, map_index, cell_index)
    g = np.random.default_rng(key)
    s1 = int(g.integers(2 ** 31))
    return {"key": key, "S1_seed": s1, "rng": g}


def key_record(ss: np.random.SeedSequence) -> dict:
    """A JSON-able record of a SeedSequence key (entropy words, spawn key, pool size)."""
    ent = ss.entropy
    words = [int(x) for x in (ent if isinstance(ent, (list, tuple, np.ndarray)) else [ent])]
    return {"entropy": words, "spawn_key": [int(x) for x in ss.spawn_key], "pool_size": int(ss.pool_size)}


def seed_record(target_number, row, map_index, cell_index, legs: Mapping[str, str] | Iterable[str] = (), *,
                g3: bool = False, j1: bool = False, naive_joint: bool = False) -> dict:
    """R7 "Every row records SS keys and integer seeds": the keys of the row's legs and the integer seeds actually used.
    `legs` maps a leg name (or number) to its use, "int" (one integer seed, `seed_int`) or "rng" (a Generator,
    `leg_rng`); an iterable of names means "rng" for each. The caller states the use; this function never infers it.
    J1 and the naive joint record their key and the integer seeds drawn in R7's order; G3 records R24's key."""
    uses = dict(legs) if isinstance(legs, Mapping) else {k: "rng" for k in legs}
    out = {"target_number": _nonneg_int(target_number, "target_number"), "row": _nonneg_int(row, "row"),
           "map_index": _nonneg_int(map_index, "map_index"), "cell_index": _nonneg_int(cell_index, "cell_index"),
           "legs": []}
    for leg, use in uses.items():
        n = _leg_no(leg)
        if n in (J1_LEG, NAIVE_JOINT_LEG):
            raise ValueError("J1 / naive joint are recorded through j1=True / naive_joint=True (R7's draw order)")
        if use not in ("int", "rng"):
            raise ValueError("use must be 'int' or 'rng', got %r" % (use,))
        ss = claim_seed(target_number, row, n, map_index, cell_index)
        rec = {"leg": LEG_NAMES[n], "leg_no": n, "use": use, "key": key_record(ss)}
        if use == "int":
            rec["seed_int"] = seed_int(ss)
        out["legs"].append(rec)
    if g3:
        out["G3"] = {"key": key_record(g3_seed(target_number, row, map_index, cell_index)),
                     "rule": "R24: first spawned child of leg 3's key"}
    if j1:
        d = j1_draws(target_number, row, map_index, cell_index)
        out["J1"] = {"key": key_record(d["key"]), "S1c_seed": d["S1c_seed"], "S2c_seed": d["S2c_seed"],
                     "order": "S1c seed, S2c seed, then the G2 sets (R7)"}
    if naive_joint:
        d = naive_joint_draws(target_number, row, map_index, cell_index)
        out["naive_joint"] = {"key": key_record(d["key"]), "S1_seed": d["S1_seed"],
                              "order": "S1 seed, then the G1 sets (R7)"}
    return out


def plant_seed_record(plant_id, case, class_id, legs: Mapping[str, str] | Iterable[str] = (), *, g3: bool = False,
                      j1: bool = False, naive_joint: bool = False, row=None, map_index=None, cell_index=None) -> dict:
    """seed_record's layout for a plant case (module docstring; PLANT CHOICE (orchestrator, 2026-10-01)): every leg's
    key SeedSequence([20260925, 900, plant_id, case, class_id, leg]) and its integer seed where used; G3 = R24's child
    of the case's leg-3 key; J1 / naive joint in R7's order. row / map_index / cell_index: the TSV row the plant case
    runs through (recorded only; never a key word)."""
    uses = dict(legs) if isinstance(legs, Mapping) else {k: "rng" for k in legs}
    out = {"keys": "plant", "plant_id": _nonneg_int(plant_id, "plant_id"), "case": _nonneg_int(case, "case"),
           "class_id": _nonneg_int(class_id, "class_id"), "row": row, "map_index": map_index, "cell_index": cell_index,
           "rule": "SeedSequence([20260925, 900, plant_id, case, class_id, leg]) (PLANT CHOICE (orchestrator, "
                   "2026-10-01): leg streams within a plant case; RUN_PLAN §7 :1121-1122)",
           "legs": []}
    for leg, use in uses.items():
        n = _leg_no(leg)
        if n in (J1_LEG, NAIVE_JOINT_LEG):
            raise ValueError("J1 / naive joint are recorded through j1=True / naive_joint=True (R7's draw order)")
        if use not in ("int", "rng"):
            raise ValueError("use must be 'int' or 'rng', got %r" % (use,))
        ss = plant_leg_seed(plant_id, case, class_id, n)
        rec = {"leg": LEG_NAMES[n], "leg_no": n, "use": use, "key": key_record(ss)}
        if use == "int":
            rec["seed_int"] = seed_int(ss)
        out["legs"].append(rec)
    if g3:
        out["G3"] = {"key": key_record(plant_g3_seed(plant_id, case, class_id)),
                     "rule": "R24: first spawned child of the plant case's leg-3 key"}
    if j1:
        d = plant_j1_draws(plant_id, case, class_id)
        out["J1"] = {"key": key_record(d["key"]), "S1c_seed": d["S1c_seed"], "S2c_seed": d["S2c_seed"],
                     "order": "S1c seed, S2c seed, then the G2 sets (R7)"}
    if naive_joint:
        d = plant_naive_joint_draws(plant_id, case, class_id)
        out["naive_joint"] = {"key": key_record(d["key"]), "S1_seed": d["S1_seed"],
                              "order": "S1 seed, then the G1 sets (R7)"}
    return out
