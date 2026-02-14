import json
from core.models import Group

def build_lcap_payload(
    groups: list[Group],
    source_path: str | None = None,
    settings: dict | None = None,
    meta: dict | None = None,
) -> dict:
    return {
    "format": "lcap",
    "version": 1,
    "source": source_path,
    "meta": meta or {"draft": True},
    "settings": settings or {},
    "groups": [
        {
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

def export_lcap(
    groups: list[Group],
    path: str,
    source_path: str | None = None,
    settings: dict | None = None,
    meta: dict | None = None,
) -> None:
    payload = build_lcap_payload(groups, source_path, settings=settings, meta=meta)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)