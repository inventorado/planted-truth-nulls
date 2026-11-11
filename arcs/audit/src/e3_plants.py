"""ASDG-AUD-E3-plants (prereg §6): plant families x classes, every null's p-value per plant.

Usage: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e3_plants.py <atlas> <family> <m> <a> <n> [n_jobs]
  family in {F-sp, F-mod, F-traj, C-sp, C-gene}; a = strength (0 for F-*).
Writes artifacts/plants/<atlas>_<family>_m<m>_a<a>.csv.gz (one row per plant, all p-values + diagnostics).
Gates are computed by e3_gates.py from these files.
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import sys  # noqa: E402
import time  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from asdg.spatial import (centroid_distance, brainsmash_surrogates, MoranSpectral,  # noqa: E402
                          stratified_surrogates, FieldGenerator, variogram_misfit)
from asdg.genesets import (Universe, random_sets, coexpr_matched_sets, Trajectories,  # noqa: E402
                           trajectory_matched_sets)
from asdg.cascade import corr_matrix, emp_p, naive_p, joint_j1, naive_joint  # noqa: E402
from asdg.brainspan import load_trajectories  # noqa: E402

AHBA = ROOT / "artifacts" / "ahba"
OUT = ROOT / "artifacts" / "plants"
GAMBA_CSV = Path("E:/data/asdg/gamba/Background_genes_null_brain.csv")
GENERATOR_CELLS = [(g, s) for g in ("grf15", "grf30", "grf60", "sar5", "sar9") for s in (0.0, 1.0)]
N_SURR, N_SETS = 500, 500
FAM_ID = {"F-sp": 1, "F-mod": 2, "F-traj": 3, "C-sp": 4, "C-gene": 5}
ATLAS_ID = {"aal": 1, "dk": 2, "cc200": 3, "ho": 4}


def primary_parcels(atlas: str):
    expr = pd.read_csv(AHBA / f"{atlas}_expr.csv.gz", index_col=0)
    info = pd.read_csv(AHBA / f"{atlas}_atlas_info.csv").set_index("id")
    cen = pd.read_csv(AHBA / f"{atlas}_centroids.csv").set_index("id")
    keep = [i for i in expr.index if info.loc[i, "hemisphere"] in ("L", "B") and not expr.loc[i].isna().all()]
    return expr.loc[keep], info.loc[keep, "structure"].to_numpy(), cen.loc[keep, ["x", "y", "z"]].to_numpy()


def brain_background(U: Universe) -> np.ndarray:
    bg = pd.read_csv(GAMBA_CSV)
    sym, flag = "symbols", "brain > body (default)"
    assert int(bg[flag].sum()) == 2711, f"GAMBA brain>body flag count {int(bg[flag].sum())} != 2711"
    conflict = bg.groupby(sym)[flag].nunique()
    genes = set(bg.loc[(bg[flag] == 1) & ~bg[sym].isin(conflict[conflict > 1].index), sym])
    assert 2600 <= len(genes) <= 2711, len(genes)
    return np.array(sorted(U.index[g] for g in genes if g in U.index))


class Ctx:
    def __init__(self, atlas: str):
        expr, self.classes, xyz = primary_parcels(atlas)
        self.U = Universe(expr)
        self.D = centroid_distance(xyz)
        self.ms = MoranSpectral(self.D)
        self.fg = FieldGenerator(xyz, self.classes)
        self.all = np.arange(len(self.U.genes))
        self.brain = brain_background(self.U)
        T, _ = load_trajectories()
        self.tr = Trajectories(T, self.U)
        Zc = self.U.X - self.U.X.mean(0)
        u, s, _ = np.linalg.svd(Zc / self.U.X.std(0, ddof=1), full_matrices=False)
        self.pcs = u[:, :3]
        self.n_parcels = len(expr)


def module(ctx: Ctx, m: int, rng, kind: str) -> np.ndarray:
    if kind == "coexp":
        g = rng.integers(len(ctx.U.genes))
        r = ctx.U.Z[:, g] @ ctx.U.Z
        r[g] = -np.inf
        return np.concatenate([[g], np.argsort(r)[::-1][: m - 1]])
    names = ctx.tr.names
    g = names[rng.integers(len(names))]
    _, ind = ctx.tr.nn.kneighbors(ctx.tr.F[[ctx.tr.row[g]]], n_neighbors=m)
    return np.array([ctx.U.index[x] for x in names[ind[0]]])


def one_plant(ctx: Ctx, family: str, m: int, a: float, seed_seq, cell: int) -> dict:
    rng = np.random.default_rng(seed_seq)
    gen, step = GENERATOR_CELLS[cell % len(GENERATOR_CELLS)]  # balanced: n/10 plants per generator cell
    if family == "F-mod":
        S = module(ctx, m, rng, "coexp")
    elif family == "F-traj":
        S = module(ctx, m, rng, "traj")
    else:
        S = rng.choice(ctx.all, size=m, replace=False)
    score = ctx.U.scores(S)[0]
    c_S = ctx.U.mean_coexpr(S)
    G2, i2 = coexpr_matched_sets(ctx.U, ctx.all, m, c_S, N_SETS, rng, exclude=S)
    field = ctx.fg.field(gen, rng, step)
    z = lambda v: (v - v.mean()) / v.std()  # noqa: E731
    if family == "C-sp":
        y = a * z(score) + np.sqrt(1 - a * a) * field
    elif family == "C-gene":
        if G2 is None:
            return dict(status="unmatched_for_plant")
        B = np.column_stack([np.ones(ctx.n_parcels), ctx.U.scores(G2).mean(0), ctx.pcs])
        resid = score - B @ np.linalg.lstsq(B, score, rcond=None)[0]
        y = a * z(resid) + np.sqrt(1 - a * a) * field
    else:
        y = field
    sign = +1
    r_obs = corr_matrix(y, score)[0, 0]
    row = dict(status="ok", gen=gen, step=step, m=m, a=a, r=r_obs, coexpr=c_S, p_naive=naive_p(r_obs, len(y), sign))
    surr = {"S1": brainsmash_surrogates(y, ctx.D, N_SURR, int(rng.integers(2**31))),
            "S2": ctx.ms.surrogates(y, N_SURR, int(rng.integers(2**31))),
            "S1c": stratified_surrogates(y, ctx.D, ctx.classes, N_SURR, int(rng.integers(2**31)), "brainsmash"),
            "S2c": stratified_surrogates(y, ctx.D, ctx.classes, N_SURR, int(rng.integers(2**31)), "msr")}
    for k, s in surr.items():
        row[f"p_{k}"] = emp_p(corr_matrix(s, score)[:, 0], r_obs, sign)
    row["vg_misfit_S1"] = variogram_misfit(y, ctx.D, surr["S1"])
    row["p_L1_joint"] = max(row["p_S1"], row["p_S2"])
    row["p_L1_strat"] = max(row["p_S1c"], row["p_S2c"])
    sets = {"G1": random_sets(ctx.all, m, N_SETS, rng, exclude=S),
            "G3": random_sets(ctx.brain, m, N_SETS, rng, exclude=S), "G2": G2}
    G4, i4 = coexpr_matched_sets(ctx.U, ctx.brain, m, c_S, N_SETS, rng, exclude=S)
    sets["G4"] = G4
    G5, i5 = trajectory_matched_sets(ctx.U, [ctx.U.genes[i] for i in S], ctx.tr, N_SETS, rng)
    sets["G5"] = G5
    row.update(G2_status=i2["status"], G4_status=i4["status"], G5_status=i5["status"])
    if G2 is None:
        row["J1_status"] = "unmatched"
    for k, st in sets.items():
        row[f"p_{k}"] = np.nan if st is None else emp_p(corr_matrix(y, ctx.U.scores(st))[0], r_obs, sign)
    g = [row[f"p_G{i}"] for i in range(1, 6)]
    row["p_L2"] = np.nan if any(np.isnan(g)) else max(g)
    if G2 is not None:
        pool = ctx.U.scores(G2)
        for pair, (sa, sb) in {"joint": ("S1", "S2"), "strat": ("S1c", "S2c")}.items():
            pa = joint_j1(y, score, pool, surr[sa], sign)[1]
            pb = joint_j1(y, score, pool, surr[sb], sign)[1]
            row[f"p_J1_{pair}"] = max(pa, pb)  # NaN (degenerate pool) propagates as a status
        row["J1_status"] = "ok" if np.isfinite(row["p_J1_joint"]) else "degenerate_pool"
        row["p_naivejoint"] = naive_joint(y, ctx.U.scores(sets["G1"]), surr["S1"], score, sign, rng)
    return row


def main():
    atlas, family, m, a, n = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
    n_jobs = int(sys.argv[6]) if len(sys.argv) > 6 else 22
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{atlas}_{family}_m{m}_a{a:g}.csv.gz"
    t0 = time.time()
    from joblib import Parallel, delayed

    ctx = Ctx(atlas)
    base = [ATLAS_ID[atlas], FAM_ID[family], m, int(round(a * 100))]
    seeds = [np.random.SeedSequence(base + [i]) for i in range(n)]

    def work(i):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = one_plant(ctx, family, m, a, seeds[i], i)
        r["i"] = i
        return r

    rows = Parallel(n_jobs=n_jobs, backend="loky", batch_size=4)(delayed(work)(i) for i in range(n))
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    back = pd.read_csv(out)
    assert len(back) == n, "read-back row count mismatch"
    print(f"{out.name}: n={n} parcels={ctx.n_parcels} genes={len(ctx.U.genes)} brain_bg={len(ctx.brain)} "
          f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
