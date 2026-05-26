from __future__ import annotations

import argparse
from pathlib import Path

from .classify import classify_nodes, implementation_distribution
from .io import load_geography, load_graph, write_table
from .metrics import (
    attach_channel_implementations,
    build_graph,
    capacity_distribution,
    channel_lifetimes,
    channel_pair_distribution,
    geographic_distribution,
    graph_outputs,
    write_json,
)
from .plots import (
    plot_capacity_hist,
    plot_channel_pairs,
    plot_degree_distribution,
    plot_implementation_distribution,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh Lightning Network topology measurements from a graph snapshot.")
    parser.add_argument("--graph", required=True, type=Path, help="Path to LND describegraph JSON")
    parser.add_argument("--out-dir", required=True, type=Path, help="Directory for CSV/JSON/plot outputs")
    parser.add_argument("--node-geo-csv", type=Path, help="Optional pub_key-keyed node geolocation CSV")
    parser.add_argument("--history-dir", type=Path, help="Optional directory of dated historical graph snapshots")
    parser.add_argument("--current-block-height", type=int, help="Current Bitcoin height for channel age proxies")
    parser.add_argument("--exact-path-metrics", action="store_true", help="Compute exact average shortest path on large components")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    nodes, channels, policies = load_graph(args.graph)
    classified_nodes = classify_nodes(nodes, policies)

    geo = load_geography(args.node_geo_csv)
    classified_nodes = classified_nodes.merge(geo, on="pub_key", how="left")

    channels = attach_channel_implementations(channels, classified_nodes)
    graph = build_graph(channels)
    degree_dist, centrality, graph_metrics = graph_outputs(graph, exact_path_metrics=args.exact_path_metrics)
    impl_dist = implementation_distribution(classified_nodes)
    geo_dist = geographic_distribution(classified_nodes)
    pair_dist = channel_pair_distribution(channels)
    cap_dist = capacity_distribution(channels)
    lifetimes = channel_lifetimes(args.history_dir, channels, args.current_block_height)

    write_table(classified_nodes, args.out_dir / "nodes_classified.csv")
    write_table(impl_dist, args.out_dir / "implementation_distribution.csv")
    write_table(geo_dist, args.out_dir / "geographic_distribution.csv")
    write_table(channels, args.out_dir / "channels.csv")
    write_table(pair_dist, args.out_dir / "channel_pair_distribution.csv")
    write_table(cap_dist, args.out_dir / "capacity_distribution.csv")
    write_table(degree_dist, args.out_dir / "degree_distribution.csv")
    write_table(centrality, args.out_dir / "centrality.csv")
    write_table(lifetimes, args.out_dir / "channel_lifetimes.csv")
    write_json(graph_metrics, args.out_dir / "graph_metrics.json")

    plot_dir = args.out_dir / "plots"
    plot_implementation_distribution(impl_dist, plot_dir)
    plot_channel_pairs(pair_dist, plot_dir)
    plot_capacity_hist(channels, plot_dir)
    plot_degree_distribution(degree_dist, plot_dir)

    print(f"Wrote Lightning measurement outputs to {args.out_dir}")


if __name__ == "__main__":
    main()
