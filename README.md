# SCRS temporal-hypergraph public-goods-game code release

This repository contains the code and manuscript-generation materials for:

**Cooperative role screening stabilizes cooperation in temporal hypergraph public goods games**

Release tag: `v0.1-nc-submission`

## Contents

- `experiments/`: formal simulation drivers for the main validation experiments and supplemental audits S20-S30.
- `paper_nc_submission/scripts/`: source-data, figure, reference-checking and LaTeX package generation scripts.
- `paper_nc_submission/figures/`: generated main and supplementary figures in vector and preview formats.
- `paper_nc_submission/tables/`: supplementary tables and table manifest.
- `paper_nc_submission/source_data/`: source-data manifests and checksum records. The full Source Data archive is deposited separately as the data DOI package.
- `paper_nc_submission/manuscript.md`: current manuscript source text.
- `paper_nc_submission/environment.yml` and `paper_nc_submission/requirements.txt`: software environment records.

## Data Separation

The full Source Data package is not duplicated in this code release. It is prepared as:

`SCRS_NC_source_data_20261013.zip`

with SHA256:

`ea5c61c021dddc116ce40242c579b74b572f4f337259644e7d26b31c72746669`

This separation keeps the code repository lightweight while allowing the data archive to receive its own Zenodo, Figshare or OSF DOI.

## Regenerating Figures and Manuscript Files

From the repository root, create the recorded environment and run:

```bash
python paper_nc_submission/scripts/make_paper_source_data.py
python paper_nc_submission/scripts/replot_fig1_scrs_mechanism_nc.py
python paper_nc_submission/scripts/replot_figures_2_to_5_nc.py
python paper_nc_submission/scripts/plot_s28_s30_supplementary.py
python paper_nc_submission/scripts/build_latex_package.py --stamp reproducibility
```

The formal experiment drivers in `experiments/` reproduce the simulation summaries when supplied with the raw empirical inputs and matched random seeds documented in the separate Source Data archive.

## Claim Boundary

The supported stabilizing component is cooperative role screening. Successful-group context is treated as an effective temporal-hypergraph exposure layer rather than an independently necessary driver under all tested regimes.
