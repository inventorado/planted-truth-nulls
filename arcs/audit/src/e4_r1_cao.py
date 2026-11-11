"""ASDG-AUD-E4-apparatus, reproduction R1 (prereg §3.3): Cao et al. 2024 (cao2024unraveling), Main + S5 + S17.

Re-implements Cao's four nulls for the Mean and Meanabs statistics on the authors' shipped inputs
(Desikan LH 34 regions x 6,513 genes; 1,000 simulated maps, Moran's I ~0.03; 500 random gene sets) and
compares per-test p-values with the authors' shipped result CSVs.

Definitions (Cao's code, functions/*.R; prereg §3.3):
  z = Fisher z of the Pearson r between the map and each gene over the 34 regions;
  Mean = mean z over the set, Meanabs = mean |z|;
  p = (#{|null| >= |obs|} + 1) / (n + 1)  (prereg formula; the shipped CSVs use #/(n+1), recorded as a descriptor);
  competitive = permute the labels of the whole gene list (resampling_geneList), 5,000 permutations;
  spin        = Cao's shipped permutation ids (first 5,000 columns), y_null[r] = y[perm[r]];
  coexp       = Cao's rejection sampler (sample_gs_matching_coexp: uniform same-size set from all 6,513 genes,
                accept iff |mean pairwise coexpression - target| < 0.01, unique sets, stop at 5,000 accepted
                or 1e6 draws), null stat = statistic of the sampled set's z (swap_geneList);
  joint       = spin ids + an independent gene-label permutation of each spun column (spin_random_mixed).
Stated deviation (prereg): random draws (competitive permutations, joint permutations, coexp sets) are shared
across the 1,000 maps (Cao draws competitive/joint permutations per map; his coexp sets are shared across maps).
Descriptor: our G2 sampler (asdg.genesets.coexpr_matched_sets, tol 0.01, exclude = the set) on the same tests.

Usage: env\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e4_r1_cao.py [--smoke] [--jobs N] [--g2-maps all|N]
Writes arcs/audit/results/e4_r1_cao.json and artifacts/r1_cao/*.npz (per-test counts / p-values).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import rdata
import scipy.sparse as sp
from joblib import Parallel, delayed
from scipy import stats

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from asdg.genesets import Universe, coexpr_matched_sets  # noqa: E402

CAO = Path("E:/data/asdg/cao2024/repo/2024_NI_Imaging_Transcriptomics")
F_GENE = CAO / "data/GeneExp/desikan_r0.4.csv"
F_BRAIN = CAO / "data/BrainDat/desikan_sim_spatial0.03.csv"
F_SETS = CAO / "data/GeneSets/desikan_r0.4_Sim.rds"
F_PERM = CAO / "data/BrainInfo/perm_id_weights/desikan_spin_brain_perm_id.rds"
NULLS = ["competitive", "spin", "coexp", "joint"]
F_REF = {
    "competitive": CAO / "results/Res_desikan_r0.4_sim_spatial0.03_Sim_random_gene_pearson_sim1000.csv",
    "spin": CAO / "results/Res_desikan_r0.4_sim_spatial0.03_Sim_spin_brain_pearson_sim1000.csv",
    "coexp": CAO / "results/Res_desikan_r0.4_sim_spatial0.03_Sim_random_gene_coexp_pearson_sim1000.csv",
    "joint": CAO / "results/Res_desikan_r0.4_sim_spatial0.03_Sim_spin_random_mixed_pearson_sim1000.csv",
}
FIG_READ = {  # note literature/notes/cao2024unraveling.md §D, read off figure
    "competitive": (0.053, 0.049), "spin": (0.061, 0.096), "coexp": (0.049, 0.049), "joint": (0.069, 0.093)}
STATS = ["mean", "meanabs"]
SEEDS = {"competitive": 202609231, "joint": 202609232, "coexp": 202609233, "g2": 202609234, "g2_subset": 202609235}
ALPHA = 0.05
OUT_JSON = ROOT / "arcs/audit/results/e4_r1_cao.json"
ART = ROOT / "artifacts/r1_cao"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ----------------------------------------------------------------------------------------------- loading
def load_inputs():
    g = pd.read_csv(F_GENE)
    g = g[g["Region"].str.match(r"^L_")]                   # load_GeneExp(hem='L')
    g = g[g.notna().all(axis=1)].set_index("Region")         # complete.cases
    b = pd.read_csv(F_BRAIN, index_col=0)
    assert g.shape == (34, 6513), g.shape
    assert b.shape == (34, 1000), b.shape
    assert list(g.index) == list(b.index), "region order of gene and brain data differ"  # corr_brain_gene check
    assert list(b.columns) == [f"sim_{i}" for i in range(1, 1001)]
    assert g.columns.is_unique
    # Cao's R read.csv(check.names=TRUE) turns e.g. 'HLA-C' into 'HLA.C'; the shipped gene sets use R names
    rn = [re.sub(r"[^A-Za-z0-9._]", ".", x) for x in g.columns]
    rn = ["X" + x if re.match(r"^([0-9]|\.[0-9])", x) else x for x in rn]
    assert len(set(rn)) == len(rn), "R make.names collision"
    g.columns = rn
    sets = rdata.read_rds(F_SETS)
    assert len(sets) == 500
    names = [str(k) for k in sets]
    gidx = {x: i for i, x in enumerate(g.columns)}
    set_idx = []
    for k in sets:
        genes = [str(x) for x in sets[k]]
        assert len(set(genes)) == len(genes), f"duplicate genes in {k}"
        missing = [x for x in genes if x not in gidx]
        assert not missing, f"{k}: {len(missing)} genes absent from the 6,513"
        set_idx.append(np.array(sorted(gidx[x] for x in genes), dtype=np.int64))
    sizes = np.array([len(s) for s in set_idx])
    assert sorted(set(sizes.tolist())) == list(range(20, 201, 20)) and all((sizes == m).sum() == 50 for m in range(20, 201, 20))
    perm = np.asarray(rdata.read_rds(F_PERM))
    assert perm.shape == (34, 10000), perm.shape
    perm = perm[:, :5000].astype(np.int64) - 1                # load_permid: first 5,000; R is 1-based
    assert (np.sort(perm, axis=0) == np.arange(34)[:, None]).all(), "a spin column is not a permutation"
    assert not (perm == np.arange(34)[:, None]).all(axis=0).any(), "identity permutation among spin ids"
    return g, b, names, set_idx, sizes, perm


def load_reference(names):
    """Returns {null: {stat: (500 sets x 1000 maps) array}} in rds set order and map order 1..1000."""
    out = {}
    for nl, f in F_REF.items():
        d = pd.read_csv(f, usecols=["geneSet", "sim_brain", "pvals.mean", "pvals.meanabs"])
        assert len(d) == 500_000 and d["sim_brain"].nunique() == 1000 and d["geneSet"].nunique() == 500
        assert not d.isna().any().any()
        out[nl] = {}
        for s in STATS:
            w = d.pivot(index="geneSet", columns="sim_brain", values=f"pvals.{s}")
            w = w.loc[names, list(range(1, 1001))]
            out[nl][s] = w.to_numpy(dtype=float)
    return out


def unit_cols(M):
    Mc = M - M.mean(0)
    return Mc / np.sqrt((Mc ** 2).sum(0))


def fisher_z(r):
    return np.arctanh(np.clip(r, -1 + 1e-15, 1 - 1e-15))


def set_matrix(set_list, n_genes):
    """Sparse (k x genes) with 1/m on members, so A @ z = mean of z over each set."""
    rows = np.concatenate([np.full(len(s), i) for i, s in enumerate(set_list)])
    cols = np.concatenate(set_list)
    vals = np.concatenate([np.full(len(s), 1.0 / len(s)) for s in set_list])
    return sp.csr_matrix((vals, (rows, cols)), shape=(len(set_list), n_genes))


# ------------------------------------------------------------------------------------------- null workers
def comp_worker(Zobs, absZ, A, obs_m, obs_a, perms):
    cm = np.zeros(obs_m.shape, np.int32)
    ca = np.zeros(obs_m.shape, np.int32)
    tm, ta = np.abs(obs_m), np.abs(obs_a)
    for p in perms:
        # (A @ Zobs[p])[s] = sum_g A[s, g] Zobs[p[g]]: relabel A's columns instead of gathering Zobs
        Ap = sp.csr_matrix((A.data, p[A.indices], A.indptr), shape=A.shape)
        cm += np.abs(Ap @ Zobs) >= tm
        ca += np.abs(Ap @ absZ) >= ta
    return cm, ca


def spin_joint_worker(Xu, Y, A, obs_m, obs_a, spin, P2T, maps, chunk):
    """For each map: spun maps -> z for all genes; spin null = set stats of z; joint null = set stats of
    z after an independent gene-label permutation of each spun column (P2T[:, k])."""
    k_all = spin.shape[1]
    res = []
    for i in maps:
        yn = Y[:, i][spin]                                      # (34, n_null): y_null[r] = y[perm[r]]
        Yu = unit_cols(yn)
        tm, ta = np.abs(obs_m[:, i])[:, None], np.abs(obs_a[:, i])[:, None]
        c = np.zeros((4, A.shape[0]), np.int32)
        for c0 in range(0, k_all, chunk):
            c1 = min(c0 + chunk, k_all)
            Z = fisher_z(Xu.T @ Yu[:, c0:c1])                   # (genes, kc)
            c[0] += (np.abs(A @ Z) >= tm).sum(1)
            c[1] += (np.abs(A @ np.abs(Z)) >= ta).sum(1)
            Zp = np.take_along_axis(Z, P2T[:, c0:c1], axis=0)
            c[2] += (np.abs(A @ Zp) >= tm).sum(1)
            c[3] += (np.abs(A @ np.abs(Zp)) >= ta).sum(1)
        res.append(c)
    return maps, np.stack(res)


def draw_distinct(rng, n, m, B):
    """B uniform m-subsets of range(n) (as rows, each a uniformly ordered distinct tuple)."""
    acc = np.exp(-m * (m - 1) / (2 * n))
    if acc > 0.25:  # i.i.d. with replacement, conditioned on distinctness (exactly uniform)
        out = []
        need = B
        while need > 0:
            S = rng.integers(0, n, size=(int(need / acc * 1.1) + 16, m))
            Ss = np.sort(S, axis=1)
            ok = ~(Ss[:, 1:] == Ss[:, :-1]).any(axis=1)
            S = S[ok][:need]
            out.append(S)
            need -= len(S)
        return np.concatenate(out)
    keys = rng.random((B, n), dtype=np.float32)
    return np.argpartition(keys, m, axis=1)[:, :m]


def cao_sampler(ZT, m, target, rng, tol=0.01, max_iter=1_000_000, n_target=5000, batch=4096):
    """sample_gs_matching_coexp, draw by draw: accept iff |coexp - target| < tol, unique sets, stop at
    n_target accepted or max_iter draws (batches are consumed in draw order and truncated exactly)."""
    accepted, acc_c, seen = [], [], set()
    draws = 0
    while draws < max_iter and len(accepted) < n_target:
        B = min(batch, max_iter - draws)
        S = draw_distinct(rng, ZT.shape[0], m, B)
        v = ZT[S].sum(axis=1)
        c = (np.einsum("ij,ij->i", v, v) - m) / (m * (m - 1))
        hit = np.flatnonzero(np.abs(c - target) < tol)
        used = B
        for b in hit:
            key = np.sort(S[b]).tobytes()
            if key in seen:
                continue
            seen.add(key)
            accepted.append(S[b].copy())
            acc_c.append(c[b])
            if len(accepted) == n_target:
                used = b + 1
                break
        draws += used
    return (np.stack(accepted) if accepted else np.zeros((0, m), int)), np.array(acc_c), draws


def matched_null_counts(sets, Zobs, absZ, obs_m_row, obs_a_row):
    B = set_matrix(list(sets), Zobs.shape[0])
    cm = (np.abs(B @ Zobs) >= np.abs(obs_m_row)[None, :]).sum(0).astype(np.int32)
    ca = (np.abs(B @ absZ) >= np.abs(obs_a_row)[None, :]).sum(0).astype(np.int32)
    return cm, ca


def coexp_worker(j, s, ZT, Zobs, absZ, obs_m_row, obs_a_row, target, seed, n_target, max_iter):
    rng = np.random.default_rng(np.random.SeedSequence([seed, j]))
    t0 = time.time()
    sets, ach, draws = cao_sampler(ZT, len(s), target, rng, n_target=n_target, max_iter=max_iter)
    cm, ca = matched_null_counts(sets, Zobs, absZ, obs_m_row, obs_a_row)
    return j, cm, ca, dict(n_null=len(sets), draws=int(draws), reached=len(sets) == n_target,
                           ach_mean=float(ach.mean()) if len(ach) else None,
                           ach_min=float(ach.min()) if len(ach) else None,
                           ach_max=float(ach.max()) if len(ach) else None, seconds=time.time() - t0)


def g2_worker(j, s, U, Zobs, absZ, obs_m_row, obs_a_row, target, seed, k):
    rng = np.random.default_rng(np.random.SeedSequence([seed, j]))
    t0 = time.time()
    sets, info = coexpr_matched_sets(U, np.arange(len(U.genes)), len(s), target, k, rng, tol=0.01, exclude=s)
    if sets is None:
        return j, None, None, {**{kk: (float(v) if isinstance(v, (float, np.floating)) else v)
                                  for kk, v in info.items() if kk != "sub_bin"}, "n_null": 0,
                               "seconds": time.time() - t0}
    assert not np.isin(sets, s).any(), "G2 set contains a member of S despite exclude"
    cm, ca = matched_null_counts(sets, Zobs, absZ, obs_m_row, obs_a_row)
    return j, cm, ca, {**info, "n_null": len(sets), "seconds": time.time() - t0}


# ------------------------------------------------------------------------------------------------- main
def psig(p):
    return float((p < ALPHA).mean())


def r2_psigG(p, coexp):
    y = (p < ALPHA).mean(axis=1)
    if y.std() == 0:
        return 0.0
    return float(stats.linregress(coexp, y).rvalue ** 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--jobs", type=int, default=22)
    ap.add_argument("--g2-maps", default="all")
    ap.add_argument("--skip-g2", action="store_true")
    a = ap.parse_args()
    T0 = time.time()
    timing = {}
    n_null = 500 if a.smoke else 5000
    n_maps = 24 if a.smoke else 1000
    coexp_max_iter = 100_000 if a.smoke else 1_000_000
    n_sets_run = 500

    g, b, names, set_idx, sizes, spin = load_inputs()
    ref = load_reference(names)

    # 1. read-check (prereg: reference Psig vs figure-read values, +-0.005; stop on failure)
    readcheck = {}
    for nl in NULLS:
        for si, s in enumerate(STATS):
            v = psig(ref[nl][s])
            readcheck[f"{nl}/{s}"] = dict(ref_psig=v, figure_read=FIG_READ[nl][si],
                                          abs_diff=abs(v - FIG_READ[nl][si]),
                                          pass_=abs(v - FIG_READ[nl][si]) <= 0.005)
    readcheck_pass = all(r["pass_"] for r in readcheck.values())
    print("read-check", "PASS" if readcheck_pass else "FAIL")
    for k, r in readcheck.items():
        print(f"  {k:22s} ref {r['ref_psig']:.4f} fig {r['figure_read']:.3f} {'ok' if r['pass_'] else 'FAIL'}")
    if not readcheck_pass:
        OUT_JSON.write_text(json.dumps(dict(readcheck=readcheck, readcheck_pass=False, R1_pass=False,
                                            note="read-check failed; nothing else run"), indent=1), encoding="utf-8")
        return

    # 2. observed z
    X = g.to_numpy(float)
    Y = b.to_numpy(float)[:, :n_maps]
    Xu = unit_cols(X)
    Zobs = fisher_z(Xu.T @ unit_cols(Y))                       # (6513, maps)
    # apparatus: one gene x one map against scipy
    r_chk = stats.pearsonr(X[:, 17], Y[:, 3]).statistic
    assert abs(np.arctanh(r_chk) - Zobs[17, 3]) < 1e-10
    absZ = np.abs(Zobs)
    A = set_matrix(set_idx, X.shape[1])
    obs_m, obs_a = A @ Zobs, A @ absZ                          # (500, maps)
    assert abs(obs_m[5, 2] - Zobs[set_idx[5], 2].mean()) < 1e-12
    assert abs(obs_a[5, 2] - np.abs(Zobs[set_idx[5], 2]).mean()) < 1e-12
    U = Universe(g)
    assert U.n_dropped_constant == 0 and list(U.genes) == list(g.columns)
    ZT = np.ascontiguousarray(U.Z.T)                           # (genes, 34), rows unit-norm: coexp = dot
    coexp = np.array([U.mean_coexpr(s) for s in set_idx])
    C_chk = np.corrcoef(X[:, set_idx[0]].T)
    assert abs(C_chk[np.tril_indices(20, -1)].mean() - coexp[0]) < 1e-12   # = mean(lower.tri(cor(gene_data)))

    counts = {}
    nnull = {}
    # 3. competitive
    t = time.time()
    rng = np.random.default_rng(SEEDS["competitive"])
    P1 = rng.permuted(np.tile(np.arange(X.shape[1], dtype=np.int32), (n_null, 1)), axis=1)
    assert len(np.unique(P1, axis=0)) == n_null                # resampling_geneList drops duplicate permutations
    chunks = np.array_split(np.arange(n_null), a.jobs * 4)
    out = Parallel(n_jobs=a.jobs)(delayed(comp_worker)(Zobs, absZ, A, obs_m, obs_a, P1[c]) for c in chunks)
    counts["competitive"] = {"mean": sum(o[0] for o in out), "meanabs": sum(o[1] for o in out)}
    nnull["competitive"] = np.full(500, n_null)
    del P1
    timing["competitive_s"] = time.time() - t
    print(f"competitive done {timing['competitive_s']:.0f}s", flush=True)

    # 4. spin + joint
    t = time.time()
    sp_ids = spin[:, :n_null]
    rng = np.random.default_rng(SEEDS["joint"])
    P2T = np.ascontiguousarray(
        rng.permuted(np.tile(np.arange(X.shape[1], dtype=np.int32), (n_null, 1)), axis=1).T)  # (genes, n_null)
    mchunks = np.array_split(np.arange(n_maps), min(n_maps, a.jobs * 4))
    out = Parallel(n_jobs=min(a.jobs, 16))(
        delayed(spin_joint_worker)(Xu, Y, A, obs_m, obs_a, sp_ids, P2T, mc, 1000) for mc in mchunks)
    c4 = np.zeros((4, 500, n_maps), np.int32)
    for maps, c in out:
        c4[:, :, maps] = np.transpose(c, (1, 2, 0))
    counts["spin"] = {"mean": c4[0], "meanabs": c4[1]}
    counts["joint"] = {"mean": c4[2], "meanabs": c4[3]}
    nnull["spin"] = nnull["joint"] = np.full(500, n_null)
    del P2T
    timing["spin_joint_s"] = time.time() - t
    print(f"spin+joint done {timing['spin_joint_s']:.0f}s", flush=True)

    # 5. coexp-matched (Cao's sampler), sets shared across maps (as in Cao)
    t = time.time()
    out = Parallel(n_jobs=a.jobs)(
        delayed(coexp_worker)(j, set_idx[j], ZT, Zobs, absZ, obs_m[j], obs_a[j], coexp[j], SEEDS["coexp"],
                              n_null, coexp_max_iter) for j in range(n_sets_run))
    cm = np.zeros((500, n_maps), np.int32); ca = np.zeros((500, n_maps), np.int32)
    coexp_info = [None] * 500
    for j, x, y, info in out:
        cm[j], ca[j], coexp_info[j] = x, y, info
    counts["coexp"] = {"mean": cm, "meanabs": ca}
    nnull["coexp"] = np.array([ci["n_null"] for ci in coexp_info])
    timing["coexp_s"] = time.time() - t
    print(f"coexp done {timing['coexp_s']:.0f}s; sets not reaching target: {int((nnull['coexp'] < n_null).sum())}",
          flush=True)

    # p-values (prereg formula) and reference-formula descriptor
    P = {nl: {s: (counts[nl][s] + 1) / (nnull[nl][:, None] + 1) for s in STATS} for nl in NULLS}
    P_refform = {nl: {s: counts[nl][s] / (nnull[nl][:, None] + 1) for s in STATS} for nl in NULLS}
    R = {nl: {s: ref[nl][s][:, :n_maps] for s in STATS} for nl in NULLS}

    # 6. criteria
    cells = {}
    for nl in NULLS:
        for s in STATS:
            po, pr = P[nl][s], R[nl][s]
            d = dict(ref_psig=psig(pr), ours_psig=psig(po), ours_psig_refformula=psig(P_refform[nl][s]))
            d["abs_diff"] = abs(d["ours_psig"] - d["ref_psig"])
            d["psig_pass"] = d["abs_diff"] <= 0.010
            d["spearman"] = float(stats.spearmanr(po.ravel(), pr.ravel()).statistic)
            pbar = (po + pr) / 2
            band = 3 * np.sqrt(2 * pbar * (1 - pbar) / 5000)
            d["frac_within_band"] = float((np.abs(po - pr) <= band).mean())
            d["r2_psigG_coexp_ours"] = r2_psigG(po, coexp)
            d["r2_psigG_coexp_ref"] = r2_psigG(pr, coexp)
            if nl in ("competitive", "spin"):
                thr = 0.99 if nl == "spin" else 0.95
                d["spearman_threshold"] = thr
                d["spearman_pass"] = d["spearman"] >= thr
                d["band_pass"] = d["frac_within_band"] >= 0.95
                d["cell_pass"] = d["psig_pass"] and d["spearman_pass"] and d["band_pass"]
            else:
                d["spearman_threshold"] = None
                d["note"] = "per-test Spearman/band are descriptors only for this cell (prereg)"
                d["cell_pass"] = d["psig_pass"]
            cells[f"{nl}/{s}"] = d
    r2o, r2r = cells["competitive/mean"]["r2_psigG_coexp_ours"], cells["competitive/mean"]["r2_psigG_coexp_ref"]
    r2_clause = dict(r2_ours=r2o, r2_ref=r2r, abs_diff_pp=100 * abs(r2o - r2r), pass_=abs(r2o - r2r) <= 0.05)
    R1_pass = all(c["cell_pass"] for c in cells.values()) and r2_clause["pass_"]
    for k, c in cells.items():
        print(f"  {k:22s} ref {c['ref_psig']:.4f} ours {c['ours_psig']:.4f} |d| {c['abs_diff']:.4f} "
              f"rho {c['spearman']:.4f} band {c['frac_within_band']:.4f} {'PASS' if c['cell_pass'] else 'FAIL'}")
    print(f"  R2 competitive/mean ours {r2o:.4f} ref {r2r:.4f} -> {'PASS' if r2_clause['pass_'] else 'FAIL'}")
    print("R1", "PASS" if R1_pass else "FAIL", flush=True)

    # reference coexp sets with a non-5,000 null count (p off the k/5001 lattice)
    k = ref["coexp"]["mean"] * 5001
    ref_offlattice = [names[j] for j in np.flatnonzero((np.abs(k - np.round(k)) > 1e-6).any(axis=1))]

    # 7. our G2 sampler, descriptor
    g2 = None
    if not a.skip_g2:
        t = time.time()
        if a.g2_maps == "all":
            g2_maps = np.arange(n_maps)
        else:
            g2_maps = np.sort(np.random.default_rng(SEEDS["g2_subset"]).choice(n_maps, int(a.g2_maps), replace=False))
        Zs, As = Zobs[:, g2_maps], absZ[:, g2_maps]
        out = Parallel(n_jobs=a.jobs)(
            delayed(g2_worker)(j, set_idx[j], U, Zs, As, obs_m[j, g2_maps], obs_a[j, g2_maps], coexp[j],
                               SEEDS["g2"], n_null) for j in range(n_sets_run))
        gm = np.full((500, len(g2_maps)), -1, np.int32); ga = gm.copy(); g2_info = [None] * 500
        for j, x, y, info in out:
            g2_info[j] = {kk: (float(v) if isinstance(v, (np.floating,)) else v) for kk, v in info.items()}
            if x is not None:
                gm[j], ga[j] = x, y
        g2_n = np.array([gi["n_null"] for gi in g2_info])
        ok = g2_n > 0
        pg = {"mean": (gm[ok] + 1) / (g2_n[ok, None] + 1), "meanabs": (ga[ok] + 1) / (g2_n[ok, None] + 1)}
        g2 = dict(maps="all" if a.g2_maps == "all" else f"random subset of {len(g2_maps)} (seed {SEEDS['g2_subset']})",
                  n_maps=int(len(g2_maps)), n_sets_matched=int(ok.sum()),
                  unmatched_sets=[names[j] for j in np.flatnonzero(~ok)],
                  psig={s: psig(pg[s]) for s in STATS},
                  cao_coexp_psig_same_tests={s: psig(P["coexp"][s][ok][:, g2_maps]) for s in STATS},
                  ref_coexp_psig_same_tests={s: psig(R["coexp"][s][ok][:, g2_maps]) for s in STATS},
                  r2_psigG_coexp={s: r2_psigG(pg[s], coexp[ok]) for s in STATS},
                  achieved_coexp_minus_target_mean=float(np.mean([g2_info[j]["achieved_mean"] - coexp[j]
                                                                  for j in np.flatnonzero(ok)])),
                  seconds=time.time() - t)
        timing["g2_s"] = g2["seconds"]
        print(f"G2 descriptor Psig mean {g2['psig']['mean']:.4f} meanabs {g2['psig']['meanabs']:.4f} "
              f"({timing['g2_s']:.0f}s)", flush=True)

    # 8. write artifacts + json
    ART.mkdir(parents=True, exist_ok=True)
    tag = "_smoke" if a.smoke else ""
    npz = ART / f"r1_cao_pertest{tag}.npz"
    arrs = {f"p_ours_{nl}_{s}": P[nl][s].astype(np.float32) for nl in NULLS for s in STATS}
    arrs.update({f"count_{nl}_{s}": counts[nl][s] for nl in NULLS for s in STATS})
    arrs.update({f"nnull_{nl}": nnull[nl] for nl in NULLS})
    arrs["set_names"] = np.array(names); arrs["set_coexp"] = coexp; arrs["set_size"] = sizes
    if g2 is not None:
        arrs.update(g2_count_mean=gm, g2_count_meanabs=ga, g2_nnull=g2_n, g2_maps=g2_maps)
    np.savez_compressed(npz, **arrs)
    with np.load(npz) as chk:                                   # read back
        for kk, v in arrs.items():
            assert np.array_equal(chk[kk], v), f"npz read-back mismatch {kk}"

    script = Path(__file__).resolve()
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", str(script)],
                           capture_output=True, text=True).stdout.strip()
    res = dict(
        entity="ASDG-AUD-E4-apparatus", reproduction="R1 Cao 2024 (cao2024unraveling), prereg §3.3",
        smoke=a.smoke, n_maps=n_maps, n_sets=500, n_null=n_null,
        readcheck=readcheck, readcheck_pass=readcheck_pass,
        cells=cells, r2_clause_competitive_mean=r2_clause, R1_pass=R1_pass if not a.smoke else None,
        coexp_sampler=dict(
            sets_not_reaching_5000=[dict(set=names[j], n_null=coexp_info[j]["n_null"], draws=coexp_info[j]["draws"])
                                    for j in range(500) if not coexp_info[j]["reached"]],
            ref_sets_off_5001_lattice=ref_offlattice,
            median_draws=float(np.median([ci["draws"] for ci in coexp_info])),
            max_abs_achieved_minus_target=float(max(max(abs(ci["ach_min"] - coexp[j]), abs(ci["ach_max"] - coexp[j]))
                                                    for j, ci in enumerate(coexp_info) if ci["n_null"]))),
        g2_descriptor=g2,
        deviations=[
            "random draws shared across maps (competitive and joint permutations; coexp sets are shared in Cao too)",
            "p = (k+1)/(n+1) per prereg; the shipped reference CSVs use k/(n+1) (p=0 occurs, max 5000/5001); "
            "ours_psig_refformula reports Psig with the reference formula",
            "coexp sampler draws uniform same-size sets exactly but not with R's RNG stream; uniqueness by sorted set",
        ],
        seeds=SEEDS, runtime_s=time.time() - T0, timing=timing,
        script=str(script.relative_to(ROOT)).replace("\\", "/"), script_sha256=sha256(script),
        script_uncommitted=bool(dirty),
        inputs={str(p.relative_to(CAO)).replace("\\", "/"): sha256(p) for p in [F_GENE, F_BRAIN, F_SETS, F_PERM, *F_REF.values()]},
        cao_repo=str(CAO), git_head=head, artifacts=str(npz.relative_to(ROOT)).replace("\\", "/"),
        python=sys.version.split()[0], numpy=np.__version__, pandas=pd.__version__,
    )
    out_json = OUT_JSON if not a.smoke else ART / "e4_r1_cao_smoke.json"
    txt = json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    out_json.write_text(txt, encoding="utf-8", newline="\n")
    assert json.loads(out_json.read_text(encoding="utf-8"))["cells"].keys() == cells.keys()   # read back
    print("wrote", out_json, f"runtime {res['runtime_s']:.0f}s")


if __name__ == "__main__":
    main()
