import re
import uuid


ZERO_WIDTH = ["\u200B", "\u200C", "\u200D", "\uFEFF"]

def normalize_plain_for_key(s: str, normalize_punct_spacing: bool = True) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    for ch in ZERO_WIDTH:
        s = s.replace(ch, "")
    s = re.sub(r"\s+", " ", s).strip()
    if normalize_punct_spacing:
        s = re.sub(r"\s+([.,!?;:])", r"\1", s)
    return s

def first_two_words(text: str) -> str:
    t = " ".join(text.replace("\r", " ").split())
    parts = t.split(" ")
    return " ".join(parts[:2]) if t else "Subtitle"

def new_gid() -> str:
    return "g_" + uuid.uuid4().hex