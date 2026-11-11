"""ASDG-AUD-E3-plants C3 (prereg §6.4, descriptor only): coordinate gradients (A-P, I-S, |x|) x 400 random and
400 coexpressed-module sets per class. No ground truth (a module can genuinely track a gradient), so nothing here
gates; the rejection rate of every null is reported per (class, set kind, gradient).

Per class (V-AAL, V-DK, V-CC200; primary parcels as in e3_plants.py): maps y = MNI y (A-P), z (I-S), |x|. Sets
(m = 25): 'random' = uniform from the universe; 'module' = a random seed gene plus its 24 highest-coexpression
neighbours (e3_plants.module). Each set runs the plant nulls: Level 0 (naive), S1, S2, S1c, S2c and both Level-1
pairs, G1-G5 and Level 2, J1 for both pairs, the naive joint null; one-sided in direction +1 (the plant
convention, §4), (k+1)/(n+1), 500 surrogates / 500 sets / M = K = 500 as for plants (§6.2). The map is fixed per
(class, gradient), so one draw of surrogates per map is shared by all its sets (a stated deviation from the plants'
fresh draws); G-sets are drawn once per set and shared by the three maps. J1 applies both §4.4 rules (sd_k > 1e-9
and mean pairwise Jaccard of the G2 pool < 0.5) and propagates NaN through the pair max.

Usage (programme root): env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e3_c3_gradients.py [--jobs 22] [--atlas aal] [--limit N]
Writes artifacts/plants/c3_<atlas>.csv.gz (one row per set x map) and arcs/audit/results/e3_c3_gradients.json
(--limit writes nothing: a code-path test).
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e3_plants as P  # noqa: E402  (puts src/ on sys.path; Ctx, module, primary_parcels, ids, N_SURR, N_SETS)
from e3_j1_pool_replay import exact_mean_jaccard  # noqa: E402
from asdg.spatial import brainsmash_surrogates, stratified_surrogates  # noqa: E402
from asdg.genesets import random_sets, coexpr_matched_sets, trajectory_matched_sets  # noqa: E402
from asdg.cascade import corr_matrix, emp_p, naive_p, joint_j1, naive_joint  # noqa: E402

RES = P.ROOT / "arcs" / "audit" / "results"
C3_ID, M, N_PER_KIND = 6, 25, 400
KINDS = {"random": 0, "module": 1}
MAPS = ("AP", "IS", "absx")
JACCARD_MAX = 0.5


def gradient_maps(atlas: str) -> dict:
    _, _, xyz = P.primary_parcels(atlas)
    return {"AP": xyz[:, 1].astype(float), "IS": xyz[:, 2].astype(float), "absx": np.abs(xyz[:, 0]).astype(float)}


def map_surrogates(ctx, y: np.ndarray, seed_seq) -> dict:
    s = [int(x) for x in np.random.default_rng(seed_seq).integers(2**31, size=4)]
    return {"S1": brainsmash_surrogates(y, ctx.D, P.N_SURR, s[0]), "S2": ctx.ms.surrogates(y, P.N_SURR, s[1]),
            "S1c": stratified_surrogates(y, ctx.D, ctx.classes, P.N_SURR, s[2], "brainsmash"),
            "S2c": stratified_surrogates(y, ctx.D, ctx.classes, P.N_SURR, s[3], "msr")}


def one_set(ctx, kind: str, i: int, atlas: str, maps: dict, surr: dict) -> list[dict]:
    rng = np.random.default_rng(np.random.SeedSequence([P.ATLAS_ID[atlas], C3_ID, M, KINDS[kind], i]))
    S = P.module(ctx, M, rng, "coexp") if kind == "module" else rng.choice(ctx.all, size=M, replace=False)
    score = ctx.U.scores(S)[0]
    c_S = ctx.U.mean_coexpr(S)
    G2, i2 = coexpr_matched_sets(ctx.U, ctx.all, M, c_S, P.N_SETS, rng, exclude=S)
    sets = {"G1": random_sets(ctx.all, M, P.N_SETS, rng, exclude=S),
            "G3": random_sets(ctx.brain, M, P.N_SETS, rng, exclude=S), "G2": G2}
    sets["G4"], i4 = coexpr_matched_sets(ctx.U, ctx.brain, M, c_S, P.N_SETS, rng, exclude=S)
    sets["G5"], i5 = trajectory_matched_sets(ctx.U, [ctx.U.genes[g] for g in S], ctx.tr, P.N_SETS, rng)
    set_scores = {k: None if v is None else ctx.U.scores(v) for k, v in sets.items()}
    jac = exact_mean_jaccard(G2) if G2 is not None else np.nan
    j1_status = ("unmatched" if G2 is None else "degenerate_jaccard" if jac >= JACCARD_MAX else "ok")
    rows = []
    for mname in MAPS:
        y, sm = maps[mname], surr[mname]
        r_obs = corr_matrix(y, score)[0, 0]
        row = dict(atlas=atlas, kind=kind, i=i, map=mname, r=r_obs, coexpr=c_S, p_naive=naive_p(r_obs, len(y), +1),
                   G2_status=i2["status"], G4_status=i4["status"], G5_status=i5["status"], jaccard_G2=jac)
        for k, s in sm.items():
            row[f"p_{k}"] = emp_p(corr_matrix(s, score)[:, 0], r_obs, +1)
        row["p_L1_joint"] = max(row["p_S1"], row["p_S2"])
        row["p_L1_strat"] = max(row["p_S1c"], row["p_S2c"])
        for k, sc in set_scores.items():
            row[f"p_{k}"] = np.nan if sc is None else emp_p(corr_matrix(y, sc)[0], r_obs, +1)
        g = [row[f"p_G{j}"] for j in range(1, 6)]
        row["p_L2"] = np.nan if any(np.isnan(g)) else max(g)
        row["J1_status"] = j1_status
        for pair, (sa, sb) in {"joint": ("S1", "S2"), "strat": ("S1c", "S2c")}.items():
            if j1_status != "ok":
                row[f"p_J1_{pair}"] = np.nan
                continue
            pa = joint_j1(y, score, set_scores["G2"], sm[sa], +1)[1]
            pb = joint_j1(y, score, set_scores["G2"], sm[sb], +1)[1]
            row[f"p_J1_{pair}"] = np.nan if np.isnan(pa) or np.isnan(pb) else max(pa, pb)
            if np.isnan(row[f"p_J1_{pair}"]):
                row["J1_status"] = "degenerate_pool"
        row["p_naivejoint"] = naive_joint(y, set_scores["G1"], sm["S1"], score, +1, rng)
        rows.append(row)
    return rows


def rates(df: pd.DataFrame) -> list[dict]:
    out = []
    pcols = [c for c in df.columns if c.startswith("p_")]
    for (atlas, kind, mname), sub in df.groupby(["atlas", "kind", "map"], sort=False):
        row = dict(atlas=atlas, kind=kind, map=mname, n=int(len(sub)))
        for c in pcols:
            x = sub[c].dropna()
            row[c] = round(float((x < 0.05).mean()), 4) if len(x) else None
            row[f"missing_{c}"] = int(sub[c].isna().sum())
        row["J1_status"] = {str(k): int(v) for k, v in sub["J1_status"].value_counts().items()}
        row["G5_status"] = {str(k): int(v) for k, v in sub["G5_status"].value_counts().items()}
        out.append(row)
    return out


def run_atlas(atlas: str, n_jobs: int, limit: int | None) -> pd.DataFrame:
    from joblib import Parallel, delayed

    t0 = time.time()
    ctx = P.Ctx(atlas)
    maps = gradient_maps(atlas)
    assert all(len(v) == ctx.n_parcels for v in maps.values()), "gradient maps do not match the primary parcels"
    surr = {m: map_surrogates(ctx, maps[m], np.random.SeedSequence([P.ATLAS_ID[atlas], C3_ID, 0, j]))
            for j, m in enumerate(MAPS)}
    n = limit or N_PER_KIND
    jobs = [(k, i) for k in KINDS for i in range(n)]

    def work(k, i):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return one_set(ctx, k, i, atlas, maps, surr)

    rows = Parallel(n_jobs=n_jobs, backend="loky", batch_size=2)(delayed(work)(k, i) for k, i in jobs)
    df = pd.DataFrame([r for rs in rows for r in rs])
    assert len(df) == len(jobs) * len(MAPS)
    print(f"C3 {atlas}: {len(jobs)} sets x {len(MAPS)} maps, parcels={ctx.n_parcels} {time.time() - t0:.0f}s",
          flush=True)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=22)
    ap.add_argument("--atlas", default=None, help="one class only (default: aal, dk, cc200)")
    ap.add_argument("--limit", type=int, default=None, help="sets per kind (code-path test; nothing written)")
    a = ap.parse_args()
    atlases = [a.atlas] if a.atlas else ["aal", "dk", "cc200"]
    frames = [run_atlas(x, a.jobs, a.limit) for x in atlases]
    df = pd.concat(frames, ignore_index=True)
    summary = rates(df)
    if a.limit:
        print(json.dumps(summary[:3], indent=1, default=float))
        print("(--limit: code-path test only, nothing written)")
        return
    for x, f in zip(atlases, frames):
        out = P.OUT / f"c3_{x}.csv.gz"
        f.to_csv(out, index=False)
        assert len(pd.read_csv(out)) == len(f), "read-back mismatch"
    res = dict(rates=summary, n_sets_per_kind=N_PER_KIND, m=M, maps={"AP": "MNI y", "IS": "MNI z", "absx": "|MNI x|"},
               direction=+1, n_surrogates=P.N_SURR, n_sets=P.N_SETS,
               seed_scheme="sets: SeedSequence([ATLAS_ID, 6, 25, kind(random=0,module=1), i]); map surrogates: "
                           "SeedSequence([ATLAS_ID, 6, 0, map index])",
               files=[f"c3_{x}.csv.gz" for x in atlases],
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               commit=subprocess.run(["git", "-C", str(P.ROOT), "rev-parse", "HEAD"], capture_output=True,
                                     text=True).stdout.strip())
    (RES / "e3_c3_gradients.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"wrote {RES / 'e3_c3_gradients.json'}")


if __name__ == "__main__":
    main()
