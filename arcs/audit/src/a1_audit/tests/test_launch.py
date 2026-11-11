"""P1 (RUN_PLAN.md v3.1 §7, :1127): the launch assertions refuse corrupted inputs before any statistic.

Run from arcs/audit/src:  ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_launch
Exits non-zero if any check fails. Scratch files go under $A1_SCRATCH (else the system temp dir) and are removed at the
end ($A1_KEEP_SCRATCH=1 keeps them). The real files are never edited: every corruption is made on a copy.

Part A  assertion functions pointed at a scratch COPY of every pinned file (git blobs from the real repository at HEAD):
        for each pinned file class one byte is changed, the evaluated set L1-L10, L12, L13 fails exactly where expected,
        and the unmodified copy passes; plus content checks (K1, scope, L12 counts, L14 comparison, L15 dispatch) on
        planted values.
Part B  full launch() in a scratch git repository (a copy of the frozen files at HEAD and of this package, committed):
        the clean control passes and reaches the statistic; a dirty tree, HEAD != run commit, and committed one-byte
        corruptions (K1_status changed among them) are refused, the statistic never reached.
Part C  launch() on the main working tree as it is: must refuse (L11, the tree is dirty); every assertion's status is
        printed. The privacy guard's self-test is NOT run here (it reads the HGNC table under E:\\data\\asdg\\, which
        this WP1 test does not open); L13's self-test is exercised in p1_worktree.py.
Part D  P1 extension (RUN_PLAN_amend_1.md R35): on a synthetic .csv.gz both readers' hashes are equal across pandas
        3.0.6 (env/venv) and 1.5.3 (env/venv_ref); the 1e-12 reader check passes on it and fails on a copy with one
        value moved by 1e-9. (L7's recomputation in env/venv_ref, the round-trip hash in env/venv and the default-reader
        pins on the real matrices are asserted in Part C, hashes only; both environments' versions in the provenance
        block in Part B.)
L5a (RUN_PLAN_amend_1.md), L5b (RUN_PLAN_amend_2.md) and L5c (RUN_PLAN_amend_3.md) are asserted with L5's cases (one
byte; FROZEN.txt's line; 0 CR in the blob).
L13's self-test, L14's real
carrier self-test and L15's real gate checks run in stubs here; the real ones run at integration (p1_worktree.py; the
gate launcher).
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import types
from pathlib import Path

from a1_audit import launch as L
from a1_audit import loader

REPO = Path(__file__).resolve().parents[5]
SRC = REPO / "arcs" / "audit" / "src"
PKG = SRC / "a1_audit"
VENV_REF = (Path(subprocess.run(["git", "-C", str(REPO), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                 capture_output=True, text=True).stdout.strip()).parent
            / "env" / "venv_ref" / "Scripts" / "python.exe")          # env/ lives in the main tree only
RESULTS: list[tuple[str, bool]] = []


def check(name: str, cond) -> bool:
    RESULTS.append((name, bool(cond)))
    print("%s  %s" % ("PASS" if cond else "FAIL", name))
    return bool(cond)


def git(root: Path, *args, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=off", "-c", "core.autocrlf=false", *args],
                          capture_output=True, env=env)


def head_of(root: Path) -> str:
    return git(root, "rev-parse", "HEAD").stdout.decode().strip()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def one_byte(data: bytes, pos: int | None = None) -> bytes:
    """`data` with exactly one byte changed: an ASCII digit / letter at or after the middle moves to the next of its
    class (text stays parseable); for binary data the byte at the middle is XOR 1."""
    b = bytearray(data)
    if pos is None:
        pos = len(b) // 2
        while pos < len(b) and not chr(b[pos]).isalnum():
            pos += 1
        if pos >= len(b):
            pos = len(b) // 2
    c = b[pos]
    if 48 <= c <= 57:
        b[pos] = 48 + (c - 48 + 1) % 10
    elif 97 <= c <= 122:
        b[pos] = 97 + (c - 97 + 1) % 26
    elif 65 <= c <= 90:
        b[pos] = 65 + (c - 65 + 1) % 26
    else:
        b[pos] = c ^ 1
    out = bytes(b)
    assert sum(x != y for x, y in zip(out, data)) == 1 and len(out) == len(data)
    return out


def rmtree(p: Path) -> None:
    def onerr(func, path, _exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    if p.exists():
        shutil.rmtree(p, onerror=onerr)


def frozen_paths() -> list[str]:
    """Every tracked file the assertions read (the manifest's 36 entries included)."""
    man = json.loads(git(REPO, "cat-file", "blob", "HEAD:" + L.MANIFEST_PATH).stdout.decode("utf-8"))
    paths = [L.FROZEN_TXT, L.REGISTER_PATH, L.TSV_PATH, L.MANIFEST_PATH, L.PLAN_PATH, L.AMEND1_PATH, L.AMEND2_PATH,
             L.AMEND3_PATH,
             L.GATES_A5_PATH,
             L.GATES_A3_PATH, L.CATCH_PATH, L.E4_MATRICES_JSON] + ["%s/%s" % (L.AUDIT_DIR, n) for n, _ in L.PREREG]
    paths += [e["path"] for e in man["files"]]
    return sorted(set(paths))


AHBA = ["%s/%s" % (L.AHBA_DIR, n) for n, _ in L.AHBA_FILES]


# ================================================================================================================
# Part A: assertion functions on copies
# ================================================================================================================
def guard_stub(calls: list):
    def run(p: Path) -> dict:
        calls.append(1)
        return {"returncode": 0, "summary": ["privacy guard self-test: 46 / 46 (planted failures caught 37 / 37)"],
                "stub": True}
    return run


def evaluate(ctx: L.Ctx, calls: list) -> dict:
    r = {"L1": L.l1_register(ctx), "L2": L.l2_tsv(ctx), "L3": L.l3_manifest(ctx), "L4": L.l4_prereg(ctx),
         "L5": L.l5_plan(ctx), "L5a": L.l5a_amendment(ctx), "L5b": L.l5b_amendment(ctx),
         "L5c": L.l5c_amendment(ctx),
         "L6": L.l6_ahba_files(ctx),
         "L7": L.l7_ahba_matrices(ctx, VENV_REF),
         "L8": L.l8_k1(ctx), "L9": L.l9_catch(ctx), "L10": L.l10_scope(ctx)}
    r["L12"] = L.l12_numbers(ctx, r)
    r["L13"] = L.l13_guard(ctx, guard_stub(calls))
    return r


def failed(r: dict) -> set:
    return {k for k, v in r.items() if not v["ok"]}


def part_a(scratch: Path) -> None:
    print("--- Part A: assertion functions on a scratch copy (git: the real repository at HEAD)")
    head = head_of(REPO)
    copy = scratch / "copy"
    for rel in frozen_paths() + AHBA:
        dst = copy / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, dst)  # raw bytes: the main tree's CRLF copies stay CRLF (LF normalisation tested)
    g5 = copy / L.GATES_A5_PATH
    if b"\r" not in g5.read_bytes():     # a worktree's LF checkout: the CRLF form of the same blob, so A0 still
        g5.write_bytes(g5.read_bytes().replace(b"\n", b"\r\n"))    # tests the LF normalisation (2026-10-16)
    ctx_new = lambda: L.make_ctx(REPO, head, files_root=copy)  # noqa: E731
    calls: list = []
    base = evaluate(ctx_new(), calls)
    check("A0 control: the unmodified copy passes L1-L10, L12, L13 (self-test stubbed)", failed(base) == set())
    check("A0 control: the copy holds CRLF files (main-tree working copies) and still passes", (copy / L.GATES_A5_PATH).read_bytes().count(b"\r") > 0)

    def case(name: str, rel: str, mutate, expect: set, extra=None):
        p = copy / rel
        orig = p.read_bytes()
        try:
            p.write_bytes(mutate(orig))
            calls.clear()
            r = evaluate(ctx_new(), calls)
            got = failed(r)
            ok = check("A %s: refused by %s (got %s)" % (name, ",".join(sorted(expect)), ",".join(sorted(got)) or "-"),
                       got == expect)
            if extra:
                extra(r, calls)
            return ok
        finally:
            p.write_bytes(orig)
            assert sha(p.read_bytes()) == sha(orig)

    case("register one byte", L.REGISTER_PATH, one_byte, {"L1", "L12"})
    case("TSV one byte", L.TSV_PATH, one_byte, {"L2", "L3", "L12"})
    case("freeze manifest one byte", L.MANIFEST_PATH, one_byte, {"L3", "L12"})
    case("manifest entry register_maps/mist64_classes.json one byte", "arcs/audit/register_maps/mist64_classes.json",
         one_byte, {"L3", "L12"})
    case("manifest entry src_register/s_build.py one byte", L.S_BUILD_PATH, one_byte, {"L3", "L12"})
    case("prereg_amend_3.md one byte", "arcs/audit/prereg_amend_3.md", one_byte, {"L4"})
    case("RUN_PLAN.md one byte", L.PLAN_PATH, one_byte, {"L5"})
    case("RUN_PLAN_amend_1.md one byte (L5a, RUN_PLAN_amend_1.md)", L.AMEND1_PATH, one_byte, {"L5a"})
    case("RUN_PLAN_amend_2.md one byte (L5b, RUN_PLAN_amend_2.md)", L.AMEND2_PATH, one_byte, {"L5b"})
    case("RUN_PLAN_amend_3.md one byte (L5c, RUN_PLAN_amend_3.md)", L.AMEND3_PATH, one_byte, {"L5c"})
    case("FROZEN.txt one byte", L.FROZEN_TXT, one_byte, {"L1", "L4", "L5", "L5a", "L5b", "L5c", "L12"})
    case("AHBA dk_expr.csv.gz one byte", "artifacts/ahba/dk_expr.csv.gz", lambda b: one_byte(b, len(b) // 2), {"L6", "L7"})
    case("AHBA aal_atlas_info.csv one byte", "artifacts/ahba/aal_atlas_info.csv", one_byte, {"L6"})

    def regzip_same(b: bytes) -> bytes:
        return gzip.compress(gzip.decompress(b), mtime=0)

    def regzip_value(b: bytes) -> bytes:
        t = bytearray(gzip.decompress(b))
        nl = t.index(b"\n")
        comma = t.index(b",", nl)
        pos = comma + 1
        while not chr(t[pos]).isdigit():
            pos += 1
        t[pos] = 48 + (t[pos] - 48 + 1) % 10
        return gzip.compress(bytes(t), mtime=0)

    case("AHBA mist64 matrix re-gzipped, same content (file pin only)", "artifacts/ahba/mist64_expr.csv.gz", regzip_same,
         {"L6"})
    case("AHBA mist64 matrix one value digit changed, re-gzipped", "artifacts/ahba/mist64_expr.csv.gz", regzip_value,
         {"L6", "L7"})
    case("e3_gates_a5.json one byte", L.GATES_A5_PATH, one_byte, {"L8", "L10"})

    def k1_fired(b: bytes) -> bytes:
        assert b.count(b'"K1_status": "not fired"') == 1
        return b.replace(b'"K1_status": "not fired"', b'"K1_status": "fired"')

    case("e3_gates_a5.json K1_status 'not fired' -> 'fired'", L.GATES_A5_PATH, k1_fired, {"L8", "L10"},
         extra=lambda r, c: check("A   ... and L8's content check K1_status itself fails",
                                  r["L8"]["detail"]["checks"].get("K1_status == 'not fired'") is False))
    case("e3_gates_a3.json one byte (gates_json CRLF pin)", L.GATES_A3_PATH, one_byte, {"L8"})
    case("e3_catch_curves_a5.json one byte", L.CATCH_PATH, one_byte, {"L9"})
    case("privacy_guard.py one byte", L.GUARD_PATH, one_byte, {"L3", "L12", "L13"},
         extra=lambda r, c: check("A   ... and the guard's self-test was not started", len(c) == 0))

    # ---- content checks on planted values (no hashes involved)
    doc = json.loads(L.lf((REPO / L.GATES_A5_PATH).read_bytes()).decode("utf-8"))
    check("A K1 content: the real e3_gates_a5.json passes every content check", all(L.k1_semantics(doc).values()))
    for key, val, label in (("K1_status", "fired", "K1_status 'fired'"), ("stop", True, "stop true"),
                            ("dirty", True, "dirty true"), ("partial_certification", ["x"], "partial_certification non-empty"),
                            ("stop", 0, "stop 0 (not the boolean false)")):
        d2 = dict(doc)
        d2[key] = val
        check("A K1 content: %s refused" % label, not all(L.k1_semantics(d2).values()))
    d2 = dict(doc)
    d2["gates_json"] = dict(doc["gates_json"], sha256="0" * 64)
    check("A K1 content: gates_json sha256 changed refused", not all(L.k1_semantics(d2).values()))
    check("A scope content: the real e3_gates_a5.json passes L10's checks", all(L.scope_semantics(doc).values()))
    d2 = dict(doc, scope_labels=doc["scope_labels"][:2])
    check("A scope content: a label dropped refused", not all(L.scope_semantics(d2).values()))
    d2 = dict(doc, scope_labels=doc["scope_labels"] + ["brain-enrichment (N1) confound untested: dk-ctx claims with brain-enriched sets"])
    check("A scope content: a dk-ctx N1 label added refused", not all(L.scope_semantics(d2).values()))
    rep = json.loads(json.dumps(doc["replica_section_4_4"]))
    rep["c"]["k"] = 40
    check("A scope content: replica (c) at 40 / 1000 (<= .05) refused", not all(L.scope_semantics(dict(doc, replica_section_4_4=rep)).values()))
    rep = json.loads(json.dumps(doc["replica_section_4_4"]))
    rep["a"]["k"] = 151
    check("A scope content: replica (a) k changed refused", not all(L.scope_semantics(dict(doc, replica_section_4_4=rep)).values()))

    # ---- L12 counting on planted rows
    _, rows = loader.parse_tsv_bytes(L.lf((REPO / L.TSV_PATH).read_bytes()))
    block = L.parse_section4_block(L.lf((REPO / L.REGISTER_PATH).read_bytes()).decode("utf-8"))
    check("A L12: the real TSV and the section 4 block agree", all(L.l12_compare(loader.register_counts(rows), block).values()))
    yes = next(r for r in rows if r.in_m)
    f = yes.fields
    f["verdict_counted_in_m"] = "no"
    rows2 = [loader.Row(f, yes.line) if r is yes else r for r in rows]
    check("A L12: one m row flipped to 'no' refused", not all(L.l12_compare(loader.register_counts(rows2), block).values()))
    g1 = next(r for r in rows if r.gate == "G1")
    f = g1.fields
    f["gate"], f["status"] = "G2", f["status"].replace("gate G1 closed", "gate G2 closed", 1)
    rows3 = [loader.Row(f, g1.line) if r is g1 else r for r in rows]
    check("A L12: one row moved from G1 to G2 refused", not all(L.l12_compare(loader.register_counts(rows3), block).values()))
    b2 = dict(block)
    b2["m.target.hansen2022local"] = 2
    check("A L12: a section-4 block value differing from its transcription refused",
          not all(L.l12_compare(loader.register_counts(rows), b2).values()))

    # ---- L14 comparison with fake outputs only (the real carrier self-test runs under the gate launcher)
    frozen = {"what": "synthetic frozen record", "n_cases": 3, "n_caught": 3, "cases": [{"case": "a", "caught": True}],
              "pdf_adapter": {"pdfplumber": "0.11.10", "pinned_in_spec": "0.11.10"}, "script_sha256": "1" * 64}
    good_rec = dict(json.loads(json.dumps(frozen)), run={"utc": "2026-10-01T00:00:00+00:00", "workdir": "W"})
    good_out = {"returncode": 0, "record": good_rec,
                "stdout": "[CAUGHT] x\nselftest: 3 / 3 cases classified as planted\n%s\n" % L.CARRIER_EQUAL}
    check("A L14: a fake passing self-test output equals the frozen record", all(L.l14_compare(good_out, frozen, "0.11.10").values()))
    bad = []
    bad.append(("return code 1", dict(good_out, returncode=1), "0.11.10"))
    bad.append(("summary 2 / 3", dict(good_out, stdout=good_out["stdout"].replace("3 / 3", "2 / 3")), "0.11.10"))
    bad.append(("EQUAL line missing", dict(good_out, stdout="selftest: 3 / 3 cases classified as planted\n"), "0.11.10"))
    bad.append(("DIFFERS line", dict(good_out, stdout=good_out["stdout"] + "record DIFFERS from the frozen x at 1 key paths: /n\n"), "0.11.10"))
    r2 = json.loads(json.dumps(good_rec)); del r2["run"]
    bad.append(("run stamp missing", dict(good_out, record=r2), "0.11.10"))
    r2 = json.loads(json.dumps(good_rec)); r2["cases"][0]["caught"] = False
    bad.append(("record differs in one nested value", dict(good_out, record=r2), "0.11.10"))
    r2 = json.loads(json.dumps(good_rec)); r2["n_cases"] = 3.0
    bad.append(("record differs in type only (3 vs 3.0)", dict(good_out, record=r2), "0.11.10"))
    r2 = json.loads(json.dumps(good_rec)); r2["pdf_adapter"]["pdfplumber"] = "0.11.9"
    bad.append(("record's pdfplumber 0.11.9", dict(good_out, record=r2), "0.11.10"))
    bad.append(("installed pdfplumber 0.11.9", good_out, "0.11.9"))
    bad.append(("installed pdfplumber absent", good_out, None))
    for label, out, pv in bad:
        check("A L14: %s refused" % label, not all(L.l14_compare(out, frozen, pv).values()))
    ctx = L.make_ctx(REPO, head)
    r = L.l14_carrier(ctx, None, False, None)
    check("A L14: outside a G1 carrier stage -> 'not exercised (no G1 carrier stage)', ok",
          r["ok"] and r["status"] == "not exercised" and r["observed"] == L.NOT_EXERCISED_L14)

    class FakeCtx(L.Ctx):
        def blob(self, rel):
            return fake_blobs.get(rel, super().blob(rel))

    fake_frozen_bytes = json.dumps(frozen).encode("utf-8")
    fake_manifest = json.dumps({"files": [{"path": L.CARRIER_RECORD_PATH, "sha256": sha(fake_frozen_bytes)}]}).encode()
    fake_blobs = {L.MANIFEST_PATH: fake_manifest, L.CARRIER_RECORD_PATH: fake_frozen_bytes}
    saved = L.MANIFEST_SHA256
    try:
        L.MANIFEST_SHA256 = sha(fake_manifest)
        fctx = FakeCtx(repo=ctx.repo, commit=ctx.commit, commit_arg=ctx.commit_arg, files=ctx.files, git=ctx.git)
        check("A L14 plumbing (synthetic frozen record and manifest): carrier stage passes",
              L.l14_carrier(fctx, "G1", True, good_out, "0.11.10")["ok"])
        check("A L14 plumbing: carrier stage without the self-test output refused",
              not L.l14_carrier(fctx, "G1", True, None, "0.11.10")["ok"])
        check("A L14 plumbing: a record differing from the frozen one refused",
              not L.l14_carrier(fctx, "G1", True, bad[5][1], "0.11.10")["ok"])
        fake_blobs[L.CARRIER_RECORD_PATH] = one_byte(fake_frozen_bytes)
        check("A L14 plumbing: a frozen record differing from its manifest entry refused",
              not L.l14_carrier(fctx, "G1", True, good_out, "0.11.10")["ok"])
    finally:
        L.MANIFEST_SHA256 = saved

    # ---- L15 dispatch with stub gate modules (the real gates.py is exercised at integration, p1_worktree.py)
    def stub(s3v, g1):
        return types.SimpleNamespace(step3v_open=lambda repo: s3v(repo), g1_open=lambda repo: g1(repo))

    def boom(repo):
        raise RuntimeError("x")

    T, F = (lambda repo: True), (lambda repo: False)
    check("A L15: ungated -> not applicable, ok", L.l15_gate(ctx, None)["status"] == "not applicable")
    check("A L15: G2 with step3v_open True passes", L.l15_gate(ctx, "G2", stub(T, F))["ok"])
    check("A L15: G2 with step3v_open False refused", not L.l15_gate(ctx, "G2", stub(F, T))["ok"])
    check("A L15: G2 with step3v_open raising refused", not L.l15_gate(ctx, "G2", stub(boom, T))["ok"])
    check("A L15: G2 with step3v_open returning 1 (not True) refused", not L.l15_gate(ctx, "G2", stub(lambda r: 1, T))["ok"])
    check("A L15: G1 with g1_open True passes", L.l15_gate(ctx, "G1", stub(F, T))["ok"])
    check("A L15: G1 with g1_open False refused (step3v_open True does not open G1)", not L.l15_gate(ctx, "G1", stub(T, F))["ok"])
    seen = []
    L.l15_gate(ctx, "G2", stub(lambda r: seen.append(Path(r)) or True, T))
    check("A L15: the gate check receives the repository root", seen == [ctx.repo])
    for kw, label in (({"gate": "G3"}, "gate G3"), ({"gate": "G2", "carrier_stage": True}, "carrier stage under G2"),
                      ({"gate": "G1", "carrier_selftest": {}}, "carrier output outside a carrier stage")):
        try:
            g = kw.pop("gate")
            L.launch(REPO, head, g, **kw)
            check("A launch(): %s rejected" % label, False)
        except ValueError:
            check("A launch(): %s rejected before any assertion" % label, True)
        except L.LaunchRefused:
            check("A launch(): %s rejected" % label, False)


# ================================================================================================================
# Part B: full launch() in a scratch git repository
# ================================================================================================================
_B_SCRIPT = r"""
import json, sys, types
from a1_audit import launch as L, seeds as S
a = json.loads(sys.argv[1])
calls = []
def guard_stub(p):
    calls.append(1)
    return {"returncode": 0, "summary": ["privacy guard self-test: 46 / 46 (planted failures caught 37 / 37)"], "stub": True}
gm = types.SimpleNamespace(step3v_open=lambda repo: a["s3v"], g1_open=lambda repo: a["g1"]) if a["gate"] else None
out = {"statistic_computed": False}
try:
    rec = L.launch(a["repo"], a["commit"], a["gate"], venv_ref_python=a["venv_ref"], guard_selftest=guard_stub,
                   gates_module=gm)
    out["statistic_computed"] = True  # a runner's first statistic would be computed here, after launch() returned
    out["test_overrides"] = rec["test_overrides"]
    if a.get("provenance"):
        try:
            L.provenance_block(rec, a["repo"])
            out["prov_refused_without_flag"] = False
        except L.ProvenanceError:
            out["prov_refused_without_flag"] = True
        blk = L.provenance_block(rec, a["repo"], allow_test_overrides=True)
        with L.RowTimer() as t:
            sr = S.seed_record(1, 1, 0, 0, {"S1c": "int", "S2c": "int", "G1": "rng"}, g3=True, j1=True, naive_joint=True)
        rp = L.row_provenance(1, 1, sr, {"map": "0" * 64}, t.started, t.finished)
        out["provenance_sha256"] = L.write_record({"provenance": blk, "row": rp}, a["provenance"])
        out["provenance_keys"] = sorted(blk)
except L.LaunchRefused as e:
    rec = e.record
out["passed"] = rec["passed"]
out["failed"] = rec["failed"]
out["statuses"] = {x["id"]: x["status"] for x in rec["assertions"]}
out["guard_calls"] = len(calls)
l11 = [x for x in rec["assertions"] if x["id"] == "L11"][0]
out["l11_modules"] = sorted(((l11.get("observed") or {}).get("modules") or {}))
out["fail_checks"] = {x["id"]: [k for k, v in (x["detail"].get("checks") or {}).items() if not v]
                      for x in rec["assertions"] if not x["ok"]}
print(json.dumps(out))
"""

GIT_ENV = dict(os.environ, GIT_AUTHOR_NAME="a1 p1 scratch", GIT_AUTHOR_EMAIL="p1@scratch.invalid",
               GIT_COMMITTER_NAME="a1 p1 scratch", GIT_COMMITTER_EMAIL="p1@scratch.invalid")


def commit(root: Path, msg: str) -> str:
    assert git(root, "add", "-A", env=GIT_ENV).returncode == 0
    r = git(root, "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", msg, env=GIT_ENV)
    assert r.returncode == 0, r.stderr
    return head_of(root)


def run_launch(root: Path, commit_: str, gate=None, s3v=True, g1=True, provenance: Path | None = None) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    arg = json.dumps({"repo": str(root), "commit": commit_, "gate": gate, "s3v": s3v, "g1": g1,
                      "venv_ref": str(VENV_REF), "provenance": str(provenance) if provenance else None})
    r = subprocess.run([sys.executable, "-X", "utf8", "-c", _B_SCRIPT, arg], cwd=str(root / "arcs" / "audit" / "src"),
                       capture_output=True, env=env, timeout=1800)
    lines = [ln for ln in r.stdout.decode("utf-8", "replace").splitlines() if ln.strip()]
    if r.returncode != 0 or not lines:
        return {"error": r.stderr.decode("utf-8", "replace")[-400:], "passed": None, "failed": None}
    return json.loads(lines[-1])


def part_b(scratch: Path) -> None:
    print("--- Part B: full launch() in a scratch git repository")
    root = scratch / "repo"
    root.mkdir(parents=True)
    assert git(root, "init", "-q").returncode == 0
    for rel in [".gitattributes", ".gitignore"] + frozen_paths():
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(git(REPO, "cat-file", "blob", "HEAD:" + rel).stdout)  # the LF checkout of a fresh worktree
    for name in ("__init__.py", "launch.py", "loader.py", "seeds.py", "tests/__init__.py"):
        dst = root / "arcs/audit/src/a1_audit" / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((PKG / name).read_bytes())
    for rel in AHBA:
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, dst)  # artifacts/ is gitignored: never committed
    c0 = commit(root, "scratch P1 base")
    check("B setup: scratch repository clean after commit", git(root, "status", "--porcelain", "--untracked-files=all").stdout.strip() == b"")

    prov = scratch / "prov" / "provenance.json"
    r = run_launch(root, c0, provenance=prov)
    check("B0 control: clean scratch tree passes L1-L15 and reaches the statistic (L13 self-test, L15 stubbed) %s"
          % (r.get("failed") or r.get("error", "")), r.get("passed") is True and r.get("statistic_computed") is True)
    check("B0 control: L14 'not exercised', L15 'not applicable' (ungated)",
          (r.get("statuses") or {}).get("L14") == "not exercised" and (r.get("statuses") or {}).get("L15") == "not applicable")
    check("B0 control: L11 recorded the scratch tree's a1_audit modules",
          {"arcs/audit/src/a1_audit/launch.py", "arcs/audit/src/a1_audit/loader.py"} <= set(r.get("l11_modules") or []))
    check("B0 control: the record lists its test stubs; provenance_block refuses it without allow_test_overrides",
          r.get("test_overrides") == ["guard_selftest"] and r.get("prov_refused_without_flag") is True)
    check("B0 control: provenance block and per-row record written and read back",
          bool(r.get("provenance_sha256")) and prov.is_file() and sha(prov.read_bytes()) == r.get("provenance_sha256"))
    if prov.is_file():
        pd = json.loads(prov.read_text(encoding="utf-8"))
        row = pd["row"]
        check("B0 control: per-row provenance holds keys, integer seeds, input hashes, times, host",
              row["seeds"]["legs"][0]["key"]["entropy"] == [20260925, 101, 1, 0, 0, 0] and "seed_int" in row["seeds"]["legs"][0]
              and "S1c_seed" in row["seeds"]["J1"] and row["seeds"]["G3"]["key"]["spawn_key"] == [0]
              and row["input_hashes"] == {"map": "0" * 64} and row["started"] and row["finished"] and "node" in row["host"])
        check("B0 control (RUN_PLAN_amend_1 R34): the per-row record holds the numpy version (%s)" % row["host"].get("numpy"),
              row["host"].get("numpy") == "2.4.6" and row["host"].get("pandas") == "3.0.6")
        check("B0 control: provenance block holds run commit, worktree, code hashes, all 18 assertions (L1-L15, L5a, "
              "L5b, L5c), gate check",
              pd["provenance"]["run_commit"] == c0 and len(pd["provenance"]["launch_assertions"]) == 18
              and [a["id"] for a in pd["provenance"]["launch_assertions"]] == list(L.ASSERTION_IDS)
              and pd["provenance"]["code"]["code_hash"] and pd["provenance"]["gate_check"]["id"] == "L15")
        envs = pd["provenance"].get("environments") or {}
        check("B0 control (P1 extension, R35): both environments' pandas / numpy / Python versions in the provenance "
              "block %s" % json.dumps(envs),
              set(envs) == {"env/venv", "env/venv_ref"} and envs["env/venv"].get("pandas") == "3.0.6"
              and envs["env/venv_ref"].get("pandas") == "1.5.3"
              and all(envs[e].get(k) for e in envs for k in ("pandas", "numpy", "python")))
        check("B0 control: the provenance block names the three amendments' pins (L5a, L5b, L5c)",
              pd["provenance"].get("amendment_sha256") == {"RUN_PLAN_amend_1.md": L.AMEND1_SHA256,
                                                           "RUN_PLAN_amend_2.md": L.AMEND2_SHA256,
                                                           "RUN_PLAN_amend_3.md": L.AMEND3_SHA256})
    rmtree(prov.parent)

    r = run_launch(root, c0, gate="G2", s3v=True)
    check("B gate G2 (stub step3v_open True): passes, L15 pass", r.get("passed") is True and (r.get("statuses") or {}).get("L15") == "pass")
    r = run_launch(root, c0, gate="G1", g1=False)
    check("B gate G1 (stub g1_open False): refused by L15 only, statistic not reached",
          r.get("failed") == ["L15"] and r.get("statistic_computed") is False)

    def expect(label: str, r: dict, want: set):
        check("B %s: refused by %s, statistic not reached (got %s)" % (label, ",".join(sorted(want)), r.get("failed")),
              set(r.get("failed") or []) == want and r.get("passed") is False and r.get("statistic_computed") is False)
        return r

    # dirty trees
    (root / "untracked.txt").write_text("x\n", encoding="utf-8")
    expect("dirty tree (one untracked file)", run_launch(root, c0), {"L11"})
    (root / "untracked.txt").unlink()
    p = root / L.GATES_A5_PATH
    orig = p.read_bytes()
    p.write_bytes(one_byte(orig))
    expect("dirty tree (e3_gates_a5.json modified, uncommitted)", run_launch(root, c0), {"L8", "L10", "L11"})
    p.write_bytes(orig)
    check("B restored: tree clean again", git(root, "status", "--porcelain", "--untracked-files=all").stdout.strip() == b"")
    # HEAD != run commit
    c1 = commit(root, "empty commit")
    expect("HEAD != the run commit named", run_launch(root, c0), {"L11"})
    r = run_launch(root, c1)
    check("B the same tree at its own HEAD passes", r.get("passed") is True)

    # committed one-byte corruptions (the blob and the worktree both differ from the pin; the tree is clean)
    def committed(label: str, rel: str, mutate, want: set, extra=None):
        q = root / rel
        o = q.read_bytes()
        q.write_bytes(mutate(o))
        c = commit(root, "corrupt " + rel)
        r = expect(label, run_launch(root, c), want)
        if extra:
            extra(r)
        q.write_bytes(o)
        c_back = commit(root, "restore " + rel)
        check("B restored %s: passes again" % rel, run_launch(root, c_back).get("passed") is True)

    def k1_fired(b: bytes) -> bytes:
        return b.replace(b'"K1_status": "not fired"', b'"K1_status": "fired"')

    committed("committed: register one byte", L.REGISTER_PATH, one_byte, {"L1", "L12"})
    committed("committed: e3_gates_a5.json K1_status changed", L.GATES_A5_PATH, k1_fired, {"L8", "L10"},
              extra=lambda r: check("B   ... L8's failed checks include K1_status",
                                    "K1_status == 'not fired'" in (r.get("fail_checks") or {}).get("L8", [])))
    committed("committed: privacy_guard.py one byte", L.GUARD_PATH, one_byte, {"L3", "L12", "L13"},
              extra=lambda r: check("B   ... the guard's self-test was not started", r.get("guard_calls") == 0))
    committed("committed: manifest entry mist64_ahba_matrix.json one byte (abagen version)",
              L.MIST64_MATRIX_JSON, lambda b: b.replace(b'"abagen": "0.1.3"', b'"abagen": "0.1.4"'), {"L3", "L12"})
    committed("committed: e3_catch_curves_a5.json one byte", L.CATCH_PATH, one_byte, {"L9"})
    committed("committed: TSV one byte", L.TSV_PATH, one_byte, {"L2", "L3", "L12"})

    def plan_line(b: bytes) -> bytes:
        i = b.index(L.PLAN_SHA256.encode())
        return one_byte(b, i + 5)

    committed("committed: FROZEN.txt's RUN_PLAN.md hash one byte", L.FROZEN_TXT, plan_line, {"L5"})

    def amend_line(b: bytes) -> bytes:
        i = b.index(L.AMEND1_SHA256.encode())
        return one_byte(b, i + 5)

    committed("committed: FROZEN.txt's RUN_PLAN_amend_1.md hash one byte (L5a)", L.FROZEN_TXT, amend_line, {"L5a"})
    committed("committed: RUN_PLAN_amend_1.md one byte (L5a)", L.AMEND1_PATH, one_byte, {"L5a"})

    def amend2_line(b: bytes) -> bytes:
        i = b.index(L.AMEND2_SHA256.encode())
        return one_byte(b, i + 5)

    committed("committed: FROZEN.txt's RUN_PLAN_amend_2.md hash one byte (L5b)", L.FROZEN_TXT, amend2_line, {"L5b"})
    committed("committed: RUN_PLAN_amend_2.md one byte (L5b)", L.AMEND2_PATH, one_byte, {"L5b"})

    def amend3_line(b: bytes) -> bytes:
        i = b.index(L.AMEND3_SHA256.encode())
        return one_byte(b, i + 5)

    committed("committed: FROZEN.txt's RUN_PLAN_amend_3.md hash one byte (L5c)", L.FROZEN_TXT, amend3_line, {"L5c"})
    committed("committed: RUN_PLAN_amend_3.md one byte (L5c)", L.AMEND3_PATH, one_byte, {"L5c"})
    # the AHBA matrix (gitignored artifacts): one byte
    q = root / "artifacts/ahba/dk_expr.csv.gz"
    o = q.read_bytes()
    q.write_bytes(one_byte(o, len(o) // 2))
    expect("AHBA dk_expr.csv.gz one byte (ignored file; tree clean)", run_launch(root, c_head(root)), {"L6", "L7"})
    q.write_bytes(o)


def c_head(root: Path) -> str:
    return head_of(root)


# ================================================================================================================
# Part C: the main working tree as it is
# ================================================================================================================
def part_c() -> None:
    print("--- Part C: launch() on the main working tree as it is (gate None; guard self-test not run by WP1)")
    head = head_of(REPO)

    def not_run(p: Path) -> dict:
        return {"status": "not run (WP1: the self-test reads the HGNC table under E:\\data\\asdg\\; run in p1_worktree.py)"}

    try:
        L.launch(REPO, head, None, guard_selftest=not_run)
        check("C main tree: launch() refused", False)
        return
    except L.LaunchRefused as e:
        rec = e.record
    by = {a["id"]: a for a in rec["assertions"]}
    for a in rec["assertions"]:
        bad = [k for k, v in (a["detail"].get("checks") or {}).items() if not v]
        print("     %-4s %-15s %s" % (a["id"], a["status"], ("failed: " + "; ".join(bad)) if bad else ""))
    # the tree as it is: the main tree is dirty (L11 fails); a fresh worktree is clean (L11's porcelain check holds)
    dirty = bool(git(REPO, "status", "--porcelain", "--untracked-files=all").stdout.strip())
    check("C main tree: launch() refused, L11 among the failures iff the tree is dirty",
          ("L11" in rec["failed"]) == dirty)
    check("C main tree: L11's porcelain check == the tree's cleanliness, HEAD == run commit held",
          by["L11"]["detail"]["checks"]["git status --porcelain (untracked included) is empty"] is (not dirty)
          and by["L11"]["detail"]["checks"]["HEAD == the run commit"] is True)
    check("C main tree: L1-L10, L5a, L5b, L5c and L12 pass",
          all(by["L%d" % i]["ok"] for i in list(range(1, 11)) + [12]) and by["L5a"]["ok"] and by["L5b"]["ok"]
          and by["L5c"]["ok"])
    r35 = by["L7"]["detail"]["R35"]
    print("     R35 reader chain: env/venv %s; env/venv_ref %s" % (json.dumps(r35["env/venv"]["versions"]),
                                                                    json.dumps(r35["env/venv_ref"]["versions"])))
    check("C main tree (P1 extension, R35): L7 recomputed in env/venv_ref equals the pins (round-trip reader)",
          all(by["L7"]["detail"]["checks"]["%s hash_pandas_object sha256 == pin" % a] for a, _ in L.AHBA_MATRIX)
          and r35["env/venv_ref"]["round_trip"] == dict(L.AHBA_MATRIX))
    check("C main tree (P1 extension, R35): the round-trip read's hash in env/venv equals the L7 pin",
          r35["env/venv"]["round_trip"] == dict(L.AHBA_MATRIX))
    check("C main tree (P1 extension, R35): default-reader hashes equal across env/venv and env/venv_ref and the R35 "
          "pins", r35["env/venv"]["default"] == r35["env/venv_ref"]["default"] == dict(L.AHBA_DEFAULT_READER))
    check("C main tree (P1 extension, R35): versions pandas 3.0.6 (env/venv) / 1.5.3 (env/venv_ref) recorded",
          r35["env/venv"]["versions"]["pandas"] == "3.0.6" and r35["env/venv_ref"]["versions"]["pandas"] == "1.5.3")
    check("C main tree: L13's hash checks pass; only its self-test (not run) fails",
          [k for k, v in by["L13"]["detail"]["checks"].items() if not v] == ["self-test passes 46 / 46"])
    try:
        L.provenance_block(rec)
        check("C provenance_block refuses a refused launch record", False)
    except L.ProvenanceError:
        check("C provenance_block refuses a refused launch record", True)
    try:
        loader.load(REPO, rec)
        check("C loader refuses a refused launch (no allow_unlaunched)", False)
    except loader.LoaderRefused:
        check("C loader refuses a refused launch (no allow_unlaunched)", True)


# ================================================================================================================
# Part D: P1 extension (RUN_PLAN_amend_1.md R35) on synthetic matrices
# ================================================================================================================
def _synthetic_matrix(path: Path, seed: int = 5) -> None:
    """A synthetic parcels x genes .csv.gz (values printed with 17 significant digits, as a round-trip writer does; a
    missing-value cell and an all-missing row included). Synthetic only: no AHBA value is read or written."""
    import random
    rnd = random.Random(seed)
    genes = ["g%d" % j for j in range(40)]
    lines = ["id," + ",".join(genes)]
    for i in range(1, 13):
        vals = ["%.17g" % (rnd.uniform(-3, 3) * 10 ** rnd.randint(-3, 2)) for _ in genes]
        if i == 4:
            vals[7] = ""
        if i == 9:
            vals = [""] * len(genes)
        lines.append("%d," % (100 + i) + ",".join(vals))
    path.write_bytes(gzip.compress(("\n".join(lines) + "\n").encode("ascii"), mtime=0))


def part_d(scratch: Path) -> None:
    print("--- Part D: P1 extension (RUN_PLAN_amend_1.md R35) on synthetic matrices")
    import pandas as pd
    d = scratch / "r35"
    d.mkdir(parents=True)
    f = d / "syn_expr.csv.gz"
    _synthetic_matrix(f)
    res = {env: L.run_l7_env(py, {"syn": f}) for env, py in (("env/venv", Path(sys.executable)),
                                                               ("env/venv_ref", VENV_REF))}
    m = {env: r["matrices"]["syn"] for env, r in res.items()}
    print("     versions: %s" % json.dumps({e: {k: r.get(k) for k in ("pandas", "numpy", "python")} for e, r in res.items()}))
    check("D synthetic frame: round-trip reader hash equal across pandas %s and %s" % (res["env/venv"].get("pandas"),
                                                                                     res["env/venv_ref"].get("pandas")),
          m["env/venv"].get("sha256_matrix") is not None and m["env/venv"]["sha256_matrix"] == m["env/venv_ref"]["sha256_matrix"])
    check("D synthetic frame: default reader hash equal across pandas 3.0.6 and 1.5.3",
          m["env/venv"].get("sha256_default") is not None and m["env/venv"]["sha256_default"] == m["env/venv_ref"]["sha256_default"])
    check("D the environments are the pinned ones (pandas 3.0.6 / 1.5.3)",
          res["env/venv"].get("pandas") == "3.0.6" and res["env/venv_ref"].get("pandas") == "1.5.3")
    rec = L.matrix_reader_check(f)
    check("D 1e-12 check passes on the synthetic .csv.gz read both ways (max |delta| %s)" % rec["max_abs_delta"],
          rec["max_abs_delta"]["default reader"] < 1e-12 and rec["sha256_default"] == m["env/venv"]["sha256_default"])
    used = pd.read_csv(f, index_col=0)  # A1's reader's frame, as handed to the statistics
    check("D 1e-12 check passes against the frame in use (rows used = all non-missing rows)",
          L.matrix_reader_check(f, used=used.loc[[i for i in used.index if i != 109]])["max_abs_delta"]["frame in use"] < 1e-12)
    # a copy with one value moved by 1e-9: the frame in use (read from the original) no longer matches the file
    txt = gzip.decompress(f.read_bytes()).decode("ascii").split("\n")
    cells = txt[2].split(",")
    cells[3] = "%.17g" % (float(cells[3]) + 1e-9)
    txt[2] = ",".join(cells)
    g = d / "syn_moved.csv.gz"
    g.write_bytes(gzip.compress("\n".join(txt).encode("ascii"), mtime=0))
    try:
        L.matrix_reader_check(g, used=used)
        refused = False
    except L.MatrixReaderError as e:
        refused = "1e-12" in str(e)
    check("D 1e-12 check fails on a copy with one value moved by 1e-9 (MatrixReaderError)", refused)
    # gene order / index order differ -> refused
    try:
        L.matrix_reader_check(f, used=used[list(reversed(used.columns))])
        refused = False
    except L.MatrixReaderError:
        refused = True
    check("D a frame in use with another gene order is refused", refused)
    # the first-use hook checks once per process and keeps the record for the provenance block
    before = len(L.first_use_records())
    L.matrix_first_use(f, used=used)
    L.matrix_first_use(f, used=used)
    check("D matrix_first_use: one check per (file, frame) per process, recorded",
          len(L.first_use_records()) == before + 1)


def main() -> int:
    base = Path(os.environ.get("A1_SCRATCH") or tempfile.gettempdir())
    base.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="a1_p1_", dir=str(base)))
    try:
        part_d(scratch)
        part_a(scratch)
        part_b(scratch)
        part_c()
    finally:
        if not os.environ.get("A1_KEEP_SCRATCH"):
            rmtree(scratch)
    n_fail = sum(1 for _, ok in RESULTS if not ok)
    print("test_launch: %d checks, %d passed, %d failed" % (len(RESULTS), len(RESULTS) - n_fail, n_fail))
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
