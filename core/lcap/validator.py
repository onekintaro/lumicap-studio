# core/lcap/validator.py

from __future__ import annotations

from core.lcap.spec import LCAP_FORMAT, LCAP_VERSION


def validate_lcap(payload: dict) -> None:
    """
    Validate LCAP v1 payload.
    Raises ValueError with a readable message on failure.
    """
    if not isinstance(payload, dict):
        raise ValueError("LCAP must be a JSON object")

    if payload.get("format") != LCAP_FORMAT:
        raise ValueError(f"Invalid format: expected '{LCAP_FORMAT}'")

    version = payload.get("version")
    if version != LCAP_VERSION:
        raise ValueError(f"Unsupported LCAP version: {version}")

    groups = payload.get("groups")
    if not isinstance(groups, list):
        raise ValueError("LCAP must contain a 'groups' array")

    for i, g in enumerate(groups):
        if not isinstance(g, dict):
            raise ValueError(f"Group[{i}] must be an object")

        # required-ish fields
        if "text" not in g or not isinstance(g["text"], str):
            raise ValueError(f"Group[{i}] missing/invalid 'text'")

        if "style" not in g or not isinstance(g["style"], str):
            raise ValueError(f"Group[{i}] missing/invalid 'style'")

        t_in = g.get("in")
        t_out = g.get("out")
        if not isinstance(t_in, (int, float)) or not isinstance(t_out, (int, float)):
            raise ValueError(f"Group[{i}] missing/invalid 'in'/'out' timing")
        if t_in < 0 or t_out < 0:
            raise ValueError(f"Group[{i}] has negative timing")
        if t_in > t_out:
            raise ValueError(f"Group[{i}] has invalid timing (in > out)")

        steps = g.get("steps", [])
        if not isinstance(steps, list):
            raise ValueError(f"Group[{i}].steps must be a list")

        # step bounds (light validation)
        text_len = len(g["text"])
        for j, s in enumerate(steps):
            if not isinstance(s, dict):
                raise ValueError(f"Group[{i}].steps[{j}] must be an object")
            if not isinstance(s.get("t"), (int, float)):
                raise ValueError(f"Group[{i}].steps[{j}] missing/invalid 't'")
            if s["t"] < 0:
                raise ValueError(f"Group[{i}].steps[{j}] has negative time")

            start = s.get("start")
            end = s.get("end")
            if not isinstance(start, int) or not isinstance(end, int):
                raise ValueError(f"Group[{i}].steps[{j}] missing/invalid start/end")
            if start < 0 or end < 0 or start > end:
                raise ValueError(f"Group[{i}].steps[{j}] has invalid range (start/end)")
            if end > text_len:
                raise ValueError(f"Group[{i}].steps[{j}] range exceeds text length")