"""WP4 G2 material stage (RUN_PLAN.md v3.1 §11, §18 WP4 "G2 downloads (FreeSurfer first), identity, extraction, gated
sets, manifests", §8 steps 0-6, R13-R18, R38; the DRAFT readings of RUN_PLAN_amend_4.md R51-R64). Phase 1 builds and
tests this on synthetic stand-ins only (tests/test_wp4_phase1.py); phase 2 runs it once, from a pinned worktree, on the
real G2 material, after the orchestrator freezes amendment 4 (wp4_layout.production_allowed).

    python -X utf8 -u -m a1_audit.wp4_material run --commit <sha>         # phase 2: launch (G2), then the stage
    python -X utf8 -m a1_audit.wp4_material plan                          # what phase 2 opens / writes (no carrier)
    python -X utf8 -m a1_audit.wp4_material r13-check                     # R13's WGCNA bicor record (no G2 material)

Order (each object through fetch_extract.run_target: gate (G2: step3v_open) -> pinned copy / fetch -> identity -> read
in §8's masked stages -> save with sha256 and read-back -> quarantine + deletion REQUEST if identifier-bearing -> R18
record; nothing is ever deleted):
  0 the gate (step3v_open(), RUN_PLAN §2.1) and the draft guard (production only).
  1 preflight - before any carrier or request: the reference pins (DK info and volume, HGNC, GAMBA, BrainSpan x3), the
    a1_builds chain (primary-dk counts, perdonor-dk, r12-han-c1-ourpc1), the identity references (IDENTITY_prefreeze
    .json's sha256) and gia_mdd_paths.json (through the freeze manifest), pdfplumber 0.11.10 (L14, extended as
    RUN_PLAN_amend_3 R47 (b) did), and R13's bicor record (RUN_PLAN.md:722 "before this audit reads any G2 map").
  2 R16: the FreeSurfer 7.4.1 fsaverage lh.aparc.annot (stream to the member; R51's header reading; the fallback order).
  3 R15: figshare 3501911's file list (the API), the HCP-MMP1 volume and its label list (size + served MD5, R52).
  4 R38: the per-donor HCP-MMP1 build (env/venv_ref subprocess; ahba_extras.build_perdonor_hcpmmp1).
  5 the local copies, identity at use then extraction: Patel's eTable 4 (R53), Giacomel @c022a29 (the comparison copy,
    R54), Hansen's three files and the Cammoun order (R60), Liu T3's two tables (R59), Pretzsch's eTable13 (R61, after
    R15's names), Leyhausen's volumes (identity only) and lh GIFTIs (R16's annot; R62).
  6 the downloads: Giacomel @93de089 (governs), the e045bc5 tree listing, the repository lists (R55), the eda33ab GEDAR
    maps (R56), the R17 inputs (R58).
  7 the Sadeghi DEG workbook (R57: listed in memory under its folder; else the Europe PMC archive's member).
  8 the gated sets (wp4_sets: the frozen S-build's build_set), the population restated.
  9 R17: the paper's script in the R17 image (rbuild/r17.py), its rebuilt DEG GEDAR maps; the DEG sets.
 10 Leyhausen's NeuroVault decoder outputs (R45's form, R63's p < .01 list; wp3_decoder's decide-once machinery).
 11 the G2 manifest (wp4_layout.MANIFEST_NAME; never overwritten).
Every line goes through privacy_wrap.Emitter (the one print rule). No carrier-derived string is printed or written.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import hashlib
import inspect
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from . import fetch_extract as FE
from . import gates
from . import identity as ID
from . import privacy_wrap as PW
from . import reparcel as RP
from . import wp4_layout as L
from . import wp4_read as RD

REL = "arcs/audit/src/a1_audit/wp4_material.py"
STATUS_PIN_MATCH = "pin match"
STATUS_PIN_CHANGED = "pin changed"
STATUS_PREFIX_CHANGED = "not auditable (map changed)"
R13_RECORD_REL = "arcs/audit/run_manifests/material/G2/r13_bicor_check.json"
R13_SCHEMA = "a1_r13_bicor_check_v1"
WP4_PHRASES = (
    "wp4_material wp4_sets wp4_read wp4_layout r17 R13 R15 R16 R17 R38 R51 R52 R53 R54 R55 R56 R57 R58 R59 R60 R61 "
    "R62 R63 bicor WGCNA check record passed present absent preflight pins pin reference references builds build "
    "manifest final partial version figshare HCP-MMP1 volume labels label list left names matched names one-to-one "
    "annot tarball probe Content-Length Last-Modified differs from the 2026-10-01 fallback official artefact "
    "eTable 4 eTable13 Patel Giacomel Hansen Liu T3 Pretzsch Leyhausen Sadeghi DEG workbook folder listed in memory "
    "declared sets set gated restated population cells cell testable lt5 decoder decoders image images GEDAR tree "
    "listing commit lists repository script inputs outputs docker Docker image R run exit status stage step steps "
    "phase G2 gate draft frozen guard production scratch comparison differing compared governs sheet sheets "
    "Thickness Subcortical cortical subcortical ids values DK prefix registered full sha256 pinned copy identity "
    "at use not auditable map changed computable volume-only lh GIFTI surface vertices dk-ctx V-DK "
    "thickness subcortical asd mdd pc1 predictors cammoun order ct sa etable4 left_names left_ids stand-ins "
    "re-hashed against their match differs artefacts wp4_material_manifest partial a1_wp4_material_manifest_v1 "
    "reused and equal same downloads "
    "member_path member_sha256 member_bytes artefacts_tried artefact_index governing_artefact_index vs_probe "
    "repo_path_sha256 registered_prefix prefix_match n_names primary-dk perdonor-dk r12-han-c1-ourpc1 matrix_d1 "
    "matrix_d2 matrix_d3 matrix_d4 matrix_d5 matrix_d6 ds_dk_ctx_perdonor pc1_dk_ctx pc1_loadings r13 door_admitted "
    "prefix_source prefix_len listing why record_sha256 object_sha256 object_path record_path identity_result "
    "identifier_bearing failed_stage refused_reason schema objects steps run scratch counts date_utc pins "
    "references builds manifest_sha256 result absent fail meta volume labels files n_files name_sha256 size md5 "
    "not_computable perdonor_hcpmmp1 exit built in_m gated n_sets restatement n_cells n_not_testable_lt5 "
    "n_in_m_not_testable_lt5 params image build script R58 note giacomel_comparison n_cells_compared "
    "n_cells_differing 93de089 c022a29 differing n_outputs deg n_pool rows_kept",
    # asdg-skeptic B3 / B5 (v2): the R17 run's record, the DEG checks, the outputs, the R15 identities
    "deg_checks passed m_script m_definition cross_check n_common n_script_only n_python_only equal role only "
    "governs yaml dockerfile_sha256 image_id tag base_digest base_override session_info_sha256 session_info_lines "
    "session_info_exit workdir_index cwd directory root created declared_outputs_found declared_outputs stdout_lines "
    "stderr_lines stdout_sha256 stderr_sha256 inputs_sha256 network none ok facts commit_date n_read_paths "
    "n_read_paths_unresolved n_tree_inputs params_sha256 r_version bioc_version codename preinstalled packages "
    "n_packages r17_in raw n_rows ran deviation adaptation_sha256 adaptation_keys n_lists_located name_regex "
    "symbol_header weight_header delimiter object_key resumed n_rows_excluded_by_type symbol_datetime symbol_date "
    "symbol_time symbol_int symbol_float symbol_NoneType symbol_bool p_str p_NoneType p_datetime logFC_str "
    "logFC_NoneType logFC_datetime reused earlier re-checked match re-hashed equal same incident field fields "
    "failing paths manifest_name MANIFEST_G2",
    # 2026-10-21 (run 3 at 9ec681e stopped at the manifest write: .run.launch_passed unregistered); the keys of the
    # run block and of the conditional entries, checked by test X6's pre-flight
    "launch_passed reason_class n other n_labels",
    # amend_5 (draft, 2026-10-21): R58' placement facts, the Sadeghi duplicate-name rule, E1, L130, R61' counts
    "n_abs_roots n_out_dirs n_read_vars sadeghi_dup_name applied sha256_match screen_exemption basis why labels "
    "line130 label cells n_names_dot_dash n_left_name_keys",
    # amend_5 v2: the post-exposure version's block, the line-130 bite record, the make.names pair counts
    "post_exposure readings r17_mdd_equals_asd eda33ab_mdd_equals_asd n_pairs_make_names n_pairs_not_make_names",
    # 2026-10-21 (run 5): the layout-blame check and the versioned object names
    "layout_condition layout_check versioned n_unmatched n_matched",
)
# every fixed text a manifest entry may carry that no imported vocabulary holds (X6 asserts each passes the
# identity-channel allow-list, and that the material code emits no other literal)
MANIFEST_TEXTS = ("not computable (gene PC1 not extracted)", "path not in gia_mdd_paths.json",
                  "not exactly one tree entry", "R57: the Europe PMC archive route runs in phase 2 only",
                  "stopped for the operator",
                  # amend_5 E1 / L130
                  "the pinned copy's name is not the declared one", "the pinned copy's bytes are not the declared ones",
                  "the runner-built link holds other bytes", "the runner-built link could not be made",
                  "declared publisher file name and sha256 (wp4_layout.SCREEN_EXEMPT)", L.LINE130_LABEL,
                  L.AMEND5_VERSION_LABEL, *L.AMEND5_PE_READINGS,
                  "not reached (another failure at the read stage)",
                  "an earlier object of other bytes kept (never overwritten)")
RUN_INFO_KEYS = ("commit", "launch_passed")
REASON_CLASSES = ("StageStop",)          # an exception class name a manifest entry may record; else "other"


def run_info_of(commit: str, launch_rec: dict) -> dict:
    """The manifest's run block (main and test X6 build it here): a commit sha and a boolean, nothing else."""
    return {"commit": str(commit), "launch_passed": not launch_rec.get("failed")}


def check_run_info(run_info: dict) -> dict:
    if set(run_info) - set(RUN_INFO_KEYS):
        raise ValueError("run_info: a key outside RUN_INFO_KEYS")
    if "commit" in run_info and not re.fullmatch(r"[0-9a-f]{7,40}|HEAD", str(run_info["commit"])):
        raise ValueError("run_info: commit is not a sha")
    if "launch_passed" in run_info and not isinstance(run_info["launch_passed"], bool):
        raise ValueError("run_info: launch_passed is not a boolean")
    return dict(run_info)


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


class PreflightRefused(Exception):
    """A check that touches no carrier failed: the stage stops before any carrier or request."""


class Door:
    def __init__(self, roots: L.Roots):
        self.roots = roots
        self.admitted: list[str] = []

    def path(self, p) -> Path:
        q = FE.refuse_quarantine_opener(p, Path(self.roots.quarantine))
        self.admitted.append(str(q))
        return q

    def read_bytes(self, p) -> bytes:
        return self.path(p).read_bytes()

    def pinned(self, key: str) -> bytes:
        path, sha = self.roots.pin(key)
        data = self.read_bytes(path)
        if sha is not None and hashlib.sha256(data).hexdigest() != sha:
            raise AssertionError(f"reference {key} differs from its pin")
        return data


def _allow(roots: L.Roots, *exact) -> PW.AllowList:
    from . import wp3_material as W3M
    allow = PW.AllowList(phrases=FE.FE_PHRASES + W3M.WP3_PHRASES + WP4_PHRASES)
    keys = [L.PATEL_KEY, L.GIA_GOV_KEY, L.GIA_CMP_KEY, L.HANSEN_CT_KEY, L.HANSEN_PC1_KEY, L.HANSEN_PRED_KEY,
            L.HANSEN_INFO_KEY, L.LIU_CT_KEY, L.LIU_SV_KEY, L.PRE_KEY, L.FS_KEY, L.HCP_VOL_KEY, L.HCP_LIST_KEY,
            L.HCP_META_KEY, L.SADEGHI_KEY, L.R17_SCRIPT_KEY, L.R17_AHBA_KEY, L.R17_HPA_KEY, "gia_tree_e045bc5",
            *L.LEY_LH_KEY.values(), *L.LEY_VOL_KEY.values(), *L.LEY_DECODER_KEY.values(),
            *[f"gia_list_{k}" for k in L.GIA_ASD_LISTS], *[f"gia_list_{k}" for k in _mdd_list_keys()],
            *[f"gia_gedar_{k}" for k in _gedar_keys()], L.R17_COMMIT_KEY, L.R17_RVERSIONS_KEY, L.R17_BIOC_KEY,
            *[v[0] for v in L.R17_DECL_KEYS.values()],
            *[f"r17_{w}_{d}_{t}" for w in ("map", "deg") for d in ("ASD", "MDD") for t in (1, 5, 10)]]
    keys += [k + L.AMEND5_OBJECT_SUFFIX for k in L.AMEND5_OBJECT_KEYS]       # amend_5's amended objects
    allow.add_words(*keys, *[f"{k}_extract" for k in keys], *[k for k, _ in roots.pins], "lh_aparc_annot", "rows",
                    "genes", "raw", "map", "readback", "pass", "fail", "found", "not", "py")
    from . import wp4_sets as WS
    allow.add_phrases(L.STATUS_R17, L.STATUS_DEG, L.STATUS_DEG_POOL, L.STATUS_DEG_CHECK, L.STATUS_DEG_NOT_FOUND,
                      "a public R17 document was not obtained", "the commit record is not e045bc5's",
                      "the commit record has no committer date", "a declaration file failed its identity",
                      "an input failed its identity", "a read input failed its identity", "not exactly one script entry",
                      "the commit's tree listing was not obtained", "the script was not obtained",
                      "more than one created file for the key", "not run (scratch: no R17 builder given)",
                      "cross-check only (the script's S governs)", "repository root", "script directory",
                      L.DEG_DEVIATION_LABEL, *R17_REFUSAL_PHRASES(), *MANIFEST_TEXTS)
    allow.add_words(*REASON_CLASSES)
    allow.add_words(*LAYOUT_COUNT_KEYS())
    allow.add_phrases(*STATUS_TEXTS())
    allow.add_words(*WS.GATED_CELLS)
    allow.add_exact(*exact)
    return allow


def STATUS_TEXTS() -> tuple:
    """Every STATUS_* text of the layout and of this module (2026-10-21: a status a target's refusal_status or a
    conditional entry carries is a code text; X6 checks each)."""
    import sys as _sys
    mods = (L, _sys.modules[__name__])
    return tuple(sorted({getattr(m, n) for m in mods for n in dir(m) if n.startswith("STATUS_")
                         and isinstance(getattr(m, n), str)}))


def LAYOUT_COUNT_KEYS() -> frozenset:
    """The count names a declared check of wp4_read can carry (its "n_..." literals): the only counts a
    layout_condition records (each a registered word)."""
    src = Path(RD.__file__).read_text(encoding="utf-8")
    return frozenset(re.findall(r'"(n_[a-z0-9_]+)"', src)) | frozenset(re.findall(r"(n_[a-z0-9_]+)=0", src))


def R17_REFUSAL_PHRASES() -> tuple:
    from .rbuild import r17 as R17
    return tuple(t.replace("\\", " ") for t in R17.REFUSALS) + (R17.REFUSAL_UNLISTED,)


def _mdd_list_keys() -> list:
    return ["MDD_top_pos_genes_thr_1", "MDD_top_neg_genes_thr_10", "MDD_top_genes_thr_1", "MDD_top_genes_thr_5",
            "MDD_top_genes_thr_10"]


def _gedar_keys() -> list:
    return [f"{d}_TPRS_thr_{t}" for d in ("ASD", "MDD") for t in (1, 5, 10)]


# ================================================================================================================
# preflight (R50's ordering applied to G2; R13; L14)
# ================================================================================================================
def file_identity(door: Door, key: str) -> dict:
    path, sha = door.roots.pin(key)
    nbytes = door.roots.pin_bytes(key)
    facts = ID.file_facts(door.path(path), quarantine_root=Path(door.roots.quarantine))
    ok = sha is not None and facts["sha256"] == sha and (nbytes is None or facts["bytes"] == nbytes)
    return {"pin": key, "path": Path(path).as_posix(), "bytes": facts["bytes"], "sha256": facts["sha256"],
            "pinned_sha256": sha, "pinned_bytes": nbytes, "result": STATUS_PIN_MATCH if ok else STATUS_PIN_CHANGED}


G2_BUILDS = {"primary-dk": ("counts",), "perdonor-dk": ("matrix", "counts"), "r12-han-c1-ourpc1": ()}


def builds_pins(door: Door) -> dict:
    """The a1_builds outputs G2 reads, re-hashed against their build records (WP2), and the MANIFEST's sha256."""
    from . import real_sources as RS
    b = Path(door.roots.builds)
    man_bytes = door.read_bytes(b / "MANIFEST.json")
    man = json.loads(man_bytes.decode("utf-8"))
    out = {"manifest_sha256": hashlib.sha256(man_bytes).hexdigest(), "builds": {}}
    for name, roles in G2_BUILDS.items():
        rb = door.read_bytes(b / name / "build_record.json")
        if hashlib.sha256(rb).hexdigest() != man["builds"][name]["record_sha256"]:
            raise AssertionError("a build record differs from the a1_builds MANIFEST")
        rec = json.loads(rb.decode("utf-8"))
        files = {}
        for o in rec["outputs"]:
            if roles and o.get("role") not in roles:
                continue
            h = ID.file_facts(door.path(b / name / o["file"]), quarantine_root=Path(door.roots.quarantine))["sha256"]
            if h != o["sha256"]:
                raise AssertionError("a build output differs from its build record")
            files[RS.build_file_key(o) if o.get("role") in ("matrix", "counts") else o["file"]] = h
        out["builds"][name] = {"record_sha256": hashlib.sha256(rb).hexdigest(), "files": files}
    return out


def repro_sha256() -> str:
    from . import repro as RE
    return hashlib.sha256(Path(RE.__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def r13_status(roots: L.Roots, door: Door) -> dict:
    """R13 (RUN_PLAN.md:722-726): the WGCNA bicor check record exists, passed, and was made with this repro.py (the
    LF sha256 equal); else the stage refuses before any G2 map is read."""
    p = Path(roots.control) / L.GATE / "r13_bicor_check.json"     # production: R13_RECORD_REL
    if not p.is_file():
        return {"result": "absent"}
    doc = json.loads(door.read_bytes(p).decode("utf-8"))
    ok = (doc.get("schema") == R13_SCHEMA and doc.get("exit") == 0 and doc.get("wgcna_check") == "PASS"
          and doc.get("repro_py_lf_sha256") == repro_sha256())
    return {"result": "pass" if ok else "fail", "record_sha256": hashlib.sha256(p.read_bytes()).hexdigest()}


def freeze_manifest_sha(door: Door, rel: str) -> str:
    """The sha256 the frozen register_freeze_manifest.json gives a file (its own sha256 = L3's pin)."""
    from . import launch as LA
    from . import loader as LD
    fm = LD.lf(door.read_bytes(Path(door.roots.repo) / LA.MANIFEST_PATH))
    if hashlib.sha256(fm).hexdigest() != LA.MANIFEST_SHA256:
        raise AssertionError("the freeze manifest differs from its L3 pin")
    hits = [e for e in json.loads(fm.decode("utf-8"))["files"] if e["path"] == rel]
    if len(hits) != 1:
        raise AssertionError("a file is not in the freeze manifest")
    return hits[0]["sha256"]


def preflight(roots: L.Roots, door: Door, em: PW.Emitter, allow) -> dict:
    failed = []
    out = {}
    try:
        out["idrefs"] = PW.stage(em, "identity", L.identity_records, roots, door.read_bytes)
    except PW.StageFailed:
        raise PreflightRefused() from None
    try:
        if not roots.scratch:
            want = freeze_manifest_sha(door, L.GIA_MDD_PATHS_REL)
            got = hashlib.sha256(LDlf(door.read_bytes(Path(roots.repo) / L.GIA_MDD_PATHS_REL))).hexdigest()
            if got != want:
                raise AssertionError("gia_mdd_paths.json differs from its freeze-manifest entry")
        out["mdd_paths"] = PW.stage(em, "identity", L.gia_mdd_paths, roots, door.read_bytes)
    except (PW.StageFailed, AssertionError):
        raise PreflightRefused() from None
    refs = {}
    for k, _ in roots.pins:
        try:
            r = PW.stage(em, "identity", file_identity, door, k)
        except PW.StageFailed:
            failed.append(k)
            continue
        allow.add_exact(r["path"])
        refs[k] = {"sha256": r["sha256"], "bytes": r["bytes"], "result": r["result"]}
        em.say(f"wp4_material: reference {k} sha256 {r['sha256']}: {r['result']}")
        if r["result"] != STATUS_PIN_MATCH:
            failed.append(k)
    out["references"] = refs
    try:
        out["builds"] = PW.stage(em, "identity", builds_pins, door)
        em.say(f"wp4_material: a1_builds manifest sha256 {out['builds']['manifest_sha256']}; builds "
               f"{len(out['builds']['builds'])} re-hashed against their records: pass")
    except PW.StageFailed:
        failed.append("builds")
    from . import wp3_pdf as WP
    if not WP.version_ok():
        failed.append("pdfplumber")
        em.say("wp4_material: pdfplumber is not 0.11.10 (L14)")
    r13 = r13_status(roots, door)
    out["r13"] = r13
    em.say(f"wp4_material: R13 bicor check record {r13['result']}")
    if r13["result"] != "pass":
        failed.append("r13")
    if failed:
        em.say(f"wp4_material: {L.STATUS_PREFLIGHT}; failed checks {len(failed)}: {', '.join(failed)}")
        raise PreflightRefused()
    return out


def LDlf(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


# ================================================================================================================
# readers (run inside fetch_extract's masked stages; nothing prints)
# ================================================================================================================
def dk_of(door: Door):
    return RD.dk_frame(door.pinned("dk_info"))


def json_reader(door: Door, sub: str):
    def read(path: Path) -> dict:
        data = door.read_bytes(path)
        json.loads(data.decode("utf-8"))
        return {sub: {"sha256": RD.sha256_bytes(data), "bytes": len(data)}}
    return read


def patel_reader(door: Door):
    """R53 with §8's PDF read-back: a second parse equal to the first (counts and hashes only)."""
    def read(path: Path) -> dict:
        dk = dk_of(door)
        a = RD.patel_parse(door.path(path), dk)
        b = RD.patel_parse(door.path(path), dk)
        if a["values"] != b["values"] or a["ids"] != b["ids"]:
            raise RD.W4Refused(L.STATUS_PATEL_LAYOUT, {"readback": 0})
        a["readback"] = "pass"
        return {"etable4": a}
    return read


def giacomel_target(key: str, url: str, refs: tuple, *, local_path: str | None, dk_names: tuple) -> FE.Target:
    cols = (FE.Column("ASD", "asd", True), FE.Column("MDD", "mdd", True))
    sheets = tuple(FE.SheetDecl(key=k, name=n, mode="labelled", columns=cols, vocab=dk_names)
                   for k, n in L.GIA_SHEETS.items())
    return FE.Target(key=key, gate=L.GATE, url=url, kind="workbook", ext=".xlsx", refs=tuple(refs),
                     identity_at_download=False, sheets=sheets, local_path=local_path,
                     refusal_status=L.STATUS_GIA_LAYOUT)


def giacomel_transform(door: Door, amend5: bool = False):
    """R54: each declared sheet's label column normalised in memory; saved: the DK-keyed values, or the sheet's
    fail-closed status with its counts (SD7's precedent, wp3_material.sd7_label_transform) - never a label string."""
    def tf(objects: dict) -> dict:
        dk = dk_of(door)
        out = {}
        for sheet in L.GIA_SHEETS:
            view = objects[sheet]
            labels = view.column(0)
            asd = view.column(view.declared["asd"])
            mdd = view.column(view.declared["mdd"])
            try:
                out[sheet] = RD.giacomel_sheet_object(labels, asd, mdd, dk, sheet, amend5=amend5)
            except RD.W4Refused as e:
                out[sheet] = {"status": e.status, "counts": {k: v for k, v in e.counts.items()
                                                             if isinstance(v, (int, float))}}
        return out
    return tf


def enigma_reader(door: Door, kind: str):
    def read(path: Path) -> dict:
        r = RD.enigma_toolbox(door.read_bytes(path), dk_of(door), kind)
        return {kind: {"by_id": {str(k): v for k, v in sorted(r["by_id"].items())}, "counts": r["counts"]}}
    return read


def hansen_reader(door: Door, what: str, pc1_object: dict | None = None):
    def read(path: Path) -> dict:
        data = door.read_bytes(path)
        if what == "ct":
            return {"asd": {"values": [float(x) for x in RD.hansen_ct(data)], "rows": "Cammoun scale033 order 1-68"}}
        if what == "pc1":
            return {"pc1": {"values": [float(x) for x in RD.hansen_pc1(data)], "rows": "Cammoun scale033 order 1-68"}}
        if what == "predictors":
            import numpy as np
            r = RD.hansen_predictors(data, np.asarray(pc1_object["values"], dtype=float))
            return {"predictors": {"matrix": r["matrix"].tolist(), "pc1_column": r["pc1_column"],
                                   "header_row": bool(r["has_header"])}}
        r = RD.cammoun_order(data, dk_of(door))
        return {"cammoun": {"left_row_ids": r["left_row_ids"], "counts": r["counts"]}}
    return read


def pretzsch_reader(door: Door, left_names: list, amend5: bool = False):
    def read(path: Path) -> dict:
        r = RD.pretzsch_csv(door.read_bytes(path), left_names, amend5=amend5)
        return {"etable13": {"CT": r["CT"], "SA": r["SA"], "counts": r["counts"],
                             "order": "the pinned HCP-MMP1 label list's left names (R15)"}}
    return read


def leyhausen_reader(door: Door, annot_path: Path):
    def read(path: Path) -> dict:
        dk = dk_of(door)
        lab, names = RP.read_annot(door.path(annot_path), Path(door.roots.quarantine))
        vals = RP.read_gifti_values(door.path(path), Path(door.roots.quarantine))
        cortex = dk[(dk["hemisphere"] == "L") & (dk["structure"] == "cortex")]
        dk_names = [str(n) for n in cortex["label"]]
        kept, v, rep = RP.surface_to_dk(vals, lab, names, dk_names)
        id_of = {str(r["label"]): int(r["id"]) for _, r in cortex.iterrows()}
        return {"dkctx": {"ids": [id_of[n] for n in kept], "values": [float(x) for x in v], "report": rep,
                          "label": RP.LABEL_REPARCELLATED}}
    return read


def raw_list_reader(door: Door):
    """R55: a repository list's rows as raw gene-level entries (Ensembl id first when present, the symbol, the weight)
    - the S-build's raw form (wp4_sets applies the frozen build_set); counts of the declared columns."""
    def read(path: Path) -> dict:
        data = door.read_bytes(path)
        rows = [r for r in RD._table(data, "\t") if any(c.strip() for c in r)]
        if not rows:
            raise RD.W4Refused(L.STATUS_LIST_LAYOUT, {"n_rows": 0})
        header = [h.strip() for h in rows[0]]
        if header.count(L.LIST_SYMBOL_HEADER) != 1:
            raise RD.W4Refused(L.STATUS_LIST_LAYOUT, {"n_symbol_headers": header.count(L.LIST_SYMBOL_HEADER)})
        ps = header.index(L.LIST_SYMBOL_HEADER)
        pe = header.index(L.LIST_ENSEMBL_HEADER) if header.count(L.LIST_ENSEMBL_HEADER) == 1 else None
        wcol = next((w for w in L.LIST_WEIGHT_HEADERS if header.count(w) == 1), None)
        pw = header.index(wcol) if wcol else None
        raw = []
        for r in rows[1:]:
            ens = r[pe].strip() if (pe is not None and pe < len(r) and r[pe].strip()) else None
            sym = r[ps].strip() if ps < len(r) else None
            w = RD._float(r[pw], L.STATUS_LIST_LAYOUT) if (pw is not None and pw < len(r)) else None
            if pw is not None and w is None:
                raise RD.W4Refused(L.STATUS_LIST_LAYOUT, {"weight_missing": 1})
            raw.append({"kind": "ensembl" if ens else None, "id": ens, "symbol": sym or None, "weight": w})
        return {"raw": {"rows": raw, "n_rows": len(raw), "weight_column": "found" if pw is not None else "none",
                        "weight_rule": L.LIST_WEIGHT_RULE}}
    return read


def gedar_reader(door: Door):   # its W4Refused (R56's declared check) is recorded by run_one's sink
    def read(path: Path) -> dict:
        r = RD.gedar_map(door.read_bytes(path), dk_of(door))
        return {"map": {"by_id": {str(k): v for k, v in sorted(r["by_id"].items())}, "label_form": r["label_form"],
                        "n_rows": r["n_rows"]}}
    return read


def script_reader(door: Door):
    def read(path: Path) -> dict:
        data = door.read_bytes(path)
        req = RD.r_script_requirements(data.decode("utf-8", "replace"))
        return {"script": {"sha256": RD.sha256_bytes(data), "bytes": len(data), "packages": req["packages"],
                           "n_read_calls": len(req["read_paths"]), "n_lines": req["n_lines"]}}
    return read


# ================================================================================================================
# targets
# ================================================================================================================
def gh_ref(blob: str, size: int) -> dict:
    return {"basis": ID.BASIS_GIT, "bytes": int(size), "git_blob": blob}


def screen_exempt_target(roots: L.Roots, t: FE.Target, door: Door) -> tuple[FE.Target, dict | None]:
    """amend_5 E1: the path screen's declared exemption (wp4_layout.SCREEN_EXEMPT: a pinned group-level copy's
    publisher file name with the copy's sha256). When the pinned copy has exactly that name and those bytes, the
    wrapper is handed a runner-built hard link to it (<data>/<key>/carrier<ext>: same bytes, no copy), so the publisher
    name is not screened; every other path component, the link's own path and the content are screened as before.
    Otherwise the target is unchanged (the name is screened as before). Returns (target, record | None)."""
    ex = L.SCREEN_EXEMPT.get(t.key)
    if ex is None or t.local_path is None:
        return t, None
    name, sha = ex
    lp = Path(t.local_path)
    if lp.name != name:
        return t, {"applied": False, "why": "the pinned copy's name is not the declared one"}
    try:
        have = PW.sha256_file(door.path(lp)) if lp.is_file() else None
    except Exception:                                  # a quarantined opener: the wrapper refuses it on its own
        have = None
    if have != sha:
        return t, {"applied": False, "why": "the pinned copy's bytes are not the declared ones"}
    link = Path(roots.data) / t.key / f"carrier{t.ext}"
    if link.exists():
        if PW.sha256_file(link) != sha:
            return t, {"applied": False, "why": "the runner-built link holds other bytes"}
    else:
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(lp, link)
        except OSError:
            return t, {"applied": False, "why": "the runner-built link could not be made"}
        if PW.sha256_file(link) != sha:
            raise OSError("read-back")
    return (dataclasses.replace(t, local_path=str(link)),
            {"applied": True, "basis": "declared publisher file name and sha256 (wp4_layout.SCREEN_EXEMPT)",
             "sha256": sha})


def local_targets(roots: L.Roots, idrefs: dict) -> dict:
    """The pinned local copies (FE15; no GET), with their identity references (R44's precedent applied to G2)."""
    out = {}
    exts = {L.PATEL_KEY: (".pdf", L.STATUS_PATEL_LAYOUT), L.HANSEN_CT_KEY: (".csv", L.STATUS_HANSEN_LAYOUT),
            L.HANSEN_PC1_KEY: (".csv", L.STATUS_HANSEN_LAYOUT), L.LIU_CT_KEY: (".csv", L.STATUS_ENIGMA_LAYOUT),
            L.LIU_SV_KEY: (".csv", L.STATUS_ENIGMA_LAYOUT), L.PRE_KEY: (".csv", L.STATUS_PRE_LAYOUT)}
    for k, (ext, st) in exts.items():
        r = idrefs[k]
        out[k] = FE.Target(key=k, gate=L.GATE, url=r["url"] or "https://none.invalid/no-url-registered", kind="file",
                           ext=ext, refs=tuple(r["refs"]), local_path=r["local_path"], refusal_status=st,
                           url_note=None if r["url"] else "no URL registered")
    for image in L.LEY_IMAGES:
        for k, ext in ((L.LEY_LH_KEY[image], ".gii"), (L.LEY_VOL_KEY[image], ".nii.gz")):
            r = idrefs[k]
            out[k] = FE.Target(key=k, gate=L.GATE, url=r["url"], kind="file", ext=ext, refs=tuple(r["refs"]),
                               local_path=r["local_path"], refusal_status=RP.STATUS_FS_NOT_MATCHING)
    return out


def prefix_target(roots: L.Roots, door: Door, key: str, ext: str, em: PW.Emitter) -> tuple[FE.Target | None, dict]:
    """R60 / R57 (draft): a registered sha256 PREFIX (64 bits) checked first; the copy's full sha256 then pins it for
    the wrapper's own identity step (BASIS_PINNED_SHA), so the bytes read are the bytes checked."""
    path, prefix, source = roots.prefix_pin(key)
    try:
        facts = PW.stage(em, "identity", ID.file_facts, door.path(path), Path(roots.quarantine))
    except PW.StageFailed:
        return None, {"status": FE.STATUS_FAILED, "failed_stage": "identity"}
    ok = facts["sha256"].startswith(prefix)
    em.say(f"wp4_material: {key} registered sha256 prefix: {'match' if ok else 'differs'}")
    if not ok:
        return None, {"status": STATUS_PREFIX_CHANGED, "identity_result": ID.STATUS_CHANGED,
                      "prefix_len": len(prefix), "prefix_source": "registered (wp4_layout prefix pins)"}
    st = {L.HANSEN_PRED_KEY: L.STATUS_HANSEN_LAYOUT, L.HANSEN_INFO_KEY: L.STATUS_CAMMOUN}.get(key)
    t = FE.Target(key=key, gate=L.GATE, url="https://none.invalid/registered-prefix-copy", kind="file", ext=ext,
                  pinned_sha256=facts["sha256"], pinned_bytes=facts["bytes"], local_path=str(path), refusal_status=st,
                  url_note="no URL registered: the incorporated draft's local copy, held to its registered prefix")
    return t, {"prefix_len": len(prefix), "prefix_source": "registered (wp4_layout prefix pins)"}


# ================================================================================================================
# manifest entries
# ================================================================================================================
def _rel(p: Path, root: str) -> str:
    return Path(p).resolve().relative_to(Path(root).resolve()).as_posix()


def entry(roots: L.Roots, res: dict) -> dict:
    rp = res.get("record_path")
    if not rp:
        return {"status": res.get("status")}
    rb = Path(rp).read_bytes()
    rec = json.loads(rb.decode("utf-8"))
    e = {"status": rec.get("status"), "record_path": _rel(Path(rp), roots.records),
         "record_sha256": hashlib.sha256(rb).hexdigest(),
         "identity_result": ((rec.get("identity") or {}).get("comparison") or {}).get("result"),
         "identifier_bearing": rec.get("identifier_bearing"),
         "quarantined": bool((rec.get("quarantine") or {}).get("quarantined")), "failed_stage": rec.get("failed_stage"),
         "refused_reason": rec.get("refused_reason"),
         "sha256": (((rec.get("identity") or {}).get("facts") or {}).get("sha256"))}
    ex = rec.get("extraction") or {}
    if ex.get("object_path"):
        op = Path(ex["object_path"])
        if not op.exists() or hashlib.sha256(op.read_bytes()).hexdigest() != ex["object_sha256"]:
            raise AssertionError("an object differs from its record on read-back")
        e.update(object_path=_rel(op, roots.artifacts), object_sha256=ex["object_sha256"])
    tar = rec.get("tar") or {}
    if tar.get("saved_path"):
        e.update(member_path=Path(tar["saved_path"]).as_posix(), member_sha256=tar["saved_sha256"],
                 member_bytes=tar.get("bytes"))
    return e


def object_of(roots: L.Roots, e: dict, sub: str):
    if e.get("status") != FE.STATUS_EXTRACTED or not e.get("object_path"):
        return None
    doc = json.loads((Path(roots.artifacts) / e["object_path"]).read_bytes().decode("utf-8"))
    return (doc.get("objects") or {}).get(sub)


def previous_record(roots: L.Roots, key: str) -> tuple[Path | None, dict | None]:
    """The latest record of `key` under records/G2 (<key>.json, <key>.<n>.json)."""
    d = Path(roots.records) / L.GATE
    best = None
    for p in d.glob(f"{key}*.json") if d.is_dir() else ():
        m = re.fullmatch(re.escape(key) + r"(?:\.(\d+))?\.json", p.name)
        if m:
            n = int(m.group(1) or 1)
            if best is None or n > best[0]:
                best = (n, p)
    if best is None:
        return None, None
    return best[1], json.loads(best[1].read_bytes().decode("utf-8"))


def run_amended(roots: L.Roots, t: FE.Target, out, **kw) -> dict:
    """amend_5 (R54'): a target whose extraction reading changed runs under <key>_a5 (wp4_layout.AMEND5_OBJECT_KEYS),
    so its object never meets an earlier run's object of other bytes; the carrier already on disk at <data>/<key>/ is
    used as found (identity by the target's own references), never fetched again. The entry stays under <key> and
    names the object by object_key."""
    if t.key not in L.AMEND5_OBJECT_KEYS:
        raise ValueError("run_amended: not an amend_5 post-exposure target")
    k5 = t.key + L.AMEND5_OBJECT_SUFFIX
    lp = t.local_path
    if lp is None:
        car = Path(roots.data) / t.key / f"carrier{t.ext}"
        if car.is_file():
            lp = str(car)
    e = run_one(roots, dataclasses.replace(t, key=k5, local_path=lp), out, **kw)
    if e.get("object_path"):
        e["object_key"] = k5
    return e


def run_one(roots: L.Roots, t: FE.Target, out, **kw) -> dict:
    """One target through the wrapper. Resume (2026-10-17): a carrier already on disk is never fetched again
    (fetch_extract's copy-on-disk rule); when the target has no identity reference of its own (identity recorded at
    download), the previous record's sha256 and size become its reference, so the identity is re-checked at use."""
    if t.local_path is None and t.kind != "tar_member" and not t.refs and not t.pinned_sha256:
        carrier = Path(roots.data) / t.key / f"carrier{t.ext}"
        if carrier.is_file():
            _p, prev = previous_record(roots, t.key)
            facts = ((prev or {}).get("identity") or {}).get("facts") or {}
            if isinstance(facts.get("sha256"), str):
                t = dataclasses.replace(t, refs=({"basis": ID.BASIS_SHA_DISK, "bytes": int(facts["bytes"]),
                                                  "sha256": facts["sha256"]},))
    sink: dict = {}
    kw2 = {k: (_checked(v, sink) if k in ("reader", "transform") and v is not None else v) for k, v in kw.items()}
    res = FE.run_target(t, roots.fe_roots(), out=out, adopt_identical=True, **kw2)
    e = entry(roots, res)
    if save_conflict(roots, e) and t.kind in ("file", "workbook"):
        e = run_versioned(roots, t, out, kw2, e)
    return blame_checked(t, e, sink, bool(kw.get("reader") or kw.get("transform")))


def _checked(fn, sink: dict):
    """The reader / transform wrapped: a DECLARED check's refusal (wp4_read.W4Refused, reparcel.ReparcelRefused, each
    with its status) is noted (status and numeric counts) before it propagates, so the stage knows the check ran."""
    from . import reparcel as _RP

    def w(*a, **k):
        try:
            return fn(*a, **k)
        except (RD.W4Refused, _RP.ReparcelRefused) as ex:
            st = getattr(ex, "status", None)
            counts = getattr(ex, "counts", None)
            sink["refused"] = {"status": st if isinstance(st, str) else None,
                               "counts": {kk: vv for kk, vv in (counts or {}).items()
                                          if kk in LAYOUT_COUNT_KEYS() and isinstance(vv, (int, float))
                                          and not isinstance(vv, bool)}
                               if isinstance(counts, dict) else {}}
            raise
    return w


def blame_checked(t: FE.Target, e: dict, sink: dict, has_code: bool) -> dict:
    """2026-10-21 (run 5): the wrapper gives a target's layout status to ANY failure of a read stage. Here a layout
    status stands only if the declared check ran and refused (sink): its condition is recorded (layout_condition:
    status, counts); a read-stage failure of another kind reads "refused (stage failed)" (layout_check: not reached)."""
    if sink.get("refused"):
        e["layout_condition"] = sink["refused"]
        st = sink["refused"].get("status")
        if isinstance(st, str) and e.get("status") == t.refusal_status and st != t.refusal_status:
            e["status"] = st
    elif has_code and t.refusal_status and e.get("status") == t.refusal_status and \
            str(e.get("failed_stage") or "").startswith("read"):
        e["status"] = FE.STATUS_FAILED
        e["layout_check"] = "not reached (another failure at the read stage)"
    return e


def save_conflict(roots: L.Roots, e: dict) -> bool:
    """The object step met an earlier run's object of other bytes (FileExistsError at save; never overwritten)."""
    if e.get("status") != FE.STATUS_FAILED or e.get("failed_stage") != "save" or not e.get("record_path"):
        return False
    rec = json.loads((Path(roots.records) / e["record_path"]).read_bytes().decode("utf-8"))
    return rec.get("failed_class") == "FileExistsError"


def run_versioned(roots: L.Roots, t: FE.Target, out, kw: dict, e0: dict) -> dict:
    """2026-10-21: an extraction whose object changed is saved under <key>_v<n> (n >= 2, the first free or
    byte-identical name; the scheme of the set files and _a5): the carrier the first attempt identity-checked is used
    as found (held to that attempt's sha256), never fetched again; the entry stays under <key> and names the object by
    object_key."""
    rec0 = json.loads((Path(roots.records) / e0["record_path"]).read_bytes().decode("utf-8"))
    facts = ((rec0.get("identity") or {}).get("facts") or {})
    lp = t.local_path or str(Path(roots.data) / t.key / f"carrier{t.ext}")
    if not isinstance(facts.get("sha256"), str) or not Path(lp).is_file():
        return e0
    for n in range(2, 51):
        tv = dataclasses.replace(t, key=f"{t.key}_v{n}", local_path=lp, pinned_sha256=facts["sha256"],
                                 pinned_bytes=int(facts["bytes"]))
        ev = entry(roots, FE.run_target(tv, roots.fe_roots(), out=out, adopt_identical=True, **kw))
        if save_conflict(roots, ev):
            continue
        if ev.get("object_path"):
            ev["object_key"] = tv.key
        ev["versioned"] = "an earlier object of other bytes kept (never overwritten)"
        return ev
    return e0


# ================================================================================================================
# R51 (draft): the FreeSurfer annot - headers recorded and labelled, never a refusal; the fallback order
# ================================================================================================================
def r16_annot(roots: L.Roots, out, em: PW.Emitter) -> dict:
    rp, prev = previous_record(roots, L.FS_KEY)
    tar = (prev or {}).get("tar") or {}
    if prev and prev.get("status") == FE.STATUS_EXTRACTED and tar.get("saved_path") and \
            Path(tar["saved_path"]).is_file() and PW.sha256_file(Path(tar["saved_path"])) == tar.get("saved_sha256"):
        e = entry(roots, {"record_path": str(rp)})
        url = str(prev.get("url", ""))
        ix = next((i for i, n in enumerate(L.FS_TARBALLS) if url.endswith(n)), None)
        e.update(resumed="the member saved by an earlier run, re-hashed equal to its record (no stream)",
                 governing_artefact_index=ix, artefacts_tried=[])
        em.say(f"wp4_material: R16 member reused from the earlier record; sha256 re-checked: match")
        return e
    tried = []
    for name in L.FS_TARBALLS:
        url = L.FS_DIR + name
        t = dataclasses.replace(FE.freesurfer_target(key=L.FS_KEY), url=url, pinned_bytes=None)
        e = run_one(roots, t, out)
        rec = json.loads((Path(roots.records) / e["record_path"]).read_bytes()) if e.get("record_path") else {}
        srv = rec.get("server") or {}
        lab = {"content_length": srv.get("content_length"), "last_modified": srv.get("last_modified")}
        if name == L.FS_TARBALLS[0]:
            lab["vs_probe"] = ("as the 2026-10-01 probe" if srv.get("content_length") == L.FS_PROBE["content_length"]
                               else "differs from the 2026-10-01 probe (recorded, R51)")
        tried.append({"artefact_index": L.FS_TARBALLS.index(name), "status": e.get("status"), "headers": lab})
        em.say(f"wp4_material: R16 artefact {L.FS_TARBALLS.index(name)} status {e.get('status')}")
        if e.get("status") == FE.STATUS_EXTRACTED and e.get("member_path"):
            e["artefacts_tried"] = tried
            e["governing_artefact_index"] = L.FS_TARBALLS.index(name)
            return e
        if e.get("refused_reason") == RP.STATUS_FS_NOT_REGULAR:     # R16: a non-regular member ends the step
            break
    checked = any(x.get("status") not in (FE.STATUS_FAILED, FE.STATUS_GATE, None) for x in tried)
    return {"status": RP.STATUS_FS_NOT_MATCHING if checked else L.STATUS_UPSTREAM, "artefacts_tried": tried}


# ================================================================================================================
# R52 (draft): figshare 3501911
# ================================================================================================================
def r15_hcp(roots: L.Roots, door: Door, out, em: PW.Emitter) -> dict:
    meta_t = FE.Target(key=L.HCP_META_KEY, gate=L.GATE, url=L.HCP_ARTICLE_API, kind="file", ext=".json",
                       identity_at_download=True, head_before_get=False)
    em_meta = run_one(roots, meta_t, out, reader=json_reader(door, "meta"))
    if em_meta.get("status") != FE.STATUS_EXTRACTED:
        return {"meta": em_meta, "status": L.STATUS_UPSTREAM}
    meta_path = Path(roots.data) / L.HCP_META_KEY / "carrier.json"

    def _files(b: bytes):
        try:
            return RD.figshare_files(b)
        except RD.W4Refused:                     # R52's declared check refused: the atlas files are not identified
            return None
    try:
        files = PW.stage(em, "read:file", _files, door.read_bytes(meta_path))
    except PW.StageFailed:
        return {"meta": em_meta, "status": L.STATUS_UPSTREAM}
    if files is None:
        return {"meta": em_meta, "status": RP.STATUS_GLASSER}
    vol_t = FE.Target(key=L.HCP_VOL_KEY, gate=L.GATE, url=files["volume"]["url"], kind="file", ext=".nii.gz",
                      refs=({"basis": ID.BASIS_MD5, "bytes": files["volume"]["size"], "md5": files["volume"]["md5"]},))
    lab_t = FE.Target(key=L.HCP_LIST_KEY, gate=L.GATE, url=files["labels"]["url"], kind="file", ext=".txt",
                      refs=({"basis": ID.BASIS_MD5, "bytes": files["labels"]["size"], "md5": files["labels"]["md5"]},))

    def labels_read(path: Path) -> dict:
        r = RD.hcp_left_names(door.read_bytes(path).decode("utf-8"))
        return {"labels": {"left_ids": r["left_ids"], "left_names": r["left_names"],
                           "n_labels": len(r["label_list"])}}
    ev = run_one(roots, vol_t, out)
    el = run_one(roots, lab_t, out, reader=labels_read)
    ok = ev.get("status") in (FE.STATUS_IDENTITY_ONLY, FE.STATUS_EXTRACTED) and el.get("status") == FE.STATUS_EXTRACTED
    checked = bool(el.get("layout_condition")) or ev.get("identity_result") == ID.STATUS_CHANGED or \
        el.get("identity_result") == ID.STATUS_CHANGED
    st = FE.STATUS_EXTRACTED if ok else (RP.STATUS_GLASSER if checked else L.STATUS_UPSTREAM)
    return {"meta": em_meta, "files": {k: {kk: vv for kk, vv in v.items() if kk != "url"} if isinstance(v, dict) else v
                                       for k, v in files.items()}, "volume": ev, "labels": el, "status": st}


# ================================================================================================================
# R38: the per-donor HCP-MMP1 build (env/venv_ref)
# ================================================================================================================
def r38_reuse(out_dir: Path, volume_sha256: str, label_list_sha256: str) -> dict | None:
    """Resume: the build record exists, is ok, names these R15 sha256s, and every output re-hashes to its record."""
    rp = Path(out_dir) / "build_record.json"
    if not rp.is_file():
        return None
    rb = rp.read_bytes()
    rec = json.loads(rb.decode("utf-8"))
    if rec.get("ok") is not True or rec.get("volume_sha256") != volume_sha256 or \
            rec.get("label_list_sha256") != label_list_sha256:
        return None
    for o in rec.get("outputs") or []:
        f = Path(out_dir) / o["file"]
        if not f.is_file() or PW.sha256_file(f) != o.get("sha256"):
            return None
    return {"status": "built", "exit": 0, "record_sha256": hashlib.sha256(rb).hexdigest(), "resumed": True}


def r38_build(roots: L.Roots, em: PW.Emitter, *, venv_python: Path | None = None, volume_sha256: str | None = None,
              label_list_sha256: str | None = None) -> dict:
    """R38 in env/venv_ref (a subprocess: abagen). The R15 download identities (the volume's and the label list's
    sha256 at download) are passed through and checked by the build before the volume is parsed (asdg-skeptic B3)."""
    if not (isinstance(volume_sha256, str) and isinstance(label_list_sha256, str)):
        return {"status": "not computable (atlas identity)", "exit": None, "record_sha256": None}
    vol = Path(roots.data) / L.HCP_VOL_KEY / "carrier.nii.gz"
    lab = Path(roots.data) / L.HCP_LIST_KEY / "carrier.txt"
    out_dir = Path(roots.hcp_build)
    reused = r38_reuse(out_dir, volume_sha256, label_list_sha256)
    if reused is not None:
        em.say("wp4_material: R38 build reused (record and outputs re-hashed equal; the same R15 downloads)")
        return reused
    py = venv_python or (L.main_repository(Path(roots.repo)) / "env/venv_ref/Scripts/python.exe")
    spec = Path(roots.logs) / L.GATE / "r38_roots_spec.json"
    spec.parent.mkdir(parents=True, exist_ok=True)
    sb = (json.dumps(roots.to_spec(), indent=1) + "\n").encode("utf-8")
    spec.write_bytes(sb)
    if spec.read_bytes() != sb:
        raise OSError("read-back")
    cmd = [str(py), "-X", "utf8", "-m", "a1_audit.wp4_material", "r38-build", "--volume", str(vol), "--labels",
           str(lab), "--out", str(out_dir), "--volume-sha256", volume_sha256, "--labels-sha256", label_list_sha256,
           "--roots-spec", str(spec)]
    r = subprocess.run(cmd, cwd=str(Path(roots.repo) / "arcs/audit/src"), capture_output=True, timeout=7200)
    rp = out_dir / "build_record.json"
    ok = r.returncode == 0 and rp.is_file()
    if ok:
        rec = json.loads(rp.read_bytes().decode("utf-8"))
        ok = rec.get("volume_sha256") == volume_sha256 and rec.get("label_list_sha256") == label_list_sha256
    em.say(f"wp4_material: R38 build exit {r.returncode}; record {'present' if rp.is_file() else 'absent'}")
    return {"status": "built" if ok else "not computable (atlas identity)", "exit": int(r.returncode),
            "record_sha256": hashlib.sha256(rp.read_bytes()).hexdigest() if rp.is_file() else None}


# ================================================================================================================
# R57 (draft): the Sadeghi workbook - listed in memory under its folder
# ================================================================================================================
def sadeghi_listing(roots: L.Roots, door: Door) -> dict:
    """§11 :1453-1455: the folder's names compared in memory with the declared relative path; found / not found and
    the name sha256s only."""
    base = Path(roots.sadeghi_folder)
    door.path(base)
    names = []
    found = False
    if base.is_dir():
        for p in sorted(base.rglob("*")):
            rel = p.relative_to(base).parts
            if len(rel) > 2:
                continue
            names.append(PW.sha256_text("/".join(rel)))
            if tuple(rel) == L.SADEGHI_DECLARED_REL and p.is_file():
                found = True
    return {"found": found, "name_sha256": names, "n_names": len(names)}


# ================================================================================================================
# the stage
# ================================================================================================================
def run_material(roots: L.Roots, *, out=None, steps=None, run_info: dict | None = None,
                 venv_python: Path | None = None, hooks: dict | None = None) -> dict:
    """Steps 0-11 (module docstring). steps: a subset (tests); production runs all. Returns the manifest document."""
    if not roots.scratch:
        ok, why = L.production_allowed()
        if not ok:
            raise PreflightRefused(why)
    allow = _allow(roots)
    log = Path(roots.logs) / L.GATE / "wp4_material.log"
    allow.add_exact(log, Path(roots.records) / L.GATE, Path(roots.artifacts) / L.GATE, Path(roots.data))
    em = PW.Emitter(allow, stream=out, log_path=log)
    door = Door(roots)
    want = set(steps) if steps else set(range(0, 12))
    man = {"schema": L.MANIFEST_SCHEMA, "gate": L.GATE, "final": False, "date_utc": utc_now(), "objects": {},
           "steps": sorted(want), "run": check_run_info(run_info or {}), "scratch": bool(roots.scratch)}
    objs = man["objects"]
    # amend_5 v2: the POST-EXPOSURE version (R61', R54', R58' (d)) beside the primary, never in place of it
    pe = man["post_exposure"] = {"label": L.AMEND5_VERSION_LABEL, "readings": list(L.AMEND5_PE_READINGS),
                                 "objects": {}}
    # 0 gate
    if not roots.scratch:
        okg, reason, _ = gates.step3v_check(Path(roots.repo))
        if not okg:
            em.say(f"wp4_material: gate G2 CLOSED (reason {reason}); nothing opened")
            raise PreflightRefused("gate")
    # 1 preflight
    pre = preflight(roots, door, em, allow)
    man["pins"] = {"references": pre["references"], "builds": pre.get("builds"), "r13": pre["r13"]}
    idrefs = pre["idrefs"]
    dk = dk_of(door)
    dk_names = tuple(str(x) for x in dk["label"])
    # 2 R16
    if 2 in want:
        objs[L.FS_KEY] = r16_annot(roots, out, em)
    annot = Path(objs.get(L.FS_KEY, {}).get("member_path") or (Path(roots.data) / L.FS_KEY / FE.R16_NAME))
    # 3 R15
    hcp = None
    if 3 in want:
        hcp = r15_hcp(roots, door, out, em)
        objs[L.HCP_META_KEY] = hcp["meta"]
        if "volume" in hcp:
            objs[L.HCP_VOL_KEY], objs[L.HCP_LIST_KEY] = hcp["volume"], hcp["labels"]
    # 4 R38
    hooks = dict(hooks or {})
    if 4 in want and hcp is not None and hcp.get("status") == FE.STATUS_EXTRACTED:
        vs, ls = objs[L.HCP_VOL_KEY].get("sha256"), objs[L.HCP_LIST_KEY].get("sha256")
        objs["perdonor_hcpmmp1"] = (hooks.get("r38") or (lambda r, e: r38_build(
            r, e, venv_python=venv_python, volume_sha256=vs, label_list_sha256=ls)))(roots, em)
    # 5 local copies
    if 5 in want:
        lt = local_targets(roots, idrefs)
        objs[L.PATEL_KEY] = run_one(roots, lt[L.PATEL_KEY], out, reader=patel_reader(door))
        r = idrefs[L.GIA_CMP_KEY]
        t_cmp = giacomel_target(L.GIA_CMP_KEY, r["url"], tuple(r["refs"]), local_path=r["local_path"], dk_names=dk_names)
        objs[L.GIA_CMP_KEY] = run_one(roots, t_cmp, out, transform=giacomel_transform(door))     # primary: R54
        pe["objects"][L.GIA_CMP_KEY] = run_amended(roots, t_cmp, out, transform=giacomel_transform(door, amend5=True))
        objs[L.HANSEN_CT_KEY] = run_one(roots, lt[L.HANSEN_CT_KEY], out, reader=hansen_reader(door, "ct"))
        objs[L.HANSEN_PC1_KEY] = run_one(roots, lt[L.HANSEN_PC1_KEY], out, reader=hansen_reader(door, "pc1"))
        pc1 = object_of(roots, objs[L.HANSEN_PC1_KEY], "pc1")
        for key, what in ((L.HANSEN_PRED_KEY, "predictors"), (L.HANSEN_INFO_KEY, "cammoun")):
            t, info = prefix_target(roots, door, key, ".csv", em)
            if t is None:
                objs[key] = info
            elif what == "predictors" and pc1 is None:
                objs[key] = {"status": "not computable (gene PC1 not extracted)"}
            else:
                objs[key] = dict(run_one(roots, t, out, reader=hansen_reader(door, what, pc1)), **info)
        for key, kind in ((L.LIU_CT_KEY, "cortthick"), (L.LIU_SV_KEY, "subvol")):
            t_ex, ex = screen_exempt_target(roots, lt[key], door)       # amend_5 E1 (the declared name exemption)
            objs[key] = run_one(roots, t_ex, out, reader=enigma_reader(door, kind))
            if ex is not None:
                objs[key]["screen_exemption"] = ex
        labels_obj = object_of(roots, objs.get(L.HCP_LIST_KEY, {}), "labels")
        if labels_obj is None:
            r15st = (objs.get(L.HCP_LIST_KEY) or {}).get("status")
            objs[L.PRE_KEY] = {"status": RP.STATUS_GLASSER if r15st == RP.STATUS_GLASSER else L.STATUS_UPSTREAM,
                               "why": "R15's label list not extracted"}
        else:
            objs[L.PRE_KEY] = run_one(roots, lt[L.PRE_KEY], out, reader=pretzsch_reader(door, labels_obj["left_names"]))
            pe["objects"][L.PRE_KEY] = run_amended(roots, lt[L.PRE_KEY], out, reader=pretzsch_reader(
                door, labels_obj["left_names"], amend5=True))                       # amend_5 R61' (post-exposure)
        for image in L.LEY_IMAGES:
            objs[L.LEY_VOL_KEY[image]] = run_one(roots, lt[L.LEY_VOL_KEY[image]], out)
            if not annot.is_file():
                r16st = (objs.get(L.FS_KEY) or {}).get("status")
                objs[L.LEY_LH_KEY[image]] = {"status": RP.STATUS_FS_NOT_MATCHING if r16st == RP.STATUS_FS_NOT_MATCHING
                                             else L.STATUS_UPSTREAM, "why": "R16's annot not extracted"}
            else:
                objs[L.LEY_LH_KEY[image]] = run_one(roots, lt[L.LEY_LH_KEY[image]], out,
                                                    reader=leyhausen_reader(door, annot))
    # 6 downloads
    if 6 in want:
        r = idrefs[L.GIA_GOV_KEY]
        url = L.RAW_URL.format(repo=L.GIA_REPO, commit=L.GIA_93DE089, path=L.GIA_XLSX_PATH)
        t_gov = giacomel_target(L.GIA_GOV_KEY, url, tuple(r["refs"]), local_path=None, dk_names=dk_names)
        objs[L.GIA_GOV_KEY] = run_one(roots, t_gov, out, transform=giacomel_transform(door))     # primary: R54
        pe["objects"][L.GIA_GOV_KEY] = run_amended(roots, t_gov, out, transform=giacomel_transform(door, amend5=True))
        tree_t = FE.Target(key="gia_tree_e045bc5", gate=L.GATE, url=L.TREE_API.format(repo=L.GIA_REPO,
                                                                                      commit=L.GIA_E045BC5),
                           kind="file", ext=".json", identity_at_download=True, head_before_get=False)
        objs["gia_tree_e045bc5"] = run_one(roots, tree_t, out, reader=json_reader(door, "tree"))
        tree = {}
        if objs["gia_tree_e045bc5"].get("status") == FE.STATUS_EXTRACTED:
            tdoc = json.loads((Path(roots.data) / "gia_tree_e045bc5" / "carrier.json").read_bytes().decode("utf-8"))
            if tdoc.get("truncated") is False and tdoc.get("sha") == L.GIA_E045BC5 or roots.scratch:
                tree = {e["path"]: (e["sha"], int(e.get("size", -1))) for e in tdoc.get("tree", [])
                        if e.get("type") == "blob"}
        mdd = pre["mdd_paths"]
        for key, path in list(L.GIA_ASD_LISTS.items()) + [(k, f"results/MDD/{k}.tsv") for k in _mdd_list_keys()]:
            ref = mdd.get(path) or ((tree[path][0], tree[path][1], L.GIA_E045BC5) if path in tree else None)
            k2 = f"gia_list_{key}"
            if ref is None:
                objs[k2] = ({"status": L.STATUS_LIST_LAYOUT, "why": "path not in the commit's tree"} if tree else
                            {"status": L.STATUS_UPSTREAM, "why": "the commit's tree listing was not obtained"})
                continue
            t = FE.Target(key=k2, gate=L.GATE, url=L.RAW_URL.format(repo=L.GIA_REPO, commit=ref[2], path=path),
                          kind="file", ext=".tsv", refs=(gh_ref(ref[0], ref[1]),), refusal_status=L.STATUS_LIST_LAYOUT)
            objs[k2] = run_one(roots, t, out, reader=raw_list_reader(door))
        for key in _gedar_keys():
            d = key.split("_")[0]
            path = f"results/{d}/{key}.tsv"
            k2 = f"gia_gedar_{key}"
            ref = mdd.get(path)
            if ref is None:
                objs[k2] = {"status": L.STATUS_UPSTREAM, "why": "path not in gia_mdd_paths.json"}
                continue
            t = FE.Target(key=k2, gate=L.GATE, url=L.RAW_URL.format(repo=L.GIA_REPO, commit=ref[2], path=path),
                          kind="file", ext=".tsv", refs=(gh_ref(ref[0], ref[1]),), refusal_status=L.STATUS_GEDAR_LAYOUT)
            objs[k2] = run_one(roots, t, out, reader=gedar_reader(door))
        scr = [p for p in tree if p.endswith(L.R17_SCRIPT_SUFFIX) or p == L.R17_SCRIPT_SUFFIX.lstrip("/")]
        if len(scr) == 1:
            t = FE.Target(key=L.R17_SCRIPT_KEY, gate=L.GATE,
                          url=L.RAW_URL.format(repo=L.GIA_REPO, commit=L.GIA_E045BC5, path=scr[0]), kind="file",
                          ext=".txt", refs=(gh_ref(*tree[scr[0]]),))
            objs[L.R17_SCRIPT_KEY] = dict(run_one(roots, t, out, reader=script_reader(door)), repo_path_sha256=
                                          PW.sha256_text(scr[0]))
        else:
            objs[L.R17_SCRIPT_KEY] = ({"status": L.STATUS_R17, "why": "not exactly one tree entry", "n": len(scr)}
                                      if tree else {"status": L.STATUS_UPSTREAM,
                                                    "why": "the commit's tree listing was not obtained"})
        for key, (path, prefix) in L.R17_INPUT_PATHS.items():
            if path not in tree:
                objs[key] = ({"status": L.STATUS_R17, "why": "path not in the commit's tree"} if tree else
                             {"status": L.STATUS_UPSTREAM, "why": "the commit's tree listing was not obtained"})
                continue
            t = FE.Target(key=key, gate=L.GATE, url=L.RAW_URL.format(repo=L.GIA_REPO, commit=L.GIA_E045BC5, path=path),
                          kind="file", ext=".csv" if path.endswith(".csv") else ".tsv", refs=(gh_ref(*tree[path]),))
            e = run_one(roots, t, out)
            rec = json.loads((Path(roots.records) / e["record_path"]).read_bytes()) if e.get("record_path") else {}
            sha = ((rec.get("identity") or {}).get("facts") or {}).get("sha256") or ""
            prefix = dict(roots.r17_prefix).get(key, prefix)
            e["prefix_len"] = len(prefix)
            e["prefix_match"] = bool(sha) and sha.startswith(prefix)
            if not e["prefix_match"] and e.get("status") in (FE.STATUS_IDENTITY_ONLY, FE.STATUS_EXTRACTED):
                e["status"] = STATUS_PREFIX_CHANGED
            objs[key] = e
        # claims_register.md:1457-1459 / RUN_PLAN.md:1470-1471: the c022a29 copy compared, differing cells counted
        gov = {sh: object_of(roots, objs.get(L.GIA_GOV_KEY, {}), sh) for sh in L.GIA_SHEETS}
        cmp_ = {sh: object_of(roots, objs.get(L.GIA_CMP_KEY, {}), sh) for sh in L.GIA_SHEETS}
        ok_objs = {sh: o for sh, o in gov.items() if o and "asd" in o}
        ok_cmp = {sh: o for sh, o in cmp_.items() if o and "asd" in o}
        man["giacomel_comparison"] = dict(RD.giacomel_compare(ok_objs, ok_cmp), governs="93de089")
        g5 = {sh: object_of(roots, pe["objects"].get(L.GIA_GOV_KEY, {}), sh) for sh in L.GIA_SHEETS}
        c5 = {sh: object_of(roots, pe["objects"].get(L.GIA_CMP_KEY, {}), sh) for sh in L.GIA_SHEETS}
        pe["giacomel_comparison"] = dict(RD.giacomel_compare({sh: o for sh, o in g5.items() if o and "asd" in o},
                                                             {sh: o for sh, o in c5.items() if o and "asd" in o}),
                                         governs="93de089")
        em.say(f"wp4_material: Giacomel c022a29 comparison: differing cells "
               f"{sum(v.get('n_cells_differing', 0) for v in man['giacomel_comparison'].values() if isinstance(v, dict))}")
    # 7 Sadeghi
    if 7 in want:
        lst = sadeghi_listing(roots, door)
        em.say(f"wp4_material: Sadeghi folder listed in memory: declared {'found' if lst['found'] else 'not found'}; "
               f"names {lst['n_names']}")
        if lst["found"]:
            t, info = prefix_target(roots, door, L.SADEGHI_KEY, ".xlsx", em)
            if t is None:
                objs[L.SADEGHI_KEY] = dict(info, listing=lst)
            else:
                t = dataclasses.replace(t, kind="workbook", sheets=(deg_sheet(),), refusal_status=L.STATUS_DEG)
                objs[L.SADEGHI_KEY] = dict(run_one(roots, t, out, transform=deg_transform), listing=lst, **info)
        else:
            objs[L.SADEGHI_KEY] = {"status": L.STATUS_SADEGHI_ABSENT, "listing": lst,
                                   "note": "R57: the Europe PMC archive route runs in phase 2 only"}
    # 9 R17: the paper's script in the R17 image (rbuild/r17.py) - run BEFORE step 8 (B5: it re-derives the DEG sets)
    if 9 in want:
        objs.update((hooks.get("r17") or run_r17)(roots, man, door, em, out))          # primary: R58 (a)-(c)
        hook = hooks.get("r17")
        if hook is not None and "post_exposure" in inspect.signature(hook).parameters:
            pe["objects"].update(hook(roots, man, door, em, out, post_exposure=True))
        else:
            pe["objects"].update(run_r17(roots, man, door, em, out, post_exposure=True))   # amend_5 R58' (d)
        # amend_5 L130: the script runs AS PUBLISHED; the cells whose second map is a line-130 file carry the label;
        # whether line 130 bites is recorded by sha256 equality only
        man["labels"] = {"line130": dict(line130_record(objs), label=L.LINE130_LABEL, cells=line130_cells())}
        pe["labels"] = {"line130": dict(line130_record({**objs, **pe["objects"]}), label=L.LINE130_LABEL,
                                        cells=line130_cells())}
    # 8 the gated sets (the frozen S-build's build_set), the population restated
    if 8 in want:
        try:
            sm = (hooks.get("sets") or build_sets)(roots, man, out=out)
            man["sets"] = {"manifest_sha256": sm["_sha256"], "manifest_name": sm["_name"], "n_sets": len(sm["sets"]),
                           "restatement": {k: v for k, v in sm["restatement"].items() if k not in ("cells", "rule")}}
            em.say(f"wp4_material: gated sets {len(sm['sets'])}; not testable lt5 "
                   f"{sm['restatement']['n_not_testable_lt5']}; in_m {sm['restatement']['n_in_m_not_testable_lt5']}")
        except PW.StageFailed:
            man["sets"] = {"status": "refused (stage failed)"}
        # the post-exposure version's sets: the same frozen S-build on the overlaid objects, written to their own
        # folder (register_sets/post_freeze/G2_a5), never beside the primary sets
        view = dict(man, objects={**objs, **pe["objects"]}, deg_checks={})
        try:
            sm5 = (hooks.get("sets") or build_sets)(dataclasses.replace(roots, version=L.VERSION_AMEND5), view, out=out)
            pe["sets"] = {"manifest_sha256": sm5["_sha256"], "manifest_name": sm5["_name"], "n_sets": len(sm5["sets"]),
                          "restatement": {k: v for k, v in sm5["restatement"].items() if k not in ("cells", "rule")}}
        except PW.StageFailed:
            pe["sets"] = {"status": "refused (stage failed)"}
        pe["deg_checks"] = view.get("deg_checks") or {}
    # 10 Leyhausen's decoders (R45's form; decided once)
    if 10 in want:
        objs.update((hooks.get("decoders") or run_decoders)(roots, idrefs, door, em, out))
    allx = {**objs, **pe["objects"]}
    allow.add_words(*[k for k in allx if re.fullmatch(r"r17_in_[0-9a-f]{16}", k)])   # R58 (h): the read inputs
    allow.add_words(*[w for e in allx.values() if isinstance(e, dict) for w in (e.get("object_key", ""),
                      f"{e.get('object_key', '')}_extract") if
                      re.fullmatch(r"r17_(map|deg)_(ASD|MDD)_\d+_r\d+|[a-z][a-z0-9_]{1,80}_(a5|v\d+)(_v\d+)?",
                                   str(e.get("object_key", "")))])
    man["final"] = not steps
    rel_counts = {}
    for e in objs.values():
        rel_counts[e.get("status")] = rel_counts.get(e.get("status"), 0) + 1
    # a status that is not text (an entry without one) is counted under the fixed word "none" (2026-10-21: "None"
    # is not vocabulary)
    cnt: dict = {}
    for k, v in rel_counts.items():
        kk = k if isinstance(k, str) else "none"
        cnt[kk] = cnt.get(kk, 0) + v
    man["counts"] = dict(sorted(cnt.items()))
    man["door_admitted"] = len(door.admitted)
    path = roots.next_manifest_path() if man["final"] else (Path(roots.records) / L.GATE /
                                                            f"{L.PARTIAL_PREFIX}.{len(roots.partial_manifests()) + 1}.json")
    allow.add_exact(path)
    manifest_exacts(allow, man)
    manifest_exacts(allow, pe)
    try:
        sha = PW.stage(em, "record", em.write_json, path, man, "identity")
    except PW.PrintRuleViolation:
        incident_note(roots, allow, man)
        raise
    em.say(f"wp4_material: manifest {path} sha256 {sha}; objects {len(objs)}")
    man["_path"], man["_sha256"] = str(path), sha
    return man


# ================================================================================================================
# 10 Leyhausen's decoders
# ================================================================================================================
def decoder_reader4(door: Door, image: int):
    from . import wp3_genes as WG
    from . import wp3_material as W3M
    cache: dict = {}

    def read(path: Path) -> dict:
        if "hg" not in cache:
            cache["hg"] = WG.HGNCTable(door.pinned("hgnc"))
        return {"genes": W3M.decoder_object(door.read_bytes(path), cache["hg"], image)}
    return read


def run_decoders(roots: L.Roots, idrefs: dict, door: Door, em: PW.Emitter, out) -> dict:
    """R63 (draft): R45's decoder (URL with mask=full, one GET, the declared columns, up to 3 transport attempts
    across runs, decided once: wp3_decoder.run_decoder with the G2 keys), for the three Leyhausen images."""
    from . import wp3_decoder as WD
    from . import wp3_layout as W3
    res = {}
    for image in L.LEY_IMAGES:
        key = L.LEY_DECODER_KEY[image]
        r = idrefs[L.LEY_VOL_KEY[image]]
        pre = {"file_url": r["url"], "content_length": r.get("content_length"), "last_modified": r.get("last_modified")}
        t = FE.Target(key=key, gate=L.GATE, url=W3.DECODER_URL.format(image=image), kind="file", ext=".json",
                      identity_at_download=True, head_before_get=False)
        try:
            d = WD.run_decoder(roots, image, t, decoder_reader4(door, image), em, out=out, prefreeze=pre,
                               utc_now=utc_now, key=key)
        except WD.StageStop as e:
            cls = type(e).__name__
            res[key] = {"status": "stopped for the operator", "reason_class": cls if cls in REASON_CLASSES else "other"}
            continue
        if d.get("adopt_record"):
            res[key] = entry(roots, {"record_path": str(Path(d["adopt_record"]))})
        else:
            res[key] = {"status": d.get("status"), "final": True}
    return res


# ================================================================================================================
# 9 R17
# ================================================================================================================
def _carrier(roots: L.Roots, key: str, ext: str) -> Path:
    return Path(roots.data) / key / f"carrier{ext}"


def r17_facts(roots: L.Roots, man: dict, door: Door, out,
              post_exposure: bool = False) -> tuple[dict | None, dict, str | None]:
    """R58 (a)-(c), (h): the repository facts under G2 - the commit record (committer date), the declaration files the
    tree holds (renv.lock, .R-version), the r-hub R versions and Bioconductor's config.yaml (public documents, one GET
    each, no identifier), the script's bytes and repository path - and the run's inputs: the two prefix-held authors'
    files at their paths, every other read path the commit's tree holds (downloaded by blob), and the Sadeghi workbook
    for a read path named like its declared file. Returns (facts, inputs {repository path: local file}, refusal)."""
    from .rbuild import r17 as R17
    objs = man["objects"]
    tp = _carrier(roots, "gia_tree_e045bc5", ".json")
    if (objs.get("gia_tree_e045bc5") or {}).get("status") != FE.STATUS_EXTRACTED:
        return None, {}, "the commit's tree listing was not obtained"
    tdoc = json.loads(door.read_bytes(tp).decode("utf-8"))
    tree = {e["path"]: (e["sha"], int(e.get("size", -1))) for e in tdoc.get("tree", []) if e.get("type") == "blob"}
    scr = [q for q in tree if q.endswith(L.R17_SCRIPT_SUFFIX) or q == L.R17_SCRIPT_SUFFIX.lstrip("/")]
    if len(scr) != 1:
        return None, {}, "not exactly one script entry"
    script_path = scr[0]
    script = door.read_bytes(_carrier(roots, L.R17_SCRIPT_KEY, ".txt"))
    docs = {}
    for key, url, ext in ((L.R17_COMMIT_KEY, L.GH_COMMIT_API.format(repo=L.GIA_REPO, commit=L.GIA_E045BC5), ".json"),
                          (L.R17_RVERSIONS_KEY, R17.RVERSIONS_API, ".json"), (L.R17_BIOC_KEY, R17.BIOC_CONFIG, ".txt")):
        t = FE.Target(key=key, gate=L.GATE, url=url, kind="file", ext=ext, identity_at_download=True,
                      head_before_get=False)
        objs[key] = run_one(roots, t, out)
        if objs[key].get("status") not in (FE.STATUS_IDENTITY_ONLY, FE.STATUS_EXTRACTED):
            return None, {}, f"a public R17 document was not obtained ({key})"
        docs[key] = door.read_bytes(_carrier(roots, key, ext))
    cdoc = json.loads(docs[L.R17_COMMIT_KEY].decode("utf-8"))
    if str(cdoc.get("sha", "")) != L.GIA_E045BC5:
        return None, {}, "the commit record is not e045bc5's"
    cdate = str(((cdoc.get("commit") or {}).get("committer") or {}).get("date", ""))
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T.*", cdate):
        return None, {}, "the commit record has no committer date"
    decl = {}
    for name, (key, ext) in L.R17_DECL_KEYS.items():
        if name in tree:
            t = FE.Target(key=key, gate=L.GATE, url=L.RAW_URL.format(repo=L.GIA_REPO, commit=L.GIA_E045BC5, path=name),
                          kind="file", ext=ext, refs=(gh_ref(*tree[name]),))
            objs[key] = run_one(roots, t, out)
            if objs[key].get("status") not in (FE.STATUS_IDENTITY_ONLY, FE.STATUS_EXTRACTED):
                return None, {}, "a declaration file failed its identity"
            decl[name] = door.read_bytes(_carrier(roots, key, ext))
    inputs = {script_path: _carrier(roots, L.R17_SCRIPT_KEY, ".txt")}
    for key, (path, _pfx) in L.R17_INPUT_PATHS.items():
        if (objs.get(key) or {}).get("status") not in (FE.STATUS_IDENTITY_ONLY, FE.STATUS_EXTRACTED):
            return None, {}, "an input failed its identity"
        inputs[path] = _carrier(roots, key, ".csv" if path.endswith(".csv") else ".tsv")
    req = RD.r_script_requirements(script.decode("utf-8", "replace"))
    sad_name = L.SADEGHI_DECLARED_REL[-1]
    sad_ok = (objs.get(L.SADEGHI_KEY) or {}).get("status") == FE.STATUS_EXTRACTED
    known = set(tree) | ({sad_name} if sad_ok else set())
    # amend_5 v2 R58' (d), POST-EXPOSURE version only: 'mmc2(<n>).xlsx' read as the Sadeghi workbook
    dup = (lambda name: bool(post_exposure and sad_ok and L.SADEGHI_DUP_NAME.match(name)))
    pl = R17.placement(req["read_paths"], script_path, known, abs_strings=tuple(req.get("abs_strings") or ()),
                       name_ok=dup)
    n_tree_inputs = 0
    sad_dup = {"applied": False}
    for rp, q in pl["resolved"].items():
        if q in inputs:
            continue
        if q in tree:
            key = "r17_in_" + hashlib.sha256(q.encode("utf-8")).hexdigest()[:16]
            ext = "." + q.rsplit(".", 1)[-1].lower() if re.search(r"\.[A-Za-z0-9]{1,5}$", q) else ".bin"
            t = FE.Target(key=key, gate=L.GATE, url=L.RAW_URL.format(repo=L.GIA_REPO, commit=L.GIA_E045BC5, path=q),
                          kind="file", ext=ext, refs=(gh_ref(*tree[q]),))
            objs[key] = run_one(roots, t, out)
            if objs[key].get("status") not in (FE.STATUS_IDENTITY_ONLY, FE.STATUS_EXTRACTED):
                return None, {}, "a read input failed its identity"
            inputs[q] = _carrier(roots, key, ext)
            n_tree_inputs += 1
        elif q.rsplit("/", 1)[-1] == sad_name and sad_ok:
            inputs[q] = Path(roots.prefix_pin(L.SADEGHI_KEY)[0])
        elif dup(q.rsplit("/", 1)[-1]):
            # amend_5 R58' (d): 'mmc2(1).xlsx' is the Sadeghi workbook only if the staged file IS the pinned copy
            sp = Path(roots.prefix_pin(L.SADEGHI_KEY)[0])
            have = hashlib.sha256(door.read_bytes(sp)).hexdigest()
            pinned = (objs.get(L.SADEGHI_KEY) or {}).get("sha256")
            sad_dup = {"applied": True, "sha256_match": have == pinned, "sha256": have}
            if have == pinned:
                inputs[q] = sp
    out_dirs = R17.out_dirs_rel(req.get("out_dirs") or (), pl.get("abs_roots") or ())
    facts = {"commit": L.GIA_E045BC5, "commit_date": cdate, "decl_files": decl, "rversions": docs[L.R17_RVERSIONS_KEY],
             "bioc_config": docs[L.R17_BIOC_KEY], "script": script, "script_path": script_path,
             "cwd_rel": pl["cwd_rel"], "n_read_paths": len(set(req["read_paths"])),
             "n_read_paths_unresolved": pl["n_unresolved"], "n_tree_inputs": n_tree_inputs,
             "abs_roots": tuple(pl.get("abs_roots") or ()), "out_dirs": tuple(out_dirs),
             "n_abs_roots": len(pl.get("abs_roots") or ()), "n_out_dirs": len(out_dirs),
             "n_read_vars": int(req.get("n_read_vars") or 0), "sadeghi_dup_name": sad_dup}
    return facts, inputs, None


def r17_outputs(roots: L.Roots, rec: dict, door: Door, out, adaptation: dict | None = None) -> dict:
    """The run's created files: the rebuilt GEDAR maps (`<DX>_literature_TPRS_thr_<t>.tsv`, R56's layout) and the DEG
    lists (wp4_read.deg_output_key), each saved through the wrapper as a pinned local copy (sha256 and size taken from
    the run's created-file record) -> objects r17_map_<DX>_<t> / r17_deg_<DX>_<t>. A key two files claim is skipped.
    Each run's objects are saved under a run-indexed key (<key>_r<n>, n = the run's work folder index), so a rerun of
    the stage (e.g. after a Q3 adaptation) never meets an earlier run's object of other bytes (saved objects are never
    overwritten, FE9 / FE18); the manifest entry under <key> names it (object_key)."""
    work = Path(rec["_workdir"])
    run_ix = int(rec.get("workdir_index") or 1)
    objs, deg_seen, map_seen = {}, {}, {}
    for rel in rec.get("_created_paths", []):
        f = work / rel
        data = door.read_bytes(f)
        name = rel.rsplit("/", 1)[-1]
        m = RD.R17_MAP_NAME.match(name)
        if m:
            map_seen.setdefault(f"r17_map_{m.group(1)}_{m.group(2)}", []).append((f, data, gedar_reader(door)))
            continue
        if adaptation is not None:                     # Q3: the operator's format-only adaptation replaces the rule
            k = RD.deg_output_key_adapted(rel, data, adaptation)
            if k is not None:
                (dx, thr), spec = k
                deg_seen.setdefault(f"r17_deg_{dx}_{thr}", []).append(
                    (f, data, deg_list_reader(door, spec["symbol"], spec["weight"], spec["delimiter"])))
            continue
        k = RD.deg_output_key(rel, data)
        if k is not None:
            (dx, thr), sym = k
            deg_seen.setdefault(f"r17_deg_{dx}_{thr}", []).append((f, data, deg_list_reader(door, sym)))
    for key, hits in list(map_seen.items()) + list(deg_seen.items()):
        if len(hits) != 1:
            objs[key] = {"status": L.STATUS_DEG_NOT_FOUND if key.startswith("r17_deg_") else L.STATUS_R17,
                         "why": "more than one created file for the key", "n": len(hits)}
            continue
        f, data, reader = hits[0]
        okey = f"{key}_r{run_ix}"
        t = FE.Target(key=okey, gate=L.GATE, url="https://none.invalid/r17-run-output", kind="file",
                      ext="." + f.name.rsplit(".", 1)[-1].lower(),
                      pinned_sha256=hashlib.sha256(data).hexdigest(), pinned_bytes=len(data), local_path=str(f),
                      url_note="no URL: a file the R17 run created (sha256 and size from the run's record)")
        objs[key] = dict(run_one(roots, t, out, reader=reader), object_key=okey)
    return objs


def deg_list_reader(door: Door, sym: str, weight: str = "logFC", delimiter: str | None = None):
    def read(path: Path) -> dict:
        rows = RD.deg_list_rows(door.read_bytes(path), sym, weight, delimiter)
        return {"raw": {"rows": rows, "n_rows": len(rows)}}
    return read


def deg_adaptation(roots: L.Roots, door: Door) -> tuple[dict | None, str | None]:
    """amend_4 v3 Q3: the operator's format-only adaptation file (control/G2/deg_list_adaptation.json), if present:
    exactly DEG_ADAPTATION_KEYS, name_regex compiles and names the groups dx and thr, the headers are non-empty text,
    the delimiter is null, a tab or a comma. Returns (the adaptation, its sha256) or (None, None); a malformed file
    raises ValueError (the stage stops: an adaptation is never half-applied)."""
    p = Path(roots.control) / L.GATE / L.DEG_ADAPTATION_NAME
    if not p.is_file():
        return None, None
    data = door.read_bytes(p)
    ad = json.loads(data.decode("utf-8"))
    if not isinstance(ad, dict) or set(ad) != set(L.DEG_ADAPTATION_KEYS):
        raise ValueError("deg_list_adaptation.json: keys")
    rx = re.compile(ad["name_regex"])
    if not {"dx", "thr"} <= set(rx.groupindex):
        raise ValueError("deg_list_adaptation.json: name_regex needs the groups dx and thr")
    for k in ("symbol_header", "weight_header"):
        if not (isinstance(ad[k], str) and ad[k].strip()):
            raise ValueError(f"deg_list_adaptation.json: {k}")
    if ad["delimiter"] not in (None, "\t", ","):
        raise ValueError("deg_list_adaptation.json: delimiter")
    return ad, hashlib.sha256(data).hexdigest()


def line130_cells() -> list:
    """amend_5 L130: the G2 cells whose second map is an MDD TPRS file - the R17-rebuilt MDD_literature_TPRS maps
    (the MDD-DEG cells of the MDD set, r17_map_MDD_<t>) and the repository's MDD GEDAR TPRS maps (the MDD list cells,
    gia_gedar_MDD_TPRS_thr_<t>), both written by the script's line 130."""
    from . import wp4_sets as WS
    out = []
    for cell, (kind, key, _w) in sorted(WS.GATED_CELLS.items()):
        if kind == "deg" and key.startswith("MDD_"):
            out.append(cell)
    return out


def line130_record(objs: dict) -> dict:
    """amend_5 v2 L130 (C): does line 130 bite? By sha256 equality only, per threshold: the R17 run's created
    MDD_literature_TPRS file vs the ASD one (True = the bug bites; None = a file absent); and, recorded beside, the
    repository's eda33ab GEDAR files (results/<D>/<D>_TPRS_thr_<t>.tsv, another file family than line 130's
    <D>_literature_TPRS_thr_<t>.tsv) MDD vs ASD."""
    def eq(a, b):
        sa, sb = (objs.get(a) or {}).get("sha256"), (objs.get(b) or {}).get("sha256")
        return (sa == sb) if (isinstance(sa, str) and isinstance(sb, str)) else None
    return {"r17_mdd_equals_asd": {str(t): eq(f"r17_map_MDD_{t}", f"r17_map_ASD_{t}") for t in (1, 5, 10)},
            "eda33ab_mdd_equals_asd": {str(t): eq(f"gia_gedar_MDD_TPRS_thr_{t}", f"gia_gedar_ASD_TPRS_thr_{t}")
                                       for t in (1, 5, 10)}}


def row_labels(cell_id: str) -> list:
    """The amend_5 labels a G2 row carries (wp4_sources.row_labels; the report reads them beside the row)."""
    return [L.LINE130_LABEL] if cell_id in set(line130_cells()) else []


def run_r17(roots: L.Roots, man: dict, door: Door, em: PW.Emitter, out, *, docker=None,
            post_exposure: bool = False) -> dict:
    """R58 (draft) / R17: the parameters from the repository facts read under G2 (r17_facts), the image built and
    pinned, the script run with network none on the identity-checked inputs, its outputs saved (r17_outputs). Any
    failure -> R17's fallback status for the DEG cells. docker: the builder (rbuild.r17.DockerR17 in production,
    under artifacts/<G2>/r17; tests pass one with a local base image, or a fake with params(facts) / build(params) /
    run(image, params, inputs=, script_rel=, cwd_rel=)). Scratch roots without a builder: not run."""
    from .rbuild import r17 as R17
    objs = man["objects"]
    scr = objs.get(L.R17_SCRIPT_KEY) or {}
    if scr.get("status") != FE.STATUS_EXTRACTED:
        return {"r17": {"status": L.STATUS_UPSTREAM, "why": "the script was not obtained"}}
    for k in (L.R17_AHBA_KEY, L.R17_HPA_KEY):
        if (objs.get(k) or {}).get("status") not in (FE.STATUS_IDENTITY_ONLY, FE.STATUS_EXTRACTED):
            return {"r17": {"status": L.STATUS_UPSTREAM, "why": "an input failed its identity"}}
    if docker is None:
        if roots.scratch:
            return {"r17": {"status": "not run (scratch: no R17 builder given)"}}
        docker = R17.DockerR17(Path(roots.artifacts) / L.GATE / "r17")
    try:
        facts, inputs, why = r17_facts(roots, man, door, out, post_exposure=post_exposure)
        if why:
            return {"r17": {"status": L.STATUS_UPSTREAM, "why": why}}
        params = docker.params(facts)
        image = docker.build(params)
        extra = ({"abs_roots": facts["abs_roots"], "out_dirs": facts["out_dirs"]}
                 if facts.get("abs_roots") or facts.get("out_dirs") else {})     # amend_5 R58' (a) / (c)
        rec = docker.run(image, params, inputs=inputs, script_rel=facts["script_path"], cwd_rel=facts["cwd_rel"],
                         **extra)
    except R17.R17Refused as e:
        # a parameter / image / placement step (ours) refused before the script ran: never the paper's status
        return {"r17": {"status": L.STATUS_UPSTREAM, "why": e.what if e.what in R17.REFUSALS else R17.REFUSAL_UNLISTED}}
    st = rec.get("status") or "ran"
    pj = json.dumps(params, sort_keys=True, default=str).encode("utf-8") if isinstance(params, dict) else b""
    res = {"r17": {**{k: v for k, v in rec.items() if not k.startswith("_") and k != "image"}, "status": st,
                   "params_sha256": hashlib.sha256(pj).hexdigest(),
                   "r_version": ((params or {}).get("r") or {}).get("version") if isinstance(params, dict) else None,
                   "bioc_version": ((params or {}).get("bioc") or {}).get("version") if isinstance(params, dict)
                   else None,
                   "n_packages": len((params or {}).get("packages") or []) if isinstance(params, dict) else None,
                   "preinstalled": bool((params or {}).get("preinstalled")) if isinstance(params, dict) else None,
                   "facts": {k: facts[k] for k in ("commit_date", "n_read_paths", "n_read_paths_unresolved",
                                                   "n_tree_inputs", "n_abs_roots", "n_out_dirs", "n_read_vars",
                                                   "sadeghi_dup_name") if k in facts}}}
    if isinstance(res["r17"].get("build"), dict):
        res["r17"]["build"] = {k: v for k, v in res["r17"]["build"].items() if k != "tag"}
    if rec.get("ok") and rec.get("_workdir"):
        ad, ad_sha = deg_adaptation(roots, door)
        outs = r17_outputs(roots, rec, door, out, adaptation=ad)
        res.update(outs)
        if ad is not None:                             # recorded as a deviation, labelled post-exposure (Q3)
            res["r17"]["deviation"] = {"label": L.DEG_DEVIATION_LABEL, "adaptation_sha256": ad_sha,
                                       "adaptation_keys": sorted(ad), "n_lists_located": sum(
                                           1 for k, e in outs.items() if k.startswith("r17_deg_")
                                           and e.get("status") == FE.STATUS_EXTRACTED)}
    em.say(f"wp4_material: R17 run exit {rec.get('exit')}; created files {len(rec.get('created') or {})}")
    return res


# ================================================================================================================
# 8 the gated sets
# ================================================================================================================
def manifest_exacts(allow: PW.AllowList, man: dict) -> None:
    """The runner-built names a manifest holds that no vocabulary can (run_material before the write; X6): the
    entries' member paths, and the R17 tree-input keys r17_in_<16 hex> (runner-built from a path's sha256; 2026-10-21:
    such a key failed the identity channel as one word)."""
    for k, e in (man.get("objects") or {}).items():
        if re.fullmatch(r"r17_in_[0-9a-f]{16}", str(k)):
            allow.add_exact(str(k))
        for f in ("member_path",):
            if isinstance(e, dict) and e.get(f):
                allow.add_exact(Path(e[f]))


def failing_fields(allow: PW.AllowList, doc, ctx: str = "identity") -> list:
    """The dotted paths (key names and list indexes only, never a value) of the leaves whose rendered JSON line the
    print rule refuses. 2026-10-21: a key is first checked on its own; a key outside the vocabulary (it may be
    data-derived, e.g. a gene symbol) is never named: its parent reports "<k non-vocabulary keys under PATH>" and its
    subtree is not walked. Lines are rendered as write_json renders them (ensure_ascii)."""
    out = []

    def line_ok(k, v) -> bool:
        return allow.check("   " + json.dumps({k: v}, ensure_ascii=True, allow_nan=False)[1:-1], ctx)

    def walk(o, path):
        if isinstance(o, dict):
            bad = 0
            for k, v in o.items():
                if not (isinstance(k, str) and line_ok(k, 0)):
                    bad += 1
                    continue
                if isinstance(v, (dict, list)):
                    walk(v, f"{path}.{k}")
                elif not line_ok(k, v):
                    out.append(f"{path}.{k}")
            if bad:
                out.append(f"<{bad} non-vocabulary keys under {path or '.'}>")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, (dict, list)):
                    walk(v, f"{path}[{i}]")
                elif not allow.check("   " + json.dumps(v, ensure_ascii=True, allow_nan=False), ctx):
                    out.append(f"{path}[{i}]")
        elif not allow.check("   " + json.dumps(o, ensure_ascii=True, allow_nan=False), ctx):
            out.append(path or ".")
    walk(doc, "")
    return out


def incident_note(roots: L.Roots, allow: PW.AllowList, man: dict) -> Path:
    """ETHICS_PRIVACY incident procedure (stop, propagate nothing, record counts): the refused manifest is NOT
    written; this note holds only the count and the dotted field paths (names) that failed, written raw (no value
    can be in it: a path whose own name fails the rule is replaced by its sha256)."""
    paths = failing_fields(allow, man)
    safe = [p if re.fullmatch(r"[A-Za-z0-9_.\[\]\-]{1,200}|<\d+ non-vocabulary keys under [A-Za-z0-9_.\[\]\-]{1,200}>",
                              p) else "sha256:" + PW.sha256_text(p) for p in paths]
    d = Path(roots.control) / L.GATE
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"manifest_print_rule_incident_{utc_now().replace(':', '').replace('-', '')}.json"
    data = (json.dumps({"what": "the G2 manifest was refused by the print rule and not written",
                        "n_failing_fields": len(safe), "failing_field_paths": safe}, indent=1) + "\n").encode("utf-8")
    p.write_bytes(data)
    if p.read_bytes() != data:
        raise OSError("read-back")
    return p


def deg_sheet() -> FE.SheetDecl:
    """R57 / R58 (f) (draft): the workbook's one sheet selected by DEG_SHEET_RULE; the exact headers Dx, p.value,
    logFC and the first symbol column of DEG_SYMBOL_ALTERNATIVES."""
    return FE.SheetDecl(key="deg", name="(by rule)", mode="columns_search", name_rule=L.DEG_SHEET_RULE,
                        name_status=L.STATUS_DEG,
                        columns=(FE.Column("Dx", "dx"), FE.Column("p.value", "p", True), FE.Column("logFC", "lfc", True)),
                        vocab=L.DEG_SYMBOL_ALTERNATIVES)


def deg_transform(objects: dict) -> dict:
    """The gene-level content the DEG sets need (the rows of Dx ASD and MDD: symbol, p.value, logFC); nothing else.
    2026-10-17 (the TypeError at save): a workbook cell may be a date / time (a spreadsheet's date-converted gene
    symbol) or another non-text value; only a non-empty text symbol and finite int / float p.value and logFC are kept
    (JSON-safe primitives, so the object can be saved); every other row of Dx ASD / MDD is excluded and counted by the
    cell's TYPE NAME only (never its value). The definition's pool count (3,599) is still the check."""
    import math as _m
    v = objects["deg"]
    sym, dx, p_, lfc = (v.column(v.declared[k]) for k in ("alt", "dx", "p", "lfc"))

    def num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool) and _m.isfinite(float(x))
    out = {"symbol": [], "dx": [], "p": [], "logFC": []}
    excluded: dict = {}
    for k, d in enumerate(dx):
        if not (isinstance(d, str) and d.strip() in ("ASD", "MDD")):
            continue
        s, a, b = sym[k], p_[k], lfc[k]
        if not (isinstance(s, str) and s.strip()):
            key = f"symbol_{type(s).__name__}"
        elif not num(a):
            key = f"p_{type(a).__name__}"
        elif not num(b):
            key = f"logFC_{type(b).__name__}"
        else:
            out["symbol"].append(s.strip())
            out["dx"].append(d.strip())
            out["p"].append(float(a))
            out["logFC"].append(float(b))
            continue
        excluded[key] = excluded.get(key, 0) + 1
    return {"deg": dict(out, n_rows_kept=len(out["dx"]), n_rows_excluded_by_type=dict(sorted(excluded.items())))}


def deg_raws(roots: L.Roots, man: dict) -> tuple[dict, dict]:
    """The 18 DEG cells' raw rows (R58 (f) v2, asdg-skeptic B5): S = the script's own list for the cell (object
    r17_deg_<DX>_<t>, rebuilt by the R17 run); the check = the TSV's definition (m = round(n x thr) on the AHBA x HPA
    pool; the ASD pool the registered 3,599), computed in Python on the workbook rows and the authors' two files; the
    Python set is recorded beside as a cross-check only. A failed check leaves the cell without a set (its status in
    the sets manifest's sources: STATUS_DEG_CHECK); no script list -> STATUS_DEG_NOT_FOUND (R17's status when the run
    failed)."""
    from . import wp4_sets as WS
    objs = man["objects"]
    deg = object_of(roots, objs.get(L.SADEGHI_KEY, {}), "deg")
    pool = None
    try:
        ah = (Path(roots.data) / L.R17_AHBA_KEY / "carrier.csv").read_bytes()
        hp = (Path(roots.data) / L.R17_HPA_KEY / "carrier.tsv").read_bytes()
        pool = RD.ahba_hpa_pool(ah, hp)
    except (OSError, RD.W4Refused):
        pool = None
    ran = ((objs.get("r17") or {}).get("status") == "ran")
    out, src = {}, {}
    man.setdefault("deg_checks", {})
    for cell, (kind, key, _w) in WS.GATED_CELLS.items():
        if kind != "deg":
            continue
        dx, thr = key.split("_")
        okey = f"r17_deg_{dx}_{thr}"
        e = objs.get(okey) or {}
        lst = object_of(roots, e, "raw")
        if lst is None:
            r17st = (objs.get("r17") or {}).get("status")
            man["deg_checks"][cell] = {"status": L.STATUS_DEG_NOT_FOUND if ran else (
                L.STATUS_R17 if r17st == L.STATUS_R17 else L.STATUS_UPSTREAM)}
            continue
        py = None
        if deg is not None and pool is not None:
            try:
                py = RD.deg_set(deg["symbol"], deg["dx"], deg["p"], deg["logFC"], pool, dx, int(thr))
            except RD.W4Refused:
                py = None
        chk = RD.deg_check([r["symbol"] for r in lst["rows"]], py, dx, int(thr))
        man["deg_checks"][cell] = dict(chk, status=None if chk["passed"] else L.STATUS_DEG_CHECK)
        if not chk["passed"]:
            continue
        out[cell] = lst["rows"]
        # the source names the list's CONTENT (its rows' sha256), not the run-indexed object: an identical rerun of
        # R17 rebuilds byte-identical set files (never overwritten); the object's sha256 is in the G2 manifest
        rows_sha = hashlib.sha256(json.dumps(lst["rows"], sort_keys=True).encode("utf-8")).hexdigest()
        src[cell] = {"object": okey, "rows_sha256": rows_sha, "m_script": chk["m_script"],
                     "m_definition": chk["m_definition"], "n_pool": chk["n_pool"],
                     "rule": "R58 (f) v2: S re-derived by the paper's script (R17); the TSV definition the check"}
    return out, src


def raws_of(roots: L.Roots, man: dict) -> dict:
    from . import wp4_sets as WS
    out, src = deg_raws(roots, man)
    for cell, (kind, key, _w) in WS.GATED_CELLS.items():
        if kind != "list":
            continue
        e = man["objects"].get(f"gia_list_{key}") or {}
        o = object_of(roots, e, "raw")
        if o is None:
            continue
        out[cell] = o["rows"]
        src[cell] = {"object": f"gia_list_{key}", "object_sha256": e.get("object_sha256")}
    return out, src


def parse_in_m(value, cell: str) -> bool:
    """The TSV's verdict_counted_in_m of a G2 cell: exactly "yes" -> True, "no" -> False; anything else refuses
    (2026-10-21: bool("no") was True, so every G2 cell's restatement read in m)."""
    if value == "yes":
        return True
    if value == "no":
        return False
    raise ValueError(f"verdict_counted_in_m of {cell} is neither 'yes' nor 'no'")


def rows_by_cell_of(repo: Path) -> dict:
    from . import loader as LD
    data = LD.lf((Path(repo) / LD.TSV_PATH).read_bytes())
    if hashlib.sha256(data).hexdigest() != LD.TSV_SHA256:
        raise AssertionError("the TSV differs from its L2 pin")
    _, rows = LD.parse_tsv_bytes(data)
    return {r.cell_id: {"analysis_class": r["analysis_class"], "in_m": parse_in_m(r.m_membership, r.cell_id)}
            for r in rows
            if r.gate == "G2"}


def build_sets(roots: L.Roots, man: dict, *, hg=None, uni=None, sb=None, rows_by_cell=None, out=None) -> dict:
    """Step 8: the 41 gated sets by the FROZEN S-build (wp4_sets). Production: hg = the S-build's own HGNC (its pinned
    table), uni = its load_universes (the pinned AHBA matrices); tests pass stand-ins."""
    from . import wp4_sets as WS
    allow = _allow(roots)
    allow.add_words("gated_G2", *[WS.set_id(c) for c in WS.GATED_CELLS], "HGNC", "drops", "written")
    allow.add_exact(roots.set_dir())
    em = PW.Emitter(allow, stream=out)
    sb = sb or WS.frozen_s_build()
    hg = hg or sb.HGNC()
    if uni is None:
        uni, _meta = sb.load_universes(hg)
    raws, src = raws_of(roots, man)
    rows_by_cell = rows_by_cell or rows_by_cell_of(Path(roots.repo))
    return WS.build_all(roots, raws, hg, uni, sb, rows_by_cell, src, em=em)


# ================================================================================================================
# CLI
# ================================================================================================================
def r13_check(repo: Path) -> dict:
    """R13 (RUN_PLAN.md:722-726): run P17's WGCNA bicor checks (tests/test_repro_p17.py --require-docker) and record
    the outcome with this repro.py's LF sha256. No G2 material is involved (synthetic vector pairs)."""
    import tempfile
    py = sys.executable
    with tempfile.TemporaryDirectory(prefix="a1_r13_") as td:
        r = subprocess.run([py, "-X", "utf8", "-m", "a1_audit.tests.test_repro_p17", "--require-docker", "--scratch",
                            td], cwd=str(repo / "arcs/audit/src"), capture_output=True, timeout=7200)
    text = r.stdout.decode("ascii", "replace")
    lines = [ln for ln in text.splitlines() if ln.startswith(("PASS", "FAIL", "SKIP"))]
    wg = [ln for ln in lines if "WGCNA" in ln or "wgcna" in ln]
    rec = {"schema": R13_SCHEMA, "what": "R13's bicor against WGCNA::bicor on 1,000 synthetic vector pairs, run before "
                                         "any G2 map is read (RUN_PLAN.md:722-726; tests/test_repro_p17.py)",
           "date_utc": utc_now(), "exit": int(r.returncode), "n_pass": sum(ln.startswith("PASS") for ln in lines),
           "n_fail": sum(ln.startswith("FAIL") for ln in lines), "n_skip": sum(ln.startswith("SKIP") for ln in lines),
           "wgcna_lines": len(wg), "wgcna_check": "PASS" if (wg and all(ln.startswith("PASS") for ln in wg)
                                                              and r.returncode == 0) else "FAIL",
           "repro_py_lf_sha256": repro_sha256(), "stdout_sha256": hashlib.sha256(r.stdout).hexdigest()}
    p = repo / R13_RECORD_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(rec, indent=1) + "\n").encode("utf-8")
    p.write_bytes(data)
    if p.read_bytes() != data:
        raise OSError("read-back")
    return rec


def r38_build_cli(a) -> int:
    """`r38-build` (asdg-skeptic B3): the HCP-MMP1 volume is G2 material, so before it is read: the draft guard and
    gate G2 (production roots; scratch roots skip both, as run_material does), R13's record passed, the paths are the
    layout's (the roots' data folder), and the R15 identities are checked by the build before any parse. Exit 2 =
    refused, nothing read."""
    from . import ahba_extras as AX
    if a.roots_spec:
        roots = L.Roots.from_spec(json.loads(Path(a.roots_spec).read_bytes().decode("utf-8")))
    else:
        from . import run as R
        roots = L.Roots.production(repo=L.REPO, out_repo=R.main_repository(L.REPO))
    why = None
    if not roots.scratch:
        ok, why_p = L.production_allowed()
        if not ok:
            why = why_p
        elif not gates.step3v_check(Path(roots.repo))[0]:
            why = "gate G2 closed"
    if why is None and r13_status(roots, Door(roots))["result"] != "pass":
        why = "R13's bicor record has not passed"
    want = (Path(roots.data) / L.HCP_VOL_KEY / "carrier.nii.gz", Path(roots.data) / L.HCP_LIST_KEY / "carrier.txt",
            Path(roots.hcp_build))
    if why is None and tuple(Path(x).resolve() for x in (a.volume, a.labels, a.out)) != \
            tuple(p.resolve() for p in want):
        why = "the paths are not the layout's"
    if why is None and not all(re.fullmatch(r"[0-9a-f]{64}", x) for x in (a.volume_sha256, a.labels_sha256)):
        why = "the R15 identities are not sha256s"
    if why is not None:
        print(f"wp4_material: r38-build refused ({why}); nothing read")
        return 2
    try:
        rec = AX.build_perdonor_hcpmmp1(Path(a.volume), Path(a.labels).read_bytes().decode("utf-8"), Path(a.out),
                                        volume_sha256=a.volume_sha256, label_list_sha256=a.labels_sha256)
    except Exception as e:  # noqa: BLE001 - the build's own refusal (identity) or a failure: exit 1, type only
        print(f"wp4_material: R38 build failed ({type(e).__name__})")
        return 1
    print(f"wp4_material: R38 build ok {rec['ok']}; outputs {len(rec['outputs'])}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m a1_audit.wp4_material")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    sub.add_parser("r13-check")
    rb = sub.add_parser("r38-build")
    rb.add_argument("--volume", required=True)
    rb.add_argument("--labels", required=True)
    rb.add_argument("--out", required=True)
    rb.add_argument("--volume-sha256", required=True)
    rb.add_argument("--labels-sha256", required=True)
    rb.add_argument("--roots-spec", default=None, help="a Roots.to_spec JSON (r38_build writes it); default production")
    ru = sub.add_parser("run")
    ru.add_argument("--commit", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "plan":
        for ln in PLAN_LINES:
            print(ln)
        return 0
    if a.cmd == "r13-check":
        rec = r13_check(L.REPO)
        print(f"wp4_material: R13 record exit {rec['exit']} PASS {rec['n_pass']} FAIL {rec['n_fail']} SKIP "
              f"{rec['n_skip']}; WGCNA {rec['wgcna_check']}")
        return 0 if rec["wgcna_check"] == "PASS" else 1
    if a.cmd == "r38-build":
        return r38_build_cli(a)
    ok, why = L.production_allowed()
    if not ok:
        print(PW.ascii_safe(why) if hasattr(PW, "ascii_safe") else why.encode("ascii", "replace").decode("ascii"))
        return 2
    from . import launch as LA
    rec = LA.launch(L.REPO, a.commit, "G2")
    from . import run as R
    roots = L.Roots.production(repo=L.REPO, out_repo=R.main_repository(L.REPO))
    man = run_material(roots, run_info=run_info_of(a.commit, rec))
    return 0 if man.get("final") else 1


PLAN_LINES = (
    "WP4 G2 material stage (phase 2; RUN_PLAN §11; RUN_PLAN_amend_4 R51-R64 once frozen):",
    "  0 gate G2 (step3v_open) and the draft guard; 1 preflight (pins, builds, identity references, pdfplumber, R13)",
    "  2 R16 FreeSurfer 7.4.1 lh.aparc.annot (stream); 3 R15 figshare 3501911 volume + label list; 4 R38 build",
    "  5 local copies: Patel eTable 4; Giacomel c022a29; Hansen x4; Liu T3 x2; Pretzsch eTable13; Leyhausen x6",
    "  6 downloads: Giacomel 93de089; e045bc5 tree; 14 lists; 6 GEDAR maps; R17 script and inputs",
    "  7 Sadeghi DEG workbook (folder listed in memory); 8 gated sets (41); 9 R17 run; 10 Leyhausen decoders x3",
    "  11 the G2 manifest (register_maps/post_freeze/G2/wp4_material_manifest.json)",
)

if __name__ == "__main__":
    sys.exit(main())
