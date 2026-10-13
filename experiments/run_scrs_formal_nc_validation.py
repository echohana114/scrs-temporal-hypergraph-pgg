#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import multiprocessing as mp
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT = Path("/Users/hui/Documents/New project 2/temporal_hypergraph_pgg_pilot")
BACKEND_SCRIPT = (
    PROJECT
    / "supplemental_lfds_runs"
    / "s18_scrs_strict_smoke_20260731_1015"
    / "run_scrs_strict_smoke.py"
)
DEFAULT_OUT_ROOT = (
    PROJECT
    / "supplemental_lfds_runs"
    / f"s20_scrs_formal_nc_validation_{datetime.now().strftime('%Y%m%d_%H%M')}"
)

STEPS = 5000
REPS = 50
TAIL_WINDOW = 1000
SUBGRAPH_DURATION = 100
SELECTION_INTENSITY = 2.0
EWMA_WINDOW = 100.0
SEED = 20260824
R_VALUES = [0.70, 0.90, 1.00]

VARIANTS = [
    "pnas",
    "csgc_gamma1",
    "csgc_gamma1_shuffled",
    "scrs_gamma1",
    "scrs_gamma1_score_shuffled",
    "scrs_gamma1_strategy_shuffled",
    "lfds_l050",
    "lfds_l050_budget",
    "lfds_l050_activity",
    "lfds_l050_local",
    "lfds_l050_score",
    "lfds_l075",
    "lfds_l075_budget",
    "lfds_l075_activity",
    "lfds_l075_local",
    "lfds_l075_score",
]

PERFORMANCE_CONTROLS = [
    "pnas",
    "csgc_gamma1",
    "scrs_gamma1_score_shuffled",
    "scrs_gamma1_strategy_shuffled",
]
STRICT_CONTROLS = [variant for variant in VARIANTS if variant != "scrs_gamma1"]
LFDS_CONTROLS = [variant for variant in VARIANTS if variant.startswith("lfds")]
MECHANISM_CONTROLS = [
    "scrs_gamma1_score_shuffled",
    "scrs_gamma1_strategy_shuffled",
    "csgc_gamma1",
]

FORMAL_DESIGN = """# SCRS Formal NC Validation Design

## Objective

Validate whether SCRS is formally stable on synthetic and real temporal hypergraph public-goods-game data, and separate performance effectiveness from mechanism novelty for an NC-oriented evidence package.

## Scale

- Steps per trial: 5000
- Repetitions per cell: 50
- Tail window: 1000
- Subgraph duration: 100
- Selection intensity: 2.0
- r grid: 0.70, 0.90, 1.00
- Cases: 2 synthetic and 4 real empirical temporal sequences
- Variants: SCRS, PNAS, CSGC, CSGC score-shuffled, SCRS score-shuffled, SCRS strategy-shuffled, LFDS lambda 0.50/0.75, and LFDS budget/activity/local/score matched controls at both lambdas

Total trials: 6 cases x 16 variants x 3 r x 50 reps = 14400.

## Claim Separation

- Performance effectiveness: SCRS keeps high tail cooperation on every real cell and synthetic cell, with small standard error and positive gaps versus PNAS/CSGC.
- Strict-control robustness: SCRS is compared with the strongest non-SCRS matched control and strongest LFDS matched control in every case-r cell.
- Mechanism novelty: SCRS is compared with `scrs_gamma1_strategy_shuffled`; a large positive gap supports successful-cooperator role screening as the active mechanism.
- Edge-score contribution: SCRS is compared with `scrs_gamma1_score_shuffled`; a small gap means edge-score group selection should not be claimed as the main driver.

## Decision Rules

- Performance pass: all real SCRS tail means >= 0.60, all synthetic SCRS tail means >= 0.95, and max SCRS SE <= 0.02.
- Mechanism-role pass: the mean gap versus `scrs_gamma1_strategy_shuffled` is positive for both real and synthetic sources, with most cell-level approximate 95% CIs above zero.
- Edge-score claim: only make a strong edge-score mechanism claim if the mean gap versus `scrs_gamma1_score_shuffled` is materially positive with most cell-level approximate 95% CIs above zero.
- Strict-control interpretation: if the strongest control is usually `scrs_gamma1_score_shuffled`, the paper should frame SCRS's robust performance as driven by successful-cooperator role screening, not by edge-score selection alone.
"""


BACKEND: Any = None


def load_backend(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("scrs_strict_backend", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load backend script: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.PROJECT = PROJECT
    module.STEPS = STEPS
    module.REPS = REPS
    module.TAIL_WINDOW = TAIL_WINDOW
    module.SUBGRAPH_DURATION = SUBGRAPH_DURATION
    module.SELECTION_INTENSITY = SELECTION_INTENSITY
    module.EWMA_WINDOW = EWMA_WINDOW
    module.SEED = SEED
    module.R_VALUES = R_VALUES
    module.VARIANTS = VARIANTS
    return module


def init_worker(backend_path: str) -> None:
    global BACKEND
    BACKEND = load_backend(Path(backend_path))


def run_one(task: tuple[str, str, float, int]) -> dict[str, Any]:
    if BACKEND is None:
        raise RuntimeError("Worker backend is not initialized")
    case_name, variant, r_value, rep = task
    case_lookup = {case.name: case for case in BACKEND.CASES}
    result = BACKEND.run_trial(case_lookup[case_name], variant, r_value, rep)
    return result


def stable_key(case: str, variant: str, r_value: float, rep: int) -> tuple[str, str, str, int]:
    return case, variant, f"{float(r_value):.4f}", int(rep)


def completed_keys(detail_path: Path) -> set[tuple[str, str, str, int]]:
    if not detail_path.exists():
        return set()
    existing = pd.read_csv(detail_path, usecols=["case", "variant", "r", "rep"])
    return {
        stable_key(str(row.case), str(row.variant), float(row.r), int(row.rep))
        for row in existing.itertuples(index=False)
    }


def build_tasks(backend: Any, detail_path: Path) -> list[tuple[str, str, float, int]]:
    done = completed_keys(detail_path)
    tasks: list[tuple[str, str, float, int]] = []
    for case in backend.CASES:
        for variant in VARIANTS:
            for r_value in R_VALUES:
                for rep in range(REPS):
                    key = stable_key(case.name, variant, r_value, rep)
                    if key not in done:
                        tasks.append((case.name, variant, r_value, rep))
    return tasks


def se(series: pd.Series) -> float:
    if len(series) <= 1:
        return 0.0
    return float(series.std(ddof=1) / math.sqrt(len(series)))


def ci_low(mean: float, se_value: float) -> float:
    return float(mean - 1.96 * se_value)


def ci_high(mean: float, se_value: float) -> float:
    return float(mean + 1.96 * se_value)


def normal_p_value(z_score: float) -> float:
    return float(math.erfc(abs(z_score) / math.sqrt(2.0)))


def summarize(
    details: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    summary = (
        details.groupby(["case", "source", "variant", "r"], as_index=False)
        .agg(
            reps=("rep", "nunique"),
            tail_coop_mean=("tail_coop", "mean"),
            tail_coop_sd=("tail_coop", lambda x: float(x.std(ddof=1)) if len(x) > 1 else 0.0),
            tail_coop_se=("tail_coop", se),
            final_coop_mean=("final_coop", "mean"),
            final_coop_sd=("final_coop", lambda x: float(x.std(ddof=1)) if len(x) > 1 else 0.0),
            final_coop_se=("final_coop", se),
            csgc_selection_lift=("csgc_selection_lift", "mean"),
            scrs_role_coop_rate=("scrs_role_coop_rate", "mean"),
            conformist_update_rate=("conformist_update_rate", "mean"),
            fermi_update_rate=("fermi_update_rate", "mean"),
        )
        .sort_values(["source", "case", "r", "variant"])
        .reset_index(drop=True)
    )
    summary["tail_coop_ci95_low"] = [
        ci_low(mean, se_value) for mean, se_value in zip(summary["tail_coop_mean"], summary["tail_coop_se"])
    ]
    summary["tail_coop_ci95_high"] = [
        ci_high(mean, se_value) for mean, se_value in zip(summary["tail_coop_mean"], summary["tail_coop_se"])
    ]
    summary["final_coop_ci95_low"] = [
        ci_low(mean, se_value) for mean, se_value in zip(summary["final_coop_mean"], summary["final_coop_se"])
    ]
    summary["final_coop_ci95_high"] = [
        ci_high(mean, se_value) for mean, se_value in zip(summary["final_coop_mean"], summary["final_coop_se"])
    ]

    cell_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    for (case, source, r_value), group in summary.groupby(["case", "source", "r"], sort=True):
        lookup = {str(row.variant): row for row in group.itertuples(index=False)}
        scrs = lookup["scrs_gamma1"]
        scrs_mean = float(scrs.tail_coop_mean)
        scrs_se = float(scrs.tail_coop_se)

        for control in STRICT_CONTROLS:
            ctrl = lookup[control]
            ctrl_mean = float(ctrl.tail_coop_mean)
            ctrl_se = float(ctrl.tail_coop_se)
            gap = scrs_mean - ctrl_mean
            gap_se = math.sqrt(scrs_se * scrs_se + ctrl_se * ctrl_se)
            z_score = gap / gap_se if gap_se > 0 else (math.inf if gap > 0 else -math.inf if gap < 0 else 0.0)
            pair_rows.append(
                {
                    "case": case,
                    "source": source,
                    "r": float(r_value),
                    "control": control,
                    "control_family": control_family(control),
                    "scrs_tail": scrs_mean,
                    "control_tail": ctrl_mean,
                    "gap": gap,
                    "gap_se": gap_se,
                    "gap_ci95_low": ci_low(gap, gap_se),
                    "gap_ci95_high": ci_high(gap, gap_se),
                    "z_approx": z_score,
                    "p_approx_normal": normal_p_value(z_score) if math.isfinite(z_score) else 0.0,
                    "scrs_reps": int(scrs.reps),
                    "control_reps": int(ctrl.reps),
                }
            )

        strict_values = {control: float(lookup[control].tail_coop_mean) for control in STRICT_CONTROLS}
        performance_values = {control: float(lookup[control].tail_coop_mean) for control in PERFORMANCE_CONTROLS}
        lfds_values = {control: float(lookup[control].tail_coop_mean) for control in LFDS_CONTROLS}
        strongest_strict = max(strict_values, key=strict_values.get)
        strongest_performance = max(performance_values, key=performance_values.get)
        strongest_lfds = max(lfds_values, key=lfds_values.get)
        gap_vs_strongest = scrs_mean - strict_values[strongest_strict]
        gap_vs_strongest_se = math.sqrt(scrs_se * scrs_se + float(lookup[strongest_strict].tail_coop_se) ** 2)
        cell_rows.append(
            {
                "case": case,
                "source": source,
                "r": float(r_value),
                "scrs": scrs_mean,
                "scrs_se": scrs_se,
                "scrs_ci95_low": float(scrs.tail_coop_ci95_low),
                "scrs_ci95_high": float(scrs.tail_coop_ci95_high),
                "scrs_final": float(scrs.final_coop_mean),
                "strongest_control": strongest_strict,
                "strongest_control_tail": strict_values[strongest_strict],
                "gap_vs_strongest": gap_vs_strongest,
                "gap_vs_strongest_ci95_low": ci_low(gap_vs_strongest, gap_vs_strongest_se),
                "gap_vs_strongest_ci95_high": ci_high(gap_vs_strongest, gap_vs_strongest_se),
                "strongest_performance_control": strongest_performance,
                "strongest_performance_control_tail": performance_values[strongest_performance],
                "gap_vs_performance_strongest": scrs_mean - performance_values[strongest_performance],
                "strongest_lfds_control": strongest_lfds,
                "strongest_lfds_control_tail": lfds_values[strongest_lfds],
                "gap_vs_lfds_strongest": scrs_mean - lfds_values[strongest_lfds],
                "gap_vs_pnas": scrs_mean - float(lookup["pnas"].tail_coop_mean),
                "gap_vs_csgc": scrs_mean - float(lookup["csgc_gamma1"].tail_coop_mean),
                "gap_vs_csgc_shuffled": scrs_mean - float(lookup["csgc_gamma1_shuffled"].tail_coop_mean),
                "gap_vs_scrs_score_shuffled": scrs_mean - float(lookup["scrs_gamma1_score_shuffled"].tail_coop_mean),
                "gap_vs_scrs_strategy_shuffled": scrs_mean - float(lookup["scrs_gamma1_strategy_shuffled"].tail_coop_mean),
                "scrs_role_coop_rate": float(scrs.scrs_role_coop_rate),
                "scrs_csgc_selection_lift": float(scrs.csgc_selection_lift),
            }
        )

    pairwise = pd.DataFrame(pair_rows).sort_values(["source", "case", "r", "control"]).reset_index(drop=True)
    cell = pd.DataFrame(cell_rows).sort_values(["source", "case", "r"]).reset_index(drop=True)
    source_summary = source_level_summary(cell)
    case_summary = case_level_summary(cell)
    mechanism_summary = mechanism_level_summary(pairwise)
    return summary, cell, source_summary, case_summary, mechanism_summary, pairwise


def control_family(control: str) -> str:
    if control == "pnas":
        return "pnas"
    if control.startswith("csgc"):
        return "csgc"
    if control.startswith("scrs"):
        return "scrs_ablation"
    if control.startswith("lfds"):
        return "lfds_matched"
    return "other"


def source_level_summary(cell: pd.DataFrame) -> pd.DataFrame:
    return (
        cell.groupby("source", as_index=False)
        .agg(
            cells=("r", "size"),
            strict_wins=("gap_vs_strongest", lambda x: int((x > 0).sum())),
            strict_ci_wins=("gap_vs_strongest_ci95_low", lambda x: int((x > 0).sum())),
            mean_gap_vs_strongest=("gap_vs_strongest", "mean"),
            min_gap_vs_strongest=("gap_vs_strongest", "min"),
            mean_scrs=("scrs", "mean"),
            min_scrs=("scrs", "min"),
            max_scrs_se=("scrs_se", "max"),
            mean_gap_vs_pnas=("gap_vs_pnas", "mean"),
            min_gap_vs_pnas=("gap_vs_pnas", "min"),
            mean_gap_vs_csgc=("gap_vs_csgc", "mean"),
            min_gap_vs_csgc=("gap_vs_csgc", "min"),
            mean_gap_vs_score_shuffled=("gap_vs_scrs_score_shuffled", "mean"),
            min_gap_vs_score_shuffled=("gap_vs_scrs_score_shuffled", "min"),
            mean_gap_vs_strategy_shuffled=("gap_vs_scrs_strategy_shuffled", "mean"),
            min_gap_vs_strategy_shuffled=("gap_vs_scrs_strategy_shuffled", "min"),
            mean_role_coop_rate=("scrs_role_coop_rate", "mean"),
            mean_selection_lift=("scrs_csgc_selection_lift", "mean"),
        )
        .sort_values("source")
        .reset_index(drop=True)
    )


def case_level_summary(cell: pd.DataFrame) -> pd.DataFrame:
    return (
        cell.groupby(["case", "source"], as_index=False)
        .agg(
            cells=("r", "size"),
            strict_wins=("gap_vs_strongest", lambda x: int((x > 0).sum())),
            strict_ci_wins=("gap_vs_strongest_ci95_low", lambda x: int((x > 0).sum())),
            mean_gap_vs_strongest=("gap_vs_strongest", "mean"),
            min_gap_vs_strongest=("gap_vs_strongest", "min"),
            mean_scrs=("scrs", "mean"),
            min_scrs=("scrs", "min"),
            max_scrs_se=("scrs_se", "max"),
            mean_gap_vs_score_shuffled=("gap_vs_scrs_score_shuffled", "mean"),
            mean_gap_vs_strategy_shuffled=("gap_vs_scrs_strategy_shuffled", "mean"),
        )
        .sort_values(["source", "case"])
        .reset_index(drop=True)
    )


def mechanism_level_summary(pairwise: pd.DataFrame) -> pd.DataFrame:
    key_controls = [
        "pnas",
        "csgc_gamma1",
        "csgc_gamma1_shuffled",
        "scrs_gamma1_score_shuffled",
        "scrs_gamma1_strategy_shuffled",
    ]
    view = pairwise[pairwise["control"].isin(key_controls)].copy()
    return (
        view.groupby(["source", "control"], as_index=False)
        .agg(
            cells=("r", "size"),
            positive_gaps=("gap", lambda x: int((x > 0).sum())),
            ci_positive_gaps=("gap_ci95_low", lambda x: int((x > 0).sum())),
            mean_gap=("gap", "mean"),
            min_gap=("gap", "min"),
            max_gap=("gap", "max"),
            mean_gap_se=("gap_se", "mean"),
        )
        .sort_values(["source", "control"])
        .reset_index(drop=True)
    )


def table(df: pd.DataFrame) -> str:
    view = df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: f"{x:.4f}")
    header = "| " + " | ".join(view.columns) + " |"
    divider = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    rows = ["| " + " | ".join(str(v) for v in row) + " |" for row in view.to_numpy()]
    return "\n".join([header, divider, *rows])


def write_outputs(out_root: Path, details: pd.DataFrame) -> None:
    summary, cell, source_summary, case_summary, mechanism_summary, pairwise = summarize(details)
    summary.to_csv(out_root / "summary.csv", index=False)
    cell.to_csv(out_root / "scrs_formal_cell_summary.csv", index=False)
    source_summary.to_csv(out_root / "scrs_formal_source_summary.csv", index=False)
    case_summary.to_csv(out_root / "scrs_formal_case_summary.csv", index=False)
    mechanism_summary.to_csv(out_root / "scrs_formal_mechanism_summary.csv", index=False)
    pairwise.to_csv(out_root / "scrs_formal_pairwise_gaps.csv", index=False)
    write_report(out_root, source_summary, case_summary, mechanism_summary, cell)


def decision_text(source_summary: pd.DataFrame, mechanism_summary: pd.DataFrame) -> list[str]:
    decisions: list[str] = []
    real = source_summary[source_summary["source"] == "real"]
    synthetic = source_summary[source_summary["source"] == "synthetic"]
    performance_pass = False
    if not real.empty and not synthetic.empty:
        performance_pass = (
            float(real.iloc[0]["min_scrs"]) >= 0.60
            and float(synthetic.iloc[0]["min_scrs"]) >= 0.95
            and float(source_summary["max_scrs_se"].max()) <= 0.02
        )
    decisions.append(
        "PERFORMANCE PASS: SCRS is formally stable under the predefined NC-oriented thresholds."
        if performance_pass
        else "PERFORMANCE CAUTION: at least one predefined stability threshold is not met."
    )

    role_rows = mechanism_summary[mechanism_summary["control"] == "scrs_gamma1_strategy_shuffled"]
    role_pass = (
        not role_rows.empty
        and int(role_rows["positive_gaps"].sum()) == int(role_rows["cells"].sum())
        and float(role_rows["mean_gap"].min()) > 0.0
    )
    decisions.append(
        "ROLE-SCREENING MECHANISM PASS: SCRS consistently exceeds the strategy-shuffled role-screening ablation."
        if role_pass
        else "ROLE-SCREENING MECHANISM CAUTION: SCRS does not consistently exceed the strategy-shuffled ablation."
    )

    score_rows = mechanism_summary[mechanism_summary["control"] == "scrs_gamma1_score_shuffled"]
    score_claim = (
        not score_rows.empty
        and int(score_rows["ci_positive_gaps"].sum()) >= math.ceil(0.75 * int(score_rows["cells"].sum()))
        and float(score_rows["mean_gap"].min()) > 0.02
    )
    decisions.append(
        "EDGE-SCORE MECHANISM PASS: edge-score selection has a material independent contribution."
        if score_claim
        else "EDGE-SCORE MECHANISM LIMITED: do not frame edge-score selection as the main independent driver unless follow-up evidence changes this."
    )
    return decisions


def write_report(
    out_root: Path,
    source_summary: pd.DataFrame,
    case_summary: pd.DataFrame,
    mechanism_summary: pd.DataFrame,
    cell: pd.DataFrame,
) -> None:
    report = [
        "# SCRS Formal NC Validation Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Scope",
        "",
        "Formal-scale SCRS validation for an NC-oriented evidence package. This run reuses the exact standalone simulator implementation from the s18 strict matched-control smoke script, with larger steps/reps and expanded reporting.",
        "",
        "## Scale",
        "",
        f"- Steps: {STEPS}",
        f"- Reps: {REPS}",
        f"- Tail window: {TAIL_WINDOW}",
        f"- r values: {', '.join(f'{r:.2f}' for r in R_VALUES)}",
        f"- Variants: {len(VARIANTS)}",
        f"- Total trials: {6 * len(VARIANTS) * len(R_VALUES) * REPS}",
        "",
        "## Decision",
        "",
        *decision_text(source_summary, mechanism_summary),
        "",
        "## Source Summary",
        "",
        table(source_summary),
        "",
        "## Case Summary",
        "",
        table(case_summary),
        "",
        "## Mechanism Summary",
        "",
        table(mechanism_summary),
        "",
        "## Cell Summary",
        "",
        table(cell),
        "",
        "## Interpretation Rules",
        "",
        "- Use `gap_vs_pnas` and `gap_vs_csgc` for performance effectiveness against classical and group-selection baselines.",
        "- Use `gap_vs_lfds_strongest` and `gap_vs_strongest` for strict matched-control robustness.",
        "- Use `gap_vs_scrs_strategy_shuffled` as the primary mechanism evidence for successful-cooperator role screening.",
        "- Use `gap_vs_scrs_score_shuffled` conservatively: small values mean edge-score group selection is not the main driver.",
    ]
    (out_root / "SCRS_formal_NC_validation_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def write_metadata(out_root: Path, backend: Any, workers: int) -> None:
    metadata = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "objective": "NC-oriented formal SCRS validation: stability plus mechanism separation",
        "project": str(PROJECT),
        "backend_script": str(BACKEND_SCRIPT),
        "steps": STEPS,
        "reps": REPS,
        "tail_window": TAIL_WINDOW,
        "subgraph_duration": SUBGRAPH_DURATION,
        "selection_intensity": SELECTION_INTENSITY,
        "ewma_window": EWMA_WINDOW,
        "seed": SEED,
        "r_values": R_VALUES,
        "variants": VARIANTS,
        "cases": [case.__dict__ for case in backend.CASES],
        "workers": workers,
        "input_reports": [
            str(
                PROJECT
                / "supplemental_lfds_runs"
                / "s19_scrs_performance_stability_smoke_20260731_1035"
                / "SCRS_performance_stability_smoke_report.md"
            ),
            str(
                PROJECT
                / "supplemental_lfds_runs"
                / "s18_scrs_strict_smoke_20260731_1015"
                / "SCRS_strict_matched_smoke_report.md"
            ),
        ],
    }
    (out_root / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (out_root / "SCRS_formal_NC_validation_design.md").write_text(FORMAL_DESIGN, encoding="utf-8")
    shutil.copy2(Path(__file__), out_root / "run_scrs_formal_nc_validation.py")
    shutil.copy2(BACKEND_SCRIPT, out_root / "backend_run_scrs_strict_smoke.py")


def write_status(out_root: Path, payload: dict[str, Any]) -> None:
    tmp = out_root / "status.json.tmp"
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(out_root / "status.json")


def seconds_to_text(seconds: float) -> str:
    if not math.isfinite(seconds) or seconds < 0:
        return "unknown"
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days:
        return f"{days}d {hours}h {minutes}m"
    if hours:
        return f"{hours}h {minutes}m"
    return f"{minutes}m {sec}s"


def run(args: argparse.Namespace) -> None:
    if not BACKEND_SCRIPT.exists():
        raise FileNotFoundError(BACKEND_SCRIPT)
    backend = load_backend(BACKEND_SCRIPT)
    out_root = Path(args.out_root).expanduser()
    if args.plan_only:
        print(FORMAL_DESIGN)
        print(f"Output root would be: {out_root}")
        print(f"Total trials: {len(backend.CASES) * len(VARIANTS) * len(R_VALUES) * REPS}")
        return

    out_root.mkdir(parents=True, exist_ok=args.resume)
    detail_path = out_root / "detail.csv"
    write_metadata(out_root, backend, args.workers)

    tasks = build_tasks(backend, detail_path)
    total = len(backend.CASES) * len(VARIANTS) * len(R_VALUES) * REPS
    already_done = total - len(tasks)
    started = time.time()
    print(f"Output root: {out_root}", flush=True)
    print(f"Formal trials: total={total}, completed={already_done}, pending={len(tasks)}", flush=True)
    if not tasks:
        details = pd.read_csv(detail_path)
        write_outputs(out_root, details)
        print("No pending trials. Outputs refreshed.", flush=True)
        return

    fieldnames = [
        "case",
        "source",
        "variant",
        "r",
        "rep",
        "tail_coop",
        "final_coop",
        "csgc_selection_lift",
        "scrs_role_coop_rate",
        "conformist_update_rate",
        "fermi_update_rate",
    ]
    write_header = not detail_path.exists() or detail_path.stat().st_size == 0
    completed_now = 0
    next_status_at = 0
    with detail_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
            handle.flush()
        with mp.Pool(processes=args.workers, initializer=init_worker, initargs=(str(BACKEND_SCRIPT),)) as pool:
            for row in pool.imap_unordered(run_one, tasks, chunksize=args.chunksize):
                writer.writerow(row)
                completed_now += 1
                if completed_now % args.flush_every == 0:
                    handle.flush()
                    os.fsync(handle.fileno())
                completed_total = already_done + completed_now
                elapsed = time.time() - started
                rate = completed_now / elapsed if elapsed > 0 else 0.0
                remaining = (len(tasks) - completed_now) / rate if rate > 0 else math.inf
                if completed_now >= next_status_at or completed_now == len(tasks):
                    status = {
                        "state": "running" if completed_now < len(tasks) else "summarizing",
                        "output_root": str(out_root),
                        "total_trials": total,
                        "completed_trials": completed_total,
                        "pending_trials": total - completed_total,
                        "completed_this_run": completed_now,
                        "workers": args.workers,
                        "elapsed_seconds_this_run": elapsed,
                        "trials_per_second_this_run": rate,
                        "estimated_remaining_seconds": remaining,
                        "estimated_remaining_text": seconds_to_text(remaining),
                        "last_update": datetime.now().isoformat(timespec="seconds"),
                    }
                    write_status(out_root, status)
                    print(
                        f"finished {completed_total}/{total}; "
                        f"rate={rate:.3f} trials/s; eta={seconds_to_text(remaining)}",
                        flush=True,
                    )
                    next_status_at = completed_now + args.progress_every
        handle.flush()
        os.fsync(handle.fileno())

    details = pd.read_csv(detail_path)
    write_outputs(out_root, details)
    write_status(
        out_root,
        {
            "state": "complete",
            "output_root": str(out_root),
            "total_trials": total,
            "completed_trials": len(details),
            "pending_trials": max(0, total - len(details)),
            "workers": args.workers,
            "last_update": datetime.now().isoformat(timespec="seconds"),
            "report": str(out_root / "SCRS_formal_NC_validation_report.md"),
        },
    )
    print(f"Formal SCRS validation complete: {out_root}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run formal-scale SCRS validation for NC-oriented evidence.")
    parser.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT), help="New output directory for this formal run.")
    parser.add_argument("--workers", type=int, default=min(6, max(1, (os.cpu_count() or 2) - 1)))
    parser.add_argument("--chunksize", type=int, default=1)
    parser.add_argument("--flush-every", type=int, default=1)
    parser.add_argument("--progress-every", type=int, default=20)
    parser.add_argument("--resume", action="store_true", help="Resume an existing output directory.")
    parser.add_argument("--plan-only", action="store_true", help="Print design and exit without creating outputs.")
    args = parser.parse_args()
    if args.workers < 1:
        raise ValueError("--workers must be >= 1")
    if args.chunksize < 1:
        raise ValueError("--chunksize must be >= 1")
    if args.flush_every < 1:
        raise ValueError("--flush-every must be >= 1")
    if args.progress_every < 1:
        raise ValueError("--progress-every must be >= 1")
    return args


if __name__ == "__main__":
    run(parse_args())
