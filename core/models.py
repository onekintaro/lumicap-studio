from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class Step:
    t: float
    start: int
    end: int
    label: str = ""

@dataclass
class Entry:
    t_in: float
    t_out: float
    plain: str
    key: str
    ranges: List[Tuple[int, int, str]] = field(default_factory=list)

@dataclass
class Group:
    key: str
    style: str
    text: str
    t_in: float
    t_out: float
    steps: List[Step] = field(default_factory=list)