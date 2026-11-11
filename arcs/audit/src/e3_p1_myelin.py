"""ASDG-AUD-E3-plants P+1 (prereg §6.4): AHBA expression PC1 over V-DK left cortical parcels x HCP T1w/T2w.

Criterion: |rho| in [0.3, 0.9] (Spearman) and Level-1 p < 0.05 (adopted pair; both pairs reported, adoption
decided by the §6 gates) and S3 (Vasa spin) p < 0.05. PC1 orientation is arbitrary, so the one-sided tests
use the observed sign. Run in the main venv; writes arcs/audit/results/e3_p1_myelin.json.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from asdg.spatial import centroid_distance, brainsmash_surrogates, MoranSpectral  # noqa: E402
from asdg.cascade import corr_matrix, emp_p  # noqa: E402

NM = Path("E:/data/asdg/neuromaps")
ANNOT = Path("E:/data/asdg/enigma_asd/giacomel2026_repo/data/DK-files/atlas-DK_fsa5_lh_aparc.annot")
N = 10000
SEED = 20260923


def main():
    from neuromaps.datasets import fetch_atlas
    from neuromaps.nulls.spins import gen_spinsamples

    rng = np.random.default_rng(SEED)
    # --- AHBA PC1 over V-DK left cortex (primary parcels, non-empty) ---
    expr = pd.read_csv(ROOT / "artifacts/ahba/dk_expr.csv.gz", index_col=0)
    info = pd.read_csv(ROOT / "artifacts/ahba/dk_atlas_info.csv").set_index("id")
    cen = pd.read_csv(ROOT / "artifacts/ahba/dk_centroids.csv").set_index("id")
    ids = [i for i in expr.index if info.loc[i, "hemisphere"] == "L" and info.loc[i, "structure"] == "cortex"
           and not expr.loc[i].isna().any()]
    X = expr.loc[ids].to_numpy(float)
    Xz = (X - X.mean(0)) / X.std(0, ddof=1)
    u, s, vt = np.linalg.svd(Xz, full_matrices=False)
    pc1 = u[:, 0] * s[0]
    var1 = float(s[0] ** 2 / (s ** 2).sum())
    names = info.loc[ids, "label"].tolist()

    # --- T1w/T2w: fsLR 32k -> fsaverage 10k, parcel mean with the DK fsa5 annotation ---
    L = sorted((NM).rglob("*myelinmap*hemi-L*.func.gii"))[0]
    R = sorted((NM).rglob("*myelinmap*hemi-R*.func.gii"))[0]
    # Connectome Workbench (wb_command) is not installed, so neuromaps' ADAP_BARY_AREA resampling cannot run.
    # Nearest-neighbour resampling instead: fsLR-32k sphere registered to fsaverage space -> fsaverage-10k
    # sphere (both neuromaps templates, fetched to E:). Medial-wall vertices (value 0 / non-finite) excluded.
    from scipy.spatial import cKDTree
    src_sph = fetch_atlas("fsLR", "32k", data_dir=str(NM))
    trg_sph = fetch_atlas("fsaverage", "10k", data_dir=str(NM))
    src = [p for p in Path(NM).rglob("tpl-fsLR_space-fsaverage_den-32k_hemi-L_sphere.surf.gii")][0]
    trg = [p for p in Path(NM).rglob("tpl-fsaverage_den-10k_hemi-L_sphere.surf.gii")][0]
    xs = nib.load(src).agg_data()[0]; xt = nib.load(trg).agg_data()[0]
    vals = np.asarray(nib.load(str(L)).agg_data(), float)
    good = np.isfinite(vals) & (vals != 0)
    xs_u = xs[good] / np.linalg.norm(xs[good], axis=1, keepdims=True)
    xt_u = xt / np.linalg.norm(xt, axis=1, keepdims=True)
    lh = vals[good][cKDTree(xs_u).query(xt_u)[1]]
    lab, _, lnames = nib.freesurfer.read_annot(str(ANNOT))
    lnames = [n.decode() for n in lnames]
    myelin = np.array([lh[lab == lnames.index(n)].mean() for n in names])
    assert np.isfinite(myelin).all()

    # --- statistic and nulls (Spearman: rank both, Pearson on ranks) ---
    a, b = rankdata(pc1), rankdata(myelin)
    rho = float(spearmanr(pc1, myelin).statistic)
    sign = 1 if rho > 0 else -1
    D = centroid_distance(cen.loc[ids, ["x", "y", "z"]].to_numpy())
    s1 = brainsmash_surrogates(b, D, N, int(rng.integers(2**31)))
    s2 = MoranSpectral(D).surrogates(b, N, int(rng.integers(2**31)))
    p_s1 = emp_p(corr_matrix(s1, a)[:, 0], rho, sign)
    p_s2 = emp_p(corr_matrix(np.apply_along_axis(rankdata, 1, s2), a)[:, 0], rho, sign)
    # S3: Vasa spin on fsaverage5 sphere, left hemisphere parcel centroids
    sph = fetch_atlas("fsaverage", "10k", data_dir=str(NM))["sphere"][0]
    coords, faces = nib.load(sph).agg_data()
    pcoords = np.array([coords[lab == lnames.index(n)].mean(0) for n in names])
    pcoords /= np.linalg.norm(pcoords, axis=1, keepdims=True)
    spins = gen_spinsamples(pcoords, np.zeros(len(names), int), n_rotate=N, method="vasa", seed=SEED)
    p_s3 = emp_p(corr_matrix(b[spins.T], a)[:, 0], rho, sign)
    out = dict(
        n_parcels=len(ids), parcels=names, pc1_var_explained=var1, rho=rho,
        p_S1=p_s1, p_S2=p_s2, p_L1_joint=max(p_s1, p_s2), p_S3_vasa=p_s3, n_null=N, seed=SEED,
        criterion=dict(rho_in_range=bool(0.3 <= abs(rho) <= 0.9), L1_joint=bool(max(p_s1, p_s2) < 0.05),
                       S3=bool(p_s3 < 0.05)),
        note="cortex only: S1c/S2c equal S1/S2 here (single tissue class); myelin resampled fsLR->fsaverage10k by nearest neighbour (no wb_command)",
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        commit=subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip())
    out["P1_pass_if_joint_adopted"] = bool(all(out["criterion"].values()))
    (ROOT / "arcs/audit/results/e3_p1_myelin.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "parcels"}, indent=1))


if __name__ == "__main__":
    main()
