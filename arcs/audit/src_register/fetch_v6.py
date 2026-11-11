"""Claims register DRAFT v6 pre-freeze downloads (decisions R1 and R12 of the orchestrator under the operator's standing
delegation, 2026-09-26; register sections 1.6, 1.11). Public, ungated external set sources; no map, no gated carrier; no
identifier is sent (plain curl, no login, no e-mail, no API key).

  E:\\data\\asdg\\register_sets_src\\enrichr_2026-09-26\\   Enrichr gene-set libraries, served by name from
        https://maayanlab.cloud/Enrichr/geneSetLibrary?mode=text&libraryName=<name>
        - KEGG_2021_Human: the library Vairam / Roy name ("KEGG 2021 Human" via gseapy prerank = the Enrichr library);
        - GO_Biological_Process_2013 / 2015 / 2017 / 2017b / 2018: the Enrichr GO BP libraries that existed up to
          Romero-Garcia's submission (2017-10-24) and the next one, fetched to identify the release the paper used (R12);
        - datasetStatistics.json: Enrichr's current catalogue listing (evidence of what is listed today).
  E:\\data\\asdg\\register_sets_src\\panther_16.0_goslim\\   PANTHERGOslim.obo of PANTHER 16.0 (the release Buch names), used
        only to map Buch's figure labels by the register's name rule (the sets themselves are built under gate G1).

  (v6.1) Enrichr KEGG_2015 and KEGG_2026 (the KEGG release rules, register 1.6); E:\\data\\asdg\\register_sets_src\\go_2021-11-16\\
        (GO release in force at Buch's submission, received 2021-11-29: the GO-slim fallback sets' annotations).
  (v6.2) Enrichr KEGG_2016 (P5: the Romero-Garcia KEGG candidates are KEGG_2015 and KEGG_2016); PANTHER 16.0's own
        gene-to-GO-slim annotation as served (PTHR16.0_human, P3: the Buch GO-slim fallback sets; the GO 2021-11-16
        version is kept only for the overlap descriptor).

Every file is recorded (URL, bytes, sha256) in its folder's SOURCE.md by s_sources_md.py (called here for these two
folders only). Idempotent: a file already present with the pinned sha256 is not fetched again.
Run: env\\venv\\Scripts\\python.exe -X utf8 arcs\\audit\\src_register\\fetch_v6.py
Prints counts and hashes only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_util  # noqa: E402
import s_sources_md  # noqa: E402

SRC = Path(r"E:\data\asdg\register_sets_src")
ENR = "https://maayanlab.cloud/Enrichr/geneSetLibrary?mode=text&libraryName=%s"
FILES = {
    ("enrichr_2026-09-26", "KEGG_2021_Human.txt"): ENR % "KEGG_2021_Human",
    ("enrichr_2026-09-26", "GO_Biological_Process_2013.txt"): ENR % "GO_Biological_Process_2013",
    ("enrichr_2026-09-26", "GO_Biological_Process_2015.txt"): ENR % "GO_Biological_Process_2015",
    ("enrichr_2026-09-26", "GO_Biological_Process_2017.txt"): ENR % "GO_Biological_Process_2017",
    ("enrichr_2026-09-26", "GO_Biological_Process_2017b.txt"): ENR % "GO_Biological_Process_2017b",
    ("enrichr_2026-09-26", "GO_Biological_Process_2018.txt"): ENR % "GO_Biological_Process_2018",
    ("enrichr_2026-09-26", "datasetStatistics.json"): "https://maayanlab.cloud/Enrichr/datasetStatistics",
    ("panther_16.0_goslim", "PANTHERGOslim.obo"): "https://data.pantherdb.org/PANTHER16.0/ontology/PANTHERGOslim.obo",
    # register DRAFT v6.1 (Q2, Q3, Q7): Enrichr KEGG snapshots for the KEGG release rules; the GO release in force at Buch's
    # submission (received 2021-11-29 -> release 2021-11-16) for the GO-slim fallback sets
    ("enrichr_2026-09-26", "KEGG_2015.txt"): ENR % "KEGG_2015",
    ("enrichr_2026-09-26", "KEGG_2026.txt"): ENR % "KEGG_2026",
    ("go_2021-11-16", "go-basic.obo"): "https://release.geneontology.org/2021-11-16/ontology/go-basic.obo",
    ("go_2021-11-16", "goa_human.gaf.gz"): "https://release.geneontology.org/2021-11-16/annotations/goa_human.gaf.gz",
    # register DRAFT v6.2 (P5): the second Romero-Garcia KEGG candidate; (P3) PANTHER 16.0 gene -> GO-slim annotation
    ("enrichr_2026-09-26", "KEGG_2016.txt"): ENR % "KEGG_2016",
    ("panther_16.0_goslim", "PTHR16.0_human"): "https://data.pantherdb.org/ftp/sequence_classifications/16.0/"
                                               "PANTHER_Sequence_Classification_files/PTHR16.0_human",
}


def main() -> None:
    for (folder, name), url in FILES.items():
        out = SRC / folder / name
        if out.exists():
            print("present %s/%s %d B sha256 %s" % (folder, name, out.stat().st_size, fetch_util.sha256(out)))
            continue
        r = fetch_util.get(url, out)
        print("fetched %s/%s %d B sha256 %s (%s)" % (folder, name, r["bytes"], r["sha256"], r["content_type"]))
    s_sources_md.main(only=("enrichr_2026-09-26", "panther_16.0_goslim", "go_2021-11-16"))


if __name__ == "__main__":
    main()
