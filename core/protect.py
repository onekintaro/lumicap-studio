# core/protect.py
from core.models import Group

def toggle_protect(g: Group, fallback_style: str = "Normal") -> None:
    if g.style != "!":
        g._style_before_protect = g.style  # dynamisches Feld ok in Py
        g.style = "!"
    else:
        g.style = getattr(g, "_style_before_protect", fallback_style)
        if hasattr(g, "_style_before_protect"):
            delattr(g, "_style_before_protect")