"""Spatial (self-contained) nulls for parcellated maps (prereg §4.2) and independent spatial fields for plants
(prereg §6).

S1 BrainSMASH, S2 Moran spectral randomisation; each also in a class-stratified variant (S1c, S2c): the map is
demeaned within tissue class, surrogates are generated within each class, class means are added back.
"""
from __future__ import annotations

import itertools
import math

import numpy as np
from scipy.spatial.distance import cdist


def centroid_distance(xyz: np.ndarray) -> np.ndarray:
    """Euclidean distance (mm) between parcel centroids, (n, 3) -> (n, n)."""
    xyz = np.asarray(xyz, dtype=float)
    assert xyz.ndim == 2 and xyz.shape[1] == 3, xyz.shape
    return cdist(xyz, xyz)


def brainsmash_surrogates(y: np.ndarray, D: np.ndarray, n: int, seed: int) -> np.ndarray:
    """S1: BrainSMASH Base surrogates, resample=True, package defaults otherwise (Base has no knn: it uses
    all pairs)."""
    from brainsmash.mapgen.base import Base

    y = np.asarray(y, dtype=float)
    assert np.all(np.isfinite(y)), "map has non-finite values"
    assert D.shape == (y.size, y.size)
    gen = Base(x=y, D=D, resample=True, seed=seed)
    s = np.atleast_2d(gen(n=n))
    assert s.shape == (n, y.size), s.shape
    return s


def variogram_misfit(y: np.ndarray, D: np.ndarray, surr: np.ndarray, nbins: int = 25, pv: float = 25) -> float:
    """Relative RMS difference between the empirical variogram of y and the mean surrogate variogram over
    the bottom pv-th percentile of distances (logged per map, prereg §4.2)."""
    iu = np.triu_indices_from(D, 1)
    d = D[iu]
    keep = d <= np.percentile(d, pv)
    edges = np.linspace(d[keep].min(), d[keep].max(), nbins + 1)
    b = np.clip(np.digitize(d[keep], edges) - 1, 0, nbins - 1)

    def vg(v):
        g = 0.5 * (v[iu[0]] - v[iu[1]])[keep] ** 2
        return np.array([g[b == j].mean() if np.any(b == j) else np.nan for j in range(nbins)])

    v0 = vg(y)
    vs = np.nanmean([vg(s) for s in surr[: min(100, len(surr))]], axis=0)
    ok = np.isfinite(v0) & np.isfinite(vs)
    return float(np.sqrt(np.mean((vs[ok] - v0[ok]) ** 2)) / np.mean(v0[ok]))


class MoranSpectral:
    """S2: Moran spectral randomisation, singleton procedure (Wagner & Dray 2015; BrainSpace's 'singleton').

    W = 1/d (zero diagonal), doubly centred; eigenvectors with non-zero eigenvalue span the space orthogonal
    to the constant. A surrogate keeps |coefficient| on every eigenvector and flips its sign at random, so
    it preserves the mean, the variance and Moran's I of y exactly (asserted in tests).
    """

    def __init__(self, D: np.ndarray, tol: float = 1e-8):
        D = np.asarray(D, dtype=float)
        n = D.shape[0]
        with np.errstate(divide="ignore"):
            W = np.where(D > 0, 1.0 / D, 0.0)
        np.fill_diagonal(W, 0.0)
        W = (W + W.T) / 2
        H = np.eye(n) - np.ones((n, n)) / n
        lam, V = np.linalg.eigh(H @ W @ H)
        keep = np.abs(lam) > tol * np.abs(lam).max()
        self.W = W
        self.lam = lam[keep]
        self.V = V[:, keep]
        assert self.V.shape[1] == n - 1, f"expected {n - 1} non-null eigenvectors, got {self.V.shape[1]}"

    def moran_i(self, y: np.ndarray) -> float:
        z = y - y.mean()
        return float(y.size / self.W.sum() * (z @ self.W @ z) / (z @ z))

    def surrogates(self, y: np.ndarray, n: int, seed: int) -> np.ndarray:
        y = np.asarray(y, dtype=float)
        c = self.V.T @ (y - y.mean())
        rng = np.random.default_rng(seed)
        signs = rng.choice([-1.0, 1.0], size=(n, c.size))
        return y.mean() + (signs * c) @ self.V.T


def stratified_surrogates(y: np.ndarray, D: np.ndarray, classes: np.ndarray, n: int, seed: int, method: str,
                          min_class: int = 10) -> np.ndarray:
    """S1c / S2c: within-class surrogates with class means preserved. Classes with < min_class parcels are
    permuted within class (the class mean is preserved exactly either way)."""
    y = np.asarray(y, dtype=float)
    classes = np.asarray(classes)
    out = np.empty((n, y.size))
    rng = np.random.default_rng(seed)
    for j, c in enumerate(np.unique(classes)):
        idx = np.flatnonzero(classes == c)
        mu = y[idx].mean()
        r = y[idx] - mu
        if idx.size < min_class or np.allclose(r, 0):
            out[:, idx] = mu + np.stack([rng.permutation(r) for _ in range(n)])
        elif method == "brainsmash":
            out[:, idx] = mu + brainsmash_surrogates(r, D[np.ix_(idx, idx)], n, seed + 7919 * (j + 1))
        elif method == "msr":
            out[:, idx] = mu + MoranSpectral(D[np.ix_(idx, idx)]).surrogates(r, n, seed + 7919 * (j + 1))
        else:
            raise ValueError(method)
    return out


# ---- audit resolution (prereg_amend_3 §2): exact enumeration of the stratified randomisation ---------------
def _class_parts(y, classes, min_class):
    y = np.asarray(y, dtype=float)
    classes = np.asarray(classes)
    for c in np.unique(classes):
        idx = np.flatnonzero(classes == c)
        mu = y[idx].mean()
        r = y[idx] - mu
        kind = "const" if np.allclose(r, 0) else "perm" if idx.size < min_class else "field"
        yield idx, mu, r, kind


def stratified_patterns(y: np.ndarray, classes: np.ndarray, method: str, min_class: int = 10) -> float:
    """Number of null patterns of S1c / S2c for this map: the product over tissue classes of 2^(n_c - 1) (an MSR class:
    one sign per non-null eigenvector), n_c! (a class of < min_class parcels, permuted within class) and 1 (a constant
    class); a BrainSMASH class has infinitely many (continuous surrogates)."""
    total = 1.0
    for idx, _, _, kind in _class_parts(y, classes, min_class):
        if kind == "perm":
            total *= math.factorial(idx.size)
        elif kind == "field":
            if method == "brainsmash":
                return float("inf")
            if method != "msr":
                raise ValueError(method)
            total *= 2.0 ** (idx.size - 1)
    return total


def stratified_exact(y: np.ndarray, D: np.ndarray, classes: np.ndarray, method: str, min_class: int = 10) -> np.ndarray:
    """Every pattern of the stratified randomisation (the Cartesian product over classes of each class's MSR sign
    patterns or within-class permutations; class means kept). The identity pattern is included, so with
    p = (k + 1)/(N + 1) the smallest attainable p is 2/(N + 1) (prereg_amend_3 §2). Only for a finite pattern count."""
    y = np.asarray(y, dtype=float)
    per = []
    for idx, mu, r, kind in _class_parts(y, classes, min_class):
        if kind == "const":
            states = r[None, :]
        elif kind == "perm":
            states = np.array([r[list(p)] for p in itertools.permutations(range(idx.size))])
        elif method == "msr":
            ms = MoranSpectral(D[np.ix_(idx, idx)])
            coef = ms.V.T @ r
            E = np.array(list(itertools.product((1.0, -1.0), repeat=coef.size)))  # row 0 = identity
            states = (E * coef) @ ms.V.T
        else:
            raise ValueError(f"{method}: a class of {idx.size} parcels has no finite pattern set")
        per.append((idx, mu, states))
    grids = np.meshgrid(*[np.arange(len(s)) for _, _, s in per], indexing="ij")
    choice = [g.ravel() for g in grids]
    out = np.empty((choice[0].size, y.size))
    for (idx, mu, states), ch in zip(per, choice):
        out[:, idx] = mu + states[ch]
    return out


def site_null(y: np.ndarray, D: np.ndarray, classes: np.ndarray, n: int, seed: int, method: str,
              min_class: int = 10) -> tuple[np.ndarray, dict]:
    """Audit-level S1c / S2c (prereg §4.2; prereg_amend_3 §2 resolution). If the map's stratified randomisation has at
    most n patterns, every pattern is enumerated exactly (floor 2/(N + 1), the identity included); otherwise n random
    surrogates by stratified_surrogates (floor 1/(n + 1)). info: n_patterns, exact, n_null, floor."""
    N = stratified_patterns(y, classes, method, min_class)
    if N <= n:
        s = stratified_exact(y, D, classes, method, min_class)
        assert len(s) == int(N), (len(s), N)
        return s, dict(n_patterns=N, exact=True, n_null=len(s), floor=2 / (len(s) + 1))
    s = stratified_surrogates(y, D, classes, n, seed, method, min_class)
    return s, dict(n_patterns=N, exact=False, n_null=n, floor=1 / (n + 1))


# ---- independent spatial fields for plant families (never BrainSMASH: prereg §6.2) -----------------------
class FieldGenerator:
    """Independent random fields on parcel centroids: Gaussian-kernel GRF (length in mm) or SAR with a
    row-normalised k-nearest-neighbour weight matrix (rho), plus an optional random tissue-class step."""

    def __init__(self, xyz: np.ndarray, classes: np.ndarray):
        self.D = centroid_distance(xyz)
        self.n = len(xyz)
        self.classes = np.asarray(classes)
        self._chol = {}
        self._sar = {}

    def grf(self, length: float, rng) -> np.ndarray:
        if length not in self._chol:
            K = np.exp(-(self.D / length) ** 2)
            self._chol[length] = np.linalg.cholesky(K + 1e-6 * np.eye(self.n))
        return self._chol[length] @ rng.standard_normal(self.n)

    def sar(self, rho: float, rng, knn: int = 6) -> np.ndarray:
        if rho not in self._sar:
            W = np.zeros((self.n, self.n))
            nb = np.argsort(self.D, 1)[:, 1: knn + 1]
            for i, row in enumerate(nb):
                W[i, row] = 1.0 / knn
            self._sar[rho] = np.linalg.inv(np.eye(self.n) - rho * W)
        return self._sar[rho] @ rng.standard_normal(self.n)

    def field(self, kind: str, rng, step: float = 0.0) -> np.ndarray:
        """kind in {'grf15','grf30','grf60','sar5','sar9'}; step = SD of the random per-class offset,
        in units of the field SD (0 = no class step)."""
        f = self.grf(float(kind[3:]), rng) if kind.startswith("grf") else self.sar(float(kind[3:]) / 10, rng)
        f = (f - f.mean()) / f.std()
        if step:
            offs = {c: rng.standard_normal() * step for c in np.unique(self.classes)}
            f = f + np.array([offs[c] for c in self.classes])
        return f
