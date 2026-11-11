"""A1 launch assertions L1-L15 and the provenance block (RUN_PLAN.md v3.1 §1, §2.3, §2.4; FROZEN sha256 16c60232...).

RUN_PLAN.md §1 (:135-137): "the runner refuses to start unless every one holds ... Every assertion is written into each
output's provenance block. A failed assertion stops the run before any statistic is computed."

`launch(repo_root, run_commit, gate, ...)` evaluates every assertion, records all of them, and raises `LaunchRefused`
(carrying the record) if any fails. Nothing here computes a statistic.

Line endings (RUN_PLAN.md:157-164): every text-file assertion is made on the git blob at the run commit AND on the
sha256 of the LF-normalised bytes read from the worktree; where the plan or a frozen text pins the CRLF hash (L8, L9,
and L8's gates_json), the CRLF form is rebuilt from the LF bytes (each LF written as CRLF) and checked too.

Pins: full values are taken from the frozen texts where they hold them (RUN_PLAN.md §0.1 :29-33, FROZEN.txt,
register_freeze_manifest.json, src_register/s_build.py:156-165, results/e4_ahba_matrices.json,
register_maps/mist64_ahba_matrix.json, prereg_amend_5.md:23). RUN_PLAN.md:148-149 pins the L8 / L9 blob ids and LF /
CRLF hashes by 8-hex prefixes only; the full values below were computed on 2026-10-01 from the committed blobs at
86edcad (git rev-parse / git cat-file, programme venv) and every one is asserted at launch to start with the plan's
prefix. A full value can only refuse more than its prefix would.

Each assertion function returns {"id", "expected", "observed", "ok", "status", "detail"}; "status" is "pass", "fail",
or (L14 outside a G1 carrier stage, L15 on an ungated run) "not exercised" / "not applicable", with ok True.

RUN_PLAN_amend_1.md v2.1 (FROZEN sha256 8e06d60e...):
- L5a: the amendment's FROZEN.txt line, asserted as L5 asserts the plan's (blob and worktree LF bytes = the pin; one
  FROZEN.txt line with the pin; 0 CR in the blob). The launch record holds L1-L5, L5a, L6-L15.
- R35 (the two AHBA matrix readers), in L7: in env/venv_ref the round-trip reader's sha256 of hash_pandas_object(df,
  index=True) bytes = the L7 pins (identity); in env/venv (this interpreter, at launch) the round-trip read's hash =
  the L7 pin; the default reader's hash computed in BOTH environments, equal across them and to its R35 pin; each
  environment's pandas, numpy and Python versions recorded (and carried into every provenance block). Before a
  matrix's first use in a process, matrix_first_use (the context builder's hook, adapters.build_context_checked)
  reads the same file with A1's default reader and with float_precision='round_trip' and asserts identical index and
  gene order and max |delta| < 1e-12 over the rows used (MatrixReaderError stops the run). Nothing here returns or
  prints a matrix value: hashes, shapes, the readers' max |delta| and versions only.

RUN_PLAN_amend_2.md v2.1 (FROZEN sha256 acdb1290...):
- L5b: the amendment-2 FROZEN.txt line, asserted as L5 / L5a (blob and worktree LF bytes = the pin; exactly one FROZEN.txt
  line with the pin; 0 CR in the blob). The launch record holds L1-L5, L5a, L5b, L6-L15; the record's and every
  provenance block's `amendment_sha256` names both amendments' pins, and provenance_block refuses a launch record
  without L5b.

RUN_PLAN_amend_3.md v2.1 (FROZEN sha256 da3f3b8b...; WP3 fix round 2):
- L5c: the amendment-3 FROZEN.txt line, asserted as L5a / L5b (blob and worktree LF bytes = the pin; exactly one
  FROZEN.txt line with the pin; 0 CR in the blob). The launch record holds L1-L5, L5a, L5b, L5c, L6-L15;
  `amendment_sha256` names the three amendments' pins, and provenance_block refuses a launch record without L5c.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import importlib
import json
import os
import platform
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Mapping

from . import loader

# ================================================================================================================
# pins (each cites its frozen source)
# ================================================================================================================
PLAN_PATH = "arcs/audit/RUN_PLAN.md"
PLAN_SHA256 = "16c6023296fab612c34155e40d271c37258627980f12d00794e0fc09e1533823"  # FROZEN.txt (its RUN_PLAN.md line)
AMEND1_PATH = "arcs/audit/RUN_PLAN_amend_1.md"  # L5a (RUN_PLAN_amend_1.md §0)
AMEND1_SHA256 = "8e06d60e8f1677ab579ebbf70db7c92f040df4c747672d71be1ce2f582f57f60"  # FROZEN.txt (its line)
AMEND2_PATH = "arcs/audit/RUN_PLAN_amend_2.md"  # L5b (RUN_PLAN_amend_2.md v2.1)
AMEND2_SHA256 = "acdb1290a676d801a174b41635c649452497dce7c04c08f484781082af7c8af7"  # FROZEN.txt (its line)
AMEND3_PATH = "arcs/audit/RUN_PLAN_amend_3.md"  # L5c (RUN_PLAN_amend_3.md v2.1)
AMEND3_SHA256 = "da3f3b8bf068b34e8a3a2c0e22cdd9fbb1af48723e61d0a805f71770ce566a0b"  # FROZEN.txt (its line)
AMENDMENTS = (("RUN_PLAN_amend_1.md", AMEND1_SHA256), ("RUN_PLAN_amend_2.md", AMEND2_SHA256),
              ("RUN_PLAN_amend_3.md", AMEND3_SHA256))
FROZEN_TXT = "arcs/audit/FROZEN.txt"
REGISTER_PATH = "arcs/audit/claims_register.md"
REGISTER_SHA256 = "897b2112d25455b330e2ae2adac659180d46f4825ae765b6a791d110873abdd3"  # RUN_PLAN.md:29; FROZEN.txt
TSV_PATH = loader.TSV_PATH
TSV_SHA256 = loader.TSV_SHA256  # RUN_PLAN.md:30; manifest files[0]
MANIFEST_PATH = "arcs/audit/register_freeze_manifest.json"
MANIFEST_SHA256 = "38c2a507b057bf50b74c5ec348f03354afb3f4fd439ef73c295568a1e3155052"  # RUN_PLAN.md:31
MANIFEST_N = 36  # RUN_PLAN.md:31, :143
# FROZEN.txt lines 1-6 (RUN_PLAN.md:32-33, :144)
PREREG = (
    ("prereg.md", "a632b852637cc9b7d104d3d225fa9c618ce6204ed3d0d7181aff6cc665ff2114"),
    ("prereg_amend_1.md", "7a0dd383e7855197482501261bd7b28c49c88bb43ea17015ba78186af565b292"),
    ("prereg_amend_2.md", "29c1ffdcb9d07b84c0951da705de413e35b9429b8fe0e2868fa751530bcb93af"),
    ("prereg_amend_3.md", "d19f0f104dc9f451df49209589440b0cb5b21dce040a4793ced208663a2f2cf7"),
    ("prereg_amend_4.md", "25114b65ca7e117c30fa6a7b631eec61f6a6e83126b9f089542b22a7bfef9f23"),
    ("prereg_amend_5.md", "023bc880df1fa5832bdfc9144118de677d6a48146a89b3e4c1dc4060615684b9"),
)
AUDIT_DIR = "arcs/audit"
# L6: frozen src_register/s_build.py:156-165 (PIN), raw-byte sha256 as s_build asserts them
AHBA_DIR = "artifacts/ahba"
AHBA_FILES = (
    ("dk_expr.csv.gz", "949aeb011a202eeae768d954e868175759de1f9e9f38c54deab88b0d48fd85bf"),
    ("aal_expr.csv.gz", "44ef457c99e39a5d72586f52dcc1974c5f317b665739978382683d1eb3ccd33c"),
    ("mist64_expr.csv.gz", "7a7a6e22ab9f4e2238e122c609b3d77ea584eb42295afd5d70cc531b0514e153"),
    ("dk_atlas_info.csv", "abb69a9bf976a153b749eb5333e92cf03d4f61f2ce3efd34e49ea6e82f18729b"),
    ("aal_atlas_info.csv", "22e758a7fd525b641ef099028f9329f932a3ff3c1acf65416a8b4574795bf0ee"),
    ("mist64_atlas_info.csv", "4dafc820bad33634666f37e0b20ee7cd0358ce67005af96bba87e6cc4fe3fcca"),
)
S_BUILD_PATH = "arcs/audit/src_register/s_build.py"
# L7: results/e4_ahba_matrices.json (dk, aal "sha256_matrix"); register_maps/mist64_ahba_matrix.json ("sha256_matrix")
AHBA_MATRIX = (
    ("dk", "9c66a2058896061fd3630fdad15abe121fc1148ac7160181b200cb0fb7d9b1b2"),
    ("aal", "0dbbb50ca9a60647b7dc49477c905dbb49631be0f42f74889039f8d8d7bb6a00"),
    ("mist64", "7f750213c2c5e02b85b0d05cdde2e095401c353cc518e21e256324542080a850"),
)
E4_MATRICES_JSON = "arcs/audit/results/e4_ahba_matrices.json"
MIST64_MATRIX_JSON = "arcs/audit/register_maps/mist64_ahba_matrix.json"
# The reader that reproduces the pins: A3's h_common.verify_matrix (:117-124) round-trip read; pandas' default float
# parser does not reproduce them (checked 2026-10-01 in env/venv_ref, pandas 1.5.3).
L7_READER = "pandas.read_csv(path, index_col=0, float_precision='round_trip'); sha256(hash_pandas_object(df, index=True))"
# RUN_PLAN_amend_1 R35: A1's default-parser reader (e3_plants.primary_parcels: read_csv(index_col=0)); its pins, computed
# by the orchestrator before the freeze (hash only; pandas 3.0.6 in env/venv and 1.5.3 in env/venv_ref identical)
DEFAULT_READER = "pandas.read_csv(path, index_col=0); sha256(hash_pandas_object(df, index=True))"
AHBA_DEFAULT_READER = (
    ("dk", "6707881c6b5d9e12858f654cdfb6ec9b416d352f74f36fe59c11d2088c6daebe"),
    ("aal", "ef455efb83f38a234f34dbd0e66153a8c48f6f1ac6f12bbab9d8bd1e0d3e9eac"),
    ("mist64", "13aa6f7df6020d6f19a37f3130b332f80f4511d9f542d2f1760f4de2a7a97997"),
)
READER_MAX_ABS_DELTA = 1e-12  # R35 "values": max |delta| < 1e-12 over the rows used
# L8 / L9 (RUN_PLAN.md:148-149): (blob id, LF sha256, CRLF sha256), full values; plan prefixes beside them
GATES_A5_PATH = "arcs/audit/results/e3_gates_a5.json"
GATES_A5 = ("1853086805b3acc9801073737029052a60d4c47a",
            "3952430cfba27d1a49084a2fd8c7ed2e49be6ea2343e084258a4b26ae21626d6",
            "6d5533b3ce27211fb46788061b4b184aea071e5ddfed22888fb2747c87fbece8")
GATES_A3_PATH = "arcs/audit/results/e3_gates_a3.json"
GATES_A3 = ("fb41a15eb1b27a83e6950062c6ff17bf4ac59660",
            "918606d85d55f582d302a4dac5d8cb07c488e9d23897408458fe22728c66aad9",
            "105e81f1674aaf600af8c22cefd3fc547badd74f2dba27e10f6f8315bfc857b0")  # CRLF: prereg_amend_5.md:23 (full)
CATCH_PATH = "arcs/audit/results/e3_catch_curves_a5.json"
CATCH = ("82fa016f9de7d2a649b75332882145bb32e02924",
         "c9d8d900595a1d6ea98d9135adad4d15b8808e23ee22e000d5a917696c05cd6b",
         "b9ff7fed11c8b1905f86e1b77506b5dfa26fd393bd8ee6690bc47aa60921a68a")
PLAN_PREFIXES = {  # RUN_PLAN.md:148-149, verbatim prefixes
    GATES_A5_PATH: ("18530868", "3952430c", "6d5533b3"),
    GATES_A3_PATH: ("fb41a15e", "918606d8", "105e81f1"),
    CATCH_PATH: ("82fa016f", "c9d8d900", "b9ff7fed"),
}
AMEND5_PATH = "arcs/audit/prereg_amend_5.md"
AMEND5_GATES_JSON_LINE = 23  # prereg_amend_5.md:23 holds the full 105e81f1... value
# L10 (RUN_PLAN.md:150; amendment 5 §4.1-4.2, §4.4): the three scope labels, verbatim as e3_gates_a5.json holds them
# (that file is pinned byte-for-byte by L8)
SCOPE_LABELS = (
    "species leg untested (gradient): V-AAL claims with R2_grad >= .25",
    "species leg untested (gradient): V-CC200 claims with R2_grad >= .25",
    "brain-enrichment (N1) confound untested: V-CC200 claims with brain-enriched sets",
)
LABEL_GRADIENT = "species leg untested (gradient)"           # prereg_amend_5.md:199
LABEL_N1 = "brain-enrichment (N1) confound untested"         # prereg_amend_5.md:220
SCOPE_PAIRS = {(LABEL_GRADIENT, "V-AAL"), (LABEL_GRADIENT, "V-CC200"), (LABEL_N1, "V-CC200")}
REPLICA = {"a": (150, 1000), "c": (131, 1000)}  # RUN_PLAN.md:150
REPLICA_C_THRESHOLD = 0.05  # prereg_amend_5.md:257-258: "> .05, the gate passes"; "<= .05" -> the dk-ctx N1 label
# L12 (RUN_PLAN.md:152): the §4 fenced block, claims_register.md:1849-1896 (transcribed; also parsed at launch)
M_LOWER = 207
GATE_ROWS = {"G1": 380, "G2": 194, "none": 115, "G1+G2": 3}
M_PER_TARGET = {
    "patel2021virtual": 3, "giacomel2026cartography": 14, "romerogarcia2019synaptic": 3, "rasero2023neurogenetics": 14,
    "buch2023asdsubgroups": 84, "mamat2025molecular": 22, "liu2026spatiotemporal": 1, "pagani2026crossspecies": 10,
    "benkarim2021connectivity": 12, "dear2024corticalgene": 2, "pretzsch2024patterns": 4, "park2021subcortico": 8,
    "moreau2020mutations": 2, "hansen2022local": 1, "leyhausen2024intrinsic": 27,
}
BLOCK_HEAD = "R4: section 4 numbers"
# L13 (RUN_PLAN.md:153; claims_register.md:832-833)
GUARD_PATH = "arcs/audit/src_register/privacy_guard.py"
GUARD_SHA256 = "430f86dc087ee47d3e673ba280a6a54dbf79c59fe2b006eb9e283ffe7602a366"  # manifest entry
GUARD_N = 46
GUARD_SUMMARY = re.compile(r"^privacy guard self-test: (\d+) / (\d+) \(planted failures caught (\d+) / (\d+)\)$")
# L14 (RUN_PLAN.md:154; claims_register.md:1288-1291, :1301-1302; carrier_test.py:2075, :2087-2112)
CARRIER_RECORD_PATH = "arcs/audit/register_maps/carrier_tests_selftest.json"
CARRIER_RUN_STAMP = "run"  # carrier_test.py:1291 SELFTEST_RUN_STAMP
CARRIER_SUMMARY = re.compile(r"^selftest: (\d+) / (\d+) cases classified as planted$")
CARRIER_EQUAL = "record EQUAL to the frozen %s (run stamps aside)" % CARRIER_RECORD_PATH
PDFPLUMBER = "0.11.10"

ASSERTION_IDS = ("L1", "L2", "L3", "L4", "L5", "L5a", "L5b", "L5c", "L6", "L7", "L8", "L9", "L10", "L11", "L12", "L13",
                 "L14", "L15")
HEX40 = re.compile(r"[0-9a-f]{40}")
HEX64 = re.compile(r"[0-9a-f]{64}")
COMMITISH = re.compile(r"[0-9a-f]{7,40}")
CODE_ROOTS = ("arcs/audit/src/a1_audit", "src/asdg")
CODE_NAMES = ("a1_audit", "asdg")
GATES = (None, "G1", "G2")
NOT_EXERCISED_L14 = "not exercised (no G1 carrier stage)"
NOT_APPLICABLE_L15 = "not applicable (ungated run: no gate check applies)"


class LaunchRefused(RuntimeError):
    """A launch assertion failed; `.record` holds every assertion's record. Nothing was computed."""

    def __init__(self, record: dict):
        self.record = record
        super().__init__("launch refused: failed %s" % ", ".join(record.get("failed", [])))


class ProvenanceError(RuntimeError):
    """A provenance condition failed (a refused launch, or code changed since the launch)."""


# ================================================================================================================
# helpers
# ================================================================================================================
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lf(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


def crlf_from_lf(b: bytes) -> bytes:
    """RUN_PLAN.md:161: the CRLF form rebuilt from the LF bytes, each LF written as CRLF."""
    return b.replace(b"\n", b"\r\n")


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def host_record() -> dict:
    """RUN_PLAN.md §2.4 "the host"; with numpy's and pandas' versions (RUN_PLAN_amend_1 R34: "The numpy version is
    recorded per row"; R35: the environment's versions)."""
    from importlib import metadata
    vers = {}
    for pkg in ("numpy", "pandas"):
        try:
            vers[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            vers[pkg] = None
    return {"node": platform.node(), "system": platform.system(), "release": platform.release(),
            "machine": platform.machine(), "python": sys.version.split()[0], "executable": sys.executable, **vers}


def _rec(aid: str, expected, observed, ok: bool, detail=None, status: str | None = None) -> dict:
    return {"id": aid, "expected": expected, "observed": observed, "ok": bool(ok),
            "status": status or ("pass" if ok else "fail"), "detail": detail if detail is not None else {}}


def strict_equal(a, b) -> bool:
    """JSON values equal with their types (True != 1, 1 != 1.0)."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return sorted(a) == sorted(b) and all(strict_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(strict_equal(x, y) for x, y in zip(a, b))
    return a == b


class Git:
    """Read-only git calls on one work tree (`git -C <root>`)."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def run(self, *args, input: bytes | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(self.root), "-c", "core.quotepath=off", *args], input=input,
                              capture_output=True)

    def resolve(self, rev) -> str | None:
        if not isinstance(rev, str) or not rev or rev.startswith("-") or any(c.isspace() for c in rev):
            return None
        r = self.run("rev-parse", "--verify", "--quiet", rev + "^{commit}")
        out = r.stdout.decode("ascii", "replace").strip()
        return out if r.returncode == 0 and HEX40.fullmatch(out) else None

    def head(self) -> str | None:
        return self.resolve("HEAD")

    def blob(self, commit: str | None, path: str) -> bytes | None:
        if commit is None:
            return None
        r = self.run("cat-file", "blob", "%s:%s" % (commit, path))
        return r.stdout if r.returncode == 0 else None

    def blob_id(self, commit: str | None, path: str) -> str | None:
        if commit is None:
            return None
        r = self.run("rev-parse", "--verify", "--quiet", "%s:%s" % (commit, path))
        out = r.stdout.decode("ascii", "replace").strip()
        if r.returncode != 0 or not HEX40.fullmatch(out):
            return None
        t = self.run("cat-file", "-t", out).stdout.decode("ascii", "replace").strip()
        return out if t == "blob" else None

    def porcelain(self) -> list[str] | None:
        r = self.run("status", "--porcelain", "--untracked-files=all")
        if r.returncode != 0:
            return None
        return [ln for ln in r.stdout.decode("utf-8", "replace").splitlines() if ln.strip()]

    def common_dir(self) -> Path | None:
        r = self.run("rev-parse", "--path-format=absolute", "--git-common-dir")
        s = r.stdout.decode("utf-8", "replace").strip()
        return Path(s) if r.returncode == 0 and s else None


@dataclass
class Ctx:
    """What the assertions read: git at `repo` (blobs at `commit`, status, HEAD) and file bytes under `files`
    (= `repo`, except in P1's copy tests, which point `files` at a scratch copy)."""
    repo: Path
    commit: str | None
    commit_arg: str
    files: Path
    git: Git
    _blobs: dict = field(default_factory=dict)
    _ids: dict = field(default_factory=dict)

    def read(self, rel: str) -> bytes | None:
        p = self.files / rel
        return p.read_bytes() if p.is_file() else None

    def blob(self, rel: str) -> bytes | None:
        if rel not in self._blobs:
            self._blobs[rel] = self.git.blob(self.commit, rel)
        return self._blobs[rel]

    def blob_id(self, rel: str) -> str | None:
        if rel not in self._ids:
            self._ids[rel] = self.git.blob_id(self.commit, rel)
        return self._ids[rel]


def make_ctx(repo_root, run_commit: str, files_root=None) -> Ctx:
    repo = Path(repo_root).resolve()
    git = Git(repo)
    full = git.resolve(run_commit) if isinstance(run_commit, str) and COMMITISH.fullmatch(run_commit) else None
    return Ctx(repo=repo, commit=full, commit_arg=str(run_commit), files=Path(files_root).resolve() if files_root else repo,
               git=git)


def text_file(ctx: Ctx, rel: str, sha_lf: str, blob_id: str | None = None, crlf: str | None = None,
              prefixes: tuple | None = None) -> tuple[bool, dict, bytes | None]:
    """The text-file assertion of RUN_PLAN.md:157-164: sha256 of the blob at the run commit and of the worktree's
    LF-normalised bytes equal the pin; the blob id equals its pin where one is pinned; the CRLF form rebuilt from the
    LF bytes equals its pin where one is pinned. Returns (ok, detail, the worktree's LF bytes)."""
    checks: dict[str, bool] = {}
    d: dict = {"path": rel}
    raw = ctx.read(rel)
    lfb = None
    if raw is None:
        checks["worktree file present"] = False
    else:
        lfb = lf(raw)
        d["worktree_cr"] = raw.count(b"\r")
        d["worktree_sha256"] = sha256_bytes(raw)
        d["lf_sha256"] = sha256_bytes(lfb)
        checks["sha256(LF bytes of the worktree file) == pin"] = d["lf_sha256"] == sha_lf
        if crlf is not None:
            d["crlf_rebuilt_sha256"] = sha256_bytes(crlf_from_lf(lfb))
            checks["sha256(CRLF form rebuilt from the LF bytes) == pin"] = d["crlf_rebuilt_sha256"] == crlf
    blob = ctx.blob(rel)
    if blob is None:
        checks["blob present at the run commit"] = False
    else:
        d["blob_sha256"] = sha256_bytes(blob)
        d["blob_cr"] = blob.count(b"\r")
        checks["sha256(blob at the run commit) == pin"] = d["blob_sha256"] == sha_lf
    bid = ctx.blob_id(rel)
    d["blob_id"] = bid
    if blob_id is not None:
        checks["git blob id at the run commit == pin"] = bid == blob_id
    if prefixes is not None:
        full = (blob_id, sha_lf, crlf)
        checks["full pins start with the plan's 8-hex prefixes"] = all(
            f is not None and f.startswith(p) for f, p in zip(full, prefixes))
    d["checks"] = checks
    return all(checks.values()), d, lfb


def frozen_txt_lines(ctx: Ctx) -> tuple[list[tuple[str, str, str]] | None, dict]:
    """FROZEN.txt read from the blob at the run commit, required equal to the worktree's LF bytes; lines parsed as
    (timestamp, sha256, file name)."""
    raw, blob = ctx.read(FROZEN_TXT), ctx.blob(FROZEN_TXT)
    d = {"worktree_present": raw is not None, "blob_present": blob is not None}
    if raw is None or blob is None:
        return None, d
    d["worktree_lf_equals_blob"] = lf(raw) == blob
    if not d["worktree_lf_equals_blob"]:
        return None, d
    out = []
    for ln in blob.decode("utf-8").split("\n"):
        if not ln.strip():
            continue
        parts = ln.split()
        if len(parts) != 3 or not HEX64.fullmatch(parts[1]):
            d["malformed_line"] = True
            return None, d
        out.append((parts[0], parts[1], parts[2]))
    d["n_lines"] = len(out)
    return out, d


# ================================================================================================================
# L1-L15
# ================================================================================================================
def l1_register(ctx: Ctx) -> dict:
    ok, d, _ = text_file(ctx, REGISTER_PATH, REGISTER_SHA256)
    lines, fd = frozen_txt_lines(ctx)
    hits = [l for l in (lines or []) if l[2] == "claims_register.md"]
    d["frozen_txt"] = fd
    d["checks"]["FROZEN.txt has exactly one claims_register.md line, with the pin"] = (
        len(hits) == 1 and hits[0][1] == REGISTER_SHA256)
    ok = all(d["checks"].values())
    return _rec("L1", {"sha256": REGISTER_SHA256, "source": "FROZEN.txt"},
                {"blob_sha256": d.get("blob_sha256"), "lf_sha256": d.get("lf_sha256")}, ok, d)


def _manifest_doc(ctx: Ctx) -> tuple[dict | None, dict]:
    ok, d, lfb = text_file(ctx, MANIFEST_PATH, MANIFEST_SHA256)
    if not ok or lfb is None:
        return None, d
    return json.loads(lfb.decode("utf-8")), d


def l2_tsv(ctx: Ctx) -> dict:
    ok, d, _ = text_file(ctx, TSV_PATH, TSV_SHA256)
    blob_m = ctx.blob(MANIFEST_PATH)
    man_ok = blob_m is not None and sha256_bytes(blob_m) == MANIFEST_SHA256
    entry = None
    if man_ok:
        doc = json.loads(blob_m.decode("utf-8"))
        hits = [e for e in doc.get("files", []) if isinstance(e, dict) and e.get("path") == TSV_PATH]
        entry = hits[0] if len(hits) == 1 else None
    d["checks"]["the freeze manifest (at its pin) holds the TSV with the pin"] = bool(
        entry is not None and entry.get("sha256") == TSV_SHA256)
    ok = all(d["checks"].values())
    return _rec("L2", {"sha256": TSV_SHA256, "source": "freeze manifest; header line 2 'DRAFT ... NOT frozen' ignored"},
                {"blob_sha256": d.get("blob_sha256"), "lf_sha256": d.get("lf_sha256")}, ok, d)


_SAFE_REL = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./-]*")


def l3_manifest(ctx: Ctx) -> dict:
    doc, d = _manifest_doc(ctx)
    checks = d["checks"]
    entries_failed: list[str] = []
    n = None
    if doc is None:
        checks["manifest parsed (after its pin held)"] = False
    else:
        files = doc.get("files")
        n = len(files) if isinstance(files, list) else None
        checks["manifest holds %d entries" % MANIFEST_N] = n == MANIFEST_N
        paths = [e.get("path") for e in files or [] if isinstance(e, dict)]
        checks["entry paths unique"] = len(set(paths)) == len(paths) == (n or 0)
        reg = doc.get("register") if isinstance(doc.get("register"), dict) else {}
        checks["manifest's register sha256_at_build == L1 pin"] = reg.get("sha256_at_build") == REGISTER_SHA256
        for e in files or []:
            p = e.get("path") if isinstance(e, dict) else None
            want, size = (e.get("sha256"), e.get("bytes")) if isinstance(e, dict) else (None, None)
            good = (isinstance(p, str) and _SAFE_REL.fullmatch(p) is not None and ".." not in p.split("/")
                    and isinstance(want, str) and HEX64.fullmatch(want) is not None and isinstance(size, int))
            if good:
                blob = ctx.blob(p)
                raw = ctx.read(p)
                good = (blob is not None and sha256_bytes(blob) == want and len(blob) == size
                        and raw is not None and sha256_bytes(lf(raw)) == want)
            if not good:
                entries_failed.append(str(p))
        checks["every entry: blob at the run commit and worktree LF bytes equal its sha256 (and blob size its bytes)"] = (
            doc is not None and not entries_failed and n == MANIFEST_N)
    d["entries_failed"] = entries_failed
    ok = all(checks.values())
    return _rec("L3", {"sha256": MANIFEST_SHA256, "entries": MANIFEST_N, "source": "RUN_PLAN.md §0.1 / manifest"},
                {"blob_sha256": d.get("blob_sha256"), "lf_sha256": d.get("lf_sha256"), "entries": n,
                 "entries_failed": len(entries_failed)}, ok, d)


def l4_prereg(ctx: Ctx) -> dict:
    lines, fd = frozen_txt_lines(ctx)
    per = {}
    checks = {}
    for i, (name, sha) in enumerate(PREREG):
        ok_i, d_i, _ = text_file(ctx, "%s/%s" % (AUDIT_DIR, name), sha)
        per[name] = d_i
        checks["%s: blob and worktree LF bytes == pin" % name] = ok_i
        checks["FROZEN.txt line %d names %s with the pin" % (i + 1, name)] = bool(
            lines is not None and len(lines) > i and lines[i][2] == name and lines[i][1] == sha)
    ok = all(checks.values())
    return _rec("L4", {n: s for n, s in PREREG}, {n: per[n].get("lf_sha256") for n, _ in PREREG}, ok,
                {"checks": checks, "files": per, "frozen_txt": fd})


def l5_plan(ctx: Ctx) -> dict:
    ok, d, _ = text_file(ctx, PLAN_PATH, PLAN_SHA256)
    lines, fd = frozen_txt_lines(ctx)
    hits = [l for l in (lines or []) if l[2] == "RUN_PLAN.md"]
    d["frozen_txt"] = fd
    d["checks"]["FROZEN.txt has exactly one RUN_PLAN.md line, with the pin"] = len(hits) == 1 and hits[0][1] == PLAN_SHA256
    d["checks"]["the plan's blob holds 0 CR (RUN_PLAN.md:145)"] = d.get("blob_cr") == 0
    ok = all(d["checks"].values())
    return _rec("L5", {"sha256": PLAN_SHA256, "source": "FROZEN.txt"},
                {"blob_sha256": d.get("blob_sha256"), "lf_sha256": d.get("lf_sha256")}, ok, d)


def l5a_amendment(ctx: Ctx) -> dict:
    """L5a (RUN_PLAN_amend_1.md §0, the L5 extension): the amendment's FROZEN.txt line; committed with 0 CR (LF blob =
    file hash)."""
    ok, d, _ = text_file(ctx, AMEND1_PATH, AMEND1_SHA256)
    lines, fd = frozen_txt_lines(ctx)
    name = AMEND1_PATH.rsplit("/", 1)[-1]
    hits = [l for l in (lines or []) if l[2] == name]
    d["frozen_txt"] = fd
    d["checks"]["FROZEN.txt has exactly one %s line, with the pin" % name] = len(hits) == 1 and hits[0][1] == AMEND1_SHA256
    d["checks"]["the amendment's blob holds 0 CR (RUN_PLAN_amend_1.md L5a)"] = d.get("blob_cr") == 0
    ok = all(d["checks"].values())
    return _rec("L5a", {"sha256": AMEND1_SHA256, "source": "FROZEN.txt"},
                {"blob_sha256": d.get("blob_sha256"), "lf_sha256": d.get("lf_sha256")}, ok, d)


def l5b_amendment(ctx: Ctx) -> dict:
    """L5b (RUN_PLAN_amend_2.md v2.1, asserted as L5 / L5a): the amendment's FROZEN.txt line (exactly one, with the
    pin); blob and worktree LF bytes equal the pin; committed with 0 CR (LF blob = file hash)."""
    ok, d, _ = text_file(ctx, AMEND2_PATH, AMEND2_SHA256)
    lines, fd = frozen_txt_lines(ctx)
    name = AMEND2_PATH.rsplit("/", 1)[-1]
    hits = [l for l in (lines or []) if l[2] == name]
    d["frozen_txt"] = fd
    d["checks"]["FROZEN.txt has exactly one %s line, with the pin" % name] = len(hits) == 1 and hits[0][1] == AMEND2_SHA256
    d["checks"]["the amendment's blob holds 0 CR (RUN_PLAN_amend_2.md L5b)"] = d.get("blob_cr") == 0
    ok = all(d["checks"].values())
    return _rec("L5b", {"sha256": AMEND2_SHA256, "source": "FROZEN.txt"},
                {"blob_sha256": d.get("blob_sha256"), "lf_sha256": d.get("lf_sha256")}, ok, d)


def l5c_amendment(ctx: Ctx) -> dict:
    """L5c (RUN_PLAN_amend_3.md v2.1, asserted as L5a / L5b): the amendment's FROZEN.txt line (exactly one, with the
    pin); blob and worktree LF bytes equal the pin; committed with 0 CR (LF blob = file hash)."""
    ok, d, _ = text_file(ctx, AMEND3_PATH, AMEND3_SHA256)
    lines, fd = frozen_txt_lines(ctx)
    name = AMEND3_PATH.rsplit("/", 1)[-1]
    hits = [l for l in (lines or []) if l[2] == name]
    d["frozen_txt"] = fd
    d["checks"]["FROZEN.txt has exactly one %s line, with the pin" % name] = len(hits) == 1 and hits[0][1] == AMEND3_SHA256
    d["checks"]["the amendment's blob holds 0 CR (RUN_PLAN_amend_3.md L5c)"] = d.get("blob_cr") == 0
    ok = all(d["checks"].values())
    return _rec("L5c", {"sha256": AMEND3_SHA256, "source": "FROZEN.txt"},
                {"blob_sha256": d.get("blob_sha256"), "lf_sha256": d.get("lf_sha256")}, ok, d)


def l6_ahba_files(ctx: Ctx) -> dict:
    checks, observed = {}, {}
    sb = ctx.blob(S_BUILD_PATH)
    sb_text = sb.decode("utf-8", "replace") if sb is not None else ""
    for name, sha in AHBA_FILES:
        p = ctx.files / AHBA_DIR / name
        got = sha256_file(p) if p.is_file() else None
        observed[name] = got
        checks["%s sha256 (raw bytes) == pin" % name] = got == sha
        checks["%s pin present in frozen s_build.py at the run commit" % name] = sha in sb_text and name in sb_text
    ok = all(checks.values())
    return _rec("L6", {n: s for n, s in AHBA_FILES}, observed, ok,
                {"checks": checks, "source": "src_register/s_build.py:156-165 (PIN)"})


def default_venv_ref_python(ctx: Ctx) -> Path | None:
    """env/venv_ref of the main repository (a worktree has no env/: it is gitignored), found through git's common dir."""
    cd = ctx.git.common_dir()
    if cd is None:
        return None
    base = cd.parent / "env" / "venv_ref"
    for cand in (base / "Scripts" / "python.exe", base / "bin" / "python"):
        if cand.is_file():
            return cand
    return None


_L7_SCRIPT = r"""
import hashlib, json, sys
import numpy as np
import pandas as pd
out = {"pandas": pd.__version__, "numpy": np.__version__, "python": sys.version.split()[0], "matrices": {}}
def h(df):
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).to_numpy().tobytes()).hexdigest()
for atlas, path in zip(sys.argv[1::2], sys.argv[2::2]):
    rec = {}
    try:
        df = pd.read_csv(path, index_col=0, float_precision="round_trip")
        rec["sha256_matrix"], rec["shape"] = h(df), [int(x) for x in df.shape]
        del df
        df = pd.read_csv(path, index_col=0)
        rec["sha256_default"], rec["shape_default"] = h(df), [int(x) for x in df.shape]
        del df
    except Exception as e:
        rec["error"] = type(e).__name__
    out["matrices"][atlas] = rec
print(json.dumps(out))
"""


def run_l7_env(python: Path, paths: Mapping[str, Path]) -> dict:
    """One subprocess in the given environment: for each matrix the sha256 of hash_pandas_object(df, index=True) bytes
    under the round-trip reader ('sha256_matrix', L7) and under A1's default reader ('sha256_default', R35), with the
    environment's pandas, numpy and Python versions. Hashes and shapes only; no value leaves the subprocess."""
    args = []
    for atlas, p in paths.items():
        args += [atlas, str(p)]
    r = subprocess.run([str(python), "-X", "utf8", "-c", _L7_SCRIPT, *args], capture_output=True, timeout=1800,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    lines = [ln for ln in r.stdout.decode("utf-8", "replace").splitlines() if ln.strip()]
    if r.returncode != 0 or not lines:
        return {"returncode": r.returncode, "error": "subprocess failed"}
    out = json.loads(lines[-1])
    out["returncode"] = r.returncode
    return out


run_l7_venv_ref = run_l7_env  # RUN_PLAN.md:147: one subprocess in env/venv_ref per launch (the name kept)


def _env_hashes(res: dict, key: str) -> dict:
    return {atlas: ((res.get("matrices") or {}).get(atlas) or {}).get(key) for atlas, _ in AHBA_MATRIX}


def _env_versions(res: dict) -> dict:
    return {k: res.get(k) for k in ("pandas", "numpy", "python")}


def l7_ahba_matrices(ctx: Ctx, venv_ref_python: Path | None = None,
                     runner: Callable[[Path, Mapping[str, Path]], dict] | None = None, *,
                     venv_python: Path | None = None) -> dict:
    """L7 with RUN_PLAN_amend_1 R35's reader chain: env/venv_ref round-trip hash == the L7 pin (identity); env/venv
    (venv_python, default: this interpreter) round-trip hash == the L7 pin; the default reader's hash in both
    environments == its R35 pin and equal across them; both environments' versions recorded."""
    checks = {}
    e4 = ctx.blob(E4_MATRICES_JSON)
    m64 = ctx.blob(MIST64_MATRIX_JSON)
    try:
        e4d = json.loads(e4.decode("utf-8")) if e4 is not None else {}
        m64d = json.loads(m64.decode("utf-8")) if m64 is not None else {}
    except ValueError:
        e4d, m64d = {}, {}
    src = {"dk": (e4d.get("dk") or {}).get("sha256_matrix"), "aal": (e4d.get("aal") or {}).get("sha256_matrix"),
           "mist64": m64d.get("sha256_matrix")}
    for atlas, sha in AHBA_MATRIX:
        checks["%s pin == its frozen source at the run commit" % atlas] = src.get(atlas) == sha
    py = Path(venv_ref_python) if venv_ref_python else default_venv_ref_python(ctx)
    pyv = Path(venv_python) if venv_python else Path(sys.executable)
    paths = {atlas: ctx.files / AHBA_DIR / ("%s_expr.csv.gz" % atlas) for atlas, _ in AHBA_MATRIX}

    def run_in(python, label):
        if runner is None and (python is None or not python.is_file()):
            return {"error": "%s interpreter not found" % label}
        try:
            return (runner or run_l7_env)(python, paths)
        except Exception as e:  # recorded, never raised
            return {"error": type(e).__name__}

    res = run_in(py, "env/venv_ref")
    resv = run_in(pyv, "env/venv")
    got = _env_hashes(res, "sha256_matrix")
    ref_default, venv_rt, venv_default = (_env_hashes(res, "sha256_default"), _env_hashes(resv, "sha256_matrix"),
                                          _env_hashes(resv, "sha256_default"))
    dpin = dict(AHBA_DEFAULT_READER)
    for atlas, sha in AHBA_MATRIX:
        checks["%s hash_pandas_object sha256 == pin" % atlas] = got.get(atlas) == sha
        checks["%s env/venv round-trip sha256 == the L7 pin (R35 chain)" % atlas] = venv_rt.get(atlas) == sha
        checks["%s env/venv_ref default-reader sha256 == R35 pin" % atlas] = ref_default.get(atlas) == dpin[atlas]
        checks["%s env/venv default-reader sha256 == R35 pin" % atlas] = venv_default.get(atlas) == dpin[atlas]
        checks["%s default-reader sha256 equal across env/venv and env/venv_ref" % atlas] = (
            venv_default.get(atlas) is not None and venv_default.get(atlas) == ref_default.get(atlas))
    vref, vv = _env_versions(res), _env_versions(resv)
    checks["pandas, numpy and Python versions recorded for both environments (R35)"] = all(
        isinstance(v, str) and v for v in list(vref.values()) + list(vv.values()))
    ok = all(checks.values())
    return _rec("L7", {a: s for a, s in AHBA_MATRIX}, got, ok,
                {"checks": checks, "interpreter": str(py) if py else None, "reader": L7_READER,
                 "venv_ref": {k: v for k, v in res.items() if k != "matrices"},
                 "shapes": {a: ((res.get("matrices") or {}).get(a) or {}).get("shape") for a, _ in AHBA_MATRIX},
                 "errors": {a: ((res.get("matrices") or {}).get(a) or {}).get("error") for a, _ in AHBA_MATRIX},
                 "R35": {"default_reader": DEFAULT_READER, "default_reader_pins": dpin,
                         "env/venv_ref": {"interpreter": str(py) if py else None, "versions": vref,
                                          "round_trip": got, "default": ref_default},
                         "env/venv": {"interpreter": str(pyv), "versions": vv, "round_trip": venv_rt,
                                      "default": venv_default,
                                      "errors": {a: ((resv.get("matrices") or {}).get(a) or {}).get("error")
                                                 for a, _ in AHBA_MATRIX},
                                      "returncode": resv.get("returncode"), "error": resv.get("error")}},
                 "environments": {"env/venv_ref": vref, "env/venv": vv}})


class MatrixReaderError(RuntimeError):
    """RUN_PLAN_amend_1 R35 "values": A1's default reader and the round-trip reader disagree on a matrix (index or gene
    order, missing-value pattern, or max |delta| >= 1e-12 over the rows used): the run stops."""


def _frame_sha(df) -> str:
    import pandas as pd
    return sha256_bytes(pd.util.hash_pandas_object(df, index=True).to_numpy().tobytes())


def matrix_reader_check(path, used=None, rows=None) -> dict:
    """RUN_PLAN_amend_1 R35 "values", in THIS environment: the file is read with A1's default reader
    (read_csv(index_col=0), as e3_plants.primary_parcels) and with float_precision='round_trip'; asserted: identical
    index and gene order, the same missing-value pattern and max |delta| < 1e-12 over the rows used (rows: parcel ids;
    default all). used: the frame A1's reader actually handed to the statistics (e.g. a3_port._primary's), compared in
    its own row order against the round-trip read of those rows (same columns, same check). Raises MatrixReaderError.
    Returns hashes, shapes, the max |delta|, the rows checked and versions: no value."""
    import numpy as np
    import pandas as pd
    p = Path(path)
    dflt = pd.read_csv(p, index_col=0)
    rt = pd.read_csv(p, index_col=0, float_precision="round_trip")
    if list(dflt.index) != list(rt.index) or list(dflt.columns) != list(rt.columns):
        raise MatrixReaderError("%s: the two readers' index or gene order differ" % p.name)
    frames = [("default reader", dflt)] if used is None else [("frame in use", used)]
    deltas = {}
    n_rows = None
    for label, a in frames:
        if list(a.columns) != list(rt.columns):
            raise MatrixReaderError("%s: %s gene order differs from the round-trip read" % (p.name, label))
        want = list(a.index) if rows is None else [x for x in rows]
        missing = [x for x in want if x not in rt.index or x not in a.index]
        if missing:
            raise MatrixReaderError("%s: %d row(s) used are not in both frames" % (p.name, len(missing)))
        A = a.loc[want].to_numpy(dtype=float)
        R = rt.loc[want].to_numpy(dtype=float)
        if A.shape != R.shape or not np.array_equal(np.isnan(A), np.isnan(R)):
            raise MatrixReaderError("%s: %s and the round-trip read differ in shape or missing-value pattern" % (p.name, label))
        fin = ~np.isnan(A)
        d = float(np.max(np.abs(A[fin] - R[fin]))) if fin.any() else 0.0
        if not d < READER_MAX_ABS_DELTA:
            raise MatrixReaderError("%s: %s vs round-trip max |delta| %.3g >= 1e-12 over the rows used" % (p.name, label, d))
        deltas[label] = d
        n_rows = len(want)
    return {"file": p.name, "sha256_default": _frame_sha(dflt), "sha256_round_trip": _frame_sha(rt),
            "shape": [int(x) for x in rt.shape], "rows_checked": n_rows, "max_abs_delta": deltas,
            "rule": "R35: identical index and gene order, max |delta| < 1e-12 over the rows used (RUN_PLAN_amend_1.md)",
            "versions": {"pandas": pd.__version__, "numpy": np.__version__, "python": sys.version.split()[0]}}


_FIRST_USE: dict = {}


def matrix_first_use(path, used=None, rows=None) -> dict:
    """R35: matrix_reader_check once per (file, rows) per process, before the matrix's first use; the record is kept
    (first_use_records) for the provenance of every output of the process."""
    p = Path(path).resolve()
    key = (str(p), None if rows is None else tuple(rows), None if used is None else (tuple(used.index), used.shape))
    if key not in _FIRST_USE:
        _FIRST_USE[key] = matrix_reader_check(p, used=used, rows=rows)
    return _FIRST_USE[key]


def first_use_records() -> list:
    return [dict(v) for v in _FIRST_USE.values()]


def k1_semantics(doc) -> dict:
    """L8's content checks on e3_gates_a5.json (RUN_PLAN.md:148)."""
    gj = doc.get("gates_json") if isinstance(doc, dict) else None
    pc = doc.get("partial_certification") if isinstance(doc, dict) else None
    return {
        "K1_status == 'not fired'": isinstance(doc, dict) and doc.get("K1_status") == "not fired",
        "stop is false": isinstance(doc, dict) and doc.get("stop") is False,
        "dirty is false": isinstance(doc, dict) and doc.get("dirty") is False,
        "partial_certification == []": isinstance(pc, list) and len(pc) == 0,
        "gates_json.path == %s" % GATES_A3_PATH: isinstance(gj, dict) and gj.get("path") == GATES_A3_PATH,
        "gates_json.sha256 == 105e81f1... (prereg_amend_5.md:23)": isinstance(gj, dict) and gj.get("sha256") == GATES_A3[2],
    }


def l8_k1(ctx: Ctx) -> dict:
    ok5, d5, lf5 = text_file(ctx, GATES_A5_PATH, GATES_A5[1], GATES_A5[0], GATES_A5[2], PLAN_PREFIXES[GATES_A5_PATH])
    ok3, d3, _ = text_file(ctx, GATES_A3_PATH, GATES_A3[1], GATES_A3[0], GATES_A3[2], PLAN_PREFIXES[GATES_A3_PATH])
    checks = {"e3_gates_a5.json: blob id, LF and CRLF hashes": ok5,
              "e3_gates_a3.json: blob id, LF and CRLF (gates_json) hashes": ok3}
    sem = {}
    if lf5 is not None:
        try:
            sem = k1_semantics(json.loads(lf5.decode("utf-8")))
        except ValueError:
            sem = {"e3_gates_a5.json parses": False}
    else:
        sem = {"e3_gates_a5.json present": False}
    checks.update(sem)
    am = ctx.blob(AMEND5_PATH)
    am_lines = am.decode("utf-8").split("\n") if am is not None else []
    checks["prereg_amend_5.md:23 (at the run commit, at its L4 pin) holds the gates_json sha256"] = bool(
        am is not None and sha256_bytes(am) == dict(PREREG)["prereg_amend_5.md"]
        and len(am_lines) >= AMEND5_GATES_JSON_LINE and GATES_A3[2] in am_lines[AMEND5_GATES_JSON_LINE - 1])
    ok = all(checks.values())
    return _rec("L8", {"e3_gates_a5.json": {"blob": GATES_A5[0], "lf": GATES_A5[1], "crlf": GATES_A5[2],
                                            "K1_status": "not fired", "stop": False, "dirty": False,
                                            "partial_certification": []},
                       "gates_json": {"sha256 (CRLF of e3_gates_a3.json)": GATES_A3[2], "blob": GATES_A3[0],
                                      "lf": GATES_A3[1]}},
                {"e3_gates_a5.json": {"blob": d5.get("blob_id"), "lf": d5.get("lf_sha256"),
                                      "crlf": d5.get("crlf_rebuilt_sha256"), "worktree_raw": d5.get("worktree_sha256")},
                 "e3_gates_a3.json": {"blob": d3.get("blob_id"), "lf": d3.get("lf_sha256"),
                                      "crlf": d3.get("crlf_rebuilt_sha256")}},
                ok, {"checks": checks, "gates_a5": d5, "gates_a3": d3})


def l9_catch(ctx: Ctx) -> dict:
    ok, d, lfb = text_file(ctx, CATCH_PATH, CATCH[1], CATCH[0], CATCH[2], PLAN_PREFIXES[CATCH_PATH])
    parsed = False
    if lfb is not None:
        try:
            json.loads(lfb.decode("utf-8"))
            parsed = True
        except ValueError:
            parsed = False
    d["checks"]["parses as JSON"] = parsed
    ok = all(d["checks"].values())
    return _rec("L9", {"blob": CATCH[0], "lf": CATCH[1], "crlf": CATCH[2]},
                {"blob": d.get("blob_id"), "lf": d.get("lf_sha256"), "crlf": d.get("crlf_rebuilt_sha256")}, ok, d)


_SCOPE_RE = re.compile(r"\A(%s|%s): (V-[A-Za-z0-9]+) claims with (.+)\Z" % (re.escape(LABEL_GRADIENT), re.escape(LABEL_N1)))


def scope_semantics(doc) -> dict:
    """L10's checks on e3_gates_a5.json (RUN_PLAN.md:150)."""
    labels = doc.get("scope_labels") if isinstance(doc, dict) else None
    pairs = set()
    parsed_all = isinstance(labels, list)
    for s in labels if isinstance(labels, list) else []:
        m = _SCOPE_RE.match(s) if isinstance(s, str) else None
        if m is None:
            parsed_all = False
        else:
            pairs.add((m.group(1), m.group(2)))
    rep = doc.get("replica_section_4_4") if isinstance(doc, dict) else None
    rep = rep if isinstance(rep, dict) else {}
    a, c = rep.get("a") or {}, rep.get("c") or {}
    counts = doc.get("counts") if isinstance(doc, dict) and isinstance(doc.get("counts"), dict) else {}
    c_k, c_n = c.get("k"), c.get("n")
    c_rate = (c_k / c_n) if isinstance(c_k, int) and isinstance(c_n, int) and c_n > 0 else None
    return {
        "exactly three scope_labels, verbatim": isinstance(labels, list) and sorted(labels) == sorted(SCOPE_LABELS),
        "labels are gradient: V-AAL, V-CC200; N1: V-CC200": parsed_all and len(labels) == 3 and pairs == SCOPE_PAIRS,
        "no scope label names dk-ctx": isinstance(labels, list) and not any("dk-ctx" in str(s) for s in labels),
        "counts.scope == 3": counts.get("scope") == 3,
        "replica (a) 150 / 1000, passed": (a.get("k"), a.get("n")) == REPLICA["a"] and a.get("pass_") is True,
        "replica (c) 131 / 1000 > .05, passed -> no dk-ctx N1 label (amendment 5 §4.4)": (
            (c_k, c_n) == REPLICA["c"] and c_rate is not None and c_rate > REPLICA_C_THRESHOLD and c.get("pass_") is True),
    }


def l10_scope(ctx: Ctx) -> dict:
    raw = ctx.read(GATES_A5_PATH)
    lfb = lf(raw) if raw is not None else None
    checks = {"e3_gates_a5.json bytes are L8's (LF sha256 == pin)": lfb is not None and sha256_bytes(lfb) == GATES_A5[1]}
    observed = None
    if lfb is not None:
        try:
            doc = json.loads(lfb.decode("utf-8"))
            checks.update(scope_semantics(doc))
            observed = {"scope_labels": doc.get("scope_labels"),
                        "replica": {k: {kk: (doc.get("replica_section_4_4") or {}).get(k, {}).get(kk) for kk in ("k", "n")}
                                    for k in ("a", "c")}}
        except ValueError:
            checks["e3_gates_a5.json parses"] = False
    ok = all(checks.values())
    return _rec("L10", {"scope_labels": list(SCOPE_LABELS), "replica": {"a": "150/1000", "c": "131/1000"},
                        "dk-ctx N1 label": "none"}, observed, ok, {"checks": checks})


def _under(p: Path, root: Path) -> bool:
    return p == root or root in p.parents


def code_modules(repo: Path) -> tuple[dict[str, Path], list[str]]:
    """{repo-relative path: file} of every loaded module whose file lies in this tree outside env/ (A3's precedent,
    step3v_common.repo_sources: every repository module; so every a1_audit and src/asdg module, and any other repository
    module a runner imports), and the names of a1_audit / asdg modules loaded from anywhere else (foreign)."""
    repo = repo.resolve()
    env = repo / "env"
    found: dict[str, Path] = {}
    foreign: list[str] = []
    for name, m in list(sys.modules.items()):
        f = getattr(m, "__file__", None)
        named = any(name == n or name.startswith(n + ".") for n in CODE_NAMES)
        p = Path(f).resolve() if isinstance(f, str) and f and not f.startswith("<") else None
        inside = p is not None and _under(p, repo) and not _under(p, env)
        if inside and p.is_file():
            found[p.relative_to(repo).as_posix()] = p
        elif named:
            foreign.append(name)
    return dict(sorted(found.items())), sorted(foreign)


def code_hash(sources: Mapping[str, str]) -> str:
    blob = json.dumps(sorted((str(k), str(v)) for k, v in dict(sources).items()), separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def l11_clean(ctx: Ctx) -> dict:
    checks = {}
    porc = ctx.git.porcelain()
    head = ctx.git.head()
    checks["run commit resolves to a commit of this repository"] = ctx.commit is not None
    checks["git status --porcelain (untracked included) is empty"] = porc == []
    checks["HEAD == the run commit"] = head is not None and head == ctx.commit
    mods, foreign = code_modules(ctx.repo)
    sources, differ = {}, []
    for rel, p in mods.items():
        s = sha256_bytes(lf(p.read_bytes()))
        sources[rel] = s
        b = ctx.blob(rel)
        if b is None or sha256_bytes(b) != s:
            differ.append(rel)
    checks["no a1_audit / asdg module loaded from outside this tree"] = not foreign
    checks["every loaded repository module (a1_audit, src/asdg, ...) equals its blob at the run commit"] = not differ
    checks["at least one a1_audit module recorded"] = any(r.startswith(CODE_ROOTS[0] + "/") for r in sources)
    ok = all(checks.values())
    return _rec("L11", {"porcelain": [], "HEAD": ctx.commit_arg},
                {"porcelain_lines": None if porc is None else len(porc), "HEAD": head, "run_commit": ctx.commit,
                 "modules": sources, "code_hash": code_hash(sources)}, ok,
                {"checks": checks, "porcelain": (porc or [])[:50], "foreign_modules": foreign, "modules_differ": differ})


def parse_section4_block(text: str) -> dict[str, int]:
    """The register's §4 fenced block (claims_register.md:1849-1896): 'key = int' lines after the 'R4: section 4
    numbers' line, up to the closing fence."""
    lines = text.split("\n")
    heads = [i for i, ln in enumerate(lines) if ln.startswith(BLOCK_HEAD)]
    if len(heads) != 1 or heads[0] == 0 or lines[heads[0] - 1] != "```":
        raise ValueError("section 4 block not found exactly once")
    out: dict[str, int] = {}
    for ln in lines[heads[0] + 1:]:
        if ln == "```":
            return out
        k, sep, v = ln.rpartition(" = ")
        if not sep or not re.fullmatch(r"\d+", v):
            raise ValueError("section 4 block: unparsable line")
        out[k] = int(v)
    raise ValueError("section 4 block not closed")


def l12_compare(counts: Mapping, block: Mapping[str, int]) -> dict:
    """The L12 checks: the TSV's re-counted numbers against the §4 block and RUN_PLAN.md:152."""
    block_targets = {k[len("m.target."):]: v for k, v in block.items() if k.startswith("m.target.")}
    return {
        "rows == 692 (TSV) == block 'rows'": counts.get("rows") == loader.N_ROWS == block.get("rows"),
        "m == 207 (TSV, verdict_counted_in_m 'yes') == block 'm.lower'": counts.get("m.lower") == M_LOWER == block.get("m.lower"),
        "m upper bound (TSV) == block 'm.upper'": counts.get("m.upper") == block.get("m.upper"),
        "m per target (TSV) == the §4 block": dict(counts.get("m.target") or {}) == block_targets,
        "the §4 block == its transcription in launch.py": block_targets == M_PER_TARGET,
        "no upper-bound-only rows unless the block lists them": dict(counts.get("m.upper_only.target") or {}) == {
            k[len("m.upper_only.target."):]: v for k, v in block.items() if k.startswith("m.upper_only.target.")},
        "rows per gate: G1 380 / G2 194 / none 115 / G1+G2 3": dict(counts.get("gate") or {}) == GATE_ROWS,
    }


def l12_numbers(ctx: Ctx, prior: Mapping[str, dict]) -> dict:
    pre = all((prior.get(k) or {}).get("ok") is True for k in ("L1", "L2", "L3"))
    if not pre:
        return _rec("L12", "re-counted from the TSV after L1-L3", None, False,
                    {"checks": {"L1-L3 passed (the TSV is parsed only after them)": False}})
    tsv = ctx.read(TSV_PATH)
    reg = ctx.read(REGISTER_PATH)
    checks = {"TSV bytes == L2 pin": tsv is not None and sha256_bytes(lf(tsv)) == TSV_SHA256,
              "register bytes == L1 pin": reg is not None and sha256_bytes(lf(reg)) == REGISTER_SHA256}
    counts, block = None, None
    if all(checks.values()):
        _, rows = loader.parse_tsv_bytes(lf(tsv))
        counts = loader.register_counts(rows)
        block = parse_section4_block(lf(reg).decode("utf-8"))
        checks.update(l12_compare(counts, block))
    ok = all(checks.values())
    return _rec("L12", {"rows": loader.N_ROWS, "m": M_LOWER, "m.target": M_PER_TARGET, "gate": GATE_ROWS,
                        "source": "claims_register.md:1849-1896 (§4 block)"}, counts, ok, {"checks": checks})


def run_guard_selftest(guard: Path) -> dict:
    """`python -X utf8 privacy_guard.py selftest` in this interpreter (the programme venv); keeps the return code and
    the summary line only (the case lines are not kept)."""
    r = subprocess.run([sys.executable, "-X", "utf8", str(guard), "selftest"], cwd=str(guard.parent), capture_output=True,
                       timeout=1800, env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1"))
    lines = r.stdout.decode("utf-8", "replace").splitlines()
    return {"returncode": r.returncode, "summary": [ln for ln in lines if ln.startswith("privacy guard self-test:")],
            "n_lines": len(lines), "interpreter": sys.executable}


def l13_guard(ctx: Ctx, selftest_runner: Callable[[Path], dict] | None = None) -> dict:
    ok_file, d, _ = text_file(ctx, GUARD_PATH, GUARD_SHA256)
    blob_m = ctx.blob(MANIFEST_PATH)
    entry = None
    if blob_m is not None and sha256_bytes(blob_m) == MANIFEST_SHA256:
        hits = [e for e in json.loads(blob_m.decode("utf-8")).get("files", []) if e.get("path") == GUARD_PATH]
        entry = hits[0] if len(hits) == 1 else None
    checks = d["checks"]
    checks["the freeze manifest's entry for privacy_guard.py == pin"] = entry is not None and entry.get("sha256") == GUARD_SHA256
    st: dict = {}
    if not all(checks.values()):
        st = {"status": "not run (the guard's bytes failed their pin)"}
        checks["self-test passes %d / %d" % (GUARD_N, GUARD_N)] = False
    else:
        try:
            st = (selftest_runner or run_guard_selftest)(ctx.files / GUARD_PATH)
        except Exception as e:
            st = {"error": type(e).__name__}
        summ = st.get("summary") or []
        m = GUARD_SUMMARY.match(summ[0]) if len(summ) == 1 else None
        nums = tuple(int(x) for x in m.groups()) if m else None
        st["parsed"] = nums
        checks["self-test passes %d / %d" % (GUARD_N, GUARD_N)] = bool(
            st.get("returncode") == 0 and nums is not None and nums[0] == nums[1] == GUARD_N and nums[2] == nums[3])
    ok = all(checks.values())
    return _rec("L13", {"sha256": GUARD_SHA256, "selftest": "%d / %d" % (GUARD_N, GUARD_N)},
                {"lf_sha256": d.get("lf_sha256"), "selftest": st.get("parsed"), "returncode": st.get("returncode")},
                ok, {"checks": checks, "selftest": st, "file": d})


def installed_pdfplumber() -> str | None:
    from importlib import metadata
    try:
        return metadata.version("pdfplumber")
    except metadata.PackageNotFoundError:
        return None


def l14_compare(selftest_output: Mapping, frozen_record: Mapping, pdfplumber_version: str | None) -> dict:
    """L14 (RUN_PLAN.md:154): the output of `carrier_test.py selftest --workdir <dir>` (produced by the gate launcher)
    against the frozen record, plus pdfplumber == 0.11.10.

    `selftest_output` = {"returncode": int, "stdout": str, "record": <the JSON the self-test wrote to
    <workdir>/carrier_tests_selftest.json>}. Returns {check: bool}."""
    out = selftest_output if isinstance(selftest_output, Mapping) else {}
    stdout = out.get("stdout") if isinstance(out.get("stdout"), str) else ""
    rec = out.get("record") if isinstance(out.get("record"), dict) else None
    lines = stdout.splitlines()
    summ = [CARRIER_SUMMARY.match(ln) for ln in lines]
    summ = [m for m in summ if m]
    nums = (int(summ[0].group(1)), int(summ[0].group(2))) if len(summ) == 1 else None
    stamp = rec.get(CARRIER_RUN_STAMP) if rec is not None else None
    rec_wo = {k: v for k, v in rec.items() if k != CARRIER_RUN_STAMP} if rec is not None else None
    pdf = (rec or {}).get("pdf_adapter") if isinstance((rec or {}).get("pdf_adapter"), dict) else {}
    return {
        "return code 0": out.get("returncode") == 0,
        "one summary line, n caught == n cases": nums is not None and nums[0] == nums[1] and nums[1] > 0,
        "the self-test printed 'record EQUAL to the frozen ...'": sum(ln.startswith(CARRIER_EQUAL) for ln in lines) == 1,
        "no 'DIFFERS' / 'no frozen record' line": not any(("record DIFFERS" in ln or "no frozen record" in ln) for ln in lines),
        "workdir record carries the run stamp {utc, workdir} only": isinstance(stamp, dict) and sorted(stamp) == ["utc", "workdir"],
        "frozen record carries no run stamp": isinstance(frozen_record, Mapping) and CARRIER_RUN_STAMP not in frozen_record,
        "workdir record == frozen record, run stamp aside (types included)": rec_wo is not None and isinstance(
            frozen_record, Mapping) and strict_equal(rec_wo, dict(frozen_record)),
        "record n_cases == n_caught == the summary": rec is not None and nums is not None and rec.get("n_cases") == rec.get(
            "n_caught") == nums[1],
        "record's pdfplumber == %s" % PDFPLUMBER: pdf.get("pdfplumber") == PDFPLUMBER,
        "installed pdfplumber == %s" % PDFPLUMBER: pdfplumber_version == PDFPLUMBER,
    }


def l14_carrier(ctx: Ctx, gate: str | None, carrier_stage: bool, carrier_selftest: Mapping | None,
                pdfplumber_version: str | None = None) -> dict:
    if not carrier_stage:
        return _rec("L14", "carrier_test.py selftest == the frozen record; pdfplumber == %s (G1 carrier stage)" % PDFPLUMBER,
                    NOT_EXERCISED_L14, True, {"gate": gate}, status="not exercised")
    checks = {"gate is G1": gate == "G1", "self-test output given": carrier_selftest is not None}
    fb = ctx.blob(CARRIER_RECORD_PATH)
    blob_m = ctx.blob(MANIFEST_PATH)
    entry = None
    if blob_m is not None and sha256_bytes(blob_m) == MANIFEST_SHA256:
        hits = [e for e in json.loads(blob_m.decode("utf-8")).get("files", []) if e.get("path") == CARRIER_RECORD_PATH]
        entry = hits[0] if len(hits) == 1 else None
    checks["frozen record at the run commit == its manifest entry"] = bool(
        fb is not None and entry is not None and sha256_bytes(fb) == entry.get("sha256"))
    frozen = json.loads(fb.decode("utf-8")) if checks["frozen record at the run commit == its manifest entry"] else None
    pv = pdfplumber_version if pdfplumber_version is not None else installed_pdfplumber()
    if carrier_selftest is not None and frozen is not None:
        checks.update(l14_compare(carrier_selftest, frozen, pv))
    ok = all(checks.values())
    return _rec("L14", {"selftest": "equal to the frozen record (run stamps aside)", "pdfplumber": PDFPLUMBER},
                {"pdfplumber": pv}, ok, {"checks": checks})


def _gates_module():
    """Imported lazily (gates.py is WP1's gate-check module: step3v_open(repo), g1_open(repo))."""
    return importlib.import_module(__package__ + ".gates")


def l15_gate(ctx: Ctx, gate: str | None, gates_module=None) -> dict:
    if gate is None:
        return _rec("L15", "G2: step3v_open(repo); G1: g1_open(repo)", NOT_APPLICABLE_L15, True, {}, status="not applicable")
    fn_name = {"G2": "step3v_open", "G1": "g1_open"}[gate]
    detail: dict = {"function": fn_name}
    try:
        mod = gates_module if gates_module is not None else _gates_module()
        f = getattr(mod, "__file__", None)
        detail["module_file"] = str(f) if f else None
        res = getattr(mod, fn_name)(ctx.repo)
        detail["returned"] = repr(res) if not isinstance(res, bool) else res
        ok = res is True
    except Exception as e:
        detail["exception"] = type(e).__name__
        ok = False
    return _rec("L15", {"gate": gate, fn_name: True}, {"gate": gate, fn_name: detail.get("returned")}, ok, detail)


# ================================================================================================================
# launch
# ================================================================================================================
def _guarded(aid: str, fn, *args, **kw) -> dict:
    try:
        r = fn(*args, **kw)
        assert isinstance(r, dict) and r.get("id") == aid
        return r
    except Exception as e:  # an assertion that raises is a failed assertion, recorded
        return _rec(aid, "(see RUN_PLAN.md §1)", "exception %s" % type(e).__name__, False, {"exception": type(e).__name__})


def launch(repo_root, run_commit: str, gate: str | None, *, carrier_stage: bool = False,
           carrier_selftest: Mapping | None = None, files_root=None, venv_ref_python=None,
           l7_runner: Callable | None = None, guard_selftest: Callable | None = None,
           pdfplumber_version: str | None = None, gates_module=None, preload: Iterable[str] = ()) -> dict:
    """Evaluate L1-L15 (RUN_PLAN.md §1), L5a (RUN_PLAN_amend_1.md; L7 carries R35's reader chain) and L5b
    (RUN_PLAN_amend_2.md), record every one, and raise LaunchRefused (carrying the record) if any fails.
    Called before any statistic. `gate` is None (ungated), "G1" or "G2". `carrier_stage` (G1 only) requires the
    carrier self-test output (L14). `files_root`, `l7_runner`, `guard_selftest` and `gates_module` exist for P1's
    tests; a claim-bearing run leaves them at their defaults."""
    if gate not in GATES:
        raise ValueError("gate must be None, 'G1' or 'G2'")
    if carrier_stage and gate != "G1":
        raise ValueError("a carrier stage is a G1 stage")
    if carrier_selftest is not None and not carrier_stage:
        raise ValueError("carrier_selftest given outside a carrier stage")
    started = now_iso()
    for m in preload:
        importlib.import_module(m)
    ctx = make_ctx(repo_root, run_commit, files_root)
    gm = gates_module
    if gate is not None and gm is None:
        try:
            gm = _gates_module()  # before L11's snapshot, so the gate module's hash is recorded
        except Exception:
            gm = None
    res: dict[str, dict] = {}
    res["L1"] = _guarded("L1", l1_register, ctx)
    res["L2"] = _guarded("L2", l2_tsv, ctx)
    res["L3"] = _guarded("L3", l3_manifest, ctx)
    res["L4"] = _guarded("L4", l4_prereg, ctx)
    res["L5"] = _guarded("L5", l5_plan, ctx)
    res["L5a"] = _guarded("L5a", l5a_amendment, ctx)
    res["L5b"] = _guarded("L5b", l5b_amendment, ctx)
    res["L5c"] = _guarded("L5c", l5c_amendment, ctx)
    res["L6"] = _guarded("L6", l6_ahba_files, ctx)
    res["L7"] = _guarded("L7", l7_ahba_matrices, ctx, venv_ref_python, l7_runner)
    res["L8"] = _guarded("L8", l8_k1, ctx)
    res["L9"] = _guarded("L9", l9_catch, ctx)
    res["L10"] = _guarded("L10", l10_scope, ctx)
    res["L12"] = _guarded("L12", l12_numbers, ctx, {k: res[k] for k in ("L1", "L2", "L3")})
    res["L13"] = _guarded("L13", l13_guard, ctx, guard_selftest)
    res["L14"] = _guarded("L14", l14_carrier, ctx, gate, carrier_stage, carrier_selftest, pdfplumber_version)
    if gate is not None and gm is None:
        res["L15"] = _rec("L15", {"gate": gate}, None, False, {"exception": "gates module not importable"})
    else:
        res["L15"] = _guarded("L15", l15_gate, ctx, gate, gm)
    res["L11"] = _guarded("L11", l11_clean, ctx)  # last: its module snapshot covers everything the launch imported
    assertions = [res[k] for k in ASSERTION_IDS]
    failed = [a["id"] for a in assertions if not a["ok"]]
    overrides = sorted(k for k, v in (("files_root", files_root), ("l7_runner", l7_runner),
                                      ("guard_selftest", guard_selftest), ("gates_module", gates_module),
                                      ("pdfplumber_version", pdfplumber_version)) if v is not None)
    record = {
        "what": "A1 launch record (RUN_PLAN.md v3.1 §1, L1-L15; RUN_PLAN_amend_1.md L5a, R35; RUN_PLAN_amend_2.md L5b; "
                "RUN_PLAN_amend_3.md L5c)",
        "plan_sha256": PLAN_SHA256,
        "amendment_sha256": dict(AMENDMENTS),
        "repo_root": str(ctx.repo),
        "files_root": None if ctx.files == ctx.repo else str(ctx.files),
        "test_overrides": overrides,  # non-empty: a P1 test launch; never provenance, never an open gate
        "run_commit_arg": ctx.commit_arg,
        "run_commit": ctx.commit,
        "gate": gate,
        "carrier_stage": bool(carrier_stage),
        "started": started,
        "finished": now_iso(),
        "host": host_record(),
        "assertions": assertions,
        "failed": failed,
        "passed": not failed,
    }
    if failed:
        raise LaunchRefused(record)
    return record


# ================================================================================================================
# provenance (RUN_PLAN.md §2.4)
# ================================================================================================================
def _by_id(record: Mapping, aid: str) -> Mapping:
    hits = [a for a in record.get("assertions", []) if a.get("id") == aid]
    if len(hits) != 1:
        raise ProvenanceError("launch record lacks %s" % aid)
    return hits[0]


def recheck_code(launch_record: Mapping) -> dict:
    """Before a write (A3 precedent `step3v_common.recheck`): the a1_audit / asdg modules loaded now equal their hashes
    at launch, and any loaded since equal their blobs at the run commit; nothing foreign. Raises ProvenanceError."""
    repo = Path(launch_record["repo_root"])
    l11 = _by_id(launch_record, "L11")
    at_launch = dict((l11.get("observed") or {}).get("modules") or {})
    mods, foreign = code_modules(repo)
    git = Git(repo)
    now, bad = {}, []
    for rel, p in mods.items():
        s = sha256_bytes(lf(p.read_bytes()))
        now[rel] = s
        if rel in at_launch:
            if at_launch[rel] != s:
                bad.append(rel)
        else:
            b = git.blob(launch_record["run_commit"], rel)
            if b is None or sha256_bytes(b) != s:
                bad.append(rel)
    if foreign or bad:
        raise ProvenanceError("code changed since the launch or foreign modules loaded: %s" % (bad + foreign))
    return {"modules": now, "code_hash": code_hash(now), "checked_at": now_iso()}


def provenance_block(launch_record: Mapping, worktree=None, *, recheck: bool = True,
                     allow_test_overrides: bool = False) -> dict:
    """RUN_PLAN.md §2.4: the run commit and the worktree path; the code hashes, the launch-assertion values and the
    gate-check result. Refuses a launch record that did not pass, and (unless `allow_test_overrides` is passed
    explicitly, P1's tests) one whose launch ran with test stubs or a files_root."""
    if not isinstance(launch_record, Mapping) or launch_record.get("passed") is not True or launch_record.get("failed"):
        raise ProvenanceError("provenance refused: the launch did not pass")
    if (launch_record.get("test_overrides") or launch_record.get("files_root")) and not allow_test_overrides:
        raise ProvenanceError("provenance refused: the launch ran with test overrides")
    l11 = _by_id(launch_record, "L11")
    l15 = _by_id(launch_record, "L15")
    l7 = _by_id(launch_record, "L7")
    _by_id(launch_record, "L5a")
    _by_id(launch_record, "L5b")   # RUN_PLAN_amend_2.md: a launch record without L5b gives no provenance
    _by_id(launch_record, "L5c")   # RUN_PLAN_amend_3.md: a launch record without L5c gives no provenance
    if launch_record.get("amendment_sha256") != dict(AMENDMENTS):
        raise ProvenanceError("provenance refused: the launch record does not name the three amendments' pins")
    envs = (l7.get("detail") or {}).get("environments")
    if not (isinstance(envs, Mapping) and set(envs) == {"env/venv", "env/venv_ref"}):
        raise ProvenanceError("provenance refused: L7 lacks both environments' versions (RUN_PLAN_amend_1 R35)")
    block = {
        "run_commit": launch_record["run_commit"],
        "worktree": str(worktree if worktree is not None else launch_record["repo_root"]),
        "plan_sha256": launch_record.get("plan_sha256"),
        "amendment_sha256": launch_record.get("amendment_sha256"),
        "environments": {k: dict(v) for k, v in envs.items()},  # R35: pandas, numpy, Python per environment
        "matrix_first_use": first_use_records(),  # R35: the 1e-12 reader checks made in this process so far
        "gate": launch_record.get("gate"),
        "code": {"modules": (l11.get("observed") or {}).get("modules"),
                 "code_hash": (l11.get("observed") or {}).get("code_hash")},
        "launch_assertions": [dict(a) for a in launch_record["assertions"]],
        "gate_check": dict(l15),
        "launch_started": launch_record.get("started"),
        "launch_finished": launch_record.get("finished"),
        "host": launch_record.get("host"),
    }
    if recheck:
        block["code_recheck"] = recheck_code(launch_record)
    return block


def row_provenance(row: int, target_number: int, seeds: Mapping, input_hashes: Mapping[str, str], started: str,
                   finished: str, host: Mapping | None = None) -> dict:
    """RUN_PLAN.md §2.4, per row: the row's SeedSequence keys and integer seeds (R7; `seeds.seed_record`), the input
    hashes, the start and end times, and the host."""
    if not isinstance(seeds, Mapping) or seeds.get("row") != row or seeds.get("target_number") != target_number:
        raise ProvenanceError("seed record does not belong to row %r / target %r" % (row, target_number))
    bad = [k for k, v in dict(input_hashes).items() if not (isinstance(v, str) and HEX64.fullmatch(v))]
    if bad:
        raise ProvenanceError("input hashes must be sha256 hex: %s" % bad)
    return {"row": int(row), "target_number": int(target_number), "seeds": dict(seeds),
            "input_hashes": dict(sorted(input_hashes.items())), "started": started, "finished": finished,
            "host": dict(host) if host is not None else host_record()}


class RowTimer:
    """with RowTimer() as t: ...; t.started / t.finished (ISO-8601 with offset)."""

    def __enter__(self):
        self.started = now_iso()
        self.finished = None
        return self

    def __exit__(self, *exc):
        self.finished = now_iso()
        return False


def write_record(record: Mapping, path) -> str:
    """Write a JSON record (UTF-8, LF) and read it back (rule 8); returns its sha256."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(record, indent=1, ensure_ascii=False, default=str) + "\n"
    data = txt.encode("utf-8")
    p.write_bytes(data)
    back = p.read_bytes()
    if back != data or json.loads(back.decode("utf-8")) != json.loads(txt):
        raise ProvenanceError("read-back of %s differs from what was written" % p.name)
    return sha256_bytes(back)


def summary_lines(record: Mapping) -> list[str]:
    """ASCII lines 'Lk status' for the console."""
    return ["%-4s %s" % (a["id"], a["status"]) for a in record.get("assertions", [])]
