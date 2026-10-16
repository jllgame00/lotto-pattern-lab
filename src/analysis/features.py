"""One causal feature definition for every predictive experiment.

Rows describe the state immediately BEFORE target_draw; appeared_next is joined
only after features are computed. Unsupported estimates remain NaN. No fitted
normalization, full-history seasonality, or retrospective regimes enter here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.periodicity import periodicity_metrics
from src.analysis.series import binary_series
from src.collect.dataset import validate_history

FREQUENCY = [f'{kind}_{w}' for w in (5,10,26,52,104) for kind in ('count','rate')]
FREQUENCY += ['short_long_ratio', 'consecutive']
GAP = ['current_gap','has_appeared','mean_gap','median_gap','gap_std','gap_ratio']
PERIODICITY = ['periodicity_score','dominant_lag','acf_strength','dominant_period',
               'spectral_strength','strong_regime','regime_age','since_strong_regime']
CALENDAR = ['month_sin','month_cos','week_sin','week_cos']
GROUPS = dict(frequency=FREQUENCY, gap=GAP, periodicity=PERIODICITY, calendar=CALENDAR,
              frequency_gap=FREQUENCY+GAP, frequency_gap_periodicity=FREQUENCY+GAP+PERIODICITY,
              full=['number']+FREQUENCY+GAP+PERIODICITY+CALENDAR)


def feature_columns(group='full'):
    if group not in GROUPS:
        raise ValueError(f'Unknown feature group: {group}')
    return list(GROUPS[group])


def build_features(history, *, min_history=104, include_current=False, progress=None):
    if isinstance(min_history, bool) or not isinstance(min_history, int) or min_history < 104:
        raise ValueError('min_history must be an integer >= 104')
    data = validate_history(history)
    binary = binary_series(data)
    rows = []
    stop = len(data) + int(include_current)
    if stop <= min_history:
        raise ValueError('Insufficient history for supervised features')
    for number in range(1,46):
        x = binary[number].to_numpy()
        sums = np.r_[0, np.cumsum(x, dtype=int)]
        positions = np.flatnonzero(x)
        number_rows = []
        # Start at 104 even when callers request a later first target: regime
        # thresholds must not depend on the exported feature-table start date.
        for end in range(104, stop):
            past = positions[positions < end]
            gaps = np.diff(past)
            gap = end-1-past[-1] if len(past) else end
            mean = float(gaps.mean()) if len(gaps) else np.nan
            date = data.iloc[end-1].draw_date + pd.Timedelta(days=7)
            month, week = date.month, date.isocalendar().week
            row = dict(target_draw=end+1, target_date=date, feature_cutoff=end, number=number,
                       current_gap=int(gap), has_appeared=int(bool(len(past))), mean_gap=mean,
                       median_gap=float(np.median(gaps)) if len(gaps) else np.nan,
                       gap_std=float(gaps.std()) if len(gaps)>=2 else np.nan,
                       gap_ratio=gap/mean if np.isfinite(mean) else np.nan,
                       consecutive=int(x[end-1] == 1 and x[end-2] == 1),
                       month=month, iso_week=week,
                       month_sin=np.sin(2*np.pi*month/12), month_cos=np.cos(2*np.pi*month/12),
                       week_sin=np.sin(2*np.pi*week/53), week_cos=np.cos(2*np.pi*week/53))
            for window in (5,10,26,52,104):
                count = int(sums[end]-sums[end-window])
                row[f'count_{window}'] = count
                row[f'rate_{window}'] = count/window
            row['short_long_ratio'] = row['rate_10']/row['rate_104'] if row['rate_104'] else np.nan
            metrics = periodicity_metrics(x[end-104:end])
            row.update({key: metrics[key] for key in PERIODICITY[:5]})
            number_rows.append(row)
        frame = pd.DataFrame(number_rows)
        frame[PERIODICITY[:5]] = frame[PERIODICITY[:5]].astype(float)
        threshold = frame.periodicity_score.shift(1).expanding(min_periods=52).quantile(.9)
        high = (frame.periodicity_score > threshold).to_numpy()
        run, last_strong = 0, None
        strong, ages, since = [], [], []
        for i, qualifies in enumerate(high):
            run = run+1 if qualifies else 0
            confirmed = run >= 3
            strong.append(int(confirmed))
            ages.append(run-3 if confirmed else np.nan)  # age since confirmation
            if confirmed:
                last_strong = i
            since.append(i-last_strong if last_strong is not None else np.nan)
        frame['strong_regime'], frame['regime_age'], frame['since_strong_regime'] = strong, ages, since
        frame['appeared_next'] = [int(x[t-1]) if t<=len(x) else np.nan for t in frame.target_draw]
        rows.append(frame[frame.target_draw > min_history])
        if progress and number % 15 == 0:
            progress(f'Features: {number}/45 numbers')
    return pd.concat(rows, ignore_index=True).sort_values(['target_draw','number']).reset_index(drop=True)
