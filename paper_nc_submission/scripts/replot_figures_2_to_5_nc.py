#!/usr/bin/env python3
"""Replot Figures 2-5 with Nature Communications-style, data-faithful panels.

The script reads only deposited Source Data files. It intentionally avoids
mocking unsupported early trajectories, hyperedge-size distributions or
weak-selection theory curves when the corresponding source data are absent.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/mpl_scrs_nc_replot")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Circle, FancyBboxPatch, Polygon
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

try:
    import seaborn as sns
except Exception:  # pragma: no cover - optional dependency
    sns = None


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "source_data"
OUT = Path(os.environ.get("SCRS_NC_REPLOT_OUT", str(ROOT / "figures")))
FORMAT_ENV = os.environ.get("SCRS_NC_REPLOT_FORMATS")
OUTPUT_FORMATS = tuple(part.strip().lower() for part in FORMAT_ENV.split(",")) if FORMAT_ENV else (
    "pdf",
    "eps",
    "svg",
    "png",
)
STEM_SUFFIX = os.environ.get("SCRS_NC_REPLOT_SUFFIX", "")

EMPIRICAL = "#008080"
SYNTHETIC = "#CC6677"
SCRS = "#2E8B57"
WARNING = "#D62728"
ORANGE = "#FF7F0E"
CONTROL = "#5A5A5A"
LIGHT_CONTROL = "#D8DDE1"
SCORE_SHADE = "#F1F1F1"
GRID = "#E0E0E0"
TEXT = "#111111"

SOURCE_COLOR = {"real": EMPIRICAL, "synthetic": SYNTHETIC}
SOURCE_LABEL = {"real": "Empirical", "synthetic": "Synthetic"}

BASELINE_ORDER = [
    "pnas",
    "csgc_gamma1",
    "lfds_strongest",
    "scrs_gamma1_strategy_shuffled",
    "scrs_gamma1_score_shuffled",
]

BASELINE_LABEL = {
    "wang_temporal_hypergraph": "Wang imitation",
    "pnas": "Wang imitation",
    "csgc_gamma1": "CSGC",
    "lfds_strongest": "LFDS",
    "scrs_gamma1_strategy_shuffled": "Strategy-shuffled",
    "scrs_gamma1_score_shuffled": "Score-shuffled",
}

MECHANISM_ORDER = [
    "scrs_gamma1_strategy_shuffled",
    "scrs_gamma1_payoff_only_role",
    "scrs_gamma1_success_only_no_coop_filter",
    "scrs_gamma1_random_role_same_edge",
    "scrs_gamma1_cooperator_only_random",
    "scrs_gamma1_score_shuffled",
]

MECHANISM_LABEL = {
    "scrs_gamma1_strategy_shuffled": "Strategy shuffled",
    "scrs_gamma1_payoff_only_role": "Payoff-only role",
    "scrs_gamma1_success_only_no_coop_filter": "No C filter",
    "scrs_gamma1_random_role_same_edge": "Same-edge random role",
    "scrs_gamma1_cooperator_only_random": "Random C role",
    "scrs_gamma1_score_shuffled": "Score shuffled",
}

VARIANT_ORDER = [
    "scrs_gamma1",
    "scrs_gamma1_strategy_shuffled",
    "scrs_gamma1_success_only_no_coop_filter",
    "scrs_gamma1_payoff_only_role",
    "scrs_gamma1_random_role_same_edge",
    "scrs_gamma1_cooperator_only_random",
    "scrs_gamma1_score_shuffled",
]

VARIANT_LABEL = {
    "scrs_gamma1": "Full SCRS",
    "scrs_gamma1_strategy_shuffled": "Strategy shuffled",
    "scrs_gamma1_success_only_no_coop_filter": "No C filter",
    "scrs_gamma1_payoff_only_role": "Payoff-only role",
    "scrs_gamma1_random_role_same_edge": "Same-edge random role",
    "scrs_gamma1_cooperator_only_random": "Random C role",
    "scrs_gamma1_score_shuffled": "Score shuffled",
}


def setup_style() -> None:
    if sns is not None:
        sns.set_theme(style="whitegrid", context="paper")
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "axes.titlesize": 8.4,
            "axes.titleweight": "bold",
            "axes.labelsize": 7.4,
            "xtick.labelsize": 6.6,
            "ytick.labelsize": 6.6,
            "legend.fontsize": 6.5,
            "font.size": 7.4,
            "axes.linewidth": 0.55,
            "axes.edgecolor": TEXT,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.major.width": 0.5,
            "ytick.major.width": 0.5,
            "xtick.major.size": 2.2,
            "ytick.major.size": 2.2,
            "grid.color": GRID,
            "grid.linewidth": 0.30,
            "legend.frameon": False,
            "lines.linewidth": 1.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name, keep_default_na=False)


def mm_fig(width: float = 183, height: float = 140) -> tuple[float, float]:
    return width / 25.4, height / 25.4


def save_figure(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in OUTPUT_FORMATS:
        if not ext:
            continue
        dpi = 300 if ext in {"png", "tif", "tiff"} else None
        kwargs = {"bbox_inches": "tight", "facecolor": "white"}
        if dpi is not None:
            kwargs["dpi"] = dpi
        fig.savefig(OUT / f"{stem}.{ext}", **kwargs)
    plt.close(fig)


def panel_label(ax: plt.Axes, letter: str, title: str, *, y: float = 1.070) -> None:
    ax.text(-0.085, y, letter, transform=ax.transAxes, ha="left", va="bottom", fontsize=9.0, fontweight="bold", color=TEXT)
    ax.text(0.025, y, title, transform=ax.transAxes, ha="left", va="bottom", fontsize=8.3, fontweight="bold", color=TEXT)


def style_axis(ax: plt.Axes, grid_axis: str | None = "y") -> None:
    ax.set_axisbelow(True)
    ax.grid(False)
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, lw=0.30)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_linewidth(0.55)
        ax.spines[spine].set_color(TEXT)


def ci_from_series(values: pd.Series) -> tuple[float, float, float]:
    arr = pd.to_numeric(values, errors="coerce").dropna().to_numpy(dtype=float)
    if arr.size == 0:
        return np.nan, np.nan, np.nan
    mean = float(arr.mean())
    if arr.size == 1:
        return mean, mean, mean
    half = 1.96 * float(arr.std(ddof=1)) / np.sqrt(arr.size)
    return mean, mean - half, mean + half


def forest_point(
    ax: plt.Axes,
    x: float,
    lo: float,
    hi: float,
    y: float,
    color: str,
    marker: str = "o",
    label: str | None = None,
    zorder: int = 4,
    ms: float = 3.6,
) -> None:
    ax.errorbar(
        x,
        y,
        xerr=[[max(0.0, x - lo)], [max(0.0, hi - x)]],
        fmt=marker,
        ms=ms,
        mfc=color,
        mec="white",
        mew=0.30,
        lw=0.8,
        capsize=1.8,
        capthick=0.65,
        color=color,
        label=label,
        zorder=zorder,
    )


def annotate_heatmap(ax: plt.Axes, values: np.ndarray, fmt: str = ".2f", text_color: str | None = None) -> None:
    finite = values[np.isfinite(values)]
    threshold = float(np.nanmean(finite)) if finite.size else 0.5
    for row in range(values.shape[0]):
        for col in range(values.shape[1]):
            value = values[row, col]
            if np.isfinite(value):
                color = text_color or ("white" if value < threshold else TEXT)
                ax.text(col, row, format(value, fmt), ha="center", va="center", fontsize=6.1, color=color)


def ordered_pivot(
    data: pd.DataFrame,
    x: str,
    y: str,
    value: str,
    *,
    x_order: list | None = None,
    y_order: list | None = None,
) -> pd.DataFrame:
    table = data.pivot_table(index=y, columns=x, values=value, aggfunc="mean")
    if x_order is None:
        x_order = sorted(table.columns)
    if y_order is None:
        y_order = sorted(table.index)
    return table.reindex(index=y_order, columns=x_order)


def draw_heatmap(
    ax: plt.Axes,
    data: pd.DataFrame,
    x: str,
    y: str,
    value: str,
    *,
    cmap: str = "viridis",
    vmin: float | None = None,
    vmax: float | None = None,
    norm: object | None = None,
    cbar_label: str = "",
    contour_levels: list[float] | None = None,
    fmt: str = ".2f",
    x_order: list | None = None,
    y_order: list | None = None,
    xlabel: str | None = None,
    ylabel: str | None = None,
) -> None:
    table = ordered_pivot(data, x, y, value, x_order=x_order, y_order=y_order)
    arr = table.to_numpy(dtype=float)
    im = ax.imshow(arr, origin="upper", aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax, norm=norm)
    ax.set_xticks(np.arange(table.shape[1]), [str(v) for v in table.columns])
    ax.set_yticks(np.arange(table.shape[0]), [str(v) for v in table.index])
    ax.set_xlabel(xlabel if xlabel is not None else x)
    ax.set_ylabel(ylabel if ylabel is not None else y)
    annotate_heatmap(ax, arr, fmt=fmt)
    if contour_levels and np.isfinite(arr).any():
        levels = [level for level in contour_levels if np.nanmin(arr) < level < np.nanmax(arr)]
        if levels:
            xx, yy = np.meshgrid(np.arange(arr.shape[1]), np.arange(arr.shape[0]))
            ax.contour(
                xx,
                yy,
                arr,
                levels=levels,
                colors="white",
                linewidths=0.55,
                linestyles="dashed",
                alpha=0.92,
            )
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.045, pad=0.025)
    cbar.ax.tick_params(labelsize=6.4, width=0.45, length=2, colors=TEXT)
    cbar.outline.set_linewidth(0.45)
    if cbar_label:
        cbar.set_label(cbar_label, fontsize=7.0, labelpad=2.0, color=TEXT)
    style_axis(ax, grid_axis=None)


def parse_topology(label: str) -> str:
    cleaned = re.sub(r", n=\d+", "", str(label))
    return {
        "Temporal modular switching": "Temporal\nmodular",
        "Heterogeneous activity": "Heterogeneous\nactivity",
        "Structured ring": "Structured\nring",
        "Uniform random": "Uniform\nrandom",
    }.get(cleaned, cleaned)


def parse_n(label: str) -> int:
    found = re.search(r"n=(\d+)", str(label))
    return int(found.group(1)) if found else 0


def figure2() -> None:
    tails = read_csv("fig2a_s20_scrs_tail_by_case.csv")
    cells = read_csv("fig2b_s20_gap_cells_for_forest.csv")
    summary = read_csv("fig2b_s20_gap_forest_summary.csv")
    phase = read_csv("fig4a_s21_phase_r_rho0.csv")

    fig = plt.figure(figsize=mm_fig(183, 170))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.0, 1.12], hspace=0.92, wspace=0.54)
    letters = list("abcdef")
    real_datasets = ["High school 2013", "Hospital ward 2010", "SFHH 2009", "Workplace 2013"]

    for idx, dataset in enumerate(real_datasets):
        ax = fig.add_subplot(gs[idx // 2, idx % 2])
        panel_label(ax, letters[idx], dataset)
        sub = tails.loc[tails["dataset_label"] == dataset].sort_values("r")
        x = sub["r"].astype(float).to_numpy()
        y = sub["scrs"].astype(float).to_numpy()
        lo = sub["scrs_ci95_low"].astype(float).to_numpy()
        hi = sub["scrs_ci95_high"].astype(float).to_numpy()
        best = sub["strongest_control_tail"].astype(float).to_numpy()
        ax.fill_between(x, lo, hi, color=SCRS, alpha=0.22, lw=0)
        ax.plot(x, y, color=SCRS, marker="o", ms=3.2, label="SCRS")
        ax.plot(x, best, color=CONTROL, marker="s", ms=2.8, lw=0.9, ls=(0, (3, 2)), label="best control")
        for _, row in sub.iterrows():
            ax.text(row["r"], row["scrs"] + 0.026, f"{row['scrs']:.2f}", fontsize=6.5, ha="center", color=TEXT)
        ax.set_xlim(0.66, 1.04)
        ax.set_ylim(0.55, 1.03)
        ax.set_xticks([0.7, 0.9, 1.0], ["0.7", "0.9", "1.0"])
        ax.set_xlabel("per-member return r")
        ax.set_ylabel("tail cooperation")
        style_axis(ax, grid_axis="y")
        if idx == 0:
            ax.legend(loc="lower right", handlelength=1.4, handletextpad=0.3)

    ax = fig.add_subplot(gs[2, 0])
    panel_label(ax, "e", r"Initial-condition phase boundary")
    draw_heatmap(
        ax,
        phase.loc[phase["source"] == "real"].copy(),
        x="r",
        y="rho0",
        value="mean_scrs",
        cmap="viridis",
        vmin=0,
        vmax=1,
        cbar_label="SCRS tail cooperation",
        contour_levels=[0.5, 0.75, 0.9],
        xlabel="r",
        ylabel=r"initial $\rho_0$",
    )
    ax.text(
        0.60,
        0.80,
        r"$\rho_C=0.5$ contour",
        transform=ax.transAxes,
        fontsize=6.2,
        color=TEXT,
        ha="left",
        va="center",
        bbox={"boxstyle": "round,pad=0.16", "facecolor": "white", "edgecolor": "none", "alpha": 0.78},
    )

    ax = fig.add_subplot(gs[2, 1])
    panel_label(ax, "f", "Paired gaps against controls")
    y_pos = {key: i for i, key in enumerate(BASELINE_ORDER)}
    score_y = y_pos["scrs_gamma1_score_shuffled"]
    ax.axhspan(score_y - 0.46, score_y + 0.46, color=SCORE_SHADE, zorder=0)
    rng = np.random.default_rng(20261010)
    source_offset = {"real": -0.12, "synthetic": 0.12}
    for _, row in cells.iterrows():
        key = "pnas" if row["comparison_key"] == "wang_temporal_hypergraph" else row["comparison_key"]
        if key not in y_pos:
            continue
        y = y_pos[key] + source_offset.get(row["source"], 0.0) + rng.normal(0, 0.022)
        ax.scatter(row["gap"], y, s=10, color=SOURCE_COLOR.get(row["source"], CONTROL), alpha=0.30, lw=0, zorder=2)
    used_labels: set[str] = set()
    for _, row in summary.iterrows():
        key = "pnas" if row["comparison_key"] == "wang_temporal_hypergraph" else row["comparison_key"]
        if key not in y_pos:
            continue
        source = row["source"]
        label = SOURCE_LABEL.get(source) if source not in used_labels else None
        used_labels.add(source)
        forest_point(
            ax,
            row["mean_gap"],
            row["gap_ci95_low"],
            row["gap_ci95_high"],
            y_pos[key] + source_offset.get(source, 0.0),
            SOURCE_COLOR.get(source, CONTROL),
            marker="D",
            label=label,
            ms=3.6,
        )
    ax.axvline(0, color=TEXT, lw=0.65, ls=(0, (3, 2)))
    ax.text(0.04, score_y - 0.18, "score ordering\nnot decisive", color=TEXT, fontsize=6.7, ha="left", va="center")
    ax.set_yticks([y_pos[k] for k in BASELINE_ORDER], [BASELINE_LABEL[k] for k in BASELINE_ORDER])
    ax.invert_yaxis()
    ax.set_xlabel("paired gap (SCRS - control)")
    ax.set_xlim(-0.06, 0.92)
    style_axis(ax, grid_axis="x")
    ax.legend(loc="lower right", handletextpad=0.3)
    save_figure(fig, f"fig2_main_performance{STEM_SUFFIX}")


def _draw_violin_fallback(ax: plt.Axes, data: pd.DataFrame, labels: list[str]) -> None:
    arrays = [data.loc[data["variant_label"] == label, "tail_coop_mean"].astype(float).to_numpy() for label in labels]
    parts = ax.violinplot(arrays, positions=np.arange(len(labels)), vert=False, showmeans=False, showmedians=False)
    for body in parts["bodies"]:
        body.set_facecolor(LIGHT_CONTROL)
        body.set_edgecolor(CONTROL)
        body.set_alpha(0.85)
        body.set_linewidth(0.45)
    for key in ("cbars", "cmins", "cmaxes", "cmedians", "cmeans"):
        if key in parts:
            parts[key].set_color(CONTROL)
            parts[key].set_linewidth(0.45)
    ax.set_yticks(np.arange(len(labels)), labels)


def figure3() -> None:
    tails = read_csv("supplementary/s25_summary.csv")
    cells = read_csv("fig3_s25_mechanism_paired_gaps_by_cell.csv")
    summary = read_csv("fig3_s25_mechanism_mean_gaps.csv")

    tails = tails.loc[tails["variant"].isin(VARIANT_ORDER)].copy()
    tails["variant_label"] = tails["variant"].map(VARIANT_LABEL)
    label_order = [VARIANT_LABEL[v] for v in VARIANT_ORDER]
    palette = {
        "Full SCRS": SCRS,
        "Strategy shuffled": WARNING,
        "No C filter": WARNING,
        "Payoff-only role": ORANGE,
        "Same-edge random role": WARNING,
        "Random C role": CONTROL,
        "Score shuffled": CONTROL,
    }

    fig = plt.figure(figsize=mm_fig(183, 156))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.45, 1.02], height_ratios=[1.0, 0.95], wspace=0.66, hspace=0.70)
    ax = fig.add_subplot(gs[:, 0])
    panel_label(ax, "a", "Cell-level ablation distributions")
    if sns is not None:
        sns.violinplot(
            data=tails,
            y="variant_label",
            x="tail_coop_mean",
            order=label_order,
            orient="h",
            cut=0,
            inner=None,
            linewidth=0.55,
            palette=palette,
            saturation=0.85,
            ax=ax,
        )
        sns.stripplot(
            data=tails,
            y="variant_label",
            x="tail_coop_mean",
            order=label_order,
            orient="h",
            hue="source",
            palette=SOURCE_COLOR,
            dodge=False,
            jitter=0.18,
            size=2.2,
            alpha=0.42,
            linewidth=0,
            ax=ax,
        )
        if ax.legend_:
            ax.legend_.remove()
    else:
        _draw_violin_fallback(ax, tails, label_order)
        rng = np.random.default_rng(20261010)
        for y, label in enumerate(label_order):
            vals = tails.loc[tails["variant_label"] == label, "tail_coop_mean"].astype(float)
            ax.scatter(vals, y + rng.normal(0, 0.08, len(vals)), s=8, color=palette.get(label, CONTROL), alpha=0.45, lw=0)
    for y, label in enumerate(label_order):
        vals = tails.loc[tails["variant_label"] == label, "tail_coop_mean"]
        mean, lo, hi = ci_from_series(vals)
        if np.isfinite(mean):
            forest_point(ax, mean, lo, hi, y, TEXT if label == "Full SCRS" else palette.get(label, CONTROL), marker="D", ms=3.1)
    ax.axvline(0.5, color=TEXT, lw=0.55, ls=(0, (3, 2)))
    ax.set_xlim(0.0, 1.03)
    ax.set_xlabel("tail cooperation")
    ax.set_ylabel("")
    ax.invert_yaxis()
    style_axis(ax, grid_axis="x")

    ax = fig.add_subplot(gs[0, 1])
    panel_label(ax, "b", "Mechanism loss gaps")
    y_pos = {control: i for i, control in enumerate(MECHANISM_ORDER)}
    ax.axhspan(-0.5, 3.5, color="#FBEAEA", zorder=0)
    ax.axhspan(3.5, 5.5, color=SCORE_SHADE, zorder=0)
    rng = np.random.default_rng(20261010)
    source_offset = {"real": -0.12, "synthetic": 0.12}
    for _, row in cells.iterrows():
        control = row["control"]
        if control not in y_pos:
            continue
        y = y_pos[control] + source_offset.get(row["source"], 0.0) + rng.normal(0, 0.022)
        ax.scatter(row["mean_gap"], y, s=10, color=SOURCE_COLOR.get(row["source"], CONTROL), alpha=0.25, lw=0, zorder=2)
    used_labels: set[str] = set()
    for _, row in summary.iterrows():
        control = row["control"]
        if control not in y_pos:
            continue
        source = row["source"]
        color = WARNING if control in MECHANISM_ORDER[:4] else CONTROL
        label = SOURCE_LABEL.get(source) if source not in used_labels else None
        used_labels.add(source)
        half = 1.96 * float(row["mean_gap_se"])
        forest_point(
            ax,
            row["mean_gap"],
            row["mean_gap"] - half,
            row["mean_gap"] + half,
            y_pos[control] + source_offset.get(source, 0.0),
            color,
            marker="D" if source == "real" else "s",
            label=label,
            ms=3.1,
        )
    ax.axvline(0, color=TEXT, lw=0.60, ls=(0, (3, 2)))
    ax.text(0.73, 1.55, "role screen\ndisrupted", color=WARNING, fontsize=6.8, ha="center", va="center")
    ax.text(0.22, 4.85, "near SCRS", color=TEXT, fontsize=6.8, ha="center", va="center")
    ax.set_yticks([y_pos[k] for k in MECHANISM_ORDER], [MECHANISM_LABEL[k] for k in MECHANISM_ORDER])
    ax.invert_yaxis()
    ax.set_xlabel("paired gap")
    ax.set_xlim(-0.08, 1.02)
    style_axis(ax, grid_axis="x")

    ax = fig.add_subplot(gs[1, 1], projection="polar")
    panel_label(ax, "c", "Data-derived evidence profile", y=1.12)
    metric_cols = {
        "tail C": "tail_coop_mean",
        "early C": "tail_coop_mean_500",
        "cell floor": "tail_coop_mean",
        "role purity": "scrs_role_coop_rate",
        "selection lift": "csgc_selection_lift",
    }
    radar_variants = [
        "scrs_gamma1",
        "scrs_gamma1_strategy_shuffled",
        "scrs_gamma1_success_only_no_coop_filter",
        "scrs_gamma1_score_shuffled",
    ]
    metrics: dict[str, list[float]] = {}
    lift_max = max(float(tails["csgc_selection_lift"].astype(float).max()), 1e-9)
    for variant in radar_variants:
        sub = tails.loc[tails["variant"] == variant]
        values = []
        for name, col in metric_cols.items():
            series = pd.to_numeric(sub[col], errors="coerce").dropna()
            if name == "cell floor":
                value = float(series.min()) if len(series) else 0.0
            elif name == "selection lift":
                value = float(series.mean()) / lift_max if len(series) else 0.0
            else:
                value = float(series.mean()) if len(series) else 0.0
            values.append(max(0.0, min(1.0, value)))
        metrics[variant] = values
    labels = list(metric_cols.keys())
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]
    radar_colors = {
        "scrs_gamma1": SCRS,
        "scrs_gamma1_strategy_shuffled": WARNING,
        "scrs_gamma1_success_only_no_coop_filter": ORANGE,
        "scrs_gamma1_score_shuffled": CONTROL,
    }
    for variant in radar_variants:
        values = metrics[variant] + metrics[variant][:1]
        color = radar_colors[variant]
        ax.plot(angles, values, color=color, lw=1.0, label=VARIANT_LABEL[variant])
        ax.fill(angles, values, color=color, alpha=0.10)
    ax.set_xticks(angles[:-1], labels)
    ax.tick_params(axis="x", labelsize=6.2, pad=2)
    ax.set_yticks([0.5, 1.0], ["0.5", "1.0"])
    ax.set_ylim(0, 1.0)
    ax.grid(color=GRID, lw=0.30)
    ax.spines["polar"].set_color(LIGHT_CONTROL)
    ax.spines["polar"].set_linewidth(0.55)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, handlelength=1.2, columnspacing=0.9)
    save_figure(fig, f"fig3_mechanism_decomposition{STEM_SUFFIX}")


def draw_null_schematic(ax: plt.Axes) -> None:
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    titles = ["Orig.", "Block", "Deg.", "Act."]
    xs = [0.13, 0.38, 0.63, 0.87]
    for idx, (x0, title) in enumerate(zip(xs, titles)):
        box = FancyBboxPatch(
            (x0 - 0.105, 0.16),
            0.21,
            0.64,
            boxstyle="round,pad=0.01,rounding_size=0.02",
            facecolor="#FAFAFA",
            edgecolor=LIGHT_CONTROL,
            linewidth=0.55,
        )
        ax.add_patch(box)
        ax.text(x0, 0.83, title, ha="center", va="bottom", fontsize=5.9, fontweight="bold", color=TEXT, linespacing=0.9)
        rng = np.random.default_rng(100 + idx)
        pts = np.array(
            [
                [x0 - 0.055, 0.62],
                [x0 + 0.040, 0.66],
                [x0 + 0.065, 0.50],
                [x0 - 0.020, 0.40],
                [x0 - 0.070, 0.47],
            ]
        )
        if idx == 1:
            pts[:, 1] = pts[[2, 0, 4, 1, 3], 1]
        elif idx == 2:
            pts += rng.normal(0, 0.012, pts.shape)
        elif idx == 3:
            pts = pts[[0, 2, 4, 1, 3]]
        hull = Polygon(pts[[0, 1, 2, 3, 4]], closed=True, facecolor="#DCEBF7", edgecolor="#1565C0", alpha=0.40, lw=0.8)
        ax.add_patch(hull)
        for k in range(len(pts)):
            ax.plot([pts[k, 0], pts[(k + 2) % len(pts), 0]], [pts[k, 1], pts[(k + 2) % len(pts), 1]], color=LIGHT_CONTROL, lw=0.45)
        for p, color in zip(pts, [SCRS, CONTROL, SCRS, CONTROL, SCRS]):
            ax.add_patch(Circle((p[0], p[1]), 0.015, facecolor=color, edgecolor="white", linewidth=0.4))
        if idx < 3:
            ax.annotate("", xy=(x0 + 0.135, 0.48), xytext=(x0 + 0.112, 0.48), arrowprops=dict(arrowstyle="-|>", lw=0.55, color=CONTROL))


def figure4() -> None:
    mutation = read_csv("fig4b_s24_phase_r_mutation.csv")
    nulls = read_csv("fig4c_s22_real_nulls_gap_cells_long.csv")
    null_cells = read_csv("fig4b_s22_real_nulls_cell_summary.csv")
    stress = read_csv("fig4c_s23_synthetic_stress_case_summary.csv")

    fig = plt.figure(figsize=mm_fig(183, 162))
    gs = fig.add_gridspec(2, 3, height_ratios=[0.90, 1.0], wspace=0.86, hspace=0.78)

    ax = fig.add_subplot(gs[0, 0])
    panel_label(ax, "a", "Null-model operations", y=1.07)
    draw_null_schematic(ax)

    ax = fig.add_subplot(gs[0, 1])
    panel_label(ax, "b", "Gap change relative to original")
    null_label = {
        "block_order_shuffle": "Block\norder",
        "degree_preserving_rewire": "Degree\nrewire",
        "activity_preserving_resample": "Activity\nresample",
    }
    comp_label = {
        "pnas": "Wang",
        "csgc_gamma1": "CSGC",
        "scrs_gamma1_strategy_shuffled": "Strat.",
        "scrs_gamma1_score_shuffled": "Score",
    }
    mean_gap = nulls.groupby(["null_model", "comparison_key"], as_index=False)["gap"].mean()
    orig = mean_gap.loc[mean_gap["null_model"] == "original", ["comparison_key", "gap"]].rename(columns={"gap": "original_gap"})
    delta = mean_gap.merge(orig, on="comparison_key", how="left")
    delta = delta.loc[delta["null_model"] != "original"].copy()
    delta["delta_gap"] = delta["gap"] - delta["original_gap"]
    delta["null_short"] = delta["null_model"].map(null_label)
    delta["comparison_short"] = delta["comparison_key"].map(comp_label)
    vmax = max(0.01, float(np.nanmax(np.abs(delta["delta_gap"].astype(float)))))
    draw_heatmap(
        ax,
        delta,
        x="comparison_short",
        y="null_short",
        value="delta_gap",
        cmap="RdBu_r",
        norm=TwoSlopeNorm(vcenter=0, vmin=-vmax, vmax=vmax),
        cbar_label=r"$\Delta$ gap",
        fmt=".2f",
        x_order=[comp_label[k] for k in ["pnas", "csgc_gamma1", "scrs_gamma1_strategy_shuffled", "scrs_gamma1_score_shuffled"]],
        y_order=[null_label[k] for k in ["block_order_shuffle", "degree_preserving_rewire", "activity_preserving_resample"]],
        xlabel="control",
        ylabel="null model",
    )

    ax = fig.add_subplot(gs[0, 2])
    panel_label(ax, "c", "Null-model SCRS levels")
    null_cells = null_cells.copy()
    null_cells["null_short"] = null_cells["null_model"].map(
        {
            "original": "Original",
            "block_order_shuffle": "Block\norder",
            "degree_preserving_rewire": "Degree\nrewire",
            "activity_preserving_resample": "Activity\nresample",
        }
    )
    null_summary = null_cells.groupby(["null_short", "r"], as_index=False)["scrs"].mean()
    draw_heatmap(
        ax,
        null_summary,
        x="r",
        y="null_short",
        value="scrs",
        cmap="viridis",
        vmin=0,
        vmax=1,
        cbar_label="tail C",
        contour_levels=[0.75, 0.9],
        x_order=[0.7, 0.9, 1.0],
        y_order=["Original", "Block\norder", "Degree\nrewire", "Activity\nresample"],
        xlabel="r",
        ylabel="",
    )

    ax = fig.add_subplot(gs[1, 0])
    panel_label(ax, "d", "Mutation phase boundary")
    mut = mutation.loc[mutation["source"] == "real"].copy()
    mut["mutation_rate"] = mut["mutation_rate"].astype(float).map(lambda v: f"{v:g}")
    draw_heatmap(
        ax,
        mut,
        x="r",
        y="mutation_rate",
        value="mean_scrs",
        cmap="viridis",
        vmin=0,
        vmax=1,
        cbar_label="tail C",
        contour_levels=[0.5, 0.75],
        x_order=[0.7, 0.9, 1.0],
        y_order=["0", "0.001", "0.005", "0.01"],
        xlabel="r",
        ylabel=r"mutation $\mu$",
    )

    stress = stress.copy()
    stress["topology"] = stress["dataset_label"].map(parse_topology)
    stress["n"] = stress["dataset_label"].map(parse_n)
    topo_order = ["Heterogeneous\nactivity", "Temporal\nmodular", "Uniform\nrandom", "Community", "Structured\nring"]
    n_order = [100, 200, 400]

    ax = fig.add_subplot(gs[1, 1])
    panel_label(ax, "e", "Synthetic stress: cooperation")
    draw_heatmap(
        ax,
        stress,
        x="n",
        y="topology",
        value="mean_scrs",
        cmap="viridis",
        vmin=0.94,
        vmax=1.0,
        cbar_label="tail C",
        fmt=".3f",
        x_order=n_order,
        y_order=topo_order,
        xlabel="n",
        ylabel="",
    )

    ax = fig.add_subplot(gs[1, 2])
    panel_label(ax, "f", "Synthetic stress: role-screen gap")
    draw_heatmap(
        ax,
        stress,
        x="n",
        y="topology",
        value="mean_gap_vs_scrs_gamma1_strategy_shuffled",
        cmap="plasma",
        vmin=0,
        vmax=max(0.7, float(stress["mean_gap_vs_scrs_gamma1_strategy_shuffled"].astype(float).max())),
        cbar_label="gap",
        fmt=".2f",
        x_order=n_order,
        y_order=topo_order,
        xlabel="n",
        ylabel="",
    )
    save_figure(fig, f"fig4_robustness_null_stress{STEM_SUFFIX}")


def figure5() -> None:
    external_cases = read_csv("fig5a_s26_external_empirical_cases.csv")
    external_gaps = read_csv("fig5a_s26_external_paired_gaps_by_cell.csv")
    manifest = read_csv("fig5a_s26_external_dataset_manifest.csv")
    payoff = read_csv("fig5b_s27_payoff_update_paired_gaps_by_cell.csv")
    trajectory = read_csv("fig5c_s24_noise_horizon_trajectory_summary.csv")
    noise_cells = read_csv("fig5c_s24_noise_horizon_cell_summary.csv")

    fig = plt.figure(figsize=mm_fig(183, 164))
    gs = fig.add_gridspec(
        2,
        3,
        width_ratios=[1.08, 1.00, 1.06],
        height_ratios=[1.06, 1.0],
        wspace=1.05,
        hspace=0.82,
    )

    ax = fig.add_subplot(gs[0, 0])
    panel_label(ax, "a", "External dumbbell benchmark")
    cases = external_cases.copy()
    cases["strategy_control"] = cases["mean_scrs"].astype(float) - cases["mean_gap_vs_scrs_gamma1_strategy_shuffled"].astype(float)
    cases["wang_control"] = cases["mean_scrs"].astype(float) - cases["mean_gap_vs_pnas"].astype(float)
    cases = cases.sort_values("mean_scrs", ascending=True)
    y = np.arange(len(cases))
    for yi, (_, row) in zip(y, cases.iterrows()):
        ax.plot([row["strategy_control"], row["mean_scrs"]], [yi, yi], color=LIGHT_CONTROL, lw=1.45, zorder=1)
        ax.scatter(row["strategy_control"], yi, s=26, color=CONTROL, zorder=3)
        ax.scatter(row["wang_control"], yi + 0.11, s=22, facecolor="white", edgecolor=CONTROL, lw=0.75, zorder=3)
        ax.scatter(row["mean_scrs"], yi, s=34, color=SCRS, edgecolor="white", lw=0.40, zorder=4)
    ax.set_yticks(y, cases["dataset_label"])
    ax.set_xlim(0, 1.03)
    ax.set_xlabel("tail cooperation")
    ax.scatter([], [], s=26, color=CONTROL, label="strategy-shuffled")
    ax.scatter([], [], s=22, facecolor="white", edgecolor=CONTROL, label="Wang")
    ax.scatter([], [], s=34, color=SCRS, label="SCRS")
    ax.legend(loc="upper center", bbox_to_anchor=(0.52, -0.18), ncol=3, handletextpad=0.3, columnspacing=0.8)
    style_axis(ax, grid_axis="x")

    ax = fig.add_subplot(gs[0, 1])
    panel_label(ax, "b", "External paired gaps")
    data = external_gaps.loc[
        external_gaps["control"].isin(["scrs_gamma1_strategy_shuffled", "scrs_gamma1_score_shuffled"])
    ].copy()
    dataset_order = data["dataset_label"].drop_duplicates().tolist()
    short_dataset_label = {
        "Congress bills": "Congress",
        "Copenhagen Bluetooth": "Copenhagen",
        "Email-Enron": "Enron",
        "Email-EU": "Email-EU",
        "Ask Ubuntu threads": "Ask Ubuntu",
    }
    y_pos = {label: i for i, label in enumerate(dataset_order)}
    r_offset = {0.7: -0.18, 0.9: 0.0, 1.0: 0.18}
    ctrl_offset = {"scrs_gamma1_strategy_shuffled": -0.045, "scrs_gamma1_score_shuffled": 0.045}
    marker_by_r = {0.7: "o", 0.9: "s", 1.0: "^"}
    for _, row in data.iterrows():
        yv = y_pos[row["dataset_label"]] + r_offset[float(row["r"])] + ctrl_offset[row["control"]]
        color = EMPIRICAL if row["control"] == "scrs_gamma1_strategy_shuffled" else CONTROL
        forest_point(
            ax,
            row["mean_gap"],
            row["gap_ci95_low"],
            row["gap_ci95_high"],
            yv,
            color,
            marker=marker_by_r[float(row["r"])],
            ms=3.0,
        )
    for i in range(len(dataset_order)):
        ax.axhline(i + 0.5, color=GRID, lw=0.30, zorder=0)
    ax.axvline(0, color=TEXT, lw=0.60, ls=(0, (3, 2)))
    ax.set_yticks(
        list(y_pos.values()),
        [short_dataset_label.get(label, label) for label in dataset_order],
    )
    ax.invert_yaxis()
    ax.set_xlabel("paired gap")
    ax.set_xlim(-0.04, 0.95)
    ax.scatter([], [], color=EMPIRICAL, s=18, label="vs strategy")
    ax.scatter([], [], color=CONTROL, s=18, label="vs score")
    ax.legend(loc="upper center", bbox_to_anchor=(0.55, -0.18), ncol=2, handletextpad=0.3, columnspacing=0.9)
    style_axis(ax, grid_axis="x")

    ax = fig.add_subplot(gs[0, 2])
    panel_label(ax, "c", "Preprocessing heterogeneity")
    hetero = external_cases.merge(manifest, left_on="case", right_on="dataset_name", how="left")
    x = np.log10(hetero["retained_events"].astype(float).clip(lower=1))
    yv = hetero["mean_gap_vs_scrs_gamma1_strategy_shuffled"].astype(float)
    sizes = 18 + 34 * (hetero["n"].astype(float) / max(hetero["n"].astype(float).max(), 1))
    ax.scatter(x, yv, s=sizes, color=EMPIRICAL, alpha=0.75, edgecolor="white", lw=0.35)
    xmin, xmax = float(x.min()) - 0.10, float(x.max()) + 0.32
    ymin, ymax = 0.0, max(0.75, float(yv.max()) + 0.10)
    for xi in x:
        ax.plot([xi, xi], [ymax - 0.030, ymax - 0.006], color=LIGHT_CONTROL, lw=0.65, zorder=0)
    for yi in yv:
        ax.plot([xmax - 0.050, xmax - 0.010], [yi, yi], color=LIGHT_CONTROL, lw=0.65, zorder=0)
    if len(hetero) >= 3:
        slope, intercept = np.polyfit(x, yv, 1)
        xx = np.linspace(float(x.min()), float(x.max()), 50)
        ax.plot(xx, slope * xx + intercept, color=CONTROL, lw=0.9, ls=(0, (3, 2)))
        corr = float(np.corrcoef(x, yv)[0, 1])
        ax.text(0.96, 0.94, f"r={corr:.2f}", transform=ax.transAxes, ha="right", va="top", fontsize=6.7, color=TEXT)
    label_specs = {
        "Ask Ubuntu threads": ("Ask Ubuntu", 0.08, 0.010, "left"),
        "Email-Enron": ("Enron", 0.08, 0.010, "left"),
        "Copenhagen Bluetooth": ("Copenhagen", -0.05, 0.022, "right"),
        "Congress bills": ("Congress", 0.00, 0.025, "center"),
        "Email-EU": ("Email-EU", 0.00, 0.025, "center"),
    }
    for _, row in hetero.iterrows():
        short_label, dx, dy, ha = label_specs.get(
            str(row["dataset_label"]),
            (str(row["dataset_label"]).split()[0], 0.00, 0.025, "center"),
        )
        label_y = min(float(row["mean_gap_vs_scrs_gamma1_strategy_shuffled"]) + 0.025, ymax - 0.035)
        label_x = np.log10(float(row["retained_events"]))
        ax.text(
            min(max(label_x + dx, xmin + 0.06), xmax - 0.08),
            min(label_y + dy, ymax - 0.030),
            short_label,
            fontsize=6.0,
            ha=ha,
            va="bottom",
            color=TEXT,
            clip_on=True,
        )
    ax.set_xlabel(r"log$_{10}$ retained events")
    ax.set_ylabel("gap vs strategy-shuffled")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    style_axis(ax, grid_axis="both")

    ax = fig.add_subplot(gs[1, 0])
    panel_label(ax, "d", "Payoff/update sensitivity")
    sens = payoff.loc[
        payoff["control"].isin(["scrs_gamma1_strategy_shuffled", "scrs_gamma1_score_shuffled"])
    ].copy()
    mode_label = {
        ("accumulated", "asynchronous_in_place"): "Accumulated\nasync",
        ("accumulated", "synchronous"): "Accumulated\nsync",
        ("degree_normalized", "synchronous"): "Degree\nnormalized",
        ("per_capita", "synchronous"): "Per-capita",
    }
    sens["mode"] = [
        mode_label.get((str(payoff_mode), str(update_mode)), f"{payoff_mode}\n{update_mode}")
        for payoff_mode, update_mode in zip(sens["payoff_mode"], sens["update_mode"], strict=False)
    ]
    mode_order = ["Accumulated\nasync", "Accumulated\nsync", "Degree\nnormalized", "Per-capita"]
    y_mode = {mode: i for i, mode in enumerate(mode_order)}
    ctrl_offset = {"scrs_gamma1_strategy_shuffled": -0.10, "scrs_gamma1_score_shuffled": 0.10}
    for control, color in [("scrs_gamma1_strategy_shuffled", EMPIRICAL), ("scrs_gamma1_score_shuffled", CONTROL)]:
        for mode in mode_order:
            vals = sens.loc[(sens["control"] == control) & (sens["mode"] == mode), "mean_gap"]
            mean, lo, hi = ci_from_series(vals)
            if np.isfinite(mean):
                forest_point(ax, mean, lo, hi, y_mode[mode] + ctrl_offset[control], color, marker="o", ms=3.2)
    ax.axvline(0, color=TEXT, lw=0.60, ls=(0, (3, 2)))
    ax.set_yticks(list(y_mode.values()), mode_order)
    ax.invert_yaxis()
    ax.set_xlabel("mean paired gap")
    ax.set_xlim(-0.04, 0.75)
    if "Per-capita" in y_mode:
        ax.text(0.54, y_mode["Per-capita"], "boundary", color=TEXT, fontsize=6.7, ha="left", va="center")
    style_axis(ax, grid_axis="x")

    ax = fig.add_subplot(gs[1, 1])
    panel_label(ax, "e", "Mutation-noise trajectory")
    traj = trajectory.loc[(trajectory["source"] == "real") & (trajectory["variant"] == "scrs_gamma1")].copy()
    r_value = 0.9 if 0.9 in set(traj["r"].astype(float)) else float(traj["r"].astype(float).iloc[0])
    traj = traj.loc[traj["r"].astype(float) == r_value]
    mutation_order = sorted(traj["mutation_rate"].astype(float).unique())
    colors = plt.cm.viridis(np.linspace(0.18, 0.82, max(len(mutation_order), 1)))
    for color, mu in zip(colors, mutation_order):
        subset = traj.loc[traj["mutation_rate"].astype(float) == mu].sort_values("step")
        subset = (
            subset.groupby("step", as_index=False)
            .agg(
                coop_mean=("coop_mean", "mean"),
                coop_ci95_low=("coop_ci95_low", "mean"),
                coop_ci95_high=("coop_ci95_high", "mean"),
            )
            .sort_values("step")
        )
        xvals = subset["step"].astype(float).to_numpy()
        yvals = subset["coop_mean"].astype(float).to_numpy()
        lo = subset["coop_ci95_low"].astype(float).to_numpy()
        hi = subset["coop_ci95_high"].astype(float).to_numpy()
        ax.plot(xvals, yvals, lw=1.1, color=color, label=fr"$\mu$={mu:g}")
        ax.fill_between(xvals, lo, hi, color=color, alpha=0.18, lw=0)
    ax.set_xlabel("step")
    ax.set_ylabel("cooperation")
    ax.set_ylim(0, 1.02)
    ax.legend(loc="lower right", handletextpad=0.3)
    style_axis(ax, grid_axis="both")

    ax = fig.add_subplot(gs[1, 2])
    panel_label(ax, "f", "Noise endpoint boundary")
    endpoint = noise_cells.copy()
    endpoint = endpoint.groupby(["source", "mutation_rate"], as_index=False).agg(
        mean_scrs=("scrs", "mean"),
        lo=("scrs_ci95_low", "mean"),
        hi=("scrs_ci95_high", "mean"),
    )
    for source, color, marker, offset in [("real", EMPIRICAL, "o", -0.0015), ("synthetic", SYNTHETIC, "s", 0.0015)]:
        sub = endpoint.loc[endpoint["source"] == source].sort_values("mutation_rate")
        if sub.empty:
            continue
        ax.errorbar(
            sub["mutation_rate"].astype(float) + offset,
            sub["mean_scrs"].astype(float),
            yerr=[
                sub["mean_scrs"].astype(float) - sub["lo"].astype(float),
                sub["hi"].astype(float) - sub["mean_scrs"].astype(float),
            ],
            color=color,
            marker=marker,
            ms=3.2,
            lw=1.0,
            capsize=1.8,
            capthick=0.65,
            label=SOURCE_LABEL[source],
        )
    ax.set_xlabel(r"mutation $\mu$")
    ax.set_ylabel("tail cooperation")
    ax.set_ylim(0, 1.02)
    ax.set_xticks([0, 0.001, 0.005, 0.01], ["0", ".001", ".005", ".01"])
    ax.legend(loc="lower left", handletextpad=0.3)
    style_axis(ax, grid_axis="both")
    save_figure(fig, f"fig5_external_sensitivity_noise{STEM_SUFFIX}")


def main() -> None:
    setup_style()
    figure2()
    figure3()
    figure4()
    figure5()
    print(f"Wrote NC-style figure files to {OUT}")


if __name__ == "__main__":
    main()
