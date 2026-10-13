# Manuscript Package QC Report

Last checked: 2026-10-13.

## Text Checks

- Abstract length: 111 words.
- Abstract sentence count: 4.
- References in abstract: none.
- Results figure order: Fig. 2, Fig. 3, Fig. 4, Fig. 5.
- Manuscript citation keys: 43.
- Missing citation keys in `references_verified.bib`: 0.
- BibTeX entries: 55, within the requested limit of 70.
- Checked phrasing exclusions and legacy labels in `manuscript.md`, `figure_legends.md`, `README.md`, `source_data/key_source_data_checks.md` and `release/deposition_checklist.md`: no matches for the legacy baseline label, old manuscript title or the listed disliked phrases.
- Claim scope revised on 2026-10-13: manuscript title, abstract, Results and Discussion now center local cooperative role screening under temporal-hypergraph exposure; temporal exposure is framed as a local context layer, while fine edge-score ordering and payoff ranking are not claimed as independent drivers.
- Author line, affiliation, correspondence, acknowledgements, funding, author contributions and competing-interest statements were added from the available Hui Zhao affiliation record.

## Reference Checks

- DOI references checked through Crossref: 49.
- DOI references verified: 49.
- DOI references failed: 0.
- Manual URL dataset/resource references: 6.
- DOI entries with missing pages or article identifiers after manual page supplement: 0.

## Availability Checks

- Data Availability no longer presents a local directory as the formal access route; the final public repository DOI is still unavailable in the workspace and must be replaced after public deposition.
- Code Availability names a public GitHub release plus DOI archive as the access route; the workspace has no Git remote or resolvable HEAD commit, so the final GitHub URL, archival DOI and release tag or commit must be supplied after public release.
- Deposition checklist: `release/deposition_checklist.md`.
- Deposition manifest: `release/deposition_manifest.csv`.
- Environment files: `requirements.txt` and `environment.yml`.
- Random seed manifest rows: 200,250.

## Figure And Source-Data Checks

- Main figures generated: 5.
- Supplementary overview figures generated: 11, one each for S20-S30.
- Figure manifest rows excluding header: 16.
- Source-data manifest rows excluding header: 96.
- Supplementary table manifest rows excluding header: 4.
- Table S2 now reports input/retained contact rows for the four core SocioPatterns-style empirical datasets.
- Table S1 now includes S28-S30 completed supplemental audits.
- Table S4 records only the completed S28-S30 supplementary robustness and mechanism audits.
- Machine-readable completed-audit records updated: `experiment_specs/completed_supplemental_audits_s28_s30.csv` and `experiment_specs/completed_supplemental_audits_s28_s30.json`.
- Cell-level inference summary added: `source_data/cell_level_inference_summary.csv` reports paired bootstrap intervals and sign-permutation summaries across matched cells, including S29 clean mechanism-context controls.
- Figure-specific Source Data packages added: `source_data/source_data_packages/Source_Data_Fig_1.zip` through `Source_Data_Fig_5.zip`, plus `Source_Data_Supplementary_Figs_S20_S30.zip`; `source_data/source_data_package_manifest.csv` maps each package to its included files.
- Main figures restyled on 2026-09-16 with a unified Times-style serif system, restrained color palette, consistent line widths, point sizes, confidence intervals and grid treatment.
- Fig. 1 was redrawn on 2026-09-26 as a four-module mechanism figure with temporal hypergraph context, contextual exposure, cooperative role screening and a separate LaTeX-rendered operational-equation module.
- Fig. 2 uses dataset-by-return SCRS cells and a paired forest plot with score-shuffled SCRS marked as the edge-score claim boundary.
- Fig. 3 uses a mechanism-loss layout with shaded core-disruption and near-SCRS regions.
- Fig. 4 uses enlarged \(r\times\rho_0\) and \(r\times\mu\) phase diagrams, a null-model dot-CI forest and a topology-size stress heatmap; heatmaps use a unified `cividis` colorblind-friendly colormap with contrast-aware cell labels.
- Fig. 5 uses grouped external-dataset forests, payoff/update paired dot-CI summaries and mutation-noise uncertainty ribbons.
- Main figure legends were shortened; detailed CSV paths are retained in the Source Data manifest rather than in the primary captions.
- Main-figure outputs are available as SVG, PDF and PNG.
- Supplementary S20-S30 overview outputs are available as SVG, PDF and PNG.

## Experiment Provenance

- Manuscript preparation used completed S20-S30 source tables.
- S28 construction sensitivity completed 45,000 matched trials with QA pass: 45,000 rows, 900 variant cells, 50 reps per cell and duplicate_keys=0.
- S29 clean mechanism-context controls completed 6,300 matched trials with QA pass: 6,300 rows, 126 variant cells, 50 reps per cell and duplicate_keys=0.
- S30 structure-stratified moderator audit completed as deterministic post-processing: 324 cell rows, 1,710 gap rows, 294 structure-stratum rows and 120 moderator-summary rows.
- Original S20-S27 output directories were not modified.
