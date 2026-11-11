"""ASDG-AUD-E4-apparatus, reproduction R2 (prereg §3.3): Giacomel et al. 2026 (giacomel2026cartography), spin level.

Inputs (authors' repo github.com/alegiac95/METAXCAN_TWAS_ANALYSIS @ e045bc51961b0425f51bbdf54672d59222cfa8b9,
copied to E:/data/asdg/enigma_asd/giacomel2026_repo with the repo's paths):
  combined-scheme GEDAR maps  results/<DIS>/<DIS>_TPRS_thr_<thr>.tsv   (PTRS_estimation.R: sum(expr*z)/sum(z))
  shipped cortical spin nulls results/<DIS>/<DIS>_cortical_corr_<thr>.tsv (999 Spearman rho values)
  shipped summary             results/<DIS>/<DIS>_cortical_correlations_results.tsv
  ENIGMA d-vectors            data/ENIGMA/ENIGMA_structural_organised.xlsx, sheet Thickness
  DK fsaverage5 annots        data/DK-files/atlas-DK_fsa5_{lh,rh}_aparc.annot
Procedure = their code/spatial_transcriptomics_analysis.py (generate_permutations + compute_correlation_and_pvalue):
  np.random.seed(2024); centroids = netneurotools.freesurfer.find_parcel_centroids(version='fsaverage5',
  surf='sphere', method='surface'), left hemisphere only; spins = netneurotools.stats.gen_spinsamples(
  n_rotate=1000, method='vasa', seed=2024); null_i = spearman(enigma, gedar[spins[:, i]]) for i = 1..999
  (column 0 skipped); rho = spearman(enigma, gedar); p = #{null > rho} / 1000 if rho > 0 else #{null < rho} / 1000.
Two spin generators: (A) primary = netneurotools 0.2.5 (exact routine they call) run in a throwaway venv via the
--nnt-worker mode of this script; (B) cross-check = neuromaps 0.0.7 neuromaps.nulls.spins.gen_spinsamples in the
project venv with centroids re-implemented from nibabel (same fsaverage5 sphere file, same drop list).

Gates (prereg §3.3 R2): identity iff max |null_ours - null_shipped| <= 1e-6 over all six cells;
  identical -> |rho - rho_paper| <= 0.001 and |p - p_paper| <= 0.001;
  otherwise -> |rho - rho_paper| <= 0.001 and |p - p_paper| <= 3*sqrt(2)*sqrt(p_paper(1-p_paper)/1000).
Plants (each must be caught): a 1e-5 perturbation of one shipped null value breaks identity; spins from seed 2025
break identity; rho_paper + 0.002 fails the rho clause; p shifted by tolerance + 0.001 fails the p clause.
Reconciliation descriptor (not the prereg verdict): the ASD cells are re-run on ASD_TPRS_thr_*.tsv from commit
eda33ab (the commit that last wrote the shipped ASD combined nulls/table), copied to
E:/data/asdg/enigma_asd/giacomel2026_repo_eda33ab with the repo's paths.

Usage: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e4_r2_giacomel.py [--nnt-python PATH]
       <nnt025 python> -X utf8 e4_r2_giacomel.py --nnt-worker OUT.npz   (internal)
Writes arcs/audit/results/e4_r2_giacomel.json (read back after writing).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO = Path("E:/data/asdg/enigma_asd/giacomel2026_repo")
NNT_DATA = Path("E:/data/asdg/enigma_asd/nnt_data")
SPHERE_LH = NNT_DATA / "tpl-fsaverage/fsaverage5/surf/lh.sphere"
SPHERE_RH = NNT_DATA / "tpl-fsaverage/fsaverage5/surf/rh.sphere"
ANNOT_LH = REPO / "data/DK-files/atlas-DK_fsa5_lh_aparc.annot"
ANNOT_RH = REPO / "data/DK-files/atlas-DK_fsa5_rh_aparc.annot"
XLSX = REPO / "data/ENIGMA/ENIGMA_structural_organised.xlsx"
DEFAULT_NNT_PY = Path(
    "C:/Users/info/AppData/Local/Temp/claude/d--RESEARCH/5b88368b-d4d3-46f0-820d-c5c29d4c70ea/scratchpad/nnt025/Scripts/python.exe")
N_ROT, SEED, N_CORT = 1000, 2024, 34
ID_TOL, RHO_TOL, P_TOL_ID = 1e-6, 0.001, 0.001
# prereg §3.3 R2: paper values (combined scheme, cortical)
PAPER = {("MDD", 10): (0.529, 0.005), ("MDD", 5): (0.546, 0.003), ("MDD", 1): (0.531, 0.003),
         ("ASD", 1): (-0.150, 0.252), ("ASD", 5): (0.413, 0.073), ("ASD", 10): (-0.053, 0.423)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def f_map(d, t): return REPO / f"results/{d}/{d}_TPRS_thr_{t}.tsv"
def f_null(d, t): return REPO / f"results/{d}/{d}_cortical_corr_{t}.tsv"
def f_table(d): return REPO / f"results/{d}/{d}_cortical_correlations_results.tsv"


REPO_OLD = Path("E:/data/asdg/enigma_asd/giacomel2026_repo_eda33ab")
OLD_COMMIT = "eda33abddd5acd396caa0ace2817a0bcd427cfe5"


def f_map_old(d, t): return REPO_OLD / f"results/{d}/{d}_TPRS_thr_{t}.tsv"


# ---------------------------------------------------------------- worker (runs in the netneurotools 0.2.5 venv)
def nnt_worker(out: str) -> None:
    import netneurotools
    import scipy
    from netneurotools import freesurfer, stats
    os.environ.setdefault("NNT_DATA", str(NNT_DATA))
    np.random.seed(SEED)  # as in generate_permutations (global state; not consumed by the cortical spins)
    cen, hemi = freesurfer.find_parcel_centroids(lhannot=str(ANNOT_LH), rhannot=str(ANNOT_RH), version="fsaverage5",
                                                 surf="sphere", method="surface")
    left = hemi == 0
    cen, hemi = cen[left], hemi[left]
    spins = stats.gen_spinsamples(cen, hemi, n_rotate=N_ROT, method="vasa", seed=SEED)
    spins_2025 = stats.gen_spinsamples(cen, hemi, n_rotate=N_ROT, method="vasa", seed=SEED + 1)  # plant
    np.savez(out, centroids=cen, spins=spins, spins_2025=spins_2025,
             fsignore=np.array(list(freesurfer.FSIGNORE)),
             versions=np.array([f"netneurotools={netneurotools.__version__}", f"numpy={np.__version__}",
                                f"scipy={scipy.__version__}", f"python={sys.version.split()[0]}"]))


# ---------------------------------------------------------------- neuromaps cross-check (project venv)
def centroids_nibabel(drop):
    """Re-implementation of netneurotools 0.2.5 find_parcel_centroids(method='surface'), left hemisphere only."""
    from nibabel.freesurfer import read_annot, read_geometry
    from scipy.spatial.distance import cdist
    vertices, _ = read_geometry(str(SPHERE_LH))
    labels, _, names = read_annot(str(ANNOT_LH))
    names = [n.decode() if isinstance(n, bytes) else n for n in names]
    cen, kept = [], []
    for lab in np.unique(labels):
        if names[lab] in drop:
            continue
        roi = np.atleast_2d(vertices[labels == lab].mean(axis=0))
        cen.append(vertices[np.argmin(cdist(vertices, roi), axis=0)[0]])
        kept.append(names[lab])
    return np.vstack(cen), kept


def spearman(x, y) -> float:
    from scipy.stats import spearmanr
    return float(spearmanr(x, y).correlation)


def null_and_p(enigma, gedar, spins):
    """Their compute_correlation_and_pvalue on their generate_permutations output (cortex only)."""
    permuted = np.asarray(gedar[spins]).reshape(N_CORT, spins.shape[1])
    rho = spearman(enigma, gedar)
    null = np.array([spearman(enigma, permuted[:, i]) for i in range(1, permuted.shape[1])])
    idx = np.where((null > rho) if rho > 0 else (null < rho))[0]
    return rho, len(idx) / permuted.shape[1], null


def gate_identity(ours: dict, shipped: dict) -> tuple[bool, float]:
    d = max(float(np.max(np.abs(ours[k] - shipped[k]))) if ours[k].shape == shipped[k].shape else math.inf
            for k in shipped)
    return d <= ID_TOL, d


def p_tol(identical: bool, p_paper: float) -> float:
    return P_TOL_ID if identical else 3 * math.sqrt(2) * math.sqrt(p_paper * (1 - p_paper) / N_ROT)


def gate_cell(rho, p, rho_paper, p_paper, identical):
    tol = p_tol(identical, p_paper)
    rho_ok = abs(rho - rho_paper) <= RHO_TOL + 1e-12
    p_ok = abs(p - p_paper) <= tol + 1e-12
    return rho_ok, p_ok, tol


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nnt-worker", default=None)
    ap.add_argument("--nnt-python", default=str(DEFAULT_NNT_PY))
    a = ap.parse_args()
    if a.nnt_worker:
        nnt_worker(a.nnt_worker)
        return

    import nibabel
    import pandas as pd
    import scipy
    import neuromaps
    from neuromaps.nulls.spins import gen_spinsamples as nm_gen_spinsamples

    root = Path(__file__).resolve().parents[3]
    script = Path(__file__).resolve()

    # ---- run the netneurotools 0.2.5 worker (primary spins)
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "nnt.npz"
        env = dict(os.environ, NNT_DATA=str(NNT_DATA))
        env.pop("SUBJECTS_DIR", None)
        env.pop("FREESURFER_HOME", None)
        r = subprocess.run([a.nnt_python, "-X", "utf8", str(script), "--nnt-worker", str(out)], env=env,
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"nnt worker failed:\n{r.stderr}")
        with np.load(out) as z:
            cen_nnt, spins, spins_2025 = z["centroids"], z["spins"], z["spins_2025"]
            fsignore = [str(s) for s in z["fsignore"]]
            nnt_versions = [str(s) for s in z["versions"]]
    nnt_freeze = subprocess.run(["uv", "pip", "freeze", "--python", a.nnt_python], capture_output=True,
                                text=True).stdout.split()

    # ---- apparatus assertions on loads
    assert cen_nnt.shape == (N_CORT, 3), cen_nnt.shape
    assert spins.shape == (N_CORT, N_ROT) and spins_2025.shape == (N_CORT, N_ROT)
    assert all(sorted(spins[:, i]) == list(range(N_CORT)) for i in range(N_ROT)), "vasa spins must be permutations"
    xl = pd.read_excel(XLSX, sheet_name="Thickness", index_col=0)
    assert xl.shape[0] == N_CORT, xl.shape
    xl_names = [s.replace("M_", "", 1).replace("_thickavg", "") for s in xl.index]
    cen_nb, kept = centroids_nibabel(set(fsignore))
    assert kept == xl_names, "annot parcel order != ENIGMA sheet order"
    centroid_maxdiff = float(np.max(np.abs(cen_nb - cen_nnt)))
    spins_nm = nm_gen_spinsamples(cen_nb, np.zeros(N_CORT, dtype=int), n_rotate=N_ROT, method="vasa", seed=SEED)
    spins_nm_equal = bool(np.array_equal(spins_nm, spins))

    cells, ours, ours_nm, ours_2025, shipped, loads = [], {}, {}, {}, {}, {}
    for (dis, thr), (rho_paper, p_paper) in PAPER.items():
        g = pd.read_csv(f_map(dis, thr), sep="\t")
        c = g[(g["hemisphere"] == "L") & (g["structure"] == "cortex")]
        assert len(c) == N_CORT and list(c["label"]) == xl_names, f"{dis} {thr}: GEDAR rows/labels"
        assert c["weighted_avg"].notna().all()
        enigma = xl[dis].dropna().to_numpy()
        assert len(enigma) == N_CORT
        gedar = c["weighted_avg"].to_numpy()
        null_ship = np.loadtxt(f_null(dis, thr))
        assert null_ship.shape == (N_ROT - 1,), null_ship.shape
        tab = pd.read_csv(f_table(dis), sep="\t")
        trow = tab[np.isclose(tab["threshold"], float(thr))]
        assert len(trow) == 1
        rho, p, null = null_and_p(enigma, gedar, spins)
        rho_nm, p_nm, null_nm = null_and_p(enigma, gedar, spins_nm)
        _, p_25, null_25 = null_and_p(enigma, gedar, spins_2025)
        k = f"{dis}_{thr}"
        ours[k], ours_nm[k], ours_2025[k], shipped[k] = null, null_nm, null_25, null_ship
        # their p recomputed from their shipped null and their table rho (checks our reading of their p definition)
        rho_t = float(trow["corr"].iloc[0])
        idx = np.where((null_ship > rho_t) if rho_t > 0 else (null_ship < rho_t))[0]
        cells.append(dict(disorder=dis, threshold_pct=thr, rho_paper=rho_paper, p_paper=p_paper,
                          rho_table=float(trow["corr"].iloc[0]), p_table=float(trow["p"].iloc[0]),
                          rho_ours=rho, p_ours=p, p_from_shipped_null=len(idx) / N_ROT,
                          rho_neuromaps=rho_nm, p_neuromaps=p_nm,
                          null_maxabs_diff_vs_shipped=float(np.max(np.abs(null - null_ship))),
                          null_maxabs_diff_neuromaps_vs_shipped=float(np.max(np.abs(null_nm - null_ship)))))
        loads[k] = dict(map=str(f_map(dis, thr).relative_to(REPO)).replace("\\", "/"),
                        null=str(f_null(dis, thr).relative_to(REPO)).replace("\\", "/"))

    identical, id_maxdiff = gate_identity(ours, shipped)
    identical_nm, id_maxdiff_nm = gate_identity(ours_nm, shipped)
    for c in cells:
        c["rho_pass"], c["p_pass"], c["p_tolerance"] = gate_cell(c["rho_ours"], c["p_ours"], c["rho_paper"],
                                                               c["p_paper"], identical)
        c["rho_tolerance"] = RHO_TOL
        c["abs_rho_diff"] = abs(c["rho_ours"] - c["rho_paper"])
        c["abs_p_diff"] = abs(c["p_ours"] - c["p_paper"])
        c["pass"] = bool(c["rho_pass"] and c["p_pass"])
        # descriptor: paper values are the table values cut to 3 decimals (rounded or truncated -> |diff| < 0.001)
        c["table_matches_paper_3dp"] = bool(abs(c["rho_table"] - c["rho_paper"]) < 0.001
                                            and abs(c["p_table"] - c["p_paper"]) < 0.001)
    overall = bool(all(c["pass"] for c in cells))

    # ---- reconciliation (NOT the prereg verdict): ASD combined maps at the commit that produced the shipped
    # ASD combined nulls/results table (eda33ab, 2024-04-16). Commit 94df223 (2024-04-30) regenerated
    # ASD_TPRS_thr_*.tsv without re-running the combined correlations; the pinned commit carries the newer maps.
    recon_cells, recon_ours, recon_ship = [], {}, {}
    for (dis, thr), (rho_paper, p_paper) in PAPER.items():
        if dis != "ASD":
            continue
        g = pd.read_csv(f_map_old(dis, thr), sep="\t")
        c = g[(g["hemisphere"] == "L") & (g["structure"] == "cortex")]
        assert len(c) == N_CORT and list(c["label"]) == xl_names
        enigma = xl[dis].dropna().to_numpy()
        rho, p, null = null_and_p(enigma, c["weighted_avg"].to_numpy(), spins)
        k = f"{dis}_{thr}"
        recon_ours[k], recon_ship[k] = null, shipped[k]
        recon_cells.append(dict(disorder=dis, threshold_pct=thr, rho_paper=rho_paper, p_paper=p_paper,
                                rho_ours=rho, p_ours=p,
                                null_maxabs_diff_vs_shipped=float(np.max(np.abs(null - shipped[k])))))
    recon_identical, recon_maxdiff = gate_identity(recon_ours, recon_ship)
    for c in recon_cells:
        c["rho_pass"], c["p_pass"], c["p_tolerance"] = gate_cell(c["rho_ours"], c["p_ours"], c["rho_paper"],
                                                               c["p_paper"], recon_identical)
        c["pass"] = bool(c["rho_pass"] and c["p_pass"])
    reconciliation = dict(
        note="Descriptor for the K2 'unless reconciled to a documented source difference' clause; the prereg "
             "verdict is overall_R2_pass on the pinned-commit inputs.",
        source=f"ASD_TPRS_thr_<thr>.tsv at alegiac95/METAXCAN_TWAS_ANALYSIS@{OLD_COMMIT}",
        documented_difference="commit 94df2231248134ea083aa3ddc4bb01baf8df1171 (2024-04-30, 'Add top up and down "
                              "regulated genes + abs results') modified results/ASD/ASD_TPRS_thr_{0.1,0.5,1,5,10}.tsv "
                              "but not ASD_cortical_corr_*.tsv or ASD_cortical_correlations_results.tsv (last "
                              "changed in eda33ab, 2024-04-16); MDD_TPRS_thr_* last changed in eda33ab",
        identical=recon_identical, max_abs_diff=recon_maxdiff, cells=recon_cells,
        all_asd_cells_pass=bool(all(c["pass"] for c in recon_cells)),
        inputs={str(f_map_old("ASD", t).relative_to(REPO.parent)).replace("\\", "/"): sha256(f_map_old("ASD", t))
                for t in (1, 5, 10)})
    reconciliation["mdd_cells_pass_pinned"] = bool(all(c["pass"] for c in cells if c["disorder"] == "MDD"))
    reconciliation["R2_pass_if_reconciled"] = bool(reconciliation["all_asd_cells_pass"]
                                                   and reconciliation["mdd_cells_pass_pinned"])

    # ---- plants (each must be caught)
    k0 = next(iter(shipped))
    pert = {k: v.copy() for k, v in shipped.items()}
    pert[k0][17] += 1e-5
    plant_perturbed_identity, _ = gate_identity(pert, shipped)
    plant_seed_identity, plant_seed_diff = gate_identity(ours_2025, shipped)
    c0 = cells[0]
    rho_plant_ok, _, _ = gate_cell(c0["rho_paper"] + 0.002, c0["p_paper"], c0["rho_paper"], c0["p_paper"], identical)
    tol0 = p_tol(identical, c0["p_paper"])
    _, p_plant_ok, _ = gate_cell(c0["rho_paper"], c0["p_paper"] + tol0 + 0.001, c0["rho_paper"], c0["p_paper"],
                                 identical)
    _, p_plant_ok_nonid, _ = gate_cell(c0["rho_paper"], c0["p_paper"] + p_tol(False, c0["p_paper"]) + 0.001,
                                       c0["rho_paper"], c0["p_paper"], False)
    plants = {
        "null_value_perturbed_1e-5_breaks_identity": dict(caught=not plant_perturbed_identity),
        "spins_seed_2025_break_identity": dict(caught=not plant_seed_identity, max_abs_diff=plant_seed_diff),
        "rho_paper_plus_0.002_fails_rho_clause": dict(caught=not rho_plant_ok),
        "p_shifted_beyond_tolerance_fails_p_clause_identical_branch": dict(caught=not p_plant_ok),
        "p_shifted_beyond_tolerance_fails_p_clause_nonidentical_branch": dict(caught=not p_plant_ok_nonid),
    }
    plants_all_caught = all(v["caught"] for v in plants.values())

    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", str(script)],
                           capture_output=True, text=True).stdout.strip()
    inputs = [XLSX, ANNOT_LH, ANNOT_RH, SPHERE_LH, SPHERE_RH, f_table("MDD"), f_table("ASD"),
              REPO / "code/spatial_transcriptomics_analysis.py", REPO / "code/PTRS_estimation.R"]
    inputs += [f_map(d, t) for d, t in PAPER] + [f_null(d, t) for d, t in PAPER]
    res = dict(
        id="ASDG-AUD-E4-apparatus / R2 Giacomel 2026 (prereg §3.3)",
        citation="giacomel2026cartography",
        source_repo="github.com/alegiac95/METAXCAN_TWAS_ANALYSIS@e045bc51961b0425f51bbdf54672d59222cfa8b9",
        scheme_mapping=dict(combined="<DIS>_TPRS_thr_<thr>.tsv / <DIS>_cortical_corr_<thr>.tsv / "
                                     "<DIS>_cortical_correlations_results.tsv",
                            up_only="_TPRS_pos_ / _cortical_top_pos_", down_only="_TPRS_neg_ / _cortical_top_neg_",
                            abs_not_in_paper="_TPRS_abs_ / _cortical_abs_"),
        procedure=dict(spins="netneurotools 0.2.5 stats.gen_spinsamples(method='vasa', n_rotate=1000, seed=2024)",
                       centroids="netneurotools 0.2.5 freesurfer.find_parcel_centroids(fsaverage5, sphere, surface), "
                                 "left hemisphere (34)",
                       null="Spearman(enigma, gedar[spins[:, i]]) for i=1..999",
                       p="one-sided in sign of rho: #{null > rho}/1000 if rho>0 else #{null < rho}/1000 (their code)"),
        identity=dict(identical=identical, max_abs_diff=id_maxdiff, tolerance=ID_TOL,
                      neuromaps_identical=identical_nm, neuromaps_max_abs_diff=id_maxdiff_nm,
                      neuromaps_spins_equal_nnt025_spins=spins_nm_equal,
                      centroid_max_abs_diff_nibabel_vs_nnt025=centroid_maxdiff),
        branch="identical: rho +-0.001, p +-0.001" if identical else
               "not identical: rho +-0.001, p +- 3*sqrt(2)*sqrt(p(1-p)/1000)",
        cells=cells, overall_R2_pass=overall, reconciliation=reconciliation,
        plants=plants, plants_all_caught=plants_all_caught,
        versions=dict(main=[f"python={sys.version.split()[0]}", f"numpy={np.__version__}",
                            f"scipy={scipy.__version__}", f"pandas={pd.__version__}",
                            f"nibabel={nibabel.__version__}", f"neuromaps={neuromaps.__version__}"],
                      nnt_worker=nnt_versions, nnt_worker_python=a.nnt_python, nnt_worker_freeze=nnt_freeze),
        inputs={str(p.relative_to(REPO.parent)).replace("\\", "/"): sha256(p) for p in inputs},
        loads=loads,
        script=str(script.relative_to(root)).replace("\\", "/"), script_sha256=sha256(script),
        git_head=head, script_dirty_vs_head=bool(dirty),
    )
    out = root / "arcs/audit/results/e4_r2_giacomel.json"
    txt = json.dumps(res, indent=2, ensure_ascii=False)
    out.write_bytes((txt + "\n").encode("utf-8"))
    back = json.loads(out.read_bytes().decode("utf-8"))
    assert back == json.loads(txt), "read-back mismatch"
    for c in cells:
        print(f"{c['disorder']} {c['threshold_pct']:>2}%  rho paper {c['rho_paper']:+.3f} ours {c['rho_ours']:+.4f}  "
              f"p paper {c['p_paper']:.3f} ours {c['p_ours']:.3f}  tol {c['p_tolerance']:.4f}  "
              f"null maxdiff {c['null_maxabs_diff_vs_shipped']:.2e}  pass {c['pass']}")
    print(f"identical={identical} maxdiff={id_maxdiff:.3e}  neuromaps identical={identical_nm} "
          f"spins equal={spins_nm_equal} centroid diff={centroid_maxdiff:.2e}")
    print(f"plants caught={plants_all_caught} {json.dumps(plants)}")
    for c in recon_cells:
        print(f"[recon {OLD_COMMIT[:7]}] {c['disorder']} {c['threshold_pct']:>2}%  rho {c['rho_ours']:+.4f}  "
              f"p {c['p_ours']:.3f}  null maxdiff {c['null_maxabs_diff_vs_shipped']:.2e}  pass {c['pass']}")
    print(f"[recon] identical={recon_identical} maxdiff={recon_maxdiff:.3e} "
          f"R2_pass_if_reconciled={reconciliation['R2_pass_if_reconciled']}")
    print(f"OVERALL R2 pass={overall}  -> {out}")


if __name__ == "__main__":
    main()
