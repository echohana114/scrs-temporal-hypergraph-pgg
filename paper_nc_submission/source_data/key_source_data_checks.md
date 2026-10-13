# Key Source-Data Checks

Figure summaries were generated from completed S20-S30 source files. The random seed manifest was generated from S20-S29 detail tables; S30 is deterministic post-processing.

Figure-specific Source Data packages are provided in `source_data/source_data_packages`: one package each for Figs. 1-5 and one package organized by S20-S30 for the supplementary overview figures. The file `source_data/source_data_package_manifest.csv` maps each package to its included CSV or JSON files.

## Main Performance

- S20 real: mean SCRS=0.8450, min SCRS=0.6289, gap vs Wang et al. baseline=+0.6543, gap vs CSGC=+0.6491, gap vs strategy-shuffled=+0.6157, gap vs score-shuffled=+0.0011.
- S20 synthetic: mean SCRS=1.0000, min SCRS=1.0000, gap vs Wang et al. baseline=+0.4100, gap vs CSGC=+0.2967, gap vs strategy-shuffled=+0.1433, gap vs score-shuffled=+0.0000.

## Mechanism Boundary

- S25 real: mean SCRS=0.8456, gap vs strategy-shuffled=+0.6074, gap vs score-shuffled=-0.0003, gap vs cooperator-only random=-0.0009.
- S25 synthetic: mean SCRS=1.0000, gap vs strategy-shuffled=+0.1200, gap vs score-shuffled=+0.0000, gap vs cooperator-only random=+0.0000.
- S29 clean controls: mean SCRS=0.8974, gap vs strategy-shuffled=+0.4577, gap vs uniform incident cooperator-only=+0.0013, gap vs random-neighbourhood cooperator-only=-0.0011, gap vs successful edge without score ranking=-0.0011.

## Extrapolation And Sensitivity

- S26 real: mean SCRS=0.9911, gap vs strategy-shuffled=+0.4313.
- S27 payoff_update_sensitivity_asynchronous_in_place real: mean SCRS=0.6978, gap vs strategy-shuffled=+0.3717, gap vs score-shuffled=+0.0009.
- S27 payoff_update_sensitivity_asynchronous_in_place synthetic: mean SCRS=1.0000, gap vs strategy-shuffled=+0.1800, gap vs score-shuffled=+0.0000.
- S27 payoff_update_sensitivity_baseline real: mean SCRS=0.6967, gap vs strategy-shuffled=+0.3678, gap vs score-shuffled=+0.0006.
- S27 payoff_update_sensitivity_baseline synthetic: mean SCRS=1.0000, gap vs strategy-shuffled=+0.2533, gap vs score-shuffled=+0.0000.
- S27 payoff_update_sensitivity_degree_normalized_payoff real: mean SCRS=0.7148, gap vs strategy-shuffled=+0.4285, gap vs score-shuffled=+0.0008.
- S27 payoff_update_sensitivity_degree_normalized_payoff synthetic: mean SCRS=1.0000, gap vs strategy-shuffled=+0.6267, gap vs score-shuffled=+0.0000.
- S27 payoff_update_sensitivity_per_capita_payoff real: mean SCRS=0.4394, gap vs strategy-shuffled=+0.1558, gap vs score-shuffled=+0.0015.
- S27 payoff_update_sensitivity_per_capita_payoff synthetic: mean SCRS=1.0000, gap vs strategy-shuffled=+1.0000, gap vs score-shuffled=+0.0000.

## Construction And Structure Audits

- S28 construction sensitivity: mean SCRS=0.8919, minimum SCRS=0.5874, gap vs Wang et al. baseline=+0.6400, gap vs CSGC=+0.6142, gap vs strategy-shuffled=+0.5929, gap vs score-shuffled=+0.0023.
- S30 temporal memory: SCRS gap vs strategy-shuffled is low=+0.3470, mid=+0.5955, high=+0.5921.
- S30 within-block overlap: SCRS gap vs strategy-shuffled is low=+0.3487, mid=+0.6096, high=+0.6300.
