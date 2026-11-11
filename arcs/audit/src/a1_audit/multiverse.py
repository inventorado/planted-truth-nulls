"""R11 multiverse plumbing (arcs/audit/RUN_PLAN.md v3.1 R11 :661-690), read by RUN_PLAN_amend_2.md v2.1 R39 (FROZEN
acdb1290...; "Multiverse cells: their parcels and counts; no crossing with >= 2 donors; MIST64"). Plant P22 (pinned
plants/p22.py) and its R39 extension (tests/test_amend2.py).

R11 (quoted): "Mini-multiverse: every surviving claim ... (srs, True) is the primary, and the cells are (zscore, True),
(srs, False) and (zscore, False). Add the bilateral cell and leave-one-out x 6: 10 cells. Each cell re-runs every leg
(T, Level 0, the site leg, the species leg and the descriptor legs) with the claim's own keys (common random numbers)."
R7 :548: "Multiverse, leave-one-out and >= 2-donor cells reuse the claim's keys (common random numbers; R11)."

R39 (RUN_PLAN_amend_2.md:199-214), as implemented here:
- Each cell is an analysis: a parcel enters iff y is finite there and THE CELL'S OWN matrix has >= 1 sample there. The
  cells' counts: the normalisation cells the primary's counts (CellSources refuses other counts for them); a
  leave-one-out cell the per-donor counts without the left-out donor (given as `counts`; asserted zero exactly where the
  cell matrix's row is empty, as ahba_builds.derive_loo checks them); the bilateral cell those of its bidirectional
  build (given as `counts`, the same assertion). Kept and dropped parcels are reported per cell (parcel_report, in every
  run_cell record of a cell as 'cell_parcels').
- Parcel universe: the normalisation and leave-one-out cells the primary parcels (L + B, the class context's parcels);
  the bilateral cell EVERY parcel of the class's tissue classes, L, R and B, with atlas_info classes and centroids
  (`bilateral`: the build's atlas_info rows, centroids and the map on those parcels). A left-only map's bilateral cell
  is "not applicable (map defined on the left hemisphere only)" (R11 :684-685).
- Parcel-set check: run_cell asserts that the analysis parcels equal R39's set, computed from R39's definition
  (expected_parcels) on a path separate from the context build; a cell built on another parcel set (for example a
  bilateral cell restricted to the primary parcels) raises CellParcelSetError (a functional defect).
- Not crossed with the >= 2-donor sensitivity (prereg.md:57; R11 'beside the primary'): run_cell runs the primary
  entry rule only, and a cell's donor_counts refuses (NOT_CROSSED), so no >= 2-donor x cell record can be made. 10 cells.
- MIST64: no cell is ever run (cells_for returns none; R11's matrix list has no MIST64 multiverse build); MIST64's
  >= 2-donor counts stay (the sensitivity pass, not here).
- A parcel-set change in a cell can change a leg's exactness: amendment 1's R32 then applies through the production
  legs unchanged (verdict.collect_legs asserts R32 (c)'s floors on every exact leg).

DEV declaration (RUN_PLAN_amend_2 §8.1 / §8.2): this module was pinned by blob (564aa4c5 at 4ad80ec) for the DEV
declaration and changed after the freeze as R39 requires; THE OFFICIAL P22 RUNS ON THIS R39 CODE with plants/p22.py
unchanged (blob 2b191232). p22.py's calls keep their meaning: CellSources(base, PRIMARY | '(zscore, True)', matrix)
(the primary's universe and counts); CellSources(base, 'leave-one-donor-out 1', matrix) without counts (the cell's
counts read from its matrix: zero exactly where the row is empty, else the primary's; recorded as such; a production
leave-one-out cell passes its per-donor counts); run_cell(...) (its records gain 'cell_parcels' for cells only).

What this module does: a claim's sources (run.Sources) with its class context rebuilt on a cell's matrix and parcel
universe - CellSources - and one cell run through the production calls (run.prepare, plant_mode.streams_screen /
verdict.shared_g6l, run.g_legs, verdict.assemble_verdict_a1, run.g_descriptors) with the claim's own seed callables. The
cell's context keeps the class's brain>body rule (ClassContext's brain_fn, applied to the cell's universe). A parcel
whose row in the cell's matrix is entirely missing has no AHBA sample in that cell (count 0): it is left out of the
context and of the map and reported. A row partly missing is refused (no frozen reading).

Not here: building the cell matrices (venv_ref builds, R11 'Matrices'), the 'donor-robust' reading and the survivors'
batches (§14) - those consume this path.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import a3_port as A3
from . import plant_mode as PM
from . import run as R
from . import verdict as V

PRIMARY = "(srs, True) primary"
NORMALISATION_CELLS = ("(zscore, True)", "(srs, False)", "(zscore, False)")
BILATERAL = "bilateral"
LOO_CELLS = tuple(f"leave-one-donor-out {k}" for k in range(1, 7))
CELLS = NORMALISATION_CELLS + (BILATERAL,) + LOO_CELLS  # R11's 10 cells, in R11's order (§14: batches by this order)
assert len(CELLS) == 10
NOT_COMPUTABLE_CELL = "not computable (multiverse cell: %s)"
NOT_APPLICABLE_LEFT_ONLY = "not applicable (map defined on the left hemisphere only)"   # R11 :684-685
NOT_CROSSED = ("not crossed: the >= 2-donor sensitivity is not run in a multiverse cell (RUN_PLAN_amend_2 R39; "
               "prereg.md:57; R11 'beside the primary')")
NO_CELL_MIST64 = ("no multiverse cell: MIST64 (RUN_PLAN_amend_2 R39: no cell is ever run, so R11's matrix list is "
                  "complete; MIST64's >= 2-donor counts stay)")
CELL_RUN = "run"
HEMISPHERES = ("L", "R", "B")
INFO_COLUMNS = ("label", "hemisphere", "structure")
COUNTS_PRIMARY = "the primary's counts (R39: normalisation cells)"
COUNTS_GIVEN_LOO = "the per-donor counts without the left-out donor (given; R39)"
COUNTS_GIVEN_BILATERAL = "the bidirectional build's counts (given; R39)"
COUNTS_FROM_MATRIX = ("read from the cell matrix: 0 where the row is empty, else the primary's (no per-donor counts "
                      "given; the entry rule only)")


class CellParcelSetError(AssertionError):
    """A cell's analysis parcels differ from R39's set (a functional defect: the run stops)."""


def matrix_sha(expr: pd.DataFrame) -> str:
    return R.arr_sha(expr.to_numpy(dtype=float), np.asarray(expr.index, dtype=np.int64),
                     np.asarray(expr.columns, dtype=str))


def cells_for(plan: dict, *, left_only_map: bool) -> list:
    """R11 / R39: the cells a surviving claim requests, in R11's order, each with its status ('run' or R11's 'not
    applicable' for the bilateral cell of a left-only map). A MIST64 claim requests no cell (R39)."""
    if plan["analysis_class"] == "MIST64":
        return []
    return [dict(cell=c, status=NOT_APPLICABLE_LEFT_ONLY if (c == BILATERAL and left_only_map) else CELL_RUN)
            for c in CELLS]


def no_cell_reason(plan: dict) -> str | None:
    return NO_CELL_MIST64 if plan["analysis_class"] == "MIST64" else None


def bilateral_universe(info: pd.DataFrame, tissue_classes) -> list:
    """R39: every parcel of the class's tissue classes, hemisphere L, R or B (atlas_info classes), in info's order.
    A hemisphere outside L / R / B is refused."""
    _check_info(info)
    hemi = info["hemisphere"].astype(str)
    if not set(hemi) <= set(HEMISPHERES):
        raise ValueError("bilateral cell: atlas_info hemispheres outside L / R / B")
    tc = {str(c) for c in tissue_classes}
    return [int(i) for i, s in zip(info.index, info["structure"].astype(str)) if s in tc]


def _check_info(info) -> None:
    if not isinstance(info, pd.DataFrame) or any(c not in info.columns for c in INFO_COLUMNS):
        raise ValueError(f"bilateral cell: atlas_info must be a DataFrame with columns {list(INFO_COLUMNS)}")
    if not info.index.is_unique:
        raise ValueError("bilateral cell: atlas_info parcel ids repeat")


def _int_counts(counts) -> dict:
    out = {}
    for k, v in dict(counts).items():
        if isinstance(v, bool) or not float(v) == int(v) or int(v) < 0:
            raise ValueError("cell counts must be non-negative integers")
        out[int(k)] = int(v)
    return out


class CellSources(R.Sources):
    """A claim's sources with the class context rebuilt on a multiverse cell's matrix (parcels x genes, indexed by
    parcel id) and the cell's parcel universe and counts (R39; module docstring). Every other source is the claim's
    own (delegated).
    counts: the cell's own per-parcel sample counts - required for the bilateral cell, the per-donor counts without
            the left-out donor for a leave-one-out cell (optional: COUNTS_FROM_MATRIX otherwise), refused for the
            primary and the normalisation cells (the primary's counts).
    bilateral (the bilateral cell only): dict(info = atlas_info rows (DataFrame, index parcel id; label, hemisphere,
            structure), xyz = {parcel id: (x, y, z)} centroids, maps = {map index: (y, parcel ids)} the map on the
            bilateral parcels).
    left_only_map: the claim's map is defined on the left hemisphere only (its bilateral cell is not applicable)."""

    def __init__(self, base: R.Sources, cell: str, expr: pd.DataFrame, expr_sha: str | None = None, *,
                 counts=None, bilateral: dict | None = None, left_only_map: bool = False):
        if cell != PRIMARY and cell not in CELLS:
            raise ValueError(f"unknown multiverse cell {cell!r}")
        if cell in (PRIMARY,) + NORMALISATION_CELLS and counts is not None:
            raise ValueError("R39: a normalisation cell takes the primary's counts (no counts may be given)")
        if cell == BILATERAL and not left_only_map and (bilateral is None or counts is None):
            raise ValueError("R39: the bilateral cell needs its build's atlas_info, centroids, map and counts")
        if cell != BILATERAL and bilateral is not None:
            raise ValueError("bilateral inputs belong to the bilateral cell only")
        self.base, self.cell = base, cell
        self.expr = expr
        self.expr_sha = expr_sha or matrix_sha(expr)
        self.counts_given = None if counts is None else _int_counts(counts)
        self.bilateral = None if bilateral is None else dict(bilateral)
        self.left_only_map = bool(left_only_map)
        if self.bilateral is not None:
            _check_info(self.bilateral["info"])
        self.kind = f"multiverse cell over {getattr(base, 'kind', '?')}"
        self.synthetic = getattr(base, "synthetic", False)

    def spec(self) -> dict:
        s = {"kind": "multiverse", "cell": self.cell, "matrix_sha256": self.expr_sha, "base": self.base.spec()}
        if self.counts_given is not None:
            s["counts_sha256"] = R.sha256_json(sorted(self.counts_given.items()))
        if self.bilateral is not None:
            s["bilateral_sha256"] = self._bilateral_sha()
        return s

    def _bilateral_sha(self) -> str:
        b = self.bilateral
        info = b["info"]
        xyz = [[int(i)] + [float(v) for v in b["xyz"][int(i)]] for i in info.index if int(i) in b["xyz"]]
        maps = {str(k): [[float(x) for x in np.asarray(v[0], float)], [int(i) for i in v[1]]]
                for k, v in sorted(b["maps"].items())}
        return R.sha256_json([[[int(i)] + [str(info.at[i, c]) for c in INFO_COLUMNS] for i in info.index], xyz, maps])

    # -- R39's definition (expected_parcels reads only these) -------------------------------------------------
    def _not_applicable(self):
        if self.cell == BILATERAL and self.left_only_map:
            raise R.SourceUnavailable(NOT_APPLICABLE_LEFT_ONLY, "bilateral cell of a left-only map (R11 :684-685)")

    def universe_ids(self, cls) -> list:
        """R39's parcel universe of this cell: the primary parcels, or (bilateral) every parcel of the class's tissue
        classes, L, R and B."""
        self._not_applicable()
        ctx0, _, _ = self.base.context(cls)
        if self.cell != BILATERAL:
            return [int(i) for i in ctx0.parcel_ids]
        uni = bilateral_universe(self.bilateral["info"], set(str(c) for c in np.unique(ctx0.classes)))
        missing = sorted(set(int(i) for i in ctx0.parcel_ids) - set(uni))
        if missing:
            raise R.SourceUnavailable(NOT_COMPUTABLE_CELL % "the bilateral universe lacks primary parcels",
                                      str(len(missing)))
        return uni

    def cell_counts(self, cls) -> tuple:
        """({parcel id: this cell's sample count} over the universe, counts source) (R39); the cell matrix's rows are
        checked against them (a count >= 1 needs a complete row; a given count is 0 exactly where the row is empty)."""
        uni = self.universe_ids(cls)
        _, counts0, _ = self.base.context(cls)
        missing = [i for i in uni if i not in set(int(x) for x in self.expr.index)]
        if missing:
            raise R.SourceUnavailable(NOT_COMPUTABLE_CELL % "the cell matrix lacks universe parcels", str(len(missing)))
        rows = self.expr.loc[uni]
        allnan = dict(zip(uni, rows.isna().all(axis=1).to_numpy().tolist()))
        part = rows.isna().any(axis=1).to_numpy() & ~rows.isna().all(axis=1).to_numpy()
        if part.any():
            raise R.SourceUnavailable(NOT_COMPUTABLE_CELL % "a parcel row partly missing", str(int(part.sum())))
        if self.cell in (PRIMARY,) + NORMALISATION_CELLS:
            c, src = {i: int(counts0[i]) for i in uni}, COUNTS_PRIMARY
            bad = [i for i in uni if c[i] >= 1 and allnan[i]]
        elif self.counts_given is not None:
            absent = [i for i in uni if i not in self.counts_given]
            if absent:
                raise R.SourceUnavailable(NOT_COMPUTABLE_CELL % "the cell's counts lack universe parcels",
                                          str(len(absent)))
            c = {i: self.counts_given[i] for i in uni}
            src = COUNTS_GIVEN_BILATERAL if self.cell == BILATERAL else COUNTS_GIVEN_LOO
            bad = [i for i in uni if (c[i] == 0) != allnan[i]]
        else:   # a leave-one-out cell without per-donor counts (plants/p22.py's call)
            c = {i: (0 if allnan[i] else int(counts0[i])) for i in uni}
            src, bad = COUNTS_FROM_MATRIX, []
        if bad:
            raise R.SourceUnavailable(NOT_COMPUTABLE_CELL % "the cell's counts disagree with its matrix's empty rows",
                                      str(len(bad)))
        return c, src

    def _cell_map(self, plan, map_index):
        """(y, ids, class, hashes) of the cell's map, before any entry rule: the claim's map, or (bilateral) the map
        on the bilateral parcels."""
        self._not_applicable()
        if self.cell != BILATERAL:
            return self.base.map(plan, map_index)
        if int(map_index) not in self.bilateral["maps"]:
            raise R.SourceUnavailable(NOT_COMPUTABLE_CELL % "no bilateral map for this map index", str(map_index))
        y, ids = self.bilateral["maps"][int(map_index)]
        y = np.asarray(y, dtype=float)
        ids = A3.as_parcel_ids(ids, "bilateral map")
        if y.shape != ids.shape:
            raise ValueError("bilateral map: one value per parcel id")
        outside = set(int(i) for i in ids) - set(self.universe_ids(plan["analysis_class"]))
        if outside:   # re-parcellation is the loader's job (as run.prepare refuses a map outside its class)
            raise RuntimeError(f"bilateral map: {len(outside)} parcel(s) outside the bilateral universe")
        return y, ids, plan["analysis_class"], {f"map[{int(map_index)}] (bilateral cell)": R.arr_sha(y, ids)}

    def expected_parcels(self, plan, map_index) -> list:
        """R39's analysis parcels of this cell, from the definition only (universe, the cell's counts, finite y), in
        the map's order: the comparison run_cell asserts."""
        cls = plan["analysis_class"]
        uni = set(self.universe_ids(cls))
        c, _ = self.cell_counts(cls)
        y, ids, _, _ = self._cell_map(plan, map_index)
        return [int(i) for i, v in zip(ids, np.asarray(y, float)) if int(i) in uni and c[int(i)] >= 1
                and np.isfinite(v)]

    def parcel_report(self, plan, map_index) -> dict:
        """R39 'Kept and dropped parcels are reported per cell': the universe (by hemisphere), the counts' source and
        the parcels kept and dropped, by reason."""
        cls = plan["analysis_class"]
        uni = self.universe_ids(cls)
        c, src = self.cell_counts(cls)
        y, ids, _, _ = self._cell_map(plan, map_index)
        yv = {int(i): float(v) for i, v in zip(ids, np.asarray(y, float))}
        info = self.bilateral["info"] if self.cell == BILATERAL else self.base.context(cls)[0].info
        hemi = {int(i): str(info.at[i, "hemisphere"]) for i in uni}
        kept = self.expected_parcels(plan, map_index)
        no_sample = [i for i in uni if c[i] == 0]
        absent = [i for i in uni if c[i] >= 1 and i not in yv]
        nonfinite = [i for i in uni if c[i] >= 1 and i in yv and not np.isfinite(yv[i])]
        return dict(cell=self.cell, universe=dict(n=len(uni), by_hemisphere={h: sum(1 for i in uni if hemi[i] == h)
                                                                             for h in HEMISPHERES}),
                    counts_source=src, n_kept=len(kept), kept=kept,
                    dropped_no_sample_in_cell=no_sample, dropped_absent_from_map=absent,
                    dropped_nonfinite=nonfinite, n_dropped=len(no_sample) + len(absent) + len(nonfinite),
                    rule="a parcel enters iff y is finite there and the cell's own matrix has >= 1 sample there "
                         "(RUN_PLAN_amend_2 R39)")

    # -- the context and the map the production calls read ----------------------------------------------------
    def _context_ids(self, cls) -> list:
        """The universe parcels whose cell row is not empty (the cell's context)."""
        uni = self.universe_ids(cls)
        c, _ = self.cell_counts(cls)
        rows = self.expr.loc[uni]
        empty = rows.isna().all(axis=1).to_numpy()
        return [i for i, e in zip(uni, empty) if not e]

    def context(self, cls):
        ctx0, _, sha0 = self.base.context(cls)
        keep = self._context_ids(cls)
        c, src = self.cell_counts(cls)
        if self.cell == BILATERAL:
            info = self.bilateral["info"]
            xyz = np.array([self.bilateral["xyz"][i] for i in keep], dtype=float)
            classes = info.loc[keep, "structure"].astype(str).to_numpy()
        else:
            info = ctx0.info
            pos = {int(p): k for k, p in enumerate(ctx0.parcel_ids)}
            sel = np.array([pos[i] for i in keep], dtype=int)
            xyz, classes = np.asarray(ctx0.xyz)[sel], np.asarray(ctx0.classes)[sel]
        ctx = A3.ClassContext(ctx0.name, self.expr.loc[keep], classes, xyz, info, ctx0.brain_fn, ctx0.atlas,
                              {"multiverse_cell": self.cell, "matrix_sha256": self.expr_sha, "counts_source": src})
        parts = [sha0, self.cell, self.expr_sha]
        if self.counts_given is not None:
            parts.append(R.sha256_json(sorted(self.counts_given.items())))
        if self.bilateral is not None:
            parts.append(self._bilateral_sha())
        return ctx, {i: c[i] for i in keep}, R.sha256_json(parts)

    def map(self, plan, map_index):
        y, ids, cls, h = self._cell_map(plan, map_index)
        keep = set(self._context_ids(cls))
        ids = np.asarray(ids, dtype=np.int64)
        m = np.array([int(i) in keep for i in ids])
        return np.asarray(y, dtype=float)[m], ids[m], cls, dict(h)

    def gene_set(self, plan):
        return self.base.gene_set(plan)

    def component(self, plan):
        return self.base.component(plan)

    def trajectories(self, cls):
        return self.base.trajectories(cls)

    def donor_counts(self, cls):
        """R39: the >= 2-donor sensitivity is not crossed with the cells (no >= 2-donor x cell record)."""
        raise R.SourceUnavailable(NOT_CROSSED, f"multiverse cell {self.cell}")

    def resolve_class(self, plan):
        return self.base.resolve_class(plan)

    def selection_rule(self, plan, ctx):
        return self.base.selection_rule(plan, ctx)


def run_cell(plan: dict, sources: R.Sources, map_index: int, K: dict, seed_callables: dict, *, g6l_mode: str,
             two_sided: bool, registered_direction=None, descriptors: bool = False) -> dict:
    """One claim on one map through the production calls with the given sources (the primary's, or CellSources of a
    cell) and the claim's own seed callables: the verdict legs and verdict; the descriptor legs at the verdict's d* (or
    the registered direction) if `descriptors`. The entry rule is the primary one ('primary': finite y and >= 1 sample
    in the cell; never the >= 2-donor rule, R39). For a cell: the analysis parcels are asserted equal to R39's set
    (CellParcelSetError otherwise) and the cell's parcel report is attached ('cell_parcels'). Returns the records and
    the prepared inputs' hashes."""
    pr = R.prepare(plan, sources, map_index, "primary")
    cell_parcels = None
    if isinstance(sources, CellSources):
        want = sources.expected_parcels(plan, map_index)
        got = [int(i) for i in pr.parcel_ids]
        if got != want:
            raise CellParcelSetError(f"multiverse cell {sources.cell}: {len(got)} analysis parcels, R39's set has "
                                     f"{len(want)} ({len(set(want) - set(got))} missing, {len(set(got) - set(want))} "
                                     "extra)")
        cell_parcels = sources.parcel_report(plan, map_index)
    sc = seed_callables
    screen = None
    if plan["form"] in V.FULL_FORMS:
        screen = PM.streams_screen(g6l_mode, pr.ctx, pr.S, {"G6l": sc["seed_of"]("G6l")}, int(K["species"]))["G6l"]
    legs = R.g_legs(pr, K, sc["seed_of"], screen)
    v = V.assemble_verdict_a1(legs["legs"], two_sided=two_sided, registered_direction=registered_direction)
    out = dict(legs=legs, verdict=v, parcel_ids=[int(i) for i in pr.parcel_ids], hashes=dict(pr.hashes),
               n_genes=int(pr.ctx.G))
    if cell_parcels is not None:
        out["cell_parcels"] = cell_parcels
    if descriptors and plan["form"] in V.FULL_FORMS:
        traj, _ = sources.trajectories(plan["analysis_class"])
        direction = v.get("d_star") if two_sided else registered_direction
        out["descriptors"] = R.g_descriptors(pr, K, sc, traj, direction, two_sided)
    return out
