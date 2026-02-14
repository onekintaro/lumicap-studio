from typing import List
from core.models import Entry, Group, Step

def build_groups(
    entries: List[Entry],
    default_style: str = "Normal",
    disable_highlight_at_out: bool = True
) -> List[Group]:
    groups: List[Group] = []
    cur: Group | None = None

    for e in entries:
        if cur is None or cur.key != e.key:
            cur = Group(
                key=e.key,
                style=default_style,
                text=e.plain,
                t_in=e.t_in,
                t_out=e.t_out,
                steps=[]
            )
            groups.append(cur)
        else:
            cur.t_out = e.t_out

        if e.ranges:
            s, en, label = e.ranges[0]
        else:
            s, en, label = 0, 0, ""

        cur.steps.append(Step(t=e.t_in, start=s, end=en, label=label))

    if disable_highlight_at_out:
        for g in groups:
            g.steps.append(Step(t=g.t_out, start=0, end=0, label=""))

    return groups