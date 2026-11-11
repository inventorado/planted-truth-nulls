"""A1 WP2: the env/venv_ref AHBA builds (RUN_PLAN.md v3.1, FROZEN 16c60232...: R10, R11, R12, R14 with R31; §14's
"venv_ref builds" row; RUN_PLAN_amend_1.md v2.1, FROZEN 8e06d60e...: R35, both matrix readers).

Nothing here reads a map, a set, a carrier, a decoder output or a claim value: AHBA (as abagen 0.1.3 reads it from
E:/data/asdg/ahba), the atlases the frozen builders used, and the primary matrices' committed pins only. No network: the
build process refuses every socket connection (an abagen download attempt fails loudly instead of fetching).

FIRST, the primary-reproduction CHECK (RUN_PLAN.md:146-147 L6 / L7; amend_1 R35). Builds `primary-dk`, `primary-aal`,
`primary-mist64` call abagen.get_expression_data at the frozen §3.1 settings (prereg.md:66-69; the recipe of
arcs/audit/src/e4_ahba_matrices.py and src_register/mist64_ahba_matrix.py, copied, not imported) and must reproduce:
  - L7: sha256 of hash_pandas_object(df, index=True) of abagen's in-memory frame AND of the written file read back by
    the round-trip reader = the L7 pin; the default reader's = the R35 pin;
  - L6: the pinned .csv.gz bytes. The frame is re-written in memory with this module's writer and the pinned file's own
    gzip header fields (FNAME, MTIME; read from its first bytes) and the sha256 must equal the L6 pin; the decompressed
    content of this build's file must equal the pinned file's. (A .csv.gz written now cannot carry the pinned bytes
    otherwise: gzip stores the write time.)
  - the committed primary meta's empty parcels, and 15,633 genes (prereg §3.1 A2 for V-DK; the meta's for AAL, MIST64);
  - the atlas NIfTI and atlas_info sha256 pins (R10 0a28c93f... for the DK volume; claims_register.md:1030 40b1edfa...
    for AAL; register_maps/mist64_ahba_matrix.json 372f27f4... for MIST64; s_build.py:155-163 for the atlas_info CSVs).
No other build of an atlas starts unless that atlas's primary check passed with the same script bytes and environment.

Builds (`BUILDS`; every abagen argument recorded and passed explicitly, the signature asserted covered):
  primary-<atlas>           §3.1 settings + return_counts: the check above; R11's per-parcel sample / donor counts
                            (V-DK, V-AAL, MIST64; dk-ctx and V-DK-subcortex are subsets of V-DK, RUN_PLAN.md:687-688)
  r11-<dk|aal>-<cell>       R11's mini-multiverse matrices (RUN_PLAN.md:677-689): (zscore, True), (srs, False),
                            (zscore, False) and the bilateral cell (lr_mirror 'bidirectional'), each with its counts
  perdonor-<dk|aal>         §3.1 settings with return_donors=True: R12 (per-donor V-DK for DS), R14's per-donor recipe
                            on the claim's class (dk-ctx: Leyhausen, Park; V-AAL: Segura, Pagani) and R31 (Benkarim,
                            dk-ctx); the six per-donor matrices + counts; the donor mean must equal the pinned primary
  r10-liu-dk-samples        R10's T4/T5 sample assignment (region_agg=None, every other argument at §3.1): per-sample
                            rows labelled by DK label; the AHBA well ids are dropped from the frame at once (never
                            printed, logged or saved; RUN_PLAN.md:653-655)
Derived (`DERIVED`; no abagen expression call):
  r12-han-c1-ourpc1         R12: DS = abagen.correct.keep_stable_genes(<per-donor V-DK, 34 left DK cortical parcels>,
                            threshold=0.1, percentile=False, rank=True, return_stability=True); PC1 = sklearn PCA()
                            (columns centred, not scaled) of the dk-ctx §3.1 matrix over the genes with DS > .1 (strict);
                            sign: corr(PC score, mean expression over genes) > 0 (prereg_amend_3.md:146)
  r11-loo                   R11's leave-one-donor-out matrices exist (A3, artifacts/ahba/loo): verified as A3 did
                            (MANIFEST, file sha256, round-trip matrix hash, six-donor full check = the L7 pin, donors =
                            the six minus exactly one) + both readers' hashes; their per-parcel counts derived from the
                            primary build's per-donor counts (the left-out donor's column dropped), checked against
                            each LOO matrix's empty parcels
Not built (`NOT_BUILT`): perdonor-hcpmmp1 (R14 on Pretzsch's 180 left Glasser parcels needs R15's figshare volume).

Outputs (git-ignored): artifacts/ahba/a1_builds/<build>/ (matrices .csv.gz written with a fixed gzip header (MTIME 0),
so a rebuild reproduces the file bytes; counts / small tables as LF CSV; abagen's report verbatim) and
<build>/build_record.json; artifacts/ahba/a1_builds/inputs.json (sha256 of every input file); MANIFEST.json.
Every writer reads back what it wrote; counts are never printed (donor columns d1..d6 = the position in DONORS).

Run (from arcs/audit/src; env/venv_ref, abagen 0.1.3, pandas 1.5.3; one BLAS thread; BelowNormal priority):
  ..\\..\\..\\env\\venv_ref\\Scripts\\python.exe -X utf8 -m a1_audit.ahba_builds inputs
  ..\\..\\..\\env\\venv_ref\\Scripts\\python.exe -X utf8 -m a1_audit.ahba_builds build primary-dk [more ...]
  ..\\..\\..\\env\\venv_ref\\Scripts\\python.exe -X utf8 -m a1_audit.ahba_builds derive r12-han-c1-ourpc1 r11-loo
  ..\\..\\..\\env\\venv_ref\\Scripts\\python.exe -X utf8 -m a1_audit.ahba_builds manifest
  ..\\..\\..\\env\\venv_ref\\Scripts\\python.exe -X utf8 -m a1_audit.ahba_builds all     (the primaries first; stops if
                                                                                          one fails the check)
Tests: a1_audit/tests/test_ahba_builds.py (env/venv; the planted failures and the record checks).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse  # noqa: E402
import ast  # noqa: E402
import datetime as _dt  # noqa: E402
import gzip  # noqa: E402
import hashlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import struct  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from dataclasses import dataclass  # noqa: E402
from pathlib import Path  # noqa: E402

# ================================================================================================================
# paths and pins (each cites its frozen source)
# ================================================================================================================
ROOT = Path(__file__).resolve().parents[4]
REL_SCRIPT = "arcs/audit/src/a1_audit/ahba_builds.py"
AHBA = ROOT / "artifacts" / "ahba"
OUT = AHBA / "a1_builds"
LOO_DIR = AHBA / "loo"
INPUTS_JSON = OUT / "inputs.json"
MANIFEST_JSON = OUT / "MANIFEST.json"
RECORD = "build_record.json"
DATA_AHBA = Path("E:/data/asdg/ahba")
E4_PATH = ROOT / "arcs" / "audit" / "src" / "e4_ahba_matrices.py"
E4_JSON = ROOT / "arcs" / "audit" / "results" / "e4_ahba_matrices.json"
MIST64_JSON = ROOT / "arcs" / "audit" / "register_maps" / "mist64_ahba_matrix.json"

# abagen.fetch_microarray(donors='all') keys (A3 ahba_loo.py DONORS; public AHBA donor labels)
DONORS = ("9861", "10021", "12876", "14380", "15496", "15697")
AHBA_FILES = ("MicroarrayExpression.csv", "Ontology.csv", "PACall.csv", "Probes.csv", "SampleAnnot.csv")
# prereg.md:66-69 §3.1 frozen defaults, as e4_ahba_matrices.py FROZEN (asserted equal to that file's literal by ast)
FROZEN = dict(ibf_threshold=0.5, probe_selection="diff_stability", donor_probes="aggregate", lr_mirror=None,
              missing=None, tolerance=2, sample_norm="srs", gene_norm="srs", norm_matched=True,
              norm_structures=False, region_agg="donors", agg_metric="mean", corrected_mni=True,
              reannotated=True, return_donors=False)
# the remaining get_expression_data arguments, passed explicitly at the values the frozen recipe leaves (abagen 0.1.3
# defaults; donors 'all' and the data_dir as e4 / mist64_ahba_matrix.py); verbose is output-only
CALL_REST = dict(sim_threshold=None, exact=None, donors="all", data_dir=str(DATA_AHBA), verbose=0, n_proc=1)

# atlases: the frozen builders' volumes and the pinned atlas_info CSVs (s_build.py:155-163 / RUN_PLAN L6)
ATLAS = {
    "dk": dict(nii="abagen-data:atlas-desikankilliany.nii.gz",
               nii_sha256="0a28c93f5967f0892810219e68edb32abcaa9fd796a217096512fb0724c20d8a",  # RUN_PLAN.md:652 (R10)
               nii_pin_source="RUN_PLAN.md:652 (R10, 8-hex prefix; full value of abagen 0.1.3's bundled file)",
               info="artifacts/ahba/dk_atlas_info.csv",
               info_sha256="abb69a9bf976a153b749eb5333e92cf03d4f61f2ce3efd34e49ea6e82f18729b",
               recipe="e4_ahba_matrices.atlas_and_info('dk'): nibabel.load(abagen.fetch_desikan_killiany()['image']), "
                      "atlas_info = abagen's atlas-desikankilliany.csv (asserted frame-equal to the pinned CSV)",
               classes=("V-DK", "dk-ctx", "V-DK-subcortex")),
    "aal": dict(nii="E:/data/asdg/abide1_pcp/atlases/aal_roi_atlas.nii.gz",
                nii_sha256="40b1edfa68bccf06f608661b79655726f59485498b665bd9bac7f86394d6b9c2",
                nii_pin_source="claims_register.md:1030 (8-hex prefix; full value recorded here)",
                info="artifacts/ahba/aal_atlas_info.csv",
                info_sha256="22e758a7fd525b641ef099028f9329f932a3ff3c1acf65416a8b4574795bf0ee",
                recipe="e4_ahba_matrices.atlas_and_info('aal'): nibabel.load(<PCP aal_roi_atlas.nii.gz>), atlas_info = "
                       "the pinned aal_atlas_info.csv (e4's id / label / hemisphere / structure frame as written)",
                classes=("V-AAL",)),
    "mist64": dict(nii="E:/data/asdg/mist/extracted/Release/Parcellations/MIST_64.nii.gz",
                   nii_sha256="372f27f4bc116f8dddce7281da11d0609655e347f26c6b4621d17c82e80e7a43",
                   nii_pin_source="register_maps/mist64_ahba_matrix.json atlas_volume_sha256",
                   info="artifacts/ahba/mist64_atlas_info.csv",
                   info_sha256="4dafc820bad33634666f37e0b20ee7cd0358ce67005af96bba87e6cc4fe3fcca",
                   recipe="src_register/mist64_classes.load_int_atlas (copied: integral float labels recast to int32, "
                          "qform / sform = the affine, code 1); atlas_info = the pinned mist64_atlas_info.csv",
                   classes=("MIST64",)),
}
# RUN_PLAN.md:146 L6 (s_build.py:155-163 PIN), raw-byte sha256 of the primary files
L6_PINS = {"dk": ("dk_expr.csv.gz", "949aeb011a202eeae768d954e868175759de1f9e9f38c54deab88b0d48fd85bf"),
           "aal": ("aal_expr.csv.gz", "44ef457c99e39a5d72586f52dcc1974c5f317b665739978382683d1eb3ccd33c"),
           "mist64": ("mist64_expr.csv.gz", "7a7a6e22ab9f4e2238e122c609b3d77ea584eb42295afd5d70cc531b0514e153")}
# RUN_PLAN.md:147 L7 (results/e4_ahba_matrices.json; register_maps/mist64_ahba_matrix.json): round-trip reader
L7_PINS = {"dk": "9c66a2058896061fd3630fdad15abe121fc1148ac7160181b200cb0fb7d9b1b2",
           "aal": "0dbbb50ca9a60647b7dc49477c905dbb49631be0f42f74889039f8d8d7bb6a00",
           "mist64": "7f750213c2c5e02b85b0d05cdde2e095401c353cc518e21e256324542080a850"}
# RUN_PLAN_amend_1.md:371-374 R35: A1's default reader (read_csv(index_col=0))
R35_DEFAULT_PINS = {"dk": "6707881c6b5d9e12858f654cdfb6ec9b416d352f74f36fe59c11d2088c6daebe",
                    "aal": "ef455efb83f38a234f34dbd0e66153a8c48f6f1ac6f12bbab9d8bd1e0d3e9eac",
                    "mist64": "13aa6f7df6020d6f19a37f3130b332f80f4511d9f542d2f1760f4de2a7a97997"}
N_GENES_PRIMARY = 15633  # prereg §3.1 A2 (V-DK); the committed metas for AAL and MIST64
READERS = {"round_trip": "pandas.read_csv(path, index_col=0, float_precision='round_trip')",
           "default": "pandas.read_csv(path, index_col=0)"}
HASH_RULE = "sha256(pandas.util.hash_pandas_object(df, index=True).to_numpy().tobytes())"
READBACK_TOL = 1e-12  # prereg §3.1 A4; amend_1 R35 'values'
A3_LOO_MANIFEST_PREFIX = "c7d12224"  # arcs/replication/src/ahba_loo_extra.py:5 ("pinned: MANIFEST c7d12224...")
R12_THRESHOLD = 0.1
R12_LABEL = "convention (pre-exposure)"
R12_EXPOSURE_NOTE = ("the exposure meant is this audit's; declared beside it (RUN_PLAN.md:707-709, §9): the exploration "
                     "lane's 2026-10-01 14:25-14:30 descriptives of the ENIGMA-ASD tables preceded these conventions, "
                     "which do not use them; they act on AHBA matrices only")


@dataclass(frozen=True)
class Spec:
    name: str
    atlas: str
    kind: str            # primary | cell | perdonor | samples
    overrides: tuple     # ((abagen argument, value), ...) over FROZEN
    readings: tuple
    what: str


def _cells(atlas: str) -> list:
    cls = {"dk": "V-DK (dk-ctx, V-DK-subcortex subsets)", "aal": "V-AAL"}[atlas]
    r11 = "R11 (RUN_PLAN.md:677-689): the mini-multiverse matrices for %s" % cls
    return [
        Spec(f"r11-{atlas}-zscore-matched", atlas, "cell", (("gene_norm", "zscore"),), (r11,),
             "mini-multiverse cell (gene_norm, norm_matched) = (zscore, True)"),
        Spec(f"r11-{atlas}-srs-unmatched", atlas, "cell", (("norm_matched", False),), (r11,),
             "mini-multiverse cell (gene_norm, norm_matched) = (srs, False)"),
        Spec(f"r11-{atlas}-zscore-unmatched", atlas, "cell", (("gene_norm", "zscore"), ("norm_matched", False)), (r11,),
             "mini-multiverse cell (gene_norm, norm_matched) = (zscore, False)"),
        Spec(f"r11-{atlas}-bilateral", atlas, "cell", (("lr_mirror", "bidirectional"),), (r11,),
             "the bilateral cell (prereg.md:56: lr_mirror='bidirectional')"),
    ]


_PRIMARY_READINGS = ("RUN_PLAN.md:146-147 L6 / L7 and RUN_PLAN_amend_1 R35: the primary-reproduction check",
                     "R11 (RUN_PLAN.md:672-673, :687-688): per-parcel AHBA sample and donor counts, return_counts=True "
                     "at the §3.1 settings (the >= 2-donor sensitivity)")
BUILDS = {s.name: s for s in [
    Spec("primary-dk", "dk", "primary", (), _PRIMARY_READINGS, "V-DK at the §3.1 settings (+ counts)"),
    Spec("primary-aal", "aal", "primary", (), _PRIMARY_READINGS, "V-AAL at the §3.1 settings (+ counts)"),
    Spec("primary-mist64", "mist64", "primary", (), _PRIMARY_READINGS, "MIST64 at the §3.1 settings (+ counts)"),
    *_cells("dk"), *_cells("aal"),
    Spec("perdonor-dk", "dk", "perdonor", (("return_donors", True),),
         ("R12 (RUN_PLAN.md:699-700): per-donor V-DK matrices for DS",
          "R14 (RUN_PLAN.md:745-747): the per-donor parcel recipe on the claim's class dk-ctx (Leyhausen, Park)",
          "R31 (RUN_PLAN.md:1061-1065): Benkarim's per-donor recipe on dk-ctx"),
         "the six per-donor V-DK matrices (§3.1 settings, return_donors=True) + counts"),
    Spec("perdonor-aal", "aal", "perdonor", (("return_donors", True),),
         ("R14 (RUN_PLAN.md:745-747): the per-donor parcel recipe on the claim's class V-AAL (Segura, Pagani)",),
         "the six per-donor V-AAL matrices (§3.1 settings, return_donors=True) + counts"),
    Spec("r10-liu-dk-samples", "dk", "samples", (("region_agg", None),),
         ("R10 (RUN_PLAN.md:651-655): the T4 / T5 sample assignment",),
         "per-sample V-DK rows (region_agg=None, every other argument at §3.1), labelled by DK label"),
]}
DERIVED = {
    "r12-han-c1-ourpc1": dict(needs=("primary-dk", "perdonor-dk"),
                              readings=("R12 (RUN_PLAN.md:692-709): HAN-C1-ourPC1, our §3.1 gene PC1 (DS > .1)",),
                              what="DS on the per-donor V-DK matrices (34 left DK cortical parcels) and PC1 of the "
                                   "dk-ctx §3.1 matrix over the genes with DS > .1"),
    "r11-loo": dict(needs=("primary-dk", "primary-aal"),
                    readings=("R11 (RUN_PLAN.md:688-689): the leave-one-out matrices already exist (verified as A3 "
                              "did, arcs/replication/src/ahba_loo.py)",),
                    what="verification of A3's 12 LOO matrices (dk, aal) + their per-parcel counts"),
}
NOT_BUILT = {
    "perdonor-hcpmmp1": ("R14 (RUN_PLAN.md:738-739): Pretzsch's recipe runs on the paper's own 180 left Glasser parcels "
                         "through the pinned HCP-MMP1 MNI volume of R15, taken from figshare 3501911 with URL, bytes and "
                         "sha256 recorded (RUN_PLAN.md:757). The volume is not on this machine and this WP2 task may use "
                         "the network only for AHBA files abagen lacks; not built (R15's fetch first; then this build "
                         "with the volume's own label list and the §3.1 settings, return_donors=True)."),
}
ORDER = ["primary-dk", "primary-aal", "primary-mist64"] + [n for n in BUILDS if not n.startswith("primary-")]


class BuildError(AssertionError):
    """An apparatus check of a build failed (nothing downstream may use the build)."""


class NetworkBlocked(RuntimeError):
    """The build process tried to open a network connection."""


# ================================================================================================================
# small pure helpers (importable in env/venv by the tests)
# ================================================================================================================
def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def _ascii(s: str) -> str:
    """Console prints are ASCII (cp1252 console): the section sign as 's', anything else non-ASCII as '?'."""
    return str(s).replace("§", "s").encode("ascii", "replace").decode("ascii")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def frame_sha(df) -> str:
    """The L7 / R35 matrix identity: sha256 of hash_pandas_object(df, index=True) bytes (e4_ahba_matrices.sha)."""
    import pandas as pd

    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).to_numpy().tobytes()).hexdigest()


def read_frame(path, reader: str):
    import pandas as pd

    if reader == "round_trip":
        return pd.read_csv(path, index_col=0, float_precision="round_trip")
    if reader == "default":
        return pd.read_csv(path, index_col=0)
    raise ValueError(reader)


def gzip_header(raw: bytes) -> dict:
    """FNAME and MTIME of a gzip member header (RFC 1952 §2.3); only the header bytes are parsed."""
    if raw[:3] != b"\x1f\x8b\x08":
        raise BuildError("not a gzip (deflate) stream")
    flg = raw[3]
    mtime = struct.unpack("<I", raw[4:8])[0]
    pos, fname = 10, None
    if flg & 4:  # FEXTRA
        xlen = struct.unpack("<H", raw[pos:pos + 2])[0]
        pos += 2 + xlen
    if flg & 8:  # FNAME
        end = raw.index(b"\x00", pos)
        fname = raw[pos:end].decode("latin-1")
    return dict(mtime=int(mtime), fname=fname, xfl=int(raw[8]), os=int(raw[9]), flags=int(flg))


def csv_gz_bytes(df, name: str, mtime: int = 0) -> bytes:
    """This module's matrix writer, in memory: pandas' to_csv (its default float format and line terminator) through a
    gzip member with FNAME `name` minus '.gz', the given MTIME and compresslevel 9."""
    bio = io.BytesIO()
    with gzip.GzipFile(filename=name, mode="wb", fileobj=bio, compresslevel=9, mtime=int(mtime)) as gz:
        df.to_csv(gz, mode="wb", encoding="utf-8", compression=None)
    return bio.getvalue()


def write_csv_gz(df, path: Path, mtime: int = 0) -> None:
    """Write `df` as path (a .csv.gz) with a fixed gzip header (FNAME = the final name, MTIME 0): the bytes depend on
    the frame only. Written to a temporary name, then renamed."""
    path = Path(path)
    _guard_out(path)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as fh:
        with gzip.GzipFile(filename=path.name, mode="wb", fileobj=fh, compresslevel=9, mtime=int(mtime)) as gz:
            df.to_csv(gz, mode="wb", encoding="utf-8", compression=None)
    os.replace(tmp, path)


def write_text(path: Path, text: str) -> None:
    """UTF-8, written as given (newline='\\n' translates nothing); the bytes are read back and compared."""
    path = Path(path)
    _guard_out(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)
    if path.read_bytes() != text.encode("utf-8"):
        raise BuildError(f"{path.name}: read-back differs")


def write_json(path: Path, doc: dict) -> None:
    text = json.dumps(doc, indent=1, default=str, ensure_ascii=True) + "\n"
    write_text(path, text)
    if json.loads(Path(path).read_text(encoding="utf-8")) != json.loads(text):
        raise BuildError(f"{Path(path).name}: JSON read-back differs")


def _guard_out(path: Path) -> None:
    """Writes go under artifacts/ahba/a1_builds/ only (never over the primary artifacts/ahba files)."""
    p = Path(path).resolve()
    if OUT.resolve() not in p.parents:
        raise BuildError(f"refusing to write outside {OUT}: {p}")


def nan_max_abs_delta(a, b) -> float:
    """max |a - b| over positions finite in both; NaN positions must coincide (else inf)."""
    import numpy as np

    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape != b.shape:
        return float("inf")
    na, nb = np.isnan(a), np.isnan(b)
    if not np.array_equal(na, nb):
        return float("inf")
    if (~na).sum() == 0:
        return 0.0
    return float(np.max(np.abs(a[~na] - b[~na])))


def counts_table(counts, donors_used):
    """abagen's (parcels x donors) sample counts -> parcel-indexed table: n_samples, n_donors (donors with >= 1
    sample), then one column per donor named d<k> by the donor's position k (1-based) in DONORS. Donor columns are
    taken by position and their labels asserted in memory (never printed)."""
    import numpy as np
    import pandas as pd

    donors_used = [str(d) for d in donors_used]
    if counts.shape[1] != len(donors_used):
        raise BuildError(f"counts: {counts.shape[1]} donor columns for {len(donors_used)} donors")
    if [str(c) for c in counts.columns] != donors_used:
        raise BuildError("counts: donor columns are not in the donor order used")
    vals = counts.to_numpy()
    if not (np.isfinite(vals.astype(float)).all() and (vals >= 0).all()):
        raise BuildError("counts: non-finite or negative count")
    vals = vals.astype(np.int64)
    cols = ["d%d" % (DONORS.index(d) + 1) for d in donors_used]
    t = pd.DataFrame(vals, index=pd.Index(np.asarray(counts.index, dtype=np.int64), name="label"), columns=cols)
    t.insert(0, "n_donors", (t[cols] > 0).sum(axis=1).astype(np.int64))
    t.insert(0, "n_samples", t[cols].sum(axis=1).astype(np.int64))
    return t


def drop_donor_counts(table, left_out: str):
    """The per-parcel counts of a leave-one-donor-out cell: the primary per-donor counts without the left-out donor's
    column (sample-to-parcel assignment is per donor, so the remaining donors' counts are unchanged)."""
    col = "d%d" % (DONORS.index(str(left_out)) + 1)
    cols = [c for c in table.columns if c.startswith("d") and c != col]
    if len(cols) != len([c for c in table.columns if c.startswith("d")]) - 1:
        raise BuildError(f"drop_donor_counts: donor column {col} absent")
    t = table[cols].copy()
    t.insert(0, "n_donors", (t[cols] > 0).sum(axis=1).astype("int64"))
    t.insert(0, "n_samples", t[cols].sum(axis=1).astype("int64"))
    return t


def empty_rows(df) -> list:
    """Parcels whose row is all-NaN (no sample), as ints in index order."""
    return [int(i) for i in df.index[df.isna().all(axis=1)]]


def counts_match_empty(table, empty: list) -> bool:
    """A parcel has no sample in the counts iff its matrix row is empty."""
    zero = [int(i) for i in table.index[table["n_samples"] == 0]]
    return sorted(zero) == sorted(int(i) for i in empty)


def loo_donors_ok(donors, left_out) -> bool:
    """A leave-one-donor-out build drops exactly one donor: the six in DONORS order without `left_out`."""
    donors = [str(d) for d in donors]
    return (str(left_out) in DONORS and len(donors) == len(DONORS) - 1 and len(set(donors)) == len(donors)
            and set(DONORS) - set(donors) == {str(left_out)} and donors == [d for d in DONORS if d != str(left_out)])


def select_ds_genes(ds, genes, threshold: float = R12_THRESHOLD) -> list:
    """R12: the genes (in `genes` order) whose DS is strictly greater than the threshold ('DS > .1')."""
    return [g for g in genes if float(ds[g]) > threshold]


def apply_sign(score, loading, mean_expr):
    """prereg_amend_3.md:146: the PC sign makes corr(PC score, mean expression over genes) > 0. Returns (score,
    loading, r before, flipped)."""
    import numpy as np

    score = np.asarray(score, dtype=float)
    loading = np.asarray(loading, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        r = float(np.corrcoef(score, np.asarray(mean_expr, dtype=float))[0, 1])
    if not np.isfinite(r) or r == 0.0:
        raise BuildError("PC sign undefined: corr(PC score, mean expression) is 0 or not finite")
    if r < 0:
        return -score, -loading, r, True
    return score, loading, r, False


def check_primary(atlas: str, obs: dict) -> dict:
    """The primary-reproduction check (RUN_PLAN L6 / L7, amend_1 R35) on observed values; returns {check: bool}.
    `obs` keys: sha256_inmemory, sha256_round_trip, sha256_default, l6_rewrite_sha256, content_equal,
    empty_parcels, expected_empty, n_genes, nii_sha256, info_sha256, settings."""
    c = {
        "L7: in-memory frame hash == pin": obs.get("sha256_inmemory") == L7_PINS[atlas],
        "L7: round-trip read of the written file == pin": obs.get("sha256_round_trip") == L7_PINS[atlas],
        "R35: default-reader read of the written file == pin": obs.get("sha256_default") == R35_DEFAULT_PINS[atlas],
        "L6: rewrite with the pinned gzip header == the pinned file sha256": obs.get("l6_rewrite_sha256") == L6_PINS[atlas][1],
        "L6: decompressed content == the pinned file's": obs.get("content_equal") is True,
        "empty parcels == the committed meta's": obs.get("empty_parcels") == obs.get("expected_empty")
        and obs.get("expected_empty") is not None,
        "n_genes == 15,633": obs.get("n_genes") == N_GENES_PRIMARY,
        "atlas volume sha256 == pin": obs.get("nii_sha256") == ATLAS[atlas]["nii_sha256"],
        "atlas_info sha256 == pin": obs.get("info_sha256") == ATLAS[atlas]["info_sha256"],
        "settings == the frozen §3.1 settings": obs.get("settings") == FROZEN,
    }
    return c


RECORD_KEYS = ("build", "kind", "atlas", "readings", "what", "environment", "inputs", "atlas_files", "abagen_call",
               "outputs", "checks", "ok", "timing", "started", "finished")
OUTPUT_KEYS = ("file", "role", "bytes", "sha256")
MATRIX_KEYS = ("shape", "sha256_inmemory", "sha256_round_trip", "sha256_default", "readback_max_abs_delta",
               "default_vs_round_trip_max_abs_delta")


def record_missing(rec: dict) -> list:
    """Keys a build record lacks (the completeness rule of the tests and the manifest)."""
    miss = [k for k in RECORD_KEYS if k not in rec]
    for i, o in enumerate(rec.get("outputs") or []):
        miss += ["outputs[%d].%s" % (i, k) for k in OUTPUT_KEYS if k not in o]
        if o.get("role") in ("matrix", "counts", "table"):
            miss += ["outputs[%d].%s" % (i, k) for k in MATRIX_KEYS if k not in o]
    if rec.get("kind") in ("primary", "cell", "perdonor", "samples"):
        call = rec.get("abagen_call") or {}
        for k in list(FROZEN) + list(CALL_REST) + ["atlas", "atlas_info", "return_counts", "return_report"]:
            if k not in call:
                miss.append("abagen_call.%s" % k)
    return miss


# ================================================================================================================
# environment, inputs
# ================================================================================================================
def _git(*args) -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def environment() -> dict:
    import numpy as np
    import pandas as pd

    env = dict(python=sys.executable, python_version=sys.version.split()[0], pandas=pd.__version__,
               numpy=np.__version__, script=REL_SCRIPT, script_sha256=sha256_file(Path(__file__)),
               script_git=_git("status", "--porcelain", "--", str(Path(__file__))) or "clean",
               commit=_git("rev-parse", "HEAD"), blas_threads={v: os.environ.get(v) for v in
                                                              ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                                                               "MKL_NUM_THREADS")})
    for mod in ("abagen", "nibabel", "scipy", "sklearn"):
        try:
            env[mod] = __import__(mod).__version__
        except Exception:  # noqa: BLE001
            env[mod] = None
    try:
        import abagen

        pkg = Path(abagen.__file__).resolve().parent
        h = hashlib.sha256()
        for f in sorted(pkg.rglob("*.py")):
            h.update(f.relative_to(pkg).as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
        env["abagen_code_sha256"] = h.hexdigest()
    except Exception:  # noqa: BLE001
        env["abagen_code_sha256"] = None
    return env


ENV_SAME = ("python_version", "pandas", "numpy", "abagen", "nibabel", "scipy", "abagen_code_sha256", "script_sha256")


def _abagen_data(name: str) -> Path:
    import abagen

    return Path(abagen.__file__).resolve().parent / "data" / name


def input_files() -> list:
    """Every file the builds read: the AHBA files abagen reads for the six donors, abagen's bundled data the §3.1
    settings use, the atlas volumes and the pinned atlas_info CSVs (paths as recorded)."""
    out = []
    for d in DONORS:
        for f in AHBA_FILES:
            out.append(("ahba", DATA_AHBA / "microarray" / f"normalized_microarray_donor{d}" / f))
    for f in ("atlas-desikankilliany.nii.gz", "atlas-desikankilliany.csv", "reannotated.csv.gz",
              "corrected_mni_coordinates.csv.gz", "donor_info.csv"):
        out.append(("abagen-data", _abagen_data(f)))
    for a in ("aal", "mist64"):
        out.append(("atlas", Path(ATLAS[a]["nii"])))
    for a in ATLAS:
        out.append(("atlas_info", ROOT / ATLAS[a]["info"]))
    return out


def _rel(p: Path) -> str:
    p = Path(p).resolve()
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        try:
            import abagen

            return "abagen-data:" + p.relative_to(Path(abagen.__file__).resolve().parent / "data").as_posix()
        except Exception:  # noqa: BLE001
            return p.as_posix()


def hash_inputs(log=print) -> dict:
    t0 = time.time()
    files = []
    for kind, p in input_files():
        st = p.stat()
        files.append(dict(kind=kind, path=_rel(p), bytes=int(st.st_size), mtime_ns=int(st.st_mtime_ns),
                          sha256=sha256_file(p)))
    doc = dict(what="sha256 of every input file of the A1 WP2 AHBA builds", files=files,
               hashed=_dt.datetime.now().isoformat(timespec="seconds"), seconds=round(time.time() - t0, 1),
               environment=environment())
    log(f"  hashed {len(files)} input files ({sum(f['bytes'] for f in files) / 2**30:.2f} GiB) in "
        f"{doc['seconds']:.0f}s")
    return doc


def cmd_inputs(log=print) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    doc = hash_inputs(log)
    for f in doc["files"]:
        for a, spec in ATLAS.items():
            if f["path"] in (spec["info"],) and f["sha256"] != spec["info_sha256"]:
                raise BuildError(f"{f['path']}: sha256 != pin")
    write_json(INPUTS_JSON, doc)
    log(f"  {INPUTS_JSON.relative_to(ROOT).as_posix()} written (sha256 {sha256_file(INPUTS_JSON)})")
    return doc


def verified_inputs() -> dict:
    """inputs.json with every file's size and mtime re-checked now (a change means re-run `inputs`)."""
    if not INPUTS_JSON.exists():
        raise BuildError("no inputs.json: run `inputs` first")
    doc = json.loads(INPUTS_JSON.read_text(encoding="utf-8"))
    want = {_rel(p) for _, p in input_files()}
    have = {f["path"] for f in doc["files"]}
    if want != have:
        raise BuildError("inputs.json does not list this script's input files")
    for kind, p in input_files():
        f = next(x for x in doc["files"] if x["path"] == _rel(p))
        st = p.stat()
        if int(st.st_size) != f["bytes"] or int(st.st_mtime_ns) != f["mtime_ns"]:
            raise BuildError(f"{f['path']}: size / mtime changed since inputs.json was hashed")
    return dict(inputs_json=INPUTS_JSON.relative_to(ROOT).as_posix(), inputs_json_sha256=sha256_file(INPUTS_JSON),
                hashed=doc["hashed"], verified="size and mtime_ns of every file equal inputs.json's at build time; "
                "re-hashed by `manifest`", files=[{k: f[k] for k in ("kind", "path", "bytes", "sha256")}
                                                 for f in doc["files"]])


def frozen_from_e4() -> dict:
    """The FROZEN literal of arcs/audit/src/e4_ahba_matrices.py, parsed (not imported)."""
    tree = ast.parse(E4_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "FROZEN" for t in node.targets):
            call = node.value
            return {kw.arg: ast.literal_eval(kw.value) for kw in call.keywords}
    raise BuildError("FROZEN not found in e4_ahba_matrices.py")


def committed_primary_meta(atlas: str) -> dict:
    """The committed primary record: results/e4_ahba_matrices.json (dk, aal) / register_maps/mist64_ahba_matrix.json."""
    if atlas in ("dk", "aal"):
        m = json.loads(E4_JSON.read_text(encoding="utf-8"))[atlas]
    else:
        m = json.loads(MIST64_JSON.read_text(encoding="utf-8"))
    if m["sha256_matrix"] != L7_PINS[atlas]:
        raise BuildError(f"{atlas}: the committed meta's sha256_matrix is not the L7 pin")
    return dict(empty_parcels=[int(i) for i in m["empty_parcels"]], n_genes=int(m["n_genes"]),
                n_parcels=int(m["n_parcels"]), source=(E4_JSON if atlas != "mist64" else MIST64_JSON)
                .relative_to(ROOT).as_posix())


# ================================================================================================================
# the build process
# ================================================================================================================
def block_network() -> None:
    """No network in a build process: every socket connection is refused (abagen would otherwise fetch missing AHBA
    files silently; the task requires stopping and asking first)."""
    import socket

    def _refuse(*a, **k):
        raise NetworkBlocked("ahba_builds: a network connection was attempted (refused; no AHBA file may be fetched "
                             "without the orchestrator)")

    socket.socket.connect = _refuse
    socket.socket.connect_ex = _refuse
    socket.create_connection = _refuse


def _kernel32():
    """A private kernel32 handle with typed prototypes (ctypes.windll's shared function objects are left untouched)."""
    import ctypes
    from ctypes import wintypes

    k = ctypes.WinDLL("kernel32")
    k.GetCurrentProcess.restype = wintypes.HANDLE
    k.GetCurrentProcess.argtypes = []
    k.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    k.SetPriorityClass.restype = wintypes.BOOL
    return k


def below_normal() -> None:
    """The machine is shared: BelowNormal priority (Windows), as A3's ahba_loo_extra.py."""
    if sys.platform == "win32":
        k = _kernel32()
        k.SetPriorityClass(k.GetCurrentProcess(), 0x4000)


def peak_rss_mib():
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        fn = ctypes.WinDLL("psapi").GetProcessMemoryInfo
        fn.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
        fn.restype = wintypes.BOOL
        if fn(_kernel32().GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
            return int(pmc.PeakWorkingSetSize // 2**20)
    except Exception:  # noqa: BLE001
        return None
    return None


def load_atlas(atlas: str):
    """The frozen builders' atlas image and atlas_info (copied recipes; pins asserted). Returns (img, info, record)."""
    import nibabel as nib
    import numpy as np
    import pandas as pd

    a = ATLAS[atlas]
    nii = _abagen_data("atlas-desikankilliany.nii.gz") if atlas == "dk" else Path(a["nii"])
    nii_sha = sha256_file(nii)
    if nii_sha != a["nii_sha256"]:
        raise BuildError(f"{atlas}: atlas volume sha256 {nii_sha[:16]}.. != pin {a['nii_sha256'][:16]}..")
    info_p = ROOT / a["info"]
    info_sha = sha256_file(info_p)
    if info_sha != a["info_sha256"]:
        raise BuildError(f"{atlas}: atlas_info sha256 {info_sha[:16]}.. != pin")
    info = pd.read_csv(info_p)
    if list(info.columns) != ["id", "label", "hemisphere", "structure"] or not info["id"].is_unique:
        raise BuildError(f"{atlas}: atlas_info columns / ids")
    rec = dict(volume=_rel(nii), volume_sha256=nii_sha, volume_pin_source=a["nii_pin_source"], atlas_info=a["info"],
               atlas_info_sha256=info_sha, recipe=a["recipe"], classes=list(a["classes"]))
    if atlas == "dk":
        ab_info = _abagen_data("atlas-desikankilliany.csv")
        ab = pd.read_csv(ab_info)
        pd.testing.assert_frame_equal(info, ab)  # e4 passed abagen's own CSV; the pinned CSV is that frame
        rec["abagen_info"] = _rel(ab_info)
        rec["abagen_info_sha256"] = sha256_file(ab_info)
        rec["abagen_info_equals_pinned_info"] = True
        img = nib.load(str(nii))
    elif atlas == "aal":
        img = nib.load(str(nii))
    else:  # mist64: src_register/mist64_classes.load_int_atlas, copied
        img0 = nib.load(str(nii))
        d = np.asarray(img0.dataobj)
        if not (np.all(np.isfinite(d)) and np.all(d == np.round(d))):
            raise BuildError("mist64: non-integral labels")
        img = nib.Nifti1Image(d.astype(np.int32), img0.affine)
        img.set_qform(img0.affine, code=1)
        img.set_sform(img0.affine, code=1)
    ids = sorted(int(i) for i in np.unique(np.asarray(img.dataobj)) if i != 0)
    if ids != sorted(int(i) for i in info["id"]):
        raise BuildError(f"{atlas}: the volume's labels are not the atlas_info ids")
    rec["n_labels"] = len(ids)
    return img, info, rec


def abagen_call(spec: Spec, atlas_rec: dict) -> dict:
    """Every get_expression_data argument for this build (FROZEN, the build's overrides, the rest at the recipe's
    values); asserted to cover abagen's signature."""
    import inspect

    import abagen

    if frozen_from_e4() != FROZEN:
        raise BuildError("FROZEN differs from e4_ahba_matrices.py's literal")
    kw = dict(FROZEN)
    for k, v in spec.overrides:
        if k not in FROZEN:
            raise BuildError(f"{spec.name}: override {k} is not a §3.1 argument")
        kw[k] = v
    kw.update(CALL_REST)
    if spec.kind == "samples":  # allen.py:517-525 returns before counts and report when region_agg is None
        kw.update(return_counts=False, return_report=False)
    else:
        kw.update(return_counts=True, return_report=True)
    params = set(inspect.signature(abagen.get_expression_data).parameters)
    if set(kw) | {"atlas", "atlas_info"} != params:
        raise BuildError(f"abagen signature not covered: {sorted(params ^ (set(kw) | {'atlas', 'atlas_info'}))}")
    return kw


def matrix_output(df, path: Path, role: str = "matrix", donor=None, write=True) -> dict:
    """Write (fixed gzip header) and read back with both readers: the round-trip read must hash as the in-memory frame
    (an exact round trip; A4's max |delta| < 1e-12 asserted too) and keep index and columns."""
    import numpy as np
    import pandas as pd

    if write:
        write_csv_gz(df, path)
    rt = read_frame(path, "round_trip")
    dflt = read_frame(path, "default")
    if rt.shape != df.shape or list(map(str, rt.columns)) != list(map(str, df.columns)):
        raise BuildError(f"{path.name}: read-back shape / columns differ")
    if not np.array_equal(np.asarray(rt.index), np.asarray(df.index)):
        raise BuildError(f"{path.name}: read-back index differs")
    if list(dflt.columns) != list(rt.columns) or not np.array_equal(np.asarray(dflt.index), np.asarray(rt.index)):
        raise BuildError(f"{path.name}: the two readers' index / column order differ")
    d_rb = nan_max_abs_delta(rt.to_numpy(dtype=float), df.to_numpy(dtype=float))
    d_rd = nan_max_abs_delta(dflt.to_numpy(dtype=float), rt.to_numpy(dtype=float))
    h_mem, h_rt, h_def = frame_sha(df), frame_sha(rt), frame_sha(dflt)
    if not d_rb < READBACK_TOL:
        raise BuildError(f"{path.name}: read-back max |delta| {d_rb} (A4)")
    if h_rt != h_mem:
        raise BuildError(f"{path.name}: the round-trip read does not hash as the in-memory frame")
    if not d_rd < READBACK_TOL:
        raise BuildError(f"{path.name}: default vs round-trip reader max |delta| {d_rd} (R35)")
    with open(path, "rb") as fh:
        head = fh.read(512)
    out = dict(file=path.name, role=role, bytes=path.stat().st_size, sha256=sha256_file(path),
               shape=[int(x) for x in df.shape], sha256_inmemory=h_mem, sha256_round_trip=h_rt, sha256_default=h_def,
               readback_max_abs_delta=d_rb, default_vs_round_trip_max_abs_delta=d_rd,
               gzip=gzip_header(head) if path.suffix == ".gz" else None)
    if donor is not None:
        out["donor"] = donor
    del rt, dflt
    _ = pd  # noqa: F841
    return out


def existing_matrix(path: Path) -> tuple:
    """A matrix this module did not build (A3's LOO files): both readers' hashes, their max |delta| (R35) and the
    file's sha256. Returns (record, round-trip frame)."""
    rt = read_frame(path, "round_trip")
    dflt = read_frame(path, "default")
    if list(dflt.columns) != list(rt.columns) or not dflt.index.equals(rt.index):
        raise BuildError(f"{path.name}: the two readers' index / column order differ")
    d_rd = nan_max_abs_delta(dflt.to_numpy(dtype=float), rt.to_numpy(dtype=float))
    if not d_rd < READBACK_TOL:
        raise BuildError(f"{path.name}: default vs round-trip reader max |delta| {d_rd} (R35)")
    rec = dict(file=_rel(path), bytes=path.stat().st_size, sha256=sha256_file(path), shape=[int(x) for x in rt.shape],
               sha256_round_trip=frame_sha(rt), sha256_default=frame_sha(dflt), default_vs_round_trip_max_abs_delta=d_rd)
    del dflt
    return rec, rt


def table_output(df, path: Path, role: str) -> dict:
    """A small table as LF CSV (counts, DS, PC1): written, read back with both readers, hashed."""
    import numpy as np

    _guard_out(path)
    tmp = path.with_name(path.name + ".tmp")
    df.to_csv(tmp, lineterminator="\n", encoding="utf-8")
    os.replace(tmp, path)
    rt, dflt = read_frame(path, "round_trip"), read_frame(path, "default")
    if rt.shape != df.shape or list(map(str, rt.columns)) != list(map(str, df.columns)) or \
            [str(i) for i in rt.index] != [str(i) for i in df.index]:
        raise BuildError(f"{path.name}: read-back shape / labels differ")
    num = [c for c in df.columns if np.issubdtype(df[c].dtype, np.number)]
    d_rb = nan_max_abs_delta(rt[num].to_numpy(dtype=float), df[num].to_numpy(dtype=float)) if num else 0.0
    d_rd = nan_max_abs_delta(dflt[num].to_numpy(dtype=float), rt[num].to_numpy(dtype=float)) if num else 0.0
    if not (d_rb < READBACK_TOL and d_rd < READBACK_TOL):
        raise BuildError(f"{path.name}: read-back max |delta| {d_rb} / {d_rd}")
    return dict(file=path.name, role=role, bytes=path.stat().st_size, sha256=sha256_file(path),
                shape=[int(x) for x in df.shape], sha256_inmemory=frame_sha(df), sha256_round_trip=frame_sha(rt),
                sha256_default=frame_sha(dflt), readback_max_abs_delta=d_rb, default_vs_round_trip_max_abs_delta=d_rd)


def _as_float(df):
    import numpy as np

    if all(np.dtype(t) == np.float64 for t in df.dtypes):
        return df, False
    return df.astype(np.float64), True


def _a3_assertions(expr, name: str) -> list:
    """prereg §3.1 A3 (e4_ahba_matrices.run): no all-NaN gene column; nothing NaN outside the empty parcels."""
    empty = empty_rows(expr)
    if expr.isna().all(axis=0).any():
        raise BuildError(f"{name}: an all-NaN gene column (A3)")
    if expr.drop(index=empty).isna().any().any():
        raise BuildError(f"{name}: NaN outside the empty parcels (A3)")
    return empty


def load_record(name: str) -> dict:
    p = OUT / name / RECORD
    if not p.exists():
        raise BuildError(f"{name}: no build record")
    return json.loads(p.read_text(encoding="utf-8"))


def require_primary(atlas: str, env: dict) -> dict:
    """A non-primary build of `atlas` starts only after its primary check passed in this environment and script."""
    rec = load_record(f"primary-{atlas}")
    if rec.get("ok") is not True or rec.get("checks", {}).get("primary_reproduction", {}).get("reproduces") is not True:
        raise BuildError(f"primary-{atlas}: the primary-reproduction check did not pass; nothing else is built")
    bad = [k for k in ENV_SAME if rec["environment"].get(k) != env.get(k)]
    if bad:
        raise BuildError(f"primary-{atlas} was built in another environment / script ({bad}); rebuild it first")
    return rec


def primary_counts(atlas: str):
    rec = load_record(f"primary-{atlas}")
    o = next(x for x in rec["outputs"] if x["role"] == "counts")
    p = OUT / f"primary-{atlas}" / o["file"]
    if sha256_file(p) != o["sha256"]:
        raise BuildError(f"{p.name}: sha256 differs from its record")
    return read_frame(p, "round_trip")


def pinned_primary(atlas: str):
    """The committed primary matrix (artifacts/ahba/<atlas>_expr.csv.gz), L7 hash asserted on a round-trip read."""
    path = AHBA / L6_PINS[atlas][0]
    if sha256_file(path) != L6_PINS[atlas][1]:
        raise BuildError(f"{path.name}: raw sha256 != the L6 pin")
    df = read_frame(path, "round_trip")
    if frame_sha(df) != L7_PINS[atlas]:
        raise BuildError(f"{path.name}: round-trip hash != the L7 pin")
    return df


def run_build(name: str, log=print) -> dict:
    """One abagen build (BUILDS[name]) with its checks; writes <build>/ and its record. Raises BuildError on a failed
    check (the record is written with ok False first)."""
    import abagen
    import numpy as np
    import pandas as pd

    import warnings

    # abagen 0.1.3 on pandas 1.5.3 emits FutureWarnings (DataFrame.append, set_axis inplace); output only
    warnings.filterwarnings("ignore", category=FutureWarning, module=r"abagen(\..*)?$")
    spec = BUILDS[name]
    block_network()
    below_normal()
    started = _dt.datetime.now().isoformat(timespec="seconds")
    t_all = time.time()
    env = environment()
    if spec.kind != "primary":
        require_primary(spec.atlas, env)
    inputs = verified_inputs()
    bdir = OUT / name
    bdir.mkdir(parents=True, exist_ok=True)
    img, info, atlas_rec = load_atlas(spec.atlas)
    kw = abagen_call(spec, atlas_rec)
    files = abagen.fetch_microarray(data_dir=str(DATA_AHBA), donors="all", verbose=0)
    if tuple(files) != DONORS:
        raise BuildError(f"donors {tuple(files)} != {DONORS}")
    log(f"  {name}: abagen.get_expression_data({spec.atlas}, {dict(spec.overrides)}) ...")
    t0 = time.time()
    out = abagen.get_expression_data(img, atlas_info=info, **kw)
    t_abagen = time.time() - t0
    t1 = time.time()
    outputs, checks = [], {}
    stem = spec.atlas
    if spec.kind in ("primary", "cell"):
        expr, counts, report = out
        expr, cast = _as_float(expr)
        empty = _a3_assertions(expr, name)
        outputs.append(matrix_output(expr, bdir / f"{stem}_expr.csv.gz"))
        ct = counts_table(counts, DONORS)
        if list(ct.index) != [int(i) for i in expr.index]:
            raise BuildError(f"{name}: counts index != matrix index")
        outputs.append(table_output(ct, bdir / f"{stem}_counts.csv", "counts"))
        write_text(bdir / f"{stem}_report.txt", report)
        outputs.append(dict(file=f"{stem}_report.txt", role="report", bytes=(bdir / f"{stem}_report.txt").stat().st_size,
                            sha256=sha256_file(bdir / f"{stem}_report.txt")))
        checks["cast_to_float64"] = cast
        checks["n_parcels"], checks["n_genes"] = int(expr.shape[0]), int(expr.shape[1])
        checks["empty_parcels"] = empty
        checks["counts: zero-sample parcels == empty matrix rows"] = counts_match_empty(ct, empty)
        checks["n_parcels_with_samples"] = int((ct["n_samples"] > 0).sum())
        checks["n_parcels_with_ge2_donors"] = int((ct["n_donors"] >= 2).sum())
        if spec.kind == "primary":
            checks["primary_reproduction"] = primary_check(spec.atlas, expr, bdir / f"{stem}_expr.csv.gz",
                                                           outputs[0], empty, atlas_rec, {k: kw[k] for k in FROZEN})
        else:
            pc = primary_counts(spec.atlas)
            same = bool(pc.equals(ct))
            checks["counts == primary counts"] = same
            if spec.overrides and dict(spec.overrides).get("lr_mirror") is None:
                # gene_norm / norm_matched do not change the sample-to-parcel assignment (allen.py:474-493)
                if not same:
                    raise BuildError(f"{name}: counts differ from the primary build's (a normalisation cell)")
            else:
                checks["parcels gaining samples vs primary"] = [int(i) for i in ct.index
                                                               if ct.loc[i, "n_samples"] > 0 and pc.loc[i, "n_samples"] == 0]
                checks["parcels losing samples vs primary"] = [int(i) for i in ct.index
                                                              if ct.loc[i, "n_samples"] == 0 and pc.loc[i, "n_samples"] > 0]
        if not checks["counts: zero-sample parcels == empty matrix rows"]:
            raise BuildError(f"{name}: counts and empty rows disagree")
    elif spec.kind == "perdonor":
        per, counts, report = out
        if list(per) != list(DONORS):
            raise BuildError(f"{name}: per-donor keys != DONORS")
        ct = counts_table(counts, DONORS)
        frames, casts = {}, {}
        for k, d in enumerate(DONORS, start=1):
            f, cast = _as_float(per[d])
            casts[d] = cast
            if [int(i) for i in f.index] != list(ct.index):
                raise BuildError(f"{name}: donor d{k} index != counts index")
            emp = empty_rows(f)
            zero = [int(i) for i in ct.index[ct[f"d{k}"] == 0]]
            if sorted(emp) != sorted(zero):
                raise BuildError(f"{name}: donor d{k}: empty rows != parcels with no sample of that donor")
            frames[d] = f
            outputs.append(matrix_output(f, bdir / f"{stem}_donor-{d}_expr.csv.gz", donor=d))
        outputs.append(table_output(ct, bdir / f"{stem}_counts.csv", "counts"))
        write_text(bdir / f"{stem}_report.txt", report)
        outputs.append(dict(file=f"{stem}_report.txt", role="report", bytes=(bdir / f"{stem}_report.txt").stat().st_size,
                            sha256=sha256_file(bdir / f"{stem}_report.txt")))
        cols = list(frames[DONORS[0]].columns)
        if any(list(frames[d].columns) != cols for d in DONORS):
            raise BuildError(f"{name}: per-donor gene columns differ across donors")
        prim = pinned_primary(spec.atlas)
        if not set(prim.columns) <= set(cols):
            raise BuildError(f"{name}: the primary's genes are not a subset of the per-donor genes")
        mean = pd.concat([frames[d][list(prim.columns)] for d in DONORS]).groupby(level=0).mean()
        mean = mean.loc[prim.index]
        dmean = nan_max_abs_delta(mean.to_numpy(), prim.to_numpy())
        checks["cast_to_float64"] = casts
        checks["n_parcels"], checks["n_genes_per_donor"] = int(len(ct)), len(cols)
        checks["n_genes_primary"] = int(prim.shape[1])
        checks["donor mean over the primary's genes vs the pinned primary: max |delta|"] = dmean
        checks["counts == primary counts"] = bool(primary_counts(spec.atlas).equals(ct))
        checks["n_all_nan_gene_columns_per_donor"] = {d: int(frames[d].isna().all(axis=0).sum()) for d in DONORS}
        if not dmean < READBACK_TOL:
            raise BuildError(f"{name}: the donor mean is not the pinned primary matrix (max |delta| {dmean})")
        if not checks["counts == primary counts"]:
            raise BuildError(f"{name}: counts differ from the primary build's")
    elif spec.kind == "samples":
        df = out
        if not isinstance(df, pd.DataFrame) or df.index.nlevels != 2 or list(df.index.names) != ["label", "well_id"]:
            raise BuildError(f"{name}: abagen did not return a (label, well_id)-indexed frame")
        lab = np.asarray(df.index.get_level_values("label"), dtype=np.int64)
        df.index = pd.Index(lab, name="label")  # the AHBA sample (well) ids leave the frame here (RUN_PLAN.md:653-655)
        df, cast = _as_float(df)
        ids = set(int(i) for i in info["id"])
        if not set(int(x) for x in np.unique(lab)) <= ids:
            raise BuildError(f"{name}: a sample label is not a DK id")
        outputs.append(matrix_output(df, bdir / f"{stem}_samples_expr.csv.gz", role="matrix"))
        pc = primary_counts(spec.atlas)
        per_label = pd.Series(lab).value_counts().reindex(pc.index, fill_value=0).astype(np.int64)
        checks["cast_to_float64"] = cast
        checks["n_samples"] = int(df.shape[0])
        checks["n_columns"] = int(df.shape[1])
        checks["n_columns_with_any_nan"] = int(df.isna().any(axis=0).sum())
        checks["n_labels_with_samples"] = int((per_label > 0).sum())
        checks["samples per label == primary counts n_samples"] = bool((per_label.to_numpy() ==
                                                                          pc["n_samples"].to_numpy()).all())
        checks["well ids saved"] = False
        checks["report"] = "not produced: abagen returns before the report when region_agg is None (allen.py:517-525)"
        if not checks["samples per label == primary counts n_samples"]:
            raise BuildError(f"{name}: samples per label differ from the primary counts")
    else:
        raise BuildError(spec.kind)
    t_write = time.time() - t1
    ok = True
    if spec.kind == "primary":
        ok = checks["primary_reproduction"]["reproduces"]
    call_rec = dict(kw)
    call_rec["atlas"] = atlas_rec["volume"] + " (sha256 %s)" % atlas_rec["volume_sha256"]
    call_rec["atlas_info"] = atlas_rec["atlas_info"] + " (sha256 %s)" % atlas_rec["atlas_info_sha256"]
    rec = dict(build=name, kind=spec.kind, atlas=spec.atlas, readings=list(spec.readings), what=spec.what,
               overrides=dict(spec.overrides), environment=env, inputs=inputs, atlas_files=atlas_rec,
               abagen_call=call_rec, outputs=outputs, checks=checks, ok=bool(ok),
               timing=dict(abagen_seconds=round(t_abagen, 1), write_and_check_seconds=round(t_write, 1),
                           total_seconds=round(time.time() - t_all, 1), peak_working_set_mib=peak_rss_mib()),
               started=started, finished=_dt.datetime.now().isoformat(timespec="seconds"),
               readers=READERS, hash_rule=HASH_RULE, donor_columns="d<k> = the k-th donor of %s" % list(DONORS))
    write_json(bdir / RECORD, rec)
    log(f"  {name}: {'ok' if ok else 'FAILED'}; abagen {t_abagen:.0f}s, write+check {t_write:.0f}s; "
        f"{len(outputs)} output files")
    if not ok:
        raise BuildError(_ascii(f"{name}: the primary-reproduction check failed: "
                         f"{[k for k, v in checks['primary_reproduction']['checks'].items() if not v]}"))
    return rec


def primary_check(atlas: str, expr, path: Path, out_rec: dict, empty: list, atlas_rec: dict, settings: dict) -> dict:
    """RUN_PLAN L6 / L7, amend_1 R35 on a primary rebuild (see check_primary); a planted failure is run first and must
    be caught. `settings` = the §3.1 arguments the call actually used."""
    pinned_path = AHBA / L6_PINS[atlas][0]
    raw = pinned_path.read_bytes()
    if sha256_bytes(raw) != L6_PINS[atlas][1]:
        raise BuildError(f"{pinned_path.name}: the pinned file's own sha256 is not the L6 pin")
    hdr = gzip_header(raw[:512])
    rewrite = csv_gz_bytes(expr, hdr["fname"] + ".gz", hdr["mtime"])
    content_equal = gzip.decompress(path.read_bytes()) == gzip.decompress(raw)
    meta = committed_primary_meta(atlas)
    art_meta = json.loads((AHBA / f"{atlas}_meta.json").read_text(encoding="utf-8"))
    if art_meta.get("settings") != FROZEN or frozen_from_e4() != FROZEN:
        raise BuildError(f"{atlas}: the primary meta's / e4's settings are not FROZEN")
    obs = dict(sha256_inmemory=out_rec["sha256_inmemory"], sha256_round_trip=out_rec["sha256_round_trip"],
               sha256_default=out_rec["sha256_default"], l6_rewrite_sha256=sha256_bytes(rewrite),
               content_equal=content_equal, empty_parcels=empty, expected_empty=meta["empty_parcels"],
               n_genes=int(expr.shape[1]), nii_sha256=atlas_rec["volume_sha256"],
               info_sha256=atlas_rec["atlas_info_sha256"], settings=dict(settings))
    # planted failure: the same observations with the in-memory hash altered must fail the check
    planted = dict(obs, sha256_inmemory=("0" if obs["sha256_inmemory"][0] != "0" else "1") + obs["sha256_inmemory"][1:])
    if all(check_primary(atlas, planted).values()):
        raise BuildError("the primary check passed a planted wrong hash")
    c = check_primary(atlas, obs)
    rep_new, rep_old = path.with_name(f"{atlas}_report.txt"), AHBA / f"{atlas}_report.txt"
    report_equal = (rep_new.read_bytes() == rep_old.read_bytes()) if rep_new.exists() and rep_old.exists() else None
    return dict(reproduces=bool(all(c.values())), checks=c, observed=obs, pinned_file=pinned_path.relative_to(ROOT)
                .as_posix(), pinned_gzip_header=hdr, committed_meta=meta["source"],
                planted_wrong_hash_caught=True,
                report_equals_primary_report=report_equal,
                report_note="recorded beside the check (abagen's report is not pinned by L6 / L7)",
                l6_note=("L6 is reproduced byte for byte by re-writing the rebuilt frame with the pinned file's gzip "
                         "header (FNAME, MTIME); this build's own file carries MTIME 0, so its sha256 differs from L6 "
                         "while its decompressed content is the pinned file's"))


# ================================================================================================================
# derived builds
# ================================================================================================================
def _output_path(build: str, out: dict) -> Path:
    p = OUT / build / out["file"]
    if sha256_file(p) != out["sha256"]:
        raise BuildError(f"{build}/{out['file']}: sha256 differs from its record")
    return p


def derive_r12(log=print) -> dict:
    """R12: DS on the per-donor V-DK matrices (34 left DK cortical parcels) and PC1 of the dk-ctx §3.1 matrix over the
    genes with DS > .1."""
    import numpy as np
    import pandas as pd
    import sklearn
    from abagen import correct
    from sklearn.decomposition import PCA

    name = "r12-han-c1-ourpc1"
    started = _dt.datetime.now().isoformat(timespec="seconds")
    t0 = time.time()
    env = environment()
    require_primary("dk", env)
    pd_rec = load_record("perdonor-dk")
    if pd_rec.get("ok") is not True or any(pd_rec["environment"].get(k) != env.get(k) for k in ENV_SAME):
        raise BuildError("perdonor-dk: not ok or another environment / script")
    info = pd.read_csv(ROOT / ATLAS["dk"]["info"])
    ids34 = [int(i) for i in info.loc[(info["hemisphere"] == "L") & (info["structure"] == "cortex"), "id"]]
    if len(ids34) != 34:
        raise BuildError(f"dk-ctx: {len(ids34)} left cortical DK parcels, not 34")
    frames = []
    used = []
    for d in DONORS:
        o = next(x for x in pd_rec["outputs"] if x.get("donor") == d)
        p = _output_path("perdonor-dk", o)
        f = read_frame(p, "round_trip")
        if frame_sha(f) != o["sha256_round_trip"]:
            raise BuildError(f"{p.name}: round-trip hash != its record")
        frames.append(f.loc[ids34])
        used.append(dict(file=f"perdonor-dk/{o['file']}", sha256=o["sha256"], sha256_round_trip=o["sha256_round_trip"]))
    genes_pd = list(frames[0].columns)
    _, ds = correct.keep_stable_genes(frames, threshold=R12_THRESHOLD, percentile=False, rank=True,
                                      return_stability=True)
    ds = pd.Series(np.asarray(ds, dtype=float), index=pd.Index(genes_pd, name="gene_symbol"), name="ds")
    if len(ds) != len(genes_pd) or not np.isfinite(ds.to_numpy()).all():
        raise BuildError("DS: length / finiteness")
    prim = pinned_primary("dk").loc[ids34]
    if prim.isna().any().any():
        raise BuildError("dk-ctx: a NaN in the §3.1 matrix's 34 left cortical rows")
    if not set(prim.columns) <= set(genes_pd):
        raise BuildError("the dk-ctx matrix's genes are not a subset of the per-donor genes")
    sel = select_ds_genes(ds, list(prim.columns))
    X = prim[sel].to_numpy(dtype=float)
    pca = PCA()  # sklearn defaults: columns centred, not scaled, whiten False; n_components None -> exact full SVD
    scores = pca.fit_transform(X)[:, 0]
    loading = pca.components_[0].copy()
    if getattr(pca, "_fit_svd_solver", None) != "full":
        raise BuildError(f"PCA solver {getattr(pca, '_fit_svd_solver', None)} != 'full'")
    # cross-check: numpy SVD of the column-centred matrix
    Xc = X - X.mean(axis=0)
    U, s, Vt = np.linalg.svd(Xc, full_matrices=False)
    sv = U[:, 0] * s[0]
    d_svd = float(min(np.max(np.abs(sv - scores)), np.max(np.abs(sv + scores))))
    if not d_svd < 1e-8:
        raise BuildError(f"PCA vs numpy SVD: max |delta| {d_svd}")
    mean_sel = X.mean(axis=1)
    scores_s, loading_s, r_before, flipped = apply_sign(scores, loading, mean_sel)
    r_after = float(np.corrcoef(scores_s, mean_sel)[0, 1])
    r_all = float(np.corrcoef(scores_s, prim.to_numpy(dtype=float).mean(axis=1))[0, 1])
    bdir = OUT / name
    bdir.mkdir(parents=True, exist_ok=True)
    outputs = [table_output(ds.to_frame(), bdir / "ds_dk_ctx_perdonor.csv", "table"),
               table_output(pd.DataFrame({"pc1": scores_s}, index=pd.Index(ids34, name="label")),
                            bdir / "pc1_dk_ctx.csv", "table"),
               table_output(pd.DataFrame({"loading": loading_s}, index=pd.Index(sel, name="gene_symbol")),
                            bdir / "pc1_loadings.csv", "table")]
    n_eq = int((ds.loc[list(prim.columns)] == R12_THRESHOLD).sum())
    checks = dict(
        n_parcels=len(ids34), parcels="dk_atlas_info.csv rows hemisphere L and structure cortex (ids 1-34)",
        n_genes_per_donor=len(genes_pd), n_genes_dk_ctx=int(prim.shape[1]),
        n_ds_gt_threshold_all=int((ds > R12_THRESHOLD).sum()), n_ds_ge_threshold_all=int((ds >= R12_THRESHOLD).sum()),
        n_selected=len(sel), n_ds_equal_threshold_in_dk_ctx=n_eq,
        filter="DS > .1 strictly (R12); abagen's keep_stable_genes keeps DS >= threshold -- %d gene(s) of the dk-ctx "
               "matrix sit exactly at .1, so the two rules select the same genes iff that count is 0" % n_eq,
        explained_variance_ratio_pc1=float(pca.explained_variance_ratio_[0]),
        pca="sklearn.decomposition.PCA() (n_components None, svd_solver 'auto' -> 'full', whiten False): columns "
            "centred, not scaled; PC1 = components_[0], score = fit_transform(X)[:, 0]",
        pca_vs_numpy_svd_max_abs_delta=d_svd,
        sign_rule="corr(PC score, mean expression over genes) > 0 (prereg_amend_3.md:146); 'genes' = the PCA's genes "
                  "(DS > .1); the sign under the mean over all 15,633 dk-ctx genes is recorded beside it",
        corr_score_mean_before=r_before, flipped=flipped, corr_score_mean_after=r_after,
        corr_score_mean_all_genes=r_all, sign_agrees_with_all_gene_mean=bool(r_all > 0),
        label=R12_LABEL, exposure_note=R12_EXPOSURE_NOTE,
        ds_call="abagen.correct.keep_stable_genes(expression=<6 per-donor frames, DONORS order, rows = the 34 ids>, "
                "threshold=0.1, percentile=False, rank=True, return_stability=True)",
        inference="a descriptor at component level, two-sided (R12); nothing here correlates PC1 with any map")
    if not r_after > 0:
        raise BuildError("PC1 sign rule not met after the flip")
    rec = dict(build=name, kind="derived", atlas="dk", readings=list(DERIVED[name]["readings"]),
               what=DERIVED[name]["what"], environment=dict(env, sklearn=sklearn.__version__),
               inputs=dict(perdonor=used, primary_dk=dict(file=f"artifacts/ahba/{L6_PINS['dk'][0]}",
                                                          sha256=L6_PINS["dk"][1], sha256_round_trip=L7_PINS["dk"]),
                           atlas_info=dict(file=ATLAS["dk"]["info"], sha256=ATLAS["dk"]["info_sha256"])),
               atlas_files=dict(atlas_info=ATLAS["dk"]["info"]), abagen_call=None, outputs=outputs, checks=checks,
               ok=True, timing=dict(total_seconds=round(time.time() - t0, 1), peak_working_set_mib=peak_rss_mib()),
               started=started, finished=_dt.datetime.now().isoformat(timespec="seconds"), readers=READERS,
               hash_rule=HASH_RULE)
    write_json(bdir / RECORD, rec)
    log(f"  {name}: ok; {len(sel)} genes with DS > .1 of {prim.shape[1]}; PC1 sign flipped: {flipped}")
    return rec


def derive_loo(log=print) -> dict:
    """R11: A3's leave-one-donor-out matrices verified as A3 did, both readers' hashes, and their per-parcel counts."""
    import numpy as np

    name = "r11-loo"
    started = _dt.datetime.now().isoformat(timespec="seconds")
    t0 = time.time()
    env = environment()
    man_p = LOO_DIR / "MANIFEST.json"
    man_sha = sha256_file(man_p)
    if not man_sha.startswith(A3_LOO_MANIFEST_PREFIX):
        raise BuildError(f"A3's LOO MANIFEST sha256 {man_sha[:16]}.. does not start with {A3_LOO_MANIFEST_PREFIX}")
    man = json.loads(man_p.read_text(encoding="utf-8"))
    if tuple(man["donors"]) != DONORS:
        raise BuildError("A3 MANIFEST donors != DONORS")
    e4_now = sha256_file(E4_PATH)
    bdir = OUT / name
    bdir.mkdir(parents=True, exist_ok=True)
    outputs, checks, loo = [], {}, {}
    for atlas in ("dk", "aal"):
        require_primary(atlas, env)
        a = man["atlases"][atlas]
        fc = a["full_check"]
        c_fc = dict(reproduces=fc.get("reproduces") is True, matrix_is_l7_pin=fc.get("sha256_matrix") == L7_PINS[atlas],
                    a1_pin_is_l7_pin=fc.get("a1_sha256_matrix") == L7_PINS[atlas])
        if not all(c_fc.values()):
            raise BuildError(f"{atlas}: A3's six-donor full check {c_fc}")
        prim = pinned_primary(atlas)
        pc = primary_counts(atlas)
        loo[atlas] = dict(full_check=c_fc, cells={})
        for d in DONORS:
            e = a["loo"][d]
            f = LOO_DIR / e["file"]
            meta = json.loads((LOO_DIR / f"{atlas}_loo-{d}_meta.json").read_text(encoding="utf-8"))
            c = {"file sha256 == A3 MANIFEST": sha256_file(f) == e["sha256_file"],
                 "donors = the six minus exactly the left-out one (MANIFEST)": loo_donors_ok(e["donors"], d),
                 "donors = the six minus exactly the left-out one (meta)": loo_donors_ok(meta["donors"], d)
                 and meta["left_out"] == d,
                 "abagen 0.1.3 and the §3.1 settings (meta)": meta.get("abagen") == "0.1.3"
                 and meta.get("settings") == FROZEN,
                 "e4_ahba_matrices.py bytes unchanged since the build (meta)": meta.get("e4_sha256") == e4_now}
            o, df = existing_matrix(f)
            c["round-trip matrix hash == A3 MANIFEST"] = o["sha256_round_trip"] == e["sha256_matrix"]
            c["round-trip matrix hash == the LOO meta's"] = o["sha256_round_trip"] == meta.get("sha256_matrix")
            c["parcel index == the primary's"] = [int(i) for i in df.index] == [int(i) for i in prim.index]
            emp = empty_rows(df)
            c["empty parcels == A3 MANIFEST"] = emp == [int(i) for i in e["empty_parcels"]]
            ct = drop_donor_counts(pc, d)
            c["derived counts: zero-sample parcels == empty rows"] = counts_match_empty(ct, emp)
            if not all(c.values()):
                raise BuildError(f"{atlas} LOO {d}: {[k for k, v in c.items() if not v]}")
            oc = table_output(ct, bdir / f"{atlas}_loo-{d}_counts.csv", "counts")
            outputs.append(oc)
            loo[atlas]["cells"][d] = dict(checks=c, matrix=o, counts=oc["file"], n_genes=int(df.shape[1]),
                                          empty_parcels=emp, n_parcels_with_ge2_donors=int((ct["n_donors"] >= 2).sum()))
            del df
        log(f"  {name}: {atlas}: 6 LOO matrices verified")
    checks["loo"] = loo
    checks["a3_manifest"] = dict(file="artifacts/ahba/loo/MANIFEST.json", sha256=man_sha,
                                 pin_prefix_source="arcs/replication/src/ahba_loo_extra.py:5")
    checks["counts_rule"] = ("derived: the primary build's per-donor counts without the left-out donor's column (the "
                             "sample-to-parcel assignment is per donor, allen.py:454-493); checked against each LOO "
                             "matrix's empty rows")
    rec = dict(build=name, kind="derived", atlas="dk, aal", readings=list(DERIVED[name]["readings"]),
               what=DERIVED[name]["what"], environment=env,
               inputs=dict(a3_manifest=checks["a3_manifest"], e4_sha256=e4_now), atlas_files=None, abagen_call=None,
               outputs=outputs, checks=checks, ok=True,
               timing=dict(total_seconds=round(time.time() - t0, 1), peak_working_set_mib=peak_rss_mib()),
               started=started, finished=_dt.datetime.now().isoformat(timespec="seconds"), readers=READERS,
               hash_rule=HASH_RULE)
    _ = np  # noqa: F841
    write_json(bdir / RECORD, rec)
    return rec


# ================================================================================================================
# manifest
# ================================================================================================================
def write_manifest(log=print) -> dict:
    """MANIFEST.json over every build and derived record: each output file re-hashed against its record, every record
    complete and from one environment and script, the inputs re-hashed against inputs.json, NOT_BUILT listed."""
    env = environment()
    inputs_doc = json.loads(INPUTS_JSON.read_text(encoding="utf-8"))
    rehash = hash_inputs(log=lambda *a: None)
    changed = [f["path"] for f, g in zip(inputs_doc["files"], rehash["files"])
               if (f["path"], f["sha256"]) != (g["path"], g["sha256"])]
    if changed or len(inputs_doc["files"]) != len(rehash["files"]):
        raise BuildError(f"inputs changed since inputs.json: {changed}")
    builds, problems = {}, []
    for name in list(ORDER) + list(DERIVED):
        p = OUT / name / RECORD
        if not p.exists():
            problems.append(f"{name}: no record")
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        miss = record_missing(rec)
        if miss:
            problems.append(f"{name}: record lacks {miss}")
        if rec.get("ok") is not True:
            problems.append(f"{name}: ok is not True")
        bad = [k for k in ENV_SAME if rec["environment"].get(k) != env.get(k)]
        if bad:
            problems.append(f"{name}: environment / script differs ({bad})")
        outs = []
        for o in rec["outputs"]:
            fp = (ROOT / o["file"]) if o["file"].startswith("artifacts/") else (OUT / name / o["file"])
            got = sha256_file(fp) if fp.exists() else None
            if got != o["sha256"]:
                problems.append(f"{name}/{o['file']}: sha256 {got} != record")
            outs.append({k: o.get(k) for k in ("file", "role", "donor", "bytes", "sha256", "shape", "sha256_round_trip",
                                                "sha256_default") if k in o})
        builds[name] = dict(record=f"{name}/{RECORD}", record_sha256=sha256_file(p), kind=rec["kind"],
                            atlas=rec["atlas"], readings=rec["readings"], what=rec["what"],
                            overrides=rec.get("overrides"), outputs=outs, timing=rec["timing"],
                            started=rec["started"], finished=rec["finished"])
        if rec["kind"] == "primary":
            builds[name]["primary_reproduction"] = rec["checks"]["primary_reproduction"]["reproduces"]
    if problems:
        raise BuildError("manifest refused: " + "; ".join(problems))
    man = dict(what="A1 WP2 env/venv_ref AHBA builds (RUN_PLAN.md v3.1 R10, R11, R12, R14, R31; §14; RUN_PLAN_amend_1 "
                    "R35)", builder=REL_SCRIPT, environment=env,
               inputs=dict(file=INPUTS_JSON.relative_to(ROOT).as_posix(), sha256=sha256_file(INPUTS_JSON),
                           rehashed=_dt.datetime.now().isoformat(timespec="seconds"), unchanged=True,
                           n_files=len(rehash["files"])),
               builds=builds, not_built=NOT_BUILT, readers=READERS, hash_rule=HASH_RULE, donors=list(DONORS),
               written=_dt.datetime.now().isoformat(timespec="seconds"))
    write_json(MANIFEST_JSON, man)
    log(f"  MANIFEST written: {MANIFEST_JSON.relative_to(ROOT).as_posix()} (sha256 {sha256_file(MANIFEST_JSON)})")
    return man


# ================================================================================================================
# CLI
# ================================================================================================================
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inputs", allow_abbrev=False)
    b = sub.add_parser("build", allow_abbrev=False)
    b.add_argument("names", nargs="+", choices=list(BUILDS))
    d = sub.add_parser("derive", allow_abbrev=False)
    d.add_argument("names", nargs="+", choices=list(DERIVED))
    sub.add_parser("manifest", allow_abbrev=False)
    sub.add_parser("all", allow_abbrev=False)
    sub.add_parser("list", allow_abbrev=False)
    a = ap.parse_args(argv)
    t0 = time.time()
    if a.cmd == "list":
        for n in ORDER:
            print(n, "|", _ascii(BUILDS[n].what))
        for n in DERIVED:
            print(n, "|", _ascii(DERIVED[n]["what"]))
        for n in NOT_BUILT:
            print(n, "| NOT BUILT")
        return 0
    if a.cmd == "inputs":
        cmd_inputs()
    elif a.cmd == "build":
        for n in a.names:
            run_build(n)
    elif a.cmd == "derive":
        for n in a.names:
            (derive_r12 if n == "r12-han-c1-ourpc1" else derive_loo)()
    elif a.cmd == "manifest":
        write_manifest()
    else:
        if not INPUTS_JSON.exists():
            cmd_inputs()
        for n in ORDER:  # the three primaries first: a failed check raises and stops everything
            run_build(n)
        derive_r12()
        derive_loo()
        write_manifest()
    print(f"done in {time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
