# SOURCE: Segura et al. 2025 NeuroVault maps (collection 12297)

- **date fetched**: 2026-09-23
- **url(s)**:
  - https://neurovault.org/api/images/790618/
  - https://neurovault.org/media/images/12297/zstat1_ADOS2Total_dm_MFG%20iFC%20corrected%20sex%20ADOSPOS%20-%20AS%20TX.nii.nii.gz
  - https://neurovault.org/api/images/781986/
  - https://neurovault.org/media/images/12297/zstat1_PostHocSCA_VisualSeed2iFC_NegativeControl.nii.gz
  - https://neurovault.org/api/collections/12297/
- **licence**: CC0 (NeuroVault FAQ Q13, https://neurovault.org/FAQ, checked 2026-09-23); collection-level licence field is null
- **description**: Two unthresholded group-level Z maps (MNI) from NeuroVault collection 12297 'Gene decoding ASD-ADHD'.

## Notes

- image 790618: name='MFG iFC corrected sex ADOSPOS - AS TX'; collection 12297; map_type=Z map; image_type=statistic_map; modality=fMRI-BOLD; space/template=GenericMNI (not_mni=False); thresholded=False; analysis_level=group; N subjects=166; description='Post Hoc unthresholded SCA-based corrected zstat 1 map - Transdiagnosis (including sex as covariate)'; file=image_790618_zstat1_ADOS2Total_dm_MFG_iFC_corrected_sex_ADOSPOS_-_AS_TX.nii.nii.gz
- image 781986: name='Visual 2 Negative Control iFC - AS TX'; collection 12297; map_type=Z map; image_type=statistic_map; modality=fMRI-BOLD; space/template=GenericMNI (not_mni=False); thresholded=False; analysis_level=group; N subjects=166; description='Negative Control 2 Post Hoc unthresholded SCA-based map - Transdiagnosis'; file=image_781986_zstat1_PostHocSCA_VisualSeed2iFC_NegativeControl.nii.gz
- collection 12297: name='Gene decoding ASD-ADHD'; owner=psegura; images=17; licence field=None; description='Exploration of cross-diagnostic genetic and functional connectivity correlations using iFC SCA-based maps for each of the MDMR-derived regions associated with autistic symptoms transdiagnostically.'
- CAUTION: neither image is a case-vs-control group map. 790618 is a seed-based (MFG) iFC map of the ADOS-2 Total association, transdiagnostic (ASD+ADHD), sex-corrected; 781986 is a negative-control map (visual seed 2 SCA), transdiagnostic. Treat as the paper's symptom map and its negative control.

## Files (5; sha256, bytes, path relative to this folder)

| sha256 | bytes | path |
|---|---:|---|
| 6c8dc97e6f08981fb0c133684f242de06f47d9c1054d92321aeb26135ecaf839 | 3156 | collection_12297.json |
| e3b404f99ee89eed37b0fd08a8aa6f1ee956620b3399469d3a0c335378505585 | 1757 | image_781986.json |
| 0c476e8e8fa227edc6fb0007c4eccd92e5376361b497f836fef3d0cd8c1f4741 | 75117 | image_781986_zstat1_PostHocSCA_VisualSeed2iFC_NegativeControl.nii.gz |
| 35373861fca420d637e6dee417b256cbe60732086ab72a0ec64a59c09efab9c3 | 1813 | image_790618.json |
| 802b4b6bf31136aee0507676a3ca4c14e0ba97bafe378f5b6aaddbe5c160af12 | 71440 | image_790618_zstat1_ADOS2Total_dm_MFG_iFC_corrected_sex_ADOSPOS_-_AS_TX.nii.nii.gz |
