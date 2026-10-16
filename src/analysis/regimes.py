"""Transparent, prior-history thresholds; recurrence diagnostics are exploratory."""
import json
from numbers import Integral

import numpy as np
import pandas as pd

from .temporal import selected_numbers, selected_windows

REGIME_COLUMNS=['number','window_size','start_draw','end_draw','start_date','end_date',
                'support_start_draw','confirmed_draw','peak_draw','peak_periodicity_score',
                'dominant_lag','dominant_period','qualifying_endpoints','open_at_cutoff']


def detect_regimes(rolling,percentile=90,min_history=52,min_length=3):
    """Return (labeled windows, contiguous high-score endpoint regimes).

    Threshold at endpoint t uses finite scores strictly before t for that number
    and window size. Confirmation needs min_length endpoints: a reported start is
    recognized only at confirmed_draw. End dates can extend as new data arrives.
    """
    if not np.isfinite(percentile) or not 0<percentile<100:
        raise ValueError('percentile must be between 0 and 100')
    for name,value in [('min_history',min_history),('min_length',min_length)]:
        if isinstance(value,bool) or not isinstance(value,Integral) or value<1:
            raise ValueError(f'{name} must be a positive integer')
    labeled=rolling.copy().sort_values(['number','window_size','end_draw']).reset_index(drop=True)
    scores=labeled.periodicity_score.dropna()
    if not scores.between(0,1).all():
        raise ValueError('Periodicity scores must be in [0,1] or missing')
    if labeled.duplicated(['number','window_size','end_draw']).any():
        raise ValueError('Duplicate rolling endpoints')
    labeled['threshold']=np.nan
    labeled['prior_valid_scores']=0
    labeled['is_strong']=False
    regimes=[]
    for (number,window),group in labeled.groupby(['number','window_size'],sort=True):
        s=group.periodicity_score
        threshold=s.shift(1).expanding(min_periods=min_history).quantile(percentile/100)
        strong=(s>threshold)&s.notna()&threshold.notna()
        labeled.loc[group.index,'threshold']=threshold
        labeled.loc[group.index,'prior_valid_scores']=s.notna().cumsum().shift(1,fill_value=0)
        labeled.loc[group.index,'is_strong']=strong
        runs=[]
        current=[]
        previous=None
        for index,row in group.iterrows():
            if strong.loc[index] and (not current or row.end_draw==previous+1):
                current.append(index)
            else:
                if current: runs.append(current)
                current=[index] if strong.loc[index] else []
            previous=row.end_draw
        if current: runs.append(current)
        for run in runs:
            if len(run)<min_length: continue
            span=group.loc[run]
            first,last=span.iloc[0],span.iloc[-1]
            peak=span.loc[span.periodicity_score.idxmax()]
            regimes.append(dict(number=int(number),window_size=int(window),start_draw=int(first.end_draw),
                end_draw=int(last.end_draw),start_date=first.end_date,end_date=last.end_date,
                support_start_draw=int(first.start_draw),confirmed_draw=int(span.iloc[min_length-1].end_draw),
                peak_draw=int(peak.end_draw),peak_periodicity_score=float(peak.periodicity_score),
                dominant_lag=peak.dominant_lag,dominant_period=peak.dominant_period,
                qualifying_endpoints=len(span),open_at_cutoff=bool(last.end_draw==group.end_draw.max())))
    return labeled,pd.DataFrame(regimes,columns=REGIME_COLUMNS)


def recurrence_stats(regimes,numbers=None,windows=(26,52,104),min_regimes=4,max_gap_cv=.25,max_period_cv=.25):
    """Coalesce overlapping support windows before checking timing regularity.

    At least four independent episodes and three intervals are required. A low
    interval CV AND similar dominant spectral periods permit a timing candidate,
    not statistically established recurrence. No recurrence null test is done.
    """
    if isinstance(min_regimes,bool) or not isinstance(min_regimes,Integral) or min_regimes<4:
        raise ValueError('min_regimes must be an integer >=4')
    if any(not np.isfinite(v) or v<0 for v in (max_gap_cv,max_period_cv)):
        raise ValueError('CV limits must be finite and nonnegative')
    rows=[]
    for number in selected_numbers(numbers):
        for window in selected_windows(windows):
            group=regimes[(regimes.number==number)&(regimes.window_size==window)].sort_values('start_draw')
            episodes=[]
            for r in group.to_dict('records'):
                if episodes and r['support_start_draw']<=episodes[-1]['end_draw']:
                    previous=episodes[-1]
                    previous['end_draw']=max(previous['end_draw'],r['end_draw'])
                    if r['peak_periodicity_score']>previous['peak_periodicity_score']:
                        previous['peak_periodicity_score']=r['peak_periodicity_score']
                        previous['dominant_period']=r['dominant_period']
                else:
                    episodes.append(r.copy())
            raw_gaps=np.diff(group.start_draw.to_numpy()).astype(int)
            gaps=np.diff([r['start_draw'] for r in episodes]).astype(int)
            periods=np.array([r['dominant_period'] for r in episodes],dtype=float)
            gap_cv=float(np.std(gaps)/np.mean(gaps)) if len(gaps)>=2 else None
            period_cv=float(np.std(periods)/np.mean(periods)) if len(periods)>=2 and np.isfinite(periods).all() and (periods>0).all() else None
            status='insufficient_independent_regimes'
            candidate=None
            if len(episodes)>=min_regimes:
                status='irregular_timing_or_periods'
                if gap_cv is not None and period_cv is not None and gap_cv<=max_gap_cv and period_cv<=max_period_cv:
                    status='exploratory_timing_candidate'
                    candidate=float(np.mean(gaps))
            rows.append(dict(number=number,window_size=window,regime_count=len(group),independent_episodes=len(episodes),
                regime_start_gaps=json.dumps(raw_gaps.tolist()),episode_start_gaps=json.dumps(gaps.tolist()),
                mean_regime_start_gap=float(raw_gaps.mean()) if len(raw_gaps) else None,
                regime_start_gap_variance=float(raw_gaps.var()) if len(raw_gaps)>=2 else None,
                mean_episode_start_gap=float(gaps.mean()) if len(gaps) else None,
                episode_start_gap_variance=float(gaps.var()) if len(gaps)>=2 else None,
                episode_gap_cv=gap_cv,episode_period_cv=period_cv,recurring_interval_candidate=candidate,status=status))
    return pd.DataFrame(rows)
