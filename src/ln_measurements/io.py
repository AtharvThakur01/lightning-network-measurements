from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


SNAPSHOT_DATE_RE = re.compile(r"(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)")


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _policy(edge: dict[str, Any], key: str, pub_key: str) -> dict[str, Any]:
    policy = edge.get(key) or {}
    return {
        "channel_id": str(edge.get("channel_id") or edge.get("chan_id") or edge.get("short_channel_id") or ""),
        "pub_key": pub_key,
        "cltv_expiry_delta": _to_int(policy.get("time_lock_delta") or policy.get("cltv_expiry_delta")),
        "htlc_minimum_msat": _to_int(policy.get("min_htlc") or policy.get("htlc_minimum_msat")),
        "fee_base_msat": _to_int(policy.get("fee_base_msat") or policy.get("base_fee_millisatoshi")),
        "fee_proportional_millionths": _to_int(
            policy.get("fee_rate_milli_msat") or policy.get("fee_proportional_millionths") or policy.get("fee_per_millionth")
        ),
        "disabled": bool(policy.get("disabled", False)),
        "last_update": _to_int(policy.get("last_update") or edge.get("last_update")),
    }


def load_graph(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw = _read_json(path)
    node_rows: list[dict[str, Any]] = []
    channel_rows: list[dict[str, Any]] = []
    policy_rows: list[dict[str, Any]] = []

    for node in raw.get("nodes", []):
        pub_key = node.get("pub_key") or node.get("nodeid") or node.get("id")
        addresses = node.get("addresses") or []
        node_rows.append(
            {
                "pub_key": pub_key,
                "alias": node.get("alias", ""),
                "color": node.get("color", ""),
                "last_update": _to_int(node.get("last_update")),
                "addresses": json.dumps(addresses, ensure_ascii=True),
                "first_address": _first_address(addresses),
            }
        )

    for edge in raw.get("edges", raw.get("channels", [])):
        channel_id = str(edge.get("channel_id") or edge.get("chan_id") or edge.get("short_channel_id") or "")
        node1 = edge.get("node1_pub") or edge.get("source") or edge.get("node1")
        node2 = edge.get("node2_pub") or edge.get("destination") or edge.get("node2")
        channel_rows.append(
            {
                "channel_id": channel_id,
                "chan_point": edge.get("chan_point", ""),
                "node1_pub": node1,
                "node2_pub": node2,
                "capacity_sat": _to_int(edge.get("capacity") or edge.get("satoshis")),
                "last_update": _to_int(edge.get("last_update")),
                "short_channel_block": short_channel_block(channel_id),
            }
        )
        policy_rows.append(_policy(edge, "node1_policy", node1))
        policy_rows.append(_policy(edge, "node2_policy", node2))

    nodes = pd.DataFrame(node_rows).drop_duplicates("pub_key")
    channels = pd.DataFrame(channel_rows).drop_duplicates("channel_id")
    policies = pd.DataFrame(policy_rows)
    return nodes, channels, policies


def _read_json(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "utf-16-le"):
        try:
            return json.loads(data.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    raise ValueError(f"Could not decode JSON file {path}; expected UTF-8 or UTF-16 JSON")


def _first_address(addresses: list[Any]) -> str:
    if not addresses:
        return ""
    first = addresses[0]
    if isinstance(first, dict):
        return str(first.get("addr") or first.get("address") or "")
    return str(first)


def short_channel_block(channel_id: str) -> int | None:
    if not channel_id:
        return None
    if "x" in channel_id:
        return _to_int(channel_id.split("x", 1)[0])
    numeric = _to_int(channel_id)
    if numeric is None:
        return None
    return numeric >> 40


def snapshot_date(path: Path) -> str | None:
    match = SNAPSHOT_DATE_RE.search(path.name)
    if not match:
        return None
    return "-".join(match.groups())


def load_geography(path: Path | None) -> pd.DataFrame:
    if path is None:
        return pd.DataFrame(columns=["pub_key", "country_code", "country_name", "continent", "city", "latitude", "longitude"])
    geo = pd.read_csv(path)
    if "pub_key" not in geo.columns:
        raise ValueError("node geography CSV must include a pub_key column")
    return geo


def write_table(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
