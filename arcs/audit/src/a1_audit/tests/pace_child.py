"""A synthetic task for tests/test_prewp4.py's pause checks (module level, so a loky worker imports it by reference).
fake_task(key, kw): sleeps kw['sleep'] s, writes one new file <key>.<pid>.<ns> into the directory kw['log'] per
invocation (recomputation is visible; no shared file, so concurrent workers never lose a mark), and returns a payload
whose value depends only on kw['seed'] and whose _meta.seconds is the INJECTED kw['seconds'] (the pause counts
_meta.seconds, pace.seconds_of)."""
from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np


def fake_task(key: str, kw: dict):
    time.sleep(float(kw.get("sleep", 0.0)))
    d = Path(kw["log"])
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{key}.{os.getpid()}.{time.time_ns()}").write_text(key, encoding="utf-8")
    v = np.random.default_rng(int(kw["seed"])).standard_normal(4).tolist()
    return key, {"value": v, "_meta": {"seconds": float(kw["seconds"]), "pid": os.getpid()}}
