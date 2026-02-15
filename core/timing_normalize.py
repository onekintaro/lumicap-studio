# core/timing_normalize.py
from core.models import Group

EPS = 0.001  # 1ms safety
TIMING_NO_OVERLAPS = True         # niemals Overlaps erlauben
TIMING_GAP_BRIDGE_MS = 100        # kleine Gaps/Overlaps "glätten" (Midpoint)
TIMING_MIN_STEP_MS = 200          # Mindestdauer pro Wort-Highlight
TIMING_MIN_GAP_MS = 0             # optional: minimale Pause erzwingen (0 = keine)

def normalize_min_step_in_group(g: Group, min_step_ms: int = TIMING_MIN_STEP_MS) -> None:
    if not g.steps or len(g.steps) < 2:
        return

    min_step = min_step_ms / 1000.0

    # Wir gehen davon aus, dass:
    # - steps[0].t == g.t_in (oder sehr nahe)
    # - letzter step ist reset bei g.t_out (oder sehr nahe)
    # Wenn nicht: lieber vorher sicherstellen.

    # Hilfsfunktionen für segment durations
    def seg_dur(i: int) -> float:
        return g.steps[i+1].t - g.steps[i].t

    def is_label_seg(i: int) -> bool:
        return bool(g.steps[i].label)  # label des "aktuellen" steps

    # 2-3 passes reichen meistens
    for _ in range(3):
        changed = False

        for i in range(len(g.steps) - 1):
            if not is_label_seg(i):
                continue

            dur = seg_dur(i)
            if dur + 1e-9 >= min_step:
                continue

            need = min_step - dur  # Zeit, die Segment i länger werden muss

            # Wir verlängern Segment i, indem wir die RECHTE Grenze nach rechts schieben
            # -> das nimmt Zeit aus Segment i+1 (oder aus weiteren über Kaskade)
            # Aber du willst "links/rechts" fair: wir versuchen zuerst halb/halb.

            take_left = need / 2.0
            take_right = need - take_left

            # Links holen: heißt Grenze zwischen i-1 und i nach links verschieben
            # -> g.steps[i].t früher machen
            if i > 0:
                # Wie viel hat linkes Segment (i-1) an Surplus?
                left_dur = seg_dur(i-1)
                left_min = min_step if is_label_seg(i-1) else EPS
                left_surplus = max(0.0, left_dur - left_min)

                got = min(left_surplus, take_left)
                if got > 0:
                    # Grenze verschieben: steps[i].t -= got
                    new_t = g.steps[i].t - got
                    # clamp: nicht vor prev step
                    new_t = max(new_t, g.steps[i-1].t + EPS)
                    got = g.steps[i].t - new_t
                    if got > 0:
                        g.steps[i].t = new_t
                        take_left -= got
                        changed = True

            # Rechts holen: Grenze zwischen i und i+1 nach rechts schieben
            if i < len(g.steps) - 2:
                right_dur = seg_dur(i+1)
                right_min = min_step if is_label_seg(i+1) else EPS
                right_surplus = max(0.0, right_dur - right_min)

                got = min(right_surplus, take_right)
                if got > 0:
                    # Grenze verschieben: steps[i+1].t += got
                    new_t = g.steps[i+1].t + got
                    # clamp: nicht hinter next-next
                    new_t = min(new_t, g.steps[i+2].t - EPS)
                    got = new_t - g.steps[i+1].t
                    if got > 0:
                        g.steps[i+1].t = new_t
                        take_right -= got
                        changed = True

            # Wenn noch Bedarf übrig ist: aggressiver von der Seite mit mehr Surplus holen
            # (z.B. dein Sonderfall: "doch" lang, "mit" kurz -> alles von "doch")
            if take_left + take_right > 1e-6:
                remain = take_left + take_right

                # Versuch: erst links extra
                if i > 0:
                    left_dur = seg_dur(i-1)
                    left_min = min_step if is_label_seg(i-1) else EPS
                    left_surplus = max(0.0, left_dur - left_min)

                    got = min(left_surplus, remain)
                    if got > 0:
                        new_t = max(g.steps[i-1].t + EPS, g.steps[i].t - got)
                        got = g.steps[i].t - new_t
                        if got > 0:
                            g.steps[i].t = new_t
                            remain -= got
                            changed = True

                # Dann rechts extra
                if remain > 1e-6 and i < len(g.steps) - 2:
                    right_dur = seg_dur(i+1)
                    right_min = min_step if is_label_seg(i+1) else EPS
                    right_surplus = max(0.0, right_dur - right_min)

                    got = min(right_surplus, remain)
                    if got > 0:
                        new_t = min(g.steps[i+2].t - EPS, g.steps[i+1].t + got)
                        got = new_t - g.steps[i+1].t
                        if got > 0:
                            g.steps[i+1].t = new_t
                            remain -= got
                            changed = True

                # Wenn remain immer noch >0: dann ist es mathematisch nicht möglich,
                # ohne ein anderes Label-Segment unter Minimum zu drücken.
                # => wir lassen es so gut wie möglich (kein Drift, kein Chaos).
        if not changed:
            break

def normalize_timings(
    groups: list[Group],
    *,
    no_overlaps: bool = TIMING_NO_OVERLAPS,
    gap_bridge_ms: int = TIMING_GAP_BRIDGE_MS,
    min_step_ms: int = TIMING_MIN_STEP_MS,
    min_gap_ms: int = TIMING_MIN_GAP_MS,
) -> None:
    bridge = gap_bridge_ms / 1000.0
    min_gap = min_gap_ms / 1000.0

    # 1) Gaps/Overlaps zwischen Groups behandeln
    for i in range(len(groups) - 1):
        a = groups[i]
        b = groups[i + 1]

        delta = b.t_in - a.t_out  # >0 gap, <0 overlap

        # clamp/min-gap (optional)
        if delta < min_gap:
            # zu wenig Abstand (oder overlap). Wir korrigieren.
            if abs(delta) <= bridge:
                mid = (a.t_out + b.t_in) / 2.0
                a.t_out = mid
                b.t_in = mid
            else:
                # wenn no_overlaps: hart aneinander
                if no_overlaps:
                    b.t_in = a.t_out
                # sonst: lassen (wenn du Overlaps erlauben willst)

            # first step von b auf b.t_in ziehen
            if b.steps:
                b.steps[0].t = b.t_in

    # 2) pro Group min-step korrigieren (zeit-erhaltend)
    for g in groups:
        normalize_min_step_in_group(g, min_step_ms=min_step_ms)