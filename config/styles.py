# config/styles.py

BASE_STYLES = ["Normal", "Strong", "Weak", "Highlight"]
CUSTOM_STYLES = []

ALPHABET_STYLES = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
NUMBER_STYLES = [f"Style {i}" for i in range(1, 9)]
PROTECTED_STYLES = ["!"]

# Base Extra Styles:
BASE_EXTRA_STYLES = ["Verse", "PreChorus", "Chorus", "Emphasis", "Bridge", "Spoken"]

# Options
ENABLE_BASE_STYLES = True
ENABLE_CUSTOM_STYLES = True
ENABLE_ALPHABET_STYLES = False
ENABLE_NUMBER_STYLES = False
ENABLE_PROTECTED_STYLES = True

ENABLE_BASE_EXTRA_STYLES = True
ENABLE_BASE_EXTRA_STYLES_NUMBERED = True
BASE_EXTRA_STYLES_NUMBERED_COUNT = 3  # ergibt: "Chorus", "Chorus 1", "Chorus 2", "Chorus 3"


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def build_styles() -> list[str]:
    styles: list[str] = []

    # Protected meist ganz vorne sinnvoll (UI/Engine erkennt's schneller)
    if ENABLE_PROTECTED_STYLES:
        styles += PROTECTED_STYLES

    if ENABLE_BASE_STYLES:
        styles += BASE_STYLES

    if ENABLE_BASE_EXTRA_STYLES:
        styles += BASE_EXTRA_STYLES

        if ENABLE_BASE_EXTRA_STYLES_NUMBERED and BASE_EXTRA_STYLES_NUMBERED_COUNT > 0:
            for s in BASE_EXTRA_STYLES:
                for i in range(1, BASE_EXTRA_STYLES_NUMBERED_COUNT + 1):
                    styles.append(f"{s} {i}")

    if ENABLE_CUSTOM_STYLES:
        styles += CUSTOM_STYLES

    if ENABLE_ALPHABET_STYLES:
        styles += ALPHABET_STYLES

    if ENABLE_NUMBER_STYLES:
        styles += NUMBER_STYLES

    return _dedupe_keep_order(styles)


STYLES = build_styles()