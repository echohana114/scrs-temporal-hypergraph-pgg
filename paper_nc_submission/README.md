# SCRS Nature Communications Manuscript Package

This directory contains the current manuscript draft, verified references, main figures and source data for:

Success-context cooperative role screening stabilizes cooperation in temporal hypergraph public goods games

## Contents

- `manuscript.md`: full draft with Abstract, Introduction, Results, Discussion, Methods, Data Availability and Code Availability.
- `figure_legends.md`: standalone legends for Figs. 1-5 and supplementary S20-S27 source views.
- `references_verified.bib`: BibTeX generated from DOI metadata and manual dataset URL entries.
- `reference_verification.md`: DOI/URL verification report from 2026-09-02.
- `source_data/`: figure source CSVs and copied S20-S27 supplementary source tables.
- `tables/`: supplementary navigation tables for experiment design, dataset statistics and ablation definitions.
- `release/`: deposition checklist and manifest for Zenodo/OSF/Figshare/GitHub archiving.
- `figures/`: exported SVG, PDF and PNG versions of Figs. 1-5.
- `scripts/make_paper_source_data.py`: regenerates figure source data from completed S20-S27 formal outputs.
- `scripts/make_figures.py`: regenerates main figures from `source_data/`.
- `scripts/verify_references.py`: regenerates verified BibTeX and reference verification tables.
- `requirements.txt` and `environment.yml`: Python environment records for package regeneration.

## Regeneration

Run from the repository root:

```bash
./.venv_scrs_nc/bin/python paper_nc_submission/scripts/make_paper_source_data.py
./.venv_scrs_nc/bin/python paper_nc_submission/scripts/make_figures.py
./.venv_scrs_nc/bin/python paper_nc_submission/scripts/verify_references.py
```

The source-data script reads completed formal output directories S20-S27 and writes derived CSVs under `paper_nc_submission/source_data`, supplementary tables under `paper_nc_submission/tables`, and release planning files under `paper_nc_submission/release`. It does not rerun formal experiments and does not modify the original S20-S27 output directories.

## Main Figures

- Fig. 1: `figures/fig1_model_diagram.svg`, `.pdf`, `.png`
- Fig. 2: `figures/fig2_main_performance.svg`, `.pdf`, `.png`
- Fig. 3: `figures/fig3_mechanism_decomposition.svg`, `.pdf`, `.png`
- Fig. 4: `figures/fig4_robustness_null_stress.svg`, `.pdf`, `.png`
- Fig. 5: `figures/fig5_external_sensitivity_noise.svg`, `.pdf`, `.png`

`figures/figure_manifest.csv` maps each figure to its source CSVs.

Supplementary S20-S27 overview figures are in `figures/supplementary`, with SVG, PDF and PNG exports for each experiment group.

## Claim Boundaries

- Strongly supported: SCRS stabilizes cooperation against the temporal-hypergraph imitation baseline based on Wang et al., CSGC and strategy-shuffled SCRS across the formal S20-S27 evidence set.
- Mechanism supported: the main gain comes from cooperation-conditioned role screening inside successful groups.
- Caution: SCRS is close to score-shuffled SCRS, so the manuscript should not claim a broad independent advantage for score ordering.
- Caution: cooperator-only random role selection is close to SCRS in S25, so payoff ranking among eligible cooperators is not required under the tested conditions.

## Deposition Notes

Before submission, mint public data and code records and replace the DOI/URL placeholders in `manuscript.md`. The local deposition checklist is `release/deposition_checklist.md`; it is a preparation aid, not a substitute for a public repository DOI.
