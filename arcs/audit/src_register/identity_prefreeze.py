"""Pre-freeze work (claims register v4 section 1.10 (0), verification finding NF11): the identity of every registered
map and map carrier, by URL, byte size and ETag / git blob id, with the date of the listing; plus the GIA-MDD path
assertion of register section 2.3 against Giacomel's repository tree listings at e045bc5 and eda33ab.

LISTING-LEVEL ONLY (gates G1 / G2 closed; Dear and Vairam / Roy deferred): HTTP HEAD (status, Content-Length, ETag,
Last-Modified), GitHub git-tree listings (path, blob sha, size), NeuroVault image metadata JSON (only the fields `file`,
`file_size`, `surface_left_file`, `surface_right_file` are read; nothing else is kept or printed; no image is fetched),
the Apollo (Cambridge) DSpace bitstream listing (name, sizeBytes, checksum), and sha256 / git-blob hashes of files that
were already on disk before this session (hashing only; no file is parsed). Unauthenticated requests; no personal
identifier is sent. Prints counts and statuses only.

Outputs: arcs/audit/register_maps/IDENTITY_prefreeze.json, arcs/audit/register_maps/gia_mdd_paths.json.
Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src_register\\identity_prefreeze.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "arcs" / "audit" / "register_maps" / "IDENTITY_prefreeze.json"
OUT_GIA = ROOT / "arcs" / "audit" / "register_maps" / "gia_mdd_paths.json"
UA = {"User-Agent": "asdg-register-prefreeze/1.0 (listing-level identity check)"}
E = Path("E:/data/asdg")
SPR_BUCH = "https://static-content.springer.com/esm/art%3A10.1038%2Fs41593-023-01259-x/MediaObjects/41593_2023_1259_"
SPR_MAMAT = "https://static-content.springer.com/esm/art%3A10.1186%2Fs13229-024-00632-2/MediaObjects/13229_2024_632_"
SPR_RG = "https://static-content.springer.com/esm/art%3A10.1038%2Fs41380-018-0023-7/MediaObjects/41380_2018_23_"
SPR_DEAR = "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41593-024-01624-4/MediaObjects/41593_2024_1624_"
SPR_PAGANI = "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41593-026-02287-z/MediaObjects/41593_2026_2287_"

REPOS = {  # key: (owner, repo, full commit sha or short to resolve)
    "pagani": ("functional-neuroimaging", "biological_subtyping", "ef58cf1622e5b60885919d108b6033d78be84d52"),
    "gia_93de089": ("alegiac95", "METAXCAN_TWAS_ANALYSIS", "93de089b614f72bda25f441518ad04b1e938fb9b"),
    "gia_c022a29": ("alegiac95", "METAXCAN_TWAS_ANALYSIS", "c022a29"),
    "gia_e045bc5": ("alegiac95", "METAXCAN_TWAS_ANALYSIS", "e045bc51961b0425f51bbdf54672d59222cfa8b9"),
    "gia_eda33ab": ("alegiac95", "METAXCAN_TWAS_ANALYSIS", "eda33abddd5acd396caa0ace2817a0bcd427cfe5"),
    "hansen": ("netneurolab", "hansen_crossdisorder_vulnerability", "54d34055bd765a79777437f362fbaf338403926e"),
    "dear": ("richardajdear", "AHBA_gradients", "ab7939cf1811cba6296b882e35e60b09fed7d653"),
    "rasero": ("compneurobilbao", "asd-subtyping-enrichment", "9a333d93dbc6249f3d24e8a492246d62a1f23d31"),
    "enigma": ("MICA-MNI", "ENIGMA", "b08974b55243060cbc1fad12c87048037446e8f7"),
    "moreau": ("kkumar-iitkgp-livia", "GeneExp_and_CNV_FCsignatures", "9e8af9c1ea094247ba1ee8824daeb7339a0a0d0e"),
    "subparc": ("RafaelRomeroGarcia", "subParcellation", "e351b3cf03fac04713eb915b5754e6144998f757"),
}
ENIGMA_SS = "enigmatoolbox/datasets/summary_statistics/"
LEY = E / "leyhausen2024intrinsic" / "neurovault_12301"

# (target, target_no, gate, object, [probes]); probe = (kind, ...)
ITEMS = [
    ("pagani2026crossspecies", 13, "G1", "hyper Cohen's d map (GitHub, paper-cited; governs)",
     [("gh", "pagani", "cognitive_maps/00_mean_regressed_global_connectivity_maps/stats_two_sample_ASD_hyper_vs_CTR_cohensd_global_connectivity_voxelwise_smoothed.nii.gz")]),
    ("pagani2026crossspecies", 13, "G1", "hypo Cohen's d map (GitHub, paper-cited; governs)",
     [("gh", "pagani", "cognitive_maps/00_mean_regressed_global_connectivity_maps/stats_two_sample_ASD_hypo_vs_CTR_cohensd_global_connectivity_voxelwise_smoothed.nii.gz")]),
    ("pagani2026crossspecies", 13, "G1", "NeuroVault 14698 image 798767 (hyper; byte-equality with GitHub asserted at download)",
     [("nv", 798767, 14698, ("file",))]),
    ("pagani2026crossspecies", 13, "G1", "NeuroVault 14698 image 798768 (hypo)", [("nv", 798768, 14698, ("file",))]),
    ("pagani2026crossspecies", 13, "G1", "Supplementary Table 3 (decoded lists; gated set carrier) MOESM4",
     [("head", SPR_PAGANI + "MOESM4_ESM.xlsx")]),
    ("benkarim2021connectivity", 14, "G1", "NeuroVault 8667 image 404555 sdistRaw (SD)", [("nv", 404555, 8667, ("file",))]),
    ("benkarim2021connectivity", 14, "G1", "NeuroVault 8667 image 404554 edistRaw (DD)", [("nv", 404554, 8667, ("file",))]),
    ("park2021subcortico", 17, "G1", "NeuroVault 743 image 396720 (registered map)", [("nv", 396720, 743, ("file",))]),
    ("park2021subcortico", 17, "G1", "NeuroVault 743 image 319367 (descriptor image)", [("nv", 319367, 743, ("file",))]),
] + [
    ("leyhausen2024intrinsic", 20, "G2", "NeuroVault 12301 image %d (%s)" % (iid, nm),
     [("nv", iid, 12301, ("file", "surface_left_file", "surface_right_file")),
      ("local", LEY / ("image_%d_t-map_%s.nii.gz" % (iid, tag))),
      ("local", LEY / ("image_%d_t-map_%s.fsaverage.lh.func.gii" % (iid, tag))),
      ("local", LEY / ("image_%d_t-map_%s.fsaverage.rh.func.gii" % (iid, tag)))])
    for iid, nm, tag in [(777428, "MSD", "m"), (777429, "PF", "pf"), (777430, "RF", "r")]
] + [
    ("giacomel2026cartography", 3, "G2", "ENIGMA_structural_organised.xlsx @93de089 (Thickness / Subcortical / MDD; governs)",
     [("gh", "gia_93de089", "data/ENIGMA/ENIGMA_structural_organised.xlsx")]),
    ("giacomel2026cartography", 3, "G2", "ENIGMA_structural_organised.xlsx @c022a29 (compared with 93de089; local copy)",
     [("gh", "gia_c022a29", "data/ENIGMA/ENIGMA_structural_organised.xlsx"),
      ("local", E / "enigma_asd" / "giacomel2026_repo" / "data" / "ENIGMA" / "ENIGMA_structural_organised.xlsx")]),
    ("hansen2022local", 19, "G2", "enigma_ct.csv (y: column asd)",
     [("gh", "hansen", "data/enigma_ct.csv"), ("local", E / "hansen2022local" / "repo" / "data" / "enigma_ct.csv")]),
    ("hansen2022local", 19, "G2", "gene_pc1.csv (component)",
     [("gh", "hansen", "data/predictors/gene_pc1.csv"),
      ("local", E / "hansen2022local" / "repo" / "data" / "predictors" / "gene_pc1.csv")]),
    ("liu2026spatiotemporal", 10, "G2", "LIU-T3 y: ENIGMA Toolbox asd meta-analysis CortThick",
     [("gh", "enigma", ENIGMA_SS + "asd_meta-analysis_case-controls_CortThick.csv"),
      ("local", E / "enigma_asd" / "enigma_toolbox" / Path(ENIGMA_SS) / "asd_meta-analysis_case-controls_CortThick.csv")]),
    ("liu2026spatiotemporal", 10, "G2", "LIU-T3 y: ENIGMA Toolbox asd meta-analysis SubVol",
     [("gh", "enigma", ENIGMA_SS + "asd_meta-analysis_case-controls_SubVol.csv"),
      ("local", E / "enigma_asd" / "enigma_toolbox" / Path(ENIGMA_SS) / "asd_meta-analysis_case-controls_SubVol.csv")]),
    ("patel2021virtual", 2, "G2", "eTable 4 (supplement PDF p. 26)",
     [("head", "https://pmc.ncbi.nlm.nih.gov/articles/instance/7450410/bin/jamapsychiatry-e202694-s001.pdf"),
      ("head", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7450410/supplementaryFiles"),
      ("local", E / "patel2021virtual" / "supp" / "jamapsychiatry-e202694-s001.pdf")]),
    ("pretzsch2024patterns", 16, "G2", "eTable13 loadings (Supplement 2; Europe PMC supplementary archive; derived CSV on disk)",
     [("head", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11581727/supplementaryFiles"),
      ("local", E / "pretzsch2024patterns" / "derived" / "eTable13_glasser360_pls_comp1_loadings.csv")]),
    ("dear2024corticalgene", 15, "deferred (G1+G2 once provenance is established)", "Supplementary Tables 1-4 workbook (Supp Table 4 = y) MOESM3",
     [("head", SPR_DEAR + "MOESM3_ESM.xlsx")]),
    ("dear2024corticalgene", 15, "deferred", "repo data/brainchart_maps_dk.csv (y check copy)",
     [("gh", "dear", "data/brainchart_maps_dk.csv")]),
    ("dear2024corticalgene", 15, "deferred", "repo outputs/ahba_dme_scores_in_dk.csv (components, DK projection)",
     [("gh", "dear", "outputs/ahba_dme_scores_in_dk.csv")]),
    ("dear2024corticalgene", 15, "deferred", "repo outputs/ahba_dme_hcp_top8kgenes_weights.csv / _scores.csv (listed)",
     [("gh", "dear", "outputs/ahba_dme_hcp_top8kgenes_weights.csv"), ("gh", "dear", "outputs/ahba_dme_hcp_top8kgenes_scores.csv")]),
    ("rasero2023neurogenetics", 6, "G1", "notebook 05-mdmr_subtypes_vs_TDC.ipynb (carrier of y_S1, y_S2)",
     [("ghname", "rasero", "05-mdmr_subtypes_vs_TDC.ipynb")]),
    ("rasero2023neurogenetics", 6, "G1", "notebook 08-calculate_gen_pvals.ipynb (per-gene step; ML_Lag weights)",
     [("ghname", "rasero", "08-calculate_gen_pvals.ipynb")]),
    ("rasero2023neurogenetics", 6, "G1", "results/desikan/Subtype_{1,2}_r2_gen_association_results.csv (RA-11 ... 14 lists)",
     [("gh", "rasero", "results/desikan/Subtype_1_r2_gen_association_results.csv"),
      ("gh", "rasero", "results/desikan/Subtype_2_r2_gen_association_results.csv")]),
    ("rasero2023neurogenetics", 6, "G1", "journal mmc1.pdf", [("head", "https://ars.els-cdn.com/content/image/1-s2.0-S0006322323012301-mmc1.pdf")]),
    ("buch2023asdsubgroups", 7, "G1", "MOESM3.xlsx (Supplementary Tables 4-5)", [("head", SPR_BUCH + "MOESM3_ESM.xlsx")]),
] + [
    ("mamat2025molecular", 8, "G1", "Additional file %d" % k, [("head", SPR_MAMAT + "MOESM%d_ESM.%s" % (k, "pdf" if k == 1 else "xlsx"))])
    for k in (1, 2, 3, 4)
] + [
    ("romerogarcia2019synaptic", 4, "G1", "MOESM%d" % k, [("head", SPR_RG + "MOESM%d_ESM.%s" % (k, "xlsx" if k == 3 else "docx"))])
    for k in (1, 2, 3)
] + [
    ("romerogarcia2019synaptic", 4, "G1", "Apollo record 10.17863/CAM.17116 (handle 1810/273626): every bitstream",
     [("apollo", "1810/273626")]),
    ("romerogarcia2019synaptic", 4, "public atlas (not a carrier)", "DK-308 lh.500.aparc.annot @e351b3cf (subParcellation)",
     [("gh", "subparc", "500mm parcellation (308 regions)/lh.500.aparc.annot"),
      ("local", E / "romerogarcia2019synaptic" / "repos" / "subParcellation" / "500mm parcellation (308 regions)" / "lh.500.aparc.annot")]),
    ("segura2024symptommapping", 1, "ungated", "NeuroVault 12297 image 790618 (MFG map)",
     [("nv", 790618, 12297, ("file",)),
      ("local", E / "segura2025" / "image_790618_zstat1_ADOS2Total_dm_MFG_iFC_corrected_sex_ADOSPOS_-_AS_TX.nii.nii.gz")]),
    ("segura2024symptommapping", 1, "ungated", "NeuroVault 12297 image 781986 (control map)",
     [("nv", 781986, 12297, ("file",)),
      ("local", E / "segura2025" / "image_781986_zstat1_PostHocSCA_VisualSeed2iFC_NegativeControl.nii.gz")]),
    ("moreau2020mutations", 18, "ungated", "Supplementary_Table_S1.xlsx @9e8af9c1 (sheets 1_16p11.2Del, 3_22q11.2Del)",
     [("gh", "moreau", "data/Supplementary_Table_S1.xlsx"),
      ("local", E / "moreau2020mutations" / "repo_GeneExp_and_CNV_FCsignatures" / "data" / "Supplementary_Table_S1.xlsx")]),
]
NOT_RECORDED = [
    ("seelemeyer2025decomposing", "G2", "NeuroVault 13397 rejected by register 1.7 (N 535 vs 428); no registered map"),
    ("wan2026abide2multiplex", "G1", "not auditable (no map obtainable; register 2.12)"),
    ("berto2022connectivity", "G1", "not auditable (controlled PsychENCODE expression; register 2.5); no registered map"),
    ("xing2026interpretable", "ungated", "not auditable (axis region sets unpublished; register 2.11)"),
    ("vairam2026hyperhypo", "deferred", "deferred; no derived map deposited (register 2.9)"),
    ("mamat2025molecular", "G1", "bioRxiv DC1-DC4 supplements: HEAD returned no Content-Length in the draft; not re-probed (journal files govern)"),
]

_tree_cache: dict = {}
_commit_full: dict = {}


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha(p: Path) -> str:
    size = p.stat().st_size
    h = hashlib.sha1(b"blob %d\0" % size)
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha_lf(p: Path):
    """git blob id of the file with CRLF -> LF (a Windows checkout of a text file); None for non-text suffixes."""
    if p.suffix.lower() not in (".csv", ".tsv", ".txt"):
        return None
    b = p.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()


def get(url, **kw):
    for attempt in range(3):
        try:
            return requests.get(url, headers=UA, timeout=90, **kw)
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(3)


def head(url: str) -> dict:
    rec = {"method": "HTTP HEAD", "url": url, "listed_utc": now()}
    try:
        r = None
        for attempt in range(3):
            try:
                r = requests.head(url, headers=UA, timeout=90, allow_redirects=True)
                break
            except requests.RequestException:
                if attempt == 2:
                    raise
                time.sleep(3)
        rec.update(status_code=r.status_code, final_url=r.url if r.url != url else None,
                   content_length=int(r.headers["Content-Length"]) if "Content-Length" in r.headers else None,
                   etag=r.headers.get("ETag"), last_modified=r.headers.get("Last-Modified"),
                   content_type=r.headers.get("Content-Type"))
        ctype = (r.headers.get("Content-Type") or "").lower()
        if r.status_code != 200:
            rec.update(status="unreachable", error="HTTP %d" % r.status_code)
        elif ctype.startswith("text/html") and not url.lower().endswith((".html", ".htm")):
            rec.update(status="unreachable", error="HTML page returned for a file URL (interstitial; Content-Length %s)"
                       % rec["content_length"])
        elif rec["content_length"] is None:
            rec.update(status="reachable, size not returned by HEAD")
        else:
            rec.update(status="ok")
    except Exception as e:  # noqa: BLE001
        rec.update(status="unreachable", error="%s: %s" % (type(e).__name__, str(e)[:200]))
    return rec


def resolve_commit(owner, repo, ref) -> str:
    if len(ref) == 40:
        return ref
    key = (owner, repo, ref)
    if key not in _commit_full:
        r = get("https://api.github.com/repos/%s/%s/commits/%s" % (owner, repo, ref))
        r.raise_for_status()
        _commit_full[key] = r.json()["sha"]
    return _commit_full[key]


def tree(key: str) -> dict:
    if key not in _tree_cache:
        owner, repo, ref = REPOS[key]
        full = resolve_commit(owner, repo, ref)
        r = get("https://api.github.com/repos/%s/%s/git/trees/%s" % (owner, repo, full), params={"recursive": "1"})
        r.raise_for_status()
        j = r.json()
        _tree_cache[key] = {"commit": full, "truncated": bool(j.get("truncated")), "listed_utc": now(),
                            "entries": {e["path"]: e for e in j["tree"]}, "n_entries": len(j["tree"])}
    return _tree_cache[key]


def gh(key: str, path: str) -> dict:
    owner, repo, _ = REPOS[key]
    rec = {"method": "GitHub git-tree listing (recursive)", "repo": "%s/%s" % (owner, repo)}
    try:
        t = tree(key)
        rec.update(commit=t["commit"], listed_utc=t["listed_utc"], tree_truncated=t["truncated"],
                   url="https://github.com/%s/%s/blob/%s/%s" % (owner, repo, t["commit"], quote(path)), path=path)
        e = t["entries"].get(path)
        if e is None:
            rec.update(status="unreachable", error="path absent from the tree listing")
        else:
            rec.update(status="ok", type=e["type"], blob_sha=e["sha"], size=e.get("size"))
    except Exception as ex:  # noqa: BLE001
        rec.update(status="unreachable", error="%s: %s" % (type(ex).__name__, str(ex)[:200]), path=path)
    return rec


def ghname(key: str, basename: str) -> dict:
    try:
        t = tree(key)
        hits = [p for p in t["entries"] if p.split("/")[-1] == basename]
    except Exception as ex:  # noqa: BLE001
        return {"method": "GitHub git-tree listing", "status": "unreachable", "error": "%s: %s" % (type(ex).__name__, str(ex)[:200])}
    if len(hits) != 1:
        return {"method": "GitHub git-tree listing", "status": "unreachable",
                "error": "basename %s found %d times in the tree" % (basename, len(hits)), "hits": hits}
    return gh(key, hits[0])


def nv(image_id: int, collection: int, fields) -> list:
    """NeuroVault image metadata: read only file / size fields; HEAD each file URL (no image fetched)."""
    api = "https://neurovault.org/api/images/%d/" % image_id
    base = {"method": "NeuroVault image metadata (file, file_size only) + HTTP HEAD", "api_url": api, "listed_utc": now()}
    try:
        r = get(api)
        if r.status_code != 200:
            return [dict(base, status="unreachable", error="HTTP %d" % r.status_code)]
        j = r.json()
        kept = {k: j.get(k) for k in ("file", "file_size", "surface_left_file", "surface_right_file")}
        del j  # nothing else from the metadata is kept
    except Exception as ex:  # noqa: BLE001
        return [dict(base, status="unreachable", error="%s: %s" % (type(ex).__name__, str(ex)[:200]))]
    out = []
    for f in fields:
        u = kept.get(f)
        if not u:
            out.append(dict(base, field=f, status="unreachable", error="field %s empty in the metadata" % f))
            continue
        u = re.sub(r"^http://", "https://", u)
        coll_ok = ("/media/images/%d/" % collection) in u
        h = head(u)
        rec = dict(base, field=f, file_url=u, collection_in_url_matches=coll_ok,
                   api_file_size=kept.get("file_size") if f == "file" else None)
        rec.update({k: v for k, v in h.items() if k not in ("method", "url", "listed_utc")})
        rec["head_listed_utc"] = h["listed_utc"]
        if f == "file" and rec.get("content_length") is not None and kept.get("file_size") is not None:
            rec["api_size_equals_head"] = int(kept["file_size"]) == rec["content_length"]
        out.append(rec)
    return out


def local(p: Path) -> dict:
    rec = {"method": "local file already on disk (hashed only, not parsed)", "path": str(p), "listed_utc": now()}
    if not p.exists():
        rec.update(status="absent")
        return rec
    st = p.stat()
    rec.update(status="ok", size=st.st_size, mtime_utc=dt.datetime.fromtimestamp(st.st_mtime, dt.timezone.utc).replace(microsecond=0).isoformat(),
               sha256=sha256_file(p), git_blob_sha=git_blob_sha(p))
    lf = git_blob_sha_lf(p)
    if lf is not None and lf != rec["git_blob_sha"]:
        rec["git_blob_sha_crlf_to_lf"] = lf
    return rec


def apollo(handle: str) -> list:
    base = {"method": "Apollo DSpace 7 REST listing (bundles / bitstreams: name, sizeBytes, checksum)", "handle": handle,
            "listed_utc": now()}
    try:
        r = get("https://api.repository.cam.ac.uk/server/api/pid/find", params={"id": handle}, allow_redirects=True)
        r.raise_for_status()
        item = r.json()
        uuid = item["uuid"]
        rb = get("https://api.repository.cam.ac.uk/server/api/core/items/%s/bundles" % uuid, params={"size": 50})
        rb.raise_for_status()
        out = []
        for b in rb.json()["_embedded"]["bundles"]:
            bs = get(b["_links"]["bitstreams"]["href"], params={"size": 100})
            bs.raise_for_status()
            for s in bs.json()["_embedded"]["bitstreams"]:
                out.append(dict(base, status="ok", item_uuid=uuid, bundle=b["name"], name=s["name"], size=s.get("sizeBytes"),
                                checksum=(s.get("checkSum") or {}).get("value"),
                                checksum_algorithm=(s.get("checkSum") or {}).get("checkSumAlgorithm"),
                                bitstream_uuid=s["uuid"],
                                url="https://www.repository.cam.ac.uk/bitstreams/%s/download" % s["uuid"]))
        return out or [dict(base, status="unreachable", error="no bitstreams listed")]
    except Exception as ex:  # noqa: BLE001
        return [dict(base, status="unreachable", error="%s: %s" % (type(ex).__name__, str(ex)[:200]))]


def run_probe(p) -> list:
    kind = p[0]
    if kind == "head":
        return [head(p[1])]
    if kind == "gh":
        return [gh(p[1], p[2])]
    if kind == "ghname":
        return [ghname(p[1], p[2])]
    if kind == "nv":
        return nv(p[1], p[2], p[3])
    if kind == "local":
        return [local(p[1])]
    if kind == "apollo":
        return apollo(p[1])
    raise ValueError(kind)


def gia_mdd() -> dict:
    """Register 2.3: the GIA-MDD set files at e045bc5 and the eda33ab MDD GEDAR map files (paths asserted, never fetched)."""
    need_e045 = ["results/MDD/MDD_top_pos_genes_thr_1.tsv", "results/MDD/MDD_top_neg_genes_thr_10.tsv",
                 "results/MDD/MDD_top_genes_thr_1.tsv", "results/MDD/MDD_top_genes_thr_5.tsv", "results/MDD/MDD_top_genes_thr_10.tsv"]
    rec = {"what": "register 2.3 GIA-MDD paths, asserted against the GitHub tree listings (listing only; no content fetched)"}
    rows = []
    for pth in need_e045:
        g = gh("gia_e045bc5", pth)
        rows.append({"commit": g.get("commit"), "path": pth, "present": g["status"] == "ok", "blob_sha": g.get("blob_sha"),
                     "size": g.get("size"), "listed_utc": g.get("listed_utc"), "error": g.get("error")})
    rec["e045bc5_sets"] = rows
    t = tree("gia_eda33ab")
    asd_maps = sorted(p for p in t["entries"] if re.fullmatch(r"results/ASD/ASD_TPRS_thr_\d+\.tsv", p))
    mdd_all = sorted(p for p in t["entries"] if p.startswith("results/MDD/"))
    mdd_maps = sorted(p for p in mdd_all if re.fullmatch(r"results/MDD/MDD_TPRS_thr_\d+\.tsv", p))
    rec["eda33ab_rule"] = ("the MDD counterpart of the ASD combined-scheme GEDAR maps results/ASD/ASD_TPRS_thr_*.tsv (draft 1 row 6): "
                           "results/MDD/MDD_TPRS_thr_<thr>.tsv; thresholds 1, 5, 10 needed (GIA-MDD-C1 / C5 / C10)")
    rec["eda33ab_asd_counterparts"] = [{"path": p, "blob_sha": t["entries"][p]["sha"], "size": t["entries"][p].get("size")} for p in asd_maps]
    rec["eda33ab_mdd_maps"] = [{"path": p, "blob_sha": t["entries"][p]["sha"], "size": t["entries"][p].get("size")} for p in mdd_maps]
    rec["eda33ab_needed"] = []
    for thr in (1, 5, 10):
        pth = "results/MDD/MDD_TPRS_thr_%d.tsv" % thr
        e = t["entries"].get(pth)
        rec["eda33ab_needed"].append({"commit": t["commit"], "path": pth, "present": e is not None,
                                      "blob_sha": e["sha"] if e else None, "size": e.get("size") if e else None,
                                      "listed_utc": t["listed_utc"]})
    rec["eda33ab_results_MDD_listing"] = [{"path": p, "type": t["entries"][p]["type"], "blob_sha": t["entries"][p]["sha"],
                                           "size": t["entries"][p].get("size")} for p in mdd_all]
    te = tree("gia_e045bc5")
    rec["e045bc5_results_MDD_listing"] = [{"path": p, "type": te["entries"][p]["type"], "blob_sha": te["entries"][p]["sha"],
                                           "size": te["entries"][p].get("size")} for p in sorted(te["entries"]) if p.startswith("results/MDD/")]
    rec["tree_truncated"] = {"e045bc5": te["truncated"], "eda33ab": t["truncated"]}
    return rec


def main() -> int:
    records = []
    for target, tno, gate, obj, probes in ITEMS:
        res = []
        for p in probes:
            res.extend(run_probe(p))
        records.append({"target": target, "target_no": tno, "gate": gate, "object": obj, "probes": res})
    # cross-checks without content: local git-blob sha vs the tree's blob sha where both exist
    for rec in records:
        ghs = [p for p in rec["probes"] if p.get("method", "").startswith("GitHub") and p.get("status") == "ok"]
        los = [p for p in rec["probes"] if p.get("method", "").startswith("local") and p.get("status") == "ok"]
        if ghs and los:
            rec["local_blob_equals_tree_blob"] = [lo["git_blob_sha"] == g["blob_sha"] for g, lo in zip(ghs, los)]
            if not all(rec["local_blob_equals_tree_blob"]):
                rec["local_blob_equals_tree_blob_after_crlf_to_lf"] = [lo.get("git_blob_sha_crlf_to_lf") == g["blob_sha"]
                                                                       for g, lo in zip(ghs, los)]
    gia = gia_mdd()
    status_counts: dict = {}
    unreachable = []
    for rec in records:
        for p in rec["probes"]:
            s = p.get("status")
            status_counts[s] = status_counts.get(s, 0) + 1
            if s in ("unreachable", "absent"):
                unreachable.append({"target": rec["target"], "object": rec["object"], "method": p.get("method"),
                                    "url_or_path": p.get("url") or p.get("file_url") or p.get("path") or p.get("api_url"),
                                    "error": p.get("error", s)})
    out = {
        "what": ("Identity of every registered map and map carrier before the freeze (claims register v4 section 1.10 (0); NF11): "
                 "URL, byte size, ETag / git blob id, listing date. Listing-level only; sha256 of gated remote files is taken at "
                 "download under the gate (a mismatch with this record -> 'not auditable (map changed)')."),
        "run_utc": now(),
        "script": {"path": "arcs/audit/src_register/identity_prefreeze.py", "sha256": sha256_file(Path(__file__)),
                   "repo_head_at_run": subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()},
        "github_trees": {k: {"repo": "%s/%s" % REPOS[k][:2], "commit": v["commit"], "n_entries": v["n_entries"],
                             "truncated": v["truncated"], "listed_utc": v["listed_utc"]} for k, v in _tree_cache.items()},
        "records": records,
        "not_recorded": [{"target": a, "gate": b, "reason": c} for a, b, c in NOT_RECORDED],
        "summary": {"n_objects": len(records), "n_probes": sum(len(r["probes"]) for r in records), "status_counts": status_counts,
                    "unreachable": unreachable},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for path, obj in ((OUT, out), (OUT_GIA, dict(gia, run_utc=now(), script=out["script"]))):
        txt = json.dumps(obj, indent=1, ensure_ascii=False)
        path.write_text(txt, encoding="utf-8", newline="\n")
        assert json.loads(path.read_text(encoding="utf-8")) == json.loads(txt)
    print("objects %d, probes %d, statuses %s" % (len(records), out["summary"]["n_probes"], status_counts))
    for u in unreachable:
        print("UNREACHABLE: %s | %s | %s" % (u["target"], u["object"][:60], u["error"]))
    for r_ in gia["e045bc5_sets"] + gia["eda33ab_needed"]:
        print("GIA-MDD %s %s present=%s blob=%s size=%s" % (r_["commit"][:7] if r_["commit"] else "?", r_["path"], r_["present"],
                                                           r_["blob_sha"], r_["size"]))
    print("eda33ab results/MDD entries %d; MDD_TPRS maps %d" % (len(gia["eda33ab_results_MDD_listing"]), len(gia["eda33ab_mdd_maps"])))
    print("outputs: %s sha256 %s; %s sha256 %s" % (OUT.relative_to(ROOT).as_posix(), sha256_file(OUT),
                                                   OUT_GIA.relative_to(ROOT).as_posix(), sha256_file(OUT_GIA)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
