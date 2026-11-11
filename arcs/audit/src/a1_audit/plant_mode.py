"""Plant-mode G6l (arcs/audit/RUN_PLAN.md v3.1, FROZEN sha256 16c60232...: §7 cost model :1090-1093; prereg_amend_3.md
§3 :130-132), a mode flag the runner passes through to the adapters.

The frozen text (prereg_amend_3.md:130-132): "Null set: eligible seed (uniform, without replacement), o uniform over O_g.
Plants: seeds screened in random order until K = 200 are accepted, with a budget of 5·K = 1,000 seed draws; audit: every
gene screened, exact enumeration if N_elig < K = 10,000. Fewer than 50 eligible seeds -> 'unmatched'." RUN_PLAN §7
(:1092-1093): "plant K = 500 surrogates per site null and K = 200 species draws, with G6l in amendment 3's plant mode
(K = 200 accepted, budget 1,000 seeds)".

The engine already implements plant mode: asdg.species.WithinClassBasis.g6l_sets(S, K, rng, exact=False) (src/asdg/
species.py:147-176: rng.permutation of the non-S genes cut to budget_factor * K = 5 K draws, one rng.choice over the
in-band offsets per eligible seed, stop at K accepted). adapters.py has no plant-mode path (its g6l_screen_safe is the
exact audit screen), and adapters.py is not edited: this module wraps the engine call so it returns the (sets, info)
pair the adapters accept as their pre-screened `g6l` argument (adapters.species_null_scores / TAbs.species_leg), with
the same R8 no-window rule as adapters.g6l_screen_safe and the info field the adapters read (n_used). Each stream is
screened on its own (plant mode draws the seed order from the stream itself, so one screen cannot serve two streams);
the call is otherwise the engine's, unchanged. RUN_PLAN_amend_1 R33 (FROZEN sha256 8e06d60e...): where a window of size
m fits only part of the offset range [0, half], the offsets are o in [0, min(half, n_rank - m + 1)] -
adapters.g6l_sets_range(..., exact=False), which equals the engine's g6l_sets wherever the full range fits.

Exact mode stays adapters.g6l_screen_safe / verdict.shared_g6l, untouched (tests/test_p0.py re-run: 19 / 19).
"""
from __future__ import annotations

import numpy as np

from . import adapters as AD

MODE_EXACT = "exact"
MODE_PLANT = "plant"
MODES = (MODE_EXACT, MODE_PLANT)
BUDGET_FACTOR = 5          # prereg_amend_3.md:131 "a budget of 5·K = 1,000 seed draws"
PLANT_K_ACCEPTED = 200     # prereg_amend_3.md:130-131; RUN_PLAN.md:1092-1093
MIN_SEEDS = 50             # prereg_amend_3.md:131-132
TOL = 0.02                 # prereg_amend_3.md:126
MODE_TEXT = ("plant mode (prereg_amend_3.md §3 :130-131: seeds screened in random order until K are accepted, budget "
             "5 K seed draws; RUN_PLAN.md:1092-1093: K = 200 accepted, budget 1,000)")


def g6l_plant_screen(B, S, rngs, K: int) -> list:
    """Amendment 3's plant-mode G6l for each stream in `rngs`: B.g6l_sets(S, K, rng, tol=.02, budget_factor=5,
    min_seeds=50, exact=False), one call per stream. Returns [(sets or None, info)] as adapters.g6l_screen_safe does
    (info carries n_used = the windows kept and mode = 'plant'). R8: no window of size m fits the ranking -> no eligible
    seed -> 'unmatched' for every stream; a window that fits only part of the offset range -> adapters.g6l_sets_range
    (RUN_PLAN_amend_1 R33)."""
    S = AD._as_set(S, B.G)
    K = int(K)
    if K < 1:
        raise ValueError("plant-mode G6l needs K >= 1")
    st = AD.pool_status(B, S)
    out = []
    for rng in rngs:
        if st["G6l"] == "no window":
            info = dict(c_s=float(B.coherence_w(S)), n=0, draws=0, eligible=0, exact=False, status="unmatched",
                        n_used=0, mode=MODE_PLANT,
                        reason="no window of size m fits the ranking: no eligible seed (RUN_PLAN R8)")
            out.append((None, info))
            continue
        if st["G6l"] == "partial":  # RUN_PLAN_amend_1 R33: offsets o <= n_rank - m + 1
            sets, info = AD.g6l_sets_range(B, S, K, rng, tol=TOL, budget_factor=BUDGET_FACTOR, min_seeds=MIN_SEEDS,
                                           exact=False)
            info = dict(info)
            info["offset_range"] = "R33 partial: o in [0, %d]" % AD.g6l_offset_max(B.G, S.size)
        else:
            sets, info = B.g6l_sets(S, K, rng, tol=TOL, budget_factor=BUDGET_FACTOR, min_seeds=MIN_SEEDS, exact=False)
            info = dict(info)
        info["n_used"] = 0 if sets is None else int(len(sets))
        info["mode"] = MODE_PLANT
        info["K_accept"] = K
        info["budget"] = BUDGET_FACTOR * K
        out.append((sets, info))
    return out


def screen(mode: str, B, S, rngs, K: int) -> list:
    """The runner's one entry point: exact mode -> adapters.g6l_screen_safe (one pass serving every stream, RUN_PLAN §4
    'Shared G6l screens'); plant mode -> g6l_plant_screen (each stream on its own)."""
    if mode == MODE_EXACT:
        return AD.g6l_screen_safe(B, S, list(rngs), keep=int(K))
    if mode == MODE_PLANT:
        return g6l_plant_screen(B, S, list(rngs), int(K))
    raise ValueError(f"G6l mode must be one of {MODES}, got {mode!r}")


def streams_screen(mode: str, ctx, S, streams, K: int) -> dict:
    """{stream name: (sets, info)} for named SeedSequences, screened on ctx.B (the basis every adapter screens G6l on:
    adapters.species_null_scores' screen_basis = ctx.B). Exact mode IS verdict.shared_g6l (one pass serving every
    stream: RUN_PLAN §4 'Shared G6l screens'); plant mode screens each stream on its own (g6l_plant_screen)."""
    if mode == MODE_EXACT:
        from . import verdict as V
        return V.shared_g6l(ctx, S, streams, int(K))
    names = list(streams)
    res = screen(mode, ctx.B, S, [np.random.default_rng(streams[n]) for n in names], K)
    return dict(zip(names, res))
