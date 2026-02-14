# core/merge.py
import re
from typing import List, Tuple
from core.models import Group, Step

def _norm(s: str) -> str:
    return (s or "").replace("’", "'").strip()

def _norm_lower(s: str) -> str:
    return _norm(s).lower()

def _find_span(text: str, label: str, start_at: int = 0) -> Tuple[int, int] | None:
    t = _norm_lower(text)
    l = _norm_lower(label)
    idx = t.find(l, start_at)
    if idx < 0:
        return None
    return idx, idx + len(l)

def merge_groups_smart(groups: List[Group], result_text: str, keep_style: str | None = None) -> Group:
    """
    Merge multiple Groups into one.
    - result_text: final text (from dialog; can be edited)
    - Steps are re-mapped by searching label spans in result_text (stable / robust).
    """
    if len(groups) < 2:
        raise ValueError("Need at least 2 groups to merge")

    groups_sorted = sorted(groups, key=lambda g: g.t_in)

    t_in = min(g.t_in for g in groups_sorted)
    t_out = max(g.t_out for g in groups_sorted)

    # Style: default first (or forced by caller)
    style = keep_style or groups_sorted[0].style

    # Key: recompute from text? (caller can overwrite after if needed)
    key = result_text

    # Collect label-steps (ignore empty reset steps; we'll add one at end)
    label_steps: List[Step] = []
    for g in groups_sorted:
        for s in g.steps:
            if s.label:
                label_steps.append(s)

    label_steps.sort(key=lambda s: s.t)

    # Re-map by label search in result_text
    mapped: List[Step] = []
    cursor = 0
    for s in label_steps:
        span = _find_span(result_text, s.label, start_at=cursor)
        if span is None:
            # fallback: clamp old indices into new text
            st = max(0, min(len(result_text), int(s.start)))
            en = max(0, min(len(result_text), int(s.end)))
        else:
            st, en = span
            cursor = en  # avoid matching the same word earlier again
        mapped.append(Step(t=float(s.t), start=st, end=en, label=s.label))

    # Add single reset step at out
    mapped.append(Step(t=float(t_out), start=0, end=0, label=""))

    return Group(
        key=key,
        style=style,
        text=result_text,
        t_in=float(t_in),
        t_out=float(t_out),
        steps=mapped,
    )