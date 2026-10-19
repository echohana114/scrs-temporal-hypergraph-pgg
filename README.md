# SCRS temporal-hypergraph public-goods-game code

Code and manuscript-generation materials for:

**Cooperative role screening stabilizes cooperation in temporal hypergraph public goods games**

- Manuscript snapshot: tag `v0.1-nc-submission`
- Snapshot commit: `f567a2e0f802813c41483eb75e9f381e40fa6c06`
- Code archive: <https://doi.org/10.5281/zenodo.23330147>
- Source Data archive: <https://doi.org/10.5281/zenodo.23329520>

## Reproduce figures from a clean checkout

The commands below regenerate Figs. 1-5, Supplementary Figs. S28-S30 and the
LaTeX manuscript package from the deposited Source Data.

```bash
git clone https://github.com/echohana114/scrs-temporal-hypergraph-pgg.git
cd scrs-temporal-hypergraph-pgg

conda env create -f paper_nc_submission/environment.yml
conda activate scrs-nc
```

Download `SCRS_NC_source_data_20261013.zip` from the
[Source Data record](https://doi.org/10.5281/zenodo.23329520), place it in the
repository root, and verify its SHA256 checksum:

```bash
shasum -a 256 SCRS_NC_source_data_20261013.zip
# expected: ea5c61c021dddc116ce40242c579b74b572f4f337259644e7d26b31c72746669

unzip -o SCRS_NC_source_data_20261013.zip -d .
```

Regenerate the figures and LaTeX package:

```bash
export MPLCONFIGDIR="${TMPDIR:-/tmp}/scrs-matplotlib"
mkdir -p "$MPLCONFIGDIR"

python paper_nc_submission/scripts/replot_fig1_scrs_mechanism_nc.py
python paper_nc_submission/scripts/replot_figures_2_to_5_nc.py
python paper_nc_submission/scripts/plot_s28_s30_supplementary.py
python paper_nc_submission/scripts/build_latex_package.py --stamp reproducibility

cd paper_nc_submission/latex_exports/SCRS_NC_latex_latest_reproducibility
latexmk -pdf -interaction=nonstopmode main.tex
```

Expected outputs:

- `paper_nc_submission/figures/fig1_model_diagram.pdf`
- `paper_nc_submission/figures/fig2_main_performance.pdf`
- `paper_nc_submission/figures/fig3_mechanism_decomposition.pdf`
- `paper_nc_submission/figures/fig4_robustness_null_stress.pdf`
- `paper_nc_submission/figures/fig5_external_sensitivity_noise.pdf`
- `paper_nc_submission/figures/supplementary/sfig_s28_construction_sensitivity.pdf`
- `paper_nc_submission/figures/supplementary/sfig_s29_clean_mechanism_context.pdf`
- `paper_nc_submission/figures/supplementary/sfig_s30_structure_moderator.pdf`
- `paper_nc_submission/latex_exports/SCRS_NC_latex_latest_reproducibility/main.pdf`

PDF is the preferred vector output. EPS cannot preserve the transparent
uncertainty layers used in several figures.

## Exact archived tag

The public release tag remains the immutable manuscript snapshot. When checking
out `v0.1-nc-submission`, create the three compatibility links below before
running the S28-S30 plotting script; the tagged script records the original
formal-output directory names.

```bash
git checkout v0.1-nc-submission
mkdir -p supplemental_lfds_runs
ln -sfn "$PWD/paper_nc_submission/source_data/supplementary" \
  supplemental_lfds_runs/s28_scrs_nc_construction_sensitivity_formal_20261010_195700
ln -sfn "$PWD/paper_nc_submission/source_data/supplementary" \
  supplemental_lfds_runs/s29_scrs_nc_mechanism_context_controls_formal_20261010_153000
ln -sfn "$PWD/paper_nc_submission/source_data/supplementary" \
  supplemental_lfds_runs/s30_scrs_nc_structure_moderator_formal_20261012_012352
```

The default branch contains the equivalent automatic Source Data fallback, so
these links are unnecessary there.

## Formal simulations

The `experiments/` directory contains the formal drivers used for experiments
S20-S30. The deposited random-seed manifest records matched seeds for every
reported trial. Full simulation reruns additionally require the raw empirical
datasets from the cited SocioPatterns, Copenhagen Networks Study and Cornell
higher-order network repositories. These third-party inputs are not duplicated
in this code archive. The Source Data deposit contains the processed result
tables needed to verify every reported figure and statistical comparison.

## Repository contents

- `experiments/`: formal simulation drivers for S20-S30.
- `paper_nc_submission/scripts/`: figure, source-data, reference-checking and LaTeX builders.
- `paper_nc_submission/figures/`: vector figures and raster previews.
- `paper_nc_submission/tables/`: supplementary tables.
- `paper_nc_submission/source_data/`: manifests and checksums; populated fully after extracting the Source Data archive.
- `paper_nc_submission/environment.yml`: recorded Python environment.

## Claim boundary

The supported stabilizing component is cooperative role screening. Successful-
group context is an effective temporal-hypergraph exposure layer rather than an
independently necessary driver under all tested regimes.
