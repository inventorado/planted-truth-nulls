"""Gene-set scores and competitive gene nulls G1-G5 (prereg §4.3).

`expr` is a parcels x genes DataFrame (abagen output, analysis parcels only).
Set score = per-parcel mean of the member genes' expression. Coexpression = Pearson across parcels.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN_SET = 5  # prereg §4: a set with fewer genes present in the matrix is "not testable"


class Universe:
    def __init__(self, expr: pd.DataFrame):
        assert not expr.isna().any().any(), "expression matrix has NaN; restrict to analysis parcels first"
        X = expr.to_numpy(dtype=float)
        sd = X.std(0, ddof=1)
        keep = sd > 1e-12
        self.n_dropped_constant = int((~keep).sum())
        X = X[:, keep]
        self.genes = np.asarray(expr.columns)[keep]
        self.index = {g: i for i, g in enumerate(self.genes)}
        self.X = X
        Z = (X - X.mean(0)) / X.std(0, ddof=1)
        self.Z = Z / np.sqrt(X.shape[0] - 1)  # columns unit-norm: Z[:,i] @ Z[:,j] = Pearson r

    def idx(self, genes) -> tuple[np.ndarray, list]:
        """Indices of genes present, and the list of genes absent (reported, never silent)."""
        present = [g for g in dict.fromkeys(genes) if g in self.index]
        missing = [g for g in dict.fromkeys(genes) if g not in self.index]
        return np.array([self.index[g] for g in present], dtype=int), missing

    def testable_set(self, genes, allow_single: bool = False) -> tuple[np.ndarray | None, dict]:
        """prereg §4: < MIN_SET genes present -> "not testable" (single-gene reproductions exempt)."""
        idx, missing = self.idx(genes)
        info = dict(n_requested=len(dict.fromkeys(genes)), n_present=len(idx), missing=missing)
        if len(idx) < MIN_SET and not (allow_single and len(idx) >= 1):
            return None, {**info, "status": "not testable"}
        return idx, {**info, "status": "ok"}

    def scores(self, sets: np.ndarray) -> np.ndarray:
        """sets: (k, m) int indices -> (k, parcels) set scores."""
        sets = np.atleast_2d(sets)
        return self.X[:, sets].mean(axis=2).T

    def mean_coexpr(self, s) -> float:
        v = self.Z[:, s].sum(1)
        m = len(s)
        return float((v @ v - m) / (m * (m - 1)))


def random_sets(pool: np.ndarray, m: int, k: int, rng, exclude=()) -> np.ndarray:
    """G1 / G3: k uniform size-m sets without replacement from pool minus exclude."""
    pool = np.setdiff1d(np.asarray(pool), np.asarray(exclude, dtype=int))
    return np.stack([rng.choice(pool, size=m, replace=False) for _ in range(k)])


def coexpr_matched_sets(U: Universe, pool: np.ndarray, m: int, target: float, k: int, rng, tol: float = 0.02,
                        exclude=(), chains: int = 4, thin: int | None = None, greedy_iter: int = 50000,
                        max_restarts: int = 20):
    """Stratified wrapper: the band is split into `chains` equal sub-bins and k/chains sets are drawn in
    each (uniform over sets *within* a sub-bin). Uniform-over-sets on the whole band would pile samples at
    the low-coexpression edge (many more sets exist there), making the null narrower than S's."""
    pool = np.setdiff1d(np.asarray(pool), np.asarray(exclude, dtype=int))
    edges = np.linspace(target - tol, target + tol, chains + 1)
    per = int(np.ceil(k / chains))
    outs, infos = [], []
    for j in range(chains):
        s, info = _band_chain(U, pool, m, edges[j], edges[j + 1], per, rng, thin, greedy_iter, max_restarts)
        if s is None:
            return None, dict(status="unmatched", target=target, sub_bin=(edges[j], edges[j + 1]))
        outs.append(s); infos.append(info)
    sets = np.concatenate(outs)[:k]
    rng.shuffle(sets)
    achieved = np.array([U.mean_coexpr(x) for x in sets])
    return sets, dict(status="ok", restarts=sum(i["restarts"] for i in infos),
                      accept_rate=float(np.mean([i["accept_rate"] for i in infos])),
                      achieved_mean=float(achieved.mean()), achieved_sd=float(achieved.std()),
                      achieved_min=float(achieved.min()), achieved_max=float(achieved.max()))


def _band_chain(U: Universe, pool, m, lo, hi, n_samples, rng, thin, greedy_iter, max_restarts):
    """G2 / G4: size-m sets whose mean pairwise coexpression lies in [target - tol, target + tol].

    Phase 1 (per chain): greedy swaps from a random start until the set enters the band (restarted up to
    max_restarts). Phase 2: Metropolis random walk — swap a uniform member for a uniform non-member of the
    pool, accept iff the result stays in the band. The proposal is symmetric, so the stationary law is
    uniform over in-band sets; samples are taken every `thin` proposals after a burn-in of `thin`.
    Returns (sets (k, m) or None, info dict). None = "unmatched" (target unreachable), never an infinite loop.
    """
    Z = U.Z
    thin = thin or 10 * m
    target = (lo + hi) / 2
    out, restarts, accepts, props = [], 0, 0, 0

    def stats_of(s):
        v = Z[:, s].sum(1)
        return v, (v @ v - m) / (m * (m - 1))

    for _ in range(1):
        # phase 1: greedy entry into the band
        entered = False
        while not entered and restarts <= max_restarts:
            s = rng.choice(pool, size=m, replace=False)
            v, c = stats_of(s)
            member = set(s.tolist())
            for _ in range(greedy_iter):
                if lo <= c <= hi:
                    entered = True
                    break
                i = rng.integers(m)
                g = pool[rng.integers(pool.size)]
                if g in member:
                    continue
                v2 = v - Z[:, s[i]] + Z[:, g]
                c2 = (v2 @ v2 - m) / (m * (m - 1))
                if abs(c2 - target) < abs(c - target):
                    member.discard(s[i]); member.add(g); s[i] = g; v, c = v2, c2
            if not entered:
                restarts += 1
        if not entered:
            return None, dict(status="unmatched", restarts=restarts, target=target)
        # phase 2: Metropolis walk uniform on the band
        n_needed = n_samples
        step = 0
        while n_needed > 0:
            i = rng.integers(m)
            g = pool[rng.integers(pool.size)]
            if g in member:
                continue  # redraw: proposal is uniform over non-members
            props += 1
            v2 = v - Z[:, s[i]] + Z[:, g]
            c2 = (v2 @ v2 - m) / (m * (m - 1))
            if lo <= c2 <= hi:
                accepts += 1
                member.discard(s[i]); member.add(g); s[i] = g; v, c = v2, c2
            step += 1
            if step > thin and step % thin == 0:
                out.append(s.copy())
                n_needed -= 1
    return np.stack(out), dict(restarts=restarts, accept_rate=accepts / max(props, 1))


class Trajectories:
    """BrainSpan trajectory space for G5 (prereg §4.3): per gene, mean log2(RPKM+1) in 8 stage bins (level
    block) and the same vector z-scored across bins (shape block); each block scaled to unit total variance.
    Duplicate symbols are averaged before this class is built (caller)."""

    def __init__(self, traj: pd.DataFrame, universe: Universe):
        assert traj.index.is_unique, "deduplicate BrainSpan symbols first"
        T = traj.loc[[g for g in traj.index if g in universe.index]]
        level = T.to_numpy(dtype=float)
        sd = level.std(1, ddof=1, keepdims=True)
        shape = np.divide(level - level.mean(1, keepdims=True), sd, out=np.zeros_like(level), where=sd > 0)
        level = (level - level.mean(0)) / np.sqrt(((level - level.mean(0)) ** 2).sum(1).mean())
        shape = (shape - shape.mean(0)) / np.sqrt(((shape - shape.mean(0)) ** 2).sum(1).mean())
        self.F = np.hstack([level, shape])
        self.names = np.asarray(T.index)
        self.row = {g: i for i, g in enumerate(self.names)}
        from sklearn.neighbors import NearestNeighbors

        self.nn = NearestNeighbors().fit(self.F)


def trajectory_matched_sets(U: Universe, set_genes, tr: Trajectories, k: int, rng, k_nn: int = 20,
                            max_fallback: float = 0.2, tol: float = 0.02, **kw):
    """G5: trajectory- AND coexpression-matched sets (prereg §4.3). Pool = union of the k_nn nearest
    trajectory neighbours of every member of S (neighbours computed with S excluded); sets are drawn from that
    pool with G2's stratified Metropolis sampler at S's mean coexpression (±tol), so G5 sets are as coherent
    as S. Members absent from BrainSpan: if > max_fallback of S, G5 is "not applicable" (returns None)."""
    set_genes = [g for g in dict.fromkeys(set_genes) if g in U.index]
    in_tr = [g for g in set_genes if g in tr.row]
    info = dict(n_fixed=len(set_genes) - len(in_tr), n_set=len(set_genes))
    if len(set_genes) - len(in_tr) > max_fallback * len(set_genes):
        return None, {**info, "status": "not applicable"}
    sset = set(set_genes)
    _, ind = tr.nn.kneighbors(tr.F[[tr.row[g] for g in in_tr]], n_neighbors=min(len(tr.names), k_nn + len(sset) + 1))
    pool = sorted({U.index[c] for row in ind for c in [x for x in tr.names[row] if x not in sset][:k_nn]})
    info["pool_size"] = len(pool)
    S_idx = np.array([U.index[g] for g in set_genes])
    if len(pool) < 2 * len(S_idx):
        return None, {**info, "status": "not applicable"}
    sets, i2 = coexpr_matched_sets(U, np.array(pool), len(S_idx), U.mean_coexpr(S_idx), k, rng, tol=tol,
                                   exclude=S_idx, **kw)
    if sets is None:
        return None, {**info, "status": "unmatched"}
    return sets, {**info, **i2, "status": "ok"}