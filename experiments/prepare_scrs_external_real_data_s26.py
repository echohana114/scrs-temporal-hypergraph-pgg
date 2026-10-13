#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import re
import shutil
import tarfile
import urllib.request
import zipfile
from collections import Counter, defaultdict
from http.cookiejar import CookieJar
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np


PROJECT = Path("/Users/hui/Documents/New project 2/temporal_hypergraph_pgg_pilot")
DEFAULT_OUT_ROOT = PROJECT / "real_data_external_s26" / f"prepared_{datetime.now().strftime('%Y%m%d_%H%M')}"
EDGE_SIZE = 6
N_EDGES = 33
N_CAP = 400
TARGET_BLOCKS = 20
SEED = 2026090102


@dataclass(frozen=True)
class ExternalDataset:
    slug: str
    family: str
    source_url: str
    urls: tuple[str, ...]
    parser: str = "benson_tar"


PRIMARY_DATASETS = [
    ExternalDataset(
        "external_copenhagen_bluetooth",
        "bluetooth_proximity",
        "https://www.nature.com/articles/s41597-019-0325-x",
        ("https://figshare.com/articles/dataset/The_Copenhagen_Networks_Study_interaction_data/7267433",),
        parser="contact_csv",
    ),
    ExternalDataset(
        "external_email_eu",
        "email_higher_order",
        "https://www.cs.cornell.edu/~arb/data/email-Eu/",
        ("gdrive://1amLeVudLBDRglCXKlieg6HHE-vu81EVF/email-Eu.tar.gz",),
    ),
    ExternalDataset(
        "external_congress_bills",
        "legislative_cosponsorship",
        "https://www.cs.cornell.edu/~arb/data/congress-bills/",
        ("gdrive://1gH1uJMZpn_SCJSRbORPH4JRQeevLwTyO/congress-bills.tar.gz",),
    ),
    ExternalDataset(
        "external_threads_ask_ubuntu",
        "online_thread_participation",
        "https://www.cs.cornell.edu/~arb/data/threads-ask-ubuntu/",
        ("gdrive://1ppdJ7CvF_aJ9GLJmVWgKpNL55YVH8MYh/threads-ask-ubuntu.tar.gz",),
    ),
    ExternalDataset(
        "external_email_enron",
        "email_higher_order",
        "https://www.cs.cornell.edu/~arb/data/email-Enron/",
        (
            "gdrive://1tTVZkdpgRW47WWmsrdUCukHz0x2M6N77/email-Enron.tar.gz",
            "https://cricca.disi.unitn.it/datasets/hypergraphx-data/email-Enron-core/email-Enron-core.json",
        ),
    ),
]

FALLBACK_DATASETS = [
    ExternalDataset(
        "external_tags_ask_ubuntu",
        "online_tag_simplices",
        "https://www.cs.cornell.edu/~arb/data/tags-ask-ubuntu/",
        ("gdrive://1tb1ZJlXEJnlRkXpTuBZlOqqsFknWCkUV/tags-ask-ubuntu.tar.gz",),
    ),
]
DATASETS = PRIMARY_DATASETS + FALLBACK_DATASETS


def open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open("r", encoding="utf-8", newline="")


def download_first(urls: Iterable[str], dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for url in urls:
        target = dest_dir / Path(url.split("?", 1)[0]).name
        try:
            with urllib.request.urlopen(url, timeout=120) as response, target.open("wb") as handle:
                shutil.copyfileobj(response, handle)
            return target
        except Exception as exc:  # noqa: BLE001 - record all source failures for reproducibility.
            errors.append(f"{url}: {exc}")
            if target.exists() and target.stat().st_size == 0:
                target.unlink()
    raise RuntimeError("; ".join(errors))


def download_url(url: str, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=120) as response, target.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    return target


def download_google_drive_file(file_id: str, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    cookie_jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    base_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    response = opener.open(base_url, timeout=120)
    content_type = response.headers.get("Content-Type", "")
    content_disposition = response.headers.get("Content-Disposition", "")
    if "attachment" in content_disposition.lower() or "text/html" not in content_type.lower():
        with target.open("wb") as handle:
            shutil.copyfileobj(response, handle)
        return target

    html = response.read().decode("utf-8", errors="ignore")
    token = ""
    for cookie in cookie_jar:
        if cookie.name.startswith("download_warning"):
            token = cookie.value
            break
    if not token:
        match = re.search(r"confirm=([0-9A-Za-z_\\-]+)", html)
        if match:
            token = match.group(1)
    if not token:
        target.write_text(html, encoding="utf-8")
        raise RuntimeError(f"Google Drive confirmation token not found for {file_id}")
    confirmed_url = f"{base_url}&confirm={token}"
    with opener.open(confirmed_url, timeout=120) as confirmed, target.open("wb") as handle:
        shutil.copyfileobj(confirmed, handle)
    return target


def download_dataset_files(dataset: ExternalDataset, dest_dir: Path) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    errors: list[str] = []
    for url in dataset.urls:
        if url.startswith("gdrive://"):
            try:
                payload = url.removeprefix("gdrive://")
                file_id, file_name = payload.split("/", 1)
                downloaded.append(download_google_drive_file(file_id, dest_dir / file_name))
                continue
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{url}: {exc}")
                continue
        if "figshare.com/articles/" in url:
            article_id = url.rstrip("/").rsplit("/", 1)[-1]
            api_url = f"https://api.figshare.com/v2/articles/{article_id}"
            try:
                with urllib.request.urlopen(api_url, timeout=120) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                files = payload.get("files", [])
                wanted = [
                    item
                    for item in files
                    if any(token in str(item.get("name", "")).lower() for token in ("bt", "bluetooth", "proximity", "contact"))
                ]
                if not wanted:
                    wanted = files[:1]
                for item in wanted:
                    file_url = str(item.get("download_url", ""))
                    file_name = str(item.get("name") or Path(file_url).name)
                    if file_url:
                        downloaded.append(download_url(file_url, dest_dir / file_name))
                continue
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{api_url}: {exc}")
                continue
        try:
            target = dest_dir / Path(url.split("?", 1)[0]).name
            downloaded.append(download_url(url, target))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{url}: {exc}")
    if downloaded:
        return downloaded
    raise RuntimeError("; ".join(errors))


def extract_if_needed(path: Path, extract_dir: Path) -> Path:
    extract_dir.mkdir(parents=True, exist_ok=True)
    if path.suffixes[-2:] == [".tar", ".gz"] or path.suffix == ".tgz":
        with tarfile.open(path, "r:*") as tar:
            target_root = extract_dir.resolve()
            for member in tar.getmembers():
                member_path = (extract_dir / member.name).resolve()
                if target_root not in member_path.parents and member_path != target_root:
                    raise ValueError(f"Unsafe tar member path: {member.name}")
            tar.extractall(extract_dir)
        return extract_dir
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            target_root = extract_dir.resolve()
            for member in archive.namelist():
                member_path = (extract_dir / member).resolve()
                if target_root not in member_path.parents and member_path != target_root:
                    raise ValueError(f"Unsafe zip member path: {member}")
            archive.extractall(extract_dir)
        return extract_dir
    return path.parent


def extract_downloaded_files(paths: list[Path], extract_dir: Path) -> Path:
    root = extract_dir
    for path in paths:
        candidate = extract_if_needed(path, extract_dir / path.stem.replace(".", "_"))
        if candidate != path.parent:
            root = extract_dir
    return root if root.exists() else paths[0].parent


def read_ints(path: Path) -> list[int]:
    with open_text(path) as handle:
        return [int(float(line.strip())) for line in handle if line.strip()]


def find_benson_files(root: Path) -> tuple[Path, Path, Path]:
    files = list(root.rglob("*"))
    nverts = [p for p in files if p.is_file() and p.name.endswith("-nverts.txt")]
    simplices = [p for p in files if p.is_file() and p.name.endswith("-simplices.txt")]
    times = [p for p in files if p.is_file() and p.name.endswith("-times.txt")]
    if not nverts or not simplices or not times:
        raise FileNotFoundError(f"Benson nverts/simplices/times files not found under {root}")
    return nverts[0], simplices[0], times[0]


def read_benson_events(root: Path) -> list[tuple[int, tuple[str, ...]]]:
    nverts_path, simplices_path, times_path = find_benson_files(root)
    nverts = read_ints(nverts_path)
    simplices = read_ints(simplices_path)
    times = read_ints(times_path)
    if len(nverts) != len(times):
        raise ValueError("nverts and times have different lengths")
    events: list[tuple[int, tuple[str, ...]]] = []
    cursor = 0
    for size, timestamp in zip(nverts, times):
        nodes = tuple(str(node) for node in simplices[cursor : cursor + size])
        cursor += size
        unique_nodes = tuple(dict.fromkeys(nodes))
        if len(unique_nodes) >= 2:
            events.append((int(timestamp), unique_nodes))
    return events


def read_hgx_json_events(path: Path) -> list[tuple[int, tuple[str, ...]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_edges = payload.get("edge_list") or payload.get("edges") or payload.get("hyperedges") or []
    raw_meta = payload.get("edge_metadata") or payload.get("edge_meta") or []
    events: list[tuple[int, tuple[str, ...]]] = []
    for idx, raw_edge in enumerate(raw_edges):
        if isinstance(raw_edge, dict):
            nodes = raw_edge.get("nodes") or raw_edge.get("edge") or raw_edge.get("members") or []
            timestamp = raw_edge.get("time") or raw_edge.get("timestamp") or idx
        else:
            nodes = raw_edge
            meta = raw_meta[idx] if idx < len(raw_meta) and isinstance(raw_meta[idx], dict) else {}
            timestamp = meta.get("time") or meta.get("timestamp") or idx
        unique_nodes = tuple(dict.fromkeys(str(node) for node in nodes))
        if len(unique_nodes) >= 2:
            events.append((int(float(timestamp)), unique_nodes))
    if not events:
        raise ValueError(f"No temporal hyperedges parsed from {path}")
    return events


def read_contact_csv_events(root: Path) -> list[tuple[int, tuple[str, ...]]]:
    candidates = [
        p
        for p in root.rglob("*")
        if p.is_file() and (p.suffix.lower() in {".csv", ".txt", ".tsv", ".gz"} or p.name.endswith(".csv.gz"))
    ]
    if not candidates:
        raise FileNotFoundError(f"No contact CSV/TXT file found under {root}")
    events: list[tuple[int, tuple[str, ...]]] = []
    for path in sorted(candidates):
        with open_text(path) as handle:
            sample = handle.read(4096)
            handle.seek(0)
            delimiter = "\t" if "\t" in sample else "," if "," in sample else None
            reader = csv.reader(handle, delimiter=delimiter) if delimiter else csv.reader(handle, delimiter=" ")
            for row in reader:
                row = [item.strip() for item in row if item.strip()]
                if len(row) < 3:
                    continue
                numeric_positions: list[int] = []
                for idx, item in enumerate(row):
                    try:
                        float(item)
                        numeric_positions.append(idx)
                    except ValueError:
                        continue
                if not numeric_positions:
                    continue
                time_idx = numeric_positions[0]
                node_values = [item for idx, item in enumerate(row) if idx != time_idx]
                if len(node_values) >= 2:
                    events.append((int(float(row[time_idx])), tuple(node_values[:2])))
        if events:
            break
    if not events:
        raise ValueError(f"No pairwise contact events parsed under {root}")
    return events


def same_block_expansion_pool(block_events: list[tuple[int, tuple[int, ...]]]) -> dict[int, list[int]]:
    co_nodes: dict[int, Counter[int]] = defaultdict(Counter)
    for _, nodes in block_events:
        for node in nodes:
            co_nodes[node].update(other for other in nodes if other != node)
    return {node: [other for other, _ in counts.most_common()] for node, counts in co_nodes.items()}


def normalize_event_to_edge(
    nodes: tuple[int, ...],
    pool: dict[int, list[int]],
    block_activity: list[int],
    edge_size: int,
    rng: np.random.Generator,
) -> tuple[tuple[int, ...], bool, bool]:
    unique_nodes = list(dict.fromkeys(nodes))
    oversized = len(unique_nodes) > edge_size
    expanded = len(unique_nodes) < edge_size
    if oversized:
        unique_nodes = [int(x) for x in rng.choice(unique_nodes, size=edge_size, replace=False)]
    if expanded:
        selected = list(unique_nodes)
        seen = set(selected)
        for base in list(selected):
            for candidate in pool.get(base, []):
                if candidate not in seen:
                    selected.append(candidate)
                    seen.add(candidate)
                if len(selected) >= edge_size:
                    break
            if len(selected) >= edge_size:
                break
        for candidate in block_activity:
            if candidate not in seen:
                selected.append(candidate)
                seen.add(candidate)
            if len(selected) >= edge_size:
                break
        unique_nodes = selected[:edge_size]
    return tuple(sorted(unique_nodes[:edge_size])), expanded, oversized


def write_fixed_sequence(
    events: list[tuple[int, tuple[str, ...]]],
    dataset: ExternalDataset,
    out_dir: Path,
    *,
    edge_size: int,
    n_edges: int,
    n_cap: int,
    target_blocks: int,
    seed: int,
) -> dict[str, object]:
    if not events:
        raise ValueError(f"{dataset.slug}: no events to prepare")
    activity = Counter(node for _, nodes in events for node in nodes)
    keep_raw = {node for node, _ in activity.most_common(n_cap)}
    filtered_raw = [
        (timestamp, tuple(node for node in nodes if node in keep_raw))
        for timestamp, nodes in sorted(events, key=lambda item: item[0])
    ]
    filtered_raw = [(timestamp, nodes) for timestamp, nodes in filtered_raw if len(set(nodes)) >= 2]
    raw_nodes = sorted({node for _, nodes in filtered_raw for node in nodes})
    if len(raw_nodes) < 50:
        raise ValueError(f"{dataset.slug}: fewer than 50 retained nodes ({len(raw_nodes)})")
    node_map = {node: idx for idx, node in enumerate(raw_nodes)}
    mapped_events = [(timestamp, tuple(node_map[node] for node in nodes)) for timestamp, nodes in filtered_raw]
    block_count = max(4, min(target_blocks, len(mapped_events)))
    chunks = np.array_split(np.arange(len(mapped_events)), block_count)
    rng = np.random.default_rng(seed)
    rows: list[dict[str, int]] = []
    stats_rows: list[dict[str, float | int]] = []
    expanded_edges = 0
    oversized_edges = 0
    total_candidate_edges = 0
    node_cols = [f"node_{idx}" for idx in range(edge_size)]

    for block, indices in enumerate(chunks):
        block_events = [mapped_events[int(idx)] for idx in indices]
        block_activity = [node for node, _ in Counter(node for _, nodes in block_events for node in nodes).most_common()]
        pool = same_block_expansion_pool(block_events)
        candidates: list[tuple[int, ...]] = []
        for event_idx, (_, nodes) in enumerate(block_events):
            local_rng = np.random.default_rng(seed + block * 100000 + event_idx)
            edge, expanded, oversized = normalize_event_to_edge(nodes, pool, block_activity, edge_size, local_rng)
            if len(edge) == edge_size:
                candidates.append(edge)
                expanded_edges += int(expanded)
                oversized_edges += int(oversized)
        unique_candidates = sorted(set(candidates))
        total_candidate_edges += len(unique_candidates)
        if not unique_candidates:
            raise ValueError(f"{dataset.slug}: empty candidate edge set in block {block}")
        replace = len(unique_candidates) < n_edges
        selected = [
            unique_candidates[int(idx)]
            for idx in rng.choice(len(unique_candidates), size=n_edges, replace=replace)
        ]
        for slot, edge in enumerate(selected):
            row = {"block": block, "slot": slot}
            row.update({col: int(node) for col, node in zip(node_cols, edge)})
            rows.append(row)
        stats_rows.append(
            {
                "block": block,
                "input_events": int(len(block_events)),
                "candidate_edges": int(len(unique_candidates)),
                "selected_edges": int(len(selected)),
                "sampled_with_replacement": int(replace),
                "time_min": int(min(timestamp for timestamp, _ in block_events)),
                "time_max": int(max(timestamp for timestamp, _ in block_events)),
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    sequence_path = out_dir / "real_sequence_edges.csv"
    stats_path = out_dir / "real_sequence_block_stats.csv"
    node_map_path = out_dir / "node_map.csv"
    metadata_path = out_dir / "real_sequence_metadata.json"

    with sequence_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["block", "slot", *node_cols])
        writer.writeheader()
        writer.writerows(rows)
    with stats_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(stats_rows[0].keys()))
        writer.writeheader()
        writer.writerows(stats_rows)
    with node_map_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["raw_node_id", "node_id"])
        writer.writeheader()
        for raw, node_id in node_map.items():
            writer.writerow({"raw_node_id": raw, "node_id": node_id})

    metadata = {
        "dataset_name": dataset.slug,
        "family": dataset.family,
        "source_url": dataset.source_url,
        "n": len(raw_nodes),
        "edge_size": edge_size,
        "n_edges": n_edges,
        "blocks": block_count,
        "input_events": len(events),
        "retained_events": len(mapped_events),
        "n_cap": n_cap,
        "target_blocks": target_blocks,
        "sequence_path": str(sequence_path.resolve()),
        "stats_path": str(stats_path.resolve()),
        "node_map_path": str(node_map_path.resolve()),
        "expansion_rate": expanded_edges / max(len(mapped_events), 1),
        "oversize_sample_rate": oversized_edges / max(len(mapped_events), 1),
        "mean_candidate_edges_per_block": total_candidate_edges / max(block_count, 1),
        "seed": seed,
        "construction": (
            "Temporal higher-order events are sorted by time, capped to the most active nodes, "
            "converted to fixed-size h=6 hyperedges, and sampled to m=33 edges per block."
        ),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def build_smoke_events(slug: str) -> list[tuple[int, tuple[str, ...]]]:
    rng = np.random.default_rng(SEED + len(slug))
    events: list[tuple[int, tuple[str, ...]]] = []
    nodes = [f"{slug}_node_{idx}" for idx in range(60)]
    for idx in range(160):
        size = int(rng.integers(3, 10))
        event_nodes = tuple(str(node) for node in rng.choice(nodes, size=size, replace=False))
        events.append((idx, event_nodes))
    return events


def prepare_dataset(dataset: ExternalDataset, args: argparse.Namespace) -> dict[str, object]:
    raw_dir = Path(args.raw_root) / dataset.slug
    prepared_dir = Path(args.out_root) / dataset.slug / "prepared_h6_m33_external_s26"
    if args.smoke:
        return write_fixed_sequence(
            build_smoke_events(dataset.slug),
            dataset,
            prepared_dir,
            edge_size=EDGE_SIZE,
            n_edges=N_EDGES,
            n_cap=N_CAP,
            target_blocks=4,
            seed=SEED,
        )
    existing = (
        list(raw_dir.rglob("*-nverts.txt"))
        + list(raw_dir.rglob("*.json"))
        + list(raw_dir.rglob("*.csv"))
        + list(raw_dir.rglob("*.csv.gz"))
        + list(raw_dir.rglob("*.tsv"))
        + list(raw_dir.rglob("*.txt"))
        + list(raw_dir.rglob("*.txt.gz"))
    )
    if not existing and args.download:
        downloaded = download_dataset_files(dataset, raw_dir)
        raw_dir = extract_downloaded_files(downloaded, raw_dir / "extracted")
    if dataset.parser == "benson_tar":
        try:
            events = read_benson_events(raw_dir)
        except FileNotFoundError:
            json_files = sorted(raw_dir.rglob("*.json"))
            if not json_files:
                raise
            events = read_hgx_json_events(json_files[0])
    elif dataset.parser == "contact_csv":
        events = read_contact_csv_events(raw_dir)
    else:
        raise ValueError(f"Unknown parser: {dataset.parser}")
    return write_fixed_sequence(
        events,
        dataset,
        prepared_dir,
        edge_size=EDGE_SIZE,
        n_edges=N_EDGES,
        n_cap=N_CAP,
        target_blocks=TARGET_BLOCKS,
        seed=SEED,
    )


def selected_datasets(names: str, smoke: bool) -> list[ExternalDataset]:
    if smoke:
        return DATASETS[:2]
    wanted = {name.strip() for name in names.split(",") if name.strip()}
    if not wanted:
        return PRIMARY_DATASETS
    lookup = {dataset.slug: dataset for dataset in DATASETS}
    missing = sorted(wanted - set(lookup))
    if missing:
        raise KeyError(f"Unknown S26 dataset slug(s): {', '.join(missing)}")
    return [lookup[name] for name in wanted]


def write_manifest(out_root: Path, rows: list[dict[str, object]], failures: list[dict[str, str]]) -> Path:
    manifest = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "prepared_datasets": rows,
        "failures": failures,
        "minimum_non_sociopatterns_required": 3,
    }
    path = out_root / "s26_external_real_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare S26 external real temporal hypergraph datasets.")
    parser.add_argument("--out-root", default=str(DEFAULT_OUT_ROOT))
    parser.add_argument("--raw-root", default=str(PROJECT / "real_data_external_s26" / "raw"))
    parser.add_argument("--datasets", default="")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--plan-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    datasets = selected_datasets(args.datasets, args.smoke)
    if args.plan_only:
        print("S26 external real data preparation")
        print(f"Output root: {args.out_root}")
        print(f"Raw root: {args.raw_root}")
        print("Datasets:")
        for dataset in datasets:
            print(f"- {dataset.slug}: {dataset.source_url}")
        return
    out_root = Path(args.out_root).expanduser()
    out_root.mkdir(parents=True, exist_ok=True)
    prepared: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for dataset in datasets:
        try:
            metadata = prepare_dataset(dataset, args)
            prepared.append(metadata)
            print(f"[prepared] {dataset.slug} -> {metadata['sequence_path']}", flush=True)
        except Exception as exc:  # noqa: BLE001 - keep preparing other datasets and record blockers.
            failures.append({"dataset": dataset.slug, "error": str(exc)})
            print(f"[failed] {dataset.slug}: {exc}", flush=True)
    if not args.smoke and not args.datasets and len(prepared) < 5:
        for dataset in FALLBACK_DATASETS:
            if len(prepared) >= 5:
                break
            try:
                metadata = prepare_dataset(dataset, args)
                prepared.append(metadata)
                print(f"[prepared:fallback] {dataset.slug} -> {metadata['sequence_path']}", flush=True)
            except Exception as exc:  # noqa: BLE001 - record fallback blocker too.
                failures.append({"dataset": dataset.slug, "error": str(exc)})
                print(f"[failed:fallback] {dataset.slug}: {exc}", flush=True)
    manifest = write_manifest(out_root, prepared, failures)
    if not args.smoke and len(prepared) < 3:
        raise SystemExit(f"S26 blocker: only {len(prepared)} external datasets prepared; need at least 3")
    print(f"Manifest: {manifest}", flush=True)


if __name__ == "__main__":
    main()
