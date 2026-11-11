"""WP3 gene-level helpers shared by the material stage (wp3_material.py), the real loaders (real_sources.py) and the
reproduction wiring (wp3_repro.py). Every reader takes the caller's byte reader (`read_bytes(path) -> bytes`), so a
real loader opens each file through its one door (run.RealSources.real_path; RUN_PLAN WP2r residue "a test enforcing
that WP3's real loaders open files only through RealSources.real_path"). Nothing here prints; nothing here computes a
statistic of a map against a set.

- HGNCTable: the S-build's HGNC rule (claims_register.md §1.6 "Mapping"; register_sets/MANIFEST.json `rule_hgnc`:
  "id given by the source (Ensembl; Entrez for KEGG / WebGestalt; UniProtKB for GO) -> HGNC when it names one approved
  gene, else symbol: approved -> previous -> alias (exact); a symbol or id matching >= 2 approved genes at the first
  matching tier is dropped"), a verbatim copy of src_register/s_build.py HGNC (:398-460; the frozen file is not
  imported for production because its reader opens the pinned path itself) reading the same table through the
  caller's reader. tests/test_wp3_phase1.py asserts symbol() / resolve() equal s_build.HGNC's on a synthetic table.
- GOTerms: the S-build's GO reader and §1.6 GO rule ("annotations to the term or any descendant over is_a and part_of,
  all evidence codes except ND, NOT-qualified annotations excluded"; s_build.py GO :551-636, copied) plus the
  resolution of its raw members (s_build.build_set :1178-1199) and a bitset form of every live term's HGNC genes for
  R22's local over-representation analysis.
- gaf_reference: R22 "the primary reference is every human gene symbol in that GAF, mapped by the S-build's HGNC rule".
- pthr16_reference: R22's sensitivity reference, PANTHER 16.0's own PTHR16.0_human (s_build.Sources.panther_annotation's
  id rule, :874-905), mapped by the same HGNC rule.
- gamba_brain_symbols: e3_plants.brain_background's GAMBA brain>body rule (flag count 2,711 asserted; symbols whose
  duplicates disagree dropped), returning the symbols (the class contexts apply them to a universe themselves).
- brainspan_*: the frozen BrainSpan trajectory rule (src/asdg/brainspan.py load_trajectories, FROZEN code) computed
  from frames the loader read through its door, the declared sample columns only (RUN_PLAN §8 "BrainSpan: only the
  declared sample columns (age, structure acronym) are read; donor columns are never read"); tests assert equality with
  asdg.brainspan.load_trajectories on a synthetic directory.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from . import a3_port as _A3  # noqa: F401  (puts src/ on sys.path: asdg.brainspan)

ReadBytes = Callable[[Path], bytes]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_pinned(read_bytes: ReadBytes, path: Path, sha256: str | None, what: str) -> bytes:
    """The file's bytes through the caller's reader, sha256 asserted when a pin is given (raises ValueError, never
    printing a value)."""
    data = read_bytes(Path(path))
    if sha256 is not None and sha256_bytes(data) != sha256:
        raise ValueError(f"{what}: sha256 differs from its pin")
    return data


# ================================================================================================================
# HGNC (s_build.py :394-460, copied; the reader is the caller's)
# ================================================================================================================
def _split(x) -> list[str]:
    return [t.strip() for t in str(x).split("|") if t.strip()] if isinstance(x, str) else []


class HGNCTable:
    """s_build.HGNC on bytes given by the caller (the frozen class reads its pinned path itself)."""

    def __init__(self, data: bytes):
        cs = pd.read_csv(io.BytesIO(data), sep="\t", dtype=str, keep_default_na=False)
        assert cs["symbol"].is_unique and cs["hgnc_id"].is_unique and (cs["status"] == "Approved").all()
        self.n = len(cs)
        self.approved = set(cs["symbol"])
        self.prev, self.alias = defaultdict(set), defaultdict(set)
        self.ids = {k: defaultdict(set) for k in ("ensembl", "entrez", "uniprot", "rnacentral", "hgnc")}
        for sym, hid in zip(cs["symbol"], cs["hgnc_id"]):
            self.ids["hgnc"][hid.strip()].add(sym)
        for sym, prev, alias, ens, ent, uni, rnc in zip(cs["symbol"], cs["prev_symbol"], cs["alias_symbol"],
                                                        cs["ensembl_gene_id"], cs["entrez_id"], cs["uniprot_ids"],
                                                        cs["rna_central_id"]):
            for u in _split(rnc):
                self.ids["rnacentral"][u].add(sym)
            for p in _split(prev):
                self.prev[p].add(sym)
            for a in _split(alias):
                self.alias[a].add(sym)
            if ens.strip():
                self.ids["ensembl"][ens.strip()].add(sym)
            if ent.strip():
                self.ids["entrez"][ent.strip()].add(sym)
            for u in _split(uni):
                self.ids["uniprot"][u].add(sym)

    def symbol(self, s) -> tuple[str | None, str]:
        if s is None:
            return None, "no symbol given"
        if not isinstance(s, str):
            return None, f"non-string cell ({type(s).__name__}; e.g. an Excel date)"
        s = s.strip()
        if not s:
            return None, "empty"
        if s in self.approved:
            return s, "approved"
        for tab, how in ((self.prev, "previous"), (self.alias, "alias")):
            if s in tab:
                t = tab[s]
                if len(t) == 1:
                    return next(iter(t)), how
                return None, f"ambiguous {how} symbol ({len(t)} approved genes)"
        return None, "unmapped symbol"

    def resolve(self, kind: str | None, ident, sym) -> tuple[str | None, str]:
        if kind and isinstance(ident, str) and ident.strip():
            key = ident.strip()
            if kind == "ensembl":
                key = key.split(".")[0]
            if kind == "uniprot":
                key = key.split("-")[0]
            if kind == "rnacentral":
                key = key.split("_")[0]
            if kind == "nongene":
                return None, "non-gene object (ComplexPortal complex)"
            hit = self.ids[kind].get(key, set())
            if len(hit) == 1:
                return next(iter(hit)), f"{kind} id"
            s, how = self.symbol(sym)
            if s:
                return s, f"{how} (symbol; {kind} id {'ambiguous' if hit else 'not in HGNC'})"
            return None, f"{kind} id {'ambiguous' if hit else 'not in HGNC'}; symbol: {how}"
        return self.symbol(sym)

    def map_columns(self, symbols, kinds_ids=None) -> tuple[list, dict]:
        """One HGNC symbol (or None) per given column, with the mapping counts by tier (the tier text up to ' (').
        kinds_ids: optional (kind, id) per column (an id the source gives, e.g. BrainSpan's Ensembl id)."""
        out, how = [], Counter()
        for k, s in enumerate(symbols):
            kind, ident = (kinds_ids[k] if kinds_ids is not None else (None, None))
            m, h = self.resolve(kind, ident, s)
            how[h.split(" (")[0]] += 1
            out.append(m)
        return out, dict(sorted(how.items()))


def resolve_raw(hg: HGNCTable, raw: list[dict]) -> tuple[set, dict]:
    """s_build.build_set's resolution of raw members (:1179-1199): unique (kind, id, symbol) entries resolved by the
    HGNC rule; returns the HGNC members and the mapping counts."""
    how, members, seen = Counter(), set(), set()
    for r in raw:
        key = (r.get("kind"), str(r.get("id")), str(r.get("symbol")))
        if key in seen:
            continue
        seen.add(key)
        s, h = hg.resolve(r.get("kind"), r.get("id"), r.get("symbol"))
        how[h] += 1
        if s:
            members.add(s)
    return members, dict(sorted(how.items()))


# ================================================================================================================
# GO (s_build.py GO :551-636, copied; reader is the caller's)
# ================================================================================================================
GO_KIND = {"UniProtKB": "uniprot", "RNAcentral": "rnacentral", "ComplexPortal": "nongene"}   # s_build.GO.members
GO_RULE = ("claims_register.md §1.6 GO rule (s_build.GO, copied): annotations to the term or any descendant over is_a "
           "and part_of, all evidence codes except ND, NOT-qualified annotations excluded; members resolved by the "
           "S-build's HGNC rule (UniProtKB id -> HGNC when it names one approved gene, else the symbol)")


class GOTerms:
    def __init__(self, obo: bytes, gaf_gz: bytes):
        self.terms = {}
        self.data_version = None
        cur = None
        for line in obo.decode("utf-8").split("\n"):
            line = line.rstrip("\r")
            if line.startswith("data-version:"):
                self.data_version = line.split(":", 1)[1].strip()
            if line == "[Term]":
                cur = {"parents": set(), "syn": [], "obsolete": False}
                continue
            if line.startswith("[") and line.endswith("]"):
                cur = None
                continue
            if cur is None or not line:
                if not line and cur is not None and "id" in cur:
                    self.terms[cur["id"]] = cur
                    cur = None
                continue
            k, _, v = line.partition(": ")
            if k == "id":
                cur["id"] = v
            elif k == "name":
                cur["name"] = v
            elif k == "namespace":
                cur["ns"] = v
            elif k == "is_obsolete" and v == "true":
                cur["obsolete"] = True
            elif k == "is_a":
                cur["parents"].add(v.split(" ! ")[0].strip())
            elif k == "relationship" and v.startswith("part_of "):
                cur["parents"].add(v.split()[1])
        if cur is not None and "id" in cur:
            self.terms[cur["id"]] = cur
        self.children = defaultdict(set)
        for t, d in self.terms.items():
            for p in d["parents"]:
                self.children[p].add(t)
        self.ann = defaultdict(set)   # GO id -> {(db, object id, symbol)}
        self.objects_all = set()      # every (db, object id, symbol) of the GAF (R22's reference: every gene in it)
        self.n_ann = Counter()
        for line in gzip.decompress(gaf_gz).decode("utf-8").split("\n"):
            if not line:
                continue
            if line.startswith("!"):
                continue
            c = line.rstrip("\r").split("\t")
            self.objects_all.add((c[0], c[1], c[2]))
            if "NOT" in c[3].split("|"):
                self.n_ann["excluded NOT"] += 1
                continue
            if c[6] == "ND":
                self.n_ann["excluded ND"] += 1
                continue
            self.ann[c[4]].add((c[0], c[1], c[2]))
            self.n_ann["kept"] += 1

    def descendants(self, term: str) -> set:
        seen, stack = {term}, [term]
        while stack:
            for c in self.children.get(stack.pop(), ()):
                if c not in seen:
                    seen.add(c)
                    stack.append(c)
        return seen

    def raw_members(self, term: str) -> tuple[list[dict], int]:
        """s_build.GO.members, copied."""
        seen = self.descendants(term)
        objs = set()
        for t in seen:
            objs |= self.ann.get(t, set())
        raw = [{"kind": GO_KIND.get(db), "id": oid, "symbol": sym, "db": db} for db, oid, sym in sorted(objs)]
        return raw, len(seen)

    def live_terms(self, ns: str = "biological_process") -> list[str]:
        return sorted(t for t, d in self.terms.items() if d.get("ns") == ns and not d["obsolete"] and "name" in d)

    def hgnc_of_objects(self, hg: HGNCTable) -> dict:
        """(db, id, symbol) -> HGNC symbol or None, for every GAF object (the resolution of build_set)."""
        out = {}
        for db, oid, sym in self.objects_all:
            s, _ = hg.resolve(GO_KIND.get(db), oid, sym)
            out[(db, oid, sym)] = s
        return out

    def term_gene_bits(self, hg: HGNCTable, genes_index: dict, ns: str = "biological_process") -> dict:
        """Every live term of the namespace -> a Python-int bitset over genes_index (HGNC symbol -> bit), by the GO
        rule: own annotations OR'd with every descendant's (memoised over the DAG; equals raw_members + resolve_raw
        restricted to genes_index, asserted by the tests on synthetic terms)."""
        obj = self.hgnc_of_objects(hg)
        own = {}
        for t, objs in self.ann.items():
            b = 0
            for o in objs:
                s = obj.get(o)
                if s is not None and s in genes_index:
                    b |= 1 << genes_index[s]
            own[t] = b
        memo: dict = {}

        def bits(t):
            if t in memo:
                return memo[t]
            # iterative post-order over the descendants (no recursion limit on deep DAGs)
            stack = [(t, False)]
            while stack:
                node, done = stack.pop()
                if node in memo:
                    continue
                kids = self.children.get(node, ())
                if done:
                    b = own.get(node, 0)
                    for k in kids:
                        b |= memo[k]
                    memo[node] = b
                else:
                    stack.append((node, True))
                    for k in kids:
                        if k not in memo:
                            stack.append((k, False))
            return memo[t]
        return {t: bits(t) for t in self.live_terms(ns)}


def gaf_reference(go: GOTerms, hg: HGNCTable) -> tuple[set, dict]:
    """R22: every human gene symbol in the GAF, mapped by the S-build's HGNC rule (every GAF line counts, whatever its
    qualifier or evidence code; U-W3-9). Returns (HGNC symbols, mapping counts)."""
    raw = [{"kind": GO_KIND.get(db), "id": oid, "symbol": sym} for db, oid, sym in sorted(go.objects_all)]
    return resolve_raw(hg, raw)


def pthr16_reference(data: bytes, hg: HGNCTable) -> tuple[set, dict]:
    """R22's sensitivity reference: PANTHER 16.0's PTHR16.0_human genes, ids as s_build.Sources.panther_annotation
    reads them (HGNC id, else Ensembl, else GeneID, else the UniProt accession, with the symbol of column 3), mapped by
    the S-build's HGNC rule. Returns (HGNC symbols, counts incl. n_rows)."""
    raw = []
    n = 0
    for line in data.decode("utf-8").split("\n"):
        if not line:
            continue
        c = line.rstrip("\r").split("\t")
        if len(c) != 11:
            raise ValueError("PTHR16.0_human: a row without 11 columns")
        n += 1
        ids = dict(x.split("=", 1) for x in c[0].split("|")[1:] if "=" in x)
        if "HGNC" in ids:
            raw.append({"kind": "hgnc", "id": "HGNC:" + ids["HGNC"], "symbol": c[2]})
        elif "Ensembl" in ids:
            raw.append({"kind": "ensembl", "id": ids["Ensembl"], "symbol": c[2]})
        elif "GeneID" in ids:
            raw.append({"kind": "entrez", "id": ids["GeneID"], "symbol": c[2]})
        else:
            raw.append({"kind": "uniprot", "id": c[1], "symbol": c[2]})
    genes, how = resolve_raw(hg, raw)
    how = dict(how, n_rows=n)
    return genes, how


# ================================================================================================================
# GAMBA brain>body (e3_plants.brain_background's rule, on symbols)
# ================================================================================================================
GAMBA_SYMBOL, GAMBA_FLAG, GAMBA_N_FLAGGED = "symbols", "brain > body (default)", 2711


def gamba_brain_symbols(data: bytes, *, n_flagged: int = GAMBA_N_FLAGGED) -> list[str]:
    """e3_plants.brain_background (arcs/audit/src/e3_plants.py:50-56): rows flagged brain > body, symbols whose
    duplicate rows disagree on the flag dropped; the flagged count asserted (2,711 in the real table)."""
    bg = pd.read_csv(io.BytesIO(data))
    if int(bg[GAMBA_FLAG].sum()) != n_flagged:
        raise ValueError("GAMBA brain>body flag count differs from its registered value")
    conflict = bg.groupby(GAMBA_SYMBOL)[GAMBA_FLAG].nunique()
    genes = set(bg.loc[(bg[GAMBA_FLAG] == 1) & ~bg[GAMBA_SYMBOL].isin(conflict[conflict > 1].index), GAMBA_SYMBOL])
    return sorted(str(g) for g in genes)


# ================================================================================================================
# BrainSpan (src/asdg/brainspan.py, the frozen rule; declared columns only)
# ================================================================================================================
BRAINSPAN_SAMPLE_COLUMNS = ("age", "structure_acronym")          # RUN_PLAN §8 :1306 (declared sample columns)
BRAINSPAN_GENE_COLUMNS = ("ensembl_gene_id", "gene_symbol")       # rows_metadata: the gene identifiers only


def brainspan_frames(expr_csv: bytes, rows_csv: bytes, cols_csv: bytes) -> tuple[np.ndarray, pd.DataFrame, pd.DataFrame]:
    """(X genes x samples, rows (ensembl_gene_id, gene_symbol), cols (age, structure_acronym)) - the declared columns
    only (pandas usecols: donor columns never enter a frame). Shapes asserted as asdg.brainspan does."""
    cols = pd.read_csv(io.BytesIO(cols_csv), usecols=list(BRAINSPAN_SAMPLE_COLUMNS), dtype=str)
    rows = pd.read_csv(io.BytesIO(rows_csv), usecols=list(BRAINSPAN_GENE_COLUMNS), dtype=str)
    X = pd.read_csv(io.BytesIO(expr_csv), header=None, index_col=0).to_numpy(dtype=float)
    if X.shape != (len(rows), len(cols)):
        raise ValueError("BrainSpan: expression shape differs from the metadata's")
    return X, rows[list(BRAINSPAN_GENE_COLUMNS)], cols[list(BRAINSPAN_SAMPLE_COLUMNS)]


def brainspan_trajectories(X: np.ndarray, gene_keys, ages, structures) -> tuple[pd.DataFrame, dict]:
    """asdg.brainspan.load_trajectories's computation (FROZEN src/asdg/brainspan.py:24-41) on given frames: mean
    log2(RPKM + 1) over neocortical samples in the 8 stage bins; rows keyed by gene_keys (the frozen rule: BrainSpan's
    gene_symbol); duplicate keys averaged. Rows whose key is None are dropped (counted)."""
    from asdg.brainspan import BINS, NEOCORTEX, age_years
    age = pd.Series(list(ages)).map(age_years).to_numpy()
    ctx = pd.Series(list(structures)).isin(NEOCORTEX).to_numpy()
    L = np.log2(X + 1.0)
    out, counts = {}, {}
    for name, lo, hi in BINS:
        sel = ctx & (age >= lo) & (age < hi)
        counts[name] = int(sel.sum())
        if not sel.sum() > 0:
            raise ValueError(f"no neocortical samples in bin {name}")
        out[name] = L[:, sel].mean(1)
    keys = list(gene_keys)
    keep = np.array([k is not None for k in keys])
    T = pd.DataFrame({k: v[keep] for k, v in out.items()}, index=np.asarray([str(k) for k in keys], dtype=object)[keep])
    n_dup = int(T.index.duplicated().sum())
    T = T.groupby(level=0).mean()
    return T, dict(samples_per_bin=counts, n_genes=len(T), n_duplicate_rows_averaged=n_dup,
                   n_rows_without_key=int((~keep).sum()))
