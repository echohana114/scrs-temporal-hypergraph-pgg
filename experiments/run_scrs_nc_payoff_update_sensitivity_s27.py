#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import scrs_nc_experiment_common as common


EXPERIMENT_NAME = "s27_scrs_nc_payoff_update_sensitivity"
REPORT_TITLE = "SCRS NC Supplemental S27 Payoff and Update-Rule Sensitivity"
BASE_SEED = 2026090104
DEFAULT_OUT_ROOT = common.RUNS_ROOT / f"s27_scrs_nc_payoff_update_sensitivity_{datetime.now().strftime('%Y%m%d_%H%M')}"

CASES = ["real_sfhh2009", "real_highschool2013", "synthetic_community"]
VARIANTS = [
    "scrs_gamma1",
    "pnas",
    "csgc_gamma1",
    "scrs_gamma1_score_shuffled",
    "scrs_gamma1_strategy_shuffled",
]
R_VALUES = [0.70, 0.90, 1.00]
EXECUTION_MODES = [
    ("baseline", "accumulated", "synchronous"),
    ("degree_normalized_payoff", "degree_normalized", "synchronous"),
    ("per_capita_payoff", "per_capita", "synchronous"),
    ("asynchronous_in_place", "accumulated", "asynchronous_in_place"),
]


DESIGN_TEXT = """S27 audits whether SCRS conclusions depend on payoff normalization, update schedule, or tail-window choice.

- Cases: real_sfhh2009, real_highschool2013, and synthetic_community.
- Variants: SCRS, PNAS, CSGC, SCRS score-shuffled, and SCRS strategy-shuffled.
- Execution modes: baseline accumulated payoff with synchronous commit, degree-normalized payoff, per-capita public-goods payoff, and asynchronous in-place updates.
- Parameters: r = 0.70, 0.90, 1.00, beta = 2.0, rho0 = 0.5.
- Formal scale: 5000 steps, 50 reps per cell, primary tail_window = 1000.
- Tail audit: each trial also records tail means for windows 500, 1000, and 2000 from the same trajectory.
- Claim use: test whether SCRS evidence is robust to core implementation details.
"""


def build_tasks(args: argparse.Namespace) -> list[dict[str, object]]:
    steps = int(args.steps or (100 if args.smoke else common.DEFAULT_STEPS))
    reps = int(args.reps or (2 if args.smoke else common.DEFAULT_REPS))
    tail_window = min(common.DEFAULT_TAIL_WINDOW, steps)
    case_names = ["real_sfhh2009", "synthetic_community"] if args.smoke else CASES
    r_values = [0.70] if args.smoke else R_VALUES
    execution_modes = EXECUTION_MODES if not args.smoke else EXECUTION_MODES[:2]
    tasks: list[dict[str, object]] = []
    for case_name in case_names:
        case = common.case_by_name(case_name)
        for condition_suffix, payoff_mode, update_mode in execution_modes:
            for variant in VARIANTS:
                for r in r_values:
                    for rep in range(reps):
                        tasks.append(
                            common.normalize_task(
                                {
                                    "experiment": EXPERIMENT_NAME,
                                    "condition": f"payoff_update_sensitivity_{condition_suffix}",
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
                                    "topology": "" if case.source == "real" else case.temporal_model,
                                    "n": int(case.n),
                                    "n_edges": int(case.n_edges),
                                    "edge_size": int(case.edge_size),
                                    "mutation_rate": 0.0,
                                    "payoff_mode": payoff_mode,
                                    "update_mode": update_mode,
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
