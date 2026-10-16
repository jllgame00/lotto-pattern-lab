import numpy as np
import pandas as pd
import pytest

from src.analysis.statistics import inspect_number
from src.analysis.temporal import calendar_stats, rolling_stats
from src.analysis.periodicity import PeriodicityConfig


def test_appearance_draws_and_longest_observed_absence(history):
    stats = inspect_number(history, 1)
    assert stats['appearance_draws'] == [1,3,4,8]
    assert stats['longest_absence'] == 4
    assert stats['longest_absence_touches_boundary']
    assert inspect_number(history,45)['longest_absence'] == 12


def test_year_normalizes_by_eligible_draws_and_internal_gaps(history):
    yearly = calendar_stats(history, 'year')
    n = yearly.query('number == 1').set_index('year')
    assert n.loc[2002,'total_draws'] == 4
    assert n.loc[2002,'appearances'] == 3
    assert n.loc[2002,'appearance_rate'] == .75
    assert n.loc[2002,'expected_appearances'] == pytest.approx(4*6/45)
    assert n.loc[2002,'rate_deviation'] == pytest.approx(.75-6/45)
    assert n.loc[2002,'mean_gap'] == 1.5
    assert n.loc[2002,'median_gap'] == 1.5
    assert n.loc[2002,'gap_std'] == .5
    assert n.loc[2003,'total_draws'] == 8
    assert n.loc[2003,'appearances'] == 1
    assert pd.isna(n.loc[2003,'mean_gap'])
    assert yearly.query('number == 45').appearances.sum() == 0


def test_month_and_year_month_denominators(history):
    month = calendar_stats(history,'month').query('number == 1').set_index('month')
    assert len(month) == 12
    assert month.loc[12,'total_draws'] == 4
    assert month.loc[12,'appearance_rate'] == .75
    assert month.loc[12,'relative_to_overall'] == pytest.approx(2.25)
    assert month.loc[3,'total_draws'] == 0
    assert pd.isna(month.loc[3,'appearance_rate'])
    assert pd.isna(calendar_stats(history,'month').query('number == 45').relative_to_overall).all()
    ym = calendar_stats(history,'year_month')
    assert len(ym) == 45*3
    assert ym.query('number == 1 and month == 1').iloc[0].appearances == 1


def long_history(history, n=120):
    frame = pd.concat([history]*((n+11)//12), ignore_index=True).iloc[:n].copy()
    frame['draw_no'] = np.arange(1,n+1)
    frame['draw_date'] = pd.date_range('2002-12-07',periods=n,freq='7D')
    return frame


def test_rolling_boundaries_and_prefix_invariance(history):
    full = long_history(history)
    config = PeriodicityConfig(max_lag=12)
    a = rolling_stats(full, numbers=[1,45], windows=[26,52,104], config=config)
    assert a.query('number == 1 and window_size == 26').end_draw.tolist() == list(range(26,121))
    row = a.query('number == 1 and end_draw == 26 and window_size == 26').iloc[0]
    assert row.start_draw == 1 and row.appearances == 9
    assert row.appearance_rate == pytest.approx(9/26)
    assert row.current_gap == 1
    assert a.query('number == 45').periodicity_score.isna().all()
    assert a.query('number == 45').current_gap.isna().all()
    assert (a.query('number == 45').absence_lower_bound == a.query('number == 45').window_size).all()
    before = rolling_stats(full.iloc[:80], numbers=[1,45], windows=[26,52,104], config=config)
    pd.testing.assert_frame_equal(a[a.end_draw <= 80].reset_index(drop=True), before.reset_index(drop=True))
    full.loc[80:, 'num1'] = 13
    changed = rolling_stats(full, numbers=[1,45], windows=[26,52,104], config=config)
    pd.testing.assert_frame_equal(a[a.end_draw <= 80].reset_index(drop=True), changed[changed.end_draw <= 80].reset_index(drop=True))


def test_empty_rolling_schema_and_invalid_options(history):
    result = rolling_stats(history,numbers=[1],windows=[26])
    assert result.empty and 'periodicity_score' in result
    for kwargs in (dict(numbers=[0]), dict(windows=[0]), dict(windows=[26,26])):
        with pytest.raises(ValueError): rolling_stats(history,**kwargs)
    with pytest.raises(ValueError): calendar_stats(history,'invalid')
