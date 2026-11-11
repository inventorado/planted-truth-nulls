"""Pre-freeze work (claims register v4 section 3.6): the section 3.1-settings MIST64 AHBA matrix for Moreau 2020.

Same machinery as arcs/audit/src/e4_ahba_matrices.py (its FROZEN abagen 0.1.3 settings, A1 / A3 / A4 assertions and its
matrix hash), with the MIST64 volume and an atlas_info built by prereg section 2's rule from
arcs/audit/register_maps/mist64_classes.json (hemisphere by centroid, B iff |x| < 2 mm; tissue class from the atlas's own
labels; abagen structure vocabulary: cortex -> 'cortex', subcortex -> 'subcortex/brainstem', cerebellum -> 'cerebellum').
No map, no claim value is read. Outputs (gitignored): artifacts/ahba/mist64_{expr.csv.gz,report.txt,atlas_info.csv,
centroids.csv,meta.json}; a summary is written to arcs/audit/register_maps/mist64_ahba_matrix.json.

Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src_register\\mist64_ahba_matrix.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import abagen
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "arcs" / "audit" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from e4_ahba_matrices import FROZEN, DATA, centroids, git_commit, sha  # noqa: E402
from mist64_classes import load_int_atlas, VOL  # noqa: E402

OUT = ROOT / "artifacts" / "ahba"
CLASSES = ROOT / "arcs" / "audit" / "register_maps" / "mist64_classes.json"
SUMMARY = ROOT / "arcs" / "audit" / "register_maps" / "mist64_ahba_matrix.json"
STRUCT = {"cortex": "cortex", "subcortex": "subcortex/brainstem", "cerebellum": "cerebellum"}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cls = json.loads(CLASSES.read_text(encoding="utf-8"))
    img = load_int_atlas()
    info = pd.DataFrame([{"id": p["roi"], "label": p["label"], "hemisphere": p["hemisphere"],
                          "structure": STRUCT[p["tissue_class"]]} for p in cls["parcels"]])
    assert list(info["id"]) == list(range(1, 65))
    cen = centroids(img, info["id"])
    # the classes file and this run must agree on the centroid-derived hemisphere
    assert np.allclose(cen["x"].to_numpy(), [p["centroid_mni_mm"][0] for p in cls["parcels"]], atol=1e-3)
    info.to_csv(OUT / "mist64_atlas_info.csv", index=False)
    cen.to_csv(OUT / "mist64_centroids.csv", index=False)
    files = abagen.fetch_microarray(data_dir=str(DATA / "ahba"), donors="all")
    assert len(files) == 6, "A1 FAIL: %d donors" % len(files)
    expr, report = abagen.get_expression_data(img, atlas_info=info, data_dir=str(DATA / "ahba"), donors="all",
                                              return_report=True, verbose=0, **FROZEN)
    (OUT / "mist64_report.txt").write_text(report, encoding="utf-8", newline="\n")
    empty = [int(i) for i in expr.index[expr.isna().all(axis=1)]]
    assert not expr.isna().all(axis=0).any(), "A3 FAIL: all-NaN gene column"
    kept = expr.drop(index=empty)
    assert not kept.isna().any().any(), "A3 FAIL: NaN left after dropping empty parcels"
    path = OUT / "mist64_expr.csv.gz"
    expr.to_csv(path)
    back = pd.read_csv(path, index_col=0)
    assert back.shape == expr.shape and np.allclose(back.to_numpy(), expr.to_numpy(), equal_nan=True, atol=1e-12), \
        "A4 FAIL: read-back differs"
    lab = dict(zip(info["id"], info["label"]))
    hem = dict(zip(info["id"], info["hemisphere"]))
    primary = [int(i) for i in info["id"] if hem[i] in ("L", "B")]
    meta = dict(atlas="mist64", atlas_volume=str(VOL), atlas_volume_sha256=sha256_file(VOL),
                n_parcels=int(expr.shape[0]), n_genes=int(expr.shape[1]), genes_equal_15633=bool(expr.shape[1] == 15633),
                empty_parcels=empty, empty_labels=[lab[i] for i in empty], n_empty=len(empty),
                empty_primary=[lab[i] for i in empty if i in primary],
                n_primary_with_samples=len([i for i in primary if i not in empty]),
                sha256_matrix=sha(expr), sha256_expr_csv_gz=sha256_file(path), abagen=abagen.__version__,
                settings=FROZEN, commit=git_commit(),
                atlas_info_sha256=sha256_file(OUT / "mist64_atlas_info.csv"),
                classes_json_sha256=sha256_file(CLASSES),
                script="arcs/audit/src_register/mist64_ahba_matrix.py", script_sha256=sha256_file(Path(__file__)),
                python=sys.executable)
    (OUT / "mist64_meta.json").write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8")
    SUMMARY.write_text(json.dumps(meta, indent=1, default=str), encoding="utf-8", newline="\n")
    assert json.loads(SUMMARY.read_text(encoding="utf-8"))["sha256_matrix"] == meta["sha256_matrix"]
    print("mist64: parcels %d genes %d (15,633: %s) empty %d %s; primary with samples %d; sha256_matrix %s; csv.gz sha256 %s"
          % (meta["n_parcels"], meta["n_genes"], meta["genes_equal_15633"], meta["n_empty"], meta["empty_labels"],
             meta["n_primary_with_samples"], meta["sha256_matrix"], meta["sha256_expr_csv_gz"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
