"""WP3 (RUN_PLAN.md v3.1 §18, FROZEN): the fixed layout shared by the material stage (wp3_material.py, phase 2) and
the real loaders (real_sources.py): runner-built paths, object keys, pins, the identity references, the declarations
the material stage reads with, and the status vocabulary. Nothing here opens a carrier; `Roots.production()` names
paths only.

Paths (R18 `RUN_PLAN.md:826-847`; fetch_extract FE10):
  records   <main repo>/arcs/audit/register_maps/post_freeze/ungated/<key>.json   one R18 record per object (committed)
  manifest  <main repo>/arcs/audit/register_maps/post_freeze/ungated/wp3_material_manifest.json   the phase-2 manifest:
            every object's runner-built path and sha256, its record, its status (the loaders' only index)
  objects   <main repo>/artifacts/audit/wp3/ungated/<key>/<key>_extract.json   (§8 step 5; artifacts/ is git-ignored)
  control   <main repo>/arcs/audit/run_manifests/material/ungated/   deletion requests (FE10)
  logs      <main repo>/artifacts/audit/material_logs/ungated/<key>.log
  data      E:/data/asdg (carriers stay where the pre-freeze identity record found them: U-W3-1)
  quarantine E:/data/asdg/_quarantine
A scratch layout (tests, the phase-1 demonstration) puts every path under one scratch directory and replaces the
identity references and file pins by scratch ones; the register files (TSV, register_sets/, mist64_classes.json) are
always read from the repository.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
GATE = "ungated"

# ---- status vocabulary (TSV / plan strings and the WP3 phase-1 additions, each cited) --------------------------------
STATUS_PENDING = "not run (phase 2 material pending)"                        # until wp3_material has run (WP3 phase 2)
STATUS_MAP_CHANGED = "not auditable (map changed)"                            # RUN_PLAN §17 :1703-1704 (identity at use)
STATUS_QUARANTINE = "refused: a source path lies under the quarantine (RUN_PLAN section 8 step 6)"
STATUS_LAYOUT = "not auditable (definition not applicable: the declared Moreau sheet layout not matched)"   # §8 step 4
# RUN_PLAN_amend_3 R46 declares SD7 (the registered copy, a sheet-name rule, an ASD-anchored column rule); a scratch
# layout without an SD7 stand-in reads this (production always has the registered copy)
STATUS_SD7_PENDING = "not run (no SD7 copy in this scratch layout)"
STATUS_OBJECT_CHANGED = "refused: a phase-2 object differs from the phase-2 manifest (sha256)"
STATUS_STAGE_REFUSED = "not run (the phase-2 material stage refused this object: %s)"
STATUS_NO_FIXED_COMPONENT = "refused: no ungated row reads a fixed component (MOR-C1 ... C3 are PLS components on S)"
# fix round 1 (A2): a carrier read at use outside a clean read (absent, locked, moved, unparseable): never a traceback
STATUS_USE_UNREADABLE = ("not run (identity at use not established: the source carrier is absent or unreadable at "
                         "use)")
STATUS_USE_FAILED = "not run (a source carrier could not be read at use: section 8 handler)"
STATUS_PREFLIGHT = "refused (preflight: a check that touches no carrier failed; no carrier was touched)"
STATUS_NOT_FINAL = "not run (phase 2 material not final: the phase-2 manifest is partial)"

# ---- object keys (fetch_extract target keys: [A-Za-z][A-Za-z0-9]*([-_][A-Za-z0-9]+)*) ------------------------------
SEGURA_IMAGES = (790618, 781986)
SEGURA_MAP_KEY = {790618: "segura_790618", 781986: "segura_781986"}
SEGURA_DECODER_KEY = {790618: "segura_decoder_790618", 781986: "segura_decoder_781986"}
# the IDENTITY_prefreeze.json record of each source carrier (its "object" field, exact)
IDENTITY_OBJECT = {
    "segura_790618": "NeuroVault 12297 image 790618 (MFG map)",
    "segura_781986": "NeuroVault 12297 image 781986 (control map)",
    "moreau2020mutations": "Supplementary_Table_S1.xlsx @9e8af9c1 (sheets 1_16p11.2Del, 3_22q11.2Del)",
}
MOREAU_KEY = "moreau2020mutations"
MOREAU_SHEET_KEY = {"1_16p11.2Del": "del16p11", "3_22q11.2Del": "del22q11"}   # fetch_extract.moreau_target's keys
BRAINSPAN_KEY = "brainspan"
AHBA_BUILDS_KEY = "ahba_builds"
SD7_KEY = "liu_sd7"
MOESM2_KEY = "segura_moesm2"                          # RUN_PLAN_amend_3 R47: MOESM2 pp. 38-39 (Tables S6, S7)
# R47 (a): s_extract.py:96-97 (frozen; s_extract.py 30a821a0... in the freeze manifest) - path and sha256
# no download (FE15: the pinned copy is used as found); the register records its source as "Europe PMC PMC12700815
# supplementaryFiles (MOESM2 pdf)" (register_sets/segura_s4.json source) and no URL, so the target's URL field holds a
# placeholder, never a guessed address
MOESM2_URL = "https://none.invalid/segura-moesm2-pinned-copy"
MOESM2_URL_NOTE = ("no URL registered: the url field is a placeholder; the register names Europe PMC PMC12700815 "
                   "supplementaryFiles (MOESM2 pdf); the pinned copy is used as found (FE15)")
# R46 (a): Liu's Supplementary Data 1-15 workbook, the registered copy (register_work/liu2026spatiotemporal.md:21,
# incorporated by reference: claims_register.md:59-61, :2210): path, sha256, bytes, URL
SD7_REGISTERED = (r"E:\data\asdg\liu2026spatiotemporal\supplement\42003_2026_10045_MOESM3_ESM.xlsx",
                  "e2bd735c0f799d8a79f1f4f72d360d1d77a0570986a2beeb9b9be08ac8661242", 1442234,
                  "https://static-content.springer.com/esm/art%3A10.1038%2Fs42003-026-10045-x/MediaObjects/"
                  "42003_2026_10045_MOESM3_ESM.xlsx")
# section 8.1: the Moreau clone directory (decision ev-1a12b80e072f8fa): moved whole after the verified extraction
MOREAU_CLONE_REL = "moreau2020mutations/repo_GeneExp_and_CNV_FCsignatures"
MOREAU_DELETION_REQUEST = {
    "scope": "the working copy and the whole clone directory, both moved within the quarantine folder named above; "
             "any other copy of the workbook by sha256 "
             "c947112ded237be43459c65f896c7ec1f120d6faaed0d5700ed63fb81e302e19 wherever it is (a submodule checkout "
             "elsewhere under the moreau2020mutations folder is possible)",
    "git_note": "removing blob 7a8b62be9b4f182f6a78e378ad1b270c1aa9ec21 means deleting or rewriting the clone; the "
                "public GitHub original kkumar-iitkgp-livia/GeneExp_and_CNV_FCsignatures at 9e8af9c1 preserves "
                "provenance",
    "registered_materials_inside_the_clone": "the two locus lists of TSV rows 615-623 set_S (sha256 prefixes b2b9dbfb "
             "and 3838d75f): surviving copies in E:/data/asdg/register_sets_src/moreau2020_locus and GitHub at "
             "9e8af9c1; the authors' AHBA x MIST64 matrix (57fba8a4), the all-genes set file (5ed37bd9), the "
             "label-shuffle null maps (3bbae5ba, 2cfa86f0, 5f93b8cc, dcd046ff), the random-index file (2fa0cf26) and "
             "the authors' published output tables: GitHub at 9e8af9c1 only",
    "why": "the quarantine follows the frozen name screen (V hits on the plan's do-not-open sheet names), not observed "
           "participant data (RUN_PLAN_amend_3 section 8.1)",
    "deletion": "the operator's step (default 24; RUN_PLAN.md:1279-1285); the wrapper never deletes",
}
MANIFEST_NAME = "wp3_material_manifest.json"          # version 1; version n > 1: wp3_material_manifest.<n>.json
PARTIAL_PREFIX = "wp3_material_manifest.partial"     # partial (non-final) manifests: <prefix>.<n>.json (never read)
MANIFEST_SCHEMA = "a1_wp3_material_manifest_v1"

# ---- the NeuroVault decoder (R22; U-W3-3): URL and the declared columns, from NeuroVault's own source --------------
# neurovault/apps/statmaps/urls.py: r'^images/(?P<pk>\d+)/gene_expression/json$' -> views.gene_expression_json, which
# returns calculate_gene_expression_similarity(map, mask).to_dict("split") without "index" (keys "columns", "data");
# neurovault/apps/statmaps/ahba.py fixes the columns. Read 2026-10-11 at NeuroVault master 9a42434e50b33af8b8967dbc792cde202df4d8ba
# (views.py sha256 d43d05f020bf601f..., ahba.py 3af0ea2a62fd38e4...); the server may run another revision, so the
# extraction fails closed on any difference (the decoder then reads "unavailable" and R22's fallback applies).
DECODER_URL = "https://neurovault.org/images/{image}/gene_expression/json?mask=full"
# fix round 1 (g): re-fetched at the commit (raw.githubusercontent.com/NeuroVault/NeuroVault/<commit>/...) and hashed;
# git blobs equal the GitHub contents API's "sha" at that ref
DECODER_SOURCE = dict(repo="NeuroVault/NeuroVault", commit="9a42434e50b33af8b8967dbc792cde202df4d8ba", files={
    "neurovault/apps/statmaps/views.py": dict(
        sha256="d43d05f020bf601fdc9751344d9baf785b3221f4c89edc8663c14d8c4ab565b9",
        git_blob="d19c6fc63d04365833603ff88402c54dde899517"),
    "neurovault/apps/statmaps/ahba.py": dict(
        sha256="3af0ea2a62fd38e4fff5d2ef7a9e77ee4c51c5d723015ed241ef87b8c8edee1b",
        git_blob="176c9ec3aa46b08bd1db593b3b064c675c68a3eb"),
    "neurovault/apps/statmaps/urls.py": dict(
        sha256="31c558a929822dfa62d0342caff70591d621187c4a6a53648b137cf506532203",
        git_blob="e8fc8b9cdc74ad3a3ab0d08fb8055f6bb71d2fd4")})
DECODER_COLUMNS = ("gene_symbol", "entrez_id.1", "gene_name", "t", "p", "p (FDR corrected)",
                   "variance explained (mean)", "variance explained (std)")      # ahba.py, the order it writes
DECODER_DECLARED = {"symbol": "gene_symbol", "entrez": "entrez_id.1", "t": "t", "p": "p", "q": "p (FDR corrected)"}
DECODER_REQUIRED = ("symbol", "q")   # U-W3-3: R22 needs the gene and its FDR q (both signs kept); the rest optional
DECODER_Q = 0.05            # R22 / TSV rows 1-3: "FDR q < .05, both signs"
# RUN_PLAN_amend_3 R45 (f): up to 3 attempts per image, transport failures only, counted across runs (wp3_decoder)
DECODER_ATTEMPTS = 3

# ---- the TSV map texts that bind a row to its object (U-W3-2) -------------------------------------------------------
SEGURA_MAP_PREFIX = {790618: "NeuroVault 790618 (", 781986: "NeuroVault 781986 ("}
MOREAU_SHEET_TEXT = {"1_16p11.2Del": "sheet 1_16p11.2Del", "3_22q11.2Del": "sheet 3_22q11.2Del"}


# ---- file pins: key -> (path relative to a root, root name, sha256, bytes or None) ----------------------------------
def _pins_production() -> dict:
    from . import ahba_builds as AB
    pins = {
        "aal_atlas": ("abide1_pcp/atlases/aal_roi_atlas.nii.gz", "data", AB.ATLAS["aal"]["nii_sha256"]),  # :1030
        "aal_info": ("aal_atlas_info.csv", "ahba", AB.ATLAS["aal"]["info_sha256"]),
        "dk_info": ("dk_atlas_info.csv", "ahba", AB.ATLAS["dk"]["info_sha256"]),
        # TSV rows 471-477 (map column): "expression_matrix.csv, sha256 e8d98aa0..." (full value)
        "brainspan_expr": ("brainspan/genes_matrix_csv/expression_matrix.csv", "data",
                           "e8d98aa02874f6b12fe7e071f4f88435b88256b6e5c4ba1d799e7b82aad28ee2"),
        # RUN_PLAN_amend_3 R50: results/data_manifests/brainspan_SOURCE.md:22-26 (5e198b7, pre-freeze), sha256 and size
        "brainspan_rows": ("brainspan/genes_matrix_csv/rows_metadata.csv", "data",
                           "dbfea0211aea42f6032084c3cdacb737943cbd786115dc5fde0f754708ae988b"),
        "brainspan_cols": ("brainspan/genes_matrix_csv/columns_metadata.csv", "data",
                           "995a8e75b76459ba2bdbb51ad2db8970272f546baae14ddd3a7df6bc3ac18a01"),
        # register_sets/MANIFEST.json "hgnc" (the S-build's table)
        "hgnc": ("explore_public/hgnc_complete_set/hgnc_complete_set_2026-09-04.txt", "data",
                 "6f43d6ff43aa9fdfa5fb2f20a20a7cace66e6e02e2a0dcf19d9b726e2e248d20"),
        # R22: GO release 2024-01-17 (s_build.PIN go_2024-01-17_*), PANTHER 16.0 PTHR16.0_human (s_build.PIN)
        "go_obo": ("register_sets_src/go_2024-01-17/go-basic.obo", "data",
                   "e078d5406cc78976941578e984e0e3809bc6f4642f8fce404990f5f7c19b0c07"),
        "go_gaf": ("register_sets_src/go_2024-01-17/goa_human.gaf.gz", "data",
                   "3ccc83fe9e18f8c41374787b0cd3b4fb9737a849096b1be5b9f1d3de9ffa7d27"),
        "pthr16": ("register_sets_src/panther_16.0_goslim/PTHR16.0_human", "data",
                   "d605cf6019298892dd0de04c51190879a3df25a2e1c26d23cbca6890c8d2590a"),
        # e3_plants.GAMBA_CSV (the class contexts' brain>body table); R50: gamba_SOURCE.md:27 (GAMBA-MATLAB @0c012868)
        "gamba": ("gamba/Background_genes_null_brain.csv", "data",
                  "442334c3cb487625349fc6e6be6fee121dbc7bdb35b9277133c04032ee0fa53a"),
        # R47 (a), (f): MOESM2 (s_extract.py:96-97) and Table S4's raw list (s_build.py:247-248, segura_s4.json source)
        "segura_moesm2": ("register_sets_src/segura2025_tables/41380_2025_3205_MOESM2_ESM.pdf", "data",
                          "ff55ffe904838fe59d3575261639c0ca922e4c6cfa788e4f7df28c2459a1be93"),
        "segura_s4_raw": ("register_sets_src/segura2025_tables/tableS4_satterstrom_1046_symbols.txt", "data",
                          "e1f4638c61e7fbc82a9867ffaff9c8ce8aa6683d88d784fcf9ffc81415721bea"),
    }
    sizes = {"brainspan_expr": 183262070, "brainspan_rows": 2151132, "brainspan_cols": 43050, "gamba": 268733}
    return {k: (v[0], v[1], v[2], sizes.get(k)) for k, v in pins.items()}


@dataclasses.dataclass(frozen=True)
class Roots:
    repo: str            # register files (TSV, register_sets, register_maps) are read from here
    data: str            # carriers and public reference files (E:/data/asdg)
    artifacts: str       # fetch_extract artifacts root: objects at <artifacts>/ungated/<key>/<key>_extract.json
    records: str         # register_maps/post_freeze (R18)
    control: str         # run_manifests/material (FE10)
    logs: str
    quarantine: str
    ahba: str            # artifacts/ahba (primary matrices, atlas info)
    builds: str          # artifacts/ahba/a1_builds (WP2 venv_ref builds)
    identity_json: str   # IDENTITY_prefreeze.json (frozen, sha256 asserted) or a scratch reference file
    identity_frozen: bool
    pins: tuple          # ((key, (relpath, root, sha256, bytes | None)), ...)
    sd7_copy: tuple | None = None        # R46 (a): (path, sha256, bytes, url); production: SD7_REGISTERED
    moreau_clone: str = ""               # section 8.1: the clone directory moved whole

    # ---- construction -------------------------------------------------------------------------------------------
    @classmethod
    def production(cls, repo: Path | None = None, out_repo: Path | None = None) -> "Roots":
        """The production layout. out_repo: the main repository (RUN_PLAN §2.3 :327-328: outputs go under the main
        repository's tree; run.main_repository resolves it from a worktree)."""
        repo = Path(repo or REPO)
        out = Path(out_repo or repo)
        data = Path("E:/data/asdg")
        return cls(repo=str(repo), data=str(data), artifacts=str(out / "artifacts/audit/wp3"),
                   records=str(out / "arcs/audit/register_maps/post_freeze"),
                   control=str(out / "arcs/audit/run_manifests/material"), logs=str(out / "artifacts/audit/material_logs"),
                   quarantine=str(data / "_quarantine"), ahba=str(repo / "artifacts/ahba"),
                   builds=str(repo / "artifacts/ahba/a1_builds"),
                   identity_json=str(repo / "arcs/audit/register_maps/IDENTITY_prefreeze.json"), identity_frozen=True,
                   pins=tuple(sorted(_pins_production().items())), sd7_copy=SD7_REGISTERED,
                   moreau_clone=str(data / MOREAU_CLONE_REL))

    @classmethod
    def scratch(cls, root: Path, *, pins: dict, identity_json: Path, builds: Path | None = None,
                sd7_copy: tuple | None = None, moreau_clone: Path | None = None, repo: Path | None = None) -> "Roots":
        """Everything under `root` (tests and the phase-1 demonstration); pins and identity references are the
        scratch stand-ins'. The AHBA matrices (allowed in phase 1) stay the repository's unless builds is given."""
        root = Path(root)
        repo = Path(repo or REPO)
        return cls(repo=str(repo), data=str(root / "data"), artifacts=str(root / "out/artifacts/audit/wp3"),
                   records=str(root / "out/arcs/audit/register_maps/post_freeze"),
                   control=str(root / "out/arcs/audit/run_manifests/material"),
                   logs=str(root / "out/artifacts/audit/material_logs"), quarantine=str(root / "data/_quarantine"),
                   ahba=str(repo / "artifacts/ahba"), builds=str(builds or (repo / "artifacts/ahba/a1_builds")),
                   identity_json=str(identity_json), identity_frozen=False,
                   pins=tuple(sorted((k, tuple(v) + (None,) * (4 - len(v))) for k, v in pins.items())),
                   sd7_copy=None if sd7_copy is None else tuple(sd7_copy),
                   moreau_clone=str(moreau_clone or (root / "data" / "moreau2020mutations" / "repo")))

    def to_spec(self) -> dict:
        d = dataclasses.asdict(self)
        d["pins"] = [[k, list(v)] for k, v in self.pins]
        d["sd7_copy"] = None if self.sd7_copy is None else list(self.sd7_copy)
        return d

    @classmethod
    def from_spec(cls, d: dict) -> "Roots":
        d = dict(d)
        d["pins"] = tuple((k, tuple(v)) for k, v in d["pins"])
        d["sd7_copy"] = None if d.get("sd7_copy") is None else tuple(d["sd7_copy"])
        return cls(**d)

    # ---- paths --------------------------------------------------------------------------------------------------
    def pin(self, key: str) -> tuple[Path, str | None]:
        hits = [v for k, v in self.pins if k == key]
        if len(hits) != 1:
            raise KeyError(key)
        rel, root, sha = hits[0][:3]
        base = {"data": self.data, "ahba": self.ahba, "repo": self.repo}[root]
        return Path(base) / rel, sha

    def pin_bytes(self, key: str) -> int | None:
        """R50: the pinned size (None: no size pinned)."""
        hits = [v for k, v in self.pins if k == key]
        if len(hits) != 1:
            raise KeyError(key)
        return hits[0][3] if len(hits[0]) > 3 else None

    @property
    def manifest_path(self) -> Path:
        """The FIRST final manifest's path (version 1); latest_manifest() gives the version the loaders read."""
        return Path(self.records) / GATE / MANIFEST_NAME

    def manifest_versions(self) -> list:
        """[(n, path)] of the final manifests, in version order (fix round 1, B2: never overwritten; a later version
        completes an earlier one, e.g. SD7 once declared)."""
        d = Path(self.records) / GATE
        out = []
        if (d / MANIFEST_NAME).exists():
            out.append((1, d / MANIFEST_NAME))
        if d.is_dir():
            for p in d.glob("wp3_material_manifest.*.json"):
                mid = p.name[len("wp3_material_manifest."):-len(".json")]
                if mid.isdigit() and int(mid) > 1:
                    out.append((int(mid), p))
        return sorted(out)

    def latest_manifest(self) -> Path | None:
        v = self.manifest_versions()
        return v[-1][1] if v else None

    def partial_manifests(self) -> list:
        d = Path(self.records) / GATE
        return sorted(d.glob(PARTIAL_PREFIX + ".*.json")) if d.is_dir() else []

    def record_path(self, key: str) -> Path:
        return Path(self.records) / GATE / f"{key}.json"

    def object_path(self, key: str) -> Path:
        return Path(self.artifacts) / GATE / key / f"{key}_extract.json"

    def fe_roots(self):
        """fetch_extract.Roots of this layout."""
        from . import fetch_extract as FE
        return FE.Roots(repo=Path(self.repo), data=Path(self.data), records=Path(self.records),
                        artifacts=Path(self.artifacts), logs=Path(self.logs), control=Path(self.control),
                        quarantine=Path(self.quarantine))


# ---- identity references ------------------------------------------------------------------------------------------
def identity_records(roots: Roots, read_bytes) -> dict:
    """{object key: {"refs": [identity.ref_from_probe dicts], "local_path": str, "url": str}} for the three source
    carriers, from IDENTITY_prefreeze.json (frozen: sha256 asserted as identity.load_prefreeze does) or a scratch
    reference file of the same record format. read_bytes: the caller's door."""
    from . import identity as ID
    import hashlib
    raw = read_bytes(Path(roots.identity_json))
    lf = raw.replace(b"\r\n", b"\n")
    if roots.identity_frozen and hashlib.sha256(lf).hexdigest() != ID.IDENTITY_PREFREEZE_SHA256:
        raise AssertionError("IDENTITY_prefreeze.json differs from its freeze-manifest entry")
    doc = json.loads(lf.decode("utf-8"))
    out = {}
    for key, obj in IDENTITY_OBJECT.items():
        recs = [r for r in doc.get("records", []) if r.get("object") == obj]
        if len(recs) != 1:
            raise AssertionError(f"identity references: {len(recs)} records for object key {key}")
        refs, local, urls, head = [], [], [], {}
        for p in recs[0].get("probes", []):
            r = ID.ref_from_probe(p)
            if r is not None:
                refs.append(r)
            ok = p.get("status") == "ok"
            method = str(p.get("method", ""))
            if method.startswith("local") and ok:
                local.append(str(p["path"]))
                # R44: the copy's git blob equals the probe's (besides its sha256 and size)
                if isinstance(p.get("git_blob_sha"), str) and isinstance(p.get("size"), int):
                    refs.append({"basis": ID.BASIS_GIT, "bytes": p["size"], "git_blob": p["git_blob_sha"]})
            if method.startswith("NeuroVault") and ok:
                # R44: the size equals NeuroVault's metadata size too (the HEAD size is ref_from_probe's)
                if isinstance(p.get("api_file_size"), int):
                    refs.append({"basis": ID.BASIS_SIZE, "bytes": p["api_file_size"]})
                head = {"file_url": p.get("file_url"), "content_length": p.get("content_length"),
                        "last_modified": p.get("last_modified")}
            for k in ("file_url", "url"):
                if isinstance(p.get(k), str) and p.get(k).startswith("https://"):
                    urls.append(p[k])
                    break
        if len(local) != 1 or not refs or not urls:
            raise AssertionError(f"identity references: object key {key} lacks a local copy, a reference or a URL")
        out[key] = {"refs": refs, "local_path": local[0], "url": urls[0], "target_no": recs[0].get("target_no"),
                    **head}
    return out
