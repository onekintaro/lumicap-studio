# core/lcap/writer.py

from __future__ import annotations

import json
from core.models import Group
from core.lcap.spec import LCAP_FORMAT, LCAP_VERSION, DEFAULT_META
from core.utils import new_gid


def build_lcap_payload(
    groups: list[Group],
    source_path: str | None = None,
    settings: dict | None = None,
    meta: dict | None = None,
) -> dict:
    return {
        "format": LCAP_FORMAT,
        "version": LCAP_VERSION,
        "source": source_path,
        "meta": (DEFAULT_META | (meta or {})),
        "settings": settings or {},
        "groups": [
            {
                "id": g.id or new_gid(),
                "key": getattr(g, "key", None),
                "style": g.style,
                "text": g.text,
                "in": g.t_in,
                "out": g.t_out,
                "steps": [
                    {"t": s.t, "start": s.start, "end": s.end, "label": s.label}
                    for s in g.steps
                ],
            }
            for g in groups
        ],
    }


def save_lcap(
    groups: list[Group],
    path: str,
    source_path: str | None = None,
    settings: dict | None = None,
    meta: dict | None = None,
) -> None:
    payload = build_lcap_payload(groups, source_path, settings=settings, meta=meta)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)