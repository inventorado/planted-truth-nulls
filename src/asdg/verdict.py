"""The A1 verdict at audit level (prereg_amend_3 §2; readings per prereg_amend_5 §3).

A claim survives iff its status is ok and Level 0, the class-stratified site leg (max of S1c, S2c) and the species leg
(max of G1, G3m, G6s, G6l) each have p < alpha_v = .025; conjunction p = max of the three. Status, in order: G6l
unmatched / degenerate; 'species leg uninformative'; 'resolution-limited' (the verdict-level resolution label: the
largest smallest-attainable p over the legs is not below alpha_v, so the claim cannot survive); ok. Each leg's floor is
1/(N + 1) for N random draws, 2/(N + 1) for an exact enumeration that contains the identity pattern (S1c / S2c patterns,
G6s signs) and 1/(N_elig + 1) for G6l over its eligible seeds; Level 0 is parametric (no floor). The site leg's floor is
the larger of S1c's and S2c's.
"""
from __future__ import annotations

import numpy as np

ALPHA_V = 0.025


def resolution(floors: dict[str, float], alpha: float = ALPHA_V) -> dict:
    """The verdict-level resolution label: {'limited', 'max_floor', 'binding'} over the legs' floors."""
    finite = {k: float(v) for k, v in floors.items() if v is not None and np.isfinite(v)}
    mx = max(finite.values()) if finite else 0.0
    return dict(limited=bool(mx >= alpha), max_floor=mx, binding=sorted(k for k, v in finite.items() if v == mx))


def verdict(p_level0: float, site: dict, species: dict, alpha: float = ALPHA_V) -> dict:
    """site: p_S1c, p_S2c and their info dicts (spatial.site_null) as info_S1c, info_S2c; species: one dict of
    WithinClassBasis.species() (p_G1, p_G3m, p_G6s, p_G6l, p_species, species_min_p, g6l_status, uninformative)."""
    p_site = max(site["p_S1c"], site["p_S2c"])
    floors = {"site": max(site["info_S1c"]["floor"], site["info_S2c"]["floor"]), "species": species["species_min_p"]}
    res = resolution(floors, alpha)
    if species["g6l_status"] != "ok":
        status = f"g6l {species['g6l_status']}"
    elif species["uninformative"]:
        status = "uninformative"
    elif res["limited"]:
        status = "resolution-limited"
    else:
        status = "ok"
    p = max(p_level0, p_site, species["p_species"]) if status == "ok" else float("nan")
    return dict(status=status, p_level0=p_level0, p_site=p_site, p_species=species["p_species"], p_verdict=p,
                survives=bool(status == "ok" and p < alpha), floors=floors, resolution=res)
