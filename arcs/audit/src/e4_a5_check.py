"""prereg_amend_1 A5: V-DK matrix from abagen 0.1.3 / pandas 1.5.3 (env/venv_ref, artifacts/ahba) vs abagen master
@dc4a007e / pandas 2.2.3 (env/venv_pd22, artifacts/ahba_master). Pass: same genes, parcels, NaN pattern, max |d| < 1e-6.
Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src\\e4_a5_check.py
"""
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
a = pd.read_csv(ROOT / "artifacts/ahba/dk_expr.csv.gz", index_col=0)
b = pd.read_csv(ROOT / "artifacts/ahba_master/dk_expr.csv.gz", index_col=0)
same_g, same_p = list(a.columns) == list(b.columns), list(a.index) == list(b.index)
ok = same_g and same_p
nanpat = bool((a.isna().to_numpy() == b.isna().to_numpy()).all()) if ok else None
d = float(np.nanmax(np.abs(a.to_numpy() - b.to_numpy()))) if ok else None
res = dict(check="A5 (prereg_amend_1)", same_gene_list=same_g, same_parcels=same_p, identical_nan_pattern=nanpat,
           max_abs_diff=d, shape=list(a.shape), pass_=bool(ok and nanpat and d < 1e-6),
           commit=subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip())
(ROOT / "arcs/audit/results/e4_a5_check.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
print(json.dumps(res, indent=1))
