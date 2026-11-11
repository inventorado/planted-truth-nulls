"""The null cascade (prereg §4): Level 0 naive, Level 1 spatial, Level 2 gene nulls, Level 3 J1; PLS1 (§4.7).

All p-values one-sided in the published direction `sign` (+1/-1), empirical p = (k + 1)/(n + 1).
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def _rows_z(A: np.ndarray) -> np.ndarray:
    A = np.atleast_2d(np.asarray(A, dtype=float))
    A = A - A.mean(1, keepdims=True)
    return A / np.linalg.norm(A, axis=1, keepdims=True)


def corr_matrix(maps: np.ndarray, scores: np.ndarray) -> np.ndarray:
    """Pearson r between every map row and every score row: (M, p) x (K, p) -> (M, K)."""
    return _rows_z(maps) @ _rows_z(scores).T


def emp_p(null: np.ndarray, obs: float, sign: int) -> float:
    null = np.asarray(null, dtype=float).ravel()
    return float((np.sum(sign * null >= sign * obs) + 1) / (null.size + 1))


def naive_p(r: float, n: int, sign: int) -> float:
    t = r * np.sqrt((n - 2) / max(1e-300, 1 - r * r))
    return float(stats.t.sf(sign * t, df=n - 2))


def pool_diversity(pool_sets: np.ndarray, n_pairs: int = 2000, seed: int = 0) -> float:
    """Mean pairwise Jaccard overlap of pool sets (sampled pairs). J1 requires < 0.5 (prereg §4.4)."""
    rng = np.random.default_rng(seed)
    k = len(pool_sets)
    a, b = rng.integers(k, size=n_pairs), rng.integers(k, size=n_pairs)
    a, b = a[a != b], b[a != b]
    j = [len(set(pool_sets[i]) & set(pool_sets[l])) / len(set(pool_sets[i]) | set(pool_sets[l])) for i, l in zip(a, b)]
    return float(np.mean(j))


def joint_j1(y: np.ndarray, set_score: np.ndarray, pool_scores: np.ndarray, surrogates: np.ndarray,
             sign: int) -> tuple[float, float, np.ndarray]:
    """J1 (prereg §4.4): z(map) = (r(S, map) - mean_k r(R_k, map)) / sd_k r(R_k, map); null = z over
    spatial surrogates of y. H0: S's advantage over its coexpression-matched pool on y is no larger than on
    maps with y's autocorrelation. Returns (z_obs, p_J1, z_null)."""
    maps = np.vstack([y, surrogates])
    r_set = corr_matrix(maps, set_score)[:, 0]
    r_pool = corr_matrix(maps, pool_scores)
    sd = r_pool.std(1, ddof=1)
    if not np.all(sd > 1e-9):  # degenerate pool: reported as a status, never an abort
        return float("nan"), float("nan"), np.array([])
    z = (r_set - r_pool.mean(1)) / sd
    return float(z[0]), emp_p(z[1:], z[0], sign), z[1:]


def naive_joint(y: np.ndarray, pool_scores: np.ndarray, surrogates: np.ndarray, set_score: np.ndarray,
                sign: int, rng) -> float:
    """Descriptor only: the naive spin+shuffle joint null (Cao 2024 S17), pool = G1 (prereg §4.4):
    r(random set_i, surrogate_i), one random set paired with one surrogate per draw."""
    r_obs = corr_matrix(y, set_score)[0, 0]
    n = min(len(surrogates), len(pool_scores))
    j = rng.permutation(len(pool_scores))[:n]
    null = np.einsum("ij,ij->i", _rows_z(surrogates[:n]), _rows_z(pool_scores[j]))
    return emp_p(null, r_obs, sign)


# ---- PLS1 (prereg §4.7) ----------------------------------------------------------------------------------
def pls1(X: np.ndarray, Y: np.ndarray):
    """Single-response PLS component 1 for one or many response maps.

    X: parcels x genes (z-scored per gene inside); Y: (p,) or (M, p). Weight w ∝ X^T y (unit norm), score
    t = X w; R² = corr(t, y)². Sign aligned so corr(t, y) > 0. Returns (W (M, genes), R2 (M,))."""
    Xz = (X - X.mean(0)) / X.std(0, ddof=1)
    Yz = _rows_z(Y)
    W = Yz @ Xz  # (M, genes) ∝ X^T y
    W /= np.linalg.norm(W, axis=1, keepdims=True)
    T = W @ Xz.T  # (M, p)
    r = np.einsum("ij,ij->i", _rows_z(T), Yz)
    W *= np.sign(r)[:, None]
    return W, r ** 2


def clopper_pearson_upper(k: int, n: int, conf: float = 0.95) -> float:
    return 1.0 if k == n else float(stats.beta.ppf(conf, k + 1, n - k))


def fa_gate(k: int, n: int, nominal: float = 0.05, alpha: float = 0.001, max_rate: float = 0.07) -> dict:
    """False-alarm gate (prereg §6.4): pass iff the one-sided binomial test of rate <= nominal is not
    rejected at alpha AND the point estimate <= max_rate."""
    p = float(stats.binom.sf(k - 1, n, nominal))
    return dict(k=k, n=n, rate=k / n, p_binom=p, pass_=bool(p >= alpha and k / n <= max_rate))
