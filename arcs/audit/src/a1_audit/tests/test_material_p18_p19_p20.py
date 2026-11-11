"""P18, P19, P20 (arcs/audit/RUN_PLAN.md v3.1 section 7) and P21's deferred part (section 2.2 "Plants (P21)": with G1
closed fetch_extract makes no network request -- its fetch functions replaced by ones that raise if called -- and the
launcher refuses).

    cd arcs/audit/src
    ..\\..\\..\\env\\venv\\Scripts\\python.exe -X utf8 -m a1_audit.tests.test_material_p18_p19_p20 [--scratch DIR] [--keep]

MATERIAL: synthetic files only, built in a scratch folder at test time: workbooks (.xlsx via openpyxl; .xls via a
minimal BIFF8 / OLE2 writer below, since xlwt is not installed), zips, tar streams, NIfTI-like arrays, FreeSurfer annots
and GIFTIs (nibabel). Identifier-shaped strings are generated at test time from digit runs of 9 (IDS below); none is
written into this file or any committed file, and none is printed (a leak is reported by its family name only).
A process-wide audit hook refuses (and counts) any file operation under E:\\data\\asdg or the agent transcript folder,
any socket connection other than 127.0.0.1, and any subprocess whose arguments name a URL other than the local stub
server; the counts are printed at the end and must be 0. The privacy guard's HGNC table (under E:\\data\\asdg) is never
read: its cache is preset to a synthetic symbol set and its path pointed at a scratch path that does not exist.
The repository files read are code, the A3 blob of h_targets.py (git), register_maps/mist64_classes.json (sha256
asserted; counts only) and register_maps/IDENTITY_prefreeze.json (sha256 asserted; counts per basis only).

P20's single criterion, for every run of the wrapper: everything the run emits (stdout, stderr, log files, every
record it writes, the names of the files it saves) is captured; (i) none of the synthetic carriers' strings occurs in
it (header / label cells, sheet names, zip / tar member names, extracted file names, undeclared cells, the planted
identifier-shaped ones) and the step-5 object holds the declared cells' values only, keyed by runner-side names;
(ii) every line parses with the print rule's allow-list. Plus the listed sub-cases.

Prints case names, counts and pass / fail only (ASCII). Exit code 0 iff every check passed.
"""
from __future__ import annotations

import argparse
import contextlib
import gzip
import hashlib
import http.server
import io
import json
import os
import re
import shutil
import socket
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1]                      # arcs/audit/src
REPO = HERE.parents[4]

ap = argparse.ArgumentParser()
ap.add_argument("--scratch", default=None)
ap.add_argument("--keep", action="store_true")
ARGS, _ = ap.parse_known_args()
SCRATCH = Path(ARGS.scratch or tempfile.mkdtemp(prefix="a1_p18_20_")).resolve()
SCRATCH.mkdir(parents=True, exist_ok=True)
RUN = SCRATCH / time.strftime("run_%Y%m%dT%H%M%S")
RUN.mkdir()

# ----------------------------------------------------------------------------------------------------------------
# process-wide tripwire (installed before any a1_audit import)
# ----------------------------------------------------------------------------------------------------------------
TRIP = {"material_path": 0, "socket": 0, "subprocess_url": 0}
_FORBIDDEN = (r"e:\data\asdg", "e:/data/asdg", r"c:\users\info\.claude\projects", "c:/users/info/.claude/projects")
STUB = {"port": None}


def _forbidden_path(a) -> bool:
    if isinstance(a, (str, bytes, os.PathLike)):
        try:
            s = os.fsdecode(a).lower()
        except Exception:  # noqa: BLE001
            return False
        return any(s.startswith(f) or (f in s and s.find(f) < 4) for f in _FORBIDDEN)
    return False


def _hook(event, args):
    if event in ("open", "os.listdir", "os.scandir", "os.rename", "os.replace", "os.remove", "os.rmdir", "os.mkdir",
                 "shutil.copyfile", "shutil.move", "shutil.rmtree", "os.chmod", "os.walk", "glob.glob"):
        if any(_forbidden_path(a) for a in args[:2]):
            TRIP["material_path"] += 1
            raise PermissionError("tripwire: material path")
    elif event == "socket.connect":
        addr = args[1] if len(args) > 1 else None
        host = addr[0] if isinstance(addr, tuple) and addr else None
        if host not in ("127.0.0.1", "::1", "localhost"):
            TRIP["socket"] += 1
            raise PermissionError("tripwire: socket")
    elif event == "subprocess.Popen":
        argv = args[1] if len(args) > 1 else None
        flat = [os.fsdecode(x) for x in (argv if isinstance(argv, (list, tuple)) else [argv]) if
                isinstance(x, (str, bytes, os.PathLike))]
        if any(_forbidden_path(x) for x in flat):
            TRIP["material_path"] += 1
            raise PermissionError("tripwire: subprocess material path")
        urls = [x for x in flat if re.match(r"(?i)^(https?|ftp)://", x)]
        if any(not x.startswith("http://127.0.0.1:") for x in urls):
            TRIP["subprocess_url"] += 1
            raise PermissionError("tripwire: subprocess url")


sys.addaudithook(_hook)
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
for _v in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
    os.environ.pop(_v, None)

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a1_audit import fetch_extract as FE  # noqa: E402
from a1_audit import gate_launch, gates  # noqa: E402
from a1_audit import identity as ID  # noqa: E402
from a1_audit import privacy_wrap as PW  # noqa: E402
from a1_audit import reparcel as RP  # noqa: E402

SYNTH_HGNC = frozenset(("SLC6A4", "ZNF804A", "KIAA0100", "LINC00473", "SHANKX1", "GRIN2B", "SCN2A", "PTEN", "DYRK1A",
                        "ARID1B", "CHD2", "NRXN1", "MECP2", "FOXP1"))
NO_HGNC = RUN / "no_such_hgnc_table.txt"
assert not NO_HGNC.exists()
FE.PG.HGNC_FILE = NO_HGNC                  # an unpatched load would fail here, never reach E:
FE.PG._HGNC = SYNTH_HGNC

# ----------------------------------------------------------------------------------------------------------------
# accounting
# ----------------------------------------------------------------------------------------------------------------
RESULTS: dict[str, dict[str, list[int]]] = {}
FAILS: list[str] = []


QUIET = {"on": False}


def ok(plant: str, sub: str, cond: bool, note: str = "") -> bool:
    r = RESULTS.setdefault(plant, {}).setdefault(sub, [0, 0])
    r[1] += 1
    if cond:
        r[0] += 1
    else:
        FAILS.append(f"{plant} / {sub}{(' / ' + note) if note else ''}")
        if not QUIET["on"]:
            print(f"  FAIL {plant} / {sub}{(' / ' + note) if note else ''}")
    return bool(cond)


# ----------------------------------------------------------------------------------------------------------------
# synthetic identifier-shaped strings (digit runs of 9, built at test time) and other carrier strings
# ----------------------------------------------------------------------------------------------------------------
def _ids() -> dict[str, str]:
    n = lambda k: "9" * k  # noqa: E731
    return {"nda_guid": "NDAR" + "_INV" + n(8), "nda_guid2": "NDAR" + "INV" + n(8), "bids": "sub-" + n(7),
            "spark": "SP" + n(7), "ssc": n(5) + ".p1", "brainspan": "HSB" + n(3) + "_QX", "umb": "UMB" + n(4),
            "gtex": "GTEX-" + n(5), "tcga": "TCGA-QQ-" + n(4), "num_code": n(4) + "_QX9", "code": "QZB-" + n(4),
            "geo": "GSM" + n(6), "an_code": "AN" + n(5)}


IDS = _ids()


class Carrier:
    """Every carrier-derived string of one synthetic carrier, by family (for criterion (i))."""

    def __init__(self):
        self.strings: dict[str, set[str]] = {}
        self.declared_values: set[str] = set()     # declared cells' text values (allowed in the step-5 object only)

    def add(self, family: str, *ss):
        for s in ss:
            if isinstance(s, str) and s.strip():
                self.strings.setdefault(family, set()).add(s)

    def all(self):
        for fam, ss in self.strings.items():
            for s in ss:
                yield fam, s


def variants(s: str) -> set[str]:
    out = {s, json.dumps(s)[1:-1], s.replace("\\", "/"), s.strip()}
    out |= {json.dumps(x)[1:-1] for x in list(out)}
    return {x for x in out if x}


# ----------------------------------------------------------------------------------------------------------------
# minimal BIFF8 (.xls) writer: OLE2 compound file with one Workbook stream; LABEL / NUMBER records
# ----------------------------------------------------------------------------------------------------------------
def _rec(op, data=b""):
    return struct.pack("<HH", op, len(data)) + data


def _bof(dt):
    return _rec(0x0809, struct.pack("<HHHHII", 0x0600, dt, 0x0DBB, 0x07CC, 0, 0x06))


def _ustr(s, lenlen):
    b = s.encode("utf-16-le")
    return (struct.pack("<B", len(s)) if lenlen == 1 else struct.pack("<H", len(s))) + b"\x01" + b


def _sheet_stream(rows):
    out = _bof(0x0010)
    nr = len(rows)
    nc = max((len(r) for r in rows), default=0)
    out += _rec(0x0200, struct.pack("<IIHHH", 0, nr, 0, nc, 0))
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            if v is None:
                continue
            if isinstance(v, str):
                out += _rec(0x0204, struct.pack("<HHH", i, j, 0) + _ustr(v, 2))
            else:
                out += _rec(0x0203, struct.pack("<HHHd", i, j, 0, float(v)))
    return out + _rec(0x000A)


def write_xls(path: Path, sheets):
    """sheets: [(name, rows, corrupt)]; a corrupt sheet's BOUNDSHEET offset points at bytes that are no BOF."""
    head = _bof(0x0005) + _rec(0x0042, struct.pack("<H", 1200))
    glob_len = len(head) + sum(len(_rec(0x0085, struct.pack("<iBB", 0, 0, 0) + _ustr(n, 1))) for n, _, _ in sheets) \
        + len(_rec(0x000A))
    bodies = [(b"\xde\xad\xbe\xef" * 8 if c else _sheet_stream(rows)) for _, rows, c in sheets]
    offs, pos = [], glob_len
    for b in bodies:
        offs.append(pos)
        pos += len(b)
    g = head + b"".join(_rec(0x0085, struct.pack("<iBB", o, 0, 0) + _ustr(n, 1)) for (n, _, _), o in zip(sheets, offs))
    g += _rec(0x000A)
    assert len(g) == glob_len
    stream = g + b"".join(bodies)
    SS = 512
    if len(stream) < 4096:
        stream += b"\x00" * (4096 - len(stream))
    if len(stream) % SS:
        stream += b"\x00" * (SS - len(stream) % SS)
    n_data, n_dir, n_fat = len(stream) // SS, 1, 1
    while n_data + n_dir + n_fat > 128 * n_fat:
        n_fat += 1
    END, FREE, FATS, NOS = 0xFFFFFFFE, 0xFFFFFFFF, 0xFFFFFFFD, 0xFFFFFFFF
    fat = [i + 1 if i < n_data - 1 else END for i in range(n_data)] + [END] + [FATS] * n_fat
    fat += [FREE] * (128 * n_fat - len(fat))

    def dentry(name, typ, child, start, size):
        nm = (name.encode("utf-16-le") + b"\x00\x00") if name else b""
        e = nm.ljust(64, b"\x00") + struct.pack("<HBB", len(nm), typ, 1) + struct.pack("<III", NOS, NOS, child)
        e += b"\x00" * 16 + struct.pack("<I", 0) + b"\x00" * 16 + struct.pack("<II", start, size) + struct.pack("<I", 0)
        return e
    d = dentry("Root Entry", 5, 1, END, 0) + dentry("Workbook", 2, NOS, 0, len(stream)) + dentry("", 0, NOS, 0, 0) * 2
    hdr = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1" + b"\x00" * 16 + struct.pack("<HHHHH", 0x3E, 3, 0xFFFE, 9, 6) + b"\x00" * 6
    hdr += struct.pack("<IIIIIIIII", 0, n_fat, n_data, 0, 4096, END, 0, END, 0)
    hdr += struct.pack("<109I", *(list(range(n_data + 1, n_data + 1 + n_fat)) + [FREE] * (109 - n_fat)))
    path.write_bytes(hdr + stream + d + struct.pack("<%dI" % len(fat), *fat))


def write_xlsx(path: Path, sheets):
    """sheets: [(name, rows, corrupt)]; a corrupt sheet's part is replaced by XML that raises if parsed."""
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, rows, _ in sheets:
        ws = wb.create_sheet(name)
        for r in rows:
            ws.append(list(r))
    tmp = path.with_name(path.name + ".plain.xlsx")
    wb.save(tmp)
    bad = {f"xl/worksheets/sheet{i + 1}.xml" for i, (_, _, c) in enumerate(sheets) if c}
    with zipfile.ZipFile(tmp) as zi, zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zi.infolist():
            b = zi.read(it.filename)
            if it.filename in bad:
                b = b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row><c r='
            zo.writestr(it, b)
    tmp.unlink()


# ----------------------------------------------------------------------------------------------------------------
# synthetic workbooks with W / N / V sheets
# ----------------------------------------------------------------------------------------------------------------
GENES = ["SLC6A4", "ZNF804A", "KIAA0100", "GRIN2B", "SCN2A", "PTEN"]


def wnv_book(tag: str, rng) -> tuple[list, list, Carrier, dict]:
    """(sheets, declarations, carrier strings, expected step-5 objects). tag makes every string distinct per book."""
    C = Carrier()
    sheets, decls, expect = [], [], {}
    # W: 56 populated columns, neutral-looking headers that are identifier-shaped beyond the declared two
    hW = [f"Qx{tag}GeneSym", f"Qx{tag}LogFold"] + [f"{IDS['bids']}{chr(65 + k % 26)}{k}" for k in range(54)]
    rowsW = [hW]
    exp_g, exp_v = [], []
    for i, g in enumerate(GENES):
        v = round(float(rng.normal()), 6)
        und = [round(900 + float(rng.random()), 7) for _ in range(54)]
        rowsW.append([g, v] + und)
        exp_g.append(g)
        exp_v.append(v)
        C.add("undeclared_numeric", *[repr(x) for x in und])
    sW = f"Qx{tag}WideSheet"
    sheets.append((sW, rowsW, False))
    decls.append(FE.SheetDecl(key=f"wide_{tag}", name=sW, header_row=0,
                              columns=(FE.Column(hW[0], "gene"), FE.Column(hW[1], "log2fc", numeric=True))))
    expect[f"wide_{tag}"] = {"columns": {"gene": exp_g, "log2fc": exp_v}}
    C.add("sheet_name", sW)
    C.add("header", *hW)
    C.declared_values |= set(exp_g)
    # N: identifier wording header; undeclared column of planted ids; a title row above the header
    hN = [f"Sample ID {tag}", f"Qx{tag}Symbol", f"Qx{tag}Score"]
    title = f"Qx{tag} Table S9 title row"
    rowsN = [[title], hN]
    fam = list(IDS)
    exp_s, exp_sc = [], []
    for i, g in enumerate(GENES):
        sc = round(float(rng.normal()), 6)
        rowsN.append([IDS[fam[i % len(fam)]] + tag, g, sc])
        exp_s.append(g)
        exp_sc.append(sc)
        C.add("undeclared_cell_id", IDS[fam[i % len(fam)]] + tag)
    sN = f"Qx{tag}SampleSheet"
    sheets.append((sN, rowsN, False))
    decls.append(FE.SheetDecl(key=f"sample_{tag}", name=sN, header_row=1,
                              columns=(FE.Column(hN[1], "symbol"), FE.Column(hN[2], "score", numeric=True))))
    expect[f"sample_{tag}"] = {"columns": {"symbol": exp_s, "score": exp_sc}}
    C.add("sheet_name", sN)
    C.add("header", *hN, title)
    C.declared_values |= set(exp_s)
    # V: identifier-valued tokens in the header zone (header cells that are planted ids)
    hV = [f"Qx{tag}Gene", IDS["brainspan"], IDS["nda_guid"], IDS["code"], f"Qx{tag}Beta"]
    rowsV = [hV]
    exp_vg, exp_vb = [], []
    for i, g in enumerate(GENES[:4]):
        b = round(float(rng.normal()), 6)
        rowsV.append([g, round(700 + float(rng.random()), 7), IDS["umb"] + tag, IDS["gtex"] + tag, b])
        exp_vg.append(g)
        exp_vb.append(b)
        C.add("undeclared_cell_id", IDS["umb"] + tag, IDS["gtex"] + tag)
    sV = f"Qx{tag}ValueSheet"
    sheets.append((sV, rowsV, False))
    decls.append(FE.SheetDecl(key=f"value_{tag}", name=sV, header_row=0,
                              columns=(FE.Column(hV[0], "gene"), FE.Column(hV[4], "beta", numeric=True))))
    expect[f"value_{tag}"] = {"columns": {"gene": exp_vg, "beta": exp_vb}}
    C.add("sheet_name", sV)
    C.add("header", *hV)
    C.declared_values |= set(exp_vg)
    # undeclared sheets: identifier-shaped names, a non-ASCII name, one whose part raises if parsed
    for nm, corrupt in ((IDS["bids"] + tag, False), (f"Donn\u00e9es {tag}", False), (IDS["nda_guid"][:20] + tag, True)):
        rows = [[f"Qx{tag}Hidden header", IDS["spark"] + tag], [IDS["ssc"] + tag, 1.5]]
        sheets.append((nm, rows, corrupt))
        C.add("sheet_name", nm)
        C.add("undeclared_cell_id", f"Qx{tag}Hidden header", IDS["spark"] + tag, IDS["ssc"] + tag)
    for fam_, s in IDS.items():
        C.add("planted_id", s)
    return sheets, decls, C, expect


def mist_vocab_synth() -> tuple:
    """64 synthetic MIST-like parcels: roi 1..64; labels mixed case; names; distinct when casefolded."""
    out = []
    for k in range(1, 65):
        out.append((k, f"QxLab{k:02d}{'Ab' if k % 2 else 'Cd'}", f"qx name {k:02d} region"))
    return tuple(out)


def moreau_sheet(vocab, form: str, rng, *, title_rows=2, corner=True, perturb=True, bad=None):
    """A 64 x 64 Moreau-like sheet: title rows, a header row of 64 identifiers (label / name / roi form) with a corner
    label, then 64 rows (row label + 64 numbers). Columns and rows are shuffled. Returns (rows, carrier strings,
    expected block by roi)."""
    C = Carrier()
    order_c = list(rng.permutation(64) + 1)
    order_r = list(rng.permutation(64) + 1)
    lab = {r: lab_ for r, lab_, _ in vocab}
    nam = {r: n_ for r, _, n_ in vocab}

    def ident(r, where):
        if form == "label":
            s = lab[r]
            return ("  " + s.swapcase() + " ") if perturb else s
        if form == "name":
            s = nam[r]
            return (" " + s.upper()) if perturb else s
        return float(r) if where == "col" else str(r)
    rows = []
    for t in range(title_rows):
        rows.append([f"QxMoreau title {t} {IDS['bids']}"] + [None] * 3)
        C.add("title", rows[-1][0])
    if title_rows:
        rows.append([None])
    header = ["QxCornerROI" if corner else None] + [ident(c, "col") for c in order_c]
    C.add("corner", "QxCornerROI")
    for v in header[1:]:
        if isinstance(v, str) and re.search("[A-Za-z]", v):   # a digit-only label is a number (declared limit)
            C.add("label_cell", v)
    rows.append(header)
    block = np.zeros((64, 64))
    for r in order_r:
        vals = [round(float(x), 6) for x in rng.normal(size=64)]
        rows.append([ident(r, "row")] + vals)
        if isinstance(rows[-1][0], str) and re.search("[A-Za-z]", rows[-1][0]):
            C.add("label_cell", rows[-1][0])
        for c, v in zip(order_c, vals):
            block[r - 1, c - 1] = v
    if bad == "nonnumeric":
        rows[-1][5] = IDS["code"]
    rows.append([f"QxFootnote {IDS['ssc']}"])
    C.add("footnote", rows[-1][0])
    return rows, C, block


# ----------------------------------------------------------------------------------------------------------------
# local stub server (127.0.0.1 only)
# ----------------------------------------------------------------------------------------------------------------
SERVED: dict[str, bytes] = {}
LAST_MOD = "Tue, 27 Jun 2023 10:00:00 GMT"


class _Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):           # the default writes the request line to stderr
        pass

    def _head(self):
        b = SERVED.get(self.path)
        if b is None:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return None
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Last-Modified", LAST_MOD)
        self.send_header("ETag", '"%s"' % hashlib.md5(b).hexdigest())
        self.end_headers()
        return b

    def do_HEAD(self):
        self._head()

    def do_GET(self):
        b = self._head()
        if b is not None:
            with contextlib.suppress(Exception):
                self.wfile.write(b)


def start_stub():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    STUB["port"] = srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    return srv


def serve(name: str, data: bytes) -> str:
    SERVED["/" + name] = data
    return f"http://127.0.0.1:{STUB['port']}/{name}"


# ----------------------------------------------------------------------------------------------------------------
# roots, capture, criteria (i) and (ii)
# ----------------------------------------------------------------------------------------------------------------
def make_roots(name: str) -> FE.Roots:
    b = RUN / name
    data = b / "data"
    return FE.Roots(repo=REPO, data=data, records=b / "records", artifacts=b / "artifacts", logs=b / "logs",
                    control=b / "control", quarantine=data / "_quarantine")


def run_captured(t: FE.Target, roots: FE.Roots) -> tuple[dict, str, str]:
    out, err = io.StringIO(), io.StringIO()
    stray_o, stray_e = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stray_o), contextlib.redirect_stderr(stray_e):
        res = FE.run_target(t, roots, out=out, err=err)
    return res, out.getvalue() + stray_o.getvalue(), err.getvalue() + stray_e.getvalue()


def all_files(roots: FE.Roots) -> list[Path]:
    base = roots.data.parent
    return sorted(p for p in base.rglob("*") if p.is_file())


def emitted_texts(roots: FE.Roots, stdout: str, stderr: str, exclude: set[Path]) -> dict[str, str]:
    """Everything a run emits except the step-5 object: stdout, stderr, every file it wrote (logs, records, SOURCE.md,
    deletion requests) as text, and the relative names of every file and folder it created."""
    texts = {"stdout": stdout, "stderr": stderr}
    base = roots.data.parent
    names = []
    for p in sorted(base.rglob("*")):
        names.append(p.relative_to(base).as_posix())
        if p.is_file() and p not in exclude and p.suffix in (".log", ".json", ".md"):
            texts["file:" + p.name] = p.read_text(encoding="utf-8")
    texts["file names"] = "\n".join(names)
    return texts


def criterion_i(texts: dict[str, str], C: Carrier, step5: dict | None, step5_expected: dict | None,
                plant: str, sub: str) -> bool:
    """(i): no carrier string in anything emitted; the step-5 object equals the expected declared values and holds no
    carrier string but declared cells' values."""
    leaks = set()
    for fam, s in C.all():
        for v in variants(s):
            for lab, txt in texts.items():
                if v in txt:
                    leaks.add((fam, lab))
    good = ok(plant, sub + ": (i) no carrier string emitted", not leaks,
              "; ".join(sorted(f"{f} in {l}" for f, l in leaks))[:300])
    if step5_expected is not None:
        good &= ok(plant, sub + ": (i) step-5 object = declared cells keyed by runner-side names",
                   step5 is not None and step5.get("objects") == step5_expected)
        s5 = json.dumps(step5, ensure_ascii=True) if step5 is not None else ""
        bad = set()
        for fam, s in C.all():
            if s in C.declared_values:
                continue
            for v in variants(s):
                if v and v in s5 and not (fam == "undeclared_numeric" and len(v) < 6):
                    bad.add(fam)
        good &= ok(plant, sub + ": (i) step-5 object holds no other carrier string", not bad, ",".join(sorted(bad)))
    return good


def test_allow(targets: list[FE.Target], roots: FE.Roots) -> PW.AllowList:
    allow = FE.make_allow(targets[0], roots)
    for t in targets[1:]:
        a2 = FE.make_allow(t, roots)
        allow.words |= a2.words
        allow.identity_exact |= a2.identity_exact
    base = roots.data.parent
    for p in base.rglob("*"):
        allow.add_exact(p)
        if roots.quarantine in p.parents and p.is_file():      # <quarantine>/<gate>/<key>/<name>: built at <data>/<key>
            allow.add_exact(roots.data / p.parent.name / p.name)
    for t in targets:
        for m in t.members:
            if m.save_name:
                allow.add_exact(m.save_name)
    allow._rx = allow._rx_id = None
    return allow


def criterion_ii(texts: dict[str, str], allow: PW.AllowList, plant: str, sub: str) -> bool:
    bad = []
    for lab, txt in texts.items():
        if lab == "file names":
            continue
        ctx = "identity" if lab.startswith("file:") and (lab.endswith(".json") or lab.endswith(".md")) else \
            ("stderr" if lab == "stderr" else "stdout")
        for k, ln in enumerate(txt.split("\n")):
            if not allow.check(ln, ctx):
                bad.append(f"{lab}:{k + 1}")
    return ok(plant, sub + ": (ii) every line parses with the allow-list", not bad, ",".join(bad[:5]))


def runner_names_ok(roots: FE.Roots, keys: set[str], plant: str, sub: str) -> bool:
    base = roots.data.parent
    pat = re.compile(r"(carrier\.[a-z.]+|SOURCE\.md|lh\.aparc\.annot|[A-Za-z0-9_\-]+_member\d+\.[a-z]+|"
                     r"[A-Za-z0-9_\-]+_extract\.json|[A-Za-z0-9_\-]+(\.\d+)?\.json|[A-Za-z0-9_\-]+_deletion_request\.json|"
                     r"[A-Za-z0-9_\-]+\.log|data|records|artifacts|logs|control|_quarantine|ungated|G1|G2)")
    bad = [p.relative_to(base).as_posix() for p in base.rglob("*")
           if not (pat.fullmatch(p.name) or p.name in keys)]
    return ok(plant, sub + ": saved file / folder names runner-built", not bad, str(len(bad)))


def load_step5(res: dict) -> tuple[dict | None, Path | None]:
    for w in res.get("written", []):
        if w.endswith("_extract.json"):
            p = Path(w)
            return json.loads(p.read_text(encoding="utf-8")), p
    return None, None


def record_of(res: dict) -> dict:
    p = res.get("record_path")
    return json.loads(Path(p).read_text(encoding="utf-8")) if p else {}


# ================================================================================================================
# P19: identity at download / use
# ================================================================================================================
def p19():
    print("\nP19 identity at download / use (synthetic files)")
    P = "P19"
    rng = np.random.default_rng(19)
    d = RUN / "p19"
    d.mkdir()
    base = bytes(rng.integers(0, 256, size=5000, dtype=np.uint8))
    one = bytearray(base)
    one[1234] ^= 0x01
    one = bytes(one)
    f0, f1 = d / "a.bin", d / "b.bin"
    f0.write_bytes(base)
    f1.write_bytes(one)
    F0, F1 = ID.file_facts(f0), ID.file_facts(f1)
    ok(P, "file_facts = facts_of_bytes", F0 == ID.facts_of_bytes(base) and F1 == ID.facts_of_bytes(one))
    refs = {"git blob": {"basis": ID.BASIS_GIT, "bytes": len(base), "git_blob": F0["git_blob"]},
            "served MD5": {"basis": ID.BASIS_MD5, "bytes": len(base), "md5": F0["md5"]},
            "sha256 copy on disk": {"basis": ID.BASIS_SHA_DISK, "bytes": len(base), "sha256": F0["sha256"]},
            "pinned sha256": {"basis": ID.BASIS_PINNED_SHA, "bytes": len(base), "sha256": F0["sha256"]}}
    for name, r in refs.items():
        ok(P, f"one byte changed -> map changed ({name})",
           ID.compare(F0, [r])["result"] == ID.STATUS_MATCH and ID.compare(F1, [r])["result"] == ID.STATUS_CHANGED)
    # git blob id = git's own (independent check through git hash-object)
    gh = subprocess.run(["git", "hash-object", str(f0)], capture_output=True).stdout.decode().strip()
    ok(P, "git blob id equals git hash-object", gh == F0["git_blob"])
    # size only: a same-size change is not detectable (declared); a size change is
    rs = {"basis": ID.BASIS_SIZE, "bytes": len(base)}
    ok(P, "size only: same-size one-byte change passes (declared limit, basis recorded)",
       ID.compare(F1, [rs])["result"] == ID.STATUS_MATCH and ID.compare(F1, [rs])["checks"][0]["basis"] == "size only")
    f2 = d / "c.bin"
    f2.write_bytes(base + b"\x00")
    ok(P, "size only: one byte added -> map changed", ID.compare(ID.file_facts(f2), [rs])["result"] == ID.STATUS_CHANGED)
    ok(P, "two references: one mismatching -> map changed",
       ID.compare(F0, [refs["git blob"], {"basis": ID.BASIS_SIZE, "bytes": 1}])["result"] == ID.STATUS_CHANGED)
    ok(P, "no reference -> not established; at download -> recorded",
       ID.compare(F0, [])["result"] == ID.STATUS_NOT_ESTABLISHED and
       ID.compare(F0, [], at_download_ok=True)["result"] == ID.STATUS_AT_DOWNLOAD)
    # CRLF copy vs LF blob (Hansen's case)
    lf = b"".join(b"r%d,%0.6f,%0.6f\n" % (i, rng.normal(), rng.normal()) for i in range(400))
    fl, fc, fx = d / "lf.csv", d / "crlf.csv", d / "crlf_changed.csv"
    fl.write_bytes(lf)
    fc.write_bytes(lf.replace(b"\n", b"\r\n"))
    xb = bytearray(lf.replace(b"\n", b"\r\n"))
    xb[100] = ord("7") if xb[100] != ord("7") else ord("8")
    fx.write_bytes(bytes(xb))
    blob = subprocess.run(["git", "hash-object", "--no-filters", str(fl)], capture_output=True).stdout.decode().strip()
    rg = {"basis": ID.BASIS_GIT, "bytes": len(lf), "git_blob": blob}
    cl = ID.compare(ID.file_facts(fl), [rg])
    cc = ID.compare(ID.file_facts(fc), [rg])
    cx = ID.compare(ID.file_facts(fx), [rg])
    ok(P, "LF copy vs LF blob: direct match", cl["result"] == ID.STATUS_MATCH and not cl["lf_conversion"])
    ok(P, "CRLF copy vs LF blob: match after LF conversion, recorded",
       cc["result"] == ID.STATUS_MATCH and cc["lf_conversion"] and cc["checks"][0]["basis"] == ID.BASIS_GIT_LF)
    ok(P, "CRLF copy, one byte changed -> map changed", cx["result"] == ID.STATUS_CHANGED)
    ok(P, "a CRLF-only check (blob of the working copy as is) fails on the CRLF copy (the conversion is needed)",
       ID.file_facts(fc)["git_blob"] != blob)
    # chunk boundary: a CR at the last byte of a 1 MiB chunk, its LF in the next chunk
    big = bytearray(b"x" * ((1 << 20) + 50))
    big[(1 << 20) - 1:(1 << 20) + 1] = b"\r\n"
    fb = d / "big.txt"
    fb.write_bytes(bytes(big))
    ok(P, "file_facts: CRLF split across a 1 MiB chunk boundary", ID.file_facts(fb) == ID.facts_of_bytes(bytes(big)))
    # plain-MD5 ETag
    h = hashlib.md5(b"q").hexdigest()
    ok(P, "plain-MD5 ETag forms", ID.plain_md5('"%s"' % h) == h and ID.plain_md5(h.upper()) == h and
       ID.plain_md5('W/"%s"' % h) is None and ID.plain_md5('"%s-3"' % h) is None and ID.plain_md5(h[:31]) is None)
    # ref_from_probe on synthetic probe records of each pre-freeze method
    probes = [({"method": "GitHub git-tree listing (recursive)", "status": "ok", "blob_sha": "a" * 40, "size": 9}, "git blob"),
              ({"method": "HTTP HEAD", "status": "ok", "content_length": 9, "etag": '"%s"' % h}, "served MD5"),
              ({"method": "HTTP HEAD", "status": "ok", "content_length": 9, "etag": '"abc-2"'}, "size only"),
              ({"method": "NeuroVault image metadata (file, file_size only) + HTTP HEAD", "status": "ok",
                "content_length": 9, "etag": None}, "size only"),
              ({"method": "Apollo DSpace 7 REST listing", "status": "ok", "size": 9, "checksum": h,
                "checksum_algorithm": "MD5"}, "served MD5"),
              ({"method": "local file already on disk (hashed only, not parsed)", "status": "ok", "size": 9,
                "sha256": "b" * 64}, "sha256 of the copy on disk"),
              ({"method": "HTTP HEAD", "status": "unreachable", "content_length": 9}, None)]
    ok(P, "ref_from_probe: basis per pre-freeze probe method (7 forms)",
       all((ID.ref_from_probe(p) or {}).get("basis") == b for p, b in probes))
    # the real IDENTITY_prefreeze.json: sha256 asserted; every ok probe maps to a basis (counts only)
    doc = ID.load_prefreeze(REPO / ID.IDENTITY_PREFREEZE_REL)
    counts: dict[str, int] = {}
    n_ok = n_none = 0
    for rec in doc["records"]:
        for p in rec.get("probes", []):
            if p.get("status") != "ok":
                continue
            n_ok += 1
            r = ID.ref_from_probe(p)
            if r is None:
                n_none += 1
            else:
                counts[r["basis"]] = counts.get(r["basis"], 0) + 1
    print(f"  IDENTITY_prefreeze.json (sha256 pinned): ok probes {n_ok}; by basis "
          + "; ".join(f"{k} {v}" for k, v in sorted(counts.items())) + f"; without a basis {n_none}")
    ok(P, "IDENTITY_prefreeze.json loads (pin) and every ok probe has a basis", n_ok > 0 and n_none == 0)
    try:
        bad = d / "pf.json"
        bad.write_bytes((REPO / ID.IDENTITY_PREFREEZE_REL).read_bytes() + b" ")
        ID.load_prefreeze(bad)
        refused = False
    except AssertionError:
        refused = True
    ok(P, "IDENTITY_prefreeze.json one byte changed -> refused", refused)

    # the size-only probe through the real HEAD code (curl) against the local stub
    url = serve("p19/size_probe.bin", base)
    head = FE._curl_head(url)
    ok(P, "HEAD (curl, local stub): Content-Length, Last-Modified, plain-MD5 ETag kept",
       head["content_length"] == len(base) and head["last_modified"] == LAST_MOD and head["etag_md5"] ==
       hashlib.md5(base).hexdigest() and head["status_code"] == 200)
    ok(P, "size-only probe: equal -> match; one byte more -> map changed; no Content-Length -> not established",
       ID.size_probe(head, len(base))["result"] == ID.STATUS_MATCH and
       ID.size_probe(head, len(base) + 1)["result"] == ID.STATUS_CHANGED and
       ID.size_probe({"content_length": None}, 5)["result"] == ID.STATUS_NOT_ESTABLISHED)

    # end to end through the wrapper: a one-byte-changed download -> map changed, nothing extracted
    sheets, decls, C, expect = wnv_book("idc", np.random.default_rng(190))
    good = d / "good.xlsx"
    write_xlsx(good, sheets)
    gb = good.read_bytes()
    changed = bytearray(gb)
    changed[-30] ^= 0x01
    url2 = serve("p19/changed.xlsx", bytes(changed))
    t = FE.Target(key="p19changed", gate="ungated", url=url2, kind="workbook", ext=".xlsx",
                  pinned_bytes=len(gb), pinned_sha256=hashlib.sha256(gb).hexdigest(), sheets=tuple(decls))
    roots = make_roots("p19_changed")
    res, so, se = run_captured(t, roots)
    rec = record_of(res)
    ok(P, "wrapper: one byte changed at download -> 'not auditable (map changed)', no sheet read",
       res["status"] == ID.STATUS_CHANGED and "sheets" not in rec and rec.get("identity", {}).get("comparison", {})
       .get("result") == ID.STATUS_CHANGED and load_step5(res)[0] is None)
    # the copy on disk is used on a second run (no download: the fetch functions raise if called); a clean workbook
    # (no identifier-bearing sheet, no screen hit), so the first run leaves it in place
    clean = d / "clean.xlsx"
    write_xlsx(clean, [("QxCleanSheet", [["QxGeneCol", "QxValCol"]] + [[g, float(i)] for i, g in enumerate(GENES)],
                        False)])
    gb = clean.read_bytes()
    cdecl = (FE.SheetDecl(key="clean", name="QxCleanSheet", header_row=0,
                          columns=(FE.Column("QxGeneCol", "gene"), FE.Column("QxValCol", "value", numeric=True))),)
    url3 = serve("p19/clean.xlsx", gb)
    t3 = FE.Target(key="p19clean", gate="ungated", url=url3, kind="workbook", ext=".xlsx", pinned_bytes=len(gb),
                   pinned_sha256=hashlib.sha256(gb).hexdigest(), sheets=cdecl)
    roots3 = make_roots("p19_clean")
    r1, _, _ = run_captured(t3, roots3)
    saved_net = dict(FE.NET)
    calls = []
    FE.NET.update(head=lambda *a, **k: calls.append(1) or (_ for _ in ()).throw(AssertionError()),
                  get=lambda *a, **k: calls.append(1) or (_ for _ in ()).throw(AssertionError()))
    try:
        r2, so2, _ = run_captured(t3, roots3)
    finally:
        FE.NET.update(saved_net)
    rec1, rec2 = record_of(r1), record_of(r2)
    ok(P, "copy on disk: first run extracted, not identifier-bearing, carrier kept in place",
       r1["status"] == FE.STATUS_EXTRACTED and rec1.get("identifier_bearing") is False and
       (roots3.data / t3.key / "carrier.xlsx").exists())
    ok(P, "copy on disk: second run makes no request, identity by the pinned sha256; the existing step-5 object is "
       "not overwritten (save refused; the record takes <key>.2.json)",
       calls == [] and rec2.get("fetch", {}).get("source") == "copy on disk" and
       rec2["identity"]["comparison"]["result"] == ID.STATUS_MATCH and rec2.get("failed_stage") == "save" and
       r2["record_path"].endswith("p19clean.2.json"))


# ================================================================================================================
# P20: privacy wrapper
# ================================================================================================================
def p20_apparatus():
    """Planted failures the print-rule apparatus must catch."""
    P = "P20"
    print("\nP20 apparatus: planted print-rule failures")
    roots = make_roots("p20_apparatus")
    t = FE.Target(key="apparatus", gate="ungated", url=serve("x/a.xlsx", b"x"), kind="file", ext=".bin")
    allow = FE.make_allow(t, roots)
    okline = "fetch_extract: apparatus declared sheets 2 / 2 found; undeclared 7 (not fetched); sheet-name sha256 " \
             "recorded 9; screen hits V 3 N 0"
    ok(P, "allow-list: a normal runner line parses", allow.check(okline, "stdout"))
    planted = list(IDS.values()) + ["QxGeneSym", "Donn\u00e9es", "1_16p11.2Del", "5_BIV", "REFUSED: plant sheet 'x'",
                                    "Sample ID", "subjects/fsaverage/label/lh.aparc.annot"]
    caught = sum(1 for s in planted if not allow.check(okline + " " + s, "stdout"))
    ok(P, f"allow-list: a line holding a planted carrier string fails ({len(planted)} strings)", caught == len(planted),
       f"{caught}/{len(planted)}")
    ok(P, "allow-list: the pinned URL only in identity records",
       allow.check("- url: " + t.url, "identity") and not allow.check("- url: " + t.url, "stdout"))
    ok(P, "allow-list: an unregistered path fails, a registered one passes",
       not allow.check(f"saved {RUN / 'x' / 'y.txt'}", "stdout") and
       (allow.add_exact(RUN / "x" / "y.txt") or allow.check(f"saved {RUN / 'x' / 'y.txt'}", "stdout")))
    buf = io.StringIO()
    logp = roots.logs / "apparatus.log"
    allow.add_exact(logp)
    em = PW.Emitter(allow, stream=buf, log_path=logp)
    em.say("fetch_extract: apparatus gate ungated open")
    try:
        em.say("fetch_extract: apparatus sheet " + IDS["bids"])
        raised = False
    except PW.PrintRuleViolation as e:
        raised = str(e) == "stdout"
    ok(P, "emitter: a failing line raises PrintRuleViolation (no text) and is written nowhere",
       raised and IDS["bids"] not in buf.getvalue() and IDS["bids"] not in logp.read_text(encoding="utf-8")
       and em.n_violations == 1)
    try:
        em.save_bytes(roots.data / ("member_" + IDS["bids"] + ".xlsx"), b"x")
        fn_ok = False
    except PW.PrintRuleViolation:
        fn_ok = True
    ok(P, "emitter: a carrier-derived file name is refused before writing",
       fn_ok and not (roots.data / ("member_" + IDS["bids"] + ".xlsx")).exists())
    try:
        em.write_json(roots.records / "apparatus.json", {"key": "apparatus", "label": IDS["nda_guid"]})
        rec_ok = False
    except PW.PrintRuleViolation:
        rec_ok = True
    ok(P, "emitter: a record holding a carrier string is refused before writing",
       rec_ok and not (roots.records / "apparatus.json").exists())
    # the stage handler: message, traceback and locals suppressed; no chained original exception
    buf2 = io.StringIO()
    em2 = PW.Emitter(allow, stream=buf2)

    def boom():
        secret = IDS["spark"]           # noqa: F841 - a local value that must not be printed
        float(IDS["nda_guid"])
    try:
        PW.stage(em2, "read:numeric-columns", boom)
        sf = None
    except PW.StageFailed as e:
        sf = e
    line = buf2.getvalue().strip()
    ok(P, "handler: 'ValueError at <stage>, <file>:<line>' and nothing else",
       re.fullmatch(r"ValueError at read:numeric-columns, test_material_p18_p19_p20\.py:\d+|"
                    r"ValueError at read:numeric-columns, fetch_extract\.py:0", line) is not None or
       re.fullmatch(r"ValueError at read:numeric-columns, [a-z_]+\.py:\d+", line) is not None, line[:80])
    ok(P, "handler: the StageFailed carries no __context__ / __cause__ (the original message is not chained)",
       sf is not None and sf.__context__ is None and sf.__cause__ is None and IDS["nda_guid"] not in str(sf)
       and IDS["spark"] not in line)
    # a guard Refused (a SystemExit) is caught by the handler, its message (naming the sheet) never printed
    buf3 = io.StringIO()
    em3 = PW.Emitter(allow, stream=buf3)

    def guard_refusal():
        raise FE.PG.Refused("REFUSED: plant sheet '%s' is identifier-bearing" % IDS["bids"])
    try:
        PW.stage(em3, "read:declared-columns", guard_refusal)
    except PW.StageFailed:
        pass
    ok(P, "handler: a guard Refused (SystemExit) prints class, stage, line only",
       re.fullmatch(r"Refused at read:declared-columns, [a-z_0-9]+\.py:\d+\n", buf3.getvalue()) is not None and
       IDS["bids"] not in buf3.getvalue())
    # StdioGuard: xlrd with its default logfile (stdout) and verbosity 2 prints sheet names -> dropped and counted
    sheets, _, _, _ = wnv_book("sg", np.random.default_rng(3))
    px = RUN / "stdio_plant.xls"
    write_xls(px, [(n, r, False) for n, r, _ in sheets[:3]])
    import xlrd
    out = io.StringIO()
    with PW.StdioGuard(allow, out=out, err=out) as sg:
        b = xlrd.open_workbook(str(px), on_demand=True, verbosity=2, logfile=sys.stdout)   # sys.stdout = the guard
        b.release_resources()
    ok(P, "stdio guard: xlrd's own sheet-name print (default logfile, verbosity 2) dropped and counted",
       sg.violations > 0 and not any(n in out.getvalue() for n, _, _ in sheets))
    # screen(): counts per letter, in memory
    s1 = PW.screen("a/" + IDS["bids"] + "/b.xlsx", FE.PG)
    s2 = PW.screen("Sample IDs.csv", FE.PG)
    s3 = PW.screen("freesurfer/subjects/fsaverage/label/lh.aparc.annot", FE.PG)
    s4 = PW.screen("QxPlainName.xlsx", FE.PG)
    ok(P, "screen: V for an identifier-shaped component, N for identifier wording / a bare subject word, none clean",
       s1["V"] >= 1 and s2["N"] >= 1 and s3["N"] >= 1 and s4 == {"V": 0, "N": 0})
    # criterion (i)'s own search catches a planted leak (so a clean result is informative)
    C = Carrier()
    C.add("planted_id", IDS["tcga"])
    QUIET["on"] = True
    try:
        leak_found = not criterion_i({"stdout": "x " + json.dumps(IDS["tcga"])}, C, None, None, "P20-selfcheck", "leak")
    finally:
        QUIET["on"] = False
    RESULTS.pop("P20-selfcheck", None)
    FAILS[:] = [f for f in FAILS if not f.startswith("P20-selfcheck")]
    ok(P, "criterion (i): its search catches a planted leak (JSON-escaped form included)", leak_found)


def p20_workbook(ext: str):
    P = "P20"
    tag = "x" + ext.strip(".")
    print(f"\nP20 {ext} workbook with W / N / V sheets (declared columns; undeclared sheets, one corrupt)")
    sheets, decls, C, expect = wnv_book(tag, np.random.default_rng(20 if ext == ".xlsx" else 21))
    p = RUN / f"wnv{ext}"
    (write_xlsx if ext == ".xlsx" else write_xls)(p, sheets)
    data = p.read_bytes()
    url = serve(f"p20/wnv{ext}", data)
    t = FE.Target(key=f"wnv{tag}", gate="ungated", url=url, kind="workbook", ext=ext, pinned_bytes=len(data),
                  pinned_sha256=hashlib.sha256(data).hexdigest(), sheets=tuple(decls))
    roots = make_roots(f"p20_wnv_{tag}")
    res, so, se = run_captured(t, roots)
    rec = record_of(res)
    step5, s5p = load_step5(res)
    sub = f"{ext} W/N/V"
    ok(P, sub + ": extracted", res["status"] == FE.STATUS_EXTRACTED, res["status"])
    texts = emitted_texts(roots, so, se, {s5p} if s5p else set())
    criterion_i(texts, C, step5, expect, P, sub)
    criterion_ii(texts, test_allow([t], roots), P, sub)
    runner_names_ok(roots, {t.key}, P, sub)
    sh = rec.get("sheets", {})
    names = [n for n, _, _ in sheets]
    ok(P, sub + ": declared sheets reported as match counts plus name sha256s",
       sh.get("declared_found") == 3 and sh.get("n_declared") == 3 and sh.get("n_undeclared") == len(names) - 3 and
       sh.get("name_sha256") == [hashlib.sha256(n.encode("utf-8")).hexdigest() for n in names])
    rules = {d["sheet_key"]: d["rules"] for d in sh.get("declared", [])}
    ok(P, sub + ": declared sheets classified by the frozen guard (W, N, V letters)",
       "W" in rules.get(f"wide_{tag}", "") and "N" in rules.get(f"sample_{tag}", "") and
       "V" in rules.get(f"value_{tag}", ""), json.dumps(rules))
    ok(P, sub + ": access log holds declared sheets only; no undeclared sheet touched",
       sh.get("access_log") == [hashlib.sha256(d.name.encode("utf-8")).hexdigest() for d in decls] and
       sh.get("access_log_declared_only") is True and
       (sh.get("parts_opened_undeclared") == 0 if ext == ".xlsx" else sh.get("sheets_loaded_undeclared") == 0))
    if ext == ".xlsx":
        import openpyxl
        try:
            openpyxl.load_workbook(str(p), read_only=True)
            raises = False
        except Exception:  # noqa: BLE001
            raises = True
        ok(P, sub + ": control: the corrupt undeclared part raises when openpyxl's plain read-only load parses it "
           "(FE1: the wrapper's deferred load never touched it)", raises)
    else:
        import xlrd
        try:
            xlrd.open_workbook(str(p), on_demand=False, logfile=PW.Sink())
            raises = False
        except Exception:  # noqa: BLE001
            raises = True
        ok(P, sub + ": control: the corrupt undeclared sheet raises when xlrd loads every sheet (on_demand=False); "
           "the wrapper opened with on_demand=True and loaded declared sheets only", raises and
           sh.get("xlrd_log_writes") is not None)
    q = rec.get("quarantine", {})
    qfiles = q.get("quarantined", [])
    ok(P, sub + ": identifier-bearing carrier quarantined (same volume rename, sha256 re-checked), deletion "
       "request written", len(qfiles) == 1 and qfiles[0]["sha256"] == hashlib.sha256(data).hexdigest() and
       Path(qfiles[0]["moved_to"]).exists() and not (roots.data / t.key / f"carrier{ext}").exists() and
       Path(q.get("deletion_request", "")).exists())
    return t, roots


def p20_cases():
    P = "P20"
    print("\nP20 sub-cases: do-not-open, non-numeric code, guard refusal, quarantine refusal, re-run")
    rng = np.random.default_rng(22)
    # do-not-open sheet declared by mistake: refused before the workbook is opened
    sheets, decls, C, _ = wnv_book("dno", rng)
    sheets = sheets + [("5_BIV", [["QxDnoHeader", IDS["bids"] + "dno"]], True)]
    C.add("sheet_name", "5_BIV")
    C.add("undeclared_cell_id", "QxDnoHeader", IDS["bids"] + "dno")
    p = RUN / "dno.xlsx"
    write_xlsx(p, sheets)
    data = p.read_bytes()
    bad_decl = decls[:1] + [FE.SheetDecl(key="dno_sheet", name="5_BIV", header_row=0,
                                         columns=(FE.Column("QxDnoHeader", "x"),))]
    t = FE.Target(key="dnotarget", gate="ungated", url=serve("p20/dno.xlsx", data), kind="workbook", ext=".xlsx",
                  pinned_sha256=hashlib.sha256(data).hexdigest(), sheets=tuple(bad_decl),
                  do_not_open=FE.MOREAU_DO_NOT_OPEN)
    roots = make_roots("p20_dno")
    res, so, se = run_captured(t, roots)
    rec = record_of(res)
    ok(P, "do-not-open sheet declared by mistake: refused, workbook never opened (no sheets record)",
       res["status"] == FE.STATUS_DO_NOT_OPEN and "sheets" not in rec and
       re.search(r"^DoNotOpen at sheets:do-not-open, fetch_extract\.py:\d+$", so, re.M) is not None)
    texts = emitted_texts(roots, so, se, set())
    criterion_i(texts, C, None, None, P, "do-not-open")
    criterion_ii(texts, test_allow([t], roots), P, "do-not-open")
    # WP2 review C9: the do-not-open names are compared casefolded and stripped (case and whitespace variants of a
    # do-not-open name declared by mistake are refused before the workbook is opened)
    for j, variant in enumerate((" 5_biv", "5_Biv\t", " 5_BIV")):
        decl_v = decls[:1] + [FE.SheetDecl(key="dno_sheet", name=variant, header_row=0,
                                           columns=(FE.Column("QxDnoHeader", "x"),))]
        tv = FE.Target(key=f"dnovariant{j}", gate="ungated", url=serve(f"p20/dno_v{j}.xlsx", data), kind="workbook",
                       ext=".xlsx", pinned_sha256=hashlib.sha256(data).hexdigest(), sheets=tuple(decl_v),
                       do_not_open=FE.MOREAU_DO_NOT_OPEN)
        rv_roots = make_roots(f"p20_dno_v{j}")
        rv, sov, sev = run_captured(tv, rv_roots)
        ok(P, f"do-not-open sheet declared with another case / surrounding whitespace (variant {j}): refused, "
           "workbook never opened (C9)",
           rv["status"] == FE.STATUS_DO_NOT_OPEN and "sheets" not in record_of(rv) and
           re.search(r"^DoNotOpen at sheets:do-not-open, fetch_extract\.py:\d+$", sov, re.M) is not None)
        criterion_ii(emitted_texts(rv_roots, sov, sev, set()), test_allow([tv], rv_roots), P,
                     f"do-not-open variant {j}")

    # a non-numeric code in a declared numeric column
    sheets, decls, C, _ = wnv_book("nnc", rng)
    name, rows, c = sheets[0]
    rows = [list(r) for r in rows]
    planted = IDS["nda_guid2"] + "nnc"
    rows[3][1] = planted
    C.add("planted_in_numeric", planted)
    sheets[0] = (name, rows, c)
    p = RUN / "nnc.xlsx"
    write_xlsx(p, sheets)
    data = p.read_bytes()
    t = FE.Target(key="nnctarget", gate="ungated", url=serve("p20/nnc.xlsx", data), kind="workbook", ext=".xlsx",
                  pinned_sha256=hashlib.sha256(data).hexdigest(), sheets=tuple(decls))
    roots = make_roots("p20_nnc")
    res, so, se = run_captured(t, roots)
    lines = [ln for ln in so.split("\n") if " at " in ln and not ln.startswith("fetch_extract:")]
    ok(P, "non-numeric code in a declared numeric column: 'ValueError at read:numeric-columns, "
       "fetch_extract.py:<line>' and nothing else; no object saved",
       len(lines) == 1 and re.fullmatch(r"ValueError at read:numeric-columns, fetch_extract\.py:\d+", lines[0]) is not None
       and res["status"] == FE.STATUS_FAILED and load_step5(res)[0] is None, lines[0][:80] if lines else "")
    texts = emitted_texts(roots, so, se, set())
    criterion_i(texts, C, None, None, P, "non-numeric code")
    criterion_ii(texts, test_allow([t], roots), P, "non-numeric code")

    # a guard refusal: a W sheet read with its header row outside the guard's zone
    sheets, decls, C, _ = wnv_book("grf", rng)
    p = RUN / "grf.xlsx"
    write_xlsx(p, sheets)
    data = p.read_bytes()
    d0 = decls[0]
    bad = FE.SheetDecl(key=d0.key, name=d0.name, header_row=25, columns=d0.columns)
    t = FE.Target(key="grftarget", gate="ungated", url=serve("p20/grf.xlsx", data), kind="workbook", ext=".xlsx",
                  pinned_sha256=hashlib.sha256(data).hexdigest(), sheets=(bad,))
    roots = make_roots("p20_grf")
    res, so, se = run_captured(t, roots)
    ok(P, "guard refusal: 'Refused at read:declared-columns, privacy_guard.py:<line>'; the guard's message (naming "
       "the sheet) never appears", re.search(r"^Refused at read:declared-columns, privacy_guard\.py:\d+$", so, re.M)
       is not None and "REFUSED" not in so and res["status"] == FE.STATUS_FAILED)
    texts = emitted_texts(roots, so, se, set())
    criterion_i(texts, C, None, None, P, "guard refusal")
    criterion_ii(texts, test_allow([t], roots), P, "guard refusal")

    # quarantine: cross-volume move refused (never copy + delete); re-run of a quarantined carrier refused
    sheets, decls, C, _ = wnv_book("qvo", rng)
    p = RUN / "qvo.xlsx"
    write_xlsx(p, sheets)
    data = p.read_bytes()
    t = FE.Target(key="qvotarget", gate="ungated", url=serve("p20/qvo.xlsx", data), kind="workbook", ext=".xlsx",
                  pinned_sha256=hashlib.sha256(data).hexdigest(), sheets=tuple(decls))
    roots = make_roots("p20_qvo")
    saved = FE._same_volume
    FE._same_volume = lambda a, b: False
    try:
        res, so, se = run_captured(t, roots)
    finally:
        FE._same_volume = saved
    ok(P, "quarantine: a move that is not a same-volume rename is refused; the carrier stays, nothing copied",
       res["status"] == FE.STATUS_FAILED and (roots.data / t.key / "carrier.xlsx").exists() and
       not (roots.quarantine / "ungated" / t.key / "carrier.xlsx").exists() and
       re.search(r"^QuarantineRefused at quarantine, fetch_extract\.py:\d+$", so, re.M) is not None)
    roots2 = make_roots("p20_qrerun")
    r1, _, _ = run_captured(t, roots2)
    r2, so2, _ = run_captured(t, roots2)
    ok(P, "quarantine: a re-run refuses (carrier in quarantine; the operator moves it back)",
       r1["status"] == FE.STATUS_EXTRACTED and r2["status"] == FE.STATUS_IN_QUARANTINE)
    refused = 0
    for pth in (roots2.quarantine / "ungated" / t.key / "carrier.xlsx", Path("E_x/_QUARANTINE/k/f.xlsx")):
        try:
            FE.refuse_quarantine_path(pth, roots2.quarantine)
        except PermissionError:
            refused += 1
    ok(P, "the runner's path check refuses any path under _quarantine", refused == 2)
    try:
        FE.refuse_quarantine_path(roots2.data / t.key / "carrier.xlsx", roots2.quarantine)
        passes = True
    except PermissionError:
        passes = False
    ok(P, "the path check passes a path outside _quarantine", passes)

    # planted failures the post-read assertions must catch: an undeclared sheet touched behind the accessor's back
    for ext in (".xlsx", ".xls"):
        tag = "pt" + ext[1:]
        sheets, decls, C, _ = wnv_book(tag, rng)
        sheets = [(n, r, False) for n, r, _ in sheets]
        p = RUN / f"planted_touch{ext}"
        (write_xlsx if ext == ".xlsx" else write_xls)(p, sheets)
        data = p.read_bytes()
        t = FE.Target(key=f"touch{tag}", gate="ungated", url=serve(f"p20/touch{ext}", data), kind="workbook", ext=ext,
                      pinned_sha256=hashlib.sha256(data).hexdigest(), sheets=tuple(decls))
        orig_fetch = FE._Book.fetch

        def touching_fetch(self, name, declared, _o=orig_fetch):
            sh = _o(self, name, declared)
            und = [n for n in self.names if n not in declared][0]
            if self.ext == ".xlsx":
                self.wb[und].a1_materialise()          # opens the undeclared sheet's part
            else:
                self.book.sheet_by_name(und)           # loads the undeclared sheet
            return sh
        FE._Book.fetch = touching_fetch
        try:
            roots = make_roots(f"p20_touch_{tag}")
            res, so, se = run_captured(t, roots)
        finally:
            FE._Book.fetch = orig_fetch
        ok(P, f"planted: an undeclared sheet touched behind the accessor ({ext}) is caught by the post-read assertion "
           f"(AssertionError at sheets:access-log); nothing saved", res["status"] == FE.STATUS_FAILED and
           re.search(r"^AssertionError at sheets:access-log, fetch_extract\.py:\d+$", so, re.M) is not None and
           load_step5(res)[0] is None)
        texts = emitted_texts(roots, so, se, set())
        criterion_i(texts, C, None, None, P, f"planted touch {ext}")
    # planted: an undeclared zip member opened -> caught
    sheets, decls, C, _ = wnv_book("pz", rng)
    bz = RUN / "pz.xlsx"
    write_xlsx(bz, sheets)
    zp = RUN / "planted.zip"
    with zipfile.ZipFile(zp, "w") as z:
        z.write(bz, "QxDir/QxDeclared.xlsx")
        z.writestr("QxDir/" + IDS["bids"] + ".csv", b"x")
    data = zp.read_bytes()
    t = FE.Target(key="touchzip", gate="ungated", url=serve("p20/planted.zip", data), kind="zip", ext=".zip",
                  pinned_sha256=hashlib.sha256(data).hexdigest(),
                  members=(FE.MemberDecl(key="m", match="QxDir/QxDeclared.xlsx", ext=".xlsx", kind="workbook",
                                         sheets=tuple(decls)),))
    orig_il = FE._AuditZipFile.infolist

    def touching_infolist(self, _o=orig_il):
        infos = _o(self)
        with self.open(infos[1]) as f:            # the undeclared member
            f.read(1)
        return infos
    FE._AuditZipFile.infolist = touching_infolist
    try:
        roots = make_roots("p20_touch_zip")
        res, so, se = run_captured(t, roots)
    finally:
        FE._AuditZipFile.infolist = orig_il
    ok(P, "planted: an undeclared zip member read is caught (AssertionError at zip:members)",
       res["status"] == FE.STATUS_FAILED and re.search(r"^AssertionError at zip:members, fetch_extract\.py:\d+$", so,
                                                       re.M) is not None)
    # a declared sheet absent from the workbook -> refused
    sheets, decls, C, _ = wnv_book("abs", rng)
    p = RUN / "absent.xlsx"
    write_xlsx(p, sheets)
    data = p.read_bytes()
    t = FE.Target(key="absentsheet", gate="ungated", url=serve("p20/absent.xlsx", data), kind="workbook", ext=".xlsx",
                  pinned_sha256=hashlib.sha256(data).hexdigest(),
                  sheets=tuple(decls) + (FE.SheetDecl(key="ghost", name="QxGhostSheet", header_row=0,
                                                      columns=(FE.Column("QxH", "h"),)),))
    roots = make_roots("p20_absent")
    res, so, se = run_captured(t, roots)
    ok(P, "a declared sheet absent from the workbook: refused (LayoutRefused at sheets:names); no sheet fetched",
       res["status"] == FE.STATUS_FAILED and re.search(r"^LayoutRefused at sheets:names, fetch_extract\.py:\d+$", so,
                                                       re.M) is not None and
       record_of(res).get("sheets", {}).get("access_log") is None)


def p20_moreau():
    P = "P20"
    print("\nP20 Moreau-like 64 x 64 sheets through the header-row search (section 8 step 4)")
    rng = np.random.default_rng(64)
    voc = mist_vocab_synth()
    rule = FE.Mist64Rule(voc)
    # the real vocabulary loader (register_maps/mist64_classes.json, sha256 pinned): the plan's counted facts
    real = FE.mist64_vocab()
    ok(P, "mist64_classes.json loader: 64 parcels, roi 1..64, labels / names distinct casefolded, disjoint "
       "(counts only)", len(real) == 64)
    sA, CA, bA = moreau_sheet(voc, "label", rng, title_rows=2)
    sB, CB, bB = moreau_sheet(voc, "roi", rng, title_rows=0)
    sheets = [(FE.MOREAU_SHEETS[0], sA, False), ("QxNotesSheet", [["QxNotes " + IDS["geo"]]], False),
              (FE.MOREAU_SHEETS[1], sB, False)]
    C = Carrier()
    for cc in (CA, CB):
        for fam, s in cc.all():
            C.add(fam, s)
    for n in FE.MOREAU_DO_NOT_OPEN:
        sheets.append((n, [["QxAbide header " + n, IDS["bids"] + n[:1]], [IDS["nda_guid"], 1.0]], True))
        C.add("undeclared_cell_id", "QxAbide header " + n, IDS["bids"] + n[:1])
    for n, _, _ in sheets:
        C.add("sheet_name", n)
    C.add("undeclared_cell_id", "QxNotes " + IDS["geo"])
    for s in IDS.values():
        C.add("planted_id", s)
    p = RUN / "moreau_like.xlsx"
    write_xlsx(p, sheets)
    data = p.read_bytes()
    t = FE.moreau_target(serve("p20/moreau_like.xlsx", data), vocab=voc, key="moreaulike",
                         pinned_sha256=hashlib.sha256(data).hexdigest())
    roots = make_roots("p20_moreau")
    res, so, se = run_captured(t, roots)
    rec = record_of(res)
    step5, s5p = load_step5(res)
    labels = [lab for _, lab, _ in voc]
    expect = {"del16p11": {"ids": list(range(1, 65)), "labels": labels, "values": bA.tolist()},
              "del22q11": {"ids": list(range(1, 65)), "labels": labels, "values": bB.tolist()}}
    ok(P, "Moreau-like: extracted (label form with a mixed-case label row; roi row of floats)",
       res["status"] == FE.STATUS_EXTRACTED, res["status"])
    dec = {d["sheet_key"]: d for d in rec.get("sheets", {}).get("declared", [])}
    ok(P, "Moreau-like: header row found by the search (rows tried 4 and 1), forms label / roi, 4,096 numeric cells, "
       "rule W", dec.get("del16p11", {}).get("header_rows_tried") == 4 and dec.get("del16p11", {}).get("form") ==
       "label" and dec.get("del22q11", {}).get("header_rows_tried") == 1 and dec.get("del22q11", {}).get("form") ==
       "roi" and all(d.get("block_cells_numeric") == 4096 and "W" in d.get("rules", "") for d in dec.values()))
    ok(P, "Moreau-like: do-not-open sheets (parts raise if parsed) never touched; access log declared only",
       rec.get("sheets", {}).get("parts_opened_undeclared") == 0 and rec.get("sheets", {}).get(
           "access_log_declared_only") is True)
    texts = emitted_texts(roots, so, se, {s5p} if s5p else set())
    criterion_i(texts, C, step5, expect, P, "Moreau-like")
    criterion_ii(texts, test_allow([t], roots), P, "Moreau-like")

    # name form; text-digit rows; no corner label
    sC, CC, bC = moreau_sheet(voc, "name", rng, title_rows=1, corner=False)
    ws_rows = sC
    pad = max(len(r) for r in ws_rows)
    rows = [list(r) + [None] * (pad - len(r)) for r in ws_rows]
    h = next(i for i, r in enumerate(rows) if rule(r))
    blk = FE._mist64_block(rows, h, rule)
    ok(P, "Moreau-like: name form without a corner label read; block equals the planted one",
       blk["form"] == "name" and np.array_equal(np.array(blk["object"]["values"]), bC))

    # the column rule's refusals (each must return [] / raise LayoutRefused)
    base_rows, _, _ = moreau_sheet(voc, "label", np.random.default_rng(5), title_rows=0, perturb=False)
    hdr = list(base_rows[0])
    cases = {}
    x = hdr[:]
    x[10] = None
    cases["an identifier missing"] = x
    x = hdr[:]
    x[11] = x[12]
    cases["an identifier twice"] = x
    x = hdr[:] + ["QxExtra", "QxExtra2"]
    cases["two other non-empty cells"] = x
    x = [None] + hdr[1:] + ["QxCornerFar"]
    x[0] = None
    cases["the one other cell not in the row-label column"] = x
    x = hdr[1:]
    cases["no row-label column (leftmost at column 0)"] = x
    x = [hdr[0]] + [h_.upper() if isinstance(h_, str) else h_ for h_ in hdr[1:33]] + \
        [str(k) for k in range(33, 65)]
    cases["mixed forms"] = x
    x = [hdr[0]] + [True] * 64
    cases["booleans are not roi"] = x
    n_ref = sum(1 for v in cases.values() if rule(v) == [])
    ok(P, f"column rule refuses ({len(cases)} cases)", n_ref == len(cases), f"{n_ref}/{len(cases)}")
    ok(P, "column rule accepts the exact, mixed-case, roi-int, roi-float and roi-text-digit forms",
       len(rule(hdr)) == 65 and len(rule([hdr[0]] + [h_.swapcase() for h_ in hdr[1:]])) == 65 and
       len(rule([None] + list(range(1, 65)))) == 65 and len(rule([None] + [float(k) for k in range(64, 0, -1)])) == 65
       and len(rule([None] + [f" {k} " for k in range(1, 65)])) == 65)
    # block refusals
    rows0 = [list(r) for r in base_rows[:65]]
    variants_ = {}
    r1 = [list(r) for r in rows0]
    r1[5][7] = "QxText"
    variants_["a non-numeric block cell"] = r1
    r2 = [list(r) for r in rows0]
    r2[6][0] = r2[7][0]
    variants_["a row label twice"] = r2
    r3 = [list(r) for r in rows0]
    r3[8][0] = "8"
    variants_["a row label in another form"] = r3
    variants_["63 rows only"] = [list(r) for r in rows0[:64]]
    r5 = [list(r) for r in rows0]
    r5[9][3] = True
    variants_["a boolean block cell"] = r5
    n_bref = 0
    for v in variants_.values():
        try:
            FE._mist64_block(v, 0, rule)
        except FE.LayoutRefused:
            n_bref += 1
    ok(P, f"post-read assertions refuse ({len(variants_)} cases)", n_bref == len(variants_), f"{n_bref}/{len(variants_)}")

    # through the wrapper: a non-numeric block cell and a header below row 20 -> Moreau's status
    for nm, kw in (("a non-numeric block cell", {"bad": "nonnumeric", "title_rows": 1}),
                   ("the header row below the guard's 20 rows", {"title_rows": 21})):
        sX, CX, _ = moreau_sheet(voc, "label", rng, **kw)
        sY, CY, _ = moreau_sheet(voc, "roi", rng, title_rows=0)
        px = RUN / f"moreau_bad_{len(nm)}.xlsx"
        write_xlsx(px, [(FE.MOREAU_SHEETS[0], sX, False), (FE.MOREAU_SHEETS[1], sY, False)])
        dx = px.read_bytes()
        tx = FE.moreau_target(serve(f"p20/mbad{len(nm)}.xlsx", dx), vocab=voc, key=f"moreaubad{len(nm)}",
                              pinned_sha256=hashlib.sha256(dx).hexdigest())
        rx = make_roots(f"p20_moreau_bad{len(nm)}")
        res, so, se = run_captured(tx, rx)
        ok(P, f"Moreau-like through the wrapper, {nm}: '{FE.MOREAU_LAYOUT[:40]}...'; no object saved",
           res["status"] == FE.MOREAU_LAYOUT and load_step5(res)[0] is None, res["status"])
        Cx = Carrier()
        for cc in (CX, CY):
            for fam, s in cc.all():
                Cx.add(fam, s)
        texts = emitted_texts(rx, so, se, set())
        criterion_i(texts, Cx, None, None, P, f"Moreau-like refusal ({nm})")
        criterion_ii(texts, test_allow([tx], rx), P, f"Moreau-like refusal ({nm})")


def p20_zip():
    P = "P20"
    print("\nP20 zip carrier: declared members (xlsx, xls) extracted under runner-built names; undeclared never read")
    rng = np.random.default_rng(23)
    sh1, de1, C1, ex1 = wnv_book("za", rng)
    sh2, de2, C2, ex2 = wnv_book("zb", rng)
    b1, b2 = RUN / "za.xlsx", RUN / "zb.xls"
    write_xlsx(b1, sh1)
    write_xls(b2, sh2)
    C = Carrier()
    for cc in (C1, C2):
        for fam, s in cc.all():
            C.add(fam, s)
        C.declared_values |= cc.declared_values
    m_names = {"decl_xlsx": f"QxTables/QxSupp_{IDS['bids']}_tables.xlsx",
               "decl_xls": "QxTables/QxSupp_moduletable.xls",
               "und1": f"QxTables/{IDS['nda_guid']}.csv", "und2": f"QxRaw/Sample IDs {IDS['spark']}.xlsx",
               "und3": "QxRaw/QxReadme.txt"}
    for v in m_names.values():
        C.add("member_name", v)
        for comp in v.split("/"):
            C.add("member_path_component", comp)
    zp = RUN / "carrier.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("QxTables/", b"")
        z.writestr(m_names["und1"], ("id,x\n" + IDS["nda_guid"] + ",1\n").encode())
        z.write(b1, m_names["decl_xlsx"])
        z.writestr(m_names["und2"], b"PK-not-really")
        z.write(b2, m_names["decl_xls"])
        z.writestr(m_names["und3"], b"QxReadme " + IDS["ssc"].encode())
    C.add("undeclared_cell_id", "id,x", "QxReadme " + IDS["ssc"])
    data = zp.read_bytes()
    t = FE.Target(key="zipcarrier", gate="ungated", url=serve("p20/carrier.zip", data), kind="zip", ext=".zip",
                  pinned_sha256=hashlib.sha256(data).hexdigest(),
                  members=(FE.MemberDecl(key="suppx", match=m_names["decl_xlsx"], ext=".xlsx", kind="workbook",
                                         sheets=tuple(de1)),
                           FE.MemberDecl(key="suppl", match="QxSupp_moduletable.xls", how="suffix", ext=".xls",
                                         kind="workbook", sheets=tuple(de2))))
    roots = make_roots("p20_zip")
    res, so, se = run_captured(t, roots)
    rec = record_of(res)
    step5, s5p = load_step5(res)
    ok(P, "zip: extracted; 2 declared members saved as <key>_member<index><ext>",
       res["status"] == FE.STATUS_EXTRACTED and [m["saved_path"].split("/")[-1] for m in rec.get("zip", {})
                                                  .get("members", [])] == ["zipcarrier_member2.xlsx",
                                                                           "zipcarrier_member4.xls"])
    ok(P, "zip: undeclared members never read (the zip's opens hold declared members only)",
       rec.get("zip", {}).get("undeclared_members_read") == 0 and rec.get("zip", {}).get("n_members") == 6)
    texts = emitted_texts(roots, so, se, {s5p} if s5p else set())
    criterion_i(texts, C, step5, {"suppx": ex1, "suppl": ex2}, P, "zip")
    criterion_ii(texts, test_allow([t], roots), P, "zip")
    runner_names_ok(roots, {t.key}, P, "zip")
    q = rec.get("quarantine", {}).get("quarantined", [])
    ok(P, "zip: the carrier and both identifier-bearing extracted members quarantined",
       sorted(Path(m["moved_to"]).name for m in q) == ["carrier.zip", "zipcarrier_member2.xlsx",
                                                       "zipcarrier_member4.xls"])


# ---- tar streams (R16) -----------------------------------------------------------------------------------------
def synth_annot(path: Path, n_vert: int, names: list[str], rng) -> np.ndarray:
    from nibabel.freesurfer import io as fsio
    labels = rng.integers(0, len(names), size=n_vert).astype(np.int32)
    ctab = np.zeros((len(names), 5), dtype=np.int32)
    for i in range(len(names)):
        ctab[i, :3] = [(i * 37) % 256, (i * 91) % 256, (i * 53 + 1) % 256]
    fsio.write_annot(str(path), labels, ctab, names, fill_ctab=True)
    return labels


def _tar_add(tf, name, data=None, kind="reg", link=None):
    ti = tarfile.TarInfo(name)
    ti.mtime = 1687860000
    if kind == "reg":
        ti.size = len(data)
        tf.addfile(ti, io.BytesIO(data))
        return
    ti.type = {"sym": tarfile.SYMTYPE, "lnk": tarfile.LNKTYPE, "dir": tarfile.DIRTYPE, "fifo": tarfile.FIFOTYPE}[kind]
    if link is not None:
        ti.linkname = link
    tf.addfile(ti)


def build_tar(path: Path, annot: bytes, variant: str, wnv: list[tuple[str, bytes]]):
    decl = "fs/subjects/fsaverage/label/lh.aparc.annot"
    with tarfile.open(path, "w:gz") as tf:
        _tar_add(tf, "fs/README", b"QxFreeSurfer synthetic readme")
        for nm, b in wnv:
            _tar_add(tf, nm, b)
        _tar_add(tf, f"fs/subjects/{IDS['bids']}/label/lh.aparc.annot", b"QxOtherSubject")
        _tar_add(tf, "fs/data/annot_real", annot)
        _tar_add(tf, "fs/data/dir_member", kind="dir")
        _tar_add(tf, "fs/data/link_to_real", kind="sym", link="annot_real")
        if variant == "regular":
            _tar_add(tf, decl, annot)
        elif variant == "symlink":
            _tar_add(tf, decl, kind="sym", link="../../../data/annot_real")
        elif variant == "hardlink":
            _tar_add(tf, decl, kind="lnk", link="fs/data/annot_real")
        elif variant == "absent":
            _tar_add(tf, decl, kind="sym", link="../../../data/no_such_member")
        elif variant == "outside":
            _tar_add(tf, decl, kind="sym", link="../../../../../../" + "QxOutside/file")
        elif variant == "absolute":
            _tar_add(tf, decl, kind="sym", link="/QxAbs/file")
        elif variant == "to_dir":
            _tar_add(tf, decl, kind="sym", link="../../../data/dir_member")
        elif variant == "chain":
            _tar_add(tf, decl, kind="sym", link="../../../data/link_to_real")
        elif variant == "fifo":
            _tar_add(tf, decl, kind="fifo")
        elif variant == "dir":
            _tar_add(tf, decl, kind="dir")
        elif variant == "missing":
            pass
        _tar_add(tf, "fs/subjects/fsaverage/label/rh.aparc.annot", b"QxRight")


def p20_tar():
    P = "P20"
    print("\nP20 tar stream (R16): declared member by path ending; links resolved or refused; W/N/V members streamed past")
    rng = np.random.default_rng(16)
    names = ["unknown"] + [f"qxdk{k:02d}" for k in range(34)] + ["corpuscallosum"]
    ap_ = RUN / "synthetic.annot"
    synth_annot(ap_, 400, names, rng)
    annot = ap_.read_bytes()
    sh, _, C0, _ = wnv_book("tr", rng)
    wb = RUN / "tar_member.xlsx"
    write_xlsx(wb, sh)
    wnv = [(f"fs/docs/QxTable_{IDS['nda_guid']}.xlsx", wb.read_bytes())]
    C = Carrier()
    for fam, s in C0.all():
        C.add(fam, s)
    for nm in ("fs/README", wnv[0][0], f"fs/subjects/{IDS['bids']}/label/lh.aparc.annot", "fs/data/annot_real",
               "fs/data/dir_member", "fs/data/link_to_real", "fs/subjects/fsaverage/label/lh.aparc.annot",
               "fs/subjects/fsaverage/label/rh.aparc.annot", "QxFreeSurfer synthetic readme", "QxOtherSubject",
               "../../../data/annot_real", "QxOutside/file", "/QxAbs/file", "QxRight"):
        C.add("tar_member_name", nm)
        for comp in nm.split("/"):
            if comp not in ("fs", "data", "label", "subjects", "..", "fsaverage", "lh.aparc.annot", "README"):
                C.add("tar_path_component", comp)
    expect = {"regular": (FE.STATUS_EXTRACTED, "regular", None, 1),
              "symlink": (FE.STATUS_EXTRACTED, "symbolic link", True, 2),
              "hardlink": (FE.STATUS_EXTRACTED, "hard link", True, 2),
              "absent": (RP.STATUS_FS_NOT_REGULAR, "symbolic link", False, 2),
              "outside": (RP.STATUS_FS_NOT_REGULAR, "symbolic link", False, 1),
              "absolute": (RP.STATUS_FS_NOT_REGULAR, "symbolic link", False, 1),
              "to_dir": (RP.STATUS_FS_NOT_REGULAR, "symbolic link", False, 2),
              "chain": (RP.STATUS_FS_NOT_REGULAR, "symbolic link", False, 2),
              "fifo": (RP.STATUS_FS_NOT_REGULAR, "other", None, 1),
              "dir": (RP.STATUS_FS_NOT_REGULAR, "other", None, 1),
              "missing": (RP.STATUS_FS_NOT_MATCHING, None, None, 1)}
    for variant, (st, mtype, resolved, passes) in expect.items():
        tp = RUN / f"fs_{variant}.tar.gz"
        build_tar(tp, annot, variant, wnv)
        data = tp.read_bytes()
        url = serve(f"p20/fs_{variant}.tar.gz", data)
        t = FE.Target(key=f"fs{variant.replace('_', '')}", gate="ungated", url=url, kind="tar_member", ext=".tar.gz",
                      pinned_bytes=len(data), identity_at_download=True,
                      members=(FE.MemberDecl(key="lh_aparc_annot", match=FE.R16_SUFFIX, how="suffix", ext=".annot",
                                             save_name=FE.R16_NAME),),
                      refusal_status=RP.STATUS_FS_NOT_REGULAR)
        roots = make_roots(f"p20_tar_{variant}")
        res, so, se = run_captured(t, roots)
        rec = record_of(res)
        tr = rec.get("tar", {})
        saved = roots.data / t.key / FE.R16_NAME
        good = res["status"] == st and tr.get("passes") == passes and tr.get("member_type") == mtype
        if st == FE.STATUS_EXTRACTED:
            good &= saved.exists() and saved.read_bytes() == annot and tr.get("saved_sha256") == \
                hashlib.sha256(annot).hexdigest() and tr.get("tarball_note") == FE.TARBALL_NOTE and \
                tr.get("member_path_sha256") == hashlib.sha256(
                    b"fs/subjects/fsaverage/label/lh.aparc.annot").hexdigest()
            if resolved:
                good &= tr.get("resolved") is True and tr.get("link_target_path_sha256") == hashlib.sha256(
                    b"fs/data/annot_real").hexdigest()
        else:
            good &= not saved.exists()
            if resolved is False:
                good &= tr.get("resolved") is False
        label = {"regular": "regular member taken", "symlink": "symbolic link to a regular member resolved by a "
                 "second pass (link type noted)", "hardlink": "hard link to a regular member resolved by a second pass",
                 "absent": "link target absent refused", "outside": "link target outside the archive (..) refused",
                 "absolute": "link target absolute (outside) refused", "to_dir": "link target not regular (directory) "
                 "refused", "chain": "link chain refused", "fifo": "other non-regular member (FIFO) refused",
                 "dir": "other non-regular member (directory) refused", "missing": "declared member absent: not "
                 "obtainable"}[variant]
        ok(P, f"tar: {label}", good, f"{res['status'][:40]} / {tr.get('passes')} / {tr.get('member_type')}")
        texts = emitted_texts(roots, so, se, set())
        criterion_i(texts, C, None, None, P, f"tar {variant}")
        criterion_ii(texts, test_allow([t], roots), P, f"tar {variant}")
    # size-only probe of the tarball (pinned bytes) refuses a changed size before streaming
    tp = RUN / "fs_regular.tar.gz"
    data = tp.read_bytes()
    t = FE.Target(key="fssizechanged", gate="ungated", url=serve("p20/fs_size.tar.gz", data), kind="tar_member",
                  ext=".tar.gz", pinned_bytes=len(data) + 1, identity_at_download=True,
                  members=(FE.MemberDecl(key="lh_aparc_annot", match=FE.R16_SUFFIX, how="suffix", ext=".annot",
                                         save_name=FE.R16_NAME),), refusal_status=RP.STATUS_FS_NOT_REGULAR)
    roots = make_roots("p20_tar_size")
    res, so, se = run_captured(t, roots)
    ok(P, "tar: size-only probe of the pinned tarball size refuses a changed size before streaming",
       res["status"] == RP.STATUS_FS_NOT_MATCHING and "bytes_streamed" not in record_of(res).get("tar", {}))
    # the R16 builder carries the plan's pins
    ft = FE.freesurfer_target()
    ok(P, "freesurfer_target(): pinned URL, 9,484,461,482 bytes, suffix, runner name, gate G2",
       ft.url == FE.R16_URL and ft.pinned_bytes == 9484461482 and ft.members[0].match ==
       "subjects/fsaverage/label/lh.aparc.annot" and ft.members[0].save_name == "lh.aparc.annot" and ft.gate == "G2")


def p20_subprocess():
    """The CLI in a separate process (process-level stdout / stderr captured), the guard's HGNC cache preset by a
    bootstrap (no production hook), the same tripwire installed in the child."""
    P = "P20"
    print("\nP20 the CLI in a subprocess (process-level stdout / stderr)")
    rng = np.random.default_rng(24)
    sheets, decls, C, expect = wnv_book("sp", rng)
    p = RUN / "sub.xls"
    write_xls(p, sheets)
    data = p.read_bytes()
    url = serve("p20/sub.xls", data)
    tj = {"targets": [{"key": "subproc", "gate": "ungated", "url": url, "kind": "workbook", "ext": ".xls",
                       "pinned_sha256": hashlib.sha256(data).hexdigest(),
                       "sheets": [{"key": d.key, "name": d.name, "header_row": d.header_row,
                                   "columns": [{"header": c.header, "key": c.key, "numeric": c.numeric}
                                               for c in d.columns]} for d in decls]}]}
    tdir = RUN / "subproc_inputs"
    tdir.mkdir()
    tpath = tdir / "targets.json"
    tpath.write_text(json.dumps(tj), encoding="utf-8")
    roots = make_roots("p20_subprocess")
    boot = (
        "import os, sys\n"
        "def hook(ev, a):\n"
        "    bad = ('e:\\\\data\\\\asdg', 'e:/data/asdg')\n"
        "    if ev in ('open', 'os.listdir', 'os.scandir') and a and isinstance(a[0], (str, bytes, os.PathLike)):\n"
        "        s = os.fsdecode(a[0]).lower()\n"
        "        if any(s.startswith(b) for b in bad): raise PermissionError('tripwire')\n"
        "    if ev == 'socket.connect' and (not isinstance(a[1], tuple) or a[1][0] not in ('127.0.0.1',)):\n"
        "        raise PermissionError('tripwire')\n"
        "sys.addaudithook(hook)\n"
        f"sys.path.insert(0, {str(SRC)!r})\n"
        "from a1_audit import fetch_extract as FE\n"
        f"FE.PG.HGNC_FILE = FE.Path({str(NO_HGNC)!r}); FE.PG._HGNC = frozenset({sorted(SYNTH_HGNC)!r})\n"
        "sys.exit(FE.main(sys.argv[1:]))\n")
    args = ["--targets", str(tpath), "--repo", str(REPO)]
    for r in ("data", "records", "artifacts", "logs", "control", "quarantine"):
        args += [f"--{r}-root", str(getattr(roots, r))]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC)
    pr = subprocess.run([sys.executable, "-X", "utf8", "-c", boot, *args], capture_output=True, env=env, timeout=600)
    so, se = pr.stdout.decode("utf-8", "replace"), pr.stderr.decode("utf-8", "replace")
    ok(P, "subprocess: exit 0, status extracted", pr.returncode == 0 and "status extracted" in so, str(pr.returncode))
    files = [p_ for p_ in all_files(roots) if p_.name.endswith("_extract.json")]
    step5 = json.loads(files[0].read_text(encoding="utf-8")) if files else None
    texts = emitted_texts(roots, so, se, set(files))
    ok(P, "subprocess: stderr empty", se == "")
    criterion_i(texts, C, step5, expect, P, "subprocess .xls")
    t = FE.targets_from_json(tpath)[0]
    criterion_ii(texts, test_allow([t], roots), P, "subprocess .xls")
    runner_names_ok(roots, {t.key}, P, "subprocess .xls")


# ================================================================================================================
# P18: re-parcellation
# ================================================================================================================
def inspect_src_of_port() -> str:
    """The '# ported from ...' line above reparcel.nn_resample_labels."""
    lines = Path(RP.__file__).read_text(encoding="utf-8").splitlines()
    i = next(k for k, ln in enumerate(lines) if ln.startswith("def nn_resample_labels("))
    if not lines[i - 1].startswith("# ported from arcs/replication/src/h_targets.py:"):
        raise AssertionError("port marker missing")
    return lines[i - 1]


def p18_r43():
    """RUN_PLAN_amend_2 R43's P18 cases (RP2 literal: a left DK cortical label holding more than 50 % of the source
    parcel's voxels, else dropped and reported; RP3: the weights are the source parcels' own voxel counts); the
    plurality variant (reparcel.py at 9addaab, blob 53d38374) must fail the 40 / 35 / 25 case."""
    P = "P18"

    def toy(parts):   # one source parcel (id 1) whose voxels fall in the given DK labels (0: outside every label)
        n = sum(k for _, k in parts)
        src = np.ones((n, 1, 1), dtype=np.int64)
        dkv = np.concatenate([np.full(k, lab, dtype=np.int64) for lab, k in parts]).reshape(n, 1, 1)
        return src, dkv
    cases = [("55 / 45 -> the 55 % label", [(201, 55), (202, 45)], 201, RP.REASON_ASSIGNED),
             ("40 / 35 / 25 -> dropped (no label above 50 %)", [(201, 40), (202, 35), (203, 25)], None,
              RP.REASON_NO_MAJORITY),
             ("50 / 50 -> dropped", [(201, 50), (202, 50)], None, RP.REASON_NO_MAJORITY),
             ("outside 55 % -> dropped", [(0, 55), (201, 45)], None, RP.REASON_OUTSIDE)]
    got = {}
    for name, parts, want, reason in cases:
        src_, dk_ = toy(parts)
        a = RP.majority_assign(src_, [1], dk_, [201, 202, 203])[1]
        got[name] = a
        ok(P, f"R43 RP2: {name}", a["assigned"] == want and a["reason"] == reason and a["n_vox"] == 100)
    blob = subprocess.run(["git", "-C", str(REPO), "show", "9addaab:arcs/audit/src/a1_audit/reparcel.py"],
                          capture_output=True).stdout.decode("utf-8")
    pin = subprocess.run(["git", "-C", str(REPO), "rev-parse", "9addaab:arcs/audit/src/a1_audit/reparcel.py"],
                         capture_output=True).stdout.decode().strip()
    ns: dict = {"__name__": "reparcel_9addaab"}
    exec(compile(blob, "reparcel_9addaab", "exec"), ns)
    src40, dk40 = toy([(201, 40), (202, 35), (203, 25)])
    old = ns["majority_assign"](src40, [1], dk40, [201, 202, 203])[1]
    ok(P, "R43 must-fail: the plurality variant (reparcel.py at 9addaab) assigns the 40 / 35 / 25 parcel, which R43 "
       "drops (caught)", pin.startswith("53d38374") and old["assigned"] == 201
       and got[cases[1][0]]["assigned"] is None)
    # RP3: two source parcels assigned to one DK label; the weights are their full voxel counts (100 and 20), not
    # their voxels inside the label (60 and 15)
    src = np.zeros((120, 1, 1), dtype=np.int64)
    dkv = np.zeros((120, 1, 1), dtype=np.int64)
    src[:100], src[100:] = 1, 2
    dkv[:60], dkv[60:100] = 201, 202        # parcel 1: 60 % in 201
    dkv[100:115] = 201                      # parcel 2: 15 of 20 (75 %) in 201, 5 outside
    ident = np.eye(4)
    ids_, vals_, rep_ = RP.parcels_to_dk({1: 2.0, 2: 8.0}, src, ident, [1, 2], dkv, ident, [201, 202])
    ok(P, "R43 RP3: DK value = (100 x 2.0 + 20 x 8.0) / 120 (the source parcels' own voxel counts)",
       ids_.tolist() == [201] and abs(vals_[0] - (100 * 2.0 + 20 * 8.0) / 120) < 1e-12
       and rep_["assignment"][1]["n_vox"] == 100 and rep_["assignment"][2]["n_vox"] == 20)


def p18():
    P = "P18"
    print("\nP18 re-parcellation (synthetic volumes / surfaces / annots)")
    rng = np.random.default_rng(18)
    # (0) the ported nn_resample_labels = A3's (text against the git blob; outputs bit-identical)
    pin = re.search(r"git blob ([0-9a-f]{40})", inspect_src_of_port()).group(1)       # the port's own pin
    blob = subprocess.run(["git", "-C", str(REPO), "cat-file", "blob", pin], capture_output=True).stdout.decode("utf-8")
    head_blob = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD:arcs/replication/src/h_targets.py"],
                               capture_output=True).stdout.decode().strip()
    print(f"  A3 h_targets.py: port pinned to blob {pin[:12]}; HEAD's blob {'the same' if head_blob == pin else 'DIFFERS'}")
    import ast
    import inspect
    tree = ast.parse(blob)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "nn_resample_labels")
    a3_src = "\n".join(blob.split("\n")[fn.lineno - 1:fn.end_lineno])
    mine = inspect.getsource(RP.nn_resample_labels).rstrip("\n")
    ok(P, "nn_resample_labels: text equals A3's pinned blob (h_targets.py)", mine == a3_src)
    ns: dict = {"np": np}
    exec(compile(a3_src, "a3_h_targets_nn", "exec"), ns)
    same = True
    for k in range(5):
        lab = rng.integers(0, 9, size=(7, 8, 6))
        A = np.diag([2.0, 2.0, 2.0, 1.0])
        A[:3, 3] = rng.normal(size=3) * 3
        B = np.diag([1.0, 1.3, 0.9, 1.0])
        B[:3, 3] = rng.normal(size=3) * 3
        same &= np.array_equal(RP.nn_resample_labels(lab, A, (9, 10, 11), B), ns["nn_resample_labels"](lab, A, (9, 10, 11), B))
    ok(P, "nn_resample_labels: outputs bit-identical to A3's function on 5 random affine pairs", bool(same))

    # (1) volume -> atlas: known parcel means recovered on a finer, shifted grid; < 50 % coverage dropped
    atlas = np.zeros((10, 10, 10), dtype=np.int64)
    atlas[0:5, 0:5, 0:10] = 1
    atlas[5:10, 0:5, 0:10] = 2
    atlas[0:5, 5:10, 0:10] = 3
    atlas[5:10, 5:10, 0:5] = 4
    atlas[5:10, 5:10, 5:10] = 5
    A_aff = np.diag([2.0, 2.0, 2.0, 1.0])
    # the map: 1 mm voxels whose centres sit at atlas index + {-0.25, +0.25} (no rounding ties)
    M_aff = np.diag([1.0, 1.0, 1.0, 1.0])
    M_aff[:3, 3] = -0.5
    shape = (20, 20, 20)
    ijk = np.indices(shape).reshape(3, -1)
    a_idx = (ijk - 0.5) / 2.0                       # atlas index of each map voxel centre
    exp_lab = atlas[tuple(np.floor(a_idx + 0.5).astype(int).clip(0, 9))].reshape(shape)
    vol = rng.normal(size=shape)
    true_means = {}
    cover = {1: 1.0, 2: 0.4, 3: 0.5, 4: 0.75, 5: 0.0}
    for pid, cov in cover.items():
        vox = np.flatnonzero(exp_lab.ravel() == pid)
        n_bad = len(vox) - int(round(cov * len(vox)))
        bad = rng.choice(vox, size=n_bad, replace=False)
        flat = vol.ravel()
        flat[bad[: n_bad // 2]] = 0.0
        flat[bad[n_bad // 2:]] = np.nan
        vol = flat.reshape(shape)
        good = np.setdiff1d(vox, bad)
        true_means[pid] = float(vol.ravel()[good].mean()) if len(good) else None
    ok(P, "volume: the independent label map equals nn_resample_labels on the tie-free grid",
       np.array_equal(RP.nn_resample_labels(atlas, A_aff, shape, M_aff), exp_lab))
    ids, vals, rep = RP.volume_to_parcels(vol, M_aff, atlas, A_aff, [1, 2, 3, 4, 5, 6])
    got = dict(zip(ids.tolist(), vals.tolist()))
    ok(P, "volume: known parcel means recovered (1e-12)", set(got) == {1, 3, 4} and
       all(abs(got[k] - true_means[k]) < 1e-12 for k in got))
    ok(P, "volume: a parcel at 40 % coverage dropped and reported; 50 % kept; 0 % and an absent parcel dropped",
       rep["dropped"] == [2, 5, 6] and [r["coverage"] for r in rep["parcels"]][:5] == [1.0, 0.4, 0.5, 0.75, 0.0]
       and rep["label"] == "re-parcellated")
    try:
        import nibabel as nib
        from nilearn.image import resample_to_img
        aimg = nib.Nifti1Image(atlas.astype(np.int16), A_aff)
        mimg = nib.Nifti1Image(np.zeros(shape, dtype=np.float32), M_aff)
        with PW.quiet_warnings():
            nl = np.asarray(resample_to_img(aimg, mimg, interpolation="nearest", force_resample=True,
                                            copy_header=True).dataobj)
        interior = np.all((a_idx >= 0) & (a_idx <= 9), axis=0).reshape(shape)
        edge = ~interior
        ok(P, "volume: nearest-neighbour labels equal nilearn's resample_to_img on every interior voxel "
           "(independent implementation; at the edge A3's floor(v + .5) keeps centres up to half a voxel outside, "
           "nilearn / scipy order 0 does not: reported)", np.array_equal(nl.astype(np.int64)[interior],
                                                                          exp_lab[interior]) and edge.any())
        print(f"  NN edge convention: map voxels whose atlas coordinate lies within half a voxel outside the atlas "
              f"{int(edge.sum())}; labelled by A3's rule {int((exp_lab[edge] > 0).sum())}, by nilearn "
              f"{int((nl.astype(np.int64)[edge] > 0).sum())}")
    except ImportError:
        print("  nilearn not importable: cross-check skipped")
    # atlas identity
    an = RUN / "atlas.nii.gz"
    import nibabel as nib
    nib.save(nib.Nifti1Image(atlas.astype(np.int16), A_aff), str(an))
    sha = hashlib.sha256(an.read_bytes()).hexdigest()
    lab2, aff2 = RP.load_atlas_verified(an, sha)
    try:
        RP.load_atlas_verified(an, "0" * 64)
        st = None
    except RP.ReparcelRefused as e:
        st = e.status
    ok(P, "atlas identity: sha256 verified before parsing; a mismatch -> 'not computable (atlas identity)'",
       np.array_equal(lab2, atlas) and np.allclose(aff2, A_aff) and st == RP.STATUS_ATLAS_IDENTITY)

    # (2) fsaverage surface -> dk-ctx through a synthetic annot and GIFTI
    dk = [f"qxdk{k:02d}" for k in range(34)]
    names = ["unknown"] + dk[:3] + ["corpuscallosum"] + dk[3:]
    apath = RUN / "lh.synthetic.annot"
    labels = synth_annot(apath, 3000, names, rng)
    vals = rng.normal(size=3000).astype(np.float32).astype(np.float64)
    vals[labels == names.index("qxdk05")] = np.nan
    vals[np.flatnonzero(labels == names.index("qxdk06"))[:5]] = np.nan
    gpath = RUN / "lh.synthetic.func.gii"
    nib.save(nib.gifti.GiftiImage(darrays=[nib.gifti.GiftiDataArray(vals.astype(np.float32),
                                                                    intent="NIFTI_INTENT_NONE",
                                                                    datatype="NIFTI_TYPE_FLOAT32")]), str(gpath))
    lab_r, names_r = RP.read_annot(apath)
    v_r = RP.read_gifti_values(gpath)
    ok(P, "annot labels read back (nibabel write / read), GIFTI vertex count = annot vertex count",
       np.array_equal(lab_r, labels) and names_r == names and v_r.shape[0] == lab_r.shape[0])
    knames, kvals, srep = RP.surface_to_dk(v_r, lab_r, names_r, dk)
    exp = {}
    for nm in dk:
        sel = (labels == names.index(nm)) & np.isfinite(vals)
        if sel.any():
            exp[nm] = float(vals[sel].mean())
    ok(P, "surface: label means over finite vertices recovered (1e-12); unknown / corpuscallosum excluded; a label "
       "with no finite vertex dropped and reported", knames == [n for n in dk if n in exp] and
       all(abs(v - exp[n]) < 1e-12 for n, v in zip(knames, kvals)) and srep["n_excluded"] == 2 and
       srep["n_matched"] == 34 and srep["n_dropped"] == 1)
    refusals = 0
    for args in ((v_r[:-1], lab_r, names_r, dk), (v_r, lab_r, ["unknown"] + ["qxzz"] + names_r[2:], dk),
                 (v_r, lab_r, names_r, dk[:33] + ["qxother"]), (v_r, lab_r, names_r, dk[:33] + [dk[0]])):
        try:
            RP.surface_to_dk(*args)
        except RP.ReparcelRefused as e:
            refusals += e.status == RP.STATUS_FS_NOT_MATCHING
    ok(P, "surface: refused when vertex counts differ, 33 names match, a DK name is absent, DK names repeat (4)",
       refusals == 4, str(refusals))
    g2 = RUN / "two.func.gii"
    nib.save(nib.gifti.GiftiImage(darrays=[nib.gifti.GiftiDataArray(vals.astype(np.float32)),
                                           nib.gifti.GiftiDataArray(vals.astype(np.float32))]), str(g2))
    try:
        RP.read_gifti_values(g2)
        r5 = False
    except RP.ReparcelRefused:
        r5 = True
    ok(P, "surface: a GIFTI with two data arrays refused (RP5)", r5)

    # (3) Glasser -> DK majority (R15): label list ids read, not assumed; outside / tie dropped; weighted mean
    src = np.zeros((12, 6, 4), dtype=np.int64)
    dkv = np.zeros((12, 6, 4), dtype=np.int64)
    src[0:4, :, :] = 7          # left parcel "L_a": 96 voxels
    src[4:6, :, :] = 3          # left parcel "L_b": 48
    src[6:8, :, :] = 11         # left parcel "L_c": 48
    src[8:10, :, :] = 5         # left parcel "L_d": 48 (tie)
    src[10:12, :, :] = 9        # right parcel "R_a": never processed
    dkv[0:3, :, :] = 101        # L_a: 72 of 96 in DK 101, 24 in DK 102 -> 101 (share .75)
    dkv[3:5, :, :] = 102        # L_b: 24 in 102, 24 outside?  -> see below
    dkv[5:6, :, :] = 0
    dkv[6:8, 0:2, :] = 102      # L_c: 16 in 102, 32 outside -> dropped (outside)
    dkv[8:10, 0:3, :] = 101     # L_d: 24 in 101, 24 in 103 -> tie -> dropped
    dkv[8:10, 3:6, :] = 103
    dkv[10:12, :, :] = 101
    S_aff = np.diag([1.0, 1.0, 1.0, 1.0])
    # the DK atlas on a coarser grid would need resampling; here both grids are identical, which nn_resample keeps
    text = "3 L_b\n9 R_a\n\n7 L_a\n5 L_d\n11 L_c\n"
    ll = RP.read_label_list(text)
    left = RP.left_ids(ll)
    ok(P, "R15: left ids read from the label list (interleaved, not assumed contiguous)", left == [3, 7, 5, 11])
    sv = {7: 2.0, 3: 5.0, 11: 9.0, 5: 4.0, 9: 100.0}
    ids, vals_, rep = RP.parcels_to_dk(sv, src, S_aff, left, dkv, S_aff, [101, 102, 103])
    asg = rep["assignment"]
    # L_b: 24 voxels in 102 (rows 4), 24 outside (row 5) -> 50 / 50, no label above 50 % -> dropped (RP2, R43)
    ok(P, "Glasser -> DK majority (> 50 %, RUN_PLAN_amend_2 R43): assignment (.75 share), outside-majority dropped, "
       "50 / 50 splits (DK-DK, DK-outside) dropped as 'no label above 50 %'",
       asg[7]["assigned"] == 101 and asg[7]["share"] == 0.75 and asg[11]["reason"] == RP.REASON_OUTSIDE and
       asg[5]["reason"] == RP.REASON_NO_MAJORITY and asg[3]["reason"] == RP.REASON_NO_MAJORITY and 9 not in asg)
    ok(P, "Glasser -> DK: DK value = voxel-count-weighted mean of its assigned parcels; unassigned DK labels missing",
       ids.tolist() == [101] and abs(vals_[0] - 2.0) < 1e-12 and rep["n_unassigned"] == 2)
    # a second assigned parcel into 101 to test the weights
    src2, dk2 = src.copy(), dkv.copy()
    dk2[4:6, :, :] = 101      # L_b now fully in 101 (48 voxels)
    ids2, vals2, rep2 = RP.parcels_to_dk(sv, src2, S_aff, left, dk2, S_aff, [101, 102, 103])
    ok(P, "Glasser -> DK: weights = source voxel counts (96 x 2.0 + 48 x 5.0) / 144",
       ids2.tolist() == [101] and abs(vals2[0] - (96 * 2.0 + 48 * 5.0) / 144) < 1e-12)
    p18_r43()
    m1 = RP.match_one_to_one(["L_a", "L_b"], ["L_b", "L_a"])
    m2 = RP.match_one_to_one(["L_a", "L_b"], ["L_b", "L_c"])
    try:
        RP.read_label_list("1 L_a\nnot a label line here\n")
        st = None
    except RP.ReparcelRefused as e:
        st = e.status
    ok(P, "R15: name match one-to-one by counts; a mismatch reported; a malformed label list refused with "
       "the Pretzsch status", m1["one_to_one"] and not m2["one_to_one"] and m2["matched"] == 1 and
       st == RP.STATUS_GLASSER)

    # (4) DK-308 name prefix; (5) spheres -> AAL centroid rule; (6) bilateral; (7) R31 / R14
    sub_names = ["unknown", "qxdk00_part1", "qxdk00_part2", "qxdk01_part1"]
    l308 = np.array([1] * 30 + [2] * 10 + [3] * 20 + [0] * 5)
    v308 = {"lh_qxdk00_part1": 1.0, "lh_qxdk00_part2": 4.0, "lh_qxdk01_part1": 7.0, "lh_qxzz_part1": 3.0}
    n3, v3, r3 = RP.dk308_to_dk(v308, l308, sub_names, dk)
    ok(P, "DK-308 -> DK: name prefix nesting, vertex-count-weighted mean (30 x 1 + 10 x 4) / 40",
       n3 == ["qxdk00", "qxdk01"] and abs(v3[0] - 70 / 40) < 1e-12 and v3[1] == 7.0 and r3["n_no_parent"] == 1)
    aal = np.zeros((10, 10, 10), dtype=np.int64)
    aal[0:5] = 2001
    aal[5:10, 0:5] = 2002
    aal_aff = np.diag([2.0, 2.0, 2.0, 1.0])
    aal_aff[:3, 3] = [-10, -10, -10]
    xyz = np.array([[-8.0, -8, -8], [-6, 0, 2], [4, -6, 0], [4, 6, 0], [40, 0, 0]])
    sv_ = np.array([1.0, 3.0, 5.0, 100.0, 7.0])
    i5, v5, r5_ = RP.spheres_to_aal(xyz, sv_, aal, aal_aff, [2001, 2002])
    ok(P, "spheres -> AAL: label containing the centroid; label value = mean of its spheres; a centroid in no label "
       "and one outside the volume dropped and reported", i5.tolist() == [2001, 2002] and v5.tolist() == [2.0, 5.0]
       and r5_["dropped_spheres"] == [3, 4])
    try:
        RP.spheres_to_aal(None, [], aal, aal_aff, [2001])
        st = None
    except RP.ReparcelRefused as e:
        st = e.status
    ok(P, "spheres: coordinates not in the carrier -> 'not auditable (ROI coordinates unpublished)'",
       st == RP.STATUS_ROI_UNPUBLISHED)
    bi, bv = RP.bilateral_on_left({"qxdk01": 2.0, "qxdk00": 1.0}, {"qxdk00": 1001, "qxdk01": 1002})
    ok(P, "bilateral-average map placed on the left parcels", bi.tolist() == [1001, 1002] and bv.tolist() == [1.0, 2.0])
    rb = RP.recipe_parcellation("parcels", None, "dk-ctx")
    rd = RP.recipe_parcellation("voxels", None, "V-AAL")
    rpp = RP.recipe_parcellation("parcels", "HCP-MMP1 left 180", "dk-ctx")
    ok(P, "R31 / R14: Benkarim -> dk-ctx with its label; decoder fallback -> the claim's class 'not the decoder'; "
       "paper parcellation kept", rb["parcellation"] == "dk-ctx" and rb["label"] ==
       "re-derived (per-donor parcel recipe, dk-ctx; the paper's parcellation unnamed)" and rd["label"] ==
       "re-derived (per-donor parcel recipe, V-AAL), not the decoder" and rpp["parcellation"] == "HCP-MMP1 left 180")
    # R31's y: the NeuroVault-like volume re-parcellated by the volume rule onto the dk-ctx subset of a DK-like atlas
    dk_ctx_ids = [1, 3, 4]                     # a "left cortical" subset; 2 and 5 stand for non-dk-ctx parcels
    ids6, v6, r6 = RP.volume_to_parcels(vol, M_aff, atlas, A_aff, dk_ctx_ids)
    ok(P, "R31: Benkarim's y = the volume rule on dk-ctx parcels only (other atlas labels never enter)",
       ids6.tolist() == [1, 3, 4] and all(abs(a - true_means[k]) < 1e-12 for k, a in zip(ids6.tolist(), v6)))


# ================================================================================================================
# P21's deferred part
# ================================================================================================================
def p21_deferred():
    P = "P21"
    print("\nP21 (deferred part): with G1 closed fetch_extract makes no network request; the launcher refuses")
    from a1_audit.tests import test_gates_p21 as T21
    g = T21.Git(RUN)
    closed = RUN / "p21_g1_closed"
    T21.build(g, closed, next(c for c in T21.cases_35() if c[0] == "R23")[2])   # later "(b-ii) commissioned"
    opened = RUN / "p21_g1_open"
    T21.build(g, opened, T21.Spec())
    g2closed = RUN / "p21_g2_closed"
    g.init(g2closed)
    g.commit(g2closed, "2026-09-30T07:16:49+02:00", "base", {"README.txt": b"synthetic\n"})
    ok(P, "scratch gates: G1 closed (superseded) / open; G2 closed (no step-3 (v) record)",
       gates.g1_check(closed)[1] == "superseded" and gates.g1_open(opened) and not gates.step3v_open(g2closed))

    calls = {"head": 0, "get": 0, "stream": 0, "opens": 0, "curl": 0, "sockets": 0}

    def raiser(name):
        def f(*a, **k):
            calls[name] += 1
            raise AssertionError("network function called")
        return f

    @contextlib.contextmanager
    def tripwires(data_root: Path):
        saved_net = dict(FE.NET)
        FE.NET.update(head=raiser("head"), get=raiser("get"), stream=raiser("stream"))
        import builtins
        orig_open, orig_io_open = builtins.open, io.open
        orig_popen_init = subprocess.Popen.__init__
        orig_connect = socket.socket.connect
        dr = str(data_root).lower()

        def t_open(file, *a, **k):
            if isinstance(file, (str, os.PathLike)) and os.fspath(file).lower().startswith(dr):
                calls["opens"] += 1
                raise AssertionError("file under the data root opened")
            return orig_open(file, *a, **k)

        def t_popen(self, args, *a, **k):
            prog = os.path.basename(str(args[0] if isinstance(args, (list, tuple)) else args)).lower()
            if prog in ("curl", "curl.exe"):
                calls["curl"] += 1
                raise AssertionError("curl started")
            return orig_popen_init(self, args, *a, **k)

        def t_connect(self, *a, **k):
            calls["sockets"] += 1
            raise AssertionError("socket connect")
        builtins.open = t_open
        io.open = t_open
        subprocess.Popen.__init__ = t_popen
        socket.socket.connect = t_connect
        try:
            yield
        finally:
            builtins.open, io.open = orig_open, orig_io_open
            subprocess.Popen.__init__ = orig_popen_init
            socket.socket.connect = orig_connect
            FE.NET.update(saved_net)

    def created(roots: FE.Roots) -> int:
        base = roots.data.parent
        return sum(1 for _ in base.rglob("*")) if base.exists() else 0

    for gate, repo, label in (("G1", closed, "G1 closed"), ("G2", g2closed, "G2 closed")):
        roots = make_roots(f"p21_{gate}")
        roots.repo = repo
        roots.data.mkdir(parents=True)
        (roots.data / f"p21{gate.lower()}").mkdir()
        carrier = roots.data / f"p21{gate.lower()}" / "carrier.xlsx"
        carrier.write_bytes(b"synthetic carrier already on disk")
        before = created(roots)
        for k in calls:
            calls[k] = 0
        t = FE.Target(key=f"p21{gate.lower()}", gate=gate, url="https://example.invalid/p21_never_requested.xlsx",
                      kind="workbook", ext=".xlsx", sheets=(FE.SheetDecl(key="s", name="QxS", header_row=0,
                                                                         columns=(FE.Column("QxH", "h"),)),))
        out = io.StringIO()
        with tripwires(roots.data):
            res = FE.run_target(t, roots, out=out)
        lines = out.getvalue().strip().split("\n")
        ok(P, f"{label}: refused before any request or file open (fetch functions raise if called: 0 calls; curl 0; "
           f"sockets 0; opens under the data root 0; nothing created)",
           res["status"] == FE.STATUS_GATE and all(v == 0 for v in calls.values()) and created(roots) == before and
           len(lines) == 1 and re.fullmatch(rf"fetch_extract: p21{gate.lower()} gate {gate} CLOSED \(reason "
                                            r"[a-z_]+\); not fetched; no network request", lines[0]) is not None,
           json.dumps(calls))
    # positive control: with G1 open the same call reaches the (raising) fetch function -> the tripwire is live
    roots = make_roots("p21_open")
    roots.repo = opened
    for k in calls:
        calls[k] = 0
    t = FE.Target(key="p21open", gate="G1", url="https://example.invalid/p21_open.xlsx", kind="workbook", ext=".xlsx",
                  sheets=(FE.SheetDecl(key="s", name="QxS", header_row=0, columns=(FE.Column("QxH", "h"),)),))
    out = io.StringIO()
    with tripwires(roots.data):
        res = FE.run_target(t, roots, out=out)
    ok(P, "control: with G1 open the wrapper reaches the fetch function (1 HEAD call, raised) -> the tripwire is live",
       calls["head"] == 1 and res["status"] == FE.STATUS_FAILED and
       re.search(r"^AssertionError at fetch:head, fetch_extract\.py:\d+$", out.getvalue(), re.M) is not None)
    # the CLI with G1 closed: exit 3, one CLOSED line, nothing created (a separate process)
    roots = make_roots("p21_cli")
    tj = RUN / "p21_targets.json"
    tj.write_text(json.dumps({"targets": [{"key": "p21cli", "gate": "G1", "url": "https://example.invalid/x.xlsx",
                                           "kind": "workbook", "ext": ".xlsx"}]}), encoding="utf-8")
    args = ["--targets", str(tj), "--repo", str(closed)]
    for r in ("data", "records", "artifacts", "logs", "control", "quarantine"):
        args += [f"--{r}-root", str(getattr(roots, r))]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC)
    boot = ("import sys\nfrom a1_audit import fetch_extract as FE\n"
            "def no(*a, **k):\n    raise SystemExit(99)\n"
            "FE.NET.update(head=no, get=no, stream=no)\nsys.exit(FE.main(sys.argv[1:]))\n")
    pr = subprocess.run([sys.executable, "-X", "utf8", "-c", boot, *args], capture_output=True, env=env, timeout=300)
    so = pr.stdout.decode("utf-8", "replace").strip().split("\n")
    ok(P, "CLI with G1 closed: exit 3 (not 99: no fetch function called), one CLOSED line, nothing created",
       pr.returncode == 3 and len(so) == 1 and "gate G1 CLOSED (reason superseded)" in so[0] and
       not roots.data.parent.exists() and pr.stderr == b"", f"{pr.returncode}")
    # the launcher refuses carrier_test.py with G1 closed (spawn replaced by a raiser)
    spawned = []
    orig = gate_launch._spawn
    gate_launch._spawn = lambda cmd: spawned.append(cmd) or (_ for _ in ()).throw(AssertionError())
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            c1 = gate_launch.main(["G1", "--repo", str(closed), "--carrier-test", "selftest", "--workdir", str(RUN)])
            c2 = gate_launch.main(["G2", "--repo", str(g2closed), "--", sys.executable, "-c", "pass"])
    finally:
        gate_launch._spawn = orig
    ok(P, "launcher: G1 closed -> carrier_test.py not started; G2 closed -> command not started",
       c1 == c2 == gate_launch.EXIT_REFUSED and spawned == [])


# ================================================================================================================
def main() -> int:
    srv = start_stub()
    t0 = time.time()
    print(f"P18 / P19 / P20 / P21-deferred (RUN_PLAN.md v3.1 s7, s8; WP2); scratch run directory created")
    sections = (p19, p20_apparatus, lambda: p20_workbook(".xlsx"), lambda: p20_workbook(".xls"), p20_cases,
                p20_moreau, p20_zip, p20_tar, p20_subprocess, p18, p21_deferred)
    for fn in sections:
        try:
            fn()
        except Exception as e:  # noqa: BLE001 - a crashed section is a failure; print the class only
            tb = e.__traceback__
            where = "?"
            while tb is not None:
                if tb.tb_frame.f_code.co_filename.endswith(("test_material_p18_p19_p20.py", "fetch_extract.py",
                                                            "privacy_wrap.py", "identity.py", "reparcel.py")):
                    where = f"{os.path.basename(tb.tb_frame.f_code.co_filename)}:{tb.tb_lineno}"
                tb = tb.tb_next
            ok("HARNESS", f"section {getattr(fn, '__name__', 'lambda')} completed", False, f"{type(e).__name__} at {where}")
    srv.shutdown()
    print("\nSUB-CASES (checks passed / run)")
    for plant in sorted(RESULTS):
        for sub, (a, b) in RESULTS[plant].items():
            print(f"  {plant} {a}/{b} {'pass' if a == b else 'FAIL'}  {sub}")
    print("\nSUMMARY (pass / total per sub-case)")
    for plant in sorted(RESULTS):
        tot = [0, 0]
        for sub, (a, b) in RESULTS[plant].items():
            tot[0] += a
            tot[1] += b
        print(f"  {plant}: {tot[0]} / {tot[1]} checks, {sum(1 for a, b in RESULTS[plant].values() if a == b)} / "
              f"{len(RESULTS[plant])} sub-cases")
    print(f"  tripwire: material-path operations {TRIP['material_path']}, non-local sockets {TRIP['socket']}, "
          f"subprocess URLs other than the local stub {TRIP['subprocess_url']}")
    ok("HARNESS", "tripwire counts all 0", all(v == 0 for v in TRIP.values()))
    print(f"  elapsed {time.time() - t0:.0f} s")
    if FAILS:
        print(f"FAILED: {len(FAILS)}")
        for f in FAILS:
            print(f"  {f}")
        print(f"  scratch kept for inspection")
        return 1
    if not ARGS.keep:
        def onexc(func, p, exc):
            os.chmod(p, stat.S_IWRITE)
            func(p)
        shutil.rmtree(RUN, onexc=onexc)
    print("P18 / P19 / P20 / P21-deferred PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
