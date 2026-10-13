#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import scrs_nc_experiment_common as common


EXPERIMENT_NAME = "s25_scrs_nc_mechanism_decomposition"
REPORT_TITLE = "SCRS NC Supplemental S25 Mechanism Decomposition"
BASE_SEED = 2026090101
DEFAULT_OUT_ROOT = common.RUNS_ROOT / f"s25_scrs_nc_mechanism_decomposition_{datetime.now().strftime('%Y%m%d_%H%M')}"

CASE_NAMES = [
    "real_highschool2013",
    "real_workplace2013",
    "real_hospitalward2010",
    "real_sfhh2009",
    "synthetic_structured_ring",
    "synthetic_community",
    "synthetic_stress_temporal_modular_switching_n200",
]
VARIANTS = [
    "scrs_gamma1",
    "scrs_gamma1_strategy_shuffled",
    "scrs_gamma1_score_shuffled",
    "scrs_gamma1_cooperator_only_random",
    "scrs_gamma1_payoff_only_role",
    "scrs_gamma1_success_only_no_coop_filter",
    "scrs_gamma1_random_role_same_edge",
]
R_VALUES = [0.70, 0.90, 1.00]
EDGE_SIZE = 6


DESIGN_TEXT = """S25 decomposes the SCRS role-selection mechanism into matched active components.

- Cases: four empirical temporal hypergraphs from s20 plus synthetic_structured_ring, synthetic_community, and temporal_modular_switching_n200.
- Variants: SCRS, strategy-shuffled SCRS, score-shuffled SCRS, cooperator-only random role, payoff-only role, success-only no cooperator filter, and random role on the same selected edge.
- Parameters: r = 0.70, 0.90, 1.00, beta = 2.0, rho0 = 0.5.
- Formal scale: 5000 steps, 50 reps per cell, tail_window = 1000.
- Claim use: separate the contribution of successful-cooperator screening, the cooperator identity filter, payoff ranking, and the contextual edge-score layer.
"""


def case_payload(case_name: str) -> dict[str, object]:
    if case_name == "synthetic_stress_temporal_modular_switching_n200":
        return {
            "case": case_name,
            "source": "synthetic",
            "topology": "temporal_modular_switching",
            "n": 200,
            "n_edges": 40,
            "edge_size": EDGE_SIZE,
        }
    case = common.case_by_name(case_name)
    return {
        "case": case.name,
        "source": case.source,
        "topology": "" if case.source == "real" else case.temporal_model,
        "n": int(case.n),
        "n_edges": int(case.n_edges),
        "edge_size": int(case.edge_size),
    }


def build_tasks(args: argparse.Namespace) -> list[dict[str, object]]:
    steps = int(args.steps or (100 if args.smoke else common.DEFAULT_STEPS))
    reps = int(args.reps or (2 if args.smoke else common.DEFAULT_REPS))
    tail_window = min(common.DEFAULT_TAIL_WINDOW, steps)
    case_names = ["real_sfhh2009", "synthetic_stress_temporal_modular_switching_n200"] if args.smoke else CASE_NAMES
    r_values = [0.70] if args.smoke else R_VALUES
    tasks: list[dict[str, object]] = []
    for case_name in case_names:
        payload = case_payload(case_name)
        for variant in VARIANTS:
            for r in r_values:
                for rep in range(reps):
                    tasks.append(
                        common.normalize_task(
                            {
                                "experiment": EXPERIMENT_NAME,
                                "condition": "mechanism_decomposition",
                                **payload,
                                "variant": variant,
                                "r": float(r),
                                "rep": int(rep),
                                "steps": int(steps),
                                "tail_window": int(tail_window),
                                "subgraph_duration": common.DEFAULT_SUBGRAPH_DURATION,
                                "selection_intensity": 2.0,
                                "rho0": 0.5,
                                "null_model": "",
                                "mutation_rate": 0.0,
                                "payoff_mode": "",
                                "update_mode": "",
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
