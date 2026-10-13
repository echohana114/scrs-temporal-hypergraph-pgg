#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


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

CASE_LABEL = {
    "synthetic_structured_ring": "Structured\nring",
    "synthetic_community": "Community\nsynthetic",
    "real_highschool2013": "High school\n2013",
    "real_workplace2013": "Workplace\n2013",
    "real_hospitalward2010": "Hospital ward\n2010",
    "real_sfhh2009": "SFHH\n2009",
}

CONTROL_LABEL = {
    "pnas": "PNAS",
    "csgc_gamma1": "CSGC",
    "csgc_gamma1_shuffled": "CSGC score shuffled",
    "scrs_gamma1_score_shuffled": "SCRS score shuffled",
    "scrs_gamma1_strategy_shuffled": "SCRS strategy shuffled",
}

PALETTE = {
    "text": "#1A1A1A",
    "muted": "#666666",
    "grid": "#E6E6E6",
    "axis": "#333333",
    "real": "#0072B2",
    "synthetic": "#CC79A7",
    "r07": "#0072B2",
    "r09": "#E69F00",
    "r10": "#009E73",
    "role": "#009E73",
    "score": "#8F8F8F",
    "strict": "#D55E00",
    "lfds": "#56B4E9",
    "zero": "#444444",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


FONT = {
    "title": font(40, True),
    "subtitle": font(24, False),
    "axis": font(24, False),
    "tick": font(20, False),
    "small": font(18, False),
    "legend": font(20, False),
    "panel": font(30, True),
}


def clean_label(value: str) -> str:
    return CASE_LABEL.get(value, value.replace("_", " "))


def fmt(value: float, digits: int = 4) -> str:
    return f"{float(value):.{digits}f}"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


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


def text_size(draw: ImageDraw.ImageDraw, text: str, image_font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.multiline_textbbox((0, 0), text, font=image_font, spacing=4, align="center")
    return int(box[2] - box[0]), int(box[3] - box[1])


def draw_centered(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    image_font: ImageFont.ImageFont,
    fill: str = PALETTE["text"],
    spacing: int = 4,
) -> None:
    width, height = text_size(draw, text, image_font)
    draw.multiline_text((xy[0] - width / 2, xy[1] - height / 2), text, font=image_font, fill=fill, spacing=spacing, align="center")


def draw_dashed_line(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float, float, float],
    fill: str,
    width: int = 2,
    dash: int = 10,
    gap: int = 7,
) -> None:
    x0, y0, x1, y1 = xy
    if abs(y0 - y1) < 1e-9:
        x = x0
        while x < x1:
            draw.line((x, y0, min(x + dash, x1), y1), fill=fill, width=width)
            x += dash + gap
    elif abs(x0 - x1) < 1e-9:
        y = y0
        while y < y1:
            draw.line((x0, y, x1, min(y + dash, y1)), fill=fill, width=width)
            y += dash + gap


def svg_text(x: float, y: float, text: str, size: int, weight: str = "400", anchor: str = "middle", fill: str = "#1A1A1A") -> str:
    lines = str(text).split("\n")
    if len(lines) == 1:
        return (
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
            f'font-family="Arial, Helvetica, sans-serif" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}">{esc(lines[0])}</text>'
        )
    tspans = []
    line_height = size * 1.18
    start = y - (len(lines) - 1) * line_height / 2
    for idx, line in enumerate(lines):
        tspans.append(f'<tspan x="{x:.1f}" y="{start + idx * line_height:.1f}">{esc(line)}</tspan>')
    return (
        f'<text text-anchor="{anchor}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">' + "".join(tspans) + "</text>"
    )


def svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#FFFFFF"/>',
    ]


def save_svg(path: Path, elements: Iterable[str]) -> None:
    path.write_text("\n".join([*elements, "</svg>\n"]), encoding="utf-8")


def y_scale(value: float, y_bottom: float, y_top: float, min_value: float, max_value: float) -> float:
    return y_bottom - (value - min_value) * (y_bottom - y_top) / (max_value - min_value)


def x_scale(index: int, count: int, x_left: float, x_right: float) -> float:
    step = (x_right - x_left) / count
    return x_left + step * (index + 0.5)


def figure_1_stability(cell: pd.DataFrame, figure_dir: Path) -> None:
    width, height = 1800, 1100
    x0, x1 = 130, width - 70
    y0, y1 = 150, height - 250
    ymin, ymax = 0.0, 1.05
    r_values = [0.7, 0.9, 1.0]
    colors = {0.7: PALETTE["r07"], 0.9: PALETTE["r09"], 1.0: PALETTE["r10"]}
    offsets = {0.7: -34, 0.9: 0, 1.0: 34}

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.text((70, 42), "Figure 1 | SCRS stability across formal cells", font=FONT["title"], fill=PALETTE["text"])
    draw.text(
        (70, 96),
        "Tail cooperation after 5000 steps; points show means over 50 repetitions and bars show approximate 95% CIs.",
        font=FONT["subtitle"],
        fill=PALETTE["muted"],
    )
    svg = svg_header(width, height)
    svg.append(svg_text(70, 76, "Figure 1 | SCRS stability across formal cells", 40, "700", "start"))
    svg.append(svg_text(70, 126, "Tail cooperation after 5000 steps; points show means over 50 repetitions and bars show approximate 95% CIs.", 24, "400", "start", PALETTE["muted"]))

    for tick in [0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        y = y_scale(tick, y1, y0, ymin, ymax)
        draw.line((x0, y, x1, y), fill=PALETTE["grid"], width=2)
        draw.text((70, y - 12), f"{tick:.1f}", font=FONT["tick"], fill=PALETTE["muted"])
        svg.append(f'<line x1="{x1:.1f}" x2="{x0:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{PALETTE["grid"]}" stroke-width="2"/>')
        svg.append(svg_text(98, y + 7, f"{tick:.1f}", 20, "400", "end", PALETTE["muted"]))

    for threshold, label, color in [(0.60, "empirical threshold", "#B3442F"), (0.95, "synthetic threshold", "#7A7A7A")]:
        y = y_scale(threshold, y1, y0, ymin, ymax)
        draw_dashed_line(draw, (x0, y, x1, y), color, 2)
        draw.text((x1 - 230, y - 28), label, font=FONT["small"], fill=color)
        svg.append(f'<line x1="{x0:.1f}" x2="{x1:.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="2" stroke-dasharray="10 7"/>')
        svg.append(svg_text(x1 - 10, y - 10, label, 18, "400", "end", color))

    draw.line((x0, y1, x1, y1), fill=PALETTE["axis"], width=3)
    draw.line((x0, y0, x0, y1), fill=PALETTE["axis"], width=3)
    svg.append(f'<line x1="{x0}" x2="{x1}" y1="{y1}" y2="{y1}" stroke="{PALETTE["axis"]}" stroke-width="3"/>')
    svg.append(f'<line x1="{x0}" x2="{x0}" y1="{y0}" y2="{y1}" stroke="{PALETTE["axis"]}" stroke-width="3"/>')

    lookup = cell.set_index(["case", "r"])
    for idx, case in enumerate(CASE_ORDER):
        base_x = x_scale(idx, len(CASE_ORDER), x0, x1)
        for r in r_values:
            row = lookup.loc[(case, r)]
            x = base_x + offsets[r]
            mean = float(row["scrs"])
            low = float(row["scrs_ci95_low"])
            high = float(row["scrs_ci95_high"])
            y_mean = y_scale(mean, y1, y0, ymin, ymax)
            y_low = y_scale(low, y1, y0, ymin, ymax)
            y_high = y_scale(high, y1, y0, ymin, ymax)
            draw.line((x, y_high, x, y_low), fill=colors[r], width=4)
            draw.line((x - 10, y_high, x + 10, y_high), fill=colors[r], width=4)
            draw.line((x - 10, y_low, x + 10, y_low), fill=colors[r], width=4)
            draw.ellipse((x - 11, y_mean - 11, x + 11, y_mean + 11), fill=colors[r], outline="white", width=3)
            svg.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y_high:.1f}" y2="{y_low:.1f}" stroke="{colors[r]}" stroke-width="4"/>')
            svg.append(f'<line x1="{x - 10:.1f}" x2="{x + 10:.1f}" y1="{y_high:.1f}" y2="{y_high:.1f}" stroke="{colors[r]}" stroke-width="4"/>')
            svg.append(f'<line x1="{x - 10:.1f}" x2="{x + 10:.1f}" y1="{y_low:.1f}" y2="{y_low:.1f}" stroke="{colors[r]}" stroke-width="4"/>')
            svg.append(f'<circle cx="{x:.1f}" cy="{y_mean:.1f}" r="11" fill="{colors[r]}" stroke="#FFFFFF" stroke-width="3"/>')
        draw_centered(draw, (base_x, height - 148), clean_label(case), FONT["axis"], PALETTE["text"])
        svg.append(svg_text(base_x, height - 154, clean_label(case), 24))

    sep_x = (x_scale(1, len(CASE_ORDER), x0, x1) + x_scale(2, len(CASE_ORDER), x0, x1)) / 2
    draw_dashed_line(draw, (sep_x, y0, sep_x, y1 + 32), PALETTE["grid"], 2)
    svg.append(f'<line x1="{sep_x:.1f}" x2="{sep_x:.1f}" y1="{y0}" y2="{y1 + 32}" stroke="{PALETTE["grid"]}" stroke-width="2" stroke-dasharray="9 8"/>')
    draw_centered(draw, ((x_scale(0, len(CASE_ORDER), x0, x1) + x_scale(1, len(CASE_ORDER), x0, x1)) / 2, height - 62), "Synthetic", FONT["legend"], PALETTE["muted"])
    draw_centered(draw, ((x_scale(2, len(CASE_ORDER), x0, x1) + x_scale(5, len(CASE_ORDER), x0, x1)) / 2, height - 62), "Empirical", FONT["legend"], PALETTE["muted"])
    svg.append(svg_text((x_scale(0, len(CASE_ORDER), x0, x1) + x_scale(1, len(CASE_ORDER), x0, x1)) / 2, height - 62, "Synthetic", 20, "400", "middle", PALETTE["muted"]))
    svg.append(svg_text((x_scale(2, len(CASE_ORDER), x0, x1) + x_scale(5, len(CASE_ORDER), x0, x1)) / 2, height - 62, "Empirical", 20, "400", "middle", PALETTE["muted"]))

    draw.text((30, 480), "Tail cooperation", font=FONT["axis"], fill=PALETTE["text"])
    for k, r in enumerate(r_values):
        lx = x1 - 330 + k * 105
        ly = 58
        draw.ellipse((lx, ly, lx + 22, ly + 22), fill=colors[r])
        draw.text((lx + 32, ly - 2), f"r={r:.1f}", font=FONT["legend"], fill=PALETTE["text"])
        svg.append(f'<circle cx="{lx + 11}" cy="{ly + 11}" r="11" fill="{colors[r]}"/>')
        svg.append(svg_text(lx + 35, ly + 18, f"r={r:.1f}", 20, "400", "start"))

    img.save(figure_dir / "fig1_scrs_stability_by_case.png", dpi=(300, 300))
    save_svg(figure_dir / "fig1_scrs_stability_by_case.svg", svg)


def build_gap_frame(source: pd.DataFrame, cell: pd.DataFrame) -> pd.DataFrame:
    rows = []
    lfds = cell.groupby("source")["gap_vs_lfds_strongest"].mean().to_dict()
    for row in source.itertuples(index=False):
        source_name = str(row.source)
        rows.extend(
            [
                {"source": source_name, "comparison": "PNAS", "gap": float(row.mean_gap_vs_pnas)},
                {"source": source_name, "comparison": "CSGC", "gap": float(row.mean_gap_vs_csgc)},
                {"source": source_name, "comparison": "LFDS\nstrongest", "gap": float(lfds[source_name])},
                {"source": source_name, "comparison": "Strategy\nshuffled", "gap": float(row.mean_gap_vs_strategy_shuffled)},
                {"source": source_name, "comparison": "Score\nshuffled", "gap": float(row.mean_gap_vs_score_shuffled)},
                {"source": source_name, "comparison": "Strict\nstrongest", "gap": float(row.mean_gap_vs_strongest)},
            ]
        )
    return pd.DataFrame(rows)


def figure_2_gap_bars(source: pd.DataFrame, cell: pd.DataFrame, figure_dir: Path) -> None:
    gap = build_gap_frame(source, cell)
    width, height = 1800, 1050
    x0, x1 = 140, width - 80
    y0, y1 = 150, height - 210
    ymin, ymax = -0.06, 0.72
    comparisons = ["PNAS", "CSGC", "LFDS\nstrongest", "Strategy\nshuffled", "Score\nshuffled", "Strict\nstrongest"]

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.text((70, 42), "Figure 2 | Performance gains and mechanism boundary", font=FONT["title"], fill=PALETTE["text"])
    draw.text((70, 96), "Bars show mean SCRS gaps against key controls across all cells within each source.", font=FONT["subtitle"], fill=PALETTE["muted"])
    svg = svg_header(width, height)
    svg.append(svg_text(70, 76, "Figure 2 | Performance gains and mechanism boundary", 40, "700", "start"))
    svg.append(svg_text(70, 126, "Bars show mean SCRS gaps against key controls across all cells within each source.", 24, "400", "start", PALETTE["muted"]))

    for tick in [-0.05, 0.0, 0.2, 0.4, 0.6]:
        y = y_scale(tick, y1, y0, ymin, ymax)
        color = PALETTE["zero"] if tick == 0 else PALETTE["grid"]
        width_line = 3 if tick == 0 else 2
        draw.line((x0, y, x1, y), fill=color, width=width_line)
        draw.text((55, y - 12), f"{tick:.2f}", font=FONT["tick"], fill=PALETTE["muted"])
        svg.append(f'<line x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="{width_line}"/>')
        svg.append(svg_text(102, y + 7, f"{tick:.2f}", 20, "400", "end", PALETTE["muted"]))

    draw.line((x0, y1, x1, y1), fill=PALETTE["axis"], width=3)
    draw.line((x0, y0, x0, y1), fill=PALETTE["axis"], width=3)
    svg.append(f'<line x1="{x0}" x2="{x1}" y1="{y1}" y2="{y1}" stroke="{PALETTE["axis"]}" stroke-width="3"/>')
    svg.append(f'<line x1="{x0}" x2="{x0}" y1="{y0}" y2="{y1}" stroke="{PALETTE["axis"]}" stroke-width="3"/>')

    bar_w = 48
    for idx, comp in enumerate(comparisons):
        center = x_scale(idx, len(comparisons), x0, x1)
        for source_name, dx, color in [("real", -bar_w / 1.7, PALETTE["real"]), ("synthetic", bar_w / 1.7, PALETTE["synthetic"])]:
            value = float(gap[(gap["source"] == source_name) & (gap["comparison"] == comp)]["gap"].iloc[0])
            y_value = y_scale(value, y1, y0, ymin, ymax)
            y_zero = y_scale(0, y1, y0, ymin, ymax)
            left = center + dx - bar_w / 2
            right = center + dx + bar_w / 2
            top, bottom = min(y_value, y_zero), max(y_value, y_zero)
            draw.rectangle((left, top, right, bottom), fill=color)
            label_y = top - 28 if value >= 0 else bottom + 8
            draw_centered(draw, (center + dx, label_y), f"{value:.3f}", FONT["small"], PALETTE["text"])
            svg.append(f'<rect x="{left:.1f}" y="{top:.1f}" width="{bar_w:.1f}" height="{bottom - top:.1f}" fill="{color}"/>')
            svg.append(svg_text(center + dx, label_y + 6, f"{value:.3f}", 18))
        draw_centered(draw, (center, height - 124), comp, FONT["axis"], PALETTE["text"])
        svg.append(svg_text(center, height - 130, comp, 24))

    draw.text((70, 918), "Positive values favor SCRS. The near-zero score-shuffled and strict gaps set the claim boundary.", font=FONT["subtitle"], fill=PALETTE["muted"])
    svg.append(svg_text(70, 938, "Positive values favor SCRS. The near-zero score-shuffled and strict gaps set the claim boundary.", 24, "400", "start", PALETTE["muted"]))
    for k, (source_name, color) in enumerate([("Empirical", PALETTE["real"]), ("Synthetic", PALETTE["synthetic"])]):
        lx, ly = width - 380 + k * 180, 58
        draw.rectangle((lx, ly, lx + 32, ly + 20), fill=color)
        draw.text((lx + 42, ly - 2), source_name, font=FONT["legend"], fill=PALETTE["text"])
        svg.append(f'<rect x="{lx}" y="{ly}" width="32" height="20" fill="{color}"/>')
        svg.append(svg_text(lx + 42, ly + 16, source_name, 20, "400", "start"))

    img.save(figure_dir / "fig2_performance_mechanism_gaps.png", dpi=(300, 300))
    save_svg(figure_dir / "fig2_performance_mechanism_gaps.svg", svg)
    gap.to_csv(figure_dir.parent / "data" / "figure2_source_gap_values.csv", index=False)


def mix(c1: str, c2: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    a = tuple(int(c1[i : i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(c2[i : i + 2], 16) for i in (1, 3, 5))
    out = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return f"#{out[0]:02X}{out[1]:02X}{out[2]:02X}"


def diverging(value: float, limit: float = 0.025) -> str:
    clipped = max(-limit, min(limit, value))
    if clipped < 0:
        return mix("#F7F7F7", "#0072B2", abs(clipped) / limit)
    return mix("#F7F7F7", "#D55E00", clipped / limit)


def sequential(value: float, max_value: float) -> str:
    return mix("#EEF6F2", PALETTE["role"], value / max_value if max_value else 0.0)


def figure_3_heatmaps(cell: pd.DataFrame, figure_dir: Path) -> None:
    real_cases = ["real_highschool2013", "real_workplace2013", "real_hospitalward2010", "real_sfhh2009"]
    r_values = [0.7, 0.9, 1.0]
    width, height = 1800, 950
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.text((70, 42), "Figure 3 | Mechanism separation in empirical data", font=FONT["title"], fill=PALETTE["text"])
    draw.text((70, 96), "Cell values show SCRS gaps against the two SCRS ablations.", font=FONT["subtitle"], fill=PALETTE["muted"])
    svg = svg_header(width, height)
    svg.append(svg_text(70, 76, "Figure 3 | Mechanism separation in empirical data", 40, "700", "start"))
    svg.append(svg_text(70, 126, "Cell values show SCRS gaps against the two SCRS ablations.", 24, "400", "start", PALETTE["muted"]))

    panels = [
        ("A", "Role-screening signal", "gap_vs_scrs_strategy_shuffled", "sequential"),
        ("B", "Edge-score contribution", "gap_vs_scrs_score_shuffled", "diverging"),
    ]
    cell_w, cell_h = 170, 100
    panel_x = [260, 1010]
    panel_y = 220
    lookup = cell.set_index(["case", "r"])

    for panel_idx, (letter, title, column, cmap) in enumerate(panels):
        px = panel_x[panel_idx]
        draw.text((px - 210, panel_y - 76), letter, font=FONT["panel"], fill=PALETTE["text"])
        draw.text((px - 160, panel_y - 72), title, font=FONT["subtitle"], fill=PALETTE["text"])
        svg.append(svg_text(px - 210, panel_y - 50, letter, 30, "700", "start"))
        svg.append(svg_text(px - 160, panel_y - 50, title, 24, "400", "start"))
        for cidx, r in enumerate(r_values):
            draw_centered(draw, (px + cidx * cell_w + cell_w / 2, panel_y - 30), f"r={r:.1f}", FONT["axis"], PALETTE["text"])
            svg.append(svg_text(px + cidx * cell_w + cell_w / 2, panel_y - 24, f"r={r:.1f}", 24))
        for ridx, case in enumerate(real_cases):
            y = panel_y + ridx * cell_h
            draw_centered(draw, (px - 95, y + cell_h / 2), clean_label(case), FONT["tick"], PALETTE["text"])
            svg.append(svg_text(px - 95, y + cell_h / 2 + 7, clean_label(case), 20))
            for cidx, r in enumerate(r_values):
                value = float(lookup.loc[(case, r), column])
                color = sequential(value, 1.0) if cmap == "sequential" else diverging(value)
                x = px + cidx * cell_w
                draw.rectangle((x, y, x + cell_w, y + cell_h), fill=color, outline="white", width=4)
                draw_centered(draw, (x + cell_w / 2, y + cell_h / 2), f"{value:+.3f}", FONT["axis"], PALETTE["text"])
                svg.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{color}" stroke="#FFFFFF" stroke-width="4"/>')
                svg.append(svg_text(x + cell_w / 2, y + cell_h / 2 + 8, f"{value:+.3f}", 24))

    draw.text((70, 805), "Large positive role-screening gaps are paired with near-zero score-shuffled gaps.", font=FONT["subtitle"], fill=PALETTE["muted"])
    svg.append(svg_text(70, 825, "Large positive role-screening gaps are paired with near-zero score-shuffled gaps.", 24, "400", "start", PALETTE["muted"]))
    img.save(figure_dir / "fig3_empirical_mechanism_heatmaps.png", dpi=(300, 300))
    save_svg(figure_dir / "fig3_empirical_mechanism_heatmaps.svg", svg)


def figure_s1_strict_boundary(cell: pd.DataFrame, figure_dir: Path) -> None:
    width, height = 1600, 950
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    draw.text((70, 42), "Supplementary Fig. 1 | Gap against strongest strict control", font=FONT["title"], fill=PALETTE["text"])
    draw.text((70, 96), "Values near zero show where score-shuffled SCRS matches SCRS.", font=FONT["subtitle"], fill=PALETTE["muted"])
    svg = svg_header(width, height)
    svg.append(svg_text(70, 76, "Supplementary Fig. 1 | Gap against strongest strict control", 40, "700", "start"))
    svg.append(svg_text(70, 126, "Values near zero show where score-shuffled SCRS matches SCRS.", 24, "400", "start", PALETTE["muted"]))

    x0, y0 = 360, 220
    cell_w, cell_h = 220, 88
    r_values = [0.7, 0.9, 1.0]
    lookup = cell.set_index(["case", "r"])
    for cidx, r in enumerate(r_values):
        draw_centered(draw, (x0 + cidx * cell_w + cell_w / 2, y0 - 34), f"r={r:.1f}", FONT["axis"], PALETTE["text"])
        svg.append(svg_text(x0 + cidx * cell_w + cell_w / 2, y0 - 28, f"r={r:.1f}", 24))
    for ridx, case in enumerate(CASE_ORDER):
        y = y0 + ridx * cell_h
        draw_centered(draw, (x0 - 140, y + cell_h / 2), clean_label(case), FONT["tick"], PALETTE["text"])
        svg.append(svg_text(x0 - 140, y + cell_h / 2 + 7, clean_label(case), 20))
        for cidx, r in enumerate(r_values):
            value = float(lookup.loc[(case, r), "gap_vs_strongest"])
            color = diverging(value)
            x = x0 + cidx * cell_w
            draw.rectangle((x, y, x + cell_w, y + cell_h), fill=color, outline="white", width=4)
            draw_centered(draw, (x + cell_w / 2, y + cell_h / 2), f"{value:+.4f}", FONT["axis"], PALETTE["text"])
            svg.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{color}" stroke="#FFFFFF" stroke-width="4"/>')
            svg.append(svg_text(x + cell_w / 2, y + cell_h / 2 + 8, f"{value:+.4f}", 24))
    draw.text((70, 825), "Positive cells favor SCRS; negative cells favor the strongest matched control in that case-r cell.", font=FONT["subtitle"], fill=PALETTE["muted"])
    svg.append(svg_text(70, 845, "Positive cells favor SCRS; negative cells favor the strongest matched control in that case-r cell.", 24, "400", "start", PALETTE["muted"]))
    img.save(figure_dir / "figS1_strict_control_gap_heatmap.png", dpi=(300, 300))
    save_svg(figure_dir / "figS1_strict_control_gap_heatmap.svg", svg)


def markdown_table(df: pd.DataFrame) -> str:
    columns = list(df.columns)
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
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
    source_table = source.assign(
        Source=source["source"].map({"real": "Empirical", "synthetic": "Synthetic"}),
        **{
            "SCRS mean": source["mean_scrs"].map(lambda x: fmt(x)),
            "SCRS min": source["min_scrs"].map(lambda x: fmt(x)),
            "Max SE": source["max_scrs_se"].map(lambda x: fmt(x)),
            "Gap vs PNAS": source["mean_gap_vs_pnas"].map(lambda x: fmt(x)),
            "Gap vs CSGC": source["mean_gap_vs_csgc"].map(lambda x: fmt(x)),
            "Gap vs strategy shuffled": source["mean_gap_vs_strategy_shuffled"].map(lambda x: fmt(x)),
            "Gap vs score shuffled": source["mean_gap_vs_score_shuffled"].map(lambda x: fmt(x)),
            "Strict wins": source.apply(lambda r: f"{int(r.strict_wins)}/{int(r.cells)}", axis=1),
        },
    )[
        [
            "Source",
            "SCRS mean",
            "SCRS min",
            "Max SE",
            "Gap vs PNAS",
            "Gap vs CSGC",
            "Gap vs strategy shuffled",
            "Gap vs score shuffled",
            "Strict wins",
        ]
    ]
    case_table = case.assign(
        Dataset=case["case"].map(lambda x: clean_label(x).replace("\n", " ")),
        Source=case["source"].map({"real": "Empirical", "synthetic": "Synthetic"}),
        **{
            "SCRS mean": case["mean_scrs"].map(lambda x: fmt(x)),
            "SCRS min": case["min_scrs"].map(lambda x: fmt(x)),
            "Max SE": case["max_scrs_se"].map(lambda x: fmt(x)),
            "Gap vs strategy shuffled": case["mean_gap_vs_strategy_shuffled"].map(lambda x: fmt(x)),
            "Gap vs score shuffled": case["mean_gap_vs_score_shuffled"].map(lambda x: fmt(x)),
            "Strict wins": case.apply(lambda r: f"{int(r.strict_wins)}/{int(r.cells)}", axis=1),
        },
    )[
        [
            "Dataset",
            "Source",
            "SCRS mean",
            "SCRS min",
            "Max SE",
            "Gap vs strategy shuffled",
            "Gap vs score shuffled",
            "Strict wins",
        ]
    ]
    mechanism_table = mechanism.assign(
        Source=mechanism["source"].map({"real": "Empirical", "synthetic": "Synthetic"}),
        Comparison=mechanism["control"].map(CONTROL_LABEL),
        **{
            "Cells": mechanism["cells"],
            "Positive gaps": mechanism.apply(lambda r: f"{int(r.positive_gaps)}/{int(r.cells)}", axis=1),
            "CI-positive gaps": mechanism.apply(lambda r: f"{int(r.ci_positive_gaps)}/{int(r.cells)}", axis=1),
            "Mean gap": mechanism["mean_gap"].map(lambda x: fmt(x)),
            "Minimum gap": mechanism["min_gap"].map(lambda x: fmt(x)),
        },
    )[
        ["Source", "Comparison", "Cells", "Positive gaps", "CI-positive gaps", "Mean gap", "Minimum gap"]
    ]
    strict_table = cell.assign(
        Dataset=cell["case"].map(lambda x: clean_label(x).replace("\n", " ")),
        r=cell["r"].map(lambda x: f"{x:.1f}"),
        **{
            "SCRS": cell["scrs"].map(lambda x: fmt(x)),
            "Strongest control": cell["strongest_control"].map(lambda x: x.replace("_", " ")),
            "Control tail": cell["strongest_control_tail"].map(lambda x: fmt(x)),
            "Gap": cell["gap_vs_strongest"].map(lambda x: fmt(x)),
            "Gap 95% CI": cell.apply(lambda r: f"[{fmt(r.gap_vs_strongest_ci95_low)}, {fmt(r.gap_vs_strongest_ci95_high)}]", axis=1),
        },
    )[["Dataset", "r", "SCRS", "Strongest control", "Control tail", "Gap", "Gap 95% CI"]]

    tables = [
        ("table1_experimental_scale", scale, "Formal SCRS validation scale."),
        ("table2_source_level_summary", source_table, "Source-level SCRS performance and mechanism summary."),
        ("table3_case_level_summary", case_table, "Dataset-level SCRS stability and mechanism separation."),
        ("table4_mechanism_comparisons", mechanism_table, "Mechanism comparisons against key controls."),
        ("table5_strict_cell_summary", strict_table, "Cell-level comparison with the strongest strict control."),
    ]
    for stem, table_df, caption in tables:
        table_df.to_csv(table_dir / f"{stem}.csv", index=False)
        (table_dir / f"{stem}.md").write_text(markdown_table(table_df), encoding="utf-8")
        (table_dir / f"{stem}.tex").write_text(latex_table(table_df, caption, f"tab:{stem}"), encoding="utf-8")


def write_texts(root: Path, package_dir: Path, source: pd.DataFrame, case: pd.DataFrame, mechanism: pd.DataFrame) -> None:
    real = source[source["source"] == "real"].iloc[0]
    synthetic = source[source["source"] == "synthetic"].iloc[0]
    role_real = mechanism[(mechanism["source"] == "real") & (mechanism["control"] == "scrs_gamma1_strategy_shuffled")].iloc[0]
    role_syn = mechanism[(mechanism["source"] == "synthetic") & (mechanism["control"] == "scrs_gamma1_strategy_shuffled")].iloc[0]
    score_real = mechanism[(mechanism["source"] == "real") & (mechanism["control"] == "scrs_gamma1_score_shuffled")].iloc[0]
    score_syn = mechanism[(mechanism["source"] == "synthetic") & (mechanism["control"] == "scrs_gamma1_score_shuffled")].iloc[0]

    results = f"""# NC-Ready SCRS Results Text

## Main Results Draft

We evaluated Success-Conditioned Role Selection (SCRS) on two synthetic temporal hypergraphs and four empirical temporal contact datasets under a formal validation scale of 5000 update steps, 50 repetitions per condition, and three enhancement factors. SCRS maintained high cooperation across all tested conditions. Across the empirical datasets, mean tail cooperation reached {fmt(real.mean_scrs)} and the weakest empirical cell remained at {fmt(real.min_scrs)}, with a maximum standard error of {fmt(real.max_scrs_se)}. Across the synthetic cases, SCRS reached full cooperation in every tested cell.

SCRS also exceeded the two main performance baselines. The mean empirical gap was {fmt(real.mean_gap_vs_pnas)} against PNAS-style imitation and {fmt(real.mean_gap_vs_csgc)} against cooperative-success group selection. The synthetic results showed the same direction, with mean gaps of {fmt(synthetic.mean_gap_vs_pnas)} and {fmt(synthetic.mean_gap_vs_csgc)}. These results support a performance claim: SCRS is stable on both empirical and synthetic temporal hypergraphs at the formal scale used here.

The mechanism tests identify successful-cooperator role screening as the main active component. When the strategy labels used for role screening were shuffled, SCRS retained a mean empirical advantage of {fmt(role_real.mean_gap)} and a synthetic advantage of {fmt(role_syn.mean_gap)}. All empirical case-r cells favored SCRS over the strategy-shuffled ablation, and all empirical cell-level approximate 95% confidence intervals remained above zero.

The edge-score component needs a narrower claim. SCRS and score-shuffled SCRS were nearly tied, with a mean empirical gap of {fmt(score_real.mean_gap)} and a synthetic gap of {fmt(score_syn.mean_gap)}. No source-level score-shuffled comparison produced cell-level CI support for an independent SCRS advantage. The safest NC framing is therefore that SCRS achieves robust cooperation through success-conditioned role-model selection, while score-based group selection acts as a contextual layer rather than the primary driver.

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
    readme = f"""# SCRS NC Submission Package

Created: {datetime.now().isoformat(timespec='seconds')}

This package converts the completed s20 formal SCRS validation into submission-facing material. It does not modify the original raw results.

Source experiment:

`{root}`

Main decision:

- Performance: pass.
- Role-screening mechanism: pass.
- Edge-score independent mechanism: limited.

Use the files in `figures/`, `tables/`, and `text/` for paper drafting. Use `data/qa_summary.json` to confirm completeness.
"""
    claim_map = pd.DataFrame(
        [
            ["Performance stability", "Supported", f"Empirical mean SCRS={fmt(real.mean_scrs)}; empirical min={fmt(real.min_scrs)}; synthetic cells=1.0000."],
            ["Improvement over PNAS/CSGC", "Supported", f"Empirical gaps: PNAS={fmt(real.mean_gap_vs_pnas)}, CSGC={fmt(real.mean_gap_vs_csgc)}."],
            ["Successful-cooperator role screening", "Supported", f"Gap vs strategy-shuffled SCRS: empirical={fmt(role_real.mean_gap)}, synthetic={fmt(role_syn.mean_gap)}."],
            ["Edge-score selection as main driver", "Limited", f"Gap vs score-shuffled SCRS: empirical={fmt(score_real.mean_gap)}, synthetic={fmt(score_syn.mean_gap)}."],
            ["Beats every strict control", "Not supported as a strong claim", f"Strict wins: empirical {int(real.strict_wins)}/{int(real.cells)}, synthetic {int(synthetic.strict_wins)}/{int(synthetic.cells)}."],
        ],
        columns=["Claim", "Status", "Evidence"],
    )
    text_dir = package_dir / "text"
    (text_dir / "nc_ready_results_text.md").write_text(results, encoding="utf-8")
    (text_dir / "figure_captions.md").write_text(captions, encoding="utf-8")
    (text_dir / "README.md").write_text(readme, encoding="utf-8")
    claim_map.to_csv(text_dir / "claim_boundary_table.csv", index=False)
    (text_dir / "claim_boundary_table.md").write_text(markdown_table(claim_map), encoding="utf-8")


def validate(root: Path, data_dir: Path) -> dict[str, object]:
    detail = pd.read_csv(root / "detail.csv")
    counts = detail.groupby(["case", "variant", "r"]).size()
    qa = {
        "rows": int(len(detail)),
        "duplicate_keys": int(detail.duplicated(["case", "variant", "r", "rep"]).sum()),
        "cells": int(len(counts)),
        "min_reps_per_cell": int(counts.min()),
        "max_reps_per_cell": int(counts.max()),
        "cases": sorted(str(x) for x in detail["case"].unique()),
        "variants": sorted(str(x) for x in detail["variant"].unique()),
    }
    (data_dir / "qa_summary.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    return qa


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


def write_manifest(package_dir: Path, root: Path, qa: dict[str, object]) -> None:
    files = sorted(str(path.relative_to(package_dir)) for path in package_dir.rglob("*") if path.is_file())
    manifest = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "package_dir": str(package_dir),
        "source_experiment": str(root),
        "qa": qa,
        "files": files,
    }
    (package_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    root = Path(args.root).expanduser()
    if args.out_dir:
        package_dir = Path(args.out_dir).expanduser()
    else:
        package_dir = root / f"nc_submission_package_{datetime.now().strftime('%Y%m%d_%H%M')}"
    if package_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing package: {package_dir}")

    figure_dir = package_dir / "figures"
    table_dir = package_dir / "tables"
    data_dir = package_dir / "data"
    text_dir = package_dir / "text"
    for directory in [figure_dir, table_dir, data_dir, text_dir]:
        directory.mkdir(parents=True, exist_ok=False)

    source = pd.read_csv(root / "scrs_formal_source_summary.csv")
    case = pd.read_csv(root / "scrs_formal_case_summary.csv")
    cell = pd.read_csv(root / "scrs_formal_cell_summary.csv")
    mechanism = pd.read_csv(root / "scrs_formal_mechanism_summary.csv")

    copy_core_data(root, data_dir)
    qa = validate(root, data_dir)
    figure_1_stability(cell, figure_dir)
    figure_2_gap_bars(source, cell, figure_dir)
    figure_3_heatmaps(cell, figure_dir)
    figure_s1_strict_boundary(cell, figure_dir)
    write_tables(source, case, mechanism, cell, table_dir)
    write_texts(root, package_dir, source, case, mechanism)
    write_manifest(package_dir, root, qa)
    print(package_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create NC-style SCRS submission figures, tables, and claims.")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="Completed s20 SCRS formal output directory.")
    parser.add_argument("--out-dir", default="", help="New package directory. Must not already exist.")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
