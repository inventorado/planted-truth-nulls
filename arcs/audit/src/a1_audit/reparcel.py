"""Re-parcellation rules of the frozen register (claims_register.md:1028-1048, section 1.7) as read by
arcs/audit/RUN_PLAN.md v3.1 (R14, R15, R16, R31); P18. Every map re-parcellated here is labelled "re-parcellated".

- volume -> class atlas (dk-ctx, V-DK, V-AAL): the class atlas resampled to the map's grid by nearest neighbour
  (nn_resample_labels, ported verbatim from A3's T2 loader); parcel value = mean over its voxels with a finite
  non-zero value; a parcel with < 50 % of its voxels finite and non-zero is dropped and reported (A3's T2 rule).
- fsaverage surface -> dk-ctx: the annot's labels (nibabel.freesurfer.read_annot), `unknown` and `corpuscallosum`
  excluded, matched to the abagen DK names (exactly 34 must match, each once); parcel value = mean over the label's
  vertices with a finite value; the vertex count of the map must equal the annot's (both read from the files).
- parcel values -> dk-ctx (Glasser-360 through HCP-MMP1; Schaefer-400): the DK atlas resampled to the source atlas's
  native grid by nearest neighbour; each LEFT source parcel (ids read from the label list, never assumed) assigned to
  the left DK cortical label holding MORE THAN 50 % of its voxels (RUN_PLAN_amend_2 R43, RP2 literal: "the DK label
  holding the majority of its voxels"); a parcel with no such label - outside-majority parcels and parcels split with no
  label above 50 % - is dropped and reported; DK value = voxel-count-weighted mean of its assigned parcels (weight: the
  source parcel's voxel count on its native grid, RP3). R15: the left names of the label list matched one-to-one to
  eTable13's names, in memory, reported as counts only.
- DK-308 -> dk-ctx (Romero-Garcia): sub-parcel -> DK parent by name prefix (lh_bankssts_part1 -> bankssts); DK value =
  vertex-count-weighted mean of its sub-parcels, counts from the subParcellation annot.
- Power spheres -> V-AAL (Buch): each sphere to the AAL label containing its centroid (nearest voxel, floor(v + .5));
  label value = mean of its spheres; a sphere whose centroid lies outside every AAL label is dropped and reported.
- bilateral-average maps: one value per region placed on the left parcels.
- R14 / R31: recipe_parcellation() -- the per-donor recipe's parcellation and label (the paper's parcellation where the
  paper decoded on named parcels; the claim's analysis class for voxel- / sample-wise decoders, labelled "re-derived
  (per-donor parcel recipe, <class>), not the decoder"; Benkarim: dk-ctx, "re-derived (per-donor parcel recipe,
  dk-ctx; the paper's parcellation unnamed)", its NeuroVault volumes re-parcellated by the volume rule).

Readings where the frozen text leaves a corner open (fail closed; listed in the WP2 report). RUN_PLAN_amend_2 R43 pins
RP1, RP2 (changed after the freeze: > 50 %), RP3 and RP7 as stated here:
  RP1 (pinned) surface rule: no coverage threshold (the register states 50 % for volumes only); a label with no finite
      vertex is dropped and reported; each label's finite-vertex share is reported.
  RP2 (pinned, R43) majority: a source parcel is assigned to the left DK cortical label holding more than 50 % of its
      voxels (count > n / 2, decided in integers); otherwise it is dropped and reported - reason 'outside' when the
      voxels outside every given DK label are more than 50 %, else 'no label above 50 %' (two-way and many-way splits,
      50 / 50 included). The largest share is reported either way. (The plurality rule of 9addaab - the largest share
      wins whatever its size - is withdrawn.)
  RP3 (pinned) weights: the source parcel's voxel count on its native grid (all of its voxels, not only those inside
      the winning DK label); a source parcel without a finite value is skipped and reported.
  RP4 the label list is "<integer> <name>" per line (blank lines skipped); any other line -> refused (WP4 checks the
      real file's form under G2).
  RP5 GIFTI: exactly one data array of the vertex count, else refused.
  RP6 a sphere centroid outside the volume counts as outside every label.
  RP7 (pinned) nearest neighbour is A3's rule unchanged (index floor(v + .5)): a map voxel whose centre lies up to half
      a voxel beyond the atlas's outermost voxel centre takes that edge voxel's label; scipy / nilearn order-0
      resampling labels those voxels 0 (P18 shows the two agree on every interior voxel).

Pure functions on arrays (plus nibabel readers); nothing prints. Raises ReparcelRefused(<status label>) on a refusal.
WP2 review B4: the three readers (load_atlas_verified, read_annot, read_gifti_values) refuse a path under the quarantine
(fetch_extract.refuse_quarantine_opener: PermissionError) before opening it.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np

MIN_COVERAGE = 0.5
LABEL_REPARCELLATED = "re-parcellated"
FS_EXCLUDED = ("unknown", "corpuscallosum")
N_DK_CORTICAL = 34

STATUS_ATLAS_IDENTITY = "not computable (atlas identity)"
STATUS_GLASSER = ("not auditable (definition not applicable: the pinned HCP-MMP1 atlas could not be matched to "
                  "eTable13)")
STATUS_FS_NOT_REGULAR = ("not auditable (definition not applicable: the FreeSurfer 7.4.1 distribution annot is not a "
                         "regular member of the stream)")
STATUS_FS_NOT_MATCHING = ("not auditable (definition not applicable: the FreeSurfer 7.4.1 distribution annot not "
                          "obtainable / not matching)")
STATUS_ROI_UNPUBLISHED = "not auditable (ROI coordinates unpublished)"
RECIPE_DECODER = "re-derived (per-donor parcel recipe, {cls}), not the decoder"
RECIPE_BENKARIM = "re-derived (per-donor parcel recipe, dk-ctx; the paper's parcellation unnamed)"

PHRASES = (LABEL_REPARCELLATED, STATUS_ATLAS_IDENTITY, STATUS_GLASSER, STATUS_FS_NOT_REGULAR,
           STATUS_FS_NOT_MATCHING, STATUS_ROI_UNPUBLISHED, RECIPE_DECODER.format(cls="dk-ctx"), RECIPE_BENKARIM,
           "n_vox n_valid coverage kept dropped n_vertices n_finite share tie outside assigned weight weights "
           "n_kept n_dropped n_assigned n_ties n_outside n_unassigned matched one_to_one n_a n_b n_no_majority "
           "no label above 50 % majority")


class ReparcelRefused(Exception):
    """A refusal; its only argument is a status label of the vocabulary above (never a name or a value)."""

    def __init__(self, status: str):
        super().__init__(status)
        self.status = status


# ported from arcs/replication/src/h_targets.py:262 (git blob a1736bcbdb63a821e8ed652e6a019310a9710690 at HEAD 7d1df00)
def nn_resample_labels(labels: np.ndarray, src_affine: np.ndarray, dst_shape, dst_affine: np.ndarray) -> np.ndarray:
    """Nearest-neighbour resampling of an integer label volume onto another grid: each destination voxel takes the
    label of the source voxel whose centre is nearest in world (mm) space (index rounding floor(v + .5)); outside the
    source volume -> 0. Only labels present in the source can appear."""
    labels = np.asarray(labels)
    ijk = np.indices(tuple(dst_shape)).reshape(3, -1).astype(float)
    world = dst_affine[:3, :3] @ ijk + dst_affine[:3, 3:4]
    inv = np.linalg.inv(src_affine)
    v = inv[:3, :3] @ world + inv[:3, 3:4]
    idx = np.floor(v + 0.5).astype(np.int64)
    inside = np.all((idx >= 0) & (idx < np.array(labels.shape[:3])[:, None]), axis=0)
    out = np.zeros(ijk.shape[1], dtype=labels.dtype)
    out[inside] = labels[idx[0, inside], idx[1, inside], idx[2, inside]]
    return out.reshape(tuple(dst_shape))
# end of the ported block


def squeeze3(a) -> np.ndarray:
    a = np.asarray(a)
    while a.ndim > 3 and a.shape[-1] == 1:
        a = a[..., 0]
    if a.ndim != 3:
        raise ValueError("volume is not 3-D")
    return a


def int_labels(a) -> np.ndarray:
    a = squeeze3(a)
    ai = np.rint(a).astype(np.int64)
    if not np.allclose(a, ai):
        raise ValueError("atlas labels are not integers")
    return ai


def nifti_from_bytes(data: bytes):
    import gzip

    import nibabel as nib
    raw = gzip.decompress(data) if data[:2] == b"\x1f\x8b" else data
    return nib.Nifti1Image.from_bytes(raw)


def _refuse_quarantine(path, quarantine_root) -> None:
    from . import fetch_extract as FE   # at call time: fetch_extract imports this module
    FE.refuse_quarantine_opener(path, quarantine_root)


def load_atlas_verified(path: Path, sha256: str, quarantine_root: Path | None = None):
    """The class atlas, read once as bytes, sha256 asserted BEFORE it is parsed (else STATUS_ATLAS_IDENTITY)."""
    _refuse_quarantine(path, quarantine_root)
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != sha256:
        raise ReparcelRefused(STATUS_ATLAS_IDENTITY)
    img = nifti_from_bytes(data)
    return int_labels(np.asarray(img.dataobj)), np.asarray(img.affine, dtype=float)


# ----------------------------------------------------------------------------------------------------------------
# volume -> class atlas
# ----------------------------------------------------------------------------------------------------------------
def volume_to_parcels(vol, vol_affine, atlas, atlas_affine, parcel_ids, min_coverage: float = MIN_COVERAGE):
    """(kept ids, values, report). The atlas is resampled onto the map's grid; valid voxels are finite and non-zero;
    a parcel is kept iff it has voxels and coverage (valid / all) >= min_coverage. Order: parcel_ids'."""
    T = squeeze3(np.asarray(vol, dtype=np.float64))
    A = int_labels(atlas)
    lab = nn_resample_labels(A, np.asarray(atlas_affine, float), T.shape, np.asarray(vol_affine, float))
    valid = np.isfinite(T) & (T != 0)
    ids, vals, rows = [], [], []
    for pid in [int(p) for p in parcel_ids]:
        vox = lab == pid
        n_vox = int(vox.sum())
        n_ok = int((vox & valid).sum())
        cov = n_ok / n_vox if n_vox else 0.0
        keep = n_vox > 0 and cov >= min_coverage
        rows.append({"id": pid, "n_vox": n_vox, "n_valid": n_ok, "coverage": round(cov, 6), "kept": bool(keep)})
        if keep:
            ids.append(pid)
            vals.append(float(T[vox & valid].mean()))
    rep = {"rule": "volume", "label": LABEL_REPARCELLATED, "min_coverage": min_coverage, "parcels": rows,
           "n_kept": len(ids), "n_dropped": len(rows) - len(ids), "dropped": [r["id"] for r in rows if not r["kept"]],
           "resampling": "nearest neighbour onto the map grid (floor(v + .5); outside -> 0)"}
    return np.asarray(ids, dtype=np.int64), np.asarray(vals, dtype=float), rep


# ----------------------------------------------------------------------------------------------------------------
# fsaverage surface -> dk-ctx
# ----------------------------------------------------------------------------------------------------------------
def read_annot(path: Path, quarantine_root: Path | None = None):
    """(per-vertex label index (-1: no entry), names as str). Names are decoded as strict UTF-8, kept in memory."""
    _refuse_quarantine(path, quarantine_root)
    from nibabel.freesurfer import io as fsio
    labels, _ctab, names = fsio.read_annot(str(path))
    return np.asarray(labels, dtype=np.int64), [n.decode("utf-8") if isinstance(n, bytes) else str(n) for n in names]


def read_gifti_values(path: Path, quarantine_root: Path | None = None) -> np.ndarray:
    """RP5: exactly one data array, 1-D after squeezing."""
    _refuse_quarantine(path, quarantine_root)
    import nibabel as nib
    img = nib.load(str(path))
    if len(img.darrays) != 1:
        raise ReparcelRefused(STATUS_FS_NOT_MATCHING)
    d = np.asarray(img.darrays[0].data, dtype=np.float64).squeeze()
    if d.ndim != 1:
        raise ReparcelRefused(STATUS_FS_NOT_MATCHING)
    return d


def surface_to_dk(values, annot_labels, annot_names, dk_names, exclude=FS_EXCLUDED):
    """(kept DK names in dk_names order, values, report). Refuses (STATUS_FS_NOT_MATCHING) when the vertex counts differ
    or when, after the exclusions, not exactly len(dk_names) == 34 annot names match the DK names, each once."""
    v = np.asarray(values, dtype=np.float64)
    lab = np.asarray(annot_labels, dtype=np.int64)
    dk = list(dk_names)
    if v.ndim != 1 or lab.ndim != 1 or v.shape[0] != lab.shape[0]:
        raise ReparcelRefused(STATUS_FS_NOT_MATCHING)
    if len(dk) != N_DK_CORTICAL or len(set(dk)) != len(dk):
        raise ReparcelRefused(STATUS_FS_NOT_MATCHING)
    kept_idx = [i for i, n in enumerate(annot_names) if n not in exclude]
    dk_set = set(dk)
    match_idx = [i for i in kept_idx if annot_names[i] in dk_set]
    matched_names = [annot_names[i] for i in match_idx]
    if len(match_idx) != N_DK_CORTICAL or len(set(matched_names)) != N_DK_CORTICAL:
        raise ReparcelRefused(STATUS_FS_NOT_MATCHING)
    index_of = {annot_names[i]: i for i in match_idx}
    names_out, vals, rows = [], [], []
    for k, name in enumerate(dk):
        vert = lab == index_of[name]
        n_v = int(vert.sum())
        fin = vert & np.isfinite(v)
        n_f = int(fin.sum())
        keep = n_f > 0
        rows.append({"dk_index": k, "n_vertices": n_v, "n_finite": n_f,
                     "coverage": round(n_f / n_v, 6) if n_v else 0.0, "kept": keep})
        if keep:
            names_out.append(name)
            vals.append(float(v[fin].mean()))
    rep = {"rule": "surface", "label": LABEL_REPARCELLATED, "n_vertices": int(v.shape[0]),
           "n_annot_names": len(annot_names), "n_excluded": len(annot_names) - len(kept_idx),
           "n_matched": len(match_idx), "n_unmatched_annot_names": len(kept_idx) - len(match_idx), "parcels": rows,
           "n_kept": len(names_out), "n_dropped": len(rows) - len(names_out)}
    return names_out, np.asarray(vals, dtype=float), rep


# ----------------------------------------------------------------------------------------------------------------
# parcel values -> dk-ctx (Glasser-360 / Schaefer-400 through the source atlas volume), R15
# ----------------------------------------------------------------------------------------------------------------
_LABEL_LINE = re.compile(r"\s*(\d+)\s+(\S+)\s*")


def read_label_list(text: str) -> list[tuple[int, str]]:
    """RP4: '<integer> <name>' per line; blank lines skipped; anything else, or a repeated id, refused."""
    out, seen = [], set()
    for ln in text.splitlines():
        if not ln.strip():
            continue
        m = _LABEL_LINE.fullmatch(ln)
        if m is None:
            raise ReparcelRefused(STATUS_GLASSER)
        i = int(m.group(1))
        if i in seen:
            raise ReparcelRefused(STATUS_GLASSER)
        seen.add(i)
        out.append((i, m.group(2)))
    return out


def left_ids(label_list, prefix: str = "L_") -> list[int]:
    """R15: the left-label indices read from the label list (names starting with the prefix), never assumed."""
    return [i for i, n in label_list if n.startswith(prefix)]


def match_one_to_one(a_names, b_names) -> dict:
    """Counts only (the names stay in memory): both lists free of repeats and equal as sets."""
    a, b = list(a_names), list(b_names)
    sa, sb = set(a), set(b)
    m = len(sa & sb)
    return {"n_a": len(a), "n_b": len(b), "matched": m,
            "one_to_one": len(sa) == len(a) and len(sb) == len(b) and sa == sb}


REASON_ASSIGNED = "assigned"
REASON_OUTSIDE = "outside"
REASON_NO_MAJORITY = "no label above 50 %"
REASON_EMPTY = "empty"
RP2_RULE = ("RUN_PLAN_amend_2 R43 (RP2): assigned to the left DK cortical label holding more than 50 % of the source "
            "parcel's voxels; otherwise dropped and reported (outside-majority, or split with no label above 50 %)")


def majority_assign(src_labels, src_ids, dk_on_src, dk_ids) -> dict:
    """RP2 (R43). {src id: {"n_vox", "assigned" (dk id or None), "share", "reason"}}; reason in REASON_ASSIGNED /
    REASON_OUTSIDE / REASON_NO_MAJORITY / REASON_EMPTY. dk_ids: the left DK cortical labels; a voxel in no given label
    is 'outside'. The majority test is in integers: 2 * count > n_vox. share: the assigned label's share, else the
    largest share among the labels and outside."""
    src = np.asarray(src_labels)
    dkl = np.asarray(dk_on_src)
    if src.shape != dkl.shape:
        raise ValueError("grids differ")
    dk_ids = [int(d) for d in dk_ids]
    dk_set = set(dk_ids)
    out = {}
    for sid in [int(s) for s in src_ids]:
        vox = src == sid
        n = int(vox.sum())
        if n == 0:
            out[sid] = {"n_vox": 0, "assigned": None, "share": 0.0, "reason": REASON_EMPTY}
            continue
        u, c = np.unique(dkl[vox], return_counts=True)
        counts = {int(a): int(b) for a, b in zip(u, c) if int(a) in dk_set}
        n_out = n - sum(counts.values())
        major = [d for d, k in counts.items() if 2 * k > n]
        if major:
            out[sid] = {"n_vox": n, "assigned": major[0], "share": round(counts[major[0]] / n, 6),
                        "reason": REASON_ASSIGNED}
        elif 2 * n_out > n:
            out[sid] = {"n_vox": n, "assigned": None, "share": round(n_out / n, 6), "reason": REASON_OUTSIDE}
        else:
            best = max([n_out] + list(counts.values()))
            out[sid] = {"n_vox": n, "assigned": None, "share": round(best / n, 6), "reason": REASON_NO_MAJORITY}
    return out


def parcels_to_dk(src_values: dict, src_labels, src_affine, src_left_ids, dk_atlas, dk_affine, dk_ids):
    """(kept dk ids, values, report). src_values: {source id: value} for the left source parcels."""
    S = int_labels(src_labels)
    D = int_labels(dk_atlas)
    dk_on_src = nn_resample_labels(D, np.asarray(dk_affine, float), S.shape, np.asarray(src_affine, float))
    asg = majority_assign(S, src_left_ids, dk_on_src, dk_ids)
    acc = {int(d): [0.0, 0] for d in dk_ids}
    n_nonfinite = 0
    for sid, a in asg.items():
        if a["assigned"] is None:
            continue
        val = src_values.get(sid)
        if val is None or not np.isfinite(val):
            n_nonfinite += 1
            continue
        acc[a["assigned"]][0] += a["n_vox"] * float(val)
        acc[a["assigned"]][1] += a["n_vox"]
    ids, vals = [], []
    for d in [int(x) for x in dk_ids]:
        s, w = acc[d]
        if w > 0:
            ids.append(d)
            vals.append(s / w)
    reasons = [a["reason"] for a in asg.values()]
    rep = {"rule": "parcel values (majority > 50 %)", "rule_text": RP2_RULE, "label": LABEL_REPARCELLATED,
           "n_source": len(asg), "n_assigned": reasons.count(REASON_ASSIGNED), "n_outside": reasons.count(REASON_OUTSIDE),
           "n_no_majority": reasons.count(REASON_NO_MAJORITY), "n_empty": reasons.count(REASON_EMPTY),
           "n_source_nonfinite": n_nonfinite, "n_kept": len(ids), "n_unassigned": len(dk_ids) - len(ids),
           "dropped_source": sorted(s for s, a in asg.items() if a["assigned"] is None), "assignment": asg}
    return np.asarray(ids, dtype=np.int64), np.asarray(vals, dtype=float), rep


# ----------------------------------------------------------------------------------------------------------------
# DK-308 -> dk-ctx (Romero-Garcia)
# ----------------------------------------------------------------------------------------------------------------
_PART = re.compile(r"(.+)_part\d+")


def dk308_parent(name: str) -> str | None:
    s = name[3:] if name.startswith(("lh_", "lh.")) else name
    m = _PART.fullmatch(s)
    return m.group(1) if m else None


def dk308_to_dk(sub_values: dict, annot_labels, annot_names, dk_names):
    """(kept DK names in dk_names order, values, report). Vertex counts from the subParcellation annot (names matched
    after dropping an 'lh_' prefix); a sub-parcel without a parent in dk_names or without vertices is dropped."""
    lab = np.asarray(annot_labels, dtype=np.int64)
    idx = {(n[3:] if n.startswith(("lh_", "lh.")) else n): i for i, n in enumerate(annot_names)}
    dk = list(dk_names)
    acc = {d: [0.0, 0] for d in dk}
    n_no_parent = n_no_vertices = n_nonfinite = 0
    for name, val in sub_values.items():
        parent = dk308_parent(name)
        key = name[3:] if name.startswith(("lh_", "lh.")) else name
        if parent is None or parent not in acc:
            n_no_parent += 1
            continue
        nv = int((lab == idx[key]).sum()) if key in idx else 0
        if nv == 0:
            n_no_vertices += 1
            continue
        if val is None or not np.isfinite(val):
            n_nonfinite += 1
            continue
        acc[parent][0] += nv * float(val)
        acc[parent][1] += nv
    names, vals = [], []
    for d in dk:
        s, w = acc[d]
        if w > 0:
            names.append(d)
            vals.append(s / w)
    rep = {"rule": "DK-308 name prefix", "label": LABEL_REPARCELLATED, "n_sub": len(sub_values),
           "n_no_parent": n_no_parent, "n_no_vertices": n_no_vertices, "n_source_nonfinite": n_nonfinite,
           "n_kept": len(names), "n_unassigned": len(dk) - len(names)}
    return names, np.asarray(vals, dtype=float), rep


# ----------------------------------------------------------------------------------------------------------------
# Power spheres -> V-AAL (Buch)
# ----------------------------------------------------------------------------------------------------------------
def spheres_to_aal(centroids_mm, values, aal, aal_affine, aal_ids):
    """(kept AAL ids in aal_ids order, values, report). centroids_mm: (n, 3) world coordinates (the paper's table)."""
    if centroids_mm is None:
        raise ReparcelRefused(STATUS_ROI_UNPUBLISHED)
    xyz = np.asarray(centroids_mm, dtype=float)
    vals = np.asarray(values, dtype=float)
    if xyz.ndim != 2 or xyz.shape[1] != 3 or vals.shape != (xyz.shape[0],):
        raise ValueError("sphere table shape")
    A = int_labels(aal)
    inv = np.linalg.inv(np.asarray(aal_affine, float))
    ijk = np.floor(inv[:3, :3] @ xyz.T + inv[:3, 3:4] + 0.5).astype(np.int64)
    inside = np.all((ijk >= 0) & (ijk < np.array(A.shape)[:, None]), axis=0)
    lab = np.zeros(xyz.shape[0], dtype=np.int64)
    lab[inside] = A[ijk[0, inside], ijk[1, inside], ijk[2, inside]]
    ids_set = set(int(i) for i in aal_ids)
    in_label = np.array([int(x) in ids_set for x in lab])
    ids, out = [], []
    for a in [int(i) for i in aal_ids]:
        sel = (lab == a) & np.isfinite(vals)
        if sel.any():
            ids.append(a)
            out.append(float(vals[sel].mean()))
    rep = {"rule": "sphere centroid", "label": LABEL_REPARCELLATED, "n_spheres": int(xyz.shape[0]),
           "n_outside": int((~in_label).sum()), "dropped_spheres": [int(k) for k in np.flatnonzero(~in_label)],
           "n_nonfinite": int((in_label & ~np.isfinite(vals)).sum()), "n_kept": len(ids)}
    return np.asarray(ids, dtype=np.int64), np.asarray(out, dtype=float), rep


# ----------------------------------------------------------------------------------------------------------------
# bilateral-average maps; R14 / R31 recipe parcellation
# ----------------------------------------------------------------------------------------------------------------
def bilateral_on_left(region_values: dict, left_id_of_region: dict):
    """One value per DK region placed on its left parcel. Every region must have a left parcel."""
    ids, vals = [], []
    for region, val in region_values.items():
        if region not in left_id_of_region:
            raise ValueError("region without a left parcel")
        ids.append(int(left_id_of_region[region]))
        vals.append(float(val))
    order = np.argsort(ids)
    return np.asarray(ids, dtype=np.int64)[order], np.asarray(vals, dtype=float)[order]


def recipe_parcellation(decoded_on: str, paper_parcellation: str | None, claim_class: str) -> dict:
    """R14's general rule with R31. decoded_on: 'parcels' | 'voxels' | 'samples'.
    - parcels, named parcellation -> the paper's parcellation (the TSV row's label governs; none is set here);
    - parcels, unnamed (Benkarim, R31) -> dk-ctx, RECIPE_BENKARIM, y by the volume rule onto dk-ctx; the claim's
      class must be dk-ctx (R31), else refused;
    - voxels / samples (NeuroVault decoder fallbacks) -> the claim's analysis class, RECIPE_DECODER."""
    if decoded_on == "parcels" and paper_parcellation:
        return {"parcellation": paper_parcellation, "label": None, "y_rule": "the paper's own parcellation"}
    if decoded_on == "parcels":
        if claim_class != "dk-ctx":
            raise ValueError("R31 reads dk-ctx")
        return {"parcellation": "dk-ctx", "label": RECIPE_BENKARIM, "y_rule": "volume rule onto dk-ctx"}
    if decoded_on in ("voxels", "samples"):
        return {"parcellation": claim_class, "label": RECIPE_DECODER.format(cls=claim_class),
                "y_rule": "the claim's analysis class"}
    raise ValueError("decoded_on")
