"""WP3 material stage (RUN_PLAN.md v3.1 §10, §18 WP3 "ungated material (identity, decoder fetch, re-parcellation,
Moreau's declared-sheet read)", §8 steps 0-6, R18, R22, R43; FROZEN). Phase 1 builds and tests this on synthetic
stand-ins only; phase 2 runs it once on the real files (the commands are in the WP3 phase-1 report).

    python -X utf8 -u -m a1_audit.wp3_material run --commit <sha>                   # phase 2: launch, then material
    python -X utf8 -m a1_audit.wp3_material plan                                    # what phase 2 opens / writes
    python -X utf8 -m a1_audit.wp3_material dry [--scratch DIR]                     # dry dispatch, counts only

Order (each object through fetch_extract.run_target: gate (ungated: open) -> pinned copy / fetch -> identity -> read in
§8's masked stages -> save with sha256 and read-back -> quarantine + deletion REQUEST if identifier-bearing -> R18
record; nothing is ever deleted):
  1 segura_790618, segura_781986: the local NIfTI copies the pre-freeze identity record names (U-W3-1), identity at use
    (sha256 + size of the copy on disk, NeuroVault's size: claims_register.md:1090-1094), then the §1.7 volume rule onto
    V-AAL (reparcel.volume_to_parcels: the PCP AAL atlas, sha256 pinned, resampled to the map grid by nearest
    neighbour; voxels = 0 missing; < 50 % coverage dropped and reported) for every AAL parcel of the pinned atlas info.
  2 segura_decoder_790618, segura_decoder_781986: the NeuroVault decoder output (mask=full) fetched by the frozen
    fetch_util.get (no identifier sent), identity recorded at download (no pre-freeze identity exists: R22 fetches it
    after the freeze), the declared columns read (wp3_layout.DECODER_DECLARED, exact texts from NeuroVault's source;
    U-W3-3) and kept as a gene-level object keyed by HGNC symbols (the S-build's rule: the Entrez id, else the symbol;
    U-W3-4). A refused fetch or read leaves R22's fallback (the per-donor recipe on V-AAL) to the reproduction step.
  3 moreau2020mutations: the local workbook copy (U-W3-1), identity at use (git blob + size, sha256 + size), §8 step 3
    (declared sheets 1_16p11.2Del and 3_22q11.2Del only; the do-not-open list) and step 4 (the MIST64 header-row search
    through the frozen guard's API); the 64 x 64 blocks saved keyed by MIST64 roi; step 6 if identifier-bearing.
  4 brainspan: identity at use of the three BrainSpan files (sha256 and size against the pre-freeze manifests: R50).
    No file content is read here.
  5 pins: the a1_builds MANIFEST and every build output the loaders read (counts, per-donor V-AAL, the R10 samples),
    re-hashed against their build records; the reference files of R22 / R10 / R47 (HGNC, GO, PANTHER 16.0, GAMBA,
    Table S4's raw list).
  6 liu_sd7 (RUN_PLAN_amend_3 R46): the registered copy (sha256 e2bd735c..., 1,442,234 B); the sheet by the name rule;
    pass 1 (position 0 only) normalised in memory (R42 (d)); pass 2 (position 0 and the ASD column); only DK-keyed
    objects are saved (never a label string); step 6 once, after pass 2.
  RUN_PLAN_amend_3: every identity and pin check (4, 5, the identity references, the Moreau clone assertion of
  section 8.1) runs FIRST (R50, B8), before any carrier or request; Moreau's whole clone is quarantined (section 8.1);
  segura_moesm2 (R47): MOESM2 pp. 38-39 under section 8's PDF rule (pdfplumber 0.11.10), read back by a second parse;
  the decoders (R45) are decided once (wp3_decoder: the size probe, up to 3 attempts across runs).
  7 the phase-2 manifest (wp3_layout.MANIFEST_NAME): every object's runner-built path, sha256, record and status; the
    loaders (real_sources.WP3Sources) read nothing else. It is never overwritten.

Every line goes through privacy_wrap.Emitter (the one print rule): counts, runner-built paths, file:line, hashes, the
fixed vocabulary. No carrier-derived string is printed or written (sheet / column / gene names stay in memory or in the
saved gene-level objects keyed by runner-side names).
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import hashlib
import io
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

from . import fetch_extract as FE
from . import identity as ID
from . import privacy_wrap as PW
from . import reparcel as RP
from . import wp3_decoder as DC
from . import wp3_genes as WG
from . import wp3_layout as L
from . import wp3_pdf as WPDF
from . import wp3_sd7 as SD7

# fix round 1 (A1): nibabel's own 'nibabel.global' StreamHandler (bound to sys.stderr at import) replaced by a
# NullHandler before any stage; inside a stage privacy_wrap.quiet_logging counts its records (import order irrelevant)
import nibabel.imageglobals as _nib_globals  # noqa: E402,F401
PW.neutralise_library_handlers("nibabel.global")

REL = "arcs/audit/src/a1_audit/wp3_material.py"
STATUS_FIRST_USE = "identity recorded at first use (no pre-freeze pin)"
STATUS_PIN_MATCH = "pin match"
STATUS_PIN_CHANGED = "pin changed"
STATUS_DECODER_COLUMNS = "refused: the decoder output's declared columns not matched (R22 fallback applies)"
STATUS_READBACK_REFUSED = "refused: the read-back could not be completed (R47 (g); section 8 handler)"
STOP_PDF_ENV = ("stopped for the operator: pdfplumber is not 0.11.10 (an environment fault; RUN_PLAN.md L14, extended "
                "by RUN_PLAN_amend_3 R47 (b))")
STATUS_STEP6_REASON = ("RUN_PLAN_amend_3 R46 (h): SD7 identifier-bearing; pass 1's extraction verified; step 6 once after "
                       "the last pass attempted")
# fix round 5: the resume of a target that crashed after section 8 step 6 (the 61b443f phase-2 KeyError)
COMPLETION_SCHEMA = "a1_wp3_completion_v1"
RESUME_STAGES = ("run", "source-md")    # where a fault after the move and the deletion request is recorded
STOP_RESUME = "stopped for the operator: a crashed step 6 cannot be completed (%s)"
RESUME_STATUS = "the record is not a stage failure after its move and deletion request"
RESUME_OBJECT = "the record's object is absent or differs from its sha256"
RESUME_IDENTITY = "the record's identity at extraction is not an identity match"
RESUME_QENTRY = "the record's quarantine entry is not the runner-built path or the identity's sha256"
RESUME_QDIR = "the carrier is absent from the quarantine"
RESUME_SOURCE = "the moved carrier is still at its source path"
RESUME_REQUEST = "the deletion request is absent or differs from the record"
RESUME_COMPLETION = "a completion record exists for another record"
RESUME_WRITE = "a write of the completion failed"
RESUME_READ = "the crashed state could not be read"
RESUME_CHECKS = (RESUME_STATUS, RESUME_OBJECT, RESUME_IDENTITY, RESUME_QENTRY, RESUME_QDIR, RESUME_SOURCE,
                 RESUME_REQUEST, RESUME_COMPLETION)
WP3_PHRASES = (
    "wp3_material wp3_material_manifest wp3 material phase manifest written objects object pins pin first use first-use schema "
    "a1_wp3_material_manifest_v1 a1_wp3_reparcel_v1 a1_wp3_decoder_v1 a1_wp3_sd7_v1 a1_wp3_identity_at_use_v1 builds "
    "build manifest_sha256 record_sha256 object_sha256 object_path record_path identity_result quarantined key keys "
    "sources source files file_key sha256_recorded status_detail run commit launch passed scratch no-launch code "
    "modules blob ungated segura moreau brainspan decoder liu sd7 SD7 pending declaration declared needs amendment "
    "frozen text TSV pinned first_use_pins ahba_builds reference references gamba hgnc go_obo go_gaf pthr16 aal_atlas "
    "aal_info dk_info brainspan_expr brainspan_rows brainspan_cols counts per-donor samples r10 primary perdonor "
    "matrix matrices change changed pin_match pin_changed R22 fallback applies refused declared columns decoder's "
    "output's matched unchanged identity_at_use loaders loader only index stage stages vocabulary V-AAL MIST64 "
    "volume rule parcels parcel kept dropped coverage rows genes mapped unmapped hgnc_mapped duplicate symbols "
    "a1_builds MANIFEST json csv gz nii xlsx extract values file_facts written_utc gate_status label labels "
    "transform liu_sd7_labels liu_sd7_values phase-2 R18 R10 R42 R43 WP3 U-W3 path_sha256 local_path",
    # fix round 1 (B2) message and record words
    "final partial adopted earlier verified nothing to do does not re-hash entries download set aside as attempt "
    "deleted supersedes decoder_attempts declared rule PROVISIONAL until RUN_PLAN_amend_3 pins it failed checks "
    "attempts_recorded transport_failures failed_stage object_problem record's absent differs preflight touches "
    "carrier touched check repro",
    # RUN_PLAN_amend_3 (WP3 fix round 2) message and record words
    "size probe content length vs pre-freeze none decided extracted unavailable fallback attempt outcome partial file "
    "accounted for never read stage stopped operator no manifest written moreau clone assertion files scanned pinned "
    "objects inside the clone other than workbook read-back pass differs not run sd7 values pass pass_no n_missing "
    "readback refusing_stage unavailable_reason attempts_recorded transport_failures record_path_last adopt_record "
    "waits_s decoder_attempts moesm2 segura_moesm2 segura_s4_raw s6 s7 transcribed check rows members_hgnc n_hgnc "
    "n_drops n_tokens n_non_gene_tokens n_genes hgnc_mapping go_id printed_row printed_order genes expected fold fdr "
    "tokens n_files_scanned n_strings n_pinned_inside_clone_other_than_workbook moreau_clone pinned_bytes "
    "column_list_sha256 column_list_label rows_beside_paper_reference paper_reference_n reading descriptive never "
    "refusal n_other_columns n_other_keys n_genes_with_more_than_one_row decoded_rows_by_t_sign t_positive t_negative "
    "t_zero_or_absent a1_wp3_decoder_attempt_v1 a1_wp3_decoder_outcome_v1 k part get made once in this run "
    "fetch:size-probe html exists failed_class where curl_exit http_status last_modified_prefreeze label across counted HTTP curl exit traces its "
    "runs block_rows registered_rows rows_reading beside registered 78 R46 (d) reported readback_failure "
    "readback_guard stdio_violations stdio_passed warnings logging read-back liu_sd7_step6 step6 where class stage "
    "PdfEnvironmentFault EnvironmentStop status_code head_failure no size returned reading url_note content_type_label "
    "html page not an stopped resumed after a crash following step 6 SOURCE.md completion record completes "
    "record_status failed_stage failed_class failed_where refusal_checks_none_held deletion_request_sha256 source_md "
    "completion_record completion_sha256 completed_from a1_wp3_completion_v1 line appended already present nothing "
    "appended absent no beside the target folder to append missing step only re-extracted moved again overwritten "
    "crash is fixed in code fix round",
    # the stage's own message templates (every literal word)
    "wp3_material: phase-2 material stage; gate ungated open; brainspan identity at use: files; a1_builds manifest "
    "sha256; builds re-hashed against their records: pass; reference sha256; liu_sd7 nothing opened; manifest "
    "written sha256; objects",
    L.STATUS_PENDING, L.STATUS_MAP_CHANGED, L.STATUS_QUARANTINE, L.STATUS_LAYOUT, L.STATUS_SD7_PENDING,
    L.STATUS_PREFLIGHT, L.STATUS_NOT_FINAL, L.STATUS_USE_UNREADABLE, L.STATUS_USE_FAILED, L.STATUS_OBJECT_CHANGED,
    STATUS_FIRST_USE, STATUS_DECODER_COLUMNS, STATUS_PIN_MATCH, STATUS_PIN_CHANGED,
    "column list as NeuroVault 9a42434e's ahba.py", "column list differs from NeuroVault 9a42434e (declared columns found)",
    "refused: the read-back differs from a second parse (R47 (g))", "not run (SD7 pass 2: pass 1 reads",
    "matched (pass 1); values:", "decoded list = HGNC genes with any row at FDR q < .05, both signs (R22; R45 (d))",
    "SD7 (declared by RUN_PLAN_amend_3 R46 (b)'s name rule)", *DC.OUTCOMES, *DC.STATUSES, *WPDF.CHECKS,
    *SD7.STATUSES, "three transport failures", STATUS_READBACK_REFUSED, STOP_PDF_ENV, STATUS_STEP6_REASON,
    FE.STATUS_STEP6, L.MOESM2_URL_NOTE, *(STOP_RESUME % c for c in (*RESUME_CHECKS, RESUME_WRITE, RESUME_READ)),
    FE.STATUS_FAILED, "resume")


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


# ================================================================================================================
# the stage's door: every file this module opens itself goes through it (quarantine refused first)
# ================================================================================================================
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
        return WG.read_pinned(self.read_bytes, path, sha, key)


def _allow(roots: L.Roots, *exact) -> PW.AllowList:
    allow = PW.AllowList(phrases=FE.FE_PHRASES + WP3_PHRASES)
    keys = (*L.SEGURA_MAP_KEY.values(), *L.SEGURA_DECODER_KEY.values(), L.MOREAU_KEY, "liu_sd7_labels",
            "liu_sd7_values", L.MOESM2_KEY)
    allow.add_words(*keys, *[f"{k}_extract" for k in keys], *[f"{k}_completion" for k in keys], L.BRAINSPAN_KEY,
                    L.AHBA_BUILDS_KEY, L.SD7_KEY, "vaal",
                    "genes", "del16p11", "del22q11", "sd7", "label", "asd", *[k for k, _ in roots.pins],
                    "primary-dk", "primary-aal", "primary-mist64", "perdonor-aal", "r10-liu-dk-samples", "counts",
                    "matrix", *[f"matrix_d{k}" for k in range(1, 7)], "py", "real_sources", "wp3_repro", "wp3_layout",
                    "wp3_genes", "reparcel", "identity", "privacy_wrap", "forms", "synthetic", "stand-ins", "mode",
                    "no", "launch", "code_hash", "passed", "commit")
    allow.add_exact(*exact)
    return allow


# ================================================================================================================
# readers (run inside fetch_extract's masked "read:file" stage; nothing prints)
# ================================================================================================================
def aal_ids(door: Door) -> list[int]:
    import pandas as pd
    info = pd.read_csv(io.BytesIO(door.pinned("aal_info")))
    ids = [int(i) for i in info["id"]]
    if len(set(ids)) != len(ids):
        raise ValueError("AAL atlas info: repeated id")
    return ids


def reparcel_object(door: Door, data: bytes, image: int) -> dict:
    """The §1.7 volume rule onto V-AAL (reparcel.volume_to_parcels; RUN_PLAN_amend_2 R43 leaves the volume rule as
    registered) for every AAL parcel of the pinned atlas info. Values of dropped parcels are null."""
    img = RP.nifti_from_bytes(data)
    atlas_path, atlas_sha = door.roots.pin("aal_atlas")
    atlas, aff = RP.load_atlas_verified(door.path(atlas_path), atlas_sha, Path(door.roots.quarantine))
    ids = aal_ids(door)
    vol = np.asarray(img.dataobj, dtype=np.float64)
    kept, vals, rep = RP.volume_to_parcels(vol, np.asarray(img.affine, float), atlas, aff, ids)
    by = {int(i): float(v) for i, v in zip(kept.tolist(), vals.tolist())}
    return {"schema": "a1_wp3_reparcel_v1", "image": int(image), "class": "V-AAL",
            "rule": "claims_register.md:1028-1034 volume -> class atlas (reparcel.volume_to_parcels)",
            "source_sha256": WG.sha256_bytes(data), "atlas_sha256": atlas_sha,
            "atlas_info_sha256": door.roots.pin("aal_info")[1], "ids": ids,
            "values": [by.get(i) for i in ids], "report": rep, "label": RP.LABEL_REPARCELLATED}


def segura_reader(door: Door, image: int):
    def read(path: Path) -> dict:
        data = door.read_bytes(path)
        return {"vaal": reparcel_object(door, data, image)}
    return read


def _q(v):
    """R45 (d): a number (int / float, not a bool) that is finite; anything else (null, a text, non-finite) is None."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    x = float(v)
    return x if math.isfinite(x) else None


def _entrez(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)) and math.isfinite(float(v)) and float(v).is_integer():
        return str(int(v))
    if isinstance(v, str) and v.strip().isdigit():
        return v.strip()
    return None


def decoder_object(data: bytes, hg: WG.HGNCTable, image: int) -> dict:
    """R45 (b)-(d), (g): NeuroVault's gene_expression_json - a JSON object with 'columns' (texts) and 'data' (rows as
    long as 'columns'), parsed by json.loads; other keys ignored and counted. Declared columns by exact text: required
    'gene_symbol' and 'p (FDR corrected)' exactly once, optional 'entrez_id.1', 't', 'p' at most once; every other column
    ignored and counted; the column list's sha256 and its label (equal to ahba.py:69-70's eight texts in order, or not)
    recorded. A row's gene: the HGNC symbol of its Entrez id when that names one approved gene (wp3_material._entrez:
    an int, an integral finite float, a text of digits), else of gene_symbol (approved -> previous -> alias); unmapped
    rows dropped and counted. A row is decoded iff its q is a finite number < .05 (both signs; t-sign counts recorded);
    a null / non-finite / non-numeric q is not decoded and is counted. Refused (ValueError, the masked read:file stage;
    the decoder is then unavailable) on a structural difference or when no row has an HGNC gene and a finite q."""
    doc = json.loads(data.decode("utf-8"))
    if not isinstance(doc, dict) or not isinstance(doc.get("columns"), list) or not isinstance(doc.get("data"), list):
        raise ValueError("decoder output: not a split-orient table")
    if not all(isinstance(c, str) for c in doc["columns"]):
        raise ValueError("decoder output: a column name that is not a text")
    cols = list(doc["columns"])
    pos = {}
    for role, text in L.DECODER_DECLARED.items():
        hits = [k for k, c in enumerate(cols) if c == text]
        if len(hits) > 1 or (role in L.DECODER_REQUIRED and len(hits) != 1):
            raise ValueError("decoder output: a declared column not found as declared")
        pos[role] = hits[0] if hits else None
    genes, t, p, q = [], [], [], []
    n_rows = n_unmapped = n_q_not_finite = 0
    how = {}
    sign = {"t_positive": 0, "t_negative": 0, "t_zero_or_absent": 0}
    for row in doc["data"]:
        if not isinstance(row, list) or len(row) != len(cols):
            raise ValueError("decoder output: a row of another length")
        n_rows += 1
        sym = row[pos["symbol"]]
        ent = _entrez(row[pos["entrez"]]) if pos["entrez"] is not None else None
        g, h = hg.resolve("entrez" if ent else None, ent, sym if isinstance(sym, str) else None)
        h = h.split(" (")[0]
        how[h] = how.get(h, 0) + 1
        tv = _q(row[pos["t"]]) if pos["t"] is not None else None
        pv = _q(row[pos["p"]]) if pos["p"] is not None else None
        qv = _q(row[pos["q"]])
        if g is None:
            n_unmapped += 1
            continue
        if qv is None:
            n_q_not_finite += 1
            continue
        genes.append(g)
        t.append(tv)
        p.append(pv)
        q.append(qv)
        if qv < L.DECODER_Q:
            sign["t_positive" if (tv or 0) > 0 else "t_negative" if (tv or 0) < 0 else "t_zero_or_absent"] += 1
    if not genes:
        raise ValueError("decoder output: no row with an HGNC gene and a finite q")
    multi = {}
    for g in genes:
        multi[g] = multi.get(g, 0) + 1
    col_sha = hashlib.sha256(json.dumps(cols, ensure_ascii=True, separators=(",", ":")).encode("ascii")).hexdigest()
    label = (DECODER_COLUMNS_SAME if cols == list(L.DECODER_COLUMNS) else DECODER_COLUMNS_DIFFER)
    return {"schema": "a1_wp3_decoder_v1", "image": int(image), "mask": "full", "genes": genes, "t": t, "p": p, "q": q,
            "counts": {"n_rows": n_rows, "n_kept": len(genes), "n_unmapped": n_unmapped,
                       "n_nonfinite_q": n_q_not_finite, "n_rows_sharing_an_hgnc_symbol": len(genes) - len(multi),
                       "n_genes_with_more_than_one_row": sum(1 for v in multi.values() if v > 1),
                       "decoded_rows_by_t_sign": sign, "hgnc_mapping": dict(sorted(how.items())),
                       "n_other_columns": sum(1 for c in cols if c not in L.DECODER_DECLARED.values()),
                       "n_other_keys": sum(1 for k in doc if k not in ("columns", "data"))},
            "rows_beside_paper_reference": {"n_rows": n_rows, "paper_reference_n": 20787,
                                            "reading": "descriptive (R45 (g)); never a refusal"},
            "optional_columns_present": sorted(r for r in ("entrez", "t", "p") if pos[r] is not None),
            "column_list_sha256": col_sha, "column_list_label": label,
            "declared_columns": "wp3_layout.DECODER_DECLARED (NeuroVault ahba.py at %s)" % L.DECODER_SOURCE["commit"],
            "rule": "decoded list = HGNC genes with any row at FDR q < .05, both signs (R22; R45 (d))"}


DECODER_COLUMNS_SAME = "column list as NeuroVault 9a42434e's ahba.py"
DECODER_COLUMNS_DIFFER = "column list differs from NeuroVault 9a42434e (declared columns found)"
STATUS_READBACK = "refused: the read-back differs from a second parse (R47 (g))"
STATUS_SD7_VALUES_SKIPPED = "not run (SD7 pass 2: pass 1 reads %s)"
REFERENCE_KEYS = ("hgnc", "go_obo", "go_gaf", "pthr16", "gamba", "aal_atlas", "aal_info", "dk_info", "segura_s4_raw")


def decoder_reader(door: Door, image: int, hg_cache: dict):
    def read(path: Path) -> dict:
        if "hg" not in hg_cache:
            hg_cache["hg"] = WG.HGNCTable(door.pinned("hgnc"))
        return {"genes": decoder_object(door.read_bytes(path), hg_cache["hg"], image)}
    return read


# ---- SD7 (RUN_PLAN_amend_3 R46: declared by rule; the code path runs on the registered copy) -------------------
def sd7_label_transform(dk):
    """Pass 1 (R10 :657-658, R42 (d), R46 (e)): position 0 of the block (the only position the wrapper hands over),
    normalised in memory (forms.sd7_normalise); saved: the normalised record (positions, kinds, DK ids, counts, merged /
    pooled) or its fail-closed status with the counts - never a label string."""
    from . import forms as FM

    def tf(objects: dict) -> dict:
        view = objects["sd7"]
        labels = view.column(0)
        try:
            rec = FM.sd7_normalise(labels, dk)
            out = {k: v for k, v in rec.items() if k != "rule"}
            out["status"] = "matched"
        except FM.FormNotTestable as e:
            out = {"status": e.status, "counts": dict(e.detail)}
        return {"sd7": dict(out, schema="a1_wp3_sd7_v1", n_labels=len(labels), pass_no=1)}
    return tf


def sd7_value_transform(dk, labels_record: dict):
    """Pass 2 (R46 (f)): position 0 again (its normalisation asserted equal to pass 1's) and the ASD column (values or
    None for a missing token, as the wrapper read them); saved: the values keyed by position, never a label string."""
    from . import forms as FM

    def tf(objects: dict) -> dict:
        view = objects["sd7"]
        labels = view.column(0)
        rec = FM.sd7_normalise(labels, dk)
        if rec["entries"] != labels_record["entries"] or bool(rec["merged"]) != bool(labels_record["merged"]):
            raise AssertionError("SD7: the label column normalises differently on the second read")
        vals = view.column(view.handed[1])
        return {"sd7": {"schema": "a1_wp3_sd7_v1", "values_by_position": list(vals), "n_labels": len(labels),
                        "n_missing": sum(1 for v in vals if v is None), "pass_no": 2}}
    return tf


# ================================================================================================================
# targets
# ================================================================================================================
def targets(roots: L.Roots, idrefs: dict) -> dict:
    """The fetch_extract targets of the local carriers and the decoders, keyed by object key. R44: the three source
    carriers are used as found at their pinned paths (FE15); no GET is made for any of them."""
    out = {}
    for image in L.SEGURA_IMAGES:
        k = L.SEGURA_MAP_KEY[image]
        r = idrefs[k]
        out[k] = FE.Target(key=k, gate="ungated", url=r["url"], kind="file", ext=".nii.gz", refs=tuple(r["refs"]),
                           local_path=r["local_path"])
        kd = L.SEGURA_DECODER_KEY[image]
        out[kd] = FE.Target(key=kd, gate="ungated", url=L.DECODER_URL.format(image=image), kind="file", ext=".json",
                            identity_at_download=True, refusal_status=STATUS_DECODER_COLUMNS,
                            head_before_get=False)            # R45 (a): one curl, a GET (fix round 3, C (a))
    r = idrefs[L.MOREAU_KEY]
    out[L.MOREAU_KEY] = dataclasses.replace(FE.moreau_target(r["url"], tuple(r["refs"]), key=L.MOREAU_KEY),
                                            local_path=r["local_path"], quarantine_dir=str(roots.moreau_clone),
                                            deletion_extra=tuple(L.MOREAU_DELETION_REQUEST.items()))
    path, sha = roots.pin("segura_moesm2")
    out[L.MOESM2_KEY] = FE.Target(key=L.MOESM2_KEY, gate="ungated", url=L.MOESM2_URL, kind="file", ext=".pdf",
                                  pinned_sha256=sha, pinned_bytes=roots.pin_bytes("segura_moesm2"),
                                  local_path=str(path), url_note=L.MOESM2_URL_NOTE)
    return out


def sd7_targets(roots: L.Roots, dk_names: tuple) -> tuple:
    """R46's two passes on the registered copy (roots.sd7_copy: path, sha256, bytes, url): the sheet by the name rule
    (exactly one match), the header row by the ASD-anchored column rule through the guard; pass 1 hands position 0
    only and defers step 6; pass 2 reads position 0 and the ASD column, and runs step 6 once."""
    from . import wp3_sd7 as SD
    path, sha, nbytes, url = roots.sd7_copy
    common = dict(gate="ungated", url=url, kind="workbook", ext=".xlsx", pinned_bytes=nbytes, pinned_sha256=sha,
                  local_path=str(path))

    def decl(p):
        return FE.SheetDecl(key="sd7", name="SD7 (declared by RUN_PLAN_amend_3 R46 (b)'s name rule)", mode="sd7",
                            vocab=tuple(dk_names), name_rule=SD.SHEET_RULE.pattern, name_status=SD.SD7_SHEET,
                            sd7_pass=p)
    lab = FE.Target(key="liu_sd7_labels", sheets=(decl(1),), defer_quarantine=True, **common)
    val = FE.Target(key="liu_sd7_values", sheets=(decl(2),), **common)
    return lab, val


def moesm2_inputs(roots: L.Roots, door: Door) -> dict:
    """R47's inputs besides the PDF: SEGURA_S7_TERMS.json (frozen), the 7 named rows' TSV values, Table S4's raw list
    (the S-build's pinned input; the runner-side vocabulary of Table S6) and the HGNC table."""
    from . import loader as LD
    from . import wp3_pdf as WPDF
    terms = json.loads(door.read_bytes(Path(roots.repo) / "arcs/audit/register_sets/SEGURA_S7_TERMS.json")
                       .decode("utf-8"))["terms"]
    data = LD.lf(door.read_bytes(Path(roots.repo) / LD.TSV_PATH))
    if hashlib.sha256(data).hexdigest() != LD.TSV_SHA256:
        raise AssertionError("the TSV differs from its L2 pin")
    _, rows = LD.parse_tsv_bytes(data)
    named_cells = {t["cell_id"] for t in terms if str(t.get("named", "")).startswith("named")}
    tsv = {}
    for r in rows:
        if r["cell_id"] in named_cells:
            tsv[r["cell_id"]] = r["published_value_and_location"]
    s4_raw = {ln.strip() for ln in door.pinned("segura_s4_raw").decode("utf-8").splitlines() if ln.strip()}
    return dict(terms=terms, tsv_named=WPDF.tsv_named_values(tsv, terms), s4_raw=s4_raw,
                hg=WG.HGNCTable(door.pinned("hgnc")))


def moesm2_reader(door: Door, inputs: dict):
    from . import wp3_pdf as WPDF

    def read(path: Path) -> dict:
        WPDF.assert_pdfplumber()                         # L14, extended: asserted before any parse
        return WPDF.parse(door.path(path), **inputs)
    return read


# ================================================================================================================
# identity at use of the BrainSpan files; pins of the builds and reference files
# ================================================================================================================
def file_identity(door: Door, key: str) -> dict:
    """R50: a pinned file's sha256 (and size, when pinned) against its pin; a file without a pin reads
    STATUS_FIRST_USE (none of the stage's files since RUN_PLAN_amend_3: every one is pinned)."""
    path, sha = door.roots.pin(key)
    nbytes = door.roots.pin_bytes(key)
    facts = ID.file_facts(door.path(path), quarantine_root=Path(door.roots.quarantine))
    if sha is None:
        result = STATUS_FIRST_USE
    else:
        ok = facts["sha256"] == sha and (nbytes is None or facts["bytes"] == nbytes)
        result = STATUS_PIN_MATCH if ok else STATUS_PIN_CHANGED
    return {"pin": key, "path": Path(path).as_posix(), "bytes": facts["bytes"], "sha256": facts["sha256"],
            "pinned_sha256": sha, "pinned_bytes": nbytes, "result": result}


def builds_pins(door: Door) -> dict:
    """The a1_builds outputs the loaders read, re-hashed against their build records (WP2), and the MANIFEST's sha256
    (its record_sha256 per build asserted)."""
    from . import real_sources as RS
    b = Path(door.roots.builds)
    man_bytes = door.read_bytes(b / "MANIFEST.json")
    man = json.loads(man_bytes.decode("utf-8"))
    out = {"manifest_sha256": WG.sha256_bytes(man_bytes), "builds": {}}
    for name in RS.BUILDS_READ:
        rp = b / name / "build_record.json"
        rb = door.read_bytes(rp)
        if WG.sha256_bytes(rb) != man["builds"][name]["record_sha256"]:
            raise AssertionError("a build record differs from the a1_builds MANIFEST")
        rec = json.loads(rb.decode("utf-8"))
        files = {}
        for o in rec["outputs"]:
            if o.get("role") not in RS.BUILDS_READ[name]:
                continue
            h = ID.file_facts(door.path(b / name / o["file"]), quarantine_root=Path(door.roots.quarantine))["sha256"]
            if h != o["sha256"]:
                raise AssertionError("a build output differs from its build record")
            files[RS.build_file_key(o)] = h
        out["builds"][name] = {"record_sha256": WG.sha256_bytes(rb), "files": files}
    return out


# ================================================================================================================
# the stage (fix round 1, B2; RUN_PLAN_amend_3 R44-R50 and section 8.1)
# ================================================================================================================
class PreflightRefused(Exception):
    """A check that touches no carrier failed: the stage stops before any carrier is touched or any request is made."""


def _rel(p: Path, root: str) -> str:
    return Path(p).resolve().relative_to(Path(root).resolve()).as_posix()


def _entry_from_record(roots: L.Roots, rp: Path, rec: dict, rb: bytes) -> dict:
    """A manifest entry from an R18 record (read back): its status, identity result, quarantine and object."""
    e = {"status": rec.get("status"), "record_path": _rel(rp, roots.records), "record_sha256": WG.sha256_bytes(rb),
         "identity_result": ((rec.get("identity") or {}).get("comparison") or {}).get("result"),
         "identifier_bearing": rec.get("identifier_bearing"),
         "quarantined": bool((rec.get("quarantine") or {}).get("quarantined")),
         "failed_stage": rec.get("failed_stage")}
    ex = rec.get("extraction") or {}
    if ex.get("object_path"):
        op = Path(ex["object_path"])
        try:
            rel = _rel(op, roots.artifacts)
        except ValueError:                          # fix round 5: an object outside the artifacts root is a problem,
            rel = None                              # not an exception that names a path
        if rel is None or not op.exists() or WG.sha256_bytes(op.read_bytes()) != ex["object_sha256"]:
            e["object_problem"] = "the record's object is absent or differs from it"
        else:
            e.update(object_path=rel, object_sha256=ex["object_sha256"])
    return e


def _entry(roots: L.Roots, res: dict) -> dict:
    """A manifest entry from a fetch_extract result and the R18 record it wrote (read back)."""
    rp = res.get("record_path")
    if not rp:
        return {"status": res["status"]}
    rb = Path(rp).read_bytes()
    e = _entry_from_record(roots, Path(rp), json.loads(rb.decode("utf-8")), rb)
    if e.get("object_problem"):
        raise AssertionError("an object differs from its record on read-back")
    return e


def records_of(roots: L.Roots, key: str) -> list:
    """Every R18 record of a key (<key>.json, <key>.<n>.json; fetch_extract FE9 numbering), in attempt order:
    [(path, record dict, bytes)]."""
    d = Path(roots.records) / L.GATE
    found = []
    if d.is_dir():
        for p in d.glob(f"{key}*.json"):
            stem = p.name[:-len(".json")]
            if stem == key:
                found.append((1, p))
            elif stem.startswith(key + ".") and stem[len(key) + 1:].isdigit():
                found.append((int(stem[len(key) + 1:]), p))
    out = []
    for _, p in sorted(found):
        b = p.read_bytes()
        out.append((p, json.loads(b.decode("utf-8")), b))
    return out


DETERMINISTIC_STAGES = ("sheets:do-not-open", "sheets:open", "sheets:names", "sheets:access", "sheets:classify",
                        "read:declared-columns", "read:numeric-columns", "read:header-search", "read:moreau-layout",
                        "read:sd7-block", "read:sd7-values", "sheets:access-log", "read:file", "transform",
                        "transform:positions")


def target_state(roots: L.Roots, key: str) -> dict:
    """The state of one local-carrier target from its records (the source of truth, B2 (2)): done (an extracted record
    whose object re-hashes to it - a quarantined carrier included), final (done, or a final refusal: an identity
    mismatch or a refusal at a stage that re-reading the same bytes would repeat) and the entry the manifest carries.
    The decoders are decided by wp3_decoder (R45 (f))."""
    recs = records_of(roots, key)
    for p, r, b in reversed(recs):
        e = _entry_from_record(roots, p, r, b)
        if r.get("status") == FE.STATUS_EXTRACTED and "object_path" in e:
            e.update(final=True, attempts_recorded=len(recs))
            return dict(done=True, final=True, entry=e)
    if not recs:
        return dict(done=False, final=False, entry=None)
    done = _completed_entry(roots, key, recs)               # fix round 5: a crashed step 6 completed by resume
    if done is not None:
        return dict(done=True, final=True, entry=done)
    p, r, b = recs[-1]
    e = _entry_from_record(roots, p, r, b)
    final = r.get("status") == ID.STATUS_CHANGED or r.get("failed_stage") in DETERMINISTIC_STAGES
    if r.get("failed_class") == "PdfEnvironmentFault":       # an environment fault is never final (C (c))
        final = False
    if r.get("status") == FE.STATUS_STEP6:                     # FE24: step 6 done
        final = True
    e.update(final=bool(final), attempts_recorded=len(recs))
    return dict(done=False, final=bool(final), entry=e)


def _file_identity_record(roots: L.Roots, door: Door, em: PW.Emitter, allow, recs: list) -> dict:
    """The BrainSpan identity-at-use record (R18 format): adopted when an earlier record carries the same files and
    result (B2 (2)), else written under the next free name (never overwritten)."""
    ok = all(r["result"] == STATUS_PIN_MATCH for r in recs)
    result = ID.STATUS_MATCH if ok else L.STATUS_MAP_CHANGED
    files = {r["pin"]: r["sha256"] for r in recs}
    for p, r, b in reversed(records_of(roots, L.BRAINSPAN_KEY)):
        if r.get("result") == result and {x["pin"]: x["sha256"] for x in r.get("files", [])} == files:
            return {"status": result, "record_path": _rel(p, roots.records), "record_sha256": WG.sha256_bytes(b),
                    "files": files, "final": True, "adopted": True}
    rec = {"schema": "a1_wp3_identity_at_use_v1", "key": L.BRAINSPAN_KEY, "gate": L.GATE, "date_utc": utc_now(),
           "files": recs, "result": result}
    for r in recs:
        allow.add_exact(r["path"])
    rp = FE._record_path(roots.fe_roots(), FE.Target(key=L.BRAINSPAN_KEY, gate=L.GATE, url="https://none.invalid",
                                                     kind="file", ext=".csv"))
    allow.add_exact(rp)
    sha = PW.stage(em, "record", em.write_json, rp, rec, "identity")
    return {"status": result, "record_path": _rel(rp, roots.records), "record_sha256": sha, "files": files,
            "final": True}


# ---- section 8.1 (decision 1): no other pinned object inside the Moreau clone ---------------------------------------
def _strings(o, out: list) -> None:
    if isinstance(o, str):
        out.append(o)
    elif isinstance(o, dict):
        for v in o.values():
            _strings(v, out)
    elif isinstance(o, (list, tuple)):
        for v in o:
            _strings(v, out)


def _norm_path_text(s: str) -> str:
    return s.replace("/", "\\").casefold()


def clone_assertion(roots: L.Roots, door: Door) -> dict:
    """Before any carrier (with R50's checks): no pinned object other than the workbook lies inside the Moreau clone
    directory. Pinned objects: every path of the identity references (IDENTITY_prefreeze.json), of register_sets'
    MANIFEST.json and set files, of the S-build's code (src_register/s_build.py, as text) and of wp3_layout's pins.
    Counts only; a hit stops the stage (PreflightRefused) and the orchestrator decides."""
    clone = _norm_path_text(str(Path(roots.moreau_clone))).rstrip("\\") + "\\"
    workbook = _norm_path_text(str(Path(L.identity_records(roots, door.read_bytes)[L.MOREAU_KEY]["local_path"])))
    texts: list = []
    _strings(json.loads(door.read_bytes(Path(roots.identity_json)).decode("utf-8")), texts)
    rs = Path(roots.repo) / "arcs/audit/register_sets"
    n_files = 1
    for p in sorted(rs.glob("*.json")):
        _strings(json.loads(door.read_bytes(p).decode("utf-8")), texts)
        n_files += 1
    texts.append(door.read_bytes(Path(roots.repo) / "arcs/audit/src_register/s_build.py").decode("utf-8"))
    n_files += 1
    for k, _ in roots.pins:
        texts.append(str(roots.pin(k)[0]))
    hits = 0
    for t in texts:
        low = _norm_path_text(t)
        start = 0
        while True:
            i = low.find(clone, start)
            if i < 0:
                break
            j = i + len(clone)
            while j < len(low) and low[j] not in "\"'\n\r\t,;)]}" and not low.startswith(" ", j):
                j += 1
            if low[i:j] != workbook:
                hits += 1
            start = j
    if not workbook.startswith(clone):
        hits += 1                                   # the workbook itself must lie inside the declared clone
    return {"n_files_scanned": n_files, "n_strings": len(texts), "n_pinned_inside_clone_other_than_workbook": hits}


def preflight(roots: L.Roots, door: Door, em: PW.Emitter, allow) -> dict:
    """R50 (B8) and section 8.1 decision 1: every identity and pin check, before any carrier is touched or any network
    request is made - the identity references (IDENTITY_prefreeze.json's sha256), all three BrainSpan files (sha256 and
    size), the a1_builds chain, the reference files (HGNC, GO obo / GAF, PANTHER 16.0, GAMBA, the AAL atlas and info,
    the DK info, Table S4's raw list), the Moreau clone assertion. Any failure -> PreflightRefused (no manifest)."""
    failed = []
    try:
        idrefs = PW.stage(em, "identity", L.identity_records, roots, door.read_bytes)
    except PW.StageFailed:
        raise PreflightRefused() from None
    try:
        bs = PW.stage(em, "identity", lambda: [file_identity(door, k) for k in
                                               ("brainspan_expr", "brainspan_rows", "brainspan_cols")])
    except PW.StageFailed:
        raise PreflightRefused() from None
    failed += [r["pin"] for r in bs if r["result"] != STATUS_PIN_MATCH]
    try:
        builds = PW.stage(em, "identity", builds_pins, door)
    except PW.StageFailed:
        raise PreflightRefused() from None
    em.say(f"wp3_material: a1_builds manifest sha256 {builds['manifest_sha256']}; builds {len(builds['builds'])} "
           f"re-hashed against their records: pass")
    refs = {}
    for k in REFERENCE_KEYS:
        try:
            r = PW.stage(em, "identity", file_identity, door, k)
        except PW.StageFailed:
            failed.append(k)
            continue
        allow.add_exact(r["path"])
        refs[k] = {"sha256": r["sha256"], "bytes": r["bytes"], "result": r["result"]}
        em.say(f"wp3_material: reference {k} sha256 {r['sha256']}: {r['result']}")
        if r["result"] != STATUS_PIN_MATCH:
            failed.append(k)
    try:
        ca = PW.stage(em, "identity", clone_assertion, roots, door)
        em.say(f"wp3_material: moreau clone assertion: files scanned {ca['n_files_scanned']}; pinned objects inside "
               f"the clone other than the workbook {ca['n_pinned_inside_clone_other_than_workbook']}")
        if ca["n_pinned_inside_clone_other_than_workbook"]:
            failed.append("moreau_clone")
    except PW.StageFailed:
        failed.append("moreau_clone")
        ca = None
    if failed:
        em.say(f"wp3_material: {L.STATUS_PREFLIGHT}; failed checks {len(failed)}: {', '.join(failed)}")
        raise PreflightRefused()
    return {"idrefs": idrefs, "brainspan": bs, "pins": {L.AHBA_BUILDS_KEY: builds, "references": refs,
                                                        "moreau_clone": ca}}


def _verify_manifest(roots: L.Roots, path: Path) -> dict:
    """An existing final manifest: every entry's record and object re-hashed against it."""
    b = path.read_bytes()
    man = json.loads(b.decode("utf-8"))
    bad = 0
    for k, e in man["objects"].items():
        if e.get("record_path"):
            rp = Path(roots.records) / e["record_path"]
            bad += (not rp.exists()) or WG.sha256_bytes(rp.read_bytes()) != e["record_sha256"]
        if e.get("object_path"):
            op = Path(roots.artifacts) / e["object_path"]
            bad += (not op.exists()) or WG.sha256_bytes(op.read_bytes()) != e["object_sha256"]
        if e.get("completion_record"):              # fix round 5: the resume's second record
            cp = Path(roots.records) / e["completion_record"]
            bad += (not cp.exists()) or WG.sha256_bytes(cp.read_bytes()) != e.get("completion_sha256")
    return {"manifest": man, "sha256": WG.sha256_bytes(b), "n_bad": int(bad)}


CARRIER_KEYS = (*L.SEGURA_MAP_KEY.values(), *L.SEGURA_DECODER_KEY.values(), L.MOREAU_KEY, L.MOESM2_KEY,
                "liu_sd7_labels", "liu_sd7_values")


# ---- fix round 5: the RESUME of a target that crashed after its step 6 (RUN_PLAN section 17) -----------------------
class ResumeRefused(Exception):
    """An inconsistent crashed state: the stage stops for the operator (.check: one of RESUME_CHECKS)."""

    def __init__(self, check: str):
        super().__init__(check)
        self.check = check


def completion_path(roots: L.Roots, key: str) -> Path:
    return Path(roots.records) / L.GATE / f"{key}_completion.json"


def crashed_after_step6(rec: dict) -> bool:
    """A record that is not 'extracted' although its extraction object was saved, its carrier moved and its deletion
    request written (the 61b443f crash: a fault after section 8 step 6's move and request). Such a target is never run
    again: it is resumed (resumable) or the stage stops for the operator."""
    q = rec.get("quarantine") or {}
    return (rec.get("status") != FE.STATUS_EXTRACTED and bool(q.get("quarantined")) and bool(q.get("deletion_request"))
            and bool((rec.get("extraction") or {}).get("object_path")))


def resumable(rec: dict) -> bool:
    """The exact crashed state the resume completes: a stage failure ('refused (stage failed)') at the run or source-md
    stage - never an incident, an identity result or any other status."""
    return (crashed_after_step6(rec) and rec.get("status") == FE.STATUS_FAILED
            and rec.get("failed_stage") in RESUME_STAGES)


def _completed_entry(roots: L.Roots, key: str, recs: list) -> dict | None:
    """The manifest entry of a crashed target whose completion record names its latest record (sha256): 'extracted',
    final, the completion record beside the crashed one."""
    cp = completion_path(roots, key)
    if not cp.exists():
        return None
    cb = cp.read_bytes()
    try:
        comp = json.loads(cb.decode("utf-8"))
    except ValueError:                              # not a completion record: the resume stops on it
        return None
    p, r, b = recs[-1]
    if not isinstance(comp, dict) or comp.get("schema") != COMPLETION_SCHEMA or \
            comp.get("status") != FE.STATUS_EXTRACTED or \
            (comp.get("completes") or {}).get("record_sha256") != WG.sha256_bytes(b):
        return None
    e = _entry_from_record(roots, p, r, b)
    if "object_path" not in e or e.get("object_problem") or not resumable(r):
        return None
    e.update(status=FE.STATUS_EXTRACTED, final=True, attempts_recorded=len(recs),
             completion_record=_rel(cp, roots.records), completion_sha256=WG.sha256_bytes(cb),
             completed_from=r.get("status"))
    return e


def _resume_checks(roots: L.Roots, key: str, target, rec: dict) -> dict:
    """Every check before anything is completed (refusal: ResumeRefused; the quarantine is never opened - only the
    existence of the runner-built quarantine path is stated, and identity is held to the phase-2 record and the object's
    sha256, U-W3-18)."""
    ex = rec["extraction"]
    op = Path(ex["object_path"])
    try:
        inside = op.resolve().is_relative_to(Path(roots.artifacts).resolve())
    except OSError:
        inside = False
    if not inside or not op.is_file() or WG.sha256_bytes(op.read_bytes()) != ex.get("object_sha256"):
        raise ResumeRefused(RESUME_OBJECT)
    ident = rec.get("identity") or {}
    if (ident.get("comparison") or {}).get("result") != ID.STATUS_MATCH:
        raise ResumeRefused(RESUME_IDENTITY)
    sha_id = (ident.get("facts") or {}).get("sha256")
    q = rec["quarantine"]
    moved = q["quarantined"]
    qdir = Path(roots.quarantine) / L.GATE / key
    whole = target.quarantine_dir is not None
    expect = qdir if whole else qdir / f"carrier{target.ext}"
    if len(moved) != 1 or moved[0].get("moved_to") != expect.as_posix() or \
            moved[0].get("carrier_sha256" if whole else "sha256") != sha_id or sha_id is None:
        raise ResumeRefused(RESUME_QENTRY)
    if not (expect.is_dir() if whole else expect.is_file()):        # a stat of the runner-built path only
        raise ResumeRefused(RESUME_QDIR)
    if Path(target.quarantine_dir if whole else target.local_path).exists():
        raise ResumeRefused(RESUME_SOURCE)
    rq = Path(roots.control) / L.GATE / f"{key}_deletion_request.json"
    if q.get("deletion_request") != rq.as_posix() or not rq.is_file():
        raise ResumeRefused(RESUME_REQUEST)
    qb = rq.read_bytes()
    req = json.loads(qb.decode("utf-8"))
    if req.get("schema") != "a1_deletion_request_v1" or req.get("key") != key or req.get("gate") != L.GATE or \
            req.get("files") != moved or any(req.get(k) != v for k, v in target.deletion_extra):
        raise ResumeRefused(RESUME_REQUEST)
    return {"moved": moved, "object_sha256": ex["object_sha256"], "deletion_request_sha256": WG.sha256_bytes(qb)}


def _resume(roots: L.Roots, em: PW.Emitter, key: str, target, recs: list) -> dict:
    """Complete ONLY the missing step of a target that crashed after its step 6 (the SOURCE.md line), then write a
    SECOND record, <key>_completion.json, that target_state reads to mark the entry final 'extracted'. Nothing is
    re-extracted, nothing is moved again, no record is overwritten (FE9); any inconsistency stops the stage."""
    p, rec, rb = recs[-1]
    if not resumable(rec):
        raise ResumeRefused(RESUME_STATUS)
    cp = completion_path(roots, key)
    if cp.exists():                                    # names another record (else target_state had adopted it)
        raise ResumeRefused(RESUME_COMPLETION)
    def checks():                                       # a refusal is returned; any other fault is the stage's
        try:
            return _resume_checks(roots, key, target, rec)
        except ResumeRefused as e:
            return e
    try:
        facts = PW.stage(em, "resume", checks)          # section 8's handler: class, stage, code line only
    except PW.StageFailed:
        raise ResumeRefused(RESUME_READ) from None
    if isinstance(facts, ResumeRefused):
        raise facts
    try:
        return _complete(roots, em, key, p, rec, rb, cp, facts)
    except PW.StageFailed:                             # the stage line (class, stage, code line) is already said
        raise ResumeRefused(RESUME_WRITE) from None


def _complete(roots, em, key, p, rec, rb, cp, facts) -> dict:
    for m in facts["moved"]:                           # runner-built paths only (checked equal in _resume_checks)
        em.allow.add_exact(m["moved_to"])
    em.allow.add_exact(_rel(p, roots.records), rec["quarantine"]["deletion_request"])
    src = Path(roots.data) / key / "SOURCE.md"
    state = "absent (no SOURCE.md beside the target folder; nothing to append)"
    if src.exists():
        em.allow.add_exact(src)
        marker = FE.source_md_quarantine_line(facts["moved"][0], "\x00").split(" (\x00)")[0]

        def append():
            text = src.read_text(encoding="utf-8", errors="replace")      # in memory only: is this move's line there?
            if marker in text:
                return "already present (nothing appended)"
            em.write_text(src, FE.source_md_quarantine_lines(facts["moved"], utc_now()), "identity", True)
            return "line appended"
        state, _ = PW.guarded_stage(em, "source-md", append, out=em.stream)
    comp = {"schema": COMPLETION_SCHEMA, "key": key, "gate": L.GATE, "date_utc": utc_now(),
            "status": FE.STATUS_EXTRACTED,
            "completes": {"record_path": _rel(p, roots.records), "record_sha256": WG.sha256_bytes(rb),
                          "record_status": rec.get("status"), "failed_stage": rec.get("failed_stage"),
                          "failed_class": rec.get("failed_class"), "failed_where": rec.get("failed_where")},
            "refusal_checks_none_held": list(RESUME_CHECKS), "object_sha256": facts["object_sha256"],
            "quarantine": facts["moved"], "deletion_request_sha256": facts["deletion_request_sha256"],
            "source_md": state,
            "rule": "WP3 fix round 5 (RUN_PLAN section 17: a crash is fixed in code): the missing step only; nothing "
                    "re-extracted, nothing moved again, no record overwritten"}
    em.allow.add_exact(cp, cp.name)
    PW.stage(em, "record", em.write_json, cp, comp, "identity")
    em.say(f"wp3_material: {key} resumed after a crash following step 6: SOURCE.md {state}; completion record {cp}")
    st = target_state(roots, key)                      # the writer reads back what it wrote: the entry from the records
    if not st["done"] or st["entry"].get("completion_record") != _rel(cp, roots.records):
        raise ResumeRefused(RESUME_WRITE)
    return st["entry"]


def _local_target(roots, em, out, key, target, reader=None, transform=None, want=lambda k: True) -> dict:
    """One local-carrier target: adopted when an earlier run finished it (B2 (2)), resumed when it crashed after its
    step 6 (fix round 5), else run once."""
    st = target_state(roots, key)
    if st["done"] or st["final"]:
        em.say(f"wp3_material: {key} final in an earlier run (adopted): status {st['entry']['status']}")
        return st["entry"]
    if not want(key):
        return {"status": L.STATUS_PENDING, "final": False}
    recs = records_of(roots, key)
    if recs and crashed_after_step6(recs[-1][1]):     # moved and requested: resumed, or a stop - never run again
        return _resume(roots, em, key, target, recs)
    FE.run_target(target, roots.fe_roots(), out=out, reader=reader, transform=transform, adopt_identical=True)
    st = target_state(roots, key)
    return st["entry"] if st["entry"] is not None else {"status": L.STATUS_PENDING, "final": False}


class EnvironmentStop(Exception):
    """pdfplumber is not 0.11.10 (fix round 3, C (c)): the stage stops for the operator; no final record."""


def _moesm2_readback(roots: L.Roots, door: Door, em: PW.Emitter, entry: dict, inputs: dict) -> dict:
    """R47 (g): a second parse of the pinned copy equals the stored object read back from disk. Fix round 3 (A1): the
    second parse runs inside the guards fetch_extract.run_target uses (privacy_wrap.guarded_stage: section 8's
    handler, the stdio guard, quiet warnings, quiet logging with a library's own handler); a failure reads 'refused'
    (final; recorded by stage, class and line only), so the stage always finishes."""
    if entry.get("status") != FE.STATUS_EXTRACTED or "object_path" not in entry:
        return entry
    stored = json.loads(door.read_bytes(Path(roots.artifacts) / entry["object_path"]).decode("utf-8"))["objects"]
    path, _ = roots.pin("segura_moesm2")
    try:
        ok, counts = PW.guarded_stage(em, "read-back", WPDF.readback, door.path(path), stored, out=em.stream,
                                      **inputs)
    except PW.PrintRuleViolation:              # fix round 4, item 3: exactly as run_target reads an incident
        return dict(entry, readback="stopped", status=FE.STATUS_INCIDENT, final=False)
    except PW.StageFailed as e:
        if e.class_name == "PdfEnvironmentFault":
            raise EnvironmentStop() from None
        if e.class_name == "StdioViolation":   # a library line off the allow-list inside the read-back
            return dict(entry, readback="stopped", status=FE.STATUS_INCIDENT, final=False,
                        readback_failure={"stage": e.stage, "class": e.class_name, "where": e.where})
        return dict(entry, readback="refused", status=STATUS_READBACK_REFUSED, final=True,
                    readback_failure={"stage": e.stage, "class": e.class_name, "where": e.where})
    return dict(entry, readback="pass" if ok else "differs", readback_guard=counts)


def run_material(roots: L.Roots, *, only=None, out=None, run_info: dict | None = None) -> dict:
    """Phase 2's material stage on `roots` (production, or a scratch layout in tests):
    (0) a final manifest exists -> it is verified and nothing else is done;
    (1) the preflight (R50, section 8.1): every identity and pin check; a failure stops the stage before any carrier is
        touched or any request is made, and no manifest is written;
    (2) the local carriers (R44: the Segura NIfTIs, Moreau's workbook - whole-clone quarantine, section 8.1; R47:
        MOESM2; R46: SD7's two passes), each adopted when an earlier run finished it (B2 (2)), or resumed when it
        crashed after section 8 step 6's move and deletion request (fix round 5: only the missing SOURCE.md line, then
        a completion record; any inconsistency stops the stage for the operator, no manifest);
    (3) the decoders (R45: the size probe, the attempts, decided once; wp3_decoder); a crash trace or a local fault
        stops the stage (no manifest);
    (4) the final manifest only when every target is final; else a partial manifest (never read by the loaders);
        `only` is for scratch layouts. Never overwrites a record, object or manifest; never deletes."""
    from . import wp3_decoder as DC
    if only and roots.identity_frozen:
        raise ValueError("only: a subset run is for scratch layouts (fix round 1, B2 (4))")
    door = Door(roots)
    allow = _allow(roots, roots.manifest_path, roots.record_path(L.BRAINSPAN_KEY))
    for p in roots.partial_manifests():
        allow.add_exact(p)
    em = PW.Emitter(allow, stream=out, log_path=Path(roots.logs) / L.GATE / "wp3_material.log")
    em.say("wp3_material: phase-2 material stage; gate ungated open")
    latest = roots.latest_manifest()
    if latest is not None:
        allow.add_exact(latest)
        v = _verify_manifest(roots, latest)
        if v["n_bad"]:
            em.say(f"wp3_material: the final manifest {latest} does not re-hash ({v['n_bad']} entries); refused")
            return {"status": "refused (the final manifest's records or objects changed)", "entries": {},
                    "admitted": list(door.admitted)}
        em.say(f"wp3_material: final manifest {latest} verified; nothing to do")
        return {"status": "final (nothing to do)", "entries": v["manifest"]["objects"], "noop": True,
                "manifest_path": str(latest), "manifest_sha256": v["sha256"], "final": True,
                "admitted": list(door.admitted), "written": [str(p) for p in em.written]}
    try:
        pre = preflight(roots, door, em, allow)
    except PreflightRefused:
        em.say(f"wp3_material: {L.STATUS_PREFLIGHT}")
        return {"status": L.STATUS_PREFLIGHT, "entries": {}, "admitted": list(door.admitted),
                "written": [str(p) for p in em.written]}
    if not WPDF.version_ok():                   # fix round 3, C (c): an environment fault, before any carrier
        em.say(f"wp3_material: stage {STOP_PDF_ENV}; no carrier touched; no manifest written")
        return {"status": STOP_PDF_ENV, "entries": {}, "stopped": True, "admitted": list(door.admitted),
                "written": [str(p) for p in em.written]}
    want = (lambda k: True) if not only else (lambda k: k in set(only))
    entries: dict = {}
    try:
        return _run_targets(roots, door, em, allow, out, want, pre, entries, run_info)
    except ResumeRefused as e:
        em.say(f"wp3_material: stage {STOP_RESUME % e.check}; no manifest written")
        return {"status": STOP_RESUME % e.check, "entries": entries, "stopped": True, "admitted": list(door.admitted),
                "written": [str(p) for p in em.written]}


def _run_targets(roots, door, em, allow, out, want, pre, entries, run_info) -> dict:
    entries[L.BRAINSPAN_KEY] = _file_identity_record(roots, door, em, allow, pre["brainspan"])
    em.say(f"wp3_material: brainspan identity at use: {entries[L.BRAINSPAN_KEY]['status']}; files 3")
    tg = targets(roots, pre["idrefs"])
    for image in L.SEGURA_IMAGES:
        k = L.SEGURA_MAP_KEY[image]
        entries[k] = _local_target(roots, em, out, k, tg[k], reader=segura_reader(door, image), want=want)
    entries[L.MOREAU_KEY] = _local_target(roots, em, out, L.MOREAU_KEY, tg[L.MOREAU_KEY], want=want)
    pdf_inputs = moesm2_inputs(roots, door)
    e = _local_target(roots, em, out, L.MOESM2_KEY, tg[L.MOESM2_KEY], reader=moesm2_reader(door, pdf_inputs),
                      want=want)
    try:
        entries[L.MOESM2_KEY] = _moesm2_readback(roots, door, em, e, pdf_inputs)
    except EnvironmentStop:
        em.say(f"wp3_material: stage {STOP_PDF_ENV}; no manifest written")
        return {"status": STOP_PDF_ENV, "entries": entries, "stopped": True, "admitted": list(door.admitted),
                "written": [str(p) for p in em.written]}
    if entries[L.MOESM2_KEY].get("readback") == "differs":
        entries[L.MOESM2_KEY].update(status=STATUS_READBACK, final=True)
    em.say(f"wp3_material: {L.MOESM2_KEY} status {entries[L.MOESM2_KEY]['status']}; read-back "
           f"{entries[L.MOESM2_KEY].get('readback', 'not run')}")
    entries.update(run_sd7(roots, door, em, out, want))
    hg_cache: dict = {}
    try:
        for image in L.SEGURA_IMAGES:
            kd = L.SEGURA_DECODER_KEY[image]
            if not want(kd):
                entries[kd] = {"status": L.STATUS_PENDING, "final": False}
                continue
            r = DC.run_decoder(roots, image, tg[kd], decoder_reader(door, image, hg_cache), em, out=out,
                               prefreeze=pre["idrefs"][L.SEGURA_MAP_KEY[image]], utc_now=utc_now)
            if r.get("adopt_record"):
                rp = Path(r["adopt_record"])
                rb = rp.read_bytes()
                ent = _entry_from_record(roots, rp, json.loads(rb.decode("utf-8")), rb)
                if ent.get("object_problem") or ent.get("status") != FE.STATUS_EXTRACTED:
                    raise AssertionError("the decoder's extracted record or object differs")
                entries[kd] = dict(ent, final=True, decided="extracted (R45 (f): decided once)")
            else:
                entries[kd] = {k: v for k, v in r.items()}
            em.say(f"wp3_material: {kd} decided: {entries[kd]['status']}")
    except DC.StageStop as e:
        em.say(f"wp3_material: stage {e.status}; no manifest written")
        return {"status": e.status, "entries": entries, "stopped": True, "admitted": list(door.admitted),
                "written": [str(p) for p in em.written]}
    required = CARRIER_KEYS if roots.sd7_copy is not None else tuple(k for k in CARRIER_KEYS
                                                                     if not k.startswith("liu_sd7_"))
    final = all(e.get("final", True) for e in entries.values()) and all(k in entries for k in required)
    man = {"schema": L.MANIFEST_SCHEMA, "gate": L.GATE, "final": bool(final), "written_utc": utc_now(),
           "run": dict(run_info or {}), "objects": entries, "pins": pre["pins"], "code": code_record(roots),
           "decoder_attempts": {"declared": DC.MAX_ATTEMPTS, "waits_s": list(DC.WAITS),
                                "rule": "RUN_PLAN_amend_3 R45 (f): transport failures only, counted across runs"}}
    d = Path(roots.records) / L.GATE
    if final:
        n = (roots.manifest_versions()[-1][0] + 1) if roots.manifest_versions() else 1
        path = roots.manifest_path if n == 1 else d / f"wp3_material_manifest.{n}.json"
    else:
        k = 1
        while (d / f"{L.PARTIAL_PREFIX}.{k}.json").exists():
            k += 1
        path = d / f"{L.PARTIAL_PREFIX}.{k}.json"
    allow.add_exact(path)
    sha = PW.stage(em, "record", em.write_json, path, man, "identity")
    em.say(f"wp3_material: {'final' if final else 'partial'} manifest written {path} sha256 {sha}; objects "
           f"{len(entries)}; not final {sum(1 for e in entries.values() if not e.get('final', True))}")
    return {"status": "final" if final else "partial", "entries": entries, "manifest_path": str(path),
            "manifest_sha256": sha, "final": bool(final), "written": [str(p) for p in em.written],
            "admitted": list(door.admitted)}


def _sd7_step6(roots: L.Roots, door: Door, em: PW.Emitter, out, want, e1: dict, e2: dict, lab_t) -> dict:
    """Fix round 3, B1 (the orchestrator's decision; section 8 step 6 runs once an extraction is verified, R46 (h) only
    defers it): pass 1's extraction verified and SD7 identifier-bearing -> step 6 (the move and the deletion request)
    runs ONCE after the last pass attempted, whether pass 2 extracted (it ran step 6 itself), was refused (FE12 kept
    it from quarantining) or was skipped (pass 1's record fail-closed). Its own record: key liu_sd7_step6."""
    rec1 = json.loads(door.read_bytes(Path(roots.records) / e1["record_path"]).decode("utf-8"))
    if not rec1.get("identifier_bearing") or e1.get("quarantined") or e2.get("quarantined"):
        return {}
    if not e2.get("final", True):
        return {"liu_sd7_step6": {"status": L.STATUS_PENDING, "final": False}}
    key = "liu_sd7_step6"
    st = target_state(roots, key)
    if st["entry"] is not None and st["final"]:
        em.say(f"wp3_material: {key} final in an earlier run (adopted): status {st['entry']['status']}")
        return {key: st["entry"]}
    if not want(key):
        return {key: {"status": L.STATUS_PENDING, "final": False}}
    t6 = dataclasses.replace(lab_t, key=key, sheets=(), defer_quarantine=False)
    FE.run_step6(t6, roots.fe_roots(), reason=STATUS_STEP6_REASON, out=out)
    st = target_state(roots, key)
    return {key: st["entry"] if st["entry"] is not None else {"status": L.STATUS_PENDING, "final": False}}


def run_sd7(roots: L.Roots, door: Door, em: PW.Emitter, out, want) -> dict:
    """R46: SD7's two passes on the registered copy (scratch: its stand-in); pass 1 (labels, position 0 only) decides
    T4 / T5; pass 2 (labels again + the ASD column) feeds the comparator only; step 6 runs once, after pass 2 (pass 1
    defers it). A layout without an SD7 copy (scratch only) reads SD7_NO_COPY."""
    import pandas as pd
    from . import wp3_sd7 as SD
    if roots.sd7_copy is None:
        em.say(f"wp3_material: liu_sd7 {L.STATUS_SD7_PENDING}; nothing opened")
        return {L.SD7_KEY: {"status": L.STATUS_SD7_PENDING, "final": True}}
    dk = pd.read_csv(io.BytesIO(door.pinned("dk_info")))
    lab_t, val_t = sd7_targets(roots, tuple(sorted(set(str(x) for x in dk["label"]))))
    e1 = _local_target(roots, em, out, "liu_sd7_labels", lab_t, transform=sd7_label_transform(dk), want=want)
    out_ = {"liu_sd7_labels": e1}
    if e1.get("status") != FE.STATUS_EXTRACTED or "object_path" not in e1:
        # pass 1's extraction not verified: no step 6 (FE12)
        out_["liu_sd7_values"] = {"status": STATUS_SD7_VALUES_SKIPPED % e1.get("status"), "final": bool(e1.get("final"))}
        out_[L.SD7_KEY] = {"status": e1.get("status"), "final": bool(e1.get("final"))}
        return out_
    lab_obj = json.loads(door.read_bytes(Path(roots.artifacts) / e1["object_path"]).decode("utf-8"))["objects"]["sd7"]
    if lab_obj.get("status") != "matched":
        out_["liu_sd7_values"] = {"status": STATUS_SD7_VALUES_SKIPPED % lab_obj.get("status"), "final": True}
        out_[L.SD7_KEY] = {"status": lab_obj.get("status"), "final": True}
        out_.update(_sd7_step6(roots, door, em, out, want, e1, out_["liu_sd7_values"], lab_t))
        return out_
    e2 = _local_target(roots, em, out, "liu_sd7_values", val_t, transform=sd7_value_transform(dk, lab_obj), want=want)
    out_["liu_sd7_values"] = e2
    out_.update(_sd7_step6(roots, door, em, out, want, e1, e2, lab_t))
    rec1 = json.loads(door.read_bytes(Path(roots.records) / e1["record_path"]).decode("utf-8"))
    n_rows = ((rec1.get("sheets") or {}).get("declared") or [{}])[0].get("n_block_rows")
    out_[L.SD7_KEY] = {"status": "matched (pass 1); values: " + str(e2.get("status")), "final": bool(e2.get("final")),
                       "block_rows": n_rows, "registered_rows": 78,
                       "rows_reading": "reported beside the registered 78 (R46 (d)); never a refusal"}
    _ = SD
    return out_


def code_record(roots: L.Roots) -> dict:
    here = Path(__file__).resolve().parent
    mods = ("wp3_material.py", "wp3_layout.py", "wp3_genes.py", "real_sources.py", "wp3_repro.py", "fetch_extract.py",
            "reparcel.py", "identity.py", "privacy_wrap.py", "forms.py")
    return {m: hashlib.sha256((here / m).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for m in mods
            if (here / m).exists()}


# ================================================================================================================
# CLI
# ================================================================================================================
PLAN_LINES = (
    "phase 2 (WP3 material) opens, in order, and writes:",
    "1 segura_790618 / segura_781986: the local NIfTI copy named by IDENTITY_prefreeze.json (sha256 + size; NeuroVault "
    "size); the pinned PCP AAL atlas and aal_atlas_info.csv -> record register_maps/post_freeze/ungated/<key>.json, "
    "object artifacts/audit/wp3/ungated/<key>/<key>_extract.json (V-AAL values, coverage report)",
    "2 segura_decoder_790618 / _781986 (R45): one HEAD of each image's NeuroVault file URL (size probe); network GET "
    "of the decoder JSON (mask=full) into E:/data/asdg/<key>/carrier.json.a<k>.part -> carrier.json + SOURCE.md, up "
    "to 3 attempts across runs (start and outcome records in run_manifests/material/ungated/); the HGNC table -> "
    "record + gene-level object, or 'unavailable' (R22's fallback)",
    "3 moreau2020mutations: the local workbook copy (sha256 + git blob + size); sheet names in memory; the two declared "
    "sheets only (do-not-open list asserted) -> record + 64 x 64 block object; the whole clone quarantined + deletion "
    "request (section 8.1) if identifier-bearing; a re-run after a crash that followed the move and the request "
    "(fix round 5) re-hashes the object, states the quarantine path and the source path, compares the deletion request "
    "with the record, appends the one missing SOURCE.md line and writes <key>_completion.json - nothing re-extracted or "
    "moved again; any inconsistency stops the stage",
    "4 brainspan: sha256 of expression_matrix.csv / rows_metadata.csv / columns_metadata.csv (no content) -> record",
    "5 pins: a1_builds MANIFEST, build records and outputs, HGNC, GO obo / GAF, PTHR16.0_human, GAMBA, AAL atlas and "
    "info, DK info (sha256 only) -> manifest",
    "6 liu_sd7 (R46): the registered copy (sha256 + size); sheet names in memory (the name rule); SD7's header "
    "search through the guard; pass 1 position 0, pass 2 position 0 + ASD; normalised record and values by position; "
    "quarantine once after pass 2 if identifier-bearing",
    "6b segura_moesm2 (R47): the pinned MOESM2 copy (sha256); pages 37 / 38 only (pdfplumber 0.11.10); S6 genes and "
    "S7 values keyed by cell id; read back by a second parse",
    "0 first (R50, section 8.1): every identity and pin check and the Moreau clone assertion; any failure stops the "
    "stage before any carrier or request",
    "7 manifest register_maps/post_freeze/ungated/wp3_material_manifest.json (never overwritten)",
)


def main(argv=None) -> int:
    PW.install_excepthook("wp3_material")      # fix round 1 (A2): an uncaught exception prints class + file:line only
    ap = argparse.ArgumentParser(prog="python -m a1_audit.wp3_material")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--commit", required=True)        # fix round 1, B2 (4): no subset runs in production
    sub.add_parser("plan")
    d = sub.add_parser("dry")
    d.add_argument("--scratch", default=None, help="build synthetic stand-ins under DIR, run the stage there, dispatch")
    a = ap.parse_args(argv)
    if a.cmd == "plan":
        for ln in PLAN_LINES:
            print(ln)
        return 0
    if a.cmd == "dry":
        from . import real_sources as RS
        if a.scratch:
            # SYNTHETIC stand-ins only: the network is mocked (no request leaves the process; the two decoder URLs get
            # a synthetic JSON) and the guard's HGNC cache is preset (no read of the table under E:)
            from . import wp3_scratch as SC
            FE.PG.HGNC_FILE = Path(a.scratch) / "no_such_hgnc_table.txt"
            FE.PG._HGNC = frozenset(("PTEN",))
            roots = SC.build_scratch(Path(a.scratch))
            with SC.scratch_net(roots):
                res = run_material(roots, out=sys.stdout,
                                   run_info={"mode": "scratch (synthetic stand-ins; no launch)"})
            print(f"wp3_material: scratch stage {res['status']}; objects {len(res['entries'])}; manifest sha256 "
                  f"{res.get('manifest_sha256')}")
        else:   # the phase-2 records live in the MAIN repository's tree (RUN_PLAN section 2.3), also from a worktree
            from . import run as R
            roots = L.Roots.production(repo=R.REPO, out_repo=R.main_repository(R.REPO))
        counts = RS.dry_counts(RS.WP3Sources(roots))
        counts.pop("_records", None)          # counts per outcome / status only (no row text)
        print(json.dumps(counts, indent=1, sort_keys=True))
        return 0
    # run (phase 2): launch first (L1-L15; the guard self-test L13 before any workbook), outputs under the main tree
    from . import launch as LA
    from . import run as R
    try:
        rec = LA.launch(R.REPO, a.commit, None)
    except LA.LaunchRefused as e:
        print("wp3_material: launch refused: failed " + ", ".join(e.record.get("failed", [])))
        return 3
    roots = L.Roots.production(repo=R.REPO, out_repo=R.main_repository(R.REPO))
    res = run_material(roots, out=sys.stdout,
                       run_info={"commit": rec.get("run_commit"), "launch": "passed",
                                 "code_hash": next((x.get("observed", {}).get("code_hash") for x in rec.get("assertions", [])
                                                    if x.get("id") == "L11"), None)})
    bad = [k for k, e in res["entries"].items() if e["status"] not in (FE.STATUS_EXTRACTED, FE.STATUS_IDENTITY_ONLY,
                                                                         ID.STATUS_MATCH, L.STATUS_SD7_PENDING)]
    print(f"wp3_material: stage {res['status']}; objects {len(res['entries'])}; not extracted {len(bad)}")
    return 0 if (not bad and res.get("final")) else 3


if __name__ == "__main__":
    sys.exit(main())
