#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import scrs_nc_experiment_common as common


EXPERIMENT_NAME = "s22_scrs_nc_real_null_models"
REPORT_TITLE = "SCRS NC Supplemental S22 Real Temporal and Topological Null Models"
BASE_SEED = 2026082702
DEFAULT_OUT_ROOT = common.RUNS_ROOT / f"s22_scrs_nc_real_nulls_{datetime.now().strftime('%Y%m%d_%H%M')}"

VARIANTS = [
    "scrs_gamma1",
    "pnas",
    "csgc_gamma1",
    "scrs_gamma1_score_shuffled",
    "scrs_gamma1_strategy_shuffled",
]
NULL_MODELS = [
    "original",
    "block_order_shuffle",
    "degree_preserving_rewire",
    "activity_preserving_resample",
]
R_VALUES = [0.70, 0.90, 1.00]


DESIGN_TEXT = """S22 tests whether SCRS evidence on empirical temporal hypergraphs depends on a narrow real-sequence artifact.

- Cases: 4 real empirical temporal hypergraphs from s20.
- Null models: original temporal sequence, shuffled block order, degree-preserving within-block hyperedge rewiring, and activity-preserving random hyperedge resampling.
- Variants: SCRS, PNAS, CSGC, SCRS score-shuffled, and SCRS strategy-shuffled.
- Parameters: r = 0.70, 0.90, 1.00, beta = 2.0, rho0 = 0.5.
- Formal scale: 5000 steps, 50 reps per cell, tail_window = 1000.
- Claim use: separate robust SCRS behavior from effects that rely on the exact empirical block order or higher-order co-membership pattern.
"""


def build_tasks(args: argparse.Namespace) -> list[dict[str, object]]:
    steps = int(args.steps or (100 if args.smoke else common.DEFAULT_STEPS))
    reps = int(args.reps or (2 if args.smoke else common.DEFAULT_REPS))
    tail_window = min(common.DEFAULT_TAIL_WINDOW, steps)
    cases = [common.case_by_name("real_sfhh2009")] if args.smoke else common.backend_cases(source="real")
    null_models = NULL_MODELS[:2] if args.smoke else NULL_MODELS
    r_values = [0.70] if args.smoke else R_VALUES
    tasks: list[dict[str, object]] = []
    for case in cases:
        for null_model in null_models:
            for variant in VARIANTS:
                for r in r_values:
                    for rep in range(reps):
                        tasks.append(
                            common.normalize_task(
                                {
                                    "experiment": EXPERIMENT_NAME,
                                    "condition": "real_null_model",
                                    "case": case.name,
                                    "source": case.source,
                                    "variant": variant,
                                    "r": float(r),
                                    "rep": int(rep),
                                    "steps": int(steps),
                                    "tail_window": int(tail_window),
                                    "subgraph_duration": common.DEFAULT_SUBGRAPH_DURATION,
                                    "selection_intensity": 2.0,
                                    "rho0": 0.5,
                                    "null_model": null_model,
                                    "topology": "",
                                    "n": int(case.n),
                                    "n_edges": int(case.n_edges),
                                    "edge_size": int(case.edge_size),
                                    "mutation_rate": 0.0,
                                },
                                BASE_SEED,
                            )
                        )
    return tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=REPORT_TITLE)
    common.add_common_args(parser, DEFAULT_OUT_ROOT)
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


if __name__ == "__main__":
    main()

