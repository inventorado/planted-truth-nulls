"""WP3 phase 1: SYNTHETIC stand-ins of every ungated phase-2 input, placed at the runner-built paths of a scratch
layout (wp3_layout.Roots.scratch), for the material-stage tests and the scratch dry dispatch. Nothing here opens an
audit carrier, map, supplement or decoder output: the stand-ins are generated from seeds, the label metadata the plan
allows (aal_atlas_info.csv, dk_atlas_info.csv, mist64_classes.json), the frozen S-build's member lists and the WP2
primary builds' count tables (copied unchanged into the scratch builds directory).

build_scratch(root) writes:
  data/segura2025/syn_790618.nii.gz, syn_781986.nii.gz   synthetic z maps on a 4 mm grid (zeros = missing)
  data/atlases/aal_syn.nii.gz                              a synthetic atlas carrying every AAL id of the atlas info
  data/moreau2020mutations/repo/data/Supplementary_Table_S1.xlsx
                                                           the Moreau layout: declared sheets 1_16p11.2Del and
                                                           3_22q11.2Del (64 x 64, MIST64 labels; a corner label), the
                                                           do-not-open sheets 5_BIV ... 9_Ranking with planted
                                                           identifier-shaped strings, an undeclared sheet
  data/brainspan/genes_matrix_csv/*.csv                    a BrainSpan-like matrix (donor columns planted with
                                                           identifier-shaped strings that must never be read)
  data/explore_public/hgnc_syn.txt                         a synthetic HGNC table (approved / previous / alias tiers)
  data/gamba/syn.csv                                       2,711 flagged rows (the registered count)
  data/register_sets_src/go_syn/{go-basic.obo, goa_human.gaf.gz}, data/.../PTHR16.0_syn   for the R22 wiring tests
  data/liu/supplement_syn.xlsx                             Liu's Supplementary Data 1-15 stand-in (SD7 declared by
                                                           RUN_PLAN_amend_3 R46's rules; SD1-SD3 planted per-sample
                                                           labels never fetched); Roots.sd7_copy
  data/register_sets_src/segura2025_tables/{moesm2_syn.pdf, tableS4_syn.txt}   the MOESM2 stand-in (matplotlib; R47's
                                                           two layouts) and Table S4's raw list (the S4 members)
  builds/                                                  the primary-* count tables (copied) + synthetic
                                                           perdonor-aal and r10-liu-dk-samples builds, a MANIFEST
  identity_refs.json                                       IDENTITY_prefreeze-format references of the stand-ins
scratch_net() replaces fetch_extract's network functions by a mock: HEAD of the decoder URLs and of the two images'
NeuroVault file URLs (R45 (e)'s size probe), GET of the decoder URLs only (scripted outcomes: curl exits, HTTP statuses,
an HTML page, decoder-output variants); every other URL raises.
"""
from __future__ import annotations

import contextlib
import gzip
import hashlib
import io
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from . import a3_port as _A3  # noqa: F401  (puts src/ on sys.path)
from . import ahba_builds as AB
from . import fetch_extract as FE
from . import identity as ID
from . import wp3_layout as L

SEED = 20261011
PLANTED_IDS = ("SUBJ-1234567890", "NDAR_INVAB123CDE", "sub-0051234", "123456789")   # identifier-shaped, test-time
SYN_GENES = [f"SYNG{k:04d}" for k in range(1, 401)]


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _write(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    if path.read_bytes() != data:
        raise OSError("read-back")
    return _sha(data)


def _nifti_bytes(vol: np.ndarray, affine: np.ndarray) -> bytes:
    import nibabel as nib
    img = nib.Nifti1Image(vol, affine)
    return gzip.compress(img.to_bytes(), mtime=0)


def _members(set_id: str) -> list[str]:
    doc = json.loads((L.REPO / "arcs/audit/register_sets" / f"{set_id}.json").read_text(encoding="utf-8"))
    return list(doc["members_hgnc"])


# ================================================================================================================
# the stand-ins
# ================================================================================================================
def synthetic_atlas_and_maps(rng) -> tuple[bytes, dict]:
    """A 4 mm-grid atlas carrying every AAL id (cubes of 2 x 2 x 2 voxels, the rest 0) and two z maps on the same grid
    (values N(0, 1); about 10 % of voxels 0; three parcels left below 50 % coverage)."""
    info = pd.read_csv(L.REPO / "artifacts/ahba/aal_atlas_info.csv")
    ids = [int(i) for i in info["id"]]
    shape = (24, 24, 24)
    atlas = np.zeros(shape, dtype=np.int16)
    k = 0
    for i in range(0, 24, 2):
        for j in range(0, 24, 2):
            for m in range(0, 24, 2):
                if k < len(ids):
                    atlas[i:i + 2, j:j + 2, m:m + 2] = ids[k]
                k += 1
    aff = np.diag([4.0, 4.0, 4.0, 1.0])
    aff[:3, 3] = [-48.0, -48.0, -48.0]
    maps = {}
    for image in L.SEGURA_IMAGES:
        v = rng.standard_normal(shape).astype(np.float32)
        v[rng.random(shape) < 0.10] = 0.0
        for drop in ids[3:6]:                      # three parcels below 50 % coverage
            mask = atlas == drop
            idx = np.argwhere(mask)
            for p in idx[:5]:
                v[tuple(p)] = 0.0
        v[atlas == 0] = 0.0
        maps[image] = _nifti_bytes(v, aff)
    return _nifti_bytes(atlas, aff), maps


def synthetic_moreau_xlsx(rng) -> bytes:
    import openpyxl
    voc = FE.mist64_vocab()
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name in ("0_README", "1_16p11.2Del", "2_16p11.2Dup", "3_22q11.2Del", "4_22q11.2Dup", "5_BIV", "6_ASD", "7_SZ",
                 "8_ADHD", "9_Ranking"):
        ws = wb.create_sheet(name)
        if name in ("1_16p11.2Del", "3_22q11.2Del"):
            ws.append(["Region"] + [lab for _, lab, _ in voc])
            B = rng.normal(0, 0.1, (64, 64))
            B = (B + B.T) / 2
            for r, (_, lab, _) in enumerate(voc):
                ws.append([lab] + [float(x) for x in B[r]])
        elif name in L.MOREAU_SHEET_KEY or name.startswith(("5_", "6_", "7_", "8_", "9_")):
            ws.append(["subject_id", "beta"])
            for s in PLANTED_IDS:
                ws.append([s, float(rng.normal())])
        else:
            ws.append(["note"])
            ws.append([PLANTED_IDS[0]])
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def synthetic_hgnc(genes: list[str]) -> tuple[bytes, dict]:
    """A synthetic HGNC table over `genes` (approved), with previous / alias symbols for a few, Ensembl and Entrez ids.
    Returns (bytes, {symbol: (ensembl, entrez)})."""
    rows, ids = [], {}
    for k, g in enumerate(genes):
        ens, ent = f"ENSG{90000000000 + k:011d}", str(900000 + k)
        prev = f"OLD{g}" if k % 50 == 0 else ""
        alias = f"AL{g}" if k % 70 == 0 else ""
        rows.append({"hgnc_id": f"HGNC:{900000 + k}", "symbol": g, "status": "Approved", "prev_symbol": prev,
                     "alias_symbol": alias, "ensembl_gene_id": ens, "entrez_id": ent, "uniprot_ids": f"Q{k:05d}",
                     "rna_central_id": ""})
        ids[g] = (ens, ent)
    df = pd.DataFrame(rows)
    return df.to_csv(sep="\t", index=False, lineterminator="\n").encode("utf-8"), ids


def synthetic_brainspan(rng, genes: list[str], ids: dict, members: list[str]) -> dict:
    from asdg.brainspan import NEOCORTEX
    ages = ["8 pcw", "9 pcw", "13 pcw", "16 pcw", "24 pcw", "37 pcw", "4 mos", "10 mos", "2 yrs", "4 yrs", "8 yrs",
            "11 yrs", "13 yrs", "18 yrs", "23 yrs", "36 yrs"]
    structs = ["DFC", "VFC", "MFC", "OFC", "MD", "DTH", "STR", "CBC", "HIP", "AMY", "V1C", "ITC"]
    samples = [(a, s) for a in ages for s in structs]
    n = len(samples)
    rows_genes = list(genes) + ["UNMAPPEDX1", "UNMAPPEDX2", genes[3]]     # an unmapped pair and a duplicate symbol
    G = len(rows_genes)
    lvl = rng.normal(3, 1, G)[:, None]
    X = np.exp2(lvl + rng.normal(0, 0.7, (G, n))) - 1.0
    mem = [k for k, g in enumerate(rows_genes) if g in set(members)]
    pre = np.array([a.endswith("pcw") for a, _ in samples])
    X[np.ix_(mem, np.flatnonzero(pre))] *= 1.6
    X = np.round(np.clip(X, 0, None), 3)
    expr = pd.DataFrame(X, index=np.arange(1, G + 1))
    rows = pd.DataFrame({"row_num": np.arange(1, G + 1), "gene_id": np.arange(1, G + 1),
                         "ensembl_gene_id": [ids[g][0] if g in ids else f"ENSG99{k:09d}" for k, g in enumerate(rows_genes)],
                         "gene_symbol": rows_genes, "entrez_id": [ids[g][1] if g in ids else "" for g in rows_genes]})
    cols = pd.DataFrame({"column_num": np.arange(1, n + 1),
                         "donor_id": [PLANTED_IDS[k % 4] for k in range(n)],
                         "donor_name": [f"H376.{PLANTED_IDS[(k + 1) % 4]}" for k in range(n)],
                         "age": [a for a, _ in samples], "gender": ["F" if k % 2 else "M" for k in range(n)],
                         "structure_id": np.arange(n), "structure_acronym": [s for _, s in samples],
                         "structure_name": [f"structure {s}" for _, s in samples]})
    assert any(s in NEOCORTEX for s in structs)
    return {"expression_matrix.csv": expr.to_csv(header=False, lineterminator="\n").encode("utf-8"),
            "rows_metadata.csv": rows.to_csv(index=False, lineterminator="\n").encode("utf-8"),
            "columns_metadata.csv": cols.to_csv(index=False, lineterminator="\n").encode("utf-8")}


def synthetic_gamba(genes: list[str]) -> bytes:
    flagged = list(genes) + [f"GAMBASYN{k:05d}" for k in range(2711 - len(genes))]
    rows = [{"symbols": g, "brain > body (default)": 1} for g in flagged]
    rows += [{"symbols": f"BODYSYN{k:04d}", "brain > body (default)": 0} for k in range(300)]
    return pd.DataFrame(rows).to_csv(index=False, lineterminator="\n").encode("utf-8")


def synthetic_go(genes: list[str], ids: dict, rng) -> tuple[bytes, bytes]:
    """A small GO: BP root GO:0008150 with two levels, a part_of edge, an obsolete term, the seven SEG-C3a-g ids and a
    few D ids; annotations by UniProtKB ids of the synthetic HGNC table, plus NOT / ND lines (excluded)."""
    terms = ["GO:0007409", "GO:0060385", "GO:0048812", "GO:0060997", "GO:0048675", "GO:0007411", "GO:0050770",
             "GO:0048667", "GO:0048666", "GO:0048468"]
    lines = ["format-version: 1.2", "data-version: releases/2024-01-17", ""]
    lines += ["[Term]", "id: GO:0008150", "name: biological_process", "namespace: biological_process", ""]
    lines += ["[Term]", "id: GO:9000001", "name: synthetic parent", "namespace: biological_process",
              "is_a: GO:0008150 ! biological_process", ""]
    for k, t in enumerate(terms):
        par = "GO:9000001" if k % 2 else "GO:0008150"
        lines += ["[Term]", f"id: {t}", f"name: synthetic term {k}", "namespace: biological_process"]
        lines += [f"is_a: {par} ! parent"] if k != 3 else [f"relationship: part_of {terms[2]} ! part"]
        lines += [""]
    lines += ["[Term]", "id: GO:9000099", "name: obsolete synthetic", "namespace: biological_process",
              "is_obsolete: true", ""]
    lines += ["[Typedef]", "id: part_of", "name: part of", ""]
    obo = "\n".join(lines).encode("utf-8")
    gaf = ["!gaf-version: 2.2", "!date-generated: 2024-01-17"]
    k_of = {g: k for k, g in enumerate(ids)}
    for t in terms + ["GO:9000001"]:
        for g in rng.choice(genes, 25, replace=False):
            k = k_of[g]
            gaf.append("\t".join(["UniProtKB", f"Q{k:05d}", g, "", t, "PMID:1", "IDA", "", "P", "", "", "protein",
                                  "taxon:9606", "20240101", "UniProt", "", ""]))
    gaf.append("\t".join(["UniProtKB", "Q00001", genes[1], "NOT", terms[0], "PMID:1", "IDA", "", "P", "", "", "protein",
                          "taxon:9606", "20240101", "UniProt", "", ""]))
    gaf.append("\t".join(["UniProtKB", "Q00002", genes[2], "", terms[0], "PMID:1", "ND", "", "P", "", "", "protein",
                          "taxon:9606", "20240101", "UniProt", "", ""]))
    return obo, gzip.compress(("\n".join(gaf) + "\n").encode("utf-8"), mtime=0)


def synthetic_pthr16(genes: list[str], ids: dict) -> bytes:
    out = []
    for k, g in enumerate(genes[: int(len(genes) * 0.9)]):
        out.append("\t".join([f"HUMAN|HGNC={900000 + k}|UniProtKB=Q{k:05d}", f"Q{k:05d}", g, "PTHR1", "fam", "sub",
                              "", "", "", "", ""]))
    return ("\n".join(out) + "\n").encode("utf-8")


def sd7_labels_synthetic() -> list:
    """ENIGMA-like SD7 row labels: DK cortical L / R '<side>_<name>_thickavg', the 7 subcortical short names L / R, the
    lateral ventricles, and three global measures (R42 (d)'s drops)."""
    from . import forms as FM
    dk = pd.read_csv(L.REPO / "artifacts/ahba/dk_atlas_info.csv")
    labels = []
    for _, r in dk.iterrows():
        if r["hemisphere"] != "B" and r["structure"] == "cortex":
            labels.append(f"{r['hemisphere']}_{r['label']}_thickavg")
    inv = {v: k for k, v in FM.SD7_ALIASES.items()}
    for side in ("L", "R"):
        for nm in ("thalamusproper", "caudate", "putamen", "pallidum", "hippocampus", "amygdala", "accumbensarea"):
            labels.append(f"{side}{inv[nm]}")
        labels.append(f"{side}LatVent")
    labels += ["ICV", "LThickness", "RThickness"]
    return labels


SD7_VARIANTS = ("two_sheets", "no_sheet", "no_header", "two_asd", "interrupted", "rownumbers", "ns", "cortical_missing",
                "identifier", "header_row0", "empty_block")


def synthetic_sd7_book(rng, variant: str | None = None) -> bytes:
    """Liu's Supplementary Data workbook stand-in: 15 sheets 'Supplementary Data 1' ... '15' (SD1-SD3 hold planted
    per-sample labels: never fetched); SD7 = 'Supplementary Data 7': a title in row 0, the header in row 2 (an empty
    position-0 header, 'ASD_SFARI_1' beside 'ASD'), two empty rows, the label block, a blank row and footnotes. Missing
    values: two cortical labels 'NA' and '#N/A', one empty. Variants (one change each, combinable with '+', e.g.
    'identifier+ns'): see SD7_VARIANTS."""
    import openpyxl
    vs = set((variant or "").split("+")) - {""}
    labels = sd7_labels_synthetic()
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    names = [f"Supplementary Data {k}" for k in range(1, 16)]
    if "no_sheet" in vs:
        names[6] = "Supplementary Table 7"
    for name in names:
        ws = wb.create_sheet(name)
        if name == names[6]:
            if "header_row0" not in vs:
                ws.append([f"Supplementary Data 7. AHBA-region r per ENIGMA label (synthetic stand-in)"])
                ws.append([None])
            asd = "ASD" if "no_header" not in vs else "ASDX"
            hdr = [None, "ASD_SFARI_1", asd, "ADHD", "SCZ"]
            if "two_asd" in vs:
                hdr[3] = "asd"
            ws.append(hdr)
            ws.append([None])
            ws.append([""])
            for k, lab in enumerate([] if "empty_block" in vs else labels):
                v = float(rng.normal(0.4, 0.03))
                if "cortical_missing" in vs and lab.endswith("_thickavg"):
                    v = "NA"
                elif k == 4:
                    v = "NA"
                elif k == 9:
                    v = "#N/A"
                elif k == 13:
                    v = None
                elif "ns" in vs and k == 20:
                    v = "n.s."
                first = lab if "rownumbers" not in vs else k + 1
                ws.append([first, float(rng.normal(0.4, 0.03)), v, float(rng.normal(0.3, 0.03)), 0.1])
            ws.append([None])
            if "empty_block" not in vs:
                ws.append(["Note: r is the Pearson correlation of the AHBA region and the ENIGMA label (synthetic)."])
            if "interrupted" in vs:
                ws.append(["L_cuneus_thickavg", 0.1, 0.2, 0.3, 0.4])
            if "identifier" in vs:
                ws.cell(row=2, column=8, value="NDAR_INVAB123CDE")
        elif name in names[:3]:
            ws.append(["sample", "ASD", "SCZ"])
            for k in range(20):
                ws.append([f"H376.{k}.{PLANTED_IDS[k % 4]}", float(rng.normal()), float(rng.normal())])
        else:
            ws.append(["Supplementary", "data", "table"])
            ws.append([1.0, 2.0, 3.0])
    if "two_sheets" in vs:
        ws = wb.create_sheet("Supp Data 7")
        ws.append(["x"])
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()


def synthetic_sd7(rng) -> tuple[bytes, dict]:
    import openpyxl
    from . import forms as FM
    dk = pd.read_csv(L.REPO / "artifacts/ahba/dk_atlas_info.csv")
    labels = []
    for _, r in dk.iterrows():
        if r["hemisphere"] == "B":
            continue
        side = r["hemisphere"]
        if r["structure"] == "cortex":
            labels.append(f"{side}_{r['label']}_thickavg")
    inv = {v: k for k, v in FM.SD7_ALIASES.items()}
    for side in ("L", "R"):
        for nm in ("thalamusproper", "caudate", "putamen", "pallidum", "hippocampus", "amygdala", "accumbensarea"):
            labels.append(f"{side}{inv[nm]}")
        labels.append(f"{side}LatVent")
    labels += ["ICV", "LThickness", "RThickness"]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SD7_syn"
    ws.append(["Region", "ASD", "ADHD"])
    for lab in labels:
        ws.append([lab, float(rng.normal(0, 0.02)), float(rng.normal(0, 0.02))])
    ws2 = wb.create_sheet("SD8_syn")
    ws2.append(["Region", "x"])
    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue(), {"sheet": "SD7_syn", "header_row": 0, "label_header": "Region", "value_header": "ASD"}


def synthetic_decoder_json(genes: list[str], ids: dict, members: list[str], rng) -> bytes:
    rows = []
    for k, g in enumerate(list(genes) + ["NOTAGENE1"]):
        t = float(rng.normal(0, 2))
        p = float(2 * (1 - __import__("scipy").stats.norm.cdf(abs(t))))
        rows.append([g if k % 40 else f"OLD{g}" if g in ids else g, float(ids[g][1]) if g in ids else None,
                     f"name {k}", t, p, None, 1.0, 0.1])
    ps = np.array([r[4] for r in rows])
    from . import repro as RE
    q = RE.bh(ps)
    for r, qq in zip(rows, q):
        r[5] = float(qq)
    rows[5][5] = None                               # a non-finite q (counted)
    return json.dumps({"columns": list(L.DECODER_COLUMNS), "data": rows}).encode("utf-8")


# ---- builds ------------------------------------------------------------------------------------------------------
def _frame_output(df: pd.DataFrame, path: Path, role: str, donor=None) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        data = gzip.compress(df.to_csv(lineterminator="\n").encode("utf-8"), mtime=0)
    else:
        data = df.to_csv(lineterminator="\n").encode("utf-8")
    path.write_bytes(data)
    back = pd.read_csv(io.BytesIO(data), index_col=0, compression="gzip" if path.suffix == ".gz" else None)
    o = dict(file=path.name, role=role, bytes=len(data), sha256=_sha(data), shape=list(df.shape),
             sha256_default=AB.frame_sha(back))
    if donor is not None:
        o["donor"] = donor
    return o


def synthetic_builds(bdir: Path, rng, genes: list[str]) -> None:
    """The scratch a1_builds directory: the real primary-* records and count tables copied unchanged (allowed AHBA
    build data), synthetic perdonor-aal (six donors x 116 AAL parcels x the synthetic genes, NaN where a donor has no
    sample) and r10-liu-dk-samples (per-sample rows labelled by DK id; no well id), and a MANIFEST."""
    real = Path(L.REPO / "artifacts/ahba/a1_builds")
    man = {"builds": {}}
    for name in ("primary-dk", "primary-aal", "primary-mist64"):
        rec = json.loads((real / name / "build_record.json").read_bytes())
        (bdir / name).mkdir(parents=True, exist_ok=True)
        o = next(x for x in rec["outputs"] if x["role"] == "counts")
        shutil.copyfile(real / name / o["file"], bdir / name / o["file"])
        shutil.copyfile(real / name / "build_record.json", bdir / name / "build_record.json")
        man["builds"][name] = {"record_sha256": _sha((bdir / name / "build_record.json").read_bytes())}
    aal = pd.read_csv(L.REPO / "artifacts/ahba/aal_atlas_info.csv")
    pc = pd.read_csv(real / "primary-aal" / "aal_counts.csv", index_col=0)
    outs = []
    for k, d in enumerate(AB.DONORS, start=1):
        M = pd.DataFrame(rng.normal(0, 1, (len(aal), len(genes))), index=aal["id"].astype(int), columns=genes)
        M.index.name = "label"
        M.loc[pc.index[pc[f"d{k}"] == 0]] = np.nan
        outs.append(_frame_output(M, bdir / "perdonor-aal" / f"aal_donor-d{k}_expr.csv.gz", "matrix", donor=d))
    outs.append(_frame_output(pc, bdir / "perdonor-aal" / "aal_counts.csv", "counts"))
    rec = {"build": "perdonor-aal", "ok": True, "outputs": outs, "synthetic": True}
    (bdir / "perdonor-aal" / "build_record.json").write_bytes(json.dumps(rec, indent=1).encode("utf-8"))
    man["builds"]["perdonor-aal"] = {"record_sha256": _sha((bdir / "perdonor-aal" / "build_record.json").read_bytes())}
    dk = pd.read_csv(L.REPO / "artifacts/ahba/dk_atlas_info.csv")
    labs = np.repeat(dk["id"].astype(int).to_numpy(), 3)
    S = pd.DataFrame(np.round(rng.normal(0.5, 0.2, (labs.size, len(genes))), 4), index=labs, columns=genes)
    S.index.name = "label"
    o = _frame_output(S, bdir / "r10-liu-dk-samples" / "dk_samples_expr.csv.gz", "matrix")
    rec = {"build": "r10-liu-dk-samples", "ok": True, "outputs": [o], "synthetic": True}
    (bdir / "r10-liu-dk-samples" / "build_record.json").write_bytes(json.dumps(rec, indent=1).encode("utf-8"))
    man["builds"]["r10-liu-dk-samples"] = {"record_sha256": _sha((bdir / "r10-liu-dk-samples" / "build_record.json")
                                                                  .read_bytes())}
    (bdir / "MANIFEST.json").write_bytes(json.dumps(man, indent=1).encode("utf-8"))


# ================================================================================================================
# the layout
# ================================================================================================================
def _probe_local(path: Path, data: bytes) -> dict:
    return {"method": "local file already on disk (hashed only, not parsed)", "path": str(path), "status": "ok",
            "size": len(data), "sha256": _sha(data), "git_blob_sha": ID.git_blob_of(data)}


def build_scratch(root: Path, *, with_sd7: bool = True, seed: int = SEED, sd7_variant: str | None = None,
                  moesm2_variant: str | None = None) -> L.Roots:
    root = Path(root)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError("the scratch directory is not empty")
    rng = np.random.default_rng(seed)
    data = root / "data"
    s4, liu, mor = _members("segura_s4"), _members("liu_merged_asd"), _members("moreau_16p11.2")
    genes = sorted(set(SYN_GENES) | set(s4) | set(liu) | set(mor))
    hg_bytes, ids = synthetic_hgnc(genes)
    pins = {}

    def pin(key, rel, b, root_name="data"):
        _write(data / rel, b)
        pins[key] = (rel, root_name, _sha(b), len(b))
    atlas, maps = synthetic_atlas_and_maps(rng)
    pin("aal_atlas", "atlases/aal_syn.nii.gz", atlas)
    for key in ("aal_info", "dk_info"):
        rel = {"aal_info": "aal_atlas_info.csv", "dk_info": "dk_atlas_info.csv"}[key]
        pins[key] = (rel, "ahba", _sha((L.REPO / "artifacts/ahba" / rel).read_bytes()))
    pin("hgnc", "explore_public/hgnc_syn.txt", hg_bytes)
    bs = synthetic_brainspan(rng, genes, ids, liu)
    pin("brainspan_expr", "brainspan/genes_matrix_csv/expression_matrix.csv", bs["expression_matrix.csv"])
    pin("brainspan_rows", "brainspan/genes_matrix_csv/rows_metadata.csv", bs["rows_metadata.csv"])      # R50
    pin("brainspan_cols", "brainspan/genes_matrix_csv/columns_metadata.csv", bs["columns_metadata.csv"])
    pin("gamba", "gamba/syn.csv", synthetic_gamba(genes[: min(len(genes), 600)]))
    obo, gaf = synthetic_go(genes, ids, rng)
    pin("go_obo", "register_sets_src/go_syn/go-basic.obo", obo)
    pin("go_gaf", "register_sets_src/go_syn/goa_human.gaf.gz", gaf)
    pin("pthr16", "register_sets_src/panther_syn/PTHR16.0_syn", synthetic_pthr16(genes, ids))
    # carriers and their pre-freeze-format identity references
    records = []
    for image in L.SEGURA_IMAGES:
        p = data / "segura2025" / f"syn_{image}.nii.gz"
        _write(p, maps[image])
        url = f"https://neurovault.org/media/images/12297/syn_{image}.nii.gz"
        records.append({"target": "segura2024symptommapping", "target_no": 1, "gate": "ungated",
                        "object": L.IDENTITY_OBJECT[L.SEGURA_MAP_KEY[image]],
                        "probes": [{"method": "NeuroVault image metadata (file, file_size only) + HTTP HEAD",
                                    "file_url": url, "status": "ok", "content_length": len(maps[image]),
                                    "api_file_size": len(maps[image]), "etag": None,
                                    "last_modified": "Thu, 12 Jan 2023 15:57:34 GMT"},
                                   _probe_local(p, maps[image])]})
    x = synthetic_moreau_xlsx(rng)
    p = data / "moreau2020mutations/repo/data/Supplementary_Table_S1.xlsx"
    _write(p, x)
    records.append({"target": "moreau2020mutations", "target_no": 18, "gate": "ungated",
                    "object": L.IDENTITY_OBJECT[L.MOREAU_KEY],
                    "probes": [{"method": "GitHub git-tree listing (recursive)", "status": "ok",
                                "url": "https://github.com/synthetic/scratch/blob/0000000/data/Supplementary_Table_S1.xlsx",
                                "blob_sha": ID.git_blob_of(x), "size": len(x)}, _probe_local(p, x)]})
    idj = root / "identity_refs.json"
    _write(idj, json.dumps({"what": "scratch identity references (synthetic stand-ins)", "records": records},
                           indent=1).encode("utf-8"))
    bdir = root / "builds"
    synthetic_builds(bdir, rng, genes)
    sd7 = None
    if with_sd7:
        xb = synthetic_sd7_book(rng, sd7_variant)
        sp = data / "liu/supplement_syn.xlsx"
        _write(sp, xb)
        sd7 = (str(sp), _sha(xb), len(xb), "https://example.org/synthetic/liu-supplementary-data-registered-copy")
    # R47: Table S4's raw list (the S-build's members) and the MOESM2 stand-in (Table S6 = 107 of them)
    from . import loader as LD
    from . import wp3_pdf as WPDF
    from . import wp3_scratch_pdf as SPDF
    pin("segura_s4_raw", "register_sets_src/segura2025_tables/tableS4_syn.txt", ("\n".join(sorted(s4)) + "\n")
        .encode("utf-8"))
    tsvb = LD.lf((L.REPO / LD.TSV_PATH).read_bytes())
    _, trows = LD.parse_tsv_bytes(tsvb)
    terms = SPDF.s7_terms()
    named = {t["cell_id"] for t in terms if str(t.get("named", "")).startswith("named")}
    tsv = {r["cell_id"]: r["published_value_and_location"] for r in trows if r["cell_id"] in named}
    mp = data / "register_sets_src/segura2025_tables/moesm2_syn.pdf"
    SPDF.write_moesm2(mp, sorted(s4), tsv_named=WPDF.tsv_named_values(tsv, terms), variant=moesm2_variant,
                      s6_genes=sorted(s4)[:107])
    mb = mp.read_bytes()
    pins["segura_moesm2"] = ("register_sets_src/segura2025_tables/moesm2_syn.pdf", "data", _sha(mb), len(mb))
    (root / "decoder_genes.json").write_text(json.dumps({"genes": genes}), encoding="utf-8")
    return L.Roots.scratch(root, pins=pins, identity_json=idj, builds=bdir, sd7_copy=sd7,
                           moreau_clone=data / "moreau2020mutations" / "repo")


DECODER_VARIANTS = ("bad_columns", "dup_symbol", "short_row", "all_q_null", "extra_cols")


def decoder_variant(data: bytes, variant: str) -> bytes:
    doc = json.loads(data)
    cols, rows = doc["columns"], doc["data"]
    if variant == "bad_columns":                       # the FDR column missing (renamed)
        cols[cols.index("p (FDR corrected)")] = "q_renamed"
    elif variant == "dup_symbol":                      # gene_symbol twice
        cols.append("gene_symbol")
        for r in rows:
            r.append(r[0])
    elif variant == "short_row":                       # a row of another length
        rows[3] = rows[3][:-1]
    elif variant == "all_q_null":                      # no row with an HGNC gene and a finite q
        q = cols.index("p (FDR corrected)")
        for r in rows:
            r[q] = None
    elif variant == "extra_cols":                      # extra and reordered columns: accepted, labelled
        order = [5, 0, 3, 1, 4, 2, 6, 7]
        doc["columns"] = [cols[i] for i in order] + ["an extra column"]
        doc["data"] = [[r[i] for i in order] + [1.0] for r in rows]
        doc["an extra key"] = {"note": "ignored and counted"}
        return json.dumps(doc).encode("utf-8")
    else:
        raise ValueError("decoder variant")
    return json.dumps(doc).encode("utf-8")


@contextlib.contextmanager
def scratch_net(roots: L.Roots, *, script: dict | None = None, head_sizes: dict | None = None,
                head_last_modified: dict | None = None, fail_images=(), fail_times: dict | None = None,
                partial_on_fail: bool = False, bad_columns_images=(), head_status: dict | None = None,
                head_html: tuple = ()):
    """fetch_extract's network replaced (no request leaves the process). HEAD: the two decoder URLs (a size-less 200)
    and the two images' NeuroVault file URLs (R45 (e)'s size probe: the scratch pre-freeze Content-Length and
    Last-Modified unless head_sizes / head_last_modified say otherwise; None = no size returned); any other URL raises.
    GET: the two decoder URLs only. script {image: [outcome per GET, ...]} scripts each GET in order (then 'ok'):
    'ok'; ('curl', n) - CalledProcessError(n) (a partial body written first if partial_on_fail); ('http', n) - the body
    written, then RuntimeError('HTTP <n> for <url>') as fetch_util.get raises it; 'html' - an HTML body, then
    RuntimeError('HTML page returned ...'); one of DECODER_VARIANTS - that output. The older knobs map onto it:
    fail_images (every GET curl 28), fail_times {image: n} (the first n GETs curl 28), bad_columns_images."""
    import subprocess
    root = Path(roots.data).parent
    genes = json.loads((root / "decoder_genes.json").read_text(encoding="utf-8"))["genes"]
    hg_path, _ = roots.pin("hgnc")
    from . import wp3_genes as WG
    hg = WG.HGNCTable(hg_path.read_bytes())
    ent = {}
    for kind, tab in hg.ids.items():
        if kind == "entrez":
            for k, syms in tab.items():
                if len(syms) == 1:
                    ent[next(iter(syms))] = k
    ids = {g: (None, ent[g]) for g in genes if g in ent}
    urls = {L.DECODER_URL.format(image=i): i for i in L.SEGURA_IMAGES}
    idr = L.identity_records(roots, lambda p: Path(p).read_bytes())
    files = {idr[L.SEGURA_MAP_KEY[i]]["file_url"]: i for i in L.SEGURA_IMAGES}
    calls = []
    plan = {i: list(v) for i, v in (script or {}).items()}
    for i in fail_images:
        plan[i] = [("curl", 28)] * 50
    for i, n in (fail_times or {}).items():
        plan[i] = [("curl", 28)] * int(n) + plan.get(i, [])
    for i in bad_columns_images:
        plan[i] = plan.get(i, []) + ["bad_columns"]

    def head(url):
        calls.append(("head", url))
        if url in urls:
            return {"status_code": 200, "content_length": None, "last_modified": None, "etag_md5": None}
        if url in files:
            im = files[url]
            ref = idr[L.SEGURA_MAP_KEY[im]]
            cl = (head_sizes or {}).get(im, ref["content_length"])
            lm = (head_last_modified or {}).get(im, ref.get("last_modified"))
            return {"status_code": (head_status or {}).get(im, 200), "content_length": cl, "last_modified": lm,
                    "etag_md5": None,
                    "content_type_label": FE.CONTENT_TYPE_HTML if im in head_html else FE.CONTENT_TYPE_OTHER}
        raise RuntimeError("scratch net: unexpected URL")

    def get(url, out):
        calls.append(("get", url))
        if url not in urls:
            raise RuntimeError("scratch net: refused")
        im = urls[url]
        step = plan.get(im, [])
        what = step.pop(0) if step else "ok"
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        if isinstance(what, tuple) and what[0] == "curl":
            if partial_on_fail:
                Path(out).write_bytes(b"{\"columns\": [\"gene_sym")
            raise subprocess.CalledProcessError(int(what[1]), ["curl"])
        if isinstance(what, tuple) and what[0] == "http":
            Path(out).write_bytes(b"<html><body>server error</body></html>")
            raise RuntimeError(f"HTTP {int(what[1])} for {url}")
        if what == "html":
            Path(out).write_bytes(b"<!doctype html><html><body>maintenance</body></html>")
            raise RuntimeError(f"HTML page returned for {url} (text/html)")
        rng = np.random.default_rng(SEED + im)
        data = synthetic_decoder_json(genes, ids, [], rng)
        if what != "ok":
            data = decoder_variant(data, what)
        Path(out).write_bytes(data)
        return {"url": url, "path": str(out), "bytes": len(data), "sha256": _sha(data), "content_type": "application/json"}

    def stream(url):
        raise RuntimeError("scratch net: no stream")
    old = dict(FE.NET)
    FE.NET.update(head=head, get=get, stream=stream)
    try:
        yield calls
    finally:
        FE.NET.clear()
        FE.NET.update(old)


def make_header_logging_standins(roots: L.Roots) -> None:
    """Fix round 1 (A1; the reviewer's x2_build.py): rewrite the two Segura stand-ins so that nibabel LOGS while parsing
    their headers through its own 'nibabel.global' logger - 790618: qfac (pixdim[0]) 0 and vox_offset 360 (loads; level
    20 / 30 messages); 781986: magic b'S12\0' (level 45: logged, then raises) - and update the scratch identity
    references to the new bytes."""
    import struct
    idj = Path(roots.identity_json)
    doc = json.loads(idj.read_bytes())
    for image in L.SEGURA_IMAGES:
        rec = [r for r in doc["records"] if r["object"] == L.IDENTITY_OBJECT[L.SEGURA_MAP_KEY[image]]][0]
        p = Path([q for q in rec["probes"] if q["method"].startswith("local")][0]["path"])
        raw = bytearray(gzip.decompress(p.read_bytes()))
        if image == 790618:
            struct.pack_into("<f", raw, 76, 0.0)          # pixdim[0] (qfac) = 0
            struct.pack_into("<f", raw, 108, 360.0)       # vox_offset 360 (not divisible by 16)
            raw = raw[:352] + bytearray(8) + raw[352:]
        else:
            raw[344:348] = b"S12\x00"                     # an invalid magic string
        data = gzip.compress(bytes(raw), mtime=0)
        p.write_bytes(data)
        rec["probes"][0]["content_length"] = len(data)
        rec["probes"][0]["api_file_size"] = len(data)
        rec["probes"][1].update(size=len(data), sha256=_sha(data), git_blob_sha=ID.git_blob_of(data))
    idj.write_bytes(json.dumps(doc, indent=1).encode("utf-8"))


def local_path(roots: L.Roots, key: str) -> Path:
    """The scratch identity reference's local copy of a source carrier."""
    doc = json.loads(Path(roots.identity_json).read_bytes())
    rec = [r for r in doc["records"] if r["object"] == L.IDENTITY_OBJECT[key]][0]
    return Path([q for q in rec["probes"] if q["method"].startswith("local")][0]["path"])
