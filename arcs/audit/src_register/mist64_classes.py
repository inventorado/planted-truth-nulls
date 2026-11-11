"""Pre-freeze work (claims register v4 section 1.10 (0), section 3.6; TSV target 18 route): MIST64 parcel centroids,
hemisphere, primary parcels and tissue classes for Moreau 2020, from the MIST atlas itself (no map is read).

Rules (register 3.6 / prereg section 2, applied mechanically):
- centroid = mean MNI mm coordinate of the parcel's voxels in Release/Parcellations/MIST_64.nii.gz (the e4 builder's
  `centroids`), checked against the atlas table's own x / y / z columns (reported, not used);
- hemisphere by prereg section 2's rule, imported from arcs/audit/src/e4_ahba_matrices.py `hemi`: B iff |x| < 2 mm, else
  L (x < 0) or R (x > 0);
- primary parcels = hemisphere L or B (prereg section 2; register 3.6);
- tissue class from the atlas's own label names (Release/Parcel_Information/MIST_64.csv, column `name`):
  cerebellum iff the name starts with "CEREBELLUM"; subcortex iff the name contains one of PUTAMEN, THALAMUS, CAUDATE,
  ACCUMBENS, PALLIDUM, AMYGDALA, HIPPOCAMPUS, BRAINSTEM (AMY_HIPP -> subcortex, register 3.6); else cortex.
  Cross-check (reported): the parcel's majority parent at MIST's 12-parcel level (Hierarchy/MIST_PARCEL_ORDER.csv, atoms
  counted) is CER (cerebellum) or BG_THAL (basal ganglia and thalamus).

Output: arcs/audit/register_maps/mist64_classes.json. Prints counts and hashes only.
Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src_register\\mist64_classes.py
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "arcs" / "audit" / "src"))
from e4_ahba_matrices import centroids, hemi  # noqa: E402  (the prereg section 2 rule, one implementation)

MIST = Path("E:/data/asdg/mist/extracted/Release")
VOL = MIST / "Parcellations" / "MIST_64.nii.gz"
TAB = MIST / "Parcel_Information" / "MIST_64.csv"
TAB12 = MIST / "Parcel_Information" / "MIST_12.csv"
ORDER = MIST / "Hierarchy" / "MIST_PARCEL_ORDER.csv"
ZIP = Path("E:/data/asdg/mist/MIST_parcellation.zip")
OUT = ROOT / "arcs" / "audit" / "register_maps" / "mist64_classes.json"
SUBCORTICAL_TOKENS = ("PUTAMEN", "THALAMUS", "CAUDATE", "ACCUMBENS", "PALLIDUM", "AMYGDALA", "HIPPOCAMPUS", "BRAINSTEM")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git_head() -> str:
    return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def tissue(name: str) -> str:
    n = name.upper()
    if n.startswith("CEREBELLUM"):
        return "cerebellum"
    if any(t in n for t in SUBCORTICAL_TOKENS):
        return "subcortex"
    return "cortex"


def load_int_atlas() -> nib.Nifti1Image:
    img = nib.load(VOL)
    d = np.asarray(img.dataobj)
    assert np.all(np.isfinite(d)) and np.all(d == np.round(d)), "non-integral labels"
    di = d.astype(np.int32)
    out = nib.Nifti1Image(di, img.affine)
    out.set_qform(img.affine, code=1)
    out.set_sform(img.affine, code=1)
    return out


def main() -> int:
    tab = pd.read_csv(TAB, sep=";")
    assert list(tab["roi"]) == list(range(1, 65)), "label table rois are not 1..64"
    assert tab["label"].is_unique and tab["name"].is_unique
    img = load_int_atlas()
    ids = sorted(int(i) for i in np.unique(np.asarray(img.dataobj)) if i != 0)
    assert ids == list(range(1, 65)), "volume labels are not 1..64 (%d found)" % len(ids)
    cen = centroids(img, ids)
    assert (cen["n_vox"] > 0).all()
    df = tab[["roi", "label", "name", "x", "y", "z"]].rename(columns={"x": "x_table", "y": "y_table", "z": "z_table"})
    df = df.merge(cen.rename(columns={"id": "roi"}), on="roi", how="left", validate="one_to_one")
    assert df[["x", "y", "z"]].notna().all().all()
    df["centroid_minus_table_max_abs_mm"] = (df[["x", "y", "z"]].to_numpy() - df[["x_table", "y_table", "z_table"]].to_numpy()).__abs__().max(1)
    df["hemisphere"] = df["x"].map(hemi)
    df["tissue_class"] = df["name"].map(tissue)
    df["primary"] = df["hemisphere"].isin(["L", "B"])
    # cross-check: majority 12-level parent over atoms
    order = pd.read_csv(ORDER)
    t12 = pd.read_csv(TAB12, sep=";")
    lab12 = dict(zip(t12["roi"], t12["label"]))
    maj = order.groupby("s64")["s12"].agg(lambda s: s.value_counts().idxmax())
    share = order.groupby("s64")["s12"].agg(lambda s: s.value_counts(normalize=True).max())
    df["mist12_majority_parent"] = df["roi"].map(lambda r: lab12[int(maj[r])])
    df["mist12_majority_share"] = df["roi"].map(lambda r: round(float(share[r]), 4))
    hier_class = df["mist12_majority_parent"].map(lambda l: "cerebellum" if l == "CER" else ("subcortex" if l == "BG_THAL" else "cortex"))
    disagree = df.loc[hier_class != df["tissue_class"], ["label", "tissue_class", "mist12_majority_parent"]]

    counts = {c: int((df["tissue_class"] == c).sum()) for c in ("cortex", "subcortex", "cerebellum")}
    hemi_counts = {h: int((df["hemisphere"] == h).sum()) for h in ("L", "B", "R")}
    prim = df[df["primary"]]
    prim_counts = {c: int((prim["tissue_class"] == c).sum()) for c in ("cortex", "subcortex", "cerebellum")}
    cross = {"%s|%s" % (c, h): int(((df["tissue_class"] == c) & (df["hemisphere"] == h)).sum())
             for c in ("cortex", "subcortex", "cerebellum") for h in ("L", "B", "R")}
    lateral_prefix = df["label"].str.match(r"^[LR]_")
    # parcels whose label carries no hemisphere prefix but whose centroid falls outside |x| < 2 mm
    unprefixed_not_B = df.loc[~lateral_prefix & (df["hemisphere"] != "B"), ["label", "x", "hemisphere"]]
    prefixed_check = df.loc[lateral_prefix, ["label", "x", "hemisphere"]]
    prefix_mismatch = [r.label for r in prefixed_check.itertuples() if r.label[0] != r.hemisphere]

    rows = []
    for r in df.itertuples():
        rows.append({"roi": int(r.roi), "label": r.label, "name": r.name, "n_vox_3mm": int(r.n_vox),
                     "centroid_mni_mm": [round(float(r.x), 4), round(float(r.y), 4), round(float(r.z), 4)],
                     "table_xyz": [float(r.x_table), float(r.y_table), float(r.z_table)],
                     "centroid_minus_table_max_abs_mm": round(float(r.centroid_minus_table_max_abs_mm), 4),
                     "hemisphere": r.hemisphere, "tissue_class": r.tissue_class, "primary": bool(r.primary),
                     "mist12_majority_parent": r.mist12_majority_parent, "mist12_majority_share": r.mist12_majority_share})
    out = {
        "what": ("MIST64 parcel centroids (MNI mm), hemisphere (prereg section 2: B iff |x| < 2 mm), primary parcels (L + B) and "
                 "tissue classes (cortex / subcortex / cerebellum; AMY_HIPP as subcortex) for Moreau 2020 (claims register v4 "
                 "section 3.6; section 1.10 (0) pre-freeze work). From the MIST atlas only; no map or claim value read."),
        "inputs": {
            "zip": {"path": str(ZIP), "sha256": sha256_file(ZIP), "doi": "10.6084/m9.figshare.5633638", "figshare_file_id": 9811081},
            "volume": {"path": str(VOL), "sha256": sha256_file(VOL), "shape": list(img.shape),
                       "voxel_mm": [float(v) for v in img.header.get_zooms()[:3]],
                       "affine": [[float(v) for v in row] for row in img.affine],
                       "note": "labels stored as float32 in the release; asserted integral and cast to int32"},
            "label_table": {"path": str(TAB), "sha256": sha256_file(TAB)},
            "mist12_table": {"path": str(TAB12), "sha256": sha256_file(TAB12)},
            "hierarchy": {"path": str(ORDER), "sha256": sha256_file(ORDER)},
        },
        "rules": {
            "centroid": "mean of voxel-centre MNI mm coordinates (affine applied), arcs/audit/src/e4_ahba_matrices.py centroids()",
            "hemisphere": "arcs/audit/src/e4_ahba_matrices.py hemi(): 'B' if abs(x) < 2.0 else ('L' if x < 0 else 'R')",
            "primary": "hemisphere in {L, B}",
            "tissue_class": ("name starts with CEREBELLUM -> cerebellum; name contains any of %s -> subcortex; else cortex"
                             % ", ".join(SUBCORTICAL_TOKENS)),
            "cross_check": "majority MIST 12-level parent over atoms: CER -> cerebellum, BG_THAL -> subcortex, else cortex",
        },
        "counts": {
            "n_parcels": int(len(df)),
            "tissue_class_all64": counts,
            "hemisphere_all64": hemi_counts,
            "tissue_by_hemisphere": cross,
            "primary_n": int(df["primary"].sum()),
            "primary_by_tissue_class": prim_counts,
            "bilateral_multiverse_cell_n": int(len(df)),
        },
        "checks": {
            "centroid_vs_table_max_abs_mm": round(float(df["centroid_minus_table_max_abs_mm"].max()), 4),
            "hierarchy_disagreements": [{"label": a, "name_rule": b, "mist12_majority_parent": c}
                                        for a, b, c in disagree.itertuples(index=False)],
            "labels_with_L_or_R_prefix": int(lateral_prefix.sum()),
            "prefixed_labels_whose_centroid_side_differs": prefix_mismatch,
            "unprefixed_labels_not_B_by_centroid": [{"label": a, "x": round(float(b), 3), "hemisphere": c}
                                                    for a, b, c in unprefixed_not_B.itertuples(index=False)],
        },
        "parcels": rows,
        "script": {"path": "arcs/audit/src_register/mist64_classes.py", "sha256": sha256_file(Path(__file__)),
                   "repo_head_at_run": git_head()},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(out, indent=1, ensure_ascii=False)
    OUT.write_text(txt, encoding="utf-8", newline="\n")
    back = json.loads(OUT.read_text(encoding="utf-8"))
    assert back == json.loads(txt)
    print("parcels %d; tissue %s; hemisphere %s; primary %d %s" % (len(df), counts, hemi_counts, int(df["primary"].sum()), prim_counts))
    print("centroid vs table max |d| %.4f mm; hierarchy disagreements %d; unprefixed labels not B %d; prefix/side mismatches %d"
          % (out["checks"]["centroid_vs_table_max_abs_mm"], len(disagree), len(unprefixed_not_B), len(prefix_mismatch)))
    print("output %s sha256 %s" % (OUT.relative_to(ROOT).as_posix(), sha256_file(OUT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
