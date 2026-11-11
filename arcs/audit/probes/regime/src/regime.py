"""ASDG-AUD-E5-regime, spaces A / A' / A'' (probe prereg v3 §2).

Spaces: A = Cao 2024's matrix (34 left-cortex Desikan regions x 6,513 genes; the E4 R1 inputs); A' = our V-DK
left-cortex matrix (the dk-ctx replica: same 34 regions, 15,633 genes, prereg §3.1 processing); A'' = A' restricted
to the gene symbols shared with Cao's 6,513. Regions matched by name.
Sets (built in each space's own matrix): A1 = 100 of Cao's shipped sets (space A only; plants), A1r = uniform random,
A2m = graded core + filler (a core of round(f m) = seed + its most coexpressed genes, f in .2/.35/.5/.65, plus uniform
filler: intermediate coherence), A2 = tight modules (seed + its m - 1 most coexpressed); 50 at m = 25 and 50 at
m = 100 each; cells are per m. Maps: B1 = Cao's near-noise maps 1-500, B2 = 500 smooth
fields on the 34 V-DK left-cortex centroids (prereg §6.1 generators, 100 each, one class). Statistics x sidedness:
C1 Mean of per-gene Fisher-z r {+, +-, c}; C2 Meanabs (upper); C3 T = r(map, set mean-expression score) {+, +-, c};
'+' one-sided positive, '+-' two-sided |stat|, 'c' centred two-sided |stat - null mean|. Nulls (K = 1,000 per set,
drawn once, shared across all maps): N1 uniform excluding S; N2 Cao's rejection sampler (all genes, tol .01,
<= 1e6 draws; < K accepted = unmatched); N3 G2 (+-.02); N3' G2 (+-.01; A1 only, plant P6).
Plants: P1, P2, P5, P6 (must pass; else the run stops with the plants reported), P4 (power, descriptor).
Classification (prereg §4): two-way (sets x maps) cluster-bootstrap 99% CI; anticonservative iff lower > .05 and
rate > .07; calibrated iff upper <= .07 and rate <= .06; else indeterminate.

Usage (programme root): env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\probes\\regime\\src\\regime.py
    [--jobs 22] [--smoke]      (--smoke: 4 sets per type x 40 maps x K 100, space A only, nothing written)
Writes arcs/audit/probes/regime/results/regime_A.json and artifacts/regime/regime_A_pvals.npz.
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
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "arcs" / "audit" / "src"))
sys.path.insert(0, str(ROOT / "src"))
import e4_r1_cao as R1  # noqa: E402
import e3_plants as P  # noqa: E402
from asdg.genesets import Universe, coexpr_matched_sets  # noqa: E402
from asdg.spatial import FieldGenerator  # noqa: E402

K, N_MAPS, ALPHAS = 1000, 500, (0.05, 0.025)
GENS = [("grf15", 0.0), ("grf30", 0.0), ("grf60", 0.0), ("sar5", 0.0), ("sar9", 0.0)]
SEED = 5  # nulls: [5, space id, set-type id, tag, set index] (tag 0 N1, 1 N2, 2 N3, 3 coherence reference,
#          4 N3'); fields: [5, 0, 0, 2, map index]; set construction: [5, space id, 9, 9, 0]; bootstrap: [5, 0, 7, 7, 7]
SPACE_ID = {"A": 1, "A'": 2, "A''": 3}
TYPE_ID = {"A1": 1, "A1r": 2, "A2m": 3, "A2": 4}
CORE_FRACS = (0.2, 0.35, 0.5, 0.65)  # A2m: graded core fractions (intermediate coherence)
FORMS = ["C1+", "C1pm", "C1c", "C2", "C3+", "C3pm", "C3c"]
OUT = ROOT / "arcs" / "audit" / "probes" / "regime" / "results"
ART = ROOT / "artifacts" / "regime"
# R1 (results/e4_r1_cao.json; artifacts/r1_cao/r1_cao_pertest.npz) on exactly this probe's A1 x B1 subset
P1_TARGET = {("N1", "C1pm"): 0.0610, ("N1", "C2"): 0.0490, ("N2", "C1pm"): 0.0446, ("N2", "C2"): 0.0499}
P6_TARGET = {("N3'", "C1pm"): 0.0366, ("N3'", "C2"): 0.0526}


def git(*a) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout.strip()


# ------------------------------------------------------------------------------------------------ spaces
def cao_space():
    g, b, names, set_idx, sizes, _ = R1.load_inputs()
    raw = pd.read_csv(R1.F_GENE, nrows=0).columns.tolist()
    raw = [c for c in raw if c != "Region"]
    assert len(raw) == g.shape[1]
    regions = [r.replace("L_", "", 1).lower() for r in g.index]
    return dict(X=g.to_numpy(dtype=float), genes=raw, regions=regions, maps=b.to_numpy(dtype=float)[:, :N_MAPS],
                set_idx=set_idx, sizes=sizes)


def our_space():
    """V-DK left cortex (the dk-ctx replica's 34 parcels); region names from the atlas label table."""
    expr, classes, xyz = P.primary_parcels("dk")
    keep = np.asarray(classes) == "cortex"
    info = pd.read_csv(P.AHBA / "dk_atlas_info.csv").set_index("id")
    ids = [int(i) for i in expr.index[keep]]
    assert all(info.loc[i, "hemisphere"] == "L" for i in ids), "non-left cortex parcel in V-DK cortex class"
    regions = [str(info.loc[i, "label"]).lower() for i in ids]
    return dict(expr=expr.loc[keep], regions=regions, xyz=np.asarray(xyz)[keep])


def reorder(src_regions, dst_regions):
    idx = {r: i for i, r in enumerate(src_regions)}
    miss = [r for r in dst_regions if r not in idx]
    assert not miss, f"regions without a match: {miss[:5]}"
    return np.array([idx[r] for r in dst_regions])


# ------------------------------------------------------------------------------------------------- sets
def modules(U: Universe, rng, n: int, m: int, window: int | None) -> list[np.ndarray]:
    """window None: seed + its m - 1 most coexpressed genes (tight); window W: seed + m - 1 uniform from its top W."""
    out = []
    for _ in range(n):
        g = int(rng.integers(len(U.genes)))
        r = U.Z[:, g] @ U.Z
        r[g] = -np.inf
        top = np.argsort(r)[::-1]
        mem = top[: m - 1] if window is None else rng.choice(top[:window], size=m - 1, replace=False)
        out.append(np.sort(np.concatenate([[g], mem])))
    return out


def graded(U: Universe, rng, n: int, m: int) -> list[np.ndarray]:
    """A2m: a core of round(f m) genes (a seed + its most coexpressed genes) plus uniform filler, f cycling through
    CORE_FRACS — intermediate coherence (the published-list range), graded by f."""
    out = []
    for i in range(n):
        core_n = max(2, int(round(CORE_FRACS[i % len(CORE_FRACS)] * m)))
        g = int(rng.integers(len(U.genes)))
        r = U.Z[:, g] @ U.Z
        r[g] = -np.inf
        core = np.concatenate([[g], np.argsort(r)[::-1][: core_n - 1]])
        fill = rng.choice(np.setdiff1d(np.arange(len(U.genes)), core), size=m - core_n, replace=False)
        out.append(np.sort(np.concatenate([core, fill])))
    return out


def coherence(ZT, s) -> float:
    v = ZT[s].sum(0)
    return float((v @ v - len(s)) / (len(s) * (len(s) - 1)))


# ------------------------------------------------------------------------------------------ statistics
def corr_cols(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return R1.unit_cols(A).T @ R1.unit_cols(B)


def stats_of(Asets, X, Zobs, Y):
    """(Mean, Meanabs, T), each (sets x maps)."""
    return (np.asarray(Asets @ Zobs), np.asarray(Asets @ np.abs(Zobs)),
            corr_cols(np.asarray(Asets @ X.T).T, Y))


def forms_p(null: np.ndarray, obs: np.ndarray, k: int, kind: str) -> dict:
    """p per map for each sidedness form; null (k x maps), obs (maps,)."""
    f = lambda c: ((c + 1) / (k + 1)).astype(np.float32)  # noqa: E731
    if kind == "C2":
        return {"C2": f((null >= obs[None, :]).sum(0))}
    mu = null.mean(0)
    return {f"{kind}+": f((null >= obs[None, :]).sum(0)), f"{kind}pm": f((np.abs(null) >= np.abs(obs)[None, :]).sum(0)),
            f"{kind}c": f((np.abs(null - mu) >= np.abs(obs - mu)[None, :]).sum(0))}


def pool_pvals(pool, s, X, Zobs, Y):
    A = R1.set_matrix([s], X.shape[1])
    om, oa, ot = (v[0] for v in stats_of(A, X, Zobs, Y))
    Bm = R1.set_matrix(list(pool), X.shape[1])
    nm, na, nt = stats_of(Bm, X, Zobs, Y)
    k = len(pool)
    return {**forms_p(nm, om, k, "C1"), **forms_p(na, oa, k, "C2"), **forms_p(nt, ot, k, "C3")}


def one_set(j, s, sp_id, ty_id, X, Zobs, Y, U, ZT, k, max_draws, plants, extra_n3p):
    t0 = time.time()
    ss = lambda tag: np.random.default_rng(np.random.SeedSequence([SEED, sp_id, ty_id, tag, j]))  # noqa: E731
    target = coherence(ZT, s)
    pool = np.setdiff1d(np.arange(X.shape[1]), s)
    r1 = ss(0)
    n1 = np.stack([r1.choice(pool, size=len(s), replace=False) for _ in range(k)])
    n2, _, draws = R1.cao_sampler(ZT, len(s), target, ss(1), n_target=k, max_iter=max_draws)
    n3, i3 = coexpr_matched_sets(U, np.arange(X.shape[1]), len(s), target, k, ss(2), exclude=s)
    pools = {"N1": n1, "N2": n2 if len(n2) >= k else None, "N3": n3}
    if extra_n3p:
        n3p, _ = coexpr_matched_sets(U, np.arange(X.shape[1]), len(s), target, k, ss(4), tol=0.01, exclude=s)
        pools["N3'"] = n3p
    rand = ZT[R1.draw_distinct(ss(3), ZT.shape[0], len(s), 2000)].sum(1)
    rc = (np.einsum("ij,ij->i", rand, rand) - len(s)) / (len(s) * (len(s) - 1))
    info = dict(m=len(s), coexp=target, target_z=float((target - rc.mean()) / rc.std()), n2_accepted=int(len(n2)),
                n2_draws=int(draws), n3_status="ok" if n3 is not None else i3.get("status", "unmatched"))
    out = {nl: (pool_pvals(pl, s, X, Zobs, Y) if pl is not None else None) for nl, pl in pools.items()}
    planted = {}
    for v, yp in plants.items():  # P4: two planted-score variants, the same pools
        Yp = yp[:, None]
        Zp = R1.fisher_z(corr_cols(X, Yp))
        planted[v] = {nl: ({c: float(p[0]) for c, p in pool_pvals(pl, s, X, Zp, Yp).items()} if pl is not None else None)
                      for nl, pl in pools.items()}
    info["seconds"] = time.time() - t0
    return j, out, info, planted


# -------------------------------------------------------------------------------------- classification
def classify(rej: np.ndarray, rng, B: int) -> dict:
    """rej: (sets x maps) 0/1. Rate, two-way cluster-bootstrap 99% CI, three-way class (prereg §4)."""
    rate = float(rej.mean())
    ns, nm = rej.shape
    bs = np.array([rej[np.ix_(rng.integers(ns, size=ns), rng.integers(nm, size=nm))].mean() for _ in range(B)])
    lo, hi = (float(x) for x in np.quantile(bs, [0.005, 0.995]))
    cls = ("anticonservative" if lo > 0.05 and rate > 0.07 else
           "calibrated" if hi <= 0.07 and rate <= 0.06 else "indeterminate")
    return dict(rate=rate, ci99=[lo, hi], cls=cls)


def classifier_selftest() -> list[str]:
    rng = np.random.default_rng(0)
    fails = []
    for rate, want in ((0.03, "calibrated"), (0.15, "anticonservative"), (0.065, "indeterminate")):
        rej = (rng.random((100, 500)) < rate).astype(float)
        got = classify(rej, rng, 200)["cls"]
        if got != want:
            fails.append(f"classifier: rate {rate} -> {got}, expected {want}")
    null = rng.standard_normal((999, 3))
    p = forms_p(null, np.array([3.2, -3.2, 0.0]), 999, "C1")
    if not (p["C1+"][0] < 0.01 and p["C1+"][1] > 0.99 and p["C1pm"][1] < 0.01 and p["C1c"][2] > 0.9):
        fails.append(f"sidedness forms wrong: {p}")
    # set constructors on a toy matrix: tight = seed + its top m - 1; coherence ordering A2 (tight) > A2m (graded
    # core + filler) > A1r (random); the ||sum z||^2 identity equals the pairwise mean
    Xt = rng.standard_normal((34, 400)) + np.outer(rng.standard_normal(34), rng.uniform(0, 2, 400))
    Ut = Universe(pd.DataFrame(Xt, columns=[f"g{i}" for i in range(400)]))
    ZTt = np.ascontiguousarray(Ut.Z.T)
    tight = modules(Ut, np.random.default_rng(1), 5, 25, None)
    win = graded(Ut, np.random.default_rng(1), 8, 25)
    rnd = [np.sort(rng.choice(400, 25, replace=False)) for _ in range(5)]
    for s in tight:
        seed = [g for g in s if set(np.argsort(Ut.Z[:, g] @ Ut.Z)[::-1][1:25]) <= set(s)]
        if not seed:
            fails.append("tight module is not a seed plus its 24 most coexpressed genes")
    ct, cw, cr = (np.mean([coherence(ZTt, s) for s in ss]) for ss in (tight, win, rnd))
    if not ct > cw > cr:
        fails.append(f"coherence ordering A2 {ct:.3f} > A2m {cw:.3f} > A1r {cr:.3f} violated")
    s = tight[0]
    pair = np.corrcoef(Xt[:, s].T)[np.triu_indices(25, 1)].mean()
    if abs(pair - coherence(ZTt, s)) > 1e-9:
        fails.append(f"coherence identity: {coherence(ZTt, s)} vs pairwise {pair}")
    return fails


# ------------------------------------------------------------------------------------------------- main
def main():
    from joblib import Parallel, delayed

    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=22)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    bad = classifier_selftest()
    if bad:
        raise SystemExit("SELFTEST FAILED: " + "; ".join(bad))
    t_start = time.time()
    cao, ours = cao_space(), our_space()
    # maps on Cao's region order; each space reorders its rows to the maps' order
    xyz = ours["xyz"][reorder(ours["regions"], cao["regions"])]
    fg = FieldGenerator(xyz, np.array(["cortex"] * 34))
    Y2 = np.column_stack([fg.field(gen, np.random.default_rng(np.random.SeedSequence([SEED, 0, 0, 2, i])), step)
                          for i, (gen, step) in enumerate(GENS * (N_MAPS // len(GENS)))])
    Y = np.column_stack([cao["maps"], Y2])                                  # 34 x 1,000 (B1 | B2)
    fam = np.array(["B1"] * N_MAPS + ["B2"] * N_MAPS)
    if a.smoke:
        keep = list(range(20)) + list(range(N_MAPS, N_MAPS + 20))
        Y, fam, Y2 = Y[:, keep], fam[keep], Y2[:, :20]
    W = 1.0 / np.maximum(np.linalg.norm(xyz[:, None] - xyz[None], axis=2), 1e-9)
    np.fill_diagonal(W, 0.0)
    Yc = Y - Y.mean(0)
    moran = (34 / W.sum()) * np.einsum("ik,ij,jk->k", Yc, W, Yc) / (Yc ** 2).sum(0)
    # the three matrices, rows in the maps' region order
    o = ours["expr"].iloc[reorder(ours["regions"], cao["regions"])]
    spaces = {"A": pd.DataFrame(cao["X"], columns=cao["genes"]), "A'": o,
              "A''": o[[c for c in o.columns if c in set(cao["genes"])]]}
    kk, max_draws, n_per = K, 1_000_000, 50
    if a.smoke:
        spaces = {"A": spaces["A"]}
        kk, max_draws, n_per = 100, 100_000, 2
    z = lambda v: (v - v.mean()) / v.std()  # noqa: E731
    results, set_info, power = {}, {}, {}
    for sp, df in spaces.items():
        U = Universe(df)
        assert U.X.shape[1] == df.shape[1], f"{sp}: Universe dropped constant genes"
        X = U.X
        ZT = np.ascontiguousarray(U.Z.T)
        Zobs = R1.fisher_z(corr_cols(X, Y))
        rng_m = np.random.default_rng(np.random.SeedSequence([SEED, SPACE_ID[sp], 9, 9, 0]))
        types = {"A1r": [np.sort(rng_m.choice(X.shape[1], size=m, replace=False)) for m in (25, 100)
                         for _ in range(n_per)],
                 "A2m": graded(U, rng_m, n_per, 25) + graded(U, rng_m, n_per, 100),
                 "A2": modules(U, rng_m, n_per, 25, None) + modules(U, rng_m, n_per, 100, None)}
        if sp == "A":
            order = {m: [i for i in range(len(cao["set_idx"])) if cao["sizes"][i] == m][:10] for m in range(20, 201, 20)}
            a1 = [cao["set_idx"][i] for m in range(20, 201, 20) for i in order[m]]
            types = {"A1": a1[:: 25] if a.smoke else a1, **types}
        for ty, sets in types.items():
            field_for = lambda j: Y2[:, j % Y2.shape[1]]  # noqa: E731
            plants = [{"raw": 0.5 * z(X[:, s].mean(1)) + np.sqrt(0.75) * z(field_for(j)),
                       "zscored": 0.5 * z(U.Z[:, s].mean(1)) + np.sqrt(0.75) * z(field_for(j))}
                      for j, s in enumerate(sets)]
            out = Parallel(n_jobs=a.jobs, backend="loky")(
                delayed(one_set)(j, s, SPACE_ID[sp], TYPE_ID[ty], X, Zobs, Y, U, ZT, kk, max_draws, plants[j],
                                 sp == "A" and ty == "A1")
                for j, s in enumerate(sets))
            set_info[f"{sp}|{ty}"] = [o_[2] for o_ in out]
            for nl in ("N1", "N2", "N3", "N3'"):
                if not any(nl in o_[1] for o_ in out):
                    continue
                for c in FORMS:
                    rows = [o_[1][nl][c] if o_[1].get(nl) is not None else np.full(Y.shape[1], np.nan, np.float32)
                            for o_ in out]
                    results[(sp, ty, nl, c)] = np.stack(rows)
                for v in ("raw", "zscored"):
                    for c in FORMS:
                        vals = [o_[3][v][nl][c] for o_ in out if o_[3][v].get(nl) is not None]
                        power[f"{sp}|{ty}|{nl}|{c}|{v}"] = float(np.mean(np.array(vals) < 0.05)) if vals else None
            print(f"{sp} {ty}: {len(sets)} sets x {Y.shape[1]} maps, {time.time() - t_start:.0f}s", flush=True)
    rng_b = np.random.default_rng(np.random.SeedSequence([SEED, 0, 7, 7, 7]))
    B_boot = 50 if a.smoke else 1000

    def fit(x, y):
        """Linear fit with the x at which the fitted rejection rate crosses .05 (cross_05 None if the slope is 0;
        cross_inside_data False when the crossing lies outside the data). None if there is too little variation."""
        if len(x) < 3 or np.std(x) == 0 or np.std(y) == 0:
            return None
        lr = stats.linregress(x, y)
        cross = (0.05 - lr.intercept) / lr.slope if lr.slope != 0 else None
        inside = cross is not None and np.min(x) <= cross <= np.max(x)
        return dict(slope=float(lr.slope), intercept=float(lr.intercept), r=float(lr.rvalue),
                    cross_05=float(cross) if cross is not None else None, cross_inside_data=bool(inside))

    cells, regress = {}, {"moran": {}, "coherence": {}}
    groups = {}  # (sp, ty) -> [(m label, set mask)]
    for (sp, ty, nl, c), p in results.items():
        ms = np.array([i["m"] for i in set_info[f"{sp}|{ty}"]])
        grp = [("mall", np.ones(len(ms), bool))] if ty == "A1" else [(f"m{m}", ms == m) for m in (25, 100)]
        groups[(sp, ty)] = grp
        ok = ~np.isnan(p).any(axis=1)
        for mlab, mask in grp:
            sel = ok & mask
            for mt in ("B1", "B2"):
                pm = p[sel][:, fam == mt]
                cells[f"{sp}|{ty}|{mlab}|{mt}|{nl}|{c}"] = dict(
                    n_sets=int(sel.sum()), n_unmatched=int((mask & ~ok).sum()), n_maps=int((fam == mt).sum()),
                    **{f"a{al:g}": (classify((pm < al).astype(float), rng_b, B_boot) if sel.any() else None)
                       for al in ALPHAS})
            if sel.any():  # O2: per-map rejection rate at .05 on the map's Moran's I, within each family and pooled
                rm = (p[sel] < 0.05).mean(0)
                regress["moran"][f"{sp}|{ty}|{mlab}|{nl}|{c}"] = {
                    "B1": fit(moran[fam == "B1"], rm[fam == "B1"]), "B2": fit(moran[fam == "B2"], rm[fam == "B2"]),
                    "pooled": fit(moran, rm)}
    for sp in spaces:  # O3: per-set rejection rate at .05 on the set's coherence, pooling A1r / A2m / A2 at one m
        for mlab in ("m25", "m100"):
            for mt in ("B1", "B2"):
                for nl in ("N1", "N2", "N3"):
                    for c in FORMS:
                        xs, ys = [], []
                        for ty in ("A1r", "A2m", "A2"):
                            if (sp, ty, nl, c) not in results:
                                continue
                            p = results[(sp, ty, nl, c)]
                            mask = dict(groups[(sp, ty)])[mlab] & ~np.isnan(p).any(axis=1)
                            co = np.array([i["coexp"] for i in set_info[f"{sp}|{ty}"]])
                            xs.append(co[mask])
                            ys.append((p[mask][:, fam == mt] < 0.05).mean(1))
                        if xs:
                            regress["coherence"][f"{sp}|{mlab}|{mt}|{nl}|{c}"] = fit(np.concatenate(xs),
                                                                                     np.concatenate(ys))

    # plants
    def cell_rate(key):
        return cells[key]["a0.05"]["rate"] if cells.get(key) and cells[key]["a0.05"] else float("nan")

    p1 = {f"{nl}|{c}": dict(ours=cell_rate(f"A|A1|mall|B1|{nl}|{c}"), target=t,
                           pass_=abs(cell_rate(f"A|A1|mall|B1|{nl}|{c}") - t) <= 0.010)
          for (nl, c), t in P1_TARGET.items()}
    d = np.load(ROOT / "artifacts" / "r1_cao" / "r1_cao_pertest.npz")
    sub = np.array([i for m in range(20, 201, 20) for i in [j for j in range(500) if d["set_size"][j] == m][:10]])
    sp_r = {}
    for c, key in (("C1pm", "p_ours_competitive_mean"), ("C2", "p_ours_competitive_meanabs")):
        mine = results[("A", "A1", "N1", c)][:, fam == "B1"]
        ref = d[key][np.ix_(sub, np.arange(N_MAPS))] if not a.smoke else None
        sp_r[c] = (float(stats.spearmanr(mine.ravel(), ref.ravel()).statistic) if ref is not None else None)
    p1["spearman_N1"] = dict(values=sp_r, pass_=all(v is None or v >= 0.95 for v in sp_r.values()))
    coex = np.array([i["coexp"] for i in set_info["A|A1"]])
    psg = (results[("A", "A1", "N1", "C1pm")][:, fam == "B1"] < 0.05).mean(1)
    r2 = float(np.corrcoef(coex, psg)[0, 1] ** 2)
    # P5 (exchangeability): uniform random sets vs N1 must not be anticonservative (C3pm, C2)
    p5 = {c: cells[f"A|A1|mall|B1|N1|{c}"]["a0.05"] for c in ("C3pm", "C2")}
    p6 = {f"{nl}|{c}": dict(ours=cell_rate(f"A|A1|mall|B1|{nl}|{c}"), target=t,
                           pass_=abs(cell_rate(f"A|A1|mall|B1|{nl}|{c}") - t) <= 0.010)
          for (nl, c), t in P6_TARGET.items()}
    plants_out = dict(P1=p1, P1_pass=all(v["pass_"] for v in p1.values()), P2=dict(r2=r2, pass_=r2 >= 0.30),
                      P5=dict(cells=p5, pass_=all(v["cls"] != "anticonservative" for v in p5.values())), P6=p6,
                      P6_pass=all(v["pass_"] for v in p6.values()), P4_power_at_05=power)
    plants_out["all_must_pass"] = bool(plants_out["P1_pass"] and plants_out["P2"]["pass_"] and
                                       plants_out["P5"]["pass_"] and plants_out["P6_pass"])
    out = dict(entity="ASDG-AUD-E5-regime", spaces=list(spaces), smoke=a.smoke, K=kk, n_maps_per_family=N_MAPS,
               plants=plants_out, cells=cells, regressions=regress,
               moran_q10_50_90={mt: np.quantile(moran[fam == mt], [0.1, 0.5, 0.9]).tolist() for mt in ("B1", "B2")},
               moran_per_map=dict(family=fam.tolist(), moran_i=moran.tolist()),
               set_info=set_info, inputs={str(f): R1.sha256(f) for f in (R1.F_GENE, R1.F_BRAIN, R1.F_SETS)},
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), commit=git("rev-parse", "HEAD"),
               dirty=bool(git("status", "--porcelain")), runtime_s=time.time() - t_start)
    print(json.dumps({k: v for k, v in plants_out.items() if k != "P4_power_at_05"}, indent=1, default=float))
    if a.smoke:
        print("(--smoke: nothing written)")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    (OUT / "regime_A.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    np.savez_compressed(ART / "regime_A_pvals.npz", **{"|".join(k): v for k, v in results.items()})
    if not plants_out["all_must_pass"]:
        raise SystemExit("MUST-PASS PLANT FAILED — readouts are not interpretable; see plants in regime_A.json")


if __name__ == "__main__":
    main()
