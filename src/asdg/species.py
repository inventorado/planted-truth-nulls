"""Species leg of the A1 verdict (prereg_amend_3 §3, draft v3): y and the expression matrix stay fixed; the gene
membership is randomised while the set's structure is preserved. Every null set R is evaluated as s_B(S) + s_W(R) — S's
between-class part replaces R's (the conditioning of the class-stratified site leg).

- G1: uniform random sets.   - G3m: random sets with S's size and count of brain>body genes.
- G6s: within-class gene-side Moran spectral randomisation with the exact spectrum, centred on S's brain-fraction-
  matched expected profile mu_S = (f/m) mu_B^w + (1 - f/m) mu_N^w; null s* = s_B + mu_S + U (eps * b), b = U^T (s_W - mu_S).
- G6l: within-class seed-anchored windows (o uniform over in-band offsets; seeds uniform over eligible genes; a pool
  with mean pairwise Jaccard >= .5 is 'degenerate', the frozen J1 rule). Rankings in float64; window sums accumulated in
  float32 (prereg_amend_3 §3).
Every null draw is y-independent: species_many() draws once per claim and scores the draws against several maps
(common random numbers; the paired w maps of §4); species() is its one-map case.
Also: the 'species leg uninformative' rule on w_k = |a_k b_k|, the species legs' resolution floor, and two REFERENCE
legs that are not valid nulls (the v1 draft's G6s and the v2 draft's species max), used only as planted flawed legs the
gates must catch. All p-values one-sided in the registered direction, (k + 1)/(n + 1) (cascade.emp_p).
"""
from __future__ import annotations

import itertools

import numpy as np
from scipy import sparse

from .cascade import corr_matrix, emp_p


class WithinClassBasis:
    def __init__(self, X: np.ndarray, classes: np.ndarray, brain: np.ndarray | None = None):
        """X: analysis parcels x genes (no NaN); classes: tissue class per parcel; brain: gene indices of the
        brain>body background (B) within X's columns."""
        X = np.asarray(X, dtype=float)
        cl = np.asarray(classes)
        assert X.shape[0] == cl.size and np.isfinite(X).all()
        Xw = X.copy()
        for c in np.unique(cl):
            m = cl == c
            Xw[m] -= X[m].mean(0)
        self.X, self.Xw, self.classes = X, Xw, cl
        self.G = X.shape[1]
        self.mu_w = Xw.mean(1)
        self.brain = np.zeros(self.G, bool)
        if brain is not None:
            self.brain[np.asarray(brain, dtype=int)] = True
        self.mu_B = Xw[:, self.brain].mean(1) if self.brain.any() else self.mu_w
        self.mu_N = Xw[:, ~self.brain].mean(1) if (~self.brain).any() else self.mu_w
        self.d_B = self.mu_B - self.mu_w  # the brain-enrichment profile (T-brain target)
        U, s, _ = np.linalg.svd(Xw - self.mu_w[:, None], full_matrices=False)
        self.U = U[:, s > 1e-10 * s[0]]
        nrm = np.linalg.norm(Xw, axis=0)
        self.Zw = Xw / np.where(nrm > 0, nrm, 1.0)  # unit-norm columns: within-class Pearson r
        self.ZwT = np.ascontiguousarray(self.Zw.T)  # genes as rows: G6l's window gathers read contiguous memory
        self.ZwT32 = self.ZwT.astype(np.float32)  # G6l window sums are accumulated in float32 (§3)
        tot = X.var(0)
        self.bshare = np.where(tot > 0, 1.0 - Xw.var(0) / np.where(tot > 0, tot, 1.0), 0.0)  # between-class share
        self._U_v1 = None

    # ---- helpers ------------------------------------------------------------------------------------------------
    def parts(self, S):
        s = self.X[:, S].mean(1)
        s_w = self.Xw[:, S].mean(1)
        return s, s - s_w, s_w

    def mu_S(self, S) -> np.ndarray:
        f = self.brain[np.asarray(S)].mean()
        return f * self.mu_B + (1 - f) * self.mu_N

    def coherence_w(self, S) -> float:
        m = len(S)
        v = self.Zw[:, S].sum(1)
        return float((v @ v - m) / (m * (m - 1)))

    def within_y(self, y) -> np.ndarray:
        y = np.asarray(y, dtype=float).copy()
        for c in np.unique(self.classes):
            m = self.classes == c
            y[m] -= y[m].mean()
        return y

    def uninformative(self, S, y) -> tuple[bool, float]:
        """§2: w_k = |a_k b_k|; flagged if max_k w_k / sum_k w_k > .8 (G6s's null degenerates to +-T)."""
        s, s_b, s_w = self.parts(S)
        w = np.abs((self.U.T @ self.within_y(y)) * (self.U.T @ (s_w - self.mu_S(S))))
        share = float(w.max() / w.sum()) if w.sum() > 0 else 1.0
        return share > 0.8, share

    def membership(self, sets: np.ndarray):
        """Sparse 0/1 matrix (sets x genes)."""
        k, m = sets.shape
        return sparse.csr_matrix((np.ones(k * m), (np.repeat(np.arange(k), m), np.asarray(sets).ravel())),
                                 shape=(k, self.G))

    def set_means(self, A: np.ndarray, sets: np.ndarray, M=None) -> np.ndarray:
        """(sets x parcels) mean of A's columns over each row of sets (no sets x m x parcels copy)."""
        M = self.membership(sets) if M is None else M
        return np.asarray(M @ A.T) / sets.shape[1]

    def conditioned_null(self, S, sets: np.ndarray, M=None) -> np.ndarray:
        """Null scores s_B(S) + s_W(R) for each row R of sets."""
        s_b = self.parts(S)[1]
        return s_b[None, :] + self.set_means(self.Xw, sets, M)

    def _p(self, S, y, null_scores, sign) -> float:
        r_obs = corr_matrix(y, self.parts(S)[0])[0, 0]
        return emp_p(corr_matrix(null_scores, y)[:, 0], r_obs, sign)

    # ---- null builders (y-independent; drawn once per claim) ------------------------------------------------------
    def g1_null(self, S, K, rng) -> np.ndarray:
        pool = np.setdiff1d(np.arange(self.G), S)
        return self.conditioned_null(S, np.stack([rng.choice(pool, size=len(S), replace=False) for _ in range(K)]))

    def g3m_sets(self, S, K, rng) -> np.ndarray:
        S = np.asarray(S)
        f = int(self.brain[S].sum())
        pb = np.setdiff1d(np.flatnonzero(self.brain), S)
        pn = np.setdiff1d(np.flatnonzero(~self.brain), S)
        return np.stack([np.concatenate([rng.choice(pb, size=f, replace=False),
                                         rng.choice(pn, size=len(S) - f, replace=False)]) for _ in range(K)])

    def g3m_null(self, S, K, rng) -> np.ndarray:
        return self.conditioned_null(S, self.g3m_sets(S, K, rng))

    def g6s_exact(self, K) -> bool:
        return 2 ** self.U.shape[1] <= K

    def g6s_scores(self, S, K, rng, mu=None) -> np.ndarray:
        s, s_b, s_w = self.parts(S)
        mu = self.mu_S(S) if mu is None else mu
        b = self.U.T @ (s_w - mu)
        if self.g6s_exact(K):  # exact enumeration of every sign pattern (§2 resolution)
            E = np.array(list(itertools.product((-1.0, 1.0), repeat=b.size)))
        else:
            E = rng.choice(np.array([-1.0, 1.0]), size=(K, b.size))
        return s_b + mu + (E * b) @ self.U.T

    def window_curve(self, g, S, m, n_rank, half, C0):
        """Seed g's ranking (float64 within-class r over genes not in S or g) and c(W(o)) for o = 0 .. half, the window
        sums accumulated in float32 in the preallocated buffer C0 ((half + m) x parcels, row 0 = 0)."""
        r = self.ZwT @ self.ZwT[g]
        r[S] = -np.inf
        r[g] = -np.inf
        rank = np.argsort(-r, kind="stable")[:n_rank]
        np.cumsum(self.ZwT32[rank[: half + m - 1]], axis=0, out=C0[1:])
        v = C0[m - 1: m - 1 + half + 1] - C0[: half + 1]
        v += self.ZwT32[g]
        return rank, (np.einsum("ij,ij->i", v, v, dtype=np.float64) - m) / (m * (m - 1))

    def g6l_sets(self, S, K, rng, tol=0.02, budget_factor=5, min_seeds=50, exact=False):
        """(sets (n x m) or None, info). exact=True screens every gene (audit); otherwise rejection-samples seeds up
        to budget_factor * K draws and stops at K accepted (plants)."""
        S = np.asarray(S)
        m, G = len(S), self.G
        c_s = self.coherence_w(S)
        not_s = np.setdiff1d(np.arange(G), S)
        seeds = not_s if exact else rng.permutation(not_s)[: budget_factor * K]
        accepted, draws, eligible = [], 0, 0
        n_rank = G - m - 1
        half = n_rank // 2
        C0 = np.empty((half + m, self.ZwT32.shape[1]), np.float32)
        C0[0] = 0.0
        for g in seeds:
            draws += 1
            rank, c = self.window_curve(g, S, m, n_rank, half, C0)
            offs = np.flatnonzero(np.abs(c - c_s) <= tol)
            if offs.size:
                eligible += 1
                o = int(rng.choice(offs))
                accepted.append(np.concatenate([[g], rank[o: o + m - 1]]))
                if not exact and len(accepted) >= K:
                    break
        info = dict(c_s=c_s, n=len(accepted), draws=draws, eligible=eligible, exact=exact)
        if len(accepted) < min_seeds:
            return None, {**info, "status": "unmatched"}
        sets = np.stack(accepted)
        if exact and len(sets) > K:
            sets = sets[rng.choice(len(sets), size=K, replace=False)]
        return sets, {**info, "status": "ok"}

    def g6l_null(self, S, K, rng, **kw):
        """(conditioned window scores or None, info with the pool descriptors and status ok / unmatched / degenerate).
        Degenerate = mean pairwise Jaccard >= .5 (the frozen J1 pool-diversity rule, prereg.md §4.4)."""
        sets, info = self.g6l_sets(S, K, rng, **kw)
        info["eligible_frac"] = info["eligible"] / max(info["draws"], 1)
        if sets is None:
            return None, info
        M = self.membership(sets)
        null = self.conditioned_null(S, sets, M)
        C = corr_matrix(null, null)
        iu = np.triu_indices(len(null), 1)
        inter = (M @ M.T).toarray()[iu]
        m = sets.shape[1]
        info.update(pool_coh_signed=float(C[iu].mean()), pool_coh_abs=float(np.abs(C[iu]).mean()),
                    s_pool_corr=float(corr_matrix(self.parts(S)[0], null)[0].mean()),
                    pool_jaccard=float(np.mean(inter / (2 * m - inter))),
                    seed_bshare=float(self.bshare[sets[:, 0]].mean()), sets=sets)  # sets: internal, never written
        if info["pool_jaccard"] >= 0.5:
            info["status"] = "degenerate"
        return null, info

    # ---- one leg against one map --------------------------------------------------------------------------------
    def g1(self, S, y, K, rng, sign=1) -> float:
        return self._p(S, y, self.g1_null(S, K, rng), sign)

    def g3m(self, S, y, K, rng, sign=1) -> float:
        return self._p(S, y, self.g3m_null(S, K, rng), sign)

    def g6s(self, S, y, K, rng, sign=1) -> float:
        return self._p(S, y, self.g6s_scores(S, K, rng), sign)

    def g6l(self, S, y, K, rng, sign=1, **kw):
        null, info = self.g6l_null(S, K, rng, **kw)
        return (self._p(S, y, null, sign) if info["status"] == "ok" else float("nan")), info

    # ---- species leg ----------------------------------------------------------------------------------------------
    def species_many(self, S, ys, K, rng, sign=1, alpha=0.025, return_sets=False) -> list[dict]:
        """The species leg of one set against each map in ys: the null draws (G1 and G3m sets, G6s signs, G6l
        windows, in that order) are made once and scored against every map."""
        N1, N3 = self.g1_null(S, K, rng), self.g3m_null(S, K, rng)
        N6s = self.g6s_scores(S, K, rng)
        N6l, info = self.g6l_null(S, K, rng)
        n6s = 2 ** self.U.shape[1] if self.g6s_exact(K) else K
        floors = [1 / (K + 1), 2 / (n6s + 1) if self.g6s_exact(K) else 1 / (K + 1)]  # exact: identity pattern counts
        if info["status"] == "ok":
            floors.append(1 / (info["n"] + 1))
        min_p = max(floors)
        common = dict(species_min_p=min_p, resolution_limited=bool(min_p >= alpha), g6l_status=info["status"],
                      g6l_n=info["n"], g6l_draws=info["draws"], g6l_eligible=info["eligible"],
                      g6l_eligible_frac=info["eligible_frac"], g6l_pool_coh_signed=info.get("pool_coh_signed", np.nan),
                      g6l_pool_coh_abs=info.get("pool_coh_abs", np.nan), g6l_s_pool_corr=info.get("s_pool_corr", np.nan),
                      g6l_pool_jaccard=info.get("pool_jaccard", np.nan), g6l_seed_bshare=info.get("seed_bshare", np.nan),
                      universe_bshare=float(self.bshare.mean()))
        out = []
        for y in ys:
            p1, p3, p6s = self._p(S, y, N1, sign), self._p(S, y, N3, sign), self._p(S, y, N6s, sign)
            p6l = self._p(S, y, N6l, sign) if info["status"] == "ok" else float("nan")
            flag, share = self.uninformative(S, y)
            out.append(dict(p_G1=p1, p_G3m=p3, p_G6s=p6s, p_G6l=p6l,
                            p_species=np.nan if np.isnan(p6l) else max(p1, p3, p6s, p6l),
                            uninformative=flag, top_w_share=share, **common,
                            **({"g6l_sets": info.get("sets")} if return_sets else {})))
        return out

    def species(self, S, y, K, rng, sign=1, alpha=0.025, return_sets=False) -> dict:
        return self.species_many(S, [y], K, rng, sign, alpha, return_sets)[0]

    # ---- reference legs (NOT valid nulls; planted flawed legs of §5) ------------------------------------------------
    def g6s_v1_flawed(self, S, y, K, rng, sign=1) -> float:
        """v1 draft: sign flips of the gene-centred whole-expression score, the shared gene-mean profile included."""
        if self._U_v1 is None:
            Xc = self.X - self.X.mean(0)
            U, s, _ = np.linalg.svd(Xc, full_matrices=False)
            self._U_v1 = U[:, s > 1e-10 * s[0]]
        s = self.parts(S)[0]
        b = self._U_v1.T @ (s - s.mean())
        E = rng.choice(np.array([-1.0, 1.0]), size=(K, b.size))
        return emp_p(corr_matrix((E * b) @ self._U_v1.T, y)[:, 0], corr_matrix(y, s)[0, 0], sign)

    def v2_species(self, S, y, K, rng, sign=1, g6l_sets="draw") -> float:
        """v2 draft's species max: G1 and G6l on whole (unconditioned) null scores, G6s centred on the universe mean
        profile mu_w (no brain-fraction matching, no G3m). g6l_sets: 'draw' draws its own windows; otherwise the v3 G6l
        windows of the same claim are rescored unconditioned (None = unmatched / degenerate -> NaN)."""
        s = self.parts(S)[0]
        r_obs = corr_matrix(y, s)[0, 0]
        pool = np.setdiff1d(np.arange(self.G), S)
        g1 = np.stack([rng.choice(pool, size=len(S), replace=False) for _ in range(K)])
        p1 = emp_p(corr_matrix(self.set_means(self.X, g1), y)[:, 0], r_obs, sign)
        p6s = emp_p(corr_matrix(self.g6s_scores(S, K, rng, mu=self.mu_w), y)[:, 0], r_obs, sign)
        sets = self.g6l_sets(S, K, rng)[0] if isinstance(g6l_sets, str) else g6l_sets
        if sets is None:
            return float("nan")
        p6l = emp_p(corr_matrix(self.set_means(self.X, sets), y)[:, 0], r_obs, sign)
        return max(p1, p6s, p6l)
