"""Minimal model contract and public pre-draw context."""
from dataclasses import dataclass
from numbers import Integral
from typing import Protocol

import pandas as pd


@dataclass(frozen=True)
class TargetDrawContext:
    draw_no: int
    draw_date: pd.Timestamp


class NumberModel(Protocol):
    def score_numbers(self, history: pd.DataFrame,
                      target_draw_context: TargetDrawContext | None = None) -> dict[int, float]: ...

    def predict(self, history: pd.DataFrame, context: TargetDrawContext | None = None,
                k: int = 6, seed: int | None = None) -> list[int]: ...


def validate_ticket(ticket) -> list[int]:
    ticket = list(ticket)
    if (len(ticket) != 6 or any(isinstance(n, bool) or not isinstance(n, Integral)
                              or not 1 <= n <= 45 for n in ticket)
            or len(set(ticket)) != 6):
        raise ValueError("A ticket must contain six unique integers in 1..45")
    return sorted(int(n) for n in ticket)
