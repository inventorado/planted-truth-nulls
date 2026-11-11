"""Common harness of the WP2 plants (RUN_PLAN.md v3.1 §7; see a1_audit/plants/__init__.py).

1. Plant ids and seeds (§7 "Seeds: SeedSequence([20260925, 900, plant_id, case, class_id])", seeds.plant_seed).
   plant_id and class_id come from seeds.py's plant interface (orchestrator decision on WP1 review B3: plant_class_id,
   the lettered-id mapping); the case ranges keep P3a (cases 0..19) and P3b (cases 1000 + j) apart if they share an id.
   PLANT CHOICE (not in §7): one claim (one map x one set x one class) has one case number; its CONSTRUCTION stream is
   default_rng(SeedSequence([20260925, 900, plant_id, case, class_id])) and each null leg L draws from
   SeedSequence([20260925, 900, plant_id, case, class_id, L]) with L the registered leg number (claims_register.md
   :1080-1082: S1c 0, S2c 1, G1 2, G3m 3, G6s 4, G6l 5, permutation 8, re-selection 10, G2 11, G4 12, G5 13, J1 14,
   naive joint 15, T_abs 21-25), the leg word appended as the 6th word, as WP1's tests' plant keys
   (tests/test_verdict.plant_keys); G3 (R24) = SeedSequence(entropy=[..., 3], spawn_key=(0,)), the first child of the
   G3m leg's key; plant-only flawed legs take words >= 90 (90: P26's within-class permutation), never a registered leg
   number. A plant's leg integer seeds follow R7 (int(default_rng(SS).integers(2**31)), inside the adapters).
   Target 900 does not exist, so no plant key equals a claim key ([20260925, 100 + target, ...], 101..121; asserted).
2. Class contexts on the real §3.1 matrices (dk-ctx, V-DK, V-AAL through adapters.build_context_checked: RUN_PLAN_amend_1
   R35's first-use reader check, then a3_port.build_context with its L7 pin); V-DK-subcortex (V-DK's 7 left subcortical
   parcels) and MIST64 (46 primary parcels; tissue classes from register_maps/mist64_classes.json) built here on the
   same reader, with both readers' hashes asserted against launch.py's pins (L6, L7, R35).
3. CaseSources: run.Sources for one synthetic claim; the production calls (run.prepare, plant_mode.streams_screen,
   run.g_legs, verdict.assemble_verdict_a1, run.g_descriptors) and compact records.
"""
from __future__ import annotations

import functools
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from .. import run as R  # noqa: F401  (forces OMP_NUM_THREADS=1; puts src/ on sys.path through a3_port)
from .. import a3_port as A3
from .. import adapters as AD
from .. import descriptors as DS  # noqa: F401
from .. import launch as LA
from .. import plant_mode as PM
from .. import seeds as SD
from .. import verdict as V

REPO = R.REPO
ALPHA = 0.025                     # alpha_v (prereg_amend_3.md:73)
K_PLANT = dict(R.PLANT_K)         # site 500, species 200 (RUN_PLAN §7 cost model); permutation 500; U6 descriptor counts
G6L_MODE = PM.MODE_PLANT          # amendment 3's plant mode (K = 200 accepted, budget 1,000; RUN_PLAN §7)
PLUS, MINUS = 1, -1

# ---- ids (the seeds.py interface of the orchestrator's decision; provisional values only for scratch tests) ------
# Orchestrator decision (2026-10-01, standing delegation; WP1 review B3): "in plant view every leg of a plant case draws
# from SeedSequence([20260925, 900, plant_id, case, class_id, leg]) with the claim leg numbers (R24 G3 = first spawned
# child of the case's leg-3 key ...); seeds.py will gain plant_class_id() (a fixed integer per class) and an integer
# mapping for lettered plant ids". class_id(cls) and plant_int(id) read that interface; until it exists they refuse
# (SeedInterfacePending), except under A1_PLANTS_PROVISIONAL_IDS=1 (scratch code-path tests only: the driver refuses
# that mode, so no plant output ever carries a provisional id).
PROVISIONAL_PLANT_INT = {"P3a": 3, "P3b": 3, "P4": 4, "P5": 5, "P6": 6, "P7": 7, "P8": 8, "P11": 11, "P12": 12,
                         "P22": 22, "P24": 24, "P25": 25, "P26": 26}
PROVISIONAL_CLASS_ID = {k: int(v["class_id"]) for k, v in R.SYN_CLASSES.items()}
PLANT_ONLY_LEGS = {"within-class permutation (plant only)": 90}
REGISTERED_LEG_NUMBERS = frozenset(SD.LEGS.values())
assert not (set(PLANT_ONLY_LEGS.values()) & REGISTERED_LEG_NUMBERS)
SEED_RULE = ("construction: default_rng(SeedSequence([20260925, 900, plant_id, case, class_id])) (seeds.plant_seed); "
             "leg L: SeedSequence([20260925, 900, plant_id, case, class_id, L]), L the registered leg number "
             "(claims_register.md:1080-1082); G3 (R24): SeedSequence(entropy=[..., 3], spawn_key=(0,)); plant-only legs "
             "L >= 90 (90: within-class permutation, P26)")


class SeedInterfacePending(RuntimeError):
    pass


def _provisional() -> bool:
    import os
    return os.environ.get("A1_PLANTS_PROVISIONAL_IDS") == "1"


def _sd_plant_int():
    for name in ("plant_int", "plant_id_int", "plant_number", "plant_id_of", "plant_integer_id"):
        f = getattr(SD, name, None)
        if callable(f):
            return f
    for name in ("PLANT_IDS", "PLANT_INT", "PLANT_ID_INT", "LETTERED_PLANTS"):
        t = getattr(SD, name, None)
        if isinstance(t, dict):
            return lambda pid, t=t: t[pid] if pid in t else int(str(pid).lstrip("P"))
    return None


def class_id(cls: str) -> int:
    f = getattr(SD, "plant_class_id", None)
    if f is not None:
        return int(f(cls))
    if _provisional():
        return PROVISIONAL_CLASS_ID[cls]
    raise SeedInterfacePending("seeds.plant_class_id is not present (wp1-fix pending)")


def plant_int(pid: str) -> int:
    f = _sd_plant_int()
    if f is not None:
        return int(f(pid))
    if _provisional():
        return PROVISIONAL_PLANT_INT[pid]
    raise SeedInterfacePending("seeds.py's integer mapping of plant ids is not present (wp1-fix pending)")


def seed_interface_record() -> dict:
    f = _sd_plant_int()
    return dict(plant_class_id=getattr(SD, "plant_class_id", None) is not None, plant_int=f is not None,
                provisional=_provisional(),
                class_ids={c: class_id(c) for c in PROVISIONAL_CLASS_ID},
                plant_ids={p: plant_int(p) for p in PROVISIONAL_PLANT_INT})


def require_seed_interface() -> dict:
    """The driver's check: seeds.py's plant interface present, never the provisional values."""
    if _provisional():
        raise SystemExit("refused: A1_PLANTS_PROVISIONAL_IDS is set (scratch tests only)")
    if getattr(SD, "plant_class_id", None) is None or _sd_plant_int() is None:
        raise SystemExit("refused: seeds.py lacks the plant interface (plant_class_id and the plant-id mapping; "
                         "wp1-fix pending)")
    rec = seed_interface_record()
    if len(set(rec["class_ids"].values())) != len(rec["class_ids"]):
        raise SystemExit("refused: seeds.plant_class_id is not one integer per class")
    return rec


class PlantKeys:
    """The seed keys of one plant claim (module docstring, item 1), through seeds.py's plant interface (orchestrator
    decision, WP1 review B3): legs seeds.plant_leg_seed (SeedSequence([20260925, 900, plant_id, case, class_id, leg])),
    G3 seeds.plant_g3_seed, records seeds.plant_seed_record; the construction stream is seeds.plant_seed itself (the
    five words §7 states; never a leg stream (six words), a data stream of run.SyntheticSources (seven words,
    seeds.plant_data_seed) or a G3 stream (spawned)). Plant-only flawed legs take words >= 90, never a registered leg
    number (PLANT_ONLY_LEGS). seed_of / tabs_seed_of / g3_seed have the signatures of verdict.seed_callables'
    callables, so every adapter and descriptor leg takes them unchanged; every key handed out is recorded."""

    def __init__(self, plant_id: int, case: int, class_id: int):
        self.plant_id, self.case, self.class_id = int(plant_id), int(case), int(class_id)
        self.words = [SD.ROOT_ENTROPY, SD.PLANT_WORD, self.plant_id, self.case, self.class_id]
        self.construction = SD.plant_seed(self.plant_id, self.case, self.class_id)
        if [int(x) for x in self.construction.entropy] != self.words:
            raise AssertionError("plant key words differ from seeds.plant_seed's")
        if self.words[1] in range(SD.TARGET_OFFSET + 1, SD.TARGET_OFFSET + SD.N_TARGETS + 1):
            raise AssertionError("a plant key would carry a claim key's target word")
        self.used: dict[str, int] = {}

    def rng(self) -> np.random.Generator:
        return np.random.default_rng(self.construction)

    def leg(self, leg_no: int) -> np.random.SeedSequence:
        if int(leg_no) in PLANT_ONLY_LEGS.values():
            return np.random.SeedSequence(self.words + [int(leg_no)])
        ss = SD.plant_leg_seed(self.plant_id, self.case, self.class_id, int(leg_no))
        if [int(x) for x in ss.entropy] != self.words + [int(leg_no)]:
            raise AssertionError("seeds.plant_leg_seed's words differ from the decided rule")
        return ss

    def seed_of(self, name: str) -> np.random.SeedSequence:
        reg = V.LEG_ALIASES.get(name, name)
        if reg in SD.LEGS:
            no = SD.LEGS[reg]
            if reg.startswith("T_abs"):
                raise ValueError("T_abs legs go through tabs_seed_of")
        elif name in PLANT_ONLY_LEGS:
            no = PLANT_ONLY_LEGS[name]
        else:
            raise ValueError(f"no leg {name!r}")
        self.used[name] = no
        return self.leg(no)

    def tabs_seed_of(self, name: str) -> np.random.SeedSequence:
        if name not in V.TABS_LEGS:
            raise ValueError(f"T_abs has no leg {name!r}")
        no = SD.LEGS[V.TABS_LEGS[name]]
        self.used[V.TABS_LEGS[name]] = no
        return self.leg(no)

    def g3_seed(self) -> np.random.SeedSequence:
        self.used["G3 (R24)"] = -1
        return SD.plant_g3_seed(self.plant_id, self.case, self.class_id)

    def callables(self) -> dict:
        return dict(seed_of=self.seed_of, tabs_seed_of=self.tabs_seed_of, g3_seed=self.g3_seed,
                    key=dict(plant_id=self.plant_id, case=self.case, class_id=self.class_id))

    def record(self) -> dict:
        """seeds.plant_seed_record of the registered legs drawn (integer seeds for the site legs), plus the plant-only
        legs and the construction key."""
        uses, g3, j1, nj = {}, False, False, False
        for name, no in self.used.items():
            if no < 0:
                g3 = True
            elif no == SD.J1_LEG:
                j1 = True
            elif no == SD.NAIVE_JOINT_LEG:
                nj = True
            elif no in PLANT_ONLY_LEGS.values():
                continue
            else:
                uses[SD.LEG_NAMES[no]] = "int" if SD.LEG_NAMES[no] in ("S1c", "S2c", "T_abs S1c", "T_abs S2c") else "rng"
        rec = SD.plant_seed_record(self.plant_id, self.case, self.class_id, dict(sorted(uses.items())), g3=g3, j1=j1,
                                   naive_joint=nj)
        rec["construction"] = dict(entropy=list(self.words), rule="seeds.plant_seed (RUN_PLAN §7 :1121-1122)")
        rec["plant_only_legs"] = {name: dict(leg_word=no, entropy=self.words + [no]) for name, no in self.used.items()
                                  if no in PLANT_ONLY_LEGS.values()}
        return rec


# ---- class contexts on the §3.1 matrices --------------------------------------------------------------------------
ATLAS = {"dk-ctx": "dk", "V-DK": "dk", "V-AAL": "aal", "V-DK-subcortex": "dk", "MIST64": "mist64"}
CLASS_COUNTS = {"dk-ctx": {"cortex": 34}, "V-DK": {"cortex": 34, "subcortex/brainstem": 8},
                "V-AAL": {"cerebellum": 9, "cortex": 38, "subcortex/brainstem": 7},
                "V-DK-subcortex": {"subcortex/brainstem": 7},
                "MIST64": {"cerebellum": 8, "cortex": 33, "subcortex/brainstem": 5}}
MIST64_CLASSES_JSON = REPO / "arcs" / "audit" / "register_maps" / "mist64_classes.json"
MIST64_CLASS_MAP = {"cortex": "cortex", "cerebellum": "cerebellum", "subcortex": "subcortex/brainstem"}


def _pin(table, key):
    hits = [v for k, v in table if k == key]
    if len(hits) != 1:
        raise KeyError(key)
    return hits[0]


@functools.lru_cache(maxsize=None)
def reader_check(atlas: str) -> dict:
    """R35 for the atlas's matrix in this process (launch.matrix_first_use on the frame A1's reader handed over), the
    file's sha256 against L6 and both readers' hash_pandas_object sha256 against L7 / R35's pins (launch.py)."""
    path = A3.AHBA / f"{atlas}_expr.csv.gz"
    sha = A3.sha256_file(path)
    want = _pin(LA.AHBA_FILES, f"{atlas}_expr.csv.gz")
    if sha != want:
        raise AssertionError(f"{atlas}: file sha256 {sha} != L6 pin {want}")
    rec = dict(LA.matrix_first_use(path, used=A3._primary(atlas)[0]))
    if rec["sha256_round_trip"] != _pin(LA.AHBA_MATRIX, atlas):
        raise AssertionError(f"{atlas}: round-trip reader hash != L7 pin")
    if rec["sha256_default"] != _pin(LA.AHBA_DEFAULT_READER, atlas):
        raise AssertionError(f"{atlas}: default reader hash != R35 pin")
    rec["file_sha256"] = sha
    return rec


def _mist64_classes(ids) -> np.ndarray:
    doc = json.loads(MIST64_CLASSES_JSON.read_text(encoding="utf-8"))
    prim = {int(p["roi"]): p["tissue_class"] for p in doc["parcels"] if p["primary"]}
    if sorted(prim) != sorted(int(i) for i in ids):
        raise AssertionError("MIST64: the reader's primary parcels differ from mist64_classes.json's")
    return np.array([MIST64_CLASS_MAP[prim[int(i)]] for i in ids])


@functools.lru_cache(maxsize=None)
def class_context(name: str) -> A3.ClassContext:
    """The class context on its primary parcels (module docstring, item 2); class counts asserted."""
    if name in ("dk-ctx", "V-DK", "V-AAL"):
        reader_check(ATLAS[name])
        ctx = AD.build_context_checked(name)
    elif name == "V-DK-subcortex":
        # PLANT CHOICE (not in §7): V-DK-subcortex = V-DK's 7 left subcortical parcels (atlas structure
        # 'subcortex/brainstem', hemisphere L; the midline brainstem excluded): claims_register.md:1026 "a
        # subcortex-only map -> V-DK's subcortical parcels, single class"; RUN_PLAN P9 "(7 parcels, single class)"
        class_context("V-DK")
        expr, classes, xyz = A3._primary("dk")
        info = A3.atlas_info("dk")
        hemi = info.loc[expr.index, "hemisphere"].astype(str).to_numpy()
        keep = (classes == "subcortex/brainstem") & (hemi == "L")
        ctx = A3.ClassContext("V-DK-subcortex", expr.loc[keep], classes[keep], xyz[keep], info, None, "dk",
                              A3.verify_matrix("dk"))
    elif name == "MIST64":
        # PLANT CHOICE (not in §7): MIST64 context = A1's reader (e3_plants.primary_parcels: L + B rows, 46 parcels)
        # with the tissue classes of register_maps/mist64_classes.json (subcortex written 'subcortex/brainstem' as
        # the other atlases' class label; the partition is asserted equal to the atlas info's)
        rec = reader_check("mist64")
        expr, classes_atlas, xyz = A3._primary("mist64")
        classes = _mist64_classes(expr.index)
        if not np.array_equal(classes, classes_atlas):
            raise AssertionError("MIST64: mist64_classes.json's tissue classes differ from the atlas info's")
        ctx = A3.ClassContext("MIST64", expr, classes, xyz, A3.atlas_info("mist64"), None, "mist64",
                              dict(matrix_sha256=rec["sha256_round_trip"], file_sha256=rec["file_sha256"]))
    else:
        raise ValueError(f"no plant class {name!r}")
    got = {str(c): int((ctx.classes == c).sum()) for c in np.unique(ctx.classes)}
    if got != CLASS_COUNTS[name]:
        raise AssertionError(f"{name}: class counts {got} != {CLASS_COUNTS[name]}")
    if not np.isfinite(ctx.X).all():
        raise AssertionError(f"{name}: non-finite matrix value")
    return ctx


@functools.lru_cache(maxsize=None)
def context_sha(name: str) -> str:
    ctx = class_context(name)
    return R.arr_sha(ctx.X, np.asarray(ctx.parcel_ids), np.array(ctx.classes, dtype=str), ctx.xyz, ctx.brain)


def context_report(name: str) -> dict:
    ctx = class_context(name)
    rep = {k: v for k, v in ctx.report.items() if k != "parcel_ids"}
    rep["context_sha256"] = context_sha(name)
    rep["reader_check"] = {k: v for k, v in reader_check(ATLAS[name]).items() if k != "versions"}
    return rep


@functools.lru_cache(maxsize=1)
def brainspan():
    """The BrainSpan trajectories the frozen code reads (asdg.brainspan.load_trajectories; prereg §4.3), P22 only."""
    from asdg.brainspan import load_trajectories
    T, info = load_trajectories()
    sha = R.arr_sha(T.to_numpy(dtype=float), np.array(T.index, dtype=str), np.array(T.columns, dtype=str))
    return T, info, sha


# ---- sources of one synthetic claim (run.Sources) -------------------------------------------------------------------
class CaseSources(R.Sources):
    """run.Sources for one plant claim: the class context on its §3.1 matrix, the plant's map y on every primary
    parcel, its set (gene symbols), its fixed component; trajectories = BrainSpan (P22). PLANT CHOICE (not in §7): the
    AHBA sample count of every primary parcel is 1 (each has a matrix row with no missing value, asserted by
    class_context), so the §4 rule keeps every parcel where y is finite."""
    kind = "plant"
    synthetic = True

    def __init__(self, cls: str, y, genes=None, component=None):
        self.cls = cls
        self.y = np.asarray(y, dtype=float)
        self.genes = None if genes is None else [str(g) for g in genes]
        self.comp = None if component is None else np.asarray(component, dtype=float)

    def spec(self) -> dict:
        return {"kind": "plant (a1_audit.plants.common.CaseSources)", "class": self.cls}

    def context(self, cls):
        if cls != self.cls:
            raise R.SourceUnavailable(R.REFUSED_CLASS, f"plant claim of class {self.cls}, asked for {cls}")
        ctx = class_context(cls)
        return ctx, {int(i): 1 for i in ctx.parcel_ids}, context_sha(cls)

    def map(self, plan, map_index):
        ctx = class_context(self.cls)
        ids = np.asarray(ctx.parcel_ids, dtype=np.int64)
        if self.y.shape != ids.shape:
            raise ValueError("plant map: one value per primary parcel")
        return self.y, ids, self.cls, {f"map[{int(map_index)}]": R.arr_sha(self.y, ids)}

    def gene_set(self, plan):
        if self.genes is None:
            raise R.SourceUnavailable(R.REFUSED_NO_SET, "plant claim without a set")
        return list(self.genes), R.sha256_bytes("\n".join(self.genes).encode("utf-8"))

    def component(self, plan):
        if self.comp is None:
            raise R.SourceUnavailable(R.NOT_RUN_WP3, "plant claim without a fixed component")
        ids = np.asarray(class_context(self.cls).parcel_ids, dtype=np.int64)
        return self.comp, ids, R.arr_sha(self.comp, ids)

    def trajectories(self, cls):
        T, _, sha = brainspan()
        return T, sha

    def donor_counts(self, cls):
        raise R.SourceUnavailable(R.NOT_RUN_WP3, "donor counts are not part of any WP2 plant")

    def resolve_class(self, plan):
        raise R.SourceUnavailable(R.REFUSED_CLASS, "plant classes are determined")

    def selection_rule(self, plan, ctx):
        raise R.SourceUnavailable(R.NOT_RUN_WP3, "no selected list in the WP2 plants")


def plan_of(form: str, cls: str, *, has_set: bool = True, component: dict | None = None) -> dict:
    """The fields run.prepare reads from a row's plan (run._head / _by_form); a plant claim has no TSV row."""
    return dict(row=0, target_no=0, analysis_class=cls, has_set=bool(has_set), form=form, component=component,
                two_sided=None, registered_direction=None, maps=[0], cell_index=0)


def genes_of(cls: str, S) -> list[str]:
    ctx = class_context(cls)
    return [str(ctx.U.genes[int(g)]) for g in S]


def prepare(form: str, cls: str, y, S=None, *, component: dict | None = None, component_values=None) -> R.Prep:
    """run.prepare (the §4 analysis-parcel rule, ClassContext.restrict, adapters.make_adapter) through CaseSources;
    asserts every primary parcel kept and the set's columns unchanged."""
    genes = None if S is None else genes_of(cls, S)
    src = CaseSources(cls, y, genes, component_values)
    plan = plan_of(form if component is None else "component", cls, has_set=S is not None, component=component)
    pr = R.prepare(plan, src, 0, "primary")
    base = class_context(cls)
    if [int(i) for i in pr.parcel_ids] != [int(i) for i in base.parcel_ids]:
        raise AssertionError("a plant map must keep every primary parcel")
    if S is not None and pr.S is not None and not np.array_equal(pr.S, np.asarray(S, dtype=int)):
        raise AssertionError("the prepared set's columns differ from the construction's")
    return pr


def g6l_screen(pr: R.Prep, keys: PlantKeys, K: dict, mode: str = G6L_MODE, stream: str = "G6l"):
    """plant_mode.streams_screen on the prepared context for the claim's G6l stream (leg 5; 'T_abs G6l' = leg 25)."""
    ss = keys.seed_of("G6l") if stream == "G6l" else keys.tabs_seed_of("G6l")
    return PM.streams_screen(mode, pr.ctx, pr.S, {stream: ss}, int(K["species"]))[stream]


def full_legs(pr: R.Prep, keys: PlantKeys, K: dict, screen=None) -> dict:
    """run.g_legs (verdict.collect_legs) on the claim's keys; the G6l windows from g6l_screen for full forms."""
    if pr.plan["form"] in V.FULL_FORMS and screen is None:
        screen = g6l_screen(pr, keys, K)
    return R.g_legs(pr, K, keys.seed_of, screen)["legs"]


def assemble(legs: dict, spec: str) -> dict:
    """spec: '+' / '-' (one-sided, registered direction) or 'two' (R1)."""
    if spec == "two":
        return V.assemble_verdict_a1(legs, two_sided=True)
    return V.assemble_verdict_a1(legs, two_sided=False, registered_direction=PLUS if spec == "+" else MINUS)


def species_only(pr: R.Prep, keys: PlantKeys, K: dict, screen, adapter=None) -> dict:
    """The species leg alone: adapter.species_leg (the call verdict.collect_legs makes, verdict.py:235) with the
    consistency checks collect_legs applies to it (verdict.py:240-247) and the uninformative flag (amendment 3 §2)."""
    ad = pr.adapter if adapter is None else adapter
    sp = ad.species_leg(int(K["species"]), keys.seed_of, g6l=screen)
    st = dict(sp["status"])
    if st["G6s"] != "ok" or sp["p"]["G6s"] is None:
        raise RuntimeError("G6s needs no pool and must always be computed")
    for leg in ("G1", "G3m", "G6l"):
        if (st[leg] == "ok") != (sp["p"][leg] is not None):
            raise RuntimeError(f"{leg}: status {st[leg]!r} disagrees with its p")
    flag, share = ad.uninformative()
    return dict(p={k: (None if v is None else {PLUS: float(v[PLUS]), MINUS: float(v[MINUS])}) for k, v in sp["p"].items()},
                status=st, floors=dict(sp["floors"]), g6l=dict(sp["g6l_info"]), uninformative=bool(flag),
                uninformative_share=float(share), species_obs=float(sp.get("species_obs", ad.T_obs)),
                null=sp["null"])


def species_rejects(sp: dict, d: int = PLUS, alpha: float = ALPHA) -> bool:
    """Amendment 3 §5's species-leg rejection: p_species = max(G1, G3m, G6s, G6l) < alpha in direction d; a G6l
    without a p (unmatched / degenerate), an uninformative or a resolution-limited claim is a non-rejection."""
    ps = [sp["p"][k] for k in ("G1", "G3m", "G6s", "G6l")]
    if any(p is None for p in ps) or sp["uninformative"]:
        return False
    if max(sp["floors"].values()) >= alpha:
        return False
    return max(p[d] for p in ps) < alpha


# ---- compact records -------------------------------------------------------------------------------------------------
def pdir(p) -> dict | None:
    """{+1: p, -1: p} -> {'+': p, '-': p} (JSON keys)."""
    if p is None:
        return None
    return {"+": None if p[PLUS] is None else float(p[PLUS]), "-": None if p[MINUS] is None else float(p[MINUS])}


def leg_table(legs: dict) -> dict:
    """Every verdict leg's one-sided p's in both directions, with the composite site and species legs (R1)."""
    out = {"Level 0": pdir(legs["level0"]["p"]), "S1c": pdir(legs["site"]["S1c"]["p"]),
           "S2c": pdir(legs["site"]["S2c"]["p"])}
    by = V.leg_p_by_direction(legs)
    out["site"] = pdir(by["site"])
    if legs["kind"] == "full":
        for k in ("G1", "G3m", "G6s", "G6l"):
            out[k] = pdir(legs["species"]["p"][k])
        sp = by["species"]
        out["species"] = None if any(math.isnan(sp[d]) for d in (PLUS, MINUS)) else pdir(sp)
    return out


def compact_verdict(v: dict) -> dict:
    keep = ("T", "d_star", "p_conjunction", "survives", "primary_status", "flags", "two_sided", "registered_direction")
    out = {k: v.get(k) for k in keep}
    if v.get("kind") != "full":
        out.update(passes_component_level=v.get("passes_component_level"), reading=v.get("reading"))
    out["p_reported"] = {leg: rec.get("p_reported") for leg, rec in v["legs"].items()}
    return out


def legs_extra(legs: dict) -> dict:
    out = dict(T=float(legs["T"]), n_parcels=int(legs["n_parcels"]),
               site_exact={k: bool(legs["site"][k]["info"]["exact"]) for k in ("S1c", "S2c")})
    if legs["kind"] == "full":
        sp = legs["species"]
        out.update(g6l=dict(status=sp["g6l"].get("status"), n_used=sp["g6l"].get("n_used"),
                            draws=sp["g6l"].get("draws"), eligible=sp["g6l"].get("eligible")),
                   g6s_exact=bool(sp["g6s_exact"]), uninformative=dict(legs["uninformative"]),
                   species_floors=dict(sp["floors"]), species_status=dict(sp["status"]))
    else:
        out["level0_kind"] = legs["level0"]["kind"]
    return out


def below(p, d: int = PLUS, alpha: float = ALPHA) -> bool:
    """A leg's one-sided p (JSON form {'+': p, '-': p}) below alpha in direction d; a missing p is a non-rejection."""
    if p is None:
        return False
    v = p["+" if d == PLUS else "-"]
    return v is not None and v < alpha


def rate(k: int, n: int) -> float | None:
    return None if n == 0 else k / n


def sha256_json(o) -> str:
    return hashlib.sha256(json.dumps(A3.jsonable(o), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def write_json(path: Path, obj) -> str:
    """UTF-8 / LF JSON, atomic, read back (run.write_json_atomic)."""
    return R.write_json_atomic(Path(path), obj)


def write_jsonl(path: Path, rows: list) -> str:
    """UTF-8 / LF JSON lines, atomic, read back and compared line by line."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(A3.jsonable(r), sort_keys=True, ensure_ascii=False) for r in rows]
    data = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    import os
    os.replace(tmp, path)
    back = path.read_bytes()
    if back != data or [json.loads(x) for x in back.decode("utf-8").splitlines()] != [json.loads(x) for x in lines]:
        raise RuntimeError(f"read-back of {path.name} differs")
    return hashlib.sha256(back).hexdigest()


def z(v) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    return (v - v.mean()) / v.std()
