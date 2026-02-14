# core/lcap/export.py

from __future__ import annotations

from core.models import Group
from core.lcap.writer import save_lcap


def export_release_lcap(
    groups: list[Group],
    path: str,
    source_path: str | None = None,
    settings: dict | None = None,
    meta: dict | None = None,
) -> None:
    # draft explizit false setzen
    meta_out = dict(meta or {})
    meta_out["draft"] = False

    save_lcap(
        groups,
        path,
        source_path=source_path,
        settings=settings,
        meta=meta_out,
    )