"""Descriptive statistics; completed gaps exclude censored boundary intervals."""
from numbers import Integral

import numpy as np
import pandas as pd

from .series import binary_series


def appearance_gaps(series: pd.Series) -> list[int]:
    """Distances in draws between appearances (adjacent appearances => 1)."""
    if not series.isin([0, 1]).all():
        raise ValueError("Expected a binary series")
    return np.diff(np.flatnonzero(series.to_numpy())).astype(int).tolist()


def inspect_number(history: pd.DataFrame, number: int) -> dict:
    if isinstance(number, bool) or not isinstance(number, Integral) or not 1 <= number <= 45:
        raise ValueError("number must be an integer in 1..45")
    series = binary_series(history)[number]
    gaps = appearance_gaps(series)
    positions = np.flatnonzero(series.to_numpy())
    run = longest = pairs = 0
    for value in series:
        if value:
            pairs += int(run > 0)
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    current_gap = int(len(series) - 1 - positions[-1]) if len(positions) else None
    return dict(number=int(number), observed_draws=len(series), total_frequency=int(series.sum()),
                appearance_rate=float(series.mean()), current_gap=current_gap,
                absence_lower_bound=current_gap if current_gap is not None else len(series),
                appearance_intervals=gaps, completed_gap_count=len(gaps),
                mean_gap=float(np.mean(gaps)) if gaps else None,
                median_gap=float(np.median(gaps)) if gaps else None,
                gap_variance=float(np.var(gaps, ddof=0)) if gaps else None,
                gap_std=float(np.std(gaps, ddof=0)) if gaps else None,
                consecutive_pairs=pairs, longest_run=longest, current_run=run,
                recent={n: dict(observed_draws=len(series.tail(n)),
                                frequency=int(series.tail(n).sum()),
                                rate=float(series.tail(n).mean())) for n in (26, 52, 104)},
                warnings=["Fewer than 10 completed gaps; estimates are unstable."] if len(gaps) < 10 else [])
