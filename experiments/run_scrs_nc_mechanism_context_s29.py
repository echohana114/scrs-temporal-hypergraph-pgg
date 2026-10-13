#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

import scrs_nc_experiment_common as common


EXPERIMENT_NAME = "s29_scrs_nc_mechanism_context_controls"
REPORT_TITLE = "SCRS NC Supplemental S29 Clean Mechanism-Context Controls"
BASE_SEED = 2026092901
DEFAULT_OUT_ROOT = common.RUNS_ROOT / f"s29_scrs_nc_mechanism_context_controls_{datetime.now().strftime('%Y%m%d_%H%M')}"

CASE_NAMES = [
    "real_highschool2013",
    "real_workplace2013",
    "real_hospitalward2010",
    "real_sfhh2009",
    "synthetic_structured_ring",
    "synthetic_community",
]
VARIANTS = [
    "scrs_gamma1",
    "scrs_gamma1_strategy_shuffled",
    "scrs_gamma1_score_shuffled",
    "scrs_gamma1_cooperator_only_random",
    "scrs_gamma1_cooperator_only_uniform_incident",
    "scrs_gamma1_cooperator_only_random_neighborhood",
    "scrs_gamma1_success_without_score_ranking",
]
R_VALUES = [0.70, 0.90, 1.00]
EDGE_SIZE = 6


DESIGN_TEXT = """S29 tests whether SCRS is more than generic local cooperator search.

- Tier: A-level required pre-submission mechanism-context control.
- Cases: four core empirical temporal hypergraphs plus synthetic_structured_ring and synthetic_community.
- Variants: SCRS, strategy-shuffled SCRS, score-shuffled SCRS, cooperator-only random role on the SCRS-selected edge, cooperator-only from a uniformly sampled incident edge, cooperator-only from the random local neighborhood, and successful edge without score ranking.
- Formal parameters: steps = 5000, tail_window = 1000, reps = 50, r = 0.70, 0.90, 1.00, rho0 = 0.5, selection_intensity = 2.0.
- Seeds: matched deterministic seeds derived from the full task key.
- Inference: cell-level paired gaps, paired bootstrap intervals and sign-permutation summaries; Monte Carlo repetitions describe within-cell uncertainty only.
- Claim use: if generic local cooperator search matches SCRS, narrow the claim to local cooperative role screening; if SCRS remains above those controls, retain the successful-group context plus role-screening interpretation.
"""


def case_payload(case_name: str) -> dict[str, object]:
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
    case_names = ["real_sfhh2009", "synthetic_structured_ring"] if args.smoke else CASE_NAMES
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
                                "condition": "clean_mechanism_context_controls",
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


def write_s29_named_outputs(out_root: Path) -> None:
    generic_to_named = {
        "scrs_nc_cell_summary.csv": "S29_cell_summary.csv",
        "scrs_nc_paired_gap_summary.csv": "S29_paired_gap_summary.csv",
    }
    for generic, named in generic_to_named.items():
        source = out_root / generic
        if source.exists():
            shutil.copy2(source, out_root / named)

    detail_path = out_root / "detail.csv"
    if not detail_path.exists():
        return
    details = common.load_detail(detail_path)
    if details.empty:
        return
    audit = (
        details.groupby(common.CELL_CONTEXT_COLUMNS + ["variant"], as_index=False, dropna=False)
        .agg(
            reps=("rep", "nunique"),
            mean_tail_coop=("tail_coop", "mean"),
            mean_role_model_cooperator_rate=("scrs_role_coop_rate", "mean"),
            min_role_model_cooperator_rate=("scrs_role_coop_rate", "min"),
            max_role_model_cooperator_rate=("scrs_role_coop_rate", "max"),
            mean_context_selection_lift=("csgc_selection_lift", "mean"),
        )
        .sort_values(common.CELL_CONTEXT_COLUMNS + ["variant"])
        .reset_index(drop=True)
    )
    audit.to_csv(out_root / "S29_role_model_eligibility_audit.csv", index=False)


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
    if not args.plan_only:
        write_s29_named_outputs(Path(args.out_root).expanduser())


if __name__ == "__main__":
    main()
