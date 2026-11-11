"""Child process of tests/test_wp3_phase1.py's real-stderr checks (WP3 fix round 1, A1 / A2). SYNTHETIC stand-ins only.

    python -X utf8 -m a1_audit.tests.wp3_child <mode> <roots.json> <order>

order: 'preimport' imports nibabel, pdfplumber and pdfminer before anything else (nibabel's own StreamHandler is
bound to the REAL stderr; pdfminer's loggers have none and reach logging.lastResort); 'lazy' imports none of them
explicitly. The parent captures this process's real stdout and stderr: stderr must stay empty and
stdout may hold only the stage's print-rule lines and one 'RESULT <json>' line.

modes:
  fe_stage    fetch_extract.run_target on the two Segura stand-ins with a reader that parses the NIfTI, WITHOUT
              importing wp3_material / real_sources (with order 'lazy', nibabel is first imported INSIDE the stage)
  stage       wp3_material.run_material on the stand-ins (scratch network)
  use         WP3Sources.map on rows 1 / 2 and run.dry_dispatch on rows 1 / 2 after phase 2 (identity at use and the
              recomputation inside section 8's handler)
  use_repro   wp3_repro.row_reproduction on row 1 and run.prepare on row 1 (as run.execute calls them)
  hook        privacy_wrap.install_excepthook, then an uncaught FileNotFoundError whose message names a carrier path
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

mode, roots_json, order = sys.argv[1], sys.argv[2], sys.argv[3]
if order == "preimport":
    import nibabel  # noqa: F401
    import pdfminer.pdfinterp  # noqa: F401
    import pdfplumber  # noqa: F401

from a1_audit import fetch_extract as FE  # noqa: E402

FE.PG.HGNC_FILE = Path(roots_json).parent / "no_such_hgnc_table.txt"
FE.PG._HGNC = frozenset(("PTEN",))
from a1_audit import wp3_layout as L  # noqa: E402

out = {}
if mode == "hook":
    from a1_audit import privacy_wrap as PW
    PW.install_excepthook("wp3_child")
    raise FileNotFoundError(2, "No such file", r"E:\data\asdg\segura2025\image_790618_secret_name.nii.nii.gz")
roots = L.Roots.from_spec(json.loads(Path(roots_json).read_text(encoding="utf-8")))
if mode == "fe_stage":
    from a1_audit import identity as ID  # noqa: F401
    from a1_audit import reparcel as RP
    out["nibabel_imported_before_stage"] = "nibabel" in sys.modules
    idrefs = L.identity_records(roots, lambda p: Path(p).read_bytes())
    for image in L.SEGURA_IMAGES:
        k = L.SEGURA_MAP_KEY[image]
        r = idrefs[k]
        t = FE.Target(key=k, gate="ungated", url=r["url"], kind="file", ext=".nii.gz", refs=tuple(r["refs"]),
                      local_path=r["local_path"])

        def reader(path):
            img = RP.nifti_from_bytes(Path(path).read_bytes())
            return {"shape": {"n": int(len(img.shape))}}
        res = FE.run_target(t, roots.fe_roots(), out=sys.stdout, reader=reader)
        rec = json.loads(Path(res["record_path"]).read_bytes()) if res.get("record_path") else {}
        out[k] = dict(status=res["status"], stdio_violations=rec.get("stdio_violations"), logging=rec.get("logging"))
elif mode == "stage":
    from a1_audit import wp3_material as WM
    from a1_audit import wp3_scratch as SC
    with SC.scratch_net(roots):
        res = WM.run_material(roots, out=sys.stdout, run_info={"mode": "scratch (synthetic stand-ins; no launch)"})
    for k in L.SEGURA_MAP_KEY.values():
        e = res["entries"].get(k) or {}
        rec = json.loads((Path(roots.records) / e["record_path"]).read_bytes()) if e.get("record_path") else {}
        out[k] = dict(status=e.get("status"), stdio_violations=rec.get("stdio_violations"), logging=rec.get("logging"))
    e = res["entries"].get(L.MOESM2_KEY) or {}
    rec = json.loads((Path(roots.records) / e["record_path"]).read_bytes()) if e.get("record_path") else {}
    out[L.MOESM2_KEY] = dict(status=e.get("status"), readback=e.get("readback"),
                             readback_logging=(e.get("readback_guard") or {}).get("logging"),
                             readback_stdio_violations=(e.get("readback_guard") or {}).get("stdio_violations"),
                             first_parse_logging=rec.get("logging"), first_parse_stdio_violations=rec.get("stdio_violations"))
    out["manifest"] = res["status"]
elif mode in ("use", "use_repro"):
    from a1_audit import real_sources as RS
    from a1_audit import run as R
    rows = {r.row: r for r in R.register_for_diagnostics(R.REPO)}
    src = RS.WP3Sources(roots)
    if mode == "use":
        for n in (1, 2):
            try:
                src.map(R.classify(rows[n], frozenset()), 0)
                out[f"map {n}"] = "ok"
            except R.SourceUnavailable as e:
                out[f"map {n}"] = e.status
        recs = R.dry_dispatch([rows[1], rows[2]], frozenset(), plant_view=False, sources=RS.WP3Sources(roots))
        out["dry"] = [f"{r['outcome']}: {r['status']}" for r in recs]
    else:
        from a1_audit import wp3_repro as WR
        try:
            WR.row_reproduction(R.classify(rows[1], frozenset()), src)
            out["repro 1"] = "ok"
        except R.SourceUnavailable as e:
            out["repro 1"] = e.status
        try:
            R.prepare(R.classify(rows[1], frozenset()), RS.WP3Sources(roots), 0)
            out["prepare 1"] = "ok"
        except R.SourceUnavailable as e:
            out["prepare 1"] = e.status
    out["stage_lines"] = len(src.stage_lines)
sys.stdout.write("RESULT " + json.dumps(out, sort_keys=True) + "\n")
