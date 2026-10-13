#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import scrs_nc_experiment_common as common


EXPERIMENT_NAME = "s24_scrs_nc_noise_long_horizon"
REPORT_TITLE = "SCRS NC Supplemental S24 Noise and Long-Horizon Stability"
BASE_SEED = 2026082704
DEFAULT_OUT_ROOT = common.RUNS_ROOT / f"s24_scrs_nc_noise_horizon_{datetime.now().strftime('%Y%m%d_%H%M')}"

CASES = ["real_sfhh2009", "real_highschool2013", "synthetic_community"]
VARIANTS = [
    "scrs_gamma1",
    "csgc_gamma1",
    "pnas",
    "scrs_gamma1_strategy_shuffled",
]
MUTATION_RATES = [0.0, 0.0001, 0.001, 0.01]
R_VALUES = [0.70, 0.90, 1.00]
FORMAL_STEPS = 10000
TRACE_EVERY = 100


DESIGN_TEXT = """S24 tests whether SCRS cooperation is a long-horizon steady behavior rather than a short transient.

- Cases: real_sfhh2009 as the weakest empirical case, real_highschool2013 as the boundary empirical case, and synthetic_community as the synthetic reference.
- Noise: per-node strategy mutation/tremble mu = 0, 1e-4, 1e-3, 1e-2 after each update step.
- Variants: SCRS, CSGC, PNAS, and SCRS strategy-shuffled.
- Parameters: r = 0.70, 0.90, 1.00, beta = 2.0, rho0 = 0.5.
- Formal scale: 10000 steps, 50 reps per cell, tail_window = 1000.
- Trajectories: save decimated cooperation trajectories every 100 steps for long-horizon diagnostics.
- Claim use: define the perturbation boundary and show whether the role-screening mechanism remains active under noise.
"""


def build_tasks(args: argparse.Namespace) -> list[dict[str, object]]:
    steps = int(args.steps or (100 if args.smoke else FORMAL_STEPS))
    reps = int(args.reps or (2 if args.smoke else common.DEFAULT_REPS))
    tail_window = min(common.DEFAULT_TAIL_WINDOW, steps)
    case_names = ["real_sfhh2009", "synthetic_community"] if args.smoke else CASES
    mutation_rates = [0.0, 0.001] if args.smoke else MUTATION_RATES
    r_values = [0.70] if args.smoke else R_VALUES
    trace_every = 25 if args.smoke else TRACE_EVERY
    tasks: list[dict[str, object]] = []
    for case_name in case_names:
        case = common.case_by_name(case_name)
        for mutation_rate in mutation_rates:
            for variant in VARIANTS:
                for r in r_values:
                    for rep in range(reps):
                        task = common.normalize_task(
                            {
                                "experiment": EXPERIMENT_NAME,
                                "condition": "noise_long_horizon",
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
                                "null_model": "",
                                "topology": "",
                                "n": int(case.n),
                                "n_edges": int(case.n_edges),
                                "edge_size": int(case.edge_size),
                                "mutation_rate": float(mutation_rate),
                            },
                            BASE_SEED,
                        )
                        task["trace_every"] = trace_every
                        tasks.append(task)
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

