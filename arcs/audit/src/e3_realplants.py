"""ASDG-AUD-E3-plants, real-data plants on Wei 2022's own inputs (prereg §6.4): P+2 (HSE x nodal strength) and
C1 (APOE x Alzheimer's VBM ALE map). DK-114 left cortex, 57 parcels, GAMBA bundle.

Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e3_realplants.py
Writes arcs/audit/results/e3_realplants.json.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from asdg.spatial import centroid_distance, brainsmash_surrogates, MoranSpectral  # noqa: E402
from asdg.genesets import Universe, random_sets, coexpr_matched_sets, Trajectories, trajectory_matched_sets  # noqa: E402
from asdg.cascade import corr_matrix, emp_p, naive_p, joint_j1  # noqa: E402
from asdg.brainspan import load_trajectories  # noqa: E402

G = Path("E:/data/asdg/gamba_matlab_data/dropbox/GAMBA_MATLAB_DATA")
GAMBA_CSV = Path("E:/data/asdg/gamba/Background_genes_null_brain.csv")
RES = ROOT / "arcs" / "audit" / "results"
N = 10000          # G1, G3, S1, S2 (audit-level counts)
N_MATCH = 2000     # G2, G4, G5, J1 pool (sampler-bound; stated in results)
SEED = 20260923


def cellstr(a):
    return [str(x[0][0]) if np.size(x[0]) else "" for x in a.ravel().reshape(-1, 1)]


def mat_strings(v) -> list[str]:
    return [str(np.squeeze(x)) for x in np.asarray(v).ravel()]


def zs(v):
    return (v - np.nanmean(v)) / np.nanstd(v, ddof=1)


def gamba_beta(expr: np.ndarray, symbols: list[str], geneset, y) -> float:
    """Wei/GAMBA: X = nanmean over set genes per region, both standardised; beta = OLS slope."""
    ii = np.isin(symbols, list(geneset))
    X = zs(np.nanmean(expr[:, ii], axis=1))
    Y = zs(y)
    ok = np.isfinite(X) & np.isfinite(Y)
    return float(np.polyfit(X[ok], Y[ok], 1)[0])


def dk114_centroids(names: list[str]) -> np.ndarray:
    img = nib.load(G / "atlas" / "atlas" / "lausanne120+aseg.nii.gz")
    lut = pd.read_csv(G / "atlas" / "atlas" / "lausanne120.txt", sep=r"\s+", header=None, comment="#")
    lut = dict(zip(lut[1].astype(str), lut[0].astype(int)))
    d = np.asarray(img.dataobj).astype(int)
    xyz = []
    for n in names:
        vox = np.argwhere(d == lut[n])
        assert len(vox), n
        xyz.append(nib.affines.apply_affine(img.affine, vox).mean(0))
    return np.array(xyz)


def parcel_means(nifti: Path, names: list[str]) -> np.ndarray:
    from nilearn.image import resample_to_img

    ref = nib.load(G / "atlas" / "atlas" / "lausanne120+aseg.nii.gz")
    img = resample_to_img(nib.load(nifti), ref, interpolation="continuous", force_resample=True, copy_header=True)
    v = np.asarray(img.dataobj)
    d = np.asarray(ref.dataobj).astype(int)
    lut = pd.read_csv(G / "atlas" / "atlas" / "lausanne120.txt", sep=r"\s+", header=None, comment="#")
    lut = dict(zip(lut[1].astype(str), lut[0].astype(int)))
    return np.array([v[d == lut[n]].mean() for n in names])


def wei_spin_scores(genes: list[str]) -> np.ndarray | None:
    """S3 for the DK-114 cortex: Wei's own spun expression files (1,000 rotations x 57), set mean."""
    base = G / "gene_expression_spin"
    files = [next(base.rglob(f"GE_spin_{g}.txt"), None) for g in genes]
    files = [f for f in files if f is not None]
    if not files:
        return None
    arr = np.stack([np.loadtxt(f, delimiter=",") for f in files])  # genes x 1000 x 57
    return np.nanmean(arr, axis=0)


def cascade_on(y, S, U, brain, tr, D, ms, rng, single=False, spin_scores=None) -> dict:
    score = U.scores(S)[0]
    r = corr_matrix(y, score)[0, 0]
    sign = 1
    out = dict(r=r, p_naive=naive_p(r, len(y), sign))
    s1 = brainsmash_surrogates(y, D, N, int(rng.integers(2**31)))
    s2 = ms.surrogates(y, N, int(rng.integers(2**31)))
    out["p_S1"] = emp_p(corr_matrix(s1, score)[:, 0], r, sign)
    out["p_S2"] = emp_p(corr_matrix(s2, score)[:, 0], r, sign)
    out["p_L1_joint"] = max(out["p_S1"], out["p_S2"])
    if spin_scores is not None:
        out["p_S3_wei_spin"] = emp_p(corr_matrix(y, spin_scores)[0], r, sign)
    m = len(S)
    out["p_G1"] = emp_p(corr_matrix(y, U.scores(random_sets(np.arange(len(U.genes)), m, N, rng, exclude=S)))[0], r, sign)
    out["p_G3"] = emp_p(corr_matrix(y, U.scores(random_sets(brain, m, N, rng, exclude=S)))[0], r, sign)
    if single:
        return out
    c = U.mean_coexpr(S)
    G2, i2 = coexpr_matched_sets(U, np.arange(len(U.genes)), m, c, N_MATCH, rng, exclude=S)
    G4, i4 = coexpr_matched_sets(U, brain, m, c, N_MATCH, rng, exclude=S)
    G5, i5 = trajectory_matched_sets(U, [U.genes[i] for i in S], tr, N_MATCH, rng)
    for k, st, info in (("G2", G2, i2), ("G4", G4, i4), ("G5", G5, i5)):
        out[f"p_{k}"] = None if st is None else emp_p(corr_matrix(y, U.scores(st))[0], r, sign)
        out[f"{k}_info"] = {kk: v for kk, v in info.items() if kk != "missing"}
    if G2 is not None:
        pool = U.scores(G2)
        out["p_J1_joint"] = max(joint_j1(y, score, pool, s1[:N_MATCH], sign)[1],
                                joint_j1(y, score, pool, s2[:N_MATCH], sign)[1])
    return out


def main():
    rng = np.random.default_rng(SEED)
    ge = loadmat(G / "gene_expression.mat" / "gene_expression.mat")
    expr = ge["mDataGEctx"]
    symbols = mat_strings(ge["gene_symbols"])
    regions = mat_strings(ge["regionDescriptionCtx"])
    ex = loadmat(G / "examples" / "examples" / "example_conn_5k_genes.mat")
    img = ex["img_data"]
    desc = mat_strings(ex["imgDescriptions"])
    hse = mat_strings(ex["geneset"])
    # region-order assertion: the example's 5k-gene matrix must equal the full matrix's columns for those genes
    ex_sym = mat_strings(ex["gene_symbols"])
    idx = [symbols.index(s) for s in ex_sym[:200]]
    a, b = ex["gene_expression"][:, :200], expr[:, idx]
    ok = np.isfinite(a) & np.isfinite(b)
    order_ok = bool(np.allclose(a[ok], b[ok]))
    res = dict(commit=subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                                     text=True).stdout.strip(), seed=SEED, n_null=N, n_matched=N_MATCH,
               region_order_ok=order_ok, img_descriptions=desc, hse=hse)
    assert order_ok, "example img_data region order does not match gene_expression.mat"

    # ---- P+2 reproduction: beta (GAMBA definition) ----
    wei = {"NOS": 0.678, "SD": 0.637, "FC": 0.450}
    betas = {d: gamba_beta(expr, symbols, hse, img[:, j]) for j, d in enumerate(desc)}
    res["P2_beta"] = betas
    res["P2_beta_check"] = {k: dict(ours=betas.get(k), wei=v, pass_=betas.get(k) is not None and abs(betas[k] - v) <= 0.05)
                            for k, v in wei.items()}

    # ---- engine universe on Wei's matrix: genes without NaN ----
    keep = np.isfinite(expr).all(0)
    sym_arr = np.array(symbols)
    dfx = pd.DataFrame(expr[:, keep], columns=sym_arr[keep]).T.groupby(level=0).mean().T
    U = Universe(dfx)
    res["universe"] = dict(n_genes_total=len(symbols), n_no_nan=int(keep.sum()), n_unique=len(U.genes))
    bg = pd.read_csv(GAMBA_CSV)
    flag = "brain > body (default)"
    conflict = bg.groupby("symbols")[flag].nunique()
    bgenes = set(bg.loc[(bg[flag] == 1) & ~bg["symbols"].isin(conflict[conflict > 1].index), "symbols"])
    brain = np.array(sorted(U.index[g] for g in bgenes if g in U.index))
    T, tinfo = load_trajectories()
    tr = Trajectories(T, U)
    xyz = dk114_centroids(regions)
    D = centroid_distance(xyz)
    ms = MoranSpectral(D)
    S, sinfo = U.testable_set(hse)
    res["P2_set"] = {k: v for k, v in sinfo.items()}
    spin = wei_spin_scores([U.genes[i] for i in S])
    res["P2_cascade"] = {}
    for j, d in enumerate(desc):
        if d in ("NOS", "SD", "FC"):
            res["P2_cascade"][d] = cascade_on(zs(img[:, j]), S, U, brain, tr, D, ms, rng, spin_scores=spin)
    res["P2_pass"] = bool(all(res["P2_beta_check"][k]["pass_"] for k in wei)
                          and all(res["P2_cascade"][d]["p_G1"] < 0.05 and res["P2_cascade"][d]["p_G3"] < 0.05
                                  for d in ("NOS", "SD")))

    # ---- C1: APOE x AD ALE ----
    ad = parcel_means(G / "examples" / "examples" / "alzheimers_ALE.nii.gz", regions)
    b_apoe = gamba_beta(expr, symbols, ["APOE"], ad)
    res["C1_beta"] = dict(ours=b_apoe, wei=0.631, reproduced=abs(b_apoe - 0.631) <= 0.10)
    if res["C1_beta"]["reproduced"]:
        Sa, _ = U.testable_set(["APOE"], allow_single=True)
        c1 = cascade_on(zs(ad), Sa, U, brain, tr, D, ms, rng, single=True,
                        spin_scores=wei_spin_scores(["APOE"]))
        res["C1_cascade"] = c1
        res["C1_pass"] = bool(c1["p_L1_joint"] < 0.05 and c1["p_G3"] >= 0.05)
    else:
        res["C1_pass"] = "not the same map (beta not reproduced) -> C1 not run; must-catch rests on F-mod"
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "e3_realplants.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("region_order_ok", "P2_beta_check", "P2_pass", "C1_beta", "C1_pass")},
                     indent=1, default=float))


if __name__ == "__main__":
    main()
