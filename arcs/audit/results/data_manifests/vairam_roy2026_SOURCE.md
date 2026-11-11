# SOURCE: Vairam & Roy 2026 neuroomics-asd code (hyper/hypo-connectivity x AHBA)

- **date fetched**: 2026-09-23
- **url(s)**:
  - https://github.com/AbinayaVairam0903/neuroomics-asd.git @ b503d1ef53a5e642974815ea1dd6a1b7ebd0e929 2026-08-01T21:00:02+05:30 (git clone --depth 1)
- **licence**: no licence file in repo (GitHub API license=null; all rights reserved by default)
- **description**: Author Python pipeline (19 numbered scripts + main.py/config.yaml) for the ABIDE hyper/hypo connectivity x AHBA/AAL3 PLSR preprint; code only, no data.

## Notes

- HEAD b503d1ef53a5e642974815ea1dd6a1b7ebd0e929 2026-08-01T21:00:02+05:30
- data files shipped in repo: none
- data needed (none included): ABIDE I preprocessed (C-PAC nofilt_noglobal func_preproc) + ABIDE II raw (S3 fcp-indi) + phenotypes; AHBA microarray (human.brain-map.org; gene_expression.csv, SampleAnnot.csv, Probes.csv); AAL3v1 atlas (NITRC AAL3v1_for_SPM12.zip; AAL3v1_1mm.nii.gz + .nii.txt); derived CSVs (Harmonized_ABIDE.csv, ASD/HC_Mean_ROI.csv, parcel_gene_expression.csv, FGSEA_*.csv, Neurosynth_Decode.csv) produced by earlier steps or external tools. Scripts hard-code the authors' Windows paths (D:\PLS\..., C:\Users\dhipi\...) that override config.yaml.
- LV1 / BrainSMASH: NOT computed anywhere in this repo. Keyword scan (brainsmash|surrogate|variogram|PLSCanonical|LV1|latent variable|neurosynth|spin) hits: ['15_gene_expression_trajectories.py:103: sns.despine()', '18_wordcloud.py:26: "DECODE_FILE": "Neurosynth_Decode.csv"', '18_wordcloud.py:128: plot_wordcloud(g1_term_freqs, "Gradient 1 – Cognitive Terms (Neurosynth)")', '18_wordcloud.py:129: plot_wordcloud(g2_term_freqs, "Gradient 2 – Cognitive Terms (Neurosynth)")']. 8_pls_analysis.py is sklearn PLSRegression(n_components=2) of Delta-FC on genes; 17_functional_gradient_analysis.py uses brainspace GradientMaps; 18_wordcloud.py only reads a precomputed Neurosynth_Decode.csv. The PLSC/LV1, BrainSMASH surrogates, LOSO/LORO and Neurosynth decoding reported in the preprint have no code here.
- requirements.txt: numpy pandas scikit-learn matplotlib seaborn nibabel nilearn gseapy tqdm joblib requests pyyaml wordcloud neuroCombat (brainspace used by script 17 but not listed).

## Files (24; sha256, bytes, path relative to this folder)

| sha256 | bytes | path |
|---|---:|---|
| 361e092de9bb6284e4e38600ec7c300a9796574acd063ea71b1a4e224db53598 | 3932 | repo/10_differential_correlation_fisher.py |
| e079259e374dc93409adec33a6fb543eecc9f2645b731b8a2df6bab7a7061b47 | 4773 | repo/11_spearman_correlation.py |
| 09a761b93586552150b705d64816ed59f5e79ae37d57ebcd6a43edd48396d669 | 5500 | repo/12_Fisher's_R-to-Z_transformatiom.py |
| 8ae6e82c81e49d0d956b46aea7d1bef346e4bfcc1c6fd25ab99f5d12504bed44 | 10267 | repo/13_hierarchical_clustering_enrichment.py |
| f43abc81a744049a9a4f38958d520809e3310fdcd301d04acdd696f6d16a0fb8 | 5269 | repo/14_brain_region_expression.py |
| e98a23e0afebaf8b7cf4bbb32c1cf57ca5a3767e862065e503e1f4b9abff753e | 5289 | repo/15_gene_expression_trajectories.py |
| 1b6e0db27c2046b863730cbf120bc6bc7171a93c788fef7fb6f60134121b9068 | 8872 | repo/16_region_mapping_asd_genes_dynamic.py |
| d0e9bee552b16e174340d69ae488a0d8bdfd3526434d5ea50541619c2420483d | 20969 | repo/17_functional_gradient_analysis.py |
| 839f50b4800055efb58a26a0bbbebe9c9f8de664dec72b3086c92fd39febd318 | 5808 | repo/18_wordcloud.py |
| 521f8f48d51810e79ab785c65ac2cac0fc0484d4d4dcfa2b03eba3cf58273c38 | 5690 | repo/19_ados_subtype.py |
| b82b12252517e6e170bcfb711b2a2e4fcd80f5fcd70fbee6f86b5c02ec4a8a17 | 5939 | repo/1_abide_ahba_downloader.py |
| 1767cfb18ff148721f60e57547e93ab80d09b647766e725a95ea6c924a321ef5 | 5631 | repo/2_idp_processing.py |
| c2334ea26038e7e217d3d11f822ca650abb1a3423733a4de11499c1917328e20 | 8483 | repo/3_idp_phenotype_mapping.py |
| 16635710918b56e8d9fc640dd5e179774a4eb068a9a7a2da08d6a39ba007540a | 4748 | repo/4_abide_harmonisation.py |
| 2f4814a7550f03a5b6eb6444627b6d85528bd186f4fee8d5d70ee0e07f911c3b | 5594 | repo/5_hyper_hypo_connectivity.py |
| cbcda80ddeaac9c95561636bc4a3aac659ad6c876a439b7511abd8ae0b0183a3 | 5026 | repo/6_ahba_to_aal3.py |
| a9f31443a2e2fe9521284edd7df7b053dd17d8f67f9cc29c7d5cf0611adbbfcb | 5734 | repo/7_identify_asd_hc_rois.py |
| 5c9351fb594ca62979837d32b8d0b7a8feb4e093104151927e8d690da1a6ef12 | 3407 | repo/8_pls_analysis.py |
| f9cb233851c6c08ee83f5fc5e15f663c6f9722e6f8f190fb40e090ffc0d51d6a | 3220 | repo/9_fast_gene_enrichment.py |
| 4f97c661980c05740ed5281b05267cd55e72f685ae5afbeb8390dcfc75c5ee90 | 546 | repo/config.yaml |
| cfdd5b85e10ea11f50d2755acab7269a8d2e6d7859826e6220d445c7faa70c6b | 1161 | repo/main.py |
| 37452c0d3653cc89b6dfc3f99acaabb2fc6e4410740217fc7828a92ff9161693 | 353 | repo/pipeline_utils.py |
| ff452d0d753ecadcf25092156c75971c23cbd689874eba018e3b4dcb5cc2970c | 3663 | repo/README.md |
| 8a481c15396207a1c0c79c7dabdb6771377364e453c354f381951c355e560910 | 130 | repo/requirements.txt |
