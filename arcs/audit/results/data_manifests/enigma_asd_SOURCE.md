# SOURCE: ENIGMA-ASD case-control summary statistics + DK/aseg labels

- **date fetched**: 2026-09-23
- **url(s)**:
  - https://github.com/MICA-MNI/ENIGMA @ b08974b55243060cbc1fad12c87048037446e8f7
  - https://raw.githubusercontent.com/MICA-MNI/ENIGMA/b08974b55243060cbc1fad12c87048037446e8f7/LICENSE
  - https://raw.githubusercontent.com/MICA-MNI/ENIGMA/b08974b55243060cbc1fad12c87048037446e8f7/enigmatoolbox/datasets/summary_statistics/asd_mega-analysis_case-controls_CortThick.csv
  - https://raw.githubusercontent.com/MICA-MNI/ENIGMA/b08974b55243060cbc1fad12c87048037446e8f7/enigmatoolbox/datasets/summary_statistics/asd_meta-analysis_case-controls_CortThick.csv
  - https://raw.githubusercontent.com/MICA-MNI/ENIGMA/b08974b55243060cbc1fad12c87048037446e8f7/enigmatoolbox/datasets/summary_statistics/asd_meta-analysis_case-controls_SubVol.csv
  - https://raw.githubusercontent.com/MICA-MNI/ENIGMA/b08974b55243060cbc1fad12c87048037446e8f7/enigmatoolbox/datasets/matrices/hcp_connectivity/strucLabels_ctx.csv
  - https://raw.githubusercontent.com/MICA-MNI/ENIGMA/b08974b55243060cbc1fad12c87048037446e8f7/enigmatoolbox/datasets/matrices/hcp_connectivity/strucLabels_sctx.csv
  - https://raw.githubusercontent.com/MICA-MNI/ENIGMA/b08974b55243060cbc1fad12c87048037446e8f7/enigmatoolbox/datasets/matrices/hcp_connectivity/strucLabels_with_sctx.csv
  - https://raw.githubusercontent.com/MICA-MNI/ENIGMA/b08974b55243060cbc1fad12c87048037446e8f7/enigmatoolbox/datasets/parcellations/aparc_fsa5.csv
  - https://raw.githubusercontent.com/MICA-MNI/ENIGMA/b08974b55243060cbc1fad12c87048037446e8f7/enigmatoolbox/datasets/parcellations/aparc_conte69.csv
  - https://raw.githubusercontent.com/MICA-MNI/ENIGMA/b08974b55243060cbc1fad12c87048037446e8f7/enigmatoolbox/datasets/parcellations/aparc_aseg_fsa5_with_sctx.csv
  - https://github.com/alegiac95/METAXCAN_TWAS_ANALYSIS @ e045bc51961b0425f51bbdf54672d59222cfa8b9
  - https://raw.githubusercontent.com/alegiac95/METAXCAN_TWAS_ANALYSIS/e045bc51961b0425f51bbdf54672d59222cfa8b9/data/ENIGMA/ENIGMA_structural_organised.xlsx
  - https://raw.githubusercontent.com/alegiac95/METAXCAN_TWAS_ANALYSIS/e045bc51961b0425f51bbdf54672d59222cfa8b9/data/DK-files/DesikanKilliany_atlas.csv
  - https://raw.githubusercontent.com/alegiac95/METAXCAN_TWAS_ANALYSIS/e045bc51961b0425f51bbdf54672d59222cfa8b9/data/DK-files/atlas-DK_fsa5_lh_aparc.annot
  - https://raw.githubusercontent.com/alegiac95/METAXCAN_TWAS_ANALYSIS/e045bc51961b0425f51bbdf54672d59222cfa8b9/data/DK-files/atlas-DK_fsa5_rh_aparc.annot
- **licence**: ENIGMA Toolbox: BSD-3-Clause (LICENSE file); Giacomel repo: no licence stated; abagen atlas: BSD-3-Clause
- **description**: ENIGMA-ASD Cohen's d (ASD vs controls) for DK-68 cortical thickness and aseg subcortical volume, with region-label and parcellation files to map them.

## Notes

- asd_mega-analysis_case-controls_CortThick.csv: 68 rows; Structure = L_bankssts .. R_insula; columns = ['CorticalThickness', 'Structure', 'd_icv', 'se_icv', 'low_ci_icv', 'up_ci_icv', 'n_controls', 'n_patients', 'pobs', 'fdr_p']; n_controls/n_patients first row = 1569.0/1650.0
- asd_meta-analysis_case-controls_CortThick.csv: 68 rows; Structure = L_bankssts .. R_insula; columns = ['CorticalThickness', 'Structure', 'd_icv', 'se_icv', 'low_ci_icv', 'up_ci_icv', 'n_controls', 'n_patients', 'pobs', 'fdr_p']; n_controls/n_patients first row = 976/1060
- asd_meta-analysis_case-controls_SubVol.csv: 16 rows; Structure = Laccumb .. RLatVent; columns = ['SubcorticalVolume', 'Structure', 'd_icv', 'se_icv', 'low_ci_icv', 'up_ci_icv', 'n_controls', 'n_patients', 'pobs', 'fdr_p']; n_controls/n_patients first row = 1071/984
- Parcellation: CortThick CSVs = Desikan-Killiany 68 cortical regions (34 per hemisphere, L_/R_ prefix, FreeSurfer aparc names); SubVol CSV = FreeSurfer aseg subcortical structures, L/R (accumb, amyg, caud, hippo, pal, put, thal) plus lateral ventricles (LLatVent/RLatVent) = 16 rows. Effect size d_icv (Cohen's d); se/CI/pobs empty.
- ENIGMA meta/mega CSVs: the Toolbox code (datasets/base.py load_summary_stats('asd')) does not name the source paper; ENIGMA-ASD working group (van Rooij et al. 2018, per giacomel2026cartography note: 1,571 ASD / 1,651 controls - close to the mega CSV n) - attribution not verified here. Sample sizes per row in n_controls/n_patients.
- strucLabels_ctx/sctx/with_sctx.csv: ENIGMA Toolbox region-name lists (DK-68 cortex; 14 subcortical: accumbens, amygdala, caudate, hippocampus, pallidum, putamen, thalamus x L/R; no ventricles).
- parcellations/aparc_*.csv: per-VERTEX DK labels on fsaverage5 / conte69 surfaces (surface, not volumetric). The ENIGMA Toolbox ships no volumetric DK atlas; a volumetric DK (MNI152) is abagen's bundled atlas-desikankilliany (copied below under abagen_atlas/ if abagen was importable at run time).
- Giacomel 2026 repo (github.com/alegiac95/METAXCAN_TWAS_ANALYSIS) has NO licence file; its data/ENIGMA xlsx has sheets Surface/Thickness/Subcortical (per note giacomel2026cartography.md). Redistribution terms unknown.
- abagen_atlas/: copied from abagen 0.1.3 package data (fetch_desikan_killiany: DK volumetric atlas, MNI152, 83 regions = 68 cortex + 14 subcortex + brainstem; 1 mm, 146x182x155; abagen BSD-3-Clause). It has no lateral-ventricle label, so SubVol rows LLatVent/RLatVent have no target region; ENIGMA 'Laccumb' etc. map to abagen labels accumbensarea/amygdala/caudate/hippocampus/pallidum/putamen/thalamusproper by name (mapping not done here).

## Files (16; sha256, bytes, path relative to this folder)

| sha256 | bytes | path |
|---|---:|---|
| d061418326874d62e9c8589e6741b1cdd282887afafe56670b921b424b9cd16b | 2400 | abagen_atlas/atlas-desikankilliany.csv |
| 0a28c93f5967f0892810219e68edb32abcaa9fd796a217096512fb0724c20d8a | 216876 | abagen_atlas/atlas-desikankilliany.nii.gz |
| 47a5301cb4f956782fa99c6c0b110fc4717c4bb626a65a4d04890ed72a745a35 | 1164 | enigma_toolbox/enigmatoolbox/datasets/matrices/hcp_connectivity/strucLabels_ctx.csv |
| 913290bc0e00e133c4c2b4f38a55e055636fcd1fd9d54a8ef07406b0efaa1bde | 86 | enigma_toolbox/enigmatoolbox/datasets/matrices/hcp_connectivity/strucLabels_sctx.csv |
| 331333840228ccb9489d7b63f6d12c08bef9ee12ec0fbe95e27b7d86759ce97a | 1249 | enigma_toolbox/enigmatoolbox/datasets/matrices/hcp_connectivity/strucLabels_with_sctx.csv |
| b6d034234b7101097ef1368b4bcce2f2e3c707a23aa12c3a4e911cf7c78d1530 | 283550 | enigma_toolbox/enigmatoolbox/datasets/parcellations/aparc_aseg_fsa5_with_sctx.csv |
| 7c2aa12fcbe956d12963549980c1381a14341f663951aa9948e6458050cbe2a7 | 183533 | enigma_toolbox/enigmatoolbox/datasets/parcellations/aparc_conte69.csv |
| be8984177d648bf79935a898352d7069a41222e6eea6736f094236bf2cb9c365 | 57956 | enigma_toolbox/enigmatoolbox/datasets/parcellations/aparc_fsa5.csv |
| af4e609ec7e2e5422defbaa0c7f94ce72d9b3f3494ed095e455ba302b7a4ff03 | 5193 | enigma_toolbox/enigmatoolbox/datasets/summary_statistics/asd_mega-analysis_case-controls_CortThick.csv |
| ee076971be6688bc99106fce4a7198a3bd927d183adb245f9810d6f71efe4f29 | 5005 | enigma_toolbox/enigmatoolbox/datasets/summary_statistics/asd_meta-analysis_case-controls_CortThick.csv |
| b2b0b02c260ec87c6ab22f40e6162ab8a475dab373390be1edd465910ca62066 | 1092 | enigma_toolbox/enigmatoolbox/datasets/summary_statistics/asd_meta-analysis_case-controls_SubVol.csv |
| aecec6f9b8e75153c441e8332d349407df4082aaf367775df49553cb07f424fe | 1520 | enigma_toolbox/LICENSE |
| 74d1c2fd5e6b7ca193f06fee45a86f5638f347e38cea5ba27fce9fd69c0056be | 83444 | giacomel2026_repo/data/DK-files/atlas-DK_fsa5_lh_aparc.annot |
| ca86b3b0bd5b74e367519dd94157154ae7c61ad128680fcc7b52e1a799e34e9f | 83444 | giacomel2026_repo/data/DK-files/atlas-DK_fsa5_rh_aparc.annot |
| 58b623281e1d3fe7f690d1ad40d66bfcfe92cb50e1d5689d388f3615b69c4ac1 | 2640 | giacomel2026_repo/data/DK-files/DesikanKilliany_atlas.csv |
| a4d4feecb028366c6ccd2ee06b216fc2be758e9b6cf92b039549b78ab5d888c8 | 16118 | giacomel2026_repo/data/ENIGMA/ENIGMA_structural_organised.xlsx |
