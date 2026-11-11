# SOURCE: GAMBA brain-expressed background genes (GAMBA-MATLAB)

- **date fetched**: 2026-09-23
- **url(s)**:
  - https://github.com/dutchconnectomelab/GAMBA-MATLAB @ 0c0128688ba898ea8bc14f0a54d6f18e12da2767
  - https://raw.githubusercontent.com/dutchconnectomelab/GAMBA-MATLAB/0c0128688ba898ea8bc14f0a54d6f18e12da2767/Background_genes_null_brain.csv
  - https://raw.githubusercontent.com/dutchconnectomelab/GAMBA-MATLAB/0c0128688ba898ea8bc14f0a54d6f18e12da2767/LICENSE
  - https://raw.githubusercontent.com/dutchconnectomelab/GAMBA-MATLAB/0c0128688ba898ea8bc14f0a54d6f18e12da2767/README.md
  - https://raw.githubusercontent.com/dutchconnectomelab/GAMBA-MATLAB/0c0128688ba898ea8bc14f0a54d6f18e12da2767/src/permutation_null_brain.m
  - https://raw.githubusercontent.com/dutchconnectomelab/GAMBA-MATLAB/0c0128688ba898ea8bc14f0a54d6f18e12da2767/src/gene_expression.mat
- **licence**: MIT (GAMBA-MATLAB LICENSE file); underlying GTEx/AHBA data under their own terms
- **description**: GAMBA null-brain-gene background: 20,949 AHBA genes with three 0/1 GTEx-derived brain-expression flags (Wei et al. 2022 HBM).

## Notes

- rows = 20949; unique symbols = 20909; rows sharing a duplicated symbol = 79 (duplicates can carry conflicting flags, e.g. APOC4 1/0 on 'brain >= body'); column sums over rows = {'brain > body (default)': 2711, 'brain >= body': 8989, 'brain non-zero': 18405}
- Default GAMBA background = column 'brain > body (default)': genes over-expressed in brain vs other GTEx body sites (paper: one-tailed two-sample t-test, FDR q<.05; paper N = 2,711).
- 'brain >= body' = over- or similarly expressed in brain (paper N = 8,989).
- 'brain non-zero' = expressed in brain without contrast. CSV sum differs from paper (16,743) and from permutation_null_brain.m docstring (16,778); docstring also gives 2,655 / 8,296 for the other two - the toolbox .mat index vectors are what the MATLAB nulls use; CSV vs .mat not reconciled here.
- GAMBA-MATLAB install.m also pulls a Dropbox bundle (https://www.dropbox.com/sh/psfudnzktyd0860/AABtx7ESvEphO60dcV_xbQ4qa?dl=0) - NOT fetched.
- Paper venue: Human Brain Mapping 43(3):885-901 (2022), not Nat Commun.

## Files (5; sha256, bytes, path relative to this folder)

| sha256 | bytes | path |
|---|---:|---|
| 442334c3cb487625349fc6e6be6fee121dbc7bdb35b9277133c04032ee0fa53a | 268733 | Background_genes_null_brain.csv |
| a79e7800c816c437c3c14c3bd73a6913f928234813dc7f36afb508412e81cfb4 | 1068 | LICENSE |
| 930eaea3d9d6799e4a784057d7dd257a333cce1c0e1ef33fbc628c060ebe9f93 | 13537 | README.md |
| 4ad659d8d8b19b2d256f0fb5de8004af0103ea1f91765ab7384aa1948c6fe855 | 16786684 | src/gene_expression.mat |
| 927e4c827048dc62186aa11b3ba4a50da781c7c73dae2382c7b4e10f20331453 | 6584 | src/permutation_null_brain.m |
