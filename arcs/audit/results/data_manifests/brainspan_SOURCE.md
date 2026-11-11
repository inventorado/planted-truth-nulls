# SOURCE: BrainSpan developmental transcriptome - RNA-Seq Gencode v10 summarized to genes

- **date fetched**: 2026-09-23
- **url(s)**:
  - https://www.brainspan.org/api/v2/well_known_file_download/267666525
  - https://www.brainspan.org/static/download.html
- **licence**: Allen Institute Terms of Use (https://alleninstitute.org/terms-of-use/) - noncommercial research use; not a CC licence
- **description**: BrainSpan RNA-Seq RPKM averaged to genes (Gencode v10): genes x samples matrix + gene and sample metadata; zip plus unzipped members.

## Notes

- expression_matrix.csv: 52376 genes x 524 samples (first column = row number)
- donors = 42; distinct ages = 31; distinct structure acronyms = 26
- ages (file order): 8 pcw, 9 pcw, 12 pcw, 13 pcw, 16 pcw, 17 pcw, 19 pcw, 21 pcw, 24 pcw, 25 pcw, 26 pcw, 35 pcw, 37 pcw, 4 mos, 10 mos, 1 yrs, 2 yrs, 3 yrs, 4 yrs, 8 yrs, 11 yrs, 13 yrs, 15 yrs, 18 yrs, 19 yrs, 21 yrs, 23 yrs, 30 yrs, 36 yrs, 37 yrs, 40 yrs
- structure acronyms: A1C, AMY, CB, CBC, CGE, DFC, DTH, HIP, IPC, ITC, LGE, M1C, M1C-S1C, MD, MFC, MGE, OFC, Ocx, PCx, S1C, STC, STR, TCx, URL, V1C, VFC
- Zip Last-Modified per server: Tue, 08 Oct 2013 (see literature/notes/resource-brainspan.md).

## Files (5; sha256, bytes, path relative to this folder)

| sha256 | bytes | path |
|---|---:|---|
| 995a8e75b76459ba2bdbb51ad2db8970272f546baae14ddd3a7df6bc3ac18a01 | 43050 | genes_matrix_csv/columns_metadata.csv |
| e8d98aa02874f6b12fe7e071f4f88435b88256b6e5c4ba1d799e7b82aad28ee2 | 183262070 | genes_matrix_csv/expression_matrix.csv |
| 6da15f84243f4218c25daec46ee96cf8fe7879dc09344d763e1bc71d9c3b34e8 | 591 | genes_matrix_csv/readme.txt |
| dbfea0211aea42f6032084c3cdacb737943cbd786115dc5fde0f754708ae988b | 2151132 | genes_matrix_csv/rows_metadata.csv |
| c0e7293bcffde300272b56643ac17706268f4d4617eb5975f3fe8e2dd38b3b66 | 62218535 | genes_matrix_csv.zip |
