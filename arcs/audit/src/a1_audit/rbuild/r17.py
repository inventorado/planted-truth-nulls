"""R17 (RUN_PLAN.md v3.1 :806-824, FROZEN): the Docker R environment for Giacomel's rebuilt DEG maps, and the run of
the paper's script `literature_gwas_analysis.R` on the authors' AHBA matrix - with the DRAFT readings of
RUN_PLAN_amend_4.md R58. Nothing here reads G2 material by itself: the material stage (wp4_material) hands it the
repository facts it read under G2 (the script's bytes, the commit date, the declaration files) and the identity-checked
input files. Phase 1 exercises every step on synthetic stand-ins (tests/test_wp4_phase1.py, Part R).

R17's frozen reading (quoted): "The script runs in a Docker R image pinned by digest. Use rocker/r-ver, whose CRAN is
date-locked; r-base only if rocker is unavailable. The R version is the one the repository declares; if it declares
none, the R release current at the commit date. CRAN packages come from the Posit Package Manager snapshot of the commit
date; Bioconductor from the release matching that R. It runs at the repository commit. Inputs and outputs are hashed;
the image digest and the session info are recorded. ... The script is read under G2 only for its package list and
inputs. Fallback: if the script cannot run, those descriptor and published-null cells (C19-C24, the 12 MDD-DEG cells)
read 'not auditable (definition not applicable: the paper's code not runnable here)'."

R58 (draft) pins what that leaves open:
  (a) the commit: e045bc5 (the commit the register names for the lists and the code; claims_register.md:1479-1481);
      its date = the COMMITTER date (GitHub's commit object, recorded);
  (b) "the R version the repository declares": renv.lock's "R" -> "Version", else a top-level `.R-version` holding
      one version x.y.z; a DESCRIPTION's "Depends: R (>= x)" is a floor, not a declaration; none -> (c);
  (c) "the R release current at the commit date": the latest R release dated on or before the commit date, from the
      r-hub R versions API (https://api.r-hub.io/rversions/r-versions; its bytes' sha256 recorded);
  (d) the image: rocker/r-ver:<version>, pulled and pinned by its digest; its Ubuntu codename read from the image
      (/etc/os-release VERSION_CODENAME);
  (e) CRAN: https://p3m.dev/cran/__linux__/<codename>/<commit date (YYYY-MM-DD)>;
  (f) Bioconductor: among the releases whose R version (Bioconductor's config.yaml r_ver_for_bioc_ver) equals the R
      minor, the one with the latest release date on or before the commit date, else the earliest of them;
  (g) packages: the script's library / require / requireNamespace calls and pkg:: references (wp4_read.
      r_script_requirements; base packages excluded), installed with BiocManager against (e) and (f);
  (h) the run: `Rscript <script path>` with the working directory a scratch copy of the repository layout holding the
      script and the identity-checked inputs at the paths the script's read calls name; `--network none`; nothing under
      E:\\data mounted; stdout / stderr to files (never printed; line counts and sha256 only); every file the run
      creates hashed; exit status != 0 or a declared output absent -> STATUS_R17 (R17's fallback, verbatim).
  (f) [v2, asdg-skeptic B5] S of the DEG cells is RE-DERIVED by the run (the TSV: "rebuilt with the paper's code
      literature_gwas_analysis.R ('S re-derived')"): the run's created gene lists with a symbol and a `logFC` column
      (wp4_read.deg_output_key names their Dx and threshold); the TSV's definition and the 3,599 ASD pool are the
      check; the Python recompute (wp4_read.deg_set) is recorded beside it as a cross-check only.
DockerR17 is the production builder (pull + digest, the codename, the Dockerfile, `docker build`, the session info,
the run). Its `base` argument (tests only) replaces rocker/r-ver:<version>@<digest> by a local image and, with
`preinstalled`, drops the package installs (no network); a production run never sets either.
Prints ASCII only (counts, hashes, the fixed vocabulary).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
R17_DIR = HERE / "r17"
STATUS_R17 = "not auditable (definition not applicable: the paper's code not runnable here)"
RVERSIONS_API = "https://api.r-hub.io/rversions/r-versions"
BIOC_CONFIG = "https://bioconductor.org/config.yaml"
ROCKER = "rocker/r-ver"
P3M = "https://p3m.dev/cran/__linux__/{codename}/{date}"
FORBIDDEN_MOUNT_PREFIXES = ("e:/data", "e:\\data")
_VER = re.compile(r"^\d+\.\d+\.\d+$")


# every text an R17Refused carries (the only R17 text a record may hold: wp4_material.run_r17 records a refusal by
# these words, anything else by a fixed fallback; 2026-10-17 incident)
REFUSALS = (
    "no R release on or before the commit date", "no Bioconductor release for the R minor",
    "the CRAN snapshot needs the image's codename", "the base image is not pinned by digest",
    "the image's codename could not be read", "the image's codename has an unexpected form",
    "the working directory lies under E:\\data", "the working directory is not empty",
    "the working directory is outside the repository copy", "the R17 work folder lies under E:\\data",
    "the base image has no repository digest", "the base image could not be pulled",
    "the base image digest could not be read", "the R17 image could not be built", "the R17 image id",
    "Bioconductor's config.yaml has an entry line of an unexpected form",
    "an absolute read path matches the tree by two suffixes of one length",
    "an absolute root is not a plain absolute path", "the absolute roots nest (an ambiguous placement)",
    "an output folder lies outside the repository copy", "a staged input path lies outside the repository copy")
REFUSAL_UNLISTED = "refused at an R17 step (its text is not one of rbuild.r17.REFUSALS: not recorded)"


class R17Refused(Exception):
    def __init__(self, what: str):
        super().__init__(what)
        self.what = what


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---- (b) the declared R version ------------------------------------------------------------------------------------
def declared_r_version(files: dict) -> dict:
    """files: {repository path: bytes} of the declaration files present at the commit (renv.lock, .R-version,
    DESCRIPTION). Returns {"version": x.y.z | None, "basis": ...}."""
    if "renv.lock" in files:
        try:
            v = json.loads(files["renv.lock"].decode("utf-8"))["R"]["Version"]
        except (ValueError, KeyError, TypeError):
            v = None
        if isinstance(v, str) and _VER.match(v.strip()):
            return {"version": v.strip(), "basis": "renv.lock R.Version"}
    if ".R-version" in files:
        s = files[".R-version"].decode("utf-8", "replace").strip()
        if _VER.match(s):
            return {"version": s, "basis": ".R-version"}
    return {"version": None, "basis": "no declaration (a DESCRIPTION floor is not one)"}


# ---- (c) the R release current at the commit date ---------------------------------------------------------------------
def r_release_at(date: str, rversions: bytes) -> dict:
    """The latest R release dated on or before `date` (YYYY-MM-DD) in the r-hub API document (a list of {version,
    date})."""
    doc = json.loads(rversions.decode("utf-8"))
    rows = []
    for e in doc if isinstance(doc, list) else []:
        v, d = e.get("version"), str(e.get("date", ""))[:10]
        if isinstance(v, str) and _VER.match(v) and re.match(r"^\d{4}-\d{2}-\d{2}$", d):
            rows.append((d, tuple(int(x) for x in v.split(".")), v))
    ok = sorted(r for r in rows if r[0] <= date)
    if not ok:
        raise R17Refused("no R release on or before the commit date")
    d, _, v = ok[-1]
    return {"version": v, "release_date": d, "basis": "r-hub rversions API", "source_sha256": sha256_bytes(rversions)}


# ---- (f) Bioconductor -------------------------------------------------------------------------------------------------
def _yaml_strip_comment(ln: str) -> str:
    """A YAML line without its comment: '#' at the line's start or after a blank, outside quotes (2026-10-20)."""
    q = None
    for i, ch in enumerate(ln):
        if q:
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
        elif ch == "#" and (i == 0 or ln[i - 1] in " \t"):
            return ln[:i].rstrip()
    return ln.rstrip()


_YAML_ENTRY = re.compile(r"^[ \t]+([\"']?)([0-9.]+)\1:[ \t]*([\"']?)([^\"']*?)\3$")


def _yaml_map(text: str, key: str) -> dict:
    """The flat 'key:' block of Bioconductor's config.yaml ("x.y": "z" lines), read without a YAML library. Comments
    are removed first (2026-10-17: the release_dates key line carries one; 2026-10-20: so does an entry line of
    r_ver_for_bioc_ver - the old pattern dropped that entry silently - and a column-0 comment line no longer ends a
    block); blank lines are skipped; the block ends at the next column-0 key. An indented line inside the block that
    is not a flat entry is refused, never skipped."""
    out, inside = {}, False
    for raw in text.splitlines():
        ln = _yaml_strip_comment(raw)
        if not ln.strip():
            continue
        if not ln.startswith((" ", "\t")):
            if inside:
                break
            inside = ln == f"{key}:"
            continue
        if inside:
            m = _YAML_ENTRY.match(ln)
            if not m or not m.group(4).strip():
                raise R17Refused("Bioconductor's config.yaml has an entry line of an unexpected form")
            out[m.group(2)] = m.group(4).strip()
    return out


def _bioc_date(s: str) -> str | None:
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def bioc_for(r_version: str, date: str, config: bytes) -> dict:
    text = config.decode("utf-8")
    rmap = _yaml_map(text, "r_ver_for_bioc_ver")
    dates = _yaml_map(text, "release_dates")
    minor = ".".join(r_version.split(".")[:2])
    cands = []
    for b, r in rmap.items():
        if r.strip() == minor:
            d = _bioc_date(dates.get(b, ""))
            if d:
                cands.append((d, tuple(int(x) for x in b.split(".")), b))
    if not cands:
        raise R17Refused("no Bioconductor release for the R minor")
    cands.sort()
    before = [c for c in cands if c[0] <= date]
    pick = before[-1] if before else cands[0]
    return {"version": pick[2], "release_date": pick[0], "rule": "latest release on or before the commit date for the "
            "R minor, else the earliest", "source_sha256": sha256_bytes(config)}


# ---- (a)-(g) the parameters -----------------------------------------------------------------------------------------
def r17_params(*, commit: str, commit_date: str, decl_files: dict, rversions: bytes, bioc_config: bytes,
               script: bytes, codename: str | None = None) -> dict:
    from a1_audit import wp4_read as RD
    date = commit_date[:10]
    dec = declared_r_version(decl_files)
    rel = {"version": dec["version"], "basis": dec["basis"]} if dec["version"] else r_release_at(date, rversions)
    req = RD.r_script_requirements(script.decode("utf-8", "replace"))
    bioc = bioc_for(rel["version"], date, bioc_config)
    return {"commit": commit, "commit_date": commit_date, "r": rel, "declared": dec, "bioc": bioc,
            "image_ref": f"{ROCKER}:{rel['version']}", "codename": codename,
            "cran": P3M.format(codename=codename, date=date) if codename else None,
            "packages": req["packages"], "read_paths": req["read_paths"], "script_sha256": sha256_bytes(script)}


def dockerfile_text(params: dict, base_digest: str | None, *, from_ref: str | None = None,
                    preinstalled: bool = False) -> str:
    """The R17 image: rocker/r-ver:<version>@<digest>, CRAN pinned to the commit-date snapshot, the script's packages
    installed with BiocManager at the chosen Bioconductor release; no data copied. from_ref / preinstalled: tests only
    (a local base image; no install step, the packages' presence still asserted)."""
    if not params.get("cran"):
        raise R17Refused("the CRAN snapshot needs the image's codename")
    if from_ref is None and not (isinstance(base_digest, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", base_digest)):
        raise R17Refused("the base image is not pinned by digest")
    pk = ", ".join(f"'{p}'" for p in params["packages"])
    lines = [f"# A1 R17 image (RUN_PLAN.md:806-824; RUN_PLAN_amend_4 R58, draft); no data is copied",
             f"FROM {from_ref or params['image_ref'] + '@' + base_digest}",
             f"RUN echo \"options(repos = c(CRAN = '{params['cran']}'), timeout = 3600)\" >> "
             f"/usr/local/lib/R/etc/Rprofile.site"]
    if not preinstalled:
        lines.append(f"RUN Rscript -e \"install.packages('BiocManager'); BiocManager::install(version = "
                     f"'{params['bioc']['version']}', ask = FALSE, update = FALSE)\"")
        if params["packages"]:
            lines.append(f"RUN Rscript -e \"BiocManager::install(c({pk}), ask = FALSE, update = FALSE)\"")
    if params["packages"]:
        lines.append(f"RUN Rscript -e \"stopifnot(all(sapply(c({pk}), requireNamespace, quietly = TRUE)))\"")
    lines.append("WORKDIR /work")
    return "\n".join(lines) + "\n"


# ---- docker helpers -----------------------------------------------------------------------------------------------
def _run(cmd, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, **kw)


def image_codename(image: str) -> str:
    r = _run(["docker", "run", "--rm", "--network", "none", image, "sh", "-c",
              ". /etc/os-release; echo $VERSION_CODENAME"], timeout=600)
    if r.returncode != 0:
        raise R17Refused("the image's codename could not be read")
    s = r.stdout.decode("ascii", "replace").strip()
    if not re.fullmatch(r"[a-z]+", s):
        raise R17Refused("the image's codename has an unexpected form")
    return s


def _forbidden(p: Path) -> bool:
    s = str(Path(p).resolve()).replace("/", "\\").casefold()
    return any(s.startswith(x.replace("/", "\\")) for x in FORBIDDEN_MOUNT_PREFIXES)


def run_script(image: str, workdir: Path, script_rel: str, inputs: dict, *, timeout: int = 7200,
               outputs_expected: tuple = (), cwd_rel: str = "", abs_roots: tuple = (), out_dirs: tuple = ()) -> dict:
    """(h): a scratch working directory (`workdir`, never under E:\\data) holding the script and the inputs at their
    repository paths; `docker run --rm --network none -v <workdir>:/work -w /work <image> Rscript <script_rel>`;
    stdout / stderr to files beside the work dir (never printed). Returns the exit status, the counts and the sha256 of
    every file the run created (keyed by the sha256 of its relative path; the path itself kept in memory only for the
    caller's declared-output match)."""
    workdir = Path(workdir)
    if _forbidden(workdir):
        raise R17Refused("the working directory lies under E:\\data")
    if workdir.exists() and any(workdir.iterdir()):
        raise R17Refused("the working directory is not empty")
    workdir.mkdir(parents=True, exist_ok=True)
    for rel, src in inputs.items():                # every staged path held inside the copy (security review)
        dst = contained(workdir, rel, "a staged input path lies outside the repository copy")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    for d in out_dirs:                             # amend_5 R58' (c): the script's output folders, pre-created
        contained(workdir, d, "an output folder lies outside the repository copy").mkdir(parents=True, exist_ok=True)
    for r in abs_roots:
        check_abs_root(r)
    before = {p.relative_to(workdir).as_posix(): sha256_bytes(p.read_bytes()) for p in workdir.rglob("*") if p.is_file()}
    logs = workdir.parent / (workdir.name + "_logs")
    logs.mkdir(parents=True, exist_ok=True)
    if cwd_rel and (cwd_rel.startswith("/") or ".." in cwd_rel.split("/")):
        raise R17Refused("the working directory is outside the repository copy")
    wd = "/work" + (f"/{cwd_rel}" if cwd_rel else "")
    run_rel = script_rel[len(cwd_rel) + 1:] if cwd_rel and script_rel.startswith(cwd_rel + "/") else script_rel
    if cwd_rel:
        (workdir / cwd_rel).mkdir(parents=True, exist_ok=True)
    mounts = ["-v", f"{workdir.resolve()}:/work"]
    for r in abs_roots:                            # amend_5 R58' (a): the same repository copy at each absolute root
        mounts += ["-v", f"{workdir.resolve()}:{r}"]
    cmd = ["docker", "run", "--rm", "--network", "none", *mounts, "-w", wd, image, "Rscript", run_rel]
    with open(logs / "stdout.txt", "wb") as fo, open(logs / "stderr.txt", "wb") as fe:
        r = subprocess.run(cmd, stdout=fo, stderr=fe, timeout=timeout)
    created = {}
    for p in workdir.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(workdir).as_posix()
        h = sha256_bytes(p.read_bytes())
        if rel not in before or before[rel] != h:
            created[rel] = h
    found = {o: (o in created) for o in outputs_expected}
    out_lines = (logs / "stdout.txt").read_bytes().count(b"\n")
    err_lines = (logs / "stderr.txt").read_bytes().count(b"\n")
    ok = r.returncode == 0 and all(found.values())
    return {"exit": int(r.returncode), "ok": ok, "status": None if ok else STATUS_R17,
            "created": {sha256_bytes(k.encode("utf-8")): v for k, v in sorted(created.items())},
            "_created_paths": sorted(created), "declared_outputs_found": sum(found.values()),
            "declared_outputs": len(found), "stdout_lines": out_lines, "stderr_lines": err_lines,
            "stdout_sha256": sha256_bytes((logs / "stdout.txt").read_bytes()),
            "stderr_sha256": sha256_bytes((logs / "stderr.txt").read_bytes()),
            "inputs_sha256": {sha256_bytes(k.encode("utf-8")): before.get(k) for k in sorted(inputs)},
            "image": image, "network": "none", "cwd": "script directory" if cwd_rel else "repository root"}


# ---- the working directory and the inputs (h) -------------------------------------------------------------------------
def placement(read_paths, script_path: str, known: set, *, abs_strings=(), name_ok=None) -> dict:
    """The script's read paths resolved against the repository root and against the script's directory; the base with
    more paths among `known` (the repository files at the commit plus the declared external inputs) is the working
    directory (ties: the root). Returns {"cwd_rel", "resolved": {read path: repository path}, "n_unresolved"}."""
    import posixpath
    sd = posixpath.dirname(script_path)

    def res(base):
        out = {}
        for rp in read_paths:
            q = posixpath.normpath(posixpath.join(base, rp)) if base else posixpath.normpath(rp)
            if not q.startswith("../") and q != "..":
                out[rp] = q
        return out
    rel_paths = [rp for rp in read_paths if not rp.startswith("/")]
    absolute = absolute_placement([rp for rp in read_paths if rp.startswith("/")], known, abs_strings, name_ok)
    read_paths = rel_paths
    root, local = res(""), res(sd)
    ok = (lambda q: q in known or posixpath.basename(q) in known or bool(name_ok and name_ok(posixpath.basename(q))))
    n_root = sum(1 for q in root.values() if ok(q))
    n_local = sum(1 for q in local.values() if ok(q))
    use_local = bool(sd) and n_local > n_root
    chosen = dict(local if use_local else root)
    chosen.update(absolute["resolved"])
    return {"cwd_rel": sd if use_local else "", "resolved": chosen, "abs_roots": absolute["roots"],
            "n_unresolved": len(set(read_paths)) - (n_local if use_local else n_root) + absolute["n_unresolved"]}


_ABS_ROOT = re.compile(r"^/[^:\0\\]*[^/:\0\\]$")


def absolute_placement(abs_reads, known: set, abs_strings=(), name_ok=None) -> dict:
    """amend_5 R58' (a): an absolute read path (the author's machine) is placed by its unique longest suffix among the
    commit's tree paths (`known`): the path minus that suffix is an absolute root, mounted onto the repository copy.
    Two tree paths matching one read path by suffixes of one length -> refused (ambiguous). A root's last component
    then also anchors the script's other absolute strings (`abs_strings`: assigned literals; a second root such as
    the script's other Dropbox root): an absolute string holding '/<that component>/' gives that prefix as another
    root, so its remainder is a repository-relative path (placed if `known` holds it or name_ok accepts its file
    name; else unresolved and counted). Returns {"roots": sorted absolute roots, "resolved": {read path: relative
    path}, "n_unresolved"}."""
    import posixpath
    roots, resolved, rest = set(), {}, []
    tree = [q for q in known if "/" in q]           # repository paths below the root (a bare declared name is not one)
    for rp in sorted(set(abs_reads)):
        cands = [q for q in tree if rp.endswith("/" + q)]
        if not cands:
            rest.append(rp)
            continue
        best = max(len(q) for q in cands)
        top = [q for q in cands if len(q) == best]
        if len(top) != 1:
            raise R17Refused("an absolute read path matches the tree by two suffixes of one length")
        q = safe_rel(top[0], "a staged input path lies outside the repository copy")
        roots.add(check_abs_root(rp[: -len(q) - 1]))
        resolved[rp] = q
    if any(a != b and b.startswith(a + "/") for a in roots for b in roots):
        raise R17Refused("the absolute roots nest (an ambiguous placement)")
    anchors = {posixpath.basename(r) for r in roots}
    for s in sorted(set(rest) | {a for a in abs_strings if a.startswith("/")}):
        for a in sorted(anchors):
            i = s.find("/" + a + "/")
            if i >= 0:
                roots.add(check_abs_root(s[: i + len(a) + 1]))
                break
    n_un = 0
    for rp in rest:
        r = next((x for x in sorted(roots, key=len, reverse=True) if rp.startswith(x + "/")), None)
        q = safe_rel(rp[len(r) + 1:], "a staged input path lies outside the repository copy") if r else None
        if q and (q in known or bool(name_ok and name_ok(posixpath.basename(q)))):
            resolved[rp] = q
        else:
            n_un += 1
            if q:
                resolved[rp] = q
    return {"roots": sorted(roots), "resolved": resolved, "n_unresolved": n_un}


def out_dirs_rel(out_dirs, roots) -> list:
    """amend_5 R58' (c): the script's absolute output folders as repository-relative folders (under one of the
    roots); others are not created. A folder name the script supplies that could escape the copy (a backslash, a ':',
    a NUL, a leading '/', a '..' or empty component) refuses (security review 2026-10-21)."""
    out = set()
    for d in out_dirs:
        r = next((x for x in sorted(roots, key=len, reverse=True) if d == x or d.startswith(x + "/")), None)
        if r is not None and d != r:
            out.add(safe_rel(d[len(r) + 1:], "an output folder lies outside the repository copy"))
    return sorted(out)


def safe_rel(rel, what: str) -> str:
    """A repository-relative path from third-party input (the paper's script): no '\\', ':' or NUL, no leading '/',
    no empty, '.' or '..' component; else R17Refused(what) (what is one of REFUSALS)."""
    if not isinstance(rel, str) or not rel or any(c in rel for c in ("\\", ":", "\x00")) or rel.startswith("/") or \
            any(p in ("", ".", "..") for p in rel.split("/")):
        raise R17Refused(what)
    return rel


def contained(workdir: Path, rel, what: str) -> Path:
    """safe_rel, then (workdir / rel).resolve() must lie inside workdir.resolve() (a link or junction that leads
    outside refuses); returns the resolved path."""
    safe_rel(rel, what)
    base = Path(workdir).resolve()
    p = (base / rel).resolve()
    if not p.is_relative_to(base) or p == base:
        raise R17Refused(what)
    return p


def check_abs_root(r) -> str:
    """An absolute root (a container path the copy is mounted at): a plain absolute posix path - no '\\', ':' or NUL,
    no empty / '.' / '..' component, not '/', '/work' or below /work."""
    if not isinstance(r, str) or not _ABS_ROOT.match(r) or r in ("/", "/work") or r.startswith("/work/") or \
            any(p in ("", ".", "..") for p in r[1:].split("/")):
        raise R17Refused("an absolute root is not a plain absolute path")
    return r


# ---- the production builder -------------------------------------------------------------------------------------------
class DockerR17:
    """R17 / R58 (draft): pull rocker/r-ver:<version> and pin it by digest, read its codename, build the image from
    dockerfile_text, record the image id and the session info, run the script (run_script). `work`: a folder under the
    G2 artifacts (never under E:\\data). `base` / `preinstalled`: tests only (module docstring)."""

    def __init__(self, work: Path, *, base: str | None = None, preinstalled: bool = False, run=None,
                 timeout: int = 7200):
        self.work = Path(work)
        if _forbidden(self.work):
            raise R17Refused("the R17 work folder lies under E:\\data")
        self.base, self.preinstalled = base, preinstalled
        self._run = run or _run
        self.timeout = timeout
        self.build_record: dict = {}

    def _ok(self, cmd, what, timeout=None):
        r = self._run(cmd, timeout=timeout or self.timeout)
        if r.returncode != 0:
            raise R17Refused(what)
        return r.stdout.decode("utf-8", "replace").strip()

    def pull(self, ref: str) -> str:
        self._ok(["docker", "pull", ref], "the base image could not be pulled")
        dig = self._ok(["docker", "image", "inspect", "--format", "{{index .RepoDigests 0}}", ref],
                       "the base image digest could not be read", 120)
        m = re.search(r"@(sha256:[0-9a-f]{64})$", dig)
        if not m:
            raise R17Refused("the base image has no repository digest")
        return m.group(1)

    def params(self, facts: dict) -> dict:
        p = r17_params(commit=facts["commit"], commit_date=facts["commit_date"], decl_files=facts["decl_files"],
                       rversions=facts["rversions"], bioc_config=facts["bioc_config"], script=facts["script"])
        if self.base is None:
            digest = self.pull(p["image_ref"])
            probe = f"{p['image_ref']}@{digest}"
        else:
            digest, probe = None, self.base
        cn = image_codename(probe)
        p.update(codename=cn, cran=P3M.format(codename=cn, date=facts["commit_date"][:10]), base_digest=digest,
                 base_override=self.base is not None, preinstalled=self.preinstalled)
        return p

    def build(self, params: dict) -> str:
        text = dockerfile_text(params, params.get("base_digest"), from_ref=self.base, preinstalled=self.preinstalled)
        h = sha256_bytes(text.encode("utf-8"))
        ctx = self.work / f"build_{h[:12]}"
        ctx.mkdir(parents=True, exist_ok=True)
        (ctx / "Dockerfile").write_bytes(text.encode("utf-8"))
        if (ctx / "Dockerfile").read_bytes() != text.encode("utf-8"):
            raise OSError("read-back")
        tag = f"a1-audit-r17:{h[:12]}"
        self._ok(["docker", "build", "-t", tag, str(ctx)], "the R17 image could not be built")
        iid = self._ok(["docker", "image", "inspect", "--format", "{{.Id}}", tag], "the R17 image id", 120)
        r = self._run(["docker", "run", "--rm", "--network", "none", tag, "Rscript", "-e", "sessionInfo()"],
                      timeout=600)
        self.build_record = {"dockerfile_sha256": h, "image_id": iid, "tag": tag,
                             "base_digest": params.get("base_digest"), "base_override": self.base is not None,
                             "session_info_sha256": sha256_bytes(r.stdout), "session_info_lines":
                                 r.stdout.count(b"\n"), "session_info_exit": int(r.returncode)}
        return tag

    def run(self, image: str, params: dict, *, inputs: dict, script_rel: str, cwd_rel: str = "", abs_roots=(),
            out_dirs=()) -> dict:
        k = 1
        while (self.work / f"run_{k}").exists():
            k += 1
        rec = run_script(image, self.work / f"run_{k}", script_rel, inputs, timeout=self.timeout, cwd_rel=cwd_rel,
                         abs_roots=tuple(abs_roots), out_dirs=tuple(out_dirs))
        rec["workdir_index"] = k
        rec["_workdir"] = str(self.work / f"run_{k}")
        rec["build"] = dict(self.build_record)
        return rec
