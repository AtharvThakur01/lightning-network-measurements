from __future__ import annotations

import json
from pathlib import Path

import networkx as nx
import pandas as pd

from .io import load_graph, snapshot_date


def attach_channel_implementations(channels: pd.DataFrame, nodes: pd.DataFrame) -> pd.DataFrame:
    labels = nodes[["pub_key", "implementation"]]
    out = channels.merge(labels.rename(columns={"pub_key": "node1_pub", "implementation": "node1_implementation"}), on="node1_pub", how="left")
    out = out.merge(labels.rename(columns={"pub_key": "node2_pub", "implementation": "node2_implementation"}), on="node2_pub", how="left")
    out["node1_implementation"] = out["node1_implementation"].fillna("unknown")
    out["node2_implementation"] = out["node2_implementation"].fillna("unknown")
    out["implementation_pair"] = out.apply(
        lambda r: "-".join(sorted([r["node1_implementation"], r["node2_implementation"]])),
        axis=1,
    )
    return out


def channel_pair_distribution(channels: pd.DataFrame) -> pd.DataFrame:
    grouped = channels.groupby("implementation_pair", dropna=False).agg(
        channel_count=("channel_id", "count"),
        capacity_sat=("capacity_sat", "sum"),
        median_capacity_sat=("capacity_sat", "median"),
    )
    out = grouped.reset_index()
    out["channel_share"] = out["channel_count"] / out["channel_count"].sum()
    out["capacity_share"] = out["capacity_sat"] / out["capacity_sat"].sum()
    return out.sort_values("channel_count", ascending=False)


def capacity_distribution(channels: pd.DataFrame) -> pd.DataFrame:
    caps = channels["capacity_sat"].dropna()
    bins = [0, 100_000, 500_000, 1_000_000, 5_000_000, 10_000_000, 50_000_000, float("inf")]
    labels = ["0-100k", "100k-500k", "500k-1m", "1m-5m", "5m-10m", "10m-50m", "50m+"]
    buckets = pd.cut(caps, bins=bins, labels=labels, include_lowest=True).value_counts().sort_index()
    summary = caps.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9, 0.99]).to_frame("capacity_sat").reset_index(names="stat")
    bucket_df = buckets.reset_index()
    bucket_df.columns = ["stat", "capacity_sat"]
    bucket_df["stat"] = "bucket_" + bucket_df["stat"].astype(str)
    return pd.concat([summary, bucket_df], ignore_index=True)


def build_graph(channels: pd.DataFrame) -> nx.MultiGraph:
    graph = nx.MultiGraph()
    for row in channels.itertuples(index=False):
        if not row.node1_pub or not row.node2_pub:
            continue
        graph.add_edge(row.node1_pub, row.node2_pub, key=row.channel_id, channel_id=row.channel_id, capacity_sat=row.capacity_sat or 0)
    return graph


def graph_outputs(graph: nx.MultiGraph, exact_path_metrics: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    degree = pd.DataFrame({"pub_key": dict(graph.degree()).keys(), "degree": dict(graph.degree()).values()})
    degree_distribution = degree["degree"].value_counts().sort_index().reset_index()
    degree_distribution.columns = ["degree", "node_count"]

    if graph.number_of_nodes() == 0:
        return degree_distribution, pd.DataFrame(), {"node_count": 0, "public_channel_count": 0}

    simple_graph = nx.Graph(graph)
    largest_nodes = max(nx.connected_components(simple_graph), key=len)
    largest = simple_graph.subgraph(largest_nodes).copy()
    betweenness = nx.betweenness_centrality(largest, k=min(1000, largest.number_of_nodes()), seed=42) if largest.number_of_nodes() > 1 else {}
    closeness = nx.closeness_centrality(largest) if largest.number_of_nodes() > 1 else {}
    try:
        eigenvector = nx.eigenvector_centrality(largest, max_iter=500)
    except nx.NetworkXException:
        eigenvector = {}

    centrality = pd.DataFrame(
        {
            "pub_key": list(largest.nodes()),
            "degree": [graph.degree(n) for n in largest.nodes()],
            "betweenness": [betweenness.get(n, 0.0) for n in largest.nodes()],
            "closeness": [closeness.get(n, 0.0) for n in largest.nodes()],
            "eigenvector": [eigenvector.get(n, 0.0) for n in largest.nodes()],
        }
    ).sort_values("degree", ascending=False)

    metrics = {
        "node_count": graph.number_of_nodes(),
        "public_channel_count": graph.number_of_edges(),
        "unique_node_pair_count": simple_graph.number_of_edges(),
        "simple_graph_density": nx.density(simple_graph),
        "component_count": nx.number_connected_components(simple_graph),
        "largest_component_node_count": largest.number_of_nodes(),
        "largest_component_channel_count": largest.number_of_edges(),
        "average_degree": sum(dict(graph.degree()).values()) / graph.number_of_nodes(),
        "average_clustering": nx.average_clustering(simple_graph),
    }
    if largest.number_of_nodes() > 1:
        metrics["largest_component_diameter_approx"] = nx.approximation.diameter(largest)
        if exact_path_metrics or largest.number_of_nodes() <= 5000:
            metrics["largest_component_average_shortest_path_length"] = nx.average_shortest_path_length(largest)
        else:
            metrics["largest_component_average_shortest_path_length"] = "skipped; rerun with --exact-path-metrics"
    return degree_distribution, centrality, metrics


def geographic_distribution(nodes: pd.DataFrame) -> pd.DataFrame:
    for col in ["country_code", "country_name", "continent"]:
        if col not in nodes.columns:
            nodes[col] = "unknown"
    geo = nodes.fillna({"country_code": "unknown", "country_name": "unknown", "continent": "unknown"})
    grouped = geo.groupby(["continent", "country_code", "country_name", "implementation"], dropna=False).size().reset_index(name="node_count")
    grouped["node_share"] = grouped["node_count"] / grouped["node_count"].sum()
    return grouped.sort_values("node_count", ascending=False)


def channel_lifetimes(history_dir: Path | None, current_channels: pd.DataFrame, current_block_height: int | None) -> pd.DataFrame:
    if history_dir and history_dir.exists():
        rows = []
        for path in sorted(history_dir.glob("*.json")):
            date = snapshot_date(path)
            if date is None:
                continue
            _, channels, _ = load_graph(path)
            rows.extend({"channel_id": cid, "snapshot_date": date} for cid in channels["channel_id"].dropna().astype(str))
        if rows:
            seen = pd.DataFrame(rows)
            out = seen.groupby("channel_id").agg(
                first_seen=("snapshot_date", "min"),
                last_seen=("snapshot_date", "max"),
                observed_snapshot_count=("snapshot_date", "nunique"),
            ).reset_index()
            out["lifetime_type"] = "observed_snapshot_window"
            return out

    out = current_channels[["channel_id", "short_channel_block"]].copy()
    if current_block_height is not None:
        out["age_blocks"] = current_block_height - out["short_channel_block"]
    out["lifetime_type"] = "current_channel_age_proxy"
    return out


def write_json(data: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
