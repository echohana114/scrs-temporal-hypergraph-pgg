#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import scrs_nc_experiment_common as common


EXPERIMENT_NAME = "s21_scrs_nc_parameter_robustness"
REPORT_TITLE = "SCRS NC Supplemental S21 Parameter and Initial-Condition Robustness"
BASE_SEED = 2026082701
DEFAULT_OUT_ROOT = (
    common.RUNS_ROOT / f"s21_scrs_nc_parameter_robustness_{datetime.now().strftime('%Y%m%d_%H%M')}"
)

VARIANTS = [
    "scrs_gamma1",
    "pnas",
    "csgc_gamma1",
    "scrs_gamma1_score_shuffled",
    "scrs_gamma1_strategy_shuffled",
    "lfds_l050",
    "lfds_l075",
    "lfds_l075_budget",
]
R_SWEEP = [0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10, 1.20]
R_CORE = [0.70, 0.90, 1.00]
BETA_SWEEP = [0.50, 1.00, 2.00, 4.00]
RHO0_SWEEP = [0.10, 0.30, 0.50, 0.70, 0.90]


DESIGN_TEXT = """S21 tests whether SCRS performance and mechanism claims survive broad parameter and initial-condition changes.

- Cases: the same 6 cases used in s20, including 4 empirical temporal hypergraphs and 2 synthetic temporal hypergraphs.
- Variants: SCRS, PNAS, CSGC, SCRS score-shuffled, SCRS strategy-shuffled, LFDS lambda 0.50, LFDS lambda 0.75, and LFDS lambda 0.75 budget control.
- r sweep: r = 0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10, 1.20 with beta = 2.0 and rho0 = 0.5.
- selection-intensity sweep: beta = 0.5, 1.0, 2.0, 4.0 with r = 0.70, 0.90, 1.00 and rho0 = 0.5.
- initial-condition sweep: rho0 = 0.10, 0.30, 0.50, 0.70, 0.90 with r = 0.70, 0.90, 1.00 and beta = 2.0.
- Formal scale: 5000 steps, 50 reps per cell, tail_window = 1000.
- Claim use: locate the SCRS stability region and failure boundary; keep role-screening evidence tied to the strategy-shuffled ablation; keep edge-score claims conservative using the score-shuffled ablation.
"""


def selected_cases(smoke: bool) -> list[object]:
    if not smoke:
        return common.backend_cases()
    return [
        common.case_by_name("synthetic_structured_ring"),
        common.case_by_name("real_sfhh2009"),
    ]


def add_task(
    tasks: list[dict[str, object]],
    *,
    case: object,
    condition: str,
    variant: str,
    r: float,
    rep: int,
    steps: int,
    tail_window: int,
    beta: float,
    rho0: float,
) -> None:
    tasks.append(
        common.normalize_task(
            {
                "experiment": EXPERIMENT_NAME,
                "condition": condition,
                "case": case.name,
                "source": case.source,
                "variant": variant,
                "r": float(r),
                "rep": int(rep),
                "steps": int(steps),
                "tail_window": int(tail_window),
                "subgraph_duration": common.DEFAULT_SUBGRAPH_DURATION,
                "selection_intensity": float(beta),
                "rho0": float(rho0),
                "null_model": "",
                "topology": "",
                "n": int(case.n),
                "n_edges": int(case.n_edges),
                "edge_size": int(case.edge_size),
                "mutation_rate": 0.0,
            },
            BASE_SEED,
        )
    )


def build_tasks(args: argparse.Namespace) -> list[dict[str, object]]:
    steps = int(args.steps or (100 if args.smoke else common.DEFAULT_STEPS))
    reps = int(args.reps or (2 if args.smoke else common.DEFAULT_REPS))
    tail_window = min(common.DEFAULT_TAIL_WINDOW, steps)
    cases = selected_cases(args.smoke)
    r_sweep = [0.70] if args.smoke else R_SWEEP
    r_core = [0.70] if args.smoke else R_CORE
    beta_sweep = [2.00] if args.smoke else BETA_SWEEP
    rho0_sweep = [0.10] if args.smoke else RHO0_SWEEP
    tasks: list[dict[str, object]] = []

    for case in cases:
        for variant in VARIANTS:
            for r in r_sweep:
                for rep in range(reps):
                    add_task(
                        tasks,
                        case=case,
                        condition="r_sweep",
                        variant=variant,
                        r=r,
                        rep=rep,
                        steps=steps,
                        tail_window=tail_window,
                        beta=2.0,
                        rho0=0.5,
                    )
            for beta in beta_sweep:
                for r in r_core:
                    for rep in range(reps):
                        add_task(
                            tasks,
                            case=case,
                            condition="selection_intensity_sweep",
                            variant=variant,
                            r=r,
                            rep=rep,
                            steps=steps,
                            tail_window=tail_window,
                            beta=beta,
                            rho0=0.5,
                        )
            for rho0 in rho0_sweep:
                for r in r_core:
                    for rep in range(reps):
                        add_task(
                            tasks,
                            case=case,
                            condition="rho0_sweep",
                            variant=variant,
                            r=r,
                            rep=rep,
                            steps=steps,
                            tail_window=tail_window,
                            beta=2.0,
                            rho0=rho0,
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

