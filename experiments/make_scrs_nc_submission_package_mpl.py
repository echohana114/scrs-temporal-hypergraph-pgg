#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd


DEFAULT_ROOT = Path(
    "/Users/hui/Documents/New project 2/temporal_hypergraph_pgg_pilot/"
    "supplemental_lfds_runs/s20_scrs_formal_nc_validation_20260824_2037"
)

CASE_ORDER = [
    "synthetic_structured_ring",
    "synthetic_community",
    "real_highschool2013",
    "real_workplace2013",
    "real_hospitalward2010",
    "real_sfhh2009",
]

REAL_CASES = [
    "real_highschool2013",
    "real_workplace2013",
    "real_hospitalward2010",
    "real_sfhh2009",
]

CASE_LABELS = {
    "synthetic_structured_ring": "Structured\nring",
    "synthetic_community": "Community\nsynthetic",
    "real_highschool2013": "High school\n2013",
    "real_workplace2013": "Workplace\n2013",
    "real_hospitalward2010": "Hospital ward\n2010",
    "real_sfhh2009": "SFHH\n2009",
}

CONTROL_LABELS = {
    "pnas": "PNAS",
    "csgc_gamma1": "CSGC",
    "csgc_gamma1_shuffled": "CSGC score\nshuffled",
    "scrs_gamma1_strategy_shuffled": "SCRS strategy\nshuffled",
    "scrs_gamma1_score_shuffled": "SCRS score\nshuffled",
}

COLORS = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "pink": "#CC79A7",
    "red": "#D55E00",
    "gray": "#6F6F6F",
    "light_gray": "#D9D9D9",
}


def configure_matplotlib(cache_dir: Path):
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache_dir))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 8,
            "axes.labelsize": 8,
            "axes.titlesize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    return plt, LinearSegmentedColormap


def fmt(value: float, digits: int = 4) -> str:
    return f"{float(value):.{digits}f}"


def latex_escape(value: object) -> str:
    text = str(value)
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("$", "\\$")
        .replace("#", "\\#")
        .replace("_", "\\_")
        .replace("{", "\\{")
        .replace("}", "\\}")
    )


def label_case(case: str) -> str:
    return CASE_LABELS.get(case, case.replace("_", " "))


def save_figure(fig, figure_dir: Path, stem: str) -> None:
    fig.savefig(figure_dir / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(figure_dir / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(figure_dir / f"{stem}.png", dpi=600, bbox_inches="tight")


def make_fig1_stability(plt, cell: pd.DataFrame, figure_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.3, 3.6))
    r_values = [0.7, 0.9, 1.0]
    colors = [COLORS["blue"], COLORS["orange"], COLORS["green"]]
    offsets = [-0.22, 0.0, 0.22]
    x_positions = list(range(len(CASE_ORDER)))
    lookup = cell.set_index(["case", "r"])

    for r, color, dx in zip(r_values, colors, offsets):
        means = [float(lookup.loc[(case, r), "scrs"]) for case in CASE_ORDER]
        lows = [float(lookup.loc[(case, r), "scrs_ci95_low"]) for case in CASE_ORDER]
        highs = [float(lookup.loc[(case, r), "scrs_ci95_high"]) for case in CASE_ORDER]
        lower = [m - lo for m, lo in zip(means, lows)]
        upper = [hi - m for m, hi in zip(means, highs)]
        xs = [x + dx for x in x_positions]
        ax.errorbar(
            xs,
            means,
            yerr=[lower, upper],
            fmt="o",
            color=color,
            ecolor=color,
            elinewidth=0.9,
            capsize=2.5,
            markersize=3.5,
            label=f"r={r:.1f}",
        )

    ax.axhline(0.60, color=COLORS["red"], linestyle="--", linewidth=0.8)
    ax.axhline(0.95, color=COLORS["gray"], linestyle=":", linewidth=0.8)
    ax.text(-0.45, 0.615, "empirical threshold", color=COLORS["red"], ha="left", va="bottom", fontsize=7)
    ax.text(len(CASE_ORDER) - 0.55, 0.965, "synthetic threshold", color=COLORS["gray"], ha="right", va="bottom", fontsize=7)
    ax.axvline(1.5, color=COLORS["light_gray"], linestyle="-", linewidth=0.8)
    ax.set_xticks(x_positions)
    ax.set_xticklabels([label_case(case) for case in CASE_ORDER])
    ax.set_ylim(0, 1.06)
    ax.set_ylabel("Tail cooperation")
    ax.set_title("SCRS stability across formal cells", loc="left", fontweight="bold")
    ax.grid(axis="y", color="#EDEDED", linewidth=0.7)
    ax.legend(ncols=3, frameon=False, loc="lower right")
    ax.text(0.5, -0.30, "Synthetic", transform=ax.get_xaxis_transform(), ha="center", va="top", color=COLORS["gray"])
    ax.text(3.5, -0.30, "Empirical", transform=ax.get_xaxis_transform(), ha="center", va="top", color=COLORS["gray"])
    save_figure(fig, figure_dir, "fig1_scrs_stability_by_case")
    plt.close(fig)


def make_fig2_gaps(plt, source: pd.DataFrame, cell: pd.DataFrame, figure_dir: Path, data_dir: Path) -> None:
    lfds = cell.groupby("source")["gap_vs_lfds_strongest"].mean().to_dict()
    rows = []
    for row in source.itertuples(index=False):
        rows.extend(
            [
                [row.source, "PNAS", float(row.mean_gap_vs_pnas)],
                [row.source, "CSGC", float(row.mean_gap_vs_csgc)],
                [row.source, "LFDS strongest", float(lfds[row.source])],
                [row.source, "Strategy shuffled", float(row.mean_gap_vs_strategy_shuffled)],
                [row.source, "Score shuffled", float(row.mean_gap_vs_score_shuffled)],
                [row.source, "Strict strongest", float(row.mean_gap_vs_strongest)],
            ]
        )
    gap_df = pd.DataFrame(rows, columns=["source", "comparison", "gap"])
    gap_df.to_csv(data_dir / "figure2_source_gap_values.csv", index=False)

    fig, ax = plt.subplots(figsize=(7.3, 3.6))
    comparisons = ["PNAS", "CSGC", "LFDS strongest", "Strategy shuffled", "Score shuffled", "Strict strongest"]
    x = list(range(len(comparisons)))
    width = 0.34
    for source_name, dx, color, label in [
        ("real", -width / 2, COLORS["blue"], "Empirical"),
        ("synthetic", width / 2, COLORS["pink"], "Synthetic"),
    ]:
        values = [
            float(gap_df[(gap_df["source"] == source_name) & (gap_df["comparison"] == comp)]["gap"].iloc[0])
            for comp in comparisons
        ]
        ax.bar([i + dx for i in x], values, width=width, color=color, label=label)
        for i, value in enumerate(values):
            y = value + (0.014 if value >= 0 else -0.014)
            ax.text(i + dx, y, f"{value:.3f}", ha="center", va="bottom" if value >= 0 else "top", fontsize=6)
    ax.axhline(0, color="#222222", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(["PNAS", "CSGC", "LFDS\nstrongest", "Strategy\nshuffled", "Score\nshuffled", "Strict\nstrongest"])
    ax.set_ylabel("Mean SCRS gap")
    ax.set_ylim(-0.06, 0.75)
    ax.set_title("Performance gains and mechanism boundary", loc="left", fontweight="bold")
    ax.grid(axis="y", color="#EDEDED", linewidth=0.7)
    ax.legend(frameon=False, loc="upper right")
    save_figure(fig, figure_dir, "fig2_performance_mechanism_gaps")
    plt.close(fig)


def annotate_heatmap(ax, values, fmt_text: str) -> None:
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, format(values[i, j], fmt_text), ha="center", va="center", fontsize=7)


def make_fig3_mechanism_heatmaps(plt, cmap_factory, cell: pd.DataFrame, figure_dir: Path) -> None:
    lookup = cell.set_index(["case", "r"])
    r_values = [0.7, 0.9, 1.0]
    role = pd.DataFrame(
        [[float(lookup.loc[(case, r), "gap_vs_scrs_strategy_shuffled"]) for r in r_values] for case in REAL_CASES],
        index=[label_case(case).replace("\n", " ") for case in REAL_CASES],
        columns=[f"r={r:.1f}" for r in r_values],
    )
    score = pd.DataFrame(
        [[float(lookup.loc[(case, r), "gap_vs_scrs_score_shuffled"]) for r in r_values] for case in REAL_CASES],
        index=role.index,
        columns=role.columns,
    )
    role_cmap = cmap_factory.from_list("role_cmap", ["#EEF7F1", COLORS["green"]])
    score_cmap = cmap_factory.from_list("score_cmap", [COLORS["blue"], "#F7F7F7", COLORS["red"]])

    fig, axes = plt.subplots(1, 2, figsize=(7.3, 3.2), gridspec_kw={"wspace": 0.34})
    im0 = axes[0].imshow(role.values, cmap=role_cmap, vmin=0, vmax=1.0, aspect="auto")
    axes[0].set_title("A  Role-screening signal", loc="left", fontweight="bold")
    axes[0].set_xticks(range(len(r_values)), role.columns)
    axes[0].set_yticks(range(len(role.index)), role.index)
    annotate_heatmap(axes[0], role.values, "+.3f")
    fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.03)

    im1 = axes[1].imshow(score.values, cmap=score_cmap, vmin=-0.025, vmax=0.025, aspect="auto")
    axes[1].set_title("B  Edge-score contribution", loc="left", fontweight="bold")
    axes[1].set_xticks(range(len(r_values)), score.columns)
    axes[1].set_yticks(range(len(score.index)), [""] * len(score.index))
    annotate_heatmap(axes[1], score.values, "+.3f")
    fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.03)

    for ax in axes:
        ax.tick_params(length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
    save_figure(fig, figure_dir, "fig3_empirical_mechanism_heatmaps")
    plt.close(fig)


def make_figs1_strict_heatmap(plt, cmap_factory, cell: pd.DataFrame, figure_dir: Path) -> None:
    lookup = cell.set_index(["case", "r"])
    r_values = [0.7, 0.9, 1.0]
    values = pd.DataFrame(
        [[float(lookup.loc[(case, r), "gap_vs_strongest"]) for r in r_values] for case in CASE_ORDER],
        index=[label_case(case).replace("\n", " ") for case in CASE_ORDER],
        columns=[f"r={r:.1f}" for r in r_values],
    )
    cmap = cmap_factory.from_list("strict_cmap", [COLORS["blue"], "#F7F7F7", COLORS["red"]])
    fig, ax = plt.subplots(figsize=(4.6, 3.9))
    im = ax.imshow(values.values, cmap=cmap, vmin=-0.025, vmax=0.025, aspect="auto")
    ax.set_title("Gap against strongest strict control", loc="left", fontweight="bold")
    ax.set_xticks(range(len(r_values)), values.columns)
    ax.set_yticks(range(len(values.index)), values.index)
    annotate_heatmap(ax, values.values, "+.4f")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    save_figure(fig, figure_dir, "figS1_strict_control_gap_heatmap")
    plt.close(fig)


def markdown_table(df: pd.DataFrame) -> str:
    lines = [
        "| " + " | ".join(df.columns) + " |",
        "| " + " | ".join(["---"] * len(df.columns)) + " |",
    ]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines) + "\n"


def latex_table(df: pd.DataFrame, caption: str, label: str) -> str:
    col_spec = "l" + "r" * (len(df.columns) - 1)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        f"\\caption{{{latex_escape(caption)}}}",
        f"\\label{{{latex_escape(label)}}}",
        f"\\begin{{tabular}}{{{col_spec}}}",
        "\\toprule",
        " & ".join(latex_escape(c) for c in df.columns) + " \\\\",
        "\\midrule",
    ]
    for row in df.itertuples(index=False):
        lines.append(" & ".join(latex_escape(x) for x in row) + " \\\\")
    lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
    return "\n".join(lines)


def write_tables(source: pd.DataFrame, case: pd.DataFrame, mechanism: pd.DataFrame, cell: pd.DataFrame, table_dir: Path) -> None:
    scale = pd.DataFrame(
        [
            ["Steps per trial", "5000"],
            ["Repetitions per cell", "50"],
            ["Tail window", "1000"],
            ["r values", "0.70, 0.90, 1.00"],
            ["Datasets", "2 synthetic; 4 empirical"],
            ["Variants", "16"],
            ["Total trials", "14400"],
        ],
        columns=["Item", "Value"],
    )
    source_table = pd.DataFrame(
        {
            "Source": source["source"].map({"real": "Empirical", "synthetic": "Synthetic"}),
            "SCRS mean": source["mean_scrs"].map(fmt),
            "SCRS min": source["min_scrs"].map(fmt),
            "Max SE": source["max_scrs_se"].map(fmt),
            "Gap vs PNAS": source["mean_gap_vs_pnas"].map(fmt),
            "Gap vs CSGC": source["mean_gap_vs_csgc"].map(fmt),
            "Gap vs strategy shuffled": source["mean_gap_vs_strategy_shuffled"].map(fmt),
            "Gap vs score shuffled": source["mean_gap_vs_score_shuffled"].map(fmt),
            "Strict wins": source.apply(lambda r: f"{int(r.strict_wins)}/{int(r.cells)}", axis=1),
        }
    )
    case_table = pd.DataFrame(
        {
            "Dataset": case["case"].map(lambda x: label_case(x).replace("\n", " ")),
            "Source": case["source"].map({"real": "Empirical", "synthetic": "Synthetic"}),
            "SCRS mean": case["mean_scrs"].map(fmt),
            "SCRS min": case["min_scrs"].map(fmt),
            "Max SE": case["max_scrs_se"].map(fmt),
            "Gap vs strategy shuffled": case["mean_gap_vs_strategy_shuffled"].map(fmt),
            "Gap vs score shuffled": case["mean_gap_vs_score_shuffled"].map(fmt),
            "Strict wins": case.apply(lambda r: f"{int(r.strict_wins)}/{int(r.cells)}", axis=1),
        }
    )
    mechanism_table = pd.DataFrame(
        {
            "Source": mechanism["source"].map({"real": "Empirical", "synthetic": "Synthetic"}),
            "Comparison": mechanism["control"].map(CONTROL_LABELS).fillna(mechanism["control"]).str.replace("\n", " ", regex=False),
            "Positive gaps": mechanism.apply(lambda r: f"{int(r.positive_gaps)}/{int(r.cells)}", axis=1),
            "CI-positive gaps": mechanism.apply(lambda r: f"{int(r.ci_positive_gaps)}/{int(r.cells)}", axis=1),
            "Mean gap": mechanism["mean_gap"].map(fmt),
            "Minimum gap": mechanism["min_gap"].map(fmt),
        }
    )
    strict_table = pd.DataFrame(
        {
            "Dataset": cell["case"].map(lambda x: label_case(x).replace("\n", " ")),
            "r": cell["r"].map(lambda x: f"{x:.1f}"),
            "SCRS": cell["scrs"].map(fmt),
            "Strongest control": cell["strongest_control"].map(lambda x: x.replace("_", " ")),
            "Control tail": cell["strongest_control_tail"].map(fmt),
            "Gap": cell["gap_vs_strongest"].map(fmt),
            "Gap 95% CI": cell.apply(lambda r: f"[{fmt(r.gap_vs_strongest_ci95_low)}, {fmt(r.gap_vs_strongest_ci95_high)}]", axis=1),
        }
    )

    tables = [
        ("table1_experimental_scale", scale, "Formal SCRS validation scale."),
        ("table2_source_level_summary", source_table, "Source-level SCRS performance and mechanism summary."),
        ("table3_case_level_summary", case_table, "Dataset-level SCRS stability and mechanism separation."),
        ("table4_mechanism_comparisons", mechanism_table, "Mechanism comparisons against key controls."),
        ("table5_strict_cell_summary", strict_table, "Cell-level comparison with the strongest strict control."),
    ]
    for stem, table, caption in tables:
        table.to_csv(table_dir / f"{stem}.csv", index=False)
        (table_dir / f"{stem}.md").write_text(markdown_table(table), encoding="utf-8")
        (table_dir / f"{stem}.tex").write_text(latex_table(table, caption, f"tab:{stem}"), encoding="utf-8")


def write_text(source: pd.DataFrame, mechanism: pd.DataFrame, root: Path, package_dir: Path) -> None:
    real = source[source["source"] == "real"].iloc[0]
    synthetic = source[source["source"] == "synthetic"].iloc[0]
    role_real = mechanism[(mechanism["source"] == "real") & (mechanism["control"] == "scrs_gamma1_strategy_shuffled")].iloc[0]
    role_synthetic = mechanism[(mechanism["source"] == "synthetic") & (mechanism["control"] == "scrs_gamma1_strategy_shuffled")].iloc[0]
    score_real = mechanism[(mechanism["source"] == "real") & (mechanism["control"] == "scrs_gamma1_score_shuffled")].iloc[0]
    score_synthetic = mechanism[(mechanism["source"] == "synthetic") & (mechanism["control"] == "scrs_gamma1_score_shuffled")].iloc[0]
    text = f"""# NC-Ready SCRS Results Text

## Results Draft

We evaluated Success-Conditioned Role Selection (SCRS) on two synthetic temporal hypergraphs and four empirical temporal contact datasets under a formal validation scale of 5000 update steps, 50 repetitions per condition, and three enhancement factors. SCRS maintained high cooperation across all tested conditions. Across the empirical datasets, mean tail cooperation reached {fmt(real.mean_scrs)} and the weakest empirical cell remained at {fmt(real.min_scrs)}, with a maximum standard error of {fmt(real.max_scrs_se)}. Across the synthetic cases, SCRS reached full cooperation in every tested cell.

SCRS exceeded the two main performance baselines. The mean empirical gap was {fmt(real.mean_gap_vs_pnas)} against PNAS-style imitation and {fmt(real.mean_gap_vs_csgc)} against cooperative-success group selection. The synthetic results showed the same direction, with mean gaps of {fmt(synthetic.mean_gap_vs_pnas)} and {fmt(synthetic.mean_gap_vs_csgc)}. These results support a performance claim: SCRS is stable on both empirical and synthetic temporal hypergraphs at the formal scale used here.

The mechanism tests identify successful-cooperator role screening as the main active component. When the strategy labels used for role screening were shuffled, SCRS retained a mean empirical advantage of {fmt(role_real.mean_gap)} and a synthetic advantage of {fmt(role_synthetic.mean_gap)}. All empirical case-r cells favored SCRS over the strategy-shuffled ablation, and all empirical cell-level approximate 95% confidence intervals remained above zero.

The edge-score component needs a narrower claim. SCRS and score-shuffled SCRS were nearly tied, with a mean empirical gap of {fmt(score_real.mean_gap)} and a synthetic gap of {fmt(score_synthetic.mean_gap)}. No source-level score-shuffled comparison produced cell-level CI support for an independent SCRS advantage. The safest NC framing is therefore that SCRS achieves robust cooperation through success-conditioned role-model selection, while score-based group selection acts as a contextual layer rather than the primary driver.

## Claim Boundary

- Safe claim: SCRS is formally stable across the tested empirical and synthetic temporal hypergraphs.
- Safe claim: successful-cooperator role screening is the dominant mechanism supported by the ablation results.
- Safe claim: SCRS strongly improves over PNAS and CSGC baselines.
- Cautious claim: SCRS is comparable to, not clearly better than, score-shuffled SCRS.
- Avoid: SCRS significantly beats every strict matched control.
- Avoid: edge-score group selection is the main independent mechanism.
"""
    captions = """# Figure Captions

**Figure 1 | SCRS stability across formal cells.** Tail cooperation is shown for SCRS after 5000 update steps. Points indicate means over 50 repetitions, and bars indicate approximate 95% confidence intervals. SCRS exceeds the empirical stability threshold in every empirical case-r cell and reaches full cooperation in all synthetic cells.

**Figure 2 | Performance gains and mechanism boundary.** Bars report the mean gap between SCRS and each comparison family. Positive values favor SCRS. Large gaps against PNAS, CSGC, LFDS strongest controls, and the strategy-shuffled ablation support SCRS performance and role-screening mechanism. Near-zero gaps against score-shuffled SCRS mark the boundary of the edge-score claim.

**Figure 3 | Mechanism separation in empirical data.** Heatmaps show cell-level SCRS gaps against the strategy-shuffled and score-shuffled SCRS ablations. Large positive role-screening gaps appear across all empirical datasets and r values, while score-shuffled gaps stay close to zero.

**Supplementary Fig. 1 | Gap against strongest strict control.** Cell-level gaps compare SCRS with the strongest matched control in each dataset and r value. Positive values favor SCRS. Near-zero values reflect the close match between SCRS and score-shuffled SCRS.
"""
    claim_boundary = pd.DataFrame(
        [
            ["Performance stability", "Supported", f"Empirical mean={fmt(real.mean_scrs)}; empirical min={fmt(real.min_scrs)}; synthetic cells=1.0000."],
            ["Improvement over PNAS/CSGC", "Supported", f"Empirical gaps: PNAS={fmt(real.mean_gap_vs_pnas)}, CSGC={fmt(real.mean_gap_vs_csgc)}."],
            ["Successful-cooperator role screening", "Supported", f"Gap vs strategy-shuffled SCRS: empirical={fmt(role_real.mean_gap)}, synthetic={fmt(role_synthetic.mean_gap)}."],
            ["Edge-score selection as main driver", "Limited", f"Gap vs score-shuffled SCRS: empirical={fmt(score_real.mean_gap)}, synthetic={fmt(score_synthetic.mean_gap)}."],
            ["Beats every strict matched control", "Not supported as a strong claim", f"Strict wins: empirical {int(real.strict_wins)}/{int(real.cells)}, synthetic {int(synthetic.strict_wins)}/{int(synthetic.cells)}."],
        ],
        columns=["Claim", "Status", "Evidence"],
    )
    readme = f"""# SCRS NC Submission Package

Created: {datetime.now().isoformat(timespec='seconds')}

Source experiment:

`{root}`

This package converts the completed s20 formal SCRS validation into submission-facing figures, tables, and claim text. It does not modify the original raw results.

Main decision:

- Performance: pass.
- Role-screening mechanism: pass.
- Edge-score independent mechanism: limited.
"""
    text_dir = package_dir / "text"
    (text_dir / "nc_ready_results_text.md").write_text(text, encoding="utf-8")
    (text_dir / "figure_captions.md").write_text(captions, encoding="utf-8")
    (text_dir / "README.md").write_text(readme, encoding="utf-8")
    claim_boundary.to_csv(text_dir / "claim_boundary_table.csv", index=False)
    (text_dir / "claim_boundary_table.md").write_text(markdown_table(claim_boundary), encoding="utf-8")


def copy_core_data(root: Path, data_dir: Path) -> None:
    for name in [
        "metadata.json",
        "status.json",
        "scrs_formal_source_summary.csv",
        "scrs_formal_case_summary.csv",
        "scrs_formal_cell_summary.csv",
        "scrs_formal_mechanism_summary.csv",
        "scrs_formal_pairwise_gaps.csv",
        "summary.csv",
    ]:
        shutil.copy2(root / name, data_dir / name)


def qa(root: Path, data_dir: Path) -> dict[str, object]:
    detail = pd.read_csv(root / "detail.csv")
    counts = detail.groupby(["case", "variant", "r"]).size()
    summary = {
        "rows": int(len(detail)),
        "duplicate_keys": int(detail.duplicated(["case", "variant", "r", "rep"]).sum()),
        "cells": int(len(counts)),
        "min_reps_per_cell": int(counts.min()),
        "max_reps_per_cell": int(counts.max()),
        "case_count": int(detail["case"].nunique()),
        "variant_count": int(detail["variant"].nunique()),
    }
    (data_dir / "qa_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def write_manifest(package_dir: Path, root: Path, qa_summary: dict[str, object]) -> None:
    manifest = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "source_experiment": str(root),
        "package_dir": str(package_dir),
        "qa": qa_summary,
        "files": sorted(str(path.relative_to(package_dir)) for path in package_dir.rglob("*") if path.is_file()),
    }
    (package_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser()
    package_dir = Path(args.out_dir).expanduser() if args.out_dir else root / f"nc_submission_package_mpl_{datetime.now().strftime('%Y%m%d_%H%M')}"
    if package_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing package: {package_dir}")

    figure_dir = package_dir / "figures"
    table_dir = package_dir / "tables"
    text_dir = package_dir / "text"
    data_dir = package_dir / "data"
    cache_dir = package_dir / ".mplconfig"
    for path in [figure_dir, table_dir, text_dir, data_dir, cache_dir]:
        path.mkdir(parents=True, exist_ok=False)

    plt, cmap_factory = configure_matplotlib(cache_dir)
    source = pd.read_csv(root / "scrs_formal_source_summary.csv")
    case = pd.read_csv(root / "scrs_formal_case_summary.csv")
    cell = pd.read_csv(root / "scrs_formal_cell_summary.csv")
    mechanism = pd.read_csv(root / "scrs_formal_mechanism_summary.csv")

    copy_core_data(root, data_dir)
    qa_summary = qa(root, data_dir)
    make_fig1_stability(plt, cell, figure_dir)
    make_fig2_gaps(plt, source, cell, figure_dir, data_dir)
    make_fig3_mechanism_heatmaps(plt, cmap_factory, cell, figure_dir)
    make_figs1_strict_heatmap(plt, cmap_factory, cell, figure_dir)
    write_tables(source, case, mechanism, cell, table_dir)
    write_text(source, mechanism, root, package_dir)
    write_manifest(package_dir, root, qa_summary)
    print(package_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create matplotlib-based NC SCRS submission package.")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="Completed SCRS formal output directory.")
    parser.add_argument("--out-dir", default="", help="New package directory. Must not exist.")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
