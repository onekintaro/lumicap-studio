import re
from typing import List, Tuple
from core.models import Entry
from core.utils import normalize_plain_for_key

def tc_to_seconds(tc: str) -> float:
    m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)", tc.strip())
    if not m:
        return 0.0
    h, mi, s, ms = map(int, m.groups())
    return h * 3600 + mi * 60 + s + ms / 1000.0

def extract_u_ranges_and_labels(raw: str) -> Tuple[str, List[Tuple[int, int, str]]]:
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    plain = ""
    ranges: List[Tuple[int, int, str]] = []
    i = 0
    while i < len(raw):
        if raw[i:i+3].lower() == "<u>":
            i += 3
            start = len(plain)
            j = raw.lower().find("</u>", i)
            if j == -1:
                chunk = raw[i:]
                i = len(raw)
            else:
                chunk = raw[i:j]
                i = j + 4
            plain += chunk
            end = len(plain)
            if end > start:
                ranges.append((start, end, chunk))
            continue

        # strip any other <...> tags
        if raw[i] == "<":
            j = raw.find(">", i)
            if j != -1:
                i = j + 1
                continue

        plain += raw[i]
        i += 1

    # AE Source Text prefers \r
    plain = plain.replace("\n", "\r")
    return plain, ranges

def parse_srt(text: str, normalize_punct_spacing: bool = True) -> List[Entry]:
    text = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    blocks = re.split(r"\n\s*\n+", text)
    entries: List[Entry] = []

    for b in blocks:
        lines = b.strip().split("\n")
        if len(lines) < 2:
            continue

        if re.match(r"^\d+$", lines[0].strip()):
            timing = lines[1]
            content = "\n".join(lines[2:])
        else:
            timing = lines[0]
            content = "\n".join(lines[1:])

        m = re.search(r"(\d+:\d+:\d+[,\.]\d+)\s*-->\s*(\d+:\d+:\d+[,\.]\d+)", timing)
        if not m:
            continue

        t_in = tc_to_seconds(m.group(1))
        t_out = tc_to_seconds(m.group(2))

        plain, ranges = extract_u_ranges_and_labels(content.strip())
        key = normalize_plain_for_key(plain.replace("\r", "\n"), normalize_punct_spacing)

        entries.append(Entry(t_in=t_in, t_out=t_out, plain=plain, key=key, ranges=ranges))

    entries.sort(key=lambda e: e.t_in)
    return entries