from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd


IMPLEMENTATIONS = ("lnd", "core-lightning", "eclair")


def _clean_color(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    color = str(value).strip().lower()
    return color if color.startswith("#") else f"#{color}"


def _mode(series: pd.Series) -> Any:
    values = [v for v in series.dropna().tolist() if v != ""]
    if not values:
        return None
    return Counter(values).most_common(1)[0][0]


def _score_policy(cltv: Any, htlc_min: Any, fee_rate: Any) -> dict[str, int]:
    scores = dict.fromkeys(IMPLEMENTATIONS, 0)

    if cltv in (40, 144):
        scores["lnd"] += 1
    if cltv == 14:
        scores["core-lightning"] += 1
    if cltv == 144:
        scores["eclair"] += 1

    if htlc_min == 1000:
        scores["lnd"] += 1
        scores["core-lightning"] += 1
    if htlc_min == 1:
        scores["eclair"] += 1

    if fee_rate == 1:
        scores["lnd"] += 1
    if fee_rate == 10:
        scores["core-lightning"] += 1
    if fee_rate == 100:
        scores["eclair"] += 1

    return scores


def classify_nodes(nodes: pd.DataFrame, policies: pd.DataFrame) -> pd.DataFrame:
    """Infer LN implementation from node metadata and most-frequent policy defaults."""
    policy_modes = (
        policies.groupby("pub_key", dropna=False)
        .agg(
            cltv_expiry_delta=("cltv_expiry_delta", _mode),
            htlc_minimum_msat=("htlc_minimum_msat", _mode),
            fee_proportional_millionths=("fee_proportional_millionths", _mode),
        )
        .reset_index()
    )
    out = nodes.merge(policy_modes, on="pub_key", how="left")

    labels: list[str] = []
    confidences: list[float] = []
    score_rows: list[dict[str, int]] = []

    for row in out.itertuples(index=False):
        scores = dict.fromkeys(IMPLEMENTATIONS, 0)
        color = _clean_color(getattr(row, "color", ""))
        pub_key = str(getattr(row, "pub_key"))

        if color == "#3399ff":
            scores["lnd"] += 1
        if color == "#49daaa":
            scores["eclair"] += 1
        if color == f"#{pub_key[:6].lower()}":
            scores["core-lightning"] += 1

        policy_scores = _score_policy(
            getattr(row, "cltv_expiry_delta", None),
            getattr(row, "htlc_minimum_msat", None),
            getattr(row, "fee_proportional_millionths", None),
        )
        for impl, score in policy_scores.items():
            scores[impl] += score

        top_score = max(scores.values())
        winners = [impl for impl, score in scores.items() if score == top_score]
        label = winners[0] if top_score > 0 and len(winners) == 1 else "unknown"
        labels.append(label)
        confidences.append(0.0 if top_score == 0 else round(top_score / max(sum(scores.values()), 1), 4))
        score_rows.append({f"score_{impl}": score for impl, score in scores.items()})

    return pd.concat(
        [
            out,
            pd.DataFrame({"implementation": labels, "implementation_confidence": confidences}),
            pd.DataFrame(score_rows),
        ],
        axis=1,
    )


def implementation_distribution(nodes: pd.DataFrame) -> pd.DataFrame:
    counts = nodes["implementation"].fillna("unknown").value_counts(dropna=False).rename_axis("implementation")
    df = counts.reset_index(name="node_count")
    df["node_share"] = df["node_count"] / df["node_count"].sum()
    return df

