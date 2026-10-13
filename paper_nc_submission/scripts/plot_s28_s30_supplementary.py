from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper_nc_submission"
FIG_DIR = PAPER / "figures" / "supplementary"
S28 = ROOT / "supplemental_lfds_runs" / "s28_scrs_nc_construction_sensitivity_formal_20261010_195700"
S29 = ROOT / "supplemental_lfds_runs" / "s29_scrs_nc_mechanism_context_controls_formal_20261010_153000"
S30 = ROOT / "supplemental_lfds_runs" / "s30_scrs_nc_structure_moderator_formal_20261012_012352"

GREEN = "#2A9D8F"
BLUE = "#1565C0"
CORAL = "#E76F51"
GREY = "#5A5A5A"
LIGHT = "#E8EEF2"
DARK = "#111111"


def style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 7.8,
            "axes.labelsize": 7.8,
            "axes.titlesize": 8.6,
            "axes.titleweight": "bold",
            "xtick.labelsize": 6.9,
            "ytick.labelsize": 6.9,
            "legend.fontsize": 6.8,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.5,
            "ytick.major.width": 0.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.dpi": 300,
        }
    )


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.12,
        1.06,
        label,
        transform=ax.transAxes,
        fontsize=9.4,
        fontweight="bold",
        va="bottom",
        ha="left",
        color=DARK,
    )


def strip_axes(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", color="#DADADA", lw=0.35, alpha=0.8)


def save_all(fig: plt.Figure, stem: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "svg", "png"):
        fig.savefig(FIG_DIR / f"{stem}.{ext}", bbox_inches="tight")
    plt.close(fig)


def ci95(values: pd.Series) -> tuple[float, float, float]:
    arr = values.dropna().to_numpy(dtype=float)
    mean = float(arr.mean())
    if len(arr) <= 1:
        return mean, mean, mean
    se = float(arr.std(ddof=1) / np.sqrt(len(arr)))
    return mean, mean - 1.96 * se, mean + 1.96 * se


def condition_family(condition: str) -> str:
    if "__baseline__" in condition:
        return "baseline"
    if "__construction_mode__" in condition:
        return "construction\nmode"
    if "__h_sensitivity__" in condition:
        return "edge size"
    if "__m_sensitivity__" in condition:
        return "edge count"
    if "__duration_sensitivity__" in condition:
        return "block\nduration"
    return "other"


def plot_s28() -> None:
    heat = pd.read_csv(S28 / "S28_construction_heatmap_source.csv")
    heat["family"] = heat["condition"].map(condition_family)
    heat["case_label"] = (
        heat["case"]
        .str.replace("real_", "", regex=False)
        .str.replace("external_", "ext_", regex=False)
        .str.replace("_", "\n", regex=False)
    )
    families = ["baseline", "construction\nmode", "edge size", "edge count", "block\nduration"]
    pivot = (
        heat.groupby(["case_label", "family"])["gap_vs_scrs_gamma1_strategy_shuffled"]
        .mean()
        .unstack()
        .reindex(columns=families)
    )

    gaps = pd.read_csv(S28 / "S28_paired_gap_summary.csv")
    control_labels = {
        "pnas": "Wang imitation",
        "csgc_gamma1": "CSGC",
        "scrs_gamma1_strategy_shuffled": "Strategy shuffled",
        "scrs_gamma1_score_shuffled": "Score shuffled",
    }
    rows = []
    for control, label in control_labels.items():
        vals = gaps.loc[gaps["control"] == control, "mean_gap"]
        rows.append((label, *ci95(vals), len(vals)))
    forest = pd.DataFrame(rows, columns=["control", "mean", "low", "high", "cells"])

    fig, axes = plt.subplots(1, 2, figsize=(8.3, 3.9), gridspec_kw={"width_ratios": [1.30, 1.05], "wspace": 0.42})
    ax = axes[0]
    im = ax.imshow(pivot.values, aspect="auto", cmap="cividis", vmin=0, vmax=1)
    ax.set_xticks(np.arange(len(families)))
    ax.set_xticklabels(families, color=DARK)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels(pivot.index, color=DARK)
    ax.set_title("Construction slices", color=DARK, pad=5)
    ax.set_ylabel("Dataset")
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val = pivot.values[i, j]
            if np.isfinite(val):
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=6.3, color="white" if val > 0.5 else DARK)
    panel_label(ax, "a")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.035)
    cb.ax.set_title("gap", fontsize=6.9, pad=4, color=DARK)
    cb.ax.tick_params(labelsize=6.6, colors=DARK)

    ax = axes[1]
    y = np.arange(len(forest))
    colors = [BLUE, BLUE, CORAL, GREY]
    ax.axvline(0, color="#777777", ls="--", lw=0.7)
    ax.axhspan(2.5, 3.5, color="#F0F0F0", zorder=0)
    for yi, row, color in zip(y, forest.itertuples(), colors):
        ax.errorbar(row.mean, yi, xerr=[[row.mean - row.low], [row.high - row.mean]], fmt="o", color=color, ecolor=color, capsize=2, ms=4, lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels(forest["control"], color=DARK)
    ax.invert_yaxis()
    ax.set_xlabel("Mean paired gap")
    ax.set_title("All construction cells", color=DARK, pad=5)
    strip_axes(ax)
    panel_label(ax, "b")
    save_all(fig, "sfig_s28_construction_sensitivity")


def plot_s29() -> None:
    gaps = pd.read_csv(S29 / "S29_paired_gap_summary.csv")
    label_order = [
        ("scrs_gamma1_strategy_shuffled", "Strategy shuffled"),
        ("scrs_gamma1_success_without_score_ranking", "Successful edge,\nno score ranking"),
        ("scrs_gamma1_cooperator_only_uniform_incident", "Uniform incident\ncooperator-only"),
        ("scrs_gamma1_cooperator_only_random_neighborhood", "Random local\ncooperator-only"),
        ("scrs_gamma1_cooperator_only_random", "Random eligible\ncooperator"),
        ("scrs_gamma1_score_shuffled", "Score shuffled"),
    ]
    rows = []
    for control, label in label_order:
        vals = gaps.loc[gaps["control"] == control, "mean_gap"]
        rows.append((control, label, *ci95(vals), len(vals)))
    forest = pd.DataFrame(rows, columns=["control", "label", "mean", "low", "high", "cells"])

    audit = pd.read_csv(S29 / "S29_role_model_eligibility_audit.csv")
    audit_rows = []
    for control, label in label_order:
        variant = control.replace("scrs_gamma1_", "scrs_gamma1_", 1)
        vals = audit.loc[audit["variant"] == variant, "mean_role_model_cooperator_rate"]
        if len(vals):
            audit_rows.append((label, vals.mean(), vals.min(), vals.max()))
    audit_df = pd.DataFrame(audit_rows, columns=["label", "mean", "min", "max"])

    fig, axes = plt.subplots(1, 2, figsize=(8.3, 3.7), gridspec_kw={"width_ratios": [1.22, 1.0], "wspace": 0.52})
    ax = axes[0]
    y = np.arange(len(forest))
    ax.axvline(0, color="#777777", ls="--", lw=0.7)
    ax.axhspan(-0.5, 0.5, color="#FBE9E7", zorder=0)
    ax.axhspan(0.5, len(forest) - 0.5, color="#F4F6F7", zorder=0)
    for yi, row in zip(y, forest.itertuples()):
        color = CORAL if row.control == "scrs_gamma1_strategy_shuffled" else GREY
        ax.errorbar(row.mean, yi, xerr=[[row.mean - row.low], [row.high - row.mean]], fmt="o", color=color, ecolor=color, capsize=2, ms=4, lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels(forest["label"], color=DARK)
    ax.invert_yaxis()
    ax.set_xlabel("SCRS paired gap")
    ax.set_title("Clean mechanism-context controls", color=DARK, pad=5)
    strip_axes(ax)
    panel_label(ax, "a")

    ax = axes[1]
    y2 = np.arange(len(audit_df))
    ax.barh(y2, audit_df["mean"], color=GREEN, alpha=0.82, height=0.55)
    ax.errorbar(audit_df["mean"], y2, xerr=[audit_df["mean"] - audit_df["min"], audit_df["max"] - audit_df["mean"]], fmt="none", ecolor=DARK, lw=0.8, capsize=2)
    ax.set_yticks(y2)
    ax.set_yticklabels(audit_df["label"], color=DARK)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.12)
    ax.set_xlabel("Role-model cooperator rate")
    ax.set_title("Eligibility audit", color=DARK, pad=5)
    strip_axes(ax)
    panel_label(ax, "b")
    save_all(fig, "sfig_s29_clean_mechanism_context")


def plot_s30() -> None:
    strata = pd.read_csv(S30 / "S30_gap_by_structure_stratum.csv")
    controls = ["scrs_gamma1_strategy_shuffled", "scrs_gamma1_score_shuffled"]
    metrics = [
        ("temporal_memory_adjacent_jaccard", "Temporal memory"),
        ("hyperedge_overlap_within_block", "Within-block overlap"),
        ("activity_cv", "Activity CV"),
    ]
    rows = []
    for metric, label in metrics:
        for control in controls:
            sub = strata[(strata["structure_metric"] == metric) & (strata["control"] == control)]
            for stratum in ["low", "mid", "high"]:
                rec = sub[sub["structure_stratum"] == stratum]
                if not rec.empty:
                    rows.append((label, control, stratum, float(rec["mean_gap"].iloc[0]), float(rec["gap_ci95_low"].iloc[0]), float(rec["gap_ci95_high"].iloc[0])))
    df = pd.DataFrame(rows, columns=["metric", "control", "stratum", "gap", "low", "high"])

    fig, axes = plt.subplots(1, 3, figsize=(8.3, 3.3), sharey=True)
    fig.subplots_adjust(wspace=0.36)
    x = np.arange(3)
    stratum_order = ["low", "mid", "high"]
    for ax, (metric, label), lab in zip(axes, metrics, ["a", "b", "c"]):
        for control, color, offset, marker, name in [
            ("scrs_gamma1_strategy_shuffled", CORAL, -0.06, "o", "Strategy shuffled"),
            ("scrs_gamma1_score_shuffled", GREY, 0.06, "s", "Score shuffled"),
        ]:
            sub = df[(df["metric"] == label) & (df["control"] == control)].set_index("stratum").reindex(stratum_order)
            y = sub["gap"].to_numpy()
            lo = y - sub["low"].to_numpy()
            hi = sub["high"].to_numpy() - y
            ax.errorbar(x + offset, y, yerr=[lo, hi], color=color, marker=marker, lw=1.0, ms=4, capsize=2, label=name)
        ax.set_xticks(x)
        ax.set_xticklabels(["low", "mid", "high"], color=DARK)
        ax.set_title(label, color=DARK, pad=5)
        ax.set_xlabel("Structure stratum")
        ax.grid(axis="y", color="#DADADA", lw=0.35)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        panel_label(ax, lab)
    axes[0].set_ylabel("Mean paired gap")
    axes[0].legend(frameon=False, loc="upper left", bbox_to_anchor=(0.0, 1.02))
    save_all(fig, "sfig_s30_structure_moderator")


def main() -> None:
    style()
    plot_s28()
    plot_s29()
    plot_s30()


if __name__ == "__main__":
    main()
