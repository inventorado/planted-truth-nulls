"""WP4 real loaders of the G2 rows (RUN_PLAN.md v3.1 §4, §11, §17; the DRAFT RUN_PLAN_amend_4.md): the runner's
Sources for gate G2, `WP4Sources(real_sources.WP3Sources)`. run.py uses it for a real (non-plant) pass with --gate G2;
the ungated rows keep WP3Sources unchanged.

ONE DOOR, PHASE-2 FIRST (as WP3): every file goes through real_path (a quarantine path refused first); the G2 manifest
(wp4_layout: register_maps/post_freeze/G2/wp4_material_manifest[.n].json, read from THIS tree, the pinned worktree) is
read before any object; objects are re-hashed against it; a source carrier's identity is re-asserted AT USE against its
references (IDENTITY_prefreeze.json; the registered prefixes); a mismatch reads "not auditable (map changed)".

Sources by the row's TSV map text (wp4_layout.MAP_BINDINGS; exactly one binding, else STATUS_NO_LOADER):
- patel (dk-ctx): eTable 4's 34 left DK values;
- giacomel_thickness / _mdd (dk-ctx), giacomel_subcortical / _mdd (V-DK-subcortex): the @93de089 object (governs);
- liu_t3 (V-DK): the L / R averages on the left V-DK parcels (R59);
- pretzsch_CT / _SA (dk-ctx, re-parcellated): eTable13's 180 left loadings -> dk-ctx by R15's majority rule
  (reparcel.parcels_to_dk on the pinned HCP-MMP1 volume and the DK atlas volume), computed at use;
- hansen (dk-ctx): enigma_ct.csv's asd column, Cammoun rows 35-68 -> DK ids by the Cammoun order object (R60);
- leyhausen_<image> (dk-ctx, re-parcellated): the lh GIFTI on R16's annot (surface rule).
- component: HAN-C1 = the shipped gene_pc1.csv's left rows (same order); HAN-C1-ourPC1 = R12's PC1 (WP2 build
  r12-han-c1-ourpc1, pc1_dk_ctx.csv, through its build-record chain).
- gene_set: a gated set (set_id 'gated_G2_*') from register_sets/post_freeze/G2 (MANIFEST_G2.json sha256 chain); any
  other set from the frozen S-build (WP3Sources.gene_set).
- gene_weights / second_map (Giacomel's signed-weight rows, RUN_PLAN_amend_2 R41): the gated set's weights on its member
  columns; the eda33ab GEDAR map (C01-C06, MDD-C1/C5/C10) or R17's rebuilt map (C19-C24, the MDD-DEG cells).
"""
from __future__ import annotations

import hashlib
import io
import json
import re
from pathlib import Path

import numpy as np

from . import fetch_extract as FE
from . import identity as ID
from . import real_sources as RS
from . import reparcel as RP
from . import run as R
from . import wp4_layout as L
from . import wp4_sets as WS

STATUS_SET_G2 = "refused: a gated G2 set differs from register_sets/post_freeze/G2/MANIFEST_G2.json"
STATUS_NO_COMPONENT = "refused: no fixed component is registered for this row"
STATUS_NO_SECOND_MAP = "not computable (the paper's GEDAR map of this cell is not among the G2 objects)"


def _sha(*arrays) -> str:
    h = hashlib.sha256()
    for a in arrays:
        a = np.ascontiguousarray(np.asarray(a))
        h.update(str(a.dtype).encode() + str(a.shape).encode() + a.tobytes())
    return h.hexdigest()


# ---- amend_5 v2: the labels a G2 row carries, and which rows have a post-exposure version ----------------------------
def row_labels(cell_id: str, version: str = L.VERSION_PRIMARY) -> list:
    """L130: the line-130 label on the cells whose second map is a line-130 file (wp4_material.line130_cells: the
    MDD-set DEG cells; descriptor-only, none in m); the post-exposure version's rows also carry its label."""
    from . import wp4_material as WM
    out = [L.LINE130_LABEL] if cell_id in set(WM.line130_cells()) else []
    if version == L.VERSION_AMEND5:
        out.append(L.AMEND5_VERSION_LABEL)
    return out


def amend5_readings(cell_id: str, map_text: str) -> list:
    """The amend_5 post-exposure readings that bear on a G2 row (empty: the row has no post-exposure version): R61'
    for a Pretzsch map (y_CT / y_SA), R54' for a Giacomel Subcortical map (ASD or MDD column), R58' (d) for the 18
    post-mortem DEG cells (their S and second map come from R17's run)."""
    from . import wp4_sets as WS
    text = str(map_text or "")
    hits = {name for name, needle in L.MAP_BINDINGS if needle in text}
    out = []
    if hits & {"pretzsch_CT", "pretzsch_SA"}:
        out.append(L.AMEND5_PE_READINGS[0])
    if hits & {"giacomel_subcortical", "giacomel_subcortical_mdd"}:
        out.append(L.AMEND5_PE_READINGS[1])
    if (WS.GATED_CELLS.get(cell_id) or (None,))[0] == "deg":
        out.append(L.AMEND5_PE_READINGS[2])
    return out


class WP4Sources(RS.WP3Sources):
    kind = "real-wp4"

    def __init__(self, roots4: L.Roots | None = None, roots3=None):
        from . import wp3_layout as W3
        super().__init__(roots3 or W3.Roots.production())
        self.r4 = roots4 or L.Roots.production()

    def spec(self) -> dict:
        return {"kind": self.kind, "roots": self.roots.to_spec(), "roots4": self.r4.to_spec()}

    # ---- the G2 manifest ----------------------------------------------------------------------------------------
    def _m4(self) -> dict:
        def f():
            if not self.r4.scratch:                      # asdg-skeptic C3: production needs the frozen amendment 4
                ok, why = L.production_allowed()         # (checked before any manifest is looked for)
                if not ok:
                    raise R.SourceUnavailable(L.STATUS_PENDING, "amendment 4 not frozen (the draft guard)")
            p = self.r4.latest_manifest()
            if p is None:
                if self.r4.partial_manifests():
                    raise R.SourceUnavailable(L.STATUS_NOT_FINAL, "only partial G2 manifests exist")
                raise R.SourceUnavailable(L.STATUS_PENDING, "the G2 manifest is absent")
            data = self.read_bytes(p)
            doc = json.loads(data.decode("utf-8"))
            if doc.get("schema") != L.MANIFEST_SCHEMA or doc.get("gate") != L.GATE or doc.get("final") is not True:
                raise R.SourceUnavailable(L.STATUS_PENDING, "the G2 manifest is not final")
            if doc.get("scratch") is not bool(self.r4.scratch):   # C3: a scratch manifest never feeds production
                raise R.SourceUnavailable(L.STATUS_PENDING, "the G2 manifest's scratch flag does not match the roots")
            doc["_sha256"] = hashlib.sha256(data).hexdigest()
            if getattr(self.r4, "version", L.VERSION_PRIMARY) == L.VERSION_AMEND5:
                # amend_5 v2: the post-exposure version reads the manifest's post_exposure block over the primary
                # objects (R61', R54', R58' (d)); its own sets and DEG checks; never the other way round
                pe = doc.get("post_exposure")
                if not isinstance(pe, dict) or pe.get("label") != L.AMEND5_VERSION_LABEL:
                    raise R.SourceUnavailable(L.STATUS_PENDING, "the G2 manifest has no post-exposure version")
                doc = dict(doc, objects={**doc["objects"], **(pe.get("objects") or {})}, sets=pe.get("sets"),
                           deg_checks=pe.get("deg_checks"), giacomel_comparison=pe.get("giacomel_comparison"),
                           version=L.VERSION_AMEND5)
            return doc
        return self._cached("m4", f)

    def _e4(self, key: str) -> dict:
        e = self._m4()["objects"].get(key)
        if e is None:
            # 2026-10-21 (run 7): the manifest is FINAL here (_m4), so an absent object was not produced by its step:
            # R17's outputs read R17's own status (A9 / upstream); any other absent object reads upstream - never
            # "material pending"
            raise R.SourceUnavailable(self.absent_status(key), f"G2 object {key} absent from the final manifest")
        return e

    def absent_status(self, key: str) -> str:
        if re.fullmatch(r"r17_(map|deg)_(ASD|MDD)_\d+", key):
            st = (self._m4()["objects"].get("r17") or {}).get("status")
            if st in (L.STATUS_R17, L.STATUS_UPSTREAM):
                return st
        return L.STATUS_UPSTREAM

    def obj4(self, key: str, sub: str):
        def f():
            e = self._e4(key)
            if e.get("status") != FE.STATUS_EXTRACTED or not e.get("object_path"):
                st = L.STATUS_MAP_CHANGED if e.get("identity_result") == ID.STATUS_CHANGED or \
                    e.get("status") == L.STATUS_MAP_CHANGED else (e.get("status") if str(e.get("status", "")).startswith(
                        ("not auditable", "not computable")) else L.STATUS_STAGE_REFUSED % e.get("status"))
                raise R.SourceUnavailable(st, f"G2 object {key}")
            rp = self.path(Path(self.r4.records) / e["record_path"])
            op = self.path(Path(self.r4.artifacts) / e["object_path"])
            rb = self.read_bytes(rp)
            if hashlib.sha256(rb).hexdigest() != e["record_sha256"]:
                raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"G2 record {key}")
            data = self.read_bytes(op)
            if hashlib.sha256(data).hexdigest() != e["object_sha256"]:
                raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"G2 object {key}")
            doc = json.loads(data.decode("utf-8"))
            if doc.get("key") != e.get("object_key", key):     # R17's run-indexed objects (wp4_material)
                raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"G2 object {key}: key")
            return doc["objects"], e["object_sha256"]
        objs, sha = self._cached(("obj4", key), f)
        if sub not in objs:
            raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"G2 object {key}: part {sub} absent")
        return objs[sub], sha

    def _idrefs4(self) -> dict:
        return self._cached("idrefs4", lambda: L.identity_records(self.r4, self.read_bytes))

    def identity4(self, key: str) -> dict:
        """Identity at use of a pinned G2 carrier (RUN_PLAN §17): its references (IDENTITY_prefreeze.json) or its
        registered prefix; a mismatch -> 'not auditable (map changed)'."""
        def f():
            if key in dict(self.r4.prefix_pins):
                path, prefix, _ = self.r4.prefix_pin(key)
                facts = self.guarded("identity", ID.file_facts, self.path(path), self.quarantine_root)
                if not facts["sha256"].startswith(prefix):
                    raise R.SourceUnavailable(L.STATUS_MAP_CHANGED, f"source {key}: registered prefix at use")
                return {"basis": "registered sha256 prefix at use", "sha256": facts["sha256"]}
            r = self._idrefs4()[key]
            facts = self.guarded("identity", ID.file_facts, self.path(r["local_path"]), self.quarantine_root)
            cmp = ID.compare(facts, r["refs"])
            if cmp["result"] != ID.STATUS_MATCH:
                raise R.SourceUnavailable(L.STATUS_MAP_CHANGED, f"source {key}: identity at use")
            return {"basis": "identity at use", "sha256": facts["sha256"]}
        return self._cached(("identity4", key), f)

    def download_identity(self, key: str) -> dict:
        """A downloaded G2 carrier: its runner-built copy re-hashed against the phase-2 record's facts."""
        def f():
            e = self._e4(key)
            rec = json.loads(self.read_bytes(Path(self.r4.records) / e["record_path"]).decode("utf-8"))
            want = ((rec.get("identity") or {}).get("facts") or {}).get("sha256")
            p = Path(self.r4.data) / key / f"carrier{Path((rec.get('fetch') or {}).get('path', 'x.bin')).suffix}"
            fp = (rec.get("fetch") or {}).get("path")
            if fp:
                p = Path(fp)
            elif e.get("object_key") and want:
                # 2026-10-21 (run 8): an amend_5 / versioned object read its carrier as a pinned copy (the record holds
                # the path's sha256 only); the carrier is the original key's runner-built copy, held to the same sha256
                hits = [q for q in sorted((Path(self.r4.data) / key).glob("carrier.*")) if q.is_file() and
                        hashlib.sha256(self.read_bytes(q)).hexdigest() == want]
                if len(hits) == 1:
                    p = hits[0]
            facts = self.guarded("identity", ID.file_facts, self.path(p), self.quarantine_root)
            if want is None or facts["sha256"] != want:
                raise R.SourceUnavailable(L.STATUS_MAP_CHANGED, f"source {key}: downloaded copy at use")
            return {"basis": "the phase-2 record's sha256", "sha256": facts["sha256"]}
        return self._cached(("dl", key), f)

    # ---- the TSV map binding --------------------------------------------------------------------------------------
    def binding(self, plan) -> str:
        text = self._rows()[int(plan["row"])]["map"]
        hits = [name for name, needle in L.MAP_BINDINGS if needle in text]
        if "giacomel_thickness_mdd" in hits and "giacomel_thickness" in hits:
            hits.remove("giacomel_thickness")
        if "giacomel_subcortical_mdd" in hits and "giacomel_subcortical" in hits:
            hits.remove("giacomel_subcortical")
        if len(hits) != 1:
            raise R.SourceUnavailable(L.STATUS_NO_LOADER, "map (no single WP4 binding)")
        return hits[0]

    def reparcellated(self, plan) -> bool:
        try:
            b = self.binding(plan)
        except R.SourceUnavailable:
            return super().reparcellated(plan)
        return b.startswith(("pretzsch", "leyhausen"))

    def _on_class(self, cls: str, by: dict, keys) -> tuple:
        ctx = self.context(cls)[0]
        ids = np.asarray(ctx.parcel_ids, dtype=np.int64)
        y = np.array([np.nan if by.get(int(i)) is None else float(by[int(i)]) for i in ids], dtype=float)
        return y, ids

    def g2_map(self, plan) -> tuple:
        """(y on the class parcels, ids, hashes) of a G2 row."""
        b = self.binding(plan)
        cls = plan["analysis_class"]
        h = {}
        if b == "patel":
            if cls != "dk-ctx":
                raise R.SourceUnavailable(R.REFUSED_CLASS, "Patel outside dk-ctx")
            o, sha = self.obj4(L.PATEL_KEY, "etable4")
            self.identity4(L.PATEL_KEY)
            by = dict(zip(o["ids"], o["values"]))
            h["object"] = sha
        elif b.startswith("giacomel"):
            sheet = "thickness" if "thickness" in b else "subcortical"
            col = "mdd" if b.endswith("_mdd") else "asd"
            want = "dk-ctx" if sheet == "thickness" else "V-DK-subcortex"
            if cls != want:
                raise R.SourceUnavailable(R.REFUSED_CLASS, "Giacomel sheet outside its class")
            o, sha = self.obj4(L.GIA_GOV_KEY, sheet)
            if "status" in o and col not in o:            # R54: the sheet's fail-closed status
                raise R.SourceUnavailable(o["status"], "Giacomel sheet layout")
            self.download_identity(L.GIA_GOV_KEY)
            by = dict(zip(o[col]["ids"], o[col]["values"]))
            h["object"] = sha
        elif b == "liu_t3":
            if cls != "V-DK":
                raise R.SourceUnavailable(R.REFUSED_CLASS, "LIU-T3 outside V-DK")
            from . import wp4_read as RD
            ct, s1 = self.obj4(L.LIU_CT_KEY, "cortthick")
            sv, s2 = self.obj4(L.LIU_SV_KEY, "subvol")
            self.identity4(L.LIU_CT_KEY)
            self.identity4(L.LIU_SV_KEY)
            dk = self.dk_table()
            m = RD.liu_t3_map({"by_id": {int(k): v for k, v in ct["by_id"].items()}},
                              {"by_id": {int(k): v for k, v in sv["by_id"].items()}}, dk)
            by = dict(zip(m["ids"], m["values"]))
            h.update(object_ct=s1, object_sv=s2)
        elif b == "hansen":
            if cls != "dk-ctx":
                raise R.SourceUnavailable(R.REFUSED_CLASS, "Hansen outside dk-ctx")
            ct, s1 = self.obj4(L.HANSEN_CT_KEY, "asd")
            cam, s2 = self.obj4(L.HANSEN_INFO_KEY, "cammoun")
            self.identity4(L.HANSEN_CT_KEY)
            self.identity4(L.HANSEN_INFO_KEY)
            vals = ct["values"]
            by = {int(did): float(vals[r]) for did, r in zip(cam["left_row_ids"], L.HANSEN_LEFT_ROWS)}
            h.update(object=s1, cammoun=s2)
        elif b.startswith("pretzsch"):
            if cls != "dk-ctx":
                raise R.SourceUnavailable(R.REFUSED_CLASS, "Pretzsch outside dk-ctx")
            by, h = self.pretzsch_dk(b.split("_")[1])
        elif b.startswith("leyhausen"):
            if cls != "dk-ctx":
                raise R.SourceUnavailable(R.REFUSED_CLASS, "Leyhausen outside dk-ctx")
            image = int(b.split("_")[1])
            o, sha = self.obj4(L.LEY_LH_KEY[image], "dkctx")
            self.identity4(L.LEY_LH_KEY[image])
            self.identity4(L.LEY_VOL_KEY[image])
            by = dict(zip(o["ids"], o["values"]))
            h["object"] = sha
        else:
            raise R.SourceUnavailable(L.STATUS_NO_LOADER, "map")
        y, ids = self._on_class(cls, by, None)
        return y, ids, h

    def pretzsch_dk(self, feature: str) -> tuple[dict, dict]:
        """R15 at use: the 180 left loadings -> dk-ctx (reparcel.parcels_to_dk: > 50 % majority, voxel-weighted)."""
        def f():
            lab, s1 = self.obj4(L.HCP_LIST_KEY, "labels")
            et, s2 = self.obj4(L.PRE_KEY, "etable13")
            self.identity4(L.PRE_KEY)
            vrec = self.download_identity(L.HCP_VOL_KEY)
            e = self._e4(L.HCP_VOL_KEY)
            rec = json.loads(self.read_bytes(Path(self.r4.records) / e["record_path"]).decode("utf-8"))
            vpath = self.path(Path((rec.get("fetch") or {})["path"]))
            src, saff = RP.load_atlas_verified(vpath, vrec["sha256"], self.quarantine_root)
            dpath, dsha = self.r4.pin("dk_atlas")
            dk_atlas, daff = RP.load_atlas_verified(self.path(dpath), dsha, self.quarantine_root)
            dk = self.dk_table()
            dk_ids = [int(i) for i in dk[(dk["hemisphere"] == "L") & (dk["structure"] == "cortex")]["id"]]
            out = {}
            for feat in ("CT", "SA"):
                vals = dict(zip([int(i) for i in lab["left_ids"]], et[feat]))
                kept, v, rep = RP.parcels_to_dk(vals, src, saff, [int(i) for i in lab["left_ids"]], dk_atlas, daff,
                                                dk_ids)
                out[feat] = ({int(i): float(x) for i, x in zip(kept.tolist(), v.tolist())},
                             {k: rep[k] for k in ("n_source", "n_assigned", "n_outside", "n_no_majority", "n_kept",
                                                  "n_unassigned")})
            return out, {"labels": s1, "etable13": s2, "volume": vrec["sha256"], "dk_atlas": dsha}
        out, h = self._cached("pretzsch_dk", f)
        by, rep = out[feature]
        # 2026-10-21 (run 8, amend5): an input HASH must be sha256 hex (launch.row_provenance); the counts are recorded by
        # the sha256 of their canonical JSON (the counts themselves are in the R15 reparcellation report)
        return dict(by), dict(h, reparcel_counts=hashlib.sha256(json.dumps(rep, sort_keys=True).encode("utf-8"))
                              .hexdigest())

    def giacomel_order_matched(self) -> bool:
        """R54 (B4): whether the governing Subcortical sheet is in the registered alphabetical order (recorded by the
        material stage; the misalignment descriptor needs it, T does not)."""
        o, _ = self.obj4(L.GIA_GOV_KEY, "subcortical")
        return bool(o.get("order_matched"))

    def pretzsch_recipe_inputs(self, plan) -> tuple:
        """R14 / R38 at use: y = eTable13's feature on the 180 left parcels (the label list's left order), the six
        per-donor HCP-MMP1 matrices (the perdonor-hcpmmp1 build, its record held to the G2 manifest's sha256; rows
        reindexed to the left ids, absent parcels NaN), and each column's HGNC symbol (the S-build's rule; unmapped
        columns dropped)."""
        import pandas as pd
        from . import ahba_builds as AB
        feat = self.binding(plan).split("_")[1]
        lab, _ = self.obj4(L.HCP_LIST_KEY, "labels")
        et, _ = self.obj4(L.PRE_KEY, "etable13")
        e = self._e4("perdonor_hcpmmp1")
        b = Path(self.r4.hcp_build)
        rb = self.read_bytes(b / AB.RECORD)
        if e.get("status") != "built" or hashlib.sha256(rb).hexdigest() != e.get("record_sha256"):
            raise R.SourceUnavailable(RS.STATUS_BUILD, "perdonor-hcpmmp1 record")
        rec = json.loads(rb.decode("utf-8"))
        # asdg-skeptic C8: the build was made from the R15 downloads (their sha256 at download, the G2 manifest)
        ev, el = self._e4(L.HCP_VOL_KEY), self._e4(L.HCP_LIST_KEY)
        if not (isinstance(ev.get("sha256"), str) and rec.get("volume_sha256") == ev["sha256"]
                and isinstance(el.get("sha256"), str) and rec.get("label_list_sha256") == el["sha256"]):
            raise R.SourceUnavailable(RS.STATUS_BUILD, "perdonor-hcpmmp1 not built from the R15 downloads")
        left = [int(i) for i in lab["left_ids"]]
        mats, cols = [], None
        for o in sorted((o for o in rec["outputs"] if o.get("role") == "matrix"), key=lambda o: o["donor_position"]):
            data = self.read_bytes(b / o["file"])
            if hashlib.sha256(data).hexdigest() != o["sha256"]:
                raise R.SourceUnavailable(RS.STATUS_BUILD, "perdonor-hcpmmp1 matrix")
            df = pd.read_csv(io.BytesIO(data), index_col=0, compression="gzip")
            if cols is None:
                cols = [str(c) for c in df.columns]
            elif [str(c) for c in df.columns] != cols:
                raise R.SourceUnavailable(RS.STATUS_BUILD, "perdonor-hcpmmp1 genes differ between donors")
            mats.append(df.reindex([int(i) for i in left]).to_numpy(dtype=float))
        mapped, _how = self.hgnc().map_columns(cols)
        keep = [k for k, m in enumerate(mapped) if m]
        mats = [M[:, keep] for M in mats]
        genes = [mapped[k] for k in keep]
        return np.asarray(et[feat], dtype=float), mats, genes

    def map(self, plan, map_index):
        if plan.get("gate") != L.GATE:
            return super().map(plan, map_index)
        self._m4()
        cls = plan["analysis_class"]
        y, ids, h = self.g2_map(plan)
        mi = int(map_index)
        hashes = {f"map[{mi}]": R.arr_sha(y, ids), f"map[{mi}] G2 manifest": self._m4()["_sha256"]}
        hashes.update({f"map[{mi}] {k}": str(v) for k, v in h.items()})
        return y, ids, cls, hashes

    # ---- sets ---------------------------------------------------------------------------------------------------------
    def _set_man4(self) -> dict:
        def f():
            name = (self._m4().get("sets") or {}).get("manifest_name") or L.SET_MANIFEST_NAME   # versioned (resume)
            if not re.fullmatch(r"MANIFEST_G2(\.\d+)?\.json", name):
                raise R.SourceUnavailable(STATUS_SET_G2, "the G2 set manifest name")
            p = self.r4.set_dir() / name
            if not p.is_file():
                raise R.SourceUnavailable(L.STATUS_PENDING, "the G2 set manifest is absent")
            data = self.read_bytes(p)
            want = (self._m4().get("sets") or {}).get("manifest_sha256")
            if want is not None and hashlib.sha256(data).hexdigest() != want:
                raise R.SourceUnavailable(STATUS_SET_G2, "the G2 set manifest differs from the G2 manifest")
            doc = json.loads(data.decode("utf-8"))
            return {e["set_id"]: e for e in doc["sets"]}
        return self._cached("setman4", f)

    def set_doc4(self, set_id: str) -> tuple[dict, str]:
        def f():
            e = self._set_man4().get(set_id)
            if e is None:
                cell = set_id[len("gated_G2_"):]
                st = ((self._m4().get("deg_checks") or {}).get(cell) or {}).get("status")   # a DEG cell: its check
                raise R.SourceUnavailable(st if isinstance(st, str) and st else L.STATUS_UPSTREAM,
                                          f"gated set {set_id} not built (final manifest)")
            if not re.fullmatch(re.escape(set_id) + r"(\.\d+)?\.json", str(e.get("json", ""))):
                raise R.SourceUnavailable(STATUS_SET_G2, f"gated set {set_id}: file name")    # <set_id>[.<n>].json
            data = self.read_bytes(self.r4.set_dir() / e["json"])
            sha = hashlib.sha256(data).hexdigest()
            if sha != e["sha256"]:
                raise R.SourceUnavailable(STATUS_SET_G2, f"gated set {set_id}")
            return json.loads(data.decode("utf-8")), sha
        return self._cached(("set4", set_id), f)

    def gene_set(self, plan):
        sid = plan["set_id"]
        if not sid.startswith("gated_G2_"):
            return super().gene_set(plan)
        doc, sha = self.set_doc4(sid)
        if doc.get("status") not in ("built under gate G2", L.STATUS_WEIGHT_COLUMN):
            raise R.SourceUnavailable(doc.get("status"), f"gated set {sid}")
        uni = (doc.get("universe") or {}).get(plan["analysis_class"])
        if uni is None:
            raise R.SourceUnavailable(STATUS_SET_G2, f"gated set {sid}: no {plan['analysis_class']} universe")
        return list(uni["columns"]), sha

    def gene_weights(self, plan):
        """R41: S's member columns and their signed weights (a gene's weight on each of its columns)."""
        doc, sha = self.set_doc4(plan["set_id"])
        w = doc.get("weights")
        if not w:
            raise R.SourceUnavailable(L.STATUS_WEIGHT_COLUMN, "gated set weights")
        cls = plan["analysis_class"]
        col_gene = (doc.get("universe_column_gene") or {}).get(cls)
        cols = (doc.get("universe") or {}).get(cls, {}).get("columns") or []
        if col_gene is None:
            raise R.SourceUnavailable(STATUS_SET_G2, "gated set: no column-gene map")
        genes = [c for c in cols if col_gene.get(c) in w]
        vals = np.array([float(w[col_gene[c]]) for c in genes], dtype=float)
        return genes, vals, sha

    def row_labels(self, plan) -> list:
        """amend_5 L130: the labels a G2 row carries beside its result (the MDD-TPRS-derived cells: the paper's line
        130 writes the ASD values into the MDD TPRS files; the script runs as published)."""
        return row_labels(plan["cell_id"], getattr(self.r4, "version", L.VERSION_PRIMARY))

    def second_map(self, plan, map_index):
        """The paper's weighted map b of a signed-weight row on the class parcels (eda33ab GEDAR map, or R17's)."""
        cell = plan["cell_id"]
        kind, key, _w = WS.GATED_CELLS.get(cell, (None, None, None))
        if kind == "list":
            thr = key.rsplit("_", 1)[1]
            dx = key.split("_")[0]
            okey = f"gia_gedar_{dx}_TPRS_thr_{thr}"
        elif kind == "deg":
            okey = f"r17_map_{key}"
        else:
            raise R.SourceUnavailable(STATUS_NO_SECOND_MAP, "second map")
        o, sha = self.obj4(okey, "map")
        self.download_identity(okey) if okey.startswith("gia_gedar_") else None
        by = {int(k): v for k, v in o["by_id"].items()}
        cls = plan["analysis_class"]
        b, ids = self._on_class(cls, by, None)
        return b, ids, sha

    # ---- components ---------------------------------------------------------------------------------------------------
    def component(self, plan):
        cell = plan["cell_id"]
        if cell == "HAN-C1":
            pc1, s1 = self.obj4(L.HANSEN_PC1_KEY, "pc1")
            cam, s2 = self.obj4(L.HANSEN_INFO_KEY, "cammoun")
            self.identity4(L.HANSEN_PC1_KEY)
            by = {int(d): float(pc1["values"][r]) for d, r in zip(cam["left_row_ids"], L.HANSEN_LEFT_ROWS)}
            c, ids = self._on_class(plan["analysis_class"], by, None)
            return c, ids, hashlib.sha256((s1 + s2).encode("ascii")).hexdigest()
        if cell == "HAN-C1-ourPC1":
            import pandas as pd
            b = Path(self.roots.builds)
            man = json.loads(self.read_bytes(b / "MANIFEST.json").decode("utf-8"))
            rb = self.read_bytes(b / "r12-han-c1-ourpc1" / "build_record.json")
            if hashlib.sha256(rb).hexdigest() != man["builds"]["r12-han-c1-ourpc1"]["record_sha256"]:
                raise R.SourceUnavailable(RS.STATUS_BUILD, "R12 record")
            rec = json.loads(rb.decode("utf-8"))
            o = [x for x in rec["outputs"] if x["file"] == "pc1_dk_ctx.csv"]
            data = self.read_bytes(b / "r12-han-c1-ourpc1" / "pc1_dk_ctx.csv")
            if len(o) != 1 or hashlib.sha256(data).hexdigest() != o[0]["sha256"]:
                raise R.SourceUnavailable(RS.STATUS_BUILD, "R12 PC1")
            df = pd.read_csv(io.BytesIO(data))
            by = {int(i): float(v) for i, v in zip(df["label"], df["pc1"])}
            c, ids = self._on_class(plan["analysis_class"], by, None)
            return c, ids, o[0]["sha256"]
        raise R.SourceUnavailable(STATUS_NO_COMPONENT, "component")
