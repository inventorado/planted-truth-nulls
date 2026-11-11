"""Module generator for the A1 mirror-null plants (prereg_amend_3 §4): spherical k-means of z-scored gene profiles over
a class's analysis parcels (whole expression), the same algorithm as explore/discovery/ahba_modules.py. Independent of
all three species nulls (G1 uniform sets; G6s spectral sign flips; G6l seed-and-window sets)."""
from __future__ import annotations

import numpy as np


def unit_profiles(X: np.ndarray) -> np.ndarray:
    """parcels x genes -> genes x parcels, each row z-scored then unit norm (dot product = Pearson r)."""
    X = np.asarray(X, dtype=float)
    sd = X.std(0)
    Z = ((X - X.mean(0)) / np.where(sd > 0, sd, 1)).T
    n = np.linalg.norm(Z, axis=1, keepdims=True)
    return Z / np.where(n > 0, n, 1)


def spherical_kmeans(P: np.ndarray, k: int, seed: int, n_init: int = 20, iters: int = 100) -> np.ndarray:
    rng = np.random.default_rng(seed)
    best, best_obj = None, -np.inf
    for _ in range(n_init):
        C = P[rng.choice(len(P), k, replace=False)]
        for _ in range(iters):
            lab = np.argmax(P @ C.T, 1)
            C_new = np.stack([P[lab == j].sum(0) if (lab == j).any() else P[rng.integers(len(P))] for j in range(k)])
            C_new /= np.linalg.norm(C_new, axis=1, keepdims=True)
            if np.allclose(C_new, C):
                break
            C = C_new
        obj = float(np.sum(np.max(P @ C.T, 1)))
        if obj > best_obj:
            best, best_obj = np.argmax(P @ C.T, 1), obj
    return best


CLASS_SEED = {"aal": 20260925, "dk": 20260926, "cc200": 20260927}  # 20260924 + class id (aal 1, dk 2, cc200 3)


def class_modules(X: np.ndarray, atlas: str, k: int = 64) -> list[np.ndarray]:
    """The registered k = 64 clusters for a class, as arrays of gene indices."""
    lab = spherical_kmeans(unit_profiles(X), k, CLASS_SEED[atlas])
    return [np.flatnonzero(lab == j) for j in range(k)]
