"""WP3 phase 1 tests (RUN_PLAN.md v3.1 §8, §10, §16-§18; R10, R14, R18, R21, R22, R27; RUN_PLAN_amend_1 R35;
RUN_PLAN_amend_2 R37, R42, R43). Plain script; exits non-zero on any failure.

    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_wp3_phase1 [--scratch DIR] [--keep]
        [--skip-real-dry] [--real-go]

Material: SYNTHETIC stand-ins only (a1_audit/wp3_scratch.py) for every ungated phase-2 input; the frozen register
texts, the S-build's set files, the AHBA matrices / class contexts and the WP2 builds' count tables (allowed in phase
1). No Segura NIfTI, decoder output, Moreau workbook, Liu supplement, quarantine path, G1 / G2 material or exploration
result is opened; no statistic of a real audit map against a real set is computed.

Part D  (d) the ONE DOOR: every open made while a WP3 loader runs (builtins / io / os open, pathlib, numpy, pandas,
        gzip, zipfile, openpyxl, xlrd, nibabel) must have been admitted through RealSources.real_path first; three
        loader variants that bypass it must FAIL the check (mutations killed); a planted quarantine root is refused
        before any open.
Part A  units: the HGNC rule and the GO rule equal the frozen S-build's (synthetic tables); BrainSpan trajectories
        equal asdg.brainspan.load_trajectories bit for bit; the GAMBA rule equals e3_plants.brain_background; the
        bitset ORA equals repro.ora; the authors' PLS equals sklearn's unscaled PLSRegression; MOR-T percentiles and
        the exact tail against a Monte Carlo; R37 labels.
Part B  the material stage end to end on synthetic stand-ins: statuses, records, objects read back, the manifest;
        the print rule over everything emitted and written (no planted identifier, no sheet / column / label string);
        Moreau's access log (declared sheets only); a changed byte -> "not auditable (map changed)"; a decoder failure
        -> refused (R22's fallback downstream); a screened sheet name -> quarantine (rename, sha256 re-checked) and the
        deletion REQUEST, nothing deleted; a re-run after a final manifest is a verified no-op; SD7 pending opens
        nothing; an identifier-shaped component of a pinned copy's path -> identifier-bearing (fix round 1, B3).
Part T  (fix round 1, A3) tampering after phase 2, refused at use: a changed byte / LF->CRLF in a carrier (M1); values
        tampered with the record and manifest made consistent (M2: the recomputation); another volume's object (M13); a
        changed record (M12); BrainSpan rows_metadata (M14); SD7's second pass (M15); a quarantined carrier whose
        phase-2 identity is not a match (M16, in B); a moved carrier reads a status (A2); the manifest sha256 in hashes.
Part R  (fix round 1, B2) resumability: the reviewer's x3 scenario (a reference off its pin -> preflight refusal, no
        carrier touched; fixed -> final; third run a no-op); decoder attempts (transient failure retried, the partial
        file set aside); a subset run's partial manifest never read by the loaders; no subset run in production.
Part U  (fix round 1, C) units that can fail: Fisher / ORA sidedness (M4, M5), the MOR-T tail in exact rationals and by
        enumeration (M6), the weak-percentile boundary (M7), Entrez before symbol (M8), _write_repro written and
        guarded (M11, C (b)), no NaN in JSON (C (d)), R27's labels and power columns on synthetic rows.
Part H  (fix round 1, A1 / A2) subprocesses, the REAL process stderr: nibabel's own logger in fetch_extract's read
        stage, the material stage and at use, both import orders; a carrier moved or locked at use; the excepthook.
Part C  the loaders on the stand-ins: pending before phase 2 (no carrier opened); map / set / context / counts /
        trajectories / Liu inputs after it; identity at use; the recomputation check; a tampered object refused; the
        runner's prepare() and forms.liu_compute run on them.
Part F  reproduction wiring on the stand-ins: Segura (decoder and fallback), Moreau (PLS check, MOR-T), Liu T4 / T5.
Part E  dry dispatch of the 115 ungated rows: real data root (before phase 2: every computing row 'phase 2 material
        pending', no carrier opened) and the scratch stand-ins (every computing row 'would compute').
Part G  (--real-refs only; reference data, no carrier) G1-G2 the GO rule on the real GO 2024-01-17 files and the
        HGNC table reproduces every frozen segura_go set (members, term size, descendant count); G3 the real BrainSpan
        expression_matrix.csv has the TSV's sha256 and the declared-columns frames give asdg.brainspan's trajectories
        bit for bit (as the frozen code reads them); G4 the WP2 build outputs the loaders read pass their record
        chain in env/venv; G5 the frozen guard's name screen on the plan's PINNED Moreau sheet names (no carrier):
        the declared names give 0 hits, each do-not-open name a V hit, so phase 2 will quarantine the workbook.
"""
from __future__ import annotations

import argparse
import builtins
import dataclasses
import gzip
import io
import json
import os
import shutil
import sys
import tempfile
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--scratch", default=None)
ap.add_argument("--keep", action="store_true")
ap.add_argument("--skip-real-dry", action="store_true")
ap.add_argument("--parts", nargs="*", default=None, help="run only these later parts (B T R U F E H G); D, A, C always")
ap.add_argument("--real-refs", "--real-go", dest="real_go", action="store_true",
                help="Part G: reference data only - the GO rule on the real GO 2024-01-17 files reproduces every frozen "
                     "segura_go set; the BrainSpan frames equal the frozen rule; the WP2 build chain; the guard's screen "
                     "of the plan's pinned Moreau sheet names")
ARGS, _ = ap.parse_known_args()

from a1_audit import a3_port as A3  # noqa: E402
from a1_audit import fetch_extract as FE  # noqa: E402
from a1_audit import forms as FM  # noqa: E402
from a1_audit import identity as ID  # noqa: E402
from a1_audit import launch as LA  # noqa: E402
from a1_audit import privacy_wrap as PW  # noqa: E402
from a1_audit import real_sources as RS  # noqa: E402
from a1_audit import repro as RE  # noqa: E402
from a1_audit import reporting as RPT  # noqa: E402
from a1_audit import run as R  # noqa: E402
from a1_audit import wp3_genes as WG  # noqa: E402
from a1_audit import wp3_layout as L  # noqa: E402
from a1_audit import wp3_material as WM  # noqa: E402
from a1_audit import wp3_repro as WR  # noqa: E402
from a1_audit import wp3_scratch as SC  # noqa: E402
from a1_audit import wp3_decoder as DC0  # noqa: E402

WAITS: list = []
DC0.SLEEP = WAITS.append          # RUN_PLAN_amend_3 R45 (f)'s 10 / 30 min waits: a recording clock in the tests

REPO = R.REPO
TMP = Path(ARGS.scratch) if ARGS.scratch else Path(tempfile.mkdtemp(prefix="a1_wp3_p1_"))
TMP.mkdir(parents=True, exist_ok=True)
RESULTS: list = []
SEP = "-" * 100

# the guard's HGNC cache preset (as tests/test_material_p18_p19_p20.py): no read of the real table under E:
NO_HGNC = TMP / "no_such_hgnc_table.txt"
FE.PG.HGNC_FILE = NO_HGNC
FE.PG._HGNC = frozenset(("SLC6A4", "GRIN2B", "SCN2A", "PTEN"))


def check(name: str, ok, detail: str = "") -> bool:
    ok = bool(ok)
    RESULTS.append((name, ok))
    print(R.ascii_line(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not ok else "")),
          flush=True)
    return ok


def raises(fn, exc, status: str | None = None):
    try:
        fn()
    except exc as e:
        return status is None or getattr(e, "status", None) == status
    except Exception:  # noqa: BLE001
        return False
    return False


def rows():
    return {r.row: r for r in R.register_for_diagnostics(REPO)}


ROWS = rows()


def plan_of(n: int) -> dict:
    return R.classify(ROWS[n], frozenset())


def fresh_caches() -> None:
    A3._primary.cache_clear()
    A3.atlas_info.cache_clear()
    A3.verify_matrix.cache_clear()
    LA._FIRST_USE.clear()


# ================================================================================================================
# the open recorder (Part D)
# ================================================================================================================
class OpenRecorder:
    """Records every file open (and every admission through the sources' real_path) in one ordered event list."""

    def __init__(self, sources=None):
        self.events: list = []
        self.sources = sources
        self._undo: list = []

    def _rec(self, kind, f):
        if isinstance(f, (str, bytes, os.PathLike)):
            try:
                self.events.append((kind, os.path.normcase(os.path.abspath(os.fsdecode(os.fspath(f))))))
            except Exception:  # noqa: BLE001
                self.events.append((kind, "<unparsable path>"))

    def _wrap(self, owner, name, arg_index=0, label=None):
        orig = getattr(owner, name)
        rec = self._rec
        lab = label or f"{getattr(owner, '__name__', type(owner).__name__)}.{name}"

        def w(*a, **k):
            f = a[arg_index] if len(a) > arg_index else (k.get("file") or k.get("filename") or k.get("path")
                                                         or k.get("filepath_or_buffer") or k.get("io"))
            rec(lab, f)
            return orig(*a, **k)
        setattr(owner, name, w)
        self._undo.append((owner, name, orig))

    def __enter__(self):
        import openpyxl
        import xlrd
        import nibabel
        self._wrap(builtins, "open")
        self._wrap(io, "open")
        self._wrap(os, "open")
        for n in ("open", "read_bytes", "read_text"):          # explicit (pathlib also reaches io.open)
            self._wrap(Path, n, label=f"pathlib.Path.{n}")
        self._wrap(np, "load")
        self._wrap(np, "fromfile")
        for n in ("read_csv", "read_excel", "read_json", "read_table"):
            self._wrap(pd, n)
        self._wrap(gzip, "open")
        self._wrap(zipfile.ZipFile, "__init__", arg_index=1, label="zipfile.ZipFile")
        self._wrap(openpyxl, "load_workbook")
        self._wrap(xlrd, "open_workbook")
        self._wrap(nibabel, "load")
        if self.sources is not None:
            orig = self.sources.real_path
            rec = self._rec

            def admit(p):
                out = orig(p)
                rec("ADMIT", out)
                return out
            self.sources.real_path = admit
            self._undo.append((self.sources, "real_path", None))
        return self

    def __exit__(self, *exc):
        for owner, name, orig in reversed(self._undo):
            if orig is None:
                delattr(owner, name)
            else:
                setattr(owner, name, orig)
        return False

    @staticmethod
    def excluded(p: str) -> bool:
        if p == "<unparsable path>":
            return False
        low = p.lower()
        if low.endswith((".py", ".pyc", ".pyd", ".dll", ".so", ".pth", ".typed")):
            return True
        for pre in {sys.prefix, sys.base_prefix, sys.exec_prefix}:
            if low.startswith(os.path.normcase(os.path.abspath(pre)).lower() + os.sep):
                return True
        return False

    def violations(self) -> list:
        admitted, bad = set(), []
        for kind, p in self.events:
            if kind == "ADMIT":
                admitted.add(p)
            elif not self.excluded(p) and p not in admitted:
                bad.append((kind, p))
        return bad

    def opened(self) -> list:
        return [p for k, p in self.events if k != "ADMIT" and not self.excluded(p)]


def door_violations(src, calls) -> tuple[list, list]:
    """Run calls(src) under the recorder; (violations, exceptions as class names)."""
    excs = []
    with OpenRecorder(src) as rec:
        for c in calls:
            try:
                c(src)
            except R.SourceUnavailable as e:
                excs.append(("SourceUnavailable", e.status))
            except Exception as e:  # noqa: BLE001
                excs.append((type(e).__name__, None))
    return rec.violations(), excs


# ================================================================================================================
# the scratch stand-ins and the stage (shared by B, C, D, E, F)
# ================================================================================================================
def make_stage(name: str, **kw) -> tuple:
    root = TMP / name
    roots = SC.build_scratch(root, **kw)
    return roots


def run_stage(roots, *, fail_images=(), only=None):
    buf = io.StringIO()
    with SC.scratch_net(roots, fail_images=fail_images) as calls:
        res = WM.run_material(roots, out=buf, only=only, run_info={"mode": "scratch (synthetic stand-ins; no launch)"})
    return res, buf.getvalue(), calls


SEG_ROWS = (1, 2, 3, 10)
MOR_ROWS = (615, 616, 617, 618, 619)
LIU_ROWS = (471, 472, 473, 474)


def loader_calls():
    """The calls a WP3 run makes on its sources (one of each loader)."""
    calls = [lambda s: s.context("V-AAL"), lambda s: s.context("MIST64"), lambda s: s.donor_counts("V-AAL")]
    for n in (1, 2, 10, 615, 617):
        calls.append(lambda s, n=n: s.map(plan_of(n), 0))
    for n in (1, 10, 615):
        calls.append(lambda s, n=n: s.gene_set(plan_of(n)))
    calls.append(lambda s: s.trajectories("V-AAL"))
    for n in (471, 473):
        calls.append(lambda s, n=n: s.liu_inputs(plan_of(n)))
    calls += [lambda s: s.decoder_genes(790618), lambda s: s.perdonor_aal(), lambda s: s.mist64_all(),
              lambda s: s.repro_bytes("go_obo"), lambda s: s.sd7_record(), lambda s: s.moesm2("s7"),
              lambda s: s.moesm2("s6"), lambda s: s.liu_group_counts({"x": ("DFC",)})]
    return calls


# ================================================================================================================
# Part D: the one door
# ================================================================================================================
def part_d(roots) -> None:
    print(SEP + "\nPart D: every open of a WP3 loader goes through RealSources.real_path; mutations killed")
    fresh_caches()
    src = RS.WP3Sources(roots)
    viol, excs = door_violations(src, loader_calls())
    check("D1 WP3Sources: every open admitted through real_path first (0 violations)", not viol,
          f"{len(viol)} violation(s): {[k for k, _ in viol][:5]}")
    check("D1 every loader call succeeded on the stand-ins", not excs, str(excs[:4]))
    check("D1 the recorder saw opens of the stand-ins and of the AHBA context files",
          len(src.admitted) > 20, f"{len(src.admitted)} admitted")

    class BypassSet(RS.WP3Sources):            # mutation 1: the set file read with open(), not through the door
        def set_doc(self, set_id):
            s = self._set_manifest()[set_id]
            p = Path(self.roots.repo) / "arcs/audit/register_sets" / s["json"]
            with open(p, "rb") as f:
                data = f.read()
            return json.loads(data.decode("utf-8")), s["sha256"]

    class BypassRead(RS.WP3Sources):           # mutation 2: every read bypasses the door
        def read_bytes(self, p):
            return Path(p).read_bytes()

    class BypassContext(RS.WP3Sources):        # mutation 3: the context builder's files not admitted first
        def _context_files(self, cls):
            return []

    for name, cls, calls in (("set file via open()", BypassSet, [lambda s: s.gene_set(plan_of(1))]),
                             ("reads via Path.read_bytes", BypassRead, [lambda s: s.map(plan_of(615), 0)]),
                             ("context files not admitted", BypassContext, [lambda s: s.context("V-AAL")])):
        fresh_caches()
        v, _ = door_violations(cls(roots), calls)
        check(f"D2 mutation killed: {name} -> the check fails ({len(v)} violation(s))", len(v) > 0)
    # a planted quarantine path: the objects' root under the quarantine -> refused before any open
    qroots = dataclasses.replace(roots, artifacts=str(Path(roots.quarantine) / "ungated" / "planted"))
    qsrc = RS.WP3Sources(qroots)
    with OpenRecorder(qsrc) as rec:
        ok = raises(lambda: qsrc.map(plan_of(615), 0), R.SourceUnavailable, L.STATUS_QUARANTINE)
    under_q = [p for p in rec.opened() if any(x.casefold() == "_quarantine" for x in Path(p).parts)]
    check("D3 a planted quarantine path: the loader reads 'refused: ... under the quarantine', nothing under it opened",
          ok and not under_q, f"{len(under_q)} opened")
    check("D3 run.RealSources.real_path itself refuses a '_quarantine' component (PermissionError)",
          raises(lambda: qsrc.real_path(Path(roots.data) / "_quarantine" / "x.json"), PermissionError))


# ================================================================================================================
# Part A: units
# ================================================================================================================
def _syn_hgnc_table(path: Path) -> bytes:
    rows = []
    for k, (sym, prev, alias) in enumerate([("AAA1", "OLDA|SHARED", ""), ("BBB2", "SHARED", "BX"), ("CCC3", "", "BX|CY"),
                                            ("DDD4", "", ""), ("EEE5", "OLDE", "")]):
        rows.append({"hgnc_id": f"HGNC:{k + 1}", "symbol": sym, "status": "Approved", "prev_symbol": prev,
                     "alias_symbol": alias, "ensembl_gene_id": f"ENSG0000{k}" if k != 3 else "",
                     "entrez_id": str(100 + k), "uniprot_ids": f"P{k}|Q{k}", "rna_central_id": ""})
    b = pd.DataFrame(rows).to_csv(sep="\t", index=False, lineterminator="\n").encode("utf-8")
    path.write_bytes(b)
    return b


def part_a() -> None:
    print(SEP + "\nPart A: units (synthetic)")
    sys.path.insert(0, str(REPO / "arcs/audit/src_register"))
    import s_build as SB
    d = TMP / "unit"
    d.mkdir(parents=True, exist_ok=True)
    hp = d / "hgnc.txt"
    hb = _syn_hgnc_table(hp)
    orig_pinned = SB.pinned
    try:
        SB.pinned = lambda key: hp
        frozen = SB.HGNC()
        mine = WG.HGNCTable(hb)
        probes = ["AAA1", "OLDA", "SHARED", "BX", "CY", "DDD4", " EEE5 ", "", None, 5, "ZZZ"]
        same = all(frozen.symbol(s) == mine.symbol(s) for s in probes)
        idp = [("ensembl", "ENSG00001.3", "zz"), ("entrez", "102", "x"), ("uniprot", "Q4-2", "EEE5"),
               ("ensembl", "ENSG99", "OLDA"), ("hgnc", "HGNC:4", "x"), ("nongene", "C1", "x"), (None, None, "BX")]
        same2 = all(frozen.resolve(*a) == mine.resolve(*a) for a in idp)
        check("A1 HGNC rule: symbol() and resolve() equal the frozen s_build.HGNC on a synthetic table", same and same2)
        # GO rule against s_build.GO on synthetic files
        genes = ["AAA1", "BBB2", "CCC3", "DDD4", "EEE5"]
        ids = {g: (None, None) for g in genes}
        obo, gaf = SC.synthetic_go(genes * 6, {g: (None, None) for g in genes}, np.random.default_rng(3))
        gaf_txt = gzip.decompress(gaf).decode("utf-8").split("\n")
        gaf_txt = [ln if ln.startswith("!") or not ln else
                   ln.replace(ln.split("\t")[1], f"P{genes.index(ln.split(chr(9))[2])}", 1) for ln in gaf_txt]
        gaf = gzip.compress("\n".join(gaf_txt).encode("utf-8"), mtime=0)
        (d / "go.obo").write_bytes(obo)
        (d / "go.gaf.gz").write_bytes(gaf)
        SB.pinned = lambda key: d / ("go.obo" if key.endswith("_obo") else "go.gaf.gz")
        fgo = SB.GO("syn")
        mgo = WG.GOTerms(obo, gaf)
        terms = mgo.live_terms()
        same3 = all(fgo.members(t) == mgo.raw_members(t) for t in terms)
        check("A2 GO rule: raw members equal the frozen s_build.GO.members on every synthetic term "
              f"({len(terms)} live BP terms; NOT / ND excluded; part_of followed)", same3 and len(terms) >= 10)
        idx = {g: k for k, g in enumerate(genes)}
        bits = mgo.term_gene_bits(mine, idx)
        same4 = all(bits[t] == WR.bits_of(WG.resolve_raw(mine, mgo.raw_members(t)[0])[0], idx) for t in terms)
        check("A2 GO bitsets equal raw members resolved by the HGNC rule (the S-build's build_set resolution)", same4)
        check("A2 the obsolete synthetic term is not live", "GO:9000099" not in terms)
        _ = ids
    finally:
        SB.pinned = orig_pinned
    # BrainSpan trajectories = the frozen load_trajectories
    import asdg.brainspan as BS
    rng = np.random.default_rng(7)
    hgb, hid = SC.synthetic_hgnc(SC.SYN_GENES[:80])
    bs = SC.synthetic_brainspan(rng, SC.SYN_GENES[:80], hid, SC.SYN_GENES[:10])
    bdir = d / "bs"
    bdir.mkdir(exist_ok=True)
    for k, v in bs.items():
        (bdir / k).write_bytes(v)
    old = BS.DIR
    try:
        BS.DIR = bdir
        T0, info0 = BS.load_trajectories()
    finally:
        BS.DIR = old
    X, rws, cls = WG.brainspan_frames(bs["expression_matrix.csv"], bs["rows_metadata.csv"], bs["columns_metadata.csv"])
    T1, info1 = WG.brainspan_trajectories(X, list(rws["gene_symbol"].astype(str)), list(cls["age"]),
                                          list(cls["structure_acronym"]))
    check("A3 BrainSpan trajectories = asdg.brainspan.load_trajectories bit for bit (synthetic directory)",
          T0.equals(T1) and info0 == {k: info1[k] for k in info0})
    check("A3 the declared sample columns only enter the frames (donor columns never read)",
          list(cls.columns) == ["age", "structure_acronym"] and list(rws.columns) == ["ensembl_gene_id", "gene_symbol"])
    # GAMBA rule = e3_plants.brain_background
    import e3_plants
    from asdg.genesets import Universe
    gb = SC.synthetic_gamba(SC.SYN_GENES[:200])
    gb2 = gb + b"SYNG0001,0\n"                     # a conflicting duplicate: dropped by both
    (d / "gamba.csv").write_bytes(gb2)
    oldg = e3_plants.GAMBA_CSV
    try:
        e3_plants.GAMBA_CSV = d / "gamba.csv"
        U = Universe(pd.DataFrame(np.random.default_rng(1).normal(size=(5, 60)), columns=SC.SYN_GENES[:60]))
        ref = e3_plants.brain_background(U)
    finally:
        e3_plants.GAMBA_CSV = oldg
    sym = WG.gamba_brain_symbols(gb2)
    mine_idx = np.array(sorted(U.index[g] for g in sym if g in U.index))
    check("A4 GAMBA brain>body symbols = e3_plants.brain_background on a synthetic table (conflicting duplicate "
          "dropped)", np.array_equal(ref, mine_idx) and "SYNG0001" not in sym)
    check("A4 a flag count other than 2,711 is refused", raises(lambda: WG.gamba_brain_symbols(gb2.replace(
        b"GAMBASYN00000,1", b"GAMBASYN00000,0")), ValueError))
    # bitset ORA = repro.ora
    rng = np.random.default_rng(11)
    ref_g = [f"G{k}" for k in range(300)]
    terms = {f"T{k}": set(rng.choice(ref_g + ["OUT1", "OUT2"], int(rng.integers(0, 40)), replace=False)) for k in range(25)}
    terms["T_empty"] = {"OUT1"}
    lst = set(rng.choice(ref_g, 30, replace=False)) | {"OUT3"}
    o1 = RE.ora(lst, terms, ref_g)
    idx = WR.gene_index(ref_g, *terms.values(), lst)
    o2 = WR.ora_bits(WR.bits_of(lst, idx), {k: WR.bits_of(v, idx) for k, v in terms.items()}, WR.bits_of(ref_g, idx))
    keys = ("a", "b", "c", "d", "p_greater", "p_two_sided", "q_greater", "q_two_sided", "p_primary", "q_primary",
            "fold_enrichment", "odds_ratio_conditional_mle")
    same = all(o1["terms"][t]["status"] == o2["terms"][t]["status"] and
               (o1["terms"][t]["status"] != "tested" or all(
                   (o1["terms"][t][k] == o2["terms"][t][k]) or (np.isnan(o1["terms"][t][k]) and np.isnan(o2["terms"][t][k]))
                   for k in keys)) for t in terms)
    check("A5 the bitset ORA equals repro.ora term by term (counts, both p's, both BH q's, the primary)", same
          and o1["n_tested"] == o2["n_tested"] and o2["primary"] == "two-sided"
          and o2["label"] == "PANTHER sidedness unverified" and o2["empirical_check"]["result"].startswith("PANTHER"))
    # the authors' PLS
    from sklearn.cross_decomposition import PLSRegression
    rng = np.random.default_rng(5)
    Xp = rng.normal(size=(64, 24)) * rng.uniform(0.2, 4, 24)
    yp = Xp[:, :3] @ np.array([1.0, -0.5, 0.2]) + rng.normal(0, 2, 64)
    mine_r2 = WR.pls_cum_r2(yp, Xp)["R2"]
    sk = PLSRegression(n_components=2, scale=False).fit(Xp, yp).score(Xp, yp)
    sk_scaled = PLSRegression(n_components=2, scale=True).fit(Xp, yp).score(Xp, yp)
    check("A6 cumulative R^2 of the centred unscaled 2-component PLS = sklearn PLSRegression(scale=False) (1e-10)",
          abs(mine_r2 - sk) < 1e-10, f"{mine_r2} vs {sk}")
    check("A6 must-differ: the scaled PLS gives another R^2 (the check can fail)", abs(sk_scaled - sk) > 1e-6)
    # MOR-T percentiles and the exact tail
    rng = np.random.default_rng(9)
    M = pd.DataFrame(rng.normal(size=(64, 500)), columns=[f"G{k}" for k in range(500)])
    y64 = M.iloc[:, :5].to_numpy().mean(1) + rng.normal(0, 0.3, 64)
    pub = ROWS[618]["published_value_and_location"]
    M = M.rename(columns={"G0": "MVP", "G1": "KIF22"})
    tl = WR.mor_t_tail(y64, M, ["MVP", "KIF22", "G2", "G3", "G4", "G10"], 618, pub)
    r = WR.per_gene_r(y64, M.to_numpy())
    direct = 100.0 * (r <= r[0]).mean()
    G, K, k = 500, tl["tails"]["98"]["n_genes_above"], tl["tails"]["98"]["k_set_above"]
    mc = np.mean([(np.argsort(np.argsort(-r))[rng.choice(500, 6, replace=False)] < K).sum() >= k for _ in range(20000)])
    check("A7 MOR-T: the named gene's weak percentile = 100 x share of r <= its r", abs(tl["named"]["MVP"]["percentile_weak"]
                                                                                     - direct) < 1e-12)
    check("A7 MOR-T: the exact hypergeometric tail agrees with 20,000 uniform random sets (|diff| < .01)",
          abs(tl["tails"]["98"]["p_exact"] - mc) < 0.01, f"{tl['tails']['98']['p_exact']} vs {mc}")
    check("A7 MOR-T: a transcription not in the TSV text is refused",
          raises(lambda: WR.mor_t_tail(y64, M, ["MVP"], 618, "no such text"), AssertionError))
    # the decoder output's declared columns (U-W3-3): required symbol + FDR q; optional Entrez / t / p
    hg5 = WG.HGNCTable(hb)
    cols = list(L.DECODER_COLUMNS)
    rows_ = [["AAA1", 100.0, "n", 2.0, 0.01, 0.02, 1, 0.1], ["OLDE", None, "n", -3.0, 0.001, 0.004, 1, 0.1],
             ["ZZZ", None, "n", 1.0, 0.5, 0.6, 1, 0.1], ["CCC3", 102.0, "n", 0.5, 0.6, None, 1, 0.1]]
    o = WM.decoder_object(json.dumps({"columns": cols, "data": rows_}).encode(), hg5, 790618)
    check("A9 decoder object: HGNC genes (Entrez id, else symbol), unmapped and non-finite q counted",
          o["genes"] == ["AAA1", "EEE5"] and o["counts"]["n_unmapped"] == 1 and o["counts"]["n_nonfinite_q"] == 1
          and WR.decoded_from_decoder(o) == {"AAA1", "EEE5"})
    no_ent = [c for c in cols if c != "entrez_id.1"]
    o2 = WM.decoder_object(json.dumps({"columns": no_ent, "data": [r[:1] + r[2:] for r in rows_]}).encode(), hg5, 1)
    check("A9 decoder object without the optional Entrez column: the symbol rule alone", o2["genes"] == ["AAA1", "EEE5"]
          and o2["optional_columns_present"] == ["p", "t"])
    no_q = [c for c in cols if c != "p (FDR corrected)"]
    check("A9 decoder object without the FDR q column, with a repeated column, or a short row: refused",
          raises(lambda: WM.decoder_object(json.dumps({"columns": no_q, "data": [r[:5] + r[6:] for r in rows_]}).encode(),
                                           hg5, 1), ValueError)
          and raises(lambda: WM.decoder_object(json.dumps({"columns": cols[:7] + ["gene_symbol"],
                                                            "data": rows_}).encode(), hg5, 1), ValueError)
          and raises(lambda: WM.decoder_object(json.dumps({"columns": cols, "data": [rows_[0][:5]]}).encode(), hg5, 1),
                     ValueError))
    c = RPT.reproduction_check(".242", 0.20, functional="R2")
    c2 = RPT.reproduction_check(".242", 0.30, functional="R2")
    check("A8 R37 (B) on R^2: .242 vs .20 reproduced; vs .30 not reproduced, never a sign label",
          c["label"] == "reproduced" and c2["label"] == "not reproduced")


# ================================================================================================================
# Part B: the material stage on synthetic stand-ins
# ================================================================================================================
def _all_written(root: Path) -> list:
    out = []
    for p in (root / "out").rglob("*"):
        if p.is_file():
            out.append(p)
    for k in (*L.SEGURA_DECODER_KEY.values(),):
        out.append(root / "data" / k / "SOURCE.md")      # the carrier itself (carrier.json) is not an output
    return out


def part_b(roots) -> dict:
    print(SEP + "\nPart B: the material stage end to end on synthetic stand-ins")
    root = Path(roots.data).parent
    res, text, calls = run_stage(roots)
    ent = res["entries"]
    exp = {**{k: FE.STATUS_EXTRACTED for k in (*L.SEGURA_MAP_KEY.values(), *L.SEGURA_DECODER_KEY.values(),
                                                L.MOREAU_KEY)}, L.BRAINSPAN_KEY: ID.STATUS_MATCH}
    check("B1 statuses: Segura x2 and decoders x2 extracted, Moreau extracted, BrainSpan identity match",
          all(ent[k]["status"] == v for k, v in exp.items()), json.dumps({k: ent[k]["status"] for k in exp}))
    check("B1 SD7 (RUN_PLAN_amend_3 R46, synthetic workbook): both passes extracted (labels first, then values)",
          ent[L.SD7_KEY]["status"].startswith("matched (pass 1)") and ent["liu_sd7_labels"]["status"] == FE.STATUS_EXTRACTED
          and ent["liu_sd7_values"]["status"] == FE.STATUS_EXTRACTED)
    check("B1 MOESM2 (R47, synthetic PDF): extracted and read back by a second parse",
          ent[L.MOESM2_KEY]["status"] == FE.STATUS_EXTRACTED and ent[L.MOESM2_KEY]["readback"] == "pass")
    lab = json.loads((Path(roots.artifacts) / ent["liu_sd7_labels"]["object_path"]).read_bytes())["objects"]["sd7"]
    check("B1 SD7 labels object: the normalised record only (positions, kinds, DK ids, counts); no label string",
          lab["status"] == "matched" and lab["n_dropped_latvent"] == 2 and lab["n_dropped_global"] == 3
          and lab["merged"] is False and all(set(e) <= {"position", "kind", "ids", "side"} for e in lab["entries"]))
    check("B1 identity: Segura and Moreau 'identity match' on every reference basis",
          all(ent[k]["identity_result"] == ID.STATUS_MATCH for k in (*L.SEGURA_MAP_KEY.values(), L.MOREAU_KEY)))
    check("B1 decoders: identity recorded at download (no pre-freeze identity)",
          all(ent[k]["identity_result"] == ID.STATUS_AT_DOWNLOAD for k in L.SEGURA_DECODER_KEY.values()))
    files = {v["file_url"] for k, v in L.identity_records(roots, lambda p: Path(p).read_bytes()).items()
             if k in L.SEGURA_MAP_KEY.values()}
    check("B1 network (R44 / R45; fix round 3, C (a)): GET of the two decoder URLs only (one curl each, no HEAD of "
          "them); one HEAD of each image file URL (the size probe)",
          sorted(c[0] for c in calls) == ["get", "get", "head", "head"]
          and {c[1] for c in calls if c[0] == "get"} == {L.DECODER_URL.format(image=i) for i in L.SEGURA_IMAGES}
          and {c[1] for c in calls if c[0] == "head"} == files)
    man = json.loads(Path(res["manifest_path"]).read_bytes())
    check("B1 the manifest: schema, every object, sha256 read back", man["schema"] == L.MANIFEST_SCHEMA and
          WG.sha256_bytes(Path(res["manifest_path"]).read_bytes()) == res["manifest_sha256"]
          and set(man["objects"]) >= set(exp))
    ok = True
    for k, e in man["objects"].items():
        if "object_path" in e:
            ok &= WG.sha256_bytes((Path(roots.artifacts) / e["object_path"]).read_bytes()) == e["object_sha256"]
        if "record_path" in e:
            ok &= WG.sha256_bytes((Path(roots.records) / e["record_path"]).read_bytes()) == e["record_sha256"]
    check("B1 every object and record re-hashes to its manifest entry", ok)
    seg = json.loads((Path(roots.artifacts) / man["objects"]["segura_790618"]["object_path"]).read_bytes())
    vaal = seg["objects"]["vaal"]
    check("B2 Segura object: every AAL id, three parcels dropped below 50 % coverage (null), the rest kept",
          len(vaal["ids"]) == 116 and sum(v is None for v in vaal["values"]) >= 3
          and vaal["report"]["min_coverage"] == 0.5 and vaal["label"] == "re-parcellated")
    mo = json.loads((Path(roots.artifacts) / man["objects"][L.MOREAU_KEY]["object_path"]).read_bytes())["objects"]
    check("B2 Moreau object: two 64 x 64 numeric blocks keyed by roi 1 ... 64",
          set(mo) == {"del16p11", "del22q11"} and all(np.asarray(mo[k]["values"]).shape == (64, 64) for k in mo))
    mrec = json.loads((Path(roots.records) / man["objects"][L.MOREAU_KEY]["record_path"]).read_bytes())
    sh = mrec["sheets"]
    check("B3 Moreau: declared sheets 2 / 2 found; undeclared never fetched; access log declared only; no undeclared "
          "worksheet part opened", sh["declared_found"] == 2 and sh["access_log_declared_only"] is True
          and sh["parts_opened_undeclared"] == 0 and sh["n_undeclared"] == 8)
    # the print rule over everything emitted and written
    blobs = [text] + [p.read_bytes().decode("utf-8", "replace") for p in _all_written(root)
                      if p.suffix in (".json", ".log", ".md")]
    # (the pinned URLs of the identity references may appear in identity records: they are not searched for; the
    # local paths' folder names are)
    forbidden = list(SC.PLANTED_IDS) + ["subject_id", "Region", "0_README", "2_16p11.2Dup", "5_BIV", "SD7_syn",
                                        "SD8_syn", "thickavg", "Lthal", "LatVent", "FDR corrected", "entrez_id",
                                        "segura2025", "repo/data/Supplementary", r"repo\data\Supplementary",
                                        r"repo\\data\\Supplementary", "/liu/sd7", r"\liu\sd7", r"\\liu\\sd7", "H376",
                                        "Supplementary Data", "supplement_syn", "moesm2_syn", "ASD_SFARI", "axonogenesis",
                                        "SYNS4", "tableS4_syn"]
    hits = {f: sum(f in b for b in blobs) for f in forbidden}
    hits = {k: v for k, v in hits.items() if v}
    check("B4 print rule: no planted identifier, sheet / column / label string or carrier file name in any output",
          not hits, json.dumps(hits))
    check("B4 the stage completed under the Emitter (a line off the allow-list stops it: PrintRuleViolation)",
          "PrintRuleViolation" not in text and "wp3_material: final manifest written" in text)
    return res


def part_b_failures() -> None:
    print(SEP + "\nPart B (failures): a changed byte, a decoder failure, a screened sheet name, no-op re-run, SD7 pending")
    roots = make_stage("stage_changed", with_sd7=False)
    p = SC.local_path(roots, "segura_790618")
    b = bytearray(p.read_bytes())
    b[100] ^= 0xFF
    p.write_bytes(bytes(b))
    res, text, calls = run_stage(roots, fail_images=(781986,))
    e = res["entries"]
    check("B5 one byte changed in a Segura stand-in -> 'not auditable (map changed)' (final), no object",
          e["segura_790618"]["status"] == ID.STATUS_CHANGED and "object_path" not in e["segura_790618"]
          and e["segura_790618"]["final"] is True)
    n_get = sum(1 for c in calls if c[0] == "get" and "781986" in c[1])
    from a1_audit import wp3_decoder as DC
    check(f"B6 a decoder failing in transport: {L.DECODER_ATTEMPTS} attempts (RUN_PLAN_amend_3 R45 (f)), then "
          "unavailable, no object (R22's fallback applies downstream)",
          e["segura_decoder_781986"]["status"] == DC.UNAVAILABLE % "three transport failures"
          and "object_path" not in e["segura_decoder_781986"]
          and e["segura_decoder_781986"]["final"] is True and n_get == L.DECODER_ATTEMPTS
          and e["segura_decoder_781986"]["transport_failures"] == L.DECODER_ATTEMPTS)
    sd7_parts = [a for a in res["admitted"] if any(x.casefold() == "liu" for x in Path(a).parts)]
    check("B9 a scratch layout without an SD7 copy: 'no SD7 copy in this scratch layout', no SD7 path admitted (by "
          "path component, not by a substring of the scratch path)", e[L.SD7_KEY]["status"] == L.STATUS_SD7_PENDING
          and roots.sd7_copy is None and not sd7_parts)
    before = sorted(str(x) for x in Path(roots.records).rglob("*.json")) + \
        sorted(str(x) for x in Path(roots.artifacts).rglob("*.json"))
    res2, _, calls2 = run_stage(roots)
    after = sorted(str(x) for x in Path(roots.records).rglob("*.json")) + \
        sorted(str(x) for x in Path(roots.artifacts).rglob("*.json"))
    check("B8 a re-run after a final manifest is a verified no-op: no record, object or manifest written, no request",
          res2.get("noop") is True and before == after and not calls2)
    # a screened sheet name: quarantine (rename), deletion request, nothing deleted
    roots2 = make_stage("stage_q", with_sd7=False)
    import openpyxl
    rec0 = json.loads(Path(roots2.identity_json).read_bytes())
    mrec = [r for r in rec0["records"] if r["object"] == L.IDENTITY_OBJECT[L.MOREAU_KEY]][0]
    mp = Path(mrec["probes"][1]["path"])
    wb = openpyxl.load_workbook(mp)
    wb.create_sheet("Subjects").append(["x"])
    bio = io.BytesIO()
    wb.save(bio)
    xb = bio.getvalue()
    mp.write_bytes(xb)
    mrec["probes"][0].update(blob_sha=ID.git_blob_of(xb), size=len(xb))
    mrec["probes"][1].update(sha256=WG.sha256_bytes(xb), size=len(xb), git_blob_sha=ID.git_blob_of(xb))
    Path(roots2.identity_json).write_bytes(json.dumps(rec0, indent=1).encode("utf-8"))
    res2, _, _ = run_stage(roots2)
    e2 = res2["entries"][L.MOREAU_KEY]
    qdir = Path(roots2.quarantine) / "ungated" / L.MOREAU_KEY
    qfiles = [x for x in qdir.rglob("*") if x.is_file()]
    reqs = list((Path(roots2.control) / "ungated").glob("*deletion_request.json"))
    check("B7 a screened sheet name -> identifier-bearing: extracted, then the whole clone moved to the quarantine "
          "(section 8.1; same volume, the workbook's sha256 re-checked), a deletion REQUEST written; nothing deleted",
          e2["status"] == FE.STATUS_EXTRACTED and e2["quarantined"] and not mp.exists()
          and any(WG.sha256_bytes(x.read_bytes()) == WG.sha256_bytes(xb) for x in qfiles) and len(reqs) == 1)
    src = RS.WP3Sources(roots2)
    y, ids, cls, h = src.map(plan_of(615), 0)
    check("B7 the loader holds a quarantined carrier to its phase-2 record (identity match at extraction) and reads "
          "its object", cls == "MIST64" and len(ids) == 46 and np.isfinite(y).all()
          and src.source_identity(L.MOREAU_KEY)["basis"].startswith("the phase-2 record"))
    check("B7 the loader never opens the quarantined carrier",
          not any(any(part.casefold() == "_quarantine" for part in Path(a).parts) for a in src.admitted))
    # M16: a quarantined carrier whose phase-2 record does not read 'identity match' is refused
    mpath = roots2.latest_manifest()
    mb = mpath.read_bytes()
    man = json.loads(mb)
    man["objects"][L.MOREAU_KEY]["identity_result"] = ID.STATUS_CHANGED
    try:
        mpath.write_bytes(json.dumps(man, indent=1).encode("utf-8"))
        check("B10 (M16) a quarantined carrier whose phase-2 identity is not a match -> 'not auditable (map changed)'",
              raises(lambda: RS.WP3Sources(roots2).map(plan_of(615), 0), R.SourceUnavailable, L.STATUS_MAP_CHANGED))
    finally:
        mpath.write_bytes(mb)
    # B3: an identifier-shaped component in a pinned copy's path
    roots3 = make_stage("stage_b3", with_sd7=False)
    sp = SC.local_path(roots3, "segura_790618")
    planted = sp.parent / "NDAR_INVAB123CDE" / sp.name
    planted.parent.mkdir()
    os.rename(sp, planted)
    rec3 = json.loads(Path(roots3.identity_json).read_bytes())
    for r in rec3["records"]:
        for q in r["probes"]:
            if q.get("path") == str(sp):
                q["path"] = str(planted)
    Path(roots3.identity_json).write_bytes(json.dumps(rec3, indent=1).encode("utf-8"))
    res3, text3, _ = run_stage(roots3)
    e3 = res3["entries"]["segura_790618"]
    rrec = json.loads((Path(roots3.records) / e3["record_path"]).read_bytes())
    q3 = Path(roots3.quarantine) / "ungated" / "segura_790618" / "carrier.nii.gz"
    check("B11 (B3) an identifier-shaped component of a pinned copy's path -> screened (V hit), identifier-bearing: "
          "extracted, quarantined under its runner-built name, deletion requested; the component never printed",
          e3["status"] == FE.STATUS_EXTRACTED and rrec["fetch"]["screen_hits"]["V"] >= 1 and rrec["identifier_bearing"]
          and e3["quarantined"] and q3.exists() and "NDAR_INVAB123CDE" not in text3
          and all("NDAR_INVAB123CDE" not in x.read_text(encoding="utf-8") for x in Path(roots3.records).rglob("*.json")))


# ================================================================================================================
# Part T: tampering at use (fix round 1, A3 / C (e)): M1, M2, M12, M13, M14, M15
# ================================================================================================================
def _manifest_edit(roots, fn):
    """Apply fn(manifest dict) to the latest final manifest (scratch only); returns the original bytes."""
    p = roots.latest_manifest()
    b = p.read_bytes()
    man = json.loads(b)
    fn(man)
    p.write_bytes(json.dumps(man, indent=1).encode("utf-8"))
    return p, b


def part_t(roots) -> None:
    print(SEP + "\nPart T: tampering after phase 2 is refused at use (M1, M2, M12, M13, M14, M15)")
    seg = SC.local_path(roots, "segura_790618")
    good = seg.read_bytes()

    def refused_identity(key, plan_n):
        """identity at use itself refuses (not only the later object-of-another-volume check) and so does the map"""
        return (raises(lambda: RS.WP3Sources(roots).source_identity(key), R.SourceUnavailable, L.STATUS_MAP_CHANGED)
                and raises(lambda: RS.WP3Sources(roots).map(plan_of(plan_n), 0), R.SourceUnavailable,
                           L.STATUS_MAP_CHANGED))
    try:
        bb = bytearray(good)
        bb[200] ^= 0x01
        seg.write_bytes(bytes(bb))
        check("T1 (M1) one byte changed in a Segura carrier at use -> identity at use refuses: 'not auditable (map "
              "changed)'", refused_identity("segura_790618", 1))
        seg.write_bytes(good.replace(b"\n", b"\r\n", 1))
        check("T2 (M1) one LF -> CRLF in a Segura carrier at use -> identity at use refuses",
              b"\n" in good and refused_identity("segura_790618", 1))
    finally:
        seg.write_bytes(good)
    check("T0 restored: the maps load (the synthetic Moreau workbook was quarantined at phase 2: its sheet names "
          "screen as identifier-bearing, as the real one's will - Part G5 - so it is held to its phase-2 record, B10)",
          RS.WP3Sources(roots).map(plan_of(1), 0)[2] == "V-AAL"
          and RS.WP3Sources(roots).map(plan_of(615), 0)[2] == "MIST64")
    # a consistently tampered object: values changed, record's object sha, manifest's object and record sha updated
    man0 = json.loads(roots.latest_manifest().read_bytes())
    e = man0["objects"]["segura_790618"]
    op, rp = Path(roots.artifacts) / e["object_path"], Path(roots.records) / e["record_path"]
    ob, rb = op.read_bytes(), rp.read_bytes()
    mpath, mb = roots.latest_manifest(), roots.latest_manifest().read_bytes()

    def consistent(new_obj_bytes):
        op.write_bytes(new_obj_bytes)
        rec = json.loads(rb)
        rec["extraction"]["object_sha256"] = WG.sha256_bytes(new_obj_bytes)
        nrb = json.dumps(rec, indent=1).encode("utf-8")
        rp.write_bytes(nrb)

        def f(man):
            man["objects"]["segura_790618"].update(object_sha256=WG.sha256_bytes(new_obj_bytes),
                                                   record_sha256=WG.sha256_bytes(nrb))
        _manifest_edit(roots, f)
    try:
        doc = json.loads(ob)
        v = doc["objects"]["vaal"]["values"]
        k = next(i for i, x in enumerate(v) if x is not None)
        v[k] = v[k] + 1e-9
        consistent((json.dumps(doc, indent=1, ensure_ascii=True) + "\n").encode("utf-8"))
        check("T3 (M2) values tampered with the record and manifest made consistent -> the recomputation from the "
              "source differs: refused", raises(lambda: RS.WP3Sources(roots).map(plan_of(1), 0), R.SourceUnavailable,
                                                L.STATUS_OBJECT_CHANGED))
        # M13: another volume's object under this key (made consistent)
        other = json.loads((Path(roots.artifacts) / man0["objects"]["segura_781986"]["object_path"]).read_bytes())
        other["key"] = "segura_790618"
        consistent((json.dumps(other, indent=1, ensure_ascii=True) + "\n").encode("utf-8"))
        try:
            RS.WP3Sources(roots).map(plan_of(1), 0)
            what = "ACCEPTED"
        except R.SourceUnavailable as ex:
            what = f"{ex.status} | {ex.what}"
        check("T4 (M13) the object of another volume (consistent record and manifest) -> 'not auditable (map changed)' "
              "at the source check", what.startswith(L.STATUS_MAP_CHANGED) and what.endswith("object of another volume"),
              what)
    finally:
        op.write_bytes(ob)
        rp.write_bytes(rb)
        mpath.write_bytes(mb)
    # M12: the record changed, the manifest not
    try:
        rp.write_bytes(rb + b"\n")
        check("T5 (M12) the phase-2 record changed (manifest not) -> refused",
              raises(lambda: RS.WP3Sources(roots).map(plan_of(1), 0), R.SourceUnavailable, L.STATUS_OBJECT_CHANGED))
    finally:
        rp.write_bytes(rb)
    # M14: BrainSpan rows_metadata changed at use
    rows_p, _ = roots.pin("brainspan_rows")
    rows_b = rows_p.read_bytes()
    try:
        rows_p.write_bytes(rows_b.replace(b"SYNG", b"SYNH", 1))
        check("T6 (M14) BrainSpan rows_metadata changed at use (its R50 pin and the phase-2 first-use hash) -> "
              "refused", rows_b != rows_p.read_bytes() and
              raises(lambda: RS.WP3Sources(roots).liu_inputs(plan_of(471)), R.SourceUnavailable, L.STATUS_MAP_CHANGED))
    finally:
        rows_p.write_bytes(rows_b)

    def _bs_entry(man):              # the phase-2 record of BrainSpan's first use names another rows_metadata hash
        man["objects"][L.BRAINSPAN_KEY]["files"]["brainspan_rows"] = "0" * 64
    mp6, mb6 = _manifest_edit(roots, _bs_entry)
    try:
        check("T6 (M14) the file still on its R50 pin but the phase-2 manifest's first-use hash differs -> refused (the "
              "loader holds BrainSpan to both)", raises(lambda: RS.WP3Sources(roots).liu_inputs(plan_of(471)),
                                                       R.SourceUnavailable, L.STATUS_MAP_CHANGED))
    finally:
        mp6.write_bytes(mb6)
    # M15: SD7's second pass must normalise as the first
    import openpyxl
    dkp, _ = roots.pin("dk_info")
    dk = pd.read_csv(io.BytesIO(dkp.read_bytes()))
    from a1_audit import wp3_sd7 as SD
    labels = SC.sd7_labels_synthetic()
    vals = [float(k) / 100 for k in range(len(labels))]
    rec1 = FM.sd7_normalise(labels, dk)
    tf = WM.sd7_value_transform(dk, rec1)

    def view(lab):              # what fetch_extract hands pass 2 (R46 (e)-(f)): positions 0 and the ASD column
        return {"sd7": SD.PositionView({0: lab, 2: vals}, handed=(0, 2))}
    ok1 = tf(view(labels))["sd7"]["values_by_position"] == list(vals)
    mpos = [e["position"] for e in rec1["entries"] if e["kind"] == "matched"]
    i, j = mpos[0], next(q for q in mpos[1:] if rec1["entries"][q]["ids"] != rec1["entries"][mpos[0]]["ids"])
    swapped = list(labels)
    swapped[i], swapped[j] = swapped[j], swapped[i]
    check("T7 (M15) SD7's second pass: the same labels pass; two labels swapped (another normalisation) refused",
          ok1 and raises(lambda: tf(view(swapped)), AssertionError))
    # A2 in-process: a moved carrier reads a status, never an uncaught OSError
    moved = seg.with_name("moved_elsewhere.bin")
    os.rename(seg, moved)
    try:
        check("T8 (A2) a moved carrier at use -> 'not run (identity at use not established ...)', no OSError escapes",
              raises(lambda: RS.WP3Sources(roots).map(plan_of(1), 0), R.SourceUnavailable, L.STATUS_USE_UNREADABLE))
    finally:
        os.rename(moved, seg)
    m = RS.WP3Sources(roots)
    y, ids, cls, h = m.map(plan_of(1), 0)
    inp = m.liu_inputs(plan_of(471))
    msha = WG.sha256_bytes(roots.latest_manifest().read_bytes())
    check("T9 (C (c)) the phase-2 manifest's sha256 is in every map's and every Liu row's input hashes",
          h.get("map[0] phase-2 manifest") == msha and inp["hashes"].get("phase-2 manifest") == msha)


# ================================================================================================================
# Part R: phase 2 resumability (fix round 1, B2; the reviewer's x3.py)
# ================================================================================================================
def part_r() -> None:
    print(SEP + "\nPart R: phase 2 is resumable: preflight first, idempotent re-runs, final / partial manifests")
    roots = make_stage("stage_r", with_sd7=False)
    gp, _ = roots.pin("go_obo")
    good = gp.read_bytes()
    gp.write_bytes(good + b"\n")
    carriers = [SC.local_path(roots, k) for k in ("segura_790618", "segura_781986", L.MOREAU_KEY)]
    res1, text1, calls1 = run_stage(roots)
    recs1 = sorted(Path(roots.records).rglob("*.json")) if Path(roots.records).exists() else []
    check("R1 run 1 with a reference file off its pin: refused at the preflight; no carrier opened, nothing "
          "recorded, no request, Moreau not quarantined, no manifest",
          res1["status"] == L.STATUS_PREFLIGHT and not recs1 and not calls1 and all(c.exists() for c in carriers)
          and not any(os.path.samefile(a, c) for a in res1["admitted"] for c in carriers if Path(a).exists())
          and roots.latest_manifest() is None)
    gp.write_bytes(good)
    res2, _, _ = run_stage(roots)
    check("R2 run 2 (the reference fixed): every target final, the final manifest written", res2["status"] == "final"
          and roots.latest_manifest() is not None and all(e.get("final", True) for e in res2["entries"].values()))
    files2 = sorted(str(x) for x in Path(roots.records).rglob("*")) + sorted(str(x) for x in Path(roots.artifacts).rglob("*"))
    res3, _, calls3 = run_stage(roots)
    files3 = sorted(str(x) for x in Path(roots.records).rglob("*")) + sorted(str(x) for x in Path(roots.artifacts).rglob("*"))
    check("R3 run 3: a verified no-op (no file written, no request)", res3.get("noop") is True and files2 == files3
          and not calls3)
    c = RS.dry_counts(RS.WP3Sources(roots))
    c.pop("_records")
    check("R4 the dry dispatch after run 2: no row reads 'phase 2 material pending'",
          not any(L.STATUS_PENDING in k for k in c["by_outcome_status"]), json.dumps(c["by_outcome"]))
    # a transient decoder failure (the first attempt fails in transport, leaving a partial file) is retried
    roots_t = make_stage("stage_transient", with_sd7=False)
    with SC.scratch_net(roots_t, fail_times={790618: 1}, partial_on_fail=True) as calls:
        rest = WM.run_material(roots_t, out=io.StringIO(), run_info={"mode": "scratch"})
    e = rest["entries"]["segura_decoder_790618"]
    from a1_audit import wp3_decoder as DC
    atts = DC.read_attempts(roots_t, "segura_decoder_790618")
    check("R5 a transient decoder failure: attempt 1 fails in transport (its .part kept, accounted for by its outcome "
          "record; never deleted), attempt 2 extracts after the declared wait; the manifest is final",
          e["status"] == FE.STATUS_EXTRACTED and [a["outcome"]["outcome"] for a in atts] ==
          [DC.OUT_TRANSPORT, DC.OUT_EXTRACTED] and atts[0]["part"] and rest["status"] == "final"
          and WAITS[-1:] == [600])
    # a subset run in scratch writes a partial manifest the loaders do not read
    roots_p = make_stage("stage_partial", with_sd7=False)
    resp, _, _ = run_stage(roots_p, only=["segura_790618"])
    check("R6 a subset run (scratch only): a partial manifest, never read by the loaders ('not final')",
          resp["status"] == "partial" and roots_p.latest_manifest() is None and len(roots_p.partial_manifests()) == 1
          and raises(lambda: RS.WP3Sources(roots_p).map(plan_of(1), 0), R.SourceUnavailable, L.STATUS_NOT_FINAL))
    resp2, _, _ = run_stage(roots_p)
    check("R7 the full run after it adopts the done target and completes: final", resp2["status"] == "final"
          and resp2["entries"]["segura_790618"]["attempts_recorded"] == 1)
    check("R8 a subset run on the production layout is refused before anything is touched",
          raises(lambda: WM.run_material(L.Roots.production(), only=["segura_790618"], out=io.StringIO()), ValueError))
    # a decoder output in another format: a non-transport refusal, final at once (no retry)
    roots_f = make_stage("stage_format", with_sd7=False)
    with SC.scratch_net(roots_f, bad_columns_images=(781986,)) as callsf:
        resf = WM.run_material(roots_f, out=io.StringIO(), run_info={"mode": "scratch"})
    ef = resf["entries"]["segura_decoder_781986"]
    check("R9 a decoder output without the declared FDR column: refused at read:file, final after one attempt",
          ef["final"] is True and ef["refusing_stage"] == "read:file" and ef["attempts_recorded"] == 1
          and sum(1 for c in callsf if c[0] == "get" and "781986" in c[1]) == 1)


# ================================================================================================================
# Part H: the real process's stderr (fix round 1, A1 / A2), in subprocesses, both import orders
# ================================================================================================================
def _child(mode: str, roots_json: Path, order: str) -> tuple:
    import subprocess
    cp = subprocess.run([sys.executable, "-X", "utf8", "-m", "a1_audit.tests.wp3_child", mode, str(roots_json), order],
                        capture_output=True, cwd=str(REPO / "arcs/audit/src"), timeout=1800)
    out = cp.stdout.decode("utf-8", "replace")
    err = cp.stderr.decode("utf-8", "replace")
    res = [ln for ln in out.splitlines() if ln.startswith("RESULT ")]
    return cp.returncode, out, err, (json.loads(res[-1][7:]) if res else None)


def part_h() -> dict:
    print(SEP + "\nPart H: real stderr in subprocesses (nibabel's own logger; carriers absent / locked at use)")
    ev = {}

    def header_logging_roots(name):
        r = make_stage(name, with_sd7=False)
        SC.make_header_logging_standins(r)
        j = TMP / f"{name}_roots.json"
        j.write_text(json.dumps(r.to_spec()), encoding="utf-8")
        return r, j
    roots, rj = header_logging_roots("stage_h")
    forbidden = ("pixdim", "qfac", "vox offset", "magic string", "S12", "segura2025", "syn_790618", "syn_781986",
                 "Traceback", "secret_name")
    for order in ("preimport", "lazy"):
        _, rj_fe = header_logging_roots(f"stage_h_fe_{order}")      # each order on its own fresh layout
        code, out, err, res = _child("fe_stage", rj_fe, order)
        ev[f"fe_stage {order}"] = dict(exit=code, stderr_bytes=len(err), result=res)
        ok = (code == 0 and err == "" and res and res["segura_790618"]["status"] == FE.STATUS_EXTRACTED
              and res["segura_790618"]["stdio_violations"] == 0 and res["segura_790618"]["logging"].get("WARNING", 0) >= 1
              and res["segura_781986"]["status"] == FE.STATUS_FAILED and res["segura_781986"]["logging"].get("level 45")
              and not any(f in out for f in forbidden))
        check(f"H1 (A1) fetch_extract's read:file stage, nibabel {order}: real stderr empty; nibabel's header messages "
              "counted in the record (stdio_violations 0); no incident", ok, json.dumps(ev[f"fe_stage {order}"])[:300])
        if order == "lazy":
            check("H1 (A1) lazy order: nibabel first imported INSIDE the stage; its handler dropped (counted)",
                  res and res["nibabel_imported_before_stage"] is False
                  and res["segura_790618"]["logging"].get("dropped_handler") == 1)
    code, out, err, res = _child("stage", rj, "preimport")
    ev["stage preimport"] = dict(exit=code, stderr_bytes=len(err), result=res)
    check("H2 (A1) the material stage (nibabel imported first): real stderr empty, records stdio_violations 0",
          code == 0 and err == "" and res and res["segura_790618"]["stdio_violations"] == 0
          and not any(f in out for f in forbidden), json.dumps(ev["stage preimport"])[:300])
    for order in ("preimport", "lazy"):
        code, out, err, res = _child("use", rj, order)
        ev[f"use {order}"] = dict(exit=code, stderr_bytes=len(err), result=res)
        check(f"H3 (A2) at use, nibabel {order}: identity at use and the recomputation in section 8's handler; real "
              "stderr empty", code == 0 and err == "" and res and res["map 1"] == "ok"
              and not any(f in out for f in forbidden), json.dumps(ev[f"use {order}"])[:300])
    seg = SC.local_path(roots, "segura_790618")
    moved = seg.with_name("moved_elsewhere.bin")
    os.rename(seg, moved)
    try:
        for mode in ("use", "use_repro"):
            code, out, err, res = _child(mode, rj, "lazy")
            ev[f"moved {mode}"] = dict(exit=code, stderr_bytes=len(err), result=res)
            st = (res or {}).get("map 1") if mode == "use" else (res or {}).get("prepare 1")
            check(f"H4 (A2) the carrier moved away, {mode}: exit 0, real stderr empty, no carrier name printed, the row "
                  "reads 'not run (identity at use not established ...)'", code == 0 and err == ""
                  and st == L.STATUS_USE_UNREADABLE and not any(f in out for f in forbidden),
                  json.dumps(ev[f"moved {mode}"])[:300])
    finally:
        os.rename(moved, seg)
    import msvcrt
    fh = open(seg, "rb+")
    try:
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, seg.stat().st_size)
        code, out, err, res = _child("use", rj, "lazy")
        ev["locked use"] = dict(exit=code, stderr_bytes=len(err), result=res)
        check("H5 (A2) the carrier locked by another process at use: exit 0, real stderr empty, 'not run (identity at "
              "use not established ...)'", code == 0 and err == "" and res and res["map 1"] == L.STATUS_USE_UNREADABLE,
              json.dumps(ev["locked use"])[:300])
    finally:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, seg.stat().st_size)
        fh.close()
    code, out, err, res = _child("hook", rj, "lazy")
    ev["hook"] = dict(exit=code, stderr=err.strip())
    check("H6 (A2) the excepthook: an uncaught FileNotFoundError naming a carrier path prints its class and file:line "
          "only", code != 0 and err.strip().startswith("wp3_child: uncaught FileNotFoundError at wp3_child.py:")
          and "secret_name" not in err and "segura2025" not in err and len(err.strip().splitlines()) == 1, err[:200])
    import inspect
    check("H6 (A2) run.py's and wp3_material's entry points install it",
          'install_excepthook("a1_audit.run")' in inspect.getsource(sys.modules["a1_audit.run"])
          and 'PW.install_excepthook("wp3_material")' in inspect.getsource(WM.main))
    # the in-process quiet_logging: a library logger with its own handler, existing and added inside
    import logging
    real_err = io.StringIO()
    lg = logging.getLogger("a1test.lib")
    lg.handlers = [logging.StreamHandler(real_err)]
    with PW.quiet_logging() as counts:
        lg.warning("a carrier name inside a library message")
        logging.getLogger("a1test.late").addHandler(logging.StreamHandler(real_err))
        logging.getLogger("a1test.late").error("late library message")
    late_handlers = logging.getLogger("a1test.late").handlers
    check("H7 (A1) quiet_logging: an existing library handler and one added inside are silenced (counted), the "
          "existing one restored after, the late one never attached", real_err.getvalue() == ""
          and counts.get("WARNING") == 1 and counts.get("ERROR") == 1 and counts.get("dropped_handler") == 1
          and len(lg.handlers) == 1 and late_handlers == [])
    lg.handlers = []
    return ev


# ================================================================================================================
# Part U: C residues (fix round 1): M4-M8, M11, NaN, R27
# ================================================================================================================
def part_u(roots) -> None:
    print(SEP + "\nPart U: reproduction units that can fail (M4-M8), _write_repro (M11), no NaN in JSON, R27")
    from fractions import Fraction
    from math import comb
    # M4: Fisher p_primary is the two-sided p, on a table where the two sidednesses differ (a depletion)
    ref = {f"G{k}" for k in range(200)}
    term = {f"G{k}" for k in range(60)}
    lst = {f"G{k}" for k in range(55, 95)}
    fr = WR.fisher_record(lst, term, ref)
    check("U1 (M4) Fisher: p_primary = the two-sided p, which differs from the one-sided p on this table",
          fr["p_primary"] == fr["p_two_sided"] and abs(fr["p_two_sided"] - fr["p_greater"]) > 1e-3)
    # M5: the ORA's q_primary is the two-sided BH q (a planted signal makes q < 1)
    rng = np.random.default_rng(3)
    refg = [f"G{k}" for k in range(400)]
    terms = {f"T{k}": set(rng.choice(refg, 30, replace=False)) for k in range(30)}
    terms["T_sig"] = {f"G{k}" for k in range(40)}
    lst2 = {f"G{k}" for k in range(30)} | set(rng.choice(refg, 20, replace=False))
    idx = WR.gene_index(refg)
    o = WR.ora_bits(WR.bits_of(lst2, idx), {k: WR.bits_of(v, idx) for k, v in terms.items()}, WR.bits_of(refg, idx))
    tested = [t for t in o["terms"].values() if t["status"] == "tested"]
    check("U2 (M5) ORA: q_primary = the two-sided BH q for every term; with a planted signal some q < 1 and the "
          "sidednesses' q's differ", all(t["q_primary"] == t["q_two_sided"] for t in tested)
          and min(t["q_two_sided"] for t in tested) < 0.05
          and any(t["q_two_sided"] != t["q_greater"] for t in tested))
    # M6 / M7: the MOR-T tail, exact
    pub = ROWS[618]["published_value_and_location"]
    G = 50
    r_target = np.linspace(-0.9, 0.95, G)
    y = np.random.default_rng(1).normal(size=64)
    yc = (y - y.mean()) / y.std()
    Z0 = np.random.default_rng(2).normal(size=(64, G))
    Z0 = Z0 - Z0.mean(0)
    Z0 = Z0 - np.outer(yc, yc @ Z0) / (yc @ yc)
    Z0 = Z0 / Z0.std(0)
    X = r_target * yc[:, None] + np.sqrt(1 - r_target ** 2) * Z0
    cols = [f"G{k}" for k in range(G)]
    cols[-1], cols[-2] = "MVP", "KIF22"
    M = pd.DataFrame(X, columns=cols)
    S = ["MVP", "KIF22", "G3", "G10", "G20"]
    tl = WR.mor_t_tail(y, M, S, 618, pub)
    t98, t95 = tl["tails"]["98"], tl["tails"]["95"]
    check("U3 (M7) weak percentile at the boundary: the gene with r of rank 49 / 50 sits at 98.0 exactly and is NOT "
          "above the 98th percentile ('>' decided exactly)", tl["named"]["KIF22"]["percentile_weak"] == 98.0
          and t98["n_genes_above"] == 1 and t95["n_genes_above"] == 3)

    def exact_tail(Gn, K, m, k):
        return Fraction(sum(comb(K, x) * comb(Gn - K, m - x) for x in range(k, min(K, m) + 1)), comb(Gn, m))
    e98 = exact_tail(G, t98["n_genes_above"], t98["m"], t98["k_set_above"])
    e95 = exact_tail(G, t95["n_genes_above"], t95["m"], t95["k_set_above"])
    check("U4 (M6) the tail p = P(X >= k) in exact rationals (k >= 1, so P(X > k) differs)",
          t98["k_set_above"] >= 1 and abs(t98["p_exact"] - float(e98)) <= 1e-12 * float(e98)
          and abs(t95["p_exact"] - float(e95)) <= 1e-12 * float(e95)
          and abs(float(e98) - float(exact_tail(G, t98["n_genes_above"], t98["m"], t98["k_set_above"] + 1))) > 1e-3)
    # exhaustive enumeration on a small case
    G2 = 12
    above = np.zeros(G2, bool)
    above[[10, 11]] = True
    import itertools
    m2, k2 = 3, 1
    hits = sum(1 for c in itertools.combinations(range(G2), m2) if above[list(c)].sum() >= k2)
    from scipy import stats as _st
    check("U4 (M6) the hypergeometric tail P(X >= k) equals an exhaustive enumeration of every set (G 12, m 3)",
          abs(float(_st.hypergeom.sf(k2 - 1, G2, 2, m2)) - hits / comb(G2, m2)) < 1e-12)
    # M8: the decoder's Entrez id before its symbol
    d = TMP / "unit_u"
    d.mkdir(parents=True, exist_ok=True)
    hb = _syn_hgnc_table(d / "hgnc.txt")
    hg = WG.HGNCTable(hb)
    rows_ = [["BBB2", 100.0, "n", 2.0, 0.01, 0.02, 1, 0.1]]       # symbol BBB2, Entrez id of AAA1
    o8 = WM.decoder_object(json.dumps({"columns": list(L.DECODER_COLUMNS), "data": rows_}).encode(), hg, 1)
    check("U5 (M8) a decoder row whose symbol and Entrez id name different genes -> the Entrez id's gene",
          o8["genes"] == ["AAA1"])
    # NaN: an empty decoded list gives non-finite odds ratios -> null + a status
    fr0 = WR.fisher_record(set(), term, ref)
    safe = WR.json_safe({"x": fr0})
    check("U6 (C (d)) non-finite values are written as null with a status; the record serialises with allow_nan=False",
          any(not np.isfinite(v) for v in (fr0["odds_ratio_sample"], fr0["odds_ratio_conditional_mle"])
              if isinstance(v, float))
          and bool(json.dumps(safe, allow_nan=False)) and safe["nonfinite_as_null"]["fields"])
    # M11: _write_repro through a minimal run object; a raising reproduction is caught inside section 8's handler

    class FakeRun:
        def __init__(self, src, out):
            self.sources, self.results_dir, self.plant_view, self.lines = src, out, False, []

        def header(self):
            return {"what": "test"}

        def provenance(self):
            return {"test": True}

        def log(self, m):
            self.lines.append(m)
    outd = TMP / "write_repro"
    fr_ = FakeRun(RS.WP3Sources(roots), outd)
    sha = R._write_repro(fr_, plan_of(615))
    doc = json.loads((outd / "row_0615_repro.json").read_text(encoding="utf-8")) if sha else {}
    check("U7 (M11) _write_repro writes row_<n>_repro.json for a real-sources row (MOR-C1: the R37 check)",
          bool(sha) and doc.get("reproduction", {}).get("check", {}).get("functional") == "R2")
    orig = WR.row_reproduction
    try:
        def boom(*a, **k):
            raise RuntimeError(r"E:\data\asdg\segura2025\secret_name.nii.gz")
        WR.row_reproduction = boom
        sha2 = R._write_repro(fr_, plan_of(616))
        doc2 = (outd / "row_0616_repro.json").read_text(encoding="utf-8")
    finally:
        WR.row_reproduction = orig
    check("U8 (C (b)) a reproduction that raises: caught inside section 8's handler, recorded as a status, never "
          "aborts the pass, its message never written", bool(sha2) and R.REPRO_FAILED in doc2 and "secret_name" not in doc2)
    try:
        WR.row_reproduction = lambda *a, **k: {"odds_ratio": float("nan"), "fold": float("inf"), "n": 3}
        R._write_repro(fr_, plan_of(617))
        raw = (outd / "row_0617_repro.json").read_text(encoding="utf-8")
    finally:
        WR.row_reproduction = orig

    def _no_constants(c):
        raise ValueError("a bare non-finite constant")
    try:
        d3 = json.loads(raw, parse_constant=_no_constants)
        ok3 = d3["reproduction"]["odds_ratio"] is None and d3["reproduction"]["nonfinite_as_null"]["fields"]
    except ValueError:
        ok3 = False
    check("U8 (C (d)) _write_repro writes a non-finite value as null with its status (strict JSON parse)", ok3)
    # R27 on synthetic rows (RUN_PLAN §16 :1667, R27 :968-977)
    from a1_audit import reporting as RPT
    import e3_plants
    saved_paths = (e3_plants.GAMBA_CSV, e3_plants.AHBA, A3.AHBA)   # run.synthetic_guard repoints them: restored below
    try:
        syn = R.SyntheticSources(15, TMP / "_no_data_r27")
        scope = R.r27_scope(REPO)
        pr = R.prepare(plan_of(10), syn, 0)
        prm = R.prepare(plan_of(615), syn, 0)
    finally:
        e3_plants.GAMBA_CSV, e3_plants.AHBA, A3.AHBA = saved_paths
    vrec = {"primary_status": "ok", "survives": False, "kind": "full"}
    r27 = R.r27_for_map(pr, vrec, reparcellated=True, scope=scope)
    desc = A3.descriptors(pr.ctx, pr.y, pr.S, parcel_ids=pr.parcel_ids)
    direct = RPT.r27_reading({"status": "ok", "survives": False}, desc, pr.ctx, reparcellated=True, scope=scope)
    check("U9 R27 on a synthetic decoded-list row: the labels, power columns and reading equal reporting.r27_reading "
          "on a3_port.descriptors (V-AAL power column; m 25: no set-size label)",
          r27["labels"] == direct["labels"] and r27["power_columns"] == ["V-AAL"] == direct["power_columns"]
          and r27["reading"] == "not detectable at this power" and r27["descriptors"]["m"] == 25)
    # pre-WP4: the fixture now carries the kind a component record carries (verdict.adapter_kind); the literal
    # "component" it used before is the kind no record carries, which hid run.r27_for_map's label defect
    r27m = R.r27_for_map(prm, {"primary_status": "ok", "survives": False, "kind": "component-permutation",
                               "reading": "does not pass at component level"}, reparcellated=False, scope=scope)
    check("U10 R27 on a synthetic component row (MIST64; kind 'component-permutation'): 'power not measured in this "
          "class', the component reading kept beside R27's, a species-leg label kept with its note",
          "power not measured in this class" in r27m["labels"]
          and r27m["reading"] == "does not pass at component level" and "reading_r27" in r27m
          and ("species leg untested (gradient)" not in r27m["labels"] or "labels_notes" in r27m))
    import inspect
    check("U11 run._assemble_row attaches R27 per map in a real verdict pass (r27_for_map with r27_scope)",
          "r27_for_map(" in inspect.getsource(R._assemble_row) and "r27_scope(REPO)" in inspect.getsource(R._assemble_row))


# ================================================================================================================
# Part C: the loaders
# ================================================================================================================
def part_c(roots_pre, roots) -> None:
    print(SEP + "\nPart C: the WP3 loaders on the stand-ins")
    pre = RS.WP3Sources(roots_pre)
    pend = []
    for n in (1, 10, 615, 618):
        pend.append(raises(lambda n=n: pre.map(plan_of(n), 0), R.SourceUnavailable, L.STATUS_PENDING))
    for n in LIU_ROWS:
        pend.append(raises(lambda n=n: pre.liu_inputs(plan_of(n)), R.SourceUnavailable, L.STATUS_PENDING))
    carriers = [Path(r["probes"][1]["path"]) for r in json.loads(Path(roots_pre.identity_json).read_bytes())["records"]]
    opened_carrier = [a for a in pre.admitted if any(os.path.samefile(a, c) for c in carriers if Path(a).exists())]
    check("C1 before phase 2: every Segura / Moreau / Liu loader reads 'not run (phase 2 material pending)'", all(pend))
    check("C1 before phase 2: no carrier was opened (the manifest is read first)", not opened_carrier)
    src = RS.WP3Sources(roots)
    ctx, counts, sha = src.context("V-AAL")
    check("C2 context V-AAL: 54 primary parcels, a count >= 1 for each, built through build_context_checked",
          ctx.n == 54 and all(counts[int(i)] >= 1 for i in ctx.parcel_ids) and "a1_class_rule" not in ctx.report)
    ctxm, cm, _ = src.context("MIST64")
    check("C2 context MIST64: 46 primary parcels (cortex 33, subcortex 5, cerebellum 8)", ctxm.n == 46)
    dc, _ = src.donor_counts("V-AAL")
    check("C2 donor counts: the primary build's n_donors on the class parcels", set(dc) == set(counts)
          and all(1 <= v <= 6 for v in dc.values()))
    y, ids, cls, h = src.map(plan_of(1), 0)
    obj = json.loads((Path(roots.artifacts) / json.loads(roots.manifest_path.read_bytes())["objects"]["segura_790618"]
                      ["object_path"]).read_bytes())["objects"]["vaal"]
    by = dict(zip(obj["ids"], obj["values"]))
    exp_y = np.array([np.nan if by[int(i)] is None else by[int(i)] for i in ids])
    check("C3 Segura map: the object's values on the 54 class parcels (NaN where the rule dropped a parcel)",
          cls == "V-AAL" and np.array_equal(np.isnan(y), np.isnan(exp_y)) and np.allclose(y[~np.isnan(y)],
                                                                                         exp_y[~np.isnan(exp_y)], 0, 0))
    check("C3 Segura map: identity at use computed and the recomputation check run",
          src.source_identity("segura_790618")["basis"] == "identity at use" and ("recompute", "segura_790618") in src._c)
    y2 = src.map(plan_of(2), 0)[0]
    check("C3 SEG-C2 binds to image 781986 (another object)", not np.allclose(np.nan_to_num(y), np.nan_to_num(y2)))
    mo = json.loads((Path(roots.artifacts) / json.loads(roots.manifest_path.read_bytes())["objects"][L.MOREAU_KEY]
                     ["object_path"]).read_bytes())["objects"]
    B = np.array(mo["del16p11"]["values"])
    np.fill_diagonal(B, 0)
    prof = B.mean(1)
    ym, idm, clm, _ = src.map(plan_of(615), 0)
    ym3 = src.map(plan_of(617), 0)[0]
    B3 = np.array(mo["del22q11"]["values"])
    np.fill_diagonal(B3, 0)
    check("C4 Moreau map: nodal profile = the block with diagonal 0, mean over 64 columns, on the 46 primary parcels",
          clm == "MIST64" and np.allclose(ym, prof[idm - 1], 0, 0))
    check("C4 MOR-C3 binds to the 22q11.2 sheet (TSV map text)", np.allclose(ym3, B3.mean(1)[idm - 1], 0, 0))
    cols, ssha = src.gene_set(plan_of(10))
    doc = json.loads((REPO / "arcs/audit/register_sets/segura_go_GO0048667.json").read_bytes())
    check("C5 gene_set: the set file's V-AAL universe columns, through the freeze chain",
          cols == doc["universe"]["V-AAL"]["columns"] and len(ssha) == 64)
    T, tsha = src.trajectories("V-AAL")
    check("C5 trajectories: genes x 8 bins (the frozen rule)", T.shape[1] == 8 and T.index.is_unique)
    tamper = dataclasses.replace(roots)
    srct = RS.WP3Sources(tamper)
    opath = Path(roots.artifacts) / json.loads(roots.manifest_path.read_bytes())["objects"]["segura_781986"]["object_path"]
    saved = opath.read_bytes()
    try:
        opath.write_bytes(saved.replace(b'"image": 781986', b'"image":  781986'))
        check("C6 a tampered phase-2 object is refused (sha256 vs the manifest)",
              raises(lambda: srct.map(plan_of(2), 0), R.SourceUnavailable, L.STATUS_OBJECT_CHANGED))
    finally:
        opath.write_bytes(saved)
    # the runner's preparation on the stand-ins
    pr = R.prepare(plan_of(1), src, 0)
    prm = R.prepare(plan_of(615), src, 0)
    check("C7 run.prepare: a Segura row (decoded-list, V-AAL) and MOR-C1 (component PLS on S) prepare on the stand-ins",
          pr.adapter is not None and prm.adapter is not None and pr.S is not None and len(prm.S) >= 5)
    inp = src.liu_inputs(plan_of(471))
    leak = [s for s in SC.PLANTED_IDS if s in inp["meta"].to_csv() or s in inp["expr"].to_csv()]
    check("C8 Liu (BrainSpan) inputs: declared metadata columns only; no planted donor string",
          list(inp["meta"].columns) == ["age", "structure_acronym"] and not leak)
    sc = R.seeds_of(plan_of(471), 0)
    out = FM.liu_compute(plan_of(471)["liu_spec"], inp, K=30, seed_of=sc["seed_of"], g3_seed=sc["g3_seed"],
                         two_sided=False, registered_direction=1)
    check("C8 forms.liu_compute runs on the BrainSpan stand-in (T finite, G1-G5 drawn)",
          np.isfinite(out["T"]) and set(out["legs"]) >= {"Level-2 G1", "G2", "G3", "G4", "G5"})
    inp4 = src.liu_inputs(plan_of(473))
    out4 = FM.liu_compute(plan_of(473)["liu_spec"], inp4, K=20, seed_of=sc["seed_of"], g3_seed=sc["g3_seed"],
                          two_sided=False, registered_direction=1)
    check("C8 Liu T4 on the per-sample stand-in with the SD7 record (no label string loaded)",
          np.isfinite(out4["T"]) and "sd7_labels" not in inp4 and out4["labels"]["label_set"]["pooled"] is False)
    check("C9 spec round trip: run.sources_from_spec rebuilds the WP3 sources with the same roots",
          R.sources_from_spec(src.spec()).roots == roots)


# ================================================================================================================
# Part F: reproduction wiring on the stand-ins
# ================================================================================================================
def part_f(roots, roots_fail) -> None:
    print(SEP + "\nPart F: reproduction wiring (synthetic)")
    src = RS.WP3Sources(roots)
    r1 = WR.row_reproduction(plan_of(1), src)
    pri = r1["per_reference"][WR.R22_REFERENCE_PRIMARY]
    check("F1 SEG-C1: Fisher vs Table S4 in both references; two-sided primary, label and empirical check beside; the "
          "paper's 20,787 beside", pri["primary"] == "two-sided" and pri["label"] == "PANTHER sidedness unverified"
          and pri["empirical_check"]["result"].startswith("PANTHER") and r1["paper_reference_n"] == 20787
          and WR.R22_REFERENCE_PANTHER in r1["per_reference"] and r1["published"]["OR"] == "1.6")
    direct = RE.fisher_counts(WR.decoded_from_decoder(src.decoder_genes(790618)[0]), WR.SeguraContext(src).s4(),
                              WR.SeguraContext(src).references()[WR.R22_REFERENCE_PRIMARY][0])
    check("F1 SEG-C1 counts equal repro.fisher_counts computed directly", all(pri[k] == direct[k] for k in "abcd"))
    r3 = WR.row_reproduction(plan_of(3), src)
    t3 = r3["per_reference"][WR.R22_REFERENCE_PRIMARY]["term"]
    check("F2 SEG-C3a: the GO ORA's term record (fold, both p's, both q's) and the TSV's Table S7 values beside",
          isinstance(t3, dict) and "q_two_sided" in t3 and r3["published"]["fold"] == "7.35")
    r10 = WR.row_reproduction(plan_of(10), src)
    from a1_audit import wp3_scratch_pdf as SPDF
    planted = SPDF.planted_values(SPDF.s7_terms(), {})["SEG-C3-D01"]
    check("F2 SEG-C3-D01 (RUN_PLAN_amend_3 R47): Table S7's row transcribed from MOESM2 p. 39 (the planted values of the "
          "synthetic PDF); Table S6's Jaccard computed (A = decoded n S4, B = S6's 107)",
          r10["published"].get("tokens") == planted and r10["jaccard_table_s6"]["status"] == "computed"
          and r10["jaccard_table_s6"]["n_B"] == 107 and r10["jaccard_table_s6"]["paper_B"] == "107 (TSV row 1)")
    r4 = WR.row_reproduction(dict(plan_of(4)), src)
    check("F2 SEG-C3b (row 4, no T): its descriptive comparison is reported too (R47 (h))",
          isinstance(r4["per_reference"][WR.R22_REFERENCE_PRIMARY]["term"], (dict, str)) and r4["published"]["fold"] == "64.75"
          and r4["t"].startswith("no T"))
    srcf = RS.WP3Sources(roots_fail)
    r2 = WR.row_reproduction(plan_of(2), srcf)
    check("F3 decoder unavailable (781986 refused at phase 2) -> R22's fallback: the per-donor recipe on V-AAL, "
          "labelled", r2["decoded_list"].get("label") == WR.R22_FALLBACK_LABEL and r2["decoded_list"]["n_tested"] > 0)
    rm = WR.row_reproduction(plan_of(615), src)
    check("F4 MOR-C1: the authors' unscaled PLS on all 64 parcels, R37 (B) check against .242",
          rm["check"]["functional"] == "R2" and rm["check"]["published"] == ".242" and rm["pls"]["n_parcels"] == 64
          and rm["pls"]["scaled"] is False)
    rt = WR.row_reproduction(plan_of(618), src)
    check("F4 MOR-T1: percentile ranks of MVP and KIF22 and the 98th / 95th tails with exact p's",
          set(rt["named"]) == {"MVP", "KIF22"} and set(rt["tails"]) == {"98", "95"})
    inp4 = src.liu_inputs(plan_of(473))
    sc = R.seeds_of(plan_of(473), 0)
    res4 = FM.liu_compute(plan_of(473)["liu_spec"], inp4, K=10, seed_of=sc["seed_of"], g3_seed=sc["g3_seed"],
                          two_sided=False, registered_direction=1)
    rl = WR.row_reproduction(plan_of(473), src, res4)
    check("F5 LIU-T4 (R46 (g)): on the common labels, our statistic vs the same statistic from SD7's values (R37 (B), "
          "rank-biserial); 'comparator on n of m labels' (the stand-in's missing values); T (all m) beside",
          rl.get("check", {}).get("functional") == "rank-biserial" and np.isfinite(rl["T_sd7_common"])
          and rl["status"] == "computed" and rl["label"].startswith("comparator on") and rl["n_common"] < rl["m"]
          and rl["T_all_labels"] == float(res4["T"]))
    rl1 = WR.row_reproduction(plan_of(471), src, {})
    rl2 = WR.row_reproduction(plan_of(472), src, {})
    check("F5 LIU-T1 / T2 (R48 / R49): the amendment's 'not computable (...)' statuses", rl1["status"] == WR.T1_PER_SAMPLE
          and rl2["status"] == WR.T2_FAMILY)


# ================================================================================================================
# Part E: dry dispatch
# ================================================================================================================
EXPECTED_COMPUTING = 90   # Segura 78 + MOR-C1..C3 + MOR-T1, T2 + Liu 7 (RUN_PLAN §10 :1413-1417)


def real_root_expected_status():
    """The real root's phase-2 state (fix round 5: phase 2 ran at 61b443f and ended partial): no manifest -> 'pending';
    only partial manifests -> 'not final'; a final manifest -> None (the real dry dispatch is then not a test's: it
    would read real phase-2 objects)."""
    rp = L.Roots.production()
    if rp.latest_manifest() is not None:
        return None
    return L.STATUS_NOT_FINAL if rp.partial_manifests() else L.STATUS_PENDING


def part_e(roots) -> dict:
    print(SEP + "\nPart E: dry dispatch of the 115 ungated rows")
    out = {}
    want = real_root_expected_status()
    if not ARGS.skip_real_dry and want is None:
        print("  E1 not run: the real root has a final phase-2 manifest (its dry dispatch reads real objects)")
    elif not ARGS.skip_real_dry:
        src = RS.WP3Sources(L.Roots.production())
        c = RS.dry_counts(src)
        recs = c.pop("_records")
        out["real"] = c
        print("  real data root: " + json.dumps(c["by_outcome_status"], indent=None)[:2000])
        comp = [r for r in recs if r["outcome"] in ("would compute", "not run")]
        check(f"E1 real root (phase-2 state: {'partial manifest' if want == L.STATUS_NOT_FINAL else 'no manifest'}): "
              f"115 rows; 90 computing rows all '{want}'; 25 no statistic",
              c["n_rows"] == 115 and len(comp) == EXPECTED_COMPUTING and all(r["status"] == want for r in comp)
              and c["by_outcome"].get("no statistic") == 25, json.dumps(c["by_outcome"]))
        carriers = [str(Path(v["local_path"])).lower() for v in L.identity_records(L.Roots.production(),
                                                                                    lambda p: Path(p).read_bytes()).values()]
        bad = [a for a in src.admitted if a.lower() in carriers or "segura" in a.lower() or "moreau" in a.lower()
               or "liu2026" in a.lower() or any(x.casefold() == "_quarantine" for x in Path(a).parts)]
        check("E1 real root: no carrier, supplement or quarantine path admitted (the manifest is read first)", not bad)
    src = RS.WP3Sources(roots)
    c = RS.dry_counts(src)
    recs = c.pop("_records")
    out["scratch"] = c
    print("  scratch stand-ins: " + json.dumps(c["by_outcome_status"], indent=None)[:2000])
    check("E2 scratch stand-ins: every one of the 90 computing rows reads 'would compute'",
          c["by_outcome"].get("would compute") == EXPECTED_COMPUTING and c["by_outcome"].get("no statistic") == 25,
          json.dumps(c["by_outcome"]))
    return out


# ================================================================================================================
# Part G (--real-go): the GO rule on the real reference files reproduces the frozen S-build's Segura GO sets
# ================================================================================================================
def part_g() -> None:
    print(SEP + "\nPart G: the GO rule on the real GO 2024-01-17 files reproduces the frozen segura_go sets (sets only)")
    src = RS.WP3Sources(L.Roots.production())
    hg = WG.HGNCTable(src.pinned("hgnc"))
    go = WG.GOTerms(src.pinned("go_obo"), src.pinned("go_gaf"))
    s4 = set(src.set_doc("segura_s4")[0]["members_hgnc"])
    man = src._set_manifest()
    ids = sorted(k for k in man if k.startswith("segura_go_"))
    bad, n_before = [], 0
    for sid in ids:
        doc, _ = src.set_doc(sid)
        gid = doc["go"]["go_id"]
        raw, n_desc = go.raw_members(gid)
        term, _ = WG.resolve_raw(hg, raw)
        if (sorted(term & s4) != doc["members_hgnc"] or len(term) != doc["n_hgnc_term_before_intersection"]
                or n_desc != doc["go"]["n_terms_with_descendants"]):
            bad.append(sid)
        n_before += 1
    check(f"G1 every frozen segura_go set ({n_before}) = (the GO rule's HGNC genes of its term) intersected with Table "
          "S4, with the frozen term size and descendant count", not bad and n_before == 78, f"{len(bad)} differ")
    idx = WR.gene_index(*(set(WG.resolve_raw(hg, go.raw_members(t)[0])[0]) for t in ("GO:0007409", "GO:0048667")))
    bits = go.term_gene_bits(hg, idx)
    ok = all(bits[t] == WR.bits_of(WG.resolve_raw(hg, go.raw_members(t)[0])[0], idx) for t in ("GO:0007409", "GO:0048667"))
    check("G2 the memoised bitsets equal the raw-member resolution on two real terms", ok)
    # G3 BrainSpan (as the frozen asdg.brainspan reads it)
    import asdg.brainspan as BS
    blobs = {k: src.read_bytes(src.roots.pin(k)[0]) for k in ("brainspan_expr", "brainspan_rows", "brainspan_cols")}
    X, rws, cls = WG.brainspan_frames(blobs["brainspan_expr"], blobs["brainspan_rows"], blobs["brainspan_cols"])
    T1, _ = WG.brainspan_trajectories(X, list(rws["gene_symbol"].astype(str)), list(cls["age"]),
                                      list(cls["structure_acronym"]))
    T0, _ = BS.load_trajectories()
    check("G3 BrainSpan: expression_matrix.csv sha256 = the TSV pin; declared-columns frames give the frozen "
          f"trajectories bit for bit ({T1.shape[0]} genes x 8)", WG.sha256_bytes(blobs["brainspan_expr"])
          == src.roots.pin("brainspan_expr")[1] and T0.equals(T1))
    # G4 the WP2 build chain
    okb = []
    for name, roles in RS.BUILDS_READ.items():
        keys = (["counts"] if "counts" in roles else []) + (
            ([f"matrix_d{k}" for k in range(1, 7)] if name == "perdonor-aal" else ["matrix"]) if "matrix" in roles else [])
        for k in keys:
            try:
                src.build_output(name, k)
                okb.append(True)
            except Exception:  # noqa: BLE001
                okb.append(False)
    check(f"G4 every WP2 build output the loaders read passes its record chain in env/venv ({len(okb)} outputs)",
          all(okb) and len(okb) == 11)
    # G5 the guard's name screen on the plan's pinned sheet names (the real HGNC table; no carrier)
    old = (FE.PG.HGNC_FILE, FE.PG._HGNC)
    try:
        FE.PG.HGNC_FILE = src.roots.pin("hgnc")[0]
        FE.PG._HGNC = None
        dec = {n: PW.screen(n, FE.PG) for n in FE.MOREAU_SHEETS}
        dno = {n: PW.screen(n, FE.PG) for n in FE.MOREAU_DO_NOT_OPEN}
    finally:
        FE.PG.HGNC_FILE, FE.PG._HGNC = old
    # G6 (RUN_PLAN_amend_3 R50, section 8.1) the stage's preflight on the REAL layout: every identity and pin check on
    # the reference / build files and the Moreau clone assertion on the run-time pins (no carrier, no request)
    old_g = (FE.PG.HGNC_FILE, FE.PG._HGNC)
    buf = io.StringIO()
    try:
        roots_p = L.Roots.production()
        door = WM.Door(roots_p)
        allow = WM._allow(roots_p)
        em = PW.Emitter(allow, stream=buf)
        try:
            pre = WM.preflight(roots_p, door, em, allow)
            ok6, refs = True, pre["pins"]["references"]
            ca = pre["pins"]["moreau_clone"]
        except WM.PreflightRefused:
            ok6, refs, ca = False, {}, {}
    finally:
        FE.PG.HGNC_FILE, FE.PG._HGNC = old_g
    carriers = [str(Path(v["local_path"])).casefold() for v in L.identity_records(roots_p, lambda p: Path(p).read_bytes())
                .values()] + [str(Path(roots_p.sd7_copy[0])).casefold(), str(roots_p.pin("segura_moesm2")[0]).casefold()]
    touched = [a for a in door.admitted if a.casefold() in carriers]
    check("G6 the preflight on the real layout passes: the R50 pins (BrainSpan x3 with sizes, GAMBA), every reference "
          "file and the a1_builds chain match; the clone assertion finds no other pinned object inside the clone; no "
          f"carrier admitted ({len(refs)} references)", ok6 and len(refs) == len(WM.REFERENCE_KEYS) and not touched
          and ca.get("n_pinned_inside_clone_other_than_workbook") == 0, buf.getvalue()[-300:] if not ok6 else "")
    check("G5 the guard's screen of the plan's pinned Moreau sheet names: declared 0 hits; every do-not-open name a V "
          "hit -> phase 2 will count the workbook identifier-bearing and quarantine it (RUN_PLAN section 8 Screening)",
          all(v == {"V": 0, "N": 0} for v in dec.values()) and all(v["V"] >= 1 for v in dno.values()),
          json.dumps({"declared": list(dec.values()), "do_not_open": list(dno.values())}))


def main() -> int:
    t0 = time.time()
    roots_pre = make_stage("stage_pre")           # stand-ins without a phase-2 run (pending)
    roots = make_stage("stage_main")
    run_stage(roots)                              # the phase-2 stage on the stand-ins (Part B checks it again below)
    for part in (lambda: part_d(roots), part_a, lambda: part_c(roots_pre, roots)):
        try:
            part()
        except Exception as e:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(f"part raised {type(e).__name__}", False)
    dry, hev = {}, {}
    roots_t = make_stage("stage_t", with_sd7=False)
    run_stage(roots_t)
    roots_b = make_stage("stage_b")
    roots_fail = make_stage("stage_fail")
    for name, part in (("B", lambda: part_b(roots_b)), ("B failures", part_b_failures), ("T", lambda: part_t(roots_t)),
                       ("R", part_r), ("U", lambda: part_u(roots)),
                       ("F", lambda: (run_stage(roots_fail, fail_images=(781986,)), part_f(roots, roots_fail))),
                       ("E", lambda: dry.update(part_e(roots))), ("H", lambda: hev.update(part_h())),
                       ("G", part_g if ARGS.real_go else (lambda: None))):
        if ARGS.parts and name.split()[0] not in ARGS.parts:
            continue
        try:
            part()
        except Exception as e:  # noqa: BLE001
            import traceback
            traceback.print_exc()
            check(f"part {name} raised {type(e).__name__}", False)
    (TMP / "dry_counts.json").write_text(json.dumps(dry, indent=1, sort_keys=True), encoding="utf-8")
    if hev:
        (TMP / "real_stderr_evidence.json").write_text(json.dumps(hev, indent=1, sort_keys=True), encoding="utf-8")
        print("  real-stderr evidence (Part H): " + json.dumps({k: {"exit": v.get("exit"), "stderr_bytes":
                                                                   v.get("stderr_bytes", len(v.get("stderr") or ""))}
                                                                for k, v in hev.items()}, sort_keys=True))
    n = len(RESULTS)
    failed = [k for k, ok in RESULTS if not ok]
    print(f"{n - len(failed)} of {n} checks passed ({time.time() - t0:.0f} s)", flush=True)
    if not ARGS.keep:
        shutil.rmtree(TMP, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
