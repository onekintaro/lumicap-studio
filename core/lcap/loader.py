# core/lcap/loader.py

from __future__ import annotations

import json
from core.lcap.validator import validate_lcap


def load_lcap(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    validate_lcap(payload)
    return payload