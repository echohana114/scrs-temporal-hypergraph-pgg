#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import scrs_nc_experiment_common as common


EXPERIMENT_NAME = "s30_scrs_nc_structure_stratified_mechanism_audit"
REPORT_TITLE = "SCRS NC Supplemental S30 Structure-Stratified Mechanism Audit"
DEFAULT_OUT_ROOT = common.RUNS_ROOT / f"s30_scrs_nc_structure_moderator_{datetime.now().strftime('%Y%m%d_%H%M')}"
LOCAL_RUNS_ROOT = Path("/Users/hui/Documents/演化博弈-NC/supplemental_lfds_runs")
PAPER_SOURCE = Path("/Users/hui/Documents/演化博弈-NC/paper_nc_submission/source_data")
EXTERNAL_MANIFEST = (
    common.PROJECT
    / "real_data_external_s26/prepared_20260901_2023/s26_external_real_manifest.json"
)

DEFAULT_S28_ROOT = LOCAL_RUNS_ROOT / "s28_scrs_nc_construction_sensitivity_formal_20261010_195700"
DEFAULT_S29_ROOT = LOCAL_RUNS_ROOT / "s29_scrs_nc_mechanism_context_controls_formal_20261010_153000"

LEGACY_ROOTS = {
    "S20": common.RUNS_ROOT / "s20_scrs_formal_nc_validation_20260824_2037",
    "S22": common.RUNS_ROOT / "s22_scrs_nc_real_nulls_20260831_1238",
    "S23": common.RUNS_ROOT / "s23_scrs_nc_synthetic_stress_20260831_1633",
    "S26": common.RUNS_ROOT / "s26_scrs_nc_empirical_extrapolation_20260901_2023",
}

STRUCTURE_COLUMNS = [
    "temporal_memory_adjacent_jaccard",
    "hyperedge_overlap_within_block",
    "hyperedge_overlap_adjacent_block",
    "exact_group_recurrence_rate",
    "activity_cv",
    "activity_gini",
    "active_node_fraction",
    "mixed_role_exposure_potential_rho0",
]


@dataclass(frozen=True)
class DatasetInput:
    experiment_label: str
    root: Path
    cell_file: str
    required: bool = True


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    text = str(value)
    return "" if text.lower() in {"nan", "none"} else text


def gini(values: np.ndarray) -> float:
    clean = np.asarray(values, dtype=float)
    clean = clean[clean >= 0]
    if clean.size == 0 or float(clean.sum()) <= 0:
        return 0.0
    sorted_values = np.sort(clean)
    n = sorted_values.size
    index = np.arange(1, n + 1, dtype=float)
    return float((2 * np.sum(index * sorted_values)) / (n * np.sum(sorted_values)) - (n + 1) / n)


def jaccard(a: set[int], b: set[int]) -> float:
    union = len(a | b)
    if union == 0:
        return 0.0
    return len(a & b) / union


def read_sequence_csv(path: Path) -> list[np.ndarray]:
    df = pd.read_csv(path)
    node_cols = [col for col in df.columns if col.startswith("node_")]
    if not node_cols:
        raise ValueError(f"No node columns in sequence file: {path}")
    blocks = [
        group[node_cols].to_numpy(dtype=np.int32)
        for _, group in df.groupby("block", sort=True)
        if not group.empty
    ]
    if not blocks:
        raise ValueError(f"No blocks in sequence file: {path}")
    return blocks


def representative_sequence_from_task(row: pd.Series, blocks: int = 100) -> list[np.ndarray]:
    backend = common.ensure_backend()
    source = clean_text(row.get("source", ""))
    case_name = clean_text(row.get("case", ""))
    topology = clean_text(row.get("topology", ""))
    if source == "real":
        case = common.case_by_name(case_name)
    else:
        if not topology:
            try:
                topology = clean_text(common.case_by_name(case_name).temporal_model)
            except KeyError:
                topology = "uniform_random"
        case = backend.Case(
            case_name,
            "synthetic",
            topology,
            int(row.get("n", 100)),
            int(row.get("edge_size", 6)),
            int(row.get("n_edges", 20)),
        )
    task = {
        "source": source,
        "case": case_name,
        "topology": topology,
        "null_model": clean_text(row.get("null_model", "")),
        "n": int(row.get("n", case.n)),
        "n_edges": int(row.get("n_edges", case.n_edges)),
        "edge_size": int(row.get("edge_size", case.edge_size)),
    }
    rng = np.random.default_rng(2026103001 + abs(hash((case_name, task["topology"], task["null_model"]))) % 1000000)
    context = common.build_edge_context(case, task, rng)
    return [common.generate_edges_for_task(case, task, rng, block, context).astype(np.int32) for block in range(blocks)]


def external_sequence_lookup(manifest_path: Path) -> dict[str, Path]:
    if not manifest_path.exists():
        return {}
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    out: dict[str, Path] = {}
    for row in payload.get("prepared_datasets", []):
        name = str(row.get("dataset_name", ""))
        path = row.get("sequence_path")
        if name and path:
            out[name] = Path(str(path))
    return out


def case_sequence(row: pd.Series, s28_manifest: pd.DataFrame, external_lookup: dict[str, Path]) -> tuple[list[np.ndarray], str]:
    condition = clean_text(row.get("condition", ""))
    case_name = clean_text(row.get("case", ""))
    if not s28_manifest.empty and condition in set(s28_manifest["condition"].astype(str)):
        hit = s28_manifest.loc[s28_manifest["condition"].astype(str) == condition].iloc[0]
        path = Path(str(hit["prepared_sequence_path"]))
        return read_sequence_csv(path), str(path)
    if case_name in external_lookup:
        path = external_lookup[case_name]
        return read_sequence_csv(path), str(path)
    source = clean_text(row.get("source", ""))
    if source == "real":
        case = common.case_by_name(case_name)
        path = Path(str(case.real_sequence_path))
        return read_sequence_csv(path), str(path)
    return representative_sequence_from_task(row), "representative_synthetic_sequence_generated_for_structure_metrics"


def sequence_metrics(blocks: list[np.ndarray], n: int, rho0: float) -> dict[str, float]:
    edge_sets_by_block: list[list[set[int]]] = [
        [set(int(x) for x in edge) for edge in block]
        for block in blocks
    ]
    all_edges = [edge for block in edge_sets_by_block for edge in block]
    all_sizes = np.asarray([len(edge) for edge in all_edges], dtype=float)
    counts = np.zeros(int(n), dtype=float)
    for edge in all_edges:
        for node in edge:
            if 0 <= int(node) < n:
                counts[int(node)] += 1.0

    within_values: list[float] = []
    for edge_sets in edge_sets_by_block:
        if len(edge_sets) < 2:
            continue
        vals = [
            jaccard(edge_sets[i], edge_sets[j])
            for i in range(len(edge_sets))
            for j in range(i + 1, len(edge_sets))
        ]
        if vals:
            within_values.append(float(np.mean(vals)))

    adjacent_values: list[float] = []
    exact_recurrence = 0
    exact_total = 0
    for prev, cur in zip(edge_sets_by_block[:-1], edge_sets_by_block[1:]):
        prev_keys = {tuple(sorted(edge)) for edge in prev}
        for edge in cur:
            if prev:
                adjacent_values.append(max(jaccard(edge, other) for other in prev))
            exact_total += 1
            exact_recurrence += int(tuple(sorted(edge)) in prev_keys)

    rho = float(rho0) if not math.isnan(float(rho0)) else common.DEFAULT_RHO0
    mixed_potential = float(np.mean([1.0 - rho ** size - (1.0 - rho) ** size for size in all_sizes])) if all_sizes.size else 0.0
    active = counts[counts > 0]
    mean_count = float(counts.mean()) if counts.size else 0.0
    sd_count = float(counts.std(ddof=1)) if counts.size > 1 else 0.0

    return {
        "blocks": float(len(blocks)),
        "edge_events": float(len(all_edges)),
        "mean_edges_per_block": float(np.mean([len(block) for block in blocks])) if blocks else 0.0,
        "mean_edge_size": float(all_sizes.mean()) if all_sizes.size else 0.0,
        "edge_size_sd": float(all_sizes.std(ddof=1)) if all_sizes.size > 1 else 0.0,
        "temporal_memory_adjacent_jaccard": float(np.mean(adjacent_values)) if adjacent_values else 0.0,
        "hyperedge_overlap_within_block": float(np.mean(within_values)) if within_values else 0.0,
        "hyperedge_overlap_adjacent_block": float(np.mean(adjacent_values)) if adjacent_values else 0.0,
        "exact_group_recurrence_rate": float(exact_recurrence / exact_total) if exact_total else 0.0,
        "activity_cv": float(sd_count / mean_count) if mean_count > 0 else 0.0,
        "activity_gini": gini(counts),
        "active_node_fraction": float(active.size / counts.size) if counts.size else 0.0,
        "mixed_role_exposure_potential_rho0": mixed_potential,
    }


def load_cells(inputs: list[DatasetInput], allow_incomplete: bool) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    missing: list[str] = []
    for item in inputs:
        path = item.root / item.cell_file
        if not path.exists():
            if item.required and not allow_incomplete:
                missing.append(str(path))
            continue
        frame = pd.read_csv(path)
        frame["s_experiment"] = item.experiment_label
        frame["input_root"] = str(item.root)
        frames.append(frame)
    if missing:
        raise FileNotFoundError("Missing required completed inputs:\n" + "\n".join(missing))
    if not frames:
        return pd.DataFrame()
    cells = pd.concat(frames, ignore_index=True, sort=False)
    for col in ["condition", "null_model", "topology", "payoff_mode", "update_mode"]:
        if col not in cells.columns:
            cells[col] = ""
    for col in ["n", "n_edges", "edge_size", "subgraph_duration", "steps", "tail_window"]:
        if col not in cells.columns:
            cells[col] = 0
        cells[col] = pd.to_numeric(cells[col], errors="coerce").fillna(0).astype(int)
    for col in ["r", "rho0", "selection_intensity", "mutation_rate", "scrs", "gap_vs_strongest", "scrs_role_coop_rate", "scrs_csgc_selection_lift"]:
        if col not in cells.columns:
            cells[col] = np.nan
        cells[col] = pd.to_numeric(cells[col], errors="coerce")
    return cells


def attach_structure_metrics(cells: pd.DataFrame, s28_manifest: pd.DataFrame, external_lookup: dict[str, Path]) -> pd.DataFrame:
    cache: dict[tuple[Any, ...], dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    for _, row in cells.iterrows():
        key = (
            clean_text(row.get("condition", "")),
            clean_text(row.get("case", "")),
            clean_text(row.get("source", "")),
            clean_text(row.get("null_model", "")),
            clean_text(row.get("topology", "")),
            int(row.get("n", 0)),
            int(row.get("n_edges", 0)),
            int(row.get("edge_size", 0)),
            int(row.get("subgraph_duration", 0)),
        )
        if key not in cache:
            blocks, sequence_source = case_sequence(row, s28_manifest, external_lookup)
            node_max = -1
            for block in blocks:
                if len(block) == 0:
                    continue
                node_max = max(node_max, int(np.asarray(block).max()))
            n = int(row.get("n", 0)) or (node_max + 1 if node_max >= 0 else 0)
            metrics = sequence_metrics(blocks, n=n, rho0=float(row.get("rho0", common.DEFAULT_RHO0) or common.DEFAULT_RHO0))
            metrics["sequence_source"] = sequence_source
            cache[key] = metrics
        rows.append({**row.to_dict(), **cache[key]})
    return pd.DataFrame(rows)


def gap_long_table(enriched: pd.DataFrame) -> pd.DataFrame:
    id_cols = [
        "s_experiment",
        "condition",
        "case",
        "source",
        "r",
        "steps",
        "tail_window",
        "subgraph_duration",
        "selection_intensity",
        "rho0",
        "null_model",
        "topology",
        "n",
        "n_edges",
        "edge_size",
        "mutation_rate",
        "payoff_mode",
        "update_mode",
        "scrs",
        "scrs_role_coop_rate",
        "scrs_csgc_selection_lift",
        *STRUCTURE_COLUMNS,
    ]
    available_ids = [col for col in id_cols if col in enriched.columns]
    gap_cols = [
        col
        for col in enriched.columns
        if col.startswith("gap_vs_") and not col.endswith("_ci95_low") and not col.endswith("_ci95_high")
    ]
    if not gap_cols:
        return pd.DataFrame()
    long = enriched.melt(
        id_vars=available_ids,
        value_vars=gap_cols,
        var_name="gap_column",
        value_name="gap",
    )
    long = long.dropna(subset=["gap"]).reset_index(drop=True)
    long["control"] = long["gap_column"].str.replace("gap_vs_", "", regex=False)
    long["cell_id"] = (
        long["s_experiment"].astype(str)
        + "|"
        + long["condition"].astype(str)
        + "|"
        + long["case"].astype(str)
        + "|"
        + long["r"].astype(str)
        + "|"
        + long["control"].astype(str)
    )
    return long


def bootstrap_ci(values: np.ndarray, seed: int = 2026103002, draws: int = 2000) -> tuple[float, float]:
    clean = np.asarray(values, dtype=float)
    clean = clean[np.isfinite(clean)]
    if clean.size == 0:
        return (np.nan, np.nan)
    if clean.size == 1:
        return (float(clean[0]), float(clean[0]))
    rng = np.random.default_rng(seed)
    means = np.empty(draws, dtype=float)
    for idx in range(draws):
        sample = rng.choice(clean, size=clean.size, replace=True)
        means[idx] = float(sample.mean())
    return (float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975)))


def sign_permutation_p(values: np.ndarray) -> float:
    clean = np.asarray(values, dtype=float)
    clean = clean[np.isfinite(clean)]
    if clean.size == 0:
        return np.nan
    nonzero = clean[clean != 0]
    if nonzero.size == 0:
        return 1.0
    positives = int((nonzero > 0).sum())
    n = int(nonzero.size)
    extreme = min(positives, n - positives)
    prob = sum(math.comb(n, k) for k in range(extreme + 1)) / (2**n)
    return float(min(1.0, 2.0 * prob))


def tertile_labels(values: pd.Series) -> pd.Series:
    ranked = values.rank(method="average")
    try:
        return pd.qcut(ranked, q=3, labels=["low", "mid", "high"]).astype(str)
    except ValueError:
        return pd.Series(["all"] * len(values), index=values.index)


def summarize_by_structure(gaps: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if gaps.empty:
        return pd.DataFrame()
    for metric in STRUCTURE_COLUMNS:
        if metric not in gaps.columns:
            continue
        temp = gaps.dropna(subset=[metric, "gap"]).copy()
        if temp.empty:
            continue
        temp["structure_stratum"] = tertile_labels(temp[metric])
        for (control, stratum), group in temp.groupby(["control", "structure_stratum"], dropna=False):
            values = group["gap"].to_numpy(dtype=float)
            low, high = bootstrap_ci(values, seed=abs(hash((metric, control, stratum))) % (2**32 - 1))
            rows.append(
                {
                    "structure_metric": metric,
                    "structure_stratum": str(stratum),
                    "control": str(control),
                    "cells": int(group["cell_id"].nunique()),
                    "mean_structure_metric": float(group[metric].mean()),
                    "mean_gap": float(np.mean(values)),
                    "gap_ci95_low": low,
                    "gap_ci95_high": high,
                    "positive_cells": int((values > 0).sum()),
                    "sign_permutation_p": sign_permutation_p(values),
                    "mean_scrs_role_coop_rate": float(group["scrs_role_coop_rate"].mean()) if "scrs_role_coop_rate" in group else np.nan,
                    "mean_scrs_csgc_selection_lift": float(group["scrs_csgc_selection_lift"].mean()) if "scrs_csgc_selection_lift" in group else np.nan,
                }
            )
    return pd.DataFrame(rows)


def slope_with_case_centering(group: pd.DataFrame, metric: str) -> dict[str, float]:
    temp = group[["case", metric, "gap"]].dropna()
    if temp.empty or temp[metric].nunique() < 2:
        return {"slope": np.nan, "case_centered_slope": np.nan}
    x = temp[metric].to_numpy(dtype=float)
    y = temp["gap"].to_numpy(dtype=float)
    slope = float(np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1)) if np.var(x, ddof=1) > 0 else np.nan
    centered = temp.copy()
    centered["_x"] = centered[metric] - centered.groupby("case")[metric].transform("mean")
    centered["_y"] = centered["gap"] - centered.groupby("case")["gap"].transform("mean")
    cx = centered["_x"].to_numpy(dtype=float)
    cy = centered["_y"].to_numpy(dtype=float)
    centered_slope = float(np.cov(cx, cy, ddof=1)[0, 1] / np.var(cx, ddof=1)) if np.var(cx, ddof=1) > 0 else np.nan
    return {"slope": slope, "case_centered_slope": centered_slope}


def moderator_regression(gaps: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if gaps.empty:
        return pd.DataFrame()
    for metric in STRUCTURE_COLUMNS:
        if metric not in gaps.columns:
            continue
        for control, group in gaps.groupby("control", dropna=False):
            temp = group.dropna(subset=[metric, "gap"]).copy()
            if temp.empty:
                continue
            stats = slope_with_case_centering(temp, metric)
            rows.append(
                {
                    "structure_metric": metric,
                    "control": str(control),
                    "cells": int(temp["cell_id"].nunique()),
                    "pearson_r": float(temp[[metric, "gap"]].corr(method="pearson").iloc[0, 1]) if temp[metric].nunique() > 1 else np.nan,
                    "spearman_r": float(temp[[metric, "gap"]].corr(method="spearman").iloc[0, 1]) if temp[metric].nunique() > 1 else np.nan,
                    "ols_slope": stats["slope"],
                    "case_centered_slope": stats["case_centered_slope"],
                    "mean_gap": float(temp["gap"].mean()),
                    "mean_structure_metric": float(temp[metric].mean()),
                    "interpretation_unit": "cell-level summary; case-centered slope is a fixed-effect proxy, not a Monte Carlo replicate test",
                }
            )
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=REPORT_TITLE)
    parser.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))
    parser.add_argument("--s28-root", default=str(DEFAULT_S28_ROOT))
    parser.add_argument("--s29-root", default=str(DEFAULT_S29_ROOT))
    parser.add_argument("--external-manifest", default=str(EXTERNAL_MANIFEST))
    parser.add_argument("--allow-incomplete", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_root = Path(args.out_root).expanduser()
    out_root.mkdir(parents=True, exist_ok=True)

    s28_root = Path(args.s28_root).expanduser()
    s29_root = Path(args.s29_root).expanduser()
    inputs = [
        DatasetInput("S20_main_validation", LEGACY_ROOTS["S20"], "scrs_formal_cell_summary.csv"),
        DatasetInput("S22_real_null_models", LEGACY_ROOTS["S22"], "scrs_nc_cell_summary.csv"),
        DatasetInput("S23_synthetic_stress", LEGACY_ROOTS["S23"], "scrs_nc_cell_summary.csv"),
        DatasetInput("S26_external_empirical", LEGACY_ROOTS["S26"], "scrs_nc_cell_summary.csv"),
        DatasetInput("S28_construction_sensitivity", s28_root, "S28_cell_summary.csv"),
        DatasetInput("S29_clean_mechanism_context", s29_root, "S29_cell_summary.csv"),
    ]
    cells = load_cells(inputs, allow_incomplete=bool(args.allow_incomplete))
    s28_manifest_path = s28_root / "S28_construction_manifest.csv"
    s28_manifest = pd.read_csv(s28_manifest_path) if s28_manifest_path.exists() else pd.DataFrame()
    external_lookup = external_sequence_lookup(Path(args.external_manifest).expanduser())

    enriched = attach_structure_metrics(cells, s28_manifest, external_lookup)
    gaps = gap_long_table(enriched)
    strata = summarize_by_structure(gaps)
    regression = moderator_regression(gaps)

    enriched.to_csv(out_root / "S30_structure_metrics.csv", index=False)
    strata.to_csv(out_root / "S30_gap_by_structure_stratum.csv", index=False)
    regression.to_csv(out_root / "S30_moderator_regression_summary.csv", index=False)
    gaps.to_csv(out_root / "S30_structure_moderator_source.csv", index=False)

    qa = {
        "state": "complete",
        "inputs": [
            {"experiment": item.experiment_label, "root": str(item.root), "cell_file": item.cell_file}
            for item in inputs
        ],
        "cell_rows": int(len(enriched)),
        "gap_rows": int(len(gaps)),
        "structure_strata_rows": int(len(strata)),
        "moderator_rows": int(len(regression)),
        "notes": [
            "Structural metrics are computed at the dataset/condition level and joined to cell-level SCRS summaries.",
            "mixed_role_exposure_potential_rho0 is a construction-level potential under the initial rho0, not a logged selected-group exposure rate.",
            "Permutation and bootstrap summaries use cell-level gaps; Monte Carlo repetitions are not treated as independent systems.",
        ],
    }
    (out_root / "S30_QA_report.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    (out_root / "SCRS_NC_s30_structure_moderator_report.md").write_text(
        "# SCRS NC Supplemental S30 Structure-Stratified Mechanism Audit\n\n"
        f"- Cell rows: {qa['cell_rows']}\n"
        f"- Gap rows: {qa['gap_rows']}\n"
        f"- Structure-stratum rows: {qa['structure_strata_rows']}\n"
        f"- Moderator rows: {qa['moderator_rows']}\n\n"
        "Outputs: `S30_structure_metrics.csv`, `S30_gap_by_structure_stratum.csv`, "
        "`S30_moderator_regression_summary.csv`, `S30_structure_moderator_source.csv`.\n",
        encoding="utf-8",
    )
    print(json.dumps(qa, indent=2))


if __name__ == "__main__":
    main()
