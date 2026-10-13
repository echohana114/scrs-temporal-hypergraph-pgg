#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path("/Users/hui/Documents/New project 2/temporal_hypergraph_pgg_pilot")
RUNS = {
    "S20": PROJECT / "supplemental_lfds_runs/s20_scrs_formal_nc_validation_20260824_2037",
    "S21": PROJECT / "supplemental_lfds_runs/s21_scrs_nc_parameter_robustness_20260828_1133",
    "S22": PROJECT / "supplemental_lfds_runs/s22_scrs_nc_real_nulls_20260831_1238",
    "S23": PROJECT / "supplemental_lfds_runs/s23_scrs_nc_synthetic_stress_20260831_1633",
    "S24": PROJECT / "supplemental_lfds_runs/s24_scrs_nc_noise_horizon_20260901_0304",
    "S25": PROJECT / "supplemental_lfds_runs/s25_scrs_nc_mechanism_decomposition_20260901_1613",
    "S26": PROJECT / "supplemental_lfds_runs/s26_scrs_nc_empirical_extrapolation_20260901_2023",
    "S27": PROJECT / "supplemental_lfds_runs/s27_scrs_nc_payoff_update_sensitivity_20260902_0025",
}
EXTERNAL_MANIFEST = (
    PROJECT
    / "real_data_external_s26/prepared_20260901_2023/s26_external_real_manifest.json"
)
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
LOCAL_PROJECT = PACKAGE_ROOT.parent
OUT = PACKAGE_ROOT / "source_data"
SUPP = OUT / "supplementary"
TABLES = PACKAGE_ROOT / "tables"
RELEASE = PACKAGE_ROOT / "release"
SUPPLEMENTAL_RUNS = {
    "S28": LOCAL_PROJECT
    / "supplemental_lfds_runs/s28_scrs_nc_construction_sensitivity_formal_20261010_195700",
    "S29": LOCAL_PROJECT
    / "supplemental_lfds_runs/s29_scrs_nc_mechanism_context_controls_formal_20261010_153000",
    "S30": LOCAL_PROJECT
    / "supplemental_lfds_runs/s30_scrs_nc_structure_moderator_formal_20261012_012352",
}


CONTROL_LABELS = {
    "pnas": "Wang et al. temporal-hypergraph imitation",
    "wang_temporal_hypergraph": "Wang et al. temporal-hypergraph imitation",
    "csgc_gamma1": "CSGC edge-context selection",
    "csgc_gamma1_shuffled": "CSGC score shuffled",
    "scrs_gamma1_strategy_shuffled": "Strategy-shuffled SCRS",
    "scrs_gamma1_score_shuffled": "Score-shuffled SCRS",
    "scrs_gamma1_cooperator_only_random": "Cooperator-only random role",
    "scrs_gamma1_payoff_only_role": "Payoff-only role",
    "scrs_gamma1_success_only_no_coop_filter": "Success-only role without cooperator filter",
    "scrs_gamma1_random_role_same_edge": "Random role on selected edge",
    "scrs_gamma1_cooperator_only_uniform_incident": "Uniform incident-edge cooperator search",
    "scrs_gamma1_cooperator_only_random_neighborhood": "Random local-neighborhood cooperator search",
    "scrs_gamma1_success_without_score_ranking": "Successful edge without score ranking",
    "lfds_l050": "LFDS lambda 0.50",
    "lfds_l075": "LFDS lambda 0.75",
    "lfds_l075_budget": "LFDS lambda 0.75 budget control",
}


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path, keep_default_na=False)


def clean_dataset_label(value: str) -> str:
    labels = {
        "real_highschool2013": "High school 2013",
        "real_workplace2013": "Workplace 2013",
        "real_hospitalward2010": "Hospital ward 2010",
        "real_sfhh2009": "SFHH 2009",
        "synthetic_structured_ring": "Structured ring",
        "synthetic_community": "Community synthetic",
        "synthetic_stress_community_resample_n100": "Community, n=100",
        "synthetic_stress_community_resample_n200": "Community, n=200",
        "synthetic_stress_community_resample_n400": "Community, n=400",
        "synthetic_stress_heterogeneous_activity_n100": "Heterogeneous activity, n=100",
        "synthetic_stress_heterogeneous_activity_n200": "Heterogeneous activity, n=200",
        "synthetic_stress_heterogeneous_activity_n400": "Heterogeneous activity, n=400",
        "synthetic_stress_structured_ring_n100": "Structured ring, n=100",
        "synthetic_stress_structured_ring_n200": "Structured ring, n=200",
        "synthetic_stress_structured_ring_n400": "Structured ring, n=400",
        "synthetic_stress_temporal_modular_switching_n100": "Temporal modular switching, n=100",
        "synthetic_stress_temporal_modular_switching_n200": "Temporal modular switching, n=200",
        "synthetic_stress_temporal_modular_switching_n400": "Temporal modular switching, n=400",
        "synthetic_stress_uniform_random_n100": "Uniform random, n=100",
        "synthetic_stress_uniform_random_n200": "Uniform random, n=200",
        "synthetic_stress_uniform_random_n400": "Uniform random, n=400",
        "external_copenhagen_bluetooth": "Copenhagen Bluetooth",
        "external_email_eu": "Email-EU",
        "external_congress_bills": "Congress bills",
        "external_threads_ask_ubuntu": "Ask Ubuntu threads",
        "external_email_enron": "Email-Enron",
    }
    return labels.get(value, value.replace("_", " "))


def write(df: pd.DataFrame, filename: str, source: str, manifest: list[dict[str, str]]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / filename
    df.to_csv(path, index=False)
    manifest.append(
        {
            "file": str(path.relative_to(PACKAGE_ROOT)),
            "rows": str(len(df)),
            "source": source,
        }
    )
    return path


def copy_summary(src: Path, dest_name: str, source: str, manifest: list[dict[str, str]]) -> None:
    if not src.exists():
        return
    SUPP.mkdir(parents=True, exist_ok=True)
    dest = SUPP / dest_name
    shutil.copy2(src, dest)
    manifest.append(
        {
            "file": str(dest.relative_to(PACKAGE_ROOT)),
            "rows": str(sum(1 for _ in dest.open("r", encoding="utf-8")) - 1),
            "source": source,
        }
    )


def add_label_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "case" in out.columns:
        out["dataset_label"] = out["case"].map(clean_dataset_label)
    if "control" in out.columns:
        out["control_label"] = out["control"].map(CONTROL_LABELS).fillna(out["control"])
    return out


def numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def gap_ci_summary(values: pd.Series) -> dict[str, float | int]:
    clean = numeric_series(values).dropna()
    count = int(clean.shape[0])
    mean = float(clean.mean()) if count else float("nan")
    sd = float(clean.std(ddof=1)) if count > 1 else 0.0
    se = sd / math.sqrt(count) if count > 1 else 0.0
    return {
        "cells": count,
        "mean_gap": mean,
        "sd_gap": sd,
        "gap_se": se,
        "gap_ci95_low": mean - 1.96 * se,
        "gap_ci95_high": mean + 1.96 * se,
        "min_gap": float(clean.min()) if count else float("nan"),
        "max_gap": float(clean.max()) if count else float("nan"),
    }


def cell_level_inference(values: pd.Series, rng: np.random.Generator, bootstrap_reps: int = 10000) -> dict[str, float | int]:
    clean = numeric_series(values).dropna().to_numpy(dtype=float)
    count = int(clean.shape[0])
    if count == 0:
        return {
            "cells": 0,
            "mean_gap": float("nan"),
            "bootstrap_ci95_low": float("nan"),
            "bootstrap_ci95_high": float("nan"),
            "sign_permutation_p_two_sided": float("nan"),
            "sign_permutation_p_positive": float("nan"),
        }
    mean = float(clean.mean())
    if count == 1:
        return {
            "cells": count,
            "mean_gap": mean,
            "bootstrap_ci95_low": mean,
            "bootstrap_ci95_high": mean,
            "sign_permutation_p_two_sided": 1.0,
            "sign_permutation_p_positive": 0.5 if mean > 0 else 1.0,
        }
    samples = rng.choice(clean, size=(bootstrap_reps, count), replace=True).mean(axis=1)
    if count <= 16:
        masks = np.arange(2**count, dtype=np.uint64)[:, None]
        bits = ((masks >> np.arange(count, dtype=np.uint64)) & 1).astype(float)
        signs = np.where(bits == 1.0, 1.0, -1.0)
        permuted = (signs * clean).mean(axis=1)
    else:
        signs = rng.choice([-1.0, 1.0], size=(50000, count), replace=True)
        permuted = (signs * clean).mean(axis=1)
    return {
        "cells": count,
        "mean_gap": mean,
        "bootstrap_ci95_low": float(np.quantile(samples, 0.025)),
        "bootstrap_ci95_high": float(np.quantile(samples, 0.975)),
        "sign_permutation_p_two_sided": float(np.mean(np.abs(permuted) >= abs(mean))),
        "sign_permutation_p_positive": float(np.mean(permuted >= mean)),
    }


def unique_join(series: pd.Series) -> str:
    values = []
    for value in series.dropna().tolist():
        text = str(value)
        if text and text.lower() != "nan" and text not in values:
            values.append(text)
    return "; ".join(values)


def format_unique(series: pd.Series, limit: int = 8) -> str:
    values = []
    for value in series.dropna().tolist():
        text = str(value)
        if not text or text.lower() == "nan":
            continue
        if text.endswith(".0"):
            text = text[:-2]
        if text not in values:
            values.append(text)
    try:
        values = [str(v) for v in sorted({float(v) for v in values})]
        values = [v[:-2] if v.endswith(".0") else v for v in values]
    except ValueError:
        values = sorted(values)
    if len(values) > limit:
        shown = ", ".join(values[:limit])
        return f"{shown}, ... ({len(values)} values)"
    return ", ".join(values)


def markdown_table(df: pd.DataFrame, title: str) -> str:
    columns = list(df.columns)
    lines = [f"# {title}", "", f"Rows: {len(df)}.", ""]
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for row in df.itertuples(index=False, name=None):
        cells = [str(value).replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def write_table(df: pd.DataFrame, stem: str, title: str, manifest: list[dict[str, str]]) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    csv_path = TABLES / f"{stem}.csv"
    md_path = TABLES / f"{stem}.md"
    df.to_csv(csv_path, index=False)
    md_path.write_text(markdown_table(df, title), encoding="utf-8")
    manifest.append(
        {
            "table": stem,
            "outputs": f"tables/{stem}.csv;tables/{stem}.md",
            "rows": str(len(df)),
        }
    )


def csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    return max(0, sum(1 for _ in path.open("r", encoding="utf-8")) - 1)


def sequence_stats(path_text: str) -> tuple[str, str]:
    if not path_text:
        return "", ""
    path = Path(path_text)
    if not path.exists():
        return "", ""
    frame = pd.read_csv(path, usecols=["block"])
    return str(int(frame["block"].nunique())), str(int(frame.shape[0]))


def prepared_real_contact_counts(path_text: str) -> tuple[str, str]:
    if not path_text:
        return "", ""
    sequence_path = Path(path_text)
    metadata_path = sequence_path.with_name("real_sequence_metadata.json")
    if not metadata_path.exists():
        return "", ""
    with metadata_path.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    stats_path = Path(metadata.get("stats_path", "") or sequence_path.with_name("real_sequence_block_stats.csv"))
    if not stats_path.exists():
        return "", ""
    stats = read_csv(stats_path)
    if "contact_rows" not in stats.columns:
        return "", ""
    contact_rows = int(pd.to_numeric(stats["contact_rows"], errors="coerce").fillna(0).sum())
    return str(contact_rows), str(contact_rows)


def package_version(package: str) -> str:
    try:
        return version(package)
    except PackageNotFoundError:
        return "not installed"


def fig1_source(manifest: list[dict[str, str]]) -> None:
    rows = [
        {
            "order": 1,
            "stage": "Temporal hypergraph context",
            "description": "Time-resolved higher-order interaction window H_t=(V,E_t), shown as focal learner i with incident hyperedges containing cooperators and defectors.",
            "claim_role": "input structure and group context",
        },
        {
            "order": 2,
            "stage": "Success-context selection",
            "description": "The cooperative-success score G_e(t)=q_e(t)*max(0,r*n_C(e,t)-1) ranks or samples the focal node's incident hyperedges; e* is the selected successful-group context.",
            "claim_role": "auxiliary context layer",
        },
        {
            "order": 3,
            "stage": "Cooperative role-model screen",
            "description": "Within the same selected hyperedge e*, eligible cooperators are screened as role models; successful defectors contribute to context success but are not cooperative role models.",
            "claim_role": "main supported mechanism",
        },
        {
            "order": 4,
            "stage": "Operational rule equations",
            "description": "The figure lists the accumulated payoff, context score, eligible cooperative candidate set and Fermi strategy-adoption probability.",
            "claim_role": "model definition",
        },
    ]
    write(pd.DataFrame(rows), "fig1_model_diagram_flow.csv", "SCRS model schematic source table", manifest)


def fig2_source(manifest: list[dict[str, str]]) -> None:
    root = RUNS["S20"]
    cell = add_label_columns(read_csv(root / "scrs_formal_cell_summary.csv"))
    source = read_csv(root / "scrs_formal_source_summary.csv")
    mech = read_csv(root / "scrs_formal_mechanism_summary.csv")

    write(
        cell[
            [
                "case",
                "dataset_label",
                "source",
                "r",
                "scrs",
                "scrs_se",
                "scrs_ci95_low",
                "scrs_ci95_high",
                "scrs_final",
                "gap_vs_pnas",
                "gap_vs_csgc",
                "gap_vs_csgc_shuffled",
                "gap_vs_scrs_score_shuffled",
                "gap_vs_scrs_strategy_shuffled",
                "gap_vs_lfds_strongest",
                "strongest_control",
                "strongest_control_tail",
                "scrs_role_coop_rate",
                "scrs_csgc_selection_lift",
            ]
        ],
        "fig2a_s20_scrs_tail_by_case.csv",
        "S20 scrs_formal_cell_summary.csv",
        manifest,
    )

    gap_comparisons = [
        ("gap_vs_pnas", "wang_temporal_hypergraph", "Wang et al. temporal-hypergraph imitation", "pnas"),
        ("gap_vs_csgc", "csgc_gamma1", "CSGC edge-context selection", "csgc_gamma1"),
        ("gap_vs_lfds_strongest", "lfds_strongest", "Strongest LFDS matched control", "lfds_strongest"),
        (
            "gap_vs_scrs_strategy_shuffled",
            "scrs_gamma1_strategy_shuffled",
            "Strategy-shuffled SCRS",
            "scrs_gamma1_strategy_shuffled",
        ),
        (
            "gap_vs_scrs_score_shuffled",
            "scrs_gamma1_score_shuffled",
            "Score-shuffled SCRS",
            "scrs_gamma1_score_shuffled",
        ),
    ]
    gap_cell_rows: list[dict[str, object]] = []
    for row in cell.itertuples(index=False):
        for gap_col, key, label, control_variant in gap_comparisons:
            gap_cell_rows.append(
                {
                    "case": row.case,
                    "dataset_label": row.dataset_label,
                    "source": row.source,
                    "r": row.r,
                    "comparison_key": key,
                    "comparison_label": label,
                    "control_variant": control_variant,
                    "gap": float(getattr(row, gap_col)),
                    "note": "Positive values favor SCRS.",
                }
            )
    gap_cells = pd.DataFrame(gap_cell_rows)
    write(
        gap_cells.sort_values(["source", "comparison_key", "case", "r"]),
        "fig2b_s20_gap_cells_for_forest.csv",
        "S20 cell-level SCRS gaps used for forest/dot-CI panel",
        manifest,
    )

    control_to_key = {
        "pnas": "wang_temporal_hypergraph",
        "csgc_gamma1": "csgc_gamma1",
        "scrs_gamma1_strategy_shuffled": "scrs_gamma1_strategy_shuffled",
        "scrs_gamma1_score_shuffled": "scrs_gamma1_score_shuffled",
    }
    ci_lookup = {
        (row.source, control_to_key.get(row.control, row.control)): int(row.ci_positive_gaps)
        for row in mech.itertuples(index=False)
        if hasattr(row, "ci_positive_gaps")
    }

    forest_rows: list[dict[str, object]] = []
    for (source_name, key, label), group in gap_cells.groupby(["source", "comparison_key", "comparison_label"]):
        summary = gap_ci_summary(group["gap"])
        forest_rows.append(
            {
                "source": source_name,
                "comparison_key": key,
                "comparison_label": label,
                **summary,
                "ci_positive_cells": ci_lookup.get((source_name, key), ""),
                "note": "Across matched case-r cells; intervals are approximate 95% CIs over cells.",
            }
        )
    forest = pd.DataFrame(forest_rows)
    write(
        forest.sort_values(["source", "comparison_key"]),
        "fig2b_s20_gap_forest_summary.csv",
        "S20 forest summary from cell-level SCRS gaps",
        manifest,
    )

    rows: list[dict[str, object]] = []
    comparisons = [
        (
            "wang_temporal_hypergraph",
            "Wang et al. temporal-hypergraph imitation",
            "mean_gap_vs_pnas",
            "min_gap_vs_pnas",
        ),
        ("csgc_gamma1", "CSGC edge-context selection", "mean_gap_vs_csgc", "min_gap_vs_csgc"),
        ("lfds_strongest", "Strongest LFDS matched control", "", ""),
        (
            "scrs_gamma1_strategy_shuffled",
            "Strategy-shuffled SCRS",
            "mean_gap_vs_strategy_shuffled",
            "min_gap_vs_strategy_shuffled",
        ),
        (
            "scrs_gamma1_score_shuffled",
            "Score-shuffled SCRS",
            "mean_gap_vs_score_shuffled",
            "min_gap_vs_score_shuffled",
        ),
    ]
    for row in source.itertuples(index=False):
        for key, label, mean_col, min_col in comparisons:
            if key == "lfds_strongest":
                lfds_subset = forest[(forest["source"] == row.source) & (forest["comparison_key"] == key)].iloc[0]
                mean_gap = float(lfds_subset["mean_gap"])
                min_gap = float(lfds_subset["min_gap"])
            else:
                mean_gap = float(getattr(row, mean_col))
                min_gap = float(getattr(row, min_col))
            rows.append(
                {
                    "source": row.source,
                    "comparison_key": key,
                    "comparison_label": label,
                    "mean_gap": mean_gap,
                    "min_gap": min_gap,
                    "cells": int(row.cells),
                    "ci_positive_cells": ci_lookup.get((row.source, key), ""),
                    "note": "Positive values favor SCRS.",
                }
            )
    gap = pd.DataFrame(rows)
    write(gap, "fig2b_s20_mean_gaps_by_source.csv", "S20 source/cell/mechanism summaries", manifest)


def fig3_source(manifest: list[dict[str, str]]) -> None:
    root = RUNS["S25"]
    wanted = [
        "scrs_gamma1_strategy_shuffled",
        "scrs_gamma1_payoff_only_role",
        "scrs_gamma1_success_only_no_coop_filter",
        "scrs_gamma1_random_role_same_edge",
        "scrs_gamma1_cooperator_only_random",
        "scrs_gamma1_score_shuffled",
    ]
    paired = add_label_columns(read_csv(root / "scrs_nc_paired_gap_summary.csv"))
    paired = paired[paired["control"].isin(wanted)].copy()
    paired["control_order"] = paired["control"].map({name: idx for idx, name in enumerate(wanted)})
    write(
        paired.sort_values(["source", "control_order", "case", "r"]),
        "fig3_s25_mechanism_paired_gaps_by_cell.csv",
        "S25 scrs_nc_paired_gap_summary.csv",
        manifest,
    )
    mech = add_label_columns(read_csv(root / "scrs_nc_mechanism_summary.csv"))
    mech = mech[mech["control"].isin(wanted)].copy()
    mech["control_order"] = mech["control"].map({name: idx for idx, name in enumerate(wanted)})
    write(
        mech.sort_values(["source", "control_order"]),
        "fig3_s25_mechanism_mean_gaps.csv",
        "S25 scrs_nc_mechanism_summary.csv",
        manifest,
    )


def fig4_source(manifest: list[dict[str, str]]) -> None:
    s21 = RUNS["S21"]
    s22 = RUNS["S22"]
    s23 = RUNS["S23"]
    s21_cell = add_label_columns(read_csv(s21 / "scrs_nc_cell_summary.csv"))
    s24_cell = add_label_columns(read_csv(RUNS["S24"] / "scrs_nc_cell_summary.csv"))
    write(s21_cell, "fig4a_s21_robustness_cell_summary.csv", "S21 cell summary", manifest)
    write(add_label_columns(read_csv(s21 / "scrs_nc_source_summary.csv")), "fig4a_s21_robustness_source_summary.csv", "S21 source summary", manifest)
    phase_r_rho0 = s21_cell[s21_cell["condition"] == "rho0_sweep"].copy()
    for column in ["r", "rho0", "scrs", "gap_vs_scrs_gamma1_strategy_shuffled", "gap_vs_scrs_gamma1_score_shuffled"]:
        phase_r_rho0[column] = numeric_series(phase_r_rho0[column])
    phase_r_rho0 = (
        phase_r_rho0.groupby(["source", "r", "rho0"], as_index=False)
        .agg(
            cells=("case", "nunique"),
            mean_scrs=("scrs", "mean"),
            min_scrs=("scrs", "min"),
            mean_gap_vs_strategy_shuffled=("gap_vs_scrs_gamma1_strategy_shuffled", "mean"),
            mean_gap_vs_score_shuffled=("gap_vs_scrs_gamma1_score_shuffled", "mean"),
        )
        .sort_values(["source", "rho0", "r"])
    )
    write(
        phase_r_rho0,
        "fig4a_s21_phase_r_rho0.csv",
        "S21 rho0 sweep summarized as r-by-rho0 phase diagram",
        manifest,
    )
    for column in ["r", "mutation_rate", "scrs", "gap_vs_scrs_gamma1_strategy_shuffled"]:
        s24_cell[column] = numeric_series(s24_cell[column])
    phase_r_mutation = (
        s24_cell.groupby(["source", "r", "mutation_rate"], as_index=False)
        .agg(
            cells=("case", "nunique"),
            mean_scrs=("scrs", "mean"),
            min_scrs=("scrs", "min"),
            mean_gap_vs_strategy_shuffled=("gap_vs_scrs_gamma1_strategy_shuffled", "mean"),
        )
        .sort_values(["source", "mutation_rate", "r"])
    )
    write(
        phase_r_mutation,
        "fig4b_s24_phase_r_mutation.csv",
        "S24 long-horizon noise summarized as r-by-mutation phase diagram",
        manifest,
    )
    write(add_label_columns(read_csv(s22 / "scrs_nc_cell_summary.csv")), "fig4b_s22_real_nulls_cell_summary.csv", "S22 cell summary", manifest)
    write(add_label_columns(read_csv(s22 / "scrs_nc_mechanism_summary.csv")), "fig4b_s22_real_nulls_mechanism_summary.csv", "S22 mechanism summary", manifest)
    write(add_label_columns(read_csv(s23 / "scrs_nc_cell_summary.csv")), "fig4c_s23_synthetic_stress_cell_summary.csv", "S23 cell summary", manifest)
    write(add_label_columns(read_csv(s23 / "scrs_nc_case_summary.csv")), "fig4c_s23_synthetic_stress_case_summary.csv", "S23 case summary", manifest)


def fig5_source(manifest: list[dict[str, str]]) -> None:
    s24 = RUNS["S24"]
    s26 = RUNS["S26"]
    s27 = RUNS["S27"]
    write(add_label_columns(read_csv(s26 / "scrs_nc_case_summary.csv")), "fig5a_s26_external_empirical_cases.csv", "S26 case summary", manifest)
    write(add_label_columns(read_csv(s26 / "scrs_nc_paired_gap_summary.csv")), "fig5a_s26_external_paired_gaps_by_cell.csv", "S26 paired gap summary", manifest)

    with EXTERNAL_MANIFEST.open("r", encoding="utf-8") as handle:
        external_manifest = json.load(handle)
    external = pd.DataFrame(external_manifest["prepared_datasets"])
    write(external, "fig5a_s26_external_dataset_manifest.csv", "S26 external manifest", manifest)

    write(add_label_columns(read_csv(s27 / "scrs_nc_source_summary.csv")), "fig5b_s27_payoff_update_source_summary.csv", "S27 source summary", manifest)
    write(add_label_columns(read_csv(s27 / "scrs_nc_paired_gap_summary.csv")), "fig5b_s27_payoff_update_paired_gaps_by_cell.csv", "S27 paired gap summary", manifest)

    write(add_label_columns(read_csv(s24 / "scrs_nc_cell_summary.csv")), "fig5c_s24_noise_horizon_cell_summary.csv", "S24 cell summary", manifest)
    trajectory = read_csv(s24 / "trajectory.csv")
    trajectory["coop"] = pd.to_numeric(trajectory["coop"], errors="coerce")
    grouped = (
        trajectory.groupby(
            ["case", "source", "variant", "r", "selection_intensity", "rho0", "mutation_rate", "step"],
            as_index=False,
            dropna=False,
        )
        .agg(
            reps=("rep", "nunique"),
            coop_mean=("coop", "mean"),
            coop_sd=("coop", lambda x: float(x.std(ddof=1)) if len(x) > 1 else 0.0),
        )
        .sort_values(["case", "variant", "r", "mutation_rate", "step"])
    )
    grouped["coop_se"] = grouped.apply(
        lambda row: row.coop_sd / math.sqrt(row.reps) if int(row.reps) > 1 else 0.0,
        axis=1,
    )
    grouped["coop_ci95_low"] = grouped["coop_mean"] - 1.96 * grouped["coop_se"]
    grouped["coop_ci95_high"] = grouped["coop_mean"] + 1.96 * grouped["coop_se"]
    write(add_label_columns(grouped), "fig5c_s24_noise_horizon_trajectory_summary.csv", "S24 trajectory.csv", manifest)


def cell_level_inference_source(manifest: list[dict[str, str]]) -> None:
    rng = np.random.default_rng(20260925)
    rows: list[dict[str, str | float | int]] = []

    def add_grouped(
        analysis: str,
        filename: str,
        value_column: str,
        group_columns: list[str],
        label_columns: list[str],
    ) -> None:
        frame = read_csv(OUT / filename)
        frame[value_column] = numeric_series(frame[value_column])
        for keys, group in frame.groupby(group_columns, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            record: dict[str, str | float | int] = {
                "analysis": analysis,
                "source_file": f"source_data/{filename}",
                "gap_column": value_column,
            }
            record.update({column: value for column, value in zip(group_columns, keys)})
            for column in label_columns:
                if column in group.columns:
                    record[column] = unique_join(group[column])
            record.update(cell_level_inference(group[value_column], rng))
            rows.append(record)

    add_grouped(
        "main_validation",
        "fig2b_s20_gap_cells_for_forest.csv",
        "gap",
        ["source", "comparison_key"],
        ["comparison_label"],
    )
    add_grouped(
        "mechanism_decomposition",
        "fig3_s25_mechanism_paired_gaps_by_cell.csv",
        "mean_gap",
        ["source", "control"],
        ["control_label"],
    )

    null_cells = read_csv(OUT / "fig4b_s22_real_nulls_cell_summary.csv")
    null_map = {
        "gap_vs_pnas": "Wang et al. temporal-hypergraph imitation",
        "gap_vs_csgc_gamma1": "CSGC edge-context selection",
        "gap_vs_scrs_gamma1_strategy_shuffled": "Strategy-shuffled SCRS",
        "gap_vs_scrs_gamma1_score_shuffled": "Score-shuffled SCRS",
    }
    null_rows = []
    for column, label in null_map.items():
        if column not in null_cells.columns:
            continue
        subset = null_cells[["source", "null_model", column]].copy()
        subset = subset.rename(columns={column: "gap"})
        subset["comparison_key"] = column.replace("gap_vs_", "")
        subset["comparison_label"] = label
        null_rows.append(subset)
    null_long = pd.concat(null_rows, ignore_index=True)
    write(
        null_long,
        "fig4c_s22_real_nulls_gap_cells_long.csv",
        "S22 real-null paired gaps reshaped for cell-level inference",
        manifest,
    )
    add_grouped(
        "null_model_audit",
        "fig4c_s22_real_nulls_gap_cells_long.csv",
        "gap",
        ["source", "null_model", "comparison_key"],
        ["comparison_label"],
    )

    add_grouped(
        "external_extrapolation",
        "fig5a_s26_external_paired_gaps_by_cell.csv",
        "mean_gap",
        ["source", "control"],
        ["control_label"],
    )
    add_grouped(
        "payoff_update_sensitivity",
        "fig5b_s27_payoff_update_paired_gaps_by_cell.csv",
        "mean_gap",
        ["source", "condition", "control"],
        ["control_label", "payoff_mode", "update_mode"],
    )

    s29 = read_csv(SUPPLEMENTAL_RUNS["S29"] / "S29_paired_gap_summary.csv")
    s29["mean_gap"] = numeric_series(s29["mean_gap"])
    for keys, group in s29.groupby(["source", "control"], dropna=False):
        source, control = keys
        record = {
            "analysis": "clean_mechanism_context",
            "source_file": "source_data/supplementary/S29_paired_gap_summary.csv",
            "source": source,
            "control": control,
            "control_label": CONTROL_LABELS.get(str(control), str(control)),
            "gap_column": "mean_gap",
        }
        record.update(cell_level_inference(group["mean_gap"], rng))
        rows.append(record)

    summary = pd.DataFrame(rows)
    leading = [
        "analysis",
        "source_file",
        "source",
        "condition",
        "null_model",
        "comparison_key",
        "control",
        "comparison_label",
        "control_label",
        "payoff_mode",
        "update_mode",
        "gap_column",
        "cells",
        "mean_gap",
        "bootstrap_ci95_low",
        "bootstrap_ci95_high",
        "sign_permutation_p_two_sided",
        "sign_permutation_p_positive",
    ]
    ordered = [column for column in leading if column in summary.columns]
    ordered.extend([column for column in summary.columns if column not in ordered])
    write(
        summary[ordered],
        "cell_level_inference_summary.csv",
        "Cell-level paired bootstrap and sign-permutation summaries for main paired claims",
        manifest,
    )


def supplementary_sources(manifest: list[dict[str, str]]) -> None:
    files = {
        "S20": [
            "scrs_formal_source_summary.csv",
            "scrs_formal_case_summary.csv",
            "scrs_formal_cell_summary.csv",
            "scrs_formal_mechanism_summary.csv",
            "scrs_formal_pairwise_gaps.csv",
        ],
        "S21": [
            "scrs_nc_source_summary.csv",
            "scrs_nc_case_summary.csv",
            "scrs_nc_cell_summary.csv",
            "scrs_nc_mechanism_summary.csv",
            "summary.csv",
            "qa_summary.json",
        ],
        "S22": [
            "scrs_nc_source_summary.csv",
            "scrs_nc_case_summary.csv",
            "scrs_nc_cell_summary.csv",
            "scrs_nc_mechanism_summary.csv",
            "scrs_nc_pairwise_gap_summary.csv",
            "scrs_nc_paired_gap_summary.csv",
            "summary.csv",
            "qa_summary.json",
        ],
        "S23": [
            "scrs_nc_source_summary.csv",
            "scrs_nc_case_summary.csv",
            "scrs_nc_cell_summary.csv",
            "scrs_nc_mechanism_summary.csv",
            "scrs_nc_pairwise_gap_summary.csv",
            "scrs_nc_paired_gap_summary.csv",
            "summary.csv",
            "qa_summary.json",
        ],
        "S24": [
            "scrs_nc_source_summary.csv",
            "scrs_nc_case_summary.csv",
            "scrs_nc_cell_summary.csv",
            "scrs_nc_mechanism_summary.csv",
            "scrs_nc_pairwise_gap_summary.csv",
            "scrs_nc_paired_gap_summary.csv",
            "summary.csv",
            "qa_summary.json",
        ],
        "S25": [
            "scrs_nc_source_summary.csv",
            "scrs_nc_case_summary.csv",
            "scrs_nc_cell_summary.csv",
            "scrs_nc_mechanism_summary.csv",
            "scrs_nc_pairwise_gap_summary.csv",
            "scrs_nc_paired_gap_summary.csv",
            "summary.csv",
            "qa_summary.json",
        ],
        "S26": [
            "scrs_nc_source_summary.csv",
            "scrs_nc_case_summary.csv",
            "scrs_nc_cell_summary.csv",
            "scrs_nc_mechanism_summary.csv",
            "scrs_nc_pairwise_gap_summary.csv",
            "scrs_nc_paired_gap_summary.csv",
            "summary.csv",
            "qa_summary.json",
        ],
        "S27": [
            "scrs_nc_source_summary.csv",
            "scrs_nc_case_summary.csv",
            "scrs_nc_cell_summary.csv",
            "scrs_nc_mechanism_summary.csv",
            "scrs_nc_pairwise_gap_summary.csv",
            "scrs_nc_paired_gap_summary.csv",
            "summary.csv",
            "qa_summary.json",
        ],
        "S28": [
            "S28_cell_summary.csv",
            "S28_paired_gap_summary.csv",
            "S28_construction_manifest.csv",
            "S28_QA_report.json",
            "S28_construction_heatmap_source.csv",
            "S28_gap_forest_source.csv",
        ],
        "S29": [
            "S29_cell_summary.csv",
            "S29_paired_gap_summary.csv",
            "S29_role_model_eligibility_audit.csv",
            "S29_QA_report.json",
        ],
        "S30": [
            "S30_structure_metrics.csv",
            "S30_gap_by_structure_stratum.csv",
            "S30_moderator_regression_summary.csv",
            "S30_structure_moderator_source.csv",
            "S30_QA_report.json",
        ],
    }
    for experiment, names in files.items():
        root = RUNS.get(experiment, SUPPLEMENTAL_RUNS.get(experiment))
        if root is None:
            raise KeyError(experiment)
        for name in names:
            copy_summary(root / name, f"{experiment.lower()}_{name}", f"{experiment} {name}", manifest)


def write_key_summary(manifest: list[dict[str, str]]) -> None:
    s20 = read_csv(RUNS["S20"] / "scrs_formal_source_summary.csv")
    s25 = read_csv(RUNS["S25"] / "scrs_nc_source_summary.csv")
    s26 = read_csv(RUNS["S26"] / "scrs_nc_source_summary.csv")
    s27 = read_csv(RUNS["S27"] / "scrs_nc_source_summary.csv")
    s28 = read_csv(SUPPLEMENTAL_RUNS["S28"] / "S28_cell_summary.csv")
    s29 = read_csv(SUPPLEMENTAL_RUNS["S29"] / "S29_cell_summary.csv")
    s30 = read_csv(SUPPLEMENTAL_RUNS["S30"] / "S30_gap_by_structure_stratum.csv")
    lines = [
        "# Key Source-Data Checks",
        "",
        "Figure summaries were generated from completed S20-S30 source files. The random seed manifest was generated from S20-S29 detail tables; S30 is deterministic post-processing.",
        "",
        "Figure-specific Source Data packages are provided in `source_data/source_data_packages`: one package each for Figs. 1-5 and one package organized by S20-S30 for the supplementary overview figures. The file `source_data/source_data_package_manifest.csv` maps each package to its included CSV or JSON files.",
        "",
        "## Main Performance",
        "",
    ]
    for row in s20.itertuples(index=False):
        lines.append(
            f"- S20 {row.source}: mean SCRS={float(row.mean_scrs):.4f}, "
            f"min SCRS={float(row.min_scrs):.4f}, gap vs Wang et al. baseline={float(row.mean_gap_vs_pnas):+.4f}, "
            f"gap vs CSGC={float(row.mean_gap_vs_csgc):+.4f}, "
            f"gap vs strategy-shuffled={float(row.mean_gap_vs_strategy_shuffled):+.4f}, "
            f"gap vs score-shuffled={float(row.mean_gap_vs_score_shuffled):+.4f}."
        )
    lines.extend(["", "## Mechanism Boundary", ""])
    for row in s25.itertuples(index=False):
        lines.append(
            f"- S25 {row.source}: mean SCRS={float(row.mean_scrs):.4f}, "
            f"gap vs strategy-shuffled={float(row.mean_gap_vs_scrs_gamma1_strategy_shuffled):+.4f}, "
            f"gap vs score-shuffled={float(row.mean_gap_vs_scrs_gamma1_score_shuffled):+.4f}, "
            f"gap vs cooperator-only random={float(row.mean_gap_vs_scrs_gamma1_cooperator_only_random):+.4f}."
        )
    lines.append(
        f"- S29 clean controls: mean SCRS={numeric_series(s29['scrs']).mean():.4f}, "
        f"gap vs strategy-shuffled={numeric_series(s29['gap_vs_scrs_gamma1_strategy_shuffled']).mean():+.4f}, "
        f"gap vs uniform incident cooperator-only={numeric_series(s29['gap_vs_scrs_gamma1_cooperator_only_uniform_incident']).mean():+.4f}, "
        f"gap vs random-neighbourhood cooperator-only={numeric_series(s29['gap_vs_scrs_gamma1_cooperator_only_random_neighborhood']).mean():+.4f}, "
        f"gap vs successful edge without score ranking={numeric_series(s29['gap_vs_scrs_gamma1_success_without_score_ranking']).mean():+.4f}."
    )
    lines.extend(["", "## Extrapolation And Sensitivity", ""])
    for row in s26.itertuples(index=False):
        lines.append(
            f"- S26 {row.source}: mean SCRS={float(row.mean_scrs):.4f}, "
            f"gap vs strategy-shuffled={float(row.mean_gap_vs_scrs_gamma1_strategy_shuffled):+.4f}."
        )
    for row in s27.itertuples(index=False):
        lines.append(
            f"- S27 {row.condition} {row.source}: mean SCRS={float(row.mean_scrs):.4f}, "
            f"gap vs strategy-shuffled={float(row.mean_gap_vs_scrs_gamma1_strategy_shuffled):+.4f}, "
            f"gap vs score-shuffled={float(row.mean_gap_vs_scrs_gamma1_score_shuffled):+.4f}."
        )
    lines.extend(["", "## Construction And Structure Audits", ""])
    lines.append(
        f"- S28 construction sensitivity: mean SCRS={numeric_series(s28['scrs']).mean():.4f}, "
        f"minimum SCRS={numeric_series(s28['scrs']).min():.4f}, "
        f"gap vs Wang et al. baseline={numeric_series(s28['gap_vs_pnas']).mean():+.4f}, "
        f"gap vs CSGC={numeric_series(s28['gap_vs_csgc_gamma1']).mean():+.4f}, "
        f"gap vs strategy-shuffled={numeric_series(s28['gap_vs_scrs_gamma1_strategy_shuffled']).mean():+.4f}, "
        f"gap vs score-shuffled={numeric_series(s28['gap_vs_scrs_gamma1_score_shuffled']).mean():+.4f}."
    )
    for metric, label in [
        ("temporal_memory_adjacent_jaccard", "temporal memory"),
        ("hyperedge_overlap_within_block", "within-block overlap"),
    ]:
        subset = s30[
            (s30["structure_metric"] == metric)
            & (s30["control"] == "scrs_gamma1_strategy_shuffled")
        ]
        if subset.empty:
            continue
        by_stratum = {
            row.structure_stratum: float(row.mean_gap)
            for row in subset.itertuples(index=False)
        }
        lines.append(
            f"- S30 {label}: SCRS gap vs strategy-shuffled is "
            f"low={by_stratum.get('low', float('nan')):+.4f}, "
            f"mid={by_stratum.get('mid', float('nan')):+.4f}, "
            f"high={by_stratum.get('high', float('nan')):+.4f}."
        )
    path = OUT / "key_source_data_checks.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest.append({"file": str(path.relative_to(PACKAGE_ROOT)), "rows": "", "source": "Derived text summary"})


def write_random_seed_manifest(manifest: list[dict[str, str]]) -> None:
    rows: list[dict[str, object]] = []
    seed_runs = {**RUNS, "S28": SUPPLEMENTAL_RUNS["S28"], "S29": SUPPLEMENTAL_RUNS["S29"]}
    for tag, root in seed_runs.items():
        detail_path = root / "detail.csv"
        if not detail_path.exists():
            continue
        detail = pd.read_csv(detail_path, keep_default_na=False)
        seed_note = "exact per-trial seed"
        if "seed" not in detail.columns:
            with (root / "metadata.json").open("r", encoding="utf-8") as handle:
                metadata = json.load(handle)
            detail["seed"] = metadata.get("seed", "")
            seed_note = "base experiment seed from metadata; S20 detail table did not store per-trial seeds"
        keep = [
            column
            for column in [
                "experiment",
                "condition",
                "case",
                "source",
                "variant",
                "r",
                "rep",
                "steps",
                "tail_window",
                "selection_intensity",
                "rho0",
                "mutation_rate",
                "payoff_mode",
                "update_mode",
                "null_model",
                "topology",
                "n",
                "n_edges",
                "edge_size",
                "seed",
            ]
            if column in detail.columns
        ]
        seed_frame = detail[keep].copy()
        seed_frame.insert(0, "experiment_group", tag)
        seed_frame["seed_note"] = seed_note
        rows.extend(seed_frame.to_dict(orient="records"))
    seeds = pd.DataFrame(rows)
    write(
        seeds,
        "random_seed_manifest.csv",
        "S20-S29 detail.csv seed records; S20 uses metadata seed because per-trial seeds were not recorded; S30 is a deterministic post-processing audit",
        manifest,
    )


def experiment_design_tables(table_manifest: list[dict[str, str]]) -> None:
    purposes = {
        "S20": "Main validation of SCRS on empirical and synthetic temporal hypergraphs.",
        "S21": "Parameter and initial-condition robustness over r, selection_intensity and rho0.",
        "S22": "Temporal and topological null-model audit for empirical hypergraphs.",
        "S23": "Synthetic topology and population-size stress test.",
        "S24": "Long-horizon mutation-noise audit.",
        "S25": "Mechanism decomposition of edge context, cooperation filter and role ranking.",
        "S26": "External empirical dataset extrapolation.",
        "S27": "Payoff scaling and update-mode sensitivity.",
    }
    figure_map = {
        "S20": "Fig. 2; Supplementary Fig. S20",
        "S21": "Fig. 4a; Supplementary Fig. S21",
        "S22": "Fig. 4c; Supplementary Fig. S22",
        "S23": "Fig. 4d; Supplementary Fig. S23",
        "S24": "Fig. 4b/Fig. 5c; Supplementary Fig. S24",
        "S25": "Fig. 3; Supplementary Fig. S25",
        "S26": "Fig. 5a; Supplementary Fig. S26",
        "S27": "Fig. 5b; Supplementary Fig. S27",
    }
    source_csv = {
        "S20": "source_data/fig2a_s20_scrs_tail_by_case.csv; source_data/fig2b_s20_gap_cells_for_forest.csv; source_data/fig2b_s20_gap_forest_summary.csv",
        "S21": "source_data/fig4a_s21_robustness_cell_summary.csv; source_data/fig4a_s21_phase_r_rho0.csv",
        "S22": "source_data/fig4b_s22_real_nulls_cell_summary.csv; source_data/fig4b_s22_real_nulls_mechanism_summary.csv",
        "S23": "source_data/fig4c_s23_synthetic_stress_cell_summary.csv; source_data/fig4c_s23_synthetic_stress_case_summary.csv",
        "S24": "source_data/fig4b_s24_phase_r_mutation.csv; source_data/fig5c_s24_noise_horizon_cell_summary.csv; source_data/fig5c_s24_noise_horizon_trajectory_summary.csv",
        "S25": "source_data/fig3_s25_mechanism_mean_gaps.csv; source_data/fig3_s25_mechanism_paired_gaps_by_cell.csv",
        "S26": "source_data/fig5a_s26_external_empirical_cases.csv; source_data/fig5a_s26_external_dataset_manifest.csv; source_data/fig5a_s26_external_paired_gaps_by_cell.csv",
        "S27": "source_data/fig5b_s27_payoff_update_source_summary.csv; source_data/fig5b_s27_payoff_update_paired_gaps_by_cell.csv",
    }
    rows: list[dict[str, object]] = []
    for tag, root in RUNS.items():
        summary = read_csv(root / "summary.csv")
        cell_name = "scrs_formal_cell_summary.csv" if tag == "S20" else "scrs_nc_cell_summary.csv"
        cells = read_csv(root / cell_name)
        varied = []
        for column in [
            "r",
            "selection_intensity",
            "rho0",
            "mutation_rate",
            "null_model",
            "topology",
            "payoff_mode",
            "update_mode",
            "n",
            "n_edges",
            "edge_size",
        ]:
            if column in summary.columns and summary[column].nunique(dropna=True) > 1:
                varied.append(f"{column}={format_unique(summary[column])}")
        rows.append(
            {
                "experiment": tag,
                "purpose": purposes[tag],
                "main_or_supplementary_display": figure_map[tag],
                "source_types": format_unique(summary["source"]) if "source" in summary.columns else "",
                "datasets_or_cases": int(summary["case"].nunique()) if "case" in summary.columns else "",
                "scrs_cells": int(cells.shape[0]),
                "variants": int(summary["variant"].nunique()) if "variant" in summary.columns else "",
                "varied_parameters": "; ".join(varied) if varied else "none beyond fixed main settings",
                "reps": format_unique(summary["reps"]) if "reps" in summary.columns else "",
                "steps": format_unique(summary["steps"]) if "steps" in summary.columns else "5000",
                "tail_window": format_unique(summary["tail_window"]) if "tail_window" in summary.columns else "1000",
                "formal_trials": int(numeric_series(summary["reps"]).sum()) if "reps" in summary.columns else "",
                "primary_source_csv": source_csv[tag],
            }
        )
    s28_summary = read_csv(SUPPLEMENTAL_RUNS["S28"] / "summary.csv")
    s28_cells = read_csv(SUPPLEMENTAL_RUNS["S28"] / "S28_cell_summary.csv")
    s29_summary = read_csv(SUPPLEMENTAL_RUNS["S29"] / "summary.csv")
    s29_cells = read_csv(SUPPLEMENTAL_RUNS["S29"] / "S29_cell_summary.csv")
    s30_metrics = read_csv(SUPPLEMENTAL_RUNS["S30"] / "S30_structure_metrics.csv")
    rows.extend(
        [
            {
                "experiment": "S28",
                "purpose": "Hypergraph construction sensitivity across edge size edge count block duration and construction mode.",
                "main_or_supplementary_display": "Supplementary Fig. S28",
                "source_types": format_unique(s28_summary["source"]),
                "datasets_or_cases": int(s28_summary["case"].nunique()),
                "scrs_cells": int(s28_cells.shape[0]),
                "variants": int(s28_summary["variant"].nunique()),
                "varied_parameters": "r=0.7, 0.9, 1; h=4, 6, 8; m=20, 33; subgraph_duration=50, 100, 200; construction_mode=baseline_hybrid, clique_only, contact_centered_fallback, fixed_h6_alternative, native_variable_size_where_available",
                "reps": format_unique(s28_summary["reps"]),
                "steps": format_unique(s28_summary["steps"]),
                "tail_window": format_unique(s28_summary["tail_window"]),
                "formal_trials": int(numeric_series(s28_summary["reps"]).sum()),
                "primary_source_csv": "source_data/supplementary/S28_cell_summary.csv; source_data/supplementary/S28_paired_gap_summary.csv; source_data/supplementary/S28_construction_manifest.csv; source_data/supplementary/S28_construction_heatmap_source.csv; source_data/supplementary/S28_gap_forest_source.csv",
            },
            {
                "experiment": "S29",
                "purpose": "Clean mechanism-context controls against generic local cooperator search.",
                "main_or_supplementary_display": "Supplementary Fig. S29",
                "source_types": format_unique(s29_summary["source"]),
                "datasets_or_cases": int(s29_summary["case"].nunique()),
                "scrs_cells": int(s29_cells.shape[0]),
                "variants": int(s29_summary["variant"].nunique()),
                "varied_parameters": "r=0.7, 0.9, 1; cooperator-only from uniformly sampled incident edge; cooperator-only from random local neighborhood; successful edge without score ranking; retained score-shuffled strategy-shuffled and cooperator-only-random controls",
                "reps": format_unique(s29_summary["reps"]),
                "steps": format_unique(s29_summary["steps"]),
                "tail_window": format_unique(s29_summary["tail_window"]),
                "formal_trials": int(numeric_series(s29_summary["reps"]).sum()),
                "primary_source_csv": "source_data/supplementary/S29_cell_summary.csv; source_data/supplementary/S29_paired_gap_summary.csv; source_data/supplementary/S29_role_model_eligibility_audit.csv",
            },
            {
                "experiment": "S30",
                "purpose": "Structure-stratified moderator audit linking temporal-hypergraph organization to SCRS paired gaps.",
                "main_or_supplementary_display": "Supplementary Fig. S30",
                "source_types": format_unique(s30_metrics["source"]),
                "datasets_or_cases": int(s30_metrics.shape[0]),
                "scrs_cells": int(s30_metrics.shape[0]),
                "variants": "cell-level moderators",
                "varied_parameters": "temporal_memory_adjacent_jaccard; hyperedge_overlap_within_block; hyperedge_overlap_adjacent_block; activity_cv; activity_gini; mixed_role_exposure_potential_rho0; completed S20 S22 S23 S26 S28 S29 source tables",
                "reps": "cell-level",
                "steps": "post-processing",
                "tail_window": "not applicable",
                "formal_trials": 0,
                "primary_source_csv": "source_data/supplementary/S30_structure_metrics.csv; source_data/supplementary/S30_gap_by_structure_stratum.csv; source_data/supplementary/S30_moderator_regression_summary.csv; source_data/supplementary/S30_structure_moderator_source.csv",
            },
        ]
    )
    write_table(pd.DataFrame(rows), "table_s1_experiment_design", "Table S1. Formal Experiment Design", table_manifest)


def dataset_statistics_table(table_manifest: list[dict[str, str]]) -> None:
    rows: list[dict[str, object]] = []
    with (RUNS["S20"] / "metadata.json").open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    for case in metadata["cases"]:
        real_sequence_path = case.get("real_sequence_path", "")
        blocks, constructed = sequence_stats(real_sequence_path)
        input_events, retained_events = prepared_real_contact_counts(real_sequence_path)
        construction_method = (
            "Pairwise contact rows aggregated into temporal snapshots; h=6 clique candidates and contact-centered fallback groups were sampled into fixed-size temporal hyperedges."
            if case["source"] == "real"
            else "Temporal hyperedges generated from the named synthetic model during simulation."
        )
        rows.append(
            {
                "scope": "S20-S25/S27 core",
                "dataset_key": case["name"],
                "dataset_label": clean_dataset_label(case["name"]),
                "source_type": case["source"],
                "family_or_model": case.get("temporal_model", ""),
                "n": case.get("n", ""),
                "h": case.get("edge_size", ""),
                "m": case.get("n_edges", ""),
                "blocks": blocks,
                "input_events": input_events,
                "retained_events": retained_events,
                "constructed_hyperedges": constructed,
                "construction_method": construction_method,
                "source_url": "http://www.sociopatterns.org/datasets/" if case["source"] == "real" else "",
            }
        )
    stress = read_csv(RUNS["S23"] / "scrs_nc_cell_summary.csv")
    stress_cases = (
        stress[["case", "source", "topology", "n", "n_edges", "edge_size"]]
        .drop_duplicates()
        .sort_values(["topology", "n", "case"])
    )
    for row in stress_cases.itertuples(index=False):
        rows.append(
            {
                "scope": "S23 synthetic stress",
                "dataset_key": row.case,
                "dataset_label": clean_dataset_label(row.case),
                "source_type": row.source,
                "family_or_model": row.topology,
                "n": int(row.n),
                "h": int(row.edge_size),
                "m": int(row.n_edges),
                "blocks": "",
                "input_events": "",
                "retained_events": "",
                "constructed_hyperedges": "generated during simulation",
                "construction_method": "Synthetic temporal-hypergraph generator with topology and m=0.2n size scaling.",
                "source_url": "",
            }
        )
    with EXTERNAL_MANIFEST.open("r", encoding="utf-8") as handle:
        external_manifest = json.load(handle)
    for case in external_manifest["prepared_datasets"]:
        blocks, constructed = sequence_stats(case.get("sequence_path", ""))
        rows.append(
            {
                "scope": "S26 external empirical",
                "dataset_key": case["dataset_name"],
                "dataset_label": clean_dataset_label(case["dataset_name"]),
                "source_type": "external empirical",
                "family_or_model": case["family"],
                "n": case["n"],
                "h": case["edge_size"],
                "m": case["n_edges"],
                "blocks": blocks or case["blocks"],
                "input_events": case["input_events"],
                "retained_events": case["retained_events"],
                "constructed_hyperedges": constructed,
                "construction_method": case["construction"],
                "source_url": case["source_url"],
            }
        )
    table = pd.DataFrame(rows).drop_duplicates(subset=["scope", "dataset_key", "n", "m"])
    write_table(table, "table_s2_dataset_statistics", "Table S2. Dataset And Hypergraph Statistics", table_manifest)


def ablation_definition_table(table_manifest: list[dict[str, str]]) -> None:
    rows = [
        {
            "variant": "SCRS",
            "edge_context": "Cooperative-success score over the focal node's incident hyperedges.",
            "role_rule": "Select an eligible cooperator from the sampled successful edge, excluding the focal node, using payoff ranking with random tie-breaking; fall back to a random non-focal edge member when no eligible cooperator exists.",
            "tests": "Proposed cooperative role-screening rule under temporal-hypergraph exposure.",
            "reported_in": "Figs. 2-5; Supplementary Figs. S20-S27",
        },
        {
            "variant": "Wang et al. temporal-hypergraph imitation",
            "edge_context": "Temporal-hypergraph interaction sequence without the SCRS cooperative role screen.",
            "role_rule": "Payoff-based imitation following the temporal-hypergraph baseline based on Wang et al.",
            "tests": "Standard temporal-hypergraph payoff imitation baseline.",
            "reported_in": "Figs. 2, 4, 5; Supplementary Figs. S20-S27",
        },
        {
            "variant": "CSGC edge-context selection",
            "edge_context": "Cooperative-success group-context selection retained.",
            "role_rule": "No SCRS requirement that the imitated role be a cooperator from the successful group.",
            "tests": "Whether edge context alone explains the SCRS gain.",
            "reported_in": "Figs. 2, 4, 5; Supplementary Figs. S20-S27",
        },
        {
            "variant": "Strongest LFDS matched control",
            "edge_context": "Matched local diffusion-style controls available in S20-S27.",
            "role_rule": "The strongest LFDS variant in each matched cell.",
            "tests": "Whether SCRS exceeds the best matched local diffusion control.",
            "reported_in": "Fig. 2; Supplementary Figs. S20-S27",
        },
        {
            "variant": "Strategy-shuffled SCRS",
            "edge_context": "SCRS edge context retained.",
            "role_rule": "Strategy labels are permuted before role screening.",
            "tests": "Whether the cooperation-conditioned role signal is required.",
            "reported_in": "Figs. 2-5; Supplementary Figs. S20-S27",
        },
        {
            "variant": "Score-shuffled SCRS",
            "edge_context": "Edge scores are permuted before edge sampling.",
            "role_rule": "Downstream SCRS cooperative role screen retained.",
            "tests": "Whether score ordering is independently decisive.",
            "reported_in": "Figs. 2-5; Supplementary Figs. S20-S27",
        },
        {
            "variant": "Cooperator-only random role",
            "edge_context": "SCRS exposure layer retained.",
            "role_rule": "Select randomly among eligible cooperators instead of ranking them by payoff.",
            "tests": "Whether payoff ranking among eligible cooperators is necessary.",
            "reported_in": "Fig. 3; Supplementary Fig. S25",
        },
        {
            "variant": "Payoff-only role",
            "edge_context": "SCRS exposure layer retained.",
            "role_rule": "Select by payoff without requiring the role model to be a cooperator.",
            "tests": "Whether payoff ranking can replace the cooperator filter.",
            "reported_in": "Fig. 3; Supplementary Fig. S25",
        },
        {
            "variant": "Success-only, no cooperator filter",
            "edge_context": "Successful edge condition retained.",
            "role_rule": "Choose from the successful edge without cooperation conditioning.",
            "tests": "Whether successful-edge exposure alone can replace cooperative role screening.",
            "reported_in": "Fig. 3; Supplementary Fig. S25",
        },
        {
            "variant": "Random role on selected edge",
            "edge_context": "SCRS selected edge retained.",
            "role_rule": "Sample a random role from the selected edge.",
            "tests": "Whether selecting the same edge explains the SCRS gain.",
            "reported_in": "Fig. 3; Supplementary Fig. S25",
        },
    ]
    write_table(pd.DataFrame(rows), "table_s3_ablation_definitions", "Table S3. Baseline And Ablation Definitions", table_manifest)


def supplemental_experiment_plan_rows() -> list[dict[str, str]]:
    return [
        {
            "experiment": "S28 hypergraph construction sensitivity",
            "priority": "completed supplemental audit",
            "status": "complete; QA passed",
            "purpose": "Audit whether SCRS advantage depends on a single fixed-size temporal-hypergraph construction.",
            "datasets_or_inputs": "Core four SocioPatterns-style datasets plus Copenhagen Bluetooth and Email-Enron.",
            "scale_or_basis": "steps=5000; tail_window=1000; reps=50; r={0.70,0.90,1.00}; rho0=0.5; selection_intensity=2.0; 45000 matched trials",
            "factors_or_moderators": "h={4,6,8}; m={20,33}; subgraph_duration={50,100,200}; baseline_hybrid; clique_only; contact_centered_fallback; fixed_h6_alternative; native_variable_size_where_available",
            "primary_comparisons_or_outputs": "SCRS versus Wang imitation, CSGC, strategy-shuffled SCRS and score-shuffled SCRS.",
            "source_files": "S28_cell_summary.csv; S28_paired_gap_summary.csv; S28_construction_manifest.csv; S28_QA_report.json; S28_construction_heatmap_source.csv; S28_gap_forest_source.csv",
            "claim_use": "Supports construction robustness; fixed-size construction affects absolute values in some cells but does not create the role-screening advantage.",
        },
        {
            "experiment": "S29 clean mechanism-context controls",
            "priority": "completed supplemental audit",
            "status": "complete; QA passed",
            "purpose": "Test whether SCRS is stronger than generic local cooperator search.",
            "datasets_or_inputs": "Core empirical cells plus synthetic structured-ring and community cases.",
            "scale_or_basis": "steps=5000; tail_window=1000; reps=50; r={0.70,0.90,1.00}; rho0=0.5; selection_intensity=2.0; 6300 matched trials",
            "factors_or_moderators": "cooperator-only from uniformly sampled incident edge; cooperator-only from random local neighborhood; successful edge without score ranking; retained cooperator-only-random, score-shuffled and strategy-shuffled controls",
            "primary_comparisons_or_outputs": "SCRS versus clean mechanism-context controls in matched case-r-rep cells.",
            "source_files": "S29_cell_summary.csv; S29_paired_gap_summary.csv; S29_role_model_eligibility_audit.csv; S29_QA_report.json",
            "claim_use": "Narrows the claim to local cooperative role screening under temporal-hypergraph exposure; successful-group context is an effective exposure layer, not an independently necessary driver in all tested regimes.",
        },
        {
            "experiment": "S30 structure-stratified mechanism audit",
            "priority": "completed supplemental audit",
            "status": "complete; QA passed",
            "purpose": "Test whether SCRS paired gaps vary with temporal-hypergraph organization.",
            "datasets_or_inputs": "Completed S20, S22, S23, S26, S28 and S29 source tables.",
            "scale_or_basis": "324 cell rows; 1710 paired-gap rows; 294 structure-stratum rows; 120 moderator-summary rows",
            "factors_or_moderators": "temporal memory; within-block and adjacent-block hyperedge overlap; activity CV and Gini; active-node fraction; mixed-role exposure potential",
            "primary_comparisons_or_outputs": "SCRS paired gap, scrs_role_coop_rate and scrs_csgc_selection_lift by structural stratum and continuous moderator.",
            "source_files": "S30_structure_metrics.csv; S30_gap_by_structure_stratum.csv; S30_moderator_regression_summary.csv; S30_structure_moderator_source.csv; S30_QA_report.json",
            "claim_use": "Supports a bounded structural-mechanism claim: temporal memory and hyperedge overlap sharpen role-screening gaps, while activity heterogeneity and mixed-role potential are less decisive in the completed cells.",
        },
    ]


def write_supplementary_experiment_specs(rows: list[dict[str, str]], manifest: list[dict[str, str]]) -> None:
    specs_dir = PACKAGE_ROOT / "experiment_specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    csv_path = specs_dir / "completed_supplemental_audits_s28_s30.csv"
    json_path = specs_dir / "completed_supplemental_audits_s28_s30.json"
    df.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    manifest.append(
        {
            "file": str(csv_path.relative_to(PACKAGE_ROOT)),
            "rows": str(len(df)),
            "source": "curated supplementary experiment specification",
        }
    )
    manifest.append(
        {
            "file": str(json_path.relative_to(PACKAGE_ROOT)),
            "rows": str(len(rows)),
            "source": "curated supplementary experiment specification",
        }
    )


def proposed_followup_experiments(table_manifest: list[dict[str, str]]) -> None:
    rows = supplemental_experiment_plan_rows()
    write_table(pd.DataFrame(rows), "table_s4_proposed_followup_experiments", "Table S4. Completed supplementary robustness and mechanism audits", table_manifest)


def write_table_manifest(rows: list[dict[str, str]]) -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(TABLES / "table_manifest.csv", index=False)


def write_environment_and_release_files() -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    requirements = [
        f"numpy=={package_version('numpy')}",
        f"pandas=={package_version('pandas')}",
        f"matplotlib=={package_version('matplotlib')}",
    ]
    (PACKAGE_ROOT / "requirements.txt").write_text("\n".join(requirements) + "\n", encoding="utf-8")
    environment = [
        "name: scrs-nc",
        "channels:",
        "  - conda-forge",
        "dependencies:",
        f"  - python={python_version}",
        "  - pip",
        "  - pip:",
    ]
    environment.extend([f"      - {requirement}" for requirement in requirements])
    (PACKAGE_ROOT / "environment.yml").write_text("\n".join(environment) + "\n", encoding="utf-8")
    release_rows = [
        {
            "path": "manuscript.md",
            "kind": "manuscript draft",
            "include_in_repository": "yes",
            "description": "Current Nature Communications-style manuscript draft.",
        },
        {
            "path": "figure_legends.md",
            "kind": "manuscript support",
            "include_in_repository": "yes",
            "description": "Standalone figure legends for main and supplementary figures.",
        },
        {
            "path": "figures/",
            "kind": "figure outputs",
            "include_in_repository": "yes",
            "description": "SVG, PDF and high-resolution PNG exports for Figs. 1-5 and Supplementary Figs. S20-S30.",
        },
        {
            "path": "source_data/",
            "kind": "source data",
            "include_in_repository": "yes",
            "description": "All source CSVs needed for main and supplementary figures, including the source-data manifest, random seed manifest and figure-specific Source Data packages.",
        },
        {
            "path": "tables/",
            "kind": "supplementary tables",
            "include_in_repository": "yes",
            "description": "Experiment design, dataset statistics, ablation definitions and completed supplementary robustness and mechanism audits.",
        },
        {
            "path": "experiment_specs/",
            "kind": "supplementary experiment specifications",
            "include_in_repository": "yes",
            "description": "Machine-readable S28-S30 completed supplemental robustness audit records.",
        },
        {
            "path": "scripts/",
            "kind": "analysis scripts",
            "include_in_repository": "yes",
            "description": "Scripts for regenerating source data, figures and verified references from completed formal outputs, including S28-S30 supplemental figure plotting.",
        },
        {
            "path": "formal_experiment_drivers/",
            "kind": "formal experiment drivers",
            "include_in_repository": "yes",
            "description": "S20-S29 formal experiment runners plus S30 post-processing script and shared simulation library included in the LaTeX export package.",
        },
        {
            "path": "references_verified.bib; reference_verification.csv; reference_verification.md",
            "kind": "references",
            "include_in_repository": "yes",
            "description": "Verified BibTeX and reference QA records.",
        },
        {
            "path": "requirements.txt; environment.yml",
            "kind": "environment",
            "include_in_repository": "yes",
            "description": "Python environment used to regenerate the manuscript package.",
        },
    ]
    release = pd.DataFrame(release_rows)
    release.to_csv(RELEASE / "deposition_manifest.csv", index=False)
    checklist = [
        "# Data And Code Deposition Checklist",
        "",
        "Deposit this manuscript package and the completed simulation code archive in a public repository such as Zenodo, OSF or Figshare. The manuscript availability statements still need live DOI, repository URL and release tag/commit identifiers before journal submission.",
        "",
        "- Source data: include `source_data/`, `source_data/source_data_packages/`, `tables/`, `experiment_specs/`, `figures/figure_manifest.csv`, `qc_report.md` and the reference verification files.",
        "- Code: publish the simulation and manuscript-generation scripts in a GitHub repository, tag the exact release used for submission and archive that tag in Zenodo.",
        "- Seeds: include `source_data/random_seed_manifest.csv`; S20 records a base metadata seed because per-trial seeds were not stored in that original detail table, S28 and S29 include exact per-trial seeds, and S30 is deterministic post-processing.",
        "- Environment: include `requirements.txt` and `environment.yml`, generated from the active `.venv_scrs_nc` environment.",
        "- Availability placeholders: replace `[data repository name and data DOI to be inserted]`, `[code DOI to be inserted]`, `[GitHub URL to be inserted]` and `[release tag/commit to be inserted]` in `manuscript.md` once the deposits are live.",
        "- Cell-level inference: include `source_data/cell_level_inference_summary.csv`, which reports paired bootstrap intervals and sign-permutation summaries across matched cells.",
        "- S28 construction-sensitivity audit: completed and included in Table S1, Table S4, Supplementary Fig. S28 and `source_data/supplementary`.",
        "- S29 mechanism-context controls: completed and included in Table S1, Table S4, Supplementary Fig. S29 and `source_data/supplementary`.",
        "- S30 structural-moderator audit: completed and included in Table S1, Table S4, Supplementary Fig. S30 and `source_data/supplementary`.",
        "- Public raw data: cite the original SocioPatterns, Copenhagen and Cornell higher-order dataset records rather than redistributing restricted raw data when licenses require source access.",
        "",
        "This checklist prepares the package for the Nature Communications data and code availability expectation that data and analysis materials be sufficient to verify and extend the conclusions.",
    ]
    (RELEASE / "deposition_checklist.md").write_text("\n".join(checklist) + "\n", encoding="utf-8")


def main() -> None:
    manifest: list[dict[str, str]] = []
    table_manifest: list[dict[str, str]] = []
    fig1_source(manifest)
    fig2_source(manifest)
    fig3_source(manifest)
    fig4_source(manifest)
    fig5_source(manifest)
    cell_level_inference_source(manifest)
    supplementary_sources(manifest)
    write_random_seed_manifest(manifest)
    write_key_summary(manifest)
    write_supplementary_experiment_specs(supplemental_experiment_plan_rows(), manifest)
    subprocess.run([sys.executable, str(PACKAGE_ROOT / "scripts" / "package_source_data.py")], check=True)
    manifest.append(
        {
            "file": "source_data/source_data_package_manifest.csv",
            "rows": 6,
            "source": "Figure-specific Source Data package manifest for Figs. 1-5 and Supplementary Figs. S20-S30",
        }
    )
    pd.DataFrame(manifest).to_csv(OUT / "source_data_manifest.csv", index=False)
    experiment_design_tables(table_manifest)
    dataset_statistics_table(table_manifest)
    ablation_definition_table(table_manifest)
    proposed_followup_experiments(table_manifest)
    write_table_manifest(table_manifest)
    write_environment_and_release_files()
    print(f"Wrote {len(manifest)} source-data files to {OUT}")
    print(f"Wrote {len(table_manifest)} tables to {TABLES}")


if __name__ == "__main__":
    main()
