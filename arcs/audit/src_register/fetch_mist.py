"""Pre-freeze work (claims register v4 section 1.10 (0), section 3.6): fetch the MIST atlas (Urchs et al. 2019),
figshare 10.6084/m9.figshare.5633638 (CC0), into E:\\data\\asdg\\mist\\, verify figshare's MD5, record sha256 of the zip
and of every extracted file, and write SOURCE.md there (a copy goes to arcs/audit/results/data_manifests/mist_SOURCE.md).

MIST is an ungated public atlas (register section 0: Moreau ungated; operator approval 2026-09-26, section 6 item 5).

Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src_register\\fetch_mist.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import sys
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
DEST = Path("E:/data/asdg/mist")
ARTICLE_API = "https://api.figshare.com/v2/articles/5633638"
UA = {"User-Agent": "asdg-register-prefreeze/1.0"}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    art = requests.get(ARTICLE_API, headers=UA, timeout=60)
    art.raise_for_status()
    meta = art.json()
    files = meta["files"]
    assert len(files) == 1 and files[0]["name"] == "MIST_parcellation.zip", "unexpected figshare file list"
    f = files[0]
    r = requests.get(f["download_url"], headers=UA, timeout=300)
    r.raise_for_status()
    blob = r.content
    assert len(blob) == int(f["size"]), "size mismatch %d vs %s" % (len(blob), f["size"])
    md5 = hashlib.md5(blob).hexdigest()
    assert md5 == f["computed_md5"], "md5 mismatch"
    zpath = DEST / f["name"]
    zpath.write_bytes(blob)
    assert sha256_bytes(zpath.read_bytes()) == sha256_bytes(blob), "read-back mismatch"
    zsha = sha256_bytes(blob)
    rows = []
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            data = z.read(info.filename)
            out = DEST / "extracted" / info.filename
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(data)
            assert out.read_bytes() == data
            rows.append((info.filename, len(data), sha256_bytes(data)))
    today = dt.date.today().isoformat()
    lines = [
        "# SOURCE: MIST multi-resolution functional parcellation (Urchs et al. 2019)",
        "",
        "- **date fetched**: %s" % today,
        "- **doi**: 10.6084/m9.figshare.5633638 (figshare article 5633638, version %s, published %s)" % (meta.get("version"), meta.get("published_date")),
        "- **title**: %s" % meta.get("title"),
        "- **licence**: %s (figshare record)" % meta.get("license", {}).get("name"),
        "- **url**: %s (file id %s)" % (f["download_url"], f["id"]),
        "- **file**: %s, %d bytes, figshare computed_md5 %s (verified), sha256 %s" % (f["name"], len(blob), md5, zsha),
        "- **fetched by**: arcs/audit/src_register/fetch_mist.py (claims register v4 section 1.10 (0), section 3.6; ungated)",
        "- **purpose**: MIST64 parcel centroids, hemisphere and tissue classes for Moreau 2020 (register 3.6), and a section 3.1-settings MIST64 AHBA matrix",
        "",
        "## Extracted files (under extracted/)",
        "",
        "| path | bytes | sha256 |",
        "|---|---|---|",
    ] + ["| %s | %d | %s |" % r_ for r_ in rows]
    txt = "\n".join(lines) + "\n"
    (DEST / "SOURCE.md").write_text(txt, encoding="utf-8", newline="\n")
    man = ROOT / "arcs" / "audit" / "results" / "data_manifests" / "mist_SOURCE.md"
    man.write_text(txt, encoding="utf-8", newline="\n")
    assert (DEST / "SOURCE.md").read_text(encoding="utf-8") == txt == man.read_text(encoding="utf-8")
    print("zip %s bytes %d sha256 %s md5 ok; extracted files %d" % (zpath, len(blob), zsha, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
