"""Identity at download / use (arcs/audit/RUN_PLAN.md v3.1 section 8 step 2, R18; P19).

The register's identity fields (claims_register.md:1088-1094, "R13"): "byte size plus git blob id for git copies;
byte size plus the served MD5 where the server gives a plain MD5 (an ETag of 32 hex digits, or a repository checksum
declared MD5 -- Apollo's DSpace listing); byte size alone otherwise (NeuroVault serves no ETag); a copy already on
disk is checked by its sha256". A mismatch at download -> "not auditable (map changed)".

- file_facts(path): bytes, sha256, MD5, git blob id of the bytes as they are, and -- when the file holds a CRLF --
  the git blob id and size after CRLF -> LF conversion (a Windows checkout of an LF blob; Hansen's case, P19).
- ref_from_probe(probe): the reference fields of one IDENTITY_prefreeze.json probe record (the record format of
  src_register/identity_prefreeze.py: GitHub git-tree listing, HTTP HEAD, NeuroVault metadata + HEAD, Apollo DSpace
  listing, local file on disk), with the basis the register assigns to it.
- compare(facts, refs): every reference must match on its own basis; the result is "identity match" or "not auditable
  (map changed)"; a git-blob reference is compared first on the bytes as they are, then (only if the file holds a CRLF)
  after CRLF -> LF conversion, and the record says which.
- size_probe(head, ref_bytes): the size-only probe -- an HTTP HEAD's Content-Length against the reference size, no
  body fetched. Its basis is "size only": a same-size change is not detectable by it (declared; the register's own
  limit for servers without a checksum, e.g. NeuroVault).
- load_prefreeze(path): the frozen IDENTITY_prefreeze.json, sha256 asserted against the freeze manifest's entry
  (register_freeze_manifest.json: 6cbde63e...), LF-normalised so a CRLF working copy is read as its blob.

Nothing here prints; callers record the returned dicts (hashes, sizes, labels from the vocabulary below).
WP2 review B4: file_facts and load_prefreeze refuse a path under the quarantine (fetch_extract.refuse_quarantine_opener:
any '_quarantine' component, or under the given quarantine root, default the production root) before opening it.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

STATUS_MATCH = "identity match"
STATUS_CHANGED = "not auditable (map changed)"
STATUS_AT_DOWNLOAD = "identity recorded at download (no pre-freeze identity)"
STATUS_NOT_ESTABLISHED = "identity not established (reference missing)"

BASIS_GIT = "git blob"
BASIS_GIT_LF = "git blob after CRLF to LF conversion"
BASIS_MD5 = "served MD5"
BASIS_SHA_DISK = "sha256 of the copy on disk"
BASIS_SIZE = "size only"
BASIS_PINNED_SHA = "pinned sha256"
BASIS_PINNED_SIZE = "pinned size"

PHRASES = (STATUS_MATCH, STATUS_CHANGED, STATUS_AT_DOWNLOAD, STATUS_NOT_ESTABLISHED, BASIS_GIT, BASIS_GIT_LF,
           BASIS_MD5, BASIS_SHA_DISK, BASIS_SIZE, BASIS_PINNED_SHA, BASIS_PINNED_SIZE,
           "bytes_lf git_blob git_blob_lf md5 sha256 basis result checks reference references lf_conversion "
           "has_crlf size_equal hash_equal content_length ref_bytes no Content-Length")

IDENTITY_PREFREEZE_REL = "arcs/audit/register_maps/IDENTITY_prefreeze.json"
IDENTITY_PREFREEZE_SHA256 = "6cbde63e33a94999554b5eb04f553a82fd58482d916958ff54979eb376d383e2"  # freeze manifest

_HEX32 = re.compile(r"[0-9a-fA-F]{32}")
_HEX40 = re.compile(r"[0-9a-f]{40}")
_HEX64 = re.compile(r"[0-9a-f]{64}")


def git_blob_of(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def facts_of_bytes(data: bytes) -> dict:
    out = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "md5": hashlib.md5(data).hexdigest(),
           "git_blob": git_blob_of(data), "has_crlf": b"\r\n" in data, "git_blob_lf": None, "bytes_lf": None}
    if out["has_crlf"]:
        lf = data.replace(b"\r\n", b"\n")
        out["git_blob_lf"], out["bytes_lf"] = git_blob_of(lf), len(lf)
    return out


def _refuse_quarantine(path, quarantine_root) -> None:
    from . import fetch_extract as FE   # at call time: fetch_extract imports this module
    FE.refuse_quarantine_opener(path, quarantine_root)


def file_facts(path: Path, quarantine_root: Path | None = None) -> dict:
    """Hashes of a file (read once). Large files are hashed in chunks; the CRLF conversion is done on the fly
    (a CR at a chunk end is carried into the next chunk). A path under the quarantine is refused first (B4)."""
    path = Path(path)
    _refuse_quarantine(path, quarantine_root)
    size = path.stat().st_size
    sha, md5 = hashlib.sha256(), hashlib.md5()
    blob = hashlib.sha1(b"blob %d\0" % size)
    lf_len, has_crlf, carry = 0, False, b""
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)
            md5.update(chunk)
            blob.update(chunk)
            buf = carry + chunk
            if buf.endswith(b"\r"):
                buf, carry = buf[:-1], b"\r"
            else:
                carry = b""
            if b"\r\n" in buf:
                has_crlf = True
            lf_len += len(buf.replace(b"\r\n", b"\n"))
    if carry:
        lf_len += 1
    out = {"bytes": size, "sha256": sha.hexdigest(), "md5": md5.hexdigest(), "git_blob": blob.hexdigest(),
           "has_crlf": has_crlf, "git_blob_lf": None, "bytes_lf": None}
    if has_crlf:
        # second pass: the git blob of the LF-converted bytes needs the converted length in its header
        h = hashlib.sha1(b"blob %d\0" % lf_len)
        carry = b""
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                buf = carry + chunk
                if buf.endswith(b"\r"):
                    buf, carry = buf[:-1], b"\r"
                else:
                    carry = b""
                h.update(buf.replace(b"\r\n", b"\n"))
        if carry:
            h.update(carry)
        out["git_blob_lf"], out["bytes_lf"] = h.hexdigest(), lf_len
    return out


def plain_md5(etag) -> str | None:
    """A plain-MD5 ETag: a strong ETag whose opaque value is exactly 32 hex digits (quoted or not). A weak ETag
    (W/...), a multipart ETag ("<hex>-<n>") or anything else -> None."""
    if not isinstance(etag, str):
        return None
    s = etag.strip()
    if s.startswith("W/"):
        return None
    if len(s) >= 2 and s[0] == s[-1] == '"':
        s = s[1:-1]
    return s.lower() if _HEX32.fullmatch(s) else None


def ref_from_probe(probe: dict) -> dict | None:
    """The reference identity fields of one IDENTITY_prefreeze probe (status "ok" only), or None.
    GitHub tree -> git blob + size; Apollo with checksum MD5 -> served MD5 + size; HEAD / NeuroVault with a plain-MD5
    ETag -> served MD5 + size; HEAD / NeuroVault otherwise -> size only; local copy -> sha256 + size."""
    if not isinstance(probe, dict) or probe.get("status") != "ok":
        return None
    method = str(probe.get("method", ""))
    if method.startswith("GitHub"):
        blob, size = probe.get("blob_sha"), probe.get("size")
        if isinstance(blob, str) and _HEX40.fullmatch(blob) and isinstance(size, int):
            return {"basis": BASIS_GIT, "bytes": size, "git_blob": blob}
        return None
    if method.startswith("Apollo"):
        size, ck, alg = probe.get("size"), probe.get("checksum"), str(probe.get("checksum_algorithm") or "")
        if isinstance(size, int) and alg.upper() == "MD5" and isinstance(ck, str) and _HEX32.fullmatch(ck):
            return {"basis": BASIS_MD5, "bytes": size, "md5": ck.lower()}
        if isinstance(size, int):
            return {"basis": BASIS_SIZE, "bytes": size}
        return None
    if method.startswith("local"):
        sha, size = probe.get("sha256"), probe.get("size")
        if isinstance(sha, str) and _HEX64.fullmatch(sha) and isinstance(size, int):
            return {"basis": BASIS_SHA_DISK, "bytes": size, "sha256": sha}
        return None
    if method.startswith("HTTP HEAD") or method.startswith("NeuroVault"):
        size = probe.get("content_length")
        if not isinstance(size, int):
            return None
        md5 = plain_md5(probe.get("etag"))
        if md5 is not None:
            return {"basis": BASIS_MD5, "bytes": size, "md5": md5}
        return {"basis": BASIS_SIZE, "bytes": size}
    return None


def _one(facts: dict, ref: dict) -> dict:
    basis = ref["basis"]
    c = {"basis": basis, "result": STATUS_CHANGED, "lf_conversion": False}
    if basis == BASIS_GIT:
        if facts["bytes"] == ref["bytes"] and facts["git_blob"] == ref["git_blob"]:
            c["result"] = STATUS_MATCH
        elif facts.get("has_crlf") and facts.get("bytes_lf") == ref["bytes"] and \
                facts.get("git_blob_lf") == ref["git_blob"]:
            c.update(result=STATUS_MATCH, basis=BASIS_GIT_LF, lf_conversion=True)
        c["size_equal"] = facts["bytes"] == ref["bytes"] or (c["lf_conversion"] and facts.get("bytes_lf") == ref["bytes"])
        c["hash_equal"] = c["result"] == STATUS_MATCH
    elif basis == BASIS_MD5:
        c["size_equal"] = facts["bytes"] == ref["bytes"]
        c["hash_equal"] = facts["md5"] == ref["md5"]
        if c["size_equal"] and c["hash_equal"]:
            c["result"] = STATUS_MATCH
    elif basis in (BASIS_SHA_DISK, BASIS_PINNED_SHA):
        c["size_equal"] = ref.get("bytes") is None or facts["bytes"] == ref["bytes"]
        c["hash_equal"] = facts["sha256"] == ref["sha256"]
        if c["size_equal"] and c["hash_equal"]:
            c["result"] = STATUS_MATCH
    elif basis in (BASIS_SIZE, BASIS_PINNED_SIZE):
        c["size_equal"] = facts["bytes"] == ref["bytes"]
        if c["size_equal"]:
            c["result"] = STATUS_MATCH
    else:
        raise ValueError("basis")
    return c


def compare(facts: dict, refs: list[dict], *, at_download_ok: bool = False) -> dict:
    """All references must match. No reference: STATUS_AT_DOWNLOAD if the target's identity is recorded at download
    (at_download_ok, e.g. R16's annot "sha256 recorded at download"), else STATUS_NOT_ESTABLISHED (fail closed)."""
    if not refs:
        return {"result": STATUS_AT_DOWNLOAD if at_download_ok else STATUS_NOT_ESTABLISHED, "checks": []}
    checks = [_one(facts, r) for r in refs]
    ok = all(c["result"] == STATUS_MATCH for c in checks)
    return {"result": STATUS_MATCH if ok else STATUS_CHANGED, "checks": checks,
            "lf_conversion": any(c["lf_conversion"] for c in checks)}


def size_probe(head: dict, ref_bytes: int) -> dict:
    """The size-only probe: a HEAD's Content-Length (no body) against the reference byte size."""
    cl = head.get("content_length") if isinstance(head, dict) else None
    if not isinstance(cl, int):
        return {"basis": BASIS_SIZE, "result": STATUS_NOT_ESTABLISHED, "content_length": None, "ref_bytes": ref_bytes}
    return {"basis": BASIS_SIZE, "result": STATUS_MATCH if cl == ref_bytes else STATUS_CHANGED,
            "content_length": cl, "ref_bytes": ref_bytes}


def load_prefreeze(path: Path, quarantine_root: Path | None = None) -> dict:
    """IDENTITY_prefreeze.json, its sha256 (LF-normalised bytes) asserted against the freeze manifest entry. A path
    under the quarantine is refused first (B4)."""
    _refuse_quarantine(path, quarantine_root)
    raw = Path(path).read_bytes()
    lf = raw.replace(b"\r\n", b"\n")
    if hashlib.sha256(lf).hexdigest() != IDENTITY_PREFREEZE_SHA256:
        raise AssertionError("IDENTITY_prefreeze.json differs from its freeze-manifest entry")
    doc = json.loads(lf.decode("utf-8"))
    if not isinstance(doc, dict) or not isinstance(doc.get("records"), list):
        raise AssertionError("IDENTITY_prefreeze.json: no records list")
    return doc


def probes_for_url(doc: dict, url: str) -> list[dict]:
    """Every ok probe of the pre-freeze record whose URL (url / file_url) equals the pinned URL exactly."""
    out = []
    for rec in doc["records"]:
        for p in rec.get("probes", []):
            if p.get("status") == "ok" and url in (p.get("url"), p.get("file_url")):
                out.append(p)
    return out
