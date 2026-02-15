from __future__ import annotations

import json
from typing import Tuple, List

from core.lcap.validator import validate_lcap
from core.models import Group, Step
from core.lcap.upgrade import upgrade_lcap_v1_inplace


def load_lcap(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # upgrade older payloads before validating
    upgraded = upgrade_lcap_v1_inplace(payload)

    validate_lcap(payload)
    payload["_upgraded"] = upgraded  # optional flag for UI/is_dirty decision
    return payload


def groups_from_payload(payload: dict) -> List[Group]:
    groups: List[Group] = []

    for g in payload.get("groups", []):
        steps = [Step(**s) for s in g.get("steps", [])]

        groups.append(
            Group(
                id=g.get("id") or "",
                key=g.get("key", "") or "",
                style=g.get("style", "Normal"),
                text=g.get("text", ""),
                t_in=g.get("in", 0.0),
                t_out=g.get("out", 0.0),
                steps=steps,
            )
        )

    return groups


def load_lcap_project(
    path: str,
) -> Tuple[List[Group], dict, dict, str | None]:
    """
    High-level project loader.
    Returns:
        groups
        meta
        settings
        source_path
    """
    payload = load_lcap(path)

    return (
        groups_from_payload(payload),
        payload.get("meta", {}),
        payload.get("settings", {}),
        payload.get("source"),
    )