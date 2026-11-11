"""Download helper for the A1 pre-freeze S-build (register §1.6). No personal identifier is ever sent (no e-mail,
no login, no API key). Every download is recorded (url, bytes, sha256) by the caller in the source's SOURCE.md.

get(url, out): plain curl; PMC 'bin' files sit behind a proof-of-work page (sha256(challenge + nonce) with
`difficulty` leading hex zeros, cookie `cloudpmc-viewer-pow` = challenge,nonce), solved here the way the page's own
script does it. curl is used because python-requests is answered with a reCAPTCHA page by PMC.

Usage: python -X utf8 fetch_util.py <url> <out_path>
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _solve(challenge: str, difficulty: int) -> int:
    pre = "0" * difficulty
    n = 0
    while not hashlib.sha256((challenge + str(n)).encode()).hexdigest().startswith(pre):
        n += 1
    return n


def _curl(url: str, out: Path, jar: Path, cookie: str | None = None, timeout: int = 900) -> str:
    cmd = ["curl", "-sS", "-L", "-m", str(timeout), "-A", UA, "-c", str(jar), "-b", str(jar), "-o", str(out),
           "-w", "%{http_code} %{content_type}", url]
    if cookie:
        cmd[1:1] = ["-b", cookie]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def get(url: str, out: Path) -> dict:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        jar = Path(td) / "jar.txt"
        status = _curl(url, out, jar)
        head = out.read_bytes()[:4000]
        if b"POW_CHALLENGE" in head:
            txt = head.decode("utf-8", "replace")
            ch = re.search(r'POW_CHALLENGE = "([^"]+)"', txt).group(1)
            diff = int(re.search(r'POW_DIFFICULTY = "(\d+)"', txt).group(1))
            name = re.search(r'POW_COOKIE_NAME = "([^"]+)"', txt).group(1)
            status = _curl(url, out, jar, cookie=f"{name}={ch},{_solve(ch, diff)}")
    code, ctype = (status.split(" ", 1) + [""])[:2]
    if code != "200":
        raise RuntimeError(f"HTTP {code} for {url}")
    head = out.read_bytes()[:600].lower()
    if "html" in ctype and not url.endswith((".html", ".htm", "/")) and (b"<html" in head or b"<!doctype" in head):
        raise RuntimeError(f"HTML page returned for {url} ({ctype})")
    return {"url": url, "path": str(out), "bytes": out.stat().st_size, "sha256": sha256(out), "content_type": ctype}


if __name__ == "__main__":
    print(get(sys.argv[1], Path(sys.argv[2])))
