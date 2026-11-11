"""ASDG-AUD-E3-plants P+1, class-stratified Level-1 pair (prereg §6.4: "Level-1 p < 0.05 (adopted pair)").

e3_p1_myelin.py (@bc69ebc) computed the joint pair (S1, S2) and recorded "S1c/S2c equal S1/S2 here (single tissue
class)" - true in distribution (one class: within-class surrogates of the demeaned map, mean added back), but not
measured. This script rebuilds the identical inputs, ASSERTS that it reproduces the committed rho, p_S1 and p_S2
exactly (same seed, same draw order), then draws S1c and S2c (stratified_surrogates, one tissue class) with seeds
taken after those draws, and writes arcs/audit/results/e3_p1_strat.json. e3_p1_myelin.json is not modified.
Run in the main venv: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e3_p1_strat.py
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from asdg.spatial import centroid_distance, brainsmash_surrogates, MoranSpectral, stratified_surrogates  # noqa: E402
from asdg.cascade import corr_matrix, emp_p  # noqa: E402
from e3_p1_myelin import NM, ANNOT, N, SEED  # noqa: E402

RES = ROOT / "arcs/audit/results"


def main():
    from neuromaps.datasets import fetch_atlas

    ref = json.loads((RES / "e3_p1_myelin.json").read_text(encoding="utf-8"))
    rng = np.random.default_rng(SEED)
    # --- inputs: verbatim from e3_p1_myelin.main ---
    expr = pd.read_csv(ROOT / "artifacts/ahba/dk_expr.csv.gz", index_col=0)
    info = pd.read_csv(ROOT / "artifacts/ahba/dk_atlas_info.csv").set_index("id")
    cen = pd.read_csv(ROOT / "artifacts/ahba/dk_centroids.csv").set_index("id")
    ids = [i for i in expr.index if info.loc[i, "hemisphere"] == "L" and info.loc[i, "structure"] == "cortex"
           and not expr.loc[i].isna().any()]
    X = expr.loc[ids].to_numpy(float)
    Xz = (X - X.mean(0)) / X.std(0, ddof=1)
    u, s, _ = np.linalg.svd(Xz, full_matrices=False)
    pc1 = u[:, 0] * s[0]
    names = info.loc[ids, "label"].tolist()
    from scipy.spatial import cKDTree
    fetch_atlas("fsLR", "32k", data_dir=str(NM))
    fetch_atlas("fsaverage", "10k", data_dir=str(NM))
    L = sorted(NM.rglob("*myelinmap*hemi-L*.func.gii"))[0]
    src = [p for p in NM.rglob("tpl-fsLR_space-fsaverage_den-32k_hemi-L_sphere.surf.gii")][0]
    trg = [p for p in NM.rglob("tpl-fsaverage_den-10k_hemi-L_sphere.surf.gii")][0]
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
    a, b = rankdata(pc1), rankdata(myelin)
    rho = float(spearmanr(pc1, myelin).statistic)
    sign = 1 if rho > 0 else -1
    D = centroid_distance(cen.loc[ids, ["x", "y", "z"]].to_numpy())
    s1 = brainsmash_surrogates(b, D, N, int(rng.integers(2**31)))
    s2 = MoranSpectral(D).surrogates(b, N, int(rng.integers(2**31)))
    p_s1 = emp_p(corr_matrix(s1, a)[:, 0], rho, sign)
    p_s2 = emp_p(corr_matrix(np.apply_along_axis(rankdata, 1, s2), a)[:, 0], rho, sign)
    # --- apparatus: the rebuilt inputs and joint pair must equal the committed run exactly ---
    assert names == ref["parcels"], "parcel list differs from e3_p1_myelin.json"
    assert rho == ref["rho"], (rho, ref["rho"])
    assert (p_s1, p_s2) == (ref["p_S1"], ref["p_S2"]), ((p_s1, p_s2), (ref["p_S1"], ref["p_S2"]))
    # --- the stratified pair (one tissue class; seeds drawn after the committed draws) ---
    classes = info.loc[ids, "structure"].to_numpy()
    assert set(classes) == {"cortex"}
    s1c = stratified_surrogates(b, D, classes, N, int(rng.integers(2**31)), "brainsmash")
    s2c = stratified_surrogates(b, D, classes, N, int(rng.integers(2**31)), "msr")
    p_s1c = emp_p(corr_matrix(s1c, a)[:, 0], rho, sign)  # BrainSMASH resamples values: ranks preserved
    p_s2c = emp_p(corr_matrix(np.apply_along_axis(rankdata, 1, s2c), a)[:, 0], rho, sign)
    out = dict(n_parcels=len(ids), rho=rho, p_S1=p_s1, p_S2=p_s2, p_S1c=p_s1c, p_S2c=p_s2c,
               p_L1_joint=max(p_s1, p_s2), p_L1_strat=max(p_s1c, p_s2c), p_S3_vasa=ref["p_S3_vasa"], n_null=N,
               seed=SEED, reproduced_committed=dict(parcels=True, rho=True, p_S1=True, p_S2=True),
               criterion=dict(rho_in_range=bool(0.3 <= abs(rho) <= 0.9), L1_joint=bool(max(p_s1, p_s2) < 0.05),
                              L1_strat=bool(max(p_s1c, p_s2c) < 0.05), S3=bool(ref["p_S3_vasa"] < 0.05)),
               source="e3_p1_myelin.json (rho, S1, S2 reproduced exactly; S3 copied)",
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               commit=subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True,
                                     text=True).stdout.strip())
    out["P1_pass_if_strat_adopted"] = bool(out["criterion"]["rho_in_range"] and out["criterion"]["L1_strat"]
                                           and out["criterion"]["S3"])
    (RES / "e3_p1_strat.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    back = json.loads((RES / "e3_p1_strat.json").read_text(encoding="utf-8"))
    assert back["p_L1_strat"] == out["p_L1_strat"]
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
