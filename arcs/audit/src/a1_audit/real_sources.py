"""WP3 real loaders (RUN_PLAN.md v3.1 §4, §10, §17, §18 WP3; RUN_PLAN_amend_1 R35; amend_2 R42; FROZEN): the runner's
Sources for the ungated rows, `WP3Sources(run.RealSources)`. run.py uses it for every real (non-plant) run; the WP2
base class `run.RealSources` (every source refused, "not run (WP3 loader pending)") is unchanged.

ONE DOOR. Every file a loader here opens is first passed through `real_path` (run.RealSources.real_path: a path under
the quarantine raises PermissionError -> the row reads STATUS_QUARANTINE), which also records it in `admitted`. Files
opened inside frozen / earlier code (a3_port's context builder, e3_plants' readers, launch.matrix_first_use) are passed
through real_path before that code runs. tests/test_wp3_phase1.py records every open made during a load (builtins /
io / os open, Path, numpy, pandas, gzip, zipfile, openpyxl, xlrd, nibabel) and fails if one was not admitted first; a
loader variant that bypasses real_path is shown to fail it.

PHASE-2 FIRST. Every loader of ungated material reads the phase-2 manifest (wp3_layout.Roots.manifest_path) before it
touches a carrier: absent -> SourceUnavailable(STATUS_PENDING) and nothing else is opened. Objects are read from the
fixed runner-built paths the manifest names, their sha256 asserted against it; a source carrier's identity is asserted
AT USE (its sha256 / size / git blob re-computed against IDENTITY_prefreeze.json's references; a carrier the stage
quarantined is held to its phase-2 record instead); a mismatch -> "not auditable (map changed)" (RUN_PLAN §17).

Sources (run.Sources interface):
- context(cls): adapters.build_context_checked (R35's first-use reader check, then a3_port.build_context with its L7
  pin); the AHBA sample counts = the WP2 primary build's counts table (n_samples) of the class's atlas, read through the
  build-record chain (a1_builds MANIFEST -> build_record.json -> file sha256 -> default-reader frame hash), and against
  the phase-2 pins when they exist. Not phase-2 material: available before phase 2 (U-W3-7).
- donor_counts(cls): the same table's n_donors (R11; donor columns read by position, never printed).
- map(plan, i): Segura (V-AAL): the phase-2 re-parcellation object, its source volume's identity at use, the
  re-parcellation recomputed from the source and asserted equal (bit for bit) to the saved object, values on the class
  context's parcels (NaN where the §1.7 rule dropped the parcel). Moreau (MIST64): the phase-2 64 x 64 block of the
  row's declared sheet (bound by the TSV map text), the nodal profile = the block with the diagonal set to 0, mean over
  its 64 columns (TSV row 615 'map'), values on the class's primary parcels. Any other row: STATUS_NO_LOADER.
- gene_set(plan): register_sets/<set_id>.json's columns of the class universe, through the freeze chain
  (register_freeze_manifest.json LF sha256 = L3 pin -> its entry for register_sets/MANIFEST.json -> the set's sha256).
- trajectories(cls): BrainSpan, the frozen rule (wp3_genes.brainspan_trajectories = asdg.brainspan.load_trajectories on
  the declared columns), keyed by BrainSpan's gene_symbol as frozen.
- liu_inputs(plan) (R10, R42): BrainSpan (T1, T2, T2-*) or the WP2 R10 per-sample build (T4, T5; well ids already
  dropped by the build; rows positional) with the S-build's HGNC mapping, the set's HGNC members, GAMBA brain>body
  symbols (HGNC-mapped; U-W3-8), the HGNC-keyed trajectories (U-W3-5), the DK table and the SD7 record (pending).
- component(plan): refused (no ungated row reads a fixed component). selection_rule / resolve_class: the base refusals.
"""
from __future__ import annotations

import functools
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import a3_port as A3
from . import adapters as AD
from . import ahba_builds as AB
from . import fetch_extract as FE
from . import identity as ID
from . import loader as LD
from . import privacy_wrap as PW
from . import run as R
from . import wp3_genes as WG
from . import wp3_layout as L
from . import wp3_material as WM      # (imports nibabel's globals and neutralises their handler: fix round 1, A1)

STATUS_NO_LOADER = "not run (no WP3 loader: this row's material is a gated target's, WP4 / WP5)"
STATUS_SET = "refused: a set file differs from the frozen S-build manifest"
STATUS_BUILD = "refused: an AHBA build output differs from its build record or the phase-2 pins"
CLASS_ATLAS = {"V-AAL": "aal", "V-DK": "dk", "dk-ctx": "dk", "V-DK-subcortex": "dk", "MIST64": "mist64"}
# the WP2 build outputs the loaders read (build -> roles): the primaries' count tables (the matrices themselves are read
# through a3_port with their L6 / L7 pins), the per-donor V-AAL matrices (R22's fallback, R14) and the R10 samples
BUILDS_READ = {"primary-dk": ("counts",), "primary-aal": ("counts",), "primary-mist64": ("counts",),
               "perdonor-aal": ("matrix", "counts"), "r10-liu-dk-samples": ("matrix",)}
SET_MANIFEST_REL = "arcs/audit/register_sets/MANIFEST.json"
# fix round 1 (A2): an OSError (absent, locked, moved carrier) at use reads STATUS_USE_UNREADABLE; anything else raised
# while a carrier is read at use reads STATUS_USE_FAILED; both through section 8's handler (class, stage, file:line)
OS_ERROR_NAMES = frozenset(n for n, o in vars(__import__("builtins")).items()
                           if isinstance(o, type) and issubclass(o, OSError))


def build_file_key(o: dict) -> str:
    """A build output's runner-side key: 'counts', 'matrix', or 'matrix_d<k>' (k = the donor's position in
    ahba_builds.DONORS; the donor id is never used as a key)."""
    if o.get("role") == "counts":
        return "counts"
    if o.get("donor") is not None:
        return "matrix_d%d" % (AB.DONORS.index(str(o["donor"])) + 1)
    return "matrix"


def sha_json(o) -> str:
    return hashlib.sha256(json.dumps(A3.jsonable(o), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class WP3Sources(R.RealSources):
    kind = "real-wp3"

    def __init__(self, roots: L.Roots | None = None):
        self.roots = roots or L.Roots.production()
        self.quarantine_root = Path(self.roots.quarantine)
        self.admitted: list[str] = []
        self._c: dict = {}
        self.stage_lines: list[str] = []       # the section 8 handler's lines of stages run at use (vocabulary only)

    # ---- section 8's handler at use (fix round 1, A2) ------------------------------------------------------------
    def _allow(self) -> PW.AllowList:
        a = self._c.get("_allow")
        if a is None:
            a = PW.AllowList(phrases=FE.FE_PHRASES + WM.WP3_PHRASES)
            self._c["_allow"] = a
        return a

    def guarded(self, label: str, fn, *args):
        """fn(*args) inside section 8's handler with the stdio guard and the quiet warnings / logging contexts (a
        library's own handler included): an exception never escapes with its message or traceback; an OSError reads
        STATUS_USE_UNREADABLE, anything else STATUS_USE_FAILED (detail: class, stage, file:line). Paths are admitted
        through the door by the caller first (a quarantine refusal keeps its own status). Fix round 3, C (b): a
        SourceUnavailable or reparcel.ReparcelRefused raised inside fn keeps its own status (e.g. section 17's 'not
        auditable (map changed)'), re-raised fresh (no chained message) after the guard."""
        import io as _io
        from . import reparcel as RP
        allow = self._allow()
        buf = _io.StringIO()
        em = PW.Emitter(allow, stream=buf)
        inner: dict = {}

        def call():
            try:
                return fn(*args)
            except R.SourceUnavailable as e:
                inner["status"], inner["what"] = e.status, e.what
            except RP.ReparcelRefused as e:
                inner["status"], inner["what"] = e.status, f"{label}: reparcel refusal"
            return None
        try:
            with PW.StdioGuard(allow, out=buf, err=buf) as sg, PW.quiet_warnings(), PW.quiet_logging():
                out = PW.stage(em, label, call)
        except PW.StageFailed as e:
            self.stage_lines += buf.getvalue().splitlines()
            st = L.STATUS_USE_UNREADABLE if e.class_name in OS_ERROR_NAMES else L.STATUS_USE_FAILED
            raise R.SourceUnavailable(st, f"{e.class_name} at {e.stage}, {e.where}") from None
        except PW.PrintRuleViolation:
            raise R.SourceUnavailable(L.STATUS_USE_FAILED, "print-rule violation at use") from None
        self.stage_lines += buf.getvalue().splitlines()
        if sg.violations:
            raise R.SourceUnavailable(L.STATUS_USE_FAILED, f"library output off the allow-list ({sg.violations} line(s))")
        if inner:
            raise R.SourceUnavailable(inner["status"], inner["what"])
        return out

    # ---- the door ------------------------------------------------------------------------------------------------
    def spec(self) -> dict:
        return {"kind": self.kind, "roots": self.roots.to_spec()}

    def real_path(self, path) -> Path:
        p = super().real_path(path)
        self.admitted.append(str(Path(p)))
        return p

    def path(self, p) -> Path:   # wp3_material.Door's interface (reparcel_object)
        try:
            return self.real_path(p)
        except PermissionError:
            raise R.SourceUnavailable(L.STATUS_QUARANTINE, "a source path under the quarantine") from None

    def read_bytes(self, p) -> bytes:
        return self.path(p).read_bytes()

    def pinned(self, key: str) -> bytes:
        path, sha = self.roots.pin(key)
        data = self.read_bytes(path)
        if sha is None:
            sha = (self._manifest().get("pins", {}).get("references", {}).get(key) or {}).get("sha256")
            if sha is None:
                raise R.SourceUnavailable(L.STATUS_PENDING, f"reference {key}: no phase-2 first-use record")
        if WG.sha256_bytes(data) != sha:
            raise R.SourceUnavailable(L.STATUS_MAP_CHANGED, f"reference {key}: sha256 differs from its pin")
        return data

    def _cached(self, key, fn):
        if key not in self._c:
            self._c[key] = fn()
        return self._c[key]

    # ---- the phase-2 manifest and its objects -------------------------------------------------------------------
    def _manifest(self) -> dict:
        def f():
            p = self.roots.latest_manifest()       # the latest FINAL version (partial manifests are never read)
            if p is None:
                if self.roots.partial_manifests():
                    raise R.SourceUnavailable(L.STATUS_NOT_FINAL, "only partial phase-2 manifests exist")
                raise R.SourceUnavailable(L.STATUS_PENDING, "the phase-2 manifest is absent")
            data = self.read_bytes(p)
            doc = json.loads(data.decode("utf-8"))
            if doc.get("schema") != L.MANIFEST_SCHEMA or doc.get("gate") != L.GATE or doc.get("final") is not True:
                raise R.SourceUnavailable(L.STATUS_PENDING, "the phase-2 manifest is not a final WP3 manifest")
            doc["_sha256"] = WG.sha256_bytes(data)
            return doc
        return self._cached("manifest", f)

    def _entry(self, key: str) -> dict:
        e = self._manifest()["objects"].get(key)
        if e is None:
            raise R.SourceUnavailable(L.STATUS_PENDING, f"phase-2 object {key} absent from the manifest")
        return e

    def _object(self, key: str, sub: str):
        def f():
            e = self._entry(key)
            if e.get("status") != FE.STATUS_EXTRACTED:
                st = L.STATUS_MAP_CHANGED if e.get("identity_result") == ID.STATUS_CHANGED else \
                    L.STATUS_STAGE_REFUSED % e.get("status")
                raise R.SourceUnavailable(st, f"phase-2 object {key}")
            rp = self.path(Path(self.roots.records) / e["record_path"])     # the door first: a quarantine path keeps
            op = self.path(Path(self.roots.artifacts) / e["object_path"])   # its own refusal status
            if not (rp.exists() and op.exists()):
                raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"phase-2 record or object {key} absent")
            rb = self.read_bytes(rp)
            if WG.sha256_bytes(rb) != e["record_sha256"]:
                raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"phase-2 record {key}")
            rec = json.loads(rb.decode("utf-8"))
            if e.get("completion_record") is not None:   # fix round 5: a crashed step 6 completed by the resume
                cp = self.path(Path(self.roots.records) / e["completion_record"])
                cb = self.read_bytes(cp) if cp.exists() else b""
                if WG.sha256_bytes(cb) != e.get("completion_sha256"):     # re-hashed before it is parsed
                    raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"phase-2 completion record {key}")
                comp = json.loads(cb.decode("utf-8"))
                if comp.get("status") != FE.STATUS_EXTRACTED or \
                        (comp.get("completes") or {}).get("record_sha256") != e["record_sha256"] or \
                        comp.get("object_sha256") != e["object_sha256"]:
                    raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"phase-2 completion record {key}")
            elif rec.get("status") != FE.STATUS_EXTRACTED:
                raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"phase-2 record {key}: not extracted")
            if (rec.get("extraction") or {}).get("object_sha256") != e["object_sha256"]:
                raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"phase-2 record {key}: object sha256 differs")
            data = self.read_bytes(op)
            if WG.sha256_bytes(data) != e["object_sha256"]:
                raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"phase-2 object {key}")
            doc = json.loads(data.decode("utf-8"))
            if doc.get("key") != key:
                raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"phase-2 object {key}: key")
            return doc["objects"], e["object_sha256"]
        objs, sha = self._cached(("object", key), f)
        if sub not in objs:
            raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"phase-2 object {key}: part {sub} absent")
        return objs[sub], sha

    def _idrefs(self) -> dict:
        return self._cached("idrefs", lambda: L.identity_records(self.roots, self.read_bytes))

    def source_identity(self, key: str) -> dict:
        """Identity at use of a source carrier (RUN_PLAN §17): re-hashed against IDENTITY_prefreeze.json's references;
        a carrier the phase-2 stage quarantined is held to its phase-2 record (identity match at extraction)."""
        def f():
            e = self._entry(key)
            r = self._idrefs()[key]
            if e.get("quarantined"):
                if e.get("identity_result") != ID.STATUS_MATCH:
                    raise R.SourceUnavailable(L.STATUS_MAP_CHANGED, f"source {key}")
                return {"basis": "the phase-2 record (carrier quarantined after extraction)",
                        "record_sha256": e["record_sha256"]}
            lp = self.path(r["local_path"])                     # the door first (a quarantine path keeps its status)
            facts = self.guarded("identity", ID.file_facts, lp, self.quarantine_root)
            cmp = ID.compare(facts, r["refs"])
            if cmp["result"] != ID.STATUS_MATCH:
                raise R.SourceUnavailable(L.STATUS_MAP_CHANGED, f"source {key}: identity at use")
            return {"basis": "identity at use", "sha256": facts["sha256"], "bytes": facts["bytes"],
                    "checks": [c["basis"] for c in cmp["checks"]]}
        return self._cached(("identity", key), f)

    # ---- the register (TSV rows; the frozen S-build) ------------------------------------------------------------
    def _rows(self) -> dict:
        def f():
            data = LD.lf(self.read_bytes(Path(self.roots.repo) / LD.TSV_PATH))
            if hashlib.sha256(data).hexdigest() != LD.TSV_SHA256:
                raise R.SourceUnavailable(STATUS_SET, "the TSV differs from its L2 pin")
            _, rows = LD.parse_tsv_bytes(data)
            return {r.row: r for r in rows}
        return self._cached("rows", f)

    def _set_manifest(self) -> dict:
        def f():
            from . import launch as LA
            repo = Path(self.roots.repo)
            fm = LD.lf(self.read_bytes(repo / LA.MANIFEST_PATH))
            if hashlib.sha256(fm).hexdigest() != LA.MANIFEST_SHA256:
                raise R.SourceUnavailable(STATUS_SET, "the freeze manifest differs from its L3 pin")
            ent = [e for e in json.loads(fm.decode("utf-8"))["files"] if e["path"] == SET_MANIFEST_REL]
            sm = LD.lf(self.read_bytes(repo / SET_MANIFEST_REL))
            if len(ent) != 1 or hashlib.sha256(sm).hexdigest() != ent[0]["sha256"]:
                raise R.SourceUnavailable(STATUS_SET, "register_sets/MANIFEST.json differs from the freeze manifest")
            m = json.loads(sm.decode("utf-8"))
            return {s["set_id"]: s for s in m["sets"]}
        return self._cached("set_manifest", f)

    def set_doc(self, set_id: str) -> tuple[dict, str]:
        def f():
            s = self._set_manifest().get(set_id)
            if s is None:
                raise R.SourceUnavailable(STATUS_SET, f"set {set_id} not in the S-build manifest")
            data = LD.lf(self.read_bytes(Path(self.roots.repo) / "arcs/audit/register_sets" / s["json"]))
            sha = hashlib.sha256(data).hexdigest()
            if sha != s["sha256"]:
                raise R.SourceUnavailable(STATUS_SET, f"set {set_id}")
            return json.loads(data.decode("utf-8")), sha
        return self._cached(("set", set_id), f)

    # ---- AHBA builds (WP2, env/venv_ref) through their record chain --------------------------------------------
    def build_output(self, name: str, key: str) -> tuple[pd.DataFrame, str]:
        """A WP2 build output read with A1's default reader, through the chain a1_builds MANIFEST -> build_record ->
        file sha256 -> default-reader frame hash; against the phase-2 pins when the manifest exists."""
        def f():
            b = Path(self.roots.builds)
            man = json.loads(self.read_bytes(b / "MANIFEST.json").decode("utf-8"))
            rb = self.read_bytes(b / name / "build_record.json")
            if WG.sha256_bytes(rb) != man["builds"][name]["record_sha256"]:
                raise R.SourceUnavailable(STATUS_BUILD, f"build {name}: record")
            rec = json.loads(rb.decode("utf-8"))
            hits = [o for o in rec["outputs"] if o.get("role") in ("matrix", "counts") and build_file_key(o) == key]
            if len(hits) != 1:
                raise R.SourceUnavailable(STATUS_BUILD, f"build {name}: output {key}")
            o = hits[0]
            p_out = self.path(b / name / o["file"])            # the door first; the read inside section 8's handler
            data = self.guarded("read:file", p_out.read_bytes)       # fix round 4, item 6
            sha = WG.sha256_bytes(data)
            if sha != o["sha256"]:
                raise R.SourceUnavailable(STATUS_BUILD, f"build {name}: output {key} sha256")
            if self.roots.manifest_path.exists():
                pins = (self._manifest().get("pins", {}).get(L.AHBA_BUILDS_KEY) or {}).get("builds", {})
                want = ((pins.get(name) or {}).get("files") or {}).get(key)
                if want is not None and want != sha:
                    raise R.SourceUnavailable(STATUS_BUILD, f"build {name}: output {key} vs the phase-2 pins")
            gz = o["file"].endswith(".gz")
            df = self.guarded("read:file", lambda: pd.read_csv(io.BytesIO(data), index_col=0,
                                                                compression="gzip" if gz else None))
            if AB.frame_sha(df) != o["sha256_default"]:
                raise R.SourceUnavailable(STATUS_BUILD, f"build {name}: output {key} default-reader frame hash")
            return df, sha
        return self._cached(("build", name, key), f)

    # ---- context, counts --------------------------------------------------------------------------------------
    def _context_files(self, cls: str) -> list[Path]:
        import e3_plants
        atlas = CLASS_ATLAS[cls]
        if Path(A3.AHBA).resolve() != Path(self.roots.ahba).resolve():
            raise R.SourceUnavailable(STATUS_BUILD, "a3_port reads another AHBA directory than the layout names")
        files = [Path(A3.AHBA) / f"{atlas}_expr.csv.gz", Path(A3.AHBA) / f"{atlas}_atlas_info.csv",
                 Path(A3.AHBA) / f"{atlas}_centroids.csv", Path(e3_plants.GAMBA_CSV)]
        if cls == "MIST64":
            files.append(Path(AD.MIST64_CLASSES_JSON))
        return files

    def context(self, cls):
        if cls not in CLASS_ATLAS:
            raise R.SourceUnavailable(R.REFUSED_CLASS, f"class {cls}")

        def f():
            for p in self._context_files(cls):
                self.path(p)                       # the door, before the builder opens them
                rp = Path(p).resolve()             # ... and the resolved path (a worktree's artifacts junction):
                if rp != Path(p):                  # launch.matrix_first_use opens the resolved path
                    self.path(rp)
            ctx = AD.build_context_checked(cls)
            tab, csha = self.build_output(f"primary-{CLASS_ATLAS[cls]}", "counts")
            ids = [int(i) for i in ctx.parcel_ids]
            missing = [i for i in ids if i not in tab.index]
            if missing:
                raise R.SourceUnavailable(STATUS_BUILD, f"class {cls}: parcels without a count row")
            counts = {i: int(tab.loc[i, "n_samples"]) for i in ids}
            donors = {i: int(tab.loc[i, "n_donors"]) for i in ids}
            sha = sha_json([cls, ctx.report.get("matrix_sha256"), csha, ids, ctx.report.get("a1_class_rule")])
            return ctx, counts, donors, sha, csha
        ctx, counts, _, sha, _ = self._cached(("context", cls), f)
        return ctx, dict(counts), sha

    def donor_counts(self, cls):
        self.context(cls)
        _, _, donors, _, csha = self._c[("context", cls)]
        return dict(donors), sha_json(["n_donors", cls, csha])

    # ---- maps ---------------------------------------------------------------------------------------------------
    def _map_binding(self, plan: dict) -> tuple[str, object]:
        text = self._rows()[int(plan["row"])]["map"]
        seg = [im for im, pre in L.SEGURA_MAP_PREFIX.items() if text.startswith(pre)]
        mor = [sh for sh, t in L.MOREAU_SHEET_TEXT.items() if t in text]
        if len(seg) == 1 and not mor:
            return "segura", seg[0]
        if len(mor) == 1 and not seg:
            return "moreau", mor[0]
        raise R.SourceUnavailable(STATUS_NO_LOADER, "map (no WP3 binding)")

    def segura_vaal(self, image: int) -> tuple[dict, dict, str]:
        """The phase-2 re-parcellation object of a Segura image, its source's identity at use and the recomputation
        check (the re-parcellation from the source equals the saved object bit for bit)."""
        key = L.SEGURA_MAP_KEY[image]
        obj, osha = self._object(key, "vaal")
        ident = self.source_identity(key)
        if ident.get("sha256") is not None and obj["source_sha256"] != ident["sha256"]:
            raise R.SourceUnavailable(L.STATUS_MAP_CHANGED, f"source {key}: object of another volume")

        def check():
            r = self._idrefs()[key]
            lp = self.path(r["local_path"])                 # the door first, then the read inside section 8's handler
            again = self.guarded("read:file", lambda: WM.reparcel_object(self, lp.read_bytes(), image))
            if again["source_sha256"] != obj["source_sha256"]:
                raise R.SourceUnavailable(L.STATUS_MAP_CHANGED, f"source {key}: changed between hash and parse")
            if again["ids"] != obj["ids"] or again["values"] != obj["values"]:
                raise R.SourceUnavailable(L.STATUS_OBJECT_CHANGED, f"phase-2 object {key}: recomputation differs")
            return True
        if ident.get("sha256") is not None:
            self._cached(("recompute", key), check)
        return obj, ident, osha

    def moreau_profile64(self, sheet: str) -> tuple[np.ndarray, str]:
        """The nodal profile on all 64 MIST64 parcels (roi 1 ... 64): the block's diagonal set to 0, mean over its 64
        columns (TSV row 615 'map': 'the code's definition')."""
        obj, osha = self._object(L.MOREAU_KEY, L.MOREAU_SHEET_KEY[sheet])
        self.source_identity(L.MOREAU_KEY)
        B = np.asarray(obj["values"], dtype=float)
        if B.shape != (64, 64) or list(obj["ids"]) != list(range(1, 65)) or not np.isfinite(B).all():
            raise R.SourceUnavailable(L.STATUS_LAYOUT, "Moreau block")
        B = B.copy()
        np.fill_diagonal(B, 0.0)
        return B.mean(axis=1), osha

    def map(self, plan, map_index):
        cls = plan["analysis_class"]
        how, which = self._map_binding(plan)
        self._manifest()                                # phase 2 first: nothing of a carrier before this
        ctx = self.context(cls)[0]
        ids = np.asarray(ctx.parcel_ids, dtype=np.int64)
        if how == "segura":
            if cls != "V-AAL":
                raise R.SourceUnavailable(R.REFUSED_CLASS, "a Segura map outside V-AAL")
            obj, ident, osha = self.segura_vaal(int(which))
            by = dict(zip([int(i) for i in obj["ids"]], obj["values"]))
            y = np.array([np.nan if by.get(int(i)) is None else float(by[int(i)]) for i in ids], dtype=float)
            src = ident.get("sha256") or ident.get("record_sha256")
        else:
            if cls != "MIST64":
                raise R.SourceUnavailable(R.REFUSED_CLASS, "a Moreau map outside MIST64")
            prof, osha = self.moreau_profile64(str(which))
            y = np.array([prof[int(i) - 1] for i in ids], dtype=float)
            ident = self.source_identity(L.MOREAU_KEY)
            src = ident.get("sha256") or ident.get("record_sha256")
        mi = int(map_index)
        return y, ids, cls, {f"map[{mi}]": R.arr_sha(y, ids), f"map[{mi}] phase-2 object": osha,
                             f"map[{mi}] source carrier": src,
                             f"map[{mi}] phase-2 manifest": self._manifest()["_sha256"]}   # fix round 1 (c)

    def reparcellated(self, plan) -> bool:
        """R27 (amendment 5 :230-232): a Segura map is re-parcellated (volume -> V-AAL, register §1.7); Moreau's is
        native MIST64."""
        try:
            how, _ = self._map_binding(plan)
        except R.SourceUnavailable:
            return False
        return how == "segura"

    # ---- sets ----------------------------------------------------------------------------------------------------
    def gene_set(self, plan):
        doc, sha = self.set_doc(plan["set_id"])
        cls = plan["analysis_class"]
        uni = (doc.get("universe") or {}).get(cls)
        if uni is None:
            raise R.SourceUnavailable(STATUS_SET, f"set {plan['set_id']}: no {cls} universe")
        return list(uni["columns"]), sha

    def component(self, plan):
        raise R.SourceUnavailable(L.STATUS_NO_FIXED_COMPONENT, "component")

    # ---- BrainSpan ---------------------------------------------------------------------------------------------
    def brainspan(self):
        """(X genes x samples, rows (ensembl id, symbol), cols (age, structure acronym), hashes): identity at use against
        the TSV's sha256 and the phase-2 record's first-use hashes; declared columns only."""
        def f():
            e = self._entry(L.BRAINSPAN_KEY)
            if e.get("status") != ID.STATUS_MATCH:
                raise R.SourceUnavailable(L.STATUS_MAP_CHANGED, "BrainSpan")
            files = e.get("files") or {}
            blobs, hashes = {}, {}
            for k in ("brainspan_expr", "brainspan_rows", "brainspan_cols"):
                path, pin = self.roots.pin(k)
                data = self.guarded("identity", self.path(path).read_bytes)
                h = WG.sha256_bytes(data)
                if (pin is not None and h != pin) or h != files.get(k):
                    raise R.SourceUnavailable(L.STATUS_MAP_CHANGED, f"BrainSpan {k}: identity at use")
                blobs[k], hashes[k] = data, h
            X, rows, cols = self.guarded("read:file", WG.brainspan_frames, blobs["brainspan_expr"],
                                         blobs["brainspan_rows"], blobs["brainspan_cols"])
            return X, rows, cols, hashes
        return self._cached("brainspan", f)

    def trajectories(self, cls):
        def f():
            X, rows, cols, hashes = self.brainspan()
            T, info = WG.brainspan_trajectories(X, list(rows["gene_symbol"].astype(str)), list(cols["age"]),
                                                list(cols["structure_acronym"]))
            return T, R.arr_sha(T.to_numpy(), np.array(list(T.index), dtype=str))
        T, sha = self._cached("trajectories", f)
        return T.copy(), sha

    # ---- reference tables ----------------------------------------------------------------------------------
    def hgnc(self) -> WG.HGNCTable:
        return self._cached("hgnc", lambda: WG.HGNCTable(self.pinned("hgnc")))

    def gamba_hgnc(self) -> tuple[list, str]:
        def f():
            data = self.pinned("gamba")
            syms = WG.gamba_brain_symbols(data)
            hg = self.hgnc()
            mapped = sorted({m for m in (hg.symbol(s)[0] for s in syms) if m})
            return mapped, WG.sha256_bytes(data)
        return self._cached("gamba", f)

    def dk_table(self) -> pd.DataFrame:
        return self._cached("dk", lambda: pd.read_csv(io.BytesIO(self.pinned("dk_info"))))

    # ---- Liu (R10, R42) --------------------------------------------------------------------------------------
    def _liu_traj(self):
        def f():
            X, rows, cols, _ = self.brainspan()
            hg = self.hgnc()
            mapped, how = hg.map_columns(list(rows["gene_symbol"]),
                                         kinds_ids=[("ensembl", e) for e in rows["ensembl_gene_id"]])
            T, info = WG.brainspan_trajectories(X, mapped, list(cols["age"]), list(cols["structure_acronym"]))
            return T, R.arr_sha(T.to_numpy(), np.array(list(T.index), dtype=str)), mapped, how
        return self._cached("liu_traj", f)

    def _sd7_identity(self) -> dict:
        """Identity at use of SD7's registered copy (R46 (a)): re-hashed against its sha256 and size; a copy the
        phase-2 stage quarantined is held to its phase-2 record (identity match at extraction)."""
        def f():
            e = self._entry("liu_sd7_labels")
            objs = self._manifest()["objects"]
            if e.get("quarantined") or any((objs.get(k) or {}).get("quarantined")
                                           for k in ("liu_sd7_values", "liu_sd7_step6")):
                if e.get("identity_result") != ID.STATUS_MATCH:
                    raise R.SourceUnavailable(L.STATUS_MAP_CHANGED, "SD7")
                return {"basis": "the phase-2 record (carrier quarantined after both passes)"}
            path, sha, nbytes, _ = self.roots.sd7_copy
            lp = self.path(path)
            facts = self.guarded("identity", ID.file_facts, lp, self.quarantine_root)
            if facts["sha256"] != sha or (nbytes is not None and facts["bytes"] != nbytes):
                raise R.SourceUnavailable(L.STATUS_MAP_CHANGED, "SD7: identity at use")
            return {"basis": "identity at use", "sha256": facts["sha256"]}
        return self._cached(("identity", "sd7"), f)

    def sd7_labels(self) -> tuple[dict, str]:
        """R46 (e): pass 1's record - T4 / T5 are computed from it alone. A pass-1 refusal (identity, sheet, header,
        interrupted block) reads as a fail-closed record with its status, which forms.sd7_from_record raises."""
        from . import forms as FM
        from . import wp3_sd7 as SD
        objs = self._manifest()["objects"]
        if "liu_sd7_labels" not in objs:
            e = self._entry(L.SD7_KEY)
            raise R.SourceUnavailable(e.get("status") or L.STATUS_PENDING, "SD7")
        e = objs["liu_sd7_labels"]
        if e.get("status") == FE.STATUS_EXTRACTED:
            self._sd7_identity()
            return self._object("liu_sd7_labels", "sd7")
        if e.get("status") in (ID.STATUS_CHANGED, SD.SD7_SHEET, SD.SD7_HEADER, SD.SD7_INTERRUPTED, FM.SD7_UNMATCHED):
            return {"status": e["status"], "counts": {}}, e.get("record_sha256")
        raise R.SourceUnavailable(L.STATUS_STAGE_REFUSED % e.get("status"), "SD7 pass 1")

    def sd7_values(self) -> tuple[list, str]:
        """R46 (f): pass 2's values (None: a missing token), for the comparator only."""
        from . import wp3_sd7 as SD
        e = self._entry("liu_sd7_values")
        if e.get("status") != FE.STATUS_EXTRACTED:
            st = e.get("status")
            raise R.SourceUnavailable(st if st == SD.SD7_NON_NUMERIC else
                                      "not computable (SD7 pass 2: %s)" % st, "SD7 pass 2")
        self._sd7_identity()
        val, s2 = self._object("liu_sd7_values", "sd7")
        return list(val["values_by_position"]), s2

    def sd7_record(self) -> tuple[dict, list, str]:
        """(pass 1's record, pass 2's values or [], a hash of both): kept for the dry calls and tests."""
        lab, s1 = self.sd7_labels()
        if lab.get("status") != "matched":
            return lab, [], s1
        try:
            vals, s2 = self.sd7_values()
        except R.SourceUnavailable:
            return lab, [], s1
        return lab, vals, hashlib.sha256((s1 + s2).encode("ascii")).hexdigest()

    def liu_group_counts(self, groups: dict) -> dict:
        """R49: our BrainSpan sample counts of the registered groups (declared metadata columns only)."""
        _, _, cols, _ = self.brainspan()
        acr = [str(x).strip() for x in cols["structure_acronym"]]
        return {g: sum(1 for a in acr if a in set(members)) for g, members in groups.items()}

    def moesm2(self, part: str) -> tuple[dict, str]:
        """R47: MOESM2's phase-2 object ('s7' / 's6'); its pinned copy re-hashed at use against s_extract's sha256."""
        from . import wp3_repro as WR
        e = self._entry(L.MOESM2_KEY)
        if e.get("identity_result") == ID.STATUS_CHANGED or e.get("status") == ID.STATUS_CHANGED:
            raise R.SourceUnavailable(WR.MOESM2_CHANGED, "MOESM2")
        if e.get("status") != FE.STATUS_EXTRACTED:
            raise R.SourceUnavailable(L.STATUS_STAGE_REFUSED % e.get("status"), "MOESM2")
        if e.get("readback") != "pass":
            raise R.SourceUnavailable((WR.S7_NOT if part == "s7" else WR.S6_NOT) % "read-back", "MOESM2")

        def ident():
            path, sha = self.roots.pin("segura_moesm2")
            h = WG.sha256_bytes(self.guarded("identity", self.path(path).read_bytes))
            if h != sha:
                raise R.SourceUnavailable(WR.MOESM2_CHANGED, "MOESM2: identity at use")
            return True
        self._cached(("identity", L.MOESM2_KEY), ident)
        return self._object(L.MOESM2_KEY, part)

    def liu_inputs(self, plan) -> dict:
        spec = plan["liu_spec"]
        self._manifest()
        doc, ssha = self.set_doc(plan["set_id"])
        members = list(doc["members_hgnc"])
        hg = self.hgnc()
        brain, gsha = self.gamba_hgnc()
        traj, tsha, _, _ = self._liu_traj()
        hashes = {"set": ssha, "gamba": gsha, "traj (HGNC-keyed BrainSpan)": tsha,
                  "phase-2 manifest": self._manifest()["_sha256"],                         # fix round 1 (c)
                  "hgnc": self.roots.pin("hgnc")[1] or WG.sha256_bytes(self.pinned("hgnc"))}
        if spec["data"] == "brainspan":
            X, rows, cols, bh = self.brainspan()
            _, _, mapped, how = self._liu_traj()
            keep = [k for k, m in enumerate(mapped) if m]
            expr = pd.DataFrame(X[keep].T, columns=[mapped[k] for k in keep])
            meta = pd.DataFrame({"age": list(cols["age"]), "structure_acronym": list(cols["structure_acronym"])})
            hashes.update({f"brainspan {k}": v for k, v in bh.items()})
            rec = dict(data="brainspan", n_samples=int(X.shape[1]), n_rows=int(X.shape[0]), n_rows_mapped=len(keep),
                       hgnc_mapping=how, rule="the S-build's HGNC rule: the Ensembl id, else the symbol (U-W3-5)")
            return dict(data="brainspan", expr=expr, meta=meta, scale="RPKM", set=members, brain=brain, traj=traj,
                        hashes=hashes, loader_record=rec)
        lab, sd7sha = self.sd7_labels()            # R46 (e): T4 / T5 from pass 1 alone
        df, ssha2 = self.build_output("r10-liu-dk-samples", "matrix")
        labels = [int(i) for i in df.index]
        mapped, how = hg.map_columns([str(c) for c in df.columns])
        keep = [k for k, m in enumerate(mapped) if m]
        expr = pd.DataFrame(df.to_numpy(dtype=float)[:, keep], columns=[mapped[k] for k in keep])
        meta = pd.DataFrame({"label": pd.Series(labels, dtype=object)})
        hashes.update({"r10 samples": ssha2, "dk_table": self.roots.pin("dk_info")[1], "sd7": sd7sha})
        rec = dict(data="ahba", n_samples=len(labels), n_columns=int(df.shape[1]), n_columns_mapped=len(keep),
                   hgnc_mapping=how, rule="the S-build's HGNC rule on abagen's symbols (U-W3-5)")
        return dict(data="ahba", expr=expr, meta=meta, scale="abagen", set=members, brain=brain, traj=traj,
                    dk_table=self.dk_table(), sd7_normalised=lab, hashes=hashes, loader_record=rec)

    # ---- reproduction inputs (wp3_repro) -----------------------------------------------------------------------
    def decoder_genes(self, image: int) -> tuple[dict, str]:
        return self._object(L.SEGURA_DECODER_KEY[image], "genes")

    def mist64_all(self) -> tuple[pd.DataFrame, str]:
        """The MIST64 §3.1 matrix on all 64 parcels (the reproduction setting, claims_register.md §3.6), A1's default
        reader with R35's first-use check and the L7 pin of the round-trip read."""
        def f():
            from . import launch as LA
            p = self.path(Path(A3.AHBA) / "mist64_expr.csv.gz")
            df = pd.read_csv(io.BytesIO(p.read_bytes()), index_col=0, compression="gzip")
            first = LA.matrix_first_use(p, used=df)
            pin = dict(LA.AHBA_MATRIX)["mist64"]
            if first["sha256_round_trip"] != pin:
                raise R.SourceUnavailable(STATUS_BUILD, "MIST64 matrix: L7 pin")
            if df.shape[0] != 64:
                raise R.SourceUnavailable(STATUS_BUILD, "MIST64 matrix: not 64 parcels")
            return df, pin
        return self._cached("mist64_all", f)

    def perdonor_aal(self) -> tuple[list, list, str]:
        mats, shas, idx, cols = [], [], None, None
        for k in range(1, len(AB.DONORS) + 1):
            df, sha = self.build_output("perdonor-aal", f"matrix_d{k}")
            if idx is None:
                idx, cols = [int(i) for i in df.index], list(df.columns)
            elif [int(i) for i in df.index] != idx or list(df.columns) != cols:
                raise R.SourceUnavailable(STATUS_BUILD, "per-donor V-AAL matrices differ in parcels / genes")
            mats.append(df)
            shas.append(sha)
        return mats, idx, hashlib.sha256("".join(shas).encode("ascii")).hexdigest()

    def repro_bytes(self, key: str) -> bytes:
        return self.pinned(key)


# ================================================================================================================
# dry dispatch of the ungated rows (counts only)
# ================================================================================================================
def dry_counts(sources, rows=None) -> dict:
    """run.dry_dispatch over the ungated TSV rows (gate 'none') with these sources; counts per outcome and per status
    (fixed vocabulary; no row text)."""
    rows = rows if rows is not None else [r for r in R.register_for_diagnostics(R.REPO) if r.gate == "none"]
    recs = R.dry_dispatch(rows, frozenset(), plant_view=False, sources=sources)
    by_outcome, by_status = {}, {}
    for r in recs:
        by_outcome[r["outcome"]] = by_outcome.get(r["outcome"], 0) + 1
        key = f"{r['outcome']}: {r['status']}"
        by_status[key] = by_status.get(key, 0) + 1
    return {"n_rows": len(recs), "by_outcome": dict(sorted(by_outcome.items())),
            "by_outcome_status": dict(sorted(by_status.items())),
            "computing_rows": sum(1 for r in recs if r["outcome"] in ("would compute", "not run")),
            "_records": recs}
