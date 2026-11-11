"""BrainSpan cortical trajectories for G5 (prereg §4.3): per gene symbol, mean log2(RPKM + 1) over neocortical
samples in 8 stage bins; duplicate symbols averaged. Source: E:\\data\\asdg\\brainspan\\genes_matrix_csv\\."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

DIR = Path("E:/data/asdg/brainspan/genes_matrix_csv")
NEOCORTEX = {"A1C", "DFC", "IPC", "ITC", "M1C", "M1C-S1C", "MFC", "OFC", "Ocx", "PCx", "S1C", "STC", "TCx",
             "V1C", "VFC"}
BINS = [("8-12pcw", 8 / 52 - 1, 13 / 52 - 1), ("13-21pcw", 13 / 52 - 1, 22 / 52 - 1),
        ("22-37pcw", 22 / 52 - 1, 38 / 52 - 1), ("0-1y", 0, 1), ("1-6y", 1, 6), ("6-12y", 6, 12),
        ("12-20y", 12, 20), ("20-40y", 20, 41)]  # age in years relative to birth; pcw mapped to (pcw/52 - 1)


def age_years(s: str) -> float:
    n, unit = re.match(r"\s*([\d.]+)\s*(pcw|mos|yrs)", s).groups()
    n = float(n)
    return {"pcw": n / 52 - 1, "mos": n / 12, "yrs": n}[unit]


def load_trajectories() -> tuple[pd.DataFrame, dict]:
    cols = pd.read_csv(DIR / "columns_metadata.csv")
    rows = pd.read_csv(DIR / "rows_metadata.csv")
    X = pd.read_csv(DIR / "expression_matrix.csv", header=None, index_col=0).to_numpy(dtype=float)
    assert X.shape == (len(rows), len(cols)), (X.shape, len(rows), len(cols))
    age = cols["age"].map(age_years).to_numpy()
    ctx = cols["structure_acronym"].isin(NEOCORTEX).to_numpy()
    L = np.log2(X + 1.0)
    out, counts = {}, {}
    for name, lo, hi in BINS:
        sel = ctx & (age >= lo) & (age < hi)
        counts[name] = int(sel.sum())
        assert sel.sum() > 0, f"no neocortical samples in bin {name}"
        out[name] = L[:, sel].mean(1)
    T = pd.DataFrame(out, index=rows["gene_symbol"].astype(str).to_numpy())
    n_dup = int(T.index.duplicated().sum())
    T = T.groupby(level=0).mean()
    return T, dict(samples_per_bin=counts, n_genes=len(T), n_duplicate_rows_averaged=n_dup)
