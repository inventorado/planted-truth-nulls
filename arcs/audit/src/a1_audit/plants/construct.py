"""Plant constructions (RUN_PLAN.md v3.1 §7; prereg §6.1-§6.3; prereg_amend_3 §4). Every value is drawn from the
claim's construction stream (common.PlantKeys.rng()); nothing here draws a null.

- C-gene (prereg §6.3; P3a, P3b, P5, P7, P8, P11, P22): S = 25 uniform genes of the class universe; y = a z(e~_S) +
  sqrt(1 - a^2) field, e~_S = S's set score residualised on [1, the mean score of S's G2 sets, the first 3 PCs of the
  class's expression matrix]. The draw order, the G2 call and the PCs are e3_plants.one_plant's C-gene branch
  (arcs/audit/src/e3_plants.py, the frozen battery behind P3b's basis), line for line: rng.choice(all genes, 25),
  coexpr_matched_sets(U, all, 25, c_S, 500, rng, exclude=S), FieldGenerator.field(gen, rng, step) with generator cell
  i mod 10; G2 unmatched -> 'unmatched for plant' (the frozen battery's status; excluded from its denominator).
- Independent fields (prereg §6.1): FieldGenerator on the class's primary-parcel centroids, generators grf15, grf30,
  grf60, sar5, sar9, class step 0 / 1.
- The aligned maps of amendment 3 §4 are built by its frozen generator (p24 / p25 import e3_align_plants).
"""
from __future__ import annotations

import functools
import math

import numpy as np

from .. import a3_port as A3  # noqa: F401  (src/ on sys.path)
import e3_plants as P  # noqa: E402  (the frozen battery's constants: GENERATOR_CELLS, N_SETS)
from asdg.genesets import coexpr_matched_sets  # noqa: E402
from asdg.spatial import FieldGenerator  # noqa: E402

from . import common as C

GENERATOR_CELLS = tuple(P.GENERATOR_CELLS)    # (generator, step) x 10: prereg §6.1, plant i -> cell i mod 10
GENERATORS = ("grf15", "grf30", "grf60", "sar5", "sar9")
assert tuple(g for g, s in GENERATOR_CELLS if s == 0.0) == GENERATORS
G2_SETS = P.N_SETS                            # 500 (the frozen battery's G2 for the C-gene residual)
M_CGENE = 25                                  # prereg §6.3 "at m = 25"
A_CGENE = 0.9                                 # RUN_PLAN §7 P3a "a = .9"


@functools.lru_cache(maxsize=None)
def aux(cls: str) -> dict:
    """Per class: the field generator on the primary-parcel centroids and the first 3 PCs of the expression matrix
    (e3_plants.Ctx: SVD of the column-centred matrix scaled by the ddof-1 SD)."""
    ctx = C.class_context(cls)
    X = ctx.U.X
    Zc = X - X.mean(0)
    u, s, _ = np.linalg.svd(Zc / X.std(0, ddof=1), full_matrices=False)
    return dict(fg=FieldGenerator(ctx.xyz, ctx.classes), pcs=u[:, :3], all=np.arange(ctx.G))


def field(cls: str, rng, cell: int) -> tuple[np.ndarray, str, float]:
    gen, step = GENERATOR_CELLS[cell % len(GENERATOR_CELLS)]
    return aux(cls)["fg"].field(gen, rng, step), gen, step


def field_kind(cls: str, rng, gen: str, step: float) -> np.ndarray:
    return aux(cls)["fg"].field(gen, rng, step)


def cgene_residual(cls: str, S, G2) -> np.ndarray:
    """e~_S: S's set score residualised on [1, mean G2 score, 3 PCs] (e3_plants.one_plant, C-gene branch)."""
    ctx = C.class_context(cls)
    a = aux(cls)
    score = ctx.U.scores(np.asarray(S))[0]
    Bm = np.column_stack([np.ones(ctx.n), ctx.U.scores(G2).mean(0), a["pcs"]])
    return score - Bm @ np.linalg.lstsq(Bm, score, rcond=None)[0]


def cgene(cls: str, rng, i: int, a: float = A_CGENE, m: int = M_CGENE, sign: int = 1) -> dict:
    """The C-gene plant in e3_plants.one_plant's draw order: S, (score, c_S), G2, field, then y. sign = -1 gives the
    negative-signal map of P8 (PLANT CHOICE, see p08)."""
    ctx = C.class_context(cls)
    al = aux(cls)["all"]
    gen, step = GENERATOR_CELLS[i % len(GENERATOR_CELLS)]
    S = rng.choice(al, size=m, replace=False)
    c_S = ctx.U.mean_coexpr(S)
    G2, i2 = coexpr_matched_sets(ctx.U, al, m, c_S, G2_SETS, rng, exclude=S)
    fld = aux(cls)["fg"].field(gen, rng, step)
    head = dict(gen=gen, step=float(step), m=int(m), a=float(a), c_S=float(c_S), G2_status=i2["status"])
    if G2 is None:
        return dict(head, status="unmatched for plant", S=S, y=None)
    resid = cgene_residual(cls, S, G2)
    y = sign * a * C.z(resid) + math.sqrt(1 - a * a) * fld
    return dict(head, status="ok", S=S, y=y)


def random_set(cls: str, rng, m: int = 25) -> np.ndarray:
    """rand-m: m uniform genes of the class universe (prereg §6.2 F-sp's S; amendment 3 §4 'rand')."""
    return rng.choice(aux(cls)["all"], size=m, replace=False)
