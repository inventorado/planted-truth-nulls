"""Verify a release tree made by build_release.py, without touching the tree itself.

    python -X utf8 verify_release.py --tree D:\\tmp\\p1_release_test [--scratch D:\\tmp\\p1_release_verify]

(a) MANIFEST.sha256 re-checked; every released Python module of the packages (a1_audit, asdg) is imported in a
    subprocess whose PYTHONPATH is the tree's source dirs only and whose cwd is outside the repo; loose scripts are
    checked statically (every top-level import must resolve on that path). Failures mean the allow-list is incomplete.
(b) The tree is copied to --scratch, `git init`-ed and committed there (derive_numbers.py refuses files that are not
    committed), then arcs/audit/paper1/figures/make_figures.py and tables/derive_numbers.py are run in place. Outputs
    are compared with the shipped ones: PNGs and numbers by sha256 / numeric equality (derive_numbers.json: every value
    equal, `last_commit` fields excluded because the scratch commit differs; derived_numbers.md: bytes equal after CRLF->LF and masking the last_commit column); PDFs by sha256, else by sha256 of the
    file with its /CreationDate /ModDate /ID stripped.
(c) file count and size of the tree.
"""
import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

SRC_DIRS = ["arcs/audit/src", "src", "arcs/audit/src_register", "arcs/audit/probes/regime/src"]
PACKAGES = [("arcs/audit/src", "a1_audit"), ("src", "asdg")]
# Modules that cannot import outside the private repository, with the substring their error must contain. They are
# reported, not counted as failures: they need git history of the private repo, its artifacts/ (not released), or the
# unreleased replication arc (arcs/replication, module h_common), or are child scripts that read sys.argv.
KNOWN_NONPORTABLE = {
    "a1_audit.tests.test_amend1": "rev-parse",
    "a1_audit.tests.test_p0": "h_common",
    "a1_audit.tests.test_wp4_phase1": "artifacts",
    "a1_audit.tests.wp3_child": "list index out of range",
}

IMPORT_CHILD = r'''
import importlib, json, os, pkgutil, sys, time, traceback
pkg = sys.argv[1]
mods = [pkg]
p = importlib.import_module(pkg)
for m in pkgutil.walk_packages(p.__path__, pkg + "."):
    mods.append(m.name)
res = {}
for m in mods:
    t = time.time()
    try:
        importlib.import_module(m)
        res[m] = None
    except BaseException as e:
        res[m] = f"{type(e).__name__}: {e}"
print(json.dumps(res))
'''


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def strip_pdf_meta(b):
    b = re.sub(rb"/(CreationDate|ModDate)\s*\(.*?\)", b"", b)
    b = re.sub(rb"/ID\s*\[.*?\]", b"", b, flags=re.S)
    b = re.sub(rb"<xmp:(CreateDate|ModifyDate|MetadataDate)>.*?</xmp:\1>", b"", b)
    return b


def check_manifest(tree):
    n = bad = 0
    for ln in open(os.path.join(tree, "MANIFEST.sha256"), encoding="utf-8").read().splitlines():
        h, rel = ln.split("  ", 1)
        n += 1
        if sha(os.path.join(tree, *rel.split("/"))) != h:
            bad += 1
            print("  MANIFEST MISMATCH", rel)
    on_disk = sum(len(fs) for _, _, fs in os.walk(tree)) - 1       # all files except MANIFEST.sha256 itself
    print(f"(0) MANIFEST.sha256: {n} entries, {bad} mismatches, {on_disk} files on disk (expect {n})")
    return bad == 0 and on_disk == n


def check_frozen(tree):
    """FROZEN.txt lines are '<timestamp>  <sha256>  <file>' (file relative to its own folder)."""
    n = bad = 0
    for rel in ("arcs/audit/FROZEN.txt", "arcs/audit/probes/regime/FROZEN.txt"):
        base = os.path.dirname(os.path.join(tree, *rel.split("/")))
        for ln in open(os.path.join(tree, *rel.split("/")), encoding="utf-8").read().splitlines():
            parts = ln.split()
            if len(parts) == 3 and re.fullmatch(r"[0-9a-f]{64}", parts[1]):
                n += 1
                fp = os.path.join(base, parts[2])
                if not os.path.exists(fp) or sha(fp) != parts[1]:
                    bad += 1
                    print("  FROZEN MISMATCH", rel, parts[2])
    print(f"(0) FROZEN.txt: {n} frozen files hash-checked against the shipped bytes, {bad} mismatches")
    return bad == 0


def internal_names(tree):
    """Module names that exist inside the release tree (a missing one of these is an incomplete allow-list)."""
    names = set()
    for root, ds, fs in os.walk(tree):
        names.update(f[:-3] for f in fs if f.endswith(".py"))
        names.update(ds)
    return names


def import_check(tree, tmp, repo_internal):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(os.path.join(tree, *d.split("/")) for d in SRC_DIRS)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    failures = {}
    total = 0
    for base, pkg in PACKAGES:
        r = subprocess.run([sys.executable, "-X", "utf8", "-c", IMPORT_CHILD, pkg], cwd=tmp, env=env,
                           capture_output=True, text=True, encoding="utf-8", timeout=1800)
        try:
            res = json.loads(r.stdout.strip().splitlines()[-1])
        except Exception:
            failures[pkg] = f"child crashed: rc={r.returncode} {r.stderr[-800:]}"
            continue
        total += len(res)
        for m, e in res.items():
            if e:
                failures[m] = e
        print(f"(a) package {pkg}: {len(res)} modules imported, {sum(1 for e in res.values() if e)} failed")
    # loose scripts: static resolution of top-level imports
    script_dirs = [("arcs/audit/src", False), ("arcs/audit/src_register", True), ("arcs/audit/probes/regime/src", True),
                   ("arcs/audit/paper1/figures", True), ("arcs/audit/paper1/tables", True), ("arcs/audit", False)]
    chk = r'''
import ast, importlib.util, json, os, sys
bad = {}
n = 0
for d in json.loads(sys.argv[1]):
    full = os.path.join(sys.argv[2], *d[0].split("/"))
    names = [f for f in os.listdir(full) if f.endswith(".py")] if d[1] or True else []
    for f in names:
        if d[0] == "arcs/audit" and not f.endswith(".py"):
            continue
        n += 1
        sys.path.insert(0, full)
        try:
            tree = ast.parse(open(os.path.join(full, f), encoding="utf-8").read())
        except SyntaxError as e:
            bad[d[0] + "/" + f] = ["SyntaxError " + str(e)]
            sys.path.pop(0); continue
        for node in ast.walk(tree):
            tops = []
            if isinstance(node, ast.Import):
                tops = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                tops = [node.module.split(".")[0]]
            for t in tops:
                try:
                    ok = importlib.util.find_spec(t) is not None
                except Exception:
                    ok = False
                if not ok:
                    bad.setdefault(d[0] + "/" + f, []).append(t)
        sys.path.pop(0)
print(json.dumps(dict(n=n, bad=bad)))
'''
    r = subprocess.run([sys.executable, "-X", "utf8", "-c", chk, json.dumps(script_dirs), tree], cwd=tmp, env=env,
                       capture_output=True, text=True, encoding="utf-8", timeout=900)
    try:
        res = json.loads(r.stdout.strip().splitlines()[-1])
        print(f"(a) loose scripts: {res['n']} files, {len(res['bad'])} with an unresolvable import")
        for f, ms in res["bad"].items():
            internal = sorted(set(m for m in ms if m in repo_internal))
            external = sorted(set(m for m in ms if m not in repo_internal))
            if external:
                print(f"    third-party, not installed in this venv (not counted): {f}: {external}")
            if internal:
                failures["script:" + f] = "unresolved internal: " + ", ".join(internal)
    except Exception:
        failures["scripts"] = f"checker crashed: {r.stderr[-800:]}"
    return total, failures


def run_in(scratch, script, env_extra):
    env = dict(os.environ)
    env.update(env_extra)
    r = subprocess.run([sys.executable, "-X", "utf8", script], cwd=scratch, env=env, capture_output=True,
                       text=True, encoding="utf-8", timeout=1800)
    return r


def numbers_equal(a, b, path=""):
    """Deep equality, excluding any key named last_commit; floats compared exactly (same code, same inputs)."""
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b):
            return [f"{path}: keys differ"]
        out = []
        for k in a:
            if k == "last_commit":
                continue
            out += numbers_equal(a[k], b[k], f"{path}/{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: length {len(a)} vs {len(b)}"]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in numbers_equal(x, y, f"{path}[{i}]")]
    return [] if a == b else [f"{path}: {a!r} vs {b!r}"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True)
    ap.add_argument("--scratch", default=r"D:\tmp\p1_release_verify")
    ap.add_argument("--skip-imports", action="store_true")
    a = ap.parse_args()
    tree, scratch = os.path.abspath(a.tree), os.path.abspath(a.scratch)
    ok = check_manifest(tree)
    ok &= check_frozen(tree)
    tmp = scratch + "_cwd"
    os.makedirs(tmp, exist_ok=True)
    if not a.skip_imports:
        names = internal_names(tree)
        for ln in subprocess.run(["git", "ls-tree", "-r", "--name-only", json.load(open(os.path.join(tree, "RELEASE.json"), encoding="utf-8"))["commit"]],
                                 cwd=os.path.dirname(os.path.abspath(__file__)), capture_output=True, text=True).stdout.splitlines():
            if ln.endswith(".py"):
                names.add(os.path.basename(ln)[:-3])        # exists in the private repo, whether released or not
        total, failures = import_check(tree, tmp, names)
        known = {m: e for m, e in failures.items() if m in KNOWN_NONPORTABLE and KNOWN_NONPORTABLE[m] in e}
        failures = {m: e for m, e in failures.items() if m not in known}
        print(f"(a) {len(known)} known non-portable modules (not counted), {len(failures)} failures")
        for m, e in sorted(known.items()):
            print(f"    known: {m}: {e[:160]}")
        for m, e in sorted(failures.items()):
            print(f"    FAIL {m}: {e[:300]}")
        ok &= not failures
    # (b)
    if os.path.exists(scratch):
        shutil.rmtree(scratch, onexc=lambda f, p, e: (os.chmod(p, 0o700), f(p)))   # .git objects are read-only
    shutil.copytree(tree, scratch)
    g = lambda *args: subprocess.run(["git", "-c", "user.name=verify", "-c", "user.email=verify@invalid", "-c",
                                      "core.autocrlf=false", *args], cwd=scratch, capture_output=True, text=True)
    g("init", "-q")
    g("add", "-A")
    c = g("commit", "-qm", "scratch snapshot of the release tree")
    assert c.returncode == 0, c.stderr
    assert g("status", "--porcelain").stdout.strip() == "", "scratch repo not clean"
    fig_dir = os.path.join("arcs", "audit", "paper1", "figures")
    tab_dir = os.path.join("arcs", "audit", "paper1", "tables")
    r1 = run_in(scratch, os.path.join(fig_dir, "make_figures.py"), {"SOURCE_DATE_EPOCH": "1700000000"})
    print(f"(b) make_figures.py rc={r1.returncode}" + ("" if r1.returncode == 0 else "\n" + r1.stderr[-1500:]))
    r2 = run_in(scratch, os.path.join(tab_dir, "derive_numbers.py"), {})
    print(f"(b) derive_numbers.py rc={r2.returncode}" + ("" if r2.returncode == 0 else "\n" + (r2.stderr or r2.stdout)[-1500:]))
    ok &= r1.returncode == 0 and r2.returncode == 0
    report = []
    for f in sorted(os.listdir(os.path.join(tree, fig_dir))):
        if not f.startswith("fig") or not f.endswith((".png", ".pdf")):
            continue
        p0, p1 = os.path.join(tree, fig_dir, f), os.path.join(scratch, fig_dir, f)
        if sha(p0) == sha(p1):
            how = "sha256 identical"
        elif f.endswith(".pdf") and hashlib.sha256(strip_pdf_meta(open(p0, "rb").read())).hexdigest() == \
                hashlib.sha256(strip_pdf_meta(open(p1, "rb").read())).hexdigest():
            how = "identical after stripping PDF dates/ID"
        else:
            how = "DIFFERENT"
            ok = False
        report.append((f, how))
    for f, how in report:
        print(f"    {f}: {how}")
    j0 = json.load(open(os.path.join(tree, tab_dir, "derived_numbers.json"), encoding="utf-8"))
    j1 = json.load(open(os.path.join(scratch, tab_dir, "derived_numbers.json"), encoding="utf-8"))
    diffs = numbers_equal(j0, j1)
    print(f"    derived_numbers.json: {'numerically identical (last_commit excluded)' if not diffs else 'DIFFERENT ' + str(diffs[:5])}"
          f"; sha256 {'identical' if sha(os.path.join(tree, tab_dir, 'derived_numbers.json')) == sha(os.path.join(scratch, tab_dir, 'derived_numbers.json')) else 'differs (last_commit values)'}")
    def norm(pth):   # Windows rerun writes CRLF (repo stores LF); the inputs table ends in each file's scratch last_commit
        b = open(pth, "rb").read().replace(bytes([13, 10]), bytes([10]))
        return re.sub(rb"(?m)^(\| arcs/\S+ \| [0-9a-f]{64} \| )[0-9a-f]{7,}( \|)$", rb"\1<last_commit>\2", b)
    md_same = norm(os.path.join(tree, tab_dir, "derived_numbers.md")) == norm(os.path.join(scratch, tab_dir, "derived_numbers.md"))
    print(f"    derived_numbers.md: {'byte-identical after CRLF->LF' if md_same else 'DIFFERENT'}")
    ok &= not diffs and md_same
    # (c)
    n = size = 0
    for root, _, fs in os.walk(tree):
        for f in fs:
            n += 1
            size += os.path.getsize(os.path.join(root, f))
    print(f"(c) tree: {n} files, {size} bytes ({size / 1e6:.1f} MB)")
    print("VERIFY", "PASSED" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
