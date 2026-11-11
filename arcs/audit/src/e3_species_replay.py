"""ASDG-AUD-E3 (prereg_amend_3 §4): the species leg — G1 (conditioned), G3m, G6s, G6l, the uninformative label and
the species legs' floor — on the existing 27 plant cells, by deterministic replay of each plant's S and y (same
SeedSequence and draw order as e3_plants.one_plant: S, G2, field, then y for the family). Every plant's saved r and
p_G2 (and G2 status) are asserted before its new p-values are used; the species leg draws from a separate stream,
SeedSequence(plant seed + [99]). K = 200 (plants). The frozen p_G1 (unconditioned, 500 sets) stays in the plant file as
a descriptor; the verdict and its status are formed in e3_gates_a3.py.

Usage (programme root): env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e3_species_replay.py <cell|all> [--jobs 22] [--limit N]
Writes artifacts/plants/a3species_<cell>.csv.gz (--limit: code-path test, nothing written).
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e3_plants as P  # noqa: E402
from asdg.cascade import corr_matrix, emp_p  # noqa: E402
from asdg.genesets import coexpr_matched_sets  # noqa: E402
from asdg.species import WithinClassBasis  # noqa: E402

K = 200
CELLS = ([f"{c}_{f}_m25_a0" for c in ("aal", "dk", "cc200") for f in ("F-sp", "F-mod", "F-traj")]
         + [f"{c}_{f}_m25_a{a:g}" for c in ("aal", "dk") for f in ("C-sp", "C-gene") for a in (0.3, 0.6, 0.9)]
         + [f"aal_{f}_m{m}_a0" for m in (10, 100) for f in ("F-sp", "F-mod", "F-traj")])


def parse(cell: str):
    atlas, fam, mm, aa = cell.split("_")
    return atlas, fam, int(mm[1:]), float(aa[1:])


def replay_one(ctx, B, fam, m, a, seed_list: list[int], i) -> dict:
    rng = np.random.default_rng(np.random.SeedSequence(seed_list))
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
    row = dict(i=i, gen=gen, step=step, G2_status_replay=i2["status"], coexpr_replay=c_S, r_replay=np.nan,
               p_G2_replay=np.nan)
    if G2 is None and fam == "C-gene":
        return row
    z = lambda v: (v - v.mean()) / v.std()  # noqa: E731
    if fam == "C-sp":
        y = a * z(score) + np.sqrt(1 - a * a) * field
    elif fam == "C-gene":
        Bm = np.column_stack([np.ones(ctx.n_parcels), ctx.U.scores(G2).mean(0), ctx.pcs])
        resid = score - Bm @ np.linalg.lstsq(Bm, score, rcond=None)[0]
        y = a * z(resid) + np.sqrt(1 - a * a) * field
    else:
        y = field
    r_obs = corr_matrix(y, score)[0, 0]
    row["r_replay"] = r_obs
    if G2 is not None:
        row["p_G2_replay"] = emp_p(corr_matrix(y, ctx.U.scores(G2))[0], r_obs, 1)
    r2 = np.random.default_rng(np.random.SeedSequence(seed_list + [99]))  # separate stream for the species leg
    row.update(B.species(S, y, K, r2), c_s_w=B.coherence_w(S), brain_frac=float(B.brain[S].mean()))
    return row


def run_cell(cell: str, n_jobs: int, limit: int | None) -> None:
    from joblib import Parallel, delayed

    atlas, fam, m, a = parse(cell)
    saved = pd.read_csv(P.OUT / f"{cell}.csv.gz")
    idx = sorted(saved["i"].astype(int))[: limit or None]
    t0 = time.time()
    ctx = P.Ctx(atlas)
    B = WithinClassBasis(ctx.U.X, ctx.classes, brain=ctx.brain)
    base = [P.ATLAS_ID[atlas], P.FAM_ID[fam], m, int(round(a * 100))]

    def work(i):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return replay_one(ctx, B, fam, m, a, base + [i], i)

    d = pd.DataFrame(Parallel(n_jobs=n_jobs, backend="loky", batch_size=2)(delayed(work)(i) for i in idx))
    s = saved.set_index("i").loc[d["i"]]
    st = s["G2_status"].where(s["status"] == "ok", "unmatched").to_numpy()
    ok = st == d["G2_status_replay"].to_numpy()
    for col in ("r", "p_G2"):
        x, y_ = s[col].to_numpy(), d[f"{col}_replay"].to_numpy()
        ok &= (np.isnan(x) == np.isnan(y_)) & (np.isnan(x) | np.isclose(x, y_, rtol=0, atol=1e-12))
    d["replay_ok"] = ok
    print(f"{cell}: n={len(d)} replay_ok={int(ok.sum())} g6l ok={int((d.get('g6l_status') == 'ok').sum())} "
          f"{time.time() - t0:.0f}s", flush=True)
    if not ok.all():
        raise SystemExit(f"REPLAY MISMATCH in {cell}: plants {d.loc[~d['replay_ok'], 'i'].tolist()[:20]}")
    if limit:
        print("(--limit: code-path test, nothing written)")
        return
    out = P.OUT / f"a3species_{cell}.csv.gz"
    d.sort_values("i").to_csv(out, index=False)
    assert len(pd.read_csv(out)) == len(saved), "read-back mismatch"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cell")
    ap.add_argument("--jobs", type=int, default=22)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    for c in (CELLS if a.cell == "all" else [a.cell]):
        run_cell(c, a.jobs, a.limit)


if __name__ == "__main__":
    main()
