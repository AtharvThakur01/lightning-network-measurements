from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def _save(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def plot_implementation_distribution(df: pd.DataFrame, out_dir: Path) -> None:
    plt.figure(figsize=(7, 4))
    plt.bar(df["implementation"], df["node_count"])
    plt.ylabel("Nodes")
    plt.xlabel("Implementation")
    plt.title("Node implementation distribution")
    _save(out_dir / "implementation_distribution.png")


def plot_channel_pairs(df: pd.DataFrame, out_dir: Path) -> None:
    top = df.head(12)
    plt.figure(figsize=(9, 5))
    plt.barh(top["implementation_pair"], top["channel_count"])
    plt.xlabel("Channels")
    plt.title("Channel implementation-pair distribution")
    plt.gca().invert_yaxis()
    _save(out_dir / "channel_pair_distribution.png")


def plot_capacity_hist(channels: pd.DataFrame, out_dir: Path) -> None:
    caps = channels["capacity_sat"].dropna()
    if caps.empty:
        return
    plt.figure(figsize=(8, 5))
    plt.hist(caps, bins=50, log=True)
    plt.xlabel("Capacity (sat)")
    plt.ylabel("Channels (log)")
    plt.title("Channel capacity distribution")
    _save(out_dir / "capacity_distribution.png")


def plot_degree_distribution(df: pd.DataFrame, out_dir: Path) -> None:
    plt.figure(figsize=(8, 5))
    plt.loglog(df["degree"], df["node_count"], marker="o", linestyle="")
    plt.xlabel("Degree")
    plt.ylabel("Nodes")
    plt.title("Degree distribution")
    _save(out_dir / "degree_distribution.png")

