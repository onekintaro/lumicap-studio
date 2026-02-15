from __future__ import annotations

from typing import Any, Dict
from core.utils import new_gid

def upgrade_lcap_v1_inplace(payload: Dict[str, Any]) -> bool:
    """
    Patch old lcap v1 payloads in-place (e.g. missing group.id).
    Returns True if payload was changed.
    """
    dirty = False

    settings = payload.get("settings", {}) or {}
    disable_out = settings.get("disable_highlight_at_out", True)

    groups = payload.get("groups", []) or []
    for g in groups:
        # Add missing id
        if not g.get("id"):
            g["id"] = new_gid()
            dirty = True

        # Ensure steps list exists
        if g.get("steps") is None:
            g["steps"] = []
            dirty = True
        if "steps" not in g:
            g["steps"] = []
            dirty = True

        # Ensure highlight-off step at out (if desired)
        if disable_out:
          out_t = g.get("out", None)
          if out_t is not None:
            steps = g["steps"]
            need = True
            if steps:
              last = steps[-1]
              if isinstance(last, dict):
                try:
                  need = not (
                    abs(float(last.get("t", -9999.0)) - float(out_t)) < 1e-6
                    and int(last.get("start", 1)) == 0
                    and int(last.get("end", 1)) == 0
                  )
                except Exception:
                  need = True
            if need:
              steps.append({"t": out_t, "start": 0, "end": 0, "label": ""})
              dirty = True

    return dirty