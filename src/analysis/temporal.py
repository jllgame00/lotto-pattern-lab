"""Normalized calendar tables and strictly trailing-window diagnostics."""
from numbers import Integral

import numpy as np
import pandas as pd

from src.collect.dataset import validate_history
from .series import binary_series
from .periodicity import PeriodicityConfig, periodicity_metrics

ROLLING_COLUMNS = ['number','window_size','start_draw','end_draw','end_date','appearances',
                   'appearance_rate','completed_gaps','mean_gap','median_gap','gap_std','gap_status',
                   'current_gap','absence_lower_bound','status','periodicity_score','acf_strength',
                   'dominant_lag','dominant_period','dominant_power','spectral_strength','gap_stability']


def selected_numbers(numbers=None):
    values = list(range(1,46)) if numbers is None else list(numbers)
    if not values or len(set(values))!=len(values) or any(
            isinstance(n,bool) or not isinstance(n,Integral) or not 1<=n<=45 for n in values):
        raise ValueError('numbers must be distinct integers in 1..45')
    return sorted(int(n) for n in values)


def selected_windows(windows=(26,52,104)):
    values=list(windows)
    if not values or len(set(values))!=len(values) or any(
            isinstance(w,bool) or not isinstance(w,Integral) or w<2 for w in values):
        raise ValueError('windows must be distinct integers >=2')
    return sorted(int(w) for w in values)


def gap_metrics(positions):
    gaps=np.diff(positions)
    return dict(completed_gaps=len(gaps),mean_gap=float(gaps.mean()) if len(gaps) else None,
                median_gap=float(np.median(gaps)) if len(gaps) else None,
                gap_std=float(gaps.std()) if len(gaps)>=2 else None,
                gap_status='ok' if len(gaps)>=10 else 'unstable' if len(gaps) else 'insufficient')


def calendar_stats(history, grouping='year', numbers=None):
    if grouping not in ('year','month','year_month'):
        raise ValueError('grouping must be year, month or year_month')
    data=validate_history(history)
    binary=binary_series(data)
    numbers=selected_numbers(numbers)
    if grouping=='year':
        groups=[({'year':int(y)},data.year==y) for y in sorted(data.year.unique())]
    elif grouping=='month':
        groups=[({'month':m},data.month==m) for m in range(1,13)]
    else:
        groups=[({'year':int(y),'month':int(m)},(data.year==y)&(data.month==m))
                for y,m in data[['year','month']].drop_duplicates().itertuples(index=False,name=None)]
    rows=[]
    for number in numbers:
        overall=float(binary[number].mean())
        for labels,mask in groups:
            draws=data.loc[mask,'draw_no'].to_numpy()
            values=binary.loc[draws,number].to_numpy()
            count=int(values.sum())
            rate=count/len(draws) if len(draws) else None
            rows.append(dict(number=number,**labels,total_draws=len(draws),appearances=count,
                             appearance_rate=rate,expected_appearances=len(draws)*6/45,
                             rate_deviation=rate-6/45 if rate is not None else None,
                             overall_rate=overall,relative_to_overall=rate/overall if overall and rate is not None else None,
                             **(gap_metrics(draws[values==1]) if grouping=='year' else {})))
    return pd.DataFrame(rows)


def rolling_stats(history,numbers=None,windows=(26,52,104),config=None):
    """At endpoint t, every metric uses t-window+1..t only (not a prediction for t).

    Completed gaps have both appearances inside the window. If no appearance is
    in-window, current_gap is unknown and absence_lower_bound is window length.
    """
    config=config or PeriodicityConfig()
    numbers,windows=selected_numbers(numbers),selected_windows(windows)
    data=validate_history(history)
    binary=binary_series(data)
    rows=[]
    for number in numbers:
        values=binary[number].to_numpy()
        for window in windows:
            for end in range(window,len(values)+1):
                x=values[end-window:end]
                positions=np.flatnonzero(x)
                gap=int(window-1-positions[-1]) if len(positions) else None
                rows.append(dict(number=number,window_size=window,start_draw=end-window+1,end_draw=end,
                                 end_date=data.iloc[end-1].draw_date,appearances=int(x.sum()),
                                 appearance_rate=float(x.mean()),**gap_metrics(positions),current_gap=gap,
                                 absence_lower_bound=gap if gap is not None else window,
                                 **periodicity_metrics(x,config)))
    return pd.DataFrame(rows,columns=ROLLING_COLUMNS)
