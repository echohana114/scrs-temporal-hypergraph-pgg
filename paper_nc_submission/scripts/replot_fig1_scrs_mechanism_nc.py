#!/usr/bin/env python3
"""Draw a dense system-architecture schematic for SCRS Fig. 1."""

from __future__ import annotations

import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/mpl_scrs_fig1_nc")
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.path import Path as MplPath
from matplotlib import patches


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"

COOP = "#006B5F"
COOP_LIGHT = "#DFF0EC"
FLOW_AMBER = "#D6922A"
DEFECT = "#B23A48"
DEFECT_LIGHT = "#F4E0E2"
CONTEXT = "#496F9E"
CONTEXT_LIGHT = "#E5EEF7"
CHARCOAL = "#263238"
NAVY = "#1A365D"
SLATE = "#60717B"
GRID = "#D7DEE4"
PALE = "#F7F9FA"
WIRE = "#AAB7C1"

PANEL_A = (42, 38, 700, 462)
PANEL_B = (756, 38, 772, 462)
PANEL_C = (42, 538, 1486, 318)


def setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "axes.linewidth": 0.45,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
            "mathtext.fontset": "stixsans",
        }
    )


def panel_label(ax, x: float, y: float, letter: str, title: str) -> None:
    baseline_y = y + 15
    ax.text(x, baseline_y, letter, fontsize=7.2, fontweight="bold", ha="left", va="baseline", color=CHARCOAL)
    ax.text(x + 22, baseline_y, title, fontsize=5.9, fontweight="bold", ha="left", va="baseline", color=CHARCOAL)


def node(ax, x: float, y: float, label: str, color: str, *, r: float = 12, alpha: float = 1.0, z: int = 10) -> None:
    ax.add_patch(patches.Circle((x, y), r, facecolor=color, edgecolor="white", linewidth=0.95, alpha=alpha, zorder=z))
    if label:
        ax.text(x, y + 0.2, label, ha="center", va="center", fontsize=4.3, fontweight="bold", color="white", alpha=alpha, zorder=z + 1)


def arrow(
    ax,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = SLATE,
    lw: float = 0.9,
    alpha: float = 0.9,
    rad: float = 0.0,
    style: str = "-|>",
    ms: float = 8.0,
    z: int = 8,
) -> None:
    ax.add_patch(
        patches.FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=ms,
            connectionstyle=f"arc3,rad={rad}",
            linewidth=lw,
            color=color,
            alpha=alpha,
            shrinkA=2,
            shrinkB=2,
            zorder=z,
        )
    )


def orthogonal_dashed_arrowhead(
    ax,
    *,
    tip: tuple[float, float],
    direction: str,
    color: str,
    size: float = 12,
    alpha: float = 0.72,
    z: int = 9,
) -> None:
    x, y = tip
    half = size * 0.45
    if direction == "up":
        pts = [(x, y), (x - half, y + size), (x + half, y + size)]
    elif direction == "right":
        pts = [(x, y), (x - size, y - half), (x - size, y + half)]
    else:
        raise ValueError(f"Unsupported arrowhead direction: {direction}")
    ax.add_patch(patches.Polygon(pts, closed=True, facecolor=color, edgecolor=color, linewidth=0, alpha=alpha, zorder=z))


def dashed_path(ax, points: list[tuple[float, float]], *, color: str, lw: float, alpha: float, z: int) -> None:
    path = MplPath(points, [MplPath.MOVETO] + [MplPath.LINETO] * (len(points) - 1))
    ax.add_patch(
        patches.PathPatch(
            path,
            facecolor="none",
            edgecolor=color,
            linewidth=lw,
            linestyle=(0, (3, 2)),
            alpha=alpha,
            capstyle="butt",
            joinstyle="miter",
            zorder=z,
        )
    )


def rounded(ax, x: float, y: float, w: float, h: float, *, fc: str = "white", ec: str = GRID, lw: float = 0.8, r: float = 9, z: int = 1, alpha: float = 1.0) -> None:
    ax.add_patch(
        patches.FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle=f"round,pad=0.02,rounding_size={r}",
            facecolor=fc,
            edgecolor=ec,
            linewidth=lw,
            alpha=alpha,
            zorder=z,
        )
    )


def draw_outer_cards(ax) -> None:
    for x, y, w, h in (PANEL_A, PANEL_B, PANEL_C):
        rounded(ax, x, y, w, h, fc="#FBFCFD", ec="#CCD9E1", lw=0.72, r=8, z=0.25, alpha=0.96)
    ax.add_patch(
        patches.FancyBboxPatch(
            (PANEL_A[0], PANEL_A[1]),
            PANEL_A[2],
            PANEL_A[3],
            boxstyle="round,pad=0.02,rounding_size=8",
            facecolor="none",
            edgecolor="#BBD4D0",
            linewidth=0.42,
            alpha=0.55,
            zorder=0.35,
        )
    )


def interp(a: tuple[float, float], b: tuple[float, float], t: float) -> tuple[float, float]:
    return a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t


def plane_point(pts: list[tuple[float, float]], u: float, v: float) -> tuple[float, float]:
    p0, p1, p2, p3 = pts
    a = interp(p0, p1, u)
    b = interp(p3, p2, u)
    return interp(a, b, v)


def draw_plane(ax, pts: list[tuple[float, float]], *, label: str, alpha: float, edge: str, z: int) -> None:
    ax.add_patch(patches.Polygon(pts, closed=True, facecolor="#F5F8FA", edgecolor=edge, linewidth=0.8, alpha=alpha, zorder=z))
    for t in (0.18, 0.36, 0.54, 0.72, 0.90):
        a = plane_point(pts, t, 0)
        b = plane_point(pts, t, 1)
        c = plane_point(pts, 0, t)
        d = plane_point(pts, 1, t)
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#DCE4EA", lw=0.45, alpha=alpha, zorder=z + 1)
        ax.plot([c[0], d[0]], [c[1], d[1]], color="#DCE4EA", lw=0.45, alpha=alpha, zorder=z + 1)
    strong_layer = label in {r"$t$", r"$t+1$"}
    label_color = FLOW_AMBER if label == r"$t+1$" else NAVY if strong_layer else SLATE
    ax.text(
        pts[1][0] + 6,
        pts[1][1] - 2,
        label,
        fontsize=4.8,
        fontweight="bold" if strong_layer else "normal",
        color=label_color,
        zorder=z + 4,
    )


def draw_hull(ax, pts: list[tuple[float, float]], indices: list[int], *, color: str, fc: str, lw: float, alpha: float, z: int) -> None:
    hull = [pts[i] for i in indices]
    ax.add_patch(patches.Polygon(hull, closed=True, facecolor=fc, edgecolor=color, linewidth=lw, alpha=alpha, zorder=z))


def draw_temporal_stack(ax) -> None:
    panel_label(ax, 64, 56, "a", "Dense temporal hypergraph layer")
    ax.text(88, 98, "layered temporal stack with group-level exposure signals", fontsize=4.7, color=SLATE)

    base = [(104, 258), (404, 176), (574, 306), (260, 408)]
    offsets = [(-32, 38), (0, 0), (34, -38)]
    labels = [r"$t-1$", r"$t$", r"$t+1$"]
    alphas = [0.35, 0.78, 0.35]
    zorders = [1, 8, 4]
    layer_edges = ["#9FB5C8", CONTEXT, FLOW_AMBER]

    uv_nodes = [
        (0.10, 0.22, "C"), (0.26, 0.18, "C"), (0.43, 0.20, "D"), (0.62, 0.19, "C"), (0.82, 0.22, ""),
        (0.18, 0.45, ""), (0.34, 0.42, "D"), (0.52, 0.44, "C"), (0.72, 0.43, "D"), (0.88, 0.47, "C"),
        (0.14, 0.68, "C"), (0.31, 0.70, ""), (0.50, 0.68, "D"), (0.70, 0.69, "C"), (0.84, 0.72, ""),
    ]

    current_positions: list[tuple[float, float, str]] = []
    for li, (dx, dy) in enumerate(offsets):
        pts = [(x + dx, y + dy) for x, y in base]
        draw_plane(ax, pts, label=labels[li], alpha=alphas[li], edge=layer_edges[li], z=zorders[li])
        positions = [(plane_point(pts, u, v), lab) for u, v, lab in uv_nodes]

        hulls = [([0, 1, 6, 10, 5], COOP, COOP_LIGHT), ([2, 3, 8, 12, 7], CONTEXT, CONTEXT_LIGHT), ([7, 9, 13, 12], DEFECT, DEFECT_LIGHT)]
        for hi, (idxs, color, fc) in enumerate(hulls):
            draw_hull(ax, [p for p, _ in positions], idxs, color=color, fc=fc, lw=1.4 if li == 1 and hi == 1 else 0.8, alpha=0.42 if li == 1 else 0.18, z=zorders[li] + 2)

        for a, b in [(0, 1), (1, 3), (3, 8), (6, 7), (7, 8), (8, 9), (10, 12), (12, 13), (5, 10), (2, 7), (4, 9), (11, 13)]:
            p1, p2 = positions[a][0], positions[b][0]
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=WIRE, lw=0.45, alpha=0.65 if li == 1 else 0.30, zorder=zorders[li] + 3)

        for p, lab in positions:
            if li == 1:
                color = COOP if lab == "C" else DEFECT if lab == "D" else "#9EADB5"
                node(ax, p[0], p[1], lab, color, r=10.5 if lab else 6.2, alpha=1.0 if lab else 0.58, z=zorders[li] + 7)
                current_positions.append((p[0], p[1], lab))
            else:
                color = COOP if lab == "C" else DEFECT if lab == "D" else "#B9C5CA"
                node(ax, p[0], p[1], "" if lab else "", color, r=4.8, alpha=0.40, z=zorders[li] + 5)

    # Temporal traces between corresponding nodes.
    for u, v, lab in uv_nodes[::2]:
        points = []
        for dx, dy in offsets:
            pts = [(x + dx, y + dy) for x, y in base]
            points.append(plane_point(pts, u, v))
        ax.plot([p[0] for p in points], [p[1] for p in points], color="#8EA3B5", lw=0.55, alpha=0.36, linestyle=(0, (2, 2)), zorder=20)

    draw_hud(ax, 547, 176)
    ax.text(
        PANEL_A[0] + PANEL_A[2] / 2,
        472,
        "Temporal hyperedges encode group contexts, not just pairwise contacts.",
        ha="center",
        fontsize=4.75,
        color=SLATE,
    )


def draw_hud(ax, x: float, y: float) -> None:
    hud_w = 178
    rounded(ax, x, y, hud_w, 210, fc="#FBFCFD", ec="#C7D3DD", lw=0.75, r=8, z=20, alpha=0.96)
    ax.text(x + 12, y + 22, "exposure HUD", fontsize=4.55, fontweight="bold", color=CHARCOAL, zorder=21)
    ax.text(
        x + hud_w - 13,
        y + 78,
        r"$G_e(t)$",
        fontsize=4.55,
        fontweight="bold",
        ha="right",
        va="center",
        color=CONTEXT,
        bbox={"facecolor": "#FBFCFD", "edgecolor": "none", "pad": 0.1, "alpha": 0.96},
        zorder=24,
    )
    vals = [0.28, 0.63, 0.86, 0.52, 0.34, 0.77, 0.48]
    sx = [x + 14 + i * 20 for i in range(len(vals))]
    sy = [y + 69 - v * 38 for v in vals]
    ax.plot(sx, sy, color=CONTEXT, lw=1.0, zorder=22)
    ax.fill_between(sx, sy, [y + 72] * len(vals), color=CONTEXT, alpha=0.10, zorder=21)
    for i, v in enumerate(vals):
        ax.add_patch(patches.Rectangle((x + 18 + i * 19, y + 102), 8, 62 * v, facecolor=CONTEXT if i == 2 else "#AEBBC4", edgecolor="none", alpha=0.88, zorder=22))
    for i in range(4):
        yy = y + 185 + i * 7
        ax.plot([x + 16, x + hud_w - 24], [yy, yy], color="#E1E7EC", lw=0.55, zorder=21)
        ax.add_patch(patches.Rectangle((x + 16, yy - 2), 16 + i * 17, 3, facecolor=COOP if i % 2 else CONTEXT, edgecolor="none", alpha=0.60, zorder=22))
    ax.text(x + 18, y + 170, "ranked contexts", fontsize=4.05, color=SLATE, zorder=22)


def draw_matrix_filter(ax) -> None:
    panel_label(ax, 760, 56, "b", "Matrix role filter / spatial masking gate")
    ax.text(784, 98, "strategy state vectors are gated by cooperation-conditioned eligibility", fontsize=4.7, color=SLATE)

    # Bypass/control path.
    rounded(ax, 782, 130, 720, 340, fc="white", ec="#D2DAE2", lw=0.8, r=11, z=1)
    ax.text(804, 160, "input role-state field", fontsize=5.0, fontweight="bold", color=CHARCOAL)
    ax.text(1282, 160, "candidate pool", fontsize=5.0, fontweight="bold", color=CHARCOAL)

    x_input = 832
    ys = [218, 262, 306, 350, 394]
    labels = ["C", "D", "C", "D", "C"]
    colors = [COOP, DEFECT, COOP, DEFECT, COOP]
    for y, lab, col in zip(ys, labels, colors):
        node(ax, x_input, y, lab, col, r=13.0 if lab == "C" else 12.0, alpha=1.0)
        ax.plot([x_input + 18, 1005], [y, y], color=col if lab == "C" else SLATE, lw=0.85, alpha=0.90 if lab == "C" else 0.28, zorder=5)

    # Tensor/matrix mask.
    mx, my = 1018, 184
    cw, ch = 26, 25
    mask_center_x = mx - 8 + (6 * cw + 5) / 2
    ax.text(
        mask_center_x,
        my - 16,
        r"$M_{ij}(e^\star,t)$ role mask",
        ha="center",
        va="center",
        fontsize=4.35,
        color=CONTEXT,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.08, "alpha": 0.92},
        zorder=8,
    )
    for row in range(6):
        for col in range(6):
            active = (row, col) in {(0, 1), (1, 3), (2, 2), (3, 4), (4, 0), (4, 5)}
            fc = CONTEXT_LIGHT if not active else "#C9D9EA"
            ax.add_patch(patches.Rectangle((mx + col * cw, my + row * ch), cw - 3, ch - 3, facecolor=fc, edgecolor="#FFFFFF", linewidth=0.45, zorder=4))
    ax.add_patch(patches.Rectangle((mx - 8, my - 8), 6 * cw + 5, 6 * ch + 5, facecolor="none", edgecolor=CONTEXT, linewidth=0.85, linestyle=(0, (2, 2)), zorder=6))

    gate_x = mx + 6 * cw + 36
    for y, lab, col in zip(ys, labels, colors):
        if lab == "C":
            arrow(ax, (mx + 6 * cw + 12, y), (gate_x + 82, y), color=COOP, lw=1.05, alpha=0.92, ms=8.0)
        else:
            ax.add_patch(
                patches.FancyArrowPatch(
                    (mx + 6 * cw + 12, y),
                    (gate_x + 50, y),
                    arrowstyle="-|>",
                    mutation_scale=6.2,
                    linewidth=0.75,
                    linestyle=(0, (2.0, 2.0)),
                    color=SLATE,
                    alpha=0.40,
                    shrinkA=1,
                    shrinkB=1,
                    zorder=6,
                )
            )
            ax.plot([gate_x + 56, gate_x + 68], [y - 6, y + 6], color=DEFECT, lw=0.85, alpha=0.82, zorder=7)
            ax.plot([gate_x + 56, gate_x + 68], [y + 6, y - 6], color=DEFECT, lw=0.85, alpha=0.82, zorder=7)

    # Candidate pool and output bus.
    rounded(ax, 1282, 198, 112, 208, fc=COOP_LIGHT, ec="#B8D8D1", lw=0.8, r=13, z=3)
    for yy in [232, 292, 358]:
        node(ax, 1324 if yy != 292 else 1354, yy, "C", COOP, r=12.0)
    ax.text(1338, 430, "cooperative role-model pool", ha="center", fontsize=4.35, color=COOP)
    arrow(ax, (1398, 302), (1468, 302), color=COOP, lw=1.25, ms=9)

    # Minimal unfiltered control trace.
    node(ax, 930, 448, "D", DEFECT, r=11, alpha=0.65)
    arrow(ax, (944, 448), (1089, 448), color=DEFECT, lw=0.9, alpha=0.55, rad=-0.18)
    ax.text(944, 428, "unfiltered bypass", fontsize=4.25, color=DEFECT)
    ax.add_patch(patches.FancyBboxPatch((1100, 428), 44, 36, boxstyle="round,pad=0.02,rounding_size=5", facecolor=DEFECT_LIGHT, edgecolor="#D8A4AA", linewidth=0.7, zorder=5))
    ax.plot([1110, 1120, 1130, 1138], [454, 440, 448, 435], color=DEFECT, lw=0.9, zorder=6)


def gradient_track(ax, x: float, y: float, w: float, h: float) -> None:
    steps = 160
    for i in range(steps):
        t = i / (steps - 1)
        if t < 0.42:
            c1, c2 = (73, 111, 158), (73, 111, 158)
        elif t < 0.70:
            c1, c2 = (73, 111, 158), (0, 107, 95)
        else:
            c1, c2 = (0, 107, 95), (38, 50, 56)
        local = t if t < 0.42 else (t - 0.42) / 0.58
        rgb = tuple(int(c1[j] * (1 - local) + c2[j] * local) for j in range(3))
        col = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
        ax.add_patch(patches.Rectangle((x + w * i / steps, y), w / steps + 1, h, facecolor=col, edgecolor="none", alpha=0.84, zorder=2))
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=15", facecolor="none", edgecolor="#B9C5CC", linewidth=0.65, zorder=4))


def equation_card(
    ax,
    x: float,
    y: float,
    w: float,
    step: str,
    title: str,
    eq: str | tuple[str, str],
    accent: str,
    *,
    connector_x: float | None = None,
) -> None:
    line_x = x + w / 2 if connector_x is None else connector_x
    ax.plot([line_x, line_x], [y - 38, y - 8], color="#9EABB3", lw=0.55, linestyle=(0, (1.6, 2.0)), zorder=5)
    rounded(ax, x, y, w, 92, fc="white", ec="#D8E0E5", lw=0.75, r=8, z=5)
    ax.add_patch(patches.Rectangle((x, y), 3.5, 92, facecolor=accent, edgecolor="none", alpha=0.90, zorder=6))
    ax.text(x + 15, y + 20, step, fontsize=4.5, fontweight="bold", color=accent, zorder=7)
    ax.text(x + 36, y + 20, title, fontsize=4.9, fontweight="bold", color=CHARCOAL, zorder=7)
    if isinstance(eq, tuple):
        ax.text(x + w / 2, y + 55, eq[0], ha="center", va="center", fontsize=5.55, fontweight="bold", color=CHARCOAL, zorder=7)
        ax.text(x + w / 2, y + 78, eq[1], ha="center", va="center", fontsize=5.55, fontweight="bold", color=CHARCOAL, zorder=7)
    else:
        ax.text(x + w / 2, y + 64, eq, ha="center", va="center", fontsize=5.55, fontweight="bold", color=CHARCOAL, zorder=7)


def draw_pipeline(ax) -> None:
    panel_label(ax, 64, 552, "c", "Continuous signal flow and mathematical pipeline")
    x0, y0, w, h = 120, 632, 1355, 28
    gradient_track(ax, x0, y0, w, h)

    milestones = [x0 + 90, x0 + 455, x0 + 825, x0 + 1190]
    labels = ["Observe", "Sample", "Screen", "Update"]
    accents = [CONTEXT, CONTEXT, COOP, CHARCOAL]
    for x, lab, acc in zip(milestones, labels, accents):
        ax.add_patch(patches.Circle((x, y0 + h / 2), 13, facecolor="white", edgecolor=acc, linewidth=1.1, zorder=8))
        ax.add_patch(patches.Circle((x, y0 + h / 2), 5.0, facecolor=acc, edgecolor="none", zorder=9))
        ax.text(x, y0 - 23, lab, ha="center", fontsize=4.8, fontweight="bold", color=CHARCOAL, zorder=9)

    card_shift = 32
    cards = [
        (milestones[0] - 175 + card_shift, 705, 350, "1", "Observe local group", r"$P_i(t)=\sum_{e\ni i}[r\,n_C(e,t)-s_i(t)]$", CONTEXT),
        (milestones[1] - 175 + card_shift, 705, 350, "2", "Sample context", r"$G_e(t)=q_e(t)\max\{0,r\,n_C(e,t)-1\}$", CONTEXT),
        (
            milestones[2] - 175 + card_shift,
            705,
            350,
            "3",
            "Screen roles",
            (r"$\mathcal{C}_i(e^\star,t)=\{j\in e^\star:$", r"$s_j(t)=1,\ j\ne i\}$"),
            COOP,
        ),
        (
            milestones[3] - 175 + card_shift,
            705,
            350,
            "4",
            "Update strategy",
            (r"$\Pr(i\leftarrow j)=[1+\exp\{-\beta\Delta P\}]^{-1}$", r"$\Delta P=P_j-P_i$"),
            CHARCOAL,
        ),
    ]
    for card, anchor_x in zip(cards, milestones):
        equation_card(ax, *card, connector_x=anchor_x)

    observe_left = (milestones[0] - 13, y0 + h / 2)
    sampling_tip = observe_left
    dashed_path(
        ax,
        [
            (PANEL_A[0] + 40, PANEL_A[1] + PANEL_A[3]),
            (PANEL_A[0] + 40, 520),
            (28, 520),
            (28, sampling_tip[1]),
            (sampling_tip[0] - 14, sampling_tip[1]),
        ],
        color=FLOW_AMBER,
        lw=0.8,
        alpha=0.62,
        z=6,
    )
    orthogonal_dashed_arrowhead(ax, tip=sampling_tip, direction="right", color=FLOW_AMBER, size=13, alpha=0.70, z=9)

    # Feedback loop from update back toward temporal observation.
    update_right = (milestones[3] + 13, y0 + h / 2)
    feedback_anchor_x = PANEL_A[0] + PANEL_A[2] - 40
    feedback_bus_y = 532
    feedback_tip = (feedback_anchor_x, PANEL_A[1] + PANEL_A[3])
    dashed_path(
        ax,
        [
            update_right,
            (1370, update_right[1]),
            (1370, feedback_bus_y),
            (feedback_anchor_x, feedback_bus_y),
            (feedback_anchor_x, feedback_tip[1] + 16),
        ],
        color=FLOW_AMBER,
        lw=0.9,
        alpha=0.62,
        z=6,
    )
    orthogonal_dashed_arrowhead(ax, tip=feedback_tip, direction="up", color=FLOW_AMBER, size=15, alpha=0.70, z=9)
    ax.text(
        1030,
        521,
        "endogenous feedback",
        ha="center",
        va="bottom",
        fontsize=4.45,
        color=FLOW_AMBER,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.35, "alpha": 0.96},
        zorder=30,
    )
    ax.text(
        PANEL_C[0] + PANEL_C[2] / 2,
        828,
        "Successful-group context selects where the signal is sampled; role screening controls who transmits.",
        ha="center",
        fontsize=5.0,
        color=SLATE,
        style="italic",
    )


def draw_figure() -> plt.Figure:
    setup_style()
    fig, ax = plt.subplots(figsize=(180 / 25.4, 101.25 / 25.4))
    ax.set_xlim(0, 1650)
    ax.set_ylim(900, 0)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.add_patch(patches.Rectangle((0, 0), 1650, 900, facecolor="white", edgecolor="none", zorder=0))

    draw_outer_cards(ax)
    draw_temporal_stack(ax)
    draw_matrix_filter(ax)
    draw_pipeline(ax)
    return fig


def main() -> None:
    fig = draw_figure()
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "svg", "png", "eps"):
        kwargs = {"bbox_inches": "tight", "pad_inches": 0.02, "facecolor": "white"}
        if ext == "png":
            kwargs["dpi"] = 500
        fig.savefig(OUT / f"fig1_model_diagram.{ext}", **kwargs)
    plt.close(fig)
    print(f"Wrote architecture Fig. 1 to {OUT}")


if __name__ == "__main__":
    main()
