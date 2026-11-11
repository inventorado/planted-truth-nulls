"""WP4 phase 1: SYNTHETIC stand-ins of every G2 input, shaped as the frozen texts declare them (RUN_PLAN.md §11; the
TSV's map texts; the incorporated drafts; the DRAFT RUN_PLAN_amend_4.md R51-R64), a scratch identity record in
IDENTITY_prefreeze.json's record format, and a fake network serving them. Nothing here opens a G2 carrier: the only
real files read are reference files allowed in phase 1 (abagen's DK atlas volume and the pinned dk_atlas_info.csv,
the AHBA dk matrix's column names).

Planted, for the print-rule checks: identifier-shaped strings (digit runs of 9 generated at run time) in undeclared
sheets, in undeclared columns and in a decoder column; none may reach any output.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd

from . import identity as ID
from . import wp4_layout as L
from . import wp4_read as RD

GH = "https://github.com/{repo}/blob/{commit}/{path}"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def planted_id(rng) -> str:
    return "".join(str(int(d)) for d in rng.integers(1, 10, 9))


def dk_table() -> pd.DataFrame:
    return RD.dk_frame((L.REPO / "artifacts/ahba/dk_atlas_info.csv").read_bytes())


def dk_names(dk, hemi: str, structure: str) -> list[str]:
    return [str(x) for x in dk[(dk["hemisphere"] == hemi) & (dk["structure"] == structure)]["label"]]


def dk_genes(n: int = 600, seed: int = 0) -> list[str]:
    """n column names of the AHBA dk matrix (header only) - real gene symbols, so gated sets reach the class
    universes of the runner's contexts."""
    with gzip.open(L.REPO / "artifacts/ahba/dk_expr.csv.gz", "rt", encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split(",")[1:]
    rng = np.random.default_rng(seed)
    return sorted(rng.choice(header, n, replace=False).tolist())


def hgnc_table(genes: list[str]) -> bytes:
    rows = [{"hgnc_id": f"HGNC:{k + 1}", "symbol": g, "status": "Approved", "prev_symbol": "", "alias_symbol": "",
             "ensembl_gene_id": f"ENSG{k:011d}", "entrez_id": str(1000 + k), "uniprot_ids": "", "rna_central_id": ""}
            for k, g in enumerate(genes)]
    return pd.DataFrame(rows).to_csv(sep="\t", index=False, lineterminator="\n").encode("utf-8")


# ---- R16: the annot and a tar stream --------------------------------------------------------------------------------
def annot_bytes(dk, n_vert: int = 680, seed: int = 1) -> tuple[bytes, np.ndarray]:
    import tempfile
    from nibabel.freesurfer import io as fsio
    names = ["unknown"] + dk_names(dk, "L", "cortex") + ["corpuscallosum"]
    lab = np.repeat(np.arange(len(names)), int(np.ceil(n_vert / len(names))))[:n_vert]
    np.random.default_rng(seed).shuffle(lab)
    ctab = np.zeros((len(names), 5), dtype=np.int32)
    ctab[:, :3] = np.arange(len(names))[:, None] % 255
    ctab[:, 4] = ctab[:, 0] + ctab[:, 1] * 256 + ctab[:, 2] * 65536
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "lh.aparc.annot"
        fsio.write_annot(str(p), lab, ctab, [n.encode() for n in names], fill_ctab=True)
        return p.read_bytes(), lab


def tar_stream(member_bytes: bytes, *, regular: bool = True, planted: str = "") -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, data in ((f"freesurfer/bin/tool_{planted}", b"x" * 10), ("freesurfer/README", b"readme")):
            ti = tarfile.TarInfo(name)
            ti.size = len(data)
            tf.addfile(ti, io.BytesIO(data))
        ti = tarfile.TarInfo("freesurfer/" + "subjects/fsaverage/label/lh.aparc.annot")
        if regular:
            ti.size = len(member_bytes)
            tf.addfile(ti, io.BytesIO(member_bytes))
        else:
            ti.type = tarfile.SYMTYPE
            ti.linkname = "/abs/elsewhere"
            tf.addfile(ti)
    return buf.getvalue()


# ---- R15: a synthetic HCP-MMP1 volume (each left DK cortical parcel split into sub-parcels) -----------------------
def hcp_volume(dk) -> tuple[bytes, str, list[str]]:
    import nibabel as nib
    from . import reparcel as RP
    path = L.main_repository(L.REPO) / "env/venv/Lib/site-packages/abagen/data/atlas-desikankilliany.nii.gz"
    A, aff = RP.load_atlas_verified(path, "0a28c93f5967f0892810219e68edb32abcaa9fd796a217096512fb0724c20d8a")
    Ad = A[::2, ::2, ::2]
    aff2 = aff.copy()
    aff2[:3, :3] = aff[:3, :3] * 2
    out = np.zeros_like(Ad, dtype=np.int32)
    names: list[str] = []
    rng = np.random.default_rng(15)
    for hemi, pref, base in (("L", "L_", 0), ("R", "R_", 180)):
        ids = [int(i) for i in dk[(dk["hemisphere"] == hemi) & (dk["structure"] == "cortex")]["id"]]
        k_each = [5] * len(ids)
        extra = 180 - sum(k_each)
        for j in range(abs(extra)):
            k_each[j % len(ids)] += 1 if extra > 0 else -1
        nid = base
        for did, k in zip(ids, k_each):
            vox = np.argwhere(Ad == did)
            order = np.argsort(vox[:, 2] + 0.01 * rng.random(len(vox)))
            parts = np.array_split(vox[order], k)
            for part in parts:
                nid += 1
                out[tuple(part.T)] = nid
                names.append(f"{pref}P{nid - base:03d}_ROI")
    img = nib.Nifti1Image(out, aff2)
    data = gzip.compress(img.to_bytes(), mtime=0)
    text = "\n".join(f"{i + 1} {n}" for i, n in enumerate(names)) + "\n"
    return data, text, [n for n in names if n.startswith("L_")]


# ---- Patel: a 26-page PDF, eTable 4 on page index 25 --------------------------------------------------------------
def patel_pdf(path: Path, dk, values: list[float], *, drop_row: bool = False) -> None:
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["pdf.fonttype"] = 42
    from matplotlib.backends.backend_pdf import PdfPages
    import matplotlib.pyplot as plt
    names = dk_names(dk, "L", "cortex")
    spaced = {"caudalanteriorcingulate": "caudal anterior cingulate", "lateraloccipital": "lateral occipital"}
    with PdfPages(str(path)) as pdf:
        for k in range(25):
            fig = plt.figure(figsize=(8.5, 11))
            fig.text(0.1, 0.9, f"page {k + 1}", fontsize=8)
            pdf.savefig(fig)
            plt.close(fig)
        fig = plt.figure(figsize=(8.5, 11))
        fig.text(0.08, 0.95, "eTable 4. Summary statistics from meta-analysis of difference", fontsize=6)
        xs = (0.08, 0.40, 0.50, 0.60, 0.70, 0.80)
        for x, h in zip(xs, ("Region", "Estimate", "SE", "p", "FDRp", "N")):
            fig.text(x, 0.92, h, fontsize=6)
        y = 0.90
        for j, (n, v) in enumerate(zip(names, values)):
            if drop_row and j == 3:
                continue
            row = (spaced.get(n, n), f"{v:.4f}".replace("-", "−"), "0.0100", "0.0300", "0.0500", "3497")
            for x, t in zip(xs, row):
                fig.text(x, y, t, fontsize=6)
            y -= 0.022
        fig.text(0.08, y - 0.02, "Abbreviations: SE standard error", fontsize=5)
        pdf.savefig(fig)
        plt.close(fig)


# ---- Giacomel's workbook -----------------------------------------------------------------------------------------------
def giacomel_xlsx(path: Path, dk, asd_t, mdd_t, asd_s, mdd_s, planted: str, *, order_swap: bool = False) -> None:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Thickness"
    ws.append(["", "ADHD", "ASD", "MDD", "SCZ"])
    for n, a, m in zip(dk_names(dk, "L", "cortex"), asd_t, mdd_t):
        ws.append([f"M_{n}_thickavg", 0.1, float(a), float(m), 0.2])
    ws2 = wb.create_sheet("Subcortical")
    ws2.append(["", "ASD", "MDD", "BD"])
    labs = ["Maccumb", "Mamyg", "Mcaud", "Mhippo", "Mpal", "Mput", "Mthal"]
    if order_swap:
        labs[0], labs[1] = labs[1], labs[0]
    for lab, a, m in zip(labs, asd_s, mdd_s):
        ws2.append([lab, float(a), float(m), 0.3])
    ws3 = wb.create_sheet(f"subj_{planted}")
    ws3.append(["participant", planted])
    wb.save(str(path))


# ---- ENIGMA Toolbox tables (Liu T3) -------------------------------------------------------------------------------
def enigma_cortthick(dk, rng) -> bytes:
    rows = ["Structure,d_icv,se_icv,low_ci_icv,up_ci_icv,n_controls,n_patients,pobs,fdr_p"]
    for hemi in ("L", "R"):
        for n in dk_names(dk, "L", "cortex"):
            rows.append(f"{hemi}_{n}_thickavg,{rng.normal(0, .1):.5f},0.03,-0.1,0.1,976,1060,0.5,0.6")
    return ("\n".join(rows) + "\n").encode("utf-8")


def enigma_subvol(rng) -> bytes:
    rows = ["Structure,d_icv,se_icv,low_ci_icv,up_ci_icv,n_controls,n_patients,pobs,fdr_p"]
    for hemi in ("L", "R"):
        for n in ("accumb", "amyg", "caud", "hippo", "pal", "put", "thal", "LatVent"):
            rows.append(f"{hemi}{n},{rng.normal(0, .1):.5f},0.03,-0.1,0.1,976,1060,0.5,0.6")
    return ("\r\n".join(rows) + "\r\n").encode("utf-8")


# ---- Hansen ---------------------------------------------------------------------------------------------------------
def cammoun_info(dk) -> tuple[bytes, list[str]]:
    rng = np.random.default_rng(19)
    left = dk_names(dk, "L", "cortex")
    order = list(rng.permutation(left))
    rows = ["id,label,scale,hemisphere,structure"]
    k = 0
    for hemi, names in (("R", order), ("L", order)):
        for n in names:
            k += 1
            rows.append(f"{k},{n},scale033,{hemi},cortex")
    for n in ("thalamus", "caudate"):
        k += 1
        rows.append(f"{k},{n},scale033,L,subcortex")
    for j in range(5):
        k += 1
        rows.append(f"{k},region{j},scale060,L,cortex")
    return ("\n".join(rows) + "\n").encode("utf-8"), order


def hansen_files(rng) -> dict:
    ct = rng.normal(0, 0.1, (68, 13))
    pc1 = rng.normal(0, 1, 68)
    X = rng.normal(0, 1, (68, 7))
    X[:, 4] = (pc1 - pc1.mean()) / pc1.std()
    ct_b = ("\r\n".join(",".join(f"{v:.6f}" for v in r) for r in ct) + "\r\n").encode("utf-8")
    pc1_b = ("\r\n".join(f"{v:.6f}" for v in pc1) + "\r\n").encode("utf-8")
    hdr = "receptor_pc1,ei_ratio,glycolytic,glucose,gene_pc1,synapse,myelin"
    X_b = (hdr + "\n" + "\n".join(",".join(f"{v:.8f}" for v in r) for r in X) + "\n").encode("utf-8")
    return dict(ct=ct_b, pc1=pc1_b, pred=X_b, ct_values=ct, pc1_values=pc1)


# ---- Pretzsch -------------------------------------------------------------------------------------------------------------
def pretzsch_csv(left_names: list[str], rng) -> bytes:
    rows = ["region,area_id,area_label,hemisphere,CT_loading,SA_loading"]
    for n in left_names:
        ct, sa = rng.normal(0, 1), rng.normal(0, 1)
        rows.append(f"{n},{1 + len(rows) % 22},Area,L,{ct:.6f},{sa:.6f}")
        rows.append(f"R{n[1:]},{1 + len(rows) % 22},Area,R,{ct:.6f},{sa:.6f}")
    return ("\n".join(rows) + "\n").encode("utf-8")


# ---- GIFTI ------------------------------------------------------------------------------------------------------------------
def gifti_bytes(values: np.ndarray) -> bytes:
    import tempfile
    import nibabel as nib
    img = nib.gifti.GiftiImage(darrays=[nib.gifti.GiftiDataArray(values.astype(np.float32))])
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "x.func.gii"
        nib.save(img, str(p))
        return p.read_bytes()


# ---- Giacomel repository lists / GEDAR maps / decoder ---------------------------------------------------------------
def list_tsv(genes: list[str], rng, *, weights: str = "z_mean", sign: int = 0, planted: str = "") -> bytes:
    hdr = ["gene", "gene_name", weights, "pvalue", "note"]
    rows = ["\t".join(hdr)]
    for k, g in enumerate(genes):
        z = abs(rng.normal(3, 1)) * (sign if sign else (1 if k % 3 else -1))
        rows.append("\t".join([f"ENSG{k:011d}" if False else "", g, f"{z:.5f}", "0.001", planted if k == 0 else ""]))
    return ("\n".join(rows) + "\n").encode("utf-8")


def gedar_tsv(dk, rng, *, by_names: bool) -> bytes:
    rows = ["region\tTPRS"]
    for _, r in dk.iterrows():
        lab = f"{r['hemisphere']}_{r['label']}" if by_names else str(int(r["id"]))
        if by_names and r["hemisphere"] == "B":
            continue
        rows.append(f"{lab}\t{rng.normal(0, 1):.6f}")
    return ("\n".join(rows) + "\n").encode("utf-8")


def decoder_json(genes: list[str], rng, planted: str) -> bytes:
    from . import wp3_layout as W3
    data = []
    for k, g in enumerate(genes):
        p = float(rng.random() ** 2)
        data.append([g, 1000 + k, f"name {planted}" if k == 0 else "name", float(rng.normal()), p, min(1.0, p * 3),
                     0.1, 0.01])
    return json.dumps({"columns": list(W3.DECODER_COLUMNS), "data": data}).encode("utf-8")


# ================================================================================================================
# the scratch layout
# ================================================================================================================
def build(root: Path, *, seed: int = 4) -> dict:
    """Writes every stand-in under root; returns {"roots": wp4_layout.Roots, "net": {url: bytes}, "facts": ...}."""
    root = Path(root)
    rng = np.random.default_rng(seed)
    planted = planted_id(rng)
    dk = dk_table()
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    genes = dk_genes(600, seed)
    hg_b = hgnc_table(genes)
    (data / "hgnc.txt").write_bytes(hg_b)
    net: dict = {}
    records = []
    facts: dict = {"planted": planted, "genes": genes}

    def local(obj, rel: str, b: bytes, *, tree_url: str | None = None, lf_blob: bool = False, extra=()):
        p = data / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
        f = ID.facts_of_bytes(b)
        probes = [{"method": "local file already on disk (hashed only, not parsed)", "status": "ok", "path": str(p),
                   "size": len(b), "sha256": f["sha256"], "git_blob_sha": f["git_blob"],
                   **({"git_blob_sha_crlf_to_lf": f["git_blob_lf"]} if lf_blob else {})}]
        if tree_url:
            probes.append({"method": "GitHub git-tree listing (recursive)", "status": "ok", "url": tree_url,
                           "blob_sha": f["git_blob_lf"] if lf_blob else f["git_blob"],
                           "size": f["bytes_lf"] if lf_blob else len(b)})
        records.append({"object": obj, "probes": probes + list(extra)})
        return p

    # Patel
    patel_vals = list(rng.normal(-0.02, 0.01, 34))
    pp = data / "patel/supp/etable.pdf"
    pp.parent.mkdir(parents=True, exist_ok=True)
    patel_pdf(pp, dk, patel_vals)
    local(L.IDENTITY_OBJECT[L.PATEL_KEY], "patel/supp/etable.pdf", pp.read_bytes())
    facts["patel_values"] = patel_vals
    # Giacomel: the governing download and the local comparison copy
    asd_t, mdd_t = rng.normal(0, .1, 34), rng.normal(0, .1, 34)
    asd_s, mdd_s = rng.normal(0, .1, 7), rng.normal(0, .1, 7)
    gx = root / "net_gia_gov.xlsx"
    giacomel_xlsx(gx, dk, asd_t, mdd_t, asd_s, mdd_s, planted)
    gov_b = gx.read_bytes()
    gf = ID.facts_of_bytes(gov_b)
    gov_url = L.RAW_URL.format(repo=L.GIA_REPO, commit=L.GIA_93DE089, path=L.GIA_XLSX_PATH)
    net[gov_url] = gov_b
    records.append({"object": L.IDENTITY_OBJECT[L.GIA_GOV_KEY], "probes": [
        {"method": "GitHub git-tree listing (recursive)", "status": "ok", "blob_sha": gf["git_blob"],
         "size": len(gov_b), "url": GH.format(repo=L.GIA_REPO, commit=L.GIA_93DE089, path=L.GIA_XLSX_PATH)}]})
    asd_t2 = asd_t.copy()
    asd_t2[0] += 0.5
    gx2 = root / "cmp.xlsx"
    giacomel_xlsx(gx2, dk, asd_t2, mdd_t, asd_s, mdd_s, planted)
    local(L.IDENTITY_OBJECT[L.GIA_CMP_KEY], "enigma_asd/gia/ENIGMA.xlsx", gx2.read_bytes(),
          tree_url=GH.format(repo=L.GIA_REPO, commit=L.GIA_C022A29, path=L.GIA_XLSX_PATH))
    facts.update(gia_asd_thickness=list(asd_t), gia_mdd_thickness=list(mdd_t), gia_asd_sub=list(asd_s))
    # Hansen
    hf = hansen_files(rng)
    local(L.IDENTITY_OBJECT[L.HANSEN_CT_KEY], "hansen/repo/data/enigma_ct.csv", hf["ct"], tree_url="https://github.com/x",
          lf_blob=True)
    local(L.IDENTITY_OBJECT[L.HANSEN_PC1_KEY], "hansen/repo/data/predictors/gene_pc1.csv", hf["pc1"],
          tree_url="https://github.com/y", lf_blob=True)
    pred_p = data / "hansen/repo/data/local_biol_predictors.csv"
    pred_p.write_bytes(hf["pred"])
    cam_b, cam_order = cammoun_info(dk)
    cam_p = data / "hansen/external/cammoun_info.csv"
    cam_p.parent.mkdir(parents=True, exist_ok=True)
    cam_p.write_bytes(cam_b)
    facts.update(hansen_ct=hf["ct_values"], hansen_pc1=hf["pc1_values"], cammoun_order=cam_order)
    # Liu T3
    local(L.IDENTITY_OBJECT[L.LIU_CT_KEY], "enigma_asd/toolbox/asd_meta_CortThick.csv", enigma_cortthick(dk, rng),
          tree_url="https://github.com/z")
    local(L.IDENTITY_OBJECT[L.LIU_SV_KEY], "enigma_asd/toolbox/asd_meta_SubVol.csv", enigma_subvol(rng),
          tree_url="https://github.com/w", lf_blob=True)
    # R15
    hcp_b, hcp_text, left_names = hcp_volume(dk)
    vol_url, lab_url = "https://ndownloader.figshare.com/files/1", "https://ndownloader.figshare.com/files/2"
    meta = {"id": 3501911, "files": [
        {"name": L.HCP_VOLUME_NAME, "size": len(hcp_b), "computed_md5": hashlib.md5(hcp_b).hexdigest(),
         "download_url": vol_url},
        {"name": L.HCP_VOLUME_NAME[:-7] + ".txt", "size": len(hcp_text.encode()),
         "computed_md5": hashlib.md5(hcp_text.encode()).hexdigest(), "download_url": lab_url},
        {"name": "HCP-MMP1_on_MNI152_ICBM2009a_nlin_hd.nii.gz", "size": 10, "computed_md5": "0" * 32,
         "download_url": "https://ndownloader.figshare.com/files/3"}]}
    net[L.HCP_ARTICLE_API] = json.dumps(meta).encode("utf-8")
    net[vol_url], net[lab_url] = hcp_b, hcp_text.encode("utf-8")
    facts["hcp_left_names"] = left_names
    # Pretzsch
    local(L.IDENTITY_OBJECT[L.PRE_KEY], "pretzsch/derived/etable13.csv", pretzsch_csv(left_names, rng))
    # R16
    annot_b, annot_lab = annot_bytes(dk)
    for name in L.FS_TARBALLS:
        net[L.FS_DIR + name] = tar_stream(annot_b, planted=planted)
    facts["n_vertices"] = int(annot_lab.size)
    # Leyhausen
    ley_sha = {}
    for image in L.LEY_IMAGES:
        vol_b = gzip.compress(b"synthetic volume " + str(image).encode(), mtime=0)
        lh_b = gifti_bytes(rng.normal(0, 1, annot_lab.size))
        pv = data / f"leyhausen/nv/image_{image}.nii.gz"
        pl = data / f"leyhausen/nv/image_{image}.lh.func.gii"
        pv.parent.mkdir(parents=True, exist_ok=True)
        pv.write_bytes(vol_b)
        pl.write_bytes(lh_b)
        fv, fl = ID.facts_of_bytes(vol_b), ID.facts_of_bytes(lh_b)
        ley_sha[image] = (fl["sha256"], fv["sha256"])
        records.append({"object": L.IDENTITY_OBJECT[L.LEY_LH_KEY[image]], "probes": [
            {"method": "NeuroVault image metadata (file, file_size only) + HTTP HEAD", "status": "ok", "field": "file",
             "file_url": f"https://neurovault.org/media/images/12301/v{image}.nii.gz", "api_file_size": len(vol_b),
             "content_length": len(vol_b), "last_modified": "Tue, 08 Mar 2022 13:56:36 GMT"},
            {"method": "NeuroVault image metadata (file, file_size only) + HTTP HEAD", "status": "ok",
             "field": "surface_left_file", "file_url": f"https://neurovault.org/media/images/12301/v{image}.lh.gii",
             "api_file_size": None, "content_length": len(lh_b)},
            {"method": "local file already on disk (hashed only, not parsed)", "status": "ok", "path": str(pv),
             "size": len(vol_b), "sha256": fv["sha256"], "git_blob_sha": fv["git_blob"]},
            {"method": "local file already on disk (hashed only, not parsed)", "status": "ok", "path": str(pl),
             "size": len(lh_b), "sha256": fl["sha256"], "git_blob_sha": fl["git_blob"]}]})
    # Giacomel repository lists at e045bc5 (the tree listing) and the MDD lists / GEDAR maps (gia_mdd_paths)
    tree = []
    mdd_paths = {}
    for key, path in L.GIA_ASD_LISTS.items():
        sub = sorted(rng.choice(genes, int(rng.integers(12, 40)), replace=False).tolist())
        b = list_tsv(sub, rng, sign=(0 if "_top_genes" in path else (1 if "pos" in path else -1)), planted=planted)
        if key == "ASD_top_neg_genes_thr_1":
            b = list_tsv(sub[:3], rng, sign=-1)                     # a list with < 5 genes -> 'not testable (< 5)'
        net[L.RAW_URL.format(repo=L.GIA_REPO, commit=L.GIA_E045BC5, path=path)] = b
        f = ID.facts_of_bytes(b)
        tree.append({"path": path, "type": "blob", "sha": f["git_blob"], "size": len(b)})
    for key in ("MDD_top_pos_genes_thr_1", "MDD_top_neg_genes_thr_10", "MDD_top_genes_thr_1", "MDD_top_genes_thr_5",
                "MDD_top_genes_thr_10"):
        path = f"results/MDD/{key}.tsv"
        sub = sorted(rng.choice(genes, 20, replace=False).tolist())
        b = list_tsv(sub, rng, weights="zscore", sign=(1 if "pos" in key else (-1 if "neg" in key else 0)))
        net[L.RAW_URL.format(repo=L.GIA_REPO, commit=L.GIA_E045BC5, path=path)] = b
        f = ID.facts_of_bytes(b)
        mdd_paths[path] = (f["git_blob"], len(b), L.GIA_E045BC5)
    for d in ("ASD", "MDD"):
        for t in (1, 5, 10):
            path = f"results/{d}/{d}_TPRS_thr_{t}.tsv"
            b = gedar_tsv(dk, rng, by_names=(d == "MDD"))
            net[L.RAW_URL.format(repo=L.GIA_REPO, commit=L.GIA_EDA33AB, path=path)] = b
            f = ID.facts_of_bytes(b)
            mdd_paths[path] = (f["git_blob"], len(b), L.GIA_EDA33AB)
    # the authors' AHBA header (the 600 dk genes and synthetic symbols) and HPA list: an ASD pool of exactly 3,599
    syn = [f"SYN{k:05d}" for k in range(3200)]
    ahba_genes = genes + syn
    pool = genes + syn[:2999]                                   # 600 + 2,999 = 3,599
    ahba_b = ("label," + ",".join(ahba_genes) + "\n1," + ",".join("0.1" for _ in ahba_genes) + "\n").encode()
    hpa_b = ("Gene\tEnsembl\n" + "\n".join(f"{g}\tENSG" for g in pool + ["NOTINAHBA1", "NOTINAHBA2"]) + "\n").encode()
    facts["deg_pool"] = len(pool)
    # the stand-in DEG table (the stand-in script reads it from the tree; the real script reads what it reads) and the
    # DK ids its stand-in maps are written on
    deg_rows = [(g, "ASD", float(np.round(rng.normal(0, 0.5), 6)) or 0.01, (k + 1) / 1e5) for k, g in enumerate(pool)]
    deg_rows += [(f"OUT{k}", "ASD", 0.1, 1e-9) for k in range(50)]
    deg_rows += [(g, "MDD", float(np.round(rng.normal(0, 0.5), 6)) or 0.01, (k + 1) / 1e5) for k, g in
                 enumerate(pool[:900])]
    deg_rows += [(genes[k], "SCZ", 0.2, 1e-12) for k in range(40)]
    deg_b = ("Gene\tDx\tlogFC\tp.value\n" + "".join(f"{g}\t{d}\t{w!r}\t{q!r}\n" for g, d, w, q in deg_rows)).encode()
    left_ids = sorted(int(r["id"]) for _, r in dk.iterrows() if r["hemisphere"] == "L")
    ids_b = ("id\n" + "".join(f"{i}\n" for i in left_ids)).encode()
    # base R only (the WP2 R image has no readxl): the TSV's definition, one DEG list per (Dx, thr) with gene_name and
    # logFC, and a stand-in rebuilt map per (Dx, thr) on the DK ids (R56's layout)
    script = (b"hdr <- strsplit(readLines('data/AHBA/AHBA_data_no_norm.csv', n = 1), ',')[[1]][-1]\n"
              b"hpa <- read.delim('data/AHBA/AHPA_mrna_brain.tsv', stringsAsFactors = FALSE)\n"
              b"deg <- read.delim('data/DEG/sadeghi_deg.tsv', stringsAsFactors = FALSE)\n"
              b"ids <- read.delim('data/AHBA/dk_left_ids.tsv')$id\n"
              b"# library(notapackage)\n"
              b"pool <- intersect(hdr, hpa$Gene)\n"
              b"for (dx in c('ASD', 'MDD')) {\n"
              b"  d <- deg[deg$Dx == dx & deg$Gene %in% pool, ]\n"
              b"  d <- d[order(d$p.value), ]\n"
              b"  n <- length(unique(d$Gene))\n"
              b"  dir.create(file.path('results', dx), recursive = TRUE, showWarnings = FALSE)\n"
              b"  for (t in c(1, 5, 10)) {\n"
              b"    m <- round(n * t / 100)\n"
              b"    write.table(data.frame(gene_name = d$Gene[seq_len(m)], logFC = d$logFC[seq_len(m)]),\n"
              b"                file.path('results', dx, paste0(dx, '_DEG_top_genes_thr_', t, '.tsv')),\n"
              b"                sep = '\\t', quote = FALSE, row.names = FALSE)\n"
              b"    write.table(data.frame(label = ids, rho = sin(ids * t) * sum(d$logFC[seq_len(m)])),\n"
              b"                file.path('results', dx, paste0(dx, '_literature_TPRS_thr_', t, '.tsv')),\n"
              b"                sep = '\\t', quote = FALSE, row.names = FALSE)\n"
              b"  }\n"
              b"}\n")
    facts["deg_rows"] = deg_rows
    for path, b in (("code/literature_gwas_analysis.R", script),
                    ("data/AHBA/AHBA_data_no_norm.csv", ahba_b),
                    ("data/AHBA/AHPA_mrna_brain.tsv", hpa_b),
                    ("data/DEG/sadeghi_deg.tsv", deg_b),
                    ("data/AHBA/dk_left_ids.tsv", ids_b)):
        net[L.RAW_URL.format(repo=L.GIA_REPO, commit=L.GIA_E045BC5, path=path)] = b
        f = ID.facts_of_bytes(b)
        tree.append({"path": path, "type": "blob", "sha": f["git_blob"], "size": len(b)})
    net[L.TREE_API.format(repo=L.GIA_REPO, commit=L.GIA_E045BC5)] = json.dumps(
        {"sha": "0" * 40, "truncated": False, "tree": tree}).encode("utf-8")
    facts["r17_prefix"] = {k: sha(net[L.RAW_URL.format(repo=L.GIA_REPO, commit=L.GIA_E045BC5, path=p)])[:16]
                           for k, (p, _) in L.R17_INPUT_PATHS.items()}
    # R58's public documents: the commit record (committer date), r-hub's R versions, Bioconductor's config.yaml
    from .rbuild import r17 as R17
    net[L.GH_COMMIT_API.format(repo=L.GIA_REPO, commit=L.GIA_E045BC5)] = json.dumps(
        {"sha": L.GIA_E045BC5, "commit": {"committer": {"date": "2024-09-01T10:00:00Z"}}}).encode("utf-8")
    net[R17.RVERSIONS_API] = json.dumps([{"version": "4.4.0", "date": "2024-04-24"},
                                         {"version": "4.4.1", "date": "2024-06-14"}]).encode("utf-8")
    net[R17.BIOC_CONFIG] = (b"release_dates:\n  \"3.19\": \"05/01/2024\"\n  \"3.20\": \"10/30/2024\"\n"
                            b"r_ver_for_bioc_ver:\n  \"3.19\": \"4.4\"\n  \"3.20\": \"4.4\"\nother: 1\n")
    # the Sadeghi workbook in the declared folder
    import openpyxl
    sad = data / "giacomel_external/sadeghi2022_csbj/mmc2.xlsx"
    sad.parent.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    wb.active.title = "Supplementary_Data1"
    ws = wb.active
    ws.append(["Gene", "Dx", "logFC", "p.value", f"note {planted}"])
    for g, d, w, q in deg_rows:                                 # ASD pool genes first by p; OUT* never in the pool
        ws.append([g, d, w, q, ""])
    import datetime as _dtm                                     # a spreadsheet's date-converted symbol (2026-10-17)
    ws.append([_dtm.datetime(2026, 3, 1), "ASD", 0.1, 0.5, ""])
    facts["deg_excluded"] = {"symbol_datetime": 1}
    wb.create_sheet(f"subj_{planted}").append([planted])
    wb.save(str(sad))
    # NeuroVault decoders (R45's form) for the three images
    from . import wp3_layout as W3
    for image in L.LEY_IMAGES:
        net[W3.DECODER_URL.format(image=image)] = decoder_json(genes, rng, planted)
    # scratch identity record, pins, prefixes
    ident = root / "identity_scratch.json"
    ident.write_text(json.dumps({"what": "scratch", "records": records}), encoding="utf-8")
    mdd_doc = {"e045bc5_sets": [{"commit": L.GIA_E045BC5, "path": p, "present": True, "blob_sha": v[0], "size": v[1]}
                                for p, v in mdd_paths.items() if v[2] == L.GIA_E045BC5],
               "eda33ab_asd_counterparts": [{"path": p, "blob_sha": v[0], "size": v[1]} for p, v in mdd_paths.items()
                                            if v[2] == L.GIA_EDA33AB and "/ASD/" in p],
               "eda33ab_mdd_maps": [{"path": p, "blob_sha": v[0], "size": v[1]} for p, v in mdd_paths.items()
                                    if v[2] == L.GIA_EDA33AB and "/MDD/" in p]}
    repo_scratch = root / "repo"
    (repo_scratch / Path(L.GIA_MDD_PATHS_REL).parent).mkdir(parents=True, exist_ok=True)
    (repo_scratch / L.GIA_MDD_PATHS_REL).write_text(json.dumps(mdd_doc), encoding="utf-8")
    pins = {"dk_info": ("artifacts/ahba/dk_atlas_info.csv", "repo",
                        "abb69a9bf976a153b749eb5333e92cf03d4f61f2ce3efd34e49ea6e82f18729b"),
            "hgnc": ("hgnc.txt", "data", sha(hg_b)),
            "dk_atlas": ("env/venv/Lib/site-packages/abagen/data/atlas-desikankilliany.nii.gz", "main",
                         "0a28c93f5967f0892810219e68edb32abcaa9fd796a217096512fb0724c20d8a")}
    prefix = {L.HANSEN_PRED_KEY: (str(pred_p), sha(hf["pred"])[:16], "scratch"),
              L.HANSEN_INFO_KEY: (str(cam_p), sha(cam_b)[:16], "scratch"),
              L.SADEGHI_KEY: (str(sad), sha(sad.read_bytes())[:16], "scratch")}
    roots = L.Roots.scratch_layout(root, pins=pins, identity_json=ident, prefix_pins=prefix, ley_sha=ley_sha,
                                   mdd_paths_json=repo_scratch / L.GIA_MDD_PATHS_REL,
                                   r17_prefix=facts["r17_prefix"])
    return dict(roots=roots, net=net, facts=facts, mdd_repo=repo_scratch, dk=dk)
