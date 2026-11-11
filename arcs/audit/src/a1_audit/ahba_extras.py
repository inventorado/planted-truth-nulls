"""RUN_PLAN_amend_2.md v2.1 (FROZEN acdb1290...) additions beside the WP2 AHBA builds (a1_audit/ahba_builds.py, kept
byte-identical so the build records' script hash stays valid; orchestrator decision 2026-10-02: "the MOVE").

- R38 (WP4): `build_perdonor_hcpmmp1` is R14's HCP-MMP1 per-donor build (ahba_builds.NOT_BUILT's perdonor-hcpmmp1),
  implemented in WP4 phase 1 and run in phase 2 after the volume and its label list are fetched under G2 (§8's wrapper
  after step3v_open(), before eTable13 is read); `hcpmmp1_atlas_info` is its atlas_info (the centroid rule). WP2's
  hook raised NotImplementedError naming R38 and WP4 (R38_WP4 is kept as the reading's text).
- R40: `r12_ds` reproduces ahba_builds.derive_r12's DS call - abagen.correct.keep_stable_genes(<per-donor frames>,
  threshold=0.1, percentile=False, rank=True, return_stability=True), "as abagen implements it" - without changing
  derive_r12 (tests/test_amend2.py asserts the call's arguments equal derive_r12's, read from its source, and the result
  equal to abagen's bit for bit). `load_r12_ds` reads R12's stored DS vector (r12-han-c1-ourpc1/ds_dk_ctx_perdonor.csv)
  back against its build record: the file's sha256 and the round-trip frame hash. Benkarim's and Park's DS are that
  vector (repro.benkarim_ds_genes / park_ds_genes).
r12_ds needs abagen (env/venv_ref); load_r12_ds runs in either environment (pandas; ahba_builds' readers and hashes).
WP2 review B4: load_r12_ds refuses a record or DS path under the quarantine (fetch_extract.refuse_quarantine_opener)
before opening it.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from . import ahba_builds as AB

R38_WP4 = ("RUN_PLAN_amend_2 R38: perdonor-hcpmmp1 is built in WP4, after the HCP-MMP1 volume and its label list are "
           "fetched under G2 (§8's wrapper after step3v_open(), before eTable13 is read): every parcel of the label list "
           "handed to abagen (the whole volume); atlas_info hemisphere by §2's centroid rule (centroids as "
           "e4_ahba_matrices.centroids), structure 'cortex', a centroid hemisphere disagreeing with the L_ / R_ prefix "
           "counted (the centroid rule governs); §3.1 settings, return_donors=True, in env/venv_ref; analysis parcels the "
           "180 left parcels by R15's name match; parcels with no sample counted per donor and left out by R14's own "
           "clause")
# derive_r12's keep_stable_genes keyword arguments (ahba_builds.py, derive_r12), reproduced here
R12_DS_KWARGS = dict(threshold=AB.R12_THRESHOLD, percentile=False, rank=True, return_stability=True)
R12_DS_CALL = ("abagen.correct.keep_stable_genes(expression=<per-donor frames>, threshold=0.1, percentile=False, "
               "rank=True, return_stability=True)")
R12_BUILD = "r12-han-c1-ourpc1"
R12_DS_FILE = "ds_dk_ctx_perdonor.csv"


HCP_BUILD = "perdonor-hcpmmp1"
HCP_B_MM = 2.0          # prereg §2 (:51-53): "B = centroid |x| < 2 mm"
R38_RULE = ("RUN_PLAN_amend_2 R38: every parcel of the label list handed to abagen; hemisphere by the centroid rule "
            "(|x| < 2 mm -> B, x < 0 -> L, else R; centroids as e4_ahba_matrices.centroids: the mean world coordinate "
            "of the parcel's voxels); structure 'cortex'; a centroid hemisphere disagreeing with the L_ / R_ name "
            "prefix counted (the centroid rule governs); §3.1 settings, return_donors=True")


def hcpmmp1_atlas_info(labels_vol, affine, label_list) -> tuple:
    """R38 (WP4): abagen's atlas_info for the HCP-MMP1 volume - (DataFrame id / label / hemisphere / structure, counts).
    label_list: [(id, name)] read from the pinned label list (reparcel.read_label_list). Pure (numpy / pandas)."""
    import numpy as np
    import pandas as pd

    d = np.asarray(labels_vol).astype(np.int64)
    aff = np.asarray(affine, dtype=float)
    rows, n_disagree, n_absent = [], 0, 0
    for i, name in label_list:
        vox = np.argwhere(d == int(i))
        if len(vox) == 0:
            n_absent += 1
            raise AB.BuildError(f"{HCP_BUILD}: a label of the list has no voxel in the volume")
        xyz = (aff[:3, :3] @ vox.T.astype(float) + aff[:3, 3:4]).mean(axis=1)
        x = float(xyz[0])
        hemi = "B" if abs(x) < HCP_B_MM else ("L" if x < 0 else "R")
        pref = "L" if str(name).startswith("L_") else ("R" if str(name).startswith("R_") else None)
        n_disagree += int(pref is not None and hemi != pref)
        rows.append((int(i), str(name), hemi, "cortex"))
    present = {int(v) for v in np.unique(d)} - {0}
    listed = {int(i) for i, _ in label_list}
    info = pd.DataFrame(rows, columns=["id", "label", "hemisphere", "structure"])
    counts = dict(n_labels=len(rows), n_hemisphere_B=int((info["hemisphere"] == "B").sum()),
                  n_hemisphere_L=int((info["hemisphere"] == "L").sum()), n_hemisphere_R=int((info["hemisphere"] == "R").sum()),
                  n_prefix_disagreements=n_disagree, n_volume_labels_not_listed=len(present - listed))
    if present - listed:
        raise AB.BuildError(f"{HCP_BUILD}: the volume holds labels the list does not name")
    return info, counts


def hcpmmp1_call(abagen_signature=None) -> dict:
    """R38's abagen arguments: ahba_builds' frozen §3.1 settings with return_donors=True (ahba_builds.abagen_call's
    assertions: FROZEN equals e4's literal; abagen's signature covered)."""
    spec = AB.Spec(HCP_BUILD, "hcpmmp1", "perdonor", (("return_donors", True),), (R38_RULE,),
                   "the six per-donor HCP-MMP1 matrices (§3.1 settings, return_donors=True) + counts")
    return AB.abagen_call(spec, {})


def build_perdonor_hcpmmp1(volume_path: Path, label_text: str, out_dir: Path, *, get_expression_data=None,
                           volume_sha256: str | None = None, label_list_sha256: str | None = None) -> dict:
    """R38 (WP4): the per-donor HCP-MMP1 build after R15's fetch. The whole volume and every listed parcel are handed
    to abagen (the must-fail variant, a left-masked volume, is refused: every listed label must have voxels); outputs:
    matrix_d<k>.csv.gz (k = the donor's position in ahba_builds.DONORS; never the donor id) and counts.csv, each
    written and read back (ahba_builds.matrix_output / table_output), and build_record.json. get_expression_data: the
    abagen function (tests pass a fake that asserts its arguments). env/venv_ref for the real build."""
    import nibabel as nib

    from . import reparcel as RP

    volume_path, out_dir = Path(volume_path), Path(out_dir)
    data = volume_path.read_bytes()
    if volume_sha256 is not None and AB.sha256_bytes(data) != volume_sha256:
        raise AB.BuildError(f"{HCP_BUILD}: the volume differs from its R15 record")
    if label_list_sha256 is not None and AB.sha256_bytes(label_text.encode("utf-8")) != label_list_sha256:
        raise AB.BuildError(f"{HCP_BUILD}: the label list differs from its R15 record")
    img = RP.nifti_from_bytes(data)
    labels = RP.int_labels(np.asarray(img.dataobj))
    lst = RP.read_label_list(label_text)
    info, counts = hcpmmp1_atlas_info(labels, img.affine, lst)
    kw = hcpmmp1_call()
    if get_expression_data is None:
        import abagen
        get_expression_data = abagen.get_expression_data
    atlas_img = nib.Nifti1Image(labels.astype("int32"), img.affine)
    res = get_expression_data(atlas=atlas_img, atlas_info=info.set_index("id")[["hemisphere", "structure"]], **kw)
    donors, cnt = res[0], res[1]
    if not isinstance(donors, dict) or sorted(map(str, donors)) != sorted(AB.DONORS):
        raise AB.BuildError(f"{HCP_BUILD}: return_donors did not give the six donors")
    out_dir.mkdir(parents=True, exist_ok=True)
    outs = []
    no_sample = {}
    for donor, df in donors.items():
        k = AB.DONORS.index(str(donor)) + 1
        df = df.astype("float64")
        no_sample[f"d{k}"] = int(df.isna().all(axis=1).sum())
        o = AB.matrix_output(df, out_dir / f"matrix_d{k}.csv.gz", role="matrix")
        o["donor_position"] = k
        outs.append(o)
    tab = AB.counts_table(cnt, [str(c) for c in cnt.columns])
    outs.append(AB.table_output(tab, out_dir / "counts.csv", "counts"))
    rec = dict(build=HCP_BUILD, kind="perdonor", atlas="hcpmmp1", readings=[R38_RULE], abagen_call=
               {k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in kw.items()},
               atlas_info_counts=counts, parcels_without_sample_per_donor=no_sample, outputs=outs,
               volume_sha256=AB.sha256_bytes(data), label_list_sha256=AB.sha256_bytes(label_text.encode("utf-8")),
               ok=True)
    rp = out_dir / AB.RECORD
    AB.write_json(rp, rec)
    return rec


def r12_ds(frames):
    """R12 / R40: the differential stability 'as abagen implements it' - the stability vector of
    abagen.correct.keep_stable_genes on the given per-donor frames (rows = regions, columns = genes) with derive_r12's
    arguments (R12_DS_KWARGS): each donor ranked over its own regions, the ranks correlated over the regions both donors
    cover (abagen 0.1.3 correct.py:601, :606-609). env/venv_ref only (abagen)."""
    import numpy as np
    from abagen import correct

    _, ds = correct.keep_stable_genes(list(frames), **R12_DS_KWARGS)
    return np.asarray(ds, dtype=float)


def load_r12_ds(out: Path | None = None, quarantine_root: Path | None = None):
    """R40: R12's stored DS vector read back against its build record (the file's sha256 and the round-trip frame hash)
    -> (pandas Series indexed by gene symbol, identity dict). out: the builds' directory (default ahba_builds.OUT,
    read at call time). Each path is refused first if it lies under the quarantine (B4)."""
    import json

    from . import fetch_extract as FE

    out = Path(out) if out is not None else AB.OUT
    rp = out / R12_BUILD / AB.RECORD
    FE.refuse_quarantine_opener(rp, quarantine_root)
    if not rp.exists():
        raise AB.BuildError(f"{R12_BUILD}: no build record")
    rec = json.loads(rp.read_text(encoding="utf-8"))
    if rec.get("ok") is not True:
        raise AB.BuildError(f"{R12_BUILD}: record not ok")
    o = next((x for x in rec.get("outputs") or [] if x.get("file") == R12_DS_FILE), None)
    if o is None:
        raise AB.BuildError(f"{R12_BUILD}: no DS output in the record")
    p = FE.refuse_quarantine_opener(out / R12_BUILD / o["file"], quarantine_root)
    if AB.sha256_file(p) != o["sha256"]:
        raise AB.BuildError(f"{R12_BUILD}: the DS file differs from its record")
    df = AB.read_frame(p, "round_trip")
    if AB.frame_sha(df) != o["sha256_round_trip"]:
        raise AB.BuildError(f"{R12_BUILD}: the DS frame's round-trip hash differs from its record")
    if list(df.columns) != ["ds"]:
        raise AB.BuildError(f"{R12_BUILD}: the DS table's columns are not ['ds']")
    s = df["ds"].astype(float)
    s.index = [str(g) for g in s.index]
    return s, dict(file=f"{R12_BUILD}/{o['file']}", sha256=o["sha256"], sha256_round_trip=o["sha256_round_trip"],
                   n_genes=int(len(s)), record=f"{R12_BUILD}/{AB.RECORD}")
