"""ASDG-AUD-E5-regime, space B (probe prereg §2): our space — E3's V-DK cells F-sp (random 25-gene sets) and F-mod
(tight modules: a seed + its 24 most coexpressed genes), 1,000 plants each, replayed exactly as
e3_species_replay.replay_one does (S, the G2 pool, the field, y; every plant's saved r and p_G2 asserted). Adds Cao's
statistics C1 Mean {+, +-, c} / C2 Meanabs (upper) (per-gene Fisher-z r on the V-DK matrix) and C3 T {+, +-, c}
(probe prereg v3 §2), with the nulls N1 (fresh uniform, K = 1,000), N2 (Cao's rejection sampler, tol .01, <= 1e6
draws, K accepted) and N3 (the replayed E3 G2 pool, 500 sets); C3+ x N3 is E3's own p_G2 (P3: equal plant by plant).
Classification (prereg §4): exact 99% binomial CI; anticonservative iff lower > .05 and rate > .07; calibrated iff
upper <= .07 and rate <= .06; else indeterminate. Every rate also by class-step stratum.

Usage (programme root): env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\probes\\regime\\src\\regime_replay.py
    [--jobs 22] [--limit N]    (--limit: code-path test, nothing written)
Writes arcs/audit/probes/regime/results/regime_B.json and artifacts/regime/regime_B_<cell>.csv.gz.
"""
from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "arcs" / "audit" / "src"))
sys.path.insert(0, str(ROOT / "src"))
import e3_plants as P  # noqa: E402
import e4_r1_cao as R1  # noqa: E402
from asdg.cascade import corr_matrix, emp_p  # noqa: E402
from asdg.genesets import coexpr_matched_sets  # noqa: E402

K, SEED = 1000, 5
CELLS = ["dk_F-sp_m25_a0", "dk_F-mod_m25_a0"]
OUT = ROOT / "arcs" / "audit" / "probes" / "regime" / "results"
ART = ROOT / "artifacts" / "regime"


def git(*a) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout.strip()


def cao_stats(Zg: np.ndarray, sets: np.ndarray):
    """Mean and Meanabs of per-gene Fisher z (Zg, one map) over each row of sets."""
    return Zg[sets].mean(1), np.abs(Zg[sets]).mean(1)


def forms(null: np.ndarray, obs: float, kind: str) -> dict:
    """p for each sidedness form (probe prereg §2): '+' one-sided positive, 'pm' two-sided |stat|, 'c' centred."""
    k = len(null)
    f = lambda c: (int(c) + 1) / (k + 1)  # noqa: E731
    if kind == "C2":
        return {"C2": f(np.sum(null >= obs))}
    mu = null.mean()
    return {f"{kind}+": f(np.sum(null >= obs)), f"{kind}pm": f(np.sum(np.abs(null) >= abs(obs))),
            f"{kind}c": f(np.sum(np.abs(null - mu) >= abs(obs - mu)))}


FORMS = ["C1+", "C1pm", "C1c", "C2", "C3+", "C3pm", "C3c"]


def replay_plant(ctx, ZT, fam, seed_list, i, max_draws):
    """E3 replay (same SeedSequence and draw order as e3_plants.one_plant), then the probe's nulls."""
    rng = np.random.default_rng(np.random.SeedSequence(seed_list))
    gen, step = P.GENERATOR_CELLS[i % len(P.GENERATOR_CELLS)]
    S = P.module(ctx, 25, rng, "coexp") if fam == "F-mod" else rng.choice(ctx.all, size=25, replace=False)
    score = ctx.U.scores(S)[0]
    c_S = ctx.U.mean_coexpr(S)
    G2, i2 = coexpr_matched_sets(ctx.U, ctx.all, 25, c_S, P.N_SETS, rng, exclude=S)
    y = ctx.fg.field(gen, rng, step)
    r_obs = corr_matrix(y, score)[0, 0]
    row = dict(i=i, gen=gen, step=step, G2_status_replay=i2["status"], r_replay=r_obs, coexp=c_S,
               p_G2_replay=emp_p(corr_matrix(y, ctx.U.scores(G2))[0], r_obs, 1) if G2 is not None else np.nan)
    # Cao's statistics on this plant's map: per-gene Fisher z of r(y, gene) over the V-DK analysis parcels
    Zg = R1.fisher_z((ZT @ ((y - y.mean()) / np.linalg.norm(y - y.mean()))))
    om, oa = cao_stats(Zg, S[None, :])
    r2 = np.random.default_rng(np.random.SeedSequence(seed_list + [SEED]))  # separate stream for the probe
    pool = np.setdiff1d(ctx.all, S)
    n1 = np.stack([r2.choice(pool, size=25, replace=False) for _ in range(K)])
    n2, _, draws = R1.cao_sampler(ZT, 25, c_S, r2, n_target=K, max_iter=max_draws)
    pools = {"N1": n1, "N2": n2 if len(n2) >= K else None, "N3": G2}
    row.update(n2_accepted=int(len(n2)), n2_draws=int(draws))
    for nl, pl in pools.items():
        if pl is None:
            row.update({f"p_{nl}_{c}": np.nan for c in FORMS})
            continue
        nm, na = cao_stats(Zg, pl)
        nt = corr_matrix(y, ctx.U.scores(pl))[0]
        ps = {**forms(nm, float(om[0]), "C1"), **forms(na, float(oa[0]), "C2"), **forms(nt, float(r_obs), "C3")}
        row.update({f"p_{nl}_{c}": v for c, v in ps.items()})
        row[f"p_{nl}_C3plus_emp"] = emp_p(nt, r_obs, 1)  # E3's own function, for P3
    return row


def binom_class(k: int, n: int) -> dict:
    """Exact (Clopper-Pearson) 99% CI and the three-way class of prereg §4."""
    if not n:
        return dict(k=0, n=0, rate=float("nan"), ci99=None, cls="not computed")
    ci = stats.binomtest(int(k), int(n)).proportion_ci(confidence_level=0.99, method="exact")
    rate = k / n
    cls = ("anticonservative" if ci.low > 0.05 and rate > 0.07 else
           "calibrated" if ci.high <= 0.07 and rate <= 0.06 else "indeterminate")
    return dict(k=int(k), n=int(n), rate=rate, ci99=[float(ci.low), float(ci.high)], cls=cls)


def selftest() -> list[str]:
    """Toy cases for this file's own sidedness forms and exact-binomial three-way rule (probe prereg §6)."""
    rng = np.random.default_rng(0)
    null = rng.standard_normal(999)
    fails = []
    a, b, c = forms(null, 3.2, "C1"), forms(null, -3.2, "C1"), forms(null, 0.0, "C3")
    if not (a["C1+"] < 0.01 and b["C1+"] > 0.99 and b["C1pm"] < 0.01 and c["C3c"] > 0.9 and forms(null, 3.2, "C2")["C2"] < 0.01):
        fails.append(f"forms: {a} {b} {c}")
    for k, want in ((30, "calibrated"), (150, "anticonservative"), (62, "indeterminate")):
        got = binom_class(k, 1000)["cls"]
        if got != want:
            fails.append(f"binom_class {k}/1000 -> {got}, expected {want}")
    return fails


def main():
    from joblib import Parallel, delayed

    bad = selftest()
    if bad:
        raise SystemExit("SELFTEST FAILED: " + "; ".join(bad))

    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=22)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    t0 = time.time()
    ctx = P.Ctx("dk")
    ZT = np.ascontiguousarray(ctx.U.Z.T)  # unit-norm gene profiles over the V-DK analysis parcels
    cells = {}
    for cell in CELLS:
        atlas, fam, mm, aa = cell.split("_")
        saved = pd.read_csv(P.OUT / f"{cell}.csv.gz")
        idx = sorted(saved["i"].astype(int))[: a.limit or None]
        base = [P.ATLAS_ID[atlas], P.FAM_ID[fam], 25, 0]

        def work(i):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return replay_plant(ctx, ZT, fam, base + [i], i, 1_000_000)

        d = pd.DataFrame(Parallel(n_jobs=a.jobs, backend="loky", batch_size=2)(delayed(work)(i) for i in idx))
        s = saved.set_index("i").loc[d["i"]]
        ok = np.isclose(s["r"].to_numpy(), d["r_replay"].to_numpy(), rtol=0, atol=1e-12)
        pg = s["p_G2"].to_numpy()
        ok &= (np.isnan(pg) == np.isnan(d["p_G2_replay"].to_numpy())) & (
            np.isnan(pg) | np.isclose(pg, d["p_G2_replay"].to_numpy(), rtol=0, atol=1e-12))
        if not ok.all():
            raise SystemExit(f"REPLAY MISMATCH in {cell}: plants {d.loc[~ok, 'i'].tolist()[:20]}")
        p3 = np.allclose(d["p_N3_C3plus_emp"].to_numpy(), d["p_G2_replay"].to_numpy(), equal_nan=True)
        assert p3, "P3: C3+ x N3 != E3 p_G2"
        same = np.allclose(d["p_N3_C3+"].to_numpy(), d["p_N3_C3plus_emp"].to_numpy(), equal_nan=True)
        assert same, "the probe's one-sided form differs from E3's emp_p"
        res = {}
        for nl in ("N1", "N2", "N3"):
            for c in FORMS:
                col = d[f"p_{nl}_{c}"]
                n_ok = int(col.notna().sum())
                res[f"{nl}|{c}"] = {f"a{al:g}": binom_class(int((col < al).sum()), n_ok) for al in (0.05, 0.025)}
                res[f"{nl}|{c}"]["unmatched"] = int(col.isna().sum())
                res[f"{nl}|{c}"]["by_step"] = {
                    f"{st:g}": binom_class(int((col[d["step"] == st] < 0.05).sum()), int(col[d["step"] == st].notna().sum()))
                    for st in sorted(d["step"].unique())}
        cells[cell] = dict(n_plants=int(len(d)), replay_ok=int(ok.sum()), P3="C3+ x N3 equals E3 p_G2 (asserted)",
                           results=res, n2_matched_frac=float((d["n2_accepted"] >= K).mean()))
        print(f"{cell}: plants={len(d)} replay_ok={int(ok.sum())} {time.time() - t0:.0f}s", flush=True)
        if not a.limit:
            ART.mkdir(parents=True, exist_ok=True)
            d.to_csv(ART / f"regime_B_{cell}.csv.gz", index=False)
    out = dict(entity="ASDG-AUD-E5-regime", space="B", K=K, cells=cells,
               script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), commit=git("rev-parse", "HEAD"),
               dirty=bool(git("status", "--porcelain")), runtime_s=time.time() - t0)
    if a.limit:
        print("(--limit: code-path test, nothing written)")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "regime_B.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()
