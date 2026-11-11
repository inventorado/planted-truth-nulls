"""Build the curated, public-safe release tree for paper P1.

    python -X utf8 build_release.py --commit 0606369 --paper-commit <sha> --out D:\\tmp\\p1_release_test \\
        [--doi 10.5281/zenodo.N] [--repo-url URL] [--final] [--pdf PATH] [--no-pdf]
    python -X utf8 build_release.py --selftest

Everything is read from git at --commit (blobs through `git cat-file --batch`; the working tree is never read).
The paper text is built from --paper-commit with build_pdf.py --final in a scratch checkout of that commit.
Order: allow-list expansion -> hard deny (refuse) -> content scans (refuse on secrets / e-mail / person-id headers;
report absolute local paths) -> write -> read back every file -> MANIFEST.sha256.
RELEASE_POLICY.md is the human-readable statement of the rules below. The deny list is code, not data, on purpose.
"""
import argparse
import collections
import csv
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DEFAULT_COMMIT = "0606369"
AUTHOR = "Lovecký, Radoslav"
AUTHOR_GIVEN, AUTHOR_FAMILY = "Radoslav", "Lovecký"
AFFIL = "Arperon"
OPERATOR_EMAIL_SHA256 = "2ab41b173f233bf003b2f385df82403c12b1a1c175533e086ebf06d3bc254450"   # sha256 of the lower-cased address; the address itself is never shipped
EMAIL_RE = re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def has_email(data, sha=OPERATOR_EMAIL_SHA256):
    return any(hashlib.sha256(m.group(0).lower()).hexdigest() == sha for m in EMAIL_RE.finditer(data))
PLACEHOLDERS = ("{{DOI}}", "{{REPO_URL}}")
# the build instrument itself is shipped (read from the directory of this script, checked against --paper-commit)
TOOLING = ["RELEASE_POLICY.md", "release_files.txt", "build_release.py", "verify_release.py"]
TOOLING_CHECKED_ONLY = ["LICENSE-DOCS.txt"]
TOOLING_DIR = "arcs/audit/paper1/release"

# ------------------------------------------------------------------ hard deny list (path level)
DENY_REGEXES = [  # (name, compiled regex over the full posix path, case-insensitive)
    ("register_work/", r"(^|/)register_work/"),
    ("literature/", r"^literature/"),
    ("run_manifests/material/", r"(^|/)run_manifests/material/"),
    ("G1 path component", r"(^|/)[^/]*(?<![A-Za-z0-9])G1(?![A-Za-z0-9])[^/]*(/|$)"),
    ("wp5*", r"(^|/)[^/]*wp5[^/]*(/|$)"),
    ("WP5_*", r"(^|/)WP5_[^/]*"),
    ("RUN_PLAN_amend_6..10", r"(^|/)RUN_PLAN_amend_(6|7|8|9|10)(\.|_|$)"),
    ("probes/spreg_raise/", r"(^|/)probes/spreg_raise/"),
    ("ARC.md", r"(^|/)ARC\.md$"),
    ("NEXT_SESSION.md", r"(^|/)NEXT_SESSION\.md$"),
    ("EVENTS.jsonl", r"(^|/)EVENTS\.jsonl$"),
    ("ENTITIES.jsonl", r"(^|/)ENTITIES\.jsonl$"),
    ("CLAUDE.md", r"(^|/)CLAUDE\.md$"),
    (".claude/", r"(^|/)\.claude/"),
    ("artifacts/", r"(^|/)artifacts/"),
    ("env/venv*", r"(^|/)env/venv[^/]*(/|$)"),
    ("*.vcf*", r"\.vcf(\.|$)"),
    ("*.bam", r"\.bam$"),
    ("*.cram", r"\.cram$"),
    ("*.fastq*", r"\.fastq"),
    ("*.h5ad", r"\.h5ad$"),
    ("*.nii*", r"\.nii(\.|$)"),
    (".env", r"(^|/)\.env($|\.)"),
    ("abide1_pcp_MANIFEST.tsv", r"(^|/)results/data_manifests/abide1_pcp_MANIFEST\.tsv$"),
    ("LEAP per-participant supplement", r"(^|/)[^/]*leap[^/]*(supp|participant|individual)[^/]*$"),
]
DENY = [(n, re.compile(r, re.I)) for n, r in DENY_REGEXES]
# content-level deny: delimited tables with a person-id column
ID_COLUMN = re.compile(r"subject|participant|sub_id|file_id", re.I)

SECRET_PATTERNS = [
    ("credential-name", re.compile(r"\bapi[_-]?key\b", re.I)),
    ("token=", re.compile(r"\btoken\s*=\s*['\"]?[A-Za-z0-9_\-\.]{12,}", re.I)),
    ("ghp_", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("sk-", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}")),
    ("password", re.compile(r"\bpassword\s*[:=]\s*\S", re.I)),
]
PATH_PATTERNS = [
    ("D:\\", re.compile(r"\bD:\\", re.I)),
    ("E:\\data", re.compile(r"\bE:\\data", re.I)),
    ("C:\\Users\\", re.compile(r"C:\\Users\\", re.I)),
]
JSON_ID_KEY = re.compile(r'"(participant_id|subject_id|sub_id|SUB_ID|FILE_ID|subject|participant)"\s*:', re.I)


def deny_hits(path):
    return [n for n, rx in DENY if rx.search(path)]


def scan_content(path, data, email_sha=OPERATOR_EMAIL_SHA256):
    """Return dict(refuse=[reasons], local_paths={label: n}, json_id_keys=n)."""
    out = dict(refuse=[], local_paths={}, json_id_keys=0)
    low = path.lower()
    text = None
    if not data[:4096].count(b"\x00"):
        text = data.decode("utf-8", errors="replace")
    if has_email(data, email_sha):
        out["refuse"].append("operator e-mail")
    if text is not None:
        if low.endswith((".tsv", ".csv")):
            for ln in text.splitlines():
                if not ln.strip() or ln.lstrip().startswith("#"):
                    continue
                cols = next(csv.reader([ln], delimiter="\t" if low.endswith(".tsv") else ","), [])
                bad = [c for c in cols if ID_COLUMN.search(c)]
                if bad:
                    out["refuse"].append(f"person-id column in header: {bad[:3]}")
                break
        for name, rx in SECRET_PATTERNS:
            if rx.search(text):
                out["refuse"].append(f"secret pattern {name}")
        for name, rx in PATH_PATTERNS:
            n = len(rx.findall(text))
            if n:
                out["local_paths"][name] = n
        if low.endswith((".json", ".jsonl")):
            out["json_id_keys"] = len(JSON_ID_KEY.findall(text))
        if re.search(r"(^|/)\.env$", path):
            out["refuse"].append(".env content")
    return out


# ------------------------------------------------------------------ git
def git(*args, cwd=REPO, check=True):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True)
    if check and r.returncode:
        sys.exit(f"git {' '.join(args)} failed: {r.stderr.decode('utf-8', 'replace')}")
    return r.stdout


def resolve(rev):
    return git("rev-parse", "--verify", rev + "^{commit}").decode().strip()


def ls_tree(commit):
    out = git("ls-tree", "-r", "-z", "--name-only", commit)
    return [p.decode("utf-8") for p in out.split(b"\0") if p]


class BlobReader:
    """git cat-file --batch: reads blobs of one commit without touching the working tree."""

    def __init__(self, commit):
        self.commit = commit
        self.p = subprocess.Popen(["git", "cat-file", "--batch"], cwd=REPO, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE)

    def read(self, path):
        self.p.stdin.write(f"{self.commit}:{path}\n".encode("utf-8"))
        self.p.stdin.flush()
        hdr = self.p.stdout.readline().decode().split()
        if len(hdr) != 3 or hdr[1] != "blob":
            sys.exit(f"cannot read {self.commit}:{path}: {hdr}")
        n = int(hdr[2])
        data = self.p.stdout.read(n)
        self.p.stdout.read(1)
        assert len(data) == n
        return data

    def close(self):
        self.p.stdin.close()
        self.p.wait()


# ------------------------------------------------------------------ allow-list
def glob_to_regex(pat):
    i, out = 0, ""
    while i < len(pat):
        c = pat[i]
        if pat.startswith("**/", i):
            out += "(?:.*/)?"; i += 3; continue
        if pat.startswith("**", i):
            out += ".*"; i += 2; continue
        if c == "*":
            out += "[^/]*"
        elif c == "?":
            out += "[^/]"
        elif c == "[":
            j = pat.index("]", i)
            out += pat[i:j + 1]; i = j + 1; continue
        else:
            out += re.escape(c)
        i += 1
    return re.compile("^" + out + "$")


def expand(allow_text, tree):
    inc, exc, stale = [], [], []
    for raw in allow_text.splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("#"):
            continue
        (exc if ln.startswith("!") else inc).append(ln.lstrip("!"))
    chosen = set()
    for pat in inc:
        rx = glob_to_regex(pat)
        hit = [p for p in tree if rx.match(p)]
        if not hit:
            stale.append(pat)
        chosen.update(hit)
    removed = collections.OrderedDict()
    for pat in exc:
        rx = glob_to_regex(pat)
        hit = sorted(p for p in chosen if rx.match(p))
        removed[pat] = len(hit)
        chosen.difference_update(hit)
    return sorted(chosen), removed, stale


# ------------------------------------------------------------------ gate self-test (a gate must be shown to fail)
def selftest():
    planted_paths = ["arcs/audit/run_manifests/G1/x.json", "arcs/audit/register_sets/gated_G1_RG-03.json",
                     "data/a.vcf.gz", "arcs/audit/WP5_PLAN.md", "arcs/audit/RUN_PLAN_amend_8.md",
                     "arcs/audit/run_manifests/material/G2/x.md", "literature/notes/a.md", "NEXT_SESSION.md",
                     "env/venv/lib/x.py", "x/y.nii.gz", "arcs/audit/results/data_manifests/abide1_pcp_MANIFEST.tsv",
                     "arcs/audit/register_work/a.md", "artifacts/audit/x", "arcs/audit/run_manifests/reprice_wp5.json"]
    for p in planted_paths:
        assert deny_hits(p), f"deny gate failed to catch planted path {p}"
    for ok in ["arcs/audit/register_sets/post_freeze/G2/gated_G2_GIA-C01.json", "arcs/audit/src/a1_audit/wp4_launch.py",
               "arcs/audit/RUN_PLAN_amend_5.md", "arcs/audit/prereg_amend_7.md", "arcs/audit/results/e3_gates.json",
               "src/asdg/spatial.py", "arcs/audit/register_maps/post_freeze/G2/hansen_cammoun_info.4.json"]:
        assert not deny_hits(ok), f"deny gate over-blocks {ok}: {deny_hits(ok)}"
    for body, why in [(b"SUB_ID\tAGE\n1\t5\n", "id header"), (b"x,FILE_ID\n", "id header"), (b"a\tParticipant\n", "id header")]:
        ext = ".csv" if b"," in body else ".tsv"
        assert scan_content("t" + ext, body)["refuse"], f"scan failed to catch {why}"
    assert scan_content("t.tsv", b"# comment, participant\nset_id\tn\n")["refuse"] == [], "comment line must be skipped"
    assert scan_content("t.py", b"ghp_" + b"a" * 30)["refuse"]
    assert scan_content("t.py", b"API_" + b"KEY = 'x'")["refuse"]
    assert scan_content("t.py", b"tok" + b"en = 'abcdefghijklmnop1234'")["refuse"]
    dummy = ("Some.One" + chr(64) + "Example.org").encode()
    assert scan_content("t.md", b"mail " + dummy, hashlib.sha256(dummy.lower()).hexdigest())["refuse"]
    assert not scan_content("t.md", b"mail " + dummy)["refuse"]
    assert scan_content("t.md", b"see D:\\RESEARCH and D:\\tmp")["local_paths"]["D:\\"] == 2
    assert not scan_content("t.md", b"nothing here")["refuse"]
    assert glob_to_regex("a/**").match("a/b/c") and not glob_to_regex("a/*").match("a/b/c")
    assert glob_to_regex("x_[1-7].md").match("x_3.md") and not glob_to_regex("x_[1-7].md").match("x_8.md")
    print("selftest: deny, scan and glob gates catch every planted failure and pass the clean controls")


# ------------------------------------------------------------------ line endings
HEX64 = re.compile(rb"(?<![0-9a-fA-F])[0-9a-f]{64}(?![0-9a-fA-F])")


def restore_crlf(blobs):
    """The repo stores text as LF (.gitattributes `text=auto eol=lf`), but some result files were hashed in their CRLF
    working-tree form (make_figures.py asserts those sha256 values; derived_numbers.json records them). A text blob
    whose LF sha256 appears nowhere in the tree but whose CRLF form's sha256 does is written in the CRLF form, so every
    recorded hash names the bytes shipped. Returns (new_blobs, restored_paths, conflicts)."""
    NUL, LF, CR = bytes([0]), bytes([10]), bytes([13])
    anchors, paper_anchors = set(), set()           # paper_anchors: hashes named by the paper's own scripts/tables
    for p, d in blobs.items():
        if d[:4096].count(NUL) == 0:
            hs = {h.decode() for h in HEX64.findall(d)}
            anchors |= hs
            if p.startswith("arcs/audit/paper1/"):
                paper_anchors |= hs
    restored, conflicts = [], []
    for p, d in blobs.items():
        if LF not in d or CR in d or d[:4096].count(NUL):
            continue
        crlf = d.replace(LF, CR + LF)
        if sha(crlf) in paper_anchors or (sha(d) not in anchors and sha(crlf) in anchors):
            if sha(d) in anchors:
                conflicts.append(p)                 # both forms are named somewhere; the paper's scripts win
            blobs[p] = crlf
            restored.append(p)
    return blobs, sorted(restored), sorted(conflicts)


# ------------------------------------------------------------------ generated files
MIT = """MIT License

Copyright (c) 2026 Radoslav Lovecký

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Scope: the code in this archive (*.py, *.R, *.ps1, Dockerfile). Text, protocol, results and
figures are under CC BY 4.0, see LICENSE-DOCS. Third-party material is not covered by either
licence; see README.md.
"""

DOCS_HEAD = """LICENSE-DOCS: Creative Commons Attribution 4.0 International (CC BY 4.0)

Applies to the text, the preregistration and amendments, the claims register, the result files,
the figures and the manuscript in this archive: Copyright (c) 2026 Radoslav Lovecký.
Code is under the MIT licence (LICENSE). Third-party material is not covered; see README.md.
The legal text below is the official CC BY 4.0 legal code (https://creativecommons.org/licenses/by/4.0/legalcode).

"""

README = """# {title}

Archive of the code, frozen protocol, result files and manuscript for paper P1: {title}.
Author: Radoslav Lovecký ({affil}). Archived at https://doi.org/{doi}; repository {repo}.

This is a curated release of one study (the "A1 audit" arc) of a larger private research repository. It was built
from git commit `{commit}` (code and results) and `{paper_commit}` (manuscript) by
`arcs/audit/paper1/release/build_release.py`, with the policy in `arcs/audit/paper1/release/RELEASE_POLICY.md`.
Repository-relative paths are kept, so the paths written in the manuscript and in the result files resolve here.

## What is in the archive
| path | content |
|---|---|
| `paper/` | `p1_final.pdf`, `p1_final.md` (the submitted text), `refs.bib` (cited references only) |
| `arcs/audit/prereg.md`, `prereg_amend_1..7.md`, `FROZEN.txt` | the frozen preregistration, its seven amendments (amendments 2, 3, 5, 6, 7 are declared post hoc in their own text) and the freeze timestamps and hashes |
| `arcs/audit/RUN_PLAN*.md`, `claims_register.md/.tsv` | the run plan with amendments 1-5 and the register of audited claims |
| `arcs/audit/src/`, `src_register/`, `probes/regime/`, `src/asdg/` | the instrument, the audit pipeline (`a1_audit`), the planted-truth generators, the regime probe |
| `arcs/audit/results/` | result files (`e3_*`, `e4_*`), `a1_run/` per-row records of the ungated and G2 passes, source notes of data used |
| `arcs/audit/run_manifests/` | launch records and plant cases |
| `arcs/audit/register_maps/`, `register_sets/` | records of the audited maps and gene sets (see below) |
| `arcs/audit/paper1/figures/`, `tables/` | figure and table scripts and their outputs |
| `arcs/audit/paper1/release/` | how this archive was made: policy, allow-list, `build_release.py`, `verify_release.py` |
| `MANIFEST.sha256`, `RELEASE.json` | sha256 of every file; commits, date, counts and scan results |

## Reproducing the figures and tables
Python 3.13; package versions in `env/requirements.lock`. From the archive root, with the lock installed:

    python -X utf8 arcs/audit/paper1/figures/make_figures.py
    git init && git config core.autocrlf false && git add -A && git -c user.name=x -c user.email=x@x commit -qm snapshot
    python -X utf8 arcs/audit/paper1/tables/derive_numbers.py

`make_figures.py` asserts the sha256 of every result file it reads and rewrites `figures/fig*.pdf/png`.
`derive_numbers.py` reads the same result files and records, for each, the last git commit that touched it, and it
refuses files that are not committed: that is why the archive must be a git repository first (the `git init` line).
The recorded `last_commit` values then differ from the original ones; the derived numbers do not.
`python -X utf8 arcs/audit/paper1/release/verify_release.py --tree .` does exactly this in a scratch copy, imports every
module and compares the outputs with the shipped ones. The audit itself (`arcs/audit/src/a1_audit/`, launched through `launch.py` / `run.py`) needs the
third-party maps, which are not redistributed; the per-row outputs it produced are in `results/a1_run/`.

## Line endings
Do not let git or an editor normalise line endings: hashes recorded in the archive name the exact bytes. The repository
stores text with LF, but {n_crlf} result files were hashed (by `make_figures.py`, `derived_numbers.json`) in their CRLF form
and are shipped in that form (`RELEASE.json`, `eol_restored_to_crlf`). `.gitattributes` sets `* -text`; use
`git config core.autocrlf false`. `MANIFEST.sha256` (`sha256sum -c MANIFEST.sha256`) checks every file.

## What is not included, and why
* **Third-party published brain maps and the supplement tables the gene lists came from are not redistributed** (licences
  differ or are unclear). `register_maps/` holds identity records only: URL, commit or ETag, byte size, sha256 and listing date,
  plus a few small transcriptions of published figure panels (for example `buch_fig5h_grid.json`). `register_sets/` holds,
  per audited gene set, the derived HGNC symbol list (`members_hgnc`), the mapping rule and counts, not the source tables.
  The register records of Giacomel et al.'s shipped result tables (`gated_G2_GIA-C01`..`C18`, `GIA-MDD-C1/C5/C10/D10/U1`)
  carry the authors' per-gene values and are left out, because their repository has no licence; their sets computed here by
  running the authors' script (`GIA-C19`..`C24`, `GIA-MDD-DEG-*`) are included.
  To re-run the audit, download each map from the URL in its record and check the sha256.
* **Allen Human Brain Atlas** expression is public and is not redistributed; it is rebuilt with abagen.
* **No individual-level data** of any kind. The archive contains no subject-level table. One public supplement (Pretzsch
  et al., Supplement 2) also contains per-participant tables of a cohort with controlled access (EU-AIMS LEAP): only its
  group-level eTable 13 loadings were extracted, the per-participant sheets were inspected by header only and never used,
  and the file was then deleted; none of it is here. Data manifests from other lanes of the wider programme (for example
  `abide1_pcp_SOURCE.md`) describe downloads that no analysis in this paper uses.
* `src/a1_audit/rbuild/logs/` keeps the R image's build and session logs, without the deparsed GPL source of GeneOverlap.
* Run records carry the authors' machine name (`"node"`) as provenance.
* **Gate G1 / the third release batch (196 population units) was not run.** Its material, run plan amendments 6-10 and
  work package 5 are not in the archive, and no number in the paper depends on them.
* The programme's literature notes, working notes on single papers, session handoff and event logs, and the draft with
  its internal provenance comments are internal and not included.
* Local absolute paths (`D:\\...`, `E:\\data\\...`) remain in launch records and logs as provenance strings; they point to the
  authors' machine and do not resolve here.

## Licence
Code: MIT (`LICENSE`). Text, protocol, results, figures: CC BY 4.0 (`LICENSE-DOCS`). Third-party material is under its
owners' terms. Cite as in `CITATION.cff`.
"""


def citation_cff(title, doi, repo, release_date):
    return f"""cff-version: 1.2.0
message: "If you use this archive, please cite it as below."
title: "{title}"
type: software
authors:
  - family-names: "{AUTHOR_FAMILY}"
    given-names: "{AUTHOR_GIVEN}"
    affiliation: "{AFFIL}"
doi: "{doi}"
repository-code: "{repo}"
license: MIT
date-released: "{release_date}"
abstract: "Code, frozen preregistration and amendments, claims register, result files, figure and table scripts, and manuscript for paper P1."
keywords:
  - imaging transcriptomics
  - gene-set enrichment
  - null models
  - planted truths
  - spatial autocorrelation
"""


def zenodo_json(title, repo, release_date):
    return json.dumps({
        "title": title,
        "upload_type": "publication",
        "publication_type": "preprint",
        "description": ("Archive for the preprint: code, frozen preregistration and amendments, claims register, "
                        "result files, figure and table scripts and the manuscript. Third-party maps are not "
                        "redistributed; no individual-level data are included."),
        "creators": [{"name": AUTHOR, "affiliation": AFFIL}],
        "license": "cc-by-4.0",
        "access_right": "open",
        "publication_date": release_date,
        "keywords": ["imaging transcriptomics", "gene-set enrichment", "null models", "planted truths"],
        "related_identifiers": [{"identifier": repo, "relation": "isSupplementTo", "scheme": "url",
                                 "resource_type": "software"}],
    }, indent=2, ensure_ascii=False) + "\n"


# ------------------------------------------------------------------ paper text from --paper-commit
def build_paper(paper_commit, doi, repo, pdf_arg, no_pdf, build_pdf_override=None):
    """Return dict name -> bytes for paper/ and a record. Builds in a scratch checkout of --paper-commit."""
    rec = {}
    tmp = tempfile.mkdtemp(prefix="p1_paper_")
    try:
        tarb = git("archive", "--format=tar", paper_commit, "arcs/audit/paper1", "literature/citations.bib")
        with tarfile.open(fileobj=io.BytesIO(tarb)) as tf:
            tf.extractall(tmp, filter='data')
        p1 = os.path.join(tmp, "arcs", "audit", "paper1")
        draft = open(os.path.join(p1, "draft.md"), "rb").read()
        rec["draft_sha256"] = hashlib.sha256(draft).hexdigest()
        rec["title"] = re.search(r'^title:\s*"(.*)"\s*$', draft.decode("utf-8"), flags=re.M).group(1)
        files = {}
        if build_pdf_override:       # until the --final build_pdf.py is committed at --paper-commit
            shutil.copyfile(build_pdf_override, os.path.join(p1, "build_pdf.py"))
            rec["build_pdf_override_sha256"] = sha(open(build_pdf_override, "rb").read())
        py = sys.executable
        if doi and repo and not no_pdf:
            r = subprocess.run([py, "-X", "utf8", "build_pdf.py", "--final", "--doi", doi, "--repo-url", repo],
                               cwd=p1, capture_output=True, text=True, encoding="utf-8")
            if r.returncode:
                sys.exit(f"build_pdf.py --final failed:\n{r.stdout}\n{r.stderr}")
            rec["build_pdf_stdout"] = r.stdout.strip().splitlines()
            for name, src in (("p1_final.md", "p1_final.md"), ("p1_final.pdf", "p1_final.pdf"), ("refs.bib", "refs.bib")):
                files["paper/" + name] = open(os.path.join(p1, "build", src), "rb").read()
        else:
            if pdf_arg:
                files["paper/p1_final.pdf"] = open(pdf_arg, "rb").read()
            r = subprocess.run([py, "-X", "utf8", "build_pdf.py", "--tex-only"], cwd=p1, capture_output=True,
                               text=True, encoding="utf-8")
            if r.returncode:
                sys.exit(f"build_pdf.py --tex-only failed:\n{r.stdout}\n{r.stderr}")
            files["paper/refs.bib"] = open(os.path.join(p1, "build", "refs.bib"), "rb").read()
            rec["note"] = "no --doi/--repo-url: p1_final.md and p1_final.pdf not built (preview only)"
        return files, rec
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--commit", default=DEFAULT_COMMIT)
    ap.add_argument("--paper-commit")
    ap.add_argument("--out")
    ap.add_argument("--doi", help="10.5281/zenodo.N")
    ap.add_argument("--repo-url")
    ap.add_argument("--final", action="store_true", help="refuse if any {{DOI}}/{{REPO_URL}} placeholder remains")
    ap.add_argument("--pdf", help="use an already built PDF when --doi/--repo-url are not given")
    ap.add_argument("--no-pdf", action="store_true", help="do not build the paper text/PDF")
    ap.add_argument("--build-pdf", help="use this build_pdf.py instead of the one at --paper-commit (recorded in RELEASE.json)")
    ap.add_argument("--allow-list", default=os.path.join(HERE, "release_files.txt"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest()
    if a.selftest:
        return
    if not (a.paper_commit and a.out):
        ap.error("--paper-commit and --out are required")
    if bool(a.doi) != bool(a.repo_url) and not a.no_pdf:
        ap.error("give --doi and --repo-url together")
    if a.doi and not re.fullmatch(r"10\.5281/zenodo\.\d+", a.doi):
        ap.error("--doi must look like 10.5281/zenodo.N")
    if a.final and not (a.doi and a.repo_url):
        sys.exit("--final needs --doi and --repo-url")
    commit, paper_commit = resolve(a.commit), resolve(a.paper_commit)
    out = os.path.abspath(a.out)
    if os.path.exists(out) and os.listdir(out):
        sys.exit(f"--out {out} exists and is not empty")
    commit_date = git("log", "-1", "--format=%cs", commit).decode().strip()
    release_date = datetime.date.today().isoformat()

    # 1. expand the allow-list against the tree of --commit
    tree = ls_tree(commit)
    paths, removed, stale = expand(open(a.allow_list, encoding="utf-8").read(), tree)
    if stale:
        sys.exit("allow-list patterns that match nothing at this commit (list is stale): " + ", ".join(stale))
    # 2. hard deny on the expansion
    offenders = [(p, deny_hits(p)) for p in paths if deny_hits(p)]
    if offenders:
        print("REFUSED: allow-listed files hit the hard deny list:", file=sys.stderr)
        for p, h in offenders[:200]:
            print(f"  {p}   [{', '.join(h)}]", file=sys.stderr)
        sys.exit(2)
    # 3. read blobs, content scans
    br = BlobReader(commit)
    blobs, scan_refuse, local_paths, json_ids = {}, [], {}, {}
    for p in paths:
        data = br.read(p)
        blobs[p] = data
        s = scan_content(p, data)
        if s["refuse"]:
            scan_refuse.append((p, s["refuse"]))
        if s["local_paths"]:
            local_paths[p] = s["local_paths"]
        if s["json_id_keys"]:
            json_ids[p] = s["json_id_keys"]
    br.close()
    # the instrument: files of this directory, compared with the blobs at --paper-commit
    tooling, tooling_state = {}, {}
    for f in TOOLING + TOOLING_CHECKED_ONLY:
        data = open(os.path.join(HERE, f), "rb").read()
        r = subprocess.run(["git", "cat-file", "blob", f"{paper_commit}:{TOOLING_DIR}/{f}"], cwd=REPO, capture_output=True)
        tooling_state[f] = "equal to --paper-commit" if r.returncode == 0 and r.stdout == data else "NOT COMMITTED / differs from --paper-commit"
        if f in TOOLING:
            tooling[f"{TOOLING_DIR}/{f}"] = data
    stale_tooling = [f for f, v in tooling_state.items() if not v.startswith("equal")]
    if a.final and stale_tooling:
        sys.exit(f"--final: release tooling differs from --paper-commit (commit it first): {stale_tooling}")
    for p, data in tooling.items():
        blobs[p] = data
        s = scan_content(p, data)
        if s["refuse"]:
            scan_refuse.append((p, s["refuse"]))
        if s["local_paths"]:
            local_paths[p] = s["local_paths"]
        if deny_hits(p):
            sys.exit(f"tooling file hits deny list: {p}")
    blobs, eol_restored, eol_conflicts = restore_crlf(blobs)
    # figures/tables drift between --commit and --paper-commit
    drift = git("diff", "--name-only", commit, paper_commit, "--", "arcs/audit/paper1/figures",
                "arcs/audit/paper1/tables").decode().split()
    # 4. paper text
    paper_files, paper_rec = build_paper(paper_commit, a.doi, a.repo_url, a.pdf, a.no_pdf, a.build_pdf)
    for p, data in paper_files.items():
        s = scan_content(p, data)
        if s["refuse"]:
            scan_refuse.append((p, s["refuse"]))
        if s["local_paths"]:
            local_paths[p] = s["local_paths"]
    if scan_refuse:
        print("REFUSED: content scan:", file=sys.stderr)
        for p, why in scan_refuse[:200]:
            print(f"  {p}   {why}", file=sys.stderr)
        sys.exit(3)

    # 5. generated files
    title = paper_rec["title"]
    doi_s = a.doi or "{{DOI}}"
    repo_s = a.repo_url or "{{REPO_URL}}"
    gen = {
        "README.md": README.format(title=title, affil=AFFIL, doi=doi_s, repo=repo_s, commit=commit[:7],
                                   paper_commit=paper_commit[:7], n_crlf=len(eol_restored)),
        "LICENSE": MIT,
        ".gitattributes": "# bytes are hashed inside this archive (MANIFEST.sha256, FROZEN.txt, make_figures.py): never normalise\n* -text\n",
        "LICENSE-DOCS": DOCS_HEAD + open(os.path.join(HERE, "LICENSE-DOCS.txt"), encoding="utf-8").read(),
        "CITATION.cff": citation_cff(title, doi_s, repo_s, release_date),
        ".zenodo.json": zenodo_json(title, repo_s, release_date),
    }
    gen["README.md"] = "\n".join(l.rstrip() for l in gen["README.md"].split("\n"))
    for k, v in gen.items():
        gen[k] = v.encode("utf-8")
    left = [k for k, v in gen.items() for ph in PLACEHOLDERS if ph.encode() in v]
    left += [k for k, v in paper_files.items() for ph in PLACEHOLDERS if ph.encode() in v]
    if a.final and left:
        sys.exit(f"--final: placeholders remain in {sorted(set(left))}")

    # 6. write, then read back
    allfiles = dict(blobs)
    allfiles.update(paper_files)
    allfiles.update(gen)
    for rel, data in allfiles.items():
        dst = os.path.join(out, *rel.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as f:
            f.write(data)
    manifest_lines = []
    for rel in sorted(allfiles):
        back = open(os.path.join(out, *rel.split("/")), "rb").read()
        assert sha(back) == sha(allfiles[rel]), f"read-back mismatch {rel}"
        manifest_lines.append(f"{sha(back)}  {rel}")
    top = collections.Counter(r.split("/")[0] if "/" in r else "(root)" for r in allfiles)
    sub = collections.Counter("/".join(r.split("/")[:3]) for r in allfiles if r.startswith("arcs/audit/"))
    total = sum(len(v) for v in allfiles.values())
    release = dict(
        built_utc=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        commit=commit, commit_date=commit_date, paper_commit=paper_commit,
        doi=a.doi, repo_url=a.repo_url, final=a.final,
        file_count=len(allfiles) + 2, bytes=total, files_by_top=dict(top), files_by_arcs_audit_subdir=dict(sub),
        soft_exclusions=removed, paper=paper_rec, tooling=tooling_state, eol_restored_to_crlf=eol_restored, eol_lf_hash_also_recorded_elsewhere=eol_conflicts,
        paper1_figures_tables_changed_between_commit_and_paper_commit=drift,
        scans=dict(
            deny_list_hits=0, secret_or_email_or_id_header_hits=0,
            local_absolute_paths=dict(files=len(local_paths), total=sum(sum(v.values()) for v in local_paths.values()),
                                      per_file=local_paths),
            json_person_id_key_files=json_ids),
        selftest="passed",
    )
    (open(os.path.join(out, "RELEASE.json"), "w", encoding="utf-8", newline="\n")
     .write(json.dumps(release, indent=1, ensure_ascii=False, sort_keys=True) + "\n"))
    manifest_lines.append(f"{sha(open(os.path.join(out, 'RELEASE.json'), 'rb').read())}  RELEASE.json")
    with open(os.path.join(out, "MANIFEST.sha256"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sorted(manifest_lines, key=lambda s: s.split("  ", 1)[1])) + "\n")
    # re-verify the manifest as a consumer would
    n = 0
    for ln in open(os.path.join(out, "MANIFEST.sha256"), encoding="utf-8").read().splitlines():
        h, rel = ln.split("  ", 1)
        assert sha(open(os.path.join(out, *rel.split("/")), "rb").read()) == h, rel
        n += 1
    assert n == len(allfiles) + 1
    print(f"release tree: {out}")
    print(f"commit {commit[:7]}  paper-commit {paper_commit[:7]}  files {len(allfiles) + 2}  bytes {total}")
    print(f"CRLF restored (recorded sha256 names the CRLF bytes): {len(eol_restored)} files")
    print(f"soft exclusions: {dict(removed)}")
    print(f"local absolute paths: {len(local_paths)} files, {release['scans']['local_absolute_paths']['total']} occurrences")
    if json_ids:
        print(f"json person-id-like keys in {len(json_ids)} files (review): {list(json_ids)[:5]}")
    if drift:
        print(f"NOTE: paper1 figures/tables differ between --commit and --paper-commit: {drift}")
    if stale_tooling:
        print(f"NOTE: release tooling not equal to --paper-commit: {stale_tooling}")
    if left:
        print(f"NOTE: placeholders remain in {sorted(set(left))} (OK without --final)")


if __name__ == "__main__":
    main()
