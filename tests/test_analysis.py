import pandas as pd
import pytest

from src.analysis.series import binary_series
from src.analysis.statistics import appearance_gaps, inspect_number
from src.collect.dataset import DatasetError


def test_binary_excludes_bonus_and_has_all_numbers(history):
    binary = binary_series(history)
    assert binary.shape == (12, 45)
    assert binary.index.tolist() == list(range(1, 13))
    assert binary[1].tolist() == [1,0,1,1,0,0,0,1,0,0,0,0]
    assert binary[45].sum() == 0
    assert (binary.sum(axis=1) == 6).all()


def test_intervals_and_censored_current_gap(history):
    assert appearance_gaps(binary_series(history)[1]) == [2,1,4]
    result = inspect_number(history, 1)
    assert result['total_frequency'] == 4
    assert result['current_gap'] == 4
    assert result['mean_gap'] == pytest.approx(7/3)
    assert result['median_gap'] == 2
    assert result['gap_variance'] == pytest.approx(14/9)
    assert result['gap_std'] == pytest.approx((14/9)**0.5)
    assert result['consecutive_pairs'] == 1
    assert result['longest_run'] == 2
    assert result['recent'][26]['observed_draws'] == 12
    assert result['recent'][26]['frequency'] == 4
    assert result['recent'][26]['rate'] == pytest.approx(1/3)


def test_never_seen_or_one_appearance_has_no_completed_gap(history):
    result = inspect_number(history, 45)
    assert result['current_gap'] is None
    assert result['absence_lower_bound'] == 12
    assert result['mean_gap'] is None
    assert result['gap_variance'] is None
    assert result['longest_run'] == 0
    result = inspect_number(history.iloc[:1], 1)
    assert result['current_gap'] == 0 and result['mean_gap'] is None


def test_analysis_refuses_missing_history_and_bad_numbers(history):
    with pytest.raises(DatasetError):
        binary_series(history.drop(index=2))
    for n in (0, 46, 1.5, True):
        with pytest.raises(ValueError): inspect_number(history, n)
    with pytest.raises(ValueError):
        appearance_gaps(pd.Series([0,2,1]))
