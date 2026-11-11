"""ASDG-AUD-E3-plants: J1 pool-diversity replay (a prereg §4.4 rule the 2026-09-23 battery did not apply).

prereg §4.4: "J1 requires pool diversity (mean pairwise Jaccard < 0.5) and sd_k > 1e-9; a violation is the
status 'degenerate pool'". e3_plants.py applies only the sd_k rule and does not save the G2 sets that form J1's
pool. This script replays each plant's RNG stream (same SeedSequence, same draw order as e3_plants.one_plant) up
to the G2 draw and the field drawn right after it, ASSERTS that the replay reproduces every plant's saved G2
status, coexpression, r and p_G2, and records the pool's exact mean pairwise Jaccard over all K(K-1)/2 pairs;
the engine's sampled estimate (cascade.pool_diversity, 2,000 pairs) is recorded as a cross-check.
e3_gates.py marks J1 'degenerate' where jaccard_exact >= 0.5.

Usage (programme root):
  env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e3_j1_pool_replay.py <cell|gated> [--jobs 22] [--limit N]
  cell = <atlas>_<family>_m<m>_a<a> as in the plant file name (e.g. aal_F-mod_m25_a0); 'gated' = the 8 cells
  whose plants J1's §6.4 gates use (F-sp and F-mod in every class, C-gene a=0.9 in V-AAL and V-DK).
Writes artifacts/plants/j1pool_<cell>.csv.gz (one row per plant); --limit writes nothing (a replay test).
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import sparse  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e3_plants as P  # noqa: E402  (puts src/ on sys.path; Ctx, module, GENERATOR_CELLS, ids, N_SETS)
from asdg.cascade import corr_matrix, emp_p, pool_diversity  # noqa: E402
from asdg.genesets import coexpr_matched_sets  # noqa: E402

GATED = ["aal_F-sp_m25_a0", "dk_F-sp_m25_a0", "cc200_F-sp_m25_a0",
         "aal_F-mod_m25_a0", "dk_F-mod_m25_a0", "cc200_F-mod_m25_a0",
         "aal_C-gene_m25_a0.9", "dk_C-gene_m25_a0.9"]
JACCARD_MAX = 0.5


def parse(cell: str):
    atlas, fam, m, a = cell.split("_")
    return atlas, fam, int(m[1:]), float(a[1:])


def exact_mean_jaccard(sets: np.ndarray) -> float:
    """Mean Jaccard overlap over all K(K-1)/2 pairs of equal-size sets (k, m)."""
    sets = np.asarray(sets)
    k, m = sets.shape
    _, inv = np.unique(sets, return_inverse=True)
    M = sparse.csr_matrix((np.ones(k * m), (np.repeat(np.arange(k), m), inv.ravel())))
    inter = (M @ M.T).toarray()[np.triu_indices(k, 1)]
    return float(np.mean(inter / (2 * m - inter)))


def replay_one(ctx, fam: str, m: int, a: float, seed_seq, i: int) -> dict:
    # --- same draws, same order as e3_plants.one_plant, up to the field ---
    rng = np.random.default_rng(seed_seq)
    gen, step = P.GENERATOR_CELLS[i % len(P.GENERATOR_CELLS)]
    if fam == "F-mod":
        S = P.module(ctx, m, rng, "coexp")
    elif fam == "F-traj":
        S = P.module(ctx, m, rng, "traj")
    else:
        S = rng.choice(ctx.all, size=m, replace=False)
    score = ctx.U.scores(S)[0]
    c_S = ctx.U.mean_coexpr(S)
    G2, i2 = coexpr_matched_sets(ctx.U, ctx.all, m, c_S, P.N_SETS, rng, exclude=S)
    field = ctx.fg.field(gen, rng, step)
    row = dict(i=i, gen=gen, step=step, coexpr_replay=c_S, G2_status_replay=i2["status"],
               r_replay=np.nan, p_G2_replay=np.nan)
    if G2 is None and fam == "C-gene":  # one_plant returns early here (y needs G2)
        return row
    z = lambda v: (v - v.mean()) / v.std()  # noqa: E731
    if fam == "C-sp":
        y = a * z(score) + np.sqrt(1 - a * a) * field
    elif fam == "C-gene":
        B = np.column_stack([np.ones(ctx.n_parcels), ctx.U.scores(G2).mean(0), ctx.pcs])
        resid = score - B @ np.linalg.lstsq(B, score, rcond=None)[0]
        y = a * z(resid) + np.sqrt(1 - a * a) * field
    else:
        y = field
    r_obs = corr_matrix(y, score)[0, 0]
    row["r_replay"] = r_obs
    if G2 is not None:
        row.update(p_G2_replay=emp_p(corr_matrix(y, ctx.U.scores(G2))[0], r_obs, +1),
                   jaccard_exact=exact_mean_jaccard(G2), jaccard_engine=pool_diversity(G2),
                   accept_rate=i2.get("accept_rate"), restarts=i2.get("restarts"))
    return row


def check(saved: pd.DataFrame, rep: pd.DataFrame) -> pd.DataFrame:
    """Per-plant agreement between the saved battery row and the replay; every plant must agree."""
    s = saved.set_index("i")
    d = rep.set_index("i").join(s[["status", "G2_status", "coexpr", "r", "p_G2"]], how="inner")
    saved_status = d["G2_status"].where(d["status"] == "ok", "unmatched")  # C-gene early return saved no status
    d["ok_status"] = saved_status.to_numpy() == d["G2_status_replay"].to_numpy()
    for col in ("coexpr", "r", "p_G2"):
        a, b = d[col], d[f"{col}_replay"]
        both = a.notna() & b.notna()
        d[f"ok_{col}"] = (a.notna() == b.notna()) & (~both | np.isclose(a, b, rtol=0, atol=1e-12))
    d.loc[d["status"] != "ok", "ok_coexpr"] = True  # early-return rows saved no coexpr
    d["replay_ok"] = d[["ok_status", "ok_coexpr", "ok_r", "ok_p_G2"]].all(axis=1)
    return d.reset_index()


def run_cell(cell: str, n_jobs: int, limit: int | None) -> None:
    from joblib import Parallel, delayed

    atlas, fam, m, a = parse(cell)
    saved = pd.read_csv(P.OUT / f"{cell}.csv.gz")
    idx = sorted(saved["i"].astype(int))[: limit or None]
    t0 = time.time()
    ctx = P.Ctx(atlas)
    base = [P.ATLAS_ID[atlas], P.FAM_ID[fam], m, int(round(a * 100))]

    def work(i):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return replay_one(ctx, fam, m, a, np.random.SeedSequence(base + [i]), i)

    rows = Parallel(n_jobs=n_jobs, backend="loky", batch_size=4)(delayed(work)(i) for i in idx)
    d = check(saved[saved["i"].isin(idx)], pd.DataFrame(rows))
    jx = d["jaccard_exact"] if "jaccard_exact" in d else pd.Series(np.nan, index=d.index)
    je = d["jaccard_engine"] if "jaccard_engine" in d else pd.Series(np.nan, index=d.index)
    bad = d.loc[~d["replay_ok"], "i"].tolist()
    print(f"{cell}: n={len(d)} replay_ok={int(d['replay_ok'].sum())} G2_ok={int(jx.notna().sum())} "
          f"jaccard_exact mean={jx.mean():.4f} max={jx.max():.4f} n>=0.5={int((jx >= JACCARD_MAX).sum())} "
          f"engine-vs-exact class disagreements={int(((je >= JACCARD_MAX) != (jx >= JACCARD_MAX))[jx.notna()].sum())} "
          f"{time.time() - t0:.0f}s", flush=True)
    if bad:
        raise SystemExit(f"REPLAY MISMATCH in {cell}: plants {bad[:20]} (n={len(bad)}); the replay is not "
                         f"faithful - do not use it")
    if limit:
        print("(--limit: replay test only, nothing written)")
        return
    for c in ("jaccard_exact", "jaccard_engine", "accept_rate", "restarts"):
        if c not in d:
            d[c] = np.nan
    cols = ["i", "gen", "step", "G2_status_replay", "jaccard_exact", "jaccard_engine", "accept_rate", "restarts",
            "replay_ok"]
    out = P.OUT / f"j1pool_{cell}.csv.gz"
    d[cols].sort_values("i").to_csv(out, index=False)
    back = pd.read_csv(out)
    assert len(back) == len(saved) and back["replay_ok"].all(), "read-back mismatch"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cell", help="<atlas>_<family>_m<m>_a<a> or 'gated'")
    ap.add_argument("--jobs", type=int, default=22)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    for c in (GATED if a.cell == "gated" else [a.cell]):
        run_cell(c, a.jobs, a.limit)


if __name__ == "__main__":
    main()
