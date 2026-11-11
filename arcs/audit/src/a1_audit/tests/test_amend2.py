"""Plants of RUN_PLAN_amend_2.md v2.1 (FROZEN sha256 acdb1290...; arcs/audit/FROZEN.txt) that are not extensions of an
existing test file's plant, on synthetic data. R41 (P15) and R42 (P16) are in tests/test_forms.py, R43 (P18) in
tests/test_material_p18_p19_p20.py, L5b in tests/test_launch.py.

    cd arcs/audit/src
    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_amend2 [--scratch DIR] [--keep]

Part L5b   provenance_block refuses a launch record without L5b, or one naming only amendment 1's pin (synthetic record).
Part R37   (P17 extension) reporting.reproduction_check on R37's pairs: (+.03, -.01) reproduced; (+.03, -.03) not
           reproduced (sign); (+.20, +.26) not reproduced; (-.28, -.23) reproduced; (0, +.04) reproduced; (0, -.06) not
           reproduced, no sign label; an R^2 / R^2_adj pair never gets the sign label; a GIA-C17-like (published .001)
           and PAT-N-like (published .019 / .034 / -.002 / .021) cases; the boundary .05 decided exactly. Must-fail: an
           (A) labeller (the sign overrides the tolerance) is caught on (+.03, -.01). R27's amendment-5 reading through
           reporting.r27_reading (A3's gate logic removed) on a synthetic class.
Part R38   R14's per-gene p = 2 sf(|t|, df) (two-sided; it differs from the one-sided sf), the per_donor_recipe_t
           assertion; the HCP-MMP1 build hook (ahba_extras.build_perdonor_hcpmmp1) raises NotImplementedError naming
           R38 and WP4; ahba_builds.NOT_BUILT names the build.
Part R39   (P22 extension) through a1_audit.multiverse on run.SyntheticSources: a leave-one-out cell with a planted
           all-missing row drops it (count 0, reported), given per-donor counts or read from the matrix; counts that
           disagree with the matrix are refused; the bilateral cell runs on L + R + B (85 parcels; two without a sample
           in the cell and one non-finite y dropped and reported) and a cell restricted to the primary parcels fails the
           parcel-set check (CellParcelSetError); the normalisation cells keep the primary parcels and refuse other
           counts; no >= 2-donor x cell record can be made; a MIST64 claim requests no cell, a left-only map's bilateral
           cell is not applicable; a 14-parcel bilateral subcortical toy (audit K) reports S2c and G6s exact (S1c
           sampled) and passes R32's floor assertion.
Part R40   (P17 extension) on synthetic per-donor frames with unequal coverage: ahba_extras.r12_ds equals abagen's
           keep_stable_genes bit for bit (env/venv_ref subprocess) and the re-ranked gloss differs (must-fail); its
           call's arguments equal derive_r12's (read from ahba_builds.py's source, which is unchanged);
           Benkarim's vector has R12's hash (another vector refused) and keeps DS >= .5 (exactly .5 kept); Park keeps
           DS > .5 (exactly .5 dropped) on the decoder's own DS column when present, else on R12's vector with a
           planted decoder gene absent from it excluded and counted; load_r12_ds re-reads R12's stored vector against
           its build record (the real build: hashes and shape only) and refuses a planted copy whose bytes differ.
Part 8.1b  plants.driver.plant_constants asserts the §8.1b values (passes as committed; each planted change refused);
           the driver asserts them before its launch and writes them into every plant header.
Part WP2r  run.plant_class_word / seed_record_for: a gene-set-only row's plant keys carry its Liu data kind's id (15 /
           16, never a PLANT_CLASS_IDS value); a signed-weight row's carry its class id.
Exits non-zero on any failure. ASCII output only. No real map, set, carrier or sample is opened; the real R12 build is
read for hashes and its shape only.
"""
from __future__ import annotations

import os

for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_k] = "1"

import argparse  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
import traceback  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1]
REPO = HERE.parents[4]
VENV_REF = (Path(subprocess.run(["git", "-C", str(REPO), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                 capture_output=True, text=True).stdout.strip()).parent
            / "env" / "venv_ref" / "Scripts" / "python.exe")          # env/ lives in the main tree only
for _p in (REPO / "src", SRC):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from a1_audit import ahba_builds as AB  # noqa: E402
from a1_audit import ahba_extras as AX  # noqa: E402
from a1_audit import launch as LA  # noqa: E402
from a1_audit import multiverse as MV  # noqa: E402
from a1_audit import plant_mode as PM  # noqa: E402
from a1_audit import repro as RE  # noqa: E402
from a1_audit import reporting as RPT  # noqa: E402
from a1_audit import run as R  # noqa: E402
from a1_audit import seeds as SD  # noqa: E402
from a1_audit import verdict as V  # noqa: E402

RESULTS: list = []
SEP = "-" * 100


def check(name: str, cond, detail: str = "") -> bool:
    ok = bool(cond)
    RESULTS.append((name, ok))
    print(R.ascii_line("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  [" + detail + "]") if detail else "")),
          flush=True)
    return ok


def raises(fn, exc, contains: str | None = None) -> bool:
    try:
        fn()
    except exc as e:  # noqa: PERF203
        return contains is None or contains in str(e)
    except Exception:  # noqa: BLE001
        return False
    return False


# ================================================================================================================
# L5b: provenance
# ================================================================================================================
def part_l5b(scratch: Path) -> None:
    print(SEP + "\nPart L5b: provenance_block and the amendment pins (RUN_PLAN_amend_2.md)")

    def rec(ids, amend):
        a = [dict(id=i, ok=True, status="pass", observed={"modules": {}, "code_hash": "0" * 64}, detail={})
             for i in ids]
        for x in a:
            if x["id"] == "L7":
                x["detail"] = {"environments": {"env/venv": {"pandas": "x"}, "env/venv_ref": {"pandas": "y"}}}
        return dict(passed=True, failed=[], assertions=a, run_commit="0" * 40, repo_root=str(REPO),
                    amendment_sha256=amend, test_overrides=[], files_root=None)
    both = dict(LA.AMENDMENTS)
    good = rec(LA.ASSERTION_IDS, both)
    blk = LA.provenance_block(good, recheck=False)
    check("L5b: ASSERTION_IDS hold L5b after L5a (18 assertions since RUN_PLAN_amend_3's L5c); a record with every "
          "assertion and the amendments' pins gives a "
          "provenance block naming both", list(LA.ASSERTION_IDS).index("L5b") == list(LA.ASSERTION_IDS).index("L5a") + 1
          and len(LA.ASSERTION_IDS) == 18 and blk["amendment_sha256"] == both
          and both == {"RUN_PLAN_amend_1.md": LA.AMEND1_SHA256, "RUN_PLAN_amend_2.md": LA.AMEND2_SHA256,
                       "RUN_PLAN_amend_3.md": LA.AMEND3_SHA256})
    check("L5b: provenance refused for a launch record without L5b",
          raises(lambda: LA.provenance_block(rec([i for i in LA.ASSERTION_IDS if i != "L5b"], both), recheck=False),
                 LA.ProvenanceError, "L5b"))
    check("L5b: provenance refused for a launch record naming only amendment 1's pin",
          raises(lambda: LA.provenance_block(rec(LA.ASSERTION_IDS, {"RUN_PLAN_amend_1.md": LA.AMEND1_SHA256}),
                                             recheck=False), LA.ProvenanceError, "three amendments"))
    check("L5c (RUN_PLAN_amend_3.md): provenance refused for a launch record without L5c, or naming only amendments 1 "
          "and 2",
          raises(lambda: LA.provenance_block(rec([i for i in LA.ASSERTION_IDS if i != "L5c"], both), recheck=False),
                 LA.ProvenanceError, "L5c")
          and raises(lambda: LA.provenance_block(rec(LA.ASSERTION_IDS, {"RUN_PLAN_amend_1.md": LA.AMEND1_SHA256,
                                                                         "RUN_PLAN_amend_2.md": LA.AMEND2_SHA256}),
                                                 recheck=False), LA.ProvenanceError, "three amendments")
          and list(LA.ASSERTION_IDS).index("L5c") == list(LA.ASSERTION_IDS).index("L5b") + 1)
    check("L5c: the pin is FROZEN.txt's RUN_PLAN_amend_3.md line (da3f3b8b...)",
          LA.AMEND3_SHA256.startswith("da3f3b8b") and LA.AMEND3_SHA256 in (REPO / LA.FROZEN_TXT).read_text("utf-8"))
    check("L5b: the pin is FROZEN.txt's RUN_PLAN_amend_2.md line (acdb1290...)",
          LA.AMEND2_SHA256.startswith("acdb1290") and LA.AMEND2_SHA256 in (REPO / LA.FROZEN_TXT).read_text("utf-8"))


# ================================================================================================================
# R37
# ================================================================================================================
def labeller_A(published, ours, *, functional):
    """R37's option (A), the must-fail variant: the sign overrides the tolerance."""
    from fractions import Fraction
    p, o = Fraction(str(published).replace("−", "-")), Fraction(ours)
    if RPT.FUNCTIONALS[functional] and p != 0 and o != 0 and (p > 0) != (o > 0):
        return RPT.NOT_REPRODUCED_SIGN
    return RPT.REPRODUCED if abs(o - p) <= Fraction(1, 20) else RPT.NOT_REPRODUCED


def part_r37(scratch: Path) -> None:
    print(SEP + "\nPart R37: the reproduction comparator (reporting.reproduction_check; P17 extension)")
    pairs = [("+.03", -0.01, "spearman rho", RPT.REPRODUCED), ("+.03", -0.03, "spearman rho", RPT.NOT_REPRODUCED_SIGN),
             ("+.20", 0.26, "pearson r", RPT.NOT_REPRODUCED), ("-.28", -0.23, "pearson r", RPT.REPRODUCED),
             ("0", 0.04, "spearman rho", RPT.REPRODUCED), ("0", -0.06, "spearman rho", RPT.NOT_REPRODUCED),
             ("0.03", -0.03, "R2_adj", RPT.NOT_REPRODUCED), ("0.30", 0.20, "R2", RPT.NOT_REPRODUCED),
             ("0.12", 0.10, "dominance", RPT.REPRODUCED)]
    for pub, ours, fn, want in pairs:
        r = RPT.reproduction_check(pub, ours, functional=fn)
        check(f"R37 ({pub}, {ours:+.2f}) [{fn}] -> {want}", r["label"] == want and r["tolerance"] == ".05")
    # GIA-C17-like (in m: published rho .001) and PAT-N-like (mean bicor .019 / .034 / -.002 / .021); ours are planted
    cases = [(".001", -0.03, "spearman rho", RPT.REPRODUCED), (".001", -0.06, "spearman rho", RPT.NOT_REPRODUCED_SIGN),
             (".019", -0.02, "mean bicor", RPT.REPRODUCED), (".034", -0.02, "mean bicor", RPT.NOT_REPRODUCED_SIGN),
             ("−.002", 0.04, "mean bicor", RPT.REPRODUCED), (".021", 0.0, "mean bicor", RPT.REPRODUCED),
             ("−.067", 0.0, "mean bicor", RPT.NOT_REPRODUCED)]
    for pub, ours, fn, want in cases:
        r = RPT.reproduction_check(pub, ours, functional=fn)
        check(f"R37 GIA-C17- / PAT-N-like ({pub.replace(chr(0x2212), '-')}, {ours:+.2f}) [{fn}] -> {want}",
              r["label"] == want)
    check("R37 boundary: |ours - published| = .05 exactly is reproduced (exact rationals); .0500001 is not",
          RPT.reproduction_check("0.05", 0.0, functional="pearson r")["label"] == RPT.REPRODUCED
          and RPT.reproduction_check("-0.05", 0.0, functional="pearson r")["label"] == RPT.REPRODUCED
          and RPT.reproduction_check("0.0500001", 0.0, functional="pearson r")["label"] == RPT.NOT_REPRODUCED)
    check("R37 must-fail: an (A) labeller (the sign overrides the tolerance) labels (+.03, -.01) 'not reproduced (sign)' "
          "where (B) reads 'reproduced' (caught)",
          labeller_A("+.03", -0.01, functional="spearman rho") == RPT.NOT_REPRODUCED_SIGN
          and RPT.reproduction_check("+.03", -0.01, functional="spearman rho")["label"] == RPT.REPRODUCED)
    check("R37 fail closed: an unknown functional, a non-finite value, a non-number published value are refused",
          raises(lambda: RPT.reproduction_check(".1", 0.1, functional="kendall tau"), ValueError, "vocabulary")
          and raises(lambda: RPT.reproduction_check(".1", float("nan"), functional="pearson r"), ValueError)
          and raises(lambda: RPT.reproduction_check("n.s.", 0.1, functional="pearson r"), ValueError))
    # R27's amendment-5 reading through the A3 port with the gate logic removed (synthetic dk-ctx class)
    src = R.SyntheticSources(37, scratch / "_no_data_r37")
    ctx, counts, _ = src.context("dk-ctx")
    keep = [i for i in ctx.parcel_ids if counts[int(i)] >= 1]
    c2 = ctx.restrict(keep)
    y = np.random.default_rng(37).standard_normal(c2.n)
    S = np.arange(30)
    desc = R.A3.descriptors(c2, y, S, parcel_ids=c2.parcel_ids)
    scope = dict(gradient_classes=["V-AAL", "V-CC200"], n1_classes=["V-CC200"])
    rp = RPT.reproduction_check(".20", 0.18, functional="pearson r")
    out = RPT.r27_reading(dict(status="ok", survives=True), desc, c2, scope=scope, reproduction=rp)
    a3 = R.A3.reading(dict(status="ok", survives=True), desc, c2, gate=None, scope=scope)
    check("R27: r27_reading = the A3 port's reading with gate=None (labels, power columns, reading unchanged), the "
          "reproduction check beside it", out["reading"] == a3["reading"] and out["labels"] == a3["labels"]
          and out["power_columns"] == a3["power_columns"] and "gate" not in out and out["reproduction"] == rp,
          out["reading"])


# ================================================================================================================
# R38
# ================================================================================================================
def part_r38(scratch: Path) -> None:
    print(SEP + "\nPart R38: R14's two-sided p; the HCP-MMP1 build hook (WP4)")
    rng = np.random.default_rng(38)
    y = rng.standard_normal(30)
    mats = [np.outer(y, rng.normal(0, 1, 40)) + rng.standard_normal((30, 40)) for _ in range(6)]
    mats[2][:28, 5] = np.nan
    rec = RE.per_donor_recipe_t(y, mats)
    t, df, p = rec["t"], rec["df"], rec["p_two_sided"]
    ok = rec["tested"]
    two = 2 * stats.t.sf(np.abs(t[ok]), df[ok])
    one = stats.t.sf(np.abs(t[ok]), df[ok])
    check("R38: R14's per-gene p = 2 sf(|t|, df) (two-sided; it is not the one-sided sf); the record states it",
          np.allclose(p[ok], two, rtol=1e-12, atol=0) and not np.allclose(p[ok], one) and "two-sided" in rec["sidedness"]
          and "R38" in rec["sidedness"], f"{int(ok.sum())} genes tested")
    # WP4 phase 1 implemented the hook (ahba_extras.build_perdonor_hcpmmp1; its P18 extension is in
    # tests/test_wp4_phase1.py, Part B38); WP2's NotImplementedError text is kept as the reading's record
    check("R38: the perdonor-hcpmmp1 build is WP4's (ahba_extras.R38_WP4 names R38 and WP4; the build function exists "
          "and takes the R15 volume and label list); ahba_builds' NOT_BUILT names the build",
          "R38" in AX.R38_WP4 and "WP4" in AX.R38_WP4 and callable(AX.build_perdonor_hcpmmp1)
          and "volume_path" in AX.build_perdonor_hcpmmp1.__code__.co_varnames and "perdonor-hcpmmp1" in AB.NOT_BUILT)


# ================================================================================================================
# R39 (P22 extension)
# ================================================================================================================
K_SMALL = dict(site=200, species=100, permutation=200, sets=60, surr=100, j1_sets=30)


def plan_of(cls: str, row: int = 478) -> dict:
    return dict(row=row, target_no=1, analysis_class=cls, has_set=True, form="set-vs-map", component=None,
                cell_index=0, depletion=False, maps=[0])


def run(plan, sources, **kw):
    return MV.run_cell(plan, sources, 0, K_SMALL, V.seed_callables(1, 1, 0, 0), g6l_mode=PM.MODE_PLANT,
                       two_sided=True, **kw)


def canon(o) -> str:
    return json.dumps(R.A3.jsonable(o), sort_keys=True)


class _MapOverride(R.Sources):
    """The base sources with one map value replaced (the primary path's comparison of a dropped parcel)."""

    def __init__(self, base, y):
        self.base, self.y = base, np.asarray(y, float)
        self.kind, self.synthetic = base.kind, True

    def spec(self):
        return dict(self.base.spec(), y_override=True)

    def context(self, cls):
        return self.base.context(cls)

    def map(self, plan, map_index):
        _, ids, cls, _ = self.base.map(plan, map_index)
        return self.y, ids, cls, {f"map[{int(map_index)}]": R.arr_sha(self.y, ids)}

    def gene_set(self, plan):
        return self.base.gene_set(plan)

    def trajectories(self, cls):
        return self.base.trajectories(cls)


def bilateral_inputs(base, cls: str, rng, *, zero=(), nan_y=(), add_b: bool = True):
    """A synthetic bidirectional build: the class's L parcels (ids 1001 ...), their R mirrors (2001 ...) and one B
    parcel (3001, the last tissue class); xyz mirrored in x; rows R = L + noise; counts >= 1 except `zero` (whose rows
    are empty); the map on every parcel, NaN at `nan_y`."""
    ctx0, _, _ = base.context(cls)
    L = [int(i) for i in ctx0.parcel_ids]
    Rr = [i + 1000 for i in L]
    classes = [str(c) for c in ctx0.classes]
    ids = L + Rr + ([3001] if add_b else [])
    struct = classes + classes + ([classes[-1]] if add_b else [])
    hemi = ["L"] * len(L) + ["R"] * len(Rr) + (["B"] if add_b else [])
    info = pd.DataFrame({"label": [f"sp{i}" for i in ids], "hemisphere": hemi, "structure": struct}, index=ids)
    xyz0 = np.asarray(ctx0.xyz, float)
    xyz = {i: tuple(v) for i, v in zip(L, xyz0)}
    xyz.update({i: (-v[0], v[1], v[2]) for i, v in zip(Rr, xyz0)})
    if add_b:
        xyz[3001] = (0.5, float(xyz0[:, 1].mean()), float(xyz0[:, 2].mean()))
    X0 = ctx0.expr.to_numpy(float)
    rows = [X0, X0 + 0.3 * rng.standard_normal(X0.shape)]
    if add_b:
        rows.append(X0[-3:].mean(0, keepdims=True) + 0.3 * rng.standard_normal((1, X0.shape[1])))
    expr = pd.DataFrame(np.vstack(rows), index=ids, columns=list(ctx0.expr.columns))
    counts = {i: int(rng.integers(1, 5)) for i in ids}
    for i in zero:
        counts[i] = 0
        expr.loc[i] = np.nan
    y = rng.standard_normal(len(ids))
    for i in nan_y:
        y[ids.index(i)] = np.nan
    return dict(info=info, xyz=xyz, maps={0: (y, ids)}), expr, counts


class _PrimaryOnlyBilateral(MV.CellSources):
    """Planted defect: a bilateral cell whose context is built on the primary parcels only."""

    def _context_ids(self, cls):
        prim = {int(i) for i in self.base.context(cls)[0].parcel_ids}
        return [i for i in super()._context_ids(cls) if i in prim]


def part_r39(scratch: Path) -> None:
    print(SEP + "\nPart R39: multiverse cells (P22 extension; synthetic sources, small K, G6l in plant mode)")
    rng = np.random.default_rng(39)
    base = R.SyntheticSources(39, scratch / "_no_data_r39")
    # --- leave-one-out: a planted all-missing row
    plan = plan_of("dk-ctx")
    ctx0, counts0, _ = base.context("dk-ctx")
    prim = run(plan, base)
    gone = int(ctx0.parcel_ids[9])
    e = ctx0.expr.copy()
    e.loc[gone] = np.nan
    e.loc[int(ctx0.parcel_ids[0])] = np.nan        # the primary's zero-count parcel is empty in a real cell matrix
    loo_counts = {int(i): (0 if int(i) == gone else int(counts0[int(i)])) for i in ctx0.parcel_ids}
    y, ids, _, _ = base.map(plan, 0)
    y4 = np.array(y, float)
    y4[list(ids).index(gone)] = np.nan
    ref = run(plan, _MapOverride(base, y4))
    for label, kw in (("given per-donor counts", dict(counts=loo_counts)), ("counts read from the matrix", {})):
        cs = MV.CellSources(base, "leave-one-donor-out 2", e, **kw)
        out = run(plan, cs)
        cp = out["cell_parcels"]
        check(f"R39 LOO ({label}): the planted all-missing parcel is dropped (count 0, reported); legs and verdict = the "
              "primary path without it", gone not in out["parcel_ids"] and gone in cp["dropped_no_sample_in_cell"]
              and canon(out["legs"]) == canon(ref["legs"]) and canon(out["verdict"]) == canon(ref["verdict"])
              and out["parcel_ids"] == ref["parcel_ids"] and cp["universe"]["n"] == len(ctx0.parcel_ids)
              and cp["counts_source"] == (MV.COUNTS_GIVEN_LOO if kw else MV.COUNTS_FROM_MATRIX),
              f"{cp['n_kept']} kept, {cp['n_dropped']} dropped")
    bad = dict(loo_counts)
    bad[gone] = 2
    check("R39 LOO: given counts that disagree with the cell matrix's empty rows are refused",
          raises(lambda: run(plan, MV.CellSources(base, "leave-one-donor-out 2", e, counts=bad)), R.SourceUnavailable,
                 "disagree"))
    check("R39 P22's own path: the primary matrix through CellSources(PRIMARY) = the primary result",
          canon(run(plan, MV.CellSources(base, MV.PRIMARY, ctx0.expr))["legs"]) == canon(prim["legs"]))
    # --- normalisation cells keep the primary parcels (the primary's counts)
    z = (ctx0.expr - ctx0.expr.mean()) / ctx0.expr.std()
    nc = run(plan, MV.CellSources(base, "(zscore, True)", z))
    check("R39 normalisation cell: the primary parcels (L + B universe of the class), the primary's counts; analysis "
          "parcels = the primary's", nc["parcel_ids"] == prim["parcel_ids"]
          and nc["cell_parcels"]["universe"]["n"] == len(ctx0.parcel_ids)
          and nc["cell_parcels"]["counts_source"] == MV.COUNTS_PRIMARY
          and nc["cell_parcels"]["universe"]["by_hemisphere"]["R"] == 0)
    check("R39 normalisation cell: other counts are refused (R39: the primary's counts)",
          raises(lambda: MV.CellSources(base, "(srs, False)", z, counts=dict(counts0)), ValueError, "primary"))
    # --- no >= 2-donor x cell record
    check("R39: not crossed with the >= 2-donor sensitivity - a cell's prepare under 'donors>=2' is refused; run_cell "
          "has no entry-rule argument",
          raises(lambda: R.prepare(plan, MV.CellSources(base, "(zscore, True)", z), 0, "donors>=2"),
                 R.SourceUnavailable, "not crossed")
          and "rule" not in inspect.signature(MV.run_cell).parameters)
    # --- cells requested
    c_dk = MV.cells_for(dict(analysis_class="dk-ctx"), left_only_map=False)
    c_left = MV.cells_for(dict(analysis_class="dk-ctx"), left_only_map=True)
    check("R39: a MIST64 claim requests no cell; others request R11's 10 cells; a left-only map's bilateral cell is "
          "'not applicable'", MV.cells_for(dict(analysis_class="MIST64"), left_only_map=False) == []
          and MV.no_cell_reason(dict(analysis_class="MIST64")) == MV.NO_CELL_MIST64 and len(c_dk) == 10
          and all(c["status"] == MV.CELL_RUN for c in c_dk)
          and [c["status"] for c in c_left if c["cell"] == MV.BILATERAL] == [MV.NOT_APPLICABLE_LEFT_ONLY])
    check("R39: a left-only map's bilateral cell refuses its context (not applicable)",
          raises(lambda: MV.CellSources(base, MV.BILATERAL, ctx0.expr, left_only_map=True).context("dk-ctx"),
                 R.SourceUnavailable, "left hemisphere only"))
    # --- the bilateral cell on L + R + B (V-DK: cortex + subcortex/brainstem)
    pv = plan_of("V-DK")
    bil, bexpr, bcounts = bilateral_inputs(base, "V-DK", rng, zero=(2005, 2040), nan_y=(2010,))
    bs = MV.CellSources(base, MV.BILATERAL, bexpr, counts=bcounts, bilateral=bil)
    out = run(pv, bs)
    cp = out["cell_parcels"]
    hem = {h: sum(1 for i in out["parcel_ids"] if bil["info"].at[i, "hemisphere"] == h) for h in ("L", "R", "B")}
    check("R39 bilateral cell: runs on L + R + B (the class's tissue classes, atlas_info classes and centroids); "
          "two parcels without a sample in the cell and one non-finite y dropped and reported",
          cp["universe"]["n"] == 85 and cp["universe"]["by_hemisphere"] == {"L": 42, "R": 42, "B": 1}
          and len(out["parcel_ids"]) == 82 and hem == {"L": 42, "R": 39, "B": 1}
          and sorted(cp["dropped_no_sample_in_cell"]) == [2005, 2040] and cp["dropped_nonfinite"] == [2010]
          and cp["counts_source"] == MV.COUNTS_GIVEN_BILATERAL, json.dumps(hem))
    try:
        run(pv, _PrimaryOnlyBilateral(base, MV.BILATERAL, bexpr, counts=bcounts, bilateral=bil))
        caught = False
    except MV.CellParcelSetError:
        caught = True
    check("R39 must-fail: a bilateral cell restricted to the primary parcels fails the parcel-set check", caught)
    check("R39 bilateral cell: its build's counts and inputs are required",
          raises(lambda: MV.CellSources(base, MV.BILATERAL, bexpr, bilateral=bil), ValueError, "bilateral"))
    # --- a 14-parcel bilateral subcortical toy: S2c and G6s exact, S1c sampled, R32's floors asserted
    ps = plan_of("V-DK-subcortex")
    bil2, bexpr2, bcounts2 = bilateral_inputs(base, "V-DK-subcortex", rng, add_b=False)
    out2 = MV.run_cell(ps, MV.CellSources(base, MV.BILATERAL, bexpr2, counts=bcounts2, bilateral=bil2), 0,
                       dict(R.AUDIT_K), V.seed_callables(1, 1, 0, 0), g6l_mode=PM.MODE_PLANT, two_sided=True)
    # (audit K: an enumeration is exact iff its patterns are <= K = 10,000; claims_register.md:1069-1070)
    lg = out2["legs"]["legs"]
    site = lg["site"]
    checked = V.check_exact_floors(lg)
    check("R39 / R32: a 14-parcel bilateral subcortical class - S2c exact (2^13 = 8,192 patterns), G6s exact (rank 13), "
          "S1c sampled; R32 (c)'s floor assertion passes on the exact legs",
          len(out2["parcel_ids"]) == 14 and site["S2c"]["info"]["exact"] and not site["S1c"]["info"]["exact"]
          and lg["species"]["g6s_exact"] and checked == ["S2c", "G6s"]
          and int(site["S2c"]["info"]["n_patterns"]) == 8192,
          f"S2c patterns {site['S2c']['info'].get('n_patterns')}, G6s n {lg['species'].get('n_G6s')}")


# ================================================================================================================
# R40
# ================================================================================================================
_DS_SCRIPT = r"""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1])
from a1_audit import ahba_extras as X
from abagen import correct
rng = np.random.default_rng(40)
regions = [f"r{k}" for k in range(20)]
genes = [f"g{j}" for j in range(60)]
base = rng.standard_normal((20, 60))
frames = []
for d in range(6):
    v = base + 0.8 * rng.standard_normal((20, 60))
    f = pd.DataFrame(v, index=regions, columns=genes)
    f.iloc[[d, (d + 7) % 20, (d + 13) % 20]] = np.nan     # unequal coverage: each donor misses three regions
    frames.append(f)
runner = X.r12_ds(frames)
_, ab = correct.keep_stable_genes(frames, threshold=0.1, percentile=False, rank=True, return_stability=True)
ab = np.asarray(ab, dtype=float)
pairs = [(i, j) for i in range(6) for j in range(i + 1, 6)]
C = np.zeros((60, len(pairs)))
for k, (i, j) in enumerate(pairs):
    reg = frames[i].dropna(how="all").index.intersection(frames[j].dropna(how="all").index)
    a = frames[i].loc[reg].rank().to_numpy(float)
    b = frames[j].loc[reg].rank().to_numpy(float)
    az = (a - a.mean(0)) / a.std(0, ddof=1)
    bz = (b - b.mean(0)) / b.std(0, ddof=1)
    C[:, k] = (az * bz).sum(0) / (len(reg) - 1)
gloss = C.mean(1)
print(json.dumps(dict(bit_equal=bool(np.array_equal(runner, ab)), n=int(runner.size),
                      gloss_max_abs_delta=float(np.max(np.abs(gloss - runner))))))
"""


def part_r40(scratch: Path) -> None:
    print(SEP + "\nPart R40: differential stability (P17 extension; synthetic per-donor frames)")
    if VENV_REF.is_file():
        r = subprocess.run([str(VENV_REF), "-X", "utf8", "-c", _DS_SCRIPT, str(SRC)], capture_output=True, cwd=str(SRC),
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"), timeout=600)
        out = json.loads(r.stdout.decode("utf-8").strip().splitlines()[-1]) if r.returncode == 0 else {}
        check("R40: with unequal coverage the runner's DS (ahba_extras.r12_ds) equals abagen's keep_stable_genes bit for "
              "bit (env/venv_ref); the re-ranked gloss differs (must-fail)", out.get("bit_equal") is True
              and out.get("gloss_max_abs_delta", 0.0) > 1e-6,
              json.dumps(out) if out else r.stderr.decode("utf-8", "replace")[-300:])
    else:
        check("R40: env/venv_ref present for the abagen comparison", False)
    import ast
    tree = ast.parse(Path(AB.__file__).read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "derive_r12")
    calls = [c for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
             and c.func.attr == "keep_stable_genes"]
    kws = {k.arg: (AB.R12_THRESHOLD if isinstance(k.value, ast.Name) and k.value.id == "R12_THRESHOLD"
                   else ast.literal_eval(k.value)) for k in calls[0].keywords} if len(calls) == 1 else None
    check("R40: ahba_extras.r12_ds reproduces derive_r12's keep_stable_genes call (its arguments, read from "
          "ahba_builds.py's source, which the move left unchanged)", kws == AX.R12_DS_KWARGS
          and len(calls[0].args) == 1, json.dumps(kws))
    genes = [f"g{j}" for j in range(10)]
    vals = [0.9, 0.5, 0.49, 0.51, 0.1, 0.5, 0.7, -0.2, 0.55, 0.3]
    r12 = pd.Series(vals, index=genes)
    sha = RE.ds_vector_sha(r12)
    bk = RE.benkarim_ds_genes(r12, r12_sha256=sha)
    check("R40 Benkarim: R12's DS vector (same hash), DS >= .5 (exactly .5 kept)",
          bk["genes"] == ["g0", "g1", "g3", "g5", "g6", "g8"] and bk["ds_sha256"] == sha)
    other = r12.copy()
    other.iloc[4] = 0.11
    check("R40 Benkarim: a DS vector other than R12's (hash differs) is refused",
          raises(lambda: RE.benkarim_ds_genes(other, r12_sha256=sha), AssertionError, "R12"))
    dec = ["g1", "g3", "g6", "gX", "g9"]
    pk = RE.park_ds_genes(dec, r12_ds=r12, r12_sha256=sha)
    check("R40 Park (no DS column): R12's vector, DS > .5 (exactly .5 dropped); a planted decoder gene absent from R12's "
          "vector excluded and counted", pk["genes"] == ["g3", "g6"] and pk["n_excluded_absent_from_r12"] == 1
          and pk["branch"].startswith("R12"))
    col = {"g1": 0.8, "g3": 0.2, "g6": 0.5, "gX": 0.9, "g9": float("nan")}
    pk2 = RE.park_ds_genes(dec, r12_ds=r12, r12_sha256=sha, decoder_ds=col)
    check("R40 Park (the decoder output carries its DS column): that column is used (gX kept from it; g9 without a "
          "value excluded and counted)", pk2["genes"] == ["g1", "gX"] and pk2["n_excluded_no_ds"] == 1
          and pk2["branch"].startswith("the decoder"))
    # load_r12_ds: the real build's stored vector against its record (hashes and shape only)
    try:
        s, ident = AX.load_r12_ds()
        real_ok = len(s) == ident["n_genes"] and len(ident["sha256"]) == 64 and s.index.is_unique
        detail = f"{ident['n_genes']} genes"
    except Exception as e:  # noqa: BLE001
        real_ok, detail = False, f"{type(e).__name__}"
    check("R40: load_r12_ds re-reads R12's stored DS vector against its build record (file sha256, round-trip hash)",
          real_ok, detail)
    # a planted copy whose bytes differ from its record is refused (a scratch OUT)
    fake = scratch / "a1_builds"
    (fake / "r12-han-c1-ourpc1").mkdir(parents=True)
    f = fake / "r12-han-c1-ourpc1" / "ds_dk_ctx_perdonor.csv"
    f.write_text("gene_symbol,ds\ng0,0.9\ng1,0.5\n", encoding="utf-8", newline="\n")
    df = AB.read_frame(f, "round_trip")
    rec = dict(ok=True, outputs=[dict(file="ds_dk_ctx_perdonor.csv", sha256=AB.sha256_file(f),
                                      sha256_round_trip=AB.frame_sha(df))])
    (fake / "r12-han-c1-ourpc1" / AB.RECORD).write_text(json.dumps(rec), encoding="utf-8")
    s2, _ = AX.load_r12_ds(out=fake)
    good = list(s2.index) == ["g0", "g1"]
    f.write_text("gene_symbol,ds\ng0,0.9\ng1,0.6\n", encoding="utf-8", newline="\n")
    refused = raises(lambda: AX.load_r12_ds(out=fake), AB.BuildError, "differs")
    check("R40: load_r12_ds reads a synthetic record's vector and refuses a planted copy whose bytes differ", good and refused)


# ================================================================================================================
# §8.1b
# ================================================================================================================
def part_constants(scratch: Path) -> None:
    print(SEP + "\nPart 8.1b: the plant constants pinned by value (plants.driver)")
    from a1_audit.plants import common as C
    from a1_audit.plants import driver as D
    rec = D.plant_constants()
    check("8.1b: the constants as committed equal RUN_PLAN_amend_2 §8.1b by value",
          rec["values"] == D.PINNED_CONSTANTS and D.PINNED_CONSTANTS["PLANT_K"] == {"site": 500, "species": 200,
                                                                                   "permutation": 500, "sets": 200,
                                                                                   "surr": 500, "j1_sets": 100}
          and D.PINNED_CONSTANTS["PLANT_WORD"] == 900 and D.PINNED_CONSTANTS["PLANT_DATA_WORD"] == 1000)
    planted = []

    def trial(name, apply, undo):
        apply()
        try:
            D.plant_constants()
            planted.append((name, False))
        except AssertionError:
            planted.append((name, True))
        finally:
            undo()
    k0 = dict(R.PLANT_K)
    trial("PLANT_K site 501", lambda: R.PLANT_K.__setitem__("site", 501), lambda: R.PLANT_K.update(k0))
    trial("PLANT_K species 200.0", lambda: R.PLANT_K.__setitem__("species", 200.0), lambda: R.PLANT_K.update(k0))
    o0 = json.loads(json.dumps(R.PLANT_K_OVERRIDES))
    trial("P12 permutation 9999", lambda: R.PLANT_K_OVERRIDES["P12"].__setitem__("permutation", 9999),
          lambda: R.PLANT_K_OVERRIDES["P12"].update(o0["P12"]))
    trial("PLANT_WORD 901", lambda: setattr(SD, "PLANT_WORD", 901), lambda: setattr(SD, "PLANT_WORD", 900))
    trial("PLANT_DATA_WORD 999", lambda: setattr(SD, "PLANT_DATA_WORD", 999), lambda: setattr(SD, "PLANT_DATA_WORD", 1000))
    trial("class id dk-ctx 3", lambda: SD.PLANT_CLASS_IDS.__setitem__("dk-ctx", 3),
          lambda: SD.PLANT_CLASS_IDS.__setitem__("dk-ctx", 2))
    trial("P3b case range from 999", lambda: SD.PLANT_CASE_RANGES.__setitem__("P3b", (999, None)),
          lambda: SD.PLANT_CASE_RANGES.__setitem__("P3b", (1000, None)))
    trial("plants.common.K_PLANT j1_sets 99", lambda: C.K_PLANT.__setitem__("j1_sets", 99),
          lambda: C.K_PLANT.__setitem__("j1_sets", 100))
    check("8.1b: every planted change is refused (%d / %d)" % (sum(v for _, v in planted), len(planted)),
          all(v for _, v in planted) and len(planted) == 8, ", ".join(n for n, v in planted if not v))
    check("8.1b: restored after the trials", D.plant_constants()["values"] == D.PINNED_CONSTANTS)
    run_src = inspect.getsource(D.Invocation.run)
    wp_src = inspect.getsource(D.Invocation.write_plant)
    check("8.1b: the driver asserts the constants before its launch and writes them into every plant header",
          run_src.index("plant_constants()") < run_src.index("self.launch()")
          and "plant_constants=self.constants" in wp_src)


# ================================================================================================================
# WP2r: plant keys of the form rows
# ================================================================================================================
def part_wp2r(scratch: Path) -> None:
    print(SEP + "\nPart WP2r: the form rows' plant keys (run.plant_class_word, seed_record_for)")
    from a1_audit import forms as FM
    sv = dict(kind="plant", plant="P16", plant_id=16, case=3)
    liu = dict(row=473, target_no=10, analysis_class="none", form_name="liu", cell_index=0,
               liu_spec=dict(FM.LIU_SPECS["LIU-T4"], cell_id="LIU-T4"), seed_view=sv)
    liu1 = dict(liu, row=471, liu_spec=dict(FM.LIU_SPECS["LIU-T1"], cell_id="LIU-T1"))
    sw = dict(row=103, target_no=3, analysis_class="dk-ctx", form_name="signed-weight", cell_index=0,
              seed_view=dict(sv, plant="P15", plant_id=15))
    r1 = R.seed_record_for(liu, 0, {"G1": "rng"}, g3=True)
    r2 = R.seed_record_for(liu1, 0, {"G1": "rng"}, g3=True)
    r3 = R.seed_record_for(sw, 0, {"S1c": "int"}, j1=True)
    check("WP2r: a gene-set-only row's plant keys carry its Liu data kind's id (AHBA 16, BrainSpan 15), outside "
          "PLANT_CLASS_IDS; a signed-weight row's its class id", r1["keys"] == "plant" and r1["class_id"] == 16
          and r2["class_id"] == 15 and r3["class_id"] == SD.plant_class_id("dk-ctx")
          and not ({15, 16} & set(SD.PLANT_CLASS_IDS.values()))
          and r1["legs"][0]["key"]["entropy"] == [20260925, 900, 16, 3, 16, 2])
    sc = R.seeds_of(liu, 0)
    check("WP2r: seeds_of draws the same plant keys the record names",
          SD.same_seed_sequence(sc["seed_of"]("G1"), SD.plant_leg_seed(16, 3, 16, 2))
          and SD.same_seed_sequence(sc["g3_seed"](), SD.plant_g3_seed(16, 3, 16)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", default=None)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    base = Path(a.scratch or os.environ.get("A1_SCRATCH") or tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="a1_amend2_", dir=str(base))).resolve()
    print("test_amend2: scratch %s" % R.ascii_line(str(scratch)))
    for part in (part_l5b, part_r37, part_r38, part_r39, part_r40, part_constants, part_wp2r):
        try:
            part(scratch)
        except Exception as e:  # noqa: BLE001
            check(f"{part.__name__} raised", False, f"{type(e).__name__}: {e}")
            print(R.ascii_line(traceback.format_exc()))
    n_ok = sum(ok for _, ok in RESULTS)
    print(SEP + "\ntest_amend2: %d / %d checks passed" % (n_ok, len(RESULTS)))
    if n_ok == len(RESULTS) and not a.keep:
        shutil.rmtree(scratch, ignore_errors=True)
    return 0 if n_ok == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
