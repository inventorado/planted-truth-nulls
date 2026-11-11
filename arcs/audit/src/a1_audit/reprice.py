"""RUN_PLAN §14 repricing of the G2 and G1 blocks from the measured WP3 (ungated) ratios (pre-WP4, §17; bench
ev-1a13e2bfff7bdb6: "G2 / G1 must be repriced and the pause implemented before WP4").

    python -X utf8 -m a1_audit.reprice [--check]

Inputs (read only; nothing is recomputed):
- RUN_PLAN.md (FROZEN, sha256 16c60232...) §14's table lines (asserted verbatim): ungated verdict ~21 / descriptor ~29,
  G2 verdict ~22 / descriptor ~97, G1 ~177 (no pass split), sensitivity "<= the verdict passes";
- the ungated run's row records results/a1_run/ungated/<pass>/row_*.json (memory.seconds: the row tasks' process-s)
  and its checkpoints artifacts/audit/a1_run/ungated/<pass>/**/ck_*.json (payload._meta.seconds: every task, the G6l
  screens included - the quantity the runner's pause counts, pace.py); the row tasks' sum is asserted equal in both;
- each pass's run.log (wall time of the pass and of its phase 2).

Rule: ratio(pass) = measured checkpoint process-h / §14 ungated estimate of that pass; the repriced estimate of a block
= its §14 estimate x the ratio of its pass; the pause threshold = PAUSE_FACTOR x the repriced estimate (pace.py). G1 has
no per-pass §14 estimate, so its range is given (all at the verdict ratio .. all at the descriptor ratio) and NO pause
estimate is pinned: a G1 pass is refused until §12 :1536-1538's repricing before WP5.
Writes arcs/audit/run_manifests/reprice_wp4.json (+ .md), read back. --check recomputes and compares (no write).
"""
from __future__ import annotations

import datetime as _dt
import glob
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from . import pace as PACE

REPO = Path(__file__).resolve().parents[4]
PLAN = REPO / "arcs/audit/RUN_PLAN.md"
PLAN_SHA256 = "16c6023296fab612c34155e40d271c37258627980f12d00794e0fc09e1533823"
PLAN_LINES = {   # RUN_PLAN.md line: the frozen text the estimates come from
    1557: "- **Uncertainty:** estimates may be off by about 2×.",
    1565: "| ungated (verdict ≈ 21 / descriptor ≈ 29) | ≈ 50 | ≈ 2.7 |",
    1566: "| G2 (verdict ≈ 22 / descriptor ≈ 97) | ≈ 118 | ≈ 6.3 |",
    1567: "| G1 (without the SZ rows' infeasible legs; repriced before WP5) | ≈ 177 | ≈ 9.5 |",
    1568: "| ≥ 2-donor sensitivity (R11): the verdict legs again, only for classes whose parcel set changes | ≤ the verdict "
          "passes (≤ ≈ 21 / 22 / G1's) | — |",
    1577: "- **Overrun:** at more than 2× the block estimate the run pauses at the next checkpoint and reports. Nothing is "
          "dropped.",
}
PLAN_EST = {("ungated", "verdict"): 21.0, ("ungated", "descriptor"): 29.0, ("ungated", "sensitivity"): 21.0,
            ("G2", "verdict"): 22.0, ("G2", "descriptor"): 97.0, ("G2", "sensitivity"): 22.0}
G1_TOTAL = 177.0
EFFECTIVE_JOBS_PLAN = 18.75   # §14 "wall-h (≈ 18.75 jobs)"
PASSES = ("verdict", "descriptor", "sensitivity")
RESULTS = REPO / "arcs/audit/results/a1_run/ungated"
CKS = REPO / "artifacts/audit/a1_run/ungated"
OUT_JSON = REPO / PACE.ESTIMATES_REL
OUT_MD = OUT_JSON.with_suffix(".md")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def git(*a) -> str:
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True).stdout.strip()


def plan_check() -> None:
    data = PLAN.read_bytes()
    if sha(data.replace(b"\r\n", b"\n")) != PLAN_SHA256:
        raise SystemExit("RUN_PLAN.md differs from its frozen sha256")
    lines = data.decode("utf-8").splitlines()
    for n, text in PLAN_LINES.items():
        if not lines[n - 1].startswith(text):
            raise SystemExit(f"RUN_PLAN.md:{n} is not the quoted §14 text")


def _clock(line: str) -> int | None:
    m = re.match(r"\[(\d\d):(\d\d):(\d\d)\]", line)
    return None if m is None else int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3])


def wall(log_text: str) -> dict:
    """Wall seconds of the pass (first line -> first 'done:' line) and of its phase 2 (the 'phase 2:' line -> 'done:'),
    days rolled over where the clock decreases."""
    t, prev, day, marks = [], None, 0, {}
    for ln in log_text.splitlines():
        c = _clock(ln)
        if c is None:
            continue
        if prev is not None and c < prev:
            day += 86400
        prev = c
        x = c + day
        t.append(x)
        if "phase 2:" in ln and "phase2" not in marks:
            marks["phase2"] = x
        if "] done:" in ln and "done" not in marks:
            marks["done"] = x
    return dict(pass_s=marks["done"] - t[0], phase2_s=marks["done"] - marks["phase2"])


def measured(pass_: str) -> dict:
    rows, row_s = 0, 0.0
    files = sorted(glob.glob(str(RESULTS / pass_ / "row_*.json")))
    hashes = []
    for f in files:
        b = Path(f).read_bytes()
        hashes.append(sha(b))
        if f.endswith(("_repro.json", "_rlm.json")):
            continue
        d = json.loads(b.decode("utf-8"))
        rows += 1
        row_s += float((d.get("memory") or {}).get("seconds") or 0.0)
    groups: dict = {}
    nostat_s = 0.0   # form tasks whose row was written without a statistic carry no memory record in the row file
    for f in glob.glob(str(CKS / pass_ / "**" / "ck_*.json"), recursive=True):
        d = json.loads(Path(f).read_bytes().decode("utf-8"))
        k = d["key"]
        g = "g6l screens" if k.startswith("g6l") else ("form rows" if k.endswith("_form") else k.split("_")[-1])
        meta = (d.get("payload") or {}).get("_meta") or {}
        n, s = groups.get(g, (0, 0.0))
        groups[g] = (n + 1, s + float(meta.get("seconds") or 0.0))
        if g == "form rows" and (d.get("payload") or {}).get("outcome") != "computed":
            nostat_s += float(meta.get("seconds") or 0.0)
    ck_total = sum(s for _, s in groups.values())
    ck_rows = sum(s for g, (_, s) in groups.items() if g != "g6l screens") - nostat_s
    if abs(ck_rows - row_s) > 1e-6 * max(1.0, row_s):   # apparatus: the two record kinds agree on the row tasks
        raise SystemExit(f"{pass_}: row records {row_s} s != checkpoints' row tasks {ck_rows} s")
    w = wall((RESULTS / pass_ / "run.log").read_text(encoding="utf-8"))
    summ = (RESULTS / pass_ / "RUN_SUMMARY.json").read_bytes()
    return dict(row_records=rows, row_tasks_process_h=row_s / 3600.0, checkpoint_process_h=ck_total / 3600.0,
                checkpoint_groups={g: dict(tasks=n, process_h=s / 3600.0) for g, (n, s) in sorted(groups.items())},
                wall_h=w["pass_s"] / 3600.0, phase2_wall_h=w["phase2_s"] / 3600.0,
                phase2_effective_jobs=(ck_total - groups.get("g6l screens", (0, 0.0))[1]
                                       - (groups.get("form rows", (0, 0.0))[1] if pass_ == "descriptor" else 0.0))
                / max(w["phase2_s"], 1),
                inputs=dict(row_files=len(files), row_files_sha256_of_sha256s=sha("".join(hashes).encode("ascii")),
                            run_summary_sha256=sha(summ),
                            committed_in=git("log", "-1", "--format=%H", "--", f"arcs/audit/results/a1_run/ungated/{pass_}"),
                            checkpoints="artifacts/audit/a1_run/ungated/%s (gitignored; _meta.seconds)" % pass_))


def build() -> dict:
    plan_check()
    m = {p: measured(p) for p in PASSES}
    ratio = {p: m[p]["checkpoint_process_h"] / PLAN_EST[("ungated", p)] for p in PASSES}
    ratio_rows = {p: m[p]["row_tasks_process_h"] / PLAN_EST[("ungated", p)] for p in PASSES}
    blocks = {}
    for (gate, p), est in PLAN_EST.items():
        rep = est * ratio[p]
        blocks[f"{gate}/{p}"] = dict(
            plan_estimate_process_h=est, plan_line=1565 if gate == "ungated" and p != "sensitivity" else
            (1566 if gate == "G2" and p != "sensitivity" else 1568),
            ratio_applied=ratio[p], ratio_source=f"ungated {p}: measured {m[p]['checkpoint_process_h']:.3f} / "
                                                  f"{PLAN_EST[('ungated', p)]:g}",
            repriced_process_h=rep, pause_estimate_process_h=rep,
            pause_threshold_process_h=PACE.PAUSE_FACTOR * rep,
            repriced_wall_h_at_plan_jobs=rep / EFFECTIVE_JOBS_PLAN)
    # the descriptor ratio without the form rows (what item 3 could at most remove): the Liu rows' own process-h
    d = m["descriptor"]
    forms_h = d["checkpoint_groups"].get("form rows", {}).get("process_h", 0.0)
    ratio_d_ex = (d["checkpoint_process_h"] - forms_h) / PLAN_EST[("ungated", "descriptor")]
    blocks["G2/descriptor"]["alternative_ex_form_rows"] = dict(
        ratio=ratio_d_ex, repriced_process_h=PLAN_EST[("G2", "descriptor")] * ratio_d_ex,
        pause_threshold_process_h=PACE.PAUSE_FACTOR * PLAN_EST[("G2", "descriptor")] * ratio_d_ex,
        note="the ungated descriptor block without its 7 form-row tasks (the Liu rows): not pinned")
    g1 = dict(plan_estimate_process_h=G1_TOTAL, plan_line=1567, pause_estimate_process_h=None,
              range_all_at_verdict_ratio_process_h=G1_TOTAL * ratio["verdict"],
              range_all_at_descriptor_ratio_process_h=G1_TOTAL * ratio["descriptor"],
              note="§14 gives G1 no verdict / descriptor split; §12 (RUN_PLAN.md:1536-1538) reprices G1 before WP5; "
                   "no pause estimate is pinned, so the runner refuses a G1 pass until then")
    for p in PASSES:
        blocks[f"G1/{p}"] = dict(g1)
    return dict(
        what="A1 §14 block estimates repriced from the WP3 (ungated) measurements (pre-WP4; a1_audit.reprice)",
        script="arcs/audit/src/a1_audit/reprice.py", generated_at_head=git("rev-parse", "HEAD"),
        generated_utc=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        plan=dict(file="arcs/audit/RUN_PLAN.md", sha256=PLAN_SHA256, lines_quoted=PLAN_LINES),
        rule=("ratio(pass) = measured checkpoint process-h of the ungated pass / its §14 estimate; repriced = §14 "
              "estimate x ratio of the same pass; pause threshold = %g x repriced (pace.PAUSE_FACTOR; RUN_PLAN.md:1577)"
              % PACE.PAUSE_FACTOR),
        why_checkpoint_process_h=("the pause counts every checkpointed task (pace.py); the row records' memory.seconds "
                                  "omit the G6l screen tasks (verdict / sensitivity), so the checkpoint sum is used; "
                                  "the row-record ratio is given beside it"),
        why_descriptor_ratio=("the ungated descriptor overrun is the decoded-list descriptor tasks (Segura's 78 rows "
                              "and MOR-T's 2: 'descriptors' + 'tabs' groups), not the Liu form rows, whose own "
                              "process-h is "
                              f"{forms_h:.2f} of {d['checkpoint_process_h']:.2f}; running the form rows in the pool "
                              "(item 3) shortens the pass's wall time (they ran serially before the pool) but leaves the "
                              "process-h ratio (and so the price) essentially as measured; the raw ratio is pinned"),
        caveat=("the ratios are measured on a decoded-list-dominated ungated block; G2's forms differ (set-vs-map, "
                "PLS-enrichment, signed-weight; Pretzsch's large sets), so its true cost may differ either way; "
                "RUN_PLAN.md:1557 'estimates may be off by about 2x'"),
        measured=m, ratio_checkpoint=ratio, ratio_row_records=ratio_rows, blocks=blocks)


def md_table(doc: dict) -> str:
    b = doc["blocks"]
    out = ["# A1 §14 block estimates repriced from WP3 (GENERATED by a1_audit.reprice; do not hand-edit)", "",
           f"Script `{doc['script']}`, generated at HEAD `{doc['generated_at_head'][:7]}`; inputs: the ungated run "
           f"records (verdict {doc['measured']['verdict']['inputs']['committed_in'][:7]}, descriptor "
           f"{doc['measured']['descriptor']['inputs']['committed_in'][:7]}, sensitivity "
           f"{doc['measured']['sensitivity']['inputs']['committed_in'][:7]}) and their checkpoints; RUN_PLAN.md §14 "
           "(lines 1565-1568, 1577).", "",
           "| block | §14 estimate (process-h) | ratio applied | repriced (process-h) | 2x pause threshold (process-h) |",
           "|---|---:|---:|---:|---:|"]
    for k in ("ungated/verdict", "ungated/descriptor", "ungated/sensitivity", "G2/verdict", "G2/descriptor",
              "G2/sensitivity"):
        e = b[k]
        out.append(f"| {k} | {e['plan_estimate_process_h']:g} | {e['ratio_applied']:.3f} ({k.split('/')[1]}) | "
                   f"{e['repriced_process_h']:.1f} | {e['pause_threshold_process_h']:.1f} |")
    alt = b["G2/descriptor"]["alternative_ex_form_rows"]
    g1 = b["G1/verdict"]
    out += [f"| G2/descriptor without the form rows (not pinned) | 97 | {alt['ratio']:.3f} | "
            f"{alt['repriced_process_h']:.1f} | {alt['pause_threshold_process_h']:.1f} |",
            f"| G1 (all passes; no split in §14) | 177 | .. | {g1['range_all_at_verdict_ratio_process_h']:.1f} .. "
            f"{g1['range_all_at_descriptor_ratio_process_h']:.1f} | none pinned (G1 refused until §12's repricing) |",
            "", "Measured (ungated): " + "; ".join(
                f"{p} {doc['measured'][p]['checkpoint_process_h']:.2f} process-h checkpointed "
                f"({doc['measured'][p]['row_tasks_process_h']:.2f} in the row records), wall {doc['measured'][p]['wall_h']:.2f} h"
                for p in PASSES) + ".", "", doc["why_descriptor_ratio"] + ".", "", doc["caveat"] + "."]
    return "\n".join(out) + "\n"


# ================================================================================================================
# G1 (WP5): RUN_PLAN §12 :1536-1538 "repriced at the measured screen time (§14) before WP5" - bottom-up from the
# measured per-row and per-screen process-seconds of the ungated, G2 primary and G2 amend_5 runs (2026-11-03)
# ================================================================================================================
G1_PLAN_LINES = {
    1536: "**Compute.** About 177 process-h without the four SZ rows (scout model 259 with them), about 9.5 wall-h. Its "
          "dk-ctx rows",
    1550: "    process-s over 2,607 wall-s ≈ 18.75 effective jobs; contention ≈ 2.5–2.6×",
}
G1_OUT_JSON = REPO / "arcs/audit/run_manifests/reprice_wp5.json"
G1_OUT_MD = G1_OUT_JSON.with_suffix(".md")
CONTENTION_20 = 2.5          # RUN_PLAN.md:1550 "contention ≈ 2.5–2.6×" (20 jobs); the lower bound's divisor
MEASURED_RUNS = {            # name: (row records, checkpoints) - every run measured at --jobs 20
    "ungated": ("arcs/audit/results/a1_run/ungated", "artifacts/audit/a1_run/ungated"),
    "G2": ("arcs/audit/results/a1_run/G2", "artifacts/audit/a1_run/G2"),
    "G2_amend5": ("arcs/audit/results/a1_run/rerun_amend5/G2", "artifacts/audit/a1_run/rerun_amend5/G2"),
}
P4_PLANT = "arcs/audit/run_manifests/plants/P4/plant_P4.json"     # plant-mode seconds per form / class (same K)
G1_CLASSES = ("dk-ctx", "V-DK", "V-AAL")


def form_family(route: str) -> str:
    for f in ("PLS-enrichment", "decoded-list", "set-vs-map", "component", "gene-set-only", "signed-weight"):
        if f in route:
            return f
    raise ValueError(f"unknown route {route!r}")


def g1_class(cls: str) -> str:
    """A conditional class ('dk-ctx | V-DK (conditional ...)') is priced at its dearer option, V-DK (41 parcels)."""
    c = str(cls)
    if c.startswith("dk-ctx | V-DK"):
        return "V-DK"
    if c not in G1_CLASSES:
        raise ValueError(f"G1 class {c!r} not priced")
    return c


def measured_run(results_rel: str, cks_rel: str, pass_: str, root: Path = REPO) -> dict:
    """Per-row seconds (row records' memory.seconds; computed rows) by (form family, class), and the checkpointed
    G6l screens. Apparatus (as measured()): the row records' sum equals the checkpoints' row tasks."""
    rows: dict = {}
    row_s = 0.0
    for f in sorted(glob.glob(str(root / results_rel / pass_ / "row_[0-9][0-9][0-9][0-9].json"))):
        d = json.loads(Path(f).read_bytes().decode("utf-8"))
        s = float((d.get("memory") or {}).get("seconds") or 0.0)
        row_s += s
        if d.get("outcome") != "computed":
            continue
        cls = (d.get("inputs") or {}).get("analysis_class")
        rows.setdefault((form_family(str(d.get("route"))), str(cls)), []).append(s)
    groups: dict = {}
    nostat_s = 0.0
    for f in glob.glob(str(root / cks_rel / pass_ / "**" / "ck_*.json"), recursive=True):
        d = json.loads(Path(f).read_bytes().decode("utf-8"))
        k = d["key"]
        g = "g6l screens" if k.startswith("g6l") else ("form rows" if k.endswith("_form") else k.split("_")[-1])
        s = float(((d.get("payload") or {}).get("_meta") or {}).get("seconds") or 0.0)
        n, t = groups.get(g, (0, 0.0))
        groups[g] = (n + 1, t + s)
        if g == "form rows" and (d.get("payload") or {}).get("outcome") != "computed":
            nostat_s += s
    ck_rows = sum(t for g, (_, t) in groups.items() if g != "g6l screens") - nostat_s
    if abs(ck_rows - row_s) > 1e-6 * max(1.0, row_s):
        raise SystemExit(f"{results_rel}/{pass_}: row records {row_s} s != checkpoints' row tasks {ck_rows} s")
    n_scr, s_scr = groups.get("g6l screens", (0, 0.0))
    return dict(rows={f"{k[0]} / {k[1]}": dict(n=len(v), mean_s=sum(v) / len(v), max_s=max(v),
                                                  n_nonzero=sum(1 for x in v if x > 0),
                                                  mean_nonzero_s=(sum(v) / max(1, sum(1 for x in v if x > 0))))
                      for k, v in sorted(rows.items())},
                n_rows_computed=sum(len(v) for v in rows.values()), row_tasks_process_h=row_s / 3600.0,
                screens=n_scr, screen_mean_s=(s_scr / n_scr) if n_scr else None,
                checkpoint_process_h=sum(t for _, t in groups.values()) / 3600.0)


def p4_ratios(root: Path = REPO) -> dict:
    """Plant-mode (P4, same K for every cell) seconds: PLS-enrichment / decoded-list per class, and V-DK / dk-ctx."""
    t = json.loads((root / P4_PLANT).read_bytes().decode("utf-8"))["timing"]
    sec = {k: float(v["mean_seconds"]) for k, v in t.items()}
    need = ("PLS-enrichment / V-AAL", "decoded-list / V-AAL", "PLS-enrichment / dk-ctx", "decoded-list / dk-ctx",
            "decoded-list / V-DK")
    if any(k not in sec for k in need):
        raise SystemExit("P4 plant timing lacks a cell the G1 model needs")
    return {"PLS/dl V-AAL": sec["PLS-enrichment / V-AAL"] / sec["decoded-list / V-AAL"],
            "PLS/dl dk-ctx": sec["PLS-enrichment / dk-ctx"] / sec["decoded-list / dk-ctx"],
            "V-DK/dk-ctx": sec["decoded-list / V-DK"] / sec["decoded-list / dk-ctx"],
            "seconds": {k: sec[k] for k in need},
            "committed_in": git("log", "-1", "--format=%H", "--", P4_PLANT)}


def g1_rows(repo: Path = REPO) -> dict:
    """G1's register rows per pass, (form family, priced class), as the runner classifies them with G1 open
    (run.classify; report_cells.computing_passes; run.FORM_NO_PASS): the register only, no G1 material."""
    sys.path.insert(0, str(repo / "arcs/audit/src"))
    from . import report_cells as RC
    from . import run as R
    rows = [r for r in R.register_for_diagnostics(repo) if r.gate in ("G1", "G1+G2")]
    if sum(1 for r in rows if r.gate == "G1") != 380:          # RUN_PLAN.md §12 "380 rows"; launch.GATE_ROWS
        raise SystemExit("the register's G1 rows are not 380")
    kinds: dict = {}
    out: dict = {p: {} for p in PASSES}
    for r in rows:
        p = R.classify(r, frozenset({"G1"}))
        kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
        if p["kind"] not in ("compute", "form"):
            continue
        for ps in {v for v in RC.computing_passes(p["route"]).values() if v}:
            if (p.get("form_name"), ps) in R.FORM_NO_PASS:
                continue
            k = f"{form_family(p['route'])} / {g1_class(p['analysis_class'])}"
            out[ps][k] = out[ps].get(k, 0) + 1
    return {"by_pass": out, "kinds": kinds, "n_rows": len(rows)}


def _class_mean(meas: dict, pass_: str, fam: str, cls: str, how: str) -> tuple:
    """(seconds per row, source) of a measured (family, class) over the runs: 'pooled' = row-weighted mean over the
    runs that measured it, 'max' = the largest run mean. Sensitivity: rows with 0 s (parcel set unchanged, not
    recomputed) are left out, so every G1 sensitivity row is priced as recomputed."""
    key = f"{fam} / {cls}"
    got = []
    for run, m in meas.items():
        e = m[pass_]["rows"].get(key)
        if e:
            n, mean = (e["n_nonzero"], e["mean_nonzero_s"]) if pass_ == "sensitivity" else (e["n"], e["mean_s"])
            if n:
                got.append((run, n, mean))
    if not got:
        return None, None
    if how == "max":
        run, n, mean = max(got, key=lambda x: x[2])
        return mean, f"{run} {key} (n {n})"
    n = sum(g[1] for g in got)
    return sum(g[1] * g[2] for g in got) / n, " + ".join(f"{g[0]} {key} (n {g[1]})" for g in got)


def g1_unit_costs(meas: dict, ratios: dict, how: str) -> dict:
    """Seconds per G1 row by pass and '<family> / <class>', from measured audit-scale rows:
    decoded-list dk-ctx (G2, G2_amend5) and V-AAL (ungated) as measured; V-DK = dk-ctx x P4's V-DK / dk-ctx;
    PLS-enrichment = decoded-list of the class x P4's PLS / decoded-list; component = G2's measured component
    (fixed) dk-ctx row (x P4's V-DK / dk-ctx for V-DK; x decoded-list V-AAL / dk-ctx as measured for V-AAL)."""
    out: dict = {}
    for ps in PASSES:
        dl = {c: _class_mean(meas, ps, "decoded-list", c, how) for c in ("dk-ctx", "V-AAL")}
        dl["V-DK"] = (dl["dk-ctx"][0] * ratios["V-DK/dk-ctx"], "dk-ctx x P4 V-DK/dk-ctx") if dl["dk-ctx"][0] else \
            (None, None)
        comp = _class_mean(meas, ps, "component", "dk-ctx", how)
        u: dict = {}
        for c in G1_CLASSES:
            if dl[c][0] is None:
                continue
            u[f"decoded-list / {c}"] = (dl[c][0], dl[c][1])
            r = ratios["PLS/dl V-AAL"] if c == "V-AAL" else ratios["PLS/dl dk-ctx"]
            u[f"PLS-enrichment / {c}"] = (dl[c][0] * r, f"decoded-list {c} x P4 PLS/dl {r:.3f}")
            if comp[0] is not None:
                f = 1.0 if c == "dk-ctx" else (ratios["V-DK/dk-ctx"] if c == "V-DK" else dl["V-AAL"][0] / dl["dk-ctx"][0])
                u[f"component / {c}"] = (comp[0] * f, f"{comp[1]} x {f:.3f}")
        out[ps] = u
    return out


def g1_screens(meas: dict, ratios: dict) -> dict:
    """G6l screens (verdict, sensitivity): screens per row pooled over the runs; seconds per screen by class
    (G2 primary = dk-ctx only, its rows are all dk-ctx; ungated = 78 of 83 rows V-AAL; V-DK = dk-ctx x P4)."""
    out = {}
    for ps in ("verdict", "sensitivity"):
        n_scr = sum(m[ps]["screens"] for m in meas.values())
        n_row = sum(m[ps]["n_rows_computed"] for m in meas.values())
        dk = meas["G2"][ps]["screen_mean_s"]
        out[ps] = dict(per_row=n_scr / n_row, screens=n_scr, rows=n_row,
                       seconds={"dk-ctx": dk, "V-AAL": meas["ungated"][ps]["screen_mean_s"],
                                "V-DK": dk * ratios["V-DK/dk-ctx"]})
    out["descriptor"] = dict(per_row=0.0, screens=0, rows=0, seconds={c: 0.0 for c in G1_CLASSES})
    return out


def g1_price(rows: dict, units: dict, screens: dict, per_row_override: float | None = None) -> dict:
    out = {}
    for ps in PASSES:
        tot, parts, missing = 0.0, {}, []
        spr = screens[ps]["per_row"] if per_row_override is None or ps == "descriptor" else per_row_override
        for k, n in sorted(rows["by_pass"][ps].items()):
            u = units[ps].get(k)
            if u is None:
                missing.append(k)
                continue
            cls = k.split(" / ")[1]
            s = n * (u[0] + spr * screens[ps]["seconds"][cls])
            parts[k] = dict(rows=n, row_s=u[0], source=u[1], process_h=s / 3600.0)
            tot += s
        if missing:
            raise SystemExit(f"G1 {ps}: no measured unit for {missing}")
        out[ps] = dict(process_h=tot / 3600.0, parts=parts, screens_per_row=spr)
    return out


def build_g1(root: Path = REPO) -> dict:
    plan_check()
    lines = PLAN.read_bytes().decode("utf-8").splitlines()
    for n, text in G1_PLAN_LINES.items():
        if not lines[n - 1].startswith(text):
            raise SystemExit(f"RUN_PLAN.md:{n} is not the quoted §12 / §14 text")
    meas = {run: {p: measured_run(r, c, p, root) for p in PASSES} for run, (r, c) in MEASURED_RUNS.items()}
    for p in PASSES:                     # apparatus: G2 primary rows are all dk-ctx (its screens are dk-ctx screens)
        if any(not k.endswith("/ dk-ctx") for k in meas["G2"][p]["rows"]):
            raise SystemExit("G2 primary has a non-dk-ctx row: its screen time is not a dk-ctx screen time")
    ratios = p4_ratios(root)
    rows = g1_rows(root)
    scr = g1_screens(meas, ratios)
    central = g1_price(rows, g1_unit_costs(meas, ratios, "pooled"), scr)
    high = g1_price(rows, g1_unit_costs(meas, ratios, "max"), scr, per_row_override=1.0)
    tail_s = max(e["max_s"] for m in meas.values() for e in m["descriptor"]["rows"].values())
    eff = {}
    for run, (r, _) in MEASURED_RUNS.items():
        for p in PASSES:
            log = root / r / p / "run.log"
            if log.is_file():
                try:
                    w = wall(log.read_text(encoding="utf-8"))
                    eff[f"{run}/{p}"] = meas[run][p]["checkpoint_process_h"] / (w["pass_s"] / 3600.0)
                except (KeyError, IndexError):
                    pass
    j20 = sum(eff.values()) / len(eff)
    blocks, total_c, total_h = {}, 0.0, 0.0
    for p in PASSES:
        c, h = central[p]["process_h"], high[p]["process_h"]
        total_c, total_h = total_c + c, total_h + h
        blocks[f"G1/{p}"] = dict(
            plan_estimate_process_h=None, plan_line=1536, repriced_process_h=c, pause_estimate_process_h=c,
            pause_threshold_process_h=PACE.PAUSE_FACTOR * c, high_process_h=h,
            low_process_h_at_low_contention=c / CONTENTION_20,
            repriced_wall_h_at_20_jobs=max(c / j20, tail_s / 3600.0 if p == "descriptor" else 0.0),
            parts=central[p]["parts"], screens_per_row=central[p]["screens_per_row"])
    return dict(
        what="A1 G1 (WP5) block estimates repriced at the measured screen and row times (RUN_PLAN §12 :1536-1538, §14)",
        script="arcs/audit/src/a1_audit/reprice.py --gate G1", generated_at_head=git("rev-parse", "HEAD"),
        generated_utc=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        plan=dict(file="arcs/audit/RUN_PLAN.md", sha256=PLAN_SHA256,
                  lines_quoted={**{k: v for k, v in PLAN_LINES.items() if k in (1557, 1567, 1577)}, **G1_PLAN_LINES}),
        rule=("per pass: sum over G1's register rows (run.classify, G1 open) of [seconds per row of its form family and "
              "class + G6l screens per row x seconds per screen of its class], from the measured audit-scale runs "
              "(20 jobs); PLS-enrichment and V-DK, never run at audit scale, are scaled from the measured decoded-list "
              "/ dk-ctx rows by the P4 plant-mode ratios (same K in every cell); conditional classes at V-DK; every "
              "carrier-conditional row priced as computing; sensitivity rows priced as recomputed. pause estimate = "
              "the central (pooled-mean) estimate; threshold = %g x it (pace.PAUSE_FACTOR; RUN_PLAN.md:1577)"
              % PACE.PAUSE_FACTOR),
        bounds=("high = the largest run mean per unit and one G6l screen per row; low = central / %g (RUN_PLAN.md:1550 "
                "20-job contention: a run at few jobs on an idle core set spends fewer process-s per task)"
                % CONTENTION_20),
        plan_g1_total_process_h=G1_TOTAL, plan_g1_wall_h=9.5,
        total_process_h=dict(central=total_c, high=total_h, low=total_c / CONTENTION_20, ratio_to_plan=total_c / G1_TOTAL),
        effective_jobs_at_20=dict(by_pass=eff, mean=j20),
        descriptor_longest_row_s=tail_s,
        wall_note=("wall-h at J jobs ~ max(process-h / J, the longest descriptor row); the measured runs' longest "
                   "descriptor row is a floor on the descriptor pass's wall time"),
        measured_g2_vs_plan={f"{run}/{p}": dict(checkpoint_process_h=meas[run][p]["checkpoint_process_h"],
                                                plan_estimate_process_h=PLAN_EST.get(("G2", p)),
                                                ratio=meas[run][p]["checkpoint_process_h"] / PLAN_EST[("G2", p)])
                             for run in ("G2", "G2_amend5") for p in PASSES},
        g1_rows=rows, p4=ratios, screens=scr, measured=meas, blocks=blocks,
        caveat=("G1's sets and maps are unopened (no G1 material is read here): set sizes drive the descriptor cost "
                "(the measured descriptor rows range up to %.0f s each), so the true cost may differ either way; "
                "RUN_PLAN.md:1557 'estimates may be off by about 2x'" % tail_s))


def wall_at_jobs(doc: dict, jobs: int, contention_low: bool = False) -> float:
    """Total wall-h of the three G1 passes at `jobs` (process-h / jobs; descriptor floored at its longest row)."""
    t = 0.0
    for p in PASSES:
        b = doc["blocks"][f"G1/{p}"]
        ph = b["low_process_h_at_low_contention"] if contention_low else b["repriced_process_h"]
        t += max(ph / jobs, doc["descriptor_longest_row_s"] / 3600.0 if p == "descriptor" else 0.0)
    return t


def md_g1(doc: dict) -> str:
    b = doc["blocks"]
    tp = doc["total_process_h"]
    out = ["# A1 G1 (WP5) block estimates repriced (GENERATED by a1_audit.reprice --gate G1; do not hand-edit)", "",
           f"Script `{doc['script']}`, generated at HEAD `{doc['generated_at_head'][:7]}`; inputs: the ungated, G2 "
           "primary and G2 amend_5 row records and checkpoints (20 jobs), the P4 plant timing (commit "
           f"`{doc['p4']['committed_in'][:7]}`), the frozen register (run.classify with G1 open); RUN_PLAN.md §12 "
           "(:1536-1538), §14 (:1550, :1557, :1567, :1577). No G1 material is read.", "",
           "| block | G1 rows | repriced (process-h) | 2x pause threshold | high | low (low contention) | wall-h at 20 jobs |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for p in PASSES:
        e = b[f"G1/{p}"]
        out.append(f"| G1/{p} | {sum(x['rows'] for x in e['parts'].values())} | {e['repriced_process_h']:.1f} | "
                   f"{e['pause_threshold_process_h']:.1f} | {e['high_process_h']:.1f} | "
                   f"{e['low_process_h_at_low_contention']:.1f} | {e['repriced_wall_h_at_20_jobs']:.1f} |")
    out += [f"| **G1 total** | | **{tp['central']:.1f}** | | {tp['high']:.1f} | {tp['low']:.1f} | "
            f"{sum(b[f'G1/{p}']['repriced_wall_h_at_20_jobs'] for p in PASSES):.1f} |", "",
            f"§14 / §12 froze G1 at {doc['plan_g1_total_process_h']:g} process-h / {doc['plan_g1_wall_h']:g} wall-h; the "
            f"repriced central total is {tp['ratio_to_plan']:.2f}x that.", "",
            "Wall-h of the three passes at J jobs (process-h / J; the descriptor pass floored at the longest measured "
            f"descriptor row, {doc['descriptor_longest_row_s'] / 3600:.1f} h): "
            + "; ".join(f"J = {j}: {wall_at_jobs(doc, j):.0f} h ({wall_at_jobs(doc, j, True):.0f} h at low contention)"
                        for j in (2, 4, 8, 13, 20)) + ".", "",
            "Units (central; seconds per row, G6l screens added per row in verdict / sensitivity):", ""]
    for p in PASSES:
        for k, v in b[f"G1/{p}"]["parts"].items():
            out.append(f"- {p} {k}: {v['rows']} rows x {v['row_s']:.0f} s ({v['source']}) -> {v['process_h']:.1f} process-h")
    sc = doc["screens"]
    out += ["", "G6l screens per row (pooled): verdict %.3f, sensitivity %.3f; seconds per screen: %s." % (
        sc["verdict"]["per_row"], sc["sensitivity"]["per_row"],
        "; ".join(f"{p} " + ", ".join(f"{c} {s:.0f}" for c, s in sc[p]["seconds"].items()) for p in ("verdict", "sensitivity"))),
            "", "Measured G2 against its §14 estimate (checkpoint process-h): " + "; ".join(
                f"{k} {v['checkpoint_process_h']:.1f} / {v['plan_estimate_process_h']:g} = {v['ratio']:.2f}x"
                for k, v in doc["measured_g2_vs_plan"].items()) + ".", "", doc["rule"] + ".", "", doc["bounds"] + ".",
            "", doc["caveat"] + "."]
    return "\n".join(out) + "\n"


def main_g1(a: list) -> int:
    doc = build_g1()
    if "--check" in a:
        old = json.loads(G1_OUT_JSON.read_bytes().decode("utf-8"))
        same = all(old["blocks"][k]["pause_estimate_process_h"] == v["pause_estimate_process_h"]
                   for k, v in doc["blocks"].items())
        print("check: " + ("same pause estimates" if same else "DIFFERENT pause estimates"))
        return 0 if same else 1
    data = (json.dumps(doc, indent=1, ensure_ascii=False, default=str) + "\n").encode("utf-8")
    G1_OUT_JSON.write_bytes(data)
    if G1_OUT_JSON.read_bytes() != data:
        raise SystemExit("read-back differs")
    md = md_g1(doc).encode("utf-8")
    G1_OUT_MD.write_bytes(md)
    if G1_OUT_MD.read_bytes() != md:
        raise SystemExit("read-back differs (.md)")
    print(f"wrote arcs/audit/run_manifests/reprice_wp5.json sha256 {sha(data)}")
    return 0


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:2] == ["--gate", "G1"]:
        return main_g1(a[2:])
    doc = build()
    if "--check" in a:
        old = json.loads(OUT_JSON.read_bytes().decode("utf-8"))
        same = all(old["blocks"][k]["pause_estimate_process_h"] == v["pause_estimate_process_h"]
                   for k, v in doc["blocks"].items())
        print("check: " + ("same pause estimates" if same else "DIFFERENT pause estimates"))
        return 0 if same else 1
    data = (json.dumps(doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    OUT_JSON.write_bytes(data)
    if OUT_JSON.read_bytes() != data:
        raise SystemExit("read-back differs")
    md = md_table(doc).encode("utf-8")
    OUT_MD.write_bytes(md)
    if OUT_MD.read_bytes() != md:
        raise SystemExit("read-back differs (.md)")
    print(f"wrote {PACE.ESTIMATES_REL} sha256 {sha(data)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
