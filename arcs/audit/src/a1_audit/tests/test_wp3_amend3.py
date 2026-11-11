"""WP3 fix round 2: the checks RUN_PLAN_amend_3.md v2.1 (FROZEN, sha256 da3f3b8b...) lists per reading (R44-R50, section
8.1, B6). Plain script; exits non-zero on any failure. SYNTHETIC stand-ins only (no ungated carrier, supplement or
decoder output is opened; the MOESM2 stand-in is written with matplotlib; the frozen s_extract leg runs on it only).

    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_wp3_amend3 [--scratch DIR] [--keep]
        [--parts P D S B M X Z N]

Part P  R47: the pdfplumber port of s_extract.segura_s7 (values kept), the cross-tool test against the frozen function
        (C:\\Python313\\python.exe -E -P, a fresh empty working directory), every refusal R47 lists, the read-back, the
        version assertion, the Jaccard's closed form, Table S6's rule.
Part D  R45: the decoder object (columns, the decoded list, Entrez ids, the must-fail variants), the failure
        classification, and the attempts through the stage (zero GETs of the carriers, one HEAD per image file URL, the
        whitelist, the waits, the cross-run cap, accounted .part files, crash traces, a foreign carrier.json, the size
        probe, the fallback with its refusing stage).
Part S  R46: the sheet rule, the header search through the guard, the block, the missing-value tokens, the position
        log (and its must-fail transform), the comparator on the common labels, the quarantine after pass 2, identity.
Part B  R50: the pins equal the two SOURCE.md files; a stand-in one byte off stops the stage before any carrier or
        network call.
Part M  section 8.1 / R44: the Moreau clone assertion, the whole-clone move, the deletion request; R44's identity
        references (size vs the remote size; the local git blob); a copy under another path is not picked up.
Part X  R48 / R49: the LIU-T1 / T2* comparator statuses and the two group counts; no target declares SD3 / SD4.
Part Z  B6: no comparator status reaches a row's status.
Part F5 fix round 5: the whole-directory SOURCE.md line (the 61b443f phase-2 KeyError, reproduced at the parent
        commit), the resume of a crashed step 6 (completion record), its no-op re-run and its refusals.
Part N  the dry dispatch (scratch and, unless --skip-real-dry, the real root).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--scratch", default=None)
ap.add_argument("--keep", action="store_true")
ap.add_argument("--skip-real-dry", action="store_true")
ap.add_argument("--parts", nargs="*", default=None)
ARGS, _ = ap.parse_known_args()

from a1_audit import a3_port as A3  # noqa: E402,F401
from a1_audit import fetch_extract as FE  # noqa: E402
from a1_audit import run as R  # noqa: E402
from a1_audit import wp3_layout as L  # noqa: E402
from a1_audit import wp3_pdf as P  # noqa: E402
from a1_audit import wp3_scratch_pdf as SP  # noqa: E402
from a1_audit import wp3_sd7 as SD  # noqa: E402

REPO = R.REPO
TMP = Path(ARGS.scratch) if ARGS.scratch else Path(tempfile.mkdtemp(prefix="a1_wp3_a3_"))
TMP.mkdir(parents=True, exist_ok=True)
RESULTS: list = []
SEP = "-" * 100
PY313 = r"C:\Python313\python.exe"
FE.PG.HGNC_FILE = TMP / "no_such_hgnc_table.txt"          # the guard's HGNC cache preset (no read under E:)
FE.PG._HGNC = frozenset(("SLC6A4", "GRIN2B", "SCN2A", "PTEN"))


def check(name: str, ok, detail: str = "") -> bool:
    ok = bool(ok)
    RESULTS.append((name, ok))
    print(R.ascii_line(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not ok else "")),
          flush=True)
    return ok


def raises(fn, exc, attr: str | None = None, value=None):
    try:
        fn()
    except exc as e:
        return attr is None or getattr(e, attr, None) == value
    except Exception:  # noqa: BLE001
        return False
    return False


ROWS = {r.row: r for r in R.register_for_diagnostics(REPO)}


def plan_of(n: int) -> dict:
    return R.classify(ROWS[n], frozenset())


def tsv_named() -> dict:
    tsv = {plan_of(n)["cell_id"]: ROWS[n]["published_value_and_location"] for n in range(3, 10)}
    return P.tsv_named_values(tsv, SP.s7_terms())


# ================================================================================================================
# Part P: R47
# ================================================================================================================
def _syn_hg(genes):
    from a1_audit import wp3_genes as WG
    from a1_audit import wp3_scratch as SC
    b, _ = SC.synthetic_hgnc(genes)
    return WG.HGNCTable(b)


def frozen_s7(pdf: Path) -> dict:
    """The frozen s_extract.segura_s7, unchanged, under C:\\Python313 -E -P from a fresh empty working directory, with
    INPUTS['segura_moesm2'] pointed at the synthetic file (the driver lives outside the empty directory)."""
    drv = TMP / "frozen_leg" / "drv"
    drv.mkdir(parents=True, exist_ok=True)
    (drv / "frozen_s7.py").write_text(
        "import json, sys\nfrom pathlib import Path\nsys.path.insert(0, sys.argv[1])\nimport s_extract as SE\n"
        "SE.INPUTS['segura_moesm2'] = (Path(sys.argv[2]), 'synthetic stand-in')\nout = SE.segura_s7()\n"
        "sys.stdout.write(json.dumps({'fitz': SE.fitz.VersionBind, 'exe': sys.executable, 'flags': "
        "[sys.flags.ignore_environment, sys.flags.safe_path], 'rows': out}) + '\\n')\n", encoding="utf-8")
    cwd = Path(tempfile.mkdtemp(prefix="empty_cwd_", dir=str(TMP)))
    cp = subprocess.run([PY313, "-E", "-P", str(drv / "frozen_s7.py"), str(REPO / "arcs/audit/src_register"), str(pdf)],
                        cwd=str(cwd), capture_output=True, timeout=600)
    left = list(cwd.iterdir())
    doc = json.loads(cp.stdout.decode("utf-8")) if cp.returncode == 0 else {}
    return dict(code=cp.returncode, stderr=len(cp.stderr), cwd_empty_after=not left, **doc)


def part_p() -> None:
    print(SEP + "\nPart P: R47 - MOESM2 pp. 38-39, the pdfplumber port, the cross-tool test, refusals, read-back")
    import pdfplumber
    terms = SP.s7_terms()
    named = tsv_named()
    s4 = [f"SYNS4G{k:04d}" for k in range(1, 400)]
    hg = _syn_hg(s4)
    d = TMP / "moesm2"
    info = SP.write_moesm2(d / "moesm2.pdf", s4, tsv_named=named)
    got = P.parse(d / "moesm2.pdf", terms, named, set(s4), hg)
    s7 = got["s7"]
    ok_vals = s7["status"] == "transcribed" and all(
        s7["rows"][c]["tokens"] == info["values"][c] for c in info["values"])
    check("P1 the port transcribes 78 terms on 77 printed rows (row 1's ' / ' pair split, the wrapped row repaired); "
          "every planted value read back exactly", ok_vals and len(s7["rows"]) == 78
          and s7["rows"]["SEG-C3a"]["printed_row"] == s7["rows"]["SEG-C3b"]["printed_row"] == 1
          and s7["rows"]["SEG-C3a"]["genes"] == 14 and s7["rows"]["SEG-C3b"]["fold"] == 64.75, json.dumps(s7)[:300])
    check("P1 the saved S7 object holds no term string (cell id, GO id, printed row / order, values)",
          all(set(v) == {"go_id", "printed_row", "printed_order", "genes", "expected", "fold", "fdr", "tokens"}
              for v in s7["rows"].values()))
    s6 = got["s6"]
    check("P1 Table S6: exactly 107 distinct genes (a footnote mark stripped), the other tokens counted, HGNC-mapped",
          s6["status"] == "transcribed" and s6["n_genes"] == 107 and s6["n_non_gene_tokens"] > 0
          and set(s6["members_hgnc"]) == set(info["s6_genes"]))
    fz = frozen_s7(d / "moesm2.pdf")
    port = P.s7_rows_of_page(pdfplumber.open(str(d / "moesm2.pdf")).pages[P.S7_PAGE])
    same = fz.get("rows") and [[r["order"], r["row"], r["term"]] for r in port] == [x[:3] for x in fz["rows"]]
    check("P2 cross-tool: the port's names, printed rows and order equal the FROZEN s_extract.segura_s7's (PyMuPDF "
          f"{fz.get('fitz')}, C:\\Python313 -E -P, a fresh empty cwd left empty); 7 named among 78",
          fz.get("code") == 0 and same and fz.get("fitz") == "1.27.1" and fz.get("flags") == [1, 1]
          and fz.get("cwd_empty_after") and sum(x[3] != "other" for x in fz["rows"]) == 7,
          json.dumps({k: v for k, v in fz.items() if k != "rows"}))
    fz_bad = frozen_s7_variant = None
    for variant, check_label, which in (("name", P.CHECK_NAMES, "s7"), ("row", P.CHECK_PRINTED_ROW, "s7"),
                                        ("precision", P.CHECK_PRECISION, "s7"), ("parts", P.CHECK_PARTS, "s7"),
                                        ("no_title", P.CHECK_TITLE, "s7"), ("s6_two_captions", P.CHECK_S6_CAPTION, "s6"),
                                        ("genes106", P.CHECK_S6_N, "s6")):
        f = d / f"moesm2_{variant}.pdf"
        SP.write_moesm2(f, s4, tsv_named=named, variant=variant)
        g = P.parse(f, terms, named, set(s4), hg)
        other = "s6" if which == "s7" else "s7"
        check(f"P3 refused ({variant}): {which} reads 'not transcribed: {check_label}'; the other table still "
              "transcribed", g[which] == {"status": "not transcribed", "check": check_label}
              and g[other]["status"] == "transcribed", json.dumps(g[which])[:200])
        _ = (fz_bad, frozen_s7_variant)
    stored = json.loads(json.dumps(got))
    check("P4 read-back: a second parse (a fresh pdfplumber.open) equals the stored object",
          P.readback(d / "moesm2.pdf", stored, terms, named, set(s4), hg))
    planted = json.loads(json.dumps(got))
    c = next(c for c in planted["s7"]["rows"] if not c.startswith("SEG-C3") or c.startswith("SEG-C3-D"))
    planted["s7"]["rows"][c]["fold"] = round(planted["s7"]["rows"][c]["fold"] + 1.0, 2)
    planted["s7"]["rows"][c]["tokens"]["fold"] = str(planted["s7"]["rows"][c]["fold"])
    check("P4 read-back: a planted one-digit change in the stored object is caught",
          not P.readback(d / "moesm2.pdf", planted, terms, named, set(s4), hg))
    old = pdfplumber.__version__
    try:
        pdfplumber.__version__ = "0.11.9"
        bad_ver = raises(lambda: P.parse(d / "moesm2.pdf", terms, named, set(s4), hg), P.PdfEnvironmentFault)
    finally:
        pdfplumber.__version__ = old
    check("P5 pdfplumber at another version: an environment fault (PdfEnvironmentFault; the stage stops: Q10), never "
          "a refusal record (L14, extended)", bad_ver)
    A, B = {"G1", "G2", "G3", "G4"}, {"G3", "G4", "G5"}
    j = P.jaccard(A, B)
    check("P6 the Jaccard of planted lists equals its closed form |A n B| / |A u B| = 2 / 5",
          Fraction(j["n_intersection"], j["n_union"]) == Fraction(2, 5) and j["J"] == 0.4 and j["n_A"] == 4
          and j["n_B"] == 3 and P.jaccard(set(), set())["J"] is None)
    # P8 identity at use (R47 (a)): MOESM2 one byte off -> the S6 and D-row comparators 'not computable (carrier changed)'
    from a1_audit import real_sources as RS
    from a1_audit import wp3_repro as WR
    r = make("p_moesm2")
    pth, _ = r.pin("segura_moesm2")
    bb = bytearray(pth.read_bytes())
    bb[len(bb) // 3] ^= 1
    pth.write_bytes(bytes(bb))
    res8, _, _, _ = stage(r)
    r10 = WR.row_reproduction(plan_of(10), RS.WP3Sources(r))
    r3 = WR.row_reproduction(plan_of(3), RS.WP3Sources(r))
    check("P8 (R47 (a)) MOESM2 one byte off its pin: the stage records 'not auditable (map changed)'; the S6 and D-row "
          "comparators read 'not computable (carrier changed: ...)'; rows 3-9 keep the TSV's values",
          res8["entries"][L.MOESM2_KEY]["status"] == "not auditable (map changed)"
          and r10["published"]["status"] == WR.MOESM2_CHANGED and r10["jaccard_table_s6"]["status"] == WR.MOESM2_CHANGED
          and r3["published"]["fold"] == "7.35")
    check("P7 half a unit in the TSV text's last digit ('9.4e-6' -> 5e-8; '14' -> 0.5; '0.0249' -> 5e-5)",
          float(P.half_unit("9.4e-6")) == 5e-8 and float(P.half_unit("14")) == 0.5
          and float(P.half_unit("0.0249")) == 5e-5)


# ================================================================================================================
# Part S (units): R46's rules
# ================================================================================================================
def part_s_units() -> None:
    print(SEP + "\nPart S (units): R46 - the sheet rule, the header rule, the block, missing values, the position log")
    names = [f"Supplementary Data {k}" for k in range(1, 16)]
    sel = SD.sheet_matches(names)
    check("S1 'Supplementary Data 7' among 'Supplementary Data 1' ... '15' is selected (exactly one)",
          [names[i] for i in sel] == ["Supplementary Data 7"])
    for n in ("SD7", "Data 7", "Supplementary Data 7 (AHBA)", "Supplemental Data 7", "Supplementary Dataset 7",
              "Supp Data 7", "SD 7", "S7", "7"):
        check(f"S1 the rule selects '{n}'", SD.sheet_matches([n, "Supplementary Data 1"]) == [0])
    for n in ("Supplementary Data 17", "Supplementary Data 70", "Table 7"):
        check(f"S1 the rule does not select '{n}' alone", SD.sheet_matches([n]) == [])
    check("S1 'Supplementary Data 7' with 'Supp Data 7': two matches (refused by the stage)",
          len(SD.sheet_matches(["Supplementary Data 7", "Supp Data 7"])) == 2)
    r1, r2 = SD.asd_rule(1), SD.asd_rule(2)
    check("S2 the ASD rule: pass 1 [0], pass 2 [0, ASD]; ASD_SFARI_1 beside ASD selects ASD; two ASD cells and ASD at "
          "position 0 are refused; an empty position-0 header accepted",
          r1(["Region", "ASD", "ADHD"]) == [0] and r2(["Region", "ASD_SFARI_1", " asd "]) == [0, 2]
          and r2(["Region", "ASD", "asd"]) == [] and r2(["ASD", "x"]) == [] and r2([None, "ASD"]) == [0, 1])
    import pandas as pd
    dk = pd.read_csv(REPO / "artifacts/ahba/dk_atlas_info.csv")
    dkn = set(str(x) for x in dk["label"])
    rows = [["title"], [None], ["Region", "ASD"], [None, None], ["", None], ["L_bankssts_thickavg", 0.1],
            ["R_bankssts_thickavg", 0.2], [None], ["Note: footnote", None], ["ICV", 0.3]]
    blk = SD.label_block(rows, 2, dkn)
    check("S3 the block: two empty rows after the header skipped; footnotes after a blank row counted, not read as "
          "labels", blk["rows"] == [5, 6] and blk["counts"]["n_rows_skipped_before_block"] == 2
          and blk["counts"]["n_cells_after_block"] == 2 and blk["counts"]["n_after_block_dropped_kind"] == 1)
    rows2 = rows[:8] + [["L_cuneus_thickavg", 0.4]]
    check("S3 a DK label after a blank row: 'SD7 label block interrupted' (fail closed)",
          raises(lambda: SD.label_block(rows2, 2, dkn), SD.Sd7Refused, "status", SD.SD7_INTERRUPTED))
    from a1_audit import forms as FM
    check("S3 a non-label column at position 0 (row numbers) fails closed by R42 (d)'s normaliser",
          raises(lambda: FM.sd7_normalise(["1", "2", "3"], dk), FM.FormNotTestable, "status", FM.SD7_UNMATCHED))
    kinds = [SD.value_of(v)[0] for v in (0.12, 3, None, "NA", " n/a ", "nan", "#N/A", "#DIV/0!", "", "n.s.", True,
                                         float("nan"), float("inf"), "0.1")]
    check("S4 missing values: NA, n/a, nan, Excel errors, empty -> missing; n.s., a bool, NaN, inf, a numeric text -> "
          "refuse; numbers -> values", kinds == ["value", "value", "missing", "missing", "missing", "missing",
                                                 "missing", "missing", "missing", "refuse", "refuse", "refuse",
                                                 "refuse", "refuse"])
    v = SD.PositionView({0: ["a", "b"], 1: [0.1, 0.2]}, handed=(0,))
    lab = v.column(0)
    check("S5 pass 1's view hands position 0 only; its log holds position 0 alone", lab == ["a", "b"]
          and v.consumed() == [0])
    v2 = SD.PositionView({0: ["a"], 1: [0.1]}, handed=(0,))

    def greedy(view):           # must-fail: a transform that reads the ASD position in pass 1
        view.column(0)
        return view.column(1)
    check("S5 must-fail: a pass-1 transform reading the ASD position is caught (refused, and logged)",
          raises(lambda: greedy(v2), SD.PositionRefused) and v2.consumed() == [0, 1])


# ================================================================================================================
# Part D (units): R45's classification
# ================================================================================================================
def part_d_units() -> None:
    print(SEP + "\nPart D (units): R45 - the failure classification")
    from a1_audit import wp3_decoder as DC

    def rec(stage, **ff):
        return {"status": FE.STATUS_FAILED, "failed_stage": stage, "failed_class": "X", "failed_where": "x.py:1",
                "fetch_failure": ff}
    out = {f"curl {n}": DC.classify(rec("fetch:get", curl_exit=n))["outcome"] for n in (18, 28, 55, 6, 7, 35, 52, 56,
                                                                                           23, 60, 2, 3, 26, 27, 77)}
    out.update({f"HTTP {n}": DC.classify(rec("fetch:get", http_status=n))["outcome"] for n in (503, 500, 429, 404,
                                                                                               403, 301)})
    out["html"] = DC.classify(rec("fetch:get", html=True))["outcome"]
    out["read:file"] = DC.classify(rec("read:file"))["outcome"]
    out["save"] = DC.classify(rec("save"))["outcome"]
    out["extracted"] = DC.classify({"status": FE.STATUS_EXTRACTED})["outcome"]
    exp = {**{f"curl {n}": DC.OUT_TRANSPORT for n in (18, 28, 55, 6, 7, 35, 52, 56)},
           **{f"curl {n}": DC.OUT_STOPPED for n in (23, 60, 2, 3, 26, 27, 77)},
           "HTTP 503": DC.OUT_TRANSPORT, "HTTP 500": DC.OUT_TRANSPORT, "HTTP 429": DC.OUT_TRANSPORT,
           "HTTP 404": DC.OUT_FINAL, "HTTP 403": DC.OUT_FINAL, "HTTP 301": DC.OUT_FINAL, "html": DC.OUT_FINAL,
           "read:file": DC.OUT_FINAL, "save": DC.OUT_STOPPED, "extracted": DC.OUT_EXTRACTED}
    check("D1 classification: curl 6 / 7 / 18 / 28 / 35 / 52 / 55 / 56, HTTP 429 and 5xx -> transport (counted); any "
          "other curl exit (2, 3, 23, 26, 27, 60, 77) -> stopped (not counted); another HTTP status, an HTML page, a "
          "declared read refused -> final refusal", out == exp,
          json.dumps({k: v for k, v in out.items() if exp[k] != v}))


# ================================================================================================================
# the stage on synthetic stand-ins (shared)
# ================================================================================================================
def make(name: str, **kw):
    from a1_audit import wp3_scratch as SC
    return SC.build_scratch(TMP / name, **kw)


class Clock:
    def __init__(self):
        self.waits = []

    def __call__(self, s):
        self.waits.append(int(s))


def stage(roots, *, only=None, **net):
    """The material stage on a scratch layout with the network mock and a recording clock."""
    from a1_audit import wp3_decoder as DC
    from a1_audit import wp3_material as WM
    from a1_audit import wp3_scratch as SC
    buf = io.StringIO()
    clock = Clock()
    old = DC.SLEEP
    DC.SLEEP = clock
    try:
        with SC.scratch_net(roots, **net) as calls:
            res = WM.run_material(roots, out=buf, only=only, run_info={"mode": "scratch (synthetic stand-ins)"})
    finally:
        DC.SLEEP = old
    return res, buf.getvalue(), list(calls), clock.waits


def urls(roots):
    from a1_audit import wp3_layout as WL
    idr = WL.identity_records(roots, lambda p: Path(p).read_bytes())
    return {"files": {idr[WL.SEGURA_MAP_KEY[i]]["file_url"]: i for i in WL.SEGURA_IMAGES},
            "decoders": {WL.DECODER_URL.format(image=i): i for i in WL.SEGURA_IMAGES},
            "moreau": idr[WL.MOREAU_KEY]["url"], "segura_urls": [idr[WL.SEGURA_MAP_KEY[i]]["url"] for i in WL.SEGURA_IMAGES]}


def n_get(calls, image):
    return sum(1 for c in calls if c[0] == "get" and f"/{image}/" in c[1])


# ================================================================================================================
# Part D (integration): R44's network and R45's attempts
# ================================================================================================================
def part_d() -> None:
    print(SEP + "\nPart D: R44 / R45 - the network, the decoder object, unavailable, attempts, crash traces")
    from a1_audit import real_sources as RS
    from a1_audit import wp3_decoder as DC
    from a1_audit import wp3_material as WM
    from a1_audit import wp3_repro as WR
    roots = make("d_main")
    res, text, calls, waits = stage(roots)
    u = urls(roots)
    heads = [c[1] for c in calls if c[0] == "head"]
    gets = [c[1] for c in calls if c[0] == "get"]
    check("D2 (R44 B7) the network mock: zero GETs of the three carriers; exactly one HEAD per image file URL; no "
          "request for Moreau; GETs of the two decoder URLs only and NO HEAD of them (R45 (a): one curl; fix round 3, "
          "C (a))", res["status"] == "final"
          and all(heads.count(f) == 1 for f in u["files"]) and not any(g in u["files"] for g in gets)
          and not any(c[1] == u["moreau"] for c in calls) and set(gets) == set(u["decoders"]) and len(gets) == 2
          and not any(h in u["decoders"] for h in heads) and len(heads) == 2, json.dumps([c[0] for c in calls]))
    e = res["entries"]
    check("D2 both decoders extracted and decided once (outcome records: start + outcome per attempt)",
          all(e[k]["status"] == FE.STATUS_EXTRACTED and e[k]["final"] for k in L.SEGURA_DECODER_KEY.values())
          and all(len(list((Path(roots.control) / "ungated").glob(f"{k}_attempt1*.json"))) == 2
                  for k in L.SEGURA_DECODER_KEY.values()))
    # D3 the decoder object on synthetic tables
    from a1_audit import wp3_genes as WG
    from a1_audit import wp3_scratch as SC
    b, ids = SC.synthetic_hgnc(["AAA1", "BBB2", "CCC3", "DDD4", "EEE5", "FFF6"])
    hg = WG.HGNCTable(b)
    ent = {g: ids[g][1] for g in ids}
    cols = list(L.DECODER_COLUMNS)

    def row(sym, entrez, t, q):
        return [sym, entrez, "name", t, 0.01, q, 1.0, 0.1]
    rows = [row("AAA1", None, -2.0, 0.049), row("BBB2", None, 2.0, 0.05), row("CCC3", None, 1.0, 0.2),
            row("CCC3", None, 3.0, 0.01), row("XXX9", int(ent["DDD4"]), 1.5, 0.001),
            row("EEE5", float(ent["EEE5"]), 0.5, 0.3), row("EEE5", " " + ent["EEE5"] + " ", 0.5, 0.3),
            row("FFF6", "12a4", 1.0, 0.04), row("BBB2", None, 1.0, None), row("BBB2", None, 1.0, "0.01")]
    o = WM.decoder_object(json.dumps({"columns": cols, "data": rows}).encode(), hg, 790618)
    dec = WR.decoded_from_decoder(o)
    E = {"AAA1", "CCC3", "DDD4", "FFF6"}
    check("D3 (R45 (d)) q .049 with t < 0 decoded, q = .05 not; two rows of one gene, one below .05 -> one gene; an "
          "Entrez id naming another approved symbol governs; '12a4' is no id (the symbol rule)", dec == E, str(sorted(dec)))
    e_rows = [r for r, g in zip(o["genes"], o["genes"]) if g == "EEE5"]
    check("D3 an Entrez id as 1234, 1234.0 and ' 1234 ' reads as the same id; a null / text q is not decoded, counted",
          len(e_rows) == 2 and o["counts"]["n_nonfinite_q"] == 2 and o["counts"]["n_genes_with_more_than_one_row"] == 2)

    def positive_only(obj):          # must-fail variant 1: positive t only
        return {g for g, q, t in zip(obj["genes"], obj["q"], obj["t"]) if q < 0.05 and (t or 0) > 0}

    def le05(obj):                   # must-fail variant 2: q <= .05
        return {g for g, q in zip(obj["genes"], obj["q"]) if q <= 0.05}
    check("D3 must-fail variants: a positive-t-only list and a '<= .05' list each differ from the registered list "
          "(the D3 check catches both)", positive_only(o) != E and le05(o) != E)
    check("D3 (R45 (c)) the column list labelled as ahba.py's; its sha256 recorded; t-sign counts of decoded rows",
          o["column_list_label"] == WM.DECODER_COLUMNS_SAME and len(o["column_list_sha256"]) == 64
          and o["counts"]["decoded_rows_by_t_sign"] == {"t_positive": 3, "t_negative": 1, "t_zero_or_absent": 0})
    order = [5, 0, 3, 1, 4, 2, 6, 7]
    o2 = WM.decoder_object(json.dumps({"columns": [cols[i] for i in order] + ["extra"],
                                       "data": [[r[i] for i in order] + [1] for r in rows], "other": 1}).encode(),
                           hg, 790618)
    check("D3 extra and reordered columns accepted and labelled; the other key and column counted; same list",
          WR.decoded_from_decoder(o2) == E and o2["column_list_label"] == WM.DECODER_COLUMNS_DIFFER
          and o2["counts"]["n_other_columns"] == 4 and o2["counts"]["n_other_keys"] == 1
          and o["counts"]["n_other_columns"] == 3)
    bad = {"missing FDR column": json.dumps({"columns": [c for c in cols if c != "p (FDR corrected)"],
                                             "data": [r[:5] + r[6:] for r in rows]}),
           "duplicated gene_symbol": json.dumps({"columns": cols + ["gene_symbol"], "data": [r + [r[0]] for r in rows]}),
           "a row of another length": json.dumps({"columns": cols, "data": rows[:2] + [rows[2][:5]]}),
           "all q null": json.dumps({"columns": cols, "data": [r[:5] + [None] + r[6:] for r in rows]})}
    for what, txt in bad.items():
        check(f"D4 (R45 (e)) refused at the declared read: {what}",
              raises(lambda t=txt: WM.decoder_object(t.encode(), hg, 1), ValueError))
    # D4 through the stage: each refusal makes the decoder unavailable, the fallback applies with the stage recorded
    for name, script, head_sizes, stage_exp in (
            ("d_cols", {790618: ["bad_columns"], 781986: ["all_q_null"]}, None, ("read:file", "read:file")),
            ("d_rows", {790618: ["dup_symbol"], 781986: ["short_row"]}, None, ("read:file", "read:file")),
            ("d_http", {790618: [("http", 404)], 781986: ["html"]}, None, ("fetch:get", "fetch:get"))):
        r = make(name)
        res2, _, calls2, _ = stage(r, script=script, head_sizes=head_sizes)
        ent = [res2["entries"][L.SEGURA_DECODER_KEY[i]] for i in L.SEGURA_IMAGES]
        ok = all(x["status"] == DC.UNAVAILABLE % DC.OUT_FINAL and x["refusing_stage"] == s and x["final"]
                 for x, s in zip(ent, stage_exp)) and res2["status"] == "final" \
            and n_get(calls2, 790618) == 1 and n_get(calls2, 781986) == 1
        check(f"D4 {name}: {list(script.values())} -> unavailable (final refusal; no retry), the refusing stage "
              "recorded", ok, json.dumps(ent)[:300])
        if name == "d_cols":
            rr = WR.row_reproduction(plan_of(1), RS.WP3Sources(r))
            dl = rr["decoded_list"]
            check("D4 the reproduction takes R22's fallback, labelled, with the refusing stage (R45 (e))",
                  dl.get("label") == WR.R22_FALLBACK_LABEL and dl.get("refusing_stage") == "read:file")
    r = make("d_size")
    cl = urls(r)
    res3, text3, calls3, _ = stage(r, head_sizes={790618: L.identity_records(r, lambda p: Path(p).read_bytes())
                                                  ["segura_790618"]["content_length"] + 1},
                                   head_last_modified={781986: "Mon, 01 Jan 2024 00:00:00 GMT"})
    e3 = res3["entries"]
    check("D10 (R45 (e)) a HEAD size of the pre-freeze size + 1 -> size mismatch, unavailable, no GET; a different "
          "Last-Modified is labelled, never refused", e3["segura_decoder_790618"]["status"] == DC.UNAVAILABLE % DC.OUT_SIZE
          and n_get(calls3, 790618) == 0 and e3["segura_decoder_781986"]["status"] == FE.STATUS_EXTRACTED
          and DC.LM_LABEL in text3 and sum(1 for c in calls3 if c[0] == "head" and c[1] in cl["files"]) == 2)
    r = make("d_nosize")
    res3b, text3b, calls3b, _ = stage(r, head_sizes={790618: None})
    check("D10 (R45 (e)) no size returned by the HEAD: the fetch proceeds (extracted), the record says so",
          res3b["entries"]["segura_decoder_790618"]["status"] == FE.STATUS_EXTRACTED and n_get(calls3b, 790618) == 1
          and "identity not established (reference missing); content length none" in text3b)
    # D5 attempts within a run: the whitelist and the waits
    r = make("d_tr")
    res4, _, calls4, waits4 = stage(r, script={790618: [("curl", 18), ("http", 503), ("curl", 28)],
                                               781986: [("curl", 55), ("http", 429), "ok"]}, partial_on_fail=True)
    e4 = res4["entries"]
    check("D5 curl 18 / HTTP 503 / curl 28 -> three transport failures in one run -> unavailable; curl 55 / HTTP 429 "
          "then a success -> extracted; waits 10 and 30 min (mocked clock)",
          e4["segura_decoder_790618"]["status"] == DC.UNAVAILABLE % "three transport failures"
          and e4["segura_decoder_781986"]["status"] == FE.STATUS_EXTRACTED and n_get(calls4, 790618) == 3
          and n_get(calls4, 781986) == 3 and waits4 == [600, 1800, 600, 1800], json.dumps(waits4))
    res4b, _, calls4b, _ = stage(r)
    check("D5 a fourth attempt never happens: the next run makes no request (final manifest: a no-op)",
          res4b.get("noop") is True and n_get(calls4b, 790618) == 0)
    # D6 local faults: stop, no attempt consumed
    r = make("d_local")
    res5, _, calls5, _ = stage(r, script={790618: [("curl", 23)]})
    check("D6 curl 23 stops the stage for the operator (no manifest), the attempt not counted",
          res5.get("stopped") and res5["status"] == DC.STOP_LOCAL and r.latest_manifest() is None
          and not r.partial_manifests())
    res6, _, calls6, _ = stage(r, script={790618: [("curl", 60)]})
    check("D6 curl 60 stops it again (not counted)", res6.get("stopped") and res6["status"] == DC.STOP_LOCAL)
    res7, _, calls7, _ = stage(r, script={790618: [("curl", 28), ("curl", 28), ("curl", 28)]})
    atts = DC.read_attempts(r, "segura_decoder_790618")
    check("D6 after two local faults, three transport attempts still run (5 attempts recorded, 3 counted)",
          res7["entries"]["segura_decoder_790618"]["status"] == DC.UNAVAILABLE % "three transport failures"
          and n_get(calls7, 790618) == 3 and len(atts) == 5 and DC.n_transport(atts) == 3)
    # D7 the cap across runs; accounted .part files
    r = make("d_cap")
    res8, _, _, _ = stage(r, script={790618: [("curl", 28), ("curl", 28), ("curl", 23)]}, partial_on_fail=True)
    parts = sorted(p.name for p in (Path(r.data) / "segura_decoder_790618").glob("carrier.json.a*.part"))
    res9, text9, calls9, _ = stage(r, script={790618: [("curl", 28), "ok"]}, partial_on_fail=True)
    check("D7 a second run after two recorded transport failures (each .part with an outcome record): no stop, one GET "
          "at most, then unavailable", res8.get("stopped") and len(parts) == 3 and not res9.get("stopped")
          and n_get(calls9, 790618) == 1 and res9["entries"]["segura_decoder_790618"]["status"]
          == DC.UNAVAILABLE % "three transport failures" and "partial file accounted for" in text9)
    # D8 a recorded final refusal whose .part is on disk: unavailable, no stop, no request (a subset run first)
    r = make("d_final")
    stage(r, only=["segura_decoder_790618"], script={790618: [("http", 404)]})
    res10, _, calls10, _ = stage(r)
    check("D8 a recorded final refusal with its .part on disk reads 'unavailable' in the next run: no stop, no request",
          (Path(r.data) / "segura_decoder_790618" / "carrier.json.a1.part").exists() and not res10.get("stopped")
          and n_get(calls10, 790618) == 0 and res10["entries"]["segura_decoder_790618"]["status"]
          == DC.UNAVAILABLE % DC.OUT_FINAL)
    # D9 crash traces
    for name, plant in (("trace_part", "part"), ("trace_start", "start"), ("trace_foreign", "foreign")):
        r = make(f"d_{name}")
        kd = Path(r.data) / "segura_decoder_790618"
        kd.mkdir(parents=True, exist_ok=True)
        if plant == "part":
            (kd / "carrier.json.a1.part").write_bytes(b"{")
        elif plant == "start":
            c = Path(r.control) / "ungated"
            c.mkdir(parents=True, exist_ok=True)
            (c / "segura_decoder_790618_attempt1.json").write_text(json.dumps({"k": 1}), encoding="utf-8")
        else:
            (kd / "carrier.json").write_bytes(b"{\"columns\": [], \"data\": []}")
        resx, _, callsx, _ = stage(r)
        exp = DC.STOP_FOREIGN if plant == "foreign" else DC.STOP_TRACE
        check(f"D9 a crash trace stops the stage ({plant}): no manifest, no GET of that image",
              resx.get("stopped") and resx["status"] == exp and n_get(callsx, 790618) == 0
              and r.latest_manifest() is None)


# ================================================================================================================
# Part S (integration): R46 through the wrapper
# ================================================================================================================
def _sd7_run(roots, variant, tag):
    """SD7's two passes on a variant workbook (a fresh output tree per variant), through wp3_material.run_sd7."""
    import dataclasses as dc
    from a1_audit import privacy_wrap as PW
    from a1_audit import wp3_material as WM
    from a1_audit import wp3_scratch as SC
    xb = SC.synthetic_sd7_book(np.random.default_rng(5), variant)
    d = TMP / f"sd7_{tag}"
    p = d / "data" / "liu" / "supplement_syn.xlsx"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(xb)
    import hashlib
    rv = dc.replace(roots, sd7_copy=(str(p), hashlib.sha256(xb).hexdigest(), len(xb), "https://example.org/syn.xlsx"),
                    records=str(d / "out/records"), artifacts=str(d / "out/artifacts"), control=str(d / "out/control"),
                    logs=str(d / "out/logs"), data=str(d / "data"), quarantine=str(d / "data/_quarantine"))
    buf = io.StringIO()
    door = WM.Door(rv)
    em = PW.Emitter(WM._allow(rv), stream=buf)
    out = WM.run_sd7(rv, door, em, buf, lambda k: True)
    return rv, out, buf.getvalue(), p


def part_s() -> None:
    print(SEP + "\nPart S: R46 - SD7 through the section 8 wrapper on synthetic workbooks")
    from a1_audit import forms as FM
    from a1_audit import wp3_material as WM
    from a1_audit import wp3_repro as WR
    roots = make("s_main")
    rv, out, text, p = _sd7_run(roots, None, "base")
    e1, e2 = out["liu_sd7_labels"], out["liu_sd7_values"]
    rec1 = json.loads((Path(rv.records) / e1["record_path"]).read_bytes())
    rec2 = json.loads((Path(rv.records) / e2["record_path"]).read_bytes())
    lab = json.loads((Path(rv.artifacts) / e1["object_path"]).read_bytes())["objects"]["sd7"]
    val = json.loads((Path(rv.artifacts) / e2["object_path"]).read_bytes())["objects"]["sd7"]
    check("S6 the sheet selected by the name rule among 15 (one match); the header found in row 2 (a title row, an "
          "empty position-0 header, ASD_SFARI_1 beside ASD)", rec1["sheet_rule_matches"] == {"sd7": 1}
          and rec1["sheets"]["declared"][0]["header_row"] == 2 and e1["status"] == FE.STATUS_EXTRACTED
          and lab["status"] == "matched")
    check("S6 the block: two empty rows skipped; the footnote after a blank row counted, not read as a label",
          rec1["sheets"]["declared"][0]["n_rows_skipped_before_block"] == 2
          and rec1["sheets"]["declared"][0]["n_cells_after_block"] == 1 and lab["n_labels"] == 87)
    check("S7 pass 1's position log holds position 0 alone; pass 2 position 0 and the ASD column",
          rec1["positions_consumed"] == {"sd7": [0]} and rec1["positions_handed"] == {"sd7": [0]}
          and rec2["positions_consumed"] == {"sd7": [0, 2]})
    check("S8 missing values: NA, #N/A and an empty cell read as missing (3), counted; values by position",
          val["n_missing"] == 3 and len(val["values_by_position"]) == 87
          and sum(v is None for v in val["values_by_position"]) == 3)
    check("S9 no label string is saved (normalised record and values by position only)",
          not any(isinstance(x, str) and "thickavg" in x for x in json.dumps(lab).split('"')))
    for variant, status in (("two_sheets", "sheet"), ("no_sheet", "sheet"), ("no_header", "header"),
                            ("two_asd", "header"), ("interrupted", "interrupted"), ("rownumbers", "unmatched")):
        rvv, outv, _, _ = _sd7_run(roots, variant, variant)
        exp = {"sheet": SD.SD7_SHEET, "header": SD.SD7_HEADER, "interrupted": SD.SD7_INTERRUPTED,
               "unmatched": FM.SD7_UNMATCHED}[status]
        got = outv[L.SD7_KEY]["status"]
        check(f"S10 {variant}: T4 / T5 read '{exp}' (fail closed), pass 2 not run", got == exp
              and outv["liu_sd7_values"]["status"].startswith("not run (SD7 pass 2"), got)
    rvn, outn, _, _ = _sd7_run(roots, "ns", "ns")
    check("S11 'n.s.' in the ASD column refuses pass 2 only: the comparator reads 'not computable (SD7's ASD column "
          "holds a non-numeric value)'; pass 1 matched (T4 / T5 computed)",
          outn["liu_sd7_values"]["status"] == SD.SD7_NON_NUMERIC and outn["liu_sd7_labels"]["status"] == FE.STATUS_EXTRACTED)
    rvi, outi, texti, pi = _sd7_run(roots, "identifier", "identifier")
    r1 = json.loads((Path(rvi.records) / outi["liu_sd7_labels"]["record_path"]).read_bytes())
    r2 = json.loads((Path(rvi.records) / outi["liu_sd7_values"]["record_path"]).read_bytes())
    check("S12 an identifier-bearing SD7 is quarantined only after pass 2 (pass 1 defers step 6), once, with the "
          "deletion request", r1["identifier_bearing"] and r1["quarantine"].get("deferred") and r2["quarantine"]["quarantined"]
          and not pi.exists() and (Path(rvi.quarantine) / "ungated" / "liu_sd7_values" / "carrier.xlsx").exists()
          and "NDAR_INVAB123CDE" not in texti)
    xb = pi.read_bytes() if pi.exists() else None
    rvc, outc, _, pc = _sd7_run(roots, None, "changed")
    _ = (xb, rvc, outc)
    b = bytearray(pc.read_bytes())
    b[len(b) // 2] ^= 1
    pc.write_bytes(bytes(b))
    import dataclasses as dc
    rvc2 = dc.replace(rvc, records=str(Path(rvc.records).parent / "records2"), artifacts=str(Path(rvc.artifacts).parent /
                                                                                          "artifacts2"))
    from a1_audit import privacy_wrap as PW
    buf = io.StringIO()
    outc2 = WM.run_sd7(rvc2, WM.Door(rvc2), PW.Emitter(WM._allow(rvc2), stream=buf), buf, lambda k: True)
    check("S6 SD7's block row count reported beside the registered 78 (R46 (d); never a refusal)",
          out[L.SD7_KEY]["block_rows"] == 87 and out[L.SD7_KEY]["registered_rows"] == 78)
    check("S13 identity: a one-byte change in the registered copy reads 'not auditable (map changed)' (T4 and T5)",
          outc2[L.SD7_KEY]["status"] == "not auditable (map changed)")
    # S14 the position log must-fail through the wrapper: a pass-1 transform reading the ASD position
    import pandas as pd
    dk = pd.read_csv(REPO / "artifacts/ahba/dk_atlas_info.csv")
    lab_t, _ = WM.sd7_targets(rv, tuple(sorted(set(str(x) for x in dk["label"]))))

    def greedy(objects):
        v = objects["sd7"]
        v.column(0)
        v.column(2)
        return {"sd7": {"x": 1}}

    def lazy(objects):
        return {"sd7": {"x": 1}}
    for name, tf in (("reads the ASD position", greedy), ("consumes nothing", lazy)):
        d = TMP / f"sd7_mustfail_{name.split()[0]}"
        import dataclasses as dc2
        froots = dc2.replace(rv.fe_roots(), records=d / "records", artifacts=d / "artifacts", logs=d / "logs",
                             control=d / "control")
        r = FE.run_target(lab_t, froots, out=io.StringIO(), transform=tf)
        rec = json.loads(Path(r["record_path"]).read_bytes())
        check(f"S14 must-fail: a pass-1 transform that {name} is caught (refused at transform / the position log)",
              r["status"] == FE.STATUS_FAILED and rec["failed_stage"] in ("transform", "transform:positions"))
    # S16 'n.s.' through the stage and the loaders: T4 computed from pass 1, the comparator not computable
    from a1_audit import real_sources as RS
    from a1_audit import forms as FM2
    rn = make("s_ns", sd7_variant="ns")
    stage(rn)
    srcn = RS.WP3Sources(rn)
    inp4 = srcn.liu_inputs(plan_of(473))
    sc = R.seeds_of(plan_of(473), 0)
    res4 = FM2.liu_compute(plan_of(473)["liu_spec"], inp4, K=10, seed_of=sc["seed_of"], g3_seed=sc["g3_seed"],
                           two_sided=False, registered_direction=1)
    rl = WR.row_reproduction(plan_of(473), srcn, res4)
    check("S16 'n.s.' (pass 2 refused): T4 still computed from pass 1; its comparator reads 'not computable (SD7's ASD "
          "column holds a non-numeric value)'", np.isfinite(res4["T"]) and rl["status"] == SD.SD7_NON_NUMERIC)
    # S15 the comparator on the common labels (synthetic result and record)
    dkt = FM.dk_table_checked(dk)
    labels = SD7_LABELS()
    labrec = FM.sd7_normalise(labels, dk)
    ids = [e["ids"][0] for e in labrec["entries"] if e["kind"] == "matched"]
    cort = [i for i in ids if dkt.at[i, "structure"] == "cortex"]
    res = {"T": 0.4, "labels": {"label_set": {"keys": cort, "hip": []}},
           "groups": {"mean_r": {str(i): 0.4 + 0.001 * k for k, i in enumerate(cort)}}}
    vals = [0.41] * len(labels)
    for e in labrec["entries"]:
        if e["kind"] == "matched" and e["ids"][0] in cort[:2]:
            vals[e["position"]] = None
    spec = plan_of(473)["liu_spec"]
    c = WR.liu_common_comparator(spec, res, dict(labrec, pooled=False), vals, dkt)
    check("S15 the comparator runs on the common labels with the 'n of m' label; T (all m) beside",
          c["status"] == "computed" and c["label"] == WR.SD7_COMMON % (len(cort) - 2, len(cort), 2)
          and c["T_all_labels"] == 0.4 and abs(c["T_sd7_common"] - 0.41) < 1e-12)
    vals2 = [None if (e["kind"] == "matched" and e["ids"][0] in cort) else 0.41 for e in labrec["entries"]]
    c2 = WR.liu_common_comparator(spec, res, dict(labrec, pooled=False), vals2, dkt)
    check("S15 T4's comparator with every cortical value missing: 'not computable (no SD7 value for a cortical "
          "label)' (T4 itself computed)", c2["status"] == WR.SD7_NO_VALUE % "a cortical label" and c2["T_all_labels"] == 0.4)


def SD7_LABELS():
    from a1_audit import wp3_scratch as SC
    return SC.sd7_labels_synthetic()


# ================================================================================================================
# Part B: R50
# ================================================================================================================
def _source_md(path: Path) -> dict:
    out = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) == 3 and len(cells[0]) == 64 and cells[1].isdigit():
            out[cells[2]] = (cells[0], int(cells[1]))
    return out


def part_b() -> None:
    print(SEP + "\nPart B: R50 - the pre-freeze pins and every check before any carrier or request")
    pins = dict(L._pins_production())
    bs = _source_md(REPO / "arcs/audit/results/data_manifests/brainspan_SOURCE.md")
    gb = _source_md(REPO / "arcs/audit/results/data_manifests/gamba_SOURCE.md")
    want = {"brainspan_expr": bs["genes_matrix_csv/expression_matrix.csv"],
            "brainspan_rows": bs["genes_matrix_csv/rows_metadata.csv"],
            "brainspan_cols": bs["genes_matrix_csv/columns_metadata.csv"], "gamba": gb["Background_genes_null_brain.csv"]}
    check("B1 the pins equal the two SOURCE.md files' sha256 and sizes (results/data_manifests, 5e198b7)",
          all((pins[k][2], pins[k][3]) == v for k, v in want.items()), json.dumps({k: pins[k][2:] for k in want}))
    for key in ("brainspan_rows", "brainspan_cols", "brainspan_expr", "gamba"):
        r = make(f"b_{key}")
        pth, _ = r.pin(key)
        bb = bytearray(pth.read_bytes())
        bb[len(bb) // 2] ^= 1
        pth.write_bytes(bytes(bb))
        res, _, calls, _ = stage(r)
        carriers = [str(SCL(r, k)).casefold() for k in (L.SEGURA_MAP_KEY[790618], L.SEGURA_MAP_KEY[781986], L.MOREAU_KEY)]
        touched = [a for a in res["admitted"] if a.casefold() in carriers]
        check(f"B2 {key} one byte off: the stage stops at the preflight - no carrier touched, no network call, no "
              "record, no manifest", res["status"] == L.STATUS_PREFLIGHT and not calls and not touched
              and not list(Path(r.records).rglob("*.json")) and r.latest_manifest() is None)


def SCL(roots, key):
    from a1_audit import wp3_scratch as SC
    return SC.local_path(roots, key)


# ================================================================================================================
# Part M: section 8.1 and R44's identity
# ================================================================================================================
def part_m() -> None:
    print(SEP + "\nPart M: section 8.1 (the Moreau clone) and R44 (identity references, no other copy)")
    import dataclasses as dc
    import hashlib
    r = make("m_main")
    clone = Path(r.moreau_clone)
    (clone / "README.md").write_text("synthetic clone file\n", encoding="utf-8")
    (clone / "data" / "other_table.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    wb = SCL(r, L.MOREAU_KEY)
    wsha = hashlib.sha256(wb.read_bytes()).hexdigest()
    res, text, calls, _ = stage(r)
    e = res["entries"][L.MOREAU_KEY]
    q = Path(r.quarantine) / "ungated" / L.MOREAU_KEY
    moved = list(q.rglob("*"))
    req = json.loads((Path(r.control) / "ungated" / f"{L.MOREAU_KEY}_deletion_request.json").read_bytes())
    check("M1 the clone assertion passes (no other pinned object inside the clone)",
          res["status"] == "final" and "pinned objects inside the clone other than the workbook 0" in text)
    check("M2 after the verified extraction the WHOLE clone directory is moved (same volume) into the quarantine; the "
          "workbook's sha256 re-checked inside it; nothing deleted", e["quarantined"] and not clone.exists()
          and sum(1 for x in moved if x.is_file()) == 3 and any(hashlib.sha256(x.read_bytes()).hexdigest() == wsha
                                                                for x in moved if x.is_file())
          and req["files"][0]["what"].startswith("the whole clone directory"))
    check("M3 the deletion request: working copy and whole clone; other copies by sha256 c947112d...; blob 7a8b62be...; "
          "GitHub @9e8af9c1; the registered materials inside the clone with their surviving copies; the frozen name "
          "screen; the operator's step", all(k in req for k in L.MOREAU_DELETION_REQUEST)
          and "c947112ded237be4" in req["scope"] and "7a8b62be" in req["git_note"]
          and "b2b9dbfb" in req["registered_materials_inside_the_clone"] and "name screen" in req["why"])
    check("M3 the clone's file names are never printed or written",
          not any(s in text for s in ("Supplementary_Table_S1", "other_table", "README"))
          and not any(s in json.dumps(req) for s in ("Supplementary_Table_S1", "other_table")))
    # M4 a pinned object inside the clone stops the stage
    r2 = make("m_planted")
    planted = Path(r2.moreau_clone) / "data" / "planted.csv"
    planted.write_text("x\n", encoding="utf-8")
    rel = os.path.relpath(planted, r2.data).replace("\\", "/")
    r2p = dc.replace(r2, pins=r2.pins + (("planted_inside_clone", (rel, "data", hashlib.sha256(b"x\n").hexdigest(),
                                                                   2)),))
    res2, _, calls2, _ = stage(r2p)
    check("M4 a pinned object planted inside the clone stops the stage before any carrier or request",
          res2["status"] == L.STATUS_PREFLIGHT and not calls2 and r2p.latest_manifest() is None)
    # M5 R44's identity references
    for name, edit in (("remote size differs", lambda rec: rec["probes"][0].update(content_length=rec["probes"][0]
                                                                                   ["content_length"] + 1,
                                                                                   api_file_size=rec["probes"][0]
                                                                                   ["api_file_size"] + 1)),
                       ("metadata size differs", lambda rec: rec["probes"][0].update(api_file_size=rec["probes"][0]
                                                                                     ["api_file_size"] + 1))):
        r3 = make("m_" + name.split()[0])
        doc = json.loads(Path(r3.identity_json).read_bytes())
        rec = [x for x in doc["records"] if x["object"] == L.IDENTITY_OBJECT["segura_790618"]][0]
        edit(rec)
        Path(r3.identity_json).write_text(json.dumps(doc), encoding="utf-8")
        res3, _, _, _ = stage(r3, only=["segura_790618"])
        check(f"M5 (R44) a Segura stand-in whose {name} from the copy's -> 'not auditable (map changed)'",
              res3["entries"]["segura_790618"]["status"] == "not auditable (map changed)")
    r4 = make("m_blob")
    doc = json.loads(Path(r4.identity_json).read_bytes())
    rec = [x for x in doc["records"] if x["object"] == L.IDENTITY_OBJECT[L.MOREAU_KEY]][0]
    rec["probes"][1]["git_blob_sha"] = "0" * 40
    Path(r4.identity_json).write_text(json.dumps(doc), encoding="utf-8")
    res4, _, _, _ = stage(r4, only=[L.MOREAU_KEY])
    check("M5 (R44) a Moreau stand-in whose local git blob differs -> 'not auditable (map changed)'",
          res4["entries"][L.MOREAU_KEY]["status"] == "not auditable (map changed)")
    r5 = make("m_other_path")
    sp = SCL(r5, "segura_790618")
    data = sp.read_bytes()
    os.rename(sp, sp.with_name("renamed_elsewhere.bin"))
    (Path(r5.data) / "segura_790618").mkdir(parents=True, exist_ok=True)
    (Path(r5.data) / "segura_790618" / "carrier.nii.gz").write_bytes(data)
    res5, _, _, _ = stage(r5, only=["segura_790618"])
    adm = [a for a in res5["admitted"] if "renamed_elsewhere" in a or a.endswith("carrier.nii.gz")]
    check("M6 (R44) a copy of the same bytes under another path is not picked up (the pinned path is absent: refused)",
          res5["entries"]["segura_790618"]["status"] == FE.STATUS_FAILED and not adm)


# ================================================================================================================
# Part X: R48 / R49
# ================================================================================================================
def part_x() -> None:
    print(SEP + "\nPart X: R48 / R49 - LIU-T1 / T2* comparator statuses and counts")
    from a1_audit import real_sources as RS
    from a1_audit import wp3_material as WM
    from a1_audit import wp3_repro as WR
    r = make("x_main")
    stage(r)
    src = RS.WP3Sources(r)
    t1 = WR.row_reproduction(plan_of(471), src, {"T": 0.1})
    check("X1 (R48) LIU-T1: both comparators 'not computable (...)' with the amendment's reasons; T reported as T",
          t1["per_sample_r"] == WR.T1_PER_SAMPLE and t1["prenatal_cluster"] == WR.T1_CLUSTER and t1["T"] == 0.1)
    t2 = WR.row_reproduction(plan_of(472), src, {"T": 0.2})
    check("X2 (R49) LIU-T2: 'not computable (...)' with our frontal / thalamus sample counts beside SD4's 164 / 29",
          t2["status"] == WR.T2_FAMILY and t2["group_counts"] == {"frontal cortex": 64, "thalamus": 32}
          and t2["sd4_counts"] == {"frontal cortex": 164, "thalamus": 29})
    tg = WM.targets(r, L.identity_records(r, lambda p: Path(p).read_bytes()))
    lab_t, val_t = WM.sd7_targets(r, ("x",))
    decls = [d for t in list(tg.values()) + [lab_t, val_t] for d in t.sheets]
    check("X3 no target declares an SD3 or SD4 sheet (the only rule-declared sheet is SD7's; the rule selects neither)",
          all(d.mode != "sd7" or d.name_rule == SD.SHEET_RULE.pattern for d in decls)
          and SD.sheet_matches(["Supplementary Data 3", "Supplementary Data 4", "SD3", "SD4"]) == [])


# ================================================================================================================
# Part Z: B6 - no comparator status reaches a row's status
# ================================================================================================================
def part_z() -> None:
    print(SEP + "\nPart Z: B6 - comparator statuses never reach a row's status")
    import ast
    import inspect
    from a1_audit import real_sources as RS
    from a1_audit import wp3_repro as WR
    r = make("z_main")
    stage(r)

    class FakeRun:
        def __init__(self, src, out):
            self.sources, self.results_dir, self.plant_view, self.lines, self.rows = src, out, False, [], []
            self.pass_ = "verdict"

        def header(self):
            return {"what": "test"}

        def provenance(self):
            return {"test": True}

        def log(self, m):
            self.lines.append(m)

        def write_row(self, p, outcome, status, **kw):
            self.rows.append((p["row"], outcome, status))
            return "sha"
    fr = FakeRun(RS.WP3Sources(r), TMP / "z_out")
    orig = WR.row_reproduction
    try:
        WR.row_reproduction = lambda *a, **k: {"status": "not computable (planted comparator status)"}
        sha = R._write_repro(fr, plan_of(1))
    finally:
        WR.row_reproduction = orig
    doc = json.loads((TMP / "z_out" / "row_0001_repro.json").read_text(encoding="utf-8"))
    check("Z1 a comparator's 'not computable (...)' goes to row_<n>_repro.json only; _write_repro never writes a row",
          sha and doc["reproduction"]["status"].startswith("not computable") and fr.rows == [])
    tree = ast.parse(inspect.getsource(R))
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "_write_repro"]
    parents = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            parents[c] = n
    check(f"Z2 every call of _write_repro in run.py discards its value ({len(calls)} calls; none feeds write_row or a "
          "status)", calls and all(isinstance(parents[c], ast.Expr) for c in calls))
    src_write = inspect.getsource(R._write_repro)
    check("Z3 _write_repro writes its own file only (no write_row, no status composition)",
          "write_row" not in src_write and "row_{p['row']:04d}_repro.json" in src_write)


def real_root_expected_status():
    """The real root's phase-2 state (fix round 5: phase 2 ran at 61b443f and ended partial): no manifest -> 'pending';
    only partial manifests -> 'not final'; a final manifest -> None (the real dry dispatch is then not a test's: it
    would read real phase-2 objects)."""
    rp = L.Roots.production()
    if rp.latest_manifest() is not None:
        return None
    return L.STATUS_NOT_FINAL if rp.partial_manifests() else L.STATUS_PENDING


# ================================================================================================================
# Part N: the dry dispatch
# ================================================================================================================
def part_n() -> dict:
    print(SEP + "\nPart N: the dry dispatch of the 115 ungated rows")
    from a1_audit import real_sources as RS
    out = {}
    want = real_root_expected_status()
    if not ARGS.skip_real_dry and want is None:
        print("  N1 not run: the real root has a final phase-2 manifest (its dry dispatch reads real objects)")
    elif not ARGS.skip_real_dry:
        src = RS.WP3Sources(L.Roots.production())
        c = RS.dry_counts(src)
        recs = c.pop("_records")
        out["real"] = c
        comp = [x for x in recs if x["outcome"] in ("would compute", "not run")]
        check(f"N1 real root (phase-2 state: {'partial manifest' if want == L.STATUS_NOT_FINAL else 'no manifest'}): "
              f"115 rows; 90 computing rows all '{want}'; 25 no statistic",
              c["n_rows"] == 115 and len(comp) == 90 and all(x["status"] == want for x in comp)
              and c["by_outcome"].get("no statistic") == 25, json.dumps(c["by_outcome"]))
    r = make("n_main")
    stage(r)
    c = RS.dry_counts(RS.WP3Sources(r))
    c.pop("_records")
    out["scratch"] = c
    check("N2 scratch stand-ins after the stage: every one of the 90 computing rows 'would compute'",
          c["by_outcome"].get("would compute") == 90 and c["by_outcome"].get("no statistic") == 25,
          json.dumps(c["by_outcome"]))
    print("  dry counts: " + json.dumps({k: v["by_outcome"] for k, v in out.items()}))
    return out


# ================================================================================================================
# Part Q: fix round 3 (the reviewer's re-check of ca28e2f; its x7-x11 as regression cases)
# ================================================================================================================
def _child3(mode: str, roots_json: Path, order: str) -> tuple:
    cp = subprocess.run([sys.executable, "-X", "utf8", "-m", "a1_audit.tests.wp3_child", mode, str(roots_json), order],
                        capture_output=True, cwd=str(REPO / "arcs/audit/src"), timeout=1800)
    out = cp.stdout.decode("utf-8", "replace")
    err = cp.stderr.decode("utf-8", "replace")
    res = [ln for ln in out.splitlines() if ln.startswith("RESULT ")]
    return cp.returncode, out, err, (json.loads(res[-1][7:]) if res else None)


def _norm_ws(t: str) -> str:
    return " ".join(t.split())


def part_q() -> dict:
    print(SEP + "\nPart Q: fix round 3 - the read-back guarded (A1), Part B's missing preflight cases (A2), SD7 step 6 "
                "(B1), the size probe's status (B2), decided once across runs (B3), C (a)-(i)")
    import contextlib
    import dataclasses as dc
    import hashlib
    from a1_audit import privacy_wrap as PW
    from a1_audit import real_sources as RS
    from a1_audit import reparcel as RP
    from a1_audit import wp3_decoder as DC
    from a1_audit import wp3_material as WM
    from a1_audit import wp3_repro as WR
    from a1_audit import wp3_scratch as SC
    from a1_audit import wp3_scratch_pdf as SPDF
    ev = {}
    # ---- A1: the read-back inside the guards (the reviewer's x7: pdfminer logs a planted operand while it parses)
    r = SPDF.plant_tf_operand(make("q_x7"), b"NDARINVAB123CDE")
    errbuf = io.StringIO()
    with contextlib.redirect_stderr(errbuf):
        res, text, _, _ = stage(r)
    e = res["entries"][L.MOESM2_KEY]
    check("Q1 (A1) the pdfminer-logging MOESM2 stand-in: the stage finishes (final); the read-back passes inside the "
          "guards with pdfminer's warning COUNTED (logging), nothing written to stderr, the operand never printed",
          res["status"] == "final" and e["readback"] == "pass" and errbuf.getvalue() == ""
          and (e.get("readback_guard") or {}).get("logging", {}).get("WARNING", 0) >= 1
          and "NDARINVAB123CDE" not in text, json.dumps({k: e.get(k) for k in ("readback", "readback_guard")}))
    for order in ("preimport", "lazy"):
        rr = SPDF.plant_tf_operand(make(f"q_x7_{order}"), b"NDARINVAB123CDE")
        rj = TMP / f"q_x7_{order}_roots.json"
        rj.write_text(json.dumps(rr.to_spec()), encoding="utf-8")
        code, out, err, rres = _child3("stage", rj, order)
        ev[f"moesm2 read-back, {order}"] = dict(exit=code, stderr_bytes=len(err),
                                                result=(rres or {}).get(L.MOESM2_KEY))
        m = (rres or {}).get(L.MOESM2_KEY) or {}
        check(f"Q2 (A1) REAL stderr ({order}: pdfminer / pdfplumber "
              f"{'imported before the stage' if order == 'preimport' else 'first imported inside it'}): the stage in a "
              "subprocess, first parse and read-back both guarded - exit 0, stderr 0 "
              "bytes, pdfminer's warnings counted in the record and the read-back's guard",
              code == 0 and err == "" and m.get("readback") == "pass" and (m.get("readback_logging") or {}).get(
                  "WARNING", 0) >= 1 and (m.get("first_parse_logging") or {}).get("WARNING", 0) >= 1
              and m.get("readback_stdio_violations") == 0 and "NDARINVAB123CDE" not in out,
              json.dumps(ev[f"moesm2 read-back, {order}"])[:300])
    r = make("q_rb_raise")
    orig = WPDF_readback = __import__("a1_audit.wp3_pdf", fromlist=["readback"])
    try:
        def boom(*a, **k):
            raise RuntimeError(r"E:\data\asdg\register_sets_src\NDARINVAB123CDE.pdf")
        orig.readback, saved = boom, orig.readback
        res, text, _, _ = stage(r)
    finally:
        orig.readback = saved
    e = res["entries"][L.MOESM2_KEY]
    man = Path(res["manifest_path"]).read_text(encoding="utf-8") if res.get("manifest_path") else ""
    res2, _, _, _ = stage(r)
    check("Q3 (A1) a read-back that raises: 'refused' (final; stage, class, line only), the message never printed or "
          "written; the stage finishes, and the next run is a no-op",
          res["status"] == "final" and e["readback"] == "refused" and e["status"] == WM.STATUS_READBACK_REFUSED
          and e["readback_failure"]["class"] == "RuntimeError" and e["readback_failure"]["stage"] == "read-back"
          and "NDARINVAB123CDE" not in text and "NDARINVAB123CDE" not in man and res2.get("noop") is True)
    _ = WPDF_readback
    # ---- A2: the preflight's builds chain, Table S4's raw list and the DK info pin (the reviewer's x11)
    for tag in ("s4raw", "build", "dk_info"):
        r = make(f"q_x11_{tag}")
        if tag == "s4raw":
            pth, _ = r.pin("segura_s4_raw")
            b = bytearray(pth.read_bytes())
            b[-2] ^= 1
            pth.write_bytes(bytes(b))
        elif tag == "build":
            bd = Path(r.builds) / "perdonor-aal"
            rec = json.loads((bd / "build_record.json").read_bytes())
            pth = bd / [o for o in rec["outputs"] if o["role"] == "counts"][0]["file"]
            b = bytearray(pth.read_bytes())
            b[-2] ^= 1
            pth.write_bytes(bytes(b))
        else:                                  # the DK info is the repository's file: its pin is changed instead
            r = dc.replace(r, pins=tuple((k, (v[0], v[1], "0" * 64) + tuple(v[3:]) if k == "dk_info" else v)
                                         for k, v in r.pins))
        try:
            res, _, calls, _ = stage(r)
        except Exception as ex:  # noqa: BLE001  (a stage that does not stop at the preflight fails this check)
            res, calls = {"status": f"raised {type(ex).__name__}"}, ["?"]
        check(f"Q4 (A2) {tag} off its pin: the preflight stops the stage - no carrier, no request, no record, no "
              "manifest, the clone in place", res["status"] == L.STATUS_PREFLIGHT and not calls
              and not (Path(r.records).exists() and list(Path(r.records).rglob("*.json")))
              and r.latest_manifest() is None and Path(r.moreau_clone).exists())
    # ---- B1: step 6 once after the last pass attempted (the reviewer's x8)
    base = make("q_x8")
    for tag, variant, how in (("ns", "identifier+ns", "refused"), ("rownumbers", "identifier+rownumbers", "skipped"),
                              ("clean", "identifier", "extracted")):
        rv, outv, textv, pv = _sd7_run(base, variant, f"q_x8_{tag}")
        q = Path(rv.quarantine)
        nq = sum(1 for x in q.rglob("*") if x.is_file()) if q.exists() else 0
        reqs = list((Path(rv.control) / "ungated").glob("*deletion_request.json")) if (Path(rv.control) / "ungated").exists() else []
        s6 = outv.get("liu_sd7_step6")
        ok = not pv.exists() and nq == 1 and len(reqs) == 1 and "NDAR_INVAB123CDE" not in textv
        if how == "extracted":
            ok = ok and s6 is None and outv["liu_sd7_values"]["quarantined"]
        else:
            ok = ok and s6 is not None and s6["status"] == FE.STATUS_STEP6 and s6["quarantined"] and s6["final"]
        rv2_out = WM.run_sd7(rv, WM.Door(rv), PW.Emitter(WM._allow(rv), stream=io.StringIO()), io.StringIO(),
                             lambda k: True)
        nq2 = sum(1 for x in q.rglob("*") if x.is_file())
        check(f"Q5 (B1) an identifier-bearing SD7 whose pass 2 is {how}: step 6 runs ONCE after the last pass "
              f"({'pass 2 itself' if how == 'extracted' else 'its own record, liu_sd7_step6'}): the copy moved, one "
              "deletion request; a re-run adopts it (no second move)", ok and nq2 == 1
              and (how == "extracted" or rv2_out["liu_sd7_step6"]["status"] == FE.STATUS_STEP6),
              json.dumps({"files_in_quarantine": nq, "requests": len(reqs), "step6": (s6 or {}).get("status")}))
    # ---- B2: a 503 to the size probe is 'no size returned' (the reviewer's x9)
    r = make("q_x9")
    res, text, calls, _ = stage(r, head_status={781986: 503}, head_sizes={781986: 162})
    st = json.loads((Path(r.control) / "ungated" / "segura_decoder_781986_attempt1.json").read_bytes())
    res2, _, calls2, _ = stage(r)
    check("Q6 (B2) the size probe answered 503 (with a 162-byte body): 'no size returned' - the GET proceeds (extracted); "
          "the start record keeps the status code; never a size mismatch",
          res["entries"]["segura_decoder_781986"]["status"] == FE.STATUS_EXTRACTED and n_get(calls, 781986) == 1
          and st["size_probe"]["status_code"] == 503 and st["size_probe"]["result"] == ID_NOT_EST
          and st["size_probe"]["reading"] == DC.NO_SIZE and res2.get("noop") is True)
    # ---- B3: a recorded size mismatch decides a later run with no manifest (the reviewer's x10)
    r = make("q_x10")
    u = urls(r)
    res, _, _, _ = stage(r, head_sizes={781986: 99999})
    mp = Path(res["manifest_path"])
    os.rename(mp, mp.with_name("moved_aside_manifest.bin"))       # the operator's step in the reviewer's scenario
    res2, _, calls2, _ = stage(r)
    dec = L.DECODER_URL.format(image=781986)
    f781 = [f for f, i in u["files"].items() if i == 781986][0]
    check("Q7 (B3) a size mismatch recorded in run 1 decides run 2 (its manifest moved aside): no HEAD and no GET for "
          "781986; unavailable (size mismatch)",
          res["entries"]["segura_decoder_781986"]["status"] == DC.UNAVAILABLE % DC.OUT_SIZE
          and res2["entries"]["segura_decoder_781986"]["status"] == DC.UNAVAILABLE % DC.OUT_SIZE
          and not [c for c in calls2 if c[1] in (dec, f781)])
    # ---- C (a): the decoder record says no HEAD was made
    rec = json.loads((Path(r.records) / "ungated" / "segura_decoder_790618.json").read_bytes())
    check("Q8 (C (a)) the decoder's R18 record: no HEAD of the decoder URL (one GET)",
          rec["server"].get("head") == FE.HEAD_NOT_MADE)
    # ---- C (b): guarded keeps an inner status
    src = RS.WP3Sources(make("q_guard"))

    def inner_su():
        raise R.SourceUnavailable(L.STATUS_MAP_CHANGED, "inner")

    def inner_rr():
        raise RP.ReparcelRefused(L.STATUS_MAP_CHANGED)

    def inner_rt():
        raise RuntimeError("x")
    check("Q9 (C (b)) WP3Sources.guarded re-raises an inner SourceUnavailable / ReparcelRefused with its own status "
          "(section 17's 'not auditable (map changed)' survives); any other exception reads the handler's status",
          raises(lambda: src.guarded("read:file", inner_su), R.SourceUnavailable, "status", L.STATUS_MAP_CHANGED)
          and raises(lambda: src.guarded("read:file", inner_rr), R.SourceUnavailable, "status", L.STATUS_MAP_CHANGED)
          and raises(lambda: src.guarded("read:file", inner_rt), R.SourceUnavailable, "status", L.STATUS_USE_FAILED))
    # ---- C (c): pdfplumber at another version stops the stage (no final record)
    import pdfplumber
    r = make("q_env")
    old = pdfplumber.__version__
    try:
        pdfplumber.__version__ = "0.11.9"
        res, _, calls, _ = stage(r)
    finally:
        pdfplumber.__version__ = old
    nrec = len(list(Path(r.records).rglob("*.json"))) if Path(r.records).exists() else 0
    res2, _, _, _ = stage(r)
    check("Q10 (C (c)) pdfplumber at another version: the stage stops for the operator before any carrier (no record, no "
          "request, no manifest); restored, the next run completes", res.get("stopped") and res["status"] == WM.STOP_PDF_ENV
          and nrec == 0 and not calls and r.latest_manifest() is not None and res2["status"] == "final")
    r = make("q_env_rb")
    mod = __import__("a1_audit.wp3_pdf", fromlist=["readback"])
    saved = mod.readback
    try:
        def env(*a, **k):
            raise mod.PdfEnvironmentFault("version")
        mod.readback = env
        res, _, _, _ = stage(r)
    finally:
        mod.readback = saved
    check("Q10 (C (c)) an environment fault met at the read-back also stops the stage (no manifest, no final record of "
          "the read-back)", res.get("stopped") and res["status"] == WM.STOP_PDF_ENV and r.latest_manifest() is None)
    # ---- C (d): the frozen amend_3 texts verbatim
    a3 = _norm_ws((REPO / "arcs/audit/RUN_PLAN_amend_3.md").read_text(encoding="utf-8"))
    from a1_audit import forms as FMq
    texts = {"T1_PER_SAMPLE": WR.T1_PER_SAMPLE, "T1_CLUSTER": WR.T1_CLUSTER, "T2_FAMILY": WR.T2_FAMILY,
             "MOESM2_CHANGED": WR.MOESM2_CHANGED, "SD7_SHEET": SD.SD7_SHEET, "SD7_HEADER": SD.SD7_HEADER,
             "SD7_INTERRUPTED": SD.SD7_INTERRUPTED, "SD7_NON_NUMERIC": SD.SD7_NON_NUMERIC,
             "SD7_UNMATCHED": FMq.SD7_UNMATCHED, "S7_NOT": WR.S7_NOT.split("%s")[0].rstrip(),
             "S6_NOT": WR.S6_NOT.split("%s")[0].rstrip()}
    missing = [k for k, v in texts.items() if _norm_ws(v) not in a3]
    fr = make("q_text")
    stage(fr)

    class FakeRun:
        def __init__(self, s, o):
            self.sources, self.results_dir, self.plant_view, self.pass_ = s, o, False, "verdict"

        def header(self):
            return {}

        def provenance(self):
            return {}

        def log(self, m):
            pass
    R._write_repro(FakeRun(RS.WP3Sources(fr), TMP / "q_text_out"), plan_of(471), {"T": 0.1})
    raw = (TMP / "q_text_out" / "row_0471_repro.json").read_bytes()
    check("Q11 (C (d)) the frozen amend_3 status texts verbatim (R46-R49; whitespace aside) and the R48 record written "
          "with a UTF-8 '\\u00a78'", not missing and "\u00a78)".encode("utf-8") in raw and b"section 8)" not in raw,
          json.dumps(missing))
    # ---- C (e): MOESM2's record names "no URL registered"
    mrec = json.loads((Path(fr.records) / "ungated" / f"{L.MOESM2_KEY}.json").read_bytes())
    check("Q12 (C (e)) MOESM2's record: the placeholder URL with 'no URL registered' beside it",
          mrec["url"] == L.MOESM2_URL and mrec.get("url_note") == L.MOESM2_URL_NOTE
          and mrec["url_note"].startswith("no URL registered"))
    # ---- C (f): the fallback only on 'unavailable'
    mp = fr.latest_manifest()
    mb = mp.read_bytes()
    man = json.loads(mb)
    man["objects"]["segura_decoder_790618"] = {"status": FE.STATUS_FAILED, "final": True}
    try:
        mp.write_bytes(json.dumps(man, indent=1).encode("utf-8"))
        bad = raises(lambda: WR.SeguraContext(RS.WP3Sources(fr)).decoded(790618, lambda: {}), R.SourceUnavailable,
                     "status", L.STATUS_STAGE_REFUSED % FE.STATUS_FAILED)
    finally:
        mp.write_bytes(mb)
    check("Q13 (C (f)) a decoder entry neither extracted nor 'unavailable' is refused, never the fallback", bad)
    # ---- C (g): an empty SD7 block
    rve, oute, _, _ = _sd7_run(base, "empty_block", "q_empty")
    check("Q14 (C (g); fix round 4, item 2) an empty SD7 block is not 'interrupted': it reads R42 (d)'s frozen 'SD7 "
          "labels unmatched'", oute[L.SD7_KEY]["status"] == FMq.SD7_UNMATCHED != SD.SD7_INTERRUPTED)
    # ---- C (h): only pages 37 and 38 get pdfplumber Page objects
    import pdfplumber.page as PPG
    n_pages = []
    orig_init = PPG.Page.__init__

    def counting(self, *a, **k):
        n_pages.append(k.get("page_number"))
        return orig_init(self, *a, **k)
    pth, _ = fr.pin("segura_moesm2")
    inputs = WM.moesm2_inputs(fr, WM.Door(fr))
    try:
        PPG.Page.__init__ = counting
        got = __import__("a1_audit.wp3_pdf", fromlist=["parse"]).parse(pth, **inputs)
    finally:
        PPG.Page.__init__ = orig_init
    check("Q15 (C (h)) pdfplumber builds Page objects for pages 38 and 39 only (indexes 37, 38); the page-tree walk "
          "recorded as a declared residual", set(n_pages) == {38, 39}
          and got["pages_opened"]["page_numbers"] == [38, 39] and "residual" in got["pages_opened"]["residual"])
    # ---- C (i): the reviewer's surviving N2, N3, N10
    for name, plant in (("a plain carrier.json.part", "plain"), ("an outcome record without its start record", "outcome")):
        r = make(f"q_trace_{plant}")
        kd = Path(r.data) / "segura_decoder_790618"
        kd.mkdir(parents=True, exist_ok=True)
        if plant == "plain":
            (kd / "carrier.json.part").write_bytes(b"{")
        else:
            c = Path(r.control) / "ungated"
            c.mkdir(parents=True, exist_ok=True)
            (c / "segura_decoder_790618_attempt1_outcome.json").write_text(json.dumps({"k": 1}), encoding="utf-8")
        resx, _, callsx, _ = stage(r)
        check(f"Q16 (C (i)) a crash trace stops the stage: {name} (no GET of that image, no manifest)",
              resx.get("stopped") and resx["status"] == DC.STOP_TRACE and n_get(callsx, 790618) == 0
              and r.latest_manifest() is None)
    # A1 audit: the decoder's hashing of an earlier attempt's .part runs inside the guards (a locked file: a stop)
    import msvcrt
    r = make("q_hash")
    stage(r, only=["segura_decoder_790618"], script={790618: [("curl", 28)]}, partial_on_fail=True)
    pp = Path(r.data) / "segura_decoder_790618" / "carrier.json.a1.part"
    fh = open(pp, "rb+")
    errbuf = io.StringIO()
    try:
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, pp.stat().st_size)
        with contextlib.redirect_stderr(errbuf):
            resh, texth, _, _ = stage(r)
    finally:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, pp.stat().st_size)
        fh.close()
    check("Q17 (A1 audit) an earlier attempt's .part locked by another process: hashing it inside the guards stops the "
          "stage for the operator (no traceback, nothing on stderr, no manifest)", resh.get("stopped")
          and resh["status"] == DC.STOP_HASH and errbuf.getvalue() == "" and "Traceback" not in texth)
    r = make("q_hash_carrier")
    stage(r, only=["segura_decoder_790618"])
    cj = Path(r.data) / "segura_decoder_790618" / "carrier.json"
    fh = open(cj, "rb+")
    errbuf = io.StringIO()
    try:
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, cj.stat().st_size)
        with contextlib.redirect_stderr(errbuf):
            resc, textc, _, _ = stage(r)
    finally:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, cj.stat().st_size)
        fh.close()
    check("Q17 (A1 audit) the decoder's carrier.json locked at the SOURCE.md check: hashed inside the guards, the stage "
          "stops for the operator (no traceback, nothing on stderr)", resc.get("stopped")
          and resc["status"] == DC.STOP_HASH and errbuf.getvalue() == "" and "Traceback" not in textc)
    r = make("q_clone_count")
    orig_rename = os.rename

    def rename(a, b):
        orig_rename(a, b)
        if Path(b).is_dir() and Path(b).name == L.MOREAU_KEY:
            (Path(b) / "appeared_during_the_move.txt").write_text("x", encoding="utf-8")
    try:
        os.rename = rename
        res, _, _, _ = stage(r, only=[L.MOREAU_KEY])
    finally:
        os.rename = orig_rename
    mrec = [json.loads(p.read_bytes()) for p in sorted((Path(r.records) / "ungated").glob(f"{L.MOREAU_KEY}*.json"))][-1]
    check("Q16 (C (i)) the whole-clone move re-checks the number of files moved: a file count that changes across the "
          "move refuses the quarantine step", mrec.get("failed_stage") == "quarantine"
          and mrec.get("failed_class") == "QuarantineRefused")
    return ev


ID_NOT_EST = "identity not established (reference missing)"


# ================================================================================================================
# Part F4: fix round 4 (the reviewer's residues on 5b14f40)
# ================================================================================================================
def _sd7_layout(roots, variant, tag):
    """An SD7 variant workbook with its own output tree (as _sd7_run) - the layout only, nothing run."""
    import dataclasses as dc
    import hashlib
    from a1_audit import wp3_scratch as SC
    xb = SC.synthetic_sd7_book(np.random.default_rng(5), variant)
    d = TMP / f"sd7_{tag}"
    p = d / "data" / "liu" / "supplement_syn.xlsx"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(xb)
    rv = dc.replace(roots, sd7_copy=(str(p), hashlib.sha256(xb).hexdigest(), len(xb), "https://example.org/syn.xlsx"),
                    records=str(d / "out/records"), artifacts=str(d / "out/artifacts"), control=str(d / "out/control"),
                    logs=str(d / "out/logs"), data=str(d / "data"), quarantine=str(d / "data/_quarantine"))
    return rv, p


def _run_sd7(rv, want):
    from a1_audit import privacy_wrap as PW
    from a1_audit import wp3_material as WM
    buf = io.StringIO()
    return WM.run_sd7(rv, WM.Door(rv), PW.Emitter(WM._allow(rv), stream=buf), buf, want), buf.getvalue()


def part_f4() -> None:
    print(SEP + "\nPart F4: fix round 4 - step 6's identity re-check, the empty block, the read-back's incident, an html "
                "HEAD, step 6's quarantine-path refusal, the per-donor matrices at use")
    import contextlib
    import dataclasses as dc
    from a1_audit import ahba_builds as AB
    from a1_audit import forms as FM4
    from a1_audit import real_sources as RS
    from a1_audit import wp3_decoder as DC
    from a1_audit import wp3_material as WM
    from a1_audit import wp3_repro as WR
    base = make("f4_base")
    # ---- item 1: run_step6's identity re-check, both branches
    rv, p = _sd7_layout(base, "identifier+ns", "f4_step6_match")
    out1, _ = _run_sd7(rv, lambda k: k != "liu_sd7_step6")            # passes 1 and 2; step 6 not yet
    pending = out1.get("liu_sd7_step6", {}).get("status") == L.STATUS_PENDING and p.exists()
    out2, _ = _run_sd7(rv, lambda k: True)                               # step 6 now: the copy unchanged
    s6 = out2["liu_sd7_step6"]
    check("F4-1a (item 1) step 6 later, the copy unchanged: identity re-checked 'identity match', then moved (one "
          "deletion request)", pending and s6["status"] == FE.STATUS_STEP6 and s6["identity_result"] == "identity match"
          and not p.exists())
    rv, p = _sd7_layout(base, "identifier+ns", "f4_step6_changed")
    _run_sd7(rv, lambda k: k != "liu_sd7_step6")
    b = bytearray(p.read_bytes())
    b[len(b) // 2] ^= 1
    p.write_bytes(bytes(b))                                              # the copy changes between the passes and step 6
    out3, _ = _run_sd7(rv, lambda k: True)
    s6 = out3["liu_sd7_step6"]
    q = Path(rv.quarantine)
    reqs = list((Path(rv.control) / "ungated").glob("*deletion_request.json")) if (Path(rv.control) / "ungated").exists() else []
    out4, _ = _run_sd7(rv, lambda k: True)
    check("F4-1b (item 1) the copy changed after the passes: step 6's identity re-check reads 'not auditable (map "
          "changed)' - final, NOT moved, no deletion request; a re-run adopts it", s6["status"] == "not auditable (map changed)"
          and s6["final"] and p.exists() and not (q.exists() and any(x.is_file() for x in q.rglob("*"))) and not reqs
          and out4["liu_sd7_step6"]["status"] == "not auditable (map changed)")
    # ---- item 2: an empty block is R42 (d)'s frozen 'labels unmatched', with a count
    rv, p = _sd7_layout(base, "empty_block", "f4_empty")
    oute, _ = _run_sd7(rv, lambda k: True)
    rp = oute["liu_sd7_labels"].get("record_path")
    rec = json.loads((Path(rv.records) / rp).read_bytes()) if rp else {}
    check("F4-2 (item 2) an empty SD7 block reads R42 (d)'s frozen 'SD7 labels unmatched' (fail closed; no new status); "
          "the record counts the block as empty", oute[L.SD7_KEY]["status"] == FM4.SD7_UNMATCHED
          and rec["status"] == FM4.SD7_UNMATCHED and rec.get("sd7_counts", {}).get("block_empty") is True
          and not hasattr(SD, "SD7_EMPTY"))
    # ---- item 3: a stdio violation inside the read-back reads as run_target's incident
    r = make("f4_rb_stdio")
    mod = __import__("a1_audit.wp3_pdf", fromlist=["readback"])
    saved = mod.readback
    try:
        def noisy(*a, **k):
            print("a library line naming NDARINVAB123CDE")
            return saved(*a, **k)
        mod.readback = noisy
        res, text, _, _ = stage(r)
    finally:
        mod.readback = saved
    e = res["entries"][L.MOESM2_KEY]
    check("F4-3 (item 3) a line off the allow-list inside the read-back: 'stopped (print-rule violation; ETHICS_PRIVACY "
          "incident)' exactly as run_target reads it (not 'refused'); not final (the manifest is partial); the line never "
          "shown", e["status"] == FE.STATUS_INCIDENT == "stopped (print-rule violation; ETHICS_PRIVACY incident)"
          and e["readback"] == "stopped" and e["final"] is False and res["status"] == "partial"
          and "NDARINVAB123CDE" not in text)
    # ---- item 4: a 200 HTML page to the size-probe HEAD
    r = make("f4_html")
    res, text, calls, _ = stage(r, head_html=(781986,), head_sizes={781986: 162})
    st = json.loads((Path(r.control) / "ungated" / "segura_decoder_781986_attempt1.json").read_bytes())
    check("F4-4 (item 4) a 200 whose Content-Type is text/html (a challenge / error page, 162 bytes): 'no size returned' - "
          "the GET proceeds (extracted); the record keeps the status and the content-type label",
          res["entries"]["segura_decoder_781986"]["status"] == FE.STATUS_EXTRACTED and n_get(calls, 781986) == 1
          and st["size_probe"]["status_code"] == 200 and st["size_probe"]["content_type_label"] == FE.CONTENT_TYPE_HTML
          and st["size_probe"]["result"] == ID_NOT_EST)
    # ---- item 5: run_step6's quarantine-path refusal is a record
    rv, p = _sd7_layout(base, "identifier+ns", "f4_qpath")
    planted = Path(rv.quarantine) / "ungated" / "elsewhere" / "copy.xlsx"
    planted.parent.mkdir(parents=True, exist_ok=True)
    planted.write_bytes(p.read_bytes())
    import pandas as pd
    lab_t, _ = WM.sd7_targets(rv, tuple(sorted(set(str(x) for x in pd.read_csv(REPO / "artifacts/ahba/dk_atlas_info.csv")
                                                   ["label"]))))
    t6 = dc.replace(lab_t, key="liu_sd7_step6", sheets=(), defer_quarantine=False, local_path=str(planted))
    try:
        r6 = FE.run_step6(t6, rv.fe_roots(), reason=WM.STATUS_STEP6_REASON, out=io.StringIO())
        rec6 = json.loads(Path(r6["record_path"]).read_bytes())
        ok5 = r6["status"] == FE.STATUS_FAILED and rec6["failed_stage"] == "quarantine" and planted.exists()
    except Exception:  # noqa: BLE001
        ok5 = False
    check("F4-5 (item 5) run_step6 on a copy under the quarantine: the refusal is a stage failure with its record "
          "(failed_stage quarantine), not a stop; nothing moved", ok5)
    # ---- item 6: the per-donor V-AAL matrices at use, guarded; a donor-id-shaped file name never emitted
    r = make("f4_donor")
    bd = Path(r.builds) / "perdonor-aal"
    rec = json.loads((bd / "build_record.json").read_bytes())
    donor = str(AB.DONORS[0])
    planted_name = f"aal_donor-{donor}_expr.csv.gz"
    o1 = [o for o in rec["outputs"] if str(o.get("donor")) == donor][0]
    os.rename(bd / o1["file"], bd / planted_name)
    o1["file"] = planted_name
    rb = json.dumps(rec, indent=1).encode("utf-8")
    (bd / "build_record.json").write_bytes(rb)
    man = json.loads((Path(r.builds) / "MANIFEST.json").read_bytes())
    man["builds"]["perdonor-aal"]["record_sha256"] = hashlib_sha(rb)
    (Path(r.builds) / "MANIFEST.json").write_bytes(json.dumps(man, indent=1).encode("utf-8"))
    errbuf = io.StringIO()
    emitted = []
    with contextlib.redirect_stderr(errbuf):
        res, text, _, _ = stage(r, script={790618: ["bad_columns"]})          # decoder unavailable: the fallback
        emitted.append(text)
        src = RS.WP3Sources(r)
        rr = WR.row_reproduction(plan_of(1), src)                              # reads the six per-donor matrices
        emitted.append(json.dumps(rr))
        emitted += src.stage_lines

        class FakeRun:
            def __init__(self, s, o):
                self.sources, self.results_dir, self.plant_view, self.pass_ = s, o, False, "verdict"

            def header(self):
                return {}

            def provenance(self):
                return {}

            def log(self, m):
                emitted.append(m)
        R._write_repro(FakeRun(RS.WP3Sources(r), TMP / "f4_donor_out"), plan_of(1))
        # at use: the planted per-donor file locked by another process -> a status from section 8's handler
        import msvcrt
        fp = bd / planted_name
        fh = open(fp, "rb+")
        try:
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, fp.stat().st_size)
            src2 = RS.WP3Sources(r)
            try:
                src2.perdonor_aal()
                locked = "ACCEPTED"
            except R.SourceUnavailable as ex:
                locked = ex.status
                emitted += [ex.status, ex.what]
            except Exception as ex:  # noqa: BLE001
                locked = f"UNCAUGHT {type(ex).__name__}"
            emitted += src2.stage_lines
        finally:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, fp.stat().st_size)
            fh.close()
    emitted.append(errbuf.getvalue())
    for f in list((Path(r.data).parent / "out").rglob("*")) + list((TMP / "f4_donor_out").rglob("*")):
        if f.is_file() and f.suffix in (".json", ".log", ".md", ".txt"):
            emitted.append(f.read_text(encoding="utf-8", errors="replace"))
    leak = [s for s in emitted if planted_name in s or f"donor-{donor}" in s]
    check("F4-6 (item 6) the per-donor V-AAL matrices read at use through guarded: a per-donor file locked at use reads "
          "'not run (identity at use not established ...)' - no exception escapes", locked == L.STATUS_USE_UNREADABLE,
          locked)
    check("F4-6 (item 6) a donor-id-shaped per-donor file name planted in a scratch build never appears in any output, "
          "record, log, manifest, reproduction record, stage line, exception text or stderr of WP3",
          not leak and rr["decoded_list"].get("label") == WR.R22_FALLBACK_LABEL and errbuf.getvalue() == "",
          f"{len(leak)} leak(s)")


# ================================================================================================================
# Part F5: fix round 5 - the whole-directory SOURCE.md line and the resume of a crashed step 6
# ================================================================================================================
PARENT_61B = "61b443f"           # the commit phase 2 ran at (the KeyError at fetch_extract.py:1424)
F5_SOURCE_MD = "# SOURCE (synthetic stand-in beside the clone)\n- fetched: synthetic\n"


def parent_function(name: str, commit: str = PARENT_61B):
    """`name` of fetch_extract.py at `commit` (git show), compiled under fetch_extract.py's file name with its own line
    numbers (so the stage handler records the parent's 'fetch_extract.py:<n>'), bound to the current module's names."""
    cp = subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:arcs/audit/src/a1_audit/fetch_extract.py"],
                        capture_output=True, check=True)
    lines = cp.stdout.decode("utf-8").splitlines(keepends=True)
    i = next(k for k, ln in enumerate(lines) if ln.startswith(f"def {name}("))
    j = next(k for k in range(i + 1, len(lines)) if lines[k].strip() and not lines[k][0].isspace())
    ns = FE.__dict__
    saved = ns.get(name)
    exec(compile("\n" * i + "".join(lines[i:j]), FE.__file__, "exec"), ns)
    fn = ns[name]
    ns[name] = saved
    return fn


def _f5_layout(name: str):
    r = make(name)
    src = Path(r.data) / L.MOREAU_KEY / "SOURCE.md"                     # beside the clone (data/<key>/repo)
    src.write_bytes(F5_SOURCE_MD.encode("utf-8"))
    return r, src


def _f5_crash(r, *, only=None):
    """The 61b443f phase-2 run on this layout: the parent's _quarantine (the KeyError on a whole-directory move)."""
    old = FE._quarantine
    FE._quarantine = parent_function("_quarantine")
    try:
        return stage(r, only=only)
    finally:
        FE._quarantine = old


def _f5_state(r) -> dict:
    """What the resume may change, read back (scratch stand-ins only)."""
    from a1_audit import wp3_material as WM
    q = Path(r.quarantine) / "ungated" / L.MOREAU_KEY
    rq = Path(r.control) / "ungated" / f"{L.MOREAU_KEY}_deletion_request.json"
    recs = WM.records_of(r, L.MOREAU_KEY)
    src = Path(r.data) / L.MOREAU_KEY / "SOURCE.md"
    obj = Path(r.artifacts) / "ungated" / L.MOREAU_KEY
    return {"records": [(x[0].name, hashlib_sha(x[2])) for x in recs],
            "quarantine": sorted((x.relative_to(q).as_posix(), hashlib_sha(x.read_bytes())) for x in q.rglob("*")
                                 if x.is_file()) if q.is_dir() else None,
            "clone_back": Path(r.moreau_clone).exists(),
            "request": hashlib_sha(rq.read_bytes()) if rq.is_file() else None,
            "source_md": hashlib_sha(src.read_bytes()) if src.is_file() else None,
            "objects": sorted((x.name, hashlib_sha(x.read_bytes())) for x in obj.rglob("*") if x.is_file())
            if obj.is_dir() else None,
            "completion": WM.completion_path(r, L.MOREAU_KEY).exists(),
            "partials": len(r.partial_manifests()), "final": r.latest_manifest() is not None}


def _f5_line_rx(r, wsha: str, n_files: int):
    import re
    q = (Path(r.quarantine) / "ungated" / L.MOREAU_KEY).as_posix()
    return re.compile(r"- quarantined \(the whole directory, RUN_PLAN_amend_3 section 8\.1\): " + re.escape(q) +
                      r" carrier sha256 " + wsha + r"; files " + str(n_files) +
                      r" \(\d{4}-\d\d-\d\dT[0-9:.+Z-]+\); deletion requested\n")


def part_f5() -> None:
    print(SEP + "\nPart F5: fix round 5 - the whole-directory SOURCE.md line (the 61b443f KeyError) and the resume of a "
                "crashed step 6")
    from a1_audit import real_sources as RS
    from a1_audit import wp3_material as WM
    # ---- item 1 / 3: the layout with a SOURCE.md beside the clone, now and at the parent commit
    ra, srca = _f5_layout("f5_now")
    wb = SCL(ra, L.MOREAU_KEY)
    wsha = hashlib_sha(wb.read_bytes())
    n_files = sum(1 for x in Path(ra.moreau_clone).rglob("*") if x.is_file())
    names = [x.name for x in Path(ra.moreau_clone).rglob("*")]
    resa, texta, _, _ = stage(ra)
    ea = resa["entries"][L.MOREAU_KEY]
    added = srca.read_text(encoding="utf-8")[len(F5_SOURCE_MD):]
    check("F5-1 (item 1) a SOURCE.md beside the clone: the stage now finishes 'final', Moreau 'extracted' with the whole "
          "clone quarantined, and SOURCE.md gains exactly ONE line: the runner-built quarantine directory, the carrier's "
          "sha256, the file count, the date, 'deletion requested'",
          resa["status"] == "final" and ea["status"] == FE.STATUS_EXTRACTED and ea["quarantined"]
          and srca.read_text(encoding="utf-8").startswith(F5_SOURCE_MD) and added.count("\n") == 1
          and _f5_line_rx(ra, wsha, n_files).fullmatch(added) is not None, repr(added[:60]))
    rest = added.replace((Path(ra.quarantine) / "ungated" / L.MOREAU_KEY).as_posix(), "")
    check("F5-1 the line carries no carrier-derived path component (beside the runner-built quarantine directory, no "
          "name of a file or folder inside the clone)", rest != added and not any(nm in rest for nm in names),
          str(len(names)))
    m_file = {"moved_to": "x/carrier.nii.gz", "sha256": "a" * 64, "bytes": 1}
    m_dir = {"moved_to": "x/key", "what": "w", "carrier_sha256": "b" * 64, "carrier_bytes": 2,
             "carrier_path_sha256": "c" * 64, "n_files_moved": 3}
    check("F5-1 every consumer of a move entry: the SOURCE.md line for a file move keeps its form; a whole-directory "
          "move has its own; any other shape raises KeyError (inside the source-md stage)",
          FE.source_md_quarantine_line(m_file, "D") == f"- quarantined: x/carrier.nii.gz sha256 {'a' * 64} (D); "
                                                       "deletion requested\n"
          and FE.source_md_quarantine_line(m_dir, "D") == "- quarantined (the whole directory, RUN_PLAN_amend_3 section "
                                                          f"8.1): x/key carrier sha256 {'b' * 64}; files 3 (D); deletion "
                                                          "requested\n"
          and raises(lambda: FE.source_md_quarantine_line({"moved_to": "x"}, "D"), KeyError))
    # the parent commit on the same layout reproduces the phase-2 crash
    rb_, srcb = _f5_layout("f5_crash")
    resb, textb, _, _ = _f5_crash(rb_)
    recs = WM.records_of(rb_, L.MOREAU_KEY)
    rec = recs[-1][1]
    stb = _f5_state(rb_)
    check(f"F5-2 (item 3) at the parent commit {PARENT_61B} the same layout crashes as phase 2 did: 'refused (stage "
          "failed)', stage run, KeyError at fetch_extract.py:1424; object saved, the clone moved, the deletion request "
          "written; SOURCE.md untouched; a PARTIAL manifest",
          resb["status"] == "partial" and len(recs) == 1 and rec["status"] == FE.STATUS_FAILED
          and rec["failed_stage"] == "run" and rec["failed_class"] == "KeyError"
          and rec["failed_where"] == "fetch_extract.py:1424" and "KeyError at run, fetch_extract.py:1424" in textb
          and rec["quarantine"]["quarantined"][0]["n_files_moved"] == n_files and stb["quarantine"]
          and not stb["clone_back"] and stb["request"] and stb["objects"]
          and stb["source_md"] == hashlib_sha(F5_SOURCE_MD.encode("utf-8"))
          and not resb["entries"][L.MOREAU_KEY]["final"] and WM.resumable(rec), str(rec.get("failed_where")))
    # ---- item 2: the resume from that exact state
    resc, textc, callsc, _ = stage(rb_)
    stc = _f5_state(rb_)
    ec = resc["entries"][L.MOREAU_KEY]
    addc = (Path(rb_.data) / L.MOREAU_KEY / "SOURCE.md").read_text(encoding="utf-8")[len(F5_SOURCE_MD):]
    comp = json.loads(WM.completion_path(rb_, L.MOREAU_KEY).read_bytes())
    check("F5-3 (item 2) the re-run resumes the crashed target: 'extracted', final, with the completion record; the "
          "stage writes the FINAL manifest", resc["status"] == "final" and ec["status"] == FE.STATUS_EXTRACTED
          and ec["final"] is True and ec["completion_record"] == f"ungated/{L.MOREAU_KEY}_completion.json"
          and ec["completed_from"] == FE.STATUS_FAILED and ec["record_sha256"] == stb["records"][0][1]
          and "resumed after a crash following step 6: SOURCE.md line appended" in textc)
    conds = {"records": stc["records"] == stb["records"], "objects": stc["objects"] == stb["objects"],
             "quarantine": stc["quarantine"] == stb["quarantine"], "source path": not stc["clone_back"],
             "request": stc["request"] == stb["request"], "one line": addc.count("\n") == 1,
             "line": _f5_line_rx(rb_, rec["identity"]["facts"]["sha256"], n_files).fullmatch(addc) is not None,
             "network": not [c for c in callsc if L.MOREAU_KEY in str(c) or "moreau" in str(c).lower()]}
    check("F5-3 only the missing step: SOURCE.md appended ONCE (the whole-directory line); nothing re-extracted (no new "
          "R18 record, the object unchanged), nothing moved again (the quarantine and the source path as they were), "
          "the deletion request unchanged; no network call for Moreau", all(conds.values()),
          ", ".join(k for k, v in conds.items() if not v))
    check("F5-3 the completion record (a SECOND record, never the crashed one overwritten): it names the crashed "
          "record by sha256, its status, stage, class and line; the object's and the deletion request's sha256",
          comp["schema"] == WM.COMPLETION_SCHEMA and comp["status"] == FE.STATUS_EXTRACTED
          and comp["completes"]["record_sha256"] == stb["records"][0][1]
          and comp["completes"]["failed_where"] == "fetch_extract.py:1424" and comp["source_md"] == "line appended"
          and comp["object_sha256"] == ec["object_sha256"] and comp["deletion_request_sha256"] == stb["request"]
          and comp["refusal_checks_none_held"] == list(WM.RESUME_CHECKS))
    try:
        prof, osha = RS.WP3Sources(rb_).moreau_profile64("1_16p11.2Del")
        loader_ok = osha == ec["object_sha256"] and len(prof) == 64
    except Exception as e:  # noqa: BLE001
        loader_ok = False
        print("    loader:", type(e).__name__)
    check("F5-3 the loader reads the resumed object through the final manifest (record, completion record and object "
          "re-hashed)", loader_ok)
    # a second re-run is a no-op
    resd, textd, callsd, _ = stage(rb_)
    std = _f5_state(rb_)
    check("F5-4 a second re-run is a no-op: the final manifest verified (completion record re-hashed), nothing written, "
          "SOURCE.md unchanged", resd.get("noop") is True and std == stc and not callsd
          and "verified; nothing to do" in textd)
    # the completion record tampered: the loader and the manifest check refuse
    cpb = WM.completion_path(rb_, L.MOREAU_KEY)
    raw = cpb.read_bytes()
    cpb.write_bytes(raw.replace(b'"line appended"', b'"line  appended"'))
    rese, _, _, _ = stage(rb_)
    check("F5-4 a completion record changed after the final manifest: the loader refuses ('phase-2 object changed') and "
          "the manifest re-check refuses the re-run",
          raises(lambda: RS.WP3Sources(rb_).moreau_profile64("1_16p11.2Del"), Exception, "status",
                 L.STATUS_OBJECT_CHANGED)
          and rese["status"] == "refused (the final manifest's records or objects changed)")
    cpb.write_bytes(raw)
    # a later manifest that drops the completion record: the loader refuses the crashed record ('not extracted')
    man = json.loads(rb_.latest_manifest().read_bytes())
    for k in ("completion_record", "completion_sha256", "completed_from"):
        man["objects"][L.MOREAU_KEY].pop(k, None)
    planted = Path(rb_.records) / "ungated" / "wp3_material_manifest.2.json"
    planted.write_bytes(json.dumps(man, indent=1).encode("utf-8"))
    try:
        dropped = raises(lambda: RS.WP3Sources(rb_).moreau_profile64("1_16p11.2Del"), Exception, "status",
                         L.STATUS_OBJECT_CHANGED)
    finally:
        planted.unlink()
    check("F5-4 (planted) a manifest entry 'extracted' over the crashed record without its completion record: the loader "
          "refuses ('phase-2 object changed')", dropped and rb_.latest_manifest().name == "wp3_material_manifest.json")
    # the target-level no-op and an append that happened before a crash of the completion write
    rc, srcc = _f5_layout("f5_subset")
    _f5_crash(rc, only=[L.MOREAU_KEY])
    with open(srcc, "ab") as f:                       # the line already there (a crash after the append)
        f.write(FE.source_md_quarantine_lines(WM.records_of(rc, L.MOREAU_KEY)[-1][1]["quarantine"]["quarantined"],
                                              "2026-10-12T00:00:00+00:00").encode("utf-8"))
    sh_before = hashlib_sha(srcc.read_bytes())
    r1, t1, _, _ = stage(rc, only=[L.MOREAU_KEY])
    s1 = _f5_state(rc)
    r2, t2, _, _ = stage(rc, only=[L.MOREAU_KEY])
    s2 = _f5_state(rc)
    check("F5-5 a SOURCE.md that already holds this move's line (a crash between the append and the completion record): "
          "nothing appended, the completion record written",
          r1["entries"][L.MOREAU_KEY]["status"] == FE.STATUS_EXTRACTED and s1["source_md"] == sh_before
          and json.loads(WM.completion_path(rc, L.MOREAU_KEY).read_bytes())["source_md"] ==
          "already present (nothing appended)")
    check("F5-5 the next run (no final manifest: a subset run) adopts the completed target: no second completion "
          "record, nothing appended", r2["entries"][L.MOREAU_KEY]["status"] == FE.STATUS_EXTRACTED
          and "final in an earlier run (adopted): status extracted" in t2
          and {k: v for k, v in s2.items() if k != "partials"} == {k: v for k, v in s1.items() if k != "partials"})
    # ---- the refusals: every inconsistent state stops for the operator; nothing is written
    def edit_record(r, fn):
        p_, rec_, _ = WM.records_of(r, L.MOREAU_KEY)[-1]
        fn(rec_)
        p_.write_bytes(json.dumps(rec_, indent=1).encode("utf-8"))

    def edit_request(r, fn):
        rq = Path(r.control) / "ungated" / f"{L.MOREAU_KEY}_deletion_request.json"
        d = json.loads(rq.read_bytes())
        fn(d)
        rq.write_bytes(json.dumps(d, indent=1).encode("utf-8"))

    def q_of(r):
        return Path(r.quarantine) / "ungated" / L.MOREAU_KEY

    def obj_of(r):
        return Path(WM.records_of(r, L.MOREAU_KEY)[-1][1]["extraction"]["object_path"])

    def write_failure(r):
        sp = Path(r.data) / L.MOREAU_KEY / "SOURCE.md"
        sp.unlink()
        sp.mkdir()                                     # SOURCE.md a folder: the in-stage read fails

    def object_outside(r):
        o = obj_of(r)
        twin = Path(r.data) / "elsewhere" / o.name     # the same bytes outside the artifacts root
        twin.parent.mkdir(parents=True)
        twin.write_bytes(o.read_bytes())
        edit_record(r, lambda d: d["extraction"].update(object_path=twin.as_posix()))

    def completion_of_incident(r):
        edit_record(r, lambda d: d.update(status=FE.STATUS_INCIDENT))
        rb = WM.records_of(r, L.MOREAU_KEY)[-1][2]
        WM.completion_path(r, L.MOREAU_KEY).write_bytes(json.dumps(
            {"schema": WM.COMPLETION_SCHEMA, "status": FE.STATUS_EXTRACTED,
             "completes": {"record_sha256": hashlib_sha(rb)}}).encode("utf-8"))

    cases = [
        ("the object's sha256 differs", WM.RESUME_OBJECT,
         lambda r: obj_of(r).write_bytes(obj_of(r).read_bytes() + b" ")),
        ("the object absent", WM.RESUME_OBJECT, lambda r: os.rename(obj_of(r), obj_of(r).with_name("away.json"))),
        ("the record's identity not a match", WM.RESUME_IDENTITY,
         lambda r: edit_record(r, lambda d: d["identity"]["comparison"].update(result="not auditable (map changed)"))),
        ("the record's quarantine path not the runner-built one", WM.RESUME_QENTRY,
         lambda r: edit_record(r, lambda d: d["quarantine"]["quarantined"][0].update(
             moved_to=d["quarantine"]["quarantined"][0]["moved_to"] + "_x"))),
        ("the record's carrier sha256 not the identity's", WM.RESUME_QENTRY,
         lambda r: edit_record(r, lambda d: d["quarantine"]["quarantined"][0].update(carrier_sha256="0" * 64))),
        ("the clone missing from the quarantine", WM.RESUME_QDIR,
         lambda r: os.rename(q_of(r), q_of(r).with_name("moved_away"))),
        ("the carrier back at its source path", WM.RESUME_SOURCE,
         lambda r: Path(r.moreau_clone).mkdir(parents=True)),
        ("the deletion request missing", WM.RESUME_REQUEST,
         lambda r: os.rename(Path(r.control) / "ungated" / f"{L.MOREAU_KEY}_deletion_request.json",
                             Path(r.control) / "ungated" / "away.json")),
        ("the deletion request's scope different", WM.RESUME_REQUEST,
         lambda r: edit_request(r, lambda d: d.update(scope=d["scope"] + " "))),
        ("the deletion request's files different", WM.RESUME_REQUEST,
         lambda r: edit_request(r, lambda d: d["files"][0].update(n_files_moved=d["files"][0]["n_files_moved"] + 1))),
        ("the deletion request for another key", WM.RESUME_REQUEST,
         lambda r: edit_request(r, lambda d: d.update(key="other"))),
        ("a completion record of another record", WM.RESUME_COMPLETION,
         lambda r: WM.completion_path(r, L.MOREAU_KEY).write_bytes(json.dumps(
             {"schema": WM.COMPLETION_SCHEMA, "status": FE.STATUS_EXTRACTED,
              "completes": {"record_sha256": "0" * 64}}).encode("utf-8"))),
        ("the record an incident, not a stage failure", WM.RESUME_STATUS,
         lambda r: edit_record(r, lambda d: d.update(status=FE.STATUS_INCIDENT))),
        ("the record a failure at another stage", WM.RESUME_STATUS,
         lambda r: edit_record(r, lambda d: d.update(failed_stage="identity"))),
        ("the SOURCE.md write failing", WM.RESUME_WRITE, write_failure),
        ("the record's object outside the artifacts root (same bytes)", WM.RESUME_OBJECT, object_outside),
        ("a completion record naming an incident record", WM.RESUME_STATUS, completion_of_incident),
        ("a completion record that is not JSON", WM.RESUME_COMPLETION,
         lambda r: WM.completion_path(r, L.MOREAU_KEY).write_bytes(b"not json\n")),
        ("the record's quarantine entry unreadable (not a mapping)", WM.RESUME_READ,
         lambda r: edit_record(r, lambda d: d["quarantine"].update(quarantined=["x"]))),
    ]
    for i, (what, check_text, plant) in enumerate(cases):
        r, _ = _f5_layout(f"f5_refuse_{i}")
        _f5_crash(r, only=[L.MOREAU_KEY])
        plant(r)
        before = _f5_state(r) if what != "the object absent" else None
        res, text, calls, _ = stage(r, only=[L.MOREAU_KEY])
        after = _f5_state(r) if before is not None else None
        comp_new = WM.completion_path(r, L.MOREAU_KEY).exists() and not what.startswith("a completion record")
        ok = (res.get("stopped") is True and res["status"] == WM.STOP_RESUME % check_text
              and f"stage {WM.STOP_RESUME % check_text}; no manifest written" in text and not comp_new
              and (before is None or after == before) and not calls
              and len(WM.records_of(r, L.MOREAU_KEY)) == 1)
        check(f"F5-6 (refusal) {what}: the stage stops for the operator ('{check_text}'); no completion record, no "
              "append, no record, no manifest, nothing moved", ok, res["status"])
    # the writer reads back what it wrote: a completion record the records do not adopt is a stop (planted)
    r, _ = _f5_layout("f5_readback")
    _f5_crash(r, only=[L.MOREAU_KEY])
    old = WM._completed_entry
    WM._completed_entry = lambda *a, **k: None
    try:
        res, text, _, _ = stage(r, only=[L.MOREAU_KEY])
    finally:
        WM._completed_entry = old
    check("F5-7 (planted) a completion record that the records do not read back as final 'extracted': the stage stops "
          "for the operator ('a write of the completion failed'); no manifest",
          res.get("stopped") is True and res["status"] == WM.STOP_RESUME % WM.RESUME_WRITE
          and len(r.partial_manifests()) == 1 and r.latest_manifest() is None, res["status"])


def hashlib_sha(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()


PARTS = {"P": [part_p], "S": [part_s_units, part_s], "D": [part_d_units, part_d], "B": [part_b],
         "M": [part_m], "X": [part_x], "Z": [part_z], "Q": [part_q], "F4": [part_f4], "F5": [part_f5],
         "N": [part_n]}


def main() -> int:
    t0 = time.time()
    for name, fns in PARTS.items():
        if ARGS.parts and name not in ARGS.parts:
            continue
        for fn in fns:
            try:
                fn()
            except Exception as e:  # noqa: BLE001
                import traceback
                traceback.print_exc()
                check(f"part {name} raised {type(e).__name__}", False)
    n = len(RESULTS)
    failed = [k for k, ok in RESULTS if not ok]
    print(f"{n - len(failed)} of {n} checks passed ({time.time() - t0:.0f} s)", flush=True)
    if not ARGS.keep:
        shutil.rmtree(TMP, ignore_errors=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
