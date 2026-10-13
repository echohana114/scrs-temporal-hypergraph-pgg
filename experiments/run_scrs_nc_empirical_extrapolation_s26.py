#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import scrs_nc_experiment_common as common


EXPERIMENT_NAME = "s26_scrs_nc_empirical_extrapolation"
REPORT_TITLE = "SCRS NC Supplemental S26 Empirical Extrapolation"
BASE_SEED = 2026090103
DEFAULT_OUT_ROOT = common.RUNS_ROOT / f"s26_scrs_nc_empirical_extrapolation_{datetime.now().strftime('%Y%m%d_%H%M')}"

VARIANTS = [
    "scrs_gamma1",
    "pnas",
    "csgc_gamma1",
    "scrs_gamma1_score_shuffled",
    "scrs_gamma1_strategy_shuffled",
]
R_VALUES = [0.70, 0.90, 1.00]


DESIGN_TEXT = """S26 tests whether SCRS empirical stability extrapolates beyond the four s20 real temporal contact sequences.

- Data: external public temporal higher-order or group-interaction datasets prepared into real_sequence_edges.csv by prepare_scrs_external_real_data_s26.py.
- Minimum formal inclusion rule: at least three non-SocioPatterns external datasets must pass n >= 50 and blocks >= 4.
- Variants: SCRS, PNAS, CSGC, SCRS score-shuffled, and SCRS strategy-shuffled.
- Parameters: r = 0.70, 0.90, 1.00, beta = 2.0, rho0 = 0.5.
- Formal scale: 5000 steps, 50 reps per cell, tail_window = 1000.
- Claim use: show that SCRS performance and role-screening evidence are not limited to the original four empirical contact datasets.
"""


def load_manifest(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = list(payload.get("prepared_datasets", []))
    valid: list[dict[str, object]] = []
    for row in rows:
        sequence_path = Path(str(row.get("sequence_path", "")))
        if not sequence_path.exists():
            continue
        if int(row.get("n", 0)) < 50 or int(row.get("blocks", 0)) < 4:
            continue
        valid.append(row)
    return valid


def build_tasks(args: argparse.Namespace) -> list[dict[str, object]]:
    if not args.manifest:
        raise ValueError("--manifest is required for S26")
    steps = int(args.steps or (100 if args.smoke else common.DEFAULT_STEPS))
    reps = int(args.reps or (2 if args.smoke else common.DEFAULT_REPS))
    tail_window = min(common.DEFAULT_TAIL_WINDOW, steps)
    datasets = load_manifest(Path(args.manifest).expanduser())
    if args.smoke:
        datasets = datasets[:1]
    elif len(datasets) < 3:
        raise ValueError(f"S26 requires at least 3 prepared external datasets; found {len(datasets)}")
    r_values = [0.70] if args.smoke else R_VALUES
    tasks: list[dict[str, object]] = []
    for dataset in datasets:
        for variant in VARIANTS:
            for r in r_values:
                for rep in range(reps):
                    tasks.append(
                        common.normalize_task(
                            {
                                "experiment": EXPERIMENT_NAME,
                                "condition": "empirical_extrapolation",
                                "case": str(dataset["dataset_name"]),
                                "source": "real",
                                "variant": variant,
                                "r": float(r),
                                "rep": int(rep),
                                "steps": int(steps),
                                "tail_window": int(tail_window),
                                "subgraph_duration": common.DEFAULT_SUBGRAPH_DURATION,
                                "selection_intensity": 2.0,
                                "rho0": 0.5,
                                "null_model": "",
                                "topology": str(dataset.get("family", "external_real")),
                                "n": int(dataset["n"]),
                                "n_edges": int(dataset["n_edges"]),
                                "edge_size": int(dataset["edge_size"]),
                                "mutation_rate": 0.0,
                                "payoff_mode": "",
                                "update_mode": "",
                                "real_sequence_path": str(dataset["sequence_path"]),
                            },
                            BASE_SEED,
                        )
                    )
    return tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=REPORT_TITLE)
    common.add_common_args(parser, DEFAULT_OUT_ROOT)
    parser.add_argument("--manifest", default="", help="Manifest from prepare_scrs_external_real_data_s26.py.")
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
