"""Build and run helpers for the A1 audit R image (RUN_PLAN.md v3.1 FROZEN: R13 "against WGCNA::bicor ... if the Docker
R environment of R17 builds", R17 "a Docker R image pinned by digest ... the image digest and the session info are
recorded", R30 "read from the package source in the R image of R17 and recorded with its version"; plant P17).

    cd arcs/audit/src
    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.rbuild.docker_r build     # build, lock, record
    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.rbuild.docker_r status    # is the recorded image here?

Build: `docker build --progress=plain` of `Dockerfile` (base rocker/r-ver:4.4.3 pinned by digest; CRAN from the
date-locked Posit snapshot that rocker/r-ver:4.4.3 itself pins; Bioconductor 3.20). The full build log is kept in
`logs/build_<UTC>.log`. First pass with an empty `packages.lock.tsv` ("record mode"): the installed package table is
read from the image and written as the lock (read back); second pass: the Dockerfile's verify step asserts every
installed package equals the lock, version by version (the build fails otherwise). `image_lock.json` records the base
digest, the built image id (the config sha256, the local content digest; the image is not pushed, so it has no
registry digest), build arguments, input hashes, R / Bioconductor versions, the named packages' versions and the
build logs' paths and sha256; it is read back after writing.

PROVISIONAL FOR R17: the repository's declared R version, its commit date and `literature_gwas_analysis.R`'s package
list are read under G2 only (R17), so at WP2 they are unknown. This image serves R13 and R30 now and is exercised on
synthetic data; under G2 (WP4) it is rebuilt with R17's values (build arguments BASE / CRAN_SNAPSHOT / BIOC_VERSION and
the script's packages) and the P17 Docker checks are rerun in it.

Run: `docker run --rm --network none` (no network at run time) by image ID, with a scratch directory mounted at /work
and `r/` mounted read-only at /opt/a1_r. Synthetic data only; nothing under E:\\data is ever mounted.
Prints ASCII only.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
R_DIR = HERE / "r"
LOG_DIR = HERE / "logs"
DOCKERFILE = HERE / "Dockerfile"
INSTALL_R = HERE / "install_packages.R"
LOCK_TSV = HERE / "packages.lock.tsv"
IMAGE_LOCK = HERE / "image_lock.json"

BASE_REF = "rocker/r-ver:4.4.3"
BASE_DIGEST = "sha256:3dae5d2eeddf74f10e0a81fb6b7ae350295e288000304f438b844b2c1e00fe2c"
CRAN_SNAPSHOT = "https://p3m.dev/cran/__linux__/noble/2025-04-10"
BIOC_VERSION = "3.20"
BIOC_BINARIES = "https://bioconductor.org/packages/3.20/container-binaries/bioconductor_docker"
IMAGE_TAG = "a1-audit-r:wp2-r4.4.3"
LOCK_HEADER = "package\tversion\tpriority\trepository\n"
NAMED = ("WGCNA", "GeneOverlap", "BiocManager", "impute", "preprocessCore", "GO.db", "AnnotationDbi")
STATUS = ("provisional for R17 (WP2): R 4.4.3 / CRAN snapshot 2025-04-10 / Bioconductor 3.20 chosen before G2; the "
          "repository's R version, commit date and the script's package list are read under G2 only (RUN_PLAN R17), "
          "and the image is rebuilt with them in WP4. Serves R13 (WGCNA::bicor) and R30 (GeneOverlap source) now.")
FORBIDDEN_MOUNT_PREFIXES = ("e:/data", "e:\\data")


class NotBuilt(RuntimeError):
    """The R image is not available; `reason` says why. Docker-dependent checks report "not built: <reason>"."""


def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _run(cmd, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, **kw)


def docker_available() -> tuple[bool, str]:
    try:
        r = _run(["docker", "version", "--format", "{{.Server.Version}}"], timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, f"docker client not runnable ({type(e).__name__})"
    if r.returncode != 0:
        return False, "docker server not reachable (docker version exited non-zero)"
    return True, r.stdout.decode("ascii", "replace").strip()


def inspect_image(ref: str) -> dict | None:
    r = _run(["docker", "image", "inspect", ref], timeout=120)
    if r.returncode != 0:
        return None
    return json.loads(r.stdout.decode("utf-8"))[0]


def _write_text(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8", newline="\n")
    if p.read_text(encoding="utf-8") != text:  # a writer reads back what it wrote
        raise RuntimeError(f"read-back mismatch: {p.name}")


def _docker_build(stamp: str) -> dict:
    LOG_DIR.mkdir(exist_ok=True)
    log = LOG_DIR / f"build_{stamp}.log"
    cmd = ["docker", "build", "--progress=plain", "-t", IMAGE_TAG,
           "--build-arg", f"BASE={BASE_REF}@{BASE_DIGEST}", "--build-arg", f"CRAN_SNAPSHOT={CRAN_SNAPSHOT}",
           "--build-arg", f"BIOC_VERSION={BIOC_VERSION}", "--build-arg", f"BIOC_BINARIES={BIOC_BINARIES}", str(HERE)]
    t0 = time.time()
    with open(log, "wb") as fh:
        fh.write((f"# A1 rbuild: {' '.join(cmd)}\n# started {_utc()}\n").encode("utf-8"))
        fh.flush()
        r = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, timeout=7200)
        fh.write(f"\n# exit {r.returncode} after {time.time() - t0:.0f} s; ended {_utc()}\n".encode("utf-8"))
    return dict(path=log.relative_to(HERE).as_posix(), exit=int(r.returncode), seconds=round(time.time() - t0, 1),
                sha256=sha256_file(log), lock_sha256_at_build=sha256_file(LOCK_TSV))


def _in_image(image_id: str, *args: str, timeout: int = 600) -> str:
    r = _run(["docker", "run", "--rm", "--network", "none", image_id, *args], timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"docker run in the image exited {r.returncode}")
    return r.stdout.decode("utf-8")


SESSION_R = ("suppressPackageStartupMessages({library(WGCNA); library(GeneOverlap)}); "
             "cat('R_VERSION\\t', as.character(getRversion()), '\\n', sep=''); "
             "cat('BIOC_VERSION\\t', as.character(BiocManager::version()), '\\n', sep=''); "
             "cat('CRAN\\t', getOption('repos')[['CRAN']], '\\n', sep=''); "
             "for (p in c('WGCNA','GeneOverlap','BiocManager','impute','preprocessCore','GO.db','AnnotationDbi')) "
             "cat('PKG\\t', p, '\\t', as.character(packageVersion(p)), '\\n', sep=''); "
             "cat('SESSIONINFO\\n'); print(sessionInfo())")


def _log_inventory() -> list:
    """Every build log kept in logs/ with its sha256, exit line, whether it ran the install / the lock verify (or took
    them from the build cache) and the image manifest digest it exported: the trace from a cached re-record back to
    the build that installed the packages."""
    out = []
    for p in sorted(LOG_DIR.glob("build_*.log")):
        t = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"exporting manifest (sha256:[0-9a-f]{64})", t)
        e = re.search(r"^# exit (-?\d+)", t, flags=re.M)
        out.append(dict(path=p.relative_to(HERE).as_posix(), sha256=sha256_file(p),
                        exit=int(e.group(1)) if e else None,
                        install_ran="A1 rbuild install: done" in t,
                        verify_ran=("A1 rbuild verify: pass;" in t) or ("A1 rbuild verify: lock empty" in t),
                        verify_mode=("pass" if "A1 rbuild verify: pass;" in t else
                                     "record (empty lock)" if "A1 rbuild verify: lock empty" in t else None),
                        exported_manifest=m.group(1) if m else None))
    return out


def build() -> dict:
    ok, why = docker_available()
    if not ok:
        raise NotBuilt(why)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = inspect_image(f"{BASE_REF.split(':')[0]}@{BASE_DIGEST}")
    logs = []
    first = _docker_build(stamp + "_pass1")
    logs.append(first)
    if first["exit"] != 0:
        raise NotBuilt(f"docker build exited {first['exit']} (log {first['path']})")
    img = inspect_image(IMAGE_TAG)
    table = _in_image(img["Id"], "cat", "/opt/a1_rbuild/installed_versions.tsv")
    if not table.startswith(LOCK_HEADER):
        raise RuntimeError("installed_versions.tsv: unexpected header")
    lock_now = LOCK_TSV.read_text(encoding="utf-8")
    if lock_now == LOCK_HEADER:
        _write_text(LOCK_TSV, table)      # record mode: the lock is written from the image, then read back
        second = _docker_build(stamp + "_pass2_verify")
        logs.append(second)
        if second["exit"] != 0:
            raise NotBuilt(f"docker build (verify pass) exited {second['exit']} (log {second['path']})")
        img = inspect_image(IMAGE_TAG)
    elif lock_now != table:
        raise RuntimeError("the image's installed table differs from packages.lock.tsv although the verify step passed")
    # the lock verify, run again in the final image (a cached build step prints nothing, so the build log alone is not
    # evidence); its output is kept as a log, and the image's copy of the lock must be the repository's
    if _in_image(img["Id"], "cat", "/opt/a1_rbuild/packages.lock.tsv") != LOCK_TSV.read_text(encoding="utf-8"):
        raise RuntimeError("the image's packages.lock.tsv differs from the repository's")
    vout = _in_image(img["Id"], "Rscript", "/opt/a1_rbuild/install_packages.R", "verify", "/opt/a1_rbuild/packages.lock.tsv")
    if "A1 rbuild verify: pass;" not in vout:
        raise RuntimeError("the lock verify did not pass in the final image")
    vpath = LOG_DIR / f"verify_{stamp}.log"
    _write_text(vpath, vout)
    blog = (HERE / logs[-1]["path"]).read_text(encoding="utf-8", errors="replace")
    exported = {k: (re.search(rf"exporting {k} (sha256:[0-9a-f]{{64}})", blog) or [None, None])[1]
                for k in ("manifest list", "manifest", "config")}
    sess = _in_image(img["Id"], "Rscript", "-e", SESSION_R)
    sess_path = LOG_DIR / f"session_info_{stamp}.txt"
    _write_text(sess_path, sess)
    kv, pkgs = {}, {}
    for line in sess.splitlines():
        parts = line.split("\t")
        if parts[0] == "PKG" and len(parts) == 3:
            pkgs[parts[1]] = parts[2]
        elif parts[0] in ("R_VERSION", "BIOC_VERSION", "CRAN") and len(parts) == 2:
            kv[parts[0]] = parts[1]
    if kv.get("CRAN") != CRAN_SNAPSHOT or kv.get("BIOC_VERSION") != BIOC_VERSION or kv.get("R_VERSION") != "4.4.3":
        raise RuntimeError(f"image R / CRAN / Bioconductor differ from the pins: {kv}")
    lock_rows = [ln.split("\t") for ln in LOCK_TSV.read_text(encoding="utf-8").splitlines()[1:] if ln]
    for p in NAMED:
        if dict((r[0], r[1]) for r in lock_rows).get(p) != pkgs.get(p):
            raise RuntimeError(f"named package {p}: session version differs from the lock")
    rec = dict(
        what="A1 audit R image (RUN_PLAN.md v3.1 R13, R17, R30; plant P17); synthetic data only",
        status=STATUS,
        built_utc=_utc(),
        base=dict(ref=BASE_REF, digest=BASE_DIGEST, repo_digests=(base or {}).get("RepoDigests"),
                  created=(base or {}).get("Created")),
        image=dict(tag=IMAGE_TAG, id=img["Id"], created=img.get("Created"), size_bytes=img.get("Size"),
                   exported_digests=exported,
                   digest_note="id = `docker image inspect` Id = with Docker Desktop's containerd image store the "
                               "image index (manifest list) digest; it changes on every build, even a fully cached "
                               "one, because the index carries a BuildKit attestation (provenance) manifest. The "
                               "content-stable identity is the image manifest digest (and its config digest), read "
                               "from the final build log. The image is local only (never pushed)."),
        build_args=dict(BASE=f"{BASE_REF}@{BASE_DIGEST}", CRAN_SNAPSHOT=CRAN_SNAPSHOT, BIOC_VERSION=BIOC_VERSION,
                        BIOC_BINARIES=BIOC_BINARIES),
        inputs_sha256={"Dockerfile": sha256_file(DOCKERFILE), "install_packages.R": sha256_file(INSTALL_R),
                       "packages.lock.tsv": sha256_file(LOCK_TSV)},
        r_version=kv["R_VERSION"], bioc_version=kv["BIOC_VERSION"], cran=kv["CRAN"],
        packages=dict(n_installed=len(lock_rows), named=pkgs),
        build_logs=logs,
        session_info=dict(path=sess_path.relative_to(HERE).as_posix(), sha256=sha256_file(sess_path)),
        lock_verify=dict(path=vpath.relative_to(HERE).as_posix(), sha256=sha256_file(vpath)),
        log_inventory=_log_inventory(),
        docker=why,
    )
    text = json.dumps(rec, indent=1, sort_keys=False) + "\n"
    _write_text(IMAGE_LOCK, text)
    if json.loads(IMAGE_LOCK.read_text(encoding="utf-8")) != rec:
        raise RuntimeError("image_lock.json read-back mismatch")
    return rec


def image_status() -> dict:
    """The recorded image, if it is usable here: docker reachable, image_lock.json present, the image with the recorded
    id present locally, and the lock / Dockerfile / install script unchanged since the record. Raises NotBuilt(reason)
    otherwise (the reason is what a Docker-dependent check prints as "not built: <reason>")."""
    ok, why = docker_available()
    if not ok:
        raise NotBuilt(why)
    if not IMAGE_LOCK.exists():
        raise NotBuilt("no image_lock.json (the image was never built by docker_r.py build)")
    rec = json.loads(IMAGE_LOCK.read_text(encoding="utf-8"))
    for name, path in (("Dockerfile", DOCKERFILE), ("install_packages.R", INSTALL_R),
                       ("packages.lock.tsv", LOCK_TSV)):
        if sha256_file(path) != rec["inputs_sha256"][name]:
            raise NotBuilt(f"{name} changed since the recorded build (rebuild with docker_r.py build)")
    img = inspect_image(rec["image"]["id"])
    if img is None:
        raise NotBuilt(f"the recorded image {rec['image']['id'][:19]} is not present locally")
    return rec


def _check_mount(path: Path) -> str:
    s = str(Path(path).resolve()).replace("\\", "/")
    if s.lower().startswith(FORBIDDEN_MOUNT_PREFIXES):
        raise PermissionError("refused: a data path is never mounted into the R image")
    return s


def run_r(script: str, args, workdir: Path, *, timeout: int = 1800) -> subprocess.CompletedProcess:
    """Rscript /opt/a1_r/<script> <args> in the recorded image (by id), no network, `workdir` at /work."""
    rec = image_status()
    sp = R_DIR / script
    if not sp.is_file():
        raise FileNotFoundError(script)
    cmd = ["docker", "run", "--rm", "--network", "none",
           "-v", f"{_check_mount(workdir)}:/work", "-v", f"{_check_mount(R_DIR)}:/opt/a1_r:ro",
           rec["image"]["id"], "Rscript", f"/opt/a1_r/{script}", *[str(a) for a in args]]
    return _run(cmd, timeout=timeout)


def main(argv) -> int:
    what = argv[1] if len(argv) > 1 else "status"
    try:
        if what == "build":
            rec = build()
        elif what == "status":
            rec = image_status()
        else:
            print(f"usage: docker_r.py build|status (got {what!r})")
            return 2
    except NotBuilt as e:
        print(f"not built: {e}")
        return 1
    print(json.dumps(dict(image=rec["image"]["id"], base=rec["base"]["digest"], r=rec["r_version"],
                          bioc=rec["bioc_version"], cran=rec["cran"], packages=rec["packages"]["named"],
                          logs=[x["path"] for x in rec["build_logs"]]), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
