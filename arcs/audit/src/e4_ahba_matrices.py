"""ASDG-AUD-E4-apparatus §3.1: AHBA parcel x gene matrices with abagen 0.1.3 frozen defaults + assertions A1-A5.

Atlases: V-AAL, V-HO, V-CC200 (PCP NIfTIs, E:\\data\\asdg\\abide1_pcp\\atlases) and V-DK (abagen's bundled DK).
Outputs (D:, gitignored if large): artifacts/ahba/<atlas>_expr.csv.gz, <atlas>_report.txt, <atlas>_atlas_info.csv,
<atlas>_meta.json; a summary is printed and written to arcs/audit/results/e4_ahba_matrices.json.

Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e4_ahba_matrices.py [atlas ...]
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import abagen
import nibabel as nib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATA = Path("E:/data/asdg")
ATL = DATA / "abide1_pcp" / "atlases"
import os  # noqa: E402

OUT = Path(os.environ.get("ASDG_AHBA_OUT", ROOT / "artifacts" / "ahba"))  # A5 writes to artifacts/ahba_pd22
RES = ROOT / "arcs" / "audit" / "results"

FROZEN = dict(ibf_threshold=0.5, probe_selection="diff_stability", donor_probes="aggregate", lr_mirror=None,
              missing=None, tolerance=2, sample_norm="srs", gene_norm="srs", norm_matched=True,
              norm_structures=False, region_agg="donors", agg_metric="mean", corrected_mni=True,
              reannotated=True, return_donors=False)
SUBCORTEX_AAL = ("Hippocampus", "ParaHippocampal", "Amygdala", "Caudate", "Putamen", "Pallidum", "Thalamus")
SUBCORTEX_HO = ("Thalamus", "Caudate", "Putamen", "Pallidum", "Brain-Stem", "Brainstem", "Hippocampus",
                "Amygdala", "Accumbens")


def git_commit() -> str:
    return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def centroids(img: nib.Nifti1Image, ids) -> pd.DataFrame:
    d = np.asarray(img.dataobj).astype(int)
    rows = []
    for i in ids:
        vox = np.argwhere(d == i)
        xyz = nib.affines.apply_affine(img.affine, vox).mean(0)
        rows.append((i, *xyz, len(vox)))
    return pd.DataFrame(rows, columns=["id", "x", "y", "z", "n_vox"])


def read_labels(path: Path) -> pd.DataFrame:
    rows = [l.split(",", 1) for l in path.read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    return pd.DataFrame([(int(a), b.strip()) for a, b in rows], columns=["id", "label"])


def aal_structure(label: str) -> str:
    if label.startswith(("Cerebelum", "Vermis")):
        return "cerebellum"
    if label.startswith(SUBCORTEX_AAL):
        return "subcortex/brainstem"
    return "cortex"


def ho_structure(label: str) -> str:
    return "subcortex/brainstem" if any(k in label for k in SUBCORTEX_HO) else "cortex"


def hemi(x: float) -> str:
    return "B" if abs(x) < 2.0 else ("L" if x < 0 else "R")


def atlas_and_info(name: str):
    if name == "dk":
        a = abagen.fetch_desikan_killiany()
        info = pd.read_csv(a["info"])
        img = nib.load(a["image"])
        cen = centroids(img, info["id"])
        return img, info, cen
    img = nib.load(ATL / f"{name}_roi_atlas.nii.gz")
    ids = [int(i) for i in np.unique(np.asarray(img.dataobj)) if i != 0]
    cen = centroids(img, ids)
    if name == "aal":
        lab = read_labels(ATL / "aal_labels.csv")
        lab["structure"] = lab["label"].map(aal_structure)
    elif name == "ho":
        lab = read_labels(ATL / "ho_labels.csv")
        lab["structure"] = lab["label"].map(ho_structure)
    elif name == "cc200":
        raw = pd.read_csv(ATL / "CC200_ROI_labels.csv", skipinitialspace=True)
        aal_col = [c for c in raw.columns if c.strip() == "AAL"][0]
        ho_col = [c for c in raw.columns if c.strip() == "Harvard-Oxford"][0]
        top = lambda s: (re.findall(r'\["([^"]+)":', str(s)) or ["None"])[0]  # noqa: E731
        lab = pd.DataFrame({"id": raw.iloc[:, 0].astype(int), "label": raw[aal_col].map(top),
                            "ho": raw[ho_col].map(top)})
        lab["structure"] = [aal_structure(a) if a != "None" else ("other" if h == "None" else ho_structure(h))
                            for a, h in zip(lab["label"], lab["ho"])]
    else:
        raise ValueError(name)
    info = cen[["id"]].merge(lab, on="id", how="left")
    # atlas ids absent from the label file (HO: id 3455, 2 voxels, present as a PCP time-series column) are kept
    # as "unlabelled_<id>" with structure "other" and listed in <atlas>_meta.json
    miss = info["label"].isna()
    info.loc[miss, "label"] = ["unlabelled_%d" % i for i in info.loc[miss, "id"]]
    info.loc[miss, "structure"] = "other"
    info["hemisphere"] = cen["x"].map(hemi).to_numpy()
    return img, info[["id", "label", "hemisphere", "structure"]], cen


def sha(df: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).to_numpy().tobytes()).hexdigest()


def run(name: str) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    img, info, cen = atlas_and_info(name)
    info.to_csv(OUT / f"{name}_atlas_info.csv", index=False)
    cen.to_csv(OUT / f"{name}_centroids.csv", index=False)
    files = abagen.fetch_microarray(data_dir=str(DATA / "ahba"), donors="all")
    assert len(files) == 6, f"A1 FAIL: {len(files)} donors"  # A1
    expr, report = abagen.get_expression_data(img, atlas_info=info, data_dir=str(DATA / "ahba"),
                                              donors="all", return_report=True, verbose=1, **FROZEN)
    (OUT / f"{name}_report.txt").write_text(report, encoding="utf-8", newline="\n")
    empty = expr.index[expr.isna().all(axis=1)].tolist()
    assert not expr.isna().all(axis=0).any(), "A3 FAIL: all-NaN gene column"  # A3
    kept = expr.drop(index=empty)
    assert not kept.isna().any().any(), "A3 FAIL: NaN left after dropping empty parcels"
    path = OUT / f"{name}_expr.csv.gz"
    expr.to_csv(path)
    back = pd.read_csv(path, index_col=0)  # A4 read-back
    assert back.shape == expr.shape and np.allclose(back.to_numpy(), expr.to_numpy(), equal_nan=True, atol=1e-12), \
        "A4 FAIL: read-back differs"
    meta = dict(atlas=name, unlabelled_ids=[int(i) for i in info.loc[info["label"].str.startswith("unlabelled_"), "id"]],
                n_parcels=int(expr.shape[0]), n_genes=int(expr.shape[1]), empty_parcels=empty,
                n_empty=len(empty), sha256_matrix=sha(expr), abagen=abagen.__version__, settings=FROZEN,
                commit=git_commit(), donors=[Path(f["microarray"]).parent.name for f in files.values()]
                if isinstance(files, dict) else len(files))
    (OUT / f"{name}_meta.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
    return meta


if __name__ == "__main__":
    names = sys.argv[1:] or ["dk", "aal", "ho", "cc200"]
    summary = {}
    for n in names:
        m = run(n)
        summary[n] = {k: m[k] for k in ("n_parcels", "n_genes", "n_empty", "empty_parcels", "sha256_matrix", "commit")}
        print(n, summary[n], flush=True)
    if "dk" in summary:
        ok = summary["dk"]["n_genes"] == 15633
        print(f"A2 {'PASS' if ok else 'FAIL'}: V-DK n_genes = {summary['dk']['n_genes']} (required 15,633)")
        summary["A2_dk_15633"] = ok
    RES.mkdir(parents=True, exist_ok=True)
    out = RES / ("e4_ahba_matrices.json" if OUT.name == "ahba" else f"e4_ahba_matrices_{OUT.name}.json")
    prev = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    prev.update(summary)
    out.write_text(json.dumps(prev, indent=1, default=str), encoding="utf-8")
