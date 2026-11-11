"""WP4 phase 1 tests (RUN_PLAN.md v3.1 §8, §11, §16-§18; R13-R17, R27, R30, R38; the DRAFT RUN_PLAN_amend_4.md
R51-R64; RUN_PLAN §17's comparison and launch). Plain script; exits non-zero on any failure.

    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_wp4_phase1 [--scratch DIR] [--require-docker]

Material: SYNTHETIC stand-ins only (a1_audit/wp4_scratch.py) for every G2 input, shaped as the frozen texts declare
them; a fake network (fetch_extract.NET) serves them. No G2 carrier, map, workbook, supplement, repository list or
decoder output is opened, downloaded, hashed or listed; reference files allowed in phase 1 are read (abagen's DK atlas
volume and atlas info, the AHBA dk matrix's header, the WP2 build records, the frozen S-build module).

Part A  units: the G2 label normaliser (R42 (d) + the 'm' marker, the two aliases, a declared side); Patel's eTable 4
        from words (the x-overlap column; a missing row refused); Giacomel's sheet object (34 / 7, the alphabetical
        order asserted; a swap refused); the ENIGMA Toolbox tables and the L / R map (ventricles dropped); Hansen's
        headerless matrix, the PC1 column by identity, the Cammoun order; Pretzsch's label / feature columns;
        a repository list; a GEDAR map (ids and names); figshare's file list; the HCP label list; the R script's
        packages; the dominance port against a brute-force Shapley value and its efficiency; R17's parameters
        (declared version, the r-hub release at the commit date, the Bioconductor release); the draft guard.
Part S  the G2 material stage end to end on the stand-ins (every step): statuses; the network log (no request for a
        pinned local copy; the annot streamed; one GET per decoder); values read back equal to the planted values;
        Giacomel's c022a29 comparison (1 differing cell); the gated sets (frozen S-build) and the restatement (< 5);
        the print rule over everything emitted and written (no planted identifier, undeclared sheet or header text);
        an identical re-run adopts every object (a new manifest version, objects unchanged).
Part F  refusals: a changed byte of a pinned copy -> 'not auditable (map changed)'; a missing eTable 4 row; a
        Giacomel order swap (fail-closed sheet object); R16's non-regular member (no fallback) and its header that
        differs from the probe (recorded, not refused); preflight without R13's record (no carrier, no request).
Part U  the loaders (WP4Sources) on the final stand-in manifest: dry dispatch of the 194 G2 rows; prepare() for each
        G2 form x class; Hansen's two components; the signed-weight rows' second map and weights; the reproduction
        wiring (Patel's bicor, Giacomel's |z| rho and the misaligned descriptor, Liu T3, Hansen's dominance,
        Leyhausen's decoder overlap, Pretzsch's recipe on an R38 build of the stand-in volume); tampering at use.
Part B38 the R38 build on the stand-in volume with a fake abagen (arguments asserted; the centroid rule; a parcel of
        the list without voxels refused - the left-masked must-fail variant).
Part R  R17: the script run (docker, network none) in the WP2 R image on a synthetic script (--require-docker turns a
        Docker skip into a failure); run_r17 with a fake builder.
Part P  §11's plants for the G2 forms x classes are in the official battery.
Part C  s17_compare: identical runs give no flag; a changed p is DIFFERS; an R27-only change is LABEL ONLY.
"""
from __future__ import annotations

import argparse
import os
import contextlib
import copy
import dataclasses
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SRC = ROOT / "arcs" / "audit" / "src"
for _p in (ROOT / "src", SRC):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

ap = argparse.ArgumentParser()
ap.add_argument("--scratch", default=None)
ap.add_argument("--require-docker", action="store_true")
ARGS, _ = ap.parse_known_args()
SCRATCH = Path(ARGS.scratch or tempfile.mkdtemp(prefix="a1_wp4p1_")).resolve()
SCRATCH.mkdir(parents=True, exist_ok=True)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from a1_audit import fetch_extract as FE  # noqa: E402
from a1_audit import privacy_wrap as PW  # noqa: E402
from a1_audit import reparcel as RP  # noqa: E402
from a1_audit import run as R  # noqa: E402
from a1_audit import wp3_genes as WG  # noqa: E402
from a1_audit import wp3_layout as W3  # noqa: E402
from a1_audit import wp4_layout as L  # noqa: E402
from a1_audit import wp4_material as WM  # noqa: E402
from a1_audit import wp4_read as RD  # noqa: E402
from a1_audit import wp4_repro as RP4  # noqa: E402
from a1_audit import wp4_scratch as SC  # noqa: E402
from a1_audit import wp4_sets as WS  # noqa: E402
from a1_audit import wp4_sources as W4S  # noqa: E402

RESULTS: dict = {}
FAILED: list = []
CHECKS: list = []
STATE: dict = {}


def check(name):
    def deco(fn):
        def run():
            t0 = time.time()
            try:
                measured = fn() or {}
                RESULTS[name] = dict(result="pass", seconds=round(time.time() - t0, 2), **measured)
                print(f"  PASS  {name} ({time.time() - t0:.1f}s)", flush=True)
            except Exception as e:  # noqa: BLE001
                FAILED.append(name)
                RESULTS[name] = dict(result="FAIL", error=f"{type(e).__name__}: {e}"[:600],
                                     trace=traceback.format_exc()[-2500:])
                print(f"  FAIL  {name}: {type(e).__name__}: {str(e)[:300]}".encode("ascii", "replace").decode(),
                      flush=True)
        CHECKS.append(run)
        return fn
    return deco


def raises(fn, exc, status: str | None = None):
    try:
        fn()
    except exc as e:
        if status is not None and getattr(e, "status", None) != status:
            raise AssertionError(f"raised {type(e).__name__} with status {getattr(e, 'status', None)!r}") from None
        return e
    raise AssertionError(f"did not raise {exc.__name__}")


# ================================================================================================================
# the fake network and the stage harness
# ================================================================================================================
class Net:
    def __init__(self, served: dict):
        self.served = dict(served)
        self.calls: list = []

    def head(self, url):
        self.calls.append(("HEAD", url))
        d = self.served.get(url)
        return {"status_code": 200 if d is not None else 404, "content_length": len(d) if d is not None else None,
                "last_modified": "Tue, 27 Jun 2023 10:00:00 GMT", "etag_md5": None,
                "content_type_label": "not an html page"}

    def get(self, url, out):
        self.calls.append(("GET", url))
        d = self.served.get(url)
        if d is None:
            raise RuntimeError(f"HTTP 404 for {url}")
        Path(out).write_bytes(d)
        return {"url": url, "path": str(out), "sha256": hashlib.sha256(d).hexdigest(), "bytes": len(d)}

    @contextlib.contextmanager
    def stream(self, url):
        self.calls.append(("STREAM", url))
        yield io.BytesIO(self.served[url])


@contextlib.contextmanager
def network(net: Net):
    old = dict(FE.NET)
    FE.NET.update(head=net.head, get=net.get, stream=net.stream)
    try:
        yield net
    finally:
        FE.NET.clear()
        FE.NET.update(old)


def plant_r13(roots) -> None:
    c = Path(roots.control) / "G2"
    c.mkdir(parents=True, exist_ok=True)
    (c / "r13_bicor_check.json").write_text(json.dumps({"schema": WM.R13_SCHEMA, "exit": 0, "wgcna_check": "PASS",
                                                        "repro_py_lf_sha256": WM.repro_sha256()}), encoding="utf-8")


def fake_abagen(calls: dict):
    from a1_audit import ahba_builds as AB

    def get(atlas, atlas_info, **kw):
        calls["kw"], calls["n_ids"] = kw, len(atlas_info)
        calls["hemi"] = atlas_info["hemisphere"].value_counts().to_dict()
        ids = [int(i) for i in atlas_info.index]
        genes = STATE["facts"]["genes"][:80]
        rng = np.random.default_rng(38)
        donors = {d: pd.DataFrame(rng.normal(size=(len(ids), len(genes))), index=pd.Index(ids, name="label"),
                                  columns=genes) for d in AB.DONORS}
        cnt = pd.DataFrame(np.ones((len(ids), 6), dtype=int), index=pd.Index(ids, name="label"), columns=list(AB.DONORS))
        return donors, cnt
    return get


class draft_guard:
    """The draft guard re-armed for a test (the module pin unset): no production stage can start inside it."""
    def __enter__(self):
        self.keep = L.AMEND4_FROZEN_SHA256
        L.AMEND4_FROZEN_SHA256 = None
        return self

    def __exit__(self, *exc):
        L.AMEND4_FROZEN_SHA256 = self.keep
        return False


def stage_hooks(b: dict, calls: dict) -> dict:
    hg = WG.HGNCTable((Path(b["roots"].data) / "hgnc.txt").read_bytes())
    uni = {c: {g: [g] for g in b["facts"]["genes"]} for c in ("dk-ctx", "V-DK", "V-AAL", "MIST64")}
    sb = WS.frozen_s_build()

    def sets(r, man, out=None):
        return WM.build_sets(r, man, hg=hg, uni=uni, sb=sb, out=out)

    def r38(r, em):
        from a1_audit import ahba_builds as AB
        from a1_audit import ahba_extras as AX
        old = AB.OUT
        AB.OUT = Path(r.hcp_build).parent
        try:
            rec = AX.build_perdonor_hcpmmp1(Path(r.data) / L.HCP_VOL_KEY / "carrier.nii.gz",
                                            (Path(r.data) / L.HCP_LIST_KEY / "carrier.txt").read_text(encoding="utf-8"),
                                            Path(r.hcp_build), get_expression_data=fake_abagen(calls))
        finally:
            AB.OUT = old
        rp = Path(r.hcp_build) / "build_record.json"
        return {"status": "built", "exit": 0, "record_sha256": hashlib.sha256(rp.read_bytes()).hexdigest(),
                "n_outputs": len(rec["outputs"])}
    def r17(r, man, door, em, out):
        from a1_audit.rbuild import r17 as R17
        if not docker_ok():
            if ARGS.require_docker:
                raise AssertionError("Docker or the WP2 R image is unavailable (--require-docker)")
            return {"r17": {"status": "not run (Docker unavailable)"}}
        dk = R17.DockerR17(Path(r.artifacts) / L.GATE / "r17", base="a1-audit-r:wp2-r4.4.3", preinstalled=True,
                           timeout=1800)
        return WM.run_r17(r, man, door, em, out, docker=dk)
    return {"sets": sets, "r38": r38, "r17": r17}


def all_written_text(root: Path) -> str:
    parts = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix in (".json", ".log", ".md", ".txt") and "data" not in p.relative_to(root).parts[:1]:
            parts.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


# ================================================================================================================
# Part A - units
# ================================================================================================================
DK = SC.dk_table()


@check("A1 normaliser: R42 (d) + the m marker, the aliases, a declared side; fail closed")
def _a1():
    left_ctx = RD.left_ids_of(DK, "cortex")
    labs = [f"M_{n}_thickavg" for n in SC.dk_names(DK, "L", "cortex")]
    r = RD.g2_normalise(labs, DK, unmarked=None, structures=("cortex",), status="x")
    assert sorted(r["ids"]) == sorted(left_ctx) and r["counts"]["n_bilateral_mean"] == 34
    sub = RD.g2_normalise(["Maccumb", "Mamyg", "Mcaud", "Mhippo", "Mpal", "Mput", "Mthal"], DK, unmarked=None,
                          structures=("subcortex/brainstem",), status="x")
    assert sub["counts"]["n_glued_markers"] == 7 and None not in sub["ids"]
    full = RD.g2_normalise(["Thalamus", "Accumbens"], DK, unmarked="L", structures=("subcortex/brainstem",), status="x")
    assert None not in full["ids"]
    pat = RD.g2_normalise(["caudal anterior cingulate", "bankssts"], DK, unmarked="L", structures=("cortex",),
                          status="x")
    assert all(i in left_ctx for i in pat["ids"])
    raises(lambda: RD.g2_normalise(["bankssts"], DK, unmarked=None, status="no side"), RD.W4Refused, "no side")
    raises(lambda: RD.g2_normalise(["L_bankssts", "Lbankssts"], DK, unmarked=None, status="coll"), RD.W4Refused,
           "coll")
    raises(lambda: RD.g2_normalise(["L_notaregion"], DK, unmarked=None, status="un"), RD.W4Refused, "un")
    vent = RD.g2_normalise(["LLatVent", "L_bankssts"], DK, unmarked=None, status="x")
    assert vent["counts"]["n_dropped_latvent"] == 1
    return {"n": 34}


def _words_for(values, drop=None, header="Estimate"):
    names = SC.dk_names(DK, "L", "cortex")
    words = [(50.0, 40.0, 80.0, 48.0, "Region"), (300.0, 40.0, 340.0, 48.0, header), (360.0, 40.0, 380.0, 48.0, "SE")]
    y = 60.0
    for j, (n, v) in enumerate(zip(names, values)):
        if j == drop:
            continue
        toks = n.split(" ")
        x = 50.0
        for t in toks:
            words.append((x, y, x + 30, y + 8, t))
            x += 35
        words.append((302.0, y, 330.0, y + 8, f"{v:.4f}".replace("-", "\u2212")))
        words.append((362.0, y, 378.0, y + 8, "0.01"))
        y += 12
    words.append((50.0, y + 10, 90.0, y + 18, "Abbreviations"))
    return words


@check("A2 Patel eTable 4 from words (R53): the Estimate column by x-overlap; a missing row or two headers refused")
def _a2():
    vals = list(np.linspace(-0.05, 0.03, 34))
    r = RD.patel_from_words(_words_for(vals), DK)
    names = SC.dk_names(DK, "L", "cortex")
    want = dict(zip([int(i) for i in DK[(DK["hemisphere"] == "L") & (DK["structure"] == "cortex")]["id"]], vals))
    assert all(abs(want[i] - v) < 5e-5 for i, v in zip(r["ids"], r["values"])), "values"
    raises(lambda: RD.patel_from_words(_words_for(vals, drop=5), DK), RD.W4Refused, L.STATUS_PATEL_LAYOUT)
    w2 = _words_for(vals) + [(300.0, 500.0, 340.0, 508.0, "Estimate")]
    raises(lambda: RD.patel_from_words(w2, DK), RD.W4Refused, L.STATUS_PATEL_LAYOUT)
    return {"n_names": len(names)}


@check("A3 Giacomel sheet objects (R54 v2): 34 / 7 by DK id; an order swap recorded, T by label (B4)")
def _a3():
    labs = [f"M_{n}_thickavg" for n in SC.dk_names(DK, "L", "cortex")]
    vals = list(np.arange(34) / 100)
    o = RD.giacomel_sheet_object(labs, vals, vals, DK, "thickness")
    assert len(o["asd"]["ids"]) == 34
    sub = ["Maccumb", "Mamyg", "Mcaud", "Mhippo", "Mpal", "Mput", "Mthal"]
    o2 = RD.giacomel_sheet_object(sub, [1.0] * 7, [2.0] * 7, DK, "subcortical")
    assert o2["order_check"].startswith("registered")
    assert o2["order_matched"] is True
    swap = [sub[1], sub[0]] + sub[2:]
    o3 = RD.giacomel_sheet_object(swap, [1.0, 9.0, 1.0, 1.0, 1.0, 1.0, 1.0], [2.0] * 7, DK, "subcortical")
    assert o3["order_matched"] is False and o3["order_check"] == RD.GIA_ORDER_NOT_MATCHED
    # by label: 9.0 sat on the accumbens row of the swapped sheet
    by = dict(zip(o3["asd"]["ids"], o3["asd"]["values"]))
    acc = next(int(r["id"]) for _, r in DK.iterrows() if r["hemisphere"] == "L" and r["label"] == "accumbensarea")
    assert by[acc] == 9.0 and sorted(o3["asd"]["values"]) == sorted([1.0] * 6 + [9.0])
    dup = [sub[0], sub[0]] + sub[2:]
    raises(lambda: RD.giacomel_sheet_object(dup, [1.0] * 7, [2.0] * 7, DK, "subcortical"), RD.W4Refused,
           L.STATUS_GIA_LAYOUT)
    raises(lambda: RD.giacomel_sheet_object(labs, vals[:-1] + ["x"], vals, DK, "thickness"), RD.W4Refused,
           L.STATUS_GIA_LAYOUT)
    cmp_ = RD.giacomel_compare({"thickness": o, "subcortical": o2},
                               {"thickness": RD.giacomel_sheet_object(labs, [v + (j == 0) for j, v in enumerate(vals)],
                                                                      vals, DK, "thickness"), "subcortical": o2})
    assert cmp_["thickness"]["n_cells_differing"] == 1 and cmp_["subcortical"]["n_cells_differing"] == 0
    return {}


@check("A4 ENIGMA Toolbox tables and the L / R map (R59); Hansen (R60); Pretzsch (R61); lists / GEDAR (R55-R56)")
def _a4():
    rng = np.random.default_rng(1)
    ct = RD.enigma_toolbox(SC.enigma_cortthick(DK, rng), DK, "cortthick")
    sv = RD.enigma_toolbox(SC.enigma_subvol(rng), DK, "subvol")
    assert sv["counts"]["n_dropped_latvent"] == 2 and len(ct["by_id"]) == 68
    m = RD.liu_t3_map(ct, sv, DK)
    lid = {(str(r["label"]), str(r["hemisphere"])): int(r["id"]) for _, r in DK.iterrows()}
    k = lid[("bankssts", "L")]
    want = (ct["by_id"][lid[("bankssts", "L")]] + ct["by_id"][lid[("bankssts", "R")]]) / 2
    assert abs(dict(zip(m["ids"], m["values"]))[k] - want) < 1e-12 and m["n_missing"] == 1   # the brainstem
    bad = SC.enigma_subvol(rng).replace(b"Lthal", b"Lxyz")
    raises(lambda: RD.enigma_toolbox(bad, DK, "subvol"), RD.W4Refused, L.STATUS_ENIGMA_LAYOUT)
    hf = SC.hansen_files(rng)
    assert np.allclose(RD.hansen_ct(hf["ct"]), hf["ct_values"][:, 2], atol=1e-6)
    pr = RD.hansen_predictors(hf["pred"], RD.hansen_pc1(hf["pc1"]))
    assert pr["pc1_column"] == 4 and pr["has_header"]
    raises(lambda: RD.hansen_ct(b"a,b\n" + hf["ct"]), RD.W4Refused)
    cam_b, order = SC.cammoun_info(DK)
    cam = RD.cammoun_order(cam_b, DK)
    name_of = {int(r["id"]): str(r["label"]) for _, r in DK.iterrows()}
    assert [name_of[i] for i in cam["left_row_ids"]] == order
    left = [f"L_P{i:03d}_ROI" for i in range(1, 181)]
    pc = RD.pretzsch_csv(SC.pretzsch_csv(left, rng), left)
    assert len(pc["CT"]) == len(pc["SA"]) == 180
    raises(lambda: RD.pretzsch_csv(SC.pretzsch_csv(left[:179] + ["L_Q_ROI"], rng), left), RD.W4Refused,
           L.STATUS_PRE_LAYOUT)
    g = RD.gedar_map(SC.gedar_tsv(DK, rng, by_names=False), DK)
    g2 = RD.gedar_map(SC.gedar_tsv(DK, rng, by_names=True), DK)
    assert g["label_form"] == "abagen DK ids" and g2["label_form"].startswith("names") and len(g2["by_id"]) == 82
    return {}


@check("A5 figshare list, HCP labels (R52 / R15), R script requirements (R58), dominance port, R17 params, guard")
def _a5():
    meta = {"files": [{"name": L.HCP_VOLUME_NAME, "size": 3, "computed_md5": "a" * 32, "download_url": "https://x/1"},
                      {"name": L.HCP_VOLUME_NAME[:-7] + ".txt", "size": 4, "computed_md5": "b" * 32,
                       "download_url": "https://x/2"}]}
    f = RD.figshare_files(json.dumps(meta).encode())
    assert f["volume"]["md5"] == "a" * 32 and "url" in f["labels"]
    meta["files"].append(dict(meta["files"][0]))
    raises(lambda: RD.figshare_files(json.dumps(meta).encode()), RD.W4Refused)
    _, text, left = SC.hcp_volume(DK)
    h = RD.hcp_left_names(text)
    assert h["left_names"] == left and len(h["left_ids"]) == 180
    raises(lambda: RD.hcp_left_names("1 L_A_ROI\nbad line\n"), RP.ReparcelRefused)
    req = RD.r_script_requirements("library(readxl)\n# library(no)\nrequire('dplyr')\nWGCNA::bicor(x)\n"
                                   "stats::sd(1)\nx <- read.csv(\"data/a.csv\")\n")
    assert req["packages"] == ["WGCNA", "dplyr", "readxl"] and req["read_paths"] == ["data/a.csv"], req
    rng = np.random.default_rng(5)
    X, y = rng.normal(size=(40, 4)), rng.normal(size=40)
    d = RP4.dominance_stats(X, y, use_adjusted_r_sq=True)
    from itertools import combinations
    from math import comb
    p = 4
    shap = np.zeros(p)
    for j in range(p):
        others = [i for i in range(p) if i != j]
        for k in range(p):
            for c in combinations(others, k):
                inc = RP4._r2(X, y, tuple(sorted(c + (j,))), True) - (RP4._r2(X, y, c, True) if c else 0.0)
                shap[j] += inc / (p * comb(p - 1, k))
    assert np.allclose(shap, d["total_dominance"], atol=1e-12) and np.isclose(d["total_dominance"].sum(),
                                                                                  d["full_r_sq"])
    from a1_audit.rbuild import r17 as R17
    rv = json.dumps([{"version": "4.3.3", "date": "2024-02-29T08:00:00Z"}, {"version": "4.4.0", "date": "2024-04-24"},
                     {"version": "4.4.1", "date": "2024-06-14"}]).encode()
    cfg = (b"release_dates:\n  \"3.18\": \"10/25/2023\"\n  \"3.19\": \"05/01/2024\"\n  \"3.20\": \"10/30/2024\"\n"
           b"r_ver_for_bioc_ver:\n  \"3.18\": \"4.3\"\n  \"3.19\": \"4.4\"\n  \"3.20\": \"4.4\"\nother: 1\n")
    p1 = R17.r17_params(commit="e" * 40, commit_date="2024-09-01T10:00:00+02:00", decl_files={}, rversions=rv,
                        bioc_config=cfg, script=b"library(WGCNA)\n", codename="noble")
    assert p1["r"]["version"] == "4.4.1" and p1["bioc"]["version"] == "3.19" and p1["packages"] == ["WGCNA"]
    assert p1["cran"].endswith("/noble/2024-09-01")
    p2 = R17.r17_params(commit="e" * 40, commit_date="2024-05-10", decl_files={"renv.lock": b'{"R": {"Version": "4.3.3"}}'},
                        rversions=rv, bioc_config=cfg, script=b"", codename="jammy")
    assert p2["r"]["version"] == "4.3.3" and p2["r"]["basis"] == "renv.lock R.Version" and p2["bioc"]["version"] == "3.18"
    assert "FROM rocker/r-ver:4.4.1@sha256:" in R17.dockerfile_text(p1, "sha256:" + "0" * 64)
    # amendment 4 v3 is frozen (FROZEN.txt, commit 1c5143d): the freeze check passes on the real pin and fails on a
    # planted one; under the draft guard (the pin unset) the production stage refuses before anything is opened
    fc = L.frozen_check()
    # amendment 5 (draft, 2026-10-21): with its pin unset, production refuses by DRAFT_GUARD5 even with amend_4 frozen
    if L.AMEND5_FROZEN_SHA256 is None:
        assert fc["ok"] and L.production_allowed() == (False, L.DRAFT_GUARD5), fc
        assert not L.frozen_check(rel=L.AMEND5_REL)["ok"]
    else:
        assert fc["ok"] and L.production_allowed() == (True, "frozen"), fc
    assert not L.frozen_check(pin="0" * 64)["ok"]
    with draft_guard():
        ok, why = L.production_allowed()
        assert not ok and why == L.DRAFT_GUARD
        raises(lambda: WM.run_material(L.Roots.production()), WM.PreflightRefused)
    return {}


# ================================================================================================================
# Part S - the stage end to end
# ================================================================================================================
@check("S1 the G2 material stage on the stand-ins: every step; statuses; network; values; sets; print rule")
def _s1():
    root = SCRATCH / "stage"
    if root.exists():
        shutil.rmtree(root)
    b = SC.build(root)
    STATE.update(b=b, facts=b["facts"])
    roots = b["roots"]
    plant_r13(roots)
    calls: dict = {}
    out = io.StringIO()
    with network(Net(b["net"])) as net:
        man = WM.run_material(roots, out=out, hooks=stage_hooks(b, calls))
    STATE.update(roots=roots, man=man)
    objs = man["objects"]
    assert man["final"] is True
    not_ok = {k: e.get("status") for k, e in objs.items()
              if e.get("status") not in (FE.STATUS_EXTRACTED, FE.STATUS_IDENTITY_ONLY, "built")}
    assert set(not_ok) == {"r17"}, not_ok
    # network: the pinned local copies are never requested; the annot is streamed; one GET per decoder
    urls = [u for _, u in net.calls]
    for k in (L.PATEL_KEY, L.HANSEN_CT_KEY, L.LIU_CT_KEY, L.PRE_KEY, L.GIA_CMP_KEY):
        assert not any("none.invalid" in u for u in urls)
    assert sum(1 for m, u in net.calls if m == "STREAM") == 1
    assert sum(1 for m, u in net.calls if m == "GET" and "gene_expression" in u) == 3
    assert not any("neurovault.org/media" in u and m == "GET" for m, u in net.calls)
    # values read back
    pat = WM.object_of(roots, objs[L.PATEL_KEY], "etable4")
    assert np.allclose(pat["values"], np.round(b["facts"]["patel_values"], 4), atol=1e-12)
    th = WM.object_of(roots, objs[L.GIA_GOV_KEY], "thickness")
    assert np.allclose(th["asd"]["values"], b["facts"]["gia_asd_thickness"], atol=1e-12)
    assert man["giacomel_comparison"]["thickness"]["n_cells_differing"] == 1
    assert WM.object_of(roots, objs[L.HANSEN_PRED_KEY], "predictors")["pc1_column"] == 4
    assert len(WM.object_of(roots, objs[L.PRE_KEY], "etable13")["CT"]) == 180
    assert len(WM.object_of(roots, objs[L.LEY_LH_KEY[777428]], "dkctx")["ids"]) == 34
    # Giacomel: the undeclared sheet was never touched
    rec = json.loads((Path(roots.records) / objs[L.GIA_GOV_KEY]["record_path"]).read_bytes())
    assert rec["sheets"]["parts_opened_undeclared"] == 0 and rec["sheets"]["access_log_declared_only"]
    # sets: the 23 list cells and the 18 post-mortem DEG cells (R58 (f): the TSV's definition, the ASD pool of 3,599)
    # built by the frozen build_set; the 1 % down-only list (3 genes) -> < 5 in both classes
    assert man["sets"]["n_sets"] == 41 and man["sets"]["restatement"]["n_not_testable_lt5"] == 2
    sm = json.loads((roots.set_dir() / L.SET_MANIFEST_NAME).read_bytes())
    assert sm["restatement"]["cells"]["GIA-C13"]["outcome"] == WS.LT5
    c19 = json.loads((roots.set_dir() / "gated_G2_GIA-C19.json").read_bytes())
    assert c19["n_hgnc"] == 36 and c19["source"]["n_pool"] == 3599 and c19["weights"], c19["source"]
    assert c19["source"]["object"] == "r17_deg_ASD_1" and c19["source"]["m_script"] == 36, c19["source"]
    m10 = json.loads((roots.set_dir() / "gated_G2_GIA-MDD-DEG-MDDset-10-ctx.json").read_bytes())
    assert m10["source"]["m_script"] == 90 and m10["source"]["m_definition"] == 90
    sad = WM.object_of(roots, objs[L.SADEGHI_KEY], "deg")
    assert sad["n_rows_excluded_by_type"] == b["facts"]["deg_excluded"], sad["n_rows_excluded_by_type"]
    chk = man["deg_checks"]["GIA-C19"]
    assert chk["passed"] and chk["cross_check"]["equal"] and chk["cross_check"]["role"].startswith("cross-check")
    assert objs["r17"]["status"] == "ran" and objs["r17"]["network"] == "none" and objs["r17"]["exit"] == 0
    assert objs["r17"]["build"]["base_override"] is True and objs["r17"]["r_version"] == "4.4.1" and objs["r17"]["n_packages"] == 0
    assert objs["r17_map_ASD_1"]["status"] == FE.STATUS_EXTRACTED
    # R38 on the stand-in: abagen called with every listed parcel and return_donors
    assert calls["n_ids"] == 360 and calls["kw"]["return_donors"] is True
    # the print rule over everything emitted and written
    planted = b["facts"]["planted"]
    text = out.getvalue() + all_written_text(root / "out")
    for s in (planted, f"subj_{planted}", "ADHD", "receptor_pc1", "area_label", "Abbreviations", "Maccumb",
              "M_bankssts_thickavg", "L_P001_ROI"):
        assert s not in out.getvalue(), s
    for s in (planted, f"subj_{planted}", "ADHD", "receptor_pc1", "area_label", "Abbreviations", "Maccumb"):
        assert s not in text, s
    return {"n_objects": len(objs), "n_calls": len(net.calls)}


@check("S2 an identical re-run adopts every object (a new manifest version; objects unchanged)")
def _s2():
    b, roots, man1 = STATE["b"], STATE["roots"], STATE["man"]
    calls: dict = {}
    with network(Net(b["net"])) as net2:
        man2 = WM.run_material(roots, out=io.StringIO(), hooks=stage_hooks(b, calls))
    assert Path(man2["_path"]).name == "wp4_material_manifest.2.json"
    # resume (2026-10-17): no carrier fetched again, the annot not streamed again; only the decoders' size probes
    # (R45's form) and none of their GETs
    gets = [u for m, u in net2.calls if m in ("GET", "STREAM")]
    assert not gets, len(gets)
    assert man2["objects"][L.FS_KEY].get("resumed"), man2["objects"][L.FS_KEY].get("status")
    # every object is adopted unchanged, except R17's run outputs: each run saves them under its own run-indexed key
    # (never overwriting an earlier run's object), so for those the CONTENT (the list rows, the map) must be equal
    r17 = [k for k in man1["objects"] if k.startswith(("r17_deg_", "r17_map_"))]
    same = [k for k, e in man1["objects"].items() if e.get("object_sha256") and k not in r17
            and man2["objects"][k].get("object_sha256") == e["object_sha256"]]
    n_obj = sum(1 for k, e in man1["objects"].items() if e.get("object_sha256") and k not in r17)
    assert len(same) == n_obj, (len(same), n_obj)
    for k in r17:
        sub = "raw" if k.startswith("r17_deg_") else "map"
        e1, e2 = man1["objects"][k], man2["objects"][k]
        assert e1["object_key"] != e2["object_key"], k
        assert WM.object_of(roots, e1, sub) == WM.object_of(roots, e2, sub), k
    assert len(r17) == 12
    STATE["man"] = man2
    return {"n_objects_adopted": len(same)}


# ================================================================================================================
# Part F - refusals
# ================================================================================================================
@check("F1 refusals: a changed byte -> map changed; R16 non-regular / header differs; preflight without R13")
def _f1():
    root = SCRATCH / "fail"
    if root.exists():
        shutil.rmtree(root)
    b = SC.build(root, seed=9)
    roots = b["roots"]
    plant_r13(roots)
    # a changed byte of the Liu CortThick copy
    idr = json.loads(Path(roots.identity_json).read_text())
    lp = [p["path"] for r in idr["records"] if r["object"] == L.IDENTITY_OBJECT[L.LIU_CT_KEY] for p in r["probes"]
          if "path" in p][0]
    data = bytearray(Path(lp).read_bytes())
    data[-3] = ord("9") if data[-3] != ord("9") else ord("8")
    Path(lp).write_bytes(bytes(data))
    # R16: the first tarball's annot is a symbolic link (no fallback); a Patel PDF without one row
    served = dict(b["net"])
    served[L.FS_DIR + L.FS_TARBALLS[0]] = SC.tar_stream(b"", regular=False)
    SC.patel_pdf(Path([p["path"] for r in idr["records"] if r["object"] == L.IDENTITY_OBJECT[L.PATEL_KEY]
                       for p in r["probes"] if "path" in p][0]), DK, b["facts"]["patel_values"], drop_row=True)
    from a1_audit import identity as ID
    pp = [p for r in idr["records"] if r["object"] == L.IDENTITY_OBJECT[L.PATEL_KEY] for p in r["probes"]][0]
    f = ID.file_facts(Path(pp["path"]))
    pp.update(size=f["bytes"], sha256=f["sha256"], git_blob_sha=f["git_blob"])
    Path(roots.identity_json).write_text(json.dumps(idr), encoding="utf-8")
    with network(Net(served)):
        man = WM.run_material(roots, out=io.StringIO(), steps=[0, 1, 2, 3, 5])
    o = man["objects"]
    assert o[L.LIU_CT_KEY]["status"] == ID.STATUS_CHANGED, o[L.LIU_CT_KEY]
    assert o[L.FS_KEY]["status"] == RP.STATUS_FS_NOT_MATCHING and len(o[L.FS_KEY]["artefacts_tried"]) == 1
    assert o[L.PATEL_KEY]["status"] == L.STATUS_PATEL_LAYOUT, o[L.PATEL_KEY]
    assert all(o[L.LEY_LH_KEY[i]]["status"] == RP.STATUS_FS_NOT_MATCHING for i in L.LEY_IMAGES)
    # R51: a ubuntu22 tarball whose Content-Length differs from the probe is recorded, not refused
    rec = json.loads((Path(roots.records) / "G2").joinpath(f"{L.FS_KEY}.json").read_bytes())
    assert rec["status"] == RP.STATUS_FS_NOT_REGULAR
    # preflight without R13's record: refused before any request
    (Path(roots.control) / "G2" / "r13_bicor_check.json").unlink()
    net = Net(b["net"])
    with network(net):
        raises(lambda: WM.run_material(roots, out=io.StringIO()), WM.PreflightRefused)
    assert net.calls == []
    return {}


@check("F2 R51: the probe's Content-Length differing is recorded and labelled, the member still taken")
def _f2():
    root = SCRATCH / "fail2"
    if root.exists():
        shutil.rmtree(root)
    b = SC.build(root, seed=11)
    roots = b["roots"]
    plant_r13(roots)
    with network(Net(b["net"])):
        man = WM.run_material(roots, out=io.StringIO(), steps=[0, 1, 2])
    e = man["objects"][L.FS_KEY]
    assert e["status"] == FE.STATUS_EXTRACTED and e["artefacts_tried"][0]["headers"]["vs_probe"].startswith("differs")
    return {}


# ================================================================================================================
# Part U - the loaders and the reproduction wiring
# ================================================================================================================
def sources():
    if "src" not in STATE:
        STATE["src"] = W4S.WP4Sources(STATE["roots"], W3.Roots.production())
    return STATE["src"]


@check("U1 dry dispatch of the 194 G2 rows on the final stand-in manifest")
def _u1():
    rows = [r for r in R.register_for_diagnostics(R.REPO) if r.gate == "G2"]
    assert len(rows) == 194
    recs = R.dry_dispatch(rows, frozenset({"G2"}), plant_view=False, sources=sources())
    by = {}
    for r in recs:
        by[r["outcome"]] = by.get(r["outcome"], 0) + 1
    pend = [r for r in recs if r["outcome"] == "not run"]
    # B5: the 18 post-mortem DEG cells now load too (S re-derived by the stand-in script's R17 run); every computing
    # row loads, none waits
    assert by.get("would compute") == 128 and not pend and by.get("no statistic") == 66, by
    return {"by_outcome": by}


@check("U2 prepare() for each G2 form x class; components; second map / weights; reproduction wiring")
def _u2():
    src = sources()
    rows = {r.row: r for r in R.register_for_diagnostics(R.REPO)}
    plan = {n: R.classify(rows[n], frozenset({"G2"})) for n in (81, 85, 91, 92, 103, 104, 118, 478, 523, 624, 625,
                                                                  626)}
    out = {}
    for n in (81, 91, 92, 118, 478, 523, 626):
        pr = R.prepare(plan[n], src, plan[n]["maps"][0])
        out[n] = (pr.ctx.n, None if pr.S is None else len(pr.S))
    assert out[81][0] == 34 and out[92][0] == 7 and out[478][0] == 41, out
    for n in (624, 625):
        pr = R.prepare(plan[n], src, plan[n]["maps"][0])
        assert pr.component is not None and np.isfinite(pr.component).all() and pr.ctx.n == 34
    # Hansen's component: the shipped PC1's left rows in the Cammoun order
    c, ids, _ = src.component(plan[624])
    cam = STATE["facts"]["cammoun_order"]
    name_of = {int(r["id"]): str(r["label"]) for _, r in DK.iterrows()}
    pc1 = STATE["facts"]["hansen_pc1"]
    by = dict(zip([int(i) for i in ids], c))
    k = cam.index(name_of[int(ids[0])])
    assert abs(by[int(ids[0])] - round(pc1[34 + k], 6)) < 1e-9
    b, bids, _ = src.second_map(plan[103], 0)
    genes, w, _ = src.gene_weights(plan[103])
    assert len(genes) == len(w) > 0 and np.isfinite(b).sum() == 34
    inp, h = R._form_inputs(plan[103], src, "descriptor")
    assert inp["weights"].shape == (len(inp["genes"]),)
    reps = {n: RP4.row_reproduction(plan[n], src) for n in (81, 85, 91, 92, 118, 478, 624, 626)}
    assert reps[81]["check"]["functional"] == "mean bicor" and "informational" in reps[85]["kind"]
    assert reps[92]["registered"] == RP4.NOT_REPRO_DEFECT and "misaligned_rho" in reps[92]
    assert reps[478]["check"]["functional"] == "rank-biserial"
    assert reps[624]["checks"]["R2_adj"]["functional"] == "R2_adj"
    assert reps[624]["blind"].startswith("NOT BLIND")                    # asdg-skeptic C1
    assert reps[626]["overlap"]["k"] >= 0 and reps[626]["paper_list_n"] == 480
    pre = RP4.row_reproduction(plan[523], src)
    assert pre["recipe"]["sign"] == -1 and "overlap" in pre, pre
    return {"prepared": {str(k): v for k, v in out.items()}}


@check("U3 tampering at use: an object byte -> refused; a pinned copy's byte -> map changed")
def _u3():
    roots = STATE["roots"]
    man = STATE["man"]
    e = man["objects"][L.PATEL_KEY]
    op = Path(roots.artifacts) / e["object_path"]
    keep = op.read_bytes()
    src = W4S.WP4Sources(roots, W3.Roots.production())
    rows = {r.row: r for r in R.register_for_diagnostics(R.REPO)}
    p = R.classify(rows[81], frozenset({"G2"}))
    try:
        op.write_bytes(keep.replace(b"etable4", b"etable5", 1))
        raises(lambda: src.map(p, 0), R.SourceUnavailable, L.STATUS_OBJECT_CHANGED)
    finally:
        op.write_bytes(keep)
    idr = json.loads(Path(roots.identity_json).read_text())
    lp = [pp["path"] for r in idr["records"] if r["object"] == L.IDENTITY_OBJECT[L.PATEL_KEY] for pp in r["probes"]][0]
    pk = Path(lp).read_bytes()
    try:
        Path(lp).write_bytes(pk + b"\n")
        src2 = W4S.WP4Sources(roots, W3.Roots.production())
        raises(lambda: src2.map(p, 0), R.SourceUnavailable, L.STATUS_MAP_CHANGED)
    finally:
        Path(lp).write_bytes(pk)
    return {}


@check("U4 the runner's production path on the G2 forms x classes (plant view, synthetic sources; dev run, small K)")
def _u4():
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    out = SCRATCH / "p2g2"
    if out.exists():
        shutil.rmtree(out)
    env = {k: v for k, v in __import__("os").environ.items() if k != "PYTHONPATH"}
    r = subprocess.run([sys.executable, "-X", "utf8", "-u", "-m", "a1_audit.run", "--commit", head, "--pass", "verdict",
                        "--gate", "G2", "--rows", "81,92,103,478,523,624,626", "--plant", "P2", "--dev", "--out",
                        str(out), "--jobs", "3", "--K", "site=120,species=40,permutation=120,sets=40,surr=120,j1_sets=30"],
                       cwd=str(SRC), capture_output=True, env=env, timeout=3600)
    assert r.returncode == 0, r.stdout.decode("utf-8", "replace")[-800:]
    got = {}
    for f in sorted((out / "G2" / "verdict").glob("row_*.json")):
        d = json.loads(f.read_bytes().decode("utf-8"))
        got[d["row"]] = (d["outcome"], ((d.get("result") or {}).get("verdict") or {}).get("primary_status"))
    assert set(got) == {81, 92, 103, 478, 523, 624, 626} and all(v[0] == "computed" for v in got.values()), got
    assert got[92][1] == "resolution-limited", got[92]          # R9: the by-construction label of the Giacomel cells
    return {"rows": {str(k): v[0] for k, v in got.items()}}


# ================================================================================================================
# Part B38, R, P, C
# ================================================================================================================
@check("B38 R38's atlas_info (centroid rule) and the left-masked must-fail variant")
def _b38():
    from a1_audit import ahba_extras as AX
    from a1_audit import ahba_builds as AB
    vol = np.zeros((10, 4, 4), dtype=np.int64)
    aff = np.eye(4)
    aff[0, 3] = -5.0                         # x = i - 5
    vol[0:2] = 1                             # x -5..-4 -> L
    vol[4:6] = 2                             # x -1..0 -> mean -0.5 -> B
    vol[8:10] = 3                            # x 3..4 -> R
    info, counts = AX.hcpmmp1_atlas_info(vol, aff, [(1, "L_A_ROI"), (2, "L_B_ROI"), (3, "L_C_ROI")])
    assert list(info["hemisphere"]) == ["L", "B", "R"] and counts["n_prefix_disagreements"] == 2
    assert set(info["structure"]) == {"cortex"}
    masked = vol.copy()
    masked[masked == 3] = 0
    raises(lambda: AX.hcpmmp1_atlas_info(masked, aff, [(1, "L_A_ROI"), (2, "L_B_ROI"), (3, "R_C_ROI")]),
           AB.BuildError)
    return {}


def docker_ok() -> bool:
    try:
        r = subprocess.run(["docker", "image", "inspect", "a1-audit-r:wp2-r4.4.3"], capture_output=True, timeout=60)
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


@check("R1 R17: the script run (network none) in the WP2 R image on a synthetic script; run_r17 with a fake builder")
def _r1():
    from a1_audit.rbuild import r17 as R17
    out = {}
    if docker_ok():
        work = SCRATCH / "r17work"
        for d in (work, SCRATCH / "r17work_logs", SCRATCH / "r17work_bad", SCRATCH / "r17work_bad_logs"):
            if d.exists():
                shutil.rmtree(d)
        inp = SCRATCH / "r17_in.csv"
        inp.write_text("a,b\n1,2\n", encoding="utf-8")
        script = SCRATCH / "r17_script.R"
        script.write_text("x <- read.csv('data/in.csv')\ndir.create('results', showWarnings=FALSE)\n"
                          "write.table(x * 2, 'results/out.tsv', sep='\\t')\n", encoding="utf-8")
        rec = R17.run_script("a1-audit-r:wp2-r4.4.3", work, "code/s.R", {"code/s.R": script, "data/in.csv": inp},
                             outputs_expected=("results/out.tsv",), timeout=900)
        assert rec["ok"] and rec["exit"] == 0 and rec["declared_outputs_found"] == 1 and rec["network"] == "none", rec
        bad = R17.run_script("a1-audit-r:wp2-r4.4.3", SCRATCH / "r17work_bad", "code/s.R",
                             {"code/s.R": script, "data/other.csv": inp}, outputs_expected=("results/out.tsv",))
        assert not bad["ok"] and bad["status"] == R17.STATUS_R17
        out["docker"] = "run"
    elif ARGS.require_docker:
        raise AssertionError("Docker or the WP2 R image is unavailable (--require-docker)")
    else:
        out["docker"] = "not run: Docker unavailable"
    raises(lambda: R17.run_script("x", Path("E:/data/asdg/x"), "s.R", {}), R17.R17Refused)

    # the production builder's command sequence (an injected command runner; no Docker): pull, digest, codename,
    # build, image id, session info; a base without a repository digest refused
    cmds = []

    class P:
        def __init__(self, rc=0, out=b""):
            self.returncode, self.stdout = rc, out

    def fake_run(cmd, timeout=None):
        cmds.append(cmd[:3])
        if cmd[:3] == ["docker", "image", "inspect"] and "RepoDigests" in cmd[4]:
            return P(0, b"rocker/r-ver@sha256:" + b"a" * 64 + b"\n")
        if cmd[:3] == ["docker", "image", "inspect"]:
            return P(0, b"sha256:" + b"b" * 64 + b"\n")
        if "VERSION_CODENAME" in cmd[-1]:
            return P(0, b"noble\n")
        return P(0, b"R version 4.4.1\n")
    R17._run_saved = R17._run
    R17._run = fake_run                                    # image_codename uses the module's runner
    try:
        dkr = R17.DockerR17(SCRATCH / "r17fake", run=fake_run)
        prm = dkr.params({"commit": "e" * 40, "commit_date": "2024-09-01T10:00:00Z", "decl_files": {},
                          "rversions": json.dumps([{"version": "4.4.1", "date": "2024-06-14"}]).encode(),
                          "bioc_config": b"release_dates:\n  \"3.19\": \"05/01/2024\"\nr_ver_for_bioc_ver:\n"
                                         b"  \"3.19\": \"4.4\"\n", "script": b"library(WGCNA)\n"})
        assert prm["base_digest"] == "sha256:" + "a" * 64 and prm["cran"].endswith("/noble/2024-09-01")
        tag = dkr.build(prm)
        assert tag.startswith("a1-audit-r17:") and dkr.build_record["image_id"] == "sha256:" + "b" * 64
        txt = (SCRATCH / "r17fake" / f"build_{dkr.build_record['dockerfile_sha256'][:12]}" / "Dockerfile").read_text()
        assert "FROM rocker/r-ver:4.4.1@sha256:" + "a" * 64 in txt and "BiocManager::install(c('WGCNA')" in txt
        assert ["docker", "pull", "rocker/r-ver:4.4.1"] in cmds and ["docker", "build", "-t"] in cmds
        raises(lambda: R17.dockerfile_text(prm, "latest"), R17.R17Refused)
    finally:
        R17._run = R17._run_saved
    man = {"objects": {L.R17_SCRIPT_KEY: {"status": FE.STATUS_EXTRACTED},
                       L.R17_AHBA_KEY: {"status": L.STATUS_MAP_CHANGED},
                       L.R17_HPA_KEY: {"status": FE.STATUS_IDENTITY_ONLY}}}
    # 2026-10-21: an input's identity failed before the script ran: never the paper's status
    assert WM.run_r17(None, man, None, None, None, docker=object())["r17"]["status"] == L.STATUS_UPSTREAM
    return out


@check("P1 §11's plants for the G2 forms x classes are in the official battery (P4 cells, P5 / P6 / P24-P26 classes)")
def _p1():
    from a1_audit.plants import p04, driver
    cells = set(p04.CELLS)
    for need in (("set-vs-map", "dk-ctx"), ("set-vs-map", "V-DK"), ("set-vs-map", "V-DK-subcortex"),
                 ("decoded-list", "dk-ctx")):
        assert need in cells, need
    for pid in ("P3a", "P3b", "P4", "P5", "P6", "P8", "P12", "P24", "P25", "P26"):
        assert pid in driver.ORDER
    reg = driver.REG
    cls = {pid: {c.cls for c in reg[pid].cells()} for pid in ("P5", "P6", "P24", "P26", "P12")}
    assert "dk-ctx" in cls["P5"] and "dk-ctx" in cls["P6"] and {"dk-ctx", "V-DK"} <= cls["P24"] | {"dk-ctx"}
    assert "V-DK" in cls["P26"] and "dk-ctx" in cls["P12"]
    return {k: sorted(v) for k, v in cls.items()}


@check("C1 s17_compare: identical -> no flag; a changed p -> DIFFERS; an R27-only change -> LABEL ONLY")
def _c1():
    from a1_audit import s17_compare as SCMP
    base = SCRATCH / "cmp"
    for d in ("old", "new"):
        (base / d / "verdict").mkdir(parents=True, exist_ok=True)
    row = {"outcome": "computed", "status_written": "s", "run_identity": {"run_commit": "a", "code_hash": "h"},
           "result": {"verdict": {"T": 0.1, "survives": False, "reading": "r", "legs": {"S1c": {"p": 0.2,
                                                                                         "seconds": 3}}},
                      "r27": {"0": {"reading": "x", "labels": ["a"]}}}, "inputs": {"hashes": {"map": "1"}}}
    for name, mod in (("row_0001.json", None), ("row_0002.json", "p"), ("row_0003.json", "r27")):
        (base / "old/verdict" / name).write_text(json.dumps(row))
        new = json.loads(json.dumps(row))
        new["run_identity"]["run_commit"] = "b"
        new["result"]["verdict"]["legs"]["S1c"]["seconds"] = 9
        if mod == "p":
            new["result"]["verdict"]["legs"]["S1c"]["p"] = 0.21
        if mod == "r27":
            new["result"]["r27"]["0"]["reading"] = "y"
        (base / "new/verdict" / name).write_text(json.dumps(new))
    doc = SCMP.compare_dirs(base / "old", base / "new")
    fl = {r["file"]: r.get("flag") for r in doc["rows"]}
    assert fl == {"row_0001.json": None, "row_0002.json": "DIFFERS", "row_0003.json": "LABEL ONLY (not expected)"}, fl
    assert doc["n_differing"] == 1 and doc["n_label_only_not_expected"] == 1 and doc["exit"] == 1
    return {}


# ================================================================================================================
# Part V - asdg-skeptic's review of 6fe112e..ea7f936 (2026-10-16): B1-B5, C2, C3, C6, C8
# ================================================================================================================
def _row_doc(row: int, *, reading="auditable (x)", p_h=1e-3, label=None, status="S", route="verdict: set-vs-map",
             K=10000, g6l="exact", seconds=1.0, commit="a" * 40):
    return {"what": "A1 run result", "stamp": f"t{seconds}", "pass": "verdict", "gate": "none", "plant": None,
            "K": {"site": K}, "g6l_mode": g6l, "threads": {"OMP_NUM_THREADS": "1"}, "output_root": "X",
            "run_identity": {"run_commit": commit, "code_hash": commit[::-1], "K": {"site": K}, "g6l_mode": g6l},
            "row": row, "cell_id": f"C{row}", "status_effective": status, "route": route, "outcome": "computed",
            "status_written": "computed", "label": label, "descriptor": True,
            "result": {"T": 0.5, "r27": {"0": {"reading": reading, "labels": ["a"],
                                               "descriptors": {"p_hypergeom": p_h, "R2_grad": 0.1}}}},
            "inputs": {"analysis_parcels": {"0": {"rule": "finite y and >= 2 donors"}}},
            "memory": {"peak": seconds}, "provenance": {"x": seconds}}


def _write_rows(d: Path, docs: dict):
    (d / "verdict").mkdir(parents=True, exist_ok=True)
    for n, doc in docs.items():
        (d / "verdict" / f"row_{n:04d}.json").write_text(json.dumps(doc), encoding="utf-8")


@check("V1 s17_compare (B1, B2, C6): the whole row compared; numeric R27 descriptors and K / route / label ... flagged; "
       "only expected label rows pass")
def _v1():
    import contextlib
    from a1_audit import s17_compare as SC17
    man = {"label_only_expected": [{"pass": "verdict", "rows": [615], "pattern": "r27_reading"}]}
    base = {615: _row_doc(615), 10: _row_doc(10)}
    cases = {
        "volatile only": ({615: _row_doc(615, seconds=9.0, commit="b" * 40)}, 0, None),
        "expected label (615 reading)": ({615: _row_doc(615, reading="auditable (y)")}, 0, "LABEL ONLY (expected)"),
        "label outside the list (10 reading)": ({10: _row_doc(10, reading="auditable (y)")}, 1,
                                                "LABEL ONLY (not expected)"),
        "R27 numeric descriptor (B1)": ({615: _row_doc(615, p_h=2e-3)}, 1, "DIFFERS"),
        "label": ({10: _row_doc(10, label="descriptive")}, 1, "DIFFERS"),
        "status_effective": ({10: _row_doc(10, status="T")}, 1, "DIFFERS"),
        "route": ({10: _row_doc(10, route="verdict: decoded-list")}, 1, "DIFFERS"),
        "K": ({10: _row_doc(10, K=1000)}, 1, "DIFFERS"),
        "g6l_mode": ({10: _row_doc(10, g6l="screened")}, 1, "DIFFERS"),
    }
    got = {}
    for name, (chg, want_exit, want_flag) in cases.items():
        d = SCRATCH / "v1" / name.replace(" ", "_").replace("(", "").replace(")", "")
        if d.exists():
            shutil.rmtree(d)
        _write_rows(d / "old", base)
        _write_rows(d / "new", {**base, **chg})
        doc = SC17.compare_dirs(d / "old", d / "new", man)
        flags = {r["file"]: r.get("flag") for r in doc["rows"]}
        n = next(iter(chg))
        assert doc["exit"] == want_exit and flags[f"row_{n:04d}.json"] == want_flag, (name, doc["exit"], flags)
        (d / "man.json").write_text(json.dumps(man), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            rc = SC17.main(["--old", str(d / "old"), "--new", str(d / "new"), "--out", str(d / "cmp.json"),
                            "--manifest", str(d / "man.json")])
        assert rc == want_exit, (name, rc)
        got[name] = want_flag
    # without the manifest even the expected label row exits 1 (C6); a missing row exits 2
    d = SCRATCH / "v1" / "expected_label_no_manifest"
    _write_rows(d / "old", base)
    _write_rows(d / "new", {**base, 615: _row_doc(615, reading="auditable (y)")})
    assert SC17.compare_dirs(d / "old", d / "new", None)["exit"] == 1
    (d / "new" / "verdict" / "row_0010.json").unlink()
    assert SC17.compare_dirs(d / "old", d / "new", man)["exit"] == 2
    # the real §17 analysis carries the machine-readable expected list
    real = json.loads((ROOT / "arcs/audit/run_manifests/s17_wp4_prerun.json").read_bytes())
    exp = SC17.expected_labels(real)
    assert exp[("verdict", 615)] == {"r27_reading"} and len([k for k in exp if k[0] == "sensitivity"]) == 83
    return {"cases": len(got)}


@check("V3 r38-build (B3): the draft guard, the gate, R13 and the paths before the volume is read; R15 sha256s through")
def _v3():
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), draft_guard():
        rc = WM.main(["r38-build", "--volume", "x.nii.gz", "--labels", "x.txt", "--out", "o", "--volume-sha256",
                      "0" * 64, "--labels-sha256", "0" * 64])
    assert rc == 2 and "refused" in buf.getvalue()           # production roots under the draft guard
    roots = STATE["roots"]
    spec = SCRATCH / "v3_spec.json"
    noctl = L.Roots.from_spec(dict(roots.to_spec(), control=str(SCRATCH / "v3_no_control")))
    spec.write_text(json.dumps(noctl.to_spec()), encoding="utf-8")
    vol = Path(roots.data) / L.HCP_VOL_KEY / "carrier.nii.gz"
    lab = Path(roots.data) / L.HCP_LIST_KEY / "carrier.txt"
    args = ["r38-build", "--volume", str(vol), "--labels", str(lab), "--out", str(roots.hcp_build), "--roots-spec",
            str(spec)]
    vs, ls = hashlib.sha256(vol.read_bytes()).hexdigest(), hashlib.sha256(lab.read_bytes()).hexdigest()
    with contextlib.redirect_stdout(buf):
        assert WM.main(args + ["--volume-sha256", vs, "--labels-sha256", ls]) == 2       # no R13 record
    spec.write_text(json.dumps(roots.to_spec()), encoding="utf-8")
    with contextlib.redirect_stdout(buf):
        assert WM.main(args[:2] + [str(lab)] + args[3:] + ["--volume-sha256", vs, "--labels-sha256", ls]) == 2
        assert WM.main(args + ["--volume-sha256", "1" * 64, "--labels-sha256", ls]) == 1  # the build's identity
    from a1_audit import ahba_builds as AB
    from a1_audit import ahba_extras as AX
    raises(lambda: AX.build_perdonor_hcpmmp1(vol, lab.read_bytes().decode("utf-8"), SCRATCH / "v3_out",
                                             volume_sha256=vs, label_list_sha256="2" * 64,
                                             get_expression_data=lambda **k: None), AB.BuildError)
    # the material stage hands the R15 sha256s on (no identity -> not computable, nothing run)
    r = WM.r38_build(roots, None, volume_sha256=None, label_list_sha256=ls)
    assert r["status"] == "not computable (atlas identity)" and r["exit"] is None
    m = STATE["man"]["objects"]
    assert m[L.HCP_VOL_KEY]["sha256"] == vs and m[L.HCP_LIST_KEY]["sha256"] == ls
    return {}


@check("V4 C3 / C8: production sources refuse the draft; a scratch-flag mismatch; the R38 record held to the R15 sha256s")
def _v4():
    import copy
    prod = W4S.WP4Sources(L.Roots.production(), W3.Roots.production())
    try:
        with draft_guard():
            prod._m4()
        raise AssertionError("production sources read a manifest under the draft")
    except R.SourceUnavailable as e:
        assert "draft" in str(e)
    src = W4S.WP4Sources(STATE["roots"], W3.Roots.production())
    m = src._m4()
    bad = copy.deepcopy(m)
    bad["scratch"] = False
    flip = W4S.WP4Sources(STATE["roots"], W3.Roots.production())
    data = (json.dumps({k: v for k, v in bad.items() if k != "_sha256"})).encode("utf-8")
    flip.read_bytes = lambda p, _d=data, _o=flip.read_bytes: _d if Path(p) == Path(STATE["roots"].latest_manifest()) \
        else _o(p)
    try:
        flip._m4()
        raise AssertionError("a scratch manifest read by non-matching roots")
    except R.SourceUnavailable:
        pass
    # C8: the R38 record's volume sha256 differs from the R15 download -> the build is refused at use
    rows = {r.row: r for r in R.register_for_diagnostics(R.REPO)}
    plan = R.classify(rows[523], frozenset({"G2"}))
    t = W4S.WP4Sources(STATE["roots"], W3.Roots.production())
    t._m4()
    t._c["m4"] = copy.deepcopy(t._c["m4"])
    t._c["m4"]["objects"][L.HCP_VOL_KEY]["sha256"] = "f" * 64
    try:
        t.pretzsch_recipe_inputs(plan)
        raise AssertionError("an R38 build not made from the R15 download was used")
    except R.SourceUnavailable:
        pass
    src.pretzsch_recipe_inputs(plan)                          # the honest manifest passes
    return {}


@check("V5 B5: S of the DEG cells from the script's lists; the TSV definition as the check; a planted mismatch refused")
def _v5():
    py = {"members": [f"G{k}" for k in range(36)], "m": 36, "n_pool": 3599}
    ok = RD.deg_check([f"G{k}" for k in range(36)], py, "ASD", 1)
    assert ok["passed"] and ok["cross_check"]["equal"]
    swapped = RD.deg_check([f"G{k}" for k in range(35)] + ["H1"], py, "ASD", 1)
    assert swapped["passed"] and not swapped["cross_check"]["equal"]     # the script's S governs; recorded beside
    assert not RD.deg_check([f"G{k}" for k in range(35)], py, "ASD", 1)["passed"]          # m differs
    assert not RD.deg_check([f"G{k}" for k in range(36)], dict(py, n_pool=3598), "ASD", 1)["passed"]
    assert not RD.deg_check([f"G{k}" for k in range(36)], None, "ASD", 1)["passed"]
    assert RD.deg_output_key("results/ASD/ASD_DEG_top_genes_thr_5.tsv", b"gene_name\tlogFC\nA\t1\n") == \
        (("ASD", 5), "gene_name")
    assert RD.deg_output_key("results/ASD/ASD_top_genes_thr_5.tsv", b"gene_name\tzscore\nA\t1\n") is None
    assert RD.deg_output_key("results/x/ASD_MDD_thr_5.tsv", b"gene_name\tlogFC\nA\t1\n") is None
    # the stage: a DEG list whose size is planted wrong -> its cell gets no set and STATUS_DEG_CHECK
    roots, man = STATE["roots"], copy_man(STATE["man"])
    e = man["objects"]["r17_deg_ASD_1"]
    o = json.loads((Path(roots.artifacts) / e["object_path"]).read_bytes())
    o["objects"]["raw"]["rows"] = o["objects"]["raw"]["rows"][:-1]
    alt = SCRATCH / "v5_obj.json"
    alt.write_text(json.dumps(o), encoding="utf-8")
    e["object_path"] = os.path.relpath(alt, roots.artifacts).replace("\\", "/")
    raws, srcs = WM.deg_raws(roots, man)
    assert "GIA-C19" not in raws and man["deg_checks"]["GIA-C19"]["status"] == L.STATUS_DEG_CHECK
    assert "GIA-C20" not in raws and "GIA-C21" in raws and srcs["GIA-C21"]["object"] == "r17_deg_ASD_5"
    return {"n_deg_sets": len(raws)}


def copy_man(m):
    import copy
    return copy.deepcopy(m)


@check("V6 C2: the dominance port equals netneurotools 0.3.0 (pinned once in a throwaway container)")
def _v6():
    from a1_audit import wp4_nnt_check as NC
    pin = json.loads((ROOT / NC.PIN_REL).read_bytes())
    assert pin["result"] == "PASS" and pin["container_versions"]["netneurotools"] == "0.3.0"
    data = NC.synthetic()
    assert hashlib.sha256(json.dumps(data).encode("utf-8")).hexdigest() == pin["data_sha256"]
    assert max(pin["max_abs_difference"].values()) <= NC.TOL and pin["n_comparisons"] == 6
    return {"max_abs_difference": max(pin["max_abs_difference"].values())}


# ================================================================================================================
# Part W - the phase-2 round (2026-10-16): the freeze pin, C9, C10, the Q3 hook, the phase-2 launcher
# ================================================================================================================
@check("W1 s17_compare (C9): row_provenance's seeds and input hashes compared, its timings not")
def _w1():
    from a1_audit import s17_compare as SC17
    def doc(seed=1, inp="a", t=1.0):
        d = _row_doc(10, seconds=t)
        d["row_provenance"] = {"row": 10, "seeds": {"per_map": [{"seed_int": seed}]}, "input_hashes": {"map[0]": inp},
                               "started": f"s{t}", "finished": f"f{t}", "host": f"h{t}"}
        return d
    base = {10: doc()}
    out = {}
    for name, new, want in (("timing", doc(t=2.0), 0), ("seed", doc(seed=2), 1), ("input", doc(inp="b"), 1)):
        d = SCRATCH / "w1" / name
        if d.exists():
            shutil.rmtree(d)
        _write_rows(d / "old", base)
        _write_rows(d / "new", {10: new})
        r = SC17.compare_dirs(d / "old", d / "new", None)
        assert r["exit"] == want, (name, r["exit"], r["rows"][0].get("differing_fields"))
        out[name] = r["rows"][0].get("flag")
    assert out["seed"] == out["input"] == "DIFFERS"
    return out


@check("W2 Roots.from_spec (C10): a scratch spec whose data root lies under E:/data/asdg is refused")
def _w2():
    spec = STATE["roots"].to_spec()
    L.Roots.from_spec(spec)                                       # the stand-in layout passes
    raises(lambda: L.Roots.from_spec(dict(spec, data="E:/data/asdg/scratch_x")), ValueError)
    raises(lambda: L.Roots.from_spec(dict(spec, data="e:\\data\\asdg")), ValueError)
    L.Roots.from_spec(dict(spec, scratch=False, data="E:/data/asdg"))   # production specs are not scratch
    return {}


@check("W3 amend_4 v3 Q3: a format-only adaptation locates the lists, is recorded as a deviation; the content check "
       "still gates")
def _w3():
    ad = {"name_regex": r"deg_(?P<dx>ASD|MDD)_top(?P<thr>1|5|10)\.csv", "symbol_header": "symbol",
          "weight_header": "lfc", "delimiter": ",", "why": "the script writes CSV lists named deg_<DX>_top<t>.csv"}
    assert RD.deg_output_key("out/deg_ASD_top1.csv", b"symbol,lfc\nA,1\n") is None      # the frozen rule misses it
    k = RD.deg_output_key_adapted("out/deg_ASD_top1.csv", b"symbol,lfc\nA,1\n", ad)
    assert k == (("ASD", 1), {"symbol": "symbol", "weight": "lfc", "delimiter": ","}), k
    assert RD.deg_list_rows(b"symbol,lfc\nA,1.5\n", "symbol", "lfc", ",")[0]["weight"] == 1.5
    roots = STATE["roots"]
    door = WM.Door(roots)
    ctl = Path(roots.control) / L.GATE
    ctl.mkdir(parents=True, exist_ok=True)
    f = ctl / L.DEG_ADAPTATION_NAME
    try:
        assert WM.deg_adaptation(roots, door) == (None, None)
        f.write_text(json.dumps(dict(ad, extra=1)), encoding="utf-8")
        raises(lambda: WM.deg_adaptation(roots, door), ValueError)                       # a malformed file stops
        f.write_text(json.dumps(dict(ad, name_regex="deg_(ASD)_top(1).csv")), encoding="utf-8")
        raises(lambda: WM.deg_adaptation(roots, door), ValueError)
        f.write_text(json.dumps(ad), encoding="utf-8")
        got, sha = WM.deg_adaptation(roots, door)
        assert got == ad and sha == hashlib.sha256(f.read_bytes()).hexdigest()
    finally:
        if f.exists():
            f.unlink()                                             # the test's own planted file
    # the stage path: a run's created CSV lists located by the adaptation; the content check unchanged
    work = SCRATCH / "w3_run"
    if work.exists():
        shutil.rmtree(work)
    (work / "out").mkdir(parents=True)
    rows = WM.object_of(roots, STATE["man"]["objects"]["r17_deg_ASD_5"], "raw")["rows"]
    body = "symbol,lfc\n" + "".join(f"{r['symbol']},{r['weight']!r}\n" for r in rows)
    (work / "out" / "deg_ASD_top5.csv").write_text(body, encoding="utf-8", newline="\n")
    (work / "out" / "deg_ASD_top1.csv").write_text("symbol,lfc\nGENE1,0.5\n", encoding="utf-8", newline="\n")
    rec = {"_workdir": str(work), "_created_paths": ["out/deg_ASD_top5.csv", "out/deg_ASD_top1.csv"],
           "workdir_index": 99}
    objs = WM.r17_outputs(roots, rec, door, io.StringIO(), adaptation=ad)
    assert objs["r17_deg_ASD_5"]["status"] == FE.STATUS_EXTRACTED and objs["r17_deg_ASD_5"]["object_key"] == \
        "r17_deg_ASD_5_r99" and objs["r17_deg_ASD_1"]["status"] == FE.STATUS_EXTRACTED, objs
    man = copy_man(STATE["man"])
    man["objects"].update(objs)
    raws, _ = WM.deg_raws(roots, man)
    assert "GIA-C21" in raws and len(raws["GIA-C21"]) == 180                  # m 180 = round(3,599 x 5 %)
    assert "GIA-C19" not in raws and man["deg_checks"]["GIA-C19"]["status"] == L.STATUS_DEG_CHECK, (
        {k: v.get("status") for k, v in objs.items()}, man["deg_checks"]["GIA-C19"])   # m 1 != 36
    return {"n_located": sum(1 for k in objs if k.startswith("r17_deg_"))}


@check("W4 wp4_launch: preconditions (the §17 plants at 36a4fe6, the diff guard, the freeze); the dry plan")
def _w4():
    import contextlib
    from a1_audit import wp4_launch as WL
    good = {"commit": "36a4fe6" + "0" * 33, "tag": "s17_wp4",
            "steps": [{"step": s, "exit": 0} for s in ("suite", "p1", "plants")]}
    assert WL.plants_passed(good)[0]
    assert not WL.plants_passed(dict(good, steps=good["steps"][:2]))[0]                  # plants not passed
    assert not WL.plants_passed(dict(good, commit="ea7f936" + "0" * 33))[0]
    assert not WL.plants_passed({"commit": good["commit"], "tag": "s17_wp4",
                                 "steps": [{"step": "suite", "exit": 1}]})[0]
    # the §17 comparison flagged rows (exit 1 -> launcher 40): accepted only with a classification that explains it
    flagged = dict(good, steps=good["steps"] + [{"step": "compare", "exit": 1}])
    cls = {"reading": WL.CLASSIFY_READING, "substantive_rows": [], "by_class": {"provenance": 349, "label": 86},
           "n_flagged": 435, "compare_sha256": "c" * 64}
    assert not WL.plants_passed(flagged)[0]                                         # no classification
    assert WL.plants_passed(flagged, cls, "c" * 64)[0]
    assert not WL.plants_passed(flagged, dict(cls, substantive_rows=[10]), "c" * 64)[0]
    assert not WL.plants_passed(flagged, dict(cls, reading="x"), "c" * 64)[0]
    assert not WL.plants_passed(flagged, dict(cls, by_class={"provenance": 349, "label": 85}), "c" * 64)[0]
    assert not WL.plants_passed(flagged, dict(cls, by_class={"provenance": 349, "statistic": 86}), "c" * 64)[0]
    assert not WL.plants_passed(flagged, cls, "d" * 64)[0]                          # another comparison file
    # the real §17 record (closed at 36a4fe6, commit 0697341) is accepted
    import hashlib as _h
    real_s = json.loads((ROOT / WL.PRERUN_SUMMARY).read_bytes()) if (ROOT / WL.PRERUN_SUMMARY).is_file() else None
    real_c = json.loads((ROOT / WL.CLASSIFY).read_bytes()) if (ROOT / WL.CLASSIFY).is_file() else None
    cmpf = ROOT / "arcs/audit/results/a1_run/s17_wp4_compare.json"
    real = WL.plants_passed(real_s, real_c, _h.sha256(cmpf.read_bytes().replace(b"\r\n", b"\n")).hexdigest()) \
        if real_s and real_c and cmpf.is_file() else (None, "absent")
    # paths outside arcs/ and src/ are not read by A1; under them the allow-list decides
    assert not any(f.startswith(WL.A1_READ_PREFIXES) for f in ("explore/discovery/x.py", "literature/n.md", ".gitignore"))
    assert all(f.startswith(WL.A1_READ_PREFIXES) for f in ("src/asdg/x.py", "arcs/replication/src/h_verdicts.py"))
    ok_f = ["arcs/audit/src/a1_audit/wp4_launch.py", "arcs/audit/src/a1_audit/wp4_layout.py",
            "arcs/audit/src/a1_audit/s17_compare.py", "arcs/audit/src/a1_audit/tests/test_wp4_phase1.py",
            "arcs/audit/RUN_PLAN_amend_4.md", "arcs/audit/FROZEN.txt", "arcs/audit/src/a1_audit/rbuild/r17.py"]
    bad_f = ["arcs/audit/src/a1_audit/run.py", "arcs/audit/src/a1_audit/pace.py", "arcs/audit/src/a1_audit/repro.py",
             "arcs/audit/src/a1_audit/plants/driver.py", "arcs/audit/src/a1_audit/real_sources.py",
             "arcs/audit/src/a1_audit/launch.py", "arcs/audit/src/a1_audit/s17_launch.py", "arcs/audit/claims_register.tsv"]
    assert all(any(rx.match(f) for rx in WL.DIFF_ALLOWED) for f in ok_f)
    assert not any(any(rx.match(f) for rx in WL.DIFF_ALLOWED) for f in bad_f)
    ok, why, _ = WL.diff_guard("6fe112e", "36a4fe6")           # planted: the WP4 phase-1 range touches run.py
    assert not ok and "outside DIFF_ALLOWED" in why
    live = WL.diff_guard("36a4fe6", "HEAD")
    # the dry plan with a planted passing §17 summary (nothing written, nothing launched)
    ps = SCRATCH / "w4_prerun.json"
    ps.write_text(json.dumps(good), encoding="utf-8")
    keep = WL.PRERUN_SUMMARY
    WL.PRERUN_SUMMARY = str(ps)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = WL.main(["--commit", "HEAD", "--dry"])
    finally:
        WL.PRERUN_SUMMARY = keep
    text = buf.getvalue()
    doc = json.loads(text[:text.rindex("}") + 1])
    if live[0]:
        assert rc == 0 and [s["step"] for s in doc["steps"]] == [
            "material", "verdict", "descriptor", "sensitivity", "verdict_amend5", "descriptor_amend5",
            "sensitivity_amend5", "report"], (rc, doc.get("reason"))
        pe_steps = [s for s in doc["steps"] if s["step"].endswith("_amend5")]
        assert all(s.get("env") == {L.VERSION_ENV: L.VERSION_AMEND5} and "--rerun-tag" in s["argv"] for s in pe_steps)
        assert all(s["exit"] is None for s in doc["steps"])
    else:
        assert rc == 2 and "DIFF_ALLOWED" in doc.get("reason", "")
    if real[0] is not None:
        assert real[0], real[1]
    return {"36a4fe6..HEAD allowed": live[0], "n_files": len(live[2]), "real s17 record": real[1][:120]}


# ================================================================================================================
# Part X - the 2026-10-17 incident (the first production material run): both causes reproduced on stand-ins
# ================================================================================================================
@check("X1 a date-typed DEG workbook cell: the old transform's object cannot be saved (TypeError at save); the "
       "transform now keeps JSON-safe primitives and counts the excluded rows by type name")
def _x1():
    import datetime as dtm

    class V:
        declared = {"alt": 0, "dx": 1, "p": 2, "lfc": 3}

        def __init__(self, cols):
            self.cols = cols

        def column(self, k):
            return self.cols[k]
    cols = [["GENE1", dtm.datetime(2026, 3, 1), "GENE3", None, "GENE5"], ["ASD", "ASD", "MDD", "ASD", "SCZ"],
            [0.01, 0.02, 0.03, 0.04, 0.05], [1.0, -1.0, 0.5, 0.2, 0.1]]
    old = {"symbol": cols[0][:4], "dx": cols[1][:4], "p": cols[2][:4], "logFC": cols[3][:4]}
    al = PW.AllowList()
    al.add_exact(SCRATCH / "x1_old.json", SCRATCH / "x1_new.json")
    al.add_exact("x1_old.json", "x1_new.json")
    em = PW.Emitter(al, stream=io.StringIO())
    raises(lambda: FE.save_object(em, SCRATCH / "x1_old.json", old), TypeError)     # the incident's TypeError
    new = WM.deg_transform({"deg": V(cols)})["deg"]
    assert new["symbol"] == ["GENE1", "GENE3"] and new["n_rows_kept"] == 2
    assert new["n_rows_excluded_by_type"] == {"symbol_NoneType": 1, "symbol_datetime": 1}
    FE.save_object(em, SCRATCH / "x1_new.json", {"deg": new})                       # saves now
    return {}


@check("X2 R17 refusal texts: only rbuild.r17.REFUSALS reach a record (each passes the print rule); any other text "
       "is replaced by a fixed note; config.yaml's commented key line parses")
def _x2():
    from a1_audit.rbuild import r17 as R17
    allow = WM._allow(STATE["roots"])
    for w in R17.REFUSALS + (R17.REFUSAL_UNLISTED,):
        assert allow.check("   " + json.dumps({"why": w})[1:-1], "identity"), w
    assert not allow.check("   " + json.dumps({"why": "planted ZQXJ text"})[1:-1], "identity")
    b, roots = STATE["b"], STATE["roots"]

    class Refuse:
        def __init__(self, text):
            self.text = text

        def params(self, facts):
            raise R17.R17Refused(self.text)
    man = copy_man(STATE["man"])
    with network(Net(b["net"])):
        r1 = WM.run_r17(roots, man, WM.Door(roots), PW.Emitter(allow, stream=io.StringIO()), io.StringIO(),
                        docker=Refuse("no Bioconductor release for the R minor"))
        r2 = WM.run_r17(roots, man, WM.Door(roots), PW.Emitter(allow, stream=io.StringIO()), io.StringIO(),
                        docker=Refuse("planted ZQXJ text"))
    assert r1["r17"]["why"] == "no Bioconductor release for the R minor"
    assert r2["r17"]["why"] == R17.REFUSAL_UNLISTED
    cfg = (b"release_dates: # a trailing comment, as Bioconductor's config.yaml has it\n  \"3.19\": \"5/1/2024\"\n"
           b"r_ver_for_bioc_ver:\n  \"3.19\": \"4.4\"\n")
    assert R17.bioc_for("4.4.1", "2024-09-01", cfg)["version"] == "3.19"
    return {}


@check("X3 a manifest the print rule refuses is not written: the stage stops, an incident note holds the failing "
       "field paths and their count only")
def _x3():
    b, roots = STATE["b"], STATE["roots"]
    allow = WM._allow(roots)
    assert WM.failing_fields(allow, {"objects": {"r17": {"why": "planted ZQXJ text", "status": "ran"}}}) == \
        [".objects.r17.why"]
    before = sorted(p.name for p in (Path(roots.records) / L.GATE).glob("wp4_material_manifest*.json"))
    hooks = dict(stage_hooks(b, {}), r17=lambda r, m, d, e, o: {"r17": {"status": "ran", "why": "planted ZQXJ text"}})
    with network(Net(b["net"])):
        raises(lambda: WM.run_material(roots, out=io.StringIO(), hooks=hooks), PW.PrintRuleViolation)
    after = sorted(p.name for p in (Path(roots.records) / L.GATE).glob("wp4_material_manifest*.json"))
    assert after == before                                     # nothing written
    notes = sorted((Path(roots.control) / L.GATE).glob("manifest_print_rule_incident_*.json"))
    assert notes
    note = json.loads(notes[-1].read_bytes())
    assert note["failing_field_paths"] == [".objects.r17.why"] and note["n_failing_fields"] == 1
    assert "ZQXJ" not in notes[-1].read_text(encoding="utf-8")
    return {}


@check("X4 resume: a downloaded carrier is held to its earlier record's sha256 at use (a changed byte refused); R38's "
       "build reused only while its record and outputs re-hash equal")
def _x4():
    b, roots = STATE["b"], STATE["roots"]
    from a1_audit.rbuild import r17 as R17
    key = L.R17_RVERSIONS_KEY
    car = Path(roots.data) / key / "carrier.json"
    keep = car.read_bytes()
    t = FE.Target(key=key, gate=L.GATE, url=R17.RVERSIONS_API, kind="file", ext=".json", identity_at_download=True,
                  head_before_get=False)
    try:
        with network(Net(b["net"])) as net:
            e1 = WM.run_one(roots, t, io.StringIO())
            car.write_bytes(keep + b" ")
            e2 = WM.run_one(roots, t, io.StringIO())
        assert e1["status"] == FE.STATUS_IDENTITY_ONLY and e1["identity_result"] == "identity match", e1
        assert e2["status"] != FE.STATUS_IDENTITY_ONLY and e2["identity_result"] != "identity match", e2
        assert not [u for m, u in net.calls if m in ("GET", "STREAM")]
    finally:
        car.write_bytes(keep)
    out_dir = Path(roots.hcp_build)
    vs = hashlib.sha256((Path(roots.data) / L.HCP_VOL_KEY / "carrier.nii.gz").read_bytes()).hexdigest()
    ls = hashlib.sha256((Path(roots.data) / L.HCP_LIST_KEY / "carrier.txt").read_bytes()).hexdigest()
    assert WM.r38_reuse(out_dir, vs, ls)["resumed"] is True
    assert WM.r38_reuse(out_dir, "0" * 64, ls) is None
    rec = json.loads((out_dir / "build_record.json").read_bytes())
    f = out_dir / rec["outputs"][0]["file"]
    kb = f.read_bytes()
    try:
        f.write_bytes(kb + b"\0")
        assert WM.r38_reuse(out_dir, vs, ls) is None
    finally:
        f.write_bytes(kb)
    return {}


@check("X5 config.yaml comments (2026-10-20): a commented key line, a commented entry line, a column-0 comment line "
       "and a '#' inside quotes all parse; a malformed entry line is refused by a REFUSALS text; every literal R17 "
       "refusal text in rbuild/r17.py is listed; the downloaded public config.yaml (when present) parses to its "
       "independently counted entries")
def _x5():
    import re as _re
    from a1_audit.rbuild import r17 as R17
    cfg = ("other: # c\n  \"9.9\": \"x\"\n"
           "r_ver_for_bioc_ver: # a comment\n  \"2.11\": \"2.15\" # a comment on an entry\n# a column-0 comment\n"
           "  '3.19': '4.4'\n\n  \"3.20\": \"4.4\"\n"
           "release_dates: # see http://example.invalid/x#y\n  \"3.19\": \"5/1/2024\"\n  \"3.20\": \"10/30/2024\" # c\n"
           "  \"3.21\": \"a#b\"\nnext_key:\n  \"3.22\": \"4.5\"\n")
    rmap = R17._yaml_map(cfg, "r_ver_for_bioc_ver")
    assert rmap == {"2.11": "2.15", "3.19": "4.4", "3.20": "4.4"}, rmap        # the old pattern dropped 2.11
    dates = R17._yaml_map(cfg, "release_dates")
    assert dates == {"3.19": "5/1/2024", "3.20": "10/30/2024", "3.21": "a#b"}, dates
    assert R17.bioc_for("4.4.1", "2024-12-01", cfg.encode())["version"] == "3.20"
    try:
        R17._yaml_map("release_dates:\n  - a list item\n", "release_dates")
        raise AssertionError("a malformed entry line was not refused")
    except R17.R17Refused as e:
        assert e.what in R17.REFUSALS
    src = (Path(R17.__file__)).read_text(encoding="utf-8")
    lits = _re.findall(r"R17Refused\(\"((?:[^\"\\]|\\.)*)\"\)", src) + \
        _re.findall(r"self\._ok\(\[[^\]]*\],\s*\"((?:[^\"\\]|\\.)*)\"", src)
    lits = [x.replace("\\\\", "\\") for x in lits]
    assert lits and not [x for x in lits if x not in R17.REFUSALS], [x for x in lits if x not in R17.REFUSALS]
    from a1_audit import wp4_launch as WL5         # the incident note passes the diff guard; another .md does not
    ok5 = lambda f: any(rx.match(f) for rx in WL5.DIFF_ALLOWED)     # noqa: E731
    assert ok5("arcs/audit/run_manifests/material/G2/incident_2026-10-17.md")
    assert not ok5("arcs/audit/run_manifests/material/G2/notes.md")
    assert not ok5("arcs/audit/run_manifests/material/G2/incident_2026-10-17.md.py")
    real = Path("E:/data/asdg") / L.R17_BIOC_KEY / "carrier.txt"
    live = None
    if real.is_file():
        text = real.read_bytes().decode("utf-8")
        lines = text.splitlines()
        live = {}
        for key in ("r_ver_for_bioc_ver", "release_dates"):
            i = next(k for k, ln in enumerate(lines) if ln.split("#")[0].strip() == key + ":")
            n = 0
            for ln in lines[i + 1:]:
                if ln and not ln[0].isspace() and not ln.startswith("#"):
                    break
                n += bool(_re.match(r"^\s+\"[0-9.]+\":", ln))
            got = R17._yaml_map(text, key)
            assert len(got) == n and n > 0, (key, len(got), n)
            live[key] = n
        assert all(R17._bioc_date(v) for v in R17._yaml_map(text, "release_dates").values())
    return {"n_literal_refusals": len(lits), "live config.yaml entries": live}


# the wp4_material functions whose dicts, keys and texts reach the G2 manifest (the others build saved objects,
# Target references, the R17 facts, the set manifest or the R13 record, each written under its own rule)
X6_MANIFEST_FUNCS = ("run_material", "entry", "prefix_target", "r16_annot", "r15_hcp", "r38_reuse", "r38_build",
                     "screen_exempt_target", "line130_cells", "run_amended",
                     "sadeghi_listing", "run_decoders", "run_r17", "run_info_of")
X6_TEXT_RETURNS = ("r17_facts", "deg_adaptation")      # their returned refusal texts become a manifest "why"
X6_NOT_MANIFEST = {("run_decoders", "file_url"), ("run_decoders", "content_length"),
                   ("run_decoders", "last_modified"),   # wp3_decoder's prefreeze argument (its own record)
                   ("run_r17", "abs_roots"), ("run_r17", "out_dirs")}   # docker.run's arguments (never recorded)


def x6_manifest_texts() -> tuple[list, list]:
    """(keys, (key, text) pairs) the material code can put in the manifest: the dict keys, keyword keys and string
    literals (f-strings rendered with a registered key) of X6_MANIFEST_FUNCS, the returned texts of X6_TEXT_RETURNS,
    every STATUS_* constant of the layouts / wrapper / identity / decoder, R17's REFUSALS, the wrapper's stages."""
    import ast
    from a1_audit import identity as IDm, wp3_decoder as WDm
    from a1_audit.rbuild import r17 as R17
    tree = ast.parse(Path(WM.__file__).read_text(encoding="utf-8"))
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert set(X6_MANIFEST_FUNCS + X6_TEXT_RETURNS) <= set(funcs), set(X6_MANIFEST_FUNCS) - set(funcs)

    def text(v):
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            return v.value
        if isinstance(v, ast.JoinedStr):
            return "".join(p.value if isinstance(p, ast.Constant) else L.SADEGHI_KEY for p in v.values)
        return None
    keys, pairs = set(), set()
    for fn in X6_MANIFEST_FUNCS:
        for n in ast.walk(funcs[fn]):
            items = []
            if isinstance(n, ast.Dict):
                items = [(k.value, v) for k, v in zip(n.keys, n.values) if isinstance(k, ast.Constant)
                         and isinstance(k.value, str)]
            elif isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", None)) in ("dict", "update"):
                items = [(kw.arg, kw.value) for kw in n.keywords if kw.arg]
            for k, v in items:
                if (fn, k) in X6_NOT_MANIFEST:
                    continue
                keys.add(k)
                t = text(v)
                if t is not None:
                    pairs.add((k, t))
    for fn in X6_TEXT_RETURNS:
        for n in ast.walk(funcs[fn]):
            if isinstance(n, ast.Return) and isinstance(n.value, ast.Tuple):
                for e in n.value.elts:
                    t = text(e)
                    if t is not None:
                        pairs.add(("why", t))
    for mod in (L, WM, FE, IDm, WDm):          # the modules whose statuses a manifest entry carries
        for name in dir(mod):
            if name.startswith("STATUS_") and isinstance(getattr(mod, name), str):
                pairs.add(("status", getattr(mod, name)))
    pairs.update(("why", w) for w in R17.REFUSALS + (R17.REFUSAL_UNLISTED,))
    pairs.update(("failed_stage", s) for s in FE.STAGES)
    pairs.update(("reason_class", c) for c in WM.REASON_CLASSES + ("other",))
    return sorted(keys), sorted(pairs)


@check("X6 pre-flight (2026-10-21, run 3's stop at .run.launch_passed): a synthetic manifest holding every key and "
       "fixed text the material code can emit passes the identity-channel allow-list; a planted key and text are "
       "refused and reported by path / count only; the run block is checked")
def _x6():
    allow = WM._allow(STATE["roots"])
    keys, pairs = x6_manifest_texts()
    run = WM.check_run_info(WM.run_info_of("9ec681e" * 5 + "abcde", {"failed": []}))
    statuses = sorted({t for k, t in pairs if k == "status"})
    man = {"schema": L.MANIFEST_SCHEMA, "gate": L.GATE, "run": run,
           "objects": {L.SADEGHI_KEY: {"fields": [{k: 0} for k in keys] + [{k: t} for k, t in pairs]},
                       "r17_in_0123456789abcdef": {"status": FE.STATUS_IDENTITY_ONLY,
                                                   "member_path": (SCRATCH / "x6_member.bin").as_posix()}},
           "counts": {**{s: 1 for s in statuses}, "none": 1}}
    probe = WM._allow(STATE["roots"])
    assert WM.failing_fields(probe, {"objects": {"r17_in_0123456789abcdef": {}}}) == \
        ["<1 non-vocabulary keys under .objects>"]                       # the key form needs manifest_exacts
    WM.manifest_exacts(allow, man)
    bad = WM.failing_fields(allow, man)
    assert bad == [], bad
    em = PW.Emitter(allow, stream=io.StringIO())
    p = SCRATCH / "x6_manifest.json"
    allow.add_exact(p, p.name)
    if p.exists():
        p.unlink()
    PW.stage(em, "record", em.write_json, p, man, "identity")         # the real write passes too, read back
    # planted: a data-like key and a non-vocabulary text are refused by the write and named by path / count only
    planted = json.loads(json.dumps(man))
    planted["objects"][L.SADEGHI_KEY]["ZQXJ1"] = {"status": "ran"}
    planted["run"]["status"] = "planted ZQXJ text"
    got = WM.failing_fields(allow, planted)
    assert got == [".run.status", f"<1 non-vocabulary keys under .objects.{L.SADEGHI_KEY}>"], got
    assert not any("ZQXJ" in g for g in got)
    p2 = SCRATCH / "x6_planted.json"
    allow.add_exact(p2, p2.name)
    raises(lambda: PW.stage(em, "record", em.write_json, p2, planted, "identity"), PW.PrintRuleViolation)
    assert not p2.exists()
    raises(lambda: WM.check_run_info({"commit": "abc1234", "note": "x"}), ValueError)
    raises(lambda: WM.check_run_info({"launch_passed": "yes"}), ValueError)
    return {"n_keys": len(keys), "n_texts": len(pairs)}


# ================================================================================================================
# Part X (amend_5, DRAFT, post-exposure, 2026-10-21): run 4's four diagnoses reproduced on stand-ins and fixed
# ================================================================================================================
@check("X7 R61' (amend_5 v2): the PRIMARY reading is R61 as frozen (the 6 '.'/'-' names refuse); the post-exposure "
       "version (amend5=True) matches them, only where the CSV name is R's make.names of the pinned one; the one-to-one "
       "match and the 180 count kept (a missing name, two pinned names one key, 179 names, a non-make.names pair: refused)")
def _x7():
    rng = np.random.default_rng(7)
    left = [f"L_P{i:03d}_ROI" for i in range(1, 175)] + [f"L_p{i}-46v_ROI" for i in range(6)]
    assert [RD.r_make_names(n) for n in left[-6:]] == [n.replace("-", ".") for n in left[-6:]]
    assert RD.r_make_names("L_V1_ROI") == "L_V1_ROI" and RD.r_make_names("1a-b") == "X1a.b"
    csv = SC.pretzsch_csv([RD.r_make_names(n) for n in left], rng)            # the derived CSV's make.names form
    raises(lambda: RD.pretzsch_csv(csv, left), RD.W4Refused, L.STATUS_PRE_LAYOUT)          # primary: R61 as frozen
    pc = RD.pretzsch_csv(csv, left, amend5=True)
    assert len(pc["CT"]) == len(pc["SA"]) == 180 and pc["counts"]["n_names_dot_dash"] == 6 and         pc["counts"]["n_pairs_make_names"] == 6, pc["counts"]
    same = RD.pretzsch_csv(SC.pretzsch_csv(left, np.random.default_rng(7)), left, amend5=True)
    assert same["counts"]["n_names_dot_dash"] == 0
    assert RD.pretzsch_csv(SC.pretzsch_csv(left, np.random.default_rng(7)), left)["counts"]["n_left_rows"] == 180
    raises(lambda: RD.pretzsch_csv(SC.pretzsch_csv([RD.r_make_names(n) for n in left[:179]] + ["L_Q_ROI"], rng),
                                   left, amend5=True), RD.W4Refused, L.STATUS_PRE_LAYOUT)
    clash = left[:179] + [left[179].replace("-", ".")]                       # 'a-b' and 'a.b' both pinned: one key
    clash[178] = left[179]
    raises(lambda: RD.pretzsch_csv(csv, clash, amend5=True), RD.W4Refused, L.STATUS_PRE_LAYOUT)
    raises(lambda: RD.pretzsch_csv(csv, left[:179], amend5=True), RD.W4Refused, L.STATUS_PRE_LAYOUT)
    rev = left[:174] + [f"L_p{i}.46v_ROI" for i in range(6)]                 # pinned '.', CSV '-': not make.names
    raises(lambda: RD.pretzsch_csv(SC.pretzsch_csv(left, np.random.default_rng(7)), rev, amend5=True), RD.W4Refused,
           L.STATUS_PRE_LAYOUT)
    return {}


@check("X8 R54' (amend_5 v2): the PRIMARY reading is R54 as frozen (the run-4 sheet's unmarked labels and 'Pallidus' "
       "refuse); the post-exposure version maps unmarked Subcortical labels to the left aseg ids (an inference) and "
       "'Pallidus' to pallidum; an unmarked Thickness label, a right marker and an unknown name still refuse")
def _x8():
    sub = ["Accumbens", "Amygdala", "Caudate", "Hippocampus", "Pallidus", "Putamen", "Thalamus"]
    raises(lambda: RD.giacomel_sheet_object(sub, [1.0] * 7, [2.0] * 7, DK, "subcortical"), RD.W4Refused,
           L.STATUS_GIA_LAYOUT)                                                 # primary: R54 as frozen
    marked = ["M" + x for x in sub]
    raises(lambda: RD.giacomel_sheet_object(marked, [1.0] * 7, [2.0] * 7, DK, "subcortical"), RD.W4Refused,
           L.STATUS_GIA_LAYOUT)                                                 # primary: no 'pallidus' alias
    o = RD.giacomel_sheet_object(sub, [1.0] * 7, [2.0] * 7, DK, "subcortical", amend5=True)
    assert o["counts"]["n_matched"] == 7 and o["order_matched"] is True, o["counts"]
    raises(lambda: RD.giacomel_sheet_object(sub[:4] + ["Pallidix"] + sub[5:], [1.0] * 7, [2.0] * 7, DK,
                                            "subcortical", amend5=True), RD.W4Refused, L.STATUS_GIA_LAYOUT)
    raises(lambda: RD.giacomel_sheet_object(["Raccumb"] + sub[1:], [1.0] * 7, [2.0] * 7, DK, "subcortical",
                                            amend5=True), RD.W4Refused, L.STATUS_GIA_LAYOUT)
    labs = [f"{n}_thickavg" for n in SC.dk_names(DK, "L", "cortex")]       # no M marker on Thickness
    raises(lambda: RD.giacomel_sheet_object(labs, [0.1] * 34, [0.1] * 34, DK, "thickness", amend5=True),
           RD.W4Refused, L.STATUS_GIA_LAYOUT)
    old = ["Maccumb", "Mamyg", "Mcaud", "Mhippo", "Mpal", "Mput", "Mthal"]   # the marked form reads in both
    assert RD.giacomel_sheet_object(old, [1.0] * 7, [2.0] * 7, DK, "subcortical")["counts"]["n_matched"] == 7
    assert set(RD.AMEND5_ALIASES) == {"pallidus"} and "pallidus" not in RD.G2_EXTRA_ALIASES
    return {}


X9_SCRIPT = """library(readr)
twas_path <- "/Users/someone/Dropbox/Proj/Repo/data/GWAS/mmc2(1).xlsx"
save_path <- "/Users/someone/Dropbox/Proj/Repo/results/"
a <- readr::read_csv("/Users/someone/Library/Cloud/Dropbox/Proj/Repo/data/AHBA/a.csv") # first root
b <- readr::read_tsv("/Users/someone/Library/Cloud/Dropbox/Proj/Repo/data/DK-files/dk.csv")
g <- readxl::read_xlsx(twas_path, sheet = 2)
readr::write_tsv(a, paste0(save_path, "MDD/MDD_literature_TPRS_thr_1.tsv"))
"""


@check("X9 R58': absolute read paths placed by the unique longest tree suffix at both roots; a variable-held read "
       "path (twas_path) counted; output folders pre-created; 'mmc2(1).xlsx' only by the Sadeghi name rule; nested "
       "roots refused; the R17 run with both roots mounted (Docker, when present)")
def _x9():
    from a1_audit.rbuild import r17 as R17
    req = RD.r_script_requirements(X9_SCRIPT)
    assert len(req["read_paths"]) == 3 and req["n_read_vars"] == 1, req
    tree = {"data/AHBA/a.csv", "data/DK-files/dk.csv", "code/s.R", "a.csv"}
    dup = lambda n: bool(L.SADEGHI_DUP_NAME.match(n))                       # noqa: E731
    pl = R17.placement(req["read_paths"], "code/s.R", tree | {"mmc2.xlsx"}, abs_strings=tuple(req["abs_strings"]),
                       name_ok=dup)
    assert sorted(pl["resolved"].values()) == ["data/AHBA/a.csv", "data/DK-files/dk.csv", "data/GWAS/mmc2(1).xlsx"]
    assert len(pl["abs_roots"]) == 2 and pl["n_unresolved"] == 0, pl["n_unresolved"]
    assert R17.out_dirs_rel(req["out_dirs"], pl["abs_roots"]) == ["results", "results/MDD"]
    pl2 = R17.placement(req["read_paths"], "code/s.R", tree, abs_strings=tuple(req["abs_strings"]))
    assert pl2["n_unresolved"] == 1                                           # without the name rule: unresolved
    assert dup("mmc2(1).xlsx") and dup("mmc2 (2).xlsx") and not dup("mmc3(1).xlsx") and not dup("mmc2.xlsx.zip")
    e = raises(lambda: R17.absolute_placement(["/x/Repo/data/a.csv", "/x/Repo/data/sub/data/a.csv"],
                                              {"data/a.csv", "sub/data/a.csv"}), R17.R17Refused)
    assert e.what in R17.REFUSALS
    raises(lambda: R17.run_script("x", SCRATCH / "x9_bad", "s.R", {}, out_dirs=("../up",)), R17.R17Refused)
    out = {"docker": "not run: Docker unavailable"}
    if docker_ok():
        work = SCRATCH / "x9work"
        for d in (work, SCRATCH / "x9work_logs"):
            if d.exists():
                shutil.rmtree(d)
        inp = SCRATCH / "x9_in.csv"
        inp.write_text("a,b\n1,2\n", encoding="utf-8")
        scr = SCRATCH / "x9.R"
        scr.write_text('a <- read.csv("/Users/someone/Library/Cloud/Dropbox/Proj/Repo/data/in.csv")\n'
                       'save_path <- "/Users/someone/Dropbox/Proj/Repo/results/"\n'
                       'write.table(a * 2, paste0(save_path, "MDD/out.tsv"), sep="\\t")\n', encoding="utf-8")
        roots = ("/Users/someone/Library/Cloud/Dropbox/Proj/Repo", "/Users/someone/Dropbox/Proj/Repo")
        rec = R17.run_script("a1-audit-r:wp2-r4.4.3", work, "code/s.R", {"code/s.R": scr, "data/in.csv": inp},
                             outputs_expected=("results/MDD/out.tsv",), timeout=900, abs_roots=roots,
                             out_dirs=("results/MDD",))
        assert rec["ok"] and rec["declared_outputs_found"] == 1, rec
        out["docker"] = "run (two roots mounted)"
    return out


@check("X10 E1: the publisher name of a declared pinned group-level copy is exempt from the path screen only with the "
       "declared bytes (a runner-built link handed to the wrapper); another name or other bytes are screened as "
       "before (the planted 'case' token quarantines)")
def _x10():
    roots = STATE["roots"]
    src = SCRATCH / "x10_pub"
    src.mkdir(exist_ok=True)
    name = "asd_meta-analysis_case-controls_X10.csv"
    assert PW.screen(name, FE.PG)["N"] >= 1                                   # run 4's false positive, reproduced
    f = src / name
    f.write_bytes(b"region,d\nbankssts,0.1\n")
    sha = hashlib.sha256(f.read_bytes()).hexdigest()
    keep = dict(L.SCREEN_EXEMPT)
    try:
        L.SCREEN_EXEMPT["x10_exempt"] = (name, sha)
        t = FE.Target(key="x10_exempt", gate=L.GATE, url="https://none.invalid/x10", kind="file", ext=".csv",
                      pinned_sha256=sha, pinned_bytes=f.stat().st_size, local_path=str(f))
        t2, ex = WM.screen_exempt_target(roots, t, WM.Door(roots))
        assert ex["applied"] and Path(t2.local_path).name == "carrier.csv" and PW.screen(
            Path(t2.local_path).relative_to(roots.data).as_posix(), FE.PG)["N"] == 0
        r = FE.run_target(t2, roots.fe_roots(), out=io.StringIO())
        rec = json.loads(Path(r["record_path"]).read_bytes())
        assert rec["identifier_bearing"] is False and not (rec.get("quarantine") or {}).get("quarantined"), rec
        assert f.is_file()                                                     # the pinned copy stays in place
        L.SCREEN_EXEMPT["x10_exempt"] = (name, "0" * 64)                       # other bytes: not exempt
        t3, ex3 = WM.screen_exempt_target(roots, dataclasses.replace(t, key="x10_exempt"), WM.Door(roots))
        assert not ex3["applied"] and t3.local_path == str(f)
        g = SCRATCH / "x10_other"
        g.mkdir(exist_ok=True)
        h = g / name
        h.write_bytes(f.read_bytes())
        t4 = FE.Target(key="x10_screened", gate=L.GATE, url="https://none.invalid/x10", kind="file", ext=".csv",
                       pinned_sha256=sha, pinned_bytes=h.stat().st_size, local_path=str(h))
        t4b, ex4 = WM.screen_exempt_target(roots, t4, WM.Door(roots))
        assert ex4 is None and t4b is t4                                         # not declared: screened
        r4 = FE.run_target(t4b, roots.fe_roots(), out=io.StringIO())
        rec4 = json.loads(Path(r4["record_path"]).read_bytes())
        assert rec4["identifier_bearing"] is True and (rec4.get("quarantine") or {}).get("quarantined")
    finally:
        L.SCREEN_EXEMPT.clear()
        L.SCREEN_EXEMPT.update(keep)
    assert set(L.SCREEN_EXEMPT) == {L.LIU_CT_KEY, L.LIU_SV_KEY}
    return {}


@check("X11 L130 (v2): the line-130 label on the 6 MDD-set DEG cells only (their second map is a line-130 file; "
       "descriptor-only, none in m); the eda33ab list cells carry none; the bite record by sha256 equality only")
def _x11():
    cells = WM.line130_cells()
    assert len(cells) == 6 and all(c.startswith("GIA-MDD-DEG-MDDset-") for c in cells), cells
    rb = WM.rows_by_cell_of(Path(STATE["roots"].repo))
    from a1_audit import loader as LD
    tsv = {r.cell_id: r for r in LD.parse_tsv_bytes(LD.lf((Path(STATE["roots"].repo) / LD.TSV_PATH).read_bytes()))[1]}
    assert all(not tsv[c].in_m for c in cells) and all(c in rb for c in cells)          # descriptor-only, none in m
    assert WM.row_labels("GIA-MDD-DEG-MDDset-05-ctx") == [L.LINE130_LABEL] and WM.row_labels("GIA-MDD-C5") == []
    assert WM.row_labels("GIA-MDD-DEG-ASDset-05-ctx") == [] and WM.row_labels("GIA-C01") == []
    src = W4S.WP4Sources(STATE["roots"], W3.Roots.production())
    assert src.row_labels({"cell_id": "GIA-MDD-DEG-MDDset-01-sub"}) == [L.LINE130_LABEL]
    assert W4S.row_labels("GIA-MDD-DEG-MDDset-01-sub", L.VERSION_AMEND5) == [L.LINE130_LABEL, L.AMEND5_VERSION_LABEL]
    rec = WM.line130_record({"r17_map_MDD_1": {"sha256": "a" * 64}, "r17_map_ASD_1": {"sha256": "a" * 64},
                             "gia_gedar_MDD_TPRS_thr_1": {"sha256": "b" * 64},
                             "gia_gedar_ASD_TPRS_thr_1": {"sha256": "c" * 64}})
    assert rec["r17_mdd_equals_asd"] == {"1": True, "5": None, "10": None}
    assert rec["eda33ab_mdd_equals_asd"]["1"] is False
    allow = WM._allow(STATE["roots"])
    assert WM.failing_fields(allow, {"labels": {"line130": {"label": L.LINE130_LABEL, "cells": cells}}}) == []
    return {"n_cells": len(cells)}


@check("X12 amend_5's DRAFT guard: production refuses (DRAFT_GUARD5) while its pin is unset, before anything is "
       "opened; a planted pin fails the freeze check; the launcher's diff guard admits the draft file")
def _x12():
    if L.AMEND5_FROZEN_SHA256 is None:
        assert L.production_allowed() == (False, L.DRAFT_GUARD5)
        raises(lambda: WM.run_material(L.Roots.production()), WM.PreflightRefused)
    assert not L.frozen_check(rel=L.AMEND5_REL, pin="0" * 64)["ok"]
    from a1_audit import wp4_launch as WL
    assert any(rx.match("arcs/audit/RUN_PLAN_amend_5.md") for rx in WL.DIFF_ALLOWED)
    return {}


@check("X13 security review (2026-10-21): third-party folder / placement names that could escape the copy refuse by a "
       "REFUSALS text - a backslash, a drive ':', a NUL, a leading '/', '..', '.' or empty components; a link or "
       "junction inside the copy that leads outside refuses (resolve + is_relative_to); roots likewise")
def _x13():
    from a1_audit.rbuild import r17 as R17
    work = SCRATCH / "x13work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir()
    bad = ["results\\..\\..\\x", "C:/Windows/x", "results/C:x", "res\x00ults", "/abs", "results/../../x", "./x",
           "results//x", "..", ""]
    for d in bad:
        e = raises(lambda d=d: R17.contained(work, d, "an output folder lies outside the repository copy"),
                   R17.R17Refused)
        assert e.what in R17.REFUSALS
        raises(lambda d=d: R17.run_script("x", SCRATCH / "x13run", "s.R", {}, out_dirs=(d,)), R17.R17Refused)
        if (SCRATCH / "x13run").exists():
            shutil.rmtree(SCRATCH / "x13run")
        raises(lambda d=d: R17.run_script("x", SCRATCH / "x13run", "s.R", {d: SCRATCH / "x13_none"}), R17.R17Refused)
        if (SCRATCH / "x13run").exists():
            shutil.rmtree(SCRATCH / "x13run")
    roots = ["/Users/a/Repo"]
    for d in ("/Users/a/Repo/res\\ults", "/Users/a/Repo/C:x", "/Users/a/Repo/a/../../b"):
        raises(lambda d=d: R17.out_dirs_rel([d], roots), R17.R17Refused)
    assert R17.out_dirs_rel(["/Users/a/Repo/results/MDD"], roots) == ["results/MDD"]
    for r in ("/Users/a\\Repo", "/Users/C:/Repo", "/Users/a/../Repo", "/", "/work", "/work/x", "relative/Repo",
              "/Users/a//Repo", "/Users/a/Re\x00po"):
        raises(lambda r=r: R17.check_abs_root(r), R17.R17Refused)
    raises(lambda: R17.run_script("x", SCRATCH / "x13run", "s.R", {}, abs_roots=("/Users/a/../b",)), R17.R17Refused)
    if (SCRATCH / "x13run").exists():
        shutil.rmtree(SCRATCH / "x13run")
    # placements: an anchored remainder or a suffix with an escape refuses
    raises(lambda: R17.absolute_placement(["/x/Repo/data/a.csv", "/x/Repo/../etc/p.csv"], {"data/a.csv"}),
           R17.R17Refused)
    assert R17.contained(work, "results/MDD", "an output folder lies outside the repository copy").is_relative_to(
        work.resolve())
    # a link / junction inside the copy that leads outside: resolve() follows it, so the folder refuses
    outside = SCRATCH / "x13_outside"
    outside.mkdir(exist_ok=True)
    link = work / "lnk"
    made = None
    try:
        os.symlink(outside, link, target_is_directory=True)
        made = "symlink"
    except OSError:
        r = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True)
        made = "junction" if r.returncode == 0 else None
    if made:
        raises(lambda: R17.contained(work, "lnk/sub", "an output folder lies outside the repository copy"),
               R17.R17Refused)
        assert not (outside / "sub").exists()
        os.rmdir(link) if made == "junction" else link.unlink()
    return {"link escape": made or "not feasible (no symlink / junction on this box)"}


@check("X14 amend_5 resume: an R54'-amended Giacomel extraction saves under <key>_a5 beside an earlier object of other "
       "bytes (never overwritten), uses the carrier already on disk (no GET), and is read at use through object_key")
def _x14():
    b, roots = STATE["b"], STATE["roots"]
    door = WM.Door(roots)
    dk = WM.dk_of(door)
    ids = L.identity_records(roots, lambda p: Path(p).read_bytes())
    r = ids[L.GIA_GOV_KEY]
    url = L.RAW_URL.format(repo=L.GIA_REPO, commit=L.GIA_93DE089, path=L.GIA_XLSX_PATH)
    t = WM.giacomel_target(L.GIA_GOV_KEY, url, tuple(r["refs"]), local_path=None,
                           dk_names=tuple(str(x) for x in dk["label"]))
    car = Path(roots.data) / L.GIA_GOV_KEY / "carrier.xlsx"
    k5dir = Path(roots.data) / (L.GIA_GOV_KEY + L.AMEND5_OBJECT_SUFFIX)
    src = k5dir / "carrier.xlsx"
    if not car.is_file() and src.is_file():                   # S1's first run downloaded under <key>_a5: stage it
        car.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, car)
    old = Path(roots.artifacts) / L.GATE / L.GIA_GOV_KEY / f"{L.GIA_GOV_KEY}_extract.json"
    old.parent.mkdir(parents=True, exist_ok=True)
    if not old.exists():
        old.write_bytes(b'{"planted": "an earlier object of other bytes"}\n')
    keep = old.read_bytes()
    with network(Net(b["net"])) as net:
        e = WM.run_amended(roots, t, io.StringIO(), transform=WM.giacomel_transform(door))
    assert e["status"] == FE.STATUS_EXTRACTED and e["object_key"] == L.GIA_GOV_KEY + L.AMEND5_OBJECT_SUFFIX, e
    assert not [u for m, u in net.calls if m in ("GET", "STREAM")]
    assert old.read_bytes() == keep                            # the earlier object untouched
    assert WM.object_of(roots, e, "subcortical") is not None
    return {}


@check("X15 amend_5 v2 two versions on the stand-ins: the primary objects keep the frozen readings; the manifest's "
       "post_exposure block holds the amended objects (<key>_a5, object_key), its own sets (G2_a5) and DEG checks; the "
       "G2 sources read the block only under version amend5; Roots.production honours A1_G2_VERSION")
def _x15():
    roots, man = STATE["roots"], STATE["man"]
    pe = man.get("post_exposure") or {}
    assert pe.get("label") == L.AMEND5_VERSION_LABEL and list(pe.get("readings") or []) == list(L.AMEND5_PE_READINGS)
    for k in (L.GIA_GOV_KEY, L.GIA_CMP_KEY, L.PRE_KEY):
        e = pe["objects"].get(k) or {}
        assert e.get("object_key") == k + L.AMEND5_OBJECT_SUFFIX, (k, e.get("status"))
        assert "object_key" not in (man["objects"].get(k) or {}), k            # the primary entry is the frozen one
    assert "r17" in pe["objects"] and isinstance(pe.get("deg_checks"), dict)
    assert (pe.get("sets") or {}).get("manifest_name"), pe.get("sets")
    r5 = dataclasses.replace(roots, version=L.VERSION_AMEND5)
    assert r5.set_dir().name == "G2_a5" and roots.set_dir().name == "G2" and (r5.set_dir() / pe["sets"]["manifest_name"]).is_file()
    s5 = W4S.WP4Sources(r5, W3.Roots.production())
    s1 = W4S.WP4Sources(roots, W3.Roots.production())
    assert s5._m4()["objects"][L.GIA_GOV_KEY]["object_key"].endswith(L.AMEND5_OBJECT_SUFFIX)
    assert "object_key" not in s1._m4()["objects"][L.GIA_GOV_KEY] and s1._m4().get("version") is None
    assert s5._m4()["sets"] == pe["sets"] and s1._m4()["sets"] == man["sets"]
    assert W4L_spec_roundtrip(r5)
    keep = os.environ.get(L.VERSION_ENV)
    try:
        os.environ[L.VERSION_ENV] = L.VERSION_AMEND5
        assert L.Roots.production().version == L.VERSION_AMEND5
        os.environ[L.VERSION_ENV] = "other"
        raises(lambda: L.Roots.production(), ValueError)
    finally:
        os.environ.pop(L.VERSION_ENV, None)
        if keep is not None:
            os.environ[L.VERSION_ENV] = keep
    assert L.Roots.production().version == L.VERSION_PRIMARY
    sub = [c for c in WS.GATED_CELLS if WS.GATED_CELLS[c][0] == "deg"]
    assert len(sub) == 18 and all(W4S.amend5_readings(c, "") == [L.AMEND5_PE_READINGS[2]] for c in sub)
    assert W4S.amend5_readings("X", "sheet Subcortical, column MDD (7 structures)") == [L.AMEND5_PE_READINGS[1]]
    assert W4S.amend5_readings("X", "y_CT: Pretzsch") == [L.AMEND5_PE_READINGS[0]]
    assert W4S.amend5_readings("X", "sheet Thickness, column ASD") == []
    return {"n_pe_objects": len(pe["objects"])}


@check("X16 in_m (2026-10-21): verdict_counted_in_m 'yes' -> True, 'no' -> False, anything else refused (bool('no') "
       "was True); the real TSV's G2 cells parse to its own yes count; a set file whose bytes change is written "
       "beside the earlier one as <set_id>.<n>.json (never overwritten), an identical one adopted; amend_5 frozen")
def _x16():
    assert WM.parse_in_m("yes", "c") is True and WM.parse_in_m("no", "c") is False
    for bad in ("No", "", None, "upper bound only", True):
        raises(lambda b=bad: WM.parse_in_m(b, "c"), ValueError)
    from a1_audit import loader as LD
    rows = LD.parse_tsv_bytes(LD.lf((Path(STATE["roots"].repo) / LD.TSV_PATH).read_bytes()))[1]
    g2 = [r for r in rows if r.gate == "G2"]
    rb = WM.rows_by_cell_of(Path(STATE["roots"].repo))
    assert sum(v["in_m"] for v in rb.values()) == sum(r.m_membership == "yes" for r in g2) < len(g2)
    no_row = next(r for r in g2 if r.m_membership == "no")
    assert rb[no_row.cell_id]["in_m"] is False and rb[no_row.cell_id]["in_m"] == no_row.in_m
    rs = WS.restate({no_row.cell_id: {"universe": {}, "status": "ok"}}, rb)
    assert rs["cells"][no_row.cell_id]["in_m"] is False and rs["n_in_m_not_testable_lt5"] == 0
    d = SCRATCH / "x16_sets"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir()
    a, b = {"set": 1}, {"set": 2}
    n1 = WS.versioned_name(d, "gated_G2_X", a)
    WS.write_set(d / n1, a)
    assert n1 == "gated_G2_X.json" and WS.versioned_name(d, "gated_G2_X", a) == n1        # identical: adopted
    n2 = WS.versioned_name(d, "gated_G2_X", b)
    WS.write_set(d / n2, b)
    assert n2 == "gated_G2_X.2.json" and json.loads((d / n1).read_bytes()) == a            # the earlier one kept
    assert L.AMEND5_FROZEN_SHA256 == "554f4e09a0f9e72141235d53f810ba300200d1c210e14692e50e372355ab1257"
    fc = L.frozen_check(rel=L.AMEND5_REL)
    assert fc["ok"], fc["checks"]
    return {"n_g2_in_m": sum(v["in_m"] for v in rb.values()), "n_g2": len(g2)}


def W4L_spec_roundtrip(r) -> bool:
    return L.Roots.from_spec(r.to_spec()) == r


@check("X17 run 5 (2026-10-21): a layout status stands only when the declared check ran (its condition recorded); "
       "another read-stage failure reads 'refused (stage failed)'; an object whose bytes changed is saved under "
       "<key>_v<n> (never overwritten, the carrier not fetched again); R17 and the DEG checks read 'refused (stage "
       "failed upstream)' when the script never ran; a GEDAR map whose names carry no side refuses by R56's check")
def _x17():
    roots = STATE["roots"]
    src = SCRATCH / "x17"
    if src.exists():
        shutil.rmtree(src)
    src.mkdir()
    f = src / "x17.csv"
    f.write_bytes(b"a,b\n1,2\n")
    sha = hashlib.sha256(f.read_bytes()).hexdigest()
    st = L.STATUS_GEDAR_LAYOUT

    def tgt(key):
        return FE.Target(key=key, gate=L.GATE, url="https://none.invalid/x17", kind="file", ext=".csv",
                         pinned_sha256=sha, pinned_bytes=f.stat().st_size, local_path=str(f), refusal_status=st)

    def bad_reader(path):
        raise KeyError("a parser defect")

    def refusing(path):
        raise RD.W4Refused(L.STATUS_LIST_LAYOUT, {"n_rows": 3, "n_unmatched": 2, "secret": 7})
    e1 = WM.run_one(roots, tgt("x17_bug"), io.StringIO(), reader=bad_reader)
    assert e1["status"] == FE.STATUS_FAILED and e1["layout_check"].startswith("not reached"), e1
    e2 = WM.run_one(roots, tgt("x17_check"), io.StringIO(), reader=refusing)
    assert e2["status"] == L.STATUS_LIST_LAYOUT and e2["layout_condition"]["counts"] == {"n_rows": 3, "n_unmatched": 2}
    # versioned objects
    ra = lambda path: {"o": {"v": 1}}                                         # noqa: E731
    rb = lambda path: {"o": {"v": 2}}                                         # noqa: E731
    a = WM.run_one(roots, tgt("x17_obj"), io.StringIO(), reader=ra)
    assert a["status"] == FE.STATUS_EXTRACTED and "object_key" not in a
    first = (Path(roots.artifacts) / a["object_path"]).read_bytes()
    b = WM.run_one(roots, tgt("x17_obj"), io.StringIO(), reader=rb)
    assert b["status"] == FE.STATUS_EXTRACTED and b["object_key"] == "x17_obj_v2", b
    assert (Path(roots.artifacts) / a["object_path"]).read_bytes() == first
    assert WM.object_of(roots, b, "o") == {"v": 2} and WM.object_of(roots, a, "o") == {"v": 1}
    c = WM.run_one(roots, tgt("x17_obj"), io.StringIO(), reader=ra)          # identical to the first: adopted
    assert c["status"] == FE.STATUS_EXTRACTED and "object_key" not in c
    # R17 upstream; the DEG checks follow R17's own status
    man = {"objects": {L.R17_SCRIPT_KEY: {"status": FE.STATUS_FAILED}}}
    assert WM.run_r17(roots, man, None, None, None, docker=object())["r17"]["status"] == L.STATUS_UPSTREAM
    from a1_audit.rbuild import r17 as R17

    class Refuse:
        def params(self, facts):
            raise R17.R17Refused("the base image could not be pulled")
    b0 = STATE["b"]
    m2 = copy_man(STATE["man"])
    with network(Net(b0["net"])):
        r = WM.run_r17(roots, m2, WM.Door(roots), PW.Emitter(WM._allow(roots), stream=io.StringIO()), io.StringIO(),
                       docker=Refuse())
    assert r["r17"]["status"] == L.STATUS_UPSTREAM and r["r17"]["why"], r         # never the paper's status
    m3 = {"objects": {"r17": {"status": L.STATUS_UPSTREAM}}}
    WM.deg_raws(roots, m3)
    assert m3["deg_checks"] and all(v["status"] == L.STATUS_UPSTREAM for v in m3["deg_checks"].values())
    m4 = {"objects": {"r17": {"status": L.STATUS_R17}}}
    WM.deg_raws(roots, m4)
    assert all(v["status"] == L.STATUS_R17 for v in m4["deg_checks"].values())
    # GEDAR: names with the side in a separate column -> R56's declared check refuses (names unmatched)
    rows = ["label\themisphere\tstructure\tweighted_avg"]
    for _, rr in DK.iterrows():
        rows.append(f"{rr['label']}\t{rr['hemisphere']}\t{rr['structure']}\t0.5")
    tsv = ("\n".join(rows) + "\n").encode("utf-8")
    e = raises(lambda: RD.gedar_map(tsv, DK), RD.W4Refused, L.STATUS_GEDAR_LAYOUT)
    assert e.counts["n_unmatched"] == e.counts["n_labels"] == len(DK) and e.counts["n_matched"] == 0
    g = src / "x17_gedar.tsv"
    g.write_bytes(tsv)
    tg = FE.Target(key="x17_gedar", gate=L.GATE, url="https://none.invalid/x17", kind="file", ext=".tsv",
                   pinned_sha256=hashlib.sha256(tsv).hexdigest(), pinned_bytes=len(tsv), local_path=str(g),
                   refusal_status=L.STATUS_GEDAR_LAYOUT)
    eg = WM.run_one(roots, tg, io.StringIO(), reader=WM.gedar_reader(WM.Door(roots)))
    assert eg["status"] == L.STATUS_GEDAR_LAYOUT and eg["layout_condition"]["counts"]["n_unmatched"] == len(DK), eg
    allow = WM._allow(roots)
    assert WM.failing_fields(allow, {"objects": {"x": {k: v for k, v in eg.items() if k in (
        "status", "layout_condition")}}}) == []
    return {}


@check("X18 run 6 (2026-10-21): the G2 sources built in a WORKTREE (run.py: out_repo = its own REPO) read the main "
       "tree's post-freeze records, sets and objects (a worktree holds none), so a final manifest is picked up; the "
       "launcher's per-pass sanity gate fails on 'material pending' rows after a final manifest and on 0 computed rows "
       "where the register's plan expects rows")
def _x18():
    from a1_audit import wp4_launch as WL
    main = L.main_repository(L.REPO)
    wt = SCRATCH / "x18_wt"
    if wt.exists():
        subprocess.run(["git", "-C", str(main), "worktree", "remove", "--force", str(wt)], capture_output=True)
    r = subprocess.run(["git", "-C", str(main), "worktree", "add", "--detach", str(wt), "HEAD"], capture_output=True)
    assert r.returncode == 0, r.stderr[-300:]
    try:
        r4 = L.Roots.production(repo=wt, out_repo=wt)                  # what run.py builds inside a worktree
        assert Path(r4.records) == main / "arcs/audit/register_maps/post_freeze", r4.records
        assert Path(r4.sets) == main / "arcs/audit/register_sets/post_freeze" and Path(r4.repo) == wt
        assert Path(L.Roots.from_spec(r4.to_spec()).records) == Path(r4.records)       # the workers' copy too
        man = main / "arcs/audit/register_maps/post_freeze/G2"
        if man.is_dir() and any(man.glob("wp4_material_manifest*.json")):
            assert r4.latest_manifest() is not None                     # the final manifest is found from the worktree
    finally:
        subprocess.run(["git", "-C", str(main), "worktree", "remove", "--force", str(wt)], capture_output=True)
    # the sanity gate on synthetic pass folders
    exp = WL.expected_rows("verdict", L.REPO)
    assert exp == 128 and WL.expected_rows("sensitivity", L.REPO) == 101, exp
    d = SCRATCH / "x18_pass"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir()

    def put(n, outcome, status):
        (d / f"row_{n:04d}.json").write_text(json.dumps({"outcome": outcome, "status_written": status}),
                                             encoding="utf-8")
    put(1, "not run", L.STATUS_PENDING)
    put(2, "no statistic", "not auditable: x")
    s1 = WL.pass_sanity(d, "verdict", L.REPO, True, sources=sources())
    assert not s1["ok"] and s1["pending"] == 1 and "material manifest" in s1["why"], s1
    (d / "row_0001.json").unlink()
    s2 = WL.pass_sanity(d, "verdict", L.REPO, False)
    assert not s2["ok"] and s2["computed"] == 0 and s2["why"].startswith("0 computed rows"), s2
    put(3, "computed", None)
    s3 = WL.pass_sanity(d, "verdict", L.REPO, False)
    assert s3["ok"] and s3["computed"] == 1 and s3["expected"] == 128, s3
    assert WL.EXIT["sanity"] not in {v for k, v in WL.EXIT.items() if k != "sanity"}
    ok_ = lambda f: any(rx.match(f) for rx in WL.DIFF_ALLOWED)                  # noqa: E731
    assert ok_("arcs/replication/ARC.md") and ok_("arcs/audit/ARC.md")
    assert not ok_("arcs/replication/src/h_common.py") and not ok_("arcs/replication/ARC.md.py")
    return {"expected_verdict": exp}


@check("X19 run 7 (2026-10-21): in a FINAL manifest an absent R17 output reads R17's own status, another absent object "
       "or an unbuilt set reads upstream / its DEG check - never 'material pending'; the sanity gate's expectation comes "
       "from the final manifest (dry dispatch on the G2 sources: 128 on the stand-ins), counted per target; a missing "
       "expected row fails the gate; row_NNNN_repro.json files are not rows")
def _x19():
    from a1_audit import wp4_launch as WL
    src = sources()
    m = src._m4()
    keep = copy.deepcopy(m)
    try:
        m["objects"] = {k: v for k, v in m["objects"].items() if not k.startswith("r17_map_MDD_1")}
        m["objects"]["r17"] = dict(m["objects"].get("r17") or {}, status=L.STATUS_R17)
        e = raises(lambda: src._e4("r17_map_MDD_1"), R.SourceUnavailable)
        assert e.status == L.STATUS_R17, e.status
        m["objects"]["r17"]["status"] = "ran"
        assert raises(lambda: src._e4("r17_map_MDD_1"), R.SourceUnavailable).status == L.STATUS_UPSTREAM
        assert raises(lambda: src._e4("no_such_object"), R.SourceUnavailable).status == L.STATUS_UPSTREAM
    finally:
        m.clear()
        m.update(keep)
    em = WL.expected_from_manifest("verdict", L.REPO, sources=src)
    assert em["expected"] == 128 and not em["not_expected"], em["not_expected"]
    d = SCRATCH / "x19_pass"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir()
    for row in em["rows"]:
        (d / f"row_{row:04d}.json").write_text(json.dumps({"row": row, "cell_id": f"c{row}", "outcome": "computed"}),
                                               encoding="utf-8")
        (d / f"row_{row:04d}_repro.json").write_text(json.dumps({"what": "reproduction check"}), encoding="utf-8")
    s1 = WL.pass_sanity(d, "verdict", L.REPO, True, sources=src)
    assert s1["ok"] and s1["n_rows"] == 128 and s1["computed"] == 128, s1["why"]
    assert sum(t["expected"] for t in s1["by_target"].values()) == 128
    gone = sorted(em["rows"])[0]
    (d / f"row_{gone:04d}.json").unlink()
    s2 = WL.pass_sanity(d, "verdict", L.REPO, True, sources=src)
    assert not s2["ok"] and s2["missing_rows"] == [gone] and "not computed" in s2["why"], s2["why"]
    return {"by_target": {k: v["expected"] for k, v in s1["by_target"].items()}}


@check("X20 run 8 (2026-10-21): every G2 map input hash is sha256 hex in BOTH versions (Pretzsch's reparcel counts "
       "were a JSON string: ProvenanceError at launch.row_provenance); an amend_5 object's carrier identity at use is "
       "found by its sha256; adopting another commit's primary passes needs only ADOPT_MAY_CHANGE code changed and "
       "every computed row's map inputs reproduced (a tampered input refuses)")
def _x20():
    import re as _re
    from a1_audit import launch as LA
    from a1_audit import wp4_launch as WL
    H = _re.compile(r"^[0-9a-f]{64}$")
    rows = {r.row: r for r in R.register_for_diagnostics(R.REPO) if r.gate == "G2"}
    n_ok = 0
    for ver in (L.VERSION_PRIMARY, L.VERSION_AMEND5):
        src = W4S.WP4Sources(dataclasses.replace(STATE["roots"], version=ver), W3.Roots.production())
        for n, r in sorted(rows.items()):
            p = R.classify(r, frozenset({"G2"}))
            if p["kind"] not in ("compute", "form"):
                continue
            try:
                mh = src.map(p, p["maps"][0])[3]
            except R.SourceUnavailable:
                continue
            assert all(isinstance(v, str) and H.match(v) for v in mh.values()), (ver, n, sorted(mh))
            LA.row_provenance(n, r.target_no, {"row": n, "target_number": r.target_no}, mh, "t0", "t1", {})
            n_ok += 1
    src = sources()
    # adoption evidence on synthetic pass folders
    d = SCRATCH / "x20_res"
    if d.exists():
        shutil.rmtree(d)
    picked = []
    for n, r in sorted(rows.items()):
        p = R.classify(r, frozenset({"G2"}))
        if p["kind"] != "compute":
            continue
        try:
            mh = src.map(p, p["maps"][0])[3]
        except R.SourceUnavailable:
            continue
        picked.append((n, mh))
        if len(picked) == 5:
            break
    for ps in ("verdict", "descriptor", "sensitivity"):
        (d / ps).mkdir(parents=True)
        for n, mh in picked:
            (d / ps / f"row_{n:04d}.json").write_text(json.dumps({"row": n, "outcome": "computed", "row_provenance": {
                "input_hashes": dict(mh, context="0" * 64)}}), encoding="utf-8")
    ev = WL.adopt_evidence(d, L.REPO, sources=src)
    assert ev["ok"] and ev["verdict"]["inputs_equal"] == 5, ev
    f = d / "descriptor" / f"row_{picked[0][0]:04d}.json"
    j = json.loads(f.read_text(encoding="utf-8"))
    k = next(iter(sorted(k for k in j["row_provenance"]["input_hashes"] if k.startswith("map["))))
    j["row_provenance"]["input_hashes"][k] = "f" * 64
    f.write_text(json.dumps(j), encoding="utf-8")
    ev2 = WL.adopt_evidence(d, L.REPO, sources=src)
    assert not ev2["ok"] and ev2["descriptor"]["differing_rows"] == [picked[0][0]], ev2
    ok, why, code = WL.adopt_code_check("8258a6e", "8258a6e")
    assert ok and code == []
    ok2, why2, _ = WL.adopt_code_check("237f248", "8258a6e")                 # wp4_launch / tests / wp4_sources only?
    assert isinstance(ok2, bool) and why2
    ok3, why3, _ = WL.adopt_code_check("087d80d", "8258a6e")                 # wp4_layout changed there: refused
    assert not ok3 and "wp4_layout.py" in why3, why3
    return {"n_rows_hex": n_ok}


@check("X21 G2 run 9 (2026-10-21): the naive joint leg on a 7-parcel class (BrainSMASH's own failure) reads 'not "
       "computable (...)' with its seeds, the other descriptor legs computed; a ValueError not raised inside "
       "brainsmash still raises; descriptors.py is admitted by the diff guard and the adoption only at its pinned blob")
def _x21():
    from a1_audit import descriptors as DS
    from a1_audit import wp4_launch as WL
    rows = {r.row: r for r in R.register_for_diagnostics(R.REPO)}
    src = sources()
    p = R.classify(rows[92], frozenset({"G2"}))
    pr = R.prepare(p, src, p["maps"][0])
    assert pr.ctx.n == 7
    sc = R.seeds_of(p, p["maps"][0])
    rec = DS.naive_joint_leg(pr.adapter, sc["seed_of"], K=20)
    assert rec["status"] == DS.NOT_COMPUTABLE_SMASH and rec["p"] is None and rec["seeds"] and rec["n_parcels"] == 7, rec
    p34 = R.classify(rows[81], frozenset({"G2"}))
    pr34 = R.prepare(p34, src, p34["maps"][0])
    r34 = DS.naive_joint_leg(pr34.adapter, R.seeds_of(p34, p34["maps"][0])["seed_of"], K=20)
    assert r34["status"] == "ok" and r34["p"] is not None
    keep = DS.brainsmash_surrogates
    try:
        def boom(*a, **k):
            raise ValueError("not brainsmash's")
        DS.brainsmash_surrogates = boom
        raises(lambda: DS.naive_joint_leg(pr34.adapter, R.seeds_of(p34, p34["maps"][0])["seed_of"], K=20), ValueError)
    finally:
        DS.brainsmash_surrogates = keep
    path = "arcs/audit/src/a1_audit/descriptors.py"
    assert path in WL.STAT_PATH_EXCEPTIONS and not WL.stat_exception_ok("36a4fe6", path)       # the old blob: refused
    pin = WL.STAT_PATH_EXCEPTIONS[path][0]
    assert subprocess.run(["git", "hash-object", str(Path(L.REPO) / path)], capture_output=True,
                          text=True).stdout.strip() == pin                                       # this tree's file
    return {"naive_joint_7": rec["status"]}


@check("X22 row rerun (2026-11-02): --row-rerun TAG --rows ROWS parses, refuses a lone flag / the amend5 tag / an "
       "adoption; its sanity passes exactly the asked rows at the commit and catches an extra row, another commit, a "
       "pending row and an absent RUN_SUMMARY")
def _x22():
    from a1_audit import wp4_launch as WL
    from a1_audit import wp4_layout as L
    assert WL.row_rerun_args(None, None, None, "amend5") == (True, None, None)
    assert WL.row_rerun_args("liu_t3", "478", None, "amend5") == (True, None, [478])
    assert WL.row_rerun_args("x", "3,1-2", None, "amend5")[2] == [1, 2, 3]
    for bad in (("liu_t3", None, None), (None, "478", None), ("amend5", "478", None), ("Liu", "478", None),
                ("liu_t3", "478", "8258a6e"), ("liu_t3", "478,478", None), ("liu_t3", "0", None), ("liu_t3", "a", None)):
        assert not WL.row_rerun_args(*bad, "amend5")[0], bad
    assert WL.ROW_RERUN_SUMMARY.format(tag="liu_t3") != WL.SUMMARY
    ok_ = lambda f: any(rx.match(f) for rx in WL.DIFF_ALLOWED)                   # noqa: E731
    for f in ("arcs/audit/results/a1_run/G2/verdict/row_0478.json", "arcs/audit/results/MANIFEST_claims.md",
              "arcs/audit/register_maps/post_freeze/G2/x.json", "arcs/audit/register_sets/post_freeze/G2_a5/s.json",
              "arcs/audit/results/a1_run/wp4_g2_summary_dc1ee73.json", "arcs/audit/prereg_amend_6.md"):
        assert ok_(f), f
    for f in ("arcs/audit/src/a1_audit/run.py", "arcs/audit/results/a1_run/ungated/verdict/row_0010.json",
              "arcs/audit/register_maps/post_freeze/ungated/x.json", "arcs/audit/src/a1_audit/verdict.py",
              "arcs/audit/register_sets/post_freeze/G1/s.json", "arcs/audit/prereg.md"):
        assert not ok_(f), f                                                     # planted: still refused
    c = "c" * 40
    d = SCRATCH / "x22_pass"
    d.mkdir(parents=True, exist_ok=True)

    def put(n, commit=c, st="ok", outcome="computed"):
        (d / f"row_{n:04d}.json").write_text(json.dumps({"row": n, "outcome": outcome, "status_written": st,
                                                          "run_identity": {"run_commit": commit}}), encoding="utf-8")
    put(478)
    r0 = WL.row_rerun_sanity(d, [478], c, L.STATUS_PENDING)
    assert not r0["ok"] and "RUN_SUMMARY" in r0["why"], r0                      # planted: no RUN_SUMMARY
    (d / "RUN_SUMMARY.json").write_text("{}", encoding="utf-8")
    r1 = WL.row_rerun_sanity(d, [478], c, L.STATUS_PENDING)
    assert r1["ok"] and r1["outcomes"] == {478: "computed"}, r1
    assert not WL.row_rerun_sanity(d, [478], "d" * 40, L.STATUS_PENDING)["ok"]   # planted: another commit
    put(477)
    assert "differ" in WL.row_rerun_sanity(d, [478], c, L.STATUS_PENDING)["why"]  # planted: an extra row
    (d / "row_0477.json").unlink()
    put(478, st=L.STATUS_PENDING, outcome="not run")
    assert not WL.row_rerun_sanity(d, [478], c, L.STATUS_PENDING)["ok"]           # planted: material pending
    return {"sanity_ok": r1["ok"]}


def main() -> int:
    t0 = time.time()
    print(f"A1 WP4 phase-1 tests: scratch {SCRATCH}", flush=True)
    for run in CHECKS:
        run()
    out = SCRATCH / "test_wp4_phase1_results.json"
    from a1_audit import a3_port as A3
    out.write_text(json.dumps(A3.jsonable(dict(results=RESULTS, failed=FAILED, seconds=round(time.time() - t0, 1))),
                              indent=1) + "\n", encoding="utf-8", newline="\n")
    back = json.loads(out.read_text(encoding="utf-8"))
    assert back["failed"] == FAILED
    print(f"{len(CHECKS) - len(FAILED)} of {len(CHECKS)} checks passed ({time.time() - t0:.0f}s)", flush=True)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
