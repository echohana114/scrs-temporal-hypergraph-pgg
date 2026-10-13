#!/usr/bin/env python3
from __future__ import annotations

import csv
import os
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "source_data"
FIGURES = ROOT / "figures"

COLORS = {
    "scrs": "#009E73",
    "empirical": "#0072B2",
    "synthetic": "#CC79A7",
    "control": "#6F6F6F",
    "control_dark": "#3A3A3A",
    "grid": "#E7E7E7",
    "soft_grid": "#F2F2F2",
    "shade": "#F7F7F7",
    "text": "#141414",
    "white": "#FFFFFF",
    # Backward-compatible aliases used by supplementary panels.
    "blue": "#0072B2",
    "green": "#009E73",
    "orange": "#E69F00",
    "red": "#D55E00",
    "pink": "#CC79A7",
    "gray": "#6F6F6F",
    "light_gray": "#E7E7E7",
    "very_light": "#F7F7F7",
}

CASE_ORDER = [
    "real_highschool2013",
    "real_workplace2013",
    "real_hospitalward2010",
    "real_sfhh2009",
    "synthetic_structured_ring",
    "synthetic_community",
]

CASE_LABELS = {
    "real_highschool2013": "High school 2013",
    "real_workplace2013": "Workplace 2013",
    "real_hospitalward2010": "Hospital ward 2010",
    "real_sfhh2009": "SFHH 2009",
    "synthetic_structured_ring": "Structured ring",
    "synthetic_community": "Community synthetic",
    "synthetic_stress_community_resample_n100": "Community n=100",
    "synthetic_stress_community_resample_n200": "Community n=200",
    "synthetic_stress_community_resample_n400": "Community n=400",
    "synthetic_stress_heterogeneous_activity_n100": "Heterogeneous n=100",
    "synthetic_stress_heterogeneous_activity_n200": "Heterogeneous n=200",
    "synthetic_stress_heterogeneous_activity_n400": "Heterogeneous n=400",
    "synthetic_stress_structured_ring_n100": "Ring n=100",
    "synthetic_stress_structured_ring_n200": "Ring n=200",
    "synthetic_stress_structured_ring_n400": "Ring n=400",
    "synthetic_stress_temporal_modular_switching_n100": "Modular n=100",
    "synthetic_stress_temporal_modular_switching_n200": "Modular n=200",
    "synthetic_stress_temporal_modular_switching_n400": "Modular n=400",
    "synthetic_stress_uniform_random_n100": "Uniform n=100",
    "synthetic_stress_uniform_random_n200": "Uniform n=200",
    "synthetic_stress_uniform_random_n400": "Uniform n=400",
    "external_copenhagen_bluetooth": "Copenhagen\nBluetooth",
    "external_email_eu": "Email-EU",
    "external_congress_bills": "Congress\nbills",
    "external_threads_ask_ubuntu": "Ask Ubuntu\nthreads",
    "external_email_enron": "Email-Enron",
}

CONTROL_SHORT = {
    "scrs_gamma1_strategy_shuffled": "Strategy-shuffled",
    "scrs_gamma1_payoff_only_role": "Payoff-only role",
    "scrs_gamma1_success_only_no_coop_filter": "Success-only,\nno coop filter",
    "scrs_gamma1_random_role_same_edge": "Random role,\nsame edge",
    "scrs_gamma1_cooperator_only_random": "Cooperator-only random",
    "scrs_gamma1_score_shuffled": "Score-shuffled",
}


def configure_matplotlib():
    os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/mpl_scrs_nc")
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import patches
    from matplotlib.colors import LinearSegmentedColormap

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "Nimbus Roman", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 7.8,
            "axes.labelsize": 7.8,
            "axes.titlesize": 8.3,
            "xtick.labelsize": 6.9,
            "ytick.labelsize": 6.9,
            "legend.fontsize": 6.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.65,
            "axes.edgecolor": COLORS["text"],
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 2.2,
            "ytick.major.size": 2.2,
            "legend.frameon": False,
            "savefig.facecolor": "white",
        }
    )
    return plt, patches, LinearSegmentedColormap


def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name, keep_default_na=False)


def save(fig, stem: str, source_files: list[str], manifest: list[dict[str, str]]) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    for ext in ("svg", "pdf"):
        fig.savefig(FIGURES / f"{stem}.{ext}", bbox_inches="tight", facecolor="white")
    fig.savefig(FIGURES / f"{stem}.png", dpi=450, bbox_inches="tight", facecolor="white")
    manifest.append(
        {
            "figure": stem,
            "outputs": ";".join([f"figures/{stem}.{ext}" for ext in ("svg", "pdf", "png")]),
            "source_data": ";".join([f"source_data/{name}" for name in source_files]),
        }
    )


def save_supplement(fig, stem: str, source_files: list[str], manifest: list[dict[str, str]]) -> None:
    out_dir = FIGURES / "supplementary"
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext in ("svg", "pdf"):
        fig.savefig(out_dir / f"{stem}.{ext}", bbox_inches="tight", facecolor="white")
    fig.savefig(out_dir / f"{stem}.png", dpi=450, bbox_inches="tight", facecolor="white")
    manifest.append(
        {
            "figure": stem,
            "outputs": ";".join([f"figures/supplementary/{stem}.{ext}" for ext in ("svg", "pdf", "png")]),
            "source_data": ";".join([f"source_data/supplementary/{name}" for name in source_files]),
        }
    )


def wrap_label(text: str, width: int = 20) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def annotate_values(ax, values: np.ndarray, fmt: str = ".2f") -> None:
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            value = values[i, j]
            if np.isfinite(value):
                text_color = COLORS["white"] if value < 0.18 else COLORS["text"]
                ax.text(j, i, format(value, fmt), ha="center", va="center", fontsize=5.0, color=text_color)


def style_axis(ax, grid_axis: str | None = "x") -> None:
    ax.set_axisbelow(True)
    if grid_axis:
        ax.grid(axis=grid_axis, color=COLORS["grid"], lw=0.45)
    ax.tick_params(width=0.6, length=2.2, color=COLORS["text"])
    for spine in ("left", "bottom"):
        ax.spines[spine].set_linewidth(0.65)
        ax.spines[spine].set_color(COLORS["text"])


def panel_title(ax, label: str, title: str) -> None:
    ax.set_title(f"{label}  {title}", loc="left", fontweight="bold", fontsize=7.7, pad=3.0)


def ci_errorbar(ax, x, y, xlow, xhigh, color, label=None, marker="o", zorder=4):
    ax.errorbar(
        x,
        y,
        xerr=[[xlow], [xhigh]],
        fmt=marker,
        ms=3.7,
        mfc=color,
        mec="white",
        mew=0.35,
        lw=0.95,
        capsize=2.0,
        capthick=0.8,
        color=color,
        label=label,
        zorder=zorder,
    )


def make_fig1(plt, patches, manifest: list[dict[str, str]]) -> None:
    read_csv("fig1_model_diagram_flow.csv")

    with plt.rc_context(
        {
            "text.usetex": True,
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
            "text.latex.preamble": r"\usepackage{amsmath}\usepackage{helvet}\renewcommand{\familydefault}{\sfdefault}",
        }
    ):
        fig, ax = plt.subplots(figsize=(7.45, 4.45))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        green = COLORS["scrs"]
        blue = COLORS["empirical"]
        gray = "#8E8E8E"
        dark_gray = COLORS["control_dark"]
        light_gray = "#D9D9D9"

        def panel_label(x, y, letter, title):
            ax.text(
                x,
                y,
                rf"\textbf{{{letter}}}\quad \textbf{{{title}}}",
                ha="left",
                va="top",
                fontsize=7.6,
                color=COLORS["text"],
            )

        def flow_arrow(x0, y0, x1, y1, label):
            arrow = patches.FancyArrowPatch(
                (x0, y0),
                (x1, y1),
                arrowstyle="Simple,head_length=5,head_width=5,tail_width=1.5",
                mutation_scale=1.0,
                linewidth=0,
                facecolor=dark_gray,
                edgecolor="none",
                alpha=0.35,
                zorder=2,
            )
            ax.add_patch(arrow)
            ax.text(
                (x0 + x1) / 2,
                y0 + 0.046,
                label,
                fontsize=5.2,
                ha="center",
                va="center",
                color=dark_gray,
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4, "alpha": 0.92},
            )

        def node(x, y, strategy, size=0.015, lw=0.45, z=6):
            color = green if strategy == "C" else gray
            circ = patches.Circle((x, y), size, facecolor=color, edgecolor="white", linewidth=lw, zorder=z)
            ax.add_patch(circ)
            ax.text(x, y - 0.0004, rf"\textbf{{{strategy}}}", ha="center", va="center", fontsize=5.1, color="white", zorder=z + 1)
            return circ

        def hyperedge(center, width, height, angle, selected=False, alpha=0.65):
            edge = patches.Ellipse(
                center,
                width,
                height,
                angle=angle,
                facecolor="#F7FAFC" if selected else "none",
                edgecolor=blue if selected else light_gray,
                linewidth=1.05 if selected else 0.65,
                linestyle="-" if selected else (0, (3, 2)),
                alpha=0.92 if selected else alpha,
                zorder=1,
            )
            ax.add_patch(edge)
            return edge

        # a. Temporal hypergraph context.
        panel_label(0.045, 0.925, "a", "Temporal hypergraph context")
        hyperedge((0.155, 0.704), 0.205, 0.142, 10, selected=False, alpha=0.75)
        hyperedge((0.196, 0.650), 0.270, 0.142, -5, selected=True)
        hyperedge((0.145, 0.580), 0.208, 0.128, -18, selected=False, alpha=0.70)
        snapshot_nodes = [
            (0.105, 0.725, "C"),
            (0.178, 0.738, "D"),
            (0.070, 0.660, "D"),
            (0.140, 0.653, "C"),
            (0.223, 0.678, "D"),
            (0.270, 0.648, "C"),
            (0.185, 0.595, "C"),
            (0.108, 0.565, "C"),
        ]
        for x, y, strategy in snapshot_nodes:
            node(x, y, strategy, size=0.014)
        focal_xy = (0.170, 0.650)
        ax.add_patch(patches.Circle(focal_xy, 0.024, facecolor="white", edgecolor=blue, linewidth=1.05, zorder=9))
        ax.text(focal_xy[0], focal_xy[1] - 0.001, r"$i$", ha="center", va="center", fontsize=9.4, color=blue, zorder=10)
        ax.text(0.058, 0.500, r"transient incident groups $\mathcal{E}_t(i)$", fontsize=6.3, ha="left", color=dark_gray)

        # b. Success-context selection.
        panel_label(0.380, 0.925, "b", "Success-context selection")
        ax.text(0.394, 0.795, r"$G_e(t)$", fontsize=9.0, ha="left", va="center", color=dark_gray)
        ax.plot([0.432, 0.573], [0.765, 0.765], color=light_gray, lw=0.55, zorder=1)
        score_rows = [(r"$e_1$", 0.38, gray), (r"$e^\star$", 0.84, blue), (r"$e_3$", 0.22, gray)]
        for idx, (edge_label, score, color) in enumerate(score_rows):
            y = 0.720 - idx * 0.075
            ax.text(0.394, y, edge_label, fontsize=7.1, ha="left", va="center", color=dark_gray)
            ax.plot([0.438, 0.438 + 0.125 * score], [y, y], color=color, lw=4.0, alpha=0.88, solid_capstyle="round")
            ax.add_patch(patches.Circle((0.438 + 0.125 * score, y), 0.006, facecolor=color, edgecolor="white", linewidth=0.3, zorder=5))
        ax.add_patch(
            patches.FancyBboxPatch(
                (0.421, 0.626),
                0.190,
                0.115,
                boxstyle="round,pad=0.004,rounding_size=0.010",
                facecolor="none",
                edgecolor=blue,
                linewidth=0.75,
                alpha=0.95,
            )
        )
        ax.text(0.395, 0.505, r"score layer selects a group context", fontsize=6.2, ha="left", color=dark_gray)
        ax.text(0.395, 0.472, r"fine ordering is auxiliary", fontsize=6.1, ha="left", color=gray)

        # c. Cooperative role screen.
        panel_label(0.682, 0.925, "c", r"Cooperative role screen")
        role_y = 0.660
        role_x = np.linspace(0.692, 0.952, 6)
        role_pattern = ["C", "D", "C", "D", "C", "C"]
        ax.add_patch(patches.Ellipse((0.822, role_y), 0.322, 0.122, facecolor="#F7FAFC", edgecolor=blue, linewidth=0.85, alpha=0.92, zorder=1))
        ax.text(0.690, 0.746, r"selected $e^\star$ contains C and D", fontsize=6.3, color=dark_gray, ha="left")
        ax.plot([role_x[0] - 0.018, role_x[-1] + 0.018], [role_y, role_y], color=light_gray, lw=0.72, zorder=2)
        for x_value, strategy in zip(role_x, role_pattern):
            node(x_value, role_y, strategy, size=0.018, z=6)
        ax.add_patch(patches.Circle((role_x[2], role_y), 0.032, facecolor="none", edgecolor=green, linewidth=1.15, zorder=10))
        ax.add_patch(patches.Circle((role_x[3], role_y), 0.032, facecolor="none", edgecolor=dark_gray, linewidth=0.80, linestyle=(0, (4, 2)), zorder=10))
        ax.text(role_x[2] - 0.010, 0.563, r"\shortstack{\textbf{eligible }$j$\\cooperative role}", fontsize=5.55, ha="center", va="top", color=green)
        ax.text(role_x[3] + 0.040, 0.563, r"\shortstack{successful D\\not copied}", fontsize=5.55, ha="center", va="top", color=dark_gray)
        ax.text(0.716, 0.480, r"screening occurs within the same temporal group", fontsize=5.8, ha="left", color=dark_gray)

        flow_arrow(0.315, 0.655, 0.365, 0.655, "context sampling")
        flow_arrow(0.610, 0.655, 0.665, 0.655, "role screening")

        # d. Operational rules.
        ax.plot([0.040, 0.960], [0.410, 0.410], color=COLORS["grid"], lw=0.65)
        panel_label(0.045, 0.368, "d", "Operational rule equations")
        label_x = 0.070
        formula_x = 0.228
        ys = [0.306, 0.242, 0.178, 0.114]
        labels = ["Payoff", "Context score", "Eligible roles", "Strategy adoption"]
        formulas = [
            r"$P_i(t)=\sum_{e\in\mathcal{E}_t:\,i\in e}\left[r\,n_C(e,t)-s_i(t)\right]$",
            r"$G_e(t)=q_e(t)\max\{0,r\,n_C(e,t)-1\},\quad q_e(t)=n_C(e,t)/|e|$",
            r"$\mathcal{C}_i(e^\star,t)=\{j\in e^\star\setminus\{i\}:s_j(t)=1\}$",
            r"$\Pr(s_i\leftarrow s_j)=\frac{1}{1+\exp\{-\beta(P_j-P_i)\}}$",
        ]
        for y, rule_label, formula in zip(ys, labels, formulas):
            ax.text(label_x, y, rf"\textbf{{{rule_label}}}", fontsize=6.9, ha="left", va="center", color=dark_gray)
            ax.text(formula_x, y, formula, fontsize=7.9, ha="left", va="center", color=COLORS["text"])
        ax.text(
            0.692,
            0.305,
            r"Temporal hyperedges supply the group-success context;",
            fontsize=6.2,
            color=dark_gray,
            ha="left",
        )
        ax.text(
            0.692,
            0.268,
            r"the cooperator filter resolves the free-rider ambiguity.",
            fontsize=6.2,
            color=dark_gray,
            ha="left",
        )

        save(fig, "fig1_model_diagram", ["fig1_model_diagram_flow.csv"], manifest)
    plt.close(fig)


def make_fig2(plt, manifest: list[dict[str, str]]) -> None:
    tails = read_csv("fig2a_s20_scrs_tail_by_case.csv")
    gap_cells = read_csv("fig2b_s20_gap_cells_for_forest.csv")
    gap_forest = read_csv("fig2b_s20_gap_forest_summary.csv")

    fig = plt.figure(figsize=(7.4, 4.15))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.24], wspace=0.42)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    r_values = [0.7, 0.9, 1.0]
    r_markers = {0.7: "o", 0.9: "s", 1.0: "^"}
    offsets = {0.7: -0.20, 0.9: 0.0, 1.0: 0.20}
    y_positions = np.arange(len(CASE_ORDER))
    lookup = tails.set_index(["case", "r"])
    for idx, case in enumerate(CASE_ORDER):
        if case.startswith("synthetic"):
            ax1.axhspan(idx - 0.42, idx + 0.42, color=COLORS["synthetic"], alpha=0.035, lw=0)
    for r in r_values:
        means = []
        lower = []
        upper = []
        for case in CASE_ORDER:
            row = lookup.loc[(case, r)]
            means.append(float(row["scrs"]))
            lower.append(float(row["scrs"]) - float(row["scrs_ci95_low"]))
            upper.append(float(row["scrs_ci95_high"]) - float(row["scrs"]))
        ax1.errorbar(
            means,
            y_positions + offsets[r],
            xerr=[lower, upper],
            fmt=r_markers[r],
            ms=3.5,
            lw=0.9,
            capsize=2.0,
            capthick=0.8,
            color=COLORS["scrs"],
            mfc=COLORS["scrs"],
            mec="white",
            mew=0.35,
            label=f"r={r:.1f}",
        )
    ax1.axvline(1.0, color=COLORS["grid"], lw=0.8)
    ax1.set_yticks(y_positions)
    ax1.set_yticklabels([CASE_LABELS[c] for c in CASE_ORDER])
    ax1.invert_yaxis()
    ax1.set_xlim(0.55, 1.02)
    ax1.set_xlabel("SCRS tail cooperation")
    panel_title(ax1, "a", "SCRS across datasets and return")
    style_axis(ax1, "x")
    ax1.legend(ncols=3, loc="lower right", handletextpad=0.4, columnspacing=0.7)
    ax1.text(0.995, 0.10, "synthetic", transform=ax1.transAxes, ha="right", va="center", fontsize=5.8, color=COLORS["synthetic"])
    ax1.text(0.995, 0.86, "empirical", transform=ax1.transAxes, ha="right", va="center", fontsize=5.8, color=COLORS["empirical"])

    comparison_order = [
        ("wang_temporal_hypergraph", "Wang imitation"),
        ("csgc_gamma1", "CSGC"),
        ("lfds_strongest", "LFDS"),
        ("scrs_gamma1_strategy_shuffled", "Strategy-shuffled"),
        ("scrs_gamma1_score_shuffled", "Score-shuffled"),
    ]
    y = np.arange(len(comparison_order))
    rng = np.random.default_rng(11)
    ax2.axhspan(3.55, 4.45, color=COLORS["shade"], lw=0, zorder=0)
    for source, dx, color, label in [
        ("real", -0.13, COLORS["empirical"], "Empirical cells"),
        ("synthetic", 0.13, COLORS["synthetic"], "Synthetic cells"),
    ]:
        for idx, (key, _label) in enumerate(comparison_order):
            cells = gap_cells[(gap_cells["source"] == source) & (gap_cells["comparison_key"] == key)].copy()
            cells["gap"] = pd.to_numeric(cells["gap"], errors="coerce")
            jitter = rng.uniform(-0.045, 0.045, size=len(cells))
            ax2.scatter(
                cells["gap"],
                np.full(len(cells), idx + dx) + jitter,
                s=11,
                alpha=0.30,
                color=color,
                edgecolors="none",
                zorder=2,
            )
            row = gap_forest[(gap_forest["source"] == source) & (gap_forest["comparison_key"] == key)].iloc[0]
            mean = float(row["mean_gap"])
            lower = mean - float(row["gap_ci95_low"])
            upper = float(row["gap_ci95_high"]) - mean
            ci_errorbar(ax2, mean, idx + dx, lower, upper, color, label=label if idx == 0 else None)
    ax2.axvline(0, color=COLORS["text"], lw=0.8)
    ax2.set_yticks(y)
    ax2.set_yticklabels([label for _key, label in comparison_order])
    ax2.invert_yaxis()
    ax2.set_xlim(-0.08, 0.78)
    ax2.set_xlabel("Paired SCRS gap")
    panel_title(ax2, "b", "Paired gaps to baselines")
    style_axis(ax2, "x")
    ax2.legend(loc="lower right", handletextpad=0.4)
    ax2.text(0.23, 4.34, "score ordering not decisive", ha="left", va="center", fontsize=6.0, color=COLORS["control_dark"])

    save(
        fig,
        "fig2_main_performance",
        [
            "fig2a_s20_scrs_tail_by_case.csv",
            "fig2b_s20_gap_cells_for_forest.csv",
            "fig2b_s20_gap_forest_summary.csv",
        ],
        manifest,
    )
    plt.close(fig)


def make_fig3(plt, manifest: list[dict[str, str]]) -> None:
    mech = read_csv("fig3_s25_mechanism_mean_gaps.csv")
    paired = read_csv("fig3_s25_mechanism_paired_gaps_by_cell.csv")
    mech = mech.sort_values(["control_order", "source"])
    control_keys = list(mech["control"].drop_duplicates())
    controls = {
        "scrs_gamma1_strategy_shuffled": "Role signal broken\n(strategy labels shuffled)",
        "scrs_gamma1_payoff_only_role": "Cooperator filter removed\n(payoff-only role)",
        "scrs_gamma1_success_only_no_coop_filter": "Cooperator filter removed\n(success-only context)",
        "scrs_gamma1_random_role_same_edge": "Same edge, random role",
        "scrs_gamma1_cooperator_only_random": "Payoff ranking removed",
        "scrs_gamma1_score_shuffled": "Score ordering removed",
    }
    y = np.arange(len(controls))
    fig, ax = plt.subplots(figsize=(7.4, 4.35))
    rng = np.random.default_rng(27)
    ax.axhspan(-0.45, 3.45, color="#F2FAF5", lw=0, zorder=0)
    ax.axhspan(3.55, 5.45, color=COLORS["shade"], lw=0, zorder=0)
    ax.axvline(0, color=COLORS["text"], lw=0.8, zorder=1)
    for source, dy, color, label in [
        ("real", -0.13, COLORS["empirical"], "Empirical cells"),
        ("synthetic", 0.13, COLORS["synthetic"], "Synthetic cells"),
    ]:
        summary_rows = mech[mech["source"] == source].set_index("control")
        for idx, key in enumerate(control_keys):
            points = paired[(paired["source"] == source) & (paired["control"] == key)].copy()
            points["mean_gap"] = pd.to_numeric(points["mean_gap"], errors="coerce")
            jitter = rng.uniform(-0.055, 0.055, size=len(points))
            ax.scatter(
                points["mean_gap"],
                np.full(len(points), idx + dy) + jitter,
                s=12,
                alpha=0.32,
                color=color,
                edgecolors="none",
                zorder=2,
            )
            mean = float(summary_rows.loc[key, "mean_gap"])
            error = 1.96 * float(summary_rows.loc[key, "mean_gap_se"])
            ci_errorbar(ax, mean, idx + dy, error, error, color, label=label if idx == 0 else None)
    ax.axhline(3.5, color=COLORS["white"], lw=2.4, zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels([controls[key] for key in control_keys])
    ax.invert_yaxis()
    ax.set_xlim(-0.08, 0.78)
    ax.set_xlabel("Mechanism loss relative to SCRS")
    panel_title(ax, "a", "Mechanism decomposition")
    style_axis(ax, "x")
    ax.legend(loc="lower right", handletextpad=0.4)
    ax.text(0.52, 1.45, "core signal disrupted", fontsize=6.4, color=COLORS["scrs"], ha="left", va="center")
    ax.text(0.18, 4.65, "near SCRS", fontsize=6.4, color=COLORS["control_dark"], ha="left", va="center")
    ax.text(0.52, -0.25, "role screen disrupted", fontsize=6.2, color=COLORS["scrs"], ha="left", va="center")
    save(
        fig,
        "fig3_mechanism_decomposition",
        ["fig3_s25_mechanism_mean_gaps.csv", "fig3_s25_mechanism_paired_gaps_by_cell.csv"],
        manifest,
    )
    plt.close(fig)


def make_fig4(plt, cmap_factory, manifest: list[dict[str, str]]) -> None:
    from matplotlib.patches import Rectangle

    phase_r_rho0 = read_csv("fig4a_s21_phase_r_rho0.csv")
    phase_r_mutation = read_csv("fig4b_s24_phase_r_mutation.csv")
    s22 = read_csv("fig4b_s22_real_nulls_cell_summary.csv")
    s23 = read_csv("fig4c_s23_synthetic_stress_cell_summary.csv")
    fig = plt.figure(figsize=(7.4, 5.75))
    outer = fig.add_gridspec(2, 3, width_ratios=[1.05, 0.95, 1.05], height_ratios=[1.13, 1.0], wspace=0.55, hspace=0.55)
    cmap = plt.get_cmap("cividis")

    axa = fig.add_subplot(outer[0, 0:2])
    phase_real = phase_r_rho0[phase_r_rho0["source"] == "real"].copy()
    for column in ["r", "rho0", "mean_scrs"]:
        phase_real[column] = pd.to_numeric(phase_real[column], errors="coerce")
    r_order = sorted(phase_real["r"].dropna().unique())
    rho_order = sorted(phase_real["rho0"].dropna().unique())
    matrix = np.array(
        [
            [
                float(phase_real[(phase_real["rho0"] == rho) & (phase_real["r"] == r)]["mean_scrs"].iloc[0])
                for r in r_order
            ]
            for rho in rho_order
        ]
    )
    im = axa.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    axa.set_xticks(np.arange(len(r_order)))
    axa.set_xticklabels([f"{value:g}" for value in r_order])
    axa.set_yticks(np.arange(len(rho_order)))
    axa.set_yticklabels([f"{value:g}" for value in rho_order])
    axa.set_xlabel("r")
    axa.set_ylabel("rho0")
    panel_title(axa, "a", "Stable region and initial-condition boundary")
    annotate_values(axa, matrix, ".2f")
    cbar = fig.colorbar(im, ax=axa, fraction=0.030, pad=0.025)
    cbar.set_label("SCRS tail cooperation", fontsize=6.5)
    cbar.ax.tick_params(labelsize=5.8, length=2.0)

    axb = fig.add_subplot(outer[0, 2])
    noise_real = phase_r_mutation[phase_r_mutation["source"] == "real"].copy()
    for column in ["r", "mutation_rate", "mean_scrs"]:
        noise_real[column] = pd.to_numeric(noise_real[column], errors="coerce")
    r_order_noise = sorted(noise_real["r"].dropna().unique())
    mu_order = sorted(noise_real["mutation_rate"].dropna().unique())
    matrix_noise = np.array(
        [
            [
                float(noise_real[(noise_real["mutation_rate"] == mu) & (noise_real["r"] == r)]["mean_scrs"].iloc[0])
                for r in r_order_noise
            ]
            for mu in mu_order
        ]
    )
    im_noise = axb.imshow(matrix_noise, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    axb.set_xticks(np.arange(len(r_order_noise)))
    axb.set_xticklabels([f"{value:g}" for value in r_order_noise])
    axb.set_yticks(np.arange(len(mu_order)))
    axb.set_yticklabels(["0", "1e-4", "1e-3", "1e-2"])
    axb.set_xlabel("r")
    axb.set_ylabel("mutation rate")
    panel_title(axb, "b", "Noise boundary")
    annotate_values(axb, matrix_noise, ".2f")
    cbar_noise = fig.colorbar(im_noise, ax=axb, fraction=0.046, pad=0.035)
    cbar_noise.set_label("SCRS tail cooperation", fontsize=6.5)
    cbar_noise.ax.tick_params(labelsize=5.8, length=2.0)

    axc = fig.add_subplot(outer[1, 0])
    null_order = ["original", "block_order_shuffle", "degree_preserving_rewire", "activity_preserving_resample"]
    null_labels = ["Original", "Block order", "Degree rewire", "Activity resample"]
    s22["gap_vs_scrs_gamma1_strategy_shuffled"] = pd.to_numeric(s22["gap_vs_scrs_gamma1_strategy_shuffled"], errors="coerce")
    s22["gap_vs_scrs_gamma1_score_shuffled"] = pd.to_numeric(s22["gap_vs_scrs_gamma1_score_shuffled"], errors="coerce")
    y_null = np.arange(len(null_order))
    rng = np.random.default_rng(44)
    for metric, dx, color, label in [
        ("gap_vs_scrs_gamma1_strategy_shuffled", -0.12, COLORS["scrs"], "Strategy-shuffled"),
        ("gap_vs_scrs_gamma1_score_shuffled", 0.12, COLORS["control"], "Score-shuffled"),
    ]:
        for idx, null_model in enumerate(null_order):
            values = s22[s22["null_model"] == null_model][metric].dropna().to_numpy(dtype=float)
            jitter = rng.uniform(-0.035, 0.035, size=len(values))
            axc.scatter(values, np.full(len(values), idx + dx) + jitter, s=9, alpha=0.20, color=color, edgecolors="none")
            mean = float(np.mean(values))
            err = 1.96 * float(np.std(values, ddof=1) / np.sqrt(len(values))) if len(values) > 1 else 0.0
            ci_errorbar(axc, mean, idx + dx, err, err, color, label=label if idx == 0 else None)
    axc.axvline(0, color=COLORS["text"], lw=0.8)
    axc.set_yticks(y_null)
    axc.set_yticklabels(null_labels)
    axc.invert_yaxis()
    axc.set_xlim(-0.05, 0.72)
    axc.set_xlabel("Paired SCRS gap")
    panel_title(axc, "c", "Null preservation")
    style_axis(axc, "x")
    axc.legend(loc="upper center", bbox_to_anchor=(0.56, -0.16), ncols=1, handletextpad=0.35)

    axd = fig.add_subplot(outer[1, 1:3])
    s23["n"] = pd.to_numeric(s23["n"], errors="coerce")
    s23["gap_vs_scrs_gamma1_strategy_shuffled"] = pd.to_numeric(s23["gap_vs_scrs_gamma1_strategy_shuffled"], errors="coerce")
    stress = s23.groupby(["topology", "n"], as_index=False)["gap_vs_scrs_gamma1_strategy_shuffled"].mean()
    base_topology_order = ["community_resample", "heterogeneous_activity", "structured_ring", "temporal_modular_switching", "uniform_random"]
    topology_order = (
        stress.groupby("topology")["gap_vs_scrs_gamma1_strategy_shuffled"]
        .mean()
        .reindex(base_topology_order)
        .sort_values()
        .index.tolist()
    )
    topology_label_map = {
        "community_resample": "Community",
        "heterogeneous_activity": "Heterogeneous",
        "structured_ring": "Ring",
        "temporal_modular_switching": "Modular switch",
        "uniform_random": "Uniform",
    }
    topology_labels = [topology_label_map[value] for value in topology_order]
    n_order = [100, 200, 400]
    matrix = np.array(
        [
            [
                float(
                    stress[(stress["topology"] == topology) & (stress["n"] == n)][
                        "gap_vs_scrs_gamma1_strategy_shuffled"
                    ].iloc[0]
                )
                for n in n_order
            ]
            for topology in topology_order
        ]
    )
    im_gap = axd.imshow(matrix, cmap=cmap, vmin=0, vmax=0.7, aspect="auto")
    axd.set_xticks(np.arange(len(n_order)))
    axd.set_xticklabels([str(n) for n in n_order])
    axd.set_yticks(np.arange(len(topology_order)))
    axd.set_yticklabels(topology_labels)
    axd.set_xlabel("n")
    panel_title(axd, "d", "Synthetic topology and size stress")
    annotate_values(axd, matrix, ".2f")
    min_pos = np.unravel_index(np.nanargmin(matrix), matrix.shape)
    axd.add_patch(Rectangle((min_pos[1] - 0.5, min_pos[0] - 0.5), 1, 1, fill=False, edgecolor=COLORS["control_dark"], linewidth=1.0))
    weakest_color = COLORS["white"] if matrix[min_pos] < 0.18 else COLORS["control_dark"]
    axd.text(min_pos[1] + 0.52, min_pos[0], "weakest", fontsize=5.5, va="center", ha="left", color=weakest_color)
    cbar_gap = fig.colorbar(im_gap, ax=axd, fraction=0.030, pad=0.025)
    cbar_gap.set_label("Gap vs strategy-shuffled", fontsize=6.5)
    cbar_gap.ax.tick_params(labelsize=5.8, length=2.0)

    save(
        fig,
        "fig4_robustness_null_stress",
        [
            "fig4a_s21_robustness_cell_summary.csv",
            "fig4a_s21_robustness_source_summary.csv",
            "fig4a_s21_phase_r_rho0.csv",
            "fig4b_s24_phase_r_mutation.csv",
            "fig4b_s22_real_nulls_cell_summary.csv",
            "fig4b_s22_real_nulls_mechanism_summary.csv",
            "fig4c_s23_synthetic_stress_case_summary.csv",
            "fig4c_s23_synthetic_stress_cell_summary.csv",
        ],
        manifest,
    )
    plt.close(fig)


def make_fig5(plt, manifest: list[dict[str, str]]) -> None:
    s26 = read_csv("fig5a_s26_external_paired_gaps_by_cell.csv")
    s27 = read_csv("fig5b_s27_payoff_update_source_summary.csv")
    s27_cells = read_csv("fig5b_s27_payoff_update_paired_gaps_by_cell.csv")
    s24 = read_csv("fig5c_s24_noise_horizon_cell_summary.csv")

    fig = plt.figure(figsize=(7.4, 5.2))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.32, 1.0], height_ratios=[1.0, 0.96], wspace=0.42, hspace=0.50)
    axa = fig.add_subplot(gs[:, 0])
    axb = fig.add_subplot(gs[0, 1])
    axc = fig.add_subplot(gs[1, 1])

    forest = s26[s26["control"] == "scrs_gamma1_strategy_shuffled"].copy()
    forest["r"] = pd.to_numeric(forest["r"], errors="coerce")
    forest["mean_gap"] = pd.to_numeric(forest["mean_gap"], errors="coerce")
    forest["gap_ci95_low"] = pd.to_numeric(forest["gap_ci95_low"], errors="coerce")
    forest["gap_ci95_high"] = pd.to_numeric(forest["gap_ci95_high"], errors="coerce")
    dataset_order = list(dict.fromkeys(forest["dataset_label"]))
    y_rows: list[float] = []
    y_labels: list[str] = []
    row_records = []
    y_value = 0.0
    for dataset in dataset_order:
        dataset_rows = forest[forest["dataset_label"] == dataset].sort_values("r")
        group_start = y_value
        for row in dataset_rows.itertuples(index=False):
            row_records.append((row, y_value))
            y_rows.append(y_value)
            y_labels.append(f"r={row.r:g}")
            y_value += 1.0
        group_end = y_value - 1.0
        axa.axhline(y_value - 0.5, color=COLORS["grid"], lw=0.55, zorder=0)
        axa.text(
            -0.16,
            (group_start + group_end) / 2,
            dataset,
            transform=axa.get_yaxis_transform(),
            ha="right",
            va="center",
            fontsize=6.2,
            color=COLORS["text"],
            clip_on=False,
        )
    r_markers = {0.7: "o", 0.9: "s", 1.0: "^"}
    for row, y_pos in row_records:
        mean = float(row.mean_gap)
        lower = mean - float(row.gap_ci95_low)
        upper = float(row.gap_ci95_high) - mean
        ci_errorbar(axa, mean, y_pos, lower, upper, COLORS["empirical"], marker=r_markers.get(float(row.r), "o"))
    axa.axvline(0, color=COLORS["text"], lw=0.8)
    axa.set_yticks(y_rows)
    axa.set_yticklabels(y_labels, fontsize=5.8)
    axa.tick_params(axis="y", pad=3)
    axa.invert_yaxis()
    axa.set_xlim(-0.05, 1.02)
    axa.set_xlabel("Gap vs strategy-shuffled SCRS")
    panel_title(axa, "a", "External empirical extrapolation")
    style_axis(axa, "x")
    axa.text(0.68, 0.04, "positive external gaps", transform=axa.transAxes, fontsize=6.1, color=COLORS["empirical"], ha="left")

    mode_labels = {
        "payoff_update_sensitivity_baseline": "Accum.\nsync",
        "payoff_update_sensitivity_degree_normalized_payoff": "Degree-norm.\nsync",
        "payoff_update_sensitivity_per_capita_payoff": "Per-capita\nsync",
        "payoff_update_sensitivity_asynchronous_in_place": "Accum.\nasync",
    }
    order = list(mode_labels.keys())
    s27_cells = s27_cells[s27_cells["source"] == "real"].copy()
    s27_cells["mean_gap"] = pd.to_numeric(s27_cells["mean_gap"], errors="coerce")
    x = np.arange(len(order))
    rng = np.random.default_rng(55)
    for control, dx, color, label in [
        ("scrs_gamma1_strategy_shuffled", -0.12, COLORS["scrs"], "Strategy-shuffled"),
        ("scrs_gamma1_score_shuffled", 0.12, COLORS["control"], "Score-shuffled"),
    ]:
        for idx, condition in enumerate(order):
            values = s27_cells[(s27_cells["condition"] == condition) & (s27_cells["control"] == control)]["mean_gap"].dropna().to_numpy(dtype=float)
            jitter = rng.uniform(-0.035, 0.035, size=len(values))
            axb.scatter(np.full(len(values), idx + dx) + jitter, values, s=9, alpha=0.22, color=color, edgecolors="none")
            mean = float(np.mean(values))
            err = 1.96 * float(np.std(values, ddof=1) / np.sqrt(len(values))) if len(values) > 1 else 0.0
            axb.errorbar(
                idx + dx,
                mean,
                yerr=[[err], [err]],
                fmt="o",
                ms=3.7,
                mfc=color,
                mec="white",
                mew=0.35,
                lw=0.95,
                capsize=2.0,
                capthick=0.8,
                color=color,
                label=label if idx == 0 else None,
                zorder=4,
            )
    axb.axhline(0, color=COLORS["text"], lw=0.8)
    axb.set_xticks(x)
    axb.set_xticklabels([mode_labels[key] for key in order])
    axb.tick_params(axis="x", labelsize=5.6)
    axb.set_ylabel("Paired SCRS gap")
    panel_title(axb, "b", "Payoff and update sensitivity")
    style_axis(axb, "y")
    axb.legend(loc="upper right", handletextpad=0.35)
    axb.text(2.0, 0.245, "per-capita boundary", ha="center", va="bottom", fontsize=5.8, color=COLORS["control_dark"])

    s24["mutation_rate"] = pd.to_numeric(s24["mutation_rate"], errors="coerce")
    s24["scrs"] = pd.to_numeric(s24["scrs"], errors="coerce")
    noise = s24.groupby(["source", "mutation_rate"], as_index=False).agg(
        mean=("scrs", "mean"),
        sem=("scrs", lambda values: float(np.std(values, ddof=1) / np.sqrt(len(values))) if len(values) > 1 else 0.0),
    )
    mu_order = [0.0, 0.0001, 0.001, 0.01]
    x = np.arange(len(mu_order))
    for source, color, label in [("real", COLORS["empirical"], "Empirical"), ("synthetic", COLORS["synthetic"], "Synthetic")]:
        values = []
        low = []
        high = []
        for mu in mu_order:
            row = noise[(noise["source"] == source) & (noise["mutation_rate"] == mu)].iloc[0]
            mean = float(row["mean"])
            err = 1.96 * float(row["sem"])
            values.append(mean)
            low.append(mean - err)
            high.append(mean + err)
        axc.fill_between(x, low, high, color=color, alpha=0.14, lw=0)
        axc.plot(x, values, marker="o", ms=3.1, lw=1.25, color=color, label=label)
    axc.set_xticks(x)
    axc.set_xticklabels(["0", "1e-4", "1e-3", "1e-2"])
    axc.set_ylim(0.4, 1.02)
    axc.set_xlabel("Mutation rate")
    axc.set_ylabel("SCRS tail cooperation")
    panel_title(axc, "c", "Long-horizon noise boundary")
    style_axis(axc, "y")
    axc.legend(loc="lower left", handletextpad=0.35)
    axc.text(2.15, 0.575, "high mutation boundary", fontsize=5.8, color=COLORS["control_dark"])

    save(
        fig,
        "fig5_external_sensitivity_noise",
        [
            "fig5a_s26_external_empirical_cases.csv",
            "fig5a_s26_external_dataset_manifest.csv",
            "fig5a_s26_external_paired_gaps_by_cell.csv",
            "fig5b_s27_payoff_update_source_summary.csv",
            "fig5b_s27_payoff_update_paired_gaps_by_cell.csv",
            "fig5c_s24_noise_horizon_cell_summary.csv",
            "fig5c_s24_noise_horizon_trajectory_summary.csv",
        ],
        manifest,
    )
    plt.close(fig)


def short_condition(value: str) -> str:
    labels = {
        "r_sweep": "r sweep",
        "rho0_sweep": "rho0",
        "selection_intensity_sweep": "beta",
        "real_null_model": "nulls",
        "synthetic_topology_size": "topology/size",
        "noise_horizon": "noise/horizon",
        "mechanism_decomposition": "mechanism",
        "empirical_extrapolation": "external",
        "payoff_update_sensitivity_baseline": "accum. sync",
        "payoff_update_sensitivity_degree_normalized_payoff": "deg.-norm.",
        "payoff_update_sensitivity_per_capita_payoff": "per-cap.",
        "payoff_update_sensitivity_asynchronous_in_place": "accum. async",
    }
    return labels.get(value, value.replace("_", " "))


def summary_source_files() -> list[tuple[str, str, str, str]]:
    return [
        ("S20", "s20_scrs_formal_source_summary.csv", "s20_scrs_formal_case_summary.csv", "s20_scrs_formal_cell_summary.csv"),
        ("S21", "s21_scrs_nc_source_summary.csv", "s21_scrs_nc_case_summary.csv", "s21_scrs_nc_cell_summary.csv"),
        ("S22", "s22_scrs_nc_source_summary.csv", "s22_scrs_nc_case_summary.csv", "s22_scrs_nc_cell_summary.csv"),
        ("S23", "s23_scrs_nc_source_summary.csv", "s23_scrs_nc_case_summary.csv", "s23_scrs_nc_cell_summary.csv"),
        ("S24", "s24_scrs_nc_source_summary.csv", "s24_scrs_nc_case_summary.csv", "s24_scrs_nc_cell_summary.csv"),
        ("S25", "s25_scrs_nc_source_summary.csv", "s25_scrs_nc_case_summary.csv", "s25_scrs_nc_cell_summary.csv"),
        ("S26", "s26_scrs_nc_source_summary.csv", "s26_scrs_nc_case_summary.csv", "s26_scrs_nc_cell_summary.csv"),
        ("S27", "s27_scrs_nc_source_summary.csv", "s27_scrs_nc_case_summary.csv", "s27_scrs_nc_cell_summary.csv"),
    ]


def first_existing_column(df: pd.DataFrame, names: list[str]) -> str | None:
    for name in names:
        if name in df.columns:
            return name
    return None


def make_supplementary_figures(plt, manifest: list[dict[str, str]]) -> None:
    rng = np.random.default_rng(42)
    for tag, source_file, case_file, cell_file in summary_source_files():
        source = pd.read_csv(DATA / "supplementary" / source_file, keep_default_na=False)
        cases = pd.read_csv(DATA / "supplementary" / case_file, keep_default_na=False)
        cells = pd.read_csv(DATA / "supplementary" / cell_file, keep_default_na=False)
        for df in (source, cases, cells):
            if "mean_scrs" in df.columns:
                df["mean_scrs"] = pd.to_numeric(df["mean_scrs"], errors="coerce")
            if "scrs" in df.columns:
                df["scrs"] = pd.to_numeric(df["scrs"], errors="coerce")

        fig = plt.figure(figsize=(8.8, 5.5))
        gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1.0], wspace=0.72, hspace=0.76)
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[1, :])

        source_labels = []
        for row in source.itertuples(index=False):
            condition = short_condition(getattr(row, "condition", ""))
            source_name = getattr(row, "source", "")
            source_labels.append(f"{source_name}\n{condition}" if condition else source_name)
        source_order = np.argsort(source["mean_scrs"].to_numpy())
        source_values = source["mean_scrs"].to_numpy()[source_order]
        source_labels_sorted = [source_labels[idx] for idx in source_order]
        y_source = np.arange(len(source_values))
        ax1.barh(y_source, source_values, color=COLORS["blue"], height=0.68)
        ax1.set_yticks(y_source)
        ax1.set_yticklabels([wrap_label(label, 18) for label in source_labels_sorted], fontsize=6.2, color=COLORS["text"])
        ax1.set_xlim(0, 1.05)
        ax1.set_xlabel("Mean SCRS")
        ax1.set_title(f"{tag} source view", loc="left", fontweight="bold", color=COLORS["text"], pad=5)
        ax1.grid(axis="x", color=COLORS["light_gray"], lw=0.6)

        label_col = first_existing_column(cases, ["dataset_label", "case"])
        case_summary = cases.copy()
        if label_col:
            raw_labels = case_summary[label_col].astype(str)
            case_summary["_label"] = raw_labels.map(CASE_LABELS).fillna(raw_labels)
        else:
            case_summary["_label"] = np.arange(len(case_summary)).astype(str)
        case_summary = (
            case_summary.groupby("_label", as_index=False)["mean_scrs"].mean().sort_values("mean_scrs", ascending=False)
        )
        case_summary = case_summary.sort_values("mean_scrs", ascending=True)
        y_cases = np.arange(len(case_summary))
        ax2.barh(y_cases, case_summary["mean_scrs"], color=COLORS["orange"], height=0.68)
        ax2.set_yticks(y_cases)
        case_label_size = 5.8 if len(case_summary) > 10 else 6.2
        ax2.set_yticklabels([wrap_label(label, 20) for label in case_summary["_label"]], fontsize=case_label_size, color=COLORS["text"])
        ax2.set_xlim(0, 1.05)
        ax2.set_xlabel("Mean SCRS")
        ax2.set_title(f"{tag} case view", loc="left", fontweight="bold", color=COLORS["text"], pad=5)
        ax2.grid(axis="x", color=COLORS["light_gray"], lw=0.6)

        if "condition" in cells.columns:
            categories = list(dict.fromkeys(cells["condition"].map(short_condition)))
            x_values = cells["condition"].map(short_condition)
        elif "r" in cells.columns:
            categories = [f"r={value:g}" for value in sorted(pd.to_numeric(cells["r"], errors="coerce").dropna().unique())]
            x_values = pd.to_numeric(cells["r"], errors="coerce").map(lambda value: f"r={value:g}")
        else:
            categories = ["cells"]
            x_values = pd.Series(["cells"] * len(cells))
        category_index = {value: idx for idx, value in enumerate(categories)}
        x = x_values.map(category_index).astype(float).to_numpy()
        jitter = rng.uniform(-0.22, 0.22, size=len(cells))
        color_values = cells["source"].map({"real": COLORS["blue"], "synthetic": COLORS["pink"]}).fillna(COLORS["gray"])
        ax3.scatter(x + jitter, cells["scrs"], c=color_values, s=10, alpha=0.72, edgecolors="none")
        grouped = cells.assign(_cat=x_values).groupby("_cat")["scrs"].mean()
        for label, value in grouped.items():
            if label in category_index:
                ax3.plot(category_index[label], value, marker="_", ms=18, mew=1.4, color=COLORS["text"])
        ax3.set_xticks(np.arange(len(categories)))
        ax3.set_xticklabels([wrap_label(label, 18) for label in categories], fontsize=6.3, color=COLORS["text"])
        ax3.set_ylim(-0.02, 1.05)
        ax3.set_ylabel("Cell SCRS tail cooperation")
        ax3.set_title(f"{tag} cell view", loc="left", fontweight="bold", color=COLORS["text"], pad=5)
        ax3.grid(axis="y", color=COLORS["light_gray"], lw=0.6)
        ax3.text(0.99, 0.06, "black ticks show category means", transform=ax3.transAxes, ha="right", fontsize=6.2, color=COLORS["text"])

        save_supplement(fig, f"sfig_{tag.lower()}_complete_views", [source_file, case_file, cell_file], manifest)
        plt.close(fig)


def write_manifest(rows: list[dict[str, str]]) -> None:
    path = FIGURES / "figure_manifest.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["figure", "outputs", "source_data"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    plt, patches, cmap_factory = configure_matplotlib()
    manifest: list[dict[str, str]] = []
    make_fig1(plt, patches, manifest)
    make_fig2(plt, manifest)
    make_fig3(plt, manifest)
    make_fig4(plt, cmap_factory, manifest)
    make_fig5(plt, manifest)
    make_supplementary_figures(plt, manifest)
    write_manifest(manifest)
    print(f"Wrote {len(manifest)} figures to {FIGURES}")


if __name__ == "__main__":
    main()
