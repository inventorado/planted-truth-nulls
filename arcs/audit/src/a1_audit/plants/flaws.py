"""Plant-only flawed legs (RUN_PLAN.md v3.1 §7 P25 (a)-(c), P26), each behind a plant-only flag a real run refuses.

None of these legs is a valid null: they are the planted flaws the P24 / P26 regime must catch (amendment 3's
precedent for reference legs that are not valid nulls, prereg_amend_3.md:174-178; RUN_PLAN R2 :481-484). They are
computed only inside `enabled(flag, plant, run_kind)`, which refuses (PlantOnlyRefused):
- any run_kind other than 'plant' (a real run never enables a flag);
- a flag outside its plant (v2-species-max, species-min, unconditioned-g1-g3m: P25; within-class-permutation: P26).
Every flawed function first checks its flag is enabled (else PlantOnlyRefused). a1_audit.run has no option that
reaches this module (its argparse refuses any unknown option, exit 2), and no a1_audit production module imports it
(tests/test_plants_wp2.py asserts both).

The legs (P25: the decoded-list adapter, statistic <y^, .> / n on the z-scored matrix; P26: any full form; every p
one-sided in both directions, (k + 1)/(n + 1)):
- v2_species_max (P25 (a); amendment 3 §4's reference leg 'the v2 species max (G1, universe-centred G6s, G6l; no brain
  matching)', asdg.species.WithinClassBasis.v2_species): G1 on whole (unconditioned) null scores; G6s centred on the
  universe mean profile mu^w (no brain-fraction matching); G6l = the claim's own v3 windows rescored unconditioned
  (unmatched / degenerate -> no p); max of the three. PLANT CHOICE (not in §7): the v2 G1 and G6s reuse the correct
  G1 (leg 2) and G6s (leg 4) streams, i.e. the same null sets / sign draws scored the flawed way (common random
  numbers; the frozen v2 leg drew its own from the claim's stream), and the G6l windows are the claim's own (as frozen).
- species_min (P25 (b)): the minimum instead of the maximum over the four correct species legs. PLANT CHOICE (not in
  §7): a leg without a p (G6l unmatched / degenerate) is left out of the minimum.
- unconditioned_g1_g3m (P25 (c); R2's reference leg 'mean of whole r over R'): the leg-2 G1 sets and the leg-3 G3m
  sets (the correct legs' streams, same sets) scored unconditioned, mean of the whole per-gene statistic over R.
- within_class_permutation (P26): K within-class parcel-label permutations of y (class means kept, spatial
  autocorrelation destroyed) in place of S1c / S2c, the form's T refit on each (T_maps). PLANT CHOICE (not in §7): K =
  500 (the site leg's plant K), its stream SeedSequence([20260925, 900, plant_id, case, class_id, 90]) (a plant-only leg
  word), classes permuted in np.unique order by rng.permuted on each class's columns.
"""
from __future__ import annotations

import contextlib

import numpy as np

from .. import adapters as AD

FLAGS = {"v2-species-max": "P25", "species-min": "P25", "unconditioned-g1-g3m": "P25",
         "within-class-permutation": "P26"}
_ENABLED: set = set()


class PlantOnlyRefused(RuntimeError):
    """A plant-only flawed leg asked for outside a plant run of its plant."""


@contextlib.contextmanager
def enabled(flag: str, plant: str, run_kind: str):
    if run_kind != "plant":
        raise PlantOnlyRefused(f"plant-only flag {flag!r} refused: run kind {run_kind!r} (a real run never enables it)")
    if FLAGS.get(flag) != plant:
        raise PlantOnlyRefused(f"plant-only flag {flag!r} refused for {plant!r} (it belongs to {FLAGS.get(flag)!r})")
    _ENABLED.add(flag)
    try:
        yield
    finally:
        _ENABLED.discard(flag)


def _require(flag: str) -> None:
    if flag not in _ENABLED:
        raise PlantOnlyRefused(f"plant-only leg {flag!r} called without its plant-only flag")


def _decoded(adapter) -> None:
    if type(adapter) is not AD.DecodedList:
        raise TypeError("the P25 flawed legs act on the decoded-list adapter (RUN_PLAN §7 P25)")


def v2_species_max(adapter, K: int, seed_of, g6l_sets, g6l_status: str) -> dict:
    _require("v2-species-max")
    _decoded(adapter)
    B = adapter.basis  # the z-scored basis (adapters.z_basis)
    S = adapter.S
    obs = adapter.T_obs  # <y^, s_z(S)> / n = mean_S r_g
    g1 = np.concatenate([adapter.T_sets(c) for c in AD.g1_set_chunks(B.G, S, int(K),
                                                                      np.random.default_rng(seed_of("G1")))])
    g6s = adapter.T(B.g6s_scores(S, int(K), np.random.default_rng(seed_of("G6s")), mu=B.mu_w))
    p = {"G1 (whole, unconditioned)": AD.p_both(g1, obs), "G6s (centred on mu^w)": AD.p_both(g6s, obs)}
    if g6l_sets is not None and g6l_status == "ok":
        p["G6l (own windows, unconditioned)"] = AD.p_both(adapter.T_sets(g6l_sets), obs)
    else:
        p["G6l (own windows, unconditioned)"] = None
    have = [v for v in p.values() if v is not None]
    vmax = None if len(have) < 3 else {d: max(v[d] for v in have) for d in (1, -1)}
    return dict(p=p, p_max=vmax, rule="max(G1 whole, G6s centred on mu^w, G6l own windows unconditioned); no p if "
                                      "G6l has none (WithinClassBasis.v2_species)")


def species_min(species_p: dict) -> dict:
    _require("species-min")
    have = [v for v in species_p.values() if v is not None]
    return dict(p_min={d: min(v[d] for v in have) for d in (1, -1)}, n_legs=len(have),
                rule="min over the correct species legs that have a p (G1, G3m, G6s, G6l)")


def unconditioned_g1_g3m(adapter, K: int, seed_of) -> dict:
    _require("unconditioned-g1-g3m")
    _decoded(adapter)
    B = adapter.basis
    S = adapter.S
    st = AD.pool_status(B, S)
    out = {}
    if st["G1"]:
        g1 = np.concatenate([adapter.T_sets(c) for c in AD.g1_set_chunks(B.G, S, int(K),
                                                                          np.random.default_rng(seed_of("G1")))])
        out["G1 (unconditioned)"] = AD.p_both(g1, adapter.T_obs)
    else:
        out["G1 (unconditioned)"] = None
    if st["G3m"]:
        g3 = np.concatenate([adapter.T_sets(c) for c in AD.g3m_set_chunks(B.brain, S, int(K),
                                                                          np.random.default_rng(seed_of("G3m")))])
        out["G3m (unconditioned)"] = AD.p_both(g3, adapter.T_obs)
    else:
        out["G3m (unconditioned)"] = None
    return dict(p=out, rule="the leg-2 G1 / leg-3 G3m sets scored by the mean whole per-gene statistic over R (R2's "
                            "reference leg; computed in plants only)")


def within_class_permutation(adapter, K: int, seed: np.random.SeedSequence) -> dict:
    _require("within-class-permutation")
    rng = np.random.default_rng(seed)
    y = np.asarray(adapter.y, dtype=float)
    cl = np.asarray(adapter.ctx.classes)
    Y = np.tile(y, (int(K), 1))
    for c in np.unique(cl):
        idx = np.flatnonzero(cl == c)
        Y[:, idx] = rng.permuted(Y[:, idx], axis=1)
    if not np.allclose(Y[:, :].mean(1), y.mean()):
        raise AssertionError("within-class permutation changed the map's mean")
    null = adapter.T_maps(Y)
    return dict(p=AD.p_both(null, adapter.T_obs), K=int(K),
                rule="within-class parcel-label permutation of y (class means kept), T refit on each (plant only)")
