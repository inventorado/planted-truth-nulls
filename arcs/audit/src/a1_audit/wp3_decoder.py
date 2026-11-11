"""WP3: the NeuroVault decoder's attempts, decided once (RUN_PLAN_amend_3.md v2.1, FROZEN sha256 da3f3b8b..., R45 (e)-(h)).

Per image, in the material stage, after every identity and pin check (R50, B8):
  0 the attempt records are read FIRST: <control>/ungated/segura_decoder_<id>_attempt<k>.json (the start record, written
    before each GET) and ..._attempt<k>_outcome.json (written after it); never overwritten (FE9).
  1 crash traces stop the stage for the operator (a stop does not make the decoder unavailable): a carrier.json.a<k>.part
    (or the plain carrier.json.part) with no attempt record; a start record with no outcome record; a carrier.json on
    disk whose SOURCE.md (this stage's) does not record its sha256. A .part whose attempt has an outcome record is
    accounted for: its size and sha256 are recorded, it is never read or parsed, it does not stop the stage.
  2 decided once: an 'extracted' outcome -> the decoder's object; a 'final refusal' or 'size mismatch' outcome, or three
    'transport failure (counted)' outcomes over all runs -> unavailable, with no new request in this or any later run.
  3 the size probe, once per image per run, before that run's first GET: a HEAD of the image's NeuroVault file_url; a
    200 whose Content-Length differs from the pre-freeze record's -> 'size mismatch' (unavailable); any other status,
    no size or a failed HEAD -> 'no size returned': the fetch proceeds and the status code is recorded (fix round 3,
    B2); Last-Modified recorded and, if it differs from the pre-freeze value, labelled (never refused). Declared
    blind spots (R45 (e)): equal size is not equal bytes; the decoder reads NeuroVault's cached reduced representation.
  4 up to 3 attempts (transport failures only), counted across runs; fixed waits of 10 and 30 minutes between attempts
    in a run (SLEEP, replaced by a mocked clock in the tests); each attempt writes carrier.json.a<k>.part (k = 1, 2, ...;
    a 'stopped' attempt takes a k and is not counted); fetch_extract renames it to carrier.json after its read-back.
  Every file this module hashes (a .part, a carrier.json) and the HEAD run inside privacy_wrap.guarded_stage, the
  guards run_target uses (fix round 3, A1 audit); a hashing failure stops the stage for the operator.
  Classification (in memory; no message text is stored): fetch_util.get raises CalledProcessError (curl exit code),
  RuntimeError 'HTTP <code> for <url>' (code parsed) or RuntimeError for an HTML page (fetch_extract records class and
  number only). Transport: curl 6, 7, 18, 28, 35, 52, 55, 56; HTTP 429; HTTP 5xx. Any other curl exit: 'stopped (local
  fault; not counted)' and the stage stops. Any other HTTP status, an HTML page, a declared read refused (read:file):
  'final refusal'. Printed on a failure: the class name, the stage, the raising line and the curl exit / HTTP status.
"""
from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

from . import fetch_extract as FE
from . import identity as ID
from . import privacy_wrap as PW
from . import wp3_layout as L

TRANSPORT_CURL = (6, 7, 18, 28, 35, 52, 55, 56)
MAX_ATTEMPTS = 3
WAITS = (600, 1800)              # seconds: after the first attempt of a run, after the second
SLEEP = time.sleep               # the tests replace it by a recording clock

OUT_EXTRACTED = "extracted"
OUT_FINAL = "final refusal"
OUT_TRANSPORT = "transport failure (counted)"
OUT_SIZE = "size mismatch"
OUT_STOPPED = "stopped (local fault; not counted)"
OUTCOMES = (OUT_EXTRACTED, OUT_FINAL, OUT_TRANSPORT, OUT_SIZE, OUT_STOPPED)
UNAVAILABLE = "decoder unavailable (R45 (e)): %s; R22's fallback applies"
UNAVAILABLE_PREFIX = UNAVAILABLE.split("%s")[0]
STOP_TRACE = "stopped for the operator: a crash trace of an earlier attempt (R45 (f))"
STOP_LOCAL = "stopped for the operator: a local fault (R45 (f); no attempt counted)"
STOP_FOREIGN = "stopped for the operator: a carrier.json without this stage's SOURCE.md sha256 (R45 (h))"
LM_LABEL = "the NeuroVault image's Last-Modified differs from the pre-freeze record"
NO_SIZE = ("no size returned (a status other than 200, an html page, no Content-Length, or a failed HEAD): the fetch "
           "proceeds")
STOP_HASH = "stopped for the operator: a file of an earlier attempt could not be hashed (R45 (f))"
STATUSES = (STOP_TRACE, STOP_LOCAL, STOP_FOREIGN, LM_LABEL, NO_SIZE, STOP_HASH) + tuple(UNAVAILABLE % o for o in OUTCOMES) + \
    (UNAVAILABLE % "three transport failures",)


class StageStop(Exception):
    """The stage stops for the operator (status: one of STOP_*); nothing is decided."""

    def __init__(self, status: str):
        super().__init__(status)
        self.status = status


def classify(rec: dict) -> dict:
    """The outcome of one attempt from fetch_extract's R18 record of it (status, failed stage, fetch_failure)."""
    st, stage = rec.get("status"), rec.get("failed_stage")
    ff = rec.get("fetch_failure") or {}
    out = dict(stage=stage, failed_class=rec.get("failed_class"), where=rec.get("failed_where"),
               curl_exit=ff.get("curl_exit"), http_status=ff.get("http_status"), html=bool(ff.get("html")))
    if st == FE.STATUS_EXTRACTED:
        return dict(out, outcome=OUT_EXTRACTED)
    if stage == "fetch:get":
        if out["curl_exit"] is not None:
            return dict(out, outcome=OUT_TRANSPORT if int(out["curl_exit"]) in TRANSPORT_CURL else OUT_STOPPED)
        if out["http_status"] is not None:
            code = int(out["http_status"])
            return dict(out, outcome=OUT_TRANSPORT if (code == 429 or 500 <= code <= 599) else OUT_FINAL)
        if out["html"]:
            return dict(out, outcome=OUT_FINAL)
        return dict(out, outcome=OUT_STOPPED)       # a download record / read-back fault: the operator's
    if stage in ("read:file", "transform"):
        return dict(out, outcome=OUT_FINAL)         # the declared read refused (R45 (e)): the fallback applies
    return dict(out, outcome=OUT_STOPPED)


def _gate(roots) -> str:
    """WP4 (G2): the gate folder of the attempt records - a WP4 layout names its own (wp4_layout.Roots.decoder_gate);
    a WP3 layout is ungated, as before."""
    return getattr(roots, "decoder_gate", L.GATE)


def _paths(roots: L.Roots, key: str, k: int) -> tuple[Path, Path, Path]:
    c = Path(roots.control) / _gate(roots)
    return (c / f"{key}_attempt{k}.json", c / f"{key}_attempt{k}_outcome.json",
            Path(roots.data) / key / f"carrier.json.a{k}.part")


def read_attempts(roots: L.Roots, key: str) -> list[dict]:
    """Every attempt k with its start / outcome records (parsed) and its .part's existence, in k order."""
    c = Path(roots.control) / _gate(roots)
    ks = set()
    if c.is_dir():
        for p in c.glob(f"{key}_attempt*.json"):
            mid = p.name[len(f"{key}_attempt"):-len(".json")]
            mid = mid[:-len("_outcome")] if mid.endswith("_outcome") else mid
            if mid.isdigit():
                ks.add(int(mid))
    kdir = Path(roots.data) / key
    if kdir.is_dir():
        for p in kdir.glob("carrier.json.a*.part"):
            mid = p.name[len("carrier.json.a"):-len(".part")]
            if mid.isdigit():
                ks.add(int(mid))
    out = []
    for k in sorted(ks):
        s, o, part = _paths(roots, key, k)
        out.append(dict(k=k, start=json.loads(s.read_bytes()) if s.exists() else None,
                        outcome=json.loads(o.read_bytes()) if o.exists() else None, part=part.exists()))
    return out


def _source_md_records(kdir: Path, sha: str) -> bool:
    src = kdir / "SOURCE.md"
    if not src.exists():
        return False
    return f"- sha256: {sha}" in src.read_text(encoding="utf-8").splitlines()


def crash_traces(roots: L.Roots, key: str, atts: list[dict]) -> list[str]:
    """Trace kinds (fixed vocabulary; no path is returned)."""
    tr = []
    kdir = Path(roots.data) / key
    if (kdir / "carrier.json.part").exists():
        tr.append("a .part without an attempt record")
    for a in atts:
        if a["part"] and a["start"] is None:
            tr.append("a .part without an attempt record")
        if a["start"] is not None and a["outcome"] is None:
            tr.append("a start record without an outcome record")
        if a["outcome"] is not None and a["start"] is None:
            tr.append("an outcome record without a start record")
    return tr


def decided(atts: list[dict]) -> tuple[str | None, dict | None]:
    """(None | 'extracted' | 'unavailable', the deciding outcome record)."""
    n_tr = 0
    for a in atts:
        o = (a["outcome"] or {}).get("outcome")
        if o == OUT_EXTRACTED:
            return "extracted", a["outcome"]
        if o in (OUT_FINAL, OUT_SIZE):
            return "unavailable", a["outcome"]
        if o == OUT_TRANSPORT:
            n_tr += 1
            if n_tr >= MAX_ATTEMPTS:
                return "unavailable", dict(a["outcome"], outcome="three transport failures")
    return None, None


def n_transport(atts: list[dict]) -> int:
    return sum(1 for a in atts if (a["outcome"] or {}).get("outcome") == OUT_TRANSPORT)


def size_probe_of(head: dict, ref: dict, failure: dict | None = None) -> dict:
    """R45 (e) on one HEAD answer of the image's file_url: ONLY a 200 whose Content-Length differs from the pre-freeze
    record is a size mismatch (fix round 3, B2). Any other status (503, 429, 404 ...), a missing size or a failed HEAD
    reads 'no size returned' (identity not established): the fetch proceeds and the record keeps the status code.
    Last-Modified (a 200 only) is recorded and labelled when it differs from the pre-freeze value; never refused."""
    code = head.get("status_code")
    ref_bytes = int(ref["content_length"])
    ctype = head.get("content_type_label")
    # fix round 4, item 4: a 200 that is an HTML page (a challenge or an error page) carries no size of the image
    if failure is None and code == 200 and ctype != FE.CONTENT_TYPE_HTML:
        sp = ID.size_probe(head, ref_bytes)
        out = dict(status_code=code, content_length=sp["content_length"], ref_bytes=ref_bytes, result=sp["result"])
        lm = head.get("last_modified")
        out.update(last_modified=lm, last_modified_prefreeze=ref.get("last_modified"))
        if lm is not None and ref.get("last_modified") is not None and lm != ref["last_modified"]:
            out["label"] = LM_LABEL
    else:
        out = dict(status_code=code, content_length=None, ref_bytes=ref_bytes, result=ID.STATUS_NOT_ESTABLISHED,
                   reading=NO_SIZE, last_modified=None, last_modified_prefreeze=ref.get("last_modified"))
    out["content_type_label"] = ctype
    if failure is not None:
        out["head_failure"] = dict(failure)
    return out


def size_probe(em: PW.Emitter, file_url: str, ref: dict) -> dict:
    """The HEAD inside the guards run_target uses (fix round 3, A1 audit): a failed HEAD is 'no size returned'."""
    try:
        head, _ = PW.guarded_stage(em, "fetch:size-probe", FE.NET["head"], file_url)
        return size_probe_of(head if isinstance(head, dict) else {}, ref)
    except PW.StageFailed as e:
        return size_probe_of({}, ref, {"class": e.class_name, "stage": e.stage, "where": e.where})


def _write_record(em: PW.Emitter, path: Path, rec: dict) -> str:
    if path.exists():
        raise FileExistsError("an attempt record exists (FE9: never overwritten)")
    if isinstance(rec.get("part"), str):
        em.allow.add_exact(rec["part"])            # the runner-built .part name
    if isinstance(rec.get("record_path"), str):
        em.allow.add_exact(rec["record_path"])     # fetch_extract's runner-built R18 record path
    em.allow.add_exact(path, path.name)            # a runner-built name
    return PW.stage(em, "record", em.write_json, path, rec, "identity")


def _part_facts(part: Path, em: PW.Emitter | None = None) -> dict:
    """A .part's size and sha256 (hashed, never parsed), inside the guards (fix round 3, A1 audit)."""
    def facts():
        if not part.exists():
            return {"exists": False}
        return {"exists": True, "bytes": part.stat().st_size, "sha256": PW.sha256_file(part)}
    if em is None:
        return facts()
    try:
        return PW.guarded_stage(em, "identity", facts)[0]
    except PW.StageFailed:
        raise StageStop(STOP_HASH) from None


def _carrier_foreign(kdir: Path, em: PW.Emitter) -> bool:
    """R45 (h): a carrier.json on disk whose SOURCE.md (this stage's) does not record its sha256 (hashed inside the
    guards; never parsed here)."""
    carrier = kdir / "carrier.json"

    def check():
        if not carrier.exists():
            return False
        return not _source_md_records(kdir, PW.sha256_file(carrier))
    try:
        return PW.guarded_stage(em, "identity", check)[0]
    except PW.StageFailed:
        raise StageStop(STOP_HASH) from None


def run_decoder(roots: L.Roots, image: int, target: FE.Target, reader, em: PW.Emitter, *, out=None,
                prefreeze: dict, utc_now, key: str | None = None) -> dict:
    """One image's decoder, decided once. Returns the manifest entry: the extracted attempt's record (adopted or
    new), or {'status': UNAVAILABLE % reason, 'final': True, ...}. Raises StageStop on a crash trace or a local fault."""
    key = key or L.SEGURA_DECODER_KEY[image]     # WP4: Leyhausen's decoders name their own keys
    kdir = Path(roots.data) / key
    atts = read_attempts(roots, key)
    tr = crash_traces(roots, key, atts)
    if tr:
        em.say(f"wp3_material: {key} {STOP_TRACE}; traces {len(tr)}")
        raise StageStop(STOP_TRACE)
    for a in atts:                           # accounted for: size and sha256 only
        if a["part"]:
            pf = _part_facts(_paths(roots, key, a["k"])[2], em)
            em.say(f"wp3_material: {key} attempt {a['k']} partial file accounted for: bytes {pf['bytes']} sha256 "
                   f"{pf['sha256']}; never read")
    if _carrier_foreign(kdir, em):
        em.say(f"wp3_material: {key} {STOP_FOREIGN}")
        raise StageStop(STOP_FOREIGN)
    how, rec = decided(atts)
    if how == "extracted":
        return dict(adopt_record=rec.get("record_path"), outcome=rec, attempts=len(atts))
    if how == "unavailable":
        em.say(f"wp3_material: {key} {UNAVAILABLE % rec['outcome']} (decided in an earlier attempt; no request)")
        return dict(status=UNAVAILABLE % rec["outcome"], final=True, refusing_stage=rec.get("stage"),
                    unavailable_reason=rec["outcome"], attempts_recorded=len(atts),
                    transport_failures=n_transport(atts))
    # undecided: the size probe once in this run, before its first GET
    next_k = (max(a["k"] for a in atts) + 1) if atts else 1
    probe = size_probe(em, prefreeze["file_url"], prefreeze)
    em.say(f"wp3_material: {key} size probe: HTTP status {probe['status_code'] if probe['status_code'] is not None else 'none'}; "
           f"{probe['result']}; content length "
           f"{probe['content_length'] if probe['content_length'] is not None else 'none'} vs pre-freeze "
           f"{probe['ref_bytes']}" + (f"; {probe['label']}" if probe.get("label") else ""))
    if probe["result"] == ID.STATUS_CHANGED:
        s, o, part = _paths(roots, key, next_k)
        _write_record(em, s, dict(schema="a1_wp3_decoder_attempt_v1", key=key, k=next_k, date_utc=utc_now(),
                                  part=part.name, size_probe=probe, get="not made (size mismatch)"))
        orec = dict(schema="a1_wp3_decoder_outcome_v1", key=key, k=next_k, date_utc=utc_now(), outcome=OUT_SIZE,
                    stage="fetch:size-probe", size_probe=probe, part=_part_facts(part, em))
        _write_record(em, o, orec)
        return dict(status=UNAVAILABLE % OUT_SIZE, final=True, refusing_stage="fetch:size-probe",
                    unavailable_reason=OUT_SIZE, attempts_recorded=len(atts) + 1,
                    transport_failures=n_transport(atts))
    n_run = 0
    k = next_k
    counted = n_transport(atts)
    while counted < MAX_ATTEMPTS:
        if n_run >= 1:
            SLEEP(WAITS[min(n_run - 1, len(WAITS) - 1)])
        s, o, part = _paths(roots, key, k)
        if part.exists() or s.exists() or o.exists():
            em.say(f"wp3_material: {key} {STOP_TRACE}; attempt {k} name exists without its records")
            raise StageStop(STOP_TRACE)
        _write_record(em, s, dict(schema="a1_wp3_decoder_attempt_v1", key=key, k=k, date_utc=utc_now(),
                                  part=part.name, size_probe=probe if n_run == 0 else "made once in this run"))
        res = FE.run_target(dataclasses.replace(target, part_name=part.name), roots.fe_roots(), out=out, reader=reader,
                            adopt_identical=True)
        frec = json.loads(Path(res["record_path"]).read_bytes()) if res.get("record_path") else {}
        c = classify(frec) if frec else dict(outcome=OUT_STOPPED, stage=None, failed_class=None, where=None,
                                             curl_exit=None, http_status=None, html=False)
        orec = dict(schema="a1_wp3_decoder_outcome_v1", key=key, k=k, date_utc=utc_now(), **c,
                    record_path=res.get("record_path"), part=_part_facts(part, em))
        _write_record(em, o, orec)
        num = (f"; curl exit {c['curl_exit']}" if c.get("curl_exit") is not None else "") + \
              (f"; HTTP status {c['http_status']}" if c.get("http_status") is not None else "")
        em.say(f"wp3_material: {key} attempt {k} outcome {c['outcome']}" +
               (f"; class {c['failed_class']}; stage {c['stage']}; at {c['where']}" if c.get("failed_class") else "")
               + num)
        n_run += 1
        k += 1
        if c["outcome"] == OUT_EXTRACTED:
            return dict(adopt_record=res.get("record_path"), outcome=orec, attempts=len(atts) + n_run)
        if c["outcome"] == OUT_FINAL:
            return dict(status=UNAVAILABLE % OUT_FINAL, final=True, refusing_stage=c.get("stage"),
                        unavailable_reason=OUT_FINAL, attempts_recorded=len(atts) + n_run,
                        transport_failures=counted, record_path_last=res.get("record_path"))
        if c["outcome"] == OUT_STOPPED:
            em.say(f"wp3_material: {key} {STOP_LOCAL}")
            raise StageStop(STOP_LOCAL)
        counted += 1
    return dict(status=UNAVAILABLE % "three transport failures", final=True, refusing_stage="fetch:get",
                unavailable_reason="three transport failures", attempts_recorded=len(atts) + n_run,
                transport_failures=counted)
