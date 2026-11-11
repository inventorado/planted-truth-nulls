# -*- coding: utf-8 -*-
"""Build arcs/audit/claims_register.tsv, the machine-readable table of the A1 claims register.

A compilation from text: arcs/audit/claims_register.md (DRAFT v5, commit 73d1313 or later; it governs), the 20
drafts arcs/audit/register_work/<key>.md (incorporated by reference at the sha256 of register section 8),
literature/notes/vairam2026hyperhypo.md (register section 2.9) and the pre-freeze outputs of register section 1.11 (v5;
binding): arcs/audit/register_sets/ (MANIFEST.json, the per-set JSONs, SEGURA_S7_TERMS.json, PRE_DG_ROWS.json) and
arcs/audit/register_maps/*.json (MIST64 classes and matrix identity, gated-map identities, GIA-MDD paths, carrier tests
and their self-test record, the Buch Fig. 5h grid, the Dear orientation check). Those JSONs hold labels, set membership
metadata, counts and hashes only; no map, gated carrier or audit-target material is opened here. The script

  1. verifies the sha256 of every draft against register section 8 (and section 8 against the copy encoded here), every
     per-set JSON against MANIFEST.json, and the carrier self-test record against the carrier spec; stops on any difference;
  2. writes one row per registered cell of all 21 targets, in target-number order and, within a target, in the order
     the register (then the draft) lists the cells; row numbers are assigned here, deterministically (they key the seeds);
     every row carries its S-build disposition (set id, size in the row's class universe, sha256, rule labels, status);
  3. reads the TSV back and checks it: header, row numbers, ids, the per-target m of register section 4 as the v5 rules
     give it, the claim ids, focal claims, class/status consistency, the section 1.11 outcomes; prints counts only;
  4. when every check passes, writes arcs/audit/register_freeze_manifest.json (sha256 of the TSV, this builder, the S-build
     manifest and its two tables, every register_maps/*.json and every src_register/*.py).

Fixed point (v5): the register's section 7 records this TSV's sha256 ('TSV sha256 <64 hex>'), so the TSV header records the
register's sha256 with that one field masked as 64 zeros and no commit id; the S-build manifest records the sha256 of the TSV
columns it reads, not the file's. A second build on the same inputs, and a build after the register is committed, write the
same bytes; the checks fail while section 7 does not equal the TSV written or the S-build does not point at this TSV.

DRAFT v6 (the orchestrator's decisions R1-R13 under the operator's standing delegation, 2026-09-26): the S-build's name-rule
records (register_sets/NAME_MATCHES.json) label every mapped row; R2's conditional sets ('S conditional ...') count in m's
upper bound only; R3's mouse rows read 'not auditable (definition not applicable)'; R5's sizes are columns; R8's precedence
orders the population composition; and (R4) the register's section 4 numbers and section 1.11 id lists are parsed from
claims_register.md and must equal the values derived from this TSV (a planted edit of a section 4 number must fail the
build: src_register/plant_register_numbers.py).

DRAFT v6.1 / v6.2 (the orchestrator's decisions Q1-Q8 and P1-P8 under the operator's standing delegation, 2026-09-26): one
source-1 criterion, positive and keyed by cell id (the builder asserts that register_maps/carrier_tests.json source1_lists.cells
holds exactly the Buch, Pagani, R2 and Romero-Garcia family rows, with Buch's printed labels); KEGG release rules (Romero-Garcia's
families: Enrichr KEGG_2015 or KEGG_2016 by the section 1.6 rule, v6.2 P5); Buch's GO-slim fallback from PANTHER 16.0's own
annotation (v6.2 P3). DRAFT v6.3 (O1-O7): the criterion's table-level statistics check, letter-bounded markers, input wording in
a list's own title, own-phrase stripping, one --name per family run, rival names (the builder asserts Buch's rival names equal the
PANTHER names register_sets/NAME_MATCHES.json records, plus 'structural constituent of ribosome'). DRAFT v6.4 (N1-N4): the
sheet-level refusal and non-data tokens; split naming only for the Zhang family, RG-15 / RG-V23 by their own title only (the
builder asserts the spec's family and own-title flags); rival-only names for family runs. DRAFT v6.5: source 1 must be
corroborated (Jaccard >= .80 with the pinned external definition, else the printed size); cells with neither are not auditable
(S undefined: source 1 uncorroborated) -- the builder asserts the spec's corroboration modes against the S-build and the TSV.
DRAFT v6.6 (B1, B2, C1-C8): every comparator pinned (set id + file / members sha256, or the KEGG family recipe) and asserted
here against the committed per-set JSONs; Buch's non-GO and Pagani's comparators built before the freeze by register 1.6's
resolution rule (its text asserted unchanged since it was written, sha256 RULE66_SHA), the unbuildable ones not auditable
(S undefined: comparator not buildable pre-freeze) -- the builder's COMP66 tables are asserted equal to the S-build's.
DRAFT v6.7 ((1)-(5), N1-N11): asdM12 built (Voineagu 2011 Supplementary Table 14); the uniform archive rule re-pins RGD, CTD and
the SFARI cells (read by the served release label); the registered SECONDARY view 'near-miss comparator' -- two columns
(secondary_view_near_miss_status, secondary_view_near_miss_set_id) and the view's own m' beside m (register 4, R4
'm.secondary.near_miss'); the builder asserts the view's pins in carrier_tests.json equal the S-build's and that no primary
status depends on it; the universe and HGNC pins (N3) asserted in the spec.
DRAFT v6.8 (the orchestrator under the operator's standing delegation, on the v6.7 final re-check; post hoc, declared): B S1 --
asdM12 moved to the near-miss view (R-d applied uniformly: 'asdM12' reaches Voineagu's M12 only through Parikshak 2013's name),
so BUCH-E-ASDdown-S1 ... S4 are not auditable in the primary view and counted in m' only (m 211 -> 207; m' 223); B S2 -- the
privacy guard on every workbook the register builders read (the S-build's concern; nothing here opens a workbook); C items in
the register and the S-build.
DRAFT v6.9 (the orchestrator's skeptic re-check 0 A / 2 B / 5 C, under the operator's standing delegation; post hoc, declared):
C3 -- NM_LABEL adds '/ name bridge'; C5 -- Buch's 'ASD rare de novo' (BUCH-E-RDNV-S1 ... S4, descriptor cells) not buildable in
the primary view by reading (iii) applied uniformly, Sanders 2019's ASD65 its near-miss comparator (m and m' unchanged).
DRAFT v6.10 (the orchestrator's v6.9 re-check 0 A / 1 B / 4 C; post hoc, declared): NM_LABEL adds '/ note reading'.
DRAFT v6.11 (the v6.10 re-check 0 A / 0 B / 4 C; post hoc, declared): text fixes only (register 1.6; the S-build's PAG route text).

Run:  python -X utf8 arcs/audit/claims_register_tsv_build.py [--draft-for-sbuild]
      --draft-for-sbuild writes the TSV without the S-build dispositions and without checks, only to feed
      src_register/s_build.py (which reads the columns row, cell_id, target_key, set_S, analysis_class, n_cells); the full
      build must follow.
Writes UTF-8 with LF line endings. Prints nothing but counts, hashes and check results.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from collections import OrderedDict, Counter

HERE = pathlib.Path(__file__).resolve()
AUDIT = HERE.parent
ROOT = AUDIT.parent.parent
REGISTER = AUDIT / "claims_register.md"
DRAFT_DIR = AUDIT / "register_work"
VAIRAM_NOTE = ROOT / "literature" / "notes" / "vairam2026hyperhypo.md"
AMEND4 = AUDIT / "prereg_amend_4.md"
AMEND5 = AUDIT / "prereg_amend_5.md"
OUT = AUDIT / "claims_register.tsv"
REGISTER_MIN_COMMIT = "73d1313"  # DRAFT v5 text (section 1.11)
SETS_DIR = AUDIT / "register_sets"
MAPS_DIR = AUDIT / "register_maps"
SRC_REG = AUDIT / "src_register"
FREEZE_MANIFEST = AUDIT / "register_freeze_manifest.json"

# register section 8 (the drafts, by reference) -- copied from claims_register.md; checked against the file below
DRAFT_SHA = OrderedDict([
    ("benkarim2021connectivity.md", "9ac5e2d38ee6d3e27dba008385f6207b4bf39136db4ce4f939bce1e2be270d5f"),
    ("berto2022connectivity.md", "ae795c268e2e08c4675993eae07141b8807fc4919c3b66b0e35cd2e7a12d4469"),
    ("buch2023asdsubgroups.md", "dd17a3b69fbaa2f21f5be3e0f0dbe902c0c3df75b98e3b81472a2d697406a02b"),
    ("dear2024corticalgene.md", "e17d9b106368f15cf7ef7f9543a441f7fe5fee671ffb2902645249d586b0701d"),
    ("giacomel2026cartography.md", "644dec2dc19e4cf287a5fda6dc709608e03032a44ec7089658813f3b36448be9"),
    ("hansen2022local.md", "12ea63a5329bc917da1b8e112bb35d491ac364df41e6c1feffa1649a29cdf653"),
    ("leyhausen2024intrinsic.md", "354c63003c23249a82f9ae8ae581ae7801172d812fecfe658734200e238c7e4a"),
    ("liu2026spatiotemporal.md", "fc2a25d4e71d1aaf2b789eddc8ca59f26316c6bf9c1c3e766878925da529b44c"),
    ("mamat2025molecular.md", "f6edbba333626da77add5f5c7453f233bb02ad653296f49b22811581cf01490b"),
    ("moreau2020mutations.md", "5b5a6a1e9321a619f8f16925b4357ed538c4ddcf7b5039cb3361e21a9b9f7596"),
    ("pagani2026crossspecies.md", "9a1d574aef76b7205a2c28a104ce7b7dca61c27f7796b9ed70df2cd3f0993e4c"),
    ("park2021subcortico.md", "ab2e78203ff3791642548dfbbaa05190dc9e06b3ebd2b5745b4ee3c10f93f959"),
    ("patel2021virtual.md", "685b0131915342a17530e91b83a17db8a45edd99da57337eb5ebf38b7fce4bf3"),
    ("pretzsch2024patterns.md", "4a41c8227bb23450f1ff280ee88b915a6f1f477167a18c9933da319e589a0d69"),
    ("rasero2023neurogenetics.md", "5f21dafb319637748bcb1b67269b34be9ff77f353be7b94c1f4b4a8836229e84"),
    ("romerogarcia2019synaptic.md", "617af5979c1830d11c34f389ceeb4259e70215ed2b952db8c5a342eeb356f1fb"),
    ("seelemeyer2025decomposing.md", "8ad454a2182b8ab37bcc161a00813c834aaf2297bc104cfc173319b5273b5a16"),
    ("segura2024symptommapping.md", "a38189942a98cc670537f931c8867733a0dc8f075865560688779acb19a972e4"),
    ("wan2026abide2multiplex.md", "16df2a97391ec5023fcfc543b6155e493c9d0aacc3227a485177d5cf3a976a5a"),
    ("xing2026interpretable.md", "71c08a198d9af250845be9cba2e2e7622165943f37115a10078563ff484e3e9c"),
])

COLS = ["row", "target_no", "target_key", "frozen11_row", "cell_id", "cell_class", "claim_form", "map", "set_S",
        "set_id", "set_size_in_class_universe", "set_sha256", "set_rule_labels", "set_status", "T",
        "direction", "analysis_class", "route", "inference_level", "status", "headline_population", "reproduction",
        "published_value_and_location", "gate", "focal", "verdict_counted_in_m", "dependencies", "notes", "n_cells", "map_index",
        "cell_index", "secondary_view_near_miss_status", "secondary_view_near_miss_set_id"]  # v6.7 (1): the near-miss view
SET_COLS = ("set_id", "set_size_in_class_universe", "set_sha256", "set_rule_labels", "set_status")

CELL_CLASSES = {"claim", "published-null", "non-ASD-outcome", "not-ASD-claim", "descriptor", "family"}
CLAIM_FORMS = {"set-vs-map", "decoded-list", "PLS-enrichment", "component", "gene-set-only", "other"}
M = "−"  # minus sign used in directions and values


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    try:
        r = subprocess.run(["git", "-C", str(ROOT)] + list(args), capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout.strip()
    except Exception as e:  # git missing
        return 1, "UNDETERMINED: git not available (%s)" % type(e).__name__


def die(msg):
    print("STOP: " + msg)
    sys.exit(1)


# ====================================================================================================================
# 0. the pre-freeze outputs (register section 1.11, v5; binding) -- labels, metadata, counts and hashes only
# ====================================================================================================================
def load_json(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


MANIFEST = load_json(SETS_DIR / "MANIFEST.json")
SET_ENTRY = {s["set_id"]: s for s in MANIFEST["sets"]}
SET_JSON = {}
for _s in MANIFEST["sets"]:
    if _s.get("json"):
        _p = SETS_DIR / _s["json"]
        if sha256_file(_p) != _s["sha256"]:
            die("register_sets/%s differs from MANIFEST.json's sha256" % _s["json"])
        SET_JSON[_s["set_id"]] = load_json(_p)
for _k, _f in (("segura_s7_terms", "SEGURA_S7_TERMS.json"), ("pre_dg_rows", "PRE_DG_ROWS.json"),
               ("universe_genes", "UNIVERSE_GENES.json")):  # v6.5: the corroboration's universes
    if MANIFEST[_k]["file"] != _f or sha256_file(SETS_DIR / _f) != MANIFEST[_k]["sha256"]:
        die("register_sets/%s differs from MANIFEST.json's sha256" % _f)
S7 = load_json(SETS_DIR / "SEGURA_S7_TERMS.json")
PREDG = load_json(SETS_DIR / "PRE_DG_ROWS.json")
DRAFT_FOR_SBUILD = "--draft-for-sbuild" in sys.argv[1:]
UNIVERSE_TXT = MANIFEST.get("universe_convention", "pending (draft for the S-build)")  # register v6 R5 (the S-build's text)
# register v6 R1: the name rule's record per cell (checked against MANIFEST.json; absent only in a draft-for-sbuild run)
NAMES = {}
if "name_matches" in MANIFEST:
    if sha256_file(SETS_DIR / MANIFEST["name_matches"]["file"]) != MANIFEST["name_matches"]["sha256"]:
        die("register_sets/NAME_MATCHES.json differs from MANIFEST.json's sha256")
    NAMES = {e["cell"]: e for e in load_json(SETS_DIR / MANIFEST["name_matches"]["file"])["cells"]}
elif not DRAFT_FOR_SBUILD:
    die("MANIFEST.json has no name_matches block (register v6 R1): re-run src_register/s_build.py")
IDENT = load_json(MAPS_DIR / "IDENTITY_prefreeze.json")
MIST = load_json(MAPS_DIR / "mist64_classes.json")
MISTM = load_json(MAPS_DIR / "mist64_ahba_matrix.json")
BUCH5H = load_json(MAPS_DIR / "buch_fig5h_grid.json")
GIAP = load_json(MAPS_DIR / "gia_mdd_paths.json")
DEAR_OR = load_json(MAPS_DIR / "dear_orientation.json")
CARRIER = load_json(MAPS_DIR / "carrier_tests.json")
CARRIER_SELF = load_json(MAPS_DIR / "carrier_tests_selftest.json")
CARRIER_SHA = sha256_file(MAPS_DIR / "carrier_tests.json")
CARRIER_ENGINE_SHA = sha256_file(SRC_REG / "carrier_test.py")
if CARRIER_SELF["spec_sha256"] != CARRIER_SHA or CARRIER_SELF["script_sha256"] != CARRIER_ENGINE_SHA:
    die("carrier_tests_selftest.json was not produced by the current carrier_tests.json / carrier_test.py: re-run the self-test")
if CARRIER_SELF["n_caught"] != CARRIER_SELF["n_cases"]:
    die("carrier self-test: %d of %d planted cases caught" % (CARRIER_SELF["n_caught"], CARRIER_SELF["n_cases"]))

# cell id -> its S-build set entries (a family's sets in the order of its defining table: family_cell_index)
CELL_SETS = OrderedDict()
for _s in MANIFEST["sets"]:
    for _c in _s["cells"]:
        _cid = _c.split(" (")[0]  # 'PRE-DG-01 (PRE-DG)' -> PRE-DG-01
        CELL_SETS.setdefault(_cid, []).append(_s)
for _cid, _l in CELL_SETS.items():
    _l.sort(key=lambda s: (SET_JSON.get(s["set_id"], {}).get("family_cell_index", 0), s["set_id"]))
NO_SET = MANIFEST["rows_without_a_set_now"]


def fmt_int(n):
    return "{:,}".format(n)


def sset(set_id):
    """the S-build JSON of a set (built or ruled on)."""
    if set_id not in SET_JSON:
        die("unknown S-build set " + set_id)
    return SET_JSON[set_id]


PSI_JSON = sset("psi_region_cortex")["source"]
PSI_PIN = ("pSI.data 1.0 (2013-12-03; the Dougherty laboratory's distribution, not on CRAN; %s, sha256 %s; register section 1.11 "
           "item 2: the only version that exists -- the '1.1' of v4 was the pSI package version)"
           % (PSI_JSON["url"], PSI_JSON["files"][0]["sha256"]))


def at_download(p):
    """register v6 R13: the identity fields compared at download -- byte size plus git blob id for git copies; byte size plus
    the served MD5 where the server gives a plain MD5 (an ETag of 32 hex digits, or a repository checksum declared MD5);
    byte size alone otherwise."""
    if p.get("blob_sha"):
        return "byte size + git blob id"
    et = (p.get("etag") or "").strip('"')
    if re.fullmatch(r"[0-9a-f]{32}", et):
        return "byte size + ETag (a plain MD5)"
    if p.get("checksum") and p.get("checksum_algorithm") == "MD5":
        return "byte size + MD5 (repository checksum)"
    return "byte size alone"


def ident(target, obj_sub, bitstreams=None):
    """register section 1.11 item 6 (NF11): a gated map's / carrier's identity before the freeze (listing level only)."""
    recs = [r for r in IDENT["records"] if r["target"] == target and obj_sub in r["object"]]
    if len(recs) != 1:
        die("IDENTITY_prefreeze.json: %d records for %s / %s" % (len(recs), target, obj_sub))
    parts = []
    for p in recs[0]["probes"]:
        if p["method"].startswith("local file"):
            parts.append("local copy %s B, sha256 %s (at use: sha256)" % (fmt_int(p["size"]), p["sha256"]))
            continue
        if bitstreams is not None and p.get("name") is not None and p["name"] not in bitstreams:
            continue
        url = p.get("url") or p.get("file_url")
        size = p.get("size") or p.get("content_length") or p.get("api_file_size")
        tag = ("git blob %s" % p["blob_sha"] if p.get("blob_sha") else "ETag %s" % p["etag"].strip('"') if p.get("etag")
               else "MD5 %s" % p["checksum"] if p.get("checksum") else "no ETag (Last-Modified %s)" % p["last_modified"]
               if p.get("last_modified") else "no ETag")
        if p["status"] != "ok":
            parts.append("%s (%s)" % (url, p["status"] + ("; " + p["error"] if p.get("error") else "")))
        else:
            parts.append("%s (%s B; %s; at download: %s)" % (url, fmt_int(size) if size else "size not returned", tag,
                                                              at_download(p)))
    extra = ""
    if bitstreams is not None:
        n_other = sum(1 for p in recs[0]["probes"] if p.get("name") is not None and p["name"] not in bitstreams)
        extra = "; the record's %d other bitstreams (article PDF, manuscript, licence, text / thumbnail derivatives) are listed there" % n_other
    return ("identity before the freeze (register section 1.11 item 6; register_maps/IDENTITY_prefreeze.json, listed %s): %s%s"
            % (IDENT["run_utc"][:10], "; ".join(parts), extra))


ID_RULE = ("sha256 taken at download under the gate; a mismatch with this identity -> 'not auditable (map changed)' (section 1.10 "
           "(0); declared deviation from prereg section 5.2's hash); the fields compared at download (register v6 R13): byte size "
           "+ git blob id for git copies, byte size + the served MD5 where the server gives a plain MD5, byte size alone otherwise "
           "(section 1.11 item 6)")


# ====================================================================================================================
# 1. verification of the inputs
# ====================================================================================================================
def verify_inputs():
    text = REGISTER.read_text(encoding="utf-8")
    sec8 = OrderedDict()
    in8 = False
    for line in text.splitlines():
        if line.startswith("## 8."):
            in8 = True
            continue
        if in8 and line.startswith("## "):
            break
        if in8 and line.startswith("| ") and ".md |" in line:
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) == 2 and len(parts[1]) == 64:
                sec8[parts[0]] = parts[1]
    if dict(sec8) != dict(DRAFT_SHA):
        die("register section 8 differs from the copy encoded in this script")
    got = OrderedDict()
    for name, want in DRAFT_SHA.items():
        p = DRAFT_DIR / name
        if not p.exists():
            die("draft missing: " + name)
        have = sha256_file(p)
        if have != want:
            die("sha256 mismatch for %s: register %s, file %s" % (name, want, have))
        got[name] = have
    return got


REG_TSV_SHA_RE = re.compile(r"(TSV sha256 )([0-9a-f]{64})")
REG_TSV_SHA_FIELD = None  # the TSV sha256 recorded in register section 7 (set by register_hashes)


def register_hashes():
    """The register records this TSV's sha256 (section 7, 'TSV sha256 <64 hex>') and this TSV records the register's sha256, so
    one of the two must leave the other's field out: the TSV header records the register's sha256 with that one field masked
    as 64 zeros (unmasked hash: console and register_freeze_manifest.json). Returns (unmasked, masked)."""
    global REG_TSV_SHA_FIELD
    raw = REGISTER.read_bytes()
    text = raw.decode("utf-8")
    hits = list(REG_TSV_SHA_RE.finditer(text))
    s7, s8 = text.find("\n## 7."), text.find("\n## 8.")
    if len(hits) != 1 or not (0 <= s7 < hits[0].start() < s8):
        die("the register must carry exactly one 'TSV sha256 <64 hex>' field, in section 7 (found %d)" % len(hits))
    REG_TSV_SHA_FIELD = hits[0].group(2)
    masked = text[:hits[0].start(2)] + "0" * 64 + text[hits[0].end(2):]
    return hashlib.sha256(raw).hexdigest(), hashlib.sha256(masked.encode("utf-8")).hexdigest()


# ====================================================================================================================
# 2. data -- the registered cells
# ====================================================================================================================
ROWS = []


class Target:
    def __init__(self, no, key, f11, gate, **defaults):
        self.no, self.key, self.f11, self.gate, self.d = no, key, f11, gate, defaults


def add(t, cell_id, **kw):
    rec = dict(t.d)
    rec.update(kw)
    rec["target_no"] = str(t.no)
    rec["target_key"] = t.key
    rec["frozen11_row"] = t.f11
    rec["cell_id"] = cell_id
    rec.setdefault("gate", t.gate)
    rec.setdefault("focal", "no")
    rec.setdefault("verdict_counted_in_m", "no")
    rec.setdefault("n_cells", "1")
    if "map_index" not in rec:  # register section 1.9 (v4): 0 for a single-map cell; a row with no registered T needs no seed
        rec["map_index"] = MAPIDX_NA if str(rec.get("T", "")).startswith("none") else "0"
    if "cell_index" not in rec:  # register section 1.9 (v5): 0 for a single cell; 1 ... n for a unit's cells in its table's order
        rec["cell_index"] = MAPIDX_NA if str(rec.get("T", "")).startswith("none") else "0"
    ROWS.append(rec)


# ---------------------------------------------------------------- shared texts (register sections 1.3-1.7)
T_SVM = ("set-vs-map (section 1.4): T = Pearson r(y, set score), set score = per-parcel mean of S's genes on the section 3.1 "
         "matrix of the analysis class; Level 0 = parametric p of r; Spearman beside it; full verdict (Level 0, class-stratified "
         "site leg, species leg max(G1, G3m, G6s, G6l), each < .025; amendment 3 section 2)")
T_DL = ("decoded-list enrichment (section 1.4; amendment 4 section 2): T = mean over S of the per-gene Pearson r(y, gene "
        "expression) (= ⟨ŷ, s_z⟩); Level 0 = Welch t of S's per-gene r against the rest of the universe; site leg recomputes "
        "every per-gene r on each surrogate; species leg by amendment 3 section 2's enrichment rule (G1, G3m, G6l = mean over each "
        "null set, per-gene r and y fixed; G6s on the z-scored matrix; every null conditioned s_B(S) + s_W(R)); T_abs descriptor "
        "beside it (mean over S of |per-gene r|, upper tail; Level 0 Welch t of |r|; site leg; unconditioned G1, G3m, G6l; "
        "'unsigned descriptor, uncalibrated (no plant for |r|; |r| favours smooth, brain-enriched genes)')")
T_PLSE = ("PLS enrichment (section 1.4; prereg section 4.7): T = mean PLS1 weight of S's genes, component oriented so "
          "corr(score, y) > 0; Level 0 = Welch t; PLS1 refit on every surrogate; species leg by amendment 3 section 2's "
          "enrichment rule")
T_COMP_PLS1 = ("component level (section 1.4; prereg section 4.7): T = R^2 of PLS1 (cascade.pls1); Level 0 = 10,000 parcel-label "
               "permutations with refit; class-stratified site leg (refit on every surrogate); read 'passes / does not pass at "
               "component level', label 'site leg only; not calibrated against expression-aligned maps'; never a survival")


def t_comp_fixed(comp):
    return ("component level (section 1.4; amendment 4 section 2): T = Pearson r(y, %s) for a fixed component; Level 0 = "
            "parametric p of r; class-stratified site leg; read 'passes / does not pass at component level', label 'site leg "
            "only; not calibrated against expression-aligned maps'; never a survival" % comp)


T_NTAS_POOLED = ("not testable as stated (section 1.4: a list that the paper states pools both signs); computed as descriptors: "
                 "the signed T of the claim's form (two-sided, with its legs) and T_abs (mean over S of |per-gene r|, upper tail; "
                 "Level 0 Welch t of |r|; site leg; unconditioned G1, G3m, G6l; 'unsigned descriptor, uncalibrated')")

ROUTE_VOL_AAL = ("re-parcellated: volume -> V-AAL via the PCP aal_roi_atlas.nii.gz (sha256 40b1edfa...) resampled to the map's "
                 "grid by nearest neighbour; parcel value = mean over its voxels with a finite non-zero value; a parcel with < 50 % "
                 "of its voxels finite and non-zero is dropped and reported (section 1.7)")
ROUTE_VOL_DKCTX = ("re-parcellated: volume -> dk-ctx via abagen atlas-desikankilliany.nii.gz (sha256 0a28c93f...) resampled to the "
                   "map's grid by nearest neighbour, cortical parcels; parcel value = mean over its voxels with a finite non-zero "
                   "value; a parcel with < 50 % of its voxels finite and non-zero is dropped and reported (section 1.7)")
ROUTE_SURF = ("re-parcellated: fsaverage surface -> dk-ctx via FreeSurfer's fsaverage lh.aparc.annot (FreeSurfer 7.4.1 file, "
              "sha256 recorded at download); parcel value = mean over the label's vertices with a finite value; labels 'unknown' "
              "and 'corpuscallosum' excluded; DK labels matched to the abagen DK names (section 1.7)")
ROUTE_PARCEL_RULE = ("the source atlas and abagen's DK atlas compared on the source atlas's native grid (DK resampled to it by nearest "
                     "neighbour); each source parcel assigned to the DK label holding the majority of its voxels (a parcel whose "
                     "majority is outside every DK cortical label is dropped and reported); DK value = voxel-count-weighted mean of "
                     "its assigned parcels; left hemisphere only (section 1.7)")
ROUTE_GLASSER = ("re-parcellated: Glasser-360 parcel values -> dk-ctx via HCP-MMP1_on_MNI152_ICBM2009a_nlin.nii.gz (Horn 2016, "
                 "figshare 3501911); " + ROUTE_PARCEL_RULE)
ROUTE_SCHAEFER = ("re-parcellated: Schaefer-400 (17 networks) parcel values -> dk-ctx via nilearn fetch_atlas_schaefer_2018("
                  "n_rois=400, yeo_networks=17, resolution_mm=1); " + ROUTE_PARCEL_RULE)
ROUTE_POWER = ("re-parcellated: Power spheres -> V-AAL: each sphere to the AAL label containing its centroid, using the ROI "
               "coordinates of the paper's own table; label value = mean of its spheres (a sphere whose centroid falls outside every "
               "AAL label is dropped and reported); coordinates not in the carrier -> 'not auditable (ROI coordinates unpublished)' "
               "(section 1.7)")

# register section 1.9 (v4): seeds carry a map index
MAPIDX_NA = "n/a: no registered T (never computed; no seed)"
MAPIDX_MAMAT = "0 = ABIDE I; 1 = ABIDE II (section 1.9)"
MAPIDX_RGVAL = "0 = Val1; 1 = Val2 (section 1.9: Romero-Garcia's validation families; register v6 R7)"

# headline population (register section 1.2, v4); frozen-11 rows only -- added targets are never headline
HL_ADDED = "out: added target (amendment 4 section 0.1; descriptive, never headline)"
HL_DESC = "out: descriptor cell (section 1.1)"
HL_PN = "out: published-null cell (section 1.1)"
HL_NTAS = "in: not testable as stated -- kept in as a non-survival with this flag (sections 1.2, 1.4)"
HL_NOTASD = "out: not an ASD claim (neurotypical participants only; section 1.1)"
HL_IN_NA = "in: not auditable -- kept in as a non-survival (section 1.2; prereg section 5.1)"
HL_IN_COMP = "in: component-level claim -- a non-survival whatever it shows (section 1.2; amendment 5 section 3)"
HL_IN_NCT = "in: 'no calibrated test' -- a non-survival (section 1.2; amendment 5 section 3)"
HL_IN_FV_CHECK = ("in: full-verdict claim (section 1.2); leaves the population if the section 1.5 check flags it 'not reproduced'")
HL_IN_FV_DESC = "in: full-verdict claim (section 1.2); reproduction descriptive, never flagged (section 1.5)"
HL_FAMILY = "; a family counts once (sections 1.1, 1.2)"
# register sections 1.2, 1.11 item 2 (v5): the S-build outcomes
HL_IN_NA_SU = ("in: not auditable (S undefined) -- kept in as a non-survival (section 1.2; prereg section 5.1; register section 1.11 "
               "item 2)")
HL_OUT_LT5 = ("out: not testable (< 5 columns of S in the class universe) -- prereg section 4's mechanical 'not testable', a "
              "frozen-text exclusion (section 1.2; register section 1.11 item 2)")
HL_IN_NA_DNA = ("in: not auditable (definition not applicable) -- kept in as a non-survival (section 1.2; prereg section 5.1; register "
                "section 1.11 item 2, v6 R3)")
# register v6 R2: a row whose S lies in a gated carrier (source 1) -- counted in m's upper bound only
M_UPPER = "yes (upper bound only: S conditional on a gated carrier, section 1.6 R2)"

# gates (register section 0, v4): the status of every gated row carries the deferral as its first flag; a frozen-11 row that
# would be in the population is out of the interim population while its gate is closed (section 1.2; amendment 4 section 0)
GATE_STATUS = {"G1": "deferred (gate G1 closed)", "G2": "deferred (gate G2 closed)"}
DEFER_HL = ("out (interim): deferred (gate %s closed; listed apart and counted neither way while it is closed: section 1.2, "
            "amendment 4 section 0); on opening: ")
DEAR_STATUS = ("deferred pending provenance (amendment 4 section 0: 'the deferral is lifted only by provenance'; register sections 0, "
               "3.3): run only if the provenance is established, then under gates G1 and G2 (both open)")
VR_DEFER = ("deferred (prereg section 5.1: 'deferred to A2'; A2 is superseded by A3, PROGRAMME.md; register section 2.9; a change "
            "of status needs an amendment)")
HL_VR = ("out: deferred (prereg section 5.1; register sections 1.2, 2.9: Vairam / Roy stays deferred, listed apart and counted "
         "neither way)")

GO_RULE = ("section 1.6 GO rule: annotations to the term or any descendant over is_a and part_of, all evidence codes except ND, "
           "NOT-qualified annotations excluded")
HGNC = "mapped to the class universe by the section 1.6 HGNC rule (approved, previous, alias; ambiguous symbols dropped; drops listed)"
PSI_DEV = "the human BrainSpan developmental table (columns = region x period)"
PSI_REGION = "the human brain-region table (read by the S-build as pSI.data human$young.adulthood: an S-build reading, section 1.6 R3)"
PSI_CELL = "the mouse cell-type table (TRAP)"


PSI_SRC = ("the pSI.data distribution (Xu et al. 2014), pinned by the pre-freeze S-build: " + PSI_PIN + "; section 1.6")


def psi_set(table, match):
    """register section 1.6 (v4): pSI.data tables and cell labels, with the column-matching rule."""
    return ("%s, %s, at pSI < .05: the column found by case-insensitive token match of %s (an S-build reading, section 1.6 R3: "
            "the query's tokens are a subset of the column's tokens); exactly one matching column required, else 'not auditable "
            "(S undefined)' (section 1.6)" % (PSI_SRC, table, match))


def carrier_note(txt):
    return (" Carrier test (section 1.8; pre-registered before the freeze, run under the gate by src_register/carrier_test.py, which "
            "prints pass / fail and counts only): " + txt + (" Spec: register_maps/carrier_tests.json sha256 %s (register section 1.11 "
            "item 8 readings); engine: src_register/carrier_test.py sha256 %s; self-test %d / %d planted cases caught "
            "(register_maps/carrier_tests_selftest.json)." % (CARRIER_SHA, CARRIER_ENGINE_SHA, CARRIER_SELF["n_caught"],
                                                              CARRIER_SELF["n_cases"])))

# ====================================================================================================================
# target 1 -- Segura 2024/25
# ====================================================================================================================
T1 = Target(1, "segura2024symptommapping", "1", "none",
            map=("NeuroVault 790618 (MFG-seed iFC x ADOS-2 CSS-Total, zstat1, unthresholded group Z map, NYU/CMI clinical sample "
                 "n = 166; FSL MNI152 4 mm grid) file image_790618_zstat1_ADOS2Total_dm_MFG_iFC_corrected_sex_ADOSPOS_-_AS_TX.nii.nii.gz, "
                 "sha256 802b4b6bf31136aee0507676a3ca4c14e0ba97bafe378f5b6aaddbe5c160af12; voxels = 0 read as missing (outside the "
                 "map's mask)"),
            analysis_class="V-AAL",
            route=ROUTE_VOL_AAL + "; V-AAL because the paper decoded the whole brain (mask=full: cortex, subcortex, cerebellum)",
            inference_level=("gene null only (uniform): analytic hypergeometric test against a uniform 20,787-gene background "
                             "(section 1.3) [draft reading 'none' recorded]"),
            dependencies=("SEG-C1 family shares y (790618) and S (Table S4); SEG-C3 cells nested in SEG-C1's 107-gene overlap; "
                          "shares the CMI collection with Pagani (register 2.1 Q2); NeuroVault-decoding family with Pagani, Park, "
                          "Leyhausen"))
SEG_GATE_NOTE = (" Gate none (register section 0: Segura ungated -- its seal rested on A3's hypotheses, now frozen; its Child Mind "
                 "Institute sample is not ABIDE II and A3 has no HBN arm; a later A3 HBN amendment declares this audit as an "
                 "exposure; the section 2.1 heading reads 'ungated (section 0)').")

SEG_S4 = ("Table S4 (MOESM2 pp. 4-36): 1,046 HGNC symbols (legacy symbols; no Ensembl IDs), the paper's n; source 1 (the paper's "
          "own list); the repo list (1,141 symbols) not used (register 2.1 Q3); " + HGNC + "; external (Satterstrom 2019 exome "
          "burden: 932 PTV genes with pLI > .9 + 114 PTV/missense genes re-selected at FDR q < .05), not selected on imaging")
SEG_STATUS = ("not testable as stated: the decoded list pools positive and negative associations (Supplement section 6: "
              "'positive and negative t both kept') (register 2.1)")
SEG_T = ("not testable as stated (section 1.4: the decoded list pools both signs); computed as descriptors on V-AAL: the signed "
         "decoded-list T (mean over S of the per-gene Pearson r(y, expression), two-sided, with its verdict legs) and T_abs (mean "
         "over S of |per-gene r|, upper tail; Level 0 Welch t of |r|; site leg; unconditioned G1, G3m, G6l; 'unsigned descriptor, "
         "uncalibrated')")
SEG_DIR = "two-sided for the signed descriptor (the decoded list pools both signs, Supplement section 6); T_abs upper tail"

add(T1, "SEG-C1", cell_class="claim", claim_form="decoded-list", set_S=SEG_S4, T=SEG_T, direction=SEG_DIR,
    status=SEG_STATUS, headline_population=HL_NTAS,
    reproduction=("descriptive (amendment 4 section 2): NeuroVault decoder output for image 790618 (mask=full; fetched after the "
                  "freeze, ungated), FDR q < .05 with positive and negative t both kept, then the hypergeometric test against the "
                  "20,787-gene background; OR, p and Jaccard with Table S6 (107 genes; the 1,519-gene decoded list is unpublished) vs "
                  "OR 1.6, p .0002"),
    published_value_and_location=("OR = 1.6, p = 0.0002; 107 of the 1,519 decoded genes in S (Results 'Transdiagnostic in silico "
                                  "gene expression'; Fig. 4 top; Table S6, MOESM2 p. 38); Abstract (i); Discussion"),
    focal="yes",
    notes=("id: register. Per-row focal of frozen-11 row 1 (register 2.1, section 4: a decoded-list form, status 'not testable as "
           "stated'; Results 'Transdiagnostic in silico gene expression'). S likely brain-enriched (N1 check applies); m ~ 961 > 100 -> "
           "'power not measured at this set size' (draft)." + SEG_GATE_NOTE))
add(T1, "SEG-C2", cell_class="published-null", claim_form="decoded-list",
    map=("NeuroVault 781986 (authors' negative-control seed map, as the text names it) file "
         "image_781986_zstat1_PostHocSCA_VisualSeed2iFC_NegativeControl.nii.gz, sha256 "
         "0c476e8e8fa227edc6fb0007c4eccd92e5376361b497f836fef3d0cd8c1f4741; same grid; voxels = 0 read as missing; image 801380's "
         "matching sphere (22-12-22) recorded, not run (register 2.1)"),
    set_S="as SEG-C1 (Table S4, 1,046 symbols; source 1)", T=SEG_T, direction=SEG_DIR,
    status="not testable as stated: pooled decoded list, as SEG-C1 (register 2.1: 'also pooled -> not testable as stated, descriptors only')",
    headline_population="out: published-null cell (section 1.1; also not testable as stated)",
    reproduction=("descriptive (amendment 4 section 2): NeuroVault decoder output for image 781986 (mask=full; ungated), FDR "
                  "q < .05, both signs; hypergeometric OR and p vs OR 1.7, p .2"),
    published_value_and_location=("OR = 1.7, p = 0.2 (n.s.), 7,572 decoded genes (Supplement section 8, MOESM1); main text Results: "
                                  "control analyses 'did not yield any significant findings'"),
    dependencies="SEG-C1 (same S); control seed chosen for |Z| < .5 in the MDMR map and r <= -.20 with the MFG map",
    notes=("id: register. Within-paper negative control. Draft arithmetic note: an expected overlap of ~381 (7,572 of 20,787 decoded, "
           "1,046 genes) makes OR 1.7 with p .2 hard to square (unresolved)."))

SEG_C3 = [("a", "axonogenesis", "14 / 1.9 / 7.35 / 9.4e-6"),
          ("b", "axonogenesis involved in innervation", "3 / 0.05 / 64.75 / 4.88e-3"),
          ("c", "neuron projection morphogenesis", "16 / 2.53 / 6.33 / 1.0e-5"),
          ("d", "dendritic spine morphogenesis", "3 / 0.09 / 32.38 / 0.024"),
          ("e", "axon extension", "4 / 0.24 / 16.53 / 0.0249"),
          ("f", "axon guidance", "7 / 1.17 / 5.96 / 0.0364"),
          ("g", "regulation of axonogenesis", "6 / 0.81 / 7.38 / 0.0356")]
for letter, term, vals in SEG_C3:
    add(T1, "SEG-C3" + letter, cell_class="claim", claim_form="decoded-list",
        set_S=("GO BP '%s' at GO release 2024-01-17 (the release the paper names; the term reached by the name rule of sections 1.1 / 1.6; %s) intersected "
               "with Table S4 (1,046) (register 2.1: S = GO term ∩ Table S4, the paper's two-list nesting); < 5 columns in the class "
               "universe -> 'not testable' (section 1.6)" % (term, GO_RULE)),
        T=SEG_T, direction=SEG_DIR, status=SEG_STATUS, headline_population=HL_NTAS,
        reproduction=("descriptive (amendment 4 section 2): the decoded list re-derived as SEG-C1 (NeuroVault decoder, 790618, "
                      "mask=full, FDR q < .05, both signs), intersected with Table S4 (Jaccard vs Table S6's 107), then the paper's GO "
                      "over-representation (PANTHER / AmiGO 2, whole Homo sapiens reference, FDR); fold enrichment and FDR vs Table S7"),
        published_value_and_location=("genes / expected / fold / FDR p = %s (Table S7, MOESM2 p. 39); term named in Fig. 4 bottom / "
                                      "Fig. S6; Results 'most significant terms indexed ... axonogenesis'; Abstract (ii)" % vals),
        dependencies="nested in SEG-C1 (107-gene overlap); GO terms overlap (parents / children); shares y and S with SEG-C1",
        notes="id: register. One of the seven GO terms the text and Fig. 4 name (register 2.1)." + SEG_GATE_NOTE)
def ordinal(n):
    return "%d%s" % (n, "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))


S7_OTHER = [t for t in S7["terms"] if t["named"] == "other"]
if [t["cell_id"] for t in S7_OTHER] != ["SEG-C3-D%02d" % k for k in range(1, 72)] or S7["n_unresolved"] != 0:
    die("SEGURA_S7_TERMS.json: the 71 descriptor terms are not SEG-C3-D01 ... D71 in printed order, or a term is unresolved")
for k, term in enumerate(S7_OTHER, start=1):
    add(T1, term["cell_id"], cell_class="descriptor", claim_form="decoded-list",
        set_S=("GO BP '%s' (%s; resolved by %s at GO release 2024-01-17; the Table S7 term printed '%s', printed order %d of 78, "
               "printed row %d of 77 -- row 1 holds two terms; register sections 2.1, 1.11 item 3; register_sets/SEGURA_S7_TERMS.json) "
               "(%s) intersected with Table S4 (1,046) (register 2.1: S = GO term ∩ Table S4)"
               % (term["go_name"], term["go_id"], term["resolved_by"], term["term"], term["printed_order"], term["printed_row"],
                  GO_RULE)),
        T=("descriptor (section 1.1): the signed decoded-list T (two-sided) and T_abs (upper tail) on V-AAL, as SEG-C3a-g"),
        direction="two-sided (descriptor cell; pooled decoded list)",
        status="auditable (descriptor cell; map public; S built by the pre-freeze S-build, section 1.11 items 1 and 3; ungated)",
        headline_population=HL_DESC,
        reproduction="descriptive (amendment 4 section 2): as SEG-C3a-g (fold enrichment and FDR vs Table S7)",
        published_value_and_location=("Table S7 row of '%s' (genes / expected / fold / FDR q < .05), MOESM2 p. 39; one of the 78 GO "
                                      "terms of 'n = 78 GO terms (Table S7)' (Results)" % term["term"]),
        dependencies="nested in SEG-C1 (107-gene overlap); overlapping GO terms",
        cell_index=str(k),
        notes=("id: register (register 2.1, section 1.11 item 3: 'Table S7's other 71 terms', descriptor cells SEG-C3-D01 ... D71 in "
               "Table S7's printed order). Seed cell index %d = its place among the 71 in the defining table's order (section 1.9)."
               % k))

# ====================================================================================================================
# target 2 -- Patel 2021
# ====================================================================================================================
T2 = Target(2, "patel2021virtual", "2", "G2",
            map=("eTable 4, column Estimate (ASD - control cortical-thickness difference; random-effects meta-analysis of 19 "
                 "ENIGMA-ASD cohorts incl. ABIDE and ABIDE2, eTable 1B; 34 left DK regions), supplement PDF "
                 "jamapsychiatry-e202694-s001.pdf p. 26, sha256 d9da0b801a43eb14b11276ba0b2df5cb3dbe376d1c56820f6f756b504a54f2e8; "
                 "transcribed by a non-printing script with read-back (register 2.2); " + ident("patel2021virtual", "eTable 4")
                 + " -- the identity rests on the local PDF (the PMC URL returns an interstitial; register section 1.11 item 6); "
                 + ID_RULE),
            analysis_class="dk-ctx",
            route=("native: Desikan-Killiany, 34 left cortical parcels, read as dk-ctx (amendment 5 section 4.3); section 3.1 V-DK "
                   "matrix, left cortical rows"),
            inference_level=("gene null only (uniform): competitive random gene sets of the panel's size drawn within a 2,511-gene "
                             "reference pool (100,000 resamples), FDR over 9 cell types; no spatial null"),
            dependencies=("PAT-C1-C3 and the null panels share y; PAT-C4 depends on C1-C3's selection; ENIGMA-ASD cohorts shared with "
                          "Giacomel, Hansen and Liu T3 (overlapping cohorts, three different files; dependent)"))

PAT_CLAIM_TXT = ("Results 'Virtual Histology of Group Difference in Cortical Thickness': expression of the panel's genes 'was negatively "
                 "associated with the interregional profile of group differences in cortical thickness'")
for cid, panel, n, nlist, val, fdr, loc, focal in [
        ("PAT-C1", "CA1 Pyramidal", 103, 95, M + "0.201", "5.40E-04", "Key Points; Results; Figure 3; eTable 9 (p. 31)", "yes"),
        ("PAT-C2", "Astrocyte", 54, 51, M + "0.226", "1.79E-03", "Results; Abstract; Figure 3; eTable 9 (p. 31)", "no"),
        ("PAT-C3", "Microglia", 48, 44, M + "0.212", "6.53E-03", "Results; Abstract; Figure 3; eTable 9 (p. 31)", "no")]:
    add(T2, cid, cell_class="claim", claim_form="set-vs-map",
        set_S=("Shin 2018 Table S1 '%s' panel (Zeisel 2015 markers ∩ 2,511 consistent genes): %d HGNC symbols (%d in the abagen DK "
               "15,633-gene list, counted by the draft); section 1.6 source 2 (the primary publication the paper cites; 'S re-derived'); "
               "%s" % (panel, n, nlist, HGNC)),
        T=T_SVM, direction=M + " (published average bicor negative; unambiguous)", status="auditable (under G2)",
        headline_population=HL_IN_FV_CHECK,
        reproduction="4.1 check: mean per-gene bicor of S's genes with y on our matrix vs %s (+-.05; an opposite sign -> 'not reproduced (sign)')" % val,
        published_value_and_location="average bicor %s, FDR p %s (%s); %s" % (val, fdr, loc, PAT_CLAIM_TXT),
        focal=focal, verdict_counted_in_m="yes",
        notes=("id: register." + (" Per-row focal of frozen-11 row 2 (Key Points; Results 'Virtual Histology...'; register section 4)."
                                  if focal == "yes" else "")
               + " dk-ctx: 'power not measured in this class' (amendment 5 section 3)."))
add(T2, "PAT-C4", cell_class="claim", claim_form="component",
    set_S=("the three panels (CA1 pyramidal, astrocyte, microglia) chosen by their significance on this same map (eTable 9) -> "
           "amendment 3 section 2 selected-list rule: the panel selection re-run on every permutation and surrogate"),
    T=("component level (section 1.4): T = R^2 of y on the three panel set scores (multivariable linear regression), refit with the "
       "panel selection re-run on every permutation and surrogate (draft section 3); never computed (not auditable)"),
    direction="+ (upper tail: R^2 above the null)",
    inference_level="none: no test reported (eMethods 'Estimation of explained variance') (section 1.3)",
    status=("not auditable: the selection re-run that amendment 3 section 2 requires needs the unpublished 2,511-gene reference pool "
            "(register 2.2)"),
    headline_population="in: not auditable, component-level -- a non-survival (section 1.2)",
    reproduction="4.1 check: R^2 with the paper's own model (linear) vs .54 (robust .44) (not run: not auditable)",
    published_value_and_location=("R^2 = 54 % (linear), 44 % (robust), model CA1 + astrocyte + microglia (eTable 18A, p. 40); Abstract / "
                                  "Results: the 3 cell types 'explain between 25% and 54% of variance'"),
    notes=("id: register. Register 2.2 gives the target's level as gene null only (uniform); this cell has no test (draft), so 'none'. "
           "PAT-X1-X3 out of scope (recorded, not registered; register 2.2)."))
for i, (panel, n, nlist, val, fdr) in enumerate([
        ("S1 Pyramidal", 73, 72, "0.019", "0.416"), ("Interneuron", 100, 93, "0.034", "0.853"),
        ("Oligodendrocyte", 60, 55, M + "0.002", "0.660"), ("Ependymal", 84, 73, M + "0.067", "0.690"),
        ("Endothelial", 57, 54, "0.021", "0.410"), ("Mural", 25, 21, M + "0.079", "0.712")], start=1):
    add(T2, "PAT-N%d" % i, cell_class="descriptor", claim_form="set-vs-map",
        set_S="Shin 2018 Table S1 '%s' panel: %d symbols (%d in the abagen DK list); source 2 ('S re-derived'); %s" % (panel, n, nlist, HGNC),
        T="descriptor (section 1.1): " + T_SVM, direction="two-sided (register 2.2: null panels are descriptor cells, two-sided)",
        status="auditable (descriptor cell; under G2)", headline_population=HL_DESC,
        reproduction="4.1 check (descriptor, informational): mean per-gene bicor vs %s" % val,
        published_value_and_location="average bicor %s, FDR p %s (eTable 9, p. 31; ASD null panel)" % (val, fdr),
        notes="id: compiler (register 2.2: 'Six null panels: descriptor cells, two-sided').")

# ====================================================================================================================
# target 3 -- Giacomel 2026
# ====================================================================================================================
GIA_Y_CTX = ("xlsx ENIGMA_structural_organised.xlsx at repository commit 93de089b614f72bda25f441518ad04b1e938fb9b (sha256 prefix "
             "15101878fd0cae37; the version behind the published ASD tables), sheet Thickness, column ASD: ENIGMA-ASD Cohen's d, "
             "bilateral mean (M_<region>_thickavg), 34 DK regions (van Rooij 2018, 1,571 ASD / 1,651 controls); its ASD column "
             "compared with c022a29's (sha256 prefix a4d4feecb028366c), any difference recorded, 93de089 governing (register 2.3)")
GIA_Y_SUB = ("same xlsx @93de089 (sha256 prefix 15101878fd0cae37), sheet Subcortical, column ASD: 7 structures (accumbens, "
             "amygdala, caudate, hippocampus, pallidum, putamen, thalamus; alphabetical sheet order; no ventricles); c022a29 "
             "comparison as the cortical sheet")
GIA_Y_MDD = ("same xlsx @93de089 (sha256 prefix 15101878fd0cae37), sheet Thickness, column MDD: the MDD map of the same xlsx "
             "(register 2.3), bilateral-mean Cohen's d, 34 DK regions")
GIA_Y_MDD_SUB = ("same xlsx @93de089 (sha256 prefix 15101878fd0cae37), sheet Subcortical, column MDD (7 structures; alphabetical "
                 "sheet order)")
GIA_ID = ("; " + ident("giacomel2026cartography", "@93de089") + "; the c022a29 copy compared: "
          + ident("giacomel2026cartography", "@c022a29").split(": ", 1)[1] + "; " + ID_RULE)
GIA_Y_CTX, GIA_Y_SUB, GIA_Y_MDD, GIA_Y_MDD_SUB = (GIA_Y_CTX + GIA_ID, GIA_Y_SUB + GIA_ID, GIA_Y_MDD + GIA_ID,
                                                  GIA_Y_MDD_SUB + GIA_ID)


def gia_path(commit, path):
    """register section 1.11 item 7: GIA-MDD paths asserted against the repository tree listings (gia_mdd_paths.json)."""
    for key in ("e045bc5_sets", "eda33ab_needed"):
        for e in GIAP[key]:
            if e["commit"].startswith(commit) and e["path"] == path:
                if not e["present"]:
                    die("GIA-MDD path absent: %s @%s" % (path, commit))
                return "%s @%s (present in the tree listing of %s; git blob %s, %s B; register section 1.11 item 7)" % (
                    path, commit, e["listed_utc"][:10], e["blob_sha"], fmt_int(e["size"]))
    die("GIA-MDD path not asserted: %s @%s" % (path, commit))
GIA_SUB_DEFECT = ("not reproduced (documented source defect: misaligned structures) -- every subcortical cell, the combined and DEG "
                  "ones included (register 2.3); the misaligned pairing reproduced as a descriptor")
GIA_ROUTE_CTX = ("native: bilateral-average DK values placed on the 34 left DK cortical parcels, as the paper (section 1.7), read as "
                 "dk-ctx (amendment 5 section 4.3)")
GIA_ROUTE_SUB = ("native: the 7 values on the 7 left aseg parcels of V-DK, matched by structure name (the paper paired the "
                 "alphabetical sheet with atlas-ordered rows by position: the documented defect); single class, 'calibration "
                 "extrapolated (class)' (section 1.7)")
GIA_LVL_CTX = ("spatial null only: spherical spin (netneurotools gen_spinsamples 'vasa', 1,000 rotations, seed 2024, left DK "
               "fsaverage5 centroids), one-sided in the observed direction, p = count/1,000 (no +1); FDR across the three thresholds "
               "within disorder; no gene-set null")
GIA_LVL_SUB = ("other: resampling the 7 GEDAR values with replacement (np.random.choice), one-sided in the observed direction; "
               "neither spatial nor gene null")
GIA_LOC = ("Results 'Correlations between GEDAR maps and brain structural changes' ('None of the remaining correlations reached "
           "significance'); Figs 3-5B")
GIA_POOL = ("the paper's AHBA ∩ HPA pool (3,909 genes; HPA 4,971-gene brain-elevated list) recorded, species legs on the section 3.1 "
            "universe (register 2.3)")
T3 = Target(3, "giacomel2026cartography", "2", "G2",
            dependencies=("cortical cells share y; nested thresholds share genes (10 % > 5 % > 1 %); combined sets contain the up/down "
                          "members; ENIGMA-ASD cohorts shared with Patel, Hansen and Liu T3 (overlapping cohorts, different files)"))
GIA_CELLS = OrderedDict([
    # id: (scheme, thr, compartment, list, m, published, shipped)
    ("GIA-C01", ("combined", "1 %", "ctx", "top", 28, M + "0.150 / .252 / .378 (Supplementary Table S1)", "")),
    ("GIA-C02", ("combined", "1 %", "sub", "top", 28, M + "0.262 / .289 / .316 (Supplementary Table S1)", "")),
    ("GIA-C03", ("combined", "5 %", "ctx", "top", 138, "0.413 / .073 / .219 (Supplementary Table S1)", "")),
    ("GIA-C04", ("combined", "5 %", "sub", "top", 138, "0.206 / .316 / .316 (Supplementary Table S1)", "")),
    ("GIA-C05", ("combined", "10 %", "ctx", "top", 277, M + "0.053 / .423 / .423 (Supplementary Table S1)", "")),
    ("GIA-C06", ("combined", "10 %", "sub", "top", 277, "0.449 / .154 / .316 (Supplementary Table S1)", "")),
    ("GIA-C07", ("up-only", "1 %", "ctx", "top_pos", 14, M + "0.095 / .35 / .340 (Supplementary Table S2)", M + "0.0951 / .305")),
    ("GIA-C08", ("up-only", "1 %", "sub", "top_pos", 14, M + "0.486 / .131 / .393 (Supplementary Table S2)", "")),
    ("GIA-C09", ("up-only", "5 %", "ctx", "top_pos", 71, "0.092 / .340 / .340 (Supplementary Table S2)", "")),
    ("GIA-C10", ("up-only", "5 %", "sub", "top_pos", 71, "0.037 / .476 / .476 (Supplementary Table S2)", "")),
    ("GIA-C11", ("up-only", "10 %", "ctx", "top_pos", 143, M + "0.093 / .416 / .340 (Supplementary Table S2)", M + "0.1325 / .25")),
    ("GIA-C12", ("up-only", "10 %", "sub", "top_pos", 143, "0.449 / .154 / .476 (Supplementary Table S2)", M + "0.0936 / .416")),
    ("GIA-C13", ("down-only", "1 %", "ctx", "top_neg", 13, "0.238 / .316 / .498 (Supplementary Table S3)", "")),
    ("GIA-C14", ("down-only", "1 %", "sub", "top_neg", 13, "0.280 / .271 / .442 (Supplementary Table S3)", "")),
    ("GIA-C15", ("down-only", "5 %", "ctx", "top_neg", 66, "0.082 / .411 / .498 (Supplementary Table S3)", "")),
    ("GIA-C16", ("down-only", "5 %", "sub", "top_neg", 66, M + "0.056 / .442 / .442 (Supplementary Table S3)", "")),
    ("GIA-C17", ("down-only", "10 %", "ctx", "top_neg", 133, "0.001 / .498 / .498 (Supplementary Table S3)", "")),
    ("GIA-C18", ("down-only", "10 %", "sub", "top_neg", 133, M + "0.093 / .425 / .442 (Supplementary Table S3)", "")),
])
GIA_R2 = {"GIA-C01": M + ".1505", "GIA-C03": ".4125", "GIA-C05": M + ".0534"}


def gia_set(scheme, thr, lst, m):
    if scheme == "combined":
        rule = ("combined scheme: the top round(n x thr) ASD TWAS genes of either sign by S-MultiXcan p (n = 2,767 ASD TWAS genes in "
                "AHBA ∩ HPA); weights = TWAS z (signed weighted mean sum(z e) / sum(z))")
    elif scheme == "up-only":
        rule = "up-only scheme: the top floor(n_pos x thr) genes within z > 0 (n_pos = 1,435), ranked by S-MultiXcan p"
    else:
        rule = "down-only scheme: the top floor(n_neg x thr) genes within z < 0 (n_neg = 1,331), ranked by S-MultiXcan p"
    return ("%s, thr %s: repo_e045bc5/results/ASD/ASD_%s_genes_thr_*.tsv (the %s file; m = %d); HGNC symbols (gene_name); source 1 "
            "(the paper's own list); external (GWAS -> TWAS), not selected on imaging; %s" % (rule, thr, lst, thr, m, GIA_POOL))


GIA_SHIPPED_CMP = {  # register 2.3 (v4): where the supplement row carries another cell's value, the 4.1 comparator is the shipped value
    "GIA-C11": (M + ".1325", "Table S2's " + M + ".093 is the shipped subcortical up-only 10 % value"),
    "GIA-C12": (M + ".0936", "Table S2's .449 is the combined subcortical 10 % value"),
}


def pn_reading(m, sub):
    """register section 1.1 (v4): the published-null readings with amendment 5 section 3's labels for set size and class."""
    det, pw = [], ["power not measured in this class (%s; amendment 5 sections 3, 4.3)"
                   % ("single-class V-DK subcortex" if sub else "dk-ctx")]
    if m < 25:
        det.append("set size")
        pw.append("power not measured at this set size (m < 25)")
    elif m > 100:
        pw.append("power not measured at this set size (m > 100)")
    if sub:
        det.append("class")
    det_txt = ("with the label 'calibration extrapolated (%s)'" % " / ".join(det)) if det else \
        "with no extrapolation label (25 <= m <= 1,000 in the planted class dk-ctx)"
    return ("Published-null reading (section 1.1): 'detectable by the verdict (the published analysis reported none)', %s; or 'not "
            "detectable at this power (as published)', with the label%s '%s'; by the paper's m = %d (the S-build's m governs)%s."
            % (det_txt, "s" if len(pw) > 1 else "", "' and '".join(pw), m,
               "; resolution-limited by construction, reported as such" if sub else ""))


def gia_row(cid, info):
    scheme, thr, comp, lst, m, pub, shipped = info
    ctx = comp == "ctx"
    pub_txt = "rho / p_spin / FDR = " + pub + (("; shipped result file %s (recorded; the supplement value is registered; %s, register 2.3)"
                                                % (shipped, "the 4.1 comparator is the shipped value" if cid in GIA_SHIPPED_CMP
                                                   else "Q4")) if shipped else "") + "; " + GIA_LOC
    common = dict(map=GIA_Y_CTX if ctx else GIA_Y_SUB, analysis_class="dk-ctx" if ctx else "V-DK-subcortex",
                  route=GIA_ROUTE_CTX if ctx else GIA_ROUTE_SUB, inference_level=GIA_LVL_CTX if ctx else GIA_LVL_SUB,
                  set_S=gia_set(scheme, thr, lst, m), published_value_and_location=pub_txt, cell_class="published-null",
                  direction="two-sided (published-null cell, section 1.1)")
    if scheme == "combined":
        rep = ("4.1 check (section 1.5: the paper's own functional recomputed on our matrix): Spearman rho of y with the TWAS-z-weighted "
               "GEDAR score (sum(z e) / sum(z)) on our matrix vs the published rho %s (+-.05); beside it the eda33ab map's rho (R2: %s, "
               "register section 0 item 2)" % (pub.split(" / ")[0], GIA_R2[cid])) if ctx else GIA_SUB_DEFECT
        add(T3, cid, claim_form="set-vs-map",
            T=("not testable as stated (section 1.4: a signed-weight set score). Descriptors (register 2.3): the paper's weighted GEDAR map "
               "(eda33ab version) rho with y; our class-stratified site leg on rho; G1-G5 and J1 with S's weights carried over (each null "
               "set receives S's weight vector in a random order)"),
            status="not testable as stated: signed-weight set score (sum(z e) / sum(z); the sign of sum(z) can flip the map) (register 2.3)",
            headline_population="out: published-null cell (section 1.1; also not testable as stated)",
            reproduction=rep,
            notes=("id: register. Combined-scheme cell, delivered as descriptors only (section 1.4)."
                   + ("" if ctx else " Subcortical: V-DK subcortex, single class; the paper's rho was computed on misaligned structures.")),
            **common)
    else:
        cmp_pub = pub.split(" / ")[0]
        flag = ""
        if cid in GIA_SHIPPED_CMP:
            cmp_pub, why = GIA_SHIPPED_CMP[cid]
            flag = " (the shipped value), flagged 'supplement row carries another cell's value' (%s; register 2.3)" % why
        if ctx:
            status = "auditable (under G2)"
            rep = ("4.1 check (section 1.5: the paper's own functional recomputed on our matrix -- Giacomel: rho of the |z|-weighted GEDAR "
                   "score): Spearman rho of y with the |z|-weighted GEDAR score (sum(|z| e) / sum(|z|)) on our matrix vs %s%s (+-.05)"
                   % (cmp_pub if flag else "the published rho " + cmp_pub, flag))
        else:
            status = ("resolution-limited: by construction (G6s: rank 6 -> 64 patterns -> floor 2/65 ~ .031 >= .025, two-sided); "
                      "reported as resolution-limited (register 2.3); otherwise auditable (under G2)")
            rep = GIA_SUB_DEFECT + ("; the 4.1 comparator is %s%s" % (cmp_pub, flag) if flag else "")
        add(T3, cid, claim_form="set-vs-map",
            T=("set-vs-map (section 1.4): T = Pearson r(y, unweighted set score) -- declared deviation from the paper's |z|-weighted mean "
               "(the weights are all positive); Level 0 = parametric p of r; Spearman beside it; full verdict legs"),
            status=status, headline_population=HL_PN, reproduction=rep, verdict_counted_in_m="yes",
            notes=("id: register. " + pn_reading(m, not ctx)
                   + (" Recorded, not registered (section 1.1): the shipped result files' unreported 0.5 % and 0.1 % cells (e.g. up-only "
                      "subcortical 0.1 %, a one-gene 'set'; draft section 3) -- not the paper's factorial." if cid == "GIA-C07" else "")),
            **common)


# register 2.3 lists C07-C18 first, then C01-C06 and C19-C24
for cid in ["GIA-C%02d" % i for i in range(7, 19)] + ["GIA-C%02d" % i for i in range(1, 7)]:
    gia_row(cid, GIA_CELLS[cid])
for i, (thr, comp, m) in zip(range(19, 25), [("1 %", "ctx", 36), ("1 %", "sub", 36), ("5 %", "ctx", 180), ("5 %", "sub", 180),
                                              ("10 %", "ctx", 360), ("10 %", "sub", 360)]):
    ctx = comp == "ctx"
    add(T3, "GIA-C%02d" % i, cell_class="published-null", claim_form="set-vs-map",
        map=GIA_Y_CTX if ctx else GIA_Y_SUB, analysis_class="dk-ctx" if ctx else "V-DK-subcortex",
        route=GIA_ROUTE_CTX if ctx else GIA_ROUTE_SUB, inference_level=GIA_LVL_CTX if ctx else GIA_LVL_SUB,
        set_S=("post-mortem DEG set: Sadeghi 2022 Supplementary_Data1 (mmc2.xlsx), Dx = ASD (20,256 rows) ∩ AHBA ∩ HPA = 3,599 genes, "
               "top round(n x thr) by p.value, thr %s -> m = %d; weights = logFC (signed weighted mean sum(logFC e) / sum(logFC)); "
               "section 1.6 source 2 (the primary publication the paper cites), rebuilt with the paper's code literature_gwas_analysis.R "
               "('S re-derived'); external (post-mortem transcriptomics)" % (thr, m)),
        T=("not testable as stated (section 1.4: a signed-weight set score). Descriptors (register 2.3): the weighted GEDAR map rebuilt "
           "with the paper's code literature_gwas_analysis.R on the authors' AHBA matrix (labelled 'rebuilt from the paper's code'), its "
           "rho with y; our class-stratified site leg on rho; G1-G5 and J1 with S's weights carried over"),
        direction="two-sided (published-null; no value reported)",
        status="not testable as stated: signed-weight set score (register 2.3)",
        headline_population="out: published-null cell (section 1.1; also not testable as stated)",
        reproduction=("descriptive (amendment 4 section 2): no numeric published value ('n.s.' only); the rebuilt map's rho with y reported"
                      if ctx else GIA_SUB_DEFECT + "; no numeric published value ('n.s.' only)"),
        published_value_and_location=("'n.s.' only: 'No significant associations were found for ASD, BD, or SCZ (Fig. 6)' (Results 'GEDAR "
                                      "maps based on empirical differentially expressed genes...'; Fig. 6 heatmap; not tabulated; the "
                                      "ASD result files are not shipped)"),
        notes="id: register. Post-mortem-DEG cell (secondary analysis), delivered as descriptors only.")
for cid, thr, rho, p in [("GIA-MDD-C1", "1 %", ".531", ".003"), ("GIA-MDD-C5", "5 %", ".547", ".003"), ("GIA-MDD-C10", "10 %", ".529", ".005")]:
    add(T3, cid, cell_class="non-ASD-outcome", claim_form="set-vs-map", map=GIA_Y_MDD, analysis_class="dk-ctx",
        route=GIA_ROUTE_CTX, inference_level=GIA_LVL_CTX,
        set_S=("MDD combined scheme at thr %s: %s (register 2.3); the MDD TWAS genes of either sign, weights = TWAS z; source 1 "
               "(the paper's own list)" % (thr, gia_path("e045bc5", "results/MDD/MDD_top_genes_thr_%s.tsv" % thr.split()[0]))),
        T=("not testable as stated (section 1.4: a signed-weight set score); prereg section 8's question 'does it survive G1-G5 and J1' "
           "answered by descriptor legs with S's weights carried over, plus the class-stratified site leg on rho, on the eda33ab MDD "
           "GEDAR map at thr %s: %s (register 2.3)" % (thr, gia_path("eda33ab", "results/MDD/MDD_TPRS_thr_%s.tsv" % thr.split()[0]))),
        direction="+ (published rho > 0; one-sided per section 1.4 for the descriptor legs)",
        status="not testable as stated: signed-weight set score (register 2.3)",
        headline_population="out: non-ASD registered outcome (prereg section 8; section 1.1; also not testable as stated)",
        reproduction=("4.1 check (section 1.5: the paper's own functional recomputed on our matrix): Spearman rho of the MDD map with the "
                      "TWAS-z-weighted GEDAR score on our matrix vs %s (+-.05); beside it R2's eda33ab-map values .5287 / .5466 / .5310 "
                      "(1 / 5 / 10 %%; a labelling swap against Table S1 at 1 %% and 10 %%, recorded in register 2.3)" % rho),
        published_value_and_location=("rho %s, p_spin %s (Supplementary Table S1, MDD rows; read by the orchestrator, register section "
                                      "0 item 1)" % (rho, p)),
        dependencies="MDD map shared by every GIA-MDD cell; nested thresholds",
        notes=("id: register (register 2.3: the combined MDD cells carry ids GIA-MDD-C1 / C5 / C10). Prereg section 8 registered outcome; "
               "delivered as descriptors. The MDD GEDAR-map file at eda33ab is the MDD counterpart of the ASD maps "
               "results/ASD/ASD_TPRS_thr_*.tsv (draft section 1 row 6), asserted present before the freeze (register section 1.11 "
               "item 7; register_maps/gia_mdd_paths.json)."))
for cid, scheme, thr, fname, rho, p, fdr, sign in [
        ("GIA-MDD-U1", "up-only", "1 %", "results/MDD/MDD_top_pos_genes_thr_1.tsv", ".396", ".031", ".093", "+"),
        ("GIA-MDD-D10", "down-only", "10 %", "results/MDD/MDD_top_neg_genes_thr_10.tsv", M + ".424", ".017", ".051", M)]:
    add(T3, cid, cell_class="non-ASD-outcome", claim_form="set-vs-map", map=GIA_Y_MDD, analysis_class="dk-ctx",
        route=GIA_ROUTE_CTX, inference_level=GIA_LVL_CTX,
        set_S=("MDD %s scheme at thr %s: %s (register 2.3; as the ASD files); source 1 (the paper's own list); size reported "
               "at the S-build under G2; unweighted in T" % (scheme, thr, gia_path("e045bc5", fname))),
        T=T_SVM.replace("T = Pearson r(y, set score)", "T = Pearson r(y, unweighted set score) (the deviation declared for C07-C18)"),
        direction="%s (register 2.3: direction + / %s for U1 / D10)" % (sign, M),
        status="auditable (under G2)",
        headline_population="out: non-ASD registered outcome (prereg section 8; section 1.1)",
        reproduction=("4.1 check (section 1.5: the paper's own functional recomputed on our matrix): Spearman rho of the MDD map with the "
                      "|z|-weighted GEDAR score on our matrix vs %s (+-.05)" % rho),
        published_value_and_location="rho %s, p_spin %s, FDR %s (Supplementary Tables S2 / S3, MDD rows; cortical)" % (rho, p, fdr),
        verdict_counted_in_m="yes", dependencies="MDD map shared by every GIA-MDD cell",
        notes="id: register. Non-ASD outcome, reported apart from every ASD count (section 1.1).")
GIA_DEG_SETS = [
    ("MDDset", "the MDD post-mortem DEG set: Sadeghi 2022 Supplementary_Data1, Dx = MDD, ∩ AHBA ∩ HPA, top round(n x thr) by "
               "p.value, thr %s; weights = logFC; rebuilt with the paper's code literature_gwas_analysis.R (section 1.6 source 2, 'S "
               "re-derived') -- the pairing the paper describes"),
    ("ASDset", "the ASD-DEG set (as GIA-C19-C24, thr %s) whose GEDAR map literature_gwas_analysis.R writes into "
               "MDD_literature_TPRS_thr_*.tsv (gw_asd) -- reproducing the flagged code defect; rebuilt with the paper's code"),
]
for tag, stext in GIA_DEG_SETS:
    for thr, tt in [("1 %", "01"), ("5 %", "05"), ("10 %", "10")]:
        for comp in ("ctx", "sub"):
            ctx = comp == "ctx"
            add(T3, "GIA-MDD-DEG-%s-%s-%s" % (tag, tt, comp), cell_class="descriptor", claim_form="set-vs-map",
                map=GIA_Y_MDD if ctx else GIA_Y_MDD_SUB, analysis_class="dk-ctx" if ctx else "V-DK-subcortex",
                route=GIA_ROUTE_CTX if ctx else GIA_ROUTE_SUB, inference_level=GIA_LVL_CTX if ctx else GIA_LVL_SUB,
                set_S=stext % thr,
                T=("descriptor (register 2.3): the weighted GEDAR map's rho with the MDD map, the class-stratified site leg on rho, G1-G5 "
                   "and J1 with S's weights carried over (signed-weight form, not a claim)"),
                direction="two-sided (the paper's value is in the Fig. 6 heatmap only)",
                status="auditable (descriptor; under G2)",
                headline_population="out: descriptor cell of a non-ASD outcome (section 1.1)",
                reproduction=("descriptive (amendment 4 section 2): Fig. 6 value (heatmap only; not tabulated)" if ctx else GIA_SUB_DEFECT),
                published_value_and_location=("'yielded significant associations only for MDD' (Results 'GEDAR maps based on empirical "
                                              "differentially expressed genes...'; Fig. 6 heatmap; not tabulated)"),
                dependencies="MDD map shared by every GIA-MDD cell; the MDD-DEG and ASD-DEG cells of one threshold share the map",
                notes=("id: compiler (register 2.3: descriptor cells for every threshold (1, 5, 10 %) x compartment (cortical, "
                       "subcortical) with the MDD-DEG set and again with the ASD-DEG set, 12 cells)."))
add(T3, "GIA-X1", cell_class="published-null", claim_form="other", map=GIA_Y_CTX, analysis_class="dk-ctx", route=GIA_ROUTE_CTX,
    set_S="H-MAGMA dysregulation score / gene list for ASD (unpublished: not in the repo or the supplement)",
    T="none registered: not auditable (list and ASD value unpublished; register 2.3)",
    direction="two-sided (published-null)",
    inference_level="other: unstated (register 2.3)",
    status="not auditable: list and ASD value unpublished (register 2.3)",
    headline_population=HL_PN,
    reproduction="descriptive (amendment 4 section 2): no ASD value reported (not run: not auditable)",
    published_value_and_location="Supplement 'Preliminary analyses with H-MAGMA': 'only one MDD showed significant correlation' (ASD value not reported)",
    notes="id: draft (GIA-X1). Read as a published-null ASD cell (only MDD significant). GIA-X2, GIA-X3 out of scope (not registered).")

# ====================================================================================================================
# target 4 -- Romero-Garcia 2019
# ====================================================================================================================
RG_CARRIERS = ("MOESM1 / MOESM2 docx, the Apollo record's SI .txt or Figures_Tables.zip (opened under G1)")
RG_APOLLO_CARRIERS = ["RomeroGarcia_etal_2017_R1_SI_clean.docx", "RomeroGarcia_etal_2017_R1_SI_clean.docx.txt", "Figures_Tables.zip"]
ID_NOTE_RG = ("carriers' " + ident("romerogarcia2019synaptic", "MOESM1") + "; " + ident("romerogarcia2019synaptic", "MOESM2").split(": ", 1)[1]
              + "; MOESM3 (PLS1 weights): " + ident("romerogarcia2019synaptic", "MOESM3").split(": ", 1)[1] + "; Apollo record "
              "10.17863/CAM.17116: " + ident("romerogarcia2019synaptic", "Apollo record", RG_APOLLO_CARRIERS).split(": ", 1)[1]
              + "; " + ID_RULE)
RG_Y = {
    "D": ("discovery DeltaCT (ABIDE I: 62 ASD / 87 TD, male, 9-11 y; mean CT(ASD) - mean CT(TD) per region; DK-308, 152 lh + 156 rh, "
          "cortex only) from a DK-308 DeltaCT table with region labels (the 152 left labels required, register section 1.11 item 8) in "
          + RG_CARRIERS + "; PLS1 weights: MOESM3 sheet "
          "'Discovery' (41380_2018_23_MOESM3_ESM.xlsx, 2,128,249 B); " + ID_NOTE_RG),
    "V1": ("Validation 1 DeltaCT (ABIDE II Georgetown: 48 ASD / 54 TD; DK-308, cortex only) from a DK-308 table with labels (the 152 left labels "
           "required, register section 1.11 item 8) in " + RG_CARRIERS + " (searched separately); PLS1 weights: MOESM3 sheet 'Validation1_GU'; " + ID_NOTE_RG),
    "V2": ("Validation 2 DeltaCT (ABIDE II Kennedy Krieger: 56 ASD / 154 TD; DK-308, cortex only) from a DK-308 table with labels "
           "(the 152 left labels required, register section 1.11 item 8) in " + RG_CARRIERS + " (searched separately); PLS1 weights: MOESM3 sheet 'Validation2_KKI'; " + ID_NOTE_RG),
}
_RGC = CARRIER["targets"]["romerogarcia2019synaptic"]
if len(_RGC["required_labels"]) != 152 or _RGC["required_count"] != 152:
    die("carrier_tests.json: Romero-Garcia must require the 152 left DK-308 labels (register section 1.11 item 8)")
RG_CARRIER_TEST = carrier_note(
    "for each map it needs (discovery; Validation 1 and Validation 2 searched separately), a table in a G1 carrier holding the "
    "152 LEFT DK-308 labels (lh; the route uses only the left hemisphere, section 1.7), each once with a numeric DeltaCT value; a "
    "left-only carrier qualifies, right-hemisphere labels are neither required nor checked (register section 1.11 item 8); "
    "required count 152 per map; label list = carrier_tests.json targets.romerogarcia2019synaptic.required_labels (the %d lh names of "
    "lh.500.aparc.annot in the paper's subParcellation repository @e351b3cf, sha256 %s, sub-parcel names nesting in their "
    "Desikan-Killiany parent by name prefix, e.g. lh_bankssts_part1); normalisation_dk308; a numeric parse of every value; partial or "
    "figure-only content does not qualify (section 1.8)."
    % (len(_RGC["required_labels"]), _RGC["label_source"]["lh.500.aparc.annot"]["sha256"]))
RG_ROUTE = ("re-parcellated: DK-308 -> dk-ctx (section 1.7): each sub-parcel nests in its Desikan-Killiany parent by name prefix "
            "(lh_bankssts_part1 -> bankssts); DK value = the vertex-count-weighted mean of its sub-parcels, counts from lh.500.aparc.annot "
            "in the paper's subParcellation repository (commit e351b3cf); left hemisphere only")
T4 = Target(4, "romerogarcia2019synaptic", "3", "G1", analysis_class="dk-ctx", route=RG_ROUTE,
            dependencies=("all discovery cells share y and PLS1; validation cells share Val1 / Val2; modules overlap the RG-05 / RG-06 "
                          "lists by construction"))
RG_COND = {k: ("conditional: a G1 carrier (%s) holds the %s DeltaCT on the 152 left DK-308 labels with numeric values (register "
               "2.4, section 1.11 item 8; carrier test in notes)" % (RG_CARRIERS, v))
           for k, v in [("D", "discovery"), ("V1", "Validation 1"), ("V2", "Validation 2"),
                        ("D+V1+V2", "discovery, Validation 1 and Validation 2"), ("V1+V2", "Validation 1 and Validation 2")]}
RG_NTAS_STATUS = ("not testable as stated: the paper pools both signs ('the sign of a weight was not informative'), whatever the "
                  "carrier holds (register 2.4); its descriptors are conditional on the carrier (section 1.8: every flag reported)")
RG_T_POOLED = ("not testable as stated (section 1.4: pooled-sign list); descriptors if the map is found (register 2.4): signed T "
               "(mean PLS1 weight of S, PLS-enrichment form, two-sided) and T_abs (mean over S of |per-gene r|, upper tail)")
RG_T_DEPL = ("not testable as stated (section 1.4: a depletion of an unsigned list); descriptors if the map is found: signed T (mean "
             "PLS1 weight of S, two-sided) and T_abs (lower tail: stated depletion)")
RG_REP = ("descriptive (amendment 4 section 2): the list re-derived by the paper's rule (PLS1 bootstrap-z with FDR inverse-quantile "
          "correction, q < .05, both signs) then its enrichment test (logistic regression with a gene-length covariate; Enrichr for "
          "GO / KEGG); OR, p and Jaccard vs %s (run only if the map is found)")
LVL_RG_STRUCT = "gene null only (structured: gene-length covariate) (register 2.4) [draft reading 'none' recorded]"
LVL_RG_UNIF = "gene null only (uniform; Enrichr) (register 2.4) [draft reading 'none' recorded]"
LVL_RG_PERM = ("other: non-spatial permutation (10,000 permutations of the variance explained; no spatial preservation named) "
               "(register 2.4) [draft reading 'none' recorded]")
LVL_RG_RANK = "none: ranking only, no test (section 1.3; draft 2.2)"
LVL_RG_V26 = "other: unstated (register 2.4)"

for cid, key, pub, rep in [
        ("RG-01", "D", ("PLS1 variance explained above chance: P = 0.009 (10,000 permutations); r(DeltaCT, PLS1 score) = 0.32, P = 4.15e-9; "
                        "components 3, 4, 6 n.s. (P .303 / .693 / .394) (Results 'PLSR analyses and characterization' para 1; Fig. 3g; "
                        "% variance in Supp Fig. S1)"),
         "4.1 check (section 1.5, register 2.4): r(PLS1 score, y) on our matrix vs the published r = .32 (+-.05)"),
        ("RG-V01", "V1", ("'only the first component ... (P < 10^-14, 10,000 permutations) ... explained a significant amount of the "
                          "variance' (Results 'Validation' para 2; Supp Fig. S2); r(DeltaCT, score) in Fig. 3h"),
         "4.1 check (section 1.5, as RG-01): r(PLS1 score, Val1 DeltaCT) vs the Fig. 3h value (read under G1)"),
        ("RG-V02", "V2", "same sentence (P < 10^-14; Supp Fig. S2); r(DeltaCT, score) in Fig. 3i",
         "4.1 check (section 1.5, as RG-01): r(PLS1 score, Val2 DeltaCT) vs the Fig. 3i value (read under G1)")]:
    add(T4, cid, cell_class="claim", claim_form="component", map=RG_Y[key],
        set_S="none (component claim); X = the section 3.1 matrix of the analysis class (the paper: whole-genome AHBA, 20,737 genes)",
        T=T_COMP_PLS1, direction="+ (upper tail: variance explained above the null)", inference_level=LVL_RG_PERM,
        status=RG_COND[key], headline_population=HL_IN_COMP,
        reproduction=rep, published_value_and_location=pub, verdict_counted_in_m="yes",
        notes="id: register. Component level; precedes the focal RG-06 but has no full-verdict form (section 1.2)." + RG_CARRIER_TEST)

RG_ENRICHR = ("Enrichr GO_Biological_Process_2015 library: the release the paper used -- the paper names Enrichr, version unstated; "
              "of the Enrichr GO BP libraries 2013, 2015, 2017, 2017b and 2018 (all obtained 2026-09-26) only 2015 names every GO BP "
              "term the paper prints under the name rule (section 1.6 R12, register section 1.11); section 1.6 source 3, 'S re-derived' "
              "(no 'release substituted'); S = the library's gene list for the term (Enrichr's own set; the 1.6 GO annotation rule "
              "does not apply to a library set); the term reached by the name rule of sections 1.1 / 1.6")
# register v6.1 Q1 / Q2 (orchestrator under the operator's standing delegation): the RG families' source-1 branch and KEGG release
RG_KEGG_FAM = ("per cell, S = the list the carrier presents as that pathway's input membership (source 1, by the section 1.6 source-1 "
               "criterion); else the gene list of the pathway the printed name reaches by the name rule in the Enrichr KEGG library "
               "chosen by section 1.6 (v6.2 P5: of KEGG_2015 and KEGG_2016, both served while the paper's GO_Biological_Process_2015 "
               "was current, the one reaching every pathway name of the gated table; both -> KEGG_2015; neither -> the one reaching "
               "more; a tie -> KEGG_2015); a name reached by neither -> that cell 'not auditable (S undefined)'; not auditable if the "
               "gated table naming the cells is absent or no name reaches the KEGG library chosen by section 1.6 (provisional, "
               "section 1.8)")
RG_SECOND_LIST = ("not auditable (S undefined: source 1 uncorroborated; v6.5): the list's identity is given only in the supplement, "
                  "no external definition is pinned and the paper prints no size, so no list the supplement holds could be "
                  "corroborated (section 1.6; v6-v6.4: S from the supplement by the source-1 criterion, provisionally)")
RG_DISC = [
    ("RG-02", "GO BP 'Synaptic Transmission' (" + RG_ENRICHR + ")",
     "P_corrected = 0.00006 ('Only the GO term Synaptic Transmission in component 1 (PLSR1) survived FDR correction'; Results para 1)",
     LVL_RG_UNIF, "pooled", "published P_corr (Enrichr)"),
    ("RG-03", "FAMILY: 11 KEGG pathways named in Table S2 (sealed-mixed until G1); " + RG_KEGG_FAM,
     "'PLSR1 was also significantly enriched for 11 pathways (Table S2) in the Kyoto Encyclopedia of Genes and Genomes (KEGG)' (Results para 1)",
     LVL_RG_UNIF, "pooled", "Table S2"),
    ("RG-04", "neuron-specific genes: top 500 by specificity among 5 classes, Zhang et al. 2014 (ref 40; mouse cortex RNA-seq; orthologue mapping "
              "unstated); section 1.6 source 2 ('S re-derived')",
     "OR = 1.1, P_corrected = 3.19 x 10^-12, Bonferroni over 5 classes (Results para 2)", LVL_RG_STRUCT, "pooled", "OR 1.10"),
    ("RG-05", "ASD-dysregulated genes, Parikshak 2016 (ref 28), n = 1,143 as stated (584 up + 558 down = 1,142, draft O13); section 1.6 "
              "source 2 (size of the pinned list reported beside the paper's)",
     "OR = 1.21 (CI 1.19-1.23), P 1.76e-15, P_corr 2.81e-15 (Table 2; Results 'Gene enrichment analyses' para 1; the abstract says OR 1.11)",
     LVL_RG_STRUCT, "pooled", "OR 1.21 (Table 2)"),
    ("RG-06", "ASD-downregulated genes, Parikshak 2016, n = 558; section 1.6 source 2",
     "OR = 1.87 (CI 1.80-1.94), P 2.00e-16, P_corr 3.55e-16 ('driven entirely by genes downregulated in autism cortex'; Results 'Gene "
     "enrichment analyses' para 1; Table 2) -- the paper's headline claim", LVL_RG_STRUCT, "pooled", "OR 1.87 (Table 2)"),
    ("RG-07", "adult module M4, Parikshak 2016 module assignments (their supplementary table; section 1.6 pinned)",
     "OR 1.08 (1.07-1.08), P_corr 3.55e-16 ('enriched for all three downregulated modules'; Fig. 3j; Table 2; Table S6)", LVL_RG_STRUCT,
     "pooled", "OR 1.08 (Table 2)"),
    ("RG-08", "adult module M10, Parikshak 2016 (section 1.6 pinned)", "OR 1.07 (1.07-1.08), P_corr 3.55e-16 (Table 2; Fig. 3j)",
     LVL_RG_STRUCT, "pooled", "OR 1.07 (Table 2)"),
    ("RG-09", "adult module M16, Parikshak 2016 (section 1.6 pinned)", "OR 1.08 (1.07-1.08), P_corr 3.55e-16 (Table 2; Fig. 3j)",
     LVL_RG_STRUCT, "pooled", "OR 1.08 (Table 2)"),
    ("RG-10", "fetal module Mdev13, Parikshak 2013 (ref 31); section 1.6 source 2",
     "OR 1.04 (1.04-1.04), P_corr 3.55e-16 (Table 2; para 3; the text says 'adult', Table 2 = fetal Mdev13/16/17)", LVL_RG_STRUCT,
     "pooled", "OR 1.04 (Table 2)"),
    ("RG-11", "fetal module Mdev16, Parikshak 2013; section 1.6 source 2", "OR 1.06 (1.05-1.06), P_corr 3.55e-16 (Table 2)",
     LVL_RG_STRUCT, "pooled", "OR 1.06 (Table 2)"),
    ("RG-12", "fetal module Mdev17, Parikshak 2013; section 1.6 source 2", "OR 1.04 (1.04-1.05), P_corr 3.55e-16 (Table 2)",
     LVL_RG_STRUCT, "pooled", "OR 1.04 (Table 2)"),
    ("RG-13", "fetal module Mdev2 (rare-variant enriched), Parikshak 2013; section 1.6 source 2",
     "OR 0.97 (0.96-0.97), P_corr 1.70e-11 ('fewer PLSR1 genes than expected by chance'; para 3)", LVL_RG_STRUCT, "depletion",
     "OR 0.97 (Table 2)"),
    ("RG-14", "fetal module Mdev3, Parikshak 2013; section 1.6 source 2",
     "OR 0.96 (0.96-0.97), P_corr 3.55e-16 (Table 2; para 3)", LVL_RG_STRUCT, "depletion", "OR 0.96 (Table 2)"),
    ("RG-15", "FAMILY: 'a second list of genes dysregulated in autism identified using a partially overlapping cortical gene expression data "
              "set' (identity only in the supplement; Table S6 sealed-mixed until G1); " + RG_SECOND_LIST,
     "Table S6 (unread); Methods 'Overview'", LVL_RG_STRUCT, "pooled", "Table S6"),
]
for cid, S, pub, lvl, kind, cmp in RG_DISC:
    fam = cid in ("RG-03", "RG-15")
    focal = cid == "RG-06"
    add(T4, cid, cell_class="family" if fam else "claim", claim_form="PLS-enrichment", map=RG_Y["D"], set_S=S,
        T=RG_T_DEPL if kind == "depletion" else RG_T_POOLED,
        direction=("two-sided for the signed descriptor (unsigned list); T_abs lower tail (stated depletion)" if kind == "depletion"
                   else "two-sided for the signed descriptor (the paper's list is unsigned); T_abs upper tail"),
        inference_level=lvl, status=RG_NTAS_STATUS + ("; also a depletion of an unsigned list (section 1.4)" if kind == "depletion" else ""),
        headline_population=HL_NTAS + (HL_FAMILY if fam else ""), reproduction=RG_REP % cmp, published_value_and_location=pub,
        focal="yes" if focal else "no",
        n_cells=("11" if cid == "RG-03" else ("UNDETERMINED: the second list's cells in Table S6 (>= 1), fixed when the table is read "
                                              "under G1; the family counts once (section 1.1)" if cid == "RG-15" else "1")),
        notes=("id: register." + (" Family (one registered unit, counts once; section 1.1) with S from the supplement if found (register 2.4)."
                                  if fam else "")
               + (" Per-row focal of frozen-11 row 3 (register 2.4, section 4: the headline finding, a PLS-enrichment form; its status is "
                  "'not testable as stated')." if focal else "") + RG_CARRIER_TEST))

RG_VAL = [
    ("RG-V03", "V1", "GO BP 'Synaptic transmission' (" + RG_ENRICHR + "; as RG-02)", "P_corrected = 1 x 10^-4 (Validation 1)",
     LVL_RG_UNIF, "RG-02"),
    ("RG-V04", "V2", "GO BP 'Synaptic transmission' (" + RG_ENRICHR + "; as RG-02)", "P_corrected = 1 x 10^-4 (Validation 2)",
     LVL_RG_UNIF, "RG-02"),
    ("RG-V05", "V2", "GO BP 'Membrane depolarization' (" + RG_ENRICHR + "; new S)", "P_corrected = 7 x 10^-4 (Validation 2)",
     LVL_RG_UNIF, "new S"),
    ("RG-V06", "V1", "FAMILY: Validation 1 KEGG pathways named in Supplementary Table S3 (sealed-mixed until G1); " + RG_KEGG_FAM,
     "Supplementary Table S3 (names unread)", LVL_RG_UNIF, "RG-03"),
    ("RG-V07", "V2", "FAMILY: Validation 2 KEGG pathways named in Supplementary Table S4 (sealed-mixed until G1); " + RG_KEGG_FAM,
     "Supplementary Table S4 (names unread)", LVL_RG_UNIF, "RG-03"),
    ("RG-V08", "V1", "as RG-04: neuron-specific genes (Zhang 2014 top 500)", "OR = 1.13; P = 2.01 x 10^-7 (Validation 1)", LVL_RG_STRUCT,
     "RG-04"),
    ("RG-V09", "V2", "as RG-04: neuron-specific genes (Zhang 2014 top 500)", "OR = 1.06; P = 0.009 (Validation 2)", LVL_RG_STRUCT, "RG-04"),
    ("RG-V10", "V1", "as RG-06: ASD-downregulated genes, Parikshak 2016 (n = 558)",
     "OR = 1.24; P_corrected = 0.004 ('Gene enrichment analyses' (validation) para 1; the abstract says 1.44)", LVL_RG_STRUCT, "RG-06"),
    ("RG-V11", "V2", "as RG-06: ASD-downregulated genes, Parikshak 2016", "OR = 1.3; P_corrected = 0.001", LVL_RG_STRUCT, "RG-06"),
    ("RG-V12", "V1", "as RG-07: adult module M4 (Parikshak 2016)", "Table S6 / Fig. 3k ('enrichment for the three adult gene co-expression "
                     "modules ... in Validation 1')", LVL_RG_STRUCT, "RG-07"),
    ("RG-V13", "V1", "as RG-08: adult module M10 (Parikshak 2016)", "Table S6 / Fig. 3k", LVL_RG_STRUCT, "RG-08"),
    ("RG-V14", "V1", "as RG-09: adult module M16 (Parikshak 2016)", "Table S6 / Fig. 3k", LVL_RG_STRUCT, "RG-09"),
    ("RG-V15", "V2", "as RG-08: adult module M10 (Parikshak 2016)", "Table S6 / Fig. 3l (M4 not replicated in Validation 2; Fig. 3 caption)",
     LVL_RG_STRUCT, "RG-08"),
    ("RG-V16", "V2", "as RG-09: adult module M16 (Parikshak 2016)", "Table S6 / Fig. 3l", LVL_RG_STRUCT, "RG-09"),
    ("RG-V17", "V1", "as RG-10: fetal module Mdev13 (Parikshak 2013)", "Table S6 / Fig. 3k ('replicated ... in both validation datasets')",
     LVL_RG_STRUCT, "RG-10"),
    ("RG-V18", "V1", "as RG-11: fetal module Mdev16", "Table S6 / Fig. 3k", LVL_RG_STRUCT, "RG-11"),
    ("RG-V19", "V1", "as RG-12: fetal module Mdev17", "Table S6 / Fig. 3k", LVL_RG_STRUCT, "RG-12"),
    ("RG-V20", "V2", "as RG-10: fetal module Mdev13", "Table S6 / Fig. 3l", LVL_RG_STRUCT, "RG-10"),
    ("RG-V21", "V2", "as RG-11: fetal module Mdev16", "Table S6 / Fig. 3l", LVL_RG_STRUCT, "RG-11"),
    ("RG-V22", "V2", "as RG-12: fetal module Mdev17", "Table S6 / Fig. 3l", LVL_RG_STRUCT, "RG-12"),
    ("RG-V23", "V1+V2", "FAMILY: the second dysregulated list (as RG-15) x Validation 1 and Validation 2; " + RG_SECOND_LIST,
     "Table S6 (Methods 'Overview')", LVL_RG_STRUCT, "RG-15"),
]
for cid, key, S, pub, lvl, cp in RG_VAL:
    fam = cid in ("RG-V06", "RG-V07", "RG-V23")
    ymap = RG_Y[key] if key in RG_Y else "Validation 1 and Validation 2 DeltaCT (as RG-V01, RG-V02)"
    add(T4, cid, cell_class="family" if fam else "claim", claim_form="PLS-enrichment", map=ymap, set_S=S, T=RG_T_POOLED,
        direction="two-sided for the signed descriptor (the paper's list is unsigned); T_abs upper tail",
        inference_level=lvl, status=RG_NTAS_STATUS, headline_population=HL_NTAS + (HL_FAMILY if fam else ""),
        reproduction=RG_REP % "the published value", published_value_and_location=pub,
        n_cells=("UNDETERMINED: pathways named in Table S3, fixed when the table is read under G1; the family counts once (section 1.1)"
                 if cid == "RG-V06" else
                 "UNDETERMINED: pathways named in Table S4, fixed when the table is read under G1; the family counts once (section 1.1)"
                 if cid == "RG-V07" else
                 "UNDETERMINED: >= 2 (Validation 1, Validation 2) x the list(s) of Table S6, fixed when the table is read under G1; the "
                 "family counts once (section 1.1)" if cid == "RG-V23" else "1"),
        map_index=(MAPIDX_RGVAL if cid == "RG-V23" else "0"),
        dependencies=("validation cells share Val1 / Val2 and their PLS1; counterpart %s" % cp if cp != "new S" else
                      "shares the Validation 2 map and PLS1 weights"),
        notes=("id: register." + (" Family (one registered unit, counts once; section 1.1) with S from the supplement if found (register 2.4)."
                                  if fam else "") + RG_CARRIER_TEST))
RG_V2425_NA = ("not auditable (definition not applicable): the paper does not state how the weights of its %s datasets are combined "
               "into one ranking%s, so the selected-list re-selection cannot be written without inventing it (register 2.4, v4)")
for cid, key, S, pub, why in [
        ("RG-V24", "D+V1+V2",
         ("the ranking itself: the top 200 genes (~1 %) by PLS1 weight across all three datasets (named: SCN1A, SLIT1, SLIT3); "
          "Supplementary Dataset (MOESM3, mixed) -- selected on the claim maps (amendment 3 section 2)"),
         "'the top 200 genes (approximately 1%) based on their gene weights in PLS1 across all the three datasets (Supplementary Dataset)'",
         RG_V2425_NA % ("three", "")),
        ("RG-V25", "V1+V2",
         ("the ranking itself: the top 1 % in the two validation datasets (named: GABRA3, GABRA5, GABRB1, PTCHD1, SYN2, SYT17); MOESM3 "
          "sheets 2-3 -- selected on the claim maps (amendment 3 section 2)"),
         "'the top 1% in the two validation datasets' (Results, Validation)",
         RG_V2425_NA % ("two", ", and V25's N is unset"))]:
    add(T4, cid, cell_class="claim", claim_form="component",
        map=("discovery, Validation 1 and Validation 2 DeltaCT (all three; as RG-01, RG-V01, RG-V02)" if key == "D+V1+V2"
             else "Validation 1 and Validation 2 DeltaCT (as RG-V01, RG-V02)"),
        set_S=S, T="none registered: " + why,
        direction="n/a: no registered T (not auditable: definition not applicable)",
        inference_level=LVL_RG_RANK, status=why, headline_population=HL_IN_NA + "; component-level",
        reproduction="descriptive (amendment 4 section 2): the published list's genes (not run: not auditable)",
        published_value_and_location=pub,
        dependencies="selected on the claim maps; shares the validation (and, for V24, discovery) maps and PLS1 weights",
        notes=("id: register. v3 registered it as a conditional selected-list component claim counted in m; v4 reads it not auditable "
               "(definition not applicable) and out of m (register 2.4, section 4, section 9 NF7)."))
add(T4, "RG-V26", cell_class="claim", claim_form="other",
    map=("the third validation cohort's DeltaCT -- cohort unidentified (identity in the unread Supplementary section 8 / Fig. S6; "
         "register 2.4)"),
    set_S="none named (a consistency statement on PLS weights)",
    T="none registered: not auditable (cohort unidentified; register 2.4)", direction="n/a: no registered T (not auditable)",
    inference_level=LVL_RG_V26, status="not auditable: cohort unidentified (register 2.4)", headline_population=HL_IN_NA,
    reproduction="descriptive (amendment 4 section 2): 'PLS weights were consistent' (not run: not auditable)",
    published_value_and_location=("'in line with the two original validation datasets and PLS weights were consistent' (Supplementary "
                                  "section 8; Fig. S6, unread)"),
    dependencies="shares the PLS pipeline with RG-01, RG-V01, RG-V02",
    notes="id: register.")

RG_NULLS = [
    ("RG-N01", "ASD-upregulated genes, Parikshak 2016, n = 584 (section 1.6 source 2)", "OR 1.01, P_corr .499 (Table 2; the within-paper "
                                                                                          "contrast of RG-06)"),
    ("RG-N02", "rare de novo variant genes, Sanders 2015 (Neuron), n = 65 (section 1.6 source 2)", "OR 0.96, P_corr .276 (Table 2)"),
    ("RG-N03", "common-variant genes, PGC ASD (5,305 trios) MAGMA (section 1.6 source 2)", "OR 1.00, P_corr .293 (Table 2)"),
    ("RG-N04", "astrocyte-specific genes, Zhang 2014 top 500 (section 1.6 source 2)", "OR 1.00 (Results para 2; cell-type analysis)"),
    ("RG-N05", "oligodendrocyte-specific genes, Zhang 2014 top 500", "OR 0.99 (Results para 2)"),
    ("RG-N06", "microglia-specific genes, Zhang 2014 top 500", "OR 0.97 (Results para 2)"),
    ("RG-N07", "vascular-specific genes, Zhang 2014 top 500", "OR 0.97 (Results para 2)"),
    ("RG-N08", "adult module M9 (upregulated), Parikshak 2016 (section 1.6 pinned)",
     "OR 0.93, P_corr 2.9e-14 (Table 2; the text claims only that 'none of the 3 upregulated modules' was enriched, no depletion)"),
    ("RG-N09", "adult module M19 (upregulated), Parikshak 2016", "OR 0.93, P_corr 3.6e-16 (Table 2)"),
    ("RG-N10", "adult module M20 (upregulated), Parikshak 2016", "OR 0.97, P_corr 7.7e-5 (Table 2)"),
]
for cid, S, pub in RG_NULLS:
    add(T4, cid, cell_class="descriptor", claim_form="PLS-enrichment", map=RG_Y["D"], set_S=S,
        T="descriptor (section 1.1; within-paper null): signed T (mean PLS1 weight of S, two-sided) and T_abs (upper tail), as RG-02 ... RG-15",
        direction="two-sided (descriptor cell)", inference_level=LVL_RG_STRUCT + " (Table 2 row)",
        status="conditional (descriptor): as the claims -- computed if the discovery DeltaCT carrier is found (register 2.4)",
        headline_population=HL_DESC, reproduction=RG_REP % "Table 2", published_value_and_location=pub,
        notes="id: register (register 2.4: within-paper nulls RG-N01 ... N10, conditional as the claims)." + RG_CARRIER_TEST)
add(T4, "RG-N11", cell_class="descriptor", claim_form="component",
    map="ADHD DeltaCT (ABIDE I: 69 ADHD vs the same 87 controls; DK-308; unpublished)",
    set_S="none (component claim)", T="descriptor: " + T_COMP_PLS1 + " (never computed: not auditable)",
    direction="+ (upper tail: R^2 above the null)", inference_level=LVL_RG_PERM + " (as RG-01)",
    status="not auditable: map unpublished (register 2.4)",
    headline_population=HL_DESC, reproduction="descriptive (amendment 4 section 2): 'did not identify any components' (Supp Table S5)",
    published_value_and_location="'PLSR analysis of DeltaCT in ADHD data did not identify any components' (Supp Table S5)",
    notes="id: register (register 2.4: RG-N11, ADHD DeltaCT).")

# ====================================================================================================================
# target 5 -- Berto 2022
# ====================================================================================================================
BE_Y = ("CTL fALFF and ReHo (606 neurotypical subjects, ABIDE I + II pooled; C-PAC 1.8; 11 merged Brodmann regions BA1/2/3/5, BA4/6, "
        "BA7, BA9, BA17, BA20/37, BA24, BA38, BA39/40, BA41/42/22, BA44/45; cortex only): Supp Data 1 (MOESM4_ESM.xlsx, 1,178,014 B) / "
        "repo rawdata (under G1; not downloaded); paired in the paper with controlled PsychENCODE tissue RNA-seq (syn4587615; 302 CTL / "
        "360 ASD samples, 11 areas)")
T5 = Target(5, "berto2022connectivity", "4", "G1", map=BE_Y, analysis_class="none",
            route=("none: no AHBA re-derivation registered (register 2.5; draft Q4 option a); the map exists only on 11 merged Brodmann "
                   "regions (native out-of-class, draft section 2.0)"),
            dependencies="all cells share y and the 415-gene DC list; BE-06 / 07 and BE-12 overlap (Gandal DGE vs modules)")
BE_CODE_NOTE = ("Code-level observation recorded as a note on the paper's inference (register 2.5; code reading only): per-gene statistics "
                "across tissue samples, each paired with a random CTL imaging value for its region (200 draws), ASD tissue paired with CTL "
                "imaging; paired.r with the sample n (302 / 360). PsychENCODE not requested.")
BE_T_NONE = ("none registered: not auditable, no AHBA re-derivation registered (register 2.5, draft Q4 option a); the draft's re-derived "
             "T (mean per-gene r on the 11-BA map) is superseded")
add(T5, "BE-01", cell_class="claim", claim_form="other",
    set_S="none: the 415 differentially correlated genes (DiffCor P < .01 and CTL FDR < .05; Fisher's method over fALFF and ReHo)",
    T="none: not testable as stated (section 1.4: a differential correlation between tissue cohorts)",
    direction="n/a: no registered T (not testable as stated)",
    inference_level="none: parametric Fisher r-to-z / Spearman with BH; no spatial or gene null (register 2.5)",
    status="not testable as stated: differential correlation between tissue cohorts (register 2.5); also needs controlled PsychENCODE expression",
    headline_population=HL_NTAS,
    reproduction="descriptive (amendment 4 section 2): 415 DC genes (not run: not testable as stated; controlled expression)",
    published_value_and_location=("415 DC genes (Diff Cor P < 0.01, CTL FDR < 0.05), 59.8 % positively correlated in CTL (Results "
                                  "'Identification of genes...' para 2; Fig. 3a)"),
    notes="id: register. The paper's headline. " + BE_CODE_NOTE)
for cid, S, pub in [("BE-02", "Wang et al. 2015 (ref 15) fMRI-correlated genes (size not stated; repo GeneSets_fMRI.RData, not downloaded)",
                     "OR = 17.3, FDR = 2.5 x 10^-15 (Results 'Identification of genes...' para 3; Fig. 3d, Supplementary Fig. 5d)"),
                    ("BE-03", "Richiardi et al. 2015 (ref 14) fMRI-correlated genes (size not stated; repo rawdata/Richiardi_science.txt)",
                     "OR = 3.2, FDR = 1.5 x 10^-10 (same sentence; Fig. 3d)")]:
    add(T5, cid, cell_class="not-ASD-claim", claim_form="decoded-list", set_S=S, T=BE_T_NONE,
        direction="two-sided (draft: the tested list mixes signs)",
        inference_level=("gene null only (uniform): Fisher's exact (greater) vs the BrainSpan background (15,585), BH (register 2.5) "
                         "[draft reading 'none' recorded]"),
        status="not auditable: the tested list (genes correlated with CTL fALFF / ReHo in CTL tissue) needs controlled PsychENCODE expression (register 2.5)",
        headline_population=HL_NOTASD,
        reproduction="descriptive (amendment 4 section 2): Fisher's exact OR (not run: not auditable)",
        published_value_and_location=pub, notes="id: register. Neurotypical-side claim (register 2.5: BE-02 ... BE-05 not ASD claims).")
for cid, gene, pub in [("BE-04", "PVALB", "rho = 0.32 (fALFF), 0.38 (ReHo) (Results para 4; Figs 3f-g)"),
                       ("BE-05", "SCN1B", "rho = 0.33 (fALFF), 0.42 (ReHo) (Results para 4; Figs 3f-g)")]:
    add(T5, cid, cell_class="not-ASD-claim", claim_form="other",
        set_S="single gene %s (prereg section 4 single-gene C1 form)" % gene, T=BE_T_NONE,
        direction="+ (draft: positive correlation with CTL fALFF / ReHo)",
        inference_level="none: Spearman on CTL PsychENCODE tissue samples (sample-level pairing) (register 2.5)",
        status="not auditable: controlled PsychENCODE expression (register 2.5)", headline_population=HL_NOTASD,
        reproduction="4.1 check: Spearman rho vs .32 / .38 (%s) (not run: not auditable)" % gene if gene == "PVALB" else
        "4.1 check: Spearman rho vs .33 / .42 (SCN1B) (not run: not auditable)",
        published_value_and_location=pub + "; 'these correlations are affected by ASD status (Fig. 3f)'",
        notes="id: register. Neurotypical side only; PVALB / SCN1B are prereg 'literature favourites' (must not feed discovery).")
BE_LOC = "Results 'Differentially correlated genes have specific developmental trajectories'"
for cid, S, lst, pub in [
        ("BE-06", "ASD-downregulated genes, Gandal 2018 (ref 55) -- section 1.6 pinned: gene-level ASD DE table, ASD FDR < .05 with log2FC < 0",
         "Adult cluster", "Fisher's exact (greater) vs the BrainSpan background (15,585), BH; -log10 FDR bar in Fig. 4d (value unread) (" + BE_LOC + " para 3)"),
        ("BE-07", "ASD-upregulated genes, Gandal 2018 -- section 1.6 pinned: ASD FDR < .05 with log2FC > 0", "EarlyDev cluster",
         "as BE-06; Fig. 4d (" + BE_LOC + " para 3)"),
        ("BE-08", "PVALB interneuron markers, Allen multi-region snRNA-seq (Hodge 2020, ref 41; FindMarkers pct > .5, FDR < .05, |log2FC| > .3); "
                  "section 1.6 source 2", "Adult cluster", "Fisher's exact, BH; Fig. 4c (" + BE_LOC + " para 3)"),
        ("BE-09", "excitatory-neuron markers (Hodge 2020, as BE-08); section 1.6 source 2", "EarlyDev cluster", "Fisher's exact, BH; Fig. 4c"),
        ("BE-10", "GO MF 'steroid binding' (ToppGene; 5-2,000 genes; BH; BrainSpan background); " + GO_RULE, "Adult cluster",
         "ToppGene hypergeometric, BH; Fig. 4b; SD2 (" + BE_LOC + " para 2)"),
        ("BE-11", "FAMILY: GO / KEGG 'transporter activity', 'ion channel activity', 'DNA-binding activity' across clusters (ToppGene)",
         "clusters (not distinct for a single trajectory)", "Fig. 4b; SD2 (" + BE_LOC + " para 2: 'not distinct for a single developmental trajectory')"),
        ("BE-12", "FAMILY: ASD / SCZ / BD co-expression modules (Gandal 2018); S in Supp Fig. 6e (sealed-mixed, unread) -- S undefined",
         "Adult / EarlyDev clusters", "Fisher's exact; Supplementary Fig. 6e ('further confirmed using modules of co-expressed genes')"),
        ("BE-13", "regional ASD-vs-CTL DEGs in PsychENCODE (FDR < .05, |log2FC| > .3), derived from controlled data", "Adult and EarlyDev clusters",
         "Fisher's exact; Fig. 5b (highest enrichment in BA17 and BA7)")]:
    fam = cid in ("BE-11", "BE-12")
    add(T5, cid, cell_class="family" if fam else "claim", claim_form="decoded-list",
        set_S=S + "; tested list: %s of the 415 DC genes (K-means on CTL trajectories; selected on the map with controlled expression)" % lst,
        T=BE_T_NONE, direction="two-sided (draft: no map-sign mapping)",
        inference_level=("gene null only (uniform): Fisher's exact / ToppGene hypergeometric with BH (register 2.5) [draft reading "
                         "'none' recorded]"),
        status="not auditable: the lists need controlled PsychENCODE expression; no AHBA re-derivation registered (register 2.5, Q4 option a)",
        headline_population=HL_IN_NA + (HL_FAMILY if fam else ""),
        reproduction="descriptive (amendment 4 section 2): Fisher's exact OR / FDR (not run: not auditable)",
        published_value_and_location=pub,
        n_cells=("UNDETERMINED: 3 named terms x the clusters in which each is enriched (not stated), fixed when the defining table is "
                 "read under G1; the family counts once (section 1.1)" if cid == "BE-11" else
                 "UNDETERMINED: modules of Supp Fig. 6e (unread), fixed when it is read under G1; the family counts once (section 1.1)"
                 if cid == "BE-12" else "1"),
        notes=("id: register." + (" Family (draft 'family'; one registered unit, section 1.1)." if fam else "")
               + " Frozen-11 row 4 has no focal (register section 4: the principal finding BE-01 has no full-verdict form)."
               + (" Recorded, not registered (section 1.1): the SCZ / BD specificity statement 'little to no enrichment' (Fig. 4d; draft "
                  "section 2.2), a within-paper control without a defined cell." if cid == "BE-06" else "")))

# ====================================================================================================================
# target 6 -- Rasero 2023
# ====================================================================================================================
RA_CARRIER = ("the repository notebook 05-mdmr_subtypes_vs_TDC.ipynb outputs (1,800,744 B) or the journal mmc1.pdf (1,691,460 B), "
              "opened under G1")
ID_NOTE_RA = ("carriers' " + ident("rasero2023neurogenetics", "notebook 05") + "; "
              + ident("rasero2023neurogenetics", "mmc1.pdf").split(": ", 1)[1] + "; per-gene step (dk34 / dk41, ML_Lag weights): "
              + ident("rasero2023neurogenetics", "notebook 08").split(": ", 1)[1] + "; " + ID_RULE)
_RAC = CARRIER["targets"]["rasero2023neurogenetics"]
RA_Y2 = ("y_S2: normalized MDMR pseudo-R^2 per DK region (82 = 68 cortical + 14 subcortical), subtype 2 'hyperconnected' (n = 284) vs "
         "TDC (n = 884); ABIDE I + II pooled (657 ASD / 884 TDC); from " + RA_CARRIER + "; " + ID_NOTE_RA)
RA_Y1 = ("y_S1: as y_S2 for subtype 1 'hypoconnected' (n = 348) vs TDC; from " + RA_CARRIER + "; " + ID_NOTE_RA)
RA_CARRIER_TEST = carrier_note(
    "the notebook outputs or mmc1.pdf hold, for subtype 1 and subtype 2, a numeric pseudo-R^2 per DK region with its region label "
    "(the MDMR maps: 82 regions, 68 cortical + 14 subcortical); required: every left parcel of the per-gene step (34 cortical, or 34 + "
    "7 subcortical, as notebook 08 or the journal Methods state -- fixed and recorded before the test runs, else not auditable "
    "(definition not applicable); register 2.6, section 1.11 item 8) on both maps, each once; a numeric parse of every value; partial or "
    "figure-only content does not qualify (section 1.8). Label list = carrier_tests.json targets.rasero2023neurogenetics.variants: "
    "dk34 = the %d left cortical abagen DK labels, dk41 = those + the %d left subcortical ones (abagen 0.1.3 %s, sha256 %s); "
    "normalisation_dk (a name without a hemisphere matches nothing)."
    % (_RAC["variants"]["dk34"]["required_count"], _RAC["variants"]["dk41"]["required_count"] - _RAC["variants"]["dk34"]["required_count"],
       _RAC["label_source"]["path_basename"], _RAC["label_source"]["sha256"]))
RA_CLASS = ("dk-ctx | V-DK (conditional: dk-ctx if the per-gene step used the 34 left cortical DK parcels, V-DK if 34 + 7 left subcortical, "
            "per notebook 08-calculate_gen_pvals.ipynb or the journal Methods; undeterminable -> not auditable (definition not applicable); "
            "register 2.6)")
T6 = Target(6, "rasero2023neurogenetics", "5", "G1", analysis_class=RA_CLASS,
            route=("native: the left-hemisphere DK parcels of the paper's per-gene step (34 -> dk-ctx; 34 + 7 -> V-DK); left hemisphere "
                   "only (the paper's restriction)"),
            dependencies=("RA-01-RA-10 overlap heavily (DLG4 in all 10; GRIA3 / GRIA4 in 9; GRIA1, GRIN2B, GRIA2 in 8) and share y_S2; "
                          "RA-11 / RA-12 share y_S2; RA-13 / RA-14 share y_S1"))
RA_COND_BASE = ("conditional: auditable iff %s, hold the subtype-1 and subtype-2 pseudo-R^2 on the DK regions with labels"
                % RA_CARRIER)
RA_COND = RA_COND_BASE + " (register 2.6; carrier test in notes)"
WG_REL = ("WebGestalt GMT, section 1.6 source 3, 'S re-derived': the 2022 release the paper used is not obtainable, the current "
          "server's category is used -- 'release substituted' (register section 1.11 item 2); the category reached by the name rule of "
          "sections 1.1 / 1.6 (register v6 R1)")
RA_VERS = ("Label 'preprint v1 claims (journal version unread)' unless the version of record is read before the freeze (register 2.6, "
           "section 6 item 6; declared); a difference found later in a claim-defining element is recorded, never used to redefine a claim.")
RA_CATS = [("RA-01", "Neuronal system", "Reactome"),
           ("RA-02", "Glutamate binding, activation of AMPA receptors and synaptic plasticity", "Reactome"),
           ("RA-03", "Trafficking of AMPA receptors", "Reactome"),
           ("RA-04", "Glutamate receptor signaling pathway", "GO BP"),
           ("RA-05", "Transmission across Chemical Synapses", "Reactome"),
           ("RA-06", "Neurotransmitter receptors and postsynaptic signal transmission", "Reactome"),
           ("RA-07", "Synapse organization", "GO BP"),
           ("RA-08", "Protein-protein interactions at synapses", "Reactome"),
           ("RA-09", "Unblocking of NMDA receptors, glutamate binding and activation", "Reactome"),
           ("RA-10", "Activation of NMDA receptors and postsynaptic events", "Reactome")]
for cid, cat, db in RA_CATS:
    focal = "yes" if cid == "RA-02" else "no"
    add(T6, cid, cell_class="claim", claim_form="decoded-list", map=RA_Y2,
        set_S=("%s '%s' (%s) intersected with the 2,587 HPA brain-specific genes "
               "(repo data/brain-specific_genes.txt, sha256 prefix c72639392c66; the paper's universe, register 2.6)" % (db, cat, WG_REL)),
        T=T_DL + "; y = y_S2", direction=M + " (enriched among the NEG genes, t < 0: registered one-sided, T < 0; register 2.6)",
        inference_level=("gene null only (uniform): WebGestalt GSEA (gene-set permutation within the FDR-pre-filtered list); per-gene "
                         "statistic from a parametric spatial-lag model (PySAL ML_Lag) upstream [draft alternative 'other' recorded]"),
        status=RA_COND, headline_population=HL_IN_FV_DESC,
        reproduction=("descriptive (amendment 4 section 2): the NEG list re-derived by the paper's rule (ML_Lag per gene on the "
                      "brain-specific universe, BH-FDR < .05, t < 0), then WebGestalt GSEA (FDR < .05); leading-edge Jaccard vs Fig. 4B; "
                      "Fig. 4A value"),
        published_value_and_location=("Fig. 4A bar (preprint v1; unlabelled axis, ~2.0-2.5 for all 10 categories); WebGestalt GSEA, FDR < "
                                      ".05 on the 322 FDR-significant subtype-2 genes ranked by ML_Lag t; Results para 5: 'for subtype 2, "
                                      "the enrichment of the NEG-genes included ... glutamate signaling (affecting both AMPA and NMDA "
                                      "receptors) and synapse organization ... (Fig. 4A)'"),
        focal=focal, verdict_counted_in_m="yes",
        notes=("id: register. " + ("Per-row focal of frozen-11 row 5: the text's first theme is glutamate signalling; the rule takes the "
                                   "first glutamate-named category in Fig. 4A order (register 2.6). " if focal == "yes" else "")
               + RA_VERS + " The paper's per-gene statistic is a spatial-lag t and its tested list the signed NEG list; our T is section "
               "1.4's mean per-gene Pearson r (register 2.6); the paper's ML_Lag t is a descriptor." + RA_CARRIER_TEST))
for cid, ymap, lab, size, sign in [("RA-11", RA_Y2, "subtype 2 NEG", "142", M), ("RA-12", RA_Y2, "subtype 2 POS", "180", "+"),
                                   ("RA-13", RA_Y1, "subtype 1 NEG", "195", M), ("RA-14", RA_Y1, "subtype 1 POS", "364", "+")]:
    k = cid[-1]
    add(T6, cid, cell_class="claim", claim_form="component", map=ymap,
        set_S=("the paper's %s list (FDR-significant ML_Lag genes; published in repo results/desikan/Subtype_%s_r2_gen_association_results.csv "
               "@9a333d93, opened under G1), selected on the claim's own map -> amendment 3 section 2 selected-list rule: re-selected on "
               "every permutation and surrogate by the paper's rule (ML_Lag + BH-FDR + sign) with the ML_Lag weights of the paper's code "
               "(notebook 08); universe = brain-specific ∩ matrix; an empty re-selected list -> T = 0 (register 2.6)"
               % (lab, "2" if cid in ("RA-11", "RA-12") else "1")),
        T=("component level (section 1.4; selected list): T = Pearson r(y, set score of the re-selected list), oriented by the list sign; "
           "Level 0 = 10,000 parcel-label permutations with re-selection; class-stratified site leg with re-selection; read 'passes / does "
           "not pass at component level'; a pass adds 'map-expression link, not set specificity'; label 'site leg only; not calibrated "
           "against expression-aligned maps'"),
        direction="%s (list sign; draft 2.2)" % sign,
        inference_level="other: parametric spatial-autoregressive model (PySAL ML_Lag) + BH; no surrogate or gene null (register 2.6)",
        status=(RA_COND_BASE + "; and the ML_Lag weights readable from notebook 08, else not auditable (definition not applicable) "
                "(register 2.6; carrier test in notes)"),
        headline_population=HL_IN_COMP,
        reproduction="descriptive (amendment 4 section 2): the re-selected list's size and Jaccard with the published list vs %s genes" % size,
        published_value_and_location=("%s %s genes (Results para 5: 'for subtype 1, a total of 195 negative-associated (NEG) genes and 364 "
                                      "positive-associated (POS) genes ... for subtype 2, we found 142 NEG-genes ... and 180 POS-genes')" % (size, lab)),
        verdict_counted_in_m="yes", notes="id: register. " + RA_VERS + RA_CARRIER_TEST)
for cid, what, ymap, S, lvl, T_, form in [
        ("RA-N1", "no enrichment for the undivided ASD group (draft 2.3)",
         "undivided ASD vs TDC pseudo-R^2 map (unpublished; register 2.6)", "no category named (the paper reports none significant)",
         "gene null only (uniform; GSEA)", "descriptor: decoded-list T over the categories (never computed: not auditable)",
         "decoded-list"),
        ("RA-N2", "none for the finer dendrogram subtypes (draft 2.3)",
         "finer-subtype pseudo-R^2 maps (number not stated; unpublished; register 2.6)", "no category named",
         "gene null only (uniform; GSEA)", "descriptor: decoded-list T over the categories (never computed: not auditable)",
         "decoded-list"),
        ("RA-N3", None, None, None, None, None, None),
        ("RA-N4", "TDC split pipeline: 'no gene survived by FDR in any subtype' (draft 2.3)",
         "TDC-split pseudo-R^2 maps (unpublished; register 2.6)", "the re-selected ML_Lag list (published: empty)",
         "other: parametric spatial-lag model + BH",
         "descriptor: the RA-11 ... RA-14 selected-list machinery (never computed: not auditable)", "component")]:
    if cid == "RA-N3":
        # register 2.6 (v4): conditional on the carrier of RA-11 ... 14, run as RA-01 ... 10's categories on y_S1, two-sided
        for k, (rid, cat, db) in enumerate(RA_CATS, start=1):
            add(T6, "RA-N3-%02d" % k, cell_class="descriptor", claim_form="decoded-list", map=RA_Y1,
                set_S=("as %s: %s '%s' (%s) intersected with the 2,587 HPA "
                       "brain-specific genes (repo data/brain-specific_genes.txt, sha256 prefix c72639392c66)" % (rid, db, cat, WG_REL)),
                cell_index=str(k),
                T="descriptor (section 1.1): " + T_DL + "; y = y_S1", direction="two-sided (descriptor cell; register 2.6)",
                inference_level="gene null only (uniform; GSEA) (register 2.6)",
                status=("conditional (descriptor): the carrier of RA-11 ... RA-14 holds the subtype-1 map y_S1 (register 2.6, v4; "
                        "carrier test in notes)"),
                headline_population=HL_DESC,
                reproduction=("descriptive (amendment 4 section 2): 'no significant enrichment for subtype 1' (Results para 5): the "
                              "subtype-1 NEG / POS lists re-derived by the paper's rule, then WebGestalt GSEA (FDR < .05)"),
                published_value_and_location=("'no significant enrichment for subtype 1' (Results para 5; no category named, no value; "
                                              "preprint v1)"),
                dependencies="shares y_S1 with RA-13 / RA-14; the category sets overlap as RA-01 ... RA-10's",
                notes=("id: compiler (register 2.6 names the unit RA-N3 -- subtype 1, map y_S1 -- run as RA-01 ... 10's categories on "
                       "y_S1, two-sided; one row per category cell, in RA-01 ... RA-10 order = Fig. 4A order; seed cell index %d, "
                       "section 1.9). " % k + RA_VERS + RA_CARRIER_TEST))
        continue
    add(T6, cid, cell_class="descriptor", claim_form=form, map=ymap, set_S=S, T=T_,
        direction="two-sided (descriptor cell)", inference_level=lvl,
        map_index=("0" if cid == "RA-N1" else "UNDETERMINED: several maps (%s); section 1.9 fixes map indices only for single-map "
                   "cells and Mamat's two-cohort claims (moot while not auditable)" % ("the finer subtypes, number not stated"
                                                                                     if cid == "RA-N2" else "the TDC split")),
        status="not auditable: the maps are unpublished (register 2.6)",
        headline_population=HL_DESC, reproduction="descriptive (amendment 4 section 2): " + what + " (not run: not auditable)",
        published_value_and_location=what,
        notes=("id: register (register 2.6: RA-N1 ... N4 = the undivided ASD group, the finer subtypes, subtype 1, the TDC split). The Dice "
               "robustness figures are not registered (register 2.6)."))

# ====================================================================================================================
# target 7 -- Buch 2023
# ====================================================================================================================
BUCH_N = {1: "69", 2: "87", 3: "67", 4: "76"}
ID_NOTE_BUCH = ident("buch2023asdsubgroups", "MOESM3") + "; " + ID_RULE
_BUC = CARRIER["targets"]["buch2023asdsubgroups"]
if _BUC["required_count"] != 230 or "id is not required" not in _BUC["required_comparison"]:
    die("carrier_tests.json: Buch must require >= 230 usable ROIs with coordinates and a value, no id (register section 1.11 item 8)")


def buch_map(k):
    return ("y_%d: net atypical connectivity per Power ROI, subgroup %d (N = %s) vs 907 controls (two-sided Welch t; sum of positive minus "
            "|sum of negative| atypical connectivity; ABIDE I + II pooled; 230 ROIs with AHBA coverage), from MOESM3.xlsx (Supplementary "
            "Tables 4-5; 1,586,689 B) opened under G1; %s" % (k, k, BUCH_N[k], ID_NOTE_BUCH))


BUCH_COND = ("conditional: MOESM3.xlsx holds, for each of the four subgroup maps y, >= 230 usable ROIs -- MNI coordinates and a numeric "
             "value; an ROI id is not required (register 2.7, section 1.11 item 8; carrier test in notes)")
BUCH_CARRIER_TEST = carrier_note(
    "MOESM3.xlsx (Supplementary Tables 4-5) holds, for each of the four subgroup maps, >= 230 usable ROIs, an ROI being usable iff it "
    "has three numeric MNI coordinates (in its row, or joined through an integer ROI id to coordinates elsewhere in the carrier) and a "
    "numeric value on that map; an ROI id is not required (the sphere rule of section 1.7 uses the carrier's own coordinates, not an "
    "id list; Buch reports 277 ROIs, Power's list has 264; register section 1.11 item 8); Power 2011 matching (%s, sha256 %s; within "
    "2.0 mm) is a diagnostic only; coordinates absent -> 'not auditable (ROI coordinates unpublished)' (section 1.7); partial or "
    "figure-only content does not qualify (section 1.8)." % (_BUC["label_source"]["source"], _BUC["label_source"]["sha256"]))
T7 = Target(7, "buch2023asdsubgroups", "6", "G1", analysis_class="V-AAL", route=ROUTE_POWER, status=BUCH_COND,
            dependencies=("cells of subgroup k share y_k and PLS1_k; overlapping sets (synaptic GO vs ASD-down; immune GO vs ASD-up); "
                          "the four subgroups share the 907 controls"))
for k in range(1, 5):
    add(T7, "BUCH-C%d" % k, cell_class="claim", claim_form="component", map=buch_map(k),
        set_S="none (component claim); X = the section 3.1 matrix of V-AAL (the paper: 10,438 z(log2) genes on 230 ROIs)",
        T=T_COMP_PLS1, direction="+ (upper tail: R^2 above the null)",
        inference_level=("spatial null only: spin test plus 10,000 sample permutations on PLS1 variance explained (spin on a sphere atlas "
                         "incl. subcortex / cerebellum / brainstem) (register 2.7)"),
        headline_population=HL_IN_COMP,
        reproduction=("4.1 check: PLS1 R^2 vs the variance explained in Supplementary Table 3 / 4 (read under G1); if the table holds no "
                      "R^2, descriptive (amendment 4 section 2): the spin p"),
        published_value_and_location=("spin p, subgroup %d: %s (Fig. 5a legend pp. 15-16: 'Subgroup 1: p = 0.014; Subgroup 2: p < 0.001; "
                                      "Subgroup 3: p < 0.001; Subgroup 4: p < 0.001; all statistics in Supplementary Table 4'); Results p. 7"
                                      % (k, {1: "0.014", 2: "< 0.001", 3: "< 0.001", 4: "< 0.001"}[k])),
        verdict_counted_in_m="yes",
        notes=("id: register. Precedes the focal enrichment cell but is not eligible (component level)."
               + (" ED Figs 8-9 out of scope (register 2.7)." if k == 1 else "") + BUCH_CARRIER_TEST))

BUCH_LOC = {
    "c": "Results pp. 7-8: 'All four subgroup PLS models were enriched for multiple ASD-related gene sets (Fig. 5c) ...'",
    "d": "Results p. 8: 'Positively-weighted genes in all four subgroups were enriched for immune-related diseases known to be comorbid with ASD (Fig. 5d)'",
    "e": "Results p. 8: 'negatively-weighted genes in Subgroups 1 and 4 ... were enriched for genes associated with Tourette's Disorder and ADHD (Fig. 5e)'; vocal learning: 'Subgroups 1, 3, and 4'",
    "f": "Results p. 8: 'Subgroup 2 ... only enriched for 2 of the 11 synaptic signaling gene sets while Subgroups 1, 3, and 4 were enriched for 11, 8, and 11 of the 11'",
    "g": "Results p. 8: 'Subgroup 3 ... enriched for all 12 immune signaling gene sets while Subgroups 1, 2, and 4 were only enriched for 6, 8 and 6'",
    "h": "Results p. 8: 'enriched for protein translation gene sets only in Subgroup 1, including ribosomal gene sets'",
}
NS = "ns"
PANTHER = ("Fig. 5%s label '%s' (as printed) -> the PANTHER 16.0 GO-slim term (the release the paper names) the label reaches by the "
           "name rule of sections 1.1 / 1.6 (register v6 R1; the term and tier: register_sets/NAME_MATCHES.json); " + GO_RULE)
# (panel, token, label/source, {subgroup: value}, {subgroup: kind}, sign)  kind: C claim, F figure-only, N16 stated null, NS other ns
BUCH_SETS = []


def bset(panel, token, src, vals, kinds, sign):
    BUCH_SETS.append((panel, token, src, vals, kinds, sign))


ALL = (1, 2, 3, 4)
bset("c", "ASDdown", "ASD downregulated genes, asdM12 (ref 118 via 119)", {1: M + "9.36", 2: M + "9.19", 3: M + "9.19", 4: M + "9.36"}, {k: "C" for k in ALL}, M)
bset("c", "ASDup", "ASD upregulated genes, asdM16 (ref 118 via 119)", {1: "9.36", 2: "9.19", 3: "9.19", 4: "9.36"}, {k: "C" for k in ALL}, "+")
bset("c", "FMRP", "FMRP-interacting genes (ref 122)", {1: M + "5.25", 2: M + "2.62", 3: M + "4.67", 4: M + "3.63"}, {k: "C" for k in ALL}, M)
bset("c", "SFARIsyn", "syndromic SFARI genes (ref 125)", {1: M + "5.13", 2: M + "1.81", 3: M + "4.77", 4: M + "2.75"}, {k: "C" for k in ALL}, M)
bset("c", "SPARK", "ASD SPARK genes (ref 121)", {1: M + "6.04", 2: M + "1.02 (ns)", 3: M + "4.24", 4: M + "2.76"}, {1: "C", 2: "NS", 3: "C", 4: "C"}, M)
bset("c", "RDNV", "ASD rare de novo variant genes (ref 120)", {1: M + "0.86", 2: M + "0.32", 3: M + "0.41", 4: M + "1.29"}, {k: "NS" for k in ALL}, "")
bset("c", "Grove", "ASD GWAS genes, Grove et al. (ref 19)", {1: "0.27", 2: M + "0.35", 3: "0.13", 4: M + "0.45"}, {k: "NS" for k in ALL}, "")
bset("d", "CNSauto", "CNS autoimmune disease genes (RGD, ref 129)", {1: "2.97", 2: "2.33", 3: "4.60", 4: "1.58"}, {k: "C" for k in ALL}, "+")
bset("d", "Osteo", "osteoarthritis genes (RGD, ref 129)", {1: "2.93", 2: "1.22 (ns)", 3: "3.54", 4: "1.82"}, {1: "C", 2: "NS", 3: "C", 4: "C"}, "+")
N16V = "n.s. (|value| < 1.30; max over the 16 stated nulls = 1.21; individual values not transcribed by the draft)"
for tok, lab in [("MSA", "multiple system atrophy genes (RGD, ref 129)"), ("Dementia", "dementia genes (RGD, ref 129)"),
                 ("HeartDisease", "heart disease genes (Pua 2016, ref 127)"), ("Psoriasis", "psoriasis genes (Nair 2009, ref 124)")]:
    bset("d", tok, "%s (Fig. 5d; v6.6 C5: the source the Methods cite)" % lab, {k: N16V for k in ALL}, {k: "N16" for k in ALL}, "")
bset("e", "Vocal", "vocal learning genes (ref 61)", {1: M + "5.58", 2: NS, 3: M + "3.54", 4: M + "4.35"}, {1: "C", 2: "NS", 3: "C", 4: "C"}, M)
bset("e", "ADHD", "ADHD genes (DISEASES, ref 128)", {1: M + "2.70", 2: NS, 3: NS, 4: M + "2.04"}, {1: "C", 2: "NS", 3: "NS", 4: "C"}, M)
bset("e", "TS", "Tourette's disorder genes (DISEASES, ref 128)", {1: M + "1.55", 2: NS, 3: NS, 4: M + "2.06"}, {1: "C", 2: "NS", 3: "NS", 4: "C"}, M)
bset("e", "SZ", "schizophrenia genes (CTD, ref 126)", {1: M + "2.07", 2: NS, 3: NS, 4: M + "1.84"}, {1: "F", 2: "NS", 3: "NS", 4: "F"}, M)
bset("e", "MDD", "MDD genes (DISEASES, ref 128)", {1: NS, 2: NS, 3: NS, 4: M + "2.11"}, {1: "NS", 2: "NS", 3: "NS", 4: "F"}, M)
bset("e", "GAD", "GAD genes (DISEASES, ref 128)", {1: NS, 2: NS, 3: NS, 4: M + "1.48"}, {1: "NS", 2: "NS", 3: "NS", 4: "F"}, M)
for tok, lab in [("ID", "intellectual disability genes, 'ID All' (Parikshak 2013, ref 123)"),
                 ("Aphasia", "aphasia genes (DISEASES, ref 128)"), ("ConductDisorder", "conduct disorder genes (DISEASES, ref 128)"),
                 ("AntisocialPD", "antisocial personality disorder genes (DISEASES, ref 128)"),
                 ("NeuroticDisorder", "neurotic disorder genes (DISEASES, ref 128)")]:
    bset("e", tok, "%s (Fig. 5e; v6.6 C5: the source the Methods cite)" % lab, {k: "ns ('none significant')" for k in ALL},
         {k: "NS" for k in ALL}, "")
# register v6 R1: the labels as printed in Fig. 5f / 5g (the draft's transcription, incorporated by reference) and Fig. 5h (the
# approved pre-freeze re-read, buch_fig5h_grid.json); the S-build maps each by the name rule (register_sets/NAME_MATCHES.json)
SYN = [("SecVesicle", "Secretory vesicle", {1: "3.37", 3: "3.24", 4: "4.00"}),
       ("PresynActiveZone", "Presynaptic active zone", {1: "3.19", 3: "3.77", 4: "2.73"}),
       ("PostsynMembrane", "Postsynaptic membrane", {1: "3.63", 3: "2.38", 4: "3.60"}),
       ("IonChannelComplex", "Ion channel complex", {1: "4.52", 3: "1.80", 4: "3.62"}),
       ("ChemSynTransmission", "Chemical synaptic transmission", {1: "7.51", 2: "3.22", 3: "7.41", 4: "7.41"}),
       ("MembranePotential", "Regulation of membrane potential", {1: "6.70", 3: "4.16", 4: "5.11"}),
       ("NTSecretion", "Neurotransmitter secretion", {1: "4.15", 2: "2.47", 3: "4.22", 4: "3.54"}),
       ("GPCR", "GPCR signaling pathway", {1: "4.23", 2: "1.32", 4: "5.73"}),
       ("SynapseOrg", "Synapse organization", {1: "3.86", 3: "3.34", 4: "2.72"}),
       ("cAMP", "cAMP-mediated signaling", {1: "2.89", 4: "3.94"}),
       ("GluRSignaling", "Glutamate receptor signaling pathway", {1: "2.92", 4: "1.71"})]
for tok, lab, v in SYN:
    bset("f", "Syn-" + tok, PANTHER % ("f", lab), {k: (M + v[k]) if k in v else NS for k in ALL}, {k: ("C" if k in v else "NS") for k in ALL}, M)
IMM = [("CytokineReceptorBinding", "Cytokine receptor binding", {3: "1.97"}),
       ("CytokineActivity", "Cytokine activity", {2: "1.59", 3: "1.84"}),
       ("CytokineBinding", "Cytokine binding", {2: "1.77", 3: "2.23"}),
       ("CytokineReceptorActivity", "Cytokine receptor activity", {2: "2.00", 3: "2.33", 4: "1.38"}),
       ("ProteaseBinding", "Protease binding", {2: "2.43", 3: "2.24", 4: "1.51"}),
       ("LeukocyteChemotaxis", "Leukocyte chemotaxis", {3: "2.22"}),
       ("ResponseToxicSubstance", "Response to toxic substance", {1: "2.07", 3: "2.47"}),
       ("CytokineProduction", "Cytokine production", {1: "2.22", 3: "2.90"}),
       ("TCRSignaling", "T cell receptor signaling pathway", {1: "1.61", 2: "2.45", 3: "1.94", 4: "3.44"}),
       ("ResponseToCytokine", "Response to cytokine", {1: "3.23", 2: "2.56", 3: "3.35", 4: "3.07"}),
       ("ImmuneActivatingST", "Immune response-activating signal transduction", {1: "2.99", 2: "3.83", 3: "3.96", 4: "4.37"}),
       ("ImmuneResponse", "Immune response", {1: "3.93", 2: "3.38", 3: "5.28", 4: "4.25"})]
for tok, lab, v in IMM:
    bset("g", "Imm-" + tok, PANTHER % ("g", lab), {k: v.get(k, NS) for k in ALL}, {k: ("C" if k in v else "NS") for k in ALL}, "+")
TRANS = [("StructConstRibosome", "2.80"), ("RibosomalSubunit", "2.25"), ("Ribosome", "2.42"), ("CytosolicRibosome", "2.94"),
         ("CytoplasmicTranslation", "1.43")]
# register section 1.11 item 9 (v5): the Fig. 5h grid re-read before the freeze (buch_fig5h_grid.json): 5 rows x 4 subgroups, the 5
# marked cells = subgroup 1 (the claims); the 15 unmarked cells carry their printed values, not 'ns'
GRID5H = {c["tsv_cell"]: c for c in BUCH5H["cells"]}
if (BUCH5H["grid_shape"]["n_cells"], BUCH5H["marked_cells"]["n"], len(GRID5H)) != (20, 5, 20):
    die("buch_fig5h_grid.json: expected 20 cells, 5 marked")
ASTERISK_ROW = BUCH5H["rows_top_to_bottom_as_printed"][0]
if not ASTERISK_ROW.startswith("*"):
    die("buch_fig5h_grid.json: the first row is not the asterisked '*Ribosomal structure'")
if len(BUCH5H["rows_top_to_bottom_as_printed"]) != len(TRANS):
    die("buch_fig5h_grid.json: 5 printed rows expected")
# register v6 R1 / R2: the asterisked row reaches no PANTHER 16.0 GO-slim term by the name rule -> S from MOESM3 if it defines the
# set, else not auditable (S undefined); v5's inferred mapping ('structural constituent of ribosome') is withdrawn
R2_BUCH = (": not auditable (S undefined: source 1 uncorroborated; v6.5) -- the printed label reaches no name, synonym or normalised "
           "name of PANTHER 16.0 GO-slim under the name rule, so sources 2-3 define no set, and the paper prints no size, so no list "
           "MOESM3 holds could be corroborated (section 1.6; register v6 R1; v6-v6.4: S conditional on MOESM3, R2; the asterisk is "
           "unexplained in the legend, register section 1.11 item 9)")
for (tok, v), printed in zip(TRANS, BUCH5H["rows_top_to_bottom_as_printed"]):
    vals, kinds = {}, {}
    for k in ALL:
        c = GRID5H["BUCH-E-Trans-%s-S%d" % (tok, k)]
        if c["marked"] != (k == 1):
            die("Fig. 5h: the marked cells are subgroup 1 only (register section 1.11 item 9)")
        if k == 1 and c["printed"] != v:
            die("Fig. 5h: the re-read value of %s S1 differs from the draft's" % tok)
        vals[k], kinds[k] = c["printed"], ("C" if c["marked"] else "NS")
    bset("h", "Trans-" + tok, PANTHER % ("h", printed), vals, kinds, "+")


# register v6.6 (B2 / C5; orchestrator under the operator's standing delegation): the comparator the S-build builds for each Buch
# Fig. 5c-e set and each Pagani set by register 1.6's resolution rule -- (set id, what it is) or (None, why not buildable); asserted
# equal to register_sets/MANIFEST.json "comparators_v6_6"
COMP66_BUCH = {
    "ASDdown": (None, "R-d (v6.8, applied uniformly; post hoc, declared): 'asdM12' reaches ref 118's module M12 only through "
                      "Parikshak 2013's name (ref 123, not cited by Buch for this set); ref 119 holds no list of that name -- "
                      "Voineagu's Supplementary Table 14 (the M12 genes) is the near-miss view's comparator (v6.7 N1 had admitted "
                      "it to the primary view)"),
    "ASDup": (None, "R-a / R-e: refs 118 / 119 distribute no asdM16 membership (Voineagu prints the M12 genes but no M16 / tan "
                    "table, its Supplementary Table 2 kME only; Parikshak 2016: no list of that name); Parikshak 2013's 'asdM16 "
                    "from Vioneagu et al 2011' (ref 123) is not reached -- it is the near-miss view's comparator"),
    "FMRP": (None, "R-a / R-e: ref 122 (Steinberg & Webber 2013) distributes no list of the 842 FMRP targets; Darnell 2011's Table "
                   "S2A (not cited) is the near-miss view's comparator"),
    "SFARIsyn": ("cmp67_buch_sfari_syndromic_20211022", "SFARI Gene syndromic genes, release 09-02-2021 as exported 10-22-2021 "
                                                         "(Wayback capture; the state current at the submission date, read by the "
                                                         "served release label: v6.7 N2)"),
    "SPARK": ("cmp66_buch_spark_gene_list_2019", "the SPARK gene list (updated July 2019; 153 single genes; current at the "
                                                 "submission date: bracketing captures, identical digest)"),
    "RDNV": (None, "R-e by reading (iii) (v6.9 C5, applied uniformly; post hoc, declared): ref 120's Table S1 presents several "
                   "gene flags (ASD65, DDD93, CHD253, sfari*) and names none 'rare de novo'; ASD65 was reached by a semantic "
                   "reading of its column note -- its 65 genes are the near-miss view's comparator (v6.6-v6.8: built, primary)"),
    "Grove": (None, "R-e: ref 19 distributes several gene lists (Supplementary Tables 4, 10, 16), none as the named set"),
    "CNSauto": (None, "R-d: 'CNS autoimmune' reaches no RGD disease-ontology term by the name rule"),
    "Osteo": ("cmp67_buch_rgd_DOID8398_20240720", "RGD human genes annotated to RDO 'osteoarthritis' (DOID:8398) or a descendant "
                                                  "(annotations of 2024-07-20, Wayback capture 2024-07-24: v6.7 (2))"),
    "MSA": ("cmp67_buch_rgd_DOID4752_20240720", "RGD human genes annotated to RDO 'multiple system atrophy' (DOID:4752) or a "
                                                "descendant (annotations of 2024-07-20: v6.7 (2))"),
    "Dementia": ("cmp67_buch_rgd_DOID1307_20240720", "RGD human genes annotated to RDO 'dementia' (DOID:1307) or a descendant "
                                                     "(annotations of 2024-07-20: v6.7 (2))"),
    "HeartDisease": ("cmp66_buch_pua2016_icc_genes", "Pua 2016 Table S1, the inherited cardiac condition genes"),
    "Psoriasis": (None, "R-e: ref 124 distributes loci with 'notable nearby genes', not a gene list"),
    "Vocal": (None, "R-e: ref 61's Tables S1-S8 (obtained, v6.7 N4) hold several specialisation lists and name none 'vocal "
                    "learning' genes"),
    "ADHD": ("cmp66_buch_diseases_DOID1094", "DISEASES v2 (2022-02-09) 'Attention deficit hyperactivity disorder' (DOID:1094): "
                                             "its filtered associations, three channels"),
    "TS": (None, "R-d: no name the paper gives ('Tourette's syndrome', 'Tourette's') reaches a DISEASES term by the name rule"),
    "SZ": ("cmp67_buch_ctd_MESHD012559_20240131", "CTD genes of Schizophrenia (MESH:D012559) and its descendants, curated and "
                                                  "inferred (report of 2024-01-31, Wayback capture 2024-02-10: v6.7 (2))"),
    "MDD": ("cmp66_buch_diseases_DOID1470", "DISEASES v2 'Major depressive disorder' (DOID:1470)"),
    "GAD": ("cmp66_buch_diseases_DOID14320", "DISEASES v2 'Generalized anxiety disorder' (DOID:14320)"),
    "ID": ("cmp66_buch_parikshak2013_id_all", "Parikshak 2013 Table S1D 'ID All'"),
    "Aphasia": ("cmp66_buch_diseases_DOID0060046", "DISEASES v2 'Aphasia' (DOID:0060046)"),
    "ConductDisorder": ("cmp66_buch_diseases_DOID12995", "DISEASES v2 'Conduct disorder' (DOID:12995)"),
    "AntisocialPD": ("cmp66_buch_diseases_DOID10939", "DISEASES v2 'Antisocial personality disorder' (DOID:10939)"),
    "NeuroticDisorder": ("cmp66_buch_diseases_DOID4964", "DISEASES v2 'Neurotic disorder' (DOID:4964)"),
}
COMP66_PAGANI = {
    "PAG-C1": ("cmp66_pagani_gandal2022_24_de_modules", "all genes of Gandal 2022's 24 gene co-expression modules DE in ASD"),
    "PAG-C2": ("cmp66_pagani_gandal2022_24_de_modules", "all genes of Gandal 2022's 24 gene co-expression modules DE in ASD"),
    "PAG-C3": ("cmp66_pagani_reactome92_RHSA112315", "Reactome 92 R-HSA-112315"),
    "PAG-C4": ("cmp66_pagani_syngo_1.2_20231201", "SynGO 1.2 (release 20231201), all 1,602 genes"),
    "PAG-C5": ("cmp66_pagani_reactome92_RHSA6794362", "Reactome 92 R-HSA-6794362"),
    "PAG-C6": ("cmp66_pagani_reactome92_RHSA199991", "Reactome 92 R-HSA-199991"),
    "PAG-C7": ("cmp66_pagani_reactome92_RHSA1280215", "Reactome 92 R-HSA-1280215"),
    "PAG-C8": ("cmp66_pagani_reactome92_RHSA168249", "Reactome 92 R-HSA-168249"),
    "PAG-C9": (None, "R-d: 'vesicle transport and release' is no module label Gandal 2022 prints (Fig. 3a / 4a); Gandal's text "
                     "describes GeneM3 with its words -- the near-miss view's comparator"),
    "PAG-C10": (None, "R-d: 'synaptic vesicles and plasticity' is no module label Gandal 2022 prints (Fig. 3a / 4a); Gandal's text "
                      "describes GeneM5 with its words -- the near-miss view's comparator"),
    "PAG-C11": ("cmp66_pagani_gandal2022_GeneM7", "Gandal 2022 GeneM7 'immune response' (Fig. 4a)"),
    "PAG-C12": ("cmp66_pagani_gandal2022_GeneM8", "Gandal 2022 GeneM8 'reactive microglia' (Fig. 4a)"),
}
# register v6.7 (1): the registered SECONDARY view 'near-miss comparator' -- (set id, what it is) or (None, why not buildable either);
# asserted equal to register_sets/MANIFEST.json comparators_v6_6.near_miss_view_v6_7 and to carrier_tests.json's view pins
# v6.9 (C3): '/ name bridge' added; v6.10: '/ note reading' added -- as s_build_v66.NEAR_MISS_LABEL
NM_LABEL = ("comparator from a near-miss source (not the cited reference) / normalised name / name bridge / "
            "note reading")
NM67 = {
    "ASDdown": ("nm68_buch_voineagu2011_M12_table14", "Voineagu 2011 Supplementary Table 14, the M12 module genes (the cited "
                                                      "source's list, reached from 'asdM12' through Parikshak 2013's name; v6.8 "
                                                      "B S1)"),
    "ASDup": ("nm67_buch_parikshak2013_asdM16", "Parikshak 2013 Table S1D 'asdM16 from Vioneagu et al 2011' (Parikshak 2013 named "
                                                "Voineagu's M16 'asdM16'; ref 123, not cited by Buch for this set)"),
    "FMRP": ("nm67_buch_darnell2011_fmrp842", "Darnell 2011 Table S2A, the 842 FMRP targets ref 122 says it used (N7; not cited by "
                                              "Buch)"),
    "CNSauto": (None, "the declared normalisation 'CNS' -> 'central nervous system' reaches no RGD disease-ontology term either"),
    "Vocal": (None, "the cited source itself distributes the candidate lists; choosing one is the choice R-e forbids"),
    "TS": ("nm67_buch_diseases_DOID11119", "DISEASES v2 DOID:11119 'Tourette syndrome', reached after the declared normalisation "
                                           "(the possessive \"'s\" stripped)"),
    "RDNV": ("nm69_buch_sanders2019_asd65", "Sanders 2019 Table S1, ASD65 (65 genes), reached from 'ASD rare de novo' by a "
                                           "semantic reading of the column's note, not its title (v6.9 C5; v6.6-v6.8's primary "
                                           "comparator)"),
    "PAG-C9": ("nm67_pagani_gandal2022_GeneM3", "Gandal 2022 GeneM3, whose Results text reads '... such as vesicle transport and "
                                                "release' (N6)"),
    "PAG-C10": ("nm67_pagani_gandal2022_GeneM5", "Gandal 2022 GeneM5, whose Results text reads '... synaptic vesicle function, "
                                                 "cytoskeleton and synaptic plasticity' (N6)"),
}
NM_CELLS = {("BUCH-E-%s-S%d" % (t, k) if not t.startswith("PAG-") else t): t for t in NM67
            for k in ((1, 2, 3, 4) if not t.startswith("PAG-") else (0,))}
M_BEFORE_SU = {}  # v6.7: a row's verdict_counted_in_m before the S-undefined rule set it to 'no' (the view's m' reads it)
COMP_S = (": Buch's own list in MOESM3 if the carrier presents it as the set's input membership (source 1, by the section 1.6 "
          "source-1 criterion) and it is corroborated -- Jaccard >= .80 with the comparator built before the freeze (v6.6 B2: "
          "register_sets/%s.json, pinned by sha256 in carrier_tests.json, B1); else that comparator ('S re-derived'): %s")
NOTBUILD_S = (": not auditable (S undefined: comparator not buildable pre-freeze; v6.6 B2) -- %s; no list MOESM3 holds could be "
              "corroborated (register 1.6)")


def buch_add(panel, tok, src, val, kind, sign, k, register_named=False):
    cid = "BUCH-E-%s-S%d" % (tok, k)
    goslim = src.startswith("Fig. 5") and tok != "Trans-StructConstRibosome"
    S = ((src + R2_BUCH) if tok == "Trans-StructConstRibosome" else
         (src + ": Buch's own list in MOESM3 if the carrier presents it as the set's input membership (source 1, by the section 1.6 "
          "source-1 criterion and corroborated by Jaccard >= .80 with the fallback, v6.5; under G1), else the fallback built before "
          "the freeze -- the genes PANTHER 16.0's own gene -> GO-slim "
          "annotation lists under that term, as served (PTHR16.0_human; the named tool's library, section 1.6 R12 logic; v6.2 P3; "
          "register_sets/buch_goslim_fallback_*.json)") if goslim else
         (src + (COMP_S % COMP66_BUCH[tok] if COMP66_BUCH[tok][0] else NOTBUILD_S % COMP66_BUCH[tok][1])))
    common = dict(map=buch_map(k), set_S=S, T=T_PLSE if kind == "C" else "descriptor (section 1.1): " + T_PLSE,
                  inference_level=("gene null only (uniform): fGSEA gene-label permutation (register 2.7) [draft reading 'none' "
                                   "(amendment 4 section 1's Pagani convention; its Q3 offered 'gene null only') recorded]"),
                  published_value_and_location=(("Fig. 5%s value %s (-log10 FDR x direction of enrichment; read from the published "
                                                 "figure by the draft); %s" % (panel, val, BUCH_LOC[panel])) if panel != "h" else
                                                ("Fig. 5h printed value %s (-log10 FDR x direction of enrichment; %s; register section "
                                                 "1.11 item 9, register_maps/buch_fig5h_grid.json); %s"
                                                 % (val, "cell marked significant (solid border); read by the draft and confirmed by "
                                                    "the pre-freeze re-read" if kind == "C" else "unmarked cell (dotted border), not "
                                                    "marked significant; printed value recorded by the approved pre-freeze re-read",
                                                    BUCH_LOC[panel]))),
                  reproduction=("descriptive (amendment 4 section 2): the PLS1 bootstrap-z ranking re-derived by the paper's rule, weighted "
                                "fGSEA, BH-FDR < .05; sign and significance vs the Fig. 5%s value %s" % (panel, val)))
    if kind == "C":
        note = "id: register." if register_named else "id: draft (pattern BUCH-E-<set>-S<k>; set token for GO cells assigned by the compiler)."
        if tok == "ASDdown" and k == 1:
            note = ("id: register. Per-row focal of frozen-11 row 6: the first enrichment cell stated (Results pp. 7-8); BUCH-C1 ... C4 "
                    "precede it but are not eligible (register 2.7).")
        add(T7, cid, cell_class="claim", claim_form="PLS-enrichment",
            direction="%s (Fig. 5 value %s 0: %s weighted genes; the section 4.7 orientation)" % (sign, ">" if sign == "+" else "<",
                                                                                             "positively" if sign == "+" else "negatively"),
            headline_population=HL_IN_FV_DESC,
            verdict_counted_in_m="yes", focal="yes" if (tok == "ASDdown" and k == 1) else "no", notes=note + BUCH_CARRIER_TEST, **common)
    elif kind == "M":
        add(T7, cid, cell_class="descriptor", claim_form="PLS-enrichment",
            direction="%s (figure sign; descriptor)" % sign, headline_population=HL_DESC,
            notes=("id: register (Syn-GPCR-S2). Descriptor cell (register 2.7, v4): its printed value " + M + "1.32 would pass the "
                   "figure's FDR .05 encoding (|x| > 1.301), but the text counts 2 of 11 synaptic sets for subgroup 2 and it is not known "
                   "that the figure marks the cell itself (mismatch recorded); v3 registered it as a claim in m." + BUCH_CARRIER_TEST),
            **common)
    elif kind == "F":
        add(T7, cid, cell_class="descriptor", claim_form="PLS-enrichment",
            direction="%s (figure sign; descriptor)" % sign, headline_population=HL_DESC,
            notes="id: draft. Figure-only cell, not cited by the text for any finding -> descriptor (register 2.7)." + BUCH_CARRIER_TEST,
            **common)
    else:
        extra = {}  # v6.6: a cell without a buildable comparator is not auditable (S undefined) through the S-build
        add(T7, cid, cell_class="descriptor", claim_form="PLS-enrichment", direction="two-sided (descriptor cell; non-significant)",
            headline_population=HL_DESC, **extra,
            notes=("id: compiler (draft pattern). " + ("One of the 16 stated non-enrichments (Results p. 8: 'there was no enrichment for "
                                                        "genes associated with multiple systems atrophy, dementia, heart disease, or "
                                                        "psoriasis') -> descriptor (register 2.7)." if kind == "N16" else
                                                        "Non-significant cell of Fig. 5%s -> descriptor (register 2.7)." % panel)
                   + (" The Fig. 5h descriptor grid is registered exactly as the figure shows it, re-read before the freeze (register "
                      "2.7, section 1.11 item 9): 5 rows x 4 subgroups, the 5 marked cells all in subgroup 1; this unmarked cell prints "
                      "%s." % val if panel == "h" else "") + BUCH_CARRIER_TEST),
            **common)


# claims, register order: ASD sets, non-psychiatric, vocal, ADHD, Tourette's, synaptic (32), immune, translation (102 enrichment claims)
REG_NAMED_BUCH = {("ASDdown", 1)}
for panel in "cdefgh":
    for (p, tok, src, vals, kinds, sign) in BUCH_SETS:
        if p != panel:
            continue
        for k in ALL:
            if kinds[k] == "C" and not (tok == "Syn-GPCR" and k == 2):
                buch_add(p, tok, src, vals[k], "C", sign, k, register_named=(tok, k) in REG_NAMED_BUCH)
# descriptors, register order: Syn-GPCR-S2 (v4), figure-only (SZ S1, SZ S4, MDD S4, GAD S4), the 16 stated nulls, then every other
# non-significant cell by panel
for (p, tok, src, vals, kinds, sign) in BUCH_SETS:
    if tok == "Syn-GPCR":
        buch_add(p, tok, src, vals[2], "M", sign, 2)
for tok, k in [("SZ", 1), ("SZ", 4), ("MDD", 4), ("GAD", 4)]:
    for (p, t_, src, vals, kinds, sign) in BUCH_SETS:
        if t_ == tok:
            buch_add(p, t_, src, vals[k], "F", sign, k)
for (p, tok, src, vals, kinds, sign) in BUCH_SETS:
    for k in ALL:
        if kinds[k] == "N16":
            buch_add(p, tok, src, vals[k], "N16", sign, k)
for panel in "cdefgh":
    for (p, tok, src, vals, kinds, sign) in BUCH_SETS:
        if p != panel:
            continue
        for k in ALL:
            if kinds[k] == "NS":
                buch_add(p, tok, src, vals[k], "NS", sign, k)

# ====================================================================================================================
# target 8 -- Mamat 2025
# ====================================================================================================================
ID_NOTE_MA = ("carriers' " + ident("mamat2025molecular", "Additional file 1") + "; "
              + "; ".join(ident("mamat2025molecular", "Additional file %d" % k).split(": ", 1)[1] for k in (2, 3, 4)) + "; " + ID_RULE)
_MAC = CARRIER["targets"]["mamat2025molecular"]
if not (_MAC["required_count"] == 400 and _MAC.get("index_labels", {}).get("allowed") and _MAC["index_labels"]["range"] == [1, 400]
        and _MAC["index_labels"].get("requires_order_file_named")):
    die("carrier_tests.json: Mamat must require 400 parcels by name, or by index 1 ... 400 only where the carrier names the "
        "17-network order file (register section 1.11 item 8, v6 R9)")
MA_FILES = ("Additional files 1-4 (13229_2024_632_MOESM1_ESM.pdf 5,191,334 B; MOESM2-4 xlsx 1,349,131 / 30,487 / 186,923 B) opened "
            "under G1; " + ID_NOTE_MA)
MA_CARRIER_TEST = carrier_note(
    "Additional files 1-4 (searched as one) hold the ABIDE I and the ABIDE II FD t-map, each as 400 numeric values on the "
    "Schaefer-400 (17 networks) parcels, the parcels given by name, OR by index 1 ... 400 ONLY IF the carrier itself names the "
    "17-network order file (Schaefer2018_400Parcels_17Networks_order; register section 1.11 item 8 as revised by v6 R9): an "
    "index-only table in a carrier that names no order file, or names another one (e.g. the 7-network order), does not qualify "
    "-> not auditable (carrier test failed); names win a tie; required count 400 per map, each parcel once (C1, C2: the ABIDE I "
    "map; C3: the ABIDE II map; every enrichment claim: both); label list = carrier_tests.json targets.mamat2025molecular."
    "labels_detail (%s; order file sha256 %s); normalisation_schaefer; a numeric parse of every value; a 399-parcel table fails; "
    "partial or figure-only content does not qualify (section 1.8); the PDF (Additional file 1) is parsed with pdfplumber, pinned "
    "and installed under the gate before its first use (section 1.11 item 8)."
    % (_MAC["label_source"]["source"], _MAC["label_source"]["labels_file_sha256"]))
MA_Y1 = ("ABIDE I FD t-map (ComBat-harmonised ASD-vs-TDC t-map of cortical fractal dimension; 460 ASD / 515 TDC, 15 sites; Schaefer-400 "
         "17-network, 400 cortical parcels) from " + MA_FILES)
MA_Y2 = "ABIDE II FD t-map (379 ASD / 475 TDC, 13 sites; Schaefer-400 17-network) from " + MA_FILES
MA_BOTH = ("ABIDE I FD t-map AND ABIDE II FD t-map (Schaefer-400, 17 networks; each enrichment claim is one test across the two cohort "
           "maps, register 2.8) from " + MA_FILES)
MA_COND = ("conditional: Additional files 1-4 hold both FD t-maps (ABIDE I and ABIDE II, Schaefer-400, 17 networks), each on the 400 "
           "parcels by name, or by index 1 ... 400 only if the carrier names the 17-network order file (section 1.11 item 8, v6 R9) "
           "(C1, C2: the ABIDE I map; C3: the ABIDE II map; every enrichment claim needs both) (register 2.8; carrier test in notes)")
T8 = Target(8, "mamat2025molecular", "7", "G1", analysis_class="dk-ctx", route=ROUTE_SCHAEFER, status=MA_COND,
            dependencies=("URG / DRG lists are a conjunction over ABIDE I PLS1 / PLS3 and ABIDE II PLS1; every enrichment claim shares "
                          "both maps; GO terms overlap (parents / children)"))
MA_COMP_PUB = ("P < 0.05 (Fig. 3A; exact value in the figure, not read): 'The first and third PLS components of ABIDE I and the first "
               "component of ABIDE II were extracted based on their high statistical significance (P < 0.05)' (Results 'Brain gene "
               "expression profiles...')")
MA_COMP_REP = "descriptive (amendment 4 section 2): only P < .05 is published (Fig. 3A; register 2.8)"
MA_COMP_LVL = ("other: unstated (the test behind the component P is not stated; spin is described for gene significance) (register 2.8) "
               "[draft: 'other / unstated' or 'spatial null only', left open (its Q5)]")
for cid, ymap, comp, T_ in [("MAMAT-C1", MA_Y1, "ABIDE I PLS1", T_COMP_PLS1),
                            ("MAMAT-C2", MA_Y1, "ABIDE I PLS3",
                             T_COMP_PLS1.replace("T = R^2 of PLS1 (cascade.pls1)", "T = R^2 of PLS component 3 (prereg section 4.7 "
                                                 "PLSRegression(n_components=3, scale=True): the smallest model holding component 3, as the "
                                                 "paper states no K; register 2.8)")),
                            ("MAMAT-C3", MA_Y2, "ABIDE II PLS1", T_COMP_PLS1)]:
    add(T8, cid, cell_class="claim", claim_form="component", map=ymap,
        set_S="none (component claim); X = the section 3.1 matrix of dk-ctx (the paper: AHBA 15,633 genes, inter-donor r >= .5, SRS)",
        T=T_, direction="+ (upper tail: R^2 above the null)", inference_level=MA_COMP_LVL,
        headline_population=HL_IN_COMP,
        reproduction=MA_COMP_REP, published_value_and_location=MA_COMP_PUB + "; " + comp,
        verdict_counted_in_m="yes",
        notes="id: register. Precedes the focal enrichment cell but is not eligible (component level)." + MA_CARRIER_TEST)
MA_LOC = "Results 'Gene enrichment analyses'"
MA_LVL = ("gene null only (uniform): Metascape / SEA / TissueEnrich over-representation (Fisher / hypergeometric + BH; background not "
          "stated) (register 2.8); spin upstream in gene selection (1,000 spin permutations to assess gene significance) [draft reading "
          "'none' (amendment 4 section 1's Pagani convention) recorded]")
MA_REP = ("descriptive (amendment 4 section 2): URG / DRG re-derived by the paper's rule (per-gene regression on each t-map, bootstrap z, "
          "|Z| > 1.96, spin check; intersection over ABIDE I PLS1 / PLS3 and ABIDE II PLS1) on amendment 4 section 2's per-donor parcel "
          "recipe, then the paper's enrichment test; OR, p and Jaccard with the published URG / DRG lists (Additional files 2-3)")
MA_T = (T_DL + "; each enrichment claim is one test across the two cohort maps: it survives iff the verdict survives on the ABIDE I map "
        "and on the ABIDE II map (p = the larger conjunction p) (register 2.8)")
MA_GO_REL = ("the release the paper names, else the release in force at the paper's submission date (Metascape; version unstated): "
             "section 1.6 source 3, 'S re-derived'")
KEGG_MAMAT = ((("" if MANIFEST["kegg_release_rule"]["mamat2025molecular"]["chosen"].startswith("KEGG REST") else "Enrichr ")
               + MANIFEST["kegg_release_rule"]["mamat2025molecular"]["chosen"]) if "kegg_release_rule" in MANIFEST
              else "pending (draft for the S-build)")  # v6.7 (2): an archived KEGG REST release may be the closest
MA_E = [
    ("MAMAT-E-URG-BP-1", "GO BP 'modulation of synaptic transmission'", "URG", "+",
     "'significant enrichment of URGs in several key biological processes, including modulation of synaptic transmission, signaling, and nervous system processes' (%s; Fig. 4A)" % MA_LOC),
    ("MAMAT-E-URG-BP-2", "GO BP 'signaling'", "URG", "+", "same sentence (%s; Fig. 4A)" % MA_LOC),
    ("MAMAT-E-URG-BP-3", "GO BP 'nervous system processes'", "URG", "+", "same sentence ('nervous system processes') (%s; Fig. 4A)" % MA_LOC),
    ("MAMAT-E-URG-CC-1", "GO CC 'mitochondrial membrane'", "URG", "+",
     "'URGs exhibited enrichment in cellular components such as the mitochondrial membrane and respirasome' (%s)" % MA_LOC),
    ("MAMAT-E-URG-CC-2", "GO CC 'respirasome'", "URG", "+", "same sentence (%s)" % MA_LOC),
    ("MAMAT-E-URG-MF-1", "GO MF 'electron transfer activity'", "URG", "+",
     "'... and in molecular functions including electron transfer activity and inorganic molecular entity transmembrane transporter activity' (%s)" % MA_LOC),
    ("MAMAT-E-URG-MF-2", "GO MF 'inorganic molecular entity transmembrane transporter activity'", "URG", "+", "same sentence (%s)" % MA_LOC),
    ("MAMAT-E-DRG-BP-1", "GO BP 'chromatin organization'", "DRG", M,
     "'DRGs showed significant enrichment in biological processes associated with chromatin organization and regulation of cellular response to stress' (%s)" % MA_LOC),
    ("MAMAT-E-DRG-BP-2", "GO BP 'regulation of cellular response to stress'", "DRG", M, "same sentence (%s)" % MA_LOC),
    ("MAMAT-E-DRG-CC-1", "GO CC 'centrosome'", "DRG", M,
     "'DRGs exhibited enrichment in cellular components such as the centrosome and Golgi membrane' (%s)" % MA_LOC),
    ("MAMAT-E-DRG-CC-2", "GO CC 'Golgi membrane'", "DRG", M, "same sentence (%s)" % MA_LOC),
    ("MAMAT-E-DRG-MF-1", "GO MF 'histone binding'", "DRG", M,
     "'... molecular functions including histone binding and molecular adaptor activity' (%s)" % MA_LOC),
    ("MAMAT-E-DRG-MF-2", "GO MF 'molecular adaptor activity'", "DRG", M, "same sentence (%s)" % MA_LOC),
]
for cid, term, lst, sign, pub in MA_E:
    focal = "yes" if cid == "MAMAT-E-URG-BP-1" else "no"
    add(T8, cid, cell_class="claim", claim_form="decoded-list", map=MA_BOTH,
        set_S=("%s (the paper's words; name rule, sections 1.1 / 1.6: the tier in register_sets/NAME_MATCHES.json); %s; %s; tested list "
               "%s (the paper's decoded list)" % (term, GO_RULE, MA_GO_REL, lst)),
        T=MA_T, direction="%s (%s: %s)" % (sign, lst, "positive PLS z, positively associated with FD changes in ASD" if sign == "+"
                                              else "negative PLS z, negatively associated with FD changes in ASD"),
        inference_level=MA_LVL, headline_population=HL_IN_FV_DESC,
        reproduction=MA_REP, published_value_and_location=pub + "; values in Supplementary Table 2 / Fig. 4 (not read; under G1)",
        verdict_counted_in_m="yes", focal=focal, map_index=MAPIDX_MAMAT,
        notes="id: register." + (" Per-row focal of frozen-11 row 7 (Results, gene enrichment, first term stated; register 2.8)." if focal == "yes" else "")
        + MA_CARRIER_TEST)
for cid, lst, sign in [("MAMAT-E-Tissue-URG", "URG", "+"), ("MAMAT-E-Tissue-DRG", "DRG", M)]:
    add(T8, cid, cell_class="claim", claim_form="decoded-list", map=MA_BOTH,
        set_S=("HPA TissueEnrich tissue-specific genes, 'cerebral cortex' (section 1.6 source 3: the release in force at the paper's "
               "submission date; 'S re-derived'); tested list %s" % lst),
        T=MA_T, direction="%s (%s; register 2.8)" % (sign, lst), inference_level=MA_LVL,
        headline_population=HL_IN_FV_DESC,
        reproduction=MA_REP,
        published_value_and_location=("'The URGs and DRGs ... exhibited specific expression patterns in brain tissue, including in the "
                                      "cerebral cortex (Fig. 4C and Supplementary Fig. 2, 3)' (%s)" % MA_LOC),
        verdict_counted_in_m="yes", map_index=MAPIDX_MAMAT, notes="id: register." + MA_CARRIER_TEST)
for cid, lab in [("MAMAT-E-SEA-cerebellum", "Cerebellum"), ("MAMAT-E-SEA-cortex", "Cortex"),
                 ("MAMAT-E-SEA-thalamus", "Thalamus"), ("MAMAT-E-SEA-hippocampus", "Hippocampus")]:
    add(T8, cid, cell_class="claim", claim_form="decoded-list", map=MA_BOTH,
        set_S=("SEA adult brain-region set: %s; tested list URG and / or DRG (not stated)"
               % psi_set(PSI_REGION, "region '%s'" % lab)),
        T=MA_T, direction="two-sided (the list -- URG or DRG -- is not stated; register 2.8)", inference_level=MA_LVL,
        headline_population=HL_IN_FV_DESC,
        reproduction=MA_REP,
        published_value_and_location=("'SEA of adult brain regions demonstrated significant expression of the identified gene sets in key "
                                      "brain regions, including the cerebellum, cerebral cortex, thalamus, and hippocampus' (%s)" % MA_LOC),
        verdict_counted_in_m="yes", map_index=MAPIDX_MAMAT, notes="id: register." + MA_CARRIER_TEST)
for cid, lab in [("MAMAT-E-SEA-Pnoc-cortex", "Pnoc+ cortical neurons"), ("MAMAT-E-SEA-cholinergic-striatum", "cholinergic striatal neurons")]:
    add(T8, cid, cell_class="claim", claim_form="decoded-list", map=MA_BOTH,
        set_S=("SEA cell-type set: %s; tested list URG and / or DRG (not stated)"
               % psi_set(PSI_CELL, "cell type '%s'" % lab)),
        T=MA_T, direction="two-sided (the list is not stated; register 2.8)", inference_level=MA_LVL,
        headline_population=HL_IN_FV_DESC,
        reproduction=MA_REP,
        published_value_and_location=("'cell type SEA revealed higher expression levels in specific neuronal populations, such as Pnoc+ "
                                      "neurons in the cortex and cholinergic neurons in the striatum (Supplementary Fig. 4, 5)' (%s)" % MA_LOC),
        verdict_counted_in_m="yes", map_index=MAPIDX_MAMAT, notes="id: register." + MA_CARRIER_TEST)
for cid, S, sign, pub, nc in [
        ("MAMAT-E-URG-KEGG", "KEGG pathways of Fig. 4B for the URGs (terms not in the text; Supplementary Table 2, read under G1); section 1.6 "
                             "KEGG rule (ii): the obtainable KEGG release closest in date to the paper's submission (2024-08-14), Enrichr "
                             "snapshots counting as releases -- %s (computed by the S-build, register section 1.11; 'release substituted'); "
                             "the pathways reached by the name rule" % KEGG_MAMAT, "+ (URG)",
         "Fig. 4B 'enriched KEGG pathways of URGs' (terms not in the text; Supplementary Table 2)", "UNDETERMINED: the Fig. 4B KEGG terms; the family counts once (section 1.1)"),
        ("MAMAT-E-KEGG-neurodeg", "KEGG 'neurodegeneration pathways' (no exact KEGG name; rule G names no set)",
         "two-sided (DRG in Results vs URG in Discussion: contradictory)",
         "Results: 'an association of DRGs with neurodegeneration pathways, as revealed by KEGG analysis'; Discussion: 'neurodegeneration "
         "pathways enriched among URGs'", "UNDETERMINED: no exact KEGG name; the family counts once (section 1.1)"),
        ("MAMAT-E-CSEAdev-URG", "CSEA BrainSpan stage x region pSI sets (" + PSI_PIN + ", pSI < .05): 'from late "
                                "fetal development onward, across "
                                "various brain regions including the cortex, and subcortex (hippocampus, striatum, thalamus)' -- stage ranges "
                                "name no bin (rule G)", "+ (URG)",
         "'URGs were expressed in the brain from late fetal development onward, across various brain regions including the cortex, and "
         "subcortex (hippocampus, striatum, thalamus)' (Results)", "UNDETERMINED: stage ranges name no bin; the family counts once (section 1.1)"),
        ("MAMAT-E-CSEAdev-DRG", "CSEA BrainSpan stage x region pSI sets (" + PSI_PIN + ", pSI < .05): 'from early to mid-fetal "
                                "development onward ... cortex and "
                                "subcortex (amygdala, thalamus)' -- stage ranges name no bin (rule G)", M + " (DRG)",
         "'DRGs exhibited expression from early to mid-fetal development onward, across several brain regions including the cortex and "
         "subcortex (amygdala, thalamus)' (Results)", "UNDETERMINED: stage ranges name no bin; the family counts once (section 1.1)")]:
    add(T8, cid, cell_class="family", claim_form="decoded-list", map=MA_BOTH, set_S=S,
        T="descriptor family (register 2.8): " + MA_T, direction=sign, inference_level=MA_LVL,
        status=MA_COND + "; S undefined until the cells are named (descriptor family)",
        headline_population="out: descriptor family (register 2.8; section 1.1)", reproduction=MA_REP,
        published_value_and_location=pub, n_cells=nc,
        map_index=MAPIDX_MAMAT + " -- the convention applied to the descriptor family's two-cohort cells",
        notes="id: draft. Descriptor family (register 2.8), not claims." + MA_CARRIER_TEST)

# ====================================================================================================================
# target 9 -- Vairam / Roy 2026
# ====================================================================================================================
VR_FACTS = ("facts recorded for the operator (register 2.9): the map pools ABIDE I and ABIDE II (ABIDE II preprocessed from raw data), "
            "no derived map is deposited, and the repository lacks the null, PLSC and LOSO code; running it would open ABIDE II imaging, "
            "which A1 never does (prereg sections 2, 8), and would be a reconstruction (prereg section 5.1)")
VR_STATUS = VR_DEFER + "; " + VR_FACTS
T9 = Target(9, "vairam2026hyperhypo", "8", "none",
            map=("Delta-FC node-strength map (mean node strength ASD - CTL after NeuroCombat; AAL3, 170 ROIs; ABIDE I PCP nofilt_noglobal + "
                 "ABIDE II preprocessed locally with C-PAC 1.8; 885 ASD / 852 CTL); no derived map deposited "
                 "(literature/notes/vairam2026hyperhypo.md)"),
            analysis_class="none", route="none: deferred, no route registered (register 2.9)", status=VR_STATUS,
            headline_population=HL_VR,
            dependencies="all cells share the Delta-FC map and the PLSR ranking; VR-E1-E4 leading-edge genes overlap (172 genes: 69 hyper / 103 hypo)")
VR_NOTE = ("Definitions from the literature note (read full-text 2026-09-22); A2, which was to reproduce it, is superseded by A3 "
           "(PROGRAMME.md). Gate none: deferred (prereg section 5.1), nothing of it is opened (register sections 0, 2.9); v3 read it "
           "'not auditable', v4 'deferred' (register section 9 NF5).")
add(T9, "VR-C1", cell_class="claim", claim_form="component",
    set_S="none (component claim); X = the authors' AHBA z-scored region x gene matrix (not abagen; empty parcels zero-filled)",
    T=("component level (register 2.9): T = cumulative R^2 of the paper's two PLSR components, refit on every permutation and "
       "surrogate (section 1.4); not computed (deferred)"),
    direction="+ (upper tail: component R^2 above the null)",
    inference_level=("spatial null only: the model-level BrainSMASH check (10,000 surrogates, PLSR refit; test statistic R^2 per LV) -- "
                     "run and failed for LV1 (p_spin .696; LV2 .006, LV3 .063, LV4 .018, LV5 .003) (register 2.9)"),
    reproduction="descriptive (amendment 4 section 2): LV1 BrainSMASH p .696 (not run: deferred)",
    published_value_and_location=("PLSR of Delta-FC node strength on AHBA (AAL3; 2 components per the text); BrainSMASH LV1 p = 0.696 "
                                  "(note 'null models'; the authors: 'not a gene-level spatial-null inference')"),
    notes="id: register. " + VR_NOTE)
for cid, path, nes, fdr in [("VR-E1", "circadian entrainment", "2.043", "< 0.001"), ("VR-E2", "glutamatergic synapse", "2.064", "0.0014"),
                            ("VR-E3", "retrograde endocannabinoid signalling", "2.005", "0.0014"),
                            ("VR-E4", "long-term potentiation", "1.865", "0.010")]:
    add(T9, cid, cell_class="claim", claim_form="PLS-enrichment",
        set_S=("KEGG '%s' (Enrichr KEGG_2021_Human: the library the paper names -- 'KEGG 2021 Human' via gseapy prerank -- obtained "
               "2026-09-26 at the named release: section 1.6 source 3, R12, no 'release substituted'; the pathway reached by the name "
               "rule of sections 1.1 / 1.6) -- built, not run (deferred)" % path),
        T=T_PLSE + " (not computed: deferred)",
        direction="+ (positive NES = hyperconnectivity-associated; register 2.9)",
        inference_level="gene null only (uniform): gseapy prerank GSEA, 1,000 permutations, seed 42 (register 2.9)",
        reproduction="descriptive (amendment 4 section 2): NES %s, P_FDR %s (not run: deferred)" % (nes, fdr),
        published_value_and_location="NES %s (P_FDR %s) (note 'Key claims': top GSEA results, KEGG 2021)" % (nes, fdr),
        focal="yes" if cid == "VR-E1" else "no",
        notes=("id: register. " + ("Per-row focal of frozen-11 row 8 (the first GSEA result stated; register 2.9, section 4: status "
                                   "'deferred (prereg section 5.1)'). " if cid == "VR-E1" else "") + VR_NOTE))
add(T9, "VR-N1", cell_class="claim", claim_form="other",
    set_S="the 172 leading-edge genes (69 hyper / 103 hypo) binned into 8 neurochemical systems (KEGG + UniProt; multi-membership allowed)",
    T="none: not testable as stated -- a comparison of two lists' composition (register 2.9)",
    direction="n/a: no registered T (not testable as stated)", inference_level="other: unstated test (section 1.3)",
    status=(VR_DEFER + "; not testable as stated: a comparison of two lists' composition, no registered T form (register 2.9, "
            "section 1.4); " + VR_FACTS),
    reproduction="descriptive (amendment 4 section 2): P = .257 (not run: deferred)",
    published_value_and_location=("P = 0.257: 'hyper and hypo gene sets differ in neurotransmitter composition' not supported (note 'Key "
                                  "claims': 'did not differ in neurotransmitter-system composition')"),
    notes="id: register. v2 read VR-N1 as published-null; v3 and v4 register it as not testable as stated (register 2.9). " + VR_NOTE)

# ====================================================================================================================
# target 10 -- Liu 2026
# ====================================================================================================================
LIU_S = ("merged ASD = Satterstrom 2020 (102) ∪ Grove 2019 MAGMA (25) ∪ SFARI score 1 at the section 1.6 release rule (the earliest "
         "release whose score-1 count equals the paper's 233, else the last release before the paper's submission) (register 2.10); "
         "HGNC symbols; external; S-build ungated. S-build outcome (register section 1.11 item 2; v6.7 (2), the uniform archive "
         "rule, the served release label read -- N2): %s; components %s against the paper's %s"
         % (sset("liu_merged_asd")["source"]["release"],
            ", ".join("%s %d" % (k, v) for k, v in sset("liu_merged_asd")["components"].items()),
            ", ".join("%s %d" % (k, v) for k, v in sset("liu_merged_asd")["paper_component_sizes"].items())))
LIU_BS = ("no spatial map: BrainSpan RNA-seq genes matrix (expression_matrix.csv, sha256 "
          "e8d98aa02874f6b12fe7e071f4f88435b88256b6e5c4ba1d799e7b82aad28ee2; 52,376 genes x 524 samples); per-sample rank-biserial r of S "
          "vs the rest (the paper's statistic, SD3)")
LIU_T_NCT = ("gene-set-only (Level 2 only; no amendment-3 verdict): %s; G1-G5 descriptors on the paper's per-sample statistic (G5 labelled "
             "'matching variable = tested quantity; expected null by construction'; register 2.10); p-values read 'no calibrated test'")
T10 = Target(10, "liu2026spatiotemporal", "9", "none", analysis_class="none", route="none: no parcel map (gene-set-only)",
             set_S=LIU_S, dependencies="T1, T2, T4, T5, T6 share S (merged ASD); T3 shares S")
add(T10, "LIU-T1", cell_class="claim", claim_form="gene-set-only", map=LIU_BS,
    T=LIU_T_NCT % ("T = mean r over prenatal samples (aged in pcw) - mean r over postnatal samples (mos / yrs)"),
    direction="+ (prenatal enrichment)", inference_level="none: no test of the timing (clustering and moving-average peak stage)",
    status="no calibrated test: no spatial map (amendment 5 section 3; register 2.10)", headline_population=HL_IN_NCT,
    reproduction="descriptive (amendment 4 section 2): per-sample r vs the SD3 'ASD' column; prenatal-cluster membership (Fig. 2b)",
    published_value_and_location=("ASD in the 'prenatal' cluster: 'most of the early onset psychiatric disorders -- including ASD ... -- "
                                  "demonstrated relatively early developmental enrichment of risk gene expression' (Results "
                                  "'Developmental expression enrichment patterns...'; Fig. 2a-d; Supp Fig. 1b-c); SD3 per-sample r"),
    notes=("id: register. Frozen-11 row 9 has no focal (register 2.10, section 4: no spatial map, no full-verdict form); v2 had "
           "LIU-T1."))
add(T10, "LIU-T2", cell_class="claim", claim_form="gene-set-only", map=LIU_BS,
    T=LIU_T_NCT % ("T = mean r (thalamus samples: MD, DTH) - mean r (frontal-cortex samples: DFC, VFC, MFC, OFC)"),
    direction=M + " (relative thalamic depletion; only the thalamus contrast is significant)",
    inference_level="none: rstatix pairwise t-test (pooled SD, FDR) across structures, parametric",
    status="no calibrated test: no spatial map (amendment 5 section 3; register 2.10)", headline_population=HL_IN_NCT,
    reproduction="descriptive (amendment 4 section 2): p only (SD4 frontal cortex vs thalamus)",
    published_value_and_location=("SD4 ASD, frontal_cortex vs thalamus: p = 7.12e-05, p.adj = 0.000712 ('risk genes for IQ and ASD showed "
                                  "minimal subcortical enrichment relative to cortical areas', Fig. 3a legend; Results 'Spatial enrichment "
                                  "patterns...')"),
    notes=("id: register. Samples from the same donors treated as independent (draft). The SD4 contrasts of frontal cortex against "
           "striatum, cerebellum and hippocampus are registered as descriptor cells (LIU-T2-STR, -CBC, -HIP; register 2.10, v4); the "
           "other SD4 structures (n.s., draft section 2) are not registered."))
LIU_T45_REP = ("4.1 check (section 1.5, register 2.10): the claim's statistic computed from our per-label rank-biserial r vs the same "
               "statistic computed from the paper's SD7 values (+-.05); the flag does not move the population (the claim cannot survive, "
               "section 1.2)")
add(T10, "LIU-T4", cell_class="claim", claim_form="gene-set-only",
    map=("no spatial verdict map: AHBA samples assigned to DK labels by abagen ('re-derived': the paper's manual AHBA -> ENIGMA mapping is "
         "unpublished; the paper: 231 AHBA structures -> 37-39 ENIGMA labels, SD7)"),
    T=LIU_T_NCT % ("T = mean r over the cortical labels"), direction="+ (widespread neocortical enrichment)",
    inference_level="none: no test reported for 'widespread'",
    status="no calibrated test: no spatial map (amendment 5 section 3; register 2.10)", headline_population=HL_IN_NCT,
    reproduction=LIU_T45_REP,
    published_value_and_location=("'risk genes for ASD, ADHD, and BIP showed widespread expression enrichment across the neocortex' (Results "
                                  "'Assessing the biological relevance...'; Fig. 5a); SD7 ASD column (per-label r)"),
    notes="id: register. The literature note reports a cortical SD of ~0.005 in r (a flat map) (draft).")
add(T10, "LIU-T5", cell_class="claim", claim_form="gene-set-only",
    map="no spatial verdict map: AHBA samples assigned to DK labels by abagen ('re-derived'), as LIU-T4",
    T=LIU_T_NCT % ("T = r(hippocampus) - mean r(other labels)"), direction="+ (hippocampal enrichment)",
    inference_level="none: per-region r only, no test",
    status="no calibrated test: no spatial map (amendment 5 section 3; register 2.10)", headline_population=HL_IN_NCT,
    reproduction=LIU_T45_REP,
    published_value_and_location=("'the hippocampus showed enrichment for risk genes associated with ASD, BIP, SZes, and epilepsy' (Results "
                                  "'Assessing the biological relevance...'; Fig. 5a); SD7"),
    notes="id: register.")
for code, lab, padj in [("STR", "striatum", "0.0863"), ("CBC", "cerebellum", "0.0863"), ("HIP", "hippocampus", "0.064")]:
    add(T10, "LIU-T2-" + code, cell_class="descriptor", claim_form="gene-set-only", map=LIU_BS,
        T="descriptor (section 1.1): " + LIU_T_NCT % ("T = mean r (%s samples: %s) - mean r (frontal-cortex samples: DFC, VFC, MFC, OFC)"
                                                      % (lab, code)),
        direction="two-sided (descriptor cell)",
        inference_level="none: rstatix pairwise t-test (pooled SD, FDR) across structures, parametric (as LIU-T2)",
        status="no calibrated test: no spatial map (amendment 5 section 3; register 2.10); descriptor cell",
        headline_population=HL_DESC,
        reproduction="descriptive (amendment 4 section 2): p.adj only (SD4 frontal cortex vs %s)" % lab,
        published_value_and_location=("SD4 ASD, frontal_cortex vs %s: p.adj = %s (SD4; raw p not transcribed by the draft); not "
                                      "significant after FDR (draft section 2, LIU-T2 row)" % (lab, padj)),
        dependencies="shares S and the frontal-cortex samples with LIU-T2",
        notes=("id: compiler (register 2.10, v4: 'the SD4 contrasts of frontal cortex against striatum, cerebellum and hippocampus are "
               "registered as descriptor cells'; %s = BrainSpan structure %s, pinned there). Ungated." % (lab, code)))
add(T10, "LIU-T3", cell_class="published-null", claim_form="set-vs-map",
    map=("ENIGMA-ASD meta-analysis d_icv: cortical thickness (asd_meta-analysis_case-controls_CortThick.csv, sha256 "
         "ee076971be6688bc99106fce4a7198a3bd927d183adb245f9810d6f71efe4f29) + subcortical volume (asd_meta-analysis_case-controls_SubVol.csv, "
         "sha256 b2b0b02c260ec87c6ab22f40e6162ab8a475dab373390be1edd465910ca62066), MICA-MNI/ENIGMA @ b08974b; L/R averaged as the paper; "
         "lateral ventricles excluded; " + ident("liu2026spatiotemporal", "CortThick") + "; SubVol: "
         + ident("liu2026spatiotemporal", "SubVol").split(": ", 1)[1] + "; " + ID_RULE),
    analysis_class="V-DK",
    route=("native: L/R-averaged values placed on the left V-DK parcels (cortex + subcortex, two classes; section 1.7 bilateral-average rule)"),
    T=T_SVM, direction="two-sided (published-null; register 2.10)",
    inference_level="none: Spearman, parametric; FDR across 8 disorders",
    status="auditable (under G2)", headline_population=HL_PN,
    reproduction=("4.1 check (section 1.5, register 2.10): Spearman rho of the paper's per-parcel rank-biserial enrichment of S "
                  "(recomputed on our matrix) with y vs R = -0.34 (+-.05)"),
    published_value_and_location=("Spearman R = -0.34, P_FDR = 0.057: 'did not reach the FDR significance threshold but showed consistent "
                                  "trend-level effects' (Results 'Assessing the biological relevance...'; Fig. 5e)"),
    gate="G2", verdict_counted_in_m="yes",
    dependencies="map family shared with Patel / Giacomel / Hansen (ENIGMA-ASD cohorts); S shared with T1, T2, T4, T5",
    notes=("id: register. The asdg-lit recomputation on this map is declared (register section 0 item 2: rho -.349 overall, -.51 cortex, "
           "+.08 subcortex, -.04 with the mega table). Mixed measures (thickness, volume) in one map. Published-null reading (section "
           "1.1): 'detectable by the verdict (the published analysis reported none)', with no extrapolation label (25 <= m <= 1,000 in "
           "the planted class V-DK); or 'not detectable at this power (as published)', with the label 'power not measured at this set "
           "size (m > 100)'; by the S-build's m, which governs: %d genes of S in the V-DK universe (%d HGNC-mapped; the paper's "
           "counts 102, 25 and 233 before the union; register section 1.11 item 2)."
           % (sset("liu_merged_asd")["universe"]["V-DK"]["n_in_universe"], sset("liu_merged_asd")["n_hgnc"])))
add(T10, "LIU-T6", cell_class="claim", claim_form="gene-set-only",
    map="no spatial map: BrainSpan WGCNA modules (41; minModuleSize 40) -- module memberships unpublished",
    set_S=LIU_S + "; tested against module membership",
    T="gene-set-only: T = module-membership overlap (OR) of S (draft); never computed (not auditable)",
    direction="+ (over-representation)",
    inference_level=("gene null only (uniform): Fisher's exact (gmodels::CrossTable), FDR within ASD across 41 modules (register 2.10) "
                     "[draft reading 'none' recorded]"),
    status="not auditable: module memberships unpublished; re-running WGCNA would be a reconstruction (register 2.10)",
    headline_population=HL_IN_NA,
    reproduction="descriptive (amendment 4 section 2): module ORs vs SD10 (not run: not auditable)",
    published_value_and_location=("SD10 ASD raw P < .05: turquoise P 6.6e-18, OR 3.93; darkgreen 8.4e-6, OR 5.23; darkorange .0072, OR 3.71; "
                                  "skyblue .012, OR 3.81; yellowgreen .046, OR 3.91; text: M14 (prefrontal deficits incl. ASD), M16 (early "
                                  "fetal deficit incl. ASD), M10 'marginal associations with ASD (PFDR = 0.076)' (Results, WGCNA section; Fig. 6c)"),
    notes=("id: register. One registered claim covering the modules the text names (M14, M16; M10 marginal), counted once. Gate none "
           "(register 2.10). LIU-T7 is not a claim and is not registered (register 2.10)."))

# ====================================================================================================================
# target 11 -- Xing 2026
# ====================================================================================================================
XI_STATUS = "not auditable: the axis region sets are unpublished (register 2.11)"
T11 = Target(11, "xing2026interpretable", "10", "none",
             analysis_class="V-AAL", route="native: AAL-116 incl. cerebellum / vermis (V-AAL; draft route; not auditable)",
             T=("decoded-list (amendment 4 section 2) on a binary map: T = mean over S of the per-gene Pearson (point-biserial) r between y "
                "and expression on the section 3.1 V-AAL matrix (draft); never computed (not auditable)"),
             inference_level=("gene null only (uniform): hypergeometric top-decile over-representation and a one-sided Mann-Whitney U of S vs "
                              "non-S genes; the paper's own non-spatial ROI-label permutation was run and failed (register 2.11) [draft "
                              "reading 'other' recorded]"),
             status=XI_STATUS,
             dependencies="cells of one axis share y; SFARI subsets nested (high-confidence, syndromic within all); the four axes share the ranking pipeline")


def xing_map(axis):
    return ("binary indicator over AAL-116 for the %s axis (1 = axis-related region: endpoints of the axis's network-pair connections; "
            "ABIDE I PCP, N 778; SHAP of an EN100 + LightGBM classifier) -- not published" % axis)


XI_S = {"all": "SFARI Gene, all genes (1,277; 1,132 in the paper's matrix)", "hc": "SFARI Gene, high-confidence genes",
        "syn": "SFARI Gene, syndromic genes"}
XI_SRULE = ("; release not stated: section 1.6 SFARI rule (the earliest release whose count equals the paper's stated count, else the "
            "last release before the paper's submission); definitions of high-confidence / syndromic as the release defines them")
for cid, sub, pub in [
        ("XING-FPV-all", "all", "ratio 1.598 (181 observed vs 113.3 expected), hypergeometric FDR 5.62e-10; rank AUC 0.5559, FDR 2.06e-9; ROI-label permutation P 0.064, FDR 0.472"),
        ("XING-FPV-hc", "hc", "ratio 1.871 (44 vs 23.5), FDR 1.28e-4; AUC 0.5532, FDR 0.0102; ROI-permutation P 0.079, FDR 0.472"),
        ("XING-FPV-syn", "syn", "ratio 1.535 (45 vs 29.3), FDR 0.0057; AUC 0.5498, FDR 0.0102; ROI-permutation P 0.182, FDR 0.536")]:
    add(T11, cid, cell_class="claim", claim_form="decoded-list", map=xing_map("frontoparietal/executive-visual (FPV)"),
        set_S=XI_S[sub] + XI_SRULE, direction="+ (S shifted to higher axis scores)", headline_population=HL_IN_NA,
        reproduction="descriptive (amendment 4 section 2): hypergeometric ratio / FDR and rank AUC (not run: not auditable)",
        published_value_and_location=pub + " (paper section 3.5, printed p. 22; Fig. 4A-B; Supplement 4)",
        focal="yes" if cid == "XING-FPV-all" else "no",
        notes="id: register." + (" Per-row focal of frozen-11 row 10 (register section 4); not auditable. Supplement 6 not registered "
                                 "(register 2.11)." if cid == "XING-FPV-all" else ""))
for cid, sub, pub in [("XING-LPS-all", "all", "ratio 1.377, hypergeometric FDR 9.37e-5, AUC 0.522, FDR 0.019, permutation P 0.223"),
                      ("XING-LPS-hc", "hc", "ratio 1.701, FDR 0.0017, AUC 0.502, FDR 0.727, permutation P 0.172"),
                      ("XING-LPS-syn", "syn", "ratio 1.262, FDR 0.164, AUC 0.501, FDR 0.727, permutation P 0.468")]:
    add(T11, cid, cell_class="descriptor", claim_form="decoded-list", map=xing_map("limbic-parietal/sensorimotor (LPS)"),
        set_S=XI_S[sub] + XI_SRULE, direction="+ (draft; descriptor)", headline_population=HL_DESC,
        reproduction="descriptive (amendment 4 section 2): ratio / FDR / AUC (not run: not auditable)",
        published_value_and_location=pub + " (Supplement 4; paper section 3.5: 'weaker and less consistent evidence of SFARI enrichment')",
        notes="id: draft. Register 2.11: the limbic-parietal rows are descriptor cells.")
for ax_id, ax_name in [("CFP", "cerebellar-frontoparietal"), ("LC", "limbic-cerebellar")]:
    for sub in ["all", "hc", "syn"]:
        add(T11, "XING-%s-%s" % (ax_id, sub), cell_class="descriptor", claim_form="decoded-list", map=xing_map(ax_name),
            set_S=XI_S[sub] + XI_SRULE, direction="two-sided (descriptor cell; null statement)", headline_population=HL_DESC,
            reproduction="descriptive (amendment 4 section 2): ratio / FDR (not run: not auditable)",
            published_value_and_location=("ratios 1.01-1.23 across the two axes, all FDR >= 0.24 (Supplement 4; paper section 3.5: 'the "
                                          "cerebellar-frontoparietal and limbic-cerebellar patterns showed no consistent enrichment')"),
            notes="id: compiler. Draft: null statements are 'descriptors, not claims'; register 2.11 silent; rule G.")

# ====================================================================================================================
# target 12 -- Wan 2026
# ====================================================================================================================
T12 = Target(12, "wan2026abide2multiplex", "11", "G1", analysis_class="none", route="none: atlas unknown; not auditable",
             T="none: T undefinable from the abstract (register 2.12); never computed",
             direction="n/a: T undefinable (register 2.12); the draft would use two-sided (sign conventions unknown)",
             inference_level="other: unstated (register 2.12)",
             status=("not auditable: full text and methods unobtainable; claims undefinable from the abstract; no author contact (prereg "
                     "section 5.1: 'only if maps / gene lists are obtained from the authors') (register 2.12)"),
             headline_population=HL_IN_NA,
             reproduction="descriptive (amendment 4 section 2): unknown (not run: not auditable)",
             dependencies="WAN-1 and WAN-2 are two layers of one multiplex analysis (ABIDE II, 240 ASD / 340 TC)")
WAN_NOTE = ("The supplementary docx (mmc1, 10,884,294 B) is not used to define claims after the freeze (register 2.12). Draft: likely "
            "decoded-list enrichment or PLS enrichment -- cannot be fixed without the methods.")
add(T12, "WAN-1", cell_class="claim", claim_form="other",
    map="white-matter-layer multiplex case-control topology map (atlas unknown; ABIDE II; 240 ASD / 340 TC); not found",
    set_S="pathway sets 'immune regulation', 'cellular metabolism' (tested against an AHBA-derived list; method unknown)",
    published_value_and_location=("abstract: 'widespread whole-brain topological reorganization in white matter multiplex networks, "
                                  "involving the corpus callosum and major fiber tracts, with gene expression enriched in immune regulation "
                                  "and cellular metabolism pathways'"),
    notes=("id: register. Frozen-11 row 11 has no focal (register 2.12, section 4: no claim can be given a form); v2 had WAN-1. "
           + WAN_NOTE))
add(T12, "WAN-2", cell_class="claim", claim_form="other",
    map="grey-matter-layer multiplex clustering case-control map (atlas unknown; ABIDE II); not found",
    set_S="pathway sets 'cell adhesion', 'synaptic transmission' (method unknown)",
    published_value_and_location=("abstract: 'The gray matter multiplex networks exhibited localized hyper-clustering centered on the "
                                  "cortico-striatum-thalamic-cortical circuit and the default mode network associated with genes implicated "
                                  "in cell adhesion and synaptic transmission'"),
    notes="id: register. " + WAN_NOTE)

# ====================================================================================================================
# target 13 -- Pagani 2026 (added)
# ====================================================================================================================
PAG_Y = {
    "hypo": ("hypo map: GitHub functional-neuroimaging/biological_subtyping @ef58cf1 cognitive_maps/00_mean_regressed_global_connectivity_maps/"
             "stats_two_sample_ASD_hypo_vs_CTR_cohensd_global_connectivity_voxelwise_smoothed.nii.gz (628,525 B; git blob "
             "1bfd99e31d3df0ac52862989d87a0165ca1dc600), asserted byte-equal to NeuroVault 14698 image 798768 (on a difference the GitHub file "
             "governs); the paper-cited copy (section 1.7 (e)); voxelwise MNI Cohen's d (negative d = hypoconnectivity)"),
    "hyper": ("hyper map: same folder, stats_two_sample_ASD_hyper_vs_CTR_cohensd_global_connectivity_voxelwise_smoothed.nii.gz (629,343 B; git "
              "blob 9106aaf50bebd7f4e9689f5217193c6f7188f30a), asserted byte-equal to NeuroVault 14698 image 798767; paper-cited copy; positive "
              "d = hyperconnectivity"),
}
PAG_Y = {k: v + "; " + ident("pagani2026crossspecies", "%s Cohen's d map" % k) + "; NeuroVault copy: "
         + ident("pagani2026crossspecies", "image %s" % ("798768" if k == "hypo" else "798767")).split(": ", 1)[1] + "; " + ID_RULE
         for k, v in PAG_Y.items()}
T13 = Target(13, "pagani2026crossspecies", "added", "G1", analysis_class="V-AAL",
             route=ROUTE_VOL_AAL + "; V-AAL because the decoder mask the paper used is unstated, so the class covering every tissue is used "
                                   "(NeuroVault brain coverage 67.9 %) (register 3.1)",
             T=T_DL, direction="two-sided (sign composition of the decoded lists unstated; prereg section 4.7), labelled",
             inference_level=("gene null only (uniform): hypergeometric vs the 16,796-gene background (section 1.3) [amendment 4 section 1: "
                              "'no spatial or gene null' -- both readings recorded; draft reading 'none' recorded]"),
             status="auditable (under G1)", headline_population=HL_ADDED, verdict_counted_in_m="yes",
             dependencies=("PAG-C1, C3-C6, C9, C10 share the hypo map; C2, C7, C8, C11, C12 the hyper map; overlapping S (SynGO vs the synaptic "
                           "Reactome classes and modules); shares the CMI collection with Segura and ABIDE II NYU with Benkarim / Park"))
PAG_LOC = "Results 'Hypoconnectivity and hyperconnectivity in humans recapitulate molecular pathways identified in rodent models'"
PAG = [("PAG-C1", "hypo", "ASD DE genes: all genes of the 24 co-expression modules differentially expressed in autism post-mortem tissue (Gandal 2022; Results ref. 16; the Methods [25] mis-cites)", "OR = 1.87, P_FDR = 10^-3 (Fig. 5a)"),
       ("PAG-C2", "hyper", "ASD DE genes (as PAG-C1)", "OR = 1.88, P_FDR = 10^-3 (Fig. 5a)"),
       ("PAG-C3", "hypo", "Reactome 'transmission across chemical synapses'", "OR = 2.26, P_FDR = 10^-7 (Fig. 5b)"),
       ("PAG-C4", "hypo", "SynGO", "OR = 2.19, P_FDR = 10^-14 (Fig. 5b)"),
       ("PAG-C5", "hypo", "Reactome 'protein-protein interaction at synapses'", "OR = 0.92, P_FDR = 10^-6 (Fig. 5b) -- an OR < 1 reported as an enrichment; registered as printed (register 3.1)"),
       ("PAG-C6", "hypo", "Reactome 'membrane trafficking'", "OR = 1.44, P_FDR = 10^-2 (Fig. 5b)"),
       ("PAG-C7", "hyper", "Reactome 'cytokine signaling in immune system'", "OR = 1.66, P_FDR = 10^-3 (Fig. 5b)"),
       ("PAG-C8", "hyper", "Reactome 'innate immune system'", "OR = 1.43, P_FDR = 10^-2 (Fig. 5b)"),
       ("PAG-C9", "hypo", "Gandal 2022 module 'vesicle transport and release'", "OR = 5.14, P_FDR = 10^-56 (Fig. 5c)"),
       ("PAG-C10", "hypo", "Gandal 2022 module 'synaptic vesicles and plasticity'", "OR = 4.38, P_FDR = 10^-26 (Fig. 5c)"),
       ("PAG-C11", "hyper", "Gandal 2022 module 'immune response'", "OR = 3.57, P_FDR = 10^-13 (Fig. 5c)"),
       ("PAG-C12", "hyper", "Gandal 2022 module 'reactive microglia'", "OR = 1.79, P_FDR = 10^-2 (Fig. 5c)")]
for cid, which, S, pub in PAG:
    img = "798768" if which == "hypo" else "798767"
    add(T13, cid, cell_class="claim", claim_form="decoded-list", map=PAG_Y[which],
        set_S=(("the list Supplementary Table 3 (MOESM4_ESM.xlsx, 224,528 B; built under G1) presents as the set's input membership "
                "(source 1, by the section 1.6 source-1 criterion: its decoded genes, a result on the paper's own maps, never qualify) "
                "and corroborated -- Jaccard >= .80 with the comparator built before the freeze (v6.6 B2: register_sets/%s.json, "
                "pinned by sha256 in carrier_tests.json, B1); else that comparator ('S re-derived'): %s -- the set: %s"
                % (COMP66_PAGANI[cid][0], COMP66_PAGANI[cid][1], S)) if COMP66_PAGANI[cid][0] else
               ("%s: not auditable (S undefined: comparator not buildable pre-freeze; v6.6 B2) -- %s; no list Supplementary Table 3 "
                "holds could be corroborated (register 1.6)" % (S, COMP66_PAGANI[cid][1]))),
        reproduction=("descriptive (amendment 4 section 2): NeuroVault decoder output for image %s (fetched under G1), FDR q < .05, genes "
                      "highly expressed in brain (16,796), shared-gene removal between the two subtype lists; hypergeometric OR, p and "
                      "Jaccard with Supplementary Table 3 vs the published OR" % img),
        published_value_and_location=pub + "; " + PAG_LOC,
        notes=("id: register." + (" Focal-for-description of the added target (register 3.1)." if cid == "PAG-C1" else "")
               + " The synaptic-vs-immune subtype dissociation is not registered (register 3.1)."
               + (" Recorded, not registered (section 1.1: collective non-enrichment statements without a defined set): hyper 'did not "
                  "show enrichment for synaptic ontologies (all P FDR > 0.05)'; 'no enrichment for bipolar disorder, psoriasis, dementia, "
                  "ADHD, schizophrenia'; 'no enrichment for transcriptional mechanisms'; the Fig. 5b / 5c grid cells beyond the text's "
                  "'for example' cells (draft section 2)." if cid == "PAG-C1" else "")))

# ====================================================================================================================
# target 14 -- Benkarim 2021 (added)
# ====================================================================================================================
BK_Y = {"SD": ("SD t-map: NeuroVault 8667 image 404555 'sdistRaw' (sdist_dil.nii.gz, 543,871 B; MNI152NLin2009cAsym volume; n = 329; "
               "attribution: metadata (version inferred) -- later than collections 8655 / 8657 / 8658; 404560 excluded as a mislabelled "
               "entropy file) (section 1.7); " + ident("benkarim2021connectivity", "404555") + "; " + ID_RULE),
        "DD": ("DD t-map: NeuroVault 8667 image 404554 'edistRaw' (edist_dil.nii.gz, 541,677 B; same attribution) (section 1.7); "
               + ident("benkarim2021connectivity", "404554") + "; " + ID_RULE)}
T14 = Target(14, "benkarim2021connectivity", "added", "G1", analysis_class="dk-ctx", route=ROUTE_VOL_DKCTX,
             headline_population=HL_ADDED,
             dependencies=("SD and DD cells share S and the SD-and-DD-selected list; overlapping CSEA sets; ABIDE II (NYU) shared with Park and "
                           "Pagani; BENK-C2's proxy S shared with PARK-C5"))
BK_C1_PUB = ("CSEA FDR-corrected p (Fig. 4b colours; no number in the text): 'associations of our idiosyncrasy descriptors with genes "
             "expressed in the brain from early infancy onwards ... across several brain regions comprising the cerebellum, cortex, and "
             "striatum. Significant gene expressions were predominantly found in adolescence and young adulthood' (Results 'Associations "
             "to cortical morphology and gene expression patterns'; Fig. 4b)")
for region in ["cortex", "cerebellum", "striatum"]:
    for stage, stage_lab in [("adolescence", "Adolescence"), ("youngadulthood", "Young Adulthood")]:
        for mp in ["SD", "DD"]:
            cid = "BENK-C1-%s-%s-%s" % (region, stage, mp)
            add(T14, cid, cell_class="claim", claim_form="decoded-list", map=BK_Y[mp],
                set_S="CSEA developmental set: %s" % psi_set(PSI_DEV, "region '%s' and period '%s'" % (region.capitalize(), stage_lab)),
                T=T_DL, direction="two-sided (the text fixes no sign; the code's upper-tail selection does not count, section 1.4; register 3.2)",
                inference_level=("gene null only (uniform): the CSEA tool's overlap test (test not named) (register 3.2); spin upstream in list "
                                 "construction (1,000 spins per the text; n_perm = 100 in the code) [draft reading 'none' recorded]"),
                status="auditable (under G1)",
                reproduction=("descriptive (amendment 4 section 2): the decoded list re-derived by amendment 4 section 2's per-donor parcel "
                              "recipe (the paper decoded with its own code, not NeuroVault), SD and DD p < .05 and DS >= .5, then CSEA (FDR); "
                              "OR, p and Jaccard with Supplementary Table 4 (Supplementary Information PDF, under G1)"),
                published_value_and_location=BK_C1_PUB, verdict_counted_in_m="yes",
                notes=("id: compiler (register 3.2: BENK-C1 = {cortex, cerebellum, striatum} x {adolescence, young adulthood} x {SD, DD} = 12 "
                       "claims)." + (" Focal-for-description of the added target (register 3.2). Recorded, not registered (section 1.1): the "
                                     "Fig. 4b CSEA cells beyond the named region x period cells (not enumerated in the texts)."
                                     if cid == "BENK-C1-cortex-adolescence-SD" else "")))
for mp, tval in [("SD", "42.270"), ("DD", "28.099")]:
    add(T14, "BENK-C2-" + mp, cell_class="claim", claim_form="other", map=BK_Y[mp],
        set_S=("none: genome-wide ranking of all genes' decoding t; descriptor proxy S = Gandal 2018 ASD-down (section 1.6 pinned: gene-level "
               "table, ASD FDR < .05 with log2FC < 0), labelled 'set proxy'"),
        T=("not testable as stated (section 1.4: a genome-wide robust regression of decoding t on log2FC). Descriptors (register 3.2): the "
           "paper's RLM (gene t ~ log2FC + GC content) on our decoding (reproduction) and the Gandal 2018 ASD-down set proxy with the "
           "decoded-list T (labelled)"),
        direction=("n/a: not testable as stated; proxy descriptor " + M + " (draft: a positive RLM t means ASD-down genes should have mean r < 0)"),
        inference_level="none: parametric robust linear regression (statsmodels RLM) (register 3.2)",
        status="not testable as stated: genome-wide robust regression of decoding t on log2FC (register 3.2)",
        reproduction=("descriptive (amendment 4 section 2): the paper's RLM on our decoding vs t = %s (%s), p < .001; SCZ and BD baselines "
                      "(18.548 / 14.192; 0.577 / -2.014) as the paper's comparison" % (tval, mp)),
        published_value_and_location=("RLM t of the log2FC coefficient, ASD: t = 42.270 (SD) / 28.099 (DD), p < 0.001; SCZ 18.548 / 14.192; "
                                      "BD 0.577 / -2.014 (p .564 / .044) (Results; Fig. 4c; Supp Fig. 9); DE source: Methods [135] Gandal 2018 "
                                      "Science 362 (RNA-seq) vs Results [60] Science 359 (microarray) -- inconsistent"),
        notes="id: draft (C2-%s; register 3.2 names BENK-C2 once; one row per map as for BENK-C1)." % mp)

# ====================================================================================================================
# target 15 -- Dear 2024 (added)
# ====================================================================================================================
ID_NOTE_DEAR = ("workbook " + ident("dear2024corticalgene", "MOESM3") + "; repo check copy: "
                + ident("dear2024corticalgene", "brainchart_maps_dk.csv").split(": ", 1)[1] + "; components: "
                + ident("dear2024corticalgene", "ahba_dme_scores_in_dk.csv").split(": ", 1)[1] + "; " + ID_RULE)
DEAR_OR_NOTE = (" Orientation (register sections 3.3, 1.11 item 10; register_maps/dear_orientation.json): Supp Table 4's orientation is "
                "not stated in any text on disk (quote found: %s); the rule applies at opening (its own header or legend, else "
                "DEAR-C1 / C2 two-sided)." % ("none" if DEAR_OR["supp_table_4_orientation_quote"] is None else "yes"))
T15 = Target(15, "dear2024corticalgene", "added", "G1+G2",
             map=("Supp Table 4 ASD column (regional cortical-volume centile-score differences, BrainChart n ASD = 381; DK-34 bilateral "
                  "average) in 41593_2024_1624_MOESM3_ESM.xlsx (499,436 B; the repo copy data/brainchart_maps_dk.csv @ab7939c compared as a "
                  "check); components = the authors' DK projection outputs/ahba_dme_scores_in_dk.csv @ab7939c (2,637 B); " + ID_NOTE_DEAR
                  + "; y oriented by Supp Table 4's own header or legend (register 3.3)"),
             analysis_class="dk-ctx",
             route="native: bilateral-average DK values placed on the 34 left DK cortical parcels, as the paper (section 1.7)",
             inference_level=("spatial null only: spin permutation (Cornblath method; 5,000 spins per the general Methods), two-sided, FDR "
                              "over 9 tests (3 disorders x 3 components) (register 3.3)"),
             status="auditable (under G1 + G2)", headline_population=HL_ADDED,
             dependencies=("C1-C3 share y and the DK projection; the components are orthogonal embedding axes; BrainChart provenance "
                           "unresolved (ABIDE II / HBN contribution unknown; register sections 0, 3.3)"))
DEAR_LOC = "Results 'Autism and schizophrenia have specific links to C1/C2 and C3'; Fig. 4b"
for cid, comp, sign, val, p in [("DEAR-C1", "C1_DK", "+", "0.49", "0.0002"), ("DEAR-C2", "C2_DK", M, "-0.28", "0.0006")]:
    add(T15, cid, cell_class="claim", claim_form="component", set_S="none: component %s (the authors' DK projection, @ab7939c)" % comp[:2],
        T=t_comp_fixed(comp),
        direction=("%s if Supp Table 4's own header or legend states the shrinkage orientation the paper reads, else two-sided "
                   "(register 3.3, v4); published r %s" % (sign, val)),
        reproduction=("4.1 check: Pearson r(y, %s) vs %s with the published orientation (+-.05; an opposite sign -> 'not reproduced (sign)'; "
                      "the draft's re-mapping rule is removed, register section 9 B21); the MDD and SCZ maps x %s as reproduction "
                      "descriptors (the paper's specificity pattern; draft)" % (comp, val, comp[:2])),
        published_value_and_location="r = %s, P_spin = %s, FDR < 5 %% ('cortical shrinkage in ASD was significantly associated with both C1 and C2'; %s)" % (val, p, DEAR_LOC),
        verdict_counted_in_m="yes",
        notes=("id: register. Counted in m while deferred pending provenance (register section 4); runs only if the provenance "
               "is established." + DEAR_OR_NOTE))
add(T15, "DEAR-C3", cell_class="descriptor", claim_form="component", set_S="none: component C3 (the authors' DK projection)",
    T="descriptor (section 1.1): " + t_comp_fixed("C3_DK"), direction="two-sided (no published direction; register 3.3)",
    reproduction=("4.1 check (descriptor): r vs the Fig. 4b value if printed (read under G1 + G2, once the provenance is established), "
                  "else none; SCZ x C3 (r = 0.43, P_spin .008) as the paper's specificity pattern"),
    published_value_and_location="not in the text (Fig. 4b only, not read); ASD is linked to 'C1 and C2', schizophrenia 'specifically' to C3",
    notes="id: register." + DEAR_OR_NOTE)

# ====================================================================================================================
# target 16 -- Pretzsch 2024 (added)
# ====================================================================================================================
PRE_Y = {"CT": ("y_CT: eTable13 PLS-DA component-1 loadings for cortical thickness, 180 left Glasser parcels (L_*_ROI); "
                "derived/eTable13_glasser360_pls_comp1_loadings.csv sha256 0ef57d234055505918e4f99a674c6e446402b5c2bea69046e2c2429f60df5d67 "
                "(extracted once from jamapsychiatry-e243194-s002.xlsx sha256 f9cc7f8f11e29d95affead7105f1d7f1d160041d5be26fb0a83e03b270ff19b4; "
                "the individual-level sheets eTables 10-11 never used, file deleted); loadings as published (positive = neurotypical "
                "individuals show a more positive change)"),
         "SA": ("y_SA: eTable13 PLS-DA component-1 loadings for surface area, 180 left Glasser parcels; same csv (sha256 "
                "0ef57d234055505918e4f99a674c6e446402b5c2bea69046e2c2429f60df5d67); loadings as published")}
PRE_Y = {k: v + "; " + ident("pretzsch2024patterns", "eTable13") + "; " + ID_RULE for k, v in PRE_Y.items()}
PRE_LVL = ("gene null only (uniform): GeneOverlap hypergeometric / Fisher (background not stated), FDR within family; no spatial null "
           "(explicitly declined, eMethods p. 8) (register 3.4) [amendment 4 section 1: 'no spatial or gene null' -- both readings recorded; "
           "draft reading 'other' recorded]")
PRE_REP = ("descriptive (amendment 4 section 2): the decoded lists re-derived by amendment 4 section 2's per-donor parcel recipe (the paper "
           "used abagen + a per-gene LME, not NeuroVault), pFDR < .01, split by sign; then GeneOverlap; OR and p vs %s (Jaccard impossible: "
           "lists unpublished)")
T16 = Target(16, "pretzsch2024patterns", "added", "G2", analysis_class="dk-ctx", route=ROUTE_GLASSER, T=T_DL, inference_level=PRE_LVL,
             headline_population=HL_ADDED,
             dependencies=("cells on one map share y; the positive and negative lists of a feature are sign complements; GO terms overlap "
                           "(parents / children); NeuroVault 12188 / 12203 rejected (section 1.7)"))
add(T16, "PRE-D1", cell_class="claim", claim_form="decoded-list", map=PRE_Y["SA"],
    set_S=("Gandal 2018 ASD-downregulated genes (section 1.6 pinned: gene-level table, ASD FDR < .05 with log2FC < 0; size reported beside "
           "the paper's K = 764)"),
    direction=M + " (enriched in the SA-negative list; register 3.4)", status="auditable (under G2)",
    reproduction=PRE_REP % "k 38, OR 3.7, p 2.60E-10",
    published_value_and_location=("k 38, OR 3.7, p 2.60E-10 (eTable 4; Abstract: 'downregulated genes in autism ... enrichment odds ratio "
                                  "=3.7; P =2.6 x 10^-10'); reciprocal ASD_upregulated row k 8, OR 0.4, p 1 (the descriptor PRE-D1r)"),
    verdict_counted_in_m="yes", notes="id: register. Focal-for-description of the added target (register 3.4).")
PRE_GO = [  # id, list, term, k, K, p, q
    ("PRE-GO-01", "CT-positive", "GOBP_CELLULAR_RESPONSE_TO_STRESS", 39, 1973, "2.91E-09", "0.0000226"),
    ("PRE-GO-02", "CT-positive", "GOBP_CELL_PROJECTION_ORGANIZATION", 30, 1576, "0.000000497", "0.000918"),
    ("PRE-GO-03", "CT-positive", "GOBP_POSITIVE_REGULATION_OF_RNA_METABOLIC_PROCESS", 33, 1853, "0.00000057", "0.000918"),
    ("PRE-GO-04", "CT-positive", "GOBP_DNA_REPAIR", 17, 584, "0.000000706", "0.000918"),
    ("PRE-GO-05", "CT-positive", "GOBP_CHROMATIN_ORGANIZATION", 18, 652, "0.000000709", "0.000918"),
    ("PRE-GO-06", "CT-positive", "GOBP_CELLULAR_RESPONSE_TO_DNA_DAMAGE_STIMULUS", 21, 868, "0.00000071", "0.000918"),
    ("PRE-GO-07", "CT-positive", "GOBP_CELL_CYCLE", 32, 1847, "0.00000154", "0.0017"),
    ("PRE-GO-08", "CT-positive", "GOBP_GROWTH", 21, 922, "0.00000184", "0.00178"),
    ("PRE-GO-09", "CT-positive", "GOBP_PROTEIN_CONTAINING_COMPLEX_ORGANIZATION", 31, 1828, "0.00000349", "0.00278"),
    ("PRE-GO-10", "CT-positive", "GOBP_DNA_METABOLIC_PROCESS", 22, 1043, "0.00000359", "0.00278"),
    ("PRE-GO-11", "SA-positive", "GOBP_CELL_PROJECTION_ORGANIZATION", 44, 1576, "1.88E-13", "1.46E-09"),
    ("PRE-GO-12", "SA-positive", "GOBP_GENERATION_OF_NEURONS", 40, 1443, "3.25E-12", "1.26E-08"),
    ("PRE-GO-13", "SA-positive", "GOBP_NEURON_DEVELOPMENT", 33, 1108, "4.68E-11", "0.000000121"),
    ("PRE-GO-14", "SA-positive", "GOBP_REGULATION_OF_CELL_PROJECTION_ORGANIZATION", 25, 684, "1.87E-10", "0.000000362"),
    ("PRE-GO-15", "SA-positive", "GOBP_NEUROGENESIS", 40, 1667, "2.45E-10", "0.00000038"),
    ("PRE-GO-16", "SA-positive", "GOBP_REGULATION_OF_NEURON_PROJECTION_DEVELOPMENT", 20, 452, "5.03E-10", "0.00000065"),
    ("PRE-GO-17", "SA-positive", "GOBP_CELL_JUNCTION_ORGANIZATION", 25, 741, "9.64E-10", "0.00000107"),
    ("PRE-GO-18", "SA-positive", "GOBP_CELL_MORPHOGENESIS", 27, 931, "5.15E-09", "0.00000499"),
    ("PRE-GO-19", "SA-positive", "GOBP_POSITIVE_REGULATION_OF_RNA_METABOLIC_PROCESS", 39, 1853, "1.56E-08", "0.0000134"),
    ("PRE-GO-20", "SA-positive", "GOBP_CHROMATIN_ORGANIZATION", 21, 652, "4.81E-08", "0.0000372"),
    ("PRE-GO-21", "CT-negative", "GOBP_REGULATION_OF_TRANSPORT", 74, 1809, "6.36E-21", "4.93E-17"),
    ("PRE-GO-22", "CT-negative", "GOBP_CELL_CELL_SIGNALING", 67, 1697, "3.42E-18", "1.33E-14"),
    ("PRE-GO-23", "CT-negative", "GOBP_NEGATIVE_REGULATION_OF_RESPONSE_TO_STIMULUS", 61, 1714, "1.38E-14", "2.43E-11"),
    ("PRE-GO-24", "CT-negative", "GOBP_CELL_ADHESION", 57, 1524, "1.4E-14", "2.43E-11"),
    ("PRE-GO-25", "CT-negative", "GOBP_RESPONSE_TO_OXYGEN_CONTAINING_COMPOUND", 63, 1819, "1.67E-14", "2.43E-11"),
    ("PRE-GO-26", "CT-negative", "GOBP_REGULATION_OF_IMMUNE_SYSTEM_PROCESS", 56, 1493, "2.16E-14", "2.43E-11"),
    ("PRE-GO-27", "CT-negative", "GOBP_SMALL_MOLECULE_METABOLIC_PROCESS", 63, 1830, "2.19E-14", "2.43E-11"),
    ("PRE-GO-28", "CT-negative", "GOBP_REGULATION_OF_SECRETION", 35, 635, "5.17E-14", "4.94E-11"),
    ("PRE-GO-29", "CT-negative", "GOBP_MONOATOMIC_ION_TRANSPORT", 50, 1252, "5.74E-14", "4.94E-11"),
    ("PRE-GO-30", "CT-negative", "GOBP_EXPORT_FROM_CELL", 41, 905, "2.22E-13", "1.72E-10"),
    ("PRE-GO-31", "SA-negative", "GOBP_ESTABLISHMENT_OF_PROTEIN_LOCALIZATION", 33, 1684, "7.23E-09", "0.000056"),
    ("PRE-GO-32", "SA-negative", "GOBP_REGULATION_OF_CELLULAR_COMPONENT_BIOGENESIS", 23, 989, "8.19E-08", "0.000317"),
    ("PRE-GO-33", "SA-negative", "GOBP_RESPONSE_TO_OXYGEN_CONTAINING_COMPOUND", 31, 1819, "0.000000461", "0.00119"),
    ("PRE-GO-34", "SA-negative", "GOBP_REGULATION_OF_CELL_JUNCTION_ASSEMBLY", 10, 214, "0.0000011", "0.00182"),
    ("PRE-GO-35", "SA-negative", "GOBP_REGULATION_OF_TRANSPORT", 30, 1809, "0.00000125", "0.00182"),
    ("PRE-GO-36", "SA-negative", "GOBP_REGULATION_OF_MONOATOMIC_ION_TRANSPORT", 16, 599, "0.00000141", "0.00182"),
    ("PRE-GO-37", "SA-negative", "GOBP_CELLULAR_COMPONENT_MORPHOGENESIS", 18, 767, "0.00000193", "0.00194"),
    ("PRE-GO-38", "SA-negative", "GOBP_REGULATION_OF_MONOATOMIC_CATION_TRANSMEMBRANE_TRANSPORT", 12, 346, "0.00000217", "0.00194"),
    ("PRE-GO-39", "SA-negative", "GOBP_REGULATION_OF_MONOATOMIC_ION_TRANSMEMBRANE_TRANSPORT", 14, 478, "0.00000225", "0.00194"),
    ("PRE-GO-40", "SA-negative", "GOBP_INTRACELLULAR_TRANSPORT", 27, 1591, "0.00000289", "0.00224"),
]
PRE_GO_CLAIMS = ("PRE-GO-07", "PRE-GO-13", "PRE-GO-15")
PRE_GO_TXT = ("Results: genes positively associated 'were enriched for genes regulating biological processes including cell cycle, cell "
              "growth, DNA metabolism and transcription, neuron development, and neurogenesis (eTable 5 ...)'; negatively associated 'for "
              "genes regulating cell signaling, secretion, metabolism, and immune response'")


def pre_go_row(g, claim):
    cid, lst, term, k, K, p, q = g
    feat = lst.split("-")[0]
    sign = "+" if lst.endswith("positive") else M
    add(T16, cid, cell_class="claim" if claim else "descriptor", claim_form="decoded-list", map=PRE_Y[feat],
        set_S=("MSigDB C5 GOBP 2023.1.Hs '%s' (K = %d in the paper; the first release with 'MONOATOMIC' term names, section 1.6; the "
               "set reached by the name rule of sections 1.1 / 1.6)" % (term, K)),
        T=T_DL if claim else "descriptor (section 1.1): " + T_DL,
        direction="%s (%s list%s)" % (sign, lst, "; register 3.4" if claim else "; descriptor"),
        status="auditable (under G2)", headline_population=HL_ADDED + ("" if claim else "; descriptor cell"),
        reproduction=PRE_REP % ("k %d, p %s, FDR q %s" % (k, p, q)),
        published_value_and_location="k %d / K %d, p %s, FDR q %s (eTable 5, MSigDB hypergeometric, top 10 per list); %s" % (k, K, p, q, PRE_GO_TXT),
        verdict_counted_in_m="yes" if claim else "no",
        notes=("id: register. One of the three eTable 5 rows whose names the text uses exactly (rule G; register 3.4)." if claim else
               "id: draft. One of 'the other 37 GO rows' -> descriptor cell (register 3.4)."))


for g in PRE_GO:
    if g[0] in PRE_GO_CLAIMS:
        pre_go_row(g, True)
PRE_CT = [("PRE-CT1", "SA", "positive", "Zhong_microglialtype2_genelist (K 488)", "k 18, OR 2, p .0074 (eTable 3)"),
          ("PRE-CT2", "SA", "positive", "Manno_midbrain_gabaneurons_genelist (K 1,106)", "k 43, OR 2.2, p 1.1e-05 (eTable 3)"),
          ("PRE-CT3", "SA", "positive", "Manno_midbrain_dopamineneurons1_genelist (K 584)", "k 21, OR 1.9, p .0053 (eTable 3)"),
          ("PRE-CT4", "CT", "negative", "Zhongmicroglialtype2_genelist (K 488)", "k 27, OR 1.8, p .0038 (eTable 4)"),
          ("PRE-CT5", "CT", "negative", "Manno_midabrain_dopamineneurons_cells (K 506)", "k 34, OR 2.3, p 3.30E-05 (eTable 4)"),
          ("PRE-CT6", "CT", "negative", "Manno_midbrain_dopamineneurons1_genelist (K 584)", "k 36, OR 2.1, p 1.20E-04 (eTable 4)"),
          ("PRE-CT7", "CT", "negative", "Manno_midbrain_dopamineneurons2_genelist (K 513)", "k 39, OR 2.6, p 4.40E-07 (eTable 4)"),
          ("PRE-CT8", "CT", "negative", "Manno_midbrain_5HTneurons_genelist (K 450)", "k 27, OR 2, p .0012 (eTable 4)"),
          ("PRE-CT9", "CT", "negative", "Manno_midbrain_gabaneurons_genelist (K 1,106)", "k 46, OR 1.4, p .03 (eTable 4; raw p may not pass FDR)")]
for cid, feat, sg, S, pub in PRE_CT:
    add(T16, cid, cell_class="claim", claim_form="decoded-list", map=PRE_Y[feat],
        set_S="%s (eMethods cite Zhang 2014 / La Manno 2016; list files unpublished, selection rule unknown)" % S,
        T=T_DL + " (never computed: not auditable)",
        direction="%s (%s-%s list; draft)" % ("+" if sg == "positive" else M, feat, sg),
        status="not auditable: cell-type lists unpublished, selection rule unknown (register 3.4)",
        reproduction=PRE_REP % pub.split(" (")[0] + " (not run: not auditable)",
        published_value_and_location=pub + "; main text: enriched for genes 'linked to microglia and GABAergic and dopaminergic neurons' / 'dopaminergic, serotonergic, and GABAergic neurons'",
        notes=("id: register." + (" Recorded, not registered (section 1.1): eTable 3-4 rows outside the named categories or without a "
                                  "defined set -- Manno 5HT (SA-positive; k 16, OR 1.9, p .01; not named in the text) and the internally "
                                  "inconsistent Zhong_microglial_genelist row (k 42, K 438, OR 3.4, p .17) (draft section 2A). The "
                                  "Gandal rows are descriptor cells (PRE-D1r, PRE-DG; register 3.4, v4)."
                                  if cid == "PRE-CT1" else "")))
add(T16, "PRE-X1", cell_class="claim", claim_form="other",
    map=("none: no map form -- an overlap between two decoded lists (the CT-positive and the SA-negative list, both decoded from the "
         "same LEAP sample's maps y_CT and y_SA; register 3.4, v4)"),
    set_S=("the other feature's decoded list, selected on the same LEAP sample's imaging data; the selection rule (donor-LME, pFDR < "
           ".01) is unpublished"),
    T="none: not testable as stated -- an overlap between two decoded lists, no map form; no registered T form (register 3.4, section 1.4)",
    direction="n/a: no registered T (not testable as stated)",
    status=("not testable as stated: an overlap between two decoded lists, no map form (register 3.4, v4); also not auditable: the "
            "selection rule (donor-LME, pFDR < .01) is unpublished (section 1.8: both flags reported)"),
    reproduction="descriptive (amendment 4 section 2): GeneOverlap OR, FDR p <= .01 (not run: not testable as stated, not auditable)",
    published_value_and_location=("'Genes associated positively with the more neurotypical/less autism-like cortical thickness component and "
                                  "negatively with the surface area component were significantly enriched for each other (Figure S9)' "
                                  "(Supplement 1, 'Genomic results -- Secondary results', p. 9; eFigure 9 tile)"),
    notes=("id: register. v3: a not-auditable selected-list component claim with its map and direction undetermined; v4: not testable "
           "as stated (no map form) and not auditable (register 3.4, section 9)."))
for g in PRE_GO:
    if g[0] not in PRE_GO_CLAIMS:
        pre_go_row(g, False)
PRE_B = [("PRE-B01", "CT", "positive", "up-regulated at 37 yrs", "eFigure 8A"),
         ("PRE-B02", "CT", "negative", "up-regulated, Late mid-prenatal", "eFigure 7B"),
         ("PRE-B03", "CT", "negative", "up-regulated, Early infancy", "eFigure 7B"),
         ("PRE-B04", "CT", "negative", "up-regulated at 4 mos", "eFigure 8B"),
         ("PRE-B05", "SA", "positive", "up-regulated at 16 pcw", "eFigure 8C"),
         ("PRE-B06", "SA", "positive", "up-regulated at 17 pcw", "eFigure 8C"),
         ("PRE-B07", "SA", "positive", "up-regulated at 21 pcw", "eFigure 8C"),
         ("PRE-B08", "SA", "positive", "up-regulated at 1 yrs", "eFigure 8C"),
         ("PRE-B09", "SA", "positive", "down-regulated, Late childhood", "eFigure 7C"),
         ("PRE-B10", "SA", "positive", "down-regulated, Young adulthood", "eFigure 7C"),
         ("PRE-B11", "SA", "positive", "down-regulated, Middle adulthood", "eFigure 7C"),
         ("PRE-B12", "SA", "positive", "down-regulated at 4 yrs", "eFigure 8C"),
         ("PRE-B13", "SA", "positive", "down-regulated at 8 yrs", "eFigure 8C"),
         ("PRE-B14", "SA", "positive", "down-regulated at 40 yrs", "eFigure 8C")]
for cid, feat, sg, S, fig in PRE_B:
    add(T16, cid, cell_class="descriptor", claim_form="decoded-list", map=PRE_Y[feat],
        set_S=("FUMA GENE2FUNC BrainSpan DEG set '%s' (FUMA's definition: one label vs the rest; version not stated: section 1.6 source 3, "
               "the release in force at the paper's submission date; 're-derived')" % S),
        T="descriptor (section 1.1): " + T_DL, direction="%s (%s-%s list; draft; descriptor)" % ("+" if sg == "positive" else M, feat, sg),
        status="auditable (S re-derived by FUMA's rule; under G2)", headline_population=HL_ADDED + "; descriptor cell",
        reproduction="descriptive (amendment 4 section 2): the paper's FUMA enrichment re-run on the re-derived lists; 'sig' bar status vs %s" % fig,
        published_value_and_location=("red ('sig') bar in %s (-log10 p; no numeric value; read by the draft at 200-300 dpi); main text themes: "
                                      "'genes upregulated in adulthood (cortical thickness), upregulated in early life (surface area), and "
                                      "downregulated in adulthood (surface area)'" % fig),
        notes="id: register (PRE-B01 ... B14: FUMA epochs named only as themes -> descriptor cells, register 3.4).")
PRE_GANDAL = {"up": ("Gandal 2018 ASD-upregulated genes (section 1.6 pinned: gene-level table, ASD FDR < .05 with log2FC > 0; size "
                     "reported beside the paper's K = 1,111)"),
              "down": ("Gandal 2018 ASD-downregulated genes (section 1.6 pinned: gene-level table, ASD FDR < .05 with log2FC < 0; size "
                       "reported beside the paper's K = 764)")}
add(T16, "PRE-D1r", cell_class="descriptor", claim_form="decoded-list", map=PRE_Y["SA"], set_S=PRE_GANDAL["up"],
    T="descriptor (section 1.1): " + T_DL, direction="two-sided (descriptor cell; register 3.4)",
    status="auditable (descriptor; under G2)", headline_population=HL_ADDED + "; descriptor cell",
    reproduction=PRE_REP % "k 8, OR 0.4, p 1",
    published_value_and_location="k 8, OR 0.4, p 1 (eTable 4: the ASD_upregulated row of the SA-negative list, PRE-D1's reciprocal row)",
    dependencies="PRE-D1 (same map, the sign-complement set of the same DE table)",
    notes="id: register (register 3.4, v4: 'PRE-D1r (SA-negative x Gandal ASD-up; k 8, OR 0.4, p 1)', two-sided).")
# register 3.4, section 1.11 item 4 (v5): the other Gandal rows of eTables 3-4 are 6 (PRE_DG_ROWS.json, labels only)
if PREDG["n_other_rows"] != 6 or [r["proposed_cell_id"] for r in PREDG["rows"]] != ["PRE-DG-%02d" % k for k in range(1, 7)]:
    die("PRE_DG_ROWS.json: expected the six rows PRE-DG-01 ... 06")
for k, r in enumerate(PREDG["rows"], start=1):
    add(T16, r["proposed_cell_id"], cell_class="descriptor", claim_form="decoded-list", map=PRE_Y[r["feature"]],
        set_S=(PRE_GANDAL[r["gandal_direction"]] + "; the eTable %d row '%s' of the %s list (Supplement 1 pp. %s; register 3.4, "
               "section 1.11 item 4; register_sets/PRE_DG_ROWS.json)" % (r["etable"], r["row_label"], r["decoded_list"],
                                                                         "-".join(str(p) for p in r["pages"]))),
        T="descriptor (section 1.1): " + T_DL, direction="two-sided (descriptor cell; register 3.4)",
        status="auditable (descriptor; under G2)", headline_population=HL_ADDED + "; descriptor cell",
        reproduction=PRE_REP % "the eTable row's k, OR and p",
        published_value_and_location=("eTable %d, %s list, row '%s' (Supplement 1 pp. %s): values not read before the freeze -- "
                                      "labels and set identity only (register section 1.11 item 4)"
                                      % (r["etable"], r["decoded_list"].split(" (")[0], r["row_label"],
                                         "-".join(str(p) for p in r["pages"]))),
        dependencies=("PRE-D1, PRE-D1r (same DE table); cells on one map share y; the positive and negative lists of a feature are "
                      "sign complements"),
        cell_index=str(k),
        notes=("id: register (register 3.4, section 1.11 item 4: 'every other Gandal up / down row of eTables 3-4', PRE-DG-01 ... 06 = "
               "CT-positive, SA-positive and CT-negative lists x Gandal down / up, two-sided descriptor cells; with PRE-D1 / PRE-D1r "
               "they cover all eight combinations). Replaces v4's one PRE-DG unit row. Seed cell index %d = its place in eTables "
               "3-4's order (section 1.9)." % k))

# ====================================================================================================================
# target 17 -- Park 2021 (added)
# ====================================================================================================================
PK_Y = ("NeuroVault 743 image 396720 'ASD grad123 T perm' (grad123_multivariate_totT_perm_dil.nii.gz, 591,269 B; GenericMNI volume; n = 84; "
        "Hotelling's T of the manifold shift, non-negative; attribution: metadata (version inferred), section 1.7 version rule); the Source "
        "Data workbook is not used (its map sheet is unnamed); " + ident("park2021subcortico", "396720") + "; " + ID_RULE)
PK_Y319 = ("NeuroVault 743 image 319367 'ASD grad123 T' (grad123_multivariate_totT_dil.nii.gz, 576,995 B; earliest upload 2019-12-29; "
           "n = 84) -- the descriptor image (section 1.7: '319367 a descriptor'); " + ident("park2021subcortico", "319367") + "; "
           + ID_RULE)
PK_LVL = ("gene null only (uniform): the CSEA tool's overlap test (test not named) (register 3.5); spin upstream (100 rotations per gene "
          "in list construction) [draft reading 'none' recorded]")
PK_REP = ("descriptive (amendment 4 section 2): NeuroVault decoder output for image %s (fetched under G1), FDR < .05, the 100-rotation "
          "spin check, DS > .5; then CSEA; OR, p and Jaccard with Supplementary Data 1")
PK_PUB = ("CSEA FDR-corrected p (Fig. 3b colours; no number in the text): 'associations between the multivariate pattern of autism-related "
          "structural manifold distortions and genes expressed in early childhood and adolescence, as well as early infancy and young "
          "adulthood, in thalamic and cortical areas (Fig. 3b)' (Results 'Transcriptomic association analysis')")
T17 = Target(17, "park2021subcortico", "added", "G1", analysis_class="dk-ctx",
             route=ROUTE_VOL_DKCTX + "; cortex only (the NeuroVault decoder masked subcortex)", headline_population=HL_ADDED,
             dependencies=("cells share y; overlapping CSEA sets; ABIDE II NYU / TCD shared with Benkarim and Pagani; PARK-C5's proxy S shared "
                           "with BENK-C2"))
PK_STAGES = [("a", "Neonatal-Early Infancy", "Neonatal & early infancy"), ("b", "Early Childhood", "early childhood"),
             ("c", "Adolescence", "adolescence"), ("d", "Young Adulthood", "young adulthood")]
PK_REGIONS = [("1", "Cortex", "cortex"), ("2", "Thalamus", "thalamus")]
for rid, rlab, region in PK_REGIONS:
    for letter, plab, stage in PK_STAGES:
        cid = "PARK-C%s%s" % (rid, letter)
        add(T17, cid, cell_class="claim", claim_form="decoded-list", map=PK_Y,
            set_S="CSEA developmental set: %s" % psi_set(PSI_DEV, "region '%s' and period '%s'" % (rlab, plab)),
            T=T_DL, direction="two-sided (sign composition unstated; the map is an unsigned Hotelling's T; register 3.5)",
            inference_level=PK_LVL, status="auditable (under G1)", reproduction=PK_REP % "396720",
            published_value_and_location=PK_PUB, verdict_counted_in_m="yes",
            notes=("id: register (PARK-C%sa-d = %s x the four stage bins)." % (rid, region)
                   + (" Focal-for-description (thalamus x early childhood: the text's first region and first stage; register 3.5)."
                      if cid == "PARK-C2b" else "")
                   + (" Recorded, not registered (section 1.1): 'they were not significantly expressed in the striatum nor hippocampus' "
                      "(no stage bin named) and the Fig. 3b cells beyond the named ones (not enumerated in the texts)."
                      if cid == "PARK-C1a" else "")))
add(T17, "PARK-C5", cell_class="claim", claim_form="other", map=PK_Y,
    set_S=("none: genome-wide ranking of all genes' NeuroVault decoding t; descriptor proxy S = Gandal 2018 ASD-down (section 1.6 pinned), "
           "labelled 'set proxy'"),
    T=("not testable as stated (section 1.4: a genome-wide robust regression); descriptors as BENK-C2 (register 3.5): the paper's RLM (decoding "
       "t ~ log2FC + GC content) on our decoding, and the Gandal 2018 ASD-down set proxy with the decoded-list T (labelled)"),
    direction="n/a: not testable as stated; proxy descriptor + (draft: a negative RLM T means ASD-down genes should have mean r > 0)",
    inference_level="none: parametric robust linear regression (register 3.5)",
    status="not testable as stated: genome-wide robust regression (register 3.5)",
    reproduction=("descriptive (amendment 4 section 2): the paper's RLM on our decoding vs T = -34.89, p < .001; SCZ (T = -8.93) and BD (T = "
                  "5.34) as the paper's comparison"),
    published_value_and_location=("robust-regression T = -34.89, p < 0.001 (ASD); SCZ -8.93; BD 5.34 (Results 'Transcriptomic association "
                                  "analysis'; Fig. 3c); DE source ref. 70 = Gandal 2018 Science 362"),
    notes="id: register.")
for cid, region, rng, pub in [
        ("PARK-C3", "cerebellum", "'early development'", "'these genes were also expressed in the cerebellum in early development'"),
        ("PARK-C4", "amygdala", "'later developmental stages'", "'and in the amygdala in later developmental stages'")]:
    add(T17, cid, cell_class="descriptor", claim_form="decoded-list", map=PK_Y,
        set_S="CSEA %s x an unnamed stage bin: %s names no bin (rule G) -- S undefined" % (region, rng),
        T="descriptor (section 1.1): " + T_DL + " (never computed: not auditable)", direction="two-sided (descriptor cell)",
        inference_level=PK_LVL, status="not auditable: no stage bin named (register 3.5)", reproduction=PK_REP % "396720" + " (not run)",
        published_value_and_location=pub + " (Results 'Transcriptomic association analysis'; Fig. 3b)",
        notes="id: register (register 3.5: %s, a descriptor cell, not auditable)." % cid)
add(T17, "PARK-C6", cell_class="family", claim_form="decoded-list", map=PK_Y,
    set_S=("Lake 2018 (Nat Biotechnol) marker table: the 13 excitatory-neuron subtypes, one descriptor family (register 3.5); section 1.6 "
           "source 2 ('S re-derived')"),
    T="descriptor family (section 1.1): " + T_DL + ", one cell per subtype",
    direction="two-sided (descriptor cells; list sign unknown)",
    inference_level="gene null only (structured: overlap ratio vs 1,000 gene-length-matched permutations; FDR across cell types)",
    status="auditable (under G1)", headline_population=HL_ADDED + "; descriptor family",
    reproduction="descriptive (amendment 4 section 2): overlap ratio and FDR vs 22.36 +- 4.16 %, FDR .1",
    published_value_and_location=("overlap 22.36 +- 4.16 % (mean +- SD across 13 excitatory subtypes), FDR = 0.1: 'Highest and marginally "
                                  "significant overlap was observed for the excitatory neurons' (Results; Supp Fig. 10b)"),
    n_cells="13",
    notes="id: register (register 3.5: PARK-C6, one descriptor family over the 13 excitatory subtypes of Lake 2018's marker table).")
for rid, rlab, region in PK_REGIONS:
    for letter, plab, stage in PK_STAGES:
        add(T17, "PARK-C%s%s-319367" % (rid, letter), cell_class="descriptor", claim_form="decoded-list", map=PK_Y319,
            set_S="as PARK-C%s%s: CSEA developmental set: %s" % (rid, letter, psi_set(PSI_DEV, "region '%s' and period '%s'" % (rlab, plab))),
            T="descriptor (section 1.1): " + T_DL, direction="two-sided (descriptor; as the claim)", inference_level=PK_LVL,
            status="auditable (descriptor image; under G1)", reproduction=PK_REP % "319367",
            published_value_and_location="as PARK-C%s%s (the paper names no image; 396720 is the registered map)" % (rid, letter),
            dependencies="PARK-C%s%s (same S, the other image of the same analysis)" % (rid, letter),
            notes="id: register (pattern PARK-*-319367; register 3.5: every claim cell again on image 319367 as a descriptor).")

# ====================================================================================================================
# target 18 -- Moreau 2020 (added; CNV class)
# ====================================================================================================================
MO_WB = ("repo kkumar-iitkgp-livia/GeneExp_and_CNV_FCsignatures @9e8af9c1 data/Supplementary_Table_S1.xlsx (sha256 "
         "c947112ded237be43459c65f896c7ec1f120d6faaed0d5700ed63fb81e302e19)")
MO_Y = {"16p": ("16p11.2-deletion FC signature (SVIP: 20 carriers vs 79 controls), " + MO_WB + " sheet 1_16p11.2Del; nodal profile = the "
                "64 x 64 beta block with the diagonal set to 0, mean over the 64 columns (the code's definition); sheets 5_BIV, 6_ASD, "
                "9_Ranking never opened"),
        "22q": ("22q11.2-deletion FC signature (UCLA: 46 carriers vs 43 controls), " + MO_WB + " sheet 3_22q11.2Del; nodal profile as "
                "for 16p (diagonal 0, mean over 64)")}
MO_S = {"16p": ("16p11.2 locus genes (29.6-30.1 Mb hg19), 24 HGNC symbols, repo data/cnv_genes_cnv16p112.csv (sha256 prefix b2b9dbfb); "
                "source 1; genomic interval, not selected on imaging"),
        "22q": ("22q11.2 locus genes (18.6-21.5 Mb hg19), 37 HGNC symbols incl. pseudo / ncRNA genes, repo data/cnv_genes_cnv22q112.csv "
                "(sha256 prefix 3838d75f); source 1")}
MO_T = ("component level (section 1.4; amendment 4 section 2): T = cumulative R^2 of two components with prereg section 4.7's "
        "PLSRegression(2, scale=True), refit on every permutation and surrogate; Level 0 = 10,000 parcel-label permutations with refit; "
        "class-stratified site leg; read 'passes / does not pass at component level', label 'site leg only; not calibrated against "
        "expression-aligned maps'")
MO_LVL = ("other: subject-label permutation (5,000 label-shuffled FC signatures, CWAS re-run); the paper's own random-gene null was run "
          "and failed (R^2 p .1782 / .8211; median-r p .31 / .36) (register 3.6)")
# register 3.6, section 1.11 item 5 (v5): MIST64 classes and the section 3.1-settings matrix, fixed before the freeze
_MC = MIST["counts"]
_MP = _MC["primary_by_tissue_class"]
_MH = _MC["hemisphere_all64"]
_MT = _MC["tissue_class_all64"]
_UNB = MIST["checks"]["unprefixed_labels_not_B_by_centroid"]
_UNB_R = sorted(x["label"] for x in _UNB if x["hemisphere"] == "R")
_NEAR = sorted((round(p["centroid_mni_mm"][0], 2) for p in MIST["parcels"] if 2.0 <= abs(p["centroid_mni_mm"][0]) < 2.2), key=abs)
if (_MC["primary_n"], _MP["cortex"], _MP["subcortex"], _MP["cerebellum"]) != (46, 33, 5, 8) or MISTM["n_empty"] != 0 \
        or not MISTM["determinism_check"]["identical"] or MISTM["n_primary_with_samples"] != _MC["primary_n"]:
    die("mist64 JSONs differ from register section 1.11 item 5 (46 primary: cortex 33, subcortex 5, cerebellum 8; 0 empty parcels)")
MO_MIST = ("MIST64 classes (register section 1.11 item 5; register_maps/mist64_classes.json, sha256 %s): prereg section 2's centroid "
           "rule applied as written (B = |x| < 2 mm): L %d / B %d / R %d; primary (L + B) = %d parcels: cortex %d, subcortex %d, "
           "cerebellum %d (all 64: cortex %d, subcortex %d, cerebellum %d); classes by the name rule (CERVM -> cerebellum; CAUDNH_NACC "
           "and AMY_HIPP -> subcortex), not MIST's 12-level hierarchy; declared consequence: %d labels without an L_ / R_ prefix have "
           "centroids right of the midline and leave the primary set (the all-64 bilateral multiverse cell keeps them); centroids "
           "near the threshold: %s mm. Matrix: section 3.1 settings, %d x %s genes, %d empty parcels, abagen %s; identity sha256_matrix "
           "%s (register_maps/mist64_ahba_matrix.json; the .csv.gz file hash varies per write, the pandas matrix hash is the "
           "registered identity)"
           % (sha256_file(MAPS_DIR / "mist64_classes.json"), _MH["L"], _MH["B"], _MH["R"], _MC["primary_n"], _MP["cortex"],
              _MP["subcortex"], _MP["cerebellum"], _MT["cortex"], _MT["subcortex"], _MT["cerebellum"], len(_UNB_R),
              " / ".join("%.2f" % x for x in _NEAR), MISTM["n_parcels"], fmt_int(MISTM["n_genes"]), MISTM["n_empty"],
              MISTM["abagen"], MISTM["sha256_matrix"]))
T18 = Target(18, "moreau2020mutations", "added", "none", analysis_class="MIST64",
             route=("native: MIST64 with a section 3.1-settings MIST64 matrix (MIST atlas, figshare 10.6084/m9.figshare.5633638), "
                    "'calibration extrapolated (class)'; primary parcels = left + midline by prereg section 2's own rule (hemisphere from "
                    "each parcel's centroid, midline B = |x| < 2 mm) and tissue classes cortex / subcortex / cerebellum (AMY_HIPP as "
                    "subcortex), both fixed before the freeze from the MIST atlas: primary %d parcels (cortex %d, subcortex %d, "
                    "cerebellum %d); matrix identity sha256_matrix %s (register 3.6, section 1.11 item 5; v3's '59 of 64' was the "
                    "draft's bilateral-as-midline reading); all 64 = the bilateral multiverse cell and the reproduction setting "
                    "(register 3.6)" % (_MC["primary_n"], _MP["cortex"], _MP["subcortex"], _MP["cerebellum"], MISTM["sha256_matrix"])),
             headline_population="out: added target; CNV class (non-ASD outcome, reported apart; amendment 4 section 2)",
             dependencies=("C1 and T1 share the 16p map and S; C2 and T2 the 22q map and S; C3 crosses the 16p genes with the 22q map; R1-R4 "
                           "use per-region columns of the same beta matrices"))
MO_RES = "Results 'CNV FC-signatures associated with gene expression patterns'"
add(T18, "MOR-C1", cell_class="non-ASD-outcome", claim_form="component", map=MO_Y["16p"], set_S=MO_S["16p"], T=MO_T,
    direction="+ (upper tail: R^2 above the null; sign-free)", inference_level=MO_LVL, status="auditable (ungated)",
    reproduction="4.1 check: cumulative R^2 with the authors' centred, unscaled PLS (plsregress, 2 components) on all 64 parcels vs 24.2 % (+-.05)",
    published_value_and_location=("'The two components ... explained 24.2%% of the variance of the 16p11.2 deletion FC profile (p = 0.041, 5000 "
                                  "random FC profiles)' (%s; Supp Data S4.1: 24.223, p .0414); own random 24-gene-set R^2 p .1782 (repo "
                                  "table_specificity_PLSR_nodal_profiles.csv); median-r p = 0.31" % MO_RES),
    verdict_counted_in_m="yes",
    notes=("id: register. CNV class, reported apart. m = 24 < 25 -> 'power not measured at this set size'. MOR-G excluded; the "
           "workbook's ABIDE sheets stay unopened (register 3.6)."))
add(T18, "MOR-C2", cell_class="non-ASD-outcome", claim_form="component", map=MO_Y["22q"], set_S=MO_S["22q"], T=MO_T,
    direction="+ (upper tail: R^2 above the null; sign-free)", inference_level=MO_LVL, status="auditable (ungated)",
    reproduction="4.1 check: cumulative R^2 with the authors' centred, unscaled PLS on all 64 parcels vs 43.2 % (+-.05)",
    published_value_and_location=("'For the 22q11.2 deletion, either one or two components were significant (p < 0.0002, 5000 random FC "
                                  "profiles). The two components explained 43.2%%' (%s; S4.1: 43.244); own random 37-gene-set R^2 p .8211; "
                                  "median-r p = 0.36" % MO_RES),
    verdict_counted_in_m="yes", notes="id: register. CNV class, reported apart.")
add(T18, "MOR-C3", cell_class="descriptor", claim_form="component", map=MO_Y["22q"], set_S=MO_S["16p"] + " (cross-locus)",
    T="descriptor (section 1.1): " + MO_T, direction="+ (upper tail; descriptor)", inference_level=MO_LVL.replace(" (register 3.6)", "") +
    "; this cell: label-shuffle p .001, random-gene R^2 p .9536", status="auditable (ungated)",
    reproduction="4.1 check (descriptor): cumulative R^2 vs 35.3 %",
    published_value_and_location="R^2 35.3 %, label-shuffle p .001 (Supp Data S4.1 only; the text states cross-locus association only regionally)",
    notes="id: register (MOR-C3 descriptor, register 3.6). 16p del x 22q genes (14.5 %, p .2928) is not significant and not registered.")
for cid, loc, S, pub in [
        ("MOR-T1", "16p", MO_S["16p"], ("MVP r = 0.33 (99.76th percentile), KIF22 r = 0.26 (98.76th); genes above the genome-wide 98th percentile "
                                        "over-represented, p = 0.03 (null: 10,000 random gene sets) (%s; Supp Data S4.4); the code uses the "
                                        "95th percentile (text: 98th)" % MO_RES)),
        ("MOR-T2", "22q", MO_S["22q"], "AIFM3, TBX1 and P2RX6 at the 99.5, 98.84, 98.33th percentile (p = 0.04) (%s)" % MO_RES)]:
    add(T18, cid, cell_class="non-ASD-outcome", claim_form="other", map=MO_Y[loc], set_S=S,
        T=("not testable as stated (section 1.4: a tail-rank statistic); computed as a descriptor: the decoded-list-type mean per-gene Pearson "
           "r of S (draft: 're-derived (tail statistic replaced)')"),
        direction="+ (descriptor; the paper: positive r)",
        inference_level="gene null only (uniform): 10,000 random gene sets of the same size (tail statistic); no spatial null",
        status="not testable as stated: tail-rank statistic (register 3.6)",
        headline_population="out: added target; CNV class; not testable as stated",
        reproduction="descriptive (amendment 4 section 2): percentile ranks and the tail p (%s)" % ("p .03" if cid == "MOR-T1" else "p .04"),
        published_value_and_location=pub, notes="id: register. CNV class. Text / code threshold mismatch (98th vs 95th percentile).")
for cid, genes, mapk, n in [("MOR-R1", "16p", "16p", 18), ("MOR-R2", "22q", "22q", 32), ("MOR-R3", "22q", "16p", 20), ("MOR-R4", "16p", "22q", 19)]:
    add(T18, cid, cell_class="non-ASD-outcome", claim_form="other",
        map=("per region i: column i of the %s-deletion beta matrix (64 values, diagonal set to 1), %s sheet %s"
             % (mapk, MO_WB, "1_16p11.2Del" if mapk == "16p" else "3_22q11.2Del")),
        set_S=MO_S[genes] + (" (cross-locus)" if genes != mapk else ""),
        T=("none: not testable as stated (section 1.4: a count of significant regions); no registered T form for count claims, so no "
           "descriptor is computed (section 1.4, v4; the draft's per-region PLSR R^2 is superseded)"),
        direction="n/a: no registered T (count claim)",
        inference_level="other: label-shuffle permutation per region, BH-FDR over 64 regions",
        status="not testable as stated: count of significant regions (register 3.6)",
        headline_population="out: added target; CNV class; not testable as stated",
        reproduction="descriptive (amendment 4 section 2): the count of FDR-significant regions vs %d (Supp Data S4.2)" % n,
        published_value_and_location=("%d of 64 regional FC-signatures significantly associated (5,000 random FC-signatures, FDR over 64 "
                                      "regions) -- %s genes x %s map (%s; Fig. 6b, c; Supp Data S4.2)" % (n, genes, mapk, MO_RES)),
        notes="id: register (MOR-R1 ... R4; R1 / R2 own-locus, R3 / R4 cross-locus per the text). CNV class.")
for _rec in ROWS:
    if _rec["target_key"] == "moreau2020mutations":
        _rec["notes"] += " " + MO_MIST + "."

# ====================================================================================================================
# target 19 -- Hansen 2022 (added)
# ====================================================================================================================
HA_Y = ("repo netneurolab/hansen_crossdisorder_vulnerability @54d34055bd765a79777437f362fbaf338403926e data/enigma_ct.csv, column asd (index 2; "
        "the ENIGMA Toolbox ASD meta-analysis d_icv), sha256 3140921933909a8b9b4b3489a72d253abb5de60f117b762d2b8f7fefa407f2e7; left rows "
        "(Cammoun 2012 scale033 order 35-68); " + ident("hansen2022local", "enigma_ct.csv") + "; component gene_pc1.csv: "
        + ident("hansen2022local", "gene_pc1.csv").split(": ", 1)[1] + "; the local checkout is CRLF, so the at-download check compares "
        "git blob ids after CRLF -> LF (register section 1.11 item 6); " + ID_RULE)
T19 = Target(19, "hansen2022local", "added", "G2", map=HA_Y, analysis_class="dk-ctx",
             route="native: DK cortical, left rows 35-68 (Cammoun order) -> dk-ctx (amendment 5 section 4.3)",
             inference_level=("none: multilinear regression R^2_adj + dominance analysis, no significance test for this pair (register 3.7: "
                              "amendment 4 section 1's '1,000 spins' belongs to other analyses; recorded)"),
             direction="two-sided (no published direction; dominance is unsigned, PC1 sign arbitrary; register 3.7)",
             status="auditable (under G2)", headline_population=HL_ADDED,
             dependencies=("ENIGMA-ASD map family shared with Patel, Giacomel and Liu T3 (overlapping cohorts, different files); gene PC1 is the "
                           "nuisance axis for every ENIGMA-ASD x AHBA claim (amendment 4 section 0)"))
add(T19, "HAN-C1", cell_class="claim", claim_form="component",
    set_S=("none: component = the shipped data/predictors/gene_pc1.csv left rows, sha256 "
           "a078a86d4e6e48980fb12bd464d7b7684a0fc21925c3a5399c8d8e8e54e599d6 (the paper's object)"),
    T=t_comp_fixed("gene PC1 (shipped)"),
    reproduction=("descriptive (amendment 4 section 2): R^2_adj .533 and gene PC1's dominance .027 recomputed with the shipped predictors "
                  "(local_biol_predictors.csv, sha256 prefix d73853619b543bf9)"),
    published_value_and_location=("gene PC1 total dominance 0.027 in the ASD molecular model (R^2_adj 0.533) (Results 'Local and global "
                                  "contributions to disorder-specific cortical morphology'; Figs 2a / 2b / 3)"),
    verdict_counted_in_m="yes",
    notes=("id: register. Reading (register 3.7): the paper never states this pair's association; it enters only as gene PC1's dominance "
           "(.027) in the ASD model. Amendment 5 section 4.4's N1 label does not apply (site-leg-only sub-claim)."))
add(T19, "HAN-C1-ourPC1", cell_class="descriptor", claim_form="component",
    set_S="none: component = our section 3.1 PC1 (V-DK matrix, left cortical parcels, genes with differential stability > .1)",
    T="descriptor (section 1.1): " + t_comp_fixed("our section 3.1 gene PC1 (DS > .1)"),
    reproduction="descriptive (amendment 4 section 2): no published value for this component (register 3.7: a descriptor)",
    published_value_and_location="none (descriptor component; register 3.7: 'our section 3.1 PC1 (DS > .1) a descriptor')",
    notes="id: compiler.")

# ====================================================================================================================
# target 20 -- Leyhausen 2024 (added)
# ====================================================================================================================
LEY_Y = {"MSD": ("MSD t-map: NeuroVault 12301 image 777428 (t-map_m), left fsaverage GIFTI t-map_m.fsaverage.lh.func.gii sha256 "
                 "5889a68733b8d541d7969bdfa8d31c859d75f646a5586839d4a539c71f2680e4 (NIfTI sha256 "
                 "3c5dfc21681e2aa279623ab7d6d2f31e98ee1fbd05ca0a4e8fb58e7e76708aff); uploaded as a surface -> the left fsaverage GIFTI "
                 "(section 1.7); attribution: metadata (version inferred)"),
         "PF": ("perimeter-function t-map: NeuroVault 12301 image 777429 (t-map_pf), left GIFTI sha256 "
                "1299426288ba4938872621c2bac06dac39bcf2ec473dd284e5c2ef41a18fc47a (NIfTI sha256 "
                "4429d1da1981770588e1c37e072d67d51e7843694aa92462c0ac24d77a6a561d); attribution: metadata (version inferred)"),
         "RF": ("radius-function t-map: NeuroVault 12301 image 777430 (t-map_r), left GIFTI sha256 "
                "e6478fdab840f63ba2df5e72d817cfe388d8eecf003847cd027a238cb2344934 (NIfTI sha256 "
                "9436a9e9061aced63eb0fcd3f54212f399722ffe8e042d0e078e3ede9932119e); attribution: metadata (version inferred)")}
LEY_IMG = {"MSD": "777428", "PF": "777429", "RF": "777430"}
LEY_Y = {k: v + "; " + ident("leyhausen2024intrinsic", "image %s" % LEY_IMG[k]) + "; " + ID_RULE for k, v in LEY_Y.items()}
LEY_NLIST = {"MSD": "480", "PF": "382", "RF": "322"}
T20 = Target(20, "leyhausen2024intrinsic", "added", "G2", analysis_class="dk-ctx", route=ROUTE_SURF, T=T_DL,
             direction="two-sided (sign composition unstated), labelled (register 3.8)",
             inference_level=("gene null only (uniform): GeneOverlap hypergeometric (background not stated), FDR (register 3.8) [draft reading "
                              "'other' recorded]"),
             status="auditable (under G2)", headline_population=HL_ADDED, verdict_counted_in_m="yes",
             dependencies=("cells on one map share y; overlapping S (Parikshak modules vs Gandal DEGs; KEGG calcium vs retrograde "
                           "endocannabinoid; Kang M2 / M15)"))
LEY_LOC = "Results pp. 178-179"
S_PARIK = "Parikshak 2016 (Nature 540) module %s, module assignments from their supplementary table (section 1.6 pinned) [%s]"
S_GANDAL = "Gandal 2018 (Science 362, eaat8127) gene-level ASD DE table, ASD FDR < .05 with log2FC %s (section 1.6 pinned) [%s]"
S_VELM = "Velmeshev 2019 (Science 364) Data S4, union over cell types at q < .05 (section 1.6 pinned) ['DEGs']"
S_KEGG = ("KEGG '%s' (Enrichr KEGG_2021_Human: the obtainable KEGG release closest in date to the paper's retrieval, 2021-12-14 -- "
          "section 1.6 KEGG rule (ii), Enrichr snapshots counting as releases (v6.1 Q3); 'release substituted'; the pathway reached "
          "by the name rule of sections 1.1 / 1.6)")
S_KANG = "Kang 2011 (Nature 478) module %s membership table (section 1.6 pinned) ['%s']"
S_POLIO = "Polioudakis 2019 (Neuron 103) cluster-enriched genes table, all rows for cluster %s (section 1.6 pinned)"
LEY = [("LEY-D1", "MSD", S_PARIK % ("M10", "CTX.down.M10"), "OR 4.12** (Fig. 3A)"),
       ("LEY-D2", "MSD", S_PARIK % ("M16", "CTX.down.M16"), "OR 2.46** (Fig. 3A)"),
       ("LEY-D3", "MSD", S_PARIK % ("M4", "CTX.down.M4"), "OR 3** (Fig. 3A)"),
       ("LEY-D4", "MSD", S_GANDAL % ("< 0", "ASD.DEGs.down"), "OR 4.62** (Fig. 3A)"),
       ("LEY-D5", "PF", S_PARIK % ("M9", "CTX.up.M9"), "OR 2.15** (Fig. 3A)"),
       ("LEY-D6", "PF", S_PARIK % ("M16", "CTX.down.M16"), "OR 2.68** (Fig. 3A)"),
       ("LEY-D7", "PF", S_VELM, "OR 2** (Fig. 3A; text cites '(45)')"),
       ("LEY-D8", "PF", S_GANDAL % ("> 0", "ASD.DEGs.up"), "OR 2.25** (Fig. 3A)"),
       ("LEY-D9", "RF", S_PARIK % ("M20", "CTX.up.M20"), "OR 3.14** (Fig. 3A)"),
       ("LEY-K1", "MSD", S_KEGG % "axon guidance", "OR 2.41** (Fig. 3B)"),
       ("LEY-K2", "MSD", S_KEGG % "retrograde endocannabinoid signaling", "OR 3.12** (Fig. 3B)"),
       ("LEY-K3", "MSD", S_KEGG % "calcium signaling pathway", "OR 2.62** (Fig. 3B)"),
       ("LEY-K4", "PF", S_KEGG % "pathways of neurodegeneration - multiple diseases", "OR 3.14** (Fig. 3B)"),
       ("LEY-K5", "PF", S_KEGG % "retrograde endocannabinoid signaling", "OR 3.96** (Fig. 3B)"),
       ("LEY-K6", "RF", S_KEGG % "calcium signaling pathway", "OR 3.21** (Fig. 3B)"),
       ("LEY-M1", "MSD", S_KANG % ("M2", "synaptic transmission"), "OR 2.66** (Fig. 3C)"),
       ("LEY-M2", "MSD", S_KANG % ("M15", "synaptic transmission"), "OR 3.19** (Fig. 3C)"),
       ("LEY-M3", "RF", S_KANG % ("M2", "synaptic transmission"), "OR 1.77** (Fig. 3C)"),
       ("LEY-M4", "RF", S_KANG % ("M15", "synaptic transmission"), "OR 3.62** (Fig. 3C)"),
       ("LEY-C01", "MSD", S_POLIO % "ExDp1 (excitatory deep layer 1)", "OR 1.90** (Fig. 4B)"),
       ("LEY-C02", "RF", S_POLIO % "End (endothelial)", "OR 2.04** (Fig. 4C)"),
       ("LEY-C03", "RF", S_POLIO % "InMGE (interneuron MGE)", "OR 3.45** (Fig. 4C)"),
       ("LEY-C04", "RF", S_POLIO % "ExDp2", "OR 3.47** (Fig. 4C)"),
       ("LEY-C05", "RF", S_POLIO % "ExDp1", "OR 3.30** (Fig. 4C)"),
       ("LEY-C06", "RF", S_POLIO % "ExM-U (maturing excitatory upper enriched)", "OR 3.35** (Fig. 4C)"),
       ("LEY-C07", "RF", S_POLIO % "ExM (maturing excitatory)", "OR 4.11** (Fig. 4C)"),
       ("LEY-C08", "PF", S_POLIO % "Per (pericyte)", "OR 1.83** (Fig. 4D)"),
       ("LEY-C09", "PF", S_POLIO % "OPC", "OR 2.43** (Fig. 4D)"),
       ("LEY-C10", "PF", S_POLIO % "ExDp2", "OR 3.99** (Fig. 4D)"),
       ("LEY-C11", "PF", S_POLIO % "ExDp1", "OR 3.49** (Fig. 4D)"),
       ("LEY-C12", "PF", S_POLIO % "ExM-U", "OR 2.83** (Fig. 4D)"),
       ("LEY-C13", "PF", S_POLIO % "oRG (outer radial glia)", "OR 2.96** (Fig. 4D)")]
for cid, mp, S, pub in LEY:
    add(T20, cid, cell_class="claim", claim_form="decoded-list", map=LEY_Y[mp], set_S=S,
        reproduction=("descriptive (amendment 4 section 2): NeuroVault decoder output for image %s (fetched under G2), nominal p < .01 (the "
                      "paper's list size %s), then GeneOverlap; OR and p vs the published OR (the paper's lists are unpublished: OR vs our "
                      "re-derived list only)" % (LEY_IMG[mp], LEY_NLIST[mp])),
        published_value_and_location=pub + " (** = significant at FDR p .01; figures give ORs only); " + LEY_LOC,
        notes="id: register." + (" Focal-for-description of the added target (register 3.8)." if cid == "LEY-D1" else ""))
add(T20, "LEY-META", cell_class="family", claim_form="decoded-list",
    map="MSD, PF and RF t-maps (NeuroVault 12301 images 777428-777430, as LEY-D / K / M / C)",
    set_S=("Metascape cluster-representative terms (20 terms of mixed ontologies, no term IDs published; Supplementary Figure 2B): S "
           "undefined"),
    T="none: never computed (not auditable: S undefined)", verdict_counted_in_m="no",
    inference_level="gene null only (uniform; Metascape hypergeometric) (register 3.8)",
    status=("not auditable (S undefined): the text names three GO terms exactly ('nervous system development', 'synaptic signaling', "
            "'neuron projection morphogenesis'), but as Metascape cluster representatives whose per-map significance is unpublished "
            "(the figure's colour scale starts at p = 1), so no map-by-set cell can be fixed (register 3.8, v4)"),
    reproduction="descriptive (amendment 4 section 2): Metascape cluster p (not run: not auditable)",
    published_value_and_location=("Supplementary Figure 2B: non-grey cells MSD 17, PF 12, RF 16 (colour scale starts at p = 1, so a coloured "
                                  "cell is not necessarily p < .01); main text names 'nervous system development, synaptic signaling, and "
                                  "neuron projection morphogenesis' (p. 179)"),
    n_cells=("UNDETERMINED: no map-by-set cell can be fixed (register 3.8, v4); the draft counts 45 non-grey map x term cells (MSD 17, "
             "PF 12, RF 16), which the colour scale does not make significant; the family counts once (section 1.1)"),
    notes="id: register (LEY-META).")

# ====================================================================================================================
# target 21 -- Seelemeyer 2025 (added)
# ====================================================================================================================
SEE_Y = {"SCI-CT": ("790838", "CT_SRS", "fea61aac3efa0f9cc746cb4659406120aa4c21bbc4d142faa6f5860117171ed3", "75c232b442d0d04e3ab5c9a4052b55efd5d91e76fc07e64dcc5218dd09cadd88"),
         "RRB-CT": ("790839", "CT_RBS", "8a52758a6b8033ff58401857417cd840c064fa15cc6b4a8bde2640689d7c41a3", "0bb7683c2cc3e65e6c49a518350cd1e2d84c167ce6fe9ba7b2748b37306eb8ef"),
         "ASP-CT": ("790840", "CT_SSP", "b47efaf32a9f7df042eabb0fc1a8d59b428f75563e8647335b5ddd156560827d", "4eec2e9f703c5d81c00903a62bed685d308131476644eb2adbc29c631ed88075"),
         "SCI-SA": ("790841", "SA_SRS", "0ecb67b775d98f850aa0505fb3963a6f45c0686ee6c1aae425c966c13054de0f", "a111acaf4d6166d9495aa8248a0b6cec4fa4d7fd27827caa1281b10de28a200b"),
         "RRB-SA": ("790842", "SA_RBS", "9c83d7507bcd6b9f20f8b720d5a6b97305c0fe645e5a17db1c088b282b1eb8e2", "df0d4fda5eb48362649187045f2767da9d5009564eb7c21c4ea91d037ca48f5b"),
         "ASP-SA": ("790843", "SA_SSP", "3140d1f82def444529df3e00b016afcb19b328155caff4eb2f39af4382eccac6", "0621993186445a6c7c14d2648e085c24755cd6295c4f5b52fc31095a23da347a")}


def see_map(k):
    img, name, lh, vol = SEE_Y[k]
    return ("%s t-map: NeuroVault 13397 image %s (%s), left GIFTI sha256 %s, volume sha256 %s; REJECTED by section 1.7 (number_of_subjects "
            "535 against the paper's analysed N 428)" % (k, img, name, lh, vol))


T21 = Target(21, "seelemeyer2025decomposing", "added", "G2", analysis_class="dk-ctx",
             route=ROUTE_SURF + " (draft route; not auditable)", T=T_DL + " (never computed: not auditable)",
             direction="two-sided (unsigned decoded lists; draft)",
             inference_level=("gene null only (uniform): GeneOverlap hypergeometric, FDR; background 15,633 (DEG / risk sets) or 18,675 "
                              "(Kang modules) (register 3.9) [draft reading 'other' recorded]"),
             status="not auditable: NeuroVault 13397 rejected by section 1.7 (N 535 against 428); no author contact (register 3.9)",
             headline_population=HL_ADDED,
             dependencies="cells on one map share y; overlapping S (Parikshak modules vs Gandal DEGs; Kang modules)")
SEE_LOC = "Results 'Gene Set Enrichment Analyses', pp. 1070-1071"
SEE = [("SEE-D01", "RRB-CT", S_PARIK % ("M10", "CTX.down.M10"), "OR 1.93** red (Fig. 2A)"),
       ("SEE-D02", "RRB-CT", S_PARIK % ("M20", "CTX.up.M20"), "OR 1.6** green (Fig. 2A)"),
       ("SEE-D03", "RRB-CT", S_PARIK % ("M4", "CTX.down.M4"), "OR 1.56** green (Fig. 2A)"),
       ("SEE-D04", "RRB-CT", S_GANDAL % ("< 0", "ASD.DEGs.down"), "OR 1.66** green (Fig. 2A)"),
       ("SEE-D05", "ASP-CT", S_PARIK % ("M20", "CTX.up.M20"), "OR 1.59** green (Fig. 2A)"),
       ("SEE-D06", "ASP-CT", S_PARIK % ("M4", "CTX.down.M4"), "OR 1.71** green (Fig. 2A)"),
       ("SEE-D07", "ASP-CT", S_VELM, "OR 1.9** red (Fig. 2A)"),
       ("SEE-D08", "ASP-CT", S_GANDAL % ("< 0", "ASD.DEGs.down"), "OR 1.31** green (Fig. 2A)"),
       ("SEE-D09", "SCI-SA", S_VELM, "OR 1.45** green (Fig. 2A)"),
       ("SEE-D10", "SCI-SA", S_GANDAL % ("< 0", "ASD.DEGs.down"), "OR 1.27** red (Fig. 2A)"),
       ("SEE-D11", "RRB-SA", S_PARIK % ("M20", "CTX.up.M20"), "OR 2.1** red (Fig. 2A)"),
       ("SEE-D12", "RRB-SA", S_VELM, "OR 1.9** green (Fig. 2A)"),
       ("SEE-D13", "ASP-SA", S_VELM, "OR 1.64** green (Fig. 2A)"),
       ("SEE-M01", "ASP-CT", S_KANG % ("M2", "synaptic transmission"), "OR 1.28** red (Fig. 2B) -- conflicts with the text 'in the SA, but not in the CT'"),
       ("SEE-M02", "SCI-SA", S_KANG % ("M10", "neuron development"), "OR 3.31** green (Fig. 2B)"),
       ("SEE-M03", "SCI-SA", S_KANG % ("M15", "synaptic transmission"), "OR 2.06** green (Fig. 2B)"),
       ("SEE-M04", "SCI-SA", S_KANG % ("M16", "cell adhesion / signalling"), "OR 2.76** green (Fig. 2B)"),
       ("SEE-M05", "RRB-SA", S_KANG % ("M15", "synaptic transmission"), "OR 2.07** green (Fig. 2B)"),
       ("SEE-M06", "RRB-SA", S_KANG % ("M20", "ZNF / SOX transcription factors"), "OR 1.26** red (Fig. 2B)"),
       ("SEE-M07", "RRB-SA", S_KANG % ("M24", "synaptic transmission"), "OR 5.78** red (Fig. 2B)"),
       ("SEE-M08", "ASP-SA", S_KANG % ("M8", "neuron development / TF"), "OR 4.25** red (Fig. 2B)"),
       ("SEE-M09", "ASP-SA", S_KANG % ("M10", "neuron development"), "OR 4.1** green (Fig. 2B)"),
       ("SEE-M10", "ASP-SA", S_KANG % ("M15", "synaptic transmission"), "OR 2.86** green (Fig. 2B)"),
       ("SEE-M11", "ASP-SA", S_KANG % ("M16", "cell adhesion / signalling"), "OR 3.23** green (Fig. 2B)"),
       ("SEE-C01", "SCI-CT", S_POLIO % "oRG (outer radial glia)", "OR 2.03** (Fig. 3B)"),
       ("SEE-C02", "ASP-CT", S_POLIO % "Per (pericyte)", "OR 1.90** (Fig. 3B)"),
       ("SEE-C03", "ASP-CT", S_POLIO % "ExM-U", "OR 2.30** (Fig. 3B)"),
       ("SEE-C04", "ASP-CT", S_POLIO % "ExN (migrating excitatory)", "OR 3.26** (Fig. 3B)"),
       ("SEE-C05", "SCI-SA", S_POLIO % "ExDp2", "OR 2.00** (Fig. 3C)"),
       ("SEE-C06", "SCI-SA", S_POLIO % "ExDp1", "OR 1.93** (Fig. 3C)"),
       ("SEE-C07", "SCI-SA", S_POLIO % "ExM-U", "OR 2.33** (Fig. 3C)"),
       ("SEE-C08", "RRB-SA", S_POLIO % "ExDp2", "OR 2.07** (Fig. 3C)"),
       ("SEE-C09", "RRB-SA", S_POLIO % "ExN (migrating excitatory)", "OR 3.80** (Fig. 3C)"),
       ("SEE-C10", "ASP-SA", S_POLIO % "ExDp2", "OR 1.94** (Fig. 3C)")]
for cid, mp, S, pub in SEE:
    add(T21, cid, cell_class="claim", claim_form="decoded-list", map=see_map(mp), set_S=S,
        reproduction="descriptive (amendment 4 section 2): GeneOverlap OR vs the published OR (not run: not auditable)",
        published_value_and_location=pub + " (** = p < .001 FDR-corrected; green = across domains, red = only in distinct domains); " + SEE_LOC,
        notes=("id: register." + (" Text-figure mismatch (the text names module 2 for SA; the figure flags M2 only for ASP-CT): the figure "
                                  "flags are followed (draft)." if cid == "SEE-M01" else "")
               + (" Recorded, not registered (section 1.1): 'rather than for autism-likelihood (common or rare variant) gene sets' -- a "
                  "collective non-enrichment without a defined set (draft section 2)." if cid == "SEE-D01" else "")))


def apply_gates():
    """register sections 0, 1.2 (v4): the deferral is the first flag of every gated row's status; a frozen-11 row that would be in the
    population is listed apart (out of the interim population) while its gate is closed, its population on opening kept beside it."""
    for rec in ROWS:
        g = rec["gate"]
        if g in GATE_STATUS:
            rec["status"] = GATE_STATUS[g] + "; " + rec["status"]
            if rec["frozen11_row"] != "added" and rec["headline_population"].startswith("in"):
                rec["headline_population"] = (DEFER_HL % g) + rec["headline_population"]
        elif g == "G1+G2":
            rec["status"] = DEAR_STATUS + "; " + rec["status"]
        elif g != "none":
            die("unknown gate %s on %s" % (g, rec["cell_id"]))


# register section 1.11 item 2 (v6): the rows whose S-build outcome changes their status. These are the builder's own lists; the
# register's section 1.11 id lists are parsed from claims_register.md (R4) and must equal them and the data.
UNCORROBORATED_EXPECTED = (["BUCH-E-Trans-StructConstRibosome-S%d" % k for k in range(1, 5)]
                           + ["RG-N03", "RG-15", "RG-V23"])  # v6.5 (1): no external definition, no printed size
NOT_BUILDABLE_EXPECTED = (["BUCH-E-%s-S%d" % (t, k) for t, (sid, _) in COMP66_BUCH.items() if sid is None for k in range(1, 5)]
                          + [c for c, (sid, _) in COMP66_PAGANI.items() if sid is None])  # v6.6 B2
MODE_NONE_EXPECTED = UNCORROBORATED_EXPECTED + NOT_BUILDABLE_EXPECTED
S_UNDEF_EXPECTED = (["LEY-M%d" % i for i in range(1, 5)] + ["SEE-M%02d" % i for i in range(1, 12)]
                    + ["PRE-B%02d" % i for i in range(1, 15)] + ["LEY-K4"]  # v6.1 Q3: KEGG_2021_Human names hsa05022 otherwise
                    + MODE_NONE_EXPECTED)
DNA_EXPECTED = ["MAMAT-E-SEA-Pnoc-cortex", "MAMAT-E-SEA-cholinergic-striatum"]  # v6 R3: definition not applicable
R2_EXPECTED = (["RG-04", "RG-V08", "RG-V09"] + ["RG-N%02d" % i for i in range(4, 8)]  # v6 R2; v6.5: the Zhang cells (printed size)
               + ["RG-03", "RG-V06", "RG-V07"])  # v6.1 Q2: the RG KEGG families, provisional
LT5_EXPECTED = (["SEG-C3b", "SEG-C3d"]  # v6.6: three Buch comparators have < 5 columns in V-AAL (descriptor cells)
                + ["BUCH-E-%s-S%d" % (t, k) for t in ("GAD", "AntisocialPD", "NeuroticDisorder") for k in range(1, 5)])
SU_NOTE = " (never computed: not auditable, S undefined; register section 1.11 item 2)"
DNA_NOTE = " (never computed: not auditable, definition not applicable; register section 1.11 item 2, v6 R3)"
R2_NOTE = (" (computed only if its gated carrier defines S under the gate, section 1.6 R2; else never computed: not auditable, S "
           "undefined)")
LT5_NOTE = " (not computed: not testable, < 5 columns of S in the class universe; prereg section 4, register section 1.11 item 2)"
R2_FLAG = "S conditional (section 1.6 R2)"
SUMMARY = {"s_undefined": [], "dna": [], "r2": [], "lt5": [], "stale_manifest_cells": [], "name_rule": {}}


def _cell_detail(sj, cid):
    for cd in sj.get("cells_detail", []):
        if cd["cell"].split(" (")[0] == cid:
            return cd
    return None


def _universe_size(sj, cls):
    """a set's size in the row's class universe, in columns of the class matrix (register v6 R5: the four class universes hold the
    same 15,633 columns; a gene with two columns contributes both), its HGNC genes beside."""
    u = sj["universe"]
    cols = {k: v["n_columns"] for k, v in u.items()}
    genes = {k: v["n_in_universe"] for k, v in u.items()}
    if cls in cols:
        txt = "%s columns (%s universe; %s HGNC genes)" % (fmt_int(cols[cls]), cls, fmt_int(genes[cls]))
    elif cls.startswith("dk-ctx | V-DK"):
        if cols["dk-ctx"] != cols["V-DK"]:
            die("dk-ctx and V-DK sizes differ for " + sj["set_id"])
        txt = ("%s columns (dk-ctx or V-DK universe: the per-gene step fixes the class, register 2.6; equal sizes; %s HGNC genes)"
               % (fmt_int(cols["dk-ctx"]), fmt_int(genes["dk-ctx"])))
    else:
        if len(set(cols.values())) != 1:
            die("class universes differ for " + sj["set_id"])
        txt = ("%s columns in every class universe (analysis class '%s': no class universe of its own; %s HGNC genes)"
               % (fmt_int(cols["dk-ctx"]), cls, fmt_int(genes["dk-ctx"])))
    txt += "; %s HGNC-mapped" % fmt_int(sj["n_hgnc"])
    if sj.get("paper_size") is not None:
        txt += "; the paper's size %s" % fmt_int(sj["paper_size"])
    for k, v in (sj.get("paper_sizes") or {}).items():
        txt += "; %s %s" % (k, fmt_int(v))
    return txt


def _release(sj):
    src = sj.get("source")
    if isinstance(src, dict) and src.get("release"):
        return "; release: " + src["release"]
    return ""


def _name_label(cid):
    """register v6 R1: the name rule's record of this cell (register_sets/NAME_MATCHES.json), as written into the TSV."""
    e = NAMES.get(cid)
    if e is None:
        return None
    if e["tier"] is None:
        return ("name rule: S undefined -- '%s' reaches no name, synonym or normalised name of %s (tiers found: %s)"
                % (e["printed"], e["release"], ", ".join("%s %d" % kv for kv in sorted(e["tier_hits"].items()))))
    return ("name rule (%s): %s -> %s '%s' (%s; printed '%s')" % (e["tier"], e["label"], e["id"], e["name"], e["release"],
                                                               e["printed"]))


def apply_sbuild():
    """register sections 1.6, 1.11 items 1-4 (v6; binding): every row carries its S-build disposition and, where a name is mapped,
    the name rule's tier; the rules' outcomes change the rows they bind (S undefined -> not auditable; definition not applicable ->
    not auditable; S conditional on a gated carrier -> flagged, counted in m's upper bound only; < 5 columns -> not testable, out
    of the headline population); nothing else moves."""
    tsv_ids = {r["cell_id"] for r in ROWS}
    SUMMARY["stale_manifest_cells"] = sorted(c for c in CELL_SETS if c not in tsv_ids)
    stale_names = sorted(c for c in NAMES if c not in tsv_ids)
    if stale_names:
        die("NAME_MATCHES.json cells without a TSV row: %s" % stale_names[:10])
    for rec in ROWS:
        cid = rec["cell_id"]
        entries = CELL_SETS.get(cid, [])
        if not entries:
            if cid not in NO_SET:
                die("%s has no S-build disposition (MANIFEST.json)" % cid)
            if cid in NAMES:
                die("%s: a name-rule record but no set" % cid)
            why = NO_SET[cid]["why"]
            rec.update(set_id="none (S-build: %s)" % why, set_size_in_class_universe="n/a (no set built)", set_sha256="n/a",
                       set_rule_labels="n/a", set_status="no set built: " + why)
            continue
        ids, sizes, shas, labels, statuses, outcomes = [], [], [], [], [], []
        for e in entries:
            st = e["status"]
            ids.append(e["set_id"])
            shas.append(e.get("sha256") or "n/a (%s)" % st)
            sj = SET_JSON.get(e["set_id"])
            if st.startswith("built under gate"):
                sizes.append("n/a until built %s" % st[len("built "):])
                labels.append("assigned when built %s" % st[len("built "):])
                statuses.append("%s (%s)" % (st, e["reason"]))
                outcomes.append(None)
                continue
            if st.startswith("not built"):
                sizes.append("n/a (not built)")
                labels.append("n/a")
                statuses.append("%s: %s" % (st, e["reason"]))
                outcomes.append(None)
                continue
            if st.startswith("not auditable (S undefined"):  # v6.6: also 'comparator not buildable pre-freeze' 
                sizes.append("n/a (S undefined)")
                labels.append("n/a (S undefined)")
                statuses.append("not auditable (S undefined): %s -- %s" % (sj["reason"], sj["definition"]))
                outcomes.append("S undefined")
                continue
            if st == "not auditable (definition not applicable)":
                sizes.append("n/a (definition not applicable)")
                labels.append("n/a (definition not applicable)")
                statuses.append("not auditable (definition not applicable): %s -- %s" % (sj["reason"], sj["definition"]))
                outcomes.append("definition not applicable")
                continue
            if st.startswith("S conditional"):
                sizes.append("n/a until built under the gate (S conditional on a gated carrier, section 1.6 R2)")
                labels.append("assigned when built under the gate (source 1: the paper's own list), section 1.6 R2")
                statuses.append("%s: %s -- %s" % (st, sj["reason"], sj["definition"]))
                outcomes.append("S conditional")
                continue
            cd = _cell_detail(sj, cid)
            if cd is None:
                die("%s: no cells_detail entry in %s" % (cid, e["set_id"]))
            if normalize(rec["analysis_class"]) != cd["analysis_class"]:
                die("%s: the S-build's class %s differs from the row's" % (cid, cd["analysis_class"]))
            sizes.append(_universe_size(sj, rec["analysis_class"]))
            labels.append("; ".join(sj["labels"]) if sj["labels"] else "none (source 1: the paper's own list)")
            statuses.append("%s; %s -- %s%s" % (st, cd["outcome"], sj["definition"], _release(sj)))
            outcomes.append(cd["outcome"])
        fam = len(entries) > 1
        if fam:  # a family's sets, in the order of its defining table (family_cell_index)
            idx = [SET_JSON[e["set_id"]].get("family_cell_index") for e in entries]
            if idx != list(range(1, len(entries) + 1)):
                die("%s: family sets not indexed 1 ... n" % cid)
            if len(set(labels)) != 1:
                die("%s: family sets with different labels" % cid)
            rec.update(set_id=" | ".join("%d: %s" % (i, s) for i, s in zip(idx, ids)),
                       set_size_in_class_universe=" | ".join("%d: %s" % (i, s) for i, s in zip(idx, sizes)),
                       set_sha256=" | ".join("%d: %s" % (i, s) for i, s in zip(idx, shas)), set_rule_labels=labels[0],
                       set_status=" | ".join("%d: %s" % (i, s) for i, s in zip(idx, statuses)))
            rec["cell_index"] = ("1 ... %d, one per cell in the defining table's order (section 1.9): %s"
                                 % (len(entries), "; ".join("%d = %s" % (i, SET_JSON[s]["definition"].split(", cluster ")[-1])
                                                           for i, s in zip(idx, ids))))
        else:
            rec.update(set_id=ids[0], set_size_in_class_universe=sizes[0], set_sha256=shas[0], set_rule_labels=labels[0],
                       set_status=statuses[0])
        # register v6 R1: the name rule's tier, per cell (cells sharing a set may reach it by different tiers)
        nl = _name_label(cid)
        if nl is not None:
            if fam:
                die("%s: a name-rule record on a family row" % cid)
            rec["set_rule_labels"] += "; " + nl
            rec["set_status"] += "; " + nl
            SUMMARY["name_rule"][cid] = NAMES[cid]["tier"]
        # the rules' outcomes (register section 1.11 item 2)
        if "S undefined" in outcomes or "definition not applicable" in outcomes:
            if fam:
                die("%s: S undefined inside a family" % cid)
            sj = SET_JSON[entries[0]["set_id"]]
            dna = "definition not applicable" in outcomes
            prior = rec["status"]
            rec["status"] = ("not auditable (%s: %s; register section 1.11 item 2%s, register_sets/%s)"
                             % ("definition not applicable" if dna else "S undefined", sj["reason"], ", v6 R3" if dna else "",
                                entries[0]["json"]))
            if not prior.startswith("auditable"):
                rec["status"] += "; also " + prior
            rec["T"] = rec["T"] + (DNA_NOTE if dna else SU_NOTE)
            M_BEFORE_SU[cid] = rec["verdict_counted_in_m"]  # v6.7 (1): read by the near-miss view only
            rec["verdict_counted_in_m"] = "no"
            hp = rec["headline_population"]
            if hp.startswith("in"):
                rec["headline_population"] = ((HL_IN_NA_DNA if dna else HL_IN_NA_SU)
                                              + ("; also not testable as stated (sections 1.2, 1.4)" if hp.startswith(HL_NTAS) else "")
                                              + (HL_FAMILY if HL_FAMILY in hp else ""))
            SUMMARY["dna" if dna else "s_undefined"].append(cid)
        elif "S conditional" in outcomes:
            if fam:
                die("%s: S conditional inside a family" % cid)
            rec["status"] += ("; %s: S depends on a gated carrier (source 1 by the section 1.6 criterion, or the carrier naming the "
                              "cells); 'not auditable (S undefined)' where it does not define S -- see set_status and register_sets/%s"
                              % (R2_FLAG, entries[0]["json"]))
            rec["T"] = rec["T"] + R2_NOTE
            if rec["verdict_counted_in_m"] == "yes":
                rec["verdict_counted_in_m"] = M_UPPER
            hp = rec["headline_population"]
            if hp.startswith("in"):
                rec["headline_population"] = hp + ("; provisional: S conditional on a gated carrier (section 1.6 R2) -- 'not auditable "
                                                   "(S undefined)' if the carrier does not define it (section 1.2, v6)")
            SUMMARY["r2"].append(cid)
        elif any(o and o.startswith("not testable (< 5") for o in outcomes):
            sj = SET_JSON[entries[0]["set_id"]]
            n = sj["universe"][rec["analysis_class"]]["n_columns"]
            rec["status"] = ("not testable (< 5): %d columns of S in the %s universe (S-build; prereg section 4; register section "
                             "1.11 item 2; v6 R5: columns counted); also %s" % (n, rec["analysis_class"], rec["status"]))
            rec["T"] = rec["T"] + LT5_NOTE
            rec["verdict_counted_in_m"] = "no"
            rec["headline_population"] = HL_OUT_LT5 + ("; also not testable as stated" if "not testable as stated" in rec["status"]
                                                       else "")
            SUMMARY["lt5"].append(cid)
    for key, want in (("s_undefined", S_UNDEF_EXPECTED), ("dna", DNA_EXPECTED), ("r2", R2_EXPECTED), ("lt5", LT5_EXPECTED)):
        if sorted(SUMMARY[key]) != sorted(want):
            die("%s rows %s differ from the builder's section 1.11 list" % (key, sorted(set(SUMMARY[key]) ^ set(want))))
    missing = sorted(c for c in NAMES if c not in SUMMARY["name_rule"])
    if missing:
        die("name-rule records not written to a TSV row: %s" % missing[:10])
    # seed cell index of the remaining family rows (section 1.9): fixed when the defining table is read under its gate
    for rec in ROWS:
        if rec["cell_class"] == "family" and rec["cell_index"] == "0":
            rec["cell_index"] = ("UNDETERMINED: 1 ... %s, one per cell in the defining table's order, fixed when (and if) the cells "
                                 "are enumerated under the gate (section 1.9)" % (rec["n_cells"] if rec["n_cells"].isdigit() else "n"))


def apply_near_miss():
    """register v6.7 (1): the registered SECONDARY view 'near-miss comparator' -- two columns per row; a row of the view reads its
    near-miss comparator (built: set id, size in the row's class universe, whether the view counts it in m') or why it is not
    buildable either; every other row 'n/a'. Never changes a primary field."""
    view = (MANIFEST.get("comparators_v6_6") or {}).get("near_miss_view_v6_7") or {}
    by_cell = {c: e for e in view.get("sets", []) for c in e["cells"]}
    for rec in ROWS:
        cid = rec["cell_id"]
        e = by_cell.get(cid)
        if e is None:
            rec.update(secondary_view_near_miss_status="n/a (not in the near-miss view: the row's primary S stands)",
                       secondary_view_near_miss_set_id="n/a")
            continue
        head = NM_LABEL + " (register 1.6, v6.7; secondary view only -- the primary status is unchanged): "
        if e["outcome"] != "built":
            rec.update(secondary_view_near_miss_status=head + "not buildable either -- %s; not auditable in both views" % e["why"],
                       secondary_view_near_miss_set_id="none (not buildable either)")
            continue
        sj = SET_JSON[e["set_id"]]
        cls = normalize(rec["analysis_class"]).split(" ")[0]
        ncol = sj["universe"][cls]["n_columns"]
        counted = (rec["cell_class"] == "claim" and M_BEFORE_SU.get(cid) == "yes" and ncol >= 5)
        why = ("yes: a claim whose primary S is undefined only for want of a buildable comparator" if counted else
               "no: %s" % ("a descriptor cell" if rec["cell_class"] != "claim" else "< 5 columns" if ncol < 5 else
                            "not counted in m before the comparator rule"))
        rec.update(secondary_view_near_miss_status=head + "built -- %s (%s); %s columns in the %s universe; counted in m' (the "
                   "view's m): %s" % (sj["definition"], e["set_id"], fmt_int(ncol), cls, why),
                   secondary_view_near_miss_set_id=e["set_id"])


def apply_draft_placeholders():
    """--draft-for-sbuild: the S-build columns are left as placeholders (the S-build reads none of them)."""
    for rec in ROWS:
        rec.update(set_id="pending (draft for the S-build)", set_size_in_class_universe="pending", set_sha256="pending",
                   set_rule_labels="pending", set_status="pending", secondary_view_near_miss_status="pending",
                   secondary_view_near_miss_set_id="pending")
        if rec["cell_class"] == "family" and rec["cell_index"] == "0":
            rec["cell_index"] = "UNDETERMINED: pending"


# ====================================================================================================================
# 3. write, read back, check
# ====================================================================================================================
EXPECTED_M = OrderedDict([  # register section 4 as the v6 rules give it (m's lower bound: S unconditional)
    ("patel2021virtual", 3), ("giacomel2026cartography", 14), ("romerogarcia2019synaptic", 3), ("rasero2023neurogenetics", 14),
    ("buch2023asdsubgroups", 84), ("mamat2025molecular", 22), ("liu2026spatiotemporal", 1), ("pagani2026crossspecies", 10),
    ("benkarim2021connectivity", 12), ("dear2024corticalgene", 2), ("pretzsch2024patterns", 4), ("park2021subcortico", 8),
    ("moreau2020mutations", 2), ("hansen2022local", 1), ("leyhausen2024intrinsic", 27)])
EXPECTED_M_UPPER_ONLY = {}  # v6 R2; v6.5: BUCH-E-Trans-StructConstRibosome-S1 is not auditable (source 1 uncorroborated)
EXPECTED_M_IDS = {  # the claim ids the register names for m (section 4 and sections 2-3); Buch checked by family counts
    "patel2021virtual": ["PAT-C1", "PAT-C2", "PAT-C3"],
    "giacomel2026cartography": ["GIA-C%02d" % i for i in range(7, 19)] + ["GIA-MDD-U1", "GIA-MDD-D10"],
    "romerogarcia2019synaptic": ["RG-01", "RG-V01", "RG-V02"],
    "rasero2023neurogenetics": ["RA-%02d" % i for i in range(1, 15)],
    "mamat2025molecular": ["MAMAT-C1", "MAMAT-C2", "MAMAT-C3"] + ["MAMAT-E-URG-%s" % s for s in ("BP-1", "BP-2", "BP-3", "CC-1", "CC-2",
                                                                                                 "MF-1", "MF-2")]
    + ["MAMAT-E-DRG-%s" % s for s in ("BP-1", "BP-2", "CC-1", "CC-2", "MF-1", "MF-2")] + ["MAMAT-E-Tissue-URG", "MAMAT-E-Tissue-DRG"]
    + ["MAMAT-E-SEA-%s" % s for s in ("cerebellum", "cortex", "thalamus", "hippocampus")],
    "liu2026spatiotemporal": ["LIU-T3"],
    "pagani2026crossspecies": ["PAG-C%d" % i for i in range(1, 13) if i not in (9, 10)],  # v6.6: C9, C10 S undefined
    "benkarim2021connectivity": ["BENK-C1-%s-%s-%s" % (r, s, m) for r in ("cortex", "cerebellum", "striatum")
                                 for s in ("adolescence", "youngadulthood") for m in ("SD", "DD")],
    "dear2024corticalgene": ["DEAR-C1", "DEAR-C2"],
    "pretzsch2024patterns": ["PRE-D1", "PRE-GO-07", "PRE-GO-13", "PRE-GO-15"],
    "park2021subcortico": ["PARK-C%s%s" % (r, l) for r in "12" for l in "abcd"],
    "moreau2020mutations": ["MOR-C1", "MOR-C2"],
    "hansen2022local": ["HAN-C1"],
    "leyhausen2024intrinsic": ["LEY-D%d" % i for i in range(1, 10)] + ["LEY-K%d" % i for i in (1, 2, 3, 5, 6)]
    + ["LEY-C%02d" % i for i in range(1, 14)],
}
M_BEFORE = {"buch2023asdsubgroups": 84, "pagani2026crossspecies": 10}  # v6.10 (m 207 / 207); v6.11 changes no m
REGISTER_NAMED = (["SEG-C1", "SEG-C2"] + ["SEG-C3" + c for c in "abcdefg"] + ["PAT-C%d" % i for i in range(1, 5)]
                  + ["GIA-C%02d" % i for i in range(1, 25)] + ["GIA-MDD-U1", "GIA-MDD-D10", "GIA-X1", "GIA-MDD-C1", "GIA-MDD-C5", "GIA-MDD-C10"]
                  + ["RG-%02d" % i for i in range(1, 16)] + ["RG-V%02d" % i for i in range(1, 27)] + ["RG-N%02d" % i for i in range(1, 12)]
                  + ["BE-%02d" % i for i in range(1, 14)] + ["RA-%02d" % i for i in range(1, 15)] + ["RA-N1", "RA-N2", "RA-N4"]
                  + ["RA-N3-%02d" % i for i in range(1, 11)]
                  + ["BUCH-C%d" % i for i in range(1, 5)] + ["BUCH-E-ASDdown-S1", "BUCH-E-Syn-GPCR-S2", "BUCH-E-SZ-S1", "BUCH-E-SZ-S4",
                                                             "BUCH-E-MDD-S4", "BUCH-E-GAD-S4"]
                  + EXPECTED_M_IDS["mamat2025molecular"] + ["MAMAT-E-SEA-Pnoc-cortex", "MAMAT-E-SEA-cholinergic-striatum"]
                  + ["VR-C1", "VR-E1", "VR-E2", "VR-E3", "VR-E4", "VR-N1"]
                  + ["LIU-T%d" % i for i in range(1, 7)] + ["XING-FPV-all", "XING-FPV-hc", "XING-FPV-syn", "WAN-1", "WAN-2"]
                  + ["PAG-C%d" % i for i in range(1, 13)] + EXPECTED_M_IDS["benkarim2021connectivity"] + ["BENK-C2-SD", "BENK-C2-DD"]
                  + ["DEAR-C1", "DEAR-C2", "DEAR-C3", "PRE-D1", "PRE-GO-07", "PRE-GO-13", "PRE-GO-15", "PRE-X1", "PRE-D1r"]
                  + ["PRE-DG-%02d" % i for i in range(1, 7)] + ["SEG-C3-D%02d" % i for i in range(1, 72)]
                  + ["LIU-T2-STR", "LIU-T2-CBC", "LIU-T2-HIP"]
                  + ["PRE-CT%d" % i for i in range(1, 10)] + ["PRE-B%02d" % i for i in range(1, 15)]
                  + EXPECTED_M_IDS["park2021subcortico"] + ["PARK-C5", "PARK-C3", "PARK-C4", "PARK-C6"]
                  + ["PARK-C%s%s-319367" % (r, l) for r in "12" for l in "abcd"]
                  + ["MOR-C1", "MOR-C2", "MOR-C3", "MOR-T1", "MOR-T2", "MOR-R1", "MOR-R2", "MOR-R3", "MOR-R4", "HAN-C1"]
                  + EXPECTED_M_IDS["leyhausen2024intrinsic"] + ["LEY-M%d" % i for i in range(1, 5)] + ["LEY-META"]
                  + ["SEE-D%02d" % i for i in range(1, 14)] + ["SEE-M%02d" % i for i in range(1, 12)] + ["SEE-C%02d" % i for i in range(1, 11)])
EXPECTED_FOCAL = {"SEG-C1", "PAT-C1", "RG-06", "RA-02", "BUCH-E-ASDdown-S1", "MAMAT-E-URG-BP-1", "VR-E1", "XING-FPV-all"}  # register section 4
NO_FOCAL_ROWS = ("4", "9", "11")  # Berto, Liu, Wan (register section 4)
RULE66_SHA = "43cefdcc81bee3cecb1d764150f9a6d39bf814f98525fd65006a4c0bbd3fa1a1"  # register 1.6 v6.6 rule, written 2026-09-27T02:56:44Z
KEGG_LIB_SHA = {"KEGG_2015": "ac721aed19bbc618c766cf1a76cc3dfa99c1df13055073ebc3d3e112fbf69369",
                "KEGG_2016": "a501968146264e4a7ba2b2fb06ff8b9c0cb9a209655f31c095ece502e04d61f5"}  # = s_build.PIN (asserted there)
M_TOTAL = 207  # m's lower bound (v6.8 B S1): v6.7's 211 without the four BUCH-E-ASDdown claims (asdM12 moved to the near-miss
# view); the 23 claims whose comparator is not buildable pre-freeze stay out (Buch 21 -- ASDdown / ASDup / FMRP / CNSauto x 4,
# Vocal x 3, TS x 2 -- and PAG-C9, PAG-C10)
M_TOTAL_UPPER = 207  # equal to the lower bound (no upper-bound-only row since v6.5)
M_SECONDARY_NEAR_MISS = 223  # v6.7 (1) / v6.8: the near-miss view's m' = m + the 16 claims with a built near-miss comparator
# (ASDdown x 4 -- v6.8 --, ASDup x 4, FMRP x 4, TS S1 / S4, PAG-C9, PAG-C10); CNSauto x 4 and Vocal x 3 not buildable in either
GATE_BY_TARGET = {  # register section 0 (v5); Liu: T3 under G2, the rest ungated (row level)
    "segura2024symptommapping": "none", "patel2021virtual": "G2", "giacomel2026cartography": "G2", "romerogarcia2019synaptic": "G1",
    "berto2022connectivity": "G1", "rasero2023neurogenetics": "G1", "buch2023asdsubgroups": "G1", "mamat2025molecular": "G1",
    "vairam2026hyperhypo": "none", "xing2026interpretable": "none", "wan2026abide2multiplex": "G1", "pagani2026crossspecies": "G1",
    "benkarim2021connectivity": "G1", "dear2024corticalgene": "G1+G2", "pretzsch2024patterns": "G2", "park2021subcortico": "G1",
    "moreau2020mutations": "none", "hansen2022local": "G2", "leyhausen2024intrinsic": "G2", "seelemeyer2025decomposing": "G2"}
# the interim population the register's lists imply (section 1.2: every gate closed; Vairam / Roy deferred) -- a compiler expectation
# (v5: SEG-C3b / SEG-C3d leave it -- not testable (< 5), section 1.11 item 2)
EXPECTED_INTERIM = (["SEG-C1"] + ["SEG-C3" + c for c in "aceg"] + ["SEG-C3f"] + ["LIU-T1", "LIU-T2", "LIU-T4", "LIU-T5", "LIU-T6"]
                    + ["XING-FPV-all", "XING-FPV-hc", "XING-FPV-syn"])
# population units behind each gate, from the register's lists (compiler expectation): G1 = Romero-Garcia 41 (RG-01 ... RG-15,
# RG-V01 ... V26; families once) + Berto 9 (BE-01, BE-06 ... BE-13) + Rasero 14 + Buch 106 + Mamat 24 + Wan 2; G2 = Patel 4
EXPECTED_DEFERRED_POP = {"G1": 196, "G2": 4}
ON_OPENING = "; on opening: "
M_VALUES = ("yes", "no", M_UPPER)


def base_status(s):
    """the status without its leading deferral flag (register sections 0, 1.8, v4)."""
    for pre in (GATE_STATUS["G1"], GATE_STATUS["G2"], DEAR_STATUS, VR_DEFER):
        p = normalize(pre) + "; "
        if s.startswith(p):
            return s[len(p):]
    return s


def hl_final(r):
    """the row's population once every gate has opened (section 1.2)."""
    hp = r["headline_population"]
    return hp.split(ON_OPENING, 1)[1] if hp.startswith("out (interim)") else hp


# register v6 R8: one precedence order for the composition -- deferred > not testable (< 5) > not auditable > not testable as
# stated > component-level > no calibrated test; a claim is counted once, by the first flag it carries in this order (every flag
# stays reported in its status). Deferred and not testable (< 5) rows are outside the population, so inside it the order starts
# at 'not auditable'.
PRECEDENCE = ("deferred", "not testable (< 5)", "not auditable", "not testable as stated", "component-level", "no calibrated test")


def row_flags(r):
    """the status flags a row carries (its primary flag and every 'also ...' flag), R2's conditional flag aside."""
    s = r["status"]
    b = base_status(s)
    f = set()
    if b != s:
        f.add("deferred")
    for flag in ("not testable (< 5)", "not auditable", "not testable as stated", "no calibrated test"):
        if b.startswith(flag) or ("; also " + flag) in b or (" also " + flag) in b:
            f.add(flag)
    if r["claim_form"] == "component":
        f.add("component-level")
    return f


def pop_category(r, view="upper"):
    """the composition of the population by status (section 1.2; R8 precedence). view 'upper': a row whose S is conditional on a
    gated carrier (R2) counted as if the carrier defines S (provisional); view 'lower': counted as not auditable."""
    f = row_flags(r) - {"deferred"}  # the population on opening: the deferral is not a category
    if view == "lower" and normalize(R2_FLAG) in r["status"]:
        f.add("not auditable")
    for p in PRECEDENCE[1:]:
        if p in f:
            return p
    b = base_status(r["status"])
    return "tested (full verdict)" + (" [conditional on its carrier]" if b.startswith("conditional") else "")


TARGET_ORDER = ["segura2024symptommapping", "patel2021virtual", "giacomel2026cartography", "romerogarcia2019synaptic",
                "berto2022connectivity", "rasero2023neurogenetics", "buch2023asdsubgroups", "mamat2025molecular", "vairam2026hyperhypo",
                "liu2026spatiotemporal", "xing2026interpretable", "wan2026abide2multiplex", "pagani2026crossspecies",
                "benkarim2021connectivity", "dear2024corticalgene", "pretzsch2024patterns", "park2021subcortico", "moreau2020mutations",
                "hansen2022local", "leyhausen2024intrinsic", "seelemeyer2025decomposing"]


def header_lines(draft_sha, reg_sha_masked, anc_ok, vairam_sha, a4_sha, a5_sha, script_sha, n_rows, m_total, m_upper):
    L = ["# claims_register.tsv -- machine-readable table of arcs/audit/claims_register.md (A1 audit claims register): one row per "
         "registered cell of all 21 targets",
         "# status: DRAFT compiled for verification, NOT frozen; frozen together with claims_register.md (bench.py freeze), the S-build "
         "manifest and arcs/audit/register_freeze_manifest.json, and never edited after the freeze (register header). Precedence: "
         "claims_register.md governs, then this TSV, then the drafts.",
         "# register: arcs/audit/claims_register.md (DRAFT v6.11) sha256 %s, computed with its one 'TSV sha256 <64 hex>' field (register "
         "section 7, which records this file's sha256) replaced by 64 zeros -- the two files cannot both carry the other's full hash; "
         "the unmasked hash is in arcs/audit/register_freeze_manifest.json. Read from the working copy at build time, which is "
         "committed unchanged right after the build; no commit id is recorded here, so a rebuild on that commit reproduces this "
         "file. Register at or after commit %s: %s" % (reg_sha_masked, REGISTER_MIN_COMMIT, anc_ok),
         "# drafts (register section 8, incorporated by reference; each sha256 verified equal to section 8 before the build):"]
    for name, sha in draft_sha.items():
        L.append("#   arcs/audit/register_work/%s sha256 %s" % (name, sha))
    L += ["# Vairam / Roy definitions (register 2.9): literature/notes/vairam2026hyperhypo.md sha256 %s" % vairam_sha,
          "# vocabulary read: arcs/audit/prereg_amend_4.md section 2 (sha256 %s); arcs/audit/prereg_amend_5.md sections 3-4 (the "
          "calibration and power labels of the published-null readings; sha256 %s)" % (a4_sha, a5_sha),
          "# pre-freeze outputs read (register section 1.11, binding; labels, counts and hashes only): arcs/audit/register_sets/"
          "MANIFEST.json sha256 %s (%d set entries; every per-set JSON verified against it), SEGURA_S7_TERMS.json sha256 %s, "
          "PRE_DG_ROWS.json sha256 %s, NAME_MATCHES.json sha256 %s; arcs/audit/register_maps/: %s"
          % (sha256_file(SETS_DIR / "MANIFEST.json"), len(MANIFEST["sets"]), sha256_file(SETS_DIR / "SEGURA_S7_TERMS.json"),
             sha256_file(SETS_DIR / "PRE_DG_ROWS.json"),
             sha256_file(SETS_DIR / "NAME_MATCHES.json") if (SETS_DIR / "NAME_MATCHES.json").exists() else "absent (draft)",
             ", ".join("%s sha256 %s" % (q.name, sha256_file(q)) for q in sorted(MAPS_DIR.glob("*.json")))),
          "# built by arcs/audit/claims_register_tsv_build.py (sha256 %s): python -X utf8 arcs/audit/claims_register_tsv_build.py; a "
          "compilation from text and the pre-freeze outputs -- no map, gated carrier or audit-target material opened" % script_sha,
          "# rows: %d; m, lower bound (rows with verdict_counted_in_m = yes: S unconditional): %d; m, upper bound (also the rows "
          "counted 'yes (upper bound only ...)': S conditional on a gated carrier, section 1.6 R2, if every such carrier qualifies -- "
          "an assumption the source-1 criterion may structurally refuse, register section 4, v6.4 N3; since v6.5 no row is counted "
          "so): %d "
          "(register section 4 as the v6.11 rules give it: %d / %d); m' of the registered secondary view '%s' (register 1.6, "
          "v6.7): %d (register section 4: %d)" % (n_rows, m_total, m_upper, M_TOTAL, M_TOTAL_UPPER, NM_LABEL,
                                                 m_total + sum(1 for r in ROWS if "counted in m' (the view's m): yes"
                                                               in r.get("secondary_view_near_miss_status", "")),
                                                 M_SECONDARY_NEAR_MISS),
          "# universe (register section 1.6, v6 R5): %s" % UNIVERSE_TXT,
          "# name rule (register sections 1.1 rule G and 1.6, v6 R1): every GO, KEGG, MSigDB, Reactome and figure-label mapping -- (a) the "
          "exact name in the pinned release; else (b) a synonym of any scope, or a former name, identifying exactly one live term, "
          "labelled 'S matched by <scope> synonym'; else (c) case, UK / US spelling or singular / plural normalisation identifying "
          "exactly one term, labelled; else 'S undefined'. The tier of every mapped row is in its set_rule_labels and set_status "
          "(register_sets/NAME_MATCHES.json; src_register/name_match.py)",
          "# sources (register section 1.6, v6.5): one source-1 criterion for every source-1 branch, per cell id (register_maps/"
          "carrier_tests.json source1_lists.cells: name alternatives and printed sizes; rival_names) -- a carrier list qualifies only if "
          "its sheet name, table title, caption or own title carries input wording, neither its own title nor the caption carries "
          "result wording or names one of the paper's maps, subgroups or cohorts (leading edge, core, driving, top, PLS, loading, "
          "weight, enriched, decoded, overlap or hit genes; '_' and '.' read as spaces) and no column title of its table carries "
          "statistics wording, and no cell of its sheet other than the lists' own genes carries statistics, result or map wording "
          "(v6.4 N1); and (v6.5) the one list it admits is source 1 only if corroborated -- Jaccard >= .80 with the cell's pinned "
          "external definition (by HGNC gene in the class universe), else a length equal to its printed size; a cell with neither is "
          "not auditable (S undefined: source 1 uncorroborated); KEGG releases -- (i) a tool library: that library's "
          "release (Vairam / Roy KEGG_2021_Human; Romero-Garcia's families KEGG_2015 or KEGG_2016, the one reaching every pathway name "
          "of the gated table, a printed hsa id selecting KEGG_2016, v6.2 P5 / v6.3 O4); (ii) otherwise the obtainable KEGG release closest in date to the paper's "
          "retrieval, else submission, date, Enrichr snapshots counting as releases (Leyhausen KEGG_2021_Human; Mamat %s)" % KEGG_MAMAT,
          "# seeds: numpy.random.SeedSequence([20260925, 100 + target_no, row, leg, map_index, cell_index]) (register section 1.9, v5); "
          "the row numbers below are those keys and are fixed by this file; map_index 0 for a single-map cell, Mamat's two-cohort cells "
          "0 = ABIDE I and 1 = ABIDE II, Romero-Garcia's validation family RG-V23 0 = Val1 and 1 = Val2; cell_index 0 for a single cell, 1 ... n for the cells of a family (one row, n cells) or of a unit "
          "the register numbers (SEG-C3-D01 ... D71, PRE-DG-01 ... 06, RA-N3-01 ... 10) in the order its defining table lists them; "
          "'n/a' where no T is registered (no seed); 'UNDETERMINED' where the index is fixed only when a table is read under a gate",
          "# gates (register section 0, as of DRAFT v6.11): G1 = Park, Benkarim, Pagani, Wan, Rasero, Buch, Mamat, Berto, Romero-Garcia -- opens when "
          "A3's ABIDE II results are committed (A3 amendment 2 as frozen, route plants passed, the operator's unsealing go, step 6''s "
          "results -- H5R and its descriptors, H1, H3 pair b, H4 stage 2, K4 -- committed), or when A3 records that no ABIDE II analysis will run and the (b-ii) fallback is declined "
          "(under the notice rule), or on any other A3 path when A3 records that no further ABIDE II analysis will run (same notice "
          "rule); G2 = Patel, "
          "Giacomel, Hansen, Liu T3, Pretzsch, Leyhausen, Seelemeyer -- opens when A3 amendment 1 is frozen and A3's step 3 (v) (the "
          "T1 / T2 tests) is committed; ungated = Segura, Moreau, Liu T1 / T2 / T4 / T5 (and T6, gate none by register 2.10), Xing and the "
          "S-build of external sets; Dear deferred pending provenance (gate value G1+G2 once established); Vairam / Roy deferred (prereg "
          "section 5.1; gate none). While a gate is closed, every row it covers carries 'deferred (gate Gx closed)' as the first flag of "
          "its status, its other flags kept",
          "# headline_population (section 1.2; frozen-11 rows): 'in' = in the interim population now; 'out (interim): deferred (gate "
          "Gx closed; ...); on opening: in|out ...' = listed apart and counted neither way while the gate is closed, with the row's "
          "population once it opens; 'out: ...' = excluded by a frozen text (descriptor, published-null, non-ASD, not-ASD, not testable "
          "(< 5 columns; prereg section 4); an added target is never headline) or deferred without a gate (Vairam / Roy). Not testable as "
          "stated, not auditable (incl. S undefined), component-level and 'no calibrated test' claims are in as non-survivals; a family "
          "counts once. A full-verdict claim leaves the population if the section 1.5 check flags it 'not reproduced'. Composition (v6 "
          "R8): one precedence order -- deferred > not testable (< 5) > not auditable > not testable as stated > component-level > no "
          "calibrated test; a row whose S is conditional on a gated carrier (R2) is counted provisionally ('; provisional: ...')",
          "# sets (register sections 1.6, 1.11 items 1-4): the S-build ran before the freeze; every row carries its disposition in "
          "set_id (the register_sets id; a family's sets as '<cell index>: <id>' in its defining table's order; 'none (...)' where the "
          "row has no set), set_size_in_class_universe (columns of S in the row's analysis-class universe, its HGNC genes beside; the "
          "four class universes hold the same 15,633 columns), set_sha256 (of the per-set JSON, as MANIFEST.json records it), set_rule_labels ('S re-derived', "
          "'release substituted', ...) and set_status (the S-build status and the outcome in the row's class, then the set's definition "
          "and release). Sets inside a gated carrier read 'built under gate Gx' and are built under that gate by the same rules; an "
          "S-undefined set whose source 1 could lie inside a gated carrier reads 'S conditional (source 1 in a gated carrier; else not "
          "auditable (S undefined))' (v6 R2)",
          "# fields: from the register first, then the draft, then the pre-freeze outputs; 'UNDETERMINED: <why>' where the texts leave a "
          "field open until a gate opens; a section sign with no document named, and 'register §x.y', = claims_register.md; 'draft' = "
          "register_work/<target_key>.md; 'paper' = the target paper",
          "# every route: prereg section 2 left + midline parcels primary, bilateral a multiverse cell (section 1.7), unless the row says "
          "otherwise; the minus sign in directions and values is U+2212",
          "# columns: row | target_no | target_key | frozen11_row (register section 4 table, or 'added') | cell_id | cell_class (claim | "
          "published-null | non-ASD-outcome | not-ASD-claim | descriptor | family) | claim_form (set-vs-map | decoded-list | "
          "PLS-enrichment | component | gene-set-only | other) | map (gated maps: their identity before the freeze, section 1.11 item 6) | "
          "set_S | set_id | set_size_in_class_universe | set_sha256 | set_rule_labels | set_status | T | direction | analysis_class | "
          "route | inference_level (section 1.3) | status (section 1.8; gated rows: the deferral first) | headline_population (section "
          "1.2) | reproduction (section 1.5) | published_value_and_location | gate (G1 | G2 | G1+G2 | none) | focal (per-row focal of the "
          "frozen 11) | verdict_counted_in_m (yes | no | yes (upper bound only: S conditional ..., v6 R2)) | dependencies | notes (incl. the carrier tests of sections 1.8 and 1.11 item 8 on "
          "conditional rows) | n_cells | map_index (section 1.9) | cell_index (section 1.9) | secondary_view_near_miss_status | "
          "secondary_view_near_miss_set_id (register 1.6, v6.7: the registered secondary view '" + NM_LABEL + "' -- never a "
          "primary field; 'n/a' outside the view)",
          "# n_cells: the number of registered cells a row stands for (1 for a single cell; > 1 or UNDETERMINED on family rows, whose "
          "count is fixed when the defining table is read under the gate, section 1.1)",
          "# ids: notes say 'id: register' (named by claims_register.md), 'id: draft' (named by the draft) or 'id: compiler' (assigned here "
          "because neither text names the cell)"]
    return L


def normalize(s):
    """Typography only (deterministic): the register's section sign, minus sign, arrows and relation signs."""
    s = re.sub(r"\bsections (?=\d)", "§§", s)
    s = re.sub(r"\bsection (?=\d)", "§", s)
    s = re.sub(r"\b([Rr]egister) (?=\d)", "\\1 §", s)
    s = re.sub(r"(?:^|(?<=[\s(/=,;:]))-(?=[\d.])", M, s)
    s = s.replace(" -- ", " — ")
    s = s.replace("+-", "±").replace("<=", "≤").replace(">=", "≥").replace("->", "→").replace("R^2", "R²")
    return s


def clean(v):
    s = normalize(str(v))
    for bad in ("\t", "\n", "\r"):
        if bad in s:
            die("field contains a tab or newline: " + s[:80])
    return s


# ---------------------------------------------------------------- register v6 R4: section 4 numbers, section 1.11 id lists
def _fenced_block(text, heading_prefix, marker):
    """the first fenced block (``` ... ```) of the section whose heading starts with heading_prefix and whose first line holds
    marker; returns its lines, or None."""
    a = text.find("\n" + heading_prefix)
    if a < 0:
        return None
    nxt = re.search(r"\n#{2,3} ", text[a + 1:])
    sec = text[a: a + 1 + nxt.start()] if nxt else text[a:]
    for m in re.finditer(r"\n```[^\n]*\n(.*?)\n```", sec, re.S):
        lines = m.group(1).split("\n")
        if lines and marker in lines[0]:
            return lines[1:]
    return None


def parse_register_blocks(path=None):
    """R4: claims_register.md section 4's numbers block ('key = value') and section 1.11's id-list block ('key [n]: a, b, ...')."""
    text = pathlib.Path(path or REGISTER).read_text(encoding="utf-8")
    errs, nums, ids = [], OrderedDict(), OrderedDict()
    b4 = _fenced_block(text, "## 4.", "R4: section 4 numbers")
    if b4 is None:
        errs.append("register section 4 (R4): no fenced numbers block ('R4: section 4 numbers') found")
    for ln in b4 or []:
        if not ln.strip() or ln.startswith("#"):
            continue
        m = re.match(r"^(.+?) = (\d+)$", ln.strip())
        if not m:
            errs.append("register section 4 (R4): unparsable line '%s'" % ln[:60])
            continue
        if m.group(1) in nums:
            errs.append("register section 4 (R4): '%s' given twice" % m.group(1))
        nums[m.group(1)] = int(m.group(2))
    b11 = _fenced_block(text, "### 1.11", "R4: section 1.11 id lists")
    if b11 is None:
        errs.append("register section 1.11 (R4): no fenced id-list block ('R4: section 1.11 id lists') found")
    for ln in b11 or []:
        if not ln.strip() or ln.startswith("#"):
            continue
        m = re.match(r"^(.+?) \[(\d+)\]: (.*)$", ln.strip())
        if not m:
            errs.append("register section 1.11 (R4): unparsable line '%s'" % ln[:60])
            continue
        items = [] if m.group(3).strip() == "none" else [x.strip() for x in m.group(3).split(";" if "label" in m.group(1) else ",")]
        ids[m.group(1)] = (int(m.group(2)), items)
    return nums, ids, errs


def register_numbers(back, interim, final, deferred_pop, m_total, m_upper, m_by, m_up_by):
    """R4: the section 4 numbers as this TSV gives them (keys are the register's)."""
    d = OrderedDict()
    d["rows"] = len(back)
    d["m.lower"] = m_total
    d["m.upper"] = m_upper
    d["m.secondary.near_miss"] = m_total + sum(1 for r in back if "counted in m' (the view's m): yes" in r["secondary_view_near_miss_status"])
    for key in TARGET_ORDER:
        if m_by.get(key, 0) or m_up_by.get(key, 0):
            d["m.target.%s" % key] = m_by.get(key, 0)
        if m_up_by.get(key, 0):
            d["m.upper_only.target.%s" % key] = m_up_by[key]
    d["population.interim"] = len(interim)
    for cat, n in sorted(Counter(pop_category(r) for r in interim).items()):
        d["population.interim.%s" % cat] = n
    d["population.full (at most)"] = len(final)
    for cat, n in sorted(Counter(pop_category(r) for r in final).items()):
        d["population.full.%s" % cat] = n
    d["population.full.provisional (S conditional, R2)"] = sum(1 for r in final if normalize(R2_FLAG) in r["status"])
    for cat, n in sorted(Counter(pop_category(r, "lower") for r in final).items()):
        d["population.full.lower view.%s" % cat] = n
    d["population.full.not auditable and also not testable as stated"] = sum(
        1 for r in final if {"not auditable", "not testable as stated"} <= row_flags(r))
    for g in ("G1", "G2"):
        d["gate.%s.units" % g] = len(deferred_pop[g])
    d["buch.units"] = sum(1 for r in final if r["target_key"] == "buch2023asdsubgroups")
    for form in ("component-level in form", "other form"):
        for na in ("not auditable", "auditable"):
            d["crosstab.%s.%s" % (form, na)] = sum(
                1 for r in final if (r["claim_form"] == "component") == (form == "component-level in form")
                and ("not auditable" in row_flags(r)) == (na == "not auditable"))
    return d


def register_id_lists(back):
    """R4: the section 1.11 id lists as this TSV (and the S-build's records) give them."""
    order = {r["cell_id"]: int(r["row"]) for r in back}
    byrow = lambda xs: sorted(xs, key=lambda c: order[c])  # noqa: E731
    d = OrderedDict()
    d["not auditable (S undefined)"] = byrow(SUMMARY["s_undefined"])
    d["not auditable (definition not applicable)"] = byrow(SUMMARY["dna"])
    d["S conditional (R2)"] = byrow(SUMMARY["r2"])
    d["not testable (< 5)"] = byrow(SUMMARY["lt5"])
    nb = {c: e for c, e in NAMES.items() if e["target_key"] != "buch2023asdsubgroups"}
    for t, key in (("b", "name rule (b)"), ("c", "name rule (c)"), (None, "name rule S undefined")):
        d[key] = byrow([c for c, e in nb.items() if e["tier"] == t])
    buch = [NAMES[c] for c in byrow([c for c, e in NAMES.items() if e["target_key"] == "buch2023asdsubgroups"])]
    for t, key in (("a", "Buch labels, name rule (a)"), ("b", "Buch labels, name rule (b)"), ("c", "Buch labels, name rule (c)"),
                   (None, "Buch labels, name rule S undefined")):
        labs = []
        for e in buch:
            if e["tier"] == t and e["printed"] not in labs:
                labs.append(e["printed"])
        d[key] = labs
    return d


def main():
    draft_sha = verify_inputs()
    if DRAFT_FOR_SBUILD:
        apply_draft_placeholders()  # only to feed the S-build (it reads none of the S-build columns); no checks follow
    else:
        apply_sbuild()  # register section 1.11 (v6): the S-build dispositions and outcomes, before the gate flags
        apply_near_miss()  # register v6.7 (1): the secondary view's two columns (never a primary field)
    apply_gates()
    reg_sha, reg_sha_masked = register_hashes()
    rc, reg_commit = git("log", "-1", "--format=%H", "--", "arcs/audit/claims_register.md")
    if rc != 0 or not reg_commit:
        reg_commit = "UNDETERMINED: git log failed"
    rc2, porcelain = git("status", "--porcelain", "--", "arcs/audit/claims_register.md")
    reg_clean = "yes" if (rc2 == 0 and porcelain == "") else ("no (modified after the commit)" if rc2 == 0 else "UNDETERMINED")
    rc3, _ = git("merge-base", "--is-ancestor", REGISTER_MIN_COMMIT, reg_commit) if not reg_commit.startswith("UNDETERMINED") else (1, "")
    anc_ok = "yes" if rc3 == 0 else "UNDETERMINED / no"
    if rc3 != 0 and not reg_commit.startswith("UNDETERMINED"):
        die("the register's last commit %s does not descend from %s" % (reg_commit, REGISTER_MIN_COMMIT))
    vairam_sha = sha256_file(VAIRAM_NOTE)
    a4_sha, a5_sha = sha256_file(AMEND4), sha256_file(AMEND5)
    script_sha = sha256_file(HERE)

    # assign row numbers deterministically, validate records
    rows = []
    for i, rec in enumerate(ROWS, start=1):
        rec = dict(rec)
        rec["row"] = str(i)
        missing = [c for c in COLS if c not in rec or rec[c] is None or str(rec[c]).strip() == ""]
        if missing:
            die("row %d (%s) lacks fields: %s" % (i, rec.get("cell_id"), ", ".join(missing)))
        extra = [k for k in rec if k not in COLS]
        if extra:
            die("row %d (%s) has unknown fields: %s" % (i, rec.get("cell_id"), ", ".join(extra)))
        rows.append(rec)
    m_total = sum(1 for r in rows if r["verdict_counted_in_m"] == "yes")
    m_upper = m_total + sum(1 for r in rows if r["verdict_counted_in_m"] == M_UPPER)

    lines = [normalize(h) for h in header_lines(draft_sha, reg_sha_masked, anc_ok, vairam_sha, a4_sha, a5_sha, script_sha,
                                                len(rows), m_total, m_upper)]
    lines.append("\t".join(COLS))
    for r in rows:
        lines.append("\t".join(clean(r[c]) for c in COLS))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    if DRAFT_FOR_SBUILD:
        print("DRAFT FOR THE S-BUILD written (no S-build dispositions, no checks): %d rows; %s sha256 %s -- run src_register/"
              "s_build.py, then this builder without --draft-for-sbuild" % (len(rows), OUT.relative_to(ROOT).as_posix(), sha256_file(OUT)))
        return

    # ------------------------------------------------------------------ read back and check
    raw = OUT.read_bytes()
    if b"\r" in raw:
        die("CR found in the output")
    text = raw.decode("utf-8")
    body = [ln for ln in text.split("\n") if ln and not ln.startswith("#")]
    hdr = body[0].split("\t")
    if hdr != COLS:
        die("header mismatch on read-back")
    back = [dict(zip(COLS, ln.split("\t"))) for ln in body[1:]]
    errors = []
    if len(back) != len(rows):
        errors.append("row count differs on read-back")
    for i, r in enumerate(back, start=1):
        if len(r) != len(COLS):
            errors.append("row %d: wrong field count" % i)
        if r["row"] != str(i):
            errors.append("row numbers not consecutive at %d" % i)
        if r["cell_class"] not in CELL_CLASSES:
            errors.append("%s: cell_class %s" % (r["cell_id"], r["cell_class"]))
        if r["claim_form"] not in CLAIM_FORMS:
            errors.append("%s: claim_form %s" % (r["cell_id"], r["claim_form"]))
        if r["focal"] not in ("yes", "no") or r["verdict_counted_in_m"] not in [normalize(v) for v in M_VALUES]:
            errors.append("%s: focal / m not yes|no (m: or the R2 upper-bound value)" % r["cell_id"])
        if r["gate"] not in ("G1", "G2", "G1+G2", "none"):
            errors.append("%s: gate %s" % (r["cell_id"], r["gate"]))
        if not (r["headline_population"].startswith("in") or r["headline_population"].startswith("out")):
            errors.append("%s: headline_population must start with in / out" % r["cell_id"])
        if not (r["reproduction"].startswith("4.1 check") or r["reproduction"].startswith(normalize("descriptive (amendment 4 section 2)"))
                or r["reproduction"].startswith("not reproduced (documented source defect") or r["reproduction"].startswith("UNDETERMINED")):
            errors.append("%s: reproduction form" % r["cell_id"])
        if not (r["n_cells"].isdigit() or r["n_cells"].startswith("UNDETERMINED")):
            errors.append("%s: n_cells" % r["cell_id"])
        if r["cell_class"] == "family" and r["n_cells"] == "1":
            errors.append("%s: family row with n_cells 1" % r["cell_id"])
        bs = base_status(r["status"])
        if r["verdict_counted_in_m"] in ("yes", normalize(M_UPPER)):
            if (r["verdict_counted_in_m"] == "yes") == (normalize(R2_FLAG) in r["status"]):
                errors.append("%s: m's upper-bound value iff the row's S is conditional (R2)" % r["cell_id"])
            if r["cell_class"] not in ("claim", "published-null", "non-ASD-outcome"):
                errors.append("%s: m row of class %s" % (r["cell_id"], r["cell_class"]))
            if bs.startswith(("not testable", "not auditable", "no calibrated test", "UNDETERMINED", "deferred")):
                errors.append("%s: m row with status %s" % (r["cell_id"], bs[:40]))
            if r["target_key"] == "vairam2026hyperhypo":
                errors.append("%s: Vairam / Roy's deferred claims are not counted in m (register section 4)" % r["cell_id"])
        hp = r["headline_population"]
        if not (hp.startswith("in: ") or hp.startswith("out: ") or (hp.startswith("out (interim): deferred (gate G")
                                                                    and ON_OPENING in hp)):
            errors.append("%s: headline_population form" % r["cell_id"])
        if r["frozen11_row"] == "added" and not hp.startswith("out: "):
            errors.append("%s: added target in the headline" % r["cell_id"])
        if r["cell_class"] in ("descriptor", "published-null", "non-ASD-outcome", "not-ASD-claim") and hl_final(r).startswith("in"):
            errors.append("%s: %s in the headline population" % (r["cell_id"], r["cell_class"]))
        # gates (register section 0, v4)
        want_gate = GATE_BY_TARGET.get(r["target_key"], "G2" if r["cell_id"] == "LIU-T3" else "none")
        if r["gate"] != want_gate:
            errors.append("%s: gate %s, register section 0 says %s" % (r["cell_id"], r["gate"], want_gate))
        if r["gate"] in GATE_STATUS:
            if not r["status"].startswith(normalize(GATE_STATUS[r["gate"]]) + "; "):
                errors.append("%s: gated row without the deferral flag" % r["cell_id"])
            if r["frozen11_row"] != "added" and hp.startswith("in"):
                errors.append("%s: gated frozen-11 row in the interim population" % r["cell_id"])
        elif r["gate"] == "G1+G2":
            if not r["status"].startswith(normalize(DEAR_STATUS) + "; "):
                errors.append("%s: Dear row without 'deferred pending provenance'" % r["cell_id"])
        elif r["target_key"] == "vairam2026hyperhypo":
            if not (r["status"].startswith(normalize(VR_DEFER)) and hp == normalize(HL_VR)):
                errors.append("%s: Vairam / Roy row not deferred (register section 2.9)" % r["cell_id"])
        elif r["status"].startswith("deferred"):
            errors.append("%s: ungated row carries a deferral" % r["cell_id"])
        mi = r["map_index"]
        if not (mi == "0" or mi.startswith(normalize(MAPIDX_MAMAT)) or mi == normalize(MAPIDX_RGVAL) or mi == MAPIDX_NA
                or mi.startswith("UNDETERMINED")):
            errors.append("%s: map_index %s" % (r["cell_id"], mi[:30]))
        if (mi == MAPIDX_NA) != r["T"].startswith("none"):
            errors.append("%s: map_index n/a iff no registered T" % r["cell_id"])
        if (r["map"] == normalize(MA_BOTH)) != mi.startswith(normalize(MAPIDX_MAMAT)):
            errors.append("%s: Mamat two-cohort cells carry map index 0 / 1 (section 1.9)" % r["cell_id"])
    ids = [r["cell_id"] for r in back]
    dup = [k for k, v in Counter(ids).items() if v > 1]
    if dup:
        errors.append("duplicate ids: " + ", ".join(dup))
    order = [int(r["target_no"]) for r in back]
    if order != sorted(order) or sorted(set(order)) != list(range(1, 22)):
        errors.append("target order broken or a target missing")
    keys = OrderedDict()
    for r in back:
        keys.setdefault(int(r["target_no"]), r["target_key"])
    if list(keys.values()) != TARGET_ORDER:
        errors.append("target keys / numbers differ from register sections 2-3")
    # m per target and ids
    m_by = Counter(r["target_key"] for r in back if r["verdict_counted_in_m"] == "yes")
    for key in TARGET_ORDER:
        want = EXPECTED_M.get(key, 0)
        if m_by.get(key, 0) != want:
            errors.append("m for %s: %d, register section 4 says %d" % (key, m_by.get(key, 0), want))
    for key, want_ids in EXPECTED_M_IDS.items():
        have = [r["cell_id"] for r in back if r["target_key"] == key and r["verdict_counted_in_m"] == "yes"]
        if sorted(have) != sorted(want_ids):
            errors.append("m ids for %s differ from the register: extra %s, missing %s"
                          % (key, sorted(set(have) - set(want_ids)), sorted(set(want_ids) - set(have))))
    gia_pn = [r for r in back if r["target_key"] == "giacomel2026cartography" and r["verdict_counted_in_m"] == "yes"
              and r["cell_class"] == "published-null"]
    if len(gia_pn) != 12 or sum(1 for r in gia_pn if base_status(r["status"]).startswith("resolution-limited")) != 6:
        errors.append("Giacomel published-null m cells: need 12 with 6 resolution-limited")
    buch_m = [r["cell_id"] for r in back if r["target_key"] == "buch2023asdsubgroups"
              and r["verdict_counted_in_m"] in ("yes", normalize(M_UPPER))]  # v6: the R2 row counts in the upper bound
    fam = Counter()
    for c in buch_m:
        if c.startswith("BUCH-C"):
            fam["component"] += 1
        else:
            tok = c.split("-")[2]
            fam[{"ASDdown": "ASD", "ASDup": "ASD", "FMRP": "ASD", "SFARIsyn": "ASD", "SPARK": "ASD", "CNSauto": "nonpsych",
                 "Osteo": "nonpsych", "Vocal": "vocal", "ADHD": "ADHD", "TS": "TS", "Syn": "syn", "Imm": "imm", "Trans": "trans"}.get(tok, "?" + tok)] += 1
    want_fam = {"component": 4, "ASD": 7, "nonpsych": 3, "ADHD": 2, "syn": 32, "imm": 32, "trans": 4}  # v6.8 (= v6.6; v6.7: ASD
    # 11; v6.5: ASD 19, nonpsych 7, vocal 3, TS 2 -- ASDdown (v6.8, B S1) / ASDup / FMRP / CNSauto / Vocal / TS: no buildable comparator)
    if dict(fam) != want_fam:
        errors.append("Buch families %s differ from register 2.7 %s" % (dict(fam), want_fam))
    buch_desc = [r for r in back if r["target_key"] == "buch2023asdsubgroups" and r["cell_class"] == "descriptor"]
    n16 = sum(1 for r in buch_desc if "One of the 16 stated non-enrichments" in r["notes"])
    if n16 != 16:
        errors.append("Buch stated non-enrichments: %d, register 2.7 says 16" % n16)
    for cid in ["BUCH-E-Syn-GPCR-S2", "BUCH-E-SZ-S1", "BUCH-E-SZ-S4", "BUCH-E-MDD-S4", "BUCH-E-GAD-S4"]:
        if cid not in [r["cell_id"] for r in buch_desc]:
            errors.append("%s should be a descriptor (register 2.7)" % cid)
    n_claims = sum(1 for r in back if r["target_key"] == "buch2023asdsubgroups" and r["cell_class"] == "claim"
                   and not r["cell_id"].startswith("BUCH-C"))
    if n_claims != 102 or sum(1 for c in buch_m if not c.startswith("BUCH-C")) != 80:
        errors.append("Buch enrichment claims: register 2.7 says 102, 80 of them in m (v6.8)")
    missing_named = [c for c in REGISTER_NAMED if c not in ids]
    if missing_named:
        errors.append("register-named ids missing: " + ", ".join(missing_named))
    focal = {r["cell_id"] for r in back if r["focal"] == "yes"}
    if focal != EXPECTED_FOCAL:
        errors.append("focal set %s differs from register section 4 %s" % (sorted(focal), sorted(EXPECTED_FOCAL)))
    for f11 in NO_FOCAL_ROWS:
        if any(r["focal"] == "yes" for r in back if r["frozen11_row"] == f11):
            errors.append("frozen-11 row %s must have no focal" % f11)
    for f11 in [str(i) for i in range(1, 12) if str(i) not in NO_FOCAL_ROWS]:
        if sum(1 for r in back if r["frozen11_row"] == f11 and r["focal"] == "yes") != 1:
            errors.append("frozen-11 row %s must have exactly one focal" % f11)
    deg = [r for r in back if r["cell_id"].startswith("GIA-MDD-DEG-")]
    if len(deg) != 12 or any(r["cell_class"] != "descriptor" for r in deg):
        errors.append("GIA-MDD post-mortem-DEG descriptor cells: %d, register 2.3 says 12" % len(deg))
    pk6 = [r for r in back if r["cell_id"] == "PARK-C6"]
    if not pk6 or pk6[0]["n_cells"] != "13" or pk6[0]["cell_class"] != "family":
        errors.append("PARK-C6 must be one descriptor family of 13 (register 3.5)")
    byid = {r["cell_id"]: r for r in back}
    for cid in ("RG-V24", "RG-V25"):
        rr = byid.get(cid)
        if (not rr or rr["claim_form"] != "component" or rr["verdict_counted_in_m"] != "no"
                or not base_status(rr["status"]).startswith("not auditable (definition not applicable)")):
            errors.append("%s must be a not-auditable (definition not applicable) component claim outside m (register 2.4, v4)" % cid)
    for cid in ("RG-V26", "RG-N11", "RA-N1", "RA-N2", "RA-N4", "PARK-C3", "PARK-C4", "LEY-META"):
        rr = byid.get(cid)
        if not rr or not base_status(rr["status"]).startswith("not auditable"):
            errors.append("%s must be not auditable (register v4)" % cid)
    rr = byid.get("PRE-X1")
    if not rr or not base_status(rr["status"]).startswith("not testable as stated") or "also not auditable" not in rr["status"] \
            or not rr["T"].startswith("none"):
        errors.append("PRE-X1 must be not testable as stated and not auditable, no T (register 3.4, v4)")
    ran3 = [r for r in back if r["cell_id"].startswith("RA-N3-")]
    if len(ran3) != 10 or any(r["cell_class"] != "descriptor" or not base_status(r["status"]).startswith("conditional")
                              or not r["direction"].startswith("two-sided") for r in ran3):
        errors.append("RA-N3: need 10 conditional two-sided descriptor cells on y_S1 (register 2.6, v4)")
    for cid in ["PRE-D1r", "LIU-T2-STR", "LIU-T2-CBC", "LIU-T2-HIP"] + ["PRE-DG-%02d" % k for k in range(1, 7)]:
        rr = byid.get(cid)
        if not rr or rr["cell_class"] != "descriptor" or not rr["direction"].startswith("two-sided"):
            errors.append("%s must be a two-sided descriptor cell (register v5)" % cid)
    for cid in ("MOR-R1", "MOR-R2", "MOR-R3", "MOR-R4"):
        rr = byid.get(cid)
        if not rr or not rr["T"].startswith("none"):
            errors.append("%s: count claim, no registered T form (section 1.4, v4)" % cid)
    seg_desc = sum(1 for r in back if r["cell_id"].startswith("SEG-C3-D"))
    pre_go_desc = sum(1 for r in back if r["cell_id"].startswith("PRE-GO-") and r["cell_class"] == "descriptor")
    pre_b = sum(1 for r in back if r["cell_id"].startswith("PRE-B"))
    if (seg_desc, pre_go_desc, pre_b) != (71, 37, 14):
        errors.append("descriptor counts Segura GO %d (71), Pretzsch GO %d (37), FUMA %d (14)" % (seg_desc, pre_go_desc, pre_b))
    ley_meta = byid.get("LEY-META")
    if not ley_meta or ley_meta["cell_class"] != "family" or not ley_meta["n_cells"].startswith("UNDETERMINED"):
        errors.append("LEY-META must be one family row whose cell count is undetermined (register 3.8, v4)")
    rg03 = byid.get("RG-03")
    if not rg03 or rg03["n_cells"] != "11" or rg03["cell_class"] != "family":
        errors.append("RG-03 must be one family row with 11 cells")
    if m_total != M_TOTAL:
        errors.append("total m (lower bound) %d != %d" % (m_total, M_TOTAL))
    if m_upper != M_TOTAL_UPPER:
        errors.append("total m (upper bound) %d != %d" % (m_upper, M_TOTAL_UPPER))
    m_up_by = Counter(r["target_key"] for r in back if r["verdict_counted_in_m"] == normalize(M_UPPER))
    for key in TARGET_ORDER:
        have = sorted(r["cell_id"] for r in back if r["target_key"] == key and r["verdict_counted_in_m"] == normalize(M_UPPER))
        if have != sorted(EXPECTED_M_UPPER_ONLY.get(key, [])):
            errors.append("m's upper-bound-only rows for %s: %s, the register says %s" % (key, have, EXPECTED_M_UPPER_ONLY.get(key, [])))
    if m_upper > 250:
        errors.append("m's upper bound %d > 250: section 1.9's resolution check (1/10,001 < .05/m) no longer holds" % m_upper)

    # ------------------------------------------------------------------ v5 checks: register section 1.11 (the pre-freeze outcomes)
    v5 = []  # names of the v5 checks run (reported)
    # (1) every row carries its S-build disposition, equal to MANIFEST.json's
    v5.append("S-build disposition on every row (set id / size / sha256 / labels / status = MANIFEST.json)")
    for r in back:
        ents = CELL_SETS.get(r["cell_id"], [])
        if not ents:
            if not r["set_id"].startswith("none (S-build: ") or r["cell_id"] not in NO_SET:
                errors.append("%s: no S-build disposition" % r["cell_id"])
            continue
        if len(ents) == 1:
            if r["set_id"] != ents[0]["set_id"] or r["set_sha256"] != (ents[0].get("sha256") or r["set_sha256"]):
                errors.append("%s: set id / sha256 differ from MANIFEST.json" % r["cell_id"])
            if ents[0]["status"].startswith("built under gate") and not r["set_status"].startswith(ents[0]["status"]):
                errors.append("%s: a gated set must read '%s'" % (r["cell_id"], ents[0]["status"]))
        else:
            for i, e in enumerate(ents, start=1):
                if ("%d: %s" % (i, e["set_id"])) not in r["set_id"] or ("%d: %s" % (i, e["sha256"])) not in r["set_sha256"]:
                    errors.append("%s: family set %d differs from MANIFEST.json" % (r["cell_id"], i))
    if SUMMARY["stale_manifest_cells"]:
        errors.append("MANIFEST.json cells without a TSV row (re-point the S-build at this TSV: src_register/s_build.py): %s"
                      % SUMMARY["stale_manifest_cells"])
    if "PRE-DG" in byid:
        errors.append("v4's PRE-DG unit row must be replaced by PRE-DG-01 ... 06")
    # (2) S undefined -> not auditable (S undefined: <reason>), out of m; frozen-11 claims stay in the population as non-survivals
    v5.append("S undefined -> not auditable (%d rows), definition not applicable -> not auditable (%d, R3), S conditional (%d, R2) "
              "(section 1.11 item 2's lists)" % (len(S_UNDEF_EXPECTED), len(DNA_EXPECTED), len(R2_EXPECTED)))
    for cid in DNA_EXPECTED:
        rr = byid[cid]
        if not base_status(rr["status"]).startswith("not auditable (definition not applicable: ") or rr["verdict_counted_in_m"] != "no" \
                or not rr["set_status"].startswith("not auditable (definition not applicable)") \
                or not hl_final(rr).startswith(normalize(HL_IN_NA_DNA)):
            errors.append("%s: must read 'not auditable (definition not applicable: ...)', outside m, in the population (R3)" % cid)
    for cid in R2_EXPECTED:
        rr = byid[cid]
        if normalize(R2_FLAG) not in rr["status"] or not rr["set_status"].startswith("S conditional") \
                or rr["verdict_counted_in_m"] not in ("no", normalize(M_UPPER)):
            errors.append("%s: must carry the R2 flag and the conditional set status" % cid)
    r2_other = [r["cell_id"] for r in back if normalize(R2_FLAG) in r["status"] and r["cell_id"] not in R2_EXPECTED]
    if r2_other:
        errors.append("rows outside section 1.11's R2 list carry the R2 flag: %s" % r2_other)
    for cid in S_UNDEF_EXPECTED:
        rr = byid[cid]
        if not base_status(rr["status"]).startswith("not auditable (S undefined: ") or rr["verdict_counted_in_m"] != "no" \
                or not rr["set_status"].startswith("not auditable (S undefined)"):
            errors.append("%s: must read 'not auditable (S undefined: ...)', outside m" % cid)
        if rr["frozen11_row"] != "added" and rr["cell_class"] in ("claim", "family") and not hl_final(rr).startswith(
                normalize(HL_IN_NA_SU)):
            errors.append("%s: a not-auditable frozen-11 claim stays in the population as a non-survival (section 1.2)" % cid)
    su_other = [r["cell_id"] for r in back if "not auditable (S undefined: " in r["status"] and r["cell_id"] not in S_UNDEF_EXPECTED]
    if su_other:
        errors.append("rows outside section 1.11's list read S undefined: %s" % su_other)
    # (3) < 5 genes -> not testable (< 5), out of the headline population
    v5.append("SEG-C3b / d not testable (< 5), out of the population")
    for cid in LT5_EXPECTED:
        rr = byid[cid]
        if not base_status(rr["status"]).startswith("not testable (< 5): ") \
                or not rr["headline_population"].startswith(normalize(HL_OUT_LT5)) \
                or rr["verdict_counted_in_m"] != "no":
            errors.append("%s: must be not testable (< 5), out of the population (section 1.2)" % cid)
    # (4) Segura Table S7: 71 descriptor rows, GO id and name from SEGURA_S7_TERMS.json, cell index 1 ... 71
    v5.append("SEG-C3-D01 ... D71 = SEGURA_S7_TERMS.json (GO id, set id, cell index)")
    for k, t in enumerate(S7_OTHER, start=1):
        rr = byid.get(t["cell_id"])
        if (not rr or rr["cell_class"] != "descriptor" or t["go_id"] not in rr["set_S"] or rr["set_id"] != t["set_id"]
                or rr["cell_index"] != str(k)):
            errors.append("%s: Table S7 descriptor row differs from SEGURA_S7_TERMS.json" % t["cell_id"])
    # (5) PRE-DG: six rows from PRE_DG_ROWS.json, gate G2, their feature's map, cell index 1 ... 6
    v5.append("PRE-DG-01 ... 06 = PRE_DG_ROWS.json (map, set, two-sided, G2, cell index)")
    for k, prow in enumerate(PREDG["rows"], start=1):
        rr = byid.get(prow["proposed_cell_id"])
        if (not rr or rr["gate"] != "G2" or rr["set_id"] != prow["set_id"] or rr["cell_index"] != str(k)
                or not rr["map"].startswith("y_%s" % prow["feature"]) or rr["verdict_counted_in_m"] != "no"):
            errors.append("%s: differs from PRE_DG_ROWS.json" % prow["proposed_cell_id"])
    # (6) Buch Fig. 5h: printed values, the asterisk label
    v5.append("Buch Fig. 5h = buch_fig5h_grid.json (20 printed values; '*Ribosomal structure' reaches no PANTHER term: R2)")
    for tsv_cell, c in GRID5H.items():
        rr = byid.get(tsv_cell)
        if not rr or ("Fig. 5h printed value %s " % c["printed"]) not in rr["published_value_and_location"] \
                or rr["cell_class"] != ("claim" if c["marked"] else "descriptor"):
            errors.append("%s: Fig. 5h value / class differ from the re-read grid" % tsv_cell)
        if "StructConstRibosome" in tsv_cell and ("Fig. 5h label '*Ribosomal structure' (as printed)" not in rr["set_S"]
                                                  or "not auditable (S undefined: source 1 uncorroborated" not in rr["set_S"]
                                                  or NAMES.get(tsv_cell, {}).get("tier", "x") is not None):
            errors.append("%s: the asterisked row must read 'not auditable (S undefined: source 1 uncorroborated)' (no PANTHER "
                          "term by the name rule, no printed size; v6.5)" % tsv_cell)
    if any(" value ns " in r["published_value_and_location"] for r in back if r["cell_id"].startswith("BUCH-E-Trans-")):
        errors.append("Fig. 5h cells must carry their printed values, not 'ns'")
    # (7) Moreau: MIST64 counts and the matrix identity in the fields and notes
    v5.append("Moreau MIST64 counts (46: 33 / 5 / 8) and sha256_matrix in route and notes")
    for r in back:
        if r["target_key"] == "moreau2020mutations":
            if (MISTM["sha256_matrix"] not in r["route"] or MISTM["sha256_matrix"] not in r["notes"] or "UNDETERMINED" in r["route"]
                    or "primary 46 parcels (cortex 33, subcortex 5, cerebellum 8)" not in r["route"]):
                errors.append("%s: MIST64 counts / matrix identity missing" % r["cell_id"])
    # (8) carrier tests (section 1.11 item 8) on every conditional row
    v5.append("carrier tests pinned on every conditional row (spec sha256, 152 left / >= 230 usable / 400 by name, or by index only "
              "where the carrier names the 17-network order file: R9)")
    need = {"romerogarcia2019synaptic": "152 LEFT DK-308 labels", "buch2023asdsubgroups": ">= 230 usable ROIs",
            "mamat2025molecular": "OR by index 1 ... 400 ONLY IF the carrier itself names the 17-network order file",
            "rasero2023neurogenetics": "dk34 = the 34 left cortical"}
    for r in back:
        if r["target_key"] in need and ("conditional" in r["status"] or "carrier test in notes" in r["status"]):
            if CARRIER_SHA not in r["notes"] or normalize(need[r["target_key"]]) not in r["notes"]:
                errors.append("%s: carrier test not pinned in notes" % r["cell_id"])
        if "not enumerated by the register or the draft" in r["notes"]:
            errors.append("%s: a carrier label list still undetermined" % r["cell_id"])
    # (9) pSI.data 1.0 pinned on every CSEA / SEA row; no '1.1'
    v5.append("pSI.data 1.0 (URL + sha256) on every CSEA / SEA row")
    for r in back:
        if "pSI" in r["set_S"] and (PSI_JSON["files"][0]["sha256"] not in r["set_S"] or "pSI.data 1.0" not in r["set_S"]):
            errors.append("%s: pSI.data 1.0 not pinned" % r["cell_id"])
        if "pSI.data 1.1" in "\t".join(r.values()) or "an obtainable copy" in r["set_S"]:
            errors.append("%s: stale pSI.data text" % r["cell_id"])
    # (10) identity of gated maps (section 1.11 item 6)
    v5.append("gated-map identity (URL, bytes, ETag / blob id) on every gated row with a registered map")
    id_targets = {"romerogarcia2019synaptic", "rasero2023neurogenetics", "buch2023asdsubgroups", "mamat2025molecular",
                  "benkarim2021connectivity", "park2021subcortico", "dear2024corticalgene", "pagani2026crossspecies",
                  "leyhausen2024intrinsic", "giacomel2026cartography", "hansen2022local", "patel2021virtual", "pretzsch2024patterns"}
    no_map = {"RG-V23", "RG-V24", "RG-V25", "RG-V26", "RG-N11", "RA-N1", "RA-N2", "RA-N4", "PRE-X1", "LEY-META"}
    for r in back:
        want = (r["target_key"] in id_targets or r["cell_id"] == "LIU-T3") and r["cell_id"] not in no_map
        if want and "identity before the freeze" not in r["map"]:
            errors.append("%s: gated map without its pre-freeze identity" % r["cell_id"])
    # (11) seeds' cell index (section 1.9, v5)
    v5.append("cell index (section 1.9): 0 single, 1 ... n unit / family, n/a iff no T")
    for r in back:
        ci = r["cell_index"]
        if (ci == MAPIDX_NA) != r["T"].startswith("none"):
            errors.append("%s: cell_index n/a iff no registered T" % r["cell_id"])
        if r["cell_class"] == "family" and ci == "0":
            errors.append("%s: a family row needs cell indices 1 ... n" % r["cell_id"])
        if not (ci == "0" or ci.isdigit() or ci == MAPIDX_NA or ci.startswith("1 ... ") or ci.startswith("UNDETERMINED")):
            errors.append("%s: cell_index %s" % (r["cell_id"], ci[:30]))
    for pref, n in (("SEG-C3-D", 71), ("PRE-DG-", 6), ("RA-N3-", 10)):
        got = [r["cell_index"] for r in back if r["cell_id"].startswith(pref)]
        if got != [str(k) for k in range(1, n + 1)]:
            errors.append("%s cells: cell indices must be 1 ... %d in the defining table's order" % (pref, n))
    if not byid["PARK-C6"]["cell_index"].startswith("1 ... 13, "):
        errors.append("PARK-C6: cell indices 1 ... 13")
    # (12) the LIU-T3 labels follow the S-build's m (register 1.1: 100 < m <= 1,000 -> the labels written in the note)
    liu_m = sset("liu_merged_asd")["universe"]["V-DK"]["n_columns"]  # v6 R5: columns
    if not 100 < liu_m <= 1000:
        errors.append("LIU-T3: the note's labels assume 100 < m <= 1,000; the S-build gives %d" % liu_m)
    v5.append("LIU-T3 reading labels vs the S-build's m (%d)" % liu_m)
    # (13) the carrier self-test record matches the spec and the engine (checked at load) and caught every plant
    v5.append("carrier self-test %d / %d, record = current spec and engine" % (CARRIER_SELF["n_caught"], CARRIER_SELF["n_cases"]))
    # (14) the S-build manifest points at this TSV: its row count, the sha256 of the columns it reads, every row reference
    v5.append("S-build manifest points at this TSV (rows, columns_read_sha256, every per-set and manifest row reference)")
    mt = MANIFEST["tsv"]
    view = hashlib.sha256("\n".join("\t".join(r[c] for c in mt.get("columns_read", [])) for r in back)
                          .encode("utf-8")).hexdigest()
    if mt.get("rows") != len(back) or mt.get("columns_read_sha256") != view:
        errors.append("MANIFEST.json's tsv block does not describe this TSV (rows %s / %d; columns_read_sha256 %s / %s): re-run "
                      "src_register/s_build.py" % (mt.get("rows"), len(back), mt.get("columns_read_sha256"), view))
    bad_refs = [cd["cell"] for sj in SET_JSON.values() for cd in sj.get("cells_detail", [])
                if cd["cell"].split(" (")[0] not in byid or str(cd["row"]) != byid[cd["cell"].split(" (")[0]]["row"]]
    bad_refs += [c for c, v in NO_SET.items() if c not in byid or str(v["row"]) != byid[c]["row"]]
    if bad_refs:
        errors.append("S-build row references that do not match this TSV: %d (%s)" % (len(bad_refs), ", ".join(bad_refs[:10])))
    # (15) the register's section 7 records this TSV's sha256 (the TSV header records the register's hash with that field masked)
    v5.append("register section 7's 'TSV sha256' = this TSV's sha256 (header: register hash with that field masked)")
    tsv_sha_now = sha256_file(OUT)
    if REG_TSV_SHA_FIELD != tsv_sha_now:
        errors.append("register section 7 records TSV sha256 %s, this build wrote %s: write it into section 7 and rebuild (the TSV "
                      "does not change: its header records the register's hash with that field masked)"
                      % ("placeholder (64 zeros)" if REG_TSV_SHA_FIELD == "0" * 64 else REG_TSV_SHA_FIELD, tsv_sha_now))

    # the interim population and the deferred population per gate (section 1.2)
    interim = [r for r in back if r["frozen11_row"] != "added" and r["headline_population"].startswith("in")]
    if sorted(r["cell_id"] for r in interim) != sorted(EXPECTED_INTERIM):
        errors.append("interim population %s differs from the register's lists %s"
                      % (sorted(r["cell_id"] for r in interim), sorted(EXPECTED_INTERIM)))
    deferred_pop = {g: [r for r in back if r["frozen11_row"] != "added" and r["headline_population"].startswith(
        normalize(DEFER_HL % g)) and hl_final(r).startswith("in")] for g in ("G1", "G2")}
    for g, want in EXPECTED_DEFERRED_POP.items():
        if len(deferred_pop[g]) != want:
            errors.append("population units deferred behind %s: %d, the register's lists give %d" % (g, len(deferred_pop[g]), want))
    final = interim + deferred_pop["G1"] + deferred_pop["G2"]
    for r in final:
        in_m = r["verdict_counted_in_m"] in ("yes", normalize(M_UPPER))
        if in_m and pop_category(r) not in ("component-level",) and not pop_category(r).startswith("tested"):
            errors.append("%s: in m but counted as %s" % (r["cell_id"], pop_category(r)))
        if not in_m and (pop_category(r) == "component-level" or pop_category(r).startswith("tested")):
            errors.append("%s: tested / component-level but outside m" % r["cell_id"])

    # ------------------------------------------------------------------ v6 checks
    # (16) R1: every mapped row carries its name-rule tier; the S-build's records cover exactly the mapped rows
    v5.append("name rule (R1): every mapped row carries its tier (NAME_MATCHES.json %d cells: %s)"
              % (len(NAMES), ", ".join("%s %d" % (k, v) for k, v in sorted(Counter(str(e["tier"]) for e in NAMES.values()).items()))))
    for r in back:
        e = NAMES.get(r["cell_id"])
        has = "name rule (" in r["set_rule_labels"] or "name rule: S undefined" in r["set_rule_labels"]
        if (e is not None) != has:
            errors.append("%s: name-rule label %s" % (r["cell_id"], "missing" if e else "without a record"))
        if e is not None and e["tier"] is not None and ("name rule (%s): " % e["tier"]) not in r["set_rule_labels"]:
            errors.append("%s: name-rule tier differs from NAME_MATCHES.json" % r["cell_id"])
    # (17) R5: every built set's size is given in columns of the row's class universe
    v5.append("set sizes in columns of the class universe (R5)")
    for r in back:
        sz = r["set_size_in_class_universe"]
        if r["set_status"].startswith(("built;", "built (")) and not re.match(r"^(\d+: )?[\d,]+ columns ", sz):
            errors.append("%s: set size not in columns (R5)" % r["cell_id"])
    if not UNIVERSE_TXT.startswith("register v6 R5"):
        errors.append("MANIFEST.json's universe convention is not the v6 R5 text")
    # (18) R4: the register's section 4 numbers and section 1.11 id lists equal the values derived from this TSV
    derived_nums = register_numbers(back, interim, final, deferred_pop, m_total, m_upper, m_by, m_up_by)
    derived_ids = register_id_lists(back)
    reg_nums, reg_ids, parse_err = parse_register_blocks()
    errors.extend(parse_err)
    for k in sorted(set(derived_nums) | set(reg_nums)):
        if derived_nums.get(k) != reg_nums.get(k):
            errors.append("register section 4 (R4): '%s' = %s in claims_register.md, the TSV gives %s"
                          % (k, reg_nums.get(k, "(absent)"), derived_nums.get(k, "(absent)")))
    for k in sorted(set(derived_ids) | set(reg_ids)):
        a, b = derived_ids.get(k), reg_ids.get(k)
        if a is None or b is None or sorted(a) != sorted(b[1]) or b[0] != len(b[1]):
            errors.append("register section 1.11 (R4): id list '%s' in claims_register.md %s, the TSV gives %s"
                          % (k, ("[%d] %s" % (b[0], b[1][:6])) if b else "(absent)", ("[%d] %s" % (len(a), a[:6])) if a is not None else "(absent)"))
    v5.append("register section 4 numbers (%d) and section 1.11 id lists (%d) parsed from claims_register.md = the TSV (R4)"
              % (len(reg_nums), len(reg_ids)))
    # (19) v6.2 P2: every Buch, Pagani, R2 and Romero-Garcia family row has a source-1 entry keyed by its cell id, and no other row
    s1c = CARRIER.get("source1_lists", {}).get("cells") or {}
    want = sorted({r["cell_id"] for r in back if r["cell_id"].startswith("BUCH-E-") or r["cell_id"].startswith("PAG-C")}
                  | set(R2_EXPECTED) | {"RG-N03", "RG-15", "RG-V23"})  # v6.5: the three RG cells left R2 (uncorroborated)
    if sorted(s1c) != want:
        errors.append("carrier_tests.json source1_lists.cells: %d entries, the Buch / Pagani / R2 / RG-family rows are %d (differ: %s)"
                      % (len(s1c), len(want), sorted(set(s1c) ^ set(want))[:10]))
    labels_fgh = {("Syn-" + t): lab for t, lab, _ in SYN}
    labels_fgh.update({("Imm-" + t): lab for t, lab, _ in IMM})
    labels_fgh.update({("Trans-" + t): lab.lstrip("*").strip() for (t, _), lab in zip(TRANS, BUCH5H["rows_top_to_bottom_as_printed"])})
    for cid, e in s1c.items():
        m_ = re.match(r"^BUCH-E-(.+)-S[1-4]$", cid)
        if m_ and m_.group(1) in labels_fgh and e.get("names") != [[labels_fgh[m_.group(1)]]]:
            errors.append("%s: source-1 names differ from the printed Fig. 5f-h label" % cid)
        if cid.startswith(("BUCH-E-", "PAG-C")) and not e.get("names"):
            errors.append("%s: no source-1 name alternatives" % cid)
    for cid in ("RG-04", "RG-V08", "RG-V09", "RG-N04", "RG-N05", "RG-N06", "RG-N07"):
        if (s1c.get(cid) or {}).get("printed_size") != 500:
            errors.append("%s: the printed size 500 is not pinned in source1_lists.cells" % cid)
    for cid in ("RG-15", "RG-V23"):
        if any("validation" in ph for alt in ((s1c.get(cid) or {}).get("names") or []) for ph in alt):
            errors.append("%s: a name alternative with 'validation' (dropped by v6.2 P7 (b))" % cid)
    # v6.3 O6: Buch's rival names = the PANTHER GO-slim names its labels reach (NAME_MATCHES.json) + 'structural constituent of ribosome'
    riv = sorted(a[0] for a in (CARRIER.get("source1_lists", {}).get("rival_names") or {}).get("buch2023asdsubgroups", []))
    want_riv = sorted({e["name"] for c, e in NAMES.items() if c.startswith("BUCH-E-") and e.get("tier")
                       and e.get("release", "").startswith("PANTHER")}  # v6.6: the Fig. 5c-e comparators' terms are not rivals
                      | {"structural constituent of ribosome"})
    if riv != want_riv:
        errors.append("carrier_tests.json source1_lists.rival_names (Buch): %d names, NAME_MATCHES.json's PANTHER names + 'structural "
                      "constituent of ribosome' are %d (differ: %s)" % (len(riv), len(want_riv), sorted(set(riv) ^ set(want_riv))[:6]))
    zhang = ["RG-04", "RG-V08", "RG-V09", "RG-N04", "RG-N05", "RG-N06", "RG-N07"]
    fams = CARRIER.get("source1_lists", {}).get("families") or {}
    if sorted((fams.get("zhang2014_top500") or {}).get("cells", [])) != sorted(zhang) or \
            (fams.get("zhang2014_top500") or {}).get("caption_phrases") != ["zhang", "top 500"]:
        errors.append("carrier_tests.json source1_lists.families: the Zhang family (7 cells; caption phrases 'zhang', 'top 500') "
                      "is not as v6.4 N2 pins it")
    for cid in zhang:
        e = s1c.get(cid) or {}
        if e.get("family") != "zhang2014_top500" or not any(len(a) == 2 and a[1] == "enriched" for a in (e.get("names") or [])):
            errors.append("%s: not in the Zhang family or without its 'enriched' alternative (v6.4 N2 / N3)" % cid)
    if sorted(c for c, e in s1c.items() if e.get("family")) != sorted(zhang):
        errors.append("source1_lists.cells: a family flag outside the Zhang cells (v6.4 N2)")
    if sorted(c for c, e in s1c.items() if e.get("own_title_only")) != ["RG-15", "RG-V23"]:
        errors.append("source1_lists.cells: own_title_only must be exactly RG-15 and RG-V23 (v6.4 N2)")
    # v6.5 (1): the corroboration modes -- external = the cell's pinned register_sets set; none = exactly the cells the S-build
    # records as S undefined for want of corroboration; printed_size = the Zhang cells; classes = the rows' analysis classes
    modes = Counter()
    for cid, e in s1c.items():
        cor = e.get("corroboration") or {}
        modes[cor.get("mode")] += 1
        row_ = byid.get(cid)
        if cor.get("class") and row_ is not None and normalize(row_["analysis_class"]).split(" ")[0] != cor["class"]:
            errors.append("%s: corroboration class %s differs from the row's analysis class" % (cid, cor["class"]))
        if cor.get("mode") == "external" and cor.get("set_id") not in [x["set_id"] for x in CELL_SETS.get(cid, [])]:
            errors.append("%s: corroboration set %s is not the S-build's set for the cell" % (cid, cor.get("set_id")))
        if cor.get("mode") == "printed_size" and (cid not in zhang or cor.get("printed_size") != 500):
            errors.append("%s: printed-size corroboration outside the Zhang cells (500)" % cid)
    none_cells = sorted(c for c, e in s1c.items() if (e.get("corroboration") or {}).get("mode") == "none")
    if none_cells != sorted(MODE_NONE_EXPECTED) or any(c not in SUMMARY["s_undefined"] for c in none_cells):
        errors.append("corroboration mode 'none' (%d) differs from the S-undefined rows without a comparator (%d)"
                      % (len(none_cells), len(MODE_NONE_EXPECTED)))
    if any(x is None for x in modes):
        errors.append("source1_lists.cells: an entry without a corroboration mode (v6.5)")
    # v6.6 B1: every external comparator pinned to the committed per-set JSON (file and members sha256); the RG KEGG families by
    # the recipe over the pinned Enrichr libraries; no gate-time file mode left
    n_pin = 0
    for cid, e in s1c.items():
        cor = e.get("corroboration") or {}
        if cor.get("mode") == "external_under_gate":
            errors.append("%s: mode external_under_gate (withdrawn by v6.6 B1)" % cid)
        if cor.get("mode") == "external":
            f_ = SETS_DIR / (cor["set_id"] + ".json")
            body = load_json(f_) if f_.exists() else None
            if body is None or sha256_file(f_) != cor.get("json_sha256") or hashlib.sha256(
                    "\n".join(body["members_hgnc"]).encode("utf-8")).hexdigest() != cor.get("members_sha256"):
                errors.append("%s: the comparator pins differ from the committed %s" % (cid, f_.name))
            else:
                n_pin += 1
        if cor.get("mode") == "kegg_family_recipe":
            libs = (cor.get("recipe") or {}).get("libraries") or {}
            for lib, want_sha in (("KEGG_2015", KEGG_LIB_SHA["KEGG_2015"]), ("KEGG_2016", KEGG_LIB_SHA["KEGG_2016"])):
                if (libs.get(lib) or {}).get("sha256") != want_sha:
                    errors.append("%s: the recipe's %s pin differs from the library file" % (cid, lib))
    if sorted(c for c, e in s1c.items() if (e.get("corroboration") or {}).get("mode") == "kegg_family_recipe") != \
            ["RG-03", "RG-V06", "RG-V07"]:
        errors.append("the KEGG family recipe must pin exactly RG-03, RG-V06, RG-V07 (v6.6 B1)")
    for cid in zhang:
        src_ = ((s1c.get(cid) or {}).get("corroboration") or {}).get("printed_size_source") or {}
        if "the top 500 genes with higher expression" not in src_.get("sentence", "") or \
                (src_.get("pdf") or {}).get("sha256") != "130a9b6ca2171563292f27dd79462ceb103c8ce56315f71efa6171d915696621":
            errors.append("%s: the printed size's verbatim sentence / PDF pin is missing (v6.6 C1)" % cid)
    # v6.7 (1): the near-miss view -- the builder's table = the S-build's view = carrier_tests.json's view pins; no primary field
    # depends on it; m' as registered
    nm_view = (MANIFEST.get("comparators_v6_6") or {}).get("near_miss_view_v6_7") or {}
    got_v = {c: (e["set_id"] if e["outcome"] == "built" else None) for e in nm_view.get("sets", []) for c in e["cells"]}
    want_v = {c: NM67[t][0] for c, t in NM_CELLS.items()}
    if got_v != want_v:
        errors.append("NM67 table differs from MANIFEST.json's near-miss view: %s"
                      % sorted(c for c in set(got_v) | set(want_v) if got_v.get(c, "?") != want_v.get(c, "?"))[:10])
    for e in nm_view.get("sets", []):
        for c in e["cells"]:
            v_ = ((s1c.get(c) or {}).get("corroboration_views") or {}).get("near_miss") or {}
            if e["outcome"] == "built" and (v_.get("mode") != "external" or v_.get("set_id") != e["set_id"]
                                            or v_.get("json_sha256") != e.get("json_sha256")
                                            or v_.get("members_sha256") != e.get("members_sha256") or v_.get("label") != NM_LABEL):
                errors.append("%s: carrier_tests.json's near-miss view pin differs from the S-build's" % c)
            if e["outcome"] != "built" and v_.get("mode") != "none":
                errors.append("%s: a not-buildable near-miss comparator must pin mode none" % c)
            if (s1c.get(c) or {}).get("corroboration", {}).get("mode") != "none":
                errors.append("%s: in the near-miss view, but its primary comparator is not 'none'" % c)
            if SET_JSON.get(e.get("set_id") or "", {}).get("cells"):
                errors.append("%s: a near-miss set with primary cells" % e["set_id"])
    extra_views = sorted(c for c, e_ in s1c.items() if e_.get("corroboration_views") and c not in got_v)
    if extra_views:
        errors.append("near-miss view pins on cells outside the view: %s" % extra_views)
    for r in back:
        if (r["cell_id"] in got_v) != (r["secondary_view_near_miss_set_id"] != "n/a"):
            errors.append("%s: the near-miss columns differ from the view" % r["cell_id"])
    m_sec = m_total + sum(1 for r in back if "counted in m' (the view's m): yes" in r["secondary_view_near_miss_status"])
    if m_sec != M_SECONDARY_NEAR_MISS:
        errors.append("m' (the near-miss view) %d != %d" % (m_sec, M_SECONDARY_NEAR_MISS))
    cc_ = CARRIER.get("source1_lists", {}).get("corroboration") or {}
    if cc_.get("universe_genes_sha256") != sha256_file(SETS_DIR / "UNIVERSE_GENES.json") or \
            (cc_.get("hgnc_table") or {}).get("sha256") != MANIFEST["hgnc"]["sha256"]:
        errors.append("carrier_tests.json's universe / HGNC pins (v6.7 N3) differ from UNIVERSE_GENES.json / the S-build's HGNC")
    v5.append("v6.7: the near-miss view (%d cells; %d sets built, %d not buildable) = MANIFEST.json = carrier_tests.json's view "
              "pins; no primary field depends on it; m' %d; the universe / HGNC pins (N3) = the files"
              % (len(got_v), nm_view.get("n_built", 0), nm_view.get("n_not_buildable", 0), m_sec))
    # v6.6 B2: the builder's comparator tables equal the S-build's outcomes; the rule text unchanged since it was written
    cmp_ = MANIFEST.get("comparators_v6_6") or {}
    got = {}
    for e in cmp_.get("sets", []):
        for c in e["cells"]:
            got[c] = e["set_id"] if e["outcome"] == "built" else None
    want_c = {"BUCH-E-%s-S%d" % (t, k): v[0] for t, v in COMP66_BUCH.items() for k in range(1, 5)}
    want_c.update({c: v[0] for c, v in COMP66_PAGANI.items()})
    if got != want_c:
        errors.append("COMP66 tables differ from register_sets/MANIFEST.json comparators_v6_6: %s"
                      % sorted(c for c in set(got) | set(want_c) if got.get(c, "?") != want_c.get(c, "?"))[:10])
    reg_txt = REGISTER.read_bytes().decode("utf-8")
    a_ = reg_txt.find("- **Comparators built before the freeze")
    b_ = reg_txt.find("\n- **", a_ + 1)
    rule_sha = hashlib.sha256(reg_txt[a_:b_ + 1].encode("utf-8")).hexdigest() if a_ >= 0 and b_ > a_ else None
    if rule_sha != RULE66_SHA or (cmp_.get("rule") or {}).get("text_sha256") != RULE66_SHA:
        errors.append("register 1.6's v6.6 resolution rule text is not the text written before the downloads (sha256 %s)" % rule_sha)
    v5.append("v6.6: %d external comparators pinned = the committed files; KEGG recipe on RG-03 / RG-V06 / RG-V07 with the "
              "library pins; Zhang printed size pinned to its sentence; comparator tables = the S-build (%d sets: %d built, %d not "
              "buildable); the resolution rule's text sha256 = %s..." % (n_pin, cmp_.get("n_sets", 0), cmp_.get("n_built", 0),
                                                                        cmp_.get("n_not_buildable", 0), RULE66_SHA[:12]))
    v5.append("source-1 entries keyed by cell id (P2): %d = the Buch, Pagani, R2 and Romero-Garcia family rows; Buch Fig. 5f-h labels "
              "as printed; Zhang printed size 500; Buch rival names (O6) %d = NAME_MATCHES.json's PANTHER names + 'structural "
              "constituent of ribosome'; the Zhang family (7 cells, caption phrases 'zhang' / 'top 500', an 'enriched' "
              "alternative each) and RG-15 / RG-V23 own-title-only (v6.4 N2 / N3); corroboration modes (v6.5): %s" %
              (len(s1c), len(riv), ", ".join("%s %d" % kv for kv in sorted(modes.items()))))

    # ------------------------------------------------------------------ report (counts and hashes only)
    print("inputs: register sha256 %s (section 7's TSV field masked: %s; last commit touching it %s, working copy equals it: %s, "
          ">= %s %s); drafts verified %d/20; Vairam note %s"
          % (reg_sha, reg_sha_masked, reg_commit, reg_clean, REGISTER_MIN_COMMIT, anc_ok, len(draft_sha), vairam_sha))
    print("pre-freeze inputs: MANIFEST.json %d set entries (%d per-set JSONs verified); S-build dispositions: %s"
          % (len(MANIFEST["sets"]), len(SET_JSON), ", ".join("%s %d" % kv for kv in sorted(Counter(
              ("family of %d sets: " % (r["set_id"].count(" | ") + 1) if " | " in r["set_id"] else "")
              + re.sub(r"^\d+: ", "", r["set_status"]).split(";")[0].split(":")[0].split(" (")[0] for r in back).items()))))
    print("rows %d; m lower bound %d, upper bound %d (v6.10 207 / 207); m' (the near-miss view, a secondary view: %s) %d"
          % (len(back), m_total, m_upper, NM_LABEL, m_total + sum(1 for r in back if "counted in m' (the view's m): yes"
                                                                    in r["secondary_view_near_miss_status"])))
    classes = sorted(CELL_CLASSES)
    print("rows by target and cell_class (%s):" % ", ".join(classes))
    for no, key in keys.items():
        c = Counter(r["cell_class"] for r in back if r["target_key"] == key)
        print("  %2d %-28s total %3d  %s  m %d" % (no, key, sum(c.values()), " ".join("%s=%d" % (k, c[k]) for k in classes if c[k]),
                                                  m_by.get(key, 0)))
    print("m changes v6.10 -> v6.11 (lower bound; upper-bound-only rows in brackets): " + ", ".join(
        "%s %d -> %d [+%d]" % (k, v, m_by.get(k, 0), m_up_by.get(k, 0)) for k, v in M_BEFORE.items()))
    print("S undefined -> not auditable: %d rows (%s); definition not applicable: %s; S conditional (R2): %s; not testable (< 5): %s"
          % (len(SUMMARY["s_undefined"]), ", ".join(sorted(SUMMARY["s_undefined"])), ", ".join(SUMMARY["dna"]),
             ", ".join(SUMMARY["r2"]), ", ".join(SUMMARY["lt5"])))

    def comp(rs, view="upper"):
        return ", ".join("%s %d" % (k, v) for k, v in sorted(Counter(pop_category(r, view) for r in rs).items()))

    def both(rs):
        return sum(1 for r in rs if base_status(r["status"]).startswith("not auditable") and "not testable as stated" in r["status"])
    print("interim population (every gate closed; families count once): %d units -- %s; by target: %s"
          % (len(interim), comp(interim), ", ".join("%s %d" % (k, v) for k, v in Counter(r["target_key"] for r in interim).items())))
    for g in ("G1", "G2"):
        rows_g = [r for r in back if r["status"].startswith(normalize(GATE_STATUS[g]) + "; ")]
        f11 = [r for r in rows_g if r["frozen11_row"] != "added"]
        print("deferred (gate %s closed): %d rows (%d frozen-11, %d added); population units on opening %d -- %s; by target: %s"
              % (g, len(rows_g), len(f11), len(rows_g) - len(f11), len(deferred_pop[g]), comp(deferred_pop[g]),
                 ", ".join("%s %d" % (k, v) for k, v in Counter(r["target_key"] for r in deferred_pop[g]).items())))
    dear = [r for r in back if r["gate"] == "G1+G2"]
    vr = [r for r in back if r["target_key"] == "vairam2026hyperhypo"]
    print("deferred pending provenance (Dear, G1+G2 once established): %d rows, %d in m; deferred (prereg section 5.1; Vairam / "
          "Roy): %d rows, %d claims listed apart, 0 in m"
          % (len(dear), sum(1 for r in dear if r["verdict_counted_in_m"] == "yes"), len(vr), sum(1 for r in vr if r["cell_class"] == "claim")))
    print("population once every gate has opened (Vairam / Roy excluded; at most, R10): %d units -- %s [provisional: %d rows with "
          "S conditional (R2)]; lower view (no R2 carrier qualifies): %s; with a verdict (in m) %d lower / %d upper; not auditable and "
          "also not testable as stated %d; by target: %s"
          % (len(final), comp(final), sum(1 for r in final if normalize(R2_FLAG) in r["status"]), comp(final, "lower"),
             sum(1 for r in final if r["verdict_counted_in_m"] == "yes"),
             sum(1 for r in final if r["verdict_counted_in_m"] in ("yes", normalize(M_UPPER))), both(final),
             ", ".join("%s %d" % (k, v) for k, v in Counter(r["target_key"] for r in final).items())))
    ct = Counter(("component-level in form" if r["claim_form"] == "component" else "other form",
                  "not auditable" if "not auditable" in row_flags(r) else "auditable") for r in final)
    print("cross-tab (R8), population once every gate has opened: " + "; ".join("%s x %s %d" % (a, b, n) for (a, b), n in sorted(ct.items())))
    print("focal (frozen 11): " + "; ".join("row %s %s: %s" % (r["frozen11_row"], r["cell_id"], r["status"][:120])
                                             for r in back if r["focal"] == "yes"))
    und = Counter()
    for r in back:
        for c in COLS:
            if "UNDETERMINED" in r[c]:
                und[c] += 1
    print("fields containing UNDETERMINED, by column: " + ", ".join("%s %d" % (k, v) for k, v in sorted(und.items())))
    tsv_sha = sha256_file(OUT)
    print("output: %s sha256 %s" % (OUT.relative_to(ROOT).as_posix(), tsv_sha))
    print("script: %s sha256 %s" % (HERE.relative_to(ROOT).as_posix(), script_sha))
    if errors:
        print("CHECKS FAILED (%d):" % len(errors))
        for e in errors:
            print("  - " + e)
        sys.exit(2)
    print("CHECKS PASSED: header, row numbers, ids unique, target order, gates and deferral flags (section 0), headline forms and "
          "exclusions (section 1.2), per-target m and m ids (section 4 as the v6.11 rules give it; R2's upper-bound rows), Buch families "
          "(2.7: 102 enrichment claims, 80 in m (v6.5: '*Ribosomal structure' S1 not auditable; v6.6: 21 without a buildable "
          "comparator; v6.7: 17, asdM12 built; v6.8: 21, asdM12 in the near-miss view; v6.9: 21, RDNV's descriptor cells to the view), synaptic 32; Syn-GPCR-S2 a descriptor), Giacomel 12 "
          "published-null (6 resolution-limited), register-named ids present, focal claims (section 4), descriptor counts (Segura 71, "
          "Pretzsch 37 + 14), GIA-MDD DEG 12, RA-N3 10, PRE-D1r / PRE-DG-01 ... 06, Liu SD4 3, LEY-META undetermined, RG-03 11, PARK-C6 "
          "13, RG-V24 / V25 not auditable outside m, MOR-R no T, not-auditable cells, map indices (section 1.9; RG-V23 0 = Val1, "
          "1 = Val2), interim population %d, deferred units G1 %d / G2 %d, m lower %d / upper %d"
          % (len(EXPECTED_INTERIM), EXPECTED_DEFERRED_POP["G1"], EXPECTED_DEFERRED_POP["G2"], M_TOTAL, M_TOTAL_UPPER))
    print("V5 ... V6.8 CHECKS PASSED (%d): %s" % (len(v5), "; ".join(v5)))
    write_freeze_manifest(tsv_sha, len(back), m_total, len(interim), len(final), (reg_sha, reg_sha_masked), m_upper,
                          Counter(pop_category(r) for r in final), Counter(pop_category(r, "lower") for r in final))


def write_freeze_manifest(tsv_sha, n_rows, m_total, n_interim, n_final, reg, m_upper, comp_upper, comp_lower):
    """register section 1.11 (v6.5): the files frozen with the register, by sha256 (deterministic: sorted, no timestamps)."""
    paths = ([OUT, HERE, SETS_DIR / "MANIFEST.json", SETS_DIR / "SEGURA_S7_TERMS.json", SETS_DIR / "PRE_DG_ROWS.json",
              SETS_DIR / "NAME_MATCHES.json", SETS_DIR / "UNIVERSE_GENES.json"] + sorted(MAPS_DIR.glob("*.json"))
             + sorted(SRC_REG.glob("*.py")))
    files = [{"path": q.relative_to(ROOT).as_posix(), "bytes": q.stat().st_size, "sha256": sha256_file(q)} for q in paths]
    if files[0]["sha256"] != tsv_sha:
        die("the TSV changed while the freeze manifest was written")
    if sha256_file(REGISTER) != reg[0]:
        die("the register changed during the build")
    man = OrderedDict([
        ("what", "A1 claims register (DRAFT v6.11) freeze manifest: the sha256 of every file frozen with claims_register.md -- the TSV, "
                 "its builder, the pre-freeze S-build manifest and its four tables (SEGURA_S7_TERMS, PRE_DG_ROWS, NAME_MATCHES, UNIVERSE_GENES), every "
                 "register_maps/*.json and every src_register/*.py (register section 1.11). Written by the builder after all its "
                 "checks passed; deterministic; repo-relative paths."),
        ("register", OrderedDict([("path", "arcs/audit/claims_register.md"), ("sha256_at_build", reg[0]),
                                  ("sha256_section7_tsv_field_masked", reg[1]), ("section7_tsv_sha256", REG_TSV_SHA_FIELD),
                                  ("note", "frozen separately with bench.py freeze; a change to it needs a TSV rebuild (the TSV "
                                           "header records the register's sha256 with section 7's 'TSV sha256' field masked as 64 "
                                           "zeros, since section 7 records the TSV's sha256) and so a new manifest")])),
        ("counts", OrderedDict([("tsv_rows", n_rows), ("m_lower", m_total), ("m_upper", m_upper),
                                ("m_secondary_near_miss", M_SECONDARY_NEAR_MISS), ("interim_population", n_interim),
                                ("population_all_gates_open_at_most", n_final),
                                ("composition_all_gates_open", OrderedDict(sorted(comp_upper.items()))),
                                ("composition_all_gates_open_lower_view", OrderedDict(sorted(comp_lower.items()))),
                                ("s_build_set_entries", len(MANIFEST["sets"])),
                                ("carrier_selftest", "%d / %d" % (CARRIER_SELF["n_caught"], CARRIER_SELF["n_cases"]))])),
        ("files", files),
    ])
    txt = json.dumps(man, indent=1, ensure_ascii=False) + "\n"
    with open(FREEZE_MANIFEST, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)
    if json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8")) != json.loads(txt):
        die("freeze manifest read-back differs")
    print("freeze manifest: %s sha256 %s (%d files)" % (FREEZE_MANIFEST.relative_to(ROOT).as_posix(), sha256_file(FREEZE_MANIFEST),
                                                         len(files)))


if __name__ == "__main__":
    main()
