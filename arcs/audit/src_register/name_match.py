"""The register's one name-matching rule (claims register DRAFT v6 section 1.1 rule G and section 1.6; decision R1 of
the orchestrator under the operator's standing delegation, taken after the v5 S-build outcome was seen).

It applies to every GO, KEGG, MSigDB, Reactome and figure-label mapping in the register: a name as the register transcribes
it from the paper (the query) is mapped to a term of the pinned release by the first tier that identifies exactly one
live term:

  (a) the exact name in the pinned release;
  (b) else a synonym of any scope (EXACT, BROAD, NARROW, RELATED), or a former name, that identifies exactly one live
      term -- labelled "S matched by <scope> synonym" (the pinned files record former names only as synonyms: GO keeps a
      renamed term's former name as a synonym; KEGG, MSigDB, WebGestalt and Enrichr libraries serve no synonyms);
  (c) else case, UK / US spelling or singular / plural normalisation that identifies exactly one term (normalised names
      first, then normalised synonyms of any scope) -- labelled with the normalisations that were needed;
  else "S undefined".

Surrounding and repeated white space is ignored in every tier (typography, not a normalisation). A tier that matches two
or more live terms does not identify one; the next tier is tried, and its result recorded. Normalisations of tier (c),
applied identically to the query and to every candidate string:
  case      -- str.casefold();
  UK / US   -- the pinned word list UK_US below (whole words) and the suffix rules -isation(s) / -ised / -ising / -ise(s)
               -> -ization(s) / -ized / -izing / -ize(s) for words of >= 7 letters;
  number    -- per word of > 3 letters: -ies -> -y, -sses -> -ss, -xes / -ches / -shes -> drop 'es', else a final -s
               dropped unless the word ends in -ss, -us, -is or -ys.
No other normalisation (hyphens, punctuation, word order, abbreviations) is made.
"""
from __future__ import annotations

import re

UK_US = {  # whole-word UK -> US spellings (pinned; register section 1.6)
    "signalling": "signaling", "signalled": "signaled", "labelling": "labeling", "labelled": "labeled",
    "modelling": "modeling", "modelled": "modeled", "travelling": "traveling", "channelling": "channeling",
    "tunnelling": "tunneling", "fuelling": "fueling", "cancelling": "canceling",
    "behaviour": "behavior", "behavioural": "behavioral", "colour": "color", "tumour": "tumor", "favour": "favor",
    "flavour": "flavor", "odour": "odor", "labour": "labor", "haemoglobin": "hemoglobin", "haematopoiesis": "hematopoiesis",
    "haematopoietic": "hematopoietic", "haem": "heme", "haemostasis": "hemostasis", "oestrogen": "estrogen",
    "oestradiol": "estradiol", "oedema": "edema", "foetal": "fetal", "anaemia": "anemia", "leukaemia": "leukemia",
    "ischaemia": "ischemia", "oesophagus": "esophagus", "oesophageal": "esophageal", "centre": "center", "fibre": "fiber",
    "litre": "liter", "metre": "meter", "analogue": "analog", "catalogue": "catalog", "sulphate": "sulfate",
    "sulphur": "sulfur", "sulphide": "sulfide", "aluminium": "aluminum", "grey": "gray", "programme": "program",
    "ageing": "aging", "paediatric": "pediatric", "orthopaedic": "orthopedic", "defence": "defense", "licence": "license",
}
_ISE = [(re.compile(r"isation(s?)$"), r"ization\1"), (re.compile(r"ised$"), "ized"), (re.compile(r"ising$"), "izing"),
        (re.compile(r"ise(s?)$"), r"ize\1")]


def ws(s: str) -> str:
    return " ".join(str(s).split())


def _uk_us_word(w: str) -> str:
    if w in UK_US:
        return UK_US[w]
    if len(w) >= 7:
        for rx, rep in _ISE:
            if rx.search(w):
                return rx.sub(rep, w)
    return w


def _number_word(w: str) -> str:
    if len(w) <= 3:
        return w
    if w.endswith("ies"):
        return w[:-3] + "y"
    if w.endswith("sses"):
        return w[:-2]
    if w.endswith(("xes", "ches", "shes")):
        return w[:-2]
    if w.endswith("s") and not w.endswith(("ss", "us", "is", "ys")):
        return w[:-1]
    return w


_WORD = re.compile(r"[A-Za-z]+")


def _apply(fn, w: str) -> str:
    """apply a word map on the lower-cased word, keeping a leading capital (so the steps can be ablated one by one)."""
    out = fn(w.lower())
    if out == w.lower():
        return w
    return out[:1].upper() + out[1:] if w[:1].isupper() else out


def norm(s: str, case: bool = True, spelling: bool = True, number: bool = True) -> str:
    s = ws(s)
    if case:
        s = s.casefold()
    if spelling:
        s = _WORD.sub(lambda m: _apply(_uk_us_word, m.group(0)), s)
    if number:
        s = _WORD.sub(lambda m: _apply(_number_word, m.group(0)), s)
    return s


def norm_number(s: str) -> str:
    """tier (c)'s full normalisation (case, UK / US spelling, singular / plural)."""
    return norm(s)


NORM_STEPS = ("case", "UK / US spelling", "singular / plural")


def needed_steps(q: str, target: str) -> list[str]:
    """the normalisations without which the two strings would differ (ablation, one step at a time)."""
    out = []
    for i, nm in enumerate(NORM_STEPS):
        flags = [True, True, True]
        flags[i] = False
        if norm(q, *flags) != norm(target, *flags):
            out.append(nm)
    return out


def match(query: str, terms: list[dict]) -> dict:
    """terms: [{'id', 'name', 'synonyms': [(text, scope)], 'live': bool}]. Returns a record: tier ('a' | 'b' | 'c' | None),
    id, name, label, and what each tier found (counts / ids only)."""
    q = ws(query)
    live = [t for t in terms if t.get("live", True)]
    rec = {"query": q, "tier": None, "id": None, "name": None, "label": "S undefined", "tiers": {}}
    # (a) exact name
    hit = sorted({t["id"] for t in live if ws(t["name"]) == q})
    rec["tiers"]["a"] = hit
    if len(hit) == 1:
        t = next(t for t in live if t["id"] == hit[0])
        rec.update(tier="a", id=t["id"], name=t["name"], label="exact name")
        return rec
    # (b) a synonym of any scope (or a former name recorded as a synonym)
    syn_hits = {}
    for t in live:
        for text, scope in t.get("synonyms", []):
            if ws(text) == q:
                syn_hits.setdefault(t["id"], set()).add(scope)
    rec["tiers"]["b"] = sorted(syn_hits)
    if len(syn_hits) == 1:
        tid = next(iter(syn_hits))
        t = next(x for x in live if x["id"] == tid)
        scope = "/".join(sorted(syn_hits[tid]))
        rec.update(tier="b", id=tid, name=t["name"], label="S matched by %s synonym" % scope)
        return rec
    # (c) case, UK / US spelling, singular / plural normalisation: names first, then synonyms of any scope
    nq = norm_number(q)
    by_name = sorted({t["id"] for t in live if norm_number(t["name"]) == nq})
    rec["tiers"]["c_name"] = by_name
    via, scope = None, None
    if len(by_name) == 1:
        via = by_name[0]
    else:
        by_syn = {}
        for t in live:
            for text, sc in t.get("synonyms", []):
                if norm_number(text) == nq:
                    by_syn.setdefault(t["id"], set()).add(sc)
        rec["tiers"]["c_synonym"] = sorted(by_syn)
        if len(by_syn) == 1:
            via = next(iter(by_syn))
            scope = "/".join(sorted(by_syn[via]))
    if via is None:
        return rec
    t = next(x for x in live if x["id"] == via)
    target = t["name"] if scope is None else next(text for text, sc in t["synonyms"] if norm_number(text) == nq)
    used = needed_steps(q, target)
    what = "name" if scope is None else "%s synonym" % scope
    rec.update(tier="c", id=via, name=t["name"],
               label="S matched by normalised %s (%s)" % (what, ", ".join(used) if used else "white space only"))
    return rec


def label_short(rec: dict) -> str:
    """the label written into the TSV: tier and what matched."""
    if rec["tier"] is None:
        return "S undefined (no name, synonym or normalised name identifies exactly one live term; tiers: %s)" % "; ".join(
            "%s %d" % (k, len(v)) for k, v in rec["tiers"].items())
    return "name rule (%s): %s -> %s '%s'" % (rec["tier"], rec["label"], rec["id"], rec["name"])
