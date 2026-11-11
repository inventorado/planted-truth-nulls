"""ASDG-AUD-E3 plants of prereg_amend_3 §4: scenario B (the mirror null) and power there.

Families:
  F-align     y_w = w z(target) + sqrt(1 - w^2) z(field); target in {wmod, grad, mod} (14 set kinds) or brain (8 kinds);
              w in {.5, .9}, PAIRED: plant i's two maps share its generator cell, field, target, sets and every null
              draw (surrogates are drawn per map). Atlas 'dk-ctx' = the cortex-only replica (V-DK left cortex).
  F-align-pc  descriptor (class-step checks): target in {pc1, pc2}; kinds rand-25, clus-25; paired as F-align
  C-align     y = a z(e_S) + .6 z(wmod target) + c z(field); a in {.3, .5, .7} (unpaired); kinds rand-25, fill-100,
              brand-100
Per plant x set kind: naive, S1c, S2c (site leg), G1, G3m, G6s, G6l (species leg; every null set conditioned on S's
between-class part), the verdict and its status (ok / g6l unmatched / g6l degenerate / uninformative / resolution-
limited: every status but ok is a non-rejection, §2), and two reference legs that are NOT valid nulls (§5 planted
legs): G6s-v1 on every plant, the v2 species max on T-brain plants only (its G6l rescores the claim's own v3 windows
unconditioned). Plant i uses generator cell i mod 10. Seeds: SeedSequence([ATLAS_ID, family id, target id, i]) for the
paired maps (C-align: [ATLAS_ID, family id, target id, round(100 * a), i]); + [kind id] for the set and its nulls.

Usage (programme root):
  env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e3_align_plants.py <atlas> <family> <target> <both|a> <n>
      [--jobs 22] [--limit N]
F-align / F-align-pc take 'both' (w = .5 and .9); C-align takes a. Writes one file per w or a:
artifacts/plants_a3/<atlas>_<family>_<target>_<w_or_a>.csv.gz (--limit: code-path test, nothing written).
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse  # noqa: E402
import math  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e3_plants as P  # noqa: E402  (primary_parcels, brain_background, GENERATOR_CELLS, ATLAS_ID, ROOT)
from asdg.spatial import centroid_distance, stratified_surrogates, FieldGenerator  # noqa: E402
from asdg.genesets import Universe  # noqa: E402
from asdg.cascade import corr_matrix, emp_p, naive_p  # noqa: E402
from asdg.species import WithinClassBasis  # noqa: E402
from asdg.modules import class_modules  # noqa: E402

OUT = P.ROOT / "artifacts" / "plants_a3"
N_SURR, K, ALPHA_V = 500, 200, 0.025
ATLAS_ID = {**P.ATLAS_ID, "dk-ctx": 5}
FAM_ID = {"F-align": 11, "F-align-pc": 12, "C-align": 13}
TARGET_ID = {"wmod": 1, "grad": 2, "mod": 3, "pc1": 4, "pc2": 5, "brain": 6}
ALL_KINDS = ["rand-25", "rand-100", "rand-300", "brand-25", "brand-100", "brand-300", "brand-500", "fill-25",
             "fill-100", "fill-300", "clus-25", "clus-100", "multi-500", "multi-1000"]
BRAIN_KINDS = ["rand-100", "rand-300", "brand-25", "brand-100", "brand-300", "brand-500", "multi-500", "fill-100"]
KIND_ID = {k: j for j, k in enumerate(ALL_KINDS)}
PAIRED_WS = (0.5, 0.9)


def kinds_for(family: str, target: str) -> list[str]:
    if family == "F-align":
        return BRAIN_KINDS if target == "brain" else ALL_KINDS
    return ["rand-25", "clus-25"] if family == "F-align-pc" else ["rand-25", "fill-100", "brand-100"]


def z(v):
    v = np.asarray(v, dtype=float)
    return (v - v.mean()) / v.std()


class Ctx:
    def __init__(self, atlas: str):
        base = "dk" if atlas == "dk-ctx" else atlas
        expr, classes, xyz = P.primary_parcels(base)
        if atlas == "dk-ctx":  # cortex-only replica: V-DK left cortex, one tissue class
            keep = np.asarray(classes) == "cortex"
            expr, classes, xyz = expr.loc[keep], np.asarray(classes)[keep], xyz[keep]
        self.atlas, self.classes, self.xyz = atlas, np.asarray(classes), xyz
        self.U = Universe(expr)
        self.X = self.U.X
        self.G = self.X.shape[1]
        self.all = np.arange(self.G)
        self.D = centroid_distance(xyz)
        self.fg = FieldGenerator(xyz, self.classes)
        self.brain = P.brain_background(self.U)
        self.B = WithinClassBasis(self.X, self.classes, brain=self.brain)
        self.other = np.setdiff1d(self.all, self.brain)
        self.mods = class_modules(self.X, base)
        Xc = self.X - self.X.mean(0)
        u, s, _ = np.linalg.svd(Xc, full_matrices=False)
        me = self.X.mean(1)
        self.pcs = [u[:, j] * np.sign(np.corrcoef(u[:, j], me)[0, 1]) for j in (0, 1)]

    def within(self, v):
        return self.B.within_y(v)

    def clusters_ok(self, min_size: int, exclude: int) -> list[int]:
        return [j for j, g in enumerate(self.mods) if len(g) >= min_size and j != exclude]

    def target(self, kind: str, i: int, rng):
        if kind in ("wmod", "mod"):
            ok = self.clusters_ok(25, -1)
            c = int(ok[rng.integers(len(ok))])
            sc = self.X[:, self.mods[c]].mean(1)
            return (self.within(sc) if kind == "wmod" else sc), c
        if kind == "grad":
            return self.within(self.xyz[:, 1] if i % 2 == 0 else self.xyz[:, 2]), -1
        if kind == "brain":
            return self.B.d_B.copy(), -1
        return self.pcs[{"pc1": 0, "pc2": 1}[kind]], -1

    def make_set(self, kind: str, rng, t_cluster: int):
        base, m = kind.split("-")
        m = int(m)
        if base == "rand":
            return rng.choice(self.all, size=m, replace=False), [-1]
        if base == "brand":
            f = round(0.45 * m)
            return np.concatenate([rng.choice(self.brain, size=f, replace=False),
                                   rng.choice(self.other, size=m - f, replace=False)]), [-1]
        if base == "clus":
            ok = self.clusters_ok(m, t_cluster)
            c = int(ok[rng.integers(len(ok))])
            return rng.choice(self.mods[c], size=m, replace=False), [c]
        if base == "fill":
            core_n = math.ceil(m / 5)
            ok = self.clusters_ok(core_n, t_cluster)
            c = int(ok[rng.integers(len(ok))])
            core = rng.choice(self.mods[c], size=core_n, replace=False)
            return np.concatenate([core, rng.choice(np.setdiff1d(self.all, core), size=m - core_n,
                                                    replace=False)]), [c]
        part = m // 4  # multi: equal parts of 4 distinct clusters
        ok = self.clusters_ok(part, t_cluster)
        assert len(ok) >= 4, f"fewer than 4 clusters with >= {part} members"
        cs = [int(x) for x in rng.choice(ok, size=4, replace=False)]
        return np.concatenate([rng.choice(self.mods[c], size=part, replace=False) for c in cs]), cs


def surrogates(ctx: Ctx, y, rng) -> dict:
    return {"S1c": stratified_surrogates(y, ctx.D, ctx.classes, N_SURR, int(rng.integers(2**31)), "brainsmash"),
            "S2c": stratified_surrogates(y, ctx.D, ctx.classes, N_SURR, int(rng.integers(2**31)), "msr")}


def verdict_status(sp: dict, site_floor: float) -> str:
    """§2: a claim that cannot survive — unmatched or degenerate G6l, 'species leg uninformative', or a smallest
    attainable p not below alpha_v (the site leg's floor is 1 / (surrogates + 1)) — is a non-rejection."""
    if sp["g6l_status"] != "ok":
        return f"g6l {sp['g6l_status']}"
    if sp["uninformative"]:
        return "uninformative"
    if sp["resolution_limited"] or site_floor >= ALPHA_V:
        return "resolution-limited"
    return "ok"


def evaluate_many(ctx: Ctx, ys, S, surrs, rng, v2: bool = False) -> list[dict]:
    """Every leg for set S against each map in ys (surrs: each map's S1c / S2c surrogates). The species null draws are
    made once and shared by the maps (species_many)."""
    s = ctx.X[:, S].mean(1)
    sps = ctx.B.species_many(S, ys, K, rng, alpha=ALPHA_V, return_sets=True)
    g6l_sets = sps[0]["g6l_sets"]  # None if unmatched; the v2 draft had no pool-diversity rule, so degenerate pools stay
    common = dict(c_s=ctx.U.mean_coexpr(S), c_s_w=ctx.B.coherence_w(S), brain_frac=float(ctx.B.brain[S].mean()))
    rows = []
    for y, surr, sp in zip(ys, surrs, sps):
        sp.pop("g6l_sets")
        r_obs = corr_matrix(y, s)[0, 0]
        p1c = emp_p(corr_matrix(surr["S1c"], s)[:, 0], r_obs, 1)
        p2c = emp_p(corr_matrix(surr["S2c"], s)[:, 0], r_obs, 1)
        p_naive, p_site = naive_p(r_obs, len(y), 1), max(p1c, p2c)
        status = verdict_status(sp, 1 / (N_SURR + 1))
        rows.append(dict(r=r_obs, **common, p_naive=p_naive, p_S1c=p1c, p_S2c=p2c, p_site=p_site, **sp,
                         verdict_status=status,
                         p_verdict=max(p_naive, p_site, sp["p_species"]) if status == "ok" else np.nan,
                         p_g6s_v1=ctx.B.g6s_v1_flawed(S, y, K, rng),
                         p_v2_species=ctx.B.v2_species(S, y, K, rng, g6l_sets=g6l_sets) if v2 else np.nan))
    return rows


def one_plant(ctx: Ctx, family: str, target: str, was: tuple, i: int) -> list[dict]:
    paired = family in ("F-align", "F-align-pc")
    base = ([ATLAS_ID[ctx.atlas], FAM_ID[family], TARGET_ID[target]] + ([] if paired else [int(round(100 * was[0]))])
            + [i])
    rng = np.random.default_rng(np.random.SeedSequence(base))
    gen, step = P.GENERATOR_CELLS[i % len(P.GENERATOR_CELLS)]
    field = ctx.fg.field(gen, rng, step)
    tgt, t_cluster = ctx.target(target, i, rng)
    head = dict(atlas=ctx.atlas, family=family, target=target, i=i, gen=gen, step=step, target_cluster=t_cluster)
    rows = []
    if paired:
        ys = [w * z(tgt) + math.sqrt(1 - w * w) * z(field) for w in was]
        surrs = [surrogates(ctx, y, rng) for y in ys]
        for kind in kinds_for(family, target):
            r2 = np.random.default_rng(np.random.SeedSequence(base + [KIND_ID[kind]]))
            S, cs = ctx.make_set(kind, r2, t_cluster)
            for w, row in zip(was, evaluate_many(ctx, ys, S, surrs, r2, v2=(target == "brain"))):
                rows.append({**head, "w_or_a": w, "kind": kind, "m": len(S), "set_clusters": ";".join(map(str, cs)),
                             **row})
        return rows
    a = was[0]
    c = math.sqrt(1 - a * a - 0.36)  # C-align
    for kind in kinds_for(family, target):
        r2 = np.random.default_rng(np.random.SeedSequence(base + [KIND_ID[kind]]))
        S, cs = ctx.make_set(kind, r2, t_cluster)
        s_w = ctx.B.Xw[:, S].mean(1) - ctx.B.mu_S(S)  # the S-specific within-class part
        U3 = ctx.B.U[:, :3]
        e_s = s_w - U3 @ (U3.T @ s_w)
        y = a * z(e_s) + 0.6 * z(tgt) + c * z(field)
        surr = surrogates(ctx, y, r2)
        rows.append({**head, "w_or_a": a, "kind": kind, "m": len(S), "set_clusters": ";".join(map(str, cs)),
                     **evaluate_many(ctx, [y], S, [surr], r2)[0]})
    return rows


def out_path(atlas, family, target, wa) -> Path:
    return OUT / f"{atlas}_{family}_{target}_{wa:g}.csv.gz"


def main():
    from joblib import Parallel, delayed

    ap = argparse.ArgumentParser()
    ap.add_argument("atlas", choices=["aal", "dk", "cc200", "dk-ctx"])
    ap.add_argument("family", choices=list(FAM_ID))
    ap.add_argument("target", choices=list(TARGET_ID))
    ap.add_argument("w_or_a", help="'both' (F-align, F-align-pc: paired w = .5, .9) or a (C-align)")
    ap.add_argument("n", type=int)
    ap.add_argument("--jobs", type=int, default=22)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    paired = a.family in ("F-align", "F-align-pc")
    if paired != (a.w_or_a == "both"):
        raise SystemExit("F-align / F-align-pc take 'both'; C-align takes a")
    was = PAIRED_WS if paired else (float(a.w_or_a),)
    t0 = time.time()
    ctx = Ctx(a.atlas)
    n = a.limit or a.n

    def work(i):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return one_plant(ctx, a.family, a.target, was, i)

    rows = [r for rs in Parallel(n_jobs=a.jobs, backend="loky", batch_size=1)(delayed(work)(i) for i in range(n))
            for r in rs]
    df = pd.DataFrame(rows)
    tag = f"{a.atlas}_{a.family}_{a.target}_{a.w_or_a}"
    print(f"{tag}: plants={n} rows={len(df)} parcels={len(ctx.classes)} clusters={len(ctx.mods)} "
          f"brain={len(ctx.brain)} {time.time() - t0:.0f}s", flush=True)
    if a.limit:
        print(df.groupby("kind")[["m", "c_s_w", "brain_frac", "g6l_n", "g6l_draws", "g6l_pool_jaccard"]].mean()
              .round(3).to_string())
        print(df["verdict_status"].value_counts().to_string())
        print("(--limit: code-path test, nothing written)")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    for wa, part in df.groupby("w_or_a"):
        out = out_path(a.atlas, a.family, a.target, wa)
        part.to_csv(out, index=False)
        assert len(pd.read_csv(out)) == len(part) == n * len(kinds_for(a.family, a.target)), "read-back mismatch"


if __name__ == "__main__":
    main()
