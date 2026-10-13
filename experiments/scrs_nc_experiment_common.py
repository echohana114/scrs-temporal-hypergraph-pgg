#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import multiprocessing as mp
import os
import shutil
import sys
import time
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT = Path("/Users/hui/Documents/New project 2/temporal_hypergraph_pgg_pilot")
RUNS_ROOT = PROJECT / "supplemental_lfds_runs"
BACKEND_SCRIPT = RUNS_ROOT / "s18_scrs_strict_smoke_20260731_1015" / "run_scrs_strict_smoke.py"
DEFAULT_STEPS = 5000
DEFAULT_REPS = 50
DEFAULT_TAIL_WINDOW = 1000
DEFAULT_SUBGRAPH_DURATION = 100
DEFAULT_SELECTION_INTENSITY = 2.0
DEFAULT_RHO0 = 0.5
DEFAULT_EWMA_WINDOW = 100.0

DETAIL_COLUMNS = [
    "experiment",
    "condition",
    "case",
    "source",
    "variant",
    "r",
    "rep",
    "steps",
    "tail_window",
    "subgraph_duration",
    "selection_intensity",
    "rho0",
    "null_model",
    "topology",
    "n",
    "n_edges",
    "edge_size",
    "mutation_rate",
    "payoff_mode",
    "update_mode",
    "seed",
    "tail_coop",
    "final_coop",
    "tail_coop_mean_500",
    "tail_coop_mean_1000",
    "tail_coop_mean_2000",
    "csgc_selection_lift",
    "scrs_role_coop_rate",
    "conformist_update_rate",
    "fermi_update_rate",
    "mutation_update_rate",
]

CELL_CONTEXT_COLUMNS = [
    "experiment",
    "condition",
    "case",
    "source",
    "r",
    "steps",
    "tail_window",
    "subgraph_duration",
    "selection_intensity",
    "rho0",
    "null_model",
    "topology",
    "n",
    "n_edges",
    "edge_size",
    "mutation_rate",
    "payoff_mode",
    "update_mode",
]

KEY_COLUMNS = [
    "experiment",
    "condition",
    "case",
    "variant",
    "r",
    "rep",
    "steps",
    "selection_intensity",
    "rho0",
    "null_model",
    "topology",
    "n",
    "n_edges",
    "edge_size",
    "mutation_rate",
    "payoff_mode",
    "update_mode",
]

METRIC_COLUMNS = [
    "tail_coop",
    "final_coop",
    "tail_coop_mean_500",
    "tail_coop_mean_1000",
    "tail_coop_mean_2000",
    "csgc_selection_lift",
    "scrs_role_coop_rate",
    "conformist_update_rate",
    "fermi_update_rate",
    "mutation_update_rate",
]

KEY_CONTROLS = [
    "pnas",
    "csgc_gamma1",
    "scrs_gamma1_score_shuffled",
    "scrs_gamma1_strategy_shuffled",
    "scrs_gamma1_cooperator_only_random",
    "scrs_gamma1_cooperator_only_uniform_incident",
    "scrs_gamma1_cooperator_only_random_neighborhood",
    "scrs_gamma1_success_without_score_ranking",
    "scrs_gamma1_payoff_only_role",
    "scrs_gamma1_success_only_no_coop_filter",
    "scrs_gamma1_random_role_same_edge",
    "lfds_l050",
    "lfds_l075",
    "lfds_l075_budget",
]

BACKEND: Any = None


def load_backend(path: Path = BACKEND_SCRIPT) -> Any:
    if not path.exists():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location("scrs_strict_backend", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load backend script: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.PROJECT = PROJECT
    return module


def init_worker() -> None:
    global BACKEND
    BACKEND = load_backend()


def ensure_backend() -> Any:
    global BACKEND
    if BACKEND is None:
        BACKEND = load_backend()
    return BACKEND


def backend_cases(source: str | None = None) -> list[Any]:
    backend = ensure_backend()
    cases = list(backend.CASES)
    if source is not None:
        cases = [case for case in cases if case.source == source]
    return cases


def case_by_name(name: str) -> Any:
    backend = ensure_backend()
    lookup = {case.name: case for case in backend.CASES}
    if name not in lookup:
        raise KeyError(name)
    return lookup[name]


def make_synthetic_case(task: dict[str, Any]) -> Any:
    backend = ensure_backend()
    return backend.Case(
        str(task["case"]),
        "synthetic",
        str(task.get("topology") or "uniform_random"),
        int(task["n"]),
        int(task["edge_size"]),
        int(task["n_edges"]),
    )


def resolve_case(task: dict[str, Any]) -> Any:
    if str(task.get("source")) == "synthetic" and str(task.get("case", "")).startswith("synthetic_stress_"):
        return make_synthetic_case(task)
    if str(task.get("source")) == "real" and task.get("real_sequence_path"):
        backend = ensure_backend()
        return backend.Case(
            str(task["case"]),
            "real",
            "real_sequence",
            int(task["n"]),
            int(task["edge_size"]),
            int(task["n_edges"]),
            str(task["real_sequence_path"]),
        )
    return case_by_name(str(task["case"]))


def stable_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.8g}"
    if isinstance(value, (np.floating,)):
        return f"{float(value):.8g}"
    return str(value)


def stable_key(row: dict[str, Any] | pd.Series, key_columns: Iterable[str] = KEY_COLUMNS) -> tuple[str, ...]:
    return tuple(stable_value(row.get(col, "")) for col in key_columns)


def deterministic_seed(task: dict[str, Any], base_seed: int) -> int:
    payload = "|".join(stable_key(task))
    digest = hashlib.blake2b(payload.encode("utf-8"), digest_size=8).hexdigest()
    return int((int(digest, 16) + int(base_seed)) % (2**32 - 1))


def normalize_task(task: dict[str, Any], base_seed: int) -> dict[str, Any]:
    normalized = {col: "" for col in DETAIL_COLUMNS if col not in METRIC_COLUMNS}
    normalized.update(task)
    normalized.setdefault("tail_window", DEFAULT_TAIL_WINDOW)
    normalized.setdefault("subgraph_duration", DEFAULT_SUBGRAPH_DURATION)
    normalized.setdefault("selection_intensity", DEFAULT_SELECTION_INTENSITY)
    normalized.setdefault("rho0", DEFAULT_RHO0)
    normalized.setdefault("null_model", "")
    normalized.setdefault("topology", "")
    normalized.setdefault("mutation_rate", 0.0)
    normalized.setdefault("payoff_mode", "")
    normalized.setdefault("update_mode", "")
    normalized["seed"] = deterministic_seed(normalized, base_seed)
    return normalized


def load_detail(detail_path: Path) -> pd.DataFrame:
    if not detail_path.exists() or detail_path.stat().st_size == 0:
        return pd.DataFrame(columns=DETAIL_COLUMNS)
    df = pd.read_csv(detail_path, keep_default_na=False)
    for col in DETAIL_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    for col in ["r", "selection_intensity", "rho0", "mutation_rate", *METRIC_COLUMNS]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    for col in ["rep", "steps", "tail_window", "subgraph_duration", "n", "n_edges", "edge_size", "seed"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df[DETAIL_COLUMNS]


def completed_keys(detail_path: Path) -> set[tuple[str, ...]]:
    details = load_detail(detail_path)
    if details.empty:
        return set()
    return {stable_key(row._asdict()) for row in details[KEY_COLUMNS].itertuples(index=False)}


def validate_planned_tasks(tasks: list[dict[str, Any]]) -> None:
    seen: set[tuple[str, ...]] = set()
    duplicates = 0
    for task in tasks:
        key = stable_key(task)
        if key in seen:
            duplicates += 1
        seen.add(key)
    if duplicates:
        raise ValueError(f"Planned task grid contains {duplicates} duplicate trial keys")


def build_pending_tasks(all_tasks: list[dict[str, Any]], detail_path: Path) -> list[dict[str, Any]]:
    done = completed_keys(detail_path)
    return [task for task in all_tasks if stable_key(task) not in done]


def fermi_beta(payoff_i: float, payoff_j: float, beta: float) -> float:
    x = -float(beta) * (payoff_j - payoff_i)
    if x > 60:
        return 0.0
    if x < -60:
        return 1.0
    return 1.0 / (1.0 + math.exp(x))


def choose_csgc_edge_fast(
    rng: np.random.Generator,
    incident: list[int],
    edge_scores: np.ndarray,
    shuffled_scores: np.ndarray | None,
    shuffled: bool,
) -> int | None:
    if not incident:
        return None
    scores_source = shuffled_scores if shuffled and shuffled_scores is not None else edge_scores
    count = len(incident)
    if count <= 1:
        return int(incident[0])
    values = [float(scores_source[int(slot)]) for slot in incident]
    mean = sum(values) / count
    variance = sum((value - mean) * (value - mean) for value in values) / count
    std = math.sqrt(max(0.0, variance))
    if std <= 1e-12:
        return int(incident[int(rng.integers(count))])
    weights = [1.0 + max(0.0, (value - mean) / std) for value in values]
    total = sum(weights)
    if total <= 1e-12:
        return int(incident[int(rng.integers(count))])
    threshold = float(rng.random()) * total
    running = 0.0
    for slot, weight in zip(incident, weights):
        running += weight
        if threshold <= running:
            return int(slot)
    return int(incident[-1])


def choose_scrs_role_fast(
    rng: np.random.Generator,
    candidates: list[int],
    strategies: np.ndarray,
    payoff: np.ndarray,
    selected_score: float,
    shuffled_strategy_labels: np.ndarray | None,
    role_mode: str = "successful_cooperator_payoff",
) -> int:
    if role_mode == "random_role_same_edge":
        return int(candidates[int(rng.integers(len(candidates)))])

    def eligible_cooperators() -> list[int]:
        eligible: list[int] = []
        for node in candidates:
            label = int(shuffled_strategy_labels[node]) if shuffled_strategy_labels is not None else int(strategies[node])
            if label == 1:
                eligible.append(int(node))
        return eligible

    def best_payoff_role(nodes: list[int]) -> int:
        best_payoff = -math.inf
        best_nodes: list[int] = []
        for node in nodes:
            node_payoff = float(payoff[node])
            if node_payoff > best_payoff + 1e-12:
                best_payoff = node_payoff
                best_nodes = [int(node)]
            elif abs(node_payoff - best_payoff) <= 1e-12:
                best_nodes.append(int(node))
        return best_nodes[int(rng.integers(len(best_nodes)))]

    if role_mode == "payoff_only_role":
        return best_payoff_role(candidates)

    if role_mode == "cooperator_only_random_any_context":
        eligible = eligible_cooperators()
        if eligible:
            return eligible[int(rng.integers(len(eligible)))]
        return int(candidates[int(rng.integers(len(candidates)))])

    if role_mode == "success_only_no_coop_filter":
        if selected_score > 1e-12:
            return best_payoff_role(candidates)
        return int(candidates[int(rng.integers(len(candidates)))])

    if selected_score > 1e-12:
        eligible = eligible_cooperators()
        if eligible:
            if role_mode == "cooperator_only_random":
                return eligible[int(rng.integers(len(eligible)))]
            return best_payoff_role(eligible)

    return int(candidates[int(rng.integers(len(candidates)))])


def role_selection_mode(variant: str) -> str:
    if variant.endswith("_cooperator_only_uniform_incident"):
        return "cooperator_only_random_any_context"
    if variant.endswith("_cooperator_only_random_neighborhood"):
        return "cooperator_only_random_any_context"
    if variant.endswith("_cooperator_only_random"):
        return "cooperator_only_random"
    if variant.endswith("_payoff_only_role"):
        return "payoff_only_role"
    if variant.endswith("_success_only_no_coop_filter"):
        return "success_only_no_coop_filter"
    if variant.endswith("_random_role_same_edge"):
        return "random_role_same_edge"
    return "successful_cooperator_payoff"


def public_goods_payoff_for_mode(
    backend: Any,
    strategies: np.ndarray,
    edges: np.ndarray,
    r: float,
    n: int,
    payoff_mode: str,
) -> np.ndarray:
    mode = payoff_mode or "accumulated"
    if mode == "accumulated":
        return backend.public_goods_payoff(strategies, edges, r, n)
    payoff = np.zeros(n, dtype=float)
    edge_strategies = strategies[edges]
    n_coop = edge_strategies.sum(axis=1)
    if mode == "degree_normalized":
        payoff = backend.public_goods_payoff(strategies, edges, r, n)
        participation = backend.participation_counts(edges, n)
        mask = participation > 0
        payoff[mask] = payoff[mask] / participation[mask]
        return payoff
    if mode == "per_capita":
        benefit = r * n_coop / edges.shape[1]
        np.add.at(payoff, edges.ravel(), np.repeat(benefit, edges.shape[1]))
        np.add.at(payoff, edges.ravel(), -edge_strategies.ravel())
        return payoff
    raise ValueError(f"Unknown payoff_mode: {payoff_mode}")


def sample_weighted_edges(
    rng: np.random.Generator,
    n: int,
    m: int,
    h: int,
    weights: np.ndarray,
) -> np.ndarray:
    probs = weights.astype(float)
    probs = probs / probs.sum()
    edges = np.empty((m, h), dtype=np.int32)
    for slot in range(m):
        edges[slot] = rng.choice(n, size=h, replace=False, p=probs)
    return edges


def temporal_modular_switching_edges(case: Any, rng: np.random.Generator, block: int) -> np.ndarray:
    community_count = 4
    parts = np.array_split(np.arange(case.n, dtype=np.int32), community_count)
    active_a = block % community_count
    active_b = (block // 2 + 1) % community_count
    edges = np.empty((case.n_edges, case.edge_size), dtype=np.int32)
    for slot in range(case.n_edges):
        if slot % 5 == 0:
            first = parts[active_a]
            second = parts[active_b]
            first_take = max(1, case.edge_size // 2)
            selected = [int(x) for x in rng.choice(first, size=min(first_take, len(first)), replace=False)]
            while len(selected) < case.edge_size:
                candidate = int(rng.choice(second))
                if candidate not in selected:
                    selected.append(candidate)
            edges[slot] = np.asarray(selected[: case.edge_size], dtype=np.int32)
        else:
            base = parts[(active_a + slot) % community_count]
            edges[slot] = rng.choice(base, size=case.edge_size, replace=False)
    return edges


def degree_preserving_hyperedge_rewire(edges: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    rewired = edges.copy()
    if rewired.shape[0] < 2:
        return rewired
    swaps = max(1, 10 * rewired.size)
    edge_count, edge_size = rewired.shape
    for _ in range(swaps):
        e1, e2 = rng.choice(edge_count, size=2, replace=False)
        p1 = int(rng.integers(edge_size))
        p2 = int(rng.integers(edge_size))
        a = int(rewired[e1, p1])
        b = int(rewired[e2, p2])
        if a == b:
            continue
        edge1 = set(int(x) for x in rewired[e1])
        edge2 = set(int(x) for x in rewired[e2])
        edge1.discard(a)
        edge2.discard(b)
        if b in edge1 or a in edge2:
            continue
        rewired[e1, p1] = b
        rewired[e2, p2] = a
    return rewired


def activity_preserving_resample(
    original_edges: np.ndarray,
    n: int,
    rng: np.random.Generator,
) -> np.ndarray:
    counts = np.bincount(original_edges.ravel(), minlength=n).astype(float)
    weights = counts + 1e-9
    return sample_weighted_edges(rng, n, original_edges.shape[0], original_edges.shape[1], weights)


def build_edge_context(case: Any, task: dict[str, Any], rng: np.random.Generator) -> dict[str, Any]:
    backend = ensure_backend()
    context: dict[str, Any] = {}
    null_model = str(task.get("null_model", ""))
    topology = str(task.get("topology", ""))
    if case.source == "real" and null_model == "block_order_shuffle":
        sequence = backend.read_real_sequence(case.real_sequence_path)
        context["block_order"] = rng.permutation(len(sequence))
    if topology == "heterogeneous_activity":
        ranks = np.arange(1, case.n + 1, dtype=float)
        weights = ranks ** -1.2
        context["activity_weights"] = weights[rng.permutation(case.n)]
    return context


def generate_edges_for_task(
    case: Any,
    task: dict[str, Any],
    rng: np.random.Generator,
    block: int,
    context: dict[str, Any],
) -> np.ndarray:
    backend = ensure_backend()
    null_model = str(task.get("null_model", ""))
    topology = str(task.get("topology", ""))

    if case.source == "real" and null_model:
        sequence = backend.read_real_sequence(case.real_sequence_path)
        if null_model == "original":
            return sequence[block % len(sequence)].copy()
        if null_model == "block_order_shuffle":
            order = context["block_order"]
            return sequence[int(order[block % len(order)])].copy()
        original = sequence[block % len(sequence)].copy()
        if null_model == "degree_preserving_rewire":
            return degree_preserving_hyperedge_rewire(original, rng)
        if null_model == "activity_preserving_resample":
            return activity_preserving_resample(original, case.n, rng)
        raise ValueError(f"Unknown null model: {null_model}")

    if case.source == "synthetic" and topology:
        if topology == "structured_ring":
            return backend.structured_ring_edges(case.n, case.n_edges, case.edge_size, block)
        if topology == "community_resample":
            return backend.community_edges(case, rng, block)
        if topology == "uniform_random":
            return backend.sample_edges(rng, case.n, case.n_edges, case.edge_size)
        if topology == "heterogeneous_activity":
            return sample_weighted_edges(
                rng,
                case.n,
                case.n_edges,
                case.edge_size,
                context["activity_weights"],
            )
        if topology == "temporal_modular_switching":
            return temporal_modular_switching_edges(case, rng, block)
        raise ValueError(f"Unknown synthetic topology: {topology}")

    return backend.generate_edges(case, rng, block)


def run_trial(task: dict[str, Any]) -> dict[str, Any]:
    backend = ensure_backend()
    case = resolve_case(task)
    rng = np.random.default_rng(int(task["seed"]))
    steps = int(task["steps"])
    tail_window = int(task["tail_window"])
    subgraph_duration = int(task["subgraph_duration"])
    beta = float(task["selection_intensity"])
    rho0 = min(1.0, max(0.0, float(task["rho0"])))
    mutation_rate = max(0.0, float(task.get("mutation_rate", 0.0)))
    trace_every = int(task.get("trace_every", 0) or 0)
    payoff_mode = str(task.get("payoff_mode", "") or "accumulated")
    update_mode = str(task.get("update_mode", "") or "synchronous")
    if update_mode not in {"synchronous", "asynchronous_in_place"}:
        raise ValueError(f"Unknown update_mode: {update_mode}")

    strategies = np.zeros(case.n, dtype=np.int8)
    coop_count = int(round(case.n * rho0))
    if coop_count > 0:
        strategies[rng.choice(case.n, size=coop_count, replace=False)] = 1

    block = 0
    edge_context = build_edge_context(case, task, rng)
    edges = generate_edges_for_task(case, task, rng, block, edge_context)
    incident_edges = backend.build_incident(edges, case.n)
    participation = backend.participation_counts(edges, case.n)
    rolling_participation = np.full(case.n, case.n_edges * case.edge_size / case.n)
    ewma_decay = math.exp(-1.0 / DEFAULT_EWMA_WINDOW)
    coop_trace: list[float] = []
    saved_trace: list[dict[str, Any]] = []
    csgc_selection_lift = 0.0
    csgc_selection_count = 0
    scrs_role_coop_count = 0
    scrs_role_count = 0
    conformist_updates = 0
    fermi_updates = 0
    mutation_updates = 0

    for t in range(steps):
        if t > 0 and t % subgraph_duration == 0:
            block += 1
            edges = generate_edges_for_task(case, task, rng, block, edge_context)
            incident_edges = backend.build_incident(edges, case.n)
            participation = backend.participation_counts(edges, case.n)
        rolling_participation = ewma_decay * rolling_participation + (1.0 - ewma_decay) * participation
        payoff = public_goods_payoff_for_mode(backend, strategies, edges, float(task["r"]), case.n, payoff_mode)
        variant = str(task["variant"])
        role_mode = role_selection_mode(variant)
        uses_group_scores = variant.startswith("csgc") or variant.startswith("scrs")
        csgc_scores = (
            backend.cooperative_success_score(strategies, edges, float(task["r"]))
            if uses_group_scores
            else np.zeros(edges.shape[0], dtype=float)
        )
        csgc_scores_shuffled = (
            rng.permutation(csgc_scores)
            if variant == "csgc_gamma1_shuffled" or variant.endswith("_score_shuffled")
            else None
        )
        activity_matched = None
        score_shuffled_q = None
        if "activity" in variant:
            activity_matched = backend.stratified_strategy_permutation(rng, strategies, rolling_participation)
        if variant.endswith("_score"):
            score_shuffled_q = rng.permutation(backend.edge_coop_scores(strategies, edges))
        shuffled_strategy_labels = rng.permutation(strategies) if variant.endswith("_strategy_shuffled") else None

        next_strategies = strategies.copy() if update_mode == "synchronous" else strategies
        focal_order = range(case.n) if update_mode == "synchronous" else rng.permutation(case.n)
        for focal_raw in focal_order:
            focal = int(focal_raw)
            incident = incident_edges[focal]
            if not incident:
                continue
            selected_slot: int | None
            if variant.endswith("_cooperator_only_random_neighborhood"):
                selected_slot = None
            elif variant.endswith("_cooperator_only_uniform_incident"):
                selected_slot = int(incident[int(rng.integers(len(incident)))])
            elif variant.endswith("_success_without_score_ranking"):
                successful = [int(slot) for slot in incident if float(csgc_scores[int(slot)]) > 1e-12]
                pool = successful if successful else [int(slot) for slot in incident]
                selected_slot = int(pool[int(rng.integers(len(pool)))])
            elif variant.startswith("csgc") or variant.startswith("scrs"):
                shuffle_edge_score = variant == "csgc_gamma1_shuffled" or variant.endswith("_score_shuffled")
                selected_slot = choose_csgc_edge_fast(
                    rng,
                    incident,
                    csgc_scores,
                    csgc_scores_shuffled,
                    shuffled=shuffle_edge_score,
                )
            else:
                selected_slot = int(incident[int(rng.integers(len(incident)))])
            if selected_slot is None:
                candidates = sorted(
                    {
                        int(node)
                        for slot in incident
                        for node in edges[int(slot)]
                        if int(node) != focal
                    }
                )
                selected_score = 1.0
            else:
                edge = edges[selected_slot]
                candidates = [int(node) for node in edge if int(node) != focal]
                selected_score = float(csgc_scores[selected_slot])
            if not candidates:
                continue
            if variant.startswith("scrs"):
                role = choose_scrs_role_fast(
                    rng,
                    candidates,
                    strategies,
                    payoff,
                    selected_score,
                    shuffled_strategy_labels,
                    role_mode,
                )
                scrs_role_coop_count += int(strategies[role] == 1)
                scrs_role_count += 1
            else:
                role = int(candidates[int(rng.integers(len(candidates)))])

            updated_by_conformity = False
            if variant.startswith("lfds"):
                target = backend.apply_lfds_update(
                    rng,
                    variant,
                    strategies,
                    edges,
                    incident,
                    focal,
                    selected_slot,
                    rolling_participation,
                    activity_matched,
                    score_shuffled_q,
                )
                if target is not None:
                    next_strategies[focal] = target
                    conformist_updates += 1
                    updated_by_conformity = True
            elif (variant.startswith("csgc") or variant.startswith("scrs")) and selected_slot is not None:
                csgc_selection_lift += float(csgc_scores[selected_slot] - csgc_scores[incident].mean())
                csgc_selection_count += 1

            if not updated_by_conformity and rng.random() < fermi_beta(float(payoff[focal]), float(payoff[role]), beta):
                next_strategies[focal] = strategies[role]
                fermi_updates += 1

        strategies = next_strategies
        if mutation_rate > 0:
            mutation_mask = rng.random(case.n) < mutation_rate
            if mutation_mask.any():
                strategies[mutation_mask] = 1 - strategies[mutation_mask]
                mutation_updates += int(mutation_mask.sum())
        coop = float(strategies.mean())
        coop_trace.append(coop)
        if trace_every > 0 and ((t + 1) % trace_every == 0 or t + 1 == steps):
            saved_trace.append(
                {
                    "experiment": task["experiment"],
                    "condition": task["condition"],
                    "case": task["case"],
                    "source": task["source"],
                    "variant": task["variant"],
                    "r": task["r"],
                    "rep": task["rep"],
                    "selection_intensity": task["selection_intensity"],
                    "rho0": task["rho0"],
                    "mutation_rate": task.get("mutation_rate", 0.0),
                    "payoff_mode": task.get("payoff_mode", ""),
                    "update_mode": task.get("update_mode", ""),
                    "step": t + 1,
                    "coop": coop,
                    "seed": task["seed"],
                }
            )

    tail = np.asarray(coop_trace[-tail_window:], dtype=float)
    def tail_mean(window: int) -> float:
        view = np.asarray(coop_trace[-min(window, len(coop_trace)) :], dtype=float)
        return float(view.mean())

    result = {col: task.get(col, "") for col in DETAIL_COLUMNS if col not in METRIC_COLUMNS}
    result.update(
        {
            "tail_coop": float(tail.mean()),
            "final_coop": float(coop_trace[-1]),
            "tail_coop_mean_500": tail_mean(500),
            "tail_coop_mean_1000": tail_mean(1000),
            "tail_coop_mean_2000": tail_mean(2000),
            "csgc_selection_lift": csgc_selection_lift / max(csgc_selection_count, 1),
            "scrs_role_coop_rate": scrs_role_coop_count / max(scrs_role_count, 1),
            "conformist_update_rate": conformist_updates / max(steps * case.n, 1),
            "fermi_update_rate": fermi_updates / max(steps * case.n, 1),
            "mutation_update_rate": mutation_updates / max(steps * case.n, 1),
            "_trace": saved_trace,
        }
    )
    return result


def run_one(task: dict[str, Any]) -> dict[str, Any]:
    return run_trial(task)


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


def table(df: pd.DataFrame) -> str:
    view = df.copy()
    for col in view.columns:
        if pd.api.types.is_float_dtype(view[col]):
            view[col] = view[col].map(lambda x: f"{x:.4f}")
    header = "| " + " | ".join(view.columns) + " |"
    divider = "| " + " | ".join(["---"] * len(view.columns)) + " |"
    rows = ["| " + " | ".join(str(v) for v in row) + " |" for row in view.to_numpy()]
    return "\n".join([header, divider, *rows])


def summarize(
    details: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if details.empty:
        empty = pd.DataFrame()
        return empty, empty, empty, empty, empty, empty, empty

    group_cols = CELL_CONTEXT_COLUMNS + ["variant"]
    summary = (
        details.groupby(group_cols, as_index=False, dropna=False)
        .agg(
            reps=("rep", "nunique"),
            tail_coop_mean=("tail_coop", "mean"),
            tail_coop_sd=("tail_coop", lambda x: float(x.std(ddof=1)) if len(x) > 1 else 0.0),
            tail_coop_se=("tail_coop", se),
            final_coop_mean=("final_coop", "mean"),
            final_coop_sd=("final_coop", lambda x: float(x.std(ddof=1)) if len(x) > 1 else 0.0),
            final_coop_se=("final_coop", se),
            tail_coop_mean_500=("tail_coop_mean_500", "mean"),
            tail_coop_mean_1000=("tail_coop_mean_1000", "mean"),
            tail_coop_mean_2000=("tail_coop_mean_2000", "mean"),
            csgc_selection_lift=("csgc_selection_lift", "mean"),
            scrs_role_coop_rate=("scrs_role_coop_rate", "mean"),
            conformist_update_rate=("conformist_update_rate", "mean"),
            fermi_update_rate=("fermi_update_rate", "mean"),
            mutation_update_rate=("mutation_update_rate", "mean"),
        )
        .sort_values(CELL_CONTEXT_COLUMNS + ["variant"])
        .reset_index(drop=True)
    )
    summary["tail_coop_ci95_low"] = [
        ci_low(mean, se_value) for mean, se_value in zip(summary["tail_coop_mean"], summary["tail_coop_se"])
    ]
    summary["tail_coop_ci95_high"] = [
        ci_high(mean, se_value) for mean, se_value in zip(summary["tail_coop_mean"], summary["tail_coop_se"])
    ]

    cell_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    for context_values, group in summary.groupby(CELL_CONTEXT_COLUMNS, sort=True, dropna=False):
        if not isinstance(context_values, tuple):
            context_values = (context_values,)
        context = dict(zip(CELL_CONTEXT_COLUMNS, context_values))
        lookup = {str(row.variant): row for row in group.itertuples(index=False)}
        if "scrs_gamma1" not in lookup:
            continue
        scrs = lookup["scrs_gamma1"]
        scrs_mean = float(scrs.tail_coop_mean)
        scrs_se = float(scrs.tail_coop_se)
        control_values: dict[str, float] = {}
        for control, ctrl in lookup.items():
            if control == "scrs_gamma1":
                continue
            ctrl_mean = float(ctrl.tail_coop_mean)
            ctrl_se = float(ctrl.tail_coop_se)
            control_values[control] = ctrl_mean
            gap = scrs_mean - ctrl_mean
            gap_se = math.sqrt(scrs_se * scrs_se + ctrl_se * ctrl_se)
            z_score = gap / gap_se if gap_se > 0 else (math.inf if gap > 0 else -math.inf if gap < 0 else 0.0)
            row = {
                **context,
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
            pair_rows.append(row)

        strongest_control = max(control_values, key=control_values.get) if control_values else ""
        row = {
            **context,
            "scrs": scrs_mean,
            "scrs_se": scrs_se,
            "scrs_ci95_low": ci_low(scrs_mean, scrs_se),
            "scrs_ci95_high": ci_high(scrs_mean, scrs_se),
            "scrs_final": float(scrs.final_coop_mean),
            "strongest_control": strongest_control,
            "strongest_control_tail": control_values.get(strongest_control, math.nan),
            "gap_vs_strongest": scrs_mean - control_values.get(strongest_control, math.nan)
            if strongest_control
            else math.nan,
            "scrs_role_coop_rate": float(scrs.scrs_role_coop_rate),
            "scrs_csgc_selection_lift": float(scrs.csgc_selection_lift),
        }
        for control in KEY_CONTROLS:
            if control in control_values:
                row[f"gap_vs_{control}"] = scrs_mean - control_values[control]
            else:
                row[f"gap_vs_{control}"] = math.nan
        cell_rows.append(row)

    pairwise = pd.DataFrame(pair_rows)
    cell = pd.DataFrame(cell_rows)
    source_summary = aggregate_cell_summary(cell, ["experiment", "condition", "source"])
    case_summary = aggregate_cell_summary(cell, ["experiment", "condition", "case", "source"])
    mechanism_summary = aggregate_mechanism_summary(pairwise)
    paired_gap_summary = aggregate_paired_gap_summary(details)
    return summary, cell, source_summary, case_summary, mechanism_summary, pairwise, paired_gap_summary


def aggregate_paired_gap_summary(details: pd.DataFrame) -> pd.DataFrame:
    if details.empty:
        return pd.DataFrame()
    rep_context_cols = CELL_CONTEXT_COLUMNS + ["rep"]
    replicate_rows: list[dict[str, Any]] = []
    for context_values, group in details.groupby(rep_context_cols, sort=True, dropna=False):
        if not isinstance(context_values, tuple):
            context_values = (context_values,)
        context = dict(zip(rep_context_cols, context_values))
        values = group.groupby("variant", dropna=False)["tail_coop"].mean().to_dict()
        if "scrs_gamma1" not in values:
            continue
        scrs_tail = float(values["scrs_gamma1"])
        for control, control_tail_raw in values.items():
            if control == "scrs_gamma1":
                continue
            control_tail = float(control_tail_raw)
            replicate_rows.append(
                {
                    **{col: context[col] for col in CELL_CONTEXT_COLUMNS},
                    "rep": int(context["rep"]),
                    "control": str(control),
                    "control_family": control_family(str(control)),
                    "scrs_tail": scrs_tail,
                    "control_tail": control_tail,
                    "gap": scrs_tail - control_tail,
                }
            )
    if not replicate_rows:
        return pd.DataFrame()
    rep_gaps = pd.DataFrame(replicate_rows)
    grouped = (
        rep_gaps.groupby(CELL_CONTEXT_COLUMNS + ["control", "control_family"], as_index=False, dropna=False)
        .agg(
            paired_reps=("rep", "nunique"),
            positive_reps=("gap", lambda x: int((x > 0).sum())),
            mean_gap=("gap", "mean"),
            sd_gap=("gap", lambda x: float(x.std(ddof=1)) if len(x) > 1 else 0.0),
            min_gap=("gap", "min"),
            max_gap=("gap", "max"),
        )
        .sort_values(CELL_CONTEXT_COLUMNS + ["control"])
        .reset_index(drop=True)
    )
    grouped["gap_se"] = grouped.apply(
        lambda row: float(row.sd_gap / math.sqrt(row.paired_reps)) if int(row.paired_reps) > 1 else 0.0,
        axis=1,
    )
    grouped["gap_ci95_low"] = [ci_low(mean, se_value) for mean, se_value in zip(grouped["mean_gap"], grouped["gap_se"])]
    grouped["gap_ci95_high"] = [
        ci_high(mean, se_value) for mean, se_value in zip(grouped["mean_gap"], grouped["gap_se"])
    ]
    grouped["ci_positive"] = grouped["gap_ci95_low"] > 0
    return grouped


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


def aggregate_cell_summary(cell: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if cell.empty:
        return pd.DataFrame()
    agg: dict[str, Any] = {
        "cells": ("scrs", "size"),
        "mean_scrs": ("scrs", "mean"),
        "min_scrs": ("scrs", "min"),
        "max_scrs_se": ("scrs_se", "max"),
        "strict_wins": ("gap_vs_strongest", lambda x: int((x > 0).sum())),
        "mean_gap_vs_strongest": ("gap_vs_strongest", "mean"),
        "min_gap_vs_strongest": ("gap_vs_strongest", "min"),
        "mean_role_coop_rate": ("scrs_role_coop_rate", "mean"),
        "mean_selection_lift": ("scrs_csgc_selection_lift", "mean"),
    }
    for control in KEY_CONTROLS:
        col = f"gap_vs_{control}"
        if col in cell.columns:
            agg[f"mean_gap_vs_{control}"] = (col, "mean")
            agg[f"min_gap_vs_{control}"] = (col, "min")
    return cell.groupby(group_cols, as_index=False, dropna=False).agg(**agg).sort_values(group_cols).reset_index(drop=True)


def aggregate_mechanism_summary(pairwise: pd.DataFrame) -> pd.DataFrame:
    if pairwise.empty:
        return pd.DataFrame()
    view = pairwise[pairwise["control"].isin(KEY_CONTROLS)].copy()
    return (
        view.groupby(["experiment", "condition", "source", "control"], as_index=False, dropna=False)
        .agg(
            cells=("gap", "size"),
            positive_gaps=("gap", lambda x: int((x > 0).sum())),
            ci_positive_gaps=("gap_ci95_low", lambda x: int((x > 0).sum())),
            mean_gap=("gap", "mean"),
            min_gap=("gap", "min"),
            max_gap=("gap", "max"),
            mean_gap_se=("gap_se", "mean"),
        )
        .sort_values(["experiment", "condition", "source", "control"])
        .reset_index(drop=True)
    )


def qa_summary(details: pd.DataFrame, total_trials: int) -> dict[str, Any]:
    if details.empty:
        return {
            "rows": 0,
            "expected_total_trials": total_trials,
            "duplicate_keys": 0,
            "cells": 0,
            "min_reps_per_cell": 0,
            "max_reps_per_cell": 0,
        }
    duplicate_keys = int(details.duplicated(KEY_COLUMNS).sum())
    reps = details.groupby(CELL_CONTEXT_COLUMNS + ["variant"], dropna=False)["rep"].nunique()
    return {
        "rows": int(len(details)),
        "expected_total_trials": int(total_trials),
        "duplicate_keys": duplicate_keys,
        "cells": int(len(reps)),
        "min_reps_per_cell": int(reps.min()) if not reps.empty else 0,
        "max_reps_per_cell": int(reps.max()) if not reps.empty else 0,
    }


def write_outputs(out_root: Path, details: pd.DataFrame, total_trials: int, report_title: str, design_text: str) -> None:
    summary, cell, source_summary, case_summary, mechanism_summary, pairwise, paired_gap_summary = summarize(details)
    summary.to_csv(out_root / "summary.csv", index=False)
    cell.to_csv(out_root / "scrs_nc_cell_summary.csv", index=False)
    source_summary.to_csv(out_root / "scrs_nc_source_summary.csv", index=False)
    case_summary.to_csv(out_root / "scrs_nc_case_summary.csv", index=False)
    mechanism_summary.to_csv(out_root / "scrs_nc_mechanism_summary.csv", index=False)
    pairwise.to_csv(out_root / "scrs_nc_pairwise_gap_summary.csv", index=False)
    paired_gap_summary.to_csv(out_root / "scrs_nc_paired_gap_summary.csv", index=False)
    qa = qa_summary(details, total_trials)
    (out_root / "qa_summary.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
    write_report(out_root, report_title, design_text, source_summary, case_summary, mechanism_summary, cell, qa)


def write_report(
    out_root: Path,
    report_title: str,
    design_text: str,
    source_summary: pd.DataFrame,
    case_summary: pd.DataFrame,
    mechanism_summary: pd.DataFrame,
    cell: pd.DataFrame,
    qa: dict[str, Any],
) -> None:
    decisions = decision_lines(source_summary, mechanism_summary, qa)
    report = [
        f"# {report_title}",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Design",
        "",
        design_text.strip(),
        "",
        "## QA",
        "",
        "```json",
        json.dumps(qa, indent=2),
        "```",
        "",
        "## Decision",
        "",
        *decisions,
        "",
        "## Source Summary",
        "",
        table(source_summary) if not source_summary.empty else "No rows yet.",
        "",
        "## Case Summary",
        "",
        table(case_summary) if not case_summary.empty else "No rows yet.",
        "",
        "## Mechanism Summary",
        "",
        table(mechanism_summary) if not mechanism_summary.empty else "No rows yet.",
        "",
        "## Cell Summary",
        "",
        table(cell) if not cell.empty else "No rows yet.",
    ]
    (out_root / "SCRS_NC_supplemental_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def decision_lines(source_summary: pd.DataFrame, mechanism_summary: pd.DataFrame, qa: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    complete = int(qa.get("rows", 0)) == int(qa.get("expected_total_trials", -1))
    duplicate_ok = int(qa.get("duplicate_keys", 0)) == 0
    rep_ok = int(qa.get("min_reps_per_cell", 0)) == int(qa.get("max_reps_per_cell", 0)) == DEFAULT_REPS
    if complete and duplicate_ok and rep_ok:
        lines.append("QA PASS: complete formal supplemental run with no duplicate trial keys and 50 reps per cell.")
    elif duplicate_ok:
        lines.append("QA PARTIAL: no duplicate trial keys, but the run is not yet complete or reps are still incomplete.")
    else:
        lines.append("QA FAIL: duplicate trial keys detected; inspect detail.csv before using results.")

    if not source_summary.empty:
        real = source_summary[source_summary["source"] == "real"]
        synthetic = source_summary[source_summary["source"] == "synthetic"]
        if not real.empty:
            lines.append(
                "REAL PERFORMANCE: mean SCRS tail cooperation ranges from "
                f"{float(real['mean_scrs'].min()):.4f} to {float(real['mean_scrs'].max()):.4f} across grouped conditions."
            )
        if not synthetic.empty:
            lines.append(
                "SYNTHETIC PERFORMANCE: mean SCRS tail cooperation ranges from "
                f"{float(synthetic['mean_scrs'].min()):.4f} to {float(synthetic['mean_scrs'].max()):.4f} across grouped conditions."
            )
    role = mechanism_summary[mechanism_summary["control"] == "scrs_gamma1_strategy_shuffled"] if not mechanism_summary.empty else pd.DataFrame()
    score = mechanism_summary[mechanism_summary["control"] == "scrs_gamma1_score_shuffled"] if not mechanism_summary.empty else pd.DataFrame()
    if not role.empty:
        lines.append(
            "ROLE-SCREENING CHECK: mean gap vs strategy-shuffled ranges from "
            f"{float(role['mean_gap'].min()):.4f} to {float(role['mean_gap'].max()):.4f}."
        )
    if not score.empty:
        lines.append(
            "EDGE-SCORE BOUNDARY CHECK: mean gap vs score-shuffled ranges from "
            f"{float(score['mean_gap'].min()):.4f} to {float(score['mean_gap'].max()):.4f}."
        )
    return lines


def write_status(out_root: Path, payload: dict[str, Any]) -> None:
    tmp = out_root / "status.json.tmp"
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    target = out_root / "status.json"
    try:
        tmp.replace(target)
    except PermissionError:
        # Some macOS LaunchAgent-created temp files can inherit a MAC label that
        # prevents atomic replacement in Documents. Preserve the run by falling
        # back to a direct status write; detail.csv remains the source of record.
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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


def write_metadata(
    out_root: Path,
    experiment_name: str,
    design_text: str,
    all_tasks: list[dict[str, Any]],
    script_path: Path,
    workers: int,
    argv: list[str],
) -> None:
    backend = ensure_backend()
    metadata = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "experiment_name": experiment_name,
        "project": str(PROJECT),
        "backend_script": str(BACKEND_SCRIPT),
        "script_path": str(script_path),
        "common_library": str(Path(__file__).resolve()),
        "argv": argv,
        "workers": workers,
        "total_trials": len(all_tasks),
        "key_columns": KEY_COLUMNS,
        "detail_columns": DETAIL_COLUMNS,
        "cases": [case.__dict__ for case in getattr(backend, "CASES", [])],
        "planned_tasks_path": str(out_root / "planned_tasks.csv"),
    }
    (out_root / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    pd.DataFrame(all_tasks).to_csv(out_root / "planned_tasks.csv", index=False)
    (out_root / "SCRS_NC_supplemental_design.md").write_text(design_text.strip() + "\n", encoding="utf-8")
    shutil.copy2(script_path, out_root / script_path.name)
    shutil.copy2(Path(__file__).resolve(), out_root / "scrs_nc_experiment_common.py")
    shutil.copy2(BACKEND_SCRIPT, out_root / "backend_run_scrs_strict_smoke.py")


def run_experiment(
    *,
    args: Any,
    all_tasks: list[dict[str, Any]],
    design_text: str,
    report_title: str,
    script_path: Path,
    experiment_name: str,
) -> None:
    validate_planned_tasks(all_tasks)
    if args.plan_only:
        print(design_text.strip())
        print(f"Total trials: {len(all_tasks)}")
        print(f"Default output root: {args.out_root}")
        return

    out_root = Path(args.out_root).expanduser()
    out_root.mkdir(parents=True, exist_ok=bool(args.resume))
    detail_path = out_root / "detail.csv"
    trace_path = out_root / "trajectory.csv"
    write_metadata(out_root, experiment_name, design_text, all_tasks, script_path, int(args.workers), sys.argv)

    pending = build_pending_tasks(all_tasks, detail_path)
    total = len(all_tasks)
    already_done = total - len(pending)
    started = time.time()
    print(f"Output root: {out_root}", flush=True)
    print(f"Supplemental trials: total={total}, completed={already_done}, pending={len(pending)}", flush=True)

    write_status(
        out_root,
        {
            "state": "running" if pending else "summarizing",
            "output_root": str(out_root),
            "total_trials": total,
            "completed_trials": already_done,
            "pending_trials": len(pending),
            "workers": int(args.workers),
            "last_update": datetime.now().isoformat(timespec="seconds"),
        },
    )

    if not pending:
        details = load_detail(detail_path)
        write_outputs(out_root, details, total, report_title, design_text)
        write_status(
            out_root,
            {
                "state": "complete",
                "output_root": str(out_root),
                "total_trials": total,
                "completed_trials": len(details),
                "pending_trials": max(0, total - len(details)),
                "workers": int(args.workers),
                "last_update": datetime.now().isoformat(timespec="seconds"),
                "report": str(out_root / "SCRS_NC_supplemental_report.md"),
            },
        )
        print("No pending trials. Outputs refreshed.", flush=True)
        return

    detail_write_header = not detail_path.exists() or detail_path.stat().st_size == 0
    trace_write_header = not trace_path.exists() or trace_path.stat().st_size == 0
    completed_now = 0
    next_status_at = 0
    stopped = False
    stop_path = out_root / "STOP"
    with detail_path.open("a", newline="", encoding="utf-8") as detail_handle, trace_path.open(
        "a", newline="", encoding="utf-8"
    ) as trace_handle:
        detail_writer = csv.DictWriter(detail_handle, fieldnames=DETAIL_COLUMNS)
        trace_fieldnames = [
            "experiment",
            "condition",
            "case",
            "source",
            "variant",
            "r",
            "rep",
            "selection_intensity",
            "rho0",
            "mutation_rate",
            "payoff_mode",
            "update_mode",
            "step",
            "coop",
            "seed",
        ]
        trace_writer = csv.DictWriter(trace_handle, fieldnames=trace_fieldnames)
        if detail_write_header:
            detail_writer.writeheader()
        if trace_write_header:
            trace_writer.writeheader()
        detail_handle.flush()
        trace_handle.flush()

        pool = mp.Pool(processes=int(args.workers), initializer=init_worker)
        try:
            for result in pool.imap_unordered(run_one, pending, chunksize=int(args.chunksize)):
                trace_rows = result.pop("_trace", [])
                detail_writer.writerow({col: result.get(col, "") for col in DETAIL_COLUMNS})
                for trace_row in trace_rows:
                    trace_writer.writerow(trace_row)
                completed_now += 1
                if completed_now % int(args.flush_every) == 0:
                    detail_handle.flush()
                    trace_handle.flush()
                    os.fsync(detail_handle.fileno())
                    os.fsync(trace_handle.fileno())
                completed_total = already_done + completed_now
                elapsed = time.time() - started
                rate = completed_now / elapsed if elapsed > 0 else 0.0
                remaining = (len(pending) - completed_now) / rate if rate > 0 else math.inf
                if completed_now >= next_status_at or completed_now == len(pending):
                    write_status(
                        out_root,
                        {
                            "state": "running" if completed_now < len(pending) else "summarizing",
                            "output_root": str(out_root),
                            "total_trials": total,
                            "completed_trials": completed_total,
                            "pending_trials": total - completed_total,
                            "completed_this_run": completed_now,
                            "workers": int(args.workers),
                            "elapsed_seconds_this_run": elapsed,
                            "trials_per_second_this_run": rate,
                            "estimated_remaining_seconds": remaining,
                            "estimated_remaining_text": seconds_to_text(remaining),
                            "last_update": datetime.now().isoformat(timespec="seconds"),
                        },
                    )
                    print(
                        f"finished {completed_total}/{total}; "
                        f"rate={rate:.3f} trials/s; eta={seconds_to_text(remaining)}",
                        flush=True,
                    )
                    next_status_at = completed_now + int(args.progress_every)
                if stop_path.exists():
                    stopped = True
                    print(f"STOP detected at {stop_path}; pausing after completed trial.", flush=True)
                    pool.terminate()
                    break
            if not stopped:
                pool.close()
        finally:
            pool.join()
            detail_handle.flush()
            trace_handle.flush()
            os.fsync(detail_handle.fileno())
            os.fsync(trace_handle.fileno())

    details = load_detail(detail_path)
    write_outputs(out_root, details, total, report_title, design_text)
    if stopped:
        state = "paused"
        pending_trials = max(0, total - len(details))
    else:
        state = "complete"
        pending_trials = max(0, total - len(details))
    write_status(
        out_root,
        {
            "state": state,
            "output_root": str(out_root),
            "total_trials": total,
            "completed_trials": len(details),
            "pending_trials": pending_trials,
            "workers": int(args.workers),
            "last_update": datetime.now().isoformat(timespec="seconds"),
            "report": str(out_root / "SCRS_NC_supplemental_report.md"),
        },
    )
    print(f"Supplemental SCRS run {state}: {out_root}", flush=True)


def add_common_args(parser: Any, default_out_root: Path) -> None:
    parser.add_argument("--out-root", default=str(default_out_root), help="Output directory.")
    parser.add_argument("--workers", type=int, default=min(6, max(1, (os.cpu_count() or 2) - 1)))
    parser.add_argument("--chunksize", type=int, default=1)
    parser.add_argument("--flush-every", type=int, default=1)
    parser.add_argument("--progress-every", type=int, default=100)
    parser.add_argument("--resume", action="store_true", help="Resume an existing output directory.")
    parser.add_argument("--plan-only", action="store_true", help="Print design and total trials only.")
    parser.add_argument("--smoke", action="store_true", help="Run a small non-formal smoke test.")
    parser.add_argument("--steps", type=int, default=None, help="Override steps.")
    parser.add_argument("--reps", type=int, default=None, help="Override reps.")


def validate_common_args(args: Any) -> None:
    for name in ("workers", "chunksize", "flush_every", "progress_every"):
        if int(getattr(args, name)) < 1:
            raise ValueError(f"--{name.replace('_', '-')} must be >= 1")
    if args.steps is not None and int(args.steps) < 1:
        raise ValueError("--steps must be >= 1")
    if args.reps is not None and int(args.reps) < 1:
        raise ValueError("--reps must be >= 1")
