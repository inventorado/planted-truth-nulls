"""Peak memory of ONE Liu gene-set-only row (RUN_PLAN R10; forms.liu_compute) at the REAL shapes, on SYNTHETIC data
(RUN_PLAN §4 :382-385, "a job above 2.5 GB is a defect"; pre-WP4 item 3). No real file is opened.

    python -X utf8 -m a1_audit.tests.liu_mem_probe make <dir>
    python -X utf8 -m a1_audit.tests.liu_mem_probe measure <dir> <cell> <K> [--result <json>]

make     writes BrainSpan-shaped stand-ins (expression_matrix.csv 52,376 x 524 values as RPKM, rows_metadata.csv,
         columns_metadata.csv; the declared columns only) into <dir>. The shapes are the WP3 run's recorded counts
         (results/a1_run/ungated/descriptor/row_0471.json inputs: 524 samples, 52,376 rows, 38,343 rows HGNC-mapped, 387
         symbols duplicated over 1,137 columns, set m 258, 2,670 GAMBA brain genes in U_stat; 237 prenatal / 287
         postnatal samples; HIP 32 vs frontal 133).
measure  in a FRESH process (= what a pool worker is): reads the three files' bytes, parses them with the production
         loader functions (wp3_genes.brainspan_frames, brainspan_trajectories), builds the Liu inputs as
         real_sources.WP3Sources.liu_inputs does, then runs forms.liu_compute at K inside run.MemProbe (the runner's
         own job measure). Prints one 'RESULT <json>' line: the process peak working set after loading and at the end,
         MemProbe's record, the seconds, T and the sha256 of the record (bit-identity across code versions).
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

N_ROWS, N_SAMPLES, N_MAPPED = 52_376, 524, 38_343
N_DUP_SYMBOLS, N_DUP_COLUMNS = 387, 1_137
N_CONST = 867            # constant genes over all samples (U_stat drops; the run's T1 count)
M_SET, N_BRAIN = 258, 2_670
N_PRE = 237
STRUCT_COUNTS = {"HIP": 32, "MD": 15, "DTH": 14, "STR": 28, "CBC": 29, "DFC": 34, "VFC": 33, "MFC": 33, "OFC": 33}
SEED = 20261015


def _symbols() -> list:
    """Row keys after the HGNC mapping: N_MAPPED mapped rows (N_DUP_SYMBOLS symbols carried by N_DUP_COLUMNS rows),
    the rest unmapped (None)."""
    uniq = N_MAPPED - N_DUP_COLUMNS + N_DUP_SYMBOLS
    syms = [f"G{j:05d}" for j in range(uniq)]
    rng = np.random.default_rng(SEED + 1)
    dup = rng.choice(uniq, N_DUP_SYMBOLS, replace=False)
    extra = N_DUP_COLUMNS - 2 * N_DUP_SYMBOLS         # copies beyond the second of a duplicated symbol
    reps = [syms[int(d)] for d in dup] + [syms[int(d)] for d in rng.choice(dup, extra, replace=True)]
    mapped = syms + reps
    order = rng.permutation(len(mapped))
    mapped = [mapped[int(k)] for k in order]
    return mapped + [None] * (N_ROWS - N_MAPPED)


def make(d: Path) -> dict:
    d.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    lvl = rng.gamma(0.6, 3.0, N_ROWS)
    fac = rng.normal(0, 1, (N_ROWS, 4)) @ rng.normal(0, 0.4, (4, N_SAMPLES))
    fac += np.abs(rng.normal(0.6, 0.3, N_ROWS))[:, None] * rng.normal(0, 1, N_SAMPLES)[None, :]   # shared axis:
    # mean pairwise coexpression well above 0, so every G2 / G4 sub-bin is reachable (as on BrainSpan; the run's legs ok)
    L2 = np.clip(np.log2(lvl + 1.0)[:, None] + fac + rng.normal(0, 0.5, (N_ROWS, N_SAMPLES)), 0.0, None)
    L2[rng.choice(N_MAPPED, N_CONST, replace=False)] = 0.0
    X = np.round(np.exp2(L2) - 1.0, 6)
    del L2, fac
    pd.DataFrame(X, index=np.arange(1, N_ROWS + 1)).to_csv(d / "expression_matrix.csv", header=False,
                                                           float_format="%.6g", lineterminator="\n")
    syms = _symbols()
    pd.DataFrame({"row_num": np.arange(1, N_ROWS + 1), "gene_id": np.arange(N_ROWS),
                  "ensembl_gene_id": [f"ENSGSYN{j:011d}" for j in range(N_ROWS)],
                  "gene_symbol": [s if s is not None else f"UNMAPPED{j}" for j, s in enumerate(syms)],
                  "entrez_id": ""}).to_csv(d / "rows_metadata.csv", index=False, lineterminator="\n")
    ages = [f"{8 + k % 30} pcw" for k in range(N_PRE)] + \
           [(f"{1 + k % 11} mos" if k % 3 == 0 else f"{1 + k % 40} yrs") for k in range(N_SAMPLES - N_PRE)]
    structs = [s for s, n in STRUCT_COUNTS.items() for _ in range(n)]
    structs += ["V1C"] * (N_SAMPLES - len(structs))
    structs = [structs[int(k)] for k in np.random.default_rng(SEED + 2).permutation(N_SAMPLES)]
    pd.DataFrame({"column_num": np.arange(1, N_SAMPLES + 1), "age": ages, "gender": "",
                  "structure_acronym": structs}).to_csv(d / "columns_metadata.csv", index=False, lineterminator="\n")
    json.dump({"symbols": syms}, open(d / "mapping.json", "w", encoding="utf-8"))
    return {"files": {f.name: f.stat().st_size for f in sorted(d.iterdir())}}


def measure(d: Path, cell: str, K: int) -> dict:
    from a1_audit import forms as FM
    from a1_audit import run as R
    from a1_audit import verdict as V
    from a1_audit import wp3_genes as WG
    t0 = time.perf_counter()
    blobs = {k: (d / k).read_bytes() for k in ("expression_matrix.csv", "rows_metadata.csv", "columns_metadata.csv")}
    X, rows, cols = WG.brainspan_frames(blobs["expression_matrix.csv"], blobs["rows_metadata.csv"],
                                        blobs["columns_metadata.csv"])
    del blobs
    mapped = json.loads((d / "mapping.json").read_text(encoding="utf-8"))["symbols"]
    traj, _ = WG.brainspan_trajectories(X, mapped, list(cols["age"]), list(cols["structure_acronym"]))
    keep = [k for k, m in enumerate(mapped) if m]
    expr = pd.DataFrame(X[keep].T, columns=[mapped[k] for k in keep])
    meta = pd.DataFrame({"age": list(cols["age"]), "structure_acronym": list(cols["structure_acronym"])})
    rng = np.random.default_rng(SEED + 3)
    uniq = sorted(set(m for m in mapped if m))
    varying = sorted({m for k, m in enumerate(mapped) if m and X[k].std() > 0} - {m for k, m in enumerate(mapped)
                                                                                 if m and not X[k].std() > 0})
    members = sorted(rng.choice(varying, M_SET, replace=False).tolist())   # m = 258 in U_stat, as the run's
    brain = sorted(rng.choice(uniq, N_BRAIN, replace=False).tolist())
    inputs = dict(data="brainspan", expr=expr, meta=meta, scale="RPKM", set=members, brain=brain, traj=traj)
    ws_load = R.process_peak_working_set()
    t_load = time.perf_counter() - t0
    spec = dict(FM.LIU_SPECS[cell], cell_id=cell)
    sc = V.plant_seed_callables(16, 0, FM.SYN_LIU_CLASS_ID["brainspan"])
    two_sided = cell in ("LIU-T2-STR", "LIU-T2-CBC", "LIU-T2-HIP")
    reg = None if two_sided else (-1 if cell == "LIU-T2" else 1)
    t1 = time.perf_counter()
    with R.MemProbe() as mp:
        rec = FM.liu_compute(spec, inputs, K=int(K), seed_of=sc["seed_of"], g3_seed=sc["g3_seed"],
                             two_sided=two_sided, registered_direction=reg)
    blob = json.dumps(R.A3.jsonable(rec), sort_keys=True).encode("utf-8")
    return dict(cell=cell, K=int(K), shapes=dict(rows=N_ROWS, samples=N_SAMPLES, mapped=N_MAPPED,
                                                 U_stat=rec["U_stat"]["n_U_stat"], m=rec["set"]["m"],
                                                 samples_used=rec["U_stat"]["n_samples_used"]),
                process_peak_working_set_after_load=ws_load, memprobe=mp.result,
                process_peak_working_set_end=R.process_peak_working_set(), seconds_load=round(t_load, 1),
                seconds_compute=round(time.perf_counter() - t1, 1), T=rec["T"],
                record_sha256=hashlib.sha256(blob).hexdigest(),
                legs={k: dict(status=v.get("status"), n=v.get("n")) for k, v in rec["legs"].items()},
                level2=R.A3.jsonable(rec["level2"]))


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[0] == "make":
        out = make(Path(a[1]))
    else:
        out = measure(Path(a[1]), a[2], int(a[3]))
        if "--result" in a:
            Path(a[a.index("--result") + 1]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print("RESULT " + json.dumps(out), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
