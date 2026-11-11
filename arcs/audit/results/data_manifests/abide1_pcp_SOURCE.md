# ABIDE I PCP ROI time series - provenance

- Downloaded: 2026-09-23 (S3 listing taken 2026-09-23T06:25:07Z UTC)
- Script: `D:\RESEARCH\asd-imaging-genetics\src\data\fetch_abide1_pcp.py` (`python -X utf8 fetch_abide1_pcp.py all`; uncommitted at time of download)
- Source: public AWS S3 bucket `fcp-indi` (us-east-1), anonymous HTTPS, no credentials. Listing via ListObjectsV2 REST: `https://s3.amazonaws.com/fcp-indi?list-type=2&prefix=<prefix>`; files via `https://s3.amazonaws.com/fcp-indi/<key>`.
- Cell prefixes: `data/Projects/ABIDE_Initiative/Outputs/<pipeline>/<strategy>/<derivative>/` for pipeline in {cpac, dparsf}, strategy in {filt_global, nofilt_noglobal}, derivative in {rois_aal, rois_ho, rois_cc200}.
- Phenotype: `data/Projects/ABIDE_Initiative/Phenotypic_V1_0b_preprocessed1.csv` -> `phenotype/`. Top level of `data/Projects/ABIDE_Initiative/` holds only 3 files: `Phenotypic_V1_0b.csv` (175924 B), `Phenotypic_V1_0b_preprocessed.csv` (603964 B), `Phenotypic_V1_0b_preprocessed1.csv` (449443 B). No separate QC CSV exists there; QC is carried as columns of the preprocessed1 sheet.
- Local layout: `E:\data\asdg\abide1_pcp\<pipeline>\<strategy>\<derivative>\<FILE_ID>_<derivative>.1D`; phenotype in `E:\data\asdg\abide1_pcp\phenotype\`

## Licence / terms
ABIDE (FCP/INDI): "data usage is unrestricted for non-commercial research purposes"; Creative Commons Attribution-NonCommercial-ShareAlike (CC BY-NC-SA). Cite the specific datasets used and acknowledge funding sources; derivatives redistributed must carry the same licence. PCP citation: Craddock et al. 2013 (Neuroinformatics, abstract). The AWS registry's generic ODC-By statement is overridden by the dataset-specific CC BY-NC-SA statement (see `literature/notes/resource-abide-i-ii.md` s.3).

## Per-cell verification (all checks passed)
| pipeline | strategy | derivative | n_files | n_size_ok | n_md5=etag | n_parsed_ok | roi_columns | timepoints min-max | subjects | bytes |
|---|---|---|---|---|---|---|---|---|---|---|
| cpac | filt_global | rois_aal | 1102 | 1102 | 1102 | 1102 | 116 (x1102) | 78-316 | 1102 | 246213753 |
| cpac | filt_global | rois_ho | 1102 | 1102 | 1102 | 1102 | 111 (x1102) | 78-316 | 1102 | 235952717 |
| cpac | filt_global | rois_cc200 | 1102 | 1102 | 1102 | 1102 | 200 (x1102) | 78-316 | 1102 | 430931451 |
| cpac | nofilt_noglobal | rois_aal | 1102 | 1102 | 1102 | 1102 | 116 (x1102) | 78-316 | 1102 | 250889571 |
| cpac | nofilt_noglobal | rois_ho | 1102 | 1102 | 1102 | 1102 | 111 (x1102) | 78-316 | 1102 | 240199907 |
| cpac | nofilt_noglobal | rois_cc200 | 1102 | 1102 | 1102 | 1102 | 200 (x1102) | 78-316 | 1102 | 437396532 |
| dparsf | filt_global | rois_aal | 1102 | 1102 | 1102 | 1102 | 116 (x1102) | 77-315 | 1102 | 485714216 |
| dparsf | filt_global | rois_ho | 1102 | 1102 | 1102 | 1102 | 111 (x1102) | 77-315 | 1102 | 464736325 |
| dparsf | filt_global | rois_cc200 | 1102 | 1102 | 1102 | 1102 | 200 (x1102) | 77-315 | 1102 | 831928690 |
| dparsf | nofilt_noglobal | rois_aal | 1102 | 1102 | 1102 | 1102 | 116 (x1102) | 77-315 | 1102 | 480641613 |
| dparsf | nofilt_noglobal | rois_ho | 1102 | 1102 | 1102 | 1102 | 111 (x1102) | 77-315 | 1102 | 460156376 |
| dparsf | nofilt_noglobal | rois_cc200 | 1102 | 1102 | 1102 | 1102 | 200 (x1102) | 77-315 | 1102 | 824609381 |

Total ROI bytes: 5389370532. Every .1D has a `#`-prefixed header row of atlas label ids; all 12 cells share the identical 1102-subject FILE_ID set.

Phenotype: `Phenotypic_V1_0b_preprocessed1.csv`, 449443 B, 1112 data rows, 106 columns, size_ok=True, md5=etag True. QC columns: qc_rater_1, qc_notes_rater_1, qc_anat_rater_2, qc_anat_notes_rater_2, qc_func_rater_2, qc_func_notes_rater_2, qc_anat_rater_3, qc_anat_notes_rater_3, qc_func_rater_3, qc_func_notes_rater_3.

Caveat: 77 phenotype rows have FILE_ID `no_filename`; 1035 of the 1102 downloaded FILE_IDs appear in the sheet's FILE_ID column and 67 downloaded files have no matching FILE_ID row (join those via SUB_ID if needed).

Checks run: file count == listed keys; local size == S3 Size; local MD5 == S3 ETag (all single-part); whitespace-numeric parse with rectangular rows; planted-failure gate (non-numeric, ragged, header-only, empty, size mismatch, md5 mismatch, missing file) all caught.

## Manifest
`MANIFEST.tsv` (columns key, size, etag, local_sha256; 13225 rows): sha256 `93a80c18114ef3eb3d941803cd9563de0dbe0100e3322432ee7c0526a6788335`. Copy: `D:\RESEARCH\asd-imaging-genetics\arcs\audit\results\data_manifests\abide1_pcp_MANIFEST.tsv`.
Also here: `_listing.json` (raw S3 listing incl. LastModified), `_verify_summary.json` (verification output).
