import numpy as np
import pandas as pd
import pytest

from src.analysis.regimes import detect_regimes, recurrence_stats


def rolling_fixture(scores):
    n=len(scores)
    return pd.DataFrame(dict(number=[17]*n,window_size=[26]*n,
        start_draw=np.arange(1,n+1),end_draw=np.arange(26,26+n),
        end_date=pd.date_range('2003-05-31',periods=n,freq='7D'),
        periodicity_score=scores,dominant_lag=[6]*n,dominant_period=[6.0]*n))


def test_prior_only_threshold_minimum_history_and_contiguous_regimes():
    frame=rolling_fixture([.1]*5+[.6,.7,.8]+[.1,.9,.1])
    labeled,regimes=detect_regimes(frame,min_history=5,percentile=90,min_length=3)
    assert labeled.iloc[:5].threshold.isna().all()
    assert labeled.iloc[5].threshold == .1
    assert len(regimes)==1
    r=regimes.iloc[0]
    assert r.start_draw==31 and r.end_draw==33 and r.confirmed_draw==33
    assert r.support_start_draw==6 and r.peak_periodicity_score==.8
    assert not r.open_at_cutoff
    prefix,_=detect_regimes(frame.iloc[:7],min_history=5,percentile=90,min_length=3)
    pd.testing.assert_frame_equal(labeled.iloc[:7].reset_index(drop=True),prefix)
    # Equal scores do not create spurious high regimes.
    assert detect_regimes(rolling_fixture([.5]*20),min_history=5)[1].empty


def test_nan_scores_break_regimes_and_require_valid_threshold_history():
    _,regimes=detect_regimes(rolling_fixture([.1]*5+[.5,.6,np.nan,.7,.8,.9]),min_history=5,min_length=3)
    assert len(regimes)==1 and regimes.iloc[0].start_draw==34
    assert regimes.iloc[0].open_at_cutoff
    for kwargs in (dict(percentile=100),dict(min_history=0),dict(min_length=0)):
        with pytest.raises(ValueError): detect_regimes(rolling_fixture([.1]),**kwargs)


def regimes_fixture(starts,periods=None):
    return pd.DataFrame([dict(number=17,window_size=26,start_draw=s,end_draw=s+3,
        support_start_draw=s-25,peak_periodicity_score=.7,dominant_period=p)
        for s,p in zip(starts,periods or [6]*len(starts))])


def test_recurrence_requires_independent_episodes_and_regular_timing():
    def summary(starts,periods=None):
        return recurrence_stats(regimes_fixture(starts,periods),numbers=[17],windows=[26]).iloc[0]
    assert summary([100,300,500]).status == 'insufficient_independent_regimes'
    a=summary([100,300,500,700])
    assert a.independent_episodes==4 and a.recurring_interval_candidate==200
    assert a.status == 'exploratory_timing_candidate'
    assert summary([100,110,120,130]).independent_episodes == 1
    assert pd.isna(summary([100,150,300,700]).recurring_interval_candidate)
    assert pd.isna(summary([100,300,500,700],[3,6,12,3]).recurring_interval_candidate)


def test_empty_reports_preserve_schema():
    labeled,regimes=detect_regimes(rolling_fixture([]))
    assert labeled.empty and regimes.empty and 'start_draw' in regimes
    r=recurrence_stats(regimes,numbers=[17],windows=[26])
    assert r.iloc[0].regime_count==0
