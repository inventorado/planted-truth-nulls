"""WP2 AHBA builds (a1_audit/ahba_builds.py; RUN_PLAN.md v3.1 R10, R11, R12, R14, R31, §14; RUN_PLAN_amend_1 R35).

Run from arcs/audit/src:  ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_ahba_builds
                          [--part A|B|all] [--skip-large]
Exits non-zero if any check fails. Prints PASS / FAIL lines only (no matrix value, no AHBA sample count, no sample id).
Part A runs on synthetic data only (scratch files under $A1_SCRATCH or the system temp dir, removed at the end); part B
reads the builds' records and outputs under artifacts/ahba/a1_builds/ (written by ahba_builds.py in env/venv_ref) and
re-reads them HERE, in env/venv (pandas 3), so the R35 reader chain is checked across the two environments.

Part A (plants; every check function must catch its planted failure)
  A1 the primary-reproduction check: passes on the pins; each pinned quantity altered alone fails exactly its check
  A2 R12's DS filter is strict ('DS > .1'): a gene exactly at .1 is excluded (a '>=' filter, planted, is told apart)
  A3 R12's sign rule (prereg_amend_3.md:146): a score anti-correlated with the mean expression is flipped; a zero
     correlation is refused
  A4 leave-one-donor-out donor lists: exactly one dropped, the rest in order (two / none / wrong order / unknown refused)
  A5 counts: n_samples / n_donors per parcel; zero-sample parcels == empty rows (a planted count change is caught);
     LOO counts drop exactly the left-out donor's column; a donor-label mismatch is refused
  A6 the matrix writer: fixed gzip header (MTIME 0, FNAME) so two writes give the same bytes; both readers' hashes; a
     copy with one value moved by 1e-9 is caught by the 1e-12 read-back check and by the hash
  A7 a build record lacking a key is reported incomplete
  A8 the writer refuses any path outside artifacts/ahba/a1_builds (the primary files can never be overwritten)
Part B (the real builds)
  B1 the primary-reproduction check: primary-dk / -aal / -mist64 reproduce the L6 / L7 pins and the R35 default-reader
     pins (re-read here in env/venv: round-trip = L7 pin, default = R35 pin; decompressed content = the pinned file's)
  B2 every build's record is complete and ok; every output file's sha256 = its record; every matrix / table re-read
     here with both readers hashes as the record says (env/venv_ref values = env/venv values)
  B3 one environment and script: every record's environment equal on ahba_builds.ENV_SAME; script_sha256 = this
     checkout's ahba_builds.py
  B4 per-parcel sample and donor counts consistent across builds (normalisation cells and per-donor = primary; zero rows
     = empty rows everywhere; bilateral >= primary per parcel; Liu samples per label = primary n_samples; per-donor
     empty rows = that donor's zero counts; LOO counts = primary minus the left-out column)
  B5 R12: DS recomputed here without abagen (abagen's algorithm, numpy) = the stored DS; the selection is exactly
     DS > .1 among the dk-ctx genes; PC1 recomputed by numpy SVD of the centred dk-ctx matrix = the stored scores;
     corr(score, mean expression) > 0; a flipped copy (planted) fails the sign check
  B6 LOO: A3's MANIFEST lists six per atlas, each dropping exactly one donor; file sha256s = MANIFEST; the r11-loo record
     holds every check True
  B7 MANIFEST.json lists every build and derived record (record sha256s equal), NOT_BUILT names perdonor-hcpmmp1
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
import os
import shutil
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from a1_audit import ahba_builds as B

RESULTS: list = []


def check(name: str, cond) -> bool:
    RESULTS.append((name, bool(cond)))
    print("%s  %s" % ("PASS" if cond else "FAIL", B._ascii(name)))
    return bool(cond)


def raises(fn, exc=Exception) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


# ================================================================================================================
# Part A: synthetic plants
# ================================================================================================================
def _good_obs(atlas: str) -> dict:
    return dict(sha256_inmemory=B.L7_PINS[atlas], sha256_round_trip=B.L7_PINS[atlas],
                sha256_default=B.R35_DEFAULT_PINS[atlas], l6_rewrite_sha256=B.L6_PINS[atlas][1], content_equal=True,
                empty_parcels=[72, 73], expected_empty=[72, 73], n_genes=B.N_GENES_PRIMARY,
                nii_sha256=B.ATLAS[atlas]["nii_sha256"], info_sha256=B.ATLAS[atlas]["info_sha256"],
                settings=dict(B.FROZEN))


def part_a(scratch: Path) -> None:
    # A1
    for atlas in ("dk", "aal", "mist64"):
        c = B.check_primary(atlas, _good_obs(atlas))
        check(f"A1 {atlas}: the primary check passes on the pinned values", all(c.values()))
    alter = {"sha256_inmemory": ("0" * 64, "L7: in-memory frame hash == pin"),
             "sha256_round_trip": ("1" * 64, "L7: round-trip read of the written file == pin"),
             "sha256_default": ("2" * 64, "R35: default-reader read of the written file == pin"),
             "l6_rewrite_sha256": ("3" * 64, "L6: rewrite with the pinned gzip header == the pinned file sha256"),
             "content_equal": (False, "L6: decompressed content == the pinned file's"),
             "empty_parcels": ([72], "empty parcels == the committed meta's"),
             "n_genes": (15632, "n_genes == 15,633"),
             "nii_sha256": ("4" * 64, "atlas volume sha256 == pin"),
             "info_sha256": ("5" * 64, "atlas_info sha256 == pin"),
             "settings": (dict(B.FROZEN, gene_norm="zscore"), "settings == the frozen §3.1 settings")}
    for key, (bad, name) in alter.items():
        c = B.check_primary("dk", dict(_good_obs("dk"), **{key: bad}))
        failed = [k for k, v in c.items() if not v]
        check(f"A1 planted {key}: exactly its check fails", failed == [name])
    # A2
    ds = pd.Series({"g1": 0.1, "g2": 0.1000001, "g3": 0.09, "g4": 0.5, "g5": -0.2})
    sel = B.select_ds_genes(ds, list(ds.index))
    ge = [g for g in ds.index if ds[g] >= 0.1]  # the planted '>=' rule (abagen's keep_stable_genes)
    check("A2 DS > .1 is strict: the gene exactly at .1 is excluded", sel == ["g2", "g4"])
    check("A2 a planted '>=' filter is told apart from the strict one", ge != sel and "g1" in ge)
    # A3
    rng = np.random.default_rng(20261001)
    X = rng.normal(size=(34, 50)) + np.linspace(0, 3, 34)[:, None]
    m = X.mean(axis=1)
    s0 = m - m.mean() + 0.1 * rng.normal(size=34)
    lo = rng.normal(size=50)
    s, l, r, flipped = B.apply_sign(-s0, -lo, m)
    check("A3 an anti-correlated score is flipped and then correlates positively",
          flipped and r < 0 and np.corrcoef(s, m)[0, 1] > 0 and np.allclose(l, lo))
    s, l, r, flipped = B.apply_sign(s0, lo, m)
    check("A3 a positively correlated score is kept", (not flipped) and r > 0 and np.allclose(s, s0))
    check("A3 a zero / undefined correlation is refused",
          raises(lambda: B.apply_sign(np.ones(34), lo, m), B.BuildError))
    # A4
    D = list(B.DONORS)
    check("A4 the six without one, in order: accepted", all(B.loo_donors_ok([x for x in D if x != d], d) for d in D))
    check("A4 two donors dropped: refused", not B.loo_donors_ok(D[2:], D[0]))
    check("A4 no donor dropped: refused", not B.loo_donors_ok(D, D[0]))
    check("A4 wrong order: refused", not B.loo_donors_ok(list(reversed(D[1:])), D[0]))
    check("A4 the left-out donor still present: refused", not B.loo_donors_ok(D[:5], D[0]))
    check("A4 an unknown donor: refused", not B.loo_donors_ok(D[1:], "99999"))
    check("A4 a duplicated donor: refused", not B.loo_donors_ok([D[1], D[1], D[2], D[3], D[4]], D[0]))
    # A5
    raw = pd.DataFrame([[0, 0, 0, 0, 0, 0], [3, 0, 1, 0, 0, 0], [1, 1, 1, 1, 1, 1], [0, 0, 0, 0, 0, 2]],
                       index=[1, 2, 3, 4], columns=D)
    t = B.counts_table(raw, D)
    check("A5 n_samples / n_donors per parcel", list(t["n_samples"]) == [0, 4, 6, 2] and list(t["n_donors"]) ==
          [0, 2, 6, 1] and list(t.columns[2:]) == ["d1", "d2", "d3", "d4", "d5", "d6"])
    check("A5 zero-sample parcels == empty rows", B.counts_match_empty(t, [1]))
    t2 = t.copy()
    t2.loc[1, "n_samples"] = 1
    check("A5 a planted count change is caught", not B.counts_match_empty(t2, [1]))
    check("A5 a planted extra empty row is caught", not B.counts_match_empty(t, [1, 4]))
    lt = B.drop_donor_counts(t, D[5])
    check("A5 LOO counts: the left-out donor's column dropped, totals recomputed",
          "d6" not in lt.columns and list(lt["n_samples"]) == [0, 4, 5, 0] and list(lt["n_donors"]) == [0, 2, 5, 0])
    check("A5 donor columns in another order are refused",
          raises(lambda: B.counts_table(raw[list(reversed(D))], D), B.BuildError))
    # A6 (the writer guard is pointed at the scratch directory for this part)
    out0 = B.OUT
    B.OUT = scratch / "a1_builds"
    try:
        B.OUT.mkdir(parents=True)
        f = pd.DataFrame(rng.normal(size=(7, 5)), index=pd.Index([1, 2, 3, 5, 8, 13, 21], name="label"),
                         columns=["GA", "GB", "GC", "GD", "GE"])
        f.iloc[3] = np.nan
        p1, p2 = B.OUT / "x_expr.csv.gz", B.OUT / "y" / "x_expr.csv.gz"
        p2.parent.mkdir()
        B.write_csv_gz(f, p1)
        B.write_csv_gz(f, p2)
        hdr = B.gzip_header(p1.read_bytes()[:64])
        check("A6 fixed gzip header: MTIME 0, FNAME the final name", hdr["mtime"] == 0 and hdr["fname"] == "x_expr.csv")
        check("A6 two writes of one frame give the same bytes", B.sha256_file(p1) == B.sha256_file(p2))
        rt, dflt = B.read_frame(p1, "round_trip"), B.read_frame(p1, "default")
        check("A6 round-trip read hashes as the in-memory frame", B.frame_sha(rt) == B.frame_sha(f))
        check("A6 default reader within 1e-12 of the round-trip reader",
              B.nan_max_abs_delta(dflt.to_numpy(), rt.to_numpy()) < B.READBACK_TOL)
        g = f.copy()
        g.iloc[0, 0] += 1e-9
        B.write_csv_gz(g, p2)
        moved = B.read_frame(p2, "round_trip")
        check("A6 a value moved by 1e-9 is caught by the 1e-12 read-back check",
              not B.nan_max_abs_delta(moved.to_numpy(), f.to_numpy()) < B.READBACK_TOL)
        check("A6 ... and by the hash", B.frame_sha(moved) != B.frame_sha(f))
        h = f.copy()
        h.iloc[3, 0] = 0.0
        check("A6 a NaN position changed is caught (max |delta| = inf)",
              B.nan_max_abs_delta(h.to_numpy(), f.to_numpy()) == float("inf"))
        rec = B.matrix_output(f, B.OUT / "z_expr.csv.gz")
        check("A6 matrix_output records both readers' hashes and a 0 read-back delta",
              rec["sha256_round_trip"] == rec["sha256_inmemory"] and rec["readback_max_abs_delta"] == 0.0
              and len(rec["sha256_default"]) == 64)
        # A8
        check("A8 the writer refuses the primary matrix path",
              raises(lambda: B.write_csv_gz(f, B.AHBA / "dk_expr.csv.gz"), B.BuildError))
        check("A8 the writer refuses a path outside a1_builds",
              raises(lambda: B.write_text(scratch / "elsewhere.txt", "x"), B.BuildError))
    finally:
        B.OUT = out0
    check("A8 the module's OUT is artifacts/ahba/a1_builds", B.OUT == B.ROOT / "artifacts" / "ahba" / "a1_builds")
    # A7
    rec = {k: None for k in B.RECORD_KEYS}
    rec.update(kind="cell", outputs=[{k: 1 for k in B.OUTPUT_KEYS + B.MATRIX_KEYS}],
               abagen_call={k: 1 for k in list(B.FROZEN) + list(B.CALL_REST) +
                            ["atlas", "atlas_info", "return_counts", "return_report"]})
    rec["outputs"][0]["role"] = "matrix"
    check("A7 a complete synthetic record has no missing key", B.record_missing(rec) == [])
    r2 = dict(rec)
    del r2["inputs"]
    r2["abagen_call"] = {k: v for k, v in rec["abagen_call"].items() if k != "tolerance"}
    check("A7 a record without 'inputs' and an abagen argument is reported",
          set(B.record_missing(r2)) == {"inputs", "abagen_call.tolerance"})


# ================================================================================================================
# Part B: the real builds
# ================================================================================================================
def _rec(name: str) -> dict | None:
    p = B.OUT / name / B.RECORD
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _counts(name: str, file: str):
    return pd.read_csv(B.OUT / name / file, index_col=0)


def ds_numpy(frames: list) -> np.ndarray:
    """abagen 0.1.3 keep_stable_genes' stability (correct.py:556-625), re-implemented without abagen: each donor's
    frame ranked per gene over its own covered rows; per donor pair the Pearson correlation (z-scores, ddof 1) of the
    ranks over the rows both cover; the mean over pairs ignoring NaN; NaN -> 0."""
    ranks = [f.rank() for f in frames]
    G = frames[0].shape[1]
    pairs = list(itertools.combinations(range(len(frames)), 2))
    C = np.zeros((G, len(pairs)))
    for k, (i, j) in enumerate(pairs):
        reg = np.intersect1d(ranks[i].dropna(axis=0, how="all").index, ranks[j].dropna(axis=0, how="all").index)
        a = ranks[i].loc[reg].to_numpy(dtype=float)
        b = ranks[j].loc[reg].to_numpy(dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            az = (a - a.mean(0)) / a.std(0, ddof=1)
            bz = (b - b.mean(0)) / b.std(0, ddof=1)
            C[:, k] = (az * bz).sum(0) / (len(reg) - 1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nan_to_num(np.nanmean(C, axis=1))


def ds_spearman_intersection(frames: list) -> np.ndarray:
    """A plain reading of R12's wording ('the Spearman correlation ... over the regions both donors cover'): ranks
    taken within each pair's common rows. Reported beside abagen's (descriptor only)."""
    G = frames[0].shape[1]
    pairs = list(itertools.combinations(range(len(frames)), 2))
    C = np.zeros((G, len(pairs)))
    for k, (i, j) in enumerate(pairs):
        reg = np.intersect1d(frames[i].dropna(axis=0, how="all").index, frames[j].dropna(axis=0, how="all").index)
        a = frames[i].loc[reg].rank().to_numpy(dtype=float)
        b = frames[j].loc[reg].rank().to_numpy(dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            az = (a - a.mean(0)) / a.std(0, ddof=1)
            bz = (b - b.mean(0)) / b.std(0, ddof=1)
            C[:, k] = (az * bz).sum(0) / (len(reg) - 1)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nan_to_num(np.nanmean(C, axis=1))


def part_b(skip_large: bool) -> None:
    names = list(B.ORDER) + list(B.DERIVED)
    recs = {n: _rec(n) for n in names}
    check("B2 every build and derived record exists", all(recs[n] is not None for n in names))
    recs = {n: r for n, r in recs.items() if r is not None}
    # B1
    for atlas in ("dk", "aal", "mist64"):
        r = recs.get(f"primary-{atlas}")
        if r is None:
            check(f"B1 {atlas}: primary record present", False)
            continue
        pr = r["checks"]["primary_reproduction"]
        check(f"B1 {atlas}: primary check reproduces, every item True", pr["reproduces"] is True
              and all(pr["checks"].values()) and r["ok"] is True)
        check(f"B1 {atlas}: the planted wrong hash was caught at build time", pr.get("planted_wrong_hash_caught") is True)
        o = next(x for x in r["outputs"] if x["role"] == "matrix")
        p = B.OUT / f"primary-{atlas}" / o["file"]
        rt, dflt = B.read_frame(p, "round_trip"), B.read_frame(p, "default")
        check(f"B1 {atlas}: env/venv round-trip read of the rebuilt file == the L7 pin", B.frame_sha(rt) == B.L7_PINS[atlas])
        check(f"B1 {atlas}: env/venv default read of the rebuilt file == the R35 pin",
              B.frame_sha(dflt) == B.R35_DEFAULT_PINS[atlas])
        pinned = B.AHBA / B.L6_PINS[atlas][0]
        check(f"B1 {atlas}: the pinned primary file is untouched (L6 sha256)", B.sha256_file(pinned) == B.L6_PINS[atlas][1])
        check(f"B1 {atlas}: decompressed content == the pinned file's",
              gzip.decompress(p.read_bytes()) == gzip.decompress(pinned.read_bytes()))
        check(f"B1 {atlas}: abagen's report == the primary build's report (recorded beside the check)",
              pr.get("report_equals_primary_report") is True)
    # B2 / B3
    here = B.sha256_file(Path(B.__file__))
    env0 = None
    for n, r in recs.items():
        check(f"B2 {n}: record complete", B.record_missing(r) == [])
        check(f"B2 {n}: ok", r.get("ok") is True)
        if env0 is None:
            env0 = r["environment"]
        check(f"B3 {n}: same environment and script as the others",
              all(r["environment"].get(k) == env0.get(k) for k in B.ENV_SAME))
        check(f"B3 {n}: script_sha256 == this checkout's ahba_builds.py", r["environment"].get("script_sha256") == here)
        if r["kind"] in ("primary", "cell", "perdonor", "samples"):
            call = r["abagen_call"]
            ov = dict(r.get("overrides") or {})
            check(f"B2 {n}: the recorded abagen call = the frozen settings + the build's overrides",
                  all(call[k] == ov.get(k, v) for k, v in B.FROZEN.items()) and r["environment"]["abagen"] == "0.1.3")
        for o in r["outputs"]:
            fp = (B.ROOT / o["file"]) if o["file"].startswith("artifacts/") else (B.OUT / n / o["file"])
            ok_sha = fp.exists() and B.sha256_file(fp) == o["sha256"]
            check(f"B2 {n}/{o['file']}: sha256 == record", ok_sha)
            if o["role"] in ("matrix", "counts", "table") and ok_sha:
                if skip_large and o["bytes"] > 100 * 2**20:
                    print("SKIP  B2 %s/%s: both readers in env/venv (--skip-large)" % (n, o["file"]))
                    continue
                rt, dflt = B.read_frame(fp, "round_trip"), B.read_frame(fp, "default")
                check(f"B2 {n}/{o['file']}: env/venv round-trip hash == the env/venv_ref record",
                      B.frame_sha(rt) == o["sha256_round_trip"])
                check(f"B2 {n}/{o['file']}: env/venv default hash == the env/venv_ref record",
                      B.frame_sha(dflt) == o["sha256_default"])
                del rt, dflt
    # B4 counts
    def pc(atlas):
        return _counts(f"primary-{atlas}", f"{atlas}_counts.csv")

    for atlas in ("dk", "aal", "mist64"):
        r = recs.get(f"primary-{atlas}")
        if r is None:
            continue
        c = pc(atlas)
        check(f"B4 {atlas}: zero-sample parcels == the primary's empty parcels",
              B.counts_match_empty(c, r["checks"]["empty_parcels"]))
        dcols = [x for x in c.columns if x.startswith("d")]
        check(f"B4 {atlas}: n_samples = the donor columns' sum; n_donors = donors with >= 1 sample",
              (c["n_samples"] == c[dcols].sum(axis=1)).all() and (c["n_donors"] == (c[dcols] > 0).sum(axis=1)).all()
              and len(dcols) == 6)
    for atlas in ("dk", "aal"):
        if recs.get(f"primary-{atlas}") is None:
            continue
        c = pc(atlas)
        for cell in ("zscore-matched", "srs-unmatched", "zscore-unmatched"):
            n = f"r11-{atlas}-{cell}"
            if n in recs:
                cc = _counts(n, f"{atlas}_counts.csv")
                check(f"B4 {n}: counts == primary counts", cc.equals(c))
                check(f"B4 {n}: zero-sample parcels == its empty rows",
                      B.counts_match_empty(cc, recs[n]["checks"]["empty_parcels"]))
        n = f"r11-{atlas}-bilateral"
        if n in recs:
            cb = _counts(n, f"{atlas}_counts.csv")
            check(f"B4 {n}: per parcel n_samples and n_donors >= the primary's (mirroring adds samples)",
                  (cb["n_samples"] >= c["n_samples"]).all() and (cb["n_donors"] >= c["n_donors"]).all())
            check(f"B4 {n}: zero-sample parcels == its empty rows",
                  B.counts_match_empty(cb, recs[n]["checks"]["empty_parcels"]))
        n = f"perdonor-{atlas}"
        if n in recs:
            cp = _counts(n, f"{atlas}_counts.csv")
            check(f"B4 {n}: counts == primary counts", cp.equals(c))
            ok = True
            for k, d in enumerate(B.DONORS, start=1):
                o = next(x for x in recs[n]["outputs"] if x.get("donor") == d)
                f = B.read_frame(B.OUT / n / o["file"], "round_trip")
                ok &= sorted(B.empty_rows(f)) == sorted(int(i) for i in cp.index[cp[f"d{k}"] == 0])
            check(f"B4 {n}: each donor's empty rows == its zero-count parcels", ok)
    n = "r10-liu-dk-samples"
    if n in recs and recs.get("primary-dk") is not None:
        o = next(x for x in recs[n]["outputs"] if x["role"] == "matrix")
        if skip_large:
            print("SKIP  B4 %s: samples per label re-read (--skip-large)" % n)
        else:
            idx = pd.read_csv(B.OUT / n / o["file"], usecols=[0]).iloc[:, 0].to_numpy()
            per = pd.Series(idx).value_counts().reindex(pc("dk").index, fill_value=0)
            check(f"B4 {n}: samples per DK label == primary-dk n_samples",
                  (per.to_numpy() == pc("dk")["n_samples"].to_numpy()).all())
        check(f"B4 {n}: the record says so and no well id was saved",
              recs[n]["checks"]["samples per label == primary counts n_samples"] is True
              and recs[n]["checks"]["well ids saved"] is False)
    # B5 R12
    r = recs.get("r12-han-c1-ourpc1")
    if r is not None and recs.get("perdonor-dk") is not None:
        info = pd.read_csv(B.ROOT / B.ATLAS["dk"]["info"])
        ids34 = [int(i) for i in info.loc[(info["hemisphere"] == "L") & (info["structure"] == "cortex"), "id"]]
        frames = []
        for d in B.DONORS:
            o = next(x for x in recs["perdonor-dk"]["outputs"] if x.get("donor") == d)
            frames.append(B.read_frame(B.OUT / "perdonor-dk" / o["file"], "round_trip").loc[ids34])
        ds_file = pd.read_csv(B.OUT / "r12-han-c1-ourpc1" / "ds_dk_ctx_perdonor.csv", index_col=0,
                              keep_default_na=False, na_values=[""])
        ds_np = ds_numpy(frames)
        check("B5 R12 DS: 34 left DK cortical parcels", len(ids34) == 34 and ids34 == list(range(1, 35)))
        check("B5 R12 DS: gene order = the per-donor columns", [str(g) for g in ds_file.index] ==
              [str(g) for g in frames[0].columns])
        dmax = float(np.max(np.abs(ds_np - ds_file["ds"].to_numpy(dtype=float))))
        check("B5 R12 DS recomputed without abagen == the stored DS (max |delta| < 1e-9)", dmax < 1e-9)
        sp = ds_spearman_intersection(frames)
        prim = B.read_frame(B.AHBA / B.L6_PINS["dk"][0], "round_trip")
        check("B5 the pinned primary dk matrix hashes as L7", B.frame_sha(prim) == B.L7_PINS["dk"])
        prim = prim.loc[ids34]
        ds_s = pd.Series(ds_np, index=frames[0].columns)
        sel = [g for g in prim.columns if ds_s[g] > 0.1]
        load = pd.read_csv(B.OUT / "r12-han-c1-ourpc1" / "pc1_loadings.csv", index_col=0, keep_default_na=False,
                           na_values=[""])
        check("B5 R12 the PCA genes are exactly the dk-ctx genes with DS > .1 (strict), in matrix order",
              [str(g) for g in load.index] == [str(g) for g in sel])
        check("B5 R12 the record's counts agree", r["checks"]["n_selected"] == len(sel)
              and r["checks"]["n_genes_dk_ctx"] == prim.shape[1])
        spd = pd.Series(sp, index=frames[0].columns)
        n_diff = sum(1 for g in prim.columns if (ds_s[g] > 0.1) != (spd[g] > 0.1))
        print("INFO  B5 R12 abagen's DS vs re-ranked-per-pair Spearman: max |delta| %.3g; dk-ctx genes classified "
              "differently at .1: %d" % (float(np.max(np.abs(ds_np - sp))), n_diff))
        X = prim[sel].to_numpy(dtype=float)
        Xc = X - X.mean(axis=0)
        U, s, Vt = np.linalg.svd(Xc, full_matrices=False)
        sc = U[:, 0] * s[0]
        mean_sel = X.mean(axis=1)
        if np.corrcoef(sc, mean_sel)[0, 1] < 0:
            sc = -sc
        pc1 = pd.read_csv(B.OUT / "r12-han-c1-ourpc1" / "pc1_dk_ctx.csv", index_col=0)
        check("B5 R12 PC1 parcels = the 34 ids", [int(i) for i in pc1.index] == ids34)
        check("B5 R12 PC1 = numpy SVD of the centred dk-ctx matrix, signed by the rule (max |delta| < 1e-8)",
              float(np.max(np.abs(pc1["pc1"].to_numpy() - sc))) < 1e-8)
        check("B5 R12 corr(PC1 score, mean expression over the PCA genes) > 0",
              np.corrcoef(pc1["pc1"].to_numpy(), mean_sel)[0, 1] > 0)
        flipped = -pc1["pc1"].to_numpy()
        check("B5 R12 a planted flipped PC1 fails the sign rule", not np.corrcoef(flipped, mean_sel)[0, 1] > 0)
        check("B5 R12 loadings x centred matrix = the scores", float(np.max(np.abs(Xc @ load["loading"].to_numpy()
                                                                                    - pc1["pc1"].to_numpy()))) < 1e-8)
        check("B5 R12 labelled 'convention (pre-exposure)' with the exposure note",
              r["checks"]["label"] == B.R12_LABEL and "14:25" in r["checks"]["exposure_note"])
    # B6 LOO
    man_p = B.LOO_DIR / "MANIFEST.json"
    man = json.loads(man_p.read_text(encoding="utf-8"))
    for atlas in ("dk", "aal"):
        cells = man["atlases"][atlas]["loo"]
        check(f"B6 {atlas}: A3's MANIFEST lists one LOO matrix per donor", sorted(cells) == sorted(B.DONORS))
        check(f"B6 {atlas}: every LOO build drops exactly one donor (MANIFEST)",
              all(B.loo_donors_ok(cells[d]["donors"], d) for d in B.DONORS))
        check(f"B6 {atlas}: every LOO file's sha256 == MANIFEST",
              all(B.sha256_file(B.LOO_DIR / cells[d]["file"]) == cells[d]["sha256_file"] for d in B.DONORS))
    r = recs.get("r11-loo")
    if r is not None:
        cells = [(a, d, v) for a in ("dk", "aal") for d, v in r["checks"]["loo"][a]["cells"].items()]
        check("B6 r11-loo: 12 cells, every check True", len(cells) == 12 and all(all(v["checks"].values())
                                                                                 for _, _, v in cells))
        for a, d, v in cells:
            lc = _counts("r11-loo", v["counts"])
            ok = B.counts_match_empty(lc, v["empty_parcels"]) and f"d{B.DONORS.index(d) + 1}" not in lc.columns
            if recs.get(f"primary-{a}") is not None:
                ok &= lc.equals(B.drop_donor_counts(pc(a), d))
            check(f"B6 {a} LOO {d}: derived counts = primary minus the left-out column; zero rows = empty rows", ok)
    # B7
    mp = B.MANIFEST_JSON
    if not mp.exists():
        check("B7 MANIFEST.json exists", False)
        return
    m = json.loads(mp.read_text(encoding="utf-8"))
    check("B7 MANIFEST lists every build and derived record", sorted(m["builds"]) == sorted(names))
    check("B7 MANIFEST record sha256s == the records",
          all(B.sha256_file(B.OUT / v["record"]) == v["record_sha256"] for v in m["builds"].values()))
    check("B7 MANIFEST names the build not made (perdonor-hcpmmp1)", set(m["not_built"]) == set(B.NOT_BUILT))
    check("B7 MANIFEST: inputs re-hashed unchanged; inputs.json sha256 equal",
          m["inputs"]["unchanged"] is True and B.sha256_file(B.INPUTS_JSON) == m["inputs"]["sha256"])
    check("B7 MANIFEST: primaries reproduce", all(m["builds"][f"primary-{a}"]["primary_reproduction"] is True
                                                 for a in ("dk", "aal", "mist64")))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--part", choices=("A", "B", "all"), default="all")
    ap.add_argument("--skip-large", action="store_true")
    a = ap.parse_args(argv)
    base = Path(os.environ.get("A1_SCRATCH") or tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="a1_wp2_ahba_", dir=str(base)))
    try:
        if a.part in ("A", "all"):
            part_a(scratch)
        if a.part in ("B", "all"):
            part_b(a.skip_large)
    finally:
        if not os.environ.get("A1_KEEP_SCRATCH"):
            shutil.rmtree(scratch, ignore_errors=True)
    n_fail = sum(1 for _, ok in RESULTS if not ok)
    print("test_ahba_builds: %d checks, %d passed, %d failed" % (len(RESULTS), len(RESULTS) - n_fail, n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
