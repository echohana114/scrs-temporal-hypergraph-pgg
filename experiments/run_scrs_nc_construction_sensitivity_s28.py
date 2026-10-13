#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import scrs_nc_experiment_common as common


EXPERIMENT_NAME = "s28_scrs_nc_hypergraph_construction_sensitivity"
REPORT_TITLE = "SCRS NC Supplemental S28 Hypergraph Construction Sensitivity"
BASE_SEED = 2026101001
DEFAULT_OUT_ROOT = common.RUNS_ROOT / f"s28_scrs_nc_construction_sensitivity_{datetime.now().strftime('%Y%m%d_%H%M')}"
EXTERNAL_MANIFEST = (
    common.PROJECT
    / "real_data_external_s26/prepared_20260901_2023/s26_external_real_manifest.json"
)

CASE_NAMES = [
    "real_highschool2013",
    "real_workplace2013",
    "real_hospitalward2010",
    "real_sfhh2009",
]
EXTERNAL_CASE_NAMES = [
    "external_copenhagen_bluetooth",
    "external_email_enron",
]
VARIANTS = [
    "scrs_gamma1",
    "pnas",
    "csgc_gamma1",
    "scrs_gamma1_strategy_shuffled",
    "scrs_gamma1_score_shuffled",
]
R_VALUES = [0.70, 0.90, 1.00]


DESIGN_TEXT = """S28 tests whether the SCRS advantage depends on a single temporal-hypergraph construction.

- Tier: A-level construction-sensitivity evidence for submission.
- Data: four core SocioPatterns-style empirical sequences plus Copenhagen Bluetooth and Email-Enron external group-event sequences.
- Construction grid: a compact one-factor sensitivity design around the h=6, m=33, subgraph_duration=100 baseline; h={4,6,8}, m={20,33}, subgraph_duration={50,100,200}, and four construction-mode projections are audited without crossing every factor.
- Variants: SCRS, Wang et al. temporal-hypergraph imitation, CSGC, strategy-shuffled SCRS and score-shuffled SCRS.
- Formal parameters: steps = 5000, tail_window = 1000, reps = 50, r = 0.70, 0.90, 1.00, rho0 = 0.5, selection_intensity = 2.0.
- Seeds: matched deterministic seeds derived from the full task key.
- Inference: cell-level paired gaps, paired bootstrap intervals and sign-permutation summaries; Monte Carlo repetitions describe within-cell uncertainty only.
- Claim use: if SCRS gaps remain positive against Wang imitation, CSGC and strategy-shuffled SCRS across construction slices while score-shuffled stays near zero, the fixed-size construction assumption is defended as a robustness boundary rather than the causal mechanism.
"""


def read_sequence(path: Path) -> list[np.ndarray]:
    df = pd.read_csv(path)
    node_cols = [col for col in df.columns if col.startswith("node_")]
    if not node_cols:
        raise ValueError(f"No node columns in {path}")
    return [group[node_cols].to_numpy(dtype=np.int32) for _, group in df.groupby("block", sort=True)]


def write_sequence(path: Path, blocks: list[np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        if not blocks:
            raise ValueError(f"No blocks for {path}")
        edge_size = int(blocks[0].shape[1])
        fieldnames = ["block", "slot", *[f"node_{idx}" for idx in range(edge_size)]]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for block_idx, edges in enumerate(blocks):
            for slot, edge in enumerate(edges):
                row = {"block": block_idx, "slot": slot}
                row.update({f"node_{idx}": int(node) for idx, node in enumerate(edge)})
                writer.writerow(row)


def gini(values: np.ndarray) -> float:
    clean = np.asarray(values, dtype=float)
    clean = clean[clean >= 0]
    if clean.size == 0 or float(clean.sum()) <= 0:
        return 0.0
    sorted_values = np.sort(clean)
    n = sorted_values.size
    index = np.arange(1, n + 1, dtype=float)
    return float((2 * np.sum(index * sorted_values)) / (n * np.sum(sorted_values)) - (n + 1) / n)


def resize_edge(
    edge: np.ndarray,
    *,
    target_h: int,
    node_pool: np.ndarray,
    n: int,
    rng: np.random.Generator,
    deterministic: bool,
) -> np.ndarray:
    unique = list(dict.fromkeys(int(node) for node in edge))
    if len(unique) >= target_h:
        if deterministic:
            return np.asarray(sorted(unique)[:target_h], dtype=np.int32)
        return np.asarray(rng.choice(unique, size=target_h, replace=False), dtype=np.int32)
    selected = list(unique)
    pool = [int(node) for node in node_pool if int(node) not in selected]
    if len(pool) < target_h - len(selected):
        pool = [node for node in range(n) if node not in selected]
    while len(selected) < target_h:
        candidate = int(rng.choice(pool))
        if candidate not in selected:
            selected.append(candidate)
    return np.asarray(selected[:target_h], dtype=np.int32)


def sample_rows(rows: list[np.ndarray], target_m: int, rng: np.random.Generator) -> list[np.ndarray]:
    if not rows:
        raise ValueError("Cannot sample from empty construction rows")
    replace = len(rows) < target_m
    indices = rng.choice(len(rows), size=target_m, replace=replace)
    return [rows[int(idx)] for idx in indices]


def construct_block(
    original: np.ndarray,
    *,
    n: int,
    target_h: int,
    target_m: int,
    mode: str,
    rng: np.random.Generator,
) -> tuple[np.ndarray, dict[str, Any]]:
    node_pool = np.unique(original.ravel()).astype(np.int32)
    if node_pool.size < target_h:
        node_pool = np.arange(n, dtype=np.int32)
    transformed = [
        resize_edge(edge, target_h=target_h, node_pool=node_pool, n=n, rng=rng, deterministic=(mode == "clique_only"))
        for edge in original
    ]
    if mode == "contact_centered_fallback":
        counts = np.bincount(original.ravel(), minlength=n).astype(float)
        weights = counts + 1e-9
        weights = weights / weights.sum()
        rows = []
        for _ in range(max(target_m, len(transformed))):
            center = int(rng.choice(n, p=weights))
            local_pool = [int(node) for edge in original if center in set(int(x) for x in edge) for node in edge]
            local_pool = np.asarray(sorted(set(local_pool) | {center}), dtype=np.int32)
            rows.append(
                resize_edge(
                    np.asarray([center], dtype=np.int32),
                    target_h=target_h,
                    node_pool=local_pool if local_pool.size >= target_h else node_pool,
                    n=n,
                    rng=rng,
                    deterministic=False,
                )
            )
    elif mode == "fixed_h6_alternative":
        rows = [
            np.roll(edge, int(slot % max(1, target_h))).astype(np.int32)
            for slot, edge in enumerate(transformed)
        ]
    else:
        rows = transformed
    if mode == "clique_only":
        dedup = {tuple(sorted(int(x) for x in row)): row for row in rows}
        rows = [dedup[key] for key in sorted(dedup)]
    sampled = np.vstack(sample_rows(rows, target_m, rng)).astype(np.int32)
    return sampled, {
        "candidate_edges": len(rows),
        "unique_nodes": int(node_pool.size),
        "activity_gini": gini(np.bincount(original.ravel(), minlength=n)),
    }


def prepare_sequence(
    *,
    source_path: Path,
    out_path: Path,
    n: int,
    target_h: int,
    target_m: int,
    mode: str,
    seed: int,
) -> dict[str, Any]:
    blocks = read_sequence(source_path)
    rng = np.random.default_rng(seed)
    prepared_blocks: list[np.ndarray] = []
    stats: list[dict[str, Any]] = []
    for block_idx, block in enumerate(blocks):
        prepared, block_stats = construct_block(
            block,
            n=n,
            target_h=target_h,
            target_m=target_m,
            mode=mode,
            rng=rng,
        )
        prepared_blocks.append(prepared)
        stats.append({"block": block_idx, **block_stats})
    write_sequence(out_path, prepared_blocks)
    return {
        "sequence_path": str(out_path),
        "blocks": len(prepared_blocks),
        "mean_candidate_edges": float(np.mean([row["candidate_edges"] for row in stats])),
        "mean_unique_nodes_per_block": float(np.mean([row["unique_nodes"] for row in stats])),
        "mean_activity_gini": float(np.mean([row["activity_gini"] for row in stats])),
    }


def construction_grid(smoke: bool) -> list[dict[str, Any]]:
    if smoke:
        return [
            {"construction_mode": "baseline_hybrid", "edge_size": 6, "n_edges": 33, "subgraph_duration": 100, "slice": "baseline"},
            {"construction_mode": "baseline_hybrid", "edge_size": 4, "n_edges": 33, "subgraph_duration": 100, "slice": "h_sensitivity"},
        ]
    grid = [
        {"construction_mode": "baseline_hybrid", "edge_size": 6, "n_edges": 33, "subgraph_duration": 100, "slice": "baseline"},
        {"construction_mode": "baseline_hybrid", "edge_size": 4, "n_edges": 33, "subgraph_duration": 100, "slice": "h_sensitivity"},
        {"construction_mode": "baseline_hybrid", "edge_size": 8, "n_edges": 33, "subgraph_duration": 100, "slice": "h_sensitivity"},
        {"construction_mode": "baseline_hybrid", "edge_size": 6, "n_edges": 20, "subgraph_duration": 100, "slice": "m_sensitivity"},
        {"construction_mode": "baseline_hybrid", "edge_size": 6, "n_edges": 33, "subgraph_duration": 50, "slice": "duration_sensitivity"},
        {"construction_mode": "baseline_hybrid", "edge_size": 6, "n_edges": 33, "subgraph_duration": 200, "slice": "duration_sensitivity"},
        {"construction_mode": "clique_only", "edge_size": 6, "n_edges": 33, "subgraph_duration": 100, "slice": "construction_mode"},
        {"construction_mode": "contact_centered_fallback", "edge_size": 6, "n_edges": 33, "subgraph_duration": 100, "slice": "construction_mode"},
        {"construction_mode": "fixed_h6_alternative", "edge_size": 6, "n_edges": 33, "subgraph_duration": 100, "slice": "construction_mode"},
        {"construction_mode": "native_variable_size_where_available", "edge_size": 6, "n_edges": 33, "subgraph_duration": 100, "slice": "construction_mode"},
    ]
    return grid


def core_dataset_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in CASE_NAMES:
        case = common.case_by_name(name)
        rows.append(
            {
                "case": case.name,
                "source": "real",
                "family": "sociopatterns_contact",
                "n": int(case.n),
                "baseline_edge_size": int(case.edge_size),
                "baseline_n_edges": int(case.n_edges),
                "source_sequence_path": str(case.real_sequence_path),
                "native_group_event": False,
            }
        )
    return rows


def external_dataset_rows(manifest_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    lookup = {str(row["dataset_name"]): row for row in payload.get("prepared_datasets", [])}
    rows: list[dict[str, Any]] = []
    for name in EXTERNAL_CASE_NAMES:
        row = lookup[name]
        rows.append(
            {
                "case": name,
                "source": "real",
                "family": str(row.get("family", "external_real")),
                "n": int(row["n"]),
                "baseline_edge_size": int(row["edge_size"]),
                "baseline_n_edges": int(row["n_edges"]),
                "source_sequence_path": str(row["sequence_path"]),
                "native_group_event": True,
            }
        )
    return rows


def prepare_constructions(args: argparse.Namespace, datasets: list[dict[str, Any]]) -> pd.DataFrame:
    out_root = Path(args.out_root).expanduser()
    prep_root = out_root / "prepared_sequences"
    rows: list[dict[str, Any]] = []
    for dataset in datasets:
        for cfg in construction_grid(bool(args.smoke)):
            mode = str(cfg["construction_mode"])
            effective_mode = mode
            if mode == "native_variable_size_where_available" and not bool(dataset["native_group_event"]):
                effective_mode = "baseline_hybrid"
            label_parts = [
                str(dataset["case"]),
                str(cfg["slice"]),
                mode,
                f"h{int(cfg['edge_size'])}",
                f"m{int(cfg['n_edges'])}",
                f"d{int(cfg['subgraph_duration'])}",
            ]
            label = "__".join(label_parts).replace("/", "_")
            sequence_path = prep_root / label / "real_sequence_edges.csv"
            seed = common.deterministic_seed(
                {
                    "experiment": EXPERIMENT_NAME,
                    "case": dataset["case"],
                    "condition": label,
                    "variant": "construction",
                    "r": 0.0,
                    "rep": 0,
                    "steps": 0,
                    "selection_intensity": 0.0,
                    "rho0": 0.0,
                    "null_model": "",
                    "topology": "",
                    "n": int(dataset["n"]),
                    "n_edges": int(cfg["n_edges"]),
                    "edge_size": int(cfg["edge_size"]),
                    "mutation_rate": 0.0,
                    "payoff_mode": "",
                    "update_mode": "",
                },
                BASE_SEED,
            )
            stats = prepare_sequence(
                source_path=Path(str(dataset["source_sequence_path"])),
                out_path=sequence_path,
                n=int(dataset["n"]),
                target_h=int(cfg["edge_size"]),
                target_m=int(cfg["n_edges"]),
                mode=effective_mode,
                seed=seed,
            )
            rows.append(
                {
                    **dataset,
                    **cfg,
                    "effective_construction_mode": effective_mode,
                    "condition": label,
                    "prepared_sequence_path": stats["sequence_path"],
                    "blocks": stats["blocks"],
                    "mean_candidate_edges": stats["mean_candidate_edges"],
                    "mean_unique_nodes_per_block": stats["mean_unique_nodes_per_block"],
                    "mean_activity_gini": stats["mean_activity_gini"],
                    "construction_seed": seed,
                }
            )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(out_root / "S28_construction_manifest.csv", index=False)
    return manifest


def build_tasks(args: argparse.Namespace) -> list[dict[str, Any]]:
    steps = int(args.steps or (100 if args.smoke else common.DEFAULT_STEPS))
    reps = int(args.reps or (2 if args.smoke else common.DEFAULT_REPS))
    tail_window = min(common.DEFAULT_TAIL_WINDOW, steps)
    datasets = core_dataset_rows() + external_dataset_rows(Path(args.external_manifest).expanduser())
    if args.smoke:
        datasets = [row for row in datasets if row["case"] in {"real_sfhh2009", "external_email_enron"}]
    manifest = prepare_constructions(args, datasets)
    r_values = [0.70] if args.smoke else R_VALUES
    tasks: list[dict[str, Any]] = []
    for row in manifest.to_dict(orient="records"):
        for variant in VARIANTS:
            for r in r_values:
                for rep in range(reps):
                    tasks.append(
                        common.normalize_task(
                            {
                                "experiment": EXPERIMENT_NAME,
                                "condition": str(row["condition"]),
                                "case": str(row["case"]),
                                "source": "real",
                                "variant": variant,
                                "r": float(r),
                                "rep": int(rep),
                                "steps": int(steps),
                                "tail_window": int(tail_window),
                                "subgraph_duration": int(row["subgraph_duration"]),
                                "selection_intensity": 2.0,
                                "rho0": 0.5,
                                "null_model": "",
                                "topology": str(row["construction_mode"]),
                                "n": int(row["n"]),
                                "n_edges": int(row["n_edges"]),
                                "edge_size": int(row["edge_size"]),
                                "mutation_rate": 0.0,
                                "payoff_mode": "",
                                "update_mode": "",
                                "real_sequence_path": str(row["prepared_sequence_path"]),
                            },
                            BASE_SEED,
                        )
                    )
    return tasks


def write_s28_named_outputs(out_root: Path) -> None:
    generic_to_named = {
        "scrs_nc_cell_summary.csv": "S28_cell_summary.csv",
        "scrs_nc_paired_gap_summary.csv": "S28_paired_gap_summary.csv",
        "qa_summary.json": "S28_QA_report.json",
    }
    for generic, named in generic_to_named.items():
        source = out_root / generic
        if source.exists():
            shutil.copy2(source, out_root / named)
    cell_path = out_root / "S28_cell_summary.csv"
    gap_path = out_root / "S28_paired_gap_summary.csv"
    if cell_path.exists():
        cell = pd.read_csv(cell_path)
        heat_cols = [
            col
            for col in [
                "condition",
                "case",
                "r",
                "edge_size",
                "n_edges",
                "subgraph_duration",
                "topology",
                "scrs",
                "gap_vs_pnas",
                "gap_vs_csgc_gamma1",
                "gap_vs_scrs_gamma1_strategy_shuffled",
                "gap_vs_scrs_gamma1_score_shuffled",
            ]
            if col in cell.columns
        ]
        cell[heat_cols].to_csv(out_root / "S28_construction_heatmap_source.csv", index=False)
    if gap_path.exists():
        gaps = pd.read_csv(gap_path)
        gaps.to_csv(out_root / "S28_gap_forest_source.csv", index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=REPORT_TITLE)
    common.add_common_args(parser, DEFAULT_OUT_ROOT)
    parser.add_argument("--external-manifest", default=str(EXTERNAL_MANIFEST))
    args = parser.parse_args()
    common.validate_common_args(args)
    return args


def main() -> None:
    args = parse_args()
    common.run_experiment(
        args=args,
        all_tasks=build_tasks(args),
        design_text=DESIGN_TEXT,
        report_title=REPORT_TITLE,
        script_path=Path(__file__).resolve(),
        experiment_name=EXPERIMENT_NAME,
    )
    if not args.plan_only:
        write_s28_named_outputs(Path(args.out_root).expanduser())


if __name__ == "__main__":
    main()
