"""The single print rule of arcs/audit/RUN_PLAN.md v3.1 section 8 (FROZEN sha256 16c60232...) as an allow-list
tokeniser, plus the exception handler, the name screen and the guarded output channels every carrier-touching
stage of fetch_extract.py uses (WP2; P20).

The print rule (section 8 :1169-1203). Printed or written (stdout, stderr, logs, records, manifests): ONLY counts;
runner-built paths (built from pinned keys); line numbers (`file:line`); hashes; labels of the runner's own fixed
vocabulary (stage labels, the guard's rule letters W / N / V, found / not found, pass / fail, exception class names,
status strings of the TSV and the plan). Identity records (R13, R18, SOURCE.md) also carry the pinned URL, dates and
times, and the server's size / date / checksum headers (Content-Length, Last-Modified, a plain-MD5 ETag). Never
printed or written: any string derived from a carrier.

How this module enforces it:
- AllowList.check(line, ctx) parses a line left to right into tokens; every token must be one of
    separator   white space or one of  , ; : = ( ) [ ] { } " ' | / \\ < > % . ! ? * # + - ~ ^ &
    exact       a string registered by the runner: a runner-built path (raw, POSIX and JSON-escaped forms), a pinned
                key, a runner-built file name; in ctx "identity" also a pinned URL
    file:line   <module>.py:<n> for the runner's own modules and the frozen guard / fetch helper
    hex         64, 40, 32 or 7-12 lower-case hex digits (sha256, git blob / commit, MD5, short commit)
    number      an integer or decimal, optionally signed / with an exponent
    datetime    an ISO 8601 date-time (ctx "identity" only)
    rules       W, N, V, WN, WV, NV, WNV (the guard's rule letters)
    word        a word of the fixed vocabulary (case-sensitive; hyphen / underscore joined forms are one token);
                in ctx "identity" also the day / month names and GMT of an HTTP date
  A token not on the list makes the line a violation: the line is NOT written anywhere, the violation counter rises,
  PrintRuleViolation (which carries no text) is raised and the run stops (section 8 "Incidents": stop, propagate
  nothing, record counts, tell the operator).
- Emitter is the only writer: say() (stdout + the run log), write_json() / write_text() (records, SOURCE.md),
  save_bytes() (files saved from a carrier, runner-built names only). Every writer reads back what it wrote.
- stage(em, label, fn, ...) is the section 8 exception handler: any exception (BaseException: the frozen guard's
  Refused is a SystemExit) is reported as "<ClassName> at <label>, <file>:<line>" with the innermost frame of the
  runner's own modules (or the frozen guard), and nothing else: no message, no traceback, no local value; the
  exception object is dropped before StageFailed (vocabulary only) is raised outside the handler (no __context__).
- StdioGuard replaces sys.stdout / sys.stderr while a carrier is touched: a library print that is not on the
  allow-list is dropped and counted (defence in depth; xlrd's logfile is also pointed at a sink).
- quiet_warnings() / quiet_logging() record warnings and log records by class / level only.
- screen(s) (section 8 "Screening"): the frozen guard's id_value_hits, ID_WORDING and BARE_SUBJECT on each path
  component and token of a carrier-derived string, in memory; returns counts per rule letter only.

Nothing in this module ever prints a carrier string; it never stores an exception message.
"""
from __future__ import annotations

import builtins
import contextlib
import hashlib
import io
import json
import logging
import os
import re
import sys
import warnings
from pathlib import Path

# ----------------------------------------------------------------------------------------------------------------
# vocabulary
# ----------------------------------------------------------------------------------------------------------------
RUNNER_FILES = ("fetch_extract.py", "privacy_wrap.py", "identity.py", "reparcel.py", "privacy_guard.py",
                "fetch_util.py", "wp3_material.py", "wp3_genes.py", "wp3_layout.py", "real_sources.py",
                "forms.py",   # WP3 phase 1: the material stage's readers report their own file:line
                "wp4_material.py", "wp4_read.py", "wp4_layout.py", "wp4_sets.py", "wp4_sources.py",
                "wp4_repro.py")   # WP4 phase 1
_FILE_LINE = re.compile(r"(?:%s):\d+(?![0-9A-Za-z_])" % "|".join(re.escape(f) for f in RUNNER_FILES))
_HEX = re.compile(r"(?:[0-9a-f]{64}|[0-9a-f]{40}|[0-9a-f]{32}|[0-9a-f]{7,12})(?![0-9A-Za-z_])")
_NUMBER = re.compile(r"[-+]?(?:\d+\.\d+|\d+)(?:[eE][-+]?\d+)?(?![0-9A-Za-z_])")
_RULES = re.compile(r"(?:WNV|WN|WV|NV|W|N|V)(?![0-9A-Za-z_])")
_ISO_DT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:\d{2})?(?![0-9A-Za-z_])")
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[-_][A-Za-z0-9]+)*(?![0-9A-Za-z_])")
SEPARATORS = frozenset(" \t\r\n,;:=()[]{}\"'|/\\<>%.!?*#+-~^&")
HTTP_DATE_WORDS = frozenset("Mon Tue Wed Thu Fri Sat Sun Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec GMT".split())

EXCEPTION_NAMES = frozenset(n for n, o in vars(builtins).items() if isinstance(o, type) and issubclass(o, BaseException))
EXTRA_EXCEPTION_NAMES = frozenset((
    "Refused", "XLRDError", "CompDocError", "BadZipFile", "LargeZipFile", "ReadError", "CompressionError",
    "StreamError", "ExtractError", "HeaderError", "TarError", "InvalidFileException", "ParseError", "ExpatError",
    "ImageFileError", "HeaderDataError", "CalledProcessError", "TimeoutExpired", "JSONDecodeError", "StageFailed",
    "PrintRuleViolation", "DoNotOpen", "LayoutRefused", "MemberRefused", "IdentityRefused", "QuarantineRefused",
    "DownloadRefused", "UnlistedException", "AssertionError", "StdioViolation", "PdfRefused", "PdfEnvironmentFault",
    "PdfminerException", "PDFSyntaxError", "PSEOF", "StageStop", "Sd7Refused", "PositionRefused", "ReparcelRefused"))

# The fixed vocabulary of every message, record key and status string this module and fetch_extract / identity /
# reparcel emit. Each phrase is split into words by _WORD; numbers and separators need no entry.
BASE_PHRASES = (
    # outcomes and connectives
    "found not found pass fail yes no none true false null of and or to from in at by on with for per after before "
    "the a an is are was were be not run stopped recorded raised refused open closed CLOSED OPEN reason count counts "
    "total kept dropped missing present absent declared undeclared fetched not-fetched matched unmatched expected "
    "observed tried try tries row rows column columns col cols cell cells sheet sheets block x numeric non-numeric "
    "header label labels form forms name names file files path paths member members link links type types regular "
    "other hard symbolic chain target outside archive stream streamed bytes size sha256 md5 git blob LF CRLF "
    "conversion basis identity match changed map maps record records log logs object objects extracted extraction "
    "save saved read read-back write written moved move quarantine quarantined deletion request operator "
    "authorised step session report register section ETHICS_PRIVACY incident procedure propagate nothing tell stop "
    "warnings warning logging level gate G1 G2 ungated status reading readings rule rules letter letters W N V "
    "screen hits hit id_wording id_value bare_subject identifier-bearing identifier per-participant supplement "
    "carrier carriers fetch_extract privacy_wrap identity reparcel privacy_guard fetch_util a1_audit run runs "
    "stage stages violation violations print-rule unchanged sheet-name member-name only touched run "
    "DEBUG INFO WARNING ERROR CRITICAL dropped_handler",
    # section 8 / R16 / R18 vocabulary
    "server content_length last_modified etag etag_md5 plain url date date_utc headers pinned prefreeze probe "
    "size-only stored tarball computed member's annot FreeSurfer distribution obtainable matching first second "
    "pass_1 pass_2 resolved unresolvable",
    # status strings (TSV / plan vocabulary; full strings are defined by the modules that use them)
    "auditable definition applicable not auditable computable atlas re-parcellated re-derived per-donor parcel "
    "recipe decoder paper's parcellation unnamed dk-ctx V-AAL V-DK MIST64 Moreau layout HCP-MMP1 eTable13 "
    "pinned coordinates unpublished ROI could be the",
)
RECORD_WORDS = ("true false null",)


def words_of(*phrases: str) -> set[str]:
    out: set[str] = set()
    for ph in phrases:
        out.update(m.group(0) for m in _WORD.finditer(ph))
    return out


class PrintRuleViolation(Exception):
    """Raised when a line fails the allow-list. Carries the channel label and a count only, never the line."""

    def __init__(self, channel: str = "unknown"):
        super().__init__(channel)
        self.channel = channel


class StageFailed(Exception):
    """A carrier-touching stage failed. Carries the class name, the stage label and file:line only."""

    def __init__(self, class_name: str, stage: str, where: str):
        super().__init__(f"{class_name} at {stage}, {where}")
        self.class_name, self.stage, self.where = class_name, stage, where


class AllowList:
    """The print rule's allow-list (module docstring). Contexts: stdout, stderr, log, record, identity, filename."""

    CONTEXTS = ("stdout", "stderr", "log", "record", "identity", "filename")

    def __init__(self, phrases=(), words=()):
        self.words: set[str] = words_of(*BASE_PHRASES, *phrases) | set(words) | set(EXCEPTION_NAMES) | \
            set(EXTRA_EXCEPTION_NAMES)
        self.record_words = words_of(*RECORD_WORDS)
        self.exact: set[str] = set()
        self.identity_exact: set[str] = set()
        self._rx = None
        self._rx_id = None

    # registration ---------------------------------------------------------------------------------------------
    def add_words(self, *words: str) -> None:
        for w in words:
            if not _WORD.fullmatch(w):
                raise ValueError("vocabulary word form")
            self.words.add(w)

    def add_phrases(self, *phrases: str) -> None:
        self.words |= words_of(*phrases)

    def add_exact(self, *items) -> None:
        """A runner-built path or name: its raw, POSIX and JSON-escaped forms become exact tokens."""
        for it in items:
            s = str(it)
            forms = {s, s.replace("\\", "/"), json.dumps(s)[1:-1], json.dumps(s.replace("\\", "/"))[1:-1]}
            self.exact |= {f for f in forms if f}
        self._rx = self._rx_id = None

    def add_identity(self, *items: str) -> None:
        """Pinned URLs (allowed in identity records and SOURCE.md only)."""
        for s in items:
            self.identity_exact |= {s, json.dumps(s)[1:-1]}
        self._rx_id = None

    def _exact_rx(self, identity: bool):
        if identity:
            if self._rx_id is None:
                toks = sorted(self.exact | self.identity_exact, key=len, reverse=True)
                self._rx_id = re.compile("|".join(re.escape(t) for t in toks)) if toks else None
            return self._rx_id
        if self._rx is None:
            toks = sorted(self.exact, key=len, reverse=True)
            self._rx = re.compile("|".join(re.escape(t) for t in toks)) if toks else None
        return self._rx

    # the check --------------------------------------------------------------------------------------------------
    def check(self, line: str, ctx: str) -> bool:
        if ctx not in self.CONTEXTS:
            return False
        if not isinstance(line, str):
            return False
        if ctx == "filename":
            return self.check_filename(line)
        identity = ctx == "identity"
        record = ctx in ("record", "identity")
        rx = self._exact_rx(identity)
        i, n = 0, len(line)
        while i < n:
            if rx is not None:
                m = rx.match(line, i)
                if m is not None and (m.end() == n or line[m.end()] in SEPARATORS):
                    i = m.end()
                    continue
            m = ((_ISO_DT.match(line, i) if identity else None) or _FILE_LINE.match(line, i)
                 or _HEX.match(line, i) or _NUMBER.match(line, i))
            if m is not None:
                i = m.end()
                continue
            m = _WORD.match(line, i)
            if m is not None:
                w = m.group(0)
                if (w in self.words or (record and w in self.record_words) or _RULES.fullmatch(w)
                        or (identity and w in HTTP_DATE_WORDS)):
                    i = m.end()
                    continue
                return False
            if line[i] in SEPARATORS:
                i += 1
                continue
            return False
        return True

    def check_filename(self, name: str) -> bool:
        """A saved file's name: a registered runner-built name, or <word>(.<word>)* where every word is vocabulary,
        a hex digest or a number (e.g. <key>_member3.xlsx, <key>.json)."""
        if name in self.exact:
            return True
        if not re.fullmatch(r"[A-Za-z0-9_.\-]{1,120}", name):
            return False
        for part in name.split("."):
            if not part:
                return False
            if part in self.words or _HEX.fullmatch(part) or re.fullmatch(r"\d+", part):
                continue
            m = re.fullmatch(r"([A-Za-z0-9_\-]+?)_member(\d+)", part)
            if m and m.group(1) in self.words:
                continue
            m = re.fullmatch(r"([A-Za-z0-9_\-]+?)_(extract|identity|deletion_request|source|log)", part)
            if m and m.group(1) in self.words:
                continue
            return False
        return True


# ----------------------------------------------------------------------------------------------------------------
# output channels
# ----------------------------------------------------------------------------------------------------------------
def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Emitter:
    """The only writer of a run. Every line is checked before it is written; a failing line is never written."""

    def __init__(self, allow: AllowList, stream=None, log_path: Path | None = None, prefix: str = ""):
        self.allow = allow
        self.stream = stream
        self.log_path = Path(log_path) if log_path is not None else None
        self.prefix = prefix
        self.n_lines = 0
        self.n_violations = 0
        self.written: list[Path] = []          # every file this emitter wrote (records, texts, saved bytes)
        if self.log_path is not None:
            self.allow.add_exact(self.log_path)
            self._check_name(self.log_path)

    def _out(self):
        return self.stream if self.stream is not None else sys.__stdout__

    def _violation(self, channel: str):
        self.n_violations += 1
        raise PrintRuleViolation(channel)

    def _check_name(self, path: Path) -> None:
        if not self.allow.check_filename(Path(path).name):
            self._violation("filename")

    def say(self, line: str) -> None:
        line = self.prefix + line
        if "\n" in line or not self.allow.check(line, "stdout"):
            self._violation("stdout")
        out = self._out()
        out.write(line + "\n")
        out.flush()
        if self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "ab") as f:
                f.write((line + "\n").encode("utf-8"))
            if self.log_path not in self.written:
                self.written.append(self.log_path)
        self.n_lines += 1

    def check_text(self, text: str, ctx: str) -> None:
        for ln in text.split("\n"):
            if not self.allow.check(ln, ctx):
                self._violation(ctx)

    def write_text(self, path: Path, text: str, ctx: str = "record", append: bool = False) -> str:
        """Write (or append) UTF-8 LF text after checking every line; read back; return the file's sha256."""
        path = Path(path)
        self._check_name(path)
        self.check_text(text, ctx)
        data = text.encode("utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        if append and path.exists():
            before = path.read_bytes()
            with open(path, "ab") as f:
                f.write(data)
            back = path.read_bytes()
            if back != before + data:
                raise OSError("read-back")
        else:
            if path.exists():
                raise FileExistsError("record exists")
            tmp = path.with_name(path.name + ".tmp")
            if tmp.exists():
                raise FileExistsError("tmp exists")
            tmp.write_bytes(data)
            os.replace(tmp, path)
            if path.read_bytes() != data:
                raise OSError("read-back")
        if path not in self.written:
            self.written.append(path)
        return sha256_file(path)

    def write_json(self, path: Path, obj, ctx: str = "record") -> str:
        text = json.dumps(obj, indent=1, ensure_ascii=True, allow_nan=False) + "\n"
        sha = self.write_text(path, text, ctx=ctx)
        if json.loads(Path(path).read_text(encoding="utf-8")) != json.loads(text):
            raise OSError("read-back")
        return sha

    def save_bytes(self, path: Path, data: bytes) -> str:
        """A file saved from a carrier (an extracted member): runner-built name, never overwritten, read back."""
        path = Path(path)
        self._check_name(path)
        if path.exists():
            raise FileExistsError("saved file exists")
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        if tmp.exists():
            raise FileExistsError("tmp exists")
        tmp.write_bytes(data)
        os.replace(tmp, path)
        sha = sha256_file(path)
        if sha != sha256_bytes(data):
            raise OSError("read-back")
        self.written.append(path)
        return sha

    def register_saved(self, path: Path) -> None:
        """A file another writer (fetch_util's curl, a streamed member) created under a runner-built name."""
        path = Path(path)
        self._check_name(path)
        if path not in self.written:
            self.written.append(path)


# ----------------------------------------------------------------------------------------------------------------
# the exception handler (section 8 "Exceptions")
# ----------------------------------------------------------------------------------------------------------------
def _where(tb, caller: str | None = None, own: str | None = None) -> str:
    """The raising code line: the innermost traceback frame in one of the runner's own modules (or the frozen guard /
    fetch helper), the handler's own frame excluded; if there is none (the callable was a library or test function),
    the line that called stage() when that is a runner line; else the handler's own line. Always '<runner file>:<n>'
    (library file names are not on the list)."""
    best = None
    while tb is not None:
        code = tb.tb_frame.f_code
        fn = os.path.basename(code.co_filename)
        if fn in RUNNER_FILES and not (fn == "privacy_wrap.py" and code.co_name == "stage"):
            best = f"{fn}:{tb.tb_lineno}"
        tb = tb.tb_next
    return best or caller or own or "privacy_wrap.py:0"


def _loc(frame) -> str | None:
    fn = os.path.basename(frame.f_code.co_filename)
    return f"{fn}:{frame.f_lineno}" if fn in RUNNER_FILES else None


def _class_name(e: BaseException, allow: AllowList) -> str:
    n = type(e).__name__
    return n if (n in allow.words and _WORD.fullmatch(n)) else "UnlistedException"


def stage(em: Emitter, label: str, fn, *args, **kw):
    """Section 8's handler for one carrier-touching stage: returns fn(*args, **kw). On any exception (BaseException:
    the frozen guard's Refused is a SystemExit) exactly one line '<ClassName> at <label>, <file>:<line>' is said and
    StageFailed (the same three items) is raised. The new exception is raised OUTSIDE the except block, so it has no
    __context__: the original exception (its message may name a sheet or hold a cell) is not chained, not printed by
    any later traceback and not kept. A StageFailed or PrintRuleViolation from an inner stage passes through once.
    KeyboardInterrupt: the line, then a fresh KeyboardInterrupt."""
    info = None
    caller = _loc(sys._getframe(1))
    try:
        return fn(*args, **kw)
    except StageFailed:
        raise
    except PrintRuleViolation as e:
        info = ("PrintRuleViolation", e.channel, _where(e.__traceback__, caller, _loc(sys._getframe(0))))
    except BaseException as e:  # noqa: BLE001 -- Refused is a SystemExit
        info = (_class_name(e, em.allow), "kbd" if isinstance(e, KeyboardInterrupt) else None,
                _where(e.__traceback__, caller, _loc(sys._getframe(0))))
    # here the exception object is gone (Python deletes the except-target name); only vocabulary remains
    cls, channel, where = info
    if cls == "PrintRuleViolation":
        try:
            em.say(f"PrintRuleViolation at {label}, {where}; run stopped (ETHICS_PRIVACY incident procedure: "
                   f"stop, propagate nothing, record counts, tell the operator)")
        except PrintRuleViolation:
            pass
        raise PrintRuleViolation(channel or "unknown")
    em.say(f"{cls} at {label}, {where}")
    if channel == "kbd":
        raise KeyboardInterrupt
    raise StageFailed(cls, label, where)


# ----------------------------------------------------------------------------------------------------------------
# library output: stdio, warnings, logging
# ----------------------------------------------------------------------------------------------------------------
class _CheckedStream(io.TextIOBase):
    def __init__(self, guard: "StdioGuard", channel: str):
        self.guard, self.channel, self.buf = guard, channel, ""

    def writable(self):
        return True

    def write(self, s):
        if not isinstance(s, str):
            s = str(s)
        self.buf += s
        while "\n" in self.buf:
            line, self.buf = self.buf.split("\n", 1)
            self.guard._line(self.channel, line)
        return len(s)

    def flush(self):
        pass

    def finish(self):
        if self.buf:
            self.guard._line(self.channel, self.buf)
            self.buf = ""


class StdioGuard:
    """Replace sys.stdout / sys.stderr: a line on the allow-list passes to the real stream, any other is dropped and
    counted. `violations` is checked by the caller after the stage (the dropped text is never kept)."""

    def __init__(self, allow: AllowList, out=None, err=None):
        self.allow = allow
        self.out = out if out is not None else sys.__stdout__
        self.err = err if err is not None else sys.__stderr__
        self.violations = 0
        self.passed = 0

    def _line(self, channel: str, line: str):
        if self.allow.check(line, channel):
            (self.out if channel == "stdout" else self.err).write(line + "\n")
            self.passed += 1
        else:
            self.violations += 1

    def __enter__(self):
        self._saved = (sys.stdout, sys.stderr)
        self._o, self._e = _CheckedStream(self, "stdout"), _CheckedStream(self, "stderr")
        sys.stdout, sys.stderr = self._o, self._e
        return self

    def __exit__(self, *exc):
        self._o.finish()
        self._e.finish()
        sys.stdout, sys.stderr = self._saved
        return False


_LEVEL_NAMES = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")   # other levels (nibabel's 45) count as 'level <n>'


class _CountingHandler(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.counts: dict[str, int] = {}

    def emit(self, record):
        name = record.levelname if record.levelname in _LEVEL_NAMES else f"level {int(record.levelno)}"
        self.counts[name] = self.counts.get(name, 0) + 1


@contextlib.contextmanager
def quiet_logging():
    """Every log record is counted by level, never formatted or printed. WP3 fix round 1 (A1): EVERY logger's own
    handlers are taken off for the duration, not only the root's - a library logger with its own handler (nibabel's
    'nibabel.global' binds a StreamHandler to sys.stderr at import, imageglobals.py:30-31) would otherwise print past
    the guard - and every logger propagates to the root logger, whose one handler counts. A handler a library adds
    during the context (a library first imported inside a stage binds sys.stderr = the guard's stream) is never
    attached: it is counted ('dropped_handler') and dropped, so no stale guard stream survives the stage. On exit
    every logger that existed before gets its own handlers and propagate flag back; loggers created inside keep none
    (their records reach the root logger). logging.lastResort is not reached (the root has a handler)."""
    root = logging.getLogger()
    h = _CountingHandler()
    loggers = [root] + [lg for lg in logging.Logger.manager.loggerDict.values() if isinstance(lg, logging.Logger)]
    saved = [(lg, lg.handlers, lg.propagate) for lg in loggers]
    saved_level = root.level
    for lg in loggers:
        lg.handlers = []
        if lg is not root:
            lg.propagate = True
    root.handlers = [h]
    root.setLevel(logging.DEBUG)
    orig_add = logging.Logger.addHandler

    def _deferred_add(self, hdlr):     # a handler added inside the context: counted, never attached
        h.counts["dropped_handler"] = h.counts.get("dropped_handler", 0) + 1
    logging.Logger.addHandler = _deferred_add
    try:
        yield h.counts
    finally:
        logging.Logger.addHandler = orig_add
        for lg, hs, prop in saved:
            lg.handlers = hs
            lg.propagate = prop
        root.setLevel(saved_level)


def guarded_stage(em: Emitter, label: str, fn, *args, out=None, err=None, **kw):
    """fn(*args, **kw) inside the guards fetch_extract.run_target puts around its body (WP3 fix round 3, A1): the stdio
    guard (a line off the allow-list dropped and counted, never shown), quiet warnings and quiet logging (every logger,
    a library's own handler included), and section 8's handler (an exception becomes StageFailed: class, stage and
    file:line only). Returns (value, counts); counts = {stdio_violations, stdio_passed, warnings, logging}. A stdio
    violation raises StageFailed('StdioViolation', label, '-') after the guard (the dropped text is never kept)."""
    with StdioGuard(em.allow, out=out, err=err) as sg, quiet_warnings() as wc, quiet_logging() as lc:
        value = stage(em, label, fn, *args, **kw)
    counts = {"stdio_violations": sg.violations, "stdio_passed": sg.passed, "warnings": dict(wc), "logging": dict(lc)}
    if sg.violations:
        raise StageFailed("StdioViolation", label, "-")
    return value, counts


def neutralise_library_handlers(*names: str) -> int:
    """WP3 fix round 1 (A1): a library logger's own handlers (e.g. 'nibabel.global', whose module the caller imports
    first) are replaced for good by a NullHandler and the logger stops propagating: silent outside a stage, and inside
    one quiet_logging takes the NullHandler off and lets the records propagate to its counting root handler. Returns
    the number of handlers removed."""
    n = 0
    for name in names:
        lg = logging.getLogger(name)
        n += sum(1 for x in lg.handlers if not isinstance(x, logging.NullHandler))
        lg.handlers = [logging.NullHandler()]
        lg.propagate = False
    return n


def install_excepthook(prefix: str) -> None:
    """WP3 fix round 1 (A2): an uncaught exception prints its class name and the innermost a1_audit frame
    ('<module>.py:<n>') only - never its message or traceback (a message or frame may name a carrier's path)."""
    pkg = os.path.dirname(os.path.abspath(__file__))

    def hook(tp, value, tb):
        name = tp.__name__ if _WORD.fullmatch(tp.__name__ or "") else "UnlistedException"
        where = None
        while tb is not None:
            fn = os.path.abspath(tb.tb_frame.f_code.co_filename)
            if os.path.dirname(fn) == pkg or os.path.dirname(os.path.dirname(fn)) == pkg:
                where = f"{os.path.basename(fn)}:{tb.tb_lineno}"
            tb = tb.tb_next
        sys.__stderr__.write(f"{prefix}: uncaught {name}" + (f" at {where}" if where else "") +
                             "; no detail printed\n")
        sys.__stderr__.flush()
    sys.excepthook = hook


@contextlib.contextmanager
def quiet_warnings():
    """Warnings recorded by category class name only (counts); their messages are never printed or kept."""
    counts: dict[str, int] = {}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            yield counts
        finally:
            for w in caught:
                n = w.category.__name__
                counts[n] = counts.get(n, 0) + 1
            caught.clear()


class Sink(io.TextIOBase):
    """A write-only text sink that counts writes (xlrd's logfile): the text is discarded at once."""

    def __init__(self):
        self.n_writes = 0

    def writable(self):
        return True

    def write(self, s):
        self.n_writes += 1
        return len(s)


# ----------------------------------------------------------------------------------------------------------------
# section 8 "Screening"
# ----------------------------------------------------------------------------------------------------------------
_PATH_SPLIT = re.compile(r"[\\/]+")


def screen(s: str, pg) -> dict:
    """The frozen guard's id_value_hits (V), ID_WORDING (N) and BARE_SUBJECT (N) on a carrier-derived string, in
    memory: each path component is searched whole (id_value_hits tokenises itself and also searches the space-joined
    forms; ID_WORDING spans separators), and BARE_SUBJECT is matched against every token of every component (the
    guard's TOKEN_SPLIT, then also split on '.', '_' and '-'). Returns {"V": n, "N": n} only."""
    v = n = 0
    for comp in _PATH_SPLIT.split(s or ""):
        if not comp:
            continue
        v += len(pg.id_value_hits(comp))
        if pg.ID_WORDING.search(comp):
            n += 1
        toks = set()
        for t in pg.TOKEN_SPLIT.split(comp):
            if t:
                toks.add(t)
                toks.update(x for x in re.split(r"[._\-]+", t) if x)
        n += sum(1 for t in toks if pg.BARE_SUBJECT.match(t))
    return {"V": v, "N": n}
