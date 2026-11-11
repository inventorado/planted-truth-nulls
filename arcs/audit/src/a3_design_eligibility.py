"""Design descriptor for prereg_amend_3 §3 (pre-freeze; AHBA + GAMBA only — no map, field, plant, gate or p-value):
G6l eligible-seed fractions and per-draw cost per atlas x registered set kind (to fix the plants' seed budget), and the
float32 window sums' error against float64 (to state the tolerance). Declared in prereg_amend_3 §0 (iv).

Per atlas x kind: 12 sets from the registered set generator (e3_align_plants.Ctx.make_set, no target cluster excluded),
each screened on 300 random seeds with the registered eligibility rule (species.g6l_sets); on the first 10 of those
seeds, c(W(o)) for every offset is recomputed in float64 (the v3 draft's parcels x genes loop): max |dc| and the number
of in-band decisions that differ. Seeds: SeedSequence([777, atlas id, kind id, j]).
Usage (programme root): env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\a3_design_eligibility.py [--jobs 22]
Writes arcs/audit/results/a3_design_eligibility.json.
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e3_align_plants as A  # noqa: E402

N_SETS, N_SEEDS, N_F64 = 12, 300, 10
RES = A.P.ROOT / "arcs" / "audit" / "results"


def c_float64(B, g, S, m, n_rank, half):
    Zw = B.Zw
    r = Zw[:, g] @ Zw
    r[S] = -np.inf
    r[g] = -np.inf
    rank = np.argsort(-r, kind="stable")[:n_rank]
    W = Zw[:, rank[: half + m - 1]]
    C0 = np.concatenate([np.zeros((W.shape[0], 1)), np.cumsum(W, axis=1)], axis=1)
    v = C0[:, m - 1: m - 1 + half + 1] - C0[:, : half + 1] + Zw[:, [g]]
    return rank, (np.einsum("ij,ij->j", v, v) - m) / (m * (m - 1))


def one(ctx, kind, j):
    rng = np.random.default_rng(np.random.SeedSequence([777, A.ATLAS_ID[ctx.atlas], A.KIND_ID[kind], j]))
    S, _ = ctx.make_set(kind, rng, -1)
    B, m = ctx.B, len(S)
    c_s = B.coherence_w(S)
    t0 = time.perf_counter()
    _, info = B.g6l_sets(S, N_SEEDS, rng, budget_factor=1, min_seeds=0)
    per_draw = (time.perf_counter() - t0) / info["draws"]
    n_rank = B.G - m - 1
    half = n_rank // 2
    C0 = np.empty((half + m, B.ZwT32.shape[1]), np.float32)
    C0[0] = 0.0
    dmax, flips, rank_diff = 0.0, 0, 0
    for g in rng.choice(np.setdiff1d(np.arange(B.G), S), N_F64, replace=False):
        rank, c = B.window_curve(g, S, m, n_rank, half, C0)
        rank64, c64 = c_float64(B, g, S, m, n_rank, half)
        rank_diff += int(not np.array_equal(rank, rank64))
        dmax = max(dmax, float(np.abs(c - c64).max()))
        flips += int(((np.abs(c - c_s) <= 0.02) != (np.abs(c64 - c_s) <= 0.02)).sum())
    return dict(kind=kind, c_s_w=c_s, eligible_frac=info["eligible"] / info["draws"], s_per_draw=per_draw,
                dc_max=dmax, band_flips=flips, offsets=N_F64 * (half + 1), rank_diff=rank_diff)


def main():
    from joblib import Parallel, delayed

    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=22)
    a = ap.parse_args()
    out = {}
    for atlas in ("aal", "dk", "cc200", "dk-ctx"):
        t0 = time.time()
        ctx = A.Ctx(atlas)
        rows = Parallel(n_jobs=a.jobs, backend="loky")(delayed(one)(ctx, k, j) for k in A.ALL_KINDS
                                                         for j in range(N_SETS))
        per = {}
        for k in A.ALL_KINDS:
            r = [x for x in rows if x["kind"] == k]
            e = np.array([x["eligible_frac"] for x in r])
            per[k] = dict(c_s_w_median=float(np.median([x["c_s_w"] for x in r])), elig_min=float(e.min()),
                          elig_median=float(np.median(e)), elig_max=float(e.max()),
                          ms_per_draw=float(1e3 * np.median([x["s_per_draw"] for x in r])),
                          f32_dc_max=float(max(x["dc_max"] for x in r)),
                          f32_band_flips=int(sum(x["band_flips"] for x in r)),
                          f32_offsets=int(sum(x["offsets"] for x in r)),
                          f32_rank_diff=int(sum(x["rank_diff"] for x in r)))
        out[atlas] = dict(genes=int(ctx.G), parcels=int(len(ctx.classes)), kinds=per)
        print(f"{atlas}: genes={ctx.G} parcels={len(ctx.classes)} {time.time() - t0:.0f}s", flush=True)
        for k, v in per.items():
            print(f"  {k:10s} c_w={v['c_s_w_median']:.3f} elig min/med/max={v['elig_min']:.3f}/"
                  f"{v['elig_median']:.3f}/{v['elig_max']:.3f} {v['ms_per_draw']:.1f} ms/draw | f32 max|dc| "
                  f"{v['f32_dc_max']:.1e} flips {v['f32_band_flips']}/{v['f32_offsets']} rank_diff "
                  f"{v['f32_rank_diff']}", flush=True)
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "a3_design_eligibility.json").write_text(json.dumps(dict(n_sets=N_SETS, n_seeds=N_SEEDS, n_f64=N_F64,
                                                                    atlases=out), indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
